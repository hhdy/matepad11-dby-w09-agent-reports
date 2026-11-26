# ROUND159 — AI2 Independent Frozen HOS4.3 Entry 2 DTBO Component Review

- Reviewer: 2号 AI independent reviewer (not WorkBuddy Window B / 2号 Agent)
- Target: Huawei MatePad 11 DBY-W09, HOS 4.3.0.196(C00E100), SM8250, ACK android17-6.18.33
- Review date: 2026-11-27
- Result: **HOST-SIDE DTBO COMPONENT GO (bounded, static evidence only); integrated boot remains NO-GO**
- Scope: exactly one frozen Entry 2 DTBO component. No device interaction, ADB, fastboot, recovery, partition access/write, boot.img creation, signing, AVB modification, or broad hardware audit.

## 1. Inputs and provenance

### 1.1 Task and plan

- START_PROMPT: `ai2/round159-frozen-dtbo-candidate-review`, blob `bd9004008ea2c436b0e1c911ddc707d044df9aef`.
- AI2 taskbook: same branch, blob `db1056af02b8cc0e07f79b10c0a775e0d237fe96`.
- AI1 plan: `ai1/round159-entry2-candidate-integration/kernel-baseline/round159/AI1_ROUND159_FROZEN_ENTRY2_DTBO_CANDIDATE_PLAN.md`, blob `ffa123600e6a4d50c22c3aa8c8370591b893e44f`.

The plan was refreshed since the previous BLOCKED review. The previous BLOCKED report is therefore stale workflow state and is superseded by this review.

### 1.2 Window A — exact target facts and selector evidence

- Branch: `workbuddy/round159-exact-entry2-facts`
- Report: `firmware-analysis/round159/WORKBUDDY_A_ROUND159_EXACT_ENTRY2_TARGET_FACTS_AND_ABL_SELECTOR_REPORT.md`
- Report blob: `a54c849a84924387b0f13eaf25dd1702398e8b5b`
- Facts JSON: `firmware-analysis/round159/entry2-target-facts.json`
- JSON blob: `db1866588836df69e959a90809e2a5fb12d89cc6`

Both exact files are now published and readable.

### 1.3 Window B — frozen candidate and evidence

- Branch: `agent2/round159-entry2-preserving-dtbo-candidate`
- Candidate report blob: `913a9fce27861104cbf1962a552f0c87779796e9`
- Manifest blob: `d4d672fed96cc49b8a4d2a73dd706397e0fc0b57`
- Normalized facts input blob: `5081365de8686ccd97b983e93282c99d28ecf92d`
- Builder script blob: `c5e5520bd270ec4dfb31040d11d145d5f4a7dfba`
- Text DTS overlay blob: `54317883f920705365fffb157a0d9a06fef396f8`
- Selftest log blob: `7a1459817593f8864703a8e5815e2c0ae8a6e55c`
- Independent verification log blob: `c2895c65427fe247723cf123a7adfcf1fd7725b6`
- Build log blob: `9de2491e35e601497335d08b4eec9a40b7208375`

All files specified by the taskbook are now present. The candidate .dtbo and .dtbo.img were fetched as base64 and decoded for direct byte inspection in this review.

## 2. Source identity and exact HOS4.3 facts

### 2.1 Source artifact identities

Window A records these source identities:

| Artifact | Size | SHA-256 | Review |
|---|---:|---|---|
| Stock DTBO partition capture | 25,165,824 B | `51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c` | Matches AI1 plan and normalized B input |
| Decompressed ABL PE payload | 2,597,064 B | `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404` | Matches AI1 plan |
| Live runtime FDT (ROUND151) | 800,316 B | `fefeaa049f64a9cc79f0aa7558883f7a31ba98cf0ad73f541834c0ec2d46b700` | Window A evidence |
| Extracted stock Entry 2 FDT | 329,240 B | `0633a6fbeebbad45c0f5572faf222c779e1cd51d253a6ef8282592a730ba3c8b` | Window A evidence |
| Candidate base DTB | 108,680 B | `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` | AI1 plan and B manifest agree; raw base DTB was not included in the published B artifacts, so this review cross-checks the identity but does not independently re-hash the base bytes |

The normalized B facts input cites the exact Window A report and JSON blob IDs. Its values match the original Window A facts for the Entry 2 root selector, stock table fields, and all five /rootparam payloads.

### 2.2 Entry 2 selector and five exact /rootparam payloads

The live selected stock entry is index 2 (live `androidboot.dtbo_idx=2`). Entry 2 root selector property is:

- `qcom,board-id = <0x200e 0x0>`, wire bytes `0000200e00000000`.

The exact five HOS4.3 properties from stock Entry 2 fragment@143 / __overlay__ are:

| Property | Exact encoding | Length | Exact bytes |
|---|---|---:|---|
| `qcom,boardid` | u32 cells [8, 2, 0, 6] | 16 B | `00000008000000020000000000000006` |
| `qcom,board_name` | NUL-terminated string | 11 B | `4442595f5730395f564400` = `DBY_W09_VD` |
| `qcom,product_name` | NUL-terminated string | 8 B | `4442592d57303900` = `DBY-W09` |
| `hardware_version` | NUL-terminated string | 9 B | `5348314442534c4d00` = `SH1DBSLM` |
| `huawei,modem_id` | u32 cells [0xffffffff, 0] | 8 B | `ffffffff00000000` |

Important correction retained: `qcom,boardid` is 16 bytes/four u32 cells, not the earlier incomplete three-byte shorthand `08 02 06`. The full modem_id payload is exactly eight bytes and is not borrowed from HOS4.2.

Window A reports that all five stock Entry 2 payloads are byte-identical to the live ROUND151 /rootparam properties. The root selector is distinct from the five /rootparam properties.

## 3. Direct inspection of the frozen candidate bytes

### 3.1 DTBO container

The actual published `entry2-candidate.dtbo.img` bytes were decoded and independently parsed in this review.

- Size: **442 bytes**
- SHA-256: **`f185c13de5f9d2ca8dc2610c4cef33d12db601bfa29bae079fb5827951c1a6cc`**
- Header (big-endian): magic `0xd7b7ab1e`, total_size 442, header_size 32, dt_entry_size 32, dt_entry_count 1, dt_entries_offset 32, page_size 4096, version 0.
- Entry 0: dt_size 378, dt_offset 64, id 0, rev 0, custom[0..3] all zero.
- Arithmetic: total_size = 64-byte header+entry area + 378-byte FDT = 442.
- Embedded payload range [64, 442) is within total_size and does not overlap the table.

These fields match the Window B manifest and the stock Entry 2 table metadata (id/rev/custom all zero). The candidate intentionally has one entry, so its selector result is index 0.

### 3.2 Embedded FDT payload

The actual published `entry2-rootparam.dtbo` bytes were decoded and parsed independently.

- Size: **378 bytes**
- SHA-256: **`5d596c2e38d18d71ebe6cee3a77617a9185ab13a941b995e57e75d8fc6ae7ea3`**
- FDT magic: `0xd00dfeed`
- FDT totalsize: 378 (exactly equals table entry dt_size)
- FDT version: 17
- Root `qcom,board-id`: exact bytes `0000200e00000000`.
- Fragment target: `/rootparam`.
- Overlay contains exactly the five target properties listed in §2.2; each decoded property payload is byte-identical to Window A's target facts.
- No extra rootparam property or unrelated overlay fragment is present.

The independently computed SHA-256 values and decoded fields match the Window B manifest. The DTS source also expresses the same root selector, target path and five values.

### 3.3 Table layout and alignment interpretation

The candidate's `dt_offset=64` is not page-aligned to 4096, but this is **not a defect on the available evidence**:

- Window A's stock table has packed entries with offsets that are not 4096-aligned; some are not even 4-byte aligned, yet the live device selects stock Entry 2.
- Window A's decoded HOS4.3 validator contains no dt_offset/dt_size alignment check in the examined validator region.
- AOSP's official DTBO format example uses `page_size=2048` and `dt_offset=128`; page_size is not a universal dt_offset alignment rule.
- The exact target ABL contract, not an assumed 4096-byte rule, governs. Candidate header page_size=4096 preserves the target's stock header value.

Therefore no alignment-based rejection is warranted.

## 4. ABL selector compatibility — static, bounded finding

Window A's decoded ABL analysis reports:

- DTBO magic must be `0xd7b7ab1e`.
- `total_size` must be nonzero and no larger than 24 MiB.
- `header_size=32` and `dt_entry_size=32`.
- Entry-array bounds are checked using count × entry size with overflow guards.
- No minimum count greater than one was found; a one-entry table passes the described count/bounds logic.
- The selector walks entries and uses root FDT board identity. Stock Entry 2's effective exact match is `qcom,board-id <0x200e 0>`.
- `androidboot.dtbo_idx` is written as the winning entry's loop index; it is not read back as selector input.
- No fixed index-2 consumer was found within the decoded ABL scope.

Thus the one-entry candidate is statically selected at **index 0**, according to the Window A ABL analysis. This is a **Grade B static selector conclusion**, not a boot test or proof of every downstream consumer.

Explicit unresolved item: userspace consumers of `ro.boot.dtbo_idx` were not audited. The change from live stock index 2 to candidate index 0 may matter to an out-of-scope consumer. This caveat does not contradict the ABL's own selector walk, but it prevents claiming end-to-end boot compatibility.

## 5. Host merge and negative checks

Window B's manifest and committed logs report:

- Text DTS source compiled with dtc and structurally matched the generated overlay (0 structural differences).
- Independent container reparse and byte-identical reserialization passed.
- Embedded FDT bytes equal the standalone .dtbo bytes.
- Host `fdtoverlay` merge returned success and structural diff contained exactly five ADDED properties under `/rootparam`, with zero unrelated node/property changes.
- All five merged values matched the normalized exact facts.
- Independent verification log: 11/11 checks PASS.
- Selftest log: 8/8 checks PASS, including truncated container, bad magic, totalsize lie and misspelled target-path negative cases.

Review limitation: the candidate base DTB itself is not included in the published Window B artifact directory. Consequently I inspected the builder, manifest, actual overlay/container bytes and committed logs, but could not independently rerun the real-base fdtoverlay merge in this review. The exact-five-change merge result is therefore **corroborated by Window B's manifest/logs, not independently reproduced against the base bytes**. The synthetic selftest uses deliberately synthetic payloads and is not treated as proof of the exact HOS4.3 payload values; those exact values were instead checked directly in the real candidate FDT bytes.

## 6. Component decision matrix

1. **DTBO FDT payload validity — PASS.** Actual FDT bytes parse; magic, totalsize, version, selector property, target path, all five exact payloads and SHA-256 match the published manifest and Window A facts. Host merge exact-five-additions result is supported by B's manifest/logs, with the reproduction limitation stated in §5.
2. **Android DT table serialization — PASS.** Actual 442-byte container header and single entry were independently decoded; sizes, offsets, count, metadata, payload bounds, FDT totalsize and SHA-256 are internally consistent and match the manifest.
3. **HOS4.3 ABL selector compatibility — PASS (static Grade B only).** Window A's decoded validator/selector evidence supports one matching entry at index 0. No device boot acceptance is claimed; userspace dtbo_idx consumers remain unaudited.
4. **Integrated boot-v2 package — NO-GO.** This component review does not establish boot-v2 handoff, ABL /memory/reg rebuild behavior, UFDT failure atomicity, AVB/vbmeta acceptance, Huawei TZ/OEM authorization, or actual bootability. No boot.img or integrated package was created or reviewed.
5. **Temporary boot and partition write — NO-GO.** Outside this task's scope and not authorized. No device, ADB, fastboot, recovery, reboot, partition read/write or flash operation was performed.

**Bounded conclusion: GO for this one host-side DTBO component's static payload/table/ABL-selector checks, with the evidence and reproduction limits above. This is not a GO for temporary boot, boot-v2 integration, or partition writing.**

## 7. Stop condition

ROUND159 review is complete. Stop after this report is committed and read back. Do not create a next audit task or expand into unrelated hardware research.

---
End of ROUND159 AI2 independent component review.
