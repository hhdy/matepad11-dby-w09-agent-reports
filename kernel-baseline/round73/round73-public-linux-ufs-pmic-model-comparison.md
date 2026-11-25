# ROUND73 — public same-device Linux DTS UFS / PMIC comparison

Date: 2026-11-25
Owner: Primary AI, read-only public source comparison
Scope: public same-device svesnav/linux-dby-w09 DTS versus current ACK 6.18.33 and HOS4.3 evidence. No local DTS change, no build, no device.

## 1. Result

The public same-device Linux 7.0 board DTS is a useful structural reference, but it is not a drop-in DTS for the pinned ACK 6.18.33 Image.

Its UFS Host override configures:
- vcc-supply = PM8150 L17;
- vccq-supply = PM8150 L6;
- vccq2-supply = PM8150 S4;
- PHY vdda-phy L5 and vdda-pll L9;
- status = okay.

The public UFS override does not show:
- qcom,vddp-ref-clk-supply;
- qcom,vccq-parent-supply;
- vdda-phy-always-on;
- an explicit two-domain MMCX + GCC UFS Host power-domain list.

The current ACK 6.18.33 Image includes patches with runtime consumers for VDDP ref-clock and PHY always-on semantics, plus the ROUND33 dual-domain helper that routes the UFS required-opps slot to RPMhPD MMCX. These are ACK-specific additions and should remain in the current candidate even though the earlier public Linux DTS does not show them.

## 2. PM8150 input supply difference

The public DTS creates a fixed regulator named vph_pwr at 3.7 V, marked always-on, and connects PM8150 S1..S10 input supply properties to it.

The HOS4.3 local audits did not find corresponding physical input-supply properties in the inspected base FDT. ROUND66 established that ACK regulator core may use dummy parents when those properties are absent, but the dummy fallback assumes the physical input exists and is already enabled. That software behavior does not verify the electrical parent path.

Do not copy the public 3.7 V vph_pwr or vdd-s* links into the current HOS4.3 board candidate without authoritative board-specific electrical evidence.

## 3. Other structural comparisons

The public source is Linux 7.0 / earlier HOS generation. It contains four reserved-memory entries, including splash_region, DFPS data and crash records; those addresses are not valid evidence for HOS4.3, which has 34 reserved-memory children in its base FDT.

Its root board identity and rootparam-only overlay are useful same-device references, but the exact selected variant and HOS4.3 DTBO table-entry matching policy remain unknown.

## 4. Status

- Public same-device DTS UFS/PMIC source inspected: PASS.
- Generic UFS rails overlap with current HOS4.3 mapping: PASS.
- Public model as a substitute for ACK-specific VDDP / always-on / dual-domain properties: NO.
- Public vph_pwr=3.7 V as HOS4.3 physical input source: UNKNOWN; not adopted.
- HOS4.3 physical PMIC inputs: BLOCKED.
- Public four reserved-memory nodes as HOS4.3 replacement: NOT VALID.
- No local source, DTS, config, build artifact, protected branch or device changed.

Source: https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts
