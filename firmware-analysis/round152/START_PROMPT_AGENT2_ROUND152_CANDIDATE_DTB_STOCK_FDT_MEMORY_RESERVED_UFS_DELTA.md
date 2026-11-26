你是 **2号 Agent（本地独立 Agent 2）**，不是 2号 AI，也不是 WorkBuddy Agent（本地 Agent 1）。

请执行 ROUND152：对比你自己 ROUND140 工作区里已经存在的候选 DTB 与 ROUND151 已公开的原厂实时 FDT 解码数据。

完整任务书：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round152-candidate-stock-fdt-memory-reserved-ufs-delta-audit/firmware-analysis/round152/AGENT2_ROUND152_CANDIDATE_DTB_STOCK_FDT_MEMORY_RESERVED_UFS_DELTA_TASKBOOK.md

严格限制：
- 只读 /home/kerneldev/work/matepad11/round140-agent2/tree、logs、a30build、out-dtb 四个已列出的自身目录。
- 先核验 candidate DTB 108648 bytes / SHA256 cab82fe3901dbb40533197eb48b2d99b08b46e5d5497ff1a6f688e9938db77e；不匹配就停止。
- 完整对照 RAM、reserved-memory、UFS host/PHY、vdd-hba/GDSC、OPP/GenPD、ARC 和 proxy 属性。
- 不连接平板、不用 ADB/root、不编译、不修改源码/DTS/DTB、不访问其他 Agent 私有目录、不刷机或启动测试。
- 上传报告并读回校验后停止。

报告路径：
firmware-analysis/round152/AGENT2_ROUND152_CANDIDATE_DTB_STOCK_FDT_MEMORY_RESERVED_UFS_DELTA_REPORT.md