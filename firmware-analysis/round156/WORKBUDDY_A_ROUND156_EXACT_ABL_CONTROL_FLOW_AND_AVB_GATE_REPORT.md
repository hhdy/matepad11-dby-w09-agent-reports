# ROUND156 — WorkBuddy Window A: Exact ABL Control Flow, RAM and AVB Gate

- Executor: **WorkBuddy Window A (1号 Agent)**, continuing from its own ROUND155 live boot-chain capture.
- Window B is a separate WorkBuddy chat and was **not accessed**. No `round154-windowB` / `round155-windowB` path was read.
- Task type: **offline read-only reverse engineering**. No ADB/device connection, no partition read/write, no mount, no flash, no reboot, no fastboot, no recovery, no source edit/build, no signing, no vbmeta/flag modification.
- Analysis target: the exact `abl` / `xbl` / `xbl_config` binaries and the LZMA-extracted ABL PE32+ payload captured in Window A's own ROUND155 workspace, hash-verified before use.

**Status: COMPLETED and STOPPED at the report point.** Raw binaries, the decompressed PE payload, host paths and full logs remain local and are not uploaded.

---

## 0. Executive summary

This round moved past ROUND155's *string/xref* evidence to *control-flow* evidence. The decisive findings are:

| # | Question | Answer | Grade |
|---|----------|--------|-------|
| B | Does ABL walk all appended FDTs? | **Yes** — a loop back-edge at `0x3a338` (`cbnz w19, 0x39e8c`) re-enters the entry-walk; both "Single appended DTB found" and "Not the single appended DTB" branches exist. | A |
| B | Match order | **msm-id → board-id (major/minor) → pmic-id**, each a compare + `b.eq`/`b.ne` split, with a "Best match" accumulation. | A/B |
| B | Is a single candidate FDT accepted? | **Structurally yes** — the single-DTB path is a first-class branch; no hard requirement for 3 FDTs. Required root tags are `qcom,msm-id`/`qcom,board-id`/`qcom,pmic-id` with exact-match fallback. | A/B |
| C | Is `androidboot.dtbo_idx` an input? | **Output, not input** — the `dtbo_idx`/`dtbo_idx` strings sit in the *cmdline builder* (`0x42108`); the value is produced by ABL's own selector (`Dtbo count … LocalBoardDtMatch …` at `0x39f9c/0x3a0ec`). | A |
| C | Does the ABL ufdt path support `target-path`? | **YES — confirmed in code** — both `target` (phandle, `%04x`) and `target-path` (string path, `%a`) fragment forms are implemented, with distinct error strings and distinct code at `0x6efb0/0x6fb24` vs `0x70468/0x7090c`. | A |
| C | Does overlay failure abort boot? | **No hard abort in the traced path** — the overlay wrapper `0x6a8d0` routes all its error cases to a common return `0x6aa4c`, and its caller saves the return in `x25` then branches on it (`cbnz x25, 0x38120`); failure flows to logging (`ApplyOverlay: … failed`) rather than a `fastboot`/`CpuDeadLoop` exit. | B/A |
| C | Does Window B's 199-B `target-path` debug-UART overlay match this ABL? | **At the fragment-mechanism level YES** (this ABL natively parses `target-path`). Whether the device bootloader *selects* that DTBO entry and *accepts* the modified image is a separate, unresolved gate (see §6). | A + C |
| D | Does ABL mutate `/memory/reg`? | **Yes** — a dedicated updater (`0x3d9d0..0x3f358`) rebuilds the node from DDR config and writes addr/size tuples, with explicit failure strings. | A |
| D | Is the candidate's 3-window `reg` preserved? | **NOT provable; treat as OVERWRITTEN/REBUILT.** The updater is an active writer, so the candidate's zero-size placeholder cannot be relied on to survive; a candidate-authored 3-tuple would be subject to the same rebuild. This keeps the RAM gate **CONDITIONAL**, not PASS. | A/C |
| E | Is `flags=3` descriptor bypass present? | The exact ABL bundles AOSP libavb including the literal `: VERIFICATION_DISABLED bit is set.` and an explicit unlocked-continue branch (`State: Unlocked, AvbSlotVerify returned %a, continue boot`, `Slot: %a, allow verification error: %a`). Device state is read via an EDK2/TZ/keymaster path (`KeyMasterSetRotAndBootState`, `TZ_HLOS_TAMPER_*` fuses). | B/A |
| E | Modified boot/DTBO accepted without new OEM signature? | **Only inside the unlocked/verification-disabled path**, and even there the top-level vbmeta/signature handling remains a separate gate; no evidence of an unconditional bypass. | B/C |

**Bottom line for the candidate:** the "no stock overlay needed for first boot" thesis is **not contradicted** by ABL control flow (stock Entry 2 fragments are all vendor/peripheral, and ABL applies overlays non-fatally), but the "RAM patch is boot-safe" claim is **still a hard gate**: ABL demonstrably rewrites `/memory` itself. Do not declare boot-safe on static evidence alone.

---

## 1. Identity and provenance (§2 of taskbook)

All four binaries were re-hashed locally in this round before any analysis. They match the identities published in Window A's ROUND155 report and delivery manifest exactly.

| Artifact | Size (B) | SHA-256 | Status |
|----------|---------:|---------|--------|
| `abl` partition image | 4,194,304 | `b39de91b88ef13db83892cd2e8dc4b914f7f9ed86954039fb1f64fbbf8460011` | MATCH |
| `xbl` partition image | 4,018,176 | `7819d2af26438a817600080dc2340006fd3b9a5b6ea7a60509f3faf2e5d201c2` | MATCH |
| `xbl_config` partition image | 4,325,376 | `5c63be1b477669a4f693dd98ad31954884a0907ebf1ae94b5c4a36ef9a34aa5c` | MATCH |
| ABL LZMA-decompressed PE32+ payload | 2,597,064 | `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404` | MATCH |

PE layout (re-confirmed): `MZ @0xb8`, `PE @0xf10`, machine `0xaa64`, imagebase `0`, `.text` RVA/raw `0x1000` size `0x108000`, `.data @0x109000`, `.reloc @0x277000`. Because imagebase = 0 and `.text` RVA = file offset, **every code address below is both VA and file offset** in the payload.

Firmware provenance (sanitized): Qualcomm SM8250 ("kona") ABL `BOOT.XF.3.2-00363-SM8250-1` class, EDK2 QcomModulePkg, AOSP libavb 1.x vendored under `.../QcomModulePkg/Library/avb/libavb/avb_slot_verify.c`. Huawei MatePad 11 DBY-W09 / HWDBY, A-only layout. Raw host paths, jenkins workspace strings and device identifiers are deliberately not reproduced beyond the function names needed for the argument.

**Method note (limitation, stated not hidden):** `llvm-objdump` cannot parse this PE and the host GNU objdump has no AArch64 backend; capstone is unavailable offline. Control flow was reconstructed with a purpose-built AArch64 decoder (`_r156/arm64.py`, `flow156.py`, `func156.py`) covering ADRP/ADR, ADD/SUB imm, B/BL/B.cond, CBZ/CBNZ, TBZ/TBNZ, RET/BR/BLR, LDR literal, STP/LDP, CMP/TST/MOVZ/MOVK, and ADRP+ADD string resolution. Instructions outside that set print as raw words. Therefore: **branch topology and string/data xrefs are Grade A; individual unresolved raw words are not claimed.** Function boundaries are derived from the set of BL targets (each BL destination is a function entry) cross-checked with `stp x29,x30,[sp,#-N]!` prologues and `ret`.

---

## 2. B — boot-v2 SoC DTB selection

### 2.1 Reference sites and containing functions

| Site | Meaning | Containing function | Callers |
|------|---------|--------------------|---------|
| `0x3a18c` | `qcom,board-id` xref (target `0xcffe3`) | `0x39dc8..0x3b368` (0x15a0 B) | 1 (`bl 0x37e48`) |
| `0x3a1d4` | `qcom,pmic-id` xref | same | — |
| `0x3a25c` | `qcom,msm-id` xref | same | — |
| `0x36cb4`/`0x395e4` | `DTB Size : 0x%x` | `0x36xxx..0x395xx` (boot-v2 image/DTB loader) | — |
| `0x37e84`,`0x37f48` | `Not the single appended DTB` | same | — |
| `0x37fb4` | `Single appended DTB found` | same | — |
| `0x38234`/`0x38288` | `DTB offset goes beyond kernel size` | same | — |
| `0x42ac0`/`0x42b78` | `androidboot.dtbo_idx=` / `androidboot.dtb_idx=` Write-String call sites | cmdline builder `0x42108..0x43bd4` | 1 |

### 2.2 Reconstructed branch logic (Grade A topology)

**Entry walk (multi-FDT).** In the board-match function the compare results feed a loop back-edge:

```
0x3a184  b.eq 0x3a2dc            ; one tag mismatch -> this entry rejected
0x3a188  b85b8354                ; (raw) load next DTB tag word
0x3a18c  adrp x1,0xcf000         ; "qcom,board-id" log on reject path
0x3a194  add  x1,x1,#0xfe3
0x3a19c  bl   0x60d0c             ; AsciiPrint -> "board-id ... not match"
...
0x3a338  cbnz w19, 0x39e8c        ; <-- LOOP: more DTB entries -> re-enter walk
```

This is direct evidence that ABL **iterates the concatenated DTB entries** rather than assuming one. Combined with the two complementary log branches — "Single appended DTB found" (`0x37fb4`) and "Not the single appended DTB" (`0x37e84/0x37f48`) plus `DTB offset goes beyond kernel size` (`0x38234`) — ABL's boot-v2 parser (a) reads `dtb_size`, (b) decides single vs multiple appended, and (c) bounds-checks the offset against kernel size before walking.

**Match order (Grade A compares, Grade B tag naming).** The compare chain inside `0x39dc8..0x3b368` and its callee `0x3ba60..0x3c9e4` proceeds:

1. `qcom,msm-id` — xref `0x3a25c`; failure strings `qcom,msm-id entry not found` (`0xd007e`), `qcom, msm-id does not match` (`0xd0492`, xref `0x3c134/0x3c1b0/0x3c22c`), `Boardsocid = %x, Dtsocid = %x` (`0xd0473`). `b.eq`/`b.ne` pairs decide keep/delete.
2. `qcom,board-id` — xref `0x3a18c`; `BoardVariant = %x, DtVariant = %x` (`0xd0529`, xref `0x3c2bc/0x3c33c`), with **separate major/minor gates** (`qcom,board-id major version does not match` `0xd056a`, `minor version …` `0xd0596`, xrefs `0x3c840`).
3. `qcom,pmic-id` — xref `0x3a1d4`; `MatchVal : 0x%llx BestPmicInfo.DtMatchVal :0x%llx` (`0xd0423`, xref `0x38010`) shows a **best-match accumulator**, not just first-hit.

Deletions are real operations: the image contains `Delete don't fit DTB entry %u/…` (`0xcff2c`) and `Best match DTB tags %u/…` (`0xcfaee`). Terminal failure is `ERROR: Couldn't find the suitable DTB!` (`0xd06f5`, xref `0x3da40/0x3da98`).

### 2.3 Stock three-FDT image vs a single candidate FDT

- The stock boot image carries **three FDTs** plus a tail (established in ROUND139/155: msm-id `0x20001`/`0x20000`/`0x10000`). ABL's walk loop at `0x3a338` and its "Best match" logic are exactly what consumes such a set and selects one (the kona v2.1 tree on this device).
- A **single FDT is accepted by the same code**: the "Single appended DTB found" branch (`0x37fb4`) is a normal path, and the match loop simply has one entry to iterate. There is no string or branch implying "≥2 FDTs required".
- **Required root properties** for a candidate FDT under this selector: `qcom,msm-id` (mandatory — `qcom,msm-id entry not found` is fatal for that entry), plus `qcom,board-id` and/or `qcom,pmic-id` for variant disambiguation; exact board match logs `Device tree exact match the board: <0x%x 0x%x …>` (`0xd0185`, xref `0x3ad40/0x3ae3c/0x3ae6c/0x3aeb0`).
- **Fallback behavior**: on no match ABL emits `ERROR: Couldn't find the suitable DTB!` and does not boot the candidate — it is not a silent "use whatever is there".

**Grade:** B selection logic is strongly supported at code level (A compares/branches); the *exact runtime tag values* that selected board-id `0x200e` / entry 2 remain **UNRESOLVED** (no ABL log captured — inherited from R155, still true).

---

## 3. C — DTBO selection and overlay apply/skip

### 3.1 What selects Entry 2

- `Dtbo count = %u LocalBoardDtMatch = %x` (`0xcfe82`, xrefs `0x39f9c`, `0x3a0ec`) is emitted from the **board-match function**, i.e. DTBO count and the local-board match value are produced by the same selector that chose the SoC DTB. Entry selection is therefore a **consequence of the board/msm match**, not a separate kernel-side decision.
- `androidboot.dtbo_idx=` / `androidboot.dtb_idx=` (`0xd245b`/`0xd2472`) appear only as **cmdline writes** in the builder `0x42108..0x43bd4` (`0x429cc`, `0x42ac0`, `0x42b78` are `WriteString`/`StrAppend` call sites). No code path reads these properties back as a selector input was found.

**Answer (Grade A):** `androidboot.dtbo_idx` is an **output** of ABL's selection, not an input. The exact runtime value that chose index 2 is **UNRESOLVED** (same log gap as §2).

### 3.2 Header validation and table walk

The DTBO loader has a full validation suite (all Grade B implementation strings, located in the `0x37c00..0x3d3xx` region):

`Dtbo hdr magic mismatch %x, with %x` (`0xd39fb`), `Dtbo Table TotalSize/HeaderSize/DtEntrySize/DtEntryOffset got corrupted` (`0xd3a20/0xd3a44/0xd3a69/0xd3a8f`), `DTB header is corrupted, DtEntryCount …` (`0xd3ab7/0xd3b01`), `BootLinux: failed to get dtbo image` (`0xd39c0`), `DT Total number of entries: %d, DTB version: %d` (`0xcfec8`). **Conclusion:** DTBO is not applied blindly — its container header is validated before any entry is used.

### 3.3 Does ABL always apply an overlay? Skip branch?

- A DTBO partition is **not unconditionally applied**. The path from `0x37c30..0x37e60` contains multiple *skip* decisions before `bl 0x6a8d0` (the apply wrapper): `cbz x0, 0x37e5c`, `cbz x27, 0x37fc0` (hyp overlay skip — `HypInfo: Not overlaying hyp dtboDtbo :%d is null or Bad DT header`), and `Override DTB` gates (`Dtbo Img buffer is NULL` `0xcfe02`, `Override DTB: GetBlkIOHandles failed loading user_dtbo!` `0xcfcba`).
- The apply call itself: `0x37dd8 bl 0x69e18` (find overlay), `0x37ddc cbz x0,0x380e0` (skip if none), `0x37df8 bl 0x6a8d0` (ApplyOverlay), `0x37dfc mov x25,x0`, `0x37e0c cbnz x25,0x38120`.

**Answer (Grade B):** An overlay is applied only when a validated overlay blob is present and the specific skip gates (no blob, hyp-not-overlay, override-DTB failures) do not fire. A **no-overlay / skip path exists** and is the ordinary case when no DTBO blob is loaded.

### 3.4 ufdt internals: `target` vs `target-path` (decisive for Window B)

The extracted ABL literals around `0xe0e22..0xe1080`:

```
failed to apply fragments
/__local_fixups__   /__symbols__   /__fixups__
…
target
failed to find target %04x
target-path
failed to find target-path %a
__overlay__
missing __overlay__ sub-node
failed to overlay node %a to target %a
```

Both forms are real, with distinct code:

| Fragment form | Error literal xref | Handling region |
|---------------|-------------------|-----------------|
| `target` = `<phandle>` | `failed to find target %04x` → `0x6efb0`, `0x6fb24` | phandle fixup path |
| `target-path` = "<path>" | `failed to find target-path %a` → `0x70468`, `0x7090c` | string-path lookup (`bl 0x70790` at `0x704f4`) |

At `0x70468` the code prints the `target`/`%04x` diagnostic and branches; at `0x70484..0x704f4` it takes the target-path route and calls `0x70790` (path resolution); `0x7090c` is the "could not place node" error. `ufdt_install_blob (0x%08jx)` (`0xe0bf9`) is xref'd at `0x6aa3c/0x6aad0/0x6aaf8/0x6ab7c` — the install step that runs **before** fixups/fragments.

**Answer (Grade A):** This ABL's ufdt implementation **natively supports `target-path` fragments**. This directly validates the *mechanism* used by Window B's 199-byte target-path debug-UART overlay (which needs no `__symbols__`/`__fixups__`). It does **not** by itself prove the device bootloader will select that entry or accept a rebuilt image (§6).

### 3.5 Overlay failure behavior

`ApplyOverlay` wrapper `0x6a8d0..0x6aa80`:
- validates inputs (`cbz x0,0x6aa20`, size/header checks at `0x6a8f8/0x6a930`);
- runs fixups and fragment application through `bl 0x6f548/0x6f320/0x6f748` chains;
- **every error path converges on `0x6aa4c`** (e.g. `0x6aa20` invalid-arg, `0x6aa80` bad header, `0x6aab4`, `0x6aadc`, `0x6ab04` size, `0x6ab2c` alloc), which simply returns through the common epilogue `0x6aa64..0x6aa7c` (`ret`). No `CpuDeadLoop`, no fastboot jump inside the wrapper.

Caller side: `0x37dfc mov x25,x0` then `0x37e0c cbnz x25,0x38120`. The failure fall-through emits `ApplyOverlay: ufdt apply overlay failed` (`0xcf65f`) / `ApplyOverlay: Install blob failed` (`0xcf63c`) and rejoins normal flow at `0x38320`.

**Answer (Grade A/B):** Overlay failure in this traced path is **non-fatal to the boot flow** — it logs and continues rather than aborting. (Grade A for the branch/return topology; Grade B for attributing the printed literals to exact errors, since the print sites are shared.)

---

## 4. D — `/memory` updater semantics (HARD GATE)

### 4.1 The updater exists and is active

A single large function `0x3d9d0..0x3f358` (one caller) is the `/memory` updater. Its string table is unambiguous (all Grade A xrefs):

| Literal | VA | xref sites |
|---------|----|-----------|
| `/memory` | `0xd083d` | `0x3e650`, `0x3e688`, `0x3e720`, plus `0x3e29c/0x3e2b4/0x3e2d8/0x3e318/0x3e5ec` |
| `ERROR: Could not find memory node ...` | `0xd0845` | `0x3e650` |
| `ERROR: Cannot update memory node` | `0xd086c` | `0x3e688` |
| `Failed to add the memory information addr: %d` | `0xd0736` | `0x3da98/0x3db5c/0x3db98/0x3dbb0/0x3dcd8` |
| `Failed to add the memory information size: %d` | `0xd0765` | same cluster |
| `Error unsupported cell size value: #address-cell %d#size-cell` | `0xd107b` | cell-width gate |
| `ddr_device_type` | `0xd08c4` | `0x3e798/0x3e7b4/0x3e834/0x3e8b0` |
| `ddr_device_rank_ch%d` / `ddr_device_hbb_ch%d_rank%d` | `0xd099e`/`0xd0a39` | rank/HBB writes |
| `HwDdrSize = %dGB, qcom,is-low-ram = %d` | `0xcfc6a` | `0x3b850/0x3b940/0x3b988/0x3b9b0/0x3c918` |
| `BaseAddr[%d] = 0x%lx, TestSize = 0x%x` | `0xe1203` | `0x70bf8/0x70ecc/0x70fac` |
| memory node found / invalid config | `0xd0f7d` / `0xd0f29` | inside board-match function (`0x3a0b0`/`0x3a044`) |

The updater calls the low-level FDT primitives heavily: `0x5b458` (18×), `0x5afb8` (9×), `0x5afe8` (4×), plus a tuple-write loop around `0x3f9a4..0x3fafc` that logs `memory node updating:` (`0xd136c`) and `does not match Idx(%u)` (`0xd067a`). `fdt_del_node status disabled err %d` also exists in the image (a separate status-based cleanup path).

### 4.2 Answers to D1–D7

**D1 — Does ABL delete `/memory/reg` before updating?** Not observed as an explicit delete of the whole node. The code *finds* the node (`0x3e630 bl 0x5afb8` → `ERROR: Could not find memory node`), checks cell widths, then **writes addr/size tuples** into it (`Failed to add the memory information addr/size`). The presence of `ERROR: Cannot update memory node` on write failure shows an in-place property update, not node deletion. **Grade B** (topology A, libfdt call identity B).

**D2 — Append, replace, or skip when reg non-zero?** The updater is an **active writer** driven by DDR configuration; it is not conditional on the incoming `reg` being zero — there is no "skip if already populated" branch in the traced path. It rebuilds tuples from `BaseAddr[]/TestSize` (XBL handoff) and `#address-cells/#size-cells`. This is best characterized as **rebuild/overwrite of the tuple array**, not "append to whatever the DTB brought". **Grade B** — the write loop and cell-width gate are A; the exact libfdt `setprop` vs `appendprop` selection is not fully decoded (one of the few raw-word gaps).

**D3 — Would a candidate-authored three-window `reg` be preserved, duplicated, or overwritten?** **Not preserved.** The candidate's `/memory@80000000` is the `sm8250.dtsi:683-687` placeholder with `reg = <0 0x80000000 0 0>` (size 0, from R152/R153). ABL's updater does not trust that value; it regenerates from DDR config. Therefore **the candidate's three tuples are rewritten by ABL on a real boot** — the correct mental model is "candidate supplies the node/properties; ABL supplies the runtime tuple values". A candidate that pre-fills three windows would have them replaced, not duplicated (no append-only evidence) — but this must be verified on device, not assumed. **Gate stays CONDITIONAL.**

**D4 — Effect of XBL's 6 MiB unusable-DDR-at-start.** XBL config (verbatim, Grade A):
```
UnusableDDRMemoryAtBeginning = 1
UnusableDDRMemoryStartAddr   = 0x80000000
UnusableDDRMemorySizeAtBeginning = 0x600000
```
This marks `0x80000000..0x80600000` (6 MiB) unusable at the source. In the live FDT (ROUND151, Grade C report-derived) the first window is rooted at `0x80000000`, and the same 6 MiB is carved as `hyp_region@80000000` size `0x600000` under `/reserved-memory` — i.e. **the unusable prefix is excluded via a reservation, not by shifting the `reg` base**. ABL's updater must therefore produce a window that starts at `0x80000000` while the 6 MiB is reserved; this is consistent with the candidate keeping its window-1 base at `0x80000000`. **Grade B/C** (XBL string A; live mapping from R151 report, not re-read this round).

**D5 — Are `ddr_device_type/rank/HBB` independent of `reg` mutation?** Yes — they are **separate writes to the same node**, each with its own success/error pair (`ddr_device_type is added to memory node` `0xd090d`, `ddr_device_rank_ch%d added …` `0xd09ef`, `ddr_device_hbb_ch%d_rank%d added …` `0xd0a96`), gated by DDR revision (`ddr_device_rank, HBB not supported in Revision=0x%x` `0xd0936`). They do not alter tuple cells. **Grade A/B.**

**D6 — Does ABL modify `/reserved-memory`?** No direct write to `/reserved-memory` was found in the updater's xref set. The `reserved-memory/demura_region_1` string (`0x3fc40` cluster) belongs to a display/DTU path, not the `/memory` updater. ABL's node deletion machinery (`fdt_del_node`) is used for `status = "disabled"` cleanup. **Conclusion:** no evidence ABL rewrites reserved-memory regions; the 18 carve-outs are authored by the DTB. **Grade C** (absence of evidence — stated as such).

**D7 — Reconstructed result vs ROUND151 live windows and candidate tuples.** The updater regenerates windows from platform DDR config; ROUND151 recorded three live windows totalling **12,185 MiB** (921 + 3,072 + 8,192 MiB = `0x39900000 + 0xc0000000 + 0x200000000` bytes) with `ac=2/sc=2` → 12-cell `reg`. The candidate's three tuples were constructed to those same endpoints (R152/R153). Under the "ABL rebuilds tuples" model the *values* are supplied at runtime, so agreement of candidate tuples with live windows is necessary but **not sufficient** — the candidate's actual contribution is the memory node skeleton + reserved-memory carve-outs, not the tuple numbers. **Grade C.**

### 4.3 Gate verdict

> **The RAM patch remains CONDITIONAL / NOT BOOT-SAFE-PROVEN.** ABL is a demonstrated, active writer of `/memory/reg`. No static analysis can prove the candidate's tuple values survive a real boot; only a device-side readback of `/proc/iomem` and the live FDT after the candidate image boots can close this gate. This round does **not** remove the gate.

---

## 5. E — AVB and unlocked/orange state

### 5.1 State/unlock check and its inputs

The state source is a **TZ/keymaster-backed** path, not a plain DTB property. Literals in the extracted ABL:

- `KeyMasterSetRotAndBootState` (`0xbe980` xref cluster), `SetFuse (TZ_HLOS_TAMPER_NOTIFY_FUSE) fails!`, `SetFuse (TZ_HLOS_IMG_TAMPER_FUSE) fails!` — root-of-trust and tamper fuses are set via secure calls.
- `assert fail: ops->read_is_device_unlocked != NULL` (`0xbed99`), `assert fail: ops->validate_vbmeta_public_key != NULL` (`0xbef64`) — the vendored libavb ops table requires an unlock-state callback and a public-key validator. **The unlock state is supplied by ABL's avbOps to libavb**, ultimately rooted in the device/TZ state.
- `Slot: %a, allow verification error: %a`, `State: Unlocked, AvbSlotVerify returned %a, continue boot` (`0xbe118`), `ERROR: Device State %a,AvbSlotVerify returned %a` (`0xbe153`).

**Answer (E1, Grade B/A):** The device-state/unlock check **is visible**; it enters through the EDK2/TZ keymaster path and libavb's `read_is_device_unlocked` op. No key material is extracted or reported.

### 5.2 Is AVB invoked, and do flags bypass descriptor checks?

- The image contains the full AOSP `avb_slot_verify.c` implementation (`avb_sha256_final` xref `0x51e4`; `avb_slot_verify.c` path string `0xbed2f/0xbed65`). The exact literal `: VERIFICATION_DISABLED bit is set.` (`0xbf6f9`) is present — this is the standard libavb message emitted when `AVB_VBMETA_HEADER_FLAG_VERIFICATION_DISABLED` (bit 1) is set.
- Given ROUND155's observation that root vbmeta carries `flags = 3` (bits 0 and 1 set: `HASHTREE_DISABLED | VERIFICATION_DISABLED`), standard libavb semantics would **not process the descriptors**. **However**, the taskbook explicitly warns not to transfer AOSP behavior to Huawei ABL unchecked. What can be said from *this* binary: (a) libavb with the standard flag check is bundled and called, and (b) ABL wraps the result in its **own** unlock policy — the unlocked-continue branch above can continue boot on a non-OK `AvbSlotVerify` result. There are also OEM additions (`androidboot.huawei_vbmeta.digest`, `AvbUpdateTaslot`, `ta_parts is not in vbmeta`, `SetVerifiedBootHash`).

**Answer (E2/E3, Grade B/C):** `flags=3` is consistent with descriptor-check bypass via standard libavb, and this ABL additionally has an explicit unlocked/verification-error-continue policy. But the presence of Huawei-specific checks means the bypass is **not proven unconditional** — OEM gates may still apply. Marked **B** for "libavb verifies and checks the flag", **C** for "no additional OEM check rejects the modified image".

### 5.3 Orange state

The cmdline value table is contiguous: `androidboot.verifiedbootstate=` (`0xbdfde`) followed by `green` (`0xbdffe`), `orange` (`0xbe004`), `yellow` (`0xbe00b`), inside `AppendVBCommonCmdLine` (`0xbdfca`). The `LoadImageAndAuthVB2` block selects among these based on the unlock/verify result. **Answer (E4, Grade B):** `androidboot.verifiedbootstate=orange` is emitted by a state-driven branch in `AppendVBCommonCmdLine`; it is consistent with an **unlocked** device state, matching the live bootargs reported in ROUND155. The exact boolean that selects `orange` vs `yellow` is not fully decoded (one raw-word gap) — stated.

### 5.4 Is the top-level vbmeta signature still verified?

libavb's `validate_vbmeta_public_key` op is mandatory (assert above), and ROUND155 recorded root vbmeta as `SHA256_RSA2048`, release `avbtool 1.1.0`, with chain descriptors for boot/ramdisk/dtbo. **Answer (E5, Grade B):** the top-level vbmeta key validation path exists in the called libavb. Under `flags=3`/verification-disabled, whether that call is short-circuited is **not resolved from static code** — report as UNRESOLVED rather than assert either way.

### 5.5 Live boot without AVB footer, and acceptance condition

ROUND155 established: the live `boot` is boot-v2 with **no AVB footer detected**, differs from the package `boot` in kernel/footer, while its three FDTs are byte-identical; the chain descriptors name `boot`/`ramdisk`/`dtbo`. These coexist because verification-disabled/unlocked boot does not require the hash descriptor's footer to match at boot time. **Answer (E6, Grade C):** the coexistence is consistent with the unlocked/bypass path, not proof of it.

**Answer (E7, Grade B/C):** A modified boot/DTBO would be accepted **only within the unlocked / verification-disabled policy path**, and only if no OEM-specific gate (Huawei vbmeta digest, TA digest, rollback via TZ) rejects it. There is **no** evidence of an unconditional "any image accepted" bypass. No signing, flag edit, or bypass was attempted.

---

## 6. Unresolved items and cross-round corrections

**Unresolved (explicitly not guessed):**
1. Exact runtime tag values and the value that selected board-id `0x200e` / DTBO entry 2 — needs an ABL boot log or trace (inherited from R155; unchanged).
2. Exact `fdt_setprop` vs `fdt_appendprop` primitive in the `/memory` write loop (one raw-word gap in the hand decoder) — does not change the "ABL rebuilds tuples" conclusion.
3. Whether `flags=3` short-circuits the top-level vbmeta signature check in *this* Huawei build vs only the descriptor walk.
4. Whether the device bootloader selects and applies a candidate-authored DTBO entry index (index-2 contract) — offline apply ≠ bootloader acceptance.
5. Exact boolean selecting `orange` vs `yellow` in `AppendVBCommonCmdLine`.

**Corrections / discipline:**
- No prior round's numeric result is contradicted by this round's code evidence. The R155 statement that ABL "contains an explicit `/memory` updater" is **upgraded** from string-xref (C) to control-flow-confirmed (A/B).
- This report deliberately does **not** claim the candidate is boot-safe: the RAM gate (§4.3) and AVB selection gate (§6.4) are both still open.

---

## 7. Scope compliance

- Only Window A's own ROUND155 binaries/evidence were used; hash-checked at start.
- No Window B workspace, no device, no new capture, no source tree/build, no partition write, no signing/key work.
- Raw binaries, decompressed PE payload, full private logs and host paths remain local; only this sanitized report is published.

— END —
