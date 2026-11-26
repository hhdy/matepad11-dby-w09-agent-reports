# ROUND159 Window B Continuation — Window A Facts Now Available (Same Round, No New Audit)

Status update: the previous Window B report "BLOCKED — WAITING FOR WINDOW A FACTS" is now stale. Window A has published both required artifacts. Continue the SAME ROUND159 task; do not open ROUND160.

## 1. Read these exact inputs

Window A report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round159-exact-entry2-facts/firmware-analysis/round159/WORKBUDDY_A_ROUND159_EXACT_ENTRY2_TARGET_FACTS_AND_ABL_SELECTOR_REPORT.md

Window A original facts JSON:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round159-exact-entry2-facts/firmware-analysis/round159/entry2-target-facts.json

Window B normalized builder input (prepared from Window A's exact JSON; use this for the current script):
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round159-entry2-preserving-dtbo-candidate/firmware-analysis/round159/entry2-target-facts.builder-input.json

Normalized input blob: `fabda246500506a52d03ea57149614116b3f3686`.

## 2. Exact candidate facts — do not substitute

- HOS4.3 selected stock entry: index 2, root `qcom,board-id=<0x200e 0>`.
- Original Entry2 dt_table_entry id=0, rev=0, custom[0..3]=0.
- ABL accepts a one-entry table structurally; one exact match selects index 0. No fixed index-2 consumer was found inside the decoded ABL. Userspace consumers were not audited. This is a host candidate GO, not boot proof.
- Header: magic 0xd7b7ab1e; header_size=32; dt_entry_size=32; count=1; entries_offset=32; page_size=4096; version=0; only FDT starts at offset 64.
- Exact rootparam payload:
  - `qcom,boardid`: u32 cells [8,2,0,6], 16-byte wire payload `00000008000000020000000000000006`.
  - `qcom,board_name`: `DBY_W09_VD`.
  - `qcom,product_name`: `DBY-W09`.
  - `hardware_version`: `SH1DBSLM`.
  - `huawei,modem_id`: u32 cells [0xffffffff,0], 8-byte payload `ffffffff00000000`.
- Do NOT use the old 3-byte shorthand `080206`, or any HOS4.2 public placeholder.
- For ABL selector root props, include only the proven matching property `qcom,board-id=<0x200e 0>`. Entry2 `compatible` and `model` may be documented, but Window A's selector result identifies qcom,board-id as the effective field for this stock table.

## 3. Continue build and fix the generator as needed

Use the existing `build_entry2_dtbo.py` in this branch and the normalized facts file above. The existing script's expected normalized schema is supplied. Run it against Window B's own exact candidate base DTB SHA-256:
`9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60`.

Before calling the build complete, correct these implementation issues if still present:
1. Current script writes the same binary FDT bytes to both `entry2-rootparam.dtso` and `.dtbo`. A `.dtso` deliverable must be readable DTS source, not a binary blob. Generate a textual DTS source (or rename the textual source artifact consistently and update the report/task path).
2. Ensure the built overlay contains exact four-cell `qcom,boardid` and exact two-cell `huawei,modem_id` from the facts file.
3. The table parser must check that embedded FDT totalsize equals dt_size and that table/entry/data ranges do not overlap or exceed total_size. The candidate builder already uses one entry, offset 64 and header total_size = 64 + payload length.
4. Host merge command order must be `fdtoverlay -i BASE -o OUTPUT OVERLAY`; verify actual structural diff rather than trusting RC alone.

Run:
```sh
python3 build_entry2_dtbo.py build \
  --facts entry2-target-facts.builder-input.json \
  --base <your verified candidate DTB> \
  --outdir round159-entry2-final
```

Acceptance: the Android DT table is independently reparsed and byte-roundtripped; exactly one table entry; entry id/rev/custom all zero; FDT has exact `qcom,board-id=<0x200e 0>`; host merge adds exactly five properties under `/rootparam` and has zero unrelated changes; negative malformed-table and typo-target tests reject; all artifacts and hashes listed in the manifest.

## 4. Required final publication

Publish/update on this same branch:
- `firmware-analysis/round159/WORKBUDDY_B_ROUND159_FROZEN_ENTRY2_DTBO_CANDIDATE_REPORT.md`
- `firmware-analysis/round159/build_entry2_dtbo.py`
- `firmware-analysis/round159/entry2-rootparam.dtso` (text source, or clearly documented source extension)
- `firmware-analysis/round159/entry2-rootparam.dtbo`
- `firmware-analysis/round159/entry2-candidate.dtbo.img`
- `firmware-analysis/round159/entry2-candidate-manifest.json`
- test logs and hashes (no raw stock dtbo.img/ABL upload).

If a required fact or host check fails, stop and report the precise failure. Do not create competing variants.

## 5. Hard boundaries

No device connection, ADB, root, fastboot, reboot, recovery, partition read/write, flash, boot.img, boot-v2, ramdisk, vbmeta, signing, keys, or AVB edits. Do not edit the kernel source, config or base DTB. This is the final bounded Window B work in ROUND159.
