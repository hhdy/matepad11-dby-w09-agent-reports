# ROUND16 local Agent start prompt

You are authorized by the user in the current ChatGPT conversation to deploy the Linux kernel build environment on the user's Windows PC, strictly within the scope below.

## Read first

1. `PROJECT_HANDOFF.md`
2. `AGENT_TASK.md`
3. `firmware-analysis/round16/AGENT_TASK.md`

## Execute

Execute ROUND16 in full, not merely summarize it:

- Inspect WSL/security/admin/virtualization state.
- If allowed, install WSL2 + Ubuntu 24.04 LTS at `D:\\WSL\\Ubuntu-24.04`.
- Let the user privately create the Linux username/password at first launch; do not log it.
- Install the minimal Ubuntu dependencies from official Ubuntu repositories.
- Initialize and sync only the official kernel manifest branch `common-android17-6.18`.
- Pin `common/` to `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.
- Save `repo manifest -r`, verify the manifest-provided Bazel/Clang/Rust toolchain, and keep the source checkout pristine.
- Upload the one sanitized report specified by ROUND16 to `firmware-audit-v1`.

## Critical limits

- This is a real execution task. Do not simply stop after writing a plan.
- Do not bypass a Windows security block, UAC, endpoint protection or application-control policy. If `wsl.exe` is blocked again, stop and report the blocker; never copy/rename it or disable security software.
- Do not change BIOS/UEFI settings or force a reboot.
- Do not remove or overwrite any existing WSL distro.
- Preserve at least 100 GiB free on D: and do not exceed the 200 GiB deployment budget.
- Do not install global Windows Bazel/Clang/Rust/JDK packages; use the official Repo-synced Kleaf prebuilts.
- Do not download a full AOSP/DerpFest platform tree.
- Do not apply any kernel patches or run Kconfig/schema/DTB checks.
- Do not compile the kernel in ROUND16.
- Do not connect to, unlock, root, flash or write the DBY-W09 device.
- Do not modify `main`, `ack18-dby-w09-dts-draft`, ROUND54 branch or PR #1.

If admin rights, a reboot or first-run user input is needed, request the user action and pause safely. Resume only when the needed action has been completed. Do not claim completion until the report has been uploaded and its exact URL/commit SHA are verified.

After successful report upload, stop. The next task will separately authorize patch integration and kernel compilation.
