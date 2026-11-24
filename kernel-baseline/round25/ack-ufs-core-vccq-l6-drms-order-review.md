# ROUND25 — ACK UFS core rail sequence and VCCQ/L6 DRMS aggregation

Date: 2026-11-24

Status: public ACK android17-6.18 source review only. No source patch apply, build, schema validation or runtime test.

## 1. Generic UFS core standard rail order

The ACK drivers/ufs/core/ufshcd.c sequence in ufshcd_hba_init() is:
1. ufshcd_init_vreg() obtains VCC/VCCQ/VCCQ2.
2. ufshcd_setup_vreg(hba, true) enables VCC, then VCCQ, then VCCQ2.
3. ufshcd_variant_hba_init() calls the Qualcomm variant ufs_qcom_init().

ufshcd_config_vreg_load() applies each generic UFS supply's max-current request via regulator_set_load() before regulator_enable(). The current DBY-W09 DTS gives standard VCCQ on PM8150 L6 a max request of 800000 uA. Thus the L6 VCCQ consumer is already enabled and has its load vote in place before the optional VDDP/S8 handling runs inside Qualcomm variant init.

This agrees with downstream Qualcomm's general design: generic core handles standard VCC/VCCQ/VCCQ2 first; the Qualcomm variant then brings up Host-specific rails such as VDDP reference pad and VCCQ parent.

Source: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/ufs/core/ufshcd.c

## 2. How the L6 DRMS mode is selected

ACK regulator core drms_uA_update():
- sums uA_load for every enabled consumer of the regulator;
- adds the regulator's system_load constraint;
- calls get_optimum_mode() where supported;
- applies the selected mode through the regulator driver's set_mode operation.

ACK PM8150 LDO6 uses pmic5_nldo with rpmh_regulator_vrm_drms_ops and hpm_min_load_uA = 30000. rpmh_regulator_vrm_get_optimum_mode() returns NORMAL/HPM at or above 30000 uA and IDLE/LPM below that threshold.

With the current board DTS:
- generic UFS VCCQ contributes up to 800000 uA when in HPM;
- Host VDDP contributes 100 uA;
- these are separate regulator consumers but both point to the same L6 regulator, so regulator core aggregates their enabled load votes.

Conditional source-model behavior, only if ROUND13 confirms DRMS permissions:
- When the generic VCCQ HPM vote is active, the aggregate is far above 30 mA, so L6 selects HPM.
- During generic UFS low-power transitions, the core reduces the VCCQ load through ufshcd_config_vreg_lpm(). If only the small VDDP vote and other sub-threshold consumers remain, the aggregate is below 30 mA and L6 can select LPM.
- The exact result remains dependent on other consumers and any system_load constraint; this is not a runtime observation.

## 3. S8 behavior is not the same as L6

PM8150L S8 uses pmic5_hfsmps510 and rpmh_regulator_vrm_ops, without get_optimum_mode or set_load. Regulator core's drms_uA_update() returns success without hardware work when neither callback exists. Thus the 210 mA VCCQ-parent request is deliberately passed, but it is a successful no-op for hardware load/mode control under the current ACK S8 ops. The enable/disable path is still implemented.

By contrast, L6 has DRMS mode-selection callbacks and a 30 mA threshold. Do not describe the two votes as having the same effect.

## 4. Patch sketch sequence

The companion patches/ufs-qcom-vccq-parent.patch.draft now:
- calls regulator_set_load() before regulator_enable() for both optional Host supplies, matching the generic UFS core regulator pattern;
- enables VDDP first, then S8, inside Qualcomm variant init after generic UFS core has enabled standard VCCQ;
- disables in reverse order on error/exit, then clears each load vote;
- leaves exact HOS4.3 link-off suspend/resume policy for later review; it does not copy a different downstream kernel's BKOPS behavior.

This remains a patch sketch, not an apply-tested diff. It has not been compiled, schema-validated or runtime-tested.

## 5. Sources

- UFS core rail initialization / power transitions: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/ufs/core/ufshcd.c
- Regulator DRMS aggregation: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/regulator/core.c
- PM8150 hardware operations and 30 mA threshold: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/regulator/qcom-rpmh-regulator.c

## 6. Verification state

| Check | Status |
|---|---|
| Standard UFS core rails initialized before variant init | SOURCE REVIEWED |
| Generic VCCQ max-load and low-power load adjustment | SOURCE REVIEWED |
| L6 PMIC5 NLDO DRMS and threshold | SOURCE REVIEWED |
| Regulator core sums enabled-consumer votes + system_load | SOURCE REVIEWED |
| Expected L6 HPM/LPM under source model | CONDITIONAL ON HOS4.3 DRMS CONSTRAINTS; NOT RUNTIME TESTED |
| S8 load vote handling | SUCCESSFUL NO-OP IF DRMS OPS ABSENT |
| Patch apply / compile / schema validation | NOT_RUN |
| Device boot / actual rail state | NOT_RUN |

## 7. Next steps

Continue GPT-side source work. ROUND12 AVB metadata inspection remains the only local Agent task. No new local task is required for this source-only review.
