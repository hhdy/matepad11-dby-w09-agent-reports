# ROUND140 Supplement — Required checks after ROUND139 delivery

This supplement is part of the ROUND140 task instructions for **2号 Agent**. It does not replace the original taskbook and does not change its prohibitions.

Read these before Stage C:
- ROUND139 report (WorkBuddy Agent): https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md
- AI1 independent review: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round139/AI1_ROUND139_INDEPENDENT_REVIEW_AND_ROUND140_SUPPLEMENT.md

## Accepted ROUND139 results

- UFS consumer/provider links are DIRECT in the inspected HOS4.3 KONA v2.1 FDT/DTBO set:
  vdda-phy → L5; vdda-pll → L9; vdd-hba → ufs_phy_gdsc; vcc → L17; vccq and qcom,vddp-ref-clk → L6; vccq2 → S4; qcom,vccq-parent → S8.
- All six physical electrical input parents remain UNKNOWN. ARC, GDSC, proxy-supply and qcom,vccq-parent-supply are not evidence of vin/input wiring.
- HOS4.3 UFS host/PHY static nodes have no power-domains, operating-points-v2 or required-opps; standard interconnects are absent (legacy qcom,msm-bus remains).
- Pinned ACK SM8250 has UFS_PHY_GDSC, OPP/required-opps and ICC declarations; ACK MMCX descriptor has no parent pointer. Static declaration does not prove runtime votes.
- Boot DTB section is three FDTs plus 173-byte MP_DATA tail. Prior candidate FDT is FDT #0 / KONA v2.1 only; FDT #1 and #2 have not been fully audited.
- Embedded boot ramdisk and standalone ramdisk.img are different objects; ABL use/merge behavior is UNKNOWN.
- DTBO entry 2 is only a conditional VD candidate because the device's actual DTBO partition has no readback hash.
- vbmeta_cust has a structurally parseable offset-0 vbmeta blob declaring SHA256_RSA2048 and a cust hashtree descriptor; its footer points out of range. Do not claim cryptographic signature verification. Footer provenance stays UNKNOWN.
- The report says “all seven header blocks” but its table lists six standalone vbmeta images. Reconcile by listing the exact files/count.
- The 11 available images are stock package images, not device partition backups. HOS4.3 recovery route is BLOCKED.

## Additional candidate-tree checks required in ROUND140

On the exact independently reproduced 23-patch tree and actual R3 output DTB, inspect and report:
1. UFS host and PHY supply properties actually present in candidate DTS and built DTB.
2. Whether each consumer property is consumed by pinned ACK source:
   - PHY side: \`vdda-phy-supply\`, \`vdda-pll-supply\`;
   - host side: \`vdd-hba-supply\`, \`vcc-supply\`, \`vccq-supply\`, \`vccq2-supply\`;
   - downstream-only extras: \`qcom,vddp-ref-clk-supply\`, \`qcom,vccq-parent-supply\` (do not assume ACK consumes these).
3. Each supply phandle's exact resolved provider node and whether provider exists/enabled in the candidate DTB.
4. UFS host/PHY \`power-domains\`, OPP / required-OPP and ICC properties, with every phandle resolved; compare with pinned ACK SM8250 baseline.
5. Do not infer actual regulator enable, physical input parent, runtime RPMh vote, frequency transition or UFS link startup from a static DTB.
6. Keep the all-six-rails physical-parent status UNKNOWN unless authoritative DBY-W09 HOS4.3 board DTS / schematic data is present in the authorized corpus.

No source changes, DTS/DTBO edits, build recipe changes, image packaging or device access are authorized by this supplement.
