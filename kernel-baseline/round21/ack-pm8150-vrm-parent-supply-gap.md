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
| Power-tree runtime voltage/mode behavior | NOT_RUN |
| DTS schema / Kconfig resolution / compile / boot | NOT_RUN |

## 7. Next step

ROUND22 defines an ACK ARC-provider port as a separate compatibility task; this does not close the physical PM8150 input-parent question. Continue looking for authoritative PMIC electrical source material and keep guessed vph_pwr wiring removed. ROUND12 AVB metadata is still the only local Agent task. PR #1 remains Draft; no flash, unlock, root, device connection, compile or writes.
