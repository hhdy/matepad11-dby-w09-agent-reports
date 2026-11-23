# DBY-W09 本地固件只读解析工具

此工具用于分析本地 HarmonyOS 4.3 固件包，为 Huawei MatePad 11 DBY-W09 的 Android / GKI 内核移植收集证据。

## 安全边界

- 只读取本地已解压固件目录或 ZIP 包。
- 不连接平板，不调用 ADB 或 fastboot。
- 不刷机、不重启、不解锁、不 root，不读取或写入设备分区。
- 不执行固件包内附带的 BAT、CMD、PS1、SH、EXE 文件。
- 只把 boot.img、dtbo.img、ramdisk.img、recovery 和 vbmeta 等启动相关镜像复制到本地输出目录。
- super.img、preload.img、cache.img 等大分区只登记文件名和大小，不解包。
- 不要把 payloads/ 下的专有固件二进制提交到这个公开仓库。

## 运行方式

在 Windows PowerShell 5.1 或 PowerShell 7 中执行。先检查脚本内容来自本仓库，再运行：

powershell.exe -NoProfile -File .\tools\Analyze-DBY-W09-Firmware.ps1 -FirmwarePath "D:\你的固件目录" -OutputPath "D:\DBY-W09_FirmwareAnalysis"

也可以直接分析 ZIP：

powershell.exe -NoProfile -File .\tools\Analyze-DBY-W09-Firmware.ps1 -FirmwarePath "D:\你的鸿蒙4.3固件包.zip" -OutputPath "D:\DBY-W09_FirmwareAnalysis"

若固件目录本身包含 images 子目录，传入固件根目录即可。输出目录必须位于固件源目录之外。

可选参数：

- -NoExtractBootImages：只生成清单，不复制启动相关镜像。
- -HashLargeFiles：仅在输入为已解压目录时，对 512 MiB 及以上的大镜像计算 SHA-256；耗时和磁盘读取量会增加，默认关闭。

## 输出内容

| 文件 | 用途 |
|---|---|
| partition_inventory.csv | 固件镜像文件清单、大小和分类 |
| firmware_analysis.txt | Android boot header、DTBO header、压缩格式及工具可用性 |
| selected_images_sha256.csv | 本地复制出的启动相关镜像的 SHA-256 |
| summary.json | 供 Agent 自动读取的简要摘要 |
| payloads/ | 本地分析用镜像副本，禁止上传公开仓库 |

## 运行完成后回传

把输出目录中的以下四个报告文件上传到仓库的新目录 firmware-analysis/round1/：

- partition_inventory.csv
- firmware_analysis.txt
- selected_images_sha256.csv
- summary.json

不要上传 payloads/，也不要上传 super.img、boot.img 等固件二进制。

## 当前已知待分析点

1. 设备报告显示运行内核为 4.19.157-perf+，存在独立 ramdisk 分区，未发现 vendor_boot / init_boot。
2. 实机 /sys/firmware/fdt 为 root-only，ADB 无法读取 live DTB。本工具只能分析固件包中可读取的启动镜像，不能替代 live DTB。
3. 需要确认 boot.img 中的内核、ramdisk、DTB 布局，以及 dtbo.img 的 entry 数量和 header 格式。
4. super.img 后续应使用可信的 lpdump / lpunpack 工具单独解析 logical partition metadata；本脚本不尝试解包它。
5. 当前尚未完成 GKI 6.18.33 源码同步、锁定和基线编译。

## 版本

- Tool: Analyze-DBY-W09-Firmware.ps1
- Version: 1.0.0
