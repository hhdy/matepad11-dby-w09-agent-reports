2号 Agent：现在开始执行 **ROUND140 — 独立构建复现与首启前测试**。

**角色确认：你是 2号 Agent（第二个本地执行 Agent）。你不是 2号 AI，也不是正在执行 ROUND139 的 WorkBuddy Agent。** 本任务由 AI1 派发，你是唯一执行者。

完整任务书：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/firmware-analysis/round140/AGENT_TASKBOOK_AGENT2_INDEPENDENT_BUILD_AND_PREBOOT_TESTS.md

本轮核心任务：
1. 建立完全独立的 worktree 和构建输出目录；
2. 对固定 ACK commit 和 23 个已验收补丁做独立重放，必须得到 tree SHA：
   afe9517f8062b96bfeb5b4dd5714942861e6a44b；
3. 独立执行 Kleaf 构建，验证 Image / DTB / .config 身份与 ROUND135 基线；
4. 用只读工具检查本次 DTB；
5. 对 ROUND138 已验收发现、以及已经交付的 ROUND139 报告进行独立逻辑核验；
6. 输出首启前测试矩阵，但不得把构建成功等同于实机可启动。

ROUND139 如果尚未正式上传，不得读取 WorkBuddy Agent 的临时目录或干扰它；先完成可独立完成的部分，并把 ROUND139 交叉核验项标为 PENDING / BLOCKED。

禁止连接平板，禁止 ADB / fastboot / recovery / USB / 串口 / reboot / bootloader 操作，禁止读取 ABL 或重试 /sys/firmware/fdt，禁止刷写、打包、签名、AVB 修改，禁止修改源码、23 个补丁、DTS、DTBO、config 或任何已有分支。不得安装工具或下载固件。

最终报告：
firmware-analysis/round140/round140-agent2-independent-build-and-preboot-test-report.md

只上传脱敏 Markdown 到 agent2/round140-independent-preboot-tests 分支，回读核验后停止。不得自行进行首次启动。
