# ROUND74 — exact ACK SM8250 MMCX parent semantics and HOS4.3 ARC equivalence gate

Date: 2026-11-25
Owner: Primary AI, exact pinned ACK source review
Baseline: ACK android17-6.18.33_r00 / common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
Scope: source-only review; no DTS, driver, config, build or device change.

## 1. Executive result

The ROUND33 dual-GenPD helper and ROUND37 DTS delta route the UFS Host's required-opps request to ACK SM8250 RPMHPD MMCX. This resolves the OPP required-device routing gap, but it does NOT reproduce the complete HOS4.3 legacy ARC MMCX-to-MX relationship.

Exact pinned ACK source facts:
- drivers/pmdomain/qcom/rpmhpd.c defines a parentless plain mmcx and mmcx_ao pair with peer relationship and resource name mmcx.lvl.
- The same file defines cx_w_mx_parent and cx_ao_w_mx_parent with .parent pointers to MX/MX_AO.
- The sm8250_rpmhpds[] table selects CX as cx_w_mx_parent, but selects MMCX as plain mmcx.
- A separate mmcx_w_cx_parent / mmcx_ao_w_cx_parent pair exists for other SoC descriptors; it parents MMCX to CX, not MX.
- SM8450 and newer descriptor tables select the MMCX-with-CX-parent variant. SM8250 does not.
- rpmhpd probe registers GenPD parent-child links only when the selected descriptor has a non-NULL parent pointer.

Exact source:
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c#L120-L154
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c#L465-L482

Thus, with the current ROUND33+ROUND37 candidate:
- UFS OPP slot 0 can request a pstate on the MMCX GenPD device.
- That MMCX pstate does not automatically propagate to MX through an ACK GenPD parent link.
- The current implementation must not be described as equivalent to the HOS4.3 MMCX-to-MX ARC graph.

## 2. HOS4.3 relationship already reported

ROUND30's prior local HOS4.3 phandle report records these ARC-level links:
- mmcxlvl / pm8150a_s4_level parent-supply -> mxlvl / regulator-pm8150a-s3-mmcx-sup-level;
- mmcxlvl / pm8150a_s4_level_ao parent-supply -> mxlvl / regulator-pm8150a-s3-level-ao.

These are logical ARC performance-level parent edges. They are NOT PM8150 physical input supply links and must not be copied to vdd-s* regulator input properties.

The earlier local reports did not capture all details needed to reproduce those parent requests:
- mmcxlvl / mxlvl qcom,resource-name values;
- child qcom,set flags, including ACTIVE / SLEEP participation;
- qcom,init-voltage-level;
- qcom,min-dropout-voltage-level;
- exact AUX logical-corner to hardware-level translation for each relevant request.

## 3. Generic ACK GenPD parent propagation is not a dropout translation

ROUND30 reviewed the pinned generic GenPD path:
- If a child GenPD has a parent and its state changes, generic GenPD calls the performance-state translation helper before setting the parent state.
- The OPP translation helper returns the incoming state unchanged when the relevant OPP table does not have required-opps mapping to another table.
- The SM8250 RPMHPD provider uses the shared OPP table without per-entry parent required-opps mappings.

So simply adding a parent pointer from MMCX to MX would propagate the same pstate one-to-one. It would not recreate a HOS non-zero minimum-dropout delta unless a separate mapping is supplied.

This means a simplistic change from plain mmcx to mmcx_w_mx_parent would be insufficient to claim equivalence, and that alternative parents CX rather than MX anyway.

## 4. Effect on the current board rev2 candidate

The board rev2 Host order:
1. RPMHPD_MMCX;
2. GCC UFS_PHY_GDSC;

is still the right way to activate ROUND33's UFS required-opps mapping under the current ACK patch. The UFS PHY remains on GCC UFS_PHY_GDSC.

But the candidate now carries an explicit risk:
- required UFS performance state reaches MMCX;
- missing ACK MMCX-to-MX parent edge may leave out the HOS4.3 parent request;
- whether that omission blocks first UFS link startup or only affects power/performance stability is unknown.

Do not remove the MMCX routing merely because full ARC equivalence is not yet proven. It still supplies the ACK-side UFS required-opps endpoint. Equally, do not add a custom MMCX-to-MX descriptor without the local HOS ARC request/corner evidence.

## 5. Options, not selected

A. Keep plain ACK SM8250 MMCX for a minimal UFS bring-up candidate. This minimizes source delta but leaves the parent/corner risk explicitly open.

B. Design a DBY-W09-scoped MMCX-with-MX-parent variant only after the HOS4.3 resource/set/init/dropout values are captured and a translation strategy is proven. Do not modify the generic descriptor for all SM8250 boards.

C. Port the legacy HOS ARC provider. This is a much larger feature: AUX mapping, active/sleep aggregation, pseudo-enable semantics, parent/dropout handling, and the correct RPMh provider/device hierarchy. Do not include it in the first boot kernel unless evidence proves UFS depends on it.

## 6. Required local evidence

ROUND25 must use already-extracted HOS4.3 base DTB / prior decompiled reports to read only the relevant MMCX/MX ARC provider and consumer properties:
- provider resource-name;
- child qcom,set values;
- init voltage level;
- minimum dropout voltage level;
- whether the UFS-related MMCX consumer requests ACTIVE, SLEEP or both;
- any AUX-corner mapping already available in local sanitized logs.

Do not upload AUX binary or raw firmware, and do not repeat ROUND11's phandle graph scan. If the values are not present in existing safe files, mark NOT_CAPTURED and stop rather than re-extract.

## 7. Status

- ACK SM8250 MMCX descriptor has no MX parent: SOURCE REVIEWED.
- ACK CX descriptor has MX parent: SOURCE REVIEWED.
- HOS4.3 has MMCX ARC parent-supply edge to MX-level provider: SOURCE-REPORTED in ROUND30.
- HOS request set, resource-name, init and dropout semantics: UNKNOWN / NOT_CAPTURED.
- ROUND33+ROUND37 routes UFS required-opps to MMCX: DESIGN / SOURCE REVIEWED.
- Full HOS4.3 ARC equivalence: NOT ESTABLISHED.
- Whether missing MX parent blocks first UFS link startup: UNKNOWN.
- No source, DTS, config, build or device change.
