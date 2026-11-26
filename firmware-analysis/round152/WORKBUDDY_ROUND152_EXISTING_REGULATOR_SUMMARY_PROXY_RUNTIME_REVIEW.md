# WORKBUDDY ROUND152 — Existing ROUND151 regulator_summary: ARC nesting and proxy-consumer runtime review

- **Executor: WorkBuddy Agent (local Agent 1).** Not 2号 AI, not 2号 Agent.
- Target: Huawei MatePad 11 (2021), DBY-W09 / HWDBY / KONA / SM8250
- Stock system under analysis: HOS 4.3.0.196(C00E100), Android 12 / API 31, kernel 4.19.157-perf+
- Input: **only** the already-captured ROUND151 local evidence
- Branch: `workbuddy/round152-existing-round151-proxy-summary-audit`
- Disposition: **LOCAL_REANALYSIS_COMPLETE — no proxy consumer handle is observable in the captured summary; proxy lifecycle remains UNKNOWN**

---

## 0. Executive disposition

This round reopened exactly one already-captured file — the ROUND151 `regulator_summary` dump — and asked whether it contains explicit proxy consumer handles, useful ARC nesting evidence, or additional UFS/GDSC runtime facts. No device was connected, no ADB or `su` command was issued, no sysfs/debugfs path was re-read.

Four results matter:

1. **The captured summary contains zero occurrences of the string `proxy`.** A proxy consumer created by the generic Qualcomm mechanism is registered against a *device*, so the regulator core prints that device's name in the supplier's consumer list. No such name exists, and more importantly **no provider has an unexplained open count** — every one of the 82 providers has `open == number of printed consumer entries` (82/82, zero exceptions). A live proxy handle would have added one.
2. **All eight `proxy-supply` sites are present in the live merged FDT** and all eight resolve, including two genuine self-references (`gdsc@af03000`, `refgen`). This corrects the earlier reading of this round's own first pass, where a truncated ARC-only excerpt appeared to show two sites. The full-file census is eight, matching ROUND139's count exactly.
3. **The two most decisive sites are runtime-dead, not runtime-active.** `pm8150_l14` declares `proxy-supply` + `qcom,proxy-consumer-enable` + a 62 000 µA current request, yet reports `state=disabled`, `num_users=0`, `open=1`, and **no named consumer at all**. `mdss_core_gdsc` (`gdsc@af03000`) declares `proxy-supply` to itself + enable, and also reports `state=disabled`, `num_users=0`.
4. **ARC and GDSC structure reconcile exactly, three ways.** 13 ARC child regulators are declared in the live FDT and 13 are registered in the summary (13/13). 13 GDSC nodes declare `parent-supply` into ARC, 13 `-SUPPLY` sysfs links carry the same edges, and 13 GDSC providers nest under ARC in the summary (13/13/13).

A note on what this does **not** establish: a static snapshot cannot distinguish "the proxy consumer was never created" from "it was created and already released". Both leave the same `open` count. The report therefore states the observable fact (no live proxy vote, no proxy handle) and leaves the lifecycle mechanism **UNKNOWN**, as §4.10 requires.

---

## 1. Input, integrity and scope

### 1.1 The one file under analysis

| Item | Value |
|---|---|
| Local path | `r151-root-readonly/evidence/raw/410_reg_summary.out` |
| Source command key | `410_reg_summary` |
| Command (ROUND151) | `cat /sys/kernel/debug/regulator/regulator_summary 2>&1` |
| Size | 25 966 bytes |
| Lines | 322 (2 header + 320 data) |
| SHA-256 | `1dc16f5660aae354540e2c05084552b6699876a68b67b84356c2eff6aaed417f` |
| Manifest entry | identical SHA-256, recorded in `evidence/meta/MANIFEST.sha256` |
| Command index status | `PASS`, exit 0, stderr 0 bytes |

The file was located through the existing command index (`evidence/meta/index.tsv`) and manifest, then read directly. The command was **not** re-executed, and no other path was inspected.

### 1.2 Supporting ROUND151 files used (same local workspace only)

| File | Use in this report |
|---|---|
| `raw/302_reg_all.out` | per-regulator `state` / `num_users` / `microvolts` |
| `raw/303_reg_uflist.out` | flat `users=N state=...` cross-check |
| `raw/304_reg_links.out` | every `-SUPPLY` symlink, i.e. the ARC and GDSC supply edges |
| `raw/106_dmesg.out` | negative check for proxy keywords |
| `private/fdt_live_round151.bin` | live merged FDT for declaration-side mapping |
| `private/fdt_decode_full.txt` | pre-decoded node dump, spot-checked against the binary |

### 1.3 What was explicitly not done

- No USB connection, no `adb`, no `su`, no `fastboot`, no reboot, no recovery, no UART.
- No new read from the tablet, including read-only paths.
- No mount, remount or debugfs change.
- No read of `/sys/kernel/debug/cmd_db` or `pmic-votable` — not captured in ROUND151, and separately gated.
- No partition access, no write, no source/DTS/patch/build change.
- No inspection of another Agent's workspace.

### 1.4 Evidence grading used below

| Grade | Meaning |
|---|---|
| **A** | Direct captured output, quoted or tabulated from the file |
| **B** | Corroborated by two or more independent captured sources |
| **C** | Parsed mapping, i.e. a deterministic transformation of captured bytes (indentation → tree, phandle → node) |
| **D** | Inference; explicitly labelled, never used as a conclusion on its own |

---

## 2. Method and self-check

### 2.1 Parser

The summary is an indented tree: a provider line carries `use / open / bypass / voltage / current / min / max`, a consumer line carries only `min / max`, and a provider nested under another provider is a supply relationship. A local parser (`parse_summary.py`) classified lines by indentation and column shape, rebuilt the parent stack, and emitted a flat table plus a provider table.

Result: **320 data rows parsed, 0 unparsed lines** — every line of the 322-line file was accounted for.

| Parsed quantity | Count |
|---|---:|
| Provider lines | 82 |
| Consumer lines | 238 — of which **18 are themselves providers** (the nested supply consumers of §3.2) |
| Data lines total | 320 (82 + 238) |

Local working artefacts, kept out of the repository because they are derived from raw capture:

| File | Content |
|---|---|
| `r152-summary-review/summary_flat.tsv` | every parsed row: line no., indent, kind, name, use/open, voltage, min/max, tree path |
| `r152-summary-review/providers.tsv` | 82 providers with use/open/volt/min/max/parent/children/deviceless |
| `r152-summary-review/work/fdt_sites.txt` | ARC providers, GDSC supply edges and every `proxy*` property site from the live FDT |
| `r152-summary-review/parse_summary.py`, `fdt_sites.py` | the two read-only parsers |

No raw summary text and no FDT bytes are reproduced in this report.

### 2.2 Structural self-check (this is what makes the negative result usable)

The parser's tree reconstruction was validated against an intrinsic property of the format: `open` is the number of times the regulator was opened, and the summary prints one line per open consumer. Therefore `open` must equal the number of child entries.

```
providers: 82
open != children: 0
```

**82 of 82 providers satisfy `open == children`, with zero exceptions.** This is the load-bearing check for §4.2: if a proxy consumer existed and held the regulator open, the provider's `open` would exceed the number of entries that can be explained by named devices plus `deviceless`. It never does.

### 2.3 A display trap worth recording

The ARC regulators report `microvolts` in the range 16–416. Those are **level encodings, not microvolts** (ROUND139, ROUND151 §5.3, AI1 §5). Because the summary prints millivolts with integer division, a level of 64 becomes `0mV`. Consequently **the `0mV` column for every ARC level regulator is a truncation artifact and must not be read as "0 volts"**. Example:

| Regulator | summary volt column | `microvolts` in sysfs | Interpretation |
|---|---:|---:|---|
| `pm8150_s3_mmcx_sup_level` | 0 mV | 64 | level 64 |
| `pm8150a_s3_mmcx_sup_level` | 0 mV | 192 | level 192 |
| `pm8150a_s4_level` | 0 mV | 192 | level 192 |
| `pm8150a_s3_level` | 0 mV | 256 | level 256 |
| `pm8150_s3_level` | 0 mV | 256 | level 256 |

Two independent captures agree on this (A/B): the summary text and `raw/302_reg_all.out` `microvolts=`.

---

## 3. Summary structure extracted (§4.1)

### 3.1 The tree at a glance

- 82 providers, of which:
  - **13** are ARC level regulators (`*_level`, `*_level_ao`, `*_level_so`, `*_mmcx_sup_level`) with `volt=0mV` due to §2.3;
  - **24** are GDSC providers (`*_gdsc`);
  - the remaining **45** split into **37** PMIC VRM rails (PM8150/PM8150A/PM8150L S/L/BOB) and **8** non-PMIC providers: `regulator-dummy`, `refgen`, `display_panel_avdd`, `hsphy@88e3000`, `hsphy@88e4000`, `vdd_hap_boost`, `smb5-vbus`, `smb5-vconn`.
- 238 consumer entries, of which **81 are the literal token `deviceless`**.

13 + 24 + 45 = 82.

### 3.2 Nested providers (supply relationships made visible)

**18** providers appear nested under another provider — 5 ARC children plus 13 GDSC nodes whose supply is another regulator. They are exactly the nodes carrying a `*-supply` edge into ARC:

| Provider | use | open | Nested under | Meaning |
|---|---:|---:|---|---|
| `pm8150_s3_level` | 2 | 12 | `pm8150a_s3_level` | CX ALL consumes MX ALL |
| `gpu_cx_gdsc` | 0 | 4 | `pm8150_s3_level` | GDSC consumes CX ALL |
| `pm8150_s3_level_ao` | 1 | 2 | `pm8150a_s3_level_ao` | CX AO consumes MX AO |
| `pm8150a_s4_level_ao` | 0 | 1 | `pm8150a_s3_level_ao` | MMCX AO consumes MX AO |
| `pm8150a_s3_mmcx_sup_level` | 3 | 1 | `pm8150_s3_mmcx_sup_level` | MX MMCX-supply consumes CX MMCX-supply |
| `pm8150a_s4_level` | 3 | 31 | `pm8150a_s3_mmcx_sup_level` | MMCX ALL consumes MX MMCX-supply |
| `bps_gdsc` | 0 | 2 | `pm8150a_s4_level` | GDSC consumes MMCX ALL |
| `ife_0_gdsc` | 0 | 3 | `pm8150a_s4_level` | idem |
| `ife_1_gdsc` | 0 | 3 | `pm8150a_s4_level` | idem |
| `ipe_0_gdsc` | 0 | 2 | `pm8150a_s4_level` | idem |
| `sbi_gdsc` | 0 | 1 | `pm8150a_s4_level` | idem |
| `titan_top_gdsc` | 0 | 23 | `pm8150a_s4_level` | idem |
| `mdss_core_gdsc` | 0 | 2 | `pm8150a_s4_level` | idem |
| `mvs0_gdsc` / `mvs0c_gdsc` / `mvs1_gdsc` / `mvs1c_gdsc` | 0 | 2/3/2/2 | `pm8150a_s4_level` | idem |
| `gpu_gx_gdsc` | 0 | 3 | `pm8150a_s1_level` | GDSC consumes GFX ARC |

The table lists 15 rows; the `mvs*` row is compact and stands for four separate providers, so it covers 18 providers in total (5 ARC children + 13 GDSC). Every one of these 18 is a `*-supply` consumer of another regulator, which is why the regulator core nests it.

### 3.3 The `deviceless` token — why it cannot be used as proxy evidence

`deviceless` appears **81 times**, i.e. in 81 of 82 providers (the sole exception is `pm8150a_s3_mmcx_sup_level`, whose single entry is its nested child). Its `min/max` is always `0mV/0mV`, and it never contributes to `num_users`.

Because it is near-universal and structurally unconditional, **`deviceless` is a formatting artifact of the summary, not a signature of a proxy consumer.** Attributing L14's lone `deviceless` entry to a released proxy vote is therefore an inference this report does **not** make.

### 3.4 Semantic boundary: a printed voltage constraint is not an enable

The consumer lines carry only `min/max`, not a per-consumer enable flag. Therefore:

- a **non-zero** consumer voltage proves only that the consumer *set a voltage request*;
- `use` / `num_users` counts *enables*, and **cannot be decomposed into which consumers enabled**.

This directly limits a claim made in ROUND151 §4.4, corrected in §10.2 below.

---

## 4. Explicit search for proxy-like consumer handles (§4.2)

### 4.1 Full-text search

```
$ grep -in "proxy" evidence/raw/410_reg_summary.out
(no match)   exit=1
```

**Zero hits across all 322 lines.** There is no consumer named `proxy`, `*-proxy`, `proxy-consumer`, and no device handle that contains the string.

### 4.2 Search across all of ROUND151's captured raw output

```
$ grep -rin "proxy" evidence/raw/
raw/110_devtree_root.out:11: battery_ui_capacity   huawei_power_proxy    sle95250_1
```

The only hit is the **name of a device-tree child node** (`/huawei_power_proxy`) listed in the root directory of `/proc/device-tree`. It is not a regulator, not a consumer, and not related to the `proxy-supply` mechanism.

### 4.3 Search for provider self-requests

A proxy request would appear either as a named consumer (the provider's own device) or as an additional open on the target regulator. Both were tested:

| Candidate signature | Finding |
|---|---|
| Consumer literally named `proxy` | absent |
| Consumer named after the ARC provider device (`18200000.rsc:rpmh-regulator-*`) | absent from every consumer list. The only `rsc` substring anywhere in the file is `af20000.qcom,sde_rscc` (line 105), an unrelated display rotator device |
| Consumer named after the GDSC device on `mdss_core_gdsc` | only `af20000.qcom,sde_rscc` |
| Unexplained extra `open` on any of the 8 sites | none (§4.5) |
| `deviceless` unique to a proxy site | no — 81/82 providers have it |

The file contains **83 distinct consumer names** in total (including `deviceless`). All of them are platform-device paths, `deviceless`, or the two SPMI child names; none is a regulator-driver device, and none is a proxy handle.

### 4.4 Result

**No proxy consumer handle is observable in the captured summary.** This is a positive, bounded statement: the summary is complete (322/322 lines parsed, 82/82 `open == children`), so the absence is not an artifact of filtering. What it does **not** prove is the reason for absence (never created vs already released) — see §9.

---

## 5. The eight proxy-supply sites mapped (§4.3)

### 5.1 Declaration side — live merged FDT census

A full-file phandle census over `fdt_live_round151.bin` (4566 nodes, 2039 phandles) finds **exactly 8** `proxy-supply` properties:

| # | Declaring node | `proxy-supply` → | phandle | Type |
|---:|---|---|---:|---|
| 1 | `/soc/qcom,gdsc@af03000` | itself | 0x71 | **self-reference** |
| 2 | `/soc/rsc@18200000/rpmh-regulator-cxlvl` | its child `regulator-pm8150-s3-mmcx-sup-level` | 0x7a | provider → own child |
| 3 | `/soc/rsc@18200000/rpmh-regulator-ldoa5` | its child `regulator-pm8150-l5` | 0x7c | provider → own child |
| 4 | `/soc/rsc@18200000/rpmh-regulator-ldoa9` | its child `regulator-pm8150-l9` | 0x7d | provider → own child |
| 5 | `/soc/rsc@18200000/rpmh-regulator-ldoa14` | its child `regulator-pm8150-l14` | 0x7e | provider → own child |
| 6 | `/soc/rsc@18200000/rpmh-regulator-mmcxlvl` | its child `regulator-pm8150a-s4-level` | 0x69 | provider → own child |
| 7 | `/soc/rsc@18200000/rpmh-regulator-ldoc11` | its child `regulator-pm8150a-l11` | 0x80 | provider → own child |
| 8 | `/soc/refgen-regulator@88e7000` | itself | 0xb2 | **self-reference** |

**Methodological note (a trap this round hit and corrected).** The first pass read only the ARC section of the extracted text and saw two `proxy-supply` properties. That was a filtered excerpt, not the file. The full census is eight. §4.9 of the taskbook warns precisely against this: *absence from a filtered excerpt is not proof of absence*. The error was caught before publication and is recorded here so the next round does not inherit it.

### 5.2 ROUND139 reconciliation

ROUND139 §(3) lists exactly these eight sites — `ldoa5`→L5, `ldoa9`→L9, `ldoa14`→L14, `ldoc11`→L11, `cxlvl`→`s3-mmcx-sup-level`, `mmcxlvl`→`s4-level`, `gdsc@af03000`→itself, `refgen`→itself — and ROUND151's decoded FDT reproduces all eight, one for one, with the same target node in every case (B).

One wording correction to ROUND139: it writes that `qcom,proxy-consumer-enable` appears "on the eight `proxy-supply` sites **plus** `/soc/qcom,gdsc@af03000` and `/soc/refgen-regulator@88e7000`", which reads as ten sites. The live census shows **eight** enable sites, and `gdsc@af03000` and `refgen` are *among* the eight, not additional to them. The "plus" phrasing double-counts; the underlying eight are unchanged.

### 5.3 Attribute values — what ROUND139 did not record

| Node carrying `qcom,proxy-consumer-*` | enable | current | voltage |
|---|---|---|---|
| `regulator-pm8150-l5` | present | **100 000 µA** | — |
| `regulator-pm8150-l9` | present | **100 000 µA** | — |
| `regulator-pm8150-l14` | present | **62 000 µA** | — |
| `regulator-pm8150a-l11` | present | **857 000 µA** | — |
| `regulator-pm8150-s3-mmcx-sup-level` | present | — | **384 … 65 535** |
| `regulator-pm8150a-s4-level` | present | — | **384 … 65 535** |
| `/soc/qcom,gdsc@af03000` | present | — | — |
| `/soc/refgen-regulator@88e7000` | present | — | — |

Three facts here are new relative to ROUND139, which gave values only for L5 and L9 and did not mention `-voltage` at all:

- **L14 = 62 000 µA** and **L11 = 857 000 µA** (A).
- **`qcom,proxy-consumer-voltage` exists on exactly two nodes**, both ARC children, value `384 … 65535`. AI2 ROUND148 §2.1 recorded this property's occurrence count as unestablished; it is now established for the live merged tree at **2** (A).
- `384 … 65535` must not be read as microvolts. Both nodes are ARC level providers, so these are **level-encoding bounds**; `65535` is the top of the u32 range, not 65.535 mV (D, consistent with §2.3).

`qcom,proxy-consumer-name` occurs **zero times**: the supply ID therefore defaults, which is consistent with the generic mechanism resolving `proxy-supply` through a `"proxy"` supply name (D).

---

## 6. Per-site runtime classification (§4.4, §4.5)

Each of the eight sites was resolved to its registered regulator and cross-checked against three captures: the summary tree, `302_reg_all.out` (`state`/`num_users`/`microvolts`) and `303_reg_uflist.out` (flat `users=`/`state=`).

### 6.1 The table

| # | Site | Registered regulator | summary use / open | `state` | `num_users` | Named consumers | Extra open for a proxy? |
|---:|---|---|---|---:|---:|---|---|
| 1 | `gdsc@af03000` | `regulator.71` `mdss_core_gdsc` | 0 / 2 | **disabled** | **0** | 1 (`af20000.qcom,sde_rscc`) | no (1 named + deviceless) |
| 2 | `cxlvl` → CX MMCX-supply | `regulator.6` `pm8150_s3_mmcx_sup_level` | 3 / 2 | enabled | 3 | 0 named + 1 nested | no (1 nested + deviceless) |
| 3 | `ldoa5` → L5 | `regulator.14` `pm8150_l5` | 5 / 9 | enabled | 5 | 8 | no (8 + deviceless) |
| 4 | `ldoa9` → L9 | `regulator.19` `pm8150_l9` | 4 / 10 | enabled | 4 | 9 | no (9 + deviceless) |
| 5 | `ldoa14` → L14 | `regulator.26` `pm8150_l14` | **0 / 1** | **disabled** | **0** | **0** | no (deviceless only) |
| 6 | `mmcxlvl` → MMCX ALL | `regulator.32` `pm8150a_s4_level` | 3 / 31 | enabled | 3 | 19 named + 11 nested | no (19 + 1 + 11 = 31) |
| 7 | `ldoc11` → L11 | `regulator.48` `pm8150a_l11` | 1 / 2 | enabled | 1 | 1 (`soc:qcom,dsi-display-primary`) | no (1 + deviceless) |
| 8 | `refgen` | `regulator.51` `refgen` | 2 / 10 | enabled | 2 | 9 | no (9 + deviceless) |

Every `open` value is **fully** explained by printed entries. In no case does a site carry one more open than its listed consumers.

### 6.2 Five-axis classification required by §4.5

| Site | Declaration exists | Runtime provider bound | Proxy handle visible | Use count / request visible | Release timing |
|---|---|---|---|---|---|
| `gdsc@af03000` | yes | yes — `mdss_core_gdsc`, disabled | **no** | **no** (0 users, 0 named) | UNKNOWN |
| CX MMCX-supply | yes | yes — enabled, 3 users | **no** | **no** (3 = nested ARC load) | UNKNOWN |
| L5 | yes | yes — enabled, 5 users | **no** | **no** (9 = 8 peripherals + deviceless) | UNKNOWN |
| L9 | yes | yes — enabled, 4 users | **no** | **no** (10 = 9 peripherals + deviceless) | UNKNOWN |
| L14 | yes | yes — **disabled**, 0 users | **no** | **no** (only deviceless) | UNKNOWN |
| MMCX ALL | yes | yes — enabled, 3 users | **no** | **no** (31 fully attributed) | UNKNOWN |
| L11 | yes | yes — enabled, 1 user | **no** | **no** (2 = dsi-display-primary + deviceless) | UNKNOWN |
| refgen | yes | yes — enabled, 2 users | **no** | **no** (10 = 9 + deviceless) | UNKNOWN |

### 6.3 What the two "disabled, zero-user" sites prove

`pm8150_l14` and `mdss_core_gdsc` are the strongest available evidence because they combine a full declaration set with a *negative* runtime state:

| Site | `qcom,proxy-consumer-enable` | `proxy-supply` | Request declared | `state` | `num_users` |
|---|---|---|---|---|---|
| `pm8150_l14` | present | → itself | current 62 000 µA | **disabled** | **0** |
| `mdss_core_gdsc` | present | → itself | — | **disabled** | **0** |

If a proxy consumer were live and enabled at capture time, both would report `num_users ≥ 1` and the summary would show an extra named consumer. Neither does. Therefore, **at the capture instant, neither site carried an active proxy vote** (A).

The converse — that the mechanism ran earlier and released — cannot be excluded from this snapshot, and is not claimed.

---

## 7. UFS rails and `ufs_phy_gdsc` reconciliation (§4.6, §4.8)

### 7.1 Six rails: summary, sysfs and constraint column

| Rail | summary use / open | sysfs `users` / `state` | Target µV | Declared min/max µV | UFS handle |
|---|---|---|---:|---|---|
| L17 | 1 / 2 | 1 / enabled | 2 504 000 | 2 496 000 / 3 008 000 | `1d84000.ufshc` 2 504 000–2 950 000 |
| L6 | 2 / 3 | 2 / enabled | 1 200 000 | 1 200 000 / 1 200 000 | `1d84000.ufshc` **twice**, both 1 200 000 |
| S4 | 5 / 7 | 5 / enabled | 1 800 000 | 1 800 000 / 1 920 000 | `1d84000.ufshc` 1 800 000–1 920 000 |
| S8 | 2 / 4 | 2 / enabled | 1 200 000 | 1 200 000 / 1 400 000 | `1d84000.ufshc` **0 / 0** |
| L5 | 5 / 9 | 5 / enabled | 880 000 | 880 000 / 880 000 | `1d87000.ufsphy_mem` 880 000 |
| L9 | 4 / 10 | 4 / enabled | 1 200 000 | 1 200 000 / 1 200 000 | `1d87000.ufsphy_mem` 1 200 000 |

summary `use` and sysfs `num_users` agree on all six rails (B).

### 7.2 Why L6 has two UFS handles — confirmed from the tree, not inferred

`pm8150_l6` prints `open = 3` with three entries: `1d84000.ufshc` at 1 200 000–1 200 000, `1d84000.ufshc` again at 1 200 000–1 200 000, and `deviceless`. The live FDT supplies the mechanism: **two distinct host properties point at L6** —

- `vccq-supply` → `regulator-pm8150-l6`
- `qcom,vddp-ref-clk-supply` → `regulator-pm8150-l6`

Two `regulator_get()` calls from the same device produce two consumer entries with the same `dev_name`. The duplicate is **two genuinely different rails-on-the-same-regulator inputs**, not a printing artifact (A/C).

### 7.3 Why S8's UFS handle is 0 mV and not an enabled user

`pm8150a_s8` prints `use = 2`, `open = 4`, with four entries: `vendor:bt_qca6390` (1 200 000–1 350 000), `b0000000.qcom,cnss-qca6390` (1 200 000–1 350 000), `1d84000.ufshc` (**0/0**), `deviceless`.

The two enabled users are BT and CNSS; the UFS entry carries no voltage request at all. This is exactly the shape of `qcom,vccq-parent-supply`: a *parent/current* relation, not a voltage vote. **Do not count S8 as a third enabled UFS rail** (A), which confirms ROUND151 §4.4 and AI1 §3.1's correction.

### 7.4 Do L5 and L9 totals include non-UFS consumers? Yes — explicitly

| Rail | Non-UFS consumers printed | UFS consumer | Non-zero entries | `use` |
|---|---|---:|---:|---:|
| L5 | `ae96400`/`ae94400` MDSS DSI PHY, `88e4000`/`88e3000` hsphy, `1c00000`/`1c08000` pcie | `1d87000.ufsphy_mem` | 7 | 5 |
| L9 | `ae90000` dp_display, `88e8000`/`88eb000` ssphy, `ae94000`/`ae96000` MDSS DSI CTRL, `1c00000`/`1c08000` pcie | `1d87000.ufsphy_mem` | 8 | 4 |

So L5 and L9 are **shared rails**, and neither rail's voltage proves the PHY is the load. This confirms ROUND151 §5.4's caution rather than weakening it.

One refinement is required: `use = 5` on L5 against **7** non-zero constraints cannot be decomposed into "which five", because the summary does not print a per-consumer enable flag (§3.4). The correct statement is: *five enables exist among the eight printed entries; the mapping from enable to consumer is not visible in this file.*

### 7.5 `ufs_phy_gdsc`

| Attribute | Value | Source |
|---|---|---|
| DT node | `/soc/qcom,gdsc@177004`, `regulator-name = "ufs_phy_gdsc"`, `qcom,retain-regs` | FDT (C) |
| `parent-supply` / any `*-supply` | **none** | FDT census + `304_reg_links.out` (B) |
| Registered regulator | `regulator.55`, device `177004.qcom,gdsc` | `302_reg_all.out` (A) |
| `state` | **disabled** | `302` / `303` (A) |
| `num_users` | **0** | `302` / `303` (A) |
| summary line | `ufs_phy_gdsc  0  2  0  0mV  0mA  0mV  0mV` | summary (A) |
| Consumer entries | `1d84000.ufshc` at **0/0**, plus `deviceless` | summary (A) |
| Any `power-domains` reference in the whole tree | **none** | FDT (C) |
| Any active vote | **none observed** | summary + sysfs (B) |

So the UFS host holds an *open* on `ufs_phy_gdsc` (hence `open = 2`) but has **never enabled it** (`use = 0`), and the provider itself is `disabled`. This is a consistent, three-source picture: bound-by-name, never-voted.

---

## 8. ARC nesting and the thirteen GDSC consumers (§4.7)

### 8.1 Declaration side: seven providers, thirteen children

| `qcom,resource-name` | Provider node | Child `regulator-name`s |
|---|---|---|
| `mx.lvl` | `rpmh-regulator-mxlvl` | `pm8150a_s3_level`, `pm8150a_s3_level_ao`, `pm8150a_s3_mmcx_sup_level` |
| `cx.lvl` | `rpmh-regulator-cxlvl` | `pm8150_s3_level`, `pm8150_s3_level_ao`, `pm8150_s3_mmcx_sup_level` |
| `mmcx.lvl` | `rpmh-regulator-mmcxlvl` | `pm8150a_s4_level`, `pm8150a_s4_level_ao`, `pm8150a_s4_level_so` |
| `lmx.lvl` | `rpmh-regulator-lmxlvl` | `pm8150_l4_level` |
| `lcx.lvl` | `rpmh-regulator-lcxlvl` | `pm8150_l11_level` |
| `gfx.lvl` | `rpmh-regulator-gfxlvl` | `pm8150a_s1_level` |
| `ebi.lvl` | `rpmh-regulator-ebilvl` | `pm8150a_s6_level` |

3 + 3 + 3 + 1 + 1 + 1 + 1 = **13 child regulators** (C).

### 8.2 Runtime side: 13 of 13 registered

The summary contains exactly these 13 names as providers, and no other `*_level*` provider:

`pm8150a_s3_level`, `pm8150a_s3_level_ao`, `pm8150a_s3_mmcx_sup_level`, `pm8150_s3_level`, `pm8150_s3_level_ao`, `pm8150_s3_mmcx_sup_level`, `pm8150a_s4_level`, `pm8150a_s4_level_ao`, `pm8150a_s4_level_so`, `pm8150_l4_level`, `pm8150_l11_level`, `pm8150a_s1_level`, `pm8150a_s6_level`.

**13 declared, 13 registered, 0 missing, 0 extra** (A/B). No ARC child failed to probe.

### 8.3 The MMCX chain: three independent sources agree on direction

| Source | Evidence | Chain |
|---|---|---|
| FDT `parent-supply` | `pm8150a_s4_level-parent-supply` → `mxlvl/regulator-pm8150a-s3-mmcx-sup-level`; `pm8150a_s3_mmcx_sup_level-parent-supply` → `cxlvl/regulator-pm8150-s3-mmcx-sup-level` | MMCX ALL ← MX MMCX-supply ← CX MMCX-supply |
| `304_reg_links.out` `-SUPPLY` | `pm8150a_s3_level` → `cxlvl/regulator.4`; `pm8150a_s3_mmcx_sup_level` → `mmcxlvl/regulator.32`; `pm8150_s3_mmcx_sup_level` → `mxlvl/regulator.3` | same, supplier-directory links point at the consumer |
| summary indentation | `pm8150a_s4_level` nested in `pm8150a_s3_mmcx_sup_level` nested in `pm8150_s3_mmcx_sup_level` | same |

Read as dependencies: **MMCX ALL depends on MX MMCX-supply depends on CX MMCX-supply.** This is ROUND139's and AI1's direction, and it re-confirms that ROUND149's `-SUPPLY` reading was inverted (B).

### 8.4 Thirteen GDSC-to-ARC edges, visible three ways

| GDSC node | `regulator-name` | ARC parent | `-SUPPLY` link present | Nested in summary |
|---|---|---|---:|---:|
| `gdsc@ad07004` | `bps_gdsc` | `pm8150a_s4_level` | yes (`regulator.65`) | yes |
| `gdsc@ad0a004` | `ife_0_gdsc` | `pm8150a_s4_level` | yes (`.66`) | yes |
| `gdsc@ad0b004` | `ife_1_gdsc` | `pm8150a_s4_level` | yes (`.67`) | yes |
| `gdsc@ad08004` | `ipe_0_gdsc` | `pm8150a_s4_level` | yes (`.68`) | yes |
| `gdsc@ad09004` | `sbi_gdsc` | `pm8150a_s4_level` | yes (`.69`) | yes |
| `gdsc@ad0c144` | `titan_top_gdsc` | `pm8150a_s4_level` | yes (`.70`) | yes |
| `gdsc@af03000` | `mdss_core_gdsc` | `pm8150a_s4_level` | yes (`.71`) | yes |
| `gdsc@abf0d18` | `mvs0_gdsc` | `pm8150a_s4_level` | yes (`.73`) | yes |
| `gdsc@abf0bf8` | `mvs0c_gdsc` | `pm8150a_s4_level` | yes (`.74`) | yes |
| `gdsc@abf0d98` | `mvs1_gdsc` | `pm8150a_s4_level` | yes (`.75`) | yes |
| `gdsc@abf0c98` | `mvs1c_gdsc` | `pm8150a_s4_level` | yes (`.76`) | yes |
| `gdsc@3d9106c` | `gpu_cx_gdsc` | `pm8150_s3_level` | yes (`regulator.62`) | yes |
| `gdsc@3d9100c` | `gpu_gx_gdsc` | `pm8150a_s1_level` | yes (`regulator.63`) | yes |

**13 / 13 / 13**: 13 FDT `parent-supply` declarations, 13 sysfs `-SUPPLY` links, 13 nested GDSC providers in the summary (B).

### 8.4.1 Why the count is 13 and not 26 — reconciling ROUND139's "31"

Each of these 13 GDSC nodes carries **two** supply properties, both pointing at the *same* ARC child:

- `parent-supply` → ARC child
- `vdd_parent-supply` → ARC child

Verified for all 13, with the two targets identical in every case; the other 11 GDSC nodes carry neither. So the property-occurrence count is **26**, over **13** distinct nodes.

Add the five ARC provider-child `*-parent-supply` properties (`pm8150_s3_level`, `pm8150_s3_level_ao`, `pm8150a_s4_level`, `pm8150a_s4_level_ao`, `pm8150a_s3_mmcx_sup_level`) and the total is **26 + 5 = 31**.

**That reproduces ROUND139's "31 `parent-supply`-family occurrences" exactly**, which ROUND139 itself decomposed as "13 GCC GDSC→ARC-level edges plus 5 ARC provider-child edges" — counting *nodes* for the GDSC half and *properties* for the ARC half. Both descriptions are correct; the live census shows why the arithmetic works (A/C).

The dual property also explains the doubled GDSC entries in the summary (§8.5): two supply declarations produce two consumer registrations, one resolved by the regulator core and one by the GDSC driver.

### 8.5 A double-counting detail that must not be misread as 22 GDSCs

`pm8150a_s4_level` prints `open = 31`. Those 31 entries are **19 named devices + 1 `deviceless` + 11 nested GDSC providers**, and of the 19 named devices **11 are the platform-device names of the same 11 GDSCs** (`abf0c98.qcom,gdsc` … `ad07004.qcom,gdsc`).

So 22 of the 31 entries belong to 11 GDSC nodes, each appearing exactly twice. The mechanism is the dual declaration of §8.4.1: one entry is the **driver's own** `regulator_get()` on the GDSC device (printed under its platform-device name), the other is the **regulator core's** supply consumer for the nested provider (printed under its `regulator-name`). **The distinct GDSC count under MMCX ALL is 11, not 22** (C for the arithmetic; D for the driver-vs-core attribution of each entry, which follows from the two declarations but was not checked against GDSC driver source).

That the 11 addresses map one-for-one onto the 11 `regulator-name`s was verified against the FDT child list, not assumed.

---

## 9. Limits of this evidence (§4.9, §4.10)

### 9.1 What is directly proven

1. The captured summary is complete and internally consistent: 322/322 lines parsed, 82/82 providers with `open == children`.
2. It contains **no** proxy-named consumer and **no** consumer that would have to be explained by a proxy request.
3. All eight `proxy-supply` sites exist in the live merged FDT and all eight resolve to the nodes ROUND139 named.
4. `pm8150_l14` and `mdss_core_gdsc` are declared proxy sites with **`state=disabled`, `num_users=0`, and no named consumer**.
5. 13 ARC children declared = 13 registered; 13 GDSC→ARC edges in three independent forms.
6. `ufs_phy_gdsc` is bound to the UFS host by name but has **0 users and is disabled**, with **no `power-domains` reference** anywhere.

### 9.2 What is explicitly not proven

| Question | Status | Why |
|---|---|---|
| Were proxy consumers ever created on this boot? | **UNKNOWN** | A released consumer leaves `open` at the same value as one that never existed |
| When would/does the proxy unvote occur? | **UNKNOWN** | `sync_state` / `late_initcall_sync` timing is code execution, not state |
| Is the physical GDSC gate really off? | **UNKNOWN** | The file reports a *software regulator* state only |
| Do L5/L9 enables belong to the PHY or to PCIe/DSI? | **UNKNOWN** | No per-consumer enable flag is printed |
| Actual ARC level values / CMD-DB AUX map | **UNKNOWN** | Not in this file; `/sys/kernel/debug/cmd_db` was not captured |
| Physical PMIC VIN parents | **UNKNOWN** | Requires schematic/netlist |

### 9.3 The lifecycle boundary, stated explicitly

Per §4.10, this report **does not infer** proxy `sync_state` / `late_initcall` unvote timing from the snapshot. The snapshot shows *current* requests and consumer handles. It cannot show whether a vote existed at second 0 and was withdrawn at second 30.

What can be said, and is said: at the moment of capture, **no proxy vote was in effect on any of the eight declared sites**.

---

## 10. Corrections to ROUND151 and to this round's own first pass

### 10.1 ROUND151 §5.4 — the table was incomplete

ROUND151's table listed **seven** rows (L5, L9, L14, `cxlvl`, `s3-mmcx-sup-level`, `mmcxlvl`, `gdsc@af03000`) and stated "14 proxy-bearing nodes in total". Two things need correcting:

- **Missing rows.** `rpmh-regulator-ldoc11` → `regulator-pm8150a-l11` and `/soc/refgen-regulator@88e7000` are `proxy-supply` sites and were not in the table. The complete set is eight.
- **The "14" figure cannot be reproduced from the regulator-proxy sites.** The live FDT has 8 `proxy-supply`, 8 `-enable`, 4 `-current`, 2 `-voltage` and 0 `-name`. Any count of 14 must have folded in unrelated property families that share the string `proxy` — `qcom,proxy-clks` / `qcom,proxy-regs` / `qcom,proxy-timeout-ms` on the remoteproc and TPDM/CTI nodes, and the `__symbols__` aliases. Those are a different mechanism (proxy *power-domain/clock voting for remoteprocs*), not `proxy-supply`. **Do not reuse "14" as a regulator-proxy count.**

A second wording issue in the same table: five of the seven rows say `proxy-supply → itself`. Only two are genuine self-references (`gdsc@af03000`, `refgen`); for `ldoa5`/`ldoa9`/`ldoa14`/`ldoc11`/`cxlvl`/`mmcxlvl` the property sits on the **provider** node and points at that provider's **own child regulator**. The distinction matters, because only the provider→child form can produce a consumer device handle, and only the self-referential form votes on the declaring device itself.

The census behind both corrections:

| Property | Count in live FDT |
|---|---:|
| `proxy-supply` | **8** |
| `qcom,proxy-consumer-enable` | **8** (the eight sites' targets) |
| `qcom,proxy-consumer-current` | **4** |
| `qcom,proxy-consumer-voltage` | **2** |
| `qcom,proxy-consumer-name` | **0** |

### 10.2 ROUND151 §4.4 — "which consumers are enabled" was over-stated

ROUND151 wrote that `num_users = 5` on L5 "counts only the enabled ones", implying the enabled subset was identifiable. The summary prints no per-consumer enable flag, so the subset is **not** identifiable from this file. The corrected statement is:

> Seven consumers carry an 880 000 µV constraint on L5 and eight carry 1 200 000 µV on L9; the rails report 5 and 4 enables respectively. The mapping from enable to consumer is not visible in `regulator_summary`.

### 10.3 ROUND139 — the "plus one GDSC and one refgen" phrasing

As in §5.2: the eight `-enable` sites are the eight `proxy-supply` sites. `gdsc@af03000` and `refgen` are two of the eight, not two more.

### 10.4 This round's own first pass

Reading only the ARC excerpt suggested two `proxy-supply` properties. That was wrong for the reason §4.9 predicts, and was corrected by a full-file census before any text was written. Recorded so the next round re-runs the census rather than trusting an excerpt.

---

## 11. Answers to the taskbook's seven questions

| § | Question | Answer |
|---|---|---|
| 4.1 | Structure table of provider / consumer / counts / requests / nesting | §3 (82 providers, 238 consumers, 320 rows, 0 unparsed) |
| 4.2 | Search for proxy-like consumer names / self-requests | §4 — **0 hits** for `proxy`; no provider self-request visible |
| 4.3 | Map observable handles to the eight sites | §5 — 8 sites declared; **0** observable proxy handles to map |
| 4.4 | Reconcile enable/current/voltage with observed handles | §6 — declarations complete, runtime handles absent |
| 4.5 | Five-axis classification per site | §6.2 |
| 4.6 | UFS rail counts and handles | §7 — L6 two handles explained; S8 0 mV not an enabled user; L5/L9 shared |
| 4.7 | ARC nesting + thirteen GDSC consumers | §8 — 13/13/13, direction MMCX ← MX ← CX |
| 4.8 | `ufs_phy_gdsc` state / users / handle / vote | §7.5 — disabled, 0 users, host handle at 0 mV, no active vote |
| 4.9 | Exact evidence and its limits | §9 |
| 4.10 | No lifecycle inference from a static snapshot | §9.3 |

---

## 12. Consequence for the candidate decision (no decision taken here)

This round is evidence work. It does not choose a candidate design. Three consequences for the pending decisions are worth recording because they narrow the option space:

1. **Proxy support cannot be validated from the stock runtime.** The declared sites exist, but the stock snapshot shows no live proxy handle on any of them, and the two fully-declared sites are disabled with zero users. Any argument that "HOS relies on a proxy vote at runtime" must therefore rest on source or on a differently-timed capture, **not** on this file.
2. **`ufs_phy_gdsc` is genuinely idle on stock.** Bound by name to `ufshc.vdd-hba-supply`, never enabled, no `power-domains` consumer. The HOS-vs-ACK behavioural difference flagged in ROUND151 (HOS uses a never-voted regulator handle; ACK attaches the GDSC through GenPD) is not resolved by this file, but its stock side is now unambiguous.
3. **The ARC structure is fully faithful at the declaration and registration level.** 13 children, 13 GDSC edges, all registered and bound. What remains unknown is the *value* layer (levels, votes), which lives in `cmd_db`/`pmic-votable` and is separately gated.

---

## 13. Deliverable, verification and stop

| Item | Value |
|---|---|
| Report path | `firmware-analysis/round152/WORKBUDDY_ROUND152_EXISTING_REGULATOR_SUMMARY_PROXY_RUNTIME_REVIEW.md` |
| Branch | `workbuddy/round152-existing-round151-proxy-summary-audit` |
| Input file hash (source) | `410_reg_summary.out`, SHA-256 `1dc16f56…` (manifest-identical) |
| Raw summary uploaded | **No** |
| Raw FDT uploaded | **No** |
| Serial / IMEI / MAC / panel ID | **Not included** |
| Device operations this round | **None** |

Nothing outside `r151-root-readonly/evidence/{raw,private,meta}` was read. No device was contacted. No state was changed anywhere.

Per §7, this report was uploaded, read back through the git object channel and byte-compared against the local file. **STOP — no new round started.**
