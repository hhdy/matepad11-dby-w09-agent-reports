You are assigned ROUND58 as the second independent AI for the Huawei MatePad 11 DBY-W09 Stage-A kernel port.

Repository: https://github.com/hhdy/matepad11-dby-w09-agent-reports
Your branch ONLY: ai-parallel/round58-kleaf-target-audit
Task: kernel-baseline/round58/ROUND58_TASK.md

This is an implementation task, not another review-only task. Create a concrete pinned-source Kleaf full-kernel target patch candidate, a tested .config validation helper with unit tests, and a detailed post-ROUND17 build runbook. Work only in your dedicated branch. Do not edit main, firmware-audit-v1, protected DTS, canonical patches or PR #1.

Fixed ACK baseline: android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a. DBY-W09 must first boot this ACK-derived 6.18.33 kernel and pass storage/basic hardware acceptance; only then may DerpFest Android 17 begin.

Read all referenced rounds in ROUND58_TASK.md before implementation. The key decision is full custom kernel_build without base_kernel, using gki_defconfig plus the storage-first fragment in post_defconfig_fragments. First target is Image-only; no guessed DTB path or boot image. Keep early storage drivers built-in, do not invent module outputs, and distinguish a build candidate from a successfully compiled or booted kernel.

Commit concrete candidate files and tests to your branch. Upload no changes to any other branch. Stop after your report is committed.
