# ROUND151 — Root capability check and privileged read-only runtime evidence capture

- **Executor / assignee: WorkBuddy Agent (local Agent 1).**
- Not assigned to 2号 AI or 2号 Agent.
- User has explicitly authorized a one-time `su -c id` capability check and, only if it succeeds with user-approved authorization, a bounded privileged read-only data capture.
- Device: Huawei MatePad 11 (2021), DBY-W09 / HWDBY / KONA / SM8250.
- Current stock system observed in ROUND149: HOS 4.3.0.196(C00E100), Android 12 / API 31, kernel 4.19.157-perf+.
- Candidate ACK remains android17-6.18.33_r00, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.
- Candidate tree remains `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
- Branch: `workbuddy/round151-root-readonly-runtime-audit`.
- This round is **read-only runtime evidence capture only**. It does not authorize a candidate kernel boot, reboot, fastboot, recovery, flashing, partition reads, backup writes or any modification.

## 1. Objective

ROUND149 established live topology but ordinary ADB shell (`uid=2000(shell)`, SELinux Enforcing) was denied access to value-bearing data. This round first checks whether the device already exposes a usable `su` command. If and only if root access is granted by the device's existing root manager and `id` reports `uid=0(root)`, collect the minimum high-value runtime evidence that was blocked in ROUND149.

The target evidence is:
1. Full live stock FDT binary, including actual root cell values, /chosen values, /memory/reg values, all reserved-memory ranges, UFS node supply/OPP/ICC declarations and RPMh/ARC provider properties.
2. Current kernel ring buffer and boot/runtime logs, where permitted.
3. UFS host / PHY live sysfs state and readable descriptor/attribute values.
4. Regulator class software-reported state, voltage/current targets and consumer counts for all available regulators, especially L5/L6/L9/L17/S4/S8 and ARC level regulators.
5. Existing RPMh / GenPD / clock debug summaries **only if debugfs is already mounted and readable**.
6. Existing partition-name and sysfs size metadata only; no partition contents.

The primary expected outcome is either:
- **ROOT_READONLY_CAPTURE_COMPLETE/PARTIAL** if root is available, with precise read/deny status; or
- **ROOT_UNAVAILABLE_STOPPED** if root is absent, denied, or the authorization dialog is not approved.

## 2. Mandatory preflight and root decision gate

1. Verify the currently connected USB ADB device is the same DBY-W09 / HWDBY device seen in ROUND149. Use `adb devices -l` and the public-safe properties `ro.product.model`, `ro.product.device`, `ro.board.platform`, `ro.soc.model`.
2. Confirm there is exactly one connected device. Do not guess a serial or select a different device.
3. Record the current ordinary identity (`adb shell id`) and SELinux mode (`adb shell getenforce`).
4. Execute exactly one root capability check:
   ```sh
   adb shell su -c id
   ```
5. If an existing root manager displays an authorization dialog, pause and ask the user to approve a **one-time / this-session** grant. Do not click through, pre-approve, set permanent grant, automate approval, or bypass the manager. Once the user grants it, rerun the same `su -c id` check once.
6. Continue only if output clearly reports `uid=0(root)`. Save the output and timestamp.
7. If `su` is missing, denied, unavailable, errors, requests an unapproved grant, or does not yield uid 0, **stop the privileged phase immediately**. Do not try another root binary, exploit, recovery, boot image, alternate account, adb root, or privilege bypass. Produce a short report saying exactly why root was unavailable and that no privileged reads occurred.
8. Do not use `adb root`. Continue to use ordinary adbd plus `su -c <read command>` for each read operation. Never change SELinux mode.

## 3. Collection plan — only after uid=0 is confirmed

### 3.1 Live FDT — highest priority

- Read only `/sys/firmware/fdt` using root and copy the binary to the **host's local ROUND151 evidence folder**, not back to the tablet.
- Preferred binary-safe host capture: use a local Python subprocess with byte pipes around `adb exec-out` and `su -c 'cat /sys/firmware/fdt'`. Do not route the binary through PowerShell text redirection or `adb shell cat`, which can corrupt binary data.
- Validate:
  - FDT magic = `0xd00dfeed`;
  - header totalsize is sane and equals or is no larger than captured bytes;
  - record exact captured bytes and SHA-256;
  - do not hand-edit the binary.
- Keep the raw FDT **local only**. Do not upload it to GitHub, attach it publicly, or expose serial/MAC/secure boot identifiers. The GitHub report may contain file size, SHA-256, parsed technical fields, and redacted snippets only.
- If already-installed host tools exist (`dtc`, `fdtdump`, `fdtget`), use them locally to decode the binary. Do not install, download, or fetch tools. If none exist, use an already-installed local parser if available; otherwise preserve the FDT locally and report that decoding was unavailable. Do not invent decoded values.
- Extract and report numeric values and decoded tuples for:
  - root `#address-cells`, `#size-cells`, `compatible`, `model`, `qcom,board-id`, `qcom,msm-id` (redact unique device identifiers if present);
  - `/chosen`: `bootargs`, initrd start/end, `linux,uefi-*`, `linux,usable-memory-range`, `linux,efi-*` and vendor handoff properties. Redact serials, tokens or other unique identifiers from public output;
  - every enabled `/memory*` node, `device_type`, full `reg` values and tuple-decoded physical base/size;
  - all 37+ `/reserved-memory` child names, `reg`, `size`, `alignment`, `alloc-ranges`, `no-map`, `reusable`, phandles and references; calculate overlaps only after decoding the actual cell values;
  - `/soc/ufshc@1d84000`, UFS PHY node(s), `ufs_phy_gdsc`, six UFS regulator references and all relevant clocks/resets/power-domains/OPP/ICC properties;
  - seven level providers (`mmcxlvl`, `mxlvl`, `cxlvl`, `lmxlvl`, `lcxlvl`, `gfxlvl`, `ebilvl`), five ARC parent-supply dependencies, GDSC parent-supply links, and proxy-supply / qcom,proxy-consumer properties.
- Do not assume the file represents another boot; label it as the FDT received by the currently running stock HOS kernel.

### 3.2 Boot arguments, memory and kernel logs

Use root reads only:
- `/proc/cmdline`, `/proc/bootconfig` (may not exist on 4.19), `/proc/meminfo`, `/proc/iomem`, `/proc/zoneinfo` if readable.
- `dmesg` (one snapshot), record byte count and timestamp. Do not clear the ring buffer.
- Existing `logcat -b kernel -d` only if meaningful and readable; do not dump main/system app logs.
- Save raw outputs locally. Public report should only use relevant kernel lines, with serials, MACs, device identifiers, user/application data or security-sensitive tokens removed.
- No prolonged log streaming, tracing activation, stress test or load generation.

### 3.3 UFS host and PHY

Read existing sysfs values only. Target the ROUND149 path `/sys/devices/platform/soc/1d84000.ufshc` and the resolved PHY path from its `of_node` / driver links.

Collect, when readable:
- driver symlinks, modalias, uevent, runtime power status;
- host `qcom/{bus_speed_mode,clk_status,err_count,err_state,power_mode}`;
- `rpm_lvl`, `spm_lvl`, target dev/link state, devfreq `cur_freq` / available frequencies;
- UFS attributes and descriptors: current power mode, active ICC level, device/geometry/power/interconnect descriptors, reference clock and error counters;
- SCSI host/targets and block-device vendor/model/rev/type/size/queue metadata via sysfs only.
- record each path, value, permission failure and timestamp.

Do not invoke UFS commands that change power mode, gear, link state, FFU, BKOPS, purge, device configuration, or descriptors. Do not run benchmark, fsck, storage tests or stress.

### 3.4 Regulator / PMIC / RPMh / GenPD

For `/sys/class/regulator/regulator.*/`, collect readable:
- regulator name, type, state/status, microvolts, min/max microvolts, current limit if exposed, num_users, always_on and uevent;
- `of_node`, device and `-SUPPLY` links;
- explicitly map six UFS provider resources: L5, L6, L9, L17, S4 and S8; map ARC level children (MMCX/MX/CX all/AO and MMCX-sup/CX-sup) and their consumers.
For PMIC/SPMI/IIO:
- enumerate PMIC/SPMI device names and driver bindings;
- enumerate existing IIO device names/labels and only read clearly identified read-only ADC channel attributes if their mapping is explicit and already present;
- do not probe raw register addresses and do not infer a rail voltage from a generic ADC channel without a verified channel-to-net mapping.
For RPMh / GenPD:
- read relevant `/sys/bus/platform/devices/18200000.rsc` and provider runtime-power status where exposed;
- inspect `mount` output first. If `debugfs` is already mounted, read existing regulator, GenPD and clock summaries if accessible.
- **Do not mount debugfs or tracefs**; do not change mount namespace; do not enable trace events.
- Explicitly separate driver bound/probed, regulator runtime state, software-reported target voltage, PMIC ADC reading, and independently measured physical voltage. A regulator `microvolts` value is not proof of physical voltage.

### 3.5 Partition metadata only

- Read `/dev/block/by-name` names and symlink targets, `/sys/class/block/*/size`, logical/physical block size and read-only flags only.
- Do not open any `/dev/block/*` device, use `dd`, `cat`, `hexdump`, `tar`, `adb pull`, or hash any partition/block contents.
- No backup or restore attempt in this round. Partition metadata is not a substitute for a validated recovery path.

## 4. Data handling and privacy

- Create a new local folder named `r151-root-readonly` in the existing project evidence workspace. Do not reuse or modify the ROUND149 raw evidence.
- Preserve exact command text, exit code, stdout/stderr byte counts, timestamp, identity used (shell or root), and status: PASS / DENIED / NOT FOUND / EMPTY / ERROR.
- Generate a SHA-256 manifest for every local evidence file, including the raw FDT and raw dmesg capture.
- Raw FDT, raw kernel logs and any data that may contain serial/MAC/boot identifiers remain **local only**. Public GitHub report contains only hashes and sanitized technical extracts.
- Never upload user/application logcat buffers, serial numbers, IMEI, MAC addresses, keys, tokens, personal app content, userdata, or raw partitions.
- No network downloads, tool installation, dependency changes, or modifications to the local kernel worktree.

## 5. Explicit prohibitions

This round MUST NOT:
- run `adb root`, `su` except the approved `su -c id` check and approved root read commands, use exploit or privilege escalation bypass;
- disable SELinux, remount partitions, remount filesystems, mount debugfs/tracefs, alter permissions or ownership;
- run `reboot`, power-cycle, enter recovery/bootloader/fastboot, unlock, flash, temporary boot or start the candidate kernel;
- write any device file, sysfs/procfs node, Android property, setting, partition, block device, or firmware;
- access user data or application logs;
- read raw partition contents or create/claim a full device backup;
- run storage benchmarks, suspend/resume experiments, stress tests, or hardware power-cycle experiments;
- modify source, DTS, DTBO, config, patch series, build outputs, or candidate artifacts.

The user's authorization is specifically for Root capability verification and a bounded read-only collection. It is **not** authorization for destructive or boot-changing operations.

## 6. Analysis and reporting requirements

Compare new observations against:
- ROUND149 live ADB report;
- ROUND139 HOS4.3 static PMIC/UFS/ARC inventory;
- ROUND143 ARM64 FDT/RAM/EFI handoff analysis;
- ROUND146 ACK ARC/proxy support gap;
- ROUND147 candidate DTB ARC inventory;
- ROUND148 AI2 ARC/proxy portability review;
- fixed ACK commit and current candidate tree.

For every important claim, distinguish:
1. direct current-device read;
2. decoded property from the live FDT;
3. source-derived interpretation;
4. inference;
5. still unknown / denied.

Required final report:
- whether `su -c id` succeeded and exact root-manager authorization path (do not expose app account identifiers);
- full command and per-command status inventory;
- FDT byte count, magic, totalsize, SHA-256, validation and decode tooling;
- decoded root cell values, memory tuple list, reserved-memory ranges/overlap analysis, chosen handoff properties;
- actual UFS node and PHY declarations and comparison with candidate;
- six UFS rails' provider mapping and readable runtime state;
- ARC live graph and regulator status / use counts where accessible;
- Proxy consumer findings and whether evidence changes ROUND146/AI2 ROUND148;
- dmesg availability and relevant error/probe-defer lines, if any;
- updated gate matrix and exact blockers remaining;
- deviations, denied values and anything not independently verifiable;
- confirm no device state was modified.

## 7. Stop condition and deliverables

Create the report at:
`firmware-analysis/round151/WORKBUDDY_ROUND151_ROOT_READONLY_RUNTIME_AUDIT_REPORT.md`

Upload only the sanitized report and optional sanitized text extracts. Keep raw FDT/logs and the SHA-256 manifest local. Read back the uploaded report and verify the exact blob.

If Root is unavailable, still publish a concise ROOT_UNAVAILABLE_STOPPED report at the same path and stop.

After report upload and read-back verification, STOP. Do not start ROUND152, do not modify code, do not build, do not boot, do not flash, and do not reboot.
