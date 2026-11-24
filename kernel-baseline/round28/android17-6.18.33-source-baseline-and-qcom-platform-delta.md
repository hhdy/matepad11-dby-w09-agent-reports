# ROUND28 — ACK/GKI 6.18.33 source baseline and Qualcomm platform-delta strategy

Date: 2026-11-24

Status: public-source review only. No local firmware access, no compile, no patch application, no DTS validation, no device operation and no partition write.

## 1. Decision

For the current Stage A kernel port, pin the Android Common Kernel tag:

- `android17-6.18.33_r00`
- Official tag page: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00
- Tag target commit shown by the official page: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Tag object: `369fecee1ecf4c78af4889640c618cc9a19f3921`

This is the precise Android Common Kernel (ACK) reference for the requested Android 17 / 6.18.33 line. Do not substitute:
- the pure upstream stable Linux `v6.18.33` tag (different git history and no Android common patches); or
- the DerpFest manifest's generic June 2026 `android17-6.18-2026-06` kernel branch, whose documented release baseline is 6.18.21; or
- the September 2026 certified GKI release branch, documented as 6.18.32.

The user-requested 6.18.33 target remains unchanged.

## 2. Important version distinction

There are three different identifiers in public sources:

| Identifier | What it is | How this project uses it |
|---|---|---|
| Linux stable `v6.18.33` | Upstream stable kernel tag, commit `83657f4189612e5cbcabc3058acd36c0bd120729` | Reference only; not a substitute for ACK |
| ACK `android17-6.18.33_r00` | Android Common Kernel tag, target commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` | **Stage A source pin** |
| DerpFest manifest `kernel-6.18.xml` | Its June 2026 `android17-6.18-2026-06` branch integration, release version 6.18.21 | Later ROM build default; must be overridden/integrated with the separately validated DBY-W09 Stage A kernel |

The Android official GKI release-build page currently documents the September 2026 Android 17 / 6.18 certified branch as 6.18.32. The existence of the ACK tag `android17-6.18.33_r00` does not by itself prove that a locally customized DBY-W09 build is an officially certified GKI artifact. Technical reports must distinguish:
- ACK-derived Android 17 kernel;
- GKI-based / GKI-compatible build;
- official certified GKI release.

Continue using “6.18.33 GKI kernel port” as the user's project shorthand, but describe the actual artifact and its certification status precisely.

## 3. DerpFest manifest mismatch — resolved for Stage A

Official manifest sources:
- https://github.com/DerpFest-AOSP/android_manifest/tree/17
- https://github.com/DerpFest-AOSP/android_manifest/blob/17/snippets/kernel-6.18.xml

The current DerpFest Android 17 `kernel-6.18.xml` points its common-kernel project at `android17-6.18-2026-06`. Android's release-build documentation identifies that branch baseline as 6.18.21. This does not change the user's requested kernel to 6.18.21.

Stage A must first create and validate the DBY-W09-specific ACK 6.18.33 kernel and its exact DTB/DTBO/modules/boot integration. During Stage B, DerpFest's generic kernel reference will need to be overridden with this already validated device kernel and matching modules. Do not start the DerpFest system tree now merely to follow the manifest's current default.

## 4. Comparable Android 17 / 6.18 Qualcomm port reviewed

Reference repositories:
- https://github.com/suvojeet-sengupta/redwood-6.18-kernel
- https://github.com/suvojeet-sengupta/redwood-6.18-modules
- https://github.com/suvojeet-sengupta/device_xiaomi_redwood-kernel-6.18
- Device integration branch: https://github.com/suvojeet-sengupta/device_xiaomi_redwood_clo/tree/6.18

This is a different device (Xiaomi redwood, SM7325 / Snapdragon 778G), not DBY-W09. It is useful for the kernel integration method, not for copying board data.

The kernel repository documents this construction:
- Android Common Kernel `android17-6.18` as the base;
- Qualcomm lahaina/yupik platform and SoC-repo driver delta carried from Qualcomm's 6.12 tree where needed;
- a GKI `gki_defconfig` plus a device/vendor config fragment;
- in-tree kernel modules and out-of-tree Qualcomm/vendor modules rebuilt against the same kernel;
- matching DTB/DTBO, module list and module-load order packaged together;
- the current main branch has subsequently moved to 6.18.63 and merged the Android `android17-6.18-lts` branch, so do not mistake its current binary or commit for a 6.18.33 artifact.

Useful methodology from its docs:
- Its README describes missing Qualcomm platform changes carried forward from 6.12, including clock, firmware, IOMMU, mailbox, PHY, remoteproc, rpmsg, SoC and thermal drivers.
- Its build guide explains that GKI config is combined with a per-device config and all in-tree/out-of-tree modules must be built for the exact same kernel release/vermagic.
- It uses Android Clang r596125, Rust 1.88 and pahole 1.25 for its current build. These are reference toolchain details only; Stage A must pin the toolchain required by the exact ACK 6.18.33 tag/build metadata rather than blindly copy a later device's tool versions.
- The redwood device branch describes a 6.18.33-Suvkernel build, but its kernel source and prebuilt have since advanced; treat that line as historical evidence only.

### What is not transferable to DBY-W09

The redwood sample uses a different SM7325 board, stock vendor, device tree, display/GPU/WLAN/audio hardware, and a modern boot arrangement including header-v4 / vendor_boot / init_boot and system_dlkm/vendor_dlkm. DBY-W09 local evidence instead shows SM8250 v2.1, boot header v2, a separate `ramdisk` partition, and no `vendor_boot` / `init_boot`.

Therefore:
- do not copy redwood's DTS, defconfig, vendor modules, DTBO, boot config or partition layout;
- do not assume its Qualcomm 6.12 carried-over driver list is identical to what DBY-W09 needs;
- use it to guide the method of isolating Qualcomm platform deltas and rebuilding matching modules only.

## 5. DBY-W09 Stage A implementation direction

Keep the existing storage-first and legacy-boot research, and refine it as follows:

1. **Source pin:** fetch/record the exact ACK `android17-6.18.33_r00` source commit, relevant submodule/toolchain refs, and the exact target Makefile version. Do not track a moving `android17-6.18` branch without a frozen SHA.
2. **Base configuration:** start from the matching GKI/ACK arm64 defconfig for this exact source ref; layer a minimal DBY-W09 board config. Keep the first configuration small and explain every non-default symbol.
3. **SoC/board delta:** retain upstream SM8250 device-tree, clock, GCC, RPMh, PMIC VRM, UFS, QMP PHY, interconnect and SMMU support where already present. Only port additional Qualcomm code when source comparison shows it is absent or incompatible.
4. **Storage-first:** complete the UFS/QMP, rail, clock, reset, interconnect, SMMU, RPMh/GenPD and early boot path. ROUND27's UFS required-OPP routing gap remains unresolved and must be addressed; do not claim the UFS OPP table already produces an RPMHPD MMCX vote.
5. **Board safety gates:** do not build a bootable DBY-W09 DTB until memory/reserved-memory handoff, regulator input/mode evidence, UFS rail topology, and DTBO/rootparam compatibility are closed to an adequate evidence level.
6. **Boot integration:** after ROUND12 AVB inspection, create an exact header-v2 + separate-ramdisk + DTBO plan that respects the observed stock ABL constraints. Do not transplant redwood's header-v4/vendor_boot instructions.
7. **Matching modules:** any module that is external to the GKI base must be rebuilt against this exact kernel build, matching vermagic and required symbols. Do not load old 4.19 modules into 6.18.33.
8. **Bring-up acceptance:** kernel compilation is not port completion. Require device boot evidence, exact `uname -r`, early boot logs, UFS enumeration and root/ramdisk availability before declaring Stage A boot success.

## 6. Existing DBY-W09 work that remains valid

This report does not replace or redo ROUND13–ROUND27. Continue using:
- ROUND13–ROUND20: minimal DTS/DTBO, Kconfig, UFS dependencies, UART, legacy boot, memory/reserved-memory, Android first-stage DM/EROFS;
- ROUND21–ROUND26: PM8150 parent-supply, ARC/provider hierarchy, UFS VCCQ parent/VDDP and DRMS evidence;
- ROUND27: UFS required-OPP to RPMHPD routing gap and the dual-GenPD design candidate.

The current local Agent task remains ROUND12 only. There is no ROUND12 result on `firmware-audit-v1` yet (the branch currently contains the ROUND11 report only). Do not mark ROUND12 complete or create a duplicate local task.

## 7. Next technical work

GPT-side:
- use the pinned ACK 6.18.33 tag, not the old GitHub mirror branch that reports 6.18.0-rc6;
- continue source review for the ROUND27 UFS dual-GenPD/required-OPP correction, including probe ordering, runtime-PM dependencies, teardown and failure unwind;
- compare only the Qualcomm SoC/platform files needed for the Stage A storage/boot milestone;
- prepare a reproducible GKI-derived build config and a version-locked kernel source manifest after the remaining evidence gates.

Local Agent:
- complete only the already assigned ROUND12 AVB metadata inspection using preinstalled trusted tools; if unavailable, report BLOCKED and stop.

## 8. Sources

- Android Common Kernel tag: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00
- Linux stable v6.18.33 tag: https://kernel.googlesource.com/pub/scm/linux/kernel/git/stable/linux/+/refs/tags/v6.18.33
- Android 17 / 6.18 GKI release builds: https://source.android.com/docs/core/architecture/kernel/gki-android17-6_18-release-builds
- DerpFest Android 17 manifest: https://github.com/DerpFest-AOSP/android_manifest/tree/17
- DerpFest kernel 6.18 manifest snippet: https://github.com/DerpFest-AOSP/android_manifest/blob/17/snippets/kernel-6.18.xml
- Qualcomm 6.18 port example source: https://github.com/suvojeet-sengupta/redwood-6.18-kernel
- Qualcomm 6.18 port example build method: https://github.com/suvojeet-sengupta/redwood-6.18-kernel/blob/main/BUILDING.md
