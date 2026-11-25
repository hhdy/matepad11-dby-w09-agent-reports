# ROUND82 — Corrected UFS VCC voltage-range schema remediation analysis

**Date:** 2026-11-25  
**Reviewer / researcher:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, under a new scoped task  
**Pinned target:** ACK android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Input:** ROUND27 report + legacy Qualcomm UFS binding/driver references

## 1. Correction to ROUND81

ROUND81 correctly identified that the current ACK 6.18.33 UFS binding rejects `vcc-voltage-level` and that the current ACK UFS code does not consume it. However, its initial recommendation to simply remove the property from the ACK-facing DTS is too aggressive and is **superseded by this report**.

The property has established Qualcomm downstream semantics. It expresses a pair of minimum/maximum VCC operating voltages in microvolts, and legacy Qualcomm UFS code parses that pair into the UFS VCC regulator descriptor and applies it with `regulator_set_voltage()` when enabling VCC.

The current ACK 6.18.33 baseline no longer carries that implementation. Thus the schema diagnostic exposes a real feature gap between the old Qualcomm consumer contract and the current ACK code, not merely dead/meaningless metadata. Removing the property without an electrically equivalent replacement would discard the UFS consumer-specific voltage range.

## 2. Legacy Qualcomm contract (evidence)

### 2.1 Binding meaning

The legacy Qualcomm UFS platform binding explicitly describes:
- `vcc-voltage-level` as the VCC supply voltage range;
- exactly a minimum/maximum pair;
- units of microvolts.

Source: [legacy Qualcomm `ufshcd-pltfrm.txt` binding](https://android.googlesource.com/kernel/msm/%2B/b5d151ed146abbf2fb5a1f004b6dfd04ec9c6032/Documentation/devicetree/bindings/ufs/ufshcd-pltfrm.txt).

### 2.2 Legacy parser

Legacy Qualcomm `drivers/scsi/ufs/ufshcd-pltfrm.c` reads `vcc-voltage-level` for the VCC regulator, checks the property length is exactly two 32-bit cells, and stores the cells in `vreg->min_uV` and `vreg->max_uV`. If the property is absent or malformed, that particular legacy revision falls back to broad UFS default VCC limits with a warning.

Source: [legacy Qualcomm `ufshcd-pltfrm.c`](https://android.googlesource.com/kernel/msm.git/%2B/313705e35923007fe451e4512cabb501179380de/drivers/scsi/ufs/ufshcd-pltfrm.c).

### 2.3 Legacy voltage application

Legacy UFS core code checks for a regulator with voltage-setting support and, when VCC has a valid min/max pair, calls `regulator_set_voltage(reg, min_uV, max_uV)` before enabling the regulator. When turning the rail off, it sets the minimum request to zero while retaining the maximum bound; only after configuration succeeds does it enable the regulator.

Source: [legacy Qualcomm UFS `ufshcd.c`](https://android.googlesource.com/kernel/msm/%2B/f24e1ee001e0515f2a60ca6d97a75fcc0c532a07/drivers/scsi/ufs/ufshcd.c).

This is a consumer-side regulator voltage request, not merely a schema annotation.

## 3. Exact ACK 6.18.33 difference

The exact pinned ACK source has removed this VCC min/max request path:

1. `include/ufs/ufs.h` defines `struct ufs_vreg` with only:
   - `struct regulator *reg`
   - `const char *name`
   - `bool always_on`
   - `bool enabled`
   - `int max_uA`
   
   There are no `min_uV` or `max_uV` members.

2. `drivers/ufs/host/ufshcd-pltfrm.c:ufshcd_populate_vreg()` reads the supply phandle and `<name>-max-microamp`; it does not parse `vcc-voltage-level`.

3. `drivers/ufs/core/ufshcd.c:ufshcd_config_vreg()` returns if the regulator has no voltage-count support; otherwise it delegates only to `ufshcd_config_vreg_load()`, which calls `regulator_set_load()`. There is no `regulator_set_voltage()` in this setup path.

4. The pinned `qcom,sc7180-ufshc.yaml` selects `qcom,sm8250-ufshc`, sets `unevaluatedProperties: false`, and does not declare `vcc-voltage-level`. `qcom,ufs-common.yaml` declares the VCC supply and max-current property but not the voltage-level property.

Pinned source references:
- [ACK `struct ufs_vreg`, `include/ufs/ufs.h`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/ufs/ufs.h)
- [ACK VCC regulator population, `ufshcd-pltfrm.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufshcd-pltfrm.c)
- [ACK regulator configuration, `ufshcd.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c)
- [ACK Qualcomm UFS binding](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.yaml)
- [ACK UFS common binding](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml)

## 4. DBY-W09 candidate values and why deletion is unsafe without replacement

The current DBY-W09 rev2 board candidate specifies:
- UFS VCC consumer range: `vcc-voltage-level = <2504000 2950000>` (2.504–2.950 V).
- PM8150 L17 regulator provider constraints: min 2.496 V, max 3.008 V.

These are not the same range. The provider node describes the regulator's board-level operating envelope, while the legacy UFS property describes a narrower consumer request. Simply deleting the consumer range and keeping only the broader regulator limits does not preserve the legacy request.

No evidence reviewed in ROUND82 proves that the broader L17 regulator limits alone are electrically equivalent to the narrower UFS consumer limits. The range must not be silently discarded or copied into regulator min/max by guess.

## 5. Recommended 2号 AI design decision

2号 AI should choose and document one of these paths before altering DTS:

### Path A — Preserve the legacy UFS VCC consumer contract in ACK (preferred if HOS behavior is intended)

Implement the VCC voltage range as a real consumer request, then add matching schema support:

1. Extend the UFS regulator descriptor with explicit min/max voltage fields, or an equivalent dedicated VCC-range structure.
2. Parse `vcc-voltage-level` strictly for the `vcc` rail only:
   - exactly two u32 cells;
   - min must be non-zero and <= max;
   - reject malformed arrays; do not silently fall back to broad voltage limits when the property is present but malformed.
3. Before VCC regulator enable, call `regulator_set_voltage(vcc, min_uV, max_uV)` when the regulator supports voltage changes; preserve correct rollback if voltage or load configuration fails.
4. On disable, release the consumer voltage request with the same safe ordering and semantics verified against the selected regulator-core API. Confirm interactions with shared consumers and regulator constraints.
5. Keep `vcc-voltage-level` in the DT only when this consumer path is actually present.
6. Add its two-cell u32 range declaration to the pinned Qualcomm UFS binding (likely `qcom,ufs-common.yaml` if the property is intentionally common to Qualcomm UFS hosts, otherwise a narrower Qualcomm host schema). The binding must describe units, pair semantics and validation limits; do not add a schema-only property without driver implementation.
7. Add tests for absent property, valid pair, malformed length, min > max, fixed-voltage regulator, voltage-capable regulator, failure rollback, shared regulator consumer and disable/re-enable.

### Path B — Do not implement the legacy consumer request

This path is acceptable only if 2号 AI obtains a hardware/source rationale that the board's regulator constraints or another real consumer mechanism fully replace the narrower VCC request. In that case:
- remove `vcc-voltage-level` from the candidate;
- document what now enforces the 2.504–2.950 V requirement;
- demonstrate that the new configuration is not wider than the hardware/UFS requirement;
- keep the regulator provider limits separate from the UFS consumer range unless evidence justifies changing them.

Do not choose Path B solely to make dt-validate green.

**1号 AI recommendation:** prefer Path A unless a source-backed, electrically equivalent replacement is found. This is a technical recommendation for 2号 AI to evaluate, not an implementation authorization.

## 6. Remaining schema diagnostics and recommended binding work

### 6.1 DBY-W09 root compatible

The pinned `Documentation/devicetree/bindings/arm/qcom.yaml` SM8250 board allow-list does not include `huawei,dby-w09`; the vendor-prefix database already recognizes `huawei,`.

2号 AI should propose adding `huawei,dby-w09` to the SM8250 compatible enumeration, or a properly scoped board binding consistent with the pinned tree. This changes schema recognition only, not the actual board DTS compatible identity.

Sources:
- [Pinned Qualcomm ARM binding](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/arm/qcom.yaml)
- [Pinned vendor prefixes](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/vendor-prefixes.yaml)

### 6.2 Huawei bootloader-owned rootparam properties

The composite has a node named `/rootparam` with five vendor-specific properties. A dedicated binding can be selected by a precise node-name/property selector, without adding a new `compatible` property to the bootloader-owned node. Linux binding guidance allows schemas to be selected by node name when compatible is absent.

Candidate shape (design only):
- `select` matches `$nodename: const: rootparam` together with the presence of `qcom,boardid` and/or `huawei,modem_id`.
- `qcom,boardid`: exactly four u32 cells.
- `huawei,modem_id`: exactly two u32 cells.
- `qcom,board_name`, `qcom,product_name`, `hardware_version`: strings.
- Keep the binding narrowly scoped to the actual Huawei rootparam shape and avoid imposing unrelated optional properties on every other vendor's rootparam.

Do not add `compatible = "huawei,..."` to `/rootparam` merely to silence dt-core diagnostics. First confirm that such a new property is harmless to HOS4.3 ABL parsing; a node-name selector avoids that risk.

Schema selection guidance: [Linux Devicetree JSON-schema writing guide](https://docs.kernel.org/devicetree/bindings/writing-schema.html).

## 7. ROUND27 report follow-up requirements

The completed test Agent report is accepted as proof of the three-target build and the diagnostics that it recorded. It has two reproducibility omissions:
- the actual `dt-validate -l` schema IDs/filenames are not printed (the report contains a placeholder);
- it does not state whether targeted `dtbs_check` availability was checked before falling back to `dt-validate`.

If 2号 AI issues a follow-up test task, it should require those exact details, full DTC warnings, all dt-validate diagnostic entries, and pre/post source hashes. The testing Agent must not independently rerun or make fixes without a new task.

## 8. Boundaries and status

1号 AI performed read-only inspection of pinned ACK source and legacy Qualcomm public source references. No code, DTS, binding, configuration, patch, branch or protected candidate was modified. No compiler/schema/device test was run.

**Final status:** schema remediation must preserve the actual VCC consumer voltage-range semantics. ROUND27 three-target build/property checks remain PASS; schema remains NOT CLEAN until the actual implementation and binding are aligned. Stage A device/boot gates remain closed.
