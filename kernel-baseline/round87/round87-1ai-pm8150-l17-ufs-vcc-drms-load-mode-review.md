# ROUND87 — 1号 AI source review: PM8150 L17 DRMS load vote for UFS VCC

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, after a separate test task is issued  
**Pinned baseline:** ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Related records:** ROUND82, ROUND84, ROUND86

## 1. Executive result

ROUND87 checks a separate but adjacent question: how the existing UFS `vcc-max-microamp` value interacts with PM8150 L17 after ROUND84's VCC voltage-range request is restored.

**Source-level result:** the candidate's `vcc-max-microamp = <800000>` is consumed by the pinned ACK UFS core as a regulator DRMS load vote, not as a hardware current-limit programming request. PM8150 L17's PMIC5 PLDO DRMS implementation selects normal/HPM mode when aggregated load is at least 10,000 uA. The candidate L17 node permits consumer load votes and supports both LPM and HPM. Thus the configured 800,000 uA request crosses the L17 HPM threshold.

This should remain separate from the VCC voltage min/max request:
- `vcc-voltage-level` → voltage constraint/vote, enforced using `regulator_set_voltage()` after ROUND84 implementation.
- `vcc-max-microamp` → UFS's DRMS load vote, enforced using `regulator_set_load()` in the existing ACK UFS core.

A patch that restores VCC voltage control must preserve the existing DRMS path, not replace it.

## 2. Exact pinned ACK UFS consumer behavior

Source: [ACK `drivers/ufs/core/ufshcd.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c).

In `ufshcd_populate_vreg()`, the platform parser reads `<name>-max-microamp` into `vreg->max_uA`; for the ordinary `vcc` descriptor the property name is `vcc-max-microamp`.

The core's existing `ufshcd_config_vreg_load()`:
- returns without a load vote when the descriptor is absent or `max_uA` is zero;
- otherwise calls `regulator_set_load(vreg->reg, ua)`;
- reports a negative result.

`ufshcd_config_vreg()` applies `vreg->max_uA` on enable and zero on disable (provided `regulator_count_voltages()` is positive). The enable path applies this DRMS request before `regulator_enable()`; the disable path drops the enable reference before applying the zero-load request.

The property is therefore an input to the regulator framework's load aggregation/DRMS policy. It is not the same thing as a PMIC hardware current-limit register or proof that the UFS device continuously draws exactly 800 mA.

## 3. Exact pinned ACK PM8150 L17 DRMS behavior

Source: [ACK `drivers/regulator/qcom-rpmh-regulator.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c).

- PM8150 LDO17 uses `pmic5_pldo`.
- `pmic5_pldo` sets `hpm_min_load_uA = 10000`.
- Its ops are `rpmh_regulator_vrm_drms_ops`, which includes `get_optimum_mode = rpmh_regulator_vrm_get_optimum_mode`.
- `rpmh_regulator_vrm_get_optimum_mode()` selects `REGULATOR_MODE_NORMAL` when aggregated load is greater than or equal to the regulator's `hpm_min_load_uA`, otherwise `REGULATOR_MODE_IDLE`.
- The candidate L17 provider node declares `regulator-allow-set-load`, permits LPM and HPM, and starts in LPM.

Therefore, if the 800,000 uA UFS VCC load request is accepted by the regulator core, it is far above the 10,000 uA HPM threshold and selects normal/HPM mode. When the UFS consumer later sets its load vote to zero, the L17 optimum mode may return to idle/LPM if no other consumer's aggregated load keeps the threshold crossed.

Other regulator consumers may contribute to the regulator's aggregate load; this report does not assume UFS is the only consumer.

## 4. Integration implications for 2号 AI

1. Preserve both operations on the VCC descriptor: the new consumer voltage interval and the existing DRMS load vote.
2. Do not reinterpret `vcc-max-microamp` as a fixed PMIC over-current limit or use it to replace `vcc-voltage-level`.
3. Preserve the candidate's `regulator-allow-set-load` and LPM/HPM allowed-mode declarations unless source evidence justifies changing them.
4. Coordinate failure handling: if the new voltage request succeeds but the DRMS load vote fails, or a later `regulator_enable()` fails, unwind the voltage request without losing track of any failed rollback. ROUND84's separate active-state/error-reporting requirement remains.
5. On disable, the driver should keep voltage-vote relaxation and zero-load application distinct and report failures. A failure to release the voltage lower bound must not be masked by a successful zero-load request, and vice versa.
6. The UFS `vcc-max-microamp` name should be documented as the load vote value used by the UFS core. It is not an independently measured current draw.

## 5. Boundaries

This is a **[1号 AI read-only source review]** for 2号 AI. 2号 AI owns implementation changes. Testing Agent remains test-only and may act only under a separate `AGENT_TEST_TASK.md`.

No source, DTS, binding, patch, config, 2号 AI branch or protected branch was modified. No patch application, build, schema validation, load measurement, regulator measurement, or device test was run.

**Final status:** the existing UFS VCC DRMS path is source-consistent with the PM8150 L17 DRMS provider contract. The 2号 AI VCC voltage patch must preserve this independent load vote and handle failure/cleanup for both vote types. This does not establish the actual current drawn by the UFS device or close HOS ARC / PMIC physical-input gates.
