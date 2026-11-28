# K1-DBY-W09-LINUX-PORT-ADAPT01-CORR01 — AI1 独立审核

审核日期：2026-11-28
对象提交：10d769eecabab4de5e7be62eb562318d70777cc4
候选 Release：k1-boot-v2-prep10-candidate
审核结论：PARTIAL PASS / BOOT WRITE HOLD

## 1. 总结

CORR01 已完成大部分上一轮要求的有限修正：DTBO entry 的 id/rev/custom[4] 解析正确；Entry 2 的 VD overlay 内容有明确证据；stock boot 分区尾部全零审计已补；PREP10 与 stock boot header 逐字段对照已补；PREP10 boot 已通过 GitHub Release 上传，资产大小与 SHA-256 元数据匹配；DTBO、separate ramdisk、vbmeta、ABL 均计划保持原样，仅拟更新 boot 分区。

但发现一个尚未分析的关键风险：PREP10 ACK kernel 增长到 44,820,992 B，boot header 中 kernel/DTB/ramdisk 地址仍为 stock 数值。按 AOSP boot header v2 定义，这些字段是物理加载地址，各组件会放到指定地址。以字段字面含义计算，PREP10 kernel 地址范围覆盖 DTB 和 embedded ramdisk 地址范围。华为 ABL 是否会重新分配、搬移或忽略这些字段，当前报告没有证明。

因此：DTBO 保持原厂、separate ramdisk 保持原厂、boot 分区尾部保护检查可通过；但在完成 ABL load-address / overlap 审计前，不批准将 PREP10 写入 boot。

## 2. GitHub 交付与候选资产

- CORR01 commit：10d769eecabab4de5e7be62eb562318d70777cc4
- 报告：firmware-analysis/boot-v2/linux-port-adapt01-corr01/K1_LINUX_PORT_ADAPT01_CORR01_REPORT.md
- Release：k1-boot-v2-prep10-candidate
- Release asset：dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img
- 资产大小：46,563,215 B
- GitHub Release API digest：sha256:d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091
- 与 PREP10 冻结 SHA-256 完全一致。

报告、SHA256SUMS、DTBO 抽取件、解析脚本、boot_tail_audit、stock/PREP10 对照、partition_map、未执行的 apply/restore 文档均已入库。

限制：Release asset 本身未通过本次文本读取接口下载并重新计算字节 SHA；本次以 GitHub Release API 的 asset digest 元数据与冻结 PREP10 SHA 相符作为核验。实际写入前仍须在本机下载后重新计算哈希。

## 3. DTBO 修正复核

### 3.1 通过项

修正解析器现按标准字段顺序读取 dt_size、dt_offset、id、rev、custom[0..3]。输出显示：
- stock dtbo.img：25,165,824 B，SHA-256 51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c；
- 9 entries，header total_size=2,963,810 B；
- 9/9 的 FDT magic 与 total size 检查通过；
- 所有条目 id=0、rev=0、custom[0..3]=0；
- entries 连续、无重叠、无空洞；
- Entry 2 = VD，Entry 8 = VG。

上轮 AI1 已独立解析 Entry 2 overlay，确认其 fixup 将 fragment@143:target 指向 rootparam；qcom,boardid=<8,2,0,6>、board_name=DBY_W09_VD、product_name=DBY-W09、hardware_version=SH1DBSLM 与既有 VD 记录相符。

### 3.2 需保守表述

9 个条目的 AOSP id/rev/custom 全零，标准 table metadata 无法区分条目。华为 ABL 可能使用私有机制或固定 index，但完整 ABL entry-selection control flow 本轮未重新闭合。

AI1 接受的结论：
- ENTRY_2_VD_FDT_CONTENT=PASS
- DTBO_ACTION=KEEP_STOCK_NO_WRITE
- ABL_SELECTS_ENTRY_2=SUPPORTED_BY_PRIOR_LIVE_FDT_EVIDENCE / PRIVATE_SELECTION_MECHANISM_UNKNOWN

不得声称 DTBO entry table metadata 本身能唯一选出 Entry 2。

## 4. Stock boot 尾部与 prefix write

报告提供 stock boot：100,663,296 B，SHA-256 7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8。最后 64 B、4 KiB、64 KiB、1 MiB 全零；PREP10 写入末端 46,563,215 B 到分区末端的保留区为 54,100,081 B，实测非零字节为 0；未发现末端 AVBf footer。

这支持 boot 前缀写入不会覆盖分区末尾非零数据：BOOT_PREFIX_TAIL_PRESERVATION=PASS。但这只证明尾部保护，不证明 ABL 会接受 PREP10，也不证明 kernel load 地址或认证路径正确。

脚本的 payload_end 是 DTB 末端向 4096 对齐后的值；PREP10 文件实际大小比该对齐值少 113 B。报告应将 page-aligned end 与文件 EOF/DTB 数据 EOF 分开标注。因为它另有对 [PREP10_size, partition_size) 保留区的直接零字节检查，这不影响保留区全零结论。

## 5. 关键阻塞：kernel / DTB / ramdisk load-address overlap 未分析

CORR01 对照记录：kernel_addr=0x00008000、ramdisk_addr=0x02000000、dtb_addr=0x01f00000；stock kernel_size=22,256,282 B；PREP10 kernel_size=44,820,992 B；PREP10 dtb_size=1,216,399 B；embedded ramdisk size=519,986 B。

AOSP boot header v2 文档将 kernel_addr、ramdisk_addr、dtb_addr 定义为物理加载地址，并说明 bootloader 将各组件加载到指定物理地址：
https://source.android.com/docs/core/architecture/bootloader/boot-image-header
https://android.googlesource.com/platform/system/tools/mkbootimg/+/refs/heads/main/include/bootimg/bootimg.h

按 header 字段的字面地址范围计算（此处不加入平台 base 偏移；所有区间同时平移时重叠关系不变）：

| Component | Load start | Size | End (exclusive) |
|---|---:|---:|---:|
| PREP10 kernel | 0x00008000 | 44,820,992 (0x02ABEA00) | 0x02AC6A00 |
| PREP10 DTB | 0x01F00000 | 1,216,399 (0x00128F8F) | 0x02028F8F |
| embedded ramdisk | 0x02000000 | 519,986 (0x0007EF32) | 0x0207EF32 |

PREP10 kernel 的表面范围 [0x8000,0x02AC6A00) 覆盖整个 DTB 区间，并越过 ramdisk 地址 0x02000000 约 11.3 MiB。

Stock kernel 范围 [0x8000,0x01541A9A)，结束在 DTB 地址 0x01F00000 之前。这是 PREP10 相对 stock 新增的重大风险：若按标准 header 地址直接加载，kernel 可能覆盖 DTB 和 ramdisk 区域。

这不证明实际 ABL 一定发生内存冲突。华为 ABL 可能使用动态分配、重新定位、特殊 buffer、忽略部分 header 地址，或单独处理 separate ramdisk。stock 的 DTB 与 embedded ramdisk 地址范围本身也有交叠，说明不能在不检查 ABL 行为时，把字段直接视作最终内存 map。

但由于 PREP10 kernel 比 stock 大约多 21.5 MiB，不能仅凭 header version/page size/分区容量相同就宣称加载布局兼容。

**当前写入 gate：BLOCKED_PENDING_ABL_LOAD_LAYOUT。**

必须通过 ABL PE 静态分析或已有准确日志/内存 map 证明：
1. kernel 实际 load / relocation destination；
2. DTB 的最终 buffer 地址及搬移行为；
3. separate ramdisk 从 ramdisk 分区加载到的最终地址；
4. ABL 是否为大于 32 MiB 的 raw Image 分配足够连续内存；
5. 最终各 payload 在 kernel entry 时不重叠，也不覆盖 ABL/secure/carveout/保留内存。

如果无法闭合，不得猜测新 kernel/ramdisk/DTB 地址。

## 6. 报告中另外两处需修正

1. partition_map.md 将 vbmeta 状态写成 rb_loc=2。此前 AI1 对 R155/toolkit vbmeta header 的独立解析显示，header rollback_index_location@124=0；chain partition entries 中 vbmeta_system 的 rollback index location 为 2。当前报告必须解释 rb_loc=2 指哪个字段/分区，否则更正，避免把 chain descriptor 值误记为根 vbmeta header 值。
2. §7 风险写 fastboot RAMDISK 路径曾实测进入。K1-FIRST-BOOT01 只记录 download OKAY 后出现 host-side USB write timeout，ABL handler 是否执行和 kernel handoff 均 NOT_CONFIRMED。不得写成 fastboot RAM boot 曾进入；应保持 RAMBOOT_NOT_CONFIRMED_USB_WRITE_TIMEOUT。

## 7. Restore plan 可信度

恢复方案 A（HarmonyOS/KernelSU root 环境下用完整 96 MiB stock backup 回写并读回）与参考项目 root-dd 思路一致，但要求设备仍能进入 Android/root 环境。

恢复方案 B（Fastboot flash 96 MiB stock boot）尚未在当前 GhostLock Hybrid ABL 上经本轮验证。应标记 FASTBOOT_FLASH_RESTORE=UNVERIFIED_ON_CURRENT_HYBRID_ABL。实际写入授权前，必须把主机侧原厂完整 boot backup、SHA、可访问性和独立恢复路径作为前置条件。

## 8. 修正后的状态

    PROJECT_REFERENCE_IDENTITY      = PASS
    STOCK_DTBO_IDENTITY             = PASS (executor-reported; hash listed)
    DTBO_ENTRY_METADATA_PARSE       = PASS
    ENTRY_2_VD_OVERLAY_CONTENT      = PASS
    DTBO_ACTION                     = KEEP_STOCK_NO_WRITE
    STOCK_SEPARATE_RAMDISK_ACTION   = KEEP_STOCK_NO_WRITE
    STOCK_BOOT_IDENTITY             = PASS (executor-reported; exact hash)
    BOOT_PREFIX_TAIL_PRESERVATION   = PASS
    PREP10_BOOT_V2_PARSE            = PASS
    PREP10_RELEASE_ASSET            = PRESENT; SHA256 METADATA MATCH
    ABL_KERNEL_LOAD_LAYOUT          = UNKNOWN / POTENTIAL ADDRESS OVERLAP
    BOOT_CANDIDATE                  = STRUCTURE_PASS / LOAD_LAYOUT_HOLD
    FASTBOOT_FLASH_RESTORE          = UNVERIFIED_ON_CURRENT_HYBRID_ABL
    DEVICE_WRITE_PERFORMED          = NO
    DEVICE_REBOOT_PERFORMED         = NO
    FINAL_RESULT                    = VD_DTBO_AND_PARTITION_PREFIX_READY; BOOT_WRITE_NOT_YET_APPROVED

## 9. 下一步最小任务

K1-BOOT-LOAD-MAP01：只追踪 Hybrid ABL 从 boot v2 parser 到 kernel/DTB/separate ramdisk allocation/copy/relocation 的真实路径；确认目的地址、大小、重叠处理及 memory carveout；对照 stock 22.3 MiB kernel 与 PREP10 44.8 MiB raw Image；解释参考 Linux 项目的 Image.gz / boot 地址不能直接外推到 ACK raw Image。只做静态分析，不接设备、不刷写、不重启；若无法闭合，明确 BLOCKED。

**最终审核结论：CORR01 是有效进展。VD overlay、stock DTBO/ramdisk 策略、boot 分区尾部保护与候选 Release 已具备；但 kernel 增大后的 ABL 物理加载布局尚未证明安全，当前不能批准实际 boot 分区写入。**