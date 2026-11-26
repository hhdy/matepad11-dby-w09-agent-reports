# AI2 ROUND150 — Live ADB ARC regulator graph reconciliation and porting disposition

- **Assignee: 2号 AI (independent AI collaborator).**
- Not assigned to 1号 AI, WorkBuddy Agent, or 2号 Agent.
- Device: Huawei MatePad 11 (2021), DBY-W09 / HWDBY / KONA / SM8250.
- Stock runtime: HOS 4.3.0.196(C00E100), Android 12, kernel 4.19.157-perf+.
- Fixed ACK: android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a.
- Current candidate tree: afe9517f8062b96bfeb5b4dd5714942861e6a44b.
- Branch: ai2/round150-live-adb-arc-reconciliation-review.

## 1. Purpose

Independently reconcile the newly published ROUND149 live ADB structure against ROUND139 HOS static DT/DTBO evidence, ROUND146 pinned-ACK ARC/proxy driver gap analysis, ROUND143 ARM64 memory handoff analysis, and fixed ACK source. Deliver a technically grounded architecture decision and smallest next implementation plan.

This is a static/report/source review only. Do not access a tablet, local Agent workspace, raw private capture, or perform builds.

## 2. Mandatory inputs

1. ROUND149 live ADB report:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round149-adb-runtime-readonly-audit/firmware-analysis/round149/WORKBUDDY_ROUND149_ADB_RUNTIME_READONLY_AUDIT.md
2. AI1 independent review and corrections:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round149/AI1_ROUND149_INDEPENDENT_REVIEW_AND_ROUND150_DISPOSITION.md
3. ROUND139 HOS4.3 PMIC/UFS/ARC static inventory:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md
4. ROUND146 AI1 ACK ARC/proxy support gap:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round146/AI1_ROUND146_RPMH_ARC_REGULATOR_SUPPORT_GAP_AND_PORTING_OPTIONS.md
5. ROUND143 AI2 ARM64/FDT/RAM handoff review:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round143-arm64-fdt-memory-handoff-audit/firmware-analysis/round143/AI2_ROUND143_ARM64_BOOT_HANDOFF_FDT_MEMORY_AUDIT.md
6. Fixed ACK source at commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a, especially drivers/regulator/qcom-rpmh-regulator.c, regulator core/of_regulator.c, drivers/pmdomain/qcom/rpmhpd.c, GenPD, UFS host/PHY and interconnect paths.
7. Generic Linux v4.19 regulator core source:
   https://github.com/torvalds/linux/blob/v4.19/drivers/regulator/core.c

## 3. Required independent questions

### A. Correctly interpret the ROUND149 runtime regulator links

Reproduce the Linux v4.19 regulator-core sysfs link semantics from source:
- set_supply() creates the regulator consumer handle on the supplier rdev;
- the -SUPPLY sysfs link is located under the supplying regulator's device directory and points to the dependent consumer regulator device;
- do not infer dependency direction from link target alone without accounting for link location.

Then reconstruct the actual HOS graph from ROUND149's regulator IDs and link descriptions. Specifically validate:
- CX child regulator.6 supplies MX child regulator.3;
- MX child regulator.3 supplies MMCX child regulator.32;
- the five ROUND139 provider-child edges (ALL/AO pairs plus MMCX-sup/CX-sup edge);
- the 11 GDSC links to MMCX level and the other GDSC links described in the report.

State whether AI1's correction to ROUND149 D-9 is right. Identify any remaining mapping uncertainty caused by the local raw s9_01/s9_02 captures not being uploaded.

### B. What does runtime presence/binding actually prove?

Evaluate the evidence that 47 RPMh provider devices and seven level-style groups exist and are bound under qcom,rpmh-regulator, with MMCX/MX/CX child regulator entries registered.

Separate:
1. provider node exists;
2. driver binds/probes;
3. regulator children/supply graph are registered;
4. runtime enable/vote values are known;
5. physical voltage is measured.

Do not upgrade levels 4 or 5; these values were denied.

### C. ARC, Proxy and GenPD architectural decision

Using the actual HOS runtime graph and pinned ACK source:
- Decide whether the current candidate's GenPD-only model is demonstrated equivalent to the HOS ARC regulator provider-child graph. Explain why or why not.
- Determine whether the runtime evidence shows UFS directly depends on MMCX ARC. Keep HOS UFS's legacy devfreq/msm-bus path separate from the 11 MMCX GDSC consumers.
- Revisit the five provider-child dependencies and 13 GDSC-to-ARC supply links. Identify which are required to preserve the stock system graph, and which are essential specifically to UFS probe/first boot (if evidence permits).
- Assess proxy-consumer separately. ROUND139 identifies qcom,proxy-consumer-enable/current and proxy-supply declarations, and ROUND146 identifies missing pinned-ACK proxy-consumer support. ROUND149 did not expose enough to prove actual proxy consumer lifecycle. Decide what can be stated and what remains unknown.
- Compare possible designs: (i) ARC provider support; (ii) ARC plus proxy consumer support; (iii) hybrid ARC + GenPD; (iv) GenPD-only. Discuss duplicate votes and supply-parent ownership risks.
- Do not recommend a blind copy of the SM8475 reference driver. Specify required CMD-DB/AUX/API/active-sleep semantics and the smallest evidence needed before code.

### D. Memory, FDT and DTBO implications

Independently assess:
- The live /chosen lacks linux,uefi-mmap-* and linux,usable-memory-range entries. State only what this proves about the current live device-tree handoff, not the entire ABL implementation.
- The live /memory/reg property is 48 bytes, but its contents and root #address-cells/#size-cells numeric values are denied. A 4-byte property file means one 32-bit cell is stored; it does not reveal that cell's numeric value. Check this carefully.
- ROUND149's MemTotal is 11,984,584 kB and /reserved-memory has 37 child nodes; ranges and memory tuple data remain unavailable.
- Candidate zero-size /memory tuple still needs a justified correction.
- ro.boot.dtbo_idx=2 is live runtime evidence; ROUND138's entry-2 mapping may be corroborated, but physical DTBO partition hash/bytes remain unknown.

### E. Final disposition and implementation plan

Return:
1. a gate table with CONFIRMED / PARTIAL / UNKNOWN / BLOCKED;
2. a decision whether to keep the 23-patch candidate unchanged until all design questions are resolved;
3. a prioritized, minimal code/DTS work plan;
4. what should be done by AI1 next vs. what (if anything) needs a local Agent;
5. whether any new compile is justified now (expected answer must be based on concrete source changes, not pressure to compile).

## 4. Prohibitions

- No tablet, ADB, fastboot, root, recovery, UART, flashing or partition access.
- No reads of another Agent's private workspace or local raw captures.
- No source/DTS/DTBO/config edits, patch creation, builds or boot tests.
- No assumptions that missing values are zero.
- No claims that UFS directly consumes MMCX unless supported by a direct consumer path.
- Do not treat the lack of /chosen EFI metadata as proof that ABL never used any EFI-related path.
- Do not equate ARC parent-supply dependencies with physical PMIC VIN/input parents.
- Do not equate regulator software-reported voltage with measured physical voltage.

## 5. Output and stopping condition

Create:
- firmware-analysis/round150/AI2_ROUND150_LIVE_ADB_ARC_RECONCILIATION_REPORT.md

Do not overwrite this taskbook or the start prompt. Include source links with immutable refs, exact file/line references where practical, and distinguish raw source facts from report-derived observations. Mark any facts dependent on unpublished local files as report-level only.

After uploading, read back the report and stop. Do not start another round.
