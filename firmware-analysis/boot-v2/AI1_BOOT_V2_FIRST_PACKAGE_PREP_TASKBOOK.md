# PREP-BOOTV2-01 — Android 17 target boot package preparation using the HOS4.3 device boot-chain baseline (Window A)

- Issuer / owner: **1号 AI (ChatGPT)**
- Executor: **WorkBuddy Window A / 1号 Agent**
- Independent reviewer: **2号 AI**, only after Window A publishes the final evidence (do not assign this task to Window B / 2号 Agent)
- Device: Huawei MatePad 11 **DBY-W09**, SM8250. Current stock firmware used as the reference baseline: HOS **4.3.0.196(C00E100)**.
- **Actual target OS: Android 17 (ACK 6.18.33 kernel bring-up first), followed by DerpFest Android 17. This task is not a HarmonyOS port.**
- Scope: offline analysis of already captured local backup files and existing build outputs; no device connection required
- Status: taskbook only; no image or partition is approved for temporary boot or flashing

## 0. Objective

Establish the exact *device bootloader/partition packaging contract* for this physical device. HOS4.3 is only the currently installed donor/reference firmware that supplies the stock partition samples and ABL binary. The deliverable being prepared later is an **Android 17 target package**, not a HarmonyOS package. Use the HOS4.3 backups only to discover the formats and constraints ABL expects. Determine how a future host-built Android 17 candidate must fit that contract, including:

1. the stock `boot` partition's on-device container/header format and payload boundaries (reference only);
2. the stock separate `ramdisk` partition's container/footer format and its role in the boot chain (reference only);
3. the frozen Android 17 ACK kernel candidate and frozen device base DTB;
4. the frozen one-entry ROUND159 device DTBO component;
5. an **Android 17-compatible target ramdisk/initramfs and required boot configuration**, which must come from the target Android 17 build/source and must not be copied from the HOS4.3 stock ramdisk;
6. ABL-provided kernel command line, FDT `/chosen` fields, and initrd placement;
7. the existing AVB/vbmeta/Huawei OEM acceptance chain.

This is an evidence-extraction and host-only reproducibility task. It is **not** a HarmonyOS image rebuild, not a boot attempt, not an image-writing task, and not permission to change AVB/security state. The stock HOS4.3 kernel/ramdisk payloads are used only for parsing and round-trip tests; they are not the Android 17 target payloads. Do not substitute the HOS4.3 stock ramdisk for the Android 17 target ramdisk.

## 1. Immutable project anchors

Do not change any of these anchors during this task.

| Item | Frozen identity |
|---|---|
| Device / firmware | DBY-W09 / HOS 4.3.0.196(C00E100) / SM8250 |
| ACK source | `android17-6.18.33_r00` |
| Pinned upstream kernel commit | `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9` |
| Candidate source tree SHA | `c56d93eafa35057d65176db6594d67d5144868a0` |
| Candidate DTB | 108,680 B; SHA-256 `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` |
| Frozen stock DTBO partition backup | 25,165,824 B; SHA-256 `51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c` |
| Extracted HOS4.3 ABL PE payload | 2,597,064 B; SHA-256 `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404` |
| ROUND159 frozen DTBO table | 442 B; SHA-256 `f185c13de5f9d2ca8dc2610c4cef33d12db601bfa29bae079fb5827951c1a6cc` |
| ROUND159 frozen overlay FDT | 378 B; SHA-256 `5d596c2e38d18d71ebe6cee3a77617a9185ab13a941b995e57e75d8fc6ae7ea3` |

ROUND159 final integration report:
`kernel-baseline/round159/AI1_ROUND159_FINAL_COMPONENT_INTEGRATION_REVIEW.md`
AI1 integration commit: `bac7f000485c84681bc173f3817e347f54a02005`.

Do not rebuild or edit the kernel, candidate DTB, or ROUND159 DTBO. Do not introduce a second DTBO candidate.

## 2. Source files and backup provenance

Use the local copies already captured in ROUND155 and later rounds. Do not read from the live tablet.

1. Locate the exact ROUND155 backup manifest and all existing backup-copy verification logs.
2. Identify the exact local files corresponding to the physical device's `boot`, `ramdisk`, `vbmeta`, `vbmeta_cust`, `dtbo`, and any other directly chained boot partitions (names must come from the actual partition manifest; do not guess).
3. For every input file record: original device partition label, exact byte size, SHA-256, backup timestamp/source, and whether a second independent copy exists and matches.
4. Reconcile the file hashes with the ROUND155 report. If a copy differs, stop using that copy and report the discrepancy.
5. Locate the frozen candidate kernel output from the successful Window B build. Record the exact file path, compression format, size, SHA-256, kernel release, build config SHA, and source-tree identity. Do not silently substitute Window A's OOM-interrupted output.
6. Locate the frozen 108,680-byte candidate base DTB and verify its hash before using it.

If a required input is absent or the original backup cannot be hash-verified, do not connect the tablet to fill the gap. Report the exact missing item and stop that subtask.

## 3. Parse the stock `boot` partition as a device-format reference

Use a pinned, identified Android boot-image parser/unpacker. Record the tool name, version/commit, and exact command. Do not rely on an undocumented local script.

Parse the actual stock HOS4.3 `boot` backup solely to learn the container and loader contract. Report all fields, including:

- partition byte size and whole-partition SHA-256;
- magic and header version (verify; do not assume version 2 merely from a project note or another port);
- page size, header size and every payload offset;
- kernel size, load address, payload hash and compression/magic;
- ramdisk size, load address, payload hash (including whether it is empty);
- second-stage size/address, if any;
- tags address;
- OS version and patch level fields;
- board/name field;
- complete command line, including both command-line areas where applicable;
- image ID and independently recomputed digest;
- recovery-DTBO size/offset, if present;
- DTB size/load address and payload hash, if present;
- any bytes between the parsed payload and partition end, separately classified as padding, AVB footer, vbmeta data, or unexplained bytes.

Do not label all remaining bytes as AVB without parsing. Use exact offsets and show the arithmetic that bounds every payload within the partition.

## 4. Parse the stock `ramdisk` partition as a device-format reference

Determine its actual on-disk format from the backup bytes; do not assume it is raw gzip/cpio or a header-v0 Android boot image.

Report:

- exact partition size and SHA-256;
- leading magic and all format/header fields;
- whether the ramdisk partition contains an Android boot-image header, compressed archive, raw cpio, or another format;
- inner ramdisk payload start/end, size, compression format and SHA-256;
- any AVB footer (`AVBf`) or vbmeta structure, with exact byte offsets and parsed footer fields;
- unused/padding ranges and their exact lengths;
- whether the stock `boot` image's embedded ramdisk is empty, duplicate, or used in addition to this separate partition.

If the device uses a different partition label or additional boot-chain partition, document the actual layout instead of forcing it into a `boot` + `ramdisk` assumption. Do not substitute `recovery_ramdisk` for `ramdisk`.

## 5. Host-only stock-reference round-trip reconstruction

This step proves the parser/packer combination understands the **actual stock reference images**. It does not build the Android 17 target package.

1. Unpack the stock `boot` backup to a temporary host directory.
2. Repack it with the exact parsed header values and original payloads.
3. Compare the reconstructed boot-image payload to the original payload byte-for-byte, excluding only explicitly identified footer/partition-tail ranges. If the packer cannot reproduce it exactly, explain every field or padding difference.
4. Reconstruct the separate ramdisk payload/container in a temporary directory and compare the meaningful bytes with the original.
5. Run an independent second parser over each reconstructed file.
6. Preserve all logs, commands, tool versions, offsets, and hashes.

This is a **round-trip test using original HOS4.3 reference payloads only**. Do not substitute the candidate kernel, candidate DTB, or Android 17 target ramdisk in this validation step. Do not produce a purported flashable image. Do not write anything to a device.

## 6. ABL boot handoff and FDT `/chosen` contract for the Android 17 payload

Use only the extracted HOS4.3 ABL payload whose SHA-256 is pinned above, plus the already captured ROUND151 live FDT. Static binary findings must be labeled static evidence, not runtime proof.

Known runtime evidence from ROUND151 (must be rechecked against its report/file if available):

- live FDT SHA-256: `fefeaa049f64a9cc79f0aa7558883f7a31ba98cf0ad73f541834c0ec2d46b700`;
- live `/chosen/linux,initrd-start = 0xf0000000`;
- live `/chosen/linux,initrd-end = 0xf015749a`;
- live stock `androidboot.dtbo_idx=2`;
- candidate one-entry DTBO is expected to select index 0 in static ABL selector analysis, not index 2.

Required analysis:

1. Identify ABL references/paths for loading the boot image, loading any separate ramdisk partition, and extracting kernel/DTB/initrd payloads.
2. Locate the logic that creates or updates `/chosen/bootargs`, `linux,initrd-start`, and `linux,initrd-end`. Explain whether these properties are derived from partition bytes, fixed addresses, boot-image header values, or another source.
3. Compare the live FDT values with the stock ramdisk payload length and all relevant boot-time address fields. Explain whether the known `0xf0000000..0xf015749a` range is consistent with the captured stock ramdisk and its format.
4. Determine what the ABL expects when the candidate base DTB has an empty `/chosen`. Do not add `/chosen` fields to the DTB merely to make the file look complete; do not change the DTB.
5. Record the complete stock command-line sources and precedence: boot image header, ABL additions, DTB `/chosen/bootargs`, and any other observed source. Separate confirmed behavior from hypotheses.
6. Reconcile the ABL's actual RAM-map rewrite behavior with the previously captured live FDT. Do not assume the candidate's static `/memory/reg` tuples will survive.

Use exact disassembly addresses, string references, control-flow evidence, and relevant raw bytes where possible. If static analysis cannot prove a behavior, state exactly what remains unknown.

## 7. AVB / Huawei acceptance analysis for modified Android 17 payloads — read-only only

Inspect the already backed-up originals for `boot`, `ramdisk`, `dtbo`, `vbmeta`, `vbmeta_cust`, and all identified chained boot partitions.

Use `avbtool info_image` / verification commands or an equivalent independently identified parser. Record:

- which images contain AVB footers/descriptors and exact footer offsets;
- hash/hashtree descriptors and which partition each descriptor authenticates;
- public-key algorithm and public-key digest (never output private keys);
- rollback index and rollback index location;
- chained vbmeta relationships, flags and partition names;
- whether `vbmeta` flags value 3 has only the standard HASHTREE_DISABLED / VERIFICATION_DISABLED meaning in the parsed structure, and what checks remain outside those flags;
- whether modified `boot`, `ramdisk`, or DTBO could be authenticated with any legitimately available signing key.

Do not disable verification, edit vbmeta flags, remove or forge AVB footers, patch ABL/TZ, bypass OEM signatures, or attempt a modified-image signature. Do not generate or request private signing keys. If the existing chain requires an unavailable OEM signature, call that an explicit package blocker.

## 8. Strict prohibitions

- No ADB, fastboot, EDL, serial, USB, or live-device commands.
- No reboot, temporary boot, bootloader-mode transition, partition write, flash, erase, format, or unlock operation.
- No changes to device state or partitions.
- No changes to kernel source/config, candidate DTB, DTBO, ABL, vbmeta or firmware files.
- No reuse of metadata from HOS4.2, other DBY variants, or any public port. In particular, do not copy another project's board-id, `qcom,boardid`, board name, `modem_id`, load addresses, page size, partition sizes, hashes, or AVB layout. Current HOS4.3 exact DTBO facts are only those frozen in ROUND159.
- Do not claim a boot image is accepted merely because it parses, round-trips, or has vbmeta flags 3.
- Do not call a host-built image bootable, flashable, or ready for the tablet.

## 9. Required deliverables

Publish on a new Window A branch, without rewriting AI1/AI2 branches:

1. `firmware-analysis/boot-v2/WORKBUDDY_A_BOOT_V2_LOCAL_EVIDENCE_REPORT.md`
   - concise executive status;
   - exact backup provenance;
   - boot and ramdisk header/partition tables;
   - payload offsets, lengths and hashes;
   - host-only round-trip commands and result;
   - ABL / `/chosen` findings with evidence grade;
   - AVB chain map and signer feasibility;
   - unresolved blockers and concrete next action.
2. `firmware-analysis/boot-v2/boot-v2-stock-image-facts.json`
   - machine-readable parsed header, offsets, hashes, partition sizes and AVB footer/descriptor metadata.
3. Minimal parser/round-trip scripts and raw logs needed to reproduce the findings. Do not commit Huawei stock partition images, proprietary binaries, private keys, certificates, or large firmware dumps.
4. A SHA-256 manifest for the new report, JSON, scripts and logs.
5. Commit and push the report branch, then provide branch name, commit SHA, report path and key result.

## 10. Final result must answer these exact questions

1. What exact container/header and payload constraints must an Android 17 candidate respect in the device's `boot` partition?
2. What exact format/container and placement does the device expect for a separate `ramdisk` partition, if confirmed?
3. Does ABL consume an embedded boot ramdisk, a separate ramdisk partition, or both—and what is the evidence?
4. What exact ABL behavior creates the live initrd range and the `/chosen` properties, and how must Android 17 supply the corresponding payload?
5. Can the original HOS4.3 reference images be unpacked/repacked byte-for-byte over the meaningful payload region with the identified tools?
6. Which AVB/OEM checks authenticate the modified Android 17 components, and is there a legitimate signer available?
7. Is there enough evidence to begin **host-only Android 17 candidate package assembly**, or is there a specific blocker that must be closed first?
8. What exact next task is necessary? Do not create a broad new audit cycle.

**Expected end state:** an exact, device-derived boot-chain/package specification for the **Android 17 target**, plus a GO/NO-GO decision for offline Android 17 candidate package assembly. HOS4.3 contributes only the stock boot-chain reference evidence; the eventual target payload is Android 17, then DerpFest Android 17. This task does not authorize temporary boot or partition flashing.
