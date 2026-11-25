# ROUND99 — 1号 AI review: ROUND52 VDDP cleanup must account for post-decrement DRMS errors and devm regulator_put

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, under a separate taskbook  
**Pinned baseline:** ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Related reviews:** ROUND49, ROUND52, ROUND87, ROUND90, ROUND93

## 1. Executive result

A fixed-source recheck found an unresolved VDDP teardown edge in the ROUND52-0002 draft.

The draft's `ufs_qcom_vddp_ref_clk_cleanup()` currently does:

1. If `vddp_ref_clk_enabled`, call `regulator_disable()`.
2. On **any** negative return, log and immediately return.
3. Only after successful disable, call `regulator_set_load(..., 0)`.
4. The regulator was obtained with `devm_regulator_get()`; its automatic devres release later calls `regulator_put()` regardless of the custom action's logged error.

ROUND90 established that `regulator_disable()` can return a negative DRMS error **after** the consumer enable count has already been decremented. A different class of failure, such as the regulator provider's hardware `.disable()` returning an error, can occur **before** that decrement. The caller receives a negative result in both cases and cannot infer the consumer reference state from the return code alone.

This matters for VDDP because the PM8150 L6 provider is DRMS-capable and VDDP retains a 100-uA vote. The correct cleanup ordering must be reviewed together with ROUND90; the current “disable, then set load zero” order leaves the known post-decrement DRMS failure path in place.

**Verdict:** ROUND52-0002 is a source-reviewed draft, not a teardown-complete implementation. 2号 AI should revise/review its L6 load-zero ordering and explicitly document the remaining true hardware-disable failure policy before adopting it.

## 2. Exact ROUND52-0002 cleanup sequence

Current patch artifact:
`kernel-baseline/round52/0002-ufs-qcom-sm8250-vddp-refclk-managed-lifecycle.patch.draft`

Current blob SHA: `fb34fbc9701bc7e7b56bb9078ee98c0cdd8caf78`.

The cleanup callback in this exact artifact:

- calls `regulator_disable(host->vddp_ref_clk)` while the 100-uA VDDP load vote is still set;
- if the call returns nonzero, it logs and returns without clearing the load vote;
- only on return 0 does it clear `vddp_ref_clk_enabled` and then request load zero.

The same patch registers this cleanup action after `devm_regulator_get()`, as required for reverse-order devres execution. Therefore the custom cleanup action is followed by the devm regulator release action.

## 3. Exact pinned ACK regulator-core behavior

### 3.1 Disable can fail before or after consumer enable-count decrement

Pinned source: `drivers/regulator/core.c`.

The relevant sequence in `_regulator_disable()` is:

1. For a last user with status-change permission, call the provider's `_regulator_do_disable()`.
2. If the provider's `.disable()` operation returns a negative error, return immediately. At this point the consumer's `enable_count` has **not** been decremented.
3. If the provider disable succeeds, update `rdev->use_count`.
4. Call `_regulator_handle_consumer_disable()`.
5. That helper decrements `regulator->enable_count` first, then calls `drms_uA_update()` if this was the final enable reference and the consumer still has a non-zero `uA_load`.
6. If the DRMS update fails, that negative error is returned even though the enable count has already reached zero.

The same post-decrement ambiguity can arise when other consumers keep the regulator enabled: `use_count` is decremented, then the consumer count is decremented, and a subsequent DRMS update can fail.

This is the precise reason that a caller must not interpret every negative `regulator_disable()` result as “the enable reference remains held”.

### 3.2 regulator_put requires a balanced consumer reference

Pinned source: `drivers/regulator/core.c`.

- `_regulator_put()` executes `WARN_ON(regulator->enable_count)` before destroying the consumer handle.
- `destroy_regulator()` removes the handle from the consumer list and frees it; it does not perform the missing consumer disable or repair `rdev->use_count`.
- Consequently, if the provider hardware disable fails before the consumer count is decremented, a later `regulator_put()` warns and the regulator core can retain an inconsistent use count.

### 3.3 devm_regulator_get always puts the handle after the custom action

Pinned source: `drivers/regulator/devres.c`.

- `devm_regulator_get()` registers `devm_regulator_release()`, which calls `regulator_put()`.
- ROUND52 registers `ufs_qcom_vddp_ref_clk_cleanup()` after that get.
- Devres LIFO means the custom cleanup runs first, followed by the earlier `devm_regulator_release()`.
- A `return` from the custom void action does not cancel or veto the later regulator-put action.

This confirms that the cleanup callback cannot simply return on a disable error and assume that the enabled handle will remain managed.

## 4. Why L6 is a real trigger, not a theoretical DRMS example

Pinned ACK PM8150 data and the DBY-W09 candidate (ROUND87/90):

- PM8150 L6 is a PMIC5 NLDO with DRMS mode-selection support.
- Its HPM threshold is 30 mA.
- UFS VCCQ is a separate consumer of the same L6 regulator with an 800-mA load request.
- VDDP REF_CLK is another separate L6 consumer with a 100-uA load request.

ROUND52 holds VDDP enabled for the bound lifetime and shuts it down from its custom devres action. The normal UFS remove path shuts down generic VCCQ before that action runs.

With VCCQ already removed, VDDP may be the remaining active UFS consumer. Its 100-uA load is below the 30-mA HPM threshold. When VDDP is disabled, the aggregate load can fall again, so the provider's mode update is on the exact path ROUND90 identified.

The current draft can therefore see a post-decrement DRMS error during VDDP cleanup. In that case its `enabled` flag remains true even though the regulator core's consumer enable count may already be zero; the subsequent managed put will not warn for that particular case, but the callback has misclassified the reference result and skipped load cleanup.

If instead the provider's actual hardware disable fails before the consumer-count decrement, the managed put later sees a nonzero enable count, warns, and destroys the handle without balancing the use count.

## 5. Required design review for 2号 AI

### 5.1 Re-evaluate VDDP load-zero ordering

For the same reason as ROUND90's generic UFS L6 recommendation, evaluate this order while the VDDP consumer reference is still held:

1. Call `regulator_set_load(vddp, 0)`.
2. If it fails, ACK regulator core restores the previous stored load; do not assume the consumer load vote changed.
3. If it succeeds, call `regulator_disable(vddp)`.
4. Track load state and enable-reference state separately; do not set the VDDP enabled flag false until the relevant reference transition has been established.

On a currently enabled consumer, `regulator_set_load(0)` runs DRMS immediately. A DRMS failure is therefore returned while the consumer's enable reference remains held and the regulator core restores the old stored load. This avoids relying on the post-decrement DRMS transition inside `regulator_disable()`.

The VDDP cleanup is a one-shot unbind path, not a runtime suspend path; this order must be assessed in that context. A successful load-zero request can move L6 to LPM before the regulator is disabled. Confirm that this happens only after generic UFS VCCQ has been shut down and the UFS host has exited active operation.

### 5.2 Do not claim that load-zero solves a true provider-disable failure

Even after a successful load-zero request, the provider's actual `.disable()` operation can fail before the consumer count is decremented. In that case the consumer reference can remain held.

The fixed devm sequence will still later execute `regulator_put()`. The current cleanup design has no way to veto that release or to report a recoverable remove error through its void devres action.

2号 AI must explicitly decide and document how this exceptional failure is handled. Do not:
- call `regulator_force_disable()` without proving no other consumer depends on L6;
- blindly retry `regulator_disable()` after an ambiguous negative return, because a post-decrement DRMS failure can mean the reference was already released;
- claim that a failed `regulator_disable()` always leaves the consumer enabled;
- claim that successful load-zero guarantees the hardware disable cannot fail.

If the implementation keeps `devm_regulator_get()`, document the remaining provider-disable-failure limitation and the resulting regulator-core warning risk. A different ownership strategy would need its own lifetime/device-link analysis; it must not leave a handle pointing at a freed consumer device.

### 5.3 Keep the failure states separate

The VDDP path must distinguish at minimum:
- load vote stored as ON / ZERO;
- regulator enable reference acquired / released / uncertain after a failed operation;
- cleanup error and the exact failing step;
- whether the devm regulator-put action will still run.

Do not reuse the VCC Sidecar booleans for this separate VDDP handle unless their ownership and release ordering are explicitly unified. ROUND96's UFS HBA sidecar is not the same object as the Qualcomm variant's `ufs_qcom_host`.

## 6. Required tests / evidence before acceptance

2号 AI should add a focused test or a source-backed failure-injection plan for:

1. VDDP load-zero succeeds, provider disable succeeds, then regulator put: no warning and consumer reference balanced.
2. VDDP load-zero DRMS update fails: old 100-uA vote remains stored and enable reference is still held; the cleanup policy is observable.
3. Provider `.disable()` fails before consumer-count decrement: prove how devm regulator release is handled and whether `regulator_put()` would warn.
4. A post-decrement DRMS failure is not misreported as a still-held enable reference.
5. Generic UFS VCCQ is already shut down before VDDP cleanup begins.
6. No action force-disables shared PM8150 L6 while another consumer still owns it.

The test report must distinguish source-model behavior, injected failure behavior and real hardware behavior. Do not infer a successful physical disable from a source-level return-path analysis.

## 7. Evidence references

All ACK source references below use commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.

- ROUND52 VDDP patch: `kernel-baseline/round52/0002-ufs-qcom-sm8250-vddp-refclk-managed-lifecycle.patch.draft`.
- `drivers/regulator/core.c`: `_regulator_handle_consumer_disable()`, `_regulator_disable()`, `regulator_disable()`, `_regulator_put()`, `destroy_regulator()`, and `regulator_set_load()`.
- `drivers/regulator/devres.c`: `devm_regulator_release()`, `_devm_regulator_get()`, `devm_regulator_get()`, and `devm_regulator_put()`.
- ROUND87: PM8150 L17/L6 DRMS thresholds and UFS load consumers.
- ROUND90: post-decrement DRMS failure and load-zero-before-disable candidate.
- ROUND52: VDDP managed-handle/action order and generic VCCQ-before-VDDP teardown.

## 8. Scope and verdict

- Read-only review of the exact ROUND52 patch artifact and fixed ACK regulator-core/devres sources.
- No source, DTS, binding, patch, Kconfig, `.config`, Image, AI2 branch, protected DTS branch or PR was modified.
- No patch application, compiler, Kleaf build, KMI check, schema validation, runtime fault injection, electrical measurement or device operation was run.

**Final verdict:** ROUND52's VDDP cleanup order is not yet reconciled with ROUND90's regulator-core failure semantics. The intended storage-first VDDP design remains viable, but its unbind/error cleanup is not yet fully reviewed. Keep VDDP L6 cleanup as an explicit AI2 implementation gate; do not mark this path lifecycle-complete based solely on the current source-review patch draft.
