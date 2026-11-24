# ROUND34 — ROUND33 UFS dual-GenPD patch: exact ACK source and lifecycle review

Date: 2026-11-24

Status: **SOURCE REVIEW PASS for the audited API/order semantics; patch remains DESIGN DRAFT ONLY.** No source-tree patch application, checkpatch, Kconfig resolution, dt-schema validation, compilation, runtime test, or device boot was performed.

## 1. Fixed source baseline

- Repository: Android Common Kernel (ACK)
- Tag: `android17-6.18.33_r00`
- Tag target commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Review targets: `drivers/pmdomain/core.c`, `drivers/base/power/common.c`, `drivers/opp/core.c`, `drivers/opp/of.c`, `drivers/ufs/host/ufs-qcom.c`, and `drivers/ufs/host/ufshcd-pltfrm.c`.

This is a source review against the pinned ACK tag, not a build or device test.

## 2. Generic GenPD behavior confirms the need for explicit multi-domain attachment

In the pinned `drivers/pmdomain/core.c`, `genpd_dev_pm_attach()` explicitly returns without attaching when `power-domains` has anything other than exactly one entry; the code comment says that devices with multiple PM domains must be attached separately because the generic device path can attach only one PM domain per device (around lines 3260–3285).

The same file's `genpd_dev_pm_attach_by_id()` creates a virtual GenPD device for the requested index and attaches that virtual device to the specified domain (around lines 3289–3352). This is the expected building block for the UFS controller's two independent domains.

## 3. Attach-list flags, return value and error cleanup

Pinned `drivers/base/power/common.c` confirms:

- `dev_pm_domain_attach_list()` counts the device's `power-domains` entries and iterates through them by index (around lines 197–254).
- With `PD_FLAG_DEV_LINK_ON`, it adds `DL_FLAG_RPM_ACTIVE` to the normal runtime-PM device-link flags (around lines 207–244).
- It creates the link from the real UFS consumer to each attached virtual GenPD device, stores the devices/links, and returns the number of attached domains (around lines 246–287).
- `devm_pm_domain_attach_list()` registers the detach-list action and returns that same positive count (around lines 306–349).

Therefore ROUND33's `ret == 2` expectation is consistent with this ACK API. It is not confusing the function with `dev_pm_domain_attach()`, whose return convention is different.

ROUND33 intentionally does not set `PD_FLAG_REQUIRED_OPP`. The attach-list's `opp_tokens` array is zero-initialized; its detach path calls `dev_pm_opp_clear_config()` on those slots. The pinned OPP implementation explicitly returns immediately for token values <= 0 (around lines 2662–2671), so this is a safe no-op when the flag was not requested.

## 4. Required-OPP mapping and initialization timing

Pinned `drivers/opp/core.c` establishes the required ordering:

1. `dev_pm_opp_set_config()` obtains/creates the device's OPP table with `_add_opp_table(dev, false)` (around lines 2546–2564).
2. The OPP-table allocator calls `_of_init_opp_table()` before returning the new table (around lines 1526–1571). That stage reads the DT OPP descriptor and initializes the required-OPP table metadata.
3. `_opp_set_required_dev()` checks `required_opp_count`, obtains the required table at the requested index, maps the supplied virtual GenPD device through `dev_to_genpd_dev()`, and stores it in `required_devs[index]` (around lines 2447–2500).
4. The table's actual OPP list is still empty while `dev_pm_opp_set_config()` applies its configuration; the function explicitly rejects configuring after OPP entries have already been initialized (around lines 2566–2570).

The UFS glue path is compatible with that order. In pinned `drivers/ufs/host/ufshcd-pltfrm.c`, `ufshcd_parse_operating_points()` first calls `devm_pm_opp_set_config()` for clock configuration and only then calls `devm_pm_opp_of_add_table()` (around lines 418–491). `ufshcd_pltfrm_init()` invokes that OPP parser before continuing host initialization (around lines 648–705). In `ufs-qcom.c`, `ufs_qcom_probe()` calls `ufshcd_pltfrm_init()` directly (around lines 2809–2825).

Consequently, ROUND33's explicit `devm_pm_opp_set_config()` before `ufshcd_pltfrm_init()` is early enough to set `required_dev` before UFS OPP entries are added. It maps only index 0, preserving the existing single `required-opps` slot in the UFS OPP table.

The `devm_pm_opp_set_config()` wrapper returns 0 on success and an error otherwise (pinned `drivers/opp/core.c`, around lines 2681–2706). ROUND33 correctly treats nonzero as failure; this differs from the positive token returned by the non-devm `dev_pm_opp_set_config()` API.

## 5. Device-managed lifetime ordering

The pinned implementations register devres actions in this order for the proposed flow:

1. `devm_pm_domain_attach_list()` registers the domain-detach action.
2. ROUND33 registers the explicit required-dev OPP-config cleanup.
3. `ufshcd_parse_operating_points()` registers the clock OPP-config cleanup.
4. `devm_pm_opp_of_add_table()` registers OPP-table removal after adding the table (pinned `drivers/opp/of.c`, around lines 1102–1141).

Device-managed actions unwind in reverse registration order. Thus the OPP table is removed first, OPP configuration references are then cleared, and only afterward does the attach-list action remove links and detach the virtual GenPD devices. That preserves the required_dev target for as long as the UFS OPP configuration can refer to it.

This ordering was checked against the pinned APIs and registration call sequence. It is not a substitute for testing driver probe failure, unbind, suspend/resume, or actual hardware votes.

## 6. ROUND33 code review result

No confirmed API-return, pre-OPP initialization, provider-attach ordering, node-reference, or devres-order defect was found in the current ROUND33 draft during this source-only pass.

The current draft remains:
- `kernel-baseline/round33/0001-scsi-ufs-qcom-sm8250-dual-genpd-required-opp.patch.draft`
- Design note: `kernel-baseline/round33/sm8250-ufs-dual-genpd-patch-design.md`

No code changes were made to the patch during this round.

## 7. Remaining gates (still open)

- Verify the DBY-W09 DTS contains exactly two `power-domains` entries in this order: RPMHPD MMCX first, GCC UFS_PHY_GDSC second.
- Verify the UFS OPP table and required-opps node identities against the final device DTS/overlay.
- Apply the schema and driver patches in a complete worktree at the fixed ACK tag; run `git apply --check`, `checkpatch.pl`, Kconfig resolution, `dt_binding_check`, `dtbs_check`, and a full kernel build.
- Confirm probe/deferred-probe behavior, supplier device-link runtime-PM behavior, real MMCX performance-state votes, UFS link startup, storage enumeration, and suspend/resume on the device.
- ROUND30 remains independent: MMCX→MX parent/corner equivalence to HOS4.3 is unproven. This report does not claim to solve it.
- ROUND12 AVB metadata inspection remains the only local Agent task; its sanitized report has not yet appeared on `firmware-audit-v1`.

**Conclusion:** ROUND33's two-domain attach and required-dev mapping are now supported by exact pinned-source evidence through the relevant API and devres lifecycle. This raises confidence in the patch design, not in implementation correctness or device readiness. Keep the patch as a draft until all gates above pass.
