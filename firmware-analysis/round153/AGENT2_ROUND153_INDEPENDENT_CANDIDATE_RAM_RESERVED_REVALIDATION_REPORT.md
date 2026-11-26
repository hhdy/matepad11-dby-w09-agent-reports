# AGENT2 ROUND153 — Independent candidate RAM / reserved-memory revalidation

- **Round:** 153
- **Branch:** `agent2/round153-independent-candidate-ram-reserved-revalidation`
- **Task type:** independent local artefact revalidation. No device, no ADB/root, no build, no `dtc`, no source edit.
- **Candidate:** ACK `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`, tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
- **Artefact audited (not modified, not uploaded):** `round140-agent2/out-dtb/arch/arm64/boot/dts/qcom/huawei-dby-w09.dtb`, 108 648 B, `cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e`.
- **Verdict summary:** RAM tuple map is **arithmetically sound and stock-identical for this unit**; 18 reserved-memory intervals are **sound, non-overlapping and fully contained**; two **hard blockers outside the RAM arithmetic** were found (malformed expected digest in the task lineage; `/rootparam` overlay fixup has no base symbol in the built DTB).

---

## 0. Execution identity, scope, and what this report claims

### 0.1 Who actually executed this

The taskbook assigns this round to **2号 Agent** and asks for explicit self-identification. This report was **not** produced by a 2号 Agent process. It was produced by the **WorkBuddy-side executor** (the same physical lane that ran ROUND152), operating on this host, reading only the frozen **Agent2 workspace paths** listed in taskbook §2:

| Path | Use |
|---|---|
| `/home/kerneldev/work/matepad11/round140-agent2/out-dtb/arch/arm64/boot/dts/qcom/huawei-dby-w09.dtb` | primary artefact, opened `rb` only |
| `/home/kerneldev/work/matepad11/round140-agent2/tree/arch/arm64/boot/dts/qcom/*` | `dts`/`dtsi` source evidence |
| `/home/kerneldev/work/matepad11/round140-agent2/logs/stage-b4-dtb-build-and-structure.log` | provenance of the identity criterion |

Consequences, stated plainly because the taskbook makes them load-bearing:

1. **The provenance requirement of this round is not met by this file.** ROUND152's defect was "a WorkBuddy-side executor produced an Agent2-labelled deliverable"; that defect is *repeated* here by construction, because no 2号 Agent process was available to this session. Marking this report as "2号 Agent independent verification" would be a false claim and is therefore **refused**.
2. What the round *does* deliver is a **second, from-scratch computation** of every number, using a parser written by this executor in ROUND138 (`_r138/fdt138.py`, copied to `_r153/` for this round) and **no ROUND152 figure as input**. Every ROUND152 value appears below only as a *comparison target* (§4.4), after my own value was computed.
3. If the orchestrator re-runs this taskbook inside an actual Agent2 environment, the checks in §5 should reproduce byte-for-byte; the parser and commands are given so the result is auditable rather than trusted.

### 0.2 Inputs read (grades in §6)

| Input | Class | Read-only? |
|---|---|---|
| Candidate DTB (binary) | frozen artefact | yes, `rb`, hash re-verified before and after |
| Candidate `tree/…/qcom/huawei-dby-w09.dts`, `sm8250.dtsi` | frozen source | yes |
| `logs/stage-b4-dtb-build-and-structure.log` | frozen provenance log | yes |
| `WORKBUDDY_ROUND151_ROOT_READONLY_RUNTIME_AUDIT_REPORT.md` (published, branch `workbuddy/round151-root-readonly-runtime-audit`) | permitted comparison input | downloaded copy only |
| `AGENT2_ROUND152_…_DELTA_REPORT.md` (published, branch `agent2/round152-…`) | permitted comparison input | downloaded copy only |

### 0.3 What was *not* read

No WorkBuddy local evidence tree, no 2号 AI private workspace, no other Agent workspace, no device, no `/proc/iomem` capture of my own, no ADB, no root, no fastboot, no partition image. Where a stock-side number is used (RAM windows, 37 stock reserved-memory children, `/proc/iomem` corroboration), it is **quoted from the published R151 report and labelled C**, never re-derived from an inaccessible artefact.

### 0.4 Prohibitions honoured

- No source edit, no patch, no `.dts` write, no build invocation, no `dtc` invocation (the frozen dtc at `out-dtb/scripts/dtc/dtc` was **not** executed; the pre-existing `logs/dtb-decompiled.dts` was likewise not regenerated).
- No write of any kind into `tree/`, `out-dtb/`, `logs/`, `a30build/`. The only writes were my own scratch scripts under `_r153/` on this host.
- DTB hash and mtime unchanged across the whole audit: `sha256_pre == sha256_post`, `mtime = 2026-11-26 20:25:31 +0800`.
- No raw FDT, no firmware bytes, no serial/IMEI/MAC/panel data in this report. The only binary values published are DT properties (addresses, sizes, phandles), which the taskbook itself requires.

---

## 1. A — Candidate DTB identity and the RAM tuple

### 1.1 Identity: size PASS, digest criterion BROKEN (finding F-1)

| Check | Value | Result |
|---|---|---|
| file size | 108 648 B | matches taskbook §0 expectation |
| FDT magic | `0xd00dfeed` | valid |
| FDT `totalsize` | 108 648 | equals file size (no trailing slop, no truncation) |
| FDT `version` / `last_comp_version` | 17 / 16 | normal |
| `sha256_pre` (before inspection) | `cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e` | — |
| `sha256_post` (after inspection) | identical | artefact untouched |

The taskbook's expected digest is:

```
cab82fe3901dbb40533197eb48b2d99b08b46e5d5497ff1a6f688e9938db77e
```

**This string is 63 hexadecimal characters.** A SHA-256 digest is 256 bits = **64** hex characters. The expected value is therefore *not a syntactically valid SHA-256* and cannot be satisfied by any file. Character-level comparison against the artefact:

| Property | Expected (taskbook) | Actual (artefact) |
|---|---|---|
| length | 63 | 64 |
| first divergence | offset 11 | offset 11 |
| local context | `…82fe3901` **`dbb4`** `0533197eb…` | `…82fe3901` **`bdb4`** `0533197ee…` |

Removing the evidently duplicated `b` still leaves a second mismatch (`…197eb…` vs `…197ee…`), so this is **not a one-character transcript slip that can be repaired by inspection**; the expectation string itself is corrupt.

This has a documented history inside the frozen workspace. ROUND140's Stage-B4 log already recorded the same pair as a **failed** criterion:

```
logs/stage-b4-dtb-build-and-structure.log:65  dtb_size=108648 expected_size=108648 match=YES
logs/stage-b4-dtb-build-and-structure.log:66  dtb_sha256=cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e
logs/stage-b4-dtb-build-and-structure.log:67  expected_sha256=cab82fe3901dbb40533197eb48b2d99b08b46e5d5497ff1a6f688e9938db77e
logs/stage-b4-dtb-build-and-structure.log:68  DTB_SHA_MATCH=NO
```

**Finding F-1 (grade A):** the candidate DTB identity is confirmed by **size (108 648 B, exact), FDT `totalsize` equality, and hash stability across the audit**. The *expected digest* in the taskbook (and in ROUND140/147 lineage) is a **63-character string that is not a SHA-256**, so `DTB_SHA_MATCH` can never be `YES` regardless of the artefact. This round therefore reports identity as **PASS on size + self-consistency, UNVERIFIABLE on digest**, and explicitly refuses to declare a hash match. Correcting the criterion is a task-document action, not an artefact action.

> Discrepancy against ROUND152: R152 §1 answered "Does the candidate DTB match the expected identity?" with **"Yes"**, recording the actual digest and the expected one as the same prefix. Both statements are literally *printed* in R152 (lines 51-53), but the conclusion "Yes" overstates what a 63-character expectation can support. Recorded in §4.4 as D-1 rather than silently inherited.

### 1.2 Tree scale (context for the census below)

| Metric | Value |
|---|---|
| nodes | 905 |
| properties | 3 443 |
| root-level children | 23 |
| nodes carrying a `phandle` property | 239 |
| `/__symbols__`, `/__fixups__`, `/__local_fixups__` | **absent** (see §3.3) |

905 nodes is consistent with the published R147 figure for the same candidate class (905), an independent structural cross-check of the artefact's identity beyond its hash.

### 1.3 Root-level `device_type = "memory"` census (finding F-2)

Scanning **every node in the whole tree** for `device_type = "memory"` returns exactly **one** hit:

| Path | `reg` cells | base | size |
|---|---|---|---|
| `/memory@80000000` | `[0, 0x80000000, 0, 0x0]` | `0x80000000` | **`0x0`** |

Its full property set is `{device_type = "memory", reg = <0x0 0x80000000 0x0 0x0>}` — no `status`, no `usable-memory`, nothing else.

The 18 children of `/reserved-memory` are named `memory@…` as well but **none of them carries `device_type`**, so they are not memory nodes and must not be counted as such. Confirmed by direct enumeration: `/reserved-memory` has exactly 18 direct children and zero of them expose `device_type`.

Provenance of the zero-size placeholder is unambiguous in the frozen source:

```
tree/arch/arm64/boot/dts/qcom/sm8250.dtsi:683  memory@80000000 {
tree/arch/arm64/boot/dts/qcom/sm8250.dtsi:684          device_type = "memory";
tree/arch/arm64/boot/dts/qcom/sm8250.dtsi:685          /* We expect the bootloader to fill in the size */
tree/arch/arm64/boot/dts/qcom/sm8250.dtsi:686          reg = <0x0 0x80000000 0x0 0x0>;
tree/arch/arm64/boot/dts/qcom/sm8250.dtsi:687  };
```

The board file deliberately does **not** define one, and says so (`huawei-dby-w09.dts:309-316`, `:319-321`). So the compiled DTB's single memory node is inherited, not board-authored — the "do not create a second node" constraint of taskbook §A.6 is therefore already the tree's own intent.

### 1.4 Tuple cell width and every base/size pair (finding F-3)

| Property | Value | Consequence |
|---|---|---|
| root `#address-cells` | 2 | base = two 32-bit cells |
| root `#size-cells` | 2 | size = two 32-bit cells |
| `/memory@80000000` local `#address-cells`/`#size-cells` | absent | inherits root 2/2 |
| `/reserved-memory` `#address-cells`/`#size-cells` | 2 / 2, `ranges` present but empty | identity mapping, same 4-cell tuples |
| current `reg` length | 4 cells | **one** tuple, size 0 |

So a 3-window map needs exactly **12 cells**, and any 8- or 16-cell form would be a different (wrong) shape. The existing 4-cell form is well-formed but degenerate: it declares a base with no extent.

### 1.5 The proposed RAM map, verified arithmetically (finding F-4)

| # | base | size | end (exclusive) | MiB | 4 KiB aligned | 64 KiB aligned |
|---:|---|---|---|---:|---|---|
| 1 | `0x0000000080000000` | `0x0000000039900000` | `0x00000000b9900000` | 921.0 | yes | yes |
| 2 | `0x00000000c0000000` | `0x00000000c0000000` | `0x0000000180000000` | 3 072.0 | yes | yes |
| 3 | `0x0000000200000000` | `0x0000000200000000` | `0x0000000400000000` | 8 192.0 | yes | yes |
| | | **total** | | **12 185.0** | | |

Independent checks, each computed rather than quoted:

| Check | Result |
|---|---|
| ascending base order (`0x80000000 < 0xc0000000 < 0x200000000`) | true |
| pairwise overlap | **none** (all three disjoint) |
| gap 1→2 | `0xb9900000 … 0xc0000000` = `0x6700000` = **103.000 MiB** |
| gap 2→3 | `0x180000000 … 0x200000000` = `0x80000000` = **2 048.000 MiB** |
| highest end vs 64-bit wrap | `0x400000000 < 2^64`, no overflow |
| sum | `0x2f9900000` = **12 185 MiB**, equals 921 + 3 072 + 8 192 |
| window 3 requires the high cell | base/size `0x200000000` = `<0x2 0x0>`; a 32-bit-only encoding would truncate to 0 |

The two gaps are not errors: `0xb9900000–0xc0000000` is the firmware/ABL window below the second DRAM bank, and `0x180000000–0x200000000` is the 2 GiB hole between the 4 GiB boundary and the second high bank on Kona. They are properties of the physical map as published, and the FDT must not fill them.

**F-4 verdict:** the three tuples are internally consistent, non-overlapping, correctly ordered, 64 KiB-aligned and sum to the stated 12 185 MiB. Nothing in the arithmetic depends on a value from ROUND152.

### 1.6 Corroboration against the published stock evidence (finding F-5)

From the published R151 report §3.5 (grade C — I did not read a stock FDT myself):

| # | stock base | stock size | `/proc/iomem` line quoted in R151 |
|---:|---|---|---|
| 0 | `0x80000000` | `0x39900000` | `80000000…b98fffff : System RAM` (split by carve-out holes) |
| 1 | `0x200000000` | `0x200000000` | `200000000-3ffffffff : System RAM` |
| 2 | `0xc0000000` | `0xc0000000` | `c0000000-ffbfffff` + `ffc20000-17fffffff : System RAM` |

- **Base and size match, all three, exactly.** No digit differs. So the map the taskbook proposes is not a reconstruction — it is the published live map of this unit (`MemTotal` 11 984 584 kB in R151, declared 12 185 MiB, the difference being carve-outs plus kernel/DMA).
- **Ordering differs, harmlessly.** Stock declares `0x80000000`, `0x200000000`, `0xc0000000`; the taskbook §A.4 lists them ascending (`0x80000000`, `0xc0000000`, `0x200000000`). `reg` tuple order has no semantic weight — `early_init_dt_scan_memory()` calls `memblock_add()` once per tuple and memblock sorts/merges — so **both orders boot identically**. For diffability against the stock FDT, reproducing the stock order is nevertheless preferable; see §4.5.
- **One iomem nuance that must not be smoothed over:** the second window is *declared* as one contiguous 3 GiB range, but `/proc/iomem` shows a **128 KiB non-RAM hole at `0xffc00000–0xffc1ffff`** inside it. The correspondence is therefore **window-level, not byte-level**: the declared `size` is stock-correct, while a small part of that window is not System RAM at runtime. This does not change the tuple to write (the stock FDT itself declares the full 3 GiB), but any later claim of "byte-exact iomem correspondence" would be wrong.

### 1.7 What a RAM-only DTS diff must look like (finding F-6)

The change is a **property replacement on the existing node path**, not a new node. Cell-exact form (`ac=2 / sc=2`):

```dts
/* cells: <base_hi base_lo size_hi size_lo> per tuple, 3 tuples = 12 cells */
memory@80000000 {
	reg = <0x0 0x80000000 0x0 0x39900000>,	/* 921 MiB  */
	      <0x0 0xc0000000 0x0 0xc0000000>,	/* 3072 MiB */
	      <0x2 0x00000000 0x2 0x00000000>;	/* 8192 MiB, base/size 0x200000000 */
};
```

Why this shape and not another:

1. **Same node name and unit address (`memory@80000000`) ⇒ same path ⇒ property merge, not a second node.** dtc merges same-path nodes; the resulting tree still has exactly one `device_type = "memory"` node. A node named e.g. `memory@c0000000` would create a *second* memory node and violates both taskbook §A.6 and the tree's own guard comment.
2. **The board file cannot use `&memory`** — `sm8250.dtsi:683` declares no label — so the board-level override must be the same-path node form above. (Alternatively `&{/memory@80000000}` would work if the tree's dtc version is used consistently; the plain same-path node is the lower-risk form.)
3. **`device_type` need not be restated**; it is inherited from `sm8250.dtsi:684`. Restating it is harmless but adds diff noise.
4. **The guard comment must be updated in the same change.** `huawei-dby-w09.dts:316` currently asserts "The final ABL-provided RAM tuple and reservation map remain UNKNOWN." After this edit the tuple is *written*, not ABL-provided — leaving that sentence in place would make the source lie about itself. Text-only change; no behaviour.
5. **This is a text recommendation, not an applied change.** No file was edited in this round.

---

## 2. B — Candidate reserved-memory census

### 2.1 All 18 children, placement-relevant properties

Every child has `reg` and `no-map`; **none** has `reusable`, `shared-dma-pool`, `linux,cma-default`, `size`, `alignment`, or `alloc-ranges`. Six carry a `phandle`.

| # | node (`/reserved-memory/…`) | base | size | MiB | flags | phandle | consumed by |
|---:|---|---|---|---:|---|---:|---|
| 1 | `memory@80000000` | `0x80000000` | `0x600000` | 6.000 | no-map | — | — |
| 2 | `memory@80700000` | `0x80700000` | `0x160000` | 1.375 | no-map | — | — |
| 3 | `memory@80860000` | `0x80860000` | `0x20000` | 0.125 | no-map, `compatible="qcom,cmd-db"` | — | RPMh cmd-db |
| 4 | `memory@80900000` | `0x80900000` | `0x200000` | 2.000 | no-map | 43 | `/smem` (enabled) |
| 5 | `memory@80b00000` | `0x80b00000` | `0x5300000` | 83.000 | no-map | — | — |
| 6 | `memory@86200000` | `0x86200000` | `0x500000` | 5.000 | no-map | — | — |
| 7 | `memory@86700000` | `0x86700000` | `0x100000` | 1.000 | no-map | — | — |
| 8 | `memory@86800000` | `0x86800000` | `0x10000` | 0.0625 | no-map | — | — |
| 9 | `memory@86810000` | `0x86810000` | `0xa000` | 0.0391 | no-map | — | — |
| 10 | `memory@8681a000` | `0x8681a000` | `0x2000` | 0.0078 | no-map | 115 | `gpu@3d00000/zap-shader` (**disabled** GPU) |
| 11 | `memory@86900000` | `0x86900000` | `0x500000` | 5.000 | no-map | — | — |
| 12 | `memory@86e00000` | `0x86e00000` | `0x500000` | 5.000 | no-map | 187 | `video-codec@aa00000` (**disabled**) |
| 13 | `memory@87300000` | `0x87300000` | `0x500000` | 5.000 | no-map | — | — |
| 14 | `memory@87800000` | `0x87800000` | `0x1400000` | 20.000 | no-map | 172 | `remoteproc@8300000` CDSP (**disabled**) |
| 15 | `memory@88c00000` | `0x88c00000` | `0x1500000` | 21.000 | no-map | 120 | `remoteproc@5c00000` SLPI (**disabled**) |
| 16 | `memory@8a100000` | `0x8a100000` | `0x1d00000` | 29.000 | no-map | 207 | `remoteproc@17300000` ADSP (**disabled**) |
| 17 | `memory@8be00000` | `0x8be00000` | `0x100000` | 1.000 | no-map | — | — |
| 18 | `memory@8bf00000` | `0x8bf00000` | `0x4600000` | 70.000 | no-map | **none** | **none** (§2.3) |

Formatting checks performed on all 18: `reg` is always 4 cells; the node's unit address always equals the low base cell (18/18 `MATCH`); no node has a `status` (OF default: not disabled).

### 2.2 Sum, union, overlap, containment (finding F-7)

| Metric | Value |
|---|---|
| entries with `reg` | 18 / 18 |
| arithmetic sum | `0xfe9c000` = 266 977 280 B = **254.609 MiB** |
| union | **254.609 MiB** (identical to the sum ⇒ **zero overlap**) |
| disjoint segments | 5 |
| pairwise overlaps | **NONE** |
| intervals outside the three RAM windows | **0** (all 18 lie inside window 1, `0x80000000 + 0x39900000`) |
| highest reserved end | `0x90500000`, i.e. 660 MiB below window-1 end `0xb9900000` |

Union segments: `[0x80000000,0x80600000)` 6.000 · `[0x80700000,0x80880000)` 1.500 · `[0x80900000,0x85e00000)` 85.000 · `[0x86200000,0x8681c000)` 6.109 · `[0x86900000,0x90500000)` 156.000.

Two adjacencies fall out exactly, which is a useful independent sanity check of the table above (they are not coincidences of rounding, they are byte-exact):

- `0x8be00000 + 0x100000 = 0x8bf00000` (node 17 abuts node 18)
- `0x8bf00000 + 0x4600000 = 0x90500000` (node 18 sets the highest reserved byte)

### 2.3 The 70 MiB carve-out at `0x8bf00000` (finding F-8)

| Question | Answer |
|---|---|
| Is it board-authored? | **No.** Inherited verbatim from `tree/…/qcom/sm8250.dtsi:862-865`: `cdsp_secure_heap: memory@8bf00000 { reg = <0x0 0x8bf00000 0x0 0x4600000>; no-map; };` |
| Does the candidate tree contain any consumer? | **No.** The node has **no `phandle` property at all**; therefore no `memory-region`/`*-supply`/`phandle` property anywhere can reference it. Whole-tree phandle resolution found 6 `memory-region` references, none to `0x8bf00000`. |
| Does any enabled driver need it? | **No evidence of one.** The CDSP PAS node that would own it, `/soc@0/remoteproc@8300000` (`qcom,sm8250-cdsp-pas`), is `status = "disabled"` and points at `0x87800000` (20 MiB `pil_cdsp_region`) instead. |
| What does stock do with the same node? | R151 lists `cdsp_secure_heap@8bf00000` with **no `reg`, no `size`** (unplaced, `removed-dma-pool`). So stock reserves nothing there; the candidate is the *more* conservative of the two. |
| Does it collide with anything? | No. No other candidate interval, and no stock-only stock interval (§2.4), overlaps `[0x8bf00000, 0x90500000)`. |
| Cost if kept | 70 MiB of usable RAM = **0.57 %** of the 12 185 MiB declared map. |
| Recommendation | **Keep. Do not remove in the RAM-only change.** It is upstream-inherited, no-map, harmless to boot, and removing it is a separate decision that would need a consumer survey this round did not perform. Deleting a `no-map` reservation without consumer evidence is exactly the class of change that produces silent DSP firmware corruption later. |

This matches R152's P-4 framing (keep-or-drop both defensible). The difference is that this round adds the *structural* reason the drop cannot be justified: the node has no phandle, so "no consumer" is not merely "no consumer found", it is "**the DTB makes consumption impossible**" — which is an argument for either course, and therefore for keeping the status quo until CDSP is enabled.

### 2.4 Stock-only fixed coverage: the 40.080 MiB, re-derived (finding F-9)

Comparing the 18 candidate intervals against R151's 37 stock children (grade C for the stock side) leaves exactly **7** stock `reg`-bearing nodes with no candidate counterpart, plus `kerneldump`:

| stock node | interval | MiB |
|---|---|---:|
| `cont_splash_region@9c000000` | `0x9c000000 + 0x2300000` | 35.000 |
| `disp_rdump_region@9c000000` | `0x9c000000 + 0x800000` | 8.000 |
| `dfps_data_region@9e300000` | `0x9e300000 + 0x100000` | 1.000 |
| `rainbow_mem@b0000000` | `0xb0000000 + 0x400000` | 4.000 |
| `bootfail_mem@b0400000` | `0xb0400000 + 0x800` | 0.00195 |
| `res_xbl_uefi_log_region@80880000` | `0x80880000 + 0x14000` | 0.07813 |
| `kerneldump` | `0x0 + 0x0` | 0 |

Two exact adjacencies inside the stock table corroborate R151's own numbers (and therefore the derivation):

- splash end `0x9c000000 + 0x2300000 = 0x9e300000` = dfps base — exact
- rainbow end `0xb0000000 + 0x400000 = 0xb0400000` = bootfail base — exact

**Uncovered union.** `disp_rdump` is a strict subset of `cont_splash`, so it adds no coverage:

```
35 + 1 + 4 + 0.078125 + 0.001953125 = 40.080078125 MiB = 42 027 008 B
```

That reproduces R152's `42 027 008 B / 40.080 MiB` exactly, but here it is derived from the interval list rather than quoted. Including the 8 MiB `disp_rdump` (naive sum) would give 48.080 MiB; the taskbook's "40.080 MiB" figure is the *union* figure and is the correct one.

**Do these omissions block boot?** Not on the arithmetic. Their status is:

| omitted stock node | honestly required for bring-up? |
|---|---|
| `cont_splash` 35 MiB, `disp_rdump` 8 MiB, `dfps_data` 1 MiB | **no**, while no display driver is enabled; **yes** before touching DSI/panel, because a still-scanned-out splash framebuffer would be recycled by the allocator |
| `rainbow_mem` 4 MiB | **no** — Huawei splash/rainbow artifact; no candidate consumer |
| `bootfail_mem` 2 KiB | **no** — Huawei ABL crash record; ABL may write it, but the kernel does not own it |
| `res_xbl_uefi_log` 80 KiB | **no** — XBL/UEFI log handoff, read-only after boot |

So the 40.080 MiB gap is a **display/Huawei-integration debt**, not a memory-map defect, and re-adding any of it is out of scope for a RAM-only change.

### 2.5 The 12 dynamic pools and the algebra that closes (finding F-10)

R151 counts the stock group as `23 static (non-zero reg) + 1 zero-size + 13 dynamic`. Of those 13 reg-less nodes, **one** is `cdsp_secure_heap@8bf00000` — which the candidate places statically at 70 MiB. That leaves **12 reusable pools** absent from the candidate, and the candidate indeed contains **zero** nodes with `size`/`alignment`/`alloc-ranges`.

| Path | absent from candidate | consumer enabled in candidate? |
|---|---|---|
| `adsp_region`, `cdsp_region`, `sdsp_region` | yes | no (DSP PAS disabled) |
| `mem_dump_region`, `sp_region`, `user_contig_region` | yes | no |
| `qseecom_region`, `qseecom_ta_region`, `secure_display_region` | yes | no |
| `cnss_wlan_region` | yes | no (no WLAN node) |
| `mailbox_region` | yes | no direct consumer |
| **`linux,cma`** (32 MiB, `linux,cma-default`) | yes | **system-wide**: see below |

**Closure check (all four numbers independently computed, then combined):**

```
candidate 254.609375
  = stock static sum 232.689453
  − stock-only union 40.080078
  − disp_rdump subset 8.000000
  + newly placed cdsp_secure_heap 70.000000
  = 254.609375   ✔ residual 0.000000
```

The same identity through the *union* route, which must exclude `disp_rdump` only once:

```
(232.689453 − 8.000000) − 40.080078 + 70.000000
  = 224.689453 − 40.080078 + 70.000000
  = 184.609375 + 70.000000
  = 254.609375   ✔ same value, different construction
```

Both routes agree to the byte with no slack term. That is the strongest available proof that the 17 "exact" matches are exact in aggregate as well as per node — a single wrong `size` in the candidate would have to be cancelled by a compensating error elsewhere to keep the total, and the per-node table in §2.1 rules that out independently.

**`linux,cma` deserves its own sentence.** With no `linux,cma-default` node, no default CMA area is registered. At bring-up with only UFS enabled this is not a boot blocker; the moment any DMA-contiguous consumer (display, camera, WLAN, ion-style heap) is enabled, it becomes one. Absence of CMA is a **functional debt**, not an arithmetic error, and it is *not* something the RAM-only change should try to fix.

**Do not treat the vendor pools as mandatory.** Every one of the 12 is referenced by a disabled or absent node; promoting any of them into the DTS without its driver adds reserved bytes with no benefit. The only structural consumer that a *host-visible* enabled node uses is `smem_region` (2 MiB, `/smem` has no `status`), and that one is present.

### 2.6 Does the RAM-only edit move any reservation? (finding F-11)

**No interval changes.** The reserved-memory children have absolute `reg` values and are unaffected by `/memory`'s `size`. What *does* change is their **validity status**, and this is the most under-stated part of the whole plan:

| State | `/memory` size | Consequence |
|---|---|---|
| today | `0x0` | memblock receives no RAM at all. The 18 `no-map` carve-outs are then reservations of memory the kernel never added — structurally orphaned. `paging_init()` on an empty memblock is not a bootable configuration. |
| after RAM-only edit | 3 windows | All 18 intervals fall inside window 1 and become real `memblock_reserve()` calls that carve usable RAM out of declared RAM. |

So the RAM tuple is a **prerequisite** for the reserved-memory table to mean anything, and the two are consistent *only after* the edit. Conversely: the edit cannot be validated in isolation — a boot with the tuple but with a wrong carve-out would fault inside a reserved area, and the 18 intervals are all inside window 1 where the kernel will now place page tables and slab.

---

## 3. C — Board ID / DTBO cross-reference

### 3.1 Candidate root identity vs the published live root (finding F-12)

| Property | candidate DTB | published live stock root (R151 §3.3, grade C) | note |
|---|---|---|---|
| `qcom,board-id` | `<0x0 0x0>` (`huawei-dby-w09.dts:39`) | `<0x200e 0x0>` | **differs** |
| `qcom,msm-id` | `<356 0x20001>` = `<0x164 0x20001>` | `<0x164 0x20001>` | identical |
| `compatible` | `huawei,dby-w09`, `qcom,sm8250` | `qcom,kona-qrd`, `qcom,kona`, `qcom,qrd` | differs (no `huawei` compat in live root) |
| `model` | `Huawei MatePad 11 (2021) DBY-W09` | `Huawei Technologies, Inc. DBY-W09` | cosmetic |
| `chassis-type` | `tablet` | (not listed in R151) | — |
| root children | 23 | 83 | expected for a minimal draft |
| `/rootparam` | present, **zero properties** | populated (7 property names, R138 §4.1) | see §3.3 |

The `0x206a` statement adjacent to `qcom,board-id` is:

```
huawei-dby-w09.dts:35-36
 *   Keep the SoC DTB board-id at zero; the separate DBY-W09 DTBO is
 *   selected by board-id 0x206a and fills /rootparam for Huawei ABL.
```

Cross-reference against published rounds:

- R138 §2: all nine stock DTBO entries carry `qcom,board-id` on the **overlay root**; entry 8 = `8298 = 0x206A`, entry 2 = `8206 = 0x200E`.
- R151 §3.4: `androidboot.dtbo_idx=2` on the live boot ⇒ the applied overlay is **entry 2 ⇒ 0x200E**, not entry 8.
- R138 F1: entry 8 is **unsupported** on this device, not "wrong" — the only direct selection evidence points at entry 2.

**So the candidate comment encodes the entry-8 hypothesis, and the only device-side evidence contradicts it.** This is a *documentation* defect inside the frozen tree, not a DTB defect. R152 already recorded the same mismatch (its L-6), so this round **confirms rather than discovers** it; it is restated because it conditions any DTBO pairing plan and because the RAM change should not be bundled with a board-id change.

### 3.2 Every DTBO assumption embedded in the candidate DTS

| Location | Assumption | Standing against published evidence |
|---|---|---|
| `huawei-dby-w09.dts:13-16` | stock entry 8 is incompatible with this base; it "contains 145 fragment targets"; pair only with a reviewed minimal DBY-W09 rootparam DTBO | **corroborated**: R138 measured 145 fragments in entry 8 (grade C) |
| `:35-36` | base `board-id = 0`; DTBO selected by `board-id 0x206a` | **contradicted** for this unit (`dtbo_idx=2` ⇒ `0x200e`) |
| `:42-47` | `rootparam` label "is required by `dby-w09-ack18-rootparam.dtso.draft`"; board identity values come from the matching DTBO | **file does not exist** in the frozen tree (§3.4) |
| `:54-58` | ROUND13 scanned HOS4.3 base FDT + all nine entries; nine entries leave the RSC regulator subtree untouched; selected entry UNKNOWN | superseded for this boot by R151 (`dtbo_idx=2`) |
| `:296` | DTBO inventory carries `vdda-phy-always-on` (UFS PHY) | out of scope here; recorded in ROUND139 lineage |

### 3.3 New finding: the `/rootparam` fixup has no base symbol in the built DTB (finding F-13)

This is the one finding of the round that was neither asked for by the taskbook nor present in R152, and it is a hard structural blocker for the documented overlay contract.

The mechanism the stock firmware uses (R138 §2, grade C): every stock entry carries
`/__fixups__ { rootparam = "/fragment@N:target:0"; }` — a **placeholder phandle** that only resolves if the base FDT exposes the symbol `rootparam` through `/__symbols__` plus a phandle on the node.

The candidate artefact does not provide that substrate:

| Requirement for a `__fixups__`-style overlay | candidate DTB |
|---|---|
| `/__symbols__` node | **absent** |
| `/__fixups__` node | **absent** |
| `/__local_fixups__` node | **absent** |
| `phandle` on `/rootparam` | **absent** — `/rootparam` has **zero properties** |
| labelled-node phandles elsewhere | present (239 nodes carry `phandle`, e.g. the six reserved-memory regions) |

Interpretation (mechanism grade D, observation grade A): the DTB was built **without `-@`**, so dtc emitted phandles for nodes that need them for internal references but did **not** emit `__symbols__`, and `/rootparam` — which nothing in the tree references — got no phandle at all. Therefore a stock-style fixup overlay naming `rootparam` **cannot bind** to this DTB: the symbol table it needs is not there. The path that would work is a `target-path = "/rootparam"` overlay (no fixup needed), and R138 established that **no stock entry uses `target-path`** (0/9).

Consequences, stated as conditions rather than solutions (settling the overlay is explicitly out of scope for this round):

1. Either the candidate build must add `-@` (DTC_FLAGS) for this target **and** the tree must be rebuilt, or
2. The DBY-W09 minimal DTBO must be authored with `target-path`, deviating from all nine stock entries.

Until one of those is chosen, the sentence "the label is required by `dby-w09-ack18-rootparam.dtso.draft`" (`:42`) describes an intent the built artefact cannot satisfy.

### 3.4 Dangling source reference (finding F-14)

`huawei-dby-w09.dts:42` cites `dby-w09-ack18-rootparam.dtso.draft`. A whole-tree search for `*rootparam*` returns **no file**; the only DBY-W09 sources present are `huawei-dby-w09.dts` and `dby-w09-proxy-review.dts` (the latter is a PM8150 proxy-supply review artefact, unrelated to memory). So the only documented consumer of the `rootparam` label **does not exist in the frozen tree**, which is consistent with F-13's conclusion and independent of it.

### 3.5 Explicitly *not* settled here

Per taskbook §C and §4: the Entry 2 vs Entry 8 fragment-by-fragment comparison, the fixup-resolution census across all nine entries, which overlay ABL actually applies on a *future* boot, and whether the device `dtbo` partition equals the E1 package are **not** resolved by this report. The values above are cross-references to R138/R151 and are labelled C wherever they come from those reports.

---

## 4. D — Independent conclusion

### 4.1 Verdicts

| # | Question | Verdict | Basis |
|---:|---|---|---|
| 1 | Candidate DTB identity | **PASS on size / totalsize / hash-stability; UNVERIFIABLE on the stated digest** | F-1: expected string is 63 hex chars |
| 2 | Proposed 3-window RAM map arithmetically sound for this unit | **YES** | F-4: no overlap, ascending, 64 KiB-aligned, 12 185 MiB, no overflow |
| 3 | Same map as the published live stock map | **YES, base and size identical for all three** (sequence differs, semantics neutral) | F-5 |
| 4 | 18 reserved-memory intervals sound | **YES** | F-7: sum = union = 254.609 MiB, 0 overlaps, 0 outside RAM |
| 5 | 70 MiB CDSP carve-out | **KEEP for now; unreferenced and unconsumable as built** | F-8 |
| 6 | Does the RAM-only edit disturb any reservation | **NO** | F-11 |
| 7 | Board-id / DTBO documentation | **One contradiction (0x206a vs 0x200e) and one hard structural blocker (`__symbols__` absent)** | F-12, F-13 |

### 4.2 Device/SKU generalisation that is **not** justified

The three tuples describe **this unit**, whose declared map is 12 185 MiB and whose `MemTotal` was 11 984 584 kB. They are physical-population facts, not SoC facts:

- A 6 GiB or 8 GiB DBY-W09 (or any other Kona device) does **not** have a 3 GiB `0xc0000000` bank or an 8 GiB `0x200000000` bank. Hard-coding this tuple into a *shared* DTS/DTSI silently describes memory that is not there, and `memblock_add()` of absent DRAM is not a recoverable error — it faults on first touch.
- Therefore: the tuple is safe **only** in a device-specific board file that is built **only** for this SKU, and **only** if the team accepts losing bootloader-driven RAM population. That is a deliberate trade (deterministic map vs portable DTB), not a bug fix, and it should be recorded as such.
- The upstream `reg = <0x0 0x80000000 0x0 0x0>` placeholder exists precisely because the bootloader knows the population and the DTS does not. Writing the tuple is an override of that contract for one device.
- Do **not** generalise "12 185 MiB" to "MatePad 11 (2021)"; it is "this unit, this boot, this SKU".

### 4.3 Unresolved conditions, with what would close each

| # | Condition | Status | Closes with |
|---:|---|---|---|
| U-1 | Does ABL fill `/memory` for an ACK-built DTB? | **UNKNOWN**. The stock *live* map is populated, the stock *base* FDT is asserted zero-size (`huawei-dby-w09.dts:319`), and R138 found no `/memory` target among entry-2/8 fragments — so "ABL fills it" is a leading hypothesis, **not** a proven fact. | one boot of a DTB with the placeholder intact, then read `/proc/iomem` / live FDT |
| U-2 | Which DTBO entry will ABL select for the new base? | **UNKNOWN** for a new base; for the *stock* boot it was entry 2 (`dtbo_idx=2`) | build-time board-id decision + ABL behaviour on a `0/0` base |
| U-3 | Can a stock-style fixup overlay bind at all? | **NO as built** (no `__symbols__`, no `rootparam` phandle) | `-@` in DTC_FLAGS, or a `target-path` overlay |
| U-4 | Is the 70 MiB CDSP heap needed? | **Not by anything enabled**; unconsumable as built | enable CDSP PAS and add the reference, or drop the `reg` |
| U-5 | Missing CMA / splash / DFPS at display bring-up | **deferred debt** (F-9, F-10) | display driver enablement |
| U-6 | Real digest of the expected artefact | **criterion corrupt** (63 chars) | fix the task-document lineage; the artefact hash is stable and recorded |

### 4.4 Discrepancies against ROUND152 (reported, not inherited)

Every ROUND152 claim in the compared surface was recomputed from the artefact. Result:

| # | R152 claim | This round | Status |
|---:|---|---|---|
| 1 | candidate DTB "matches the expected identity — **Yes**" | size/totalsize/hash-stability pass; the *expected* digest is a 63-char non-SHA-256 ⇒ digest criterion unsatisfiable | **D-1 DISCREPANT (overstated)** — R152 printed both digests but concluded "Yes" |
| 2 | 17 nodes exact by base **and size** | confirmed, all 17 base+size identical to R151's table | CONFIRMED |
| 3 | 1 same-base / new-reg node = `cdsp_secure_heap@8bf00000` +70 MiB | confirmed; additionally: node carries **no phandle**, i.e. unconsumable, and provenance is `sm8250.dtsi:862-865` | CONFIRMED + extended |
| 4 | 7 stock-static-only nodes | confirmed (splash, rdump, dfps, rainbow, bootfail, xbl-uefi-log, kerneldump) | CONFIRMED |
| 5 | uncovered stock union = 42 027 008 B = 40.080 MiB | re-derived from the interval list, including the exact splash→dfps and rainbow→bootfail adjacencies | CONFIRMED |
| 6 | 12 dynamic pools including `linux,cma`; 37 = 23+12+1+1 | confirmed; candidate contains **zero** dynamic pools | CONFIRMED |
| 7 | closure 254.609 − 70 = 184.609 = 224.689 − 40.080 | reproduced, residual 0.000 | CONFIRMED |
| 8 | board-id `0x206a` comment vs live `0x200e` mismatch (L-6) | confirmed, and it is the only device-side selection evidence | CONFIRMED |
| 9 | candidate root `reg = <0 0x80000000 0 0>`, single memory node | confirmed; **and** it is the only `device_type="memory"` node in all 905 nodes | CONFIRMED + extended |
| 10 | *(not covered by R152)* `/rootparam` overlay fixup substrate | **no `__symbols__`, no `__fixups__`, `/rootparam` has zero properties** | **D-2 NEW** |
| 11 | *(not covered by R152)* `dby-w09-ack18-rootparam.dtso.draft` | cited at `:42`, **absent from the tree** | **D-3 NEW** |

So: the arithmetic of R152 is **reproducible and correct**; its identity verdict is **overstated**; and two structural items were **missed** by it. No R152 number had to be corrected.

### 4.5 Minimal next change (recommendation only — nothing was applied)

Ranked, each independently revertible:

1. **RAM tuple only** (§1.7), one 12-cell `reg` on the existing `memory@80000000` path, plus the one-line comment correction at `huawei-dby-w09.dts:316`. Highest value, lowest risk, mathematically verified.
2. **Build flag / overlay path decision** before any DTBO pairing: either emit `__symbols__` (`-@`) or author the DTBO with `target-path` (F-13). Without this, `/rootparam` stays empty and the DTBO's fixups cannot resolve.
3. **Board-id decision** (`0/0` vs `0x200e` vs `0x206a`) — must follow a decision, not this report: the live unit says `0x200e`, the comment says `0x206a`, and the tree currently says `0/0` (F-12).
4. **Leave `cdsp_secure_heap`'s 70 MiB in place**; revisit only when CDSP PAS is enabled (F-8).
5. **Leave the reserved-memory list untouched** in this change; the 40.080 MiB and CMA debts are display/DSP-scope (F-9, F-10).

If only item 1 is taken, the result is a DTB that declares this unit's RAM correctly and still cannot accept a stock fixup overlay — which is exactly the state the current build is in, with one fewer blocker.

---

## 5. Method and reproduction

- Parser: `_r138/fdt138.py` (written in ROUND138, pure `struct` FDT walker, `rb` only), copied unmodified to `_r153/fdt138.py` for this round. Two drivers: `_r153/scan153.py` (identity, memory census, reserved-memory census, phandle/consumer resolution, RAM arithmetic) and `_r153/scan153b.py` (tree-wide `device_type` sweep, group-node properties, `__symbols__` presence, unit-address vs `reg` base).
- Executed with `python3` (3.12.3) inside the WSL distro that hosts the frozen workspace, with the artefact path hard-coded to the taskbook §2 location.
- Guardrails in the code: no `open(..., 'w')` on any artefact path; hash computed before and after the parse in the same process; `dtc`, `fdtdump`, `fdtget` never invoked; the pre-existing `logs/dtb-decompiled.dts` was not regenerated or written.
- Every figure in §1–§2 is printed by those two scripts; the report adds only the stock-side comparisons, which are attributed to R151/R138 inline and graded C.

## 6. Evidence grades

| Grade | Meaning | Findings |
|---|---|---|
| **A** | read directly from the frozen binary artefact by this executor | F-1 (size/totalsize/stability), F-2, F-3, F-4, F-7, F-8 (no phandle), F-11 (mechanism of `reg`), F-13 (absence of `__symbols__`), §2.1 table |
| **B** | read directly from frozen source text (`file:line`) | F-6 provenance (`sm8250.dtsi:683-687`), F-8 provenance (`:862-865`), F-12 comment (`:35-36`), F-14 (`:42`), `:309-321` |
| **C** | quoted from a published report as read-only comparison (R138/R151/R152) | stock RAM windows and `/proc/iomem` lines, 37 stock children, 232.689 MiB, entry 2/8 board-ids, `dtbo_idx=2`, live root identity |
| **D** | inference / mechanism reasoning not executed here | U-1 (ABL fill hypothesis), fixup-binding mechanism, "either `-@` or `target-path`" conclusion |

No finding above is graded A where it depends on a stock artefact this executor could not read.

## 7. Limitations

1. **Provenance** — §0.1; this file cannot substitute for a genuine 2号 Agent run.
2. One host for both artefact read and script execution; artefact integrity is evidenced by hash-before/after and mtime, not by an independent copy.
3. Stock-side numbers are report-derived (grade C). If R151's table were wrong, §1.6, §2.4 and §2.5 would inherit that error; the two internal adjacency checks (`0x9c000000+0x2300000 = 0x9e300000`, `0xb0000000+0x400000 = 0xb0400000`) and the byte-exact closure in §2.5 are what make that inheritance unlikely.
4. `/proc/iomem` corroboration is window-level, not byte-level (§1.6, 128 KiB hole).
5. No boot, no build, no `dtc` — so "the DTB with the tuple compiles and boots" is **not** demonstrated; only that the tuple is well-formed, in-range, non-overlapping and stock-identical.
