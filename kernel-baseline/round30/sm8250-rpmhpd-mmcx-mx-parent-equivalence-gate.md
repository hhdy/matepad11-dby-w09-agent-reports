# ROUND30 — SM8250 RPMHPD MMCX-to-MX parent/corner equivalence gate

Date: 2026-11-24

Status: source-side comparison of exact ACK tag android17-6.18.33_r00 against already approved/sanitized HOS4.3 ROUND11–ROUND24 evidence. No local FDT re-extraction, no firmware operation, no DTS edit, no patch application, no schema validation, no compile, no device boot or write.

Source pin:
- ACK tag: android17-6.18.33_r00
- target commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

## 1. Decision

ROUND29's UFS dual-GenPD candidate solves only the routing question: it can direct the UFS Host's one required-opps performance-state request to ACK SM8250 RPMHPD MMCX while keeping GCC UFS_PHY_GDSC as the independent physical PHY power domain.

It does not yet prove that ACK's MMCX domain reproduces the full HOS4.3 ARC dependency graph.

The key mismatch:
- HOS4.3's already-reported ARC graph contains an MMCX-level parent-supply edge from the MMCX group to an MX-level group.
- ACK android17-6.18.33_r00 selects the plain mmcx / mmcx_ao descriptors for SM8250. Those descriptors have no .parent pointer. The same source has a CX-with-MX-parent variant, but SM8250 selects it only for CX, not MMCX.
- Therefore the proposed UFS vote reaching ACK MMCX must not be described as automatically propagating to MX.

**Do not silently add an MMCX→MX parent in DTS or claim the two implementations are equivalent.** A new SM8250-specific RPMHPD descriptor variant is a possible source-code design, not a confirmed fix. It remains blocked on exact HOS4.3 ARC resource/set/corner evidence and a deliberate assessment of whether UFS actually requires the parent vote.

## 2. HOS4.3 evidence already available

ROUND11/ROUND16 resolved four legacy ARC parent-supply edges. The two relevant HOS4.3 MMCX entries are:

| HOS group | Child property | Resolved parent target |
|---|---|---|
| mmcxlvl | pm8150a_s4_level-parent-supply | mxlvl / regulator-pm8150a-s3-mmcx-sup-level |
| mmcxlvl | pm8150a_s4_level_ao-parent-supply | mxlvl / regulator-pm8150a-s3-level-ao |

This establishes that the HOS4.3 legacy ARC graph models an MMCX-to-MX logical-level dependency. It is not a PM8150 physical input-supply link.

The sanitized source reports do not yet capture the HOS4.3 values for:
- top-level qcom,resource-name on the mmcxlvl and mxlvl providers;
- qcom,set on the relevant child resources (ACTIVE / SLEEP / ALL participation);
- qcom,init-voltage-level;
- qcom,min-dropout-voltage-level;
- complete ARC AUX logical-corner-to-hardware-level mapping.

The existing ROUND7 property inventory was filtered and cannot prove these properties are absent. ROUND11 was deliberately limited to supply topology and does not establish the missing request semantics. ROUND22–ROUND24 explicitly retain these values as UNKNOWN / NOT_CAPTURED.

## 3. Exact ACK .33 RPMHPD mapping

In drivers/pmdomain/qcom/rpmhpd.c, the common descriptors include:
- cx_w_mx_parent and cx_ao_w_mx_parent, whose .parent pointers reference mx.pd and mx_ao.pd;
- plain mmcx and mmcx_ao, which define peer relationships and mmcx.lvl resource names but have no .parent pointers;
- mmcx_w_cx_parent / mmcx_ao_w_cx_parent, a different parented MMCX variant used by later SoC descriptor tables, with parent CX/CX_AO rather than MX/MX_AO.

The exact sm8250_rpmhpds[] table selects:
- RPMHPD_CX → cx_w_mx_parent;
- RPMHPD_CX_AO → cx_ao_w_mx_parent;
- RPMHPD_MMCX → plain mmcx;
- RPMHPD_MMCX_AO → plain mmcx_ao;
- RPMHPD_MX / RPMHPD_MX_AO → plain mx / mx_ao.

In rpmhpd_probe(), ACK initializes each descriptor as a GenPD and calls pm_genpd_add_subdomain(parent, child) only when the selected rpmhpd object has a non-NULL .parent. Consequently the current SM8250 MMCX selection has no GenPD parent edge to MX. The existing CX→MX path does not implicitly make MMCX→MX a child relationship.

The driver aggregates active/sleep peer votes for each RPMh resource. GenPD parent propagation is a separate hierarchy mechanism; one resource's vote does not automatically create another resource's parent relationship merely because HOS ARC had one.

### Exact parent performance-state translation in ACK .33

The generic ACK GenPD implementation was also inspected. When a GenPD child has a parent link and its performance state changes, _genpd_set_parent_state() calls genpd_xlate_performance_state(child, parent, state) before applying the parent request.

In the exact .33 OPP core, dev_pm_opp_xlate_performance_state() returns the incoming pstate unchanged when the source GenPD OPP table has no required_opp_count. The SM8250 RPMHPD provider uses one operating-points-v2 table containing the shared RETENTION / MIN_SVS / LOW_SVS / SVS / NOM / TURBO opp-level entries; those entries do not contain required-opps mappings to another GenPD table. Consequently, if a custom MMCX descriptor were given an MX parent link while retaining this OPP table, generic GenPD would pass the same performance-state value to MX (one-to-one), not calculate a HOS-specific dropout delta.



**ROUND30 refinement — parent state translation:** ACK .33 generic GenPD propagates a child's state to a parent when a parent link exists, using dev_pm_opp_xlate_performance_state(). The SM8250 RPMHPD provider uses the same operating-points-v2 table for its domains, whose entries have opp-level values but no required-opps map to a parent table. The generic helper therefore passes the same pstate to the MX parent (one-to-one). A descriptor parent pointer alone does not reproduce a non-zero HOS qcom,min-dropout-voltage-level delta. That HOS property is still UNKNOWN / NOT_CAPTURED, so the parent/corner gate remains open.

This narrows the possible port:
- Adding a parent pointer alone would make ACK propagate the same OPP state to MX.
- It would not implement a non-zero HOS qcom,min-dropout-voltage-level rule unless an explicit OPP-level translation or a deliberately reviewed driver mechanism supplied that mapping.
- The local HOS4.3 value of qcom,min-dropout-voltage-level remains UNKNOWN / NOT_CAPTURED.

The new GenPD source review therefore does not close the HOS equivalence gate; it describes exactly what a simple descriptor change would and would not do.

## 4. What this means for ROUND29

ROUND29 proposes:
1. UFS Host power-domain index 0 = RPMHPD MMCX;
2. UFS Host power-domain index 1 = GCC UFS_PHY_GDSC;
3. explicitly map the existing single UFS required-OPP slot 0 to the MMCX virtual GenPD device;
4. keep UFS PHY attached to the GCC GDSC.

If implemented exactly as proposed, the UFS performance-state request reaches the plain ACK SM8250 MMCX domain. On the inspected descriptor table, that MMCX vote does not itself have an ACK GenPD parent link to MX.

So the UFS routing candidate is not yet a complete HOS4.3 ARC-topology port. It may still be sufficient for the first storage milestone if:
- the hardware/firmware's required UFS corner can be satisfied by the MMCX vote as exposed through the ACK descriptor; or
- the relevant HOS ARC parent relationship is not a required UFS boot dependency in this configuration.

Neither condition has yet been demonstrated by local evidence or runtime measurement.

## 5. Possible implementation directions — none selected

### Option A — keep plain SM8250 MMCX for the first UFS test

Keep the upstream sm8250_rpmhpds[] mapping unchanged and implement ROUND29's UFS dual-GenPD routing. Record MMCX→MX equivalence as an explicit remaining power-corner risk.

This minimizes source delta and tests whether UFS storage can initialize under the SoC's upstream RPMHPD model. It is not permission to assume full HOS equivalence or to enable additional multimedia consumers.

### Option B — add a DBY-W09/SM8250-specific MMCX-with-MX-parent descriptor

The existing RPMHPD driver demonstrates the parented-domain mechanism for CX→MX and for MMCX→CX on other SoCs. A dedicated MMCX→MX descriptor pair could be prototyped by adding parent pointers to the MMCX active and AO domain descriptors and selecting them only for a narrowly scoped DBY-W09 SM8250 variant.

This is not an approved patch direction yet:
- do not change the generic SM8250 descriptor for every SM8250 board without wider validation;
- do not assume the HOS ARC parent edge's dropout semantics equal the ACK GenPD hierarchy;
- do not assume HOS logical corner numbers equal ACK RPMHPD OPP levels;
- do not assume the same active/sleep request membership;
- assess interactions with the existing CX→MX path and peer aggregation;
- prove that the UFS use case needs this dependency.

### Option C — deliberately port the legacy HOS ARC provider

ROUND22/ROUND23 describe the alternative: an ACK-native ARC aggregate provider with AUX mapping, active/sleep aggregation, pseudo-enable semantics, parent/dropout handling and a direct apps_rsc child device to satisfy the current RPMh controller lookup API.

This is much larger than a UFS-specific parent edge and must not be folded into the first UFS patch without proving it is required for boot.

## 6. Required evidence before selecting a direction

After the current ROUND12 AVB task and already-queued ROUND13 regulator mode/DRMS check have finished, a narrowly scoped local read-only property check may capture only:
- qcom,resource-name for the existing mmcxlvl and mxlvl groups;
- relevant child qcom,set values;
- qcom,init-voltage-level;
- qcom,min-dropout-voltage-level;
- whether the MMCX UFS-related child participates in ACTIVE, SLEEP or both.

This must reuse the previously reviewed parser/workflow, not reparse the ROUND11 parent/proxy phandle graph, and must not upload FDT/DTBO or AUX binary data. It is not a new active Agent task now; ROUND12 remains the only active local task and ROUND13 stays queued.

GPT-side source work should:
- compare exact ACK .33 RPMHPD descriptor and GenPD aggregation behavior;
- inspect the generic GenPD parent performance-state propagation and required-OPP translation;
- determine whether a DBY-W09-specific MMCX→MX descriptor can be expressed without affecting unrelated SM8250 consumers;
- keep the option open until HOS4.3 resource and corner evidence is available.

## 7. Verification status

| Item | Status |
|---|---|
| HOS4.3 has MMCX ARC parent-supply edge to MX-level group | SOURCE-REPORTED / PHANDLE RESOLVED in ROUND11/16 |
| HOS4.3 MMCX/MX resource names | UNKNOWN / NOT_CAPTURED |
| HOS4.3 relevant qcom,set values | UNKNOWN / NOT_CAPTURED |
| HOS4.3 init/dropout/corner AUX semantics | UNKNOWN / NOT_CAPTURED |
| ACK .33 SM8250 selects CX-with-MX-parent | SOURCE REVIEWED |
| ACK .33 SM8250 selects plain MMCX without MX parent | SOURCE REVIEWED |
| ACK .33 has an MMCX-with-CX-parent variant for other SoCs | SOURCE REVIEWED |
| ACK .33 generic GenPD parent state propagation | SOURCE REVIEWED |
| ACK .33 RPMHPD child/parent OPP translation with current shared table | SOURCE-REVIEWED ONE-TO-ONE pstate when no required-opps mapping exists |
| HOS4.3 parent dropout delta and equivalence to ACK one-to-one pstate | UNKNOWN / NOT_CAPTURED |
| ROUND29 UFS request can be routed to MMCX | DESIGN CANDIDATE / SOURCE-REVIEWED |
| ROUND29 UFS request also reproduces HOS MMCX→MX edge | NOT ESTABLISHED |
| New DBY-W09-specific MMCX→MX RPMHPD descriptor | POSSIBLE DESIGN ONLY / NOT IMPLEMENTED |
| Full HOS4.3 ARC provider port required for UFS boot | UNKNOWN |
| DTS/driver patch, schema, Kconfig, compile, runtime votes | NOT RUN |

## 8. Sources

- Exact ACK tag: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00
- Exact ACK SM8250 descriptor table and parent variants: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/pmdomain/qcom/rpmhpd.c
- Exact ACK GenPD parent/child registration: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/pmdomain/core.c
- Existing HOS4.3 parent graph report: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round16/hos43-rpmh-arc-parent-graph-to-ack-dts.md
- Legacy ARC implementation feasibility: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round22/ack-rpmh-arc-and-proxy-consumer-port-feasibility.md
- ARC provider aggregation/device hierarchy: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round23/ack-arc-provider-device-and-aggregation-design.md
- HOS logical-corner semantics: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round24/hos43-arc-logical-corner-dt-semantics.md
- UFS routing gap and candidate correction: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round27/ack-sm8250-ufs-rpmhpd-required-opp-routing-gap.md
- ROUND29 exact UFS dual-GenPD design: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round29/ack-qcom-ufs-dual-genpd-required-opp-probe-integration.md
