WorkBuddy Agent：现在执行 ROUND139 — HOS4.3 PMIC/UFS 与 boot/AVB 静态证据收口审计。

任务书（必须完整阅读并严格遵守）：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/firmware-analysis/round139/AGENT_TASKBOOK_HOS43_PMIC_UFS_AND_BOOT_AVB_AUDIT.md

这是 WorkBuddy Agent 的本地离线只读任务，不是 AI2 任务。只用任务书列出的既有 HOS4.3 解包文件、ROUND2/13/19/21/24/51/64/136/137/138 既有记录和 parser 输出；不得重新解包，不得搜索任意磁盘路径。

本轮分两条线：
1. PM8150/PM8150L 六条 UFS 消费轨的真实输入 parent 证据，以及 UFS OPP / MMCX / MX / CMD DB / runtime vote 证据；
2. boot-v2、embedded stock ramdisk、独立 ramdisk、DTBO、vbmeta 链、vbmeta_cust 异常与可恢复路径的静态核验。

必须把物理电源 parent、RPMh/ARC corner 关系、proxy supply 分开；没有权威证据就标 UNKNOWN / BLOCKED，严禁猜测。HOS4.3 ABL 实际行为、真实恢复路径和首次启动安全性不得从 HOS4.2 公共项目推断。

严禁连接设备、ADB、fastboot、recovery、USB/串口、读取 ABL、重试权限拒绝的 FDT、提权、重启、打包、构建、AVB 修改、刷写或任何源代码修改。

按任务书生成报告，上传至 firmware-audit-v1 的 firmware-analysis/round139/，回读核验后停止。