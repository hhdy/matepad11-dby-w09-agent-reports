# ROUND85 — 1号 AI design review: SM8250 board compatible and Huawei rootparam schema

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, after a separate test task is issued  
**Pinned baseline:** ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Related record:** ROUND81 primary review of ROUND27; ROUND82/84 UFS VCC binding work

## 1. Executive result

The remaining ROUND27 non-UFS schema diagnostics should be handled as two distinct binding changes:

1. Add `huawei,dby-w09` to the existing SM8250 board-compatible allow-list in the pinned `Documentation/devicetree/bindings/arm/qcom.yaml`. The Huawei vendor prefix is already present in `vendor-prefixes.yaml`; no duplicate prefix entry is needed.
2. Add a narrowly selected binding for the bootloader-owned `/rootparam` node. Select by node name **and** the presence of Huawei/DBY-specific signature properties, not by node name alone. Do not add a new `compatible` to the bootloader-owned node just to silence dt-schema.

The exact candidate shape is supported by the checked-in rootparam overlay: four u32 cells for `qcom,boardid`, two u32 cells for `huawei,modem_id`, and strings for `qcom,board_name`, `qcom,product_name`, and `hardware_version`.

This is a binding design review only. It does not assert that the VG DTBO is the actual runtime-selected entry. The overlay remains a candidate and ABL selection is still UNKNOWN.

## 2. Root compatible — exact pinned schema gap

Pinned source: [`Documentation/devicetree/bindings/arm/qcom.yaml`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/arm/qcom.yaml).

The `compatible` property is an explicit `oneOf` list of SoC-specific compatible tuples. In the SM8250 tuple, the board-specific first compatible is an enum, followed by `const: qcom,sm8250`. The existing enum contains RB5, SM8250 HDK/MTP, Samsung R8Q/X1Q, Sony PDX203/206 and Xiaomi Elish/Pipa, but not `huawei,dby-w09`.

The current board candidate declares:

```dts
compatible = "huawei,dby-w09", "qcom,sm8250";
```

The correct narrow correction is to add `huawei,dby-w09` to the board-specific enum for the existing `qcom,sm8250` tuple. Do not:
- add a new SoC tuple for DBY-W09;
- replace the board's compatible order or remove `qcom,sm8250`;
- add unrelated aliases that were not observed in the actual board candidate;
- add a vendor-prefix entry, since the pinned `vendor-prefixes.yaml` already recognizes `^huawei,.*`.

The same qcom.yaml already conditionally allows `qcom,board-id` for the legacy/SM8250 compatible group, and applies its existing two-cell shape rule except for separately enumerated OnePlus cases. The candidate root uses `qcom,board-id = <0 0>`, so this board allow-list addition is consistent with the present tuple design. Keep the separate rootparam overlay board-id and Android DT table id/rev concepts distinct.

## 3. Rootparam — precise node-name selector

Pinned selector precedent: [`Documentation/devicetree/bindings/net/ethernet-phy.yaml`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/net/ethernet-phy.yaml).

The ACK tree already documents explicit `select` by `$nodename` when compatible is optional. That precedent does not mean every node named `rootparam` should be claimed by a Huawei schema. The DBY-W09 base DTB deliberately contains an empty `rootparam` node, while the separate overlay adds the identifying vendor properties.

A safer selector shape is therefore conceptually:

```yaml
select:
  properties:
    $nodename:
      const: rootparam
  required:
    - $nodename
    - qcom,boardid
    - huawei,modem_id
```

This makes the binding apply to the overlay-populated Huawei rootparam node, while leaving the empty base placeholder unmatched. The final schema should keep the selector deliberately narrow. If dt-schema's exact selector semantics require the signature properties inside `select.properties` as well as `required`, follow the pinned tool's documented/validated syntax; do not rely on a broad automatic nodename match.

### 3.1 Property contracts from the actual overlay

Source: [DBY-W09 rootparam overlay candidate](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/dts/dby-w09-ack18-rootparam.dtso.draft).

| Property | Candidate value shape | Binding type/constraint |
|---|---|---|
| `qcom,boardid` | `<0x08 0x02 0x09 0x08>` | exactly 4 u32 cells |
| `huawei,modem_id` | `<0xffffffff 0x00>` | exactly 2 u32 cells |
| `qcom,board_name` | `"DBY_W09_VG"` | string |
| `qcom,product_name` | `"DBY-W09"` | string |
| `hardware_version` | `"SH1DBSLM"` | string |

The binding should document that these are bootloader-facing identity/variant metadata properties. Do not reinterpret `qcom,boardid` as the root node's `qcom,board-id`, and do not infer table-selection metadata from either value.

A binding can require the five properties for the specific overlay-populated rootparam shape if validation is explicitly against the composite candidate. If validation also covers the base DTB before overlay, the selector must exclude its intentionally empty placeholder as described above. Avoid making the binding apply to unrelated vendors' rootparam nodes.

Use strict array lengths and the proper u32/string type references. Whether to close the property set with `additionalProperties: false` should be decided against the complete HOS rootparam inventory; the current nine-entry stock-DTBO scan recorded five common properties, but this alone should not be generalized to every future Huawei bootloader revision without evidence.

## 4. Why not add a compatible to /rootparam

The rootparam node is owned by the Huawei/ABL interface in this candidate. Adding a made-up compatible would alter the firmware-visible tree and has no evidence-backed consumer requirement. Schema selection by node name plus distinctive required properties is sufficient to match the node without introducing a new DT property.

This is especially important because the board's root compatible and the rootparam node's data serve different roles:
- root `compatible`: Linux board/SoC identification;
- `/rootparam` fields: Huawei bootloader/variant data;
- rootparam overlay `qcom,board-id`: separate overlay content value;
- Android DT table header id/rev: packaging/ABL table metadata, still independently unresolved.

No schema change should claim that the current VG candidate is selected on the actual device.

## 5. Validation plan

When 2号 AI implements these changes in its own integration branch, validate in this order:

1. Run `dt_binding_check` for the modified qcom ARM schema and the new rootparam schema. Preserve complete schema ID, filenames, and diagnostics.
2. Run the root/base DTB validation and the composite DTB validation separately if the build flow supports both. Confirm the empty base `rootparam` placeholder is not incorrectly matched.
3. Confirm the composite `rootparam` node is selected exactly once and that all five property types/array lengths validate.
4. Confirm the root compatible tuple is accepted with the existing `qcom,sm8250` SoC compatible.
5. Re-run the ROUND27 UFS/PHY/regulator/power-domain targeted schema set after the separate UFS VCC driver+binding fix from ROUND82/84 is integrated.
6. Keep the remaining UFS, root-compatible and rootparam diagnostics separate in the report; a decrease in error count is not a pass unless all target diagnostics are explained and resolved.

## 6. Scope and ownership

**This is a [1号 AI research/design-review report].** It is provided to 2号 AI as a technical recommendation, not as an implementation task and not as permission to edit 2号 AI's branch.

- 1号 AI: public pinned-source review and design feedback.
- 2号 AI: owns implementation decision and patch changes in its dedicated branch.
- Testing Agent: test executor only; requires a separate `AGENT_TEST_TASK.md` from the responsible developer.
- The user is not being asked to run these commands.

No source, binding, DTS, patch, or branch was modified in this round. No dt-schema/build/test command or device operation was run.

**Final status:** the qcom board-compatible fix is a narrow allow-list addition; the rootparam fix should be a Huawei-signature-selected node-name binding. Both are independent of the still-open ABL variant-selection and boot acceptance gates.
