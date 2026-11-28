# K1 DBY-W09 Direct ABL Partition Adaptation — AI2 Report

Scope: read-only source and prior offline evidence review. Target: DBY-W09 VD, HOS4.3.0.196(C00E100), ACK android17-6.18.33_r00.

- Device connected: NO
- ADB/fastboot/recovery/device commands: NOT RUN
- Source edits/build/image construction/partition writes: NOT PERFORMED

## Executive decision

DIRECT_ABL_ACK_ANDROID = FEASIBLE_WITH_IMAGE_ADAPTATION (architecture/design hypothesis only; not boot-validated and not authorized for image construction or device use).

The public svesnav project documents Huawei ABL loading boot-v2 plus a separate ramdisk and DTBO. Its implementation is for mainline Linux 7.0.14 with a microSD ext4 root and a custom Linux initramfs. It is not an Android adaptation. Android must preserve Huawei's Android first-stage environment and satisfy the exact target ABL kernel-loader contract.

The decisive unresolved item is physical alignment for ACK Image. The taskbook reports text_offset=0, image_size=45,547,520, flags=0xA, magic=0x644D5241. The reviewed inputs do not establish the exact HOS4.3 ABL raw/gzip branch, decompression destination or runtime allocation residue modulo 0x200000. Compression alone does not solve alignment.

## Final fields

| Field | Finding |
|---|---|
| SVESNAV_REFERENCE_IDENTITY | PASS — all 12 pinned source blob SHAs match |
| ABL_FASTBOOT_BOOT_REFUSAL | REPORTED for public project; exact HOS4.3 UNKNOWN |
| STOCK_BOOT_V2_REPACK_METHOD | CONFIRMED in source; target-specific compatibility PARTIAL |
| SVE_KERNEL_PAYLOAD_FORMAT | IMAGE_GZ |
| SVE_UNCOMPRESSED_TEXT_OFFSET | UNKNOWN |
| ABL_GZIP_KERNEL_DEST_OFFSET | UNKNOWN |
| PREP10_RAW_ALIGNMENT | UNKNOWN |
| ACK_IMAGE_GZ_ALIGNMENT | UNKNOWN |
| ACK_SOURCE_ADAPTATION_NEEDED | UNKNOWN |
| ANDROID_RAMDISK_POLICY | KEEP_STOCK |
| VD_DTBO_POLICY | KEEP_STOCK_VD_ENTRY2 (preserve live stock partition; no VG transplant) |
| BOOT_PARTITION_SIZE_CHECK | PASS arithmetically for reported PREP10 payload vs 96 MiB; ABL acceptance not implied |
| SEPARATE_RAMDISK_AVB_FOOTER | VERIFIED by prior report as footer/layout; exact boundary not re-read here |
| WRITE_READBACK_ROLLBACK_PLAN | PARTIAL |
| DIRECT_ABL_ACK_ANDROID | FEASIBLE_WITH_IMAGE_ADAPTATION |
| RECOMMENDED_NEXT_STEP | Obtain exact-HOS4.3 ABL loader trace for raw/gzip dispatch, destination and allocator residue |
| DEVICE_WRITE_PERFORMED | NO |
| DEVICE_CONNECTED | NO |

## Findings

1. All 12 pinned svesnav source identities match: README, repack_boot.py, build_dev_images.sh, configure-and-build.sh, install_images.py, matepad-kernel-install, boot-cmdline.txt, pack_dtbo.py, dby-w09-rootparam.dtso, build_release.sh, sd_root_init.sh and KERNEL_VERSION.
2. The Linux flow replaces boot-v2 kernel/DTB, creates a Linux SD-root initramfs, overlays a header-v0 ramdisk payload onto the separate ramdisk partition preserving the reported AVB footer region, and creates a one-entry DTBO table. Linux cmdline includes rdinit=/init; it is not an Android first-stage init command line.
3. repack_boot.py checks fixed stock SHA 6fb82f6ca823c8acffaece13b161eca6c685a6e26f2c216b50293c3fd5da539d, which differs from target live stock boot SHA 7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8. Do not apply the public hash guard to this target.
4. STOCK_PAYLOAD_SIZE=24,412,160 is a script-defined payload boundary, not the 96 MiB partition size. --full-partition copies the stock partition, overlays the payload, zeroes to that boundary, and leaves the tail unchanged. It does not independently verify the AVB footer.
5. Both public installer paths back up full selected partitions, but readback hashes only the written image-length prefix. On mismatch they stop and direct manual restoration; no automatic rollback is implemented.
6. Target live DTBO selection is stock Entry 2 / board-id 0x200e. Public overlay is VG / 0x206a. Do not transplant it. Preserve stock VD Entry 2 pending exact integration approval.
7. Android separate ramdisk is reported to contain Huawei init/init.real and KernelSU files. The Linux SD-root initramfs is incompatible in purpose. KEEP_STOCK is the conservative Android policy; Android 12-to-17 init/fstab/bootconfig compatibility remains open.
8. Prior target evidence reports boot=96 MiB, ramdisk=2 MiB, DTBO=25,165,824 B. Stock hashes: boot 7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8; ramdisk 4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb; DTBO 51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c. These are reused from prior evidence, not raw-image re-read in this task.

## Gate decisions

| Gate | Decision | Reason |
|---|---|---|
| Public reference identity | PASS | 12 frozen blob SHAs match |
| Direct ABL architecture | CONDITIONAL | Same-model flow exists; Linux-only pieces cannot be copied |
| ACK raw/gzip alignment | UNKNOWN | Exact loader branch and allocator residue open |
| Android ramdisk | KEEP_STOCK | Preserve Huawei Android init chain |
| VD DTBO | KEEP_STOCK_VD_ENTRY2 | Public VG overlay incompatible |
| Boot-v2 layout | PARTIAL | Repack source understood; target ABL acceptance not proven |
| AVB | PARTIAL | Footer preservation in Linux ramdisk code; Huawei Android acceptance unknown |
| Partition recovery | NO-GO | Full-chain backup/restore proof incomplete |
| Device write | HARD NO-GO | Explicitly out of scope |

## Next action and stop

Smallest next action: offline exact-HOS4.3 ABL loader trace, scoped only to raw ARM64 Image and gzip handling. Identify dispatch predicate, decompression destination, kernel offset, header fields consumed and runtime ImageBuffer physical residue modulo 0x200000. If residue cannot be established statically, retain UNKNOWN and propose a separately authorized read-only observation plan. Do not edit ACK source or rebuild.

Supporting files: boot_v2_repack_analysis.md, abl_imagegz_alignment_analysis.md, android_ramdisk_and_bootconfig.md, vd_dtbo_policy.md, partition_write_readback_recovery_matrix.csv and evidence_matrix.csv.

Prior evidence:
- ROUND158: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round158-independent-rootparam-bootgate/firmware-analysis/round158/AI2_ROUND158_INDEPENDENT_ROOTPARAM_AND_FASTBOOT_BOOT_GATE_REVIEW_REPORT.md
- ROUND155 ABL capture: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round155-readonly-bootchain-backup/firmware-analysis/round155/WORKBUDDY_A_ROUND155_READONLY_BOOTCHAIN_PARTITION_CAPTURE_REPORT.md
- ROUND155 candidate analysis: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round155-candidate-overlay-minimal-plan/firmware-analysis/round155/WORKBUDDY_B_ROUND155_CANDIDATE_SPECIFIC_DTBO_MINIMAL_OVERLAY_REPORT.md

STOP: research only. No device operation, image creation, build, source modification or partition action.
