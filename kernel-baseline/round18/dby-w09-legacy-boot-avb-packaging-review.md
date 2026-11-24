# ROUND18 — DBY-W09 legacy boot / ramdisk / DTBO packaging review

Date: 2026-11-24

Status: public same-device source review and existing local report comparison. No images were rebuilt, extracted, modified, packaged, flashed or written. HOS4.3 AVB footer / vbmeta descriptor coverage remains pending ROUND12.

## 1. New same-device boot-flow reference

The public svesnav/linux-dby-w09 repository documents the DBY-W09 boot flow:
- Huawei ABL boots a header-v2 boot image.
- The actual ramdisk used by this Linux port is loaded from a separate ramdisk partition.
- The minimal DTBO entry must populate /rootparam; the README says ABL rejects an entry that does not fill this identity node.
- The same project reports that fastboot boot (RAM boot) is refused, so its tests are performed by writing boot partitions.
- Its Linux installer builds the boot, ramdisk and DTBO partition payloads from stock partition copies and local kernel/DTB artifacts.

Primary source:
https://github.com/svesnav/linux-dby-w09

Supporting source files:
- README boot flow / release bundle: https://github.com/svesnav/linux-dby-w09/blob/main/README.md
- boot image repacking: https://github.com/svesnav/linux-dby-w09/blob/main/repack_boot.py
- partition image creation: https://github.com/svesnav/linux-dby-w09/blob/main/build_dev_images.sh
- release bundle construction: https://github.com/svesnav/linux-dby-w09/blob/main/build_release.sh
- installer-side boot/ramdisk assembly: https://github.com/svesnav/linux-dby-w09/blob/main/deb/matepad-kernel-install
- one-entry DTBO table builder: https://github.com/svesnav/linux-dby-w09/blob/main/pack_dtbo.py

This is a valuable same-model implementation reference. It is a Linux 7.0 port and does not prove that an Android 17 DerpFest ramdisk or newly packed images will boot on the user's HOS4.3 ABL.

## 2. Comparison with the user's existing HOS4.3 image inventory

ROUND2 local report records:
- boot.img file size 100,663,296 bytes (96 MiB), header version 2, kernel 22,264,379 bytes, embedded ramdisk 519,986 bytes, page size 4096, DTB 1,664,243 bytes.
- ramdisk.img file size 2,097,152 bytes (2 MiB), header v0, kernel size zero, ramdisk payload 1,322,962 bytes, page size 2048.
- dtbo.img file size 25,165,824 bytes (24 MiB), table version 0, nine entries.
- vbmeta images exist (root and chained names), but ROUND2 only identified AVB_VBMETA image magic; it did not enumerate descriptors or footer coverage.

The public same-device Linux project expects the same total file sizes for stock boot (96 MiB) and ramdisk (2 MiB). The same user ROUND2 inventory also reports a 24 MiB DTBO partition, matching the public board family context. ROUND2 further records that all nine stock DTBO table entries have id=0 and rev=0; the public same-device one-entry packer also writes zero id/rev/custom fields. This corroborates the table-entry metadata convention, but it does not prove ABL accepts the new overlay, table total-size/alignment, or AVB coverage.

This size match is corroborating evidence for the partition envelope, not proof of AVB descriptor content, ABL policy or Android ramdisk compatibility.

## 3. What the public packer actually does

### 3.1 Boot partition

The same-device repack flow uses a stock header-v2 boot image and an AOSP mkbootimg unpack/repack path:
- requires header version 2;
- extracts the original boot header arguments and embedded ramdisk;
- replaces the compressed kernel, DTB and command line;
- preserves the stock embedded ramdisk, second stage and recovery_dtbo data from the extracted boot image;
- regenerates the boot header/image ID using the new payloads.

Its separate installer-side function performs the same high-level transformation by reading the stock header-v2 fields and repacking a new payload.

Do not copy the public script's stock image hash, path assumptions, WSL workflow or exact constants into this project. Its stock image identity check is specific to that project's own HOS dump. The user also has an explicit no-WSL / no-device-write boundary.

### 3.2 Separate ramdisk partition

The public Linux port creates a header-v0 ramdisk payload with an empty kernel and a Linux initramfs. Its installer overlays that payload onto the beginning of the stock 2 MiB ramdisk partition, pads the area up to the original image-size boundary, and preserves the AVB footer and remaining bytes.

This is a packaging method for that Linux SD-root initramfs. It is not an Android 17 ramdisk recipe and must not be copied as the target DerpFest ramdisk contents. It does establish that the separate ramdisk partition must be treated independently from the boot.img embedded ramdisk.

### 3.3 DTBO partition

The public project builds one-entry DTBO table around its minimal /rootparam overlay. Its packer writes a standard v0 DT table header and one 32-byte entry; the table-entry id/rev/custom fields are zero while the embedded overlay root carries qcom,board-id = <0x206a 0>.

This is an observed public implementation detail, not a complete explanation of Huawei ABL's DTBO matching rules. The current ACK minimal overlay remains a .draft and ABL acceptance remains UNKNOWN / NOT_TESTED. Do not treat the one-entry packing method as verified until the HOS4.3 AVB/DTBO and ABL metadata boundary is reviewed.

## 4. AVB is the remaining packaging gate

The public project explicitly handles an AVB footer on the separate ramdisk partition, but its code does not establish the user's HOS4.3 descriptor/chain state. The local ROUND2 report:
- gives the total boot/ramdisk/DTBO image file sizes;
- identifies vbmeta image magic;
- does not report AVB footer presence at the end of boot.img, ramdisk.img or dtbo.img;
- does not map root/chained vbmeta descriptors to these partitions;
- does not record whether verification is disabled, enforcing, chained or otherwise configured.

Therefore it is premature to write a HOS4.3-safe boot/ramdisk/DTBO packer or to reuse the public ramdisk overlay method without a descriptor-level check.

ROUND12 requests a narrowly scoped, read-only local AVB metadata check. It must only use an already-installed trusted avbtool or an already-reviewed read-only helper; no tool install, WSL, parser implementation or image write is allowed. If no suitable tool is already installed, report BLOCKED and stop.

## 5. Target Android 17 port consequences

The storage-first ACK board source remains a source draft only:
- boot.img output will need to follow the HOS4.3 header-v2 ABL structure, not a modern GKI v3/v4 vendor_boot/init_boot recipe;
- the stock boot header/embedded ramdisk preservation strategy must be established from trusted source before any future packaging;
- the separate ramdisk partition needs a distinct Android 17 first-stage/initramfs design, not the public Linux SD-root initramfs;
- minimal /rootparam DTBO must satisfy ABL selection and identity requirements; stock entry 8's 145 vendor fragments must not be copied to the minimal ACK DTS;
- the exact AVB footer and vbmeta descriptor chain must be understood before any modified partition image can be considered safe.

The public Linux 7.0 port's README says fastboot boot is refused. Thus an eventual runtime test may require a partition-write path; however the current project boundary forbids all writes and no such test is authorized.

## 6. Verification state

| Item | Status |
|---|---|
| Same-device public header-v2 + separate-ramdisk boot flow | SOURCE REVIEWED |
| Same-device public boot repacker behavior | SOURCE REVIEWED |
| Same-device public separate ramdisk + AVB footer handling | SOURCE REVIEWED |
| User ROUND2 boot/ramdisk/DTBO file sizes | EXISTING LOCAL REPORT REVIEWED |
| ROUND2 stock DTBO entry id/rev fields | ALL NINE = 0/0; PUBLIC PACKER ALSO USES ZERO ENTRY FIELDS |
| HOS4.3 boot.img AVB footer | UNKNOWN / ROUND12 |
| HOS4.3 ramdisk.img AVB footer and original image size | UNKNOWN / ROUND12 |
| HOS4.3 dtbo.img AVB footer | UNKNOWN / ROUND12 |
| vbmeta descriptor coverage for boot/ramdisk/dtbo | UNKNOWN / ROUND12 |
| HOS4.3 /memory / live ABL memory injection into a replacement DTB | NOT_ESTABLISHED; base FDT inventory has no /memory node |
| HOS4.3 reserved-memory handoff / exact region recreation in ACK | NOT_ESTABLISHED; 34 local child nodes, values redacted |
| ABL accepts the newly built minimal ACK DTBO | UNKNOWN / NOT_TESTED |
| Android 17 ramdisk/fstab/module ordering | BLOCKED (ROUND10) |
| DTS / DTBO compile, Kconfig resolution, kernel build | NOT_RUN |
| Any partition write / fastboot / device boot | NO |

## 7. Android first-stage compatibility and module-loading boundary

AOSP first-stage init loads eligible kernel modules from /lib/modules before it performs first-stage device creation and partition mounting. It selects a module directory matching the running kernel release and page-size suffix, reads modules.dep / soft dependencies and a mode-specific modules.load list, and then proceeds to first-stage mount. The official Android module-support guide documents these files and their role.

However, the published Android documentation's standard layout puts vendor modules in vendor ramdisk (vendor_boot), while this DBY-W09 layout has legacy header-v2 boot plus a separate ramdisk partition. It is not yet proven that the HOS4.3 ABL-combined first-stage initramfs exposes the same /lib/modules tree in a way compatible with DerpFest Android 17. ROUND10 ramdisk contents are BLOCKED. Therefore UFS/QMP modules remain built-in in the first storage-first plan until this path is established; this is conservative, not a hard Android requirement.

AOSP first-stage mount sees logical fstab entries, initializes device-mapper, reads LP metadata from super, and creates dm-linear logical devices. In this ACK kernel, dm-linear is part of dm-mod; there is no CONFIG_DM_LINEAR Kconfig option. The local HOS4.3 vendor/odm EROFS signatures justify EROFS_FS=y. DM_VERITY / FEC still depend on ROUND12 AVB metadata and the actual fstab.

Sources:
- First-stage module support: https://source.android.com/docs/core/architecture/kernel/kernel-module-support
- First-stage init: https://android.googlesource.com/platform/system/core/+/refs/heads/main/init/first_stage_init.cpp
- First-stage logical partition creation: https://github.com/aosp-mirror/platform_system_core/blob/main/init/first_stage_mount.cpp
- ACK dm target composition: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/md/Makefile
- ACK EROFS Kconfig: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/fs/erofs/Kconfig

## 8. Next steps

1. Await ROUND12's read-only AVB footer / vbmeta descriptor report.
2. GPT continues source-side ACK storage-first and Android 17 initramfs / boot integration research; do not copy the Linux SD-root initramfs.
3. Do not repack, sign, flash, boot or write any device image under the current boundary.
