# ROUND61 Continuous Stage-A Port — Progress Log

**Owner:** Second GitHub-connected AI  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Mission:** `kernel-baseline/round61/ROUND61_LONG_RUNNING_STAGEA_MISSION.md`  
**Fixed ACK:** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

## Current overall state

**PHASE A + PHASE B PASS; PHASE C PASS; PHASE D IMAGE BUILD PASS (archived .config independently rechecked 33/33).** The latest nine-stage workflow retry exposed and isolated a toolchain-discovery path bug; it did not invalidate the earlier successful Image build.

| Phase | Current state | Evidence / exit gate |
|---|---|---|
| A — real Git patch application | PASS | Hosted validation run 45457083961: exact ACK commit verified; ordered UFS + ROUND63 binding/driver + ROUND58 Kleaf patches applied with real git apply; diff-check, strict checkpatch, buildifier and 11-test config-helper suite passed. Only CAMELCASE is ignored for the existing `init_load_uA` API field. |
| B — UFS / PHY binding validation | PASS | Hosted run 45457083961: kernel dt_binding_check with dtschema 2023.9; 2 UFS positive + 8 UFS negative fixtures; 2 PHY positive + 1 PHY negative fixture all behaved as expected. Artifact 14951770706. |
| C — Kleaf target validation | PASS | Original successful run 45453412267 completed official manifest sync, exact ACK pin, Bazel query/cquery and the manifest-pinned `//common:dby_w09` target. It resolved `.config`, `Image`, `System.map`, and `vmlinux`. Run 45463060672 additionally passed manifest sync and ACK pin; its later toolchain-discovery step failed on a bad constants-file path, not on Kleaf target analysis. |
| D — final Kconfig + Image build | PASS (33/33 archived config recheck) | Original run 45453412267 built Image successfully (44,820,992 B). Its archived `.config` was independently checked against the current 33-symbol validator: 33/33 =y, no missing symbols, no non-y values, no duplicates; 238,376 B, SHA-256 `5f7fd8b32a4127b7ca10d2333d71e6d10aec7a566cf886251f7bc2af253366d7`. The new nine-stage retry is to validate exact toolchain discovery in a transparent workflow; its stage-4 fix is now committed. |
| E — board DTS + memory/power handoff | BLOCKED | No trusted final HOS4.3 post-ABL FDT/EFI memory handoff or PM8150 physical supply-parent map. Do not guess. |
| F — boot image / ramdisk / AVB | BLOCKED | ROUND62 same-device cross-reference warns fastboot RAM boot may be refused, but exact HOS4.3 AVB/footer/partition metadata and ABL behavior remain unverified. |
| G — device validation | NOT RUN | No boot authorization, partition write, or hardware test. |

Phase E blocker report: `kernel-baseline/round61/phase-e-board-dts-and-memory-handoff.md` (committed 2026-11-25). It records the exact missing HOS4.3 final ABL memory handoff and physical PM8150 input-parent evidence, and keeps the DTS draft review-only.

Phase F blocker report: `kernel-baseline/round61/phase-f-boot-packaging-avb.md` (existing; reviewed 2026-11-25). It records the missing trusted AVB footer/vbmeta descriptor inspection and exact HOS4.3 header-v2 / separate-ramdisk packaging metadata.

## 2026-11-24 execution evidence

### Real source patch and driver style checks

Hosted runner [45435020774](https://github.com/hhdy/matepad11-dby-w09-agent-reports/actions/runs/45435020774):
- Fetched exact ACK commit and verified source blob identities.
- Applied the UFS source patch series with real `git apply --check`, `git apply` and `git diff --check`.
- ROUND57 was skipped because its additional `minItems/maxItems` on the fixed eight-entry `clock-names.items` list violates ACK's dt-schema meta-schema. ROUND32 already provides the eight ordered `const` entries; exact count still needs negative-fixture proof.
- Applied the ROUND58 Kleaf target patch and storage-first fragment.
- Strict checkpatch with `--no-signoff --strict` passed for the branch-local cleaned ROUND33 and ROUND52-0002 patches: 0 errors, 0 warnings, 0 checks. No author sign-off was fabricated.

### Kleaf candidate and config helper

Run 45435020774:
- `buildifier -mode=check` initially found a single formatting issue: one blank line was needed after the new `kernel_build(name = "dby_w09")` target.
- The ROUND61-local ROUND58 patch now includes that blank line.
- A follow-up workflow revision removes temporary auto-fix and requires `buildifier -mode=check` to pass on the patch itself.
- All 9 Python config-validator unit tests passed.

### UFS schema result

Run 45435020774:
- The colon-separated `DT_SCHEMA_FILES` filter now selects the two UFS schema files.
- Direct `dt-doc-validate` and direct `yamllint` completed successfully.
- The processed schema and both UFS example DTBs were generated.
- The example validation output still reports:
  - `qcom,ufs.example.dtb`: `power-domains` is too short for the selected qcom,ufs schema.
  - `unevaluatedProperties` rejects common UFS properties including interrupts, iommus, phys/phy-names, resets, and regulator supplies.
- The Makefile/example path does not reliably propagate these diagnostics as a nonzero target result. Therefore Phase B is NOT PASS even though the workflow step concluded success.
- Next work: inspect the merged schema/evaluation path and run explicit `dt-validate` on the generated UFS example DTBs with a nonzero failure gate. Do not weaken `unevaluatedProperties` or skip examples to force a pass.

## Phase E evidence report

`kernel-baseline/round61/phase-e-board-dts-memory-power-gates.md` records why ROUND37 remains review-only: no trusted final HOS4.3 FDT/EFI memory handoff and no board-specific PM8150 VDDP/VCCQ parent-supply facts. No memory range or regulator parent is guessed.

## Next concrete actions

1. Re-run the current 33-symbol config validator against the archived `dby_w09.config` from artifact 14951184014; do not launch another full Image build just for this check.
2. Correct the manifest toolchain reporting: resolve the actual Kleaf-pinned Clang `r584948c` and Rust `1.91.1.p3` paths rather than reporting the alphabetically first toolchain directories.
3. After review/approval, split the monolithic manifest workflow step into stage-specific steps so Actions exposes sync, patching, query, build and artifact-validation progress independently. Do not use `cancel-in-progress: true`.
4. Keep ROUND37 excluded until Phase E evidence is supplied. Continue the final HOS4.3 FDT/memory handoff and PM8150 physical supply-parent evidence work; do not guess.
5. Keep Phase F blocked pending trusted AVB/footer/descriptor and HOS4.3 packaging evidence. Do not start DerpFest Stage B or any device write/boot operation.


## 2026-11-25 ROUND63 mandatory integration

**Branch HEAD after this progress update:** pending commit SHA (this file update).  
**Active phase:** Phase A/B/C source integration; hosted validation required.

- Read the updated full ROUND61 mission, ROUND63 primary report, ROUND62 boot-chain cross-reference, ROUND59 exact-source integration report, ROUND60 Kleaf/config review, and ROUND58 target/helper artifacts.
- Copied the exact main-branch ROUND63 candidates into this branch without editing their canonical originals:
  - Driver candidate source blob: `a06b7d3fc19e0b23895b0013ab9ac322d84cdda5`.
  - Binding candidate source blob: `a6668eebe293f9a35e9c08d6be4f37c4340e7ddd`.
- Added both patches to the real pinned-ACK GitHub Actions apply sequence after the existing UFS binding/driver patch items. The workflow now runs strict checkpatch on the ROUND63 driver patch and includes the QMP UFS PHY binding in the filtered dt_binding_check, direct dt-doc-validate and yamllint command sets.
- Independent lifecycle review recorded in `round63-ufs-phy-integration.md`: managed cleanup is registered after regulator acquisition and therefore runs before regulator-handle release; ordinary UFS consumer removal powers off/exits the PHY before releasing the PHY reference; the stateless PHY device link does not guarantee forced provider-first unbind safety.
- The ROUND63 candidate does not resolve HOS ARC 100mA proxy votes or the physical PM8150 L5 input-supply parent. Neither is guessed or silently marked closed.

### Current ROUND63 validation status

| Check | Status |
|---|---|
| Exact source candidate copied into dedicated branch | PASS |
| Independent source/lifecycle review | PASS (review only) |
| Real `git apply --check` / apply on pinned ACK | PENDING hosted run |
| `git diff --check` | PENDING hosted run |
| Strict checkpatch | PENDING hosted run |
| QMP UFS PHY `dt_binding_check` / direct example validation | PENDING hosted run |
| QMP UFS PHY object / full Image compile | BLOCKED pending manifest-pinned Repo/Kleaf toolchain |
| Runtime power/load transition test | BLOCKED pending device and approved local test |

The workflow's earlier UFS example diagnostics remain unresolved. Phase B is still PARTIAL/BLOCKED; do not treat a successful make target exit as proof while direct example validation is not clean.

### Next concrete actions

1. Inspect the new hosted workflow run and fix any actual ROUND63 patch, checkpatch, buildifier or schema errors on this branch.
2. Add direct QMP PHY example validation with positive/negative fixtures after confirming the installed `dt-validate` CLI and generated example paths.
3. Resolve UFS schema-composition diagnostics and add the mission-required clock/domain/supply negative fixtures.
4. Continue to the next unblocked build/source work; do not wait for the local memory/AVB/device gates.


### ROUND63 fixture and diagnostic-gate update (2026-11-25)

Branch HEAD before this log update: `1c703050087f2d0fb6ad8eed3b01cd63e5229502`.

Added three DTS fixtures under `kernel-baseline/round61/fixtures/`:
- `round63-phy-legacy-no-property.dts`: optional property absent; expected PASS.
- `round63-phy-always-on-valid.dts`: empty boolean present; expected PASS.
- `round63-phy-always-on-invalid-type.dts`: property encoded as a cell value; expected FAIL.

The workflow now compiles the fixtures with `dtc`, validates the first two with the processed ACK schema, and asserts that the malformed-type fixture is rejected with a diagnostic naming the property. It also runs explicit `dt-validate` on the UFS example and prints the actual return code/output while keeping the known UFS failure distinct from the PHY fixture gate.

Workflow revision: `de431840a025a3f66ff8bb3de74eae4e59edb863`. Fixture/report update commit: `1c703050087f2d0fb6ad8eed3b01cd63e5229502`.

**Execution status remains PENDING:** this session's GitHub connector exposes job/run-log retrieval only after a run/job ID is known, but does not expose a push-triggered run listing. The new workflow is configured to trigger on these branch changes; no result is claimed until actual runner evidence is available. Local container has no `dtc`, `dt-validate`, `dtschema`, `bazel`, or `repo`, so the fixtures cannot be executed locally here.


### ROUND63 regulator-list cross-check (2026-11-25)

Independently parsed all 15 static regulator bulk lists in pinned ACK QMP UFS PHY source blob `8af777f7ddd0385a6bb9d9b9563f0e6329699cd3`: all 15 are ordered `vdda-phy`, then `vdda-pll`. Also inspected pinned regulator-core bulk helpers: bulk enable unwinds successful entries on partial failure; bulk disable restores already-disabled entries if a later disable fails; `regulator_set_load()` restores the previous load if DRMS update fails. The ROUND63 report records this source evidence. No runtime regulator state is claimed.

Report update commit: `ff816f9665876200a5df63f14aa42f10385b1c77`.

The first outstanding gate remains the actual hosted Actions result for the updated workflow; the local container cannot run dtc/dtschema or the manifest-pinned Bazel toolchain.


## 2026-11-25 manifest-pinned hosted Kleaf/Image build attempt

**Trigger commit:** `2229d9b8982d42c4d47f6ec92b1fdfab632f5746`  
**Workflow:** `.github/workflows/round61-manifest-kleaf-build.yml`  
**Pinned manifest commit:** `46a1a5274ff0b40419952c861a8958bba5f28cfc` on `common-android17-6.18`  
**Fixed ACK common commit:** `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

Added a one-shot GitHub-hosted build workflow (triggered only by `run-manifest-kleaf-build.txt`) to attempt the official kernel Repo manifest path rather than substituting the host's preinstalled Clang. It:
- verifies the manifest branch resolves to the exact manifest commit before syncing;
- syncs the official kernel manifest, records `repo manifest -r`, build/kernel revision, Bazel/Clang/Rust versions and lockfile hash;
- checks out the immutable ACK commit into the `common` project;
- applies the ordered UFS patch set, the two ROUND63 PHY patches and the ROUND58 Kleaf target in a disposable manifest workspace;
- runs strict checkpatch, buildifier, the 9 config-helper tests, Bazel query/cquery, and the full `//common:dby_w09` Image build with pipefail;
- runs the final-config validator, hashes Image/.config/System.map/vmlinux, uploads artifacts, and publishes the result/manifest back to this branch.

ROUND57 remains deliberately superseded rather than applied: ROUND32's fixed eight-entry `clock-names.items` list already expresses exact cardinality, while ACK dt-schema rejects redundant minItems/maxItems on that list. The earlier schema diagnostics and the rationale are documented above.

**Status: TRIGGER COMMITTED / RESULT NOT YET AVAILABLE.** No repo sync, Bazel query, final Kconfig resolution or Image build is claimed until the hosted workflow writes `hosted-build-latest.md`. If the workflow cannot complete because the hosted environment cannot access the manifest or dependencies, that exact external blocker will be recorded there. No local firmware, device, boot image or partition was accessed.


### Hosted validation result publication added

The UFS/PHY validation workflow was hardened to publish its actual runner evidence to `kernel-baseline/round61/hosted-ufs-validation-latest.md` and upload its logs as an Actions artifact. Its push-path filter now excludes progress/result documents, preventing a report commit from retriggering the same validation job. The workflow has `contents: write` only for this evidence publication; no other branch is targeted.

Workflow update commit: `35c71f9299165443586fe7e27cc196bcaab7382b`. This update itself triggers the narrowed validation workflow. The result file is not present yet, so patch/schema/fixture outcomes remain PENDING rather than assumed.


### ROUND63 checkpatch preflight correction

The independent driver-patch line scan found an 82-column Subject line. Shortened only the branch-local patch subject to `[PATCH DRAFT] phy: qcom-qmp-ufs: keep vdda-phy enabled when idle`; source hunks are unchanged and canonical main candidate remains untouched. Repeat scan has no over-80-column source/message lines (only the conventional `diff --git` header). This patch update triggers the narrowed UFS/PHY hosted validation workflow again. Commit: `3d56f4449ff3330300036b5a79cde3550db00f3f`; report note commit: `853538b3a26c965eea25224f8f9458cf133d9d49`.


## Phase B fixture expansion — 2026-11-25

Added `tests/generate_round61_ufs_fixtures.py` and wired it into the ACK schema workflow. It generates nine minimal DTS fixtures and checks the exact intended matrix against processed ACK schemas: SM8250 1/2 GenPD accepted; SM8250 7/9 clock names rejected; SM8250 3 GenPD rejected; SM8150 2 GenPD rejected; missing VDDP/VCCQ-parent max-load pair rejected; zero VDDP load rejected. The SM8150 fixture uses its valid 9-clock/two-reg baseline so the failure isolates the non-SM8250 power-domain limit.

Positive UFS fixture output is retained, and every negative fixture must fail with a diagnostic naming its expected property. ROUND63 PHY fixtures remain independent: property absent accepted, empty boolean accepted, malformed cell-valued property rejected.

Added `phase-b-dt-binding-validation.md` with exact command gates and the Round57 supersession rationale. The workflow publishes real output to `hosted-ufs-validation-latest.md` and uploads artifacts. **All current fixture outcomes remain pending** until that hosted result appears; the prior run predates these tests.


The UFS negative matrix was extended to test zero VCCQ-parent max-microamp as well as zero VDDP load, so both positive-load constraints are exercised. Current generator has ten cases (two positive, eight negative). Workflow now requires both zero-load values to be rejected.


### Actual hosted ROUND63 apply diagnostics

Run `45441391557` fetched exact ACK `8ad08f75...`, verified the prior source blob identities, and applied ROUND32, ROUND36, corrected ROUND52-0001, cleaned ROUND33, cleaned ROUND52-0002 and the ROUND63 PHY binding patch. The ROUND63 driver patch's first include hunk failed at line 16; all later driver hunks applied in diagnostic reject mode. This is a real failure, not a pass.

Corrected the include hunk with broader pinned-source context (including `linux/of_address.h` and the blank line after the include block). Driver implementation hunks unchanged. New run `45442605274` tests the corrected patch. The prior run's evidence-publish push also failed non-fast-forward because the branch advanced after clone; publisher now fetches/resets to the latest branch before commit. Run `45442645017` contains that publication fix. Await these actual results before changing Phase A to PASS.


### ROUND63 strict-checkpatch correction

Run `45442605274` proves the corrected driver patch and ROUND58 Kleaf patch both apply to the fixed ACK tree. The next gate failed strict checkpatch on two raw commit hashes in the patch preamble, one long description line, one continuation alignment, and the upstream API field spelling `init_load_uA`. The branch-local patch now removes raw hashes from the preamble, wraps the line, aligns `qphy_clrbits()`, and the workflow ignores only the false-positive `CAMELCASE` check for this upstream field. Other strict checks remain enabled. A fresh hosted run is pending.

The first manifest build run `45441246235` confirmed the official manifest branch resolved to the pinned manifest commit and initialized successfully, but `repo sync` failed because Repo v2.71 does not accept `--depth` on `repo sync`. The workflow now removes that unsupported flag (keeps `-c` branch-only sync) and retries the immutable ACK tag checkout. The result publisher is race-safe with latest-branch fetch/retry. Trigger commit `9934bf735a31c565456fd7a1c5c8d67121e8a541` starts the corrected manifest sync/build attempt.


### ROUND63 real apply now confirmed; one final checkpatch warning fixed

Hosted run `45443465025` confirms, on the exact ACK commit, the previous UFS series, ROUND63 binding patch, corrected ROUND63 driver patch (all hunks, no rejects), and ROUND58 Kleaf patch all apply; final `git diff --check` passes. Applied-diff SHA-256: `d79a35bbfe6a44bfe9aa2e69c32caac0e3f2862349f26299d190f0bf092eef65`.

That run stopped at checkpatch with only one remaining 75-column commit-description warning (0 errors, 0 CHECKs); the final description line was wrapped in commit `dc091a5927bbdb8b8b9834996e0e5ea766658a37`. Latest run `45443538190` is validating the warning-free patch. Phase A remains PARTIAL until that gate passes; Phase B has not yet run on this latest applied patch because checkpatch is an earlier gate.


### Hosted run 83 pre-schema gates passed

Run `45443538190` (commit `dc091a5927bbdb8b8b9834996e0e5ea766658a37`) has completed successfully through:
- exact ACK source verification and all ordered source patch applications, including both ROUND63 PHY patches and ROUND58 Kleaf target;
- final `git diff --check`;
- strict checkpatch on ROUND33, ROUND52-0002 and ROUND63 driver patches (the only ignored type is the upstream `init_load_uA` CAMELCASE false positive);
- `buildifier -mode=check common/BUILD.bazel`;
- all 9 config-helper unit tests.

At the time of this update the same run is installing dtschema prerequisites; the schema and fixture step has not yet completed. Phase A is now PASS. Phase C is still PARTIAL until manifest-pinned Bazel query/cquery and Image build complete.


### Phase B run-83 result: validator diagnostics are output-based

Run `45443538190` passed source patch/checkpatch/buildifier/unit-test gates, then exposed two harness facts: the direct UFS example `dt-validate` command returned 0 despite printing schema diagnostics, and the generated UFS fixture DTS had root `interrupt-parent` after a subnode (invalid DTS property ordering). Fixed the fixture generator to place all root properties before subnodes. Updated validation so positive DTBs require empty diagnostic logs and negative DTBs must contain the expected property diagnostic, independent of dt-validate's exit status. The original UFS example diagnostics are now a final failure gate. The processed schema is also retained as a hashed artifact for inspection. New run is pending.


### Manifest sync succeeded; toolchain preflight remains unresolved

Hosted manifest run `45442933079` successfully initialized the pinned `common-android17-6.18` manifest and completed `repo sync`. It verified the exact ACK common HEAD `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`, recorded `build/kernel` at `2bebe7c443d0e6d5d549fb2a2377dce980d1b15e`, and published `manifest-pinned.xml` (SHA-256 `6449879cd7081345cf0a2e7060a1e40b9edfe1b8b22629263c96f8e2141a1f11`). It failed after source identity capture and before Bazel target query; no Bazel query or Image build occurred. The coarse stage label did not identify which toolchain preflight command failed. The workflow now sets the manifest JDK explicitly and records granular Bazel/JDK/Clang/Rust stages and paths. Trigger commit `82f218ad5b042c89596d58b6fd9563c4f9fc3324` starts the next diagnostic attempt.


### UFS schema ownership correction

The exact ACK tree already selects `qcom,sm8250-ufshc` in `qcom,sc7180-ufshc.yaml` and defines the eight-clock SM8250 branch there. ROUND32's addition to `qcom,ufs.yaml` duplicates that selector, so both hosted workflows now skip ROUND32 (canonical draft untouched). ROUND57 is likewise redundant against the existing fixed eight-item tuple.

Moved the four ROUND52-0001 supply/load property definitions and pair requirements into shared `qcom,ufs-common.yaml`, which is referenced by both Qualcomm UFS binding families. The branch-local patch still applies after ROUND36; canonical ROUND52 remains untouched. The schema workflow now directly validates generic `ufs-common.yaml` and the actual `qcom,sc7180-ufshc.yaml` binding as well.


## 2026-11-25 follow-up — hosted failures converted into targeted fixes

### Latest UFS / PHY validation (run 45445251142)

- Exact ACK patch application, ROUND63 PHY binding/driver application, git diff --check, strict checkpatch, buildifier and the 9 config-helper tests all completed successfully.
- The ten UFS fixtures reached their intended matrix: two positive cases passed and eight negative cases were rejected with the expected property diagnostics.
- The three ROUND63 PHY fixtures were not reached in this run because the UFS fixture stage stopped first.
- The remaining failure is now isolated: the positive SM8250 fixture is rejected by the separately selected qcom,sc7180-ufshc.yaml schema because its top-level unevaluatedProperties: false does not accept the two new VDDP/VCCQ-parent properties as currently composed through the nested Qualcomm common schema. Do not weaken unevaluatedProperties. Next step is to validate the schema composition against the ACK-supported dtschema minimum (2023.9) before changing the schema layout.
- Workflow diagnostic commit f6e6894ed062d144ad992c5a43afd9d2782fc409 pins dtschema to the ACK Makefile's declared minimum version 2023.9 for a controlled compatibility comparison. Its hosted result is pending.

### Manifest-pinned Kleaf/Image attempt (run 45444678133)

- Official manifest sync succeeded and resolved the fixed ACK common commit and build/kernel commit exactly.
- The runner then failed before Bazel query because it invoked tools/bazel --version; the manifest-provided Kleaf wrapper interprets this as an unsupported startup option and exits with Unknown startup option: '--version'.
- Corrected the preflight to invoke the Bazel version subcommand (tools/bazel version) in workflow commit 6594582ddd6758ba59ba0ec8ed85869cf73a517f.
- Triggered a fresh manifest-pinned build in commit 17fc9603ce29f0dbaa270fd1c0cfe8922fd4e5e7. Await its actual result; no Bazel query, cquery, Kconfig resolution or Image build is claimed yet.

### Current gate summary

- Phase A: PASS (hosted exact-source patch apply, diff-check and strict style gates).
- Phase B: BLOCKED on schema composition / dtschema compatibility; new controlled-version run pending.
- Phase C/D: PARTIAL / NOT RUN beyond source target validation; corrected manifest-pinned Bazel preflight run pending.
- Phase E: BLOCKED on target-specific HOS4.3 FDT/EFI memory handoff and PM8150 supply-parent evidence.
- Phase F/G: NOT RUN; no boot image or device write/boot operation performed.


### dtschema 2023.9 comparison and fixture correction

Run 45446071024 used the ACK Makefile's declared minimum dtschema version 2023.9. Under that version, the SM8250 one-domain positive fixture (including VDDP/VCCQ-parent metadata) validates with an empty diagnostic log, so the prior latest-dtschema unevaluatedProperties failure is not reproduced on the ACK-minimum tool version. The two-domain positive fixture exposed a fixture-generation error: its power-domain providers declare #power-domain-cells = <0> but the generated references incorrectly appended a zero argument, causing the two-domain list to be decoded as four entries. Corrected the generator to emit <&pdN> with no argument in commit 3f7284355b881bbba59b5d6092ae384b324e574b. The same run still shows diagnostics on the upstream qcom,ufs.example.dtb; investigate whether the example's provider-less phandle encoding or a schema condition is responsible, and do not suppress it.


### Correct ACK schema target and hunk accounting

The original ROUND32/ROUND57 drafts target qcom,ufs.yaml, but the pinned ACK commit already selects qcom,sm8250-ufshc via qcom,sc7180-ufshc.yaml. Applying the original ROUND32 would select the same SM8250 node through two independent strict schemas. The correct Stage-A adjustment is therefore a dedicated branch-local patch against qcom,sc7180-ufshc.yaml, adding maxItems: 8 to the non-SC7180 (SM8250) clock-names branch. This is a source-based correction to the old series, not a change to the immutable ACK baseline.

The first two real git apply attempts exposed a unified-diff hunk-count defect in that new patch: the blank context line after clock-names was not counted in the hunk header. Corrected the hunk to 3 old / 4 new lines in patch commit 0dfefc43e707929e29d187d333b30d9a05d3eafb; a direct exact-source context comparison now matches the pinned ACK file. Hosted real git apply validation is pending.

The manifest-pinned build run 45446186250 passed repo sync, exact ACK pin verification, manifest JDK discovery, and the Kleaf wrapper version command. Bazel then failed before analysis because JAVA_HOME was relative (prebuilts/jdk/jdk11/linux-x86); Bazel 8.7 requires an absolute path. Corrected the workflow to realpath the manifest java executable and set an absolute runner TMPDIR in commit 409af36b6814b275c615d539cb8ecf25357d0731. The build workflow now applies the corrected SM8250 schema patch; retry triggered by commit 1f62f80cd87461c59f068598344eb5057e88b28b. No Bazel query, cquery, final .config, Image compile or Image artifact has passed yet.


### Power-domain cardinality correction from processed-schema inspection

Run 45448394286 applied every patch successfully and completed all pre-schema gates, but its provider-backed one-domain fixture exposed a schema-generation detail: dtschema 2023.9 converts maxItems: 2 without an explicit minItems into an exact two-entry array. This made ROUND36 unintentionally reject the valid one-domain SM8250 topology and caused the related unevaluatedProperties cascade. Inspected the actual processed-schema.json artifact to confirm qcom,ufs-common.yaml emitted minItems: 2, maxItems: 2. Added branch-local patch round61/patches/round36-corrected-power-domain-range.patch to set minItems: 1 alongside maxItems: 2, preserving the intended one-or-two SM8250 range; the non-SM8250 conditional remains exactly one. Exact source-context comparison passed. Both UFS validation and manifest-pinned build workflows now apply this correction after ROUND36. UFS workflow retry is pending; manifest build retry triggered by 558c2d2deb1c8d5bd6eaea29db6766cf7e04af64.


### Patch ordering correction after ROUND52-0001 full-file update

The latest hosted UFS run 45449480649 passed ROUND36, the ROUND52-0001 shared-schema patch, and the new power-domain/clock-count correction only when applied in the correct sequence; the initial workflow sequence had placed the minItems correction before ROUND52-0001, whose full-file replacement overwrote it. Reordered both UFS validation and manifest-build workflows to apply ROUND36 → ROUND52-0001 → explicit minItems=1 range correction → SM8250 clock-names maxItems correction. The earlier run failed at the subsequent ROUND52 patch because of this ordering, not because of the correction hunk itself. Fresh UFS and manifest runs are pending.


### Conditional branch lower-bound correction

The latest processed-schema artifact from run 45449803857 confirms the shared property now emits minItems: 1, maxItems: 2, but the SM8250 conditional's own then.properties.power-domains.maxItems: 2 is independently converted to minItems: 2. The previous correction therefore did not fully restore the intended one-or-two range. Extended round36-corrected-power-domain-range.patch to add minItems: 1 in both the shared property and the SM8250 then-branch. The non-SM8250 else branch remains exactly one. Fresh UFS validation and manifest-pinned build runs are pending after this patch update.


## 2026-11-25 — Phase B closed; manifest build host compatibility fix

### Phase B — PASS (latest hosted run 45451513173)

- Exact ACK source: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.
- Real ordered patch application, `git diff --check`, strict checkpatch, buildifier and all 9 config-helper unit tests passed.
- `make ARCH=arm64 dt_binding_check` completed with dtschema 2023.9.
- UFS fixtures: 2/2 positive cases passed (SM8250 one/two power domains); 8/8 negative cases rejected as expected (7/9 clocks, 3 domains, non-SM8250 dual domain, missing/zero VDDP and VCCQ-parent load pairs).
- ROUND63 PHY fixtures: 2/2 positive cases passed (legacy absent property and valid boolean); malformed cell-valued boolean rejected as expected.
- Artifact ID `14947424627`; processed-schema SHA-256 `da083e8307d1f903d5784392b3cba29542343f49964482882b84f13a478447f6`.
- The schema log notes two unrelated malformed upstream YAML files ignored by the scanner; the changed schemas and explicit fixtures passed. Phase B is closed for this patch set.

### Phase C/D — manifest-pinned build retry after identified runner ABI gap

Run `45450833773` successfully synced the official `common-android17-6.18` manifest, verified the exact ACK common commit and build/kernel revision, and successfully invoked manifest Bazel 8.7. It then failed before Bazel query because the manifest-provided Clang 3289846 requires `libtinfo.so.5`, which is absent from the Ubuntu-latest (Ubuntu 26.04) runner. Exact log: `clang.real: error while loading shared libraries: libtinfo.so.5: cannot open shared object file` (exit 127). This is a runner userspace compatibility failure, not a source/compiler error.

Corrected `.github/workflows/round61-manifest-kleaf-build.yml` to pin `ubuntu-22.04` and install the real `libtinfo5` compatibility package rather than creating an unsafe symlink to libtinfo.so.6. Retry trigger commit: `4a2db7667b14d1fb83477e692b6f38d6e5c126b2`. Await the new run before claiming Bazel query, cquery, Kconfig resolution or Image compilation.

### Current gate summary

- Phase A: PASS — exact-source real patch application, whitespace/style checks, BUILD syntax/buildifier and config-helper tests.
- Phase B: PASS — authoritative pinned-version schema validation plus positive/negative UFS and ROUND63 PHY fixtures.
- Phase C/D: IN PROGRESS — manifest sync and exact source pin pass; prior build attempt blocked at Clang runtime dependency before Bazel analysis; Ubuntu 22.04 + libtinfo5 retry queued.
- Phase E: BLOCKED — actual HOS4.3 final post-ABL memory handoff and PM8150 physical supply-parent evidence unavailable.
- Phase F: BLOCKED — trusted AVB footer/descriptor and exact HOS4.3 packaging metadata unavailable.
- Phase G: NOT RUN — no device operation or boot authorization.


### Build retry 45452267778 — Clang runtime fixed; strict checkpatch false positive isolated

The Ubuntu 22.04 runner successfully installed and executed the manifest toolchain: OpenJDK 11.0.15, Bazel 8.7.0 and Rust 1.91.1; Clang was located and executed far enough for the workflow to proceed. The run stopped at strict checkpatch on the ROUND63 patch's use of the existing kernel struct member `init_load_uA`: upstream checkpatch emitted one CAMELCASE CHECK (0 errors, 0 warnings). The independent UFS workflow already uses `--ignore CAMELCASE` for this exact known API-name false positive and still reports 0 errors / 0 warnings. Narrowly aligned the manifest build workflow to ignore only CAMELCASE for ROUND63; all other strict checks remain active. Retry trigger commit `1b833dd74ddb39dd90f7a691f62ce313e0dfe5d2`. No Bazel query, cquery, final .config or Image compile has yet run.


### Watchdog — corrected diagnosis after independent verification (2026-11-25)

**Supersedes the preliminary false-stall diagnosis above.** Independent read-only verification is recorded in `firmware-analysis/round61/agent-verification-runner-stall-report.md` (commit `05824fdf63207929feb499d8da0ca515fa5e6459`, report blob `37dd1b1dcb9ac31782a67d597c32aebf06bd0cb1`).

**Confirmed outcome:** run `45453412267` / job `138656311747` completed successfully at `2026-11-24T18:22:49Z`, exit 0, after 29m56s total. Its monolithic step 3 ran 28m44s. The Bazel Image build itself took 1,348.097s (22m28s; 775 actions). It validated the final config against the then-current 31-symbol checker and published commit `019463c350223a6b79654cea5f074ece6c9961c5`. Artifact `round61-ack-6.18.33-image-build` (ID `14951184014`) contains Image (44,820,992 B; SHA-256 `e3c1cb564f767ed6c9961298b9bafd10473facaddbc92dc38247bd8290400e40`) and `dby_w09.config` (238,376 B; SHA-256 `5f7fd8b32a4127b7ca10d2333d71e6d10aec7a566cf886251f7bc2af253366d7`). The .config hash matches the independent ROUND18 local build byte-for-byte; Image size matches, while its hash differs consistently with the embedded build-time UTS_VERSION timestamp.

**The three earlier watchdog signals are withdrawn:**

1. `updated_at` is a state-transition timestamp, not a heartbeat. The successful run's value stayed at `17:52:57Z` during the build and changed to `18:22:49Z` at completion. Do not use it as a liveness signal.
2. `BlobNotFound` from the job-log endpoint while a job is in progress is not evidence of runner death. Control testing showed the same endpoint returns 404 while running and HTTP 200 only after completion, when GitHub uploads the log blob. A PAT does not provide the browser's live-log WebSocket session.
3. The historical 22–510s failure envelope is not a valid normal-duration baseline: the ten prior failures all exited at cheap pre-build gates (missing `libtinfo.so.5`, exit 127, or the `init_load_uA` CAMELCASE check, exit 1). The first successful run spent 22m28s compiling. A 20-minute timeout heuristic was therefore invalid.

**Correct watchdog rule:** read the current job step's `started_at` and measure elapsed time for that active stage. For the current monolithic step 3, use **50 minutes** as the alert threshold (28m44s observed, with headroom); retain the job's 180-minute hard timeout. Stage-specific budgets should replace the single threshold once the workflow is split. Never infer liveness from `updated_at` or an in-progress log 404.

**Root design defects and prevention:**
- Step 3 combines repo sync, toolchain discovery, patching, validation, Bazel query/cquery, the long Image build and artifact preparation into one opaque step. Split it into nine independently visible stages: preflight/tool installation; repo init/sync; pin ACK/record manifest; discover pinned toolchains; apply patches; style/buildifier/unit tests; Bazel query/cquery; Image build; final config/artifact validation.
- The workflow has no concurrency group. The 18:03:14Z watchdog-recovery push started run `45455279898` only 4m02s into run `45453412267`, creating a duplicate build. Do **not** add `cancel-in-progress: true`: that would have killed the healthy run that later succeeded. A non-cancelling serialization guard (`cancel-in-progress: false`) may be considered with an explicit policy for queued runs; it must not be used to cancel an active valid build.
- Toolchain reporting must resolve the compiler/toolchain actually selected by Kleaf. The prior `find | sort | head -1` reported Clang `clang-3289846` (self-identifies as 3.8.275480) rather than pinned `r584948c`, and Rust `1.91.1.p2` rather than expected `1.91.1.p3`. Mark those old paths as discovery artifacts, not the compiler versions used for the build.

No run was cancelled by the independent verifier. No new build is needed to establish the successful Image result. Run `45455279898` was still in progress at the report's observation cutoff; it is a redundant same-source build, and no action is taken here.


## 2026-11-25 independent runner verification handoff

**Second AI issued a read-only verification taskbook:** `kernel-baseline/round61/AGENT_VERIFICATION_TASKBOOK_SECOND_AI.md`.

The independent Agent report subsequently established that run `45453412267` was alive and completed successfully; the frozen `updated_at` and live-job `BlobNotFound` were normal platform behavior, not stale-run evidence. Run `45455279898` was a duplicate launched by the watchdog-recovery trigger while the first build was healthy. See the corrected Watchdog section above and the independent report. The earlier "unresolved runs / no Image" statements in this handoff are retained only as a record of what was believed before verification and are superseded by the confirmed build result.


### Phase D acceptance-script hardening — block-layer assertion

A static comparison of the storage-first fragment and resolved-config checker found that the fragment explicitly sets `CONFIG_BLOCK=y`, but the checker did not assert it. The Second AI added `BLOCK` to the required symbol list and added a regression test that must fail when the synthetic config disables it.

- Validator commit: `40000bc93ca3b0b480b85607b4d2ca3695c0bfdd`.
- Regression test commit: `d6fac731e9f5b50ee3110873e5d0b365f5e9dd02`.
- Reported acceptance scope is now 32 explicit required symbols and 10 unit tests.
- The test has not yet been re-run by hosted CI after this edit; do not count it as passed until the new validation workflow reports success.
- This edit does not trigger another full Kleaf/Image build. It triggers the lightweight ACK UFS/PHY validation workflow because its test/checker paths changed.


### Phase D acceptance-script hardening — Qualcomm SMMU implementation

A second static review found that generic `ARM_SMMU=y` alone is not enough to prove the Qualcomm apps_smmu driver is included. The fragment documents `ARM_SMMU_QCOM` as a derived `def_tristate y` selected under `ARM_SMMU && ARCH_QCOM`; the validator previously treated its absence as informational. The Second AI promoted `ARM_SMMU_QCOM` to a required =y output and added regression tests for missing and =m cases. The symbol is not forced into the fragment.

- Validator commit: `40e6c909f9d23e0e489fb75d573d36464e7b3215`.
- Regression tests: `4f5adaf6d22f5bf1eca5e30cd711cf545cce7d86`; test newline correction: `055e4b5a51bbfd1c76a04ff15d468f9879c5a7cf`.
- Acceptance scope: 33 explicit required symbols; 11 unit tests.
- The current hosted UFS/PHY validation runs were triggered by these checker/test changes. Their terminal results are pending. These edits do not trigger a full Kleaf/Image build.


### Hosted validation after block-layer checker correction

- Run `45456839358` reached and completed the `Validate Kleaf BUILD syntax and config helper tests` step successfully. This run includes the `CONFIG_BLOCK` required-symbol assertion and its regression test (10-test suite at that revision).
- The run then advanced to `Run authoritative UFS dt_binding_check`; its final result is still pending.
- The subsequent Qualcomm-SMMU validator/test edits are newer than this completed unit-test step. Runs `45457024349`, `45457059231`, and `45457083961` were triggered by those edits; at last inspection they were still fetching the pinned ACK source. Do not claim the new 11-test suite passed until one of those newer runs completes its unit-test step.
- Five UFS/PHY validation runs were created by sequential checker/test commits before this issue was noticed. No run was cancelled. Avoid further pushes touching the workflow's path filters until the current set drains; group any future checker changes into one commit.
- The manifest/Kleaf runner verification remains separately in progress with the independent Agent. No new full Image build was started.


### Updated Phase D validator result

Hosted run `45457083961` at head `055e4b5a51bbfd1c76a04ff15d468f9879c5a7cf` completed the source fetch, immutable identity checks, ordered patch application, strict checkpatch, buildifier and config-helper test steps successfully. The updated **11-test** suite includes:
- rejection when `CONFIG_BLOCK` is unset;
- rejection when `CONFIG_ARM_SMMU_QCOM` is absent;
- rejection when `CONFIG_ARM_SMMU_QCOM=m`.

At last poll, the run had advanced to installing device-tree schema prerequisites; schema validation remained pending. This is source/validator CI only, not a Kleaf .config or Image build.


### Latest UFS / PHY source and schema validation — PASS

Hosted run `45457083961` at `055e4b5a51bbfd1c76a04ff15d468f9879c5a7cf` published `hosted-ufs-validation-latest.md` with Job status success. It revalidated exact ACK source identity, real ordered patch application, diff-check, strict checkpatch, buildifier, the updated 11-test config helper, and the authoritative `make ARCH=arm64 dt_binding_check` step. UFS positive fixtures (2/2), UFS negative fixtures (8/8), PHY positive fixtures (2/2) and PHY negative fixture (1/1) all behaved as expected.

Artifact ID `14951770706`; processed-schema SHA-256 `da994937d63cca2176a5065e8119be7ecd8b45c4939729f1810a8a8f5cc8dc50`; applied diff SHA-256 `b6897118cbef2fe36216d8fa00c22707531b7d6ba6aa5b35417c547185d54b90`.

The schema scanner reports two unrelated malformed upstream YAML files ignored by its scanner; all modified UFS/PHY schema and explicit fixture gates passed. Phase B remains PASS for the current patch set. No actual Kleaf Kconfig resolution or Image compile is implied.


### Archived .config recheck and workflow observability update (2026-11-25)

The original hosted artifact `round61-ack-6.18.33-image-build` (run `45453412267`, artifact `14951184014`) was downloaded and its `dby_w09.config` independently rechecked against the current 33-symbol requirement set. Result: **33/33 =y, no missing symbols, no non-y values, no duplicate assignments**. File size is 238,376 bytes and SHA-256 is `5f7fd8b32a4127b7ca10d2333d71e6d10aec7a566cf886251f7bc2af253366d7`, matching the recorded hosted/local byte-identical config. This closes the pending 33-symbol archived-config recheck without another Image build.

The manifest workflow has been refactored into nine separately visible stages: preflight/dependencies; repo init/sync; ACK pin/manifest record; manifest-pinned JDK/Clang/Rust discovery; ordered patch application; checkpatch/buildifier/unit tests; Bazel query/cquery; Image build; final config/artifact validation. The Image build is now its own Actions step. The workflow uses `concurrency.group: round61-manifest-kleaf-build` with `cancel-in-progress: false` to queue duplicate triggers without cancelling an active valid build. The job hard timeout remains 180 minutes. Operational watchdogs must use the active step `started_at` (50-minute alert threshold for the former monolithic stage), never `updated_at` or an in-progress log 404.

Toolchain discovery now reads `CLANG_VERSION` and `RUSTC_VERSION` from manifest-pinned `build/kernel/build.config.constants` and resolves the exact matching versioned paths, instead of selecting the alphabetically first toolchain directory. The prior `clang-3289846` / Rust `1.91.1.p2` reports are treated as misleading first-on-disk discoveries, not the toolchains selected by Kleaf.

The workflow change is path-filtered away from its own trigger: it listens only to `kernel-baseline/round61/run-manifest-kleaf-build.txt`. This workflow-file and progress-document update does not request a new full Image build.


Workflow correction note: the first refactor commit (`a9f3088f206dc5d2712aae1a3e8be4ac65ab653a`) placed `runner.temp` expressions in job-level `env`, which GitHub rejected before creating any job (run `45462793435`, zero jobs; no build was started). Corrected in `aff63c21a84267301c7d2eafce88db99134cfcd7`: runner-derived paths are now initialized in step 1 and exported through `GITHUB_ENV`. The manifest-build workflow is path-filtered to the explicit trigger marker, so this correction did not start a full build. The corrected workflow now awaits its next intentional marker-triggered validation; do not claim the nine-step workflow has executed successfully until that validation completes.


### Nine-stage workflow validation run — completed at toolchain discovery

The explicit marker update `68ed4de9454a2fcc012264a9c634629dd18465e2` started hosted run `45463060672`. It completed with failure at stage 4/9: stages 1–3 passed, toolchain discovery failed on the incorrect constants-file path, and stages 5–9 were skipped. The exact error and correction are recorded in the following subsection. This was a script path error, not a runner-stall event or a compiler-not-found result.


### Nine-stage workflow retry — toolchain constants path corrected (2026-11-25)

Run `45463060672` completed with failure at stage 4/9. Stages 1–3 passed: runner preflight, immutable manifest sync, and exact ACK tag pin. The stage-4 log shows JDK 11 and Bazel 8.7.0 started successfully, then the script attempted to read `build/kernel/build.config.constants`; that path was not present, and its fallback search was incorrectly limited to `build/kernel`. The subsequent `grep: : No such file or directory` exited 2. Clang/Rust discovery never ran; this is **not** evidence that either compiler is missing. Stages 5–9 were skipped. Failure artifact: `14953212288`.

Second AI verified the correct constants file directly in the exact pinned ACK repository/commit:
- File: `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a:build.config.constants`
- Blob: `cc08dcbb5cbb543fc508dca51d14ad00d2b665b8`
- Values: `CLANG_VERSION=r584948c`, `RUSTC_VERSION=1.91.1.p3`
- Therefore the file's workspace path is `$WORK/common/build.config.constants`; the synchronized manifest separately confirms the Clang and rust-toolchain prebuilt project roots.

The workflow stage 4 is corrected to read `$WORK/common/build.config.constants`, hash the file, assert the two pinned versions expected under this immutable ACK commit, and test the exact manifest prebuilt paths:
- `prebuilts/clang/host/linux-x86/clang-r584948c/bin/clang`
- `prebuilts/rust-toolchain/linux-x86/1.91.1.p3/bin/rustc`

This removes the invalid `build/kernel` constants search and avoids non-deterministic compiler selection. A new explicit marker trigger is queued below to validate the corrected stage and complete the remaining stages. No active run was cancelled.


### Corrected nine-stage retry — Image build in progress (2026-11-25)

Trigger commit `eb37d21224a0878059b0ed5eef72a29cdbd69af9` started run `45529395645`, job `138920645396`. Stages 1–7 have all completed successfully:
- preflight/dependencies/repo launcher;
- immutable manifest sync;
- exact ACK source pin and manifest record;
- manifest-pinned Clang `r584948c` and Rust `1.91.1.p3` discovery with exact executable paths;
- ordered UFS / ROUND63 PHY / Kleaf patch application;
- strict checkpatch, buildifier and all 11 config-helper tests;
- Bazel query/cquery and target output inventory.

Stage 8/9, `Build DBY-W09 Image`, is `in_progress`, started at `2026-11-25T02:03:17Z`. Stage 9/9 final config/artifact validation remains pending. No failed step is reported and no run has been cancelled. The former step-4 constants-file path failure is fixed and has not recurred.


### Follow-up: watchdog-created duplicate Image run also completed

A post-report poll confirmed that the formerly in-progress duplicate run `45455279898` completed successfully at `2026-11-24T18:34:35Z` (job `138662922161`). It uploaded artifact `14951574600` (210,439,547 B). Its completed log independently records:
- `.config`: 238,376 B, SHA-256 `5f7fd8b32a4127b7ca10d2333d71e6d10aec7a566cf886251f7bc2af253366d7` (same archived config as run 45453412267);
- `Image`: 44,820,992 B, SHA-256 `8a90e4fa5bd77ce266e9c095cc8e451815cf10bf27099c6e408e6b865a8747de`.

This is an additional successful Image-build result, but remains the accidental duplicate started by the 18:03Z watchdog push. Its log's manually reported first-on-disk Clang path (`clang-3289846`) is not accepted as proof of the compiler selected by Kleaf. The corrected nine-stage run remains the validation of deterministic, exact-version toolchain discovery.


### Phase E — board DTS and memory/power handoff blocker report committed

Second AI inspected the current board draft and committed `kernel-baseline/round61/phase-e-board-dts-and-memory-handoff.md` (commit `3cb01092277b0750faa534160639fc81bf128b68`). The report preserves the two hard blockers: no evidenced final HOS4.3 ABL-to-Linux memory handoff (or EFI memory-map handoff), and no source-backed physical PM8150 VRM input-parent map. It distinguishes the HOS ARC/proxy graph from physical VRM inputs and records a narrow read-only evidence request for the local Agent. No DTS source input, DTB target, memory address or regulator parent was invented.


### Phase C–E report synchronization (2026-11-25)

The detailed reports have been reconciled with verified evidence:
- `phase-c-kleaf-target-validation.md` now records run `45529395645` stages 2–7 passing, including exact Clang/Rust pin discovery and Bazel query/cquery. Its repeat Image build is tracked separately in Phase D.
- `phase-d-kconfig-and-image-build.md` now corrects the prior stale NOT RUN label: actual Image builds succeeded in runs `45453412267` and `45455279898`; the archived final config passes 33/33 required symbols. The current transparent retry `45529395645` is still compiling at stage 8/9 as of the latest poll; stage 9 remains pending.
- `phase-e-board-dts-and-memory-handoff.md` is now committed and linked above. It documents the actual HOS4.3 final-memory-handoff and PM8150 physical-input-parent evidence required before DTS promotion.

No board DTB/boot package or device operation has been attempted. Phase E/F remain BLOCKED; Phase G remains NOT RUN.


### Phase G — controlled device validation plan prepared

Second AI committed `kernel-baseline/round61/phase-g-device-validation.md` (commit `a8f8d71116d0d3db309e64c0c14b2cb571a20831`). It defines strict entry gates, the pre-boot review packet, first-boot evidence checklist, stop conditions and Stage-A device acceptance criteria. It authorizes no operation: Phase G remains NOT RUN; no device connection, bootloader action, reboot, partition write or hardware test has been performed.
