# ROUND157 — 2号 AI: integrated first-boot strategy and go/no-go

- Executor: 2号 AI, independent AI collaborator.
- This is not AI1 and not either WorkBuddy chat window.
- Task type: read-only review of the actual ROUND156 Window A/B results, AOSP AVB definitions and ROUND155 backup capture.

## 1. Mandatory inputs

Read the actual ROUND156 result reports:
- WorkBuddy Window A: firmware-analysis/round156/WORKBUDDY_A_ROUND156_EXACT_ABL_CONTROL_FLOW_AND_AVB_GATE_REPORT.md
- WorkBuddy Window B: firmware-analysis/round156/WORKBUDDY_B_ROUND156_CANDIDATE_FIRSTBOOT_DTB_VARIANTS_REPORT.md
- Prior AI2 ROUND156 report and identify that it was executed before the WorkBuddy A/B result reports were published; its missing-input section is stale.
- AI1 integration report: kernel-baseline/round156/AI1_ROUND156_DELIVERY_REVIEW_AND_ROUND157_PLAN.md
- ROUND155 WorkBuddy Window A partition backup/ABL report.
- ROUND155 WorkBuddy Window B candidate first-boot report.
- ROUND154 Window A/B reports.

## 2. Required questions

1. Update the ABL conclusions based on actual ROUND156 Window A control-flow:
   - single-FDT boot-v2 path and MSM/board/PMIC match order;
   - DTBO index is an output of ABL selector;
   - explicit no-overlay/skip path;
   - target-path support;
   - overlay application failure non-fatal return;
   - whether failure occurs before fragments mutate base;
   - /memory updater rewrite/append semantics and implications.
2. Review Window B variants A/B/C and recommend the smallest first-boot candidate. Distinguish the base DTB from optional UART-enabled variant and target-path overlay.
3. Interpret flags=3 strictly:
   - AOSP bit definitions;
   - top-level vbmeta image signature/key/rollback order;
   - descriptor skip behavior;
   - unlocked allow-verification-error branch in Huawei ABL;
   - Huawei-specific digest/TA/rollback checks and unresolved proof.
4. Confirm the exact state of live bootargs orange and its relation to ABL's AppendVBCommonCmdLine branch; distinguish standard AVB orange meaning from Huawei userlock.
5. Evaluate whether the simplest test can leave stock DTBO bytes unchanged and rely on the ABL's non-fatal failed overlay, or whether this is unsafe due possible partial application. Do not guess if ABL atomicity evidence is incomplete.
6. Review 18/18 boot-chain backups and identify exactly what is missing for a boot-only write and a recovery route: complete chain target partitions, GPT/partition geometry, rollback/boot-control metadata, a supported way to enter restore mode, eRecovery and actual restoration rehearsal.
7. Give distinct go/no-go for (a) offline full kernel build, (b) offline boot.img construction, (c) temporary boot, (d) partition write.
8. Recommend the shortest exact next step, without reopening ARC/proxy/display audits.

## 3. Evidence standard

Use official AOSP AVB source:
- avb_vbmeta_image.h
- avb_slot_verify.c
- avb_slot_verify.h
Cite exact source lines/links. Do not call AOSP standard behavior proof of Huawei ABL behavior without matching the exact binary report.

Distinguish:
- demonstrated by exact ABL control-flow;
- reported from live device capture;
- host-side DTB/DTBO result;
- inference/unknown.

## 4. Deliverable

Publish:
firmware-analysis/round157/AI2_ROUND157_INTEGRATED_FIRST_BOOT_GO_NO_GO_REPORT.md

Read back and verify blob/content, then STOP.

No device, code edits, build, package generation, flash, reboot, fastboot, recovery, signing or key operations.

— END —