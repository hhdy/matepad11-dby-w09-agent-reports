# ROUND97 — 1号 AI source review: UFS async-scan join is required before HBA / sidecar teardown

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, under a separate taskbook  
**Pinned baseline:** ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Related reviews:** ROUND95, ROUND96

## 1. Executive result

ROUND96's proposal to pass `struct ufs_hba *` through the private UFS regulator enable/disable helpers remains a plausible way to reach the `ufs_hba::android_oem_data1` sidecar without changing KMI-visible UFS interfaces.

However, ROUND95's devres-order proof is **not sufficient by itself** to establish sidecar lifetime safety. The pinned UFS core schedules an independent asynchronous callback, `ufshcd_async_scan()`, with `async_schedule()`. The callback retains and uses the HBA after `ufshcd_init()` returns. The reviewed UFS remove path does not explicitly join that UFS-owned asynchronous callback before `ufshcd_hba_exit()` and device devres release.

The SCSI mid-layer has a separate asynchronous scan mechanism, but its scan tracking is not a join for the earlier UFS `ufshcd_async_scan()` callback. In particular, that UFS callback can still be running its HBA-side probe / WLUN / devfreq setup before it calls `scsi_scan_host()`.

**Disposition:** treat asynchronous HBA/sidecar quiescence as a required implementation gate for 2号 AI. Do not adopt the sidecar on the assumption that reverse devres order alone protects it. This is a source-level lifecycle gap / race risk; this review does not claim a runtime use-after-free has been reproduced.

## 2. Exact UFS asynchronous callback path

Pinned source: `drivers/ufs/core/ufshcd.c`.

### 2.1 Scheduling point

In `ufshcd_init()` (lines 10952–11203), after the host has initialized and the SCSI host has been added, the core executes:

```c
pm_runtime_get_sync(dev);
...
async_schedule(ufshcd_async_scan, hba);
```

The call is at line 11190. The return value of `async_schedule()` is not retained in the current source. `ufshcd_init()` then returns to `ufshcd_pltfrm_init()`, which completes platform probe and enables runtime PM.

The async callback itself is `ufshcd_async_scan()` (lines 9360–9378). It:
1. takes `hba->host_sem`;
2. calls `ufshcd_probe_hba(hba, true)`;
3. releases the semaphore;
4. if successful, calls `ufshcd_add_lus(hba)`;
5. finally calls `pm_runtime_put_sync(hba->dev)` and may log through `hba->dev`.

The callback therefore continues to use HBA and device state after the synchronous platform probe path has returned.

### 2.2 Work performed before the SCSI scanner is scheduled

`ufshcd_add_lus()` (lines 9087–9127) performs UFS-owned work before calling `scsi_scan_host(hba->host)`:
- adds the well-known logical units;
- configures devfreq / clock-scaling state when supported;
- initializes clock-scaling sysfs;
- schedules `ufs_rtc_update_work`;
- probes UFS BSG;
- then starts the SCSI host scan.

This distinction matters: a SCSI scan barrier cannot join the UFS callback while it is still in the preceding HBA-side work.

## 3. Exact remove path and missing join

Pinned source: `drivers/ufs/host/ufshcd-pltfrm.c` and `drivers/ufs/core/ufshcd.c`.

### 3.1 Platform remove

`ufshcd_pltfrm_remove()` (platform file lines 709–717) obtains a runtime-PM reference, calls `ufshcd_remove(hba)`, disables runtime PM and drops its reference.

That runtime-PM get is a usage-count / resume operation. In the pinned PM runtime implementation, `__pm_runtime_resume()` increments `dev->power.usage_count` when `RPM_GET_PUT` is set and then carries out a resume operation. It is not a wait for unrelated users of the device's usage reference to finish.

### 3.2 UFS core remove

`ufshcd_remove()` (core lines 10716–10733):
- optionally obtains a runtime-PM reference for the UFS device WLUN;
- removes hwmon, BSG and sysfs state;
- cancels `ufs_rtc_update_work`;
- destroys the TMF queue;
- calls `scsi_remove_host()` when the host was added;
- disables interrupts, stops the HBA and calls `ufshcd_hba_exit()`.

`ufshcd_hba_exit()` (lines 9835–9852) tears down clocks / scaling / gating work, variant state, UFS regulators and the HBA power state.

The reviewed UFS remove path contains no `async_synchronize_cookie()`, `async_synchronize_full()` or UFS-specific completion wait corresponding to the `async_schedule(ufshcd_async_scan, hba)` submission. No cookie from that submission is saved.

## 4. Why SCSI scan tracking is not a substitute

Pinned source: `drivers/scsi/hosts.c` and `drivers/scsi/scsi_scan.c`.

- `scsi_remove_host()` (hosts.c lines 165–203) calls `scsi_forget_host()`, waits for the TMF workqueue and removes the SCSI host. It does not itself call `scsi_complete_async_scans()`.
- `scsi_forget_host()` (scsi_scan.c lines 2076 onward) removes devices already attached to the host; it is not a join for `ufshcd_async_scan()`.
- The SCSI layer's `scsi_prep_async_scan()` / `scsi_finish_async_scan()` mechanism tracks the separate `do_scan_async()` work created by `scsi_scan_host()`. It takes a SCSI-host reference for that scan and releases it on completion.
- `scsi_complete_async_scans()` waits on the SCSI layer's `scanning_hosts` list. The UFS `ufshcd_async_scan()` callback is not inserted into that list merely by being scheduled with kernel `async_schedule()`; it reaches `scsi_scan_host()` only later, after its own UFS-side work.

Therefore, the SCSI scan lifetime and the UFS async-callback lifetime are distinct. Any implementation relying on SCSI's own scan completion to protect HBA-side sidecar access must prove that the UFS callback has reached the SCSI scan handoff and that all remaining HBA accesses are covered. The reviewed call graph does not establish this.

## 5. Relationship to ROUND95 devres ordering

ROUND95 correctly identified the following registration order:
1. `ufshcd_alloc_host()` allocates the SCSI host / HBA and registers `ufshcd_devres_release(host)`;
2. `ufshcd_pltfrm_init()` later parses regulators;
3. a sidecar allocated by `devm_kzalloc()` during regulator parsing would be registered after the host-release action;
4. devres unwinds in reverse order, so the later sidecar allocation is freed before the earlier host-release action.

This order protects the sidecar relative to HBA memory **only after all asynchronous users have stopped**. It does not prove that `ufshcd_async_scan()` or SCSI scan work has stopped when platform remove returns and device devres starts unwinding.

The existing HBA OEM slot and `CONFIG_ANDROID_VENDOR_OEM_DATA` remain subject to ROUND95's checks: final configuration must enable the field, and 2号 AI must verify no existing OEM consumer in its complete integration tree. This review does not change those conditions.

## 6. Required implementation closure for 2号 AI

Before treating ROUND96's sidecar design as teardown-safe, 2号 AI should establish an explicit, race-free completion guarantee for the UFS async callback:

1. **Track the UFS async submission.** The current `async_schedule()` return cookie is available for checkpoint synchronization but is currently discarded. Alternatively, use a per-HBA completion/refcount protocol with well-defined ownership and all callback exit paths covered.
2. **Join before teardown.** Ensure the callback has completed before `ufshcd_hba_exit()`, regulator cleanup, sidecar release or any other resource teardown it can race with. The wait must not occur while holding a lock/semaphore that the callback needs.
3. **If using async-cookie synchronization:** the pinned API documents `async_synchronize_cookie(cookie)` as waiting for asynchronous functions submitted *prior to* the checkpoint cookie. In this implementation, the callback's returned cookie is its own sequence value; a checkpoint strictly after that value (normally `cookie + 1`) is needed to include that callback. Review default-domain/global wait implications before choosing this mechanism.
4. **Cover all exits.** Include successful scan, UFS probe failure, WLUN-add failure, error recovery / rescan interaction, platform remove and probe-failure paths. Do not signal completion before the callback's final HBA/device access.
5. **Keep SCSI scan lifetime separate.** If the SCSI scan worker can continue after the UFS callback returns, prove that its host reference and teardown ordering are safe for any state it can access; do not assume an UFS callback join alone automatically drains that second worker.
6. **Preserve KMI.** Prefer private tracking / sidecar or an existing lifecycle primitive over adding fields to `struct ufs_hba`, `struct ufs_vreg` or exported variant-ops interfaces without separate ABI approval.
7. **Add validation.** Test remove/unbind during the async UFS probe window and during SCSI scan handoff in a controlled test environment, or provide equivalent concurrency proof and targeted tests before device validation.

A completion object owned by the sidecar can be one design candidate, but it must be initialized before scheduling, completed on every callback exit path, and waited before resource teardown. It must not be signalled while the callback still needs to access HBA or the sidecar. A stored async cookie is another candidate; its checkpoint semantics and global-domain side effects must be handled correctly.

## 7. Evidence references

All references below are pinned to ACK commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.

- `drivers/ufs/core/ufshcd.c`: `ufshcd_async_scan()` lines 9360–9378; `ufshcd_add_lus()` lines 9087–9127; `ufshcd_hba_exit()` lines 9835–9852; `ufshcd_remove()` lines 10716–10733; `ufshcd_init()` async scheduling at line 11190.
- `drivers/ufs/host/ufshcd-pltfrm.c`: `ufshcd_pltfrm_init()` lines 644–702; `ufshcd_pltfrm_remove()` lines 709–717.
- `drivers/scsi/hosts.c`: `scsi_remove_host()` lines 165–203; `scsi_host_alloc()` lines 392–544.
- `drivers/scsi/scsi_scan.c`: `scsi_complete_async_scans()` lines 142–192; SCSI async scan bookkeeping lines 1919–2075; `scsi_forget_host()` lines 2076 onward.
- `kernel/async.c`: async scheduling / cookie sequence allocation lines 150–180; cookie synchronization lines 302–335.
- `include/linux/async.h`: `async_schedule()` returns an `async_cookie_t`; `async_synchronize_cookie()` declarations and API comments.
- `drivers/base/power/runtime.c`: `__pm_runtime_resume()` lines 1175–1202 increments usage count for `RPM_GET_PUT` then performs resume; this is not an async-callback join.
- `include/ufs/ufshcd.h`: `struct ufs_hba` ends with `ANDROID_OEM_DATA(1)` at line 1299 in this pinned tree.

## 8. Review scope and status

- Source-only review of the exact pinned ACK commit; no local workspace or device access.
- No source, DTS, binding, patch, Kconfig, .config, Image, 2号 AI branch, protected DTS branch or PR was modified.
- No patch apply, compiler, Kleaf, KMI checker, dt-schema, runtime concurrency test, regulator measurement or device operation was run.

**Final status:** ROUND96's private-helper / sidecar direction remains plausible, but teardown safety is **NOT YET PROVEN** until the UFS async scan is explicitly joined and the subsequent SCSI scan lifetime is separately accounted for. Phase E/F remain BLOCKED; Phase G remains NOT RUN.
