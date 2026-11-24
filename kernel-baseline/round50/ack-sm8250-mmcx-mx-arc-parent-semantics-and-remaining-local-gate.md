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

Keep the UFS-only board DTS on the existing ACK RPMHPD/OPP model and keep full ARC equivalence explicitly unclaimed. Do not add an MMCX→MX parent edge to the shared SM8250 descriptor.

ROUND14 has now supplied the exact local base-FDT corner, set, dropout and proxy values; ROUND51 has reviewed their source semantics:
- Providers: `mmcxlvl` / resource `mmcx.lvl`; `mxlvl` / resource `mx.lvl`.
- MMCX ALL/AO/SO min/init corner 64 (LOW_SVS); MX MMCX-supply/AO min/init corner 16 (RETENTION); max 65535 is a logical storage ceiling.
- `qcom,set` 3/1/2 means ALL/ACTIVE/SLEEP.
- MMCX ALL/AO `qcom,min-dropout-voltage-level=<0xffffffff>`; in the public KONA implementation this is read into signed int and added numerically along the logical ARC parent request path as -1 on ARM64 two's-complement, not a no-dropout sentinel.
- MMCX ALL has a temporary proxy-enable request at TURBO..MAX.
- ROUND14 found no static S8 init-enable / boot-on / always-on property in the inspected base-FDT scope. Runtime S8 enable state remains UNKNOWN.

The remaining uncertainty is not the above captured node values; it is full ARC graph census, selected/effective DTBO, Command DB runtime level maps and actual runtime votes. Do not repeat ROUND14 FDT extraction. Do not create a DBY-W09-specific ARC compatible or patch a shared SM8250 GenPD parent relationship from corner-number similarity alone.

## 4. Verification status

| Item | Status |
|---|---|
| Public KONA vendor MMCX→MX ARC parent graph | SOURCE REVIEWED |
| Public KONA child min-dropout application path | SOURCE REVIEWED |
| Fixed ACK SM8250 descriptor lacks MMCX→MX parent | SOURCE REVIEWED |
| Generic GenPD parent performance-state translation | SOURCE REVIEWED |
| Exact HOS4.3 MMCX/MX set, corner, dropout and proxy properties | COMPLETE IN ROUND14; INTERPRETED IN ROUND51 |
| ROUND11 parent-edge count reconciliation | AT LEAST FIVE CONFIRMED; full total unverified |
| Exact HOS4.3 S8 static enable/boot properties | NOT_FOUND_IN_INSPECTED_SCOPE BY ROUND14; live state UNKNOWN |
| DBY-W09-specific parent edge or dedicated ARC provider implementation | DESIGN ONLY; NOT JUSTIFIED FOR STORAGE-FIRST |
| Full-tree source/schema/Kconfig/build/DTB/boot/runtime validation | NOT_RUN |

ROUND14 is complete and uploaded. Do not rerun the local FDT parser or rescan ROUND11/13/14 fields. No new local Agent task is active. Full ARC graph enumeration, selected DTBO identity, runtime RPMh votes and Command DB effective maps remain separate evidence/implementation gates; they do not block the conservative decision to keep the current ACK RPMHPD/OPP model for the first storage milestone.

## ROUND51 correction — ROUND14 resolves corner names and a fifth edge (2026-11-24)

ROUND14 is now complete. Local MMCX ALL/AO/SO min/init=64 maps to LOW_SVS; MX MMCX-supply/AO child min/init=16 maps to RETENTION; qcom,set values 3/1/2 are ALL/ACTIVE/SLEEP. MMCX ALL carries proxy-consumer-enable with voltage <384 65535> (TURBO..MAX). These values are logical ARC levels, not microvolts.

The raw qcom,min-dropout-voltage-level=<0xffffffff> on MMCX ALL/AO is not a no-dropout sentinel in the public KONA implementation. The parser stores it in signed int min_dropout_uV and regulator core adds it directly to the ARC list_voltage value; on the ARM64 two's-complement target this is -1 in the logical level value path. Do not normalize to zero. Exact hardware margin remains unmeasured.

ROUND14 also found mxlvl provider property pm8150a_s3_mmcx_sup_level-parent-supply=<122>, phandle 122 resolving to the CX MMCX-supply child. KONA rpmh_regulator_init_vreg_supply() constructs this exact property name from the child regulator-name, confirming it is a real parent edge. Thus ROUND11's four-edge set was incomplete: at least five base-FDT parent-supply edges are now proven. The full count is still not claimed because ROUND14 did not perform a full graph rescan. The six proxy-supply links remain a separate category.

ACK's fixed SM8250 RPMHPD OPP table includes the same canonical corner labels, but this does not make its shared per-domain GenPD model fully equivalent to HOS's child-specific ARC parent-supply chain and MMCX boot proxy request. Do not add a shared MMCX->MX parent pointer. Full ARC equivalence remains a separate gate. See ROUND51 for details.
