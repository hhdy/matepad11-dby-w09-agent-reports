你现在执行 K1_UBOOT_RECOVERY_ABL_HANDOFF_AUDIT01。

先阅读 GitHub 任务书：
firmware-analysis/boot-v2/uboot-chainloader-adapt01/K1_UBOOT_RECOVERY_ABL_HANDOFF_AUDIT01_TASKBOOK.md

身份门禁是第一步：实际使用的 ABL PE SHA-256 必须严格等于：
a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404

不一致、原始 PE 缺失或只有其他版本时立即 BLOCKED 并停止。

这是一次有界只读静态分析，只闭合：
1. HOS4.3 recovery 分支是否走同一 BootLinux 尾段、最终 x0 是否为 FDT；
2. recovery 时 separate ramdisk 的真实来源、payload/wrapper 处理及 linux,initrd-start/end；
3. ABL UpdateDeviceTree/EFI_RAMPARTITION 对 /memory/reg、reserved-memory、memreserve 的真实修改。

优先复用现有报告、脚本、脱敏反汇编，不要重扫 ABL。严格区分 HOS4.3 recovery 与普通 boot / fastboot 路径。无法从精确 PE 指令闭环的值一律 UNKNOWN，不要推断。

禁止设备连接、ADB/Fastboot/OEM/EDL、reboot、临时启动、刷写、分区读写、工具安装、固件下载、镜像构建或上传原始固件。只把脱敏报告上传到分支 ai1/boot-v2-first-package-prep 的指定路径。

写完报告并从 GitHub 回读核对后停止，不自动开始下一轮。