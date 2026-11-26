# ROUND155 — WorkBuddy Window B: candidate-specific minimal DTBO

- Executor: WorkBuddy Window B (2号 Agent), a separate WorkBuddy chat from Window A.
- Both agents use WorkBuddy; do not describe them as different products.
- Candidate base: ROUND154 RAM-patched DTB SHA-256 9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60.
- Frozen source: ACK android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9; pre-change tree afe9517f8062b96bfeb5b4dd5714942861e6a44b.
- Task type: isolated scratch-only overlay design and static application test. No device or partition operation.

## 1. Purpose

ROUND154 proved stock Entry 2 cannot be applied to the minimal candidate:
- without -@: 0/166 external symbols bind;
- with scratch -@: 10/166 bind, 156 remain absent;
- 57/144 fragment targets resolve, 87 remain absent;
- fdtoverlay fails with FDT_ERR_NOTFOUND.

Do not retry stock Entry 2 or assume -@ solves it. Determine whether the candidate can boot with a candidate-specific minimal overlay, or whether required nodes/settings should instead be built into the candidate base DTB.

## 2. Workspace isolation

Use only Window B's own isolated ROUND154 workspace and frozen source/artifacts. Never enter Window A's private directory or use its logs/raw images. Preserve the original RAM-patched DTB and stock DTBO bytes. Create a new ROUND155 scratch directory.

Inputs may include published ROUND154 A/B reports and ROUND151 live report. The stock DTBO already used in Window B's ROUND154 workspace may be reused read-only.

## 3. Required analysis

### A. Candidate baseline

Record patched DTB size/hash, source tree SHA and toolchain. Confirm the 108,680-byte RAM-patched base. Confirm the 18 reserved-memory nodes and all candidate UFS/PMIC/GCC/UFS-PHY nodes. Do not edit candidate source.

### B. First-boot minimum

Classify candidate nodes needed for:
1. kernel early boot / RAM / timer / interrupt controller / console;
2. storage discovery / UFS host / PHY / regulators / clocks / resets / interconnect / power domains;
3. root filesystem access only if initramfs/package requires UFS;
4. non-essential devices that can remain disabled (display, audio, camera, WLAN, sensors, remote DSPs).

Use exact candidate tree and initramfs/package evidence. Do not assume UFS is needed to reach a rescue shell if initramfs can boot independently.

### C. Scratch candidate-specific overlay

1. Enumerate candidate node labels/paths relevant to the minimum above.
2. Compare against stock Entry 2 fragments; identify which required settings are already in the candidate base versus absent.
3. If an overlay is needed, write a new scratch DT overlay targeting only nodes actually present in the candidate, using real labels or paths and established properties.
4. Add no stock fragments merely because they exist. Do not fabricate labels, regulator phandles, UFS supply mappings, board selectors or vendor properties.
5. If no overlay is needed, demonstrate the candidate base already contains each proven first-boot essential and mark DTBO selection as a separate ABL/package dependency.

### D. Prove scratch application

Compile using the same dtc version; use -@ only where required. Apply via fdtoverlay to the RAM-patched base. Verify:
- application RC=0;
- every target resolves;
- no phandle collision;
- only intended properties/nodes change;
- RAM tuples and all 18 reserved-memory intervals remain byte-identical;
- output DTB parses and SHA-256 is recorded.

Also explain whether a custom overlay must occupy stock index 2 to match the captured live selection, while explicitly marking loader selection UNKNOWN absent ABL evidence. Do not create or modify a full DTBO container before its selection contract is established.

### E. Go/no-go verdict

Provide one:
- candidate-specific overlay is technically applicable and includes minimum proven first-boot settings; ABL selection remains separately gated;
- base DTB already contains all first-boot essentials and a no-overlay route is viable subject to bootloader acceptance;
- candidate lacks essential UFS/boot nodes and needs named DTS work;
- safe minimum cannot be established, with exact missing evidence.

Never claim that offline overlay application proves the device bootloader will apply/select it.

## 4. Deliverable

Publish:
firmware-analysis/round155/WORKBUDDY_B_ROUND155_CANDIDATE_SPECIFIC_DTBO_MINIMAL_OVERLAY_REPORT.md

Include commands, hashes, all scratch diffs and test results. Raw device/firmware files and private paths remain local. Read back and verify the report, then STOP.

## 5. Prohibitions

No source branch changes, no accepted patch edits, no full kernel/Image build, no device, ADB, root, fastboot, recovery, partition read/write, flash, reboot, unlock or state change. Do not access Window A's workspace.

— END —