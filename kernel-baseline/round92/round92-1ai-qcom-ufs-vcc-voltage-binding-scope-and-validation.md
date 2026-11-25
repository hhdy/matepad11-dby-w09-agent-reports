# ROUND92 — 1号 AI source review: place the VCC voltage-range schema in Qualcomm UFS common binding

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, with a separate AGENT_TEST_TASK.md  
**Pinned baseline:** ACK android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Related records:** ROUND81, ROUND82, ROUND84, ROUND88, ROUND91

## 1. Executive result

The narrowest reusable binding location for the legacy Qualcomm UFS vcc-voltage-level consumer range is the pinned ACK file:

Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml

Do **not** place this Qualcomm-specific extension in the vendor-neutral ufs-common.yaml, because that file is inherited by non-Qualcomm UFS controller bindings too.

The current chain is:
- qcom,ufs.yaml includes qcom,ufs-common.yaml through allOf and uses unevaluatedProperties: false;
- qcom,ufs-common.yaml includes the vendor-neutral ufs-common.yaml through allOf;
- vendor-neutral ufs-common.yaml defines the VCC supply and vcc-max-microamp properties, but not the Qualcomm legacy voltage interval.

Adding the optional property to qcom,ufs-common.yaml makes it valid for Qualcomm UFS hosts, including DBY-W09 once ROUND32 adds qcom,sm8250-ufshc to the Qualcomm binding selection/compatible list, while leaving other vendor bindings unchanged.

## 2. Exact pinned binding relationships

### 2.1 Qualcomm host binding

Pinned source: [Documentation/devicetree/bindings/ufs/qcom,ufs.yaml](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/ufs/qcom,ufs.yaml).

- It selects Qualcomm UFS host nodes by the compatible list.
- It declares Qualcomm-specific host properties.
- Its allOf references qcom,ufs-common.yaml.
- It closes the evaluated node property set with unevaluatedProperties: false.

The pinned base compatible list does not yet include qcom,sm8250-ufshc; ROUND32 is the separate draft that adds the SM8250 Qualcomm host. This review assumes that dependent compatible addition is present when schema validation runs.

### 2.2 Qualcomm common binding

Pinned source: [Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml).

- It owns common properties across the Qualcomm UFS host binding family, such as clocks, interconnects, PHYs, power-domains and resets.
- It references the generic ufs-common.yaml.
- The Qualcomm host schema consumes this file through allOf, so a property defined here is evaluated by the qcom host schema.

### 2.3 Vendor-neutral UFS common binding

Pinned source: [Documentation/devicetree/bindings/ufs/ufs-common.yaml](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/ufs/ufs-common.yaml).

This file already defines:
- vcc-supply;
- vccq-supply;
- vccq2-supply;
- vcc-max-microamp;
- vccq-max-microamp;
- vccq2-max-microamp.

It is the vendor-neutral layer and is not the right place for a property whose established semantics come from the Qualcomm UFS platform parser/driver. Putting vcc-voltage-level here would expose a Qualcomm downstream extension to every UFS controller binding inheriting the generic common schema.

## 3. Proposed schema contract

A narrow property definition in qcom,ufs-common.yaml should express:
- the UFS VCC consumer's min/max operating voltage request;
- units of microvolts;
- exactly two unsigned 32-bit cells;
- both entries non-zero.

A conceptual YAML shape is:

```yaml
  vcc-voltage-level:
    $ref: /schemas/types.yaml#/definitions/uint32-array
    minItems: 2
    maxItems: 2
    items:
      minimum: 1
    description:
      Minimum and maximum voltage requested by the UFS host for its VCC
      regulator supply, in microvolts.
```

This is an example contract for 2号 AI to implement and validate using the pinned dt-schema version, not a claim that the schema snippet has been run through dt_binding_check.

### 3.1 Cross-cell ordering belongs in driver parsing

The portable array schema can enforce that there are exactly two positive u32 values. A standard per-item JSON schema does not conveniently express the relational condition that array item 0 must be less than or equal to array item 1.

The driver parser must therefore enforce:
- min_uV > 0;
- min_uV <= max_uV;
- reject a present but malformed property before any regulator is enabled.

Tests must cover reversed pairs and boundary values. Do not silently swap an inverted pair or substitute provider constraints.

## 4. Why this closes the observed ROUND27 diagnostic

ROUND81 recorded an unevaluatedProperties: false error for the UFS host's vcc-voltage-level.

Because the DBY-W09 host compatible is intended to be a Qualcomm SM8250 UFS host, the Qualcomm host binding chain is the correct schema scope. Declaring the property in qcom,ufs-common.yaml makes it an evaluated property in the qcom binding chain. It does not broaden the generic UFS base schema.

The binding-only change must land with the matching early driver parser and voltage-request lifecycle implementation. Adding the property to schema without driver support merely suppresses a diagnostic and would not restore the electrical consumer contract (ROUND82/84/88/89/91).

## 5. Binding/driver test sequence for 2号 AI

1. Add the property only to qcom,ufs-common.yaml and run dt_binding_check for the Qualcomm UFS binding chain.
2. Confirm the DBY-W09 SM8250 compatible is recognized through the separate ROUND32 compatible change.
3. Use schema tests for absent property, one cell, three cells, zero value, and valid two-cell values.
4. Use driver parser tests for min > max, missing VCC supply, and valid min/max pair. The driver must reject a malformed present property before the first VCC enable.
5. Confirm generic non-Qualcomm UFS bindings do not newly accept this Qualcomm-specific property.
6. Confirm schema validation accepts the DBY-W09 composite only after the actual driver consumer path is integrated.
7. Preserve the separate root compatible and /rootparam binding diagnostics; this schema change resolves only the UFS voltage-range property.

## 6. Ownership and boundaries

**This is a [1号 AI read-only binding-scope review] for 2号 AI.**
- 1号 AI: pinned schema relationship analysis and design recommendation.
- 2号 AI: owns the schema and driver implementation.
- Testing Agent: test executor only under a separate AGENT_TEST_TASK.md.
- The user is not asked to run commands.

No binding, driver, DTS, patch, config, 2号 AI branch, protected branch or PR was modified. No dt_binding_check, dtbs_check, dt-validate, compiler or device operation was run.

**Final status:** qcom,ufs-common.yaml is the narrowest common binding layer for this Qualcomm-specific VCC voltage interval. Driver-side min/max ordering and lifecycle enforcement remain mandatory. ROUND27 schema stays NOT CLEAN until implementation and validation are completed.
