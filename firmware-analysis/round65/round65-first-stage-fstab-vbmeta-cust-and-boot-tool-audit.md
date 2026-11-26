# ROUND65 — HOS4.3 first-stage fstab, vbmeta_cust provenance and boot-tool contract audit

**Executor:** local WorkBuddy Agent; offline, read-only evidence review
**Device:** Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250
**Baseline:** ACK android17-6.18.33_r00 / common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
**Taskbook:** `kernel-baseline/round61/AGENT_TASKBOOK_PHASE_FOLLOWUP_READONLY_SECOND_AI.md`,
blob `ef0251fe59d3b78d852ff8474a073149be763108` (6762 B), branch
`ai-parallel/stagea-port-until-boot`.
**Date:** 2026-11-25 (GMT+8)

## 0. Evidence classes and boundaries

Every statement below is tagged with one of four classes:
- **[P]** direct parser output from an already-present local artifact or read-only tool invocation;
- **[R]** fact reused from a prior-round report / inventory (not re-derived this round);
- **[S]** source-derived tool behavior (read from trusted, already-present source or `--help`);
- **[U]** unknown / unavailable — no authorized local evidence establishes it.

Boundaries honored (taskbook §1): no source/DTS/DTBO/firmware/image/config/script/report edit;
no kernel build, Kleaf/Bazel, Kconfig regeneration, mkbootimg/unpack_bootimg image generation;
no tool install/download; no device/ADB/fastboot/recovery/reboot/unlock/root/remount/flash;
no AVB disable/footer edit/sign/repack/boot-candidate creation. No raw firmware, DTB/DTBO,
ramdisk, vbmeta data, keys, signatures, salts, digests, rollback values, serials, MACs,
IMEIs, account identifiers or private paths are published. `mkbootimg --help` was invoked
once, read-only, on an already-installed executable (permitted by §5). Nothing was written
back into any image. No ABL behavior was inferred from board-id candidates.

## 1. Work package A — first-stage fstab contract

**Source:** ROUND19 already-decompiled base FDT `base_2.dts`, node
`/firmware/android/fstab`, lines 24190–24381. **Class [P]** (direct read of existing
decompiled text; no firmware extraction). This corroborates the ROUND64 statement that the
first-stage fstab lives in the base FDT, not in the standalone ramdisk **[R]**.

The node has `compatible = "android,fstab"` and 19 child entries. Sanitized semantic table
(no long raw strings reproduced; `dev` shown as logical name or by-name path only):

| # | entry | mount point | dev | fs type | mnt_flags | fs_mgr flags (semantics) |
|---:|---|---|---|---|---|
| 1 | system_ext4 | /system | system | ext4 | ro | wait, logical, avb |
| 2 | system_erofs | /system | system | erofs | ro | wait, logical, avb |
| 3 | vendor_ext4 | /vendor | vendor | ext4 | ro | wait, logical, avb |
| 4 | vendor_erofs | /vendor | vendor | erofs | ro | wait, logical, avb |
| 5 | odm_ext4 | /odm | odm | ext4 | ro | wait, logical, avb |
| 6 | odm_erofs | /odm | odm | erofs | ro | wait, logical, avb |
| 7 | cust_ext4 | /cust | cust | ext4 | ro | wait, nofail, logical, avb |
| 8 | cust_erofs | /cust | cust | erofs | ro | wait, nofail, logical, avb |
| 9 | hw_product_ext4 | /hw_product | hw_product | ext4 | ro | wait, nofail, logical, avb |
| 10 | hw_product_erofs | /hw_product | hw_product | erofs | ro | wait, nofail, logical, avb |
| 11 | version_ext4 | /version | by-name/version | ext4 | ro | wait, nofail, avb |
| 12 | version_erofs | /version | by-name/version | erofs | ro | wait, nofail, avb |
| 13 | preload_ext4 | /preload | by-name/preload | ext4 | ro | wait, nofail, avb |
| 14 | preload_erofs | /preload | by-name/preload | erofs | ro | wait, nofail, avb |
| 15 | preas_ext4 | /preas | by-name/preas | ext4 | ro | wait, nofail, avb |
| 16 | preas_erofs | /preas | by-name/preas | erofs | ro | wait, nofail, avb |
| 17 | preavs_ext4 | /vendor/preavs | by-name/preavs | ext4 | ro | wait, nofail, avb |
| 18 | preavs_erofs | /vendor/preavs | by-name/preavs | erofs | ro | wait, nofail, avb |
| 19 | metadata | /metadata | by-name/metadata | ext4 | rw,noatime,nosuid,nodev,discard | wait, **first_stage_mount**, check, formattable |
| — | patch_ext4 | /patch_hw | by-name/patch | ext4 | ro | wait, nofail, **avb_keys=/patch_avb_key** |
| — | patch_erofs | /patch_hw | by-name/patch | erofs | ro | wait, nofail, **avb_keys=/patch_avb_key** |

(19 core entries plus 2 `patch_*` variants = 21 child nodes total; the table lists all.)

### Flag semantics present / absent
- **Present:** `wait` (all entries); `logical` (system/vendor/odm/cust/hw_product —
  dynamic/super partitions); `avb` (all except metadata); `nofail` (cust onward and patch);
  `first_stage_mount` + `check` + `formattable` (metadata only); `avb_keys=/patch_avb_key`
  (patch entries only). All have `status = "ok"`.
- **Explicitly ABSENT from this fstab node** (kept absent per taskbook §2, not read as
  "disabled"): `verify`, `slotselect`, `latemount`, `quota`, `fileencryption`, `fsverity`.
  No `userdata` and no `recovery` fstab entry appears in this node.
- **Dual ext4/erofs pairs** for every read-only partition: two selectable filesystem
  variants for the same `dev`/mount point (both `status="ok"`); which is actually used at
  runtime is a build/mount-policy matter not established here **[U]**.
- **dm-verity / hashtree / FEC:** the fstab itself only carries `avb` / `logical` /
  `avb_keys` semantics. The hashtree parameters (sha1, 4096/4096, fec 2, per-partition
  image_size/tree_size) are a separate AVB-descriptor matter, already inventoried in
  ROUND19/64 and not reproduced here **[R]**. No digest/salt is published.

## 2. Work package B — ramdisk and module-loading route

**Source:** ROUND19 `logs/ramdisk_inventory.json` (2932 B) **[P]**, cross-checked against
ROUND19/20/21/22 reports **[R]** and the final `.config` **[P]**.

The standalone `ramdisk_payload.bin` (gzip/newc, 1,322,962 B → 2,884,352 B, 17 entries:
13 dir / 3 file / 1 trailer) contains exactly three files:
- `/init` — 2,880,584 B static AArch64 ELF;
- `/patch_avb_key` — 520 B (AVB 2048-bit public-key blob; not reproduced);
- `/system/etc/ramdisk/build.prop` — 942 B.
Plus 13 empty directories (including `/dev`, `/patch_hw`, `/second_stage_resources`).

`key_hits` outcomes **[P]**: `first_stage_init=1`; and **0** for each of `init_rc`,
`first_stage_rc`, `fstab`, `ueventd`, `selinux_policy`, `kernel_module`, `modules_load`,
`by_name`, `ufs`, `dm_verity`, `avb`, `logical_partition`, `erofs`, `mount_stage`,
`recovery`, `vendor_mount`. So: **no** init rc, **no** ueventd, **no** fstab file,
**no** `modules.load`/module list, **no** `.ko` in this archive.

### Reconciliation / module-loading route
- The missing standalone-ramdisk fstab is expected, not contradictory: the first-stage
  fstab is in the base FDT (work package A) **[P/R]**.
- ROUND21 established from `/init` symbols that `FirstStageMain` manually mounts
  `tmpfs` on `/dev`, performs mknod and uevent/coldboot to create block devices; it does
  not depend on devtmpfs **[R]**. This explains an empty `/dev` directory in the cpio.
- **The absence of `modules.load` in this archive does NOT prove modules are never used.**
  Comparison against authorized build evidence only: final `.config` has
  `CONFIG_MODULES=y` (line 919) while `CONFIG_DEVTMPFS is not set` (line 1952) **[P]**;
  ROUND20 established from the Image/build tree that the kernel is effectively
  monolithic — 0 `.ko` files, 0-byte `Module.symvers`, `modules_staging_dir.tar.gz`
  containing only `./`, yet `CONFIG_MODULES=y` **[R]**. Conclusion: for THIS built payload
  there is no out-of-tree module set to load; any alternate module-loading path (modules in
  vendor/system partitions or init configuration) is **not present in the authorized local
  corpus and remains UNKNOWN [U]** — it is not denied, merely unevidenced. No module list
  is inferred from the archive alone.

## 3. Work package C — vbmeta_cust anomaly provenance

### What is established locally
- File exists: `vbmeta_cust.img`, **1,048,576 B** (1 MiB), recorded in the ROUND2 partition
  inventory and selected-images SHA-256 list **[R]**. (Hash intentionally not republished.)
- Partition inventory row: `BOOT_OR_METADATA_IMAGE`, DIRECTORY-sourced, size 1 MiB **[R]**.
- ROUND19 `logs/avb_all.json` (self-written parser, read-only) **[P]** reports at file
  offset 0 a vbmeta **header** (release string `avbtool 1.2.0`, algorithm SHA256-RSA2048,
  one `hashtree` descriptor for partition `cust`, sha1 / 4096/4096 / fec 2, structure end
  at 1344 B, ~1 MiB trailing area) and flags one internal consistency problem:
  `public_key (224+520) exceeds auth size 320`. (No key/digest/salt values reproduced.)
- ROUND64 Phase F sanitized report and `logs/f2_avb_table.md` **[R]** report, using the
  pinned AOSP `avbtool.py` 1.4.0 in read-only `info_image` mode, that the file's **AVBf
  footer** points to a vbmeta blob at offset **10,375,168** — outside the 1 MiB file —
  which resolves to `Algorithm: NONE`, release `avbtool 1.4.0`, no descriptors; footer
  state was logged `UNPARSEABLE_OR_ABSENT` with original-image-size `10375168`. The
  root `vbmeta.img` chain declares a target named `vbmeta_cust` **[R]**.

### Reconciliation and verdict
The two observations are **different structures in the same file**, not a contradiction to
be "fixed": an offset-0 header/descriptor set (ROUND19 parser) and a footer at file end
whose target offset lies beyond the file (ROUND64 avbtool). Neither parser was pointed at
the other's structure by this round's evidence.

- **File length / inventory length:** 1 MiB, consistent across ROUND2 inventory and
  ROUND64 table **[P/R]**.
- **Partition table / manifest size or distinct source image explaining the out-of-file
  pointer:** none found in the authorized local corpus. The partition inventory records
  only the 1 MiB file size; no manifest entry, source-image record or larger vbmeta_cust
  object was located (WSL source tree has no `vbmeta_cust` reference; it is a firmware-side
  name) **[P]** — this is a negative search result in the searched scope, not proof of
  absence everywhere.
- **Complete vbmeta_cust object elsewhere:** none found in the authorized local corpus
  **[U]**.
- **Verdict:** the anomaly is **UNKNOWN**. The exact missing facts are: (a) whether a
  larger/complete `vbmeta_cust.img` exists in the source firmware package (and its true
  partition size), and (b) whether the vendor intentionally wrote an out-of-file footer
  pointer (e.g. a template/truncated extraction or a vendor layout variant). Per taskbook,
  no repair, reinterpretation, repack, or write-back was attempted; no key/signature/salt/
  digest/rollback field is published.

## 4. Work package D — Android boot-v2 packaging-tool source contract

**Tool present (provenance):** pre-installed executable
`prebuilts/kernel-build-tools/linux_musl-x86/bin/mkbootimg`, 22,851,365 B, mode 755,
in the pinned ROUND18 ACK tree **[P]**. Read-only `mkbootimg --help` (exit 0) shows it is a
PyInstaller-packed Python `mkbootimg` (the binary contains `runpy._run_module_as_main
("mkbootimg"...)` and `mkbootimg.pyc`), i.e. an AOSP `platform/system/tools/mkbootimg`
style implementation. A related trusted Rust source fork is present at
`bootable/libbootloader/gbl/libbootimg/mkbootimg/` with README "Fork of
platform/system/tools/mkbootimg with only the headers and Rust sources needed to interpret
a boot image" (TODO b/451913026) **[S]**. AOSP `system/core/mkbootimg/` and
`external/mkbootimg/` source directories are absent in this tree; no standalone
`mkbootimg.py`/`bootimg.py` exists (only the embedded `.pyc`) **[P]**. ROUND19/20 did not
use or download mkbootimg — they used a self-written parser **[R]**.

### Header-v2 capability — **[S]**
- `--help` exposes `--header_version HEADER_VERSION`, `--pagesize {2048,4096,8192,16384}`,
  `--kernel`, `--ramdisk`, `--dtb`, `--dtb_offset`, `--kernel_offset`, `--ramdisk_offset`,
  `--second_offset`, `--tags_offset`, `--os_version`, `--os_patch_level` — an explicit
  Android boot-header-v2 path with page-size/DTB/ramdisk options.
- The trusted Rust source `mkbootimg/rust/bootimg.rs` parses `boot_img_hdr_v0..v4` and
  `vendor_boot_img_hdr_v3..v4` and branches on `hdr.header_version` (`V0`, `V2`, `V3`,
  `V4`) **[S]**. The C++ header `include/bootimg/bootimg.h` defines `boot_img_hdr_v2`
  (derives from v1) with the page-aligned layout including `dtb_size`/`dtb_addr` **[S]**.

### Embedded kernel+ramdisk+DTB vs separate ramdisk partition — **[S]**
The tool builds **one boot image** containing kernel + ramdisk (and, for header v2, DTB)
as page-aligned sections selected by `--kernel`, `--ramdisk`, `--dtb`, `--header_version 2`.
It has no option that says "emit a boot image with an empty ramdisk because the ramdisk
lives in a separate partition"; `--ramdisk` is simply a path to the ramdisk payload to embed.
On this device the stock layout has both a `boot.img` carrying a ramdisk payload
(ROUND19: header v2, page 4096, kernel 22,264,379 B, ramdisk 519,986 B, dtb 1,664,243 B)
**and** a separate `ramdisk.img` partition (1 MiB AVB-wrapped, payload 1,322,962 B)
**[R/P]**. These are **separate boot inputs**; the tool can describe each image's
construction, but which one ABL actually consumes at boot is not a packaging-tool question
and is not established here **[U]** (see work package E).

### What the tool does not handle — **[S]**
- No general AVB footer / vbmeta placement, hashing, hashtree or descriptor management.
  The only signing-related options are GKI-specific (`--gki_signing_algorithm`,
  `--gki_signing_key`, `--gki_signing_signature_args`, `--gki_signing_avbtool_path`),
  which are a GKI signing helper, not a general "make this image AVB-valid" facility.
- No ABL selection policy, no slot/board-id choice, no boot acceptance decision.
Nothing in this section was executed to produce an image; only `--help` and source reads.

## 5. Work package E — actual ABL selection evidence

Searched only existing local reports/logs/configuration. Every relevant item is a
**negative/UNKNOWN** finding **[R/U]**:
- **Which of the nine DTBO entries HOS4.3 ABL selected:** no direct same-boot evidence.
  ROUND19/21 established nine board-id variants and that `0x206a` is a *candidate*;
  `0x206a` is explicitly "a candidate, not a fact", runtime selection UNKNOWN (ROUND21
  U-5) **[U]**.
- **Classic FDT vs EFI stub boot path:** ROUND20 proved the ACK Image *has* an EFI/PE-COFF
  entry and that the EFI path is kernel-side capable, but "Layer 3 — ABL invokes that
  entry" is UNKNOWN; no ABL binary/authoritative log was available (ROUND20 U-1/U-2,
  U-4: whether ABL publishes DEVICE_TREE_GUID and whether it decompresses gzip) **[U]**.
- **Whether HOS4.3 ABL accepts temporary/RAM boot for this exact device/build:** no direct
  evidence found in the authorized corpus. ROUND20's closest statement is an indirect
  capability note (stock kernel is gzip, so ABL must decompress) and that acceptance policy
  is ABL behavior with no ABL artifact available **[U]**.
- No HOS4.2 public report, board-id candidate or general kernel EFI capability was treated
  as proof. Device not contacted.

**Narrowest authoritative evidence required** (not available locally): an ABL image/boot
log from this exact HOS4.3 build, or a captured live FDT plus boot path indicator from a
single boot, sufficient to (a) name the selected DTBO index, (b) show whether the PE/COFF
EFI entry or classic FDT path was taken, and (c) show the boot-source/acceptance decision.
Until then these remain UNKNOWN.

## 6. Summary by work package

| Package | Verdict | Basis |
|---|---|---|
| A — first-stage fstab contract | PASS | Direct read of base FDT fstab node; 21 child entries, sanitized flag semantics (§1) |
| B — ramdisk & module route | PASS with UNKNOWN | cpio inventory direct; no modules.load in archive; alternate module path UNKNOWN, not denied (§2) |
| C — vbmeta_cust provenance | UNKNOWN | 1 MiB established; out-of-file footer pointer unresolved; no complete local object (§3) |
| D — boot-v2 tool contract | PASS | mkbootimg present with explicit header-v2/DTB/pagesize path; tool limits stated (§4) |
| E — actual ABL selection | UNKNOWN | Nine DTBO choice, FDT-vs-EFI path, RAM-boot acceptance all lack direct HOS4.3 evidence (§5) |

## 7. Boundaries and stop

No raw firmware, binaries, scripts, keys, signatures, salts, digests, rollback values or
private paths are included. No image/DTB/DTBO/vbmeta was created, modified, repacked or
signed. No device was contacted. Per the taskbook stop rule, this single report is the
deliverable; no other round, kernel/DTS change, build, packaging, signing or device action
was started.
