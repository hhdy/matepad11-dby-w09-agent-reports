# ROUND101 — 1号 AI：固定 ACK UFS async-cookie join 方案与 VDDP disable 错误边界

**Date:** 2026-11-25  
**Task ownership:** 1号 AI（ChatGPT）独立固定源码审查  
**Implementation owner:** 2号 AI（独立开发 AI）  
**Test executor:** 本地测试 Agent，仅运行另行授权的测试任务  
**Pinned baseline:** ACK android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Related:** ROUND95–100  
**Result:** **UFS async join now has a simpler exact-source implementation candidate: capture the existing async cookie and synchronize at cookie + 1. VDDP load-zero-before-disable remains the best ordinary-path ordering, but a provider disable failure is not fully recoverable through the current consumer API and must remain an explicit exceptional teardown limitation.**

---

## 1. Executive result

This report re-opened the exact pinned ACK files from the aosp-mirror/kernel_common mirror at the immutable commit above. It resolves an implementation choice that ROUND97/98 had left between a per-HBA completion and async-cookie synchronization.

**Preferred UFS join candidate:** preserve the current async_schedule(ufshcd_async_scan, hba) submission, save its returned async_cookie_t in the already-planned HBA sidecar, and call async_synchronize_cookie(cookie + 1) at the very beginning of ufshcd_remove(), before any HBA teardown.

This is stronger and simpler than making ufshcd_async_scan() signal a completion:
- the callback does not need to touch the sidecar at exit;
- the waiter is released only after the async framework has observed the callback function return and removed its entry from the pending queue;
- the callback's final runtime-PM put and error log are covered;
- a synchronous fallback from async_schedule_node_domain() is also safe;
- no UFS KMI-visible structure needs to grow if the cookie is stored in the existing OEM-slot sidecar.

This method uses the default async domain. It waits for any still-pending default-domain callbacks submitted before the checkpoint, not only this UFS callback; it does not wait for work submitted after the checkpoint. That bounded-prefix side effect must be documented. It is not an async_synchronize_full() global drain.

For VDDP, moving regulator_set_load(vddp, 0) before regulator_disable(vddp) removes the known final-consumer DRMS error caused by disabling with a non-zero load. It does not make every possible negative disable result unambiguous: regulator-core notifier / provider-disable errors can occur before consumer reference decrement, while coupled-voltage / parent-supply failures can occur after it. The current API returns only an integer and exposes no supported consumer enable-count query. Do not blindly retry or force-disable shared L6.

---

## 2. Exact pinned source identities

All source blobs below were fetched at ACK commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a:

| File | Blob SHA |
|---|---|
| include/linux/async.h | 19b778d08600f1d1e1bf25a8cd0e8a390b39cac5 |
| kernel/async.c | 4c3e6a44595fa176f06108c869d164cca26546a1 |
| drivers/ufs/core/ufshcd.c | 2cf7aa8e0a9472f9024d4251ac2f9d7da830e219 |
| drivers/regulator/core.c | 39d317ad73a33c4aa27e179cc436d8bf4daf5bcc |
| drivers/regulator/devres.c | 2cf03042fddf4263d05c95e29dd534003fb8246c |
| include/ufs/ufshcd.h | ee5c1c607237d5eaf743d4a267a760c1e0efcf97 |
| drivers/android/Kconfig | 8b498ee93256a7fdc09d5bab07c3e907c135ae9e |

Mirror URLs:
- [Pinned async.h](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/linux/async.h)
- [Pinned async.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/kernel/async.c)
- [Pinned ufshcd.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c)
- [Pinned regulator core](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c)
- [Pinned regulator devres](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/devres.c)

---

## 3. Exact async-cookie semantics in this ACK

### 3.1 API contract

Pinned include/linux/async.h:
- async_cookie_t is u64 (line 16).
- async_schedule() returns an async_cookie_t (approximately lines 52–56).
- async_synchronize_cookie() is declared (approximately line 118).
- async_schedule_domain() and async_synchronize_cookie_domain() exist, but are not needed for the minimal candidate.

Pinned kernel/async.c:
- next_cookie starts at 1 (line 31).
- async_schedule_node_domain() assigns newcookie = next_cookie++, places the work in the domain pending list, queues it, and returns the cookie (approximately lines 200–231).
- If allocation fails or the async queue is overloaded, it calls func(data, newcookie) synchronously and returns the cookie after the function has returned (approximately lines 200–217).
- async_synchronize_cookie_domain(cookie, domain) waits until lowest_in_progress(domain) >= cookie (approximately lines 310–320).
- async_synchronize_cookie(cookie) uses the default async domain (approximately lines 322–326).
- The framework's async_run_entry_fn() invokes entry->func(), then removes the entry from the pending queues, frees the entry, and only then wakes waiters (approximately lines 117–150).

The documented semantic is strict: synchronize functions submitted **prior to** the checkpoint cookie. If the UFS callback's own cookie is C, waiting at C does not include the still-pending entry C; waiting at C + 1 does.

The framework removes the pending entry only after ufshcd_async_scan() has fully returned. Therefore the C + 1 checkpoint does not merely wait for an early completion signal; it covers the entire callback return.

### 3.2 Exact UFS call sites

Pinned drivers/ufs/core/ufshcd.c:
- ufshcd_async_scan() is at lines 9360–9378.
- ufshcd_init() submits it at line 11190 using async_schedule(ufshcd_async_scan, hba); the returned cookie is currently discarded.
- ufshcd_remove() starts at line 10716. It currently begins with the optional ufshcd_rpm_get_sync(hba), followed by hwmon/BSG/sysfs/workqueue/SCSI/HBA teardown. There is no UFS-cookie join before those operations.

The async callback:
1. takes hba->host_sem;
2. calls ufshcd_probe_hba(hba, true);
3. processes the probe result and releases host_sem;
4. if successful, calls ufshcd_add_lus(hba);
5. calls pm_runtime_put_sync(hba->dev);
6. may log an error via hba->dev;
7. returns to async_run_entry_fn(), which then removes the async entry.

ufshcd_add_lus() schedules the SCSI host scan only after UFS WLUN/devfreq/clock-scaling work. The UFS callback cookie and the later SCSI async scan cookie are distinct; the later SCSI worker is not included by waiting only through C + 1.

### 3.3 Recommended implementation candidate for 2号 AI

Use the generic lifecycle sidecar that ROUND95/96 already propose. It must be allocated and initialized before ufshcd_init() can reach line 11190. Add only private sidecar fields, for example:
- async_cookie_t async_scan_cookie;
- bool async_scan_cookie_valid.

At the existing submission point, capture the return value:

    sidecar->async_scan_cookie = async_schedule(ufshcd_async_scan, hba);
    sidecar->async_scan_cookie_valid = true;

At the very beginning of ufshcd_remove(), before ufshcd_rpm_get_sync(), sysfs removal, work cancellation, SCSI teardown, interrupt stop, or ufshcd_hba_exit():

    if (sidecar && sidecar->async_scan_cookie_valid) {
            async_synchronize_cookie(sidecar->async_scan_cookie + 1);
            sidecar->async_scan_cookie_valid = false;
    }

This is a design sketch, not an applied patch. The final code must use the project's reviewed sidecar accessor and error/path guards.

Required invariants:
- sidecar pointer and cookie fields are initialized before the schedule call;
- the cookie is stored before the synchronous probe path can return and the driver core can begin remove;
- every path that schedules ufshcd_async_scan() has a valid join token before teardown;
- zero may be used as an initial invalid cookie because the pinned sequence begins at 1, but a separate validity boolean is clearer;
- the async callback itself should not dereference the sidecar or signal a completion;
- the wait is before all HBA teardown, and must not hold hba->host_sem or any lock needed by the callback;
- the sidecar is freed only after this join and normal synchronous teardown;
- retain normal scsi_remove_host() cancellation/reference handling; do not add a global SCSI barrier.

Do not replace this with async_synchronize_cookie(C): the pinned comparison is strict and that checkpoint excludes the callback with cookie C.

### 3.4 Scope and default-domain side effect

The existing UFS call uses async_schedule(), hence the default async domain. Using async_synchronize_cookie(C + 1) waits for all still-pending default-domain entries submitted before that checkpoint, including any earlier callbacks from other subsystems. It does not wait for later entries such as the SCSI scan submitted by this UFS callback after cookie C.

This is a bounded prefix barrier, not a full global drain. For the first implementation, preserving the existing default-domain scheduling behavior is preferable to introducing a new domain, changing global boot-order participation, or adding domain lifetime/unregister complexity. If the extra prefix wait is later shown to be unacceptable, a separately reviewed per-UFS registered-domain design can be considered; do not introduce an exclusive domain without checking async_synchronize_full() ordering expectations.

### 3.5 Why this supersedes the completion-first preference

ROUND98 preferred a per-HBA completion over a cookie because it avoids waiting unrelated default-domain work. Exact pinned implementation review now shows a concrete advantage for the cookie method:
- the async framework's own pending-list removal occurs only after the callback function returns;
- the callback therefore does not need to touch sidecar memory at its final instruction;
- no completion-object wake/free race or callback-side completion protocol needs to be designed;
- the code changes are limited to capturing a cookie and adding an early remove barrier.

This is a refined recommendation, not a claim that the existing driver already contains the fix.

---

## 4. Sidecar and KMI placement conditions

Pinned include/ufs/ufshcd.h ends struct ufs_hba with ANDROID_OEM_DATA(1) at line 1299. Pinned drivers/android/Kconfig defines CONFIG_ANDROID_VENDOR_OEM_DATA with depends on 64BIT and default y.

ROUND95 establishes that the existing final .config must still be checked and that the OEM field must have no competing project consumer. Do not add a member to struct ufs_hba, struct ufs_vreg, or struct ufs_hba_variant_ops merely to hold the cookie. Use the already-planned sidecar only if:
- the final build's CONFIG_ANDROID_VENDOR_OEM_DATA=y;
- the pointer conversion/storage is explicitly 64-bit-safe;
- a complete integration-tree search confirms the OEM slot is unused;
- the sidecar is available on every relevant UFS path that schedules the callback.

If the sidecar is currently allocated only when a board-specific VCC property is present, 2号 AI must make the lifecycle token available on the DBY-W09 path unconditionally before scheduling. Do not silently skip the join when an optional voltage property is absent.

---

## 5. VDDP REF_CLK cleanup — pinned regulator-core error boundary

### 5.1 Exact code behavior

Pinned drivers/regulator/core.c:
- _regulator_handle_consumer_disable() at lines 2879 onward decrements regulator->enable_count first, then calls drms_uA_update() only if the consumer still has a non-zero load and its count reached zero.
- _regulator_disable() at lines 3019 onward can return before decrement if the PRE_DISABLE notifier rejects the operation or the provider's _regulator_do_disable() fails.
- Once the early hardware-disable part succeeds, it calls _regulator_handle_consumer_disable(); then, if applicable, may call regulator_balance_voltage(); then, if the provider use count reaches zero and it has a parent supply, it can call _regulator_disable(rdev->supply).
- _regulator_put() at lines 2444 onward performs WARN_ON(regulator->enable_count) and destroys the consumer handle; it does not balance an outstanding enable reference.
Pinned drivers/regulator/devres.c:
- devm_regulator_get() registers devm_regulator_release(), which later calls regulator_put().
- The custom cleanup action registered after the get runs before managed put, but its return cannot cancel that later managed release.

### 5.2 Normal-path ordering

For the PM8150 L6 shared-consumer scenario already documented in ROUND87/90/99, the candidate ordering should be:

1. UFS core remove shuts down generic UFS VCCQ first.
2. VDDP cleanup requests regulator_set_load(vddp, 0) while the VDDP enable reference is still held.
3. Only if load-zero succeeds does it call regulator_disable(vddp).
4. The software flags for load and enable are updated independently and only when the corresponding state transition is known to have succeeded.

While a consumer is enabled, the pinned regulator_set_load() updates the load then performs DRMS; if DRMS fails, the regulator core restores the old uA_load. Thus a load-zero failure leaves the old load and enable reference active. Do not clear the software load flag on that failure.

This ordering removes the known non-zero-load DRMS failure from the normal regulator_disable() path.

### 5.3 Remaining ambiguity after load-zero

Even after successful regulator_set_load(0), a negative regulator_disable() result can arise:
- **before consumer count decrement:** PRE_DISABLE notifier rejection or provider hardware .disable() failure; the consumer reference may still be held, so the subsequent managed put can warn;
- **after consumer count decrement:** coupled-voltage balancing or parent-supply disable failure; the consumer reference may already be released, so retrying disable can underflow.

The return value is not enough to infer which state occurred. regulator_is_enabled() is a provider-state observation and is not a reliable query of this consumer handle's enable count when the rail is shared. The current public consumer API has no supported way to inspect that per-handle count.

Therefore:
- never blindly retry after a negative disable;
- never call regulator_force_disable() on shared PM8150 L6 without proving no other consumer depends on it;
- do not assume a custom devres action can veto devm_regulator_release();
- retain an explicit documented error limitation and targeted failure-injection plan;
- keep this exceptional provider-disable failure open until the final regulator ownership/error policy is reviewed.

A complete fix for the pre-decrement provider failure would require a policy that keeps a valid consumer handle and its owner lifetime until a later successful balance/release, or an independently justified regulator-core/API change. Simply replacing devm_regulator_get() with regulator_get() does not solve the state ambiguity or owner lifetime by itself.

### 5.4 PM8150 L6 provider implementation — what is confirmed and what is not

The exact pinned Qualcomm RPMh regulator provider adds an important refinement. Source blob:
- drivers/regulator/qcom-rpmh-regulator.c SHA: 109f0aae09b1df431d2e14d45a64d115e87cdec4
- [Pinned Qualcomm RPMh regulator provider](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c)

Verified in that source:
- PM8150 LDO6 is registered in pm8150_vreg_data at line 996 as pmic5_nldo with supply_name "vdd-l6-l9".
- pmic5_nldo at lines 771–781 uses rpmh_regulator_vrm_drms_ops and has hpm_min_load_uA = 30000.
- rpmh_regulator_vrm_drms_ops contains the .disable callback; rpmh_regulator_disable() at lines 259–262 calls rpmh_regulator_set_enable_state(rdev, false).
- rpmh_regulator_set_enable_state() passes the enable boolean into rpmh_regulator_send_request(). For disable, wait_for_ack is false. rpmh_regulator_send_request() at lines 163–174 uses rpmh_write_async() unless qcom,always-wait-for-ack is set on the regulator node; that property is read at lines 460–461.
- The provider installs rdesc.supply_name from the LDO6 table at line 447. Therefore a regulator-core parent-supply relationship can exist if the actual PMIC regulator node provides the corresponding vdd-l6-l9-supply link.

Implications:
1. A negative provider .disable return before consumer-count decrement is possible at least from RPMh request-submission failure. If qcom,always-wait-for-ack is enabled, the disable path can additionally wait for and report the RPMh acknowledgement result. Do not assume the HOS4.3 PMIC regulator node has that property until its exact FDT content is checked.
2. In the default no-ACK path, the provider submits the disable asynchronously. A successful return means the RPMh request was accepted by the asynchronous path; it is not proof that a later remote hardware action has been observed synchronously by this consumer.
3. The LDO6 descriptor names a candidate parent supply, vdd-l6-l9, but this does not identify the physical upstream rail by itself. The matching supply link in the actual DBY-W09/HOS4.3 regulator node and its resolved phandle are still required before claiming a parent-supply disable failure is an actual board path.
4. Consequently, load-zero-before-disable remains correct for the DRMS transition. The pre-decrement submission/notifier path remains a real source-code possibility. The post-decrement parent-supply path is possible in regulator core but is not proven to be wired on this specific tablet until the FDT parent relation is resolved.

Do not infer the board's physical parent for L6 from the string "vdd-l6-l9"; it is a regulator-provider supply name, not a verified schematic net name. The HOS4.3 final PMIC input topology remains a Phase-E evidence requirement.

### 5.5 Required focused cases


2号 AI should add a source-backed test/failure-injection plan that distinguishes:
1. VDDP load-zero succeeds and disable succeeds;
2. VDDP load-zero fails, old load is restored, reference remains held;
3. provider hardware disable fails before decrement;
4. coupled-voltage or parent-supply operation fails after the consumer decrement;
5. the UFS VCCQ consumer has already released its own shared L6 vote;
6. probe fails after load set but before enable succeeds.

Do not label this a real regulator hardware test unless it was actually run on hardware.

---

## 6. Project status and ownership

Current verified 2号 AI branch head remains 44121bbfc17039e1ae838bf4b090d0f0d8f230ea (ROUND29 task assignment). No new UFS async-cookie or VDDP implementation commit was present at the time of this review. The ROUND29 taskbook is assigned to 2号 AI with the local Agent as executor; its report had not yet appeared at the time of this check.

Phase A–D remain PASS, including the successful Image build recorded in [ROUND61 Phase D](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai-parallel/stagea-port-until-boot/kernel-baseline/round61/phase-d-kconfig-and-image-build.md). Phase E/F remain BLOCKED and Phase G NOT RUN. No board DTB/boot package or device operation is authorized by ROUND101.

Ownership boundaries:
- **1号 AI:** source/API analysis and independent review — this report.
- **2号 AI:** implement async-cookie join and VDDP cleanup/error-state changes on its development branch.
- **测试 Agent:** only run a separately authorized validation/failure-injection task; not implementation owner.

ROUND101 changes no kernel source, patch, DTS, binding, config, workflow, build artifact, protected branch or PR.

**Final verdict:** for UFS teardown, prefer the exact pinned ACK cookie checkpoint async_synchronize_cookie(C + 1) over a hand-built completion; it waits until the callback itself has returned. For VDDP, load-zero-before-disable improves the normal path, but the remaining provider-disable failure cannot be declared solved by that ordering alone. Keep both implementation/review gates explicit.
