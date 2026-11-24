# ROUND14 — ACK android17-6.18 boot-critical Kconfig dependency review

Date: 2026-11-24
Status: source review and config fragment draft only; dependency table updated by ROUND15 after re-reading the ACK SM8250 UFS clock and interconnect references. No ACK source sync, Kconfig resolution, Kleaf run, kernel build, DTB build, packaging or device test.

## 1. Purpose

Define the minimum built-in driver dependency chain required for DBY-W09 to enumerate the internal UFS device from the ACK SM8250 DTSI. This is a custom ACK-derived early-boot target, not a claim of certified GKI compliance.

The first milestone is UFS host/PHY initialization and enumeration. Mounting Android logical partitions is a second milestone because ROUND10 could not inspect ramdisk fstab or module loading order.

## 2. Source topology dependencies

Current ACK SM8250 DTSI source view:
https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/arch/arm64/boot/dts/qcom/sm8250.dtsi

Its `ufs_mem_hc` node contains:
- `qcom,sm8250-ufshc` compatible chain;
- lane PHY, clock and reset references;
- `GCC_UFS_PHY_BCR` reset;
- `UFS_PHY_GDSC` power domain;
- IOMMU references to `apps_smmu`;
- UFS AXI/AHB/UniPro and RPMh XO clock references;
- two interconnect paths named `ufs-ddr` and `cpu-ufs`.

Its `ufs_mem_phy` / `ufs_mem_phy_lanes` hierarchy uses `qcom,sm8250-qmp-ufs-phy`, QMP reference/aux clocks and a PHY reset specifier.

This means UFS is not a stand-alone pair of drivers. It depends on Qualcomm clock/GDSC, RPMh, regulator, reset, PHY, MSI and SMMU infrastructure.

## 3. Kconfig dependency map

| Function | Symbol(s) | Dependency / reason | First-stage target |
|---|---|---|---|
| UFS core | `SCSI`, `SCSI_DMA`, `SCSI_UFSHCD` | UFS core requires SCSI and SCSI DMA support | built-in |
| Platform UFS | `SCSI_UFSHCD_PLATFORM` | Platform-bus UFS Host | built-in |
| Qualcomm UFS glue | `SCSI_UFS_QCOM` | Requires platform UFS, ARCH_QCOM, GENERIC_MSI_IRQ and RESET_CONTROLLER | built-in |
| QMP PHY framework | `PHY_QCOM_QMP`, `PHY_QCOM_QMP_UFS` | UFS transceiver PHY | built-in |
| Generic PHY | `GENERIC_PHY` | Consumed by QMP UFS PHY | built-in |
| SM8250 GCC | `COMMON_CLK_QCOM`, `SM_GCC_8250` | UFS GCC clocks and `UFS_PHY_GDSC`; `SM_GCC_8250` selects `QCOM_GDSC` | built-in |
| RPMh clock | `QCOM_RPMH`, `QCOM_CLK_RPMH` | UFS node references `RPMH_CXO_CLK`; RPMh clock driver depends on `QCOM_RPMH` | built-in |
| Command DB | `QCOM_COMMAND_DB` | RPMh resource address/metadata; required by RPMh provider / interconnect path | built-in |
| RPMh regulator | `REGULATOR`, `REGULATOR_QCOM_RPMH` | PM8150 LDO/SMPS rails mapped in ROUND9 | built-in |
| Interconnect core | `INTERCONNECT`, `INTERCONNECT_QCOM` | Generic interconnect framework and Qualcomm provider | built-in |
| SM8250 interconnect | `INTERCONNECT_QCOM_SM8250` | Provides the UFS `ufs-ddr` and `cpu-ufs` paths; selects Qualcomm RPMh/BCM voting backends | built-in |
| Reset | `RESET_CONTROLLER` | Qualcomm UFS Host reset dependency | built-in |
| Generic MSI IRQ | `GENERIC_MSI_IRQ` | Explicit dependency of `SCSI_UFS_QCOM` in current Kconfig | built-in |
| ARM SMMU | `IOMMU_SUPPORT`, `ARM_SMMU` | UFS Host node contains `iommus = <&apps_smmu ...>` | built-in |
| SMMU Qualcomm variant | `ARM_SMMU_QCOM` | Kconfig defaults it on when ARM_SMMU and ARCH_QCOM are enabled | automatic from dependencies |

Key Kconfig/source references:
- UFS Host Kconfig and Qualcomm dependency: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/ufs/host/Kconfig
- QMP PHY / QMP UFS Kconfig: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/phy/qualcomm/Kconfig
- RPMh regulator dependency: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/regulator/Kconfig
- RPMh and RPMh power domain: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/soc/qcom/Kconfig
- SM8250 GCC: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/clk/qcom/Kconfig
- ARM SMMU: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/iommu/Kconfig

The config fragment is a draft input layered on top of a pinned ACK configuration, not a replacement for `gki_defconfig` or the product's full defconfig. Kconfig resolution may add/remove symbols through selects and dependencies. The exact pinned source tree must be used when that phase is authorized.

## 4. Why these are built-in for the first milestone

The device's Android system/vendor/odm logical partitions live on internal UFS. Until ROUND10 ramdisk contents are readable, the first-stage module load order cannot be established. A UFS Host or QMP PHY module cannot safely be assumed to load from a filesystem that itself requires UFS to mount.

Therefore the first custom-kernel milestone sets UFS Host, QMP PHY, clocks, RPMh, regulator, reset and SMMU support to built-in (`=y`). This is a conservative device-kernel bring-up strategy. It changes the GKI module/built-in composition and must not be represented as an unchanged certified GKI build.

The exact Android 17 GKI boot-module path remains separate. DBY-W09's legacy header-v2 + separate-ramdisk layout is not a standard modern `vendor_boot` / `init_boot` layout.

## 5. Storage filesystem and device-mapper phase (not yet frozen)

Existing local facts:
- vendor and odm logical partition images are EROFS signatures.
- Their file contents are unread (EROFS BLOCKED).
- system/cust/hw_product filesystem types and complete fstab/mount chain remain UNKNOWN.
- ROUND10 ramdisk fstab, mount statements and module directives are NOT_READ_BLOCKED.

Likely Android mount-stage candidates to resolve after the ramdisk/partition inventory:
- `BLK_DEV_DM`, `DM_LINEAR` for dynamic logical partitions;
- `DM_VERITY` for verified partitions if fstab uses it;
- `EROFS_FS` for the confirmed vendor/odm partition format;
- `EXT4_FS` and/or `F2FS_FS` for other partitions once filesystem types are confirmed.

These are not included as asserted final values in the storage-first fragment because the exact fstab, AVB chain and full partition formats have not been read. They will likely need to be built in or loaded from a trusted early ramdisk before Android mounts its logical partitions; the correct choice depends on the recovered init sequence.

## 6. Deferred Kconfig groups

| Group | Current treatment | Reason |
|---|---|---|
| SPMI PMIC MFD / PMIC arbiter | deferred from UFS-only fragment | RPMh RSC regulators are not accessed through the SPMI arbiter; enable SPMI path only when PMIC SPMI GPIO/PON/IRQ consumers are added |
| SM8250 pinctrl / TLMM | deferred from UFS-only fragment | Needed for board GPIO/pinctrl peripherals, but minimal UFS node has no board GPIO phandle |
| GENI UART / console | deferred | Existing cmdline contains `androidboot.console=ttyMSM0`, but exact ACK UART node/console driver mapping has not been proven; same-device reference uses uart6 alias, but avoid prematurely assigning a Bluetooth UART as console |
| `QCOM_RPMHPD` | deferred | ACK UFS Host references `UFS_PHY_GDSC` from `&gcc`, provided by `SM_GCC_8250` / `QCOM_GDSC`; it does not use an `&rpmhpd` domain in this DTS path |
| IOMMU extras beyond ARM SMMU | deferred | only required SMMU v2 path is included for UFS |
| Display / touch / WLAN / audio / camera | deferred | each subsystem has additional board/firmware/config dependencies; no need to widen the first UFS bring-up kernel |

## 7. Safety and verification status

- Kconfig names reviewed against current public ACK source references, including the UFS RPMh XO clock and interconnect consumers.
- ROUND15 removed the incorrect implication that `QCOM_RPMHPD` is required for `UFS_PHY_GDSC`; GCC GDSC is the path used by this UFS node.
- Fragment written only as a draft.
- No actual Kconfig resolution (`olddefconfig`) performed.
- No build or module compile performed.
- No local Agent task required for this source-side assessment.
- No device operation, flashing, write, root, module load or writable mount occurred.

## 8. Next step

Next: resolve the PMIC parent-input supply topology from the local HOS4.3 base FDT; then re-check the full olddefconfig result against the exact pinned ACK manifest on an explicitly approved build host. This storage-first fragment remains un-resolved and uncompiled. Keep the custom built-in ACK device kernel and any GKI boot retrofit as separate deliverables.
