# DBY-W09 DerpFest ROM Port Path Assessment

Date: 2026-11-24

## Executive conclusion

The DerpFest direction is feasible as a separate Android userspace/ROM bring-up track, but it should not be conflated with the ACK/GKI 6.18.33 kernel port. The lowest-risk architecture is to first reproduce a DBY-W09-compatible Android userspace using the existing HarmonyOS boot/vendor chain (subject to exact-version and VINTF checks), and only later replace the 4.19 kernel with a new kernel.

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

## Recommended port architecture

### Track A — DerpFest userspace bring-up first

1. Identify the exact DerpFest Android release used by the Coolapk porter, if possible. Exact release matching is preferable to choosing a newer branch by guesswork.
2. Keep the existing DBY-W09 board/boot identity as the source of truth. Do not substitute Motorola pstar/nio board properties.
3. Prefer an initial bring-up that preserves the device-matched stock boot image, ramdisk, DTBO and vendor/odm partitions, unless verified evidence from the Coolapk port proves a different architecture.
4. Build/adapt the DerpFest system userspace and make only the minimum DBY-W09-specific product, VINTF, init and compatibility changes needed.
5. Validate Android boot-complete and hardware surfaces separately. Do not label a launcher boot as a fully working port.
6. Only after this baseline is reproducible should the team consider changing the kernel.

### Track B — ACK/GKI kernel migration later

Keep the android17-6.18 kernel work as an independent future track. Do not force the 6.18 kernel into the first DerpFest userspace milestone. DBY-W09 currently has a legacy boot layout and an Android 12/HarmonyOS vendor stack; a new kernel will add a distinct driver, module, KMI, DTB and boot-image compatibility problem.

## Blocking facts and explicit UNKNOWNs

- The exact Coolapk DerpFest Android version and its porting method are UNKNOWN.
- The user's current HarmonyOS 4.3 system/vendor API, VNDK level and full VINTF state are not verified from EROFS content; the EROFS content layer remains BLOCKED.
- The public API32 same-device precedent is not the user's exact HOS 4.3 firmware baseline. Do not assume every fix or binary is transferable.
- The DBY-W09 display active profile remains UNKNOWN.
- A successful DerpFest launcher boot, Wi-Fi, audio, camera, suspend and update/OTA behavior require separate acceptance evidence.

## Proposed next work

After the current ROUND10 task is completed, create a DerpFest-specific read-only source-and-configuration assessment. It should compare:
- the exact public DerpFest source branch selected for the target Android release;
- Motorola pstar/nio SM8250 build patterns, separating common SoC logic from Motorola-only assumptions;
- DBY-W09 boot header/ramdisk/partition layout facts already established in ROUND1–ROUND9;
- the published DBY-W09 Android 12L/API32 research milestones and their stated limits;
- any exact Coolapk post metadata supplied by the user.

Do not ask the local Agent to repeat FDT/DTBO parsing. Do not ask for firmware re-upload. Do not flash, unlock, root, connect to the device, write partitions, compile, load modules or mount writable filesystems as part of this assessment.
