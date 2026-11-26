# WORKBUDDY ROUND152 — Analyze existing ROUND151 regulator summary for ARC and proxy runtime evidence

- **Assigned executor: WorkBuddy Agent (local Agent 1).**
- Not assigned to 2号 AI or 2号 Agent.
- Scope: analyze only the already-captured local ROUND151 evidence. No device connection or new ADB command.
- Target: Huawei MatePad 11 DBY-W09 / SM8250.
- Input report: ROUND151 Root read-only runtime capture.
- Branch: workbuddy/round152-existing-round151-proxy-summary-audit.

## 1. Purpose

ROUND151 successfully captured a full regulator_summary from already-mounted debugfs under the existing root session, but the public report does not expose its full sanitized regulator consumer tree. Revisit only that already-captured local file to determine whether it contains explicit proxy consumer handles or useful additional runtime evidence for:
- the eight proxy-supply sites and associated qcom,proxy-consumer properties;
- ARC child regulators and their regulator-core nesting;
- UFS rails L5/L6/L9/L17/S4/S8, especially the S8 UFS handle;
- ufs_phy_gdsc and its UFS consumer handle.

This is a **local evidence interpretation task only**. The original root capture is complete. Do not reconnect to the tablet.

## 2. Mandatory input

Read the published reports:
- ROUND151:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round151-root-readonly-runtime-audit/firmware-analysis/round151/WORKBUDDY_ROUND151_ROOT_READONLY_RUNTIME_AUDIT_REPORT.md
- AI1 independent review:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round151/AI1_ROUND151_INDEPENDENT_REVIEW_AND_ROUND152_PLAN.md
- ROUND139 proxy property inventory:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md
- AI2 ROUND148 portability:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round148-arc-regulator-portability-review/firmware-analysis/round148/AI2_ROUND148_ARC_REGULATOR_AND_PROXY_CONSUMER_PORTABILITY_AUDIT.md

## 3. Permitted local workspace

Use only the existing ROUND151 folder:
- r151-root-readonly/evidence/raw
- r151-root-readonly/evidence/private
- r151-root-readonly/evidence/meta

Do not inspect any other path, another Agent's folder, kernel source checkout, project secrets, user files or application data.

Locate the exact captured regulator_summary output by reading the existing command index / manifest; do not rerun the command. The raw capture remains local and must not be uploaded.

If the local folder does not exist or the regulator_summary output is missing, stop and report that it cannot be analyzed. Do not substitute another file.

## 4. Required analysis

1. Extract the regulator_summary structure into a local working table:
   - provider regulator;
   - consumer device / consumer handle name;
   - use count / open count;
   - requested voltage range/current/load if shown;
   - parent supply nesting.
2. Search explicitly for proxy-like consumer names, including "proxy", provider self-requests or any device handles created for proxy-supply.
3. Map every observable proxy handle to ROUND139's eight proxy-supply sites and ROUND151's decoded FDT property sites:
   - L5 / L9 / L14 / L11;
   - CX MMCX-supply ARC child;
   - MMCX ALL ARC child;
   - GDSC af03000;
   - refgen.
4. Reconcile enable/current/voltage declarations with observed summary handles, where possible.
5. For each proxy property site classify:
   - declaration exists;
   - runtime provider bound;
   - proxy consumer handle explicitly visible in summary;
   - use count / request visible;
   - release timing observed or unknown.
6. Reconcile UFS rail use counts and handles:
   - verify why L6 has two UFS host handles;
   - verify that S8's UFS handle is 0 mV / 0 mV and does not contribute to enabled users;
   - verify whether L5/L9 user totals include other consumers beyond UFS PHY.
7. Reconcile the ARC MMCX/MX/CX nesting and thirteen GDSC consumers with regulator_summary.
8. Reconcile ufs_phy_gdsc: provider state, num_users, open count, UFS handle name and any active vote.
9. Report exact evidence and its limits. A name match or DT property is not proof of a proxy request. Absence from a filtered excerpt is not proof of absence from the full local summary; inspect the full relevant section locally.
10. Do not infer proxy sync_state / late_initcall unvote timing from a static snapshot. The summary shows current requests/consumer handles, not lifecycle code execution history.

## 5. Privacy and reporting

- Keep full raw summary, FDT and any sensitive device identifiers local.
- GitHub report must contain only sanitized names, consumer topology and numbers necessary for technical analysis.
- Do not upload the raw regulator_summary or full FDT.
- Do not upload serials, MACs, IMEI, panel identifiers, keys or user/application logs.
- Include the source raw capture key / local evidence filename and its manifest hash prefix, but not the raw file content.
- Clearly mark claims as direct captured output, parsed mapping, or inference.

## 6. Prohibitions

- No USB device connection, ADB, su, fastboot, reboot, recovery, UART or root command.
- No new reads from the tablet, even read-only.
- No mount/remount/debugfs changes.
- No reading /sys/kernel/debug/cmd_db or pmic-votable in this task; those were not captured in ROUND151 and require a separate authorization.
- No partition access, writes, source or DTS changes, patch, build or tests.
- Do not access any other Agent's private workspace.
- Do not attempt to prove physical voltage or physical PMIC input topology.

## 7. Deliverable and stop

Create:
firmware-analysis/round152/WORKBUDDY_ROUND152_EXISTING_REGULATOR_SUMMARY_PROXY_RUNTIME_REVIEW.md

Upload only the sanitized report. Read it back and verify its exact blob. Then STOP. Do not start a new round.
