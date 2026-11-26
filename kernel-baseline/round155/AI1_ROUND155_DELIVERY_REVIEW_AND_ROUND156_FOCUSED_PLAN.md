# AI1 ROUND155 Delivery Review and ROUND156 Focused Plan

- Reviewer: 1号 AI (ChatGPT)
- Date: 2026-11-27
- Candidate: ACK android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9
- RAM-patched candidate DTB: 108,680 bytes; SHA-256 9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60
- No device write, flash or reboot was performed in this review.

## 1. ROUND155 delivery review

### WorkBuddy Window A — exact boot-chain capture

Report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round155-readonly-bootchain-backup/firmware-analysis/round155/WORKBUDDY_A_ROUND155_READONLY_BOOTCHAIN_PARTITION_CAPTURE_REPORT.md

Blob: 07ed0907fe1a008f115b20aa469d4fd8c3758340

- Root access remained available through the existing KernelSU path.
- 86 by-name names resolved to 86 unique block nodes.
- 18 of 18 requested boot-chain targets were present and captured.
- Every capture passed exact byte-count, host SHA-256 versus independent device-side second-read SHA-256, and local readback SHA-256 checks.
- Ten key targets have a verified second copy on a separate host volume.
- Exact live ABL, XBL and xbl_config were captured locally. The compressed ABL payload was decompressed and hashed.
- The ABL contains code references to board/msm/pmic matching, boot-v2 DTB parsing, DTBO table/overlay handling, and /memory update routines.
- The live vbmeta_cust anomaly was confirmed.
- No write, reboot, fastboot, recovery, user-data read or full-UFS dump occurred.

Limitation: ABL analysis currently consists mainly of direct instruction-to-string xrefs and implementation strings. It does not yet prove the complete call graph, branch conditions, optionality of DTBO, target-path support, the exact /memory reg update semantics, or Huawei-specific AVB enforcement.

### WorkBuddy Window B — first-boot minimum and candidate overlay

Report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round155-candidate-overlay-minimal-plan/firmware-analysis/round155/WORKBUDDY_B_ROUND155_CANDIDATE_SPECIFIC_DTBO_MINIMAL_OVERLAY_REPORT.md

Blob: 81e2d06c28f8462f2c179aef28eb247273293850

- Candidate RAM-patched DTB identity matches ROUND154.
- It contains timer/GIC/PSCI/PDC, GCC/RPMh, PMIC regulators, UFS host and UFS PHY. All listed UFS supply/clock/reset/interconnect/power-domain phandle edges resolve.
- UFS host and PHY are status=okay.
- /chosen remains empty and requires bootloader-supplied bootargs/initrd.
- A 199-byte target-path overlay that enables the existing debug UART applies with host fdtoverlay RC=0 and changes only UART status. RAM and all 18 reserved-memory entries remain byte-identical.
- This supports a no-overlay technical hypothesis, but host fdtoverlay success does not prove Huawei ABL skip/apply behavior or proprietary ufdt compatibility.

### 2号 AI — ROUND155 strategy review

Report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round155-custom-dtbo-bootchain-plan/firmware-analysis/round155/AI2_ROUND155_DTBO_SELECTION_AND_FIRST_BOOT_STRATEGY_REPORT.md

Blob: 9da92e98e2022666b036610fa6f1e6ae369163d8

The review correctly rejects flashing the ROUND154 candidate as-is. Its statement that exact ABL is unavailable is superseded by the Window A ROUND155 live partition capture. It must be refreshed using the new ABL findings.

## 2. Consolidated technical status

1. Stock Entry 2/8 remain incompatible with the current minimal candidate in the tested host libfdt path.
2. Candidate RAM and UFS baseline is materially closer to a first-boot DTB. A no-overlay strategy is technically plausible but not yet proven by ABL control flow.
3. Exact live ABL is now available in Window A's local workspace.
4. ABL may update /memory after the base DTB is loaded. We must determine whether it clears/replaces existing reg tuples, appends regions, or skips an update for a non-zero map. This is a critical check before relying on explicit RAM tuples.
5. The ABL DTBO selection and overlay path must be traced: whether an overlay can be skipped, how index 2 is selected, whether failure aborts boot, and whether its ufdt implementation supports target-path.
6. Root vbmeta reports flags=3. Under AOSP definitions bit0 is HASHTREE_DISABLED and bit1 is VERIFICATION_DISABLED. Standard libavb semantics say verification-disabled means descriptors are not processed. This does not yet prove that this Huawei ABL follows the same path or does not perform extra checks.
7. The live bootargs report androidboot.verifiedbootstate=orange. AOSP defines orange as an unlocked state, but the exact source/emission path and its relation to the ABL verification decision still need to be established.
8. ROUND155 captured 18 boot-chain partitions with verified bytes and hashes; ten have a second local copy. This is a strong backup step, but it is not a tested restore rehearsal or a complete copy of all 86 partitions/GPT metadata.

## 3. ROUND156 narrow tasks

- WorkBuddy Window A: offline exact-ABL control-flow and AVB analysis using only its locally captured ROUND155 binaries. No additional device reads.
- WorkBuddy Window B: scratch-build and compare no-overlay base, UART-enabled base, and the tested target-path UART overlay. No access to Window A.
- 2号 AI: update the first-boot recommendation using the new ABL capture, candidate minimum report and official AVB definitions.

## 4. Flash decision

ROUND155 does not yet authorize a flash. There is real progress: verified boot-chain copies, the exact live ABL, a reproducible RAM-patched DTB, and a candidate that already contains the essential early-boot/UFS tree.

The remaining gates are now focused:
- prove ABL RAM mutation does not duplicate or corrupt the explicit three-window map;
- prove ABL's DTB selection and optional/mandatory DTBO behavior;
- determine whether flags=3 and orange state allow the proposed package under this exact ABL;
- prepare and parse a size-bounded candidate boot image;
- establish a credible stock restore route using the verified backups and a tested way to reach the restore environment.

Do not write an unverified image. The user's request to accelerate is acknowledged; it is not a reason to risk an unrecoverable device.

— END —