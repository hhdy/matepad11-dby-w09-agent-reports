# ROUND71 — same-device Linux packaging reference versus HOS4.3 boot / AVB facts

Date: 2026-11-25
Owner: Primary AI, read-only public source comparison
Scope: public same-device Linux packaging scripts versus the user's local HOS4.3 ROUND19/20/64 facts. No boot image created, no device operation.

## 1. Executive result

The public same-device Linux 7.0 project provides useful structural confirmation:
- Huawei ABL uses boot header v2;
- kernel is supplied as compressed Image.gz;
- ramdisk is loaded from the separate ramdisk partition;
- one minimal rootparam-only DTBO is packaged;
- the project README says fastboot RAM boot is refused and its testing path writes boot/ramdisk/dtbo partitions.

But its packaging scripts contain version-specific constants and a development strategy that must NOT be copied blindly:
- repack_boot.py hardcodes STOCK_PAYLOAD_SIZE = 24,412,160 bytes and a specific stock boot SHA-256.
- HOS4.3 ROUND19/20 measured boot-v2 payload_end / AVB original_image_size = 24,457,216 bytes, 45,056 bytes larger.
- The public repack script preserves the original AVB footer bytes by overwriting the payload region; it does not recalculate the AVB hash descriptor or regenerate a signature.
- Its ramdisk builder also lays a new v0 ramdisk payload over the stock ramdisk partition and preserves the footer bytes; it does not create a new AVB signature.
- ROUND64 shows the user's HOS4.3 root vbmeta has chain links / descriptors covering boot, standalone ramdisk and dtbo. Reusing the stock footer and chain metadata after payload changes is therefore not cryptographic validation.

The scripts prove a packaging technique used by that public project, not its AVB acceptance mechanism or compatibility with the user's exact HOS4.3 build. Do not copy its sizes, hashes, footer-preservation strategy, or assume that one-entry DTBO id=0 will be accepted by HOS4.3 ABL.

## 2. Public same-device reference facts

Repository: https://github.com/svesnav/linux-dby-w09

Relevant files:
- README.md: https://github.com/svesnav/linux-dby-w09/blob/main/README.md
- repack_boot.py: https://github.com/svesnav/linux-dby-w09/blob/main/repack_boot.py
- build_dev_images.sh: https://github.com/svesnav/linux-dby-w09/blob/main/build_dev_images.sh
- pack_dtbo.py: https://github.com/svesnav/linux-dby-w09/blob/main/pack_dtbo.py
- install_images.py: https://github.com/svesnav/linux-dby-w09/blob/main/install_images.py

Observed behavior:
- README states Huawei ABL boots Android boot header v2 and loads ramdisk from the separate ramdisk partition.
- README states the applied DTBO must fill /rootparam like stock overlay 8; another DTBO leads to fastboot.
- README states fastboot boot (RAM boot) is refused. Its development path tests by writing partitions.
- build_dev_images.sh produces a boot-v2 image with Image.gz and DTB, a separate header-v0 ramdisk image, and a one-entry DTBO image.
- pack_dtbo.py writes a table with page_size 4096, version 0, one entry and id=0/rev=0. The overlay root itself carries qcom,board-id=<0x206a 0>.
- repack_boot.py unpacks/recreates boot header v2 using AOSP mkbootimg, optionally overlays the new payload into the original 96 MiB boot partition while retaining the footer bytes.
- build_dev_images.sh similarly overlays a new header-v0 ramdisk payload into the original 2 MiB ramdisk partition and retains footer bytes.
- install_images.py is a privileged partition writer with backup/readback; it is not part of this project's authorized workflow and must not be executed.

The public README describes that tree as Linux 7.0. The already-recorded project handoff says its board DTS is based on HOS4.2, not this user's HOS4.3 firmware. Use it as structural reference only.

## 3. Concrete version mismatch: stock boot payload size

Public repack_boot.py:
- STOCK_PAYLOAD_SIZE = 24,412,160 bytes.
- Requires a particular stock boot backup SHA-256.
- Requires the full partition to be 96 MiB.

User HOS4.3 reports:
- ROUND19 / ROUND20 Android header-v2 embedded payload_end = 24,457,216 bytes.
- ROUND64 avbtool info_image confirms boot footer original_image_size = 24,457,216 bytes.
- The HOS4.3 ramdisk partition footer original_image_size = 1,325,056 bytes.
- The HOS4.3 dtbo original_image_size = 2,963,810 bytes.

The public boot payload constant is 45,056 bytes smaller than the HOS4.3 value. It belongs to a different stock image backup and cannot be used for the current build. Any future packer must parse the actual HOS4.3 boot header/footer from the actual local backup rather than hard-code public project values.

## 4. AVB boundary

The public scripts preserve stock footer bytes after changing boot/ramdisk payloads. That is not the same as recomputing a hash descriptor, creating a valid vbmeta chain, signing the modified image with an authorized key, or proving the HOS4.3 ABL accepts it.

ROUND64 for the user's firmware confirms root vbmeta chain targets for boot/ramdisk/dtbo and corresponding hash descriptors. Any payload modification changes the bytes to which the original descriptor applies. The public scripts do not show an AVB signing step in the reviewed packaging path.

The actual HOS4.3 boot acceptance policy remains UNKNOWN. It may differ by bootloader lock state, secure boot policy, verified-boot configuration and vendor loader behavior. No assumption of unlocked-device tolerance or AVB bypass is permitted.

Do not copy the public hard-coded stock SHA/size; treat a physically preserved footer as a valid signature; use the public privileged install_images.py; flash, unlock, root or test via fastboot RAM boot; or create a candidate package until the user's HOS4.3 ABL and AVB acceptance path are established.

## 5. Combined structural picture for this project

The best evidence-backed structure for the next build design is:
- Android boot header v2 boot image;
- gzip compressed ARM64 Image (stock HOS4.3 uses gzip; whether raw is accepted remains unknown);
- base board DTB embedded in boot;
- separate ramdisk partition (header v0, kernel_size=0, per ROUND19);
- separate DTBO partition with DT table metadata, the exact HOS4.3 rootparam/ABL acceptance contract still UNKNOWN.

The base DTB / rootparam overlay and one-entry DTBO packaging are separate layers. The main rootparam candidate's qcom,board-id 0x206a is an overlay root property; it does not by itself prove the table entry ID must also be 0x206a. Public same-device packaging uses entry id=0; HOS4.3 stock table entry 8 uses 0x206a. Keep replacement table selection policy UNKNOWN until HOS4.3-specific evidence closes it.

## 6. Status

- Public same-device packaging source inspected: PASS.
- Structural header v2 / separate ramdisk / one rootparam DTBO reference: PASS as cross-reference.
- Exact HOS4.3 boot/ramdisk/dtbo payload sizes: PASS from ROUND19/20/64.
- Public boot payload constants suitable for HOS4.3: NO.
- AVB validity of the public retained-footer strategy on user's HOS4.3: UNKNOWN.
- HOS4.3 ABL fastboot RAM boot behavior: UNKNOWN; do not infer from earlier HOS version.
- New boot package / dtbo.img / AVB signing: NOT RUN.
- Device operations: NOT RUN.

No local firmware, source, build artefact, DTS, branch-protected ref or device was modified.