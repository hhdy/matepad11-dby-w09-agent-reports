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
