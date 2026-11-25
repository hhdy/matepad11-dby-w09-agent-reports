# ROUND109 — 1号 AI: QMP PHY power-off success semantics and residual regulator-state design

**Date:** 2026-11-25  
**Owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Pinned ACK:** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Scope:** reconcile QMP PHY power-off, generic PHY power-count and Qualcomm UFS variant-exit contracts after ROUND106/107. No source, patch or 2号 AI branch was modified.

## 1. Decision

The QMP provider callback should not report a failed *regulator optimization/cleanup* as a failed *PHY hardware power-off* after it has already asserted the PHY's power-down state and disabled its clocks.

The safer source-level contract for this specific provider is:

- perform the PHY hardware-down sequence;
- attempt to reduce/drop regulator consumer votes;
- on any regulator error, retain truthful per-rail state and log the error;
- return success once the PHY hardware is down, so generic PHY core decrements `phy->power_count`;
- make the next power-on reuse any regulator references that remain held rather than enabling them a second time;
- on final QMP provider removal, attempt to drain all residual references before the managed regulator handles are put.

This is preferable to simply propagating the regulator error from `qmp_ufs_power_off()`: the Qualcomm UFS variant `exit` callback is void and currently ignores the return from `phy_power_off()`, then unconditionally calls `phy_exit()`. Error propagation alone therefore does not stop the UFS remove sequence or guarantee a later retry. It can instead leave generic PHY `power_count` stale while the UFS host releases its PHY reference.

This decision does **not** make regulator failure harmless. It requires an explicit, retry-safe regulator state machine and a separate final-unbind cleanup attempt. A true persistent regulator error remains visible and is not solved by devres ordering.

## 2. Exact caller/provider contracts

Pinned sources:
- [Generic PHY core](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/phy/phy-core.c)
- [Qualcomm UFS variant callback](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufs-qcom.c)
- [UFS variant ops type](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/ufs/ufshcd.h)

### 2.1 Generic PHY core

Pinned `phy_power_off()`:
1. calls provider `.power_off()` only when `phy->power_count == 1`;
2. if provider returns negative, the core returns immediately without decrementing `power_count`;
3. if provider returns success, the core decrements `power_count`, releases runtime-PM reference and returns 0.

Thus the provider return value is a statement about whether the PHY power-off transition completed—not a mechanism for rolling back regulator operations already done by the callback.

### 2.2 Qualcomm UFS variant exit is void

Pinned `struct ufs_hba_variant_ops` declares:

```c
void (*exit)(struct ufs_hba *);
```

Pinned `ufs_qcom_exit()` is also void:

```c
ufs_qcom_disable_lane_clks(host);
phy_power_off(host->generic_phy);
phy_exit(host->generic_phy);
```

The return from `phy_power_off()` is ignored. `ufshcd_hba_exit()` invokes the variant exit through a void wrapper and continues with generic UFS VCC/VCCQ, clocks and host-controller power cleanup. The remove callback itself is void.

Therefore changing the QMP callback to return an error after partially powering the PHY down does not abort UFS remove and does not automatically retry that PHY transition. It may leave `phy->power_count` nonzero even though the consumer's managed PHY reference is released afterwards.

## 3. Concrete residual-reference failure case

For the SM8250 two-entry QMP UFS PHY list:
- index 0: `vdda-phy` (PM8150 L5, 89.9mA stored initial load);
- index 1: `vdda-pll` (PM8150 L9, 18.8mA stored initial load).

The following error path is possible if the L9 asynchronous provider-disable request fails before its TCS trigger:

1. QMP has powered down the PHY and disabled its clocks.
2. `regulator_bulk_disable(1, &vregs[1])` returns an error. With this board's absent RPMh ACK override, the L9 disable helper returns before the provider request is accepted; the regulator consumer enable reference remains held.
3. The current QMP helper logs the error, but does not retain an explicit tail-rail state.
4. If it returns success, generic PHY core decrements `power_count`.
5. On a later `phy_power_on()`, the core calls the provider callback again. A naive helper calls `regulator_bulk_enable()` on L9 a second time even though the previous enable reference remains held. The consumer reference count can then be 2.
6. A later successful single disable leaves one reference behind, and provider devres release eventually warns about an unbalanced regulator enable.

There is an analogous L5 path if `regulator_set_load(0)` fails after L9 was successfully disabled: L9 is already off while the L5 retained enable and its old load vote remain active.

These are conditional source-level failure paths, not observed tablet failures.

## 4. Required per-rail state model

A single `vdda_phy_enabled` boolean is not enough. The QMP instance needs state sufficient to distinguish:

| State | Meaning |
|---|---|
| L5 enable reference held | Whether the QMP L5 consumer has successfully acquired its retained enable reference |
| L5 stored load active | Whether the stored consumer request currently equals the active `init_load_uA` rather than zero |
| L9/tail enable reference held | Whether the trailing PHY consumer reference remains held after the last successful API transition |

Important initialization detail from pinned `devm_regulator_bulk_get_const()` / `_regulator_bulk_get()`:

- at probe, the bulk-get path already stores each positive `init_load_uA` in the consumer handle;
- the consumer is not enabled yet, so that initial load does not contribute to DRMS;
- therefore a false “enable held” flag at probe does not mean the stored load is zero;
- after successful load-zero, the stored request is zero;
- after a successful restore, the stored request is back at its init value.

The implementation may encode this using explicit flags or a small enum, but it must not infer stored load from enable count.

## 5. Suggested transition contract

This section gives the required behavior; it does not prescribe exact C code or authorize 1号 AI to edit the implementation branch.

### 5.1 Power-on

1. Restore L5 active load if the stored request is zero.
2. If L5 enable reference is not held, acquire exactly one reference and mark it held only after success.
3. Enable L9 only if its reference is not already held from a previous failed cleanup.
4. Mark the tail state only after successful enable.
5. Continue clock enable and PHY register power-up.
6. If a later step fails, unwind only operations acquired by this invocation; do not disable an older retained reference that pre-dated the invocation.

This prevents a second `regulator_enable()` from being applied to L9 after a previous disable failed.

### 5.2 Power-off

1. Put the PHY hardware into power-down state and disable clocks.
2. If the tail rail is tracked as enabled, attempt its shutdown. Preserve the state on failure. For this board's L9, the async disable failure is before the provider-trigger/consumer-decrement boundary, so an error means the reference remains held.
3. If tail shutdown succeeds, mark the tail reference not held.
4. Request L5 load zero while its retained enable reference remains held.
5. If load-zero fails, regulator core restores the previous stored load. Preserve the “load active” state and retained L5 reference.
6. If load-zero succeeds, record that the stored load is zero. The L5 enable reference remains held by policy.
7. Return success **after the PHY hardware is down**, even when a regulator vote could not be optimized/released, while emitting an explicit failure diagnostic and preserving state. The next power-on must reconcile those states without duplicate enable operations.

The key distinction is: a regulator vote may remain active while the PHY is logically powered off; this consumes extra power and must be surfaced, but it must not make generic PHY `power_count` lie about the hardware state.

### 5.3 Final QMP provider removal

The QMP provider's custom devres action is registered after the managed bulk regulator get, so it runs before managed regulator handles are put.

That action must:
1. turn the L5 stored load to zero if currently active;
2. disable the retained L5 reference only after a successful load-zero;
3. drain the L9/tail reference if the tail state says it is still held, using load-zero-before-disable if required by the provider's DRMS semantics;
4. clear each state flag only after its corresponding operation succeeds;
5. log any remaining failure.

A void devres callback cannot veto the later managed `regulator_put()`. If a true persistent provider error leaves a reference outstanding, the regulator core will still warn. Do not hide the warning, clear state falsely, or use force-disable on a shared PMIC rail.

## 6. Why this design fits the known DBY-W09 FDT evidence

- ROUND106 confirms no L5 `qcom,always-wait-for-ack`, no coupling properties and no ordinary parent-supply property anywhere in the three base candidates or nine stock DTBOs.
- ROUND103 confirms the equivalent ACK/coupling/parent absence for L6.
- The QMP PHY property `vdda-phy-always-on` is a consumer-side policy to retain L5, not a PMIC-provider always-on declaration.
- The HOS4.3 vendor 100mA proxy-consumer fields on L5/L9 remain a separate unimplemented ARC/proxy-compatibility gap. Pinned ACK RPMh provider source does not parse those vendor properties.
- The normal consumer-first UFS remove order remains required; the PHY core device link is stateless and does not authorize manually unbinding QMP while UFS remains bound.

## 7. Acceptance tests for 2号 AI

At minimum test the state machine against:
1. Initial probe: L5 stored load=89.9mA, L5 enable=false, tail stored load=18.8mA, tail enable=false.
2. First power-on succeeds: exactly one L5 reference and one tail reference.
3. Ordinary power-off succeeds: tail reference removed, L5 reference retained with stored load zero.
4. Second power-on: L5 reference reused, active load restored, tail gets exactly one reference.
5. L9 disable fails before trigger: tail flag remains true; the next power-on must not add another reference.
6. L9 disable succeeds, L5 load-zero fails: tail stays false; L5 stays enabled with old 89.9mA stored load; next power-on restores hardware without duplicate tail enable.
7. L5 load-zero succeeds, L5 provider disable at final provider removal fails before trigger: enable flag remains true and failure is reported; managed-put limitation is explicit.
8. Provider removal after a clean idle state: L5 load zero, one retained reference disabled, tail already disabled, then both managed handles can be put without enable-count warnings.
9. Property absent: original bulk behavior is unchanged.

Runtime hardware measurement and failure injection remain separate; this report only defines source-level acceptance behavior.

## 8. Status

- Generic PHY power-count semantics: SOURCE-CONFIRMED.
- Qualcomm UFS variant-exit is void and ignores `phy_power_off()` return: SOURCE-CONFIRMED.
- L5/L9 async provider disable boundaries for the inspected HOS4.3 DT configuration: SOURCE-CONFIRMED subject to the absence of separately registered out-of-DT supply aliases.
- Current QMP implementation: lacks sufficient residual-rail state to avoid duplicate tail enables after partial failures.
- Suggested truthful-success / tracked-residual power-off contract: DESIGN RECOMMENDATION FOR 2号 AI.
- Actual patch, apply, checkpatch, compile, failure injection and device test: NOT RUN.

No source, patch, binding, DTS, configuration, development branch, protected branch, PR or firmware artifact was modified by this report.


## 9. All pinned QMP UFS PHY regulator tables are exactly two rails

I parsed every `static const struct regulator_bulk_data ..._vreg_l[]` initializer in the exact pinned `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c` source:

- 15 regulator-list arrays found;
- every array has exactly two entries;
- every array orders them `vdda-phy` first and `vdda-pll` second;
- the SM8250 list is `vdda-phy = 89900µA`, `vdda-pll = 18800µA`.

This confirms that the current pinned tree's vendor property path has one retained L5 rail and exactly one trailing L9 rail for every existing QMP UFS compatible. Therefore a single tail-enabled state is sufficient for the exact pinned source revision, provided 2号 AI does not broaden the supported list or alter its ordering. The driver's fail-closed first-entry validation remains appropriate.

The binding declares the optional boolean in the shared QMP UFS PHY schema, whose compatible enum contains `qcom,sm8250-qmp-ufs-phy` and the other listed QMP UFS variants. The property is therefore schema-accepted for any of those compatible strings, not syntactically restricted to SM8250. The fixed ACK source currently makes all 15 lists the same two-rail ordering, so this does not create a different current list layout. Future additions to a list must revisit the state machine.

