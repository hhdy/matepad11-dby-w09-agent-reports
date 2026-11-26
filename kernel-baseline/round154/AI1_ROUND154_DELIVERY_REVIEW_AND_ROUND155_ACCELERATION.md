# AI1 ROUND154 Delivery Review and ROUND155 Acceleration Decision

- Reviewer: 1号 AI (ChatGPT)
- Date: 2026-11-26
- Candidate: ACK android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9
- Pre-change source tree: afe9517f8062b96bfeb5b4dd5714942861e6a44b
- No device operation, flash, reboot or partition access performed by this review.

## 1. Delivered reports

| Lane | Report | Blob | Disposition |
|---|---|---|---|
| WorkBuddy Window A (1号 Agent) | [ROUND154 Window A report](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round154-candidate-dtbo-symbol-fixup-boot-packaging/firmware-analysis/round154/WORKBUDDY_A_ROUND154_MINIMAL_RAM_PATCH_AND_DTBO_BOOT_PACKAGE_GATE_REPORT.md) | 5b2f51e598b6550b27bd9ab9eafdffb805178a7f | Read back. Minimal RAM DTS patch and scratch DTB pass; stock overlay compatibility fails; boot-v2 selection partial/unknown; safety not authorized. |
| WorkBuddy Window B (2号 Agent) | [ROUND154 Window B report](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round154-true-independent-ram-reserved-hash/firmware-analysis/round154/WORKBUDDY_B_ROUND154_INDEPENDENT_PATCH_AND_DTBO_REPRODUCTION_REPORT.md) | f187b6151ad291102846933b108148f7b6714f85 | Read back. Explicitly identifies Window B as a separate WorkBuddy chat and isolated workspace. Independently reproduces identity, RAM/reservations, patch DTB and overlay failure. |

Both agents are two separate WorkBuddy chat windows. No different AI product is required.

## 2. Cross-window reproducibility

The reports agree on the key outcomes and binary identities:

| Artifact / test | Window A | Window B | Review |
|---|---|---|---|
| Frozen DTB | 108,648 B; SHA-256 cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e | same measured SHA-256 | Confirmed |
| RAM-patched DTB | 108,680 B; SHA-256 9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60 | same SHA-256 | Byte-identical output |
| Scratch -@ DTB | SHA-256 235663547667c06871c1f2b7a2977395905e0f49ed4b6b543602477316e35ef7 | same SHA-256 | Byte-identical output |
| Symbols exported with -@ | 514 | 514 | Confirmed |
| Entry 2 external symbols resolved with -@ | 10/166; 156 absent | same | Confirmed |
| Entry 2 fragment targets resolved with -@ | 57/144; 87 absent | same | Confirmed |
| Whole stock overlay application | FDT_ERR_NOTFOUND | FDT_ERR_NOTFOUND | Confirmed |

The old expected candidate DTB hash string is 63 hexadecimal characters and invalid. The correct frozen identity, independently reproduced by Window B and recorded by ROUND140/147, is:
cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e
Do not reuse the 63-character value. The previous taskbooks/report lineage overstated its validity.

Window B had not seen Window A's patch when its run completed, so its report correctly marked the direct patch comparison blocked at that time. AI1 has now compared both reports: their RAM-patched DTB and -@ DTB hashes match exactly. Window A's extra source-only comment corrections do not change the DTB bytes.

## 3. Technical decisions

### 3.1 RAM patch: PASS

Retain the three exact device-specific RAM windows on the existing single /memory@80000000 node:
- 0x80000000 + 0x39900000 (921 MiB)
- 0xc0000000 + 0xc0000000 (3072 MiB)
- 0x200000000 + 0x200000000 (8192 MiB)

The 18 reserved-memory children remain unchanged; all lie within the first RAM window. Keep the 70 MiB CDSP carve-out provisionally. Do not generalize this map to other DBY-W09 memory variants.

Window A source tree after patch: c56d93eafa35057d65176db6594d67d5144868a0. Window A patch commit: 491d0cbffb4d16e2840c1788674e6a05b26e88a2. The reversible patch is recorded in Window A's local evidence; it was not placed in the report repository.

### 3.2 Stock DTBO: FAIL

Stock Entry 2 cannot be applied to the candidate. A normal candidate DTB has no exported symbols. Adding -@ exports 514 symbols and makes rootparam available, but still leaves 156/166 external labels and 87/144 fragment targets unresolved. Entry 8 offers no compatibility advantage.

Do not claim that -@ alone solves the problem. Do not package the candidate with the stock Entry 2 overlay as though application were proven.

### 3.3 Boot-v2 / DTBO selection: PARTIAL

The candidate qcom,msm-id matches stock DTB slot 0 (Kona v2.1), but the ABL/XBL selector path is unknown because no exact ABL binary was available in the existing workspace. The stock boot-v2 image contains three concatenated FDTs. A one-FDT package is not justified without loader evidence. DTBO entry selection is separate from SoC DTB selection and must not be conflated.

### 3.4 First-boot safety: FAIL

- AVB/vbmeta chain: PARTIAL; the vbmeta_cust footer/range anomaly remains unexplained and signatures were not verified.
- Required partition backups: FAIL; no complete hash-verified boot-chain backup exists.
- Tested exact-stock restore route: FAIL.
- ABL/XBL binary: absent from existing offline firmware package.

No image has been flashed, and first boot is not safe to start yet.

## 4. ROUND155 shortest path

Do not repeat the RAM or UFS static census. Three focused tasks have been created:

1. **WorkBuddy Window A (1号 Agent):** use the already verified root/ADB access for strictly read-only acquisition of the exact on-device ABL/XBL and relevant boot-chain partitions. Preserve raw copies locally only, verify size and independent SHA-256 reads, analyze the ABL and AVB metadata, and document the restore materials. Do not read userdata or private-data partitions. No write/reboot/flash.
2. **WorkBuddy Window B (2号 Agent):** in its own isolated workspace, test whether the RAM-patched candidate can use a safe no-overlay first-boot path or needs a candidate-specific minimal overlay. Build and apply only scratch DTBOs against nodes and labels that exist; do not claim ABL will select them.
3. **2号 AI:** review both ROUND154 reports and pinned source mechanics, and recommend one minimal first-boot strategy. Separate facts about boot-v2 SoC DTB selection, DTBO index selection, overlay fixups, AVB and rootparam.

## 5. Stop gate

A full kernel/Image build follows only after one coherent candidate base-DTB plus DTBO strategy is proven offline and independently reproduced. Flash remains blocked until the relevant partition backups are hash-verified, AVB/install target behavior is understood, a credible stock recovery route exists, and the user authorizes the write. No unverified flash is justified by the request to accelerate.

— END —