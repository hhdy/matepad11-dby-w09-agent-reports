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

- ROUND11 is complete; its sanitized findings are documented in ROUND16/21/22. ROUND22 records the ARC-provider API adaptation and the separate, not-yet-confirmed boot proxy-consumer layer. ROUND21 records the remaining ACK PM8150 VRM parent-supply gap and the regulator-core dummy fallback semantics. ROUND17 records the ACK GENI UART/console distinction and why both candidate UART nodes remain disabled. ROUND19 records the HOS4.3 memory/reserved-memory audit and the still-unresolved ABL memory injection boundary. ROUND20 documents Android first-stage module loading and dynamic/EROFS mount requirements. No source sync, dtc invocation, dt-schema validation, Kconfig resolution, compile, boot-image packing or hardware test has been done.
- PM8150 UFS output consumers are mapped from local HOS4.3 data. ROUND11 completely scanned the apps_rsc supply-property scope and found four internal ARC *-parent-supply edges plus six ARC proxy-supply links; it found no upstream VRM input properties for the expected S4/LDO parent supply names, and the whole FDT had no vdd-s1..s10 / vin / vph-pwr properties. ACK's PM8150 VRM driver assigns internal supply_name values to S4/L5/L6/L9/L17. On populated DT, regulator core can use a dummy parent if no matching real supply is found; that assumes the physical rail already exists and is enabled, it does not prove the electrical path. Do not restore HOS4.2 public-reference vph_pwr=3.7 V or invent a parent.
- SPMI PMIC GPIO/PON/arbiter nodes are intentionally absent from this minimal UFS-only base.
- ARC/proxy are not enabled in this UFS-first DTS: ACK's upstream RPMh regulator has VRM/XOB only; the older vendor ARC driver is a porting reference, not code that can be copied without adapting Command DB/RPMh APIs. ACK has no REGULATOR_PROXY_CONSUMER support; the six HOS proxy-supply links are known but their qcom,proxy-consumer request flags are not yet inspected.
- No UART console, reserved-memory, panel, THP, WLAN, BT, audio, camera, USB-C or DP nodes are enabled. ACK maps uart2 to the GENI debug-console path (ttyMSM / earlycon) and uart6 to the regular GENI UART path (ttyHS); the same-device Linux reference uses uart6 with a Bluetooth child. Do not assume serial0=uart6 makes it ttyMSM0 under ACK 6.18. The HOS androidboot.console=ttyMSM0 property is not by itself a proven ACK console-to-pin mapping.
- ROUND7 HOS4.3 base-FDT inventory has no /memory or device_type node, but it has 34 reserved-memory children across boot/security handoff, firmware carveouts, reusable pools and crash/log areas. The public HOS4.2-based Linux DTS has no explicit /memory node either and only four reserved-memory children. ABL may inject usable RAM metadata, but this is not established for the ACK replacement DTB. Do not copy HOS4.2 splash/DFPS addresses or omit all HOS4.3 carveouts on the assumption that ABL will preserve them. See ROUND19; memory/reserved-memory handoff remains a pre-build gate.
- Public same-device Linux 7.0 source documents ABL v2 boot plus a separate ramdisk partition and a /rootparam-only DTBO requirement. Local ROUND2 confirms matching image file sizes (boot 96 MiB, ramdisk 2 MiB, dtbo 24 MiB), but HOS4.3 AVB footer / vbmeta descriptor coverage has not yet been inspected. ROUND12 is pending read-only local AVB metadata inspection.
- Panel `ACTIVE_PROFILE=UNKNOWN`.
- The stock HOS4.3 ramdisk remains unread (ROUND10 BLOCKED); whether its ABL-combined initramfs exposes Android's /lib/modules/<release>/modules.load and depmod files is unknown. Android first-stage can load UFS modules before mounting logical partitions, but this legacy boot/ramdisk combination has not been proven compatible; the storage-first config conservatively keeps UFS built-in.
- ROUND20 adds CONFIG_BLK_DEV_DM=y because Android first-stage maps dynamic logical partitions with dm-linear (built into dm-mod; no CONFIG_DM_LINEAR symbol exists), and CONFIG_EROFS_FS=y because vendor/odm EROFS signatures are locally confirmed. DM_VERITY / FEC stay pending ROUND12 AVB descriptors and ramdisk fstab; EXT4/F2FS stay pending exact filesystem identification.
- These files use the suffix `.draft` deliberately. Do not rename them into build input or flash them.

## Source and evidence basis

- Google ACK `android17-6.18` SM8250 DTSI: UFS host, QMP PHY, GCC GDSC, RPMh XO clock and RPMh OPP references, IOMMU and interconnect topology.
- ACK does not use the legacy vendor qcom,rpmh-arc-regulator graph in its upstream PMIC regulator driver. Its SM8250 power-level representation uses the SoC rpmhpd provider and OPP table. The upstream SM8250 RPMhPD domain descriptor does not mirror every HOS4.3 MMCX ARC edge, so full corner equivalence remains a later subsystem validation item.
- Local ROUND7/ROUND9 HOS4.3 facts: stock DTBO rootparam values and UFS rail closure.
- Local ROUND8 overlay target map: stock entry 8 has 145 fragments and is incompatible with a minimal ACK base.
- Public same-device Linux DTS / rootparam overlay, used as a cross-reference only, not copied as a complete Android/ACK solution.
