# 发给本地 WorkBuddy 测试 Agent

你是 **用户本地 WorkBuddy 测试 Agent**，不是 2号 AI。请执行 **TEST-AGENT-AI1-ROUND135-R3**。

## 角色
- 下发方、技术负责人、候选源码负责人、最终审核方：1号 AI（ChatGPT）
- 执行方：你（本地测试 Agent）
- 2号 AI：已经独立审核 R2；本轮不负责本地执行

## 必须先读
分支：ai1/round130-stagea-ufs-lifecycle-integration

1. kernel-baseline/round135/TEST_AGENT_ROUND135_R3_TASKBOOK.md（本任务完整授权与验收条件）
2. kernel-baseline/round135/ROUND135_23_PATCH_SERIES_MANIFEST.md（最新 blob 9188de2022f88c374bfcaa367c505428812608d9）
3. kernel-baseline/round135/AI1_ROUND135_UBUNTU_REFERENCE_RECONCILIATION.md
4. kernel-baseline/round132/ROUND132_OFFSET_ACCEPTANCE_POLICY_1AI.md（blob 6712f686da9940937ed87eab2f4b27d44cb29626）

## 不可变 SHA gate
固定 ACK commit：8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
ACK root tree：790a68ae6d4f4ac51ab2d88977b6fd5c031473b7
17-patch intermediate tree：77e2b2b1515b3813f7538aedffe4c5a4e90edb57
**完整 23-patch 预期 content tree：afe9517f8062b96bfeb5b4dd5714942861e6a44b**

新建验证树必须从固定 ACK 和全部 23 个精确输入重建。tree SHA 不匹配立即停止，不得构建或测试，不得修改任何输入。

## 执行范围
按 R3 任务书依次进行：
- 精确核验全部 23 patch 的 blob / SHA-256 / size / 顺序；
- primary git apply --check --verbose → git apply --verbose → git diff --check；
- 完整披露并复现已接受 Offset：patch16(-25,-2,+2)、patch17(+1,-2)、patch20 H3(-19)；
- 完成 23-patch expected Tree SHA gate；
- source assertions、schema、真实 huawei-dby-w09.dtb build/decompile、dtbs_check；
- final .config、受影响 C objects、full Kleaf //common:dby_w09 Image；
- 固定 Host 38/38 和 83/83 回归；
- checkpatch / diff / SPDX；
- 上传六份原始证据和最终报告到 firmware-audit-v1:firmware-analysis/round135/r3-validation/，再逐个 raw readback 验证。

## 特别注意
Ubuntu Linux 参考包的 UFS Host DT 只有 GCC GDSC，但其 UFS OPP 仍引用 RPMhPD；Ubuntu 7.3.1-loa driver 源码没有提供。不得仅凭该 DTB 推翻 ACK 候选。R3 必须按 reconciliation 文件验证：Host MMCX index0 + GCC UFS_PHY_GDSC index1；OPP 的 required_dev 显式映射 MMCX index0；UFS PHY 仍是 GCC GDSC；实际生成 DTB 必须保留 inherited UFS OPP table 和两个 required-opps。

严格不接触平板、USB、ADB、fastboot、recovery、serial、分区或固件；不 boot / flash / packaging；不改任何源文件或补丁；不改 AI2/main/protected branches；不覆盖旧证据。遇到工具、依赖或源码问题按任务书报告，不能现场修补。

## 完成后
上传并确认六份报告/日志 byte-identical readback 后立刻停止，不要开始 ROUND136 或其他任务。把上传 commit/blob 和 PASS/FAIL/BLOCKED 结论交回 1号 AI。


# ROUND135 R3 — fast-track execution addendum (does not relax acceptance)

Owner / dispatcher: 1号 AI（ChatGPT）
Executor: user-local WorkBuddy test Agent
Scope: time-efficient execution of the already-authorized R3 taskbook. This addendum changes scheduling only; it does NOT remove or weaken any gate.

## Priority

The immediate target for today is to establish a reproducible ROUND135 buildable candidate, not to claim a hardware-booted port before the independent blockers are closed.

Do not repeat R2's two-tree exercise. R2 has already been independently accepted and the full-series expected tree SHA is pinned. R3 still requires one fresh isolated tree to reapply all exact inputs and prove the pinned SHA before any test.

## Time-saving execution rules

1. Use the already available local pinned ACK source and already-installed pinned toolchain/workspace. Do not spend time on new repo sync, fresh toolchain downloads, package installation, WSL deployment, or internet research. If required existing inputs are unavailable, report the exact missing item and stop rather than attempting broad environment repair.
2. Create one new clean disposable working tree and one new output directory. Never mutate historical a30 / R1 / R2 workspaces or shared source branches.
3. Complete all 23 patch identity checks, primary check/apply, offset capture, patch17 intermediate tree check, and full expected tree SHA gate first. This is the hard gate. If it fails, do not launch any downstream task.
4. Once the exact expected tree SHA is proven, perform independent read-only validation lanes in parallel where tool/output isolation is safe:
   - Lane A: source assertions, dt_binding_check, real huawei-dby-w09.dtb build/decompile, and dtbs_check. Use its own Kbuild O= output directory.
   - Lane B: fixed host tests (38/38 + 83/83), checkpatch, git diff check and SPDX status. Host test scratch files / binaries / logs must stay outside the source tree; do not alter the runner, mock, tests, source or patches.
   - Lane C: final .config/Kconfig symbol validation and affected-object compilation using a separate O= output directory. Do not share a mutable Kbuild output directory with Lane A.
5. Keep one coordinator responsible for confirming Lane A/B/C logs and gate results. Start full Kleaf //common:dby_w09 Image build only after every required pre-build gate in the main R3 taskbook has passed. Use a distinct Bazel output root and keep its artifacts outside the source tree.
6. Do not run competing Kbuild processes against the same O= directory, do not let any lane write into the source tree, and do not run multiple full Kleaf builds concurrently. If the local agent cannot safely parallelize lanes, run them sequentially; correctness takes priority over concurrency.
7. Write each log as the relevant step completes. Do not wait until the end to reconstruct command output. Any failure is recorded immediately with full stdout/stderr, exact command, exit code and the relevant SHA.
8. Do not spend time on formatting, cosmetic cleanup, new design ideas, or optional unrelated research. No source fixes are authorized. Report checkpatch warnings and existing blockers; do not edit patches.
9. After the full Image build and host regression complete, upload all six R3 artifacts and verify byte-identical readback. Stop after readback.

## Scope/claim limit

Even a complete R3 PASS means offline source/schema/DTB/build/host validation only. It does not prove MMCX physical voltage behavior, MMCX-to-MX ARC equivalence, PMIC physical parent rails, ABL final FDT/EFI memory handoff, boot-chain/AVB/DTBO selection, device UFS probe, storage enumeration or hardware stability. Do not label the device port complete or attempt a tablet boot/flash under this taskbook.
