# AI1 ROUND152 Supplement — Review of AI2 UFS / GenPD / ARC / Proxy Architecture Report

- Reviewer: **1号 AI (ChatGPT)**
- AI2 report: `firmware-analysis/round152/AI2_ROUND152_LIVE_UFS_GDSC_GENPD_ARC_PROXY_DECISION_REPORT.md`
- AI2 report blob SHA: `3145dc115cb8925e860c239ab573fbd10ccd3ee3`
- AI2 report readback: complete; 41,831 characters.
- Candidate: ACK `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`, candidate tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
- Review date: 2026-11-26.
- Disposition: **AI2 source-trace work accepted as a useful independent review; candidate remains frozen; no first boot authorization.**

## 1. AI2 report review

The AI2 report correctly traces the fixed ACK UFS HBA regulator path:

- Without `vdd-hba-supply`, ACK leaves the UFS HBA regulator pointer NULL; obtaining/enabling/disabling that optional regulator is a no-op. The candidate's missing `vdd-hba-supply` is therefore not by itself a generic ACK UFS probe failure.
- With a populated regulator, fixed ACK obtains and enables it during HBA initialization, with unwind/exit and selected low-power transitions disabling it.
- The candidate's UFS host and PHY GenPD references resolve to the same GCC `ufs_phy_gdsc` domain object, not two duplicate GDSC providers. The host has multiple attached power-domain virtual devices, and the PHY is a separate member/client. Generic PM-domain shared membership does not by itself establish that the full host/PHY runtime-PM sequencing is correct for this board.
- The active HOS UFS host alongside a disabled/zero-user `vdd-hba` regulator handle remains unexplained. AI2 correctly avoids treating regulator-framework state as a physical gate measurement.
- The candidate OPP/required-opps + RPMhPD + ICC path is an upstream-native possible replacement for some legacy vendor performance path, but is not a demonstrated equivalent of HOS's 26-case/two-path `qcom,msm-bus` vectors. The candidate does include ICC paths; the unverified part is numerical/topological equivalence and the added MMCX request.
- HOS does not prove UFS itself is an MMCX ARC consumer. Candidate RPMHPD MMCX and a future ARC `mmcxlvl` provider must not become independent writers to `mmcx.lvl`.
- The report correctly keeps the candidate frozen, avoids adding ARC/proxy or changing GDSC/OPP, and says no compile is justified until the architecture is resolved.

These conclusions are accepted with the evidence boundaries and open items in the AI2 report. In particular, AI2 has not proven that GenPD is necessary for first boot, that the candidate arrangement is equivalent to HOS, or that the current UFS OPP levels are correct for this hardware.

## 2. Reconciliation with the WorkBuddy ROUND152 runtime-summary review

AI2's report was scoped to the reports and fixed ACK source available to that independent reviewer; it did not consume WorkBuddy's subsequently published sanitized re-analysis of the existing ROUND151 local `regulator_summary`. The two reports therefore have different evidence cutoffs, not contradictory raw measurements.

The newer WorkBuddy ROUND152 review:
- parsed all 322 lines (header and data) of the already-captured summary, with 320 data rows and no unparsed lines;
- found 82/82 regulator providers satisfy `open == printed consumer entries`;
- found no explicit proxy consumer handle or unexplained extra open at the capture instant;
- mapped all eight `proxy-supply` sites in the live FDT;
- found the two fully declared negative sites (L14 and MDSS core GDSC) disabled with zero users;
- still cannot distinguish a proxy consumer never created from one created and released before the snapshot; proxy creation/teardown timing remains UNKNOWN.

Thus the merged evidence is: **no active proxy handle is observable at the captured instant; lifecycle history and Huawei 4.19 sync-state/late-init behavior remain unknown.** This does not authorize importing the OnePlus SM8475 implementation as if it were Huawei's exact source.

Source report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round152-existing-round151-proxy-summary-audit/firmware-analysis/round152/WORKBUDDY_ROUND152_EXISTING_REGULATOR_SUMMARY_PROXY_RUNTIME_REVIEW.md

## 3. Corrected proxy declaration counts

AI2 §5.1 repeats an older count of **10** `qcom,proxy-consumer-enable` declarations. The full-file WorkBuddy ROUND152 census reports **8**, matching the eight `proxy-supply` sites/targets:

| Property | Adopted count | Evidence |
|---|---:|---|
| `proxy-supply` | 8 | Full merged-FDT census, WorkBuddy ROUND152 |
| `qcom,proxy-consumer-enable` | **8** | Full merged-FDT census, WorkBuddy ROUND152 |
| `qcom,proxy-consumer-current` | 4 | Full merged-FDT census, WorkBuddy ROUND152 |
| `qcom,proxy-consumer-voltage` | 2 | Full merged-FDT census, WorkBuddy ROUND152 |
| `qcom,proxy-consumer-name` | 0 | Full merged-FDT census, WorkBuddy ROUND152 |

Use these updated counts in future work. The enable count in AI2 §5.1 should be treated as stale. The WorkBuddy report also corrects the declaration shape: six provider-to-own-child references and two genuine self-references, not ten distinct sites.

## 4. UFS GDSC / ARC ownership conclusion

The WorkBuddy ROUND152 report enumerates all 13 stock GDSC-to-ARC consumers. The list does **not** include `ufs_phy_gdsc@0x177004`. Its stock FDT node also has no parent-supply edge. Therefore the specific ROUND152 question "is the UFS PHY GDSC one of the thirteen GDSCs requiring an ARC parent?" is answered **NO on the published live FDT evidence**.

This closes that particular parent-edge uncertainty. It does **not** settle the separate behavioral question of why the HOS UFS `vdd-hba` handle is never enabled, whether the hardware gate needs explicit GenPD control, or whether candidate GenPD runtime sequencing is correct.

The conditional shared-resource warning remains:
- candidate currently has RPMHPD MMCX writing `mmcx.lvl`;
- current candidate DTB inventory has zero ARC providers;
- if ARC `mmcxlvl` is added as an independent writer, the same CMD-DB resource can be updated by two independent aggregators;
- no such dual-writer collision has been observed in the current candidate artefact because the ARC writer is absent.

## 5. Integrated ROUND152 decision

| Area | Integrated disposition |
|---|---|
| UFS HBA regulator | ACK permits absent optional supply; this alone does not prove candidate power correctness |
| UFS PHY GDSC | same hardware gate at `0x177004`; stock 13-edge ARC list does not include it; runtime behavior still unproven |
| Host + PHY GenPD | one shared GenPD provider with multiple clients; PM/runtime sequencing requires care |
| HOS devfreq/msm-bus vs candidate OPP/ICC/RPMhPD | plausible upstream-native replacement, not HOS-equivalent; mapping and MMCX vote need evidence |
| `mmcx.lvl` | enforce one writer only; do not add ARC MMCX beside RPMHPD MMCX |
| Proxy | 8 declarations; no active proxy handle visible in the existing capture; lifecycle timing unknown |
| Compile | not justified before separate RAM/DTBO/boot-chain gates and architecture decision |
| First boot | BLOCKED / NOT AUTHORIZED |

## 6. ROUND153 dependencies after AI2 completion

AI2's ROUND152 task is now complete. The remaining ROUND153 work is:

1. **WorkBuddy Agent (local Agent 1):** read-only inventory of its own existing stock firmware/boot-chain artifacts; compare the entire DTBO Entry 2 and Entry 8 payloads; investigate ABL memory fixup only if an actual artifact exists. No device, no build, no writes.
2. **2号 Agent (local Agent 2):** perform a genuinely independent revalidation in its own workspace of the frozen DTB identity, three live-device RAM windows and all reserved-memory ranges. ROUND152's DTB report disclosed execution by the WorkBuddy-side agent, so it must not be counted as independent Agent 2 verification.
3. **AI1:** after those deliverables, decide and implement the minimum RAM-only DTS change if the exact single-device evidence and boot-chain review support it. Do not mix in ARC, proxy, CMA, display reservations or speculative UFS changes.
4. **Formal builds:** only after the source diff and DTBO/board-ID decisions are reviewed, perform one primary build and one truly independent reproduction. Compare tree/config/DTB/Image/BTF and signing-certificate provenance; do not treat Image SHA alone as a definitive equality gate when generated certificate material differs.
5. **Boot safety:** packaging/AVB, complete partition backup and a verified recovery path remain required, followed by the user's explicit authorization for any first candidate boot.

No source, DTS, patch, DTBO, config, build, device or partition operation was performed by this review.

## 7. References

- AI2 ROUND152 architecture decision:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round152-live-ufs-gdsc-genpd-arc-proxy-decision/firmware-analysis/round152/AI2_ROUND152_LIVE_UFS_GDSC_GENPD_ARC_PROXY_DECISION_REPORT.md
- WorkBuddy ROUND152 runtime-summary/proxy review:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round152-existing-round151-proxy-summary-audit/firmware-analysis/round152/WORKBUDDY_ROUND152_EXISTING_REGULATOR_SUMMARY_PROXY_RUNTIME_REVIEW.md
- Candidate DTB / RAM / reserved-memory / UFS delta:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round152-candidate-stock-fdt-memory-reserved-ufs-delta/firmware-analysis/round152/AGENT2_ROUND152_CANDIDATE_DTB_STOCK_FDT_MEMORY_RESERVED_UFS_DELTA_REPORT.md
- AI1 ROUND152 delivery review and ROUND153 decision:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round152/AI1_ROUND152_DELIVERY_REVIEW_AND_ROUND153_DECISION.md

— END OF AI1 ROUND152 AI2-REVIEW SUPPLEMENT —
