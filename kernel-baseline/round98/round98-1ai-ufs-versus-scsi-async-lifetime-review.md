# ROUND98 — 1号 AI source review: distinguish UFS async-probe join from SCSI async-scan teardown

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, under a separate taskbook  
**Pinned baseline:** ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Clarifies:** ROUND97  
**Related reviews:** ROUND95, ROUND96, ROUND97

## 1. Executive result

ROUND97 correctly identified a missing explicit join for the UFS-owned `ufshcd_async_scan()` callback. This round checks whether a second global async join is also needed for the later SCSI bus scan.

**Refined conclusion:**
1. A per-HBA join for `ufshcd_async_scan()` remains mandatory before UFS remove tears down HBA resources or the VCC sidecar.
2. The separate SCSI async scan does not appear to require a second global async barrier for the current pinned UFS host template. Its actual command/probe phase is serialized by the SCSI host's `scan_mutex`; `scsi_remove_host()` obtains that mutex and changes the host state to `SHOST_CANCEL`. A scan that has not yet entered its critical section will then be rejected by `scsi_host_scan_allowed()`.
3. The SCSI async worker can still have a finalization tail after `scsi_remove_host()` releases the scan mutex. That tail may invoke `ufshcd_sdev_destroy()`, but it is not the bus-command scan phase and the callback currently does not access the VCC sidecar. The async scan's `scsi_host_get()` reference keeps the embedded HBA memory alive until `scsi_host_put()`.

Therefore, **do not solve this by adding `async_synchronize_full()` or an indiscriminate global wait for all SCSI scans**. Join the exact UFS-owned callback; preserve the SCSI layer's own host-state/scan-mutex/reference protocol. If 2号 AI adds sidecar accesses to SCSI-device destruction or other post-scan callbacks, that changes this conclusion and requires a new lifetime review.

This is source-level reasoning only. No runtime race has been reproduced.

## 2. UFS-owned async callback: still requires an exact join

Pinned source: `drivers/ufs/core/ufshcd.c`.

- `ufshcd_init()` schedules `ufshcd_async_scan(hba)` at line 11190.
- `ufshcd_async_scan()` (lines 9360–9378) takes `host_sem`, performs `ufshcd_probe_hba()`, then calls `ufshcd_add_lus()` on success; it finally performs `pm_runtime_put_sync(hba->dev)` and may log using HBA/device state.
- `ufshcd_remove()` (lines 10716–10733) currently proceeds directly to WLUN handling, work cancellation, SCSI-host removal, HBA stop and `ufshcd_hba_exit()`; it has no join for the previously scheduled UFS callback.

The UFS callback can be using the HBA before it submits the SCSI scan. Consequently, waiting only for the SCSI `scan_mutex` is insufficient: it would not join the earlier `ufshcd_probe_hba()` or UFS logical-unit setup work.

**Required ordering:** join the UFS async callback at the beginning of `ufshcd_remove()`, before dereferencing mutable HBA state for removal or tearing down any resource the callback may use. Do not hold `host_sem`, `scan_mutex`, a regulator lock or another lock required by the callback while waiting.

## 3. SCSI async scan: exact synchronization already present

Pinned sources:
- `drivers/scsi/scsi_scan.c`
- `drivers/scsi/hosts.c`
- `include/scsi/scsi_host.h`
- `drivers/ufs/core/ufshcd.c`

### 3.1 The UFS host uses the default SCSI scan path

The pinned `ufshcd_driver_template` (around lines 9427–9443) supplies `queuecommand`, `sdev_init`, `sdev_configure`, `sdev_destroy` and error handlers. It does not set the optional `scan_start` or `scan_finished` callbacks.

Therefore the pinned SCSI `do_scsi_scan_host()` takes its normal branch and calls `scsi_scan_host_selected()`, rather than a host-specific scan loop outside the SCSI scan-mutex protocol.

### 3.2 Probe/command phase is under scan_mutex

- `scsi_scan_host()` calls `scsi_prep_async_scan()`, which takes a `scsi_host_get(shost)` reference, sets `shost->async_scan`, and submits `do_scan_async()`.
- `do_scan_async()` calls `do_scsi_scan_host()`.
- The default `scsi_scan_host_selected()` path takes `shost->scan_mutex` before calling `scsi_scan_channel()` and the target/LUN probe functions. The SCSI inquiry/report-LUN activity therefore occurs within the scan-mutex critical section.
- `scsi_remove_host()` first takes this same `scan_mutex`, changes the state to `SHOST_CANCEL` under `host_lock`, and only then continues to flush the TMF workqueue and forget/remove devices.

This produces the needed serialization:
- If the SCSI scan is already probing devices, remove blocks on `scan_mutex` until that probe phase releases it.
- If the SCSI scan has not yet acquired the mutex, remove marks the host `SHOST_CANCEL`; when the scan later enters `scsi_scan_host_selected()`, `scsi_host_scan_allowed()` rejects scanning because it accepts only `SHOST_RUNNING` or `SHOST_RECOVERY`.

Thus, by the time `scsi_remove_host()` passes its initial scan-mutex/state transition, no new SCSI bus-probe command phase can begin for this host.

## 4. SCSI async finalization may outlive remove, but has a distinct lifetime

After `do_scsi_scan_host()` returns, `do_scan_async()` calls `scsi_finish_async_scan()`. That function takes `scan_mutex`, waits for the SCSI ordering completion, and calls `scsi_sysfs_add_devices()`.

There is a possible interleaving where `scsi_remove_host()` wins the mutex after the probe phase and marks the host `SHOST_CANCEL` before `scsi_finish_async_scan()` acquires it. The later finalization path then calls `scsi_host_scan_allowed()`; because the host is cancelled, it calls `__scsi_remove_device()` for devices that must not be published. It does not resume the bus-probe phase.

The current UFS-specific callback reached by that removal is `ufshcd_sdev_destroy()` (around lines 5600–5634). It retrieves the HBA from `shost_priv()`, updates `ufs_device_wlun` under the host lock, and removes a device link where needed. It does **not** read `android_oem_data1`, dereference the VCC sidecar, or invoke the regulator enable/disable helpers.

The SCSI async scan data retains the `scsi_host_get()` reference from `scsi_prep_async_scan()` until `scsi_finish_async_scan()` calls `scsi_host_put()`. Therefore the Scsi_Host allocation and its embedded `ufs_hba_priv` remain alive while this finalization tail can call `ufshcd_sdev_destroy()`, even if the platform-device devres reference has already been dropped.

**Boundary:** this argument applies to the pinned callbacks and current implementation only. 2号 AI must not add sidecar dereferences to `ufshcd_sdev_destroy()`, SCSI host teardown callbacks, or any post-scan finalization path unless the sidecar lifetime is extended or a new synchronization guarantee is added.

## 5. Exact sidecar recommendation

The narrowest candidate remains a per-HBA completion object in the existing sidecar:

1. Allocate and initialize the sidecar before `ufshcd_init()` can schedule the async callback. The completion must start in a state that lets removal proceed if async scheduling is never reached.
2. Immediately before scheduling `ufshcd_async_scan()`, reset/arm the completion.
3. At the single common exit of `ufshcd_async_scan()`, signal completion only after its final `pm_runtime_put_sync()` and final HBA/device logging/access.
4. At the very beginning of `ufshcd_remove()`, retrieve the sidecar and wait for that completion before touching WLUN state, cancelling HBA work, stopping the controller or removing regulators.
5. Ensure the synchronous fallback path of `async_schedule()` also signals completion before returning. Do not assume that `async_schedule()` always queues work to another thread.
6. Cover every callback exit path and probe-failure path. If the callback may be scheduled only once per HBA, document and assert that one-shot invariant.
7. Keep the existing SCSI protocol: after joining UFS async probe, call the normal `scsi_remove_host()`; do not add a global `async_synchronize_full()` merely to wait for the SCSI finalization tail.
8. Keep sidecar-free code paths valid. If the sidecar is optional, the UFS join must still exist for every path that can schedule `ufshcd_async_scan()`; either allocate a small lifecycle token unconditionally for this board-specific driver path or use a separately proven per-HBA cookie/completion storage strategy.

A completion is preferred over `async_synchronize_cookie(cookie + 1)` for a first implementation because it is scoped to this HBA and does not wait for unrelated global async jobs. If 2号 AI chooses the cookie method, it must document the pinned API's “submitted prior to cookie” semantics and global default-domain effects.

## 6. Remaining verification

Required before the sidecar implementation is considered lifecycle-safe:

- Inspect 2号 AI's actual complete integration diff to confirm the wait is the first remove-side lifetime operation and does not hold a callback-needed lock.
- Confirm completion is initialized/armed before scheduling and signalled on all exits, including `async_schedule()` synchronous fallback.
- Confirm no new sidecar access is introduced in `ufshcd_sdev_destroy()` or any SCSI finalization path that can outlive the device remove callback.
- Confirm final `.config` enables `CONFIG_ANDROID_VENDOR_OEM_DATA=y`, and the OEM slot is unused in the complete worktree/OEM extensions (ROUND95 conditions).
- Run the exact pinned Kleaf KMI/ABI check after implementation. No ABI PASS is inferred from this source review.
- Use a controlled concurrency test for removal during UFS async probe and during SCSI scan handoff before device validation.

## 7. Evidence map (all pinned to ACK commit)

| Path | Relevant lines | Evidence |
|---|---:|---|
| `drivers/ufs/core/ufshcd.c` | 9360–9378 | UFS async callback body and final runtime-PM put |
| `drivers/ufs/core/ufshcd.c` | 9087–9127 | UFS LUN setup precedes `scsi_scan_host()` |
| `drivers/ufs/core/ufshcd.c` | 9427–9443 | UFS host template lacks custom `scan_start/scan_finished` |
| `drivers/ufs/core/ufshcd.c` | 9835–9852 | HBA resource teardown in `ufshcd_hba_exit()` |
| `drivers/ufs/core/ufshcd.c` | 10716–10733 | UFS remove sequence and missing UFS async join |
| `drivers/scsi/scsi_scan.c` | 1880–1901 | Default scan holds `scan_mutex` around probe operations |
| `drivers/scsi/scsi_scan.c` | 1910–1916 | Cancelled host's late SCSI sysfs finalization removes devices |
| `drivers/scsi/scsi_scan.c` | 1928–1967 | SCSI async scan takes a host reference |
| `drivers/scsi/scsi_scan.c` | 1977–2017 | Finalization and host-reference release |
| `drivers/scsi/scsi_scan.c` | 2050–2074 | SCSI scan scheduling and async completion path |
| `drivers/scsi/hosts.c` | 165–203 | `scsi_remove_host()` scan-mutex/state cancellation |
| `include/scsi/scsi_host.h` | 805–810 | Scan allowed only in RUNNING / RECOVERY |
| `drivers/ufs/core/ufshcd.c` | 5600–5634 | UFS `sdev_destroy` touches HBA but not sidecar |
| `drivers/scsi/scsi_pm.c` | 245–258 | SCSI host runtime-PM references around async scan |

## 8. Review scope and verdict

- Read-only review of the exact pinned ACK source.
- No source, DTS, binding, patch, Kconfig, `.config`, Image, AI2 branch, protected DTS branch or PR was modified.
- No patch apply, compiler, Kleaf, KMI checker, dt-schema, runtime concurrency test, regulator measurement or device operation was run.

**Final verdict:** ROUND97's UFS async-callback join requirement is upheld. The SCSI async-scan finalization tail is a separate, reference-protected cleanup path in the pinned tree and does not currently require a second global async wait for the VCC sidecar. Keep that conclusion conditional on the exact callback set and prohibit future sidecar access from the post-scan tail. Phase E/F remain BLOCKED; Phase G remains NOT RUN.
