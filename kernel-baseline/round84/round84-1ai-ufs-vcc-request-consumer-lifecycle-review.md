# ROUND84 — 1号 AI review: ACK UFS VCC consumer voltage request and lifecycle integration

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, after a separate test task is issued  
**Pinned baseline:** ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Related records:** ROUND81 (DT schema result), ROUND82 (legacy VCC range semantics), ROUND83 (PM8150 parent supply-name contract)

## 1. Executive result

This is a read-only follow-up to ROUND82. The fixed ACK source confirms that:

1. The legacy Qualcomm `vcc-voltage-level` value is a VCC consumer voltage interval, not a PMIC provider constraint and not a decorative DTS annotation.
2. ACK 6.18.33's common UFS platform parser does not read that property, and the UFS core does not apply a consumer voltage request. Its current regulator configuration path only manages DRMS load.
3. The ACK exported helper `ufshcd_populate_vreg()` is also used by the in-tree MediaTek UFS host for dynamically selected VCC regulator names. The DBY-W09/Qualcomm-specific property must therefore not be blindly added to the shared helper or change its semantics for all callers.
4. The existing ACK enable/disable sequence gives a clear place to add a VCC-only voltage vote, but the existing disable path ignores errors from releasing the configuration vote. If a voltage request is added without addressing that behavior, a stale minimum-voltage request can remain silently active.
5. The regulator API explicitly allows a consumer to set voltage while the regulator is enabled or disabled. Thus the legacy order (apply request before enable, relax request after dropping the enable reference) is API-compatible; there is no evidence-based reason to reorder it merely because the rail is disabled during request setup.

**Recommendation to 2号 AI:** retain ROUND82's preferred Path A for evaluation: restore the actual VCC consumer request in ACK and provide matching binding support. Keep parsing narrow to the regular `vcc` supply. Do not remove the DTS interval just to silence dt-schema. This report is design review only: it does not authorize 1号 AI to alter 2号 AI's patch series, DTS candidate, or branch.

## 2. Exact pinned ACK source findings

### 2.1 Platform parsing and shared helper boundary

Pinned source: [`drivers/ufs/host/ufshcd-pltfrm.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufshcd-pltfrm.c)

- `ufshcd_populate_vreg()` reads `<name>-supply` and, unless `skip_current` is true, `<name>-max-microamp`. It does not read `vcc-voltage-level`.
- `ufshcd_parse_regulator_info()` calls the helper for `vdd-hba`, `vcc`, `vccq`, and `vccq2`.
- `ufshcd_populate_vreg()` is exported with `EXPORT_SYMBOL_GPL`.

The exported helper has another in-tree caller: [`drivers/ufs/host/ufs-mediatek.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufs-mediatek.c). The MediaTek path calls it using version-dependent names such as `vcc-ufsX` and `vcc-optX`, then obtains/enables the selected regulator.

**Integration consequence:** do not hard-code a DBY-W09/SM8250-only `vcc-voltage-level` parser into the exported generic helper, and do not change the helper signature without an explicit cross-host compatibility review. A safer design is to parse the property in the standard platform regulator-info path specifically after populating the regular `vcc` descriptor, or through a narrowly named helper invoked only for that descriptor. Keep MediaTek's dynamically named supply path unchanged.

### 2.2 UFS regulator descriptor

Pinned source: [`include/ufs/ufs.h`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/ufs/ufs.h)

The pinned `struct ufs_vreg` contains:
- regulator handle;
- supply name;
- `always_on` and `enabled` state;
- `max_uA`.

It has no `min_uV` or `max_uV` members. `struct ufs_vreg_info` separately stores `vcc`, `vccq`, `vccq2`, and `vdd_hba`.

Any implementation therefore needs a real place to retain the parsed VCC range and enough state to know whether that consumer request is currently held. Do not conflate “the regulator enable reference was dropped” with “the voltage request was successfully released.”

### 2.3 Current enable / disable lifecycle

Pinned source: [`drivers/ufs/core/ufshcd.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c), around `ufshcd_config_vreg_load()`, `ufshcd_config_vreg()`, `ufshcd_enable_vreg()`, and `ufshcd_disable_vreg()`.

Current behavior:
- `ufshcd_config_vreg_load()` calls `regulator_set_load()` only when a maximum current is configured.
- `ufshcd_config_vreg()` first checks `regulator_count_voltages()`; if it is positive, it configures DRMS load. It does not call `regulator_set_voltage()`.
- Enable path: apply `ufshcd_config_vreg(..., true)`, then call `regulator_enable()`, then mark `vreg->enabled = true`.
- Disable path: call `regulator_disable()` first. If that succeeds, call `ufshcd_config_vreg(..., false)`; the return value of this configuration-release call is deliberately ignored, and then `vreg->enabled` is set false.

**New risk when voltage requests are restored:** if the disable-side configuration function also releases the VCC minimum-voltage request, the current ignored-error behavior would silently permit a stale request to remain. This is materially different from merely logging a load optimization failure: a retained minimum-voltage request can continue constraining the shared regulator even though the UFS consumer no longer holds its enable reference.

The implementation should:
- track the voltage request independently from `enabled` (for example, a dedicated request-active state);
- check and report voltage-release errors instead of silently discarding them;
- define a retry/cleanup policy for a failed release without falsely claiming that the regulator enable reference is still held;
- define rollback if the voltage request succeeds but a subsequent DRMS-load setup or `regulator_enable()` fails;
- preserve the existing `always_on` semantics and ensure setup rollback does not accidentally drop a request that is intentionally retained.

This report does not prescribe a specific state-machine implementation. 2号 AI should select the minimal robust shape consistent with the UFS core's existing lifecycle and then test it.

## 3. Legacy behavior and regulator API compatibility

Legacy Qualcomm references used by ROUND82:
- [Legacy Qualcomm UFS platform parser](https://android.googlesource.com/kernel/msm.git/%2B/313705e35923007fe451e4512cabb501179380de/drivers/scsi/ufs/ufshcd-pltfrm.c): parses `vcc-voltage-level` as exactly two 32-bit cells for the VCC rail and stores the min/max values.
- [Legacy Qualcomm UFS core](https://android.googlesource.com/kernel/msm/%2B/f24e1ee001e0515f2a60ca6d97a75fcc0c532a07/drivers/scsi/ufs/ufshcd.c): requests the VCC voltage range using `regulator_set_voltage()`; when relaxing the request on power-off it uses a zero minimum while retaining the maximum bound.

The [Linux regulator consumer API documentation](https://www.kernel.org/doc/html/next/driver-api/regulator.html) states that:
- regulator enable/disable calls are reference-counted and must be balanced;
- consumer voltage configuration may be performed while the regulator is enabled or disabled;
- `regulator_set_voltage()` accepts a minimum/maximum interval.

Thus, applying the VCC voltage range before `regulator_enable()`, and relaxing it after a successful `regulator_disable()`, is compatible with the documented API and mirrors the legacy sequence. The API also warns that `regulator_disable()` does not guarantee the physical rail turns off, because other consumers or machine constraints may keep it enabled. Releasing the UFS consumer's own voltage vote must therefore be treated as distinct from physically shutting off PM8150 L17.

## 4. DBY-W09-specific candidate constraints

ROUND82 recorded the current board candidate values:
- UFS VCC consumer range: `vcc-voltage-level = <2504000 2950000>` (2.504–2.950 V).
- PM8150 L17 provider range: 2.496–3.008 V.

The provider interval is wider and is not a substitute for the narrower UFS consumer request. The candidate already has a VCC regulator phandle to PM8150 L17, so the standard VCC consumer descriptor is the relevant place to hold this request. This report does not independently validate the electrical correctness of the chosen interval; that remains dependent on the original platform evidence and the candidate's documented constraints.

Handling conditions that need an explicit implementation decision:
- If `vcc-voltage-level` is present but there is no `vcc-supply` phandle, the driver has no VCC consumer regulator handle on which to enforce the request. Treat this as a contradictory configuration (prefer a clear probe error or another explicitly justified policy), not as successful enforcement.
- A regulator may not support adjustable voltage. The implementation must define and log/validate this case rather than assume that merely obtaining a regulator handle makes the interval enforceable. For this DBY-W09 path, verify the actual PM8150 L17 regulator ops in the pinned source.
- Keep provider constraints and consumer request separate; do not widen the UFS range to the provider's broader interval to avoid an API/schema problem.

## 5. Binding and validation guidance

The driver and binding must land together. A schema-only addition would hide the current mismatch without restoring behavior; a driver-only addition would leave ROUND27's schema failure unresolved.

Potential schema placement:
- Put the property in `qcom,ufs-common.yaml` only if its semantics are intentionally supported by all covered Qualcomm UFS consumers.
- Otherwise, keep it in the narrowest host-specific Qualcomm schema that accurately represents the intended users, such as the SM8250/SC7180-compatible host binding.
- Whichever location is selected, specify exactly two unsigned 32-bit microvolt cells, min > 0, min <= max, and document that it is the UFS VCC consumer operating range.
- The schema must reject malformed lengths and should not silently bless the property without matching driver consumption.

Other ROUND81 schema errors remain separate work:
- `huawei,dby-w09` needs a correct SM8250 board compatible binding/allow-list entry.
- The five bootloader-owned `/rootparam` vendor properties need a narrowly selected binding with accurate string/u32-array types; do not add a speculative compatible to `/rootparam` merely to suppress diagnostics.

## 6. Suggested validation matrix for 2号 AI and the test Agent

At minimum, cover:

1. Property absent: preserve existing generic ACK behavior and no voltage request.
2. Valid two-cell interval: parse exact min/max values for VCC only.
3. Invalid lengths (one cell, three cells, malformed/empty property), zero minimum, and min greater than max: fail parsing clearly; do not silently use a wider default when a present property is invalid.
4. VCC supply absent while the interval is present: explicit error/policy; no false PASS.
5. Adjustable PM8150 L17 path: request accepted and later relaxed; verify the consumer request lifecycle.
6. Non-adjustable/fixed regulator: explicit, documented handling.
7. Voltage request succeeds but later load setup or regulator enable fails: rollback or retain state in a deliberate, diagnosable way.
8. Regulator disable fails: keep the enabled/request state coherent.
9. Regulator disable succeeds but voltage-request release fails: record a distinct pending/stale request state and make cleanup/retry behavior observable.
10. `always_on`, repeated enable/disable, setup rollback, and suspend/resume interactions.
11. Other UFS host users of `ufshcd_populate_vreg()`, especially MediaTek version-dependent VCC rails, remain behaviorally unchanged.

Recommended validation order:
- static diff review and real patch application on a disposable exact ACK worktree;
- `checkpatch` and relevant UFS binding `dt_binding_check`;
- base/composite DTB build and targeted `dtbs_check` / `dt-validate`;
- focused tests for parsing/state transitions where the source tree offers a suitable harness;
- full Kleaf Image build only after the source and config gates are ready.

## 7. Scope and ownership

**This is a [1号 AI research/review report].** It is intended for 2号 AI to evaluate while continuing its independent implementation work.

- 1号 AI: source analysis and review only in this round.
- 2号 AI: decides whether/how to implement the design, owns any implementation patch.
- Testing Agent: test executor only, and only after receiving a distinct `AGENT_TEST_TASK.md` scoped to the resulting patch.
- No task is being assigned to the testing Agent by this report.

No source, DTS, binding, patch, build configuration, branch, or protected PR was modified. No patch was applied, no compiler/schema/test command was run, no device was accessed, and no boot/flash operation occurred.

**Final status:** the UFS VCC consumer voltage-range omission is confirmed in the pinned ACK source; the shared-helper and disable-error handling constraints are now explicit. Driver + binding remediation remains pending 2号 AI's implementation decision and later test evidence. ROUND27 schema remains NOT CLEAN until all outstanding diagnostics are remediated.
