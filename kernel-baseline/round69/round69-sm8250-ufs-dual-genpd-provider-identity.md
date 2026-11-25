# ROUND69 — exact SM8250 UFS dual-GenPD provider labels and binding constants

**Date:** 2026-11-25  
**Baseline:** ACK android17-6.18.33_r00 / common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Scope:** source-only identity cross-check for the main board rev2 candidate. No DTS or source edit, no build.

## 1. Result

The two binding headers included by the new board DTS rev2 candidate exist at the exact pinned ACK commit and define the required constants:

- include/dt-bindings/power/qcom,rpmhpd.h:16 — RPMHPD_MMCX = 6.
- include/dt-bindings/clock/qcom,gcc-sm8250.h:263 — UFS_PHY_GDSC = 4.

The exact pinned SoC DTSI also contains all three labels needed by the proposed power-domain list:

- arch/arm64/boot/dts/qcom/sm8250.dtsi:953 — gcc provider label, compatible qcom,gcc-sm8250.
- arch/arm64/boot/dts/qcom/sm8250.dtsi:2507 — ufs_mem_hc host node.
- arch/arm64/boot/dts/qcom/sm8250.dtsi:2579 — ufs_mem_phy node.
- arch/arm64/boot/dts/qcom/sm8250.dtsi:6193 — rpmhpd provider label, compatible qcom,sm8250-rpmhpd.

The SoC DTSI's current Host power-domains property is one cell: GCC UFS_PHY_GDSC at line 2519. Its UFS OPP table at lines 2550–2575 has exactly two available entries, each with a required-opps pointer to RPMhPD (low-svs and nominal). The PHY at line 2593 independently retains the GCC UFS_PHY_GDSC power-domain.

This source-level cross-check confirms the exact labels and numeric IDs used by the ROUND37 board delta and current main branch board rev2 candidate. It does not replace dtc/schema/driver build validation.

## 2. Relevant exact-source excerpts

### Binding constants

File: include/dt-bindings/power/qcom,rpmhpd.h

    #define RPMHPD_MMCX       6
    #define RPMHPD_MMCX_AO    7

File: include/dt-bindings/clock/qcom,gcc-sm8250.h

    #define UFS_PHY_GDSC      4

### SoC provider / consumer labels

File: arch/arm64/boot/dts/qcom/sm8250.dtsi

- 953: gcc: clock-controller@100000, compatible qcom,gcc-sm8250.
- 2507: ufs_mem_hc: ufshc@1d84000.
- 2508–2509: Host compatible qcom,sm8250-ufshc, qcom,ufshc, jedec,ufs-2.0.
- 2519: power-domains = <&gcc UFS_PHY_GDSC>.
- 2542: operating-points-v2 = <&ufs_opp_table>.
- 2550–2575: two UFS OPP entries, each with one required-opps property referring to rpmhpd_opp_low_svs / rpmhpd_opp_nom.
- 2579: ufs_mem_phy: phy@1d87000.
- 2580: PHY compatible qcom,sm8250-qmp-ufs-phy.
- 2593: PHY power-domains = <&gcc UFS_PHY_GDSC>.
- 6193–6196: rpmhpd: power-controller, compatible qcom,sm8250-rpmhpd, #power-domain-cells=1, and its OPP table.

## 3. rev2 candidate consistency

The current main branch candidate:

    dts/dby-w09-ack18-board.dts.rev2.candidate

adds:
- include <dt-bindings/clock/qcom,gcc-sm8250.h>;
- include <dt-bindings/power/qcom,rpmhpd.h>;
- Host power-domains ordered as:
  RPMhPD MMCX index 0;
  GCC UFS_PHY_GDSC index 1.

The labels/macros exist with the exact intended compatible providers and numeric cell values. The PHY property remains inherited from the SoC DTSI and is not changed by this board delta.

This makes the DTS property internally consistent with the ROUND33 driver helper's documented two-domain contract and its required-opps slot 0 mapping. It still does not prove the actual RPMhPD parent/corner behavior is equivalent to HOS4.3 vendor ARC logic; ROUND30/50 remain open. It also does not prove UFS link startup or runtime PM behavior.

## 4. Status

- Exact header path and ID constants: PASS.
- Exact SoC DTSI provider labels and compatibles: PASS.
- Exact UFS Host / PHY node locations and inherited power domains: PASS.
- UFS OPP required-opps entries: PASS.
- Candidate rev2 dtc compile: NOT RUN.
- dt_binding_check / dtbs_check: NOT RUN.
- Kleaf device-tree graph execution: NOT RUN.
- MMCX-to-MX ARC semantics: UNKNOWN.
- Device boot / UFS runtime: NOT RUN.

No source, candidate DTS, Kconfig, build artifact, protected branch or device was modified.
