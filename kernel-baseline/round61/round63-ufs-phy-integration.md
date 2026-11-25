# ROUND61 Phase B/C continuation — ROUND63 UFS PHY always-on integration

**Date:** 2026-11-25  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Pinned ACK:** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Status:** ROUND63 candidates imported; real hosted-runner apply/check/schema validation queued by the branch workflow. No compile or hardware test is claimed.

## 1. New mandatory source integration

ROUND61's updated mission adds ROUND63's `vdda-phy-always-on` finding as a required Stage-A source patch. The primary artifacts were fetched from `main` and copied byte-for-byte into this branch:

| Candidate | Main source blob | ROUND61 path |
|---|---|---|
| QMP UFS PHY driver | `a06b7d3fc19e0b23895b0013ab9ac322d84cdda5` | `patches/round63-0001-phy-qcom-qmp-ufs-always-on.patch` |
| QMP UFS PHY binding | `a6668eebe293f9a35e9c08d6be4f37c4340e7ddd` | `patches/round63-0002-qmp-ufs-phy-binding.patch` |

The canonical main candidates and protected DTS branch were not modified.

## 2. Independent driver/lifecycle review

The pinned ACK source was fetched directly at the immutable commit. The exact QMP driver source blob is `8af777f7ddd0385a6bb9d9b9563f0e6329699cd3`; the strict binding blob is `fba7b2549ddee7ee4e048277a11a7da053d52887`.

Review findings:

- `qmp_ufs_probe()` obtains the managed regulator bulk handles before parsing the PHY DT node. The candidate registers `devm_add_action_or_reset()` after those handles have been acquired. Devres reverse-order cleanup therefore runs the retained-vdda cleanup action before the managed regulator handles are released.
- The candidate reads the optional boolean from the same `np` selected for the normal/legacy binding path. Nodes without the property retain the original `regulator_bulk_enable()` / `regulator_bulk_disable()` path.
- For the special path, it verifies `num_vregs >= 2` and that list entry zero is exactly `vdda-phy`. The primary report separately audited all 15 pinned QMP UFS regulator lists: `vdda-phy` is first and `vdda-pll` second. The remaining regulator entries continue through the normal bulk helper.
- First power-on restores `init_load_uA` and acquires one `vdda-phy` enable reference. Later power-ons restore the load without acquiring another enable reference. Power-off disables the remaining rails and sets the vdda-phy load to zero while retaining that one enable. The managed cleanup action clears the load and balances the retained enable.
- Clock-enable failure unwinds the remaining rails and drops the vdda-phy load vote while preserving the retained enable for later retry.
- The normal UFS consumer remove path is consumer-first: `ufshcd_pltfrm_remove()` calls `ufshcd_remove()`; variant exit calls `ufs_qcom_exit()`, which powers off/exits the PHY before the UFS devres PHY reference is released. The PHY core link is stateless, however, so it does not guarantee forced provider-first unbind safety. Do not manually unbind the QMP PHY provider while UFS remains bound.
- This candidate does not recreate HOS ARC's temporary 100mA proxy votes and does not resolve the physical PM8150 L5 input-supply parent. Those remain independent blockers.

No obvious enable-count imbalance was found in the reviewed normal power-on/off and normal consumer-first removal sequence. This is source review only, not runtime proof.

## 3. Workflow integration

The ROUND61 hosted workflow was updated to:
1. apply the ROUND63 binding patch and driver patch to the disposable pinned ACK checkout using real `git apply --check`, `git apply`, and `git diff --check`;
2. run strict `checkpatch.pl --no-tree --no-signoff --strict` on the ROUND63 driver patch;
3. include `Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml` in the filtered `dt_binding_check`, direct `dt-doc-validate`, and `yamllint` command set.

Workflow commit: `be920a991cef6e6bd20ffe0d7556cf2f8ce88e03`.

The hosted run must still establish the actual apply/checkpatch/schema results. The existing UFS example validation errors remain open; the Makefile target's exit code alone is not sufficient evidence. The PHY example also needs explicit positive/negative property validation after confirming the dtschema CLI and generated example paths.

## 4. Remaining validation gates

- [ ] Confirm ROUND63 patches apply in the exact ACK worktree.
- [ ] Confirm `git diff --check` and strict checkpatch pass.
- [ ] Run explicit `dt-validate` against the QMP PHY example and add positive/negative fixtures: property absent (legacy behavior), empty boolean present (accepted), malformed non-boolean value (rejected).
- [ ] Resolve UFS `power-domains` / `unevaluatedProperties` diagnostics and add the required UFS positive/negative fixtures.
- [ ] Compile the QMP PHY object and the full `//common:dby_w09` target with the manifest-pinned toolchain after a real manifest workspace is available.
- [ ] Runtime power-cycle and load-vote verification on hardware; requires local Agent/device and explicit safe authorization.
- [ ] Keep PM8150 physical input-supply and HOS ARC proxy semantics separate and unresolved.

## 5. Evidence boundary

The hosted runner is a disposable source-validation environment, not the user's manifest-pinned Repo/Kleaf workspace. No Bazel query/cquery, actual Kconfig resolution, kernel Image build, board DTB/DTBO, boot image, AVB validation or device boot is claimed here.


## 6. Positive/negative schema fixtures added

Three minimal, self-contained DTS fixtures now exercise the optional property against the processed ACK schema:

- `fixtures/round63-phy-legacy-no-property.dts` — SM8250 PHY node without the optional property; must validate.
- `fixtures/round63-phy-always-on-valid.dts` — same valid node with the empty boolean property; must validate.
- `fixtures/round63-phy-always-on-invalid-type.dts` — property incorrectly encoded as `<1>`; must be rejected.

The hosted workflow compiles these with `dtc`, runs `dt-validate -s processed-schema.json` on the first two, and asserts that the malformed-type fixture fails with a diagnostic naming `vdda-phy-always-on`. It also captures the explicit UFS example `dt-validate` return code separately, because the current UFS composition errors remain a known Phase-B blocker and must not prevent the independent PHY fixture gate from running.

Workflow updates through commit `de431840a025a3f66ff8bb3de74eae4e59edb863`. These fixtures are committed but their hosted execution result is not yet available in this session.


## 7. Independent regulator-list and bulk-helper source check

I independently re-fetched pinned `phy-qcom-qmp-ufs.c` and parsed every static `regulator_bulk_data` list in the exact source blob `8af777f7ddd0385a6bb9d9b9563f0e6329699cd3`. Result: **15/15 lists** contain exactly two entries, ordered `vdda-phy` then `vdda-pll`. This independently confirms the first-entry guard and the remaining-rail bulk operation for the currently pinned driver.

I also inspected pinned ACK `drivers/regulator/core.c`:
- `regulator_bulk_enable()` waits for all consumers and unwinds every successfully enabled consumer if any entry fails.
- `regulator_bulk_disable()` restores already-disabled entries if a later disable fails.
- `regulator_set_load()` updates the consumer load and restores the old value if DRMS update fails.

These contracts support the candidate's remaining-rail failure unwind and load-vote handling. They are source-level contracts only; no live regulator state was measured.


## 8. ROUND63 patch-format correction before hosted checkpatch

A local line-length scan found the copied driver patch's Subject line was 82 columns. The branch-local copy's subject was shortened to `[PATCH DRAFT] phy: qcom-qmp-ufs: keep vdda-phy enabled when idle`; the actual source diff/hunks are unchanged. The canonical main candidate remains untouched. A repeat line scan now finds no over-80-column added source/message lines; the only >80 line is the standard 94-column `diff --git` header. Hosted strict checkpatch remains the authoritative result.


## 9. First hosted apply failure and correction

Hosted run `45441391557` reached the exact fixed ACK commit and applied the UFS patch series plus the ROUND63 PHY binding patch. The ROUND63 driver patch then failed only its first include hunk at `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c:16`; its later four source hunks applied cleanly under diagnostic `--reject` mode. The cause was insufficient include-block context in the candidate patch. The source body itself was not changed by this failed validation attempt.

Corrected the branch-local include hunk to anchor on the preceding `linux/of_address.h` include and the following blank line, with updated hunk counts. The driver implementation hunks are unchanged. A new hosted run on commit `4f8eaacf045b1179d099ba2307175193c651884c` is executing this corrected patch.

The same failed run also exposed a race in result publication: the branch advanced after the report checkout, so the bot's push was non-fast-forward rejected. The publisher now fetches and resets to the latest branch head immediately before writing and pushing its result. Run `45442645017` is queued with that publisher fix. These are validation/workflow corrections, not evidence of a passing patch yet.


## 10. Hosted strict-checkpatch diagnostics and correction

Run `45442605274` confirms the corrected ROUND63 driver patch now applies cleanly to the fixed ACK tree, and the ROUND58 Kleaf patch also applies. Strict checkpatch then found:
- two commit-description errors because the patch preamble included raw source commit/blob hashes rather than the required `commit <sha> ("title")` format;
- one over-75-column description line;
- a continuation-alignment check in the existing `qphy_clrbits()` call;
- a `CAMELCASE` false positive for the upstream regulator API field `init_load_uA`.

The branch-local patch now removes raw hashes from the patch preamble (the report retains immutable identities), wraps the long description, and aligns the continuation at the opening parenthesis. The workflow ignores only checkpatch's `CAMELCASE` check for this patch because `init_load_uA` is an existing public field name in the pinned regulator API and cannot be renamed by this driver patch. All other strict checks remain enabled. A fresh hosted run is required to establish the corrected result.


## 11. Hosted application evidence — ROUND63 driver now applies

Hosted run `45443465025` (workflow commit `501b9c4d8c23588971e4983a71bbac2eb50f9369`) completed:
- fixed ACK HEAD verified as `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`;
- all previous UFS binding/driver patches applied;
- ROUND63 PHY binding patch applied;
- corrected ROUND63 PHY driver patch applied with no rejected hunks;
- ROUND58 Kleaf target patch applied;
- final `git diff --check` passed.

The hosted applied-diff SHA-256 was `d79a35bbfe6a44bfe9aa2e69c32caac0e3f2862349f26299d190f0bf092eef65`. The diff stat included 123 added lines in `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c`, 5 in the PHY binding, 281 in the UFS QCOM driver, 18 net in UFS bindings, 19 in `BUILD.bazel`, and the new config fragment.

The same run then stopped at strict checkpatch with exactly one remaining 75-column commit-description warning (zero errors and zero CHECKs); `CAMELCASE` was successfully ignored as configured. The final description line was wrapped in commit `dc091a5927bbdb8b8b9834996e0e5ea766658a37`. Run `45443538190` is now checking the warning-free patch. The UFS/PHY schema stage did not run in run 82 because checkpatch is an earlier gate.


## 12. Warning-free hosted checkpatch and Phase-A source gates

Hosted run `45443538190` (commit `dc091a5927bbdb8b8b9834996e0e5ea766658a37`) passed:
- exact immutable ACK source verification;
- real application of the complete UFS patch series, ROUND63 PHY binding and driver patches, and ROUND58 Kleaf target patch;
- final `git diff --check`;
- strict checkpatch for ROUND33, ROUND52-0002 and ROUND63 driver patches (only `CAMELCASE` is ignored for the upstream `init_load_uA` API field);
- buildifier `-mode=check`;
- all nine config-helper unit tests.

This closes the ROUND63 source-application/checkpatch gate and Phase A. The same run was still installing dtschema prerequisites when this report was updated; schema/fixture results remain pending. The manifest-pinned Bazel/Image workflow is independent and still running.

## 10. ROUND30 — real integration and Image build (executed 2026-11-25)

This section is appended by the ROUND30 executor. It records what was actually run; the earlier
sections remain the 2号 AI design record and are not rewritten.

**Applied artifact.** `patches/round63-0001-phy-qcom-qmp-ufs-always-on.patch` (blob
`99fffb10…`, 7,402 B), not the locked ROUND63 draft blob `a06b7d3f…`. The draft's identity is
correct but it is not appliable by `git apply` or `patch(1)`: its first hunk ends on an added line
(`+#include <linux/string.h>`) with no trailing context. `-C1`/`-C0` accept it, default context does
not, which is why a relaxed check would produce a false PASS. The draft was left untouched.

**Ordered series actually applied** (each `--check` → `apply` → `diff --check`, all rc 0):
`round36/0001-…dual-power-domains.patch.draft`, `round52-0001-context-corrected`,
`round36-corrected-power-domain-range`, `round32-corrected-sc7180-clock-names`,
`round33-checkpatch-clean`, `round52-0002-checkpatch-clean`, `round63-0002-qmp-ufs-phy-binding`,
`round63-0001-phy-qcom-qmp-ufs-always-on`, `round58-kleaf-target`.
Resulting `git diff --binary` sha256 `04534123…`, reproduced identically in the 41 GiB build copy.

**New fixture.** `fixtures/round63-phy-undeclared-property.dts` — a node that carries an
undeclared child property, used as the fourth gate case. With the binding still
`additionalProperties: false`, `dt-validate` must name the offending property; the gate asserts
that text is present, rather than trusting the tool's exit status.

**`dt-validate` exit-status trap.** On dtschema 2023.9 and 2026.9 alike, `dt-validate` prints
validation errors and still exits 0, and neither version exposes a flag to change that. Negative
fixtures are therefore judged by an explicit content gate; raw stdout and raw rc are both kept. Do
not "simplify" the gate later by switching to exit-code-only assertions — it would silently turn
the negative cases into no-ops.

**Schema results.** `dt_binding_check` PASS for the binding on both versions, with
`processed-schema.json` deleted first each time (a stale file makes the target a no-op that also
returns 0). Four fixture behaviours as designed. `vdda-phy-max-microamp` / `vdda-pll-max-microamp`
were **not** added to the schema or to any DTS.

**Code review.** 7/7 items re-derived from the applied source, including devres LIFO order
(`devm_regulator_bulk_get_const` before `devm_add_action_or_reset`, so the cleanup action runs
before the handles are released), single write to `vdda_phy_enabled`, idempotent second power-on,
and rejection of a `vreg_list` whose first entry is not `vdda-phy`. PHY core
`device_link_add(..., DL_FLAG_STATELESS)` gives **no** managed supplier-unbind guarantee, so the
consumer-first remove ordering in `ufs-qcom` remains a code contract, not something the driver core
enforces.

**Build.** `tools/bazel build //common:dby_w09 --jobs=8 --local_ram_resources=6144` → rc 0,
775 actions, 370.197 s. `Image` 44,820,992 B `36ed275b…`, `System.map` 7,610,772 B `353911b1…`,
`vmlinux` 230,254,408 B `b3ea307e…`, `.config` 238,376 B `5f7fd8b3…`. `CONFIG_PHY_QCOM_QMP_UFS=y`
and `t qmp_ufs_vdda_phy_cleanup` present in `System.map`/`vmlinux` prove the patched driver is in
the artifact. Object-level before/after: 271,032 B/164 syms → 277,056 B/174 syms, with
`regulator_set_load`/`regulator_enable`/`regulator_disable` relocations appearing only after the
patch.

**Still open (deliberately).** PM8150 L5 physical parent supply; HOS4.3 ARC/proxy lifecycle; the
actual boot entry selected by ABL; ROUND29 schema experiments. Phase E/F stay BLOCKED: an Image
that links is not a device that boots.
