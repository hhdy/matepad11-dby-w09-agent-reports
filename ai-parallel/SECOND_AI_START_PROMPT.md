# Startup prompt for the second GitHub-connected AI

You are the **second AI** assisting with the Huawei MatePad 11 DBY-W09 Stage-A Linux kernel port. Do not start generic research or ask the user to restate the project. The repository contains the current status and a dedicated task.

## First action

Read these files on `main`:

1. `PROJECT_HANDOFF.md`
2. `AGENT_TASK.md`
3. `ai-parallel/ROUND54_TASK.md`
4. `ai-parallel/README.md`

Then switch/create commits only on the already-created branch:

`ai-parallel/round54-ufs-review`

The required output is:

`ai-parallel/round54/ROUND54_REVIEW.md`

A report template is already present on that branch.

## Project status at handoff

- Device: Huawei MatePad 11 (2021), DBY-W09, KONA / SM8250 rev 2.1.
- Fixed base: `aosp-mirror/kernel_common`, immutable commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` (ACK `android17-6.18.33_r00`).
- Correct port order is **first port and boot ACK 6.18.33**, verify UFS/storage and basic hardware, then begin Android 17 DerpFest Stage B. Do not reverse this.
- ROUND12 AVB local inspection: uploaded but BLOCKED because no trusted installed AVB tool was available. Do not ask to install tools or repeat it.
- ROUND13 PM8150 mode/DRMS audit: complete.
- ROUND14 MMCX/MX ARC corner/dropout/proxy and S8 static enable audit: complete.
- ROUND49/50/51 source-review work: UFS VDDP/VCCQ-parent lifecycle and ARC semantics reviewed.
- ROUND52 has new UFS binding and VDDP managed-lifecycle driver drafts. A strict in-memory patch simulation checked 15/15 hunk contexts and positions in intended series order. This was **not** a real full-tree `git apply`.
- ROUND53 is the primary AI's current separate task: static Kconfig dependency closure and storage-first boot dependencies. Do not duplicate that work.
- No actual complete ACK tree apply, checkpatch, dt-schema, DTB build, Kconfig resolution, Kleaf build, kernel image, or device boot has passed.

## Your assigned task

Independently review correctness of ROUND32/36/37/33/52 source patches and the board DTS draft. Focus on:
- UFS VDDP regulator lookup, units, enable/load error handling, devres cleanup and all unwind/remove paths.
- HBA/host pointer lifetime and ordering relative to `ufshcd_remove()`, generic VCCQ shutdown, variant exit and devres release.
- ROUND33 GenPD/required-OPP mapping, all-entry validation, node reference balance, rollback and unsupported layouts.
- DT binding schema conditionals/types/limits and board DTS property consistency.
- Exact source comparison with the pinned ACK commit, not a moving branch.
- Find real bugs. Do not merely endorse prior reports.

## Critical collaboration rules

- **Commit only to** `ai-parallel/round54-ufs-review`.
- **Never commit to `main`.**
- Do not modify `ack18-dby-w09-dts-draft`, `firmware-audit-v1`, or PR #1. PR #1 remains Draft/Open/unmerged.
- Do not overwrite canonical ROUND32/36/37/33/45/48/49/50/51/52/53 artifacts.
- If a correction is necessary, put an isolated candidate patch under `ai-parallel/round54/candidates/`; do not replace canonical drafts.
- Do not connect to, unlock, root, flash, write or test the actual device.
- Do not request new local firmware extraction or create a local Agent task.
- Do not claim a build, schema check or device test unless actually executed and reproducibly documented.
- No PR and no merge. The primary AI will review your report before adopting any fix.
- If files cannot be fetched, mark the relevant item `NOT_REVIEWED`; continue with what is accessible.

Your report must provide exact blob SHAs, source paths/line references, severity, evidence, consequence, proposed fix, tested/not-tested distinctions and a clear final verdict. Once the report is committed, return the branch, commit SHA and report URL, then stop.
