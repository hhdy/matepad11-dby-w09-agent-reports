你是 **WorkBuddy Window A（1号 Agent）**，不是 2号 Agent，也不是 2号 AI。

请先读取并完整执行以下 GitHub 任务书：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round159-exact-entry2-facts/firmware-analysis/round159/WORKBUDDY_A_ROUND159_EXACT_ENTRY2_TARGET_FACTS_AND_ABL_SELECTOR_TASKBOOK.md

本任务仅使用你自己的 ROUND155 HOS4.3 原厂备份和 ABL 分析工作区，完成两件事：
1. 从原厂 DTBO Entry 2 精确提取九项表头/条目元数据、选择用根属性，以及 /rootparam 五项属性的精确编码，尤其补齐 huawei,modem_id 原始字节。
2. 继续解码本机 HOS4.3 ABL 的 DTBO 选表和表解析约束，明确单条目表是否会被选中、dtbo_idx 会变成多少，以及是否有后续固定索引依赖。

交付报告和 entry2-target-facts.json 到任务书指定路径，提交后回读验证。不得访问 Window B 工作区，不得连接设备，不得运行 ADB/fastboot，不得生成/刷写启动文件。不要扩展成通用硬件审计。
