# AGENT_TASK_ROUND3.md — DBY-W09 Logical Partition 元数据与设备树分析

> 接续 round2。此次只做本地只读解析和文本报告，不刷机、不连接设备、不写分区、不编译内核。不要要求用户重新上传 HarmonyOS 4.3 固件，也不要把固件二进制上传到公开仓库。

## 已知基线（来自 round2，勿重新猜测）

- 设备：Huawei MatePad 11 DBY-W09。
- 原始固件目录：`D:\解锁bl\鸿蒙4.3\images`。
- 43 个镜像清单与 round1 一致。
- `boot.img`：Android boot header v2；kernel 22,264,379 B；ramdisk 519,986 B；page 4096 B；DTB 1,664,243 B。
- `dtbo.img`：magic `D7B7AB1E`；`total_size=2,963,810`；header size 32；entry size 32；entry count 9；header validation VALID。
- `super.img`：文件大小 7,114,729,004 B；Android sparse；block size 4096；total blocks 1,835,008；total chunks 127；理论 raw 大小 7,516,192,768 B（7 GiB）。
- round2 本地磁盘检查：D 盘约 333 GB 可用。
- round2 报告已上传到 `firmware-audit-v1:firmware-analysis/round2/`，用户报告最新提交为 `7e8e9ece4904b0ffaa2d1111a80c6091f9868e7c`。
- round2 没有安装或下载 `lpdump`、`lpunpack`、`simg2img`、`dtc`；没有展开 super，也没有提取任何分区。
- PR #1 仍为 Draft、未合并。不要合并 PR，不要改写/强推 feature branch。

## 仓库与分支

- 仓库：`hhdy/matepad11-dby-w09-agent-reports`
- 本任务文件在 `main` 分支。
- 分析脚本、测试和本轮报告提交到 `firmware-audit-v1` 分支。
- 开始前先检查本地工作区状态；不要覆盖未提交内容。
- 拉取 `firmware-audit-v1` 最新提交，并确认 round2 报告真实存在；若分支或提交与上文不同，以远端实际内容为准并记录。

## 安全边界

1. 所有源镜像只读打开，禁止覆盖、重命名、移动或修改源文件。
2. 不刷机、不连接平板、不运行 ADB/fastboot、不写设备分区、不编译或刷入内核。
3. 不安装新 Linux/WSL 发行版；不下载不明 EXE/DLL；不使用不明网盘、随机论坛或个人 release 的预编译工具。
4. 不为完成任务强行展开完整 7 GiB raw super。优先使用 Python 标准库实现只读的 sparse 虚拟读取。
5. 只允许将脱敏后的文本、CSV、JSON、源码和测试提交到公开仓库。禁止提交 `boot.img`、`dtbo.img`、`super.img`、DTB/DTBO 二进制、vendor/odm 镜像、内核/模块/固件二进制、PAT、序列号、MAC 或个人路径。
6. 如果解析边界、checksum、格式版本或设备树结构无法通过校验，必须停止该分支并报告，不得猜测或绕过校验。

## 第一部分：可信工具可用性复核（只检测，不安装）

在 Windows 当前环境检测：

```powershell
Get-Command lpdump,lpunpack,simg2img,dtc,python,python3 -ErrorAction SilentlyContinue |
  Format-List Name,Source,Version
```

若发现 `lpdump` / `lpunpack` / `simg2img` / `dtc`：
- 记录实际路径、版本信息、文件 SHA-256 和可证明的来源。
- 只有可确认来自本机 AOSP 构建产物或可信官方软件包的工具才可用。
- 如果无法证明来源，不运行该可执行文件；继续采用本任务规定的 Python 只读解析，或报告阻塞。
- 不允许为本轮安装 WSL / Linux 发行版。

AOSP 参考：
- Dynamic Partition Tools： https://android.googlesource.com/platform/system/extras/+/master/partition_tools/README.md
- AOSP `lpdump.cc` / `lpunpack.cc`： https://android.googlesource.com/platform/system/extras/+/master/partition_tools/
- AOSP Logical Partition metadata layout： https://android.googlesource.com/platform/system/core/+/master/fs_mgr/liblp/include/liblp/metadata_format.h
- AOSP metadata reader / checksum / bounds validation： https://android.googlesource.com/platform/system/core/+/master/fs_mgr/liblp/reader.cpp
- AOSP sparse image support： https://android.googlesource.com/platform/system/core/+/master/libsparse/

## 第二部分：super.img 的只读 Logical Partition 元数据解析

### 目标

读取 `super.img` 的 Logical Partition geometry、metadata slots、partition/group/block-device/extent tables，生成准确分区清单。**本轮不提取 vendor、odm 或任何分区二进制。**

### 优先方案：Python 标准库 sparse 虚拟读取

由于当前机器没有确认可用的 AOSP 工具，请在 feature branch 新增一个 Python 3 工具，例如：

- `tools/Analyze-DBY-W09-Super.py`
- `tools/Test-DBY-W09-SuperParser.py`

不得依赖第三方 Python 包；如确有依赖，必须先说明并停止等待确认，不要自动安装。

实现要求：
1. 以只读方式打开原始 `super.img`，不复制、不展开整个 7 GiB raw 文件。
2. 实现 Android sparse image 的随机访问虚拟读取层，严格校验 sparse header、chunk header、chunk 长度、总 block 数和文件边界。至少正确处理：
   - RAW chunk（`0xCAC1`）
   - FILL chunk（`0xCAC2`）
   - DONT_CARE chunk（`0xCAC3`，读作零填充）
   - CRC32 chunk（`0xCAC4`，校验/记录其存在；若不能正确处理则明确停止）
3. 不要只根据 64-byte 头部判断解析成功；遍历并验证全部 127 个 chunk 的边界与逻辑总长度，但不计算整个大文件哈希。
4. 按 AOSP `metadata_format.h` / `reader.cpp` 的结构和算法读取 geometry：
   - geometry magic、struct size、SHA-256 checksum；
   - metadata_max_size、metadata_slot_count、logical_block_size；
   - primary / backup geometry；
   - 几何区与 metadata / logical partition 区间不能重叠。
5. 从 AOSP `utility.cpp` / `reader.cpp` 核实 primary metadata offset 与 backup metadata offset 的精确公式，不要自行猜测偏移量。
6. 对 geometry 声明的每一个 metadata slot 读取 primary metadata；primary 校验失败时按 AOSP 规则读取 backup metadata。
7. 验证 metadata header magic、major/minor version、header_size、header SHA-256、tables_size、tables SHA-256，以及所有 table descriptor 的 offset/count/entry_size 边界。
8. 按实际 metadata 版本解析 partition / extent / group / block-device 表。至少输出：
   - partition name、attributes、group（若格式可关联）、first_extent_index、num_extents；
   - extent 的 num_sectors、target_type、target_data、target_source；
   - group name、flags、maximum_size；
   - block-device 的 partition_name、size、first_logical_sector、alignment、alignment_offset、flags。
9. 检查数组索引、extent 引用、block-device 索引、整数溢出和所有读区间；检测到不合法字段必须停止，不能静默跳过。
10. 所有 size 均转换为 bytes 时注明原始单位（extent 使用 512-byte sectors）；不能把 sector 数直接当成字节数。
11. 对所有 slots 输出摘要并比对；若 slot 内容不同，分别报告，不要擅自选择一个作为“正确版本”。

### 单元测试

在读取真实 `super.img` 前先通过合成测试：
- sparse RAW / FILL / DONT_CARE / CRC32 chunk 的随机范围读取；
- chunk 边界和展开逻辑长度检查；
- geometry magic 与 SHA-256 验证；
- metadata header / tables checksum 验证；
- table 越界、异常 entry_size、无效 extent 索引、非法 block-device 索引必须失败；
- 生成至少一个小型 synthetic sparse super 测试镜像，其中包含 1 个逻辑分区、1 个 group、1 个 block device 和至少 1 个 LINEAR extent。
- 测试需在 Windows PowerShell 可调用的 Python 3 环境运行并输出明确 PASS/FAIL。

如果无法实现通过校验的只读解析器，就只提交失败测试和技术阻塞报告；不要转而下载来历不明的工具。

### 输出

保存到全新本地目录，例如：
`D:\DBY-W09_FirmwareAnalysis_round3\`

期望报告：
- `super_sparse_validation.txt`
- `super_metadata_slot0.json`（实际存在的 slot）
- `super_metadata_slots_summary.json`
- `super_partition_summary.csv`
- `super_parser_test.txt`

JSON/CSV 必须记录数据来源和校验状态。partition 数量、slot 数量、group 数量以真实 metadata 为准，不预设 vendor/odm 一定存在。

## 第三部分：boot.img / dtbo.img 设备树信息提取

### 目标

识别华为设备实际使用的 FDT / DTB / DTBO 信息，收集 Qualcomm SoC、board ID、panel、touch、regulator、GPIO、I2C、SPI 等设备树证据。只在本地提取小型 DTB/DTBO 工作副本；二进制不得上传公开仓库。

### DTBO entry 处理

round2 的 `firmware_analysis.txt` 已给出 9 个 entry 的 size/offset。必须从 round2 报告重新读取这些数据，禁止手写猜测偏移。
- 对每个 entry 验证 offset + size 不超出 DTBO `total_size` 和源文件边界。
- 在输出目录单独提取 9 个 entry，源 `dtbo.img` 始终只读。
- 检查各 entry 是否为有效 FDT：magic `0xD00DFEED`、totalsize、structure/string/reserve-map offset 与 size 全部落在 blob 边界内。
- 对 FDT structure block 解码 token（BEGIN_NODE、END_NODE、PROP、NOP、END），检查深度/长度/对齐和字符串表引用，避免越界。
- 提取关键节点路径与属性，优先检索：
  `model`、`compatible`、`status`、`qcom,msm-id`、`qcom,board-id`、`qcom,pmic-id`、display/panel/DSI、touch/SPI/I2C、regulator、GPIO、pinctrl、clock。
- 同时记录 `__symbols__`、`__fixups__`、`__local_fixups__` 等 overlay 元信息（如存在）。
- DTBO entry 的 id/rev/custom 字段必须从原始 table 重新解析并输出，不能只保留 entry size 和 offset。

### boot.img 中的 DTB

- 从 `boot.img` 本地工作副本中查找并验证 FDT header；必须校验 totalsize 和所有 block ranges，不得仅用字符串搜索就认定存在 DTB。
- 如果识别出多个合法 DTB，逐个记录偏移、大小、model/compatible；不要只挑第一个。
- 如能够按 Android boot image 布局准确定位 DTB，应记录计算依据；否则标记为“扫描发现的 FDT candidate”，不要称为确定的 boot DTB。
- 对 DTB 使用与 DTBO 相同的结构解码逻辑。

### 设备树分析报告

至少输出：
- `device_tree_inventory.csv`：来源镜像、entry index、偏移、大小、FDT magic/validation、model、compatible。
- `device_tree_analysis.txt`：各 entry / DTB 的关键节点和属性摘要。
- `round3_summary.json`：实际完成项、失败项、校验状态、是否有多个候选 DTB。

不要将 Xiaomi 的 DTS 节点直接覆盖或合并到 Huawei 设备树。本轮只收集 Huawei 的实机固件设备树证据；之后再与 Xiaomi Pad 5 Pro（elish / enuma / dagu 需按 ZIP 内容确定）做逐项硬件比较。

## 第四部分：本轮禁止事项

- 不提取或解包 `vendor`、`odm`、`system`、`product`、`preload` 分区。
- 不解包内核/ramdisk，不运行刷机或固件更新脚本。
- 不修改 boot、DTBO、super 或其他源镜像。
- 不生成可供刷机的 boot.img / dtbo.img。
- 不下载/运行不可信工具二进制。
- 不上传任何镜像、DTB、DTBO、分区文件、驱动模块、固件二进制。

## 第五部分：提交与回报

只把以下内容提交到 `firmware-audit-v1`：
- Python 源码和合成单元测试；
- 脱敏的 TXT / CSV / JSON 报告；
- 必要的简短 README / 工具使用说明。

上传前扫描个人目录、用户名、序列号、MAC、PAT 和任何 token。原始固件文件永远留在用户本地。

完成后用中文汇报：
1. sparse / LP metadata parser 的测试通过情况；
2. 每个 metadata slot 的校验结果、真实 partition/group 数量；
3. 是否发现 vendor / odm 逻辑分区（只报告存在性和 metadata 信息，本轮不提取）；
4. DTBO 9 个 entry 的 FDT 验证情况；
5. boot.img 中发现的有效 FDT 数量与定位证据；
6. 是否提取了任何本地二进制工作副本（如有，明确说明只留本地）；
7. 本轮没有做的事情。

PR #1 继续保持 Draft、未合并。不要把本轮提交自动合并进 main。

## 完成标准

只有当 synthetic tests PASS、真实 sparse chunk 边界验证成功、LP metadata checksum/slot/table 验证成功，并且设备树结构解析有明确有效性证据时，才把对应分析项标记为完成。任何部分失败都要准确标为 BLOCKED / PARTIAL，不能以“脚本运行结束”冒充解析成功。
