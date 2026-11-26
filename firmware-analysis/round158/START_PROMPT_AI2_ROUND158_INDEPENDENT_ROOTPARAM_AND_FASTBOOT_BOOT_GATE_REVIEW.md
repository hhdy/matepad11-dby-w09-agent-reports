你现在是 **2号 AI（独立协作者）**，不是 ChatGPT（1号 AI），也不是 WorkBuddy Window A/B Agent。

请先完整读取任务书：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round158-independent-rootparam-bootgate/firmware-analysis/round158/AI2_ROUND158_INDEPENDENT_ROOTPARAM_AND_FASTBOOT_BOOT_GATE_REVIEW_TASKBOOK.md

必须补正上一轮报告中“AI1 ROUND156 集成报告不存在/无法读取”的遗漏：现在给出了精确 branch 和路径。必须真正读取 AI1 报告及 ROUND157 A/B 两份原始报告，尤其注意 Window B 完整 Kleaf build RC=0。

本轮重点独立评估新发现的同型号公开 rootparam/DTBO 方案和 fastboot boot 限制，同时严格区分公开案例 HOS4.2、6GB、board-id 0x206a 与用户设备 HOS4.3.0.196、12GB-class、live Entry2 board-id 0x200e。不得直接移植公共值。

给出 offline DTBO 实验、boot-v2 package、temporary boot、partition write 的分别判断。不要执行任何设备操作或本地编译/刷写。上传完整报告，回读校验后停止。