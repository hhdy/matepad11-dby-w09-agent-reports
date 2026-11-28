# K1-DBY-W09-UBOOT-CHAINLOADER-ADAPT01
## DBY-W09 U-Boot chainloader 对 ACK Android 17 的离线适配评估

- 签发：AI1
- 执行：WorkBuddy Agent（本机离线；GitHub 已接入）
- 目标：Huawei MatePad 11 DBY-W09 / HWDBY / SM8250(Kona) / 本机 VD
- 内核：ACK android17-6.18.33_r00，目标 DerpFest Android 17
- 主参考：https://github.com/CoWave-Fall/linux-on-arm-matepad11
- 辅助参考：https://github.com/svesnav/linux-dby-w09
- 性质：只读仓库/源码/已有分区备份/启动链可行性评估；不连接设备、不执行设备命令、不写分区、不修改或生成固件。

## 0. 为什么启动本任务

当前 Hybrid ABL 对直接加载 ARM64 kernel Image 的目的地址为：

    KernelLoadAddress = ImageBuffer + 0x80000

PREP10 ACK Image：
- text_offset=0
- image_size=45,547,520
- flags=0xA
- magic=0x644D5241

因此需要 ImageBuffer 物理地址满足 mod 2MiB = 0x180000。ALIGN02 的结论是 UNKNOWN；其分配器调用点还有待 CORR01 纠正。不得直接批准 PREP10 分区写入。

本轮找到另一套 DBY-W09 已运行 Linux 的项目：CoWave-Fall/linux-on-arm-matepad11。其方案不是把 Linux 内核交给华为 ABL，而是：
1. 将位置无关的 U-Boot 2026.10 封装在原厂 recovery v2 镜像中；
2. Huawei ABL 启动 U-Boot；
3. U-Boot 从 reserved3 读取 FIT；
4. U-Boot 按 FIT 描述把 Linux kernel 放到 0x91000000，DTB 放到 0x96000000，再执行 bootm。

这可能避开华为 ABL 对 Linux Image 的固定 +0x80000 放置和 PREP10 对齐矛盾。但该项目公开的实测目标是 Linux 7.3.4 + Arch Linux ARM/microSD，不是 ACK Android 17。不得直接声称现成支持 Android。

本任务只判断这条 U-Boot 链式启动路线能否适配本机 VD + ACK Android 17。优先级高于继续无限扩展 PREP10 allocator 静态分析。

## 1. 本机冻结事实

- 板级：DBY_W09_VD
- live FDT root board-id：<0x200e 0>
- rootparam：qcom,boardid=<0x08 0x02 0x00 0x06>；qcom,board_name=DBY_W09_VD
- SoC：SM8250 / Kona
- HarmonyOS：4.3.0.196(C00E100)，Android 12
- boot 分区：96 MiB，A-only，无 _a/_b suffix
- separate ramdisk 分区：2 MiB
- PREP10 boot SHA-256：d1d76c2199dff54e762bffe98260c2dfb38bb607d18a1abcec2786684bbcc46
- ACK Image SHA-256：f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21
- ACK Image size：44,820,992 B；image_size=45,547,520；text_offset=0；flags=0xA
- Hybrid ABL PE SHA-256：a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404

原厂对象策略：
- DTBO 保持本机 stock。Entry 2 是 VD，rootparam boardid=<08 02 00 06>，保持不动。
- Huawei separate ramdisk 保持原厂；不能拿 svesnav/CoWave 的 Linux initramfs 覆盖。
- 不公开 stock ABL、boot、ramdisk、recovery、vbmeta、userdata、persist、oeminfo 或其他敏感原始分区。

## 2. 必须检查的参考项目文件

### CoWave-Fall/linux-on-arm-matepad11
重点文件：
- README.md
- docs/install.md
- docs/status.md
- docs/troubleshooting.md
- uboot/dby-w09_defconfig
- uboot/patches/0004-dts-qcom-add-dby-w09.patch
- uboot/patches/0005-board-qualcomm-add-dby-w09-env.patch
- scripts/build-uboot.sh
- scripts/pack-recovery.sh
- scripts/build-kernel.sh（仅比较主线 Linux build）
- scripts/pack-fit.sh
- tools/fit/dby-w09-sd.its
- tools/host/boot-linux.sh

公开代码中值得核验的关键点：
- U-Boot 2026.10，CONFIG_POSITION_INDEPENDENT=y，CONFIG_FIT=y；
- U-Boot recovery wrapper 保留原 recovery ramdisk、dtb、recovery_dtbo；
- FIT 中 Linux kernel load/entry=0x91000000，DTB load=0x96000000；
- U-Boot 的 boot_linux 从 reserved3 读 FIT 后执行 bootm；
- U-Boot DTS qcom,board-id=<0x200e 0>，与本机 VD live FDT root board-id 相同；
- U-Boot DTS 提及 splash 地址 0x9c000000 / size 0x2300000，与本机 live FDT 记录相符。

### svesnav/linux-dby-w09
重点文件：
- README.md
- repack_boot.py
- build_dev_images.sh
- configure-and-build.sh
- tools/mkbootimg.py

只作为 direct ABL partition-flash 路线对照。其公开 overlay 使用 DBY_W09_VG（boardid 0x206a / rootparam 08 02 09 08），禁止复制到本机 VD。

## 3. 阶段 A：证明 U-Boot 可否作为 ABL 第一阶段载荷

不能只看到 CONFIG_POSITION_INDEPENDENT=y 就断言可行。必须核对 U-Boot 2026.10 源码和 defconfig：

1. ABL 对 gzip U-Boot payload 的实际分支、解压目的地址、入口跳转地址。
2. U-Boot ARM64 初始入口是否真正 position-independent；检查 startup assembly、链接地址、relocation table、relocate_code、BSS/stack 初始化。
3. CONFIG_POSITION_INDEPENDENT 的实际作用；CONFIG_SYS_INIT_SP_BSS_OFFSET=0x180000 的实际作用。
4. U-Boot 初始执行是否要求 2MiB 对齐，是否依赖固定物理地址，是否有其他 alignment/low-memory constraints。
5. 区分 U-Boot 在被 ABL 跳转前必须满足的条件，以及 U-Boot 自己 relocate 到 RAM 后的地址。
6. ABL 在 recovery v2 路径是否与普通 boot 使用同一 kernel placement；已有 PE 证据若不能证明 recovery 也相同，标 UNKNOWN。
7. U-Boot 的 control FDT 与 ABL 传入的 FDT 是否不同；recovery 镜像中的原厂 dtb/recovery_dtbo 的用途是什么。

输出：
- UBOOT_STAGE_POSITION_INDEPENDENT = CONFIRMED / CONDITIONAL / UNKNOWN
- ABL_RECOVERY_TO_UBOOT_HANDOFF = CONFIRMED / CONDITIONAL / UNKNOWN
- UBOOT_STAGE_ALIGNMENT_REQUIREMENT = 具体要求 / UNKNOWN
- ABL_TEXT_OFFSET_CONFLICT_BYPASSED = YES / NO / CONDITIONAL

## 4. 阶段 B：本机 VD 适配，不能复制 VG

对照本机 live FDT 与 CoWave U-Boot DTS：
1. qcom,msm-id 与 qcom,board-id 是否一致；特别确认 <0x200e 0>。
2. 内存 bank 范围是否与本机 live FDT 一致；列出差异，不能照抄不匹配的 RAM 总量。
3. splash reserve 0x9c000000 / 0x2300000 的 no-map、simple-framebuffer、分辨率、stride、格式是否匹配。
4. UFS、USB、UART12、PMIC GPIO、按键、SDHC2、Type-C、DRAM/LLCC/OCMEM 中第一阶段启动必需节点的差异。
5. UART12 的 clock/pinmux/handoff 仍是 HOLD；不能把 DTS status=okay 当成硬件 handoff 已证实。
6. 说明 U-Boot 实际使用的是 control FDT 还是 ABL 传入 working FDT。
7. 区分 U-Boot control FDT 和最终传给 ACK kernel 的 VD FDT，不能混为同一份 DTS。

输出 VD 适配差异表：可沿用 / 必须按 VD 修改 / 未知。

## 5. 阶段 C：reserved3 与 FIT 暂存区

CoWave 文档称 reserved3 为 24 MiB。此前本机 Fastboot gate 只明确核对了 boot 分区大小，尚未确认 reserved3 是否存在、容量、用途和 AVB 状态。

只从本机已有 partition inventory/备份元数据核查：
- reserved3 是否存在、准确 label、起始位置、大小；
- 是否 >= Android FIT 总大小；
- 是否由 HarmonyOS 挂载、是否被 AVB/vbmeta hash chain 覆盖、是否承载 OEM 数据；
- 与其他敏感分区是否重叠/别名；
- 如本机资料没有，必须标 UNKNOWN；不连接设备、不运行 getvar、不猜大小。

Android FIT 预算必须包含：
- raw ACK Image：44,820,992 B；
- 本机 VD DTB，大小从冻结候选读取；
- Android separate ramdisk 实际 initramfs payload（需先识别 mini-bootimg wrapper，再抽取正确 payload；不可把 2MiB 分区原样直接当 cpio）；
- FIT 元数据、对齐和 bootconfig/cmdline 开销。

如果最终 FIT 大于 24 MiB，明确 CoWave reserved3 方案不能直接套用。不得擅自寻找或写入其他未知分区。

## 6. 阶段 D：ACK Android 17 FIT 设计，不制作镜像

目标不是 Arch Linux SD root，而是 ACK 6.18.33 + Huawei Android first-stage init + Android 17。

设计一个静态 Android FIT spec：
1. Kernel：优先 raw ACK Image，因 U-Boot 可指定 2MiB aligned 物理 load/entry；也比较 gzip FIT decompression 路径，但说明 gzip 不会改变内层 text_offset。
2. Kernel load/entry：在本机 live FDT RAM bank 中选择 2MiB 对齐地址，至少容纳 image_size；避开 U-Boot relocation、stack、malloc、DMA、splash、secure carveout、reserved-memory、initrd、DTB。
3. DTB：必须用本机 VD ACK FDT；保持本机原厂 DTBO Entry 2 的 rootparam 选择策略；禁止使用 CoWave VG overlay。
4. Android initrd：识别本机 separate ramdisk mini-bootimg 格式，核对实际 gzip CPIO 内容、init/init.real、KernelSU 等；提出如何作为 FIT ramdisk 交给 ACK。
5. Android bootconfig：检查 ACK 6.18.33 first-stage init 对 cmdline/bootconfig 的要求；设计 U-Boot 如何传入 bootargs、initrd-start/end、FDT chosen 和 bootconfig node。
6. UFS：确认 U-Boot 是否需要扫描 UFS，Linux ACK 是否可以接管 UFS 并按 Android fstab 挂载动态分区。
7. AVB/verified boot：不要承诺 U-Boot 自动绕过 AVB；区分已知 unlocked/orange 与实际 vbmeta、dm-verity、first-stage init 的兼容性。
8. USB/early console：CoWave USB ACM console 分别在 U-Boot 与 Linux 阶段何时可用，能否观察 K1/K2。
9. 区分 kernel 能启动 Android initrd 与 DerpFest framework/vendor 完整兼容；本任务只核验 boot chain。

输出：
- ANDROID_FIT_KERNEL_LAYOUT = proposed
- ANDROID_FIT_RAMDISK_SOURCE = proven / partial / unknown
- ANDROID_BOOTCONFIG_HANDOFF = proven / partial / unknown
- KERNEL_DTB_MEMORY_NONOVERLAP = numeric / unknown
- UFS_HANDOFF = proven / partial / unknown
- AVB_AND_ANDROID_FIRST_STAGE = proven / partial / unknown
- DEBUG_OBSERVABILITY = UBOOT / KERNEL / BOTH / NONE

## 7. 阶段 E：Recovery 写入面与回滚风险（只读）

CoWave 首次部署需要写 recovery + recovery_vbmeta。比 boot-only 写入影响面大，因此必须从本机已有备份/分区清单审计：
1. recovery、recovery_vbmeta、misc 原始备份是否存在；文件大小、SHA-256、来源、备份时间。
2. recovery/recovery_vbmeta 分区大小是否已知；原厂 recovery header、page_size、kernel/ramdisk/DTB/recovery_dtbo 长度。
3. 本机 Hybrid ABL 解锁后是否可以写 recovery，只能依据本机已有证据；secure=yes/unlocked=yes 不能单独推出签名验证行为。
4. recovery_vbmeta flags=2 的确切 AVB 作用范围，不要声称关闭所有 AVB。
5. 原厂 recovery/vbmeta/misc 准确回滚条件；缺少任何关键备份则 NO-GO。
6. 区分原厂 recovery 与工具包里的 TWRP recovery，核验文件身份。
7. 说明 CoWave recovery wrapper 保留了原厂 recovery ramdisk/dtb/recovery_dtbo，只替换 kernel payload 的过程。
8. 不制作 recovery 候选、不生成 vbmeta、不打包。

## 8. 阶段 F：两种路线比较

A. Direct boot-only：
- 最少写入面；
- 使用 Hybrid ABL 直接加载 ACK Image；
- 当前 PREP10 ImageBuffer residue UNKNOWN，text_offset=0 与 +0x80000 placement 有潜在冲突；
- Image.gz 不会自动改 text_offset。

B. Recovery U-Boot chainloader + FIT：
- 初次写入面是 recovery + recovery_vbmeta；
- ABL 启动 U-Boot，不直接加载 ACK Linux Image；
- U-Boot 再把 ACK kernel 放置到明确的 2MiB aligned address；
- 需证明 U-Boot PIE/recovery handoff、VD FDT、reserved3、Android ramdisk/bootconfig/AVB；
- 后续可能通过 U-Boot Fastboot/FIT 暂存升级，而非每次改 boot 分区。

给出矩阵，别只因 B 看起来先进就选择它。若 A 可以通过 CORR01 给出静态对齐保证，也要公平比较。

## 9. 最终结论：只给一个推荐的最小行动

- 若 U-Boot chainloader 静态路径、VD board ID、RAM map 和 recovery rollback 条件满足，推荐将它作为 ACK Android 的新主线，下一步单独准备 U-Boot recovery 候选（仍不刷入）。
- 若 Android initrd/bootconfig handoff 不适配，明确最关键的一到两个阻塞项。
- 若 reserved3 不存在/不可用，说明可否用经证明安全的 U-Boot fastboot 下载缓冲方案；不得猜其它分区。
- 若 recovery 备份不完整，列出缺失的原始分区，不进入候选制作。
- 禁止无限扩大分析，输出明确 PASS/FAIL/UNKNOWN 和下一步。

## 10. GitHub 交付

仓库：hhdy/matepad11-dby-w09-agent-reports
目录：firmware-analysis/boot-v2/uboot-chainloader-adapt01/

提交：
- K1_DBY_W09_UBOOT_CHAINLOADER_ADAPT01_REPORT.md
- comparison_matrix.csv
- vd_dts_diff.md
- android_fit_layout.md
- recovery_rollback_inventory.csv
- evidence_matrix.csv
- SHA256SUMS.txt
- 必要的脱敏脚本/来源清单。

提交后逐项从 GitHub 读回，记录 commit SHA、blob SHA、内容校验。不要公开任何原始分区 dump。

## 11. 严格禁止

- 不连接平板，不查询设备，不切换 recovery/fastboot。
- 不执行 ADB/Fastboot/OEM 命令。
- 不刷写 recovery/recovery_vbmeta/boot/ramdisk/DTBO/reserved3/misc/vbmeta。
- 不重启，不进行 EDL/HiSuite/TWRP 操作。
- 不修改原始镜像或候选。
- 不重编 ACK 内核，不改 head.S，不生成 FIT/recovery 候选。
- 不将 CoWave VG overlay 或 Linux rootfs/initramfs 写入本机。
- 不公开原始分区和设备敏感数据。

## 12. 停止条件

- 完成两种路线的静态可行性比较和 Android FIT 设计后立即停止。
- 当前资料不能证明的分区用途、运行时地址、AVB 状态必须 UNKNOWN。
- 交 AI1 独立审核；不因本任务结果自动获得任何设备写入授权。

本任务目标：评估一条不依赖 Huawei ABL 直接加载 ACK Linux Image 的启动路线；不制作镜像、不授权写入。


---

## 13. AI1 研究补充 / 任务收敛修订（2026-11-28）

本节优先于前文中与现有证据不符或已经被 AI1 源码核验的表述。不要重复进行已经闭环的通用源码审查。

### 13.1 reserved3 已经确认，不要再要求设备查询

现有 PREP12 只读分区 inventory 的准确记录位于：
`firmware-analysis/boot-v2/linux-port-adapt01-corr01/partition_map.md`

其中已确认：
- label：`reserved3`
- block device：`/dev/block/sda13`
- size：25,165,824 B（24 MiB）

因此本任务不能再写“尚未确认 reserved3 是否存在/容量”。不得连接设备重新查询。仍然未知的是该分区当前内容、OEM 用途/保护策略、能否安全覆盖；没有原始备份和使用情况核验，不得写入。

### 13.2 ARM64 Linux FDT memory fixup 已有上游代码闭环

AI1 已独立核验 U-Boot v2026.10：
- `arch/arm/lib/bootm-fdt.c::arch_fixup_fdt()` 使用 `gd->dram[]` 调用 `fdt_fixup_memory_banks()`；
- `boot/image-fdt.c::image_setup_linux()` 调用该 arch fixup；
- Qualcomm `arch/arm/mach-snapdragon/board.c::board_fdt_blob_setup()` 在 internal FDT 有效时优先从 internal FDT 的 `/memory/reg` 运行 `qcom_parse_memory()`；`dram_init_banksize()` 再把 banks 复制到 `gd->dram[]`。

CoWave dby-w09 defconfig 已见：
- `CONFIG_ARCH_SNAPDRAGON=y`
- `CONFIG_NR_DRAM_BANKS=24`
- `CONFIG_FIT=y`
- `CONFIG_OF_BOARD_SETUP=y`

CoWave patch 0004 internal U-Boot control DTS 给出三个固定 RAM tuples：
- `0x80000000 + 0x3BB00000`
- `0xC0000000 + 0xC0000000`
- `0x180000000 + 0x100000000`

因此，U-Boot 可以在 Linux 交接前自动把其 DRAM bank ranges 写入 FIT 内的 ACK DTB，原始 ACK `/memory/reg=<0 0 0 0>` 不是不可解问题。

**但是**这些固定 tuples 在本机 HOS4.3 的最终 ABL memory map 中尚无独立可核验 capture。ROUND64 Phase E 将 `/sys/firmware/fdt` 读取记为 Permission denied；stock base DTB 的 memory 仍是 placeholder。故 CoWave tuples 对本机只能判 CONDITIONAL，不能报告为本机 RAM 已验证。

### 13.3 本轮最有价值的剩余工作

不要再审查 generic ARM memory fixup 本身。只聚焦：
1. 三段 CoWave RAM tuples 的真实来源，是否为同一 RAM SKU 的 DBY-W09 live final FDT；不能只引用 DTS 注释；
2. U-Boot 最终 .config 的 CONFIG_OF_LIBFDT / CONFIG_ARCH_SNAPDRAGON / CONFIG_NR_DRAM_BANKS / CONFIG_FIT / CONFIG_CMD_BOOTM / CONFIG_ANDROID_BOOT_IMAGE 实际值；
3. 将 ACK candidate DTB 的 37 个 reserved-memory children 与现有 HOS4.3 证据做脱敏逐项对比（name / size / no-map / reusable / consumer 类别），不要公开原始物理地址；
4. 核算 Android FIT 的 kernel gzip 实际尺寸能否连同 VD DTB 和 FIT 元数据放入已知 24 MiB reserved3。原始 ACK Image 44,820,992 B 不能未经压缩直接放入。

AI1 已提交两份源码结果供参考：
- `AI1_UBOOT_ANDROID_FIT_SOURCE_FINDINGS.md`
- `AI1_UBOOT_FDT_MEMORY_FIXUP_SUPPLEMENT.md`

### 13.4 仍然不得做的事项

保持本任务原有全部禁止事项：不得连接设备、ADB/Fastboot/OEM 命令、reboot、fastboot boot、分区写入、刷写、构建 U-Boot/FIT/recovery、生成候选或公开固件二进制。此补充不改变任何操作授权。
