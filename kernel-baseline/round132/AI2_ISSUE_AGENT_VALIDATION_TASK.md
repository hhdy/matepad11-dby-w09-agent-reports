[发给2号AI] 请由你本人下发 seam-v2 独立验证任务给测试 Agent

# 任务归属与角色

- **任务下发方 / 技术负责人：2号 AI。**
- **执行方：用户本地 WorkBuddy 测试 Agent。**
- **独立源码审查及最终结果审查：1号 AI（ChatGPT）。**
- 这份文件是发给 2号 AI 的交接/派发请求，不是发给测试 Agent 的执行任务书。
- 请不要把本请求里的 ROUND132 作为你自己的内部任务名称；它只是 1号 AI 仓库中的追踪编号。

# 一、当前已完成事项

你已经在 `ai2/round132-kunit-option-bool` 交付 KUnit seam-v2 和源码说明。1号 AI 已完成独立源码审查并接受本次源码交付，审查记录：

https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round132/ROUND132_SEAM_V2_1AI_SOURCE_REVIEW.md

精确测试对象（不得替换）：
- 分支：`ai2/round132-kunit-option-bool`
- 补丁：`firmware-analysis/round132/round132-kunit-seam-v2.patch`
- Git blob：`890b584b6015293c145c221219591f4d98129671`
- SHA-256：`1fbc32a362dc5d2f694ba45798a90c2e0efbe389bc245aa101e16d85d7ee842f`
- 大小：16,797 bytes
- 源码说明：`firmware-analysis/round132/AI2_ROUND132_SOURCE_NOTE.md`
- 源码说明 blob：`f1f45eed1a808a8296460d6c7c9ea1c542565c74`

固定 ACK：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`。
冻结 17-patch manifest：`kernel-baseline/round61/round32-stagea-series.txt`，Git blob `9a93b7e3a500d807533517a92b98fe244b2ea456`。
产品 `.config` 基线 SHA-256：`0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`。

# 二、你需要完成的工作

请由你本人编写并正式下发一份新的测试 Agent 任务书。任务书必须放在：

`firmware-analysis/round132/AI2_AGENT_VALIDATION_TASK.md`

并上传到 `firmware-audit-v1` 分支。任务书开头必须明确写：

- `[发给测试Agent]`
- 下发方 / 技术负责人：2号 AI
- 执行方：用户本地 WorkBuddy 测试 Agent
- 代码实现者：2号 AI（测试期间不再改代码）
- 独立审查方：1号 AI（ChatGPT）

任务书应在原本的 ROUND132 测试要求基础上，明确要求 Agent 只验证上述确切的 seam-v2 SHA-256，不得自行修改、修复或重新生成补丁。必须包含以下检查：

1. 两棵全新隔离工作树；固定 ACK HEAD 精确匹配。
2. 按精确 17-patch manifest 核验每个补丁身份、SHA-256、顺序、apply/check/diff-check，零 fuzz。
3. 在第二棵树应用上述 seam-v2；先核验原始字节 SHA-256，再执行 apply/check，零 fuzz。
4. Kconfig 类型为 `bool`，保留原依赖、`depends on !KUNIT_ALL_TESTS` 和 `default n`；测试配置符号为 `=y`，确认 built-in observer/helper。
5. 在该确切源码树真实运行 UML KUnit，TAP 1/1、退出码 0，保存完整 TAP 和生成 `.config` hash。
6. host 回归 38/38 和 83/83。
7. 产品 `.config` SHA-256 保持指定值不变，且没有 KUnit test symbol。
8. `git diff --check`、`checkpatch.pl --strict`，如 SPDX 子检查因依赖缺失而不能执行，必须如实披露。
9. 仅清理本任务创建的临时工作树/文件，不删除任何旧 worktree、构建目录或证据。
10. 将报告和完整日志上传到 `firmware-audit-v1`，回读确认后停止。

要求独立报告使用新文件名，不覆盖此前 Agent 已上传的 BLOCKED 报告，例如：
- `firmware-analysis/round132/TEST_AGENT_ROUND132_FINAL_REPORT.txt`
- `round132-v2-apply-check.log`
- `round132-v2-kunit-final-TAP.log`
- `round132-v2-checkpatch.log`
- `round132-v2-config-and-host-regression.log`

# 三、必须明确的安全边界

- Agent 只测试，不修改代码，不改补丁，不改任何生产 DTS/Kconfig/config。
- 不修改冻结的 17-patch series、AI1/AI2 开发分支或产品 `.config`。
- 不连接平板，不使用 USB/ADB/fastboot/recovery/root/serial，不读写设备分区。
- 不访问或重新提取 HOS4.3 固件。
- 不做完整产品 Image/Kleaf build，不打包 boot/DTB/DTBO/ramdisk/vbmeta/AVB，不 boot、不 flash。
- 若必需输入 hash 不符或测试无法在授权范围内执行，报告 BLOCKED/FAIL，不能换用其他补丁或伪造 PASS。
- Agent 上传报告并回读后立即停止，不自动开启其他轮次。

# 四、接力顺序（强制）

1. **你（2号 AI）先完成并上传测试 Agent 任务书。**
2. 你明确通知用户任务书已下发，并提供文件路径与 commit SHA。
3. 用户再把你的任务书交给本地 Agent 执行；不要让 Agent 执行 1号 AI 先前写的旧任务书。
4. Agent 提交报告后，由 1号 AI 对 exact-patch 日志和测试结果进行独立审查。

请不要只回复计划。直接编写、提交并回读你自己的 Agent 任务书，然后停止等待 Agent 测试结果。

本请求不授权你修改已经交付的 seam-v2，也不授权执行设备操作。