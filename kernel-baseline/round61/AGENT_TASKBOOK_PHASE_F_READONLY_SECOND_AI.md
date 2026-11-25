# ROUND61 Phase F — local Agent read-only boot-v2 and AVB evidence taskbook

**Issued by:** Second AI (ChatGPT GitHub-connected implementation agent)  
**Target:** Huawei MatePad 11 (2021), DBY-W09, HOS4.3  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Purpose:** Determine the exact stock HOS4.3 boot-v2 / separate ramdisk / DTBO packaging and AVB metadata using only already-approved local tools and existing local files.

## 0. Hard safety limits

This is a **local file inspection** task only.

Do NOT:
- install, download, compile or invoke an untrusted AVB parser or third-party inspection binary;
- extract, publish or upload raw stock boot, ramdisk, DTBO, vbmeta or other partition bytes;
- expose public keys, signatures, salts, digests, rollback indices or secret material;
- append/remove/modify an AVB footer, repack any image, edit vbmeta, patch boot or DTBO;
- execute fastboot, reboot, unlock bootloader, write partitions or modify device state;
- guess mkbootimg arguments, page sizes, offsets, alignment or partition sizes from another device/OS release.

Use only existing local HOS4.3 image files and a trusted AVB/image inspection utility already installed and approved in the authorized environment. If no such utility exists, stop and report BLOCKED. Do not write a parser or substitute an `AVB0` magic scan.

## 1. Establish stock image identity and layout

For each existing HOS4.3 local image (`boot.img`, separate `ramdisk.img` if present, `dtbo.img`, all vbmeta-related files identified by the trusted local inventory):
- record sanitized local path / inventory identifier, exact byte size, and SHA-256;
- record provenance/build fingerprint or firmware package revision where available;
- state whether the file is a whole partition image, extracted payload or container;
- retain originals unchanged and do not upload bytes.

### Boot header-v2 metadata

Using an already-available trusted image-header inspector/unpack tool in read-only mode, report only:
- Android boot image header version;
- page size;
- kernel, ramdisk, second-stage and DTB sizes as applicable;
- header cmdline length/presence (do not publish device-specific secret tokens or serial values);
- payload offsets/alignment and total image length;
- whether DTB is embedded in boot or supplied separately;
- any vendor boot / init_boot presence or confirmed absence.

For the separate ramdisk and DTBO partition, report exact file identity/hash/size and only the metadata needed to understand how ABL consumes them. Do not assume a modern vendor_boot/init_boot format.

## 2. AVB footer and descriptor inspection

Proceed only when an already-installed, trusted AVB parser (for example, an existing approved `avbtool` installation whose origin/version is known) is available.

For boot, ramdisk, DTBO and each vbmeta candidate, determine:
- whether a valid AVB footer is present, absent, or unparseable;
- if present, its footer version and original-image-size field;
- which vbmeta image authenticates the target image/partition;
- descriptor class only: hash, hashtree, chain partition, or other;
- target partition name and chain relationship;
- whether a separately stored ramdisk and DTBO are directly or indirectly covered;
- whether any relationship is missing, ambiguous or unverifiable.

Do **not** publish:
- public key bytes or key hashes;
- signatures;
- salts, image digests or hashtree root digests;
- rollback indexes/locations;
- raw vbmeta structures or image blocks.

A leading `AVB0` magic observation is NOT a parser result and cannot establish footer presence, descriptor coverage or a trusted chain. File sizes are not enough either.

## 3. DTBO and Huawei ABL selection metadata

Using only already-available trusted DTBO image inspection tools, report:
- DTBO container format/version/header identity;
- total entries and entry table shape;
- board-id / msm-id / custom selection fields and the sanitized values relevant to DBY-W09;
- whether the selected entry is established by HOS4.3 ABL evidence or remains unknown;
- if entry 8 is referenced, state explicitly that its 145 fragments target many Huawei vendor-only nodes and are not compatible with the minimal ACK board draft.

Do not repack a new DTBO, change entry ordering or assume a same-device HOS4.2 public reference describes this HOS4.3 ABL.

## 4. First-stage ramdisk and module-load evidence

Using already extracted local ramdisk files, report:
- ramdisk archive type and compression;
- presence and sanitized contents of first-stage fstab entries relevant to system/vendor/odm/super/dynamic partitions;
- first-stage init modules-load path, if any;
- kernel module directory path and `modules.load`, `modules.dep`, `modules.alias`, `modules.softdep`, `modules.options` presence;
- kernel release / page-size compatibility signals if available;
- EROFS, dm-linear, dm-verity/FEC and dynamic-partition mount expectations that can be traced directly to the fstab/init files.

Do not infer modules will load simply because the kernel has module support. The current storage-first port intentionally builds early UFS/PHY dependencies in; the actual first-stage mount chain must still be verified.

## 5. Required output report

Create a sanitized Markdown report at:

`firmware-analysis/round64/round64-dby-w09-hos43-bootv2-ramdisk-dtbo-avb-evidence.md`

Use these fields:

```text
Firmware build/revision:
Input inventory file list:
Existing trusted tool name/version/path:
Tool provenance:
boot.img SHA-256 / bytes:
boot header version:
page size:
kernel/ramdisk/DTB sizes and offsets:
separate ramdisk SHA-256 / bytes:
DTBO SHA-256 / bytes:
vbmeta file inventory (names/hashes/sizes only):
AVB footer state per image:
AVB footer original-image-size field:
Descriptor class / target partition / parent vbmeta:
Separate ramdisk and DTBO coverage:
DTBO container format and entries:
HOS4.3 ABL-selected entry:
First-stage fstab/module-load observations:
Unknown or ambiguous facts:
Evidence file paths and SHA-256:
```

Every field must be marked **PASS / BLOCKED / UNKNOWN / NOT_APPLICABLE**. State explicitly which claims come from actual parser output, which from local static inventory, and which remain unknown.

Do not upload raw firmware/images or secret AVB metadata. Upload only the sanitized report plus hashes and tool version outputs.

## 6. Stop and hand back

Stop immediately if:
- no trusted AVB parser is already installed and approved;
- the local image inventory is incomplete or identity cannot be tied to HOS4.3;
- a tool attempts to modify an image or access a device;
- descriptor coverage cannot be proven from the available vbmeta chain.

Do not install/download a replacement tool or write a custom parser to bypass the environment restriction. Return **BLOCKED** and identify the exact missing trusted tool or local input.

This taskbook does not authorize image repacking, ABL interaction, temporary boot, bootloader unlock, partition writes or flashing.
