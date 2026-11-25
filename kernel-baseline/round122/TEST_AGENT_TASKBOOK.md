# TEST AGENT TASKBOOK — ROUND122

**Task ID:** TEST-AGENT-ROUND122  
**Task owner:** 1号 AI（ChatGPT）  
**Executor:** 用户本地测试 Agent  
**Other AI:** 2号 AI 的 ROUND32 是独立工作；不要修改其分支。  
**Task type:** 只读验证 / 构建执行。Agent is not a kernel patch author.

## Candidate

- Branch: ai1/round122-ufs-vreg-load-order
- Patch: kernel-baseline/round122/0001-ufs-core-vreg-load-first.patch
- Pinned source: aosp-mirror/kernel_common @ 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

## Allowed actions

1. Fetch the patch and pinned ACK source.
2. Use a disposable detached worktree for all apply/build activity.
3. Run git apply --check, apply only to the disposable tree, then git diff --check.
4. Run scripts/checkpatch.pl --strict on the patch.
5. Read-only inspect the UFS regulator enable/disable call paths and verify that the exact disable helper path clears load before regulator_disable.
6. Compile drivers/ufs/core/ufshcd.o with the pinned Kleaf toolchain/config.
7. If the existing Stage A source tree and manifest-pinned Kleaf workspace are available without changing another branch, run the full tools/bazel build //common:dby_w09 --jobs=8 --local_ram_resources=6144.
8. Upload exactly one report to firmware-analysis/round122/ on firmware-audit-v1.

## Required checks

- Patch applies with zero offset/fuzz.
- Patch changes only drivers/ufs/core/ufshcd.c.
- ufshcd_disable_vreg() calls ufshcd_config_vreg(..., false) and checks its return before regulator_disable().
- vreg->enabled is cleared only after successful regulator_disable().
- ufshcd_enable_vreg() reapplies the configured active load before it skips regulator_enable() for an already-enabled reference.
- No public struct layout, Kconfig, DTS, regulator core, AVB, boot packaging, or firmware changes.
- Compile and full Image build results are reported separately.
- Explicitly retain the known managed-put limitation on true regulator_disable failure; do not claim it is solved by this patch.

## Prohibited actions

- Do not edit, rewrite, or "fix" the candidate patch.
- Do not author kernel code, bindings, DTS, fixtures or config.
- Do not modify main, ack18-dby-w09-dts-draft, PR #1, ai-parallel/stagea-port-until-boot, or any AI2 branch.
- No device connection, ADB, fastboot, root, reboot, boot, flash, partition access, DTBO/AVB/vbmeta operation, or firmware upload.
- Do not start ROUND123.

## Completion

Upload one report with exact patch SHA-256 and blob, source/tree identity, commands, exit codes, relevant logs, apply/checkpatch/object compile/full build results, and per-check PASS/FAIL/BLOCKED evidence.

After upload, stop immediately. Do not begin another round.
