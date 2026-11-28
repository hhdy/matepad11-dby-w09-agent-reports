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
- 本任务吸收并取代：`K1_UBOOT_CHAINLOADER_PREBUILD_GATE02_TASKBOOK.md`。GATE02 报告已于 commit `8d1f1190762ee6399448230a2479aac2a96ba5df` 交付并回读；其结论作为本任务固定基线，不再重复执行 GATE02。
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
- `firmware-analysis/boot-v2/uboot-chainloader-adapt01/K1_UBOOT_CHAINLOADER_PREBUILD_GATE02_REPORT.md`（commit `8d1f1190762ee6399448230a2479aac2a96ba5df`）

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

**GATE02 已经完成 900 指令窗口（0x3D9D4 起，149 个 BL，gBS 加载调用 @0x3E1A0）并交付 `evidence_updtdt_full.txt`。本任务先核对该证据；不得原样重复该 900 指令 pass。**只有在本地已有更完整的函数边界/反汇编或 provider 文件时，才做一次增量核对，重点识别 GATE02 尚未证明的真实 FDT 写入接口。没有新证据就沿用 `NOT_FOUND_IN_ANALYZED_PATH` / `UNKNOWN`，继续其余工作。

围绕精确 PE 的 `0x3D9D0/0x3D9D4` 函数族和直接 helper/provider，增量检查：

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
4. 允许从官方/公开源码仓库获取纯源码，并固定 commit/tree；禁止下载设备固件、闭源分区镜像或未知二进制，也不安装新工具。缺少既有工具链时标记 BLOCKED，继续做可做部分。

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

你是 K1_DBY_W09_UBOOT_CHAINLOADER_ONEPASS01 的唯一主执行 Agent。GATE02 commit 8d1f1190 已完成并回读，直接采用其证据，不重复已完成的 900 指令窗口。请一次性完成本任务书第 1–11 节的所有可执行工作：读取既有证据，完成剩余 ABL recovery/initrd/FDT 静态检查，盘点 U-Boot/ACK/DTB/ramdisk/recovery 输入，验证或生成最终 U-Boot 配置，在本地主机条件具备时构建 U-Boot、组装并测试 FIT 和 external Android ramdisk 路径，审核 recovery 容器结构与合法认证门禁，完成所有可行 host-side 验证，最后给出 HOST_PACKAGE_READINESS、DEVICE_BOOT_READINESS 和 USER_AUTHORIZATION_GATE。不要每个阶段结束后停下来请求新任务；缺项标 UNKNOWN/BLOCKED 后继续其余独立工作。不得连接设备、运行 ADB/Fastboot/OEM、读取 live 分区、reboot、临时启动、写分区、刷写、修改 AVB/vbmeta、绕过签名或上传原始固件。不得创建第二份任务书。同时把六份 recovery 备份核验、U-Boot/ACK/FIT 主机端工作、认证检查、FDT 对照及授权后的设备验证流程全部按本任务书一次性纳入执行范围；未授权的设备阶段只标 AUTHORIZATION_REQUIRED。最终只交付并回读核验一份 ONEPASS01 综合报告，回读成功立即停止，不得再创建后续任务书。


---

## 10. GATE02 已完成结果：固定基线，不得再拆任务重复执行

GATE02 于 commit `8d1f1190762ee6399448230a2479aac2a96ba5df` 已交付，报告路径：

`firmware-analysis/boot-v2/uboot-chainloader-adapt01/K1_UBOOT_CHAINLOADER_PREBUILD_GATE02_REPORT.md`

本轮确认以下事实，ONEPASS Agent 必须直接采用：

| 子项 | 已交付状态 | 后续处理 |
|---|---|---|
| A1 recovery 间接调用 | `CONDITIONAL`，BL/静态指针扫描 0 命中 | 只允许一次以 loader/最终 `blr` 为根的数据流增量检查；仍缺则保留 CONDITIONAL |
| A2 recovery initrd label | `PARTIAL`；候选 `ramdisk` / `erecovery_ramdisk`；payload form UNKNOWN | 一次检查 LoadRamdisk 调用者参数；不套用 PREP04 normal 路径结论 |
| UpdateDeviceTree | 已有 900 指令窗口、149 BL、gBS 加载 @`0x3E1A0`；标准 `/memory/reg` 与 reserved-memory 为 `NOT_FOUND_IN_ANALYZED_PATH` | 不重复原窗口；仅用新函数边界/provider 证据做增量检查 |
| initrd memreserve | `UNKNOWN` | 不把 chosen start/end 等同 reservation |
| RAM bank | `RUNTIME_DEPENDENT`；EFI_RAMPARTITION provider 不在冻结 PE | 不推算物理 bank tuples |
| U-Boot `.config` | `MISSING` | 从固定源码/defconfig 在本地主机生成最终配置；无法构建则说明原因 |
| FIT | `UNKNOWN_NOT_BUILT` | 完成 host-side 组装前置条件后实际构建、解析、计量；不能假报 PASS |
| recovery 链备份 | `INCOMPLETE`；六个文件在 r155 copies-primary 在册，但 SHA/provenance 未闭环 | 在本地一次性对六文件及 manifest 逐项闭环；不从设备补采 |
| 总体 | `PREBUILD_READINESS = HOLD` | 不可提升为实机可写或可刷 |

六个备份对象必须分别核验：
- `recovery.img`
- `recovery_ramdisk.img`
- `recovery_vbmeta.img`
- `erecovery.img`
- `erecovery_ramdisk.img`
- `erecovery_vbmeta.img`

每个文件必须记录原始采集 manifest、源 label、路径、长度、SHA-256、采集时间及 manifest 一致性。仅“文件在册”不等于完整备份。任何一个关键项缺少 provenance，恢复/刷写门禁仍为 NO-GO。

---

## 11. 一次性完整执行路线：从当前状态直至实机验证结束

下列项目全部属于同一主任务，不得另发任务书。Agent 应在一次执行中完成所有无需用户补充授权的工作；遇到设备侧授权门槛，只记录待授权，不得擅自执行。

### 11.1 静态证据最终收敛

完成第 2 节规定的 ABL 增量检查，目标仅是：
- recovery 是否实际到达 common BootLinux 尾段；
- recovery LoadRamdisk 的准确 label 与 payload form；
- ABL 是否写入 RAM bank、reserved-memory 或 initrd reservation。

对已由 GATE02 充分覆盖的 900 指令窗不重复扫描。找不到 caller/provider 时以最小缺口结束，不再开展同类字符串搜索。

### 11.2 recovery 链备份闭环

在现有 r155 copies-primary 文件夹内完成六文件 hash + manifest provenance。若本地实际文件路径缺失或 manifest 不全：
- 不通过文件名/长度推断；
- 不联网下载闭源固件；
- 不连接设备重新采集；
- 记录缺失对象和其唯一缺失证据。

若六项全部闭环，形成只读恢复清单；原文件保留不变，不重新压缩、不覆盖。

### 11.3 U-Boot 源码、配置、构建与测试

1. 固定 CoWave DBY-W09 U-Boot v2026.10 的源码 commit/tree 与补丁清单；
2. 检查 toolchain 和 defconfig；生成唯一最终 `.config`；
3. 检查第 3.2 节全部 CONFIG 项；
4. 构建 U-Boot ELF/map/bin；
5. 核验 PIE、relative relocations、4 KiB entry alignment、initial stack、FIT 与 Android boot image parser 命令；
6. 运行所有可用 sandbox/host 测试；
7. 归档构建日志、配置、map、ELF 和产物 SHA。

若源码/工具链不能取得或构建失败，记录首个可复现根因，不再创建“修复任务书”；其余静态打包分析继续。

### 11.4 ACK Image / DTB / FIT 与 ramdisk 完整组装

1. 锁定 ACK commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`、设备 VD 配置和补丁；
2. 锁定 Image、目标 VD DTB 的来源和 SHA；
3. 核验 Image header、kernel load、2 MiB Linux Image 物理对齐要求；
4. 在主机端生成 gzip kernel、ITS、完整 FIT；
5. 核算完整 FIT 与 reserved3 25,165,824 B 的容量关系；
6. 使用 U-Boot 自身工具解析 FIT，并核验 FIT configuration、kernel、FDT 和地址属性；
7. 对 live separate ramdisk `4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb` 重新 hash；仅匹配后解析 v0 wrapper；
8. 使用 `CONFIG_CMD_ABOOTIMG=y`、`abootimg addr <wrapper-address>` 与 plain-address `bootm <FIT-address> <wrapper-address>` 路径做 host/sandbox 验证，禁止冒号形式；
9. 用 sandbox/单元测试核验解析出的 ramdisk payload 范围、搬移、LMB 冲突检查和最终 FDT chosen/initrd 处理。

FIT 若实际超过 24 MiB，优先在不改变内核语义、不丢 DTB/reservation 的前提下分析压缩与 metadata；不得静默裁剪内核、DTB 或 ramdisk。无论 FIT 是否通过，sandbox 通过不等于设备验证通过。

### 11.5 FDT / RAM / reserved-memory 最终安全对照

1. 对 ACK VD DTB 中 37 个 reserved-memory children 形成脱敏表：节点名/用途类别、size、no-map、reusable、compatible/consumer 类别；不公开不必要的物理地址；
2. 与已有 HOS4.3 DTB/FDT 报告逐项比较；
3. 标记每个节点为 MATCH / DIFFERENT / UNKNOWN；
4. 确认 U-Boot 会如何将真实 `gd->dram[]` 更新进 ACK FDT 的 `/memory/reg`；
5. 确认 U-Boot LMB 对 U-Boot 本体、FIT buffer、DTB、initrd、ABL reserved ranges 的保护；
6. 对于 ABL final-FDT 真实 RAM tuple 与 reserved-memory 无证据的部分，保持 UNKNOWN；不以 CoWave HOS4.2 tuples 填补；
7. 在缺少真实 RAM map 时，不得把静态地址布局宣称为无重叠或设备可启动。

### 11.6 Recovery 容器与合法认证

1. 完成六份 recovery 链文件身份和恢复能力闭环；
2. 完成 ABL recovery 的 LoadImageAndAuth/LoadImageAndAuthVB2、vbmeta/AVB 依赖图；
3. 判断 U-Boot recovery 容器能否由现有合法签名/认证链接受；
4. 如果必须使用未提供的 OEM 私钥、关闭验证或修改 vbmeta，立即 `AUTH_BLOCKED / NO-GO`；
5. 仅在输入、备份和合法认证门禁均通过后，才可制作主机端离线候选；未签名候选必须标记 `UNSIGNED / NOT FOR DEVICE`；
6. 候选必须通过 Android boot/recovery header、DTB/recovery_dtbo、分区容量、hash、container parser 检查；
7. 不得生成可误刷的“最终版”文件名，不得上传原始固件。

### 11.7 设备侧只读 FDT 证据（授权门）

唯一权威的 HOS4.3 真实 RAM bank/reservation 证据是设备运行时 final-FDT 字节或等价可信只读采集。GATE02 已说明本地静态 PE 不能证明非零 `/memory/reg`。

本任务书提前列出该步骤，但**没有设备操作授权**。只有用户之后明确授权特定只读采集时，Agent 才可：
- 使用用户明确指定的只读方式采集 final FDT；
- 不读取/导出其他私有分区，不写分区、不重启；
- 对采集结果本地 hash，并解析 `/memory/reg`、`/reserved-memory`、memreserve、`/chosen/linux,initrd-start/end`；
- 公开仓库只交付脱敏 tuple/范围类别和哈希，不上传原始 FDT 或可识别物理布局的敏感数据。

没有授权则本阶段保持 `AUTHORIZATION_REQUIRED`，继续完成其余任务并提交总报告。

### 11.8 实机启动验证与回退（预先布置，严格授权门）

本任务把完整测试顺序和验收标准一次性布置好，但**任务书不构成实机操作授权**。只有同时满足下列全部条件且用户针对具体操作明确授权时，才可执行相应设备步骤：

- HOST_PACKAGE_READINESS = READY；
- recovery/recovery_vbmeta 及所有相关写入面备份逐项 SHA/provenance 完整；
- 认证路径合法，候选已通过独立签名/认证验证；
- final FDT RAM banks、reserved-memory、initrd、U-Boot/FIT/DTB 地址范围无重叠证据；
- 有经验证的恢复步骤与所需原始备份；
- 设备型号、固件版本、电量、数据风险与可能失去启动能力的风险已明确；
- 用户明确批准具体测试动作（只读检查、非持久临时启动或指定分区写入必须分别说明，不能把一次授权扩展到其他动作）。

执行顺序：
1. 先只读确认当前设备身份/固件和启动状态（仅在单独授权后）；
2. 若硬件/ABL 确实支持非持久加载路径，先做一次非持久测试；不可用就停止，不用未验证方法强试；
3. 采集完整 UART/USB/ABL/U-Boot/Linux 启动日志，按阶段判定 ABL entry、U-Boot PIE relocation、DRAM、FDT、FIT、kernel entry、earlycon、initcall、rootfs；
4. 一旦发现地址冲突、FDT 内存异常、启动卡死或不可解释重启，立即停止，不自动重复启动；
5. 只有临时启动获得明确成功日志且用户再次明确授权，才可考虑持久化恢复/写入路径；
6. 任何分区写入前必须再次核验原始备份 SHA、目标分区 label/大小/布局和恢复命令；写入后只读回读并对比 hash；
7. 若失败，按事先验证过的原始备份恢复，不得临场猜测分区或写入命令。

若认证链不允许、无 OEM key、不能做安全临时启动、或无可验证恢复方案，则 `DEVICE_BOOT_READINESS = NO_GO`，不尝试刷入。

### 11.9 最终报告必须一次给出全链路结果

唯一总报告应包括各阶段结果：
- ABL 静态证据；
- GATE02 已有证据及本轮增量；
- 六份备份 provenance；
- U-Boot 源码、工具链、最终配置、构建日志、ELF/map/hash；
- ACK Image/DTB/FIT/ramdisk 的 hash、尺寸和 host parser 测试；
- reserved-memory 对照和 RAM/LMB 区间安全；
- recovery auth/AVB/vbmeta 判定；
- final FDT 授权状态及设备实测结果（如获授权）；
- HOST_PACKAGE_READINESS、DEVICE_BOOT_READINESS、USER_AUTHORIZATION_GATE；
- 明确推荐继续、暂停或 NO-GO 的唯一决策。

**最终总报告发布并回读后，整个任务结束。不得再另发 PREBUILD_GATE03、FIT_AUDIT、FLASH_TASKBOOK 或类似分拆任务书。**



---

## 12. 2026-11-28 用户明确授权：主机工具安装 + 一次性构建续行（本节优先级高于旧限制）

用户在 2026-11-28 明确回复“继续”，对应主机侧安装编译依赖并继续构建的授权。**本节覆盖本任务旧版 §3.1“不得安装新工具”的限制**，仅在以下边界内生效：

- 允许：在本地 Ubuntu 24.04 构建主机上用系统 APT 安装 U-Boot / FIT 主机端构建依赖；固定公开 CoWave 源码及 U-Boot v2026.10；生成最终 .config；构建 U-Boot；在输入身份核验通过时制作、解析和计量 ACK FIT；做离线 parser / sandbox / ELF / FIT 验证。
- 不允许：连接 DBY-W09；运行 ADB、Fastboot、EDL、Sahara、Firehose 或 OEM 命令；读取设备分区；reboot / recovery / 临时启动；写分区、刷写；修改 recovery、recovery_vbmeta、vbmeta、AVB、安全启动状态；绕过或关闭签名验证；上传任何原始设备固件。
- 这不是设备操作授权。即使 host build 和 FIT 全部 PASS，仍不得触碰设备。

### 12.1 Ubuntu 24.04 APT 安装范围

先只读盘点 OS、磁盘空间、已有包版本、工具是否存在；记录安装前状态。只在确认为 Ubuntu 24.04 的构建主机上执行。允许一次 APT 安装，按需安装缺失项：

```bash
sudo apt-get update
sudo apt-get install --no-install-recommends \
  build-essential make git curl xz-utils bzip2 bc bison flex \
  gcc-aarch64-linux-gnu device-tree-compiler u-boot-tools \
  libssl-dev libgnutls28-dev libncurses-dev libpython3-dev \
  python3 python3-dev python3-setuptools python3-pyelftools \
  swig pkg-config
```

注意：
1. 不运行 `apt upgrade`、`full-upgrade`、`autoremove`，不添加 PPA、不下载第三方 .deb、不改系统源。
2. 如果部分包已安装，保留现有版本，不必重复安装；若包名在该 Ubuntu 版本不存在，先记录并停止该包，不得擅自改用来源不明的软件。
3. APT 若要求用户输入 sudo 密码/交互确认，等待用户在本机授权输入；不得尝试绕过。
4. 安装后保存 `dpkg-query` 包版本、`aarch64-linux-gnu-gcc --version`、`dtc --version`、`mkimage -V`、`make --version`、`python3 --version` 和完整 APT 日志。
5. 不安装 adb/fastboot/EDL 工具；本任务不需要这些设备工具。

### 12.2 CoWave 源码固定（禁止跟踪浮动分支）

本轮已通过 GitHub API 核实的 CoWave 仓库固定点：

- Repo：`https://github.com/CoWave-Fall/linux-on-arm-matepad11`
- `main` 当前审计固定 commit：`b76d7e095104fc2a010f2d1dc43121a9e3484464`
- Tree：`2d6b79e3df31bfad1001da6e565a155794b5e7f7`
- 该 commit 未签名（GitHub verification reason=unsigned），报告中必须记录，不得称签名验证通过。
- U-Boot 上游目标 tag：`v2026.10`；CoWave 固定脚本给出的源码压缩包 SHA-256：`f943a88389c8fd70a6b0d061a88267465e143c7ca6ea2b75837ab20f5b60c739`。下载后必须核验 SHA；若不匹配，停止使用该源码包。

必须固定并记录以下 CoWave 文件身份（按该 commit 读取并核对本地内容）：

| 文件 | Git blob SHA |
|---|---|
| `uboot/dby-w09_defconfig` | `38a39ecd60f25360ceabe2ee81f1f1e96564b52c` |
| `uboot/patches/0001-gpio-qcom-pmic-add-bias-and-input-config.patch` | `c17d6a2dd4a393f110e829ee5b236adb37932c53` |
| `uboot/patches/0002-button-gpio-apply-pinctrl-default.patch` | `72cebdaae482f97eedcfe644f47b66469fcf7ff8` |
| `uboot/patches/0003-input-button-kbd-initialize-state.patch` | `bedfbbe01310e17aecda64adf54abfffee37684f` |
| `uboot/patches/0004-dts-qcom-add-dby-w09.patch` | `bc10cbcde24275c91dcf56ef8f9e8562260c3714` |
| `uboot/patches/0005-board-qualcomm-add-dby-w09-env.patch` | `f07d01f1f073f63ae8b75493dd6560f56c2d4dca` |
| `scripts/build-uboot.sh` | `bb1e94b8b0cad0df4eca9b771bca77fd53770ca7` |
| `scripts/pack-fit.sh` | `529bebcf3fe0380d4c21b4998467db42898f3584` |
| `scripts/pack-recovery.sh` | `0f3076bcd397f8d694a950b49bfd381cb571fee4` |
| `scripts/fetch-sources.sh` | `a640962b7f985904cb330d6355bbdf009fc1e8e8` |

执行规则：
- checkout 到精确 commit `b76d7e095104fc2a010f2d1dc43121a9e3484464`，记录本地 HEAD、tree、所有补丁 SHA；不得以最新 main 替换。
- 仅使用 U-Boot v2026.10；CoWave 的 `fetch-sources.sh` 会同时抓取 Linux 7.3.4，**不得运行它来代替 ACK 6.18.33 目标内核构建**。可只按已固定 SHA 获取 U-Boot v2026.10 源码包。
- 先静态阅读 `build-uboot.sh`、所有 5 个 patch、defconfig，再应用补丁；确认 patch 顺序与源树匹配，保留 pristine tree 和 patched tree 的差异摘要。
- CoWave defconfig 是板级配置参考，不等于最终 .config；本机 HOS4.3 / ACK 项目所需的差异必须有源码和运行时证据。

### 12.3 高风险脚本明确禁用

**绝对禁止运行 CoWave `scripts/pack-recovery.sh`**。本轮已读取该固定 commit 的脚本内容：它会生成 `recovery_vbmeta.img`，并以 `avbtool make_vbmeta_image --flags 2` 生成“关闭校验”的 vbmeta。这与本项目禁止 AVB/vbmeta 修改、不得绕过认证的要求直接冲突。不得复制其输出、参数或做法。

同时禁止运行：
- `tools/host/boot-linux.sh`（其用途涉及 fastboot/设备启动操作）；
- 任何 recovery 写入、fastboot flash、reserved3 写入、设备 boot 命令；
- CoWave 的 `scripts/build-kernel.sh`，除非仅作静态阅读。该脚本目标为 Linux 7.3.4，不是本项目 ACK `android17-6.18.33_r00`，不可将其输出冒充本项目 ACK。
- 不得运行含 `avbtool`、`fastboot`、`adb`、`dd`（指向设备）、`flash`、`reboot` 的打包/部署流程。

`scripts/build-uboot.sh` 只可在审计脚本内容、将源码和输出路径限定为项目独立 host workspace 后运行；任何副作用不得触及设备或用户原始固件文件。

### 12.4 最终 .config 与 U-Boot 构建

在固定的 CoWave U-Boot v2026.10 源码 + 5 个 patch + defconfig 上完成一次构建。构建前后保存：
- pristine source commit/tree、patched tree hash / diff；
- patch apply log；
- defconfig SHA；
- `.config` 原件及 SHA；
- 完整构建日志；
- `u-boot` ELF、`u-boot.bin`、map 文件及 SHA/长度；
- `readelf -h/-l/-r`、PIE/relocation/entry alignment 审计结果。

最终配置必须从生成的 `.config` 读取，不能从 defconfig 推断。重点核验：
- `CONFIG_POSITION_INDEPENDENT=y`
- `CONFIG_INIT_SP_RELATIVE` 的最终值
- `CONFIG_SYS_INIT_SP_BSS_OFFSET`
- `CONFIG_ARCH_SNAPDRAGON=y`
- `CONFIG_SAVE_PREV_BL_FDT_ADDR` 相关功能实际启用情况
- `CONFIG_SAVE_PREV_BL_INITRAMFS_START_ADDR`
- `CONFIG_CMD_ABOOTIMG=y`
- `CONFIG_ANDROID_BOOT_IMAGE=y`
- `CONFIG_FIT=y`
- `CONFIG_CMD_BOOTM=y`
- `CONFIG_OF_LIBFDT=y`
- `CONFIG_OF_BOARD_SETUP=y`
- `CONFIG_NR_DRAM_BANKS`
- `CONFIG_SYS_BOOTM_LEN`
- `CONFIG_USB_FUNCTION_FASTBOOT`

若 `CMD_ABOOTIMG` 缺失或因依赖未启用，基于本地 Kconfig 做一次明确配置调整并重新生成 .config；仍不可用则标记 ramdisk handoff BLOCKED，不得自写 parser 规避证据。CoWave defconfig 未显式列出 `CONFIG_CMD_ABOOTIMG`，不能假定它默认启用。

**内存策略**：
- 不把 CoWave 的三个固定 RAM tuples 或静态约 7.93 GiB RAM 布局移植到 HOS4.3 的 12GB 报告设备。
- 检查其控制 FDT 的 `/memory/reg` 处理以及 Qualcomm `board_fdt_blob_setup()` previous-BL fallback 路径；若要删除控制 FDT 的静态 memory reg，必须先做源码级审查并在报告说明变更理由，不能在无最终 FDT 证据下自行填入 bank 值。
- ABL final-FDT / RAM bank 值仍为 UNKNOWN，host build 不能提升此门禁。

### 12.5 ACK / FIT 的一次性主机端构建与验证

目标仍是 ACK/GKI `android17-6.18.33_r00`，commit 基线 `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`。只用确切 ACK 源码/补丁/输入，不得使用 CoWave Linux 7.3.4 内核。

1. 从本地冻结目录 inventory ACK Image、VD DTB、gzip 输入、ITS、外置 ramdisk；对每项重算 SHA/长度并关联 PREP 来源。缺少就用已固定 ACK 源码及已验证补丁在主机端构建；不得下载闭源固件或从 CoWave 拿 DTB 代替。
2. 如果 ACK/DTB 构建依赖缺包，可一次性把必要公开 Ubuntu 软件包加入同一次 APT 安装（仅构建依赖）；记录新增包名及版本。不要安装与设备操作有关的工具。
3. gzip ACK Image 既有数据为 17,860,410 B（17.04 MiB），但最终容量只以真实生成的完整 FIT 文件长度为准。
4. 生成 FIT 时明确 image type、compression、load/entry 地址、FDT binding 和配置名；不要使用未经证明的 HOS4.3 RAM tuples。核验 FIT 完整文件 `<= 25,165,824 B`（reserved3 24 MiB）并以 `dumpimage -l` / `mkimage -l` 等实际解析输出证明结构。
5. 外置 Android ramdisk wrapper 使用此前 source-closed 路径：`CONFIG_CMD_ABOOTIMG=y`、`abootimg addr <plain-hex-wrapper-address>`、`bootm <FIT-address> <plain-hex-wrapper-address>`。禁止 address:size / 冒号格式。对本地 wrapper 重算 SHA，必须匹配 live wrapper 固定身份 `4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb`；不匹配则停止对该副本的解析。
6. 执行 parser / sandbox / FIT listing / LMB 范围静态测试。必须把“parser 接受 wrapper”与“目标 DRAM 里无重叠 / initrd 已被安全保留”分开判定；后者缺 final-FDT / memreserve 证据仍 UNKNOWN。
7. 不把 FIT 成功解析或主机端 build PASS 表述为真机启动验证。

### 12.6 六份 recovery 备份 provenance 处理

仅在当前本地文件/manifest 已存在时做一次完整复核：
- `recovery.img`
- `recovery_ramdisk.img`
- `recovery_vbmeta.img`
- `erecovery.img`
- `erecovery_ramdisk.img`
- `erecovery_vbmeta.img`

对每个文件核验路径、大小、SHA-256、原始采集 label、源 manifest 记录及采集时间。重点解释 `recovery.img == erecovery.img`、`recovery_ramdisk.img == erecovery_ramdisk.img` 的 hash 相同现象：对照原始采集 manifest 和文件复制日志，不得通过重命名/文件名/长度推断身份。无 manifest 原始记录时维持 provenance UNKNOWN / recovery write surface NO-GO，不得连接设备重新读取。

### 12.7 本轮唯一交付和停止条件

在当前 ONEPASS01 下只更新一份综合报告：
`firmware-analysis/boot-v2/uboot-chainloader-adapt01/K1_DBY_W09_UBOOT_CHAINLOADER_ONEPASS01_REPORT.md`

报告至少增加：
- 用户 host-install authorization 的范围与执行日期；
- Ubuntu 版本、安装前后包清单/版本、APT 日志；
- CoWave 固定 commit/tree、所有五个补丁和 defconfig blob SHA；
- U-Boot v2026.10 tarball SHA、最终 .config、build output hashes、PIE/ELF 验证；
- ACK Image / VD DTB / wrapper 的实际输入身份、完整 FIT 实际长度、FIT parser / sandbox 日志；
- 六份 recovery provenance 的最终结论；
- 单独列明 CoWave `pack-recovery.sh` 被禁止的原因（flags=2）；
- HOST_PACKAGE_READINESS、DEVICE_BOOT_READINESS、USER_AUTHORIZATION_GATE 的新值。

若任一构建项缺失，先保留根因、继续其他独立步骤；最终单报告交付后立即停止。GitHub 上传仅限脱敏报告和文本日志摘要，不上传 U-Boot/ACK/FIT/DTB/ramdisk/recovery/vbmeta 二进制，不创建新任务书。

### START_PROMPT_OVERRIDE（本节覆盖旧 START_PROMPT 的“不安装新工具”句）

你是 K1_DBY_W09_UBOOT_CHAINLOADER_ONEPASS01 唯一主执行 Agent。用户已明确授权在本机 Ubuntu 24.04 主机通过 APT 安装 U-Boot/FIT 构建所需的软件包，并继续主机端源码固定、U-Boot 构建、ACK 6.18.33 / VD DTB / FIT 组装和离线验证。请按本任务书 §12 一次执行到底，不得再创建新任务书或每完成阶段向用户索要下一轮任务。先盘点，随后只安装 §12.1 列出的缺失构建包；固定 CoWave 源码到 commit `b76d7e095104fc2a010f2d1dc43121a9e3484464` 和 U-Boot v2026.10 精确源码；核对 5 个 patch；完成最终 .config、U-Boot build、ACK/FIT/ramdisk parser 测试和六份备份 provenance 复核。明确禁止运行 CoWave `pack-recovery.sh`（该脚本用 AVB flags=2 关闭校验）、`boot-linux.sh`、任何 adb/fastboot/OEM/EDL 命令、任何设备连接、重启、临时启动、分区读取或写入，且禁止修改任何 vbmeta/AVB 状态。缺少最终 FDT 或 recovery provenance 时保留 HOLD/NO-GO。最终只更新并回读核验 ONEPASS01 综合报告，回读成功立即停止。


---

## 17. 用户明确授权：当前 HOS4.3 运行态 final-FDT 一次性只读取证（2026-11-29）

本节是用户在 2026-11-29 明确批准的窄范围设备只读授权，仅覆盖当前已启动的 HOS4.3 系统中的 final-FDT 导出及最低限度身份/权限核验。本节仅在与旧版 §8 / §12 的“完全不连接设备”条款冲突时，对本节明列的读取动作作例外；除此之外所有禁止事项继续有效。

### 17.1 授权范围

允许执行一次：
1. 使用已经配置、已经授权的本地 ADB 传输连接当前正在运行的 HOS4.3 系统；
2. 只读采集 /sys/firmware/fdt 原始 FDT 二进制；
3. 只读读取最少设备身份字段，用于证明采集对象确为目标 DBY-W09 / HOS4.3：ro.build.fingerprint、ro.build.version.release、ro.build.version.incremental、ro.product.device、ro.boot.hardware。不要采集序列号、IMEI、账号或其他个人数据；
4. 本地核验 FDT magic/header/总长度/SHA-256，解析 /memory/reg、/reserved-memory 的全部子节点、/memreserve/ map、/chosen/linux,initrd-start、linux,initrd-end、bootargs（只在报告必要字段，不公开完整 bootargs）；
5. 对照 U-Boot 控制 DTB 中保留的 6 个 reserved-memory / framebuffer 项和 ACK VD DTB 中 37 个 reserved-memory children，逐项标记 MATCH / DIFFERENT / ABSENT / UNKNOWN；
6. 只上传脱敏的解析报告、SHA-256、尺寸、节点名/地址/属性差异；原始 final-FDT 二进制只保留在本地，不上传 GitHub。

### 17.2 执行前置条件

- 必须是当前已启动的 HOS4.3 正常系统，不得通过重启、切换启动模式、进入 Recovery/Fastboot 或临时启动来取得。
- 仅能使用已经可用的 ADB transport；不得为了本任务启用开发者选项、修改 USB 调试配置、运行 adb tcpip、adb connect、安装设备端应用或更改系统属性。
- 可先运行只读的 adb devices -l 和上述 getprop 字段检查目标身份；不要把设备序列号写入公开报告。
- 只读权限优先。读取原始文件时可在当前已授权的 root 环境下使用一次性 su -c cat；如出现新的 root 授权弹窗、需要修改 superuser 策略、需要 remount 或更改权限，立即停止并将权限门记为 BLOCKED，不能自行批准持久 root 权限或修改设备设置。

### 17.3 唯一允许的采集方式

优先从当前运行系统导出原始扁平 FDT：

    mkdir -p final-fdt-capture
    adb devices -l
    adb shell getprop ro.build.fingerprint
    adb shell getprop ro.build.version.release
    adb shell getprop ro.build.version.incremental
    adb shell getprop ro.product.device
    adb shell getprop ro.boot.hardware
    adb exec-out su -c 'cat /sys/firmware/fdt' > final-fdt-capture/hos43-final-fdt.dtb

执行后必须检查：
- 输出文件非空；
- 读取的 FDT magic 是 big-endian 0xd00dfeed；
- FDT header 的 totalsize 不大于文件实际长度，且不小于 header 最小长度；
- 对原始文件记录精确字节数及 SHA-256；
- 用本地 fdtdump / dtc -I dtb -O dts / fdtget 解析；任何解析错误都保留日志并标记 INVALID，不得手工修补后冒充原始 FDT。

如果 /sys/firmware/fdt 不存在或不可读：
- 可以只读检查 /sys/firmware/devicetree/base 的存在性和权限，报告为辅助信息；
- 不得把 sysfs 展开树伪装为原始 FDT；它不能替代原始 FDT header/memreserve map；
- 不得使用 /dev/mem、/proc/kcore、任意物理地址扫描或其他旁路读取方式；
- 不得重启或切换 Recovery 以寻找另一个 FDT；
- 报告 FINAL_FDT_CAPTURE = BLOCKED/PARTIAL，任务照样完成并停止。

### 17.4 解析与审计要求

对取得的原始 FDT 解析并报告：

**A. FDT 身份 / 来源**
- 五个允许的 build/product 字段；
- 文件路径（本地）、实际字节数、SHA-256、FDT magic、totalsize、version/last_comp_version；
- 明确注明这是当前正常 HOS4.3 启动会话的 Linux 可见 final-FDT。它不自动证明 recovery 模式的 FDT 完全相同；recovery 路径仍需按已有 ABL 条件结论标记。

**B. RAM bank**
- /memory 节点是否存在；
- device_type、#address-cells、#size-cells；
- 原始 reg bytes 与按 cell 解码出的每个 (base,size,end)；
- 每个 bank 的 64-bit overflow、零长度、对齐、彼此重叠和排序检查；
- 总 RAM 仅作为各 bank size 的和报告，不从产品名或“12GB”报告倒推。

**C. Reserved memory / memreserve**
- /reserved-memory 的 cells/ranges；
- 每个子节点的名称、reg、no-map、reusable、alignment、size、compatible、status 等实际存在的关键属性；
- 根 FDT memreserve map 的所有 (address,size) tuple；
- 对照 U-Boot 控制 DTB 的 6 个节点（cont-splash@9C000000、framebuffer@9C000000、四个 Qualcomm sm8250.dtsi carveout）和 ACK VD DTB 的 37 个 reserved-memory children，逐项给出 MATCH / DIFFERENT / ABSENT / UNKNOWN；
- 重点判断 0x9C000000 + 0x2300000（35 MiB）区域是否真实存在于 final-FDT、是否有 no-map / reusable 差异、是否与其他 carveout 冲突；
- 不得因为节点名相同就宣称地址/属性匹配。

**D. initrd / chosen**
- /chosen/linux,initrd-start 与 linux,initrd-end 的原始 cell、解码值、长度；
- 与 live separate ramdisk 身份/长度及 ABL 已证据作静态一致性比较；
- 明确 SAVE_PREV_BL_INITRAMFS_START_ADDR 只读取 start 的事实，不能把它表述成 end 已保存或 memreserve 已建立；
- 对 initrd 与 RAM bank/reserved regions 的重叠做算术分析；未证 reservation 时不能声称安全。

**E. 对 U-Boot fallback 的判定**
- 结合已验证控制 DTB 根级 /memory 已移除、U-Boot v2026.10 board_fdt_blob_setup() / qcom_parse_memory() 源码，以及本次取得的有效 final-FDT：
  - 若 raw final-FDT 有有效非零 /memory/reg：ABL_FINAL_FDT_RAM_SOURCE = PRESENT；源码层 external fallback 可提供 bank source，但仍未实机运行 U-Boot。
  - 若无有效 RAM reg：ABL_FINAL_FDT_RAM_SOURCE = INVALID，U-Boot 将无法从该 external FDT 成功初始化 RAM，维持 NO-GO。
  - 若文件无效或未取得：UNKNOWN/BLOCKED。
- 严格区别“源码路径能够 fallback”和“目标 U-Boot 已在设备运行并采用该 FDT”。不能把前者写成实机运行结果。

### 17.5 禁止事项（本次授权不覆盖）

- 不执行 adb reboot、fastboot、recovery、临时启动、boot、flash、erase、format、OEM、EDL、Sahara、Firehose。
- 不运行 adb root（若当前系统不支持则不要重启 adbd）；不运行 adb remount、adb disable-verity、adb tcpip、adb connect。
- 不修改 /sys、/proc、/dev 节点，不 chmod/chown，不修改 bootargs、属性或配置，不安装 APK/二进制。
- 不读取任何分区、vbmeta、recovery、boot 或其他原始固件；本授权只读 /sys/firmware/fdt 和最低限度 getprop 字段。
- 不对设备执行写入、刷写或恢复操作；不修改 AVB/vbmeta/安全启动。
- 不把原始 FDT、完整设备属性转储或设备序列号上传公开 GitHub。

### 17.6 单次交付 / 停止条件

在原 ONEPASS01 综合报告中新增 final-FDT capture 结果，不创建新任务书。唯一更新：
firmware-analysis/boot-v2/uboot-chainloader-adapt01/K1_DBY_W09_UBOOT_CHAINLOADER_ONEPASS01_REPORT.md

更新内容必须包含：
- 本节授权的使用范围；
- 当前 HOS4.3 设备身份字段（脱敏）；
- 原始 FDT 本地路径/尺寸/SHA/header 校验结果；
- RAM bank、memreserve、reserved-memory 及 initrd 解析表；
- 6 个 U-Boot 控制 FDT 项和 ACK 37 个 reserved-memory children 的对照结果；
- fallback 是否满足所需输入条件（不宣称 U-Boot 已实机启动）；
- 重新计算 HOST_PACKAGE_READINESS、DEVICE_BOOT_READINESS、USER_AUTHORIZATION_GATE；
- 明确声明无重启、无分区读取、无分区写入、无 AVB/vbmeta 修改。

若 capture 成功，完成全部解析和一次 GitHub 回读后停止；若 capture 被权限/路径阻断，记录最小缺口、继续所有可完成的本地 FDT/节点对照后交付并停止。不得自动扩成下一轮、不得执行任何实机启动/刷写。

### START_PROMPT_OVERRIDE — 当前 HOS4.3 final-FDT 只读采集

用户已于 2026-11-29 明确批准一次当前 HOS4.3 正常运行态 final-FDT 只读采集。现在按本任务书 §17 执行一次：仅使用现有 ADB transport，读取规定的五个非敏感 build/product 字段及 /sys/firmware/fdt 原始二进制；优先保持当前权限，必要时只允许一次性 su -c cat，不能触发持久权限策略修改。不得重启、切换模式、读其他分区、写设备、修改 AVB/vbmeta、使用 /dev/mem 或物理内存扫描。把原始 FDT 留在本地，计算 hash/header，解析 RAM banks、memreserve、reserved-memory 全量节点、chosen initrd 区间，并对照 U-Boot 6 项与 ACK 37 项。若原始 FDT 不可读，停止设备侧尝试，不得改用旁路方法；报告 BLOCKED/PARTIAL。最终只更新原 ONEPASS01 综合报告并 GitHub 回读，完成即停止。