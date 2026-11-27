# AI1 Android 17 Package Tooling — PREP01

- Date: 2026-11-27
- Owner: 1号 AI (ChatGPT)
- Target: DBY-W09 Android 17 ACK 6.18.33 bring-up, then DerpFest Android 17.
- Reference-only firmware: HOS 4.3.0.196(C00E100). This is not a HarmonyOS port.

## Completed by AI1 without Agent

AI1 prepared a host-side package utility and tests in the companion archive `Android17_Boot_Package_Tools_PREP01.zip`.

Implemented:
- Android boot-image header v0-v2 inspection and section extraction.
- v2 boot payload preview assembly from a supplied stock template, replacing target kernel/DTB while preserving the template's board/header/address/command-line metadata and optional second/recovery-DTBO sections.
- Strict refusal to silently carry a non-empty HOS embedded ramdisk into Android 17. Caller must supply a target Android 17 ramdisk or explicitly clear the embedded ramdisk after ABL handoff is established.
- v0 separate ramdisk wrapper preview from a confirmed empty-kernel v0 template.
- SHA-256 accounting, AOSP boot image-ID recomputation, AVB footer metadata detection, and verification of the frozen one-entry ROUND159 DTBO table/FDT content.
- Seven synthetic unit tests; all pass.

The actual frozen 442-byte ROUND159 candidate DTBO table was obtained from Window B's final branch and verified locally:
- Size: 442 bytes
- SHA-256: `f185c13de5f9d2ca8dc2610c4cef33d12db601bfa29bae079fb5827951c1a6cc`
- One dt_table entry, 378-byte FDT payload
- Root selector: `qcom,board-id=<0x200e 0>`
- Static resulting `dtbo_idx=0`
- All five exact HOS4.3 `/rootparam` properties match the frozen ROUND159 facts.

## Why the final Android 17 image is not emitted yet

The active runtime does not contain the actual binary inputs needed for a real image:
1. the successful frozen Window B kernel Image/Image.gz;
2. the candidate DTB binary matching SHA-256 `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60`;
3. the verified local ROUND155 stock boot/ramdisk/vbmeta backup files and exact partition metadata;
4. an Android 17 target ramdisk/initramfs.

The HOS4.3 boot/ramdisk images are reference templates only. The HOS ramdisk must never be substituted for the Android 17 target ramdisk. The 442-byte DTBO table is a component, not a full AVB-authenticated DTBO partition image.

## Safety / acceptance

The companion utility emits host payload previews only. It does not generate AVB descriptors, Huawei OEM signatures, modify vbmeta, or prove ABL acceptance. No device command, reboot, temporary boot or partition write was performed.

The next offline assembly can proceed as soon as the required kernel/DTB and local reference backups are available. Agent involvement is deferred until local workspace access is actually required.
