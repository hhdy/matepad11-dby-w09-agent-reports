# ROUND105 — 1号 AI: UFS QMP/VDDP load-first teardown contract after ROUND103

**Date:** 2026-11-25  
**Owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Testing Agent role:** read-only evidence / test execution only; not a kernel patch author  
**Pinned ACK:** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Scope:** source-level reconciliation of regulator-core disable ordering, ROUND103 L6 FDT evidence, ROUND52 VDDP cleanup and ROUND63 QMP UFS PHY cleanup. No source or development branch was modified.

## 1. Result

The Stage-A candidate contains two related teardown defects which must be corrected by 2号 AI before the UFS regulator lifecycle can be called complete:

1. **VDDP on PM8150 L6:** the current ROUND52 cleanup calls `regulator_disable()` while the 100µA load is still set, then clears the load afterwards. This preserves the exact post-decrement DRMS failure path already identified in ROUND90/99/100. It must clear the load first and abort the disable if that operation fails.
2. **QMP PHY vdda-phy on PM8150 L5:** the current ROUND63 cleanup requests load zero, but proceeds to `regulator_disable()` even when load-zero failed; it then clears its software enabled flag regardless of the disable result. This can likewise expose the post-decrement DRMS ambiguity and can misrepresent an outstanding enable reference.

The normal-path design remains viable: retain one consumer enable on vdda-phy while the PHY is idle, set its active load to zero, and release it on provider teardown; hold VDDP for the UFS host's bound lifetime, then release it after generic UFS VCCQ shutdown. The patch implementations must be made error-state-aware.

## 2. Exact ACK regulator-core contract

Pinned source: [`drivers/regulator/core.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c).

### 2.1 `regulator_set_load()`

At `regulator_set_load()`:
- the consumer handle's stored `uA_load` is updated;
- if that handle is enabled and the load changes, the core immediately calls `drms_uA_update()`;
- if the DRMS update fails, the core restores the previous stored `uA_load` and returns a negative error;
- while the handle is disabled, a load change is stored without immediately running DRMS.

Source: [`regulator_set_load()`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L4920-L4980).

### 2.2 `regulator_disable()`

The relevant order in `_regulator_disable()` is:
1. for the final active consumer, PRE_DISABLE notifier and provider `.disable()` can run first;
2. after a successful provider disable, provider `use_count` can be set to zero;
3. `_regulator_handle_consumer_disable()` decrements this consumer handle's `enable_count`;
4. if the stored load is still nonzero and this is the handle's last reference, a DRMS update is attempted **after the decrement**;
5. a later negative DRMS result is returned without rolling the decremented handle count back;
6. coupling balance and parent-supply shutdown follow when applicable.

Sources:
- [`_regulator_handle_consumer_disable()`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L2820-L2865)
- [`_regulator_disable()`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L3020-L3090).

Therefore a negative `regulator_disable()` return is not, in general, proof that the consumer enable reference remains held. A teardown caller must remove the fallible nonzero-load DRMS transition before disabling.

## 3. L6: ROUND103 narrows the VDDP teardown boundary

The completed local Agent report [ROUND103](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round103/TEST_AGENT_ROUND103_L6_RPMH_DISABLE_CONFIG_REPORT.txt) covers the base FDT candidates 0/1/2, all nine stock DTBO entries and their compositions.

For PM8150 L6 node `/soc/rsc@18200000/rpmh-regulator-ldoa6/regulator-pm8150-l6`, it reports no:
- `qcom,always-wait-for-ack`;
- `regulator-coupled-with` or coupling spread properties;
- `vdd-l6-l9-supply`;
- `vin-supply`, `vdd-supply` or `vph-pwr-supply`.

No one of the nine overlays modifies this provider node or its regulator group. This is static HOS4.3 FDT evidence, not a live-rail measurement.

The pinned ACK RPMh driver reads `qcom,always-wait-for-ack` from each regulator node. With the property absent, PMIC5 L6 provider disable calls `rpmh_write_async()`; the RSC path programs and triggers the request, then returns without waiting for the final ACK. Any negative return from that async path is before the request trigger/acceptance boundary. In contrast, DRMS mode changes call the synchronous RPMh write and can return `-ETIMEDOUT` after the request has been triggered.

Sources:
- [RPMh per-regulator ACK property and request selection](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c#L145-L180)
- [RPMh disable state update](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c#L220-L270)
- [RPMh async write completion boundary](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/soc/qcom/rpmh.c#L190-L275)
- [RSC request programming and trigger](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/soc/qcom/rpmh-rsc.c#L600-L685).

### 3.1 Required VDDP cleanup sequence

For the current L6 use, the implementation sequence should be:

1. If the VDDP load vote is set, call `regulator_set_load(vddp, 0)` while the VDDP enable reference is still held.
2. If load-zero returns negative, stop this cleanup attempt. Regulator core restores the previous 100µA stored load; do **not** call `regulator_disable()` with that nonzero load still stored.
3. Only after load-zero succeeds, call `regulator_disable(vddp)`.
4. Clear the software enabled flag only after `regulator_disable()` returns success. If it returns negative, retain the flag and log the failure; the L6 async-provider error boundary means the provider request was not accepted and the consumer reference has not yet been decremented.
5. Clear the software load-set flag immediately after successful load-zero, not after disable.

This makes the normal disable path avoid the post-decrement DRMS update. The exact L6 FDT audit also excludes a real DT coupling or parent-supply chain for this provider. The absent upstream property may be handled by the ACK dummy-regulator fallback under full constraints; that dummy is an always-on software placeholder, not a physical power source. See [ROUND66](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round66/round66-pm8150-rpmh-parent-supply-dummy-fallback-audit.md).

The L6 zero-load operation itself remains a synchronous DRMS mode request and can time out after triggering. In that case its previous load is restored and the VDDP enable reference remains held, so the only safe immediate action is to leave the reference held and report the failure.

## 4. L5: QMP cleanup must not disable after failed load-zero

The current branch-local ROUND63 implementation performs:

```c
ret = regulator_set_load(qmp->vregs[0].consumer, 0);
if (ret < 0)
        dev_err(...);

ret = regulator_disable(qmp->vregs[0].consumer);
if (ret)
        dev_err(...);

qmp->vdda_phy_enabled = false;
```

Two state errors follow:

- If `regulator_set_load(0)` fails, regulator core restores the old nonzero load. Calling `regulator_disable()` then still allows the post-decrement DRMS operation to fail after the consumer reference has already been decremented.
- If `regulator_disable()` fails before decrement, the enable reference remains held; setting `vdda_phy_enabled = false` loses the only software record of it. The later managed regulator put still runs.

The minimum correct control-flow shape is:

```c
ret = regulator_set_load(qmp->vregs[0].consumer, 0);
if (ret < 0) {
        dev_err(qmp->dev, "failed to clear vdda-phy load, err=%d\\n", ret);
        return;
}

ret = regulator_disable(qmp->vregs[0].consumer);
if (ret) {
        dev_err(qmp->dev, "failed to disable vdda-phy, err=%d\\n", ret);
        return;
}

qmp->vdda_phy_enabled = false;
```

This is a sequencing/state-tracking requirement, not proof that L5's provider disable cannot fail. The HOS4.3 L5 group is PMIC5 NLDO with DRMS and a vendor `proxy-supply` / 100mA proxy-consumer configuration. That vendor proxy property is not an electrical parent input. Unlike L6, the already-completed ROUND103 task did not explicitly verify L5's `qcom,always-wait-for-ack` and coupling metadata across every base-FDT candidate and overlay. A negative L5 provider-disable result must therefore not be interpreted as a known pre-decrement-only error until the supplemental local evidence task is complete.

Do not copy the L6 disable-error conclusion to L5 yet.

## 5. Devres limitation remains real

The custom cleanup actions are registered after their managed regulator gets, so they run before the corresponding managed handle release. However, ACK `devm_regulator_release()` always calls `regulator_put()`; returning from the custom action does not cancel the later put.

Sources:
- [ACK regulator devres release](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/devres.c#L14-L42)
- [ACK regulator put / enable-count warning](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c).

Consequently:
- The load-first order eliminates a known post-decrement DRMS hazard when load-zero succeeds.
- It does **not** make a true provider disable failure disappear.
- If a managed handle reaches `regulator_put()` while its consumer enable count is still nonzero, the core warns. A custom action's `return` cannot prevent that.
- Do not hide the warning, clear state falsely, or call `regulator_force_disable()` on a shared rail as a shortcut. Any stronger failure policy must explicitly account for ownership of the regulator handle and the safety of retaining an enabled output.

## 6. Additional PHY API issue

The QMP candidate's `qmp_ufs_power_off()` currently logs a failure from `qmp_ufs_regulators_disable()` but returns success unconditionally. The PHY core only decrements `phy->power_count` when the provider `.power_off()` callback returns success; a negative callback result leaves the power count unchanged and is reported to the caller.

Source: [ACK `phy_power_off()`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/phy/phy-core.c#L350-L390).

2号 AI should decide whether the new regulator/load-clear failure should be propagated through `qmp_ufs_power_off()`. If propagated, preserve the hardware-down / clocks-off state and ensure retry semantics are correct; do not silently report a successful PHY power-off while the active load vote may still be present. This must be tested against the caller's shutdown handling.

## 7. Actions for 2号 AI

The actual patch changes belong to 2号 AI on `ai-parallel/stagea-port-until-boot`. The branch-local source changes should:

1. Change ROUND52 VDDP cleanup to load-zero-before-disable and maintain separate truthful load/enable state.
2. Change ROUND63 QMP cleanup so load-zero failure aborts before disable, and clear `vdda_phy_enabled` only after successful regulator disable.
3. Decide and document the error return behavior of QMP `.power_off()` for a failed load-vote transition.
4. Preserve the original bulk path when `vdda-phy-always-on` is absent.
5. Do not change board DTS, PMIC parent supply declarations, AVB, boot packaging or device state as part of this source correction.
6. Rerun the real patch/apply, checkpatch, binding fixtures and complete pinned Stage-A Image build after the final corrected series. A previous Image build does not validate these later source corrections.

The taskbook `AI2-ROUND30` is currently an implementation task for 2号 AI. The local Agent is **not** the kernel patch author. Any local Agent work is restricted to read-only evidence collection or authorized test/build execution, with explicit task ownership stated separately.

## 8. Review boundary and status

- Pinned source semantics for `regulator_set_load()`, `_regulator_disable()`, RPMh write modes and devres ordering: CONFIRMED.
- L6 HOS4.3 static ACK/coupling/parent property audit: COMPLETED in ROUND103.
- L5 HOS4.3 static ACK/coupling/parent property audit: NOT YET COMPLETED at the same evidence standard; see the separate ROUND106 Agent taskbook.
- QMP/VDDP corrected implementation: NOT YET PRESENT in the reviewed branch snapshot.
- Runtime regulator transitions, failure injection, device boot and rail measurement: NOT RUN.

No source, binding, DTS, config, 2号 AI branch, protected branch, PR or firmware artifact was modified by this report.
