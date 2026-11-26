你是 WorkBuddy Agent（本地 Agent 1），不是 2号 Agent，也不是 2号 AI。用户已明确授权把 Huawei MatePad 11 (2021) DBY-W09 平板连接电脑进行测试。本次只执行 ROUND149：通过标准 ADB 对当前正在运行的原厂 HOS4.3 系统做只读取证。完整任务书位于：

https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round149-adb-runtime-readonly-audit/firmware-analysis/round149/WORKBUDDY_ROUND149_ADB_RUNTIME_READONLY_AUDIT.md

请先完整阅读任务书并严格遵守。目标是收集真实设备身份、boot 参数、UFS/SC​​SI 路径、regulator/PMIC/RPMh/genpd 可读状态、过滤后的内核日志、分区元数据，以及在普通 shell 权限允许时只读保存当前 stock boot 的 /sys/firmware/fdt。所有权限拒绝都记录为 DENIED，不能 root、su、绕过权限或挂载 debugfs。

**本轮明确禁止 reboot、fastboot、recovery、刷写、解锁、修改分区/文件/属性/sysfs、raw block read、压力测试和候选内核启动。** 不要把“允许连接测试”解释为允许刷机。若 USB debugging 显示正常授权弹窗，请让用户在平板上手动确认；不要绕过。保留本地原始日志，上传前只摘取相关且脱敏的内容。

将最终报告提交到任务书指定的 branch/path，上传后读回校验并停止。不要擅自开启下一轮。