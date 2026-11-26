# ROUND135 — AI1 review of the Ubuntu Linux UFS reference finding

- Owner: 1号 AI（ChatGPT）
- Review date: 2026-11-26
- Scope: reconcile AI2's Ubuntu FIT/DTB audit with the pinned ACK android17-6.18.33_r00 source and the current ROUND135 23-patch candidate.
- Reviewed AI2 report: ai2/round135-controlled-offset-taskbook-audit:firmware-analysis/round135/AI2_ROUND135_UBUNTU_LINUX_REFERENCE_AUDIT.md, blob b1dfdf1ac88013a124917898cb630564481e3056.
- Fixed ACK: aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a.
- Candidate manifest: ai1/round130-stagea-ufs-lifecycle-integration:kernel-baseline/round135/ROUND135_23_PATCH_SERIES_MANIFEST.md, current blob 9188de2022f88c374bfcaa367c505428812608d9.

## 1. Decision

**The Ubuntu UFS DT topology difference is a valid comparison item, but it does not by itself invalidate the ROUND135 dual-GenPD / required-OPP design. Do not change the frozen 23-patch candidate merely to copy the Ubuntu DTB topology.**

The Ubuntu audit reports that its UFS Host has only the GCC UFS_PHY_GDSC in power-domains, while its UFS OPP entries still refer to RPMhPD OPPs. That is a real DTB fact. However, the Ubuntu report does not provide the source of its 7.3.1-loa kernel's UFS Qualcomm probe / OPP integration. A DTB alone cannot establish how that kernel routes the required-OPP performance request at runtime.

## 2. Pinned ACK source facts

The exact pinned ACK file arch/arm64/boot/dts/qcom/sm8250.dtsi has:

- UFS Host compatible qcom,sm8250-ufshc.
- Baseline Host power-domains = <&gcc UFS_PHY_GDSC>.
- operating-points-v2 = <&ufs_opp_table>.
- Two available UFS OPP entries: 37.5 MHz with required-opps = <&rpmhpd_opp_low_svs>, and 300 MHz with required-opps = <&rpmhpd_opp_nom>.
- The separate ufs_mem_phy node also retains its GCC UFS_PHY_GDSC domain.

ROUND27's pinned-source review found that an OPP required-opps reference does not, by itself, prove an RPMhPD vote when the UFS Host is attached only to the standalone GCC UFS PHY GDSC: the inspected GDSC domain has no set_performance_state implementation and no RPMhPD parent route in the inspected upstream SM8250 DTS topology. Therefore the unmodified one-domain ACK path does not establish the desired UFS-to-MMCX vote.

## 3. What the ROUND135 candidate actually implements

The current 23-patch manifest does not add a second duplicate UFS driver patch. The driver implementation is already contained in frozen patch 5:

- Frozen patch 5: round33-checkpatch-clean.patch
- Git blob: f1d54e5e0379183fbdfb3ca6132c6d0fc61d4622

That exact patch contains the SM8250 dual-domain / required-OPP implementation reviewed in ROUND29 and hardened in ROUND45. Its intended order is:

1. Validate the SM8250 UFS Host's first domain as RPMHPD MMCX.
2. Validate the second domain as GCC UFS_PHY_GDSC.
3. Validate every available UFS OPP child has exactly one required-opps reference and that the target belongs to the exact OPP table advertised by the SM8250 RPMhPD provider.
4. Attach the two domains using devm_pm_domain_attach_list() with PD_FLAG_DEV_LINK_ON.
5. Map the UFS OPP table's sole required_dev slot to pd_list->pd_devs[0] (MMCX, required_dev_index 0).
6. Only then call ufshcd_pltfrm_init(), whose existing generic path configures the UFS clock OPPs and adds the OPP table.

PD_FLAG_REQUIRED_OPP is deliberately not used for both domains: the current UFS OPP entries have one required-opps slot, so mapping a second required-dev slot to index 1 is invalid. The GCC GDSC remains separately attached at domain index 1 for the Host/PHY power-domain relationship; the UFS PHY node itself is not changed to MMCX.

The current DBY-W09 board DTS includes the pinned sm8250.dtsi and overlays the UFS Host's ordered power-domains property. It does not remove or replace operating-points-v2, so the base 37.5/300 MHz OPP entries and their RPMhPD required-opps references remain inherited into the candidate DTB unless a later overlay unexpectedly changes them. R3 must prove this on the newly generated DTB rather than relying only on source inspection.

## 4. Why the Ubuntu DTB is not a direct replacement

AI2's Ubuntu audit is limited to an offline FIT/DTB package audit. It does not include the corresponding Linux 7.3.1-loa UFS driver source, its downstream changes to ufs_qcom_probe(), OPP configuration, GenPD attachment, or runtime-PM device links. It is therefore not possible to conclude from the DTB alone whether Ubuntu uses:
- a patched Qualcomm UFS driver that manually maps required_dev to MMCX;
- another provider/consumer performance-state path;
- or a different kernel implementation not represented in the DTB.

The Ubuntu FIT/DTB remains valuable same-device hardware and board-topology reference evidence. It is not an ACK Android DTS template and not an Android boot artifact.

## 5. Mandatory R3 checks

The Agent must verify against the final candidate tree and the real newly built huawei-dby-w09.dtb:

- Host power-domains has exactly two entries, MMCX at index 0 and GCC UFS_PHY_GDSC at index 1.
- UFS PHY power-domains remains exactly GCC UFS_PHY_GDSC.
- UFS Host retains the inherited operating-points-v2 table.
- Every available UFS OPP entry has exactly one required-opps target; the 37.5 MHz and 300 MHz entries resolve to the expected low-svs and nominal RPMhPD OPP nodes in the provider's exact table.
- The applied ufs-qcom.c contains the exact-table / all-available-OPP validator and sets required_dev to the first attached virtual GenPD before ufshcd_pltfrm_init().
- The compiled DTB, not just the DTS source, carries the expected phandles, arguments and order.

Do not remove MMCX, replace the explicit required_dev mapping, add a second required-opps slot, alter the UFS PHY's domain, or modify the frozen patch series based solely on the Ubuntu DTB.

## 6. Boundaries that remain open

This reconciliation does not prove MMCX-to-MX ARC/corner equivalence with HOS4.3, PM8150 physical input rails, ABL's final FDT / memory handoff, reserved-memory ownership, selected DTBO, AVB/footer provenance, boot-v2 ramdisk selection, UFS probe, storage enumeration, runtime-PM stability or device boot. Those remain separate gates. No device access or hardware action is authorized by this review.

**AI1 disposition:** retain the exact R2-pinned 23-patch candidate for ROUND135 R3 validation. Treat the Ubuntu UFS layout as a documented comparison, not a reason for speculative source edits.
