# PREP03 — Hash-verified export of existing Android 17 bring-up package inputs

- Issuer / owner: **1号 AI (ChatGPT)**
- WorkBuddy Window A executor: **1号 Agent**
- WorkBuddy Window B executor: **2号 Agent** (not 2号 AI)
- 2号 AI: not needed at this stage; review can happen after AI1 has built the host-side preview.
- Device: Huawei MatePad 11 DBY-W09 / SM8250 / A-only
- Target: ACK Android 17 kernel 6.18.33 bring-up first; DerpFest Android 17 full ROM follow-up.
- HOS4.3.0.196(C00E100): boot-chain reference / current Android 12 vendor-userspace source only. This is not a HarmonyOS port.
- Task type: copy/export already-existing local binaries from each Agent's own workspace to private deliverable archives. **No device access, no rebuild, no flashing, no broad audit.**

## 1. Why this is the only Agent step needed now

AI1 has already implemented the host-side parser, boot-v2 builder, three-FDT slot composer, separate header-v0 ramdisk builder, CPIO/gzip packer and verifier. The synthetic tests pass. The actual kernel Image, frozen DTB and ROUND155 raw stock partition binaries are only present (or expected to be present) in the two separate local WorkBuddy workspaces. They cannot be reconstructed from hashes or report text.

Do not start a new audit round. Do not repeat any source review or device read. This is a deterministic artifact-export task only.

## 2. WorkBuddy Window A — 1号 Agent: export device-local reference binaries

Use **only Window A's own existing workspace**. Do not access Window B paths, sessions, caches or logs. Do not connect to the tablet.

Create one private archive named:

`PREP03_WindowA_Device_Inputs.zip`

Include these exact inputs if present:

| File in archive | Expected size | Expected SHA-256 | Purpose |
|---|---:|---|---|
| `stock-live-boot.img` | 100,663,296 B | `7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8` | exact ROUND155 live boot partition backup / boot-v2 template |
| `stock-live-ramdisk.img` | 2,097,152 B | `4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb` | exact ROUND155 separate ramdisk partition backup |
| `candidate-dby-w09.dtb` | 108,680 B | `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` | frozen candidate board DTB |
| `abl-hos43-pe.bin` | 2,597,064 B | `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404` | previously extracted HOS4.3 ABL payload for AI1 offline handoff analysis |

Optional, only if already in Window A's own workspace:
- `stock-package-boot.img` (firmware package reference, not interchangeable with the live partition copy), expected 100,663,296 B and SHA-256 `027f88fd6f318523925ca27a4d681d17a9bbca904b0c471ccc05e651d3da19b8`.

Requirements:
1. Verify exact bytes and SHA-256 before packaging; include `SHA256SUMS` and `provenance.txt` recording source report, local artifact identity and which files were unavailable.
2. Do not rename one ramdisk copy to impersonate the other. Do not substitute the ROUND64 package-reference ramdisk hash `5c20e4781f701e075ab30d3f8389172435e5591579bb5971f1b29331862fddc0` for the ROUND155 live hash.
3. If any expected file is missing, report it as missing; do not regenerate it, rebuild the DTB, reread the device, or search Window B.
4. Do not include raw vbmeta, keys, signatures, full firmware packages, user data or unrelated partitions.
5. Do not commit the archive or proprietary binaries to the public GitHub report repository. Return it as a private attachment to the user so it can be uploaded into this ChatGPT conversation.

## 3. WorkBuddy Window B — 2号 Agent: export successful frozen kernel binary

Use **only Window B's own existing workspace**. Do not access Window A paths, sessions, caches or logs. Do not rebuild the kernel.

Create one private archive named:

`PREP03_WindowB_Kernel_Inputs.zip`

Include:
- the successful frozen build's raw ARM64 kernel `Image`;
- an existing `Image.gz` or other compressed form only if it was already produced by that same successful build (do not create a new compression variant or assume which compression ABL expects);
- the exact accepted `.config` used for the successful build;
- `kernel-release.txt` (output of the built kernel's release identity, or the build record if the Image cannot be executed on the host);
- `build-provenance.txt` recording the exact build report/branch/commit, source-tree SHA, config SHA, Kleaf target, successful exit code, output paths, sizes and hashes.

Required source identity:
- ACK commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`
- candidate source tree SHA: `c56d93eafa35057d65176db6594d67d5144868a0`
- expected accepted config SHA from the frozen R140/R157 baseline: `efb663e9c792840e2cfbbc03e115996bb486aefe964b448c1717828c55bf042f`

Requirements:
1. Prove the binary came from the already-successful Window B build and the frozen candidate tree. If the local metadata differs, report the difference instead of silently substituting another build.
2. Record SHA-256 and exact size for every exported file; include `SHA256SUMS`.
3. Do not rebuild, recompress, patch, strip, or otherwise change the binary.
4. Do not include an unrelated `Image`, a failed Window A output, private credentials or signing keys.
5. Do not commit the kernel binary to the public GitHub report repository. Return it as a private attachment to the user so it can be uploaded into this ChatGPT conversation.

## 4. Stage distinction: do not mix the two package goals

**Stage 1 — ACK 6.18.33 kernel bring-up:** the immediate package goal is to test the new kernel against the currently existing DBY-W09 Android 12/HOS vendor/userspace baseline. If ABL/runtime evidence proves the relevant ramdisk placements, AI1 may build a host-only preview that keeps existing embedded and/or separate ramdisk bytes unchanged. This is a kernel bring-up strategy, not the DerpFest ROM and not a claim that HOS is the target OS.

**Stage 2 — DerpFest Android 17:** the later full-ROM package must use real DerpFest/Android 17 first-stage init, fstab, policy and target ramdisk content. Do not label a stock HOS ramdisk as the final Android 17/DerpFest ramdisk. Do not fabricate these files.

The exact ABL relationship among the boot image's 519,986-byte embedded ramdisk, the separate header-v0 ramdisk partition, and live `/chosen/linux,initrd-start/end` remains unresolved. Preserve the source files for comparison; do not decide placement yourselves. AI1 will inspect the actual binaries and decide the next host-side packaging operation.

## 5. Strict stop conditions

- No ADB, USB, fastboot, EDL, serial or live device access.
- No root commands, reboot, temporary boot, unlock, partition write, erase, format or flash.
- No new kernel build or DTB build.
- No AVB footer changes, vbmeta edits, signatures, key extraction or bypass.
- No cross-window workspace access.
- No public upload of raw proprietary firmware/kernel binaries.

## 6. Deliverables

Each Window returns exactly:
1. Its private ZIP attachment.
2. A short text summary with the archive SHA-256 and per-file sizes/hashes.
3. A list of any missing inputs and the exact local evidence for that absence.

Stop after export. AI1 will perform all subsequent image parsing, ramdisk placement analysis, package assembly, checksums and host-side verification. Only then will we decide whether any further local Agent work is genuinely necessary.
