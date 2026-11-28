# K1_UBOOT_CHAINLOADER_PREBUILD_GATE02
## HOS4.3 recovery / ABL FDT / U-Boot configuration — 有界只读预构建门禁

- 任务编号：K1_UBOOT_CHAINLOADER_PREBUILD_GATE02
- 执行者：本地 WorkBuddy Agent
- 目标设备：Huawei MatePad 11 2021 DBY-W09 / HOS4.3 / SM8250 / VD
- 仓库：`hhdy/matepad11-dby-w09-agent-reports`
- 分支：`ai1/boot-v2-first-package-prep`
- 基线交付：`K1_UBOOT_RECOVERY_ABL_HANDOFF_AUDIT01_REPORT.md`
- 基线 commit：`7f03c2fd70598d9bf8a39eb58358ace7d0ab06a7`
- 唯一 ABL PE SHA-256：`a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`
- 本任务性质：**一次性、有界、本地只读门禁审计**。不是新一轮泛化 ABL 研究，不是构建任务，也不是实机启动任务。

---

## 0. 本轮目标与停止原则

AUDIT01 已经交付。现在只核对影响 U-Boot chainloader 是否能进入下一阶段的剩余门禁：

1. 尽最大努力用一次寄存器数据流 pass 追踪 recovery 间接调用到 BootLinux，并闭合 recovery 的 LoadRamdisk 分区 label。
2. 对精确 ABL 的 UpdateDeviceTree 路径做一次完整、受限的调用/数据流检查，确认标准 `/memory/reg`、initrd memreserve 和 reserved-memory 的写入证据；没有证据就保持 UNKNOWN。
3. 核对本地已有的 U-Boot 最终配置、候选 FIT 文件（若已存在）和 recovery 写入面备份完整性，形成明确的 PREBUILD GO/HOLD/NO-GO 结论。

**禁止把本轮变成循环审计。**每个静态子项只允许一次聚焦检查；无法闭环就记录最小缺失证据并停止。总工作时限 60 分钟。到时按现有证据交付，不得扩大范围。

## 1. 先做身份与输入门禁

1. 使用现有本地 PE 文件，重新计算 SHA-256；必须精确等于：
   `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`
2. 若 PE 缺失或不匹配，立即 BLOCKED；不得换用其他固件版本。
3. 读取并引用以下已交付材料，不重复其已经闭环的部分：
   - `firmware-analysis/boot-v2/uboot-chainloader-adapt01/K1_UBOOT_RECOVERY_ABL_HANDOFF_AUDIT01_REPORT.md`
   - `firmware-analysis/boot-v2/uboot-chainloader-adapt01/K1_DBY_W09_UBOOT_CHAINLOADER_ADAPT01_ADDENDUM01.md`
   - `firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_PIE_ENTRY_AND_RUNTIME_RAMMAP_REVIEW.md`
   - `firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_PREVBL_FDT_RAM_FALLBACK.md`
   - `firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_EXTERNAL_ANDROID_RAMDISK_HANDOFF_FIX.md`
   - `firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_ANDROID_RAMDISK_RAMMAP_CORRECTION.md`
   - `firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_FIT_GZIP_LIMIT_REVIEW.md`
4. 可以读取现有本地反汇编、manifest、备份、构建目录与配置文件；不得重新采集设备数据。

## 2. 组 A：一次性 recovery 间接调用与 initrd label 数据流

### A1. recovery → BootLinux 的间接调用

基线结论必须保持：
- `RECOVERY_USES_COMMON_BOOTLINUX = CONDITIONAL`
- `RECOVERY_HANDOFF_FINAL_X0_FDT = CONFIRMED`（仅共享尾段不变量；不能单独证明 recovery 已到达该尾段）

只执行一个以最终 `blr x8`（现有尾段约 `0x38868–0x3887C`）和 BootLinux 入口 `0x36C1C` 为锚点的寄存器数据流 pass：

1. 从已分析的 recovery loader/partition-mode 决策站点向前追踪函数指针来源、寄存器写入及保存/恢复关系。
2. 尽可能识别谁向 BootLinux 函数指针槽赋值、何处装载该指针、最终哪一个 `blr` 触发调用。
3. 记录至少两级逻辑调用关系（允许注明间接调用，不要求存在直接 BL relocation）。
4. 必须把 recovery mode 条件与该函数指针的实际选择关联起来。单独的字符串、唯一尾段、相邻代码或函数名不构成调用闭环。
5. 若在本轮 pass 内无法证明，结论维持 CONDITIONAL，并列出最小缺失的寄存器/内存窗口；不得因共享尾段就提升为 CONFIRMED。

### A2. LoadRamdisk 分区 label

围绕 `LoadRamdisk`（基线候选 `0x3969C`）及其调用者，只追踪传入的分区 label 参数：

1. 建立 bootmode/recovery mode → label 的选择表。
2. 区分 `ramdisk`、`recovery_ramdisk` 和其他可能分区名。
3. 证明 recovery 分支实际传入的字符串/缓冲区来源；若由动态格式化或配置表决定，说明可证明范围。
4. 确认是否存在 wrapper 剥离：源偏移、复制长度及最终 FDT chosen initrd start/end 指向 wrapper 还是 gzip payload。
5. 禁止把 normal boot 路径 PREP04 的 payload 结果直接套用到 recovery 路径。

A1/A2 状态分别输出：
- `RECOVERY_ENTRY_CHAIN = CONFIRMED / CONDITIONAL / UNKNOWN`
- `RECOVERY_INITRD_LABEL = exact label / PARTIAL / UNKNOWN`
- `RECOVERY_INITRD_PAYLOAD_FORM = RAW_CPIO / GZIP_PAYLOAD / ANDROID_WRAPPER / UNKNOWN`

## 3. 组 B：ABL UpdateDeviceTree / RAM / initrd reservation

唯一目标仍为精确 PE；聚焦 UpdateDeviceTree 函数族（基线候选 `0x3D9D0/0x3D9D4`）及其直接调用的 helper/provider：

1. 获取完整函数边界和一次调用图；检查所有与 FDT/libfdt 操作有关的调用点及参数来源。
2. 逐项核对是否存在对以下对象的实际写操作：
   - `/memory/reg`
   - `/reserved-memory` 子节点及 `no-map` / `reusable` 属性
   - FDT memreserve map（例如实际 reserve-entry 添加接口）
   - `/chosen/linux,initrd-start`
   - `/chosen/linux,initrd-end`
   - vendor `RAM Partitions` 节点
3. 将 EFI RAM Partition Protocol 的 LocateProtocol / ReadRamPartitions provider 和消费者区分开。若 provider 二进制/实现不在现有资料中，明确标记缺失；不得根据协议名称推断返回内容。
4. 对每个结论提供实际调用目标、关键指令地址、传入 FDT/节点/属性参数的数据流。字符串 xref 或 `grep 0` 只能作为辅助，不能代替完整写路径证据。
5. 若 bank 值来自运行时协议，仍标记 runtime-dependent；不得用用户报告的 12GB、CoWave HOS4.2 三段 tuples 或 stock base DTB placeholder 推导本机真实 bank tuples。
6. 本轮没有已授权的 final-FDT 原始字节证据时，`/memory/reg` 的非零状态继续 UNKNOWN；不要尝试连接设备补采。
7. 只有 chosen start/end 写入，不等于建立 memreserve；不得声称 U-Boot LMB 会自动保护 initrd。

输出状态：
- `ABL_MEMORY_REG_MUTATION = CONFIRMED / NOT_FOUND_IN_ANALYZED_PATH / UNKNOWN`
- `ABL_RESERVED_MEMORY_MUTATION = CONFIRMED / NOT_FOUND_IN_ANALYZED_PATH / UNKNOWN`
- `ABL_INITRD_MEMRESERVE = YES / NO / UNKNOWN`
- `ABL_RAM_BANK_VALUES = STATIC_VALUES / RUNTIME_DEPENDENT / UNKNOWN`

注意：`NOT_FOUND_IN_ANALYZED_PATH` 仅表示已覆盖的确切调用路径没有发现写操作，不得泛化为整个 ABL 二进制绝对不存在该操作。

## 4. 组 C：U-Boot 最终配置与已有候选文件盘点

本组只检查本地已经存在的文件；不运行配置生成、不构建、不打包。

### C1. 最终 .config

优先查找 CoWave DBY-W09 U-Boot v2026.10 对应构建目录中的最终 `.config`。必须区分：
- 最终生成的 `.config`
- defconfig
- Kconfig 默认值
- AI1 研究笔记中的预期配置

仅最终 `.config` 可作为“最终配置已确认”的依据。至少记录：

```
CONFIG_POSITION_INDEPENDENT
CONFIG_INIT_SP_RELATIVE
CONFIG_SYS_INIT_SP_BSS_OFFSET
CONFIG_ARCH_SNAPDRAGON
CONFIG_SAVE_PREV_BL_FDT_ADDR
CONFIG_SAVE_PREV_BL_INITRAMFS_START_ADDR
CONFIG_CMD_ABOOTIMG
CONFIG_ANDROID_BOOT_IMAGE
CONFIG_FIT
CONFIG_CMD_BOOTM
CONFIG_OF_LIBFDT
CONFIG_OF_BOARD_SETUP
CONFIG_NR_DRAM_BANKS
CONFIG_SYS_BOOTM_LEN
CONFIG_USB_FUNCTION_FASTBOOT
```

若最终 `.config` 不存在，只能报告缺失；不得从 defconfig 推断所有结果。

### C2. 已有 FIT / reserved3 容量

1. 盘点本地是否已经存在 ACK Image、目标 VD DTB、FIT ITS、FIT 文件或 gzip 输出。
2. 对已存在文件只做身份/hash/尺寸盘点；不重新生成压缩文件或 FIT。
3. reserved3 已确认容量为 25,165,824 B（24 MiB），不得再次要求设备查询其容量。
4. 只有在完整 FIT 文件真实存在时才比较其实际字节数与 24 MiB；只有 gzip kernel 单体尺寸不得冒充完整 FIT 尺寸。
5. 若本地没有完整 FIT，`FIT_RESERVED3_CAPACITY = UNKNOWN_NOT_BUILT`，不是 PASS，也不是 FAIL。

### C3. recovery 写入面备份完整性

仅盘点已经存在的本地只读备份、采集 manifest 与 SHA-256 清单：
- `recovery`
- `recovery_vbmeta`
- 如 manifest 明确列出与目标 recovery 启动链直接相关的额外分区，也一并核验其备份身份，但不要扩展到无关分区。

每项记录 label、来源 manifest、文件长度、SHA-256、采集时间/来源标记、是否与 manifest 一致。不得连接设备补读，不得以同尺寸旧文件代替当前版本。缺少任一关键备份或 provenance 不闭环，保持写入门禁 NO-GO。

输出状态：
- `UBOOT_FINAL_CONFIG = VERIFIED / DEFCONFIG_ONLY / MISSING`
- `FIT_RESERVED3_CAPACITY = PASS / FAIL / UNKNOWN_NOT_BUILT`
- `RECOVERY_WRITE_SURFACE_BACKUPS = COMPLETE / INCOMPLETE / UNKNOWN`

## 5. 总体决策矩阵

报告最后必须给出下列结论，不允许把不同阶段合并：

| 阶段 | 决策条件 |
|---|---|
| 继续静态源码准备 | 可以继续，但不得重复已闭环的 generic U-Boot 源码分析 |
| 进入 host-side package preparation | 必须明确哪些配置、ramdisk parser 和 FIT 内容是真实文件已验证，哪些仍是计划 |
| 生成/修改 recovery 或 FIT 候选 | 本任务不授权；即使静态门禁通过，也不得在本轮制作 |
| 设备临时启动 / 刷写 | 本任务不授权；recovery/recovery_vbmeta 备份不完整时必须明确 NO-GO |

总体状态只允许：
- `PREBUILD_READINESS = HOLD`：有任一关键静态信息未知或未具备必要备份；
- `PREBUILD_READINESS = CONDITIONAL`：host-side 准备条件具备，但设备侧 RAM/FDT、保留区或备份门禁仍未闭环；
- `PREBUILD_READINESS = READY_FOR_HOST_PACKAGE_PREP`：仅表示可进入主机端候选准备规划，不代表可以生成镜像、临时启动或刷写。

任何状态均不得解释为设备写入授权。

## 6. 强制禁止事项

- 不连接设备；不运行 ADB、Fastboot、OEM、EDL、Sahara、Firehose。
- 不读取 live 分区，不执行 reboot、临时启动、recovery 选择或任何设备侧命令。
- 不写入、擦除、格式化、刷写任何分区。
- 不修改 ABL/XBL/boot/recovery/recovery_vbmeta/vbmeta/dtbo/ramdisk。
- 不构建 U-Boot，不运行 defconfig/config 生成，不生成 FIT、boot、recovery 或任何候选镜像。
- 不签名、不修改 AVB/vbmeta，不改变启动链安全状态。
- 不上传任何原始固件、原始 ramdisk、原始 DTB、vbmeta、设备标识或可还原私有物理地址的材料。
- 不从 CoWave 的 HOS4.2 实测推断本机 HOS4.3 live RAM map。
- 不重复审查已经 source-closed 的 U-Boot PIE、generic FDT fixup、CMD_ABOOTIMG 命令解析机制。

## 7. 交付与停止条件

只交付一个报告：
`firmware-analysis/boot-v2/uboot-chainloader-adapt01/K1_UBOOT_CHAINLOADER_PREBUILD_GATE02_REPORT.md`

报告必须包含：
1. PE SHA-256 身份门禁；
2. 实际检查过的文件/manifest/配置文件清单及 hash/blob identity；
3. A1/A2 的最小调用图、关键指令地址和状态；
4. UpdateDeviceTree 对标准 memory/reserved-memory/chosen/memreserve 的写路径证据；
5. 最终 `.config`、FIT 文件盘点与 reserved3 容量核对；
6. recovery/recovery_vbmeta 本地备份完整性表；
7. 上述所有 gate 的状态和 `PREBUILD_READINESS` 总判定；
8. 未闭合项及其唯一最小证据需求；
9. 无设备操作、无构建、无镜像生成、无分区写入的声明。

完成后将报告提交到指定分支，随后从 GitHub 回读报告与 commit，核对报告内容和 SHA/路径一致。**到此停止，不自动开启下一轮。**

若 60 分钟内任一分析无法完成，按 UNKNOWN/BLOCKED 交付，不扩成第二轮。

---

## START_PROMPT（可直接交给本地 WorkBuddy Agent）

你是本任务的本地只读执行 Agent。请严格执行 `K1_UBOOT_CHAINLOADER_PREBUILD_GATE02`，以 AUDIT01 的已核验证据为基线。先复核精确 ABL PE SHA-256，再只做本任务规定的 A/B/C 三组一次性检查。必须区分直接证据、条件推断和 UNKNOWN；不得把共享 BootLinux 尾段的不变量当成 recovery 调用链已闭合，不得把 chosen initrd 属性当成 LMB reservation，不得把 CoWave tuples 当成本机 RAM map，也不得从 defconfig 冒充最终 `.config`。不连接设备、不读取 live 分区、不构建、不生成镜像、不写入、不刷写。60 分钟到时或完成一个报告即停止。最终只提交并回读核验 `K1_UBOOT_CHAINLOADER_PREBUILD_GATE02_REPORT.md`，不得自动启动下一轮。
