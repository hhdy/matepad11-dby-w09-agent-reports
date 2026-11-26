# AI2 ROUND148 TASKBOOK — Qualcomm ARC regulator and proxy-consumer portability audit for ACK 6.18.33

## Assignment identity

- **Assigned executor: 2号 AI (independent AI collaborator).**
- This is not 2号 Agent and not WorkBuddy Agent.
- 1号 AI is the integration owner and will independently review the report.
- Target: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1.
- Kernel: Android 17 ACK android17-6.18.33_r00.
- Pinned commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9.
- Candidate tree SHA: afe9517f8062b96bfeb5b4dd5714942861e6a44b.

## Purpose

Independently audit whether the generic Qualcomm RPMh ARC regulator implementation model can be adapted to the pinned ACK 6.18.33 tree, and identify every material dependency beyond adding an RPMHPD parent pointer.

This is a source portability assessment, not a coding assignment. Do not create or modify a patch.

## Required reading

1. 1号 AI ROUND146 report:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round146/AI1_ROUND146_RPMH_ARC_REGULATOR_SUPPORT_GAP_AND_PORTING_OPTIONS.md
2. ROUND139 accepted HOS4.3 provider/ARC inventory:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md
3. Exact pinned ACK:
   - drivers/regulator/qcom-rpmh-regulator.c
   - drivers/regulator/core.c
   - drivers/regulator/of_regulator.c
   - drivers/regulator/Kconfig and Makefile
   - include/soc/qcom/rpmh.h
   - include/soc/qcom/cmd-db.h
   - drivers/soc/qcom/rpmh.c
   - drivers/soc/qcom/cmd-db.c
   - regulator public headers and registration APIs
4. Generic Qualcomm reference:
   - OnePlusOSS/android_kernel_oneplus_sm8475
   - commit 7278ce9a3c8539b4630d6988cc80f90c31c07336
   - drivers/regulator/rpmh-regulator.c
   - drivers/regulator/proxy-consumer.c
   - include/linux/regulator/proxy-consumer.h
   - related Kconfig / Makefile entries.
   This is a generic Qualcomm reference, not proven to be the exact Huawei HOS4.3 driver.

## Required independent questions

### A. Confirm ARC driver coverage
- Does pinned ACK support qcom,rpmh-arc-regulator? Inspect the actual type enum and match table.
- Which ARC-specific functions in the reference are missing?
- Distinguish ordinary qcom,pm8150-rpmh-regulators VRM providers from ARC level provider groups.

### B. API compatibility matrix
For every relevant ARC reference dependency, compare the pinned ACK equivalent:
- cmd_db_read_addr
- cmd_db_read_slave_id
- cmd_db_read_aux_data
- rpmh_write_async / rpmh_write
- RPMh state enums and TCS command structures
- regulator_desc and regulator_ops for ARC selector operations
- devm_regulator_register
- regulator_set_voltage / regulator_set_load / regulator_enable
- of_platform_populate / child regulator lookup
- proxy consumer registration / unregister / sync_state APIs

Classify each as:
- PRESENT with compatible signature/semantics;
- PRESENT but signature/semantics differ;
- ABSENT;
- UNKNOWN (if code evidence incomplete).

Do not assume an API is absent based solely on a failed search result; verify the exact header/source or clearly state the evidence limitation.

### C. Proxy-consumer feature gap
- Determine exact behavior of qcom,proxy-consumer-enable, qcom,proxy-consumer-current, qcom,proxy-consumer-voltage, qcom,proxy-consumer-name and proxy-supply in the Qualcomm reference.
- Check which of these properties occur in ROUND139 HOS4.3 and which are consumed by pinned ACK.
- Explain lifecycle semantics: registration, sync_state unvote, legacy late_initcall cleanup, unregister and error handling.
- Do not conflate proxy supply with ARC child parent-supply or physical VIN parent.

### D. ARC request semantics
- Per-resource CMD-DB AUX level map (hardware level ↔ consumer voltage selector).
- ACTIVE/SLEEP and WAKE_ONLY request handling.
- Per-child request aggregation / max vote.
- ARC enable/disable behavior (level 0 / OFF mapping).
- Per-child parent-supply behavior.
- Default request and proxy lifecycle.
- Determine which exact parts could be reused from fixed ACK and which require port/adaptation.

### E. Porting recommendation
Compare:
1. Port ARC producer only.
2. Port ARC producer plus proxy-consumer facility.
3. Keep GenPD UFS OPP only as a narrow replacement and separately implement missing ARC pieces.
4. Custom GenPD-only reimplementation.
For each list benefits, missing proof and risk. Explicitly consider duplicate votes/ownership when GenPD UFS OPP and ARC mmcx.lvl provider both vote on the same CMD-DB resource.

Do not decide board-specific equivalence from resource-name similarity alone.

## Deliverable

Upload a Markdown report to:
- branch: ai2/round148-arc-regulator-portability-review
- path: firmware-analysis/round148/AI2_ROUND148_ARC_REGULATOR_AND_PROXY_CONSUMER_PORTABILITY_AUDIT.md

Include:
- source references with exact line ranges;
- API compatibility matrix;
- proxy behavior summary;
- source facts vs inferences vs unknowns;
- recommendation and next evidence required.

Read the uploaded report back to verify content and stop.

## Restrictions

- Static source review only.
- No code or DTS changes; do not prepare patches.
- No builds, tests, downloads or local filesystem execution.
- Do not connect to the tablet or use ADB/fastboot/recovery/UART/root/partitions.
- Do not inspect the private workspace of 2号 Agent or WorkBuddy Agent.
- Do not claim the public OnePlus source is the exact Huawei HOS driver.
- Do not invent CMD-DB AUX data, resource identifiers, voltages or hardware behavior.
- Do not authorize first device boot.
