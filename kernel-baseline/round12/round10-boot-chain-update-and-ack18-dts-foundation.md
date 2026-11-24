# ROUND12 — DBY-W09 ACK 6.18 board-DTS foundation and ROUND10 boot-chain update

Date: 2026-11-24
Status: ChatGPT source-side research; no kernel sync, build, DTB compile, boot-image repack, flash, or device test performed.

## 1. Decision

Target remains Huawei MatePad 11 DBY-W09 (KONA / SM8250 v2.1 / Snapdragon 865), Android 17 DerpFest and a 6.18-family kernel.

The recommended first implementation target is an **ACK android17-6.18-derived DBY-W09 device kernel**, initially preserving the existing legacy DBY-W09 ABL boot chain where possible. Do not claim official GKI compliance until the boot-image format, KMI, certified GKI integration and relevant Android requirements are separately demonstrated.

The user reports a successful same-model Android 17 DerpFest + Linux 6.18 port by a Coolapk contributor. That is feasibility evidence supplied by the user. The porter did not publish source; source branch, patches, defconfig, boot packing and validation details remain UNKNOWN. This project will independently rebuild, not wait for their package.

## 2. ROUND10 evidence incorporated

Local Agent uploaded two sanitized files to `firmware-analysis/round10/` on `firmware-audit-v1`:
- `round10_boot_ramdisk_inventory.txt`
- `round10_boot_chain_summary.json`

Summary JSON status: `COMPLETE_WITH_BLOCKED_SUBITEMS`.

### Evidence grades — keep separate

| Evidence area | Result | What it actually proves |
|---|---|---|
| Existing boot/recovery/erecovery cmdline records | `NO_PANEL_SELECTOR_FOUND_IN_CMDLINE_SCOPE` | No panel/lcd/display selector was found in the successfully reviewed cmdline fields |
| `video=vfb` | Generic framebuffer-console argument | Does not select a DBY-W09 panel profile |
| boot.img embedded ramdisk | `BLOCKED` | Region was not located/extracted; compression and contents are undetermined |
| ramdisk inventory | `EMPTY (BLOCKED)` | Not an empty ramdisk; zero files were inspected |
| init/fstab/mount statements | `NOT_READ_BLOCKED` | No conclusions can be drawn about mount order or fstab |
| module load directives | `NOT_READ_BLOCKED` | No conclusions can be drawn about module loading stage/source |
| firmware path references | `NOT_READ_BLOCKED` | Firmware paths and required payloads remain unknown |
| panel active profile | `UNKNOWN` | No final/live FDT or runtime profile evidence |

Do not summarize the cmdline finding as a global absence of panel selection. The correct combined status is: no selector found in cmdline scope; ramdisk selector scan blocked; global panel selector unknown/blocked; `ACTIVE_PROFILE=UNKNOWN`.

### Conditions to unblock ramdisk inspection

The only acceptable route is a **trusted Android boot-image unpacking tool or already-reviewed extractor, plus explicit user authorization** to use it within the read-only boundary. The Agent must not write a new boot parser, install unknown binaries, bypass Windows security policy, or invoke WSL. No new ramdisk task is issued until those conditions are met.

## 3. Legacy boot chain versus official GKI architecture

Existing local evidence:
- Stock `boot.img` header v2.
- Separate `ramdisk` partition exists.
- No `vendor_boot` or `init_boot` partition was identified in the inspected firmware partition layout.
- ABL/DTBO behavior includes a strict `/rootparam` identity contract. ROUND8 resolved all 145 DTBO entry-8 fragment targets through `__fixups__` and base `__symbols__`; fragment@143 populates `/rootparam`.
- The exact ramdisk content and mount/module flow are blocked under ROUND10.

Official Android documentation distinguishes GKI boot formats:
- Android 11 GKI devices use boot header v3 with device-specific boot information moved into `vendor_boot`.
- Android 12/13 GKI-capable devices use header v3/v4; Android 13 launch devices add `init_boot`.
- The official GKI retrofit utility can produce a header-v2 retrofitted boot image, but its documented inputs include a source GKI `boot.img`, `init_boot.img` and `vendor_boot.img`. DBY-W09's known legacy layout does not presently provide that standard input set.
References:
- https://source.android.com/docs/core/architecture/bootloader/boot-image-header
- https://source.android.com/docs/core/architecture/partitions/vendor-boot-partitions
- https://android.googlesource.com/platform/system/tools/mkbootimg/+/refs/tags/android-13.0.0_r0.43/gki/README.md

Therefore distinguish two possible deliverables:

A. **ACK 6.18.33-derived custom device kernel using legacy boot v2 + the existing separate ramdisk/DTBO flow.** This is the preferred first bring-up target, if ABL accepts a correctly repacked compatible image. It may use the ACK codebase but is not automatically an officially GKI-compliant device.

B. **Full GKI boot architecture retrofit.** This would require an explicit boot-chain/partition migration design, proof of ABL compatibility, AVB treatment and a valid vendor/init ramdisk arrangement. It is not currently justified and must not be assumed possible merely because a GKI v2 retrofit utility exists.

Do not change partition layout or build a new `vendor_boot`/ `init_boot` convention by guesswork.

## 4. Source-version status

- The parent source branch `android17-6.18` is the intended ACK source line.
- The branch HEAD Makefile was previously checked in this project and identified Linux 6.18.33.
- Google’s Android 17 GKI release page currently documents the September 2026 release series as version 6.18.32; it does not establish a published/certified 6.18.33 GKI artifact.
- A source tag `android17-6.18.33_r00` was previously located; its existence is not proof of a certified GKI image.

References:
- https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18
- https://source.android.com/docs/core/architecture/kernel/gki-android17-6_18-release-builds
- https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00

When a build environment is available, freeze the exact ACK commit / manifest before source sync. Until then, call the target an ACK 6.18.33-derived custom device kernel, not a certified 6.18.33 GKI release.

## 5. ACK SM8250 DTS foundation confirmed from source

The ACK `android17-6.18` SM8250 SoC DTSI exposes the following relevant labels and default nodes. The same structural definitions appear in the public source view inspected on 2026-11-24:

Source: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/arch/arm64/boot/dts/qcom/sm8250.dtsi

### UFS Host

The SoC node is `ufs_mem_hc: ufshc@1d84000` and carries:
- compatible `qcom,sm8250-ufshc`, `qcom,ufshc`, `jedec,ufs-2.0`;
- PHY consumer `phys = <&ufs_mem_phy_lanes>`, `phy-names = "ufsphy"`;
- two lanes per direction;
- host reset controller `resets = <&gcc GCC_UFS_PHY_BCR>`, `reset-names = "rst"`;
- power domain `<&gcc UFS_PHY_GDSC>`;
- the SM8250 UFS core, bus, interface, UniPro, reference and lane-sync clocks;
- default `status = "disabled"`.

### UFS QMP PHY

The SoC node is `ufs_mem_phy: phy@1d87000`:
- compatible `qcom,sm8250-qmp-ufs-phy`;
- reference and auxiliary clocks;
- `resets = <&ufs_mem_hc 0>`, `reset-names = "ufsphy"`;
- lane provider `ufs_mem_phy_lanes: phy@1d87400` with the SM8250 two-lane register layout;
- default `status = "disabled"`.

This confirms the reset-cell interpretation: `<&ufs_mem_hc 0>` is one provider phandle plus one reset specifier cell. Do not interpret the HOS raw cell array as two unrelated phandles. Keep the SoC reset topology from the ACK DTSI unless board-specific evidence demonstrates a required override.

### SPI14 / THP controller

The ACK SM8250 DTSI defines `qupv3_id_2: geniqup@8c0000` and `spi14: spi@880000` under it. The SPI controller uses `compatible = "qcom,geni-spi"`, a QUP2 S0 clock, GPI DMA channels, CX power domain and a default disabled status.

For an ACK-derived DBY-W09 DTS:
- enable `&qupv3_id_2` and `&spi14`;
- keep `qcom,geni-spi` (do not carry HOS `qcom,spi-geni`);
- add board pinctrl/CS from the local ROUND9 values;
- add the DBY-W09 THP child only after the driver OF match is deliberately aligned;
- use the local HOS conservative 10 MHz parent/initial operating point as the bring-up starting point; do not immediately raise to the external reference's 16 MHz maximum.

Same-device reference:
https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts

## 6. UFS rail mapping proposal for the initial board DTS

ROUND9 local HOS4.3 evidence resolves all eight supply fixups. The ACK upstream consumer semantics imply this initial mapping:

| ACK consumer node/property | ROUND9 local rail | Treatment |
|---|---|---|
| `&ufs_mem_hc: vcc-supply` | PM8150 L17, 2.496–3.008 V rail; HOS overlay level 2.504–2.95 V, 800 mA | Map to board regulator phandle; carry 800 mA maximum from HOS4.3 overlay |
| `&ufs_mem_hc: vccq-supply` | PM8150 L6, 1.2 V | Map to board regulator phandle |
| `&ufs_mem_hc: vccq2-supply` | PM8150 S4, 1.8 V | Map to board regulator phandle |
| `&ufs_mem_phy: vdda-phy-supply` | PM8150 L5, 0.88 V, 89.9 mA | Map to PHY; add `vdda-max-microamp = <89900>` |
| `&ufs_mem_phy: vdda-pll-supply` | PM8150 L9, 1.2 V, 18.8 mA | Map to PHY; add `vdda-pll-max-microamp = <18800>` |
| `&ufs_mem_phy: vddp-ref-clk-supply` (optional QMP PHY rail) | PM8150 L6, same physical rail as local vccq | Put on PHY node, not Host; verify the ACK 6.18 QMP binding/driver before finalizing |

The mapping above is a DTS design candidate, not a compiled DTS. Regulator node declarations and input-supply topology must be written from the exact DBY-W09 PMIC nodes and HOS4.3 facts, not copied wholesale from Motorola or Xiaomi.

Two HOS/downstream properties should not be blindly carried over:
- `vdd-hba` resolves to the UFS PHY GDSC power domain. The ACK SM8250 Host node already expresses this via `power-domains = <&gcc UFS_PHY_GDSC>`; do not represent the same GDSC as a regulator supply.
- `qcom,vccq-parent-supply` is downstream-specific and has no generic equivalent in the inspected upstream Host binding. Omit it unless a concrete ACK driver dependency is identified.

Reference binding:
https://kernel.googlesource.com/pub/scm/linux/kernel/git/torvalds/linux/+/ea5751ccd665a2fd1b24f9af81f6167f0718c5f6/Documentation/devicetree/bindings/phy/qcom-qmp-phy.txt

## 7. Panel, touch and other peripheral gating

### Panel

- HOS4.3 entry-8 overlay `qcom,dsi-default-panel` points within the overlay to a CSOT NT36523 10.9-inch 1600x2560 dual-DSI/C-PHY profile.
- ROUND10 found no selector in the cmdline scope only.
- Ramdisk scan is blocked and has not ruled out a ramdisk/vendor selector.
- No final live FDT or runtime display service configuration is available.
- Keep `ACTIVE_PROFILE=UNKNOWN`. Do not enable a guessed candidate profile in the first board DTS.

### THP

- Local HOS values: native CS GPIO43, IRQ GPIO39, reset GPIO98, parent 10 MHz, child maxima 16 MHz.
- HOS compatible: `huawei,thp`; same-device Linux shim uses a device-specific OF match string `huawei,dby-w09-thp`.
- Decide whether the new ACK node uses the shim-specific compatible alone or a compatible list only after confirming the driver's actual `of_match_table`. Do not assume a generic upstream touchscreen driver can replace the Huawei THP/aptouch ABI.

### WLAN / audio / cameras / USB

- GKI 6.18 module catalog contains upstream Qualcomm building blocks such as `ufs-qcom.ko`, `phy-qcom-qmp-ufs.ko`, `ath11k`, `wcd938x` and `fsa4480`; this only establishes upstream/GKI source build availability, not DBY-W09 board-data, private firmware or VINTF compatibility.
- QCA6391 hardware revision/PCI ID and private calibration/board data remain UNKNOWN.
- WCD938x exact 9380 vs 9385 identity must be proved before picking an upstream compatible.
- Camera sensor models/endpoints remain UNKNOWN in local HOS4.3 reports.
- Redriver model remains UNKNOWN; do not name it NB7VPQ904M without local ID evidence.
- Keep these devices out of the minimal boot acceptance target until the matching board wiring and required firmware are verified.

Reference GKI module list:
https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18-2026-09_r8/BUILD.bazel

## 8. Early-boot configuration principle

The device's Android system/vendor/odm logical partitions reside on UFS. The ramdisk's fstab and module-loading order are unknown because ROUND10 could not read its content. For the first bootable ACK-derived kernel, storage, UFS Host, QMP PHY, required clocks/reset/pinctrl/regulator and other pre-mount dependencies should be built in rather than relying on an unverified module-loading script. This is a conservative bring-up principle; final Kconfig values must be checked against the pinned ACK branch.

The existence of GKI module artifacts does not mean the same modules can safely be deferred until after system partitions are mounted. Nor can Huawei 4.19.157-perf+ modules be assumed to work on ACK 6.18.

## 9. Next engineering steps

1. GPT source-side work: create a minimal ACK SM8250-derived DBY-W09 DTS draft with only identity, verified regulator definitions and UFS/QMP enablement; keep panel/THP and other peripherals disabled or gated.
2. Explicitly preserve the ABL `/rootparam` identity contract. Do not assume the stock DTBO works against an ACK-produced base DTB until all referenced `__symbols__` / `__fixups__` are checked against that new DTB.
3. Compare the initial DTS against the actual pinned ACK source, not only upstream Linux v6.18 excerpts. No source sync/build has yet been run.
4. Build and validate offline only after the user provides/authorizes an approved build environment. At present source sync / Kleaf build remains NOT_RUN; WSL remains blocked.
5. No new local Agent task is required for this source-side stage. If a trusted boot unpack tool becomes available with explicit authorization, create a narrow follow-up task only for ramdisk inspection. Do not repeat ROUND1–ROUND10 parsing.

## 10. Safety and status

No device connection, ADB, fastboot, unlock, root, partition write, module load, writable mount, kernel compile, WSL invocation, EROFS unpack or binary upload occurred in ROUND10. PR #1 remains Draft. No local binary is to be uploaded.
