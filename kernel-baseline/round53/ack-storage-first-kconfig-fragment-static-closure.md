# ROUND53 — Storage-first Kconfig fragment static dependency-closure audit

Date: 2026-11-24

Status: **PINNED-SOURCE KCONFIG DEPENDENCIES CROSS-CHECKED; ACTUAL KCONFIG RESOLUTION / FINAL .CONFIG NOT RUN.**

## 1. Scope and immutable baseline

This round audits the existing storage-first config fragment against the exact ACK source tree, rather than treating symbol names/comments as proof that the selected options can resolve.

- ACK tag: `android17-6.18.33_r00`
- Immutable source commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Base config: `arch/arm64/configs/gki_defconfig`, blob `a3e1c0d60d5220b6be8b306157a331fc1696afb0`
- Device fragment: `config/dby-w09-ack18-storage-first.fragment.draft`
- Pre-audit fragment blob: `20f88ec3ea2d42e59d297268cce15940c1630a9d`
- Corrected fragment blob: `d708791962e7a8bebbe6d5d07658c53e6c8808bb`

This is public-source and config-text review only. No Kconfig parser, `olddefconfig`, `savedefconfig`, Kleaf, or kernel build was run.

## 2. Base GKI facts established

The pinned `gki_defconfig` already explicitly sets the following relevant options to built-in:

- `CONFIG_ARCH_QCOM=y`
- `CONFIG_SCSI=y`
- `CONFIG_BLK_DEV_SD=y`
- `CONFIG_SCSI_UFSHCD=y`
- `CONFIG_SCSI_UFSHCD_PLATFORM=y`
- `CONFIG_REGULATOR=y`
- `CONFIG_BLK_DEV_DM=y`
- `CONFIG_DM_VERITY=y`
- `CONFIG_DM_VERITY_FEC=y`
- `CONFIG_EROFS_FS=y`

These are inherited base-config settings, not new hardware-enablement discoveries. The fragment repeats several intentionally to make its storage-first requirements legible.

Absence of an explicit `CONFIG_...` assignment in `gki_defconfig` is **not** treated as `n`: some symbols are defaults, hidden symbols, architecture selections, or Kconfig-selected dependencies. The final resolved `.config` remains the only definitive check.

## 3. UFS host and OPP dependency chain

Pinned ACK source confirms:

1. `SCSI_UFSHCD` depends on `SCSI && SCSI_DMA` and selects `PM_DEVFREQ`.
2. `SCSI` selects `SCSI_DMA` when `HAS_DMA`; the fragment's explicit `SCSI_DMA=y` is redundant but consistent for arm64.
3. `PM_DEVFREQ` selects hidden `PM_OPP`.
4. `SCSI_UFSHCD_PLATFORM` depends on `HAS_IOMEM`; arm64 satisfies the platform's MMIO capability.
5. `SCSI_UFS_QCOM` depends on `SCSI_UFSHCD_PLATFORM && ARCH_QCOM`, plus `GENERIC_MSI_IRQ` and `RESET_CONTROLLER`.
6. The fragment explicitly requests `GENERIC_MSI_IRQ=y` and `RESET_CONTROLLER=y`; `COMMON_CLK_QCOM` also selects `RESET_CONTROLLER`.

Therefore the intended built-in route for the ROUND33 UFS OPP helper is source-consistent:

`SCSI_UFSHCD=y → PM_DEVFREQ=y → PM_OPP=y`

The OPP helper's APIs are not a missing direct config symbol; they are reached through the UFS selection chain.

Relevant pinned blobs:
- `drivers/ufs/Kconfig`: `90226f72c158aad3253f5854f02c4a66ea25d83f`
- `drivers/ufs/host/Kconfig`: `48ee7e9b665efcb376f32746b49fbe437e7dd618`
- `drivers/scsi/Kconfig`: `19d0884479a247f1e91300bcfc1112e7b3ea5e46`
- `drivers/devfreq/Kconfig`: `c999c4a1e56756920633059fd4cbe3b885abf26b`

## 4. QMP UFS PHY and GCC/RPMh clocks

Pinned source confirms:

- `PHY_QCOM_QMP` depends on `OF && COMMON_CLK && (ARCH_QCOM || COMPILE_TEST)`.
- `PHY_QCOM_QMP_UFS` selects `GENERIC_PHY` and defaults to the parent `PHY_QCOM_QMP`.
- `COMMON_CLK_QCOM` depends on `OF` and `ARCH_QCOM || COMPILE_TEST`; it selects `RESET_CONTROLLER`, `INTERCONNECT`, and `INTERCONNECT_CLK`.
- `QCOM_CLK_RPMH` is nested under `COMMON_CLK_QCOM` and depends on `QCOM_RPMH`.
- `SM_GCC_8250` is nested under `COMMON_CLK_QCOM`, depends on `ARM64 || COMPILE_TEST`, and selects hidden `QCOM_GDSC`.
- `QCOM_GDSC` selects `PM_GENERIC_DOMAINS` when `PM=y`.

Thus the fragment's parent/child requests are consistent:
- `COMMON_CLK=y`
- `COMMON_CLK_QCOM=y`
- `QCOM_CLK_RPMH=y`
- `SM_GCC_8250=y`
- `PM=y`

The explicit UFS PHY and GCC entries are not standalone drivers; they are children of their parent menuconfig and must resolve with the parent dependencies enabled.

Pinned blobs:
- `drivers/phy/qualcomm/Kconfig`: `60a0ead127fa9f08749e1bc686e15cc5eb341c28`
- `drivers/clk/qcom/Kconfig`: `6fef0bfc17736b62e89d4d2e434a0a59f4f081aa`

## 5. Interconnect dependency chain

The ACK SM8250 UFS node has the two interconnect paths audited in prior rounds. The Kconfig source establishes:

- `INTERCONNECT_QCOM` depends on `ARCH_QCOM`.
- `INTERCONNECT_QCOM_RPMH_POSSIBLE` defaults to `INTERCONNECT_QCOM` and depends on `QCOM_RPMH`, `QCOM_COMMAND_DB`, and `OF` (with a separate compile-test exception).
- `INTERCONNECT_QCOM_SM8250` depends on `INTERCONNECT_QCOM_RPMH_POSSIBLE`, then selects `INTERCONNECT_QCOM_RPMH` and `INTERCONNECT_QCOM_BCM_VOTER`.

The fragment requests `INTERCONNECT`, `INTERCONNECT_QCOM`, `INTERCONNECT_QCOM_SM8250`, `QCOM_RPMH`, `QCOM_COMMAND_DB`, and `OF`; this closes the declared dependency chain. The child RPMh transport and BCM voter are selected by the SM8250 driver rather than requiring additional direct fragment lines.

Pinned blob:
- `drivers/interconnect/qcom/Kconfig`: `5b4bb9f1382b2fd3c14b6f1ea35c43ac9fddd803`

## 6. Command DB, RPMhPD and RPMh regulator providers

The fixed ACK Kconfig contracts are:

- `QCOM_COMMAND_DB` depends on `ARCH_QCOM || COMPILE_TEST` and `OF_RESERVED_MEM`.
- `OF_RESERVED_MEM` is `def_bool OF_EARLY_FLATTREE`; it is derived from the OF early flattened-tree path, not an independent selectable driver.
- `QCOM_RPMH` depends on `ARCH_QCOM || COMPILE_TEST` and has the source-declared Command DB relationship.
- `QCOM_RPMHPD` depends on both `QCOM_RPMH` and `QCOM_COMMAND_DB`.
- `REGULATOR_QCOM_RPMH` depends on both `QCOM_RPMH` and `QCOM_COMMAND_DB).
- `QCOM_CLK_RPMH` depends on `QCOM_RPMH`.

The fragment requests all the externally selectable nodes in this chain. `OF_RESERVED_MEM` is explicitly stated for clarity; its Kconfig definition is automatically enabled when `OF_EARLY_FLATTREE` is enabled.

The PM-domain Makefile only descends into the `pmdomain/` subtree when `PM_GENERIC_DOMAINS` is enabled. The `SM_GCC_8250 → QCOM_GDSC → PM_GENERIC_DOMAINS if PM` chain supplies that requirement for the first UFS milestone. The RPMhPD symbol has its own provider dependencies; its source inclusion additionally relies on the generic-domain subsystem being built.

Pinned blobs:
- `drivers/soc/qcom/Kconfig`: `2caadbbcf8307ff94f5afbdd1481e5e5e291749f`
- `drivers/pmdomain/qcom/Kconfig`: reviewed in this pass
- `drivers/regulator/Kconfig`: `d84f3d054c59d86d91d859808aa73a3b609d16d0`
- `drivers/pmdomain/Makefile`: `ebc802f13eb953db750f5a9507caa64c637a957a`
- `drivers/pmdomain/qcom/Makefile`: `403dfc5af095b05beeb948285a3848219044cfce`

## 7. SMMU / Qualcomm SMMU implementation

Pinned ACK confirms:

- `IOMMU_SUPPORT` is a bool menuconfig depending on `MMU` and defaults to y.
- `ARM_SMMU` depends on `ARM64 || ARM || COMPILE_TEST`, and selects `IOMMU_API` and `IOMMU_IO_PGTABLE_LPAE`.
- `ARM_SMMU_QCOM` is a `def_tristate y` under `if ARM_SMMU`, depends on `ARCH_QCOM`, and selects `QCOM_SCM`.
- The ARM SMMU Makefile appends `arm-smmu-qcom.o` when `CONFIG_ARM_SMMU_QCOM` is enabled.

Therefore the fragment's `IOMMU_SUPPORT=y`, `ARM_SMMU=y`, and inherited `ARCH_QCOM=y` establish the expected Qualcomm SMMU implementation selection; no separate explicit `CONFIG_ARM_SMMU_QCOM=y` line is needed. The fragment correctly leaves it as an automatically derived symbol.

Pinned blobs:
- `drivers/iommu/Kconfig`: `aa4262f1f441d2d9fa263f07d2021587f08e4810`
- `drivers/iommu/arm/Kconfig`: `3a2611ffe62fac167542129936a077d23b4334da`
- `drivers/iommu/arm/arm-smmu/Makefile`: `2a5a95e8e3f938c7fed32a6b4e2e53ba3144b67b`

## 8. DM / EROFS / AVB capability correction

The exact pinned GKI base config already includes:
- `CONFIG_BLK_DEV_DM=y`
- `CONFIG_DM_VERITY=y`
- `CONFIG_DM_VERITY_FEC=y`
- `CONFIG_EROFS_FS=y`

The device fragment repeats the Device Mapper and EROFS requirements for the storage-first intent. The previous comment implied DM_VERITY/FEC still needed to be enabled after ROUND12; that was inaccurate because the base config already has both built-in. The fragment comment has been corrected to state that the kernel capability is inherited.

This does **not** resolve AVB. ROUND12 remains BLOCKED at the trusted local tool gate; the actual boot/vbmeta descriptor contents, hashtree/FEC use, fstab policy, and image chain remain UNKNOWN. Having DM_VERITY/FEC compiled in is not proof that the target image requires or correctly configures those features.

The pinned `drivers/md/Kconfig` defines `BLK_DEV_DM` and `DM_VERITY`; `DM_VERITY_FEC` depends on `DM_VERITY`. Device-mapper linear is part of the DM core and does not have a standalone `CONFIG_DM_LINEAR` symbol.

## 9. Fragment/base comparison and disposition

Explicit assignments already present with the same built-in value in pinned `gki_defconfig` include ARCH_QCOM, SCSI, BLK_DEV_SD, SCSI_UFSHCD, SCSI_UFSHCD_PLATFORM, REGULATOR, BLK_DEV_DM, DM_VERITY, DM_VERITY_FEC and EROFS_FS. Repeating them in the fragment is redundant but consistent and communicates the minimum desired storage composition.

Other listed values are not necessarily disabled when absent from `gki_defconfig`; they can be defaults, hidden symbols, or selected by the explicit chain above. This round did not label those as n or claim the final .config value.

No missing Kconfig dependency was identified in the static source review. No new direct config symbol is proposed. The only concrete correction in this round is the AVB capability comment in the device fragment.

## 10. Validation not performed / next step

Still NOT_RUN:
- Run `make ARCH=arm64 gki_defconfig` and the frozen board fragment through the exact ACK Kconfig resolver.
- Run `olddefconfig` and capture the final `.config`.
- Assert all UFS/QMP/GCC/RPMhPD/ICC/SMMU/DM/EROFS requirements resolve to built-in `y`, not `m` or `n`.
- Check for unknown fragment symbols, dependency warnings, unmet direct dependencies, and silently downgraded tristates.
- Run the actual pinned Kleaf full-image `kernel_build` path and inspect produced vmlinux/Image/modules/config artifacts.

The next real Kconfig gate requires the full ACK source worktree and pinned build environment. It does not require another local firmware scan. The Local Agent queue remains empty; no ROUND15 task was created.
