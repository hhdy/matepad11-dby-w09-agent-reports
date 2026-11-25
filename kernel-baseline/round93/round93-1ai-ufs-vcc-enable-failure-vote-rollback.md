# ROUND93 — 1号 AI source review: UFS VCC voltage/load votes must be unwound when regulator enable fails

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, under a separate AGENT_TEST_TASK.md  
**Pinned baseline:** ACK android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Related records:** ROUND84, ROUND88, ROUND89, ROUND90, ROUND91

## 1. Executive result

The fixed ACK UFS enable path has a rollback gap that becomes important once a VCC voltage request is added:

1. UFS calls its regulator configuration helper before calling regulator_enable().
2. The configuration helper can successfully store a DRMS load request while the regulator consumer is still disabled.
3. A VCC voltage request added by ROUND84/88 would likewise be applied before enable.
4. If regulator_enable() then fails, the UFS descriptor's enabled flag remains false.
5. The subsequent generic setup rollback calls ufshcd_disable_vreg(), but that function returns immediately when enabled is false. It does not run config(false).

Therefore, a successful voltage request can remain active after the enable attempt failed, and the stored DRMS load request can remain in the regulator consumer handle. The voltage request must be cleaned up independently of the enable-reference flag.

**Recommendation to 2号 AI:** introduce explicit request-state tracking and a failed-enable unwind path. Do not make release/relaxation conditional solely on vreg->enabled. The rollback must handle the case where no regulator_enable reference was acquired.

## 2. Exact pinned ACK UFS sequence

Source: [ACK drivers/ufs/core/ufshcd.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c).

Current generic behavior:

- ufshcd_enable_vreg() checks for a descriptor and returns if already enabled.
- It calls ufshcd_config_vreg(dev, vreg, true).
- Only when config succeeds does it call regulator_enable(vreg->reg).
- Only when regulator_enable() succeeds does it set vreg->enabled = true.
- If either configuration or regulator_enable() fails, the function logs the error and returns while vreg->enabled remains false.
- ufshcd_setup_vreg(hba, true) enables VCC, then VCCQ, then VCCQ2. If a later enable fails, its rollback calls ufshcd_toggle_vreg(..., false) for all three rails.
- ufshcd_disable_vreg() begins by returning if vreg is absent, disabled, or always-on. Therefore a failed enable attempt with enabled still false skips the config(false) cleanup.

This is the key distinction: the core's managed regulator handle can already hold voltage/load consumer requests even though the UFS code never marked the descriptor enabled.

## 3. Why this matters after ROUND84/88

The VCC implementation proposed in ROUND84/88 needs to apply the UFS consumer voltage interval before the first regulator_enable():
- on-state request: [2,504,000, 2,950,000] uV;
- off-state/relaxed request: [0, 2,950,000] uV (ROUND89).

If applying the interval succeeds but a subsequent DRMS load setup fails, or regulator_enable() fails, the UFS descriptor still has enabled=false. The current rollback helper therefore does not relax the voltage interval. The VCC regulator can remain constrained by a UFS consumer that never acquired an enable reference.

The DRMS load has a related but different regulator-core behavior:
- regulator_set_load() called while the consumer is disabled stores uA_load without running DRMS immediately.
- regulator_enable() calls the DRMS update after incrementing the consumer enable count and before the hardware enable.
- if that DRMS update fails at the consumer-enable stage, regulator core decrements the enable count again, but the stored uA_load value is not automatically reset to zero.
- if a later hardware-enable step fails, the regulator core also attempts consumer-disable/DRMS rollback; an error from that rollback path can be ignored by the core (ROUND90).

The UFS driver therefore needs to clean up or deliberately retain the stored load vote after a failed enable, independent of whether it owns an enable reference.

## 4. Suggested state model

2号 AI should separate at least these facts for each DRMS/voltage-controlled supply:

- enable-reference state: whether regulator_enable() completed successfully for this UFS consumer;
- voltage-request state: whether the ON interval was installed, and whether it was successfully relaxed to the OFF interval;
- DRMS-load state: whether the requested load value is currently stored on this regulator handle;
- pending-cleanup state: whether a voltage relaxation or load-zero request failed and needs a later retry/report.

A single bool named enabled is insufficient to represent all four.

### 4.1 Failed enable unwind

Conceptual sequence:

1. Parse and validate the optional VCC interval before ufshcd_init() (ROUND88/91).
2. Before enable, apply the ON voltage interval.
3. Apply the ON DRMS load vote.
4. Call regulator_enable().
5. If configuration or regulator_enable() fails before an enable reference is acquired:
   - do not call regulator_disable() for a reference that was never acquired;
   - attempt DRMS load zero while the consumer is disabled (this updates the stored vote without a hardware DRMS transition);
   - relax VCC voltage to [0, max_uV];
   - track each cleanup result independently.
6. If any cleanup step fails, preserve explicit pending-cleanup state and a diagnostic. Do not pretend that the vote was released.

This unwind must be available to ufshcd_enable_vreg() itself or an equivalent helper; relying on ufshcd_setup_vreg() to call ufshcd_disable_vreg() is not sufficient when enabled remains false.

### 4.2 Normal disable

For DRMS-capable rails, evaluate ROUND90's safer candidate:
- while the reference is still held, request load zero;
- if load-zero fails, abort disable and retain the old load/reference;
- if it succeeds, call regulator_disable();
- on hardware-disable failure, attempt to restore the on-state load and track restoration failure;
- after successful VCC disable, relax the voltage request to [0, max_uV].

Other post-decrement regulator-core errors (coupling/upstream parent) still need separate review if such topology is added.

## 5. Required tests

2号 AI's implementation and the later testing Agent task should cover:

1. Voltage request succeeds, load request fails: voltage request is relaxed even though enabled was never true.
2. Voltage and load requests succeed, regulator_enable() fails at DRMS setup: no enable reference remains; load is reset and voltage lower bound is relaxed.
3. DRMS setup succeeds but provider hardware enable fails: verify rollback of load and voltage requests, including error in the core's consumer-disable DRMS rollback.
4. Later rail (VCCQ or VCCQ2) enable fails after VCC succeeded: VCC disable and vote cleanup use the tracked enable/request states correctly.
5. Cleanup voltage relaxation fails: state remains pending and is reported; no false claim that the voltage request is released.
6. Cleanup load-zero fails: state remains pending and is reported separately from voltage state.
7. A second enable attempt after failed first attempt does not inherit an unintended stale minimum-voltage request or stale high load vote.
8. Normal disable path continues to preserve ROUND89's [0, max_uV] OFF interval.
9. L17 and L6 DRMS HPM→LPM error path follows ROUND90's reviewed ordering; include the L6 VCCQ + VDDP shared-consumer case.
10. MediaTek dynamic VCC users without vcc-voltage-level retain existing behavior.

## 6. Ownership and boundaries

**This is a [1号 AI read-only source review] for 2号 AI.**
- 1号 AI: source-path and rollback review.
- 2号 AI: owns implementation and patch changes.
- Testing Agent: test execution only, after a separate AGENT_TEST_TASK.md.
- The user is not asked to run any command.

No source, DTS, binding, patch, config, 2号 AI branch, protected branch or PR was modified. No patch was applied, no build/schema/test command was run, and no device was accessed.

**Final status:** UFS regulator vote cleanup must run even when regulator_enable() never succeeded and the UFS enabled flag remains false. The implementation needs separate enable-reference, voltage-request, DRMS-load and pending-cleanup state. ROUND27 schema remains NOT CLEAN until the driver+binding fixes and independent schema remediation are implemented and validated.
