# TEST AGENT TASKBOOK — ROUND116

**Task ID:** TEST-AGENT-ROUND116  
**Task owner:** 1号 AI（ChatGPT）  
**Executor:** 用户本地测试 Agent  
**Other AI:** 2号 AI 不执行本任务；其 `ai-parallel/stagea-port-until-boot` 分支不得被修改。  
**Task type:** 测试 / 独立验证。Agent is not a kernel patch author.

## Objective

Validate the 1号 AI candidate patch for joining the UFS-owned async scan before UFS host removal touches HBA resources.

**Candidate branch:** `ai1/round116-ufs-async-domain`  
**Patch:** `kernel-baseline/round116/0001-ufs-core-per-hba-async-domain.patch`  
**Pinned upstream source:** `aosp-mirror/kernel_common` commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.

## Allowed actions

1. Fetch the candidate patch and pinned source.
2. Use a disposable worktree / temporary checkout only.
3. Run `git apply --check`; apply the patch only to the disposable checkout.
4. Run `scripts/checkpatch.pl --strict`.
5. Use the existing pinned Kleaf manifest/environment for object compilation and, only if the Stage A source/patch-series inputs are available without changing protected branches, attempt the complete `//common:dby_w09` Image build.
6. Perform read-only source-flow inspection of the async callback, schedule, remove, synchronous fallback and error paths.
7. Upload a single test report under `firmware-analysis/round116/` on `firmware-audit-v1`.

## Required checks

- The patch applies exactly, with zero fuzz and zero offset.
- `ufshcd-priv.h` owns the new fields; public `struct ufs_hba` is unchanged.
- There is one `ufshcd_async_scan` schedule site and it stores the cookie returned from `async_schedule_domain()`.
- `async_domain.pending` is initialized before any possible scheduling, and `registered` is set to 1.
- `ufshcd_remove()` joins using the stored cookie + 1 before the first HBA field read or teardown action.
- No path acquires `host_sem` before the join.
- If callback execution falls back synchronously, the callback has already completed when the schedule call returns; the stored checkpoint must be harmless.
- Probe failures before the schedule site leave `async_scan_scheduled == false`.
- Report compile and full build outcomes separately; a successful object compile is not a full Image build.

## Prohibited actions

- Do not edit or rewrite the candidate patch.
- Do not add kernel code, DTS, bindings, config or packaging changes.
- Do not modify `main`, `ack18-dby-w09-dts-draft`, PR #1, or `ai-parallel/stagea-port-until-boot`.
- Do not treat this task as 2号 AI implementation work.
- No device connection, ADB, root, boot, flash, partition write, boot/DTBO/vbmeta/AVB operation, or firmware upload.
- Do not begin ROUND117 or any follow-up task.

## Completion and stop condition

Upload exactly one report with:
- tested commit and patch SHA-256;
- source revision and worktree identity;
- exact commands, exit codes and relevant logs;
- apply/checkpatch/object compile/full Image build results;
- each required check marked PASS / FAIL / BLOCKED with evidence.

After uploading the report, stop immediately. Do not create code commits or continue to another round.
