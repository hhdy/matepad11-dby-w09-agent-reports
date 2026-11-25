# AI2-ROUND32 — child-scoped proxy-supply implementation record

date: 2026-11-25
executor: local Agent (2号 AI taskbook AI2-ROUND32)
pinned ACK: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a (android17-6.18.33_r00)
stage branch: ai-parallel/stagea-port-until-boot

## 1. Design gate: the pinned core already has a safe regulator-by-node API

Source-level trace against the pinned commit (all paths relative to the ACK
tree):

- `regulator_get()` (drivers/regulator/core.c:2358) → `_regulator_get()`
  (:2331) → `regulator_dev_lookup()` (:2003) → `regulator_dt_lookup()`
  (:1975) → `of_regulator_dev_lookup(dev, dev_of_node(dev), supply)` — the
  plain path only ever reads the *consumer device's own* node.
- `of_get_regulator(dev, node, supply)` (drivers/regulator/of_regulator.c)
  reads `<supply>-supply` from the explicit `node` via `of_parse_phandle()`,
  then falls back to `of_get_child_regulator(dev->of_node, ...)`, which is
  **recursive** over all descendants.
- `of_regulator_dev_lookup(dev, np, supply)` (of_regulator.c:663) resolves
  the phandle from `np`, looks the rdev up by node
  (`of_find_regulator_by_node()` → `class_find_device_by_of_node`, class-core
  refcount +1), and returns **-EPROBE_DEFER** when the node exists but has no
  registered device.
- **`of_regulator_get(dev, node, id)`** (of_regulator.c, EXPORT_SYMBOL_GPL,
  declared `__must_check` in include/linux/regulator/consumer.h) →
  `_of_regulator_get()` → `_regulator_get_common_check()` +
  `of_regulator_dev_lookup()` + `_regulator_get_common()` (core.c:2204).
  This is exactly the needed regulator-by-device-node API with the full
  shared allocation path (coupling check, `regulator_resolve_supply()`,
  module ref, `create_regulator()` under `regulator_lock()`, open_count,
  `device_link_add()`), so **no new core API was required**.
- `_regulator_get_common()` dummy fallback happens only for -ENODEV;
  **-EPROBE_DEFER is returned untouched**, so "target not registered yet" is
  distinguishable from "no such supply".
- Non-coupled regulators get `n_coupled = n_resolved = 1`
  (`regulator_init_coupling()`), so self-targets pass the coupling gate
  immediately.

## 2. Self-target timing proof

`regulator_register()` does `device_add(&rdev->dev)` (core.c, before
`rdev_init_debugfs()` at :5998) and `rdev->dev.of_node =
of_node_get(config->of_node)` earlier (:5880). The ROUND31 hook (and the
ROUND32 hook) runs after both, therefore at hook time
`class_find_device_by_of_node()` already finds the just-registered rdev:
a child whose `proxy-supply` phandle points at itself resolves to its own
rdev. No recursion into `regulator_register()` happens, no lock is held
across the lookup, and the resulting handle's get/put is balanced
(`regulator_put()` → `_regulator_put()` → `put_device()`).

## 3. Child-scoped mapping rules implemented (patch 13)

- child node carries `proxy-supply` → handle resolved by
  `of_regulator_get(reg_dev, reg_node, "proxy")` from the child node.
- child node carries no `proxy-supply` → legacy ROUND31 behavior unchanged
  (`regulator_get(reg_dev, "proxy")`, which includes the recursive child
  search on the provider node).
- **ambiguity gate**: child-scoped + provider-level `proxy-supply` on the
  same provider → `-EINVAL`, no lookup performed.  (Explicit, testable
  rejection chosen over silent priority.)
- consumer gains `reg_dev`/`reg_node`/`child_scoped`/`deferred` context;
  votes are applied by a shared `proxy_consumer_apply_votes()` helper with
  reverse-order rollback on partial failure.

## 4. Deferred handling

- `-EPROBE_DEFER` at registration (target rdev not yet registered, or its
  coupling unresolved): consumer is **parked** (not an error, no vote made),
  back-pointer stays valid, `rdev->proxy_consumer` returns the parked
  consumer so an unregister still cleans it.
- `late_initcall` (level 7, i.e. strictly before the level-7s
  `late_initcall_sync` bulk revoke) retry pass re-resolves parked consumers
  once and applies their votes; a vote failure inside the retry unwinds and
  frees the consumer.
- Consumers still parked at the bulk revoke are dropped **without ever
  having voted** (explicit log).  Nothing claims a rail was kept on.

## 5. Ordering / cleanup semantics retained from ROUND31

- `late_initcall_sync` bulk revoke runs once; per-rdev back-pointers are
  cleared inside `regulator_proxy_consumer_remove()` so individual
  unregister and bulk revoke can never act on the same consumer twice;
  repeated teardown is a no-op.
- Makefile order stays core-first, proxy-second; the new `late_initcall`
  retry lives in the same object, so it cannot precede the core's own
  late initcalls.
- Core's delayed unused-regulator cleanup (late_initcall work, then delayed
  work window) runs *after* our revoke decision point: revoking the proxy
  votes does **not** guarantee the rail turns off, and the revoke also does
  not guarantee it stays on — a still-unused rail is closed later by the
  core's own cleanup.  This is stated explicitly; no always-on semantics
  were introduced.

## 6. Kconfig

`REGULATOR_PROXY_CONSUMER` now `depends on OF` (follow-up patch, allowed):
the child-scoped path calls `of_regulator_get()`, which has **no !CONFIG_OF
inline stub** in the pinned consumer.h (only the `_optional` variants have
one), so building without OF would fail at link time.  Proxy properties only
come from DT, so the dependency is semantic, not just mechanical.

## 7. Binding (patch 14)

- child-level `proxy-supply` declared inside the existing
  `^(smps|ldo|lvs|bob)[0-9]+$` pattern properties; `unevaluatedProperties:
  false` preserved everywhere; no key relaxed.
- provider-level `proxy-supply` description extended (legacy mapping + the
  mixing prohibition).
- **`$ref: .../definitions/phandle` was deliberately NOT added**: the
  dtschema meta-schema (core.yaml, `'--supply$'` rule) restricts any
  `*-supply` property to `description`/`deprecated` keys only, so a `$ref`
  fails `dt-doc-validate` (observed, then removed).  Type conveyance follows
  the same convention as every other `*-supply` declaration in the tree.
- Consequence: a plain u32 instead of a phandle cannot be rejected at schema
  level; it surfaces at runtime as -EPROBE_DEFER (phandle target never
  registers).  A dangling label reference is rejected by dtc at compile
  time.  Both are covered by fixtures/tests.

## 8. Review DTS (patch 15)

`arch/arm64/boot/dts/qcom/dby-w09-proxy-review.dts` expresses the HOS4.3
ROUND13 evidence (L5/L9 children each with `proxy-supply` self-phandle +
`qcom,proxy-consumer-enable` + `qcom,proxy-consumer-current = <100000>`) in
the ACK flattened `qcom,pm8150-rpmh-regulators` shape.  No voltages/modes
are restated (board draft territory).  Not referenced by any build target.
Validates clean on the regulator node; the only diagnostics are the known
ROUND29 F1 root-compatible gap (`arm/qcom.yaml` has no `huawei,dby-w09`
board entry), asserted explicitly in the fixture gate instead of being
"fixed" by editing arm/qcom.yaml in this series.

## 9. Verification summary (numbers in the round report)

- 15/15 patches apply with 45/45 zero rc; ROUND31 blobs 1-12 re-verified.
- checkpatch --strict: 0E/0C on 13/14; 2 documented warnings on 15.
- Host mock suites compile the **real** driver source: legacy 38/38,
  ROUND32 child-scoped 73/73 (both committed under kernel-baseline/round61/tests/).
- Schema gate 14/14 across dtschema 2023.9 and 2026.9 with content
  assertions on negative cases.
- Full `//common:dby_w09` Kleaf Image rebuild PASS (hashes in the report).


## ROUND33 follow-up: enforce self-target lifetime ownership (2号 AI implementation)

- Source patch: `patches/round33-0001-regulator-proxy-self-target-only.patch` (blob `262ab30f458ebb603902014be8bbc9a5a8654437`, SHA-256 `5505d1e3f8dbec696d797e15c0484263e532c3397174cd149915ae8b5c7ec0e9`).
- The per-rdev `proxy_consumer` back-pointer is the owner and teardown hook. A child-scoped or legacy provider-level `proxy-supply` must now resolve through `of_parse_phandle()` to the exact `reg_node` that owns the request. A cross-target phandle returns `-EINVAL` before regulator handle acquisition or any vote.
- Legacy provider-level mapping remains available for the single request-bearing child that is itself the provider phandle target. If another child on the same provider attempts a proxy request, it is rejected rather than sharing a foreign target.
- Binding descriptions now state the same runtime self-target rule. L5 and L9 review DTS already uses separate self-targets and remains unchanged.
- Host harness now mocks OF phandle parsing and provider-level regulator lookup against the named target. ROUND32 suite adds nine assertions: child cross-target rejection, legacy cross-target rejection, and legacy self-target register/teardown. Existing 38-check ROUND31 suite and all prior ROUND32 coverage are retained.
- **Verification status:** code and tests committed to the Stage A branch; patch application against the pinned ACK, strict checkpatch, dtschema/dt_binding_check, full Kleaf Image rebuild, ROUND58 config and helper regressions still require the local Agent execution. Do not mark this follow-up PASS until those checks complete.


### ROUND33 patch-format repair after Agent failure (2号 AI)

- The first Agent verification correctly found malformed hunk counts in the original combined patch 16; no dependent checks were run.
- Corrected the patch by splitting the driver runtime guard and binding documentation into two independently reviewable patches:
  - Patch 16 driver: blob `3899e2b7ce7f6e028bf3f79ed31fc47cf442abfe`, SHA-256 `7b4858f5bf8f80e83092275afc1add586676b45ebc4f343fa9d2fcb218ec2de4`.
  - Patch 17 binding: blob `d2e818296118672bd708db34ed08d817fcd3895b`, SHA-256 `d19fb3b6ddf43ed5c05c1ca6dc3d7a57602514fb954bb3854b5a7ee78d681d05`.
- A local structural pass now confirms all five hunk headers exactly match their body line counts: driver 6/30, 6/7, 6/25; binding 7/9, 11/11. This is only text-structure verification, **not** proof of git apply or source-context applicability.
- The series record now has 17 patches. All runtime tests, checkpatch, schema checks, and full Image rebuild remain pending a fresh local Agent run.
