# AGENT_TASK_ROUND4.md — DBY-W09 vendor / odm 选择性只读提取与驱动清单

> 接续 round3。目标是从本地 HarmonyOS 4.3 `super.img` 中，仅提取 metadata 已确认的 Huawei DBY-W09 `vendor` 与 `odm` 逻辑分区，用于识别文件系统、内核模块、固件文件和 VINTF 配置。所有源镜像保持只读；不连接设备、不刷机、不写设备分区、不 root、不编译内核。

## 一、输入和可信基线

本地原始固件目录仍为：
`D:\解锁bl\鸿蒙4.3\images`

本地源文件：
`D:\解锁bl\鸿蒙4.3\images\super.img`

先读取仓库最新的：
- `firmware-analysis/round2/round2_summary.json`
- `firmware-analysis/round3/round3_summary.json`
- `firmware-analysis/round3/super_metadata_slot0.json`
- `firmware-analysis/round3/super_metadata_slot1.json`
- `firmware-analysis/round3/super_metadata_slots_summary.json`
- `firmware-analysis/round3/super_partition_summary.csv`
- `firmware-analysis/round3/super_sparse_validation.txt`
- `firmware-analysis/round3/tools/Analyze-DBY-W09-Super.py`
- `firmware-analysis/round3/tools/Test-DBY-W09-SuperParser.py`

### Round3 核验基线（执行时仍须从报告/源镜像复核）

- Android sparse：block size 4096；total blocks 1,835,008；total chunks 127；raw logical size 7,516,192,768 B。
- 114 RAW、7 FILL、6 DONT_CARE；全部 chunk 边界和逻辑 block 总量检查 PASS；无 CRC32 chunk。
- Geometry：metadata slot count 2；metadata max size 65,536；logical block size 4096；checksum PASS。
- slot0 与 slot1 的 primary/backup metadata 均 VALID；metadata 内容 SHA-256 相同：`746EBF7AA5CD431C77BCB05CD63855689F1B110E256895C969462D58B44CE7C8`。
- Block device table：index 0，partition `super`，size 7,516,192,768 B，first_logical_sector 2048。
- `vendor`：metadata extent index 4，LINEAR，num_sectors 1,996,168，size 1,022,038,016 B，target_data 11,907,072，target_source 0。
- `odm`：metadata extent index 2，LINEAR，num_sectors 100,768，size 51,593,216 B，target_data 5,539,840，target_source 0。
- 两个分区属性均为 `0x00000001`（READONLY），group 为 `qti_dynamic_partitions`，每个分区目前均为一个 LINEAR extent。

## 二、严格只读边界

1. `super.img` 只能以只读方式打开；不修改、不重命名、不移动、不覆盖、不原地转换。
2. 禁止执行 ADB、fastboot、刷机脚本、OTA/updater 脚本或任何设备端操作。
3. 禁止安装新 Linux / WSL 发行版；禁止下载来源不明的 EXE/DLL/驱动工具。
4. 不生成完整 7 GiB raw super；只允许在本地独立输出目录生成 vendor/odm 分区工作副本。
5. 不提取 `system`、`hw_product`、`cust`、userdata、modem 或其他分区。
6. 原始固件目录必须保持不变；执行前后用文件名、大小、修改时间快照对比 `super.img`。
7. 固件二进制、内核模块、固件文件、DTB/DTBO、镜像、私人标识和 PAT 一律不得上传 GitHub。
8. 本任务的“只读”指源固件、设备与分区完全只读。允许在源目录之外创建本地提取工作副本和文本报告。

## 三、AOSP extent 映射规则（必须遵守）

AOSP `LpMetadataExtent` 规定 LINEAR 的 `target_data` 是物理分区上的 sector 起点；`target_source` 是 block_devices 表索引。AOSP `lpunpack` 将源偏移计算为：

`super_offset_bytes = target_data * 512`

**不要再加 `first_logical_sector * 512`，也不要从 target_data 减去 first_logical_sector。** `first_logical_sector` 用来验证 LINEAR extent 起点不早于可分配区域，并非第二次偏移量。

权威源码：
- `LpMetadataExtent` 字段定义： https://android.googlesource.com/platform/system/core/+/refs/heads/main/fs_mgr/liblp/include/liblp/metadata_format.h
- AOSP `lpunpack.cc` 的 `super_offset = extent.target_data * LP_SECTOR_SIZE`： https://android.googlesource.com/platform/system/extras/+/refs/heads/main/partition_tools/lpunpack.cc
- AOSP `writer.cpp` 的物理 sector 下界/上界验证： https://android.googlesource.com/platform/system/core/+/master/fs_mgr/liblp/writer.cpp

## 四、工具实现和提取前验证

使用 round3 已通过 22/22 合成测试的 `SparseImage` 虚拟读取器，禁止复制/展开 raw super。

建议新增独立脚本：
- `firmware-analysis/round4/tools/Extract-DBY-W09-LogicalPartitions.py`
- `firmware-analysis/round4/tools/Test-DBY-W09-LogicalPartitions.py`

不要破坏或重写 round3 的原始分析脚本。新脚本可通过 importlib 导入 round3 的 `Analyze-DBY-W09-Super.py`，也可复制必要的 SparseImage 代码，但需说明来源，保持标准库依赖。

### 在真实提取前必须全部满足

1. 重新打开源 `super.img`，执行完整 127 chunk 边界与数据长度验证。
2. 重新解析 geometry 与 metadata；slot0/slot1、primary/backup checksum 必须全部 PASS，metadata canonical 内容必须相同。若发生变化，停止并报告。
3. 对每个欲提取分区从 metadata 按名称查找，禁止硬编码 extent index、大小或 offset。
4. 仅接受 `target_type=LINEAR` 的 extent；`target_source` 必须索引有效 block device；本次预期 index 0 的 `super`。
5. 校验 `target_data >= first_logical_sector`。
6. 校验 `target_data + num_sectors <= block_device.size / 512`，并做无溢出边界检查。
7. 计算每个 extent 的读取偏移 `target_data * 512` 和字节数 `num_sectors * 512`。多 extent 分区按 metadata 顺序拼接；本次报告预期 vendor / odm 各 1 个 extent，但必须以真实 metadata 为准。
8. 每个 extent 起点、结束点、partition 总字节数必须对齐 logical_block_size；不满足就停止，不擅自补齐。
9. 合成测试先 PASS：
   - RAW / FILL / DONT_CARE 的交叉边界提取正确；
   - 多 extent 按顺序拼接；
   - ZERO extent 或未知 target type 按 AOSP 语义处理，若尚未实现则必须 fail closed；
   - 越界、负值/整数溢出、错误 block-device index、短读等均拒绝；
   - 输出长度、SHA-256 与预期字节一致。
10. 测试输出必须标明所有 fixtures 是合成数据，不读取真实固件。

## 五、选择性提取 vendor / odm 到本地独立目录

目标路径建议：
`D:\DBY-W09_FirmwareAnalysis_round4\partitions\`

为避免覆盖已有输出：
- 如目录已存在，创建新的带序号或时间标签子目录；不得覆盖旧结果。
- 输出 `vendor.img` 与 `odm.img`，仅为本地分析工作副本。
- 分块读取 SparseImage 虚拟逻辑视图，每次建议 1–4 MiB；禁止一次性将大分区读入内存。
- 写入工作副本时，原始 `super.img` 仍保持打开为只读。
- 完成后核对实际输出长度与 metadata 计算长度，计算工作副本 SHA-256，并保存到本地清单；hash 仅用于本地报告校验，**不要上传分区二进制**。
- 如目标磁盘空间不足、读取报错、任何 checksum/bounds 校验失败，停止，不继续提取其他分区。

预期 baseline（执行时必须重读 metadata）：
| 分区 | 预期 offset（bytes） | 预期 size（bytes） |
|---|---:|---:|
| odm | 2,836,398,080 | 51,593,216 |
| vendor | 6,096,420,864 | 1,022,038,016 |

这些值来自 `target_data * 512` 与 `num_sectors * 512`。若真实读取值与这些基线不符，先报告差异，不要按表格强制提取。

## 六、识别文件系统与只读文件清单

先用只读签名识别，不挂载、不修复、不重放 journal、不执行文件系统写操作：
- ext4：检查 superblock magic `0xEF53`（superblock 起始 1024 B，magic 字段偏移 56 B）；
- EROFS：检查 EROFS superblock magic `0xE0F5E1E2`（通常位于 1024 B 起始位置）；
- F2FS：检查 superblock magic `0xF2F52010`（按官方格式核实其偏移）；
- 其他格式记录原始 magic/签名，不猜测。

检测本机已有的只读分析工具，例如 `debugfs`、`e2ls`、`dump.erofs`、`fsck.erofs`、`file`、`7z`、`bsdtar`、`modinfo`、`readelf`、`strings`。先查看版本和 help，确认来源；不得下载未知二进制或安装 Linux。

如为 ext4：
- 仅使用 `debugfs -R` / `e2ls` 等只读查询方式；
- 禁止 `debugfs -w`、`e2fsck` 修复、可写 mount；
- 尝试清点目录（存在时）：
  - `/lib/modules`
  - `/vendor/lib/modules`
  - `/vendor_dlkm/lib/modules`
  - `/lib/firmware`
  - `/vendor/firmware`
  - `/vendor/firmware_mnt/image`
  - `/etc/vintf/manifest.xml`
  - `/vendor/etc/vintf/manifest.xml`
  - `/etc/vintf/manifest`
- 按真实文件系统路径调整，以实际目录为准，不假设目录一定存在。

如为 EROFS：
- 只有本机存在可信 `dump.erofs` / `fsck.erofs` 或等价官方工具时，先查 help 并使用明确的只读列表/导出功能；
- 不执行修复，不调用未知参数；
- 若没有可信只读工具，停止在文件系统识别层，报告 blocker，不要自行实现未经验证的 EROFS 解码器。

如为其他文件系统：
- 先记录识别证据，未经格式确认不要尝试挂载或解包。

### 驱动 / 固件 / VINTF 清单

如目录读取可用，收集以下信息：
1. 内核模块：
   - 文件路径、文件名、大小、压缩后缀（如 .ko/.ko.xz/.ko.gz/.ko.zst）；
   - 若有可信 `modinfo` 或 `readelf`，记录 vermagic、depends、ELF machine/class；
   - 不执行或加载模块，不修改模块；
   - 不要因文件名含某驱动名称就断定硬件存在，需结合 DTS / manifest 属性。
2. firmware：
   - 文件路径、名称、大小、文件类型；
   - 按 UFS/Qualcomm、GPU、Wi-Fi/BT、DSP、camera、display/touch 等类别做“候选分类”，证据不足时标 UNKNOWN；
   - 不复制固件二进制到 GitHub。
3. VINTF / manifest：
   - 记录 HAL interface、instance、version、transport、kernel FCM level（若存在）；
   - 摘要 vendor/odm 的 manifest 与 compatibility matrix 文件路径；
   - 只上传脱敏文本摘要，不公开原始设备标识。

## 七、与 GKI 6.18.33 的可移植性判断

结合 round1 的旧系统内核 `4.19.157-perf+`、本轮 vendor/odm 信息与 round3 设备树：
- 区分 vendor modules 是 4.19 厂商模块还是其他内核版本；
- 识别 `vermagic`、模块依赖、是否存在 GKI/KMI/ABI 线索；
- 标出可能属于 Qualcomm common/platform 的驱动候选，以及 Huawei board-specific 驱动；
- 标出需要对应源代码才能适配的驱动；不要声称仅凭 .ko 可迁移到 6.18；
- 标出依赖旧 Android vendor interface / KMI 的风险；
- 不修改任何 defconfig，不构建内核，不加载模块。
- 小米 elish ROM 没有 kernel source/DTS/defconfig，且其 boot 为 APatch repack；不得将其预编译镜像或模块拿来代替华为 vendor 证据。

## 八、报告与提交

本地输出：
`D:\DBY-W09_FirmwareAnalysis_round4\`

至少生成：
- `partition_extraction_report.txt`
- `partition_hashes_local.csv`（如含 SHA-256，仅上传经过脱敏且被用户接受的摘要？默认不上传 hash 文件，以防泄露设备镜像身份；保留本地）
- `filesystem_inventory.csv`
- `kernel_modules_inventory.csv`
- `firmware_inventory.csv`
- `vintf_summary.txt`
- `round4_summary.json`
- 合成测试输出 `partition_extractor_test.txt`

GitHub 上传限制：
- 可以上传脱敏后的 TXT / CSV / JSON 报告，但默认不上传完整分区 SHA-256；除非用户后续明确要求。
- 不上传任何 vendor.img / odm.img、内核模块、固件文件、manifest 原件、DTB/DTBO 二进制或私有原始文件。
- 不上传含本地完整路径、设备序列号、MAC、token、PAT、证书或密码的内容。
- 不修改 round1/round2/round3 历史报告，不改写主工具脚本，不合并 PR #1。
- 分析源码/测试脚本可提交至 `firmware-analysis/round4/tools/`。

## 九、完成后汇报

清楚区分：
- 已通过的合成测试；
- 已复核的真实 metadata / extent；
- 实际已提取的分区与准确字节数；
- 实际识别的文件系统；
- 实际列出的模块、firmware、VINTF 信息；
- 因缺少可信工具而停止的项目；
- 未做事项：未展开完整 super、未提取其他逻辑分区、未 root、未连接平板、未刷机、未写设备分区、未编译内核。

任何步骤未完成必须标记 PARTIAL / BLOCKED。不能把“文件成功输出”说成“文件系统已成功解析”。

## 完成标准

只有在 synthetic tests PASS、metadata slots 和 extent 校验重新 PASS、vendor/odm 输出长度与 SHA-256 本地核验成功后，才可将“分区提取”标为 PASS。文件系统解析、模块清单、firmware 清单和 VINTF 分别独立报告 PASS / PARTIAL / BLOCKED。
