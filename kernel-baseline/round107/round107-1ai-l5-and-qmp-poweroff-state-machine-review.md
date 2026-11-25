# ROUND107 — 1号 AI: L5 ACK disable contract and QMP power-off retry-state review

**Date:** 2026-11-25  
**Owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Local evidence executor:** TEST-AGENT-ROUND106 (completed; read-only)  
**Pinned ACK:** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Scope:** combine ROUND106 HOS4.3 L5 FDT evidence with exact regulator/RPMh/PHY-core contracts. No kernel, binding, DTS, patch, or 2号 AI branch was modified.

## 1. Decision

ROUND106 closes the static HOS4.3 evidence question for PM8150 L5:

- no `qcom,always-wait-for-ack` anywhere in the three base FDT candidates or nine stock DTBO entries;
- no regulator coupling attributes anywhere in the base candidates or DTBOs;
- no ordinary upstream `*-supply` / `*-parent-supply` property on the L5 provider group or its three children;
- the only L5-group supply-like property is vendor `proxy-supply`, which points back to the L5 regulator child itself and is not a physical input parent;
- none of the nine overlays targets or alters the L5 regulator group / children.

This makes the L5 disable path materially narrower than a generic “regulator_disable can return after decrement” warning:

1. **L5 provider disable is asynchronous in this board FDT.** The ACK RPMh provider sends the disable request through `rpmh_write_async()` because the per-regulator ACK property is absent. The RSC function returns after command-buffer programming and trigger, not after final hardware acknowledgement. A negative provider `.disable()` result is therefore before the request-trigger boundary; after a successful trigger the asynchronous call returns 0.
2. **The remaining known post-decrement DRMS hazard is avoided by clearing L5 load first.** `regulator_set_load(0)` while the consumer is enabled performs the DRMS transition before changing the consumer enable count. On failure the regulator core restores the previous stored load and leaves the enable reference held. QMP must abort the disable attempt on this failure.
3. **Coupling is not a post-decrement failure source in the inspected HOS4.3 DT.** ROUND106 found no coupling properties, including reverse coupling references, in the full base FDT or any stock overlay.
4. **A physical parent is not described in the inspected FDT.** The ACK L5 descriptor has a software `supply_name`, but the board has no matching DT supply phandle. The regulator core may use its full-constraints dummy-regulator fallback for an unresolved missing supply. That dummy is a software placeholder and does not prove a physical input source. A possible out-of-DT regulator alias or mapping is not proven by the firmware report, so it must not be silently ruled out.

The correct QMP consumer sequence remains **load-zero first, then disable; abort before disable if load-zero fails; only clear software enable state after disable succeeds**. The implementation still needs a retry-safe state model for the non-L5 PHY rails and a deliberate teardown policy for managed regulator puts.

## 2. ROUND106 evidence accepted with scope limits

Agent report:
[`TEST_AGENT_ROUND106_L5_RPMH_DISABLE_CONFIG_REPORT.txt`](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round106/TEST_AGENT_ROUND106_L5_RPMH_DISABLE_CONFIG_REPORT.txt)

The report records matching hashes and lengths for the three base FDT candidates and nine DTBO entries; all 13 objects passed the existing parser's structural checks. It independently declares that no inputs, parser, other ROUND workspaces, source files, or Git branches were changed.

The following details are important to the code review:

- L5 is the PMIC5 NLDO provider under `/soc/rsc@18200000/rpmh-regulator-ldoa5`.
- L5 child is `.../regulator-pm8150-l5`; sibling nodes are `l5-ao` and `l5-so`.
- Group-level `proxy-supply` points to the L5 child itself. The child contains vendor `qcom,proxy-consumer-enable` and `qcom,proxy-consumer-current = 100000`.
- The proxy relationship is not a physical upstream power connection and is not an ordinary regulator parent-supply edge.
- All nine overlays add the PHY consumer's `vdda-phy-supply` reference to L5 and `vdda-phy-always-on` boolean, but do not change the L5 provider node.
- The report performed structural composition reasoning rather than binary `fdtoverlay` because that executable was unavailable. Since no fragment targets the L5/RSC subtree and no overlay node is placed there, the no-change conclusion for L5 provider properties is a sufficient structural result. It is not a binary recomposition claim.
- DTBO entry 8 is not asserted to be the runtime-selected overlay. The L5 result is identical across all nine entries.

## 3. Exact pinned ACK L5 disable path

### 3.1 Provider's ACK policy is read from the regulator child

Pinned ACK `drivers/regulator/qcom-rpmh-regulator.c` reads `qcom,always-wait-for-ack` from the individual regulator node into `vreg->always_wait_for_ack`.

The send helper selects:

- synchronous `rpmh_write()` when `wait_for_ack` is true or `vreg->always_wait_for_ack` is set;
- asynchronous `rpmh_write_async()` otherwise.

The state helper calls the send function with `enable` as the wait argument. Thus enable requests wait for acknowledgement, while disable requests are asynchronous unless the DT property overrides them.

ROUND106 found no such property on L5, its siblings, its group, the full base FDT, or any of the nine overlays. The L5 provider's normal disable therefore uses the asynchronous branch.

Pinned sources:
- [RPMh send helper and provider state helper](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c)
- [RPMh asynchronous and synchronous write implementation](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/soc/qcom/rpmh.c)
- [RSC trigger implementation](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/soc/qcom/rpmh-rsc.c)

### 3.2 What an asynchronous disable error means

Pinned `rpmh_rsc_send_data()`:
1. resolves the TCS group;
2. claims a free TCS;
3. writes the command buffer;
4. triggers the TCS;
5. returns 0 without waiting for completion.

Errors from the helper's TCS resolution occur before the buffer write/trigger. There is no completion timeout on this asynchronous branch. The RPMh regulator updates `vreg->enabled` only when the send function returns 0.

Consequently, for L5's DT configuration, a negative result from the provider's asynchronous disable operation means the request was not accepted/triggered by this helper. The regulator core's `_regulator_do_disable()` returns that provider error before it reaches `_regulator_handle_consumer_disable()`, so the consumer enable count has not yet been decremented on this provider-disable error path.

This is a source-contract statement about the pinned asynchronous call. It is not a runtime measurement of the PMIC rail after a successful trigger; that operation is intentionally not acknowledged synchronously.

### 3.3 Why load-zero must precede disable

The generic ACK regulator core behaves differently for the DRMS load transition:

- `regulator_set_load()` on an enabled consumer calls `drms_uA_update()` immediately.
- If the RPMh mode request fails, the core restores the previous stored load and returns a negative error while the enable reference remains held.
- If the consumer is disabled while its old nonzero load is still stored, `_regulator_handle_consumer_disable()` decrements the consumer's enable count first and then calls DRMS. A negative DRMS result is returned after that decrement and is not rolled back.

L5 is PMIC5 NLDO, which has the ACK PMIC5 DRMS operations and a 30mA HPM threshold. The QMP SM8250 active load is 89.9mA. Clearing the load while enabled causes the mode transition to be attempted before the consumer reference is removed.

Therefore:
- if `regulator_set_load(0)` fails, do not call `regulator_disable()`;
- if load-zero succeeds, the subsequent consumer disable no longer needs the nonzero-load DRMS transition after decrement;
- only clear the software “enabled reference held” flag after `regulator_disable()` succeeds.

Pinned sources:
- [ACK regulator core DRMS update and load handling](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c)
- [ACK PM8150 L5 uses PMIC5 NLDO DRMS operations](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c)

## 4. Parent-supply and coupling boundary

ROUND106 found no `regulator-coupled-with`, max/min spread, no-balance or vendor coupling property anywhere in the three base FDT candidates or nine DTBOs. No regulator in the RSC subtree can reverse-couple to L5 through those attributes.

The base FDT also has no `vdd-l3-l4-l5-l18-supply`, `vin-supply`, `vdd-supply`, `vph-pwr-supply`, or other parent-supply property on L5's group/children. This is a confirmed DT fact, not proof that a physical input rail does not exist.

Pinned ACK L5 descriptor has software parent name `vdd-l3-l4-l5-l18`. When an upstream property/alias cannot resolve a regulator and full constraints are active, the regulator core can substitute its dummy regulator. That dummy is configured always-on and is only a software fallback. It must not be described as a DBY-W09 schematic or physical parent.

The exact source review cannot exclude a separately registered supply alias or regulator mapping unless the actual complete booted driver inventory is known. Therefore the post-decrement parent-disable path is classified as **not evidenced in DT; dummy fallback is possible; external alias/mapping not established**. Do not invent a parent phandle.

Pinned source:
- [ACK regulator supply resolution and full-constraints dummy fallback](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c)
- [ACK dummy regulator's always-on constraint](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/dummy.c)

## 5. Vendor proxy is a separate compatibility gap

The HOS4.3 L5 group declares `proxy-supply` pointing to its own L5 child; that child carries the vendor 100mA proxy-consumer properties. The pinned ACK `drivers/regulator/qcom-rpmh-regulator.c` does not parse `proxy-supply`, `qcom,proxy-consumer-enable`, or `qcom,proxy-consumer-current` (a full-file source scan found no matching implementation references beyond its ordinary `supply_name` fields).

Thus the HOS4.3 proxy-consumer semantics are not automatically reproduced by merely porting the QMP PHY's 89.9mA active load and always-on enable behavior. The missing ARC/proxy lifecycle remains a separate compatibility task; it must not be represented as a physical PMIC input parent, permanent `regulator-system-load`, or proof of an always-on constraint.

## 6. QMP implementation requirements and retry-state hazard

The branch-local ROUND63 candidate currently has these defects/limitations in its cleanup helper:

1. It logs a failed `regulator_set_load(vdda_phy, 0)` but still calls `regulator_disable()`. This reintroduces the post-decrement DRMS path that the load-first order is meant to avoid.
2. It clears `vdda_phy_enabled` even when `regulator_disable()` returns an error, losing the software record of a still-held reference.
3. The top-level `qmp_ufs_power_off()` logs an error from regulator shutdown but returns success unconditionally.
4. The state does not separately track the trailing PHY regulator bulk state and the vdda-phy load-vote state.

### 6.1 Minimum L5 state transition

For the retained L5 reference, the special cleanup transition must be equivalent to:

```c
ret = regulator_set_load(qmp->vregs[0].consumer, 0);
if (ret < 0) {
        dev_err(qmp->dev, "failed to clear vdda-phy load, err=%d\\n", ret);
        return ret;
}

ret = regulator_disable(qmp->vregs[0].consumer);
if (ret) {
        dev_err(qmp->dev, "failed to disable vdda-phy, err=%d\\n", ret);
        return ret;
}

qmp->vdda_phy_enabled = false;
```

This is a sequencing illustration, not a complete cleanup implementation. A void devres action cannot veto the later managed `regulator_put()`; if an error leaves the enable reference held, regulator core will still warn when the managed handle is released. Do not clear flags falsely, ignore the failure, or use `regulator_force_disable()` on a shared PMIC rail as a shortcut.

### 6.2 Required retry state for the trailing rails

The special power-off path disables the trailing PHY supplies (currently including `vdda-pll`) before attempting L5 load-zero. If the trailing bulk-disable succeeds but the later L5 load-zero fails, the helper has partially completed its off transition.

Pinned `regulator_bulk_disable()` rolls back already-disabled members only if a member within that bulk operation fails. It does not roll back a successful bulk disable when a later, separate L5 `regulator_set_load(0)` call fails.

Therefore, if the PHY API path can retry after an L5 load-zero failure, a second call must not blindly invoke `regulator_bulk_disable()` on already-disabled trailing consumers. The QMP private state needs to record at least:
- whether the retained L5 enable reference is held;
- whether the L5 load vote is currently active;
- whether the trailing PHY regulator set is enabled.

The state flags change only after the corresponding regulator API succeeds. Enable/disable helpers must be idempotent against partially completed power-on/off operations. If a trailing bulk-disable itself fails, the regulator core attempts rollback for the members already disabled; that rollback can also fail and must remain observable.

Pinned source:
- [ACK regulator bulk disable and rollback behavior](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c)

### 6.3 PHY API and UFS remove caller must be reviewed together

The PHY core decrements `phy->power_count` only when provider `.power_off()` returns success. A negative return leaves that count unchanged.

However, pinned `drivers/ufs/host/ufs-qcom.c` has a void `ufs_qcom_exit()` which currently calls `phy_power_off()` and then `phy_exit()` without checking the first return value. Merely changing QMP power-off to return an error is therefore not a complete remove-path fix: the UFS caller still proceeds to `phy_exit()`, and later devres release still occurs.

The implementation owner must choose and document the behavior for:
- ordinary PHY power-cycle callers that can consume a negative `phy_power_off()` result;
- UFS host remove, where the variant exit callback is void and currently ignores the PHY power-off result;
- QMP provider devres cleanup, which cannot prevent the managed regulator handle from being put.

Do not assume that error propagation alone makes removal retryable. Conversely, do not silently claim power-off success if the regulator state is only partially transitioned. The exact caller and cleanup constraints need to be represented in the state machine and tests.

Pinned sources:
- [ACK PHY power-off / power-count contract](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/phy/phy-core.c)
- [ACK Qualcomm UFS variant exit caller](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufs-qcom.c)

## 7. VDDP L6 remains a separate but parallel fix

ROUND103 establishes that PM8150 L6 also lacks `qcom,always-wait-for-ack`, coupling and a DT parent-supply property, and that no one of the nine overlays changes those properties.

The current ROUND52 VDDP cleanup still calls `regulator_disable()` before requesting load zero. It must use the same load-first ordering:
1. set VDDP load to zero while its reference remains held;
2. abort the disable if that returns an error (the core restores the previous stored load);
3. on successful load-zero, call regulator disable;
4. clear the enable-state flag only after successful disable.

L6's async disable has the same pre-trigger error boundary as L5's, but the L6 HOS4.3 evidence should be referenced from ROUND103 rather than inferred from L5.

## 8. Action for 2号 AI

2号 AI owns all source implementation changes on `ai-parallel/stagea-port-until-boot`. The local Agent does not edit the driver.

Before accepting ROUND63 / ROUND52 teardown as complete, the implementation should:
1. make both L5 and L6 load-zero-before-disable;
2. abort disable after a failed load-zero and preserve truthful state;
3. clear enable flags only after successful regulator disable;
4. track the trailing PHY regulator enable state separately so retries do not disable a second time;
5. define the power-off failure behavior for normal PHY power cycles and for the void UFS variant exit caller;
6. retain the original bulk behavior for PHY nodes without `vdda-phy-always-on`;
7. preserve the independent HOS ARC/proxy compatibility gap as OPEN;
8. rerun real patch apply/checkpatch/binding fixtures and the full manifest-pinned Stage-A `//common:dby_w09` Image build after the corrected series.

No device access or power-rail measurement is authorized by this review.

## 9. Status

- ROUND106 Agent delivery and static FDT input integrity: ACCEPTED.
- L5 ACK flag absence / coupling absence / no DT parent property / no overlay provider edits: CONFIRMED.
- L5 async-disable request boundary in pinned ACK: SOURCE-CONFIRMED.
- Load-zero-before-disable requirement: CONFIRMED.
- Current ROUND63/QMP cleanup and retry-state implementation: NOT YET CORRECTED in the branch snapshot reviewed.
- Current ROUND52/VDDP cleanup ordering: NOT YET CORRECTED in the branch snapshot reviewed.
- ARC/proxy consumer framework parity: OPEN.
- Physical PMIC L5 input topology: OPEN.
- Hardware regulator transitions, failure injection, PHY power cycles and device boot: NOT RUN.

No source, patch, binding, DTS, config, branch, PR or firmware artifact was modified by this report.


## 10. ROUND61 built-config cross-check: dummy regulator implementation is present

The Phase-D Image artifact previously downloaded and independently checked contains `CONFIG_REGULATOR=y` in its final `.config`. The exact pinned ACK `drivers/regulator/Makefile` places `dummy.o` in the `CONFIG_REGULATOR` object list. The pinned `drivers/regulator/core.c` calls `regulator_dummy_init()` from its `core_initcall(regulator_init)`, and `drivers/regulator/dummy.c` registers the dummy regulator with an `always_on = 1` constraint.

Thus the actual Phase-D candidate includes the ACK dummy-regulator implementation and its early initialization path. Given the absent L5 parent-supply property, if ordinary supply lookup has no separately registered alias or matching mapped regulator, the regulator core has an available always-on dummy fallback for the L5 descriptor's software parent request.

This strengthens the classification from “dummy fallback is theoretically available” to “the built candidate contains and early-registers the dummy provider.” It still does **not** prove that a particular L5 lookup selected that dummy at runtime; a separate supply alias or matching regulator map would take precedence. It also does not establish any physical L5 input net. No change to the Phase-D artifact or source tree was made.


## 11. QMP bulk-get initializes the stored load before the first PHY power-on

A final pinned-source check adds an important state-machine detail:

- `devm_regulator_bulk_get_const()` copies the static QMP `vreg_list` into managed mutable storage, then calls `devm_regulator_bulk_get()`.
- `_regulator_bulk_get()` acquires each regulator and immediately calls `regulator_set_load(consumer, init_load_uA)` for every positive initial load.
- Therefore, after QMP probe succeeds, the L5 consumer handle already stores its 89.9mA `init_load_uA` request even though its enable count is still zero and the load is not yet included in DRMS aggregation.
- The ROUND63 first-power-on call to `regulator_set_load(init_load_uA)` is initially a same-value request; it does not create the first load vote by itself. The subsequent `regulator_enable()` makes that stored request active for DRMS.
- A successfully completed power-off `regulator_set_load(0)` changes the stored request to zero. Later power-on must restore the original init load before/with the enable transition.

This means the state model must distinguish **stored load request** from **enabled consumer reference**. In particular, `vdda_phy_enabled == false` after probe does not mean the stored load is zero. The initial stored request is 89.9mA but is inactive until the handle is enabled.

Suggested logical state (not a prescribed struct layout):
- L5 enable reference held: false at probe; true after successful first enable; remains true during ordinary PHY off/on cycles; false only after successful final disable.
- L5 stored load request: initialized to `init_load_uA` by bulk-get; becomes zero only after successful load-zero; returns to `init_load_uA` on subsequent successful restore.
- trailing PHY rail state: false at probe; true after successful bulk-enable; false after successful bulk-disable.

If load-zero fails, regulator core restores the previous stored load request, so the state must remain “init load” and the L5 enable reference must remain held. The cleanup action must reattempt load-zero before disable; it must not infer load state from the enable-reference flag.

Pinned sources:
- [ACK regulator bulk-get and init-load application](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c)
- [ACK devm regulator bulk-get-const copy / lifetime](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/devres.c)

## 12. Removal retry caveat for the UFS variant

Pinned `ufs_qcom_exit()` is a void callback and currently ignores the return from `phy_power_off()`, then calls `phy_exit()`. Therefore an error returned by the QMP `.power_off()` implementation can be observed by other PHY API callers but is not currently used to stop the ordinary UFS variant teardown sequence.

If an implementation chooses to propagate `qmp_ufs_power_off()` errors, it must not claim that this automatically retries UFS removal. Any retry/best-effort policy needs to be implemented and documented at the UFS variant-exit call site (or in the QMP managed cleanup strategy) without assuming the core can abort a void remove callback. The existing consumer-first teardown order still holds, but it is not an error-recovery mechanism.

This distinction is important because a failed L5 load-zero can occur after the trailing PLL consumer has already been disabled successfully. Any explicit retry must remember that the trailing rail is off and must not call `regulator_disable()` on it a second time.


## 13. Concrete trailing-rail failure case: vdda-pll / PM8150 L9

The SM8250 QMP UFS PHY configuration has two rails:
- index 0: `vdda-phy`, 89.9mA initial load, PM8150 L5;
- index 1: `vdda-pll`, 18.8mA initial load, PM8150 L9.

HOS4.3 ROUND13 identifies L9 as PMIC5 NLDO with a 30mA HPM threshold and a vendor 100mA proxy-consumer property. The ACK regulator driver does not implement the vendor proxy-consumer properties. ROUND106's global base-FDT/DTBO scan also found no `qcom,always-wait-for-ack` or coupling property anywhere, so the L9 provider disable request uses the asynchronous RPMh branch too.

The failure sequence in the current ROUND63 helper is concrete:
1. `regulator_bulk_disable()` attempts to disable the trailing `vdda-pll` consumer.
2. If L9's asynchronous provider disable fails before trigger, regulator core returns the error before decrementing that consumer handle's enable count.
3. `qmp_ufs_regulators_disable()` returns an error, but current `qmp_ufs_power_off()` only logs it and returns success.
4. PHY core therefore decrements `phy->power_count` as if the whole power-off succeeded.
5. A subsequent PHY power-on calls `regulator_bulk_enable()` again for L9. Because the previous failed disable left the consumer reference held, this creates a second reference.
6. A later successful power-off then removes only one reference; L9 can remain logically enabled after the PHY is off.

This double-reference scenario is conditional on a provider disable failure; it is not a claim that such a failure has been observed on the tablet. It demonstrates why the non-L5 rail state must be tracked rather than discarded when the helper returns an error.

For the SM8250 two-rail list, a per-tail-rail enabled flag is sufficient to avoid re-enabling a reference that remains held after an error. The special property path should also consider whether a DRMS load-zero request is needed for the trailing L9 consumer before disable, because it is itself a DRMS-capable NLDO. With its 18.8mA request below the 30mA threshold, an isolated L9 consumer remains in LPM on both sides of the disable; however, any additional active consumer could change the aggregate and cross the mode threshold. Do not assume absence of other consumers without an exact phandle-reference inventory.

The HOS4.3 100mA L9 proxy-consumer field does not establish an ACK Linux DRMS load: the pinned ACK provider has no implementation for that vendor property. Keep the ARC/proxy parity gap separate.


### ROUND107 dummy-provider operational semantics (additional pinned-source check)

Pinned ACK `drivers/regulator/core.c::_regulator_is_enabled()` returns 1 when a regulator provider has no `.is_enabled` operation, with the explicit comment “If we don't know then assume that the regulator is always on.” The built-in dummy provider has no regulator ops and has `constraints.always_on = 1`. Therefore, if L5's missing parent is resolved to the dummy regulator:
- regulator-core treats that parent as logically already enabled;
- no physical upstream enable/disable operation exists on the dummy;
- the dummy consumer reference can still be accounted by regulator core;
- this mechanism is a software assumption that the physical PMIC input is already available, not an actual power source.

This supports the statement that the built candidate can proceed without a declared L5 parent phandle, but does not prove the regulator lookup selected dummy rather than an alias/mapping, and does not close the L5 electrical input topology.

Pinned source:
[`_regulator_is_enabled()`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L3240-L3255)
