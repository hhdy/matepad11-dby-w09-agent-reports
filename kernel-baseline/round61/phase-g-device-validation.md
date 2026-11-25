# ROUND61 Phase G — controlled device validation plan

**Owner:** Second AI  
**Date:** 2026-11-25  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Device:** Huawei MatePad 11 (2021), DBY-W09  
**Status:** NOT RUN — no device session, bootloader operation, reboot, temporary boot or partition write has been authorized or performed.

## 1. Entry gates — all must pass before a boot attempt

Phase G is downstream of the source/build and packaging work. Do not attempt device validation until all of the following are reviewed and evidenced:

1. **Phase D:** exact ACK source/manifest revisions, ordered source diff, final .config validator output, Image SHA-256 and size, plus successful build log.
2. **Phase E:** a real board DTS/DTB built from the proven HOS4.3 final ABL-to-Linux memory handoff (or verified EFI memory-map path) and a source-backed PM8150 power-input topology. New DTS/DTB must pass pinned-kernel `dtc` and relevant `dtbs_check` / `dt_binding_check`.
3. **Phase F:** exact header-v2 boot / separate ramdisk / DTBO composition and AVB footer/vbmeta descriptor coverage must be inspected with a trusted approved tool. No guessed mkbootimg arguments, metadata offsets or AVB changes.
4. **Boot-path feasibility:** the actual HOS4.3 ABL behavior must be established. ROUND62 is only a HOS4.2 cross-reference and warns that `fastboot boot` may be refused on the tested setup; do not assume a RAM-only boot works.
5. **Recovery:** a validated original HOS4.3 boot path and exact rollback payload identities/checksums must be available. A generic fastboot recovery assumption is not enough.
6. **Explicit authorization:** the user must separately approve the exact proposed operation after reviewing the artifact hashes, safety analysis, command list and rollback path. Any persistent partition write/flash requires its own explicit approval; it is not implied by permission for a temporary test.

Until these entry gates close, Phase G remains NOT RUN.

## 2. Pre-boot review packet

Before requesting approval, provide one immutable packet containing:
- exact ACK tag and commit;
- pinned Repo manifest commit and XML SHA-256;
- full ordered patch list and applied-diff SHA-256;
- final .config plus validator output and SHA-256;
- Image, DTB, DTBO and boot/ramdisk candidate identities, sizes and SHA-256;
- AVB footer and descriptor classification (without publishing keys/signatures/salts/digests or rollback values);
- verified image header-v2 fields, page size, payload sizes/offsets and DTBO selection metadata;
- exact boot method and why Huawei ABL accepts it;
- original firmware/partition preservation details and tested recovery/rollback method;
- exact proposed commands, classifying each as read-only, temporary execution or persistent write;
- expected outputs and the earliest failure evidence to capture.

If any one of these values is unknown, do not create the boot candidate or ask the user to run an incomplete command sequence.

## 3. First-boot evidence checklist

Only after the approved entry packet and operation authorization exist, collect evidence in this order. Prefer read-only collection and do not remount writable or alter verified boot policy.

### Kernel identity
- `uname -a` and `uname -r`;
- exact kernel build string / UTS version;
- confirm it is the ACK 6.18.33-derived kernel built from the reviewed commit, not the stock kernel.

### Memory and early platform
- earliest available kernel log from entry onward;
- RAM memory map, chosen usable-memory range, and each reserved-memory node as consumed by the kernel;
- confirm no overlap among RAM, kernel image, initramfs, DTB, secure firmware, DSP and reusable carveouts;
- clock, reset, RPMh, regulator and power-domain probe results;
- QMP UFS PHY and UFS Host initialization sequence, including the retained `vdda-phy` state and load-vote behavior.

### Storage and first-stage mount
- UFS link startup and Host/controller identity;
- block device enumeration and expected device/partition names;
- read-only identity checks for expected super/dynamic partition metadata;
- first-stage mount results for vendor/odm and required system partitions;
- dm-verity / FEC state consistent with the validated stock fstab and AVB descriptors;
- no filesystem repair, writable mount, or partition modification as part of first boot.

### Agreed basic hardware
- display/backlight and touch/input function;
- audio / USB / Wi-Fi / Bluetooth only where the validated board source actually enables those devices;
- suspend/resume and one cold/warm restart only where separately reviewed as safe and feasible;
- capture dmesg and userspace logs after each milestone, and stop at the first critical power/storage/memory error.

Do not interpret a working display alone or a successful boot animation as Stage-A acceptance.

## 4. Stop conditions

Immediately stop the experiment and preserve logs if:
- RAM map or reserved-memory ranges differ from the reviewed handoff;
- UFS Host/PHY, regulator, clock, GenPD or RPMh probe fails;
- storage enumerates inconsistently, reports I/O errors, or expected partitions do not match;
- first-stage mounts or dm-verity fail;
- AVB / bootloader reports verification errors;
- unexpected thermal, power, reset, display or input instability appears.

Do not try alternative DTBs, disable AVB, unlock the bootloader, flash a different partition, or repeat a failed boot using guessed offsets. Return to source/packaging diagnosis and re-submit a revised pre-boot review packet.

## 5. Evidence required for Stage-A device acceptance

The final record must link:
- successful exact kernel identity;
- memory/reserved-memory handoff match;
- UFS link and block enumeration;
- read-only storage/first-stage mount verification;
- agreed minimum hardware checks;
- complete logs and timestamps;
- the operation actually authorized and performed, including whether it was temporary or persistent;
- proof that the original HOS4.3 boot path and recovery route remain available.

Only after the above evidence is reviewed may Phase G be marked PASS. The overall Stage A mission remains incomplete until both this device gate and the earlier source/build/board/AVB gates are closed.

## 6. Current verdict

**PHASE G: NOT RUN.** No ADB/fastboot session, bootloader unlock, temporary boot, reboot, partition write, flash, mount-state change or hardware test has been performed. The plan is prepared for a later separately reviewed operation; it is not authorization to execute one.
