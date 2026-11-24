# ROUND61 — Long-running Stage-A implementation mission: DBY-W09 ACK 6.18.33 to verified device boot

**Owner:** Second GitHub-connected AI (the independent implementation AI)  
**Dedicated branch:** `ai-parallel/stagea-port-until-boot` ONLY  
**Mission type:** Persistent, multi-phase implementation. Do not stop after producing one report or one patch.  
**Date:** 2026-11-24  
**Device:** Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1 / Snapdragon 865  
**Current milestone:** Stage A — port, compile, package and verify the ACK-derived 6.18.33 kernel.  
**Final Stage-A acceptance:** the tablet actually boots this kernel and passes UFS/storage plus agreed basic-hardware checks.  
**Stage B:** Android 17 DerpFest is strictly out of scope until Stage A is accepted.

---

## 0. What you are being asked to do

You are not being asked for another one-off review. You are now the **continuous Stage-A kernel implementation owner** on your own branch.

Keep working through the phases below in order. After completing a phase, immediately start the next phase that is not blocked by an external prerequisite. Commit progress continuously and maintain `kernel-baseline/round61/PROGRESS.md` as the single source of truth.

Do not stop merely because:
- a design note or patch candidate has been written;
- an in-memory patch simulation passes;
- a synthetic test passes;
- one review report is committed;
- the local WorkBuddy/WSL path is temporarily blocked.

The job is to turn the existing source-level work into a real, validated, compiled device-kernel implementation, and then bring it to the edge of a safe device boot. Resolve defects you discover, rerun affected tests, and record the exact evidence.

**Important honesty boundary:** a source/build AI cannot truthfully claim the tablet has booted without real device evidence. Complete every source/build/packaging task available to you. Device boot and hardware acceptance may require the user's local Agent, their physical tablet and explicit approval for any reboot/temporary boot/flash operation. Do not bypass that gate.

## 1. Branch ownership and safety contract

Work only on:
`ai-parallel/stagea-port-until-boot`

This branch was created from the current main branch and contains ROUND59/ROUND60 and the latest project handoff at task creation.

You may:
- create and update ROUND61 implementation files, scripts, patches, tests, reports and logs on this branch;
- fetch and reuse the completed second-AI implementation from `ai-parallel/round58-kleaf-target-audit`;
- create disposable source worktrees and temporary build outputs in your own permitted Linux build environment;
- correct or replace candidate patches on this branch when real tests demonstrate a defect;
- create a reproducible build script and, only if technically feasible and permitted, a CI workflow that does not require secrets or paid external services.

You must not:
- commit to or modify `main`, `firmware-audit-v1`, `ack18-dby-w09-dts-draft`, or any protected branch;
- edit or merge PR #1; it must remain Draft/Open/unmerged;
- overwrite canonical patch drafts on main. Copy them into your branch/worktree and record their exact blob hashes;
- upload raw HOS firmware, stock boot/ramdisk/DTBO images, private partition data, device serials, account identifiers or secrets;
- bypass host/security policies, alter endpoint controls, disable Defender/firewall, rename/copy blocked executables, or try alternate shells/wrappers to evade a block;
- access, unlock, root, flash, write partitions or issue device commands without a separately reviewed user-approved device-operation plan.

Keep the pristine ACK source baseline intact. All patches must be applied to a disposable copy/worktree.

## 2. Immutable baseline and project order

The only permitted kernel baseline is:

- ACK tag: `android17-6.18.33_r00`
- immutable `common` commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- upstream source: `https://android.googlesource.com/kernel/common`
- architecture: arm64

Do not substitute upstream Linux `v6.18.33`, a moving branch HEAD, or another ACK tag.

Overall order:
1. Complete Stage-A ACK-derived 6.18.33 device-kernel port.
2. Build and validate the kernel.
3. Close the device DTB/boot-chain/memory/AVB gates.
4. With user approval, perform controlled first boot and verify storage/basic hardware.
5. Only after Stage-A acceptance may anyone begin Android 17 DerpFest Stage B.

Do not research Android 12L, ColorOS or unrelated ROMs.

## 3. Existing evidence — reuse it, do not redo it

Read the current main copies before coding:

- `PROJECT_HANDOFF.md`
- `AGENT_TASK.md`
- `kernel-baseline/round55/stage-a-execution-gate-matrix.md`
- `kernel-baseline/round56/linux-build-host-deployment-decision.md`
- `kernel-baseline/round59/round59_ufs_patch_series_exact_source_integration.md`
- `kernel-baseline/round60/round60_primary_review_round58_kleaf_and_config_validator.md`
- `kernel-baseline/round32/`, `round33/`, `round36/`, `round37/`, `round38/`, `round41/`, `round45/`, `round49/`, `round52/`, `round53/`, `round57/`
- `config/dby-w09-ack18-storage-first.fragment.draft`
- `dts/dby-w09-ack18-board.dts.draft` and `dts/README.md`

Reuse these prior results:

### ROUND59
The ordered UFS patch set was replayed through an exact-context in-memory simulator: 16/16 hunks matched pinned source identities, including corrected ROUND57. This is NOT a real Git apply. Current patch order and source identities are recorded in ROUND59.

### ROUND58 and ROUND60
Second AI committed a candidate Kleaf target, a standard-library Python validator, nine synthetic tests, and a build runbook on `ai-parallel/round58-kleaf-target-audit`. Primary review ROUND60 passed the design/source-context review with command-runner clarifications. No real Bazel query, actual Kconfig resolution or compile has occurred.

Fetch and inspect these exact ROUND58 artifacts on its branch:
- `kernel-baseline/round58/0001-add-dby-w09-full-kernel-kleaf-target.patch`
- `kernel-baseline/round58/check_dby_w09_config.py`
- `kernel-baseline/round58/tests/test_check_dby_w09_config.py`
- `kernel-baseline/round58/round58_kleaf_target_implementation.md`

Do not assume these candidates are correct merely because ROUND60 passed a source-level review. Revalidate them with actual tools in the real pinned workspace and fix any failures on your branch.

### ROUND16 / ROUND17 local host status
ROUND16 could not enter WSL because WorkBuddy's command-safety/sandbox layer blocked `wsl.exe`. ROUND17 identified WorkBuddy 5.11.3.0 / sandbox-cli 5.11.4 as the policy owner; the local Agent is handling its own authorization path. No WSL distro deployment, Repo sync, ACK workspace or toolchain is yet evidenced.

Do not spend this task re-investigating WorkBuddy policy. Do not ask the user to navigate guessed Windows menus. Do not assume local WorkBuddy's environment is your execution environment. You may continue using a build environment legitimately available to you. If you have no Linux shell or no suitable execution facility, complete the source-level and reproducibility work that remains, and record exactly which real commands cannot be run; do not fabricate test output.

## 4. Phase A — make a real disposable ACK worktree and apply code patches

This is the first priority.

1. Establish a Linux-capable workspace in an execution environment you are actually authorized to use. Prefer the official Android kernel Repo manifest `common-android17-6.18` so manifest-managed Kleaf/Clang/Rust prebuilts are used. Do not download a whole AOSP/DerpFest platform tree.
2. Record:
   - `repo manifest -r`;
   - exact `common` HEAD and `git status --short`;
   - `MODULE.bazel.lock` hash;
   - exact build/kernel, bazel, rules_devicetree and compiler project revisions;
   - Clang and Rust versions from the manifest-provided toolchain.
3. Verify `common` is exactly `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`. If not, stop and correct the source pin before patching.
4. Preserve a pristine baseline; create a disposable worktree/copy at that exact commit.
5. Fetch the canonical patches by exact path and blob SHA and run the **real** `git apply --check` followed by `git apply`, one patch at a time, in this order:
   - ROUND32: SM8250 UFS compatible / eight-clock schema;
   - ROUND57: exact eight-entry `clock-names` constraint;
   - ROUND36: SM8250-scoped dual power-domain schema;
   - ROUND52-0001: UFS VDDP / VCCQ-parent binding declarations;
   - ROUND33: UFS dual-GenPD / required-OPP driver code;
   - ROUND52-0002: VDDP managed regulator lifecycle.
6. After each patch, record the exact command, exit code and affected paths. Finish with `git diff --check`, inspect the entire diff and run `scripts/checkpatch.pl` on the driver patches. Fix all new errors and justify any warning retained.
7. Do not include ROUND37 in the real kernel source patch sequence yet. ROUND37 only modifies the review-only file `dts/dby-w09-ack18-board.dts.draft`; it is not an upstream ACK DTS path and is not a device-tree build input. Keep it as a fixture until Phase E's board-DTS gate is legitimately closed.

A failure is not a stopping point: diagnose it against the pinned source, fix the candidate patch on your branch, rerun the failed check and all downstream checks affected by the change.

## 5. Phase B — real schema validation

Use the manifest-pinned kernel build environment and actual ACK source tree.

1. Run the kernel's `dt_binding_check` for the modified UFS binding files (`qcom,ufs.yaml` and `qcom,ufs-common.yaml`).
2. Capture the exact commands, tool versions, stdout/stderr, return codes and generated warnings.
3. Fix schema errors in your branch, preserving the intended scope:
   - SM8250 only gets exactly eight clocks and names;
   - only `qcom,sm8250-ufshc` may use the two-domain exception;
   - other Qualcomm UFS compatible paths remain one-domain;
   - supply/load properties retain required pairing and positive-load constraints.
4. Validate negative fixtures as well as positive fixtures. At minimum test: SM8250 with 8 clock names + 1/2 domains accepted; 7/9 names rejected; 3 domains rejected; non-SM8250 2 domains rejected; malformed supply/load pairs rejected.
5. Do not report the schema as passed on the basis of Python YAML parsing or synthetic JSON Schema alone. The kernel `dt_binding_check` result is the authoritative gate.

If the binding check exposes unrelated pre-existing upstream diagnostics, separate them from new errors and prove the changed schemas themselves are clean.

## 6. Phase C — integrate and verify the Kleaf build target

Reuse ROUND58 but do real integration.

1. Inspect the ROUND58 Kleaf patch and validator on their dedicated branch. Copy their contents into this branch's disposable ACK source workspace; preserve the original source files and hashes.
2. Apply the BUILD/config patch with real `git apply --check`, apply and `git diff --check`.
3. Confirm the manifest-pinned Kleaf API and module lock versions, not only a moving documentation branch.
4. Run buildifier (if provided by the manifest/toolchain) and the real Bazel/Kleaf target checks:
   - query the package and `//common:dby_w09` target;
   - verify the target rule and attributes are accepted;
   - inspect target files with `cquery --output=files`;
   - confirm the fragment is actually applied at `post_defconfig_fragments`.
5. The build is a full custom `kernel_build` without `base_kernel`, based on `gki_defconfig`. Keep early storage/PHY/clock/RPMh/ICC/SMMU dependencies built-in. Do not add `# nocheck` to hide missing symbols. Do not claim official GKI certification.
6. Retain the candidate's initial Image-focused scope. Do not guess a DTB, DTBO, boot.img, vendor_boot, init_boot or flash-package output.

If the Kleaf rule API rejects an attribute or output, inspect the exact pinned API and fix the target rather than abandoning it.

## 7. Phase D — actual Kconfig resolution and kernel compilation

This phase is the main deliverable: get a DBY-W09 storage-first Image to compile.

1. Use the real Kleaf target to generate the resolved final `.config`.
2. Run the ROUND58 `check_dby_w09_config.py` against that actual output; archive the complete PASS/FAIL output and final `.config` hash.
3. Independently inspect all storage-first dependencies and any silently downgraded symbols. Required early-storage/clock/power/interconnect/SMMU/DM/EROFS items must resolve to built-in `=y`. Hidden symbols must be verified through Kconfig selection and not assigned blindly.
4. If any required symbol is missing, `=m`, `=n`, or absent unexpectedly:
   - identify the real Kconfig dependency or source inclusion path;
   - make the minimum justified config/source correction;
   - regenerate the final config;
   - rerun the validator and all affected checks.
5. Compile the full custom DBY-W09 Image target using manifest-provided Clang/Rust/Bazel. Use a conservative concurrency value and inspect cgroup/WSL/runner memory before selecting limits; do not invent a RAM budget.
6. Any command piped to `tee` must run with `set -o pipefail` so a failed Bazel process cannot be hidden by the logger. Avoid repeating an identical successful Bazel build just to create a second phase label; use `cquery --output=files` and verify the declared outputs.
7. For each build failure, diagnose the first meaningful compiler/Bazel error, fix it on this branch, rerun the impacted stage and then rerun the full build. Continue until the Image target succeeds or a clearly external infrastructure blocker is proven.
8. Archive:
   - full unredacted build log if safe for the branch; otherwise sanitized build log and exact log checksum;
   - Bazel command and exit code;
   - source manifest and commit identities;
   - compiler/Rust/Bazel versions;
   - final `.config` and SHA-256;
   - Image SHA-256 and size;
   - System.map and vmlinux presence/metadata;
   - full `git diff` summary and patch provenance.

A successful candidate patch or Bazel target query is NOT a successful kernel compile. Do not stop until a real Image build is recorded when an authorized build environment is available.

## 8. Phase E — migrate the board DTS only when evidence allows it

This phase follows successful Phase D Image compilation, but may run in parallel where it does not depend on the Image result.

Current board DTS is only `dts/dby-w09-ack18-board.dts.draft`. It is not a kernel source input. The ROUND37 patch targets that draft only.

Before integrating a real board DTS:
1. Re-read ROUND42/43/55 and local HOS4.3 firmware evidence.
2. Obtain trustworthy evidence for the actual post-ABL final memory handoff. One of these must be proven:
   - classic FDT contains enabled RAM node(s) with `device_type = "memory"` and trusted `reg` / `linux,usable-memory` ranges; or
   - the actual entry path is Linux EFI stub with complete trusted `/chosen/linux,uefi-system-table` and UEFI memory-map metadata.
3. Preserve the HOS4.3 reserved-memory carveouts that are required by the real handoff. The 34 existing reserved-memory children are not a substitute for RAM size/ranges. Do not invent ranges or copy them from another SM8250 device/HOS4.2 tree.
4. Identify the actual ACK DTS include/Makefile conventions for the SM8250 DBY-W09 board and create a real source-tree DTS path on this branch only when the above input facts are adequate.
5. Integrate the existing board draft carefully; then apply the ROUND37 dual-GenPD delta to that real board source.
6. Add only properties supported by the local evidence and pinned ACK binding. Resolve the physical PM8150 VRM parent-supply gap; do not silence regulator warnings with dummy fixed regulators or fabricated input rails.
7. Keep the unresolved HOS ARC/proxy semantics explicit. ACK RPMhPD/GenPD is not automatically equivalent to the HOS4.3 vendor ARC graph; do not add MMCX→MX parent edges or permanent proxy/always-on votes without evidence.
8. Run real `dtc`, `dtbs_check`, and relevant `dt_binding_check` against the actual source tree, resolving all new diagnostics.

If the RAM map, boot entry or physical supply topology is still unavailable, do not guess. Keep the board DTB gate open and continue other source/build work.

## 9. Phase F — boot-image, ramdisk and AVB preparation

This is a first-boot gate and does not block the Image-only compile.

Facts already established:
- device boot image header v2;
- separate ramdisk partition;
- current inventory has not established vendor_boot or init_boot;
- dynamic partitions/super exist;
- AVB footer/vbmeta descriptor relationship remains unresolved because ROUND12 was blocked;
- actual ramdisk content and early module-loading path are unknown.

Tasks:
1. Inspect the current ACK build packaging tools and determine whether they can produce exactly the legacy header-v2 boot layout needed by this device. Do not use a modern generic boot.img target by assumption.
2. Determine how the separate ramdisk partition is passed/combined by the actual Huawei ABL path. Preserve header/page-size/base/cmdline/DTB placement only from trustworthy local evidence.
3. Review AVB using the trusted local report/tool path once WorkBuddy's separate authorization issue is resolved. Do not fabricate AVB output or infer descriptor coverage from file magic or size.
4. Determine whether built-in early storage drivers allow a kernel-only Image/DTB experiment without altering the stock ramdisk. Prove rather than assume.
5. Produce a non-flashing packaging specification with exact inputs, formats, offsets, sizes, checksums, verification chain and rollback plan. Do not generate a device boot candidate until all input identities are known.

No bootloader unlock, vbmeta disable, verification disable, partition write or flash command is authorized by this task.

## 10. Phase G — prepare and execute controlled device validation

You are responsible for preparing the test plan and evidence collection, not independently deciding to write the user's device.

Before any actual boot attempt, submit for primary-AI/user review:
- exact Image/DTB/DTBO/boot artifacts and checksums;
- source commit and applied patch set;
- complete boot/AVB layout validation;
- trusted RAM/reserved-memory strategy;
- recovery/rollback plan that preserves the original HOS4.3 boot path;
- non-destructive vs persistent action distinction;
- exact commands and expected outputs.

Only after explicit user authorization may the local Agent/user execute the approved temporary boot or other device operation. No partition flash/write is permitted without a separate explicit authorization.

Acceptance evidence must include:
- `uname -a` or equivalent exact kernel version/build identity;
- early dmesg with memory map, reserved memory, clocks, regulators, GenPD, PHY and UFS initialization;
- UFS link startup and actual block-device enumeration;
- read-only validation of expected partitions and mounted root/first-stage storage path;
- basic touch/display/input or other agreed minimum hardware evidence;
- suspend/resume and repeated cold/warm boot observations if feasible.

If the new kernel fails to boot, capture logs, identify the earliest failure, fix the source/DT/packaging issue, rebuild and repeat only under a reviewed safe plan. Do not interpret a successful Image compile as device acceptance.

## 11. Progress logging and no-idle rule

Maintain:
`kernel-baseline/round61/PROGRESS.md`

Update it at every phase transition and every significant failure/fix with:
- current branch HEAD;
- active phase;
- exact commands run;
- PASS / FAIL / BLOCKED / NOT_RUN statuses;
- artifact paths and SHA-256/Git blob IDs;
- first unresolved blocker and the next concrete action.

Create phase reports such as:
- `phase-a-real-patch-application.md`
- `phase-b-dt-binding-validation.md`
- `phase-c-kleaf-target-validation.md`
- `phase-d-kconfig-and-image-build.md`
- `phase-e-board-dts-and-memory-handoff.md`
- `phase-f-boot-chain-packaging.md`
- `phase-g-device-validation.md`

Commit each meaningful milestone to this dedicated branch. Keep a single continuous task; do not create a succession of unrelated review-only rounds. After any deliverable is committed, immediately proceed to the next unblocked phase within the same mission.

When a phase is blocked by unavailable local firmware, host approval or physical device access:
- record the exact missing input and why it cannot be inferred;
- finish all other work that does not depend on it;
- provide the narrowest precise request for the local Agent/user;
- do not idle by repeating previously completed public-source research.

## 12. Final completion criteria

Mark Stage A **COMPLETE** only when all applicable criteria are evidenced:

1. exact ACK commit and complete revision-pinned build manifest archived;
2. actual Git patch application and whitespace/checkpatch checks pass;
3. UFS binding `dt_binding_check` passes;
4. actual Kconfig resolution and final-config validator pass;
5. real DBY-W09 custom Image compilation succeeds;
6. actual board DTS/DTB/DTBO are built from trusted RAM and supply data;
7. legacy boot header v2 / separate ramdisk / AVB chain is validated;
8. tablet boots the built ACK-derived 6.18.33 kernel using an approved, recoverable method;
9. UFS/internal storage is enumerated and the agreed basic hardware checks pass with logs.

Until #8–#9 have real evidence, status must remain **STAGE_A_BUILD_READY** or **STAGE_A_DEVICE_VALIDATION_PENDING**, not COMPLETE.

After Stage A completion, do not automatically begin Stage B. Submit a handoff for explicit approval to start the Android 17 DerpFest device/vendor/HAL work.

**The mission remains active until Stage A is genuinely accepted or a specific externally controlled gate requires user action.**
 

## Primary-AI supplemental evidence — ROUND62 boot-chain reference

Before starting Phase E/F, read the primary-AI report on main:
`kernel-baseline/round62/round62_same_device_abl_bootv2_ramdisk_dtbo_reference.md`.

It reviews a pinned public DBY-W09 Linux 7.0 reference commit and finds a same-device report of:
- Huawei ABL booting header-v2 `boot` with a separate `ramdisk` partition;
- `fastboot boot` refused on that tested setup;
- an ABL-accepted DTBO that fills `/rootparam`;
- a method that unpacks the exact local stock boot image to preserve header-v2 metadata;
- a separate ramdisk payload path that preserves that other setup's AVB footer after validating its exact stock partition.

This is cross-reference only, not proof of the user's HOS4.3 details. Do not copy its HOS4.2 assumptions, stock hashes, fixed 96 MiB / 2 MiB partition sizes, offsets, command line, DTB or AVB metadata. Phase A–D must continue regardless of this later packaging gate. Treat lack of `fastboot boot` as a significant potential safety constraint: no partition writes without separately reviewed inputs and explicit user authorization. 