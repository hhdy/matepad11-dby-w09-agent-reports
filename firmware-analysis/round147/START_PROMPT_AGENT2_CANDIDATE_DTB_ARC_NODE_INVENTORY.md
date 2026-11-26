你是本项目的 **2号 Agent（本地执行 Agent）**，不是 2号 AI，也不是 WorkBuddy Agent。

请执行 ROUND147：只读取你自己 ROUND140 工作区中已经生成的候选 DTB，核对所有 qcom,rpmh-arc-regulator 节点及其子 regulator / parent-supply 关系。不得重新编译。

先读完整任务书：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round147-candidate-arc-node-inventory/firmware-analysis/round147/AGENT_TASKBOOK_AGENT2_CANDIDATE_DTB_ARC_NODE_INVENTORY.md

本任务只可使用你自己的既有路径：
- /home/kerneldev/work/matepad11/round140-agent2/tree
- /home/kerneldev/work/matepad11/round140-agent2/logs
- /home/kerneldev/work/matepad11/round140-agent2/a30build
- /home/kerneldev/work/matepad11/round140-agent2/out-dtb

关键要求：
1. 先验证 DTB 路径、108648 bytes 和 SHA256 cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e。
2. 只对既有 DTB 做只读反编译/文本检查，不重编译。
3. 完整统计 qcom,rpmh-arc-regulator group、mmcx/mx/cx 资源、子 regulator、*-parent-supply、proxy 关系。
4. 统计 PM8150/PM8150L per-PMIC regulator groups，区分 ARC provider 和 VRM rails。
5. 严格区分观察事实、解释和未知；不要推断设备实际供电或实际 runtime vote。

禁止连接平板、ADB/fastboot/recovery/UART、读写分区、构建、网络下载、改源文件/DTB、清理文件、访问别的 Agent 的 workspace。

完成后上传报告到分支 agent2/round147-candidate-arc-node-inventory：
firmware-analysis/round147/AGENT2_ROUND147_CANDIDATE_DTB_ARC_NODE_INVENTORY.md

回读核验上传文件后停止。