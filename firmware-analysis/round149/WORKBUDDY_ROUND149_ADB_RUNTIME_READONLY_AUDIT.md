# ROUND149 — WorkBuddy Agent ADB runtime evidence capture (read-only)

## Assignment identity

- **Assigned executor: WorkBuddy Agent (local Agent 1).**
- This is NOT 2号 Agent and NOT 2号 AI.
- 1号 AI (ChatGPT) owns task design, later independent review, source correlation and next-step decisions.
- The user has explicitly authorized connecting the Huawei MatePad 11 (2021) DBY-W09 tablet for device testing. This round is authorized for **ADB connection and read-only runtime evidence collection only**.

## Goal

Replace avoidable offline assumptions with evidence from the currently installed, working HOS4.3 system. Collect enough read-only ADB evidence to compare actual board identity, boot arguments, UFS host/device visibility, regulator availability, power-domain/RPMh observability, kernel logs, partition layout metadata and (only if naturally readable) the current boot's final FDT.

This is a diagnostic evidence round. It does not boot or install the candidate kernel. It must not modify the currently installed system.

## Device / project baseline

- Device: Huawei MatePad 11 (2021), DBY-W09 / KONA / Qualcomm SM8250 v2.1.
- Target kernel: Android Common Kernel `android17-6.18.33_r00`.
- Pinned ACK commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`.
- Candidate content tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
- Existing R3/ROUND135 and ROUND140 are offline build evidence only; neither proves the candidate boots on the tablet.
- Critical open topics: final RAM/FDT handoff; HOS-to-ACK regulator/ARC/proxy semantics; UFS supply and runtime sequencing; MMCX/CX/MX vote propagation; AVB / DTBO / boot-v2 / ramdisk; backup and tested recovery.

## Authorization and hard safety boundary

### Allowed in this round

1. Connect the tablet over USB and use standard `adb` commands.
2. If Android displays its normal USB debugging authorization dialog, ask the user to approve it on the tablet. Do not bypass the prompt.
3. Run read-only shell queries and collect logs from the already-running stock HOS4.3 installation.
4. Read sysfs, procfs, properties, and metadata when normal ADB shell permissions allow it.
5. If `/sys/firmware/fdt` is readable by the ordinary ADB shell user, copy that existing file as a read-only artifact, hash it locally, and record its size. If denied, record the exact permission error and stop there.
6. Capture narrowly filtered kernel/system log lines for UFS, RPMh, regulator, PMIC, power-domain, SMMU/IOMMU, storage and boot topics.
7. Inspect partition **names, symlink targets, reported sizes and layout metadata only**.

### Explicitly forbidden

- No reboot, power cycle, bootloader/recovery transition or fastboot mode.
- No `adb root`, `su`, privilege escalation, permission changes, SELinux changes, remounts, debugfs mounts or attempts to bypass access controls.
- No writes to sysfs, procfs, debugfs, properties, settings, partitions, block devices or files on the tablet.
- No `adb push`, package install/uninstall, disable/enable, shell scripts written to the device, or configuration changes.
- No `dd`, `cat` or other reads of raw partition/block-device contents. Partition names/sizes metadata only.
- No flashing, unlocking, AVB changes, boot image construction, temporary boot, or candidate-kernel boot.
- No stress test, benchmark, suspend/resume cycle or deliberate UFS workload.
- Do not retry a denied read through root or another account.
- Do not download/install tools or dependencies. Use the already-installed host ADB only.
- Do not inspect another Agent's private workspace.

**Any proposed operation outside these boundaries requires a new explicit user authorization.** The user's permission to connect/test does not authorize flashing or writing partitions.

## Step 0 — Host and connection identity

1. Detect host OS and current ADB executable/version without installing anything.
2. Record `adb version`.
3. Run `adb devices -l`.
4. Confirm exactly which connected serial is the DBY-W09. Do not print full serial in the public report; record a redacted suffix or local evidence hash.
5. If device state is `unauthorized`, stop and ask the user to approve the normal Android USB debugging prompt. Do not bypass.
6. If no device or multiple ambiguous devices appear, stop and report the exact blocker rather than selecting the wrong device.
7. Do not proceed unless the target is identified and `device` state is confirmed.

## Step 1 — Basic board, OS and boot identity

Capture outputs, with user-identifying values redacted before upload:

```sh
adb shell getprop ro.product.model
adb shell getprop ro.product.device
adb shell getprop ro.product.board
adb shell getprop ro.hardware
adb shell getprop ro.boot.hardware
adb shell getprop ro.build.fingerprint
adb shell getprop ro.build.version.release
adb shell getprop ro.build.version.sdk
adb shell getprop ro.bootloader
adb shell getprop ro.boot.slot_suffix
adb shell getprop ro.boot.dtbo_idx
adb shell getprop ro.boot.bootdevice
adb shell uname -a
adb shell cat /proc/version
adb shell cat /proc/cmdline
adb shell cat /proc/bootconfig
```

For missing paths or properties, record NOT FOUND. Do not infer that absence means a boot path is unused.

Also read, if normally accessible:

```sh
adb shell 'tr "\\000" "\\n" < /proc/device-tree/model'
adb shell 'tr "\\000" "\\n" < /proc/device-tree/compatible'
```

If the device-tree paths do not exist or are denied, record that.

## Step 2 — UFS and block-device runtime evidence

Use ordinary ADB shell only. Read these where present:

- `/sys/class/scsi_host/` directory listing.
- `host*/proc_name`, `host*/uevent`, and other plainly readable host identity fields.
- `/sys/class/ufs/` listing and readable identity/state attributes, if present.
- `/sys/block/` listing; for the actual UFS-backed SCSI block device, record `device/vendor`, `device/model`, `device/rev`, `size`, `queue/logical_block_size`, `queue/physical_block_size` and `stat` if present.
- Relevant `/sys/devices/platform/` UFS host path and its `uevent` / `power/runtime_status` only when readable.
- Read-only `/proc/mounts` and `/proc/partitions` metadata if needed to establish current storage identity.

Do not assume the first `sd*` device is the UFS device without tracing its sysfs path. Do not run benchmarks or I/O load. Do not read raw block devices.

## Step 3 — Regulator / PMIC / RPMh / power-domain observations

List and read only attributes that already exist and are accessible:

- `/sys/class/regulator/` names and available `name`, `state`, `status`, `microvolts`, `current_limit`, `num_users`, `type` attributes.
- Relevant PMIC / RPMh platform device directory names and `uevent` / `power/runtime_status`.
- `/sys/kernel/debug/regulator/regulator_summary`, `/sys/kernel/debug/pm_genpd/pm_genpd_summary`, `/sys/kernel/debug/clk/clk_summary`, or RPMh debug paths **only if already accessible without mounting debugfs or escalating privileges**.
- Any existing read-only power-domain summary or device link information under sysfs.

For every item, distinguish:
1. device-tree/provider node exists;
2. driver successfully probed;
3. runtime state is reported;
4. actual physical voltage / PMIC input is directly measured.

Do not treat an absent sysfs attribute as proof of absent hardware. Do not claim a physical rail voltage from a regulator name or DT property alone.

## Step 4 — Kernel and system logs

Attempt ordinary unprivileged reads:

```sh
adb shell dmesg
adb logcat -b kernel -d -v threadtime
adb logcat -b main -b system -d -v threadtime
```

Permission denial is an acceptable result; do not use root or attempt bypass.

Before upload, filter for relevant lines, case-insensitive:

`ufs|ufshcd|u​​fs-qcom|rpmh|rpmhpd|regulator|pmic|pm8150|genpd|power domain|mmcx|mmc[xX]|cx|mx|smmu|iommu|scsi|scsi host|sdhci|dtbo|bootconfig|memory|reserved-memory|avb|dm-verity|failed|timeout|probe defer`

Preserve timestamps and a small amount of surrounding context. Keep raw logs locally. Do not upload full unfiltered logcat if it contains account identifiers, notifications, message content, Wi-Fi data, location, tokens or other unrelated personal data.

## Step 5 — Current final FDT (only if naturally accessible)

1. Check whether ordinary ADB shell can read `/sys/firmware/fdt`.
2. If readable, copy it read-only to the Agent's local evidence folder, record byte size and SHA-256, and parse a local copy to report:
   - FDT header / total size;
   - root `#address-cells` and `#size-cells`;
   - root model / compatible;
   - all memory-node `reg` tuples and status;
   - `/chosen` boot metadata including `linux,usable-memory-range` and `linux,uefi-*` if present;
   - complete `/reserved-memory` node names, reg/size, no-map/reusable, phandles and memory-region references.
3. Clearly label it as the current stock HOS4.3 boot's FDT, not the candidate ACK DTB and not necessarily a future boot's FDT.
4. If denied, record denial and do not try `su`, root, another path or permission changes.
5. Do not upload the binary FDT unless necessary; report hash and parsed structural facts. Keep the local original intact.

## Step 6 — Partition metadata and recovery readiness (metadata only)

Read:

- `/proc/partitions`.
- `ls -l /dev/block/by-name` and/or `/dev/block/bootdevice/by-name` if accessible.
- `getprop ro.boot.slot_suffix`, `ro.boot.slot`, `ro.boot.verifiedbootstate`, `ro.boot.flash.locked`, `ro.boot.vbmeta.device_state`, `ro.boot.avb_version` where present.

Record partition names, sizes (if exposed), symlink targets and slot properties only. Do not read partition data, calculate hashes of partition contents, or test restore. Do not state that a recovery path is proven merely because a recovery partition exists.

## Step 7 — Deliverable and reporting format

Write report:

`firmware-analysis/round149/WORKBUDDY_ROUND149_ADB_RUNTIME_READONLY_AUDIT.md`

Branch:

`workbuddy/round149-adb-runtime-readonly-audit`

The report must include:

1. Executor identity (WorkBuddy Agent), date/time with timezone, host OS, ADB version.
2. Device identification result and redacted serial identifier.
3. Exact command inventory and per-command status: PASS / DENIED / NOT FOUND / NOT RUN.
4. Board, build, boot, cmdline, bootconfig and DT identity.
5. UFS host / SCSI / storage mapping with actual sysfs path evidence.
6. Regulator / PMIC / RPMh / genpd evidence, each classified as node / probe / runtime / physical measurement.
7. Filtered kernel logs with timestamps, including negative results and permission denials.
8. Current stock FDT facts/hash or precise access denial.
9. Partition metadata only, with no claim of a tested backup/recovery route.
10. A correlation table against ROUND139, ROUND141, ROUND143, ROUND146 and the candidate's known UFS regulator mapping.
11. Remaining UNKNOWNs and the smallest next evidence action for each.
12. Explicit safety declaration: no reboot, no root, no writes, no raw partition reads, no flashing, no candidate boot.

Keep raw, unredacted capture files locally in the Agent's evidence directory. Upload only relevant, minimized and redacted excerpts. Include SHA-256 hashes of locally retained raw evidence files so the user can verify them locally without exposing personal data.

After upload, fetch/read the report back to verify that the uploaded content matches the local report, then stop. Do not start another test round or change any device state.

## Stop conditions

Stop immediately and report if:
- device is not recognized or is ambiguous;
- USB debugging is unauthorized;
- ADB disconnects unexpectedly;
- a command appears to require privilege escalation;
- any requested file is denied;
- a command would write, reboot, flash, change settings or access raw partition data.

## Expected outcome

This round should give us real HOS4.3 runtime observations and possibly the current stock final FDT without changing the tablet. It is **not** a candidate-kernel boot test and does not close first-boot authorization by itself.
