# ROUND156 — WorkBuddy Window A: exact ABL control-flow, RAM and AVB gate

- Executor: WorkBuddy Window A (1号 Agent).
- Window B is a separate WorkBuddy chat. Do not access it.
- Use only the exact ABL/XBL/xbl_config binaries and extracted ABL PE already captured in Window A's own ROUND155 workspace.
- Task type: offline read-only reverse engineering. No additional ADB/device reads, source edits, builds, flash, reboot, fastboot or recovery.

## 1. Purpose

ROUND155 obtained exact live ABL and XBL binaries and found instruction xrefs to board/msm/pmic matching, boot-v2 DTB parsing, DTBO selection, ufdt overlay apply, and /memory update routines. Those xrefs do not prove control flow. This round must trace branches and call sites sufficiently to decide whether the candidate can boot without the stock overlay and whether ABL will rewrite the RAM tuples.

## 2. A — identity and provenance

From Window A's local ROUND155 evidence, record:
- live ABL partition size and SHA-256;
- decompressed PE payload size and SHA-256;
- XBL and xbl_config sizes and SHA-256;
- sanitized firmware/build provenance.
Keep all raw binaries, decompressed payload, private paths and complete logs local. Do not upload them.

## 3. B — boot-v2 SoC DTB selection

Trace actual AArch64 instruction/control flow around and upstream of the known references:
- qcom,board-id xref site 0x3a18c;
- boot-v2 strings for DTB Size, single appended DTB, multiple appended DTB and qcom,msm-id;
- androidboot.dtb_idx and DTBO index output site 0x42ac0.

Determine:
1. how the ABL parses dtb_size and walks concatenated FDTs;
2. whether it scans all FDTs or expects one, and exact msm-id/revision/board match order;
3. how it handles the stock three-FDT image and selects the kona v2.1 tree;
4. whether a single candidate FDT is accepted;
5. required candidate root properties and any fallback behavior.

Give exact code ranges and reconstructed branches. If control flow cannot be recovered, mark the unresolved item clearly.

## 4. C — DTBO selection and overlay apply/skip behavior

Trace:
- DTBO count, LocalBoardDtMatch, header validation and table entry selection;
- androidboot.dtbo_idx / dtb_idx output;
- ufdt_install_blob xrefs around 0x6aaf8 and 0x6ab7c;
- fixup and fragment error paths.

Answer:
1. What exact input chooses Entry 2? Is androidboot.dtbo_idx an input, output, or both?
2. Does ABL always apply an overlay when a DTBO partition is present?
3. Is a no-DTBO or skip-overlay branch present? Give the exact condition.
4. Does the actual ufdt path support target-path fragments?
5. Does overlay failure abort boot, fall back to base DTB, or continue?
6. Does the 199-byte target-path debug-UART overlay from Window B match this ABL implementation, based on code evidence only?

Do not assume host fdtoverlay success proves Huawei ufdt behavior.

## 5. D — /memory updater semantics

Trace around:
- /memory reference at 0x3e650;
- ddr_device_type references at 0x3e798, 0x3e7b4, 0x3e834;
- error strings for memory addr/size, BaseAddr, HwDdrSize and cell widths.

Answer:
1. Does ABL delete /memory/reg before updating it?
2. Does it append RAM tuples, replace existing tuples, or skip when reg is already non-zero?
3. Would a candidate-authored three-window reg be preserved, duplicated or overwritten?
4. How does the XBL config's 6 MiB unusable DDR-at-start setting affect the published ranges and reserved areas?
5. Are ddr_device_type/rank/HBB properties independent of reg mutation?
6. Does ABL modify /reserved-memory? If so, exactly which nodes and under what conditions?
7. Compare the reconstructed result with ROUND151 live RAM windows and the candidate's three tuples.

This section is a hard gate. Do not declare the RAM patch safe for boot until this is resolved or a minimal proof is identified.

## 6. E — AVB and unlocked state

Use only Window A's local ROUND155 copies of ABL, boot, dtbo, root/child vbmeta and recovery images.

ROUND155 observations:
- root vbmeta is SHA256_RSA2048 with flags=3 and chain descriptors including boot, ramdisk and dtbo;
- live boot is boot-v2, has no AVBf footer detected, and differs from firmware package boot in kernel/footer region; its three FDTs are byte-identical;
- live bootargs report androidboot.verifiedbootstate=orange;
- vbmeta_cust is a 1 MiB footer-only shell with Algorithm NONE, zero auth/aux blocks, no descriptors and an out-of-range original-size pointer.

AOSP reference semantics:
- bit0 = HASHTREE_DISABLED;
- bit1 = VERIFICATION_DISABLED;
- VERIFICATION_DISABLED means descriptors are not processed in standard libavb.
Do not transfer this standard behavior to Huawei ABL without inspecting its exact implementation.

Determine:
1. Is the ABL device-state/unlocked check visible? What source or secure-state input is used?
2. Does ABL invoke AVB verification? Trace the path and relevant flags.
3. Does flags=3 bypass the boot/ramdisk/dtbo descriptor checks in this exact firmware, or are there additional OEM checks?
4. Is orange state emitted from an actual unlocked-state branch?
5. Is the top-level vbmeta signature still verified?
6. How does the live boot partition without AVBf coexist with the reported chain descriptors?
7. Under what exact condition, if any, would a modified boot/dtbo image be accepted without a new OEM signature?

No keys, signing, flag modification, vbmeta edit or bypass attempt.

## 7. Deliverable

Publish sanitized report:
firmware-analysis/round156/WORKBUDDY_A_ROUND156_EXACT_ABL_CONTROL_FLOW_AND_AVB_GATE_REPORT.md

Include binary hashes, code ranges, instruction/control-flow excerpts, evidence grades and unresolved items. Raw binaries, PE payload, private paths, serials and full logs stay local. Read back and verify exact blob/content, then STOP.

## 8. Prohibitions

No additional device command or ADB connection. No partition read/write, mount, property change, flash, reboot, fastboot, recovery, source edit or build. No access to Window B's workspace.

— END —