# ROUND62 — Same-device ABL / boot-v2 / ramdisk / DTBO reference reconciliation

**Date:** 2026-11-24  
**Owner:** Primary AI  
**Status:** PUBLIC SAME-MODEL CROSS-REFERENCE COMPLETE; HOS4.3 TARGET IMAGE / AVB / ABL DETAILS STILL NOT VERIFIED  
**Device:** Huawei MatePad 11 2021 DBY-W09 / KONA / SM8250  
**Stage:** A — ACK 6.18.33 first

## 1. Purpose

This round examines a current public Linux port for the exact DBY-W09 model to refine the first-boot questions. It does not import its Linux 7.x kernel, board DTS, userspace, rootfs, command line, partition writes or firmware assumptions into this Android/ACK project.

The source repository is pinned for this report to:

- Repository: https://github.com/svesnav/linux-dby-w09
- Branch commit: `116cb1fe06110543ce03217e8bd8f35c12ca89c3`
- Commit date: 2026-11-02
- Kernel version in that repository's `KERNEL_VERSION`: `v7.0.14`

This is a same-device, highly relevant cross-reference, but its README/DTS describe a Linux 7.0 project based on its own firmware observations (and the repository itself notes HarmonyOS 4.2 in the DTS). It is not direct proof of the user's currently installed HOS4.3 ABL behavior. No HOS4.3 local image was read or modified in this round.

## 2. Findings from the public DBY-W09 Linux port

### 2.1 ABL boot image and separate ramdisk

The repository README states that Huawei ABL boots an Android boot header-v2 `boot` image and reads the ramdisk from a separate `ramdisk` partition. It also states that ABL refuses `fastboot boot` RAM boot on the tested setup, so that project's kernel tests use partition images instead.

This is the same general layout already observed in the user's local HOS4.3 inventory:
- boot image header v2;
- separate ramdisk partition;
- no confirmed vendor_boot/init_boot.

The cross-reference increases confidence that we must not assume a modern vendor_boot/init_boot packaging flow or generic fastboot RAM-boot support. It does **not** prove that the exact HOS4.3 ABL build has the same RAM-boot policy or every partition size/offset.

### 2.2 Required /rootparam overlay behavior

The README reports that the ABL-applied DTBO entry must populate `/rootparam` like the stock board overlay; the tested device otherwise returns to fastboot.

The repository's `dby-w09-rootparam.dtso`:
- keeps model/compatible on the overlay root;
- sets root `qcom,board-id = <0x206a 0>`;
- applies a fragment targeting `&rootparam`;
- fills `qcom,boardid`, `qcom,board_name`, `qcom,product_name`, `hardware_version` and `huawei,modem_id`.

This is consistent with the current project principle that DBY-W09 rootparam data must be treated as part of the ABL board-selection contract, not optional decoration. It is a useful structural cross-check for our minimal rootparam overlay draft.

It does not prove that a newly assembled DTBO table is accepted by the user's exact HOS4.3 ABL. Preserve the local firmware-derived board values and selected-entry facts; do not copy the external repository's HOS4.2 assumptions without local confirmation.

### 2.3 How the external project rebuilds the legacy boot partition

Its `repack_boot.py` is a useful reference implementation:
- requires a local stock `boot.img` backup;
- checks a particular stock backup SHA-256 and 96 MiB partition size;
- uses AOSP `unpack_bootimg.py` to derive the mkbootimg arguments from that stock image;
- explicitly requires `--header_version 2`;
- replaces kernel and DTB arguments while preserving the other unpacked metadata;
- can preserve the full stock partition length and footer region;
- its no-kernel reconstruction path checks that the original boot payload can be recreated byte-for-byte.

The important reusable *method* is to derive header/page-size/base/offset/cmdline metadata by unpacking the exact local stock boot image and verify a no-op rebuild before replacing the kernel. The hard-coded SHA, partition size, load offsets and OS fields belong only to that other image and must **not** be copied into this project.

### 2.4 How the external project handles the ramdisk partition and AVB footer

Its `build_dev_images.sh`:
- creates a header-v0 payload with an empty kernel and the new initramfs;
- expects the stock ramdisk partition to be exactly 2 MiB;
- checks for an `AVBf` footer marker at a fixed offset near the end;
- reads the footer's original image size from the footer structure;
- bounds-checks the replacement payload against that original image size;
- replaces the partition payload region and zero-fills the remainder up to the recorded image size, leaving the footer bytes untouched.

This gives us a concrete *inspection question* for HOS4.3: is the user’s ramdisk partition/footer shaped the same way, and does the footer's descriptor relationship still match the partition? The external project's fixed 2 MiB / byte offsets are not proof for our firmware. ROUND12 on this project remains BLOCKED for trusted AVB footer/vbmeta descriptor inspection; do not infer applicability from an `AVBf` magic value alone.

### 2.5 DTBO table construction

Its `pack_dtbo.py` constructs a single-entry Android DT table around a flattened overlay. The external README reports that this entry fills /rootparam and is accepted by its tested ABL.

This is a concrete format lead for future source review, not a ready-to-use DBY-W09 Android boot DTBO. We still need to validate the actual stock DTBO header/version, page size, selected entry metadata, ABL selection logic and HOS4.3 compatibility before producing a candidate.

## 3. Important risk: no proven RAM boot path

The same-device README explicitly reports `fastboot boot` refusal. If this exact restriction also applies to the user's HOS4.3 ABL, then first-boot testing may require writing one or more boot-related partitions rather than using a non-persistent RAM boot.

That materially changes the recovery and authorization bar. This project must not:
- assume `fastboot boot` works;
- treat a temporary boot command as safe without an ABL capability check;
- flash `boot`, `ramdisk`, `dtbo`, `recovery` or `vbmeta` without a separate explicit authorization;
- disable AVB or use another project's prebuilt partition images;
- omit a verifiable original-image backup and readback/rollback design.

A controlled boot plan remains a later user-approved gate, not an automatic consequence of a successful Image build.

## 4. Relationship with current project evidence

| Topic | Our HOS4.3 project evidence | Same-device external cross-reference | Current decision |
|---|---|---|---|
| boot format | local inventory: header v2 | ABL consumes header v2 | Consistent at format level |
| separate ramdisk | local inventory: separate ramdisk | ABL loads separate ramdisk partition | Consistent |
| vendor_boot/init_boot | not found in local inventory | external flow uses boot + ramdisk + dtbo | Continue treating as absent until new local evidence |
| fastboot RAM boot | UNKNOWN locally | external README says refused | High-risk unknown; do not assume available |
| /rootparam | local DTBO/board-id studies | tested overlay must populate /rootparam | Strong structural cross-reference; local HOS4.3 still authoritative |
| AVB footer | ROUND12 BLOCKED | external script preserves a footer by parsing its specific stock ramdisk | Do not borrow offsets or claim AVB closure |
| memory handoff | final HOS4.3 post-ABL FDT UNKNOWN | external DTS states its own map was checked against HOS4.2 | No RAM ranges may be copied |
| board DTS | current file is a review-only draft | external board DTS is for Linux 7.0 | Do not copy whole DTS or enable all Linux features |

## 5. Actions for the primary and second AI

### Primary AI
- Keep the current Stage-A source/build work moving independently of boot packaging.
- When local firmware/approved tooling becomes available, request exact, read-only extraction of the HOS4.3 boot/ramdisk/DTBO/vbmeta metadata and the final post-ABL FDT evidence. This is not a reason to re-scan already completed base-FDT reports.
- Review the rootparam DTBO draft against the local HOS4.3 selected overlay evidence before DTBO packaging.
- Keep a separate decision record for RAM-boot feasibility vs the possibility of partition-write-only testing.

### Second AI — ROUND61
- Read this report as context for Phases E–G.
- Do not allow boot packaging uncertainty to block Phase A–D schema/config/Image build.
- Use the external scripts only to identify what must be measured on the actual stock image; do not copy stock-image hashes, offsets, sizes or command lines.
- Add any packaging-code candidate to its dedicated branch only, and do not make a boot image/flash package until every local source input is verified.

## 6. Exact public source identities

Pinned repository commit: `116cb1fe06110543ce03217e8bd8f35c12ca89c3`.

| File | Git blob | Relevance |
|---|---|---|
| `README.md` | `3f7a18eb8a9ec7cf2917521ba4d694202f5b1200` | ABL boot-v2 + separate ramdisk + rootparam + fastboot boot refusal |
| `sm8250-huawei-dby-w09.dts` | `e56b2abcef38a7a76933ead77dbd941fa63bfb49` | board identity / rootparam / same-device Linux DTS |
| `dby-w09-rootparam.dtso` | `f7f3d5dfc370ecaafdd78cc04274d21735c9eeb1` | ABL rootparam overlay structure |
| `repack_boot.py` | `143c6f4c634a34cd2068ecd3c42cb471b8b832fb` | stock header-v2 unpack/repack/checksum procedure |
| `build_dev_images.sh` | `d1cbb590396f0cbb7bb229ece2fae8ebf12d2dd3` | separate ramdisk partition payload/footer handling |
| `pack_dtbo.py` | `210f27355cf034c7cbe8313e4ca66e73dd4d15bc` | single-entry DT table construction |
| `build_release.sh` | `1d85c6d7ad9e03bf814e955cb887f61fee803258` | blob-free release assembly |

Source URLs:
- https://github.com/svesnav/linux-dby-w09/tree/116cb1fe06110543ce03217e8bd8f35c12ca89c3
- https://github.com/svesnav/linux-dby-w09/blob/116cb1fe06110543ce03217e8bd8f35c12ca89c3/repack_boot.py
- https://github.com/svesnav/linux-dby-w09/blob/116cb1fe06110543ce03217e8bd8f35c12ca89c3/build_dev_images.sh
- https://github.com/svesnav/linux-dby-w09/blob/116cb1fe06110543ce03217e8bd8f35c12ca89c3/dby-w09-rootparam.dtso
- https://github.com/svesnav/linux-dby-w09/blob/116cb1fe06110543ce03217e8bd8f35c12ca89c3/pack_dtbo.py

## 7. What this round did not do

- No user HOS4.3 boot/ramdisk/DTBO/vbmeta image was read.
- No local firmware parser, AVB tool or WSL command was run.
- No kernel patch was applied or compiled.
- No DTB/DTBO/boot/ramdisk image was generated.
- No tablet, ADB, fastboot, recovery, bootloader or partition was accessed.
- No AVB, RAM map, exact ABL boot policy or device write permission was inferred.

**Decision:** the same-device public port provides a strong boot-layout and rootparam cross-reference. It raises a specific risk that ABL RAM boot is unavailable, but that behavior must be verified against the user's current HOS4.3 bootloader before any boot experiment. Keep Stage A source/build phases moving; keep board image and device boot gates closed.
