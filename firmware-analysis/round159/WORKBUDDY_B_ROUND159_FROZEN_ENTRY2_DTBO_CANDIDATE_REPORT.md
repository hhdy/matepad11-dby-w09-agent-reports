# ROUND159 — WorkBuddy Window B Report: Frozen Entry2 DTBO Candidate (FINAL)

- Executor: **WorkBuddy Window B (2号 Agent)**. Host-only, offline. No device, no ADB/root/fastboot/recovery, no reboot, no partition read/write, no flash, no boot.img/boot-v2/ramdisk/vbmeta/AVB work, no signing or keys. Kernel source/config/base DTB untouched. Window A's private workspace was not accessed.
- Taskbook: `firmware-analysis/round159/WORKBUDDY_B_ROUND159_FROZEN_ENTRY2_DTBO_CANDIDATE_TASKBOOK.md`; continuation: `ROUND159_WINDOW_B_CONTINUATION_AFTER_WINDOW_A_FACTS.md`.
- **Verdict: COMPLETE — ONE host-side DTBO candidate component built, independently re-parsed, round-tripped, host-merge-verified and negative-tested. This is a host candidate, not boot proof.**

**Status history**: the first Window B report on this branch was `BLOCKED — WAITING FOR WINDOW A FACTS` (correct at the time: `entry2-target-facts.json` did not exist yet). Window A has since published its report and facts JSON; this report supersedes that verdict per the continuation instruction (same ROUND159, no new audit round).

## 1. Input identities (all re-verified this round)

| Item | Value | Verification |
|---|---|---|
| Candidate base DTB (Window B's own R156 frozen output) | 108,680 B, SHA-256 `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` | re-hashed locally, exact match |
| Normalized builder input `entry2-target-facts.builder-input.json` (committed on this branch) | 2,197 B, SHA-256 `f1dbe1aa6873120be0133febfdc86759ad083a1491949605337115559a805658`, blob `5081365de8686ccd97b983e93282c99d28ecf92d` | fetched from branch tip; cited origin blobs inside re-verified against Window A branch (`origin_json_blob db186658…` ✓, `origin_report_blob a54c849a…` ✓) |
| Window A facts (original) `entry2-target-facts.json` | blob `db1866588836df69e959a90809e2a5fb12d89cc6` | cross-checked field-by-field against normalized input (see §2) |
| Stock dtbo partition (Window A only) | `51a5d7b8…` / 25,165,824 B | cited from facts; **not read** |
| Stock Entry2 FDT | 329,240 B, `0633a6fb…` | cited from facts; **not read** |
| ABL payload | `a14e29da…` | cited; not re-analyzed |

Blob discrepancy note: the continuation document cites normalized-input blob `fabda246…`, but the current branch tip blob is `5081365d…` (the file was evidently revised after the doc was committed). Content was cross-verified against Window A's original facts JSON, so the tip content is authoritative; both values recorded here.

## 2. Facts cross-verification (normalized vs Window A original)

| Field | Normalized | Window A original | Match |
|---|---|---|---|
| stock dtbo sha/size | `51a5d7b8…` / 25,165,824 | same | ✓ |
| Entry2 FDT sha/size | `0633a6fb…` / 329,240 | same | ✓ |
| dt_table_header (stock) | magic `0xd7b7ab1e`, hs=32, es=32, count=9, eo=32, page=4096, ver=0 | same (plus total_size 2,963,810 & trailing-AVB notes) | ✓ |
| Entry2 table fields | dt_size 329,240 / dt_offset 658,716 / id 0 / rev 0 / custom[0..3]=0 | same | ✓ |
| selector | `qcom,board-id = <0x200e 0>` only, required | same (msm-id/pmic-id null; compatible/model documented not selector-effective) | ✓ |
| `qcom,boardid` | u32 [8,2,0,6] → 16 B `00000008000000020000000000000006` | same, sha `b1d1c09e…`, `live_fdt_rootparam_byte_identical: true` | ✓ |
| `qcom,board_name` / `qcom,product_name` / `hardware_version` | `DBY_W09_VD` / `DBY-W09` / `SH1DBSLM` | same, all `live_fdt_rootparam_byte_identical: true` | ✓ |
| `huawei,modem_id` | u32 [0xffffffff,0] → 8 B `ffffffff00000000` | same, sha `72a4fa35…` | ✓ |
| ABL decision | `one_entry_go: true`, resulting dtbo_idx **0**, grade B | A report §3.4 "GO — one-entry image structurally selected, `androidboot.dtbo_idx=0`"; no fixed-index consumer found in decoded ABL; userspace `ro.boot.dtbo_idx` consumers NOT audited (open item) | ✓ |

HOS4.2 placeholders (0x206a, guessed modem_id) and the old 3-byte `080206` shorthand were **not** used anywhere.

## 3. Command

```
python3 build_entry2_dtbo.py build \
  --facts entry2-target-facts.builder-input.json \
  --base patched.dtb  (9d0d7600…, R156 frozen) \
  --outdir round159-entry2-final
```

WSL Ubuntu-24.04, Python 3.12, dtc/fdtoverlay 1.7.0. fdtoverlay invocation order: `fdtoverlay -i BASE -o OUTPUT OVERLAY` (see §6 tooling note). Merge verdict is based on structural diff, not RC alone.

## 4. Deliverables (committed on this branch)

| File | Size | SHA-256 |
|---|---|---|
| `entry2-rootparam.dtso` (textual DTS source) | 369 B | `34939a4146e3280ff7ee521b48b0d3a388b172770fd6ac306b127172dbaf0442` |
| `entry2-rootparam.dtbo` (compiled overlay FDT) | 378 B | `5d596c2e38d18d71ebe6cee3a77617a9185ab13a941b995e57e75d8fc6ae7ea3` |
| `entry2-candidate.dtbo.img` (single-entry container) | 442 B | `f185c13de5f9d2ca8dc2610c4cef33d12db601bfa29bae079fb5827951c1a6cc` |
| `entry2-candidate-manifest.json` | 2,049 B | (in repo; contains all above hashes + validation results) |
| `build_entry2_dtbo.py` (updated generator/validator) | — | (see commit) |
| test logs: `evidence/selftest.log`, `evidence/independent-verify.log`, `evidence/build.log` | — | (in repo) |

Overlay content (textual source, exact):

```dts
/dts-v1/;
/ {
    qcom,board-id = <0x200e 0x0>;
    fragment@0 {
        target-path = "/rootparam";
        __overlay__ {
            qcom,boardid = <0x8 0x2 0x0 0x6>;
            qcom,board_name = "DBY_W09_VD";
            qcom,product_name = "DBY-W09";
            hardware_version = "SH1DBSLM";
            huawei,modem_id = <0xffffffff 0x0>;
        };
    };
};
```

## 5. Container fields and validation results

Container (independently re-parsed and reserialized byte-identical):

| Field | Value |
|---|---|
| magic | `0xd7b7ab1e` |
| total_size | 442 = 64 (header+entry) + 378 (FDT payload) |
| header_size / dt_entry_size | 32 / 32 |
| dt_entry_count | **1** |
| dt_entries_offset | 32 |
| page_size / version | 4096 / 0 |
| Entry 0 | dt_size=378, dt_offset=64, **id=0, rev=0, custom[0..3]=0** (exact stock Entry2 metadata per facts) |
| resulting dtbo_idx | **0** (per Window A GO; differs from stock live dtbo_idx=2 — see §7 open items) |

Validation matrix (all PASS; full logs committed):

| Check | Result |
|---|---|
| Skeleton selftest (FDT round-trip; reader vs 905-node candidate DTB; container round-trip; truncated/bad-magic/totalsize-lie rejected; typo target-path fails; synthetic merge = 5 additions only) | PASS 8/8 |
| Independent reparse: count=1, reserialize byte-identical, embedded FDT == `.dtbo` file bytes | PASS |
| Entry metadata all zero; total_size = 64 + payload; page_size 4096 / version 0 | PASS |
| Overlay root selector `qcom,board-id = <0x200e 0>` exact | PASS |
| `.dtso` text → dtc recompile → structural diff vs scripted binary FDT | PASS (0 diffs) |
| Host merge `fdtoverlay -i base -o out overlay`: diff = **exactly 5 ADDED properties under `/rootparam`**, zero unrelated changes | PASS |
| Merged payloads byte-identical to facts JSON (recomputed independently of overlay bytes) | PASS |
| Negative: truncated real container rejected; FDT-totalsize lie (entry dt_size 378→99999) rejected; real-facts typo overlay `/rootparam_typo` fails under fdtoverlay (`FDT_ERR_NOTFOUND`, rc≠0) | PASS |
| **Independent verification of the real artifacts** | **PASS 11/11** |

No host-tool acceptance is presented as ABL/device acceptance.

## 6. Tooling notes carried from the skeleton phase

- `fdtoverlay` (dtc 1.7.0) argument order is `-i <base> -o <out> <overlay>`; inverted arguments silently no-op with rc=0. All merge calls this round used the correct order and were verified by structural diff.
- `entry2-rootparam.dtso` is textual DTS source (continuation §3.1 correction; the earlier blocked-phase script wrote binary to both paths — fixed).
- Parser now enforces embedded FDT totalsize == dt_size and payload/table range non-overlap (continuation §3.3).

## 7. Limitations and explicit component-only decision

1. **Component only**: this is a host-built DTBO candidate. It is NOT boot-proven. Window A's ABL GO is grade B (structural); actual boot acceptance of a rebuilt one-entry image was not and will not be tested without explicit user authorization.
2. `androidboot.dtbo_idx` will be **0** (not the stock 2). Window A found no fixed-index consumer inside the decoded ABL, but **userspace consumers of `ro.boot.dtbo_idx` were not audited** — explicit open item.
3. `huawei,modem_id` here is the generic stock Entry2 payload (`ffffffff00000000`), byte-identical to the R151 live FDT per Window A facts; it is not a per-device serial.
4. The stock partition's trailing 22,202,014 AVB bytes are beyond `header.total_size`; the in-device parser is bounded by total_size (A report §63). This candidate's total_size is exactly 64+378 with no trailing data.
5. No AVB/vbmeta interaction is addressed: signing/boot packaging is out of ROUND159 scope.
6. No competing variants were built; exactly one candidate exists.

## 8. Artifacts in this commit

| Path | Purpose |
|---|---|
| `firmware-analysis/round159/build_entry2_dtbo.py` | final generator/validator |
| `firmware-analysis/round159/entry2-rootparam.dtso` / `.dtbo` / `entry2-candidate.dtbo.img` / `entry2-candidate-manifest.json` | the ONE candidate component + manifest |
| `firmware-analysis/round159/WORKBUDDY_B_ROUND159_FROZEN_ENTRY2_DTBO_CANDIDATE_REPORT.md` | this report |
| `firmware-analysis/round159/evidence/` | selftest / independent-verify / build logs |
