# ROUND44 — ACK 6.18.33 UFS dual-GenPD probe contract review

Date: 2026-11-24

Status: **CORE PROBE ORDER AND API CONTRACT SOURCE-VERIFIED; PATCH HARDENING REQUIRED BEFORE FULL-TREE APPLY / BUILD.** This is a read-only review of the exact ACK source and existing ROUND32–ROUND43 artifacts. No kernel worktree was created, no patch was applied to a full source tree, no toolchain or Kconfig run was performed, and no device was accessed.

## 1. Fixed source identity and scope

- Repository: Android Common Kernel (kernel/common)
- Tag: android17-6.18.33_r00
- Immutable target commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- Architecture: arm64
- Board: Huawei MatePad 11 2021 DBY-W09, KONA / SM8250 v2.1

This review validates the proposed UFS dual-power-domain probe mechanism against the fixed ACK source. It does not close the separate MMCX-to-MX corner-equivalence issue, prove the HOS4.3 boot memory handoff, or authorize changes to the protected DTS draft branch or PR #1.

## 2. Exact source facts re-confirmed

The following files were retrieved from the immutable commit above:

- drivers/ufs/host/ufs-qcom.c
- drivers/ufs/host/ufshcd-pltfrm.c
- drivers/base/power/common.c
- drivers/pmdomain/core.c
- drivers/pmdomain/qcom/rpmhpd.c
- drivers/opp/core.c
- drivers/opp/of.c
- arch/arm64/boot/dts/qcom/sm8250.dtsi

### 2.1 Generic GenPD intentionally skips a multi-domain consumer

In drivers/pmdomain/core.c, genpd_dev_pm_attach() counts the consumer's power-domains entries and returns 0 unless the count is exactly one. The source comment explains that a device with multiple PM domains must be attached separately because the core can attach only one PM domain to the device itself.

Consequences for this design:

- With two power domains, the generic attach path does not attach either domain to the original UFS device.
- It therefore does not set the original device's pm_domain to an attached GenPD.
- A driver-level call to devm_pm_domain_attach_list() from the UFS probe is compatible with this path; it is not rejected by the helper's dev->pm_domain -EEXIST guard.
- The generic one-domain route remains available for existing SM8250 boards.

This confirms the architectural reason for a Qualcomm UFS-owned multi-domain attach operation.

### 2.2 Attach-list semantics match the proposed use

In drivers/base/power/common.c:

- dev_pm_domain_attach_list() iterates the power-domain entries by index and obtains a virtual device for each domain.
- PD_FLAG_DEV_LINK_ON adds DL_FLAG_RPM_ACTIVE to the runtime-PM/stateless device-link flags.
- The function returns the number of attached domains on success, or a negative error on failure.
- Partial attachment failure unwinds already attached virtual devices and links.
- devm_pm_domain_attach_list() registers the detach-list action with devres.
- Detach clears any attach-list-owned OPP config tokens, deletes device links, and detaches the virtual devices.

Thus the expected positive return value of 2 is the right success check for the DBY-W09 two-domain topology. The virtual domain devices can be retained in the returned list and used as required-OPP consumers.

### 2.3 UFS probe ordering is correct in principle

The pinned ufs-qcom.c calls ufshcd_pltfrm_init() from ufs_qcom_probe().

In ufshcd-pltfrm.c, the UFS OPP setup path:

1. configures the UFS clocks using devm_pm_opp_set_config();
2. then adds the DT OPP table using devm_pm_opp_of_add_table().

The proposed ROUND33 helper runs before ufshcd_pltfrm_init(). Therefore its devm_pm_opp_set_config() call can establish the required_dev mapping before the generic UFS code initializes the OPP table, which is required by the OPP API contract.

The OPP implementation confirms:

- dev_pm_opp_set_config() must be called before OPPs are initialized.
- It supports multiple configuration calls for one OPP table.
- devm_pm_opp_set_config() returns 0 on success and an errno on failure.
- required_dev_index must be within the source OPP table's required_opp_count.

The custom mapping uses slot 0. The later generic clock configuration does not itself set another required_dev mapping, so it does not intentionally replace this slot.

The custom OPP configuration's devres cleanup is registered after the attach-list cleanup action. Devres reverse-order release therefore clears the custom OPP mapping before the earlier attach-list action detaches the MMCX/GCC virtual devices. The generic UFS OPP table/config resources are registered later still and are released before those earlier resources.

### 2.4 Fixed SM8250 UFS source has two matching OPP entries

In the pinned arch/arm64/boot/dts/qcom/sm8250.dtsi:

- ufs_mem_hc is compatible with qcom,sm8250-ufshc.
- The inherited default Host power domain is GCC UFS_PHY_GDSC.
- The UFS Host uses operating-points-v2 = <&ufs_opp_table>.
- The table currently contains two available entries: opp-37500000 and opp-300000000.
- Each entry has exactly one required-opps reference: respectively rpmhpd_opp_low_svs and rpmhpd_opp_nom.
- The UFS PHY itself remains attached to GCC UFS_PHY_GDSC.

This fixed-source evidence matches the intended order contract:

1. Host power-domain index 0: RPMhPD MMCX.
2. Host power-domain index 1: GCC UFS_PHY_GDSC.
3. Host OPP required-device slot 0: the MMCX virtual GenPD device.
4. UFS PHY power domain: GCC UFS_PHY_GDSC, unchanged.

### 2.5 Provider OPP-table identity validation is valuable

The current ROUND33 draft follows the first UFS required-OPP target to its containing OPP table and provider node, then checks that the provider's operating-points-v2 phandle points to the same table node.

This is stronger than checking only the provider's compatible string. It avoids accepting a required-OPP target that happens to be nested below a node with a matching compatible but belongs to another OPP table.

Keep this identity check in the next revision.

## 3. Required ROUND33 patch hardening

### 3.1 Iterate over every available UFS OPP entry

The current draft obtains only the first available child with of_get_next_available_child(opp_np, NULL) and validates that child's required-opps property.

The exact pinned SM8250 table currently has two entries and both are valid. So this is not evidence of a failure on the unmodified pinned source.

It is nevertheless an incomplete preflight contract. A later board DTS override or source update could introduce another available OPP entry that is not covered by the first-child check.

Before full-tree application, revise the helper to:

- iterate every available child OPP node in the UFS OPP table;
- require every available entry to contain exactly one required-opps phandle;
- resolve every required-OPP target to its containing table and provider;
- require every target provider to be qcom,sm8250-rpmhpd;
- require every provider operating-points-v2 phandle to resolve to the exact table containing that entry's required-OPP target;
- fail if the table has no available OPP entries;
- balance all OF node references on success and every error path.

The validation should cover every entry, not just confirm that the first one establishes the expected provider.

### 3.2 Make the board scope explicit or document the intended driver-wide contract

The current helper activates for any qcom,sm8250-ufshc device with exactly two power-domain entries. It rejects an unexpected two-domain provider/order rather than silently proceeding.

That fail-closed behavior is safer than allowing the generic core to skip both domains and then probing UFS without either attachment. However, the helper is not uniquely scoped to DBY-W09: a future SM8250 board using a different valid dual-domain arrangement would also enter this helper and be rejected.

Before implementation, choose and document one of these contracts:

- The driver is intentionally defining this exact two-domain MMCX-then-GCC arrangement for every SM8250 UFS host; retain fail-closed validation and add compatibility review for that wider scope.
- The behavior is intended only for DBY-W09; add a deliberate, schema-reviewed board identification/opt-in mechanism and keep the generic one-domain behavior for other boards.

Do not solve this by silently returning success for an unknown two-domain layout. The generic GenPD core skips multi-domain attachment, so that would risk leaving both domains unattached.

## 4. Important separate gate: MMCX-to-MX is still unresolved

The exact ACK drivers/pmdomain/qcom/rpmhpd.c maps RPMHPD_MMCX for SM8250 to the plain mmcx descriptor. That descriptor has no .parent pointer to MX. The existing CX-to-MX relation does not imply an MMCX-to-MX relation.

ROUND30 already established that HOS4.3 reports an MMCX-to-MX ARC parent-supply edge, while the ACK SM8250 MMCX descriptor has no such parent. A simple parent pointer would propagate the same performance-state value with the current shared OPP table; it would not automatically implement an unknown HOS dropout delta.

Therefore:

- ROUND33 routes the UFS OPP request to ACK MMCX.
- ROUND33 does not prove that the full HOS4.3 MMCX-to-MX request graph is reproduced.
- Do not add an MMCX-to-MX parent or claim equivalence without the missing HOS4.3 resource/corner evidence and a reviewed implementation.
- Keep this as a separate power-tree gate when planning the first UFS boot milestone.

## 5. Current validation matrix

| Item | Result |
|---|---|
| Exact ACK commit identity | SOURCE-VERIFIED |
| Generic GenPD skips multi-domain consumers | SOURCE-VERIFIED |
| Attach-list virtual-device and return semantics | SOURCE-VERIFIED |
| PD_FLAG_DEV_LINK_ON runtime-active link behavior | SOURCE-VERIFIED |
| UFS QCOM probe calls generic platform init after the proposed insertion point | SOURCE-VERIFIED |
| OPP config must precede OPP table initialization | SOURCE-VERIFIED |
| Fixed SM8250 UFS table has two one-slot required-OPP entries | SOURCE-VERIFIED |
| ROUND33 exact provider OPP-table identity check | SOURCE-REVIEWED |
| All-entry required-OPP validation in ROUND33 | **MISSING — HARDEN BEFORE FULL-TREE APPLY** |
| Driver behavior scope for non-DBY SM8250 dual-domain boards | **REVIEW REQUIRED** |
| ROUND32/36 schema patch pair on precise file fixtures | Prior report: PASS |
| ROUND37 board-DTS patch on precise file fixture | Prior report: PASS; protected branch unchanged |
| ROUND33 patch applied to a complete ACK worktree | NOT_RUN |
| checkpatch.pl | NOT_RUN |
| dt-schema / dt_binding_check | NOT_RUN |
| Combined DBY-W09 DTS / dtbs_check / compiled DTB inspection | NOT_RUN |
| Final Kconfig / olddefconfig / built-in audit | NOT_RUN |
| Kleaf / Bazel workspace sync and kernel build | NOT_RUN |
| UFS probe, MMCX vote, GDSC state, link startup, storage enumeration | NOT_RUN |
| Suspend/resume and actual device boot | NOT_RUN |

## 6. Next work, preserving the project order

1. Harden ROUND33 to validate every available UFS OPP entry and settle the DBY-W09 versus driver-wide scope.
2. Keep the exact patch series order from ROUND38: ROUND32 schema, ROUND36 common binding, ROUND37 board DTS integration, ROUND33 UFS driver.
3. Do the first full-tree patch integration in a disposable checkout of the immutable ACK commit; run git apply --check, checkpatch.pl, dt-schema and combined DTS/DTB validation.
4. Resolve the HOS4.3 final memory handoff gate before building/booting a board DTB. ROUND42/43 establish that the actual Huawei classic-FDT versus EFI-stub path is still UNKNOWN and that no guessed RAM ranges are acceptable.
5. Keep ROUND12 as the only active local Agent task. Its scope remains read-only AVB metadata inspection using existing trusted local tools; do not create a second local firmware task.
6. Once AVB/boot-chain and memory gates are closed, continue the frozen ACK Kleaf full-image target and final Kconfig/build validation.
7. Do not begin full DerpFest device/vendor/system integration until Stage A has booted and passed its kernel/storage acceptance criteria.

## 7. Branch and safety boundary

- This report is for project main only.
- ack18-dby-w09-dts-draft remains unchanged.
- PR #1 remains Draft and unmerged.
- firmware-audit-v1 remains unchanged; ROUND12 remains pending.
- No local firmware, device, bootloader, or partition was accessed or modified.
- No compiler, Kconfig resolver, dtc, dt-schema, checkpatch, Bazel/Kleaf build, or flashing operation was run.

**Conclusion:** The core ROUND33 architecture is consistent with the fixed ACK probe and OPP APIs: attach two virtual domains, set the single required-device mapping before generic UFS OPP initialization, and preserve the normal one-domain path. The current draft still needs an all-available-OPP validation loop and an explicit board-scope contract before full-tree application. The separate MMCX-to-MX and final memory/boot-chain gates remain open.