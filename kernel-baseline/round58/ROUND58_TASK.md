# ROUND58 — Build the DBY-W09 Kleaf target (implementation task)

**Owner:** Second GitHub-connected AI  
**Dedicated branch:** ai-parallel/round58-kleaf-target-audit ONLY  
**Priority:** HIGH — this is an implementation workstream, not a passive review  
**Date:** 2026-11-24  
**Status:** READY FOR SECOND AI — NO BUILD EXECUTION CLAIMED  
**Device:** Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 rev 2.1  
**Stage:** A only — ACK/GKI-based 6.18.33 kernel port

## 1. Mission

The project is moving too slowly because the main work has not reached compilation. ROUND16 did not provision the environment: the local Agent was blocked by the Windows Program Blacklist before WSL could be entered. While the user resolves that host-side block, the second AI must independently prepare the **real Kleaf/Bazel full-kernel build target and its verification machinery** from public, pinned source.

This is an implementation assignment. Do not produce only a prose review. Create a concrete, source-backed BUILD.bazel patch candidate and a config-validation helper, with exact application instructions and evidence.

The local Agent will separately resume WSL/deployment under ROUND17. These workstreams are independent and should proceed in parallel.

## 2. Fixed source baseline and migration order

ACK tag: android17-6.18.33_r00  
Exact common source commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
Repository: https://android.googlesource.com/kernel/common  
Architecture: arm64

Do not substitute upstream Linux v6.18.33, a moving HEAD, or a different ACK tag.

Migration order is fixed:
1. First port and boot ACK/GKI-based 6.18.33 on DBY-W09.
2. Verify UFS/storage and basic hardware on the tablet.
3. Only after Stage-A device acceptance, start Android 17 DerpFest Stage B.

No Android 12L research is requested.

## 3. Read these existing project artifacts first (do not repeat their completed analysis)

- kernel-baseline/round39/ack-6.18.33-kleaf-build-toolchain-baseline.md
- kernel-baseline/round41/gki-defconfig-storage-driver-gap-and-full-kernel-build-decision.md
- kernel-baseline/round53/ack-storage-first-kconfig-fragment-static-closure.md
- kernel-baseline/round55/stage-a-execution-gate-matrix.md
- kernel-baseline/round56/linux-build-host-deployment-decision.md
- config/dby-w09-ack18-storage-first.fragment.draft
- kernel-baseline/round38/ufs-dual-genpd-patch-series-manifest.md
- kernel-baseline/round57/sm8250-ufs-clock-names-exact-count-follow-up.md
- kernel-baseline/round57/0001-dt-bindings-ufs-sm8250-clock-names-exact-count.patch.draft

Key prior conclusions:
- Stock gki_defconfig does not enable the Qualcomm UFS/QMP UFS PHY/SM8250 GCC/RPMhPD/SM8250 interconnect/SMMU chain needed for the first DBY-W09 storage milestone.
- The first target must therefore be a full custom kernel_build without base_kernel, based on gki_defconfig plus the storage-first fragment in post_defconfig_fragments.
- Do not choose a base_kernel mixed build as the default; earliest storage drivers must be built-in because the actual initramfs/module loading path has not been proven.
- Build system is Kleaf/Bazel. Legacy build.config.gki.aarch64 and build.sh are explicitly disabled in the pinned ACK.
- Pinned source-declared compiler contract: Clang r584948c, Rust 1.91.1.p3. Verify actual tools from the full revision-pinned manifest after ROUND17.
- The board DTS is still a .dts.draft artifact, not yet a real ACK source-tree DTS input. Final memory handoff is unknown. Do not invent a board DTS source path or RAM ranges.
- AVB/ramdisk/image packaging and final memory handoff remain first-boot gates; they must not block preparing/building an Image-only source target.

## 4. Required deliverable A — concrete Kleaf BUILD.bazel patch

Inspect the exact ACK common BUILD.bazel at commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a and the exact Kleaf API/documentation revision specified by the official common-android17-6.18 manifest. Do not rely on a moving Kleaf master when the manifest provides a pinned build/kernel project revision.

Create:
- kernel-baseline/round58/0001-add-dby-w09-full-kernel-kleaf-target.patch
- kernel-baseline/round58/round58_kleaf_target_implementation.md

The patch candidate should add a DBY-W09 full custom kernel_build target to the correct package BUILD.bazel. It must follow the exact no-base_kernel full-image pattern in the pinned ACK source (the existing yukawa example is the known starting reference), rather than cloning a module-only/mixed build.

Requirements:
- use the pinned ACK kernel_aarch64_sources target (or verify exact current label from pinned BUILD.bazel);
- arch arm64;
- use arch/arm64/configs/gki_defconfig as base;
- add the repository's storage-first fragment as a post_defconfig_fragments input, after confirming how the fragment must be copied into the kernel source tree;
- preserve all required early-storage dependencies as built-in =y; no # nocheck for critical symbols;
- do not set base_kernel;
- do not claim GKI certification or silently inherit stock GKI KMI enforcement;
- choose only output attributes that exist in the pinned Kleaf API;
- keep the first target focused on compiling the full kernel Image and the outputs needed to debug it (e.g. Image, System.map, vmlinux, vmlinux.symvers and built-in metadata) only where the pinned target/API really supports them;
- do not list speculative module_outs or module_implicit_outs; built-in early storage drivers are not delivered as modules in the first milestone;
- do not add a DTB make_goal or point to the current .dts.draft file. Device-tree rules are a separate later target after the board DTS is migrated into a real source path and the memory handoff is evidenced.

The patch candidate must be internally coherent with exact source context and line anchors. Preserve source-file blob SHA and target commit identity in the report. Do not make changes to the pinned public upstream source or the project's main branch.

If a single BUILD.bazel target cannot safely be created without a currently unknown attribute, document exactly which field is unknown and produce the safest minimal candidate without inventing it.

## 5. Required deliverable B — storage-first Kconfig validation helper

Create a small standalone helper:
- kernel-baseline/round58/check_dby_w09_config.py

It must:
- accept a final .config path as a required CLI argument;
- fail clearly if the file is absent, unreadable, duplicated/conflicting assignments exist, or any required symbol is not =y;
- check the current storage-first critical built-in symbol set based on ROUND53 and ROUND41, including at minimum:
  ARM64, ARCH_QCOM, OF, SCSI, BLK_DEV_SD, SCSI_UFSHCD, SCSI_UFSHCD_PLATFORM, SCSI_UFS_QCOM, GENERIC_PHY, PHY_QCOM_QMP, PHY_QCOM_QMP_UFS, COMMON_CLK, COMMON_CLK_QCOM, QCOM_CLK_RPMH, SM_GCC_8250, RESET_CONTROLLER, PM, INTERCONNECT, INTERCONNECT_QCOM, INTERCONNECT_QCOM_SM8250, QCOM_COMMAND_DB, QCOM_RPMH, QCOM_RPMHPD, REGULATOR, REGULATOR_QCOM_RPMH, IOMMU_SUPPORT, ARM_SMMU, BLK_DEV_DM and EROFS_FS;
- check derived ARM_SMMU_QCOM is present =y where it appears in final config; if absent, report that it is a hidden/derived symbol requiring source/Kconfig investigation rather than blindly adding it to the fragment;
- verify DM_VERITY and DM_VERITY_FEC are present =y as inherited GKI baseline capabilities;
- optionally check that no required early storage symbol is =m or =n;
- produce deterministic human-readable PASS/FAIL output and nonzero exit on failure;
- include a --json option if straightforward, but no external Python dependencies.

Add unit tests using temporary synthetic .config fixtures. Tests must prove pass, missing symbol, =m, =n, conflicting duplicate assignments and unreadable/missing input handling. Do not treat synthetic tests as actual kernel Kconfig resolution.

## 6. Required deliverable C — build and verification runbook

The report must give the exact post-ROUND17 command sequence with clear gate separation:

1. Verify repo manifest -r and common HEAD equals 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a.
2. Keep the synced baseline clean; create a disposable source copy/worktree for all port changes.
3. Apply the source patch series in this exact order:
   ROUND32 → ROUND57 → ROUND36 → ROUND52-0001 → ROUND37 (only after migration to a real DTS path) → ROUND33 → ROUND52-0002.
4. Run git apply --check, actual apply, git diff --check, and checkpatch on the driver patches; record exact evidence.
5. Run dt_binding_check on the modified UFS schemas. Do not claim board dtbs_check until a real DTS path and trusted memory strategy exist.
6. Generate final config using the chosen Kleaf target; run the ROUND58 Python helper against the actual final .config; archive it.
7. Run a stock ACK GKI baseline build only as an optional toolchain sanity check (not a device kernel).
8. Build the DBY-W09 full custom Image target with bounded Bazel jobs/memory appropriate to a 15.16 GiB host; do not invent the exact WSL memory settings until inspected.
9. Archive exact Bazel command, logs, source/manifest identities, .config hash, Image hash, System.map and vmlinux metadata.

Do not build a boot image, DTBO image or flash package. Those remain separate device boot gates.

The report must explicitly distinguish:
- candidate target written;
- target label validates under Bazel query;
- target config resolution passes;
- source compilation succeeds;
- a bootable board image exists;
- device actually boots.

These are six distinct evidence states. Do not conflate them.

## 7. Device-tree and boot boundary

The current board DTS draft is not a source-tree build input. The final memory handoff has not been established:
- Classic FDT path needs trusted /memory with device_type="memory" and valid reg/linux,usable-memory ranges; or
- a real Linux EFI-stub path needs complete trusted /chosen UEFI system-table and memory-map metadata.

Do not invent memory ranges or borrow from other SM8250 devices.

Therefore round58 should prepare the Image build target without the DBY-W09 DTB dependency. Separately specify the correct future rules_devicetree dtb()/dtbo() graph using the pinned Kleaf API, but explicitly mark board target integration blocked until a real DTS file path and memory evidence are provided.

Do not generate a boot_image target by assuming modern vendor_boot; device evidence so far is boot header v2 with separate ramdisk and no proven vendor_boot/init_boot.

## 8. Toolchain and host constraints

- User has Windows 11 Pro for Workstations, Ryzen 5 9600X, 12 logical CPUs, about 15.16 GiB visible RAM; D: had 325.3 GiB free.
- ROUND16 was blocked by Windows Program Blacklist; no source or build workspace exists yet.
- Local Agent will handle ROUND17 only after the user manually allows wsl.exe and runs the Agent elevated.
- Do not ask the second AI to interact with the user's PC or assume a local WSL workspace exists.
- Keep Bazel resource policy conservative. Give a recommended first-build job/memory profile only when grounded in pinned Kleaf docs and measured host settings.
- Do not ask to disable security features or alter BIOS/UEFI.

## 9. Branch and safety boundaries

- Write all ROUND58 deliverables only on branch ai-parallel/round58-kleaf-target-audit.
- Do not write to main, firmware-audit-v1 or ack18-dby-w09-dts-draft.
- Do not alter PR #1; it remains Draft/Open/unmerged.
- Do not modify canonical ROUND32/33/36/37/52/57 artifacts. Create separate candidate files only.
- Do not merge the branch or open/merge a PR unless explicitly authorized.
- Do not claim actual Bazel query/config/build, dt-schema, dtc, DTB or device boot was run unless it truly was run.
- No tablet access, unlock, root, ADB, fastboot, partition writes or flashing.

## 10. Completion report

Complete round58_kleaf_target_implementation.md with:
- source revisions and Git blob SHA identities;
- precise target design and why each attribute is chosen;
- exact Kleaf API source URLs/commit identities;
- patch diffstat and SHA;
- helper behavior and unit test results;
- known blockers and exact non-run gates;
- commands the local build Agent should execute after ROUND17;
- explicit stop state.

The task is not complete with a vague design note. Commit at least the actual candidate BUILD.bazel patch plus the tested config helper and its tests, unless a source-proven blocker makes a candidate technically unsafe; if blocked, explain precisely and still deliver a concrete safe fallback.

After committing the report and candidates to this dedicated branch, stop and do not touch other branches.
