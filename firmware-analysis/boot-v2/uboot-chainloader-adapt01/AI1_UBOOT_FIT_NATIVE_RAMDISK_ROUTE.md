# AI1 — U-Boot Android ramdisk handoff: FIT-native route decision

- Date: 2026-11-28
- Target: DBY-W09 / HOS4.3 / ACK android17-6.18.33 / U-Boot v2026.10
- Scope: Pinned U-Boot source-control-flow review and FIT design comparison. No device or image operations.

## 1. Decision

If the exact live Android separate ramdisk payload plus compressed ACK Image and ACK DTB fits within the 24 MiB staging budget, prefer a FIT-native ramdisk node over a U-Boot raw-initrd parser patch.

The proposed host-side flow is:
1. Fetch/inspect the exact live separate ramdisk backup by its verified SHA-256.
2. Parse its Android mini-bootimg wrapper and extract only the actual initramfs payload. Do not copy the wrapper header into FIT.
3. Create a FIT ramdisk image node with type=ramdisk, arch=arm64, os=linux, compression=none and the raw CPIO payload.
4. Add ramdisk="ramdisk" to the default FIT configuration alongside kernel and fdt.
5. Let U-Boot v2026.10 select this FIT configuration ramdisk and use boot_ramdisk_high() to copy it into an LMB-selected safe range. image_setup_linux() then writes the initrd start/end and reservation into the final Linux FDT.

This avoids both previously found parser traps:
- An Android wrapper as the second bootm parameter is not treated as an arbitrary external Android initrd; Android-format handling reads the primary Android image/global abootimg context.
- addr:size is ambiguous with FIT [address]:subimage syntax when CONFIG_FIT=y because fit_parse_subimage()/fit_parse_spec() recognizes any colon before the raw-initrd parser.

## 2. U-Boot source path for a FIT-native ramdisk

Pinned v2026.10 control flow:

1. bootm_find_images() calls boot_get_ramdisk() with the selected ramdisk argument. When the FIT config was loaded and no explicit second argument is supplied, the FIT configuration is used.
2. select_ramdisk() looks up FIT_RAMDISK_PROP in the selected FIT configuration. If present, it resolves the named FIT ramdisk image and loads/returns its data and length.
3. boot_ramdisk_high() takes the returned raw payload and either keeps it in place under an explicit zero-copy configuration or allocates a safe LMB region, copies the payload, and sets initrd_start/initrd_end.
4. image_setup_libfdt() invokes fdt_initrd(), which adds an FDT memreserve entry and writes /chosen/linux,initrd-start and /chosen/linux,initrd-end.

If the FIT configuration has no ramdisk property, select_ramdisk() returns -ENOPKG; boot_get_ramdisk() turns that into success with rd_start=rd_end=0. In that case fdt_initrd() returns immediately for zero size. This would preserve initrd properties already present in the selected FDT, but the proposed Android FIT uses the ACK DTB as its FDT; therefore it must include the FIT-native ramdisk if it needs an initrd. One cannot assume ABL's separate initrd properties magically carry across into a different FIT DTB.

Sources:
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/bootm.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-board.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-fit.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-fdt.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/fdt_support.c

## 3. Size gate

Known exact limits:
- reserved3 capacity: 25,165,824 bytes.
- ACK DTB candidate referenced in the existing plan: 1,216,399 bytes.
- A prior package-copy ramdisk payload: 1,322,962 bytes. This is not the live ramdisk SHA, so it is only a budget illustration, not the accepted live size.
- Remaining theoretical space for gzip(ACK Image) after those two payloads: 22,626,463 bytes, before FIT header, configuration data, nodes, string table, alignment and padding.

Therefore the actual acceptance condition is:

gzip(ACK Image) + exact live CPIO payload + exact ACK VD DTB + FIT metadata/alignment <= 25,165,824 bytes.

The compressed kernel length and exact current live CPIO payload length are not yet measured from the authorized frozen candidate files. Do not assume the image fits.

## 4. Why the FIT-native route is preferable when it fits

Advantages:
- No patch to U-Boot's generic FIT subimage parser.
- No reliance on ambiguous addr:size second-argument handling.
- No need to interpret an Android wrapper inside bootm's external initrd selection path.
- U-Boot owns the LMB placement and final FDT initrd fixup.
- Android boot header v2 remains a recovery/ABL wrapper; the Linux boot payload is represented independently as FIT kernel + FDT + ramdisk.

Fallback only if capacity fails:
- Consider a tightly scoped U-Boot raw-initrd syntax patch, parsed before FIT [address]:subimage parsing, with CONFIG_FIT=y and CONFIG_SUPPORT_RAW_INITRD=y tests. Keep the separate ramdisk as a distinct UFS read rather than squeezing it into FIT.
- Do not silently fall back to reusing ABL's previous initrd. The ABL x0 FDT handoff may be useful for RAM banks, but the selected Linux FDT in the FIT is a different tree. Reusing ABL initrd requires an explicit copy/import and LMB-reservation implementation, plus proof that the recovery ABL path provided the correct Android ramdisk.

## 5. Remaining prerequisites

1. Parse the exact live separate-ramdisk backup by SHA-256 and report header version, page_size, kernel_size, ramdisk_size, exact payload offset/length and CPIO magic/compression. Keep the raw firmware private.
2. Obtain the exact frozen ACK Image bytes and compute gzip size with a recorded command, tool version, output SHA and reproducible log.
3. Build the FIT in a host-only scratch area and record exact total byte count, component hashes and parser verification.
4. Re-check FIT staging, 0x91000000 kernel output range, 0x96000000 DTB (or final chosen address), U-Boot relocation/stack, LMB reserved-memory, initrd output range and splash/carveout non-overlap.
5. Read back final U-Boot .config including CONFIG_FIT, CONFIG_CMD_BOOTM, CONFIG_SYS_BOOTM_LEN, CONFIG_LMB and CONFIG_OF_LIBFDT.

## 6. Non-approval boundary

This is a host-side design decision only. It does not approve recovery image creation, AVB/vbmeta changes, temporary boot, recovery boot, partition writes, fastboot, or flashing. No device command was run and no image was built.
