# AGENT2 ROUND152 — Existing candidate DTB vs live stock FDT memory/reserved/UFS delta audit

- **Assigned executor: 2号 Agent (independent local Agent 2).**
- This is not 2号 AI and not WorkBuddy Agent (local Agent 1).
- Device target: Huawei MatePad 11 (2021), DBY-W09 / HWDBY / KONA / SM8250.
- Stock runtime evidence: ROUND151, HOS 4.3.0.196(C00E100), Android 12, kernel 4.19.157-perf+.
- Candidate fixed ACK: android17-6.18.33_r00, pinned commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a.
- Candidate tree SHA: afe9517f8062b96bfeb5b4dd5714942861e6a44b.
- Existing candidate DTB identity expected from ROUND140/147: 108648 bytes, SHA-256 cab82fe3901dbb40533197eb48b2d99b08b46e5d5497ff1a6f688e9938db77e.
- Branch: agent2/round152-candidate-stock-fdt-memory-reserved-ufs-delta.

## 1. Purpose

Compare the exact already-built candidate DTB from 2号 Agent's own ROUND140 workspace against the now-decoded live stock HOS4.3 FDT facts published in ROUND151. The goal is to determine the smallest evidence-backed candidate DTS changes required for RAM and reserved-memory, and quantify UFS/GDSC/ARC topology differences.

This is an **existing-artifact, read-only inspection**. Do not rebuild, do not open the tablet, and do not inspect another Agent's private workspace.

## 2. Mandatory stock input

Read the current sanitized ROUND151 report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round151-root-readonly-runtime-audit/firmware-analysis/round151/WORKBUDDY_ROUND151_ROOT_READONLY_RUNTIME_AUDIT_REPORT.md

Also read AI1 review:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round151/AI1_ROUND151_INDEPENDENT_REVIEW_AND_ROUND152_PLAN.md

Use only the published decoded stock data; do not access WorkBuddy Agent's raw local FDT or evidence directory.

Known live stock RAM tuples from ROUND151:
1. base 0x80000000, size 0x39900000 (921 MiB)
2. base 0x200000000, size 0x200000000 (8192 MiB)
3. base 0xc0000000, size 0xc0000000 (3072 MiB)
Root cell values: #address-cells=2, #size-cells=2.
Stock /reserved-memory: 37 children; 23 non-zero reg entries, one zero-size kerneldump placeholder, 13 dynamic pools. 23 static entry sizes total about 232.689 MiB; one nested 8 MiB overlap exists between disp_rdump_region and cont_splash_region. Do not mistake sum-of-entry sizes for unique range coverage.
Stock UFS host has no power-domains and no operating-points-v2; host has legacy qcom,msm-bus and devfreq. Stock UFS PHY also has no power-domains. Stock live vdd-hba maps to ufs_phy_gdsc; that provider reports disabled / zero users while UFS is active. Six stock UFS rail assignments are described in ROUND151 §4.1–4.4.
Stock FDT has seven qcom,rpmh-arc-regulator groups; five provider-child parent-supply edges; thirteen GDSC-to-ARC edges.

## 3. Workspace restriction

Inspect **only 2号 Agent's own existing ROUND140 workspace**:
- /home/kerneldev/work/matepad11/round140-agent2/tree
- /home/kerneldev/work/matepad11/round140-agent2/logs
- /home/kerneldev/work/matepad11/round140-agent2/a30build
- /home/kerneldev/work/matepad11/round140-agent2/out-dtb

Do not inspect /home/kerneldev/work/matepad11 outside those exact directories. Do not inspect WorkBuddy Agent or 2号 AI workspaces. Do not search the user's machine, other mounted locations or credentials. The only target input is the already-existing candidate DTB artifact; no source worktree mutation.

First identify the exact candidate DTB inside out-dtb. Verify its byte size and SHA-256 against the expected identity above before parsing. If it does not match exactly, stop and report the mismatch; do not substitute a different build or copy.

## 4. Required checks

### A. Candidate root and RAM node

Record:
- root compatible/model/#address-cells/#size-cells;
- all nodes representing memory and exact device_type/status/reg properties;
- decode all base/size tuples using the actual root cell values;
- explicitly identify every zero-size tuple and its physical base;
- determine whether the candidate currently provides any non-zero System RAM range to the pinned ACK early FDT scanner;
- compare exact candidate RAM tuples against the three stock ranges above;
- do not simply paste stock RAM ranges into candidate without a stated rationale and risk discussion.

### B. Candidate reserved-memory full census

For every candidate /reserved-memory child, output:
- node name;
- phandle;
- compatible;
- reg (decoded base/size);
- size, alignment, alloc-ranges;
- no-map / reusable / linux,cma-default / removed-dma-pool flags;
- memory-region references from consumers where identifiable.

Compare candidate nodes with all stock names in ROUND151 and classify each:
1. same name + same semantic values;
2. same name + changed address/size/flags;
3. candidate-only;
4. stock-only;
5. dynamic pool with different semantics;
6. unresolved due property missing or parser limitations.

Compute candidate interval overlap and stock-candidate interval differences. Distinguish:
- sum of declared entry sizes;
- unique physical address union after overlaps;
- dynamic allocation requests;
- physical RAM containment.
Do not call any overlap a defect until semantics are checked. Do not claim that every stock vendor-only carveout must be copied.

### C. UFS Host / PHY and GDSC topology

For candidate live-independent DTB only, report:
- host and PHY node status, compatible and reg;
- all supply properties and resolved provider phandles;
- vdd-hba-supply presence/absence;
- power-domains on host and PHY, exact provider and domain indices;
- OPP table, required-opps, frequency table and interconnect paths;
- whether the same UFS_PHY_GDSC is referenced on both host and PHY;
- GDSC node flags/provider details;
- exact difference against stock ROUND151 topology.

The stock UFS GDSC observation is disabled/zero users while UFS is active. Treat this as a stock software-observed state, not as proof of physical gate status. Identify what candidate DTB alone cannot prove about runtime PM/genpd.

### D. ARC / RPMHPD resource ownership inventory

Independently confirm:
- candidate count of qcom,rpmh-arc-regulator groups (ROUND147 reported zero);
- any qcom,resource-name values;
- any ARC child regulator-name and parent-supply references;
- qcom,proxy-consumer properties and proxy-supply links;
- RPMHPD descriptor resource name mmcx.lvl for the UFS OPP required domain;
- whether candidate DTB currently contains both ARC mmcx.lvl provider and GenPD MMCX consumer. Do not infer a runtime collision if one side is absent.

### E. Final candidate disposition

Report:
- candidate RAM blocker status;
- stock/candidate reserved-memory parity and unresolved critical ranges;
- UFS GDSC/GenPD differences;
- ARC and proxy status;
- exact minimum DTS/source deltas that evidence supports, separated into confirmed / proposed / not justified;
- whether a new compile is justified now (no compile in this task).

## 5. Prohibitions

- No device connection, ADB, root, fastboot, recovery, UART, reboot, flashing, partition reads or writes.
- No build, test or generated artifacts.
- No source, DTS, DTBO, config, patch or candidate-file modifications.
- No downloads, package installation or network fetch other than the two published GitHub reports and this repository deliverable.
- Do not read WorkBuddy Agent's local folders or AI2's private workspace.
- Do not inspect another user's or Agent's private files.
- Do not change the candidate DTB or calculate a replacement.
- Do not treat provider presence as proof of voltage/vote/physical state.
- Do not authorize first boot.

## 6. Deliverable and stop condition

Create report at:
firmware-analysis/round152/AGENT2_ROUND152_CANDIDATE_DTB_STOCK_FDT_MEMORY_RESERVED_UFS_DELTA_REPORT.md

Include exact candidate DTB path relative to the permitted out-dtb folder, size, SHA-256, parser/tool versions already installed, all decoded tables, errors and limitations. Upload only the text report; no local candidate binary needed.

After upload, read the report back and verify the blob. Then STOP. Do not start another round.
