# TEST AGENT TASKBOOK — ROUND124 combined UFS core candidate validation

**Task ID:** TEST-AGENT-ROUND124  
**Task owner:** 1号 AI（ChatGPT）  
**Executor:** 用户本地测试 Agent（只读验证 / 构建执行）  
**2号 AI:** 独立负责 `ai-parallel/stagea-port-until-boot`；本任务严禁改动其分支。  
**Task type:** byte-identical patch validation, source inspection and build only. Agent is not a kernel patch author.

## 1. Candidate inputs

Repository: `hhdy/matepad11-dby-w09-agent-reports`  
Candidate branch: `ai1/round124-ufs-core-combined-candidates`  
Pinned ACK: `aosp-mirror/kernel_common @ 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.

Apply these two patches in the exact listed order:

| Order | Candidate | Expected Git blob | Expected SHA-256 |
|---|---|---|---|
| 1 | `kernel-baseline/round124/0001-ufs-core-per-hba-async-domain.patch` | `f604c8672fcbc98f3e9645f5e8888c8a34b1c11e` | `12efbe8a14d80f8b657bad763a344b5439abeb572158079beb32daba05e02bc7` |
| 2 | `kernel-baseline/round124/0002-ufs-core-vreg-load-first.patch` | `64dd2ad9022251e2411a1a745aeb920a0badfa85` | `2f335f513fd1f7013a0edbc2e0d9eb5dca9ae68055eff4fd526b1c4274cfca66` |

The files are byte-for-byte copies of the previously validated ROUND120 and ROUND122 patches. Recompute hashes; if either identity differs, stop and report BLOCKED. Do not fix or regenerate a patch.

## 2. Required Stage A baseline

Use a disposable copy of the validated Stage A ROUND32 workspace with the ordered 15-patch series from:

`ai-parallel/stagea-port-until-boot`  
`kernel-baseline/round61/round32-stagea-series.txt`  
branch head recorded for this round: `5f587aaa40853cf3ec754f7455930aa404bf9b9a`.

The manifest's base commit must be the pinned ACK above. Confirm the Stage A-only working-tree snapshot / changed-file list matches the existing ROUND32 / ROUND120 / ROUND122 test workspace before applying the new candidates.

**Do not include AI2 ROUND33 patch 16** (`round33-0001-regulator-proxy-self-target-only.patch`) in this test: that separate AI2 patch was not yet accepted by the local validation gate when ROUND124 was issued. If the only available local workspace already has patch 16 applied, do not remove it in place; make a fresh disposable ROUND32/15-patch copy or report BLOCKED.

Do not make any branch checkout, commit, or mutation in shared workspaces. Use a detached disposable worktree or disposable copy. Never modify any original source/build tree.

## 3. Allowed actions

1. Fetch both patches and verify expected Git blob / SHA-256.
2. Verify source HEAD and the Stage A 15-patch manifest identity.
3. On the disposable Stage A tree, run `git apply --check --verbose` for patch 0001, apply it, and run `git diff --check`.
4. Then run `git apply --check --verbose` for patch 0002, apply it, and run `git diff --check`. Keep the exact order 0001 then 0002. Record actual output. Zero offset and zero fuzz are required for PASS.
5. Confirm the candidate overlay adds exactly two changed source paths relative to the Stage A baseline: `drivers/ufs/core/ufshcd.c` and `drivers/ufs/core/ufshcd-priv.h`. Stage A's own pre-existing changes must remain intact.
6. Run the source gates in §4.
7. Run `scripts/checkpatch.pl --strict --no-signoff` separately on both patches. Record errors, warnings, CHECKs and exit codes exactly. Do not fix style or candidate contents.
8. Compile the affected UFS core objects using the pinned Kleaf toolchain and the Stage A .config. At minimum compile `drivers/ufs/core/ufshcd.o`; because `ufshcd-priv.h` is a shared private header, also compile all UFS core objects or document why the selected Kleaf target rebuilt every dependent object.
9. Run the full build:
   `tools/bazel build //common:dby_w09 --jobs=8 --local_ram_resources=6144`.
10. Record Image, System.map, vmlinux and .config sizes / SHA-256. Confirm .config is byte-identical to the Stage A-only build result unless an independently justified config delta is found (none is expected).
11. Restore the disposable workspace to its pre-overlay Stage A state and verify the exact pre-overlay dirty path list and diff hash / snapshot. If cleanup cannot be proven, stop and disclose it.

## 4. Required source gates

### A. ROUND120 async lifecycle

- `ufshcd-priv.h` includes `linux/async.h` and stores `struct async_domain`, `async_cookie_t`, and a scheduled flag only in `struct ufs_hba_priv`.
- Public `struct ufs_hba` and public headers are unchanged.
- `ufshcd_alloc_host()` initializes `async_domain.pending`, sets `registered = 1`, and initializes the scheduled flag false before any call to `ufshcd_init()` can schedule the scan.
- The only UFS scan schedule site uses `async_schedule_domain()` and stores the returned cookie.
- `ufshcd_remove()` joins the scheduled cookie + 1 in that HBA's domain before reading the HBA's WLUN or running any teardown. When no scan was scheduled, remove must not wait on an uninitialized cookie.
- Inspect the three in-tree `ufshcd_alloc_host()` call sites and remove callers; confirm no caller holds `host_sem` before entering the join.

### B. ROUND122 regulator load ordering

- In `ufshcd_disable_vreg()`, the checked `ufshcd_config_vreg(dev, vreg, false)` runs before `regulator_disable()`; load-clear failure exits before decrement attempt.
- `vreg->enabled` is cleared only after `regulator_disable()` succeeds.
- In `ufshcd_enable_vreg()`, active load configuration is attempted before the already-enabled early exit; it does not call `regulator_enable()` again for an already-enabled handle.
- Preserve the known limitation: the patch does not solve every post-decrement regulator error or the devm release / nonzero enable_count lifetime boundary. Do not claim it does.

### C. Combined blast radius

- No public UFS struct layout, Kconfig, DTS, regulator core, binding, config, AVB, boot packaging or firmware changes are introduced by these two candidate patches.
- No Stage A patch was edited to accommodate these candidates.

## 5. Prohibited actions

- Do not author, edit, reformat, regenerate, or repair either kernel patch.
- Do not author kernel code, DTS, bindings, tests, config or firmware.
- Do not modify `main`, `ack18-dby-w09-dts-draft`, PR #1, `ai-parallel/stagea-port-until-boot`, `firmware-audit-v1` (except the one required final report upload), or any other AI2 branch.
- No device connection, ADB, fastboot, root, reboot, boot, flash, partition access, DTBO/AVB/vbmeta operation or firmware upload.
- Do not integrate or merge either candidate into AI2 Stage A.
- Do not start ROUND125.

## 6. Required report

Upload exactly one report:

`firmware-analysis/round124/TEST_AGENT_ROUND124_COMBINED_UFS_CORE_REPORT.txt`

on `firmware-audit-v1`.

Include:
- exact source/workspace identity and Stage A manifest,
- both patch Git blobs and SHA-256,
- commands, full exit codes and relevant excerpts,
- apply offset/fuzz results for both sequential applies,
- per-gate PASS/FAIL/BLOCKED evidence,
- checkpatch results per patch,
- affected object compile results,
- complete Image build results and artifact hashes,
- pre/post workspace restoration evidence,
- explicit statement that no device or prohibited action occurred.

Do not upload build artifacts or full local paths that reveal usernames, tokens, serials or private directories. Sanitize logs, preserving source paths, commands, hashes, exit codes and compiler/tool identities.

After the sole report is uploaded and read-back verified, stop immediately. Do not start another task.
