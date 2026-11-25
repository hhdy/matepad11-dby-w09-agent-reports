# ROUND89 — 1号 AI correction: legacy UFS VCC disable relaxes the lower bound, it does not clear the entire voltage vote

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, after a separate test task is issued  
**Pinned target:** ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Related records:** ROUND82, ROUND84, ROUND87, ROUND88

## 1. Correction / clarification

ROUND84 correctly identified that voltage-request release can fail and that such failures must not be silently ignored. This report sharpens the exact legacy Qualcomm semantics:

**When the UFS VCC rail is turned off, the legacy Qualcomm driver sets the consumer voltage request to `[0, vcc_max_uV]`; it does not remove the entire voltage request by setting the maximum to `INT_MAX`.**

The minimum voltage bound is relaxed to zero, while the upper bound remains the parsed VCC maximum. The existing current/load request is separately changed to zero. The voltage lower-bound update and DRMS load update are separate regulator API operations and can fail independently.

Do not call this a complete release of the consumer's voltage interval. It is a **lower-bound relaxation with the upper bound retained**.

## 2. Legacy Qualcomm evidence

Source: [legacy Qualcomm `drivers/scsi/ufs/ufs-qcom.c`](https://android.googlesource.com/kernel/msm/%2B/4e3173f8620be201225f35c6d45e962e5b72d9d4/drivers/scsi/ufs/ufs-qcom.c).

The historical `ufs_qcom_config_vreg(dev, vreg, on)` sequence, when regulator voltage control exists, is:

1. `min_uV = on ? vreg->min_uV : 0`;
2. `regulator_set_voltage(reg, min_uV, vreg->max_uV)`;
3. `uA_load = on ? vreg->max_uA : 0`;
4. `regulator_set_load(reg, uA_load)`.

The corresponding `ufs_qcom_enable_vreg()` calls config(on) before `regulator_enable()`.

The corresponding `ufs_qcom_disable_vreg()` calls `regulator_disable()` first, then config(false); the function only changes its `enabled` software flag after config(false) succeeds.

Another historical Qualcomm UFS core implementation uses the same lower-bound relaxation expression in its generic regulator configuration path: [legacy `drivers/scsi/ufs/ufshcd.c`](https://android.googlesource.com/kernel/msm.git/%2B/330705db41eb77d77476c5fccf3527f5db1d1525/drivers/scsi/ufs/ufshcd.c).

## 3. What this means for DBY-W09

The DBY-W09 candidate has:
- VCC min = 2,504,000 uV;
- VCC max = 2,950,000 uV;
- VCC load value = 800,000 uA.

Legacy-style requested states are therefore:

| State | Voltage request | DRMS load request |
|---|---|---|
| VCC on | 2,504,000–2,950,000 uV | 800,000 uA |
| VCC off | 0–2,950,000 uV | 0 uA |

The off-state row is deliberately not `0–INT_MAX`. The UFS consumer still has a maximum-voltage ceiling. On a shared regulator, this retained maximum can continue to constrain aggregation with other consumers. Whether that ceiling is desired for DBY-W09 is a legacy-contract decision; do not silently widen it to `INT_MAX` without evidence and a reviewed semantic change.

## 4. Error-state implications for ACK implementation

The ACK 6.18.33 generic `ufshcd_disable_vreg()` currently:
1. calls `regulator_disable()`;
2. if that succeeds, calls `ufshcd_config_vreg(..., false)`;
3. ignores the config(false) result;
4. sets `vreg->enabled = false`.

A new voltage + load implementation must not retain that blanket ignored-error behavior. It also should not blindly copy the legacy Qualcomm software-state behavior, where a config(false) error can leave `enabled` true even though `regulator_disable()` has already succeeded and dropped the enable reference.

Recommended state separation:
- **enable reference state:** whether this UFS consumer still owns a successful `regulator_enable()` reference;
- **voltage interval state:** whether the legacy on-range or off-relaxed range was successfully applied;
- **DRMS load state:** whether the on-load or zero-load request was successfully applied.

After `regulator_disable()` succeeds, the enable-reference state must become false regardless of whether later voltage relaxation or load-zero requests succeed. The two configuration failures must be logged/returned and tracked separately so a retry or cleanup path can correct them without falsely claiming the rail is still enabled.

If voltage relaxation fails, the consumer may still have the old minimum voltage request active. If load-zero fails, the old DRMS load vote may remain. A successful update to one does not prove the other succeeded.

The first-enable path must apply both on-state requests before `regulator_enable()`, per ROUND88. If either configuration request fails, do not proceed as though both requests were established; unwind any successfully applied vote according to a tracked rollback policy.

## 5. Recommendation to 2号 AI

- Preserve the legacy `[min_uV, max_uV]` on-state and `[0, max_uV]` off-state contract unless the implementation explicitly chooses and justifies a different contract.
- Preserve `max_uA` on-state and zero-load off-state as a separate DRMS vote.
- Track request state independently from regulator enable-reference state.
- Keep error returns/diagnostics for voltage and load updates separate.
- Do not make the property vanish from DTS/schema merely to pass dt-schema.
- Ensure all new parsing occurs before first VCC regulator enable (ROUND88); do not put first-time parsing solely in `ufs_qcom_init()`.

## 6. Ownership and boundaries

**This is a [1号 AI read-only clarification report] for 2号 AI.**
- 1号 AI: legacy/pinned source comparison and state-machine review.
- 2号 AI: implementation owner.
- Testing Agent: test-only, with a separate `AGENT_TEST_TASK.md`.
- The user is not asked to execute commands.

No ACK source, DTS, binding, patch, config, 2号 AI branch or protected branch was modified. No patch application, build, schema test, electrical measurement or device operation occurred.

**Final status:** legacy VCC disable semantics are now precisely recorded: relax minimum to zero, retain maximum, and zero the load request. These are two independent operations with separate failure states. ROUND27 schema remains NOT CLEAN until the implementation and all remaining binding fixes are applied and verified.
