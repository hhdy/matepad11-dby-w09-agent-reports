# ROUND20 — Android 17 first-stage modules, dynamic partitions and EROFS

Date: 2026-11-24

Status: public AOSP / ACK source review, plus integration of existing HOS4.3 ROUND2/ROUND4/ROUND10 evidence. No local firmware extraction, ramdisk inspection, dtc, Kconfig resolution, kernel build, image packing or device operation.

## 1. Correct Android first-stage order

AOSP first-stage init loads eligible kernel modules from /lib/modules before it performs first-stage device creation and partition mounting. The module loader:
- checks the running kernel release (uname -r) and page-size suffix;
- selects a matching release directory under /lib/modules;
- parses modprobe metadata such as modules.dep, aliases and soft dependencies;
- loads the mode-specific list (modules.load, modules.load.recovery, or modules.load.charger);
- then proceeds to first-stage mount / logical-device creation.

The official Android kernel-module support document describes the module and metadata files. Current AOSP first-stage init source implements the version/page-size directory selection and load-list mechanism.

References:
- https://source.android.com/docs/core/architecture/kernel/kernel-module-support
- https://android.googlesource.com/platform/system/core/+/refs/heads/main/init/first_stage_init.cpp

## 2. Important DBY-W09 legacy-layout caveat

The standard Android documentation describes generic/vendor ramdisks, with vendor first-stage modules in vendor_boot. DBY-W09 has a legacy boot header v2 plus a separate ramdisk partition; no standard vendor_boot/init_boot was found in the local inventory.

Therefore the AOSP mechanism proves that Android can load UFS modules before mounting UFS-backed partitions, but it does not prove that the user's HOS4.3 ABL combines the legacy boot embedded ramdisk and separate ramdisk into the exact initramfs layout expected by DerpFest Android 17.

For module-based UFS bring-up, the eventual initramfs must expose:
- /lib/modules/<exact-kernel-release>/ (and matching page-size policy);
- UFS/QMP and all dependencies built against the exact ACK kernel;
- modules.dep, modules.softdep, modules.alias, modules.options as needed;
- modules.load containing the first-stage UFS dependency order.

ROUND10 could not read ramdisk contents, so all of these DBY-W09 facts remain UNKNOWN/BLOCKED. The current first-stage configuration therefore keeps the entire UFS/PHY/clock/regulator/interconnect chain built-in. This is a conservative initial boot strategy, not an Android requirement that UFS drivers must always be built-in.

## 3. Dynamic logical partitions: corrected Kconfig

The local ROUND2 super image analysis identifies the logical partitions carried by the super image. AOSP first-stage mount checks first-stage fstab entries marked logical, initializes the device-mapper control device, reads LP metadata, discovers the backing physical partition devices, and creates logical mappings before mounting them.

ACK android17-6.18 driver composition:
- CONFIG_BLK_DEV_DM=y enables the device-mapper core required by first-stage logical partition creation.
- dm-linear is compiled into dm-mod in drivers/md/Makefile; there is no independent CONFIG_DM_LINEAR Kconfig symbol.

References:
- https://github.com/aosp-mirror/platform_system_core/blob/main/init/first_stage_mount.cpp
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/md/Makefile
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/md/Kconfig

The config fragment now sets CONFIG_BLK_DEV_DM=y and removes the invalid CONFIG_DM_LINEAR line.

## 4. Filesystem Kconfig from local image evidence

ROUND4 confirmed EROFS superblock magic in the HOS4.3 vendor and odm logical partition images. EROFS content extraction remains blocked, but its filesystem type is already known at the image-signature level. First-stage vendor/odm mounts therefore require CONFIG_EROFS_FS=y unless a precisely compatible EROFS module is proven to load from the initramfs; under the present blocked ramdisk state, built-in is the conservative setting.

Other filesystems:
- system, cust and hw_product exact filesystem types remain UNKNOWN;
- CONFIG_EXT4_FS and CONFIG_F2FS_FS remain pending;
- CONFIG_DM_VERITY and optional CONFIG_DM_VERITY_FEC remain pending ROUND12's AVB hashtree descriptor data and first-stage fstab options.

References:
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/fs/erofs/Kconfig
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/md/Kconfig

## 5. Updated storage-first fragment

Branch ack18-dby-w09-dts-draft:
- actively adds CONFIG_BLK_DEV_DM=y;
- actively adds CONFIG_EROFS_FS=y;
- removes non-existent CONFIG_DM_LINEAR;
- keeps CONFIG_DM_VERITY / CONFIG_DM_VERITY_FEC commented pending AVB/fstab;
- keeps EXT4/F2FS commented pending actual filesystem identification;
- keeps UFS/QMP boot dependencies built-in until legacy ABL/initramfs module exposure is verified.

Main:
- ROUND14's candidate list corrected;
- ROUND18's boot flow report extended with the first-stage module and dynamic partition boundary;
- DTS README and AGENT_TASK.md updated.

## 6. Verification status

| Item | Status |
|---|---|
| AOSP first-stage module path and load-list mechanism | SOURCE REVIEWED |
| Exact HOS4.3 /lib/modules contents / kernel release directory | UNKNOWN (ROUND10 ramdisk BLOCKED) |
| Legacy ABL concatenation/exposure of separate ramdisk to Android first-stage init | UNKNOWN |
| UFS/QMP module compatibility and load order | NOT_ESTABLISHED |
| HOS4.3 dynamic logical partitions in super | EXISTING ROUND2 REPORT REVIEWED |
| BLK_DEV_DM required for first-stage dm-linear mapping | SOURCE REVIEWED |
| Independent CONFIG_DM_LINEAR Kconfig symbol | DOES NOT EXIST |
| HOS4.3 vendor/odm EROFS signatures | CONFIRMED ROUND4 |
| EROFS_FS=y included in storage-first fragment | UPDATED |
| system/cust/hw_product filesystem types | UNKNOWN |
| AVB hashtree/FEC descriptor and fstab requirements | WAITING ROUND12 |
| Kconfig olddefconfig resolution / build | NOT_RUN |
| DTB / boot packaging / device boot | NOT_RUN |

## 7. Next steps

1. Continue public ACK source review and source-draft refinement.
2. Wait for ROUND12 AVB metadata report before selecting DM_VERITY/FEC and deciding how partition images may be repacked.
3. Keep memory/reserved-memory handoff (ROUND19) as a mandatory pre-DTB-build gate.
4. Do not read/reparse the ramdisk again unless an already-trusted, approved tool path is established; do not install tools or use WSL.
5. Keep all files suffixed .draft; keep PR #1 Draft; no flash, unlock, root, device connection or writes.
