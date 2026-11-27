# AI1 Android 17 boot-package tooling — PREP02

**Date:** 2026-11-27  
**Owner:** 1号 AI (ChatGPT)  
**Target:** DBY-W09 Android 17 / ACK 6.18.33 kernel bring-up first, then DerpFest Android 17.  
**Reference only:** HOS 4.3.0.196(C00E100). This is not a HarmonyOS port.

## What AI1 has made directly

The host-only package toolkit is available as:
- Archive: `Android17_Boot_Package_Tools_PREP02.zip`
- SHA-256: `e698f2bd873ec3ca047dcefe84535012e88857e6739c7031cb908c47024a40ea`

It includes:
- Android boot-image header v0-v2 parser and v2 unsigned payload packer.
- Page-aligned payload/original-image boundary calculation and AOSP boot image ID recomputation.
- DBY-W09 three-FDT DTB-slot composer: candidate Kona v2.1 FDT + stock Kona v2/v1 fallback FDTs + original 173-byte tail.
- First-stage fstab presence check at `/firmware/android/fstab`; warns if absent from candidate FDT.
- Header-v0 separate ramdisk wrapper builder.
- Deterministic root-owned CPIO newc + gzip archive creator from an Android 17 ramdisk source tree (does not invent init/fstab contents).
- Gzip decompression with a 128 MiB cap and CPIO newc/crc inventory parser.
- AVB footer metadata inspection only; no signatures or descriptors are forged.
- Frozen ROUND159 442-byte DTBO table/FDT verifier.

## Reconciled device-reference facts

From existing ROUND154/155/64/65 reports (not a fresh parse of unavailable raw local binaries):

- `boot`: 96 MiB partition, Android header v2, page 4096, header_size 1660, kernel 22,264,379 B in the firmware package reference, embedded ramdisk 519,986 B, DTB 1,664,243 B at `0x1f00000`, AVB original-image-size 24,457,216 B.
- Separate `ramdisk`: 2 MiB partition, Android header v0, page 2048, empty kernel, gzip CPIO newc payload 1,322,962 B at offset 2048, page-aligned original-image-size 1,325,056 B, expanded CPIO 2,884,352 B, 17 entries (13 directories, 3 files, trailer).
- ROUND155 live ramdisk hash `4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb` differs from the ROUND64 package reference hash `5c20e4781f701e075ab30d3f8389172435e5591579bb5971f1b29331862fddc0`. Both are 2 MiB but are distinct source copies.
- Stock first-stage fstab is in base FDT `/firmware/android/fstab` (21 children). Candidate FDT presence must be checked; if absent, target Android 17 ramdisk must supply compatible first-stage configuration or the FDT must be deliberately extended.
- Live `/chosen/linux,initrd-start/end` span 1,406,106 B, which is not equal to the separate ramdisk compressed payload or its expanded CPIO. Embedded-vs-separate ramdisk placement remains unresolved.
- Root vbmeta descriptors cover `boot`, `ramdisk` and `dtbo`. Huawei OEM acceptance/signing is not proven; `vbmeta_cust` remains anomalous.

## Verification

- Python compile: PASS.
- Synthetic unit tests: **16/16 PASS**.
- Real frozen ROUND159 DTBO component: **PASS**, 442 B and SHA-256 `f185c13de5f9d2ca8dc2610c4cef33d12db601bfa29bae079fb5827951c1a6cc`.

## What is not claimed

No real Android17 boot or ramdisk payload image has been emitted yet. The actual successful Window B kernel binary, candidate DTB binary, ROUND155 local stock boot/ramdisk bytes, and a target Android 17 ramdisk are not present in this runtime. The exact ABL initrd handoff and AVB/Huawei acceptance are unresolved.

No HOS ramdisk is reused as target content. No AVB footer, vbmeta, Huawei signature, rollback state or security flag is altered. No device command, reboot, temporary boot, partition write or flash occurred.

**Current disposition:** host-side package tooling PREP02 ready; real Android 17 payload assembly remains blocked on exact binaries and the target ramdisk/handoff contract; no device test approval.
