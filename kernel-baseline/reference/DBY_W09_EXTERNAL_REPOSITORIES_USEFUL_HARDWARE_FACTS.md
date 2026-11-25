# DBY-W09 external repositories — useful hardware facts and reuse boundaries

Date: 2026-11-26  
Maintainer / reviewer: 1号 AI (ChatGPT)  
Source intake: ROUND131 private mirror acceptance; ROUND133 pinned-ACK UFS SMMU cross-check  
Scope: preserve useful evidence from the six Gitee repositories for the DBY-W09 ACK 6.18.33 Stage A port. This document does not change the fixed source baseline, production patches, DTS, configuration, or device state.

## 1. Conclusions at a glance

**The UniXNU DBY-W09 repository is the strongest new same-device reference.** It supplies useful hardware facts and measured bring-up history for UFS, display, touch, and input. It is an XNU/iPadOS port, not Linux/ACK code; its driver logic, SMMU programming, power policy, boot package and memory map must not be transplanted into the Linux kernel.

The other five repositories are secondary references:
- GXDE kernel: Linux subsystem inventory and future project roadmap only; current mirror is a vanilla Linux v7.0.14 scaffold, not a ready-made DBY-W09 kernel implementation.
- GXDE hardware support: userspace feature roadmap; individual planned or reference-system outcomes are not proof for this ACK port.
- GXDE product repository: Debian/GXDE product and service design; relevant only to a possible later Linux desktop effort, not Android 17 DerpFest.
- pocket-linux: boot-switch APK with boot/ramdisk/DTBO partition-writing behavior; do not execute, adapt, or include in the source-only kernel workflow.
- GXDE touch calibration: Xorg/evdev userspace affine-coordinate calibration; potentially useful only after a Linux desktop/input stack is running, not a kernel touchscreen driver.

No repository provides a complete, directly reusable Linux driver or replacement for the project's fixed ACK 6.18.33 + Stage A patch series.

## 2. UFS hardware facts — cross-checked against pinned ACK

### Same-device UniXNU reference

The mirrored DBY-W09 board DTS declares:
- UFS host controller base: `0x1d84000`, compatible `qcom,sm8250-ufshc` / `qcom,ufshc`.
- QMP UFS PHY base: `0x1d87000`, compatible `qcom,sm8250-qmp-ufs-phy`.
- The UniXNU NativeUfs SM8250 feed is pinned at `FFT-infra/NativeUfs-alioth@ab5405905a1892da03a9a53e0fa3dcd255d04055` and records UFS SMMU stream IDs `0x0e0` and `0x4e0`.

References:
- [UniXNU DBY-W09 DTS](https://github.com/hhdy/UniXNU-dby_w09-gitee-mirror/blob/main/dts/dby_w09.dts)
- [UniXNU feeds](https://github.com/hhdy/UniXNU-dby_w09-gitee-mirror/blob/main/feeds.toml)
- [Pinned NativeUfs-alioth feed](https://github.com/FFT-infra/NativeUfs-alioth/tree/ab5405905a1892da03a9a53e0fa3dcd255d04055)
- [UniXNU porting record](https://github.com/hhdy/UniXNU-dby_w09-gitee-mirror/blob/main/porting.toml)

### Fixed ACK 6.18.33 confirmation

ROUND133 independently checked the project's immutable ACK source:
`aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.

In `arch/arm64/boot/dts/qcom/sm8250.dtsi`, UFS host `ufshc@1d84000` already declares:
```dts
iommus = <&apps_smmu 0x0e0 0>, <&apps_smmu 0x4e0 0>;
```
The `apps_smmu` provider uses `#iommu-cells = <2>`; in the pinned ARM SMMU driver, the first cell is parsed as the stream ID and the second as the mask. The DBY-W09 draft board DTS includes this SoC DTSI and does not replace the inherited UFS `iommus` property. Thus the current draft inherits both stream IDs; there is no reason to add a duplicate board-level `iommus` property merely because the XNU repository mentions them.

Source review record: [ROUND133 ACK SM8250 UFS IOMMU cross-check](../round133/ROUND133_ACK_SM8250_UFS_IOMMU_CROSSCHECK.md).

**Still unknown:** whether the actual HOS4.3 base FDT and selected DTBO expose, alter, or remove the same mapping. ROUND133's read-only Agent task is specifically checking existing ROUND3 base FDT candidates and all nine DTBOs. Do not claim HOS4.3 presence or absence until that report is reviewed. Kconfig resolution/build and runtime SMMU operation are separate gates.

## 3. Touchscreen firmware — a useful but unit-specific warning

The UniXNU DBY-W09 record says its DbyTouch firmware picker reads the unit's own `oeminfo` partition and selects among `W2599Z1100`, `W2599Z1300`, and `W2599Z2700`.

For the particular tested UniXNU unit:
- The driver's readable OEMINFO range contained no panel project ID.
- Automatic fallback selected `W2599Z2700`.
- That fallback produced a garbled panel and the touch path did not start.
- Explicit `dby-touch-fw=W2599Z1100` produced a clean display and responsive touch on that tested panel; the project record retained this explicit selection.

This is important as a **panel-firmware identification and fallback-risk lead**, not a universal DBY-W09 setting. Before considering it for this user's unit, identify the actual panel/revision and inspect that unit's own HOS4.3 firmware/OEMINFO evidence. Do not force `W2599Z1100`, copy XNU touch code, or assume the same project ID/fallback behavior without matching hardware evidence.

Reference: [UniXNU DBY-W09 porting record](https://github.com/hhdy/UniXNU-dby_w09-gitee-mirror/blob/main/porting.toml); repository overview also explains that touch firmware selection is per-unit and reads OEMINFO: [README](https://github.com/hhdy/UniXNU-dby_w09-gitee-mirror/blob/main/README.md).

## 4. Per-unit memory and storage values — do not copy

The UniXNU README and board DTS explicitly state that the model has per-unit variants:
- DRAM: 6 or 8 GiB in the reference project.
- UFS: 128 or 256 GiB in the reference project.
- Their published DTS/payload combination was measured on one 6 GiB / 128 GiB unit; its sample `memory@80000000` range is not a DBY-W09 board constant.
- The record itself requires reading DRAM size from the target unit and still calls for firmware memory-map confirmation.

This user's tablet is reported as a 12 GB expanded configuration. Do not use the UniXNU 6/8 GiB examples, its memory `reg`, 128 GiB GPT/userdata LBAs, or any per-unit storage UUID/geometry. The usable RAM map must be established from this user's actual boot handoff evidence (ABL/FDT/EFI path) and the real partition table. Model name equality is not sufficient.

Reference: [UniXNU README — values that belong to the unit](https://github.com/hhdy/UniXNU-dby_w09-gitee-mirror/blob/main/README.md#values-that-belong-to-the-unit).

## 5. What the same-device XNU port has demonstrated — and has not

The UniXNU record describes a tested XNU/iPadOS environment reaching launchd with native UFS root, display scanout and touch/key input. This is strong evidence that the hardware can be driven by a separate OS implementation and supplies subsystem-specific investigation leads.

It does **not** demonstrate Linux ACK bootability or validate Linux regulator/QMP/UFS/SMMU code. The same record marks GPU as not ported (CPU-rendered scanout); audio, network and camera are also not started. Therefore do not turn the XNU project's user-space progress into claims that those functions are already available to Linux or Android.

## 6. Six-repository triage and future use

| Repository | Useful content | Reuse decision |
|---|---|---|
| [gxde-kernel-dby-w09](https://github.com/hhdy/gxde-kernel-dby-w09) | Desired Linux subsystem inventory: panel/backlight/touch/pen, SD-root initramfs, boot-image assembly. Pins vanilla Linux v7.0.14; current tracked mirror is scaffold/docs without a complete board DTS/patch/config implementation. | Read as a future checklist. Do not substitute its kernel baseline or claim there is a reusable driver series. |
| [gxde-hwsupport-dby-w09](https://github.com/hhdy/gxde-hwsupport-dby-w09) | Userspace roadmap for audio, sensors, camera, USB/DP and power. | Roadmap only. DP 1080p60 reference-system result is not proof for this ACK candidate. |
| [gxde-dby-w09](https://github.com/hhdy/gxde-dby-w09) | Debian/GXDE product and service design. | Not part of current Android/DerpFest Stage B. Keep for a possible later Linux desktop project. |
| [pocket-linux](https://github.com/hhdy/pocket-linux) | HarmonyOS boot-switch APK. Its documented behavior writes boot, ramdisk and DTBO partitions. | Do not run or adapt in this source-only workflow. |
| [gxde-touch-calibration](https://github.com/hhdy/gxde-touch-calibration) | Xorg/evdev affine calibration utility. | Only consider after a Linux desktop and its input device are working; it cannot replace the touchscreen driver/firmware work. |
| [UniXNU-dby_w09-gitee-mirror](https://github.com/hhdy/UniXNU-dby_w09-gitee-mirror) | Same-device hardware facts, UFS/PHY addresses, per-unit memory/storage warning, panel firmware selection evidence, and XNU bring-up status. | Highest-value hardware reference. Use only for cross-checks and investigation direction; no XNU driver/power/SMMU implementation is directly transplanted. |

Mirror acceptance details and source HEADs remain in [ROUND131 acceptance and source triage](../../firmware-analysis/round131/ROUND131_ACCEPTANCE_AND_SOURCE_TRIAGE.md). All six GitHub mirrors are private; originals were not modified.

## 7. Actionable follow-ups for the current Stage A line

1. **ROUND133 HOS4.3 FDT/DTBO SMMU audit is complete.** The three existing base FDT candidates lack UFS Host `iommus`; all nine scanned DTBOs enable UFS/PHY and add supply consumers but do not add or override IOMMU properties. The detailed evidence and limits are recorded in `firmware-analysis/round133/TEST_AGENT_ROUND133_UFS_SMMU_FDT_REPORT.txt` and `kernel-baseline/round133/ROUND133_1AI_REVIEW.md`.
2. **Keep the fixed ACK UFS SMMU mapping unchanged for now.** The current board draft inherits upstream SID `0x0e0` and `0x4e0`; do not duplicate or remove it because of HOS4.3 static absence. HOS4.3 runtime SMMU/bypass/bootloader state remains UNKNOWN.
3. **Keep PMIC topology and memory handoff as the actual blockers.** Nothing in these six repositories proves the physical PM8150 parent supplies, final ABL-selected usable-memory map, reserved-memory map, or selected DTBO for this user's unit.
4. **Preserve the touch firmware lead for later device-specific analysis.** First establish the exact panel/revision and unit-specific OEMINFO behavior; only then consider firmware selection. This is not a reason to pause current UFS/memory/boot-chain work.
5. **Do not alter the immutable ACK source ref, 17-patch Stage A baseline, AI2 branch, protected DTS draft or PR #1 as a side effect of reading these references.** AI1/AI2 candidate series remain separately reviewed and tested.

## 8. Current status boundary

- Stage A remains the only active development stage; Android 17 DerpFest Stage B is deferred until Stage A hardware acceptance.
- Phase E/F remain BLOCKED; Phase G remains NOT RUN.
- No device was connected, no boot/flash/partition operation was performed, and no build or runtime validation is claimed by this reference synthesis.


## 9. ROUND133 — HOS4.3 UFS Host SMMU/IOMMU static evidence (2026-11-26)

- Agent report: [ROUND133 UFS SMMU/FDT report](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round133/TEST_AGENT_ROUND133_UFS_SMMU_FDT_REPORT.txt), Git blob `b953aa1627a067dde6491ee85ea415f177ec5daa`. Independent review: [ROUND133 1AI review](../round133/ROUND133_1AI_REVIEW.md).
- Three existing base FDT candidates (KONA v2.1/v2/v1) all contain `/soc/ufshc@1d84000` but have `status="disabled"` and no `iommus`, `iommu-map`, `iommu-map-mask`, `stream-match-mask`, or `iommu-parent`. UFS PHY `/soc/ufsphy_mem@1d87000` also has no IOMMU properties.
- The SMMU provider exists independently at `/soc/apps-smmu@15000000`, compatible `qcom,qsmmu-v500`, `#iommu-cells=<2>`; this does **not** mean UFS Host is bound to it. The Host has no phandle/specifier.
- All nine examined DTBOs resolve UFS PHY fragment@63 and UFS Host fragment@64. They enable the nodes and add PHY/Host supply consumers; none adds or overrides IOMMU properties, and none targets the SMMU provider. The report records 1299/1299 fragment targets resolved and no unresolved/ambiguous targets.
- Fixed ACK `sm8250.dtsi` explicitly gives UFS two SMMU entries: SID `0x0e0`, mask `0`; SID `0x4e0`, mask `0`. HOS4.3 has no SID/mask value to compare (NOT_PRESENT); only `#iommu-cells=2` matches.
- Provider compatible strings differ. Do not copy HOS4.3's `qcom,qsmmu-v500` into the ACK-derived board tree: the fixed ACK's SMMU match/implementation tables are keyed for the upstream SM8250 provider compatible list. The board DTS draft includes `sm8250.dtsi` and does not override `iommus`, so it inherits the two upstream entries.
- Disposition: preserve the upstream ACK mapping; do not add a duplicate board property or delete the inherited mapping based solely on HOS4.3's static absence. Runtime SMMU translation/bypass, ABL-selected base FDT/DTBO, bootloader/secure-firmware SMMU setup, stream-table and context-bank state remain UNKNOWN.
- This is static firmware evidence only. It does not clear the separate Phase E/F blockers or authorize device access/boot/flash.
