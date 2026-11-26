# AI1 ROUND153 — Fast-track first-boot path

- Role: **1号 AI (ChatGPT)**
- Date: 2026-11-26
- Goal: reach the first controlled candidate boot as soon as the required evidence and safety gates permit.
- Fixed base: ACK `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`.
- Frozen candidate tree before RAM change: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
- No boot, flash, device write or build was performed by this memo.

## 1. Scope reduction — stop expanding the pre-boot audit

The following work is **not a first-boot blocker** and is frozen unless new evidence shows a direct boot dependency:
- exact HOS proxy consumer lifecycle recreation;
- porting all seven HOS ARC provider groups;
- full HOS ARC regulator-child fidelity;
- numerical reconstruction of all 26 HOS msm-bus vectors;
- camera/display/CMA reservation completeness;
- exact HOS 4.19 vendor UFS driver source, unless it reveals a concrete fatal incompatibility in the retained candidate path.

Do not add ARC or proxy support in the first-boot candidate. Do not introduce a second `mmcx.lvl` writer.

## 2. Freeze the candidate UFS architecture for the bring-up attempt

For the first candidate boot, retain the currently compiled ACK UFS architecture as the comparison baseline:
- UFS host RPMHPD MMCX + UFS PHY GDSC GenPD attachment;
- UFS PHY same GDSC GenPD attachment;
- current OPP / required-opps;
- current `ufs-ddr` and `cpu-ufs` ICC paths;
- six already matched UFS rail mappings.

This is **not** accepted as HOS-equivalent, and does not prove runtime correctness. It is a controlled upstream-native bring-up baseline. The stock `ufs_phy_gdsc` software regulator being disabled/unused does not prove the physical GDSC is off. The candidate must retain one coherent gate owner: do not add `vdd-hba-supply` on top of GenPD.

## 3. Minimal DTS correction to prioritize

The candidate root `/memory@80000000` currently has one size-zero tuple. Fixed ACK early FDT scanning skips zero-sized RAM tuples. The published live ROUND151 map for this exact device is:

| Base | Size | MiB |
|---|---:|---:|
| `0x80000000` | `0x39900000` | 921 |
| `0xc0000000` | `0xc0000000` | 3072 |
| `0x200000000` | `0x200000000` | 8192 |
| **Total** | | **12,185 MiB** |

After Agent2's independent confirmation, AI1 should make a **single-property RAM-only change** on the existing root memory node: replace `reg` with exactly these three 2-address-cell/2-size-cell tuples in ascending base order. The 64-bit tuple encoding is:
- base/size `0x80000000 / 0x39900000` → `<0x0 0x80000000 0x0 0x39900000>`;
- base/size `0xc0000000 / 0xc0000000` → `<0x0 0xc0000000 0x0 0xc0000000>`;
- base/size `0x200000000 / 0x200000000` → `<0x2 0x0 0x2 0x0>`.

Do not create another `device_type = "memory"` node. Do not change any reserved-memory node in this minimal patch. This map is proven for the captured unit only; do not generalize it to all DBY-W09 capacity/board variants without evidence.

This explicit map removes the need to rely on an unproven ABL memory-fill contract. ABL behavior is still desirable evidence, but it should not hold up the RAM-only patch if the bootloader artifact is unavailable and the exact full DTBO selection can be resolved.

## 4. DTBO / boot-chain gate — narrow it

WorkBuddy Agent 1's current task has two distinct outputs:
1. Compare **all bytes / all FDT nodes and properties** of stock DTBO Entry 2 and Entry 8; verify live `androidboot.dtbo_idx=2`; record their board-id/revision fields and differences.
2. Inspect any already-existing ABL/XBL artifact in its own workspace. If none exists or it is not analyzable, report that explicitly. Do not invent an ABL fixup path.

The DTS comment's `0x206a` / Entry 8 assumption is not to be copied blindly. ROUND151 reports the actual running stock selection `dtbo_idx=2` / board ID `0x200e`. The first-boot package must use a deliberate, evidence-backed overlay selection. If Entry 2 is the actual selected payload and the complete comparison shows the relevant overlay is suitable, document that choice and update only the stale DTS comment if the source confirms it is wrong.

## 5. Parallel work and handoff

- **WorkBuddy Agent (local Agent 1):** finish whole Entry 2 vs Entry 8 comparison and ABL artifact inventory. Do not spend time on unrelated firmware packages if the task's own existing workspace has no artifact. Provide a partial report as soon as DTBO findings are complete; ABL can remain UNKNOWN.
- **2号 Agent (local Agent 2):** independently validate the candidate DTB hash, all three RAM windows, and all reserved-memory intervals in its own workspace. This must be genuinely performed by Agent 2, correcting the ROUND152 execution-identity issue.
- **AI1:** no more broad static UFS research. Once the two independent outputs arrive, produce the minimal RAM patch and exact resulting source-tree identity, then review it.
- **2号 AI:** ROUND152 architecture review is complete. No new AI2 round is needed unless AI1 finds a concrete source discrepancy.

## 6. Build sequence — exactly two formal builds

After the RAM-only patch and DTBO decision are reviewed:
1. Primary build on the canonical tree, record exact source tree, patch diff, `.config`, toolchain/dependency provenance, DTB, Image, BTF, module-signing certificate hash and full logs.
2. Independent Agent2 build from an independent workspace using the exact taskbook and dependencies. Compare the same artifacts; explain nondeterministic certificate/BTF differences. Never use Image SHA alone as the only pass/fail measure.

Do not create speculative ARC/proxy/CMA/display changes that would force another build.

## 7. First-boot safety gate

A test package can be prepared after both builds, but **first boot remains prohibited** until all items below are explicit PASS:
- exact boot image / vendor_boot / boot-v2 / independent ramdisk / DTBO packaging selected and hashed;
- AVB/vbmeta chain understood, no unexplained footer/range anomaly or forced verification bypass;
- full required partition backup completed and hashes verified;
- tested/reliable recovery route to the exact stock state is available;
- candidate package identity and install target are unambiguous;
- user gives explicit authorization for the first candidate boot.

No partition writes, flash, reboot, fastboot or recovery action is authorized by this memo.

## 8. Stop rule

If the DTBO selection and minimal RAM patch are ready, proceed directly to the two formal builds. Do not open another round for questions already settled. If a blocker remains, create one focused task for that blocker only. Keep the first-boot goal ahead of full post-boot hardware feature completeness.

— END —
