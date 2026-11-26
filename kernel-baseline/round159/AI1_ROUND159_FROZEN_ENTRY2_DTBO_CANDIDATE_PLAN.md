# AI1 ROUND159 — Frozen HOS4.3 Entry 2 DTBO Candidate Plan

- Owner: 1号 AI (ChatGPT)
- Date: 2026-11-27
- Target: Huawei MatePad 11 DBY-W09 / HOS 4.3.0.196(C00E100) / SM8250
- Candidate ACK: android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9
- Accepted source tree: c56d93eafa35057d65176db6594d67d5144868a0
- Candidate base DTB: 108,680 B, SHA-256 9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60
- Exact target ABL payload: SHA-256 a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404
- Captured stock dtbo partition: 25,165,824 B, SHA-256 51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c
- Scope: one bounded implementation task to produce and review ONE host-side HOS4.3 DTBO candidate component. No device interaction or flashing.

## 1. Why this task exists

ROUND158 established from the exact HOS4.3 captures:
- Live boot selected stock DTBO Entry 2, board ID 0x200e; Entry 8 / 0x206a is not the user's active entry.
- The original Entry 2 fragment@143 supplies five /rootparam properties by external symbol fixup.
- The candidate base contains /rootparam but no phandle or exported symbols. The stock Entry 2 with 166 external fixups therefore cannot be reused.
- A single target-path="/rootparam" fragment merges into the candidate with only five properties changed. ROUND158 prototypes used public HOS4.2 values and are NOT final.
- Exact HOS4.3 values known so far: qcom,boardid raw bytes [08 02 06], qcom,board_name "DBY_W09_VD", qcom,product_name "DBY-W09", hardware_version "SH1DBSLM"; exact huawei,modem_id bytes must be extracted from the already captured stock Entry 2, not guessed.
- The HOS4.3 ABL selection/table contract is not fully closed. The target-derived table metadata and selector rules must decide whether one-entry or preserved-index table construction is appropriate.

## 2. ROUND159 bounded deliverable

Create ONE deterministic, reproducible host-side DTBO candidate for the accepted candidate base DTB. It must carry the exact HOS4.3 Entry 2 board identity and rootparam payload, using the smallest safe target-path overlay and exact ABL-compatible table metadata established from target evidence.

This is a DTBO-component exercise only. Do not create boot.img, boot-v2 package, ramdisk image, AVB metadata, vbmeta, signatures, keys, or a flashable partition package. Do not test on the device.

### Acceptance criteria

1. Target-derived Entry 2 fields are extracted from the ROUND155 stock dtbo capture and exact ABL, with source hashes and byte offsets.
2. The table-selection behavior is explained enough to select ONE table layout:
   - Prefer a single-entry table if exact ABL analysis shows it is accepted and the resulting dtbo_idx=0 is not a required downstream invariant.
   - If preserving stock index 2 is required, use the least-change layout supported by exact ABL evidence.
   - Do not guess or generate multiple competing variants.
3. New overlay root-node properties needed by ABL selection are copied exactly from stock Entry 2, not derived from decimal board-ID digits or public HOS4.2 files.
4. /rootparam receives exactly the five stock HOS4.3 properties, including the exact full huawei,modem_id byte payload.
5. Host application to the exact candidate DTB succeeds. A structural diff must show exactly five property additions under /rootparam and zero unrelated node/property changes.
6. Android DT table header/entry fields, offsets, sizes, page_size and version pass an independent parse and byte-for-byte roundtrip check. Use the exact target contract; do not assume a compact image or a 4096-aligned dt_offset is automatically valid/invalid.
7. Deliver hashes, sizes, reproducible build script, tool versions and full host logs. Raw ABL / raw stock partition dumps and unrelated identifiers stay local.
8. The independent 2号 AI reviewer issues a bounded GO/NO-GO for this DTBO component only.

## 3. AOSP format reference — correct alignment interpretation

Official AOSP DTB/DTBO partition documentation:
https://source.android.com/docs/core/architecture/dto/partitions

Facts to apply:
- A DTBO partition uses dt_table_header even for one entry; dt_entry_count=1 is explicitly supported.
- total_size includes the header, all dt_table_entry records and all DTB/DTBO blobs.
- id/rev/custom[] are optional hardware identifiers; a bootloader may inspect them, or inspect properties in the DTB/DTBO root.
- page_size is the assumed flash page size. The AOSP sample shows page_size=2048 with dt_offset=128, so dt_offset is not generally required to equal a page_size multiple.
- AOSP says mkdtimg appends the DTBO and does not itself align the payload; dtc -a can pad the blob (example -a 4). The exact HOS4.3 ABL remains authoritative if it imposes additional rules.

Do not repeat ROUND158's page-alignment observation as a failure by itself.

## 4. Work allocation

- WorkBuddy Window A (1号 Agent): exact target Entry 2 facts and ABL selector/table evidence. Taskbook below.
- WorkBuddy Window B (2号 Agent): one deterministic target-derived DTBO component, only after reading Window A's published facts. Taskbook below.
- 2号 AI: independent review after A/B delivery. It is not WorkBuddy Window B.

## 5. Stop conditions

STOP after one of these outcomes:
- PASS: exact target facts + one reproducible DTBO component + independent review all pass; report the next boot-v2 handoff blockers without automatically opening another broad audit.
- BLOCKED: a specific ABL contract or target payload fact cannot be proven. State exactly which fact is missing and stop; do not create speculative payloads.
- FAIL: host merge or DTBO serialization fails. Report the concrete failure and one minimal repair recommendation; do not multiply variants.

No ADB, root, fastboot, recovery, reboot, partition read/write, flash, source/config edit, AVB bypass, signing/key extraction, or device test is authorized by ROUND159.
