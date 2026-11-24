Execute ROUND19 exactly as written in:
`firmware-analysis/round19/AGENT_TASK.md` on main.

Before doing anything, read the complete task file and confirm the existing local paths/tool inventory from the already-used ROUND3/ROUND12 work copy. This is not a public-repository research task.

Important:
- The private same-device DerpFest developer's implementation is not open source. Do not search for it or ask the user about it again.
- ROUND18 Image compilation is already complete. Do not redeploy WSL, repo init/sync, download source/toolchains, reapply patches, rerun Kconfig or rebuild Image.
- Reuse existing HOS4.3 work copies and parsed artifacts. Do not repeat ROUND7/8/12 wholesale; only execute the specifically new all-nine-DTBO and metadata tasks in ROUND19.
- Read-only local firmware analysis only. No device, ADB, fastboot, reboot, unlock/root, partition writes, flashing, repacking/deployment, AVB disable, tool installation/download, shell/security-policy workaround or elevation.
- If an exact input/tool is unavailable, record BLOCKED/UNKNOWN and continue the other independent work packages.
- Do not edit the stock firmware, existing parser/work copies or ACK original workspace.
- Upload only `firmware-analysis/round19/round19_hos43_boot_ramdisk_avb_dtbo_audit.txt` to `firmware-audit-v1`.
- After uploading the one report, stop. Do not modify main, the protected DTS branch, the second AI branch or PR #1.
