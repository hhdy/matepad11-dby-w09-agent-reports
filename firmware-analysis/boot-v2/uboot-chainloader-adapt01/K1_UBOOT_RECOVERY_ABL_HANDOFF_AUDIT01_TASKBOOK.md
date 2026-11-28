# K1_UBOOT_RECOVERY_ABL_HANDOFF_AUDIT01
## HOS4.3 recovery → U-Boot PIE → previous-BL FDT / ramdisk handoff 精确只读审计

- 任务编号：K1_UBOOT_RECOVERY_ABL_HANDOFF_AUDIT01
- 执行者：本地 WorkBuddy Agent（只读）
- 复核基线：AI1 已发布的 U-Boot v2026.10 上游分析
- 设备目标：Huawei MatePad 11 2021 DBY-W09 / HOS4.3 / SM8250 / VD
- 唯一目标 ABL PE SHA-256：a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404
- 任务日期：2026-11-28

---

## 0. 任务目标（仅三个闭环）

这不是新一轮泛化 ABL audit。只使用当前已经冻结的精确 ABL PE 与现有反汇编/任务产物，回答：

1. recovery 分区中把 Android boot v2 kernel 替换为 gzip U-Boot 后，HOS4.3 ABL 是否进入现已分析的 BootLinux 主加载路径，并最终以 ARM64 x0 传入最终 FDT？
2. recovery 启动时，ABL 传入的 initrd 到底来自 boot image embedded ramdisk、HOS separate ramdisk 分区、recovery_ramdisk 分区，还是其他来源？最终 FDT 的 linux,initrd-start/end 指向何处、指向 wrapper 还是已提取 payload？
3. ABL UpdateDeviceTree / EFI_RAMPARTITION 路径究竟更新哪些 FDT memory 节点/属性？是否能静态确认最终 FDT 的 /memory/reg 有非零 bank？是否有 FDT memreserve / reserved-memory 记录可供 U-Boot LMB 保护 initrd？

只回答上述三项。找不到静态证据时明确 UNKNOWN / BLOCKED，不扩大到无关驱动或签名分析。

## 1. 必须先做身份门禁

1. 找到本地现有 ABL PE 派生文件与 SHA 清单。
2. 对实际用于分析的 PE 字节重新计算 SHA-256。
3. 必须与本任务指定 SHA 完全一致：
   a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404
4. 如果原始 PE 不存在、哈希不匹配、只有不同版本的 stock ABL、或只能取得不确定的 HEX/转储：
   - 报告 BLOCKED；
   - 记录文件名、可见哈希和差异；
   - 立即停止，不从旧版本推断 HOS4.3 当前行为。

不要重新上传原始 ABL、boot、ramdisk、vbmeta、DTB 或任何设备固件到公开仓库。

## 2. 最小输入资料

先从 GitHub 只读读取本任务之前的以下脱敏报告和证据文件：

- firmware-analysis/boot-v2/boot-load-map01/K1_BOOT_LOAD_MAP01_REPORT.md
- firmware-analysis/boot-v2/boot-load-map01/hybrid_abl_load_path.md
- firmware-analysis/boot-v2/boot-load-map01/evidence/dis_bootlinux_full.txt
- firmware-analysis/boot-v2/boot-load-map01/evidence/dis_loadramdisk.txt
- firmware-analysis/boot-v2/boot-load-map01/evidence/dis_updatememtree.txt
- firmware-analysis/boot-v2/boot-load-map01/evidence/abl_boot_strings.txt
- firmware-analysis/boot-v2/round? 如实际本地目录有其他已完成的 recovery ABL 相关报告，仅按需读取，不重复扫描。

并核对 AI1 已发布的公开 U-Boot 源码分析：
- firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_PREVBL_FDT_RAM_FALLBACK.md
- firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_ANDROID_RAMDISK_RAMMAP_CORRECTION.md
- firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_EXTERNAL_ANDROID_RAMDISK_HANDOFF_FIX.md
- firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_FIT_NATIVE_RAMDISK_ROUTE.md

注意：AI1_UBOOT_EXTERNAL_ANDROID_RAMDISK_HANDOFF_FIX.md 只证明 U-Boot v2026.10 的源码命令机制，不证明本机 ABL recovery 分支实际提供的是同一份 separate ramdisk。审计 B 必须独立从精确 HOS4.3 ABL 的 recovery caller 和 LoadRamdisk 数据流判断来源，不得把 U-Boot 之后可读取的 ramdisk 分区反推成 ABL 当前选择的 initrd。

如现有本地分析脚本/反汇编已能回答，不要重复整套反编译工作。

## 3. 审计 A：recovery boot image → BootLinux 调用链

在精确 ABL PE 中：

1. 找到决定 boot / recovery / fastboot 的模式选择与 recovery partition 选择代码。
2. 从 recovery 分区打开/读取/认证的调用点开始，向后追踪到：
   - LoadImageAndAuth / LoadImageAndAuthVB2；
   - BootLinux 主函数（现有报告识别为 0x36C1C–0x388E8）；
   - kernel destination 计算；
   - ExitBootServices；
   - 最终 kernel entry。
3. 证明 recovery 路径是否真正调用同一 BootLinux 尾段，不能仅根据正常 boot 和 fastboot RAM boot 共用函数就推定 recovery 也共用。
4. 若确实共用，提供：
   - recovery 分支调用者 VA；
   - 至少两级 caller/callee 链；
   - 函数边界与关键条件分支；
   - recovery image 的 kernel/header_version 字段在本函数中的解析路径；
   - 最终 x8 / x0 / x1-x3 寄存器赋值；
   - 最终 blr 的地址。
5. 关键判断：
   - ABL 解压 gzip U-Boot 到 ImageBuffer + 0x80000 是否被 recovery 分支使用；
   - AllocatePages 页面粒度为 4KiB 时，该位置是否满足 U-Boot PIE 的 4KiB 入口约束；
   - 不要把这个 4KiB 约束与 Linux ACK Image 的 2MiB base alignment 混为一谈。

输出状态：
- RECOVERY_USES_COMMON_BOOTLINUX = CONFIRMED / CONDITIONAL / UNKNOWN
- RECOVERY_KERNEL_LOAD_DESTINATION = 已证值 / UNKNOWN
- UBOOT_ENTRY_ALIGNMENT = PASS / FAIL / UNKNOWN
- RECOVERY_HANDOFF_FINAL_X0_FDT = CONFIRMED / CONDITIONAL / UNKNOWN

## 4. 审计 B：recovery 路径 ramdisk 来源及内存载荷形态

**ramdisk 文件身份提醒：**现有报告有两个不同的 2,097,152 B 候选：
- K1_FASTBOOT_GATE01_AI1_REVIEW.md 标记 stock separate-ramdisk SHA-256 为 4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb；
- ROUND64 Phase F 标记 ramdisk.img SHA-256 为 5c20e4781f701e075ab30d3f8389172435e5591579bb5971f1b29331862fddc0，并复用了 header v0 / page_size 2048 / payload 1,322,962 B 的历史 inventory。

这两者哈希不同。不得把 5c20 对应的 header / payload 字段套用到 4dd6。先从本地 acquisition manifest、源分区 label、采集路径和时间戳核对哪个文件才是当前 HOS4.3 live separate ramdisk；没有 provenance 闭环就将 live wrapper 身份标 UNKNOWN，不得尝试解析/推断。



1. 从 recovery 选择分支进入 LoadRamdisk 函数（现有地址候选 0x3969C），追踪所有关键参数和数据来源。
2. 逐项判断：
   - Android boot v2 embedded ramdisk header/payload 是否参与；
   - separate partition label 究竟是 ramdisk、recovery_ramdisk 或其他名称；
   - 是否另行读取 recovery image 中的 ramdisk section；
   - 是否读取 mini-bootimg / Android header；
   - 是否剥除 wrapper header；
   - 最终复制到 R 区域的字节从哪个源偏移开始、长度如何计算；
   - 传给最终 FDT 的 linux,initrd-start/end 是 wrapper 还是 initramfs payload。
3. 如果恢复路径参数无法从现有 PE 调用链解出，标 PARTIAL/UNKNOWN，明确缺少的 caller、协议实现或 UEFI driver provider。不得通过函数/字符串名称猜测。
4. 严格区分：
   - ABL 当前启动的 recovery ramdisk；
   - HOS4.3 的 Android separate ramdisk 分区；
   - AI1 主机端 FIT-native ramdisk 候选。
   三者可能不同，不能混用名称。

输出状态：
- RECOVERY_INITRD_SOURCE = EMBEDDED / SEPARATE_RAMDISK / RECOVERY_RAMDISK / OTHER / UNKNOWN
- RECOVERY_INITRD_IS_RAW_CPIO = YES / NO / UNKNOWN
- RECOVERY_INITRD_START_END = 静态计算值 / runtime-dependent / UNKNOWN
- FDT_INITRD_PROPERTIES = CONFIRMED / PARTIAL / UNKNOWN

## 5. 审计 C：ABL UpdateDeviceTree 与 RAM bank / LMB reservation

重点函数候选 0x3D9D0/0x3D9D4；已知字符串：
- “Invalid memory configuration, check memory partition table”
- “RAM Partitions”
- “Locate EFI_RAMPARTITION_Protocol failed”
- “Failed to get RAM partitions”
- “Error Occured while populating RamPartitions”

请闭合：

1. 0x3D9D0/0x3D9D4 的全部 caller；确定传入的 FDT 指针、RAM partition table 或其他结构地址。
2. EFI_RAMPARTITION_Protocol 的 LocateProtocol / ReadRamPartitions 调用路径，返回表结构和每项字段如何被消费。
3. 哪些 FDT path / node / property 被读取、创建、删除或写入。重点确认：
   - /memory
   - /memory/reg
   - /reserved-memory 子节点
   - FDT memreserve map
   - /chosen/linux,initrd-start
   - /chosen/linux,initrd-end
4. 若代码仅更新 vendor node “RAM Partitions”，但没有更新 /memory/reg，必须明确区分，不得把 vendor 内存表说成标准 /memory。
5. 如果内存 bank 值来自运行时 EFI protocol，而不是 PE 中的静态常量，明确说值是 runtime-dependent；不要从 12GB 用户设备容量、CoWave 8GB DTS 或 HOS4.2 参考推导本机 bank tuple。
6. 判断是否能静态证明 ABL 在 recovery → U-Boot 路径给出的最终 FDT 带有非零 /memory/reg。不能证明时保持 UNKNOWN。
7. 检查 ABL 是否给 initrd 地址范围加入 FDT memreserve 或 /reserved-memory reservation。若只设置 chosen start/end，不得声称 U-Boot LMB 自动保留了这块内存。

输出状态：
- ABL_UPDATEDEVICETREE_NODE = 确切路径/UNKNOWN
- ABL_FINAL_FDT_MEMORY_REG = NONZERO_CONFIRMED / ZERO / UNKNOWN
- ABL_FINAL_FDT_INITRD_MEMRESERVE = YES / NO / UNKNOWN
- UBOOT_QCOM_EXTERNAL_FDT_FALLBACK_INPUT = usable / unavailable / conditional / unknown

## 6. 审计 D：与 U-Boot v2026.10 机制对照（只核对，不重新泛化）

对照这些已固定源码点：
- arch/arm/cpu/armv8/start.S：save_boot_params 位于 PIE fixup 前；PIE 要求 _start 4KiB 对齐；
- arch/arm/lib/save_prev_bl_data.c：save_boot_params(r0) 保存 x0，get_prev_bl_fdt_addr() 返回该值；
- arch/arm/Kconfig：ARCH_SNAPDRAGON 选择 SAVE_PREV_BL_FDT_ADDR；
- arch/arm/mach-snapdragon/board.c：internal /memory 失败时尝试 previous-BL external FDT；
- boot/image-board.c：boot_get_ramdisk / boot_ramdisk_high；
- boot/image-fdt.c：boot_fdt_add_mem_rsv_regions；
- boot/fdt_support.c：fdt_initrd()。

请给出最小判定：
1. 若 recovery x0=最终 ABL FDT 且 /memory/reg 非零，是否可让 U-Boot internal control DTS 不提供硬编码 /memory/reg，触发 external FDT 的 qcom_parse_memory() fallback？
2. 如果没有有效 external /memory，U-Boot 会在哪里失败？
3. ABL initrd properties / memreserve 能否安全地复用到 ACK FIT FDT？若需额外复制/patch，列明最小代码接口；未证明前不建议直接复用。
4. 不要把从 external FDT 读取 RAM bank 说成自动继承其 reserved-memory、no-map、reusable 或 chosen 属性。

## 7. 强制禁止事项

- 不运行 ADB、Fastboot、OEM、EDL、Sahara、Firehose，不连接设备。
- 不 reboot、不 fastboot boot、不做临时启动。
- 不刷写、不写入/擦除/格式化任何分区。
- 不改 ABL、XBL、boot、recovery、vbmeta、dtbo、ramdisk。
- 不创建/修改 U-Boot / FIT / recovery / boot 镜像，不运行内核构建。
- 不安装工具、不下载固件。
- 不上传任何原始固件/设备标识/私有 ramdisk/DTB/vbmeta。
- 不把现有报告已证结论重新写成新发现。
- 不扩展到 UFS、PMIC、显示、UART、音频等无关硬件子系统。

## 8. 交付文件与证据标准

在 GitHub 分支 ai1/boot-v2-first-package-prep 写入：

firmware-analysis/boot-v2/uboot-chainloader-adapt01/K1_UBOOT_RECOVERY_ABL_HANDOFF_AUDIT01_REPORT.md

报告必须包含：
1. ABL PE 完整 SHA-256 身份；
2. 输入证据清单（每个文件路径、SHA/blob identity 或来源）；
3. recovery 分支到最终 blr 的调用图；
4. 关键指令窗口（地址 + 原指令 + 数据流解释）；
5. initrd 来源、wrapper/payload 与 FDT memory/reservation 的确定性证据；
6. 每项 CONFIRMED / PARTIAL / UNKNOWN / BLOCKED 判定；
7. 未闭合项及需要的最小证据；
8. 明确说明无设备操作、无镜像制作、无分区写入。

所有结论必须来自精确 SHA ABL 的指令、调用图和数据流。单独的字符串、函数名、其他 firmware 版本或 CoWave 的 HOS4.2 实测不能作为本机 HOS4.3 recovery 结论。

## 9. 停止条件

只允许一次有界审计。完成上述报告并上传后停止，不自动开启下一轮，不执行设备测试。若在 60 分钟内无法证明 recovery 到 BootLinux 的完整路径，按 BLOCKED/UNKNOWN 交付，明确指出缺少的最小反汇编窗口，不要继续扩成大范围 ABL audit。
