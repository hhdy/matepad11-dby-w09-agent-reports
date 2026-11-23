# AGENT_TASK_XIAOMI_ZIP.md — 本地小米平板 5 Pro 分卷移植包只读盘点

> 本任务针对用户本机 `D:\123pan\Downloads` 下的两个小米平板 5 Pro 移植包。两个包均为分卷压缩。先识别卷组、验证完整性，再只读盘点内部内容。不要要求用户重新上传文件，也不要把原始压缩包或解出的固件二进制上传到公开 GitHub。

## 任务目标

判断两个压缩包分别属于什么类型、对应什么设备代号，以及其中哪些资料能帮助 Huawei MatePad 11 DBY-W09（Qualcomm KONA / SM8250 系）Android GKI 6.18.33 移植研究。

候选设备代号仅作为识别线索，不能预设：
- `elish`：Xiaomi Pad 5 Pro 11-inch Wi-Fi 相关包；
- `enuma`：Xiaomi Pad 5 Pro 5G 相关包；
- `dagu`：Xiaomi Pad 5 Pro 12.4-inch 相关包。

包的实际型号必须由包内 manifest、目录、DTS model/compatible、build properties 或可靠元数据确认，不得仅按 ZIP 文件名推断。

## 输入位置与边界

- 本地目录：`D:\123pan\Downloads`
- 目录中用户指出有两个包，且均为分卷压缩。
- 不要扫描或上传该目录下无关个人文件；优先按 Xiaomi / Pad 5 Pro / elish / enuma / dagu / ROM / kernel / port 等文件名线索筛选，再结合文件大小、时间、扩展名确认候选。
- 不要移动、重命名、删除、覆盖或修改原始压缩卷。
- 所有输出放在独立目录，例如 `D:\DBY-W09_XiaomiReference_Audit\`。
- 本任务与 `AGENT_TASK_ROUND3.md` 并行；不要覆盖 round3 的工作区或输出目录。

## 第一阶段：识别两个分卷集合（只读，不解压）

1. 记录候选文件的：
   - 原始文件名；
   - 扩展名；
   - 字节大小；
   - 修改时间；
   - 所属卷组推断和理由。
2. 识别常见分卷命名：
   - ZIP multi-volume：`.z01/.z02/... + .zip`；
   - 7-Zip：`.7z.001/.7z.002/... 或 .001/.002/... `；
   - RAR：`.part1.rar/.part2.rar...` 或旧式 `.rar/.r00/.r01...`；
   - 其他格式必须依据文件头识别，不要只按扩展名认定。
3. 明确区分“两套压缩包”与“同一套压缩包的多个卷”。不要把两个不同 base name 的分卷混在一起。
4. 检查卷号是否连续、是否缺卷、是否有同名冲突、是否出现卷号重复或大小异常。
5. 若无法确定分组，停止解压，仅输出候选表和需要用户确认的文件名，不要猜测。

## 第二阶段：压缩包完整性验证（仍不解压）

1. 只使用本机已安装且来源可信的 7-Zip / WinRAR / 官方系统工具；记录工具名称、版本、实际路径。
2. 不得下载随机网站、网盘或个人 GitHub Release 的可执行文件；不得安装新 Linux / WSL。
3. 对每一套分卷执行对应的只读 list/test 操作；必须从正确的首卷/主卷入口操作，不可单独测试某个中间卷。
4. 若有密码、缺卷、CRC 错误、unexpected end、unsupported method 或加密无法验证：
   - 如实记录；
   - 不尝试破解密码；
   - 不尝试从网上寻找同名固件；
   - 停止对该卷组进行解压。
5. 记录每套卷组是否：
   - ARCHIVE_LIST_OK；
   - ARCHIVE_TEST_OK；
   - MISSING_VOLUME；
   - CRC_ERROR；
   - ENCRYPTED_UNVERIFIED；
   - TOOL_UNAVAILABLE；
   - UNKNOWN_FORMAT。
6. 不要对大型卷做全量 SHA-256，除非本地已有校验值需要核对；记录已有官方 checksum 文件即可。

## 第三阶段：安全列出包内结构（只读）

在确认卷组完整可读取后，对两套包分别输出完整目录清单，但不直接全部解压。

优先搜集以下文件和线索：

### 设备身份 / 包类型
- README、说明文档、release notes、manifest、metadata、checksum；
- `build.prop`、`default.prop`、`vendor/build.prop`；
- `META-INF/com/android/metadata`、OTA metadata、updater-script（仅作为文本读取，不执行）；
- 包含设备 codename、model、board、SoC、Android version、kernel version 的文本。

### 内核 / 驱动源码
- `Makefile`、`Kconfig`、`defconfig`、`*_defconfig`、`.config`；
- `arch/arm64/boot/dts/` 下的 `.dts` / `.dtsi`；
- Qualcomm/KONA/SM8250 相关 DTS、clock、regulator、pinctrl、UFS、PCIe、USB、display、touch、audio 源码；
- kernel source 版本信息、git commit、submodule manifest、patch 文件名和头部说明。

### 预编译系统镜像 / ROM
- `boot.img`、`vendor_boot.img`、`dtbo.img`、`super.img`、`vendor.img`、`odm.img`、`vbmeta*.img`、`payload.bin`、`*.ko` 等只记录名称、大小和路径；
- 不要将这些二进制上传到公开仓库；
- 不要尝试刷机，不执行包内脚本或安装器。

为每个包生成：
- `package_1_inventory.csv` / `package_2_inventory.csv`（entry path、uncompressed size、compressed size、file type、classification）；
- `package_1_summary.json` / `package_2_summary.json`；
- `package_structure_report.txt`。

目录清单应防范恶意 archive path：
- 检测 `../`、绝对路径、盘符路径、UNC path、符号链接、重复文件名和路径穿越；
- 如发现危险路径，不解压该包，只记录风险 entry；
- 不运行任何包内 EXE、BAT、CMD、PS1、SH、Python、安装器或 updater-script。

## 第四阶段：选择性提取文本源文件（满足条件才做）

只有在以下条件全部成立时才可选择性提取：
1. 对应卷组完整性测试通过；
2. ZIP 内所有路径通过安全检查，不存在路径穿越/绝对路径/危险链接；
3. 目标输出目录在原包目录之外；
4. 已确认文件条目是文本源码/文档，而不是固件二进制；
5. 记录每个提取文件的归档路径、文件大小和 SHA-256。

允许选择性提取：
- README / .md / .txt；
- .dts / .dtsi / .dtsinc；
- Makefile / Kconfig；
- defconfig / .config；
- .patch / .diff；
- manifest / XML / JSON / YAML / TOML；
- 其他能明确识别为纯文本的源代码与配置文件。

不允许提取或公开上传：
- .img / .bin / .mbn / .elf / .so / .ko / .dtb / .dtbo；
- modem、DSP、firmware、trustzone、安全芯片和 bootloader 二进制；
- 私钥、密钥、token、认证数据或用户隐私文件。

对 zip bomb 风险设定限制：
- 先统计归档声明的总解压大小、最大单文件大小、压缩比和文件数量；
- 如超出本机可接受资源阈值，或元数据明显异常，停止解压并只报告清单；
- 不允许用未知工具自动解压整个包。

## 第五阶段：与 DBY-W09 的适配价值分类

只根据实际内容做证据分类：

- **HIGH**：SM8250/KONA 公共平台源码、Qualcomm common DTS、UFS/PCIe/USB/clock/regulator/pinctrl 等通用驱动源码；
- **MEDIUM**：同 SoC 不同板型的驱动实现、参考 defconfig、启动配置、内核补丁（需版本适配）；
- **REFERENCE_ONLY**：Xiaomi 专属 panel、touch IC、GPIO、背光、电源 rail、键盘、音频 codec、PMIC 与板级 DTS；
- **NOT_DIRECTLY_REUSABLE**：旧内核的预编译 .ko、boot/vendor 镜像、DTB/DTBO、固件二进制或 Xiaomi 特定分区映像；
- **UNKNOWN**：证据不足或包损坏/缺卷。

报告必须指出 Xiaomi Pad 5 Pro 870 与 Huawei DBY-W09 865 虽属相近 KONA/SM8250 平台，但 SoC bin / OPP / CPU 频率 / board ID / panel / touch / regulator / GPIO 不能直接照搬。不得把 Xiaomi 板级 DTS 覆盖到 Huawei 设备树。

如果包内内核版本是 4.19 或其他旧版本，不得声称代码可直接并入 GKI 6.18；应列出可以作为参考的驱动子系统、改动范围和 ABI/Kconfig 风险。

## 第六阶段：输出和 GitHub 回传

本地输出独立目录，例如：
`D:\DBY-W09_XiaomiReference_Audit\`

只上传脱敏文本文件到仓库分支 `firmware-audit-v1`：
`xiaomi-reference-audit/`

可上传：
- TXT / CSV / JSON 报告；
- 经筛选的纯文本 DTS/DTSI、defconfig、README、Makefile、Kconfig、patch（仅当没有版权/许可/隐私冲突；若授权不明确，只上传文件名、路径、摘要，不上传源码正文）；
- 不上传压缩包，不上传镜像或任何二进制。

绝不上传：
- 两套原始 ZIP/7z/RAR 分卷；
- boot/vendor/super/system/odm/dtbo/vbmeta 镜像；
- .ko、.dtb、.dtbo、.bin、.elf、固件或 bootloader 二进制；
- PAT、密码、序列号、MAC、个人完整路径。

如无法验证压缩包或 GitHub 上传失败，保留本地报告并明确说明，不要编造完成状态。

## 完成后汇报

用中文明确列出：
1. 识别到的两套分卷集合名称、格式、卷数及是否完整；
2. 两套压缩包的 CRC / integrity test 结果；
3. 包内设备型号、codename、SoC、Android/内核版本（如可证实）；
4. 内含 kernel source / DTS / defconfig / boot / vendor / dtbo / super 等内容；
5. 哪些资料对 DBY-W09 有 HIGH / MEDIUM / REFERENCE_ONLY / NOT_DIRECTLY_REUSABLE 价值；
6. 是否执行了选择性文本提取及其范围；
7. 本地输出路径（仅目录名，不输出用户名等隐私路径）；
8. 上传到 GitHub 的报告文件和 commit SHA；
9. 明确说明没有执行包内脚本、没有运行安装器、没有刷机、没有修改设备，也没有上传任何固件二进制。

## 结束条件

在卷组关系与完整性未确认前，不提取任何内容。若两套包的文件集合无法分辨，或卷不完整/受密码保护/工具不可用，停止在只读盘点，并输出待确认文件名。