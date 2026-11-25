# Primary-AI review — ROUND25 / ROUND26 reports and ROUND27 release gate

Date: 2026-11-25  
Reviewer: primary AI (ChatGPT)  
Decision: **ACCEPTED FOR ROUND27 ONLY — ROUND27 AUTHORIZED FOR LOCAL AGENT EXECUTION**

## 1. Reviewed artifacts

Both required deliverables were fetched successfully from branch `firmware-audit-v1`:

| Round | Report | Blob SHA | Review |
|---|---|---|---|
| ROUND25 | `firmware-analysis/round25/round25-hos43-mmcx-mx-arc-request-semantics.txt` | `8bcfd37d290fdb2ed41879d4ebca69aa7c9a6df1` | Present; content reviewed |
| ROUND26 | `firmware-analysis/round26/round26-sm8250-vs-hos43-reserved-memory-interval-audit.txt` | `e55ecacaf0b345971062142765fd36e46551484e` | Present; content reviewed |

The review also compared each report with its corresponding `AGENT_TASK.md`, the ROUND27 task, the ROUND27 start prompt, and the existing main-branch ROUND30 source-side review.

## 2. ROUND25 review — HOS4.3 MMCX/MX ARC semantics

**Accepted as a properly bounded evidence report; unresolved semantics remain explicitly unresolved.**

Confirmed report findings:
- HOS4.3 MMCX and MX providers are identified as `mmcx.lvl` and `mx.lvl`.
- The MMCX ALL and AO child parent-supply references resolve by phandle to MX child nodes. The report correctly distinguishes these ARC topology links from PMIC physical input supplies.
- MMCX ALL/AO `qcom,min-dropout-voltage-level` is recorded as the stored value `0xffffffff`; the report does not invent signed-sentinel semantics.
- The report records the `qcom,set` values and prior ALL/AO/SO labels, while leaving literal ACTIVE/SLEEP bit-name mapping NOT_CAPTURED.
- The HOS4.3 base UFS node is not shown as an explicit MMCX/MX ARC consumer. Whether the real UFS path participates in ACTIVE, SLEEP, or both remains UNKNOWN.
- The comparison correctly concludes that adding only an ACK MMCX→MX GenPD parent would propagate the same pstate under the reviewed ACK path, and would not by itself reproduce an unknown HOS dropout/corner translation.

Completeness assessment:
- Work package A: PARTIAL, with provider/child/edge facts captured and the unavailable set-bit mapping explicitly bounded.
- Work package B: UNKNOWN, which is an allowed result under the task when no exact UFS ARC consumer can be identified.
- Work package C: PARTIAL/BLOCKED by the task's evidence boundary. The report says ROUND30 was not present on `firmware-audit-v1`; the primary review separately checked the existing main-branch ROUND30 design note. That note also retained the HOS resource/set/init/dropout/AUX translation values as unknown, so it supplies no missing evidence that would justify changing the report's conclusion.
- Work package D: PASS as a source-side classification.

**Decision impact:** Do not add an MMCX→MX descriptor, invent a required-OPP translation, or claim HOS ARC equivalence from this report. This is not a blocker for a build-only ROUND27 validation because ROUND27 does not alter the ARC driver/DTS power topology or test hardware votes.

## 3. ROUND26 review — reserved-memory interval comparison

**Accepted as a sanitized static interval-comparison report; final memory safety remains BLOCKED.**

Confirmed report findings:
- The pinned ACK `sm8250.dtsi` has 18 immediate fixed `no-map` reserved-memory children.
- The HOS4.3 base inventory has 37 children: 24 fixed-reg children and 13 dynamic/no-fixed-reg children.
- 17 ACK fixed intervals are exact matches to HOS4.3 fixed intervals.
- `cdsp_secure_heap` is the single ACK_ONLY case: ACK has a fixed interval while the same-name HOS child is dynamic/no-fixed-reg. It is not claimed to be equivalent.
- Seven HOS fixed nodes have no exact ACK counterpart. The report identifies an HOS-internal same-base/different-size nested pair.
- The current rev2 candidate includes `sm8250.dtsi`, so the inherited reservations and the inherited top-level memory placeholder are present in the compiled candidate even though the board source does not redeclare them.
- The ACK and HOS top-level memory placeholders are not identical: both have zero size, but their initial base-cell states differ. Actual post-ABL RAM ranges and final-FDT behavior remain UNKNOWN.

Completeness assessment:
- Work packages A/B: PASS for the reported fixed-reg enumeration and ACK↔HOS fixed-interval classification.
- Work package C: PARTIAL because inheritance is confirmed but runtime overlap cannot be established without the post-ABL FDT.
- Work package D: PARTIAL/BLOCKED for the same final-FDT dependency and the `cdsp_secure_heap` mismatch.
- The report says dynamic size/`alloc-ranges` pools were parsed separately, but does not publish a separate aggregate intersection result for those dynamic pools. Therefore this review does **not** infer that no ACK interval can intersect an HOS dynamic allocation pool. Preserve this as an explicit pre-boot memory-audit caveat.

**Decision impact:** Do not change, delete, resize, or override any reserved-memory node based on this report alone. Keep the final RAM/ABL/reserved-memory gate BLOCKED. This is not a blocker for ROUND27's isolated source-build/schema check, which does not boot the device or change the memory map.

## 4. Privacy and evidence boundary

Both uploaded reports were checked for the task's redaction requirements:
- No physical start/end/base/reg coordinates or coordinate hashes were found in the report text.
- No raw AUX binary, firmware, signing material, keys, or device-unique identifiers were uploaded.
- ROUND25's retained corner values are explicitly described as logical DT corner indices, not physical addresses.
- No claim in either report establishes runtime rail state, actual post-ABL memory, selected DTBO, or device boot behavior.

## 5. ROUND27 release decision

**The ROUND25/ROUND26 prerequisite review is complete. ROUND27 is now AUTHORIZED for the responsible local WorkBuddy Agent.**

The local Agent should execute the existing task exactly as written:
- `firmware-analysis/round27/AGENT_TASK.md`
- `firmware-analysis/round27/START_PROMPT.md`

Authorized scope only:
1. Inspect the exact already-present ROUND18 local Kleaf/Bzlmod/toolchain pins.
2. Use a disposable copy of the existing workspace and temporary staged copies of the current main-branch rev2 board DTS and rootparam overlay.
3. Build only the three DT targets: base board DTB, raw rootparam DTBO, and composite-check DTB.
4. Inspect composite properties and run the narrowest supported pinned schema validation, preserving every diagnostic and exit status.
5. Remove temporary staged sources/BUILD files and verify pre-existing tracked source/config/Image artifacts remain unchanged.
6. Upload one sanitized report to `firmware-audit-v1/firmware-analysis/round27/round27_kleaf_dtb_dtbo_composite_schema_validation.txt`, then stop.

Hard limits remain unchanged: no `kernel_build` or Image rebuild, no `dtbo_image`, no boot packaging/signing, no source/DTS/config/patch edits, no device access or writes, and no modification to protected branches or PR #1.

ROUND27 passing would mean only that the specified DT targets and composite/schema checks pass in the pinned local toolchain. It would **not** close the ARC corner-equivalence, final memory/ABL handoff, DTBO selection, AVB, or device-boot gates.
