# ROUND44 — ROUND33 UFS required-opps check aligns with the pinned ACK OPP parser

Date: 2026-11-24

Status: **FIRST-AVAILABLE-OPP VALIDATION CONFIRMED AS THE CORRECT ACK OPP-CORE MODEL. NO CHANGE TO ROUND33 DRIVER PATCH REQUIRED FOR THIS QUESTION.** This is a fixed-source review only; the driver patch remains unapplied/uncompiled.

## 1. Fixed source identities

- ACK tag: android17-6.18.33_r00
- Commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- `drivers/opp/of.c` blob: `505d79821584e28f454dae673cf85078762b2ec7`
- `drivers/opp/core.c` blob: `157c84b689feba9ae2c446083e42de63e94a38a6`
- `arch/arm64/boot/dts/qcom/sm8250.dtsi` blob: `adf6b49b52c48ca05ed6d0c1251f97ace664ef9d`
- Current ROUND33 UFS driver patch blob: `565090acbfe9aad00200b3cccbd64a8a45c7c4c3`

## 2. The OPP core explicitly uses the first available OPP entry for required-table discovery

In pinned `drivers/opp/of.c`, `_opp_table_alloc_required_tables()` has the source comment:

> "Populate all devices and opp tables which are part of required-opps list. Checking only the first OPP node should be enough."

Its implementation:
1. Calls `of_get_next_available_child(opp_np, NULL)` to get the first available OPP child.
2. Calls `of_count_phandle_with_args(first_opp, "required-opps", NULL)`.
3. Uses that count to allocate the required-OPP table/device arrays.
4. Resolves each required-OPP phandle from that same first OPP node and finds its parent OPP table.

This is the exact parser model ROUND33 had independently mirrored. A loop over all OPP entries inside the driver helper would not make its table discovery more consistent with the ACK OPP core; the generic core intentionally anchors the shared required-table metadata on the first available entry.

## 3. Per-entry required-opps links are still resolved individually

The same `drivers/opp/of.c` has `_of_opp_alloc_required_opps()` and `_link_required_opps()`:
- each concrete OPP entry allocates its own required-opps array according to the required table count established above;
- `_link_required_opps()` parses the required-opps phandle from that concrete OPP node and resolves it against the required table;
- a missing required OPP node or a target that cannot be found returns `-ENODEV`.

Thus the generic parser uses the first entry to discover the required-table schema, then resolves actual required-OPP target entries for each OPP. ROUND33's first-entry validation checks the provider/table identity used for the shared single required-dev index, while generic OPP linking handles each OPP's target.

## 4. SM8250 UFS OPP table shape

The pinned `sm8250.dtsi` defines `ufs_opp_table` on the UFS Host with two available entries:
- `opp-37500000` has one `required-opps = <&rpmhpd_opp_low_svs>`;
- `opp-300000000` has one `required-opps = <&rpmhpd_opp_nom>`.

Both targets are entries in the SM8250 RPMhPD OPP table. The same UFS table therefore exposes one required-OPP slot, while the selected required-performance level changes by UFS frequency.

This is why ROUND33 must map required-dev index 0 to MMCX; it must not allocate a second required-dev index for the GCC GDSC domain.

## 5. ROUND33 alignment result

ROUND33:
- gets the UFS OPP descriptor node;
- chooses the first available child via `of_get_next_available_child(opp_np, NULL)`;
- requires exactly one required-opps phandle;
- follows that target to its containing OPP table and provider;
- validates the provider compatible and verifies its `operating-points-v2` phandle points to the exact same table node;
- maps the UFS table's single required-dev index 0 to the first attached virtual GenPD device (MMCX).

The source review confirms that using the first available OPP for the table-level required-opps/provider identity check matches the pinned ACK OPP parser's own design. No additional loop over every OPP entry is required for this specific shared-table identity check. Per-entry OPP target resolution remains the generic OPP core's responsibility.

## 6. What this does not prove

- It does not prove that ROUND33 is accepted by a complete kernel worktree's `git apply --check`.
- It does not replace `checkpatch.pl`, Kconfig resolution, compilation, schema validation, or runtime testing.
- It does not solve the separate ROUND30 MMCX→MX corner-equivalence issue.
- It does not imply a real MMCX RPMh vote has been observed on DBY-W09.
- Current ROUND33 patch blob remains `565090acbfe9aad00200b3cccbd64a8a45c7c4c3`.

**Conclusion:** the first-entry required-opps check in ROUND33 is intentional and matches the exact fixed ACK OPP parser, which explicitly uses the first available OPP node to discover the table-level required-OPP provider metadata. No patch change is needed for this question.
