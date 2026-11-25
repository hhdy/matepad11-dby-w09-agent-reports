# ROUND83 — ACK PM8150 RPMh regulator supply-name contract for DBY-W09 UFS rails

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Baseline:** ACK android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Scope:** read-only review of the pinned RPMh regulator driver tables and DT binding, cross-referenced with the DBY-W09 rev2 UFS regulator nodes.

## 1. Result

**DRIVER SUPPLY-NAME CONTRACT: CONFIRMED. PHYSICAL BOARD INPUT PARENTS: STILL UNKNOWN.**

The pinned ACK PM8150 RPMh-regulator driver identifies the specific parent-supply property names that its regulator instances will look up. This lets the project name the expected DeviceTree keys for every PM8150 output used by the UFS candidate.

It does **not** reveal which physical PMIC pin, board rail, battery path, another regulator or power-tree node actually feeds those outputs on DBY-W09. HOS4.3 base FDT contains no matching vdd-*-supply properties in the inspected PMIC provider scope, and board-specific schematic/final-DT evidence is still missing.

Therefore this report narrows the evidence request but does not authorize adding any vdd-*-supply property or dummy parent regulator.

## 2. Exact mappings in pinned ACK driver

In drivers/regulator/qcom-rpmh-regulator.c, pm8150_vreg_data[] defines:

| PMIC output | UFS use in rev2 candidate | Driver supply_name | DT property key if an upstream provider is described |
|---|---|---|---|
| PM8150 L5 / LDO5 | QMP UFS PHY vdda-phy | vdd-l3-l4-l5-l18 | vdd-l3-l4-l5-l18-supply |
| PM8150 L6 / LDO6 | UFS VCCQ and device REF_CLK | vdd-l6-l9 | vdd-l6-l9-supply |
| PM8150 L9 / LDO9 | QMP UFS PHY vdda-pll | vdd-l6-l9 | vdd-l6-l9-supply |
| PM8150 L17 / LDO17 | UFS VCC | vdd-l13-l16-l17 | vdd-l13-l16-l17-supply |
| PM8150 S4 / SMPS4 | UFS VCCQ2 | vdd-s4 | vdd-s4-supply |

In pm8150l_vreg_data[], PM8150L SMPS8 has:

| PMIC output | UFS use in rev2 candidate | Driver supply_name | DT property key if an upstream provider is described |
|---|---|---|---|
| PM8150L S8 / SMPS8 | HOS VCCQ-parent topology metadata; not currently consumed by ACK UFS driver | vdd-s8 | vdd-s8-supply |

The table values above are copied from the driver initialization descriptors' supply_name fields. They are Linux regulator-core lookup names, not measured or schematic-verified physical net names.

Pinned source:
- [PM8150 and PM8150L regulator init tables](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c#L980-L1034)

## 3. Schema confirms the expected property groups

The pinned qcom,rpmh-regulator.yaml permits the PM8150 groups:
- vdd-l1-l8-l11-supply
- vdd-l2-l10-supply
- vdd-l3-l4-l5-l18-supply
- vdd-l6-l9-supply
- vdd-l7-l12-l14-l15-supply
- vdd-l13-l16-l17-supply
- vdd-s1-supply through vdd-s10-supply

For PM8150L the binding permits corresponding LDO group inputs and vdd-s1-supply through vdd-s8-supply.

Pinned source:
- [PM8150 / PM8150L supply-property allow-list](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml#L145-L174)
- [PM8150 supply-property allow-list](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml#L282-L295)

This confirms the exact names the driver/schema support. It does not say that all these inputs have to be declared for every board, nor does it state what real electrical source each one uses.

## 4. Cross-check against DBY-W09 rev2 candidate

Current dts/dby-w09-ack18-board.dts.rev2.candidate:
- PM8150 regulators-0 contains smps4, ldo5, ldo6, ldo9 and ldo17 with the matching HOS4.3-derived output constraints.
- PM8150L regulators-1 contains smps8.
- UFS Host consumers reference L17, L6 and S4; QMP PHY references L5 and L9; UFS VCCQ-parent metadata references S8 but is not consumed by the current pinned ACK UFS driver.
- The candidate does not add any of the parent properties listed in section 2. This is deliberate and is consistent with the absence of verified upstream input-provider information.

## 5. Why this still does not establish the physical topology

The supply_name field expresses how the Linux regulator driver asks regulator core to find an upstream supply for that PMIC output. It cannot determine:
- whether the board actually wires that rail to an external/other PMIC output;
- whether several LDOs share the same physical source, which source node models that connection, or its voltage range;
- whether the regulator input is a package pin fed from VBAT/VPH_PWR or from an intermediate rail;
- which HOS4.3 ARC/proxy relationships are internal voltage-level request semantics rather than physical power input paths.

The HOS4.3 evidence inventory specifically found no explicit vdd-s1..s10-supply, vin-supply or vph-pwr-supply properties in the inspected base FDT. ROUND64 also records no DBY-W09 board-specific schematic/power tree in the authorized local corpus.

A regulator driver having a parent-supply lookup name is not proof that the board has that parent wired in the same way as another Qualcomm reference platform. It is not grounds to invent a fixed 3.7 V VPH regulator or to connect all PM8150 rails to a guessed battery node.

## 6. What evidence can now resolve the PMIC gate

The next authoritative source needs only to resolve the following specific input nets:
- PM8150 vdd-l3-l4-l5-l18 group;
- PM8150 vdd-l6-l9 group;
- PM8150 vdd-l13-l16-l17 group;
- PM8150 vdd-s4;
- PM8150L vdd-s8.

A DBY-W09 schematic page, PMIC power tree, or authoritative final post-ABL FDT containing the relevant regulator input properties must identify the provider and its constraints. If a shared property group supplies several rails, the exact group membership should match the actual hardware. Do not split/merge the Linux properties based on assumptions.

Once the evidence is available, add only the verified input phandles and appropriate regulator constraints, then run the PMIC binding validation. Until then keep the parent properties absent and retain the PMIC gate as BLOCKED.

## 7. Boundaries

1号 AI inspected only pinned ACK source files and the current main-branch candidate. No board DTS, PMIC binding, driver, config, patch, 2号 AI branch or protected branch was modified. No device access, electrical measurement, compiler or schema validation was performed.

**Final status: exact ACK regulator-core supply-name contract established; DBY-W09 physical PMIC inputs remain BLOCKED.**
