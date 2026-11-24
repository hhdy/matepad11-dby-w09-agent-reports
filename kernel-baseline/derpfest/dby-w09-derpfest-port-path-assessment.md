# DBY-W09 DerpFest ROM Port Path Assessment — updated to kernel-first plan

Date: 2026-11-24

> **Superseding decision (user-confirmed 2026-11-24): this document's former userspace-first recommendation is obsolete. The mandatory order is Stage A: first port and validate DBY-W09 ACK/GKI 6.18.33; Stage B: only then port Android 17 DerpFest. Stage C: only after that assess ColorOS or other ROMs. Read [PROJECT_HANDOFF.md](../../PROJECT_HANDOFF.md) and [ROUND28](../round28/android17-6.18.33-source-baseline-and-qcom-platform-delta.md) as authoritative.**

## Executive conclusion

The DerpFest direction remains feasible, but the user's required project order is kernel-first. Stage A must first port and device-validate the DBY-W09 ACK `android17-6.18.33_r00` kernel. Only after Stage A passes its startup acceptance gates does Stage B begin Android 17 DerpFest integration. This is an independent kernel milestone followed by ROM integration, not a userspace-first port.

Do not wait for or depend on the unpublished Coolapk package. Treat the reported successful Coolapk port as an important lead, but do not assume its Android version, partition strategy, boot image, or vendor base until the post or an independently verifiable record is available.

## Evidence checked

### 1. DerpFest source and SM8250 device references

- Official DerpFest source organization: https://github.com/DerpFest-AOSP
- Official organization README states that its current mainline support is Android 17 (status November 2026), with a secondary/low-key Android 13 QPR3 line (status July 2026): https://github.com/DerpFest-AOSP
- Official device repository organization: https://github.com/DerpFest-Devices
- It has Motorola Edge 20 Pro (pstar) and Moto G100/Edge S (nio) SM8250 device trees, plus a shared SM8250 common tree and a shared kernel:
  - https://github.com/DerpFest-Devices/device_motorola_pstar
  - https://github.com/DerpFest-Devices/device_motorola_nio
  - https://github.com/DerpFest-Devices/device_motorola_sm8250-common
  - https://github.com/DerpFest-Devices/kernel_motorola_sm8250
- The pstar/nio device README describes Snapdragon 870 SM8250-family devices shipped with Android 11. These are useful SoC-family references, not DBY-W09 board references.
- The shared Motorola kernel branch 13.0 Makefile identifies Linux 4.19.157; branch 17 identifies Linux 4.19.325. The latter is not the DBY-W09 stock kernel binary or ABI. Do not copy their kernel image or modules to Huawei.
- Their common BoardConfig uses boot header v3, A/B OTA partitions and vendor_boot. The DBY-W09 firmware evidence instead shows a boot header v2, a separate ramdisk partition, no vendor_boot/init_boot, and logical partitions cust/hw_product/odm/system/vendor. Therefore the Motorola BoardConfig/device tree is not a drop-in template. Reuse conceptual Android build structure and carefully selected generic SM8250 pieces only.

### 2. Independent same-device Android userspace precedent

A public DBY-W09 project by Queen_Glasser documents Android 10 -> Android 11 -> Android 12L/API32 bring-up on the MatePad 11 (Snapdragon 865):
- https://github.com/glasses666/dby-w09-boot-research
- Its README reports boot-complete Android 12L/API32, repeated cold boots, display/touch/GPU, Wi-Fi, camera, sensors, audio and Google services on its research device.
- Its release notes explicitly say the tested system retained the original boot/vendor chain and that Android 13+ remained unaccepted as of 2026-10-29.
- It does not distribute a flashable ROM or Huawei vendor/boot binaries. The repository states that no license has been granted and all rights are reserved. Use it as published evidence and a research pointer; do not copy or redistribute its protected artifacts or substantial code without permission.

This is not evidence that DerpFest itself has already booted on the user's exact firmware. It does, however, demonstrate that the device's legacy boot/vendor chain can support a newer AOSP userspace after carefully scoped framework/VINTF compatibility work.

### 3. Coolapk report

The user reports that a Coolapk contributor successfully ported DerpFest to DBY-W09 but has not released the original package. Public searches in this assessment did not locate a verifiable post/package. Status: USER-REPORTED LEAD; exact Android version, firmware baseline, build type (GSI vs device-specific), boot/vendor handling and tested features remain UNKNOWN.

## Required port architecture — kernel first

### Stage A — DBY-W09 ACK/GKI 6.18.33 kernel (current mainline)

1. Pin the official ACK `android17-6.18.33_r00` tag and exact commit. Do not use the pure stable `v6.18.33` source tree as a substitute for ACK and do not follow a moving branch HEAD.
2. Finish the existing SM8250 board DTS, PMIC/RPMh, UFS/QMP, clock/reset/interconnect/SMMU, memory/reserved-memory and GenPD/OPP work.
3. Close the legacy header-v2 / separate-ramdisk / DTBO / AVB constraints before creating the device boot image. ROUND12 is the currently assigned local read-only task.
4. Build a reproducible arm64 GKI-derived config and exact matching Image, DTB/DTBO and any required modules. Do not reuse 4.19 vendor modules with a 6.18 kernel.
5. Validate the kernel on DBY-W09 independently with controlled boot evidence. Compilation alone does not complete Stage A; require actual device startup, exact kernel release, logs and UFS/storage availability.

### Stage B — Android 17 DerpFest (after Stage A acceptance)

1. Use the DerpFest Android 17 source manifest, but override its current generic June/6.18.21 kernel reference with the already validated DBY-W09 6.18.33 kernel and matching modules.
2. Adapt DBY-W09 device/product/vendor configuration, fstab, init, VINTF, SELinux and proprietary firmware only after the kernel/boot integration baseline is stable.
3. Preserve the real DBY-W09 legacy boot layout unless new local evidence proves otherwise. Do not copy the Motorola pstar/nio header-v3/A-B/vendor_boot layout.
4. Bring the ROM to boot-complete and validate hardware surfaces separately.

### Stage C — later ROM targets

Only after Android 17 DerpFest is stable should ColorOS or other ROMs be evaluated.

## Blocking facts and explicit UNKNOWNs

- The exact Coolapk DerpFest Android version and its porting method are UNKNOWN.
- The user's current HarmonyOS 4.3 system/vendor API, VNDK level and full VINTF state are not verified from EROFS content; the EROFS content layer remains BLOCKED.
- The public API32 same-device precedent is not the user's exact HOS 4.3 firmware baseline. Do not assume every fix or binary is transferable.
- The DBY-W09 display active profile remains UNKNOWN.
- A successful DerpFest launcher boot, Wi-Fi, audio, camera, suspend and update/OTA behavior require separate acceptance evidence.

## Proposed next work

After Stage A kernel acceptance, create a DerpFest-specific source-and-configuration assessment. It should compare:
- the exact public DerpFest source branch selected for the target Android release;
- Motorola pstar/nio SM8250 build patterns, separating common SoC logic from Motorola-only assumptions;
- DBY-W09 boot header/ramdisk/partition layout facts already established in ROUND1–ROUND9;
- the published DBY-W09 Android 12L/API32 research milestones and their stated limits;
- any exact Coolapk post metadata supplied by the user.

Current work remains Stage A kernel migration; do not start the full DerpFest device/vendor port before Stage A acceptance. ROUND12 remains the only active local read-only Agent task. Do not ask the local Agent to repeat FDT/DTBO parsing. Do not ask for firmware re-upload. Do not flash, unlock, root, connect to the device, write partitions, compile locally, load modules or mount writable filesystems as part of this assessment.
