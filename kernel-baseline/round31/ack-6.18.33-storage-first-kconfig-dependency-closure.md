# ROUND31 — ACK .33 storage-first Kconfig dependency closure

Date: 2026-11-24

Status: exact-tag Kconfig / Makefile / source-binding review against ACK android17-6.18.33_r00. No Kconfig resolver, olddefconfig, dtc, dt-schema, compiler or device was run. The existing fragment remains a draft and has not been used to build a kernel.

Pinned source:
- ACK tag: android17-6.18.33_r00
- target commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

## 1. Result

The existing storage-first fragment has the correct major driver symbols for DBY-W09's first UFS milestone. This round closes the dependency relationships and identifies which hidden Kconfig symbols are selected transitively rather than set manually.

The confirmed storage path is:
- SCSI disk layer and UFS Host core/platform/QCOM glue;
- Qualcomm QMP UFS PHY;
- SM8250 GCC + RPMh clock;
- RPMh regulator / RPMh power-domain provider;
- SM8250 RPMh/BCM interconnect;
- ARM SMMU v2 with Qualcomm implementation;
- block device-mapper + EROFS for the known dynamic vendor/odm partitions.

UFS/QMP and the providers they need before the root filesystem is mounted should remain built-in for the first bring-up. ROUND10 ramdisk module inventory is still BLOCKED, so no module-loading route is assumed.

## 2. Required direct config symbols

| Symbol | First-milestone value | Exact dependency / evidence |
|---|---:|---|
| SCSI | y | Parent SCSI subsystem |
| SCSI_DMA | y | Required by SCSI_UFSHCD |
| SCSI_UFSHCD | y | UFS host core; selects PM_DEVFREQ, DEVFREQ_GOV_SIMPLE_ONDEMAND, NLS |
| SCSI_UFSHCD_PLATFORM | y | UFS platform controller driver; requires HAS_IOMEM |
| SCSI_UFS_QCOM | y | Requires SCSI_UFSHCD_PLATFORM, ARCH_QCOM, GENERIC_MSI_IRQ, RESET_CONTROLLER |
| GENERIC_PHY | y | PHY framework used by QMP UFS |
| PHY_QCOM_QMP | y | Requires OF, COMMON_CLK, ARCH_QCOM or compile-test |
| PHY_QCOM_QMP_UFS | y | QMP UFS PHY implementation; selects GENERIC_PHY, defaults to parent PHY_QCOM_QMP |
| COMMON_CLK | y | Clock framework |
| COMMON_CLK_QCOM | y | Qualcomm clock controller family; requires OF and ARCH_QCOM |
| SM_GCC_8250 | y | SM8250 GCC / UFS clocks / UFS PHY GDSC; selects QCOM_GDSC |
| QCOM_CLK_RPMH | y | RPMh clock controller; requires QCOM_RPMH |
| RESET_CONTROLLER | y | Required by Qualcomm UFS Host glue |
| INTERCONNECT | y | Interconnect core |
| INTERCONNECT_QCOM | y | Qualcomm interconnect provider family; requires ARCH_QCOM |
| INTERCONNECT_QCOM_SM8250 | y | SM8250 interconnect; requires RPMh-capable interconnect backend |
| QCOM_COMMAND_DB | y | RPMh resource address/AUX lookup; requires ARCH_QCOM and OF_RESERVED_MEM |
| QCOM_RPMH | y | RPMh request transport |
| QCOM_RPMHPD | y | RPMh Generic PM domain provider; requires QCOM_RPMH and Command DB |
| REGULATOR | y | Regulator core |
| REGULATOR_QCOM_RPMH | y | PM8150/PM8150L RPMh VRM/XOB regulators; requires RPMh and Command DB |
| IOMMU_SUPPORT | y | ARM64 default is y when MMU is enabled |
| ARM_SMMU | y | ARM SMMU v1/v2; selects IOMMU API and LPAE page tables |
| BLK_DEV_DM | y | Device-mapper core; dm-linear is built into dm-mod, not a separate CONFIG_DM_LINEAR symbol |
| EROFS_FS | y | Confirmed vendor/odm filesystem type |
| BLOCK | y | Required by block, DM and EROFS |
| BLK_DEV_SD | y | SCSI disk block driver |

The current fragment explicitly enables the core driver symbols, while the frozen base GKI config provides some general subsystem symbols. The final resolved .config must still be checked for every row.

## 3. Hidden / transitive Kconfig relationships

Do not try to add hidden symbols as if they were user-selectable menu options. The exact Kconfig shows these relationships:

### 3.1 UFS → devfreq → OPP

- SCSI_UFSHCD selects PM_DEVFREQ.
- PM_DEVFREQ selects PM_OPP.
- This makes the OPP framework available for UFS's OPP table and required-OPP handling, even though the storage fragment does not explicitly set hidden CONFIG_PM_OPP.
- SCSI_UFSHCD also selects the simple ondemand devfreq governor; this is part of the UFS clock-scaling path.

### 3.2 SM8250 GCC → Generic PM domains

- SM_GCC_8250 selects QCOM_GDSC.
- QCOM_GDSC selects PM_GENERIC_DOMAINS when PM is enabled.
- PM_GENERIC_DOMAINS_OF is def_bool y when PM_GENERIC_DOMAINS and OF are enabled.
- Therefore the Host's GCC UFS_PHY_GDSC consumer has the generic PM-domain framework when SM_GCC_8250=y and PM=y.

### 3.3 RPMh interconnect backend

- INTERCONNECT_QCOM_SM8250 depends on INTERCONNECT_QCOM_RPMH_POSSIBLE.
- The possible helper requires the Qualcomm interconnect parent, RPMh, Command DB and OF; it defaults from INTERCONNECT_QCOM.
- The SM8250 driver selects both INTERCONNECT_QCOM_RPMH and INTERCONNECT_QCOM_BCM_VOTER.
- These are needed for the two UFS interconnect paths (UFS DDR and CPU-to-UFS config).

### 3.4 SMMU implementation

- ARM_SMMU_QCOM is declared as def_tristate y inside if ARM_SMMU, depends on ARCH_QCOM, and selects QCOM_SCM.
- Thus with ARM_SMMU=y and ARCH_QCOM=y, the Qualcomm implementation is enabled automatically in the resolved config. It is not a separate menu tristate that needs a manually forced value.
- IOMMU_DMA is def_bool ARM64; OF_IOMMU is def_bool y when OF and IOMMU_API are enabled.

## 4. Baseline GKI config comparison

The exact-tag arch/arm64/configs/gki_defconfig already enables:
- ARCH_QCOM;
- BLK_DEV_DM;
- SCSI_UFSHCD and SCSI_UFSHCD_PLATFORM;
- EROFS_FS.

It does not by itself represent the DBY-W09 board-specific storage closure. The device fragment must additionally ensure:
- SCSI_UFS_QCOM;
- PHY_QCOM_QMP + PHY_QCOM_QMP_UFS;
- COMMON_CLK_QCOM + SM_GCC_8250 + QCOM_CLK_RPMH;
- INTERCONNECT_QCOM + INTERCONNECT_QCOM_SM8250;
- QCOM_COMMAND_DB, QCOM_RPMH, QCOM_RPMHPD, REGULATOR_QCOM_RPMH;
- ARM_SMMU;
- the target block/filesystem and boot-chain options.

This is still a minimal storage milestone, not the final full-device config. Keep display/GPU/USB-C/DP/thermal/WLAN/audio/camera and unrelated subsystem drivers out until their DTS/provider evidence is ready.

## 5. Boot-critical built-in vs module policy

| Component | First milestone | Reason |
|---|---|---|
| UFS core + platform + QCOM glue | built-in (=y) | Needed to enumerate the root storage device |
| QMP UFS PHY | built-in (=y) | Required before UFS link startup |
| SM8250 GCC + RPMh clock | built-in (=y) | UFS clocks and UFS PHY GDSC |
| RPMh transport + Command DB | built-in (=y) | Provider dependency for clocks/regulators/RPMhPD |
| RPMh regulator + RPMhPD | built-in (=y) | UFS rails / OPP performance domain must be ready during probe |
| SM8250 interconnect / BCM voter | built-in (=y) | UFS controller's named ICC paths must resolve before use |
| ARM SMMU | built-in (=y) | Host DTS has SMMU stream IDs and needs translation setup |
| DM + EROFS | built-in (=y) | First-stage maps logical partitions and mounts vendor/odm |

This policy follows the current known boot path and does not claim the final module design is impossible. If ROUND10 later proves a usable matching initramfs module tree, selected non-root-critical drivers can be reconsidered; the default for this milestone remains built-in.

## 6. Binding observation for the dual-GenPD UFS candidate

Exact qcom,ufs.yaml in this ACK tag:
- the schema's select.compatible list omits qcom,sm8250-ufshc, even though sm8250.dtsi uses that compatible;
- the Qualcomm binding does not define a dedicated power-domains property or a per-domain name list;
- ufs-common.yaml also does not define power-domains; it focuses on UFS clocks, OPP, supplies and common tuning properties;
- the generic power-domain binding allows a consumer to refer to a provider and describes dependencies between power domains, but it does not define a UFS-specific maximum count.

This means the proposed Host dual-domain property is not explicitly constrained by a maxItems rule in the inspected UFS schema, but that is not equivalent to a successful dt-schema validation. The schema's SM8250 compatible coverage itself deserves a targeted binding correction or a confirmed matching-schema explanation before the two-domain DTS change is promoted. No dt-schema run was performed.

Do not add power-domain-names by guesswork. The .33 attach-list API consumes the standard power-domains phandle order when no names array is supplied; the candidate order remains MMCX index 0, UFS PHY GDSC index 1.

## 7. Outstanding checks

- Run Kconfig resolution against the frozen .33_r00 source using the pinned base GKI config and this board fragment; none run in this round.
- Confirm all final built-in values in .config, especially the RPMh interconnect helpers, ARM SMMU QCOM def-tristate, and generic PM-domain OF support.
- Verify target DTS provider nodes for RPMh regulator, RPMhPD, RPMh clocks, GCC, SMMU and both interconnect providers all exist and are enabled in the board DTB.
- Resolve the binding/schema coverage for qcom,sm8250-ufshc and the dual power-domains order before modifying the DTS.
- Keep ROUND12 as the only local Agent task; do not issue a second firmware scan in parallel.

## 8. Exact sources

- ACK tag: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00
- GKI base config: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/arch/arm64/configs/gki_defconfig
- UFS top-level Kconfig: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/ufs/Kconfig
- UFS core Kconfig: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/ufs/core/Kconfig
- UFS platform/QCOM Kconfig: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/ufs/host/Kconfig
- QMP PHY Kconfig: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/phy/qualcomm/Kconfig
- Qualcomm clock Kconfig: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/clk/qcom/Kconfig
- Qualcomm interconnect Kconfig: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/interconnect/qcom/Kconfig
- Qualcomm RPMh / Command DB Kconfig: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/soc/qcom/Kconfig
- RPMHPD Kconfig: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/pmdomain/qcom/Kconfig
- ARM SMMU Kconfig: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/iommu/arm/Kconfig
- dm-verity Kconfig: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/md/Kconfig
- EROFS Kconfig: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/fs/erofs/Kconfig
- Qualcomm UFS binding: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/Documentation/devicetree/bindings/ufs/qcom,ufs.yaml
- UFS common binding: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/Documentation/devicetree/bindings/ufs/ufs-common.yaml
- Generic power-domain binding: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/Documentation/devicetree/bindings/power/power-domain.yaml
