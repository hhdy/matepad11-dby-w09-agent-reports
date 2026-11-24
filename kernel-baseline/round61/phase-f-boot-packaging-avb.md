# ROUND61 Phase F — boot-image packaging, ramdisk and AVB gate

**Date:** 2026-11-25  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Status:** BLOCKED — stock HOS4.3 AVB footer/descriptor coverage and exact packaging metadata remain unknown.

## 1. Existing evidence

ROUND12 on `firmware-audit-v1` is the authoritative read-only AVB result:

- No trusted, already-installed `avbtool` or previously reviewed AVB metadata helper was available in the local Agent environment.
- The existing reviewed scripts detect leading `AVB0` magic only; they do not parse AVB footers or vbmeta descriptors.
- No footer presence, original-image-size field, hash/hashtree descriptor, chained vbmeta relationship or partition coverage was determined.
- The task stopped without installing tools, downloading binaries, writing a parser, invoking WSL, changing policy or accessing a device.

ROUND2's previously reported sizes are 96 MiB for `boot.img`, 2 MiB for `ramdisk.img` and 24 MiB for `dtbo.img`. Sizes and an `AVB0` magic observation do not establish footer placement or AVB coverage.

ROUND43 describes the HOS4.3 boot-image context as header v2 with a separate ramdisk and DTBO image. Exact packaging offsets/alignment, footer state and vbmeta descriptor relationships remain unverified.

## 2. Packaging decision

The ROUND58 Kleaf target is intentionally Image-first. It does not produce a DTB, DTBO, boot image, vendor_boot, init_boot or flash package. This is appropriate while the board DTS/memory gate and stock packaging metadata remain unresolved.

Do not run `mkbootimg` with guessed arguments, append or strip AVB footers, or modify stock vbmeta/chained vbmeta images. Do not assume a modern `vendor_boot`/`init_boot` layout applies to this header-v2 image.

## 3. Required read-only metadata before packaging

Using only an approved, already-available AVB inspection tool/helper:

1. Determine whether boot.img, ramdisk.img and dtbo.img have AVB footers; record footer original-image-size fields.
2. Enumerate only metadata needed to classify hash/hashtree coverage: descriptor type, target partition, parent vbmeta partition and chain relationship. Do not publish keys, signatures, salts, digests or rollback values.
3. Establish which vbmeta image authenticates each target and whether separate ramdisk/DTBO content is covered directly or through another descriptor.
4. Inventory stock header-v2 fields, page size, kernel/ramdisk/DTB sizes and offsets, command line and board-specific DTBO selection metadata from existing images.
5. Identify first-stage ramdisk content, fstab, module-loading route, root/system partition layout and dm-verity/FEC expectations before deciding which kernel components must be built in.
6. Record the exact reversible packaging plan and preserve original image metadata. Do not produce a candidate package until Phase E's final memory handoff is resolved.

If the trusted AVB tool remains unavailable, retain BLOCKED status. Do not bypass the tool gate.

## 4. Phase F verdict

**BLOCKED / NOT PACKAGED.** No boot image, ramdisk, DTBO or vbmeta file has been generated or modified. The kernel Image build may proceed independently, but it is not a device boot package.


## ROUND62 same-device boot-chain cross-reference (not HOS4.3 proof)

The primary report `kernel-baseline/round62/round62_same_device_abl_bootv2_ramdisk_dtbo_reference.md` reviews public DBY-W09 Linux source pinned at `116cb1fe06110543ce03217e8bd8f35c12ca89c3`. It reports Huawei ABL consuming a header-v2 `boot` image plus a separate `ramdisk` partition, and that `fastboot boot` was refused on that project's tested setup. It also documents a required ABL-selected DTBO fragment that populates `/rootparam`.

This raises the risk that a RAM-only first boot may not be available and makes a future write-based boot experiment a separate, high-authorization operation. It is cross-reference only: that public port's own DTS refers to HarmonyOS 4.2, so it does not prove the user's HOS4.3 ABL policy, selected overlay, partition sizes, offsets, AVB footer or RAM map. Do not copy its stock hashes, fixed 96 MiB / 2 MiB sizes, command line, offsets, DTB or AVB data. The reusable method is to inspect and no-op-rebuild the exact local stock header-v2 image before replacing any payload, after local AVB and final-memory evidence are available.

**Packaging remains BLOCKED and no image is generated.** Do not assume `fastboot boot` works, and do not write boot/ramdisk/DTBO/vbmeta without a separate explicit reviewed authorization and a verified rollback path.
