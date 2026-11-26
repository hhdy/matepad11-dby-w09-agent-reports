# ROUND158 — WorkBuddy Window B: independent rootparam overlay and DTBO-container audit

- Executor: **WorkBuddy Window B (2号 Agent)**, a separate WorkBuddy chat.
- Do not access Window A's private workspace, local files, build output or raw ABL.
- This is an independent offline candidate-design experiment, not permission to flash or boot.
- Use only Window B's own reconstructed candidate source tree and public repository evidence cited below.

## 1. Context and objective

ROUND157 Window B successfully built the exact candidate source tree:
- source tree: `c56d93eafa35057d65176db6594d67d5144868a0`;
- Kleaf config: SHA-256 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`;
- Image: 44,820,992 B / SHA-256 `f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21`;
- reproduced standalone Kbuild DTB: 108,680 B / SHA-256 `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60`.

New public evidence from another DBY-W09 Linux port suggests that ABL may require a DTBO entry to populate `/rootparam` with board identity, and that a target-path-only minimal overlay is preferable to applying stock fragments:
- https://github.com/svesnav/linux-dby-w09
- https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso
- https://github.com/svesnav/linux-dby-w09/blob/main/pack_dtbo.py
- https://github.com/Anglerfish314/matepad11-dby-w09-kubuntu

**Critical variant difference:** that published HOS4.2.0.213 sample reports 6 GB RAM and uses board-id `0x206a`; our target HOS4.3.0.196 live capture shows 12GB-class RAM windows and selected stock Entry 2 with board-id `0x200e`. Treat the public implementation as a reference, not the correct board-id for this target. Do not make a single chosen overlay and call it accepted.

## 2. Independent candidate source audit

Using your own candidate tree `c56d93e...` and compiled DTB:

1. Determine whether the candidate actually defines `/rootparam`, whether it is empty or pre-populated, and whether it has a label/phandle.
2. Record `/rootparam` node path, current properties, phandle, and corresponding source lines.
3. Record whether base DTB has `/__symbols__`, `/__fixups__`, `/__local_fixups__`.
4. Compare with public `dby-w09-rootparam.dtso`: root `model`, `compatible`, `qcom,board-id`; fragment fields for `qcom,boardid`, `qcom,board_name`, `qcom,product_name`, `hardware_version`, `huawei,modem_id`.
5. Explicitly mark every public property value as HOS4.2 reference evidence only. The live HOS4.3 Entry2 0x200e and Entry8 0x206a identities are in ROUND153 reports; do not claim which must be used for the current candidate.

## 3. Build two offline overlay prototypes

Only if `/rootparam` exists in the candidate, or in a clearly isolated scratch-DTS variant where it is added:

- Prototype P: fragment uses `target-path="/rootparam"` (no external labels/fixups).
- Prototype Q: phandle-target form for comparison, with all symbols/fixups exported correctly if technically required.

For P, compile a target-path overlay containing only the public HOS4.2 reference rootparam fields, plus clearly labelled variants for the two possible board-id metadata values `0x200e` and `0x206a`. Do not silently merge the two IDs into one file or assert either is correct.

For Q, record symbol/fixup dependencies and whether the candidate base can resolve them. Do not add the 166 stock downstream symbol stubs; the task is to compare a minimal overlay to the current candidate, not to recreate the vendor DTBO.

For each prototype:
- report source, overlay FDT size/hash, header, fragment target and fixup counts;
- run host `fdtoverlay` against the candidate DTB and validate resulting `/rootparam` properties;
- show whether any unrelated property/node changes;
- check overlay merge error behavior only in host tools, not infer ABL atomicity from it.

## 4. Android DTBO table container checks

Reimplement or reuse the small public `pack_dtbo.py` logic only for disposable offline test artifacts. Verify:
- DT table magic `0xD7B7AB1E`;
- 32-byte header and 32-byte entry;
- total size, entry count, offsets, size and page alignment;
- the two candidate board-id metadata variants are represented consistently with the embedded overlay FDT;
- `dt_table_entry` fields and table-end bounds parse back identically.
Do not assert ABL accepts the table. The exact target selector contract must come from the HOS4.3 ABL audit in Window A.

## 5. Build handoff and module-config sanity

Use the existing ROUND157 build evidence only; do not rerun the full kernel build.

- Confirm whether the empty `modules_staging_dir.tar.gz` (67 B) and zero-byte `Module.symvers` result from the candidate `.config` setting `CONFIG_MODULES=n`, from all drivers being built-in, or from a packaging gap.
- Identify the required storage-first drivers and verify the configuration includes them built-in.
- Do not alter the config or source in this round.

## 6. Deliverable

Publish:
`firmware-analysis/round158/WORKBUDDY_B_ROUND158_INDEPENDENT_ROOTPARAM_DTBO_VARIANT_AND_CONTAINER_AUDIT_REPORT.md`

Include candidate rootparam inspection, public-reference comparison, prototype P/Q results, DTBO-table parsing checks, modules/config finding, SHA-256 values, and limitations. Read back and verify the report, then STOP.

## 7. Prohibitions

No Window A files or private outputs. No ADB/root/fastboot/device access. No partition read/write, flash, reboot, temporary boot, recovery. No boot.img or vbmeta package. No signing/key extraction/AVB bypass. No source edits or config changes. No claim of flash readiness.

— END —