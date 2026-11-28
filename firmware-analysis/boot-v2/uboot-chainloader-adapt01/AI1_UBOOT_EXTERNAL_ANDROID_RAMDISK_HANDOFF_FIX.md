# AI1 — U-Boot External Android Ramdisk Handoff Fix

- Date: 2026-11-28
- Target: Huawei MatePad 11 DBY-W09 / VD / SM8250 / HOS4.3 / ACK android17-6.18.33
- Source baseline: U-Boot v2026.10
- Scope: static source-path audit and a minimal host-side boot-command/configuration design. No device operation or image build.
- Result: **A source-supported workaround exists using the existing `abootimg` command; the live wrapper's exact header remains a separate hard prerequisite.**

## 1. Correction to the previous FIT report

The previous statement that `bootm FIT_ADDR EXTERNAL_ANDROID_WRAPPER_ADDR` automatically parses the second argument as an Android boot v0 ramdisk was incomplete.

In U-Boot v2026.10 `boot/image-board.c::select_ramdisk()`:
1. It parses the second `bootm` argument into `rd_addr` and detects that the buffer at that address is Android format.
2. If `CONFIG_CMD_ABOOTIMG` is **not** enabled, its Android-format branch calls `android_image_get_ramdisk()` on `images->os.start`, which is the first boot image's OS address. In this design the first image is FIT/ACK Image, not an Android boot wrapper. It therefore does not parse the second argument.
3. If `CONFIG_CMD_ABOOTIMG` **is** enabled, that branch instead calls `get_abootimg_addr()` (or the configured init_boot address) and passes that pointer to `android_image_get_ramdisk()`.

Thus the generic second-argument mechanism alone is insufficient for an external Android wrapper when the first argument is FIT. This report supersedes that one claim in `AI1_UBOOT_ANDROID_FIT_SOURCE_FINDINGS.md`; the FIT kernel/FDT layout and other findings are not changed by this correction.

Relevant source:
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/bootm.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-board.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-android.c

## 2. Minimal workaround using the existing `abootimg` command

U-Boot v2026.10 already implements the needed pointer override:
- `cmd/abootimg.c::do_abootimg_addr()` sets the static `_abootimg_addr` from `abootimg addr <address>`.
- `get_abootimg_addr()` returns that configured address.
- When `CONFIG_CMD_ABOOTIMG=y`, `select_ramdisk()` calls `android_image_get_ramdisk()` using `get_abootimg_addr()` when the second argument is recognized as Android format.

Therefore a source-supported command sequence can be designed as follows (addresses intentionally remain placeholders until the actual memory map is approved):

```text
scsi scan
part start scsi 0 ramdisk ramdisk_start
part size  scsi 0 ramdisk ramdisk_blocks
scsi read  ${ramdisk_wrapper_addr} ${ramdisk_start} ${ramdisk_blocks}
abootimg addr ${ramdisk_wrapper_addr}
bootm ${fit_addr} ${ramdisk_wrapper_addr}
```

Semantics:
- The U-Boot SCSI read loads the complete `ramdisk` partition wrapper into a verified scratch buffer.
- `abootimg addr` explicitly points the Android parser global at that exact wrapper.
- The second `bootm` argument makes `select_ramdisk()` recognize the external buffer's Android image format.
- With `CONFIG_CMD_ABOOTIMG=y`, `select_ramdisk()` invokes the Android ramdisk parser on the pointer just set by `abootimg addr`.
- `boot_get_ramdisk()` receives the payload address and length. The normal `boot_ramdisk_high()` path can then place/copy the initrd into an LMB-managed final range before Linux handoff.
- The FIT still supplies the ACK kernel and ACK FDT; this does not put the Huawei ramdisk back into the Android boot v2 embedded ramdisk.

Do not copy the placeholder commands verbatim into a device environment yet. `ramdisk_wrapper_addr` must be selected from a verified free range that does not collide with the FIT staging buffer, U-Boot relocation/stack/malloc, ACK kernel destination, FDT, splash, or any secure/reserved-memory region.

### 2.1 Direct Android wrapper mode uses a plain address

For the CMD_ABOOTIMG global-pointer route in §2, the second parameter must be the plain hexadecimal wrapper address:

```text
abootimg addr <ANDROID_WRAPPER_ADDR>
bootm <FIT_ADDR> <ANDROID_WRAPPER_ADDR>
```

Do not append :<size> in this particular route. That would ask select_ramdisk() to interpret the second argument using FIT subimage syntax first, not the Android wrapper mode.

This restriction is specific to passing the Android wrapper itself. The separate raw-payload addr:size route is valid with CONFIG_SUPPORT_RAW_INITRD=y; see §5 below.

Source:
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-fit.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-board.c

## 3. Required U-Boot configuration

Add the following explicit line to the target defconfig:

```text
CONFIG_CMD_ABOOTIMG=y
```

Other relevant configuration behavior:
- `CMD_ABOOTIMG` depends on `ANDROID_BOOT_IMAGE` in U-Boot v2026.10 `cmd/Kconfig`.
- `ANDROID_BOOT_IMAGE` defaults to y when `FASTBOOT` is enabled. CoWave enables `CONFIG_USB_FUNCTION_FASTBOOT=y`, which selects `FASTBOOT`; nevertheless the generated `.config` must be archived and checked.
- U-Boot v2026.10 `arch/arm/Kconfig` makes `ARCH_SNAPDRAGON` select `ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR`.
- For Android header v0-v2, `android_image_get_ramdisk()` returns the ramdisk payload's in-wrapper address when `ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR` is enabled, rather than honoring a stale absolute `ramdisk_addr` from the wrapper header.
- `boot_ramdisk_high()` then handles the final initrd placement. The final destination must still be checked against the target RAM map and all reservations.

Do not remove `ARCH_SNAPDRAGON` or disable `ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR` for this path without a separately justified design.

Configuration sources:
- https://github.com/u-boot/u-boot/blob/v2026.10/cmd/Kconfig
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/Kconfig
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/Kconfig
- https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/uboot/dby-w09_defconfig

## 4. Exact parser behavior and remaining live-wrapper gate

`android_image_get_ramdisk()` parses Android boot image headers v0-v2 by deriving the payload pointer from the header size/page size and the kernel payload size rounded to the declared page size. For versions <=2, the payload can be passed in place. With Snapdragon's `ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR`, U-Boot returns that payload pointer and parsed ramdisk length.

This is the correct mechanism only if the current live `ramdisk` partition backup is actually a valid Android boot v0-v2 wrapper with:
- Android magic at the start of the partition data;
- valid `header_version` (0, 1, or 2 for this expected path);
- valid non-zero `page_size` and consistent component offsets/sizes;
- a non-zero `ramdisk_size` that stays within the partition's captured byte length;
- a ramdisk payload whose decompressed CPIO/initramfs contents match the expected Huawei first-stage image.

Earlier project reports identify the current live wrapper backup SHA-256 as `4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb`, but the exact live header fields have not yet been closed in the current analysis. A separate historical package copy was reported as header v0 / page size 2048 / ramdisk payload 1,322,962 bytes, but it has a different SHA and must not be substituted for the live backup.

Therefore `ANDROID_RAMDISK_PARSER_PATH=SOURCE_CONFIRMED`, while `CURRENT_LIVE_WRAPPER_COMPATIBILITY=UNKNOWN/HOLD` until the exact live bytes are re-read and validated.

## 5. Alternative: extract payload, then use raw addr:size

The same U-Boot source provides a second route:

```text
abootimg addr <ANDROID_WRAPPER_ADDR>
abootimg get ramdisk rd_data rd_size
bootm <FIT_ADDR> ${rd_data}:${rd_size}
```

Requirements:
- CONFIG_ANDROID_BOOT_IMAGE=y
- CONFIG_CMD_ABOOTIMG=y
- CONFIG_SUPPORT_RAW_INITRD=y
- The second bootm parameter must identify the raw CPIO/gzip initramfs payload address and its true length, not the wrapper address/partition length.

This route is source-supported even with CONFIG_FIT=y. select_ramdisk() does first call fit_parse_conf()/fit_parse_subimage() and the colon may initially be recorded as a FIT subimage separator. But it does not return at that point. It inspects the bytes at the parsed address with genimg_get_format(). A raw CPIO/gzip payload is not a FIT image, so the FIT case does not set done. The later CONFIG_SUPPORT_RAW_INITRD branch then parses the colon suffix as the raw payload length and sets the output ramdisk range.

Consequently no fit_parse_subimage() patch is required for raw addr:size. The previous claim that the colon inevitably prevents the raw-initrd fallback was incorrect.

This route is a valid alternative, but it requires a final build with SUPPORT_RAW_INITRD enabled and a host/sandbox test using the exact target wrapper/payload format. The simpler CMD_ABOOTIMG Android-format path in §2 remains the first-choice route because it needs only a plain wrapper address as the second bootm argument and does not require SUPPORT_RAW_INITRD.

## 6. Updated gate matrix

| Gate | Result | Meaning |
|---|---|---|
| Generic `bootm FIT wrapper_addr` with `CMD_ABOOTIMG` disabled | **FAIL for this use** | The v2026.10 Android branch parses `images->os.start`, not the second argument |
| `CONFIG_CMD_ABOOTIMG=y` + `abootimg addr wrapper_addr` | **SOURCE-CONFIRMED WORKAROUND** | The external pointer is used by `select_ramdisk()` when it recognizes Android format |
| Snapdragon ignore-header-address behavior | **SOURCE-CONFIRMED** | `ARCH_SNAPDRAGON` selects `ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR`; v0-v2 returns in-wrapper payload pointer |
| Live Huawei wrapper header compatibility | **UNKNOWN/HOLD** | Current live backup SHA is known, but exact header/page/length has not been verified in this review |
| Final initrd placement | **PARTIAL** | `boot_ramdisk_high()` has LMB relocation path; actual free RAM/reservations remain unverified |
| ACK bootconfig requirement | **UNKNOWN/PARTIAL** | Header v0-v2 has no vendor_boot v4 bootconfig section; Android first-stage expectations still need review |
| Integrated boot / temporary boot / partition write | **NO-GO / HARD NO-GO** | This source fix does not prove ABL recovery acceptance, RAM map, AVB, rollback, or bootability |

## 7. Minimal follow-up actions

Before any FIT/recovery candidate is produced:
1. Add `CONFIG_CMD_ABOOTIMG=y` to the target U-Boot defconfig and preserve the final generated `.config`.
2. On the already-authorized local read-only copy, validate the exact live wrapper SHA, magic, header version, page size, kernel/ramdisk sizes and payload bounds. Do not use the older package copy.
3. Confirm the decompressed payload's CPIO structure and essential first-stage files against the existing read-only evidence.
4. After the correct target RAM map is available, select a non-overlapping wrapper staging address and verify U-Boot's LMB final initrd destination.
5. Add host-side tests for: valid wrapper, truncated wrapper, wrong magic, unsupported header version, zero/invalid page size, payload length outside partition, and a `ramdisk_addr` value that conflicts with the staging location. Confirm the parser ignores the stale address under the Snapdragon config.
6. Re-check the Android bootargs/bootconfig contract before claiming Android first-stage compatibility.

## 8. Safety boundary

This is a static source review and command-design note only. No device was connected; no ADB/Fastboot/OEM/boot/reboot command was run; no U-Boot/FIT/recovery image was built; no partition was written; no temporary boot was attempted; and no device operation was authorized.

**Conclusion:** the external Huawei ramdisk handoff is not supported by the unmodified generic path as previously described, but U-Boot v2026.10 already has a practical workaround via `CONFIG_CMD_ABOOTIMG` and an explicit `abootimg addr` assignment. The live wrapper still must be verified before this becomes a proven Android initrd path.