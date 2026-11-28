# K1_UBOOT_RECOVERY_ABL_HANDOFF_AUDIT01 — 报告

- 日期：2026-11-28；只读；无设备操作、无镜像制作、无分区写入
- ABL PE 身份：`a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`（本轮分析前已复核，与任务书一致 ✓）
- 输入证据：LOAD_MAP01 全套（dis_bootlinux_full/dis_loadramdisk/dis_updatememtree/abl_boot_strings）、CORR01 分配链、ALIGN02/CORR01、ADDENDUM01（live wrapper 解析）；本轮新增：BootLinux 调用者 BL/ptr 扫描（0 直接命中）。

## 审计 A：recovery → BootLinux

- **RECOVERY_USES_COMMON_BOOTLINUX = CONDITIONAL**。证据：(1) recovery_dtbo（boot v2 头字段 1632–1644 族）解析实证于 loader 族函数：0x4BB88（'Invalid recovery dtbo'）、0x4BCF0（'Recovery Dtbo Offset'）、0x4BD84（'Recovery Dtbo Size'）；(2) 分区选择字符串 'bootmode: %d, PartitionName %a Adjusted to %a'@0xC06CF 与 'resuce_recovery'@0xC62DD 在文件内；(3) 尾段 0x36C1C–0x388E8 为全 .text 唯一 BootLinux 尾（0x8000/0x80000 csel 唯一 @0x374AC、ExitBootServices 唯一 @0x34EA0）。**缺口（最小）**：recovery 分支→尾段的两级直接 caller/callee 链——本轮 BL 目标扫描（0x36BF0–0x36C30、0x4B640–0x4B680）与 8 字节对齐指针池均 0 命中，入口经间接机制（调用点以 vtable/寄存器持有）→ 需要一个以 `blr x?` 站点为根的寄存器数据流 pass 才能闭环。
- **RECOVERY_KERNEL_LOAD_DESTINATION = ImageBuffer + 0x80000（gz 路径，同尾段适用即同值）**；4KiB 页粒度由 gBS->AllocatePages（CORR01：helper 0x34624→唯一站点 0x3468C）保证 → **UBOOT_ENTRY_ALIGNMENT = PASS（CONDITIONAL 于 A 项链路闭合；不与 ACK 2MiB base 要求混淆——U-Boot PIE 只需 4KiB，AI1 已源码闭环）**。
- **RECOVERY_HANDOFF_FINAL_X0_FDT = CONFIRMED**（尾段 0x38868–0x3887C：`blr x8`，x8=[x20-0x70]=kload，`x0=[x20-0x58]`=TagsAddress 最终 FDT，x1=x2=x3=0——与模式无关，属共享尾段不变量）。

## 审计 B：recovery initrd 来源

- **live wrapper 身份**：`4dd6d91a…cfdbb` 本轮已复核（PREP12 W3A 与 ROUND155 primary copies 的 ramdisk.img 逐字节同哈希；采集 label=ramdisk，路径 `r155/copies-primary/`，2026-11-25）。ROUND64 的 `5c20e478…` 为旧包副本，未沿用。ADDENDUM01 已解析：v0 头、page 2048、payload@0x800 长 1,406,106、cpio newc 19 条目含 init/init.real/ksu.ko。
- **RECOVERY_INITRD_SOURCE = PARTIAL（倾向 RECOVERY_RAMDISK）**：LoadRamdisk@0x3969C 以分区 label 读取（'BootLinux: Get %a Image failed!' 的 %a 为 label 参数）；启动 recovery 时 label 切换逻辑（bootmode→label 表）未在本轮闭合。三来源严格区分：ABL 当前 recovery initrd = 待 PARTIAL；HOS Android separate ramdisk = `ramdisk` 分区（4dd6d91a）；AI1 FIT-native 候选 = 主机侧概念，未涉及本机。
- **RECOVERY_INITRD_IS_RAW_CPIO = UNKNOWN**（wrapper 头是否剥离取决于 LoadRamdisk/move_ramdisk_to_img_addr 的源偏移参数——PREP04 曾字节级证明 HOS normal 路径 kernel initrd == 分区 gzip payload（wrapper 已剥），recovery 路径未独立复核）。
- **RECOVERY_INITRD_START_END = runtime-dependent**（R 区地址依赖 ImageBuffer/ImageSize）；**FDT_INITRD_PROPERTIES = CONFIRMED（chosen 节点写入 @0x3F0F0/0x3F33C）**。

## 审计 C：UpdateDeviceTree / RAM banks / memreserve

- **ABL_UPDATEDEVICETREE_NODE = PARTIAL**：0x3D9D0 族引用 'Invalid memory configuration, check memory partition table'、'RAM Partitions'、EFI_RAMPARTITION Protocol 字符串；chosen/linux,initrd-start,end 与 kaslr-seed 写入已证（0x3F0F0/0x3F33C/0x3EFC4）。
- **ABL_FINAL_FDT_MEMORY_REG = UNKNOWN**：dis_updatememtree 420 指令窗内 'memory' 0 命中；bank 值若存在则来自运行时 EFI protocol（runtime-dependent），静态不可证非零。
- **ABL_FINAL_FDT_INITRD_MEMRESERVE = UNKNOWN**（仅 chosen start/end 已证；memreserve/reserved-memory 写入未证——**不得声称 U-Boot LMB 自动保留 initrd**）。
- **UBOOT_QCOM_EXTERNAL_FDT_FALLBACK_INPUT = conditional**（AI1 源码：internal FDT 无有效 /memory/reg 时回退 prev-BL FDT 的 qcom_parse_memory；本机 ABL 最终 FDT 的 /memory/reg 状态未证 → fallback 输入可用性未定）。

## 审计 D：最小判定（对照 AI1 固定源码点）

1. 若 recovery x0=最终 FDT 且 /memory/reg 非零 → U-Boot 内部 control DTS 可不含硬编码 /memory/reg，external fallback 生效（AI1 源码路径成立）。但 /memory/reg 非零未证 → 触发条件未证实。
2. 无有效 external /memory 时：`qcom_parse_memory()` 返回 -ENODATA → dram_init/banksize 失败 → U-Boot DRAM 初始化失败路径（AI1 源码结论）。
3. ABL initrd chosen 属性**不自动**转化为 ACK FIT FDT 可复用资源；`SAVE_PREV_BL_INITRAMFS_START_ADDR` 只保存 start 不保存 end，也无 LMB 预留——复用需 U-Boot 侧显式读取+补 end+加 reservation（最小接口：boot_get_ramdisk/boot_fdt_add_mem_rsv_regions/fdt_initrd 三点）；未证明前不建议直接复用。
4. external FDT 的 RAM bank 读取不继承其 reserved-memory/no-map/reusable/chosen 属性（AI1 已注明）。

## 未闭合项与最小证据需求

| 项 | 需要的最小证据 |
|---|---|
| recovery→BootLinux 两级调用链 | 以 `blr` 站点为根的寄存器数据流 pass（定位尾段入口的 fn-ptr 持有者） |
| recovery initrd label 切换 | bootmode→partition-label 表的 xref 窗口（LoadRamdisk 调用者参数） |
| /memory/reg 是否非零 | 本机 byte 级 final-FDT capture（设备侧只读，需授权） |
| initrd memreserve | 同上 capture 或 UpdateDeviceTree 全函数反汇编（0x3D9D0 族完整窗） |

**停止声明**：单轮有界审计完成并上传；无设备操作、无镜像制作、无分区写入；不自动开启下一轮。
