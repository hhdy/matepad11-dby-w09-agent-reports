# ROUND116 — 1号 AI：UFS async-scan per-HBA lifecycle join implementation candidate

**Owner:** 1号 AI（ChatGPT）  
**Patch author:** 1号 AI（ChatGPT）  
**Test executor:** 用户本地测试 Agent（只执行测试，不编写或修改内核实现）  
**Implementation boundary:** 独立 AI1 分支；不修改 2号 AI 的 `ai-parallel/stagea-port-until-boot`，不修改 `main`、`ack18-dby-w09-dts-draft`、PR #1 或固件。  
**Pinned source:** `aosp-mirror/kernel_common` @ `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` (`android17-6.18.33_r00`)  
**Branch:** `ai1/round116-ufs-async-domain`

## 1. Implemented candidate

Added `kernel-baseline/round116/0001-ufs-core-per-hba-async-domain.patch`.

The patch implements the ROUND108 design in the exact pinned source:

1. Extends the existing `struct ufs_hba_priv` with an embedded `struct async_domain`, returned scan cookie and scheduled flag. It does not change public `struct ufs_hba`.
2. Initializes the embedded domain pending list and `registered = 1` in `ufshcd_alloc_host()`. Registered-domain semantics preserve participation in global `async_synchronize_full()`.
3. Replaces the discarded default-domain `async_schedule()` cookie with `async_schedule_domain()` and records the cookie for this HBA.
4. Makes `ufshcd_remove()` join that specific callback at its first HBA-lifecycle boundary using `async_synchronize_cookie_domain(cookie + 1, domain)`, before reading `hba->ufs_device_wlun` or tearing down sysfs, SCSI, IRQ, HBA, PHY or regulator resources.
5. Leaves unrelated SCSI async work and the global default async domain unchanged.

## 2. Source-level validation performed

The patch generator fetched the three source files from the exact pinned ACK commit and verified that every replacement context occurs exactly once in `ufshcd.c` / `ufshcd-priv.h`. It generated unified hunks from those fetched source lines and rejected overlapping edits.

Key assumptions carried forward from ROUND108:
- `ufshcd-priv.h` is the existing SCSI-host private wrapper and `struct ufs_hba` is its first member.
- The UFS scan schedule occurs once in `ufshcd_init()`.
- The async API in the pinned tree exposes `async_schedule_domain()` and `async_synchronize_cookie_domain()`.
- The stored cookie plus one is the checkpoint that waits until the scheduled callback has left the domain pending list.

This is a source-pinned patch candidate, not a claim of successful kernel compilation or runtime behavior.

## 3. Required test gate — not yet run

The local test Agent must independently:
- apply the patch in a disposable checkout of the pinned ACK source;
- run `git apply --check` before applying and confirm there are no offsets/fuzz;
- run `scripts/checkpatch.pl --strict` on the patch;
- compile at least the affected UFS core object using the project's pinned Kleaf environment, then run the full manifest-pinned Stage A `//common:dby_w09` Image build if the current disposable worktree can include the current accepted Stage A patch series;
- verify there is only one UFS-owned scan scheduling site and that all pre-schedule failure paths leave the flag false;
- inspect the synchronous OOM fallback, callback-completed-before-remove, blocked-in-`host_sem`, and ordinary remove paths;
- upload one report with commands, exact source/tree/patch hashes, exit codes and logs.

The Agent must not author or modify the patch, change the AI2 branch, edit DTS/config/firmware, access or flash the device, or start a later task. If the disposable source tree or build environment is unavailable, report that exact blocker and stop.

## 4. Status

- AI1 patch candidate: CREATED in this branch.
- Exact-source context checks: PASS.
- Patch apply / checkpatch: NOT RUN by a test executor.
- Compilation / Kleaf Image build: NOT RUN.
- Device boot / storage acceptance: NOT RUN; Stage A Phase E/F remain gated separately.

The patch must remain a candidate until the test report is reviewed. It must not be represented as already integrated into the 2号 AI implementation branch.
