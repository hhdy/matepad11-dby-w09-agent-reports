# ROUND23 — UFS VCCQ parent rail and ACK driver adaptation

Date: 2026-11-24

Status: ROUND7/ROUND9 local report review plus ACK and downstream Qualcomm source review. Board DTS and an ACK UFS driver patch sketch have been updated. No patch was applied to an ACK checkout; no schema validation, compile, device access or runtime power test was performed.

## 1. Additional HOS4.3 UFS rail

ROUND9 resolved the extra UFS Host property qcom,vccq-parent-supply to the PM8150A S8 resource, with an output range of 1.2–1.4 V and a maximum load request of 210 mA. This is distinct from the standard VCCQ supply, which remains PM8150 L6 at 1.2 V.

ROUND7's local deterministic base-FDT property inventory identifies the RPMh VRM group and child:
- Provider group: /soc/rsc@18200000/rpmh-regulator-smpc8
- Child: regulator-pm8150a-s8
- Regulator name: pm8150a_s8
- Locally recorded output range: 1.2–1.4 V

The property qcom,vccq-parent-supply is a UFS consumer extension. It is not the PMIC regulator's own input property vdd-s8-supply.

## 2. Mapping the legacy resource to upstream ACK

The same-device public Linux 7.0 board DTS maps the stock pm8150a_s8 resource under:
- compatible qcom,pm8150l-rpmh-regulators
- qcom,pmic-id c
- child smps8
- regulator name pm8150l_s8

The same public board file comments that this is the QCA6390 RFA 1.35 V rail. That public source is a HOS4.2 cross-reference, not the voltage source for this HOS4.3 draft. The ACK board draft therefore uses the HOS4.3 local range 1.2–1.4 V and does not copy HOS4.2's 1.35 V minimum or initial-mode setting.

ACK android17-6.18's qcom-rpmh-regulator.c PM8150L table includes SMPS8 and maps it to pmic5_hfsmps510. Thus the S8 output can be represented through the upstream PM8150L VRM provider. The current board DTS draft adds regulators-1 with PMIC ID c and an smps8 child; it also adds the UFS consumer's qcom,vccq-parent-supply phandle and qcom,vccq-parent-max-microamp = 210000.

## 3. Downstream UFS driver behavior and upstream gap

Qualcomm downstream UFS implementations parse qcom,vccq-parent-supply and qcom,vccq-parent-max-microamp and look up the regulator with consumer ID qcom,vccq-parent.

Observed downstream variants differ:
- The OnePlus SM8150 implementation uses the maximum current as a regulator load vote during init, drops the load when the link is off (subject to auto-BKOPS state), and reapplies it on resume.
- A Motorola Qualcomm-derived implementation additionally enables/disables the regulator during init, link-off suspend and resume.

The current ACK android17-6.18 drivers/ufs/host/ufs-qcom.c has no VCCQ-parent field, parser or corresponding PM callback. Merely adding the two properties to DTS would therefore leave the property unused by unmodified ACK.

## 4. PM8150L S8 DRMS limitation

ACK's PM8150L SMPS8 hardware data uses pmic5_hfsmps510 and rpmh_regulator_vrm_ops. The current VRM ops support enable, disable, enabled-state, voltage and mode operations, but do not provide set_load or get_optimum_mode.

The generic regulator_set_load() API can return success without changing hardware when DRMS is unsupported. Therefore the proposed UFS patch records and attempts the 210 mA load request, but it cannot prove that the request changes the S8 hardware mode under the current ACK regulator provider. No speculative PMIC-specific load-to-mode policy is added.

Enable/disable of the regulator remains supported through the VRM ops. The proposed first-storage implementation conservatively enables S8 while the UFS host is bound and releases it on init failure or host exit. It deliberately does not imitate an unverified downstream suspend/resume sequence.

## 5. PMIC input path remains a separate unknown

ROUND11's full HOS4.3 base-FDT scan found no vdd-s1..s10-supply, vin-supply or vph-pwr-supply properties. It did not establish the physical input source for PM8150L S8 either. Do not add vdd-s8-supply or a guessed fixed vph_pwr node.

Because the board has a populated Device Tree, regulator core may use a dummy parent if the upstream regulator supply_name cannot be resolved. That behavior assumes the physical parent rail already exists and is enabled; it does not prove the PMIC input network or guarantee that this is the supported board configuration.

## 6. Updated source drafts

Branch ack18-dby-w09-dts-draft:
- dts/dby-w09-ack18-board.dts.draft: adds PM8150L S8 under regulators-1 with HOS4.3 1.2–1.4 V range; adds the UFS VCCQ-parent phandle and 210 mA maximum-load request.
- patches/ufs-qcom-vccq-parent.patch.draft: adds a source patch sketch for optional regulator lookup, enable/load request, init-failure cleanup, host-exit cleanup and binding properties.
- dts/README.md: records the parent-rail and driver requirement.

The patch file is a review sketch with source-context anchors, not an apply-verified diff. It has not been applied to a pinned ACK source checkout.

## 7. Verification status

| Item | Status |
|---|---|
| HOS4.3 UFS parent rail identity / output window | ROUND7/ROUND9 LOCAL EVIDENCE |
| HOS4.3 UFS maximum-load request | ROUND9 FOUND — 210000 uA |
| Same-device mapping to PM8150L / PMIC ID c / SMPS8 | PUBLIC SAME-DEVICE SOURCE REVIEWED |
| ACK PM8150L S8 VRM provider | SOURCE REVIEWED |
| ACK PM8150L S8 DRMS set_load support | NOT PROVIDED BY CURRENT VRM OPS |
| ACK UFS qcom,vccq-parent-supply handling | NOT PRESENT UPSTREAM; PATCH SKETCH CREATED |
| Physical input supply for PM8150L S8 | UNKNOWN / NOT_ESTABLISHED |
| Exact HOS4.3 UFS init/suspend/resume semantics | UNKNOWN |
| Patch application / dt-schema / Kconfig / compile | NOT_RUN |
| Device boot / runtime rail behavior | NOT_RUN |
| Device connection / flash / write | NO |

## 8. Next steps

Continue GPT-side source review and draft iteration. ROUND12 AVB metadata inspection remains the only local Agent task. No additional local FDT, EROFS or ramdisk scan is needed for this UFS parent-rail mapping. Keep all source drafts clearly marked, PR #1 Draft, and do not perform any image write or device operation.
