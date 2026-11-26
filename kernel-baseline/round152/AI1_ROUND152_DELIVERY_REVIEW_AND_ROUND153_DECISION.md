# AI1 ROUND152 Delivery Review and ROUND153 Decision

- Reviewer: 1号 AI (ChatGPT)
- Fixed target: ACK `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Candidate tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- Review date: 2026-11-26
- Candidate remains frozen. No source/DTS/patch/build/device action was taken in this review.

## 1. ROUND152 delivery integrity

| Workstream | Published item | Review disposition |
|---|---|---|
| Candidate DTB / stock FDT / RAM / reserved-memory / UFS delta | `firmware-analysis/round152/AGENT2_ROUND152_CANDIDATE_DTB_STOCK_FDT_MEMORY_RESERVED_UFS_DELTA_REPORT.md`, blob `5b67d0560a0357eb7d6726d9cc437d5da4f0eb7a` | Content is readable and internally detailed; **not an independent 2号 Agent deliverable**. Its §1.4 explicitly says the WorkBuddy-side Agent executed it while reading the permitted `round140-agent2` workspace. Treat as a WorkBuddy-side re-derivation, not as Agent 2's independent result. |
| Existing ROUND151 regulator-summary / ARC / proxy re-analysis | `firmware-analysis/round152/WORKBUDDY_ROUND152_EXISTING_REGULATOR_SUMMARY_PROXY_RUNTIME_REVIEW.md`, blob `97e1ab888571a9d7abdebf0cf836356ef2c34efa` | Delivered by WorkBuddy Agent as assigned; readback path and contents verified. |
| Independent UFS GDSC / GenPD / devfreq / ARC / proxy architecture review | Expected: `firmware-analysis/round152/AI2_ROUND152_LIVE_UFS_GDSC_GENPD_ARC_PROXY_DECISION_REPORT.md` on `ai2/round152-live-ufs-gdsc-genpd-arc-proxy-decision` | **Not present at the expected delivery path** at review time. The branch's `firmware-analysis/round152` directory contains only the taskbook and start prompt. Do not mark AI2 review complete until its report is uploaded and read back. |

The candidate-DTB report's SHA/size match the frozen DTB (`108648` bytes; SHA-256 `cab82fe3901dbb40533197eb48b2d99b08b46e5d5497ff1a6f688e9938db77e`). Its numerical work remains useful, but the execution-identity mismatch must not be hidden.

## 2. Findings that are now firm enough to carry forward

### 2.1 Candidate RAM must be made explicit for a deterministic first boot

The candidate `/memory@80000000` has exactly one 2/2 tuple with size zero. The pinned ACK early FDT memory scanner ignores zero-sized tuples; a kernel given only this candidate blob therefore receives no System RAM from that node.

The live stock HOS FDT and `/proc/iomem` corroborate the following map for this exact tablet:

| Base | Size | MiB |
|---|---:|---:|
| `0x80000000` | `0x39900000` | 921 |
| `0xc0000000` | `0xc0000000` | 3072 |
| `0x200000000` | `0x200000000` | 8192 |

Total declared RAM: 12,185 MiB. The exact map is unit-specific evidence, not a universal DBY-W09 SKU assumption.

**AI1 decision:** for this single-device bring-up candidate, replace the existing zero-sized `/memory/reg` property with these three exact, non-overlapping tuples in ascending address order. Do not add a second memory node. This removes dependence on whether ABL rewrites or preserves the placeholder. The next implementation must still inspect the post-build DTB bytes and verify all three tuples and all reserved ranges. Any claim that ABL will reliably fill an arbitrary replacement DTB remains unproven.

### 2.2 Reserved-memory: retain the current layout provisionally; do not blindly clone HOS

The candidate has 18 non-overlapping static carve-outs totalling 254.609 MiB; all fall inside the low 921 MiB RAM window. Seventeen match stock regions by base and size. The main exception is a fixed 70 MiB candidate carve-out at `0x8bf00000`, where stock's `cdsp_secure_heap` node has no `reg`.

Stock-only coverage absent from the candidate is 40.080 MiB (XBL log, splash/DFPS, rainbow/bootfail), plus dynamic pools including CMA. These are not automatically required: each must be tied to a consumer and first-boot/display scope.

**AI1 decision:** do not copy all stock reservations and do not add CMA merely for parity. Preserve the existing candidate layout during the RAM-only correction; make the 70 MiB CDSP carve-out and splash/CMA requirements explicit follow-up decisions before enabling their consumers. Confirm the 70 MiB region is physically safe and not allocated by an ABL/firmware handoff before first boot.

### 2.3 UFS supplies and GDSC

The six candidate UFS rail mappings resolve to the same RPMh resources as stock. The naming difference `pm8150l_s8` versus `pm8150a_s8` is not a resource mismatch: the candidate's PMIC ID resolves it to `smpc8`. L6's two host handles correspond to `vccq` and `qcom,vddp-ref-clk`; S8's stock UFS handle is 0/0 and is not an enabled voltage vote. L5/L9 are shared rails and cannot be attributed solely to UFS.

The candidate GCC GenPD GDSC and stock regulator node identify the **same hardware gate**: absolute register `0x177004`. Stock UFS holds a zero-voltage/zero-user regulator handle while the host is active. This is a software-framework observation, not physical proof that the gate is off.

WorkBuddy's full 13-node GDSC-to-ARC inventory does **not** include `ufs_phy_gdsc@0x177004`; its stock FDT node also has no parent-supply edge. Therefore the prior unknown about this GDSC needing one of the 13 stock ARC parents is closed by the ROUND152 evidence.

The candidate attaches the same UFS PHY GDSC GenPD to both the UFS host and PHY. The generic-PM-domain shared-consumer semantics and the exact pinned ACK call sequence still require the AI2 source review. Keep the current GenPD arrangement provisionally; do not add `vdd-hba-supply` on top of it, and do not remove GenPD only because stock's regulator framework says disabled.

### 2.4 OPP / MMCX ownership and ARC

The candidate currently has an RPMHPD MMCX consumer and **zero ARC provider groups**. Consequently there is no present dual-writer collision inside the frozen candidate. Adding a stock `mmcx.lvl` ARC provider independently would create a potential second writer to the same CMD-DB resource; do not add it until a single-owner/arbitration design is proven.

Stock HOS UFS is not shown as a direct MMCX ARC consumer. Candidate OPP/required-opps is therefore an upstream-native performance policy, not a proven byte-for-byte HOS equivalent. Retain it provisionally pending the AI2 source review and later live candidate validation.

### 2.5 Proxy lifecycle

The ROUND151 regulator summary was parsed completely: 322/322 lines accounted for, 82/82 providers satisfy `open == printed consumers`. No proxy-named consumer or unexplained extra open is visible. All eight live HOS `proxy-supply` declarations are confirmed, but no active proxy vote was visible at capture time. Whether proxy consumers were never created or were created and released earlier remains unknown.

**AI1 decision:** do not port or wire proxy-consumer support based only on declarations. Revisit only if source tracing or a differently-timed capture demonstrates a required live proxy lifecycle.

## 3. A separate board-ID / DTBO mismatch must be resolved

The candidate board DTS comment says DBY-W09 DTBO selection is by board ID `0x206a` (entry 8). ROUND151 reports the live boot `androidboot.dtbo_idx=2`, corresponding to entry 2 / board ID `0x200e`. ROUND138 found entry 2 and entry 8 have equivalent UFS/PMIC/regulator/RPMh payloads, but that does **not** prove every overlay payload is identical.

This mismatch is not corrected in this review. Before packaging, verify the exact selected overlay, all entry-2-vs-entry-8 differences, and whether the candidate's base-tree board ID influences ABL overlay selection or is only documentation. Do not infer that `dtbo_idx=2` is wrong or that the DTS comment is right.

## 4. ROUND153 implementation and verification sequence

1. **AI1 (this role):** create a minimal DTS change replacing only the zero-sized System RAM tuple with the three exact live-device tuples. Keep the 23-patch source base/tree identity pinned; record the exact patch diff and new tree SHA. Do not add ARC, proxy, CMA, splash or new GDSC supply changes in this patch.
2. **WorkBuddy Agent (local Agent 1):** read-only inspect any already-existing local stock firmware package/artifacts available in its own workspace for ABL, base DTB, DTBO image and boot-chain metadata. Resolve the `0x206a` comment vs live `dtbo_idx=2 / 0x200e` issue and identify any post-build packaging dependency. No device, no build, no partition access. If the firmware package is absent, report that fact without searching another Agent workspace.
3. **2号 Agent (local Agent 2):** independently re-open the frozen candidate DTB from its own permitted workspace, revalidate exact RAM and all 18 reserved intervals, and independently check the proposed three-tuple patch against the device-specific ROUND151 published RAM map. Do not use WorkBuddy's ROUND152 local workspace or claim its previous report as Agent 2's own. No device/build/write.
4. **2号 AI:** upload the missing ROUND152 architecture report to its already-assigned branch and verify the blob before any new AI2 assignment. This is a delivery correction, not a new review scope.
5. Only after steps 1–4 and review of the resulting patch may the project run the primary build and an independent reproducibility build. Compare exact source tree, `.config`, DTB, Image, BTF, signing certificate provenance and full logs. Do not compare Image SHA alone if generated certificate material is not pinned.
6. Boot packaging, AVB, full partition backup, and verified recovery path remain separate gates. No flash, reboot, fastboot, recovery, partition write, or candidate boot is authorized by this report.

## 5. Stop / authorization

- Candidate is still **not boot-ready** and first boot remains **not authorized**.
- No device operation was performed by AI1 in this review.
- Do not add a patch that makes a stock-specific assumption about other DBY-W09 memory variants.
- Next compile is justified only after the RAM patch, DTBO/board-ID resolution, independent review, and source-level UFS decision have been completed.

## 6. Source / evidence links

- Pinned ACK tag and commit: https://android.googlesource.com/kernel/common/%2B/refs/tags/android17-6.18.33_r00
- Candidate DTB / RAM / reserved-memory delta: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round152-candidate-stock-fdt-memory-reserved-ufs-delta/firmware-analysis/round152/AGENT2_ROUND152_CANDIDATE_DTB_STOCK_FDT_MEMORY_RESERVED_UFS_DELTA_REPORT.md
- ROUND151 live stock root runtime capture: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round151-root-readonly-runtime-audit/firmware-analysis/round151/WORKBUDDY_ROUND151_ROOT_READONLY_RUNTIME_AUDIT_REPORT.md
- ROUND151 independent review: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round151/AI1_ROUND151_INDEPENDENT_REVIEW_AND_ROUND152_PLAN.md
- ROUND152 regulator-summary review: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round152-existing-round151-proxy-summary-audit/firmware-analysis/round152/WORKBUDDY_ROUND152_EXISTING_REGULATOR_SUMMARY_PROXY_RUNTIME_REVIEW.md
- Expected but missing AI2 ROUND152 report: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round152-live-ufs-gdsc-genpd-arc-proxy-decision/firmware-analysis/round152/AI2_ROUND152_LIVE_UFS_GDSC_GENPD_ARC_PROXY_DECISION_REPORT.md
