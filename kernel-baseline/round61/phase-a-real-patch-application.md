# ROUND61 Phase A — real ACK patch application

**Date:** 2026-11-24  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Phase status:** PASS — latest hosted run 45451513173 completed exact-source patch application, diff checks, strict checkpatch, buildifier and config-helper tests  
**Fixed source:** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

## 1. Work performed

1. Read the complete ROUND61 mission, progress log, ROUND59 exact-source integration report, ROUND60 primary review and ROUND62 same-device boot-chain cross-reference.
2. Confirmed source-only patch order:
   - ROUND32
   - corrected ROUND57
   - ROUND36
   - ROUND52-0001
   - ROUND33
   - ROUND52-0002
3. Deliberately excluded ROUND37. It still targets the review-only DTS draft and cannot be applied to ACK source until a real board DTS path and the memory/power evidence gates are established.
4. Added a no-secret GitHub Actions workflow:
   `.github/workflows/round61-ack-ufs-validation.yml`
   It fetches the pinned ACK commit, verifies source blob identities, applies the source patch series in order, runs diff/checkpatch checks and then the authoritative UFS binding check.
5. Diagnosed and corrected the ROUND52-0001 hunk on this branch only. The canonical main patch remains unchanged.
6. The first successful full patch-series runner completed on GitHub-hosted Ubuntu. A later review of its schema log found the `DT_SCHEMA_FILES` separator was wrong, so the schema stage is not accepted yet.

## 2. Execution environment and source identity

The local shell available to this session is a Linux container with 3 logical CPUs, 5.8 GiB visible memory, a 4 GiB cgroup limit, and no `repo` or Bazel. A direct `git ls-remote` attempt against android.googlesource.com failed due to DNS resolution. This local container was not used as an ACK worktree.

The hosted runner fetched:
- ACK commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- `Documentation/devicetree/bindings/ufs/qcom,ufs.yaml`: `1dd41f6d5258014d59c8c8005bc54f7994351a52`
- `Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml`: `962dffcd28b44b3489be5615c75e7270a0c45dc4`
- `drivers/ufs/host/ufs-qcom.c`: `a80c6998406dbc88c25dbd9977699ba481207efe`
- `drivers/ufs/host/ufs-qcom.h`: `5f979daabd5323184eeee137cc8ecc076193979e`

All four source blob assertions passed.

## 3. ROUND52-0001 diagnosis and branch-local correction

The canonical main patch blob is preserved:
- `kernel-baseline/round52/0001-dt-bindings-ufs-vddp-vccq-parent-supplies.patch.draft`
- blob `c0ac84067a900022a077c748b7abb10345f1295f`

Real Git rejected its second hunk at line 64, although the first property hunk applied. Diagnostic output showed the short context around `allOf` visually matched. A ROUND61-local candidate was created:
- `kernel-baseline/round61/patches/round52-0001-context-corrected.patch`
- blob `6ab8411cd1bec6675e412633093b9b7d74dbce58`

It preserves the original semantics and adds the next existing `  - if:` line as trailing context, updating the hunk count from 3/16 to 4/17. This candidate is now confirmed to pass real `git apply --check` and `git apply` in the ordered series. No change was made to main or the canonical patch.

## 4. Real source patch application — PASS

Runner:
[45431820876](https://github.com/hhdy/matepad11-dby-w09-agent-reports/actions/runs/45431820876)

The runner fetched the exact ACK commit and checked all four immutable source blobs before patching. It then ran `git apply --check`, `git apply`, and `git diff --check` for every patch in order:

| Patch | Check | Apply | Result |
|---|---:|---:|---|
| ROUND32 | 0 | 0 | PASS |
| ROUND57 | 0 | 0 | PASS |
| ROUND36 | 0 | 0 | PASS |
| ROUND52-0001 ROUND61-local corrected copy | 0 | 0 | PASS |
| ROUND33 | 0 | 0 | PASS |
| ROUND52-0002 | 0 | 0 | PASS |

The final `git diff --check` also returned 0. The resulting source diff contained:
- `qcom,ufs-common.yaml`: 17 additions / 1 deletion
- `qcom,ufs.yaml`: 61 additions
- `ufs-qcom.c`: driver additions
- `ufs-qcom.h`: host state additions

The runner printed the complete resulting diff. SHA-256 of the binary diff:
`e52f213856caac061a403da922ca1675386db317791d9ed022e8c19acee75139`.

This is real patch application evidence on a disposable hosted-runner checkout. It is not a kernel compile or runtime test.

## 5. Schema validation — NOT YET ACCEPTED

Runner `45431820876` completed its `make ARCH=arm64 dt_binding_check` step with exit 0, but review of the log found that the invocation did **not** actually select the requested UFS files.

The ACK `Documentation/devicetree/bindings/Makefile` constructs its filter using:

```make
$(subst :," -e ",$(DT_SCHEMA_FILES))
```

Therefore `DT_SCHEMA_FILES` must be colon-separated, not space-separated. The initial workflow passed a space-separated string. The observed log showed:
- `SCHEMA Documentation/devicetree/bindings/processed-schema.json` was generated;
- `CHKDT` / `LINT` were invoked with an empty file list;
- `yamllint` printed its usage error because it received no files;
- the ACK Makefile uses `|| true` for these helper commands, so the target's exit 0 is not proof that the selected schemas were checked.

Accordingly:
- This run is **not** counted as a UFS `dt_binding_check` PASS.
- No schema correctness conclusion is drawn from the generated all-tree processed-schema file alone.
- The workflow has been corrected to use a colon-separated `DT_SCHEMA_FILES` value and to invoke `dt-doc-validate -u Documentation/devicetree/bindings` directly on both modified UFS schema files. It also asserts that processed-schema output exists and lists the generated UFS example DTBs.

The corrected workflow still needs a new run before Phase B can be accepted.

## 6. Checkpatch status

The first strict checkpatch attempt on ROUND33 failed for these reasons:
- ERROR: missing Signed-off-by line. These are unsigned draft patches with no confirmed human sign-off identity; no sign-off is fabricated.
- WARNING: one commit-description line exceeds 75 columns.
- CHECK: the continuation indentation for `ufs_qcom_validate_required_opp()` does not align with the opening parenthesis.

The no-signoff strict run [45432489540](https://github.com/hhdy/matepad11-dby-w09-agent-reports/actions/runs/45432489540) produced:
- ROUND33: 0 errors, 1 warning (75-column commit-description line), 1 CHECK (continuation alignment), exit 1.
- ROUND52-0002: 0 errors, 1 warning (75-column commit-description line), 2 CHECKs (continuation alignment in `of_property_read_u32()` and `devm_regulator_get()`), exit 1.

Two branch-local cleaned copies have been created:
- `kernel-baseline/round61/patches/round33-checkpatch-clean.patch`: wraps the long commit-description line and corrects the function continuation indentation.
- `kernel-baseline/round61/patches/round52-0002-checkpatch-clean.patch`: wraps the long commit-description lines and aligns both continuation arguments with their opening parentheses.

The workflow now applies and checks these branch-local copies. The changes are formatting/patch-message only; they do not alter driver logic. The next run must confirm both copies still apply and that `--no-signoff --strict` exits 0. The canonical main drafts remain unchanged.

## 7. Remaining gates

- [x] Fetch exact ACK commit on a hosted runner.
- [x] Verify four immutable source blob identities.
- [x] Apply all six source patches in order using real Git, using the ROUND61-local corrected ROUND52-0001 copy.
- [x] Final `git diff --check`.
- [ ] Strict checkpatch for ROUND33 and ROUND52-0002.
- [ ] Correctly filtered and directly validated `dt_binding_check`.
- [ ] Positive/negative DT-schema fixtures.
- [ ] Kleaf BUILD patch real apply, buildifier, Bazel query/cquery.
- [ ] Actual final Kconfig and Image build.

## 8. Next action

Run the latest workflow revision from a fresh pinned ACK checkout. Inspect strict checkpatch output and the corrected colon-filtered UFS schema validation. Then add positive/negative fixtures for SM8250 clock counts, power-domain limits and supply/load pairing. Only after these gates pass should Phase C proceed. Keep ROUND37 excluded until Phase E legitimately migrates the board DTS.


## 2026-11-24 follow-up — superseding evidence

The earlier section describing a six-patch application is superseded by the actual schema-driven sequence below.

### Source patch sequence used by the passing runner

The hosted runner `45435020774` successfully applied:
1. ROUND32
2. ROUND36
3. ROUND52-0001 ROUND61-local corrected copy
4. ROUND33 ROUND61-local checkpatch-clean copy
5. ROUND52-0002 ROUND61-local checkpatch-clean copy

ROUND57 was intentionally not applied. ACK dt-schema rejected its redundant `minItems/maxItems` constraints when combined with the fixed eight-entry `clock-names.items` list. ROUND32 already defines the eight ordered const items. The exact 8-entry constraint still needs explicit 7/8/9 negative/positive DT fixtures before this design is accepted.

### ROUND52-0001 schema correction

The branch-local copy also removes four invalid explicit `$ref` declarations from standard `*-supply` and `*-microamp` properties. The qcom,ice phandle reference in the original context is retained. The corrected patch applies cleanly; canonical main remains unchanged.

### Kleaf target and validator

The ROUND58 target patch and storage-first fragment apply cleanly. The branch-local target patch was updated with the one blank line required by buildifier. The hosted runner's auto-format diagnostic showed that was the only BUILD.bazel formatting change. The nine config-helper unit tests passed. A subsequent workflow revision now runs `buildifier -mode=check` without auto-fixing the temporary source tree.

### Latest schema evidence

The colon-filtered `dt_binding_check` run generated the processed schema and both UFS example DTBs; direct `dt-doc-validate` and `yamllint` passed. However, the example validation emitted real errors:
- `qcom,ufs.example.dtb`: `power-domains` too short.
- `unevaluatedProperties` rejects common UFS properties (interrupts, iommus, phys/phy-names, resets and regulator supplies).

The upstream make target did not propagate these example diagnostics as a nonzero exit, so Phase B is **NOT PASS**. The next workflow must invoke `dt-validate` directly on the generated examples and fail on these diagnostics. Do not suppress or work around them by weakening schema constraints.

### Phase status

- Source patch application: PASS on hosted runner.
- Driver checkpatch: PASS (draft sign-off intentionally not fabricated).
- Kleaf patch application: PASS.
- Buildifier: the formatted temporary BUILD file passed; the corrected branch patch still requires the new non-auto-fixing check run.
- Config helper tests: 9/9 PASS.
- UFS schema documentation lint: PASS.
- UFS example schema validation: FAIL / unresolved.
- Bazel query, final Kconfig, kernel Image, DTB/boot image and device boot: NOT_RUN.
- Phase E remains blocked on trusted HOS4.3 FDT/EFI memory handoff and board-specific PM8150 rail evidence, as detailed in `phase-e-board-dts-memory-power-gates.md`.


## Superseding schema ownership decision — ROUND32 skipped

The fixed ACK source already has `qcom,sc7180-ufshc.yaml` selecting `qcom,sm8250-ufshc` and defining the eight-clock SM8250 branch. Applying the ROUND32 draft would add the same compatible to `qcom,ufs.yaml`, creating duplicate schema selection. The current UFS validation and manifest build workflows therefore skip ROUND32; its canonical draft is unchanged. ROUND57 is also skipped because the existing fixed eight-item tuple already constrains the SM8250 clock-name count and the ACK meta-schema rejects redundant min/max tuple constraints.

ROUND52-0001's branch-local implementation is now placed in the shared `qcom,ufs-common.yaml` schema, so the properties are visible to the actual SM8250 binding (`qcom,sc7180-ufshc.yaml`) as well as the generic Qualcomm UFS binding. This patch applies after ROUND36. The canonical ROUND52 patch remains unchanged.


## Final source/style gate confirmation

Hosted run `45451513173` re-applied the ordered UFS, ROUND63 PHY and Kleaf patches to the exact ACK commit with real `git apply --check` / `git apply`, verified the pristine source identity, and passed `git diff --check`, strict checkpatch, buildifier and all 9 config-helper tests. The only checkpatch ignore is the narrowly scoped `CAMELCASE` false positive for the existing API field `init_load_uA`; all other strict checks remain active. Phase A is PASS.


## 2026-11-25 re-validation with deterministic manifest workflow

Run `45529395645`, job `138920645396`, independently repeated the source and style gates using the nine-stage workflow. Stages 2–5 passed: immutable manifest sync, exact ACK pin, exact manifest-pinned toolchain discovery, and real ordered patch application. Stage 6 passed strict checkpatch, `buildifier -mode=check`, and the hardened 11-test config-helper suite. Thus the current patch series and check suite are revalidated immediately before the separate Image build stage. The toolchain constants path in this run is `$WORK/common/build.config.constants`, yielding Clang `r584948c` and Rust `1.91.1.p3`; the prior failed attempt searched under the wrong repo subdirectory and did not reach compiler discovery.