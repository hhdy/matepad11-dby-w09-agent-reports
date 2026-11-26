# WORKBUDDY ROUND153 — Stock boot-chain / DTBO / ABL memory-fixup audit

- **Assigned executor: WorkBuddy Agent (local Agent 1) only.**
- Not 2号 AI; not 2号 Agent; not AI1.
- Device: Huawei MatePad 11 (2021), DBY-W09 / HWDBY / KONA / SM8250.
- Candidate: ACK `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`, content tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
- Branch: `workbuddy/round153-stock-boot-chain-dtbo-memory-fixup-audit`.
- Task type: **existing-artifact, read-only firmware/boot-chain audit**. No device access.

## 1. Purpose

Resolve the boot-chain questions left by ROUND152 before a RAM-only DTS correction or any candidate build is approved:

1. Candidate DTS says DBY-W09 DTBO board ID `0x206a` / Entry 8, while the live stock boot reports `androidboot.dtbo_idx=2`, corresponding to board ID `0x200e` / Entry 2.
2. ROUND138 found Entry 2 and Entry 8 UFS/PMIC/regulator/RPMh payloads equal, but did not establish that the full overlays are identical.
3. Stock live FDT has three System RAM tuples, while the candidate source has one zero-size upstream placeholder. We need determine what the available stock boot artifacts can prove about ABL memory fixups, without touching the device.

## 2. Permitted input scope

Use only:
- WorkBuddy Agent 1's own already-existing workspace and its own prior firmware extraction directories;
- the published ROUND137, ROUND138, ROUND151 and AI1 ROUND152 reports linked below;
- public firmware/source files reachable through normal public repositories where needed.

Do not enter, inspect, copy, or reuse any 2号 Agent or 2号 AI private workspace. Do not inspect unlisted WorkBuddy user-private data. If the existing firmware package is absent from WorkBuddy's own workspace, stop and report it absent.

Required published references:
- ROUND138 DTBO inventory: https://github.com/hhdy/matepad11-dby-w09-agent-reports
- ROUND151 live runtime report: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round151-root-readonly-runtime-audit/firmware-analysis/round151/WORKBUDDY_ROUND151_ROOT_READONLY_RUNTIME_AUDIT_REPORT.md
- AI1 ROUND152 decision: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round152/AI1_ROUND152_DELIVERY_REVIEW_AND_ROUND153_DECISION.md

## 3. Required work

### A. Inventory existing firmware artifacts

Search only WorkBuddy Agent 1's existing workspace for already-extracted or already-downloaded:
- `abl.elf`, `abl.img`, `abl.mbn`, `xbl.elf` or equivalent bootloader payloads;
- stock `dtbo.img`, base `dtb`, `boot.img`, `vendor_boot.img`, firmware update archives or extracted UPDATE.APP contents;
- hash manifests and extraction logs establishing artifact provenance.

For every relevant artifact record path relative to the WorkBuddy workspace, size, SHA-256 and provenance. Do not upload raw firmware or private blobs. If no ABL artifact exists, state that clearly; do not infer its behavior.

### B. Resolve DTBO Entry 2 versus Entry 8

Using the existing stock `dtbo.img` if present:
1. Revalidate header, entry count, entry indices and board-id/revision fields for Entries 2 and 8.
2. Compare the **entire overlay payloads**, not only UFS/PMIC/RPMh nodes. Report byte equality or a structured full-node/property diff.
3. Identify which entry is selected by the live `dtbo_idx=2` evidence and distinguish the selected index from board-id metadata.
4. Compare these findings with the candidate DTS comment `0x206a` and candidate `qcom,board-id = <0 0>`.
5. Do not edit the DTS or rewrite the comment. Recommend an exact correction only if evidence supports it.

### C. ABL memory-fixup evidence

If a stock ABL or XBL artifact exists:
1. Search strings/symbols where possible for FDT memory-node lookup, `device_type=memory`, `/memory`, `fdt_setprop`, `memstart`, `dram`, `memory` and Qualcomm memory fixup routines.
2. Identify whether the binary contains readable function/symbol evidence, disassembly evidence, or only weak strings. Grade evidence accordingly.
3. Do not claim that the stock ABL will patch a replacement DTB unless the code path or a reproducible artifact comparison demonstrates it.
4. Compare stock base FDT placeholder (if present) with the ROUND151 live FDT and record whether the artifact proves wholesale replacement, one-tuple size patch, or remains indeterminate.

If ABL is absent or stripped and cannot be responsibly analyzed, record the unresolved contract and stop. No speculative conclusions.

### D. Output decision

Give a clear result for:
- Are Entries 2 and 8 fully identical?
- Does current live evidence support Entry 2 as the actual selected overlay?
- Is the candidate DTS comment wrong, stale, or still unresolved?
- Is there evidence ABL fills all three RAM windows into a replacement DTB?
- What exact non-device evidence remains required before a candidate boot package can be assembled?

## 4. Prohibitions

- No tablet / ADB / root / fastboot / recovery / UART / partition reads.
- No reboot, flash, boot, writes or state change.
- No source, DTS, DTBO, config or patch edits.
- No builds or tests.
- Do not access another Agent's workspace.
- Do not upload ABL/XBL/DTB/DTBO raw binaries, private FDT or serial-number-bearing logs.
- Do not disclose serial, IMEI, MAC, panel ID or user-specific identifiers.
- Do not claim bootloader memory fixups from the stock live FDT alone.

## 5. Deliverable

Upload:
`firmware-analysis/round153/WORKBUDDY_ROUND153_STOCK_BOOT_CHAIN_DTBO_MEMORY_FIXUP_AUDIT_REPORT.md`

Before stopping, read the uploaded report back and verify its exact blob SHA and content. Report only sanitized findings and references. **STOP after delivery; do not start another round.**
