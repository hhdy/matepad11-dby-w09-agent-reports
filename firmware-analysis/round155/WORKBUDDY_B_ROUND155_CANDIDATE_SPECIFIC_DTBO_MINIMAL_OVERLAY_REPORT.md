# ROUND155 — WorkBuddy Window B: candidate-specific minimal DTBO / first-boot analysis

**Executor: WorkBuddy Window B (2号 Agent), a separate WorkBuddy chat window from Window A. Both agents use WorkBuddy.**

Task type: isolated scratch-only overlay design and static application test. **No device, ADB, root, fastboot, recovery, partition read/write, flash, reboot, unlock or state change. No source-branch change, no accepted-patch edit, no full kernel/Image build, no DTBO container creation/modification, and no access to Window A's workspace.**

All paths are sanitised: `<WB14>` = Window B's own ROUND154 workspace, `<WB15>` = the new ROUND155 scratch directory created this round, `<TREE>` = Window B's frozen candidate source tree, `<STOCK_DTBO>` = the stock DTBO already present in Window B's permitted local check set (reused read-only). No raw firmware, private path, serial, IMEI, MAC or panel ID appears in this report.

---

## 0. Verdict (§3.E) — one line

> **The RAM-patched candidate base already contains every proven first-boot essential (RAM, timer, GIC, PSCI, GCC, PMIC regulators, UFS host + UFS PHY, all UFS supply/phandle edges closed); a no-overlay first-boot route is viable subject to bootloader acceptance. Stock Entry 2 contributes *zero* first-boot settings and cannot be applied. A candidate-specific minimal overlay is nevertheless technically applicable — a 199 B `target-path` overlay enabling the existing debug UART applies with RC=0, changes exactly one property, and leaves RAM tuples and all 18 reserved-memory intervals byte-identical. DTBO entry selection and bootloader acceptance remain separately UNKNOWN (no ABL evidence).**

This maps to taskbook §3.E option 2 as the primary verdict, with option 1 demonstrated as an *optional* rescue-console enhancement. It is **not** option 3 (candidate does not lack essential nodes) and not option 4 (safe minimum was established from exact tree + initramfs evidence).

Offline `fdtoverlay` success **does not** prove the device bootloader will apply or select any overlay — stated explicitly per taskbook §3.E.

---

## 1. [§3.A] Candidate baseline (all A-grade, measured this round)

| Item | Value |
|---|---|
| Candidate base | `<WB14>/out/patched.dtb`, **108 680 B**, SHA-256 `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` — matches taskbook §1 and Window A/B ROUND154 reports exactly |
| FDT header | `magic=0xd00dfeed`, `totalsize==filesize==108680`, version/last-comp consistent |
| Source tree | `<TREE>` HEAD `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`, root tree `790a68ae6d4f4ac51ab2d88977b6fd5c031473b7`, board DTS blob `58293f7a62a50f8109886c92ce4b9cd14d7980e2` (all three match Window A's published identities) |
| Toolchain | in-tree `<TREE>/out-dtb/scripts/dtc/dtc` → `Version: DTC 1.7.2-g52f07dcc`; `gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`; `fdtoverlay` from the same build |
| Reproduced base (unpatched) | `<WB14>/out/base.dtb` 108 648 B `cab82fe3…db77e` (byte-equal to frozen ROUND140 candidate, per ROUND154) |
| Node count | 905 nodes; phandles 239; `/__symbols__` absent (base built without `-@`) |
| `/memory@80000000` | `device_type=memory`, 12-cell `reg`, three windows 921 + 3 072 + 8 192 = **12 185 MiB** |
| `/reserved-memory` | **18** children, sum = union = `0xfe9c000` = **254.609375 MiB**, zero overlap, all `no-map` |
| Early boot | timer `/soc@0/timer@17c20000` (`arm,armv7-timer-mem`), GIC `/soc@0/interrupt-controller@17a00000` (`arm,gic-v3`), PDC `/soc@0/interrupt-controller@b220000`, `/psci` (`arm,psci-1.0`), `/soc@0/watchdog@17c10000`, `/smem` — all present |
| Clocks / power | GCC `/soc@0/clock-controller@100000` (`qcom,gcc-sm8250`, phandle 48, `#clock/#reset/#power-domain-cells`), `/soc@0/rsc@18200000/clock-controller` (phandle 46), `/soc@0/rsc@18200000/power-controller` (phandle 52), 12 interconnect nodes |
| PMIC regulators | `/soc@0/rsc@18200000/regulators-0` (`qcom,pm8150-rpmh-regulators`: ldo17 #93, ldo6 #94, smps4 #96, ldo5 #99, ldo9 #100) and `regulators-1` (`qcom,pm8150l-rpmh-regulators`: smps8 #95) |
| UFS host | `/soc@0/ufshc@1d84000` (`qcom,sm8250-ufshc`) **status=okay**, phandle 98, reg `0x1d84000+0x3000`, 2 lanes, OPP table (phandle 92), IOMMU, interrupts |
| UFS PHY | `/soc@0/phy@1d87000` (`qcom,sm8250-qmp-ufs-phy`) **status=okay**, phandle 91 |
| Global status distribution | `(unset)` 811, `disabled` 91, **`okay` exactly 2 — the UFS host and the UFS PHY** |

**UFS supply/phandle closure (all 8 edges resolve to in-tree nodes — no external fixup needed):**

| Consumer property | phandle | Resolves to |
|---|---|---|
| `vcc-supply` | 93 | `regulators-0/ldo17` |
| `vccq-supply` | 94 | `regulators-0/ldo6` |
| `qcom,vccq-parent-supply` | 95 | `regulators-1/smps8` |
| `vccq2-supply` | 96 | `regulators-0/smps4` |
| `qcom,vddp-ref-clk-supply` | 100 | `regulators-0/ldo9` |
| `vdda-phy-supply` | 99 | `regulators-0/ldo5` |
| `vdda-pll-supply` | 100 | `regulators-0/ldo9` |
| host `power-domains` | 52, 6 / 48, 4 | rpmh power-controller / GCC UFS_PHY_GDSC |
| PHY `power-domains` / `resets` | 48,4 / 98,0 | GCC / UFS host |
| host `clocks`/`resets`/`phys`/`interconnects` | 48/46/91/55,54,45,6 | GCC, RPMh clock-controller, PHY, NoC/interconnect nodes |

All 239 phandles in the tree are self-contained; the candidate base has **no** unresolved external DT reference. `/chosen` has **0 properties** — bootargs/initrd must be injected by the bootloader (grade D: no ABL image in workspace).

---

## 2. [§3.B] First-boot minimum classification

### 2.1 Category 1 — kernel early boot / RAM / timer / interrupt / console

| Requirement | Candidate status | Evidence |
|---|---|---|
| RAM (3 windows, 12 185 MiB) | present in base | patched `reg` 12 cells, measured byte-for-byte |
| timer | present | `arm,armv7-timer-mem` at `0x17c20000` |
| interrupt controller | present | GIC-v3 at `0x17a00000` + PDC |
| PSCI / CPU idle | present | `/psci` + 8 power-domain children |
| early console node | **present but `status=disabled`** | `/soc@0/geniqup@ac0000/serial@a90000` (`qcom,geni-debug-uart`, phandle-capable path, reg `0xa90000+0x4000`, irq 357) |
| bootargs / initrd (`/chosen`) | **absent from DTB** | 0 properties; live boot's `earlycon=msm_geni_serial,0xa90000`, `console=NULL loglevel=0`, `androidboot.dtbo_idx=2` come from R151 live `/chosen` (report-derived grade C), not from candidate DT |

The earlycon address in the live boot (`0xa90000`) maps exactly to the candidate's `uart12` node. `earlycon` is cmdline-driven and does not itself require the DT node to be `okay`, but enabling the node gives a usable post-early console/rescue tty — this is the one and only first-boot-adjacent setting absent from the base.

### 2.2 Category 2 — storage discovery: UFS host / PHY / regulators / clocks / resets / interconnect / power domains

**All present and fully wired in the base** (§1 table). The two and only two `okay` nodes are precisely the UFS host and PHY — strong evidence the frozen candidate was built as a minimal storage-boot base. No overlay is needed to make UFS discoverable.

### 2.3 Category 3 — root filesystem access / initramfs

Local evidence (from Window B's own permitted local check set, read-only): the captured separate `ramdisk.img` is an Android header image whose embedded gzip cpio decompresses to 2 884 352 B and contains **17 entries including `/init`** (ELF). Parsed `/init` strings include `First stage mount for rescue mode`, `prepare_ramdisk`, `/dev/block/platform/soc/`, `failed to read fstab from dt`, `/fstab/compatible`, `fstab_suffix`, `/first_stage_ramdisk`, and `/system will not be available for overlayfs`. There is **no standalone fstab file** in the cpio; fstab is loaded from DT `/fstab` or kernel cmdline.

- A rescue shell can run from this initramfs without mounting UFS-backed `/system` (the strings explicitly handle "First stage mount for rescue mode" and a tmpfs second stage) — **do not assume UFS is required to reach rescue shell** (taskbook §3.B).
- Full Android userspace **does** need UFS because `androidboot.bootdevice=1d84000.ufshc` / `androidboot.boot_devices=soc/1d84000.ufshc` (R151 live grade C) and the candidate has no `/fstab` DT node — so the rootfs path depends on bootloader-supplied cmdline + the already-present UFS nodes, not on any DTBO fragment.
- Both paths are satisfied by the base + bootloader cmdline; neither requires stock Entry 2.

### 2.4 Category 4 — non-essential devices (remain disabled)

91 nodes are `status=disabled` and 811 are unset, including every display (34 stock fragments target `mdss_mdp`), camera, audio, WLAN, sensor, and remote-DSP (`adsp`/`cdsp`/`slpi`) node. No first-boot requirement depends on any of them.

---

## 3. [§3.C] Stock Entry 2 vs candidate: required-setting coverage

Window B did **not** retry applying stock Entry 2 (proven failed in ROUND154: 0/166 without `-@`, 10/166 with scratch `-@`, `FDT_ERR_NOTFOUND`). Instead it enumerated all 144 fragment targets statically against the candidate's own symbol table:

| Fragment target resolution | Count |
|---|---|
| Stock fragment targets total | **144** (all use `target=<0xffffffff>` external fixup; zero `target-path`) |
| Target symbol resolves in candidate (scratch `-@`, 514 symbols) | **57** |
| Target symbol absent | **87** |
| Resolved fragments touching first-boot-critical paths (UART/serial, timer, GIC, PSCI, GCC, UFS, PHY, RAM, reserved-memory, `/chosen`, regulators) | **0** |
| Resolved target groups | display-controller 34, pinctrl 9, `/soc@0` 7, spmi 5, `mmc@8804000` 1 (itself `disabled`), `rootparam` 1 |

Of the five SPMI hits, the target is `/soc@0/spmi@c440000` (the bus that hosts the PMIC), but the candidate already has a complete `qcom,pm8150-rpmh-regulators` / `pm8150l` hierarchy under `/soc@0/rsc@18200000/` with all UFS supplies resolved — the SPMI fragments add vendor/board-only children, not first-boot rails. The single `rootparam` fragment (`fragment@143`) targets an empty placeholder node and carries vendor board identity, not a boot essential.

**Conclusion:** every setting that stock Entry 2 could contribute is display/board/vendor/peripheral configuration. None is needed to reach a rescue shell or to discover UFS. Therefore the correct minimal overlay is built **only** from candidate-present nodes and candidate-established properties.

### 3.1 Scratch overlay authored (not applied to accepted source)

New scratch directory `<WB15>` was created. The overlay source `<WB15>/src/minimal-firstboot.dts`:

```
/dts-v1/;
/plugin/;
/ {
    fragment@0 {
        target-path = "/soc@0/geniqup@ac0000/serial@a90000";
        __overlay__ {
            status = "okay";
        };
    };
};
```

- `target-path` is copied **verbatim** from the candidate DTB node path (verified unique: exactly 1 `serial@a90000` node).
- Only property changed: `status: disabled → okay` — an established DT property.
- **No** fabricated label, phandle, regulator/supply mapping, board selector, or vendor property. **No** stock fragment copied. **No** second memory node, no new reserved-memory region.
- Rationale: give a first-boot rescue console by enabling the existing debug UART whose address matches the live `earlycon=…,0xa90000`. Optional enhancement; not required for a no-overlay boot.

Compile command (same frozen dtc as §1, no `-@` needed because `target-path` needs no fixups):

```
<DTC> -I dts -O dtb -o <WB15>/out/minimal-firstboot.dtbo <WB15>/src/minimal-firstboot.dts
```

| Scratch artifact | Size | SHA-256 |
|---|---|---|
| `<WB15>/src/minimal-firstboot.dts` | 435 B | `515d5a9bfd82e9b8073d172075e05dc454e8b79052de553ac52e9bf99e64114b` |
| `<WB15>/out/minimal-firstboot.dtbo` | 199 B | `05494d47506a127f7826fb3db3f3319a9865fbcea5c59fd3c3f603653af1a1c2` |
| `<WB15>/out/patched+minimal.dtb` (apply result) | 108 676 B | `647af49b8c21198d9cba99fac444131aaf95e86c99b28af87b610fc46b30cea2` |

`dtc` produced zero warnings; decompiled `.dtbo` shows exactly one `fragment@0` with `target-path` and `status="okay"`.

---

## 4. [§3.D] Scratch application proof

Apply command:

```
<FDTOVERLAY> -i <WB14>/out/patched.dtb -o <WB15>/out/patched+minimal.dtb <WB15>/out/minimal-firstboot.dtbo
```

| Check | Result |
|---|---|
| application RC | **0** (empty stderr) |
| output size | 108 676 B = 108 680 − 4 (`"disabled"` 8 B → `"okay"` 4 B) |
| output SHA-256 | `647af49b8c21198d9cba99fac444131aaf95e86c99b28af87b610fc46b30cea2` |
| target resolves | target node present in base; `status=disabled → okay` ✔ |
| full structural diff vs base | **exactly 1 changed property**: `/soc@0/geniqup@ac0000/serial@a90000 :: status` (`disabled → okay`); node count 905 → 905 ✔ |
| phandle collision | phandle count 239 → 239; **sets and path mappings identical**; added phandles = none ✔ |
| RAM tuples | 12-cell `reg` byte-for-byte identical (`0000000080000000…0000020000000000`) ✔ |
| 18 reserved-memory intervals | 18 → 18 children; **0 differing children**; sum unchanged `0xfe9c000` = 254.609375 MiB ✔ |
| output DTB parses | `magic=0xd00dfeed`, `totalsize==filesize==108676` ✔ |
| **verdict** | **PASS** |

Full diff (the only change in the entire tree):

```
/soc@0/geniqup@ac0000/serial@a90000 :: status
    before: str:disabled
    after : str:okay
```

**Negative control:** an otherwise identical scratch overlay targeting `/soc@0/does-not-exist@deadbeef` compiled fine but `fdtoverlay` returned rc=1 with `FDT_ERR_NOTFOUND` — so the RC=0 above is a real resolution, not a no-op.

**Fixup-independence control:** applying the same `target-path` overlay to the **unpatched** base (which has **no** `/__symbols__`) also returned RC=0 and produced a 108 644 B DTB. A `target-path` overlay therefore works on the frozen candidate without `-@`, in direct contrast to stock Entry 2's 166 external fixups (0 bindable). No `-@` was used anywhere in the accepted flow.

### 4.1 Slot / index-2 selection contract (explicitly UNKNOWN)

The live unit booted with `androidboot.dtbo_idx=2` (R151 grade C), and stock Entry 2 indeed sits at DTBO container index 2. If a future loader contract proves it scans a fixed slot, a custom overlay would have to be placed at index 2 to match that selection; if the loader instead matches by `qcom,msm-id`/`board-id`, no evidence supports such a match (all 9 DTBO entries have `id=rev=0`, candidate base board-id `<0 0>`, stock Entry 2 board-id `8206/0x200e`, live selected `0x200e`). **No ABL/XBL image or bootloader trace exists in Window B's permitted files; loader selection and acceptance remain UNKNOWN (grade D).** Per taskbook §3.D, Window B did **not** create or modify any DTBO container. Offline `fdtoverlay` RC=0 proves only static applicability of the overlay blob to the DTB, not that any bootloader will select or apply it.

---

## 5. [§4] Deliverable discipline / prohibitions

| Constraint | Status |
|---|---|
| Window A workspace / private logs / raw images | not accessed |
| Frozen source, accepted patch, ROUND140/154 artifacts, stock DTBO bytes | unmodified (read-only) |
| Source branch changes | none |
| Full kernel/Image build | none |
| Device / ADB / root / fastboot / recovery / partition / flash / reboot / unlock | none |
| DTBO container create/modify | none |
| Raw firmware / private paths / serial / MAC / panel IDs in report | none |

Scripts and full logs remain in `<WB15>` locally; only hashes, exact commands and derived results are published.

---

## 6. Evidence grade legend

- **A** — measured/compiled/applied in Window B this round.
- **C** — report-derived from published ROUND151/ROUND154 reports or captured local image (not re-measured from a live device).
- **D** — blocked/unknown for lack of ABL/bootloader trace; no claim made.

**Executor: WorkBuddy Window B (2号 Agent), a separate WorkBuddy chat window from Window A. END — stop after readback per taskbook §4.**
