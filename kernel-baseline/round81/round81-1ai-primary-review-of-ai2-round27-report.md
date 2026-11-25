# ROUND81 — 1号 AI primary review of AI2-ROUND27 DT build and schema report

**Date:** 2026-11-25  
**Reviewer:** 1号 AI（ChatGPT）  
**Task issuer / design owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent (local WorkBuddy)  
**Report reviewed:** firmware-audit-v1:firmware-analysis/round27/AI2_ROUND27_KLEAF_DTB_DTBO_SCHEMA_REPORT.txt  
**Report blob:** ee573f75048a20b4393c0a4478f9d7e76b6bdfdb  
**Pinned ACK:** android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

## 1. Overall verdict

**ROUND27 BUILD / COMPOSITE PROPERTY CHECKS: PASS. SCHEMA: FAIL (DIAGNOSTICS PRESENT). REPORT: ACCEPTED WITH REPRODUCIBILITY NOTES.**

The testing Agent completed the exact three-target Kleaf/Bazel DT build and generated a base DTB, rootparam DTBO and composite DTB. The report states all three query/cquery targets resolved and the combined build returned 0. Composite property assertions passed.

The real schema validator returned exit code 0 but produced error-level diagnostics. The report correctly refuses to call this a clean schema PASS. One narrow UFS diagnostic and seven additional full-corpus diagnostics remain. The schema gate is therefore **NOT PASS / REMEDIATION REQUIRED**.

The overall board/boot gate remains closed: this test does not prove ABL overlay selection, final memory handoff, PM8150 input topology, AVB acceptance or device boot.

## 2. Input identity — independently resolved

The original ROUND78 preflight observed:
- 2号 AI taskbook expected board DTS blob: 9918efe3f253a3e4821689ffeb899d5a0f237e8f.
- Current main board candidate blob: f5449bac669ea71d7149ffb1fc858e39eb128572.

The ROUND27 report says it recovered the exact locked blob from immutable main history commit e06062cac9e319bbb4156226469a1e295338fe95 and verified the Git blob hash. 1号 AI independently fetched the same file at that exact commit and confirmed the returned blob SHA is 9918efe3f253a3e4821689ffeb899d5a0f237e8f. The current main file still returns f5449bac669ea71d7149ffb1fc858e39eb128572.

1号 AI also independently compared the two source versions after stripping C-style block comments, line comments and whitespace. The remaining DTS content is identical (2,749 normalized characters each). The commit diff itself changes only a comment block. The rootparam overlay blob also matches the taskbook pin c7e5b145d4308e0675ff648b4e046033c5560083.

**Input identity verdict: PASS.** The testing Agent used the exact immutable input required by the taskbook; it did not silently replace it with current HEAD. Because the HEAD-only difference is comment text and all non-comment DTS content is identical, the board output is semantically applicable to the current main candidate. The earlier ROUND78 INPUT IDENTITY BLOCKED status is superseded and closed for this validation.

Sources:
- [Exact locked board DTS commit](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/e06062cac9e319bbb4156226469a1e295338fe95/dts/dby-w09-ack18-board.dts.rev2.candidate)
- [Current main board DTS](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/dts/dby-w09-ack18-board.dts.rev2.candidate)
- [Pinned rootparam overlay](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/dts/dby-w09-ack18-rootparam.dtso.draft)

## 3. Build and composite property verification

The report records:
- Bazel 8.7.0; rules_devicetree 0.1.4 at a locally resolved git revision.
- Three target labels resolved by query and cquery with RC=0.
- One Bazel build command for exactly the three requested targets returned BUILD_RC=0.
- Three actions ran with 258 cache hits; no kernel Image, kernel_build or dtbo_image was built.
- Outputs:
  - base DTB: 145,849 bytes; SHA-256 0a4a471c8cea3093c25a4da6b26d81cddbc6bfeeb166ac9071476bb3a5e1f4e7
  - rootparam DTBO: 536 bytes; SHA-256 8005d2bb6402a77751b68842604f58a985f3ac8de09925f46f733121f97c66a2
  - composite DTB: 146,045 bytes; SHA-256 a82ca733e5c3005ed4f2beebbc19185391862f6b1d03b77a4b1753984828b0a2

Composite checks recorded:
- root model/compatible and base/composite root board-id remain as expected;
- overlay root board-id is separately recorded and not confused with Android DT table id/rev;
- all five /rootparam vendor identity values match the VG candidate;
- UFS host power-domain specifiers are in the correct order: RPMhPD MMCX (provider index 6), then GCC UFS_PHY_GDSC (provider index 4). “index 0 / index 1” in the taskbook means the first and second list positions, not provider cell values;
- QMP PHY retains GCC UFS_PHY_GDSC only;
- UFS supplies and the VDDP/VCCQ-parent metadata are present; vdd-hba-supply is absent by design;
- cleanup restored the disposable qcom directory and preserved the pre-existing ROUND18 tracked/untracked workspace baseline, according to the Agent report.

**Build/composite property verdict: PASS as reported.** 1号 AI did not rerun the local build or download the binary artifacts; this is a source/report review, not an independent rebuild.

## 4. Schema diagnostics — real failures, not a pass

The report says the existing processed schema corpus was used with dtschema dt-validate 2026.9.

### 4.1 Narrow schema run

- RC=0.
- One error-level diagnostic on the UFS host:
  vcc-voltage-level is an unevaluated / unexpected property under qcom,sc7180-ufshc.yaml.

This is a real diagnostic. The DTB is not schema-clean.

### 4.2 Full schema run

- RC=0.
- Eight error-level diagnostics were reported:
  1. root compatible pair huawei,dby-w09 + qcom,sm8250 is not in the qcom.yaml allow-list for SM8250 boards.
  2-3. vcc-voltage-level has a generic type diagnostic and is rejected as an unexpected UFS property.
  4-8. The five Huawei rootparam vendor properties are treated by generic dt-core validation as raw byte blobs with no selected Huawei rootparam binding declaring their types.

The validator's return code 0 must not be treated as schema success. The Agent correctly reported the diagnostics instead of suppressing them.

### 4.3 Source-level classification of vcc-voltage-level

The fixed ACK 6.18.33 UFS schemas:
- qcom,sc7180-ufshc.yaml selects qcom,sm8250-ufshc and sets unevaluatedProperties: false;
- qcom,ufs-common.yaml defines vcc-supply, vccq-supply, vccq2-supply and their max-microamp properties, but does not define vcc-voltage-level.

1号 AI searched the pinned ACK UFS driver files ufs-qcom.c, ufshcd-pltfrm.c and core ufshcd.c: no vcc-voltage-level consumer was found. The generic UFS core configures regulator load and enable references; the board candidate already describes the PM8150 L17 regulator's permitted min/max range at the regulator node. Thus adding vcc-voltage-level to the ACK schema merely to silence validation would document a property that the pinned ACK driver does not consume.

**Corrected disposition (see ROUND82):** the legacy Qualcomm UFS binding and driver show that vcc-voltage-level expresses an actual VCC min/max consumer request in microvolts, parsed into the VCC regulator descriptor and applied through regulator_set_voltage(). The pinned ACK no longer implements that behavior, but deleting the property would lose the narrower consumer range (2.504–2.950 V) currently represented separately from the broader PM8150 L17 provider limits (2.496–3.008 V). Do not delete the property until 2号 AI either implements and schema-declares the real UFS VCC voltage request in ACK, or proves an electrically equivalent alternative. Do not add a schema-only property without driver behavior.

See [ROUND82 — Corrected UFS VCC voltage-range schema remediation analysis](../round82/round82-corrected-vcc-voltage-level-schema-remediation.md).

Sources:
- [UFS SM8250/SC7180 binding](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.yaml)
- [UFS common binding](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml)
- [Pinned UFS generic regulator setup](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c)

### 4.4 Board compatible / rootparam binding remediation

The pinned qcom.yaml SM8250 root compatible enum currently lists upstream-known SM8250 boards but not huawei,dby-w09. The vendor-prefix schema already recognizes the huawei, prefix.

Recommended follow-up:
1. Add huawei,dby-w09 to the SM8250 compatible allow-list in the Qualcomm ARM binding (or add a properly scoped board binding if required by the pinned schema structure).
2. Add a narrowly selected Huawei rootparam schema declaring:
   - qcom,boardid as a four-cell unsigned array;
   - qcom,board_name, qcom,product_name and hardware_version as strings;
   - huawei,modem_id as the exact two-cell unsigned array present in the candidate.
3. Prefer selecting the rootparam node by a precise node-name/property selector if supported by the pinned dtschema version. Do not add a guessed compatible property to the bootloader-owned rootparam node merely to silence schema diagnostics; first verify that any new property is safe for HOS4.3 ABL parsing.
4. Re-run the full and narrow schema validation and retain all diagnostics.

These are proposed schema changes; no binding source was modified in ROUND81.

## 5. Report completeness / reproducibility gaps

The report is accepted as proof that a real composite was built and real schema diagnostics were obtained, but two details prevent calling the schema subtask fully reproducible:

1. The narrow dt-validate command prints a literal placeholder for the -l list instead of the exact selected schema IDs/filenames. The report describes the coverage categories but does not disclose the actual list.
2. The taskbook says to prefer a targeted dtbs_check if supported, otherwise use the existing dt-validate. The report uses dt-validate but does not state whether a targeted Makefile/Kbuild dtbs_check was found unsupported or why the fallback was selected.

These omissions do not erase the recorded errors or invalidate the three-target build. A follow-up schema run, if issued, should include the exact schema ID list, the Makefile/tooling availability check, and all relevant warnings/diagnostics. Do not ask the testing Agent to rewrite or rerun the completed task unless 2号 AI issues a separate scoped test task.

## 6. Current project gate update

- ROUND27 input identity: **PASS** — exact locked historic blob restored and verified; non-comment content equals current main.
- ROUND27 base DTB / rootparam DTBO / composite build: **PASS** as reported.
- ROUND27 composite properties: **PASS** as reported.
- ROUND27 schema: **FAIL / NOT CLEAN** — 1 narrow and 8 full error-level diagnostics; remediation required.
- ROUND27 report delivery: **COMPLETE** — uploaded at the only taskbook path.
- Phase D kernel Image build: **PASS**, independently checked in ROUND79.
- Phase E final HOS4.3 ABL memory handoff / PM8150 physical supply-parent: **BLOCKED**.
- Phase F boot-v2/ramdisk/DTBO selection/AVB packaging: **BLOCKED**.
- Phase G device validation: **NOT RUN**.

No board DTB/DTBO from this task is boot-ready or authorized for flashing. No HOS4.3 ABL overlay selection is proven. Do not start Android 17 DerpFest Stage B.

## 7. Work performed by 1号 AI

Read-only GitHub review of the report, taskbook, old and current DTS blobs, exact history commit, pinned ACK UFS binding/source and Qualcomm ARM compatible schema. The older and current board DTS non-comment content was independently compared.

No local rebuild, no raw Agent log access, no dt-schema execution, no patch edit, no 2号 AI branch change, no protected DTS branch change, no device operation and no AVB operation.

**Final verdict: ROUND27 report accepted; the three-target composite build passed, but schema validation did not pass. Stage A remains incomplete.**
