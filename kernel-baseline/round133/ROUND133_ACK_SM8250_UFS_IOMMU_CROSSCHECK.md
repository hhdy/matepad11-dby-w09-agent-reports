# ROUND133 — Fixed ACK SM8250 UFS IOMMU stream-ID reconciliation

Date: 2026-11-26
Owner: 1号 AI (ChatGPT)
Scope: read-only source review of fixed ACK 6.18.33, current DBY-W09 DTS draft, and newly mirrored UniXNU reference.
Fixed ACK: `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.

## 1. Result

The fixed target ACK already declares **two SMMU stream IDs on the SM8250 UFS Host**:

```dts
iommus = <&apps_smmu 0x0e0 0>, <&apps_smmu 0x4e0 0>;
```

This is in the pinned `arch/arm64/boot/dts/qcom/sm8250.dtsi`, UFS Host node `ufshc@1d84000`, lines 2507–2521 (file blob `adf6b49b52c48ca05ed6d0c1251f97ace664ef9d`). The referenced `apps_smmu` provider is declared at `iommu@15000000`, compatible `qcom,sm8250-smmu-500`, `qcom,smmu-500`, `arm,mmu-500`, with `#iommu-cells = <2>` (same file lines 5867–5871). The provider node has no `status = "disabled"` property in this SoC DTSI.

The Qualcomm UFS Host in this DTSI is initially disabled by default; the current DBY-W09 board draft enables `&ufs_mem_hc` while adding only board-specific regulator consumers and does **not** replace or delete the inherited `iommus` property.

## 2. Meaning of the two-cell IOMMU specifiers

Pinned ACK `drivers/iommu/arm/arm-smmu/arm-smmu.c` implements `arm_smmu_of_xlate()` at lines 1587–1600:
- first cell `args[0]` is encoded into `ARM_SMMU_SMR_ID` (stream ID);
- second cell `args[1]` is encoded into `ARM_SMMU_SMR_MASK` (stream-match mask).

Therefore the two ACK entries mean:
- stream ID `0x0e0`, mask `0`;
- stream ID `0x4e0`, mask `0`.

They are two distinct stream IDs, not a single combined numeric ID and not regulator/clock values.

The pinned ARM SMMU master code also handles all parsed IDs:
- `arm_smmu_probe_device()` iterates `fwspec->num_ids` and validates each SID/mask against the SMMU capabilities (lines 1431–1462).
- `arm_smmu_master_alloc_smes()` iterates the device's configured stream entries and allocates an SMR/S2CR mapping entry for each (lines 1085–1115).

This is source-level confirmation of the ACK's multi-stream mapping model. It is not a runtime observation of this tablet's SMMU registers or firmware state.

## 3. Cross-check with the six newly mirrored Gitee repositories

The mirrored [UniXNU DBY-W09 repository](https://github.com/hhdy/UniXNU-dby_w09-gitee-mirror) pins the SM8250 UFS implementation through [NativeUfs-alioth](https://github.com/FFT-infra/NativeUfs-alioth/tree/ab5405905a1892da03a9a53e0fa3dcd255d04055). That implementation records the same `0x0e0` and `0x4e0` pair as an SM8250/alioth stream mapping. This is corroborating context only: the driver is XNU code and its feed provenance is an alioth reference; it is not a Linux driver or proof of the exact HOS4.3 live FDT.

The UniXNU `porting.toml` itself documents that its older Linux source cross-reference was a 6.x revision where its UFS node did not show these properties. That observation must not be carried forward as a statement about the user's fixed ACK target: the actual pinned ACK 6.18.33 DTSI does contain both `iommus` entries.

## 4. Current DBY-W09 board draft and storage config

The existing draft:
- includes `sm8250.dtsi` at line 24;
- overlays `&ufs_mem_hc` at lines 214–234 to add HOS4.3 VCC/VCCQ/VCCQ2, VDDP, S8 consumer supplies and `status = "okay"`;
- does not redeclare `iommus`.

Because a board overlay that only adds those properties leaves the base node's unmodified properties intact, the current draft inherits the two ACK SMMU streams. Do not add a duplicate `iommus` declaration unless a later source comparison proves the inherited property has been removed or overridden.

The existing storage-first config fragment also already includes:
`CONFIG_IOMMU_SUPPORT=y` and `CONFIG_ARM_SMMU=y`; it comments that `ARM_SMMU_QCOM` is selected/defaulted under `ARM_SMMU && ARCH_QCOM`. The fragment is still a draft; its Kconfig resolution has not been run.

Sources:
- [Pinned ACK SM8250 UFS node](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/boot/dts/qcom/sm8250.dtsi#L2507-L2521)
- [Pinned ACK apps_smmu provider](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/boot/dts/qcom/sm8250.dtsi#L5867-L5871)
- [Pinned ACK ARM SMMU OF translation](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/iommu/arm/arm-smmu/arm-smmu.c#L1587-L1600)
- [Pinned ACK ARM SMMU multi-stream allocation](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/iommu/arm/arm-smmu/arm-smmu.c#L1085-L1115)

## 5. HOS4.3 boundary — still needs one narrow offline confirmation

ROUND21's report confirms the stock UFS Host node is `/soc/ufshc@1d84000` and that its nine UFS overlay fragments do not add clocks, resets, pinctrl, power-domains, required-opps or regulator rails except the documented supply set. However, the report does not provide an explicit property census for `iommus` on the UFS Host, nor the resolved SMMU provider path and two stream cells.

Accordingly:
- Do **not** claim that HOS4.3 has or lacks the same `iommus` property based solely on ROUND21.
- Do **not** infer the runtime-selected DTBO entry.
- A narrow Agent read-only parse of the already-existing ROUND3 base FDT candidates and nine DTBOs is the next appropriate check.
- The fixed ACK board DTSI mapping above is already confirmed and need not be recopied into the custom board file.

## 6. Limits and disposition

- This source review changed no kernel code, DTS, binding, config, patch series, branch or PR.
- No build, schema validation, firmware extraction, live FDT read or device operation was performed.
- No assertion is made about the actual SMMU stream table, context banks, translation regime, bootloader-programmed bypass state, or selected runtime overlay on the user's device.
- The two IDs are confirmed in the fixed ACK SM8250 SoC DTSI and are already inherited by the draft; HOS4.3-specific FDT comparison remains open.
