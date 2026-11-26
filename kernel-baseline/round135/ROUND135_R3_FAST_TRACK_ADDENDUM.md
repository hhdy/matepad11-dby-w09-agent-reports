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
