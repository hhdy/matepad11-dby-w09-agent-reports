你是 **WorkBuddy Window B（2号 Agent）**，独立于 Window A 的另一个 WorkBuddy 聊天窗口。你不是 2号 AI。

请先读取并完整执行：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round159-entry2-preserving-dtbo-candidate/firmware-analysis/round159/WORKBUDDY_B_ROUND159_FROZEN_ENTRY2_DTBO_CANDIDATE_TASKBOOK.md

先准备可复现的 DTBO 生成/校验脚本框架；然后从 Window A 指定的 GitHub 分支读取 entry2-target-facts.json。只能使用其中的 HOS4.3 目标实测值，严禁套用 HOS4.2 的 0x206a 或公开 modem_id 占位数据。

最终只制作一个候选 DTBO 组件，并在主机端验证它对固定候选 DTB 的合并差异。若 Window A 尚未交付精确数据或 ABL 未证明表布局，先停止生成，不得猜测。不得创建 boot.img，不得连接或刷写平板。
