# ROUND24 — HOS4.3 ARC logical-corner and Device Tree semantics

Date: 2026-11-24

Status: legacy Qualcomm downstream binding/source review plus the existing sanitized ROUND7 property inventory and ROUND11 parent graph. No local re-extraction or new parser. No DTS/schema compile, Kconfig resolution, kernel build, boot, device access or write.

## 1. The key semantic distinction

For ordinary PMIC VRM regulators, regulator-min-microvolt and regulator-max-microvolt are physical voltages in microvolts.

For legacy Qualcomm RPMh ARC regulators, the same generic regulator properties intentionally carry logical RPMH_REGULATOR_LEVEL identifiers (roughly 1–513). They are corner / performance-level values, not physical microvolt measurements.

The ARC regulator driver's list_voltage callback returns the logical corner identifier from the resource's Command DB AUX map. Its set_voltage_sel callback sends the selected hardware ARC level. The AUX map translates a logical corner into a 4-bit hardware level from 0 through 15.

Sources:
- Legacy RPMh regulator binding: https://android.googlesource.com/kernel/msm.git/%2B/5e38624d74de6c07495e6e50605bbd9cbf1d8698/Documentation/devicetree/bindings/regulator/rpmh-regulator.txt
- ARC selector implementation: https://android.googlesource.com/kernel/msm/%2B/cc4f613cfcde9e379c409d43ffd7fc9e64427363/drivers/regulator/rpmh-regulator.c
- Same-family Kona regulator DTS example: https://android.googlesource.com/kernel/msm.git/%2B/494fd11726717faabf58dbf2d7f56e58baafdda1/arch/arm64/boot/dts/qcom/kona-regulators.dtsi

## 2. Required and optional ARC binding properties

At provider/resource node level:
- compatible = qcom,rpmh-arc-regulator;
- qcom,resource-name identifies the ARC resource in Command DB;
- qcom,send-defaults optionally sends the default aggregated request during probe;
- qcom,always-wait-for-ack optionally forces synchronous ACK handling;
- an optional awake-state selector exists in some downstream revisions, but ACK's RSC API does not expose RPMH_AWAKE_STATE and must not inherit it blindly.

At each regulator child:
- regulator-name identifies the logical endpoint;
- regulator-min-microvolt and regulator-max-microvolt define the minimum and maximum logical RPMH_REGULATOR_LEVEL corner IDs;
- qcom,set is required and selects ACTIVE, SLEEP or ALL request sets (binding values 1, 2 or 3);
- qcom,init-voltage-level optionally requests an initial logical corner;
- qcom,min-dropout-voltage-level optionally defines the minimum parent-to-child logical level delta, meaningful only with a parent-supply relationship;
- the provider's parent-supply property can define the ARC regulator framework dependency.

These are not ordinary PMIC LDO electrical voltage limits. Do not translate them into 0.8 V / 1.0 V values or merge them into the VRM output regulator table.

## 3. What ROUND7's selected HOS4.3 inventory already shows

The existing sanitized property inventory contains these representative ARC child constraints:
| ARC child endpoint | Minimum logical corner | Maximum logical corner |
|---|---:|---:|
| pm8150_s3_level | 16 | 65535 |
| pm8150_s3_mmcx_sup_level | 48 | 65535 |
| pm8150a_s4_level | 64 | 65535 |
| pm8150_l4_level | 16 | 65535 |
| pm8150_l11_level | 16 | 65535 |
| pm8150a_s1_level | 16 | 65535 |
| pm8150a_s6_level | 16 | 65535 |

The value 65535 is the raw maximum sentinel in the property inventory. Its precise meaning in the target's chosen regulator binding/runtime constraints must be preserved as encoded; do not reinterpret it as a real physical voltage.

Contrast with the same selected HOS4.3 inventory's VRM output constraints:
- PM8150 L5: 880000 uV;
- PM8150 L9: 1200000 uV;
- PM8150 L14: 1800000–1880000 uV;
- PM8150A L11: 3104000–3304000 uV.

This demonstrates why the driver must branch by regulator type before interpreting regulator-min/max-microvolt.

## 4. What is still not known locally

The ROUND7 selected inventory was designed for identity, PMIC/GPIO and other specific categories. Its ARC rows expose compatible, regulator-name and regulator min/max only; it does not show the following properties:
- qcom,resource-name on each aggregate ARC group;
- qcom,set on each ARC child;
- qcom,init-voltage-level;
- qcom,min-dropout-voltage-level;
- qcom,send-defaults;
- qcom,always-wait-for-ack;
- any downstream qcom,use-awake-state field.

These values remain UNKNOWN / NOT_CAPTURED by that inventory. Do not write NOT_FOUND. The ROUND11 task intentionally scanned only supply/vin/parent names, so it did not close this gap either.

The exact Command DB AUX tables for the HOS4.3 ARC resources also remain unread in the sanitized inventory. They must be obtained by the future ARC driver at runtime using cmd_db_read_aux_data(); they must never be hardcoded from a generic SM8250 table.

## 5. Porting requirements

A valid ARC provider must:
1. Branch by ARC type so generic regulator constraints are interpreted as logical corner IDs.
2. Validate the resource name, CMD_DB slave type, address and AUX length.
3. Read the little-endian u16 AUX map, require 1–16 entries and even byte length, and ignore permitted trailing zero padding.
4. Register the child regulator with the AUX map as list_voltage data and use set_voltage_sel/get_voltage_sel for ARC selector semantics.
5. Honour qcom,set active/sleep membership independently per child.
6. Preserve qcom,init-voltage-level, optional parent level delta, parent dependency, pseudo-enable and aggregate max vote behavior.
7. Keep logical corner state separate from actual PM8150 VRM voltage constraints.
8. Use the direct apps_rsc child device context defined in ROUND23 and ACK's device-based RPMh APIs.

No such driver or binding has been implemented in this round.

## 6. Verification status

| Item | Status |
|---|---|
| Legacy ARC min/max logical-corner semantics | SOURCE REVIEWED |
| ARC list_voltage / set_voltage_sel behavior | SOURCE REVIEWED |
| HOS4.3 ARC example min/max values | EXISTING ROUND7 INVENTORY REVIEWED |
| HOS4.3 qcom,resource-name values | UNKNOWN / NOT_CAPTURED |
| HOS4.3 qcom,set values | UNKNOWN / NOT_CAPTURED |
| HOS4.3 init/dropout/send-defaults/always-wait fields | UNKNOWN / NOT_CAPTURED |
| HOS4.3 raw Command DB AUX maps | UNKNOWN / NOT_CAPTURED |
| ARC driver source / binding / Kconfig | NOT_IMPLEMENTED |
| DTS/schema build / kernel build / boot | NOT_RUN |

## 7. Next step

After ROUND12 AVB metadata is completed, a narrow read-only local property scan may be issued for only the HOS4.3 ARC provider properties listed in section 4 and qcom,proxy-consumer-* request flags. It must reuse the previously reviewed FDT parser, not reparse the supply graph, and report only sanitized property names/values needed for the port. Until then, keep ARC nodes out of the UFS-first draft and keep proxy consumer support conditional.
