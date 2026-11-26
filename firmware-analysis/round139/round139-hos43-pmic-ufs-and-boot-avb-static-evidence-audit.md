# ROUND139 — HOS4.3 PMIC/UFS and boot/AVB static evidence closeout

- **Executor:** WorkBuddy Agent (local executor only; not AI2)
- **Dispatched by:** AI1 (ChatGPT); taskbook `firmware-analysis/round139/AGENT_TASKBOOK_HOS43_PMIC_UFS_AND_BOOT_AVB_AUDIT.md`
- **Device:** Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- **Kernel baseline:** ACK android17-6.18.33_r00, pinned `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`; candidate tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b` (unchanged, not rebuilt)
- **Mode:** offline, read-only, existing local artifacts only. **No device access of any kind.**
- **Final outcome:** **PARTIAL — STATIC INVENTORY COMPLETE WITH INPUT LIMITATIONS**

Section 7 lists the two input gaps that force the PARTIAL rather than PASS verdict. Neither gap is in the B or D question set itself: they are (a) the three named prior parser outputs are absent from the workspace, and (b) four package images referenced by earlier rounds are not among E1's eleven copied files.

---

## 0. Result in one paragraph

Workstream B is closed at the static-declaration level. The six UFS rail consumers resolve **DIRECT**-ly to PM8150 L5 / L6 / L9 / L17 / S4 and PM8150L S8 through overlay `__fixups__` label fixups, identically in all nine DTBO entries, and the base FDT itself declares **no** UFS supply property at all (`status = "disabled"` on both nodes). Every *physical electrical input parent* of those six rails remains **UNKNOWN**: the base FDT and all nine overlays contain **zero** `vin-supply`, `vph-pwr-supply`, `vdd-s*-supply` or `input-supply` occurrences, and the only parent-like properties present are three structurally different things — 31 `parent-supply`-family occurrences that decompose exactly into 13 GCC GDSC→ARC-level edges and the five ARC provider-child edges already reconciled by ROUND51, eight self-referential `proxy-supply` occurrences, and the overlay's vendor `qcom,vccq-parent-supply` → S8. Pinned ACK declares physical parents in exactly this namespace (`vdd-s1-supply` 138 hits / 64 files, `vin-supply` 2 402 hits / 629 files) but has **zero** occurrences of any of the HOS4.3-specific vendor property names, so the HOS4.3 omission is a vendor-declaration gap, not a missing mechanism. Workstream D re-verified the boot-v2 layout byte-for-byte against the AVB footer's original-image-size field, and produced two findings that change the standing picture: the boot/recovery DTB section is a **three-FDT concatenation** (kona v2.1 / v2 / v1) plus a 173-byte vendor `MP_DATA` FDT, of which all prior rounds ever opened only the first; and `vbmeta_cust.img` **does** carry a complete signed hashtree descriptor for partition `cust` (image size 90 726 400), so ROUND64's "Algorithm NONE / no descriptors / empty shell" description is a footer-following parser artifact, not a property of the file. Which DTBO entry ABL selects, whether ABL consumes the independent `ramdisk` partition, and whether any tested HOS4.3 recovery route exists all remain **UNKNOWN / BLOCKED**.

---

## 1. Input inventory

### 1.1 Inputs actually opened (all read-only, `rb`)

| ID | Path (sanitized) | Kind | Bytes | SHA-256 |
|---|---|---|---:|---|
| E1-README | `<ws>/MatePad11_HOS43_LocalCheck_20261123_230849/REPORT_README.txt` | text | 709 | `04eb5732f56d935e91d18ab0b01e01513591b38d30a41563e3f2f5fee2000b58` |
| E1-INV | `<ws>/…/package_inventory.csv` | text | 2 495 | `29eb236ab219e5e49482f589afafad94986e1ebf3b650da764911c7e09c03480` |
| E1-SHA | `<ws>/…/copied_files_sha256.csv` | text | 1 305 | `7ea703547d404805d24284a193f4877fe12aa95b09bd2bda1bc67e6e75f1fae8` |
| E1-IMG×11 | `<ws>/…/selected_files/*.img` | binary | see Appendix B | see Appendix B |
| E5-GETPROP | `<ws>/Agent_Round2_Report/device/adb_getprop_redacted.txt` | text | 55 397 | `1947ea0d106c562417810f3710001c80ebf4f99609a1a3ebb420dd1f9ce8b061` |
| E5-PART | `<ws>/Agent_Round2_Report/device/partition_names_redacted.txt` | text | 6 266 | `d24f20c03fccbf289ee20cb714b9a86e379b85f6276ee38d18488e4ce19a5293` |
| E5-DTBASE | `<ws>/Agent_Round2_Report/device/devicetree_base_redacted.txt` | text | 4 478 | `202d2c5406d9dc186390f75a578776012a3278fb527b02d1a848b6f66bf52d49` |
| E5-DTNODES | `<ws>/Agent_Round2_Report/device/devicetree_nodes_redacted.txt` | text | 7 006 | `27a6c3cee4743faff50dc04ec2a71162a460d456663e1e2507d0670d354dcba5` |
| E5-FASTBOOT | `<ws>/Agent_Round2_Report/device/fastboot_getvar_redacted.txt` | text | 86 | `24f8d8fbd4cfb1aa6b55ceb9d2c1f49ce194c8fa5b35b5b8853e8cd546a382af` |
| E5-LIVEDTB | `<ws>/Agent_Round2_Report/device/live_dtb_status.txt` | text | 543 | `6d796daaf119e511c834ed328eeb4efce408ca91ec603c64e38543aee96546b9` |
| E7-BASE | `<round3-work>/dtb_work/boot_fdt_candidate_0.dtb` | binary | 556 524 | `df2730f3d2e9bdabad874c3ef7399534c5c6070b046c4524224aa461ba2c70f7` |
| E7-DTBO×9 | `<round3-work>/dtb_work/dtbo_entry_0..8.dtbo` | binary | 329 044–329 356 | per-entry, Appendix C |
| R13 | `<ws>/_a31/inputs/round13_pm8150_mode_drms_findings.txt` | text | 23 425 | `7c5a92eadd5188e55d50031d3e7bf1c765fa5f1eb30a7494446a9ac5112e3e51` |
| R21 | `<round21-work>/round21_first_stage_devtmpfs_and_ufs_pinctrl_overlay_audit.txt` | text | 33 544 | `3288984c04e93186c67d4f3a13259277afd9b69e3b1bbaed96df2b91a8cae084` |
| R51 | `<ws>/_a32/baseline/round51_arc_semantics.md` | text | 16 860 | `13c9e3249455bfcc30f9916c94ec03efc32a0cbe1faabed1ef3de6c1e6d23994` |
| R64-E | `<round64-work>/round64-dby-w09-hos43-final-memory-and-pm8150-input-evidence.md` | text | 8 301 | `45166938ebeef79344f464ff1afc4d4df416028f56864390aae69dc33dd8b4cb` |
| R64-F | `<round64-work>/round64-dby-w09-hos43-bootv2-ramdisk-dtbo-avb-evidence.md` | text | 11 958 | `22856b2acc3e4d08f0b47e3204f3d9e050850dfec075c25a003db0b3f31bc764` |
| R65 | `<ws>/_r65/round65-first-stage-fstab-vbmeta-cust-and-boot-tool-audit.md` | text | 16 593 | `428f5c4339dd82384b1316443477b2e9e10414a5b8e5aaf827130ad30d0050e4` |
| R137 | `<ws>/_r137/round137-hos43-abl-existing-artifact-and-trace-audit.md` | text | 19 906 | `0ced579dd9833b0a0f044a58aa7593a5ecae04c15d3704611240243882deaec6` |
| ACK-TOOL | `<ack-6.18.33-round18>/external/avb/avbtool.py` (AOSP `avbtool 1.4.0`) | tool, pre-existing | 241 922 | `da733b43019931f1dd5d62a0e856bc769acbd7034dd8d376582881f42a9a83c3` (identical to ROUND64's recorded value) |

Pinned ACK source tree inspected: `<ack-6.18.33>/common`, `git rev-parse HEAD` = `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`, `Makefile` VERSION 6 / PATCHLEVEL 18 / SUBLEVEL 33. Read-only `git grep`; nothing checked out, applied or built.

### 1.2 Declared inputs that are absent — recorded, not substituted

| Declared in taskbook §1 | Status |
|---|---|
| `<…>/logs/boot_headers.json` | **NOT FOUND** — 0 matches for the name anywhere under the workspace |
| `<…>/logs/ramdisk_inventory.json` | **NOT FOUND** — 0 matches |
| `<…>/logs/dtbo_audit.json` | **NOT FOUND** — 0 matches |
| `recovery_vbmeta.img` | **NOT among E1's eleven copied files** (E1-README: "Copied files: 11"; E1-INV lists 43 rows of which 32 are inventory-only) |
| `erecovery.img`, `erecovery_ramdisk.img`, `erecovery_vbmeta.img` | same — not copied into E1 |

Consequence: the boot/ramdisk/DTBO/AVB fields that ROUND64 sourced "from prior-round local inventory" were **re-derived in this round** from the E1 image bytes with two readers written for this audit (a boot-image header reader and an FDT/DTBO reader) plus AOSP `avbtool`. The four missing vbmeta/erecovery rows stay **NOT FOUND**; ROUND64's values for them are cited as *reused prior evidence*, not re-verified here. No firmware was re-extracted and no arbitrary directory was enumerated.

---

## 2. Workstream B — PM8150 / PM8150L physical input topology

### 2.1 B1 — UFS consumer → supply → regulator provider (**DIRECT**)

Resolved from E7 by phandle/`__symbols__`, not by quoting R21. Both consumers live in the base FDT; **every supply property is added by the overlay**, not by the base tree.

Base FDT (`boot_fdt_candidate_0.dtb`, 3 471 nodes):

| Node | phandle | `status` | supply properties in base | `power-domains` | OPP / interconnect |
|---|---|---|---|---|---|
| `/soc/ufsphy_mem@1d87000` | `119` (0x77) | `disabled` | **none** | **none** | none |
| `/soc/ufshc@1d84000` | `950` (0x3B6) | `disabled` | **none** | **none** | no `operating-points-v2`, no `required-opps`, no `interconnects`; legacy `qcom,msm-bus,*` only |

Overlay consumers — **identical in all nine entries** (signature hash `5cbe5ea8c015` over all nine, i.e. one distinct signature):

| Fragment | Target (resolved by fixup label) | Supply property | Provider label | Resolved provider path |
|---|---|---|---|---|
| `fragment@63` | `/soc/ufsphy_mem@1d87000` (`ufsphy_mem`) | `vdda-phy-supply` | `pm8150_l5` | `…/rpmh-regulator-ldoa5/regulator-pm8150-l5` |
| `fragment@63` | same | `vdda-pll-supply` | `pm8150_l9` | `…/rpmh-regulator-ldoa9/regulator-pm8150-l9` |
| `fragment@64` | `/soc/ufshc@1d84000` (`ufshc_mem`) | `vdd-hba-supply` | `ufs_phy_gdsc` | `/soc/qcom,gdsc@177004` |
| `fragment@64` | same | `vcc-supply` | `pm8150_l17` | `…/rpmh-regulator-ldoa17/regulator-pm8150-l17` |
| `fragment@64` | same | `vccq-supply` | `pm8150_l6` | `…/rpmh-regulator-ldoa6/regulator-pm8150-l6` |
| `fragment@64` | same | `qcom,vddp-ref-clk-supply` | `pm8150_l6` | same node as `vccq-supply` (one label, two fixup sites) |
| `fragment@64` | same | `vccq2-supply` | `pm8150_s4` | `…/rpmh-regulator-smpa4/regulator-pm8150-s4` |
| `fragment@64` | same | `qcom,vccq-parent-supply` | `pm8150a_s8` | `…/rpmh-regulator-smpc8/regulator-pm8150a-s8` |

So the answer to "does existing evidence map UFS consumers to L5/L6/L9/L17/S4 and PM8150L S8" is **yes, DIRECT** — five consumers on six rails, `vdd-hba` additionally on the GCC GDSC `ufs_phy_gdsc` (`/soc/qcom,gdsc@177004`, `compatible = "qcom,gdsc"`, `reg = <0x177004 0x4>`, `qcom,retain-regs`).

Two clarifications that prior rounds did not separate explicitly:

- `pm8150a_s8` is **not** a PM8150L-specific provider node. Its identity comes from the *group* node `/soc/rsc@18200000/rpmh-regulator-smpc8` (`compatible = "qcom,rpmh-vrm-regulator"`, `qcom,resource-name = "smpc8"`); the child's `regulator-name = "pm8150a_s8"` uses the legacy `pm8150a` label. This matches R13 §4.6 and is re-confirmed here.
- `qcom,vddp-ref-clk-supply` and `qcom,vccq-supply` share **one** label and **one** provider node. They are two fixup sites on the same rail, not two rails.

### 2.2 B2 — physical electrical input parent, per rail

Probe scope: the whole base FDT's 3 471 nodes and 3 281 property-bearing paths, plus all nine overlays.

| Property form | base FDT | overlay (all nine entries) | verdict |
|---|---:|---:|---|
| `vin-supply` | **0** | **0** | NOT FOUND |
| `vph-pwr-supply` | **0** | **0** | NOT FOUND |
| `vdd-s<N>-supply` | **0** | **0** | NOT FOUND |
| `input-supply` / `vs-supply` | **0** | **0** | NOT FOUND |
| `parent-supply` / `vdd_parent-supply` | 26 occurrences over 13 nodes, all `/soc/qcom,gdsc@*` | 0 | different structure (§2.3) |
| `<name>-parent-supply` (ARC provider-child form) | 5 occurrences, all on `rpmh-regulator-*lvl` groups | 0 | different structure (§2.3) |
| `proxy-supply` | 8 occurrences, all self-referential | 0 | different structure (§2.3) |
| `qcom,vccq-parent-supply` | 0 | 9 (one per entry, UFS `fragment@64`) | consumer-side, not electrical (§2.3) |

Per-rail result:

| Rail | Provider node | Explicit physical input parent | Status |
|---|---|---|---|
| PM8150 S4 (UFS VCCQ2) | `regulator-pm8150-s4` | none declared; group has only `compatible`, `qcom,resource-name = "smpa4"` | **UNKNOWN** |
| PM8150 L5 (UFS QMP VDDA-PHY) | `regulator-pm8150-l5` | none declared; group carries `qcom,regulator-type/supported-modes/mode-threshold-currents` + self-`proxy-supply` | **UNKNOWN** |
| PM8150 L6 (UFS VCCQ + VDDP REF_CLK) | `regulator-pm8150-l6` | none declared; no `proxy-supply` | **UNKNOWN** |
| PM8150 L9 (UFS QMP VDDA-PLL) | `regulator-pm8150-l9` | none declared; self-`proxy-supply` | **UNKNOWN** |
| PM8150 L17 (UFS VCC) | `regulator-pm8150-l17` | none declared; no `proxy-supply` | **UNKNOWN** |
| PM8150L S8 (UFS VCCQ parent) | `regulator-pm8150a-s8` | none declared; group `qcom,regulator-type = "pmic5-hfsmps"` | **UNKNOWN** |

**Zero rails reach DIRECT or CONDITIONAL on a physical parent.** No `vph_pwr = 3.7 V` assumption, no invented fixed regulator, no `vdd-s*-supply` was written into anything. Per-rail constraints as declared (all still *declaration*, not runtime):

| Rail | min/max µV | `qcom,init-voltage` | `qcom,init-mode` | `qcom,set` | `status` property |
|---|---|---|---|---|---|
| S4 | 1 800 000 / 1 920 000 | 1 800 000 | absent | 3 | absent |
| L5 | 880 000 / 880 000 | 880 000 | 4 | 3 | absent |
| L6 | 1 200 000 / 1 200 000 | 1 200 000 | 2 | 3 | absent |
| L9 | 1 200 000 / 1 200 000 | 1 200 000 | 4 | 3 | absent |
| L17 | 2 496 000 / 3 008 000 | 2 496 000 | 2 | 3 | absent |
| S8 | 1 200 000 / 1 400 000 | 1 200 000 | 1 | 3 | absent |

Note on `status`: **no** `status` property exists on any of the six child regulators or their group nodes. Its absence is not evidence of enablement; it only means the file does not disable them. Runtime enable state is **UNKNOWN**.

### 2.3 B2 — the three concepts, kept apart

The taskbook requires separating (1) physical electrical input parent, (2) RPMh/ARC corner or level relation, (3) proxy/consumer-side dependency. The 31 `parent-supply`-family occurrences decompose **exactly** into (2) plus a GDSC-to-(2) edge, and the remainder is (3):

**(2a) GCC GDSC → ARC level rail — 13 nodes × 2 property spellings = 26 occurrences**

| Target ARC level rail | GDSC nodes |
|---|---|
| `…/rpmh-regulator-mmcxlvl/regulator-pm8150a-s4-level` | `gdsc@ad07004`, `gdsc@ad0a004`, `gdsc@ad0b004`, `gdsc@ad08004`, `gdsc@ad09004`, `gdsc@ad0c144`, `gdsc@af03000`, `gdsc@abf0d18`, `gdsc@abf0bf8`, `gdsc@abf0d98`, `gdsc@abf0c98` (11 nodes) |
| `…/rpmh-regulator-cxlvl/regulator-pm8150-s3-level` | `gdsc@3d9106c` |
| `…/rpmh-regulator-gfxlvl/regulator-pm8150a-s1-level` | `gdsc@3d9100c` |

**(2b) ARC provider-child → ARC provider-child — 5 occurrences, matching ROUND51 §4 one-for-one**

| Property (on group) | phandle | Resolves to |
|---|---:|---|
| `rpmh-regulator-cxlvl / pm8150_s3_level-parent-supply` | 106 | `mxlvl/regulator-pm8150a-s3-level` (CX ALL → MX ALL) |
| `rpmh-regulator-cxlvl / pm8150_s3_level_ao-parent-supply` | 123 | `mxlvl/regulator-pm8150a-s3-level-ao` (CX AO → MX AO) |
| `rpmh-regulator-mmcxlvl / pm8150a_s4_level-parent-supply` | 127 | `mxlvl/regulator-pm8150a-s3-mmcx-sup-level` (MMCX ALL → MX MMCX-supply ALL) |
| `rpmh-regulator-mmcxlvl / pm8150a_s4_level_ao-parent-supply` | 123 | `mxlvl/regulator-pm8150a-s3-level-ao` (MMCX AO → MX AO) |
| `rpmh-regulator-mxlvl / pm8150a_s3_mmcx_sup_level-parent-supply` | 122 | `cxlvl/regulator-pm8150-s3-mmcx-sup-level` (MX MMCX-supply → CX MMCX-supply) |

This is a numerical reconciliation of ROUND51, not a new discovery: ROUND51 §4 listed exactly these five edges and said the complete graph remains uncensused; this round's whole-FDT count returns 31 and no sixth provider-child edge exists, so the "at least five" is now "exactly five of this form, plus 26 GDSC-form".

**(3) proxy / consumer-side — 8 `proxy-supply` occurrences, every one self-referential**

`rpmh-regulator-ldoa5` → `regulator-pm8150-l5` (124); `ldoa9` → `regulator-pm8150-l9` (125); `ldoa14` → `regulator-pm8150-l14` (126); `ldoc11` → `regulator-pm8150a-l11` (128); `cxlvl` → `regulator-pm8150-s3-mmcx-sup-level` (122); `mmcxlvl` → `regulator-pm8150a-s4-level` (105); `/soc/qcom,gdsc@af03000` → itself (113); `/soc/refgen-regulator@88e7000` → itself (178). Every site points into its own child set. `qcom,proxy-consumer-current` appears on four nodes — L5 (100 000 µA), L9 (100 000 µA), L14, and `pm8150a-l11`; `qcom,proxy-consumer-enable` appears on the eight `proxy-supply` sites plus `/soc/qcom,gdsc@af03000` and `/soc/refgen-regulator@88e7000`. Both properties are vendor-only (§2.5) and neither is consumed by the pinned tree.

**Naming traps that must not be crossed:**

- `regulator-pm8150a-s4-level` (ARC, `qcom,resource-name = "mmcx.lvl"`) is **not** `regulator-pm8150-s4` (SMPS4 VRM, `qcom,resource-name = "smpa4"`, the UFS VCCQ2 provider). One is a corner interface, the other is a rail. The `s4` token in the level regulator's name is a label, not a resource identity.
- `regulator-pm8150-s3-level` and `regulator-pm8150a-s3-level` are ARC `cx.lvl` / `mx.lvl` interfaces. There is **no** `rpmh-regulator-smpa3` group in this FDT, so no VRM S3 exists to be confused with.
- `qcom,vccq-parent-supply` → `pm8150a_s8` is a consumer-declared parent rail. It is neither an electrical `vin` of L6 nor an ARC corner.

### 2.4 B3 — UFS performance-domain / OPP / interconnect evidence

| Question | HOS4.3 static answer | Basis |
|---|---|---|
| `power-domains` on `/soc/ufshc@1d84000` | **absent** | E7 property list |
| `power-domains` on `/soc/ufsphy_mem@1d87000` | **absent** | E7 property list |
| `operating-points-v2` / `required-opps` | **absent** on both nodes; no `ufs_opp_table`-like node exists | 77 OPP-table candidates in the FDT were enumerated; none is referenced by a UFS node |
| RPMh power-domain provider referenced by UFS | **none** | whole-FDT `power-domains` census = **1** consumer total, and it is `/soc/qcom,mdss_rotator@aea8800` → `/soc/qcom,mdss_mdp@ae00000`, unrelated to UFS |
| RPMh ARC/corner providers that exist | `mxlvl` (`mx.lvl`), `cxlvl` (`cx.lvl`), `mmcxlvl` (`mmcx.lvl`), `lmx.lvl`, `lcx.lvl`, `gfx.lvl`, `ebi.lvl` — 7 groups, all `compatible = "qcom,rpmh-arc-regulator"`, within 47 `rpmh-regulator-*` provider groups (105 nodes under that prefix) |
| Consumer→domain association for UFS | **UNKNOWN / none declared** | follows from the absent `power-domains` |
| CMD DB / ARC / proxy relation for UFS | only the GDSC→`mmcx.lvl` edge through `ufs_phy_gdsc`'s *consumers*, not through UFS itself. `ufs_phy_gdsc` has **no** `parent-supply` | `gdsc@177004` property list is only `compatible`, `reg`, `regulator-name`, `qcom,retain-regs`, `phandle` |
| ICC | legacy `qcom,msm-bus,name = "ufshc_mem"`, `num-cases = 26`, `num-paths = 2`, `vectors-KBps`, `bus-vector-names`; **no** `interconnects` | E7 |
| Clocks / resets | 9 clocks (`gcc` + `rpmhcc` providers), `resets = <23 33>` / `core_reset`, two pinctrl states `dev-reset-assert` / `dev-reset-deassert` | E7; unchanged by every overlay |

Comparison with pinned ACK (`8ad08f75`):

- `sm8250.dtsi:2519` — `power-domains = <&gcc UFS_PHY_GDSC>` on `ufs_mem_hc`; `sm8250.dtsi:2593` — the same on `ufs_mem_phy`. ACK therefore *does* attach UFS to a power domain; HOS4.3 attaches it to none.
- `gcc-sm8250.c:3256-3262` — `ufs_phy_gdsc` has `.gdscr = 0x77004`, `pwrsts = PWRSTS_OFF_ON`, and **no `.parent`** and no `cxpd`. So the ACK UFS domain chain terminates at the GDSC; there is no ACK-side MMCX edge for UFS either.
- `sm8250.dtsi:2542, 2544, 2550-2577` — `operating-points-v2 = <&ufs_opp_table>`; `interconnects = <&aggre1_noc MASTER_UFS_MEM …>, <&gem_noc …>` with names `ufs-ddr`, `cpu-ufs`; `opp-37500000 → required-opps = <&rpmhpd_opp_low_svs>` and `opp-300000000 → required-opps = <&rpmhpd_opp_nom>` (`:2562`, `:2574`).
- `rpmhpd.c:126-130` — `mmcx` descriptor: `.peer = &mmcx_ao`, `.res_name = "mmcx.lvl"`, **no `.parent`**. `rpmhpd.c:90-95` — `cx_w_mx_parent`: `.parent = &mx.pd`. `rpmhpd.c:465-477` — `sm8250_rpmhpds[]` maps `RPMHPD_MMCX = &mmcx` and `RPMHPD_CX = &cx_w_mx_parent`. A `mmcx_w_cx_parent` descriptor exists at `:140-144` but SM8250 does not select it. This is exactly the taskbook's stated ACK behaviour, and it is now verified at file:line rather than restated.
- `ufshcd-pltfrm.c:176-195` — `ufshcd_parse_regulator_info()` populates **only** `vdd-hba`, `vcc`, `vccq`, `vccq2`. `vdd-hba` alone is marked fixed-regulator. No code path in the pinned tree reads `qcom,vccq-parent-supply` or `qcom,vddp-ref-clk-supply`.

Numeric corner labels were **not** treated as runtime equivalence: matching `LOW_SVS` / `NOM` names between HOS child `qcom,init-mode` integers and ACK `opp-level` symbols is not claimed anywhere in this report.

### 2.5 B4 — exact differences between HOS4.3 static declarations and pinned ACK support

`git grep -c -F` over the pinned `common/` tree:

| Property / symbol | HOS4.3 FDT | pinned ACK occurrences | Meaning |
|---|---|---|---|
| `qcom,rpmh-vrm-regulator` (per-group compatible) | **40** of the 47 `rpmh-regulator-*` provider groups | **0 files, 0 hits** | pinned ACK binds a single per-PMIC node `compatible = "qcom,pm8150-rpmh-regulators"` / `"qcom,pm8150l-rpmh-regulators"` with `regulator-N` children (`sm8250-xiaomi-elish-common.dtsi:231`, `:364`) |
| `qcom,rpmh-arc-regulator` | **7** groups (`mxlvl`, `cxlvl`, `mmcxlvl`, `lmx.lvl`, `lcx.lvl`, `gfx.lvl`, `ebi.lvl`) | **0 / 0** | ACK models ARC corners as GenPDs through `qcom,sm8250-rpmhpd`, not as regulators |
| `qcom,regulator-type` | 34 nodes (pmic5-ldo / pmic5-hfsmps / pmic5-bob) | **0 / 0** | vendor-only |
| `qcom,supported-modes` | 31 nodes (`<2 4>` LDO, `<1 3>` SMPS, `<0 2 4>` BOB) | **0 / 0** | vendor-only; upstream equivalent is `regulator-allowed-modes` |
| `qcom,mode-threshold-currents` | 31 nodes (30 000 / 10 000 / 200 000 µA) | **0 / 0** | vendor-only |
| `qcom,init-mode` | 1/2/4 per rail | **0 / 0** | vendor-only; upstream is `regulator-initial-mode` (`sm8250-xiaomi-elish-common.dtsi:297`) |
| `proxy-supply` | 8 self-referential sites | **0 / 0** | the property has no consumer at all in the pinned tree — the `proxy-consumer` mechanism is absent, not merely unmatched |
| `qcom,vccq-parent` | 1 site (UFS) | **0 / 0** | downstream-only |
| `vdd-hba-supply` | 1 (overlay) | 21 files | shared with upstream |
| `vdd-s1-supply` | 0 | 138 hits / 64 files | upstream board files **do** declare physical parents using the exact property HOS omits |
| `vin-supply` | 0 | 2 402 hits / 629 files | same conclusion |

The last three rows are the load-bearing ones for B2: the electrical-parent *vocabulary* is fully present and heavily used in pinned ACK, so HOS4.3's silence is a vendor declaration gap, not a limitation of the format.

There is also a R13 §3 claim that needs a small correction in scope. R13 reported `proxy-supply` as "existing ROUND11 finding, unchanged" and treated it as a working mechanism; against the pinned tree there is **no** consumer for it at all, so in an ACK build these eight properties are inert metadata. This does not change R13's rail census, only the implied semantics.

### 2.6 ROUND64 reconciliation

ROUND64 Phase E output B reported `BLOCKED — PM8150 physical parent not established`, with "no `vdd-s1..s10-supply`, `vin-supply`, or `vph-pwr-supply` was found in the inspected stock FDT scope". This round **reproduces that result independently** and must not be read as a new successful discovery: the count is still zero, and the conclusion is still UNKNOWN per rail. What this round adds is only (a) the exact decomposition of the 31 parent-like occurrences into three non-electrical structures, (b) the file:line ACK side showing the vocabulary is available upstream, and (c) the smallest missing artifact per rail below. ROUND64's actionable request — a board-specific PMIC power tree or schematic page for DBY-W09 naming the physical input of these six rails — is still the only thing that would close it.

### 2.7 Smallest missing authoritative artifact, per rail

| Rail | Smallest artifact that would decide it |
|---|---|
| L5, L9 | vendor board DTS (or schematic page) showing `vdd-l3-l4-l5-l18`-class input grouping for DBY-W09; a same-SoC reference board's grouping is a *hint*, not evidence |
| L6 | board declaration of the S8/other input for L6 (note L6 and L9 are commonly on one input domain in reference boards — a hint only) |
| L17 | board declaration of the buck feeding L13/L16/L17 group |
| S4 | board `vdd-s4-supply` declaration |
| S8 | board `vdd-s8-supply` declaration |
| Any rail, runtime | a PMIC register / RPMh trace capture; **out of scope and not authorized** |

One artifact covers all six at once: the **HOS4.3 board DTS/DTBO source**, or a **post-ABL `/sys/firmware/fdt`** capture (which ROUND2 attempted and was denied). Neither exists in the corpus.

---

## 3. Workstream D — boot-v2 / ramdisk / DTBO / AVB / recovery

### 3.1 D1 — boot layout re-verified from bytes (**DIRECT**)

| Field | boot.img | recovery.img | ramdisk.img | recovery_ramdisk.img |
|---|---|---|---|---|
| magic / header version | `ANDROID!` / **2** | `ANDROID!` / **2** | `ANDROID!` / **0** | `ANDROID!` / **0** |
| page size | 4 096 | 4 096 | 2 048 | 2 048 |
| kernel size @ offset | 22 264 379 @ 4 096 | 22 254 704 @ 4 096 | 0 | 0 |
| ramdisk size @ offset | 519 986 @ 22 269 952 | 519 986 @ 22 261 760 | 1 322 962 @ 2 048 | 29 099 169 @ 2 048 |
| second stage | 0 | 0 | 0 | 0 |
| `recovery_dtbo` size @ offset | 0 / 0 | **25 165 824 @ 22 781 952** | — | — |
| DTB size @ offset | **1 664 243 @ 22 790 144** | **1 664 243 @ 47 947 776** | — | — |
| payload end | **24 457 216** | **49 614 848** | **1 325 056** | **29 102 080** |
| header_size field | 1 660 | 1 660 | (n/a, v0) | (n/a, v0) |
| os_version decode | Android 11 / patch month 2020-11 (`369 099 083`) | identical | — | — |

Every payload end matches the AVB footer's `original image size` for the same file (§3.2) **exactly**, which is an independent two-parser cross-check on five numbers.

**Finding D1-a (new): the DTB section is a three-FDT concatenation plus a 173-byte vendor FDT.**

The 1 664 243-byte DTB region of `boot.img` and of `recovery.img` (same total size, different bytes overall) begins with three complete FDT blobs and ends with a fourth:

| # | offset | totalsize | nodes | `model` | `qcom,msm-id` | sha256 (12) |
|---:|---:|---:|---:|---|---|---|
| 0 | 0 | 556 524 | 3 471 | `… kona v2.1 SoC` | `<356 131073>` | `df2730f3d2e9` |
| 1 | 556 524 | 556 520 | 3 471 | `… kona v2 SoC` | `<356 131072>` | `f3dcba83e73f` |
| 2 | 1 113 044 | 551 026 | 3 433 | `… kona v1 SoC` | `<356 65536>` | `6cda673986bf` |
| 3 | 1 664 070 | 173 | 1 | — | — | boot `f06fb36d7847` / recovery `8f63b9bfabe5` |

`556 524 + 556 520 + 551 026 + 173 = 1 664 243` exactly; there are no trailing bytes. All four also carry `qcom,board-id = <0 0>` — the base tree is a pre-ABL template in all variants, consistent with ROUND64.

FDT #3 is not a device tree in the usual sense: it has only a root node carrying `qcom,rtic-id = <1>` and a `MP_DATA` vendor blob, and its last four bytes differ between `boot.img` and `recovery.img`. It is the tail of the unsigned payload and is counted inside avbtool's `original image size`.

Consequence for every earlier round: E7's `boot_fdt_candidate_0.dtb` (556 524 B, `df2730f3…`) is **byte-identical to FDT #0 only**. Everything R13/R21/R24/R64/R65/R138 concluded about "the base FDT" describes the **v2.1 SoC variant**. That happens to be the variant matching this device's stated platform (`kona v2.1`), so no earlier conclusion is invalidated — but "the base FDT" should be read as "base FDT variant v2.1, FDT #0 of three", and the v2 / v1 variants (3 433–3 471 nodes) have never been opened in this project. The 38-node difference between FDT #0 and FDT #2 is not analyzed here.

**Finding D1-b: the independent ramdisk and the embedded stock ramdisk are distinct objects.**

| | embedded in boot.img | standalone `ramdisk.img` |
|---|---|---|
| section size | 519 986 | 1 322 962 |
| magic | gzip `1f8b08` | gzip `1f8b08` |
| decompressed | 1 093 888 B, CPIO newc, **5** entries | 2 884 352 B, CPIO newc, **17** entries |
| identical? | **no** (neither the compressed nor the decompressed content matches) | |

The device also exposes a **separate `ramdisk` partition** — `ramdisk -> /dev/block/sda22` (E5-PART), distinct from `boot -> /dev/block/sde9`. Existence of the partition is DIRECT; whether ABL *uses* it is §3.3.

**DTBO container (DIRECT):** magic `0xD7B7AB1E`, `total_size` 2 963 810, header 32 B, entry size 32 B, `entry_count = 9`, `entries_offset = 32`, `page_size = 4096`, `version = 0`, file 25 165 824 B. Entry table:

| entry | dtb size | dtb offset | entry | dtb size | dtb offset |
|---:|---:|---:|---:|---:|---:|
| 0 | 329 044 | 320 | 5 | 329 356 | 1 646 394 |
| 1 | 329 352 | 329 364 | 6 | 329 356 | 1 975 750 |
| 2 | 329 240 | 658 716 | 7 | 329 352 | 2 305 106 |
| 3 | 329 098 | 987 956 | 8 | 329 352 | 2 634 458 |
| 4 | 329 340 | 1 317 054 | | | |

`total_size` 2 963 810 equals the AVB footer's original-image-size for `dtbo.img`, and the last entry ends exactly at 2 963 810.

**Finding D1-c (new): `recovery.img` embeds a byte-identical copy of the standalone `dtbo.img`.** The `recovery_dtbo` section at offset 22 781 952, length 25 165 824, hashes to `51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c` — the same value as `dtbo.img` itself (full-file byte comparison, not just hash). `boot.img` has `recovery_dtbo_size = 0`. This is an observation about the package, not a claim about which copy ABL reads.

### 3.2 D2 — AVB chain and the `vbmeta_cust` anomaly (**DIRECT, one prior claim corrected**)

Parser of record: AOSP `avbtool 1.4.0` (`external/avb/avbtool.py`, sha256 `da733b43…`), read-only `info_image`, output filtered so that no key, key hash, signature, salt, or root digest is reproduced. No tool was installed.

| Image | bytes | avbtool exit | footer | original image size | release string | algorithm | descriptors → targets |
|---|---:|---:|---|---:|---|---|---|
| boot.img | 100 663 296 | 0 | PRESENT | 24 457 216 | 1.1.0 | SHA256_RSA2048 | Hash → boot |
| ramdisk.img | 2 097 152 | 0 | PRESENT | 1 325 056 | 1.2.0 | SHA256_RSA2048 | Hash → ramdisk |
| dtbo.img | 25 165 824 | 0 | PRESENT | 2 963 810 | 1.1.0 | SHA256_RSA2048 | Hash → dtbo |
| recovery.img | 100 663 296 | 0 | PRESENT | 49 614 848 | 1.1.0 | SHA256_RSA2048 | Hash → recovery |
| recovery_ramdisk.img | 33 554 432 | 0 | PRESENT | 29 102 080 | 1.1.0 | SHA256_RSA2048 | Hash → recovery_ramdisk |
| vbmeta.img | 1 048 576 | 0 | PRESENT | n/a | 1.1.0 | SHA256_RSA2048 | **Chain →** boot, ramdisk, vbmeta_system, vbmeta_vendor, vbmeta_odm, eng_vendor, eng_system, dtbo, version, vbmeta_hw_product, preload, preas, preavs, vbmeta_cust (14) |
| vbmeta_system.img | 1 048 576 | 0 | PRESENT | n/a | 1.2.0 | SHA256_RSA2048 | Hashtree → system |
| vbmeta_vendor.img | 1 048 576 | 0 | PRESENT | n/a | 1.1.0 | SHA256_RSA2048 | Hashtree → vendor |
| vbmeta_odm.img | 1 048 576 | 0 | PRESENT | n/a | 1.1.0 | SHA256_RSA2048 | Hashtree → odm |
| vbmeta_hw_product.img | 1 048 576 | 0 | PRESENT | n/a | 1.2.0 | SHA256_RSA2048 | Hashtree → hw_product |
| recovery_vbmeta.img, erecovery*.img | — | — | **NOT IN E1** | — | — | — | not verified this round |

Hashtree sizes as declared (image size / tree size / FEC size): system 3 525 328 896 / 27 766 784 / 28 090 368; vendor 947 318 784 / 7 467 008 / 7 553 024; odm 635 641 856 / 5 013 504 / 5 070 848; hw_product 2 369 454 080 / 18 665 472 / 18 882 560; **cust 90 726 400 / 724 992 / 729 088**. All descriptors use `sha1` with 4096/4096 blocks and FEC 2. Their sum (7 568 470 016) exceeds the declared `super.img` size 7 114 729 004 by 453 741 012 B; R64 already flagged `hashtree image_size` semantics as ROUND19 U-8 and did not re-litigate it, and this round does not either — the arithmetic is recorded, the semantics stay **UNKNOWN**.

Chain coverage answers: boot and ramdisk are covered by the root `vbmeta.img` chain; `dtbo` is covered **twice** (root chain + its own footer hash descriptor); `cust` is covered by a chain descriptor in root vbmeta plus a hashtree descriptor inside `vbmeta_cust.img` (§below).

Rollback / key metadata (presence only, values not published): `rollback_index` field is zero and `rollback_index_location` is 0 in all seven header blocks; `flags` = 0 everywhere (no disable-verity / verification-disabled flag asserted); a 520-byte RSA-2048 public key is embedded in each; `public_key_metadata` size is 0 in all seven (no key metadata blob).

**The `vbmeta_cust` anomaly, re-checked**

Byte-level structure of the 1 048 576-byte file:

- `AVB0` at offset **0** — exactly one occurrence in the file.
- `AVBf` at offset **1 048 512** (= file size − 64) — exactly one occurrence.
- Footer: version 1.0, `image_size` 1 048 576, `original_image_size` **10 375 168**, `vbmeta_offset` **10 375 168**, `vbmeta_size` **1 344**.
- Header at offset 0 (fields read directly, no key material): `required libavb 1.0`, header 256, auth 320, aux 768, **`algorithm = SHA256_RSA2048`**, descriptors 224, `rollback_index` 0, `flags` 0, `rollback_index_location` 0, release string **`'avbtool 1.2.0'`**.
- `256 + 320 + 768 = 1 344` — i.e. the footer's `vbmeta_size` equals the complete header+auth+aux length of the blob at offset 0. There is no fourth 1 344-byte vbmeta anywhere in the file.

Because the footer is present, `avbtool info_image` follows it to offset 10 375 168 — past EOF — and reports `Algorithm: NONE`, release `'avbtool 1.4.0'`, no descriptors. **That output describes zero bytes, not the file.** When the same, unmodified parser is pointed at the 1 568-byte blob at offset 0 (a read-only byte-range copy in a temp directory; original untouched, no footer repaired, no descriptor edited, copy deleted), it reports:

```
Header 256 / Authentication 320 / Auxiliary 768
Algorithm: SHA256_RSA2048        Release String: 'avbtool 1.2.0'
Hashtree descriptor:  Partition Name: cust
  Image Size 90726400  Tree Offset 90726400  Tree Size 724992
  Data/Hash Block 4096/4096  FEC num roots 2  FEC offset 91451392  FEC Size 729088
  Hash Algorithm sha1  Flags 0
```

So:

| Claim | Status |
|---|---|
| `vbmeta_cust.img` contains a valid signed vbmeta blob at offset 0 with a hashtree descriptor for `cust` | **DIRECT** (avbtool 1.4.0, and independently ROUND65's citation of ROUND19's parser) |
| ROUND64's "the referenced vbmeta is an empty shell; Algorithm NONE; no descriptors; coverage for `cust` **UNKNOWN**" | **CORRECTED** — that is a footer-following artifact; coverage for `cust` is DIRECT, image size 90 726 400 |
| Why the footer points to 10 375 168 (> the 1 MiB file) | **UNKNOWN** — three candidate explanations (malformed file / truncated extraction of a 10 376 576-byte object / foreign or template footer) can be distinguished only by the source package's own `vbmeta_cust.img` or the partition's true size; none is available locally, and no explanation is selected here |
| The file is 1 MiB while its footer describes a ~9.9 MiB object | **DIRECT** (arithmetic: 10 375 168 + 1 344 + 64 = 10 376 576, i.e. **9 328 000 B** more than the 1 048 576-byte file) |

Note that ROUND65 had already reconciled these two structures and left the anomaly UNKNOWN; this round's contribution is the independent avbtool confirmation of the offset-0 descriptor (replacing the self-written parser as the source of that fact) and the `1 344 = 256+320+768` identity that explains why the footer looks self-consistent while describing the wrong object.

No signing, verification-key substitution, vbmeta regeneration, disable-verity change, footer repair, descriptor edit or image patch was performed. `cust -> /dev/block/dm-0` and `hw_product -> /dev/block/dm-1` in E5-PART confirm both are logical (super) partitions, consistent with a hashtree-descriptor model but not proof of it.

### 3.3 D3 — ABL and partition-consumption limits

| Question | State | Basis |
|---|---|---|
| Does HOS4.3 ABL accept a replacement boot-v2 DTB? | **UNKNOWN** | no ABL binary, no ABL version, no handoff trace; R137 `BLOCKED — ABL ARTIFACT/TRACE NOT PRESENT` |
| Does ABL consume the independent `ramdisk` partition? | **UNKNOWN** (partition exists = DIRECT; consumption = UNKNOWN) | `ramdisk -> sda22` in E5-PART; embedded 519 986-byte ramdisk also present in `boot.img` |
| Which DTBO entry is selected? | **CONDITIONAL — entry 2 is the strongest available candidate** | `ro.boot.dtbo_idx=[2]` published by the bootloader (E5-GETPROP, line 753); entry 2 = board-id 8206 (`0x200E`) / `DBY_W09_VD` (ROUND138). Conditional on "device dtbo partition == package dtbo.img", which has no readback hash |
| Does ABL apply a `/rootparam` overlay, and how? | **UNKNOWN** — the *DTBO* contains a `/rootparam` fragment in all nine entries (DIRECT, ROUND138), but ABL's application of it is unobserved | ROUND138 §Task B; R137 §5.2 |
| Does boot preserve or replace the embedded stock ramdisk? | **UNKNOWN** | both an embedded (5-entry) and a standalone (17-entry) ramdisk exist; no boot trace |

ABL version / policy is not inferable from XBL, TZ or the UEFI Secure App, and nothing in this corpus substitutes for it. `abl -> /dev/block/sde6` exists as a partition node (E5-PART) and `xbl -> /dev/block/sdb1`; no image of either was pulled and none was read.

**New, mildly useful for D3:** the package contains **two** possible DTBO sources for a recovery path — the standalone `dtbo.img` and the byte-identical `recovery_dtbo` section inside `recovery.img` (§3.1 D1-c). If ABL's recovery path reads the latter, the two are interchangeable *in this package*; that is a package property, not evidence of ABL behaviour.

### 3.4 D4 — recovery / reversibility

| Item | State |
|---|---|
| Original partition **backup images** available | **11 stock package images** (boot, dtbo, ramdisk, recovery, recovery_ramdisk + 6 vbmeta). These are **package** images, not device partition dumps — nothing in the corpus is a readback of this tablet's own `boot`/`dtbo`/`ramdisk`/`vbmeta` |
| Known partition sizes | only package-declared sizes (E1-INV, 43 rows); device-side sizes **not captured** — no `blockdev --getsize64`, no `fastboot getvar partition-size` |
| Known image hashes | all 11 verified byte-for-byte against E1-SHA this round (§3.1 table + Appendix) |
| Documented recovery/restore route | a same-device **public HOS4.2** project is cited (`<ws>/_pkg_v2/MatePad11_DBY-W09_预移植研究报告_2026-11-23.md:10`) as recording header-v2 `boot`, an independent `ramdisk` partition, a DTBO `/rootparam` requirement **and `fastboot boot` being unusable**. This is a **HOS4.2 third-party record, not verified on this HOS4.3 tablet** |
| Evidence about `fastboot boot` refusal / recovery entry on *this* device | **NOT FOUND** — `fastboot_getvar_redacted.txt` reads `NOT AVAILABLE: device is in Android adb mode, not fastboot. No reboot was issued.` (86 B). No fastboot session has ever been captured on this device |
| Live FDT / `/sys/firmware/fdt` | **denied** in ROUND2 (`live_dtb_status.txt`: `Permission denied`; `live.dtb.sha256`: `NOT AVAILABLE`) |
| Prohibited-partition backups | E1-README explicitly excludes persist, modemst1/2, fsg, fsc, oeminfo, userdata, FRP, metadata; `super` (7 114 729 004 B), `preload`, `cache` are inventory-only and were not copied |
| **Recovery readiness** | **BLOCKED** — no tested HOS4.3 recovery route and no complete original-partition backup set |

Two consequences worth stating plainly: (a) restoring from E1 images presupposes that this tablet's partitions equal the package's, which ROUND138 already found doubtful (`ro.boot.dtbo_idx=2` vs the entry-8 baseline; live `/rootparam` missing `qcom,product_name`); (b) the only *documented* route is a third-party HOS4.2 record whose central warning — `fastboot boot` unusable — removes the least destructive trial mechanism if it also holds on HOS4.3.

### 3.5 D5 — matrix summary

| Item | Label |
|---|---|
| boot-v2 header/version/page/offsets/sizes | **DIRECT** |
| embedded vs standalone ramdisk distinction | **DIRECT** (sizes, content hash, CPIO entry counts) |
| DTBO container version/count/table | **DIRECT** |
| three-FDT + MP_DATA composition of the DTB section | **DIRECT** |
| `recovery.img` `recovery_dtbo` == `dtbo.img` | **DIRECT** |
| AVB footer presence, original sizes, descriptor class→target | **DIRECT** |
| rollback-index/key-metadata presence | **DIRECT** (all zero / absent; values not published) |
| `vbmeta_cust` offset-0 hashtree descriptor for `cust` | **DIRECT** |
| `vbmeta_cust` footer provenance | **UNKNOWN** |
| `recovery_vbmeta.img`, `erecovery*` descriptors | **NOT FOUND** in E1 |
| ABL DTB acceptance / ramdisk consumption / rootparam application | **UNKNOWN** |
| ABL-selected DTBO entry | **CONDITIONAL (entry 2)** |
| HOS4.3 recovery route | **BLOCKED** |

---

## 4. Corrections and inconsistencies carried forward

| # | Item | Disposition |
|---|---|---|
| 1 | ROUND64-F: `vbmeta_cust` "embedded blob = Algorithm NONE, no descriptors; coverage UNKNOWN" | **Corrected** — §3.2. The blob at offset 0 is a valid SHA256_RSA2048 vbmeta with one `cust` hashtree descriptor (image size 90 726 400). ROUND64's footer facts stand; its descriptor-coverage conclusion does not. |
| 2 | R13 §3: `proxy-supply` described as an existing working mechanism | **Scope-limited** — the pinned ACK tree contains zero `proxy-supply` / `proxy-consumer` consumers, so in an ACK build the eight HOS sites are inert. R13's rail census is unaffected. |
| 3 | R64-E: base FDT `/reserved-memory` "34 children" | **Stale** — the file has **37** direct children (this round: 37; ROUND24: 37; ROUND138: 37). 34 appears to be an ROUND19-era number. The 39-vs-37 discussion remains ROUND138's, and is not reopened. |
| 4 | "the base FDT" (all rounds) | **Now qualified** — E7's file is FDT #0 (kona v2.1) of a three-FDT section. ROUND138's entry-2/entry-8 comparison, R13's rail census and R21's UFS map are all v2.1-only statements. |
| 5 | R21 §3.4 "the base regulator nodes do NOT carry an explicit `parent-supply`" | **Confirmed and sharpened** — for the six UFS rails, true; but 13 *other* nodes (`qcom,gdsc@*`) do carry `parent-supply`/`vdd_parent-supply`, and five ARC provider-child edges exist. R21's sentence is correct only within the UFS rail scope. |
| 6 | R64-F: AVB table had 15 rows including erecovery | **Input-limited here** — E1 has 11; the four erecovery/recovery_vbmeta rows are quoted from R64, not re-verified. |
| 7 | ROUND65 vs ROUND64 on `vbmeta_cust` | ROUND65 already reconciled the two structures and left the anomaly UNKNOWN; this round confirms ROUND65's offset-0 reading with the trusted parser. No conflict remains between them. |

---

## 5. What this round actually closed

1. **UFS rail consumers are settled, statically.** Eight consumer→provider edges across `fragment@63`/`fragment@64`, identical in all nine DTBO entries, resolving to L5 / L9 / GDSC / L17 / L6 / L6 / S4 / S8. The base FDT contributes **no** supply property, so any board DTS replacement must either reproduce these overlay edges or deliberately deviate — silently dropping them removes `vccq` and `vddp-ref-clk` (both L6) and `vccq2` (S4).
2. **The parent-edge census is arithmetically closed for this FDT.** 31 parent-like occurrences = 26 GDSC-form (13 nodes × 2 spellings) + 5 ARC provider-child edges (exactly ROUND51's five). Zero electrical `vin`/`vph-pwr`/`vdd-s*` parents exist for the six rails.
3. **HOS4.3 vs pinned ACK divergence is now enumerated at file:line**, including the hard fact that ACK has *no* consumer for `qcom,regulator-type`, `qcom,supported-modes`, `qcom,init-mode`, `proxy-supply`, `qcom,vccq-parent` — and that ACK does attach UFS to `UFS_PHY_GDSC` (`sm8250.dtsi:2519`, `:2593`) while HOS attaches it to nothing.
4. **Boot/ramdisk/DTBO/AVB layout is independently re-derived and cross-checked** against avbtool's `original image size` on five numbers, with the three-FDT composition and the `recovery_dtbo == dtbo.img` identity established.
5. **The `vbmeta_cust` "empty shell" is retired**; `cust` coverage is DIRECT, and the residual question is narrowed from "does cust have descriptors" to "why does the footer describe a 10 376 576-byte object".

## 6. What still needs an authoritative external artifact or explicit user-authorized device evidence

| Open item | Smallest sufficient artifact | Authorization needed |
|---|---|---|
| Physical input parent of L5/L6/L9/L17/S4/S8 | HOS4.3 board DTS/DTBO source, or a DBY-W09 schematic page naming those rails' inputs | none for the source if the vendor DTS is obtained; schematic needs a user-held document |
| Post-ABL final FDT (memory handoff, live reserved-memory identity/values) | `cat /sys/firmware/fdt` with sufficient privilege, plus statement of capture route | **explicit device authorization** — ROUND2 was denied, and the taskbook explicitly withholds it |
| ABL DTB acceptance / selected DTBO entry / ramdisk consumption / rootparam application | ABL binary or version string, or a bootloader trace | **explicit device or firmware authorization** |
| `vbmeta_cust` footer provenance | the source package's own `vbmeta_cust.img`, or the `vbmeta_cust` partition's true size | none locally available |
| Tested HOS4.3 recovery route | a documented + executed restore on this tablet | **explicit device authorization, and not before a complete backup set exists** |

**No first-boot readiness is declared by this report.** Static inspection cannot establish it, and the taskbook forbids it.

---

## 7. Why PARTIAL rather than PASS

- Three taskbook-named inputs are absent (`logs/boot_headers.json`, `logs/ramdisk_inventory.json`, `logs/dtbo_audit.json`); their content was re-derived from the E1 image bytes with readers written for this audit plus AOSP `avbtool`, and the re-derivation agrees with ROUND64 on every overlapping number — but the *declared* artifacts themselves were not available.
- Four images referenced by ROUND64's AVB table are not among E1's eleven copied files, so `recovery_vbmeta.img` and the three `erecovery*` rows remain unverified here.
- Both are **input** limitations, not analysis gaps: every B and D question in the taskbook received a labeled answer (DIRECT / CONDITIONAL / UNKNOWN / NOT FOUND), and the two workstreams' open items are open for reasons that no further local static work can change.

---

## 8. Limits observed

```
device_connected        = false        adb_invoked          = false
fastboot_invoked        = false        recovery_touched     = false
usb_or_serial_used      = false        rebooted             = false
abl_partition_read      = false        /sys/firmware/* read = false
privilege_escalation    = false        root_attempted       = false
firmware_downloaded     = false        firmware_reextracted = false
tools_installed         = false        images_modified      = false
signed / avb_modified   = false        flashed              = false
source_modified         = false        compiled / built     = false
round135_rerun          = false
```

- Only the §1.1 paths were opened. No drive-wide search, no personal-directory enumeration, no cloud access.
- Every E7 and E1 file was opened `rb`; no file was renamed, rewritten, repaired or re-extracted. The one temporary write was a 1 568-byte diagnostic copy of a byte range of `vbmeta_cust.img` into a temp directory, used solely to point the same `avbtool` at the file's own offset-0 blob; it was deleted and no original byte was altered.
- No key material, key hash, signature, salt, image/root digest, rollback-index value, serial number, MAC address, IMEI or user identifier is reproduced. Partition and image SHA-256 values published here are firmware digests already published in prior accepted rounds.
- No report content asserts runtime regulator state, runtime corner selection, ABL behaviour, or boot success.

---

## Appendix A — Evidence paths for each DIRECT claim

**B1 (consumer→provider)** — E7 `boot_fdt_candidate_0.dtb`: `/soc/ufsphy_mem@1d87000` (phandle 119, `status="disabled"`, property set = `reg`, `reg-names`, `#phy-cells`, `lanes-per-direction`, `clock-names`, `clocks`, `status`, `phandle`), `/soc/ufshc@1d84000` (phandle 950, `compatible="qcom,ufshc"`, `status="disabled"`, no `*-supply`, no `power-domains`, no `interconnects`). Overlay: each `dtbo_entry_*` → `/__fixups__` entries `/fragment@63/__overlay__:vdda-phy-supply:0` → `pm8150_l5`, `/fragment@63/__overlay__:vdda-pll-supply:0` → `pm8150_l9`, `/fragment@64/__overlay__:vdd-hba-supply:0` → `ufs_phy_gdsc`, `:vcc-supply:0` → `pm8150_l17`, `:vccq-supply:0` → `pm8150_l6`, `:qcom,vddp-ref-clk-supply:0` → `pm8150_l6`, `:vccq2-supply:0` → `pm8150_s4`, `:qcom,vccq-parent-supply:0` → `pm8150a_s8`; labels resolved through `/__symbols__`.

**B2 (rail identity/constraints)** — `/soc/rsc@18200000/rpmh-regulator-{smpa4,ldoa5,ldoa6,ldoa9,ldoa17,smpc8}` group nodes and their `regulator-pm8150*` children; property spellings and values in §2.2/§2.3. `ufs_phy_gdsc` = `/soc/qcom,gdsc@177004`.

**B3 (ACK side)** — `<ack>/common/arch/arm64/boot/dts/qcom/sm8250.dtsi:2507,2519,2542,2544,2550-2577,2579,2593`; `drivers/pmdomain/qcom/rpmhpd.c:90-95,126-137,140-144,465-477`; `drivers/ufs/host/ufshcd-pltfrm.c:176-195`; `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c:1169-1190`; `drivers/clk/qcom/gcc-sm8250.c:3256-3262`; `drivers/regulator/qcom-rpmh-regulator.c` (`qcom,pm8150-rpmh-regulators` match).

**B4 (property-name counts)** — `git grep -c -F` / `git grep -n -F` over `<ack>/common` at `8ad08f75`; counts as tabulated in §2.5.

**D1** — E1 `selected_files/boot.img`, `recovery.img`, `ramdisk.img`, `recovery_ramdisk.img`, `dtbo.img`; boot header fields at offsets 0–1647 (v0/v1 fields) and 1648–1659 (v2 `dtb_size`/`dtb_addr`); DTB section decoded as four consecutive FDTs.

**D2** — AOSP `avbtool 1.4.0` `info_image` on all eleven E1 images (sanitized); `vbmeta_cust.img` offsets 0 (`AVB0`), 1 568 (end of header+auth+aux), 1 048 512 (`AVBf`).

**D3/D4** — E5 `partition_names_redacted.txt` (87 by-name links; `abl→sde6`, `boot→sde9`, `dtbo→sde13`, `ramdisk→sda22`, `vbmeta→sde12`, `vbmeta_cust→sda28`, `cust→dm-0`, `hw_product→dm-1`, `super→sda37`), `fastboot_getvar_redacted.txt`, `live_dtb_status.txt`, `live.dtb.sha256`, `adb_getprop_redacted.txt:753` (`ro.boot.dtbo_idx=[2]`); E1 `REPORT_README.txt` (exclusions), `package_inventory.csv` (43 rows), `copied_files_sha256.csv` (11 rows).

## Appendix B — E1 image hashes re-verified this round

All eleven files were re-hashed during this round and compared against `copied_files_sha256.csv`; **11/11 match**, no mismatch.

| File | Bytes | SHA-256 |
|---|---:|---|
| `boot.img` | 100663296 | `027f88fd6f318523925ca27a4d681d17a9bbca904b0c471ccc05e651d3da19b8` |
| `dtbo.img` | 25165824 | `51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c` |
| `ramdisk.img` | 2097152 | `5c20e4781f701e075ab30d3f8389172435e5591579bb5971f1b29331862fddc0` |
| `recovery.img` | 100663296 | `956417584d2deb409761316f262732859e356a15cb5fe85436df3d5f141c5548` |
| `recovery_ramdisk.img` | 33554432 | `b2b9e3391927bd31684504e7dee7f527bdcbfe53d4bd325e5d1beeeaada7c3e1` |
| `vbmeta.img` | 1048576 | `c797232b437c483ad2332e8754d880ce61f0d211676dfc6397d98160230bbce7` |
| `vbmeta_cust.img` | 1048576 | `eb517a9776581677d6550d35689301b19c8a528fb9c8070d0180c9d8d3fe511f` |
| `vbmeta_hw_product.img` | 1048576 | `387d5307048a4036525f61a9fd6ba30ad9302fb4e7c497cde74e6bb98161311d` |
| `vbmeta_odm.img` | 1048576 | `c99184823142b9351b601e101a80ebecd947845002d561d9c9f3a42623420747` |
| `vbmeta_system.img` | 1048576 | `8cf59433d16973adf542ec570c1656a773cdf77a0efb82f6544a7ce9fa735bf6` |
| `vbmeta_vendor.img` | 1048576 | `375ec9c09cc829736359b86b2b09179b46995fba68a661d0cbf2e11df6c61a0a` |

`recovery.img` and `erecovery.img` are recorded in prior rounds as byte-identical (sha256 `956417584d2…`); only `recovery.img` is in E1, so that identity is quoted from ROUND64, not re-checked here.

## Appendix C — E7 DTBO entry hashes

| File | Bytes | SHA-256 |
|---|---:|---|
| `dtbo_entry_0.dtbo` | 329044 | `6940ce1167a3a21cb677a422da4327682d5e6d266dc5af5a002acb28cfc72aef` |
| `dtbo_entry_1.dtbo` | 329352 | `685a837e65a692da8780df6f9245c010128893ef22d0aeb1046b572eabe2872f` |
| `dtbo_entry_2.dtbo` | 329240 | `0633a6fbeebbad45c0f5572faf222c779e1cd51d253a6ef8282592a730ba3c8b` |
| `dtbo_entry_3.dtbo` | 329098 | `e68e5a48f64cfb686e2698b4dba07d58fa07fe4316522bbb4323ecfbeb9f486c` |
| `dtbo_entry_4.dtbo` | 329340 | `866991056bef3a99d7e010bc13196f87ee5b93474e70a75a4c34ddcc4bad6cfc` |
| `dtbo_entry_5.dtbo` | 329356 | `699df8950612ca3825db38050dceb20d08c85ded666e238a57b281c80ba7eec1` |
| `dtbo_entry_6.dtbo` | 329356 | `fca5a7a83ea69a473720c180594cf95035c57707957e1effe0484b76bdbad844` |
| `dtbo_entry_7.dtbo` | 329352 | `0a57a7f8ac678073542de72cef02e2bbbf9d40dd5aeb30000835258d55cff07b` |
| `dtbo_entry_8.dtbo` | 329352 | `a7946352a86ab6e47b5ee79d84e5d6c4cf4e548c96b0221cec909f32ebd9d21d` |

`boot_fdt_candidate_0.dtb` = 556 524 B, sha256 `df2730f3d2e9bdabad874c3ef7399534c5c6070b046c4524224aa461ba2c70f7` — byte-identical to FDT #0 of the boot/recovery DTB section (§3.1 D1-a).
