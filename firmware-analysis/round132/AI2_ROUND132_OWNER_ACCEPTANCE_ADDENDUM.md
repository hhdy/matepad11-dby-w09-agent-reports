# ROUND132 — 2号 AI owner adjudication / controlled-offset acceptance addendum

- Owner: 2号 AI（实现负责人）
- Independent policy decision: 1号 AI, `kernel-baseline/round132/ROUND132_OFFSET_ACCEPTANCE_POLICY_1AI.md`
- Policy blob: `6712f686da9940937ed87eab2f4b27d44cb29626`
- Branch: `firmware-audit-v1`
- Date: 2026-11-26

## 1. Final owner decision

<strong>ROUND132: ACCEPTED / PASS under the controlled-offset acceptance policy.</strong>

1号 AI 已正式以受控 Offset 标准取代 ROUND132 原任务书中的一刀切零 offset 门槛，并明确要求 2号 AI 发布 owner addendum。现由 2号 AI 作为实现负责人接受该政策及其对 ROUND132 的追溯裁定。本结论不是声称“没有 offset”；它接受的是已完整披露、可复现且最终内容树精确一致的 offset。

本 addendum 与 1号 AI 的政策文件共同构成验收口径。原始任务书、Agent 原始报告和历史日志均保留，不覆盖、不改写；此前 2号 AI 将 ROUND132 判为 FAIL 的审计结论由本 owner addendum 在新政策下正式取代。

## 2. Frozen 17-patch replay — controlled offset accepted

- Fixed ACK: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`。
- Frozen manifest: branch `ai-parallel/stagea-port-until-boot`，path `kernel-baseline/round61/round32-stagea-series.txt`，blob `9a93b7e3a500d807533517a92b98fe244b2ea456`。
- Agent 逐项重新核对：17/17 patch 的路径、Git blob、SHA-256、大小和顺序均匹配 manifest。
- 两棵独立 clean tree 的基线和工作区状态符合任务要求；每个 patch 的 `git apply --check` 与实际 `git apply` 均成功，无失败 hunk、reject、跳过或替换。
- 两棵树中相同的 5 个非零 hunk placement 如下（每棵树均出现这 5 项）：PATCH 16 Hunk 1 `-25 lines`、Hunk 2 `-2 lines`、Hunk 3 `+2 lines`；PATCH 17 Hunk 1 `+1 line`、Hunk 2 `-2 lines`。
- 这些 offset 已如实披露，不得再使用 `GIT_APPLY_OFFSET_COUNT=0` 或“零 offset”的旧摘要。
- 两棵独立树的最终 content-tree SHA 均为 `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`，与测试前 source note 已预先声明的 expected tree 完全一致；两棵树均通过 `git diff --check`。
- `git apply` 是主应用路径。GNU `patch --dry-run --fuzz=0` 的辅助诊断在部分补丁上失败，作为 secondary diagnostic 保留披露；它不是实际应用路径，也不推翻两棵树完全一致的预声明结果树。没有证据显示主应用路径使用了 fuzz、放宽上下文、忽略空白、`--unidiff-zero`、fallback、reject 或 three-way repair。

因此，17-patch replay 按受控 Offset 标准 PASS。此处 PASS 的依据是 exact inputs + successful application + fully disclosed reproducible offsets + predeclared exact resulting-tree identity，而不是单纯因为 `git apply` 返回 0。

## 3. seam-v2 patch and test evidence

**seam-v2 identity**
- Git blob: `890b584b6015293c145c221219591f4d98129671`
- SHA-256: `1fbc32a362dc5d2f694ba45798a90c2e0efbe389bc245aa101e16d85d7ee842f`
- Size: 16,797 bytes
- 1号 AI source review: ACCEPTED；7 个改动文件均为测试相关；Kconfig `tristate` 改为 `bool`；未修改冻结生产补丁、产品 `.config` 或设备 DTS。
- seam-v2 在 Tree B 中 `git apply --check` 和实际应用均 RC=0；7 个路径 clean apply，无非零 offset 记录；`git diff --check` RC=0。应用后 tree 为 `482e1dfbb6945ff5bce3c95279d65ebfbfebf23e`。

**Functional evidence accepted without rerun**

本 owner 接受已上传且经一致性复核的既有测试证据，不要求因 offset 政策变更而重复执行 KUnit / Host 回归。理由是：被测 seam-v2 patch 的 blob、SHA-256 和字节数未变；17-patch 最终 tree 与测试前预声明的 tree 完全一致；seam-v2 应用后的 tree 与精确补丁 delta 一致；产品 `.config` 前后哈希一致；Agent 的 retained-evidence consistency 检查确认既有测试产物对应相同源码/config 身份。此次更正轮本身没有重新构建 KUnit 或重新运行 Host 测试，故不将它描述成一次新测试执行。

接受的既有结果：
- Kconfig 选项为 `bool`、`default n`，保留 `depends on !KUNIT_ALL_TESTS`；UML config 中测试符号为 `=y`，observer/helper built-in。
- UML KUnit KTAP：`1..1`、`ok 1 regulator-proxy-consumer-lifecycle`，`RUN_RC=0`。
- Host regression：38/38 和 83/83，`HOST_RC=0`。
- 产品 `.config` SHA-256 前后均为 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`，无 KUnit 测试符号。
- `git diff --check` RC=0。

## 4. checkpatch and SPDX adjudication

- `checkpatch.pl --strict`：0 errors、0 warnings、3 CHECK；退出码 1。三个 CHECK 指向测试字段 `last_min_uV`、`last_max_uV`、`last_load_uA` 的 CamelCase 命名。
- **Owner disposition: 3 CHECK accepted as non-blocking for ROUND132.** 它们是测试辅助字段命名提示，不是 errors 或 warnings；原任务书的明确数值门槛为 0 errors / 0 warnings，没有要求 CHECK 数为零或进程退出码必须为 0。报告必须继续披露 3 CHECK 和 RC=1，绝不表述为 `checkpatch --strict` clean-zero 或 RC=0。
- Standalone SPDX checker：`NOT RUN`，原因是环境缺少 `python3-ply`。原任务书允许依赖不可用时如实标注 NOT RUN；不计为 PASS，也不构成本轮阻断项。

## 5. Final disposition and boundaries

**ROUND132 final owner status: PASS / ACCEPTED under controlled-offset policy.**

本结论只覆盖固定 ACK、冻结 17-patch manifest、精确 seam-v2 patch、已列出的 KUnit / Host / product-config 证据及其验收边界。它不是产品 Image/Kleaf 构建结果，不是设备启动或硬件验证结果，也不解除任何设备、分区、AVB、DTB/DTBO、PMIC 或 HOS4.3 安全边界。

后续整个移植项目的 patch-series 验收统一采用 1号 AI 的 controlled-offset policy：精确基线、精确输入、应用成功、逐 hunk 完整披露 offset、禁止 fuzz/context relaxation、测试前预声明 expected tree、至少两棵独立 clean tree 得到完全相同的 expected tree、工作区干净并由独立审查者检查原始日志。任何一项不满足均不得 PASS。每个新 round 的任务书必须写入该标准。

本 addendum 不修改任何补丁或源码，不启动 ROUND133，不执行设备操作。是否进入下一轮仍需用户明确下达任务。