# ROUND154 — WorkBuddy Window B: independent patch / DTBO reproduction

- **Executor: WorkBuddy Window B (2号 Agent).**
- Important: Window A and Window B are both WorkBuddy. They are separate chat windows and separate execution contexts; this task does not require a different AI product.
- This report must explicitly identify Window B and its own workspace. Do not call yourself a different product or say a different tool is required.
- Candidate: ACK `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`; pre-change accepted tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
- Task type: independent artifact/source reproduction and static DTB/DTBO compatibility test. No device or full kernel/Image build.

## 1. Purpose

ROUND153 has the core RAM/reservation calculations, but Window B must reproduce them in its own separate WorkBuddy chat/workspace. It also must independently verify the key newly discovered packaging blocker: the candidate DTB has no exported `rootparam` symbol and stock overlays use external fixups.

The previous ROUND153 report from the second lane is not discarded. This task corrects its ambiguous execution provenance and creates independently attributable evidence from Window B.

## 2. Workspace isolation

Use Window B's own existing candidate artifacts/workspace. Do not enter or reuse Window A's workspace, temporary directory, build output, raw logs or private chat artifacts. If only Window A's workspace is available, stop and report; do not relabel it as independent.

Create an isolated scratch worktree/output directory under Window B's own workspace; do not overwrite the frozen ROUND140 outputs or original candidate. Record the exact workspace path in the private run log, but do not expose user-specific or sensitive identifiers in the report.

## 3. Required checks

### A. Candidate identity correction

1. Independently hash Window B's candidate DTB and record its 64-character SHA-256 and size.
2. Compare it to:
   - the malformed 63-character expectation inherited by ROUND147/152/153 taskbooks;
   - ROUND140 Stage-B4 log's actual and expected values;
   - ROUND147's published DTB identity.
3. Resolve which 64-character digest is the true frozen candidate identity. Do not repair a hash by guessing or dropping/inserting a character.
4. If local file cannot be read, report that and stop identity claims.

### B. RAM and reserved-memory reproduction

Independently verify:
- exactly one root `device_type = "memory"` node;
- its current size-zero tuple;
- three ROUND151 live RAM windows and exact 12,185 MiB total;
- ordering, gaps, overlap, 64-bit representation and overflow;
- all 18 candidate reserved-memory intervals, sum, union, containment, and all consumers/phandle references;
- 70 MiB `cdsp_secure_heap` status and whether it is referenced;
- 40.080 MiB stock-only fixed coverage and dynamic pools only as cross-reference (mark stock values as report-derived if the stock binary is unavailable).

### C. Reproduce the RAM-only patch independently

After Window A publishes its patch diff and patch blob/commit, independently apply the same intended change from Window B's unmodified frozen base:
- alter only existing `/memory@80000000/reg` to the 3 exact 2/2 tuples;
- do not create a second memory node;
- do not change the 18 reserved-memory nodes;
- retain `qcom,board-id = <0 0>` pending selector proof.
Build the affected DTB in Window B's isolated output. Compare full source diff, source tree identity, DTB size/hash and all RAM/reservation properties. Explain any nondeterministic or toolchain difference.

### D. Reproduce candidate-vs-stock DTBO external fixup compatibility

Using Window B's own candidate source/output and its available stock Entry 2 artifact:
1. Enumerate all Entry 2 external fixup symbols and fragment targets.
2. Test them against the baseline candidate DTB.
3. In scratch only, test a labelled `rootparam` plus symbol export via `-@`; do not edit the accepted source.
4. Determine whether every external symbol and target resolves, not just `rootparam`.
5. Run a whole-overlay apply test if the available local tools support it. Preserve complete logs and report the exact unresolved list and error.
6. If Window B cannot obtain the stock DTBO from its own permitted files, say so; do not copy Window A's raw/private artifact.

### E. Compare with Window A

Only after Window A publishes its report and patch identity:
- compare final source diff and tree SHA;
- compare candidate DTB bytes;
- compare all 144 Entry 2 fragment/fixup outcomes;
- list any discrepancy; do not silently reconcile by changing evidence.

## 4. Prohibitions

- No access to Window A's workspace or private logs.
- No device, ADB, root, fastboot, recovery, partition reads/writes, flash, reboot or candidate boot.
- No modification of the frozen base, prior build output, stock firmware or original DTBO.
- No full kernel/Image build.
- No raw firmware/FDT, serial, IMEI, MAC, panel IDs or private logs in public report.

## 5. Deliverable

Publish:
`firmware-analysis/round154/WORKBUDDY_B_ROUND154_INDEPENDENT_PATCH_AND_DTBO_REPRODUCTION_REPORT.md`

The first section must say: "Executor: WorkBuddy Window B (2号 Agent); separate WorkBuddy chat window from Window A." Do not call this executor a different AI product.

Read back the report, verify exact blob SHA/content, then STOP.