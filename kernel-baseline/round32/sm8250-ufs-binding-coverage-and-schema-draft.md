# ROUND32 — SM8250 UFS Device Tree binding coverage and schema patch draft

Date: 2026-11-24

Status: exact ACK .33 binding comparison plus current upstream Linux binding comparison. A schema-only patch draft was created. No dt_binding_check, dtbs_check, dtc, schema test, driver patch, build, device operation or write was run.

Source pin:
- ACK: android17-6.18.33_r00
- ACK commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

## 1. Finding

The qcom,ufs.yaml schema in the pinned ACK .33 source omits qcom,sm8250-ufshc from:
- select.properties.compatible.contains.enum;
- properties.compatible.items[0].enum;
- any compatible-specific clock/register layout branch.

The same omission is present in the current Torvalds Linux master qcom,ufs.yaml at the time of this review. This is not specific to the older ACK tag.

However, arch/arm64/boot/dts/qcom/sm8250.dtsi in both the pinned ACK source and the current upstream tree defines the UFS host as:
- qcom,sm8250-ufshc;
- qcom,ufshc;
- jedec,ufs-2.0.

The same node has exactly eight clocks and a single register range:
- core_clk;
- bus_aggr_clk;
- iface_clk;
- core_clk_unipro;
- ref_clk;
- tx_lane0_sync_clk;
- rx_lane0_sync_clk;
- rx_lane1_sync_clk.

It does not define an ICE register range, reg-names pair or ice_core_clk.

The existing schema branches cannot be reused:
- SM8150/SDM845/SM6350 expects nine clocks, with ice_core_clk as clock 9 and two reg ranges;
- QCS615/SM6115/SM6125 expects eight clocks, but clock 8 is ice_core_clk and it expects two reg ranges;
- SM8250 needs its own eight-clock/no-ICE rule.

## 2. Draft patch

Created:
- kernel-baseline/round32/0001-dt-bindings-ufs-add-sm8250-compatible.patch.draft

The draft:
1. adds qcom,sm8250-ufshc to the select compatible list;
2. adds it to the first-compatible enum;
3. adds an SM8250-specific clock-names rule for the exact eight clock names above;
4. specifies a single reg range for the standard UFS Host window.

It intentionally does not add, reorder or constrain the Host power-domains property. The future MMCX + UFS_PHY_GDSC dual-domain work remains a separate change and must pass dt-schema and runtime checks independently.

## 3. QCOM driver matching

The pinned ACK .33 ufs-qcom.c match table has a generic qcom,ufshc entry. The SM8250 DTSI contains that fallback compatible as its second entry, so the Qualcomm UFS driver still matches the SM8250 node even though the first qcom,sm8250-ufshc entry is not a dedicated driver match-table entry.

The proposed UFS dual-GenPD branch can identify the specific SoC via of_device_is_compatible(node, "qcom,sm8250-ufshc") without changing the existing driver match behavior. This is only a source-level conclusion; no driver code has been changed.

## 4. Binding validation boundaries

- The schema-only draft corrects the missing SM8250 compatible selection and its actual clock/register layout.
- Generic power-domains is not given a speculative per-controller name list.
- The UFS Host's first-milestone single power domain remains GCC UFS_PHY_GDSC.
- ROUND29's proposed dual-domain change (MMCX first, GCC GDSC second) remains unapplied and must be checked with the actual schema tool.
- The draft does not claim successful validation; it is a patch candidate only.

## 5. Required next checks

1. Apply the binding patch to a disposable source worktree at the exact ACK .33 tag.
2. Run dt_binding_check for qcom,ufs.yaml and dtbs_check for the SM8250 board DTS.
3. Confirm whether generic power-domains is accepted when the schema selects the SM8250 compatible.
4. Only then prepare the separate dual-GenPD DTS change and check its phandle order and power-domain consumer semantics.
5. Keep the local Agent task unchanged: ROUND12 remains the only active local task.

## 6. Sources

- Pinned ACK qcom,ufs.yaml: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/Documentation/devicetree/bindings/ufs/qcom,ufs.yaml
- Pinned ACK SM8250 UFS node: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/arch/arm64/boot/dts/qcom/sm8250.dtsi
- Pinned ACK UFS QCOM match table: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/ufs/host/ufs-qcom.c
- Current Linux master UFS binding: https://github.com/torvalds/linux/blob/master/Documentation/devicetree/bindings/ufs/qcom%2Cufs.yaml
- Current Linux master SM8250 UFS node: https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/qcom/sm8250.dtsi
