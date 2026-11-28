# AI1 — U-Boot Android FIT 路线源码补充核验

- 日期：2026-11-28
- 目标：Huawei MatePad 11 DBY-W09 / VD / SM8250，ACK android17-6.18.33
- 范围：CoWave U-Boot chainloader 的上游 U-Boot 源码核验；只读分析，不生成镜像、不连接设备。
- 参考任务书：`K1_DBY_W09_UBOOT_CHAINLOADER_ADAPT01_TASKBOOK.md`

## 1. 新确认的关键结论

**U-Boot Android FIT 路线在软件机制上成立为一个可继续推进的候选方向；不能把现有 PREP10 Android boot v2 镜像直接交给 U-Boot bootm。**

原因和依据：

1. 本机 PREP10 boot v2 头中的 `kernel_addr=0x8000`，`ramdisk_addr=0x02000000`，并沿用 stock header。U-Boot v2026.10 的 Android image parser 会读取 Android header 里的 kernel address。直接 `bootm <PREP10>` 会落入旧 Android boot header 地址语义，不能满足 ACK Image 的 2 MiB load contract。PREP10 header 字段见本仓库 `linux-port-adapt01-corr01/stock_prep10_comparison.md`。

2. U-Boot v2026.10 的 ARM64 `booti_setup()` 读取 Image 的 `text_offset`、`image_size` 和 flags；当 flags bit 3 置位时，按 `ALIGN(image - text_offset, 2 MiB) + text_offset` 计算 relocated address。ACK Image 为 `text_offset=0`、`image_size=45,547,520`、`flags=0xA`。因此可由 U-Boot 把解压后的 raw Image 放到明确的 2 MiB 对齐基址；这与华为 ABL 的 `ImageBuffer+0x80000` 放置路径不同。

3. CoWave FIT 样例已经采用 `compression = "gzip"`，kernel `load/entry=0x91000000`、FDT `load=0x96000000`。对本机 ACK，`0x91000000` 是 2 MiB 对齐地址；按 Image header `image_size` 预留到 `0x93B70000`。这能避开 PREP10 的 ABL text_offset 冲突，但需确认 U-Boot 解压成功和所有保留内存不重叠。

4. 上游 U-Boot 的 `bootm` 支持 FIT 的第二个 initrd 参数。源码 `bootm_find_images()` 将显式传入的 `conf_ramdisk` 交给 `boot_get_ramdisk()`；后者对 Android 格式 ramdisk wrapper 调用 `android_image_get_ramdisk()`。因此可以把本机 separate ramdisk 分区镜像读入 RAM，作为外部 initrd wrapper 交给 FIT kernel，而不是把新的 initramfs 塞进 Android boot v2 的 embedded ramdisk 区。此路径要求 `CONFIG_ANDROID_BOOT_IMAGE=y`；建议显式配置 `CONFIG_ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR=y`，避免 wrapper header 中未确认的 ramdisk load address 被当作实际 DDR 目的地址。CoWave defconfig 启用 USB Fastboot；上游 Kconfig 对 `ANDROID_BOOT_IMAGE` 的默认值是 FASTBOOT=y 时启用，但正式构建仍须核对生成的 `.config`。

5. U-Boot `image_setup_linux()` 会对最终 FDT 执行 `fdt_chosen()` 和 `fdt_initrd()`。上游实现中，`fdt_chosen()` 从 U-Boot 环境变量 `bootargs` 写入 `/chosen/bootargs`；`fdt_initrd()` 写入 `linux,initrd-start/end` 并为 initrd 加入 FDT memory reservation。故 bootargs 与 initrd 地址交接机制有源码依据，不必自行手工拼接 FDT 的 initrd 两个属性。

## 2. 建议的 Android FIT / U-Boot 命令布局（设计，不是已制作镜像）

| 对象 | 建议位置/格式 | 依据及限制 |
|---|---|---|
| FIT staging | `0x98000000` | CoWave U-Boot env 现用地址 |
| FIT 所在分区 | `reserved3`，容量 25,165,824 B（24 MiB） | 本机 PREP12 partition inventory 已列出；不能据此推断其当前内容可覆盖 |
| FIT kernel | ACK raw Image，经 gzip 压缩；FIT 声明 `compression=gzip` | 压缩仅缩小暂存文件，不改变解压后 Image header |
| kernel load / entry | `0x91000000` | 2 MiB 对齐；按 `image_size` 的 end = `0x93B70000` |
| 外部 initrd | separate ramdisk wrapper 从 UFS `ramdisk` 分区单独读取，再作为 `bootm` 第二参数 | 不作为 Android boot v2 embedded ramdisk；当前 live wrapper 必须按精确 SHA 复核 |
| Linux FDT | FIT 内的 ACK VD FDT，建议 `0x96000000` | CoWave 的已用地址；必须先修正并验证 ACK DTB 的 /memory 与 rootparam |
| U-Boot boot command | `bootm <FIT_ADDR> <EXTERNAL_RAMDISK_WRAPPER_ADDR>` | FIT config 提供 kernel/FDT；显式第二参数覆盖 FIT 默认 ramdisk |

### 2.1 FIT 尺寸门槛

- `reserved3` = 25,165,824 B。
- raw ACK Image = 44,820,992 B，**比 reserved3 大 19,655,168 B，不能直接存放**。
- 已知候选 VD DTB = 1,216,399 B。
- 若 ramdisk 保持作为独立分区读取，而不放进 FIT，则 FIT 可用空间大约要求：`gzip(Image) + 1,216,399 B + FIT metadata/alignment <= 25,165,824 B`。
- 因此 gzip kernel 的实测压缩长度必须不大于 23,949,425 B，且还需扣除 FIT 头、配置、节点与 padding。**当前没有精确 ACK Image 二进制可在本轮复压，压缩尺寸仍 UNKNOWN；不得以“通常能压进”当作 PASS。**
- 如果超出 24 MiB，reserved3 方案不能按 CoWave 原参数直接使用；不得未经核验改用其它分区或扩大读写范围。

### 2.2 已知的地址算术与未闭合的内存条件

在 CoWave U-Boot DTS 已声明的第一段 DRAM `0x80000000..0xBBB00000` 内：
- kernel image reservation：`0x91000000..0x93B70000`；
- ramdisk wrapper 可规划在 kernel 之后、FDT 之前的空隙，但最终 initrd 目的区应由 U-Boot LMB 安全分配并经 map 核验；
- FDT：`0x96000000`；
- FIT staging 若严格不超过 24 MiB：`0x98000000..0x99800000`；
- CoWave splash carveout：`0x9C000000..0x9E300000`。

上述固定区间彼此不重叠，且 FIT staging 上限低于 splash 起点；这**仅是已列区间的算术检查**，不等于完整内存安全证明。ACK 候选 DTS 当前 `/memory/reg=<0 0 0 0>`，并带有 37 个 reserved-memory child；必须确认最终 Linux FDT 如何获得真实 RAM banks，以及所有 37 个 carveout 是否与 kernel、FIT、ramdisk、FDT 不冲突。不能仅凭 U-Boot control DTS 有 memory 节点就认定 Linux FIT DTB 已完成内存修复。

## 3. Ramdisk 的边界

- 本机 separate ramdisk 分区容量为 2 MiB；当前冻结 live backup SHA 为 `4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb`。此前解析记录表明它承载 Huawei first-stage `init/init.real` 与 KernelSU，不含 adbd；Android first-stage fstab 位于 DTB `/firmware/android/fstab`。
- ROUND2/ROUND64 的固件包副本另有一个 header-v0 ramdisk wrapper（page size 2048，ramdisk payload 1,322,962 B，固件包副本 SHA 与上述 live backup 不同）。不能把包副本的字段或长度不经复核直接套到当前 live backup。
- U-Boot 外部 Android ramdisk parser 路径已在上游源码确认，但**当前 live wrapper 的版本、page size、payload offset/length、ramdisk_addr 字段仍须针对当前 SHA 复核**。这就是 `ANDROID_FIT_RAMDISK_SOURCE=PARTIAL)，不是“已能直接 boot”。
- 推荐的第一阶段语义：保留 separate ramdisk 原角色；不要把相同 initramfs 再复制到 boot v2 embedded ramdisk。boot v2 的原有 519,986 B embedded ramdisk 仍应按原厂模板语义处理，不得凭本报告清空或替换。

## 4. 设备树与 Android 启动参数的未闭合项

1. U-Boot `bootm` 的 FDT fixup 可建立/更新 `/chosen`、写入 bootargs 和 initrd range；但 `fdt_root()` 本身不负责为 ACK DTB 填入正确 /memory bank。CoWave defconfig 有 `CONFIG_OF_BOARD_SETUP=y`，仍须查明实际 `ft_board_setup()` 是否对**FIT 中的 Linux FDT**填充 RAM range。
2. ACK 候选 DTB 已知 /memory reg 为空，同时有 37 个 reserved-memory nodes。必须填入与当前 HOS4.3 runtime memory contract 一致的 range；否则不能通过 K1。
3. 候选 base DTB 的 /rootparam 目前是空节点；stock VD Entry 2 使用外部 symbols/fixups，不能直接套到当前 ACK base。FIT 中必须使用已冻结且经核对的 VD target-path rootparam overlay 结果。U-Boot 本身不会因为读取 FIT 就自动从 DTBO 分区选 Entry 2。
4. CoWave Linux 示例的 `bootargs` 是 microSD root/f2fs，不能沿用。Android 路线须从 stock cmdline 重建 `androidboot.*`、console、SELinux、UFS/first-stage 所需参数；U-Boot 环境变量是实际 `/chosen/bootargs` 来源。
5. 传统 boot header v2 不含 v4 `vendor_boot` 的 bootconfig section。上游 `fdt_chosen` 自动写 bootargs，但不自动证明 Android bootconfig 兼容。当前 stock boot v2 的 first-stage 是否要求附加 bootconfig 数据仍为 PARTIAL/UNKNOWN，不得编造 bootconfig 内容。

## 5. Recovery / AVB 写入面

- CoWave 的初次 chainloader 安装要替换 `recovery` 与 `recovery_vbmeta`；不是只写 `reserved3`。
- CoWave pack 脚本保留原厂 recovery 镜像的 ramdisk、DTB、recovery_dtbo，替换 kernel 为 gzip U-Boot。
- `recovery_vbmeta` flags=2 的范围是 recovery chain 的 verification disabled；不能表述为关闭主 vbmeta、所有 AVB 或 system/vendor dm-verity。
- 本机已知 recovery 96 MiB、recovery_vbmeta 1 MiB，分区清单还列有 misc 2 MiB；但本轮未证明当前 live 原始 recovery/recovery_vbmeta/misc 三份备份均可按字节恢复，也没有完成真实回滚演练。因此 **RECOVERY_WRITE_GATE=HOLD**。
- `reserved3` 在既有 root vbmeta chain descriptor 列表中未出现；这是“该记录的 AVB chain 未列它”的证据，不等价于证明没有任何 Huawei OEM 自定义写保护或原有数据用途。未备份该分区前不得写入。

## 6. 更新后的证据矩阵

| 项目 | 结论 |
|---|---|
| U-Boot PIE 自身设计 | CONFIRMED（需 4 KiB 对齐入口；不是任意字节地址） |
| ABL gzip recovery handoff 到 U-Boot（本机精确 HOS4.3 ABL） | CONDITIONAL；CoWave 同型号实现有实测参考，但 recovery 分支需对精确目标二进制闭环 |
| 规避 Linux ACK Image 的 ABL +0x80000 / text_offset 冲突 | YES，条件是 ABL 成功启动 U-Boot，后由 U-Boot 放置 Linux Image |
| FIT kernel 地址算术 | PASS（0x91000000 是 2 MiB 对齐；image_size end=0x93B70000） |
| reserved3 容量 | CONFIRMED：25,165,824 B；FIT 压缩后长度 | UNKNOWN |
| FIT / DTB / splash 已列区间算术 | PASS；完整 reserved-memory non-overlap | UNKNOWN |
| external Android v0 ramdisk wrapper parser | CONFIRMED（上游 U-Boot 有该解析路径）；本机当前 live wrapper 精确头字段 | PARTIAL |
| bootargs / initrd chosen fixup | CONFIRMED（U-Boot 源码实现）；Android 完整 bootconfig 需求 | PARTIAL/UNKNOWN |
| VD rootparam / final Linux DTB | HOLD：须使用精确 VD overlay、填充 /memory 并核对 37 个 carveout |
| UFS | PARTIAL：U-Boot UFS 读取与 ACK 内建 UFS 驱动存在；Linux 接管同一 UFS controller 的时钟/复位/PHY 干净重初始化未证明 |
| K1 debug | U-Boot 阶段可通过 Fastboot USB / U-Boot console 观测；Linux K1 早期日志通道未证明。总体 DEBUG_OBSERVABILITY=UBOOT |
| Recovery 回滚 / 写入 | HOLD |
| 实机操作授权 | NONE；本报告不授予任何刷写或启动测试权限 |

## 7. 当前唯一建议

继续使用现有 `uboot-chainloader-adapt01` 任务书让 WorkBuddy 完成其本机离线证据项，但无需再开一个宽泛 audit round。应优先闭合三个实现阻断：
1. 针对当前 live ramdisk SHA 核准 v0 wrapper header 并用 U-Boot 当前配置验证外部 initrd 参数路径；
2. 生成 Android FIT 前，先确定 final ACK VD FDT 的真实 RAM banks、37 个 reserved-memory carveout 与精确 rootparam；
3. 对 ACK Image 做一次 host gzip 长度核算，确认 FIT + DTB 可放进 24 MiB reserved3。

这三项完成前不制作 recovery/FIT 候选；即使完成，也只允许主机端候选与解析验证，不代表设备写入授权。

## 8. 上游源码与项目来源

- CoWave Dby-W09 project: https://github.com/CoWave-Fall/linux-on-arm-matepad11
- CoWave U-Boot defconfig: https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/uboot/dby-w09_defconfig
- CoWave recovery wrapper packer: https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/scripts/pack-recovery.sh
- CoWave Android FIT ancestor: https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/tools/fit/dby-w09-sd.its
- U-Boot Android image parser: https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-android.c
- U-Boot external ramdisk selection: https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-board.c
- U-Boot `bootm` FIT / external ramdisk path: https://github.com/u-boot/u-boot/blob/v2026.10/boot/bootm.c
- U-Boot ARM64 `booti_setup()`: https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/lib/image.c
- U-Boot FDT `/chosen`, initrd and command line fixups: https://github.com/u-boot/u-boot/blob/v2026.10/boot/fdt_support.c and https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-fdt.c
- Existing local partition inventory: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/boot-v2-first-package-prep/firmware-analysis/boot-v2/linux-port-adapt01-corr01/partition_map.md
- Existing stock ramdisk / AVB package facts: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round64/round64-dby-w09-hos43-bootv2-ramdisk-dtbo-avb-evidence.md
- ACK candidate DTB memory placeholder: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/boot-v2-first-package-prep/kernel-baseline/round135/arch/arm64/boot/dts/qcom/huawei-dby-w09.dts

**边界：**本补充没有访问设备、没有执行 ADB/Fastboot、没有构建 U-Boot、没有生成 FIT/recovery、没有修改任何分区或现有候选镜像。
