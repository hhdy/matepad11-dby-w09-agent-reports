# DBY-W09 Android 17 / ACK 6.18 Kernel-First Port Plan

Date: 2026-11-24
Status: research and architecture decision; no source synchronization, compilation, flashing, or device test performed.

## 1. Target decision

Target product: Huawei MatePad 11 DBY-W09 (KONA / SM8250 v2.1, Snapdragon 865)
Target OS: Android 17 / DerpFest
Target kernel family: Android Common Kernel (ACK), `android17-6.18`
Initial kernel milestone: board-specific bootable ACK-derived kernel, using the existing DBY-W09 boot chain where technically feasible.
Do not wait for or depend on the Coolapk porter’s unpublished source/package.

The user reports a successful Android 17 DerpFest + Linux 6.18 port on the same model. Treat that as user-provided feasibility evidence only. Exact source base, patch set, Kconfig, board DTS, image packing, and validation scope are UNKNOWN.

## 2. Correct interpretation of 6.18.33 / GKI

- The canonical Android common branch is `android17-6.18`. Android’s common-kernel documentation identifies ACK as downstream of kernel.org and describes the Android-specific patch/KMI branch model: https://source.android.com/docs/core/architecture/kernel/android-common
- The current branch HEAD was previously checked in this project and its Makefile identifies Linux 6.18.33. Pin the exact resolved commit/manifest when starting a build; do not build against a moving branch without recording the SHA.
- A Google source tag named `android17-6.18.33_r00` exists, created 2026-10-15. Its tagged commit message specifically says it merges `android17-6.18` into `android17-6.18-lts`. This proves a source tag exists; it does not, by itself, prove that a certified GKI boot artifact with that tag was published: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00
- The official Android 17 GKI release-build page lists published monthly GKI artifact releases and must be used to determine certified artifacts separately from source branch/tag version: https://source.android.com/docs/core/architecture/kernel/gki-android17-6_18-release-builds
- Thus the project should call its target an **ACK android17-6.18-derived DBY-W09 device kernel** until certified GKI/KMI compliance and a matching published GKI artifact are demonstrated. A branch version of 6.18.33 is not equal to a certified GKI image.
- Vendor modules from Huawei's existing 4.19.157-perf+ kernel must not be assumed to load on 6.18. Their vermagic, symbol versions, exported symbols, KMI and dependencies are presently UNKNOWN because EROFS content inspection is BLOCKED.

## 3. Best public same-device references found

### A. CoWave-Fall/linux-on-arm-matepad11

Repository: https://github.com/CoWave-Fall/linux-on-arm-matepad11

The current README identifies a DBY-W09 mainline Linux port and documents display (dual DSI, 1600x2560), Novatek touchscreen, RT8555 backlight, QCA6391 Wi-Fi, audio, USB-C/DP, PM8150B power, sensors and other board-specific support. Its kernel README identifies Linux 7.3.4 and ten ordered board/driver patches. The status page records HarmonyOS 4.2.0.213 as its test baseline and lists cameras/NPU/fast charging as not implemented.

Important value: its patch set and board support are a public same-device implementation reference, not an ACK 6.18 patch set. The kernel base is newer (7.3.4), so every driver and DTS change must be checked for dependencies before backporting to 6.18. Do not copy its U-Boot/SD-root setup into Android.

### B. svesnav/linux-dby-w09

Repository: https://github.com/svesnav/linux-dby-w09

Its README identifies mainline Linux 7.0.14 for DBY-W09. It contains:
- `sm8250-huawei-dby-w09.dts`
- `dby-w09-rootparam.dtso`
- board-specific panel and RT8555 backlight code
- Huawei THP bridge driver
- camera DTS
- Type-C / DP DTS
- audio / TDM patch scripts
- boot repacking/build scripts

Its documented boot-chain facts align with the earlier local firmware investigation: legacy boot header v2, a separate `ramdisk` partition, and a required /rootparam DTBO overlay behavior. The README says the ABL-applied entry must populate `/rootparam` consistently with the stock overlay; selecting an incompatible DTBO causes fastboot fallback. Treat this as an important same-device public report and verify every part against our own firmware evidence before use.

Important value: same-device board DTS and the accepted boot-chain/rootparam concept. It is not Android/ACK integration code. Its README describes custom Linux booting via U-Boot and microSD; do not adopt its flashing procedure or assume it describes the exact current HOS4.3 runtime state.

### C. youzjuzi/dby-w09-kernel

Repository: https://github.com/youzjuzi/dby-w09-kernel

The Chinese README identifies Linux 7.2.10, a DBY-W09 board DTS, a defconfig and a device-specific patch set; it states that the tested device was HarmonyOS 4.2. The project documents that private owner data (panel command data, memory include, touch plan, firmware/calibration) is not distributed. This can help identify where board-specific private data is unavoidable, but it is not an Android kernel base and should not be treated as a stock HOS4.3 configuration.

## 4. What can be reused and what cannot

### Reuse after verification
- Device-level topology: SM8250/KONA nodes, PMIC rails, clocks, pinctrl, UFS host/PHY, SPI touch, display dual DSI, USB-C/DP, QCA639x and audio topology.
- The local ROUND7–ROUND9 HOS4.3 facts are the primary board-specific source for this tablet's installed firmware.
- Public same-device Linux DTS is a cross-check and an implementation reference for kernel code that HOS4.3 DTBO does not fully expose.
- Public driver patch sets are candidates for individual backport analysis, with commit provenance and licensing retained.

### Do not reuse blindly
- Any full Linux 7.0/7.2/7.3 kernel tree as if it were ACK 6.18.
- Motorola pstar/nio DTS, BoardConfig, partitions, init, module aliases or vendor files.
- HarmonyOS 4.2-specific assumptions as facts about HOS4.3.
- HOS4.3 4.19 vendor modules as 6.18-compatible modules.
- A clean mainline DTS with the old stock DTBO unless symbol/fixup/target compatibility is proven. ROUND8 shows 145 overlay fragments rely on symbols/fixups; a newly generated DTB can change labels/phandles/symbol exposure. The ABL-required /rootparam contract must also be preserved.
- A GKI v4 boot image layout, vendor_boot/init_boot assumptions or standard A/B partition layout. The user's device is documented locally as boot header v2, a separate ramdisk partition and no vendor_boot/init_boot.

## 5. Proposed kernel bring-up order

### Stage K0 — Freeze source and define integration model
1. Resolve and pin the ACK `android17-6.18` manifest and exact commit. Keep the target source version and tag/certification status explicit.
2. Use `gki_defconfig`/Kleaf only as a baseline, then define the DBY-W09 configuration strategy. Avoid assuming that a GKI defconfig alone produces a usable device kernel.
3. Separate built-in early-boot drivers from modular device drivers. For the first boot milestone, make essential boot/storage/console/power dependencies available before Android's module services are ready.
4. Inventory the Android 17 boot image requirements and map them to the device's legacy ABL/boot header v2 + separate ramdisk design.

### Stage K1 — Board DTS foundation
1. Start from the ACK 6.18 SM8250/KONA SoC DTSI and the local HOS4.3 base/overlay facts, not Motorola board files.
2. Create a DBY-W09-specific board DTS with only verified resources.
3. Resolve the ABL DTBO contract: accepted DTBO entry, /rootparam content, overlay targets, __symbols__/__fixups__ and required exported labels. Avoid assuming a clean compiled DTS can consume the original overlay unchanged.
4. Add UFS host and QMP PHY with the ROUND9 closed regulator phandles. Validate each supply name and consumer binding against the exact ACK 6.18 source.
5. Keep optional display/touch/WLAN/audio/camera nodes disabled until driver, compatible, regulator and firmware requirements are individually validated.

### Stage K2 — Minimal boot kernel
1. Enable arm64, Qualcomm SM8250 clocks/interconnects/pinctrl/GPIO/PMIC/regulator, PSCI, SCM, SPMI, RPMh, UFS/QMP and serial console as required by exact DTS.
2. Preserve the existing bootloader contract and rootparam data.
3. Build Image, DTB, required modules and boot image offline; inspect all outputs and run image-format / DTB checks before any device test.
4. Do not flash during this stage. A successful build or static image check is not proof of device bootability.

### Stage K3 — Device feature drivers
Recommended priority:
1. Display + backlight + touch (high value for interactive boot).
2. USB-C / Type-C / DP.
3. QCA6391 WLAN / BT (requires firmware/calibration/board-data strategy).
4. Audio / TFA9874 / WCD938x.
5. Sensors, battery, charging and suspend.
6. Cameras last; current local HOS4.3 sensor model and endpoints remain UNKNOWN.

### Stage K4 — Android 17 integration
Only after kernel + board DTB boot foundation is stable:
- determine which vendor/odm framework and HAL compatibility layer the unpublished port used (currently UNKNOWN);
- inspect VINTF, init, module loading, fstab and vendor API requirements;
- integrate DerpFest Android 17 system/product tree.
This is intentionally later than kernel bring-up.

## 6. Current blockers

| Item | Status | Impact |
|---|---|---|
| EROFS vendor/odm file content | BLOCKED | Cannot inventory proprietary .ko, firmware, VINTF, init or vendor KMI |
| Local ramdisk contents | ROUND10 complete with BLOCKED subitems | Cmdline only: no selector found; ramdisk contents, fstab and module sequence remain NOT_READ_BLOCKED |
| ACK source sync / Kleaf | NOT_RUN / WSL blocked | No build performed |
| Android17 + old HOS4.3 vendor compatibility | UNKNOWN | Full Android17 system bring-up remains separate risk |
| Exact Coolapk kernel source | NOT_PUBLIC | Cannot reproduce that maintainer's patch set |
| Panel active profile | UNKNOWN | Do not hardcode a profile by guess |
| WLAN PCI HW ID / calibration | UNKNOWN | Cannot certify QCA6391 ath11k configuration |
| Camera sensor model/I2C/endpoints | UNKNOWN | Camera cannot be treated as first-boot requirement |

## 7. Immediate next actions

1. ROUND10 is complete with blocked subitems. Its ramdisk scan is BLOCKED; its cmdline finding is limited to the reviewed cmdline scope. Do not state globally that no panel selector exists.
2. GPT continues source-side work: build the minimal DBY-W09 ACK 6.18 DTS foundation and verify the legacy boot-v2 / separate-ramdisk integration model. ROUND12 records the current evidence and DTS mapping.
3. No new local Agent task is pending. A follow-up ramdisk task requires both a trusted boot unpack tool and explicit user authorization. Do not repeat FDT/DTBO parsing.
4. Preserve read-only boundaries: no flashing, unlocking, device connection, root, partition writes, module loading, writable mounts or compilation until the user explicitly changes the operating boundary.
