# ROUND135 — Independent source review of SM8250 UFS dual-GenPD / required-OPP candidate

- **Review owner:** 1号 AI (ChatGPT)
- **Scope:** fixed-ACK source review of ROUND45 UFS Qualcomm probe patch, the SM8250 UFS OPP table, GenPD attach semantics, OPP required-device mapping, and Kconfig dependency reachability.
- **Fixed ACK:** `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9` (`android17-6.18.33_r00`)
- **Candidate driver patch:** `kernel-baseline/round33/0001-scsi-ufs-qcom-sm8250-dual-genpd-required-opp.patch.draft`, current Git blob `2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5`.
- **Related design / schema evidence:** ROUND29, ROUND36, ROUND37, ROUND38, ROUND45.

## 1. Disposition

**SOURCE-LEVEL DESIGN REVIEW: PASS, with integration gates remaining.**

The ROUND45 hardened driver helper matches the fixed ACK SM8250 UFS device-tree shape and the documented PM domain / OPP APIs. No source-level mismatch was found in:
- the UFS Host compatible guard;
- the MMCX index-0 / GCC UFS_PHY_GDSC index-1 contract;
- required-opps target / provider OPP-table validation;
- the required_dev index-0 mapping;
- the pre-`ufshcd_pltfrm_init()` ordering;
- the source-declared Kconfig dependency route.

This is not a full-tree application, C compile, dt-schema, DTB, final .config, Kleaf build, runtime PM or device test. The current board DTS file is still a draft; the old ROUND37 patch targets a different/older draft revision and a repository-only `.dts.draft` path.

## 2. Exact pinned ACK UFS node / OPP table

Pinned file: `arch/arm64/boot/dts/qcom/sm8250.dtsi`, blob `adf6b49b52c48ca05ed6d0c1251f97ace664ef9d`.

The UFS Host node `ufs_mem_hc: ufshc@1d84000` declares:
- compatible: `qcom,sm8250-ufshc`, `qcom,ufshc`, `jedec,ufs-2.0`;
- one existing power-domain specifier: `<&gcc UFS_PHY_GDSC>`;
- UFS Host SMMU streams `0x0e0` and `0x4e0`;
- `operating-points-v2 = <&ufs_opp_table>`.

Its `ufs_opp_table` has exactly two available entries in this pinned source:
- 37.5 MHz: `required-opps = <&rpmhpd_opp_low_svs>`;
- 300 MHz: `required-opps = <&rpmhpd_opp_nom>`.

Both target OPP nodes are children of the shared `rpmhpd_opp_table`, itself a child of `power-controller` compatible with `qcom,sm8250-rpmhpd`. That provider advertises exactly one `operating-points-v2` phandle, which points back to the same table node.

Source: [pinned SM8250 UFS Host and OPP table](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/boot/dts/qcom/sm8250.dtsi#L2500-L2585).

The ROUND45 validator's path walk is therefore correct for the current tree:
1. required-opps target;
2. parent `operating-points-v2` table;
3. table parent SM8250 RPMhPD provider;
4. provider's sole `operating-points-v2` phandle;
5. exact node-pointer identity comparison against the target-containing table.

The validator also iterates every available UFS OPP child, requires exactly one `required-opps` entry for each, verifies the target node is available, balances all OF node references, and rejects an empty available table. This is stronger than the earlier first-entry-only check.

## 3. GenPD attach contract

The candidate patch checks that only the expected two-domain SM8250 UFS arrangement reaches its special path:
- `power-domains[0]`: provider `qcom,sm8250-rpmhpd`, one cell, ID `RPMHPD_MMCX`;
- `power-domains[1]`: provider `qcom,gcc-sm8250`, one cell, ID `UFS_PHY_GDSC`.

The fixed SoC DTSI confirms the UFS Host's compatible begins with `qcom,sm8250-ufshc`; this satisfies the candidate's SoC-specific guard. The provider compatible strings and IDs align with the pinned header definitions and the current ROUND37 board-delta design.

The use of `PD_FLAG_DEV_LINK_ON` is consistent with the pinned header: it creates runtime-active device links so suppliers / domains remain active while the UFS consumer is active. The patch intentionally does not use `PD_FLAG_REQUIRED_OPP`; that generic flag maps one required-OPP slot per attached domain, while this UFS table has only one required-OPP slot. The candidate instead explicitly maps that single slot to the first attached virtual GenPD device (MMCX).

One-domain and no-domain cases are left on the existing generic path. Unsupported domain counts or unrecognized two-domain provider/order/ID combinations fail closed. This is safer than silently attaching an unverified layout, given the generic GenPD multi-domain auto-attach limitation recorded in ROUND44.

## 4. OPP required-device mapping and probe ordering

Pinned `include/linux/pm_opp.h` defines `required_dev_index` as the required-OPP slot index for the specified required device. Pinned `drivers/opp/core.c::_opp_set_required_dev()`:
- rejects a required-device index greater than or equal to the OPP table's `required_opp_count`;
- verifies the supplied device is a GenPD virtual device;
- refreshes the corresponding required OPP table from the GenPD device's OPP table;
- stores the supplied virtual device in `required_devs[index]`.

The candidate sets `required_dev = pd_list->pd_devs[0]` and `required_dev_index = 0`, which matches the single required-opps cell in each UFS OPP entry and the MMCX-first ordering.

The placement in `ufs_qcom_probe()` is before `ufshcd_pltfrm_init()`. In the pinned UFS common path, `ufshcd_pltfrm_init()` performs generic OPP setup and adds the UFS OPP table later. The pinned `dev_pm_opp_set_config()` contract explicitly requires configuration before any OPPs are initialized. The ordering therefore matches the API lifecycle.

Sources:
- [pinned PM domain flags and attach API](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/include/linux/pm_domain.h#L20-L60)
- [pinned OPP config structure](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/include/linux/pm_opp.h#L58-L85)
- [pinned required-device handling / OPP config ordering](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/opp/core.c#L2443-L2643)
- [pinned UFS Qualcomm probe entry](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/host/ufs-qcom.c#L2808-L2825)

## 5. Kconfig dependency source route

The following fixed-ACK source declarations provide a route to the APIs used by the patch:
- `SCSI_UFSHCD` selects `PM_DEVFREQ` in `drivers/ufs/Kconfig`.
- `PM_DEVFREQ` selects `PM_OPP` in `drivers/devfreq/Kconfig`.
- SM8250 GCC support selects `QCOM_GDSC` in `drivers/clk/qcom/Kconfig`; `QCOM_GDSC` selects `PM_GENERIC_DOMAINS` when `PM` is enabled.
- `QCOM_RPMHPD` depends on `QCOM_RPMH && QCOM_COMMAND_DB` and selects `PM_GENERIC_DOMAINS` plus `PM_GENERIC_DOMAINS_OF` in `drivers/pmdomain/qcom/Kconfig`.
- `PM_GENERIC_DOMAINS_OF` depends on `PM_GENERIC_DOMAINS && OF` in `kernel/power/Kconfig`.

The existing storage-first config fragment requests the relevant built-in SoC/UFS/RPMh/Command DB/GCC/RPMHPD symbols. This establishes source-level dependency reachability only. No Kconfig resolver / final `.config` was executed in this review.

## 6. Integration risks not cleared

### 6.1 Board DTS patch is stale and not at a kernel source path

ROUND37's old patch was built against protected board draft blob `e86c8707c413a9376b1e332a94e292b86acde3e2`. The current main board draft and AI1 ROUND130 board copy have different blob identities and additional PMIC / memory / supply notes. Therefore do not apply the old ROUND37 patch by line number or blindly copy it.

The dual-domain property must be deliberately re-based onto the current reviewed board candidate, and that candidate must be placed at a real kernel DTS path (for example a new DBY-W09 board DTS under `arch/arm64/boot/dts/qcom/`) with the appropriate Makefile DTB entry. Verify the result has:
```dts
power-domains = <&rpmhpd RPMHPD_MMCX>,
                <&gcc UFS_PHY_GDSC>;
```
The UFS PHY's own GCC UFS_PHY_GDSC domain must remain unchanged.

### 6.2 Schema series still needs full-tree validation

The intended order is:
1. ROUND32 SM8250 compatible / clock / reg binding.
2. ROUND57 exact 8 clock-names count.
3. ROUND36 compatible-scoped two-domain common binding limit (already represented in the frozen Stage A series where applicable; do not apply twice).
4. ROUND52-0001 VDDP / VCCQ-parent supply binding.
5. The current-source board DTS candidate in a real kernel DTS path.
6. ROUND45 driver patch.
7. ROUND52-0002 VDDP managed lifecycle patch (written after / against the dual-GenPD driver include state).

Run dt-schema / `dt_binding_check`, DTS preprocessing / dtc, `dtbs_check`, then inspect the emitted DTB to verify the exact ordered two-domain array and unchanged PHY domain.

### 6.3 Independent power gates remain

- ROUND30 MMCX-to-MX ARC/corner propagation is not implemented by this GenPD mapping. Matching numeric corner indices do not prove the HOS4.3 ARC parent/dropout behavior is equivalent.
- PM8150 physical VIN input parents remain unproven; the dummy regulator fallback is not an electrical source. Do not use the GenPD patch as a reason to invent PMIC input rails.
- Final ABL memory/FDT/EFI handoff, reserved-memory map, boot/AVB/footer and selected DTBO remain unresolved.

## 7. Validation status

| Gate | Status |
|---|---|
| Fixed ACK source / UFS compatible / OPP shape | PASS (source review) |
| All-entry required-OPP validator | PASS (source review) |
| MMCX/GCC power-domain provider and ID checks | PASS (source review) |
| OPP required_dev index 0 semantics | PASS (source review) |
| Pre-UFS OPP initialization ordering | PASS (source review) |
| Kconfig dependency source route | PASS (source review) |
| Full ACK worktree patch apply | NOT_RUN |
| Full schema `dt_binding_check` | NOT_RUN |
| Board DTS preprocessing / dtc / DTB emission | NOT_RUN |
| `dtbs_check` and final DTB inspection | NOT_RUN |
| Final Kconfig resolver / built-in `.config` | NOT_RUN |
| C object compile / full Kleaf build for this series | NOT_RUN |
| MMCX runtime vote / GCC GDSC / UFS link / storage | NOT_RUN |
| Device boot / hardware acceptance | NOT_RUN |

## 8. Implementation decision

- Keep ROUND45 driver patch as a source-reviewed candidate; do not merge it into the frozen 17-patch series or AI2 branch as part of this review.
- Keep ROUND32 / ROUND57 / ROUND36 / ROUND52 binding artifacts in their recorded roles and order. Do not apply ROUND36 again if the selected 17-patch baseline already includes its blob.
- Rebase the board dual-domain delta onto the current AI1 board DTS candidate and create a real kernel DTS source path before Agent validation.
- Only after that exact series is packaged with fixed hashes should a local test Agent task be written for full disposable-tree apply, schema/DTB checks and target object/full build.
- No source code, DTS, config, protected branch, firmware or device was modified or accessed by this source review.
