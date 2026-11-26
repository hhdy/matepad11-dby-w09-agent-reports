# ROUND156 — WorkBuddy Window B: candidate base / UART / overlay variants

- Executor: WorkBuddy Window B (2号 Agent), separate WorkBuddy chat from Window A.
- Use only Window B's own ROUND154/155 workspace and candidate artifacts.
- Do not access Window A's ABL or raw backup workspace.
- Task type: offline scratch-only DTB/DTBO validation. No device or partition operations.

## 1. Purpose

ROUND155 proves the RAM-patched candidate has early timer/GIC/PSCI/PDC, GCC/RPMh, PMIC regulators, UFS host/PHY and closed UFS supply/clock/reset/interconnect/power-domain references. It also provides a 199-byte target-path overlay that enables the existing debug UART via host fdtoverlay.

Prepare byte-verified alternatives for the exact ABL decision, without guessing the ABL behavior or modifying the accepted source branch.

## 2. Workspace isolation

Use only Window B's own ROUND154/155 local artifacts and scratch directory. Do not use Window A's private paths, raw binaries or logs. Preserve the original candidate and ROUND155 outputs.

## 3. Required variants

A. No-overlay base: reproduce the 108,680-byte RAM-patched candidate DTB from source.

B. UART-enabled base: scratch rebuild with only the existing debug UART node status changed from disabled to okay. Preserve the same RAM tuples and all 18 reserved-memory entries.

C. RAM base plus target-path UART overlay: reproduce the 199-byte overlay from source and apply it to a fresh RAM-patched base.

For each variant record:
- source file/diff and SHA;
- build command and tool versions;
- DTB/DTBO size and SHA-256;
- full node/property diff;
- UFS host/PHY and supply/clock/reset/interconnect/power-domain closure;
- exact RAM tuples and reserved-memory byte identity;
- phandle set and collision check.

## 4. Cross-tests

1. Reproduce the target-path overlay apply test against a fresh base.
2. Negative test an unknown target path and verify FDT_ERR_NOTFOUND.
3. Confirm variants B and C differ from A by the same single UART status property and nothing else.
4. Confirm /chosen remains empty in all variants. List required bootloader-injected fields based only on the published live FDT: bootargs, initrd start/end, kaslr-seed and relevant androidboot state/index values. Do not invent values.
5. Compare variants for use if ABL permits no overlay versus if ABL requires a DTBO.
6. Do not create a DTBO container or boot.img until Window A's ABL control-flow report confirms selection/apply behavior.

## 5. Verdict

State which outputs are internally valid and which ABL questions remain outside Window B's evidence. Explicitly distinguish host fdtoverlay success from Huawei ABL compatibility. Do not label any variant flash-ready.

## 6. Deliverable

Publish:
firmware-analysis/round156/WORKBUDDY_B_ROUND156_CANDIDATE_FIRSTBOOT_DTB_VARIANTS_REPORT.md

Include exact hashes, commands, tool versions, full diffs and proof frozen inputs remain unchanged. Read back and verify, then STOP.

## 7. Prohibitions

No source branch change, accepted patch edit, full kernel/Image build, device/ADB/root/fastboot/recovery, partition read/write, flash, reboot or boot. No access to Window A's workspace.

— END —