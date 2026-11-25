# ROUND65 — HOS4.3 first-stage fstab, vbmeta_cust provenance and boot-tool contract audit

**Executor:** local WorkBuddy Agent; offline, read-only evidence review  
**Device:** Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250  
**Baseline:** ACK android17-6.18.33_r00 / common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Purpose:** continue the Phase F evidence work after ROUND64 without creating or modifying any boot artifact.

## 0. Existing inputs — reuse only

Use already-existing local work copies and inventory outputs from ROUND19–ROUND22 and ROUND64:
- decompiled HOS4.3 base FDT / `base_2.dts` if it is already present;
- `logs/boot_headers.json`, `logs/ramdisk_inventory.json`, `logs/dtbo_audit.json`;
- the existing firmware/partition inventory and any existing vbmeta_cust file/metadata;
- the pinned ACK source workspace already used for the Image build, especially `external/avb/avbtool.py`;
- the new ROUND64 Phase E and Phase F sanitized reports.

Do not re-extract firmware, resync source, copy new raw partition images, or deploy WSL.

## 1. Strict boundaries

- Read-only only. Do not edit source, DTS/DTBO, firmware, boot/ramdisk/vbmeta images, configuration, scripts or existing reports.
- Do not run a kernel build, Kleaf/Bazel, Kconfig regeneration, `mkbootimg`, `unpack_bootimg` or any image-generation command.
- Do not install or download tools. Use only tools already present in the authorized local workspace.
- Do not connect to the tablet or use ADB/fastboot/recovery, reboot, unlock, root, remount-write, flash or write partitions.
- Do not disable AVB, alter footer/vbmeta metadata, sign, repack or create a boot candidate.
- Do not publish raw firmware, raw DTB/DTBO/ramdisk/vbmeta data, keys, signatures, salts, public-key material, image/hashtree digests, rollback values, serials, MACs, IMEIs, account identifiers or private paths.
- If a fact cannot be established from already-existing authorized evidence, report UNKNOWN/BLOCKED. Never infer ABL behavior from board-id candidates.

## 2. Work package A — extract the first-stage fstab contract from existing evidence

The ROUND64 report says the first-stage fstab is located in the base FDT at `/firmware/android/fstab`, not in the standalone ramdisk.

From the already-decompiled base FDT or an existing structured inventory, report a sanitized table of:
- fstab entry / partition label;
- mount point;
- filesystem type;
- mount flags and fs_mgr flags relevant to first-stage mounting;
- whether the entry concerns super/dynamic partitions, system/vendor/odm/product, metadata, userdata or recovery;
- whether `avb`, `verify`, `avb_keys`, `logical`, `first_stage_mount`, `slotselect`, `latemount`, `wait`, `check`, `formattable`, `quota`, `fileencryption` or `fsverity` semantics are present.

Do not reproduce long raw property strings. Summarize only the semantics needed to understand root/system layout, dm-verity / hashtree, FEC and first-stage mount dependencies. Keep any absent flag explicitly absent; do not infer a disabled feature from a missing field unless the format defines that implication.

If the exact fstab cannot be read from an already-present decompressed source, report BLOCKED rather than extracting new firmware.

## 3. Work package B — ramdisk and module-loading route

Reconcile the existing ROUND64 ramdisk inventory with any already-existing local text inventory:
- identify whether `/init`, init rc, ueventd, fstab, module-load lists or kernel modules are actually present;
- check only already-existing local inventories for an alternate module-loading path (for example modules in vendor/system partitions or init configuration);
- report the exact evidence source for each conclusion.

The absence of `modules.load` in the standalone ramdisk does not prove that modules are never used. Do not infer that all drivers are built-in solely from this archive; compare only against the existing final `.config` and prior source/build evidence.

## 4. Work package C — `vbmeta_cust` anomaly provenance

Using only existing local metadata:
- confirm the file length / inventory length of `vbmeta_cust.img`;
- inspect whether the existing partition table or package manifest records a partition size or a distinct source image that explains the ROUND64 footer pointer beyond the 1 MiB file;
- check whether an already-existing complete vbmeta_cust object is present elsewhere in the authorized corpus;
- if no local evidence resolves it, retain UNKNOWN and record the exact missing fact.

AOSP avbtool may be used in read-only `info_image` mode only. Do not publish key/signature/salt/digest/rollback fields. Do not write output back into any image. Never repair or reinterpret the anomaly.

## 5. Work package D — Android boot-v2 packaging-tool source contract

Use only an already-present, trusted source or executable in the authorized workspace:
- check whether an existing `mkbootimg` source tree or executable is actually present, and record its provenance/version;
- inspect whether that exact version has an explicit Android header-v2 path and the relevant page-size / DTB / ramdisk options;
- determine whether it can describe a boot image with embedded kernel+ramdisk+DTB while the device also has a separate ramdisk partition, or whether those are separate boot inputs;
- state what the tool does **not** handle (especially AVB signing/footer placement and ABL selection) unless source proves otherwise.

Do not execute the tool, install it, download it, build it or generate a test image. A `--help` invocation is permitted only for an already-installed executable and must be read-only.

## 6. Work package E — actual ABL selection evidence

Search only existing local reports/logs/configuration for direct evidence of:
- which of the nine DTBO entries HOS4.3 ABL selected;
- whether the actual boot path used classic FDT or EFI stub;
- whether HOS4.3 ABL accepts temporary/RAM boot for this exact device/build.

A board-id candidate, an HOS4.2 public report or a general kernel EFI capability is not proof. If no direct HOS4.3 evidence exists, report UNKNOWN and identify the narrowest authoritative evidence required. Do not contact the device.

## 7. Deliverable

Upload exactly one sanitized UTF-8 report:
`firmware-analysis/round65/round65-first-stage-fstab-vbmeta-cust-and-boot-tool-audit.md`
to branch `firmware-audit-v1`.

The report must distinguish:
- direct parser output;
- facts reused from prior inventory;
- source-derived tool behavior;
- unknown/unavailable fields.

Do not upload raw firmware, binaries, scripts, or new extracted artifacts.

## 8. Stop rule

After the one report is uploaded, stop. Do not start another round, change the kernel/DTS, build, package, sign or contact the tablet.
