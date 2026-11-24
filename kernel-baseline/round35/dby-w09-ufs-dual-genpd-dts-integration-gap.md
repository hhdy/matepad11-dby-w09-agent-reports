# ROUND35 — DBY-W09 UFS dual-GenPD DTS integration gap

Date: 2026-11-24

Status: **INTEGRATION GAP CONFIRMED — current board DTS draft does not activate ROUND33.** This report records a required follow-up; it does not modify the protected `ack18-dby-w09-dts-draft` branch.

## 1. Source and artifacts checked

- Fixed ACK baseline: `android17-6.18.33_r00`
- Tag target commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Current DBY-W09 board DTS draft on branch `ack18-dby-w09-dts-draft`:
  - `dts/dby-w09-ack18-board.dts.draft`
  - blob SHA at review: `e86c8707c413a9376b1e332a94e292b86acde3e2`
- Existing exact-tag UFS topology summarized in ROUND29:
  - `kernel-baseline/round29/ack-qcom-ufs-dual-genpd-required-opp-integration.md`
- ROUND33 driver patch/design:
  - `kernel-baseline/round33/0001-scsi-ufs-qcom-sm8250-dual-genpd-required-opp.patch.draft`
  - `kernel-baseline/round33/sm8250-ufs-dual-genpd-patch-design.md`
- ROUND34 fixed-source lifecycle review:
  - `kernel-baseline/round34/round33-pinned-source-lifecycle-review.md`

## 2. Existing SoC UFS Host topology

The ACK SM8250 SoC DTSI UFS Host node is `ufs_mem_hc` / compatible `qcom,sm8250-ufshc` with fallback `qcom,ufshc`. Its inherited default is a single power-domain entry:

```dts
power-domains = <&gcc UFS_PHY_GDSC>;
```

The same node references `ufs_opp_table`; its 37.5 MHz and 300 MHz OPP entries each contain exactly one RPMHPD `required-opps` reference (`rpmhpd_opp_low_svs` and `rpmhpd_opp_nom`). The UFS PHY node separately remains attached to GCC `UFS_PHY_GDSC`.

ROUND29 records these facts against the pinned ACK `.33_r00` source. A public source rendering of the SM8250 DTSI exposes the same UFS Host default at lines 2500–2569 and UFS PHY domain at lines 2572–2587:
https://android.googlesource.com/kernel/common/+/7f90573099e8a506a6874d691d884d7f5b77ec74/arch/arm64/boot/dts/qcom/sm8250.dtsi

## 3. Current DBY-W09 board overlay does not change power-domains

The current `dts/dby-w09-ack18-board.dts.draft` overrides `&ufs_mem_hc` to add HOS4.3-derived UFS rails and set `status = "okay"`. It does **not** declare `power-domains`, so the UFS Host continues to inherit the SoC's single GCC `UFS_PHY_GDSC` entry.

This means the current DTS draft does not meet ROUND33's driver guard. With the existing one-domain property:
- ROUND33 helper sees `num_domains == 1` and deliberately returns 0;
- generic single-domain GenPD attachment remains responsible for the GCC GDSC;
- the explicit RPMHPD MMCX attach does not occur;
- the UFS OPP `required-opps` is therefore still not mapped to a virtual MMCX GenPD device by ROUND33.

**Conclusion:** ROUND33 can be source-correct as a conditional driver candidate while still being inactive in the current board DTS. Do not describe the UFS-to-MMCX vote path as integrated or fixed yet.

## 4. Required DTS delta for the next integration draft

The intended DBY-W09 UFS Host topology, matching ROUND33's hard validation, is:

```dts
&ufs_mem_hc {
    power-domains = <&rpmhpd RPMHPD_MMCX>,
                    <&gcc UFS_PHY_GDSC>;

    /* existing board rails and status remain here */
};
```

Index contract:
1. index 0 — RPMHPD provider, domain ID `RPMHPD_MMCX`; the explicit UFS OPP `required_dev_index = 0` targets this attached virtual GenPD device.
2. index 1 — GCC provider, domain ID `UFS_PHY_GDSC`; retain the physical UFS PHY/GDSC dependency rather than replacing it.

Do not change `ufs_mem_phy`'s existing GCC `UFS_PHY_GDSC` domain. Do not add an MMCX→MX parent to the provider descriptor. ROUND30 remains a separate unresolved power-corner-equivalence gate.

This snippet is a design delta only. It has not been applied to the protected DTS branch, and its phandle labels / final combined-DTS resolution must be checked in the complete fixed-tag source tree before use.

## 5. Required follow-up validation

Before integrating this topology:
- Confirm the fixed ACK `.33_r00` labels and domain IDs resolve in the final combined DTS: `rpmhpd`, `RPMHPD_MMCX`, `gcc`, and `UFS_PHY_GDSC`.
- Confirm no included board DTS, overlay, or later fragment replaces/reorders `power-domains`.
- Review the UFS binding schema after ROUND32, specifically whether the two-entry property is accepted by the full schema path; ROUND32 intentionally did not change power-domain constraints.
- Apply the driver and schema changes in a full worktree at the fixed tag; run `dt_binding_check`, `dtbs_check`, `git apply --check`, `checkpatch.pl`, Kconfig resolution, and compile.
- Inspect final DTB/DTBO output, not only source fragments, to confirm exactly two Host domains in the required order.
- Only then perform controlled hardware testing and confirm an actual MMCX performance-state vote, UFS link startup, storage enumeration, and suspend/resume.

## 6. Branch safety and status

- No files on `ack18-dby-w09-dts-draft` were modified.
- No changes to PR #1 were made; keep it Draft.
- No local device operation or firmware operation was performed.
- No `dtc`, `dt_binding_check`, `dtbs_check`, build, or runtime test was run.
- ROUND12 remains the only local Agent task for read-only AVB metadata inspection.

**Conclusion:** the next necessary code-integration item is not another rewrite of the UFS driver patch; it is a carefully validated DBY-W09 DTS override adding MMCX first and GCC UFS_PHY_GDSC second. Until that is integrated and validated, ROUND33's MMCX route is dormant on the current board DTS draft.
