# ROUND70 — DBY-W09 DTBO table id versus root board-id: same-device reference reconciliation

**Date:** 2026-11-25  
**Owner:** Primary AI, public same-device source cross-check  
**Scope:** public same-device Linux DTBO packing reference, local HOS4.3 ROUND19 table inventory and project candidate; no local firmware, build or device operation.

## 1. Executive correction

A prior ROUND68 illustrative example suggested a candidate DTBO table entry with id=0x206a and rev=0 because the HOS4.3 stock DTBO entry 8 has that board-id. This was too specific and is now withdrawn.

The public same-device Linux reference shows a different, working design:
- base board DTS keeps qcom,board-id = <0 0>;
- the rootparam-only overlay sets root qcom,board-id = <0x206a 0>;
- its pack_dtbo.py creates a one-entry Android DT table with page_size=4096, version=0, entry id=0 and rev=0;
- the repository README states its tested ABL path requires the selected DTBO to populate /rootparam like stock overlay 8, otherwise the tablet returns to fastboot.

This is a strong structural reference for the same device, but its Linux 7.0 tree is based on an earlier HOS generation and is NOT proof of the user's HOS4.3 ABL table-selection rules.

Therefore:
- The root DT overlay identity value 0x206a and the Android dt_table_entry id are separate metadata layers.
- Do not automatically set dt_table_entry id=0x206a just because qcom,board-id in the overlay is 0x206a.
- Also do not automatically choose id=0 because the earlier public project did so.
- HOS4.3 ABL's exact policy for one-entry id=0/default matching versus per-board table ids remains UNKNOWN.
- No dtbo.img table configuration or package should be generated until the HOS4.3 ABL matching contract is independently evidenced.

## 2. Exact same-device reference facts

Repository:
https://github.com/svesnav/linux-dby-w09

Rootparam overlay:
https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso

Base board DTS:
https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts

DTBO packer:
https://github.com/svesnav/linux-dby-w09/blob/main/pack_dtbo.py

Build script:
https://github.com/svesnav/linux-dby-w09/blob/main/build_dev_images.sh

Observed source content:
- base board DTS sets qcom,msm-id = <QCOM_ID_SM8250 0x20001> and qcom,board-id = <0 0>.
- rootparam-only overlay sets root compatible = "huawei,dby-w09", "qcom,sm8250", qcom,board-id = <0x206a 0>, and the five /rootparam properties matching HOS4.3 ROUND19 entry 8 / VG.
- pack_dtbo.py constructs a DT table header with magic 0xD7B7AB1E, 32-byte header, 32-byte entry, one entry, page_size=4096, version=0; its entry fields include dt_size/dt_offset followed by id=0 and rev=0, with custom fields zero.
- build_dev_images.sh calls this packer for the one rootparam overlay. The README explicitly says ABL refuses a DTBO that does not fill /rootparam like the stock overlay.

The README describes that public repo's kernel as Linux 7.0, and the project handoff already notes its board DTS is based on HOS4.2 rather than the user's HOS4.3 package. The reference is therefore a useful same-device precedent, not authoritative proof for the current ABL version.

## 3. Reconciliation with HOS4.3 ROUND19

The user's HOS4.3 stock DTBO image has:
- 9 entries;
- page_size 4096;
- version 0;
- 32-byte table entries;
- entry 8 = board-id 0x206a, revision 0, variant VG.

This proves the stock table's entry metadata. It does not prove the user's ABL requires a replacement table to contain a matching id=0x206a entry, nor that a one-entry id=0 wildcard/default table will be accepted.

The rootparam candidate remains correct as a source overlay for the VG identity values. It is not yet a proven DTBO partition configuration.

## 4. Updated decision

Keep:
- root base board-id = <0 0>;
- rootparam overlay root qcom,board-id = <0x206a 0> as the VG-only identity candidate;
- the five ROUND19 rootparam properties from entry 8.

Do not yet choose the dt_table_entry id/rev or produce dtbo.img. Record the table metadata as UNKNOWN for HOS4.3 until one of:
- HOS4.3 ABL image / loader source directly establishes match behavior;
- a known-good HOS4.3 replacement DTBO package or build config establishes the accepted table format;
- an already authorized same-device boot log or successful boot evidence establishes which entry was selected.

Do not run a boot attempt, flash, unlock or policy bypass in order to discover this.

## 5. ROUND68 correction

The example in ROUND68 section 4 that showed id=0x206a in a hypothetical cfg_create file is withdrawn as a specific recommendation. It should now be read only as an example of how table metadata is explicit. The current HOS4.3 table id remains unknown for a replacement package, and the public Linux reference demonstrates a distinct id=0 / root overlay board-id=0x206a arrangement.

ROUND23 only compiles and applies the raw overlay to a temporary composite DTB. It does not package a DTBO table or validate ABL selection.

## 6. Status

- Public same-device base/root overlay / packer cross-check: PASS.
- HOS4.3 stock DTBO table inventory: PASS (ROUND19 / ROUND64).
- Whether HOS4.3 ABL accepts a one-entry id=0 table: UNKNOWN.
- Whether HOS4.3 ABL requires a per-variant id=0x206a table entry: UNKNOWN.
- Raw rootparam overlay compile/composite: pending ROUND23.
- DTBO partition packaging: NOT RUN.
- Device boot: NOT RUN.

 
## Addendum — AOSP DTBO metadata semantics

AOSP's DTB/DTBO partition specification explicitly defines dt_table_entry id/rev/custom fields as optional hardware-identification metadata. Its sample bootloader logic first checks entry fields and, if those fields are insufficient, loads and parses the DTB/DTBO root node for additional hardware properties. The mkdtimg create/cfg_create tool can set entry fields explicitly or read a 32-bit value from a root property path.

This confirms the distinction between:
- table-level fields: dt_table_entry.id / rev / custom[4];
- overlay-root fields: such as qcom,board-id=<board-id, board-revision> and qcom,boardid.

It does not specify how Huawei HOS4.3 ABL implements matching. In particular, optional metadata does not mean every ABL treats id=0 as wildcard. The public same-device Linux id=0 packaging is an older-HOS project observation only. Keep HOS4.3 replacement table id/rev unknown.

AOSP reference: https://source.android.com/docs/core/architecture/dto/partitions
