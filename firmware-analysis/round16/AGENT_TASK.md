# firmware-analysis ROUND16 — Deploy WSL2 Ubuntu and prepare the pinned ACK 6.18.33 Kleaf workspace

**Date:** 2026-11-24  
**Status:** READY FOR LOCAL AGENT — USER EXPLICITLY AUTHORIZED ENVIRONMENT DEPLOYMENT IN CHAT  
**Target:** Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 rev 2.1  
**Stage:** A only — ACK 6.18.33 kernel port  
**Immutable kernel source:** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Required report:** `firmware-analysis/round16/round16_wsl_ack_workspace_deployment.txt`  
**Upload destination:** `hhdy/matepad11-dby-w09-agent-reports`, branch `firmware-audit-v1`

---

## 0. Authorization and mission

The user explicitly authorized the local Agent to deploy the required Linux development environment on the Windows PC.

This task supersedes the ROUND15 read-only restriction **only for the specific software/environment installation and source-workspace setup described here**. It does not authorize device operations, firmware modification, flashing, or security-policy bypass.

Mission:

1. Establish a WSL 2 Ubuntu 24.04 LTS environment, preferably stored on Drive D:.
2. Install only the required Ubuntu host packages from trusted Ubuntu repositories.
3. Initialize and synchronize the official Android kernel manifest workspace.
4. Pin the `common` kernel source checkout to the exact immutable ACK commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.
5. Capture the revision-pinned Repo manifest and verify the manifest-provided Kleaf/Bazel and compiler toolchain.
6. Leave the source checkout clean and unmodified, ready for a separate patch-integration/build task.

**Do not compile the kernel in this round.** Environment provisioning and source synchronization are the deliverables. The next task will separately authorize patch application, schema/Kconfig checks and compilation.

## 1. Evidence and rationale

ROUND15 report (completed):
`firmware-analysis/round15/round15_stagea_build_environment_inventory.txt`

- No kernel source tree or Android repo workspace was found in the bounded permitted search.
- No native Linux environment, Docker or Podman was evidenced.
- `wsl.exe` exists, but a WSL query was blocked by the host security program. Recheck it through the normal approved invocation path. Do not bypass a security block.
- Windows-side Clang, LLD, Bazel/Bazelisk, JDK, GNU Make, Ninja, dtc and dt-schema were not found.
- Drive D: had 325.4 GiB free at the time of ROUND15.

Official technical basis:

- Microsoft documents WSL installation, `--location`, `--no-launch`, WSL 2 and first-run Linux user creation:
  https://learn.microsoft.com/windows/wsl/install
  https://learn.microsoft.com/windows/wsl/basic-commands
- Android Common Kernel documentation says Kleaf has no additional host dependencies; the Bazel toolchain and environment are supplied through `repo sync`:
  https://android.googlesource.com/kernel/build/+/refs/heads/main-kernel-2026/kleaf/docs/kleaf.md
- Android's kernel build guide says a kernel checkout includes `tools/bazel` and that Repo is the supported way to obtain recent kernel source/tooling:
  https://source.android.com/docs/setup/build/building-kernels
- The official kernel manifest branch `common-android17-6.18` exists:
  https://android.googlesource.com/kernel/manifest/+/refs/heads/common-android17-6.18/

The 400 GiB free space / 64 GiB RAM requirements on the AOSP workstation page apply to checking out and building the **full Android platform**, not automatically to this kernel-only Kleaf workspace. Do not attempt a full Android/DerpFest platform checkout in this round.

## 2. Global safety boundaries

### Allowed in this task

- Enable/install official WSL 2 components if permitted by the current Windows policy and administrator context.
- Install Ubuntu 24.04 LTS to a dedicated directory on Drive D:.
- Ask the user to enter the Linux username/password in the distro's first-run prompt. Do not record the password.
- Install packages from the configured official Ubuntu repositories.
- Install the official Repo launcher using the Ubuntu package when available.
- Download/synchronize the official Android kernel manifest workspace over HTTPS.
- Create workspace directories, Repo metadata, logs and a local environment README inside the newly created WSL workspace.
- Check compiler/Bazel/Rust versions supplied by that workspace.
- Upload only the sanitized text report specified in section 10 to `firmware-audit-v1`.

### Hard prohibitions

- **Never bypass a Windows security program, application-control rule, execution blacklist, UAC boundary or organization policy.** If `wsl.exe` is still blocked, stop. Do not copy/rename the executable, invoke a hidden alternate path, use another shell to evade the block, disable security settings, change policy or use an untrusted WSL package.
- Do not disable Windows Defender, antivirus, SmartScreen, application control, firewall or endpoint protection.
- Do not change BIOS/UEFI settings. If CPU virtualization is disabled, report it and stop for the user's manual decision.
- Do not force a Windows reboot. If a restart is needed, finish the current stage safely, report `WAITING_FOR_USER_RESTART`, and stop.
- Do not overwrite, unregister, delete, reset or relocate any existing WSL distribution. If the target distro name or D: install directory already exists, inspect and report; do not replace it.
- Do not install a complete AOSP/DerpFest source tree or Android platform build environment.
- Do not install global Windows Clang/LLD, Bazel, Bazelisk, JDK, Rust or NDK packages. Use the versions provided by the kernel manifest.
- Do not use unofficial mirrors, third-party prebuilt toolchains or unverified scripts.
- Do not clone the user's firmware, run AVB/FDT/EROFS/ramdisk parsing or device discovery.
- Do not connect to the DBY-W09, use ADB/fastboot, unlock, root, flash, write partitions or change device state.
- Do not modify `main`, `ack18-dby-w09-dts-draft`, the ROUND54 branch or PR #1.
- Do not apply any kernel patch, edit kernel source, create a device BUILD target, run Kconfig/olddefconfig, run dt-schema/dtbs_check, or compile any kernel in this round.

## 3. Stage A — Windows and WSL preflight

Record (sanitized):
- Windows edition/build and architecture;
- physical RAM (GiB), logical processor count and whether hardware virtualization is enabled;
- current free space on C:, D: and E:;
- whether the current process has administrator rights;
- WSL installation/version/status and existing distro names/version/location if safely available;
- whether `VirtualMachinePlatform` and `Microsoft-Windows-Subsystem-Linux` features are enabled.

Use only normal PowerShell / Microsoft WSL commands.

If direct WSL commands remain blocked by the security program, **stop immediately** and report `BLOCKED_BY_HOST_SECURITY_POLICY`. The earlier ROUND15 block is not permission to circumvent it.

If the Windows feature setup requires administrator rights:
- use a normal approved UAC elevation path if available;
- if elevation is denied/unavailable, stop and report `ADMIN_REQUIRED`;
- do not attempt privilege escalation or policy changes.

If hardware virtualization is disabled or unavailable, do not change BIOS/UEFI. Report `VIRTUALIZATION_UNAVAILABLE` and stop.

## 4. Stage B — Install WSL 2 and Ubuntu 24.04 on D:

Preferred distro: **Ubuntu 24.04 LTS**, WSL version 2.

Preferred location:
`D:\\WSL\\Ubuntu-24.04`

Before installation:
- check whether Ubuntu 24.04 is already registered;
- check whether the target directory already exists;
- if either exists, do not overwrite or unregister it. Reuse it only if it is clearly the intended existing WSL 2 Ubuntu 24.04 installation and its storage location is confirmed; otherwise stop and report the conflict.

If WSL is absent or incomplete, use Microsoft's official WSL installation mechanism. The documented install options include a selected distro, `--location` and `--no-launch`. The intended command shape is:

```powershell
wsl --install --distribution Ubuntu-24.04 --location "D:\\WSL\\Ubuntu-24.04" --no-launch
```

If WSL components are already present but outdated, use only the supported Microsoft `wsl --update` path. Do not install preview builds.

Then verify:
```powershell
wsl --status
wsl --version
wsl --list --verbose
```

Ensure the distro is WSL 2. If needed, use:
```powershell
wsl --set-default-version 2
wsl --set-version Ubuntu-24.04 2
```

If Windows requires a restart at any point, do not reboot automatically. Report the precise required restart and stop. Continue only when the user reopens/resumes the task after restarting.

On the first Ubuntu launch, Windows/Ubuntu will ask for a Linux username and password:
- suggest the neutral Linux username `kerneldev`;
- let the user type and choose the password privately;
- never echo, store, upload or place the password in logs;
- do not reuse the user's Windows password.

If the agent cannot provide an interactive secure password prompt, stop and let the user complete first-run initialization manually. Do not create a password-less root environment.

## 5. Stage C — Install minimal Ubuntu host packages

Inside Ubuntu 24.04, update the package index and install only the following kernel/repo host dependencies from configured official Ubuntu repositories:

```bash
sudo apt-get update
sudo apt-get install -y \
  git git-lfs curl ca-certificates gnupg repo \
  flex bison build-essential zip zlib1g-dev \
  libncurses-dev libssl-dev libelf-dev \
  libxml2-utils xsltproc unzip fontconfig \
  bc rsync python3 python3-venv python3-pip python3-yaml \
  device-tree-compiler dwarves lz4 file pkg-config
```

If package `repo` is not available in the configured Ubuntu repositories:
- follow only the official Android Repo installation guidance;
- verify the Google Repo launcher signature before installing it;
- if signature verification cannot be completed, stop and report. Do not install an unverified script.

Do not globally install Bazel, Clang, LLD, Rust or JDK. The Android kernel manifest supplies the hermetic toolchain; see the Kleaf documentation in section 1.

After package installation record:
```bash
git --version
git-lfs --version
repo version
python3 --version
make --version
gcc --version
dtc --version
pahole --version
```

Do not add arbitrary PPAs or third-party apt repositories. Do not use `pip install --break-system-packages`. A dedicated Python venv for dt-schema may be created in a later validation task after the exact kernel source requirements are reviewed; it is not needed to declare this setup complete.

## 6. Stage D — Prepare the official Android kernel Repo workspace

Place the source workspace **inside the WSL Linux filesystem**, not under `/mnt/d`, so kernel builds do not operate on the Windows-mounted NTFS filesystem.

Suggested Linux path:
`/home/kerneldev/work/matepad11/ack-6.18.33`

Use the official kernel manifest:
```bash
mkdir -p ~/work/matepad11/ack-6.18.33
cd ~/work/matepad11/ack-6.18.33
repo init -u https://android.googlesource.com/kernel/manifest -b common-android17-6.18
repo sync -c -j4 --fail-fast
```

Notes:
- This is the **kernel manifest workspace only**, not the Android platform or DerpFest manifest.
- The `common-android17-6.18` manifest branch is a moving workspace/tooling recipe. Preserve its exact revision using `repo manifest -r`.
- If the sync fails, retain the diagnostic log and report. Do not switch to a random branch, unofficial mirror or alternate prebuilt source.
- If network reliability requires a retry, retry the same official sync command with `-j2`; do not change manifest branch.
- Before sync and after sync, confirm at least 100 GiB remains free on Drive D:. Keep a 100 GiB safety reserve. If the workspace would exceed a 200 GiB total deployment budget or the D: free space would fall below 100 GiB, stop and report rather than consuming the remaining disk.
- Record CPU/RAM and choose `-j4` only for Repo download concurrency; do not infer this is a safe kernel compile parallelism setting.

## 7. Stage E — Pin the exact ACK common source and capture toolchain metadata

Inside the synced workspace:

1. Identify the project path for the common kernel (expected `common/`).
2. Inspect its remote identity and current revision.
3. Verify that tag `android17-6.18.33_r00` resolves to:
   `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.
4. If the commit/tag object is not locally present, fetch only the exact official tag from the configured official common-kernel remote. Do not use the moving branch head as a substitute.
5. Check out the immutable target commit in detached-HEAD state:
   `git checkout --detach 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.
6. Verify:
   - `git rev-parse HEAD` equals the exact pinned commit;
   - `git status --short` is empty;
   - the tag points to the expected commit;
   - kernel top-level Makefile reports the expected 6.18.33 version.
7. Create the metadata directory and capture the full workspace manifest **after pinning common**:
   `mkdir -p metadata`
   `repo manifest -r > metadata/repo-manifest-revisions.xml`.
8. Also capture the manifest-branch revision and Repo tool version in metadata. Do not include credentials or private URLs.
9. Compare the source-declared toolchain versions in the pinned kernel tree with the manifest-provided prebuilt tools. ROUND39 recorded the expected compiler/Rust baselines as Clang `r584948c` and Rust `1.91.1.p3`; verify from the actual pinned source and resolved prebuilt project revisions rather than assuming.
10. Inspect the workspace-provided `tools/bazel` wrapper and run `tools/bazel --version` if it is available. This is a tool-version query only, not a build. If the wrapper needs to fetch its declared Bazel version, use only the official URL/configuration embedded in that wrapper and record the result.

If the manifest's compiler/Rust prebuilts do not satisfy the pinned source's declared toolchain contract, **do not manually replace them**. Leave the workspace intact, report the mismatch and stop before any build.

The `common/` tree must remain pristine. Do not apply ROUND32/36/37/33/52 patches yet.

## 8. Stage F — Local workspace README and readiness checks

Create a local workspace README at:
`~/work/matepad11/ack-6.18.33/WORKSPACE_STATUS.txt`

It should record:
- exact ACK tag and commit;
- Repo manifest branch and revision;
- `repo manifest -r` metadata path;
- actual manifest-provided Clang/Rust/Bazel revisions;
- host package list and versions;
- WSL distro/version and Linux kernel version;
- workspace path;
- remaining disk space;
- explicit statement: no kernel patches applied and no build executed.

Do not put passwords, tokens, personal full Windows paths, firmware details or sensitive user data in this README.

## 9. Stop point — no compilation in ROUND16

After the Linux environment, host dependencies, official kernel manifest checkout and exact ACK source pin are verified, STOP.

Do not run:
- `make`, `olddefconfig`, `savedefconfig`;
- `tools/bazel build`, `bazel build`, `bazel query` or any compile target;
- `git apply`, `checkpatch.pl`, `dt_binding_check`, `dtbs_check`, `dtc` against the board tree;
- image packaging, AVB tools, boot image assembly or device tests.

These are a later separately reviewed task. The purpose here is to deliver a stable, reproducible build environment and a clean pinned source worktree.

## 10. Required report and upload

Create exactly one UTF-8 text report:
`firmware-analysis/round16/round16_wsl_ack_workspace_deployment.txt`

Report sections:

1. **Authorization and boundaries:** confirm user authorization and list what was not done.
2. **Windows/WSL:** OS build, architecture, CPU count, RAM, virtualization status, WSL version, distro, WSL2 status and whether security/admin/reboot blockers occurred.
3. **Storage:** C:/D:/E: free space before and after, total WSL/source deployment size if measurable.
4. **Ubuntu packages:** exact apt package list and versions; distinguish installed from failed/not attempted.
5. **Repo workspace:** official manifest URL/branch, manifest revision, sync outcome, project revisions, `repo manifest -r` file path, sync errors if any.
6. **ACK source pin:** remote identity, tag, expected commit, actual HEAD, Makefile version, clean/dirty state.
7. **Toolchain:** actual Bazel wrapper version, Clang version/revision, Rust version/revision, and comparison with pinned source declarations. Do not claim success if not measured.
8. **Workspace path:** sanitized Windows storage label and Linux workspace path (generic Linux username only).
9. **Readiness verdict**, choose one:
   - `WSL_AND_PINNED_ACK_WORKSPACE_READY`
   - `WSL_READY_SOURCE_SYNC_INCOMPLETE`
   - `WSL_READY_TOOLCHAIN_MISMATCH`
   - `BLOCKED_BY_HOST_SECURITY_POLICY`
   - `ADMIN_REQUIRED`
   - `WAITING_FOR_USER_RESTART`
   - `VIRTUALIZATION_UNAVAILABLE`
   - `DISK_BUDGET_EXCEEDED`
   - `BLOCKED_OTHER`
10. **Not performed:** explicitly state no patch apply, Kconfig resolution, schema check, compile, image packaging, flashing or device boot.

Redact:
- Linux password, Windows account name, private keys/tokens, personal home path, serial numbers, volume IDs, and any unrelated data.
- Public repo URLs and public model/SoC facts may be included.

Upload only this report to:
`firmware-audit-v1:firmware-analysis/round16/round16_wsl_ack_workspace_deployment.txt`

Do not upload the source tree, VHDX, binaries, package caches, logs with personal paths, or credentials.

## 11. Completion protocol

- No changes to `main`, `ack18-dby-w09-dts-draft`, ROUND54 branch or PR #1.
- PR #1 remains Draft/Open/unmerged.
- Verify the report upload and return the commit SHA, report URL, readiness verdict and any blocker.
- After the report is uploaded, STOP. Do not continue into patch application or kernel compilation in the same task.

**Stage order remains unchanged:** finish and boot the DBY-W09 ACK 6.18.33 kernel first; only after actual Stage-A boot and storage/basic-hardware acceptance may Android 17 DerpFest Stage B begin.
