# AI1 Android 17 boot-package tooling — PREP03

- Date: 2026-11-27
- Owner: 1号 AI (ChatGPT)
- Device: Huawei MatePad 11 DBY-W09 / SM8250 / A-only
- Target: Android 17 ACK 6.18.33 kernel bring-up first; DerpFest Android 17 follow-up.
- HOS4.3.0.196(C00E100) is a device boot-chain reference and current Android 12 vendor/userspace baseline only, not the ROM target.

## 1. Tool archive delivered

- Archive: `Android17_Boot_Package_Tools_PREP03.zip`
- SHA-256: `2ae2338aa9270f61b7df472d99ede06d00c34acee7f4e173aa9a0c8e8bd527e1`
- Contents: host-only boot-image/ramdisk parsers and builders, DTB-slot composer, frozen ROUND159 DTBO component, deterministic CPIO+gzip packer, JSON input manifest, checksums and tests.

## 2. New capability in PREP03

- Added explicit `--preserve-template-ramdisk` mode to the boot-v2 builder.
- The option preserves the embedded ramdisk bytes from the supplied stock template byte-for-byte and labels that source in the output JSON.
- Replace / preserve / clear modes are mutually exclusive.
- This is for the **Stage 1 ACK 6.18.33 kernel-only bring-up preview** on the existing device-matched Android 12/HOS vendor/userspace baseline, if ABL handoff and first-stage mount compatibility support it.
- It does not represent a DerpFest Android 17 image. **Stage 2 DerpFest must use genuine DerpFest/Android 17 first-stage init and ramdisk content.**
- The separate ramdisk partition may likewise be preserved byte-for-byte for Stage 1 only after ABL load/handoff is established. AI1 will not guess whether the embedded and separate ramdisks are both used.

## 3. Implemented capabilities

- Android boot header v0-v2 parser, bounded payload validation, section extraction, AOSP boot image ID recomputation, AVB footer metadata inspection (read-only).
- v2 boot payload builder that preserves device header metadata/load addresses/cmdline, replaces kernel and DTB, page-aligns sections, and explicitly replaces, preserves or clears embedded ramdisk.
- DBY-W09 DTB slot composer: candidate 108,680B FDT + stock Kona v2/v1 fallback FDTs + exact 173-byte tail; expected size 1,216,399B at `dtb_addr=0x1f00000`.
- Candidate FDT first-stage fstab presence check at `/firmware/android/fstab`.
- Separate Android boot header-v0 ramdisk builder and gzip/CPIO newc inspector.
- Deterministic root-owned CPIO newc + gzip packer from a real supplied target ramdisk tree; does not fabricate `/init`, fstab, policy, modules or SELinux labels.
- Frozen ROUND159 one-entry DTBO verifier; real 442B component included and exact-hash verified.

## 4. Verification

- `python -m py_compile`: PASS.
- Synthetic unit tests: **18/18 PASS**.
- Frozen ROUND159 DTBO component: PASS; exact SHA-256 `f185c13de5f9d2ca8dc2610c4cef33d12db601bfa29bae079fb5827951c1a6cc`.
- These are host synthetic/unit and component checks, not a fresh parse of the unavailable local raw backups and not a device boot test.

## 5. Actual inputs still needed to emit a real kernel bring-up preview

1. Window A local exact ROUND155 live `boot` partition file: 100,663,296B, SHA-256 `7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8`.
2. Window A local exact ROUND155 separate `ramdisk` partition file: 2,097,152B, SHA-256 `4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb`.
3. Window A frozen candidate DTB: 108,680B, SHA-256 `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60`.
4. Window B successful frozen kernel Image (and an already-existing compressed variant only if present) plus config/build provenance.
5. Window A previously extracted ABL PE payload (2,597,064B, SHA-256 `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`) for AI1's final offline ramdisk-handoff analysis.

The exact runtime relation between boot's 519,986B embedded ramdisk, separate v0 ramdisk, and live `/chosen/linux,initrd-start/end` remains unresolved. The candidate DTB's fstab presence must be inspected from the actual binary. No placement or removal will be guessed.

## 6. Narrow next action — no new audit round

PREP03 taskbook asks:
- WorkBuddy Window A / 1号 Agent: export only its existing boot/ramdisk/candidate-DTB/ABL binaries, hash-verified.
- WorkBuddy Window B / 2号 Agent: export only its existing successful kernel Image and provenance, hash-verified.
- No device reads, rebuilds, new tests, cross-window workspace reads, or public repository uploads of proprietary binaries.

Taskbook:
`firmware-analysis/boot-v2/AI1_PREP03_HASH_VERIFIED_BINARY_EXPORT_TASKBOOK.md`

AI1 will then perform all host parsing, DTB composition, boot-v2/ramdisk preview assembly, hash checks and package manifest generation. Further Agent work is deferred unless a concrete local-only blocker remains.

## 7. Acceptance boundary

No full 96 MiB partition image, AVB footer/signature, vbmeta edit, Huawei OEM signature, or flashable package is created. No device commands, reboot, temporary boot, partition write or flash were performed. The host package preview is not proof of ABL acceptance.

**Current status: tooling PREP03 ready; waiting only for private binary export to assemble the Stage 1 ACK-kernel bring-up preview. Stage 2 DerpFest image requires its own target system/ramdisk inputs.**
