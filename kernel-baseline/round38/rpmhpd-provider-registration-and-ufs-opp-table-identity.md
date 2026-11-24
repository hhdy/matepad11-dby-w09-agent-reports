# ROUND38 — RPMhPD provider registration, OPP-table identity and UFS attach rollback

Date: 2026-11-24

Status: PINNED-SOURCE REVIEW PASS for provider ordering/defer rollback; ROUND33 driver draft strengthened with exact provider OPP-table identity validation. No full-tree patch application, checkpatch, build, dt-schema, DTB, runtime, or device test was run.

## 1. Fixed baseline

- ACK tag: android17-6.18.33_r00
- Tag target commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- Reviewed: drivers/pmdomain/qcom/rpmhpd.c, drivers/pmdomain/core.c, drivers/base/power/common.c, drivers/opp/of.c, drivers/opp/core.c, drivers/of/base.c, drivers/ufs/host/ufs-qcom.c, and the SM8250 UFS/RPMHPD DTS nodes.

## 2. MMCX exists as a real SM8250 RPMhPD domain

The pinned rpmhpd.c source defines:
- mmcx with resource name mmcx.lvl;
- a peer mmcx_ao;
- the SM8250 domain index array maps RPMHPD_MMCX to &mmcx;
- rpmhpd_probe() assigns rpmhpd_set_performance_state as the GenPD callback and initializes the domain with pm_genpd_init().

The pinned binding ID is RPMHPD_MMCX = 6. GCC's UFS_PHY_GDSC = 4. These are consistent with the current ROUND33 exact domain checks and ROUND37 DTS delta.

This confirms that MMCX is present in the SM8250 RPMhPD provider implementation. It does not prove the PMIC/ARC corner semantics match HOS4.3 MMCX→MX; ROUND30 remains open.

## 3. RPMhPD OPP tables are ready before provider exposure

The exact rpmhpd_probe() sequence:
1. reads Command DB resource addresses and validates the slave ID;
2. creates the GenPD domains, sets their power and performance-state operations, and initializes them;
3. invokes of_genpd_add_provider_onecell().

The exact of_genpd_add_provider_onecell() loop:
1. assigns the RPMhPD provider node to each domain's GenPD device;
2. calls dev_pm_opp_of_add_table_indexed(&genpd->dev, i) for performance-state domains;
3. obtains/stores the GenPD OPP-table handle;
4. only after each domain's setup sets genpd->provider / has_provider;
5. only after the loop registers the OF GenPD provider with genpd_add_provider().

The pinned OPP helper _of_add_table_indexed() explicitly maps every requested index to index 0 when the provider has exactly one operating-points-v2 phandle. SM8250's rpmhpd provider declares exactly one shared rpmhpd_opp_table phandle. Thus the MMCX domain's performance-state OPP table is registered before the provider becomes attachable.

This narrows the earlier ROUND29 observation to the exact provider registration and OPP indexed-table fallback code.

## 4. Deferred-probe and partial-attach failure behavior

- genpd_dev_pm_attach_by_id() returns an error pointer with deferred-probe state when the OF domain provider is not registered yet.
- dev_pm_domain_attach_list() creates attached domain devices in property order.
- If attaching a later domain fails, its err_attach unwind removes device links and detaches every previously attached domain. Therefore a second-domain provider defer does not intentionally leave the first MMCX domain attached.
- devm_pm_domain_attach_list() registers its final detach action only after the full list has attached successfully.

This supports using the MMCX-first, GCC-second ordering without a partial attach leak. It does not replace runtime device-link, resume/suspend or probe-failure testing.

## 5. Required-OPP index behavior

The pinned GenPD helper:
- calls genpd_set_required_opp(dev, index) for each virtual PM-domain device;
- applies a default performance state when the indexed required-OPP is present;
- treats -ENODEV and -EOPNOTSUPP as absence of a default required state rather than a fatal failure.

The UFS OPP table has one required-OPP phandle per entry. Therefore index 0 (MMCX) receives the UFS OPP's RPMhPD performance state; index 1 (GCC GDSC) has no second required-OPP slot and does not receive a default required state. ROUND33 separately maps the UFS OPP table's sole required-dev index 0 to the MMCX virtual GenPD device.

The generic attach-list's PD_FLAG_REQUIRED_OPP remains inappropriate here: it sets required_dev_index = i for each domain. For index 1 that exceeds the one-entry required-OPP slot. ROUND33 uses only PD_FLAG_DEV_LINK_ON and explicitly configures the single required-dev index 0.

## 6. ROUND33 patch strengthening: exact OPP-table identity

The prior ROUND33 helper validated that the required-OPP target was under a node compatible with qcom,sm8250-rpmhpd. ROUND38 identified that this checks the provider type but does not prove the provider itself advertises that exact OPP table.

The current ROUND33 draft now additionally:
- obtains the required-OPP target's parent OPP table and parent provider node;
- parses the provider node's operating-points-v2 phandle at index 0;
- requires the parsed provider table node pointer to equal the target's containing OPP table node;
- drops all three node references after the comparison, including failure paths.

Current ROUND33 patch blob SHA: 565090acbfe9aad00200b3cccbd64a8a45c7c4c3.

The updated include and probe hunks were checked against the exact pinned ACK ufs-qcom.c source:
- Include hunk @@ -11,12 +11,18 @@: old/new counts and old-side source context match.
- Probe hunk @@ -2802,15 +2808,141 @@: old/new counts and old-side source context match.

This is exact hunk-context verification, not full-worktree git apply, checkpatch.pl, compile, or runtime validation.

## 7. Remaining gates

- Integrate ROUND32, ROUND36, ROUND37 and updated ROUND33 in a disposable full ACK .33_r00 worktree.
- Run git apply --check, checkpatch.pl, Kconfig resolution, dt_binding_check, dtbs_check, dtc and a complete kernel build.
- Check final DTB contains exactly Host domains MMCX index 0 / GCC GDSC index 1 and preserves the UFS PHY's GCC GDSC.
- Verify actual MMCX OPP votes, GCC GDSC state, UFS link startup, storage enumeration, runtime PM, suspend/resume.
- Keep MMCX→MX corner equivalence, PM8150 physical parent rails/mode, memory handoff and AVB/ramdisk as separate blockers.
- ROUND12 remains the only local Agent task; it has not been uploaded to firmware-audit-v1.

Conclusion: the fixed ACK source confirms MMCX provider availability, indexed OPP setup, and safe attach-list failure rollback. ROUND33 now verifies the exact required OPP table phandle rather than only a compatible string. The driver/DTS/schema design is more internally consistent, but none of this constitutes a compiled or boot-tested kernel.
