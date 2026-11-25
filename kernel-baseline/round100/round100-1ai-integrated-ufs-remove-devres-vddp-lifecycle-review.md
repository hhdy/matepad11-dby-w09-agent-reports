# ROUND100 — 1AI integrated UFS remove, sidecar and VDDP devres lifecycle review

**Date:** 2026-11-25  
**Task ownership:** 1号 AI（ChatGPT）独立源码审查  
**Implementation owner:** 2号 AI（独立开发 AI）  
**Test executor:** 本地测试 Agent，仅执行另行授权的本地只读/故障注入任务  
**Pinned baseline:** ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Review inputs:** ROUND95–99, ROUND52-0002 draft, ROUND61 Phase A–D evidence  
**Result:** **LIFETIME DESIGN PARTIAL — two separate teardown gates remain open.** The current devres registration order is directionally correct, but it does not join the UFS-owned async callback; the VDDP cleanup action also does not safely resolve all `regulator_disable()` failure states before the managed regulator handle is put.

---

## 1. Executive result

This review combines three lifetimes that must be reasoned about together but must not be conflated:

1. the UFS-owned `ufshcd_async_scan()` callback, which continues to use `struct ufs_hba` after the synchronous probe path returns;
2. the proposed generic UFS VCC sidecar, whose storage is associated with `ufs_hba::android_oem_data1` and is released through device devres;
3. the Qualcomm-specific VDDP REF_CLK regulator handle and custom devres cleanup action in ROUND52-0002.

The following conclusions are independent:

- **UFS async join is mandatory.** The callback must be known complete before HBA/sidecar/rail teardown starts. Reverse devres release order alone is not an asynchronous lifetime barrier.
- **The current VDDP cleanup failure path is incomplete.** A negative return from `regulator_disable()` is ambiguous: the consumer enable count may already have been decremented, or it may still be held because the provider's hardware disable failed first. The custom action's `return` cannot cancel the later `devm_regulator_release()`.
- **The SCSI async scan does not currently require a second global async barrier.** For the pinned driver-template callbacks, its command/probe phase is handled by SCSI's scan mutex and cancellation state; its post-scan reference keeps HBA memory alive. This remains conditional on no new sidecar accesses being added to SCSI finalization callbacks.
- **The existing devres order is useful and should be preserved.** The VDDP cleanup action is registered after `devm_regulator_get()`, so it runs before that regulator handle's managed put. The action also runs after the driver's synchronous remove callback has returned. This ordering is necessary, but not sufficient, for safe teardown.

This is a source-level review only. ROUND100 does not modify a driver patch, does not build or test a kernel, and does not validate physical regulator behavior.

## 2. Build context — distinguish compile success from lifecycle acceptance

The 2号 AI's ROUND61 pipeline has completed a manifest-pinned nine-stage workflow:
- Phase A: real ordered patch application and static checks — PASS;
- Phase B: targeted UFS / QMP UFS PHY binding validation — PASS;
- Phase C: Kleaf target query/cquery — PASS;
- Phase D: `//common:dby_w09` Image build and final config validation — PASS.

The successful run is [45529395645](https://github.com/hhdy/matepad11-dby-w09-agent-reports/actions/runs/45529395645). The resulting Image is 44,820,992 bytes; the final configuration has 33/33 required symbols set to `=y`. The Phase-D report records artifact 14985348694 and independently checked hashes.

The build patch sequence includes the branch-local checkpatch-clean ROUND52-0002 VDDP implementation. The canonical ROUND52-0002 draft has the same blob SHA on `main` and `ai-parallel/stagea-port-until-boot` (`fb34fbc9701bc7e7b56bb9078ee98c0cdd8caf78`). Its logic remains the reviewed disable-before-load-zero sequence. A successful compile proves that this candidate compiles; it does **not** prove regulator teardown is failure-safe.

The generic VCC sidecar proposed in ROUND95/96 and the UFS async join required by ROUND97/98 must not be treated as already integrated merely because the earlier Image build passed. Their final implementation and integration diff still require review.

Phase E remains BLOCKED, Phase F remains BLOCKED, and Phase G remains NOT RUN. No board DTB/boot package or device boot is established by this report.

## 3. Cross-layer lifetime map

### 3.1 Probe and devres registration

The intended registration order, subject to confirmation against the final integrated tree, is:

1. `ufshcd_alloc_host()` allocates the SCSI host/HBA and registers its host-release devres action.
2. `ufshcd_pltfrm_init()` parses generic UFS regulator information before `ufshcd_init()`; a generic UFS sidecar allocated at this stage is therefore registered after the HBA release action and before the Qualcomm variant initialization path.
3. The Qualcomm variant path allocates `struct ufs_qcom_host`.
4. ROUND52-0002 obtains VDDP with `devm_regulator_get()`, then registers `ufs_qcom_vddp_ref_clk_cleanup()` through `devm_add_action_or_reset()`.
5. After UFS initialization, the core schedules `ufshcd_async_scan()` with `async_schedule()`.

The exact final integration must preserve the critical invariants:
- sidecar and completion state are fully initialized before the async callback can be scheduled;
- the VDDP cleanup action is registered after the regulator handle so the action runs before regulator put;
- any data pointer passed to the VDDP cleanup remains alive until that action runs;
- the HBA release action remains later in the reverse-unwind order than any sidecar release.

### 3.2 Remove and asynchronous quiescence

The pinned UFS core schedules `ufshcd_async_scan()` from `ufshcd_init()`. The current source does not retain an async cookie or otherwise join this UFS-owned callback in the remove path.

The callback can still use HBA/device state while it performs `ufshcd_probe_hba()`, logical-unit setup, devfreq/clock-scaling work, WLUN handling and the final runtime-PM put. A remove-side runtime-PM get is not a join for this callback.

**Required order:** before `ufshcd_hba_exit()`, generic regulator teardown, sidecar release, or other destruction that can race with the callback, the implementation must wait for the exact UFS-owned callback to finish. This wait must not hold `hba->host_sem` or another lock that the callback needs.

A per-HBA completion is the preferred first design:
- initialize it before the scheduling point;
- use an explicit scheduled/started state or an initially-complete protocol so probe/remove paths that never schedule the callback do not wait forever;
- cover every callback exit path;
- signal only after the callback's final HBA/device access, including its final runtime-PM operation;
- wait before UFS teardown starts destroying callback-visible state.

An async-cookie design is possible but must obey the pinned API's checkpoint semantics. The callback's returned cookie is its own sequence value; a checkpoint strictly after that value is needed to include it. The global default async domain and unrelated work impact must be documented. Do not substitute `async_synchronize_full()` without a specific need.

### 3.3 SCSI async scan is a separate lifetime

ROUND98 refined the ROUND97 distinction:
- the UFS-owned callback exists before the SCSI scanner is even submitted;
- the SCSI scan command/probe phase is serialized by the host's `scan_mutex`;
- `scsi_remove_host()` takes that mutex and moves the host to `SHOST_CANCEL`;
- scans entering later are rejected by `scsi_host_scan_allowed()`;
- an async scan's SCSI-host reference keeps the embedded HBA memory alive until `scsi_host_put()`;
- a post-scan finalization tail may continue after the scan mutex is released, but the currently pinned `ufshcd_sdev_destroy()` callback does not dereference the proposed VCC sidecar.

Accordingly, for the current pinned callback set, join the UFS-owned callback and retain normal `scsi_remove_host()` ordering. Do **not** add an indiscriminate global SCSI/async wait. Re-review if any future implementation adds sidecar access to `ufshcd_sdev_destroy()`, SCSI host teardown, or post-scan finalization.

## 4. Devres reverse-unwind order

With the registration order above, the intended device devres release sequence is approximately:

1. `ufs_qcom_vddp_ref_clk_cleanup()` custom action;
2. managed VDDP regulator-handle release (`devm_regulator_release()`);
3. Qualcomm variant host memory release, if registered before the VDDP handle/action;
4. generic UFS sidecar memory release;
5. HBA/SCSI-host release action registered by `ufshcd_alloc_host()`.

The exact middle ordering must be checked in the final integrated tree, but two lifetime rules are clear:

- The custom VDDP action must run while its `struct ufs_qcom_host` data remains valid and before its regulator handle is put.
- The generic sidecar must not be freed until the UFS async callback has been joined and all synchronous UFS users have stopped. Its being freed before the HBA object is not itself proof that an async callback has stopped.

On ordinary consumer-first remove, the core's synchronous `ufshcd_remove()` path performs generic UFS/HBA shutdown before device devres release begins. This is the intended point at which generic VCCQ has been shut down before the later VDDP action runs. It must be confirmed against the final patch sequence and failure unwind paths, not assumed from comments alone.

## 5. ROUND52-0002 VDDP cleanup — exact unresolved error states

The current cleanup action is effectively:

```c
if (host->vddp_ref_clk_enabled) {
        ret = regulator_disable(host->vddp_ref_clk);
        if (ret)
                return;
        host->vddp_ref_clk_enabled = false;
}

if (host->vddp_ref_clk_load_set) {
        ret = regulator_set_load(host->vddp_ref_clk, 0);
        ...
}
```

This has two separate problems.

### 5.1 Negative disable return does not identify the consumer reference state

Pinned regulator-core behavior distinguishes at least two failure locations:

- A provider hardware `.disable()` failure can be returned before the consumer's enable count is decremented. The consumer reference may still be active.
- A later operation such as the DRMS update in `_regulator_handle_consumer_disable()` can fail after the consumer enable count has already been decremented. The call still returns a negative value, but the reference may already be gone.

Therefore the current `if (ret) return;` leaves software flags stale in the post-decrement case, skips load cleanup, and cannot safely infer that a retry is appropriate.

### 5.2 The custom action cannot veto managed regulator put

`devm_regulator_get()` registers its own managed release action. The custom cleanup action is registered later, so it correctly runs first. However, a `return` from this custom void action does not remove or cancel the later `devm_regulator_release()`.

The regulator core's `_regulator_put()` warns if the consumer handle still has a non-zero `enable_count`; destroying the handle does not balance the outstanding enable reference or repair the regulator provider's use count. Thus a true pre-decrement hardware-disable failure can still reach a managed put with an active consumer reference.

### 5.3 L6 makes the DRMS case relevant

ROUND87/90/99 identify PM8150 L6 as a DRMS-capable PMIC5 NLDO:
- UFS VCCQ is one L6 consumer with an 800-mA load request;
- VDDP REF_CLK is another L6 consumer with a 100-uA request;
- the L6 HPM threshold is 30 mA.

This is a shared-regulator case. Do not use `regulator_force_disable()` without proof that no other consumer depends on L6.

### 5.4 Safer ordering candidate and remaining policy

The source-reviewed candidate remains:
1. while the VDDP enable reference is still held, request `regulator_set_load(vddp, 0)`;
2. if this fails, the regulator core restores the old load request and the consumer reference remains held; report the error and follow an explicit policy;
3. if load-zero succeeds, call `regulator_disable()`;
4. if a pre-decrement provider disable failure occurs, the reference remains held and the implementation must define how the original load/state is restored and how the handle's eventual release is made safe;
5. audit any other possible negative post-decrement paths (coupling/parent operations) in the exact pinned core before inferring reference state from the return code.

Load-zero-before-disable removes the known non-zero-load DRMS transition from the later disable call, but it does not magically make a provider hardware-disable failure disappear. It is not yet a complete lifecycle fix by itself.

Do not:
- treat every negative `regulator_disable()` result as a still-held reference;
- blindly retry `regulator_disable()` after an ambiguous negative result;
- force-disable shared L6;
- claim that a void devres action can prevent managed regulator put;
- silently leave a managed handle pointing at freed consumer-device state.

A different handle-ownership strategy (for example, non-managed acquisition with an explicit release policy) would require its own rigorous device-lifetime and failure-path design. Simply replacing `devm_regulator_get()` is not a fix unless it prevents both use-after-free and regulator-core reference inconsistency.

## 6. Required implementation closure for 2号 AI

Before the current built candidate can be treated as lifecycle-reviewed for device testing, 2号 AI should:

1. Add a per-HBA UFS async completion/join or a fully documented cookie checkpoint, initialized before scheduling and waited before teardown.
2. Ensure every UFS async callback exit reaches the completion point only after its final HBA/device access.
3. Keep SCSI scan cancellation/reference handling separate; do not add an unnecessary global async barrier.
4. Keep the VCC sidecar allocation before `ufshcd_init()` can schedule work; verify the OEM slot is enabled by the final config and has no competing consumer in the complete integration tree.
5. Rework ROUND52-0002 cleanup around load-zero-before-disable and explicitly design the provider-disable-failure/managed-put policy.
6. Track voltage request, DRMS load and enable-reference state independently. Do not collapse them into one boolean.
7. Add source-model/failure-injection cases for: load-zero failure; successful load-zero + successful disable; provider hardware-disable failure before decrement; possible post-decrement coupling/parent failure; shared L6 with another consumer; and probe failure after load set but before enable success.
8. Submit the complete integration diff for independent 1号 AI review before any DTB/boot package or device validation gate is advanced.

Task ownership remains separated: the above is a **2号 AI implementation list**. A local Agent may run only a separately written **测试 Agent** task, and must not become the implementer or be described as 2号 AI.

## 7. Current project gates and evidence boundary

| Gate | State | ROUND100 interpretation |
|---|---|---|
| Phase A — real patch application | PASS | Hosted-runner source patch application and strict static checks |
| Phase B — targeted binding validation | PASS | UFS / QMP PHY targeted schema validation |
| Phase C — Kleaf target validation | PASS | Pinned manifest/toolchain and Bazel query/cquery |
| Phase D — Image build | PASS | ARM64 Image, System.map, vmlinux and 33/33 config checks |
| Phase E — board DTS / memory / power | BLOCKED | Final ABL FDT/memory handoff and physical PM8150 input topology missing |
| Phase F — boot package / DTBO / AVB | BLOCKED | ABL DTBO selection/boot path and vbmeta_cust provenance/descriptor coverage unresolved |
| Phase G — device validation | NOT RUN | No device boot, flash or hardware test |

ROUND100 itself:
- did not alter any patch, DTS, binding, Kconfig, fragment, workflow or source branch;
- did not change `main`'s source-code implementation;
- did not run a new compile, checkpatch, dt-schema, Kleaf, runtime regulator test or device operation;
- does not close any Phase E/F/G gate.

## 8. Related reports

- [ROUND95 — KMI-safe UFS sidecar review](../round95/)
- [ROUND97 — UFS async scan teardown review](round97-1ai-ufs-async-scan-teardown-review.md)
- [ROUND98 — UFS versus SCSI async lifetime review](../round98/round98-1ai-ufs-versus-scsi-async-lifetime-review.md)
- [ROUND99 — VDDP DRMS and devres cleanup review](../round99/round99-1ai-vddp-regulator-disable-and-devres-cleanup-review.md)
- [ROUND61 Phase D — actual Image build report](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai-parallel/stagea-port-until-boot/kernel-baseline/round61/phase-d-kconfig-and-image-build.md)
- [ROUND61 Phase G — device validation entry gates](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai-parallel/stagea-port-until-boot/kernel-baseline/round61/phase-g-device-validation.md)

**Final verdict:** the current devres registration order is a valid foundation, but it must not be mistaken for an async join or a failure-safe VDDP cleanup policy. Keep UFS async quiescence and VDDP consumer-reference/error handling as two explicit implementation gates. The compiled Image is a real build milestone, not a device-ready boot candidate.
