# AGENT2 ROUND153 — Independent candidate RAM / reserved-memory revalidation

- **Assigned executor: 2号 Agent (independent local Agent 2) only.**
- Not WorkBuddy Agent 1; not 2号 AI; not AI1.
- Device: Huawei MatePad 11 (2021), DBY-W09 / HWDBY / KONA / SM8250.
- Candidate: ACK `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`, content tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
- Expected candidate DTB: 108,648 bytes, SHA-256 `cab82fe3901dbb40533197eb48b2d99b08b46e5d5497ff1a6f688e9938db77e`.
- Branch: `agent2/round153-independent-candidate-ram-reserved-revalidation`.
- Task type: **independent local artifact revalidation**, no device, no build, no writes.

## 1. Purpose

ROUND152's candidate-DTB report was published on the Agent2 branch but explicitly disclosed that WorkBuddy-side Agent 1 executed it while reading the Agent2 workspace. That report is useful evidence but is **not** an independent 2号 Agent deliverable. This round corrects the role separation and independently verifies the small set of facts that will decide the next DTS change.

## 2. Permitted inputs

Use only 2号 Agent's own workspace and its own frozen candidate artifacts:
- `/home/kerneldev/work/matepad11/round140-agent2/tree`
- `/home/kerneldev/work/matepad11/round140-agent2/out-dtb`
- `/home/kerneldev/work/matepad11/round140-agent2/logs`
- `/home/kerneldev/work/matepad11/round140-agent2/a30build` only if needed to locate provenance; do not write there.

Use the published ROUND151 stock runtime report and ROUND152 report as read-only comparison inputs. Do not inspect WorkBuddy's local evidence tree, AI2 private workspace, or any other Agent workspace. Do not access the tablet.

## 3. Required checks

### A. Candidate DTB identity and RAM tuple

1. Recompute exact candidate DTB size and SHA-256 before and after inspection; verify it matches the expected identity above.
2. Decode **all** root-level `device_type = "memory"` nodes. Distinguish them from same-named children under `/reserved-memory`.
3. Confirm tuple cell widths and every base/size pair in `/memory/reg`.
4. Confirm the proposed RAM map from ROUND151:
   - base `0x80000000`, size `0x39900000`;
   - base `0xc0000000`, size `0xc0000000`;
   - base `0x200000000`, size `0x200000000`.
5. Independently check ordering, overflow, pairwise overlap, gaps and total = 12,185 MiB. Confirm all three ranges correspond to the published live stock FDT and `/proc/iomem` evidence for this specific unit.
6. Explain what a RAM-only DTS diff should look like: replace the existing zero-size `reg` property on the one root memory node with exactly three 64-bit base/size tuples; do not create a second `device_type=memory` node.

### B. Candidate reserved-memory census

1. Decode all 18 candidate reserved-memory child nodes and all their properties relevant to placement: `reg`, `size`, `alignment`, `alloc-ranges`, `no-map`, `reusable`, `linux,cma-default`, phandles, `memory-region` references.
2. Verify no pairwise overlaps, all intervals sit inside one of the three stock RAM windows, and the sum/union calculations independently.
3. Specifically review the candidate 70 MiB fixed carve-out at `0x8bf00000` (CDSP secure heap): does the candidate tree contain any consumer or phandle reference? Is the same stock node placed or unplaced? Do not recommend removing it without exact source/consumer evidence.
4. Reconcile the stock-only 40.080 MiB fixed reservation coverage and the 12 dynamic pools. Do not treat vendor-only pools as mandatory without an enabled candidate consumer.
5. State whether the proposed RAM-only edit changes any reserved-memory interval (it must not).

### C. Board ID / DTBO cross-reference

From candidate source only, verify:
- root `qcom,board-id`;
- adjacent comments citing DTBO board ID `0x206a`;
- any additional DTBO assumptions embedded in the DTS.
Compare only against the published ROUND138/151 entries and clearly mark unverified overlay details. Do not access another Agent workspace or device. Do not try to settle the full Entry 2/8 overlay comparison; that is WorkBuddy's separate ROUND153 task.

### D. Independent conclusion

State whether the RAM-only tuple change is mathematically safe for this exact device's published map, what device/SKU generalization is not justified, and all unresolved ABL / DTBO conditions. Report any discrepancy against the ROUND152 report rather than silently inheriting it.

## 4. Prohibitions

- No WorkBuddy Agent workspace access.
- No 2号 AI private workspace.
- No tablet, ADB, root, fastboot, recovery, partition read/write.
- No source edits, no DTS/patch change, no build, no dtc invocation that writes outputs.
- No raw FDT, raw firmware, serial, IMEI, MAC, panel ID or private logs in the repository.
- No claims of independent verification unless performed by 2号 Agent in its own workspace.

## 5. Deliverable

Upload:
`firmware-analysis/round153/AGENT2_ROUND153_INDEPENDENT_CANDIDATE_RAM_RESERVED_REVALIDATION_REPORT.md`

Include identity hash, exact arithmetic, evidence-grade labels, local execution role and scope. Read the uploaded file back, verify its exact blob SHA and content, then STOP.
