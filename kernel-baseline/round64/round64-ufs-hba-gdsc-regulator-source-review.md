# ROUND64 — ACK UFS vdd-hba supply versus SM8250 UFS_PHY_GDSC source contract

**Date:** 2026-11-25  
**Owner:** Primary AI source review  
**Baseline:** ACK android17-6.18.33_r00, common commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Scope:** pinned public ACK source and existing HOS4.3 ROUND21 property inventory; no source or DTS changes, no build, no device.

## 1. Executive result

The HOS4.3 UFS Host overlay contains both:
- `vdd-hba-supply = <&ufs_phy_gdsc>`;
- `vdd-hba-fixed-regulator`.

ROUND21 resolves `ufs_phy_gdsc` to the HOS4.3 node `/soc/qcom,gdsc@177004`, compatible `qcom,gdsc`.

The pinned ACK UFS core has a real optional `vdd-hba-supply` consumer. When the property is present, it allocates a `ufs_vreg`, later obtains a regulator handle and calls regulator enable/disable during host initialization and teardown. When absent, it logs that the supply is not found and assumes it is already enabled.

However, the pinned ACK Qualcomm GDSC driver is a **generic power-domain provider**, not a regulator-output provider. Its registration path calls `of_genpd_add_provider_onecell()`; it does not register a regulator for each GDSC node. In the pinned regulator OF lookup path, when a phandle names an existing DT node but no regulator device has registered for that node, lookup returns `-EPROBE_DEFER`. This is distinct from an entirely missing supply property, which the UFS platform parser deliberately treats as always-on.

Therefore, blindly copying the HOS `vdd-hba-supply` property into the ACK board DTS is unsafe and may prevent UFS probe from completing. The existing board draft's choice to omit this property and rely on the inherited SM8250 `power-domains = <&gcc UFS_PHY_GDSC>` is source-consistent for the pinned ACK port. Do not add the HOS-only `vdd-hba-fixed-regulator` flag either: the reviewed pinned ACK UFS platform/core code does not consume it.

This conclusion is limited to the pinned upstream ACK implementation. It does not claim the HOS vendor kernel treats the HOS GDSC node the same way.

## 2. HOS4.3 input facts

ROUND21 report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round21/round21_first_stage_devtmpfs_and_ufs_pinctrl_overlay_audit.txt

The report states that every one of the nine stock DTBO entries has the same UFS host fragment, including `vdd-hba-supply` targeting external label `ufs_phy_gdsc`. The external fixup resolves to `/soc/qcom,gdsc@177004`, compatible `qcom,gdsc`.

The same HOS UFS host/PHY configuration has separate power/clock/reset details. This does not establish that the HOS and ACK drivers expose identical frameworks for the GDSC node.

## 3. Pinned ACK UFS consumer behavior

### 3.1 Parsing the HBA supply

File:
`drivers/ufs/host/ufshcd-pltfrm.c`

At lines 121–156, `ufshcd_populate_vreg()`:
- builds the property name `<name>-supply`;
- if the phandle is absent, logs “assuming enabled” and returns a NULL `ufs_vreg`;
- if the property exists, allocates the regulator descriptor and records its name;
- for `skip_current=true`, skips max-current parsing and sets the load to zero.

At lines 181–188, `ufshcd_parse_regulator_info()` invokes:
`ufshcd_populate_vreg(dev, "vdd-hba", &info->vdd_hba, true)`.

Source:
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufshcd-pltfrm.c#L121-L188

### 3.2 Acquiring and toggling the supply

File:
`drivers/ufs/core/ufshcd.c`

- `ufshcd_get_vreg()` obtains a normal regulator handle with `devm_regulator_get(dev, vreg->name)` (lines 9565–9582).
- `ufshcd_enable_vreg()` calls the regulator configuration helper then `regulator_enable()` (lines 9499–9518).
- `ufshcd_disable_vreg()` calls `regulator_disable()` (lines 9519–9544).
- `ufshcd_setup_hba_vreg()` toggles the optional `vdd_hba` object (lines 9567–9572).
- `ufshcd_init()` enables HBA supply before host clocks and generic UFS vcc/vccq/vccq2 initialization; the unwind path disables it (lines 9792–9834).
- `ufshcd_hba_exit()` shuts down variant and generic UFS rails, then toggles HBA supply off (lines 9845–9852).

Source:
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c#L9499-L9852

The property is therefore functional in ACK. It is not an inert marker.

## 4. Pinned ACK GDSC provider behavior

File:
`drivers/clk/qcom/gdsc.c`

- The driver models a GDSC as `struct generic_pm_domain`; power-on/off callbacks are `gdsc_enable()` and `gdsc_disable()` (lines 259 onward and 317 onward).
- The descriptor registration path initializes each domain and exposes it through `of_genpd_add_provider_onecell()` (lines 570–628).
- The file does not call `devm_regulator_register()` and does not register a regulator device for the GDSC node. The `rsupply` handles in this driver are upstream/input supplies used by the GDSC itself, not output regulator consumers.

Source:
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/clk/qcom/gdsc.c#L259-L317
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/clk/qcom/gdsc.c#L570-L628

The SM8250 base DTSI already attaches both UFS Host and UFS PHY to `&gcc UFS_PHY_GDSC` through their `power-domains` properties.

Source:
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/boot/dts/qcom/sm8250.dtsi

## 5. Why a GDSC phandle in vdd-hba-supply is not a valid ACK regulator reference

File:
`drivers/regulator/of_regulator.c`, lines 647–665:
- `of_regulator_dev_lookup()` parses the consumer's `*-supply` phandle;
- if that node exists but `of_find_regulator_by_node()` finds no registered regulator device, it returns `-EPROBE_DEFER`.

File:
`drivers/regulator/core.c`, lines 2210–2245:
- a missing regulator may be replaced by the dummy regulator only when the lookup result is `-ENODEV` and full constraints are active;
- non-`-ENODEV` errors, including `-EPROBE_DEFER`, are returned directly.

Sources:
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/of_regulator.c#L647-L665
https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L2210-L2245

Thus the regulator core's dummy-supply fallback does not rescue a phandle that points to an existing GenPD-only node without a regulator device.

## 6. Board-DTS recommendation

Keep the current review draft's approach:
- do not add `vdd-hba-supply = <&ufs_phy_gdsc>`;
- do not add `vdd-hba-fixed-regulator`;
- retain the SoC DTSI's UFS Host and UFS PHY GCC `UFS_PHY_GDSC` power-domain properties;
- if a separate real regulator provider or regulator alias is ever introduced, review it as a distinct design and verify it with pinned regulator lookup/driver semantics before use.

This note does not make the board DTS build-ready. ROUND22 still needs to verify the exact board source, UFS supplies, source patch set, PMIC input parents and /memory comment, and the runtime memory/AVB/ABL gates remain open.

## 7. Evidence status

- Pinned ACK source review: PASS.
- HOS-side origin of the GDSC fixup: PASS via ROUND21.
- Full-tree apply / dtc / dt-schema / Kconfig / build of a board DTB: NOT RUN in this note.
- Runtime PM-domain / regulator operation: NOT RUN.
- Device boot: NOT RUN.
