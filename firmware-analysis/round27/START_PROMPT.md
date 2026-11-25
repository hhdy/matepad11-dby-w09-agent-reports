[已废弃 / DO NOT SEND OR EXECUTE]
本启动提示把测试 Agent 错误写成 2号 AI，已被纠正并废弃。正确角色：1号 AI = ChatGPT；2号 AI = 独立开发 AI；Agent = 仅负责测试/验证的本地执行者。当前 ROUND27 唯一有效指令由 2号 AI 下发给测试 Agent，见：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round27/AI2_ROUND27_TASKBOOK.md
以下旧内容仅作历史记录，不得据此派发或执行。

[发给2号AI｜2号AI任务书 / LOCAL_AGENT_TASK｜ROUND27]

执行者：2号 AI（本地 WorkBuddy Agent）
委托与验收审核：1号 AI（ChatGPT）
状态：AUTHORIZED / READY TO EXECUTE
审查放行依据：firmware-analysis/round25-26/PRIMARY_AI_REVIEW_2026-11-25.md

请按本任务书执行 ROUND27。ROUND25、ROUND26 已由 1号 AI（ChatGPT）审查并放行。开始前仍需核对两份报告和 `firmware-analysis/round25-26/PRIMARY_AI_REVIEW_2026-11-25.md` 均可读取；缺任一文件则停止并报告。

本轮只做真正的 Kleaf/Bazel 设备树目标验证，不重编内核：
1. 在 ROUND18 现有本地 workspace 中读取 MODULE.bazel、MODULE.bazel.lock、build/kernel/kleaf/bzlmod/bazel.MODULE.bazel 和 repo manifest，锁定实际 rules_devicetree 版本/提交及 dtc toolchain。
2. 从 main 的 dby-w09-ack18-board.dts.rev2.candidate 与 dby-w09-ack18-rootparam.dtso.draft 精确复制临时源到 qcom DTS 目录。临时创建 BUILD.bazel，加载本地确切版本的 dtb、dtbo、dtb_composite，依赖 //common:dtc_includes_aarch64。
3. 只运行 query/cquery 和三个设备树 target 的 bazel build：base DTB、rootparam DTBO、composite DTB。禁止构建 kernel/Image 或 dtbo_image。
4. 检查 composite DTB 的五项 rootparam、root board-id 与 overlay board-id 区别、UFS Host MMCX index0/GCC GDSC index1、PHY GCC GDSC、UFS rail properties、缺少 vdd-hba-supply。
5. 对 composite 运行最窄可用的 dtbs_check / dt-validate，所有诊断都要记录。不要把 dtc exit 0 当成 schema PASS。
6. 删除临时 BUILD 和 staged files，确认 ROUND18 已有 patch/.config/Image 无变化；只上传脱敏报告，不上传二进制。

不下载、不安装、不 repo sync，不修改任何 tracked source/DTS/config，不做内核编译、不打包、不 AVB、不操作设备。完成报告后停止。