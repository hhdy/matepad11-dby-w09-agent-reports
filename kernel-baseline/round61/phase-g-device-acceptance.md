# ROUND61 Phase G — controlled device boot and Stage-A acceptance

**Date:** 2026-11-25  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Status:** NOT RUN — no device operation or boot authorization is claimed.

## 1. Current boundary

No ACK-derived DBY-W09 kernel has been booted on the tablet. No ADB/fastboot connection, unlock, flash, partition write, reboot, recovery operation or runtime hardware query was performed in this work segment.

Phase G depends on the following earlier gates:

- Phase A: exact-source patch application and source/style checks.
- Phase B: UFS/PHY binding schema validation and negative fixtures.
- Phase C/D: real Kleaf target analysis, final .config validation and full Image compilation.
- Phase E: trusted final memory handoff and PM8150 physical supply-parent evidence before any board DTB is promoted.
- Phase F: stock boot header-v2, separate ramdisk, DTBO and AVB descriptor/coverage metadata before packaging.

A compiled Image is not a boot package. A successful schema check is not a board DTB. A board DTB compile is not proof of correct memory reservations or first-boot safety.

## 2. Acceptance evidence required after explicit authorization

Only after the relevant gates close and the user explicitly authorizes a reversible device test should the operator prepare a device-specific plan with:

1. verified stock backups and recorded hashes for every partition that could be affected;
2. verified bootloader state and a documented non-destructive/reversible boot route, if supported;
3. exact kernel Image and packaging manifest identities;
4. serial/boot-console capture and a rollback route;
5. post-boot evidence for kernel release, UFS host and PHY probe/link initialization, block-device enumeration, required storage partitions mounted, and absence of memory-map or regulator failures;
6. basic agreed hardware acceptance before Stage A is marked complete.

Do not assume `fastboot boot` support or issue a write command before the exact device bootloader capabilities and image format are verified.

## 3. Stage-A completion definition

Stage A is complete only when the tablet actually boots the ACK-derived 6.18.33 kernel and evidence confirms kernel identity, UFS/storage operation and the agreed basic hardware set. Compilation alone is not acceptance. Android 17 DerpFest Stage B remains deferred until this point.

## 4. Phase G verdict

**NOT RUN.** No device operation was attempted or authorized in this work segment.
