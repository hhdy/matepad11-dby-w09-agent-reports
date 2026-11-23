# AGENT_TASK_ROUND2.md — DBY-W09 DTBO 修复验证与 super.img 分析

> 本任务接续 `AGENT_TASK.md` 和固件分析 round 1。请使用本地已存在的固件目录，不要要求用户重新上传固件，也不要把固件二进制上传到公开仓库。

## 本轮目标

分两部分执行：

1. 验证已修复的 DTBO 头部解析，并重新生成准确的 round 2 启动镜像报告。
2. 对本地 `super.img` 做只读格式识别和 Logical Partition 元数据读取；在满足工具和磁盘空间条件时，再选择性提取 vendor / odm 分区用于驱动清点。

本轮不刷机、不连接设备、不写设备分区、不编译内核、不修改任何原始固件镜像。

## 一、获取最新脚本

仓库：`hhdy/matepad11-dby-w09-agent-reports`

分支：`firmware-audit-v1`

先单独克隆或在干净工作区更新，不覆盖用户已有未提交文件：

```powershell
git clone https://github.com/hhdy/matepad11-dby-w09-agent-reports.git
cd matepad11-dby-w09-agent-reports
git fetch origin firmware-audit-v1
git switch --track -c firmware-audit-v1 origin/firmware-audit-v1
```

如果已有本地 clone，先检查 `git status --short`，不要丢弃用户改动。

本轮必须读取：
- `tools/Analyze-DBY-W09-Firmware.ps1`
- `tools/Test-DTBO-Header.ps1`
- `tools/README-FIRMWARE-ANALYSIS.md`

## 二、验证 PowerShell 5.1 的 DTBO 修复

之前的问题：DTBO magic 原始字节为 `D7 B7 AB 1E`，PowerShell 5.1 将高位十六进制字面量与有符号 Int32 比较时导致匹配失败。

修复版本改为把 big-endian magic 格式化成固定八位十六进制字符串，与 `D7B7AB1E` 比较；同时输出 DTBO 头字段、基本结构校验和前 32 个 entry 摘要。

先执行合成文件回归测试：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\Test-DTBO-Header.ps1
```

必须看到：
`PASS: Windows PowerShell DTBO high-bit magic and one-entry header test.`

若失败，保留完整异常和 PowerShell 版本，不要继续重跑实际固件解析，也不要改动原始镜像。

## 三、重新解析真实固件并生成 round 2 报告

已确认的本地固件目录：

`D:\解锁bl\鸿蒙4.3\images`

不要修改其中任何文件。输出到一个全新目录，例如：

`D:\DBY-W09_FirmwareAnalysis_round2`

执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\Analyze-DBY-W09-Firmware.ps1 -FirmwarePath "D:\解锁bl\鸿蒙4.3\images" -OutputPath "D:\DBY-W09_FirmwareAnalysis_round2"
```

要求：
- 不传 `-HashLargeFiles`。
- 保持默认单文件 512 MiB 提取上限。
- 确认镜像清单仍为 43 项，与 round 1 的原始清单 43/43 对应。
- 确认 `firmware_analysis.txt` 有 `DTBO_MAGIC_HEX: D7B7AB1E`、`DTBO_ENTRY_COUNT`、`DTBO_HEADER_VALIDATION` 和 entry 摘要。
- 若 DTBO 结构校验为 INVALID，原样报告原因，不猜测 entry count 或跳过校验。
- 再次核验 boot.img 关键数据与 round 1 一致：header v2、kernel 22264379 B、ramdisk 519986 B、page 4096 B、DTB 1664243 B。
- 不把 `payloads/` 上传到 GitHub。

只把以下四个文本报告上传到当前工作分支的 `firmware-analysis/round2/`：
- `partition_inventory.csv`
- `firmware_analysis.txt`
- `selected_images_sha256.csv`
- `summary.json`

上传前检查并脱敏私人路径、用户名、设备序列号、MAC 地址。不得上传任何镜像文件或 PAT。

## 四、只读识别 super.img 的格式

原始文件位置：

`D:\解锁bl\鸿蒙4.3\images\super.img`

文件清单记录大小：7,114,729,004 bytes（约 6.62 GiB）。

先用只读方式读取前 64 bytes，不复制、不修改、不计算整个文件哈希。示例：

```powershell
$super = "D:\解锁bl\鸿蒙4.3\images\super.img"
$fs = [System.IO.File]::Open($super, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
try {
    $head = New-Object byte[] 64
    $read = $fs.Read($head, 0, $head.Length)
    $hex = (($head[0..($read - 1)] | ForEach-Object { $_.ToString("X2") }) -join " ")
    "SIZE_BYTES=$($fs.Length)"
    "HEADER_HEX=$hex"
    "MAGIC=$($head[0].ToString('X2')) $($head[1].ToString('X2')) $($head[2].ToString('X2')) $($head[3].ToString('X2'))"
}
finally { $fs.Dispose() }
```

判断：
- 字节开头为 `3A FF 26 ED`：Android sparse image。
- 否则记录完整 64-byte magic/header，不要直接假定是 raw super。
- 若是 Android sparse，按 sparse header 的 little-endian 字段读取 block size、total blocks、total chunks，计算展开后的理论大小：`block_size × total_blocks`。只读取 header，不要自行转换。
- 检查临时磁盘剩余空间；如需要展开，空间必须足够容纳 raw super 以及之后所选 logical partitions 的输出，并留至少 20% 余量。

## 五、lpdump 元数据读取（优先做，不提取分区）

只使用可信的 AOSP 构建产物或本机已验证的工具。先记录：

```powershell
Get-Command lpdump, lpunpack, simg2img -ErrorAction SilentlyContinue | Format-List Name,Source
```

不得从不明网盘、随机论坛或不明个人 GitHub release 下载可执行文件。若工具不存在，先停止工具执行，报告缺少哪些工具；不要为了本轮分析强行安装新 Linux 发行版。

AOSP 工具说明：
- `lpdump` 展示 super image 的 Logical Partition 元数据；官方文档支持 `lpdump [-s,--slot=N] PATH`，输入是非 Android-sparse 的 super image。
- `lpdump` 输出应收集 metadata version、metadata size、metadata slot count、partition table、每个 partition 的 name/group/attributes/extents、block device table 和 group table。
- 先运行 `lpdump --slot=0 <raw-super.img>`。根据输出中的 metadata slot count，若大于 1，再运行 `lpdump --slot=1 <raw-super.img>`。
- 若工具版本支持 `--json`，可额外保存每个 slot 的 JSON；不要假设所有版本支持相同参数，先看 `lpdump --help`。

若 `super.img` 被识别为 Android sparse：
- AOSP `lpdump` 说明其读取的是 non-sparse image；先不要直接对 sparse 文件运行并把失败当作元数据损坏。
- 只有在 `simg2img` 已存在且来源可信、已确认 raw 展开大小与磁盘空间足够时，才运行 `simg2img <source-sparse-super.img> <separate-output-super.raw.img>`。
- `simg2img` 的输入必须是原始 super.img，输出必须是另一个临时路径；严禁原地转换或覆盖源文件。
- 如果工具不在本机或磁盘空间不足，停在格式识别步骤并回报，不要临时寻找来历不明的工具。

把 lpdump 文本输出和 JSON（如有）保存在本地输出目录。只上传文本/JSON 元数据报告，不上传 raw super、sparse super 或任何分区镜像。

## 六、选择性 lpunpack（必须先满足条件）

只有在以下条件全部满足时才继续：
1. lpdump 成功读取元数据。
2. 已明确 exact partition names、slot、各分区大小和所属 group。
3. 本机有可信的 AOSP `lpunpack`。
4. 单独输出目录位于源固件目录之外。
5. 磁盘剩余空间大于本轮要提取分区的大小总和，并额外留至少 20%。

优先目标：
- `vendor` 或 metadata 中实际存在的 `vendor_a/vendor_b` 等精确名称；
- `odm` 或 metadata 中实际存在的精确名称。

不要猜分区名。以 lpdump 的 partition table 为准。

AOSP lpunpack 的参数形式为：

```text
lpunpack -S <slot> -p <exact-partition-name> <non-sparse-super-image> <output-directory>
```

对多个分区可重复 `-p` 参数。先只提取 vendor 与 odm（如存在），不要一次性提取 system/product/preload 等全部分区。

重要：AOSP lpunpack 当前实现会拒绝 Android sparse super image，并提示必须先 unsparse；只有对 raw super 或经可信 simg2img 转换得到的 raw 副本运行。

完成后：
- 记录提取文件名、大小、SHA-256、本地输出目录。
- 使用 `file` 等只读工具识别 ext4 / EROFS / sparse 格式。
- 如为 ext4，可使用默认只读模式的 `debugfs -R "ls -l /lib/modules" <vendor.img>`、`debugfs -R "ls -l /lib/firmware" <vendor.img>` 等查看模块和固件目录；严禁传入 `-w`，严禁挂载为可写。
- 检查 VINTF manifest 与模块清单时，只输出文件名、模块名、版本和依赖，不复制驱动二进制到公开仓库。
- 不上传 vendor.img、odm.img 或其他分区二进制。

## 七、报告上传与结束标准

目标目录：`firmware-analysis/round2/`

建议报告：
- `dtbo_regression_test.txt`
- `super_image_header.txt`
- `lpdump_slot0.txt` / `lpdump_slot1.txt`（实际存在的 slot）
- `lpdump_slot0.json` / `lpdump_slot1.json`（工具支持 JSON 时）
- `super_partition_summary.csv`（partition、group、attributes、size、extent 数量）
- `vendor_odm_inspection.txt`（仅在选择性提取成功时生成）
- `round2_summary.json`

所有报告必须先脱敏。不要上传任何固件镜像或私人标识信息。使用已配置的 GitHub 认证；不要索要、生成或保存 PAT。若写入仓库失败，保留本地报告并告知用户。

完成报告必须明确区分：
- 已完成的只读检查；
- 因工具缺失或磁盘空间不足而跳过的步骤；
- 实际提取了哪些分区；
- 没有做的事情（刷机、内核编译、设备分区写入等）。

## AOSP 参考资料

- Dynamic Partition Tools / lpdump README: https://android.googlesource.com/platform/system/extras/+/HEAD/partition_tools/README.md
- AOSP lpdump source: https://android.googlesource.com/platform/system/extras/+/refs/heads/main/partition_tools/lpdump.cc
- AOSP lpunpack source: https://android.googlesource.com/platform/system/extras/+/refs/heads/main/partition_tools/lpunpack.cc
- AOSP simg2img source: https://android.googlesource.com/platform/system/core/+/13a560659381b34ce3edbfa8dbe6c0aa6c076f20/libsparse/simg2img.c
