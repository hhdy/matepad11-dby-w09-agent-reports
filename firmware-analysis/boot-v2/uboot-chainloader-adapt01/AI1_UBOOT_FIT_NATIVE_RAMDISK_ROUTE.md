# AI1 — U-Boot Android separate ramdisk handoff route comparison

- Date: 2026-11-28
- Target: DBY-W09 / HOS4.3 / ACK android17-6.18.33 / U-Boot v2026.10
- Scope: Pinned U-Boot source-control-flow and packaging-route comparison. No device or image operations.

## 1. Updated decision

FIT-native ramdisk is a valid option, but it is **not required** merely to avoid a U-Boot parser conflict. A direct source-supported route exists using the existing U-Boot Android boot-image command:

```text
abootimg addr <ANDROID_WRAPPER_ADDR>
bootm <FIT_ADDR> <ANDROID_WRAPPER_ADDR>
```

This route requires CONFIG_ANDROID_BOOT_IMAGE=y, CONFIG_CMD_ABOOTIMG=y, and an exact valid Android wrapper (expected v0-v2). The wrapper buffer is passed as the second bootm address so U-Boot recognizes Android format; the command-global pointer set by abootimg addr tells android_image_get_ramdisk() which external wrapper to parse.

If live wrapper validation or sandbox testing shows this route is unsuitable, an alternative is to extract the payload and use raw addr:size with CONFIG_SUPPORT_RAW_INITRD=y. FIT-native ramdisk remains a third option when a self-contained FIT is useful and the bundle fits reserved3.

## 2. Route A — existing CMD_ABOOTIMG external wrapper path (preferred first test)

Sequence after the wrapper has been read into a safe RAM staging buffer:

```text
abootimg addr <ANDROID_WRAPPER_ADDR>
bootm <FIT_ADDR> <ANDROID_WRAPPER_ADDR>
```

Pinned v2026.10 source chain:

1. cmd/abootimg.c::do_abootimg_addr() stores the supplied address in the global Android boot image pointer.
2. bootm_find_images() passes the explicit second bootm argument to boot_get_ramdisk()/select_ramdisk().
3. select_ramdisk() parses a plain hexadecimal address, inspects the data format at that address, and identifies the Android wrapper.
4. With CONFIG_CMD_ABOOTIMG enabled, its Android-format branch obtains get_abootimg_addr() and calls android_image_get_ramdisk() on that global wrapper pointer.
5. For Android header v0-v2, android_image_get_data() calculates the actual payload pointer/length. ARCH_SNAPDRAGON selects ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR, so U-Boot ignores stale wrapper ramdisk_addr values and can reference the payload inside the wrapper buffer.
6. boot_get_ramdisk() returns the extracted payload range. boot_ramdisk_high() normally allocates a safe LMB destination and copies it.
7. image_setup_libfdt() calls fdt_initrd(), which adds the final initrd FDT memreserve and writes /chosen/linux,initrd-start and /chosen/linux,initrd-end.

Important:
- Generic bootm FIT + wrapper address without an earlier abootimg addr setup is not sufficient for this external wrapper case.
- Use a plain wrapper address in the second argument, not addr:size.
- Do not set initrd_high=~0 unless a zero-copy memory reservation is fully designed and verified.
- The current live separate-ramdisk wrapper must be checked by exact SHA; do not substitute old package-copy fields.

Sources:
- https://github.com/u-boot/u-boot/blob/v2026.10/cmd/abootimg.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-board.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-android.c
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/Kconfig
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/fdt_support.c

## 3. Route B — extract raw payload, then addr:size

Alternative sequence:

```text
abootimg addr <ANDROID_WRAPPER_ADDR>
abootimg get ramdisk rd_data rd_size
bootm <FIT_ADDR> ${rd_data}:${rd_size}
```

Required configuration:
- CONFIG_ANDROID_BOOT_IMAGE=y
- CONFIG_CMD_ABOOTIMG=y
- CONFIG_SUPPORT_RAW_INITRD=y
- CONFIG_FIT=y

This is source-supported with FIT enabled. select_ramdisk() initially tries FIT address/name syntax. When the parsed address points to raw CPIO/gzip bytes, genimg_get_format() does not identify a FIT image, so the later SUPPORT_RAW_INITRD branch processes the colon suffix as the raw payload length. It then goes through the ordinary boot_ramdisk_high()/LMB and fdt_initrd() path.

There is no need to modify fit_parse_subimage() for this route. The earlier claim that the colon inevitably blocks the raw-initrd fallback was incorrect.

This alternative reduces reliance on the Android-format second-argument branch, but needs the extra CONFIG_SUPPORT_RAW_INITRD setting and explicit address/length variables.

Sources:
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-board.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-fit.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/Kconfig
- https://github.com/u-boot/u-boot/blob/v2026.10/cmd/abootimg.c

## 4. Route C — FIT-native ramdisk node

If a self-contained FIT is preferable, parse the exact live Android wrapper on the host, extract only the actual initramfs payload, and add that payload as a FIT image node of type=ramdisk. The default configuration then references ramdisk="ramdisk" alongside kernel and fdt.

U-Boot source path:
1. bootm_find_images() calls boot_get_ramdisk().
2. If the FIT configuration supplies a ramdisk property, select_ramdisk() resolves that FIT ramdisk node and returns its data/length.
3. boot_ramdisk_high() allocates/copies it to an LMB-managed destination.
4. image_setup_libfdt()/fdt_initrd() writes the final initrd reservation and chosen properties.

Do not assume ABL's initrd properties transfer into a different ACK FIT FDT. FIT route C explicitly supplies the initrd to the FDT that will be passed to Linux.

## 5. FIT size gate for Route C only

Known values:
- reserved3 capacity: 25,165,824 bytes.
- ACK DTB candidate referenced in the existing plan: 1,216,399 bytes.
- ROUND64 Phase F package/inventory candidate (SHA-256 `5c20e4781f701e075ab30d3f8389172435e5591579bb5971f1b29331862fddc0`) had a previously inventoried payload of 1,322,962 bytes. A different 2 MiB candidate (`4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb`) is listed in K1_FASTBOOT_GATE01 as the stock separate-ramdisk backup. Their acquisition provenance must be resolved; do not treat the 1,322,962-byte figure as valid for the 4dd6 candidate.
- Remaining theoretical space for gzip(ACK Image), after those two payloads: 22,626,463 bytes, before FIT header, configuration data, nodes, strings, alignment and padding.

Actual Route C acceptance condition:

gzip(ACK Image) + exact live CPIO payload + exact ACK VD DTB + FIT metadata/alignment <= 25,165,824 bytes.

The exact gzip length and live CPIO length are not yet measured from the authorized frozen candidate files. Do not assume the bundle fits.

Routes A and B keep the separate ramdisk wrapper/payload outside the FIT and therefore do not add its bytes to reserved3. They still need a separate safe RAM staging range for the wrapper/payload, plus final LMB placement and reservation validation.

## 6. Current target disposition

| Gate | Result |
|---|---|
| Route A CMD_ABOOTIMG source path | SOURCE-CONFIRMED |
| Route B raw addr:size with CONFIG_SUPPORT_RAW_INITRD | SOURCE-CONFIRMED |
| Route C FIT-native ramdisk node | SOURCE-CONFIRMED |
| Exact live wrapper v0-v2 header/payload compatibility | UNKNOWN pending exact SHA parse |
| Final U-Boot .config | UNKNOWN pending readback |
| Recovery ABL path actually launches U-Boot | CONDITIONAL; recovery-specific ABL control flow audit pending |
| RAM banks and full reserved-memory map for expanded device | BLOCKED pending authoritative final FDT |
| External ramdisk partition authorization/AVB expectations | OPEN |
| Android bootargs/bootconfig, UFS takeover, recovery rollback | OPEN |

Recommended sequence: validate Route A with exact live wrapper bytes and U-Boot host/sandbox. Keep Route B as alternate. Choose Route C only if bundle size and a self-contained FIT provide a concrete advantage.

No device boot, reboot, ADB/Fastboot command, image creation, AVB modification, partition write or flash was performed.
