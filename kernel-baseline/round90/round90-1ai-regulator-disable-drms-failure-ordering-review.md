# ROUND90 — 1号 AI source review: avoid post-decrement DRMS failures during UFS regulator disable

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, under a separate `AGENT_TEST_TASK.md`  
**Pinned baseline:** ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Related records:** ROUND52, ROUND84, ROUND86, ROUND87, ROUND88, ROUND89

## 1. Executive result

The fixed ACK regulator core contains a subtle but concrete error-state hazard:

**`regulator_disable()` can return a negative DRMS error after it has already decremented the calling consumer's enable reference.** When this occurs, the UFS wrapper's simple `if (ret) keep vreg->enabled = true` logic can become inconsistent with regulator core state. A subsequent disable attempt may be unbalanced.

This is directly relevant to the DBY-W09 candidate:
- PM8150 L17 is a PMIC5 PLDO with a 10 mA HPM threshold. UFS VCC requests 800 mA. Turning VCC off changes the aggregate L17 load from HPM territory to below threshold.
- PM8150 L6 is a PMIC5 NLDO with a 30 mA HPM threshold. UFS VCCQ requests 800 mA, while the independent VDDP/REF_CLK consumer also holds L6 with a 100 uA vote. Turning VCCQ off can change aggregate L6 load from HPM territory to only 100 uA, below threshold.
- Both L17 and L6 candidates permit set-load and LPM/HPM operation. Their PMIC5 regulator ops use DRMS and RPMh mode requests.

**Recommended design candidate for 2号 AI:** clear the particular UFS consumer's DRMS load vote while its regulator enable reference is still held, then call `regulator_disable()`. If setting load to zero fails, ACK regulator core restores the previous stored load and the UFS consumer reference has not yet been decremented, so the caller can safely abort the disable. If the load-zero operation succeeds, `_regulator_handle_consumer_disable()` will no longer need to perform the same DRMS transition after decrementing the reference. This removes the specific post-decrement DRMS failure path.

This is a source-backed design recommendation, not an implementation authorization. It changes the order of the legacy off sequence and must be evaluated carefully by 2号 AI.

## 2. Exact pinned ACK regulator-core behavior

Source: [ACK `drivers/regulator/core.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c).

### 2.1 What `regulator_set_load()` does

At `regulator_set_load()`:
- The consumer's `uA_load` is updated.
- If that consumer's `enable_count` is nonzero and the load changed, the core calls `drms_uA_update()` immediately.
- If DRMS update fails with a negative error, the core restores the previous `uA_load`.
- If that consumer is disabled, the function just stores the requested load; it does not immediately issue the DRMS mode update.
- Its documented return is 0 on success or a negative error on failure. It does not return a positive operating-mode enum.

Relevant source lines: [`regulator_set_load()` around lines 4948–4968](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L4948-L4968).

### 2.2 What `regulator_disable()` does

In `_regulator_disable()`, for a consumer's last enable reference:
1. If this is the last active consumer and status change is permitted, the core may first call the regulator hardware `disable()` and set the provider `use_count` to zero.
2. It then calls `_regulator_handle_consumer_disable()`.
3. That helper decrements the consumer's `enable_count`.
4. If the stored `uA_load` is nonzero and the consumer count has reached zero, it invokes `drms_uA_update()`.
5. If that DRMS update fails, the negative error is returned. **The consumer `enable_count` decrement is not rolled back.**

Relevant source lines:
- [`_regulator_handle_consumer_disable()` lines 2879–2895](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L2879-L2895)
- [`_regulator_disable()` lines 3019–3071](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L3019-L3071)
- [`regulator_disable()` lines 3074–3100](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L3074-L3100)

Thus a negative `regulator_disable()` return does not universally prove that the calling consumer's enable reference remains held. It may mean a later DRMS operation failed after the reference was already decremented. If the provider was the last active user, its physical disable may also already have succeeded. If it is shared, the provider can remain on for another consumer even though this consumer's reference has been dropped.

### 2.3 Why the error is possible on these PMIC5 regulators

`drms_uA_update()` sums the loads of enabled consumers and system load, gets the optimum mode, constrains it against provider-allowed modes, and calls the provider's `set_mode()`. A negative RPMh set-mode result is returned to its caller.

Relevant sources:
- [ACK `drms_uA_update()` lines 969–1061](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L969-L1061)
- [ACK RPMh regulator `rpmh_regulator_vrm_set_mode()`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c)
- [ACK `pmic5_pldo` and `pmic5_nldo` DRMS definitions](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c)

## 3. DBY-W09-specific trigger conditions

### 3.1 PM8150 L17 — UFS VCC

Pinned ACK:
- LDO17 uses `pmic5_pldo`.
- `hpm_min_load_uA = 10000` (10 mA).
- Its operation table includes the optimum-mode callback.
- Candidate L17 allows set-load and LPM/HPM modes.

Candidate consumer:
- `vcc-max-microamp = <800000>` (800 mA).
- This is far above the 10 mA HPM threshold.

When VCC is turned off and its load vote is removed, L17's aggregate may fall below the threshold. The core attempts HPM→LPM as part of consumer disable. If the synchronous RPMh mode request fails, `regulator_disable()` may return an error after VCC's enable reference has already been decremented.

### 3.2 PM8150 L6 — UFS VCCQ shared with VDDP/REF_CLK

Pinned ACK:
- LDO6 uses `pmic5_nldo`.
- `hpm_min_load_uA = 30000` (30 mA).
- Its operation table includes DRMS.
- Candidate L6 allows set-load and LPM/HPM modes.

Candidate consumers:
- UFS VCCQ: `vccq-max-microamp = <800000>` (800 mA).
- UFS VDDP/REF_CLK: `qcom,vddp-ref-clk-max-microamp = <100>` (100 uA).

ROUND52 establishes the VDDP consumer as a separate managed L6 consumer reference. Once VCCQ is disabled, VDDP can remain enabled with only its 100 uA load vote. That is below L6's 30 mA threshold, so removing the VCCQ 800 mA vote can cause HPM→LPM. A failed RPMh mode update can therefore occur during VCCQ consumer disable even though L6 remains physically enabled for VDDP.

The candidate explicitly marks L6 as `regulator-allow-set-load` and permits LPM/HPM. These are not hypothetical properties inferred from another device.

### 3.3 S4 / UFS VCCQ2

The pinned PM8150 S4 descriptor uses `pmic5_hfsmps510`, whose ops are `rpmh_regulator_vrm_ops`, not the DRMS variant. It therefore does not have the same PMIC5 PLDO/NLDO `get_optimum_mode` error trigger under the present candidate. Keep this rail's separate behavior rather than applying L17/L6 assumptions indiscriminately.

## 4. Safer disable-order candidate for 2号 AI to evaluate

Because `regulator_set_load()` executes DRMS while the consumer's enable reference is still held, and rolls the stored load back on a negative DRMS error, a safer candidate order for DRMS-capable UFS rails is:

1. While the consumer is still enabled, call `regulator_set_load(reg, 0)`.
2. If this returns a negative error, abort disable. The previous load vote is restored by regulator core and the consumer enable reference remains held.
3. If it succeeds, call `regulator_disable(reg)`. Since this consumer's stored load is now zero, `_regulator_handle_consumer_disable()` does not need to perform a second DRMS update after decrementing the reference.
4. If regulator disable fails at the actual hardware/status step, the consumer reference normally remains held; restore the configured on-state load before treating the consumer as active, and track/report if that restoration fails.
5. After a successful disable, apply the legacy off-state VCC voltage interval `[0, max_uV]` (for VCC only). Track a failure to relax the voltage lower bound independently from the already released enable reference and zeroed DRMS load.

The exact implementation must also account for:
- shared regulators where another consumer's vote remains active;
- `always_on` rails, which current ACK code deliberately skips;
- regulator coupling or a real upstream supply parent, which can still produce other post-decrement failures after the DRMS step. The current board candidate does not declare a verified physical parent input or a `regulator-coupled-with` relationship for L17/L6; any future such topology must be re-audited.
- best-effort/error handling on setup rollback and remove paths.

This ordering changes the historic sequence for the load vote (legacy code commonly zeroed load after `regulator_disable()`). The reason to evaluate the change is pinned ACK regulator-core ordering, not stylistic preference. It must be explicitly reviewed and tested rather than copied blindly.

## 5. Enable-side behavior is complementary

Pinned ACK `regulator_set_load()` called while disabled stores the load vote without running DRMS immediately. The subsequent `regulator_enable()`:
- increments the consumer enable count;
- then calls `drms_uA_update()` if this is the first enable reference and a load is stored;
- only afterward proceeds to the provider hardware enable.

This means the existing storage-first ON sequence of setting the UFS max load before `regulator_enable()` is correctly ordered: HPM request is applied before hardware enable. Preserve it when integrating VCC voltage constraints.

## 6. Implementation and test implications for 2号 AI

- Apply the same state-aware DRMS shutdown design to both generic UFS VCC (L17) and VCCQ (L6); do not patch only L17.
- Include the managed VDDP/REF_CLK L6 consumer in the aggregate-load scenario: VCCQ off while VDDP remains enabled at 100 uA.
- Test injected failure for L17 HPM→LPM and L6 HPM→LPM during load-zero while enabled. The expected result is that the failed `regulator_set_load(0)` restores the old vote and the UFS reference remains held, so no subsequent unbalanced disable occurs.
- Test successful load-zero followed by successful disable and off-state voltage relaxation for VCC.
- Test actual regulator hardware-disable failure after load-zero and restoration of the on-state load.
- Test shared L6 behavior with VDDP retained, and another consumer keeping aggregate load above/below threshold.
- Keep OFF VCC voltage request as `[0, 2.950 V]`, not `[0, INT_MAX]`, unless 2号 AI explicitly justifies a semantic change (ROUND89).
- Preserve separate state for voltage-range request, DRMS load request, and enable reference.
- Include the other regulator-core post-decrement paths (coupling/upstream parent) in design review if verified input parents or regulator coupling are added later.

## 7. Ownership and boundaries

**This is a [1号 AI read-only source-analysis report] for 2号 AI.**
- 1号 AI: source analysis and review only.
- 2号 AI: owns the driver/binding implementation and branch.
- Testing Agent: test execution only, under a separate `AGENT_TEST_TASK.md`.
- The user is not asked to run commands.

No ACK source, DTS, binding, patch, config, 2号 AI branch, protected branch, or PR was modified. No real patch apply, build, schema validation, PMIC measurement or device operation was performed.

**Final status:** pinned ACK regulator core can return a negative disable result after decrementing the consumer reference because DRMS mode update happens afterward. DBY-W09 UFS VCC/L17 and VCCQ/L6 hit the threshold-crossing pattern; L6 is shared with the independent VDDP consumer. The 2号 AI should evaluate moving each DRMS zero-load request before regulator_disable(), with explicit rollback, while preserving ROUND88 pre-enable voltage setup and ROUND89 off-state voltage semantics. ROUND27 schema remains NOT CLEAN until the complete implementation and binding fixes are applied and tested.
