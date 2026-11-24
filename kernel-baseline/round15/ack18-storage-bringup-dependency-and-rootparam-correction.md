# ROUND15 — ACK UFS first-stage dependency and DBY-W09 rootparam corrections

Date: 2026-11-24

Status: source-side review and text-draft corrections completed. ROUND11 local read-only HOS4.3 base-FDT parent-supply verification is complete; ROUND16 documents the result and ACK translation boundary. No dtc, dt-schema, Kconfig resolution, kernel/DTB build, packaging, ABL acceptance test or device boot was run.

## 1. Main corrections

ROUND13/14 and the review branch have been updated in response to a closer pass over the local reports and current ACK SM8250 DTS/Kconfig topology.

### 1.1 Preserve the stock rootparam modem_id sentinel

ROUND7's sanitized local DTBO property inventory contains huawei,modem_id for each of the nine stock DTBO entries. All nine report the same generic sentinel pair 0xffffffff, 0; it is not a per-device identifier.

The same-device public Linux project's minimal dby-w09-rootparam.dtso also preserves this field. The ACK minimal overlay draft now includes:

~~~dts
huawei,modem_id = <0xffffffff 0x00>;
~~~

This improves fidelity to the stock rootparam contract. It is not proof that a newly assembled DTBO image, header, entry table, compatible strings or ABL selection logic will be accepted by the user's HOS4.3 bootloader. No new DTBO binary was created or tested.

Source reference:
https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso

### 1.2 Remove the unverified PMIC parent-supply assumption

The local ROUND7 CSV inventory confirms the relevant PM8150 RPMh regulator provider nodes and the output rails used by UFS:

| Rail | Local base-FDT inventory evidence |
|---|---|
| PM8150 S4 | regulator name pm8150_s4, 1.8–1.92 V |
| PM8150 L5 | regulator name pm8150_l5, 0.88 V |
| PM8150 L6 | regulator name pm8150_l6, 1.2 V |
| PM8150 L9 | regulator name pm8150_l9, 1.2 V |
| PM8150 L17 | regulator name pm8150_l17, 2.496–3.008 V |

ROUND9 independently resolves the actual UFS consumer-to-supply closure and max-current constraints.

However, the ROUND7 property inventory does not record vph_pwr, vdd-s*-supply, or another explicit input-supply relationship for those RPMh provider groups. That omission is not proof the properties are absent from the raw FDT; the inventory may not have exported those fields.

The same-device Linux 7.0 public DTS includes a fixed 3.7 V vph_pwr node and links vdd-s1-supply through vdd-s10-supply to it. Its own source comment says its board/PMIC information was checked against HarmonyOS 4.2. This is useful corroboration, but it is not sufficient evidence to declare the topology correct for the user's HOS4.3 firmware.

Therefore the current ACK DTS draft has removed:
- the provisional fixed 3.7 V vph_pwr regulator node;
- the speculative vdd-s1-supply ... vdd-s10-supply parent links.

The draft keeps only the PM8150 VRM output rails used by UFS, whose voltages and UFS consumer references are locally resolved. ROUND11 is now complete: it found four parent links only inside legacy ARC voltage-level groups, six ARC proxy links, and no vdd-s, vin or vph-pwr input properties anywhere in the base FDT. The physical PM8150 input topology remains unspecified rather than guessed. See ROUND16 for the distinction and the upstream ACK mapping limit.

### 1.3 Complete the UFS source-level Kconfig consumers

The earlier storage-first fragment omitted two consumers visible in the ACK SM8250 UFS Host DTSI: RPMh XO clock and interconnect paths. The draft now includes:

~~~text
CONFIG_SCSI_DMA=y
CONFIG_QCOM_CLK_RPMH=y
CONFIG_QCOM_RPMHPD=y
CONFIG_INTERCONNECT=y
CONFIG_INTERCONNECT_QCOM=y
CONFIG_INTERCONNECT_QCOM_SM8250=y
~~~

The fragment also explicitly lists CONFIG_ARM_SMMU_QCOM=y alongside the ARM SMMU core, subject to final resolution by the pinned ACK Kconfig.

The ACK ufs_mem_hc node references:
- GCC UFS clocks, GCC_UFS_PHY_BCR reset and UFS_PHY_GDSC;
- RPMh RPMH_CXO_CLK;
- IOMMU stream IDs under apps_smmu;
- interconnect paths ufs-ddr and cpu-ufs.

The Qualcomm SM8250 interconnect driver provides those SoC paths and selects its RPMh/BCM voting backend. QCOM_CLK_RPMH is the provider for RPMh clocks and depends on QCOM_RPMH.

References:
- ACK SM8250 DTS: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/arch/arm64/boot/dts/qcom/sm8250.dtsi
- Qualcomm clock Kconfig: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/clk/qcom/Kconfig
- Qualcomm interconnect Kconfig: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/interconnect/qcom/Kconfig
- UFS Host Kconfig: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/ufs/host/Kconfig

### 1.4 Keep the direct GCC GDSC and RPMh OPP paths distinct

The UFS Host DTSI has a direct power-domains reference to UFS_PHY_GDSC from the SM8250 GCC provider (&gcc). SM_GCC_8250 selects QCOM_GDSC, which supplies this direct generic power-domain.

However, the same ufs_mem_hc node also references ufs_opp_table. Its OPP entries carry required-opps references to rpmhpd_opp_low_svs and rpmhpd_opp_nom. The UFS clock-scaling path can call dev_pm_opp_set_opp(), so those OPP transitions need the RPMh power-domain OPP provider. Consequently CONFIG_QCOM_RPMHPD remains built-in in the storage-first fragment for the OPP path, not because UFS_PHY_GDSC is an RPMh domain. Exact pinned-ACK behavior must still be confirmed with Kconfig resolution and source build; no runtime test was run.

Likewise, the RPMh regulator provider under apps_rsc is distinct from the SPMI PMIC arbiter path. The minimal UFS-only DTS has no PMIC SPMI GPIO/PON/IRQ consumers, so SPMI_MSM_PMIC_ARB, MFD_SPMI_PMIC and PMIC SPMI pinctrl stay deferred for now.

References:
- SM8250 GCC Kconfig: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/clk/qcom/Kconfig
- RPMh power-domain Kconfig: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/soc/qcom/Kconfig
- SPMI PMIC arbiter / MFD Kconfig: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/spmi/Kconfig and https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/mfd/Kconfig

## 2. Updated review-branch files

Branch: ack18-dby-w09-dts-draft

- dts/dby-w09-ack18-board.dts.draft — removed unverified vph_pwr / vdd-s*-supply input topology.
- dts/dby-w09-ack18-rootparam.dtso.draft — restored stock generic huawei,modem_id sentinel.
- config/dby-w09-ack18-storage-first.fragment.draft — added SCSI DMA, RPMh XO clock, SM8250 interconnect support and explicit SMMU variant; retained QCOM_RPMHPD for UFS OPP required-opps (separate from the direct GCC GDSC).
- dts/README.md — updated limitations and evidence boundary.

ROUND15 follow-up note: the UFS OPP table includes required-opps references to RPMh power-domain OPP states. The config fragment and ROUND14 table retain QCOM_RPMHPD for OPP scaling; this is separate from the direct GCC UFS_PHY_GDSC reference. ROUND16 additionally establishes that HOS4.3's ARC *-parent-supply graph must not be copied into the ACK VRM regulator node.

These remain .draft files, not build inputs.

## 3. Current verification state

| Item | Status |
|---|---|
| ROUND7 output-rail regulator names / voltage properties rechecked | SOURCE INVENTORY REVIEWED |
| ROUND9 UFS phandle supply closure | PREVIOUSLY COMPLETE |
| All nine stock DTBO rootparam sentinel values compared | SOURCE INVENTORY REVIEWED |
| Public same-device minimal overlay compared | SOURCE REVIEWED |
| PMIC input/parent properties in HOS4.3 base FDT | ROUND11 COMPLETE — four ARC level parents, six ARC proxy links; no vdd-s / vin / vph-pwr input properties |
| Exact ABL acceptance of a new minimal DTBO | UNKNOWN / NOT_TESTED |
| UFS clock/interconnect source-level consumer mapping | SOURCE REVIEWED |
| UFS OPP required-opps RPMhPD dependency | SOURCE REVIEWED; QCOM_RPMHPD RETAINED |
| Kconfig fragment olddefconfig resolution | NOT_RUN |
| dtc / dt-schema validation | NOT_RUN |
| Kernel / DTB compile or image packaging | NOT_RUN |
| Device boot / UFS runtime | NOT_RUN |
| Any device write / flash / unlock | NO |

## 4. Next steps

1. The only new local dependency is ROUND11: read-only check of PM8150 RPMh parent-input supply properties in the already-existing HOS4.3 base FDT, using an already installed and trusted FDT inspection tool only. If no such tool is already available, report BLOCKED; do not install tools, write a parser or invoke WSL.
2. GPT continues with ACK console/GENI UART and the remaining UFS regulator/clock provider audit using public source and current drafts.
3. After parent topology is resolved, update the DTS draft. Only after all static source reviews and an explicitly approved build environment exist should dtc, schema, Kconfig resolution or compilation be considered.
4. Keep the minimal DTS and Kconfig files suffixed .draft; keep PR #1 Draft. No flashing, device connection or writes.

## 5. Safety boundary

The local task is read-only and narrowly scoped. No firmware, boot, ramdisk, DTB, DTBO, FDT or binary output is to be uploaded. Only a short sanitized text report may be committed to the Agent branch. No identifiers, addresses, local absolute paths, full local hashes, secrets or unrelated hardware properties are needed.
