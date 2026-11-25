# ROUND20 — ACK Image EFI-stub capability and boot-v2 payload compatibility audit

**Owner:** local WorkBuddy Agent; read-only local artifact/source analysis  
**Target:** Huawei MatePad 11 (2021) DBY-W09 / KONA / SM8250  
**Fixed kernel:** ACK android17-6.18.33_r00, common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Prior milestone:** ROUND18 produced a real Image; ROUND19 completed HOS4.3 offline boot/ramdisk/AVB/9-DTBO audit.

## 0. Why this round exists

ROUND19 established:
- HOS4.3 base DTB has a root /memory node but its reg is an all-zero placeholder.
- None of the nine stock DTBO entries populates memory or adds /chosen/linux,uefi-* properties.
- There is no ABL binary in the existing ROUND2 extraction.
- Stock boot.img is Android boot header v2; stock kernel payload is about 22.3 MB.
- ROUND18 compiled ACK Image successfully at:
  /home/kerneldev/work/matepad11/ack-6.18.33-round18/bazel-bin/common/dby_w09/Image
  with sibling .config, System.map and vmlinux.
- Image size is 44,820,992 bytes. Do not rebuild it.

The key question is whether this exact Image includes the Linux EFI Stub and therefore has a valid PE/COFF EFI entry. That establishes a possible kernel capability for consuming UEFI memory-map metadata, but does not prove Huawei ABL actually invokes it. Also measure the exact stock kernel container/compression format and deterministic compression of the new Image, so boot-v2 payload-size feasibility is known without producing any boot image.

The user's same-device Android 17 DerpFest precedent is established project context. Its author will not open-source the implementation. Do not search public repos, ask for private sources, or revisit that question.

## 1. Non-repeatable boundaries

Do NOT:
- redeploy WSL, run repo init/sync, download source/toolchains or install anything;
- apply patches, alter the ACK workspace, change configs, rebuild Image or change .wslconfig;
- repeat ROUND18 schema/Kconfig/Image work or ROUND19 firmware/AVB/DTBO parsing;
- connect to the tablet, run ADB/fastboot/recovery, reboot, unlock/root/flash/write partitions;
- create, repack, sign, flash or deploy a boot image, or modify any firmware input;
- search public repositories or posts for the closed-source author's implementation.

Everything is read-only. Generated compression probes and logs stay under a dedicated ROUND20 temp directory. Existing Image/vmlinux/.config/System.map and firmware files must remain byte-identical.

## 2. Work package A — exact Image EFI / PE-COFF capability

Use the existing ROUND18 outputs only:
- .../bazel-bin/common/dby_w09/Image
- .../bazel-bin/common/dby_w09/vmlinux
- .../bazel-bin/common/dby_w09/.config
- .../bazel-bin/common/dby_w09/System.map

Record:
- CONFIG_EFI, CONFIG_EFI_STUB, CONFIG_EFI_ZBOOT if present, CONFIG_ARM64, CONFIG_OF and other directly relevant EFI/boot symbols.
- whether Image contains a PE/COFF header and EFI application subsystem; exact machine architecture and entry point if present.
- read-only results from installed file, objdump -x/-h, readelf -h/-S, or a small bounded Python PE header reader if tools do not expose required fields.
- whether vmlinux exports/contains efi_pe_entry, efi_stub_entry, efi_enter_kernel, efi_init, arm64 primary_entry and early DT/memblock initialization symbols. Symbol presence is capability/source evidence, not proof of runtime entry path.
- exact ACK source definitions for CONFIG_EFI_STUB and the arm64 EFI entry path by reading the already-synced pinned source tree (no network).

Verdict must distinguish:
1. EFI Stub compiled into this Image;
2. Image has a PE/COFF EFI entry;
3. ABL invokes that entry;
4. final FDT receives complete linux,uefi-* metadata.
Only the first two can be established offline from the Image. The last two remain UNKNOWN unless existing local evidence proves them.

## 3. Work package B — memory handoff route logic

From the same pinned ACK source tree and built Image, trace only:
- normal arm64 Image entry and early FDT memory scan;
- EFI-stub entry and where UEFI system-table / memory-map descriptors enter memblock;
- whether EFI-stub boot can proceed without a usable /memory/reg in the input DTB;
- exact /chosen/linux,uefi-* properties or EFI system-table handoff metadata consumed, and whether these are created by stub or must be supplied by bootloader;
- arm64 requirement for passing DTB pointer to stub/EFI entry.

Use exact source line references from the local ACK checkout. Do not infer Huawei ABL behavior from generic UEFI documentation. Conclude whether an EFI-capable Image gives a viable conditional workaround to the zeroed memory node, and list the exact ABL-side proof still missing.

## 4. Work package C — stock boot kernel payload format

Using the existing ROUND2 work copy only:
- locate the exact stock boot.img and isolate its kernel payload using ROUND19 header results;
- inspect first bytes, file result and already-installed compression/container recognizers;
- determine whether payload is raw arm64 Image, gzip, LZ4, XZ, zstd or another known wrapper;
- if compressed, verify decompressed data starts as a valid ARM64 Image header (magic at expected ARM64 Image header offset) and record uncompressed size;
- if not confidently classifiable, report UNKNOWN.
Do not upload or print kernel binary.

## 5. Work package D — deterministic compression size and boot-v2 capacity calculation

This is a size-only calculation, not packaging:
- read existing ROUND18 Image.
- create temporary compression output under ROUND20 temp directory using installed gzip only, with deterministic settings (e.g. gzip -n -9; optionally gzip -n -1 as speed/size comparison). Never overwrite Image.
- measure raw Image, compressed Image, stock kernel payload, stock embedded boot ramdisk and DTB sizes.
- calculate candidate boot-v2 payload ends:
  (i) raw Image + existing stock embedded boot ramdisk + existing stock DTB;
  (ii) gzip Image + existing stock embedded boot ramdisk + existing stock DTB.
- compare each only with 96 MiB partition capacity and stock footer original_image_size; explicitly state physical partition fit does not preserve AVB validity or imply ABL acceptance.
- do NOT copy any AVB footer/vbmeta into a candidate or write a boot image. Do NOT create a candidate boot image.
- state gzip requirement only if established by stock payload / ABL evidence; otherwise label compatibility unverified.

## 6. Work package E — first-stage storage prerequisites cross-check

Use ROUND19 findings and local pinned ACK source/config only:
- list built-in storage-critical driver/config gates already satisfied by ROUND18 (UFS, QMP UFS PHY, SM8250 GCC/RPMhPD/ICC, SMMU, DM/verity/EROFS).
- verify from current output tree whether compiled Image is monolithic built-in for those drivers or relies on .ko modules. ROUND18 reports no module_outs and no .ko artifact; verify without rebuilding.
- compare with ROUND19 ramdisk inventory: no modules.load, no modules, no text fstab, first-stage logic in /init, DT fstab at /firmware/android/fstab.
- note remaining boot-critical unknowns: effective DTB/UFS node state, PMIC parent-supply, ARC/proxy handoff, selected rootparam overlay, memory handoff, AVB.

Do not generate or modify board DTS in this round.

## 7. Deliverable

Upload one UTF-8 text report only:
firmware-analysis/round20/round20_efi_stub_memory_handoff_and_boot_payload_compatibility.txt
to branch firmware-audit-v1.

Include:
- PASS / PARTIAL / BLOCKED per work package;
- exact source paths and line ranges;
- exact tool versions;
- EFI/PE entry verdict and memory-route decision tree;
- stock kernel payload format and new Image raw/gzip size comparison;
- boot-v2 size arithmetic for both scenarios;
- explicit distinction between Image capability and ABL behavior;
- remaining unknowns and exact evidence requirements.

Do not upload source, binaries, Image, vmlinux, config, firmware content or parser.

## 8. Completion rule

Complete all work possible using existing local files and installed tools. Upload the single sanitized report, then stop. Do not wait for device access and do not claim any DTB/boot package/AVB/real-boot milestone.
