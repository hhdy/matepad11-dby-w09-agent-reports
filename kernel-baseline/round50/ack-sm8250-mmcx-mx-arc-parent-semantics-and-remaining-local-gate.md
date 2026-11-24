# ROUND50 — HOS4.3 MMCX→MX ARC parent semantics versus ACK SM8250 RPMHPD

Date: 2026-11-24

## Scope and source baseline

This report extends ROUND30 using the public Qualcomm SM8250 KONA source as a structural analogue, while keeping the DBY-W09 HOS4.3 local property gaps explicit.

Fixed ACK baseline:
- tag `android17-6.18.33_r00`
- commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

Public Qualcomm KONA reference:
- repository `OnePlusOSS/android_kernel_oneplus_sm8250`
- commit `cad09e061ef6cf689a4a1e54d27562e0f042236a`

This is source review only. No local FDT was parsed in this round, and no kernel/DTB was built or booted.

## 1. What public KONA source proves

### 1.1 Vendor ARC graph

Public KONA `arch/arm64/boot/dts/vendor/qcom/kona-regulators.dtsi` defines three distinct logical RPMh ARC providers:

- `rpmh-regulator-mxlvl`, resource name `mx.lvl`
- `rpmh-regulator-cxlvl`, resource name `cx.lvl`
- `rpmh-regulator-mmcxlvl`, resource name `mmcx.lvl`

Its MMCX group contains two distinct parent-supply edges:
- `pm8150a_s4_level-parent-supply` → the MX group's `regulator-pm8150a-s3-mmcx-sup-level` child
- `pm8150a_s4_level_ao-parent-supply` → the MX group's `regulator-pm8150a-s3-level-ao` child

The same KONA DTS defines the MX parent child `regulator-pm8150a-s3-mmcx-sup-level` with a logical corner range / initial level separate from the MMCX child. The MMCX ALL and AO children also have different `qcom,set` membership and different constraints. This is not one generic edge to one generic parent node: active/all and AO paths are explicitly distinct.

Source: [KONA regulator DTS](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/arch/arm64/boot/dts/vendor/qcom/kona-regulators.dtsi), source blob `49936ae5f014ab7d4925f4bb9178eee36136e5f3`.

### 1.2 ARC child minimum-dropout handling

The same KONA RPMh regulator driver:
- reads `qcom,init-voltage-level` for an ARC child and maps it through the Command DB AUX-derived logical level table;
- reads optional `qcom,min-dropout-voltage-level` and assigns the result to the regulator descriptor's `min_dropout_uV`.

The KONA regulator core then uses the child descriptor's `min_dropout_uV` when propagating a child voltage request to its parent regulator. It obtains the child's requested corner-level voltage, adds the min-dropout amount, and requests the parent supply to provide that value before setting the child. Therefore the vendor `*-parent-supply` edge is a real regulator dependency with regulator-core voltage propagation, not just a decorative graph edge.

Sources:
- [KONA RPMh regulator driver](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/rpmh-regulator.c), blob `e6667c59818621a99bc53fc560e353d8c25e14e5`
- [KONA regulator core](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/core.c), blob `9fc11af942334b43d4c42bca34144bd9e55a5ead`

The public KONA example writes `qcom,min-dropout-voltage-level = <(-1)>` on the MMCX ALL/AO children. The vendor driver reads this using `of_property_read_u32()` and stores it in an `int` descriptor field; regulator core later adds that field as a numeric microvolt adjustment. Do **not** re-label `-1` as a proven special enum or infer that HOS4.3 uses the same value. The target HOS4.3 values were not captured by ROUND7/ROUND11/ROUND13. The public KONA source is a platform analogue, not a substitute for the exact local FDT.

### 1.3 Same-device local evidence still incomplete

ROUND11 already resolved the DBY-W09 HOS4.3 parent graph:
- MMCX `pm8150a_s4_level` → MX `regulator-pm8150a-s3-mmcx-sup-level`
- MMCX AO `pm8150a_s4_level_ao` → MX AO `regulator-pm8150a-s3-level-ao`

ROUND24 explicitly states the selected ROUND7 property inventory did not export the exact parent groups' `qcom,resource-name`, child `qcom,set`, `qcom,init-voltage-level`, or `qcom,min-dropout-voltage-level`. Its min/max summary by regulator name is not enough to reconstruct the exact phandle target child's full constraints because similar child names appear under different provider groups.

Therefore, the DBY-W09 local ARC parent graph's complete voltage/corner contract remains UNKNOWN. No second local FDT pass has been performed in ROUND50.

## 2. What fixed ACK SM8250 RPMHPD does

The pinned ACK `drivers/pmdomain/qcom/rpmhpd.c` declares:
- plain `mmcx` / `mmcx_ao` objects with resource `mmcx.lvl`, no parent pointer;
- `mx` / `mx_ao` objects with resource `mx.lvl`;
- SM8250's descriptor explicitly maps `RPMHPD_MMCX` to plain `mmcx` and `RPMHPD_MMCX_AO` to plain `mmcx_ao`;
- SM8250 CX/CX_AO use the separate `*_w_mx_parent` descriptors.

This confirms the ROUND30 gap at the pinned ACK tag: stock SM8250's RPMHPD descriptor does not create an MMCX→MX parent edge.

The generic GenPD framework can propagate a child performance state to a parent. It first calls `genpd_xlate_performance_state(child, parent, pstate)`; if the parent has no `set_performance_state`, it forwards the same value, otherwise it uses `dev_pm_opp_xlate_performance_state(child->opp_table, parent->opp_table, pstate)`. It then aggregates/sets that parent performance state. This mechanism translates between OPP tables, not the vendor ARC regulator's explicit min-dropout voltage property.

In the fixed ACK SM8250 RPMHPD topology, the domains use the shared RPMHPD performance-state/OPP model. Adding a generic MMCX→MX GenPD edge would therefore require confirming that the MMCX and MX OPP tables/corner maps represent the correct corresponding states. It would not automatically recreate an arbitrary positive vendor dropout delta or the distinct ALL/AO supplier target semantics.

Source anchors:
- ACK `drivers/pmdomain/qcom/rpmhpd.c`: SM8250 descriptor table maps plain MMCX and independent MX; `rpmhpd_probe()` adds only declared descriptor parents as GenPD subdomains.
- ACK `drivers/pmdomain/core.c`: `genpd_xlate_performance_state()`, `_genpd_set_parent_state()`, and `_genpd_set_performance_state()` implement OPP-table translation and parent aggregation.

## 3. Architecture choices and current recommendation

### Option A — add an MMCX→MX parent to the shared SM8250 descriptor

Not recommended from current evidence:
- It changes the shared `qcom,sm8250-rpmhpd` descriptor for every SM8250 board using that provider, not just DBY-W09.
- Generic GenPD parent propagation only works in the performance-state/OPP model; it does not import the vendor ARC `qcom,min-dropout-voltage-level` semantics or per-child `qcom,set` and proxy behavior automatically.
- The exact HOS4.3 MMCX child and MX target properties are missing from current sanitized reports.

### Option B — introduce a DBY-W09-specific RPMHPD compatible/descriptor

Technically possible as a source architecture, but not justified yet:
- It would require a compatible-specific match entry in the ACK RPMHPD driver and binding/schema changes.
- It still needs exact local MX/MMCX level metadata and compatible OPP-table mappings.
- A separate compatible alone does not implement an arbitrary dropout delta or vendor ARC request aggregation.

### Option C — implement a dedicated ACK-compatible ARC regulator provider

This is the closest semantic match to the HOS4.3 evidence:
- Keep a separate ARC-capable provider/child regulator graph under the appropriate RSC device context.
- Read Command DB ARC AUX maps at runtime rather than hardcoding public KONA level tables.
- Implement each child's active/sleep set membership, init logical corner, parent-supply dependency / min-dropout, proxy and aggregation semantics only where the exact local evidence requires them.

This is a larger port with separate driver/binding/Kconfig/lifecycle work. It must not be pulled into the first UFS/storage milestone unless that subsystem is demonstrated to require it for first boot.

### Current recommendation

Keep the UFS-only board DTS on the existing ACK RPMHPD/OPP model and keep full ARC equivalence explicitly unclaimed. Do not add an MMCX→MX parent edge to the shared SM8250 descriptor yet. First obtain the exact existing HOS4.3 property values for:
- `rpmh-regulator-mmcxlvl` and `rpmh-regulator-mxlvl` resource names;
- MMCX ALL/AO/SO and the exact two MX target children resolved by ROUND11;
- `qcom,set`, `regulator-min/max-microvolt` (logical corner indices), `qcom,init-voltage-level`, `qcom,min-dropout-voltage-level`;
- provider/child proxy flags and voltage/current requests relevant to those nodes.
Also inspect the already-existing S8 `qcom,init-enable` / standard boot-on / always-on fields because ROUND49 found its load-only UFS vote may not actually invoke the driver callback without an enable reference.

## 4. Verification status

| Item | Status |
|---|---|
| Public KONA vendor MMCX→MX ARC parent graph | SOURCE REVIEWED |
| Public KONA child min-dropout application path | SOURCE REVIEWED |
| Fixed ACK SM8250 descriptor lacks MMCX→MX parent | SOURCE REVIEWED |
| Generic GenPD parent performance-state translation | SOURCE REVIEWED |
| Exact HOS4.3 MMCX/MX dropout and request properties | UNKNOWN / NOT_CAPTURED |
| Exact HOS4.3 S8 init-enable / boot-on policy | UNKNOWN / NOT_CAPTURED |
| DBY-W09-specific parent edge or ARC provider implementation | DESIGN ONLY |
| Full-tree source/schema/Kconfig/build/DTB/boot/runtime validation | NOT_RUN |

The next step requires a tightly scoped local, read-only property extraction using the previously approved ROUND3 parser and the existing FDT work copy. It must not repeat ROUND11's parent phandle extraction or ROUND13's mode scan, and must not create a new parser or touch the device.
