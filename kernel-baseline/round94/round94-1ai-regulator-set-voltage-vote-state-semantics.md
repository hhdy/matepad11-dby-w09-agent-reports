# ROUND94 — 1号 AI source review: regulator_set_voltage request-state semantics for UFS VCC

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, under a separate AGENT_TEST_TASK.md  
**Pinned baseline:** ACK android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Related records:** ROUND84, ROUND86, ROUND88, ROUND89, ROUND93

## 1. Executive result

This review answers two driver-implementation questions:
- When should UFS update its internal voltage-request state after calling regulator_set_voltage()?
- Should the driver reject a supply merely because regulator_count_voltages() is zero?

Pinned ACK regulator core shows:

1. For the DBY-W09 candidate's current PM8150 L17/L6 constraints (no regulator-max-step-microvolt property), regulator_set_voltage_unlocked() saves the old consumer min/max, installs the new request, calls regulator_balance_voltage(), and restores the old consumer range if the balance/programming operation fails.
2. Therefore the UFS driver should update its request-state enum/flag only after regulator_set_voltage() returns success. On a negative result for this current candidate, keep the previous request state.
3. The regulator core has a deliberate fixed/non-adjustable-regulator path: when voltage changes are not permitted, if the current output voltage is already inside the requested interval, it records the consumer interval and returns success. Thus a generic implementation should not use regulator_count_voltages() <= 0 as an unconditional reason to reject the request; it should call regulator_set_voltage() and handle the actual result.
4. The PM8150 L17 used by DBY-W09 is adjustable (ROUND86), so this fixed-regulator acceptance path is not needed to make the current board request work. It is nevertheless important to avoid an unnecessarily restrictive generic driver design.

## 2. Exact pinned ACK behavior

Source: [ACK drivers/regulator/core.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c).

### 2.1 Non-adjustable regulator overlap path

In regulator_set_voltage_unlocked():
- If REGULATOR_CHANGE_VOLTAGE is not permitted, the core reads the current output voltage.
- If min_uV <= current_uV <= max_uV, it stores the requested consumer interval and returns success without changing hardware.
- If the current output is outside the interval, it proceeds to the normal set_voltage/set_voltage_sel capability checks, which can return -EINVAL when no adjustable operation exists.

This is intentional API behavior, not a silent bypass: the requested range is still recorded, and the regulator output already satisfies it.

### 2.2 Current DBY-W09 L17/L6 error rollback

For an adjustable regulator:
- the core sanity-checks that set_voltage or set_voltage_sel exists;
- checks the requested interval against machine constraints;
- saves the previous consumer min/max;
- installs the new consumer min/max;
- calls regulator_balance_voltage();
- if balancing/programming returns a negative error, restores the previous consumer min/max.

Relevant pinned lines: [regulator_set_voltage_unlocked(), around lines 3820–3908](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L3820-L3908).

The extra max_uV_step loop can perform repeated balance operations after the initial successful update. The DBY-W09 candidate L17 and L6 provider nodes do not set regulator-max-step-microvolt, so the default max_uV_step is zero and this additional loop is not entered for the current candidate.

This supports treating a negative regulator_set_voltage() result as failure to install the new consumer range for this current L17/L6 configuration. It is not a general guarantee for every future regulator configuration with step-limited voltage transitions or upstream supply dependencies.

## 3. Candidate voltage request

The DBY-W09 board candidate has:
- UFS VCC ON range: 2,504,000–2,950,000 uV;
- UFS VCC OFF/relaxed range from ROUND89: 0–2,950,000 uV;
- PM8150 L17 provider range: 2,496,000–3,008,000 uV.

ROUND86 independently established that L17 has a voltage-adjustable PMIC5 PLDO table and selectable voltages from 2.504 V to 2.944 V inside the UFS ON interval. The candidate provider has no regulator-max-step-microvolt constraint.

Therefore:
- ON request success should change the UFS software state to ON_RANGE.
- OFF/relaxed request success should change it to OFF_RELAXED.
- A negative return should leave the previous software request state intact, while logging the error and retaining any pending-cleanup indication as appropriate.
- Do not mark the request relaxed before the OFF call succeeds.

## 4. Implementation guidance for 2号 AI

1. Do not gate range-request application solely on regulator_count_voltages() > 0. Call regulator_set_voltage() when the property is present and allow the regulator core to decide whether the request is satisfiable by adjustment or by an already-in-range fixed output.
2. Propagate regulator_set_voltage() failure. Do not proceed to the regulator enable step if the required ON range could not be installed.
3. Update UFS software state only after successful API return.
4. Keep voltage request state separate from enable-reference and DRMS load state (ROUND84/89/90/93).
5. For the current PM8150 L17/L6 candidate, a negative API return restores the prior stored consumer interval at regulator core level because max_uV_step is unset. Do not invent an independent selector rollback mechanism for this specific case.
6. If a future board adds regulator-max-step-microvolt, a real upstream input supply, or regulator coupling, re-audit the non-atomic/secondary error paths before claiming identical semantics.
7. Test both the ON range and OFF relaxed range, including forced provider programming failure and a repeated call with the same requested range (core no-op path).

## 5. Ownership and boundaries

**This is a [1号 AI read-only regulator API review] for 2号 AI.**
- 1号 AI: pinned regulator-core source analysis.
- 2号 AI: owns driver/binding implementation.
- Testing Agent: test executor only under a separate AGENT_TEST_TASK.md.
- The user is not asked to run commands.

No source, DTS, binding, patch, config, 2号 AI branch, protected branch or PR was modified. No patch application, compiler, dt-schema, electrical measurement or device operation was run.

**Final status:** for the current DBY-W09 L17/L6 provider constraints, failed voltage requests restore the previous consumer voltage interval; UFS software state should change only after successful regulator_set_voltage(). Do not reject every non-adjustable regulator without giving the regulator core a chance to accept an already-satisfied interval. ROUND27 schema remains NOT CLEAN.
