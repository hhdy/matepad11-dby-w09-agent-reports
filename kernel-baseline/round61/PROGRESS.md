# ROUND61 Continuous Stage-A Port — Progress Log

**Owner:** Second GitHub-connected AI  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Mission:** `kernel-baseline/round61/ROUND61_LONG_RUNNING_STAGEA_MISSION.md`  
**Fixed ACK:** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

## Current overall state

**PHASE A SOURCE PATCHES PASS — exact ACK apply, diff-check, ROUND63 PHY integration and strict checkpatch now pass in hosted run 83; ROUND58 Kleaf patch/buildifier/config-helper tests pass; Phase B schema fixtures and manifest-pinned Bazel/Image build are still running. No Image or device boot is yet evidenced.**

| Phase | Current state | Evidence / exit gate |
|---|---|---|
| A — real Git patch application | PASS | Hosted run 45443538190: fixed ACK commit verified; UFS series, ROUND63 binding/driver and ROUND58 Kleaf patches applied; git diff --check and strict checkpatch passed. ROUND57 is superseded by ROUND32's fixed eight-item list because ACK dt-schema rejects redundant min/max constraints |
| B — UFS binding validation | PARTIAL / BLOCKED | Schema docs and yamllint pass; generated example DTBs exist; qcom,ufs.example.dtb still reports power-domains too short and unevaluatedProperties errors. ACK Makefile returns success despite those example diagnostics; do not mark Phase B PASS |
| C — Kleaf target validation | PARTIAL | ROUND58 patch applies; buildifier auto-format showed only one missing blank line, now fixed in branch-local patch; current workflow revision requires clean buildifier check. 9 config-validator unit tests pass. No Bazel query/cquery because full manifest workspace and locked build/kernel dependency are unavailable |
| D — final Kconfig + Image build | NOT_RUN | No manifest-pinned Kleaf workspace, actual .config, or Image build |
| E — board DTS + memory/power handoff | BLOCKED | See `phase-e-board-dts-memory-power-gates.md`; no trusted final HOS4.3 FDT RAM map or PM8150 physical supply-parent facts |
| F — boot image / ramdisk / AVB | BLOCKED | ROUND62 cross-reference reviewed; local HOS4.3 partition, AVB and ABL RAM-boot evidence remains unavailable |
| G — device validation | NOT_RUN | No approved boot plan or hardware test |

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

1. Run the latest workflow revision with the corrected ROUND58 patch and non-auto-fixing buildifier check.
2. Fix the qcom,ufs example validation errors at the schema-composition level, then add positive/negative fixtures for 7/8/9 clocks, one/two/three power domains, non-SM8250 domain count, and supply/load pairing.
3. Archive the final applied diff and validation logs.
4. Only then proceed to Kleaf workspace/Bazel query and Kconfig/Image build once the manifest-pinned `build/kernel` workspace is available.
5. Keep ROUND37 excluded until Phase E evidence is supplied. Do not start DerpFest Stage B.


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
