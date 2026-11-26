# AI1 ROUND154 — Bring-up decision and WorkBuddy window allocation

- Owner: 1号 AI (ChatGPT)
- Date: 2026-11-26
- Goal: move directly from ROUND153 evidence to a tested candidate DTB and a first-boot package decision.
- Fixed kernel base: ACK `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`.
- Frozen pre-change 23-patch tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
- No device operation, boot, flash or partition write is authorized here.

## 1. Correct role model

The two local agents are **two separate WorkBuddy chat windows**, not different software products:
- **WorkBuddy Window A = 1号 Agent**: primary local implementation and package compatibility test.
- **WorkBuddy Window B = 2号 Agent**: independent reproduction/review from its own isolated workspace.
Both may use WorkBuddy. Independence is established by separate chat context, separately controlled workspace and independently reproduced evidence—not by different product names.

ROUND153's second report is technically usable. Its self-description says the executor reused the Agent2 workspace and does not certify a separate WorkBuddy-window execution. The report must not be discarded; Window B's ROUND154 task is to repeat the decisive checks in its own isolated workspace and explicitly identify that window. Do not describe the second WorkBuddy window as a different AI product.

## 2. ROUND153 consolidated findings

1. For the captured tablet only, live RAM is:
   - `0x80000000 + 0x39900000` (921 MiB)
   - `0xc0000000 + 0xc0000000` (3072 MiB)
   - `0x200000000 + 0x200000000` (8192 MiB)
   Total 12,185 MiB. The tuples are ordered, non-overlapping and no-overflow. Candidate has one size-zero `/memory@80000000` tuple.
2. Candidate's 18 reserved-memory intervals total 254.609 MiB, do not overlap, and sit within RAM window 1. Keep them unchanged in the minimal RAM patch. Retain the 70 MiB CDSP carve-out provisionally; no consumer/need is proven.
3. Live HOS boot selected DTBO Entry 2 / board-id `0x200e`. Entry 8 / `0x206a` is not the live entry. The candidate comment's selection mechanism is unsupported; do not change the base DTS `qcom,board-id = <0 0>` without evidence.
4. Entry 2 and Entry 8 are not byte-identical: 5 property differences plus one duplicated sensor fragment. All UFS/PMIC/regulator/RPMh/GDSC/power-domain fragments are equal.
5. Stock boot's base DTB is not wholesale replaced by the final live FDT. The stock boot-chain transforms the base `/memory/reg` from one zero tuple to three windows; DTBO does not target `/memory`. The exact component (ABL or another layer) is unknown because no ABL binary is available.
6. The stock base DTB preserves its 37 reserved-memory children; boot chain does not provide candidate carveouts on the candidate's behalf.
7. Candidate built DTB lacks `/__symbols__`, `/__fixups__`, `/__local_fixups__`; `/rootparam` has no phandle. The source references a missing `dby-w09-ack18-rootparam.dtso.draft`. A stock-style `rootparam` symbol fixup cannot bind to the current candidate DTB as built. This is a first-boot packaging blocker until tested/resolved.
8. Stock `boot.img` header v2 contains three concatenated DTBs. Candidate packaging must explicitly establish whether one device-specific DTB is accepted or the three-DTB container/selection contract must be preserved.
9. Candidate DTB identity string in earlier taskbooks is malformed (63 hex characters). Do not use it as a passing criterion. Window B must verify the real 64-character digest from its own bytes and reconcile with ROUND140/147 logs before any hash claim.

## 3. Scope cut for first boot

Do not port ARC, proxy-consumer, CMA, display, camera, WLAN or the complete HOS 4.19 power topology as a precondition. Retain the current ACK UFS GenPD/OPP/RPMHPD baseline; do not add a second `mmcx.lvl` writer or `vdd-hba-supply` on top of GenPD. These are later functionality work unless a concrete first-boot dependency is found.

## 4. Window A — minimal patch and real packaging compatibility

Window A task:
`firmware-analysis/round154/WORKBUDDY_A_ROUND154_MINIMAL_RAM_PATCH_AND_DTBO_BOOT_PACKAGE_GATE_TASKBOOK.md`

Deliver:
- a reversible, minimal source patch changing only the existing root `/memory@80000000/reg` to the three exact 2/2 tuples above; no new memory node and no reserved-memory edits;
- correct only stale comments that become false; leave `qcom,board-id = <0 0>` unchanged pending selector evidence;
- a scratch DTB build of this patch, full DTB node/RAM/reservation checks;
- a source/DTB-level test of stock Entry 2 fixups against candidate. Try label + `-@` only in scratch; determine whether all external fixups resolve, not only `rootparam`. Do not assume `-@` alone solves missing symbols/targets;
- boot-v2/DTB-container and DTBO partition packaging decision, based on existing artifacts and build scripts;
- AVB/backup/recovery blockers list based on existing records only; no device access.

No full kernel/Image build until Window A proves the DTBO and container strategy. Do not flash or boot.

## 5. Window B — truly separate WorkBuddy chat-window reproduction

Window B task:
`firmware-analysis/round154/WORKBUDDY_B_ROUND154_INDEPENDENT_PATCH_AND_DTBO_REPRODUCTION_TASKBOOK.md`

Use its own isolated workspace, not Window A's private path/logs. Starting from the pinned ACK + accepted 23-patch candidate, independently:
- verify actual candidate DTB size and SHA-256 (64 hex characters);
- independently calculate the three RAM windows and all 18 reserved intervals;
- reproduce the RAM-only source patch and scratch DTB;
- test Entry 2 overlay external fixup resolution against its built candidate DTB, including all fragments/targets;
- compare final patch, tree identity, DTB bytes and overlay application results with Window A only after its report is published.
Do not claim independence if the work used Window A's modified tree or private logs. Report any difference rather than forcing a match.

## 6. Build gate

Only after both windows confirm the same RAM patch and one viable DTBO/boot-v2 packaging strategy:
1. primary full build with full source tree SHA, 23-patch replay, config, toolchain/dependency provenance, DTB, Image, BTF and module-signing certificate evidence;
2. independent full build by Window B from its own workspace;
3. compare artifacts with certificate/BTF nondeterminism explained.

## 7. Safety gate

First candidate boot remains prohibited until boot image / vendor_boot / DTBO packaging is unambiguous, AVB/vbmeta path is understood, full required partition backups are hash-verified, tested stock recovery is available, and the user explicitly authorizes the candidate boot. No partition reads/writes, flash, reboot, fastboot or recovery operation is authorized by these tasks.

— END —