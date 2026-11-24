# ROUND13 — DBY-W09 ACK 6.18 initial DTS draft and DTBO compatibility decision

Date: 2026-11-24
Status: source-side draft only; superseded/clarified by ROUND15 (rootparam sentinel) and ROUND16 (HOS4.3 ARC parent graph vs ACK RPMhPD mapping). No source sync, dtc, schema validation, compile, image packaging, boot, flash or hardware test.

## 1. Result of this design pass

A minimal DBY-W09 ACK-derived board DTS is now drafted on a dedicated review branch. It enables only the verified SM8250 UFS Host and QMP UFS PHY path plus the PM8150 rails they consume. A separate minimal DBY-W09 rootparam DTBO is drafted to preserve the ABL board-identity contract.

These files are deliberately marked draft and are not declared buildable. Exact ABL semantics / DTBO packaging, memory reservations, and full MMCX/CX/MX voltage-corner equivalence still need review. ROUND15 restores the huawei,modem_id stock sentinel after confirming it is present in all nine local stock DTBO entries; ROUND16 resolves the local PMIC ARC parent links without copying unsupported vendor ARC properties into ACK.

## 2. Critical DTBO finding: do not reuse stock entry 8 against a minimal ACK DTS

ROUND8 established that the original DBY-W09 DTBO entry 8 contains 145 fragments, all resolved against the HOS base FDT through `__fixups__` and `__symbols__`. Its fragment targets include much more than `/rootparam`: PMIC / SPMI, thermal zones, MDSS, display, USB, camera CCI, audio and Huawei-specific services/nodes. ROUND8 target map evidence: `firmware-analysis/round8/dtbo8_fragment_target_map.csv`.

A minimal ACK board DTS built from the upstream SM8250 SoC DTSI will not contain all the vendor-only node paths and labels referenced by those 145 fragments. Therefore:
- Do not apply the original stock DTBO entry 8 to the new minimal ACK DTB.
- Do not assume all original fragments can be silently ignored by ABL.
- The draft uses a fresh minimal DBY-W09 DTBO entry containing only the board identity and one `rootparam` target.
- That approach follows the same-device public Linux reference's published `dby-w09-rootparam.dtso`, which states that ABL requires the rootparam identity overlay while the other stock fragments target vendor-only nodes: https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso
- This is a source reference, not proof that the user's current HOS4.3 ABL accepts a newly built DTBO image. ABL header format, entry selection and rootparam field requirements must be validated before any device use.

## 3. Base-DTS facts used

Local DBY-W09 facts:
- SoC identity: KONA / SM8250 v2.1; local MSM-ID `[356, 131073]`.
- Board id for DBY-W09 entry 8: 8298 decimal = `0x206a`.
- Root identity fields: boardid digits `[8,2,9,8]`, board name `DBY_W09_VG`, product `DBY-W09`, hardware version `SH1DBSLM`.
- The minimal overlay includes huawei,modem_id = <0xffffffff 0x00>: ROUND7's sanitized local DTBO property inventory shows the same sentinel in all nine stock entries. It is a common stock sentinel, not a per-device modem identifier. This preserves the stock rootparam shape; it still does not prove newly packaged DTBO acceptance.

Public same-device DTS:
https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts

The draft uses the board/SoC include pattern from that BSD-3-Clause reference but only carries the minimal SoC and UFS-provider portions needed for first review. It does not copy its Linux 7.0 display, Wi-Fi, audio or touch configuration into ACK. Its HOS4.2-derived vph_pwr 3.7 V and vdd-s*-supply wiring is deliberately excluded until HOS4.3 local evidence confirms the PMIC input topology.

## 4. UFS mapping from ROUND9 local HOS4.3 data

All values below come from ROUND9's fully resolved 8/8 regulator/GDSC phandle chain:

| Consumer | Local HOS target | HOS4.3 constraints | Draft treatment |
|---|---|---|---|
| UFS Host `vcc` | PM8150 L17 | 2.496–3.008 V; max 800 mA; overlay `vcc-voltage-level` 2.504–2.950 V | `vcc-supply`, `vcc-voltage-level`, `vcc-max-microamp` |
| UFS Host `vccq` | PM8150 L6 | 1.2 V; max 800 mA | `vccq-supply`, `vccq-max-microamp` |
| UFS Host `vccq2` | PM8150 S4 | 1.8–1.92 V; max 800 mA | `vccq2-supply`, `vccq2-max-microamp` |
| UFS PHY `vdda-phy` | PM8150 L5 | 0.88 V; max 89.9 mA | `vdda-phy-supply`, `vdda-phy-max-microamp` |
| UFS PHY `vdda-pll` | PM8150 L9 | 1.2 V; max 18.8 mA | `vdda-pll-supply`, `vdda-pll-max-microamp` |
| UFS PHY `vddp-ref-clk` | PM8150 L6 | 1.2 V; max 100 µA | optional PHY supply `vddp-ref-clk-supply` and max load |

Upstream UFS common binding defines `vcc`, `vccq`, `vccq2`, their max-current fields and optional voltage range. The QMP UFS PHY binding defines the core / PLL rails and optional `vddp-ref-clk-supply`:
- https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/Documentation/devicetree/bindings/ufs/ufs-common.yaml
- https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/Documentation/devicetree/bindings/phy/qcom-qmp-phy.txt

Design interpretation:
- `vdd-hba-supply` resolves to UFS_PHY_GDSC in HOS. ACK SM8250 Host already has `power-domains = <&gcc UFS_PHY_GDSC>`; the draft relies on that power-domain and does not model GDSC as a regulator.
- `qcom,vccq-parent-supply` resolves to PM8150A S8 but is a downstream-specific property absent from the generic upstream UFS binding. It is omitted from the initial upstream node.
- HOS `vcc-low-voltage-sup` is not blindly translated to upstream `vcc-supply-1p8`; the HOS VCC operating window is 2.504–2.950 V. This property requires separate exact-driver interpretation.
- The existing ACK SM8250 DTSI already declares Host reset, PHY reset, clocks, lanes, interconnect / power-domain structure. Do not duplicate those SoC-level definitions in the board DTS.

### Provider-aware regulator load voting note

The ACK UFS PHY helper reads each PHY rail's `*-max-microamp` value and may call `regulator_set_load()` for variable-voltage rails. Accordingly, the draft enables DRMS/load voting on the PM8150 LDO rails L5, L6 and L9 using `regulator-allow-set-load` plus LPM/HPM allowed modes. The shared L6 vote covers both Host VCCQ and PHY VDDP ref-clock consumers. The RPMh binding describes `regulator-allow-set-load` for LDO regulators managed via VRM:
https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.txt

PM8150 S4 is mapped by the ACK RPMh regulator driver to `pmic5_hfsmps510`, whose operations differ from the DRMS-enabled LDO path. Therefore the draft does not add the LDO-specific `regulator-allow-set-load` property to S4. Keep the HOS-confirmed `vccq2-max-microamp = <800000>` at the UFS Host; verify its exact power-mode behavior in the pinned ACK driver before claiming load voting works on this SMPS:
https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/regulator/qcom-rpmh-regulator.c

The UFS core also uses `vccq-max-microamp` and `vccq2-max-microamp` when deriving the device Active ICC level. These values therefore remain useful even where the PMIC regulator does not perform DRMS mode switching:
https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/ufs/core/ufshcd.c

## 5. ACK source-level topology

ACK `android17-6.18` SoC DTSI defines:
- `ufs_mem_hc` compatible `qcom,sm8250-ufshc`, `qcom,ufshc`, `jedec,ufs-2.0`;
- `ufs_mem_phy` compatible `qcom,sm8250-qmp-ufs-phy`;
- lane provider `ufs_mem_phy_lanes`;
- Host reset `<&gcc GCC_UFS_PHY_BCR>` and `UFS_PHY_GDSC` power domain;
- QMP PHY reset `<&ufs_mem_hc 0>`;
- SoC clock and register definitions.

Source view:
https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/arch/arm64/boot/dts/qcom/sm8250.dtsi

The first draft enables the existing SoC UFS nodes by label and supplies board-specific VRM regulators. ROUND11's complete base-FDT scan found four parent-supply properties only on legacy ARC level groups and six ARC proxy-supply properties. It found no vdd-s1..s10-supply, vin-supply or vph-pwr-supply in the full base FDT. The ARC links are not physical PM8150 VRM input parents; ACK's upstream RPMh regulator path does not accept the vendor ARC compatible. See ROUND16 for the translation boundary. The board draft intentionally leaves PM8150 physical input links unspecified.

## 6. Files created on review branch

Branch: `ack18-dby-w09-dts-draft`

- `dts/dby-w09-ack18-board.dts.draft`
- `dts/dby-w09-ack18-rootparam.dtso.draft`
- `dts/README.md`

The DTS files are intentionally suffixed `.draft` so they cannot be mistaken for ready-to-build source. Do not compile, package, boot or flash them without further review.

## 7. Explicitly deferred

- Panel: `ACTIVE_PROFILE=UNKNOWN`. ROUND10 cmdline scope had no selector; ramdisk scan remains BLOCKED. No panel profile is enabled.
- THP: not enabled in the minimal boot draft; OF match, 10MHz parent ceiling, GPIO43 CS, GPIO39 IRQ, GPIO98 reset and Huawei userspace ABI remain for a later change.
- WLAN/BT: not enabled; QCA6391 PCI HW revision and firmware/calibration are UNKNOWN.
- Audio, cameras, USB-C/DP: not enabled pending separate verified driver/firmware/endpoint mapping.
- Memory map, reserved-memory / splash, ramoops and crash regions: not carried from Linux 7.0 references into this initial draft without an ACK-specific memory-region audit.
- UART alias / console: deferred pending exact ACK console and bootloader cmdline validation.
- Ramdisk: ROUND10 content remains BLOCKED; no mount/fstab/module sequence assertions are made.
- Vendor/odm EROFS: content remains BLOCKED; no 4.19 modules are assumed ABI compatible with ACK 6.18.

## 8. Verification status

| Check | Status |
|---|---|
| Source text created | YES |
| Reviewed against ROUND9 UFS map | YES |
| Reviewed against ACK SM8250 topology | SOURCE REVIEW ONLY |
| Reviewed original DTBO fragment-target compatibility | YES — original DTBO is incompatible with minimal base strategy |
| Stock huawei,modem_id sentinel reproduced | YES — ROUND7 inventory shows same value in all nine entries |
| ROUND11 HOS4.3 PMIC parent-supply check | COMPLETE — four ARC-level parent links, six ARC proxy links; no vdd-s / vin / vph supply link in base FDT |
| Fresh minimal DTBO ABL acceptance | UNKNOWN / NOT_TESTED |
| dtc compile | NOT_RUN |
| dt-schema validation | NOT_RUN |
| Kleaf / kernel compile | NOT_RUN |
| Image packaging | NOT_RUN |
| Device boot / UFS runtime | NOT_RUN |
| Any flashing / device write | NO |

## 9. Next engineering step

ROUND16 records the completed ROUND11 findings and the correct ACK translation boundary. Continue next with the early-boot console/GENI UART and any remaining source-side dependency audit. No compile or static build validation is claimed.
