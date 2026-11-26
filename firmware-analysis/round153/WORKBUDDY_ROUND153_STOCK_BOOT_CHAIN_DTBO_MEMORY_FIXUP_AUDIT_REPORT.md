# WORKBUDDY ROUND153 — Stock boot-chain / DTBO / ABL memory-fixup audit

**Executor:** WorkBuddy Agent (local Agent 1) only.
**Branch:** `workbuddy/round153-stock-boot-chain-dtbo-memory-fixup-audit`
**Device class:** Huawei MatePad 11 (2021) DBY-W09 / HWDBY / KONA / SM8250.
**Candidate under review:** ACK `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`, content tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
**Task type:** existing-artifact, read-only firmware/boot-chain audit. **No device access. No build. No patch. No flash. No boot.**

**Final outcome: `STATIC_BOOT_CHAIN_AUDIT_COMPLETE — ABL ARTIFACT ABSENT`.**

`COMPLETE` covers tasks A, B and D plus the parts of C that the corpus can answer. Task C is *not* closed: no ABL/XBL binary exists in this agent's workspace, so §7 records the unresolved contract instead of inferring bootloader behaviour.

---

## 0. The four answers

| # | Question | Answer | Basis |
|---|---|---|---|
| 1 | Are DTBO Entries 2 and 8 **fully** identical? | **No.** They differ in exactly **5 properties + 1 duplicated fragment**. Every UFS / PMIC / regulator / RPMh / power-domain payload *is* identical (142 of 144 fragments byte-identical). | §3 |
| 2 | Does live evidence support Entry 2 as the actually selected overlay? | **Yes — five independent lines**, including two that Entry 8 alone would have changed. | §4 |
| 3 | Is the candidate DTS comment (`0x206a` / Entry 8) wrong, stale, or unresolved? | **Wrong for the audited unit.** `0x206a` is Entry 8 = variant `VG`; this unit boots Entry 2 = `0x200e` = variant `VD`. The comment's *causal clause* ("selected by board-id") is also unsupported. | §5 |
| 4 | Is there evidence ABL fills all three RAM windows into a **replacement** DTB? | **No — and the premise fails.** The handed-off tree is the stock base DTB with **0 base-only nodes** (no replacement). The three windows do appear, and they are **not** attributable to any DTBO fragment, so a non-overlay boot-chain mutation is demonstrable — but naming that layer "ABL" requires the binary, which is absent. | §6, §7 |

**One line for the decision log:** the stock chain demonstrably rewrites `/memory` (1 zero tuple → 3 tuples, plus a new `ddr_device_type`) on a base tree it does **not** replace, and it never touches `/reserved-memory` — so the candidate must author its own carveouts and must not assume the boot chain will supply RAM safely.

---

## 1. Task A — inventory of existing firmware artifacts

### 1.1 What exists in this agent's own workspace

All firmware bytes used this round come from the ROUND2 extraction directory, which is this agent's own prior product and carries its own manifests. Nothing was re-downloaded, and no other agent's workspace was entered.

| Artifact | Path (relative to `D:\DBY-W09_FirmwareAnalysis_round2`) | Size (B) | SHA-256 |
|---|---|---:|---|
| Stock `dtbo.img` | `payloads/dtbo.img` | 25 165 824 | `51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c` |
| Stock `boot.img` (contains base DTB) | `payloads/boot.img` | 100 663 296 | `027f88fd6f318523925ca27a4d681d17a9bbca904b0c471ccc05e651d3da19b8` |
| Base DTB slot as declared by the boot header | inside `boot.img` @ `0x15bc000` | 1 664 243 | `1478a522c20fa2ce455bf0200d4b364ee69babb5b5f95d620ae9723f22db754b` |
| — DTB #0 `kona v2.1` (the one actually used) | extracted this round | 556 524 | `df2730f3d2e9bdabad874c3ef7399534…` |
| — DTB #1 `kona v2` | extracted this round | 556 520 | `f3dcba83e73f4d868e8e069369eb499e…` |
| — DTB #2 `kona v1` | extracted this round | 551 026 | `6cda673986bf814c9f118aa129e3e85f…` |

Recomputed hashes match the ROUND2 manifest `selected_images_sha256.csv` exactly for both `dtbo.img` and `boot.img`, so the artifacts are provenance-consistent with the report corpus that cites them.

**Provenance record as written by the producing run** (`summary.json`): `SourceMode = EXTRACTED_DIRECTORY_READ_ONLY`, `SourceName = images`, `InventoryRows = 43`, `ExtractedBootRelatedImages = 15`, `Safety = "Local read-only package inspection only; no device connection or partition writes."` `payloads/` holds 15 files.

### 1.2 Bootloader artifacts — absent

| Artifact | Status in this workspace |
|---|---|
| `abl.img` / `abl.elf` / `abl.mbn` | **ABSENT.** The 43-row package inventory contains **no** `abl*` entry at all. |
| `xbl.elf` | **ABSENT.** |
| `xbl.img` (4 018 176 B) | **Not retained.** Present as an inventory row only; the file was never copied into `payloads/`. |
| `xbl_config.img` (4 325 376 B) | **Not retained.** Inventory row only. |
| firmware update archive / `UPDATE.APP` | **ABSENT** from this workspace. |

This is not a new finding: ROUND36 `A-32` already recorded *"ABL binary bytes in the corpus: none"*, and `A-31` separately recorded that an `abl` partition exists **on the device** and was never dumped. Task C is therefore constrained by artifact availability, not by choice.

**Per taskbook §3C last sentence, and per ROUND36's `D`-grade rule, no ABL behaviour is inferred anywhere in this report.**

---

## 2. Task B.1 — DTBO table revalidation

Header re-parsed from `dtbo.img` bytes:

| Field | Value |
|---|---|
| magic | `0xd7b7ab1e` (`ANDROID_DTBO`) |
| `total_size` | **2 963 810** (= sum of the 9 payloads; last payload ends exactly at this offset, 0 trailing bytes) |
| `header_size` / `entry_size` | 32 / 32 |
| `entry_count` | **9** |
| `entries_offset` | 32 |
| `page_size` | 4096 |
| `version` | 0 |

All nine entries, re-derived from the table rather than copied:

| Entry | dtb_size | dtb_offset | table `id` | table `rev` | `custom[4]` | payload FDT magic | SHA-256 (first 8) |
|---:|---:|---:|---|---|---|---|---|
| 0 | 329 044 | 320 | `0x0` | `0x0` | all 0 | `0xd00dfeed` | `6940ce11` |
| 1 | 329 352 | 329 364 | `0x0` | `0x0` | all 0 | `0xd00dfeed` | `685a837e` |
| 2 | 329 240 | 658 716 | `0x0` | `0x0` | all 0 | `0xd00dfeed` | `0633a6fb` |
| 3 | 329 098 | 987 956 | `0x0` | `0x0` | all 0 | `0xd00dfeed` | `e68e5a48` |
| 4 | 329 340 | 1 317 054 | `0x0` | `0x0` | all 0 | `0xd00dfeed` | `86699105` |
| 5 | 329 356 | 1 646 394 | `0x0` | `0x0` | all 0 | `0xd00dfeed` | `699df895` |
| 6 | 329 356 | 1 975 750 | `0x0` | `0x0` | all 0 | `0xd00dfeed` | `fca5a7a8` |
| 7 | 329 352 | 2 305 106 | `0x0` | `0x0` | all 0 | `0xd00dfeed` | `0a57a7f8` |
| 8 | 329 352 | 2 634 458 | `0x0` | `0x0` | all 0 | `0xd00dfeed` | `a7946352` |

**Every `dt_table_entry.id` / `.rev` / `custom[]` is zero.** The board variant therefore cannot be carried by the DTBO table header — it can only come from each overlay's own root `qcom,board-id` (and the Huawei `rootparam` payload). This matters for §5: any statement of the form "the DTBO is selected by the table's board-id" is structurally impossible for this image.

### 2.1 The nine variants, from the overlays themselves

| Entry | nodes | fragments | root `qcom,board-id` | `qcom,board_name` | `wifi,pubfile_id` |
|---:|---:|---:|---|---|---|
| 0 | 1 687 | 143 | `0x2008,0x0` | `DBY_W09_VA` | `dby_lx9` |
| 1 | 1 690 | 145 | `0x2068,0x0` | `DBY_W09_VF` | `dby_ddr_lx9` |
| **2** | **1 688** | **144** | **`0x200e,0x0`** | **`DBY_W09_VD`** | **`dby_lx9`** |
| 3 | 1 686 | 143 | `0x2010,0x0` | `DBY_W09_VC` | `dby_lx9` |
| 4 | 1 689 | 144 | `0x200a,0x0` | `DBY_W09_VB` | `dby_lx9` |
| 5 | 1 690 | 145 | `0x202e,0x0` | `DBY_W09_VI` | `dby_fem_vi_lx9` |
| 6 | 1 690 | 145 | `0x206e,0x0` | `DBY_W09_VH` | `dby_fem_5g_lx9` |
| 7 | 1 690 | 145 | `0x2030,0x0` | `DBY_W09_VE` | `dby_ddr_lx9` |
| **8** | **1 690** | **145** | **`0x206a,0x0`** | **`DBY_W09_VG`** | **`dby_fem_lx9`** |

Board-id → decimal, for cross-check against ROUND36 `A-35` (which listed 8200 / 8296 / 8206 / 8208 / 8202 / 8238 / 8302 / 8240 / 8298):

`0x2008`=8200, `0x2068`=8296, `0x200e`=**8206**, `0x2010`=8208, `0x200a`=8202, `0x202e`=8238, `0x206e`=8302, `0x2030`=8240, `0x206a`=**8298**.

**Nine-for-nine agreement with the published independent inventory** — all nine board-ids, all nine `board_name` values and the entry order line up with ROUND36 `A-35`'s "nine hardware variants VA..VI".

Note the Wi-Fi profile is **not** a proxy for the variant family: `dby_lx9` is shared by entries 0, 2, 3, 4, while `dby_ddr_lx9` appears at 1 and 7, `dby_fem_vi_lx9` at 5, `dby_fem_5g_lx9` at 6 and `dby_fem_lx9` only at 8. Reading a variant from the Wi-Fi string alone would be wrong for six of nine entries.

---

## 3. Task B.2 — Entry 2 vs Entry 8, entire payload

Method: both overlays parsed to full path→property maps (all 4-byte and string properties included, no name filter), then compared on the union of paths.

| Measure | Entry 2 | Entry 8 |
|---|---:|---:|
| nodes | 1 688 | 1 690 |
| fragments | 144 | 145 |
| distinct resolved fragment targets | 73 | 73 |
| fragments with unresolved target | 0 | 0 |
| payload bytes | 329 240 | 329 352 |
| byte-identical? | **No** | |

### 3.1 Complete difference set

Shared nodes: 1 688. Property differences on shared nodes: **5**. Node-set difference: **2 nodes**.

| # | Location | Property | Entry 2 | Entry 8 | Reading |
|---:|---|---|---|---|---|
| 1 | `/` (overlay root) | `qcom,board-id` | `<0x200e 0x0>` | `<0x206a 0x0>` | variant selector |
| 2 | `/fragment@136/__overlay__` → `/huawei_wifi_info` | `wifi,pubfile_id` | `dby_lx9` | `dby_fem_lx9` | WLAN front-end-module profile |
| 3 | `/fragment@143/__overlay__` → `/rootparam` | `qcom,board_name` | `DBY_W09_VD` | `DBY_W09_VG` | variant name |
| 4 | `/fragment@143/__overlay__` → `/rootparam` | `qcom,boardid` | `u32 <8,2,0,6>` (= 8206) | `u32 <8,2,9,8>` (= 8298) | variant id, digit-encoded |
| 5 | `/__fixups__` | `huawei_slpi_sensor` | `/fragment@135:target:0` | `/fragment@135:target:0` **+ `/fragment@144:target:0`** | Entry 8 re-applies the sensor overlay |
| 6 | node `/fragment@144` + `/fragment@144/__overlay__` | — | absent | `als_para_select = "old_struct"` | duplicate of Entry 8 `fragment@135` |

`hardware_version` is `SH1DBSLM` in **both** entries, and `huawei,modem_id` is the same generic sentinel in both — neither discriminates the variant. `qcom,product_name` is `DBY-W09` in both.

### 3.2 What is *not* different

Fragment-by-fragment subtree comparison (each fragment plus its whole `__overlay__` subtree, all properties, raw bytes):

| Measure | Value |
|---|---:|
| Entry 2 fragments | 144 |
| fragments byte-identical to Entry 8 | **142** |
| fragments that differ | **2** — `/fragment@136` (Wi-Fi profile) and `/fragment@143` (`rootparam` identity) |
| Entry 8 fragments | 145 (the extra one is `/fragment@144`) |
| fragments whose target resolves | **144 / 144** (Entry 2), **145 / 145** (Entry 8), 73 distinct targets each |

The 142 identical fragments cover 71 of the 73 targets — including **every** UFS host/PHY fragment, every PMIC/SPMI fragment, every `rpmh-regulator-*` fragment, every GDSC and `power-domains` touch point, and every clock/reset/interconnect fragment. No fragment in either entry modifies `clocks`, `resets`, `power-domains`, `interconnects`, `phys` or `phy-names`.

This round therefore **confirms** ROUND138 §3's conclusion ("functionally identical for storage rails, PMIC, regulators and power domains") and supplies the missing quantifier: the difference is confined to **5 properties plus one duplicated fragment**, none of which is a storage, PMIC, regulator or power-domain property.

---

## 4. Task B.3 — which entry the live boot actually used

`androidboot.dtbo_idx=2` is only one line. Five independent lines were assembled; the last two would each have been *different* had Entry 8 been applied.

| # | Observation | Live value | Entry 2 predicts | Entry 8 predicts | Source |
|---:|---|---|---|---|---|
| 1 | `androidboot.dtbo_idx` | **2** | 2 | 8 | ROUND151 `101_cmdline.out` |
| 2 | root `qcom,board-id` | **`<0x200e 0x0>`** | `0x200e` | `0x206a` | live FDT `/` |
| 3 | `/rootparam` `qcom,board_name` | **`DBY_W09_VD`** | `DBY_W09_VD` | `DBY_W09_VG` | live FDT |
| 4 | `/rootparam` `qcom,boardid` | **`<8,2,0,6>`** | `<8,2,0,6>` | `<8,2,9,8>` | live FDT |
| 5 | `/huawei_wifi_info` `wifi,pubfile_id` | **`dby_lx9`** | `dby_lx9` | `dby_fem_lx9` | live FDT |

Absence check over the entire 800 316-byte live blob: `DBY_W09_VG` occurs **0 times**, `dby_fem_lx9` occurs **0 times**. The Entry-8 fingerprint is not merely unselected — it is *absent from the handed-off bytes*.

`als_para_select = "old_struct"` is present at `/huawei_slpi_sensor` in live, which is **also** what Entry 2 sets, through `fragment@135`. Entry 8 sets the same value twice (`fragment@135` and `fragment@144`). This property therefore does **not** discriminate, and must not be cited as evidence for Entry 8 (see §9.1).

**Selection index vs board-id metadata.** These are two different things and are kept separate here:
- the *index* is what `dtbo_idx=2` reports, and it is an index into the 9-entry table;
- the *board-id* is a property inside each overlay's root, and the table's own `id`/`rev` fields are all zero (§2).

Because the base DTB declares `qcom,board-id = <0 0>` (§6) and no entry carries an msm-id, the selector cannot be reading the base DTB's board-id. Where the selector *does* get 0x200e from is exactly the unresolved contract of §7 — and is the reason §5 rejects the candidate comment's causal clause.

---

## 5. Task B.4/B.5 — the candidate DTS comment

The candidate source cited in the corpus (`huawei-dby-w09.dts`, 343 lines) states at lines 35–36:

> `* Keep the SoC DTB board-id at zero; the separate DBY-W09 DTBO is`
> `* selected by board-id 0x206a and fills /rootparam for Huawei ABL.`

with `qcom,board-id = <0 0>;` at line 39.

| Claim in the comment | Verdict | Evidence |
|---|---|---|
| "DTBO … selected by board-id **0x206a**" | **Wrong for the audited unit.** `0x206a` is Entry 8, variant `VG`. This unit runs Entry 2 = `0x200e`, variant `VD`, and no Entry-8 fingerprint exists in the live blob. | §4 lines 1–5 |
| "Keep the SoC DTB board-id at zero" | **Consistent with stock.** The stock base DTB also declares `<0 0>`; the candidate is faithfully copying shipped behaviour. | §6.1 |
| "…is selected by board-id" (mechanism) | **Unsupported.** All nine table `id`/`rev` are zero, the overlays carry no `qcom,msm-id`, and the base board-id is `<0 0>`. A board-id comparison against the base DTB cannot produce the observed selection. | §2, §6.1 |
| "…and fills `/rootparam` for Huawei ABL" | **Structurally correct, attribution unproven.** `/rootparam` does get filled, and no DTBO fragment targets `/` itself, so the root-level identity does come from the overlay root merge. Whether "Huawei ABL" is the filler is not established. | §4, §7 |

### 5.1 Recommended correction (recommendation only — no file was edited)

Two independent defects, so two edits:

1. **Value.** Replace `0x206a` with **`0x200e`** and `Entry 8` with **`Entry 2`**, *if and only if* the target unit is the audited unit (`VD`). If the candidate is aimed at a `VG` unit, then `0x206a` is right and **this audited device is the wrong reference** — in which case the DTBO comparison in §3 still holds, but every live-tree statement in §4 would have to be re-derived on a `VG` unit. This round has no authorization to probe hardware variant, so it does not choose between the two.
2. **Mechanism.** Delete the clause "selected by board-id" or mark it `UNKNOWN`. Nothing in the artifacts supports it, and keeping it will mislead the next round into assuming that setting `qcom,board-id` in the candidate DTS influences DTBO selection.

---

## 6. Task C.4 — base DTB placeholder vs live FDT

### 6.1 The base DTB slot actually contains three concatenated DTBs

`boot.img` is Android boot header v2 (`header_version = 2`, `header_size = 1660`, `page_size = 4096`, `kernel_size = 22 264 379`, `ramdisk_size = 519 986`). Header `dtb_size = 1 664 243`, `dtb_addr = 0x1f00000`. The DTB region starts at file offset `0x15bc000` and holds **three** contiguous FDTs with zero inter-DTB gaps and 173 trailing bytes:

| # | offset | size | `/model` | `qcom,msm-id` | root `qcom,board-id` | `/memory.reg` | `/reserved-memory` children |
|---|---:|---:|---|---|---|---|---:|
| 0 | `0x15bc000` | 556 524 | `Qualcomm Technologies, Inc. kona v2.1 SoC` | `<0x164 0x20001>` | `<0 0>` | 4 cells, all zero | 37 |
| 1 | `0x1643dec` | 556 520 | `… kona v2 SoC` | `<0x164 0x20000>` | `<0 0>` | 4 cells, all zero | 37 |
| 2 | `0x16cbbd4` | 551 026 | `… kona v1 SoC` | `<0x164 0x10000>` | `<0 0>` | 4 cells, all zero | 37 |

All three are generic Qualcomm templates: `#address-cells = 2`, `#size-cells = 2`, `/memory` carrying `device_type = "memory"` and `reg = <0 0 0 0>` — the zero-size placeholder named in the taskbook §1.3. **The candidate's `<0 0>` and its "one zero-size upstream placeholder" are therefore exactly the shipped template's shape, not an invention.**

### 6.2 The live tree is the base tree, not a replacement

| Measure | Value |
|---|---:|
| base (DTB #0) node paths | 3 471 |
| live node paths | 4 566 |
| **base-only** (in base, missing from live) | **0** |
| live-only (added by overlays) | 1 095 |
| shared | 3 471 |

**Set containment is total: every base node survives.** A wholesale substitution of a different DTB would have to reproduce all 3 471 paths byte-for-byte while also adding 1 095 overlay nodes — that is not a replacement, it is a merge. Root identity confirms the same document: live keeps `qcom,msm-id = <0x164 0x20001>`, which is DTB #0's value and is *not* present in any overlay root.

### 6.3 Attributing every base→live difference

Merging is only half the question. Every property difference on shared nodes was attributed to a fragment target (resolved through the base DTB's `__symbols__` table, since `__fixups__` values are symbol names, not paths):

| Bucket | Count |
|---|---:|
| property differences on shared nodes | **441** |
| — inside a subtree targeted by one of Entry 2's 144 fragments | 411 |
| — **not** explained by any fragment | **30** |
| fragments resolved | 144 (73 distinct paths, 0 phandle-only) |
| does any fragment target `/memory`? | **No** |
| does any fragment target `/reserved-memory`? | **No** |
| does any fragment target `/`? | **No** |

The 30 non-fragment differences decompose exactly:

| Group | n | Detail |
|---|---:|---|
| root identity | 3 | `compatible`, `model`, `qcom,board-id` — values equal to the overlay's **own root properties**, which merge onto the base root without a fragment |
| `/chosen` | 4 | `bootargs` extended, `linux,initrd-start`, `linux,initrd-end`, `kaslr-seed` added |
| `/firmware/android/fstab/*` | 21 | `status` `"ok"` → `"okay"` |
| **`/memory`** | **2** | `reg` 4 cells → 12 cells; `ddr_device_type = 0x7` **added** |

`/chosen` is the witness that the pre-Linux boot chain mutates this tree directly: live `bootargs` = the base DTB's 47-character `bootargs` **plus all 16 tokens of the `boot.img` header cmdline** plus bootloader-set `androidboot.*` (including `nokaslr`, `androidboot.verifiedbootstate=orange`). No fragment touches `/chosen`. So a non-DTBO, boot-chain-side mutation layer is **directly demonstrated**, not inferred.

### 6.4 The `/memory` delta itself

| | base DTB #0 | live |
|---|---|---|
| property set | `device_type`, `reg` | `ddr_device_type`, `device_type`, `reg` |
| `reg` bytes / cells | 16 / 4 | 48 / 12 |
| tuple 0 | `(0x0, 0x0)` — zero size | `(0x80000000, 0x39900000)` = 921 MiB |
| tuple 1 | — | `(0x200000000, 0x200000000)` = 8192 MiB |
| tuple 2 | — | `(0xc0000000, 0xc0000000)` = 3072 MiB |
| total | 0 MiB | 12 185 MiB |

This is consistent with ROUND151's independent `/proc/iomem` and `MemTotal` (11 984 584 kB ≈ 11.43 GiB after carveouts).

**Answer to "wholesale replacement / one-tuple size patch / indeterminate":**

- **Wholesale replacement: ruled out** — 0 base-only nodes, and `msm-id` is preserved.
- **One-tuple size patch: ruled out** — the tuple count went 1 → 3, and a property that did not exist (`ddr_device_type`) appeared. A size patch on the existing single tuple cannot produce either.
- **What the artifacts do prove:** the surviving base tree's own `/memory` node was rewritten in place to carry three windows plus a DDR-type property, by a layer that is *not* the DTBO application (no fragment targets `/memory`), on a tree that was *not* replaced.
- **What they do not prove:** which component that layer is. `ABL` is the conventional answer and is consistent with everything above, but consistency is grade `D`, and §7 explains why the corpus cannot promote it.

### 6.5 A consequence for the candidate: `/reserved-memory` is nobody else's job

The `/reserved-memory` subtree is **byte-identical** between base DTB and live: 38 nodes (parent + 37 children), **0** property differences, identical subtree fingerprint `66ddc0f82e9cd3f6` on both sides. The boot chain adds RAM but does **not** add, move or resize a single carveout.

The candidate DTS currently declines to reconstruct them (its own comment: *"Memory / HOS reserved-memory is deliberately not reconstructed here yet"*). That is a defensible deferral, but it must not be read as "the bootloader will supply them" — on the stock boot it demonstrably did **not**.

### 6.6 Second consequence: the packaging contract

The stock slot holds **three** DTBs and the header declares their aggregate size (`1 664 243`), with `dtb_addr = 0x1f00000`. A candidate build that emits one DTB, or that emits them in the wrong slot order, changes what the loader can select. This is a packaging question, not a DTS question, and it is listed in §8 because a candidate boot image cannot be assembled correctly without an answer.

---

## 7. Task C.1–C.3 — ABL evidence: unavailable, contract recorded

**No ABL/XBL artifact exists in this agent's workspace** (§1.2). Consequently:

| Taskbook item | Status |
|---|---|
| C.1 string/symbol search for `/memory`, `device_type=memory`, `fdt_setprop`, `memstart`, `dram`, memory-fixup routines | **NOT EXECUTED — no artifact to search.** Deliberately not simulated against an unrelated or private copy. |
| C.2 grade the evidence as symbol / disassembly / weak string | **N/A.** |
| C.3 do not claim the stock ABL patches a replacement DTB | **Honoured.** §6 states replacement is *ruled out*, and never asserts ABL authorship. |

**Unresolved contract (recorded, not guessed):**

1. What supplies the per-unit board id that DTBO selection compares against, given that the table `id`/`rev` are zero, the overlays carry no `msm-id`, and the base DTB says `<0 0>`?
2. Which component rewrites `/memory` — and does it key on `device_type = "memory"`, on the zero-size `reg`, on root `#address-cells`/`#size-cells`, or on nothing at all?
3. Does that component also add `ddr_device_type`, and is its absence in a candidate DTB benign?
4. Is the 3-window set derived from an on-die RAM partition table, from a boot-config partition, or from a hard-coded variant table?
5. Why do 21 `fstab` `status` strings change `"ok"` → `"okay"` between the base DTB and `/sys/firmware/fdt`? This matters for provenance: it shows the exposed blob is not a pristine copy of the loader's output. Its author is not identified here.

ROUND36 `A-38` records that a **public same-SoC-class reference** (`FreeABL` SM8250) implements `UpdateDeviceTree()` → `FdtPathOffset(fdt, "/memory")` → `AddMemMap()` rewriting the **existing** `/memory/reg`, and returns `EFI_NOT_FOUND` if `/memory` is absent. That is a grade `C` datapoint about a reference implementation, and it is *consistent* with §6.4 — but it is not this device's ABL and it is not used here to close anything.

---

## 8. Task D — what remains before a candidate boot package can be assembled

Non-device evidence, in the order that unblocks the most:

| # | Required evidence | Why it is blocking | Would close |
|---:|---|---|---|
| 1 | **An ABL image for this exact build** (`abl` partition dump, or `abl.elf`/`abl.img` from a package that has one) | Only artifact that can turn §6.4's "some boot-chain layer" into a code path, and §7.1's selector into a fact | §6.4 actor, §7.1–§7.4 |
| 2 | **A DTBO-selection + memory-fixup contract note** from a Huawei/Qualcomm document, or an ABL serial log from any boot of this SKU | Even one `dtbo_idx=` + RAM-map line would independently confirm the selector's input | §7.1, §7.2 |
| 3 | **Boot-image packaging spec for the candidate**: how many DTBs, concatenation order, declared `dtb_size`, `dtb_addr` | §6.6 — a single-DTB candidate changes loader selection semantics | §6.6 |
| 4 | **Whether the target unit is `VD` (`0x200e`) or `VG` (`0x206a`)** — from packaging/label evidence, not from a device probe | §5.1 decides between "fix the comment" and "wrong reference unit" | §5 |
| 5 | A 47th answer to `ddr_device_type`'s author and necessity (§7.5) | Determines whether the candidate DTS must declare it | §7.5 |

Not required, and explicitly **not** requested: another live read. The live tree was captured in ROUND151 at byte level and re-used here unchanged.

---

## 9. Corrections, and errors caught in this round

### 9.1 Corrections to prior rounds

| Target | Prior statement | This round |
|---|---|---|
| ROUND138 §3 | "entry 2 and entry 8 … only differences are the `rootparam` identity pair and the Wi-Fi pubfile selector, plus one duplicated sensor fragment" | **Confirmed and quantified**: exactly 5 properties + 1 duplicated fragment (2 nodes), out of 1 688 shared nodes. The claim was right; it is now falsifiable at property granularity. |
| ROUND138 §3 | "142 fragments carry byte-identical payloads" | **Reproduced** (142/144 for Entry 2; 71/73 targets). |
| ROUND36 `A-04`/`A-35` | live `/memory` decomposition "not established"; `dtbo_idx` selection "not established" | **Both now established** from the ROUND151 blob: 3 tuples at 2/2 cells, and Entry 2 by five independent lines. |
| ROUND36 `A-07` | cause of the 16 B → 48 B change "not established" | **Narrowed**: replacement ruled out, one-tuple patch ruled out, actor still open. |

### 9.2 Errors caught in this round, before publication

1. **"Only Entry 8 has `als_para_select`" — false.** My first two-entry comparison showed `fragment@144` as Entry-8-only, and I nearly reported the live `als_para_select` as a contradiction. Checking all nine entries showed Entry 2 sets the same value through `fragment@135`; Entry 8 merely sets it twice. Recorded here because a later round reading only §3 would re-make the mistake.
2. **`__fixups__` values are symbol names, not paths.** My first attribution pass resolved 0 of 144 fragments and therefore classified all 441 differences as "not overlay". The fix — resolve symbols against the base DTB's 1 753-entry `__symbols__` table — flipped the result to 411/30. The wrong version would have "proved" that overlays change almost nothing.
3. **Android boot header v2 field offsets.** `header_size` is at `1644`, `dtb_size` at `1648`, `dtb_addr` at `1652` (not `1648`/`1652` as first assumed). The first attempt mis-read the DTB slot; only the corrected offsets produced the 3-DTB structure of §6.1.
4. **A single-FDT parse was mistaken for the whole DTB slot.** `dtb_size = 1 664 243` but the FDT at that offset reports `totalsize = 556 524`. The declaration covers three concatenated DTBs, not one — a trap that would silently reduce "which base DTB was used" to a guess.

---

## 10. Boundaries honoured

- **No device access of any kind**: no ADB, no root, no fastboot, no recovery, no UART, no partition read, no reboot, no flash, no boot.
- **No source / DTS / DTBO / config / patch edits.** The candidate DTS was **read only**; §5.1 is a recommendation, not a change.
- **No build, no test.**
- **No other agent's workspace** entered, inspected, copied or reused. All inputs are this agent's own ROUND2 extraction plus published reports (ROUND36, ROUND138, ROUND151 in the local clone) and the candidate DTS already present in this agent's own prior round directory.
- **No raw binaries uploaded**: no ABL/XBL/DTB/DTBO bytes, no live FDT blob, no firmware images in this report — sizes, hashes, paths and decoded property values only.
- **No identifiers disclosed**: no serial, IMEI, MAC, panel ID or user-specific value appears here. `huawei,modem_id` is described only as "the same generic sentinel in all nine entries", never reproduced.
- **No bootloader-fixup claim from the live FDT alone** (§7).

---

## 11. Reproduction map

| Step | Script (this workspace) | Output |
|---|---|---|
| DTBO header + 9 entries | `r153-dtbo-audit/dtbo_parse.py` | §2 table |
| overlay extraction + root identity | `r153-dtbo-audit/extract.py` | §2.1 |
| Entry 2 vs 8 full diff | `r153-dtbo-audit/diff.py`, `detail.py` | §3 |
| 9-entry variant matrix | `r153-dtbo-audit/matrix9.py` | §2.1 |
| boot.img DTB slot scan | `r153-dtbo-audit/scan_fdt.py` | §6.1 |
| base DTB decode | `r153-dtbo-audit/basedtb.py` | §6.1 |
| base vs live node-set / memory | `r153-dtbo-audit/merge_shape.py`, `mem_compare.py` | §6.2–§6.5 |
| difference attribution | `r153-dtbo-audit/attrib.py` → `work/attrib.txt` | §6.3 |
| live variant fingerprints | `r153-dtbo-audit/live_check.py` | §4 |

Inputs are hash-pinned in §1.1; nothing in this round rewrote any of them.

**STOP.** No ROUND154 started.
