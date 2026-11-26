# AI1 ROUND137 — DBY-W09 boot-v2 / ramdisk / DTB static contract audit

- Date: 2026-11-26
- Device: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Kernel baseline: ACK `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Fixed validated candidate tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- Purpose: move from the user's group-chat warning to a source- and artifact-grounded candidate boot-layout contract.
- Work type: public source review + existing sanitized HOS4.3 inventory reconciliation. No package creation, source/patch edits, ADB/fastboot, partition writes, or device tests.

## 1. Executive decision

The next safe architecture hypothesis is **not** "put the new ramdisk in boot" and **not** "skip all ramdisk". The same-device public DBY-W09 implementation demonstrates a more specific arrangement:

1. Preserve Android boot header v2 and the original boot image's embedded stock ramdisk bytes.
2. Replace the boot image's kernel and its header-v2 DTB section.
3. Put the new Linux initramfs payload in the independent `ramdisk` partition, not into the boot image's ramdisk section.
4. Keep DTBO as a separate partition and preserve the board-specific `/rootparam` requirement documented by the same-device project.

This is a **candidate model only**. The public implementation is a same-device Linux 7.0 / HOS4.2-era reference; it does not prove that the exact HOS4.3 ABL build used by this Android 17 port behaves identically. HOS4.3 ABL consumption, selected DTBO, AVB signing and rollback acceptance are still unproven. D remains BLOCKED for first Android 17 boot.

## 2. User-provided group-chat record

The verbatim group-chat excerpt is preserved separately:
[`USER_CHAT_RECORD_DBY_W09_ABL_BOOT_RAMDISK.md`](USER_CHAT_RECORD_DBY_W09_ABL_BOOT_RAMDISK.md).

Its statements are treated as an important lead, not a complete technical contract. In particular, "boot custom dt", "embedded DTB", and "ramdisk in boot" are ambiguous until the exact image section/partition is identified.

## 3. Direct same-device implementation evidence

Public repositories reviewed:
- `svesnav/linux-dby-w09`
- `svesnav/dby-w09-installer`

### 3.1 Python repacker

`repack_boot.py`:
- unpacks the original boot image with AOSP `unpack_bootimg.py`;
- rejects any header version other than 2;
- takes the unpacked mkbootimg flags as its base;
- optionally replaces `--kernel`, `--dtb`, and command line;
- does not replace the stock boot image's `--ramdisk` path.

Source: https://github.com/svesnav/linux-dby-w09/blob/main/repack_boot.py

### 3.2 The Android installer independently documents the same contract

The installer's `BootImage.java` parser/build code handles header v0–v2 and stores the kernel, ramdisk, recovery-DTBO and DTB sections independently. Its class comment explicitly states that the installer keeps every stock header field and the stock ramdisk, while replacing the kernel, DTB and command line. The build code serializes the sections separately and recomputes the image ID.

Source: https://github.com/svesnav/dby-w09-installer/blob/main/app/src/main/java/org/matepad/installer/core/BootImage.java

This is stronger than relying on the README alone: both a Python repacker and the Android installer implementation describe the same same-device boot-v2 layout.

### 3.3 Independent ramdisk and DTBO handling

`build_dev_images.sh` creates a new header-v0 ramdisk payload with an empty kernel and Linux initramfs as the ramdisk payload, then overlays it onto the separate stock `ramdisk` partition while preserving the AVB footer. It separately creates the boot-v2 image and DTBO image.

Source: https://github.com/svesnav/linux-dby-w09/blob/main/build_dev_images.sh

The installer's `boot-linux.sh` processes three independent partition images — `boot`, `ramdisk`, and `dtbo` — and checks the written bytes by readback hash before rebooting. This is evidence of the public project's actual partition-writing workflow, **not authorization to replicate it**.

Source: https://github.com/svesnav/dby-w09-installer/blob/main/app/src/main/assets/boot-linux.sh

### 3.4 ABL / DTBO rule

The same-device Linux README says the ABL-applied DTBO must fill `/rootparam` in the way the stock board overlay does; the wrong overlay causes return to fastboot. It also states that `fastboot boot` (RAM boot) is refused in that tested setup.

Source: https://github.com/svesnav/linux-dby-w09/blob/main/README.md

The repository's `dby-w09-rootparam.dtso` carries DBY-W09 board properties and a fragment targeting `&rootparam`. Its `pack_dtbo.py` wraps a supplied overlay into a DT table. These establish a same-device implementation lead, not proof of HOS4.3 runtime DTBO selection.

Sources:
- https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso
- https://github.com/svesnav/linux-dby-w09/blob/main/pack_dtbo.py

## 4. HOS4.3 stock image facts already in the repository

Source: ROUND64 Phase F sanitized report, branch `firmware-audit-v1`, blob `b1e27ce5ad37280ed4ed48f1560e10cfad332617`:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round64/round64-dby-w09-hos43-bootv2-ramdisk-dtbo-avb-evidence.md

| Artifact | Existing HOS4.3 observation | Relevance |
|---|---|---|
| `boot.img` | 96 MiB partition image; Android header v2; 4096-byte page; kernel 22,264,379 B at offset 4,096; embedded ramdisk 519,986 B at offset 22,269,952; embedded DTB 1,664,243 B; payload end 24,457,216 B | Boot has its own ramdisk section and DTB section |
| separate `ramdisk.img` | 2 MiB partition image; header v0; 2048-byte page; ramdisk 1,322,962 B; payload end 1,325,056 B | Independent ramdisk partition exists |
| `dtbo.img` | 24 MiB; DTBO v0; 4096-byte page; 9 entries | Runtime selected entry remains unknown |
| root `vbmeta.img` | Chain targets include `boot`, `ramdisk`, `dtbo` and additional partitions | Changes to any of these may require a valid authorized AVB/signing path |
| `vbmeta_cust.img` | 1 MiB; footer present but its reported original-image-size points outside the file; referenced blob reports Algorithm NONE/no descriptors | Anomaly remains UNKNOWN; do not repair/rebuild it |

The boot image section sizes/offsets and payload boundary are from prior-round local inventory cross-referenced in ROUND64; they were not re-parsed during this AI1 audit.

### 4.1 Calculated boot-v2 section boundary cross-check

Using 4096-byte page alignment and the ROUND64 section sizes:
- Header page: starts at 0, next section starts at 4,096.
- Kernel: 22,264,379 bytes, padded to 22,265,856 bytes; starts at 4,096; next section starts at 22,269,952.
- Embedded stock ramdisk: 519,986 bytes, padded to 520,192 bytes; next section starts at 22,790,144.
- Embedded DTB: 1,664,243 bytes, padded to 1,667,072 bytes; payload end is 24,457,216.

The calculated end exactly matches the ROUND64/AVB original-image-size inventory (24,457,216). This is a consistency cross-check of the existing measurements, not a new image parse.

The separate ramdisk payload is 1,322,962 bytes with page 2,048; its padded payload after the header page ends at 1,325,056, matching the ROUND64/AVB original-image-size inventory.

## 5. Pinned ACK 6.18.33 kernel FDT entry contract

AI1 directly inspected the fixed ACK source at commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.

### 5.1 arm64 direct-entry ABI

`arch/arm64/kernel/head.S` documents the arm64 boot requirement:
- MMU off;
- D-cache off;
- I-cache may be on or off;
- `x0` is the physical address of the FDT blob.

The same source preserves bootloader arguments and saves the original `x0` value as the kernel's FDT pointer.

Source: https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/kernel/head.S

### 5.2 Early kernel FDT validation

`arch/arm64/kernel/setup.c::setup_machine_fdt()` remaps the FDT and reports an invalid blob if it cannot be scanned. The source diagnostic explicitly states that the DTB must be 8-byte aligned and must not exceed 2 MiB. `setup_arch()` calls this function with the saved `__fdt_pointer`.

Source: https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/kernel/setup.c

### 5.3 R3 DTB size comparison

ROUND135 R3 built `qcom/huawei-dby-w09.dtb` at 108,648 bytes (SHA-256 `cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e`). It is below the ACK early FDT 2 MiB limit. This only satisfies the size side of the kernel ABI. It does **not** prove:
- ABL loads this DTB;
- ABL passes a correctly aligned physical pointer in `x0`;
- the FDT contains the final post-ABL memory / reservation / regulator state;
- the platform enters through classic arm64 direct boot or EFI stub.

The presence of a PE/COFF header in arm64 `head.S` is not proof that Huawei ABL invokes EFI stub. The actual entry route must be observed.

## 6. Distinguishing the two ramdisk meanings

The phrase "ramdisk cannot be put into boot because it causes duplicate boot" must be interpreted precisely.

- **New Linux initramfs payload:** the same-device public project puts this in the separate `ramdisk` partition, not the boot-v2 ramdisk section.
- **Original stock embedded boot ramdisk:** the same-device Python repacker and Android `BootImage.java` retain it as part of the stock boot-v2 structure.
- **Independent stock ramdisk partition:** the public project writes the new Linux initramfs there while keeping the boot-v2 stock ramdisk bytes.

Thus, do not add the same new initramfs to both boot-v2 ramdisk and the separate ramdisk partition. Also do not zero/delete the stock boot-v2 ramdisk field based only on a verbal summary. The actual HOS4.3 ABL precedence/consumption semantics are not yet observed.

## 7. ABL artifact availability lead

The existing `firmware-hos43/package_inventory.csv` (main branch, blob `9bf4f0885b523698ad3bb3b9bee46762bae5805d`) lists 43 firmware image entries. It includes `boot.img`, `ramdisk.img`, `dtbo.img`, `xbl.img`, `xbl_config.img`, `tz.img`, and `uefisecapp.img`, but contains no separately named `abl.img` / `abl.elf` entry. The inventory describes the already-extracted directory; it does not prove no ABL exists elsewhere in any source package or firmware bundle.

That gap motivates the next narrow local task: search only already-existing authorized local evidence directories for an ABL artifact or existing ABL/DTBO/kernel-entry trace. No new firmware extraction or device collection is authorized.

## 8. Decision matrix

| Statement / approach | Current evidence | AI1 decision |
|---|---|---|
| "ABL cannot use a custom DTB from boot" | Same-device public Python and Java implementations replace boot-v2 DTB section; exact HOS4.3 ABL version is unavailable | Not established as a blanket statement; keep HOS4.3-specific behavior UNKNOWN |
| "DTB must be embedded" | Public reference embeds DTB as the boot-v2 DTB section, separate from kernel bytes | Interpret "embedded" only as candidate boot-v2 DTB section until clarified; do not append to Image or enable built-in DTB on this wording alone |
| "new ramdisk cannot be put in boot" | Same-device public reference writes new initramfs to independent ramdisk partition, preserves stock boot ramdisk | Do not duplicate the new initramfs in both locations |
| "skip ramdisk" | Public reference does not skip the separate ramdisk partition | Reject as a default strategy |
| "ABL DTBO must fill /rootparam" | Same-device public project reports this as a tested bootloader rule | High-priority compatibility lead; still verify HOS4.3 selected entry and final FDT |
| "fastboot boot can be used for first test" | Same-device public README says RAM boot is refused | Do not plan on RAM boot without HOS4.3 evidence |

## 9. Immediate next task and stop conditions

Next task is a **WorkBuddy Agent local read-only availability audit** of already-existing HOS4.3 local evidence:
- search for an already-extracted `abl.elf`, `abl.img`, `abl.mbn`, `abl.bin`, or equivalent;
- search existing reports/logs for ABL build ID/version, DTBO selection, `/rootparam`, final FDT handoff, or boot entry mode;
- if an ABL artifact exists, record only sanitized relative path, size, SHA-256, file type and non-sensitive version/build strings using already-installed read-only tools;
- no binary upload, no firmware extraction, no device connection, no ADB/fastboot, no permission bypass.

If there is no ABL artifact or trace in the already-existing authorized corpus, report `BLOCKED — ABL ARTIFACT/TRACE NOT PRESENT` and stop. That is a useful result; do not invent a workaround.

No package creation, AVB manipulation, signing, partition writes, or boot testing is authorized. A/B/C/D remain BLOCKED for first boot until their respective target-local evidence is closed.
