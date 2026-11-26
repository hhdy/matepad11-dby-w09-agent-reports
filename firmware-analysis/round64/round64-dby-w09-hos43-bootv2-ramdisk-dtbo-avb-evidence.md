# ROUND64 Phase F — HOS4.3 boot-v2 / ramdisk / DTBO / AVB read-only evidence

Executor: local Agent (independent of both AI task authors)
Taskbook: `kernel-baseline/round61/AGENT_TASKBOOK_PHASE_F_READONLY_SECOND_AI.md`, blob `f5dd7e0222e98685184be8881b68615e42b442e8`, issued 2026-11-25T02:20:37Z by the Second AI
Target: Huawei MatePad 11 (2021), DBY-W09, HOS4.3
Mode: local, offline, read-only. No repack, no image edit, no AVB metadata disclosure, no device operation.

## 0. Tool gating (satisfied)

The taskbook permits only an already-installed trusted AVB parser and forbids writing a custom parser or using an `AVB0` magic scan as a substitute. That gating is **satisfied** here: the pinned ACK 6.18.33 source tree contains AOSP's own `external/avb/avbtool.py`, self-reported version `avbtool 1.4.0`, run read-only in `info_image` mode. Provenance: AOSP source, present in the pinned kernel tree before this round; file sha256 `da733b43019931f1dd5d62a0e856bc769acbd7034dd8d376582881f42a9a83c3`. No parser was written for this task; the only new script is a *sanitizer* that calls that avbtool and discards forbidden fields.

Available non-AVB tools: file 5.45, dtc/fdtget/fdtdump 1.7.0, gzip 1.12, lz4 1.9.4, xz 5.4.5, Python 3.12.3, binutils readelf 2.42. No `unpack_bootimg`, `mkbootimg`, `avbtool` on PATH, no Python `avb` module; those are reported as such rather than replaced with a substitute.

Forbidden outputs are suppressed throughout: public key bytes/hashes, signatures, salts, image and hashtree root digests, rollback index values/locations, and raw vbmeta blocks. Fields below marked `(prior-round inventory)` come from existing local JSON outputs and are identified as such — they are not presented as new parser results.

## 1. Required fields

| Field | Status | Value / note |
|---|---|---|
| Firmware build/revision | PARTIAL | HOS4.3 DBY-W09; stock `boot.img` os_version field decodes to Android 11 / 2020-11 (prior-round inventory), standalone `ramdisk.img` build.prop to Android 12 / `SKQ1.220804.001` / 2022-08. Exact package revision UNKNOWN. |
| Input inventory file list | PASS | 15 files below, all in one local payload directory. Whole partition images, unchanged. |
| Existing trusted tool name/version/path | PASS | AOSP `avbtool` 1.4.0 from pinned ACK 6.18.33 `external/avb/avbtool.py`; sha256 above. |
| Tool provenance | PASS | AOSP upstream source inside the pinned kernel tree, pre-existing, unmodified. |
| boot.img SHA-256 / bytes | PASS | `027f88fd…3da19b8` / 100,663,296 |
| boot header version | PASS (prior-round inventory) | Android boot header v2 |
| page size | PASS (prior-round inventory) | 4096 |
| kernel / ramdisk / DTB sizes and offsets | PASS (prior-round inventory) | kernel 22,264,379 @ 4096; ramdisk 519,986 @ 22,269,952; embedded DTB 1,664,243 @ offset derived from header; payload end 24,457,216. Standalone `ramdisk.img` is header v0 / page 2048 / ramdisk 1,322,962, payload end 1,325,056. |
| separate ramdisk SHA-256 / bytes | PASS | `5c20e478…fddc0` / 2,097,152 |
| DTBO SHA-256 / bytes | PASS | `51a5d7b8…70c0c0c` / 25,165,824 |
| vbmeta file inventory (names/hashes/sizes only) | PASS | 7 vbmeta files listed below; all 1,048,576 bytes. |
| AVB footer state per image | PASS | AOSP avbtool reports a footer on all 14 of 15 images; see table. |
| AVB footer original-image-size field | PASS | boot 24,457,216; ramdisk 1,325,056; dtbo 2,963,810; recovery and erecovery 49,614,848; recovery/erecovery_ramdisk 29,102,080; vbmeta_cust 10,375,168 (anomalous, see below). Independent cross-check: these match the prior-round independently computed payload ends byte-for-byte. |
| Descriptor class / target partition / parent vbmeta | PASS | AOSP avbtool descriptor classes and target names below; no key/rollback/digest values published. |
| Separate ramdisk and DTBO coverage | PASS | Root vbmeta chain descriptor targets `ramdisk` and `dtbo`; DTBO also carries its own hash descriptor in the partition image. |
| DTBO container format and entries | PASS | magic `0xD7B7AB1E`, version 0, page 4096, 9 entries, 32-byte entries at offset 32, total size 2,963,810 (32-byte header read-only). Entry board-id values and fragment counts below (prior-round inventory). |
| HOS4.3 ABL-selected entry | UNKNOWN | No ABL selection evidence. Entry 8 / board-id `0x206a` is a candidate only; nine board-ids exist. Entry 8's 145 fragments target vendor-only nodes and are not compatible with the minimal ACK board draft — stated as a taskbook-mandated caveat, not as a selection claim. |
| First-stage fstab/module-load observations | PASS (prior-round inventory) | Standalone ramdisk is gzip→CPIO newc with 17 entries: `/init` (2,880,584 B), `/patch_avb_key` (520 B), `system/etc/ramdisk/build.prop` (942 B), 13 empty dirs. Zero hits for fstab, init.rc, ueventd, sepolicy, kernel modules, modules.load, by-name, dm-verity, erofs in the ramdisk inventory. First-stage fstab is therefore not in this ramdisk; it resides in the base DTB `/firmware/android/fstab` (ROUND19). No module-load conclusion is drawn from kernel module support. |
| Unknown or ambiguous facts | PASS | Listed in section 4. |
| Evidence file paths and SHA-256 | PASS | Sanitized identifiers and hashes below. |

## 2. Full sanitized avbtool table

Columns: footer state / original image size / release string / algorithm / descriptor classes → target partitions. Values forbidden by the taskbook are not emitted.

| inventory id | bytes | sha256 (full) | avbtool exit | footer state | original image size | release string | algorithm | descriptor classes → target partitions |
|---|---:|---|---:|---|---:|---|---|---|
| boot.img | 100663296 | 027f88fd6f318523925ca27a4d681d17a9bbca904b0c471ccc05e651d3da19b8 | 0 | PRESENT | 24457216 | avbtool 1.1.0 | SHA256_RSA2048 | Hash → boot |
| ramdisk.img | 2097152 | 5c20e4781f701e075ab30d3f8389172435e5591579bb5971f1b29331862fddc0 | 0 | PRESENT | 1325056 | avbtool 1.2.0 | SHA256_RSA2048 | Hash → ramdisk |
| dtbo.img | 25165824 | 51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c | 0 | PRESENT | 2963810 | avbtool 1.1.0 | SHA256_RSA2048 | Hash → dtbo |
| recovery.img | 100663296 | 956417584d2deb409761316f262732859e356a15cb5fe85436df3d5f141c5548 | 0 | PRESENT | 49614848 | avbtool 1.1.0 | SHA256_RSA2048 | Hash → recovery |
| recovery_ramdisk.img | 33554432 | b2b9e3391927bd31684504e7dee7f527bdcbfe53d4bd325e5d1beeeaada7c3e1 | 0 | PRESENT | 29102080 | avbtool 1.1.0 | SHA256_RSA2048 | Hash → recovery_ramdisk |
| recovery_vbmeta.img | 1048576 | bf59d55d664b9f6295273b10701845b9e4e3f184b6e7c5140f29681d1c5b507b | 0 | PRESENT | N/A | avbtool 1.1.0 | SHA256_RSA2048 | Chain → recovery, dtbo, recovery_ramdisk, recovery_vendor |
| erecovery.img | 100663296 | 956417584d2deb409761316f262732859e356a15cb5fe85436df3d5f141c5548 | 0 | PRESENT | 49614848 | avbtool 1.1.0 | SHA256_RSA2048 | Hash → recovery |
| erecovery_ramdisk.img | 33554432 | b2b9e3391927bd31684504e7dee7f527bdcbfe53d4bd325e5d1beeeaada7c3e1 | 0 | PRESENT | 29102080 | avbtool 1.1.0 | SHA256_RSA2048 | Hash → recovery_ramdisk |
| erecovery_vbmeta.img | 1048576 | ed04c8480c9b9438445c03179e16012aefa69b4169a194a82e260b246a65c73f | 0 | PRESENT | N/A | avbtool 1.1.0 | SHA256_RSA2048 | Chain → erecovery, dtbo, erecovery_ramdisk, erecovery_vendor |
| vbmeta.img | 1048576 | c797232b437c483ad2332e8754d880ce61f0d211676dfc6397d98160230bbce7 | 0 | PRESENT | N/A | avbtool 1.1.0 | SHA256_RSA2048 | Chain → boot, ramdisk, vbmeta_system, vbmeta_vendor, vbmeta_odm, eng_vendor, eng_system, dtbo, version, vbmeta_hw_product, preload, preas, preavs, vbmeta_cust |
| vbmeta_system.img | 1048576 | 8cf59433d16973adf542ec570c1656a773cdf77a0efb82f6544a7ce9fa735bf6 | 0 | PRESENT | N/A | avbtool 1.2.0 | SHA256_RSA2048 | Hashtree → system |
| vbmeta_vendor.img | 1048576 | 375ec9c09cc829736359b86b2b09179b46995fba68a661d0cbf2e11df6c61a0a | 0 | PRESENT | N/A | avbtool 1.1.0 | SHA256_RSA2048 | Hashtree → vendor |
| vbmeta_odm.img | 1048576 | c99184823142b9351b601e101a80ebecd947845002d561d9c9f3a42623420747 | 0 | PRESENT | N/A | avbtool 1.1.0 | SHA256_RSA2048 | Hashtree → odm |
| vbmeta_cust.img | 1048576 | eb517a9776581677d6550d35689301b19c8a528fb9c8070d0180c9d8d3fe511f | 0 | PRESENT (anomalous) | 10375168 | avbtool 1.4.0 | NONE | none |
| vbmeta_hw_product.img | 1048576 | 387d5307048a4036525f61a9fd6ba30ad9302fb4e7c497cde74e6bb98161311d | 0 | PRESENT | N/A | avbtool 1.2.0 | SHA256_RSA2048 | Hashtree → hw_product |

Note: `erecovery.img` is byte-identical to `recovery.img`, and `erecovery_ramdisk.img` is byte-identical to `recovery_ramdisk.img` (matching sha256 values above), but their vbmeta chain descriptor targets differ (`erecovery*` vs `recovery*`). This is observed metadata, not an explanation.

`vbmeta_cust.img` anomaly: a valid `AVBf` footer is present at the end of the file, pointing to a 1,344-byte vbmeta blob at offset 10,375,168 outside the 1 MiB file. AOSP avbtool reports that embedded blob as `Algorithm: NONE`, release string `avbtool 1.4.0`, no descriptors. Footer state is therefore PRESENT but its referenced vbmeta is an empty shell; this is recorded rather than "explained away". Descriptor coverage for `cust` via this file is **UNKNOWN**. The root vbmeta still declares a chain target named `vbmeta_cust`.

## 3. Cross-checks and provenance of claims

- Claims from actual trusted parser output: all footer states, original image sizes, release strings, algorithms, descriptor classes and target names in section 2; produced by AOSP avbtool 1.4.0 `info_image` with forbidden fields discarded by the sanitizer.
- Claims from prior-round local inventory: boot header version/page/size/offset, ramdisk CPIO inventory, DTBO nine-entry board-id/fragment census, base DTB fstab location. Sources: ROUND19 `logs/boot_headers.json`, `logs/ramdisk_inventory.json`, `logs/dtbo_audit.json`, and the ROUND19 report. These were not re-parsed and no new parser was written.
- Claims from this round's read-only header read: DTBO container magic/total/entry count/version/page size, from the first 32 bytes of `dtbo.img`.
- Independent cross-check: the five boot-family original image sizes from avbtool match the prior-round independently computed payload ends exactly (boot 24,457,216; ramdisk 1,325,056; recovery 49,614,848; recovery_ramdisk 29,102,080), and dtbo 2,963,810 matches the DTBO container `total_size`. This increases confidence in both readings; it is not an AVB verification or an ABL-acceptance claim.

## 4. Unknown / ambiguous facts

- Which of the nine DTBO board-ids HOS4.3 ABL selects at runtime. UNKNOWN.
- Whether the `AVBf` footer in `vbmeta_cust.img` referencing a blob beyond the file boundary is intentional, a truncated extraction, or a vendor layout variant. UNKNOWN; no repack or reinterpretation attempted.
- Whether `hash` descriptors in images with a `recovery` target being byte-identical to `erecovery` images is intentional. UNKNOWN.
- Hashtree `image_size` semantics versus measured dynamic-partition sizes (ROUND19 U-8). Not re-litigated here; the taskbook asked for class/target coverage only, which is provided.
- Any first-stage module-load path beyond "none present in this ramdisk". The `modules.load`/`modules.dep`/`modules.alias`/`modules.softdep`/`modules.options` files are absent; whether the kernel expects them elsewhere is UNKNOWN.

## 5. Limits observed

- No image, vbmeta, DTB, ramdisk, source or config file was modified. No candidate boot image was created; no footer appended or removed; no AVB disabled or re-signed.
- No fastboot, reboot, unlock, root, partition write, device connection, ADB or flashing.
- No tool installation or download. No raw firmware bytes, keys, signatures, salts, digests, rollback indexes, serial numbers, MAC addresses, IMEIs or user identifiers published.
- No conclusion is drawn about whether the current storage-first port will boot; this is an evidence inventory only.
