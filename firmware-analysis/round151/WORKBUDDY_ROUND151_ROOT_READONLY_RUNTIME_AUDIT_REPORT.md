# ROUND151 — Root capability check and privileged read-only runtime capture

- **Executor:** WorkBuddy Agent (local Agent 1), branch `workbuddy/round151-root-readonly-runtime-audit`.
- **Device:** Huawei MatePad 11 (2021) DBY-W09 / HWDBY / KONA / SM8250, serial `<SERIAL-REDACTED>` (redacted in public text as `<SERIAL>`).
- **Stock system:** HOS 4.3.0.196(C00E100), Android 12 / API 31, kernel `4.19.157-perf+ #1 SMP PREEMPT Fri Aug 30 08:34:06 CST 2024`.
- **Candidate (unchanged, not touched):** ACK `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`; candidate tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
- **Outcome:** **`ROOT_READONLY_CAPTURE_COMPLETE`** — root was available, and every item the taskbook §3 asked for was read. Nothing on the device was written, mounted, re-mounted, rebooted or flashed.

---

## 0. Results at a glance

| # | Question | Answer | Grade |
|---:|---|---|---|
| 1 | Is a usable `su` present, and does it yield `uid=0`? | **Yes.** `su -c id` → `uid=0(root) gid=0(root) groups=0(root) context=u:r:ksu:s0`. Reserved as the only privilege-gate invocation. | A (direct read) |
| 2 | Was the live FDT readable? | **Yes.** `/sys/firmware/fdt`, 800 316 B, `-r-------- root root`, captured byte-exact, SHA-256 `fefeaa04…46b700`. | A |
| 3 | Root cell values | `#address-cells = 2`, `#size-cells = 2`; `model = "Huawei Technologies, Inc. DBY-W09"`; `compatible = "qcom,kona-qrd","qcom,kona","qcom,qrd"`. | A (decoded FDT) |
| 4 | EFI / UEFI handoff through `/chosen` | **Still absent.** `/chosen` holds exactly four DT properties; none is `linux,uefi-*`, `linux,efi-*` or `linux,usable-memory-range`. ROUND149's conclusion now has a values-level proof. | A |
| 5 | `/memory` physical map | **Three** regions, 12 cells total, 921 + 8192 + 3072 MiB; corroborated line-by-line by `/proc/iomem`. ROUND149 D-2 is closed. | A + B |
| 6 | `/reserved-memory` | **37** children, 23 with a non-zero `reg` totalling 232.7 MiB, one intentional 8 MiB overlap (rdump inside splash). | A |
| 7 | Six UFS rails | All six resolve in the **live merged** FDT: L17, L6, S4, L8-parent S8 on `ufshc`; L5, L9 on `ufsphy`. All six are `state=enabled` with non-zero users right now. | A |
| 8 | `vdd-hba` → `ufs_phy_gdsc` | Bound but **never enabled**: `state=disabled`, `num_users=0`, `regulator_summary` use-count 0, while UFS is active. New A-grade runtime fact. | A |
| 9 | Seven ARC level providers | **7 present** in the live FDT and **7 bound** at runtime; the five provider-child parent edges match ROUND139 exactly, phandle-by-phandle on a different blob. | A |
| 10 | ARC nesting direction (ROUND149 D-9) | **Resolved against ROUND149's wording.** `regulator_summary` nesting and FDT phandles both say MMCX ⇐ MX-mmcx-sup ⇐ CX-mmcx-sup, i.e. MMCX *consumes* MX-mmcx-sup. | A |
| 11 | Kernel log | dmesg readable **as root** (994 476 B / 7 579 lines) but covers only the last **234 s** of a 198 308 s uptime — zero boot-time UFS/RPMh/regulator lines survive. logd `kernel` buffer is empty. | A (negative) |
| 12 | Device modified? | **No** by this agent. See §10.1 for the one user-side change (USB debugging re-enabled). | — |

---

## 1. Identity and the root decision gate

### 1.1 Preflight (taskbook §2.1–2.3)

| Property | Value |
|---|---|
| `adb devices -l` | exactly one entry: `<SERIAL-REDACTED>  device product:DBY-W09 model:DBY_W09 device:HWDBY` |
| `ro.product.model` | `DBY-W09` |
| `ro.product.device` | `HWDBY` |
| `ro.board.platform` | `kona` |
| `ro.soc.model` | `SM8250` |
| `ro.build.fingerprint` | `HUAWEI/DBY-W09/HWDBY:12/HUAWEIDBY-W09/104.3.0.196C00:user/release-keys` |
| `ro.build.version.release` / `sdk` | `12` / `31` |
| `adb shell id` | `uid=2000(shell) … context=u:r:shell:s0` |
| `getenforce` | `Enforcing` |

Every value matches the ROUND149 preflight, so the device is the same unit in the same build state.

### 1.2 Root gate (taskbook §2.4–2.7)

```
adb exec-out su -c id
→ uid=0(root) gid=0(root) groups=0(root) context=u:r:ksu:s0
```

- `which su` → `/system/bin/su`; manager artifacts `/data/adb/ksu`, `/data/adb/modules` exist; the SELinux domain `u:r:ksu:s0` identifies the manager family as **KernelSU**.
- **No interactive prompt appeared** in this session. The grant was already in effect for `shell` under the existing manager configuration; nothing was clicked, pre-approved, set to permanent, or automated by this agent.
- The check was executed **exactly once** and succeeded on the first invocation, so no re-run was needed.
- All subsequent reads used `adb exec-out su -c '<cmd>'`. `adb root` was never used and SELinux was never touched.

### 1.3 Explicitly not done

No `adb root`; no SELinux change; no mount/unmount (debugfs was already mounted by the system — see §6.1); no write to any sysfs, procfs, devfreq, attribute, property or block device; no `reboot`, `fastboot`, `recovery`, `flash`, `boot`, `slot`; no partition content read (`dd`/`cat`/`hexdump`/`adb pull` of `/dev/block/*`); no FFU, BKOPS, purge, power-mode or gear command; no benchmark, fsck or stress; no source/DTS/DTBO/config/patch/build-output modification; no network download or tool installation.

---

## 2. Command inventory and evidence handling

| Metric | Value |
|---|---:|
| Commands executed (index rows) | **77** |
| PASS | 73 |
| NOT FOUND | 3 (`/proc/bootconfig`, `/sys/devices/platform/18200000.rsc{,/power/runtime_status}` — wrong prefix, corrected in 417–420) |
| EMPTY | 1 (`logcat -b kernel -d`) |
| DENIED | **0** (contrast: ROUND149 recorded 69 DENIED as uid 2000) |
| Local evidence files under manifest | 152 |
| Manifest | `evidence/meta/MANIFEST.sha256`, 152 lines, file SHA-256 `d1d353cb07cf70ee9df1ea06bee481b26cf7d346dad5bd0e1c9f73a6188284b0` |
| Command table | `evidence/meta/index.tsv` — key, exit code, status, stdout bytes, stderr bytes, sha256 prefix, exact command text |

Evidence workspace: `r151-root-readonly/` with `evidence/raw/` (per-command stdout+stderr), `evidence/private/` (raw FDT, full decode, rail extract), `evidence/meta/` (index, manifest, gate record). ROUND149's raw evidence was not reused or modified.

**Zero DENIED is itself a result**: every value ROUND149 could not read because of uid 2000 / SELinux is readable under this root, which is why §3–§5 can report values rather than structure.

---

## 3. Live FDT capture and decode

### 3.1 Binary integrity (taskbook §3.1)

Captured through a byte pipe (`adb exec-out` from a Python subprocess), never through text redirection.

| Item | Value |
|---|---|
| Source | `/sys/firmware/fdt`, `-r-------- 1 root root 800316` |
| Captured bytes | **800 316** |
| SHA-256 (local file) | `fefeaa049f64a9cc79f0aa7558883f7a31ba98cf0ad73f541834c0ec2d46b700` |
| SHA-256 (device-side `sha256sum /sys/firmware/fdt`) | `fefeaa049f64a9cc79f0aa7558883f7a31ba98cf0ad73f541834c0ec2d46b700` |
| Magic | `0xd00dfeed` ✔ |
| `totalsize` | 800 316 ✔ equals captured length |
| `version` / `last_comp_version` | 17 / 16 |
| `off_dt_struct` / `size_dt_struct` | 56 / 728 212 |
| `off_dt_strings` / `size_dt_strings` | 728 268 / 72 048 |
| `boot_cpuid_phys` | 0 |
| Struct block census | 4 566 BEGIN_NODE, 4 566 END_NODE, 23 912 PROP, 131 NOP |
| Nodes / phandles | 4 566 / 2 039 |
| Hand-edited? | No. Not uploaded to GitHub. |

The device-side `sha256sum` was taken from the same in-kernel blob, so the equality is an end-to-end integrity proof of the transport, not just a local recomputation.

### 3.2 Decode tooling

No `dtc`, `fdtdump` or `fdtget` exists on this host and none was installed or downloaded. Decoding used the **already-installed local parser written in ROUND147** (`r147/fdt_inv.py`, pure-Python struct-block walker) plus a ROUND151 analysis layer that resolves phandles by property class. Every number below is read from the binary; nothing is inferred from text.

One display defect found and fixed before any value was reported: a 4-byte cell such as `<0x77>` was initially rendered as the string `"w"`. The string detector now requires the first byte to be printable and the table to be NUL-terminated, so `phys` and `pinctrl-*` resolve as phandles. This is the same class of error as the ROUND140 `vddp-ref-clk-max-microamp` false ABSENT; recorded so later rounds do not inherit it.

### 3.3 Root node

| Property | Value |
|---|---|
| `#address-cells` | 2 |
| `#size-cells` | 2 |
| `compatible` | `qcom,kona-qrd`, `qcom,kona`, `qcom,qrd` |
| `model` | `Huawei Technologies, Inc. DBY-W09` |
| `qcom,board-id` | `<0x200e 0x0>` |
| `qcom,msm-id` | `<0x164 0x20001>` |
| `interrupt-parent` | `<0x1>` |
| child nodes | 83 |

`qcom,board-id` / `qcom,msm-id` carry no serialised device-unique identifier, so they are reported as-is.

### 3.4 `/chosen` — complete content

| Property | Bytes | Value |
|---|---:|---|
| `bootargs` | 1 507 (incl. NUL) | 1 506 characters, 62 tokens (sanitised excerpt below) |
| `kaslr-seed` | 8 | `<0x0 0x0>` — zeroed |
| `linux,initrd-start` | 8 | `0x00000000f0000000` |
| `linux,initrd-end` | 8 | `0x00000000f015749a` (initrd window 1 406 106 B ≈ 1.34 MiB) |

That is the **entire** property set. There is **no** `linux,uefi-mmap-start`, `linux,uefi-mmap-size`, `linux,uefi-mmap-desc-size`, `linux,uefi-mmap-desc-ver`, `linux,usable-memory-range`, `linux,efi-*` or any other vendor handoff property. Combined with the zeroed `kaslr-seed` and `nokaslr` in `bootargs`, the live boot is a plain cmdline-style handoff.

**Reconciliation with ROUND149.** ROUND149 reported "all five" entries for `/chosen`. The sysfs view `/proc/device-tree/chosen` contains the same four properties plus the kernel-synthesised `name` file (7 bytes, value `chosen`). There is no disagreement: **4 DT properties + 1 synthetic `name` = the 5 directory entries ROUND149 counted.**

Sanitised `bootargs` (serials, panel serial, `HIMNTN`, `oba_version` redacted; the rest verbatim):

```
cgroup_disable=pressure rcupdate.rcu_expedited=1 rcu_nocbs=0-7 kpti=off
earlycon=msm_geni_serial,0xa90000 androidboot.hardware=qcom androidboot.console=ttyMSM0
androidboot.memcg=1 lpm_levels.sleep_disabled=1 video=vfb:640x400,bpp=32,memsize=3072000
msm_rtb.filter=0x237 service_locator.enable=1 androidboot.usbcontroller=a600000.dwc3
swiotlb=2048 loop.max_part=7 cgroup.memory=nokmem,nosocket reboot=panic_warm
androidboot.selinux=enforce unmovable_isolate1=2:256M,3:312M,4:348M buildvariant=user
nokaslr androidboot.verifiedbootstate=orange androidboot.keymaster=1
androidboot.bootdevice=1d84000.ufshc androidboot.fstab_suffix=default
androidboot.boot_devices=soc/1d84000.ufshc androidboot.serialno=<REDACTED>
androidboot.swtype=normal … normal_reset_type=NORMALBOOT reboot_reason=NORMALBOOT
sreason=D_PS_HOLD reset_type=COLD oba_version=<REDACTED> HIMNTN=<REDACTED>
console=NULL loglevel=0 androidboot.baseband=mdm
msm_drm.dsi_display0=lcd_kit_debussy_290_20d_10p9_qcom: … panel_sn=<REDACTED>
enter_recovery=0 devmodel=DBY-W09 marketingName="HUAWEI MatePad 11"
androidboot.product.hardware.sku=DBY-W09 check_vc=1 androidboot.dtbo_idx=2
usb_macbt=normal androidboot.odm.conn.chiptype=Q userlock=locked androidboot.oemmode=rd
boot_detector_enable=1 boot_recovery_enable=1 bopd_mem_sp=on bopd.mode=0x bootfailno=0x
userdata_2mb_align=true ro.boot.powerkey_restart_type=1
```

Two bootargs facts matter for the candidate-boot risk model and are A-grade here:

- **`androidboot.dtbo_idx=2`** — the running boot selected DTBO entry index 2. ROUND139 could only say "all nine overlay entries wire the six rails identically" and had to leave "which entry ABL selects" UNKNOWN. That specific unknown is now closed for *this* boot.
- **`loglevel=0`** explains why the early boot console is silent and why no probe-time messages survive.

`/proc/cmdline` (1 530 chars, 63 tokens) is the same sequence with **`cgroup_disable=pressure` prepended**; a token-by-token diff shows the other 62 tokens identical and in the same order (suffix match true). The extra token is not in the FDT `bootargs`; whether the kernel or ABL adds it is **not established here** (grade D).

### 3.5 `/memory` — physical RAM

`/memory` has `device_type = "memory"` and no `status` (OF default = available — the ROUND142 terminology correction applies: that is "not disabled", not "verified enabled at runtime"). `reg` is 12 cells = 3 tuples of (`#address-cells` = 2, `#size-cells` = 2):

| # | base | size | MiB | `/proc/iomem` corroboration |
|---:|---|---|---:|---|
| 0 | `0x0000000080000000` | `0x0000000039900000` | 921.0 | `80000000…b98fffff : System RAM` (listing split by carved-out holes) |
| 1 | `0x0000000200000000` | `0x0000000200000000` | 8192.0 | `200000000-3ffffffff : System RAM` |
| 2 | `0x00000000c0000000` | `0x00000000c0000000` | 3072.0 | `c0000000-ffbfffff` + `ffc20000-17fffffff : System RAM` |

Total declared = 12 185 MiB; `MemTotal` = 11 984 584 kB (11.43 GiB), the difference being the 232.7 MiB of static carve-outs plus kernel/dma reservations. `ddr_device_type = <0x7>`.

**ROUND149 D-2 is closed.** The earlier reading — "root `#address-cells`/`#size-cells` cannot be reconciled with a 12-cell `/memory/reg`" — came from the sysfs cell size (`/proc/device-tree/memory@…/reg` is exposed as bytes and the root cell files were denied to uid 2000). With the binary FDT in hand, `ac=2 / sc=2` divides 12 exactly into 3 regions, and `/proc/iomem` independently shows all three windows. There is no inconsistency in the device tree; the inconsistency was in the unreadable-view reconstruction.

### 3.6 `/reserved-memory` — 37 children

Group node: `#address-cells = 2`, `#size-cells = 2`, `phandle = 0x682`, `ranges` empty (i.e. identity mapping).

| # | node | base | size | MiB | flags |
|---:|---|---|---|---:|---|
| 1 | `hyp_region@80000000` | 0x80000000 | 0x600000 | 6.0 | no-map |
| 2 | `xbl_aop_region@80700000` | 0x80700000 | 0x160000 | 1.4 | no-map |
| 3 | `reserved-memory@80860000` | 0x80860000 | 0x20000 | 0.1 | no-map `qcom,cmd-db` |
| 4 | `res_xbl_uefi_log_region@80880000` | 0x80880000 | 0x14000 | 0.1 | no-map `removed-dma-pool` |
| 5 | `smem_region@80900000` | 0x80900000 | 0x200000 | 2.0 | no-map |
| 6 | `removed_region@80b00000` | 0x80b00000 | 0x5300000 | 83.0 | no-map |
| 7 | `pil_camera_region@86200000` | 0x86200000 | 0x500000 | 5.0 | no-map `removed-dma-pool` |
| 8 | `pil_wlan_fw_region@86700000` | 0x86700000 | 0x100000 | 1.0 | no-map `removed-dma-pool` |
| 9 | `pil_ipa_fw_region@86800000` | 0x86800000 | 0x10000 | 0.1 | no-map `removed-dma-pool` |
| 10 | `pil_ipa_gsi_region@86810000` | 0x86810000 | 0xa000 | 0.0 | no-map `removed-dma-pool` |
| 11 | `pil_gpu_region@8681a000` | 0x8681a000 | 0x2000 | 0.0 | no-map `removed-dma-pool` |
| 12 | `pil_npu_region@86900000` | 0x86900000 | 0x500000 | 5.0 | no-map `removed-dma-pool` |
| 13 | `pil_video_region@86e00000` | 0x86e00000 | 0x500000 | 5.0 | no-map `removed-dma-pool` |
| 14 | `pil_cvp_region@87300000` | 0x87300000 | 0x500000 | 5.0 | no-map `removed-dma-pool` |
| 15 | `pil_cdsp_region@87800000` | 0x87800000 | 0x1400000 | 20.0 | no-map `removed-dma-pool` |
| 16 | `pil_slpi_region@88c00000` | 0x88c00000 | 0x1500000 | 21.0 | no-map `removed-dma-pool` |
| 17 | `pil_adsp_region@8a100000` | 0x8a100000 | 0x1d00000 | 29.0 | no-map `removed-dma-pool` |
| 18 | `pil_spss_region@8be00000` | 0x8be00000 | 0x100000 | 1.0 | no-map `removed-dma-pool` |
| 19 | `cdsp_secure_heap@8bf00000` | — | no reg/size | — | no-map `removed-dma-pool` |
| 20 | `adsp_region` | — | dyn size=0xc00000 align=0x400000 alloc-ranges=0x0 | — | reusable `shared-dma-pool` |
| 21 | `sdsp_region` | — | dyn size=0x800000 align=0x400000 | — | reusable `shared-dma-pool` |
| 22 | `cdsp_region` | — | dyn size=0x400000 align=0x400000 | — | reusable `shared-dma-pool` |
| 23 | `cont_splash_region@9c000000` | 0x9c000000 | 0x2300000 | 35.0 | — |
| 24 | `disp_rdump_region@9c000000` | 0x9c000000 | 0x800000 | 8.0 | — |
| 25 | `dfps_data_region@9e300000` | 0x9e300000 | 0x100000 | 1.0 | — |
| 26 | `mem_dump_region` | — | dyn size=0x2800000 | — | reusable `shared-dma-pool` |
| 27 | `sp_region` | — | dyn size=0x1000000 align=0x400000 | — | reusable `shared-dma-pool` |
| 28 | `user_contig_region` | — | dyn size=0x1000000 align=0x400000 | — | reusable `shared-dma-pool` |
| 29 | `rainbow_mem@b0000000` | 0xb0000000 | 0x400000 | 4.0 | no-map `removed-dma-pool,rainbow_mem` |
| 30 | `bootfail_mem@b0400000` | 0xb0400000 | 0x800 | 0.0 | no-map `removed-dma-pool,bootfail_mem` |
| 31 | `kerneldump` | 0x0 | 0x0 | 0.0 | — (unpopulated placeholder) |
| 32 | `qseecom_region` | — | dyn size=0x1400000 align=0x400000 | — | reusable `shared-dma-pool` |
| 33 | `qseecom_ta_region` | — | dyn size=0x1000000 align=0x400000 | — | reusable `shared-dma-pool` |
| 34 | `secure_display_region` | — | dyn size=0xa400000 align=0x400000 | — | reusable `shared-dma-pool` |
| 35 | `cnss_wlan_region` | — | dyn size=0x2000000 align=0x400000 | — | reusable `shared-dma-pool` |
| 36 | `linux,cma` | — | dyn size=0x2000000 align=0x400000 | — | reusable `linux,cma-default` `shared-dma-pool` |
| 37 | `mailbox_region` | — | dyn size=0x20000 align=0x400000 | — | no-map `shared-dma-pool` |

- **Count check:** 37 children = 23 with a non-zero `reg` + 1 zero-size `reg` (`kerneldump`) + 13 dynamic (`size`/`alignment`/`alloc-ranges`) nodes. Total statically placed = **232.7 MiB**.
- **Overlap analysis (decoded, not guessed): exactly one overlap**, `disp_rdump_region@9c000000 [0x9c000000, 0x9c800000)` fully inside `cont_splash_region@9c000000 [0x9c000000, 0x9f300000)`, 8 388 608 B. The rdump window being carved out of the splash buffer is a display-ramdump arrangement, not a sizing error; it is reported as observed and not "corrected". No other pair overlaps.
- **Every statically placed range falls inside one of the three `/memory` regions**, as required.
- `linux,cma` is `reusable` + `linux,cma-default` with a 32 MiB dynamic window — consistent with the 32 MiB `cnss_wlan_region` and the 164 MiB `secure_display_region` claims being *reservations of headroom*, not fixed carve-outs.
- ROUND149 counted 37 directory entries; the binary FDT has exactly 37 child nodes. **No discrepancy.**

---

## 4. UFS — live declarations and live state

### 4.1 Controller `/soc/ufshc@1d84000`

`status = "ok"`, `compatible = "qcom,ufshc"`, `phandle = 0x3b6`, `reg = <0x1d84000 0x3000 0x1d90000 0x8000>` (`reg-names = "ufs_mem","ufs_ice"`).

Supply / power declarations — **this is the six-rail answer, from the live merged tree**:

| Property | Resolves to | Kind |
|---|---|---|
| `vcc-supply` | `/soc/rsc@18200000/rpmh-regulator-ldoa17/regulator-pm8150-l17` | rail (UFS VCC) |
| `vccq-supply` | `…/rpmh-regulator-ldoa6/regulator-pm8150-l6` | rail (UFS VCCQ) |
| `vccq2-supply` | `…/rpmh-regulator-smpa4/regulator-pm8150-s4` | rail (UFS VCCQ2) |
| `qcom,vddp-ref-clk-supply` | `…/rpmh-regulator-ldoa6/regulator-pm8150-l6` | rail, second consumer of L6 |
| `qcom,vccq-parent-supply` | `…/rpmh-regulator-smpc8/regulator-pm8150a-s8` | consumer-declared parent rail |
| `vdd-hba-supply` | `/soc/qcom,gdsc@177004` (`regulator-name = "ufs_phy_gdsc"`) | GDSC as a regulator |
| `vcc-low-voltage-sup`, `vdd-hba-fixed-regulator` | present but **empty** | vendor marker properties |
| `power-domains` | **ABSENT** | — |
| `operating-points-v2` | **ABSENT** (uses `freq-table-hz` + devfreq instead) | — |

Constraints as declared: `vcc-voltage-level = <2504000 2950000>`, `vcc-max-microamp = 800000`, `vccq-max-microamp = 800000`, `vccq2-max-microamp = 800000`, `qcom,vccq-parent-max-microamp = 210000`, `qcom,vddp-ref-clk-max-microamp = 100`, `lanes-per-direction = 2`, `dev-ref-clk-freq = 0`.

### 4.2 PHY `/soc/ufsphy_mem@1d87000`

`status = "ok"`, `compatible = "qcom,ufs-phy-qmp-v4"`, `phandle = 0x77`, `#phy-cells = 0`, `reg = <0x1d87000 0xe00 0x1d90000 0x8000>` (`reg-names = "phy_mem","ufs_ice"`), `lanes-per-direction = 2`.

| Property | Resolves to |
|---|---|
| `vdda-phy-supply` | `…/rpmh-regulator-ldoa5/regulator-pm8150-l5` |
| `vdda-pll-supply` | `…/rpmh-regulator-ldoa9/regulator-pm8150-l9` |
| `vdda-phy-always-on` | present (boolean, empty value) — **new** |
| `vdda-phy-max-microamp` | 89 900 µA |
| `vdda-pll-max-microamp` | 18 800 µA |
| `power-domains` | **ABSENT** |

`vdda-phy-always-on` declares that the PHY rail must not be powered down while the PHY is present. It is a PHY-side declaration only — it does **not** explain L5's five enabled users, which are other devices sharing the rail (§4.4).

The host binds to PHY `0x77` via `phys = <0x77>` / `phy-names = "ufsphy"`, and `/sys/.../of_node` for both nodes resolves into `/sys/firmware/devicetree/base/soc/…`, i.e. the same blob that was captured.

### 4.3 The six rails — declared vs ROUND139

| Rail | Regulator-name | Provider group | Live DT consumer |
|---|---|---|---|
| L5 | `pm8150_l5` | `rpmh-regulator-ldoa5` | `ufsphy.vdda-phy-supply` |
| L6 | `pm8150_l6` | `rpmh-regulator-ldoa6` | `ufshc.vccq-supply` **and** `ufshc.qcom,vddp-ref-clk-supply` |
| L9 | `pm8150_l9` | `rpmh-regulator-ldoa9` | `ufsphy.vdda-pll-supply` |
| L17 | `pm8150_l17` | `rpmh-regulator-ldoa17` | `ufshc.vcc-supply` |
| S4 | `pm8150_s4` | `rpmh-regulator-smpa4` | `ufshc.vccq2-supply` |
| S8 | `pm8150a_s8` | `rpmh-regulator-smpc8` | `ufshc.qcom,vccq-parent-supply` |

This is the same six-rail assignment ROUND139 derived from the DTBO `__fixups__` labels, and the same one the candidate DTB declares (ROUND147 §: `ldo17`/`ldo6`/`ldo6`/`smps4`/`smps8` + `ldo5`/`ldo9` on the PHY). Three different artefacts, three different phandle numbering schemes, identical connectivity.

**What is new here:** ROUND139 recorded that the *base* FDT declares no UFS supply at all and both nodes are `status = "disabled"` — i.e. the wiring exists only after overlay application. The live FDT shows `status = "ok"` on both nodes **and** all seven supply properties present. Since `androidboot.dtbo_idx=2`, this is a direct, values-level confirmation that DTBO entry 2 carries `fragment@63`/`fragment@64` and that they were applied on this boot. ROUND139's "which entry ABL selects" is closed for this boot.

### 4.4 The six rails — live regulator state (uid 0)

| Rail | `regulator.N` | µV (live) | min / max µV | state | num_users |
|---|---|---:|---|---|---:|
| L5 | 14 | 880 000 | 880 000 / 880 000 | enabled | **5** |
| L6 | 17 | 1 200 000 | 1 200 000 / 1 200 000 | enabled | **2** |
| L9 | 19 | 1 200 000 | 1 200 000 / 1 200 000 | enabled | **4** |
| L17 | 29 | 2 504 000 | 2 496 000 / 3 008 000 | enabled | **1** |
| S4 | 7 | 1 800 000 | 1 800 000 / 1 920 000 | enabled | **5** |
| S8 | 37 | 1 200 000 | 1 200 000 / 1 400 000 | enabled | **2** |

Cross-check against ROUND139's static `qcom,init-voltage` column: L5 880 000 ✔, L6 1 200 000 ✔, L9 1 200 000 ✔, L17 2 496 000 → live **2 504 000** (the consumer set a value 8 mV above init, inside the declared 2 496 000–3 008 000 window) ✔, S4 1 800 000 ✔, S8 1 200 000 ✔.

User-count reconciliation from `/sys/kernel/debug/regulator/regulator_summary` (children are consumers):

- **L17 (1 user)**: `1d84000.ufshc 2504mV / 2950mV` — exactly one consumer, the host VCC input.
- **L6 (2 users)**: `1d84000.ufshc` appears **twice** at 1200 mV — the two distinct host inputs (`vccq`, `vddp-ref-clk`) that both point at L6. The count is real, not a duplicate entry.
- **S4 (5 users)**: `1d84000.ufshc` + 3 × `wcd938x-codec` + `cnss-qca6390`, all at 1800 mV; the `va-macro` entry sits at 0 mV as an unasserted constraint.
- **S8 (2 users)**: `bt_qca6390` and `cnss-qca6390` at 1200 mV, plus `1d84000.ufshc` at **0 mV / 0 mV** — the UFS use of S8 carries no voltage constraint, which is exactly what `qcom,vccq-parent-supply` means, so S8's `num_users = 2` counts the two *enabled* consumers and the UFS relation is a current/parent vote, not a third enabled user.
- **L5 (5 enabled users)**: 7 consumers carry a 880 mV constraint — `1d87000.ufsphy_mem`, `88e3000.hsphy`, `88e4000.hsphy`, `ae94400`/`ae96400` MDSS DSI PHY, `1c00000.pcie`, `1c08000.pcie` — with `1c10000.pcie` at 0 mV. `num_users = 5` counts only the *enabled* ones, so a constrained-but-not-enabled consumer must not be added to the count.
- **L9 (4 enabled users)**: 8 consumers carry a 1200 mV constraint — `1d87000.ufsphy_mem`, `ae90000.dp_display`, `88e8000`/`88eb000` SSPHY, `ae94000`/`ae96000` MDSS DSI CTRL, `1c00000.pcie`, `1c08000.pcie` — with `1c10000.pcie` at 0 mV; again only 4 are enabled.

`num_users` therefore counts *enabled* consumers, while `regulator_summary` also lists consumers that have only registered a voltage constraint. The two must be read together, and neither figures above is derived by adding up the children column.

### 4.5 `ufs_phy_gdsc` — bound, declared as `vdd-hba`, never enabled

| Item | Value |
|---|---|
| DT node | `/soc/qcom,gdsc@177004`, `compatible = "qcom,gdsc"`, `reg = <0x177004 0x4>`, `regulator-name = "ufs_phy_gdsc"`, `qcom,retain-regs` (empty/boolean) |
| Live regulator | `regulator.55` → device `177004.qcom,gdsc` |
| `state` | **disabled** |
| `num_users` | **0** |
| `regulator_summary` | `ufs_phy_gdsc  0  2  0  0mV …`, single child `1d84000.ufshc  0mV/0mV` |
| `power-domains` referencing it | **none** in the whole tree |

So on the running stock system the UFS PHY GDSC is (a) present and probed, (b) named as the `vdd-hba` regulator of `ufshc`, and (c) **not enabled and not used as a power domain** while UFS is fully active at HS-G1 ×2 lanes.

Interpretation, ranked honestly:
1. **A-grade:** the node exists, the supply link resolves, the runtime use count is 0 and the state is `disabled`.
2. **C/D-grade:** *why*. Either the HOS `ufshcd-qcom` build never votes for `vdd-hba` on this platform, or the GDSC is effectively always-on in hardware and the driver's vote is meaningless. ROUND139 §2.4 recorded that HOS attaches UFS to **no** power domain while pinned ACK attaches both `ufs_mem_hc` and `ufs_mem_phy` to `UFS_PHY_GDSC`; this capture shows the HOS mechanism is the `vdd-hba` *regulator* path, and that path is inert at runtime. It does **not** prove the PHY is unpowered — the PHY is demonstrably working.

This is a concrete delta the candidate-boot risk model did not previously have, and it is a *behavioural* difference (ACK votes the GDSC through genpd, HOS does not vote at all), not merely a naming difference.

### 4.6 Host / device live state

| Item | Value |
|---|---|
| Driver binding | `ufshcd-qcom` (`/sys/bus/platform/drivers/ufshcd-qcom`), `power/runtime_status = active` |
| PHY binding | `ufs_qcom_phy_qmp_v4`, `runtime_status = unsupported` |
| `qcom/power_mode` | `[Rx,Tx]: Gear[1,1], Lane[2,2], PWR[FAST MODE,FAST MODE], Rate-A` |
| `qcom/bus_speed_mode` | `0` |
| `qcom/clk_status`, `qcom/err_state` | `0`, `0` |
| `qcom/err_count` | `pa_err_cnt_total 0`, `dl_err_cnt_total 0`, `dme_err_cnt 0` |
| `attributes/current_power_mode` | `0x11` (UFS_ACTIVE) |
| `attributes/active_icc_level` | `0x0F` |
| `attributes/reference_clock_frequency` | `0x00` |
| `attributes/boot_lun_enabled` | `0x01` |
| `attributes/bkops_status` | `0x01`; `flags/bkops_enable = true` |
| `attributes/ffu_status` | `0x01` |
| `attributes/wb_*` | `wb_avail_buf 0x0A`, `wb_cur_buf 0x160F`, `wb_life_time_est 0x05`; `flags/wb_enable = false` |
| `auto_hibern8` | 1000 |
| devfreq | governor `simple_ondemand`, cur 37 500 000 Hz, available 37.5 MHz / 300 MHz, `max_freq` 300 MHz, 4 328 total transitions |

Device descriptor (readable values only): `specification_version 0x0310` (UFS 3.1), `manufacturer_id 0x01CE` (raw JEDEC code — vendor name intentionally not asserted), `number_of_luns 0x06`, `number_of_wluns 0x04`, `queue_depth 0x20`, `rtt_capability 0x02`, `support_security_lun 0x01`, `wb_type 0x01`, `psa_max_data_size 0x0`.
Geometry: `raw_device_capacity 0x000000000EE64000` (in 512 B units ⇒ 127 985 000 000 B ≈ 119 GiB usable geometry, consistent with a 128 GB part), `segment_size 0x2000`, `max_number_of_contexts 0x05`, `bMaxInBufferSize/bMaxOutBufferSize 0x08`.
Health: `eol_info 0x01`, `life_time_estimation_a 0x03`, `life_time_estimation_b 0x03`.
Low-power: `rpm_lvl = 3`, `spm_lvl = 3`.
SCSI: single host `host0`, `proc_name = ufshcd`, `state = running`.

`attributes/reference_clock_frequency = 0x00` while the DT declares `ref_clk` 37.5 MHz and devfreq reports 37.5 MHz is left as an observed raw value; no interpretation is offered (grade C at most).

### 4.7 LUN → block map (metadata only)

`/sys/class/block` shows six UFS disks, matching `number_of_luns = 6`:

| Disk | SCSI address | size (512 B sectors) | logical / physical block | `ro` |
|---|---|---:|---|---:|
| sda | `0:0:0:0` | 245 547 008 (≈117 GiB) | 4096 / 4096 | 0 |
| sdb | `0:0:0:1` | 16 384 (8 MiB) | 4096 / 4096 | 0 |
| sdc | `0:0:0:2` | 16 384 (8 MiB) | 4096 / 4096 | 0 |
| sdd | `0:0:0:3` | 65 536 (32 MiB) | 4096 / 4096 | 0 |
| sde | `0:0:0:4` | 4 194 304 (2 GiB) | 4096 / 4096 | 0 |
| sdf | `0:0:0:5` | 65 536 (32 MiB) | 4096 / 4096 | 0 |

`/sys/class/block/*/size` is always in 512-byte units regardless of the 4 KiB logical block size — stated explicitly so a later round does not multiply by 4096 and conclude the device has a 1 TB LUN.

`/dev/block/by-name` holds **86** symlinks (firmware slots on `sde`, `sdd`, `sda`, `sdf`); names and targets only, no partition content was opened, read, hashed or copied.

---

## 5. ARC / PMIC architecture — live

### 5.1 Seven level providers, 47 providers total

Live FDT: **7** nodes with `compatible = "qcom,rpmh-arc-regulator"`, each carrying `qcom,resource-name`:

| Provider | `qcom,resource-name` | children (regulator-name) |
|---|---|---|
| `rpmh-regulator-mxlvl` | `mx.lvl` | `pm8150a_s3_level` (0x6a), `pm8150a_s3_level_ao` (0x7b), `pm8150a_s3_mmcx_sup_level` (0x7f) |
| `rpmh-regulator-cxlvl` | `cx.lvl` | `pm8150_s3_level` (0x67), `pm8150_s3_level_ao` (0x68), `pm8150_s3_mmcx_sup_level` (0x7a) |
| `rpmh-regulator-mmcxlvl` | `mmcx.lvl` | `pm8150a_s4_level` (0x69), `pm8150a_s4_level_ao` (0x3c1), `pm8150a_s4_level_so` (no phandle) |
| `rpmh-regulator-lmxlvl` | `lmx.lvl` | `pm8150_l4_level` (0x92) |
| `rpmh-regulator-lcxlvl` | `lcx.lvl` | `pm8150_l11_level` (0x91) |
| `rpmh-regulator-gfxlvl` | `gfx.lvl` | `pm8150a_s1_level` (0x75) |
| `rpmh-regulator-ebilvl` | `ebi.lvl` | `pm8150a_s6_level` (0x3c2) |

`/sys/devices/platform/soc/18200000.rsc` exposes **47** child provider devices (7 ARC + 40 `qcom,rpmh-vrm-regulator`), all bound to the `rpmh` platform driver — the same 47 ROUND149 counted in the class directory, now confirmed at the platform-device level with names.

### 5.2 The five provider-child edges (vs ROUND139)

| Group property | Live phandle | Resolves to |
|---|---:|---|
| `cxlvl / pm8150_s3_level-parent-supply` | 0x6a | `mxlvl/regulator-pm8150a-s3-level` |
| `cxlvl / pm8150_s3_level_ao-parent-supply` | 0x7b | `mxlvl/regulator-pm8150a-s3-level-ao` |
| `mmcxlvl / pm8150a_s4_level-parent-supply` | 0x7f | `mxlvl/regulator-pm8150a-s3-mmcx-sup-level` |
| `mmcxlvl / pm8150a_s4_level_ao-parent-supply` | 0x7b | `mxlvl/regulator-pm8150a-s3-level-ao` |
| `mxlvl / pm8150a_s3_mmcx_sup_level-parent-supply` | 0x7a | `cxlvl/regulator-pm8150-s3-mmcx-sup-level` |

**5 of 5 match ROUND139's list one-for-one**, on a blob whose phandle numbering is different from the one ROUND139 read (0x6a/0x7b/0x7f/0x7a here vs 106/123/127/123/122 there). Independent numbering with identical topology is a strong confirmation, not a re-read of the same file.

GDSC → ARC level edges also match: exactly **13** GDSC nodes carry `parent-supply` **and** `vdd_parent-supply` (26 occurrences) — 11 → `mmcxlvl/pm8150a_s4_level`, 1 → `cxlvl/pm8150_s3_level`, 1 → `gfxlvl/pm8150a_s1_level`.

### 5.3 Runtime nesting — ROUND149 D-9 resolved

`/sys/kernel/debug/regulator/regulator_summary` nests consumers under suppliers, which fixes the direction unambiguously:

```
pm8150_s3_mmcx_sup_level       use=3  open=2
  └─ pm8150a_s3_mmcx_sup_level      use=3  open=1
       └─ pm8150a_s4_level           use=3  open=31
```

(`use` = enabled consumers, `open` = cumulative enable calls; the nesting is what matters here, not the second column.)

and the same chain is present in the FDT phandles (0x7a → 0x7f → 0x69). Both independent sources agree: **MMCX level consumes MX-mmcx-sup, which consumes CX-mmcx-sup.**

This is the opposite of how ROUND149 D-9 described its own `-SUPPLY` reading ("the MX mmcx-sup child is supplied by the MMCX level child"). The cause was a symlink-semantics inversion: the `<consumer>-SUPPLY` link is created **in the supplier's directory** and points **at the consumer**. ROUND149 read `regulator.32-SUPPLY` inside `regulator.3` as "regulator.3 is supplied by 32", when it means "32 is a consumer of 3". **D-9 is now closed in favour of ROUND139's direction**, and the FDT/ROUND139 wording was correct all along.

Consumer counts at runtime: `pm8150_s3_mmcx_sup_level` 3, `pm8150a_s3_mmcx_sup_level` 3, `pm8150a_s4_level` 3, `pm8150_s3_level` 2, `pm8150a_s3_level` 2, `pm8150a_s3_level_ao` 1, `pm8150_s3_level_ao` 1, `pm8150a_s4_level_ao` 0 (disabled), `pm8150a_s1_level` 0 (disabled), `pm8150_l11_level` 0 (disabled), `pm8150_l4_level` 0 (disabled), `pm8150a_s6_level` 0 (disabled).

The ARC regulators report their value in *level*, not volts (e.g. `microvolts = 192` for `pm8150a_s4_level` with min/max 64/384). Those numbers are level encodings and must never be read as µV.

### 5.4 Proxy consumers

| Site | Declaration | Value |
|---|---|---|
| `rpmh-regulator-ldoa5` / `regulator-pm8150-l5` | `proxy-supply` → itself; `qcom,proxy-consumer-enable` (boolean); `qcom,proxy-consumer-current` | 100 000 µA |
| `rpmh-regulator-ldoa9` / `regulator-pm8150-l9` | same pattern | 100 000 µA |
| `rpmh-regulator-ldoa14` / `regulator-pm8150-l14` | `proxy-supply` → itself; `qcom,proxy-consumer-current` | 62 000 µA |
| `rpmh-regulator-cxlvl` | `proxy-supply` → `regulator-pm8150-s3-mmcx-sup-level` | — |
| `…-s3-mmcx-sup-level` | `qcom,proxy-consumer-enable`, `qcom,proxy-consumer-voltage` | `<0x180 0xffff>` |
| `mmcxlvl` | `proxy-supply` → `regulator-pm8150a-s4-level` | — |
| `/soc/qcom,gdsc@af03000` | `proxy-supply` → itself; `qcom,proxy-consumer-enable` | — |

14 proxy-bearing nodes in total. **Both UFS PHY rails (L5, L9) are proxy-consumer rails**: the PHY is not the only entity that can vote on them, so a rail held at 880 mV / 1200 mV with 5 and 4 users does not by itself prove the PHY is the load.

### 5.5 What this does to ROUND146 / AI2 ROUND148

Neither report is present in the repository (§9, V-8), so this is a statement about *evidence*, not about their text. What ROUND151 adds to that discussion:

- The **producer side** the ACK supposedly lacks is demonstrably present and working on the stock kernel: 7 ARC provider groups, 40 VRM providers, 5 provider-child parent edges, 13 GDSC→level edges, all bound to a single `rpmh` driver at `18200000.rsc`.
- The **level values** stay out of reach: nothing here exposes the RPMh sleep/wake vote values (`/sys/kernel/debug/cmd_db` exists but was **not** read — see §8.1), so "ARC support gap" remains a *declaration and binding* question that is now answered, and a *vote-value* question that is still open.

---

## 6. Logs

### 6.1 debugfs was already mounted — not mounted by this agent

`mount` (read before any debugfs read) shows, as pre-existing system state:

```
tracefs on /sys/kernel/tracing        type tracefs  (rw,seclabel,relatime)
debugfs on /sys/kernel/debug          type debugfs  (rw,seclabel,relatime)
tracefs on /sys/kernel/debug/tracing  type tracefs  (rw,seclabel,relatime)
```

Every debugfs read in this round is therefore permitted by taskbook §3.4 ("only if debugfs is already mounted"). No mount, remount or namespace change was performed.

Read: `regulator/regulator_summary` (25 966 B, full), `pm_genpd/pm_genpd_summary` (only one domain listed: `ae00000.qcom,mdss_mdp off-0` — UFS is not a genpd client here), `clk/clk_summary` (filtered to `ufs*`), `opp/` (contains `soc-1d84000.ufshc`). Not modified.

`clk_summary` shows `gcc_ufs_phy_tx_symbol_0_clk`, `gcc_ufs_phy_rx_symbol_0_clk`, `gcc_ufs_phy_rx_symbol_1_clk` at use-count 1, while `gcc_ufs_phy_ahb_clk`, `gcc_ufs_phy_axi_clk`, `gcc_ufs_phy_unipro_core_clk`, `gcc_ufs_phy_ice_core_clk` read 0. That is a momentary snapshot of an idle link, not a fault; it is reported as raw state.

### 6.2 dmesg

| Item | Value |
|---|---|
| Bytes | 994 476 |
| Lines | 7 579 |
| Window | uptime 198 074.36 s → 198 308.11 s (**234 s**), wall 2026-11-26 22:19:37 → 22:23:31 |
| `ufs` / `rpmh` / `regulator` / `genpd` / `devfreq` / `deferred` hits | **0 / 0 / 0 / 0 / 0 / 0** |
| `watchdog` / `thermal` hits | 24 / 31 |
| Panic / oops / call trace | none |
| `logcat -b kernel -d` | **empty** |

Two conclusions, both negative and both useful:

1. **The ring buffer no longer holds the boot.** At 198 308 s of uptime, everything from probe time has been overwritten. Any claim of the form "driver X bound and voted at boot" cannot be recovered from this build without a reboot, which is prohibited. Runtime state must be read from sysfs, as done here.
2. **HOS does not mirror kernel messages into logd's `kernel` buffer** — ROUND149's finding is confirmed under root.

The buffer does contain `KernelSU: su_compat …` lines for the commands this round issued (they are the only reason those lines exist) and a `HISEC: [ENGINE] usb-debug: record updated / upload disabled, never upload configured` pair. The HISEC line is noted only because it plausibly relates to the ADB-dropout described in §10.1; it is **not** evidence of the cause.

---

## 7. Cross-round reconciliation

| Ref | Previous state | ROUND151 | Effect |
|---|---|---|---|
| **R139 §1** | "base FDT declares no UFS supply at all; both nodes `status="disabled"`; all nine DTBO entries wire the six rails identically; which entry ABL selects UNKNOWN" | live merged FDT: both nodes `status="ok"`; all 7 supplies present; `dtbo_idx=2` | **Entry selection closed for this boot** (A); "identical in all nine entries" is now moot for this boot and still unverified for the other eight |
| **R139 §2.2** | six rails, static min/max/init µV, runtime state UNKNOWN | all six rails live-enabled with matching voltages and explicit user counts | **Runtime half closed** (A) |
| **R139 §2.3 (2b)** | exactly five provider-child edges, phandles 106/123/127/123/122 | exactly five, phandles 0x6a/0x7b/0x7f/0x7b/0x7a, same endpoints | **Reconfirmed on a different blob** (A) |
| **R139 §2.4** | "HOS attaches UFS to no power domain; ACK attaches both nodes to UFS_PHY_GDSC" | confirmed: zero `power-domains` on both nodes, zero referencing nodes; HOS uses `vdd-hba` → GDSC **regulator**, which is never enabled | **Mechanism identified**; behavioural delta for candidate boot quantified |
| **R139 §2.2 note** | physical electrical input of every rail UNKNOWN | unchanged — no `vin-supply` in the live FDT either | **Still UNKNOWN**; the schematic page ROUND64 asked for is still the only closer |
| **R147** | candidate DTB: 905 nodes, **0** ARC groups, 18 reserved-memory, `ufshc` has `power-domains` + OPP table | stock: 4 566 nodes, **7** ARC groups, 37 reserved-memory, no `power-domains`, no OPP table | The R146-style gap is now quantified **stock-side as well** |
| **R149 §1** | `/chosen` has no EFI/usable-memory property (structure only) | four properties read in full, values included; none is EFI | **Upgraded to values-level A** |
| **R149 D-2** | root cells vs 12-cell `/memory/reg` inconsistent | `ac=2/sc=2`, 3 regions, `/proc/iomem` agrees | **Closed — no defect** |
| **R149 D-9** | ARC parent/child direction contradicts R139 | FDT phandles + `regulator_summary` nesting both agree with R139 | **Closed in favour of R139**; R149's link reading was inverted |
| **R149 U-1** | "`/sys/firmware/fdt` unreadable by construction without root" | read, hashed, decoded | **Closed** |
| **R149 U-5** | runtime MMCX/MX/CX votes unreadable | user counts and nesting now readable; **vote values still not** (cmd_db not read) | **Partially closed** |

### 7.1 Stock vs candidate, side by side

| Aspect | Stock HOS 4.19 (this capture) | Candidate ACK 6.18 (ROUND147) |
|---|---|---|
| UFS VCC / VCCQ / VCCQ2 / parent | L17 / L6 / S4 / S8 | L17 / L6 / S4 / S8 |
| PHY VDDA-PHY / VDDA-PLL | L5 / L9 | L5 / L9 |
| `vdd-hba` | `<&gdsc@177004>` (`ufs_phy_gdsc`) as a **regulator** | GCC `UFS_PHY_GDSC` as a **power domain** |
| `power-domains` on ufshc | absent | `<rpmhpd 6>, <gcc 4>` |
| `operating-points-v2` | absent (`freq-table-hz` + devfreq) | present, 2 OPPs with `required-opps` to rpmhpd `opp3`/`opp6` |
| ARC level providers | **7** (`mmcx`/`mx`/`cx`/`lmx`/`lcx`/`gfx`/`ebi`) | **0** |
| reserved-memory children | 37 | 18 |
| DT nodes | 4 566 | 905 |

The rail wiring is the part that **is** equivalent. The corner/level architecture and the GDSC attachment mechanism are the parts that **are not**, and both are now evidenced on the stock side with values rather than inference.

---

## 8. Gate matrix after ROUND151

| Gate | Status | Basis |
|---|---|---|
| G1 — root obtainable on stock HOS 4.3 | **PASS** | `su -c id` → `uid=0(root)`, `u:r:ksu:s0`, one invocation, no bypass |
| G2 — live FDT readable and byte-exact | **PASS** | 800 316 B, magic/totalsize ok, device-side and host SHA-256 identical |
| G3 — `/chosen` EFI handoff | **CLOSED (no handoff)** | four properties enumerated, none EFI/usable-range |
| G4 — physical RAM map | **PASS** | 3 regions from FDT + `/proc/iomem` corroboration |
| G5 — reserved-memory inventory | **PASS** | 37 children, 23 sized (232.7 MiB), one intentional overlap |
| G6 — six UFS rails declared | **PASS** | all six resolved in the live merged tree |
| G7 — six UFS rails enabled at runtime | **PASS** | all six `enabled`, users 5/2/4/1/5/2, voltages match R139 within declared windows |
| G8 — UFS link health | **PASS (healthy)** | HS-G1 ×2 lanes, zero PA/DL/DME errors |
| G9 — ARC producer presence on stock | **PASS** | 7 groups declared + 7 bound; 47 providers |
| G10 — ARC parent-edge topology | **PASS** | 5/5 identical to R139, independent phandles |
| G11 — ARC nesting direction | **CLOSED** | MMCX ⇐ MX-mmcx-sup ⇐ CX-mmcx-sup (two independent sources) |
| G12 — RPMh vote **values** | **BLOCKED** | command-DB not read (out of §3 enumerated scope) |
| G13 — physical electrical parents of the six rails | **BLOCKED** | no `vin-supply`/`vph-pwr` anywhere; needs a board power tree or schematic |
| G14 — UFS PHY GDSC behaviour | **NEW OPEN ITEM** | `vdd-hba` GDSC probed but `disabled` / 0 users while UFS active; cause not established |
| G15 — candidate boot readiness | **UNCHANGED / not attempted** | no build, no boot, no flash this round |

---

## 9. Deviations and self-corrections (all disclosed)

| ID | Deviation | Handling |
|---|---|---|
| V-1 | **No ADB transport at session start.** The tablet enumerated as `USB\VID_12D1&PID_107E` with a single child interface (WPD/MTP); the ADB interface was absent, `adb devices -l` was empty, no `unauthorized`/`offline` entry existed, and no USB error device was present. Historical PnP records show this same serial previously as `USB\VID_18D1&PID_D001` (Android Composite ADB Interface), now `Unknown`. | Recorded (`raw/001_preflight_adb.txt`, `raw/002_preflight_hostpnp.txt`); asked the user; user re-enabled USB debugging; transport came up as `device` on the first poll. **No privileged read happened before the gate.** |
| V-2 | **No root manager dialog appeared.** Root was granted immediately with `context=u:r:ksu:s0`. | Reported as observed. Nothing was clicked, pre-approved or automated; if the user's manager was configured to remember the grant, that predates this session. |
| V-3 | First 1xx batch invoked bare `adb` (not on `PATH`) ⇒ 12 rows exit 127. | Index file deleted, batch re-run with the absolute path; **zero** stale outputs retained. Only the successful rows exist. |
| V-4 | Wrong RSC prefix (`/sys/devices/platform/18200000.rsc` instead of `…/platform/soc/…`) ⇒ 2 NOT FOUND. | Kept and marked NOT FOUND; corrected commands added as 417–420. |
| V-5 | `dmesg` was first classified NOT FOUND because log text contains the words "not found"/"denied". | Classifier rule changed to `rc == 0 ⇒ PASS`; index recomputed **from the stored bytes**, dmesg was not re-captured (one snapshot only). |
| V-6 | **`-SUPPLY` symlink direction was initially misread** and would have inverted the ARC chain in this report. | Caught before publication by testing the one-consumer case (L17) and by cross-checking `regulator_summary` nesting. §5.3 now states the correct direction and explicitly supersedes ROUND149 D-9. |
| V-7 | `/chosen` shows 4 properties vs ROUND149's "five". | Reconciled: 4 DT properties + kernel-synthesised `name`. Documented in §3.4 so a later round does not treat it as a regression. |
| V-8 | **Referenced material absent:** ROUND143 (FDT/RAM/EFI handoff), ROUND146 (ACK ARC/proxy gap) and ROUND148 (AI2 portability) exist in **no** branch of the repository (checked `firmware-audit-v1`, `main`, `ai1/…`, `agent2/…`, `workbuddy/…`). | Cross-comparison restricted to ROUND139, ROUND147, ROUND149 and this agent's own ROUND140/142. §5.5 is worded accordingly. |
| V-9 | Taskbook §2.4 asks for exactly one `su -c id`. | One invocation, recorded. |
| V-10 | A display defect rendered single-phandle properties as one-letter strings (`phys = "w"`). | Fixed before any value was written down; recorded in §3.2 and in the parser so later rounds do not inherit it. |

### 9.1 Not read, deliberately

- `/sys/kernel/debug/cmd_db` and `pmic-votable` — the RPMh command DB would give sleep/wake **vote values**, but §3.4 enumerates only *regulator, GenPD and clock* summaries. Treated as out of scope rather than quietly expanded.
- Any `/dev/block/*` content, `dd`, `hexdump`, partition hashes, `adb pull` of a partition.
- App/user data, `logcat` main/system buffers, IMEI/MAC/serial beyond the redacted handoff.
- The UFS `string_descriptors/serial_number` value is captured locally and **redacted** here; `product_revision` is device-identifying in combination and is likewise withheld.

---

## 10. Boundaries and confirmation of no modification

### 10.1 The one state change in this session

USB debugging was turned back on **by the user, on the device**, in response to V-1, before any privileged read. That is a device-setting change this agent requested but did not perform. After that point, nothing was written.

### 10.2 Confirmation

- No `adb root`, no exploit, no alternate privilege path.
- No SELinux mode change; `getenforce` = `Enforcing` throughout.
- No mount / remount / namespace change; debugfs was pre-existing.
- No write to any sysfs/procfs node, devfreq field, UFS attribute, property, partition or block device.
- No FFU / BKOPS / purge / power-mode / gear / descriptor-write command.
- No reboot, power-cycle, recovery, bootloader, fastboot, unlock, flash, temporary boot or candidate kernel start.
- No source, DTS, DTBO, `.config`, patch-series, build-output or candidate-artefact change; the candidate tree was not entered.
- No benchmark, fsck, suspend/resume experiment, stress test or load generation.
- No network download or tool installation; no packages added.

### 10.3 Local-only artefacts

The raw FDT, the full decode, the raw `dmesg`, and any line containing a serial/MAC/panel identifier remain **local** under `r151-root-readonly/evidence/` and are not part of this report. This document contains only sizes, hashes, decoded technical fields and redacted excerpts.

---

## 11. Highest-value next actions (for the dispatcher, not started)

1. **Read `/sys/kernel/debug/cmd_db` (or the `pmic-votable` view) under the same root**, if the dispatcher grants it explicitly. That is the only artefact in reach that can turn G12 from BLOCKED into evidence, and it is a one-shot read of an already-mounted pseudo-filesystem.
2. **Decide what `ufs_phy_gdsc` staying `disabled` while UFS is active means for the candidate** (G14). Options: treat it as an always-on GDSC with a harmless vote, or make the candidate's first boot preserve the HOS behaviour (no GDSC vote) to reduce delta. This round cannot choose; it only shows the stock behaviour.
3. **Obtain the DBY-W09 board power tree or a schematic page** naming the physical input of L5/L9/L6/L17/S4/S8. G13 has been BLOCKED since ROUND64 and no amount of further runtime reading will close it.
4. **Retire the file-name collision** raised in ROUND147/ROUND149 if it is still live for this round: `firmware-analysis/round151/` contains only the taskbook and start prompt, and the report path below was free at commit time.

---

## 12. Deliverable

- This report: `firmware-analysis/round151/WORKBUDDY_ROUND151_ROOT_READONLY_RUNTIME_AUDIT_REPORT.md`
- Branch: `workbuddy/round151-root-readonly-runtime-audit`
- Local evidence (not uploaded): `r151-root-readonly/evidence/{raw,private,meta}` — 152 files, manifest `d1d353cb07cf70ee9df1ea06bee481b26cf7d346dad5bd0e1c9f73a6188284b0`, FDT `fefeaa049f64a9cc79f0aa7558883f7a31ba98cf0ad73f541834c0ec2d46b700`.

**Stop condition reached.** No ROUND152 work started, no code modified, no build, no boot, no flash, no reboot.
