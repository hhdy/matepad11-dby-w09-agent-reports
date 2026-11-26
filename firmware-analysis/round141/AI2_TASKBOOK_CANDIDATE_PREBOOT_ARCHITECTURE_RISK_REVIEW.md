# ROUND141 — 2号 AI 首启前架构风险独立审查

执行方：2号 AI（独立 AI 协作者）。
重要：本任务属于 2号 AI，不属于 2号 Agent，也不属于 ROUND139 的 WorkBuddy Agent。
派发方：AI1（ChatGPT）。
设备：Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1。
内核：ACK android17-6.18.33_r00，固定 commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a。
候选树：afe9517f8062b96bfeb5b4dd5714942861e6a44b。
模式：只读源码和报告审查；禁止设备访问、构建、下载和任何修改。
报告分支：ai2/round141-candidate-preboot-risk-review。
报告路径：firmware-analysis/round141/AI2_ROUND141_CANDIDATE_PREBOOT_ARCHITECTURE_RISK_REVIEW.md。

## 1. 必须阅读

1. ROUND135 R3：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round135/r3-validation/ROUND135_R3_FINAL_REPORT.txt
2. ROUND138：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round138/round138-dtbo-variant-and-live-fdt-delta-audit.md
3. ROUND139：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md
4. AI1 ROUND139 review：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round139/AI1_ROUND139_INDEPENDENT_REVIEW_AND_ROUND140_SUPPLEMENT.md
5. ROUND140 2号 Agent report：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round140-independent-preboot-tests/firmware-analysis/round140/round140-agent2-independent-build-and-preboot-test-report.md
6. AI1 ROUND140 review：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round140/AI1_ROUND140_INDEPENDENT_REVIEW_AND_ROUND141_DISPOSITION.md

## 2. Review A — UFS supplies and driver consumers

Against the exact pinned ACK source and 23-patch candidate, independently verify:
- PHY vdda-phy → L5; vdda-pll → L9; actual QMP UFS PHY consumer and enable/load sequence.
- Host vcc → L17; vccq → L6; vccq2 → S4; exact UFS host parser and regulator use.
- Candidate patch 06 consumer for qcom,vddp-ref-clk-supply.
- Whether any source consumes qcom,vccq-parent-supply → S8. Do not infer consumption from a DT property alone.
- HOS vdd-hba-supply → ufs_phy_gdsc versus candidate omission plus UFS_PHY_GDSC power-domain. Determine exactly what source proves and what runtime sequence remains unknown.

Output a property → provider → code consumer → verdict table. Explicitly identify properties that are present but inert.

## 3. Review B — MMCX / MX / GDSC

Inspect pinned ACK generic multi-power-domain attachment and RPMh power-domain code:
- Does the UFS host attach to both listed power domains?
- What provider descriptor is selected for RPMHPD_MMCX on SM8250?
- Does that descriptor have an MX parent pointer?
- Can an MMCX vote cause an MX vote in this exact source version?
- What does the candidate addition of MMCX alongside UFS_PHY_GDSC establish, and what remains runtime-only?

Do not equate matching numeric corner labels or HOS ARC edges with ACK runtime behavior.

## 4. Review C — memory and reserved-memory

ROUND140 reports candidate /memory@80000000 reg size zero, 18 candidate reserved-memory children, and 37 children in vendor FDT #0. Confirm pinned ACK early_init_dt_scan_memory zero-size behavior and scan order. Compare node ownership and address ranges only where the source reports actual values. Do not infer that 18 is wrong solely because vendor FDT has 37; do not copy all 37 blindly.

State the smallest evidence needed to close final post-ABL FDT, RAM tuples, reservation ownership and handoff.

## 5. Review D — reproducibility / process compliance

Evaluate:
- ROUND140 build success, exact source tree, .config and DTB identity.
- Image hash difference: auto-generated signing certificate and BTF type-set delta. Assess whether the report supports each explanation; do not call the BTF output inherently nondeterministic without exact pahole/BTFGen version and command.
- ROUND140 records external Kleaf repositories fetched with HTTP 200. Original taskbook required stopping if the local dependency cache was insufficient. With only the report available, classify this as COMPLIANT / DEVIATION / UNRESOLVED and explain what existing log could resolve it. Do not access another Agent's private workspace or download anything.

## 6. First-boot gate matrix

Report PASS / CONDITIONAL / BLOCKED / NOT AUTHORIZED for:
1. 23-patch candidate identity.
2. independent build and artifact identity.
3. UFS consumer/provider/driver links.
4. physical inputs for L5/L6/L9/L17/S4/S8.
5. S8 effective consumer and power sequencing.
6. MMCX/MX runtime votes.
7. final post-ABL FDT and usable RAM tuples.
8. reserved-memory ranges/ownership.
9. device DTBO identity and selected entry.
10. ABL boot-v2 DTB / independent ramdisk handling.
11. AVB trusted verification and remaining footer provenance.
12. complete device-matched backups and tested HOS4.3 recovery route.
13. first device boot authorization.

Unknown stays UNKNOWN/BLOCKED. A static build cannot close runtime or device gates.

## 7. Prohibitions

No tablet connection, USB, ADB, fastboot, recovery, serial, reboot, bootloader, partition access, FDT read, privilege escalation, root, source/patch/DTS/DTBO/config modification, build, packaging, signing, AVB changes, flashing, firmware download or dependency fetch. Do not ask 2号 Agent or WorkBuddy Agent to redo ROUND140. Do not claim first boot is authorized.

## 8. Report and stop

Create the report at the path above. Include exact source file paths and line numbers, assumptions, unknowns, the full gate matrix, and the smallest missing artifact for each blocker. Recommend one of:
- source-level defect needs AI1 follow-up;
- ready only for separately authorized device-read-only evidence collection;
- not ready, more offline evidence needed.

Upload only sanitized Markdown to ai2/round141-candidate-preboot-risk-review. Read back and verify byte identity, then stop.
