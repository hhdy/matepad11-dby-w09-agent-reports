# ROUND158 — WorkBuddy Window A: Exact HOS4.3 ABL rootparam / DTBO / fastboot-boot Audit

- Executor: **WorkBuddy Window A (1号 Agent)**. Not Window B, not 2号 AI.
- Scope: **offline reverse engineering + read-only analysis only**. No ADB, no device command, no root, no fastboot session, no partition read/write, no reboot, no flash, no temporary boot, no boot.img/DTBO/vbmeta generation, no key/signing/AVB edit, no source edit, no access to Window B workspace.
- Target: DBY-W09, HOS 4.3.0.196 (C00E100), ABL payload SHA-256 `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`.
- Inputs used: Window A's own ROUND155 captured boot-chain/ABL files and Window A's own ROUND157 source tree only.

## 0. Verdict summary

| Question | Grade | Conclusion |
|---|---|---|
| A. Does this exact HOS4.3 ABL *itself* require `/rootparam` as a hard gate? | **A/B** | **NOT REQUIRED by ABL code.** The ABL contains **zero** byte-level occurrences of `rootparam`, `/rootparam`, `qcom,boardid`, `qcom,board_name`, `qcom,product_name`, `hardware_version`, `huawei,modem_id` (all case variants + UTF-16 + partial tokens checked). There is no ADRP/ADR/ADRP+ADD path that could reference such a node name; the ABL never looks up `/rootparam` by string. |
| A2. Is `/rootparam` nevertheless *functionally required* for a boot to look like stock? | **A** | **Yes, but the writer is the DTBO overlay, not the ABL.** The live stock FDT has `/rootparam` fully populated. The values come from stock DTBO Entry 2 `fragment@143/__overlay__`, whose target is bound via `__fixups__` external symbol `rootparam` to the base FDT's `/rootparam` node (phandle `0x3e`). This is the real mechanism behind the public port's "rootparam overlay" claim. |
| B. Which DTBO entry can be selected, and can stock Entry 2 be applied to the candidate? | **A** | Selection is a vendor `qcom,board-id` / `qcom,msm-id` / subtype / DDR-size match against local board values (e.g. `0x200e` for live Entry 2). **Stock Entry 2 cannot be safely applied to the minimal candidate**: R154 measured 0/166 external symbols bound; the candidate DTB has no `__symbols__`/`__fixups__`/`__local_fixups__`, so `fragment@143`'s external `rootparam` fixup cannot bind. A rootparam overlay is structurally valid only if the candidate base first carries the fixup symbol (label in a `-@` build). |
| C. Is `fastboot boot` supported by this exact ABL? | **B/C** | **Static command path exists; runtime policy is locked-device gated.** The ABL contains a dedicated `CmdBoot` error chain (`Fastboot boot command is not available in locked device`, `Invalid Boot image Header`, `CmdBoot: ClearUnbootable failed`) and a standalone `boot` token. A full command-dispatch table decode was **not** achieved, so **unlocked-device `fastboot boot` remains INDETERMINATE**. No command was sent to any device. |

**Bottom line for the port:** the "rootparam hard gate" reported for the public same-model Linux 7.0 port is **not an ABL string-level requirement in this exact HOS4.3.0.196 ABL**. It is a **DTBO overlay fixup requirement**: the selected stock DTBO Entry 2 supplies `/rootparam` content through `fragment@143` target-bound by the external `rootparam` symbol. Any candidate that wants the same board identity must provide a bindable `/rootparam` node and the matching fixup label; copying the public `qcom,board-id=0x206a` is wrong for this device (live selection is Entry 2 / `0x200e`).

## 1. Artifact identity recheck (all computed this round, read-only)

| Artifact | Bytes | SHA-256 | Note |
|---|---:|---|---|
| `abl-decompressed.bin` (decompressed ABL payload) | 2,597,064 | `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404` | **matches TARGET from taskbook** |
| `abl-pe.exe` (PE view) | 2,596,680 | `6fbef511ab40c6242dd71f749669e19caf6474523d35026a2111dcf4c6c9eb2d` | PE32+ AArch64 |
| `abl.img` (captured partition) | 4,194,304 | `b39de91b88ef13db83892cd2e8dc4b914f7f9ed86954039fb1f64fbbf8460011` | ROUND155 primary |
| `boot.img` (captured partition) | 100,663,296 | `7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8` | ROUND155 primary |
| `dtbo.img` (captured partition) | 25,165,824 | `51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c` | ROUND155 primary |
| candidate `huawei-dby-w09.dtb` | 108,680 | `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` | same object as R154/R156/R157 |

ABL PE layout (from `pe_probe.py`, re-run): `machine=0xaa64`, PE32+ (`opt magic 0x20b`), `imagebase=0x0`, `entryRVA=0x1000`, `.text RVA=RAW=0x1000 size=0x108000`, `.data RVA=RAW=0x109000 size=0x16e000`, `.reloc RVA=RAW=0x277000`.
**Because imagebase=0 and section RAW==RVA, file offset == VA throughout.** All addresses below are both file offsets and VAs.

Disassembly method: `capstone 5.0` ARM64 little-endian, with ADRP/ADD pairs scanned word-by-word over `.text` (R155-verified pattern) to avoid linear-disasm desync at literal pools. Calibration: `qcom,board-id @ 0xcffd3` → ADRP@`0x3a18c` page `0xcf000` + ADD@`0x3a194 #0xfe3` → `0xcffe3`, reproducing R155's independent result. Grade A applies only to decoded control flow; grade B to string/ADRP evidence; grade C to inference.

## 2. Priority A — Is `/rootparam` a hard condition in this exact ABL?

### 2.1 Exhaustive string search (grade B, decisive for "ABL does not name it")

Search over the full 2,597,064-byte payload, ASCII + case-insensitive + UTF-16LE + partial tokens:

| Needle | Count | Result |
|---|---:|---|
| `rootparam`, `ROOTPARAM`, `RootParam`, `/root`, `rootpar` | 0 | absent |
| `qcom,boardid` | 0 | absent |
| `qcom,board_name`, `qcom,product_name`, `hardware_version`, `huawei,modem_id`, `modem_id`, `board_name`, `product_name` | 0 | absent (all) |
| UTF-16LE `rootparam`, `hardware_version`, `modem_id`, `product_name`, `board_name` | 0 | absent (all) |
| `qcom,board-id` | 7 | present — `0xcffd3`, `0xcfff6`, `0xd0035`, `0xd054c`, `0xd056a`, `0xd0596`, `0xd0618` (all generic Qualcomm board-match messages, see §3) |
| `qcom,` / `huawei,` | 102 / 1 | generic DT property fragments; none rootparam-identity |

**No ADRP/ADD reference can exist to a string that is not in the image.** Cross-referencing all ADRP pages found no candidate path for a `/rootparam` lookup. Therefore: **the ABL itself does not look up, validate, or copy `/rootparam` by name, and cannot treat a missing rootparam as a fatal ABL-level gate**.

### 2.2 What the stock firmware actually contains (grade A — captured objects, not public inference)

Two independent captures were read:

1. **Base FDTs inside the ROUND155 `boot.img`** (header v2, `header_size=1660`, `dtb_size=1,664,243`, `dtb_addr=0x1f00000`, `page=4096`; DTB region at `0x15ba000`). Three concatenated FDTs:
   - `fdt0` off `0x15ba000`, 556,524 B, sha256 `df2730f3d2e9bdab…`, board-id `<0 0>`, **`/rootparam` present**, only property `phandle = <0x3e>`.
   - `fdt1` off `0x1641dec`, 556,520 B, sha `f3dcba83e73f4d86…`, same shape, `/rootparam` with `phandle <0x3e>`.
   - `fdt2` off `0x16c9bd4`, 551,026 B, sha `6cda673986bf814c…`, same shape, `/rootparam` with `phandle <0x3e>`.
   - (4th blob at `0x1750446`, 173 B, is a non-rootparam fragment.)
   - So **the base FDT intentionally carries an empty `/rootparam` node with a phandle** — a fixup anchor.

2. **Live FDT (ROUND151 Window A read-only capture, same device, boot already complete)**: `/rootparam` is present and fully populated:
   ```
   qcom,boardid       = bytes 08 02 06
   qcom,board_name    = "DBY_W09_VD"
   qcom,product_name  = "DBY-W09"
   hardware_version   = "SH1DBSLM"
   huawei,modem_id    = (non-ASCII bytes)
   phandle            = <0x3e>
   ```
   This is the **only** place those identity strings appear in the boot chain; they are not in the ABL (§2.1) and not in the base boot.img FDTs.

3. **ROUND155 stock `dtbo.img`** (9 entries, board-ids below). Every entry's own `/rootparam` node is **absent**; no entry defines the five identity properties at its root. But the raw string `DBY_W09_VD` occurs in `dtbo.img`, and only **Entry 2** contains it. Exact host node:
   - `entry2.dtbo` sha256 `0633a6fbeebb…` (entry id=0, board-id `<0x200e 0>`), node `/fragment@143/__overlay__` carries all five properties:
     `qcom,boardid = [08 02 06]`, `qcom,board_name="DBY_W09_VD"`, `qcom,product_name="DBY-W09"`, `hardware_version="SH1DBSLM"`, `huawei,modem_id=<bytes>`.
   - `/fragment@143` has `target = <0xffffffff>` (external fixup). `dtbo.img`'s `/__fixups__` maps symbol **`rootparam`** → `/fragment@143:target:0`.
   - Base FDT's `/rootparam` has `phandle=<0x3e>` — exactly the symbol/fixup anchor the external reference resolves against.

**Conclusion (grade A):** `/rootparam` content is supplied by **DTBO Entry 2 fragment 143 via external fixup**, not by ABL code, and not by the public HOS4.2 overlay values (our `qcom,boardid` is `08 02 06`, not the public `0x206a 0`). The public port's "if the selected DTBO doesn't write rootparam, ABL returns to fastboot" is consistent with these captures **as an overlay/boot-policy observation**, but the exact HOS4.3 ABL contains no rootparam-specific code to confirm the "ABL checks it and falls back" half — that half is **INDETERMINATE from static ABL code**.

### 2.3 Candidate source/DTB state (grade A)

- Source (Window A's own R157 tree) `a157build/common/arch/arm64/boot/dts/qcom/huawei-dby-w09.dts`:
  - line 42: `qcom,board-id = <0 0>;` (candidate base deliberately zero — comment at lines 37–40 records that live selection was Entry 2 `0x200e`, mechanism then UNKNOWN).
  - lines 57–63: `rootparam: rootparam { };` — empty node **with label**, comment names `dby-w09-ack18-rootparam.dtso.draft` (draft file does not exist in the R157 tree).
- Compiled candidate DTB (`9d0d7600…`) decompiled with R157's own `dtc`:
  - `/rootparam { };` present at decompiled line 6157, empty.
  - `qcom,board-id = <0x00 0x00>;` at line 11.
  - **`/__symbols__`, `/__fixups__`, `/__local_fixups__` all absent** — the Makefile has only `dtb-$(CONFIG_ARCH_QCOM) += huawei-dby-w09.dtb` (no `DTC_FLAGS_huawei-dby-w09 := -@`).
- Consequence for §2.2 mechanism: because the candidate has no `/__symbols__`, an external fixup symbol named `rootparam` cannot be resolved against it. A `target-path = "/rootparam"` overlay does **not** need `__fixups__`, but a stock-style external `rootparam` fixup **does**. This is the structural reason R154 measured 0/166 external symbols binding.

### 2.4 Priority A final answer

- **ABL-level mandatory `/rootparam` check: NOT REQUIRED** (grade A/B: zero ABL string/xref evidence, base FDT carries only a phandle anchor, ABL has no rootparam-specific code path).
- **Functional equivalence to stock: `/rootparam` content must still be supplied**, and for a stock-style external-fixup overlay the candidate must be rebuilt with `-@` so its `rootparam` label is exported. This is a **DTBO construction requirement**, not an ABL rootparam gate.

## 3. Priority B — Entry2 (`0x200e`) vs Entry8 (`0x206a`) selection contract

### 3.1 Captured DTBO board-id table (grade A, from ROUND155 dtbo.img)

| Entry | root `qcom,board-id` | dtbo sha256 prefix | symbols / fixups | has `DBY_W09_VD` |
|---:|---|---|---|:---:|
| 0 | `0x2008 0` | `6940ce1167a3` | 355 / 165 | no |
| 1 | `0x2068 0` | `685a837e65a6` | 354 / 166 | no |
| **2** | **`0x200e 0`** | `0633a6fbeebb` | 354 / 166 | **yes** |
| 3 | `0x2010 0` | `e68e5a48f64c` | 354 / 165 | no |
| 4 | `0x200a 0` | `866991056bef` | 355 / 165 | no |
| 5 | `0x202e 0` | `699df8950612` | 354 / 166 | no |
| 6 | `0x206e 0` | `fca5a7a83ea6` | 354 / 166 | no |
| 7 | `0x2030 0` | `0a57a7f8ac67` | 354 / 166 | no |
| 8 | `0x206a 0` | `a7946352a86a` | 354 / 166 | no |

Live boot selected `androidboot.dtbo_idx=2` → Entry 2 (`0x200e`). The public port's `0x206a` is Entry 8 and **was not selected on this device**. Do not copy it.

### 3.2 ABL matching path (grade A for decoded flow; raw strings cited where not fully decoded)

Generic DTBO entry matching is in the ABL around `0x37f80–0x3831c` and `0x3c300–0x3c448`. Decoded evidence:

- `0x3a18c`: `adrp x1, #0xcf000`; `0x3a194`: `add x1, x1, #0xfe3` → `0xcffe3`, referencing the `qcom,board-id` string block at `0xcffd3` (used as a property-name argument to `bl 0x60d0c`, the debug-print routine; note `0x611b0`/`0x611d8` immediately before are log-level gates, not board decisions).
- Error strings the match path can emit (all at `0xd04xx–0xd06xx`):
  `qcom,msm-id does not match` (`0xd0492`), `soc version does not match` (`0xd04ce`), `soc foundry does not match` (`0xd050d`), `qcom,board-id does not match` (`0xd054c`), `qcom,board-id major version does not match` (`0xd056a`), `qcom,board-id minor version does not match` (`0xd0596`), `subtype-id doesnot match` (`0xd05e5`), `ddr size does not match` (`0xd05ff`), `qcom,board-id does not exist (or) (%d) is not a multiple of (%d)` (`0xd0618`).
- `0x38054`: ADRP page `0xd0000` + `0x38058 add x1,x1,#0x54b` → `0xd054b` (`qcom,board-id does not match`), inside a function that loads local board constants (`mov x26,#0xe; movk x26,#0x8000,lsl#48` at `0x3802c–0x38030`, i.e. `0x80000000000e`-class board tokens) and calls `bl 0x3d3b8` / `bl 0x6127c`.
- `0x3c300–0x3c378`: `ldur x8,[x19,#-0x20]; orr x8,x8,#0x2000000000000` sets a match-status bit; `bl 0x36b68` then `eor w8,w0,w21; tst w8,#0x700` compares local board value (bits 8–10) against a candidate value; on mismatch it prints via the `0x3c33c → 0xd054b` path. `sub_0x36b68` (`0x36b68`, 4 instructions) returns `ldr w0,[x8,#0x34]` with `x8 = 0x264400` → local board word at `0x264434`.
- `0x3c360–0x3c3a8`: `bl 0x5f010` is called with two different property-name pointers (`0x3c364 adrp x2,#0xcf000 … add #0xf0e`; `0x3c390 adrp x2,#0xd0000 … add #0x31b`) and `w1 = board value`; it returns parsed values consumed by the match loop — consistent with reading `qcom,msm-id` / `qcom,board-id` arrays from the DT entry and comparing major/minor/subtype/DDR against the local board.

**Selection inputs (grade A/B):** local board identity word from `[0x264434]` and from board constants (`0x8000…000e`), versus candidate DTBO root `qcom,board-id` / `qcom,msm-id` / subtype / DDR properties; match must hold across major/minor/subtype/DDR. With the captured runtime, the matching entry is Entry 2 (`0x200e`).

### 3.3 Can the candidate be matched, and can stock Entry 2 be reused? (grade A)

- Candidate base root is `qcom,board-id = <0 0>`; it is a **base FDT**, and in stock the base FDTs also have `<0 0>` while the selected DTBO carries the real board-id `<0x200e 0>`. So a candidate could in principle be matched by a DTBO whose root `qcom,board-id` equals the local board word — **provided** the ABL reads that property from the DTBO entry after overlay (the match code above reads DT-entry properties, not ABL-hardcoded IDs).
- **Reusing stock Entry 2 on the minimal candidate is NOT safe**:
  - R154 measured **0/166 external fixups bound** when applying stock overlays to the candidate; stock Entry 2 expects the base to export 166 symbols (including `rootparam`) via `__symbols__`.
  - The candidate DTB has no `__symbols__`/`__fixups__`/`__local_fixups__` (§2.3), so even `fragment@143`'s single external `rootparam` fixup cannot bind.
  - Grade A evidence: `dtbo_entries.py` reports Entry 2 `symbols=354 fixups=166`, candidate symbols/fixups = 0.
- A one-entry DTBO with a `target-path="/rootparam"` overlay is **structurally acceptable to a generic libfdt-style fixup path** (no external symbol needed), but this exact ABL's required DTBO header/table metadata is **not fully proven** here: this round did not decode the complete `dt_table_entry` validation used before overlay (id/rev/custom fields). Grade C for the metadata checklist; carry-forward gap.

## 4. Priority C — `fastboot boot` support

### 4.1 Static evidence (grade B)

| Evidence | VA | Note |
|---|---|---|
| `FastbootCommandSetup` | `0xcb061` | setup routine name present in image |
| `boot` (standalone NUL-terminated token) | `0xbe6c0` | adjacent to partition-name strings (`ramdisk`, `vbmeta_system`, `vbmeta_vendor`) — boot command/partition token |
| `Fastboot boot command is not available in locked device` | `0xcbbc2` | dedicated locked-device refusal message |
| `Invalid Boot image Header` | `0xcbbfa` | CmdBoot validation error |
| `CmdBoot: ClearUnbootable failed` | `0xcbc14` | CmdBoot-specific error |
| `Failed to load/authenticate …` | `0xcbc34` | CmdBoot load/auth error |
| `continue` token | `0xcad7d` | separate fastboot command |
| `download` / `flashing` / `oem` command families | many | `download:` at `0xcbfea`, `flashing unlock/lock`, `oem …` in `0xc5fxx–0xc62xx`, `CmdDownload: Send 12 %a` at `0xcc090` |

### 4.2 Decoded control flow (grade A for the error path, not for a full command table)

- ADRP+ADD references to the `0xcbbxx` CmdBoot error-string cluster are in a compact function group at `0x303f8–0x304a0`:
  - `0x30418 adrp x1,#0xcb000`, `0x30420 add x1,x1,#0xbbf` → `0xcbbbf` (2 bytes before the locked-refusal string, whose exact start is `0xcbbc2`: bytes at `0xcbbbf` are `64 0a 00` = tail of the previous string + NUL, then `Fastboot boot command...`). Strings are tightly packed; the ADRP+ADD lands on the preceding NUL boundary, a normal compiler artifact. Preceded by `bl 0x611b0` / `bl 0x327b0 → 0x611d8` log-level gates (grade A for the reference, grade B for the semantic association).
  - `0x30434 adrp x0,#0xcb000`, `0x30438 add x0,x0,#0xbd8` → `0xcbbd8` (`Invalid Boot image Header`), `0x30440 b #0x2b794` (error-return path); `0x30444 bl 0x32d44` → `0xe40c7b`, `0x3044c b #0x2b870` (success/return path).
  - `0x3046c/0x30474` → `0xcbbf8` (`CmdBoot: ClearUnbootable failed`); `0x30488/0x3048c` → `0xcbc12` (`CmdBoot: ClearUnbootable failed` cluster).
- **`0x611b0` is a debug-log gate, not the lock-state decision**: `0x611b8 bl 0x6121c`, `0x611c8 ldrb w8,[x8,#0x590]`, `0x611cc ubfx w0,w8,#1,#1` — extracts a log-level bit. `0x611d8` tests `ldr w8,[0xbd594]` against a passed mask (`tst x8,x0; cset w0,ne`) and includes a stack-canary check on `[0x10e…d00]`. I explicitly do **not** treat these as the bootloader lock check.
- `sub_0x4bac0` (called at `0x302c4`) is a 4-instruction wrapper around `0x1bd54` with only a stack-canary save — not a lock check either.

### 4.3 Grade-separated conclusion

- **Static support (grade B):** a `CmdBoot` handler and a `boot` token exist; the ABL has dedicated locked-device refusal and boot-image validation messages. The fastboot application clearly contains a `boot` code path.
- **Runtime policy (grade B for locked case):** when the device is locked, the dedicated message `Fastboot boot command is not available in locked device` exists and sits in the CmdBoot error cluster — consistent with "refused in locked state", which is also what the public port reports.
- **Unlocked device behavior (grade C): INDETERMINATE.** I did not fully decode the command registration/dispatch table (commands use a generated table indexed with `0x84`-byte stride near `0x265f7c`, and `FastbootCommandSetup` has no direct 64-bit pointer reference), and no device command was sent. I cannot assert from static code alone that `fastboot boot` would succeed even when unlocked, nor that it is unconditionally disabled.
- No fastboot session was started; no command was sent; nothing was flashed or rebooted.

## 5. Carry-forward narrow gaps

- **`/memory/reg` property builder (ROUND157 C1):** R155/xref evidence retained — `/memory` string at `0xd083d`, `Failed to add mem` at `0xd0831`, both referenced by ADRP@`0x3e650` page `0xd0000` + `add #0x855` → `0xd0855` through `bl 0x60d0c` (debug print). The `0x3e650` region uses custom `AllocatePool`/property-builder calls and was re-observed here but **whole-tree replace vs append remains unproven** (grade C). Not expanded.
- **Overlay fixup atomicity (ROUND157 C2):** `ufdt_install_blob` string at `0xe0bf9`, referenced at `0x6aaf8` (ADRP `0xe0000` + `#0xbf7`) and `0x6ab7c` (`#0xc2d`) in the `0x6aa40–0x6aba0` function; failure branches consistently jump to `0x6aa4c` (cleanup/return with `x19=xzr`). This shows a single install entry point with error exits, but **whether partial fragment mutations can persist after a failed fixup is still PARTIAL** (grade C). Not expanded.
- **DTBO header/table validation:** not decoded; see §3.3 grade-C note.

## 6. What this round did NOT establish

- Exact runtime condition that selected Entry 2 (`0x200e`) over the other eight entries (board word source `[0x264434]` decoded; the value and comparison chain are A/B-grade, but a full end-to-end selection trace to `dtbo_idx` was not completed).
- Whether ABL "returns to fastboot" on a missing/mismatched rootparam — no ABL code for rootparam exists, so this public-port claim can only be an overlay/policy observation (grade C from this ABL).
- `fastboot boot` success on an unlocked device (INDETERMINATE, §4.3).
- Any AVB/OEM acceptance detail beyond carry-forward; explicitly out of scope.

## 7. Reproduction commands (offline, read-only)

All analysis ran inside Window A's own WSL distro `Ubuntu-24.04`; inputs are Window A's ROUND155 captures and ROUND157 source tree.

```
python3 r158/strings_locate.py            # exact string offsets
python3 r158/strings_deep.py              # variants / UTF-16 / NUL tokens / contexts
python3 r158/disasm.py xref 0xcbbc2       # ADRP+ADD xref (capstone)
python3 r158/disasm.py dis 0x303c0 0x30520
python3 r158/disasm.py dis 0x3c300 0x3c3b0
python3 r158/disasm.py func 0x36b68
python3 r158/disasm.py func 0x611d8
python3 r158/dtbo_entries.py              # 9-entry dtbo identity + rootparam presence
python3 r158/rootparam_frag.py            # fragment@143 identity props
python3 r158/boot_base_fdt.py             # boot.img base FDT /rootparam check
dtc -I dtb -O dts candidate.dtb -o candidate.dts
```

No device, ADB, root, fastboot, partition read/write, flash, reboot, temporary boot, boot.img/DTBO/vbmeta generation, key/signing/AVB edit, source edit, or Window B workspace access occurred in this round.

— END —
