# ROUND17 — Diagnose local Agent execution-policy blocker, then resume WSL deployment

**Date:** 2026-11-24  
**Status:** WAITING FOR BLOCKER IDENTIFICATION — DO NOT RETRY wsl.exe YET  
**Target:** Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 rev 2.1  
**Stage:** A only — ACK 6.18.33 kernel port  
**Pinned common source:** android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Predecessor:** ROUND16 ended as BLOCKED_BY_HOST_SECURITY_POLICY. No deployment or source sync occurred.

## 0. Critical correction to the prior taskbook

ROUND16 reported this message in substance:

"The sandbox prevented a program on the configured Program Blacklist from starting: wsl.exe ... This block cannot be approved or bypassed from the current command. Do NOT retry this program, launch it through another shell or script, or attempt an equivalent workaround."

The message does NOT identify Windows Security Center, Microsoft Defender, a third-party endpoint product, the local Agent's own command sandbox, or a named policy-management UI. Therefore the earlier guess "Security Center → Command Security → Program Blacklist" is withdrawn. Do NOT instruct the user to search for that menu; it may not exist.

The only proven fact is: the local Agent's attempt to execute wsl.exe was blocked by a program-execution policy implemented somewhere in the execution path. The policy owner/configuration point is currently UNKNOWN.

This round must first identify where the block originates using passive product/version/configuration evidence and official documentation. Do not invoke wsl.exe again in this diagnostic phase.

## 1. Current verified machine facts from ROUND16

Read report:
firmware-analysis/round16/round16_wsl_ack_workspace_deployment.txt on firmware-audit-v1, commit 2150bb1c3239630635b24f1265fc7aa1b6fcdac0.

- Windows 11 Pro for Workstations build 26200, x64.
- Store WSL Appx MicrosoftCorporationII.WindowsSubsystemForLinux 2.7.3.0 installed.
- One distro named Ubuntu is registered as WSL2; exact Ubuntu release UNKNOWN.
- Distro is stored under C: user profile; precise BasePath/directory status UNKNOWN.
- VirtualMachinePlatform is Enabled.
- Microsoft-Windows-Subsystem-Linux legacy optional feature is Disabled; whether it is relevant to Store WSL is UNKNOWN.
- HypervisorPlatform is Disabled; not proven to be a blocker.
- HypervisorPresent and VirtualizationFirmwareEnabled are TRUE. Do not infer a BIOS problem from VMMonitorModeExtensions=False.
- D: had about 325.3 GiB free; not a storage blocker.
- The local Agent process was not elevated.
- No WSL invocation succeeded; no packages, Repo sync, ACK pin, patches, build or device operation occurred.

ROUND15 did not prove WSL absent; ROUND16 later established the Store WSL package and registered WSL2 distro.

## 2. User question / required clarification

The user reports there is no "Command Security → Program Blacklist" menu. That is expected because the prior taskbook guessed the product/UI incorrectly.

Before continuing any installation, ask the user to identify the local Agent application or host (name and version, e.g. the actual product they use) and, where possible, provide a screenshot or exact unredacted block dialog text without tokens or personal data. Do not assume Codex, VS Code, an endpoint antivirus, Defender, or any particular product.

This is an information request, not a demand to change settings. User may simply share the app name/screenshot. Do not ask for passwords, account tokens, keys or private policy files.

## 3. Passive local Agent diagnostics — NO wsl.exe invocation

Using only already available UI/app metadata and safe read-only inspection that does not launch blocked programs:
- identify the exact local Agent product, version/build and execution mode;
- identify whether its command is run through a built-in sandbox, managed enterprise policy, configured executable denylist, OS application-control product, or another known layer;
- identify the exact source of the "Program Blacklist" wording if the product logs or official docs provide it;
- capture the exact block message and the command context as already recorded; do not reproduce the blocked action;
- inspect the Agent's visible settings/help/docs for the supported, administrator-authorized way to request/approve an allowed development command, if one exists;
- determine whether policy is user-controlled, device-admin-managed, or fixed by the host/service.

Use official documentation for the actual identified product/version only. If identity is not available from passive evidence, report UNKNOWN and ask user for the product name/screenshot. Do not guess a settings path.

Do NOT:
- retry wsl.exe or equivalent;
- launch WSL through another shell/script/tool;
- copy, rename, wrap or repackage wsl.exe;
- change PowerShell execution policy or AppLocker/WDAC/Defender/SmartScreen;
- disable antivirus/firewall/security controls;
- attempt UAC bypass, scheduled tasks, token manipulation or silent elevation;
- install WSL alternatives / third-party distro packages;
- change BIOS/UEFI, reboot, access the tablet or modify partitions.

The "administrator context" requirement in the prior ROUND17 draft is also withdrawn as a blanket precondition. Elevation is needed only if a later, identified official installation step actually requires it. Do not launch the whole Agent as administrator preemptively. First identify the execution-policy owner and supported approval path.

## 4. Fixed distro decision remains unchanged

Once the normal authorized WSL entry point is available, preserve the existing C: distro named Ubuntu entirely:
- do not launch/inspect its filesystem;
- do not update, move, export/import, unregister, delete, reset or overwrite it;
- install a separate Ubuntu-24.04 to D:\WSL\Ubuntu-24.04;
- do not change the default distro.

The installed Store WSL 2.7.3.0 and enabled VirtualMachinePlatform should be verified before any install. Do not blindly reinstall WSL or enable legacy Windows optional components. Do not enable HypervisorPlatform without an actual error proving it is necessary.

## 5. WSL deployment procedure — ONLY AFTER supported approval path is established

Only after the block source is identified and an authorized administrator/user has approved the normal command through the documented supported method, resume the install:
- verify wsl.exe --version, --status, --list --verbose and --list --online;
- confirm existing Ubuntu remains registered and target name/path are free;
- check D: free space >=100 GiB and deployment budget <=200 GiB;
- install Ubuntu-24.04 at D:\WSL\Ubuntu-24.04 with Microsoft's documented WSL CLI syntax and existing Store WSL;
- user personally completes first-run Linux username/password creation;
- verify Ubuntu 24.04 (noble), WSL Version 2 and registered D: BasePath;
- only then install official Ubuntu host packages and sync the official kernel-only common-android17-6.18 manifest;
- pin common to exact ACK commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a;
- capture repo manifest -r plus actual Bazel/Clang/Rust versions (source contract Clang r584948c, Rust 1.91.1.p3).

No patch application and no kernel compilation is part of ROUND17. Do not install global Bazel/Clang/Rust/JDK/NDK. Do not sync full AOSP or DerpFest.

## 6. Required result/report

If blocker product/policy identity is established but still requires user/admin action, upload a diagnostic-only report with status BLOCKED_PENDING_USER_OR_ADMIN_APPROVAL. Do not call this deployment complete.

If the policy is resolved through documented authorized means and deployment is subsequently completed, report the full exact evidence and status. If security policy remains fixed/non-overridable, stop and recommend a compliant alternative build host only after user decision; do not bypass.

Report path:
firmware-analysis/round17/round17_wsl_ack_workspace_deployment.txt

Upload only sanitized text to:
hhdy/matepad11-dby-w09-agent-reports, branch firmware-audit-v1.

After upload, stop. No device connection, unlocking, root, fastboot, flashing, partition writing or ROM work.

## 7. Next project stage

The parallel second-AI ROUND58 implementation branch is:
ai-parallel/round58-kleaf-target-audit.

It independently prepares a pinned-source full-image Kleaf target, final .config checker/tests and build runbook. This work does not require WSL execution and should continue while the local policy issue is diagnosed.

After ROUND17 produces a pinned workspace and ROUND58 is reviewed, primary AI will coordinate an actual disposable-source patch integration, Kconfig/schema verification and first Image build.

Stage A ACK 6.18.33 first; Android 17 DerpFest Stage B only after Stage-A boot and storage/basic hardware acceptance.
