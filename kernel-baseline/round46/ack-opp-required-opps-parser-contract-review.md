# ROUND46 — ACK OPP parser contract cross-check for the UFS dual-GenPD patch

Date: 2026-11-24

Status: **PINNED-SOURCE SEMANTICS CONFIRMED; ROUND45 ALL-ENTRY PREFLIGHT IS CONSISTENT WITH THE OPP FRAMEWORK. NO PATCH CHANGE REQUIRED FROM THIS REVIEW. FULL-TREE APPLY / CHECKPATCH / BUILD REMAIN NOT_RUN.**

## 1. Fixed source baseline

- Device: Huawei MatePad 11 (2021), DBY-W09, KONA / SM8250 v2.1.
- ACK tag: `android17-6.18.33_r00`.
- Immutable commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.
- Sources reviewed:
  - `drivers/opp/of.c`, blob `505d79821584e28f454dae673cf85078762b2ec7`.
  - `drivers/opp/core.c`, blob `157c84b689feba9ae2c446083e42de63e94a38a6`.

Source pages:
- https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/opp/of.c
- https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18.33_r00/drivers/opp/core.c

## 2. OPP framework table-discovery contract

The pinned `dev_pm_opp_of_get_opp_desc_node()` helper resolves the device's `operating-points-v2` descriptor using the first phandle and returns a referenced DT node. The caller must release that reference.

The pinned `_opp_table_alloc_required_tables()` implementation uses the **first available OPP child** to determine the table-level `required_opp_count`. It counts that child's `required-opps` phandles and allocates the required-table / required-device arrays from that count.

This is a table-discovery step, not validation that every later OPP child has a matching usable reference.

## 3. Per-entry linking contract

The pinned `_of_opp_alloc_required_opps()` path is called for concrete OPP entries. For each entry, it loops over the table-level `required_opp_count`, parses that entry's corresponding `required-opps[i]`, and links the target into the required OPP table selected during table discovery.

Consequently, if the first available OPP establishes one required slot but a later available OPP omits that slot or points to an invalid target, the defect appears during per-entry parsing/linking. If a later entry declares additional slots beyond the first entry's discovered count, the table-level shape does not represent those extra slots.

## 4. ROUND45 preflight assessment

The current ROUND33 patch draft (ROUND45 revision, blob `2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5`) performs a stricter preflight before attaching the dual GenPD and before generic UFS initialization adds the OPP table:

- It obtains the UFS descriptor through `dev_pm_opp_of_get_opp_desc_node()`.
- It iterates every available OPP child, using the same available-child notion as the OPP parser.
- For this explicitly supported SM8250 UFS topology, every available OPP must contain exactly one `required-opps` reference.
- Every target must exist, be available, belong to an `operating-points-v2` table nested under `qcom,sm8250-rpmhpd`, and resolve to the exact table node advertised by that provider.
- Empty OPP tables are rejected and DT-node references are released on error and success paths.

This does not contradict the core parser's “first available OPP” table-discovery behavior. The patch validates the consistency of every concrete OPP entry against the single required slot which the table-level parser will allocate.

## 5. required_dev index and devm return semantics

The pinned `_opp_set_required_dev()` checks `required_dev_index` against `required_opp_count`, translates the supplied GenPD virtual consumer device to its GenPD device/table, and records the required device in the corresponding slot.

The patch's `required_dev_index = 0` is therefore aligned with the one-slot contract enforced by its preflight. This does not imply that both attached GenPDs should be mapped to required-opps slots; the second (GCC UFS_PHY_GDSC) domain remains attached for power-domain control, while the one required-OPP slot is routed to MMCX.

The pinned `devm_pm_opp_set_config()` wrapper returns 0 after successfully adding the managed cleanup action; checking `if (ret)` in the patch is correct. This differs from the non-devm config API's positive token on successful configuration.

## 6. Decision

No source change to ROUND33 is required based on this parser-contract review. Keep the ROUND45 all-entry validation and the current one-slot MMCX mapping.

This only establishes static consistency against the pinned OPP source. It does **not** establish:
- full-tree patch application;
- checkpatch or compiler success;
- final Kconfig resolution;
- combined DTS/schema/DTB correctness;
- runtime MMCX performance-state propagation;
- GCC GDSC behavior, UFS link startup, storage enumeration or suspend/resume;
- actual DBY-W09 boot of the 6.18.33 kernel.

## 7. Unchanged independent gates

- ROUND12 AVB footer / vbmeta descriptor metadata audit remains the only active Local Agent task; no ROUND12 report has been uploaded to `firmware-audit-v1` at this check.
- ROUND30 MMCX-to-MX parent/corner equivalence remains unresolved.
- ROUND42/43 Huawei final FDT and actual classic-FDT vs Linux EFI-stub handoff remain UNKNOWN.
- ROUND40 VCCQ-parent / VDDP teardown-order draft remains separate and must not be merged unchanged.
- Stage B Android 17 DerpFest remains deferred until Stage A 6.18.33 actually boots and passes storage/basic-hardware acceptance.

No protected branch, PR #1, device, bootloader, firmware image or partition was changed or accessed.

**Conclusion:** the ROUND45 “validate every available UFS OPP entry” guard is justified by the pinned ACK parser's split between first-entry table-shape discovery and per-entry required-OPP linking. The current patch's single required-dev slot 0 mapping is also consistent with the pinned OPP core API. All build and device validations remain NOT_RUN.
