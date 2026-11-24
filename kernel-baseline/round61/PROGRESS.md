# ROUND61 Continuous Stage-A Port — Progress Log

**Owner:** Second GitHub-connected AI  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Mission:** `kernel-baseline/round61/ROUND61_LONG_RUNNING_STAGEA_MISSION.md`  
**Fixed ACK:** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

## Current overall state

**STAGE_A_SOURCE_PATCHES_APPLIED — UFS driver/style checks pass; Kleaf candidate and validator tests pass in the hosted runner; UFS example schema validation still reports errors; no kernel Image or device boot exists.**

| Phase | Current state | Evidence / exit gate |
|---|---|---|
| A — real Git patch application | PASS with branch-local corrections | Run 45435020774: exact ACK fetch/blob checks; ROUND32, ROUND36, corrected ROUND52-0001, cleaned ROUND33 and cleaned ROUND52-0002 applied; ROUND57 intentionally skipped as redundant/invalid; final diff-check pass |
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
