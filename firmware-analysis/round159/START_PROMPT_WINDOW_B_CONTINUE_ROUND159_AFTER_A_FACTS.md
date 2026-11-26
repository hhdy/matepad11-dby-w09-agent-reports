你是 WorkBuddy Window B（2号 Agent）。继续你已开始的 **ROUND159**，不要开新一轮。

上一份报告之所以 BLOCKED，是因为它执行时 Window A 尚未上传数据。现在数据已经在 GitHub 上，直接按这份续执行说明继续：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round159-entry2-preserving-dtbo-candidate/firmware-analysis/round159/ROUND159_WINDOW_B_CONTINUATION_AFTER_WINDOW_A_FACTS.md

请读取该说明中的 normalized facts 文件，以你自己的候选 DTB 完成唯一 DTBO 构建、表解析/回序列化、host merge 五属性差异验证和负向测试。特别注意 qcom,boardid 是 4 个 u32 单元 [8,2,0,6]，huawei,modem_id 是 2 个 u32 单元 [0xffffffff,0]。把此前 BLOCKED 报告更新为最终结果并回读校验。

不连接平板，不运行 ADB/fastboot，不制作 boot.img，不刷写。只完成 ROUND159 的剩余交付。
