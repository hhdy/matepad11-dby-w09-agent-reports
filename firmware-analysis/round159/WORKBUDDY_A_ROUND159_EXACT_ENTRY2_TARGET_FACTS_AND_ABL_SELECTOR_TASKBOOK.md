# ROUND159 — WorkBuddy Window A Taskbook: Exact HOS4.3 Entry 2 Facts + ABL Selector Contract

- Executor: **WorkBuddy Window A (1号 Agent)** only.
- Role: local evidence extraction and exact HOS4.3 ABL analysis. You are NOT 2号 Agent and NOT 2号 AI.
- Target: DBY-W09 / HOS 4.3.0.196(C00E100) / SM8250.
- Mode: offline/read-only against Window A's own ROUND155 capture and its own existing ABL analysis workspace.
- No ADB, device, root, fastboot, recovery, reboot, partition access, writing to device, flash, AVB edits, signing or keys. Do not access Window B's workspace.

## 1. Accepted identities

- ABL PE payload SHA-256: a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404 (2,597,064 B).
- Captured stock dtbo.img SHA-256: 51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c (25,165,824 B).
- Candidate base DTB SHA-256: 9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60 (108,680 B).
- Live runtime observation: androidboot.dtbo_idx=2, matching stock DTBO Entry 2 / qcom,board-id <0x200e 0>. Entry 8 / 0x206a is not the active target.
- ROUND158 exact HOS4.3 rootparam values already reported: qcom,boardid raw bytes [08 02 06]; qcom,board_name="DBY_W09_VD"; qcom,product_name="DBY-W09"; hardware_version="SH1DBSLM". The huawei,modem_id full property bytes remain to be extracted from stock Entry 2.

## 2. Task A — extract exact stock Entry 2 data

From Window A's own verified ROUND155 capture only:

1. Re-hash the raw dtbo partition and confirm exact size/hash.
2. Parse and publish the full dt_table_header: magic, total_size, header_size, dt_entry_size, dt_entry_count, dt_entries_offset, page_size, version.
3. Parse all nine dt_table_entry records. For Entry 2, publish dt_size, dt_offset, id, rev, custom[0..3], and distinguish these table fields from FDT root properties.
4. Extract Entry 2's FDT to a separate offline file, compute full SHA-256, and enumerate root properties used for selector matching (including qcom,msm-id, qcom,board-id, subtype/DDR and any PMIC/SOC fields actually present).
5. Extract the exact raw value of /fragment@143/__overlay__/huawei,modem_id as a byte array and byte length. Also record qcom,boardid as raw bytes, not a guessed cell conversion. Include a hash for each property payload. No modem/serial/IMEI-like device identifier from unrelated partitions is needed.
6. Record all other /rootparam fields in their exact wire representation and verify the values against the ROUND151 live FDT if the matching raw captured property is available.
7. Publish a machine-readable JSON file containing the required Entry 2 table fields, selector root properties, exact five /rootparam property encodings, source artifact hashes, and FDT hash. Use explicit encodings: string, u32-cell list, or raw byte hex. Do not coerce byte properties to strings or cells.

## 3. Task B — decode exact ABL selection and DTBO parser contract

Use the exact ABL payload above. This is a narrow continuation of ROUND158, not a broad reverse-engineering audit.

1. Trace the selector from the nine-entry DTBO table through matching and selected-index return/output. Determine which fields actually participate:
   - dt_table_entry id/rev/custom;
   - root qcom,msm-id, qcom,board-id, board subtype, DDR size;
   - any compatible/model/PMIC identity fields.
2. Explain how stock Entry 2 is selected and how androidboot.dtbo_idx=2 is derived.
3. Determine whether a one-entry image that carries Entry 2's exact selector root properties and exact dt_table_entry metadata would be selected on this HOS4.3 ABL. State its resulting dtbo_idx and whether any later ABL/kernel handoff consumes that index as a required fixed value.
4. Decode only the DT table parser constraints needed for the host candidate: accepted header/version, entry count, offsets/bounds, alignment assumptions (if any), FDT total size/padding, duplicate/unknown fields and whether zero trailing partition padding is ignored.
5. Do not assert 4096-byte dt_offset alignment merely because header.page_size is 4096. Compare actual stock layout and AOSP standard format. Any HOS4.3-specific requirement must have direct ABL instruction/control-flow evidence.
6. Do not re-investigate /rootparam string lookup: ROUND158 already established there is no rootparam-specific ABL string/xref. Focus on selector/table handling.

## 4. Required report and data artifacts

Create:
- firmware-analysis/round159/WORKBUDDY_A_ROUND159_EXACT_ENTRY2_TARGET_FACTS_AND_ABL_SELECTOR_REPORT.md
- firmware-analysis/round159/entry2-target-facts.json

Report must include:
- source hashes, extraction commands, exact table and Entry 2 fields;
- exact /rootparam byte payloads including full modem_id hex (only that property; no unrelated identifiers);
- ABL function ranges, instruction addresses, decision path and evidence grade;
- one-entry-vs-preserved-index decision with an explicit GO/NO-GO and resulting dtbo_idx;
- if a question is not proven, say so and identify exact missing evidence. Do not invent certainty.

## 5. Absolute boundaries

- No device operations or partition access.
- Do not publish raw ABL, raw dtbo.img, or unrelated partition dumps.
- Do not edit kernel source/config or candidate DTB.
- Do not create an overlay or DTBO candidate in this task; Window B owns candidate creation.
- Do not use public HOS4.2 rootparam values as fallback.
- Stop after report + JSON have been committed and read back.

END ROUND159 — WINDOW A
