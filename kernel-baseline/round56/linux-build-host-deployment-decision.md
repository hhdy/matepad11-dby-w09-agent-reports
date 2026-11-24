# ROUND56 — Linux build-host deployment decision after ROUND15

**Date:** 2026-11-24  
**Status:** DEPLOYMENT PLAN APPROVED BY USER; LOCAL EXECUTION NOT YET REPORTED  
**Device:** Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 rev 2.1  
**Stage:** A — ACK 6.18.33 only

## 1. ROUND15 findings

The local Agent completed ROUND15 and uploaded:

`firmware-analysis/round15/round15_stagea_build_environment_inventory.txt`

Git blob: `e4d5bcdb8ae2d6f7ff8ae173308badf549b8f0bb`.

Observed:
- Windows 11 Pro for Workstations, build 10.0.26200, x64.
- No ACK/kernel source checkout or Android Repo workspace found in the bounded scan.
- No native Linux build host, Docker or Podman evidenced.
- `wsl.exe` exists, but the WSL distribution query was blocked by a host security program; whether an existing distro is installed remains UNKNOWN.
- No Windows-side Clang/LLD, Bazel/Bazelisk, JDK, Make/Ninja, dtc/dt-schema, or Repo launcher found.
- Git 2.55.0.windows.3 and Python 3.13.14 exist; they do not form a kernel build environment.
- Free capacity at scan time: C: 64.3 GiB, D: 325.4 GiB, E: 299.2 GiB.

No build, source sync, patch application or device operation was performed in ROUND15.

## 2. Decision

The user explicitly authorized the local Agent to deploy the required environment on the computer.

The preferred path is:
- WSL 2;
- Ubuntu 24.04 LTS;
- distro storage rooted at `D:\\WSL\\Ubuntu-24.04`;
- kernel source workspace inside the WSL Linux filesystem at `/home/kerneldev/work/matepad11/ack-6.18.33`, not under `/mnt/d`;
- official Android kernel manifest branch `common-android17-6.18`;
- pin the `common` kernel project to immutable commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.

The environment task limits the new deployment to 200 GiB and preserves at least 100 GiB free on D:. ROUND15 observed 325.4 GiB free, so this is a bounded kernel-workspace plan rather than an AOSP platform checkout.

Do **not** check out the entire AOSP or DerpFest Android platform. The 400 GiB / 64 GiB RAM workstation requirements on AOSP setup pages apply to the full Android platform checkout/build, not automatically to this kernel-only Kleaf workspace.

## 3. Toolchain installation strategy

Do not install Clang, LLD, Bazel, Bazelisk, Rust, JDK or NDK globally on Windows.

Kleaf documentation states that the Bazel toolchain and environment are provided through `repo sync`, and Android's kernel build documentation says recent kernel checkouts include `tools/bazel` and the required build tools.

The local Agent should install only the minimum Ubuntu host dependencies from official Ubuntu repositories (Git, Repo, Git LFS, curl, gnupg, flex/bison/build-essential, libraries and standard helper utilities), then verify the actual Bazel/Clang/Rust versions from the pinned kernel source and the manifest-provided prebuilts. It must not replace mismatched prebuilts manually.

Relevant official references:
- Microsoft WSL install and distro location options: https://learn.microsoft.com/windows/wsl/install and https://learn.microsoft.com/windows/wsl/basic-commands
- Kleaf toolchain model: https://android.googlesource.com/kernel/build/+/refs/heads/main-kernel-2026/kleaf/docs/kleaf.md
- Android kernel Repo/Bazel workflow: https://source.android.com/docs/setup/build/building-kernels
- Official kernel manifest branch: https://android.googlesource.com/kernel/manifest/+/refs/heads/common-android17-6.18/

## 4. Deployment authorization boundaries

ROUND16 taskbook:
`firmware-analysis/round16/AGENT_TASK.md`

The user authorizes official WSL/Ubuntu installation, apt package installation, official Repo sync and local workspace creation within the stated budget. It does not authorize:
- bypassing Windows security/application-control policy;
- disabling antivirus, Defender, firewall or execution controls;
- BIOS/UEFI modification;
- forced reboot or privilege escalation;
- deleting/unregistering existing WSL distributions;
- device access, unlocking, rooting, flashing or partition writes;
- kernel patch application or compilation.

If WSL is still blocked by the host security program, stop with `BLOCKED_BY_HOST_SECURITY_POLICY`. Do not rename/copy the executable or use alternate execution routes to evade the block. If administrator elevation or reboot is required, request the user action and stop safely.

## 5. Post-deployment sequence

After ROUND16 returns `WSL_AND_PINNED_ACK_WORKSPACE_READY`:
1. Inspect the actual `repo manifest -r` and toolchain revisions.
2. Review the second AI's ROUND54 independent UFS review before adopting any correction.
3. Create a disposable worktree or copy for patch integration; keep the pristine `common` baseline unchanged.
4. Apply the documented series in order and run actual `git apply --check`, patch checks, schema checks and Kconfig resolution.
5. Only then start the authorized full custom Kleaf kernel build.

No compilation or device boot is part of ROUND16. The actual board memory handoff, AVB, ramdisk and image packaging remain first-boot gates. Stage B DerpFest remains deferred until the ACK 6.18.33 kernel actually boots and passes storage/basic-hardware acceptance.

## 6. Current state

- ROUND15: COMPLETE; environment absent in the permitted scan.
- ROUND16: READY FOR LOCAL AGENT; deployment authorized; execution/report not yet observed.
- ROUND54: second AI task/branch ready; review template exists; final review report not yet uploaded.
- Main ACK source baseline and canonical patch drafts remain unchanged.


## Status correction — ROUND16 actual outcome (2026-11-24)

ROUND16 was executed and uploaded, with terminal verdict **BLOCKED_BY_HOST_SECURITY_POLICY**. The report is `firmware-analysis/round16/round16_wsl_ack_workspace_deployment.txt` on `firmware-audit-v1`, commit `2150bb1c3239630635b24f1265fc7aa1b6fcdac0`.

Corrections to §6 above:
- WSL is already installed as Store Appx `MicrosoftCorporationII.WindowsSubsystemForLinux 2.7.3.0`.
- A pre-existing distro named `Ubuntu` is registered as WSL2 on C:, but its Ubuntu release is UNKNOWN.
- `VirtualMachinePlatform` is Enabled.
- The normal `wsl.exe` entry point is explicitly blocked by Command Security → Program Blacklist; the Agent's process is not elevated.
- No new distro or build workspace was deployed; apt, Repo sync, ACK pin and toolchain checks were NOT_ATTEMPTED.
- D: free space was about 325.3 GiB.

ROUND15 must not be paraphrased as proof WSL was absent; it had not successfully queried the WSL registration. ROUND16 is the first successful registry/Appx inventory.

## Current continuation — ROUND17

The user must manually remove/allow only `C:\Windows\System32\wsl.exe` in Security Center → Command Security → Program Blacklist and relaunch the local Agent in an elevated context. The Agent must not touch the blacklist or use a workaround.

Primary AI fixed the distro decision: retain the existing C: Ubuntu intact; create a second, separate Ubuntu-24.04 at `D:\WSL\Ubuntu-24.04`. Verify the installed Store WSL 2.7.3.0 CLI first. Do not blindly reinstall WSL or enable the legacy WSL / HypervisorPlatform optional features; VMP is already enabled and no actual error currently establishes the need for legacy components.

ROUND17 taskbook: `firmware-analysis/round17/AGENT_TASK.md`; start prompt: `firmware-analysis/round17/START_PROMPT.md`. It resumes source workspace preparation only and ends before patch integration or compilation.

## Parallel second-AI assignment — ROUND58

The second AI is no longer idle after ROUND54. It has a dedicated implementation task on `ai-parallel/round58-kleaf-target-audit`:
- deliver a concrete no-`base_kernel` full-image Kleaf target patch candidate;
- deliver a deterministic final .config checker with synthetic unit tests;
- deliver a build runbook for post-ROUND17 actual integration and Image compilation.

This is source-only candidate work and must not claim Bazel compilation. Board DTS/DTB and boot-image packaging stay separate because final memory handoff / AVB / ramdisk remain unresolved.
