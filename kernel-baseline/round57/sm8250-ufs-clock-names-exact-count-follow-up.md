# ROUND57 — SM8250 UFS clock-names exact-count follow-up

**Date:** 2026-11-24  
**Status:** SOURCE-REVIEWED FOLLOW-UP DRAFT; FULL-SOURCE APPLICATION AND SCHEMA VALIDATION NOT RUN  
**Device:** Huawei MatePad 11 DBY-W09 / KONA / SM8250 rev 2.1  
**ACK baseline:** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

## 1. Origin and primary review decision

The second AI completed ROUND54 on branch `ai-parallel/round54-ufs-review` with verdict `PASS WITH NON-BLOCKING FINDINGS`.

Finding R54-001 (P3):
- Canonical ROUND32 adds an SM8250-specific UFS binding branch.
- The branch restricts `clocks` to exactly 8 entries.
- It enumerates eight positional `clock-names.items` values but does not add `minItems` / `maxItems` to `clock-names`.
- The shared `qcom,ufs-common.yaml` permits 7..9 clock-names entries, so a malformed 7- or 9-name array may pass the conditional tuple constraint.
- The pinned SM8250 DTSI has exactly eight clock phandles and eight matching names.

The primary review accepts this as a valid schema-hardening correction. It is non-blocking to the source-level driver design but must be incorporated before final UFS binding validation.

Second-AI report:
`ai-parallel/round54/ROUND54_REVIEW.md`, branch `ai-parallel/round54-ufs-review`.

Second-AI candidate:
`ai-parallel/round54/candidates/0001-qcom-ufs-sm8250-clock-names-exact-count.patch`, blob `6f3715c8b068556baf2993477c2387df98f8a574`.

## 2. Canonical follow-up patch

Primary-owned follow-up draft:
`kernel-baseline/round57/0001-dt-bindings-ufs-sm8250-clock-names-exact-count.patch.draft`.

It adds:
```yaml
clock-names:
  minItems: 8
  maxItems: 8
  items:
    - const: core_clk
    - const: bus_aggr_clk
    - const: iface_clk
    - const: core_clk_unipro
    - const: ref_clk
    - const: tx_lane0_sync_clk
    - const: rx_lane0_sync_clk
    - const: rx_lane1_sync_clk
```

The hunk is anchored in the SM8250 branch after the ROUND32 patch's actual resulting line position. It is applied immediately after ROUND32 in the proposed series. The original ROUND32 patch remains unchanged so all historical blob references remain valid.

## 3. Updated intended binding/driver series order

1. ROUND32 — add SM8250 UFS compatible and base clock/reg branch.
2. ROUND57 — constrain SM8250 clock-names to exactly 8.
3. ROUND36 — compatible-scoped two-power-domain schema support.
4. ROUND52-0001 — VDDP/VCCQ-parent supply binding properties.
5. ROUND37 — board DTS dual-GenPD and supply delta (after migration into a real board DTS source path).
6. ROUND33 — UFS dual-GenPD / required-OPP driver logic.
7. ROUND52-0002 — VDDP managed regulator lifecycle helper.

This ordering ensures the follow-up operates after the ROUND32 branch exists. Its target file is the same UFS binding file; later binding patches target their own files/sections.

## 4. Validation boundary

Source review verifies the property placement and count intent. However, the following remain NOT_RUN:
- actual complete-worktree `git apply --check` and apply;
- combined schema validation against the real ACK binding graph;
- `dt_binding_check`;
- `dtbs_check`;
- board DTS migration and `dtc`;
- Kconfig resolution, Kleaf and kernel build;
- device runtime and boot validation.

The second AI likewise did not run these tests. This follow-up is not represented as schema PASS or build PASS.

## 5. Project state

- ROUND54 independent review: complete; one P3 schema finding; no confirmed P1/P2 driver-lifecycle defects at pinned-source review level.
- ROUND57 canonical follow-up draft: prepared on main; not applied to the ACK source tree.
- ROUND15 local environment inventory: completed; no existing build workspace found.
- ROUND16 WSL2 + Ubuntu 24.04 + pinned ACK workspace deployment: taskbook and start prompt prepared; execution report not yet uploaded.
- Stage A remains ACK 6.18.33 first; Stage B DerpFest begins only after actual Stage-A boot and storage/basic-hardware acceptance.

## ROUND59 integration correction and result (2026-11-24)

The first strict ordered-series parse found the previous ROUND57 patch blob `f282a695ed1201298f29a54ff0871084d995b3f2` had an invalid unified-diff hunk declaration: it declared 6 old / 8 new lines, while the hunk body contains 13 old lines and 15 new lines. It also used an old line anchor 163, while the ROUND32-applied SM8250 clock block begins at line 165.

The canonical patch has been corrected:
- Hunk header: `@@ -165,13 +165,15 @@`
- Current patch blob SHA: `3656f05ad01d54452b83591b762faaa71a16f592`

ROUND59 replayed the complete ordered series against exact pinned ACK file blobs. ROUND57 now passes 1/1 exact hunk after ROUND32. All seven patches / 16 hunks pass the in-memory exact-context and line-anchor simulation. This is **not** real `git apply`, `git diff --check`, dt_binding_check or a build. See `kernel-baseline/round59/round59_ufs_patch_series_exact_source_integration.md`.

The old blob SHA is retained only as historical provenance; use the current canonical blob SHA above.
