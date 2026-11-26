# ROUND154 — WorkBuddy Window B: independent patch / DTBO reproduction report

**Executor: WorkBuddy Window B (2号 Agent); separate WorkBuddy chat window from Window A.**

Both Window A and this window are WorkBuddy chat windows / execution contexts. No different AI product or different tool is claimed. This report is written by Window B from its own isolated candidate workspace; it does not rely on, enter, read or relabel Window A's workspace, temporary directory, build output, raw logs or private chat artifacts. The exact absolute workspace path is recorded only in Window B's private scratch logs (`<WB_WS>/logs/`, locally); this public report uses the sanitised prefix `<WB_WS>` / `<TREE>` / `<FROZEN_DTB>` and contains no user-specific identifier, raw firmware, serial, IMEI, MAC, panel ID, private log or partitiondump.

Task type: independent artifact/source reproduction and static DTB/DTBO compatibility test. **No device, ADB, root, fastboot, recovery, partition read/write, flash, reboot or candidate boot. No full kernel/Image build. No modification of the frozen base, prior build output, stock firmware, original DTBO or accepted source patch.**

---

## 0. Scope, evidence grade and provenance

| ID | Statement | Grade | Basis |
|---|---|---|---|
| A | Direct measurement performed in Window B's own isolated workspace this round | A |
| B | Independent local reproduction from Window B's own frozen artifacts (no other lane's files) | A |
| C | Report-derived cross-reference; the underlying original binary is not in Window B's permitted files | C |
| D | Blocked / not executable this round (state the exact reason) | D |

**Workspace isolation (all paths below are Window B lane artifacts):**

| Sanitised name | Role | Written to this round? |
|---|---|---|
| `<WB_WS>` | new isolated scratch worktree created this round (`round154-windowB`, under the Agent2/Window-B workspace) | yes — `src/`, `out/`, `logs/`, `dbg/`, `dtbo/` only |
| `<TREE>` | Window B's own frozen candidate source tree (`round140-agent2/tree`) | no — read-only |
| `<FROZEN_DTB>` | Window B's frozen candidate DTB (`round140-agent2/out-dtb/.../huawei-dby-w09.dtb`) | no — read-only |
| `<DTC>` | Window B's own frozen kernel-built `dtc` / `fdtoverlay` from `round140-agent2/out-dtb/scripts/dtc/` | no — read-only |
| `<STOCK_DTBO>` | stock `dtbo.img` from Window B's own local firmware-check directory (`MatePad11_HOS43_LocalCheck_20261123_230849/selected_files/dtbo.img`) | no — read-only; Entry 2 sliced into `<WB_WS>/dtbo/` |

The stock DTBO is **not** copied from Window A's raw/private artifact; it is a file already present in Window B's own permitted local check set. If it had not been available, §D would have been declared blocked rather than borrowed.

Toolchain: kernel's own two-stage DTS pipeline reproduced by hand — `gcc -E -nostdinc -I<TREE>/include -I<TREE>/arch/arm64/boot/dts -I<TREE>/arch/arm64/boot/dts/qcom -undef -D__DTS__ -x assembler-with-cpp`, then `<DTC> [-@] -I dts -O dtb`. This never writes into `<TREE>` or `<FROZEN_DTB>`.

---

## 1. [A — §3.A] Candidate identity correction

### 1.1 Independent hash and size (A)

| Measurement | Value |
|---|---|
| `<FROZEN_DTB>` size | **108 648 bytes** |
| `<FROZEN_DTB>` SHA-256 | **`cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e`** (64 hex) |
| Window B fresh rebuild from unmodified `<TREE>/.../huawei-dby-w09.dts` → `base.dtb` | 108 648 bytes, SHA-256 **`cab82fe…db77e`** — byte-identical to `<FROZEN_DTB>` |
| FDT header self-consistency | `totalsize == file size == 108 648`; version/last-comp fields consistent |

The rebuild is not a copy: it is `gcc -E` + `<DTC> -I dts -O dtb` over the copied board DTS, and it lands on the same 64-character digest. That independently validates both the frozen artifact and the Window B toolchain used later in §3.

### 1.2 The malformed inherited expectation (A)

| String | Length | Source | Verdict |
|---|---|---|---|
| `cab82fe3901dbb40533197eb48b2d99b08b46e5d5497ff1a6f688e9938db77e` | **63** | the "expected SHA-256" inherited by ROUND147/152/153 taskbooks and by `<FROZEN_DTB>`'s own build log | **not a legal SHA-256** (64 hex required) |
| `cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e` | **64** | Window B measurement; R140 Stage-B4 `:66`; R147 `:30,:41` | **true frozen candidate identity** |

First divergence is at **offset 11**: the 63-char string has `…3901d b b405…`, the measured value has `…3901b d b405…`. The 63-char string is **not** obtainable from the 64-char value by deleting exactly one character (checked: no single-character deletion reproduces it), so the discrepancy is a transcription/declaration defect, not a trivial dropped digit. Per taskbook §3.A.3 this report does **not** "repair" a hash by guessing, inserting or dropping characters.

### 1.3 Resolution against the three required references (A)

| Reference | Its recorded value | Agreement with Window B measurement |
|---|---|---|
| malformed 63-char expectation (ROUND147/152/153 lineage) | 63 hex, `…3901dbb405…` | **no** — cannot match any file; length invalid |
| `<FROZEN_DTB>`/R140 `stage-b4-dtb-build-and-structure.log:65-68` | `:65 dtb_size=108648 expected_size=108648 match=YES`; `:66 dtb_sha256=cab82fe3901bdb40533197eeb48…db77e`; `:67 expected_sha256=cab82fe3901dbb40…` (63 char); `:68 DTB_SHA_MATCH=NO` | **yes** for the `:66` measured value (byte-identical to Window B); the `MATCH=NO` at `:68` is explained entirely by the 63-char expected value |
| ROUND147 published identity (`r147:29-30`, `:41`) | `:29 size 108648`; `:30` SHA-256 `cab82fe3901bdb40533197eeb48…db77e`; `:41` R140 `:66` same digest | **yes** for the digest value itself |

**Correction to inherited literature (disclosed, not silently reconciled):** R147 `:30` says the digest "equals the taskbook and START_PROMPT value **exactly**". That is an overstatement: R147's *printed* 64-char digest equals the R140 measured value, but the *taskbook/START_PROMPT expected value* is the 63-char malformed string, which cannot equal a 64-char digest. R152 and ROUND153 inherited the same expectation; ROUND153 already flagged the length defect (F-1). Window B confirms that finding from an independent rebuild and states the correct, usable identity: **`cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e`, 108 648 bytes.**

**Identity verdict: PASS** (size + FDT self-consistency + 64-char digest, all independently reproduced); **the 63-char expectation is UNVERIFIABLE by construction and is rejected as an identity criterion.** No identity claim rests on "repairing" it.

---

## 2. [A — §3.B] RAM and reserved-memory reproduction

All numbers in this section were recomputed by Window B from `<TREE>` source and the candidate DTB DTB (`base.dtb` = byte-equal to `<FROZEN_DTB>`); nothing was taken on trust from ROUND153's prose.

### 2.1 Exactly one root memory node, size zero (A)

| Property | Result |
|---|---|
| Nodes in tree | 905 (base / patched); `<FROZEN_DTB>` also 905 |
| `device_type = "memory"` nodes | **exactly 1**: `/memory@80000000` |
| Its `reg` in the **unpatched frozen** candidate | `<0x0 0x80000000 0x0 0x0>` — 4 cells, **size = 0** |
| Source of the placeholder | `<TREE>/arch/arm64/boot/dts/qcom/sm8250.dtsi:683-687`; `:685` comment "We expect the bootloader to fill in the size" |
| 18 `<reserved-memory>` children named `memory@…` | none carries `device_type = "memory"` — they are reservations, not RAM declarations |
| `#address-cells/#size-cells` at root | `ac=2 sc=2` → 2/2 cell tuple form |

The size-zero tuple is the reason ROUND151/152 classified the RAM declaration as **CONDITIONAL** rather than proven: the DTB itself declares 0 bytes of usable RAM at that node.

### 2.2 Three live RAM windows (A; window values C where report-derived)

Window bounds are the three ROUND151 live windows (cross-reference grade C: Window B has no original RAM capture of its own; the values are taken from the published R151 §3.5 table). The arithmetic, ordering, overlap, alignment and overflow checks on them are grade A.

| # | base | size | end | MiB | 4 KiB align | 64 KiB align |
|---|---|---|---|---|---|---|
| 1 | `0x0000000080000000` | `0x0000000039900000` | `0x00000000b9900000` | 921 | yes | yes |
| 2 | `0x00000000c0000000` | `0x00000000c0000000` | `0x0000000180000000` | 3 072 | yes | yes |
| 3 | `0x0000000200000000` | `0x0000000200000000` | `0x0000000400000000` | 8 192 | yes | yes |

| Check | Result (A) |
|---|---|
| Total | `0x2f9900000` = **12 185 MiB** exactly (921 + 3 072 + 8 192) |
| Ordering | strictly ascending ✔ |
| Overlap | none ✔ |
| Gap 1 | `0xc0000000 − 0xb9900000` = `0x6700000` = **103 MiB** |
| Gap 2 | `0x200000000 − 0x180000000` = `0x80000000` = **2 048 MiB** |
| 64-bit representation | base/size split into hi/lo cells: `0x200000000` → `<0x2 0x0>`; `0x400000000` end fits in 64-bit, no wrap ✔ |
| Max end | `0x400000000` (16 GiB boundary), no overflow ✔ |

### 2.3 Eighteen reserved-memory intervals (A)

| Check | Result |
|---|---|
| `<reserved-memory>` children | **18** |
| Sum of `reg` sizes | `0xfe9c000` = **254.609375 MiB** |
| Union of intervals | `0xfe9c000` = **254.609375 MiB** in **5** merged segments |
| Sum == union | **yes** → zero overlap among the 18 ✔ |
| Containment | every interval lies inside window 1 (`0x80000000…0xb9900000`); none outside the three windows ✔ |
| `no-map` | all 18 carry `no-map` |

Byte-level spot check (A): `0x8be00000 + 0x100000 = 0x8bf00000` and `0x8bf00000 + 0x4600000 = 0x90500000`, matching the declared node boundaries exactly.

**All consumers / phandle references (A) — memory-region style, 6 total:**

| Consumer node | `memory-region` target |
|---|---|
| `/smem` | `/reserved-memory/memory@80900000` |
| `/soc@0/gpu@3d00000/zap-shader` | `/reserved-memory/memory@8681a000` |
| `/soc@0/remoteproc@5c00000` | `/reserved-memory/memory@88c00000` |
| `/soc@0/remoteproc@8300000` | `/reserved-memory/memory@87800000` |
| `/soc@0/video-codec@aa00000` | `/reserved-memory/memory@86e00000` |
| `/soc@0/remoteproc@17300000` | `/reserved-memory/memory@8a100000` |

`cdsp_secure_heap` (70 MiB) at `<TREE>/.../sm8250.dtsi:862` has **no** `memory-region`/phandle reference from any consumer; the CDSP remoteproc node is `disabled` and points at a different address (`0x87800000`). This reproduces ROUND153's structural finding. Window B takes no position on whether the reservation should be kept — deleting an unreferenced reservation is a design decision outside this report, so it is **retained** in the reproduction.

### 2.4 Stock-only fixed coverage / dynamic pools (C — report-derived)

The original stock FDT binary is **not** in Window B's permitted files, so the stock-only numbers cannot be re-measured here. They are carried only as published cross-reference (R151/R152/ROUND153): stock static sum 232.689 MiB; 17 address-exact matches; +70 MiB newly placed `cdsp_secure_heap`; −40.080 MiB stock-only fixed coverage (35 + 1 + 4 + 0.078125 + 0.001953125 MiB; the 8 MiB `disp_rdump` is a splash subset and is not counted); 12 dynamic pools. Closure: `232.689 − 40.080 − 8 + 70 = 254.609` and `224.689 − 40.080 + 70 = 254.609`, residual 0.000 — consistent with Window B's independently recomputed candidate sum/union of 254.609375 MiB. **No stock-derived number is presented as Window B measurement.**

**§B verdict: PASS** for all directly measurable candidate properties (one memory node, size-zero tuple, window arithmetic, 18 reservations, sum/union/containment, 6 consumers, cdsp status). Stock cross-reference is explicitly grade C.

---

## 3. [A — §3.C] Reproduce the RAM-only patch independently

### 3.1 Scope discipline

Window A's patch diff/blob/commit was **not published** when this round was executed (§5). Per taskbook §3.C ("after Window A publishes its patch diff … independently apply the same intended change"), Window B did **not** read, copy or align to any Window A patch. It applied the *stated intent* from its own unmodified frozen base: alter only the existing `/memory@80000000/reg`, three 2/2 tuples; no second memory node; no change to the 18 reservations; keep `qcom,board-id = <0 0>`.

### 3.2 The applied change (A)

Insertion point: immediately after `rootparam: rootparam { };` at `<TREE>/.../huawei-dby-w09.dts:47`; the patch block begins at `<WB_WS>/src/patched.dts:51`. It uses the **same node path** as `sm8250.dtsi:683-687` (property merge, not a new node):

```
memory@80000000 {
    reg = <0x0 0x80000000 0x0 0x39900000>,
          <0x0 0xc0000000 0x0 0xc0000000>,
          <0x2 0x0        0x2 0x0>;
};
```

Cells expand to `[0, 0x80000000, 0, 0x39900000, 0, 0xc0000000, 0, 0xc0000000, 2, 0, 2, 0]` — 12 cells = 3 tuples × 4.

### 3.3 Source and DTB identity (A)

| Artifact | Size | SHA-256 | dtc warnings |
|---|---|---|---|
| `src/base.dts` (copy of frozen board DTS) | 15 437 B | `70b86877ec8fee3dfdb9dffc50f2ab6dd9eb925f59fa346e81c3bf67ee010ddc` | — |
| `src/patched.dts` | 15 800 B | `e5c6a80382d582ab3a95078b84bb7a0d4a79eac58f1bd84b252be313affc83ef` | — |
| `out/base.dtb` | 108 648 B | `cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e` | 32 |
| `out/patched.dtb` | **108 680 B** (+32) | `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` | 32 (no new warning class) |
| `out/base_at.dtb` (`-@`, scratch experiment) | 145 849 B | `0a4a471c8cea3093c25a4da6b26d81cddbc6bfeeb166ac9071476bb3a5e1f4e7` | 32 |
| `out/patched_at.dtb` (`-@`, scratch experiment) | 145 881 B | `235663547667c06871c1f2b7a2977395905e0f49ed4b6b543602477316e35ef7` | 32 |

The 32 dtc warnings are the frozen tree's pre-existing `avoid_unnecessary_addr_size` / `unique_unit_address` set; patched build introduces **no new warning** (identical warning count and text class). This is the toolchain-determinism answer required by §3.C: no nondeterministic size/hash drift was observed — base rebuild is byte-identical to the frozen DTB, and the only structural delta is the one intended property.

### 3.4 Structural diff (A)

| Check | Result |
|---|---|
| `<FROZEN_DTB>` vs Window B `base.dtb` | **0** differing properties, 905 nodes each — byte-equal structure ✔ |
| `base.dtb` vs `patched.dtb` | **1** changed property: `/memory@80000000 reg` (size-zero → three tuples); node count 905 → 905 ✔ |
| Reserved-memory child count | 18 → 18; property sets **identical** ✔ |
| Reserved sum/union | unchanged `0xfe9c000` = 254.609375 MiB ✔ |
| Second memory node created? | **no** — tree still has exactly `['/memory@80000000']` ✔ |
| `qcom,board-id` | still `u32[0, 0]` (selector proof not attempted) ✔ |
| `qcom,msm-id` | `u32[356, 131073]`, untouched ✔ |
| `compatible` / `model` | `huawei,dby-w09` + `qcom,sm8250`; "Huawei MatePad 11 (2021) DBY-W09" — untouched ✔ |
| `-@` symbol export (scratch only) | 514 symbols; `rootparam = /rootparam`; `/rootparam` phandle **514** |

Window B did **not** edit the accepted source patch, the frozen tree, or any prior build output; `patched.dts` is a new file in `<WB_WS>/src/`. The comment at `<TREE>/.../huawei-dby-w09.dts:316` ("The final ABL-provided RAM tuple and reservation map remain UNKNOWN") still describes the frozen source and was deliberately **not** modified — updating that comment is a documentation decision for whoever owns the publishable patch, not part of this read-only reproduction.

**§C verdict: PASS** for independent application and byte-level delta verification; **comparison against Window A's patch identity is BLOCKED (§5)** because that lane had not published at execution time.

---

## 4. [A — §3.D] Candidate-vs-stock DTBO external fixup compatibility

### 4.1 Stock Entry 2 inventory (A)

| Property | Value |
|---|---|
| `<STOCK_DTBO>` image | 25 165 824 bytes |
| Container header | `magic=0xd7b7ab1e`, `total=2 963 810`, header 32 B, entry 32 B, `entry_count=9`, entries at offset 32, page 4096, version 0 |
| Entry 2 slice | offset `0xa0d1c`, size **329 240 B**, written to `<WB_WS>/dtbo/entry2.dtbo` (scratch copy of a read-only source) |
| Entry 2 root | 1 688 nodes / 8 480 props; `compatible=qcom,kona-qrd,qcom,kona,qcom,qrd`; `qcom,board-id = u32[8206, 0]` → matches the ROUND138 entry-2 identity (8206 = 0x200E) |
| Fragments | **144** |
| Fragment target mechanism | **144** use `target = <0xffffffff>` (external fixup); **0** use `target-path` |
| `__fixups__` distinct external symbols | **166** |
| Fixup use split | 73 symbols used as fragment targets, 102 used as property references (a symbol may be both) |

An earlier classification pass (`fixup154.py`) split 166 into 73 target + 93 property and reported 0 resolvable fragment targets; the corrected pass (`fixup154b.py`) fixes the property count to 102 and the target resolution to 6/73. The corrected numbers are used throughout this report; the discrepancy is a counting-method defect in Window B's scratch script, disclosed rather than hidden.

Fixup value shape example (verbatim from the parsed blob): `BOB → /fragment@46/__overlay__/wcd938x-codec:cdc-vdd-mic-bias-supply:0`; `S4A →` four paths at `fragment@44`/`fragment@46`; `antenna_board_detect → /fragment@115:target:0`. This confirms the overlay is external-fixup-based throughout: every fragment's `target` is the placeholder `0xffffffff`, to be filled from the base's `__symbols__`.

### 4.2 Resolution against baseline candidate (A)

| Base tested | Symbols exported | Bindable fixups |
|---|---|---|
| `base.dtb` (frozen reproduction, **no `-@`**) | **0** (`/__symbols__` absent) | **0 / 166** |

The frozen candidate has no `/__symbols__`, no `/__fixups__` and no `/__local_fixups__`, and `/rootparam` is an empty node with **no phandle**. An external-fixup overlay therefore has no symbol table to resolve against. ROUND153 F-13 independently observed the same absence; Window B confirms it from its own rebuilt base.

### 4.3 Scratch `-@` experiment (A — not the accepted source)

With `<DTC> -@` on the unchanged board DTS in `<WB_WS>/out/base_at.dtb`:

| Metric | Result |
|---|---|
| Exported symbols | **514** |
| `rootparam` | exported → `/rootparam`; phandle **514** |
| Fixups resolvable | **10 / 166** |
| Resolved symbols | `intc, mdss_dsi0, mdss_dsi1, mdss_mdp, pdc, rootparam, sdhc_2, soc, spmi_bus, tlmm` |
| Unresolved | **156** (full list preserved in `<WB_WS>/logs/unresolved-entry2.txt`) |
| Target symbols resolved | **6 / 73**: `spmi_bus, soc, mdss_mdp, tlmm, sdhc_2, rootparam` |
| Property symbols resolved | **7 / 102** (subset of the 10 above) |
| Fragments whose target symbol resolves | **57 / 144**; **87 fail** |
| Fragments still carrying `0xffffffff` target in the source blob after `-@` base | **144 / 144** (the placeholder is in the overlay source; `-@` only supplies a base symbol table — it does not rewrite the overlay) |

Representative unresolved symbols (first 20 of 156): `BOB, S4A, antenna_board_detect, audio_apr, battery_core, battery_fault, battery_ui_capacity, bolero, bt_en_sleep, btkb_led, cam_cci0, cam_cci1, cam_sensor_active_rear, cam_sensor_active_rst2, cam_sensor_mclk0_active, cam_sensor_mclk0_suspend, cam_sensor_mclk1_active, cam_sensor_mclk1_suspend, cam_sensor_mclk2_active, cam_sensor_mclk2_suspend`. Vendor-specific labels (`huawei_wifi_info`, `huawei_lcd_panel`, `huawei_batt_soh`, `direct_charger*`, `battery_*`, `pd_dpm`, …) and UFS/PMIC labels (`ufsphy_mem`, `ufshc_mem`, `ufs_phy_gdsc`, `pm8150_l5/l9/l17/l6`, `pm8150_s4`, `pm8150a_s8`, …) are all in the unresolved set. **Therefore adding `-@` to the candidate alone does not make stock Entry 2 applicable** — 156 of 166 symbols remain unbound.

Positive control (A): a minimal scratch overlay with `target = <&rootparam>` and a `__fixups__ { rootparam = …; }` entry, compiled with `-@` and applied by `<DTC>`'s companion `fdtoverlay`, **succeeds** against `base_at.dtb` — the result node has `qcom,board_name = "WB_POSITIVE_CONTROL"` and phandle 514 preserved. This proves the fixup mechanism and Window B's toolchain work; the failures above are symbol-availability failures, not tool failures. The same minimal overlay applied to the non-`-@` `base.dtb` fails, as expected.

### 4.4 Whole-overlay apply test (A)

`<DTC>`-paired `fdtoverlay -i <base> -o <out> dtbo/entry2.dtbo` results:

| Base | rc | Error | Output DTB |
|---|---|---|---|
| `base.dtb` (frozen, no `-@`) | 1 | `Failed to apply …: FDT_ERR_BADOFFSET` + `base blob does not have a '/__symbols__' node, make sure you have compiled the base blob with '-@' option` | none |
| `base_at.dtb` (`-@`) | 1 | `Failed to apply …: FDT_ERR_NOTFOUND` | none |
| `patched_at.dtb` (`-@`, RAM patched) | 1 | `Failed to apply …: FDT_ERR_NOTFOUND` | none |

The `FDT_ERR_NOTFOUND` on the `-@` bases is consistent with the 156 unresolved symbols: the symbol table exists but most fixup labels are absent, so overlay application aborts. No output DTB was produced in any case; logs are preserved in `<WB_WS>/logs/apply-*.txt`.

**§D verdict: FAIL (candidate-vs-stock DTBO compatibility) — with precise scope:** the stock Entry 2 overlay cannot be applied to the frozen candidate (0/166 fixups bindable), and cannot be applied to an otherwise-identical `-@` candidate either (10/166 bindable, 156 missing labels; `fdtoverlay` → `FDT_ERR_NOTFOUND`). This is a packaging blocker, not a source-format claim: Window B did not test whether Huawei's bootloader applies these overlays by a different mechanism. §3.C's RAM-only change neither creates nor worsens this blocker (both `-@` bases fail identically).

---

## 5. [D — §3.E] Comparison with Window A — BLOCKED

Window A's lane was checked at execution time via the repository API: branch `workbuddy/round154-candidate-dtbo-symbol-fixup-boot-packaging` contains only `START_PROMPT_WORKBUDDY_A_ROUND154_…md` and `WORKBUDDY_A_ROUND154_…_TASKBOOK.md` — **no published report, no patch diff/blob/commit, no source-branch/tree SHA**. The `ai2/round154-…` branch has no `firmware-analysis/round154/` content. Consequently §3.E cannot be executed:

| Required comparison | Status |
|---|---|
| final source diff and tree SHA vs Window A | BLOCKED — no Window A patch identity published |
| candidate DTB bytes vs Window A | BLOCKED — no Window A report artifact |
| all 144 Entry 2 fragment/fixup outcomes vs Window A | BLOCKED — no Window A report artifact |
| list any discrepancy | BLOCKED — nothing to compare; **no silent reconciliation performed** |

Window B's own results stand alone as grade-A evidence (§1–§4). The exact next action, once Window A publishes, is a mechanical comparison of: its patch SHA vs `e5c6a803…` (Window B patched.dts), its rebuilt DTB SHA vs `9d0d7600…`, its source-tree SHA vs `<TREE>`'s, and its 144-fragment outcome table vs §4 of this report. Until then this report makes no claim about agreement or disagreement with Window A.

---

## 6. Prohibitions compliance (A)

| Prohibition | Compliance |
|---|---|
| Access Window A workspace / private logs | none — all paths used are Window B lane or the public report repository |
| Device / ADB / root / fastboot / recovery / partition read-write / flash / reboot / boot | none |
| Full kernel/Image build | none — only `gcc -E` DTS preprocessing and `dtc` DTB compilation |
| Modify frozen base / prior build output / stock firmware / original DTBO / accepted source patch | none — all writes confined to `<WB_WS>/{src,out,logs,dbg,dtbo}/`; `<STOCK_DTBO>` only read, Entry 2 slice is a scratch copy |
| Raw firmware / FDT / serial / IMEI / MAC / panel IDs / private logs in public report | none — all paths sanitised, no raw dumps embedded, full 156-symbol list kept in local scratch log only |

---

## 7. Summary verdicts

| Section | Verdict | One-line result |
|---|---|---|
| §1 Identity | **PASS** | True frozen identity = 108 648 B / `cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e`; the inherited 63-char expectation is invalid and rejected |
| §2 RAM/reservations | **PASS** | One size-zero memory node; 3 windows = 12 185 MiB; 18 reservations sum=union=254.609 MiB, zero overlap, 6 consumers; stock cross-reference marked C |
| §3 RAM-only patch | **PASS (reproduction) / BLOCKED (Window A compare)** | 1-property delta, +32 B DTB, no new warning, board-id still `<0 0>`; no Window A patch published |
| §4 DTBO fixup | **FAIL (compatibility)** | 0/166 fixups bindable on frozen candidate; 10/166 even with `-@`; 156 missing labels; `fdtoverlay` → `FDT_ERR_NOTFOUND` |
| §5 Window A comparison | **BLOCKED** | No Window A report/patch published; no reconciliation attempted |

**Executor: WorkBuddy Window B (2号 Agent); separate WorkBuddy chat window from Window A.** End of report. Stop here per taskbook §5.
