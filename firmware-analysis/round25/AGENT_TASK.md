# ROUND25 — HOS4.3 MMCX/MX ARC request and dropout semantics audit

Owner: local WorkBuddy Agent; read-only offline property extraction
Baseline: HOS4.3 firmware already extracted in ROUND2/ROUND19 and existing sanitized ROUND11/ROUND16/ROUND30 reports.

## Purpose

The exact ACK 6.18.33 SM8250 RPMHPD descriptor selects a parentless MMCX GenPD. The HOS4.3 legacy ARC graph reports MMCX-to-MX parent-supply edges. Before accepting the ROUND33/ROUND37 UFS dual-domain candidate as a sufficient UFS performance-power route, capture the exact HOS4.3 parent request semantics for only the UFS-related MMCX/MX nodes.

## Hard boundaries

- Use only the existing ROUND19 decompiled HOS4.3 base DTS and already available local reports/work copies.
- Do not re-extract firmware, redeploy WSL, install/download tools, or repeat the whole ROUND11 parent/proxy graph parser.
- Do not edit source, DTS, config, build files, patches, firmware or previous reports.
- Do not run Kconfig, Kleaf, Bazel, kernel build, DT compilation, AVB, packaging or signing.
- Do not connect to tablet, run ADB/fastboot/recovery, reboot, unlock, root, flash or write partitions.
- Do not upload raw physical addresses, AUX binary, full firmware, keys or sensitive identifiers.
- If required property is not present in existing safe decompiled files, mark NOT_CAPTURED; do not reconstruct it from guesses.

## Work package A — exact HOS4.3 ARC providers and consumers

For only the relevant mmcxlvl and mxlvl provider nodes and their UFS-related consumer children, collect:
- provider compatible and qcom,resource-name;
- child node name (redact any unit-address values if present);
- qcom,set and whether it includes ACTIVE, SLEEP, ALL or other flags;
- qcom,init-voltage-level;
- qcom,min-dropout-voltage-level;
- relevant qcom,proxy-supply / qcom,*-parent-supply references only insofar as they establish ARC topology;
- the parent edge from mmcxlvl to mxlvl, with target node names and phandle confirmation.

Do not treat these as PMIC physical input supplies.

## Work package B — UFS request participation

Determine whether the exact UFS-related MMCX consumer participates in:
- active state;
- sleep state;
- both;
- or the existing reports do not prove it.

If the UFS consumer cannot be identified exactly from the local base DTB and prior logs, mark UNKNOWN.

## Work package C — corner translation

Inspect already available sanitized ROUND22–ROUND30 reports or existing local logs for:
- AUX logical corner names and associated hardware-level indexes;
- whether qcom,min-dropout-voltage-level equals zero, one, negative one sentinel or another value;
- any actual rule used by HOS ARC parent provider to derive parent state.

Do not inspect/upload binary AUX data in this round. Do not infer a signed value unless its encoding is documented in the existing report.

## Work package D — compare with ACK

Compare results only with these exact ACK facts:
- SM8250 RPMHPD selects plain MMCX without MX parent.
- CX uses CX-with-MX-parent.
- Other SoC tables select MMCX-with-CX-parent, not MX.
- generic GenPD parent propagation would pass the same pstate absent a required-opps translation table.

Classify whether a simple MMCX->MX parent descriptor would be:
- same-state propagation;
- require an explicit corner translation;
- or unresolved.

## Deliverable

Upload one sanitized UTF-8 report only:
firmware-analysis/round25/round25-hos43-mmcx-mx-arc-request-semantics.txt
to branch firmware-audit-v1.

Include exact source line references and property values, except all physical addresses must be redacted. Report PASS/PARTIAL/BLOCKED per work package and state what the findings mean for initial UFS bring-up. Upload no source, binary, AUX blob, DTS or firmware.

## Stop

After the report is uploaded, stop. Do not implement a parent descriptor, ARC provider, DTS change or new build.
