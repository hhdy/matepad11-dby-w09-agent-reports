# ROUND19 — HOS4.3 boot artifacts, all-DTBO memory handoff and Android first-stage inventory

**Owner:** local WorkBuddy Agent (read-only firmware analysis)
**Target:** Huawei MatePad 11 (2021) DBY-W09 / KONA / SM8250 v2.1
**Kernel baseline:** ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
**Purpose:** close the next offline evidence gaps after ROUND18 produced a real Image. This is NOT a repeat of ROUND7/8/12 and NOT a request to search public repositories.

## 0. Non-repeatable project context

The user has already confirmed that another developer privately brought up Android 17 DerpFest on this exact DBY-W09 with ACK/GKI 6.18.33. That private implementation is not going to be published. Do not search for it, ask for it again, or try to locate substitute public repositories. We must implement the missing pieces ourselves from the user's HOS4.3 evidence and pinned ACK source.

ROUND18 is complete:
- real ACK .33_r00 patch application and schema/config validation passed;
- real Kleaf Image build exited 0;
- Image size 44,820,992 bytes;
- Image SHA-256: `983b342ea5f0b48d5b9a808f37ba8405d92d283d1f9303a7c5054e26fbd8d884`.
This round must NOT repeat WSL deployment, repo init/sync, source/toolchain download, ROUND18 patch apply, Kconfig, or Image compilation.

## 1. Exact scope

Use only the existing local HOS4.3 firmware extraction/work copy and previously installed tools. The purpose is to determine the exact offline boot-image/ramdisk/AVB/DTBO facts needed to assemble a candidate boot package later, and to discover whether any stock overlay carries memory/EFI handoff changes.

Existing reports to reuse as starting points:
- ROUND2: stock image inventory and file sizes;
- ROUND3: validated FDT/DTBO extraction parser and source work copy;
- ROUND7: base boot FDT inventory;
- ROUND8: DTBO entry-8 fragment map and UFS/panel/rootparam evidence;
- ROUND12: AVB inspection was blocked only because no trusted AVB tool/helper was available then;
- ROUND18: pinned ACK workspace and successful Image output.
Do not rerun those rounds or re-extract the whole firmware package. Reuse their existing working copy, parser and exact source files.

## 2. Hard safety boundaries

Read-only analysis only:
- No ADB, fastboot, recovery, bootloader interaction, device connection or device reboot.
- No unlock, root, flash, partition write, `fastboot boot`, AVB disable, vbmeta modification, signing or packaging deployment.
- No modifications to the stock firmware images, existing work copies, ACK source workspace or other round reports.
- No software install, download, network access, security-policy change, command-policy bypass, shell/wrapper substitution or elevation.
- Temporary derived files and any new parser/tests must stay under a dedicated ROUND19 temp/work directory. Preserve original files byte-for-byte.
- Do not print or upload serials, MACs, IMEI, key material, private keys, salts, full digests, rollback values, or device-unique data. Hashes may be used locally for integrity checks but redact them from the report unless they are the already-public pinned kernel/Image identities above.
- If a required input is absent or an approved tool is blocked, mark that item BLOCKED/UNKNOWN. Do not search unrelated disks or repeat broad full-tree searches.

## 3. Work package A — inventory the exact boot chain images

From the existing ROUND2/ROUND3 work copy only, locate and record availability, byte size, container type and local integrity identity for:
- stock `boot.img`;
- stock `ramdisk.img`;
- stock `dtbo.img`;
- root `vbmeta.img` and all already-inventoried chained `vbmeta_*.img`;
- already-extracted ABL image/ELF, only if it is in the same existing extraction directory.

Do not treat a matching filename or an `AVB0`/`AVBf` magic alone as proof of AVB descriptor coverage.

## 4. Work package B — boot header v2 metadata

Use an already-installed trusted AOSP `unpack_bootimg.py` / `mkbootimg` utility if present. If absent, implement a small read-only Python header parser in the ROUND19 work directory; no downloaded code.

For `boot.img`, report:
- Android boot magic and header version;
- page size, kernel/ramdisk/second-stage/DTB sizes and offsets as encoded;
- header v2 DTB size/address fields;
- cmdline length only (redact actual command-line values that contain identifiers, tokens or unique device values; otherwise retain non-sensitive boot arguments);
- OS version / patch level fields;
- exact partition file size and payload end boundaries.

If the utility is available, produce an unpacked *temporary* metadata listing only. Do not repack or emit a candidate boot image in this round.

Also inspect the standalone ramdisk image header/version and identify whether its payload is a header-v0 image or another container. Separate facts read from the header from assumptions about how HOS4.3 ABL consumes it.

## 5. Work package C — ramdisk / first-stage inventory

Using tools already installed (for example `file`, gzip/lz4/xz/zstd, `cpio`, Python), determine:
- payload compression and CPIO format;
- whether `/init`, first-stage init scripts, fstab files, ueventd rules, init rc files and SELinux policy files are present;
- any storage-critical modules or module-load lists;
- references to `/dev/block/by-name`, UFS, dm-verity, AVB, logical partitions, EROFS, first-stage mount, recovery and vendor mount.
- whether the current ramdisk represents the HOS4.3 environment or has an evident Android-version mismatch; distinguish hard evidence from inference.

Only report file paths and relevant property/value names. Do not upload ramdisk contents, binaries, certificates or firmware blobs. Redact secrets and unique identifiers.

## 6. Work package D — AVB footer and vbmeta descriptor map

First detect whether a trusted AVB tool is already installed and already reviewed. If yes, use its read-only info/list operations and record exact commands and versions.

If no such tool exists, do not install/download one. You may implement a narrowly scoped read-only parser in the ROUND19 temp directory only if all of these are met:
1. parser reads byte arrays/files and never writes inputs;
2. parser validates bounds, lengths, reserved fields and integer overflows before following offsets;
3. parser supports AVB footer and vbmeta header parsing, and descriptor framing with safe unknown-tag handling;
4. parser reports only descriptor type, target partition name, image-size metadata and parent/chain relationship; do not output key bytes, key digests, salts, hash digests, signatures, rollback values or any other secret/security metadata;
5. synthetic unit fixtures cover valid footer, missing footer, truncated footer, valid vbmeta header, malformed block sizes, truncated descriptor and unknown descriptor tag; all malformed fixtures must fail closed;
6. parser output must be cross-checked against an independently available trusted tool if one already exists. If no independent implementation exists, mark parser-only conclusions PRELIMINARY and keep the corresponding packaging gate open.

Build a graph describing which vbmeta image (if determinable) covers `boot`, `ramdisk`, `dtbo` and other relevant partitions, whether coverage is hash vs hashtree, and any chained vbmeta partition names. If descriptors cannot be decoded confidently, state UNKNOWN rather than inferring from partition names.

Do NOT attempt signature verification unless a trusted already-installed tool supports it and it is strictly read-only. This round is metadata inventory, not AVB policy bypass.

## 7. Work package E — inspect all nine DTBO entries for boot/memory handoff deltas

Reuse the existing ROUND3 parser and extracted base DTB / all nine DTBO entries. Do not re-extract the firmware.

For each entry, inventory only nodes/properties that can change:
- root identity / board-id / msm-id;
- `/rootparam`;
- root-level memory nodes (`device_type = "memory"`, `reg`, `linux,usable-memory`);
- `/reserved-memory` and any changes to its children/properties;
- `/chosen`, including `bootargs`, `linux,uefi-system-table`, `linux,uefi-mmap-start`, `linux,uefi-mmap-size`, `linux,uefi-mmap-desc-size`, `linux,uefi-mmap-desc-ver`;
- memory-related ABL properties or bootconfig handoff nodes;
- UFS/PHY/panel/touch status or supply properties, only as a concise per-entry delta.

For all nine entries, report exact entry index, board-id tuple, fragment count and whether any memory/EFI/chosen/rootparam properties are added, changed or deleted. Pay particular attention to entry 8 (board-id 0x206a), but do not assume it is the selected overlay merely because it matches the product. Do not output RAM physical addresses or unique board identifiers in the report; use redacted ranges and indicate whether a complete map was internally observed.

The key question is whether any available stock DTBO can explain the missing root `/memory` node or create the EFI-stub `/chosen/linux,uefi-*` handoff. A negative answer must be limited to the nine extracted entries and exact inspected paths.

## 8. Work package F — ABL artifact triage (only if already extracted)

If an ABL binary is already present in the existing local extraction folder:
- record file type, architecture, container/ELF format and non-sensitive version strings;
- identify whether available symbol/section/string metadata contains explicit references to `/memory`, `linux,uefi-mmap`, `EFI_MEMORY_DESCRIPTOR`, DTB/DTBO overlay selection, `rootparam`, or EFI stub handoff;
- use only already-installed disassembly/string tools;
- no binary patching, no execution, no emulation and no new reverse-engineering framework installation.

Do not infer final runtime FDT or memory values from strings alone. This work package is optional and must not block completion of A–E.

## 9. Deliverables

Upload one sanitized UTF-8 report only:
`firmware-analysis/round19/round19_hos43_boot_ramdisk_avb_dtbo_audit.txt`
to branch `firmware-audit-v1`.

Report must include:
- a clear PASS / PARTIAL / BLOCKED status per work package;
- exact tools and versions;
- source file names and sizes;
- exact offsets/metadata only where safely useful;
- parser source and unit-test result if a parser was created;
- all nine DTBO entry findings;
- a boot/ramdisk/vbmeta coverage graph;
- explicit remaining UNKNOWNs and their exact evidence requirements.

Do not upload any binary or parser unless separately requested. Do not modify main, `ack18-dby-w09-dts-draft`, `ai-parallel/stagea-port-until-boot`, `ai-parallel/round54-ufs-review`, `ai-parallel/round58-kleaf-target-audit`, or PR #1.

## 10. Completion rule

Finish all offline work packages possible under the installed-tool and local-file constraints. Upload the report once, then stop. Do not wait for a future device session and do not claim that board DTB, boot image, AVB, memory handoff or real boot is complete.
