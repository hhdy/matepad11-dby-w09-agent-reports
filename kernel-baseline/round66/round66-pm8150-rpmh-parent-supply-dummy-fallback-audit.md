# ROUND66 — PM8150 RPMh input-parent binding and regulator-core dummy fallback audit

**Date:** 2026-11-25  
**Owner:** Primary AI, exact ACK source review  
**Baseline:** ACK android17-6.18.33_r00 / common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Scope:** binding, RPMh regulator driver and regulator-core control flow only. No DTS edits, no Kconfig, no build, no device.

## 1. Executive result

The current DBY-W09 board DTS draft omits PM8150 VRM input-parent properties such as `vdd-s4-supply`, grouped `vdd-l*-supply` and `vdd-s8-supply`. This is a real unresolved electrical assumption, but it is **not automatically a DT-schema error or a regulator-driver registration failure** in the pinned ACK implementation.

Three distinct software facts are established:

1. The pinned ACK binding `Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml` describes the PM8150 parent-input supply properties in compatible-specific `allOf` branches, but does not add them to the schema's top-level `required` list. The only top-level required keys are `compatible` and `qcom,pmic-id`.
2. The pinned RPMh regulator driver installs each regulator's internal parent supply name in `regulator_desc.supply_name` from the PMIC-specific descriptor table. For PM8150, examples include:
   - SMPS4 → `vdd-s4`;
   - LDO5 → `vdd-l3-l4-l5-l18`;
   - LDO6/LDO9 → `vdd-l6-l9`.
   Those names are software parent requirements; they are not proof of the physical source or voltage.
3. Regulator core can substitute its dummy regulator when the parent lookup returns `-ENODEV` and full constraints are active. In this pinned tree, `have_full_constraints()` returns true if either explicit full constraints were declared or `of_have_populated_dt()` is true. If an input supply property is simply absent and no platform alias resolves it, the core may use a dummy regulator, with an explicit comment that this assumes the physical regulator exists and is already enabled.

The dummy fallback is not applied in every case. A phandle that names an existing DT node but whose regulator has not registered can return `-EPROBE_DEFER`, and that error is not converted into a dummy. A malformed/self-referential or unresolved provider path may likewise fail for a different reason.

**Conclusion:** missing PM8150 input-supply phandles can be accepted by the binding and may fall back to dummy regulator in DT boot. That does not establish the physical PMIC input rail topology, prove that a regulator is actually powered, or validate PMIC5 sequencing. Keep the electrical gate unresolved. Do not invent `vph_pwr`, fixed regulators or PMIC input voltages.

## 2. Binding facts

Pinned file:
`Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml`.

- PM8150 and PM8150L compatible strings are supported in the schema.
- The PM8150 conditional branch permits:
  `vdd-l1-l8-l11-supply`,
  `vdd-l2-l10-supply`,
  `vdd-l3-l4-l5-l18-supply`,
  `vdd-l6-l9-supply`,
  `vdd-l7-l12-l14-l15-supply`,
  `vdd-l13-l16-l17-supply`,
  and pattern `vdd-s([1-9]|10)-supply`.
- The PM8150L conditional branch permits:
  `vdd-l1-l8-supply`,
  `vdd-l2-l3-supply`,
  `vdd-l4-l5-l6-supply`,
  `vdd-l7-l11-supply`,
  `vdd-l9-l10-supply`,
  and pattern `vdd-s[1-8]-supply`.
- These are declared under `properties` / `patternProperties` in `allOf`; the schema does not put them in a `required` array.
- The only top-level `required` keys are `compatible` and `qcom,pmic-id`.

Source:
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/regulator/qcom%2Crpmh-regulator.yaml

This proves only that the schema does not require each input-supply link. A successful schema check is not an electrical schematic.

## 3. RPMh regulator driver facts

Pinned file:
`drivers/regulator/qcom-rpmh-regulator.c`.

- `struct rpmh_vreg_init_data` carries `supply_name` (lines 144–152).
- `rpmh_regulator_init_vreg()` copies the PMIC descriptor's `supply_name` into `vreg->rdesc.supply_name` (around line 447).
- PM8150 descriptor entries map SMPS4 to `vdd-s4`, LDO3/LDO4/LDO5 to the shared `vdd-l3-l4-l5-l18`, LDO6/LDO9 to `vdd-l6-l9`, and others to their PMIC5 input names (around lines 980–1005).
- The provider registers its output regulator via `devm_regulator_register()` (around lines 484–487); it does not manufacture a physical input-source node.

Sources:
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c

## 4. Regulator-core dummy fallback behavior

Pinned files:
- `drivers/regulator/core.c`
- `drivers/regulator/of_regulator.c`

### 4.1 What counts as full constraints

`drivers/regulator/core.c:L114-L117`:
`have_full_constraints()` returns `has_full_constraints || of_have_populated_dt()`.

Thus a populated DT boot activates the core's full-constraints predicate even without relying on a board-specific call to `regulator_has_full_constraints()`.

### 4.2 Missing supply property / missing regulator

`drivers/regulator/core.c:L2046-L2103`:
- `regulator_resolve_supply()` attempts DT and parent-device regulator lookup.
- If no parent regulator is found (`-ENODEV`) and full constraints are active, it obtains `dummy_regulator_rdev`.
- If full constraints are not active, it reports failure / defers instead.

`drivers/regulator/core.c:L2210-L2245`:
- `_regulator_get()` substitutes dummy supply only on the `-ENODEV` branch with full constraints and normal (not exclusive) get.
- Its comment states the core assumes the physical supply is present and already enabled even when it is not hooked up in DT.

### 4.3 Existing DT node with no registered regulator is different

`drivers/regulator/of_regulator.c:L647-L665`:
- if the `*-supply` phandle resolves to a DT node but `of_find_regulator_by_node()` cannot find a registered regulator for that node, it returns `-EPROBE_DEFER`.
- This is not the `-ENODEV` case that the normal-get dummy fallback handles.

Sources:
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L114-L117
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L2046-L2103
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L2210-L2245
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/of_regulator.c#L647-L665

## 5. What this means for DBY-W09

ROUND11/14/21 local HOS4.3 reports did not find the PMIC VRM output providers' own physical input-supply properties in the inspected base FDT. They did find vendor ARC parent-supply and proxy-supply relationships, but those are not interchangeable with physical PMIC VRM input rails.

Consequently:

- Do not add arbitrary `vdd-s4-supply`, grouped `vdd-l*-supply` or `vdd-s8-supply` phandles merely to fill the schema.
- Do not treat a dummy parent as a real hardware connection.
- Do not add a fixed regulator or guess a `vph_pwr` voltage.
- A temporary dummy parent may allow a regulator consumer/driver path to register and request a PMIC output, but it assumes the physical PMIC input is already powered and available. It cannot ensure rail safety under cold boot, suspend or failure recovery.
- The missing physical input map remains a pre-boot hardware/evidence gate even if dtc/dt-schema accepts the board source.

Evidence needed to close the electrical gate:
- authoritative DBY-W09 HOS4.3 PM8150/PM8150L schematic or power-tree document; or
- an equally trustworthy final hardware description that identifies the physical upstream sources and enable sequencing for all used PM8150 outputs.
Do not infer this from the vendor ARC parent graph, PMIC rail names, regulator voltage ranges, or another SM8250 board.

## 6. Status boundary

- Pinned binding schema optionality: PASS.
- Pinned PM8150 driver supply-name mapping: PASS.
- Pinned regulator-core dummy fallback code path: PASS.
- Whether the actual hardware input rails are physically present / held enabled by ABL: UNKNOWN.
- Whether the current board DTS can pass full dt_binding_check/dtbs_check in the actual ACK worktree: NOT RUN here; ROUND22 handles it.
- Electrical validation or device boot: NOT RUN.

No repository source, DTS, config, firmware, branch or device was modified.
