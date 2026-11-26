# ROUND132 — controlled hunk-offset acceptance decision (1号 AI)

- Decision owner / independent reviewer: 1号 AI (ChatGPT)
- Authorization: user explicitly asked 1号 AI to decide whether ROUND132 must fail on any offset or whether the acceptance standard may allow documented offsets with exact resulting-tree verification.
- Scope: ROUND132 exact seam-v2 validation and the project's subsequent patch-series validation policy. This decision does not alter any source patch, frozen manifest, AI2 branch or historical log.

## 1. Decision

**Adopt option 2: controlled, fully disclosed hunk offsets are permitted.**

A zero-offset rule is not required as a universal acceptance condition. An offset is a reported hunk-placement fact, not automatically a patch failure. It must not be hidden, normalized to zero or described as "no offset." It is acceptable only when the exact-input, exact-application and exact-result gates below all pass.

This decision supersedes the blanket zero-offset gate in the original ROUND132 taskbook for adjudicating the already-executed ROUND132 evidence. It does not erase that original taskbook requirement or alter its historical record. The reason for changing the rule is to prioritize deterministic source-tree identity over incidental line-number drift, while preserving stronger controls against patch misapplication.

## 2. Controlled-offset acceptance criteria

Every patch series using this rule must satisfy all of the following:

1. **Exact base:** checkout commit, tree and initial clean worktree are recorded and match the fixed baseline.
2. **Exact inputs:** each patch's Git blob / SHA-256 / byte size and the manifest order match the predeclared immutable manifest. No substitution, regeneration, edit, omission or reordering is allowed.
3. **Successful application:** for each patch, `git apply --check` and the actual `git apply` both return 0. No failed hunk, reject file, partial application, skipped patch, or conflict is allowed.
4. **Offset disclosure:** every offset printed by the primary check/apply commands is recorded per patch and per hunk. The report must not claim zero offset if any nonzero offset exists. The offset pattern must be reproducible in independent clean trees. Tool-specific secondary diagnostics (for example GNU `patch --dry-run`) must be labelled as secondary and must not be mixed with the primary applier result.
5. **No fuzz / no context relaxation:** no hunk may be applied by dropping or relaxing its required context, ignoring whitespace, using `--unidiff-zero`, or using a fallback/reject/three-way repair path. Any evidence of context relaxation or fuzzy application is a failure, not an allowable offset.
6. **Predeclared resulting-tree identity:** before test execution, the source note or manifest must declare the expected post-series content-tree SHA. Each of at least two independently created clean trees must produce that exact same tree SHA after the full series. The expected SHA may not be chosen or edited after seeing the test results.
7. **Clean result:** `git diff --check` passes; the resulting worktree/index contains exactly the expected changes and no unexplained files or edits.
8. **Independent review:** the reviewer checks the raw logs, not only the summary flags. If the raw output contradicts a summary count or conclusion, the report must be corrected by an addendum before final acceptance.

If there is no independently predeclared expected tree SHA, any nonzero offset remains a review blocker until an independently reproducible expected tree is established. An offset must never be waived merely because `git apply` returned 0.

## 3. ROUND132 raw evidence against the revised standard

### 3.1 Frozen 17-patch replay

Fixed ACK: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`.

Manifest blob: `9a93b7e3a500d807533517a92b98fe244b2ea456`; all 17 patch blobs, SHA-256 values and order are reported as matching.

The pre-test AI2 source note (blob `f1f45eed1a808a8296460d6c7c9ea1c542565c74`) declares the reproducible patch-base tree:
`77e2b2b1515b3813f7538aedffe4c5a4e90edb57`.

The raw `round132-v2-apply-check.log` (blob `faee9bc0b98fcd9b86a6264f327c550a3f57ca7f`) records these primary `git apply --check --verbose` and `git apply --verbose` offsets in **both** independent clean trees:

| Patch | Hunk | Offset | Tree A | Tree B |
|---:|---:|---:|---|---|
| 16 | 1 | -25 lines | same | same |
| 16 | 2 | -2 lines | same | same |
| 16 | 3 | +2 lines | same | same |
| 17 | 1 | +1 line | same | same |
| 17 | 2 | -2 lines | same | same |

All other frozen patches have no nonzero offset recorded by the primary applier. Every primary check/apply exit code is 0, all 17 patches apply, and no failed hunk/reject is recorded by the primary applier.

The independently created trees both produce:
`77e2b2b1515b3813f7538aedffe4c5a4e90edb57`

This exactly equals the predeclared source-note tree. Both trees also pass `git diff --check`. Therefore the frozen 17-patch replay **passes under the controlled-offset standard**. The old log's summary fields `GIT_APPLY_OFFSET_COUNT=0` and statements that git apply has no offset mechanism are inaccurate and must not be repeated. The correct offset count is five nonzero hunk placements per tree (the same five hunk offsets are observed in each tree).

The GNU `patch --dry-run --fuzz=0` diagnostics in the same log are secondary diagnostics and produce failures for some patches. They are not the primary application path and do not alter the result-tree identity. Their output must remain disclosed, not discarded.

### 3.2 seam-v2 patch

The unique seam-v2 patch identity matches:
- Git blob `890b584b6015293c145c221219591f4d98129671`
- SHA-256 `1fbc32a362dc5d2f694ba45798a90c2e0efbe389bc245aa101e16d85d7ee842f`
- 16,797 bytes.

It applies in Tree B with `git apply --check` and `git apply` RC 0; all seven touched paths report clean application and no nonzero offset. `git diff --check` returns 0. The resulting tree is `482e1dfbb6945ff5bce3c95279d65ebfbfebf23e`; the only delta from the pre-seam tree is the exact seam-v2 patch.

### 3.3 Functional test evidence

The Agent report and raw logs record:
- Kconfig option is `bool`, `default n`, preserves `depends on !KUNIT_ALL_TESTS`;
- UML final config sets the test symbol to `=y`; built-in observer/helper symbols are present in vmlinux;
- UML KUnit KTAP `1..1`, `ok 1`, process exit code 0;
- Host regression suites 38/38 and 83/83, both exit code 0;
- product `.config` SHA-256 unchanged before and after: `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`;
- `git diff --check` returns 0.

These are positive Agent-reported results. They are not a product Image build or hardware/device test.

## 4. Static-check and report-consistency adjudication

The original AI2 taskbook's literal checkpatch threshold was **0 errors and 0 warnings**; it did not separately require a zero process exit code or zero CHECK items.

The raw `round132-v2-checkpatch.log` (blob `5d4bd93870f4a07e92bc455a2957ee765fcf02e4`) records:
- 0 errors;
- 0 warnings;
- 3 CHECK items: `last_min_uV`, `last_max_uV`, `last_load_uA`;
- `checkpatch.pl --strict` exit code 1 because CHECK items make the tool return nonzero;
- `git diff --check` exit code 0.

Thus the numeric hard threshold explicitly stated in that taskbook (zero errors / zero warnings) is met, but the style check is **not clean-zero**: three CHECK items remain and must be listed. Final owner adjudication must explicitly state whether these three CamelCase test-field checks are accepted as nonblocking, and must not claim `checkpatch --strict` returned 0.

The independent `scripts/spdxcheck.py` run is `NOT RUN` due missing `python3-ply`. The taskbook expressly allowed this item to be marked NOT RUN when the dependency was unavailable, provided the error was disclosed; it is not to be misreported as PASS.

The Agent final report's unconditional PASS and its zero-offset narrative are inaccurate under the raw logs. The report must be supplemented with an owner-authored correction/addendum; do not overwrite the historical log or original report.

## 5. Current ROUND132 disposition

**1号 AI ruling: the offset issue is accepted under the revised controlled-offset rule. The frozen 17-patch replay is no longer a FAIL solely because of the five deterministic hunk offsets.**

The complete ROUND132 result is **ELIGIBLE FOR 2号 AI OWNER ACCEPTANCE, not yet finally accepted by the implementation owner**. 2号 AI must publish an owner adjudication / report addendum that:

1. replaces the inaccurate zero-offset claim with the exact five hunk offsets listed above;
2. confirms both independent trees equal the predeclared tree `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`;
3. explicitly adjudicates the 3 checkpatch CHECK items and RC 1 under the literal 0-error/0-warning taskbook threshold;
4. records standalone SPDX as NOT RUN due missing `python3-ply`;
5. confirms whether the KUnit / Host / product-config evidence is accepted without rerun, since the exact tested patch SHA and product config are unchanged.

2号 AI remains owner of its implementation and testbook and must write/publish its own owner addendum. 1号 AI must not edit the AI2 branch, modify the test patch, rewrite the historical test evidence, or issue an Agent task on AI2's behalf.

## 6. Forward rule

For subsequent patch validation rounds, use the controlled-offset criteria in §2 instead of a blanket zero-offset requirement. Every new taskbook must declare the expected result tree before execution where possible. Report raw offsets faithfully, and require exact tree agreement in independent clean trees.
