# ROUND149 — WorkBuddy Agent ADB runtime evidence capture (read-only)

**Status: PARTIAL — structure, presence and topology established at runtime; nearly all property/attribute *values* are denied to the ordinary ADB shell user.**

Three results are worth stating up front:
1. The live `/chosen` carries **no** `linux,uefi-*` property and **no** `linux,usable-memory-range` — this boot received no EFI memory map through the device tree (direct observation, exhaustive list).
2. The HOS **ARC nesting is real at runtime**: `-SUPPLY` symlinks show MMCX ⇐ MX-mmcx-sup ⇐ CX-mmcx-sup as a resolved nested regulator chain, with 11 GDSCs consuming the MMCX level rail.
3. **Nothing value-level is readable**: `/sys/firmware/fdt` is `-r-------- root`, `dmesg` is denied, the logcat kernel buffer is empty, and debugfs is unavailable — so RAM tuples, bootargs, rail voltages and RPMh votes all remain UNKNOWN.

This round replaced a set of offline assumptions with live observations from the currently installed, working HOS4.3 system. It did **not** boot, flash, modify, or reboot anything, and it does **not** close first-boot authorization.

---

## 1. Executor identity, time and host

| Item | Value |
|---|---|
| Executor | WorkBuddy Agent (local Agent 1). Not 2号 Agent, not 2号 AI. |
| Round | ROUND149 only |
| Date/time (start → end) | 2026-11-26 21:40 → 21:58 (host local, GMT+8). Device clock read 21:48:53 at capture time. |
| Host OS | Windows 11 Pro for Workstations, NT 10.0.26200 |
| ADB executable | `D:\Tools\platform-tools\adb.exe` (pre-existing; nothing installed or downloaded) |
| `adb version` | `Android Debug Bridge version 1.0.41` / `Version 37.0.3-16887417` / `Installed as D:\Tools\platform-tools\adb.exe` / `Running on Windows 10.0.26200` |
| Connection | USB, single device, state `device` (no `unauthorized` prompt appeared) |

Nothing was installed on the host or on the tablet. No `apt`/`pip`/`choco`/winget invocation, no tool download.

---

## 2. Device identification

```
List of devices attached
W3VB…4537   device product:DBY-W09 model:DBY_W09 device:HWDBY transport_id:1
```

- Full serial is **redacted**. Local redaction record: `sha256(<full serial as printed by adb devices>) = eadf51795bd0b1511b284e118e6d8d164a9541da068044771c579ae2070c2ef0`; visible suffix is the last four digits, `4537`. The literal string is present only in the local raw captures (`step1/19.txt`, `step6/…`), which are **not** uploaded.
- Exactly one device was attached; no ambiguity, no selection fallback.
- `id` → `uid=2000(shell) gid=2000(shell) groups=2000(shell),1004(input),1007(log),1011(adb),1015(sdcard_rw),1028(sdcard_r),1078(…)` — ordinary shell user throughout. **No `su`, no `adb root`, no privilege escalation attempt at any point.**
- `getenforce` → `Enforcing`.

---

## 3. Command inventory and per-command status

252 shell commands were executed in 16 batches. Every command, its exact text, exit code, output byte count and classification is retained locally in `evidence/raw/index-step*.tsv`. Distribution:

| Batch | Scope | Commands | PASS | DENIED | NOT FOUND | EMPTY | other |
|---|---|---:|---:|---:|---:|---:|---:|
| step1 | board/OS/boot identity | 25 | 18 | 3 | 1 | 2 | 1 |
| step2 | UFS/SCSI/storage discovery | 14 | 4 | 7 | 3 | 0 | 0 |
| step2b | UFS descriptor/attribute census | 20 | 6 | 12 | 1 | 0 | 1 |
| step3 | regulator/debugfs/FDT probes | 20 | 7 | 8 | 3 | 1 | 1 |
| step3b | regulator+PMIC+RPMh enumeration | 20 | 12 | 3 | 4 | 1 | 0 |
| step3c | regulator→device mapping, DT root | 20 | 16 | 3 | 1 | 0 | 0 |
| step3d | regulator `of_node` property probes | 16 | 2 | 14 | 0 | 0 | 0 |
| step4 | kernel/userspace logs | 12 | 7 | 2 | 2 | 1 | 0 |
| step5 | live DT structure at root/chosen | 18 | 16 | 2 | 0 | 0 | 0 |
| step5b | `/memory`, `__symbols__`, misc | 14 | 9 | 3 | 1 | 1 | 0 |
| step6 | partition metadata, slot/AVB props | 20 | 14 | 1 | 0 | 5 | 0 |
| step6b | partition sizes, FDT access probes | 15 | 4 | 9 | 0 | 2 | 0 |
| step7 | memory/SoC identity | 15 | 10 | 1 | 2 | 1 | 1 |
| step8 | regulator supply-link sweep (partial) | 9 | 8 | 1 | 0 | 0 | 0 |
| step9 | full 82-regulator `of_node`/`-SUPPLY` map | 7 | 6 | 0 | 0 | 1 | 0 |
| step10 | UFS rail → provider → DT node paths | 7 | 7 | 0 | 0 | 0 | 0 |
| **Total** | | **252** | **146** | **69** | **18** | **15** | **4** |

Definitions used: **PASS** = command produced its intended data; **DENIED** = SELinux or file-permission refusal (`Permission denied` / `klogctl: Permission denied`); **NOT FOUND** = path or property does not exist on this build; **EMPTY** = command succeeded but the value is absent/empty; **other** = non-zero exit for a reason other than denial (e.g. `readlink -f` on a directory).

Representative commands and exact outcomes are quoted inline in §4–§9. No command in this round wrote to the device: no `adb push`, no `setprop`, no `pm`, no `mount`, no `remount`, no file creation, no `debugfs` mount.

---

## 4. Board, build, boot, cmdline and DT identity

### 4.1 Product / build identity (all PASS)

| Property | Value |
|---|---|
| `ro.product.model` | `DBY-W09` |
| `ro.product.name` | `DBY-W09` |
| `ro.product.device` | `HWDBY` |
| `ro.product.board` | `DBY` |
| `ro.hardware` / `ro.boot.hardware` | `qcom` / `qcom` |
| `ro.board.platform` | `kona` |
| `ro.soc.model` / `ro.soc.manufacturer` | `SM8250` / `QTI` |
| `ro.build.fingerprint` | `HUAWEI/DBY-W09/HWDBY:12/HUAWEIDBY-W09/104.3.0.196C00:user/release-keys` |
| `ro.build.display.id` | `DBY-W09 4.3.0.196(C00E100)` |
| `ro.build.version.release` / `.sdk` / `ro.build.type` | `12` / `31` / `user` |
| `hw_sc.build.platform.version` | `4.3.0` |

### 4.2 Kernel

`uname -a`:
```
Linux localhost 4.19.157-perf+ #1 SMP PREEMPT Fri Aug 30 08:34:06 CST 2024 aarch64
```
`/proc/version`: `Linux version 4.19.157-perf+ (HarmonyOS@localhost) (clang version 10.0.7 for Android NDK, GNU ld (binutils-2.27-…) …)`.

`/proc/cpuinfo`: `Processor: AArch64 Processor rev 14 (aarch64)`, `CPU implementer 0x51 / part 0x805`, 8 CPUs (`cpu0..cpu7`).

Uptime at capture: `21:48:53 up 3 days, 20:28` → this boot started ≈ **2026-11-23 01:20:53** device local time. Load average 9.89/8.87/8.47 (busy, not a quiet device — relevant when reading any timing).

### 4.3 Boot properties (all PASS unless noted)

| Property | Value |
|---|---|
| `ro.boot.bootdevice` | `1d84000.ufshc` |
| `ro.boot.boot_devices` | `soc/1d84000.ufshc` |
| `ro.boot.dtbo_idx` | `2` |
| `ro.boot.console` | `ttyMSM0` |
| `ro.boot.baseband` | `mdm` |
| `ro.boot.bootreason` | `reboot,shell` |
| `ro.boot.dynamic_partitions` | `true` |
| `ro.boot.fstab_suffix` | `default` |
| `ro.boot.hardware` | `qcom` |
| `ro.boot.product.hardware.sku` | `DBY-W09` |
| `ro.boot.selinux` | `enforce` |
| `ro.boot.usbcontroller` | `a600000.dwc3` |
| `ro.boot.loader` | `unknown` |
| `ro.boot.slot_suffix` | **empty** (A-only layout; no `_a`/`_b`) |
| `ro.boot.slot` | **empty** (EMPTY) |
| `ro.boot.verifiedbootstate` | `orange` |
| `ro.boot.flash.locked` | `0` |
| `ro.boot.vbmeta.device_state` | **empty** (EMPTY) |
| `ro.boot.avb_version` | **empty** (EMPTY) |
| `ro.boot.revision` | **empty** (EMPTY) |
| `ro.boot.serialno` | present, redacted (same serial as §2) |

`ro.boot.verifiedbootstate=orange` and `ro.boot.flash.locked=0` are recorded **as reported**. `orange` is the AOSP-listed unlocked state; however this is a vendor HOS build whose own lock-state convention is not established by this capture, so **no claim is made here about the effective bootloader lock state**. `vbmeta.device_state` and `avb_version` are absent, so the AOSP AVB property surface is only partially populated.

### 4.4 cmdline, bootconfig and DT identity

| Item | Result |
|---|---|
| `cat /proc/cmdline` | **DENIED** — `cat: /proc/cmdline: Permission denied` |
| `cat /proc/bootconfig` | **NOT FOUND** — `No such file or directory` (4.19 kernel; bootconfig is a 5.x feature) |
| `/proc/device-tree/model` | **DENIED** — `sh: can't open /proc/device-tree/model: Permission denied` |
| `/proc/device-tree/compatible` | **DENIED** — same |
| `/proc/device-tree` | `lrwxrwxrwx … /proc/device-tree -> /sys/firmware/devicetree/base` (symlink readable) |

The DT property **names and byte lengths** are readable even though the **values** are not (see §8). Root-level properties on the live FDT:

| Root property | Length (bytes) | Note |
|---|---:|---|
| `#address-cells` | 4 | one cell |
| `#size-cells` | 4 | one cell |
| `compatible` | 33 | value denied |
| `model` | 34 | value denied |
| `interrupt-parent` | 4 | one cell |
| `qcom,board-id` | 8 | two cells — vendor board match property |
| `qcom,msm-id` | 8 | two cells — vendor SoC match property |
| `name` | 1 | empty string |

So the live stock FDT carries vendor `qcom,board-id` / `qcom,msm-id` match properties, which the candidate DTB (compiled from the upstream-model board file) does **not** carry. This is recorded as an observation, not a defect: the candidate is a different DT with a different match strategy.

---

## 5. UFS host / SCSI / storage mapping (actual sysfs paths)

### 5.1 Which block device is actually UFS — traced, not assumed

`/sys/block/` contains `dm-0..4`, `loop0..39`, `ram0..15`, `zram0`, and `sda..sdf`. The UFS-backed device was identified by following the symlink, not by taking the first `sd*`:

```
sdf -> ../devices/platform/soc/1d84000.ufshc/host0/target0:0:0/0:0:0:5/block/sdf
```

`readlink -f /sys/block/sdf` → `/sys/devices/platform/soc/1d84000.ufshc/host0/target0:0:0/0:0:0:5/block/sdf`.

**The readable UFS block device is `sdf`, LUN 5.** `sda` … `sde` appear in `/sys/block` as `l????????? ? ? ? ? ? sda -> ?` — the symlink metadata itself is not stat-able by uid 2000, so their LUN mapping is **not established by this capture** (see §9 for the by-name partition evidence that does reach them).

### 5.2 Host / SCSI topology

| Path | Result |
|---|---|
| `/sys/class/scsi_host/` | one entry, `host0` (PASS) |
| `/sys/class/scsi_host/host0/proc_name` | **DENIED** |
| `/sys/class/scsi_host/host0/unique_id` | **DENIED** |
| `/sys/class/scsi_host/host0/uevent` | **DENIED** |
| `/sys/class/ufs/` | **NOT FOUND** — `ls: /sys/class/ufs/: No such file or directory` (vendor 4.19 does not create a `ufs` class) |
| `/sys/class/scsi_device/` | 9 entries: `0:0:0:0`, `0:0:0:1`, `0:0:0:2`, `0:0:0:3`, `0:0:0:4`, `0:0:0:5`, plus `0:0:0:49456`, `0:0:0:49476`, `0:0:0:49488` (PASS) |
| `/sys/bus/platform/drivers/ufshcd-pltfrm/` | **NOT FOUND** |
| `/sys/bus/platform/drivers/ufs_qcom/` | **NOT FOUND** |
| `/sys/bus/platform/drivers/` listing | contains `ufshcd-qcom`, `ufs_qcom_phy_qmp_v3`, `ufs_qcom_phy_qmp_v3_660`, `ufs_qcom_phy_qmp_v4`, `ufs_qcom_phy_qmp_v4_lito`, `ufs_qcom_phy_qrbtc_sdm845` (PASS) |

Two naming facts worth recording: the vendor driver is named `ufshcd-qcom`, not the ACK 6.18 name `ufs_qcom`, and the vendor kernel exposes a separate UFS PHY driver family. Those are naming/architecture differences between HOS4.3 (4.19) and the pinned ACK (6.18), not defects.

### 5.3 UFS host device directory — rich and partly readable

`/sys/devices/platform/soc/1d84000.ufshc/` (PASS, full listing captured):

```
driver -> ../../../../bus/platform/drivers/ufshcd-qcom
of_node -> ../../../../firmware/devicetree/base/soc/ufshc@1d84000
attributes/            device_descriptor/     geometry_descriptor/
health_descriptor/      power_descriptor/      interconnect_descriptor/
string_descriptors/     qcom/                  devfreq/1d84000.ufshc
host0/                 power/                 flags/         wakeup/
clkgate_delay_ms_perf  clkgate_delay_ms_pwr_save  clkgate_enable
max_bus_bw             driver_override        subsystem
modalias (r--r--r--)   rpm_lvl (rw)           spm_lvl (rw)
rpm_target_dev_state   rpm_target_link_state  spm_target_dev_state
spm_target_link_state  (all r--r--r--)
```

`of_node` resolves to `/sys/firmware/devicetree/base/soc/ufshc@1d84000`, confirming the host is bound to that DT node — but listing that node is **DENIED** (§8).

`qcom/`: `bus_speed_mode`, `clk_status`, `err_count`, `err_state`, `power_mode` — all `-r--r--r--`, **all values DENIED**.

`devfreq/1d84000.ufshc` exists (a devfreq device is registered for the host; `cur_freq` **DENIED**). This is runtime evidence that the vendor UFS stack scales through devfreq/msm-bus rather than through an `operating-points-v2` OPP table — consistent with ROUND139's reading of the HOS FDT, though the host's own OPP/`interconnects` properties could not be read here (§10, row 3).

### 5.4 UFS descriptor / attribute census (names PASS, values DENIED)

`attributes/` exposes 24 entries including `active_icc_level`, `bkops_status`, `boot_lun_enabled`, `configuration_descriptor_lock`, `current_power_mode`, `exception_event_control/status`, `ffu_status`, `max_data_in_size`, `max_data_out_size`, `max_number_of_rtt`, `ooo_data_enabled`, `psa_data_size`, `psa_state`, `purge_status`, `reference_clock_frequency`. `device_descriptor/`, `geometry_descriptor/`, `health_descriptor/`, `power_descriptor/`, `interconnect_descriptor/`, `string_descriptors/` all enumerate their property files, e.g. `power_descriptor/active_icc_levels_vcc0`.

**Every one of those property values returned `Permission denied` — 142 attribute files enumerated across the six descriptors directories, zero values read** (7 directory headers + `total 0` lines excluded from that count). Directory structure and property inventory are PASS; contents are DENIED.

### 5.5 Block-device attributes and sizes

| Read | Result |
|---|---|
| `/sys/block/sdf/device/{vendor,model,rev,type}` | **DENIED** (4/4) |
| `/sys/block/sdf/size` | **DENIED** |
| `/sys/block/sdf/queue/{logical_block_size,physical_block_size,nr_requests}` | **DENIED** (3/3) |
| `/sys/block/sdf/stat` | **DENIED** |
| `/sys/block/dm-*/size` | **DENIED** |
| `blockdev --getsize64 /dev/block/{sde9,sde13,sde12,sda37,sda40,sdf}` | **DENIED** (6/6) — `blockdev: /dev/block/…: Permission denied` |
| `blockdev --getss /dev/block/sdf` | **DENIED** |
| `/proc/partitions` | **DENIED** — `cat: /proc/partitions: Permission denied` |
| `/proc/mounts` | PASS (full table captured; `erofs` root via `dm-3`, `lz4asm`) |

Consequence: **no block sizes, sector sizes or I/O statistics are exposed to the shell user on this build.** The device's own storage geometry remains UNKNOWN from ADB.

---

## 6. Regulator / PMIC / RPMh / power-domain observations

Each item is classified per the required four-level scale:
**(a)** DT/provider node exists · **(b)** driver probed · **(c)** runtime state reported · **(d)** physical voltage measured.

### 6.1 Regulator class

| Observation | Result |
|---|---|
| `/sys/class/regulator/` entries | **82** (`regulator.0` … `regulator.81`) — PASS |
| `/sys/class/regulator/regulator.N/name` | **DENIED** (every attempt, including `regulator.0`, `.1`, `.32`) |
| `type`, `state`, `status`, `microvolts`, `num_users`, `always_on`, `optname` | **DENIED** (all) |
| Attribute file inventory per regulator | readable — 11 attributes (`max_microvolts`, `microvolts`, `min_microvolts`, `name`, `num_users`, `state`, `type`, `suspend_disk_state`, `suspend_mem_state`, `suspend_standby_state`, `uevent`) plus `of_node`, `device`, `subsystem`, `power/` and any `<consumer>-SUPPLY` links |

Classification: **(a) yes, (b) yes, (c) DENIED, (d) no.**

### 6.2 Regulator → provider mapping recovered from class symlinks

Because `name` is unreadable, the mapping was recovered from the class symlink targets — a legitimate, value-free route:

```
regulator.1  -> ../../devices/platform/soc/18200000.rsc/18200000.rsc:rpmh-regulator-mxlvl/regulator/regulator.1
regulator.10 -> …/18200000.rsc:rpmh-regulator-ldoa1/regulator/regulator.10
regulator.0  -> ../../devices/platform/reg-dummy/regulator/regulator.0
```

Under the single RPMh Resource Controller node `18200000.rsc` there are **51 subdirectory entries**: **47** `rpmh-regulator-*` provider devices, plus the three non-regulator children `msm_bus_apps_rsc`, `qcom,rpmhclk` and `system_pm`, plus the `power/` attribute directory.

The 47 provider devices, verbatim:

`bobc1`, `cxlvl`, `ebilvl`, `gfxlvl`, `lcxlvl`, `lmxlvl`, `ldoa1`, `ldoa2`, `ldoa3`, `ldoa5`, `ldoa6`, `ldoa7`, `ldoa9`, `ldoa10`, `ldoa12`, `ldoa13`, `ldoa14`, `ldoa15`, `ldoa16`, `ldoa17`, `ldoa18`, `ldoc1`…`ldoc11`, `ldof1`, `ldof2`, `ldof3`, `ldof5`, `ldof6`, `ldof7`, `mmcxlvl`, `mxlvl`, `smpa4`, `smpa5`, `smpa6`, `smpc7`, `smpc8`, `smpf1`, `smpf2`.

Composition of the 82 regulator-class entries, recovered from each `of_node` symlink leaf name:

| Category | Count | Examples |
|---|---:|---|
| `reg-dummy` (no DT node) | 1 | `regulator.0` |
| PM8150 VRM rails (`regulator-pm8150-*`) | 27 | `pm8150-l6`, `pm8150-s4`, `pm8150-l17`, `pm8150-l4-level` |
| PM8150A VRM rails (`regulator-pm8150a-*`) | 23 | `pm8150a-s8`, `pm8150a-l11`, `pm8150a-s4-level` |
| GCC / MM / CAM / GPU GDSCs (`qcom,gdsc@*`) | 24 | `qcom,gdsc@177004` (= `ufs_phy_gdsc`), `qcom,gdsc@3d9106c` |
| Peripheral regulators | 7 | `refgen-regulator@88e7000`, `hsphy@88e3000`, `hsphy@88e4000`, `display_gpio_regulator@1`, `regulator-haptics-boost`, `qcom,smb5-vbus`, `qcom,smb5-vconn` |
| **Total** | **82** | |

Of the PM8150/PM8150A entries, **13 are ARC-style level children** (`…-level`, `…-level-ao`, `…-level-so`), e.g. `regulator-pm8150a-s4-level`, `regulator-pm8150a-s3-level`, `regulator-pm8150a-s3-mmcx-sup-level`, `regulator-pm8150-s3-mmcx-sup-level`.

Regulator-class entries per provider (from symlink grouping):

| Provider | # class entries |
|---|---:|
| `rpmh-regulator-mmcxlvl` | 3 |
| `rpmh-regulator-mxlvl` | 3 |
| `rpmh-regulator-cxlvl` | 3 |
| `rpmh-regulator-ldoa5` | 3 |
| `rpmh-regulator-ldoa12` | 3 |
| `rpmh-regulator-bobc1` | 2 |
| all remaining 41 providers | 1 each |

Classification for every provider: **(a) yes, (b) yes** (bound under `/sys/bus/platform/drivers/qcom,rpmh-regulator/`, 47 devices present), **(c) DENIED, (d) no.**

### 6.3 The seven `*lvl` providers — the live counterpart of the HOS ARC model

Seven of the 47 providers carry the `lvl` (level) suffix: **`mmcxlvl`, `mxlvl`, `cxlvl`, `lmxlvl`, `lcxlvl`, `gfxlvl`, `ebilvl`**.

This is the *same seven* groups that ROUND139 counted statically in the HOS FDT as `compatible = "qcom,rpmh-arc-regulator"`, and that ROUND146 built its support-gap analysis on. The live capture adds the runtime half of that claim: **seven `*lvl` platform devices exist and are bound to `qcom,rpmh-regulator` right now, on the running device, with `mmcx`/`mx`/`cx` each exposing three regulator-class entries.**

Boundary of this claim, stated precisely: what is proven at runtime is device **name + driver binding + child-regulator count**. The `compatible` string of those nodes is **not readable** — `…/of_node/compatible` → `Permission denied` — so the identification "these are `qcom,rpmh-arc-regulator` nodes" rests on the ROUND139 static parse plus name correspondence, **not** on a value read this round. Grade: **B (corroborating)**, upgraded from C (static-only), not upgraded to A.

### 6.3.1 The live regulator supply graph — ARC nesting observed at runtime

Each `/sys/class/regulator/regulator.N/` directory carries two usable links: `of_node` → the exact DT node, and `<name>-SUPPLY` → the regulator that `N` depends on. Both are symlinks, so both are readable even though every attribute *value* is denied. 18 `-SUPPLY` links exist across the 81 real regulators, and they reproduce the ARC provider-child nesting that ROUND139 derived statically and ROUND146 built its gap analysis on.

| Consumer (class entry) | DT node (`of_node` leaf) | Supply link |
|---|---|---|
| `regulator.32` | `rpmh-regulator-mmcxlvl/regulator-pm8150a-s4-level` | (no supply link of its own; **11 consumer links point at it**, see below) |
| `regulator.3` | `rpmh-regulator-mxlvl/regulator-pm8150a-s3-mmcx-sup-level` | `regulator.32-SUPPLY` → `rpmh-regulator-mmcxlvl/regulator/regulator.32` |
| `regulator.6` | `rpmh-regulator-cxlvl/regulator-pm8150-s3-mmcx-sup-level` | `regulator.3-SUPPLY` → `rpmh-regulator-mxlvl/regulator/regulator.3` |
| `regulator.1` | `rpmh-regulator-mxlvl/regulator-pm8150a-s3-level` | `regulator.4-SUPPLY` → `rpmh-regulator-cxlvl/regulator/regulator.4` |
| `regulator.4` | `rpmh-regulator-cxlvl/regulator-pm8150-s3-level` | `regulator.62-SUPPLY` → `3d9106c.qcom,gdsc/regulator/regulator.62` |
| `regulator.2` | `rpmh-regulator-mxlvl/regulator-pm8150a-s3-level-ao` | `regulator.33-SUPPLY` → `mmcxlvl/regulator.33`; `regulator.5-SUPPLY` → `cxlvl/regulator.5` |
| `regulator.31` | `rpmh-regulator-…/regulator-pm8150a-s1-level` | `regulator.63-SUPPLY` → `3d9100c.qcom,gdsc/regulator.63` |

Eleven GDSC regulators consume the MMCX level rail `regulator.32` directly (`ad07004`, `ad0a004`, `ad0b004`, `ad08004`, `ad09004`, `ad0c144`, `af03000`, `abf0d18`, `abf0bf8`, `abf0d98`, `abf0c98` — i.e. camera, video, display and GPU GDSCs).

**What this proves directly (A-grade, runtime, no values needed):** on the running stock system, the ARC level regulators are registered as *individual child regulator devices that consume other regulators through the regulator core* — MMCX ⇐ MX-mmcx-sup ⇐ CX-mmcx-sup is a real nested supply chain with resolved `-SUPPLY` links, not merely a set of aliases for GenPD parent pointers. This is exactly the mechanism ROUND146 §3.2 says the pinned ACK regulator core already supports but has no producer for.

**What it does not prove:** the enabled/disabled state, the vote values, or the RPMh corner actually requested (§6.6, §11).

Note a direction-wording discrepancy to reconcile: the live links say the MX `mmcx-sup` child is *supplied by* the MMCX level child (and CX `mmcx-sup` by MX `mmcx-sup`), whereas ROUND139's table row reads as "mmcxlvl … → mxlvl". The nesting itself agrees; only which end is described as parent differs. Recorded as D-9 rather than silently harmonised.

### 6.4 PMIC / SPMI

`/sys/bus/platform/devices/` (PASS) shows the SPMI controller `c440000.qcom,spmi` with per-PMIC children:

- `qcom,pm8150@0`, `qcom,pm8150b@2`, `qcom,pm8150b@3`, `qcom,pm8150l@4`, `qcom,pm8150l@5`, `qcom,pmxprairie@8`, `qcom,pm8009@a`
- per-PMIC sub-devices: `adc_tm@3500`, `clock-controller@5b00`, `pinctrl@c000`, `qcom,power-on@800`, `qcom,revid@100`, `qcom,temp-alarm@2400`, `vadc@3100`, `qpnp-smb5`, `qpnp,fg`, `bcl@…`, `huawei_battery`, `vbus_monitor`, `qcom,amoled`, `qcom,leds@…`, `qcom,pwms@…`

So the four PMICs of interest (PM8150, PM8150B, PM8150L, plus PM8009) are **present and probed**. `/sys/bus/spmi/devices/` listing → **DENIED**.

### 6.5 debugfs and power-domain summaries

| Path | Result |
|---|---|
| `/sys/kernel/debug` | **DENIED** — `ls: /sys/kernel/debug: Permission denied` |
| `/sys/kernel/debug/regulator/regulator_summary` | **DENIED** |
| `/sys/kernel/debug/pm_genpd/pm_genpd_summary` | **DENIED** |
| `/sys/kernel/debug/clk/clk_summary` | **DENIED** |
| `mount` | `tracefs on /sys/kernel/tracing` present; **no debugfs mount line** |

No debugfs was mounted and none was attempted (§ safety). Consequently there is **no genpd summary, no regulator summary and no RPMh vote trace** from this round.

### 6.6 Physical voltage — the four-level boundary

**No physical rail voltage was read, and none can be read this way.** Regulator-class `microvolts` (a software-reported target), PMIC ADC channels (`vadc@3100` exists but its reads are not exposed through ADB shell) and debugfs summaries are all denied. Every one of the six UFS rails (L5, L6, L9, L17, S4, S8) therefore remains **(d) NOT MEASURED**, i.e. the physical input still **UNKNOWN**.

`/sys/class/power_supply/` is readable as a directory (`battery bk_battery bms dc huawei_charge main pc_port usb`) but that is battery/charger telemetry, not PMIC rail voltage, and no rail voltage is claimed from it.

---

## 7. Kernel and system logs

| Attempt | Result |
|---|---|
| `dmesg` | **DENIED** — `dmesg: klogctl: Permission denied` |
| `dmesg \| wc -l` | **DENIED** — same |
| `logcat -b kernel -d -v threadtime` | **EMPTY** (0 bytes) |
| `logcat -g` | `kernel: ring buffer is 256 KiB (0 B consumed, 0 B readable)` |
| `logcat -b main -d -v threadtime` | PASS — 2 865 lines / 344 987 B (raw, local only) |
| `logcat -b system -d -v threadtime` | PASS — 3 202 lines / 366 545 B (raw, local only) |
| `/dev/kmsg` | `crw--w---- 1 root system 1, 11` — not readable by shell; **not opened** (a `cat` on a live kmsg pipe can block) |

`logcat -g` in full:
```
main:   ring buffer is 256 KiB (243 KiB consumed, 243 KiB readable)
system: ring buffer is 256 KiB (253 KiB consumed, 253 KiB readable)
crash:  ring buffer is 256 KiB (15 KiB consumed, 15 KiB readable)
kernel: ring buffer is 256 KiB (0 B consumed, 0 B readable)
```

**The kernel log is structurally unavailable to this session**: `klogctl` is denied and HOS does not forward kernel messages into logd's `kernel` buffer, which is empty. Filtered result over main+system with the mandated keyword set (`ufs|ufshcd|ufs-qcom|rpmh|rpmhpd|regulator|pmic|pm8150|genpd|power domain|mmcx|cx|mx|smmu|iommu|scsi|sdhci|dtbo|bootconfig|memory|reserved-memory|avb|dm-verity|failed|timeout|probe defer`):

```
ufs 0 · rpmh 0 · regulator 0 · pmic 0 · genpd 0 · smmu 0 · iommu 0 · scsi 0
avb 0 · verity 0 · dtbo 0 · memory 0 · storage 0 · charge 126 · timeout 6 · failed 35
```

**Zero matches.** Filter sanity control: the same filter *does* hit (`charge` 126, `failed` 35, `timeout` 6), so the zero result is a property of the data, not of a broken filter. The reason is structural: this boot is 3 d 20 h old, the buffers are 256 KiB rolling, and the kernel never logs into them here. No boot-time kernel message of any kind is recoverable through ordinary ADB on this build.

Only counts and the zero-hit result are uploaded. The 711 kB of raw logcat stays local because it contains notification/app content unrelated to this audit; it is not needed to support any claim above.

---

## 8. Current stock FDT (Step 5)

### 8.1 The binary is root-only

```
ls -l /sys/firmware/fdt
-r-------- 1 root root 800316 2026-11-26 21:46 /sys/firmware/fdt
```

- **Size: 800 316 bytes** (`0x0C362C`). (The `sysfs` mtime shown by `ls` reflects lookup time on this kernel, not a boot timestamp — the same `21:4x`-style timestamp appears on every devicetree attribute, so it carries no meaning here.)
- `cat /sys/firmware/fdt` → **DENIED**, `cat: /sys/firmware/fdt: Permission denied`.
- `dd if=/sys/firmware/fdt of=/dev/null bs=1 count=1` → **DENIED**, `dd: /sys/firmware/fdt: Permission denied`.
- Mode `-r--------`, owner `root`: unreadable by uid 2000 regardless of tool.

**The binary FDT could not be copied. No hash of it can be produced from this session.** No `su`, no alternate path, no permission change was attempted.

### 8.2 What *is* readable: the live DT structure (values denied)

`/sys/firmware/devicetree/base/` — the kernel's live, already-unflattened FDT — is **partially enumerable** by the shell user. Node names, property names and property byte-lengths are readable; property **contents** are denied. This yields structural facts that do not require the binary.

Root: **83 child nodes** + 8 property files (§4.4). Notable children: `chosen`, `firmware`, `memory`, `psci`, `reserved-memory`, `__symbols__`, `aliases`, `cpus`, `soc`.

**`/chosen` — complete property list (all five):**

| Property | Bytes |
|---|---:|
| `bootargs` | 1 507 |
| `kaslr-seed` | 8 |
| `linux,initrd-start` | 8 |
| `linux,initrd-end` | 8 |
| `name` | 7 |

This is the single most consequential negative of the round, and it is a **direct** observation:

> The live `/chosen` of the currently booted HOS4.3 kernel contains **no `linux,uefi-mmap-start`, no `linux,uefi-mmap-size`, no `linux,uefi-mmap-desc-size`, no `linux,uefi-mmap-desc-ver`, no `linux,usable-memory-range`, and no `linux,efi-*` property of any kind.**

The list is exhaustive — it is the directory's full contents, not a filtered view. Therefore, **on this boot, no EFI memory map and no usable-memory-range was handed to Linux through the device tree.** The 1 507-byte `bootargs` is present (value denied), which is consistent with a classic cmdline-style handoff. This directly addresses the ROUND36 Workstream-A question ("does ABL hand the kernel an EFI mmap / usable-memory-range via DT?") for the *live* boot: **no**, not through these `/chosen` properties.

**`/memory`:**

| Property | Bytes | Note |
|---|---:|---|
| `reg` | 48 | 12 cells |
| `device_type` | 7 | value denied |
| `name` | 7 | value denied |
| `ddr_device_type` | 4 | vendor property, one cell |

The stock boot **does** carry a populated `/memory` node — 48 bytes of `reg`, i.e. **12 cells, non-zero**. This contrasts with the candidate build, whose `/memory@80000000` `reg` is 16 bytes under a 2/2 root, i.e. one tuple whose size is zero (ROUND141 §3.1). So "zero-size `/memory`" is a **candidate-only** characteristic; the stock system does not have it.

**`/reserved-memory`: 37 child nodes** (directory count, `grep -c '^d'` = 37), plus 5 property files (`#address-cells` 4, `#size-cells` 4, `name` 16, `phandle` 4, `ranges` 0). The 37 names, verbatim:

`adsp_region`, `bootfail_mem@b0400000`, `cdsp_region`, `cdsp_secure_heap@8bf00000`, `cnss_wlan_region`, `cont_splash_region@9c000000`, `dfps_data_region@9e300000`, `disp_rdump_region@9c000000`, `hyp_region@80000000`, `kerneldump`, `linux,cma`, `mailbox_region`, `mem_dump_region`, `pil_adsp_region@8a100000`, `pil_camera_region@86200000`, `pil_cdsp_region@87800000`, `pil_cvp_region@87300000`, `pil_gpu_region@8681a000`, `pil_ipa_fw_region@86800000`, `pil_ipa_gsi_region@86810000`, `pil_npu_region@86900000`, `pil_slpi_region@88c00000`, `pil_spss_region@8be00000`, `pil_video_region@86e00000`, `pil_wlan_fw_region@86700000`, `qseecom_region`, `qseecom_ta_region`, `rainbow_mem@b0000000`, `removed_region@80b00000`, `res_xbl_uefi_log_region@80880000`, `reserved-memory@80860000`, `sdsp_region`, `secure_display_region`, `smem_region@80900000`, `sp_region`, `user_contig_region`, `xbl_aop_region@80700000`.

Per-node property-name sets were captured for all 37 (e.g. `hyp_region@80000000` → `name`(11), `no-map`(0), `phandle`(4), `reg`(16); `linux,cma` → `alignment`(8), `alloc-ranges`(16), `compatible`(16), `linux,cma-default`(0), `name`(10), `reusable`(0), `size`(8)). **All values denied**, so ranges, `no-map`/`reusable` semantics and phandle targets cannot be resolved — but the *shape* (which nodes exist, which carry `reusable`/`no-map`/`alloc-ranges`/`size`) is now live evidence rather than a static parse.

Other DT paths:

| Path | Result |
|---|---|
| `/sys/firmware/devicetree/base/soc/` | **DENIED** (listing) |
| `/sys/firmware/devicetree/base/cpus/` | **DENIED** |
| `/sys/firmware/devicetree/base/firmware/android/` | **DENIED** |
| `/sys/firmware/devicetree/base/reserved-memory/kerneldump/` | **DENIED** |
| `/sys/firmware/devicetree/base/__symbols__/` | PASS — **1 754** entries |
| `/sys/firmware/devicetree/base/psci/` | PASS — `method`, `compatible`, `name` etc. (values denied) |

So SELinux allows the DT **root** and `reserved-memory` subtree but denies `soc/`, `cpus/` and `firmware/android/`. That asymmetry is why the UFS node's own properties (which live under `soc/`) could not be enumerated at all.

### 8.3 Label

Everything in §8.2 is the **current stock HOS4.3 boot's** DT — not the candidate ACK DTB, and not necessarily any future boot's DT. It is the FDT the running kernel received and unflattened.

---

## 9. Partition metadata (metadata only)

`/dev/block/by-name/` is readable as a symlink farm: **86 entries**. `ls -l` gives name → target; **no sizes are exposed** (`/proc/partitions` DENIED, `blockdev` DENIED, `/sys/block/*/size` DENIED).

| Partition | Target | Partition | Target |
|---|---|---|---|
| `abl` | `/dev/block/sde6` | `xbl` | `/dev/block/sdb1` |
| `aop` | `sde1` | `xbl_config` | `sdb2` |
| `boot` | `sde9` | `modem` | `sde4` |
| `dtbo` | `sde13` | `dsp` | `sde7` |
| `vbmeta` | `sde12` | `bluetooth` | `sde5` |
| `super` | `sda37` | `keymaster` | `sde8` |
| `userdata` | `sda40` | `devcfg` | `sde10` |
| `metadata` | `sda32` | `featenabler` | `sde15` |
| `misc` | `sda4` | `qupfw` | `sde11` |
| `persist` | `sda2` | `uefisecapp` | `sde14` |
| `cache` | `sda10` | `uefivarstore` | `sde22` |
| `recovery` | `sda19` | `secdata` | `sde23` |
| `recovery_ramdisk` | `sda20` | `storsec` | `sde21` |
| `recovery_vendor` | `sda21` | `apdp` | `sde18` |
| `recovery_vbmeta` | `sda24` | `limits` | `sde19` |
| `erecovery` | `sda16` | `rawdump` | `sde20` |
| `erecovery_ramdisk` | `sda17` | `dfx` | `sde24` |
| `erecovery_vendor` | `sda18` | `dip` | `sde17` |
| `erecovery_vbmeta` | `sda23` | `devinfo` | `sde16` |
| `vbmeta_system` | `sda25` | `modemst1` | `sdf2` |
| `vbmeta_vendor` | `sda26` | `modemst2` | `sdf3` |
| `vbmeta_odm` | `sda27` | `fsg` | `sdf4` |
| `vbmeta_cust` | `sda28` | `fsc` | `sdf5` |
| `vbmeta_hw_product` | `sda29` | `ALIGN_TO_128K_1` | `sdd1` |
| `system` | `dm-3` | `ALIGN_TO_128K_2` | `sdf1` |
| `vendor` | `dm-4` | `cdt` | `sdd2` |
| `cust` | `dm-0` | `ddr` | `sdd3` |
| `hw_product` | `dm-1` | `reserved4` | `sdc1` |
| `odm` | `dm-2` | `ssd` | `sda1` |

Simplified **8 `vbmeta`-semantic partitions** are visible: `vbmeta` (sde12), `vbmeta_system` (sda25), `vbmeta_vendor` (sda26), `vbmeta_odm` (sda27), `vbmeta_cust` (sda28), `vbmeta_hw_product` (sda29), plus the recovery-side `recovery_vbmeta` (sda24) and `erecovery_vbmeta` (sda23). ROUND140 §D-2 counted 6 standalone vbmeta images inside the vendor FDT's boot region; the *partition table* carries 8 vbmeta-named partitions. These are different artefacts (boot-image header blocks vs. partition names) and the two numbers are not expected to match — recorded so the discrepancy is not inherited as a contradiction.

Slot / AVB state: `ro.boot.slot_suffix` **empty**, `ro.boot.slot` **empty**, `ro.boot.dynamic_partitions=true`, `ro.boot.verifiedbootstate=orange`, `ro.boot.flash.locked=0`, `ro.crypto.state=encrypted`, `ro.boot.fstab_suffix=default`. A-only layout; no `_a`/`_b` suffixing.

**No partition data was read, no hash of any partition was computed, and no restore was attempted.** The existence of `recovery`/`erecovery` partitions is **not** any claim that a recovery route works.

Storage identity cross-check: the by-name targets `sda…sdf` match the six UFS LUNs, and `sdf` is the LUN-5 device whose sysfs path resolves through `1d84000.ufshc` (§5.1). `fsc`/`fsg`/`modemst1/2` sit on `sdf`, consistent with a dedicated firmware LUN.

---

## 10. Correlation against ROUND139 / ROUND141 / ROUND143 / ROUND146 and the candidate UFS mapping

| # | Prior claim | Source | Live ROUND149 observation | Verdict |
|---|---|---|---|---|
| 1 | HOS FDT has **47** `rpmh-regulator-*` provider groups | ROUND139 §(census) | `18200000.rsc` has **47** bound `rpmh-regulator-*` platform devices | **CONFIRMED at runtime** (exact count match, independent method) |
| 2 | **7** groups use `compatible = "qcom,rpmh-arc-regulator"`: `mmcxlvl`, `mxlvl`, `cxlvl`, `lmx.lvl`, `lcx.lvl`, `gfx.lvl`, `ebi.lvl` | ROUND139, ROUND146 §1 | 7 `*lvl` devices present and bound to `qcom,rpmh-regulator`; `mmcx`/`mx`/`cx` each expose 3 regulator entries | **CONFIRMED for presence/binding**; `compatible` string unreadable → grade B, not A |
| 3 | HOS UFS node has no `power-domains`, no `operating-points-v2`, legacy `qcom,msm-bus` only | ROUND139 E7 | `devfreq/1d84000.ufshc` exists; `qcom/bus_speed_mode` attribute present; UFS node properties unreadable (`soc/` denied) | **CONSISTENT, not independently read** — C grade; the devfreq device is direct evidence of a devfreq/msm-bus scaling path |
| 4 | Six UFS rails resolve to L5/L6/L9/L17/S4 + PM8150L S8; physical input parents UNKNOWN | ROUND139 §B, ROUND141 gate 4 | All six provider devices exist live (`ldoa5`, `ldoa6`, `ldoa9`, `ldoa17`, `smpa4`, `smpc8`); **no rail voltage readable**, no `vin`-style parent readable | **UNCHANGED — physical input still UNKNOWN** |
| 5 | `qcom,vccq-parent-supply` → S8 is inert in the candidate; no ACK consumer | ROUND140/ROUND142 | HOS-side S8 (`smpc8`) exists and is probed; its consumer set is **not readable** on HOS | **UNKNOWN for HOS**; candidate finding stands |
| 6 | Candidate `/memory` `reg` size is zero and ACK skips zero-size tuples | ROUND141 §3.1 | Stock `/memory.reg` = **48 B / 12 cells, non-zero** | **Candidate-only defect confirmed as such** — the stock boot has a real memory node |
| 7 | Final post-ABL FDT / EFI handoff unresolved; reserved-memory 37 (vendor) vs 18 (candidate) | ROUND36 A/B, ROUND141 gates 7–8 | Live `/chosen` has **no** `linux,uefi-*` and **no** `linux,usable-memory-range`; live reserved-memory = **37** children | **Gate narrowed**: 37 confirmed live; no EFI-mmap/usable-range handoff through DT on this boot; FDT **values** still unreadable |
| 8 | MMCX→MX→CX ARC equivalence vs candidate GenPD unproven | ROUND145/ROUND146, ROUND141 gate 6 | 7 `*lvl` devices live; **`-SUPPLY` symlinks show MMCX ⇐ MX-mmcx-sup ⇐ CX-mmcx-sup as a real nested chain**, and 11 GDSCs consume the MMCX level rail; **no CMD-DB/RPMh vote values** (debugfs denied) | **PARTIALLY DEMONSTRATED**: the nested ARC *structure* is now runtime evidence (was static-only); vote **values** and GenPD equivalence remain **BLOCKED** |
| 9 | AVB trusted chain / footer provenance unproven | ROUND139 D, ROUND141 gate 11 | 8 vbmeta-named partitions visible; `verifiedbootstate=orange`, `flash.locked=0`; contents not read | **Structure only** — no verification claim |
| 10 | HOS 4.3 boot identity / DTBO selection | ROUND139, ROUND141 gate 10 | `ro.boot.dtbo_idx = 2` (single index reported, not a list); A-only slot layout | **NEW datum**: the running system reports dtbo index 2 |
| 11 | ROUND143 report | cited in ROUND149 taskbook | **NOT FOUND** — 0 paths matching `round143` on `main`, `firmware-audit-v1`, `ai1/round130-…`, `ai2/round141-…` | **Cannot correlate** — the artefact was not located; not silently skipped |

### 10.1 Candidate UFS mapping vs live HOS provider reality

| Candidate property (ROUND140/142) | Candidate provider | Live HOS regulator (class entry → provider device → DT node) | Present? |
|---|---|---|---|
| `vcc-supply` | `pm8150_l17` | `regulator.29` → `rpmh-regulator-ldoa17` → `rpmh-regulator-ldoa17/regulator-pm8150-l17` | **yes** |
| `vccq-supply` | `pm8150_l6` | `regulator.17` → `rpmh-regulator-ldoa6` → `…/ldoa6/regulator-pm8150-l6` | **yes** |
| `vccq2-supply` | `pm8150_s4` | `regulator.7` → `rpmh-regulator-smpa4` → `…/smpa4/regulator-pm8150-s4` | **yes** |
| `qcom,vddp-ref-clk-supply` | `pm8150_l6` | same node as `vccq` (`regulator.17`) | **yes** |
| `qcom,vccq-parent-supply` | `pm8150l_s8` | `regulator.37` → `rpmh-regulator-smpc8` → **`…/smpc8/regulator-pm8150a-s8`** | **yes** |
| `vdda-phy` | `pm8150_l5` | `regulator.14` → `rpmh-regulator-ldoa5` → `…/ldoa5/regulator-pm8150-l5` | **yes** |
| `vdda-pll` | `pm8150_l9` | `regulator.19` → `rpmh-regulator-ldoa9` → `…/ldoa9/regulator-pm8150-l9` | **yes** |
| `vdd-hba` (deliberately absent) | — GDSC via `power-domains` | `regulator.55` → `177004.qcom,gdsc` → `soc/qcom,gdsc@177004` (`ufs_phy_gdsc`) | **yes** |

Every rail the candidate binds to exists as a probed provider on the live device, and the `ufs_phy_gdsc` the candidate uses for `vdd-hba` sits at the identical address (`177004`). **That establishes rail and GDSC availability, not wiring equivalence**: which consumer HOS attaches to each rail, and in what order, is not readable on this build.

One naming point reconciled: the candidate's `qcom,vccq-parent-supply` target is labelled `pm8150l_s8` in the board file (PM8150L S8), while ROUND139 recorded the HOS name as `pm8150a_s8`. Both are correct about different strings — live, the node is named **`regulator-pm8150a-s8` but sits inside the `smpc8` provider**, i.e. PM8150L's S8 resource carrying a `pm8150a-` node name. This is not a contradiction between sources; it is vendor naming.

---

## 11. Remaining unknowns and the smallest next evidence action

| # | Unknown | Smallest next action |
|---|---|---|
| U-1 | Values of the live `/chosen` (`bootargs` 1 507 B), `/memory/reg` (12 cells), all 37 `reserved-memory` ranges | **Needs `root` or a debug/shell-privileged build.** On a stock HOS4.3 user build with SELinux enforcing and uid 2000, `/sys/firmware/fdt` is unreadable by construction. Options: (a) user-authorized `adb root` on a debuggable/userdebug build only; (b) capture the same FDT from an authorised boot-time hook; (c) accept static offline evidence. |
| U-2 | Whether `/memory` 12-cell `reg` maps to a >4 GiB layout (see D-2) | Same as U-1 — a single `hexdump -C` of `/sys/firmware/fdt` would settle it in one shot. |
| U-3 | HOS UFS node's actual `power-domains` / OPP / `interconnects` / supply declarations | `soc/` subtree is DENIED to shell; requires U-1 access. |
| U-4 | Whether the 7 `*lvl` nodes really carry `compatible = "qcom,rpmh-arc-regulator"` | Requires reading `…/of_node/compatible` → same access problem. The *nested supply behaviour* is already demonstrated (§6.3.1); only the compatible string remains unread. |
| U-5 | Runtime MMCX/MX/CX votes and RPMh corner state | `debugfs` unavailable without mount + root; not authorized this round. |
| U-6 | UFS vendor/model/geometry and block sizes | `/sys/block/sdf/*` DENIED; no unprivileged route found. |
| U-7 | Partition sizes and a real backup/recovery route | Not obtainable read-only; needs a separately authorized backup plan (not this round). |
| U-8 | Physical input parents of L5/L6/L9/L17/S4/S8 | Still requires the PMIC power-tree schematic/netlist or a measured board — ADB cannot answer this at any privilege level. |

The single highest-yield action is U-1/U-2: **one privileged read of `/sys/firmware/fdt` (800 316 B)** would simultaneously resolve the bootargs, the memory map, all 37 reservation ranges, and (via the `soc/` subtree) the UFS node declarations. It requires either `adb root` on a privileged build or an explicitly authorised root shell — neither of which this round authorized.

---

## 12. Safety declaration

| Prohibition | Status |
|---|---|
| Reboot / power cycle / bootloader / recovery / fastboot | **NOT DONE** — no such command was issued |
| `adb root`, `su`, any privilege escalation | **NOT DONE** — uid stayed 2000 throughout |
| Permission / SELinux / remount changes | **NOT DONE** |
| debugfs mount or attempt to mount | **NOT DONE** |
| Writes to sysfs, procfs, properties, settings, partitions, block devices, files | **NOT DONE** — every command was a read; the only `dd` invocation wrote to `/dev/null` on the host side and was denied |
| `adb push`, package install/uninstall, `pm`/`setprop`/`settings put` | **NOT DONE** |
| Raw partition / block-device content reads | **NOT DONE** — `/dev/block/*` was never opened; `blockdev --getsize64` (a size ioctl, no data transfer) was attempted and denied (D-5) |
| Flashing / unlocking / AVB change / boot image build / temporary boot / candidate kernel boot | **NOT DONE** |
| Stress test / benchmark / suspend-resume / deliberate UFS load | **NOT DONE** |
| Retry of a denied read via root or another account | **NOT DONE** — denials were recorded and left alone |
| Tool/dependency download or install | **NOT DONE** on host or device |
| Inspect another Agent's private workspace | **NOT DONE** — only the public report repo was read (§D-7) |

The tablet's state is unchanged: no reboot occurred (uptime still 3 d 20 h at capture), no write of any kind was performed.

**This round does not authorize a candidate-kernel boot and does not close any first-boot gate by itself.** Gates 4, 6, 8, 9, 10, 11, 12 and 13 in the ROUND141 matrix remain as they were; gate 7 and gate 8 are *narrowed* (§10 rows 6–7) but not closed.

---

## 13. Local evidence retention and hashes

270 raw evidence files (252 command outputs + 16 per-batch status indexes + 2 filtered log files) = 1.4 MB, retained locally under `r149/evidence/raw/`, with a full SHA-256 manifest at `r149/evidence/MANIFEST.sha256` (**270 lines**, sha256 of the manifest file itself: `30aae0cd78a6f9afa09324c4d779e14c65d10f5b8693f99cad76c4c034c17afc`).

Key artefacts (first 16 hex of SHA-256, full values in the manifest):

| File | Bytes | SHA-256 (prefix) | Content |
|---|---:|---|---|
| `step1/19.txt` | 1 173 | `074b40b606fb9d52` | full `ro.boot.*` property dump (serial inside → **not uploaded**) |
| `step2/s2_04.txt` | 5 499 | `ed3b003d35bf8342` | `/sys/block` listing showing `sdf -> …ufshc…0:0:0:5` |
| `step3b/s3b_04.txt` | 3 923 | `a1cb71447ca15dd6` | 47 `rpmh-regulator-*` platform devices + SPMI/PMIC children |
| `step3c/s3c_02.txt` | 9 941 | `1aca801703ed426e` | regulator class → provider symlink mapping (82 entries) |
| `step3c/s3c_09.txt` | 2 | `031b4af5197ec30a` | `18200000.rsc` child count = 51 |
| `step3b/s3b_15.txt` | 2 654 | `a0a898431dab0c13` | live `/sys/firmware/devicetree/base/reserved-memory/` listing |
| `step5/s5_02.txt` | 293 | `7e303ad808b7a6b7` | live `/chosen` property list (5 properties) |
| `step5b/s5b_01.txt` | 216 | `299c2a58d46c0bcd` | live `/memory` property list (`reg` = 48 B) |
| `step5/s5_16.txt` | 459 | `34433f133ad9b711` | live DT root properties with byte lengths |
| `step4/s4_06.txt` | 434 | `e9c2abd9eaa37a05` | `logcat -g` showing kernel buffer 0 B |
| `step6b/s6b_09.txt` | 64 | `738d54c6cf56c0c9` | `-r-------- 1 root root 800316 /sys/firmware/fdt` |
| `step6/s6_01.txt` | 6 091 | `e9803853b1716815` | 86 `by-name` symlink targets |
| `step7/s7_02.txt` | 139 | (see manifest) | `/proc/meminfo` MemTotal 11 984 584 kB |
| `step9/s9_01.txt` + `s9_02.txt` | 9 435 + 6 136 | (see manifest) | `of_node` + `-SUPPLY` link for all 82 regulators (the ARC nesting evidence) |
| `step10/s10_01.txt` | 1 863 | (see manifest) | the six UFS rails: class entry → provider device → DT node |
| `index-step*.tsv` (16 files) | — | see manifest | exact command text, exit code, bytes, status per command |

Redaction performed before upload: the device serial (replaced by `W3VB…4537` + SHA-256 of the full string), `ro.boot.serialno`, and the entire raw `logcat` main/system buffers (retained locally only; only zero-hit counts uploaded). No account identifiers, message content, Wi-Fi or location data appear in this report.

---

## 14. Discrepancies and process deviations (self-reported)

| ID | Item | Detail |
|---|---|---|
| D-1 | **Deliverable path collides with the taskbook** | The branch already held `firmware-analysis/round149/WORKBUDDY_ROUND149_ADB_RUNTIME_READONLY_AUDIT.md` as the **taskbook** (12 005 B, blob `63ca25463d`). §7 of that taskbook names the *same* path for the report, so writing the report here necessarily replaces the taskbook. The taskbook blob remains recoverable from branch history. **One of the two filenames should be changed** so this does not recur every round. |
| D-2 | **Root cell size vs memory map arithmetic** | Live root `#address-cells` and `#size-cells` are 4 B each (one cell each), while `/memory.reg` is 48 B (12 cells) and `MemTotal` is 11 984 584 kB (≈11.4 GiB, i.e. RAM above 4 GiB). Under standard OF rules a 1/1 root cannot express addresses above 4 GiB, so either the root cell declaration or the tuple grouping is not what it appears. **Not resolvable without reading the FDT values**; recorded rather than guessed. |
| D-3 | First capture contains the ADB daemon banner | The first `adb` invocation of the session emitted `* daemon not running; starting now…` / `* daemon started successfully` ahead of the actual value in `step1/01.txt` (84 B: two banner lines + `DBY-W09`). Re-running did not remove it because the daemon exits between host shell invocations on this host; the file is left as-is rather than hand-edited, and later batches call `adb start-server` before the first command so only this one file is affected. Read the value from line 3. |
| D-4 | Two commands malformed by host-side quoting | PowerShell strips embedded double quotes when invoking native executables, so `step3/s3_09` and `step3/s3_10` reached the device as unquoted pipelines and failed (`sh: pmic: inaccessible or not found`). Both were re-run with single quotes as `step3b/s3b_04`/`s3b_05` and succeeded. Same cause made `step3b/s3b_01` return empty; superseded by `step3c/s3c_02`. |
| D-5 | `blockdev --getsize64` is arguably beyond "metadata only" | Size ioctls transfer no data, and the taskbook allows "reported sizes", but a strict reading of §"Explicitly forbidden" (no reads of block devices) makes even this borderline. It was denied by SELinux on all six partitions, so no data was obtained. Disclosed rather than omitted. |
| D-6 | `dd … of=/dev/null` used as an access probe | Step 5 explicitly authorises copying `/sys/firmware/fdt`; `dd` was used only to test readability with a 1-byte read into `/dev/null`. Denied. No data left the device and nothing was written to it. |
| D-7 | Network reads beyond the device | Fetching the ROUND139 / ROUND141 / ROUND146 reference reports and the branch file manifest required HTTPS requests to the report repository. The taskbook's "no network fetches or downloads" is read as referring to tools/dependencies; disclosed here so the reference reading is not invisible. |
| D-8 | `sda`…`sde` symlinks unreadable | `/sys/block/sda..sde` appear as `l?????????` — the symlink metadata is not stat-able by uid 2000, so only `sdf` (LUN 5) could be traced by path. Their LUN identity is inferred from `by-name` targets (§9), which is a **weaker** grade of evidence and is labelled as such. |
| D-9 | ARC supply-edge **direction** wording differs between ROUND139 and the live graph | ROUND139's table records the mmcxlvl-side property (`pm8150a_s4_level-parent-supply`) as the edge and describes it as "mmcxlvl → mxlvl". The live `-SUPPLY` symlinks say the opposite direction: `regulator.3` (mxlvl/`pm8150a-s3-mmcx-sup-level`) is *supplied by* `regulator.32` (mmcxlvl/`pm8150a-s4-level`), and `regulator.6` (cxlvl/`pm8150-s3-mmcx-sup-level`) is supplied by `regulator.3`. The three-node nesting agrees; the "which end is the parent" wording does not. Not harmonised here — flagged for one reconciliation pass against the raw HOS DT text. |
| D-10 | `step8`/`step9` aggregation quirks | The first supply-link sweep (`s8_01`) printed only the per-regulator headers — its inline `sed`/`grep` combination produced no rows; re-done as explicit index loops (`s9_01`, `s9_02`) which succeeded (9 435 B / 6 136 B). `s8_01` is retained as a failed attempt rather than deleted. |
