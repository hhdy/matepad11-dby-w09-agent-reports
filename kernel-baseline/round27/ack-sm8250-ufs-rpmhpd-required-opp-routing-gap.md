# ROUND27 — ACK SM8250 UFS required-opps to RPMHPD routing gap

Date: 2026-11-24

Status: public ACK android17-6.18 / SM8250 DTS / UFS / OPP / GenPD / GCC source review. No local firmware operation, no DTS patch application, no schema validation, no build, no device boot or write.

## 1. Finding

The SM8250 UFS node contains an operating-points-v2 table whose OPP entries reference RPMHPD corner OPPs with required-opps. This is not, by itself, proof that UFS votes the RPMHPD domain.

The generic OPP core sends a required OPP through the performance-state callback of the device's currently attached PM domain. In the upstream SM8250 DTS, UFS Host power-domains points to GCC UFS_PHY_GDSC, not directly to rpmhpd. The GCC UFS PHY GDSC has no set_performance_state implementation and the upstream GCC node is not attached to an RPMHPD parent domain in the inspected generic SM8250 DTS or the HDK/MTP board overrides.

Therefore, with the unmodified upstream SM8250 DTS/driver topology, the required-opps entry is routed through the UFS GDSC GenPD; the reviewed source does not establish a propagation path from that GDSC to RPMHPD MMCX/MX. The required-opps declarations must not be described as a confirmed UFS MMCX ARC vote until a parent/domain path or a separate RPMHPD attachment is actually present.

This is a source-topology finding, not a runtime observation. A downstream/vendor tree or a target-specific overlay could add a missing relationship; HOS4.3 runtime power-domain wiring has not been fully inventoried here.

## 2. Exact source path

### 2.1 UFS declares a required OPP

In arch/arm64/boot/dts/qcom/sm8250.dtsi:
- ufs_mem_hc has power-domains = GCC UFS_PHY_GDSC;
- ufs_mem_hc has operating-points-v2 = ufs_opp_table;
- the 37.5 MHz OPP has required-opps = rpmhpd_opp_low_svs;
- the 300 MHz OPP has required-opps = rpmhpd_opp_nom;
- ufs_mem_phy also references GCC UFS_PHY_GDSC.

This establishes an OPP-to-performance-state reference but does not specify which provider receives the performance-state call beyond the device's attached GenPD.

### 2.2 OPP core routes the level through the currently attached GenPD

In drivers/opp/core.c:
- _set_opp_level() calls dev_pm_domain_set_performance_state(dev, level);
- required OPP handling calls _set_opp_level() for each configured required_dev;
- the generic GenPD attach path sets the required device automatically when a single power domain is attached;
- when multiple power-domains are present, the GenPD core comments that platform code must specify the required-domain index/required device.

In drivers/base/power/common.c:
- dev_pm_domain_set_performance_state() dispatches through dev->pm_domain->set_performance_state when present;
- if the attached PM domain does not expose this callback, the helper returns success without a performance-state operation.

In drivers/pmdomain/core.c:
- generic GenPD performance-state handling invokes the domain's set_performance_state callback, if one exists;
- parent-domain votes are propagated only through explicit GenPD parent/subdomain links.

This makes the active PM-domain attachment and its parent graph decisive. The required-opps property does not bypass the GenPD attachment layer to call the phandle target directly.

### 2.3 UFS currently attaches to GCC GDSC, not directly to RPMHPD

The inspected upstream files show:
- sm8250.dtsi: UFS Host and UFS PHY both reference GCC UFS_PHY_GDSC;
- gcc-sm8250.c: ufs_phy_gdsc contains its register offset, GenPD name and power-state mask; it does not define a parent domain or a performance-state callback;
- drivers/clk/qcom/common.c: qcom_cc_really_probe() calls devm_pm_domain_attach_list() for the GCC device and passes the returned list into gdsc_register();
- drivers/clk/qcom/gdsc.c: each GDSC is linked to a parent only if its struct gdsc has an explicit parent, the GCC device itself is attached to a PM domain, or a parent list was supplied;
- the generic SM8250 GCC node has no power-domains property;
- the inspected sm8250-hdk.dts and sm8250-mtp.dts do not add an RPMHPD parent to GCC.

With no explicit GDSC parent and no GCC parent GenPD in this source topology, the UFS GDSC is standalone for GenPD performance-state propagation. Its power_on/power_off callbacks control the hardware GDSC, but that is separate from RPMHPD ARC corner voting.

## 3. What ACK RPMHPD itself does

ACK drivers/pmdomain/qcom/rpmhpd.c does implement RPMh ARC performance votes and GenPD aggregation. Its domain descriptors include CX, MMCX, MX, LCX, LMX, GFX and EBI resources.

For SM8250 specifically:
- CX uses the cx_w_mx_parent descriptor and propagates a parent vote to MX;
- MMCX uses the plain mmcx / mmcx_ao descriptors in the SM8250 table, without the same explicit parent link;
- a mmcx_w_cx_parent variant exists in the driver for another SoC mapping, but is not the selected SM8250 MMCX descriptor.

HOS4.3 ROUND11 found an MMCX ARC parent-supply edge targeting a child in the MX-level group. The exact qcom,resource-name, qcom,set and other ARC child properties are not yet locally captured, so the HOS edge cannot yet be asserted to be identical to RPMHPD's MMCX/MX domain descriptor relationship. Even after a valid UFS-to-MMCX vote is routed, exact HOS4.3 MMCX/MX corner equivalence remains an open point.

## 4. Consequences for this board draft

- Keep the physical UFS_PHY_GDSC power-domain reference. It controls the UFS PHY power island and must not be removed to make room for an RPMHPD vote.
- Keep the UFS OPP table and its required-opps entries as an upstream reference, but do not count them as an established RPMHPD request in the current topology.
- Keep CONFIG_QCOM_RPMHPD enabled provisionally because the board/SoC may need direct RPMHPD consumers and the future corrected routing; do not label it as proven active via UFS merely because required-opps exists.
- Do not add a speculative rpmhpd power-domain phandle to GCC without evaluating the effect on every GCC GDSC. The current qcom_cc_really_probe()/gdsc_register() path can attach the GCC's entire GDSC list beneath the GCC device's parent-domain list; this may broaden the relationship beyond UFS.
- Do not replace the UFS GDSC with RPMHPD MMCX. They serve different purposes.

## 5. Candidate correction architectures (not implemented)

1. Targeted UFS dual-domain integration. Preserve UFS_PHY_GDSC and add RPMHPD MMCX as a second UFS Host GenPD. Generic genpd_dev_pm_attach() deliberately skips devices with more than one power-domain phandle, so the UFS driver must call devm_pm_domain_attach_list() during probe and retain both virtual GenPD devices/device-links. The UFS power-domains order should be RPMHPD MMCX first, GCC UFS_PHY_GDSC second, so the existing single required-opps entry remains index 0 for RPMHPD. The UFS driver must then configure struct dev_pm_opp_config.required_dev = pd_list->pd_devs[0] and required_dev_index = 0 before devm_pm_opp_of_add_table(). This needs a carefully reviewed UFS/OPP patch and error/teardown handling.
2. Targeted GDSC parent relationship. Extend the GCC/GDSC integration so UFS_PHY_GDSC has an explicit RPMHPD parent and the required performance-state requests propagate through it. The current qcom_cc_really_probe()/gdsc_register() parent-list path can attach the GCC device's supplied parent-domain list to its GDSCs broadly, so do not add an RPMHPD parent to GCC globally unless every GCC GDSC's domain/corner semantics are justified.
3. Board-specific performance vote. If the UFS driver's OPP framework cannot safely express a second domain, add a narrowly scoped RPMHPD vote at the appropriate UFS lifecycle/OPP transitions. This must use supported RPMH/GenPD interfaces and preserve active/sleep and failure rollback behavior.

Before selecting an architecture, verify the exact HOS4.3 UFS ARC resource-name, qcom,set and parent/dropout properties from existing local data after ROUND12 and the already-queued ROUND13 mode/DRMS task. Do not run concurrent local scans or reparse the ARC supply graph.

## 5.1 Multi-domain GenPD API detail (additional ACK source review)

ACK provides devm_pm_domain_attach_list() and struct dev_pm_domain_attach_data for drivers whose device has multiple power-domains. It creates a virtual device for each listed domain, adds device links (by default DL_FLAG_STATELESS | DL_FLAG_PM_RUNTIME), and returns a struct dev_pm_domain_list containing pd_devs. The generic device-core genpd_dev_pm_attach() skips automatic attachment when more than one power-domain phandle is present, so the UFS driver must own this attach-list path.

The existing UFS platform probe calls ufshcd_parse_operating_points() before ufshcd_init(). Inside ufshcd_parse_operating_points(), ACK calls devm_pm_opp_set_config() first and devm_pm_opp_of_add_table() second. That is an insertion point for multi-domain attachment and OPP required_dev configuration; dev_pm_opp_set_config() must be called before the OPP table is initialized.

Important indexing trap: PD_FLAG_REQUIRED_OPP tells devm_pm_domain_attach_list() to configure required_dev_index=i for every attached domain. The UFS OPP entries currently contain exactly one required-opps phandle, so applying this flag to both the RPMHPD and GDSC domains will attempt to configure index 1 even though required_opp_count is 1; ACK OPP core rejects this with -EINVAL. Do not use PD_FLAG_REQUIRED_OPP for this two-domain, one-required-OPP layout.

A possible source-patch sequence is therefore:
1. Order UFS Host power-domains as RPMHPD MMCX first, GCC UFS_PHY_GDSC second; keep UFS PHY itself attached to GCC UFS_PHY_GDSC.
2. In the Qualcomm UFS platform/variant setup before OPP table parsing, call devm_pm_domain_attach_list() without PD_FLAG_REQUIRED_OPP and retain the returned list.
3. Set dev_pm_opp_config.required_dev to pd_list->pd_devs[0] and required_dev_index to 0, using devm_pm_opp_set_config() before devm_pm_opp_of_add_table(). The existing OPP required-opps[0] then targets the RPMHPD virtual device, while the second GDSC domain remains attached through its device link.
4. Verify initial power-on/runtime-PM ordering, error unwind and managed teardown. The default attach-list flags create runtime-PM device links but do not themselves prove the UFS register-access/initialization sequence is safe.

This is a source-derived implementation candidate only. It has not been patched or tested, and the RPMHPD MMCX-to-MX corner equivalence remains a separate HOS4.3 question.

Sources:
- Multi-domain GenPD attachment: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/base/power/common.c
- GenPD attach-by-id behavior: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/pmdomain/core.c
- Multi-domain flags/list structure: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/include/linux/pm_domain.h
- OPP required-device mapping: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/include/linux/pm_opp.h
- OPP config required-dev index validation: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/opp/core.c
- UFS OPP parsing order: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/ufs/host/ufshcd-pltfrm.c

## 5.1 Multi-domain GenPD API detail (additional ACK source review)

ACK provides devm_pm_domain_attach_list() and struct dev_pm_domain_attach_data for drivers whose device has multiple power-domains. It creates a virtual device for each listed domain, adds device links (by default DL_FLAG_STATELESS | DL_FLAG_PM_RUNTIME), and returns a struct dev_pm_domain_list containing pd_devs. The generic device-core genpd_dev_pm_attach() skips automatic attachment when more than one power-domain phandle is present, so the UFS driver must own this attach-list path.

The existing UFS platform probe calls ufshcd_parse_operating_points() before ufshcd_init(). Inside ufshcd_parse_operating_points(), ACK calls devm_pm_opp_set_config() first and devm_pm_opp_of_add_table() second. That is an insertion point for multi-domain attachment and OPP required_dev configuration; dev_pm_opp_set_config() must be called before the OPP table is initialized.

Important indexing trap: PD_FLAG_REQUIRED_OPP tells devm_pm_domain_attach_list() to configure required_dev_index=i for every attached domain. The UFS OPP entries currently contain exactly one required-opps phandle, so applying this flag to both the RPMHPD and GDSC domains will attempt to configure index 1 even though required_opp_count is 1; ACK OPP core rejects this with -EINVAL. Do not use PD_FLAG_REQUIRED_OPP for this two-domain, one-required-OPP layout.

A possible source-patch sequence is therefore:
1. Order UFS Host power-domains as RPMHPD MMCX first, GCC UFS_PHY_GDSC second; keep UFS PHY itself attached to GCC UFS_PHY_GDSC.
2. In the Qualcomm UFS platform/variant setup before OPP table parsing, call devm_pm_domain_attach_list() without PD_FLAG_REQUIRED_OPP and retain the returned list.
3. Set dev_pm_opp_config.required_dev to pd_list->pd_devs[0] and required_dev_index to 0, using devm_pm_opp_set_config() before devm_pm_opp_of_add_table(). The existing OPP required-opps[0] then targets the RPMHPD virtual device, while the second GDSC domain remains attached through its device link.
4. Verify initial power-on/runtime-PM ordering, error unwind and managed teardown. The default attach-list flags create runtime-PM device links but do not themselves prove the UFS register-access/initialization sequence is safe.

This is a source-derived implementation candidate only. It has not been patched or tested, and the RPMHPD MMCX-to-MX corner equivalence remains a separate HOS4.3 question.

Sources:
- Multi-domain GenPD attachment: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/base/power/common.c
- GenPD attach-by-id behavior: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/pmdomain/core.c
- Multi-domain flags/list structure: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/include/linux/pm_domain.h
- OPP required-device mapping: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/include/linux/pm_opp.h
- OPP config required-dev index validation: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/opp/core.c
- UFS OPP parsing order: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/ufs/host/ufshcd-pltfrm.c

## 6. Verification status

| Item | Status |
|---|---|
| SM8250 UFS OPP entries reference RPMHPD OPPs | SOURCE REVIEWED |
| OPP core sends required OPP through attached PM-domain performance-state path | SOURCE REVIEWED |
| UFS Host currently references GCC UFS_PHY_GDSC | SOURCE REVIEWED |
| UFS PHY currently references GCC UFS_PHY_GDSC | SOURCE REVIEWED |
| GCC UFS PHY GDSC has its own performance-state callback | NOT PRESENT IN INSPECTED GDSC DEFINITION |
| Generic SM8250 GCC has an explicit RPMHPD parent | NOT PRESENT IN INSPECTED DTS |
| HDK/MTP overrides add an RPMHPD parent to GCC | NOT PRESENT IN INSPECTED FILES |
| UFS OPP required-opps actually reaches RPMHPD under the inspected topology | NOT ESTABLISHED; source path terminates at standalone GDSC GenPD |
| HOS4.3 UFS ARC resource-name / qcom,set details | UNKNOWN / NOT_CAPTURED |
| MMCX-to-MX HOS/ACK corner equivalence | NOT_ESTABLISHED |
| devm_pm_domain_attach_list multi-domain API | SOURCE REVIEWED / AVAILABLE |
| Single required-opps entry + two-domain PD_FLAG_REQUIRED_OPP mapping | INVALID: second required_dev_index exceeds required_opp_count |
| Manual required_dev mapping to first RPMHPD virtual domain before OPP table init | DESIGN CANDIDATE |
| devm_pm_domain_attach_list multi-domain API | SOURCE REVIEWED / AVAILABLE |
| Single required-opps entry + two-domain PD_FLAG_REQUIRED_OPP mapping | INVALID: second required_dev_index exceeds required_opp_count |
| Manual required_dev mapping to first RPMHPD virtual domain before OPP table init | DESIGN CANDIDATE |
| Corrected GenPD/UFS patch | NOT_IMPLEMENTED |
| DTS/schema/Kconfig resolution, compile, boot and rail runtime | NOT_RUN |

## 7. Sources

- ACK UFS/OPP DTS: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/arch/arm64/boot/dts/qcom/sm8250.dtsi
- OPP core required-OPP routing: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/opp/core.c
- Generic GenPD attachment and performance-state routing: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/pmdomain/core.c
- PM-domain convenience wrapper: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/base/power/common.c
- Qualcomm GCC GenPD attachment: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/clk/qcom/common.c
- GCC GDSC registration: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/clk/qcom/gdsc.c
- SM8250 GCC GDSC definitions: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/clk/qcom/gcc-sm8250.c
- ACK RPMHPD descriptors and vote implementation: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/pmdomain/qcom/rpmhpd.c

## 8. Next step

Continue source-side design of a targeted UFS-to-RPMHPD performance-state path while keeping UFS_PHY_GDSC intact. Do not assume UFS required-opps already emits an MMCX vote. ROUND12 AVB metadata remains the only active local Agent task; ROUND13 regulator mode/DRMS scan stays queued after it. PR #1 remains Draft; no device operation, compile, boot or image write.
