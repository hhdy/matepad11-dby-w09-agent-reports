# ROUND131 — Gitee six-repository mirror acceptance and source triage

Date: 2026-11-26
Owner / reviewer: 1号 AI (ChatGPT)
Executor: user-local WorkBuddy Agent (mirror-only)
Agent report: [AGENT_ROUND131_GITEE_MIRROR_REPORT.txt](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round131/AGENT_ROUND131_GITEE_MIRROR_REPORT.txt)
Report blob: `6be2c93dbe2f389617a3cc7ff27da7109f02b9ab`

## 1. Mirror disposition

**ACCEPTED — 6/6 private targets mirrored and verified.**

All six destination repositories independently queried through the GitHub connection report `visibility=private`; read permissions confirmed. Ref names and commit SHAs for all source heads and tags match the GitHub targets. The Agent also cloned each target independently and ran `git fsck --full --no-dangling` (RC=0 for all).

| Source Gitee repo | Private GitHub target | Default branch | Source HEAD |
|---|---|---|---|
| `gxde-pocket/gxde-kernel-dby-w09` | [hhdy/gxde-kernel-dby-w09](https://github.com/hhdy/gxde-kernel-dby-w09) | main | `f5d066bc0600605d14d51a3604cc5b9af1b14a13` |
| `gxde-pocket/gxde-hwsupport-dby-w09` | [hhdy/gxde-hwsupport-dby-w09](https://github.com/hhdy/gxde-hwsupport-dby-w09) | main | `e0a8b93a7e49c864f1901dc8a7fb37a7ec1e88af` |
| `gxde-pocket/gxde-dby-w09` | [hhdy/gxde-dby-w09](https://github.com/hhdy/gxde-dby-w09) | master | `e96d9823308107a8607a689eb2e121d948fc67b8` |
| `gxde-pocket/pocket-linux` | [hhdy/pocket-linux](https://github.com/hhdy/pocket-linux) | main | `5e8b9690f03943ce0546d17f50fac4fab5d47bb0` |
| `gxde-pocket/gxde-touch-calibration` | [hhdy/gxde-touch-calibration](https://github.com/hhdy/gxde-touch-calibration) | master | `1e79acf2fa133370d1a927862cad3d559b467a9d` |
| `uni-xnu-dby-w09/UniXNU-dby_w09` | [hhdy/UniXNU-dby_w09-gitee-mirror](https://github.com/hhdy/UniXNU-dby_w09-gitee-mirror) | main | `af7a7b2445e8ecb7006b5ba49bf692b6504b365d` |

- All source heads and tags match; no ref SHA mismatches.
- No LFS pointers or LFS objects found; LFS status is NONE for all six.
- No `.gitmodules` or gitlink submodules found in any mirrored refs.
- Four repositories carried 14 total Gitee `refs/pull/*` refs which GitHub refuses because that namespace is platform-reserved. The Agent listed all omitted refs in the original report. All source heads/tags/notes that can be pushed were mirrored. The omission does not affect branch/tag completeness.
- All six Gitee source HEADs were re-probed after the mirror and remained unchanged. No push was made to Gitee; no device was accessed.

## 2. 1号 AI source triage — relevance to DBY-W09 ACK Stage A

### GXDE kernel repository

[README](https://github.com/hhdy/gxde-kernel-dby-w09/blob/main/README.md), [KERNEL_VERSION](https://github.com/hhdy/gxde-kernel-dby-w09/blob/main/KERNEL_VERSION), [M1 handoff](https://github.com/hhdy/gxde-kernel-dby-w09/blob/main/docs/HANDOFF-M1.md), [kernel status](https://github.com/hhdy/gxde-kernel-dby-w09/blob/main/docs/STATUS.md).

- This is a separate Linux/GXDE project. It pins vanilla stable Linux `v7.0.14`, commit `b38d6c0b6e7f406a7feb7d46f184ec3edaac8c3b`, not the project’s fixed Android ACK GKI 6.18.33 commit.
- The mirrored kernel repository currently contains only the fetch/scaffold and documentation; the referenced board DTS, patch series, config and build/boot implementation are not yet present in the mirror's tracked tree. Its M1 handoff is a plan for those deliverables, not proof of a bootable independent Linux kernel.
- Its documented product scope (panel, backlight, touch/pen, SD-root initramfs, boot-image assembly) is useful as an inventory of desired Linux subsystems, but no code can be imported into the fixed ACK Stage A series from this scaffold.

### GXDE userspace / product / switch / calibration repositories

- [hwsupport README](https://github.com/hhdy/gxde-hwsupport-dby-w09/blob/main/README.md) and [status](https://github.com/hhdy/gxde-hwsupport-dby-w09/blob/main/docs/STATUS.md) describe audio, sensor, camera, USB/DP and power userspace components. Many are planned; the recorded DP Alt Mode 1080p60 result belongs to its GXDE reference system, not to the new ACK kernel candidate.
- [GXDE product design](https://github.com/hhdy/gxde-dby-w09/blob/master/docs/superpowers/specs/2026-10-30-gxde-dby-w09-design.md) and hardware README document a Debian/GXDE product and its services. This is not the Android/DerpFest Stage B project.
- [pocket-linux](https://github.com/hhdy/pocket-linux) is a HarmonyOS-side boot-switch application. Its README explicitly describes writing boot/ramdisk/dtbo partitions from microSD. It is not a kernel driver source and must not be run as part of this source-only research.
- [touch calibration](https://github.com/hhdy/gxde-touch-calibration) is a GXDE/Xorg userspace affine calibration utility over evdev, not a kernel touchscreen transport or Android input implementation.

### UniXNU same-device repository

[UniXNU DBY-W09 README](https://github.com/hhdy/UniXNU-dby_w09-gitee-mirror/blob/main/README.md), [board DTS](https://github.com/hhdy/UniXNU-dby_w09-gitee-mirror/blob/main/dts/dby_w09.dts), [board record](https://github.com/hhdy/UniXNU-dby_w09-gitee-mirror/blob/main/porting.toml), [SoC feed](https://github.com/FFT-infra/UniXNU-sm8250-common/tree/a6e7e36caab58f5b9a5625dbdb8da2bf290fa5cc), [UFS feed](https://github.com/FFT-infra/NativeUfs-alioth/tree/ab5405905a1892da03a9a53e0fa3dcd255d04055).

This is the strongest new same-model hardware reference among the six, but it is a port of XNU/iPadOS, not Linux. Its successful XNU/UFS/display/input experience does not validate ACK Linux regulator, QMP, UFS core or boot handoff code.

Useful cross-check facts:
- Its shared SM8250 DTS declares UFS HC at `0x1d84000` with compatible `qcom,sm8250-ufshc` / `qcom,ufshc`, and QMP UFS PHY at `0x1d87000` with compatible `qcom,sm8250-qmp-ufs-phy`. Those address/compatible facts are consistent with the SM8250 Linux-family source model, but each Linux property/interrupt/clock/IOMMU declaration must still be verified against pinned ACK and HOS4.3.
- Its pinned SM8250 UFS driver feed records two UFS SMMU stream IDs, `0x0e0` and `0x4e0`, for the alioth/SM8250 implementation. This is a valuable exact stream-ID lead to compare against our ACK DTS and existing ROUND evidence; it is not by itself proof that the Linux DTS should copy an XNU SMMU programming policy or invent an `iommus` property.
- The UniXNU board record explicitly says the model has per-unit DRAM/storage variants (6/8 GiB RAM and 128/256 GiB UFS), and that its published DTS/payload pair was measured on one 6 GiB / 128 GiB unit. Its memory section itself says the firmware memory-map confirmation is still an action. **Do not copy its 6 GiB `memory/reg` or 128 GiB GPT numbers to the user's expanded 12 GB tablet.** The actual unit's ABL handoff and memory map remain required.
- The XNU port's UFS path is a separate native driver and has its own SMMU, I/O queue, and storage design. We may reuse verified hardware facts and source pointers, not transplant its implementation into Linux ACK.

## 3. Stage A implications and next source review

1. The six repositories are now available as private, read-only reference mirrors. No Gitee changes were made.
2. The GXDE kernel scaffold is not an alternative to the fixed ACK 6.18.33 GKI line. Keep Stage A's pinned ACK source and 17-patch production series intact.
3. Use the UniXNU SM8250 UFS stream IDs as a targeted source cross-check against the pinned ACK device tree, HOS4.3 FDT/DTBO findings, and existing SMMU reports. Do not assume XNU's successful UFS path proves Linux GKI readiness.
4. Keep the memory/partition figures per-unit. The user unit's 12 GB expansion supersedes any temptation to reuse the reference port's 6/8 GiB example, but no actual usable-memory geometry can be asserted until ABL handoff evidence is obtained.
5. No Phase E/F or hardware activity was performed, authorized or inferred by this mirror acceptance. Phase E/F remain BLOCKED; Phase G NOT RUN; Stage B remains deferred.

