# ROUND21 — ACK PM8150 VRM parent-supply gap and dummy-regulator semantics

Date: 2026-11-24

Status: ACK android17-6.18 source review plus previously completed local ROUND11 report review. No local re-extraction, no DTB/DTBO compilation, no Kconfig resolution, no kernel build, no boot, no device access or write.

## 1. What the ACK PM8150 driver expects

The ACK drivers/regulator/qcom-rpmh-regulator.c PM8150 table sets a non-NULL regulator supply_name for each output rail used by this board:
- PM8150 SMPS4 / DBY-W09 output alias pm8150_s4: vdd-s4
- PM8150 LDO5: vdd-l3-l4-l5-l18
- PM8150 LDO6: vdd-l6-l9
- PM8150 LDO9: vdd-l6-l9
- PM8150 LDO17: vdd-l13-l16-l17

The driver copies this table value to rdesc.supply_name during rpmh_regulator_init_vreg() and registers the regulator. The YAML binding describes these as optional PMIC parent supply properties for the PM8150 regulator group; the driver nevertheless knows the logical supply name internally.

Source:
https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/regulator/qcom-rpmh-regulator.c
Binding:
https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml

## 2. What the HOS4.3 local evidence says

ROUND11 examined the entire /soc/rsc@18200000 property set (109 property paths), filtering every property name containing supply / vin / parent. It found exactly:
- four vendor ARC parent-supply links from CX/MMCX level groups into MX level nodes;
- six proxy-supply links within or between the ARC proxy groups.

It did not report PM8150 VRM parent properties such as vdd-s4-supply or the grouped vdd-l*-supply names required by the upstream driver. Its whole-base-FDT scan separately found zero vdd-s1..s10-supply, vin-supply, or vph-pwr-supply properties.

The ARC parent links must not be substituted for the generic PMIC VRM properties:
- their targets are voltage-level ARC nodes, not ordinary PM8150 supply regulators;
- proxy-supply has a separate proxy-request meaning;
- ACK upstream PMIC VRM driver does not bind the HOS vendor qcom,rpmh-arc-regulator compatible.

Therefore the actual physical supply inputs for the PM8150 UFS rails remain NOT_ESTABLISHED from the available HOS4.3 base-FDT evidence. The HOS4.2-based public 3.7 V vph_pwr + vdd-s* solution must not be restored on assumption.

## 3. Why a missing parent phandle may not stop probe

The ACK regulator core resolves each regulator supply_name. If it cannot find a matching DT phandle or regulator provider:
- have_full_constraints() returns true when full constraints are explicitly set OR when a populated Device Tree exists (of_have_populated_dt()).
- In that full-constraints case, the regulator core can substitute the dummy regulator for an unresolved supply.
- The dummy regulator semantics explicitly assume that the physical supply is present and already enabled, even though it is not connected in the software regulator graph.

This means the current minimal DTS may not fail only because those parent supply phandles are absent. But it does not mean the missing parent relationship has been discovered, validated, or safely modeled. Dummy fallback does not create a real regulator path, vote a parent rail, or prove the power source is enabled under ACK runtime conditions.

Relevant source:
https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/regulator/core.c

## 4. Impact on the current board DTS draft

The current draft correctly maps the UFS consumers to the locally resolved PM8150 output rails:
- UFS VCC -> PM8150 L17;
- UFS VCCQ -> PM8150 L6;
- UFS VCCQ2 -> PM8150 S4;
- QMP PHY VDDA-PHY -> PM8150 L5;
- QMP PHY VDDA-PLL -> PM8150 L9;
- QMP PHY VDDP-REF-CLK -> PM8150 L6.

This is a consumer-to-output mapping, not a complete physical power-tree model.

The draft will therefore:
- keep the five UFS output rails and consumer links;
- keep external PM8150 parent supplies unspecified;
- not create a guessed 3.7 V fixed regulator;
- not convert ARC parent-supply or proxy-supply into generic regulator supply phandles;
- explicitly record that regulator parent-path / electrical validation remains a pre-boot gate.

## 4.5 ARC parent links are a separate vendor accelerator graph (ROUND22)

ROUND22 confirmed the four HOS4.3 parent-supply edges belong to qcom,rpmh-arc-regulator providers. An older Qualcomm downstream driver has a dedicated ARC path that reads each resource's voltage-level map from Command DB AUX data and implements each ARC child as a regulator. It dynamically maps a child regulator-name to a regulator-name-parent-supply property and a regulator-name-parent supply name. This is the correct semantic class for those four CX/MMCX-to-MX edges; it is not a way to manufacture PM8150 VRM LDO/SMPS input parents.

An ACK ARC port may help reproduce the HOS4.3 shared voltage-level hierarchy and make this generic regulator tree explicit, but it does not establish the physical PM8150 input source by itself. See ROUND22.

## 4.6 UFS VCCQ parent rail is not the PMIC regulator input supply (ROUND23)

The UFS Host overlay has a second, distinct property named `qcom,vccq-parent-supply`. ROUND9's HOS4.3 UFS supply closure identifies it as PM8150A S8 (`pm8150a_s8`), with an output window of 1.2–1.4 V and a maximum load request of 210 mA. This is not a `vdd-s8-supply` input property on the PM8150L regulator provider.

The same-device public Linux 7.0 board DTS places the legacy `pm8150a_s8` resource in `regulators-1`, compatible `qcom,pm8150l-rpmh-regulators`, `qcom,pmic-id = "c"`, child `smps8`, regulator name `pm8150l_s8`. Its HOS4.2-derived range is 1.35–1.4 V; the current ACK draft deliberately uses the local HOS4.3-confirmed 1.2–1.4 V range instead. The HOS4.3 local inventory does not establish initial mode, regulator boot-on state, DRMS support, or the S8 physical input supply.

Downstream Qualcomm UFS drivers explicitly parse `qcom,vccq-parent-supply` and `qcom,vccq-parent-max-microamp`. Some versions use the latter as a DRMS/load vote only; another Qualcomm-derived version also enables/disables the rail during init, link-off suspend and resume. ACK android17-6.18's `drivers/ufs/host/ufs-qcom.c` and `struct ufs_qcom_host` have no equivalent field/parser/callback, so a DTS property alone would have no effect.

ROUND23 adds a review-only companion patch draft to:
- look up the optional regulator by consumer ID `qcom,vccq-parent` when its supply property is present;
- request the declared 210 mA load and enable S8 before UFS link bring-up;
- release the load/enable vote on init failure or host exit;
- document both properties in the ACK UFS common binding.

Important limit: ACK PM8150L S8 maps to `pmic5_hfsmps510` and `rpmh_regulator_vrm_ops`, whose operations implement enable/disable/voltage/mode but no `set_load` / DRMS callback. The regulator core can return success without effect when DRMS is unsupported. Thus the proposed patch can preserve and attempt the load request, but it does not prove that 210 mA changes the S8 hardware mode. No PMIC-specific load-mode policy is guessed.

The patch is a source draft, not applied or compiled. Its conservative always-enabled-while-UFS-bound policy differs from some downstream suspend/resume variants; exact HOS4.3 UFS driver semantics remain unknown. Do not claim PM behavior equivalence.

Sources:
- HOS4.3 local evidence: ROUND9 UFS supply closure and ROUND7 PM8150A S8 node inventory on `firmware-audit-v1`.
- Same-device cross-reference: https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts
- ACK PM8150L table/ops: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/regulator/qcom-rpmh-regulator.c
- ACK UFS driver: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/ufs/host/ufs-qcom.c
- Downstream UFS parser/PM callbacks: https://github.com/LineageOS/android_kernel_oneplus_sm8150/blob/9f007fac27dce21d29d8230753b71d5634b8a00e/drivers/scsi/ufs/ufs-qcom.c and https://github.com/MotorolaMobilityLLC/kernel-msm/blob/0450c5076a8ec9415a10888c8c183ef6ff5f91b8/drivers/scsi/ufs/ufs-qcom.c

## 5. Potential future resolution paths (not implemented)

1. Find an authoritative HOS4.3 board/PMIC source or a documented rail-power schematic that resolves the true PM8150 input network and voltage ranges.
2. Review a matching vendor Android kernel implementation of qcom,rpmh-arc-regulator and the PMIC ARC requests, without copying unverified binaries or local firmware.
3. Determine whether the target system is expected to run with firmware-established / shared RPMh parent rails and whether dummy regulator semantics are part of the supported platform model. This requires authoritative platform documentation or an explicitly approved hardware/runtime validation.
4. Only if technically justified, consider an ACK driver adaptation to model the required ARC level provider; do not implement a speculative driver based only on property names.

No further local FDT parse is required; ROUND11 completed the relevant scope. Do not create a new Agent task merely to repeat this evidence.

## 6. Verification status

| Item | Status |
|---|---|
| ACK PM8150 driver supply_name for UFS output rails | SOURCE REVIEWED |
| ACK regulator core missing-parent fallback in populated-DT mode | SOURCE REVIEWED |
| HOS4.3 apps_rsc supply/parent properties | ROUND11 COMPLETE |
| HOS4.3 generic VRM parent phandles for S4/L5/L6/L9/L17 | NOT_FOUND_IN_INSPECTED_SCOPE |
| Actual physical PM8150 input network / external rail | UNKNOWN / NOT_ESTABLISHED |
| Dummy-regulator fallback equals electrically correct platform configuration | NOT_ESTABLISHED |
| Board DTS consumer-to-output rail phandles | SOURCE DRAFT MAPPED |
| HOS4.3 UFS VCCQ parent rail PM8150A S8 | ROUND9 FOUND; same-device PM8150L/S8 group mapping SOURCE REVIEWED |
| ACK UFS qcom,vccq-parent-supply consumption | NOT_SUPPORTED_UPSTREAM; companion patch DRAFTED |
| PM8150L S8 DRMS set_load support in ACK | NOT PROVIDED BY CURRENT VRM OPS; regulator_set_load may be no-op |
| S8 physical PMIC input supply / exact HOS mode and PM behavior | UNKNOWN / NOT_ESTABLISHED |
| Power-tree runtime voltage/mode behavior | NOT_RUN |
| DTS schema / Kconfig resolution / compile / boot | NOT_RUN |

## 7. Next step

ROUND22 defines an ACK ARC-provider port as a separate compatibility task; this does not close the physical PM8150 input-parent question. Continue looking for authoritative PMIC electrical source material and keep guessed vph_pwr wiring removed. ROUND12 AVB metadata is still the only local Agent task. PR #1 remains Draft; no flash, unlock, root, device connection, compile or writes.
