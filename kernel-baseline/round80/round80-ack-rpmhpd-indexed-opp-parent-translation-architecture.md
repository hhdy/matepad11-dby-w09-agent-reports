# ROUND80 — ACK 6.18.33 RPMhPD indexed-OPP parent translation architecture

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Target baseline:** ACK android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Inputs:** pinned upstream source + accepted ROUND25 HOS4.3 report  
**Scope:** read-only generic GenPD / OPP / Qualcomm RPMhPD architecture investigation

## 1. Result

**ARCHITECTURE FEASIBILITY: CONFIRMED. DEVICE-SPECIFIC MMCX→MX IMPLEMENTATION: BLOCKED BY EVIDENCE.**

The pinned ACK source does provide a supported mechanism for translating a child power-domain performance state into a different parent-domain performance state:

1. Qualcomm RPMhPD descriptors create a static GenPD parent/child link.
2. GenPD propagates performance-state requests through that link.
3. dev_pm_opp_xlate_performance_state() translates the child state using the child's OPP entry and its required-opps reference into the destination parent OPP table.
4. The RPMhPD provider supports an indexed operating-points-v2 phandle array, so individual domain indexes can use different OPP tables.

This is more expressive than a same-state parent link. A bare parent link with one shared OPP table and no required-opps mapping still propagates the same pstate and is **not** an HOS-equivalent corner translation.

The architecture does not supply the missing HOS4.3 mapping values automatically. ROUND25 did not capture the AUX level table, the meaning of the stored 0xffffffff dropout field, the ARC parent-state derivation rule, or proof that UFS is an explicit HOS MMCX/MX consumer. No MMCX→MX change is authorized by this report.

## 2. Pinned ACK source findings

### 2.1 GenPD parent performance-state propagation

In drivers/pmdomain/core.c:

- genpd_xlate_performance_state() calls dev_pm_opp_xlate_performance_state(child->opp_table, parent->opp_table, pstate) when the parent supports performance states.
- _genpd_set_parent_state() computes the translated parent pstate, stores/aggregates the parent vote, and applies it recursively.
- _genpd_set_performance_state() propagates to parents **before** changing the child when scaling up, and propagates to parents **after** changing the child when scaling down. Failed updates attempt rollback.

Pinned source:
- [GenPD propagation and ordering, drivers/pmdomain/core.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/core.c#L400-L525)

### 2.2 OPP translation semantics

In drivers/opp/core.c, dev_pm_opp_xlate_performance_state(src_table, dst_table, pstate) behaves as follows:

- If the source table is absent or has no required-opps mappings, the input pstate is returned unchanged. This is the same-state behavior.
- If mappings exist, both tables must be GenPD OPP tables.
- The function finds which required-OPP table corresponds to the actual destination table.
- It finds the source OPP whose opp-level exactly matches the requested pstate and returns the level of that OPP's referenced destination OPP.
- Missing table/level mappings return an error instead of fabricating a state.

Pinned source:
- [dev_pm_opp_xlate_performance_state(), drivers/opp/core.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/opp/core.c#L2758-L2802)

**Consequence:** if a parent translation is implemented, every performance level that can actually be requested from the child must have a valid, matching OPP entry and a valid required-opps reference to the correct parent table. A one-point mapping is not enough to prove that all runtime votes are safe.

### 2.3 Per-domain indexed OPP tables are supported

In drivers/pmdomain/core.c, of_genpd_add_provider_onecell() loops over the provider's domain array and calls dev_pm_opp_of_add_table_indexed(&genpd->dev, i) for each performance-state-capable domain.

In drivers/opp/of.c:
- _opp_of_get_opp_desc_node() parses operating-points-v2 at the requested index; its source comment explicitly says the property can be an array for power-domain providers.
- _of_add_table_indexed() falls back to index 0 only when the property contains exactly one phandle. With multiple phandles, each GenPD index receives its indexed table.
- Required-OPP table references can be linked lazily when a referenced table is registered later.

Pinned sources:
- [of_genpd_add_provider_onecell(), drivers/pmdomain/core.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/core.c#L2738-L2834)
- [Indexed OPP parsing, drivers/opp/of.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/opp/of.c#L31-L43)
- [Indexed OPP table initialization, drivers/opp/of.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/opp/of.c#L1063-L1095)
- [Required OPP table linking, drivers/opp/of.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/opp/of.c#L115-L225)

### 2.4 Existing SM8250 RPMhPD driver hierarchy

In pinned drivers/pmdomain/qcom/rpmhpd.c:

- The driver already has parented descriptor variants mmcx_w_cx_parent and mmcx_ao_w_cx_parent.
- Their normal and active-only peer semantics are paired; the corresponding descriptors set parents to CX and CX_AO.
- The current sm8250_rpmhpds[] selects the parentless mmcx and mmcx_ao descriptors at indexes 6 and 7, and MX / MX_AO at indexes 8 and 9.
- SM8450 selects the existing MMCX-with-CX-parent variants, demonstrating that parented MMCX variants are already a supported implementation pattern, but it is not evidence that SM8250 should use MX as its parent.
- After descriptors are initialized, rpmhpd_probe() calls pm_genpd_add_subdomain(parent, child) for every descriptor with a parent pointer.

Pinned sources:
- [RPMhPD descriptors and SoC domain tables](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c#L125-L180)
- [SM8250 domain index table](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c#L465-L482)
- [RPMhPD parent link registration](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c#L1001-L1068)
- [SM8250 RPMhPD binding indexes](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/dt-bindings/power/qcom,rpmhpd.h)

### 2.5 Existing SM8250 DTS currently uses one shared OPP table

Pinned arch/arm64/boot/dts/qcom/sm8250.dtsi sets one scalar phandle:

rpmhpd: power-controller { operating-points-v2 = <&rpmhpd_opp_table>; ... }

The common RPMhPD table holds the standard levels (retention, min-SVS, low-SVS, SVS, SVS-L1, nominal, etc.). UFS OPP entries currently reference common rpmhpd_opp_low_svs and rpmhpd_opp_nom entries.

As a result, the current SM8250 DTS assigns the same OPP table to MMCX, MMCX_AO, MX and MX_AO. With no source required-opps translation on that shared parent/child table, generic GenPD preserves the pstate.

Pinned source:
- [SM8250 UFS OPP table](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/boot/dts/qcom/sm8250.dtsi#L2507-L2577)
- [SM8250 RPMhPD provider and shared OPP table](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/boot/dts/qcom/sm8250.dtsi#L6193-L6241)

## 3. Candidate architecture if future evidence authorizes MMCX→MX

This is a design outline only, not an implementation or patch.

1. Add separate static RPMhPD descriptor variants for MMCX→MX and MMCX_AO→MX_AO, analogous to the existing MMCX→CX / MMCX_AO→CX_AO pair. Select them only in a board/SoC variant for which the hierarchy is authoritatively proven; do not globally change SM8250 without board-level justification.
2. Provide indexed operating-points-v2 tables for the 10 SM8250 domain indexes. Unchanged domains can continue to reference the existing shared table. MMCX/MMCX_AO child tables would contain explicit required-opps references into the appropriate MX/MX_AO parent table(s); parent tables would expose the levels supported by their own RPMhPD command-database mapping.
3. Ensure UFS OPP required-opps points to the intended MMCX OPP entries if UFS is confirmed as an MMCX consumer.
4. Cover every possible requested child level, preserve the separate ALL/AO domain behavior, and test both ramp-up ordering and ramp-down ordering. Verify failure rollback and lazy OPP linking.
5. Run pinned DT schema and Kleaf targets only after the source and taskbook input identities are fixed; runtime rail validation remains a later, separate gate.

## 4. Why this cannot be implemented safely yet

ROUND25 facts:
- HOS4.3 has explicit MMCX ALL and AO parent edges to MX children by confirmed phandle owner.
- Captured child and parent qcom,init-voltage-level values differ: MMCX ALL 0x40 vs MX target 0x10.
- MMCX ALL/AO qcom,min-dropout-voltage-level is stored as 0xffffffff, whose meaning is UNKNOWN.
- AUX logical corner names / actual per-level table and HOS ARC parent-state derivation rule were not captured.
- HOS UFS host has no explicit MMCX/MX ARC consumer phandle in the available base FDT. ACTIVE/SLEEP participation through any non-DT-visible mechanism remains UNKNOWN.

Therefore:
- Do not infer that numeric 0x40 and 0x10 alone define a complete per-level translation.
- Do not treat 0xffffffff as a signed sentinel, zero dropout, one-step delta or any other guessed value.
- Do not convert ARC parent edges into PMIC physical supply dependencies.
- Do not add a bare parent relationship and claim HOS equivalence.
- Do not assert UFS is a HOS MMCX/MX ARC consumer without post-ABL/runtime evidence.
- Do not modify 2号 AI's branch or current DTS candidates based on this design outline.

ROUND25 is the authoritative input:
[round25-hos43-mmcx-mx-arc-request-semantics.txt](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round25/round25-hos43-mmcx-mx-arc-request-semantics.txt).

## 5. Required evidence before any implementation decision

- Exact CMD_DB AUX level tables for mmcx.lvl and mx.lvl from the target firmware/runtime, including active-only/peer behavior.
- Authoritative interpretation of HOS4.3 qcom,set active/sleep bits.
- Authoritative meaning of qcom,min-dropout-voltage-level = 0xffffffff and the HOS ARC provider's parent-state derivation algorithm.
- Proof whether DBY-W09 UFS actually votes MMCX/MX during ACTIVE, SLEEP or both (post-ABL FDT plus runtime/firmware evidence as available).
- Electrical/firmware review that the parent/child pair is valid for this board's actual RPMh resource graph.
- Build and schema validation of the complete per-index OPP table array and descriptor variant, followed by a controlled runtime vote test before device boot acceptance.

## 6. Review boundaries

1号 AI inspected public files at the exact pinned ACK commit and the existing accepted ROUND25 report. No kernel source, driver, DTS, patch, config or branch was modified. No compiler, Kleaf/Bazel build, dt-schema, board test, device operation or rail measurement was run.

**Final status: ACK source has a real per-domain OPP translation mechanism; DBY-W09 MMCX→MX hierarchy and mapping remain BLOCKED by missing evidence.**
