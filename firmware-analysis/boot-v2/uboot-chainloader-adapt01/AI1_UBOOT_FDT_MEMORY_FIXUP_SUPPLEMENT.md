# AI1 U-Boot FDT Memory Fixup 补充核验

- 日期：2026-11-28
- 适用路线：CoWave U-Boot chainloader → ACK Android 17 FIT
- 本文补充并细化 AI1_UBOOT_ANDROID_FIT_SOURCE_FINDINGS.md 的 RAM handoff 章节。
- 范围只限公开 U-Boot v2026.10 源码、CoWave 已提交配置/patch 和本仓库既有本机证据。

## 1. 先前疑问的源码闭环：最终 Linux /memory 并非只靠 ft_board_setup

U-Boot v2026.10 的 ARM 代码 arch/arm/lib/bootm-fdt.c::arch_fixup_fdt() 在 CONFIG_OF_LIBFDT 启用时，会遍历 gd->dram[0..CONFIG_NR_DRAM_BANKS-1]，然后调用 fdt_fixup_memory_banks() 写入待启动 Linux FDT 的 /memory/reg。

该函数由 boot/image-fdt.c::image_setup_linux() 调用。因此：
- 即使 FIT 内 ACK DTB 的原始 /memory/reg 是全零占位；
- 只要 U-Boot 自己的 DRAM bank 已正确初始化；
- 在 bootm 最终交给 Linux 前，generic ARM64 fixup 可以把 U-Boot 的 RAM banks 写入 ACK FDT。

这意味着不能简单以“ACK DTB 中 /memory 为零”断言 U-Boot 路线无法启动。真正硬条件是 U-Boot 的 gd->dram[] 必须准确反映本机实际 RAM bank，并与最终 DTB 的 reserved-memory 节点相容。

源码：
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/lib/bootm-fdt.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-fdt.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/fdt_support.c

## 2. CoWave Snapdragon 内存来源的具体路径

CoWave uboot/dby-w09_defconfig 确认：
- CONFIG_ARCH_SNAPDRAGON=y
- CONFIG_NR_DRAM_BANKS=24
- CONFIG_FIT=y
- CONFIG_OF_BOARD_SETUP=y

CoWave patch 0004-dts-qcom-add-dby-w09.patch 的 internal control DTS 内置三个 /memory tuples：

| bank | start | size | end-exclusive |
|---|---:|---:|---:|
| 0 | 0x80000000 | 0x3BB00000 | 0xBBB00000 |
| 1 | 0xC0000000 | 0xC0000000 | 0x180000000 |
| 2 | 0x180000000 | 0x100000000 | 0x280000000 |

在 U-Boot v2026.10 的 arch/arm/mach-snapdragon/board.c：
1. board_fdt_blob_setup() 先检查 U-Boot internal FDT 和上一阶段 external FDT；
2. 如果 internal FDT 有效，优先调用 qcom_parse_memory(internal_fdt)；
3. 只有 internal FDT 没有有效 memory 时，才 fallback 到 previous bootloader external FDT；
4. qcom_parse_memory() 逐项解析 /memory/reg，保存到 prevbl_ddr_banks[]，并设置 gd->ram_base/gd->ram_size；
5. dram_init_banksize() 在 relocation 后把这些 bank 复制到 gd->dram[]。

因此，按照当前 CoWave 配置，U-Boot 的 DRAM banks 将优先来自其打包的 internal control DTS，而不是自动继承 HOS4.3 ABL 的最终 memory map。随后 generic ARM arch_fixup_fdt() 会把同一组 gd->dram[] ranges 写入 ACK Linux FDT。

源码：
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/mach-snapdragon/board.c
- https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/uboot/patches/0004-dts-qcom-add-dby-w09.patch
- https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/uboot/dby-w09_defconfig

## 3. 与本机已有 HOS4.3 证据交叉检查

本机 ROUND64 Phase E 明确记录：
- 唯一候选 post-ABL final FDT /sys/firmware/fdt 在 ROUND2 因权限不足读取失败；
- stock base FDT 的 /memory/reg 是全零 placeholder，不是可用 RAM map；
- stock base FDT 有 34 个 reserved-memory children（ROUND24 对直接子节点计数曾更新为37，后续 ACK 候选 DTS 中也记载37）；
- final post-ABL RAM tuples 和 reservation attributes 都是 BLOCKED。

来源：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round64/round64-dby-w09-hos43-final-memory-and-pm8150-input-evidence.md

CoWave 的 U-Boot DTS 注释声称三段 RAM range“取自设备运行时设备树”，并且公开项目报告在同型号硬件上已成功启动 Linux；这构成很强的同设备参考证据，但目前本仓库没有可逐字节核验的 CoWave 实测 RAM capture，也没有本机 HOS4.3 final FDT。因此不能将 CoWave 三段 tuple 直接升级为本机 HOS4.3 已验证事实。

另一个关键点：CoWave 的 Linux FIT DTS 使用的是 Linux 内核 FDT。U-Boot 对它做 memory fixup，并不意味着 U-Boot control DTS 的 /reserved-memory 会自动整体复制到 Linux FDT；最终 Linux DTB 仍须携带正确的 HOS4.3 reserved-memory nodes、ranges、no-map/reusable 属性。当前 ACK candidate DTS 记载37个 children，但它们的每个地址/属性还没有与真实 HOS4.3 final handoff 逐项核对。

## 4. 更新后的判断

| 项目 | 新判断 |
|---|---|
| U-Boot 是否能自动修正 ACK FDT 的 /memory/reg | 源码机制 CONFIRMED：由 ARM arch_fixup_fdt() 基于 gd->dram[] 写入 |
| CoWave U-Boot 的 RAM 来源 | CONFIRMED：默认优先 internal control DTS 的静态 /memory，而非 HOS4.3 final FDT |
| CoWave 三段 RAM tuples 是否已证明适用于本机 HOS4.3 | CONDITIONAL：同型号公开实测参考，但本机 final FDT 仍无可核验证据 |
| U-Boot 能否直接借用 ABL final memory map | 默认不能假设：internal FDT valid 时 Snapdragon board code 优先用 internal |
| ACK Linux DTB 的 /memory 全零能否由 U-Boot fixup 解决 | YES，条件式：U-Boot DRAM bank 正确，且 ARM OF/FDT fixup 生效 |
| ACK Linux DTB 的37个 reserved-memory children 是否正确 | UNKNOWN/HOLD：需核对各节点地址、大小、no-map/reusable 与 HOS4.3 runtime reservation |
| FIT kernel/initrd/FDT/splash 地址无重叠是否已完整证明 | UNKNOWN：只有拟议静态地址算术通过，未计入全部真实 carveouts |

## 5. 当前最有效的下一步

不要再重新审查整个 U-Boot memory framework。若本机 WorkBuddy 任务仍在执行，要求其只补交以下证据即可：

1. CoWave 原始来源中三段 RAM tuple 的 provenance（是否从 DBY-W09 同一硬件、同一 RAM SKU 的 live FDT 读取，还是静态推定）；
2. U-Boot 编译后的最终 .config 证明 CONFIG_OF_LIBFDT、CONFIG_ARCH_SNAPDRAGON、CONFIG_NR_DRAM_BANKS=24、CONFIG_OF_BOARD_SETUP、CONFIG_CMD_BOOTM、CONFIG_FIT 的最终值；
3. 对照 ACK candidate FDT 的37个 reserved-memory children，逐项输出脱敏 name / size / flags / source，不公开物理地址；判断是否存在对 CoWave kernel/FIT/ramdisk/FDT/splash 区间的碰撞；
4. 若没有本机 final memory map，明确维持 UNKNOWN，不准以重复静态搜索代替。

## 6. 安全边界

本补充没有访问平板，没有执行任何 ADB/Fastboot/boot/reboot 命令，没有构建 U-Boot/FIT/recovery，没有修改任何镜像或分区，没有授权任何写入。