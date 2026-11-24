# ROUND16 — HOS4.3 RPMh ARC parent graph and ACK DTS translation

Date: 2026-11-24

Status: ROUND11 local read-only evidence has been reviewed. ACK DTS/Kconfig/README draft comments updated. No DTS compile, schema validation, Kconfig resolution, kernel build, DTB build, image packaging, ABL test or device boot.

## 1. ROUND11 local result: classify the edges correctly

The completed ROUND11 report is:
- Branch: firmware-audit-v1
- File: firmware-analysis/round11/round11_pmic_parent_supply_findings.txt
- Tool: previously reviewed ROUND3 parser, used read-only on the existing HOS4.3 base boot FDT work copy.
- Provider subtree: /soc/rsc@18200000, all 109 property paths checked; a full base-FDT property-name scan was also performed for the requested vdd-s / vin / vph patterns.
- All 11 reported phandles resolved; BLOCKED=none, UNKNOWN=none.

### 1.1 Four explicit ARC parent-supply links

| Consumer ARC group | Property | Resolved target |
|---|---|---|
| cxlvl | pm8150_s3_level-parent-supply | mxlvl / regulator-pm8150a-s3-level |
| cxlvl | pm8150_s3_level_ao-parent-supply | mxlvl / regulator-pm8150a-s3-level-ao |
| mmcxlvl | pm8150a_s4_level-parent-supply | mxlvl / regulator-pm8150a-s3-mmcx-sup-level |
| mmcxlvl | pm8150a_s4_level_ao-parent-supply | mxlvl / regulator-pm8150a-s3-level-ao |

These properties are inside legacy qcom,rpmh-arc-regulator groups. Their targets are RPMh ARC voltage-level regulator nodes, not fixed regulators and not PM8150 VRM output/input supply rails.

### 1.2 Six proxy-supply links

ROUND11 also found six proxy-supply properties. Their phandles resolve to children inside their own ARC provider groups. They represent the RPMh proxy mechanism and must not be treated as physical input-supply links.

The six proxy targets include ARC level nodes and same-group L5/L9/L14/L11 proxy children. Generic regulator-min-microvolt values on some proxy targets (0.88 V, 1.20 V, 1.80 V, 3.104 V) are not evidence of the ARC interconnect's physical input voltage.

### 1.3 Verified global absence of external supply properties

The local parser successfully read the complete base FDT and scanned property names:
- vdd-s1-supply through vdd-s10-supply: 0 hits anywhere in base FDT.
- vin-supply: 0 hits anywhere.
- vph-pwr-supply: 0 hits anywhere.

This is a verified absence in the inspected base-FDT property-name scope, not an inference from the earlier ROUND7 CSV. It does not prove there is no electrical PMIC input stage or runtime parent; that was explicitly NOT_RUN and remains outside the FDT property evidence.

Therefore the public same-device Linux 7.0 fixed 3.7 V vph_pwr plus vdd-s1..s10-supply wiring (whose source states HOS4.2 as its reference) must not be restored to the ACK HOS4.3 board DTS on the current evidence.

## 2. ACK translation decision: do not copy the vendor ARC nodes

### 2.1 Upstream ACK regulator driver model

The upstream qcom-rpmh-regulator implementation describes two accelerator classes:
- VRM: PMIC LDO, SMPS and BOB enable/voltage/mode requests.
- XOB: PMIC peripheral enable requests.

Its match table binds PMIC-level compatible groups such as qcom,pm8150-rpmh-regulators. It does not bind qcom,rpmh-arc-regulator. The upstream qcom,rpmh-regulator.yaml schema describes PMIC VRM/XOB group compatibles and optional PMIC physical input supply properties such as PM8150 vdd-l* / vdd-s* groups; it does not define the legacy qcom,rpmh-arc-regulator provider.

References:
- Driver model / supported accelerator classes: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/regulator/qcom-rpmh-regulator.c
- Binding: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml

### 2.2 Upstream SM8250 performance-level representation

The ACK SM8250 SoC DTSI already defines, under apps_rsc:
- rpmhcc for RPMh XO clocks;
- rpmhpd with a common OPP table of retention/SVS/NOM/TURBO performance levels;
- apps_bcm_voter.

The UFS Host SoC node references the GCC UFS_PHY_GDSC generic power domain, the RPMh XO clock, and UFS bus interconnect paths. The UFS OPP table references rpmhpd_opp_low_svs and rpmhpd_opp_nom through required-opps. This is the upstream ACK path that the storage-first configuration preserves.

References:
- ACK SM8250 SoC DTSI: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/arch/arm64/boot/dts/qcom/sm8250.dtsi
- RPMhPD driver: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/pmdomain/qcom/rpmhpd.c
- RPMhPD Kconfig: https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/soc/qcom/Kconfig

### 2.3 Important non-equivalence: preserve as a porting risk

The local HOS4.3 mx/cx/mmcx ARC relationship is not automatically identical to the upstream SM8250 RPMhPD descriptor. The public upstream SM8250 RPMhPD mapping uses cx_w_mx_parent for CX/CX_AO, but maps MMCX to the plain mmcx / mmcx_ao descriptor (without an explicit parent pointer in that SM8250 table). Other later SoCs use a different MMCX-with-CX-parent descriptor.

Therefore:
- Keep the UFS OPP required-opps configuration and the SoC's upstream rpmhpd model.
- Do not claim every vendor ARC parent edge has been reproduced one-for-one.
- Do not add legacy qcom,rpmh-arc-regulator nodes to this upstream ACK DTS.
- Keep full MMCX/CX/MX corner behavior as a later per-subsystem voltage/OPP compatibility audit before enabling more hardware (display, GPU, multimedia, etc.).

This distinction is important: the UFS storage-first draft is an upstream-oriented design direction, not proof that the complete HOS4.3 ARC graph is already equivalent at runtime.

## 3. Updated ACK board DTS PMIC segment

The board DTS draft now:
- keeps the five locally mapped PM8150 VRM outputs consumed by UFS (S4, L5, L6, L9, L17);
- does not add fixed vph_pwr=3.7 V;
- does not add vdd-s1..s10-supply, vin-supply, or any invented input rail;
- does not copy the four vendor *-parent-supply edges into the PM8150 VRM group;
- does not convert any of the six proxy-supply references into consumer or regulator input links;
- records the HOS4.3 ARC graph and the ACK translation limitation in source comments / README.

The current PM8150 input supply is intentionally unspecified because the local base FDT does not expose an external input relationship. This is a fail-closed source draft, not a verified electrical schematic.

## 3.5 Additional ACK VRM parent-supply gap identified in ROUND21

The ACK PM8150 VRM driver table has a non-NULL supply_name for the exact UFS rails: S4 uses vdd-s4; L5 uses vdd-l3-l4-l5-l18; L6/L9 use vdd-l6-l9; L17 uses vdd-l13-l16-l17. ROUND11's full apps_rsc scan found no corresponding VRM supply phandles; the four parent-supply properties it did find are legacy ARC level-provider edges, not these PMIC VRM input links.

The regulator core can use a dummy parent when Device Tree is populated and a named supply cannot be resolved. That means missing parent phandles do not necessarily force a regulator probe failure; the dummy regulator assumes the physical supply is present and already enabled. This is not evidence of the actual electrical parent or proof that the PMIC rails are safe under ACK runtime voltage/mode transitions. The UFS consumer-to-output mapping remains locally resolved, but the PM8150 output-rail input power-tree remains NOT_ESTABLISHED. See ROUND21.

## 4. Changed files

Branch ack18-dby-w09-dts-draft:
- dts/dby-w09-ack18-board.dts.draft — added ROUND11 topology comments and the ARC-to-ACK mapping boundary; no unsupported vendor ARC nodes added.
- config/dby-w09-ack18-storage-first.fragment.draft — comments document the vendor ARC vs upstream RPMhPD distinction; QCOM_RPMHPD remains enabled for UFS OPP required-opps.
- dts/README.md — records completed ROUND11 evidence and remaining MMCX equivalence risk.

Main branch:
- ROUND13 and ROUND14 reports cross-reference this correction.
- ROUND15 status and parent-supply section updated from pending Agent check to completed ROUND11 evidence.
- AGENT_TASK.md records ROUND11 complete and no current Agent task.

## 5. Verification status

| Item | Status |
|---|---|
| ROUND11 local base-FDT parser read | COMPLETE |
| Four ARC parent-supply edges and all phandles | COMPLETE / RESOLVED |
| Six proxy-supply edges and all phandles | COMPLETE / RESOLVED |
| Global vdd-s / vin / vph-pwr property scan | COMPLETE / ZERO HITS |
| ACK VRM/XOB vs legacy ARC driver distinction | SOURCE REVIEWED |
| SM8250 RPMhPD domain mapping and OPP model | SOURCE REVIEWED |
| One-to-one equivalence of all HOS4.3 MMCX/CX/MX ARC edges in ACK | NOT_ESTABLISHED |
| ACK board DTS dtc compile / schema validation | NOT_RUN |
| Kconfig olddefconfig resolution | NOT_RUN |
| Kernel/DTB build / packaging | NOT_RUN |
| ABL acceptance / device boot / runtime voltage behavior | NOT_RUN |
| Device operation / flash / unlock / write | NO |

## 6. Next engineering step

ROUND17 subsequently reviews the ACK GENI UART/console path and keeps UART nodes deferred because ttyMSM debug-console and ttyHS regular-UART roles differ. ROUND18 reviews the same-device legacy boot packaging flow and assigns ROUND12 to check the HOS4.3 AVB footer / vbmeta descriptor scope. Continue GPT-side review of the remaining storage-first DTS/Kconfig and boot packaging plan. Keep the MMCX/CX/MX one-to-one voltage-corner mapping as an explicit open issue until a later consumer-specific OPP audit or permitted runtime validation can close it.

Keep every file suffixed .draft. Keep PR #1 Draft. No device connection, flash, write, root, compile or image packaging.
