# ROUND61 Phase A — real ACK patch application

**Date:** 2026-11-24  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Phase status:** SOURCE PATCH APPLICATION PASS with a ROUND61-local ROUND52-0001 correction; checkpatch pending; Phase B command is being corrected after a false-positive run  
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

The first successful patch-application run predates the strict checkpatch step. The workflow has now been updated to run:

```sh
perl scripts/checkpatch.pl --no-tree --strict < ROUND33 patch
perl scripts/checkpatch.pl --no-tree --strict < ROUND52-0002 patch
```

Those checks have not yet run on a completed workflow revision. Do not mark checkpatch PASS until its output and exit code are inspected.

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
