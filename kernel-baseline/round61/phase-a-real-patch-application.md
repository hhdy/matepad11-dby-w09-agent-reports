# ROUND61 Phase A — real ACK patch application

**Date:** 2026-11-24  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Phase status:** PARTIAL / BLOCKED — first three patches apply; ROUND52-0001 original hunk fails; a branch-local context-strengthened candidate is queued for validation  
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
5. The workflow ran repeatedly on GitHub-hosted Ubuntu runners. The source fetch and exact blob checks succeeded; the original ROUND52-0001 hunk failed consistently.

## 2. Execution environment and source identity

The local shell available to this session is a Linux container with 3 logical CPUs, 5.8 GiB visible memory, a 4 GiB cgroup limit, and no `repo` or Bazel. A direct `git ls-remote` attempt against android.googlesource.com failed due to DNS resolution. This local container was not used as an ACK worktree.

The hosted runner successfully fetched:
- ACK commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- `Documentation/devicetree/bindings/ufs/qcom,ufs.yaml`: `1dd41f6d5258014d59c8c8005bc54f7994351a52`
- `Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml`: `962dffcd28b44b3489be5615c75e7270a0c45dc4`
- `drivers/ufs/host/ufs-qcom.c`: `a80c6998406dbc88c25dbd9977699ba481207efe`
- `drivers/ufs/host/ufs-qcom.h`: `5f979daabd5323184eeee137cc8ecc076193979e`

All four source blob assertions passed in each completed runner attempt.

## 3. Real Git application results for the canonical source series

Initial runner: [45430859807](https://github.com/hhdy/matepad11-dby-w09-agent-reports/actions/runs/45430859807)  
Repeat runner: [45430957517](https://github.com/hhdy/matepad11-dby-w09-agent-reports/actions/runs/45430957517)  
Diagnostic runner: [45431553772](https://github.com/hhdy/matepad11-dby-w09-agent-reports/actions/runs/45431553772)

| Patch | `git apply --check` | `git apply` | Result |
|---|---:|---:|---|
| ROUND32 | 0 | 0 | PASS |
| ROUND57 | 0 | 0 | PASS |
| ROUND36 | 0 | 0 | PASS |
| ROUND52-0001 canonical | 1 | NOT_RUN | FAIL — hunk 2 near line 64 |
| ROUND33 | NOT_RUN | NOT_RUN | BLOCKED |
| ROUND52-0002 | NOT_RUN | NOT_RUN | BLOCKED |

Exact failure:

```
error: patch failed: Documentation/devicetree/bindings/ufs/qcom,ufs.yaml:64
error: patch does not apply
```

The runner used `set -euo pipefail`; this is not a hidden pipeline failure. `git apply --reject --verbose` confirmed:
- ROUND52-0001 hunk 1 (the VDDP/VCCQ-parent property declarations) applies cleanly.
- ROUND52-0001 hunk 2 (the `allOf` supply/load required-property conditions) is rejected.

The diagnostic runner printed the exact lines:
- line 64: `allOf:`
- line 65: `  - $ref: qcom,ufs-common.yaml`
- line 66: empty line
- line 67: `  - if:`

It also ran `sed -n '62,68l'`; the source showed no hidden trailing whitespace around this context. The rejected hunk's raw bytes show the three expected old context lines are `allOf:`, the common-schema ref, and one empty line. Thus the failure is not explained by an obvious visible whitespace mismatch. The exact reason Git rejects this short hunk remains under investigation.

## 4. ROUND61-local corrective candidate

The canonical main patch is preserved unchanged:
- Original patch blob: `c0ac84067a900022a077c748b7abb10345f1295f`

A branch-local candidate was created at:
`kernel-baseline/round61/patches/round52-0001-context-corrected.patch`

Candidate blob:
`6ab8411cd1bec6675e412633093b9b7d74dbce58`

The candidate preserves the original property hunk and supply/load semantics. It strengthens the second hunk with the following existing `  - if:` line as trailing context and updates the hunk counts from 3/16 to 4/17. It does not change schema behavior. The workflow has been updated to test this candidate instead of the canonical main draft.

**This candidate has not yet passed real `git apply --check`.** It is an experiment to test whether a stronger context anchor resolves the Git application issue, not yet an accepted correction. The next workflow run must start from a fresh ACK checkout and validate it.

## 5. Schema/checkpatch status

Because the complete patch series has not yet applied:
- ROUND33 and ROUND52-0002 remain NOT_RUN.
- Driver `checkpatch.pl --strict` remains NOT_RUN.
- The authoritative kernel `dt_binding_check` remains NOT_RUN.
- No schema PASS is claimed.

The prior ROUND59 16/16 in-memory hunk simulation remains historical static evidence only and is superseded for the failing hunk by the actual Git result.

## 6. Remaining Phase A gates

- [x] Fetch exact ACK commit on a hosted runner.
- [x] Verify four immutable source blob identities.
- [x] Real `git apply --check` and apply for ROUND32, ROUND57 and ROUND36.
- [ ] Validate the ROUND61-local ROUND52-0001 candidate.
- [ ] Real apply for ROUND33 and ROUND52-0002.
- [ ] Final `git diff --check`.
- [ ] `scripts/checkpatch.pl --strict` for both driver patches.
- [ ] Archive resulting source diff and hashes.

## 7. Next action

Inspect the next workflow run for the branch-local corrected hunk. If it applies, continue the full ordered source series and then run checkpatch plus authoritative `dt_binding_check`. If it still fails, stop patch-series advancement and isolate the hunk with a minimal independent Git fixture; do not force-apply or edit the canonical main artifact. Keep ROUND37 excluded until Phase E legitimately migrates the board DTS.
