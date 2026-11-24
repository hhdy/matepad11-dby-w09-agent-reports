You are the second independent AI and now own the continuous Stage-A implementation for Huawei MatePad 11 DBY-W09.

Repository: https://github.com/hhdy/matepad11-dby-w09-agent-reports
Your ONLY write branch: `ai-parallel/stagea-port-until-boot`
Master task: `kernel-baseline/round61/ROUND61_LONG_RUNNING_STAGEA_MISSION.md`
Progress log: `kernel-baseline/round61/PROGRESS.md`

This is a LONG-RUNNING IMPLEMENTATION MISSION, not a one-report review. Read the entire task first, inspect current main + ROUND58/59/60 artifacts, then execute the first unblocked phase. Do not stop after writing a report. Commit each meaningful phase, update PROGRESS.md, and immediately continue to the next unblocked phase on the same branch.

Fixed ACK source: tag `android17-6.18.33_r00`, exact commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`. First compile the ACK-derived DBY-W09 Image. Do not start DerpFest Android 17 until Stage A boots and passes storage/basic-hardware acceptance.

Priority order:
1. Real disposable ACK worktree; apply the actual ROUND32 → ROUND57 → ROUND36 → ROUND52-0001 → ROUND33 → ROUND52-0002 patches with git apply; run checkpatch/diff checks.
2. Real UFS dt_binding_check and negative schema fixtures.
3. Reuse ROUND58 Kleaf target/config checker, perform Bazel query/cquery and actual Kconfig resolution.
4. Compile the full DBY-W09 Image target. Diagnose errors and continue fixing/rebuilding until successful where your authorized build environment permits.
5. Independently close board DTS, memory handoff, physical power-supply and HOS ARC/proxy gaps before DTB/boot candidate creation.
6. Validate legacy boot v2 + separate ramdisk + AVB, then prepare a recoverable first-boot plan.
7. Obtain explicit approval before any device boot/write operation and collect actual boot/UFS/storage/hardware evidence.

ROUND16/17 WorkBuddy sandbox issues are being handled separately by the user's local Agent. Do not investigate WorkBuddy policy, do not ask the user to open guessed menus, and do not wait idle for that local task. Use an execution environment legitimately available to you. If no Linux build runtime is available, do not invent success: finish all source/patch/script/CI tasks possible and report the exact external blocker.

Hard boundaries:
- Never modify main, firmware-audit-v1, ack18-dby-w09-dts-draft or PR #1.
- Never guess RAM ranges, PMIC supply inputs, AVB descriptors or boot-image layout.
- Never flash, write partitions, unlock/root, bypass security or disable security tools.
- Treat source-context replay and synthetic tests as design/static evidence only.
- Keep committing to your dedicated branch, maintain PROGRESS.md, and continue to the next unblocked phase until Stage A is genuinely accepted or only user-controlled hardware/host action remains.

Start now. Do not respond with a plan alone.

Primary AI has also added `kernel-baseline/round62/round62_same_device_abl_bootv2_ramdisk_dtbo_reference.md` on main. Read it for Phase E/F only. It is a same-device public Linux cross-reference, not proof of this user's HOS4.3 ABL behavior. It reports `fastboot boot` refusal on a tested setup, boot header v2 + separate ramdisk, and a required /rootparam overlay; do not copy its image hashes, sizes, offsets, HOS4.2 assumptions or AVB footer values. Continue Phase A–D compilation even while these packaging gates remain open.


New mandatory item: read and integrate ROUND63 `vdda-phy-always-on` finding from main report `kernel-baseline/round63/round63-ufs-phy-always-on-lifecycle-compatibility.md`. Independently validate both ROUND63 patch drafts, apply them in the disposable pinned ACK worktree, run PHY dt_binding_check/checkpatch/compile, and test both property paths. Do not treat the primary draft as validated. See the full requirements appended to ROUND61_LONG_RUNNING_STAGEA_MISSION.md.
