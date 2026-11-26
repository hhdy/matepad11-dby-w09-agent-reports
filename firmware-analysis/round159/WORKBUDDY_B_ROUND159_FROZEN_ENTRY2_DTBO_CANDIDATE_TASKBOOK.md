# ROUND159 — WorkBuddy Window B Taskbook: One Frozen HOS4.3 Entry 2 DTBO Component

- Executor: **WorkBuddy Window B (2号 Agent)** only.
- Role: independent host-side implementation in Window B's own workspace. You are NOT 2号 AI and do not access Window A's private workspace.
- Target: DBY-W09 / HOS 4.3.0.196(C00E100), candidate ACK 6.18.33.
- Mode: offline host-only. No device, no ADB/root/fastboot/recovery, no reboot, no partition writes, no flash, no AVB/signing/key work.

## 1. Fixed input identities

- Candidate source tree: c56d93eafa35057d65176db6594d67d5144868a0.
- Candidate base DTB: 108,680 B, SHA-256 9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60.
- Original stock dtbo partition (Window A only): 25,165,824 B, SHA-256 51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c.
- Live selected stock entry: Entry 2 / board-id 0x200e / androidboot.dtbo_idx=2.
- Current target-path mechanics already host-tested in ROUND158: target-path="/rootparam" adds exactly five properties to the candidate base with no unrelated change. However those prototypes used HOS4.2/public placeholder data and must NOT be reused as final content.

## 2. Dependency on Window A — do not guess

First prepare a deterministic generator/validator skeleton that accepts a JSON facts file. Then fetch Window A's published:
firmware-analysis/round159/entry2-target-facts.json
from branch workbuddy/round159-exact-entry2-facts.

Use ONLY its exact HOS4.3 property bytes and the ABL selector/table decision. Do not read Window A's private workspace or raw files.

If the JSON/report is not yet published, work only on the generic script skeleton and stop before producing any DTBO candidate. Do not substitute public HOS4.2 values.

## 3. Produce ONE candidate only

After Window A data is available:

1. Generate a minimal plugin overlay with:
   - exact root-level selector properties required by HOS4.3 ABL, copied from the Entry 2 facts;
   - one fragment targeting target-path = "/rootparam";
   - exactly the five exact HOS4.3 /rootparam properties, including the complete huawei,modem_id byte payload.
2. Do not add unrelated device configuration fragments. Do not attempt to transplant stock Entry 2's 166 external-fixup overlay.
3. Use the single-entry table OR another one-layout design only if Window A establishes which layout is acceptable. Preserve the exact stock Entry 2 dt_table_entry id/rev/custom metadata where the selector requires it.
4. If a single-entry table is proven acceptable, build one entry with the exact Entry 2 selector values and record resulting dtbo_idx=0. If ABL requires index 2, construct the minimum compatible one-table layout that preserves it, only if the required nonmatching entries can be represented safely and deterministically. Do not fabricate entries or build competing variants.
5. Use the HOS4.3 stock page_size and exact ABL parser constraints. page_size must not be confused with a universal dt_offset alignment rule: AOSP documentation explicitly shows page_size=2048 with dt_offset=128 and describes page_size as flash-page size. Follow any additional HOS4.3 ABL-specific check only if proven from its code.
6. Build the container using a reproducible script (Python or existing dtc/mkdtimg). Keep all offsets/sizes within the header's total_size and exact FDT payload size. Reparse independently and reserialize all fields; verify source-overlay bytes exactly equal the embedded FDT.
7. Apply the overlay with host fdtoverlay to the exact candidate base DTB. Compare base and merged FDT structurally: exactly five property additions under /rootparam; zero unrelated node/property changes; all five payloads byte-identical to Entry 2.
8. Add negative host checks: a target-path typo must fail, and a deliberately malformed/truncated table must be rejected by your parser. Do not present host-tool acceptance as ABL/device acceptance.

## 4. Required deliverables

Create:
- firmware-analysis/round159/WORKBUDDY_B_ROUND159_FROZEN_ENTRY2_DTBO_CANDIDATE_REPORT.md
- firmware-analysis/round159/build_entry2_dtbo.py
- firmware-analysis/round159/entry2-rootparam.dtso
- firmware-analysis/round159/entry2-rootparam.dtbo
- firmware-analysis/round159/entry2-candidate.dtbo.img
- firmware-analysis/round159/entry2-candidate-manifest.json

The binary artifacts should be committed only if repository policy accepts user-provided firmware-derived device-tree fragments. If binary files are not appropriate, commit the reproducible script and hex/manifest representation, retain the generated binary locally, and state the exact SHA/size in the report. Do not upload raw stock dtbo.img or ABL.

Report exact facts.json blob/branch, inputs hashes, commands, tools, full output hashes/sizes, candidate table fields and selection index, host merge diff, negative checks, limitations and explicit component-only decision.

## 5. Stop conditions

- Produce exactly ONE target-derived DTBO candidate.
- If Window A cannot prove the table layout/selector needed, stop before building speculative binaries and report the precise blocker.
- Do not create boot.img, boot-v2 package, ramdisk, vbmeta or AVB metadata.
- No device operation, fastboot command, partition write or flash.
- Do not start another general audit round.

END ROUND159 — WINDOW B
