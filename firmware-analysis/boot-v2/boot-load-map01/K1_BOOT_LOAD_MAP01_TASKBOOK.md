# K1-BOOT-LOAD-MAP01 — Hybrid ABL 实际 Kernel / DTB / Separate Ramdisk 内存加载布局审计

**签发：AI1（ChatGPT）**  
**执行：WorkBuddy Agent（本机离线）**  
**目标：Huawei MatePad 11 DBY-W09 / HWDBY / SM8250(Kona)**  
**内核候选：ACK android17-6.18.33_r00 / PREP10**  
**性质：只读 AArch64 Hybrid ABL PE 静态分析；不连接设备、不运行设备命令、不修改镜像。**

## 0. 背景与为何必须做

PREP10 已在 GitHub Release 发布，boot header v2 可解析，分区前缀尾部保护通过。但 AI1 审核发现一个未解决的启动内存布局风险，必须先闭合，否则不能批准写入 boot 分区。

PREP10 与 stock boot header 中的字段：

| 字段 | stock | PREP10 |
|---|---:|---:|
| kernel_addr | 0x00008000 | 0x00008000 |
| kernel_size | 22,256,282 B | 44,820,992 B |
| ramdisk_addr | 0x02000000 | 0x02000000 |
| embedded ramdisk_size | 519,986 B | 519,986 B |
| dtb_addr | 0x01F00000 | 0x01F00000 |
| dtb_size | 1,664,243 B | 1,216,399 B |

按字段字面值计算的 PREP10 范围：

    kernel [0x00008000, 0x02AC6A00)  size 44,820,992 B
    DTB    [0x01F00000, 0x02028F8F)  size 1,216,399 B
    ramdisk[0x02000000, 0x0207EF32)  size   519,986 B

PREP10 kernel 范围覆盖 DTB，并越过 ramdisk 地址约 11.3 MiB。stock kernel 结束在 0x01541A9A，未越过 DTB 起始地址。

AOSP boot header v2 定义 kernel_addr、ramdisk_addr、dtb_addr 为物理 load addresses，规范流程将组件放到这些指定地址；但本机 stock header 的 DTB 与 embedded ramdisk 字段在字面范围上也存在交叠，且本设备实际使用独立 ramdisk。这说明必须审计华为 ABL 的真实行为，不能只用通用规范推断 ABL 一定按字面加载，也不能在没证据时宣称不会冲突。

参考规范：
- https://source.android.com/docs/core/architecture/bootloader/boot-image-header
- https://android.googlesource.com/platform/system/tools/mkbootimg/+/refs/heads/main/include/bootimg/bootimg.h

本任务只回答：ABL 实际如何加载/搬移 kernel、DTB、embedded ramdisk 与 separate ramdisk，PREP10 raw Image 增长后是否造成真实内存覆盖。

## 1. 冻结身份

### 1.1 当前 Hybrid ABL 与 PE
- R155 ABL 分区转储：4,194,304 B（CORR01 已更正尺寸），SHA-256 b39de91b88ef13db83892cd2e8dc4b914f7f9ed86954039fb1f64fbbf8460011。
- 文件偏移 0x3078 的 LZMA_ALONE 流解出 Hybrid AArch64 PE：2,597,064 B，SHA-256 a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404。
- stock ABL PE：2,531,528 B，SHA-256 44cda9af120520805bad31d0684afdf7411ce22baf9158a660e05e880e7d9176。
- R155 ABL / PE 与 stock 不同，必须分析 Hybrid PE，不得用 stock PE 代替。
- R155 Hybrid 前缀由 GhostLock 602,112 B patch + stock 尾部组成；PT_LOAD 正确 p_offset=0x3000、p_filesz=0x90000（589,824 B），不要将 602,112 当成 PT_LOAD 大小。

若文件缺失或 hash mismatch，停止该输入支线，不连接设备重新读取、不从网上下载相似 ABL。

### 1.2 Stock boot / PREP10 / ramdisk
- stock live boot：100,663,296 B，SHA-256 7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8。
- PREP10 boot：46,563,215 B，SHA-256 d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091。
- PREP10 kernel Image：44,820,992 B，SHA-256 f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21。
- PREP10 embedded ramdisk：519,986 B，SHA-256 a4b94ff6bb2d9525fa6ad0010d8efa4c6fe2bd49d36956115c26a656b631af3c。
- PREP10 DTB：1,216,399 B，SHA-256 7bb9a1fba8d4574bce9d54795d67217d6f72857e792cbafa626ece3459b996b7。
- stock separate ramdisk partition：2,097,152 B，SHA-256 4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb。
- PREP04 既有字节级分析指出 ABL 会从独立 ramdisk 分区加载 init/init.real/KSU ramdisk 作为 kernel initrd；不得将 Linux 项目的 Kubuntu initramfs 加入 Android ACK。

### 1.3 板级 / 分区背景
- 设备板级 variant：DBY_W09_VD。
- DTBO 保持 stock；Entry 2 FDT 含 VD /rootparam，当前策略 KEEP_STOCK_NO_WRITE。
- DTBO 分区 25,165,824 B；boot 分区 96 MiB；separate ramdisk 分区 2 MiB。
- 当前不需要重新解析 DTBO，不需要改 DTBO 或 ramdisk。

## 2. 阶段 A — 解析地址语义和 PREP10 输入

1. 用至少一个与 ACK Android 17 boot header v2 格式兼容的解析器，独立解析 stock boot 与 PREP10 的所有 header field、kernel/ramdisk/DTB payload sizes、addresses、offsets、alignment、cmdline、OS version 和 boot ID。
2. 对 kernel_addr / ramdisk_addr / dtb_addr 记录原始字段、是否需要加 base、base 来源是什么；不得自行假设 base=0 或 0x80000000。
3. 从 PREP10 ACK Image 检查 ARM64 Image header 中 image_size、text_offset、flags、magic 等字段（仅静态读取），确认其对 kernel loading address/relocation 的约束。
4. 区分 boot image 中 embedded ramdisk 与设备 separate ramdisk 的路径。分别记录它们是否被读取、是否被加载、加载地址由何字段决定。
5. 标出 stock kernel 的地址范围和 PREP10 kernel 的地址范围，分别计算与 DTB、embedded ramdisk、separate ramdisk、ABL memory regions 的可能交叠。
6. 所有范围使用半开区间 [start,end)，对 base、offset 和最终 physical address 分列，不得混合。

## 3. 阶段 B — Hybrid ABL 实际 loader 静态路径

目标是闭合 Hybrid ABL 从 Fastboot boot / normal boot 入口到 kernel entry 的真实内存放置路径。

必须定位并追踪：
1. Boot image v2 header 解析函数；其 kernel_size/kernel_addr、ramdisk_size/ramdisk_addr、dtb_size/dtb_addr 是否被读取。
2. kernel payload 读取、校验、解压（若存在）、copy/memmove、load address 选择与 relocation。
3. DTB payload 的读取、FDT header size 校验、最终分配 buffer、copy/memmove、DTBO merge 后最终 FDT address。
4. separate ramdisk partition 读取路径、header/payload 解析、initrd size、最终加载地址，以及它是否取代/覆盖 embedded ramdisk。
5. 是否有动态 memory allocator、memory map、download buffer、image staging area、reserved memory/carveout、low/high memory boundary 等约束。
6. kernel Image header 的 text_offset/image_size 是否被 ABL 解析；若 ABL 不处理，记录内核自解压/自重定位是否适用（raw Image 不应臆测压缩路径）。
7. 所有实际 copy 的目的地址与长度；如果函数内部参数在不同基本块间变化，要完整追踪 caller、callee 和寄存器传递。
8. ABL 在进入 kernel 前是否将 boot image buffer 中的 kernel/DTB/ramdisk 移到最终地址；顺序是什么；是否会导致覆盖。
9. kernel entry 前的寄存器设置与 DTB pointer 传递，确认最终跳转地址。

### 证据要求
- 每一个地址都要有 Hybrid PE SHA、函数 VA/RVA、文件 offset、汇编片段和 caller/xref 关系。
- 必须根据 PE 映射正确换算 file offset ↔ RVA/VA；不能用 file offset 代替 VA。
- 不能只用字符串、单个 ADRP xref、反编译伪代码或函数名命名推断。
- 如果完整间接调用/函数指针表路径不能闭合，标 PARTIAL/UNKNOWN。
- 如果有多个候选加载路径（fastboot boot vs normal boot），分开分析；不能把 normal boot 路径自动套到 fastboot。
- 要特别注意 ABL 是否有不同的 fastboot CmdBoot 与 normal boot image loader，两者可能共享或不共享函数。

## 4. 阶段 C — overlap 和 capacity 判定

对 stock 与 PREP10 分别建立 load map，至少包含：

| Object | Source | Destination | Length | End | Overlap result | Evidence |
|---|---|---|---:|---|---|---|
| Kernel Image | boot kernel payload | 实际 Hybrid ABL 目标地址 |  |  |  |  |
| Embedded ramdisk | boot ramdisk payload | 实际目标地址或 UNUSED |  |  |  |  |
| Separate ramdisk | ramdisk partition payload | 实际目标地址 |  |  |  |  |
| Base DTB | boot DTB payload | 实际目标地址 |  |  |  |  |
| Merged DTB/overlay | post-DTBO FDT | 最终 FDT 地址 |  |  |  |  |
| ABL staging/download buffers | ABL memory |  |  |  |  |  |
| Other reserved/carveout | platform memory map |  |  |  |  |  |

必须回答：
- 按 ABL 实际 destination，PREP10 kernel 是否覆盖 DTB/separate ramdisk/embedded ramdisk？
- 若有搬移，搬移的时机是否避免 source/destination overlap？
- PREP10 44.8MB raw Image 是否超过 ABL/平台 loader 的最大 kernel size 或单个连续 RAM 区域？
- Kernel image 到达 kernel entry 时，其 text_offset/image_size 与 ABL load address 是否相容？
- 是否有任何明确的 size cap、overflow、alignment 或 reserved-memory 检查？

最终判定只能是：

    ABL_BOOT_V2_PARSER             = CONFIRMED | PARTIAL | UNKNOWN
    ABL_KERNEL_DESTINATION         = CONFIRMED | PARTIAL | UNKNOWN
    ABL_KERNEL_RELOCATION          = CONFIRMED | ABSENT | UNKNOWN
    ABL_DTB_DESTINATION            = CONFIRMED | PARTIAL | UNKNOWN
    ABL_SEPARATE_RAMDISK_PATH      = CONFIRMED | PARTIAL | UNKNOWN
    EMBEDDED_RAMDISK_USED          = YES | NO | UNKNOWN
    KERNEL_DTB_OVERLAP             = NONE | RESOLVED_BY_RELOCATION | PRESENT | UNKNOWN
    KERNEL_RAMDISK_OVERLAP         = NONE | RESOLVED_BY_RELOCATION | PRESENT | UNKNOWN
    PREP10_KERNEL_SIZE_LIMIT       = PASS | FAIL | UNKNOWN
    PREP10_LOAD_LAYOUT             = SAFE | UNSAFE | UNKNOWN
    FINAL_RESULT                   = LOAD_MAP_CONFIRMED_SAFE | BLOCKED_OVERLAP | BLOCKED_ON_UNKNOWN

## 5. 阶段 D — 与 Linux DBY-W09 项目进行有限对照

主要参考：svesnav/linux-dby-w09。只检查该项目对 boot image 组件地址、kernel gzip/raw 格式、boot v2 header 参数、DTB 与 ramdisk payload 布局的真实构建参数。

不得将该项目 Linux 7.0 Image.gz 可启动直接推导为 ACK raw Image 可使用相同 header load addresses。

需要明确：
- 项目使用 Image.gz 还是 raw Image；
- 其实际压缩 kernel 大小；
- 其 stock boot header load addresses 与实际 kernel/Dtb/ramdisk 组件大小；
- 项目构建工具是否更改 kernel_addr/ramdisk_addr/dtb_addr；
- 其 actual initramfs 与 ramdisk 分区载荷和 Android separate ramdisk 的区别。

这部分只为解释为什么不能直接类比，不需要重新审计项目所有代码。

## 6. 严格禁止

- 不连接平板，不执行 ADB/Fastboot/OEM 命令。
- 不执行 fastboot boot/flash/reboot，不 dd、不写分区，不切换模式。
- 不运行 ABL/PE、kernel、init、adbd 或任何从固件提取的二进制。
- 不重新编译内核，不改 boot header 参数，不重新打包候选，不生成猜测地址的新镜像。
- 不改 DTBO、ramdisk、vbmeta、ABL、DTB 或原始 boot。
- 不访问 userdata、persist、oeminfo、TEE key、IMEI、MAC、校准数据。
- 不为了闭合路径而扩大到无限全盘扫描；只对精确 Hybrid PE 与已有 stock/PREP10 文件分析。

## 7. 交付

生成 K1_BOOT_LOAD_MAP01_REPORT.zip，至少包含：
1. K1_BOOT_LOAD_MAP01_REPORT.md
2. stock_vs_prep10_load_ranges.csv
3. hybrid_abl_load_path.md（函数、VA/RVA、caller/callee、汇编证据）
4. memory_map.md（kernel、DTB、embedded/separate ramdisk、ABL staging/carveout）
5. linux_dby_w09_comparison.md
6. evidence_matrix.csv
7. SHA256SUMS.txt

脱敏报告上传至 hhdy/matepad11-dby-w09-agent-reports，建议目录 firmware-analysis/boot-v2/boot-load-map01/。原始完整 ABL、boot、ramdisk、userdata 和设备识别信息不得公开上传。候选 boot 不得修改或重新发布。

## 8. 停止条件

- 如果 Hybrid ABL 实际 loading path 能闭合，给出 load map 与最终 overlap 判定后立即停止。
- 如果 indirect call/relocation path 不能闭合，明确 UNKNOWN，不以通用 AOSP 规范推断具体 ABL 行为。
- 如果结果为 SAFE，仍只提交给 AI1 审核；本任务不构成设备写入授权。
- 如果结果为 UNSAFE/UNKNOWN，BOOT_WRITE_GATE 继续 BLOCKED，不猜测修改地址。

本轮只解决一个问题：**PREP10 44.8 MiB raw ACK Image 在当前 Huawei Hybrid ABL 下，是否会与 DTB/ramdisk 内存区域冲突。** 完成后交 AI1 审核。