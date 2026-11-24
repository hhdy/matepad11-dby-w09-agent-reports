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
