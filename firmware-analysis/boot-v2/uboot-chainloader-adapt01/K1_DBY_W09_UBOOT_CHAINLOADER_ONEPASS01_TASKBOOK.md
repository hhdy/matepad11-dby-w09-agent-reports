# K1_DBY_W09_UBOOT_CHAINLOADER_ONEPASS01
## U-Boot chainloader 一次性总执行任务书：证据闭环 → 主机端构建/打包 → 测试就绪判定

- 任务编号：K1_DBY_W09_UBOOT_CHAINLOADER_ONEPASS01
- 执行模式：**单一主 Agent、一次性全量执行、单份最终报告**
- 设备：Huawei MatePad 11 2021 DBY-W09 / HOS4.3 / SM8250 / VD
- 目标内核：ACK/GKI `android17-6.18.33_r00`
- 目标 ABL PE SHA-256：`a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`
- GitHub 仓库：`hhdy/matepad11-dby-w09-agent-reports`
- 分支：`ai1/boot-v2-first-package-prep`
- 先前基线：`K1_UBOOT_RECOVERY_ABL_HANDOFF_AUDIT01`，commit `7f03c2fd70598d9bf8a39eb58358ace7d0ab06a7`
- 本任务吸收并取代：`K1_UBOOT_CHAINLOADER_PREBUILD_GATE02_TASKBOOK.md`。不要把 GATE02 再作为独立任务启动。
- 重要边界：**本任务允许本地主机端源码检查、配置、构建、测试与候选文件制作；不授权任何设备连接、设备侧读取、临时启动、分区写入、刷写或 AVB/vbmeta 修改。**

---

## 0. 执行原则：一次布置，不再拆分小轮次

你是唯一主执行 Agent。按下面阶段顺序完成，但阶段只是同一任务内部的工作包，不是多个任务书：

1. 固定证据身份并读取既有报告；
2. 一次完成 ABL recovery 调用链、initrd 来源、RAM/FDT/reservation 剩余静态审计；
3. 一次盘点并确定 U-Boot 配置、源码版本、工具链与所有本地输入；
4. 在输入齐全时完成 U-Boot 主机端构建与 PIE/配置验证；
5. 在输入齐全时完成 ACK FIT、外置 Android ramdisk 的主机端组装与解析验证；
6. 在输入齐全且认证链允许的情况下，完成 recovery 容器的离线结构组装检查；
7. 完成所有可执行的 host-side 测试，形成唯一总决策。

**不要每完成一个阶段就停下来索要下一份任务书。**某个子项缺证据时，记录 UNKNOWN/BLOCKED，然后继续完成其他独立工作。不要为了追求“全 PASS”臆造地址、RAM tuple、密钥、配置或设备行为。

本任务最多一次执行、一次最终报告、一次 GitHub 回读。建议总时限 120 分钟；到时按已完成内容交付，不扩成第二轮。不得创建新的后续任务书，不得自动把缺口转成新一轮审计。

## 1. 基线复核与输入身份门禁

### 1.1 必须读取的现有报告

读取并使用以下已交付资料，不要重复其中已闭环的通用知识：

- `firmware-analysis/boot-v2/uboot-chainloader-adapt01/K1_UBOOT_RECOVERY_ABL_HANDOFF_AUDIT01_REPORT.md`
- `firmware-analysis/boot-v2/uboot-chainloader-adapt01/K1_DBY_W09_UBOOT_CHAINLOADER_ADAPT01_ADDENDUM01.md`
- `firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_PIE_ENTRY_AND_RUNTIME_RAMMAP_REVIEW.md`
- `firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_PREVBL_FDT_RAM_FALLBACK.md`
- `firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_EXTERNAL_ANDROID_RAMDISK_HANDOFF_FIX.md`
- `firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_ANDROID_RAMDISK_RAMMAP_CORRECTION.md`
- `firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_PREVBL_INITRD_REUSE_REVIEW.md`
- `firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_FIT_GZIP_LIMIT_REVIEW.md`
- `firmware-analysis/boot-v2/uboot-chainloader-adapt01/AI1_UBOOT_FIT_NATIVE_RAMDISK_ROUTE.md`
- `firmware-analysis/boot-v2/boot-load-map01/K1_BOOT_LOAD_MAP01_REPORT.md`
- `firmware-analysis/boot-v2/boot-load-map01/hybrid_abl_load_path.md`

如某路径不存在，记录 missing，不得用相似名字/其他版本报告冒充。

### 1.2 精确 ABL 身份

对实际本地使用的 ABL PE 重新计算 SHA-256，必须匹配：

```
a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404
```

不匹配或文件缺失：ABL 新审计部分立即 BLOCKED；其余不依赖 ABL 的主机端工作继续。禁止换用其他固件版本。

### 1.3 输入文件库存

对本地已经存在的文件只做 inventory，不联网下载固件、不连接设备：

- U-Boot 源码（目标优先 CoWave DBY-W09 U-Boot v2026.10，并记录精确 commit/tree）；
- DBY-W09 / VD defconfig、DTS/DTSI、已有补丁；
- ACK 源码、补丁集、最终 `Image`、目标 VD DTB；
- live separate ramdisk 现有备份；
- recovery、recovery_vbmeta 现有备份；
- toolchain、host build tools、已有构建目录、`.config`、map/elf/bin；
- FIT ITS、FIT、gzip kernel、日志与 SHA manifest。

所有输入记录路径、字节数、SHA-256、来源和版本。没有来源闭环的同尺寸文件不能视作正确输入。

---

## 2. ABL 剩余静态闭环（一次性完成）

本节只做 AUDIT01 明确留下的最小缺口，不重做已完成的常规反汇编。

### 2.1 recovery 间接调用链

基线保持：
- `RECOVERY_USES_COMMON_BOOTLINUX = CONDITIONAL`
- `RECOVERY_HANDOFF_FINAL_X0_FDT = CONFIRMED`（这是共享尾段寄存器不变量，不单独证明 recovery 已到达该尾段）

围绕 BootLinux `0x36C1C` 和最终 `blr x8`（约 `0x38868–0x3887C`）做一次寄存器/内存数据流检查：

1. recovery mode / BCB / partition-selection 到间接调用站点；
2. 函数指针槽的写入者、读取者和寄存器传递链；
3. 证明 recovery mode 条件是否选择该指针；
4. 输出至少两级逻辑调用关系和关键指令窗口；
5. 如果仍无法连接，保持 CONDITIONAL/UNKNOWN，列出缺失的最小寄存器或内存窗口，不再循环扫描。

### 2.2 recovery initrd 的 label、wrapper 与 payload

围绕 `LoadRamdisk`（候选 `0x3969C`）及其实际调用者：

1. 闭合 bootmode/recovery mode → 分区 label；
2. 明确区分 `ramdisk`、`recovery_ramdisk` 和其他名称；
3. 确定读取源 offset、复制长度、是否剥离 Android wrapper；
4. 判断最终 FDT `linux,initrd-start/end` 指向 wrapper 还是 gzip payload；
5. 不得把 normal boot 的 PREP04 结果套用到 recovery。

已有 live separate ramdisk 期望身份：
`4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb`。
只有本地字节重新哈希完全匹配时才允许使用；不得用 ROUND64 旧副本 `5c20e478…` 替代。

### 2.3 UpdateDeviceTree / RAM / reservation

围绕精确 PE 的 `0x3D9D0/0x3D9D4` 函数族和直接 helper/provider，做一次完整、受限的调用/数据流检查：

- 标准 `/memory/reg` 是否有实际写操作；
- `/reserved-memory` 子节点和 `no-map` / `reusable`；
- FDT memreserve map 是否真实新增 reservation；
- `/chosen/linux,initrd-start` 与 `linux,initrd-end`；
- vendor `RAM Partitions` 节点；
- EFI RAM Partition Protocol provider 与消费者分别在哪里。

字符串命中、grep 0、协议名称均不足以单独证明写入或未写入。对每个结论给出真实调用目标、指令地址和参数数据流。没有 byte-level final-FDT 时，最终非零 RAM tuples 必须保持 UNKNOWN；不使用用户报告的 12GB、CoWave HOS4.2 tuples 或 stock placeholder 推导。

输出：
- `RECOVERY_ENTRY_CHAIN`
- `RECOVERY_INITRD_LABEL`
- `RECOVERY_INITRD_PAYLOAD_FORM`
- `ABL_MEMORY_REG_MUTATION`
- `ABL_RESERVED_MEMORY_MUTATION`
- `ABL_INITRD_MEMRESERVE`
- `ABL_RAM_BANK_VALUES`

---

## 3. U-Boot 最终配置与源码固定

### 3.1 源码与工具链

1. 记录 CoWave DBY-W09 U-Boot v2026.10 源码精确 commit/tree；
2. 记录本地补丁顺序、每个补丁 SHA、应用结果；
3. 记录交叉编译器/版本、host 工具版本、构建环境；
4. 不从网络下载固件或安装新工具。缺少工具时标记 BLOCKED，继续做可做部分。

### 3.2 配置必须来自最终生成的 .config

优先检查本地最终 `.config`。若不存在且源码/工具链齐全，可在主机端生成配置并构建；这属于本任务授权的 host-side 工作。不得把 defconfig 或 Kconfig 默认值冒充最终值。

逐项记录实际配置：

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

要求：
- PIE 必须启用；
- Android wrapper 路线必须核实 `CONFIG_CMD_ABOOTIMG=y` 和 Android boot image parser 可用；
- 不得硬编码 CoWave 固定 RAM tuples 作为本机 HOS4.3 最终 RAM map；
- 优先保持 Snapdragon previous-BL FDT fallback 机制；
- 如果最终配置无法满足必要条件，修正本地 defconfig/配置并重新生成最终 `.config`，但不允许写设备。

### 3.3 U-Boot 主机端构建

仅当精确源码、补丁、工具链和 defconfig 均完整时执行：

1. 生成最终 `.config`；
2. 构建 U-Boot；
3. 保存 ELF、map、最终 .config、构建日志；
4. 验证 PIE relative relocations、入口地址/4KiB 对齐约束、初始栈配置；
5. 核对 U-Boot 二进制尺寸和 FIT/ramdisk parser 相关命令可用性；
6. 执行可用的 host/sandbox 单元测试。

不得声称 QEMU/sandbox 通过等于 DBY-W09 真机启动通过。构建失败要保留首个根因与日志，不得无限修补。

---

## 4. ACK Image / FIT / 外置 Android ramdisk 主机端组装

仅在精确输入已存在或可由已固定源码/补丁在本地主机端生成时执行。

### 4.1 ACK 内核与目标 DTB

目标：
- ACK/GKI `android17-6.18.33_r00`
- commit 基线 `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

核对实际 `Image` 和 VD DTB 的来源/哈希/配置/补丁。不能把其他机型 DTB、不同 ACK tag 或旧 Image 替代。

若只有源码无二进制，且 toolchain 与补丁齐全，可在主机端构建；否则说明缺少项，继续其他任务。

### 4.2 FIT

构建 FIT 前先核实：
- raw Image 的 header/load/alignment 属性；
- 目标 VD DTB；
- U-Boot 的 FIT support；
- gzip kernel 压缩后完整 FIT 由 kernel + DTB + ITS/metadata + padding 组成。

`reserved3` 已知容量为 25,165,824 B（24 MiB）。只有完整 FIT 文件实际存在后，才能以文件真实字节数判定是否放得下。仅有 gzip kernel 尺寸不能判 PASS。

不允许把未知 RAM tuples 写入 DTS/ITS。若必须靠 live final-FDT 才能确定 RAM map，本任务不连接设备，按 UNKNOWN 留在最终门禁。

### 4.3 separate ramdisk 外部 wrapper

优先沿用已 source-closed 的方案，不创建自定义 parser：

```
CONFIG_CMD_ABOOTIMG=y
abootimg addr <wrapper-address>
bootm <FIT-address> <wrapper-address>
```

第二参数必须是 plain hexadecimal address，禁止 `<address>:<size>`（冒号会触发 FIT subimage 解析）。

要求：
1. 对实际 live wrapper 精确 SHA、v0 header、payload offset/length 再次核验（不得仅引用历史 hash）；
2. 用 U-Boot v2026.10 实际 parser 做 host-side/sandbox 可行性验证；
3. 证明 ramdisk 被解释为 wrapper 内 payload，而不是把整个 2MiB wrapper 当 raw initrd；
4. 验证 initrd 搬移、LMB 范围、FDT chosen 属性与预留行为；
5. 若 parser 测试环境不支持，保留最小测试日志，标 PARTIAL，不得臆称已在目标机执行。

不在本任务内上传原始 ramdisk 或 CPIO 内容到 GitHub。

---

## 5. recovery 容器离线结构与认证门禁

本节只做主机端只读分析/离线候选结构检查，不改变任何设备分区。

1. 核对本地 recovery、recovery_vbmeta 的准确来源、完整 SHA-256、长度和 manifest provenance；
2. 确认 ABL recovery 分支实际的 `LoadImageAndAuth/LoadImageAndAuthVB2` 认证路径和 AVB/vbmeta 依赖；
3. 判断替换 recovery kernel 为 gzip U-Boot 是否能通过既有合法认证流程；
4. 不得绕过签名，不得伪造签名，不得修改 vbmeta/AVB 状态，不得移除验证机制；
5. 若必须依赖 OEM 私钥、签名授权或 vbmeta 修改才能启动，结论明确为 AUTH_BLOCKED / NO-GO；
6. 只有当原始 recovery 备份完整且认证流程有合法可用方式时，才允许在本地主机目录生成结构性 recovery 候选用于解析/尺寸/hash 检查。否则只输出离线结构计划，不生成伪装成可启动的镜像；
7. 即使生成了候选，也只能标记为 `UNSIGNED / NOT FOR DEVICE`，除非合法签名验证已被独立证明通过。

不得上传原始 recovery、recovery_vbmeta、boot、DTB、ramdisk 或其他设备固件二进制到公开仓库。只上传脱敏报告、工具源码、SHA/尺寸和日志摘录。

---

## 6. 主机端验证矩阵

在不连接设备的前提下，执行所有可行测试并记录准确范围：

| 测试 | 通过含义 | 不代表 |
|---|---|---|
| U-Boot build | 指定源码/配置能编译 | 真机可启动 |
| PIE/ELF 检查 | 重定位项和 4KiB 入口约束符合预期 | ABL 必然交接成功 |
| FIT parse/list | FIT 结构可被工具解析 | 真机内存布局安全 |
| Android v0 wrapper parse | wrapper ramdisk payload offset/size 正确 | recovery 一定选择该分区 |
| bootm command-path test | 命令参数/Android parser 路径成立 | 实际 DRAM/LMB 不重叠 |
| QEMU/sandbox | 模拟环境覆盖的代码路径通过 | Snapdragon/HOS4.3 真机通过 |
| image size check | 完整候选文件尺寸满足分区容量 | 认证/写入可行 |
| signature/auth review | 认证所需证据明确 | 获得 OEM 签名授权 |

测试中如出现失败，记录最先失败点、日志、输入 hash、复现命令。不得连续无目标试错。

---

## 7. 最终实测就绪门禁（只给决策，不执行实机操作）

分别给出三个结果：

### A. HOST_PACKAGE_READINESS
- `READY`：U-Boot、FIT、ramdisk 输入身份/构建/解析/尺寸均可复核；
- `PARTIAL`：部分输入或测试缺失；
- `BLOCKED`：关键源码/工具链/二进制缺失。

### B. DEVICE_BOOT_READINESS
必须逐项判断：
- recovery→BootLinux 的调用链是否 CONFIRMED；
- recovery initrd label/payload 形式是否明确；
- U-Boot 最终配置是否验证；
- HOS4.3 final FDT 是否有可用 RAM bank（无 byte-level 证据就 UNKNOWN）；
- ACK 37 个 reserved-memory children 与本机 HOS4.3 证据是否完成安全对照；
- initrd / U-Boot / FIT / FDT / reserved-memory 是否有冲突；
- recovery 和 recovery_vbmeta 备份是否完整；
- ABL/AVB/vbmeta 认证是否有合法通路；
- recovery 写入面恢复方案是否有已验证备份支持。

任一关键项 UNKNOWN、NO-GO 或 AUTH_BLOCKED，`DEVICE_BOOT_READINESS = NO_GO` 或 `HOLD`，不得用主机端测试 PASS 覆盖。

### C. USER_AUTHORIZATION_GATE
即使所有门禁通过，也只报告 `READY_FOR_EXPLICIT_USER_AUTHORIZATION`。本任务不执行设备连接、reboot、临时启动、分区读取或写入。不得自行升级授权。

最终总体状态：
- `ONEPASS_RESULT = HOST_READY_DEVICE_HOLD`
- `ONEPASS_RESULT = PARTIAL_BLOCKED`
- `ONEPASS_RESULT = READY_FOR_USER_AUTHORIZATION`

**READY_FOR_USER_AUTHORIZATION 不是刷写授权。**

---

## 8. 强制禁止事项

- 不连接设备；不运行 ADB、Fastboot、OEM、EDL、Sahara、Firehose。
- 不读取 live 分区，不执行 reboot、临时启动、recovery 选择或设备侧命令。
- 不写入、擦除、格式化、刷写任何分区。
- 不修改 ABL、XBL、boot、recovery、recovery_vbmeta、vbmeta、dtbo、ramdisk。
- 不修改 AVB、安全启动状态或绕过任何认证。
- 不伪造 OEM 签名，不使用未知密钥，不从其他固件提取认证材料。
- 不把原始固件、ramdisk、DTB、vbmeta、设备标识上传到公开仓库。
- 不使用未经证实的 CoWave 8GB tuples 作为本机 12GB RAM map。
- 不将 host/QEMU/sandbox 结果表述为实机结果。
- 不创建新的下一轮任务书，不把本任务拆成连续小任务等待用户再次派发。

---

## 9. 唯一交付物与停止条件

只提交一个综合报告：

`firmware-analysis/boot-v2/uboot-chainloader-adapt01/K1_DBY_W09_UBOOT_CHAINLOADER_ONEPASS01_REPORT.md`

报告必须包括：

1. 所有输入文件路径、commit/blob/hash、尺寸与 provenance；
2. 精确 ABL SHA-256；
3. recovery 间接调用链、initrd label/payload 结论；
4. UpdateDeviceTree / memory / reserved-memory / memreserve 数据流；
5. U-Boot 精确源码版本、补丁、工具链、最终 `.config`；
6. U-Boot 构建产物身份、PIE 检查与 host 测试结果（若已构建）；
7. ACK Image、DTB、FIT、ramdisk 输入和完整 FIT 尺寸（若已具备）；
8. recovery / recovery_vbmeta 备份与认证门禁；
9. HOST_PACKAGE_READINESS、DEVICE_BOOT_READINESS、USER_AUTHORIZATION_GATE；
10. 未闭合项的最小缺失证据；
11. 明确声明没有连接设备、没有设备侧读取、没有刷写/分区写入、没有 AVB/vbmeta 修改。

上传后必须从 GitHub 回读该报告，校验 commit、路径、内容和 SHA。**回读成功即为任务结束，不再创建后续任务书。**

---

## START_PROMPT（整段可直接交给本地 WorkBuddy Agent）

你是 K1_DBY_W09_UBOOT_CHAINLOADER_ONEPASS01 的唯一主执行 Agent。请一次性完成本任务书第 1–9 节的所有可执行工作：读取既有证据，完成剩余 ABL recovery/initrd/FDT 静态检查，盘点 U-Boot/ACK/DTB/ramdisk/recovery 输入，验证或生成最终 U-Boot 配置，在本地主机条件具备时构建 U-Boot、组装并测试 FIT 和 external Android ramdisk 路径，审核 recovery 容器结构与合法认证门禁，完成所有可行 host-side 验证，最后给出 HOST_PACKAGE_READINESS、DEVICE_BOOT_READINESS 和 USER_AUTHORIZATION_GATE。不要每个阶段结束后停下来请求新任务；缺项标 UNKNOWN/BLOCKED 后继续其余独立工作。不得连接设备、运行 ADB/Fastboot/OEM、读取 live 分区、reboot、临时启动、写分区、刷写、修改 AVB/vbmeta、绕过签名或上传原始固件。不得创建第二份任务书。最终只交付并回读核验一份 ONEPASS01 综合报告，回读成功立即停止。
