# ROUND155 — WorkBuddy Window A: read-only boot-chain partition capture

- Executor: WorkBuddy Window A (1号 Agent).
- Window B (2号 Agent) is a separate WorkBuddy chat window. Both are WorkBuddy.
- Device: Huawei MatePad 11 (2021), DBY-W09 / HWDBY / KONA / SM8250.
- Purpose: obtain exact ABL/boot-chain evidence and local rollback backups before any future write.
- This task is read-only. It does not authorize flash, reboot, fastboot, recovery, mount, or any block-device write.

## 1. Why this is the fastest next step

ROUND154 established:
- RAM-only DTS patch builds to a validated DTB;
- stock Entry 2 cannot be applied to the candidate (156 missing external labels, 87 missing fragment targets even with -@);
- the stock boot-v2 image has three concatenated FDTs;
- exact ABL/XBL selector contract is unknown;
- AVB is only partially understood, and full backups / tested restore are absent.

The exact on-device ABL plus local boot-chain partition copies can settle several blockers at once. Do not repeat RAM or UFS census.

## 2. Allowed operations

- Use the existing ADB connection and root method already verified in ROUND151.
- Read directory metadata and symlink targets under the actual by-name directory.
- Read-only blockdev --getsize64, readlink -f, stat, dd if=<partition> of=<host-file>, and SHA-256.
- Copy directly from device to the local host; do not stage raw images on tablet storage.
- Run host-side avbtool info_image, verify_image only if a public verification key already exists, strings, and static ABL inspection/disassembly.
- Do not extract signing keys or bypass AVB.

Use a new ROUND155 evidence folder in Window A's own local workspace. Preserve raw binaries locally. Raw firmware/bootloader binaries and raw device images must not be uploaded to GitHub.

## 3. Partition inventory

Locate the actual by-name directory; do not assume its path. Record name, resolved block node and exact byte size for each present target:

- abl / abl_a / abl_b
- xbl / xbl_a / xbl_b
- xbl_config / slot variants
- boot / slot variants
- dtbo / slot variants
- vbmeta, vbmeta_system, vbmeta_vendor, vbmeta_cust and slot variants
- ramdisk / slot variants
- recovery, erecovery and related recovery boot image

Do not read userdata, metadata, persist, frp, devinfo, modem NV, keystore, or other personal/private data partitions. Do not dump the full UFS device.

Resolve aliases: if multiple names point to the same block node, record the alias and read only once.

## 4. Read-only copies and verification

For each present target:

1. Verify the source resolves to a block device.
2. Record blockdev --getsize64 and stat metadata.
3. Read source to a host-side file using a command such as adb exec-out su -c 'dd if=/dev/block/... bs=4M iflag=fullblock status=none' piped to local storage. The remote dd command must have no of= argument.
4. Confirm bytes received exactly equal partition size.
5. Compute host SHA-256. Independently compute a device-side streaming SHA-256 in a separate read pass; compare.
6. Keep two local copies on separate host storage locations where available for boot, dtbo, all present root/child vbmeta, recovery and erecovery. If a second storage location is unavailable, record it.
7. Read each local copy back and recompute SHA-256 before calling it verified.

If root access fails, a read errors, capacity changes, hashes differ or safe host storage is unavailable, stop. Do not try a state-changing workaround. Do not remount anything.

## 5. ABL/XBL analysis

Use only exact copied binaries:
- identify ELF/MBN/Qualcomm wrapper, segment layout and entry addresses where decodable;
- hash every copy;
- inspect strings, symbols and disassembly;
- trace FDT memory fixups, board-id input, DTBO table selection, msm-id selection and use of boot-v2 dtb_size/dtb_addr;
- grade direct code/disassembly separately from strings and hypotheses;
- do not claim a selector or RAM-mutation path without a code path.

If symbols are stripped, record limitations and only defensible conclusions.

## 6. AVB/package implications

Run read-only avbtool info_image on copies of boot/DTBO/vbmeta images. Record vbmeta chains, partition descriptors, algorithm, public-key digest, rollback index/location, original image size and footer location. Recheck whether the vbmeta_cust anomaly also exists in the live partition copy. Do not disable verification, resign, patch vbmeta or modify any image.

## 7. Deliverable

Publish only the sanitized report:
firmware-analysis/round155/WORKBUDDY_A_ROUND155_READONLY_BOOTCHAIN_PARTITION_CAPTURE_REPORT.md

Raw binaries, full host paths, private logs, serial/IMEI/MAC/panel IDs and user data remain local. Report only partition name, size, technical metadata, hashes and sanitized findings. Read back the uploaded report and verify the blob/content, then STOP.

## 8. Prohibitions

- No flash, write, erase, format, reboot, fastboot, recovery entry, temporary boot or bootloader unlock/lock.
- No dd of=/dev/block/*, flash_image, fastboot flash/erase, applypatch, or app/module installation.
- No personal-data partition reads.
- No ADB root remount, SELinux change, kernel parameter change, mount/unmount or property write.
- No access to Window B's workspace.

— END —