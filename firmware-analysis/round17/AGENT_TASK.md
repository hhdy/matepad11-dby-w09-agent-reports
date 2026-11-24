# ROUND17 — Resume WSL deployment after operator clears security policy

**Date:** 2026-11-24  
**Status:** WAITING FOR USER PRECONDITIONS — DO NOT RUN UNTIL BOTH ARE CONFIRMED  
**Target:** Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 rev 2.1  
**Stage:** A only — ACK 6.18.33 kernel port  
**Pinned common source:** android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Predecessor:** ROUND16 ended normally as BLOCKED_BY_HOST_SECURITY_POLICY; it is not a failed installation and must not be represented as partially deployed.

## 0. What ROUND16 actually established

Read the completed report:
firmware-analysis/round16/round16_wsl_ack_workspace_deployment.txt on firmware-audit-v1, commit 2150bb1c3239630635b24f1265fc7aa1b6fcdac0.

Verified in ROUND16:
- Windows 11 Pro for Workstations, build 26200, x64.
- Store WSL Appx MicrosoftCorporationII.WindowsSubsystemForLinux version 2.7.3.0 is installed.
- One WSL distribution named Ubuntu is already registered, Version=2, State=installed. Its exact Ubuntu release is UNKNOWN; its BasePath is under C: and the directory probe was inconclusive.
- VirtualMachinePlatform is Enabled.
- Microsoft-Windows-Subsystem-Linux legacy optional feature is Disabled; whether that is relevant to this Store WSL2 installation is UNKNOWN.
- HypervisorPlatform is Disabled; this is not established as a WSL2 blocker.
- HypervisorPresent and VirtualizationFirmwareEnabled are TRUE. Do not treat VMMonitorModeExtensions=FALSE, while a hypervisor is present, as a BIOS/CPU defect.
- D: had 325.3 GiB free; D: storage is not the blocker.
- The only execution attempt of wsl.exe was blocked by the host Program Blacklist. The agent complied and stopped.
- The local Agent process was not elevated. No WSL installation, distro creation/launch, apt package installation, repo sync, pinning or build occurred.

ROUND15 conclusion correction: WSL was not absent. ROUND15 did not successfully query it. The existing Store WSL2 app package and registered WSL2 distro were discovered only in ROUND16. Preserve this distinction in all future reports.

## 1. User/operator prerequisites — NOT AGENT TASKS

The user must complete both items before dispatching this task:

### A. Remove only the explicit WSL program blacklist entry

On the local computer, user/operator opens:
**Security Center → Command Security → Program Blacklist**

Remove/allow this exact blocked program entry:
C:\Windows\System32\wsl.exe.

This must be a user/operator action. The Agent must not open or modify Security Center, must not alter blacklist entries, and must never attempt workarounds. Do not disable endpoint protection globally or weaken unrelated security settings.

After the user says the entry was removed/allowed, the Agent may make a normal approved wsl.exe invocation. If still blocked, immediately stop and report BLOCKED_BY_HOST_SECURITY_POLICY; do not retry through another shell, script, path, copy or renamed executable.

### B. Start the local Agent in an elevated Administrator context

The user must launch the local Agent/application once using the normal **Run as administrator** flow, or otherwise provide the task in an already-approved elevated terminal/session. The task requires a privileged context only if official WSL/Windows feature installation proves necessary.

The Agent must inspect its own current elevation status without trying to self-elevate. If it is not elevated, stop with ADMIN_REQUIRED; ask the user to relaunch it elevated. Do not use credentials, scheduled tasks, token duplication, UAC bypass or silent privilege escalation.

Do not request or store the Windows password or Linux password. During Ubuntu's first-run username/password prompt, pause and let the user enter those values directly.

**ROUND17 is not dispatched merely because this taskbook exists.** Wait until the user confirms A and B are complete.

## 2. Fixed user decision — preserve the existing Ubuntu

The primary AI has decided the safe path:

- Preserve the pre-existing WSL distribution Ubuntu on C: exactly as found.
- Do not inspect its filesystem by launching it, do not update it, do not set it as default, do not change its WSL version, do not move/export/import it, and do not unregister/delete/reset it.
- Install a separate distro named Ubuntu-24.04 at exactly:
  D:\WSL\Ubuntu-24.04.
- Do not ask the Agent to choose between reuse and replacement. This decision is already made.
- Do not modify any other existing distro or change the default distro.

## 3. Store WSL 2.7.3.0 verification strategy — do not reinstall the WSL platform blindly

ROUND16 has shown that Store WSL 2.7.3.0 already exists and a WSL2 distro is registered; VirtualMachinePlatform is already enabled. Therefore the Agent must **not** begin by rerunning the full wsl --install platform bootstrap, reinstalling the Store WSL package, or enabling legacy optional features speculatively.

After prerequisites A and B are confirmed, use the standard WSL entry point and collect:
    wsl.exe --version
    wsl.exe --status
    wsl.exe --list --verbose
    wsl.exe --list --online

Record exact outputs and exit codes. These commands verify the Store WSL CLI/runtime, default WSL settings, existing distro registration and the official available distribution names. They do not launch the existing Ubuntu distro.

Do not treat HypervisorPlatform=Disabled as a blocker. Do not enable it.

Do not enable the legacy Microsoft-Windows-Subsystem-Linux optional feature merely because CIM reported it Disabled. Store WSL is already installed, and a WSL2 distro is registered. Only consider an official feature enablement if the actual Store WSL CLI or Ubuntu-24.04 installation returns a specific error proving it is required. If the requirement is unclear, stop and report evidence; do not guess.

## 4. Install the separate Ubuntu 24.04 distro on D:

First check that Ubuntu-24.04 is not already registered and that the target directory does not contain user data. Do not overwrite anything.

Create D:\WSL if absent. Confirm D: free space remains at least 100 GiB and total deployment stays within 200 GiB.

Use Microsoft's documented WSL distribution install options (the installed Store WSL CLI supports distribution selection and location):
    wsl.exe --install --distribution Ubuntu-24.04 --location D:\WSL\Ubuntu-24.04

**Omit --no-launch intentionally.** This allows the new distro's first-run initialization to open normally. If the first-run account creation prompt appears, pause and ask the user to enter a normal Linux username (suggested: kerneldev) and a private password directly. Do not capture or log the password. Continue only after the user confirms first-run setup completed.

This path is the alternative to the old --no-launch sequence:
- The already-installed Store WSL is verified with --version / --status.
- The new distro is installed directly at the selected location.
- First-run setup is completed interactively by the user.
- The registered distro is verified after setup with wsl --list --verbose and an in-distro /etc/os-release check.

Do not use the default Ubuntu distribution package or install a generic Ubuntu without the 24.04 identity. Ensure the new registration is WSL version 2.

If the install explicitly requires a reboot, do not force it. Ask the user to reboot normally and resume only after the user confirms. If it requires a Windows feature, use only the exact official feature identified by the error and the existing elevated context; do not enable unrelated optional features. Record changes and reasons. If the action is ambiguous, stop.

## 5. Verify both distributions and the target location

After first-run setup:
    wsl.exe --list --verbose

It must show both:
- existing Ubuntu — preserved, unmodified;
- new Ubuntu-24.04 — Version 2.

Verify the new distro in Linux:
    cat /etc/os-release
    id
    uname -r
    df -h /

Confirm VERSION_ID="24.04" / VERSION_CODENAME=noble, the current user is the intended unprivileged user, and the filesystem has sufficient free space. Verify the Windows registration BasePath or equivalent supported WSL registration evidence points at D:\WSL\Ubuntu-24.04. Do not infer the D: location from the install command alone.

The default WSL distro does not need to change. If possible, keep Ubuntu-24.04 invoked explicitly with wsl -d Ubuntu-24.04.

## 6. Prepare the kernel-only build workspace

Only after §5 is proven:
- Work inside the distro Linux filesystem, not under /mnt/d:
  /home/kerneldev/work/matepad11/ack-6.18.33.
- Use only official Ubuntu repositories for the minimal host package set from the original ROUND16 §5 (Git, Git LFS, curl, certificates, GnuPG, Repo launcher, flex/bison/build-essential, required libraries, Python, dtc, pahole, lz4 and standard helpers).
- Prefer the official Android Repo launcher/install instructions with signature verification. Do not install a random similarly named repo binary.
- Do not install global Bazel, Bazelisk, Clang, LLD, Rust, JDK or NDK. The pinned Android kernel manifest supplies the expected build toolchain.
- Initialize only the official kernel manifest:
  https://android.googlesource.com/kernel/manifest
  branch common-android17-6.18.
- Synchronize with the original ROUND16 bounded settings, e.g. repo sync -c -j4 --fail-fast.
- In common/, checkout detached commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a; verify git rev-parse HEAD.
- Capture repo manifest -r and preserve the output.
- Verify manifest-provided tools/bazel, Clang r584948c, Rust 1.91.1.p3, and project revisions. Do not assume version strings without actually running the binaries.
- The workspace is kernel-only, not a full AOSP or DerpFest platform checkout.
- Do not apply any DBY-W09 patch or alter canonical source artifacts in this round. Keep source checkout clean after pinning.

## 7. Stop conditions

Stop immediately with a precise status if:
- user has not confirmed the blacklist change;
- the normal wsl.exe entry point remains blocked;
- the local Agent is not elevated when a privileged action is needed;
- a distro named Ubuntu-24.04 or target directory already exists unexpectedly;
- official CLI flags / distro identity differ from expectations;
- a reboot or ambiguous feature change is requested;
- D: free space falls below 100 GiB or the 200 GiB budget would be exceeded;
- a trusted official Repo installation cannot be verified;
- source ref/toolchain mismatch appears.

Never bypass security, use third-party WSL packages, disable Defender/AV/firewall, change BIOS/UEFI, force reboot, overwrite the existing Ubuntu, touch the tablet, apply patches or compile during this round.

## 8. Required report and upload

Write one sanitized text report:
firmware-analysis/round17/round17_wsl_ack_workspace_deployment.txt

Upload to:
hhdy/matepad11-dby-w09-agent-reports, branch firmware-audit-v1.

Report:
- operator preconditions confirmed / not confirmed (do not expose personal names);
- WSL Store version and exact CLI status;
- registered distro list and proof existing Ubuntu was preserved;
- new Ubuntu release, Version 2 registration and D: BasePath;
- exact host packages and versions;
- repo manifest revisions and manifest -r file hash;
- pinned common HEAD and dirty status;
- Bazel/Clang/Rust actual versions;
- D: free space before/after and resource budget;
- every action not attempted and every remaining blocker.

Do not include usernames, user profile paths, GUIDs, passwords, tokens, keys or other identifying details.

After upload, stop. No kernel compilation is authorized in ROUND17.

## 9. Next stage after ROUND17

When the report proves the WSL2 Ubuntu 24.04 environment, pinned ACK workspace and matching toolchain are ready, the next task will be a separate disposable-source integration/build round:
1. import the ROUND57 follow-up in the ordered UFS patch series;
2. actual git apply --check / apply / git diff --check;
3. dt-schema and Kconfig resolution;
4. add and verify the full no-base_kernel Kleaf DBY-W09 target;
5. compile the first ACK-derived storage-first Image and archive logs/artifacts.

No DerpFest Stage B before Stage-A device boot and storage/basic-hardware acceptance.
