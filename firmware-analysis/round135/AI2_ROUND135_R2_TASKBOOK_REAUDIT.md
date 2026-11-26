# ROUND135 R2 — AI2 controlled-offset taskbook re-audit

- Reviewer: 2号 AI
- Review date: 2026-11-26
- Review branch: `ai2/round135-controlled-offset-taskbook-audit`
- Governing policy: ROUND132 controlled-offset policy, blob `6712f686da9940937ed87eab2f4b27d44cb29626`
- Audited AI1 branch: `ai1/round130-stagea-ufs-lifecycle-integration`
- Current taskbook blob: `7bb2c2ea1749e0c7b84469472123d498c5823e8c`
- Current R2 start prompt blob: `fc04ecaf99e54562a114c80ee077a6a636cb3878`
- Current 23-patch manifest blob: `6268dd363c08f549e2fd092364adafc65bce93e9`

## 1. Superseding finding

This re-audit supersedes the earlier AI2 taskbook-gap finding in `AI2_ROUND135_TASKBOOK_CONTROLLED_OFFSET_AUDIT.md`, which reviewed the earlier R0/R1 taskbook before Revision 2 existed.

**ROUND135 R2 taskbook and start prompt are ACCEPTABLE for the limited two-tree identity / offset / final-tree preflight.** They are not authorization for downstream schema, DTB, Kconfig, compilation, Image or regression testing.

## 2. Exact source-series corrections confirmed

- The current manifest contains 23 distinct ordered inputs: immutable frozen 17 + ROUND130 patches 18–21 + DTS-only patch 22 + Makefile-only patch 23.
- Patch 22 blob is `ab0108364c835d87ac35ca670347d9d0001a821d`; patch 23 blob is `ceb72ed206d97beb2c2fa8558cb120ee186cb685`.
- The former duplicate UFS driver patch `2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5` is explicitly excluded. The driver implementation is already supplied by frozen patch 5 blob `f1d54e5e0379183fbdfb3ca6132c6d0fc61d4622`.
- The taskbook explicitly says Revision 2 supersedes earlier patch-22/23 identities. The stale R0/R1 descriptions remain historical and must not be followed over Revision 2.

## 3. Controlled-offset and tree-identity gates

R2 now correctly requires:

1. Two independent clean Git clones with separate object stores, indexes, working directories and no shared Git common directory.
2. Exact ACK commit and root tree, clean initial state, and exact verification of all 23 patch blobs / byte sizes / SHA-256 / manifest order.
3. For every patch in each tree: primary `git apply --check --verbose`, actual `git apply --verbose` only after successful check, and `git diff --check`, with raw output and exit codes.
4. Per-patch/per-hunk offset disclosure, with the known ROUND132 patch16/17 and ROUND128 V2 offsets identified by exact patch identity; no zero-offset assumption.
5. Explicit bans on fuzz, ignored whitespace, `--unidiff-zero`, `--3way`, fallback appliers, reduced context, manual edits, rejects, skips and partial application.
6. The two patch-17 intermediate trees must both equal the pre-established `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`.
7. The complete 23-patch resulting content tree must be independently calculated in both trees, including untracked files, and both candidate SHAs must match exactly.
8. The full 23-patch SHA is deliberately not predeclared in R2. R2 only establishes a candidate. AI2 independently verifies raw logs and the candidate; AI1 must then pin that verified SHA in a follow-on taskbook before downstream tests.
9. R2 explicitly stops after upload/readback and forbids schema, dtbs_check, DTB, Kconfig, C object, Kleaf/Image, Host regression, checkpatch and SPDX execution.

This staged procedure is consistent with the controlled-offset policy: no downstream test is authorized until the expected full-series tree SHA has been independently verified and predeclared.

## 4. Minor interpretation note

The taskbook asks any newly observed non-historical nonzero offset to be explicitly reviewed by AI1/AI2. That is a conservative review hold, not a blanket zero-offset gate; it is compatible with the project policy. The executor must preserve the raw output and stop at the R2 boundary for review rather than silently accepting or modifying a patch.

## 5. Current status and next action

- R2 taskbook audit: **PASS — READY FOR LOCAL AGENT PREFLIGHT**.
- R2 Agent execution: **NOT STARTED / no result uploaded in the reviewed handoff**.
- Full 23-patch final Tree SHA: **NOT YET ESTABLISHED**.
- Downstream build/schema/DTB/regression validation: **NOT AUTHORIZED YET**.
- Device / firmware / boot / partition operations: **PROHIBITED**.

The user may now hand the exact `START_PROMPT_R2.md` to the local WorkBuddy Agent. After the Agent uploads the five R2 preflight artifacts and stops, 2号 AI must independently audit the raw logs, patch identities, offsets, both intermediate trees and final 23-patch tree SHA. Only then may 1号 AI pin the SHA and issue a downstream validation taskbook.

No Agent was launched by 2号 AI. No source, patch, DTS, manifest, taskbook, protected branch, firmware or device was modified by this audit.