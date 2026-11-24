# ROUND33 — SM8250 UFS dual-GenPD driver patch draft

Date: 2026-11-24

Status: source patch candidate against exact ACK tag android17-6.18.33_r00. No patch applied, no checkpatch, compiler, Kconfig resolver, dt-schema, runtime test or device boot was run.

Source pin:
- ACK tag: android17-6.18.33_r00
- commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

## 1. Patch artifact

Draft patch:
- kernel-baseline/round33/0001-scsi-ufs-qcom-sm8250-dual-genpd-required-opp.patch.draft

The draft adds a helper in ufs-qcom.c and calls it before ufshcd_pltfrm_init().

## 2. Scope / compatibility guard

The helper only changes behavior when the node:
- is compatible with qcom,sm8250-ufshc; and
- has exactly two power-domains entries.

It checks the exact provider and argument order:
1. index 0 must be qcom,sm8250-rpmhpd with argument RPMHPD_MMCX;
2. index 1 must be qcom,gcc-sm8250 with argument UFS_PHY_GDSC.

If the node has one domain, the existing generic attach path is preserved. A missing power-domains property is also left on the pre-existing path. More than two domains, or a two-domain layout with different providers/order, fails clearly rather than silently routing required OPP to the wrong supplier.

The patch reads the UFS OPP description, verifies that the first available OPP contains exactly one required-opps phandle, follows that phandle to its containing OPP table and provider node, and requires that provider to be qcom,sm8250-rpmhpd. The latest revision also parses the provider node's operating-points-v2 phandle and requires it to resolve to the exact same table node containing the required-OPP target. This avoids mapping the UFS OPP to a different table merely because it is nested under a compatible RPMhPD provider. The current SM8250 OPP table has two entries, each with one RPMHPD OPP reference.

## 3. Probe order

The candidate order is:
1. validate SM8250 compatible and two-domain shape;
2. validate provider names and domain indices;
3. validate one required-opps entry and confirm its containing OPP provider is qcom,sm8250-rpmhpd;
4. call devm_pm_domain_attach_list() with PD_FLAG_DEV_LINK_ON;
5. map required_dev = pd_list->pd_devs[0], required_dev_index = 0 through devm_pm_opp_set_config();
6. call the existing ufshcd_pltfrm_init(), which later configures clock OPPs and adds the OPP table.

The exact ACK .33 OPP API's devm_pm_opp_set_config() returns 0 on success, unlike dev_pm_opp_set_config(), whose success result is a positive token. The patch uses the devm return convention and checks ret != 0.

## 4. Behavior preserved

- Existing one-domain SM8250 UFS boards retain the generic GenPD attach behavior.
- UFS_PHY_GDSC remains attached; it is not replaced by RPMHPD.
- UFS PHY remains on GCC UFS_PHY_GDSC.
- Generic ufshcd-pltfrm.c and ufs_hba_variant_ops are untouched.
- No global SM8250 RPMHPD descriptor or MMCX parent relation is changed.
- PD_FLAG_REQUIRED_OPP is deliberately not used because it attempts to map both domain indices while the UFS OPP table has only one required-OPP slot.

## 5. Remaining hard gates

- ROUND30: ACK SM8250 MMCX descriptor has no MX parent; HOS4.3 does. The patch does not solve or claim MMCX-to-MX equivalence.
- ROUND32: SM8250 UFS binding schema omission; the schema-only patch draft must be reviewed/applied to a test tree and validated.
- The actual DBY-W09 DTS must put MMCX first and GCC UFS_PHY_GDSC second.
- Verify provider status and deferred probe behavior.
- Verify device-link runtime-PM active references and UFS resume/suspend ordering.
- Verify no lifecycle conflict between OPP table cleanup, explicit required-dev token cleanup and GenPD list detach.
- Run checkpatch, Kconfig resolution, dt_binding_check, dtbs_check and compile before considering an implementation patch.
- Then perform controlled device probe and confirm MMCX vote, GCC GDSC state, UFS link startup, suspend/resume and storage enumeration.

The patch must remain a draft until these gates are closed. ROUND12 remains the only active local Agent task.

## 6. Exact sources

- QCOM UFS probe: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/ufs/host/ufs-qcom.c
- GenPD attach-list API: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/base/power/common.c
- GenPD/virtual-device attach: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/pmdomain/core.c
- OPP required-dev / devm config APIs: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/opp/core.c
- SM8250 provider compatibles and domain IDs: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/arch/arm64/boot/dts/qcom/sm8250.dtsi
- RPMHPD MMCX ID: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/include/dt-bindings/power/qcom,rpmhpd.h
- GCC UFS_PHY_GDSC ID: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/include/dt-bindings/clock/qcom,gcc-sm8250.h

## 7. Latest exact-source hunk recheck

On 2026-11-24, the complete ROUND33 draft was re-read from `main` and both unified-diff hunks were compared against the exact pinned ACK `ufs-qcom.c` file:
- ACK source blob SHA: `a80c6998406dbc88c25dbd9977699ba481207efe`.
- ROUND33 patch blob SHA: `454a4443035cf3451c87e2735f0b876d65d52f8b`.
- Include hunk `@@ -11,12 +11,18 @@`: 12 old / 18 new lines; every old-side line matches the pinned source.
- Probe hunk `@@ -2802,15 +2808,128 @@`: 15 old / 128 new lines; every old-side line matches the pinned source.

This is full-file source-context and hunk-count verification, not `git apply` on a full kernel worktree. No checkpatch, compile, dt-schema, DTB, runtime-PM, or device validation is claimed.

## 8. Latest provider-table identity hardening

ROUND38 added a source-level check that the required-OPP target's ancestor provider node advertises the exact same containing OPP table through its operating-points-v2 property. This is stricter than a provider-compatible check and prevents a false match to an unrelated table below a node with the correct compatible.

Updated patch blob SHA: `565090acbfe9aad00200b3cccbd64a8a45c7c4c3`.

The updated include and probe hunk old-side source contexts and declared old/new counts match the exact pinned ACK `ufs-qcom.c` source. This remains a source-context check only; full-tree application, checkpatch, compile and hardware tests remain NOT_RUN. See ROUND38: `../round38/rpmhpd-provider-registration-and-ufs-opp-table-identity.md`.


## 9. ROUND45 all-entry validation and scope decision

ROUND45 supersedes the earlier first-available-child-only preflight description above.

The updated patch at `kernel-baseline/round33/0001-scsi-ufs-qcom-sm8250-dual-genpd-required-opp.patch.draft` has Git blob SHA `2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5`. It adds `ufs_qcom_validate_required_opp()` and `ufs_qcom_validate_opp_table()` so every available child OPP is checked, including an empty-table rejection and balanced OF-node reference cleanup.

ROUND45 selected an explicit fail-closed driver contract rather than a DBY-W09-only opt-in property: for `qcom,sm8250-ufshc`, the ordinary one-domain path remains unchanged; the only currently supported two-domain layout is MMCX index 0 + GCC UFS_PHY_GDSC index 1; unsupported multi-domain counts or orderings fail rather than silently continuing without an attached domain. DBY-W09 is the board currently opting into this topology by its DTS. This is not a claim that arbitrary SM8250 UFS multi-domain layouts are supported.

ROUND45 parsed both unified-diff hunks against the exact pinned ACK `ufs-qcom.c` fetched at commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`: include hunk 12/18 and probe/helper hunk 15/214; both count checks and both old-side source-context comparisons PASS. The diffstat is 205 insertions. This is patch-file/hunk verification only, not full-tree `git apply`, checkpatch, compiler or device validation. See `../round45/ack-ufs-dual-genpd-all-opp-validation.md`.
