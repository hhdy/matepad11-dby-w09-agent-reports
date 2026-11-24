# ROUND55 — Stage-A execution gate matrix and critical-path separation

**Date:** 2026-11-24  
**Status:** PLANNING CONSOLIDATION — NO SOURCE PATCH, BUILD TARGET, CONFIG, DTB, OR IMAGE WAS MODIFIED OR EXECUTED  
**Device:** Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 rev 2.1  
**Immutable ACK baseline:** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

## 1. Purpose

This round converts the existing Stage-A evidence into an execution sequence that separates:

1. work that can proceed once a source/build workspace exists;
2. checks that require a board DTS and trusted memory description;
3. boot-image / AVB / ramdisk gates that matter before a device boot but do not need to block all source-level integration work.

It is intended to stop repeated static research from obscuring the next concrete action. It does not create a new firmware scan and does not duplicate the second AI's ROUND54 review.

## 2. Current proven state

| Area | Current state | Evidence boundary |
|---|---|---|
| ACK source identity | Fixed to tag `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` | Source reference is pinned; the user's local worktree is not yet confirmed |
| UFS dual-GenPD patch | Draft exists; all-entry OPP/required-opps validation and fail-closed two-domain policy were source reviewed | Hunk context checks are not a full worktree apply/build |
| UFS VDDP / binding patches | ROUND52 drafts exist | 15/15 strict in-memory ordered hunk-context simulation; not actual `git apply` |
| Storage-first Kconfig fragment | ROUND53 static dependency chain reviewed; hidden symbols `GENERIC_MSI_IRQ`, `SCSI_DMA`, `OF_RESERVED_MEM` removed from direct assignments; `PM_OPP` selection-derived | No Kconfig resolver, `olddefconfig`, or final `.config` |
| Kleaf build model | Pinned ACK uses Kleaf/Bazel; DBY-W09 design prefers full custom `kernel_build` without `base_kernel`; storage fragment belongs in `post_defconfig_fragments` | No synced full manifest workspace or build target |
| Local source/build environment | ROUND15 read-only inventory taskbook exists | Not dispatched; no local inventory report |
| Second AI review | ROUND54 task and dedicated branch/template exist | No completed review report or candidate patch |
| Board memory handoff | HOS4.3 base FDT inventory has no ordinary `/memory` node and has 34 reserved-memory children; target final post-ABL FDT / EFI-stub entry remains unknown | No trusted final memory map; do not invent RAM ranges |
| AVB / ramdisk | ROUND12 AVB inspection remains blocked; ramdisk contents and descriptor relationships remain unresolved | Do not infer footer/vbmeta policy from magic or file size |
| Device boot | No ACK 6.18.33 build or device boot has occurred | Runtime status unknown |

## 3. Critical distinction: source/build gate versus first-boot gate

### 3.1 What does not need to wait for AVB resolution

The following can be performed in an isolated, disposable ACK source workspace once the local environment and source tree are available:

- verify the exact ACK source commit and reproducible workspace manifest;
- apply and inspect source-only driver/schema patch series;
- run `git diff --check` and `checkpatch.pl` against the actual patches;
- run binding-schema checks that do not depend on guessed board memory ranges;
- resolve the storage-first Kconfig fragment and inspect the generated final `.config`;
- compile a stock ACK sanity target if useful, then compile the DBY-W09 full custom kernel target once the required source files and target definitions are reviewed;
- compile isolated driver objects or the full kernel to catch C/API errors.

These steps do not make a board image safe to flash or boot. They can identify and fix build defects earlier, without claiming runtime readiness.

### 3.2 What remains blocked before using a device DTB / attempting first boot

The board's final memory handoff cannot be guessed. Before promoting the board DTS into a boot candidate, obtain trusted evidence that one of these paths is true:

1. **Classic ARM64 FDT path:** final enabled FDT node(s) with `device_type = "memory"` and trusted `reg` or `linux,usable-memory` ranges are present; or
2. **Real Linux EFI-stub path:** actual entry is through the Linux EFI stub and the final `/chosen` contains the complete trusted UEFI system-table and memory-map metadata required by ACK.

A UEFI ABL or Qualcomm EFI_KERNEL_PROTOCOL alone does not establish Linux EFI-stub entry. The 34 `/reserved-memory` entries are a separate reservation database and do not substitute for system RAM. Do not borrow addresses from another SM8250 tablet or HOS4.2 DTS.

The boot-image path also remains gated by ROUND12: verify the actual boot header v2 / separate ramdisk / DTBO / vbmeta relationship and the correct image metadata using a trusted, already available inspection path. Do not assume a modern `vendor_boot` or `init_boot` layout. The actual ramdisk contents, first-stage module-loading route, fstab, DM-verity/FEC descriptor requirements and EROFS content remain unresolved.

## 4. Execution sequence after ROUND15

### Gate 0 — Existing local capability inventory

Input: `firmware-analysis/round15/AGENT_TASK.md`.

Expected result: one sanitized report showing whether a complete matching source tree and a Linux-capable build environment already exist.

- If a complete source tree and environment exist, verify the exact refs and cleanliness before use.
- If source exists but environment is incomplete, do not modify it; decide on a separate build-host plan.
- If environment exists but source is missing, plan a pinned source workspace.
- If neither exists, the next user decision is how to provide an authorized build host/workspace.

ROUND15 is read-only. It does not grant permission to sync, install, patch, or compile.

### Gate 1 — Disposable full source workspace

Use the exact ACK common source commit and record `repo manifest -r` plus every Kleaf/toolchain project revision used. Verify compiler and Rust revisions against ROUND39 before building.

Do not use the legacy `build.config.gki.aarch64` / `build/build.sh` route; the pinned ACK source deliberately disables it.

Do not write to the report repository's canonical patch drafts, protected DTS branch, or firmware Agent branch while validating a disposable source tree.

### Gate 2 — Patch application and source checks

Use the exact ordered series:

1. ROUND32 UFS schema coverage patch
2. ROUND36 compatible-scoped dual-power-domain schema patch
3. ROUND52-0001 UFS VDDP / VCCQ-parent binding patch
4. ROUND37 board UFS dual-GenPD DTS delta
5. ROUND33 UFS dual-GenPD / required-OPP driver patch
6. ROUND52-0002 VDDP managed lifecycle driver patch

The series order is based on the existing ROUND38 manifest and ROUND52 context simulation. The actual disposable-worktree operation must still run `git apply --check`, then apply, then `git diff --check`, and record exact outputs. The second AI's ROUND54 report must be reviewed before adopting any suggested correction to canonical drafts or the candidate series.

### Gate 3 — Schema and device-tree validation

- Run `dt_binding_check` for the modified UFS bindings.
- Add the board DTS to an actual kernel DTS source path only after its source structure, include paths and memory strategy are reviewed.
- Run `dtc` and `dtbs_check` on the exact final board tree; capture all warnings and distinguish pre-existing upstream warnings from new warnings.
- Do not claim the current repository `.dts.draft` is already a build input.

A standalone schema pass does not prove the board DTB is bootable. A successful DTB compile does not close the memory/bootloader handoff question.

### Gate 4 — Kconfig resolution and kernel compilation

Use the full custom kernel target pattern selected by ROUND41:

- no `base_kernel` for the first storage-first build;
- `gki_defconfig` as the base;
- the storage-first device fragment in `post_defconfig_fragments`;
- required early storage/clock/power/interconnect/SMMU dependencies must resolve to built-in `=y`;
- do not use `# nocheck` to hide missing critical symbols;
- inspect and archive the final `.config`, not merely the fragment text;
- build Image, System.map, vmlinux, symvers and built-in metadata; record modules only as applicable.

An optional stock `//common:kernel_aarch64_dist` build is a toolchain sanity check, not a DBY-W09 device kernel. The full custom target and ABI/KMI checks must be reported separately; using `gki_defconfig` does not establish official GKI certification.

### Gate 5 — Boot packaging and controlled first boot

Do not define a generic modern boot-image target by assumption. Before assembling a device boot candidate, close:

- exact boot header v2 layout and image size/alignment;
- separate ramdisk partition handling;
- DTB/DTBO composition and selected DTBO entry;
- vbmeta/footer descriptor coverage and verification chain;
- actual first-stage ramdisk content, fstab, module loading or built-in strategy;
- trusted system RAM and reserved-memory handoff.

Only after these inputs are evidenced can a reversible, device-specific boot plan be reviewed. No flashing or partition writes are authorized by this matrix.

### Gate 6 — Stage-A acceptance

Stage A is complete only after the tablet actually boots the ACK-derived 6.18.33 kernel and evidence confirms:

- kernel version and boot logs;
- UFS host / PHY / required storage path initialization;
- storage detection and required root/system partitions mounted;
- basic hardware acceptance appropriate to the agreed first milestone.

Compilation alone is not Stage-A completion. Stage B Android 17 DerpFest remains deferred until this acceptance.

## 5. Current action ownership

| Owner | Assigned work | Write scope |
|---|---|---|
| Primary AI / ChatGPT | Continue Stage-A integration planning and public/pinned-source work; review second-AI findings before adoption | `main` canonical reports/docs only; do not touch protected DTS branch or PR #1 |
| Second GitHub-connected AI | ROUND54 independent UFS patch/schema/DTS/lifecycle review | `ai-parallel/round54-ufs-review` only |
| Local read-only Agent | ROUND15 existing source/build environment inventory | One sanitized text report on `firmware-audit-v1` only |

The second AI's dedicated branch currently has a report template, not a completed review. ROUND15 currently has a taskbook, not an execution report. Neither workstream should be represented as complete until its report is uploaded.

## 6. Hard boundaries

- Stage A remains ACK 6.18.33 first; DerpFest Android 17 Stage B only after Stage-A boot and storage/basic-hardware acceptance.
- Do not repeat Android 12L general research or completed ROUND11/13/14 FDT scans.
- Do not infer device runtime state from source review.
- Do not claim real `git apply`, dt-schema, DTB, Kconfig, Kleaf, build, packaging or boot success unless the exact operation was executed and logged.
- Keep PR #1 Draft/Open/unmerged and leave `ack18-dby-w09-dts-draft` unchanged unless separately authorized.
- The local Agent remains read-only and must not install tools, sync source, compile, or operate the device.

## 7. Immediate next actions

1. Dispatch ROUND15 to the local read-only Agent.
2. Give the second AI the startup prompt in `ai-parallel/SECOND_AI_START_PROMPT.md`; let it complete ROUND54 on its dedicated branch.
3. Once ROUND15 returns, decide whether the next blocker is an existing source checkout, a Linux build host, or both.
4. Then move to Gate 1–4 in a disposable ACK workspace while keeping AVB/memory/ramdisk as first-boot gates.

**Bottom line:** The project has enough pinned-source design to stop endlessly expanding the research backlog. The next acceleration comes from confirming the existing build environment, completing the independent UFS review in parallel, and executing the real disposable-worktree validation sequence. No kernel compile or device boot is claimed by ROUND55.


## Status correction — ROUND15 complete; ROUND16 authorized (2026-11-24)

ROUND15 has now completed and uploaded its report. It found no existing ACK worktree and no evidenced Linux build host/toolchain; verdict `NO_EXISTING_BUILD_WORKSPACE_FOUND`. D: had 325.4 GiB free at scan time. The WSL distribution listing remained NOT_RUN because the host security program blocked the query.

The user explicitly authorized environment deployment. ROUND16 is now the active local Agent task:
`firmware-analysis/round16/AGENT_TASK.md`.

It provisions WSL2 Ubuntu 24.04 on D:, installs minimal official Ubuntu host packages, syncs only the official `common-android17-6.18` kernel manifest and pins the common source to the immutable ACK .33_r00 commit. It reserves at least 100 GiB free on D: and stops before patch application or compilation. It must not bypass the host security block if it recurs.

The second AI's ROUND54 review remains independent and must be completed on its dedicated branch. No kernel compile or device boot is claimed.


## Status correction — ROUND16 blocked; ROUND17 / ROUND58 parallel work (2026-11-24)

ROUND16 has now completed with terminal verdict **BLOCKED_BY_HOST_SECURITY_POLICY**. Its sanitized report is uploaded at `firmware-analysis/round16/round16_wsl_ack_workspace_deployment.txt` on `firmware-audit-v1`. No distro install, apt, repo sync, ACK pin, source patch, Kconfig, schema, build or device operation occurred.

ROUND16 corrected ROUND15's earlier uncertainty:
- Store WSL Appx 2.7.3.0 is installed.
- A WSL2 distribution named Ubuntu is already registered on C:; its distro release is UNKNOWN.
- VirtualMachinePlatform is Enabled.
- wsl.exe is blocked by the endpoint's Program Blacklist.
- the local Agent process was not elevated.
- D: had about 325.3 GiB free.
Do not call this a no-WSL system. The older legacy WSL optional feature and HypervisorPlatform being disabled are not proven blockers.

**Current local Agent work is ROUND17, not ROUND16.** User must manually clear only the wsl.exe Program Blacklist entry and relaunch the Agent elevated before ROUND17 may run. The existing C: Ubuntu must be preserved; install a separate Ubuntu-24.04 at D:\WSL\Ubuntu-24.04. Round17 taskbook and start prompt: `firmware-analysis/round17/AGENT_TASK.md` and `START_PROMPT.md`. Store WSL should first be verified; do not blindly reinstall/enable legacy features. Round17 still stops before patch application and compilation.

**Second AI active implementation task is ROUND58** on `ai-parallel/round58-kleaf-target-audit`:
- create a concrete pinned-source no-`base_kernel` full-image Kleaf target patch candidate;
- provide a tested final .config validation helper and tests;
- prepare exact post-ROUND17 patch/config/Image build runbook.
The first target must not invent DTB/DTBO/boot-image inputs because board DTS integration and memory handoff remain unresolved. It must work only on its dedicated branch.

Primary AI will review ROUND58 and prepare the canonical integration path. The next actual local build round after ROUND17 is expected to apply the ordered series (ROUND32 → ROUND57 → ROUND36 → ROUND52-0001 → ROUND37 once a real DTS path is ready → ROUND33 → ROUND52-0002), validate schemas and Kconfig, then compile the full DBY-W09 Image using the custom Kleaf target. No kernel compile is claimed yet.

## ROUND59 ordered patch integration result (2026-11-24)

A stricter in-memory exact-source replay was completed for the full UFS patch series. Source blob identities were verified against the fixed ACK commit; all 16/16 patch hunks matched exact context and declared new line anchors in this order:
ROUND32 → ROUND57 → ROUND36 → ROUND52-0001 → ROUND37 (review-only DTS fixture) → ROUND33 → ROUND52-0002.

ROUND52-0002 was correctly applied across both `drivers/ufs/host/ufs-qcom.h` and `ufs-qcom.c`. Post-application text assertions passed for the SM8250 compatible, eight clocks/names, supply bindings, dual-domain schema, MMCX-first/GCC-second fixture, required-OPP mapping and VDDP lifecycle.

ROUND59 found and corrected the ROUND57 patch's malformed hunk header. Current main blob is `3656f05ad01d54452b83591b762faaa71a16f592`, hunk `@@ -165,13 +165,15 @@`. The earlier blob `f282a695...` must not be used.

**Boundary:** the replay was performed in memory from exact GitHub source blobs. It is not real `git apply --check`, `git diff --check`, checkpatch, dt_binding_check, dtbs_check, Kconfig, Bazel or a build. ROUND37 still targets the review-only .dts.draft fixture rather than a real ACK DTS path. Full detail: `kernel-baseline/round59/round59_ufs_patch_series_exact_source_integration.md`.

The local Agent is WorkBuddy using DeepSeek V4.1 Flash. ROUND17 lets WorkBuddy itself identify its execution-policy/approval path; do not send the user to an unverified Windows menu and do not bypass or retry blocked commands. The second AI remains on ROUND58 Kleaf implementation.


## ROUND60 — primary review of second-AI Kleaf implementation (2026-11-24)

Second AI completed ROUND58 on `ai-parallel/round58-kleaf-target-audit`. It delivered a no-`base_kernel` Image-first full custom Kleaf target candidate, a deterministic final .config validator and nine synthetic unit tests, plus a build runbook.

Primary AI review in `kernel-baseline/round60/round60_primary_review_round58_kleaf_and_config_validator.md`:
- pinned ACK BUILD insertion context exact match, and copied 132-line storage-first fragment matches the canonical main fragment;
- no-`base_kernel` full custom target is consistent with the pinned `yukawa` pattern and ROUND41 storage-first driver requirement;
- Kleaf manifest-declared `main-kernel-2026` config documentation confirms post_defconfig_fragments are applied after defconfig, then olddefconfig, with final config checks;
- config checker implementation/tests inspected; second AI reports nine synthetic tests passed;
- actual Git apply, buildifier, Bazel query, Kconfig, final .config validation and compile remain NOT_RUN.

ROUND60 runbook note: use `set -o pipefail` when piping Bazel output through `tee`; avoid repeating the same target build when no source/config changed. Four Bazel jobs is only a conservative starting CPU cap; measure effective WSL memory before any memory cap.

ROUND17's latest report confirms the wsl.exe block is WorkBuddy's own default Program Blacklist in WorkBuddy 5.11.3.0, not the Windows OS security menu. Status remains BLOCKED_PENDING_USER_OR_ADMIN_APPROVAL; WorkBuddy has not yet removed/allowed the rule or invoked WSL again. User asked that WorkBuddy handle its own settings; keep progressing source-only kernel work without requesting OS security changes from the user.

ROUND59 exact-source patch replay is complete with 16/16 hunks; ROUND57 hunk corrected. Full-tree apply, schema, config, compile and device test remain NOT_RUN.
