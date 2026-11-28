# CORR01 — evidence_matrix.md

每条断言 → 证据文件/命令/哈希。主机环境：Windows 10 (cmd)，分析经 WSL Python / Windows Node v24.15.0。
注意：本轮执行中途 WSL2 ext4.vhdx 挂载失败（`Wsl/Service/CreateInstance/MountDisk/ERROR_PATH_NOT_FOUND`），DTBO 解析改用 Windows Node 重跑（`scripts/dtbo_parse_corr01.js`），与此前 WSL Python 结果一致（同 id/rev/custom=0、同条目偏移/大小）。

## E1. stock 输入文件

| 断言 | 值 | 证据 |
|---|---|---|
| stock dtbo.img（分区完整副本） | 25,165,824 B | `r155/copies-primary/dtbo.img`；sha256 `51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c`（解析器首行输出） |
| stock boot.img（分区完整副本） | 100,663,296 B | `r155/copies-primary/boot.img`；sha256 `7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8` |
| PREP10 候选 boot | 46,563,215 B | `K1_HOST_CANDIDATE_PREP/dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img`；sha256 `d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091` |

## E2. DTBO 表修正解析（Stage A）

| 断言 | 值 | 证据 |
|---|---|---|
| 表头 | magic=0xD7B7AB1E，total_size=2,963,810，hdr_size=32，entry_size=32，num_entries=9，entries_offset=32，page_size=4096，version=0 | `dtbo_parse_corr01_output.txt` |
| 条目 id/rev/custom 全零 | 9/9 条目 id=0x00000000 rev=0x00000000 custom=[0,0,0,0] | 同上（每条 Entry 块） |
| FDT 有效性 | 9/9 条目 FDT magic=0xD00DFEED，fdt_total_size==dt_size | 同上 |
| 条目布局 | 连续无重叠无空洞：320→329364→658716→987956→1317054→1646394→1975750→2305106→2634458→2963810；max_end==total_size | 同上 boundary checks |
| 打包布局（非 mkdtimg 默认页对齐） | 9/9 条目 dt_offset 非 page_size 对齐（320/329364/…） | 同上 |
| dt_size/偏移逐条 | E0=329044@320 … E8=329352@2634458（各条目完整 SHA-256 见输出） | 同上 |
| 变体标记 | Entry 2 含 `DBY_W09_VD` @overlay+0x399b0；Entry 8 含 `DBY_W09_VG` @overlay+0x399b4；9/9 含 `rootparam` | 同上 |
| Entry 2 = VD 与实机一致 | `qcom,boardid=<0x8 0x2 0x0 0x6>`、`board_name=DBY_W09_VD` 与 PREP12 提取的实机 FDT 完全一致 | PREP12 轮 rootparam 对照证据（本仓库 linux-port-adapt01 目录） |
| 抽取副本 | 9 个 .dtbo 文件已落盘 | `dtbo_entries_corr01/entry_0…entry_8_…dtbo`，SHA-256 见 `SHA256SUMS.txt` |

**id/rev/custom=0 的含义**：标准 AOSP libufdt/dt_table 选择逻辑（按 id/rev/board 掩码匹配）在这张表上无法区分任何条目——所有条目匹配值相同。华为 ABL 必然使用表外机制（FDT 内容匹配或固定索引）选择 overlay；实机验证选中 Entry 2 (VD)。**推论：不重建 DTBO，保持 stock 原样（DTBO_KEEP_STOCK）。**

## E3. boot 尾部审计（Stage C）

| 断言 | 值 | 证据 |
|---|---|---|
| stock payload 布局 | kernel@0x1000(22,256,282B) ramdisk@0x153b000(519,986B) dtb@0x15ba000(1,664,243B) payload_end=0x1751000=24,449,024 | `boot_tail_audit_output.txt` |
| 尾部全零 | [24,449,024, 100,663,296) = 76,214,272 B 全零，非零区间=0 | 同上 `tail non-zero ranges: 0` |
| 无 AVB footer | 末 64B/4KiB/64KiB/1MiB 全零，无 `AVBf` magic | 同上 |
| 前缀写安全 | 写 PREP10 [0,46,563,215) 后保留区 [46,563,215, 100,663,296) 非零字节=0 | 同上 preserved region 段 |
| PREP10 适配分区 | 46,563,215 < 100,663,296 ✓；PREP10 payload_end=0x2c68000=46,563,328（4K 对齐） | 同上 |
| **BOOT_PREFIX_WRITE_GATE** | **PASS** | 同上 |

## E4. stock vs PREP10 对照（Stage D）

| 断言 | 值 | 证据 |
|---|---|---|
| 结构参数全同 | page_size=4096 header_version=2 header_size=1660 kernel_addr=0x8000 ramdisk_addr=0x2000000 tags_addr=0x100 dtb_addr=0x1f00000 os_version=0x1600014b second_size=0 | `boot_tail_audit_output.txt` header comparison（SAME 项） |
| 差异仅 3 处 | kernel_size（22,256,282→44,820,992）、dtb_size（1,664,243→1,216,399）、cmdline（432→442 字符） | 同上 DIFF 项 |
| cmdline 变更 | 前缀加 `ignore_loglevel `；`earlycon=msm_geni_serial`→`earlycon=qcom_geni`；其余 432 字符与 stock 一致 | 同上 first_diff + 前缀 |
| embedded ramdisk 与 stock 逐字节一致 | 519,986 B，sha256 `a4b94ff6…1af3c`（双方同值） | PREP10 构建轮冻结值 + header rsz SAME |
| kernel/DTB 为冻结构建产物 | ACK Image sha256 `f89a2839…bad21`；PREP04 candidate DTB sha256 `7bb9a1fb…996b7` | PREP10 构建轮（linux-port-adapt01 主报告） |
| **PREP10 有效性** | **PASS**（boot v2 全字段可解析，结构=stock 克隆，仅按设计替换 kernel/DTB/cmdline 前缀） | 本轮全部分析 |

## E5. separate ramdisk / DTBO 处置

| 断言 | 值 | 证据 |
|---|---|---|
| DTBO | **KEEP_STOCK_NO_WRITE** | E2 推论（id 全零不可区分 + Entry 2 已是实机变体） |
| separate ramdisk（sda22, 2,097,152 B） | **KEEP_STOCK_NO_WRITE**——ABL 加载它作为 kernel initrd（PREP04 字节级证实），含 init/init.real/ksu.ko | PREP04/PREP12 轮证据 |
| vbmeta / abl / misc | 不写 | 本候选方案写入面仅 boot 分区 |

## E6. 交付物

| 项 | 值 |
|---|---|
| 仓库 | `hhdy/matepad11-dby-w09-agent-reports`，目录 `firmware-analysis/boot-v2/linux-port-adapt01-corr01/` |
| 候选交付 | GitHub Release 资产（PREP10 boot.img 原样，字节不改动） |
| 敏感 excluded | 原厂完整固件（r155 全量）、设备识别数据不上传 ✓（用户指令） |

## 局限

- 本轮为纯离线审计，未做任何设备写入（apply/restore 仅文档）。
- DTBO 选择机制的 ABL 侧代码依据来自 PREP13/14 ABL 逆向轮（boot_v2 加载路径），未在本轮重新反汇编——引用为上游轮次结论。
- WSL 中途不可用导致分析工具链切换为 Node（Windows 原生），两个实现（Python/JS）输出一致，脚本双份保留于 `scripts/`。
