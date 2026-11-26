# WORKBUDDY A — ROUND159 Report: Exact HOS4.3 Entry 2 Target Facts and ABL DTBO Selector Contract

- Executor: **WorkBuddy Window A (1号 Agent)**. Offline/read-only. No device, ADB, fastboot, flash, signing, or Window B workspace access.
- Target: DBY-W09 / HOS 4.3.0.196(C00E100) / SM8250.
- Companion machine-readable artifact: `firmware-analysis/round159/entry2-target-facts.json` (same branch/path).
- Scope discipline: no raw ABL / raw dtbo.img uploaded; only extracted facts, addresses and hashes.

## 1. Accepted identities (re-verified this round)

| Artifact | Size (B) | SHA-256 | Result |
|---|---|---|---|
| Stock dtbo partition image (Window A ROUND155 capture, `copies-primary/dtbo.img`) | 25,165,824 | `51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c` | **MATCH** |
| ABL PE payload (decompressed, `evidence/abl/abl-decompressed.bin`) | 2,597,064 | `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404` | **MATCH** |
| Live runtime FDT (ROUND151 capture, `fdt_live_round151.bin`) | 800,316 | `fefeaa049f64a9cc79f0aa7558883f7a31ba98cf0ad73f541834c0ec2d46b700` | new evidence this round |

Live runtime observation carried in: `androidboot.dtbo_idx=2` → stock DTBO **Entry 2** is the active target; Entry 8 / `0x206a` is not.

Extraction commands (host, offline):

```
sha256sum dtbo.img abl-decompressed.bin fdt_live_round151.bin
python extract_entry2.py        # header/entries/Entry-2-FDT/rootparam dump
python build_facts.py           # writes entry2-target-facts.json
python flow159.py <start> <end> # ABL annotated decode (arm64.py backend)
```

## 2. Task A — exact stock DTBO table facts

### 2.1 dt_table_header (all fields, big-endian, raw values)

| Field | Value |
|---|---|
| magic | `0xd7b7ab1e` |
| total_size | **2,963,810** (≠ file size 25,165,824; file is the 24 MiB partition) |
| header_size | 32 |
| dt_entry_size | 32 |
| dt_entry_count | **9** |
| dt_entries_offset | 32 |
| page_size | 4096 |
| version | **0** |

### 2.2 All nine dt_table_entry records

Every entry carries `id = 0, rev = 0, custom[0..3] = 0`. **The table metadata therefore cannot be what discriminates the entries** — selection must run on the embedded FDT root properties. Sizes/offsets (raw, big-endian):

| Index | dt_size | dt_offset | dt_offset mod 4 | dt_offset mod 4096 |
|---|---|---|---|---|
| 0 | 329,044 | 320 | 0 | 320 |
| 1 | 329,352 | 329,364 | 0 | 1,684 |
| **2** | **329,240** | **658,716** | 0 | 3,356 |
| 3 | 329,098 | 987,956 | 0 | 820 |
| 4 | 329,340 | 1,317,054 | 2 | 2,238 |
| 5 | 329,356 | 1,646,394 | 2 | 3,898 |
| 6 | 329,356 | 1,975,750 | 2 | 1,478 |
| 7 | 329,352 | 2,305,106 | 2 | 3,154 |
| 8 | 329,352 | 2,634,458 | 2 | 730 |

Layout facts (Grade A, arithmetic on the verified image):

- Entries are packed **strictly back-to-back** from `dt_entries_offset = 32` with **zero padding**; entry i+1 `dt_offset` = entry i end exactly.
- `dt_size mod 4 = 2` for Entry 3 (329,098), so offsets of Entries 4–8 are **2 mod 4**. The stock image is **not 4-byte aligned**, and no `dt_offset` is page-aligned despite `page_size = 4096` in the header.
- All nine embedded FDTs parse with correct magic `0xd00dfeed` and internal `totalsize == dt_size`.
- Beyond `total_size` (2,963,810) the partition holds 22,202,014 bytes that are **not zero**: an `AVB0` descriptor blob at offset 2,965,504 and an `AVBf` footer in the last 64 bytes whose `original_image_size` field equals the header `total_size`. The device still selects Entry 2 (live `dtbo_idx=2`), so the in-device parser is demonstrably bounded by `header.total_size`, not by partition size or trailing zero scanning.

### 2.3 Entry 2 embedded FDT

- Extracted blob: 329,240 B, SHA-256 `0633a6fbeebbad45c0f5572faf222c779e1cd51d253a6ef8282592a730ba3c8b`, FDT version 17.
- Root properties (**only three**; selector-relevant fields exactly as present):
  - `compatible` = `["qcom,kona-qrd", "qcom,kona", "qcom,qrd"]` (string list, 33 B)
  - `model` = `"Huawei Technologies, Inc. DBY-W09"` (34 B)
  - `qcom,board-id` = `0000200e00000000` → **`<0x200e 0x0>`** (u32 cells [8206, 0])
  - `qcom,msm-id`: **absent**. `qcom,pmic-id`: **absent**. No subtype/DDR/PMIC identity fields at root.
- The five `/rootparam` payload properties live in **`/fragment@143/__overlay__`** (all 144 fragments use unresolved phandle targets `target = <0xffffffff>`; fragment@143 is the fragment that overlays `/rootparam` in the base DTB — consistent with the live FDT gaining a `/rootparam` node with `phandle 0x345`).

### 2.4 Exact five `/rootparam` encodings (stock Entry 2 wire bytes)

| Property | Encoding | Length | Raw hex | Value | Payload SHA-256 |
|---|---|---|---|---|---|
| `qcom,boardid` | u32-cell-list | 16 | `00000008000000020000000000000006` | cells [8, 2, 0, 6] | `b1d1c09e1992ee1df6eb30e4e4e00e5a5826eff648e49a7ffb8e7d74e2c6ad37` |
| `qcom,board_name` | string | 11 | `4442595f5730395f564400` | `"DBY_W09_VD"` | `57a764019b27ded9a052b2f771ebbfbc7187ed28cf6e8b8218edb241919be9f1` |
| `qcom,product_name` | string | 8 | `4442592d57303900` | `"DBY-W09"` | `7659477258493b605369344c9861c4be5ce98ae4dfd75e908f76986849991745` |
| `hardware_version` | string | 9 | `5348314442534c4d00` | `"SH1DBSLM"` | `bb002cab9e01a59ee3b8c8aac1da3f3e61285c0fd9c2f283fb1c051e94077b66` |
| `huawei,modem_id` | u32-cell-list | **8** | **`ffffffff00000000`** | cells [0xffffffff, 0] | `72a4fa3544e43a836ffcb268ce06ccdbc55d44d5e6b1b1c19216a53ea98301fd` |

The `huawei,modem_id` full raw bytes requested by the taskbook: **8 bytes `ff ff ff ff 00 00 00 00`** (two u32 cells: `0xffffffff`, `0x00000000`). No device identifier from unrelated partitions is included.

Correction to the inherited paraphrase: `qcom,boardid` exact wire is **four cells `[8, 2, 0, 6]` (16 bytes)**, not three bytes `[08 02 06]`.

### 2.5 Live verification (ROUND151 FDT, Grade A)

Live `/rootparam` (800,316-byte runtime FDT) contains exactly these five properties plus `phandle 0x345`; **all five payloads are byte-identical** to the stock Entry 2 fragment@143 values above (`live_fdt_rootparam_byte_identical: true` for each in the JSON). This confirms (a) the live device applied stock Entry 2, and (b) the overlay landed on `/rootparam` as a full-property replacement. Live root `qcom,board-id` = `<0x200e 0x0>` matches Entry 2's root.

Full board-id matrix across the nine entries (root `qcom,board-id` / fragment@143 `qcom,boardid` / `qcom,board_name`):

| Entry | root board-id | frag boardid cells | board_name |
|---|---|---|---|
| 0 | `0x2008` | — (no fragment@143) | — |
| 1 | `0x2068` | [8,2,9,6] | DBY_W09_VF |
| **2** | **`0x200e`** | **[8,2,0,6]** | **DBY_W09_VD** |
| 3 | `0x2010` | — (no fragment@143) | — |
| 4 | `0x200a` | [8,2,0,2] | DBY_W09_VB |
| 5 | `0x202e` | [8,2,3,8] | DBY_W09_VI |
| 6 | `0x206e` | [8,3,0,2] | DBY_W09_VH |
| 7 | `0x2050` | [8,2,4,0] | DBY_W09_VE |
| 8 | `0x206a` | [8,2,9,8] | DBY_W09_VG |

Entries 0 and 3 carry no rootparam overlay at all; every entry with a fragment@143 has `huawei,modem_id = ffffffff00000000` (constant across variants).

## 3. Task B — ABL DTBO parser and selector contract

Decoder limitation (stated, not hidden): same as ROUND156 — control flow reconstructed with the purpose-built AArch64 decoder; branch topology, constants and string xrefs are Grade A; raw undecoded words are not claimed.

### 3.1 DTBO header validation (decoded function containing the `0xd7b7ab1e` check)

Function region: **`0x4b300..0x4b654`** (entry into validator logic at `0x4b374`; success return `movz w0, #0x1; b 0x4b178` at `0x4b64c`). Decoded checks, in order (all addresses are instruction addresses in the decompressed PE, VA == file offset):

1. `0x4b374`: load DTBO buffer pointer; `cbz` → null-buffer error path.
2. `0x4b37c-0x4b390`: read header word 0, convert (big-endian helper `0x6127c`), **`cmp w0, w20` where `w20 = movz #0xab1e; movk #0xd7b7,lsl16 = 0xd7b7ab1e`**; `b.ne` → mismatch error path printing `Dtbo hdr magic mismatch %x, with %x` (`0xd39fb`, xref `0x4b590`).
3. `0x4b398-0x4b3a4`: `w20 = 0x01800001` (25,165,825 = 24 MiB + 1); size `b.cc` continue — image size must be below 24 MiB + 1.
4. `0x4b440-0x4b45c`: `total_size` (header +4): **must be ≤ `0x01800000`** (`b.hi` error) and **≠ 0** (`cbz` error).
5. `0x4b460-0x4b46c`: `header_size` (header +8): **`cmp w0, #0x20`** (`0x7100801f`), `b.ne` error → must be 32.
6. `0x4b470-0x4b47c`: `dt_entry_size` (header +0xc): **`cmp w0, #0x20`**, `b.ne` error → must be 32.
7. `0x4b480-0x4b48c`: `dt_entries_offset` (header +0x14) compared against the 0x1800001 bound (`b.cc` continue).
8. `0x4b530-0x4b5e0`: `dt_entry_count` (header +0x10) × `dt_entry_size` multiply (`mul` at `0x9bb47c09`-encoding) with integer-overflow guards, then bound comparison against `total_size`; failure prints the `Dtbo Table TotalSize/HeaderSize/DtEntrySize/DtEntryOffset got corrupted` family (`0xd3a20/0xd3a44/0xd3a69/0xd3a8f`) and the `DTB header is corrupted, DtEntryOffset %x, DtEntryCount %x, DtEntrySize %x, DtboImgSize %x` diagnostic (`0xd3b01`).

**Not present in this decoded validator**: any check of the `version` field (header +0x1c), any check or use of `page_size` (header +0x18), and **any alignment check on `dt_offset` or `dt_size`** (no `and #3` / `#0xfff` masking in the range; the only immediate masks decoded are the two `#0x20` equality checks).

### 3.2 What actually selects an entry

- The selector strings live in the board-match walk (ROUND156 §2/§3, re-confirmed): `Dtbo count = %u LocalBoardDtMatch = %x` (`0xcfe82`, xrefs `0x39f9c`, `0x3a0ec`) and `DT Total number of entries: %d, DTB version: %d` (`0xcfec8`, xrefs `0x39f9c/0x39fb4/0x39fcc`) — count and version are printed from the validated table, version only as a diagnostic.
- Match participation is by **FDT root properties**, with diagnostics `qcom,msm-id does not match` / `qcom,msm-id entry not found` (`0xd0492/0xd007e`), `qcom,board-id does not match` + major/minor split (`0xd054c/0xd056a/0xd0596`), `qcom,pmic-id does not exit` (`0xd0457`, sic), and the winner log `Best match DTB tags %u/08x/0x%08x/%x/%x/%x/%x/%x/(offset)0x%08x/(size)...` (`0xcfaee`) whose **first `%u` argument is the winning index**, plus `Device tree exact match the board: <0x%x 0x%x 0x%x 0x%x> == <0x%x 0x%x ...>` (`0xd0185`).
- **`dt_table_entry` id/rev/custom do not participate**: all nine stock entries carry zero there while Entry 2 is nonetheless selected. No instruction-level evidence of entry-metadata matching was found in the decoded selector; the format `version = 0` also implies the id/rev/custom metadata is not the selector input.
- **Empirical correction to ROUND156 §2**: stock DTBO entries carry **no `qcom,msm-id` and no `qcom,pmic-id` at root**, yet Entry 2 is selected. On this HOS4.3 device the effective selector input is the root **`qcom,board-id`** exact match (`<0x200e 0x0>`); msm/pmic property handling exists in the same match code but is not exercised by the stock table. How a missing `qcom,msm-id` interacts with the "entry not found" path is not instruction-resolved here — the live outcome (Entry 2 chosen) is Grade A; the exact msm-id skip logic is Grade B/C.

### 3.3 `androidboot.dtbo_idx` derivation

- Written only in the cmdline builder (`androidboot.dtbo_idx=` `0xd245b`, write sites `0x429cc/0x42ac0/0x42b78`); no read-back of it as selector input anywhere (ROUND156 §3.1, unchanged). The value emitted is the winning index from the match walk (the `%u` of `Best match DTB tags %u/...`), i.e. **the loop index of the matched entry**, not a value stored in the table or the FDT.

### 3.4 One-entry image decision — **GO, resulting `androidboot.dtbo_idx=0`**

Question: would a one-entry DTBO image carrying Entry 2's exact selector root properties and exact `dt_table_entry` metadata be selected on this HOS4.3 ABL?

- The validator imposes **no minimum entry count** in the decoded range (count participates only in the count×entry_size bounds arithmetic; count=1 passes trivially). A count of 0 has no candidate and would fall to the `ERROR: Couldn't find the suitable DTB!` terminal path (`0xd06f5`) — i.e. ≥1 entry must match.
- The match walk iterates `dt_entry_count` entries; with exactly one entry whose root carries `qcom,board-id <0x200e 0x0>` (the live device's exact-match value), the walk finds the exact match on the first iteration and the emitted index is **0**.
- No later ABL/kernel handoff consumes a *fixed* index: `androidboot.dtbo_idx` is a pure output; within the decoded ABL scope there is no constant `2` comparison on the index. Consumers beyond ABL (kernel cmdline `ro.boot.dtbo_idx` userspace readers) were **not audited** in this round and remain an explicit open item.
- **Decision: GO** — a one-entry image is structurally selected, with `androidboot.dtbo_idx=0` (not 2). Evidence grade: **B** (structurally supported by decoded validator + match-loop topology + all-zero stock metadata; not boot-proven — no device operation was permitted or performed). The resulting cmdline will differ from stock live state (`dtbo_idx=0` vs `2`); any consumer that hard-codes 2 is unverified and would be a separate risk item.

### 3.5 Parser constraints summary (for the host candidate builder)

| Constraint | Value | Evidence |
|---|---|---|
| Header magic | `0xd7b7ab1e` | A (decoded cmp `0x4b380-0x4b390`) |
| `header_size` | == 32 | A (`cmp #0x20` at `0x4b460`) |
| `dt_entry_size` | == 32 | A (`cmp #0x20` at `0x4b470`) |
| `total_size` | > 0 and ≤ 24 MiB (`0x1800000`) | A (`0x4b440-0x4b45c`) |
| entry array | `entries_offset + count*entry_size` bounded vs `total_size`, overflow-guarded | A (`0x4b530-0x4b5e0`) |
| `version` | no rejection found in decoded validator (stock = 0) | A for absence-in-range; nonzero-version behavior **UNRESOLVED** |
| `dt_offset` alignment | **none required** — stock violates 4-byte and page alignment yet is accepted | A empirical (stock layout + live dtbo_idx=2); B code-level (no alignment ops in decoded validator) |
| Trailing partition padding | need not be zero; parser bounded by `header.total_size` (stock carries AVB data beyond `total_size`) | A empirical |
| Entry FDT integrity | each embedded FDT magic + internal totalsize == dt_size | A (all 9 verified offline) |

Note on taskbook §B.5: the 4096 `page_size` header field is **not** used as an alignment enforcer anywhere in the decoded validator; combined with the stock unaligned layout this explicitly rejects any host-side assumption that `dt_offset` must be page- or even 4-byte aligned.

## 4. Unresolved / not proven (explicit)

1. Nonzero `version` header handling — no rejection found in the decoded range, but not every call path was exhaustively scanned (decoder scope limitation). Stock uses 0; safest host choice is 0.
2. Exact `qcom,msm-id`-absent skip logic inside the match walk (Grade C) — live outcome proves it does not block Entry 2 on this device.
3. Userspace consumers of `androidboot.dtbo_idx` (any hard-coded expectation of 2) — outside ABL scope, not audited.
4. Boot-time acceptance of a one-entry rebuilt DTBO image — static GO above; actual boot acceptance requires a device run and was not performed (and is not permitted in this round).

## 5. Boundaries honored

No device/partition access, no ADB/fastboot, no flash/sign/AVB edits, no kernel source/config/DTB edits, no overlay or DTBO candidate creation, no Window B workspace access, no public HOS4.2 fallback values used, no raw firmware uploaded.

END ROUND159 — WINDOW A
