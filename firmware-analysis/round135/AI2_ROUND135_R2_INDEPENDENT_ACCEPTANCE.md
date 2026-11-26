# ROUND135 R2 — AI2 Independent Preflight Audit

Date: 2026-11-26
Repository: hhdy/matepad11-dby-w09-agent-reports
Executor: user-local WorkBuddy Agent (parallel session upload)
Reviewer: AI2 (independent evidence review; no local Agent execution)

## Verdict

**PASS — R2 candidate tree established.** This accepts only the exact 23-patch content-tree identity for the next authorization step. It does not authorize schema/DTB/Kconfig/compile/Image/Host testing. AI1 must pin the verified candidate SHA in a follow-on taskbook before downstream validation.

Candidate full 23-patch content tree:

`afe9517f8062b96bfeb5b4dd5714942861e6a44b`

Tree A and Tree B report this exact value independently. The 17-patch intermediate tree in both is `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`, matching the previously established ROUND132 value.

## Evidence reviewed

R2 deliverables on `firmware-audit-v1`, directory `firmware-analysis/round135/r2-preflight/`:

- Final report blob `2d8b006482b4542e6018e27afbe8b4d8fbeed5d8`.
- Tree A raw log blob `6fe70593091d0aaed0478b8b5bb100d1479c1b7f`.
- Tree B raw log blob `87c7119c687448b1f1336f120a437ec15d8bba6d`.
- Tree-equivalence/offset log blob `1a191291963d0e78c2138332fb639e5232d9d687`.
- Upload/readback log blob `f03511589fba658a503fcb11efb6365396ff8a42`.

All five files were fetched from GitHub and are non-empty. The upload/readback record reports byte-identical readback for all five deliverables, including the corrected final versions of the Tree A and Tree B logs.

## Independent checks

1. Fixed base: both trees report ACK `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`, root tree `790a68ae6d4f4ac51ab2d88977b6fd5c031473b7`, clean starting status, and no alternates.
2. Independence: Tree A and Tree B have distinct gitdirs; Tree B was made with `git clone --no-hardlinks` from Tree A, which the R2 taskbook explicitly permits. The log records different pack inodes and no alternates/shared object directory.
3. Patch identities: both raw logs contain 23 identity records and their blob/SHA-256/size tuples match each other in order. I independently fetched the authoritative frozen manifest blob `9a93b7e3a500d807533517a92b98fe244b2ea456` and the ROUND135 extension manifest blob `6268dd363c08f549e2fd092364adafc65bce93e9`; the 17 frozen patch blob/SHA entries and six extension patch blob entries in the logs match the authoritative manifest entries. Patch 22 is DTS-only; patch 23 is Makefile-only. The former duplicate driver patch is not part of the series; the driver implementation is in frozen patch 5.
4. Apply gates: each tree records `git apply --check --verbose`, actual `git apply --verbose`, and `git diff --check` for all 23 patches. The reported per-patch results are RC=0 throughout; no failed hunk, reject, fuzz, partial application, or fallback applier is reported.
5. Controlled offsets: both trees reproduce exactly the historical offsets: patch 16 H1 -25/H2 -2/H3 +2; patch 17 H1 +1/H2 -2; patch 20 H3 -19. No additional offset line is reported. These are accepted under the controlled-offset policy, not treated as zero-offset.
6. Tree calculation: both logs use a temporary index (`read-tree HEAD`, `add -A`, `write-tree`) to include modified and untracked content without relying on an unchanged unstaged main index. Both 17-stage trees match `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`; both final 23-stage trees match `afe9517f8062b96bfeb5b4dd5714942861e6a44b`. Changed-path sets and final diff-check results match.
7. Scope: the report explicitly states that schema, dtbs_check, DTB build/decompile, Kconfig, object compile, Image build, Host regressions, checkpatch and SPDX were NOT RUN, consistent with the R2 stop condition.

## Manifest snapshot discrepancy — reviewed and resolved

Tree A's prep log records `FROZEN_MANIFEST_BLOB_MISMATCH`: it read a local snapshot with blob `96b52a4fdbc1f63023ec1fbfc9aec12b8176cfdb`, not the authoritative pinned blob `9a93b7e3a500d807533517a92b98fe244b2ea456`. I fetched both GitHub revisions independently and compared their contents. The only differences are the trailing annotations on frozen patches 16 and 17: the older snapshot says `pending-local-apply-check`; the authoritative pinned manifest says `PASS: 17-patch final revalidation 2026-11-25`. Both revisions carry the exact same 17 patch paths, Git blob IDs and SHA-256 values. I therefore verified the Agent's 17 patch identity records against the authoritative pinned manifest, rather than accepting the stale local snapshot as authority. This is a disclosed provenance/process discrepancy, not a patch identity mismatch, and it does not change the resulting content tree.

## Disposition and next gate

R2 is accepted as **PASS — PREFLIGHT CANDIDATE ESTABLISHED**. The full 23-patch candidate tree SHA is independently verified as `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.

AI1 must now publish a follow-on taskbook that pins this exact SHA as the expected full 23-patch tree before authorizing any downstream validation. Until that taskbook exists, do not run dt_binding_check, dtbs_check, board DTB build/decompile, Kconfig, UFS object compile, Kleaf/Image build, Host regressions, checkpatch or SPDX.

No hardware/device/USB/ADB/fastboot/recovery/serial/partition/firmware action occurred or is authorized by this acceptance. Phase E/F blockers remain separate; this R2 result is not a claim of successful device boot or completed kernel port.