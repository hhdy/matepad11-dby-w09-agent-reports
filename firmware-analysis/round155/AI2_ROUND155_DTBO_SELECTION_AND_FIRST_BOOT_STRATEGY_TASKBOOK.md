# ROUND155 — 2号 AI: DTBO selection and first-boot strategy review

- Executor: 2号 AI, the independent AI collaborator.
- Not WorkBuddy Window A, not WorkBuddy Window B, not AI1.
- Task type: read-only architecture/source/report review. No device access, source edits or builds.

## 1. Inputs

Read:
- Window A report: firmware-analysis/round154/WORKBUDDY_A_ROUND154_MINIMAL_RAM_PATCH_AND_DTBO_BOOT_PACKAGE_GATE_REPORT.md
- Window B report: firmware-analysis/round154/WORKBUDDY_B_ROUND154_INDEPENDENT_PATCH_AND_DTBO_REPRODUCTION_REPORT.md
- AI1 review: kernel-baseline/round154/AI1_ROUND154_DELIVERY_REVIEW_AND_ROUND155_ACCELERATION.md
- ROUND151 live stock FDT and ROUND138 full DTBO inventory reports.
- Pinned ACK source, particularly DTS/Makefiles, overlay fixup behavior and boot integration references.

## 2. Questions

1. Independently confirm stock Entry 2 incompatibility: 0/166 symbols without -@; 10/166 with -@; 156 labels missing; 87/144 fragment targets missing.
2. Could first boot proceed without a DTBO overlay if the candidate base DTB contains all minimum required nodes, or is there evidence the bootloader applies the selected overlay unconditionally?
3. Separate boot-v2 SoC DTB selection by qcom,msm-id; separate DTBO index selection; external fixup resolution; bootargs/rootparam mutation. Do not conflate index 2 with board-id matching.
4. Would modifying only DTBO Entry 2 be technically sufficient, or must the entire table/header, AVB descriptor and vbmeta chain be regenerated? Assume no OEM signing key.
5. Compare a candidate-specific minimal overlay with expanding the base DTB. Enumerate evidence-based decision criteria and risks of the missing labels/targets.
6. Explain why -@ is a prerequisite for symbol export but cannot create vendor labels/nodes absent from the base.
7. Assess package options: retain three concatenated FDTs with candidate at slot 0 matching msm-id 0x164/0x20001; one-FDT slot; no DTBO; custom DTBO. Classify each proven/disproven/unknown.
8. Recommend the smallest next experiment that closes the most important unknown without writing to tablet.

## 3. Required verdict

Give one recommended minimal first-boot strategy and ranked blockers. State what is offline-testable, what needs the exact ABL, what only device boot can determine, what must be backed up before writes, and whether current ROUND154 is a hard no-go for flash.

Do not recommend disabling AVB or assuming an unknown signature bypass. Do not overstate recovery from KernelSU/root.

## 4. Deliverable

Publish:
firmware-analysis/round155/AI2_ROUND155_DTBO_SELECTION_AND_FIRST_BOOT_STRATEGY_REPORT.md

Read back and verify blob/content, then STOP.

— END —