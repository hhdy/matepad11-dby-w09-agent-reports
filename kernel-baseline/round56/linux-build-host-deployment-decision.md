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
