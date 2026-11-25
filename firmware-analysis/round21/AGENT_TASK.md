# ROUND21 — first-stage /dev population and UFS pinctrl / DTBO dependency audit

**Owner:** local WorkBuddy Agent; offline, read-only local artefact and source inspection  
**Device:** Huawei MatePad 11 (2021) DBY-W09 / KONA / SM8250  
**Kernel:** ACK android17-6.18.33_r00, common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Inputs:** existing ROUND18 build/config/source tree; existing ROUND19 HOS4.3 base-DTB, nine-DTBO and standalone ramdisk work copies.

## 0. Purpose

ROUND20 established two concrete gaps in the successful ROUND18 Image configuration:
- CONFIG_DEVTMPFS is not set.
- CONFIG_PINCTRL_MSM is not set.

These are not yet proven boot blockers. ROUND21 must inspect the actual HOS4.3 first-stage /init and the actual UFS host/PHY device-tree properties to determine whether either missing driver is genuinely required before the first system partitions can mount.

This round also records the exact UFS-related properties from base DTB and each of the nine DTBO variants. The board-id 0x206a / VG entry is a candidate variant, not proven runtime selection. Never merge all variants or label a variant as selected without same-boot evidence.

## 1. Hard boundaries — do not cross

READ ONLY. Do NOT:
- redeploy or alter WSL, run repo init/sync, fetch source, download firmware/toolchains or install packages;
- repeat the ROUND19 full firmware/AVB/DTBO scan or ROUND20 Image/EFI/compression audit;
- modify the ACK source tree, .config, config fragment, any DTS/DTBO, firmware input or existing report;
- run olddefconfig, menuconfig, Kleaf, Bazel or any kernel build;
- create a patch, DTB, DTBO, boot.img, candidate package, AVB footer or signature;
- connect to the tablet, run ADB/fastboot/recovery, reboot, unlock/root, flash or write any partition;
- modify main source files, ack18-dby-w09-dts-draft, ai-parallel/stagea-port-until-boot or PR #1.

Use only the already existing ROUND18 and ROUND19 local work copies and installed tools. If an input or required tool is missing, report BLOCKED for that subtask; do not reconstruct by re-extracting.

## 2. Work package A — Android first-stage /init and /dev

Use the exact standalone ramdisk.img and its extracted /init from the ROUND19 work copy. Do not execute /init.

Inspect:
1. ELF identity, architecture, static/dynamic linkage, symbol/section/strip state.
2. Strings and, where local tools allow, static disassembly around first-stage mount and device-node handling.
3. Evidence for:
   - mount("devtmpfs", "/dev", "devtmpfs", ...);
   - mount("tmpfs", "/dev", "tmpfs", ...);
   - mkdir/chmod/chown or mknod handling under /dev;
   - /dev/block, /dev/block/by-name, ueventd, netlink uevents, device-handler or coldboot handling;
   - first-stage fstab lookup and block-device discovery;
   - any fallback path when devtmpfs mount fails.
4. Separate proven code paths from mere strings, imported function names, dead/unreachable text or static-analysis uncertainty.
5. Determine whether this exact /init appears to require kernel devtmpfs, can use tmpfs + userspace mknod/uevent handling, or cannot be decided without deeper disassembly/source.

No claims from strings alone. If symbols are stripped and installed disassembly is insufficient, mark PARTIAL/UNKNOWN and list what evidence would settle it. Do not use dynamic execution, emulation or device execution.

## 3. Work package B — base DTB and nine DTBO UFS mapping

Reuse the already parsed base DTB and nine overlays. Do not redo the complete tree inventory. Limit the analysis to:
- UFS host (for example ufs_mem_hc), UFS PHY, UFS crypto if present;
- clocks, clock-names, resets, reset-names, power-domains, required-opps;
- vcc-supply, vccq-supply, vccq2-supply, vdda-phy-supply, vdda-pll-supply, regulator-always-on and related UFS rail properties;
- pinctrl-names, pinctrl-0, pinctrl-1 and any referenced GPIO properties;
- provider nodes and regulator parent-supply chains reached by those exact phandles.

For the base DTB and each of the nine DTBO entries, report:
- whether each relevant node is present/changed/disabled/enabled;
- the exact properties added, replaced or deleted by the overlay;
- every referenced phandle resolved to its provider node and compatible;
- whether a UFS pinctrl state exists and which Qualcomm pinctrl provider owns it;
- whether UFS rails have explicit parent-supply chains in the source DT;
- whether the resulting tree would need the Qualcomm TLMM driver for UFS probe or rail control.

Check all nine variants individually. Do NOT apply overlays together. Do NOT assume board-id 0x206a/VG is selected. You may mark it as the matching board-id candidate based on ROUND19, but state that runtime selection is unknown.

If the prior ROUND19 parser output/work copy is unavailable, report BLOCKED instead of re-extracting or re-parsing the full DTBO set.

## 4. Work package C — exact ACK Kconfig dependency and config gap review

Use only the pinned ACK source already in the ROUND18 work tree and its final built .config:
- locate config DEVTMPFS, DEVTMPFS_MOUNT and required dependencies/selects;
- locate config PINCTRL_MSM and its dependencies/selects/compatible coverage;
- identify the relevant SM8250/SM8250 TLMM compatible string and the driver that binds it;
- compare these with the base/overlay UFS pinctrl provider compatible(s);
- explain whether enabling only the Kconfig symbol would be enough or if another dependency must also be enabled;
- identify whether DEVTMPFS_MOUNT is necessary for this Android first stage or merely a kernel auto-mount convenience, based on work package A.
No .config edits, fragments, Kconfig runs or rebuilds.

## 5. Work package D — decision matrix and next-build recommendation

Provide a concise matrix:
- DEVTMPFS: evidence that it is required / not required / unresolved for this init and exact first-stage path;
- DEVTMPFS_MOUNT: required / optional / not required, and why;
- PINCTRL_MSM: required by UFS DT / not referenced by UFS / unresolved;
- any UFS-specific pinctrl states and their state names;
- UFS supply parent chains that must be preserved in board DTS;
- which overlay variants change UFS properties, with runtime selection still marked UNKNOWN.

Give a next-build recommendation limited to the config delta that evidence supports. Do not apply it. Explicitly separate must-enable from prudent-but-unverified. If the DT proves UFS uses Qualcomm TLMM, recommend PINCTRL_MSM built-in. If /init relies on devtmpfs or there is strong first-stage requirement, recommend DEVTMPFS built-in; do not automatically recommend DEVTMPFS_MOUNT unless userspace behavior needs it.

## 6. Deliverable

Upload one UTF-8 sanitized text report only to:
firmware-analysis/round21/round21_first_stage_devtmpfs_and_ufs_pinctrl_overlay_audit.txt
on branch firmware-audit-v1.

Include:
- PASS / PARTIAL / BLOCKED for each work package;
- exact local paths only if non-sensitive and already present in prior reports; do not expose usernames or personal directory details;
- exact source paths/line ranges for Kconfig;
- tool names/versions;
- per-overlay UFS property matrix;
- /init evidence hierarchy and limitations;
- config recommendation and unresolved dependencies;
- statement that no source/config/firmware/device was modified or accessed.

Do not upload /init, DTB/DTBO, firmware, source, binaries, disassembly dumps or keys.

## 7. Stop rule

After the single report is uploaded successfully, stop. Do not start another round, edit configuration, rebuild the kernel or contact the device.