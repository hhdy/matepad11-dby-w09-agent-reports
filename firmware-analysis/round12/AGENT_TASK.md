# ROUND12 — HOS4.3 boot / ramdisk / DTBO AVB metadata check (read-only)

## Objective

Before designing any DBY-W09 Android 17 boot/ramdisk/DTBO packaging, determine the existing HOS4.3 AVB footer and vbmeta descriptor coverage for the local stock images:
- boot.img
- ramdisk.img
- dtbo.img
- root vbmeta.img and only the chained vbmeta images needed to identify descriptors for those three partitions.

ROUND2 already reports the file sizes and image header magic. This task must not repeat header/FDT/DTBO parsing or re-extract firmware. It only checks the AVB metadata boundary that ROUND2 did not report.

## Safety and tool gate

1. Use only an already-installed, trusted AVB inspection tool (for example, an existing reviewed avbtool) or an already-reviewed read-only helper.
2. First check whether the trusted tool is already present. If it is absent, report BLOCKED and stop. Do not install/download tools, do not run WSL, do not write a parser, do not execute unknown EXE/DLL, and do not change Windows execution policy.
3. Do not use fastboot or ADB; do not connect to the tablet; do not unlock/root/flash/write partitions; do not mount writable filesystems; do not compile.
4. Work only from existing HOS4.3 local image copies. No firmware re-extraction and no source-image modification.
5. Do not upload boot/ramdisk/DTBO/vbmeta binaries, full local paths, full local SHA256, keys, signatures, salts, descriptor digests, rollback values, serial/MAC/IMEI or tokens.

## Requested checks

For boot.img, ramdisk.img and dtbo.img:
- confirm the already-known total file size;
- determine whether an AVB footer is present at the partition-image end;
- if trusted avbtool is already available, obtain the footer original-image-size value without publishing signatures/digests/salts;
- classify whether the image is a standalone AVB footer image, appears to be covered through a vbmeta hash/hashtree descriptor, or cannot be determined.

For root/chained vbmeta images:
- use read-only metadata listing only;
- identify which vbmeta image lists hash/hashtree descriptors for boot, ramdisk or dtbo, and whether descriptor chains point into other vbmeta partitions;
- report only descriptor type, target partition name and parent vbmeta image role/name;
- suppress public key material, digests, salts, signatures, rollback-index values and all full hashes.

If avbtool is not installed or any needed information cannot be obtained with an already approved tool, mark that subitem BLOCKED / UNKNOWN. Do not approximate.

## Required result

Commit one short sanitized UTF-8 text report under firmware-analysis/round12/ on branch firmware-audit-v1. Mark every item COMPLETE / BLOCKED / UNKNOWN / NOT_RUN. Do not commit binaries or modify the existing ROUND2–ROUND11 reports.

## Stop condition

After uploading the text report to firmware-audit-v1, stop. Do not update main, ACK DTS draft branch or PR #1.
