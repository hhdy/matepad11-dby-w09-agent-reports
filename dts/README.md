# DBY-W09 ACK 6.18 DTS draft

This directory contains a **review-only source draft** for the initial DBY-W09 board DTS and its minimal ABL rootparam overlay.

Files:
- `dby-w09-ack18-board.dts.draft` — minimal SM8250 board identity + HOS4.3 PM8150 UFS rails + UFS/QMP enablement.
- `dby-w09-ack18-rootparam.dtso.draft` — separate minimal DBY-W09 board identity overlay, including the stock `huawei,modem_id` sentinel.
- `../config/dby-w09-ack18-storage-first.fragment.draft` — built-in UFS/QMP/RPMh clock/regulator/SM8250 GCC/interconnect/SMMU Kconfig fragment for the first storage milestone.

## Important integration rule

Do **not** apply the stock HOS4.3 DTBO entry 8 to this minimal base. ROUND8 resolved 145 stock fragments targeting many nodes absent from this minimal DTS. Use a separately built and ABL-validated minimal DBY-W09 overlay.

The local ROUND7 DTBO inventory shows that all nine stock entries carry the same generic `huawei,modem_id = <0xffffffff 0>` sentinel. The same-device Linux reference preserves that field in its minimal overlay:
https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso

The draft now preserves that known stock value. This is stronger evidence than omitting it, but it does **not** prove that a newly packed DTBO header / entry table is accepted by the user's current ABL.

## Current limits

- ROUND11 is complete; its sanitized findings are documented in ROUND16. ROUND17 records the ACK GENI UART/console distinction and why both candidate UART nodes remain disabled. No source sync, dtc invocation, dt-schema validation, Kconfig resolution, compile, boot-image packing or hardware test has been done.
- PM8150 UFS output regulators are mapped from local HOS4.3 data. ROUND11 completely scanned the base FDT and found four internal ARC *-parent-supply edges plus six ARC proxy-supply links, but no vdd-s1..s10-supply, vin-supply or vph-pwr-supply anywhere in the FDT. The ARC edges are virtual level dependencies, not physical PM8150 VRM input-supply links. Do not restore the HOS4.2 public-reference vph_pwr=3.7 V wiring.
- SPMI PMIC GPIO/PON/arbiter nodes are intentionally absent from this minimal UFS-only base.
- No UART console, reserved-memory, panel, THP, WLAN, BT, audio, camera, USB-C or DP nodes are enabled. ACK maps uart2 to the GENI debug-console path (ttyMSM / earlycon) and uart6 to the regular GENI UART path (ttyHS); the same-device Linux reference uses uart6 with a Bluetooth child. Do not assume serial0=uart6 makes it ttyMSM0 under ACK 6.18. The HOS androidboot.console=ttyMSM0 property is not by itself a proven ACK console-to-pin mapping.
- Public same-device Linux 7.0 source documents ABL v2 boot plus a separate ramdisk partition and a /rootparam-only DTBO requirement. Local ROUND2 confirms matching image file sizes (boot 96 MiB, ramdisk 2 MiB, dtbo 24 MiB), but HOS4.3 AVB footer / vbmeta descriptor coverage has not yet been inspected. ROUND12 is pending read-only local AVB metadata inspection.
- Panel `ACTIVE_PROFILE=UNKNOWN`.
- The stock HOS4.3 ramdisk remains unread (ROUND10 BLOCKED); module ordering is unknown.
- Logical-partition filesystem / device-mapper options remain commented until the ramdisk fstab and full filesystem inventory are known.
- These files use the suffix `.draft` deliberately. Do not rename them into build input or flash them.

## Source and evidence basis

- Google ACK `android17-6.18` SM8250 DTSI: UFS host, QMP PHY, GCC GDSC, RPMh XO clock and RPMh OPP references, IOMMU and interconnect topology.
- ACK does not use the legacy vendor qcom,rpmh-arc-regulator graph in its upstream PMIC regulator driver. Its SM8250 power-level representation uses the SoC rpmhpd provider and OPP table. The upstream SM8250 RPMhPD domain descriptor does not mirror every HOS4.3 MMCX ARC edge, so full corner equivalence remains a later subsystem validation item.
- Local ROUND7/ROUND9 HOS4.3 facts: stock DTBO rootparam values and UFS rail closure.
- Local ROUND8 overlay target map: stock entry 8 has 145 fragments and is incompatible with a minimal ACK base.
- Public same-device Linux DTS / rootparam overlay, used as a cross-reference only, not copied as a complete Android/ACK solution.
