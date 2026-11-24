# ROUND37 — DBY-W09 UFS Host dual-GenPD board DTS delta

Date: 2026-11-24

Status: BOARD DTS DELTA DRAFT CREATED; NOT APPLIED TO PROTECTED DTS BRANCH. The delta is designed to activate the conditional path in ROUND33 after ROUND32/ROUND36 schema integration.

## 1. Target and current condition

Protected review branch: ack18-dby-w09-dts-draft
Current board file: dts/dby-w09-ack18-board.dts.draft
Current source blob SHA: e86c8707c413a9376b1e332a94e292b86acde3e2

The present board overlay overrides &ufs_mem_hc to add board rails and enable the controller, but it does not override power-domains. The Host therefore inherits the SoC's single GCC UFS_PHY_GDSC entry, as documented in ROUND35.

The exact ACK tag android17-6.18.33_r00 defines:
- rpmhpd provider compatible qcom,sm8250-rpmhpd, with one argument cell;
- gcc provider compatible qcom,gcc-sm8250, with one argument cell;
- RPMHPD domain ID RPMHPD_MMCX = 6;
- GCC domain ID UFS_PHY_GDSC = 4;
- UFS Host compatible list beginning qcom,sm8250-ufshc, fallback qcom,ufshc;
- UFS OPP table with two entries, each carrying one required-opps phandle to an RPMHPD OPP.

These match the exact provider and ID checks in ROUND33.

## 2. Proposed delta

Patch draft:
- kernel-baseline/round37/0001-dby-w09-ufs-host-dual-genpd-dts.patch.draft

It makes two minimal source changes in the board DTS draft:
1. Explicitly includes qcom,gcc-sm8250.h and qcom,rpmhpd.h for the domain-ID macros.
2. Overrides &ufs_mem_hc with:

```dts
power-domains = <&rpmhpd RPMHPD_MMCX>,
                <&gcc UFS_PHY_GDSC>;
```

The order is a hard contract with ROUND33:
- index 0 maps the UFS OPP's only required-OPP slot to the attached MMCX virtual GenPD device;
- index 1 retains the existing GCC UFS PHY GDSC power-domain consumer.

The separate &ufs_mem_phy remains attached to GCC UFS_PHY_GDSC. No MMCX-to-MX provider parent is added, and ROUND30's HOS4.3 corner-equivalence gap remains open.

## 3. Required companion integration

This DTS delta must not be considered independently complete. It must be integrated with:
- ROUND32: qcom,sm8250-ufshc selection, compatible enum and eight-clock / one-reg binding branch;
- ROUND36: compatible-scoped increase of Qualcomm UFS power-domains maximum to two only for SM8250;
- ROUND33: probe-time two-domain attach list and required-dev index-0 mapping.

The current original single-domain layout remains accepted by the ROUND36 binding rule and the ROUND33 helper preserves the generic path when only one domain is present. This delta changes the DBY-W09 board configuration to the two-domain candidate.

## 4. Validation still required

- Apply this board delta to a disposable copy of the current board DTS draft and confirm the exact hunk context.
- Integrate it in the full ACK .33_r00 source tree with ROUND32/ROUND36 binding changes.
- Run dt_binding_check, dtbs_check, and dtc; inspect the final compiled DTB to confirm exactly two UFS Host power domains in the specified order.
- Confirm the UFS PHY's own GCC GDSC property is unchanged.
- Build the ROUND33 driver patch and the storage-first kernel; test deferred probe, runtime PM device links, MMCX performance-state requests, GCC GDSC state, UFS link startup, storage enumeration, and suspend/resume.
- Separately prove the MMCX/MX corner behavior before claiming full HOS4.3 power-tree equivalence.

The isolated environment currently lacks dtc, dt_binding_check / dtbs_check (dt-schema), checkpatch.pl, and a full ACK worktree. No such validation is claimed.

## 5. Branch and device safety

- This report and patch draft were added to main only.
- ack18-dby-w09-dts-draft was not modified.
- PR #1 remains Draft and untouched.
- No device connection, flashing, partition write, firmware extraction, or local Agent task change occurred.
- ROUND12 remains the only local Agent task.

Conclusion: the board-level two-domain delta is now specified and matches the pinned ACK provider names/domain IDs and ROUND33's order contract. It remains unapplied and uncompiled. It must be reviewed together with ROUND32, ROUND36 and ROUND33 before it becomes part of the protected DTS branch or a kernel build.
