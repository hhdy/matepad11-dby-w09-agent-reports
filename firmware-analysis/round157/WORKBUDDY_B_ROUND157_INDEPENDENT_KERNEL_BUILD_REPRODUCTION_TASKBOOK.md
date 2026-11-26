# ROUND157 — WorkBuddy Window B: independent full kernel build reproduction

- Executor: WorkBuddy Window B (2号 Agent), separate WorkBuddy chat from Window A.
- Both local agents use WorkBuddy; no different AI product is required.
- Use only Window B's own frozen ACK/23-patch workspace and build environment.
- Never access Window A's private workspace, build output, raw ABL or local logs.
- Task type: independent source reproduction and formal full kernel build. No device operations.

## 1. Purpose

ROUND156 established three internally valid candidate DTB variants. The common minimal no-overlay base is the preferred build baseline for first-boot preparation, with debug UART as an optional variant. ROUND157 now requires the first formal full kernel build and independent reproduction.

Window A will publish a small RAM DTS patch at:
firmware-analysis/round157/AI1_R157_RAM_DTS_PATCH.patch
and a report containing the exact source tree SHA and build target.

Do not start from Window A's modified files or private output. Recreate the same source content independently.

## 2. Source identity and patch procedure

- ACK: android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9.
- Pre-change 23-patch source tree SHA: afe9517f8062b96bfeb5b4dd5714942861e6a44b.
- 23 patches: verify all patch SHA-256 values against identity.json and replay 23/23 without fuzz/reject.
- RAM/comment patched expected source tree SHA: c56d93eafa35057d65176db6594d67d5144868a0.
- RAM-patched DTB expected 108680 B / SHA-256 9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60.

Use your own frozen source workspace, apply the published ROUND157 patch from GitHub when Window A publishes it. If the patch is not yet available, reconstruct only from the exact published ROUND154 Window A diff and verify the resulting source tree SHA equals c56d93eafa35057d65176db6594d67d5144868a0. If it does not, stop and report differences; do not force a match. Do not read Window A's local workspace.

## 3. Independent full build

Use a fresh isolated output directory and same proven target/config/toolchain as Window A:
tools/bazel build //common:dby_w09 --jobs=2

Record exact launcher, full source SHA, config SHA, patch replay and hashes, Bazel/Kleaf/clang versions, dependency/cache provenance, full log and exit code.

Output hashes/sizes must include:
- Image;
- dby-w09 DTB;
- vmlinux/BTF;
- modules and module archive;
- System.map and Module.symvers;
- module-signing certificate/material identity, without publishing the certificate bytes or private key.

Do not treat an entirely cached result as a fresh independent build. Record Bazel cache action evidence. Do not delete or overwrite ROUND140 outputs.

If the source tree identity differs from expected or the build fails, stop and report the exact mismatch/failure. No opportunistic code fix in this task.

## 4. DTB and source equivalence checks

- decode the DTB produced by this full kernel build;
- verify the 3 RAM windows and 18 reserved-memory entries;
- verify UFS host/PHY and all supply/clock/reset/interconnect/power-domain/OPP references;
- verify candidate /chosen is empty;
- compare source tree SHA, DTS blob SHA and DTB bytes with Window A only after Window A publishes its report and patch;
- explain any differences from generated signing certificate, BTF or build nondeterminism.

## 5. Build handoff assessment

Give one verdict:
- both full builds reproducible and ready to begin offline boot-image package design;
- build technically passes but artifact differences need reconciliation;
- build blocked by an environment/dependency/source issue.

Do not make a boot image, DTBO container or vbmeta image. The next package phase will require an ABL/AVB and restoration go/no-go.

## 6. Deliverable

Publish:
firmware-analysis/round157/WORKBUDDY_B_ROUND157_INDEPENDENT_KERNEL_BUILD_REPRODUCTION_REPORT.md

Include exact source identities, build logs summary, output hashes, DTB validation, independent comparison, and blockers. Read back and verify blob/content, then STOP.

## 7. Prohibitions

No Window A workspace/private logs/raw binaries. No device/ADB/root/fastboot/recovery/partition reads or writes. No flash, reboot, temporary boot. No source change outside the exact RAM DTS patch. No signing/AVB bypass/key handling.

— END —