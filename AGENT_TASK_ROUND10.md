# AGENT_TASK_ROUND10.md — DBY-W09 boot ramdisk / boot-chain 静态只读取证

日期：2026-11-24  
任务编号：ROUND10  
性质：本地已有 boot.img / ramdisk 的静态审查；只读，不连接设备。  
目的：为 ACK / GKI 6.18.33 boot-chain 适配补充证据，并寻找可能存在的 panel / lcd / display boot-time selector 线索。本轮不要求必须确定 ACTIVE_PROFILE。

## 0. 开始前阅读

1. 根目录 AGENT_TASK.md。
2. 本轮公开研究：kernel-baseline/round10/ack18-board-dts-migration-assessment.md。
3. 已有 ROUND2 / ROUND3 报告中关于 boot.img header、kernel/ramdisk/DTB 区域的记录。
4. ROUND9 报告只作为背景；不要重新解析 base FDT / DTBO。

## 1. 唯一目标

只对已经存在的 stock HarmonyOS 4.3 boot.img 及已存在的 boot/ramdisk 工作副本进行静态只读盘点，回答：

- ramdisk 压缩格式是什么（仅在可信工具/已存在脚本可判定时）？
- ramdisk 是否可在不安装工具、不绕过安全策略的情况下读取？
- init rc / fstab / prop.default / bootconfig / cmdline 中是否有 display、panel、lcd、Huawei display selection 相关的 property key、脚本触发器或文件路径？
- boot chain 是否引用 vendor / odm / system 的特定挂载、模块加载或 firmware 路径？
- 是否能从 boot ramdisk 找到面板选择线索？如果没有直接证据，明确写 ACTIVE_PROFILE=UNKNOWN。

本任务不是要求解包 vendor/odm，也不是要求通过猜测补齐面板型号。

## 2. 输入与范围

优先使用已知原始文件：
- D:\解锁bl\鸿蒙4.3\images\boot.img

若 ROUND3 / ROUND4 已有可信 boot header 或 ramdisk 工作副本，则优先使用其现有输出，不重复提取、不复制完整 boot image。

已知事实（不要重复声称为本轮新发现）：
- boot image header v2；
- 独立 ramdisk partition / region；
- kernel 22,264,379 B；
- ramdisk 519,986 B；
- page size 4096 B；
- boot 中 DTB region 1,664,243 B；
- 当前系统 Android 12 / API31，原内核 4.19.157-perf+。

不得要求用户重新上传固件或重述已知本地路径。

## 3. 只读执行要求

### A. 首先检查是否已有工作副本与工具

- 检查 ROUND3 / ROUND4 已有输出中是否存在 ramdisk 提取文件、boot unpack 工具或已审核过的 boot image 解析脚本。
- 只复用已有且可解释的工具 / 脚本；记录文件名和版本（若可得）。
- 只允许检测本机已经存在的工具。不得下载、安装或执行来源不明的 EXE/DLL。
- 不调用 WSL；不绕过 Windows 命令安全策略；不修改 PowerShell execution policy；不关闭安全软件。
- 若只能通过新增自制 Android boot image parser、未知归档解压器或未审核脚本才能继续，停止该子项并记为 BLOCKED。不得为了完成任务自行写 boot/FDT/DTBO/EROFS parser。

### B. Ramdisk 文件枚举

只有在现有工作副本 / 已有可信脚本 / 本机已安装且可信的工具链能够安全读取时才继续。

允许检查的内容：
- 文件路径 basename 或脱敏后的相对路径；
- init*.rc、fstab.*、prop.default、ueventd*.rc；
- module load directives / firmware path references；
- system/vendor/odm/product/cust 相关 mount statements；
- androidboot.* / ro.boot.* 等 boot property 名称；
- 与 panel / lcd / display / Huawei display service 有关的 property key、service name、触发器条件的字段名称。

禁止输出：
- 任何 token、密码、cookie、密钥、设备唯一标识；
- serial / IMEI / MAC / Wi-Fi / Bluetooth address；
- 设备私有 panel init sequence、display tuning payload、寄存器表；
- firmware blobs / binary modules；
- 完整原始 property 敏感值；
- 完整私人本地路径、用户名、主机名、完整本地 SHA-256。

### C. Panel selector 证据等级

对每一条线索明确分级：

- DIRECT_BOOT_SELECTOR：boot ramdisk 存在明确 property key / selector 路径，其值可安全脱敏且与 panel candidate 直接对应；即使如此也只能表述为 boot-time selector evidence，不等于 runtime active proof。
- INDIRECT_DISPLAY_BOOT_EVIDENCE：仅表明加载 display 服务、执行通用 LCD 脚本或挂载显示配置目录。
- NO_PANEL_SELECTOR_FOUND：在实际成功检查的 ramdisk 文件范围内未找到相关项。
- BLOCKED：由于 ramdisk 压缩 / unpack 工具缺失而未能检查。
- 永远不能仅靠 qcom,dsi-default-panel 静态 pointer 将状态改成 ACTIVE。
- 若缺乏最终 bootloader FDT / runtime 日志或 vendor/odm 真实选择配置，最终仍写 ACTIVE_PROFILE=UNKNOWN。

### D. Boot-chain mount / module / firmware path

只记录路径类别、挂载点、脚本引用和文件 basename。不得提取模块或 firmware 内容。

若找到 module load directive：
- 记录模块 basename / 加载阶段 / 来源分区类别；
- 不读取 .ko 二进制，不计算完整哈希，不试图装载模块；
- 将旧 4.19 模块与 ACK 6.18 KMI 的兼容性标记 UNKNOWN。

若找到 firmware path：
- 只记录文件名 / 目录类别，不提取文件、不打开 payload。

### E. 完成后清理

- 原始 boot.img 必须保持未修改。
- 若本轮创建临时解包目录，确认没有覆盖 ROUND1–ROUND9 历史输出。
- 不得上传任何二进制或包含敏感值的完整 ramdisk 文件。
- 如果只读工具无法保证安全，不提取，记录 BLOCKED 原因。

## 4. 输出文件

新建目录：
D:\DBY-W09_FirmwareAnalysis_round10\

只输出 UTF-8 文本：

1. round10_boot_ramdisk_inventory.txt
   - 工具 / 工作副本可用性；
   - ramdisk 格式与读取结果；
   - 脱敏文件 inventory；
   - mount / module / firmware 相关路径索引；
   - panel / lcd / display selector 命中与证据等级。
2. round10_boot_chain_summary.json
   - 输入文件是否存在（不含完整路径）；
   - 是否读取 header / ramdisk；
   - 用到的已有工具 / 脚本；
   - 文件数量、selector 命中统计；
   - BLOCKED / UNKNOWN 原因；
   - 边界布尔值（device_connected=false、adb=false、fastboot=false、flashed=false、unlocked=false、rooted=false、wrote_partitions=false、kernel_compiled=false、wsl_invoked=false、erofs_unpacked=false）。
3. 可选：round10_panel_profile_evidence.txt，仅在有可复核 selector 线索时生成。

## 5. GitHub 上传

只上传上述纯文本脱敏报告至：
- 仓库：hhdy/matepad11-dby-w09-agent-reports
- 分支：firmware-audit-v1
- 目录：firmware-analysis/round10/

上传前复查，不得出现：
- boot.img / ramdisk / DTB / DTBO / kernel / module / firmware binary；
- panel command payload / tuning / EEPROM / OTP / calibration；
- token / PAT / cookie / password / keys；
- serial / IMEI / MAC / 私人完整路径 / 用户名 / 主机名；
- 完整本地 SHA-256。

若只读检查受工具限制，应上传简短的 BLOCKED 文本报告，而不是自行找工具绕过。

## 6. 严禁事项

- 不重新提取原始固件，不扫描其他目录。
- 不读取 vendor/odm EROFS，不调用任何 EROFS 工具。
- 不重新解析 DTB/DTBO，不重写 FDT/DTBO parser。
- 不刷机、不解锁、不连接设备，不运行 ADB / fastboot。
- 不 root、不写分区、不加载模块、不挂载可写文件系统。
- 不编译内核、不运行 repo / Bazel / Kleaf / make / clang。
- 不调用 WSL、不绕过 Windows 命令安全策略、不下载未知 EXE/DLL。
- 不把任何二进制文件上传到 GitHub。

## 7. 完成标准

- 明确 ramdisk 能否在现有可信工具条件下安全检查；
- 对所有 selector 线索保留证据等级，不夸大；
- 无法读取时明确 BLOCKED，不写虚构 inventory；
- ACTIVE_PROFILE 没有 runtime / final FDT 证据就继续 UNKNOWN；
- 只上传脱敏纯文本；
- PR #1 仍为 Draft，不合并。
