# ROUND61 Phase A — real ACK patch application

**Date:** 2026-11-24  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Phase status:** PARTIAL / BLOCKED — first three patches apply; ROUND52-0001 fails and is under diagnosis  
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
5. The workflow has run twice on GitHub-hosted Ubuntu runners. Both runs fetched the exact source and reproduced the same real Git patch failure.

## 2. Execution environment and source identity

The local shell available to this session is a Linux container with 3 logical CPUs, 5.8 GiB visible memory, a 4 GiB cgroup limit, and no `repo` or Bazel. A direct `git ls-remote` attempt against android.googlesource.com failed due to DNS resolution. This local container was not used as an ACK worktree.

The hosted runner successfully fetched:
- ACK commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- `Documentation/devicetree/bindings/ufs/qcom,ufs.yaml`: `1dd41f6d5258014d59c8c8005bc54f7994351a52`
- `Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml`: `962dffcd28b44b3489be5615c75e7270a0c45dc4`
- `drivers/ufs/host/ufs-qcom.c`: `a80c6998406dbc88c25dbd9977699ba481207efe`
- `drivers/ufs/host/ufs-qcom.h`: `5f979daabd5323184eeee137cc8ecc076193979e`

All four source blob assertions passed in both runs.

## 3. Real Git application results

Workflow runs:
- Run 1: [45430859807](https://github.com/hhdy/matepad11-dby-w09-agent-reports/actions/runs/45430859807)
- Run 2: [45430957517](https://github.com/hhdy/matepad11-dby-w09-agent-reports/actions/runs/45430957517)

Both runners performed a real fetch/checkout of the immutable ACK commit. Both produced the following results:

| Patch | `git apply --check` | `git apply` | Result |
|---|---:|---:|---|
| ROUND32 | 0 | 0 | PASS |
| ROUND57 | 0 | 0 | PASS |
| ROUND36 | 0 | 0 | PASS |
| ROUND52-0001 | 1 | NOT_RUN | FAIL — qcom,ufs.yaml hunk near line 64 |
| ROUND33 | NOT_RUN | NOT_RUN | BLOCKED by prior patch failure |
| ROUND52-0002 | NOT_RUN | NOT_RUN | BLOCKED by prior patch failure |

Exact failure:

```
error: patch failed: Documentation/devicetree/bindings/ufs/qcom,ufs.yaml:64
error: Documentation/devicetree/bindings/ufs/qcom,ufs.yaml: patch does not apply
```

The runner used `set -euo pipefail`; the failure was not hidden by logging. The authoritative `dt_binding_check` and checkpatch steps were skipped because the patch series did not reach a valid fully applied state.

The prior ROUND59 result (16/16 in-memory hunks) remains static simulation evidence and is superseded for this hunk by the real Git failure. No source patch has been silently modified or skipped to force a green result.

## 4. Current diagnosis

The failing artifact is:
`kernel-baseline/round52/0001-dt-bindings-ufs-vddp-vccq-parent-supplies.patch.draft`
(blob `c0ac84067a900022a077c748b7abb10345f1295f` on main).

The failure occurs in the same file modified by ROUND32 and ROUND57. The first ROUND52-0001 hunk adds VDDP/VCCQ-parent properties after `qcom,ice`; its second hunk adds supply/load pairing conditions under `allOf`. The workflow has been amended to print the post-prior-patch file with line numbers and use `git apply --reject --verbose` to expose the exact rejected hunk. That diagnostic workflow revision is committed on this branch; its next run is pending.

Do not guess a hunk line-number change until the rejected context is inspected. If the existing patch is defective, create a corrected ROUND61 branch-local copy and preserve the canonical main draft and its blob identity unchanged.

## 5. Remaining Phase A gates

- [x] Fetch exact ACK commit on a hosted runner.
- [x] Verify four immutable source blob identities.
- [x] Real `git apply --check` and apply for ROUND32, ROUND57 and ROUND36.
- [ ] Diagnose and correct ROUND52-0001 without modifying main.
- [ ] Real `git apply --check` and apply for ROUND52-0001, ROUND33 and ROUND52-0002.
- [ ] Final `git diff --check`.
- [ ] `scripts/checkpatch.pl --strict` for both driver patches.
- [ ] Archive resulting source diff and hashes.

## 6. Next action

Inspect the diagnostic workflow output for the rejected ROUND52-0001 hunk, then make the smallest evidence-based correction on `ai-parallel/stagea-port-until-boot`. Rerun the entire ordered patch sequence from a fresh pristine ACK checkout. Only after all six source patches apply should Phase B begin. Keep ROUND37 excluded until Phase E legitimately migrates the board DTS.
