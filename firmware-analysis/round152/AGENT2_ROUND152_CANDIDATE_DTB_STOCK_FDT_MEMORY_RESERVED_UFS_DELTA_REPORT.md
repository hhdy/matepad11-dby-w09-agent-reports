# AGENT2 ROUND152 — Existing candidate DTB vs live stock FDT: memory / reserved-memory / UFS delta

- **Round:** ROUND152 (read-only existing-artefact inspection).
- **Assigned executor per taskbook:** 2号 Agent (independent local Agent 2).
- **Dispatched executor for this run:** the WorkBuddy-side local agent on the same host. Disclosed in §1.4; scope was still cut to the four permitted `round140-agent2` directories.
- **Candidate fixed ACK:** `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`; candidate tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
- **Stock runtime reference:** ROUND151, HOS 4.3.0.196(C00E100), Android 12, kernel `4.19.157-perf+`.
- **Branch:** `agent2/round152-candidate-stock-fdt-memory-reserved-ufs-delta`.
- **Outcome:** **`DELTA_AUDIT_COMPLETE`** — candidate DTB identity reproduced exactly; the memory, reservation and UFS/GDSC/ARC deltas are quantified below. **First boot remains NOT READY and NOT AUTHORIZED.**

---

## 0. Result at a glance

| # | Question (taskbook §4) | Answer | Grade |
|---:|---|---|---|
| 1 | Does the candidate DTB match the expected identity? | **Yes.** 108 648 B, SHA-256 `cab82fe3…db77e`, FDT `totalsize` equal to file size. | A |
| 2 | Does the candidate provide any non-zero System RAM to the ACK early FDT scanner? | **No.** `/memory@80000000` is `reg = <0x0 0x80000000 0x0 0x0>` — one tuple, **size 0**. Zero bytes of declared RAM. | A |
| 3 | Is that zero a defect or an upstream placeholder? | **Upstream placeholder**, source-visible at `sm8250.dtsi:683-687` with the comment "We expect the bootloader to fill in the size". Whether the ABL fill applies to a *replaced* DTB is **UNKNOWN**. | A (bytes) / UNKNOWN (contract) |
| 4 | Candidate reserved-memory census | **18** children, all statically placed, all `no-map`; **0** dynamic pools, **0** CMA, **0** `reusable`. Sum = 266 977 280 B = 254.609 MiB, no internal overlap. | A |
| 5 | Parity against the 37 stock nodes | **17 exact** (base + size identical), **1 same base / new reg** (`cdsp_secure_heap@8bf00000`: stock has no `reg`, candidate carries 70 MiB), **7 stock-static-only**, **12 stock dynamic pools only**, **1 stock reg-less node only**, **1 stock zero-size placeholder only**. Uncovered stock interval union = 42 027 008 B = **40.080 MiB**. | A |
| 6 | UFS host / PHY topology | Host: `status=okay`, **no `vdd-hba-supply`**, `power-domains = <&rpmhpd MMCX>, <&gcc UFS_PHY_GDSC>`, `operating-points-v2` present, `interconnects` present. PHY: `status=okay`, `power-domains = <&gcc UFS_PHY_GDSC>`, no `vdd-hba`. **Both nodes attach the same GDSC.** | A |
| 7 | Is the candidate's GenPD the same gate as the stock `vdd-hba` regulator? | **Yes — same hardware register.** ACK `gcc-sm8250.c:3256` `gdscr = 0x77004`, GCC base `0x100000` ⇒ **0x177004**, which is exactly the stock node address `/soc/qcom,gdsc@177004`. Mechanism differs (genpd vs regulator), gate identity does not. | A |
| 8 | ARC groups in the candidate | **0** `qcom,rpmh-arc-regulator`, **0** `qcom,rpmh-vrm-regulator` groups of that kind, **0** `qcom,resource-name`, **0** `proxy-supply`, **0** `proxy-consumer*`. Only two VRM group nodes (`pm8150` id `a`, `pm8150l` id `c`) with six rails. ROUND147's "zero ARC groups" is independently confirmed. | A |
| 9 | Dual `mmcx.lvl` ownership inside the DTB? | **Not present.** The DTB carries the GenPD consumer (`<&rpmhpd RPMHPD_MMCX>`) and **no** ARC `mmcx.lvl` provider, so no collision can be inferred from this artefact. It becomes a design decision only if ARC is later added. | A (absence) |
| 10 | Is a new compile justified now? | **No.** The single blocking unknown (ABL memory-fill contract) is not resolvable by another compile, and every other delta is a consumer-driven decision. See §6. | — |

---

## 1. Scope, inputs and identity gate

### 1.1 Permitted inputs actually used

| Input | Role |
|---|---|
| `<round140-agent2>/out-dtb/arch/arm64/boot/dts/qcom/huawei-dby-w09.dtb` | The candidate artefact under audit |
| `<round140-agent2>/out-dtb/arch/arm64/boot/dts/qcom/.huawei-dby-w09.dtb.cmd` | Provenance: exact `dtc` command line and dependency list |
| `<round140-agent2>/out-dtb/.config`, `Makefile`, `include/config/*` | Build context only (not parsed for this report) |
| `<round140-agent2>/logs/dtb-build-raw.log`, `stage-b4-dtb-build-and-structure.log`, `dtb-decompiled.dts` | Build provenance and a prior decompile (used only to cross-check node counts) |
| `<round140-agent2>/tree/arch/arm64/boot/dts/qcom/{huawei-dby-w09.dts,sm8250.dtsi}` | Source provenance for placeholder semantics and proposed deltas — **read-only, no edit** |
| `<round140-agent2>/a30build` | Listed but not needed beyond confirming the Kleaf staging tree is separate from `out-dtb` |
| Published ROUND151 report (`workbuddy/round151-root-readonly-runtime-audit`) | The only stock-decoded data used |
| Published AI1 ROUND151 review (`ai1/round130-…`, `kernel-baseline/round151/`) | Corrections and ROUND152 plan |

No other directory, no other agent workspace, no WorkBuddy raw FDT, no device, no network source besides the two reports above.

### 1.2 Identity gate (mandatory before parsing)

```
path (relative to permitted out-dtb): arch/arm64/boot/dts/qcom/huawei-dby-w09.dtb
bytes                                : 108648
sha256                               : cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e
expected (taskbook §0 / ROUND140/147) : 108648 / cab82fe3…db77e
```

**Match.** Exactly one 108 648-byte file exists under `out-dtb`; no substitute was considered, and no other `.dtb`/`.dtbo` exists there.

### 1.3 Decoded FDT header

| Field | Value |
|---|---|
| magic | `0xd00dfeed` |
| totalsize | 108 648 ( **= file size** ) |
| version / last_comp_version | 17 / 16 |
| off_dt_struct / size_dt_struct | 56 / 105 468 |
| off_dt_strings / size_dt_strings | 105 524 / 3 124 |
| nodes | **905** |
| nodes with ≥1 property | 782 |
| distinct phandles | 239 |

Stock comparison (ROUND151): 4 566 nodes / 2 039 phandles. The candidate is a minimal board tree, not a merged vendor tree.

### 1.4 Tooling and dispatch disclosure

| Item | Value |
|---|---|
| Decoder | `fdt138.py` — the pure-stdlib struct-block walker written and verified in ROUND138, reused unchanged (`sha256 05038f20…420d9a`) |
| Analysis layer | `scan152.py` (`sha256 7c04b4ed…b05f0`), `cmp152.py` (`sha256 369117c9…42601`), both stdlib-only |
| Python | 3.12.3 |
| `dtc` | present at `out-dtb/scripts/dtc/dtc` (DTC 1.7.2-g52f07dcc) but **not invoked** this round; the artefact was read as bytes |
| Installs / downloads | none |

**Dispatch disclosure.** The taskbook assigns this round to 2号 Agent. The prompt that carried the taskbook was handled by the WorkBuddy-side local agent on the same machine, which is why this section states it explicitly instead of silently claiming the assigned identity. The read set was nevertheless cut to the four permitted `round140-agent2` directories plus the two published reports; no WorkBuddy evidence directory, no AI1/AI2 private workspace and no other `matepad11/*` tree was opened. If the dispatcher intended a strictly separate executor, this report should be treated as an independent third-party re-derivation of the same numbers — which is what the identity gate and the byte-level tables below make checkable.

---

## 2. A — Candidate root node and RAM

### 2.1 Root

| Property | Candidate value | Stock (ROUND151) |
|---|---|---|
| `model` | `Huawei MatePad 11 (2021) DBY-W09` | `Huawei Technologies, Inc. DBY-W09` |
| `compatible` | `huawei,dby-w09`, `qcom,sm8250` | `qcom,kona-qrd`, `qcom,kona`, `qcom,qrd` |
| `#address-cells` | **2** | 2 |
| `#size-cells` | **2** | 2 |
| `qcom,board-id` | `<0x0 0x0>` | `<0x200e 0x0>` |
| `qcom,msm-id` | `<0x164 0x20001>` | `<0x164 0x20001>` |
| child nodes | 23 | 83 |

`compatible` and `model` are expected to differ: the candidate is an ACK board file, not a HOS/kona one. The two identity cells are worth separating:

- `qcom,msm-id` matches stock exactly (`0x164` = SM8250, `0x20001` = v2.1). This is the SoC revision gate the bootloader uses to pick a base DTB.
- `qcom,board-id` is `0 0` in the candidate and `0x200e 0` on the live blob. The local board file documents this deliberately (`huawei-dby-w09.dts:35-39`: "Keep the SoC DTB board-id at zero; the separate DBY-W09 DTBO is selected by board-id 0x206a"; `qcom,board-id = <0 0>` on line 39). That comment cites **0x206a = 8298 = stock DTBO entry 8**, while ROUND138/R151 establish `androidboot.dtbo_idx=2` ⇒ **0x200e = 8206** for the live boot. The comment's selection assumption and the live selection disagree; that is a documentation-vs-live mismatch outside the DTB, recorded here because it conditions any DTBO pairing plan, and **not** acted on.

### 2.2 Every memory node in the candidate

Two nodes in the blob carry the name `memory@80000000`, under different parents. They are listed separately, because a name-based grep would silently conflate them.

| # | Path | `device_type` | `status` | `reg` (raw cells) | Decoded (ac=2, sc=2) | MiB |
|---:|---|---|---|---|---|---:|
| 1 | `/memory@80000000` | `memory` | *(absent → not disabled)* | `<0x0 0x80000000 0x0 0x0>` | base `0x80000000`, **size `0x0`** | **0.000** |
| 2 | `/reserved-memory/memory@80000000` | *(none)* | *(none)* | `<0x0 0x80000000 0x0 0x600000>` | base `0x80000000`, size `0x600000` | 6.000 |

Node 1 is the only node with `device_type = "memory"`. There is no second RAM window, no `linux,usable-memory`, no `/memory@…` sibling.

### 2.3 Does the candidate give the ACK early scanner any RAM?

**No — zero bytes.**

- 12 cells were not needed: `reg` is 16 B = one `(ac=2, sc=2)` tuple, and its size half is `0x00000000`.
- `early_init_dt_scan_memory()` adds a region only for `size > 0`; a zero-size tuple contributes nothing to memblock. The resulting memblock is empty, so a kernel that scans **this blob alone** cannot complete memory initialisation. The exact failure site (early panic vs later allocation failure) is *not* asserted here — only the input condition is.
- The candidate therefore satisfies no part of stock's three-window map:

| Stock window | base | size | MiB | Present in candidate |
|---|---|---:|---:|---|
| 0 | `0x80000000` | `0x39900000` | 921 | base only, **size 0** |
| 1 | `0x200000000` | `0x200000000` | 8 192 | **absent** |
| 2 | `0xc0000000` | `0xc0000000` | 3 072 | **absent** |

### 2.4 Why the zero exists, and what is still unknown

`sm8250.dtsi:683-687` (candidate tree, read-only):

```dts
memory@80000000 {
	device_type = "memory";
	/* We expect the bootloader to fill in the size */
	reg = <0x0 0x80000000 0x0 0x0>;
};
```

So the zero is **intentional upstream design**, not a build accident and not a truncation. Three statements must be kept apart:

1. **A-grade:** the shipped blob declares zero RAM (bytes above).
2. **A-grade:** the *live stock* blob declares three windows, so something in the stock chain does populate RAM — the stock FDT is not self-sufficient either.
3. **UNKNOWN:** whether that same population step runs for a **replaced** DTB. The live evidence cannot distinguish three very different mechanisms:
   - (a) ABL rewrites `/memory/reg` wholesale with three tuples;
   - (b) ABL patches only the size of the existing single tuple (then a one-tuple candidate can only ever yield the low window);
   - (c) the stock base DTB already carried real tuples and no fixup happens at all (then a candidate with zero tuples gets nothing).

The local board file additionally records, as prior-round documentation, that the stock **base** FDT `/memory` `reg` is an all-zero placeholder (`huawei-dby-w09.dts:318-320`, citing ROUND19/20/22). If that record is accurate it excludes mechanism (c) and leaves (a) or (b) — but it is documentation grade here (no stock base FDT was opened this round, by scope), so it is reported as **C-grade corroboration, not proof**.

**Consequence for the blocker label.** "Candidate RAM = zero" is confirmed. "Candidate cannot boot" is *conditional* on the fill contract. Calling it a proven fatal defect would overstate the evidence; calling it resolved would understate it.

### 2.5 Note on pasting stock tuples

Pasting R151's three tuples into the candidate is technically possible and the values are A-grade for **this unit**, but it is a decision with a real risk surface, so it is deferred to §6 with the risk table rather than done here. Two hazards are worth naming now:

- If ABL rewrites `reg` wholesale (mechanism a), explicit tuples are harmless — they are simply overwritten.
- If ABL appends rather than rewrites, or if the unit is one of several capacity variants sharing this DTB, fixed tuples could describe RAM that is not populated — a paging-time failure that is harder to diagnose than a clean "no memory".

---

## 3. B — Candidate reserved-memory census

### 3.1 Group node

| Property | Value |
|---|---|
| path | `/reserved-memory` |
| `#address-cells` / `#size-cells` | 2 / 2 |
| `ranges` | present, **length 0** (identity mapping) |
| `phandle` | **none** (stock group has `0x682`) |
| children | **18** |

All 18 children decode cleanly with the group's own cell values; **0 unresolved**.

### 3.2 Full census

Flags: `NM` = `no-map`; `CDB` = `compatible = "qcom,cmd-db"`; `RD` = `removed-dma-pool` in `compatible`. No node carries `reusable`, `linux,cma-default`, `size`, `alignment` or `alloc-ranges`.

| # | Node | phandle | base | size | MiB | Flags | `memory-region` consumer |
|---:|---|---:|---|---|---:|---|---|
| 1 | `memory@80000000` | — | `0x80000000` | `0x600000` | 6.000 | NM | — |
| 2 | `memory@80700000` | — | `0x80700000` | `0x160000` | 1.375 | NM | — |
| 3 | `memory@80860000` | — | `0x80860000` | `0x20000` | 0.125 | NM, CDB | — |
| 4 | `memory@80900000` | 43 | `0x80900000` | `0x200000` | 2.000 | NM | `/smem` |
| 5 | `memory@80b00000` | — | `0x80b00000` | `0x5300000` | 83.000 | NM | — |
| 6 | `memory@86200000` | — | `0x86200000` | `0x500000` | 5.000 | NM | — |
| 7 | `memory@86700000` | — | `0x86700000` | `0x100000` | 1.000 | NM | — |
| 8 | `memory@86800000` | — | `0x86800000` | `0x10000` | 0.0625 | NM | — |
| 9 | `memory@86810000` | — | `0x86810000` | `0xa000` | 0.039 | NM | — |
| 10 | `memory@8681a000` | 115 | `0x8681a000` | `0x2000` | 0.0078 | NM | `/soc@0/gpu@3d00000/zap-shader` |
| 11 | `memory@86900000` | — | `0x86900000` | `0x500000` | 5.000 | NM | — |
| 12 | `memory@86e00000` | 187 | `0x86e00000` | `0x500000` | 5.000 | NM | `/soc@0/video-codec@aa00000` |
| 13 | `memory@87300000` | — | `0x87300000` | `0x500000` | 5.000 | NM | — |
| 14 | `memory@87800000` | 172 | `0x87800000` | `0x1400000` | 20.000 | NM | `/soc@0/remoteproc@8300000` |
| 15 | `memory@88c00000` | 120 | `0x88c00000` | `0x1500000` | 21.000 | NM | `/soc@0/remoteproc@5c00000` |
| 16 | `memory@8a100000` | 207 | `0x8a100000` | `0x1d00000` | 29.000 | NM | `/soc@0/remoteproc@17300000` |
| 17 | `memory@8be00000` | — | `0x8be00000` | `0x100000` | 1.000 | NM | — |
| 18 | `memory@8bf00000` | — | `0x8bf00000` | `0x4600000` | 70.000 | NM | — |

**Internal arithmetic**

| Quantity | Value |
|---|---:|
| Sum of declared sizes | **266 977 280 B = 254.609 MiB** |
| Unique union after overlaps | **266 977 280 B** (identical — no pair overlaps) |
| Pairwise overlap check | 153 pairs tested, **0 overlapping** |
| Dynamic allocation requests | **0** |
| Ranges outside a stock RAM window | **0** — highest end `0x90500000` < `0xb9900000` |

The last row matters independent of the RAM question: even in the pessimistic scenario where only the 921 MiB low window is ever populated, **all 18 carve-outs still fall inside it**. The reservation map is structurally consistent with the smallest plausible RAM map.

### 3.3 Classification against the 37 stock nodes

Two different comparison keys are needed, and using the wrong one produces a false mismatch:

- **Names are not comparable.** Every candidate node is named `memory@<addr>` (upstream style with a label), while stock uses descriptive names (`hyp_region@…`, `pil_adsp_region@…`). Name-based matching yields 0/37 identical and is meaningless.
- **Addresses are comparable** and are used below. The labels in the local DTS (`hyp_mem`, `xbl_aop_mem`, `smem_mem`, …) were used only to *name* the match, not as evidence.

| Class | Count | Detail |
|---|---:|---|
| 1. Same name **and** same semantic values | **0** | no textual name overlap by construction |
| 2. Same base, changed address/size/flags | **1** | `memory@8bf00000` ↔ stock `cdsp_secure_heap@8bf00000` |
| — *(actual match class, by address)* | **17** | base **and** size identical to stock: `0x80000000`, `0x80700000`, `0x80860000`, `0x80900000`, `0x80b00000`, `0x86200000`, `0x86700000`, `0x86800000`, `0x86810000`, `0x8681a000`, `0x86900000`, `0x86e00000`, `0x87300000`, `0x87800000`, `0x88c00000`, `0x8a100000`, `0x8be00000` |
| 3. Candidate-only (base absent from stock) | **0** | — |
| 4. Stock-only, statically placed | **7** | see below |
| 5. Dynamic pool with different semantics | **12** (+1 related) | stock has 12 `size`/`alignment` pools, candidate has none |
| 6. Unresolved (missing property / parser limit) | **0** | every `reg` decoded; no ambiguity |

**Class 2 in detail.** Stock `cdsp_secure_heap@8bf00000` carries `no-map`, `removed-dma-pool` and **no `reg` at all**. The candidate gives the same base a fixed 70 MiB. Source: `sm8250.dtsi:862-865`. So this is not a mismatched address — it is a *newly fixed* carving of a window that stock leaves unplaced.

### 3.4 Stock-only static nodes and the uncovered interval union

| Stock node | base | size | MiB | Flags | In candidate |
|---|---|---:|---:|---|---|
| `res_xbl_uefi_log_region@80880000` | `0x80880000` | `0x14000` | 0.078 | no-map, removed-dma-pool | **absent** |
| `cont_splash_region@9c000000` | `0x9c000000` | `0x2300000` | 35.000 | — | **absent** |
| `disp_rdump_region@9c000000` | `0x9c000000` | `0x800000` | 8.000 | — | **absent** (nested in splash) |
| `dfps_data_region@9e300000` | `0x9e300000` | `0x100000` | 1.000 | — | **absent** |
| `rainbow_mem@b0000000` | `0xb0000000` | `0x400000` | 4.000 | no-map, removed-dma-pool, rainbow_mem | **absent** |
| `bootfail_mem@b0400000` | `0xb0400000` | `0x800` | 0.0005 | no-map, removed-dma-pool, bootfail_mem | **absent** |
| `kerneldump` | `0x0` | `0x0` | 0 | — (unpopulated placeholder) | **absent** |

Subtracting the candidate's intervals from the stock static union leaves **42 027 008 B = 40.080 MiB** in three contiguous gaps:

| Gap | Bytes | MiB | Meaning |
|---|---:|---:|---|
| `0x80880000` – `0x80894000` | 81 920 | 0.078 | XBL/UEFI log region |
| `0x9c000000` – `0x9e400000` | 37 748 736 | 36.000 | splash 35 + dfps 1 (rdump nested) |
| `0xb0000000` – `0xb0400800` | 4 196 352 | 4.002 | rainbow 4 + bootfail 0x800 |

### 3.5 Sum versus union versus containment — kept separate on purpose

| Metric | Stock | Candidate |
|---|---:|---:|
| Non-zero static `reg` entries | 23 | 18 |
| Sum of static entry sizes | 243 992 576 B = 232.689 MiB | 266 977 280 B = 254.609 MiB |
| Unique static interval union | 235 603 968 B = **224.689 MiB** (8 MiB removed: the one nested pair) | 266 977 280 B = **254.609 MiB** |
| Dynamic allocation requests | 12 pools, sizes summing to 360.125 MiB (requests, not placement) | 0 |
| Containment in stock RAM | all inside | all inside |

Closing check: candidate 254.609 − 70.000 (`cdsp_secure_heap`) = **184.609 MiB**, and stock union 224.689 − 40.080 (uncovered) = **184.609 MiB**. The two independent paths agree, so the 17 "exact" matches are exact in aggregate as well as per node.

### 3.6 A classification nuance in the input, recorded not silently fixed

ROUND151 §3.6 states the 37 children are "23 with a non-zero `reg` + 1 zero-size `reg` + 13 dynamic (`size`/`alignment`/`alloc-ranges`) nodes". Recounting the *published* table gives:

```
23 static (non-zero reg) + 12 size/alignment pools + 1 reg-less node (cdsp_secure_heap) + 1 zero-size (kerneldump) = 37
```

The total (37) and the static count (23) both hold; only the "13 dynamic" figure requires counting the reg-less `cdsp_secure_heap@8bf00000` as a pool. Since the candidate now places that very node statically with 70 MiB, the distinction is load-bearing for this round and is stated rather than smoothed over. Both readings are compatible; the report uses the explicit four-way split.

### 3.7 Overlaps are not defects, and stock vendor carve-outs are not automatic requirements

- The one stock overlap (`disp_rdump_region` inside `cont_splash_region`, 8 MiB) is a display-ramdump arrangement. Nothing here calls it an error, and the candidate reproduces neither node.
- The 12 missing pools and the 7 missing static nodes are **not** treated as mandatory copies. Sections 6.2–6.3 sort them by whether an enabled consumer exists in the candidate tree.

---

## 4. C — UFS Host / PHY and GDSC topology

### 4.1 Controller `/soc@0/ufshc@1d84000`

| Item | Candidate | Stock (R151) |
|---|---|---|
| `compatible` | `qcom,sm8250-ufshc`, `qcom,ufshc`, `jedec,ufs-2.0` | `qcom,ufshc` |
| `status` | `okay` | `ok` |
| phandle | 98 | `0x3b6` |
| `reg` | `<0x0 0x1d84000 0x0 0x3000>` | `<0x1d84000 0x3000 0x1d90000 0x8000>` (+ ICE) |
| `interrupts` | `<0x0 265 0x4>` (GIC_SPI 265, level-high) | — |
| `vdd-hba-supply` | **ABSENT** | present → `ufs_phy_gdsc` |
| `power-domains` | `<&rpmhpd RPMHPD_MMCX>` **+** `<&gcc UFS_PHY_GDSC>` | **ABSENT** |
| `operating-points-v2` | `<&opp-table>` (child of the host node) | **ABSENT** |
| `interconnects` | 2 paths: `ufs-ddr`, `cpu-ufs` | legacy `qcom,msm-bus` + devfreq |
| `freq-table-hz` | absent | present |
| `phys` / `phy-names` | `<&ufs_mem_phy>` / `ufsphy` | same relation |

Supply properties, with resolved providers:

| Property | phandle | Resolves to | RPMh resource | Stock equivalent |
|---|---:|---|---|---|
| `vcc-supply` | 93 | `/soc@0/rsc@18200000/regulators-0/ldo17` | `ldoa17` (pmic-id `a` + `ldo17`) | PM8150 L17 ✔ |
| `vccq-supply` | 94 | `…/regulators-0/ldo6` | `ldoa6` | PM8150 L6 ✔ |
| `vccq2-supply` | 96 | `…/regulators-0/smps4` | `smpa4` | PM8150 S4 ✔ |
| `qcom,vddp-ref-clk-supply` | 94 | `…/regulators-0/ldo6` | `ldoa6` (2nd consumer of L6) | PM8150 L6 ✔ |
| `qcom,vccq-parent-supply` | 95 | `…/regulators-1/smps8` | **`smpc8`** (pmic-id `c` + `smps8`) | `smpc8` / `pm8150a_s8` ✔ |
| `vdd-hba-supply` | — | — | — | `ufs_phy_gdsc` **✗ replaced by GenPD** |

**The S8 naming trap, resolved.** The candidate child is named `pm8150l_s8` and stock names the same rail `pm8150a_s8`. That looks like a different PMIC. It is not: the ACK driver builds the RPMh resource string as `format(pmic_id, vreg_name)` (`qcom-rpmh-regulator.c:419-439`, format from `RPMH_VREG("smps8", "smp%s8", …)` at `:1020`), and the candidate group declares `qcom,pmic-id = "c"` ⇒ **`smpc8`** — byte-for-byte the resource stock's `rpmh-regulator-smpc8` group addresses. Only the display name differs. This is a naming difference to document, not a wiring difference to fix.

### 4.2 QMP PHY `/soc@0/phy@1d87000`

| Item | Candidate | Stock |
|---|---|---|
| `compatible` | `qcom,sm8250-qmp-ufs-phy` | `qcom,ufs-phy-qmp-v4` |
| `status` | `okay` | `ok` |
| phandle | 91 | `0x77` |
| `reg` | `<0x0 0x1d87000 0x0 0x1000>` | `<0x1d87000 0xe00 0x1d90000 0x8000>` (+ ICE) |
| `power-domains` | `<&gcc UFS_PHY_GDSC>` (idx 4) | **ABSENT** |
| `vdda-phy-supply` | 99 → `…/ldo5` (`ldoa5`) | PM8150 L5 ✔ |
| `vdda-pll-supply` | 100 → `…/ldo9` (`ldoa9`) | PM8150 L9 ✔ |
| `vdda-phy-always-on` | present | present |
| `#phy-cells` | 0 | 0 |
| `resets` / `reset-names` | `<&ufshc 0>` / `ufsphy` | — |

**Same GDSC on both nodes: yes.** Host `<&gcc 4>` and PHY `<&gcc 4>` reference one provider (phandle 48 = `/soc@0/clock-controller@100000`, `#power-domain-cells = 1`, `compatible = "qcom,gcc-sm8250"`).

### 4.3 The GDSC provider and its identity

| Item | Candidate (ACK) | Stock (HOS) |
|---|---|---|
| Node form | **no standalone node**; GDSC is a gdsc inside the GCC clock controller | standalone `/soc/qcom,gdsc@177004` |
| Provider | `/soc@0/clock-controller@100000`, phandle 48 | `177004.qcom,gdsc` |
| Name | `ufs_phy_gdsc` (`gcc-sm8250.c:3259`) | `regulator-name = "ufs_phy_gdsc"` |
| Register | `gdscr = 0x77004` relative to GCC base `0x100000` | `reg = <0x177004 0x4>` |
| **Absolute address** | `0x100000 + 0x77004 = **0x177004**` | `**0x177004**` |
| Power states | `pwrsts = PWRSTS_OFF_ON` | — (regulator with `qcom,retain-regs`) |
| Parent supply | **none** | unknown per-GDSC; 13 of the stock GDSCs carry `parent-supply`/`vdd_parent-supply` |
| Consumers | host + PHY via `power-domains` | `vdd-hba-supply` of the host, only |

**Same gate, different contract.** The register equality (`0x177004`) is an arithmetic identity, not an inference, and it settles the question the delta really hinges on: the candidate is not powering a *different* gate than stock's `vdd-hba`. It powers the *same* gate through genpd instead of through a regulator handle.

### 4.4 OPP, required-opps and interconnect

`/soc@0/ufshc@1d84000/opp-table` (phandle 92, `compatible = "operating-points-v2"`):

| OPP | `opp-hz` (8 × 64-bit, clock order per `clock-names`) | `required-opps` | Level |
|---|---|---|---|
| `opp-37500000` | `37500000, 0, 0, 37500000, 0, 0, 0, 0` | `<&rpmhpd_opp_low_svs>` = `opp3` | `0x40` = 64 |
| `opp-300000000` | `300000000, 0, 0, 300000000, 0, 0, 0, 0` | `<&rpmhpd_opp_nom>` = `opp6` | `0x100` = 256 |

The two required levels are the same two numbers ROUND151 read off the live ARC rails (`pm8150a_s4_level` min/max `64/384`, live level `192`) — i.e. the candidate asks rpmhpd for `LOW_SVS` and `NOM` on a resource whose stock consumer set is the same corner graph. Interconnect paths: `ufs-ddr` (`<&aggre1_noc MASTER_UFS_MEM …>` → `mc_virt SLAVE_EBI_CH0`) and `cpu-ufs` (`<&gem_noc MASTER_AMPSS_M0 …>` → `config_noc SLAVE_UFS_MEM_CFG`), both `sm8250.dtsi:2544-2546`.

### 4.5 Exact topology difference against stock

| Aspect | Stock | Candidate | Nature of delta |
|---|---|---|---|
| `vdd-hba` | regulator handle to `ufs_phy_gdsc` | absent | **mechanism replaced** |
| GDSC attachment | none (`power-domains` absent) | host + PHY → same GDSC | **new attachment** |
| MMCX corner | none (no OPP, no `power-domains`) | host → `rpmhpd MMCX`, 2 OPPs with `required-opps` | **new performance contract** |
| Performance mechanism | `freq-table-hz` + devfreq + legacy `qcom,msm-bus` | OPP/`required-opps` + `interconnects` | **different contract** |
| ICE window | second `reg` + `reg-names = "ufs_mem","ufs_ice"` | absent | declaration difference |
| Six rails | L17/L6/S4/L6/S8 + L5/L9 | identical | **no delta** |

### 4.6 The one stock fact that must not be over-read

Stock reports `ufs_phy_gdsc` **`disabled`, `num_users = 0`** while UFS is fully active at HS-G1 ×2. R151 and AI1 both insist this is a *software-reported regulator state*, not proof of a physical gate state. What it does establish is narrower and still important: **on the stock software path, the gate is not required to be "enabled" for UFS to work.** The candidate will instead have genpd vote it on at probe (`PWRSTS_OFF_ON`, no `ALWAYS_ON` flag), which is a behavioural change regardless of the physical outcome.

### 4.7 What the candidate DTB alone cannot prove

1. Whether the genpd will actually be powered on before the first UFS register access (runtime-PM ordering is code, not DT).
2. Whether `UFS_PHY_GDSC` has an implicit parent requirement in **stock** — if `ufs_phy_gdsc` is among the 13 stock GDSCs carrying `parent-supply` to an ARC level, then a parent corner must be voted before the gate can be enabled, and ACK's `ufs_phy_gdsc` descriptor (`gcc-sm8250.c:3256-3262`) declares **no** parent. ROUND151 publishes the count (13) but not the names, so **whether `177004` is one of them is UNKNOWN**. This is the sharpest open item this round produces.
3. Whether the ARC/`mmcx.lvl` producer side will exist at all in the candidate (it will not — §5).
4. Anything about voltage, vote value or physical rail state. Provider presence never implies any of those.

---

## 5. D — ARC / RPMHPD resource ownership

| Item | Result | Method |
|---|---|---|
| `qcom,rpmh-arc-regulator` groups | **0** | full-tree scan of every node's `compatible` |
| `qcom,rpmh-vrm-regulator` groups | **0** | same |
| Nodes carrying `qcom,resource-name` | **0** | property scan over all 905 nodes |
| Nodes carrying any `proxy*` property (`proxy-supply`, `qcom,proxy-consumer-*`) | **0** | property scan |
| `*-parent-supply` edges between providers | **0** | the only `parent-supply`-containing property in the blob is `qcom,vccq-parent-supply` on the host — a consumer declaration, not a provider edge |
| Standalone GDSC nodes | **0** | no node named or compatible `qcom,gdsc` |
| RPMh regulator groups present | **2**: `regulators-0` (`qcom,pm8150-rpmh-regulators`, `qcom,pmic-id = "a"`), `regulators-1` (`qcom,pm8150l-rpmh-regulators`, `qcom,pmic-id = "c"`) | — |
| Rails under those groups | **6**: `ldo5`, `ldo6`, `ldo9`, `ldo17`, `smps4` (group `a`), `smps8` (group `c`) | — |
| RSC children | `clock-controller`, `power-controller`, `bcm-voter`, `regulators-0`, `regulators-1` | — |

**ROUND147's "zero ARC groups" is confirmed independently**, on this exact blob, with a different parser.

**RPMHPD descriptor for the UFS OPP domain.** `drivers/pmdomain/qcom/rpmhpd.c:126-130`:

```c
static struct rpmhpd mmcx = {
	.pd = { .name = "mmcx", },
	.peer = &mmcx_ao,
	.res_name = "mmcx.lvl",
};
```

No `.parent` pointer (consistent with ROUND139/ROUND145/ROUND151). The candidate's host references `<&rpmhpd RPMHPD_MMCX>` — `RPMHPD_MMCX = 6` per `dt-bindings/power/qcom,rpmhpd.h:16` — and its OPPs require `opp3`/`opp6` on that provider.

**Is there a dual-owner collision inside this DTB?** No. The DTB contains:

- the **GenPD consumer** side of `mmcx.lvl` (host, via rpmhpd), and
- **no** ARC `mmcxlvl` provider.

So the conditional `mmcx.lvl` conflict AI1 §5.1 describes is a *future* consequence of adding stock ARC groups to this tree, not a property of the current artefact. Nothing in this round licenses inferring a runtime collision from one side being absent.

---

## 6. E — Final candidate disposition

### 6.1 State of the four questions

| Question | Status |
|---|---|
| Candidate RAM blocker | **CONFIRMED as a declaration gap** (zero-size tuple, A-grade). **CONDITIONAL as a boot blocker** — depends on the ABL fill contract, which is UNKNOWN for a replaced DTB. |
| Stock/candidate reserved-memory parity | **QUANTIFIED**: 17/18 exact by address, +70 MiB new fixed carve, −40.080 MiB of stock static coverage (splash/dfps, rainbow/bootfail, XBL log), −12 dynamic pools including **`linux,cma`**. No overlap, no range outside stock RAM. |
| UFS GDSC/GenPD difference | **CHARACTERISED**: same gate (`0x177004`), different contract (genpd + MMCX corner vs `vdd-hba` regulator with zero users). Both host and PHY attach the single GDSC. |
| ARC and proxy status | **ABSENT (0/0)** in the candidate; the `mmcx.lvl` dual-owner question is latent, not present. |

### 6.2 CONFIRMED — evidence already supports the change

| ID | Change | Basis |
|---|---|---|
| C-1 | `/memory` must end with **non-zero** `reg` before the ACK early scan | A-grade: candidate declares 0 B of RAM; the scanner cannot place anything without it |
| C-2 | If the dispatcher chooses the explicit-tuple route, the three stock windows (`0x80000000/0x39900000`, `0x200000000/0x200000000`, `0xc0000000/0xc0000000`, ac/sc 2/2) are the values to use | A-grade for this unit (FDT + `/proc/iomem` corroboration in R151) |
| C-3 | Keep the six-rail assignment exactly as is | 6/6 rail→provider→RPMh resource identity with stock, independently derived twice |

### 6.3 PROPOSED — evidence supports, consumer decision required first

| ID | Change | Why it is not "confirmed" |
|---|---|---|
| P-1 | `linux,cma`: `size 0x2000000`, `alignment 0x400000`, `reusable` + `linux,cma-default` | No CMA consumer is enabled in this DTS. Becomes necessary the moment display/camera/dmabuf work starts; absent CMA also degrades high-order allocation under fragmentation. |
| P-2 | `cont_splash_region` 35 MiB @ `0x9c000000` + `dfps_data_region` 1 MiB @ `0x9e300000` | Only meaningful if the ABL splash handoff is preserved and a display driver consumes it. Copying the stock addresses without a display plan buys nothing and costs 36 MiB. |
| P-3 | Any of the 12 stock reusable pools (`qseecom`, `qseecom_ta`, `secure_display`, `cnss_wlan`, `adsp`, `sdsp`, `cdsp`, `mem_dump`, `sp`, `user_contig`, `mailbox`) | Each needs a *named* consumer. `mailbox_region` is the only one with a plausible existing ACK consumer (`qcom,smem`-adjacent mailbox); the rest belong to drivers not yet enabled. |
| P-4 | Decide `cdsp_secure_heap` 70 MiB: keep, or drop the `reg` to match stock's unplaced node | It is upstream-inherited, has no consumer in the blob, and stock places nothing. Keeping it costs 70 MiB; dropping it is also defensible. Both are honest; the DTB cannot choose. |
| P-5 | Document the `pm8150l_s8` vs `pm8150a_s8` naming difference | Same `smpc8` resource; no code change, but the difference will otherwise be re-discovered as a bug. |

### 6.4 NOT JUSTIFIED — do not do these on current evidence

| ID | Temptation | Why it is unjustified |
|---|---|---|
| N-1 | Copy `rainbow_mem`, `bootfail_mem`, `res_xbl_uefi_log_region`, `kerneldump` | Pure HOS vendor machinery with no ACK consumer; `kerneldump` is a zero-size placeholder. Copying them adds reserved memory and nothing else. |
| N-2 | Add the seven ARC groups / `smpc8`-style `mmcxlvl` provider for "fidelity" | The genpd side already owns `mmcx.lvl` in this tree. Adding the ARC provider creates the dual-writer condition AI1 §5.1 flags. This is an ownership decision, not a port. |
| N-3 | Add `vdd-hba-supply` back on top of the existing GDSC `power-domains` | Two handles to one gate (`0x177004`); the ACK core would enable the gate as a regulator *and* as a genpd. |
| N-4 | Remove the `UFS_PHY_GDSC` attachment because stock shows it disabled / 0 users | Stock's software state does not prove a physical requirement, and ACK has no `vdd-hba` path to replace it. Removing it would leave the gate with no voter at all. |
| N-5 | Treat the zero-size `/memory` as proof that ABL will fill it | The fill is documented for the bootloader-filled placeholder but is **not** demonstrated for a replaced DTB. §2.4 lists the three mechanisms that remain indistinguishable. |

### 6.5 Is a new compile justified now?

**No.** Reasoning, stated plainly:

1. The blocking unknown is a **contract** question (does ABL populate `/memory` in a replacement DTB?), not a code question. A compile produces a second artefact that is exactly as unverifiable as the first — the only way to read the merged FDT is to boot, which is prohibited.
2. Every other delta (P-1…P-4) is a consumer/design decision. Compiling before those choices would bake arbitrary reservations into a binary and make the next comparison noisier, not clearer.
3. The one change that is both small and unambiguous (C-1 explicit tuples) is *conditionally* correct: if the dispatcher accepts §6.2 C-2 with the §2.5 risk table, then a single-file, three-tuple edit plus one compile and an `fdtdump`-free byte check would be a reasonable next step. That is a dispatcher decision, not something this round can take.

**Recommended next gate (not started):** decide the memory-fill contract (rely on ABL vs declare tuples), and — separately — ask a future authorised stock capture for the **names of the 13 GDSC nodes carrying `parent-supply`** and specifically whether `177004`/`ufs_phy_gdsc` is one of them. That single list decides whether the candidate's parentless `UFS_PHY_GDSC` genpd is safe.

---

## 7. Errors, corrections and limitations

| ID | Item | Handling |
|---|---|---|
| L-1 | Names cannot be used to match candidate and stock reserved-memory nodes (upstream `memory@<addr>` vs vendor descriptive names; and `memory@80000000` exists **twice** — once as RAM, once as a carve-out) | Switched to address-keyed comparison; both same-named nodes reported separately (§2.2, §3.3) |
| L-2 | ROUND151's "13 dynamic" pools vs this recount's 12 size/alignment pools + 1 reg-less node | Reported as an explicit four-way split rather than silently reconciled (§3.6) |
| L-3 | The `pm8150l_s8` vs `pm8150a_s8` naming would read as a PMIC mismatch | Resolved via the driver's `format(pmic_id, name)` construction to the same `smpc8` resource (§4.1) |
| L-4 | Stock base-FDT `/memory` placeholder status is only available here as a **comment** in the candidate tree (citing ROUND19/20/22), not as a re-read artefact | Labelled C-grade corroboration; scope forbade opening the stock base FDT this round (§2.4) |
| L-5 | Whether `ufs_phy_gdsc` is one of the 13 stock GDSCs with a `parent-supply` | **UNKNOWN** — ROUND151 publishes the count, not the names; listed as the top open item (§4.7, §6.5) |
| L-6 | The board file's DTBO-selection comment (`board-id 0x206a` = entry 8) disagrees with live `dtbo_idx=2` (`0x200e`) | Recorded as a documentation-vs-live mismatch; not acted on (§2.1) |
| L-7 | No `dtc`/`fdtget` was used on the artefact; the decompiled `logs/dtb-decompiled.dts` was consulted only to cross-check the 905-node count | Stated so the numbers are traceable to bytes, not to a prior decompile |

**Not done, deliberately:** no build, no `dtc` invocation, no edit to DTS/DTB/config/patch, no copy or replacement of the candidate, no device, no ADB/root/fastboot, no partition read, no network fetch beyond the two published reports, no inspection of `matepad11/*` outside the four permitted directories, no inspection of the WorkBuddy Agent evidence tree or the AI2 workspace.

**Artefact integrity:** the candidate DTB was opened `rb` only. Its size and SHA-256 were unchanged after all reads (re-hashed at the end of the run: identical), and no other file in `out-dtb`/`logs`/`tree` was written.

---

## 8. Deliverable

- This report: `firmware-analysis/round152/AGENT2_ROUND152_CANDIDATE_DTB_STOCK_FDT_MEMORY_RESERVED_UFS_DELTA_REPORT.md`
- Branch: `agent2/round152-candidate-stock-fdt-memory-reserved-ufs-delta`
- Candidate artefact audited (not uploaded, not modified): `out-dtb/arch/arm64/boot/dts/qcom/huawei-dby-w09.dtb`, 108 648 B, `cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e`

**Stop condition reached.** No other round started, no candidate change, no compile, no device operation.
