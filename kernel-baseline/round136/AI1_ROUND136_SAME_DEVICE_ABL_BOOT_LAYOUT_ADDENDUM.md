# AI1 ROUND136 Addendum — DBY-W09 Same-Device ABL / Boot Image Layout Reconciliation

- Date: 2026-11-26
- Device under investigation: Huawei MatePad 11 (2021), DBY-W09 / SM8250
- Kernel target remains: ACK `android17-6.18.33_r00`, pinned commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Nature: AI1 public-source cross-check and interpretation addendum; no source-tree or patch changes, no package construction, no device actions.
- Base review: `kernel-baseline/round136/AI1_ROUND136_REVIEW_AND_DISPOSITION.md`
- Related AI2 report: `firmware-analysis/round136-preboot-blocker-audit/AI2_ROUND136_PREBOOT_BLOCKER_AUDIT.md`

## 1. New evidence: public same-device Linux port

AI1 reviewed the public repositories:

- `https://github.com/svesnav/linux-dby-w09`
- `https://github.com/svesnav/dby-w09-installer`

The first repository identifies the target as Huawei MatePad 11 (2021), DBY-W09, SM8250 / Snapdragon 865. Its README documents the boot flow as:
- Huawei ABL boots an Android header-v2 `boot` image.
- ABL loads its ramdisk from the separate `ramdisk` partition.
- The ABL-applied DTBO must fill `/rootparam` like the stock overlay; the repository says other DTBO choices return the tablet to fastboot.
- `fastboot boot` (RAM boot) is refused by that tested setup.

Source: `https://github.com/svesnav/linux-dby-w09/blob/main/README.md`

## 2. What the public implementation actually does

### 2.1 Boot image and DTB

`repack_boot.py`:
1. Unpacks the stock `boot.img` with AOSP `unpack_bootimg.py`.
2. Explicitly requires header version 2.
3. Reuses the stock mkbootimg flags/payload layout.
4. Replaces the kernel path when requested.
5. Replaces the `--dtb` path when requested.
6. Does not replace the stock `--ramdisk` argument.

Source: `https://github.com/svesnav/linux-dby-w09/blob/main/repack_boot.py`

`build_dev_images.sh` invokes it with:
- `--kernel Image.gz`
- `--dtb sm8250-huawei-dby-w09.dtb`
- a replacement command line.

It therefore demonstrates a same-device implementation using the Android header-v2 boot image's own DTB field, not a separately written DTB partition and not a DTB appended to the kernel bytes.

Source: `https://github.com/svesnav/linux-dby-w09/blob/main/build_dev_images.sh`

### 2.2 Independent ramdisk partition

The same `build_dev_images.sh` separately builds a header-v0 ramdisk payload with:
- an empty kernel,
- the Linux initramfs as the ramdisk payload,
- 2048-byte page size,
- then lays that payload over the stock 2 MiB `ramdisk` partition while preserving its AVB footer.

The public port's new initramfs is therefore placed in the independent `ramdisk` partition, not inserted into the `boot.img` ramdisk field. The original stock boot-image ramdisk field is retained by the repacker rather than overwritten.

Source: `https://github.com/svesnav/linux-dby-w09/blob/main/build_dev_images.sh`

The installer README likewise says it prepares three distinct images: `boot` (stock header + kernel + DTB + command line), `ramdisk` (new payload laid over stock partition with AVB footer retained), and `dtbo`. It stores stock copies for the return-to-HarmonyOS path.

Source: `https://github.com/svesnav/dby-w09-installer/blob/main/README.md`

## 3. Reconciliation with the group-chat statements

The group-chat statements were:
- "ABL does not support custom DT in boot; it must be embedded."
- "ramdisk cannot be put into boot; it will cause duplicate boot."
- "unless ramdisk is skipped, but that is not worthwhile / elegant."

AI1 interpretation:

1. **The broad claim that this ABL cannot use a custom DTB carried by boot is not established.** The same-model public project documents an Android header-v2 boot image with a replacement DTB supplied through `--dtb`, plus a separate DTBO. This is direct counter-evidence to a blanket statement that the ABL cannot consume a custom DTB from the boot image's DTB section.

2. "Embedded DTB" is ambiguous and must not be conflated:
   - header-v2 `boot.img` DTB section (`--dtb`);
   - concatenating/appending DTB bytes to `Image.gz` (often called Image.gz-dtb);
   - compiling a built-in DTB into the kernel;
   - a separate DTBO partition applied by ABL.
   The public DBY-W09 project demonstrates the first mechanism. It does not prove that every other mechanism is supported or interchangeable.

3. **The ramdisk warning is compatible with the public implementation.** It does not put the new Linux initramfs in the boot image's ramdisk section; it installs that initramfs in the independent ramdisk partition. However, it preserves the original stock boot-image ramdisk field. Therefore we must not translate this into "zero the boot ramdisk field", "delete the stock ramdisk", or "skip ramdisk". The exact ABL selection/consumption semantics for HOS4.3 Android boot remain to be proven.

4. The public project's DTBO statement makes `/rootparam` a high-priority same-device compatibility constraint. It is a test result/documentation from the public HOS4.2/Linux 7.0 path, not proof that the HOS4.3 Android 17 runtime chooses the same DTBO entry or accepts the same one-entry overlay. Preserve the constraint as a hypothesis to verify, not as an automatic patch instruction.

5. The public project reports `fastboot boot` refusal. We must not assume RAM boot is an available reversible first-test method. This is not permission to flash any partition.

## 4. Updated decision for the ACK 6.18.33 project

- Keep ROUND135 R3 output unchanged. The offline Image and DTB build remain valid as offline build evidence only.
- Do not append DTB to the kernel or change Kconfig built-in-DTB behavior merely because the group used the word "embedded".
- Do not add a new initramfs to the boot image's ramdisk section.
- Do not erase, zero, omit, or rewrite the stock boot image's existing ramdisk field without a direct HOS4.3 ABL contract proving that operation safe.
- Keep boot-v2, independent ramdisk partition, DTBO, and AVB as separate D-path artifacts.
- Treat the likely candidate packaging hypothesis as: preserve stock header-v2 structure; replace only kernel and the boot-v2 DTB section if HOS4.3 evidence confirms that ABL path; keep the stock boot ramdisk field untouched; prepare any intended ramdisk payload only in the independent ramdisk partition; preserve the required DTBO/rootparam contract. This is a hypothesis only, not an approved package recipe.
- Do not package, sign, modify AVB, connect to the tablet, use ADB/fastboot, write partitions, or boot without separate explicit authorization and an audited restore path.

## 5. What remains required before first Android 17 boot

This addendum narrows the search but does not close D. We still need HOS4.3-specific, auditable evidence for:
1. Exact HOS4.3 ABL version/build and its boot-v2 DTB-field behavior for the intended Android kernel.
2. Whether ABL uses the boot image's embedded ramdisk, the independent ramdisk partition, or a defined precedence/combination; what happens if both carry non-empty initramfs payloads.
3. Full stock boot-v2 header fields and section boundaries, including both ramdisk observations and DTB placement.
4. The actual selected DTBO entry and the final FDT after ABL's DTBO/rootparam processing.
5. Complete AVB descriptor/chain, `vbmeta_cust` anomaly resolution, signing and rollback policy.
6. Whether the test route requires partition writes; the public same-device reference says `fastboot boot` is refused, so a full verified backup/restore plan is mandatory before any write.

Until those are proven, D remains BLOCKED for Android 17 first boot. A/B/C also remain as recorded in ROUND136. No hardware testing is authorized by this addendum.

## 6. Evidence classification

- Public same-device DBY-W09 / HOS4.2 Linux 7.0 project: direct implementation and reported boot-flow reference.
- HOS4.3 target boot inventory: existing local extracted evidence as summarized in ROUND136; not a newly reproduced ABL trace.
- HOS4.3 Android 17 ABL behavior: UNKNOWN where not directly established.
- No claims are made that the public Linux boot package can be transplanted as-is to ACK Android 17.
