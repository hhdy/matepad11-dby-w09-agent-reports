# ROUND61 Phase F — boot-image packaging, ramdisk and AVB gate

**Date:** 2026-11-25  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Status:** BLOCKED FOR PACKAGING — ROUND64 completed the trusted read-only boot/ramdisk/DTBO/AVB inventory, but ABL-selected DTBO, one anomalous vbmeta_cust image, final Phase E inputs and boot-path acceptance remain unresolved.

## 1. Existing evidence

ROUND12's original tool-availability blocker is superseded by the local Agent's ROUND64 report below. ROUND12 remains historical context only; its `AVB0` magic scan was not AVB evidence. ROUND64 used the already-present AOSP `external/avb/avbtool.py` from the pinned ACK source tree (version 1.4.0) in read-only `info_image` mode, with a sanitizer that suppresses keys, signatures, salts, image/hashtree digests and rollback values. The tool gate for metadata inspection is therefore satisfied; this does not provide signing capability or permission to modify an image.

ROUND2's reported whole-file sizes (96 MiB `boot.img`, 2 MiB `ramdisk.img`, 24 MiB `dtbo.img`) are only inventory facts; sizes and an `AVB0` magic observation do not establish footer placement or AVB coverage. ROUND64 adds the following header/payload facts, distinguishing prior-round header parsing from the new AVB parser output: stock `boot.img` is header v2 / page 4096, with kernel 22,264,379 bytes at offset 4,096, embedded ramdisk 519,986 bytes at offset 22,269,952, embedded DTB 1,664,243 bytes at a header-derived offset, and payload end 24,457,216. The separate `ramdisk.img` is header v0 / page 2048, with a 1,322,962-byte payload ending at 1,325,056. The DTBO image has nine entries and a container `total_size` of 2,963,810 bytes. These describe stock inputs only, not a replacement image layout.

ROUND43 first identified the header-v2 / separate-ramdisk / DTBO layout. ROUND64 now supplies trusted footer and descriptor classification plus the prior inventory's header offsets. The exact ABL-composed runtime layout, selected DTBO and whether ABL will accept a test image remain unverified.

## 2. ROUND64 local-Agent read-only inventory — completed, packaging still blocked

Full sanitized report (on `firmware-audit-v1`):
[ROUND64 Phase F — HOS4.3 boot-v2 / ramdisk / DTBO / AVB read-only evidence](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round64/round64-dby-w09-hos43-bootv2-ramdisk-dtbo-avb-evidence.md).

### Verified from trusted parser output or clearly identified prior inventory

- **Boot image:** Android boot header v2; page size 4096. The prior-round header inventory records kernel, ramdisk and embedded-DTB payload positions/sizes; the trusted AVB parser independently reports the boot footer's original-image-size boundary. The Agent distinguishes parser-derived footer information from prior-round header offsets.
- **Separate ramdisk:** a standalone `ramdisk.img` exists and is header v0 with page size 2048. Its payload inventory is gzip-to-CPIO newc. The archive contains 17 entries; no fstab, init scripts, ueventd rules, module-load lists or kernel modules were found in that ramdisk inventory.
- **DTBO container:** version 0, page size 4096, nine entries. The runtime ABL-selected entry is **UNKNOWN**. Entry 8 is only a candidate by board-id; do not treat it as selected. Its 145 fragments target Huawei vendor-only nodes absent from the minimal ACK board draft.
- **AVB metadata:** AOSP avbtool 1.4.0 reports footers on 14 of 15 inventoried images. Root vbmeta descriptor/chain metadata includes coverage targets for `boot`, `ramdisk` and `dtbo`; the separate ramdisk and DTBO are not unprotected just because they are separate partitions. The report publishes descriptor classes/target names only, not cryptographic secrets or digest material.
- **First-stage fstab location:** prior-round inventory places it in the base DTB at `/firmware/android/fstab`, not in the separate ramdisk. This does not identify the actual selected DTBO or prove the whole first-stage boot path.

### Material anomaly and unresolved facts

- `vbmeta_cust.img` has an AVB footer whose original-image-size / vbmeta-blob pointer is outside the 1 MiB file. The referenced blob is reported as an empty `Algorithm: NONE` object with no descriptors. Whether this is intentional, a truncated extraction or a vendor layout variant is **UNKNOWN**; descriptor coverage for `cust` is not established.
- Which of the nine DTBO entries ABL selects is **UNKNOWN**.
- Whether ABL accepts a temporary/RAM boot remains **UNKNOWN**. ROUND62 is a same-device HOS4.2 cross-reference only and is not proof of HOS4.3 policy.
- The Agent had no `mkbootimg` / `unpack_bootimg` executable on PATH. The AVB report's parser was used only for read-only metadata inspection; no packaging or signing command was executed.
- No candidate image, modified footer, vbmeta or flash package was created.

Therefore the AVB inventory requirement is **substantially satisfied for read-only classification**, but Phase F's package-exit gate is not met. The anomalous `vbmeta_cust`, unknown ABL DTBO selection, unproven HOS4.3 boot method, and unresolved Phase E memory/board-DTS inputs prevent a deterministic boot package. No guessed `mkbootimg` parameters or AVB changes are allowed.

## 3. Packaging decision

The ROUND58 Kleaf target is intentionally Image-first. It does not produce a DTB, DTBO, boot image, vendor_boot, init_boot or flash package. This is appropriate while the board DTS/memory gate and stock packaging metadata remain unresolved.

Do not run `mkbootimg` with guessed arguments, append or strip AVB footers, or modify stock vbmeta/chained vbmeta images. Do not assume a modern `vendor_boot`/`init_boot` layout applies to this header-v2 image.

## 4. Remaining gates before packaging

The ROUND64 read-only Agent report has now completed much of this inventory. Remaining gates are:

1. **ABL selection and acceptance:** obtain trustworthy HOS4.3 evidence of the selected DTBO entry and the actual boot path / temporary-boot acceptance. A board-id candidate is not proof.
2. **AVB anomaly resolution:** explain `vbmeta_cust` using an authoritative local image/partition inventory or leave its coverage explicitly unresolved. Do not repair, regenerate or reinterpret it speculatively.
3. **Phase E inputs:** close the final ABL memory handoff and physical PM8150 input topology before generating any DTB or boot candidate.
4. **Packaging-tool contract:** inspect a trusted, available toolchain capable of reproducing the exact header-v2 and separate-ramdisk layout, offsets, padding and footer placement. The existence of AOSP avbtool for read-only inspection does not prove a compatible signing or mkbootimg path.
5. **First-stage integration:** preserve the base-DTB fstab and verify how the actual ABL combines the base DTB, selected DTBO and separate ramdisk. Identify module-loading and root/verity expectations rather than infer them from an absent `modules.load` file.
6. **Reversible plan:** only after the above are evidenced, write a non-flashing package specification with exact inputs, checksums, format, rollback and validation chain. No boot candidate until the Phase E handoff is resolved.

Do not assume a RAM-only boot works, alter AVB, install tools, or bypass the evidence/tool gate.

## 5. Phase F verdict

**BLOCKED FOR PACKAGING / NOT PACKAGED.** The ROUND64 read-only metadata inventory is complete, but no boot image, ramdisk, DTBO or vbmeta file has been generated or modified. Phase F is not a boot-package PASS; the ABL-selected DTBO, vbmeta_cust anomaly, actual HOS4.3 boot method and Phase E memory/board evidence remain open.


## ROUND62 same-device boot-chain cross-reference (not HOS4.3 proof)

The primary report `kernel-baseline/round62/round62_same_device_abl_bootv2_ramdisk_dtbo_reference.md` reviews public DBY-W09 Linux source pinned at `116cb1fe06110543ce03217e8bd8f35c12ca89c3`. It reports Huawei ABL consuming a header-v2 `boot` image plus a separate `ramdisk` partition, and that `fastboot boot` was refused on that project's tested setup. It also documents a required ABL-selected DTBO fragment that populates `/rootparam`.

This raises the risk that a RAM-only first boot may not be available and makes a future write-based boot experiment a separate, high-authorization operation. It is cross-reference only: that public port's own DTS refers to HarmonyOS 4.2, so it does not prove the user's HOS4.3 ABL policy, selected overlay, partition sizes, offsets, AVB footer or RAM map. Do not copy its stock hashes, fixed 96 MiB / 2 MiB sizes, command line, offsets, DTB or AVB data. The reusable method is to inspect and no-op-rebuild the exact local stock header-v2 image before replacing any payload, after local AVB and final-memory evidence are available.

**Packaging remains BLOCKED and no image is generated.** Do not assume `fastboot boot` works, and do not write boot/ramdisk/DTBO/vbmeta without a separate explicit reviewed authorization and a verified rollback path.
