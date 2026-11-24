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

The patch reads the UFS OPP description, verifies that the first available OPP contains exactly one required-opps phandle, follows that phandle to its containing OPP table and provider node, and requires that provider to be qcom,sm8250-rpmhpd. This avoids applying the index-0 MMCX mapping to an unrelated required-OPP provider. The current SM8250 OPP table has two entries, each with one RPMHPD OPP reference.

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
