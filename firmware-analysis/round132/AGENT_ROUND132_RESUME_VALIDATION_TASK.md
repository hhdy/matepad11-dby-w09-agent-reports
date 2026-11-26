[已撤回 / DO NOT EXECUTE] 由1号AI误下发的测试任务书

本文件已于 2026-11-26 撤回，不再授权测试 Agent 执行。

原因：根据本项目三方职责规则，2号 AI 自己的代码实现及其对应测试派发，应由 2号 AI 编写并下发 Agent 任务书。1号 AI 不应越过 2号 AI 直接给 Agent 下发这项验证任务。

**请勿执行本文件内的旧测试指令，也不要使用此文件作为任何测试依据。**

正确接力顺序：
1. 2号 AI 阅读 `kernel-baseline/round132/AI2_ISSUE_AGENT_VALIDATION_TASK.md`。
2. 2号 AI 本人编写并上传新的 `firmware-analysis/round132/AI2_AGENT_VALIDATION_TASK.md` 到 `firmware-audit-v1`。
3. 用户将 2号 AI 的新任务书交给测试 Agent。
4. 测试 Agent 只按 2号 AI 的任务书验证，不改代码。
5. 1号 AI 审查 Agent 的报告。

精确补丁仍以 2号 AI 已交付的 seam-v2 为准：
- Branch: `ai2/round132-kunit-option-bool`
- Path: `firmware-analysis/round132/round132-kunit-seam-v2.patch`
- Git blob: `890b584b6015293c145c221219591f4d98129671`
- SHA-256: `1fbc32a362dc5d2f694ba45798a90c2e0efbe389bc245aa101e16d85d7ee842f`

本文件保留仅为避免历史链接失效和误执行；它已撤回，不能执行。