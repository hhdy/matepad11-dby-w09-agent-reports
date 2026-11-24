# ROUND24 — ACK UFS Host VDDP rail placement and L6 DRMS aggregation

Date: 2026-11-24

Status: public ACK android17-6.18 and downstream Qualcomm source review; board DTS and the companion UFS supply patch sketch corrected. No source patch application, schema validation, compile or runtime test.

## 1. HOS4.3 node placement and consumers

ROUND9's local HOS4.3 overlay resolution places both vendor-specific supply consumers on UFS Host fragment@64:

| UFS Host property | Rail | Output / load evidence |
|---|---|---|
| qcom,vddp-ref-clk-supply | PM8150 L6 | fixed 1.2 V; max 100 uA |
| qcom,vccq-parent-supply | PM8150A S8 | 1.2–1.4 V; max 210000 uA |

These are Host variant-driver resources. They are not QMP UFS PHY analog supplies. The QMP PHY node has its own two generic supplies:
- vdda-phy -> PM8150 L5, fixed 0.88 V, max 89900 uA;
- vdda-pll -> PM8150 L9, fixed 1.2 V, max 18800 uA.

## 2. ACK QMP PHY versus UFS Host consumption

ACK android17-6.18 drivers/phy/qualcomm/phy-qcom-qmp-ufs.c defines the SM8250 UFS PHY regulator list with only vdda-phy and vdda-pll. It bulk-gets and enables those supplies as part of QMP PHY power-on; it does not parse vddp-ref-clk.

The downstream Qualcomm UFS Host driver instead parses qcom,vddp-ref-clk and qcom,vccq-parent from the UFS Host node. It acquires the reference-clock pad supply, enables it after PHY initialization, and manages its power state during suspend/resume; qcom,vccq-parent is managed as a separate UFS Host consumer.

Therefore the earlier draft placement of vddp-ref-clk-supply under &ufs_mem_phy was incorrect. The board DTS now puts qcom,vddp-ref-clk-supply and qcom,vddp-ref-clk-max-microamp under &ufs_mem_hc. The &ufs_mem_phy block now contains only vdda-phy and vdda-pll.

Sources:
- ACK QMP UFS PHY: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/phy/qualcomm/phy-qcom-qmp-ufs.c
- ACK UFS Host: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/ufs/host/ufs-qcom.c
- OnePlus Qualcomm UFS extension: https://github.com/LineageOS/android_kernel_oneplus_sm8150/blob/9f007fac27dce21d29d8230753b71d5634b8a00e/drivers/scsi/ufs/ufs-qcom.c

## 3. L6 DRMS: 100 uA is not the whole regulator load

ACK qcom-rpmh-regulator.c maps PM8150 LDO6 to pmic5_nldo and rpmh_regulator_vrm_drms_ops. The PMIC5 NLDO data uses hpm_min_load_uA = 30000. The function rpmh_regulator_vrm_get_optimum_mode() selects:
- REGULATOR_MODE_NORMAL (HPM) when the regulator's aggregated consumer load is >= 30000 uA;
- REGULATOR_MODE_IDLE (LPM) below that threshold.

The HOS4.3 Host VDDP consumer asks for only 100 uA, but the same physical PM8150 L6 is also the ordinary VCCQ rail. ACK UFS core stores vccq-max-microamp = 800000 on its standard regulator consumer and calls regulator_set_load() when configuring VCCQ HPM/LPM. Regulator core aggregates those separate consumer votes.

Consequently, when VCCQ is in HPM and its 800 mA request is active, the L6 aggregate exceeds 30 mA and the provider selects HPM. During low-power transitions the UFS core reduces the VCCQ load request; with only the 100 uA VDDP vote remaining, the aggregate is below 30 mA and the provider selects LPM. This is the upstream DRMS model; exact hardware behavior still needs runtime verification.

Board DTS already sets regulator-allow-set-load and regulator-allowed-modes LPM/HPM on PM8150 L6. No further guessed mode property is needed.

## 4. S8 and L6 are intentionally different

PM8150L S8 maps to pmic5_hfsmps510 / rpmh_regulator_vrm_ops, which has no DRMS set_load or get_optimum_mode callback. The UFS 210 mA request can be passed to regulator_set_load(), but it may be accepted without causing a physical mode vote. Its enable/disable path is supported.

PM8150 L6 LDO6 maps to pmic5_nldo / rpmh_regulator_vrm_drms_ops with the 30 mA threshold. Its 100 uA VDDP request is therefore handled by the DRMS aggregator together with the standard VCCQ current request.

Do not report the S8 and L6 requests as if both have identical load-voting semantics.

## 5. Companion patch sketch changes

Branch ack18-dby-w09-dts-draft, file patches/ufs-qcom-vccq-parent.patch.draft:
- now models both optional Host consumers: qcom,vddp-ref-clk and qcom,vccq-parent;
- requests each load vote before enabling its regulator, following the generic UFS regulator sequence;
- enables VDDP first and S8 second; cleans up in reverse order on error/exit;
- adds schema descriptions for both properties to qcom,ufs-common.yaml;
- retains the conservative host-bound rail lifetime and does not invent a suspend/resume policy.

The file remains a source patch sketch with context anchors, not an apply-verified diff. It has not been rebased onto a pinned ACK tree, compiled or runtime-tested.

## 6. Verification state

| Item | Status |
|---|---|
| HOS4.3 Host qcom,vddp-ref-clk mapping to L6 / 100 uA | ROUND9 COMPLETE |
| ACK QMP PHY uses only vdda-phy and vdda-pll | SOURCE REVIEWED |
| ACK UFS Host lacks vddp-ref-clk consumer handling | SOURCE REVIEWED |
| Downstream Qualcomm Host parses/controls VDDP | SOURCE REVIEWED |
| PM8150 L6 DRMS threshold / mode mapping | SOURCE REVIEWED: 30 mA, aggregate-load based |
| PM8150 S8 DRMS set_load | NOT PROVIDED BY CURRENT S8 VRM OPS |
| Board DTS property placement | UPDATED, DTS SOURCE DRAFT ONLY |
| UFS Host VDDP + VCCQ-parent patch sketch | UPDATED, NOT APPLIED |
| Schema validation / patch apply / Kconfig / compile | NOT_RUN |
| Runtime current aggregation / rail transitions | NOT_RUN |

## 7. Next steps

Continue GPT-side source review and draft iteration. ROUND12 AVB metadata inspection remains the only local Agent task. No local FDT scan is needed for this source-only correction. Keep all files marked .draft and do not perform device operations.
