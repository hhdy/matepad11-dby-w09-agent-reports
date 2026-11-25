# ROUND126 — AI1 proxy-consumer load-first teardown candidate

- Owner / patch author: **1号 AI（ChatGPT）**
- Implementation review scope: ACK regulator core + AI2 ROUND31/32/33 proxy-consumer implementation
- Validation executor: 用户本地测试 Agent（only identity/apply/source gates/checkpatch/compile/build; no code edits)
- Fixed ACK: aosp-mirror/kernel_common @ 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- AI2 source baseline used to derive the patch: Stage A 17-patch series at ai-parallel/stagea-port-until-boot@2f21233148a04afdd61e44b1be7688399967d9d0
- Candidate branch: ai1/round126-proxy-consumer-load-first

## 1. Finding

The current AI2 proxy-consumer implementation removes a proxy request in the following order:

1. regulator_disable(consumer->reg)
2. regulator_set_load(consumer->reg, 0)
3. optional regulator_set_voltage(..., 0, INT_MAX)
4. regulator_put(consumer->reg)

That order is present in the original ROUND31 helper and is unchanged by ROUND32 child-scoped mapping and ROUND33 self-target-only validation.

The pinned ACK regulator core has a relevant ordering:

- _regulator_handle_consumer_disable() decrements the consumer handle's enable_count first.
- If the consumer's stored uA_load is non-zero and that was its final enable reference, it calls drms_uA_update() after the decrement.
- regulator_set_load() on an enabled handle performs the DRMS update immediately; when this update fails, regulator core restores the previous stored load and returns the error.
- Therefore, proxy-consumer teardown can encounter the same post-decrement DRMS failure already identified in UFS VCC/VDDP teardown. It can return a negative regulator_disable() result after its own enable_count has already been decremented.

This is particularly relevant to the inspected HOS4.3 PM8150 L5/L9 children:
- both request qcom,proxy-consumer-enable;
- both declare qcom,proxy-consumer-current = 100000 (100mA);
- both provider groups declare qcom,mode-threshold-currents = <0 30000> (30mA);
- their proxy-supply group mapping resolves back to the corresponding owner child.
The Stage A proxy-consumer implementation turns those declarations into real regulator_set_load() and regulator_enable() votes. The 100mA request is not merely an unused metadata field after this Stage A change.

The teardown hook is used by both per-regulator regulator_unregister() and the late_initcall_sync bulk proxy-vote removal. Thus correcting the ordering affects both paths.

## 2. Candidate change

Patch:
kernel-baseline/round126/0001-proxy-consumer-load-first.patch

The patch moves the current-load vote removal before regulator_disable():

1. If current_uA > 0, call regulator_set_load(reg, 0) while the consumer enable reference is still held.
2. Record/log load-zero error as before, but retain the existing best-effort teardown behavior and continue to regulator_disable() because regulator_unregister() is a void teardown path that cannot be vetoed here.
3. If enable is requested, call regulator_disable() after the load-zero attempt.
4. Voltage-vote cleanup and regulator_put() remain in their existing order.

On the normal path, the failure-prone DRMS mode transition now occurs before the consumer enable_count decrement. This avoids the known post-decrement DRMS transition when load-zero succeeds.

## 3. Explicit limitations

- If regulator_set_load(0) itself fails, the regulator core restores the previous nonzero stored load. The void proxy-consumer unregister hook cannot abort regulator_unregister(); the patch therefore preserves the existing best-effort disable/put attempt. That exceptional path can still encounter ambiguous regulator errors or a nonzero-enable-count warning.
- A negative regulator_disable() result is not universally proof that the enable reference remains held. Generic regulator core can return a later error after decrement (e.g. parent supply or coupling paths). The inspected HOS4.3 L5/L9 tree has no coupling declarations and no ordinary input-parent phandles, but an out-of-DT alias is not independently proven absent.
- No force-disable, retry based on an ambiguous return, regulator-core API change, or fake parent-supply declaration is introduced.
- This is a source-ordering improvement, not runtime proof of the PMIC rail or proxy consumer behavior.

## 4. Exact fixed-source references

Pinned ACK:
- drivers/regulator/core.c:2879-2894 — _regulator_handle_consumer_disable() decrements enable_count before DRMS.
- drivers/regulator/core.c:3030-3070 — provider disable, consumer decrement, coupling/parent shutdown order.
- drivers/regulator/core.c:4950-4968 — regulator_set_load() updates DRMS while enabled and restores the old load on failure.
- drivers/regulator/qcom-rpmh-regulator.c:163-174, 229-261 — per-rail ACK policy, enable/disable state, synchronous versus asynchronous RPMh request choice.

HOS4.3 evidence:
- firmware-analysis/round106/TEST_AGENT_ROUND106_L5_RPMH_DISABLE_CONFIG_REPORT.txt — L5 provider/group/child proxy mapping and 100mA enabled proxy request.
- firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt — L5 and L9 30mA mode threshold plus 100mA proxy current, and L9 self-target proxy mapping.
- firmware-analysis/round111/TEST_AGENT_ROUND111_L17_RPMH_DISABLE_CONFIG_REPORT.txt — separate UFS L17 consumer review; not used as L5/L9 proxy evidence.

## 5. Candidate identity and pre-Agent review

- Patch blob: c180dbf458403d68b2c32c1d54776a7559e7e5db
- SHA-256: eae21b96d34ebff0e7bbd4843bcd4f96cda26b02f83dd6f323b8c571e51fef80
- One file only: drivers/regulator/proxy-consumer.c
- Patch has one hunk, old/new counts 25/29.
- AI1 independently reconstructed the actual proxy-consumer.c contents by applying the AI2 ROUND31 add-file patch, ROUND32 delta and ROUND33 self-target-only delta; the ROUND126 hunk matched and applied to that reconstructed 17-patch source. This is an author-side source/context check, not a substitute for Agent git apply/build validation.

The candidate remains isolated on the AI1 branch. It does not modify AI2's branch or test harness. Full validation is queued for the combined AI1 ROUND125/ROUND126 Agent task after ROUND33 has released its build slot.
