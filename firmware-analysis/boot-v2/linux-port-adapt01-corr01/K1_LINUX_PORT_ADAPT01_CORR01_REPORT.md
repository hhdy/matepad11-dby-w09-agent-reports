# K1_DBY_W09_LINUX_PORT_ADAPT01_CORR01 — 审核与修正报告

- 日期：2026-11-28
- 性质：对 PREP10 候选与 boot v2/DTBO 元数据的离线修正审核（CORR01）
- 设备操作：**无**（纯离线；未连接设备、未写入任何分区）
- 输入：
  - stock boot 分区副本：`r155/copies-primary/boot.img`（100,663,296 B，sha256 `7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8`）
  - stock dtbo 分区副本：`r155/copies-primary/dtbo.img`（25,165,824 B，sha256 `51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c`）
  - PREP10 候选：`K1_HOST_CANDIDATE_PREP/dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img`（46,563,215 B，sha256 `d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091`）

## 0. 结论速览

| 审核项 | 判定 |
|---|---|
| DTBO 表修正解析（id/rev/custom 映射） | **PASS** — 9 条目全部 id=0 rev=0 custom=[0,0,0,0]；9/9 FDT magic=0xD00DFEED；条目连续无重叠；max_end==total_size |
| PREP10 boot v2 有效性 | **PASS** — 结构参数与 stock 全同，仅 kernel/DTB/cmdline 前缀三处按设计替换 |
| stock boot 尾部审计 | **PASS** — payload_end=24,449,024；其后 76.68 MiB 全零；无 AVB footer、无私有尾部数据 |
| **BOOT_PREFIX_WRITE_GATE** | **PASS** — 前缀写 [0,46,563,215) 不破坏任何尾部数据（保留区非零字节=0） |
| DTBO 处置 | **KEEP_STOCK_NO_WRITE**（id/rev/custom 全零 → AOSP 掩码选择机制无法区分条目；实机已选中 Entry 2=VD，改写无收益、有风险） |
| separate ramdisk 处置 | **KEEP_STOCK_NO_WRITE**（ABL 加载它作 kernel initrd，PREP04 已字节级证实） |
| 候选交付 | PREP10 原样字节交付（不做重打包）——`dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img` |
| ignore_loglevel 策略 | **AI1_DECISION**（保留=维持 UART earlycon 调试意图；移除=贴近 stock；参数本身不能创造输出通道，见 §4） |

## 1. 背景：AI1 指出的三类问题与本轮修正

1. **DTBO 元数据解析错误**：此前轮次把 dt_table_entry 的 id/rev/custom[4] 字段映射读错，REV2 报告还把 AvbHashDescriptor (tag=4) 误标为 Property Descriptor (tag=0)。本轮用修正解析器重新解析全表。
2. **boot 尾部未审计**：PREP10 只有 46.4 MiB，而 boot 分区 96 MiB；写入方案（前缀写）要求证明尾部无需要保留的数据。本轮完成全 96 MiB 审计。
3. **stock vs PREP10 未做系统对照**：本轮逐字段对照，明确 PREP10 的每一处差异及其来源。

## 2. Stage A：DTBO 表修正解析

完整输出：`dtbo_parse_corr01_output.txt`；脚本：`scripts/dtbo_parse_corr01.py`（WSL Python）与 `scripts/dtbo_parse_corr01.js`（Windows Node 重跑版，本轮实际执行版）；抽取条目：`dtbo_entries_corr01/`。

表头：`magic=0xD7B7AB1E total_size=2963810 hdr_size=32 entry_size=32 num_entries=9 entries_offset=32 page_size=4096 version=0`

| Entry | dt_size | dt_offset | id | rev | custom[4] | FDT magic | fdt_total==dt_size | 变体标记 | sha256（前 16） |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 329,044 | 320 | 0 | 0 | 全 0 | 0xD00DFEED | ✓ | — | `6940ce1167a3a21c` |
| 1 | 329,352 | 329,364 | 0 | 0 | 全 0 | 0xD00DFEED | ✓ | — | `685a837e65a692da` |
| 2 | 329,240 | 658,716 | 0 | 0 | 全 0 | 0xD00DFEED | ✓ | **VD**@0x399b0 | `0633a6fbeebbad45` |
| 3 | 329,098 | 987,956 | 0 | 0 | 全 0 | 0xD00DFEED | ✓ | — | `e68e5a48f64cfb68` |
| 4 | 329,340 | 1,317,054 | 0 | 0 | 全 0 | 0xD00DFEED | ✓ | — | `866991056bef3a99` |
| 5 | 329,356 | 1,646,394 | 0 | 0 | 全 0 | 0xD00DFEED | ✓ | — | `699df8950612ca38` |
| 6 | 329,356 | 1,975,750 | 0 | 0 | 全 0 | 0xD00DFEED | ✓ | — | `fca5a7a83ea69a47` |
| 7 | 329,352 | 2,305,106 | 0 | 0 | 全 0 | 0xD00DFEED | ✓ | — | `0a57a7f8ac678073` |
| 8 | 329,352 | 2,634,458 | 0 | 0 | 全 0 | 0xD00DFEED | ✓ | **VG**@0x399b4 | `a7946352a86ab6e4` |

边界审计：
- 条目连续（无重叠、无空洞）：每条 end == 下一条 offset；末条 end=2,963,810 == total_size 字段 == 表自述大小。
- **打包布局**：9/9 条目 dt_offset 非 page_size 对齐（320、329364、…）——非 AOSP mkdtimg 默认的页对齐布局，是华为私有打包。这再次证明该表由华为工具生成，标准工具链不能假设布局惯例。
- 9/9 条目含 `rootparam` 属性。
- Entry 2 `qcom,boardid=<0x8 0x2 0x0 0x6>`、`board_name=DBY_W09_VD` 与 PREP12 轮从实机提取的运行时 FDT 完全一致（实机 = VD 变体）。
- 分区文件 25,165,824 B，仅前 2,963,810 B 被表使用，其余全零（分区填充）。

**关键推论（DTBO_KEEP_STOCK）**：id/rev/custom 全零意味着 AOSP dt_table 的 (id, rev, board 掩码) 选择机制在这张表上对 9 个条目给出完全相同的匹配值——标准选择器无法区分条目。华为 ABL 必然依赖表外机制（FDT 内容匹配或固定索引），实机验证结果为 Entry 2 (VD)。任何 DTBO 重写（哪怕语义等价）都可能破坏这个未知选择机制，而收益为零（Entry 2 本身已含正确 /rootparam）。→ **不改 DTBO。**

## 3. Stage C：stock boot 尾部审计

完整输出：`boot_tail_audit_output.txt`；脚本：`scripts/boot_tail_audit.py`；纪要：`boot_tail_audit.md`。

- stock boot image：kernel@0x1000（22,256,282 B）、ramdisk@0x153b000（519,986 B）、dtb@0x15ba000（1,664,243 B），payload_end=0x1751000=24,449,024 B（≈23.3 MiB）。
- 尾部 [24,449,024, 100,663,296) 共 76,214,272 B：**非零区间 0 个，全零**。
- 末 64 B / 4 KiB / 64 KiB / 1 MiB 全零；**无 `AVBf` footer**（boot 分区不带 AVB 尾部；AVB 元数据在 vbmeta 分区，与本轮写入面无关）。
- 前缀写 [0, 46,563,215) 保留区 [46,563,215, 100,663,296)（54,100,081 B）非零字节 = 0。
- PREP10 按 4K 对齐 payload_end=0x2c68000=46,563,328 ≤ 100,663,296，适配分区。
- **BOOT_PREFIX_WRITE_GATE = PASS**。

## 4. Stage D：stock vs PREP10 逐字段对照

纪要：`stock_prep10_comparison.md`；原始输出：`boot_tail_audit_output.txt`（header comparison 段）。

**SAME**：magic、header_version=2、page_size=4096、header_size=1660、kernel_addr=0x8000、ramdisk_addr=0x2000000、second_size=0、tags_addr=0x100、dtb_addr=0x1f00000、os_version=0x1600014b、extra_cmdline=空、name=空、**embedded ramdisk 519,986 B 逐字节一致（sha256 `a4b94ff6…1af3c`）**。

**DIFF（全部 3 处）**：
1. kernel：22,256,282 B（HOS）→ 44,820,992 B（ACK Image，sha256 `f89a2839…bad21` = 冻结值）。
2. DTB：1,664,243 B（stock）→ 1,216,399 B（PREP04 candidate，sha256 `7bb9a1fb…996b7` = 冻结值）。
3. cmdline：432→442 字符；差异恰好两处——前缀加 `ignore_loglevel `（PREP10 设计目的：压制 ABL 追加的 `loglevel=0`），`earlycon=msm_geni_serial`→`earlycon=qcom_geni`（PREP06 改名适配 ACK 驱动）。其余字节与 stock 一致。

**PREP10 有效性 = PASS**。PREP10 不是 stock 的复制品，而是共享 stock 全部结构参数与 embedded ramdisk 的独立构建，替换件均可溯源到冻结哈希。

**ignore_loglevel 说明**：该参数只解除 kernel printk 级别过滤，不创造输出通道；若 kernel 在 earlycon 之前崩溃它无意义。它是否保留影响 UART12 观测窗口（K1 仍无可观察通道，UART12 硬件审计仍 HOLD）——**保留与否交 AI1 决策**，两种选择均不影响本候选的结构有效性。

## 5. 写入面与处置计划（均 NOT EXECUTED）

- `partition_map.md`：启动链分区映射（boot=sde9 96MiB、dtbo=sde13、ramdisk=sda22、vbmeta=sde12、abl=sde6）+ 完整分区表。
- `apply_plan_NOT_EXECUTED.md`：boot 分区前缀写 + 读回核验 + 失败即停规程。**未执行。**
- `restore_plan_NOT_EXECUTED.md`：两条恢复路径（设备侧备份 dd / fastboot flash 完整 96 MiB）。**未执行。**
- 写入面 = 仅 boot 分区。DTBO、separate ramdisk、vbmeta、abl、misc 一律不写。

## 6. 候选交付

- 交付物 = PREP10 文件**原样字节**（sha256 `d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091`），无重打包。修正审核未发现需要改动 PREP10 的任何理由。
- 交付通道：GitHub Release 资产（仓 `hhdy/matepad11-dby-w09-agent-reports`），报告与脚本入库 `firmware-analysis/boot-v2/linux-port-adapt01-corr01/`。
- 按 AI1/用户约束：**原厂完整固件、设备识别数据、ksu 细节不公开**；仅交付含 ACK kernel + PREP04 DTB + stock embedded ramdisk 的候选 boot 与元数据报告。
- 复现说明：`packaging_repro.md`。

## 7. 风险与未决

| 风险 | 等级 | 缓解 |
|---|---|---|
| K1 无可观察通道（UART12 HOLD 依赖硬件审计） | 高 | 本轮不动；UART 观测仍需 USB-UART 适配器（PREP13/14 轮结论） |
| ABL 对非 stock kernel 的二次校验未知 | 中 | GhostLock 工程 ABL（china_compile）已替换 retail；vbmeta rb_loc=2 已写；fastboot RAMDISK 路径曾实测进入（RAMBOOT_NOT_CONFIRMED_USB_WRITE_TIMEOUT 为主机 USB 错误，非 ABL 拒绝） |
| DTBO 选择机制未知（id 全零） | 低（不改即无风险） | KEEP_STOCK |
| 写入后无法进系统 | 低 | restore_plan 两条路径；boot 备份哈希已知 |

## 8. 环境备注

本轮执行中途 WSL2 ext4.vhdx 挂载失败（ERROR_PATH_NOT_FOUND），DTBO 解析改用 Windows Node v24.15.0 重跑；Python/JS 两版实现输出一致（同表头、同 id/rev/custom=0、同条目偏移/大小/SHA），两版脚本均入库以供复核。boot 尾部审计仍为 WSL Python 产出的有效输出（`boot_tail_audit_output.txt`，故障发生前完成）。
