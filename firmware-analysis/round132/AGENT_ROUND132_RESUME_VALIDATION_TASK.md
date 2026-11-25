[发给测试Agent] ROUND132 seam-v2 精确补丁独立验证任务

# 任务身份与责任

- **下发方 / 技术负责人：1号 AI（ChatGPT）。**
- **执行者：用户本地 WorkBuddy 测试 Agent。**
- **代码实现者：2号 AI（已完成，本任务禁止 Agent 改代码）。**
- **独立审查者：1号 AI（ChatGPT）。**
- 本任务恢复此前因 AI2 交付缺失而 BLOCKED 的验证。Agent 只负责测试，不得实现或修复补丁。
- ROUND132 只是 1号 AI 仓库中的验证轮次编号，不是 2号 AI 的任务名称。
- 原任务书：`firmware-analysis/round132/AI2_ROUND132_TASKBOOK.md`（main）。
- 一号 AI 源码审查：[ROUND132 seam-v2 1AI source review](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round132/ROUND132_SEAM_V2_1AI_SOURCE_REVIEW.md)。

## 1. 精确输入身份（不得替换）

### 固定 ACK

`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`

### 冻结 17-patch manifest

- 路径：`kernel-baseline/round61/round32-stagea-series.txt`
- blob：`9a93b7e3a500d807533517a92b98fe244b2ea456`
- 必须逐项验证 17 个 patch identity 和 SHA-256，不得使用本机过期的 15 行 manifest。优先按 GitHub blob SHA 原样导出，避免 CRLF 改写。

### AI2 已交付的 seam-v2（本轮唯一可测试对象）

- 分支：`ai2/round132-kunit-option-bool`
- 路径：`firmware-analysis/round132/round132-kunit-seam-v2.patch`
- Git blob：`890b584b6015293c145c221219591f4d98129671`
- **SHA-256：`1fbc32a362dc5d2f694ba45798a90c2e0efbe389bc245aa101e16d85d7ee842f`**
- 大小：16,797 bytes
- 源码说明：`firmware-analysis/round132/AI2_ROUND132_SOURCE_NOTE.md`
- 源码说明 blob：`f1f45eed1a808a8296460d6c7c9ea1c542565c74`

必须先验证下载后的补丁原始字节 SHA-256 与上述值完全一致。任何字节差异、换行变化或 hash 不符，立即 BLOCKED 并停止，不得继续使用另一份 patch。

### ROUND35R / ROUND35S 来源说明

原任务书基于 ROUND35R。2号 AI 的源码说明以后来已经通过验证的 ROUND35S 为直接来源。1号 AI 已直接比较补丁内容：ROUND35S 相对 ROUND35R 的功能差异只有 Kconfig 类型从 `tristate` 改为 `bool` 以及对应帮助文本；seam-v2 相对 ROUND35S 只进一步精确化帮助文本。其余测试/observer/helper 代码和七个文件范围保持一致。因此本次只需按精确固定 ACK + 17 个生产补丁基线，应用指定的完整 seam-v2；不要另行重建旧的 ROUND35R 单独 seam。

## 2. 必须执行的验证步骤

1. 从固定 ACK 创建两棵全新、一次性、隔离工作树。禁止复用 ROUND35、ROUND35R、ROUND35S 或此前 BLOCKED 任务工作树。确认 HEAD 精确等于固定 ACK。
2. 使用指定 manifest，逐项验证 17 个生产补丁 blob/SHA-256，并在两棵树按 manifest 顺序运行 `git apply --check`、`git apply`、每步 `git diff --check`。记录每个补丁身份、退出码、offset/fuzz；要求 17/17 成功且零 fuzz。
3. 在第二棵干净树对 seam-v2 执行原始字节 SHA-256 核验，再运行 `git apply --check` 和 `git apply`；要求成功且零 fuzz。保留完整日志。
4. 检查 Kconfig 最终类型必须为 `bool`，并确认依赖 `KUNIT && REGULATOR_PROXY_CONSUMER && OF && OF_OVERLAY`、`depends on !KUNIT_ALL_TESTS`、`default n` 均存在。检查 KUnit `.config` 中选项为 `=y`，无 `_MODULE` 选择；确认内建 core observer 和 helper 符号确实进入该构建配置。
5. 在应用精确 seam-v2 的同一源码树上重新执行 UML KUnit。保存实际命令、输入配置、生成 `.config` SHA-256、完整 TAP 输出和退出码。要求真实执行并通过 1/1；不得用 ROUND35S 的历史 TAP 代替。
6. 重新运行原 AI2 base harness 的 host regression suites，要求 38/38 和 83/83。保存命令、完整日志和退出码。
7. 检查产品 `.config` SHA-256 仍严格为 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`，且不包含 KUnit 测试符号。
8. 执行 `git diff --check` 与 `checkpatch.pl --strict`。完整记录错误/警告/检查项。如果 SPDX 检查因 `python3-ply` 缺失失败，保留原始错误并明确标记未执行，不得写成通过。
9. 只清理本任务新创建的一次性 worktree、临时文件和输出；不得删除或修改以前任何工作树、构建目录、缓存、报告或源文件。
10. 上传本轮单独的最终报告和实际日志到 `firmware-audit-v1`，回读确认后停止。不得覆盖此前 BLOCKED 报告。

## 3. 交付文件名

在 `firmware-analysis/round132/` 下提交：
- `TEST_AGENT_ROUND132_FINAL_REPORT.txt`
- `round132-v2-apply-check.log`
- `round132-v2-kunit-final-TAP.log`
- `round132-v2-checkpatch.log`
- `round132-v2-config-and-host-regression.log`

报告必须逐项写明：固定 ACK、17-patch manifest blob、每个 patch SHA；seam-v2 路径/blob/原始字节 SHA-256；两棵工作树 HEAD、补丁应用结果、offset/fuzz；Kconfig bool/依赖/default、生成 `.config`、observer/helper 可见性；实际 KUnit 命令、完整 TAP、配置 hash、退出码；两组 host tests 完整结果；产品 `.config` 前后 hash；checkpatch/SPDX 实际结果；清理结果及未完成项。

报告必须区分 PASS / FAIL / BLOCKED / NOT_RUN。任何必需测试失败则按真实结果报告，不要修代码，不要重跑不同代码后冒充同一补丁通过。

## 4. 严格安全边界

- 不连接平板；不执行 USB、ADB、fastboot、recovery、root、serial 或任何设备接口命令。
- 不读写设备分区，不 boot、不 flash、不解锁。
- 不访问、重新提取、解包或上传 HOS4.3 固件。
- 不做完整产品 Image/Kleaf build，不打包 boot/DTB/DTBO/ramdisk/vbmeta/AVB。
- 不改源代码、DTS、binding、Kconfig、产品 defconfig、产品 `.config`、AI2/AI1 分支或 17-patch series。
- 不修改 2号 AI 已提交的 seam-v2 patch。
- ROUND133 已完成；本任务不得重新启动 ROUND133。
- 如果任何验证需要越过上述边界，立即停止并报告。

## 5. 停止条件

所有允许验证完成后，上传单一最终报告及规定日志，回读校验后立即停止，等待 1号 AI 审查。不得自动开始下一轮或宣称 Phase E/F/G 已解锁。