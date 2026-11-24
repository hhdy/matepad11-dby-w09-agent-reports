# ROUND13 — HOS4.3 PM8150 UFS regulator mode / DRMS metadata audit (read-only)

Date: 2026-11-24

## Context and sequence

ROUND12 has been uploaded to `firmware-audit-v1` and stopped at its tool gate:
- no trusted, already-installed AVB inspection tool or reviewed AVB parser was available;
- outcome is BLOCKED; no AVB footer or vbmeta descriptor was inspected;
- do not repeat ROUND12, install/download avbtool, write an AVB parser, use WSL, or change local security policy.

ROUND13 is the next scoped local evidence task. It is independent of the unresolved AVB values and uses only the previously reviewed read-only device-tree parser/work copies. The GPT-side ACK interpretation is documented in:
`kernel-baseline/round47/ack-pm8150-regulator-mode-drms-capability-review.md`.

## Objective

Determine the HOS4.3 base boot FDT and applicable stock DTBO values for the regulator operating-mode / DRMS properties on DBY-W09 UFS-related PMIC rails. Earlier ROUND7 filtered inventories did not include these properties, so do not infer absence from ROUND7.

Target rails:
- PM8150 S4 — UFS VCCQ2.
- PM8150 L5 — UFS QMP VDDA-PHY.
- PM8150 L6 — UFS VCCQ and VDDP REF_CLK shared output.
- PM8150 L9 — UFS QMP VDDA-PLL.
- PM8150 L17 — UFS VCC.
- PM8150L S8 — UFS VCCQ parent rail.

Identify each target by its existing PMIC provider / group identity (compatible and pmic-id) and child regulator node. Do not assume that a regulator label or the PM8150A legacy resource name alone uniquely identifies the ACK provider group.

## Approved inputs and tools

1. Use only existing HOS4.3 work copies from prior rounds:
   - the ROUND3 base boot-FDT work copy (ROUND11 previously used `boot_fdt_candidate_0.dtb`);
   - the already extracted stock DTBO / fragment work copies and target inventory from ROUND7/ROUND8.
2. Reuse only the already-reviewed ROUND3 device-tree parser and ROUND9 audited indexing/resolution pattern. No new parser, binary utility or script.
3. Check that the expected work copies and parser are present before starting. If a required input/tool is absent or malformed, report BLOCKED / NOT_RUN and stop that subitem.
4. Do not re-extract firmware, re-run the broad ROUND7/ROUND8 inventory, or inspect unrelated regulator rails.
5. Do not use avbtool or any tool not already approved for the existing FDT/DTBO work.

## Required properties

For each target regulator node, inspect the base boot FDT and the relevant DTBO overlay fragment(s) for:

- `regulator-initial-mode` — report raw numeric value and mapped symbolic value only if the mapping is verified against the existing RPMh mode header / audited source.
- `regulator-allowed-modes` — report the complete ordered array, raw values and verified symbolic mapping where available.
- `regulator-allow-set-load` — presence / absence.
- `regulator-system-load` — raw value in microamps if present.
- Nested child nodes `regulator-state-standby`, `regulator-state-mem`, `regulator-state-disk`, where present:
  - `regulator-mode`;
  - `regulator-on-in-suspend` / `regulator-off-in-suspend`;
  - `regulator-suspend-min-microvolt`;
  - `regulator-suspend-max-microvolt`;
  - `regulator-suspend-microvolt`.

Also preserve the exact node path, PMIC provider compatible, pmic-id, child node name, and the overlay fragment-to-target path relationship.

## DTBO requirements

- Use ROUND7/ROUND8's existing board/entry selection facts and target map to identify which stock DTBO entry/fragment(s) are applicable to DBY-W09.
- Inspect only relevant fragments that target or modify one of the six target regulator nodes or the relevant PMIC regulator group.
- Record whether each property is added, replaced, deleted, or unchanged by a fragment; preserve fragment order where the existing inventory makes it knowable.
- If the applicable entry cannot be established, do not guess. You may report targeted matches across candidate entries, but label the final effective post-overlay value UNKNOWN.
- Do not claim a merged post-overlay FDT unless the approved existing tooling can actually establish the overlay target and property application semantics.
- If a property is absent in the base FDT and all applicable inspected fragments, report `NOT_FOUND_IN_INSPECTED_SCOPE`, not globally absent.

## Interpretation boundary

Do not infer runtime PMIC mode, actual voltage, regulator enable state, consumer load, or HOS ARC performance corner from static DT properties.

ROUND47's ACK interpretation is a separate source-level contract:
- PM8150 L5/L6/L9 use ACK PMIC5 NLDO DRMS ops with a 30 mA HPM threshold.
- PM8150 L17 uses ACK PMIC5 PLDO DRMS ops with a 10 mA HPM threshold.
- PM8150 S4 and PM8150L S8 use PMIC5 HFSMPS ops with manual set_mode but no automatic DRMS callback.
- `regulator-initial-mode` is a one-time initial request; `regulator-allowed-modes` is a mode constraint; `regulator-allow-set-load` grants DRMS permission but cannot create missing hardware callbacks.
Do not make a new hardware/DT change recommendation unless the observed HOS4.3 property values are first shown rail-by-rail.

## Safety / privacy boundary

- Strictly read-only local work copies.
- No ADB / fastboot / device connection, reboot, unlock, root, flash, partition write, writable mount or compile.
- Do not install or download tools, use WSL, alter PowerShell execution policy, or modify security settings.
- Do not modify input files or re-extract firmware.
- Do not publish local absolute paths, firmware binaries, complete local hashes, keys, signatures, digests, salts, rollback data, serials, MAC/IMEI or tokens.
- Do not modify main, `ack18-dby-w09-dts-draft`, PR #1 or any existing ROUND1–ROUND12 report.

## Required result

Create one sanitized UTF-8 text report:
`firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt`

Use a per-rail table with:
- rail / PMIC provider identity / node path;
- base-FDT values and status;
- relevant DTBO entry + fragment index + target path;
- overlay action and value;
- effective post-overlay value (only when actually established);
- status COMPLETE / NOT_FOUND_IN_INSPECTED_SCOPE / UNKNOWN / BLOCKED / NOT_RUN.

Include parser/input availability, exact limited scope, any incomplete overlay association, and explicit non-claims about runtime behavior.

Upload only that text report to branch `firmware-audit-v1`. Do not update main or any other branch from the local Agent task. After upload, stop and provide the report path plus concise status summary.
