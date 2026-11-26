# ROUND159 — WorkBuddy Window B Report: Frozen Entry2 DTBO Candidate (Skeleton Complete, Build Blocked on Window A Facts)

- Executor: **WorkBuddy Window B (2号 Agent)**. Host-only, offline. No device, no ADB/root/fastboot/recovery, no reboot, no partition writes, no flash, no AVB/signing/key work. Window A's private workspace was not accessed.
- Taskbook: `firmware-analysis/round159/WORKBUDDY_B_ROUND159_FROZEN_ENTRY2_DTBO_CANDIDATE_TASKBOOK.md`
- **Verdict: `BLOCKED — WAITING FOR WINDOW A FACTS`. The deterministic generator/validator skeleton is complete and self-tested (8/8 PASS). No candidate DTBO was produced, per taskbook §2 stop rule.**

## 1. Fixed input identities re-verified

| Item | Value | Status |
|---|---|---|
| Candidate source tree | `c56d93eafa35057d65176db6594d67d5144868a0` | cited, not touched this round |
| Candidate base DTB (Window B's own R156 frozen output) | 108,680 B, SHA-256 `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` | **re-hashed locally, exact match** |
| Stock dtbo partition (Window A only) | `51a5d7b8…` / 25,165,824 B | **not read** (Window A ownership) |
| Live selected entry | Entry 2 / board-id 0x200e / dtbo_idx=2 | cited from prior rounds |
| ABL payload | `a14e29da…` | cited from R158; not re-analyzed this round |

## 2. Dependency status — precise blocker

Taskbook §2 requires `firmware-analysis/round159/entry2-target-facts.json` from branch `workbuddy/round159-exact-entry2-facts`.

Fetched that branch (remote tip `c293351d3bdfd0cbb2766514df90118beebe6e8b` at fetch time):

```
firmware-analysis/round159/START_PROMPT_WORKBUDDY_A_ROUND159_EXACT_ENTRY2_TARGET_FACTS_AND_ABL_SELECTOR.md
firmware-analysis/round159/WORKBUDDY_A_ROUND159_EXACT_ENTRY2_TARGET_FACTS_AND_ABL_SELECTOR_TASKBOOK.md
```

**`entry2-target-facts.json` is NOT published. Window A's R159 report is also not published.** A remote `ls-remote` cross-check shows no other round159 branch carries the facts file (only taskbook/prompt branches exist; Window A's R158 report branch predates this round).

Blocker statement (exact): *Window A has not yet delivered the exact HOS4.3 Entry 2 table fields, the exact five `/rootparam` property wire encodings (including the full `huawei,modem_id` byte payload), or the proven ABL selector/table-layout decision. Per taskbook §2 and §5, no speculative binary is built.*

The published Window A taskbook was read to align the facts schema (its Task A.7). HOS4.2 public placeholder values (0x206a, guessed modem_id) were **not** used anywhere.

## 3. Deliverable: `build_entry2_dtbo.py` (committed with this report)

Self-contained (Python stdlib only), deterministic, two modes:

- `selftest` — no facts needed, produces no candidate. Validates the FDT writer/reader round-trip, the dt_table container writer/reader round-trip, and negative checks.
- `build --facts <json> --base <dtb> --outdir <dir>` — full candidate build. **Refuses to run** unless the facts JSON contains Window A's proven decision (`abl_decision.one_entry_go == true`), the exact five `rootparam_properties`, non-empty `selector_root_properties`, and a valid `dt_table_header` (magic `0xd7b7ab1e`, explicit `page_size`/`version`/`header_size`/`dt_entry_size`).

Expected facts schema (aligned with Window A taskbook Task A.7; strict encodings `string` / `u32-cells` / `raw-bytes`, no coercion — documented in the script docstring):

- `source`: stock dtbo.img + Entry2 FDT hashes;
- `dt_table_header`: exact stock header as parsed by Window A;
- `entry2_table_fields`: `dt_size/dt_offset/id/rev/custom[0..3]` (table metadata, kept distinct from FDT root properties);
- `selector_root_properties`: root-level selector props (marked `required` or not);
- `rootparam_properties`: exactly five, including `huawei,modem_id` as raw hex;
- `abl_decision`: `one_entry_go` GO/NO-GO, resulting `dtbo_idx`, `preserve_index_2`, layout decision.

Design points implemented per taskbook §3:

- Overlay = root selector props + ONE fragment `target-path = "/rootparam"` + exactly five props in `__overlay__`. No unrelated fragments; no transplant of stock Entry 2's 166 external fixups; no `__symbols__`/`__fixups__` emitted (R154 proved the candidate base carries none, and target-path binding needs none).
- Container written per the Android `dt_table` big-endian layout (R153-verified `>8I` header + 32-byte entries); header fields come from facts, not hardcoded guesses. `page_size` is recorded as flash-page size only — **no 4096-byte dt_offset alignment is asserted** (AOSP documents page_size=2048 with dt_offset=128; any ABL-specific alignment must arrive via facts with ABL code evidence).
- Independent reparse + reserialize must be byte-identical; embedded FDT bytes must equal the source overlay bytes (asserted in `build`).
- Merge validation: `fdtoverlay` merge onto the fixed candidate base, structural diff must be **exactly five ADDED properties under `/rootparam`, zero other changes**, and each merged payload must be byte-identical to the facts JSON (recomputed independently of the overlay file). Host-tool acceptance is never presented as ABL/device acceptance.
- Negative checks built in: target-path typo must fail; malformed/truncated/bad-magic/lying-totalsize containers must be rejected by the parser.

## 4. Self-test results (committed evidence: `evidence/selftest.log`)

Run under WSL Ubuntu-24.04, Python 3.12, fdtoverlay/dtc 1.7.0, base = fixed candidate DTB:

| Check | Result |
|---|---|
| `fdt_roundtrip` (writer→reader, rootparam node + phandle) | PASS |
| `reader_vs_candidate_dtb` (905 nodes, `/rootparam` present) | PASS |
| `container_roundtrip` (+ reserialize byte-identical, entry id `0x200E`) | PASS |
| `negative_truncated_REJECTED` | PASS |
| `negative_badmagic_REJECTED` | PASS |
| `negative_totalsize_lie_REJECTED` | PASS |
| `negative_targetpath_typo_FAILS` (fdtoverlay rc≠0, `FDT_ERR_NOTFOUND`) | PASS |
| `positive_synthetic_merge_5_additions_only` (synthetic facts; diff = exactly 5 `/rootparam` ADDED, nothing else) | PASS |
| **SELFTEST** | **PASS (8/8)** |
| `build` with NO-GO facts → `FACTS-REJECTED`, exit 2, **zero files produced** | PASS (`evidence/nogo-refusal.log`) |

Note: self-test property values are synthetic placeholders for mechanics validation only; they were never written into a candidate artifact (no candidate artifact exists).

## 5. Tooling finding recorded (affects future rounds)

`fdtoverlay` (dtc 1.7.0) argument order is **`-i <base-dtb> -o <out> <overlay-dtb>`**. With inverted arguments (`-i overlay … base`) the tool **silently no-ops and exits 0**, writing an output shaped like the "base" it was given (e.g., 362-byte overlay-only output) — no error, no merge. Reproduced with both a dtc-compiled overlay and a scripted one; evidence retained locally (`evidence/fdtoverlay-inverted-args-silent-noop.dtb`). Any prior or future host merge claim must state the argument order used. R156's negative test (`negative.sh:14`) used the correct order.

## 6. Next step (unblocks in one command)

Once Window A publishes `entry2-target-facts.json` on `workbuddy/round159-exact-entry2-facts`:

```
python3 build_entry2_dtbo.py build --facts entry2-target-facts.json \
    --base patched.dtb --outdir <out>
```

produces `entry2-rootparam.dtso`, `entry2-rootparam.dtbo`, `entry2-candidate.dtbo.img`, `entry2-candidate-manifest.json` with all §3 validations executed. If Window A's decision is `preserve_index_2` instead of single-entry, the facts schema carries that decision and the build command is extended only then — no speculative variants are built now.

## 7. Boundaries

No device operation, no fastboot command, no partition write, no flash, no reboot, no boot.img/boot-v2/ramdisk/vbmeta/AVB artifact, no raw stock dtbo.img or ABL upload, no HOS4.2 placeholder substitution. No candidate DTBO component exists at the time of this report. Window A's private workspace and raw artifacts were not accessed.

## 8. Artifacts in this commit

| Path | Purpose |
|---|---|
| `firmware-analysis/round159/build_entry2_dtbo.py` | deterministic generator/validator (deliverable) |
| `firmware-analysis/round159/WORKBUDDY_B_ROUND159_FROZEN_ENTRY2_DTBO_CANDIDATE_REPORT.md` | this report |
