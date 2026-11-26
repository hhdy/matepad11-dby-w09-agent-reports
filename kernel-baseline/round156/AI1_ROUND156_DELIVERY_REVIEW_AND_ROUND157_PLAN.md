# AI1 ROUND156 Delivery Review and ROUND157 Build Acceleration Plan

- Reviewer: 1号 AI (ChatGPT)
- Date: 2026-11-27
- Candidate: ACK android17-6.18.33_r00, pinned commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9
- Frozen 23-patch source tree before the RAM DTS change: afe9517f8062b96bfeb5b4dd5714942861e6a44b
- RAM-patched DTB: 108,680 B, SHA-256 9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60
- No device write, flash, reboot, fastboot or recovery was performed in this review.

## 1. ROUND156 deliveries verified

### WorkBuddy Window A — exact ABL control-flow report

Report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round156-abl-control-flow-avb-and-overlay-gates/firmware-analysis/round156/WORKBUDDY_A_ROUND156_EXACT_ABL_CONTROL_FLOW_AND_AVB_GATE_REPORT.md

Blob: e29c9789a1b30678b23e8fb1624129b056d003fb

Key results:
- ABL walks concatenated boot-v2 FDTs and has a first-class single-FDT branch.
- Match order is msm-id, board-id major/minor, then pmic-id/best-match logic.
- androidboot.dtbo_idx is output by the ABL selector, not the selector input.
- ABL has conditional no-overlay/skip branches; applying an overlay is not unconditional.
- Its UFDT implementation supports both target and target-path fragments.
- In the traced overlay path, apply errors converge to a return; the caller logs the failure and rejoins normal flow. It does not directly hard-abort the boot path.
- ABL actively rebuilds /memory/reg from DDR configuration. It does not simply trust a pre-populated candidate tuple. The best-supported model is rewrite/rebuild rather than append, but the exact low-level setprop/appendprop primitive remains one disassembly gap.
- XBL config marks the first 6 MiB beginning at 0x80000000 unusable; live HOS reserves that prefix as hyp_region while keeping the RAM window base at 0x80000000.
- Exact ABL has AOSP libavb code and an unlocked-state continuation branch. Root vbmeta flags=3 are consistent with descriptor processing being skipped under standard libavb semantics. Huawei-specific digest/TA checks and whether the top-level signature check can be bypassed remain unresolved.

### WorkBuddy Window B — first-boot DTB variants

Report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round156-candidate-dtb-firstboot-package-variants/firmware-analysis/round156/WORKBUDDY_B_ROUND156_CANDIDATE_FIRSTBOOT_DTB_VARIANTS_REPORT.md

Blob: 81e2d06c28f8462f2c179aef28eb247273293850

Key results:
- Variant A, the no-overlay RAM-patched base, is byte-reproduced: 108,680 B / 9d0d7600…fed60.
- Variant B, with debug UART enabled directly in the base DTS, is 108,676 B / 47ca4ff748baf6e72bc4ab26c4369ef13a15df9443a0a8dac16135ac0a7e78c7.
- Variant C, the base with the 199 B target-path UART overlay applied, is 108,676 B / 647af49b8c21198d9cba99fac444131aaf95e86c99b28af87b610fc46b30cea2.
- B and C are semantically and byte-structurally equivalent after decompilation: both differ from A only in UART status disabled -> okay.
- All three keep the same 3 RAM tuples, 18 reserved-memory nodes, 239 phandles, and UFS/PHY dependency closure.
- /chosen remains empty in all three and requires bootloader handoff injection.
- No boot.img or DTBO container was produced.

### 2号 AI — updated strategy report

Report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round156-updated-avb-first-boot-decision/firmware-analysis/round156/AI2_ROUND156_UPDATED_ABL_AVB_FIRST_BOOT_DECISION_REPORT.md

Blob: 9da92e98e2022666b036610fa6f1e6ae369163d8

Important delivery limitation: the AI2 report explicitly says the ROUND156 Window A and Window B reports were not yet published at the time it ran. It therefore did not integrate the two actual ROUND156 reports. Its no-go safety conclusion remains conservative and valid, but its report is not a final review of the completed ROUND156 evidence. It must be superseded by the ROUND157 AI2 integration review.

## 2. Consolidated technical decision

### 2.1 Base DTB and no-overlay strategy

The candidate base already includes the early boot and UFS/PHY nodes, regulators and all static phandle edges required by the minimum storage/rescue configuration. Window B found no identified stock Entry 2 fragment that is essential to the first-boot minimum.

ABL has a no-overlay/skip path, and its apply-error path continues normal boot flow. This makes a no-overlay candidate base **plausible**. It does not yet prove the exact device will take the path cleanly with the stock DTBO partition present.

Recommended first-boot design for offline package preparation:
- candidate RAM-patched base DTB in the boot-v2 SoC DTB slot matching msm-id 0x164/0x20001;
- preserve the stock three-FDT order as the conservative package hypothesis;
- leave the existing stock DTBO partition byte-identical for now;
- do not modify or replace Entry 2/Entry 8;
- expect the existing Entry 2 compatibility attempt to fail on missing candidate symbols, but do not rely on this until Window A confirms fixup failure occurs before any base-tree fragment merge and that its return path is non-fatal and clean;
- debug UART may be built into a candidate-only variant if the console is needed; no separate overlay is required for that variant.

This is a proposed test package strategy only, not authorization to flash.

### 2.2 RAM semantics

ABL actively writes the memory tuple array. The 3-window values in the candidate were copied from the live HOS FDT, but ABL may regenerate them from XBL DDR data. Keep the RAM patch as a deterministic fallback and preserve the node/cell geometry. The candidate's actual boot-time RAM map must be confirmed after a controlled boot by reading live FDT and /proc/iomem.

Window A still needs to close whether the updater's low-level write is a replace or append primitive. Until then, do not claim RAM is boot-safe-proven.

### 2.3 AVB

AOSP flag definitions: bit0 disables hashtree verification; bit1 disables verification and descriptor parsing. In AOSP libavb, the top-level vbmeta image signature is checked before the VERIFICATION_DISABLED descriptor-skip branch; public-key trust and rollback checks are also encountered before that branch. Sources:
- https://android.googlesource.com/platform/external/avb/+/master/libavb/avb_vbmeta_image.h
- https://android.googlesource.com/platform/external/avb/+/master/libavb/avb_slot_verify.c

The exact Huawei ABL contains libavb and an unlocked continue path, but the complete top-level signature/key/TZ/OEM digest flow is not fully reconstructed. The stock root vbmeta must remain byte-identical unless a legitimate, verified signing route exists. Flags=3 alone is not proof that arbitrary package changes will be accepted.

## 3. ROUND157 decision: begin formal kernel builds now

It is safe and useful to run full builds offline before every flash gate is closed. This does not modify the tablet.

- WorkBuddy Window A (1号 Agent): primary full kernel build from its ROUND154 RAM-patched source tree; additionally close the smallest remaining ABL proof gaps using its existing local exact ABL.
- WorkBuddy Window B (2号 Agent): independent full build from its own workspace, reconstructing exactly the same RAM patch from the published ROUND154 report and verifying the final source tree SHA before building.
- 2号 AI: review the actual ROUND156 A/B reports and update its stale decision with one integrated first-boot strategy, AVB interpretation, and remaining safety blockers.

Use the same target and build settings as the established ROUND135/ROUND140 build when available: tools/bazel build //common:dby_w09 --jobs=2. Preserve full logs, .config, toolchain/dependency provenance, source tree SHA, patch SHA, DTB, Image, BTF and module-signing certificate evidence. If this target or environment is unavailable, report the exact blocker and do not silently change target/config.

Both builds must record the exact source tree. Candidate tree after the minimal DTS and comment edits is c56d93eafa35057d65176db6594d67d5144868a0. The Window A RAM patch commit is 491d0cbffb4d16e2840c1788674e6a05b26e88a2. The true frozen pre-change DTB SHA-256 is 64-character value cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e; do not reuse the malformed 63-character inherited expectation.

## 4. Safety and current status

- No full Image build has yet been completed on the RAM-patched tree.
- No boot.img / DTBO package has been produced.
- ROUND155 captured and verified 18 boot-chain partitions; ten have second host copies. This is not a complete backup of all AVB chain targets, not a full GPT/partition geometry capture, and not a proven restore rehearsal.
- Device is A-only; no alternate slot is available.
- Exact ABL no-overlay/apply paths and RAM updater are much clearer, but runtime FDT/RAM behavior can only be closed after a controlled boot.
- First boot/flash remains NOT AUTHORIZED until the signed/accepted package path and a reliable stock restoration route are established, and the user authorizes the exact write target.

ROUND157 must focus on formal build artifacts and the final few ABL/AVB gates. Do not re-open broad ARC/proxy/display audits.

— END —