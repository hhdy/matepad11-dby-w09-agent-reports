# firmware-analysis ROUND15 — Stage-A ACK build environment and source-worktree inventory

**Date:** 2026-11-24  
**Status:** READY FOR LOCAL AGENT — NOT DISPATCHED  
**Target:** Huawei MatePad 11 (2021), DBY-W09, KONA / SM8250 rev 2.1  
**Stage:** A only — ACK 6.18.33 kernel port  
**Pinned source:** `aosp-mirror/kernel_common`, tag `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Required report:** `firmware-analysis/round15/round15_stagea_build_environment_inventory.txt`  
**Upload destination:** repository `hhdy/matepad11-dby-w09-agent-reports`, branch `firmware-audit-v1`

---

## 0. Mission

Perform a **strictly read-only inventory** of the user's existing local development environment to answer the next Stage-A gating question:

> Does a usable full ACK 6.18.33 source worktree and an already-installed Linux-capable kernel build toolchain exist locally, or must the project first prepare an appropriate build environment?

ROUND53 has completed a pinned-source static Kconfig dependency audit and removed direct assignments of hidden symbols `GENERIC_MSI_IRQ`, `SCSI_DMA`, and `OF_RESERVED_MEM`. It has **not** run Kconfig resolution, `olddefconfig`, produced a final `.config`, or performed a Kleaf build.

ROUND54 is assigned to the second GitHub-connected AI for an independent UFS patch-series review on its separate branch. This local task must not inspect or modify that branch.

This task only inventories existing local resources. It is not a request to create, download, sync, build, patch, or repair a kernel workspace.

## 1. Required repository reading

Read the current `main` versions of:

1. `PROJECT_HANDOFF.md`
2. `AGENT_TASK.md`
3. `kernel-baseline/round39/ack-6.18.33-kleaf-build-toolchain-baseline.md`
4. `kernel-baseline/round41/gki-defconfig-storage-driver-gap-and-full-kernel-build-decision.md`
5. `kernel-baseline/round53/ack-storage-first-kconfig-fragment-static-closure.md`

Use these as project context. Do not repeat their public-source research.

## 2. Allowed read-only checks

### A. Existing source worktree discovery

Check only a bounded set of likely user workspace roots, such as existing `source`, `src`, `workspace`, `android`, `aosp`, `kernel`, or `codex` directories under the user's home directory and the top level of available fixed drives.

- Do not recursively scan whole drives.
- Maximum traversal depth: 3 directory levels beneath a candidate workspace root.
- Do not enumerate unrelated personal files.
- Identify candidate directories only by project markers, such as `.git`, `.repo`, `build/kernel/kleaf`, `arch/arm64/configs/gki_defconfig`, `drivers/ufs/host/ufs-qcom.c`, and the kernel top-level `Makefile`.
- Distinguish a complete `kernel_common` checkout from an Android `repo` manifest workspace, a partial source archive, an unrelated kernel tree, or the agent-reports repository.
- If a candidate Git checkout exists, read only:
  - remote URL (redact credentials/tokens; retain only public repository identity);
  - current branch and HEAD commit;
  - clean/dirty status summary;
  - whether the exact pinned commit object exists locally (`git cat-file -e 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a^{commit}`);
  - whether tag `android17-6.18.33_r00` exists locally.
- Do not fetch, pull, checkout, switch branches, reset, stash, or alter any Git metadata.

### B. Already-installed tools

Check whether the following tools are already available and record their versions when safely queryable:

- Git and Git LFS
- `repo`
- Bazel or Bazelisk
- Java/JDK
- Python
- Clang and LLD
- GNU make
- Ninja
- Device Tree Compiler (`dtc`)
- dt-schema tools (`dt-validate`, `dt-doc-validate`, or equivalent)
- `checkpatch.pl` if already present inside an existing kernel source tree
- Docker or Podman availability (presence only; do not start containers)

Use command-existence checks first. Do not install, update, bootstrap, or download any tool. If a version command might initialize a service or download data, do not run it; record presence only.

### C. Existing Linux-capable build environment

Determine only whether an existing Linux environment appears to be available:

- Native Linux host, if applicable;
- WSL executable and already-registered distribution names (presence/listing only; do not start WSL);
- existing Docker/Podman executable presence (do not launch);
- any already-existing Linux build workspace marker discovered in section A.

Do not run WSL, start a VM/container, or invoke remote build services.

### D. Storage capacity

Read the free/total capacity of available filesystem volumes and report the figures in GiB. Do not create test files or benchmark storage.

## 3. Prohibited actions — hard boundary

Do **not**:

- clone, download, fetch, pull, `repo init`, `repo sync`, or access a remote source tree;
- install, update, bootstrap, or unpack any tools, packages, SDKs, compilers, or dependencies;
- execute `make`, `olddefconfig`, `savedefconfig`, Bazel/Kleaf build targets, `bazel query`, `git apply`, `checkpatch`, `dtc`, `dt_binding_check`, `dtbs_check`, or any compilation/build/test command;
- run WSL, start a VM/container, or invoke a remote builder;
- change PATH, registry, environment variables, execution policy, security settings, services, drivers, or system configuration;
- create, edit, delete, rename, or move local files/directories;
- inspect unrelated user documents, browser data, credentials, tokens, private keys, or personal content;
- connect to the DBY-W09 device, use ADB/fastboot, unlock, root, flash, write partitions, or read live device state;
- repeat firmware parsing, AVB parsing, FDT scans, ROUND11/13/14 work, or any task assigned to ROUND54.

If a check is unavailable or would violate these boundaries, mark it `NOT_RUN` and continue with the remaining permitted checks.

## 4. Required report contents

Create exactly one UTF-8 text report:

`firmware-analysis/round15/round15_stagea_build_environment_inventory.txt`

Include:

1. **Execution boundary:** confirm read-only mode and list any check skipped.
2. **Host summary:** OS family/version and whether a Linux-capable build environment already exists. Do not include machine serial numbers, account names, or full personal paths.
3. **Source-worktree table:** candidate type, sanitized workspace label, source completeness markers, Git remote identity, branch, HEAD SHA, clean/dirty state, exact pinned commit object availability, exact tag availability.
4. **Tool table:** tool name, present/missing, exact version if safely obtained, and whether it is usable in an existing Linux build environment versus Windows-only.
5. **Storage table:** volume label, free GiB, total GiB. Do not include volume serial numbers.
6. **Stage-A readiness verdict**, choose one:
   - `READY_FOR_NEXT_BUILD_GATE`: a complete matching ACK source tree and an existing Linux-capable environment/toolchain are both evidenced;
   - `SOURCE_TREE_PRESENT_BUT_ENVIRONMENT_INCOMPLETE`;
   - `BUILD_ENVIRONMENT_PRESENT_BUT_SOURCE_TREE_MISSING`;
   - `NO_EXISTING_BUILD_WORKSPACE_FOUND`;
   - `BLOCKED / INSUFFICIENT_EVIDENCE`.
7. **Exact next blocker:** state what is missing, based only on observed facts. Do not recommend installing or downloading anything in this report.
8. **Not tested:** explicitly state that no Kconfig resolution, final `.config`, patch application, dt-schema/DTB check, kernel build, packaging, or device boot was performed.

Redact all usernames and full local absolute paths. Do not include secrets or unrelated personal data. For a found path, use a neutral label such as `Drive D: / workspace candidate 1`.

## 5. Upload and stop protocol

- Upload only the single report to:
  `firmware-audit-v1:firmware-analysis/round15/round15_stagea_build_environment_inventory.txt`
- Do not upload scripts, binaries, source code, logs containing personal paths, or screenshots.
- Do not update `main`, `ack18-dby-w09-dts-draft`, the ROUND54 branch, or PR #1.
- PR #1 must remain Draft/Open/unmerged.
- After verifying the report upload, STOP. Do not create another task or continue into setup/build work.

The result will tell GPT whether the next stage can proceed with an already-existing environment or whether the user must first decide how to provide a suitable build host. It does not authorize local source modifications or kernel compilation.
