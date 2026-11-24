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
