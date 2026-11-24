# firmware-analysis ROUND14 — HOS4.3 MMCX/MX ARC corner/dropout and S8 enable-property audit

Date: 2026-11-24
Target: Huawei MatePad 11 2021 DBY-W09 / HOS4.3
Mode: READ-ONLY, EXISTING WORK COPIES ONLY
Priority: Stage A ACK 6.18.33 UFS/storage bring-up research

## 0. Purpose

ROUND49 and ROUND50 completed the public ACK .33 and Qualcomm SM8250 KONA source review. That work exposed two remaining questions which cannot be answered from public sources:

1. The exact HOS4.3 logical ARC corner properties for the existing MMCX→MX parent links. ROUND11 resolved the phandles, but ROUND24 explicitly says the previous inventory did not capture provider resource names, child qcom,set, init-voltage-level, or min-dropout-voltage-level.
2. The actual HOS4.3 S8 provider/child enable metadata. ROUND13 captured its vendor modes and threshold, but did not report qcom,init-enable / regulator-boot-on / regulator-always-on. This matters because the public KONA UFS code treats qcom,vccq-parent as a load-only consumer and does not explicitly enable S8.

This task is a narrow property extraction only. It must not repeat ROUND11's parent/proxy graph scan, ROUND13's full mode scan, or ROUND8/ROUND13's DTBO resolution work.

## 1. Required existing inputs and approved tools

Use only:
- the already existing ROUND3 base boot-FDT work copy;
- the already reviewed ROUND3 FDT parser;
- the existing ROUND9 base phandle/path index;
- the already reviewed ROUND8/ROUND13 fragment/symbol/target resolution results, only as references for the overlay boundary.

Do NOT:
- re-extract firmware, unpack a new boot image, or create another work copy;
- write or modify a parser, shell script, binary, or analysis tool;
- install/download any tool or Python package;
- invoke WSL, change command safety policy, or search the entire disk for tools;
- connect to ADB/fastboot/device, read live runtime status, unlock, root, flash, or write any partition.

If the exact existing ROUND3 input or reviewed parser is unavailable, or a required path cannot be resolved with the approved existing indices, mark the relevant item BLOCKED / NOT_RUN and stop. Do not invent paths or values.

## 2. Target ARC provider scope

Read only these existing provider groups and their specifically linked child nodes:

- MMCX provider: `/soc/rsc@18200000/rpmh-regulator-mmcxlvl`
  - ALL child corresponding to the ROUND11 phandle source `pm8150a_s4_level-parent-supply`
  - AO child corresponding to `pm8150a_s4_level_ao-parent-supply`
  - sleep/SO sibling only if it is already a direct sibling under this same provider and is available in the existing parser result.
- MX provider: `/soc/rsc@18200000/rpmh-regulator-mxlvl`
  - the exact target child previously resolved for MMCX ALL: `regulator-pm8150a-s3-mmcx-sup-level`
  - the exact target child previously resolved for MMCX AO: `regulator-pm8150a-s3-level-ao`

Use the existing ROUND11 phandle result as the authoritative edge list; do not rescan all parent-supply properties. Confirm target node identity/path from the existing phandle index so similarly named children under other provider groups are not conflated.

### 2.1 Provider-level properties

For MMCX and MX provider groups only, extract these properties when present:
- `compatible`
- `qcom,resource-name`
- `qcom,send-defaults`
- `qcom,always-wait-for-ack`
- `qcom,use-awake-state`
- `proxy-supply` target identity/path, if present on either provider

For each `proxy-supply` reference in this exact scope, identify the resolved provider/child path only. Do not infer its runtime effect.

### 2.2 Child-level properties

For each of the four exact MMCX/MX child nodes above, extract only:
- exact node path and parent provider path;
- `regulator-name`;
- `regulator-min-microvolt` and `regulator-max-microvolt` (report as raw logical corner values; do not convert them to physical microvolts);
- `qcom,set`;
- `qcom,init-voltage-level`;
- `qcom,min-dropout-voltage-level`;
- `qcom,proxy-consumer-enable`;
- `qcom,proxy-consumer-voltage`;
- `qcom,proxy-consumer-current`.

Also report any matching ALL/AO/SO child distinction and its exact path. Do not merge values across same-named nodes in different provider groups.

For any property not present on an examined node, report `NOT_FOUND_IN_INSPECTED_SCOPE`. Do not label it globally absent.

### 2.3 Cross-check already known edges without repeating the scan

ROUND11 already resolved:
- MMCX ALL `pm8150a_s4_level-parent-supply` → MX `regulator-pm8150a-s3-mmcx-sup-level`;
- MMCX AO `pm8150a_s4_level_ao-parent-supply` → MX `regulator-pm8150a-s3-level-ao`.

Preserve these edge labels in the output and confirm the exact source/target path references. Do not discover or enumerate other parent-supply or proxy-supply edges.

## 3. S8 enable/boot-policy scope

Use the already known HOS4.3 S8 provider:
- provider: `/soc/rsc@18200000/rpmh-regulator-smpc8`
- child: the exact child path previously identified by ROUND13 for resource `smpc8` (legacy child label may be `pm8150a_s8`; do not identify the PMIC from the legacy label alone).

Extract only enable/boot/power initialization fields not reported by ROUND13:
- child `qcom,init-enable`;
- child `regulator-boot-on`;
- child `regulator-always-on`;
- child `regulator-state-standby`, `regulator-state-mem`, or `regulator-state-disk` subnodes only for on/off fields, if any are present;
- child `qcom,set`, `qcom,init-voltage`, `regulator-min-microvolt`, `regulator-max-microvolt`;
- provider `qcom,resource-name` and `qcom,regulator-type`.

Do not re-scan/re-report S8 mode enums, supported-modes, thresholds, or init-mode; ROUND13 is authoritative for those values. Do not claim a live regulator enabled/disabled state: this is static DT metadata only.

## 4. DTBO boundary

Reuse ROUND13's completed finding: all nine inspected stock DTBO entries had zero fragment targets under `/soc/rsc@18200000`, but the selected entry was not identified and effective post-overlay remains UNKNOWN.

Do not repeat DTBO parsing or select an entry by guess. Include this exact boundary in the report and distinguish base-FDT static values from verified effective post-overlay values.

## 5. Output format and redaction

Create exactly one UTF-8 text report:

`firmware-analysis/round14/round14_arc_mmcx_mx_power_properties.txt`

Upload it to repository `hhdy/matepad11-dby-w09-agent-reports`, branch `firmware-audit-v1`.

The report must include:
1. tool/input gate status;
2. each provider and child path separately;
3. exact raw property names and values (numeric values may be decimal/hex if both are already reported by the reviewed parser);
4. parent edge source and resolved target paths;
5. explicit `NOT_FOUND_IN_INSPECTED_SCOPE`, `UNKNOWN`, `BLOCKED`, and `NOT_RUN` states where appropriate;
6. DTBO boundary exactly as in section 4;
7. a statement that no runtime mode or regulator enable state was read.

Redact/omit:
- local absolute filesystem paths;
- physical addresses, offsets, binary payloads, full firmware hashes and binary dumps;
- serial numbers, IMEI, MAC, device IDs beyond public model/SoC identifiers;
- keys, salts, digests, signatures, rollback values, tokens, credentials, or other secrets.

## 6. Stop conditions and branch safety

- Upload only the one text report to `firmware-audit-v1`.
- After successful upload, STOP. Do not edit `main`, `ack18-dby-w09-dts-draft`, PR #1, or any other branch/file.
- PR #1 must remain Draft.
- Do not create follow-up work or perform another audit in the same run.
- No device interaction, flashing, unlocking, rooting, partition writes, tool installation/download, parser development, firmware re-extraction, or compilation.

The result is evidence for GPT's public-source comparison and DTS design only; it is not authorization to implement an ARC driver, add an MMCX→MX ACK parent edge, or change S8 enable policy before review.
