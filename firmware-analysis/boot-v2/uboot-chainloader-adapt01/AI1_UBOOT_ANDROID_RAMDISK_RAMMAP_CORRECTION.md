# AI1 — U-Boot Android ramdisk handoff 与扩容 RAM map 修正报告

- 日期：2026-11-28
- 目标：Huawei MatePad 11 2021 DBY-W09 / VD / HOS4.3 / ACK android17-6.18.33
- 固定 U-Boot 参考：U-Boot v2026.10
- 范围：只读核对 U-Boot 上游源码与 CoWave 同型号公开实现；不连接设备、不运行 ADB/Fastboot、不构建或生成镜像、不修改分区。
- 本报告修正此前 AI1_UBOOT_ANDROID_FIT_SOURCE_FINDINGS.md 对“外置 Android ramdisk wrapper 可直接作为 bootm 第二参数”的过度推断。

## 1. 结论摘要

U-Boot 作为 ABL 后的第二启动级仍然是值得保留的主候选：U-Boot ARM64 PIE 的入口约束是 4 KiB 对齐，不是 Linux ACK Image 的 2 MiB 对齐约束；它可以在自己的 bootm 路径中把 ACK Image 放到 2 MiB 对齐地址。

但 Android 17 的 ramdisk 交接方案必须修正，且 CoWave 的静态 RAM map 不能直接用于本机扩容设备。

当前判断：

| 项目 | 判断 | 说明 |
|---|---|---|
| U-Boot PIE 入口对齐 | 源码 CONFIRMED：4 KiB | start.S 有 4 KiB 运行时断言 |
| U-Boot PIE 重定位 | 源码 CONFIRMED | early RELA fixup + 后续 relocate_code |
| U-Boot 规避 ABL 对 Linux Image 的 +0x80000 放置冲突 | CONDITIONAL GO | 需 ABL recovery 路径确实能把 U-Boot 交给它 |
| Android wrapper 直接作为 bootm 第二参数、未设置 abootimg 全局地址 | NO-GO | Android image 分支使用 abootimg 全局地址；但先执行 abootimg addr wrapper 后可用同一 wrapper 地址作为第二参数 |
| CMD_ABOOTIMG 外置 wrapper 路径 | 源码机制 CONFIRMED；目标 live wrapper 待核 | CMD_ABOOTIMG=y + abootimg addr wrapper + bootm FIT wrapper |
| 提取 payload 后 addr:size | 源码机制 CONFIRMED（需 SUPPORT_RAW_INITRD） | raw 数据格式识别失败后会进入 raw-initrd 分支；不会因前置 FIT parser 解析冒号而提前退出 |
| abootimg 提取 ramdisk | 源码机制 CONFIRMED | header v0-v2 可返回原始 ramdisk payload 地址/长度 |
| 提取后用 addr:size 直接作为 FIT bootm 第二参数 | 当前源码路径 NO-GO | FIT 子镜像解析先吞掉冒号 |
| CoWave 8 GiB 静态 RAM tuples 用于当前扩容设备 | NO-GO | tuple 总量约 7.93 GiB，不能覆盖用户报告的 12GB RAM |
| ACK Android 第一启动包 | NO-GO | 仍缺 live ramdisk header、正确 ramdisk 参数路径、真实 RAM map、保留区与 AVB/恢复闭环 |

## 2. U-Boot PIE：4 KiB 是入口约束，不是 2 MiB

U-Boot v2026.10：

- arch/arm/cpu/armv8/start.S 在 CONFIG_POSITION_INDEPENDENT 下读取运行时 _start，检查低 12 位；非 4 KiB 对齐会进入 WFI 死循环。
- 紧接着执行 pie_fixup，遍历 __rel_dyn_start 到 __rel_dyn_end，对 R_AARCH64_RELATIVE relocation 应用运行时相对偏移。
- arch/arm/cpu/armv8/start.S 的 4 KiB 检查与 Linux ARM64 Image 的 2 MiB base alignment 是两个不同契约。
- arch/arm/Kconfig 中 INIT_SP_RELATIVE 在 POSITION_INDEPENDENT=y 时默认启用（ARCH_QEMU 除外）；SYS_INIT_SP_BSS_OFFSET 依赖 INIT_SP_RELATIVE。
- CoWave dby-w09_defconfig 明确设置 POSITION_INDEPENDENT=y、SYS_INIT_SP_BSS_OFFSET=0x180000。按该 Kconfig 默认规则，早期 SP 由运行时 __bss_start + 0x180000 计算，而不是硬编码物理地址；仍需以最终构建 .config 读回结果为准。
- arch/arm/lib/crt0_64.S 展示了这个相对 stack 计算，之后 board_init_f() 选定顶端 RAM 的 relocation destination，再由 relocate_code() 搬迁 U-Boot。

因此，只要 ABL 解压 U-Boot 的实际入口地址保持 4 KiB 对齐，U-Boot 的 PIE 入口并不要求 2 MiB 对齐。若 ABL 的 ImageBuffer 由 4 KiB 页分配得到，额外 +0x80000 仍保持 4 KiB 对齐；但这只是地址算术，不能代替对 HOS4.3 ABL recovery 分支实际解压目的地址和跳转点的二进制证据。

上游来源：
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/cpu/armv8/start.S
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/lib/crt0_64.S
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/lib/relocate_64.S
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/Kconfig

## 3. Android separate ramdisk：wrapper 不能直接作为 FIT bootm 第二参数

### 3.1 对此前方案的源码纠正

此前报告建议将 Android separate ramdisk wrapper 的地址直接作为：

    bootm <FIT_ADDR> <ANDROID_RAMDISK_WRAPPER_ADDR>

这条推断不成立。

U-Boot v2026.10 boot/image-board.c 的 select_ramdisk() 会先识别第二参数指向的镜像格式。如果它是 IMAGE_FORMAT_ANDROID，后续 Android 分支调用 android_image_get_ramdisk() 时，在没有 CMD_ABOOTIMG 特殊路径的情况下使用 images->os.start；即主启动镜像的地址，而不是第二参数 rd_addr。启用 CMD_ABOOTIMG 时也会读取 get_abootimg_addr()/get_ainit_bootimg_addr() 全局地址，不是自动把第二参数视为任意 Android wrapper。

因此不能宣称 Android wrapper 地址可直接作为 bootm 外置 initrd 参数。

源码：
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-board.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/bootm.c

### 3.2 U-Boot 已提供的 wrapper payload 提取 API

U-Boot v2026.10 的 cmd/abootimg.c 提供：

    abootimg addr <ANDROID_WRAPPER_ADDR>
    abootimg get ramdisk <RAMDISK_ADDR_VAR> <RAMDISK_SIZE_VAR>

abootimg get ramdisk 调用 android_image_get_ramdisk()，把返回的 payload 地址和长度写入环境变量。

对 Android boot header v0-v2：
- android_image_get_data() 从 header page size、kernel_size 等字段计算 ramdisk payload offset/length；
- android_image_get_ramdisk() 可以返回原始 ramdisk payload 的地址和长度；
- ARCH_SNAPDRAGON 在 arch/arm/Kconfig 中 select ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR，因此旧式 v0-v2 wrapper 的 ramdisk_addr 不会强制将 payload 搬到 header 声明的固定 DDR 地址，而是允许在 wrapper 当前缓冲区内原位引用。
- Android header v3+ 需要 vendor_boot image；当前设备没有已确认的 vendor_boot 分区，不能假定这一分支适用。

但当前 live separate ramdisk 备份虽然已有文件 SHA 记录，header version、page_size、kernel_size、ramdisk_size、payload offset/length 仍必须按当前 live backup 的精确 SHA 重新核验。此前 ROUND2/ROUND64 的固件包副本 header-v0 不能代替 live backup 的身份核验。

源码：
- https://github.com/u-boot/u-boot/blob/v2026.10/cmd/abootimg.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-android.c
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/Kconfig

### 3.3 重新核对：addr:size 在当前 FIT 流程中可以进入 raw-initrd 分支

此前曾把 fit_parse_subimage() 找到冒号理解成提前结束，这个结论不正确。必须按 select_ramdisk() 完整控制流判断：

1. CONFIG_FIT=y 时，select_ramdisk() 先调用 fit_parse_conf() 和 fit_parse_subimage()。若参数包含冒号，fit_parse_subimage() 会把冒号后部分记录为 FIT subimage name，并设置 done_select=true。
2. 随后代码仍会调用 genimg_get_format() 检查 rd_addr 指向的实际内存。
3. 如果地址指向真正的原始 CPIO / gzip initramfs payload，而不是 FIT 容器，genimg_get_format() 不会返回 IMAGE_FORMAT_FIT，switch 也不会设置 done。
4. switch 之后，若 CONFIG_SUPPORT_RAW_INITRD=y，代码会再次查找 select 中的冒号，读取冒号后的十六进制长度，并把 rd_addr / rd_len 作为 raw initrd。
5. 因此 raw payload 的 addr:size 在 CONFIG_FIT=y 情况下仍是源码支持的路径；前置 fit_parse_subimage() 没有使函数提前返回。

真正的限制是：
- 整个 ANDROID! wrapper 不能在未设置 abootimg 全局地址时直接作为第二参数；Android-format 分支不会仅凭 rd_addr 自动解析任意外部 wrapper。
- addr:size 必须指向已经提取的 raw ramdisk payload，而不是 Android mini-bootimg wrapper header。
- 必须显式启用 CONFIG_SUPPORT_RAW_INITRD=y，并在 host/sandbox 上验证真实 payload 格式和参数路径。

来源：
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-board.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-fit.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/Kconfig

### 3.4 首选现成 U-Boot 路径：CMD_ABOOTIMG 设置外部 wrapper 全局地址

无需改 U-Boot parser，也不必先嵌入 FIT。若先把 live Android wrapper 读到 RAM，现有命令/bootm 路径可按以下方式组合：

```text
abootimg addr <ANDROID_WRAPPER_ADDR>
bootm <FIT_ADDR> <ANDROID_WRAPPER_ADDR>
```

机制：
1. CMD_ABOOTIMG=y 时，abootimg addr 设置 U-Boot 全局 abootimg 地址。
2. bootm 的第二参数为普通十六进制地址（不加冒号），select_ramdisk() 先按该地址读取格式；wrapper magic 识别为 IMAGE_FORMAT_ANDROID。
3. Android-format 分支在 CMD_ABOOTIMG=y 时调用 android_image_get_ramdisk()，其输入取自 get_abootimg_addr()，即上一步设置的外置 wrapper 地址。
4. 对 header v0-v2，android_image_get_ramdisk() 计算 ramdisk payload pointer/size。ARCH_SNAPDRAGON 会选择 ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR，忽略 wrapper 内旧的固定 ramdisk 地址，返回 wrapper 内实际 payload 的位置。
5. boot_get_ramdisk() 随后把得到的 payload range 传给 boot_ramdisk_high()；默认路径使用 LMB 分配安全目的区并复制 ramdisk。image_setup_libfdt() 最终调用 fdt_initrd()，为 initrd 添加 FDT memreserve 并写 /chosen/linux,initrd-start/end。

因此：
- “直接把 wrapper 当作第二参数、未先执行 abootimg addr”仍然不可依赖；
- “先 abootimg addr wrapper，再 bootm FIT wrapper”是 U-Boot v2026.10 源码支持的组合；
- 本机 live wrapper 的 header、payload 长度、mini-bootimg 版本和目标 U-Boot 构建配置仍需按精确 SHA 核验，当前不能宣称设备已可启动。

相关源码：
- https://github.com/u-boot/u-boot/blob/v2026.10/cmd/abootimg.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-board.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-android.c
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/Kconfig
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/fdt_support.c

### 3.5 备用路线：先提取 payload，再走 SUPPORT_RAW_INITRD

若不希望 bootm 的第二参数处于 Android image format 分支，可以显式提取地址/长度：

```text
abootimg addr <ANDROID_WRAPPER_ADDR>
abootimg get ramdisk rd_data rd_size
bootm <FIT_ADDR> ${rd_data}:${rd_size}
```

这条路径要求：
- CONFIG_ANDROID_BOOT_IMAGE=y
- CONFIG_CMD_ABOOTIMG=y
- CONFIG_SUPPORT_RAW_INITRD=y
- wrapper 必须是 U-Boot 当前 parser 支持的有效 Android header（本机优先核验 v0-v2）
- rd_data 指向真正的 raw initramfs payload；rd_size 是 payload 长度，不是整个 wrapper 大小。

其优点是第二参数会指向原始 payload；U-Boot 即使先尝试 FIT 语法，随后也会因实际数据不是 FIT image 而进入 SUPPORT_RAW_INITRD 分支。这个路径不要求修改 fit_parse_subimage()。

### 3.6 FIT-native ramdisk 仍是可选方案

若希望启动文件完全自包含，或外置 wrapper/parser 路径在 host/sandbox 验证中出现问题，可以在 FIT 中增加 ramdisk image 节点，并在配置节点设置 ramdisk = "ramdisk"。

预算仍需满足：

gzip(ACK Image) + exact live CPIO payload + exact ACK VD DTB + FIT metadata/alignment <= 25,165,824 B。

此前固件包副本中的 1,322,962 B 只能作为预算示例，不能代替当前 live ramdisk payload 的长度。FIT-native 方案不是由于 addr:size 解析限制而被强制采用。

### 3.5 CoWave defconfig 不是 Android 完整配置

CoWave scripts/build-uboot.sh 只安装 uboot/dby-w09_defconfig、应用五个板级补丁，再执行 dby-w09_defconfig 和编译，没有额外 Android Kconfig fragment。

当前公开 dby-w09_defconfig：
- CONFIG_FIT=y
- CONFIG_USB_FUNCTION_FASTBOOT=y
- 未显式设置 CONFIG_CMD_ABOOTIMG=y
- 未显式设置 CONFIG_SUPPORT_RAW_INITRD=y
- 未显式设置 CONFIG_ANDROID_BOOT_IMAGE=y（虽 ANDROID_BOOT_IMAGE 在 FASTBOOT 时有默认 y，但必须检查最终 .config）

Android 适配应显式配置并回读：
- CONFIG_ANDROID_BOOT_IMAGE=y
- CONFIG_CMD_ABOOTIMG=y
- CONFIG_SUPPORT_RAW_INITRD=y（若采用 abootimg get ramdisk + addr:size raw payload 路线）
- CONFIG_FIT=y
- CONFIG_CMD_BOOTM=y
- CONFIG_OF_LIBFDT=y
- CONFIG_ARCH_SNAPDRAGON=y
- CONFIG_POSITION_INDEPENDENT=y
- CONFIG_INIT_SP_RELATIVE=y

这里不需要为了 addr:size 修改 FIT 解析器；但必须确保第二参数指向 raw payload，而不是整个 Android wrapper。若使用 3.4 的 CMD_ABOOTIMG 方案，则可将 wrapper 作为第二参数，但必须事先执行 abootimg addr wrapper。

CoWave 来源：
- https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/scripts/build-uboot.sh
- https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/uboot/dby-w09_defconfig

## 4. CoWave 固定 RAM map 不适用于直接照搬的当前设备

CoWave 公开 patch 0004 的 internal control DTS 含三段 /memory/reg：

| Bank | Start | Size | End-exclusive |
|---|---:|---:|---:|
| 0 | 0x80000000 | 0x3BB00000 | 0xBBB00000 |
| 1 | 0xC0000000 | 0xC0000000 | 0x180000000 |
| 2 | 0x180000000 | 0x100000000 | 0x280000000 |

三段 size 总和：
- 955 MiB + 3072 MiB + 4096 MiB = 8123 MiB
- 即约 7.93 GiB，不是 12 GiB。

这台目标设备此前已报告做过 RAM 扩容、系统 RAM 为 12GB。因此 CoWave 这组三段固定 tuples 不能直接照抄作为本机 U-Boot 的内存来源；如果照搬，至少可能遗漏实际可用 RAM，且 Linux 最终 /memory 将由 U-Boot gd->dram[] 重写。

关键源码控制流：
- arch/arm/mach-snapdragon/board.c::board_fdt_blob_setup() 优先对 internal FDT 执行 qcom_parse_memory()；
- 只有 internal FDT 无有效 /memory/reg 时，才 fallback 到 get_prev_bl_fdt_addr() 的 previous-bootloader external FDT；
- arch/arm/lib/bootm-fdt.c::arch_fixup_fdt() 会把 gd->dram[] 写回最终 Linux FDT 的 /memory/reg；
- boot/image-fdt.c::image_setup_linux() 在 bootm 流程中调用 arch_fixup_fdt()。

因此，不能只修 ACK FDT 的零值 /memory/reg 就算完成；真正权威的是 U-Boot 用来填充 gd->dram[] 的 bank map 是否与这台 12GB 扩容设备的 HOS4.3 实际 RAM map 相符。

潜在方向（仅设计，不执行）：
- 若 recovery ABL 确实把准确的 final FDT 通过 previous-bootloader FDT pointer 交给 U-Boot，可评估从 internal control DTS 移除 /memory/reg，使 qcom_parse_memory() fallback 到 external FDT；
- 或从本机 HOS4.3 最终 memory map 取得精确 bank tuples，更新 internal control DTS；
- 不允许把 CoWave 8GB tuples、设备宣传参数或普通 /proc/meminfo 总量替代为物理 bank map；
- final FDT 的 reserved-memory、no-map/reusable、secure carveout 仍须逐项核对，不能因 RAM banks 正确就宣称 memory handoff 完成。

来源：
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/mach-snapdragon/board.c
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/lib/bootm-fdt.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-fdt.c
- https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/uboot/patches/0004-dts-qcom-add-dby-w09.patch

## 5. CoWave 实测范围与当前目标差异

CoWave 仓库公开 README/status 记载其实际启动链为 U-Boot 2026.10 -> Linux 7.3.4 -> Arch Linux ARM / microSD；其验证系统记为 HarmonyOS 4.2。它能证明同型号设备上 U-Boot recovery chainloader 的总体方向有实机先例，但不证明：
- 本机 HOS4.3 ABL 的 recovery kernel 分支和解压/跳转地址完全相同；
- 当前 12GB 扩容设备 RAM map 与 CoWave internal DTS 相同；
- 本机 separate ramdisk live wrapper 的头字段与旧版 CoWave/固件包副本一致；
- Android 17 first-stage init、ACK 6.18.33 UFS 接管、AVB/vbmeta 与 bootconfig 已可工作。

来源：
- https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/docs/status.md
- https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/README.md

## 6. 下一步收敛建议

不要再重复通用 U-Boot PIE 或 generic ARM FDT fixup 的源码审查。下一步按以下顺序闭合：

1. 本机 live separate ramdisk（精确 SHA）离线解析：header version、page_size、kernel_size、ramdisk_size、payload offset/length、payload magic/压缩格式；只上传脱敏字段和哈希，不上传固件本体。
2. 本机 HOS4.3 recovery previous-bootloader FDT 的来源和有效性；确认是否能提供准确的 12GB RAM banks。若无可核验 final FDT，就保持 UNKNOWN。
3. 优先验证现成 CMD_ABOOTIMG 路径：abootimg addr wrapper + bootm FIT wrapper；同时用 U-Boot sandbox 测试 payload/addr:size 备用路径。只有这两条现成源码机制有缺陷时，才考虑改 parser 或 FIT-native 节点。
4. 最终 U-Boot .config readback，确认 PIE、relative SP、FIT、bootm、Android parser、raw-initrd 配置。
5. 只有当 RAM banks、reserved-memory、ramdisk 交接、Android bootargs/bootconfig、UFS handoff、recovery rollback 都有证据后，才进入主机端 boot package 设计。

本报告未批准启动、fastboot、recovery 写入、临时启动、分区写入或刷机。没有执行任何设备命令，也没有生成或修改镜像。

## 3.6 Further source closure — existing `CMD_ABOOTIMG` pointer override avoids the proposed patch/embed workarounds

A later direct control-flow review identified a narrower option that was not captured in §3.4: enable `CONFIG_CMD_ABOOTIMG=y`, then explicitly point the command's global Android-image address at the external wrapper before calling `bootm`.

```text
abootimg addr ${ramdisk_wrapper_addr}
bootm ${fit_addr} ${ramdisk_wrapper_addr}
```

Why this is different from the original NO-GO:
- The original failure is real when `CMD_ABOOTIMG` is disabled, or when the `abootimg` global address is not set to the same external wrapper.
- With `CMD_ABOOTIMG=y`, `select_ramdisk()` uses `get_abootimg_addr()` in the Android-format branch. `abootimg addr` sets that global address to the external wrapper buffer.
- The second `bootm` argument is still required as a plain hexadecimal address so `select_ramdisk()` recognizes the buffer's Android image format and enters the Android branch.
- Do not use `addr:size`: with `CONFIG_FIT=y`, U-Boot tries `fit_parse_conf()` (`#`) and `fit_parse_subimage()` (`:`) first. A colon is treated as a FIT subimage separator. A plain hex address has neither separator and falls through to `hextoul()` correctly.
- `ARCH_SNAPDRAGON` selects `ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR`; for a valid Android wrapper header v0-v2, the parser returns the ramdisk payload address inside the wrapper instead of honoring the stale header RAM address. The normal bootm initrd relocation/FDT handoff can then handle placement.

This means the current first-choice implementation does **not** require a custom `boot/image-board.c` parser patch and does **not** require embedding the ramdisk in the FIT. It still requires `CONFIG_CMD_ABOOTIMG=y`, explicit `abootimg addr` setup, a plain-address second argument, exact live wrapper header validation, and a verified scratch/final initrd memory range.

Source-level implementation details and the full command design are recorded in:
`AI1_UBOOT_EXTERNAL_ANDROID_RAMDISK_HANDOFF_FIX.md`.

Updated disposition:
- Generic `bootm FIT_ADDR wrapper_addr` without an explicit `abootimg addr` setup: **NO-GO**.
- `CONFIG_CMD_ABOOTIMG=y` + `abootimg addr wrapper_addr` + `bootm FIT_ADDR wrapper_addr`: **SOURCE-CONFIRMED WORKAROUND; live-wrapper compatibility remains UNKNOWN/HOLD**.
- Candidate A (patch raw-initrd syntax) and candidate B (FIT ramdisk node) remain fallback designs only if host/sandbox validation finds a defect in the existing `CMD_ABOOTIMG` route.
