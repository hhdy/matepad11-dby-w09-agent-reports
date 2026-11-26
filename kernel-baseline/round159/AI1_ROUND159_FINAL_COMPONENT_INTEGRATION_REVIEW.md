# AI1 ROUND159 Final Integration Review — Frozen HOS4.3 Entry 2 DTBO Component

- Reviewer/integrator: 1号 AI (ChatGPT)
- Target: Huawei MatePad 11 DBY-W09 / HOS 4.3.0.196(C00E100) / SM8250
- Date: 2026-11-27
- Scope: final offline validation of the one ROUND159 DTBO component. This report does not claim an independent 2号 AI approval and does not authorize device operations.

## 1. Final artifacts and source-of-truth links

### Window A — target-derived stock facts

- Report: `firmware-analysis/round159/WORKBUDDY_A_ROUND159_EXACT_ENTRY2_TARGET_FACTS_AND_ABL_SELECTOR_REPORT.md`
- Report blob: `a54c849a84924387b0f13eaf25dd1702398e8b5b`
- Facts JSON: `firmware-analysis/round159/entry2-target-facts.json`
- JSON blob: `db1866588836df69e959a90809e2a5fb12d89cc6`
- Stock DTBO: 25,165,824 B, SHA-256 `51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c`
- Extracted Entry 2 FDT: 329,240 B, SHA-256 `0633a6fbeebbad45c0f5572faf222c779e1cd51d253a6ef8282592a730ba3c8b`
- Exact HOS4.3 ABL payload: 2,597,064 B, SHA-256 `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`

Exact HOS4.3 /rootparam payloads:
- `qcom,boardid`: u32 cells [8,2,0,6], 16-byte wire `00000008000000020000000000000006`.
- `qcom,board_name`: `DBY_W09_VD`.
- `qcom,product_name`: `DBY-W09`.
- `hardware_version`: `SH1DBSLM`.
- `huawei,modem_id`: u32 cells [0xffffffff,0], 8-byte wire `ffffffff00000000`.

All five are reported byte-identical to ROUND151's live runtime FDT. The earlier shorthand `080206` was incomplete and is superseded by the 16-byte four-cell value above.

### Window B — one frozen candidate

- Final report: `firmware-analysis/round159/WORKBUDDY_B_ROUND159_FROZEN_ENTRY2_DTBO_CANDIDATE_REPORT.md`
- Report blob: `913a9fce27861104cbf1962a552f0c87779796e9`
- Manifest blob: `d4d672fed96cc49b8a4d2a73dd706397e0fc0b57`
- Build log blob: `9de2491e35e601497335d08b4eec9a40b7208375`
- Independent verify log blob: `c2895c65427fe247723cf123a7adfcf1fd7725b6`
- Self-test log blob: `7a1459817593f8864703a8e5815e2c0ae8a6e55c`

Final artifact identities:
| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `entry2-rootparam.dtso` (text source) | 369 | `34939a4146e3280ff7ee521b48b0d3a388b172770fd6ac306b127172dbaf0442` |
| `entry2-rootparam.dtbo` (compiled FDT) | 378 | `5d596c2e38d18d71ebe6cee3a77617a9185ab13a941b995e57e75d8fc6ae7ea3` |
| `entry2-candidate.dtbo.img` (one-entry dt_table) | 442 | `f185c13de5f9d2ca8dc2610c4cef33d12db601bfa29bae079fb5827951c1a6cc` |

The B branch's original BLOCKED report is superseded by the final B report above. It was valid when authored because A had not yet published its facts.

## 2. AI1 independent byte/hash verification performed in this integration

The committed DTBO FDT and dt_table binary were fetched again from the B branch as base64 bytes and independently hashed and parsed in this integration.

Results:
- DTBO payload: 378 B; SHA-256 equals manifest; FDT magic `0xd00dfeed`, FDT totalsize 378, FDT version 17.
- dt_table image: 442 B; SHA-256 equals manifest; big-endian header = `magic 0xd7b7ab1e`, `total_size 442`, `header_size 32`, `dt_entry_size 32`, `count 1`, `entries_offset 32`, `page_size 4096`, `version 0`.
- Entry 0 = `dt_size 378`, `dt_offset 64`, `id 0`, `rev 0`, `custom[0..3]=0`.
- Payload extracted from the container has the same SHA-256 as the standalone .dtbo file.

The standalone FDT was independently parsed at the property-wire level. All seven expected items match:
- root `qcom,board-id=<0x200e 0>`;
- `fragment@0/target-path="/rootparam"`;
- all five /rootparam property payloads exactly as listed in §1.

Window B's published positive host-merge evidence reports `fdtoverlay -i BASE -o OUTPUT OVERLAY`, with exactly five ADDED properties under `/rootparam`, zero unrelated changes, and all payloads matching the facts. Its independent verification log records 11/11 checks passing, including table round-trip, payload equality, entry metadata, malformed/truncated rejection and a wrong-target-path negative case. AI1's direct byte verification corroborates the published file sizes, hashes, header and FDT payload content; AI1 did not rerun fdtoverlay against Window B's private base DTB.

## 3. Candidate component disposition

| Gate | AI1 result | Reason |
|---|---|---|
| Exact HOS4.3 rootparam facts | PASS | Window A's source facts and live FDT byte comparison are present |
| DTBO FDT payload integrity | PASS | Hash verified; FDT parses; selector property, target path and five exact payloads match |
| Android dt_table serialization | PASS | Header/entry parsed; bounds, one entry and embedded FDT size/hash are consistent |
| Host merge / exact diff | PASS based on Window B evidence | Published build and independent-verification logs show exactly five additions, no unrelated changes |
| HOS4.3 ABL one-entry selection | CONDITIONAL / Grade B static GO | Window A decodes a 1-entry match to index 0, but no actual device boot was performed |
| User-space consumption of `ro.boot.dtbo_idx=0` | OPEN | Not audited; stock runtime was index 2 |
| Integrated boot-v2 image/package | NO-GO | Boot-v2 handoff, /chosen/ramdisk contract, AVB/Huawei OEM acceptance and complete package composition remain unresolved |
| Temporary boot | NO-GO | No positive exact-target proof that the unlocked ABL accepts it |
| Partition write | HARD NO-GO | Recovery/restore path, A-only layout and full chain backup/AVB acceptance remain incomplete |

**AI1 conclusion:** the single host-side Entry 2 DTBO component is now frozen and passes the offline FDT/container/host-merge checks. This is not a bootable or flashable package. It must not be written to the DTBO partition by itself. The table is 442 bytes and contains no original AVB descriptor/footer; its component-only nature is intentional.

## 4. Independent 2号 AI review status — stale report must not be misrepresented

The file at the assigned 2号 AI report path currently remains blob `20fa1f5e3dd5c48c7f8c7ed207955ce23841f3ab`. It is the earlier **BLOCKED — required Window A and Window B artifacts are not published** report, authored before Window A facts and Window B final candidate existed. It has not been replaced with a review of the final candidate.

Therefore:
- This old BLOCKED report is **not** a negative technical finding against the candidate.
- It also cannot be counted as 2号 AI approval of the final candidate.
- AI1 has performed its own final byte-level check as documented above, but does not impersonate 2号 AI.

## 5. End of ROUND159 and next phase boundary

ROUND159's implementation goal — one reproducible host-side HOS4.3 Entry 2 DTBO candidate — is complete. No competing variants were created; kernel source/config/base DTB were not changed; no device operation occurred.

Do not automatically open ROUND160 or repeat the same DTBO tests. The next work, when the independent review status is settled, should move directly to the minimum boot-v2 package prerequisites and a single consolidated recovery/acceptance gate. Current hard blockers remain:
1. exact boot-v2 kernel/ramdisk/initrd and `/chosen` handoff assembly;
2. ABL runtime `/memory/reg` rewrite and resulting memory/reserved-memory map;
3. UFDT overlay error atomicity / safe application behavior;
4. Huawei AVB/TZ/OEM digest/signature/rollback acceptance for modified images;
5. credible exact-stock recovery and restoration route (A-only target, complete GPT/chain evidence and restore rehearsal);
6. check whether any Android userspace consumer assumes `androidboot.dtbo_idx=2` rather than 0.

No boot.img, boot-v2 package, ramdisk, vbmeta, signing material, temporary boot, reboot, ADB/fastboot command, partition write or flash was produced/performed in ROUND159.

**Final status: DTBO COMPONENT = FROZEN / OFFLINE PASS. FIRST BOOT PACKAGE = NOT READY.**
