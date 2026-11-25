# ROUND86 — 1号 AI source review: PM8150 L17 voltage-table compatibility with the UFS VCC request

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, after a separate test task is issued  
**Pinned baseline:** ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Related records:** ROUND82, ROUND83, ROUND84

## 1. Executive result

**The pinned ACK PM8150 L17 regulator implementation can represent the DBY-W09 candidate's UFS VCC consumer interval of 2.504–2.950 V. No voltage-table/provider-constraint conflict was found at source level.**

The relevant facts are:
- The ACK PM8150 LDO17 descriptor uses `pmic5_pldo`, a voltage-adjustable VRM regulator with 256 linear voltage selectors, starting at 1.504 V in 8 mV increments.
- Its operation table includes `set_voltage_sel` and `list_voltage`, so the regulator core can map a consumer min/max request onto an available PMIC voltage selector.
- The candidate PM8150 L17 provider constraints are 2.496–3.008 V. Both endpoints are on the same 8 mV grid.
- The candidate UFS consumer range is 2.504–2.950 V. 2.504 V is an exact selectable point. 2.950 V is not itself a selector point; the highest available point not exceeding the consumer maximum is 2.944 V.
- Thus the interval contains supported selector values 2.504 V through 2.944 V in 8 mV increments. All these points lie within the candidate provider constraints.

This supports ROUND82's recommendation to restore a real UFS VCC consumer voltage request rather than delete the property to silence schema validation. It does **not** establish actual measured board voltage, power margin under load, HOS ARC/dropout equivalence, or first-boot behavior.

## 2. Exact pinned ACK regulator descriptor

Source: [ACK `drivers/regulator/qcom-rpmh-regulator.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c).

The file defines `pmic5_pldo` with:
- `regulator_type = VRM`;
- `ops = &rpmh_regulator_vrm_drms_ops`;
- one linear range: `REGULATOR_LINEAR_RANGE(1504000, 0, 255, 8000)`;
- `n_linear_ranges = 1`;
- `n_voltages = 256`.

The PM8150 regulator table maps `ldo17` to `&pmic5_pldo` and the supply lookup name `vdd-l13-l16-l17`:
- `RPMH_VREG("ldo17", "ldo%s17", &pmic5_pldo, "vdd-l13-l16-l17")`.

The VRM-DRMS operation table includes `set_voltage_sel = rpmh_regulator_vrm_set_voltage_sel` and `list_voltage = regulator_list_voltage_linear_range`, in addition to enable/disable and mode operations. Therefore this is not an XOB/fixed-only regulator descriptor.

The voltage set callback computes the selected voltage from the linear range and writes it in millivolts using `DIV_ROUND_UP(..., 1000)`. The selected L17 values on this 8 mV grid are already whole millivolts, so this conversion does not distort the points calculated below.

## 3. Selector arithmetic against DBY-W09 candidate constraints

The pinned range formula is:

```
V(selector) = 1,504,000 uV + selector * 8,000 uV
selector = 0..255
```

### 3.1 UFS consumer interval

Candidate property:
```dts
vcc-voltage-level = <2504000 2950000>;
```

Selector bounds:
- First selector at or above 2,504,000 uV: `(2,504,000 - 1,504,000) / 8,000 = 125`.
- Last selector at or below 2,950,000 uV: `floor((2,950,000 - 1,504,000) / 8,000) = 180`.
- Selector 180 is 2,944,000 uV.
- Selector 181 is 2,952,000 uV and exceeds the requested 2,950,000 uV maximum.

Therefore the request has 56 supported values (selectors 125 through 180, inclusive), from **2.504 V to 2.944 V**, at 8 mV steps. The requested maximum is a tolerance bound; the PMIC need not generate exactly 2.950 V for the range to be satisfiable.

### 3.2 Provider constraints

Candidate L17 node:
```dts
regulator-min-microvolt = <2496000>;
regulator-max-microvolt = <3008000>;
```

These correspond to:
- 2,496,000 uV = selector 124;
- 3,008,000 uV = selector 188.

The complete UFS consumer selector subset 125..180 is inside the provider selector envelope 124..188. Both consumer and provider bounds are aligned with the L17's 8 mV step grid, except the consumer's 2.950 V upper tolerance, which safely lies above selector 180 and below selector 181.

## 4. Implications for the 2号 AI implementation

1. **The PM8150 L17 provider does not need to be widened or changed to accommodate the consumer interval.** Its existing 2.496–3.008 V provider range already contains all selectable UFS request points.
2. Keep the consumer interval separate from provider constraints. Do not rewrite the UFS request as the L17 provider's 2.496–3.008 V range.
3. Once ROUND84's VCC parsing/lifecycle fix exists, `regulator_set_voltage(vcc, 2504000, 2950000)` has a valid selectable PMIC range on this pinned L17 descriptor. The regulator framework and RPMh regulator driver can select a supported point within the request interval.
4. Keep ROUND84's shared-helper isolation and voltage-request state/error handling requirements. This report does not supersede them.
5. If the VCC range is present without `vcc-supply`, it still cannot be enforced by this regulator path. That contradictory DT configuration must be rejected or handled by an explicitly justified policy.
6. This source check establishes neither the external PMIC input source nor the required HOS MMCX/MX ARC voltage/dropout translation. Those remain separate gates.

## 5. Evidence locations

Pinned ACK:
- [`pmic5_pldo` linear range and VRM-DRMS ops](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c)
- [PM8150 LDO17 descriptor mapping](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c)
- [RPMh regulator binding](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml)

Project candidate:
- [DBY-W09 rev2 board DTS candidate](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/dts/dby-w09-ack18-board.dts.rev2.candidate) — PM8150 L17 provider node and UFS VCC consumer.

## 6. Scope and ownership

**This is a [1号 AI read-only source-analysis report] for 2号 AI.**
- 1号 AI: independently verifies ACK source behavior and provides the selector calculation.
- 2号 AI: owns whether/how to implement the UFS VCC consumer request and binding.
- Testing Agent: may test only after a separate `AGENT_TEST_TASK.md` is issued.
- The user is not being asked to run any commands.

No source, DTS, binding, patch, build config, 2号 AI branch or protected branch was changed. No patch application, build, dt-schema run, electrical measurement, or device operation occurred.

**Final status:** PM8150 L17's pinned ACK voltage table and the current board candidate's provider/consumer ranges are numerically compatible at source level. ROUND27 schema remains NOT CLEAN until 2号 AI's driver+binding and the separate root-compatible/rootparam binding changes are implemented and tested.
