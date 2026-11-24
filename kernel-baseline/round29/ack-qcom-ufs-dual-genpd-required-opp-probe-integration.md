# ROUND29 — ACK .33 UFS dual-GenPD probe integration design

Date: 2026-11-24

Status: exact-source review against ACK tag `android17-6.18.33_r00`. Design candidate only. No patch applied, no DTS edit, no schema validation, no Kconfig resolution, no compilation, no device boot or write.

Source pin:
- ACK tag: `android17-6.18.33_r00`
- target commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Exact source URLs are listed in §8.

## 1. Finding

ROUND27 correctly identified that SM8250 UFS has `required-opps` entries pointing at RPMHPD OPPs, but its Host attaches only to GCC `UFS_PHY_GDSC`. The new exact-tag review finds a narrower way to connect the existing OPP entries to RPMHPD MMCX without changing the generic UFS platform code or the `ufs_hba_variant_ops` interface.

**Candidate architecture:** for the DBY-W09 SM8250 UFS Host only, use the Qualcomm UFS probe to:
1. attach both PM domains using `devm_pm_domain_attach_list()`, with RPMHPD MMCX first and GCC UFS PHY GDSC second;
2. set OPP `required_dev` to the first attached virtual GenPD device at index 0 using `devm_pm_opp_set_config()`;
3. then invoke the existing `ufshcd_pltfrm_init()`, whose unchanged OPP parser adds its clock configuration and initializes the OPP table afterward.

Use `PD_FLAG_DEV_LINK_ON` only. **Do not use `PD_FLAG_REQUIRED_OPP`** for this two-domain / one-required-OPP layout: that helper assigns required-dev index 0 to the first domain and index 1 to the second; OPP core rejects index 1 because the UFS OPP table has only one required-OPP slot.

This keeps the physical UFS PHY GDSC relationship. It adds a separate MMCX performance-state consumer rather than replacing the GDSC.

## 2. Exact ACK .33 source facts

### 2.1 SM8250 UFS DT topology

In `arch/arm64/boot/dts/qcom/sm8250.dtsi`, the UFS Host node:
- currently has exactly one `power-domains = <&gcc UFS_PHY_GDSC>`;
- references `operating-points-v2 = <&ufs_opp_table>`;
- its 37.5 MHz OPP has `required-opps = <&rpmhpd_opp_low_svs>`;
- its 300 MHz OPP has `required-opps = <&rpmhpd_opp_nom>`.

There is exactly one required-OPP phandle in each UFS OPP entry. The UFS PHY node also remains attached to the GCC UFS PHY GDSC.

The proposed DBY-W09 Host power-domain order is:
- index 0: `<&rpmhpd RPMHPD_MMCX>`;
- index 1: `<&gcc UFS_PHY_GDSC>`.

The PHY's existing `power-domains = <&gcc UFS_PHY_GDSC>` is not changed.

### 2.2 Generic GenPD attachment

In `drivers/pmdomain/core.c`, `genpd_dev_pm_attach()` deliberately returns without attaching a platform device when the Device Tree has more than one `power-domains` entry. The multi-domain driver must attach them itself.

`genpd_dev_pm_attach_by_id()` creates a virtual device for each selected domain. The virtual device is attached to the provider and runtime-PM enabled. During attachment, GenPD reads the default `required-opps` state at the corresponding domain index. A missing index is tolerated when `of_get_required_opp_performance_state()` returns `-ENODEV` or `-EOPNOTSUPP`.

Consequences for this DTS layout:
- the first virtual device (MMCX, index 0) sees the existing default required-opps state;
- the second virtual device (GDSC, index 1) has no second required-opps element, and the GenPD helper tolerates that absence;
- the UFS Host itself has no single attached `dev->pm_domain`; performance requests are directed through the OPP table's explicit `required_dev` mapping.

### 2.3 Attach-list flags and link power-on

In `drivers/base/power/common.c`, `dev_pm_domain_attach_list()`:
- reads all phandles from the consumer's `power-domains` property when no names list is supplied;
- attaches a virtual GenPD device for each index;
- by default creates a device link with `DL_FLAG_STATELESS | DL_FLAG_PM_RUNTIME`;
- when `PD_FLAG_DEV_LINK_ON` is specified, adds `DL_FLAG_RPM_ACTIVE` to the link flags.

In `drivers/base/core.c`, `device_link_add()` calls `pm_runtime_get_sync(supplier)` when both `DL_FLAG_PM_RUNTIME` and `DL_FLAG_RPM_ACTIVE` are present. This is important because the GenPD virtual attach itself is performed without requesting an immediate power-on; the active device link holds the supplier runtime-active during the UFS consumer's active lifetime and establishes the normal runtime-PM supplier dependency.

Do not use `PD_FLAG_ATTACH_POWER_ON` as a substitute: the inspected `dev_pm_domain_attach_list()` implementation consumes `PD_FLAG_DEV_LINK_ON`, `PD_FLAG_NO_DEV_LINK` and `PD_FLAG_REQUIRED_OPP`; it does not consume the attach/detach power-on flags in this helper.

### 2.4 OPP configuration order and multiple configuration calls

In `drivers/ufs/host/ufshcd-pltfrm.c`, `ufshcd_parse_operating_points()`:
1. builds the UFS clock-name list;
2. calls `devm_pm_opp_set_config()` for the clock configuration;
3. calls `devm_pm_opp_of_add_table()` to initialize the table.

The generic platform init calls this OPP parser before `ufshcd_init()` and before enabling UFS Host runtime PM.

In `drivers/ufs/host/ufs-qcom.c`, `ufs_qcom_probe()` currently just calls `ufshcd_pltfrm_init(pdev, &ufs_hba_qcom_vops)`.

In `drivers/opp/core.c`, `dev_pm_opp_set_config()` explicitly supports multiple calls for the same OPP table, provided all calls happen before OPP initialization and are balanced by corresponding clear-config calls. The required-dev configuration is applied before `devm_pm_opp_of_add_table()` if set in `ufs_qcom_probe()` before calling `ufshcd_pltfrm_init()`.

The key simplification is therefore:
- attach GenPDs and set required-dev in the Qualcomm-specific probe;
- let the existing generic UFS platform code make its separate clock-config call;
- let the existing generic code add the OPP table only after both configurations are present.

No change to generic `ufshcd-pltfrm.c`, the UFS HBA structure, or `ufs_hba_variant_ops` is required by this design.

## 3. Candidate patch shape — not implemented

The following is pseudocode, not a ready-to-apply patch. It omits the final compatibility guard and error-message details until the device-tree and driver binding checks are complete.

```c
#include <linux/pm_domain.h>
#include <linux/pm_opp.h>

/* In ufs_qcom_probe(), before ufshcd_pltfrm_init(): */
if (dev->of_node &&
    of_device_is_compatible(dev->of_node, "qcom,sm8250-ufshc")) {
        struct dev_pm_domain_attach_data pd_data = {
                .pd_flags = PD_FLAG_DEV_LINK_ON,
        };
        struct dev_pm_domain_list *pd_list;
        struct dev_pm_opp_config opp_cfg = {};
        int num_pds;

        num_pds = of_count_phandle_with_args(dev->of_node,
                                             "power-domains",
                                             "#power-domain-cells");
        if (num_pds != 2)
                return dev_err_probe(dev, -EINVAL,
                                     "expected MMCX + UFS PHY power domains\n");

        err = devm_pm_domain_attach_list(dev, &pd_data, &pd_list);
        if (err < 0)
                return dev_err_probe(dev, err,
                                     "failed to attach UFS power domains\n");
        if (err != 2)
                return dev_err_probe(dev, -EINVAL,
                                     "unexpected UFS power-domain count\n");

        /* DT order is MMCX first, UFS_PHY_GDSC second. */
        opp_cfg.required_dev = pd_list->pd_devs[0];
        opp_cfg.required_dev_index = 0;

        err = devm_pm_opp_set_config(dev, &opp_cfg);
        if (err)
                return dev_err_probe(dev, err,
                                     "failed to map UFS MMCX required OPP\n");
}

err = ufshcd_pltfrm_init(pdev, &ufs_hba_qcom_vops);
```

Implementation guardrails:
- The dual-domain branch must be limited to the intended SM8250 UFS compatible / board topology. Do not silently apply a single-required-OPP mapping to an unrelated multi-domain UFS node.
- Preserve the one-domain path unchanged.
- Treat a malformed/missing domain property distinctly from the intended one-domain legacy path; do not silently continue after an unexpected count on DBY-W09.
- Verify the OPP table is present and the UFS required-OPP count is exactly one before applying index 0. The base SM8250 DTSI shows this shape, but the final overlay and OPP data must be checked together.
- Keep the DT order as a documented ABI between board DTS and this driver mapping: MMCX index 0; GDSC index 1.
- Do not apply `PD_FLAG_REQUIRED_OPP` to the attach list.
- Do not remove UFS Host's `UFS_PHY_GDSC` or alter the UFS PHY's GDSC attachment.
- Include explicit `<linux/pm_domain.h>` and `<linux/pm_opp.h>` in the QCOM driver if not already present.
- Do not create any new exported symbols or change generic platform function signatures.

## 4. Managed lifetime and failure unwind

The candidate ordering is:
1. `devm_pm_domain_attach_list()` creates/attaches the two virtual domains and registers its managed detach action.
2. `devm_pm_opp_set_config()` adds an explicit MMCX required-dev configuration and registers its clear-config action.
3. `ufshcd_pltfrm_init()` later calls `devm_pm_opp_set_config()` for clocks, then `devm_pm_opp_of_add_table()`.

Device-managed cleanup is reverse-registration order. At device teardown, OPP table/config resources registered later are released before the explicit required-dev configuration, and both are released before the earlier domain-list detach action. This preserves the lifetime dependency: the OPP table does not retain a required-dev pointer after the GenPD virtual device is detached.

If any operation fails after the attach-list call, devres cleanup still unwinds the already registered domain list. The attach helper itself also has an error-unwind path that detaches earlier attached virtual devices and deletes device links if a later attachment fails.

The device-link active reference keeps the supplier runtime-active during consumer use; runtime-PM link semantics must still be validated with actual UFS probe/resume/suspend testing. This source review does not prove the MMCX rail or GDSC powers up correctly on DBY-W09.

## 5. Required validation before promoting to an implementation patch

### Source / static checks
- Verify the final Device Tree contains exactly two Host domains in the exact order MMCX then UFS PHY GDSC.
- Verify UFS PHY itself still references only GCC UFS PHY GDSC.
- Verify every UFS OPP entry retains exactly one required-opps phandle, and that the target provider phandle is an RPMHPD OPP usable by SM8250 MMCX.
- Verify the actual binding/schema permits the intended multi-domain consumer description; `power-domain-names` should only be added if schema and code use it consistently.
- Verify the driver branch is specific enough not to change other QCOM UFS boards unintentionally.
- Run checkpatch, compile, dtc, dt-schema and Kconfig resolution after source work is approved. None have been run in this round.

### Runtime / power checks
- Confirm both virtual GenPD suppliers become runtime-active before controller register access.
- Confirm UFS Host resume obtains/releases both supplier runtime-PM dependencies in the correct order.
- Confirm the low-SVS and nominal OPP transitions cause MMCX performance-state requests on the first virtual device.
- Confirm GCC UFS_PHY_GDSC still gates the PHY independently.
- Confirm failed probe unwinds both domains and the OPP config cleanly.
- Confirm repeated suspend/resume, UFS reset/link startup, low-power and gear changes.
- Verify the HOS4.3 ARC MMCX resource-name, parent/dropout and qcom,set semantics before claiming that ACK MMCX corner values are electrically equivalent to vendor HOS4.3 levels. ROUND11/ROUND27 still leave this mapping unproven.

## 6. Verification state

| Item | Status |
|---|---|
| Exact ACK .33 source tag / commit | SOURCE PINNED |
| UFS Host currently references GCC UFS_PHY_GDSC | SOURCE REVIEWED |
| UFS OPP entries each have one RPMHPD required-opps entry | SOURCE REVIEWED |
| Generic GenPD auto-attach skips multiple power-domains | SOURCE REVIEWED |
| GenPD attach-list API available in exact .33 source | SOURCE REVIEWED |
| `PD_FLAG_DEV_LINK_ON` adds RPM-active runtime supplier link | SOURCE REVIEWED |
| OPP config supports multiple config calls before table initialization | SOURCE REVIEWED |
| OPP required-dev index 0 maps to the one existing required-opps entry | SOURCE REVIEWED |
| `PD_FLAG_REQUIRED_OPP` for both domains | REJECTED — second index exceeds the single required-OPP slot |
| QCOM probe pre-attach + explicit OPP required-dev mapping | DESIGN CANDIDATE |
| DTS two-domain order | NOT APPLIED |
| Schema / dtc / Kconfig | NOT RUN |
| Patch application / kernel build | NOT RUN |
| Device probe / MMCX voltage vote / runtime-PM | NOT RUN |
| HOS4.3 MMCX/ACK corner equivalence | NOT ESTABLISHED |

## 7. Next step

Continue with a source-patch draft against the exact pinned `android17-6.18.33_r00` tree after the remaining binding and corner-evidence checks. The draft must remain unapplied/uncompiled until the source review is complete. ROUND12 AVB metadata inspection remains the only active local Agent task. Do not update the ACK DTS draft branch or PR #1.

## 8. Exact source references

- ACK tag: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00
- SM8250 UFS Host and UFS OPP table: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/arch/arm64/boot/dts/qcom/sm8250.dtsi
- QCOM UFS probe: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/ufs/host/ufs-qcom.c
- Generic UFS OPP parse and probe order: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/ufs/host/ufshcd-pltfrm.c
- GenPD attach-list and `PD_FLAG_DEV_LINK_ON`: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/base/power/common.c
- GenPD multi-domain auto-attach and virtual devices: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/pmdomain/core.c
- OPP multiple configuration calls and required-dev mapping: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/opp/core.c
- Device-link RPM runtime semantics: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/base/core.c
- PM domain flags and attach-list structures: https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/include/linux/pm_domain.h
