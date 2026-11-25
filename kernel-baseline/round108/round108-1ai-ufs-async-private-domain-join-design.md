# ROUND108 — 1号 AI source design: per-HBA join for UFS-owned asynchronous scan

**Date:** 2026-11-25  
**Owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Pinned ACK:** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Scope:** exact source review of Linux async-domain API and UFS HBA probe/remove lifetime. No kernel, DTS, patch, or 2号 AI branch was modified.

## 1. Decision

Pinned ACK `ufshcd_init()` submits `ufshcd_async_scan()` with `async_schedule()`, discards the returned cookie, and returns to the platform probe while the callback may still be using the HBA. Pinned `ufshcd_remove()` begins touching HBA and SCSI resources without first joining that UFS-owned callback.

The safe narrow solution is a **per-HBA registered async domain plus stored checkpoint cookie**, held in the existing private `struct ufs_hba_priv` wrapper. At the very start of `ufshcd_remove()`, before PM runtime operations, sysfs/BSG/host teardown, or hardware shutdown, wait for that HBA's callback to finish using:

```c
async_synchronize_cookie_domain(cookie + 1, &priv->async_domain);
```

This gives device-local quiescence without serializing unrelated UFS hosts or unrelated default-domain async jobs. The domain must be registered (`registered = 1`) so the work also participates in the kernel's global `async_synchronize_full()` contract.

This design does **not** require a global `async_synchronize_full()`, a new HBA public field, or a SCSI async barrier. It is a source design requirement for the later implementation owner, not a patch authorization.

## 2. Exact pinned ACK facts

### 2.1 Current UFS async schedule

Pinned `drivers/ufs/core/ufshcd.c`:
- `ufshcd_async_scan()` calls `down(&hba->host_sem)`, probes/initializes the device, processes the probe result, releases the semaphore, may add LUs, then calls `pm_runtime_put_sync(hba->dev)`.
- `ufshcd_init()` adds the SCSI host and, later, invokes `async_schedule(ufshcd_async_scan, hba)`.
- The returned `async_cookie_t` is discarded.
- `ufshcd_remove()` starts by using HBA state and then removes hwmon/BSG/sysfs/workqueues, removes the SCSI host, disables interrupts, stops the HBA and calls `ufshcd_hba_exit()`. There is no async join before these operations.

Pinned source:
[`drivers/ufs/core/ufshcd.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c)

### 2.2 The UFS private wrapper already exists

Pinned `drivers/ufs/core/ufshcd-priv.h` has:

```c
struct ufs_hba_priv {
        struct ufs_hba hba;
        bool zwor_sup;
};
```

`ufshcd_alloc_host()` allocates `sizeof(struct ufs_hba_priv)` as SCSI host private storage and sets `hba = shost_priv(host)`. The private wrapper is therefore the intended location for per-instance lifecycle state without extending the `struct ufs_hba` layout.

The HBA devres release (`scsi_host_put`) is registered before the HBA private fields are initialized. It runs only later during device devres release, after the synchronous remove callback. A join at the beginning of `ufshcd_remove()` therefore occurs while the private wrapper and its domain remain alive.

Pinned sources:
- [`drivers/ufs/core/ufshcd-priv.h`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd-priv.h)
- [`ufshcd_alloc_host()` and devres registration](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c)

### 2.3 Exact async-domain API semantics

Pinned `include/linux/async.h` defines:

```c
struct async_domain {
        struct list_head pending;
        unsigned registered:1;
};
```

It provides:
- `async_schedule_domain()`;
- `async_synchronize_cookie_domain()`;
- `async_synchronize_full_domain()`.

There is no separate `async_domain_init()` function in this pinned API. An embedded per-HBA domain must have its pending list initialized explicitly with `INIT_LIST_HEAD()`; its `registered` field must be set intentionally.

The static macro `ASYNC_DOMAIN(name)` initializes a domain with `registered = 1`; `ASYNC_DOMAIN_EXCLUSIVE(name)` sets `registered = 0`. A per-HBA domain stored inside dynamic host-private memory must replicate the registered-domain initialization semantics explicitly.

Pinned source:
[`include/linux/async.h`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/linux/async.h)

### 2.4 Why the cookie checkpoint is `cookie + 1`

In pinned `kernel/async.c`:
- every scheduled job receives a globally increasing cookie;
- each job is appended to its domain's pending list in cookie order;
- the worker removes its entry only after the callback returns;
- `async_synchronize_cookie_domain(cookie, domain)` waits until the lowest pending cookie in that domain is greater than or equal to the checkpoint;
- therefore a checkpoint of the scheduled cookie itself does not guarantee that the job with that exact cookie has left the pending list;
- using `cookie + 1` waits until that job has completed and its entry has been removed.

If allocation pressure causes `async_schedule_node_domain()` to run the callback synchronously, the scheduler returns only after the callback has completed; the subsequent checkpoint is therefore already satisfied.

A registered custom domain adds each job to both its per-domain pending list and the global pending list. This preserves global `async_synchronize_full()` visibility. An exclusive domain would omit the global-list entry and is not appropriate for this UFS boot-time task unless the subsystem deliberately changes that global synchronization contract.

Pinned source:
[`kernel/async.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/kernel/async.c)

## 3. Implementation shape for 2号 AI

The following is a design shape, not a source patch. Names can be adjusted consistently with the final code.

### 3.1 Private state

Add to `struct ufs_hba_priv`:
- one `struct async_domain`;
- one `async_cookie_t` for the scheduled UFS callback;
- one boolean recording whether this callback was scheduled.

Because the domain is embedded (not a pointer), include `<linux/async.h>` where the complete type is required. Do not add these fields to public `struct ufs_hba`.

### 3.2 Initialize in `ufshcd_alloc_host()`

Immediately after `hba = shost_priv(host)`:
- obtain `priv = to_hba_priv(hba)`;
- initialize `priv->async_domain.pending` with `INIT_LIST_HEAD()`;
- set `priv->async_domain.registered = 1`;
- initialize the scheduled flag false.

Do this before any possible call to `ufshcd_init()` or any other code can schedule work.

### 3.3 Store the returned cookie at the existing schedule point

Replace the existing default-domain call with an explicit domain schedule, storing the returned cookie in the private wrapper and marking the scheduled state.

Only the existing UFS-owned `ufshcd_async_scan()` should be moved into this per-HBA domain. Do not move unrelated SCSI async work into it.

### 3.4 Join at the earliest remove boundary

At the **first executable point** in `ufshcd_remove()`, before the current initial `ufshcd_rpm_get_sync()` and before hwmon/BSG/sysfs/host/IRQ/HBA teardown:
- obtain the private wrapper;
- if the UFS callback was scheduled, wait with `async_synchronize_cookie_domain(stored_cookie + 1, &priv->async_domain)`;
- only after the wait returns mark the scheduled flag false and continue remove.

Do not insert the join only inside `ufshcd_hba_exit()`: that function is reached after `ufshcd_remove()` has already touched and removed multiple HBA resources. The pinned init failure path also calls `ufshcd_hba_exit()` before the async scheduling point, so the private false flag should make any unrelated pre-scan cleanup a no-op if a shared helper is used.

The remove path must not hold `hba->host_sem` or another lock/semaphore needed by `ufshcd_async_scan()` while waiting. The current `ufshcd_remove()` entry does not acquire `host_sem` before its first operations, so the earliest join point is compatible with the callback's `down(&hba->host_sem)`.

## 4. Why not use the alternatives

### 4.1 Do not add global `async_synchronize_full()`

The default async domain is global across independent subsystems and devices. A global barrier could wait for unrelated asynchronous probes and lengthen UFS removal unnecessarily. It also creates a broader synchronization side effect than the UFS-owned lifetime requires.

### 4.2 Do not use the default-domain cookie without need

Storing the cookie from `async_schedule()` and calling `async_synchronize_cookie(cookie + 1)` would work for correctness, but that call waits for all default-domain pending jobs submitted before the checkpoint, not only this HBA's callback. The per-HBA registered domain preserves global ordering participation while making the remove join local.

### 4.3 Do not substitute a guessed SCSI barrier

SCSI async scan has its own scan mutex, cancellation/state and host-reference mechanisms. The UFS-owned callback and the SCSI async scan are separate asynchronous lifetimes. The join here is specifically for `ufshcd_async_scan()`; do not add an unrelated global SCSI barrier without a separately proven HBA-memory access path.

## 5. Required checks for the eventual implementation

Before accepting the code:
1. Verify there is exactly one UFS-owned schedule path on the pinned tree and no hidden second call site.
2. Verify all error paths before scheduling leave the private scheduled flag false.
3. Verify OOM/synchronous fallback still stores a valid cookie and the checkpoint returns immediately.
4. Verify remove joins before the first read/mutation of HBA state that may race with `ufshcd_async_scan()`.
5. Verify the callback entry is removed from both pending lists only after `ufshcd_async_scan()` returns.
6. Verify registered-domain participation preserves `async_synchronize_full()` semantics.
7. Verify the private wrapper remains alive until the join completes and until later devres `scsi_host_put`.
8. Keep the existing SCSI async-scan synchronization logic unchanged.
9. Exercise at least these source/model scenarios: callback already complete before remove; callback blocked in `host_sem`; callback in probe; callback in `ufshcd_add_lus()`; synchronous fallback; probe failure before schedule; remove with no scheduled scan.

This report does not authorize a device boot, forced unbind, ADB or hardware operation.

## 6. Relationship to the UFS teardown findings

This async join must happen before the UFS remove sequence reaches:
- Qualcomm variant exit and QMP PHY power-off/exit;
- generic VCC/VCCQ regulator cleanup;
- VDDP managed cleanup actions;
- HBA/SCSI host devres release.

It is independent of the ROUND105/107 regulator load-first teardown correction. Both are necessary: the regulator state machine handles power-vote correctness; the async join guarantees no UFS probe callback continues using that state while remove tears it down.

## 7. Status

- Fixed ACK async-domain cookie semantics: SOURCE-CONFIRMED.
- HBA private wrapper available for per-instance storage: SOURCE-CONFIRMED.
- Current UFS async callback schedule cookie discarded: SOURCE-CONFIRMED.
- Current `ufshcd_remove()` has no early UFS async join: SOURCE-CONFIRMED.
- Proposed per-HBA registered-domain integration: DESIGN READY FOR 2号 AI IMPLEMENTATION.
- Actual patch, apply, checkpatch, compile, failure injection and device remove test: NOT RUN.

No source, patch, binding, DTS, configuration, 2号 AI branch, protected branch, PR or firmware artifact was modified by this report.
