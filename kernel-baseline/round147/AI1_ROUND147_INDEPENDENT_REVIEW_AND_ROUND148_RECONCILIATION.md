# AI1 ROUND147 independent review and ROUND148 reconciliation

- Reviewer: 1号 AI (ChatGPT)
- Date: 2026-11-26
- Target: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Fixed ACK: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`
- Candidate content tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- Reviewed report: `firmware-analysis/round147/AGENT2_ROUND147_CANDIDATE_DTB_ARC_NODE_INVENTORY.md`
- Reviewed ROUND147 report blob: `ed4726832fa9d1b97fd9db6ec7ea2e1b10895e6b`
- Companion analysis: AI2 ROUND148 `firmware-analysis/round148/AI2_ROUND148_ARC_REGULATOR_AND_PROXY_CONSUMER_PORTABILITY_AUDIT.md`, blob `2379a7dda2a40a86328f52ebb3a55c66aec743e4`

## 1. Review verdict

**ROUND147 evidence is accepted for the narrow compiled-candidate-DTB inventory.** The report identifies the exact existing ROUND140 DTB, verifies size and SHA-256, reconciles its parser against independent text and binary representations, and cross-checks zero ARC matches with three instruments.

Artifact identity is:

- Size: 108648 bytes.
- SHA-256: `cab82fe3901dbb40533197eb48b2d99b08b46e5d5497ff1a6f688e9938db77e`.
- Path is the existing ROUND140 Agent2 output; no rebuild was performed.

The two-character transcription error in ROUND140's recorded expected hash is separately understood; the build-produced value and the existing file both match the correct hash above.

## 2. Findings accepted from ROUND147

1. The compiled candidate DTB contains **zero** `qcom,rpmh-arc-regulator` nodes.
2. It contains zero `rpmh-regulator-*` group nodes, zero `qcom,resource-name`, zero ARC resource strings (`mmcx.lvl`, `mx.lvl`, `cx.lvl`), zero `proxy-supply` and zero `qcom,proxy-consumer-enable`.
3. It has two per-PMIC VRM provider groups:
   - PM8150: 5 rails (L5, L6, L9, L17, S4);
   - PM8150L: 1 rail (S8).
   Neither group has a phandle.
4. It has seven typed `*-supply` edges, all associated with UFS host/PHY:
   - UFS host: vcc→L17; vccq→L6; qcom,vddp-ref-clk→L6; vccq2→S4; qcom,vccq-parent→S8.
   - UFS PHY: vdda-phy→L5; vdda-pll→L9.
5. `vin-supply` count is zero. The only `*-parent-supply` is the UFS consumer property `qcom,vccq-parent-supply`; this is not one of the HOS ARC provider-child dependencies.
6. UFS host uses:
   - RPMhPD MMCX domain (domain 6);
   - GCC UFS PHY GDSC (domain 4);
   - two OPP entries with `required-opps` to RPMhPD OPP levels 64 and 256.
7. The candidate board DTS documents the omission as intentional: use ACK RPMhPD/OPP model for this board file and do not introduce vendor ARC nodes until an ARC-capable driver is deliberately ported and reviewed.

Terminology: node status absent means available under standard OF default semantics. It does **not** prove regulator probe, enable vote, voltage, a valid physical input or measured rail state.

## 3. Reconciliation with AI2 ROUND148 — important correction

ROUND148 raised a conditional shared-resource ownership conflict:

- HOS4.3 ARC `mmcxlvl` uses CMD-DB resource `mmcx.lvl`.
- Pinned SM8250 RPMhPD MMCX also uses `mmcx.lvl`.
- The independent ARC and GenPD aggregators are not shown to share a Linux max-vote arbitration layer; two independent writers would therefore be unsafe without a single-owner arbitration design.

ROUND147 now supplies the missing compiled-DTB census. **The current ROUND140 candidate DTB contains no ARC provider**, so there is no evidence that the current compiled candidate instantiates both ARC MMCX and GenPD MMCX. The ROUND148 collision is therefore a **future design constraint if ARC is added**, not a demonstrated active collision in the current candidate artifact.

This does not prove that the existing GenPD-only UFS performance model is equivalent to HOS4.3. It only establishes that the present DTB has selected one owner path (RPMhPD/GenPD) for the UFS OPP corner request, with no ARC node in that artifact.

The stale ROUND148 statement that the candidate DTB ARC inventory was not published is now superseded by ROUND147. Update it in any later synthesis rather than continuing to describe the candidate ARC count as unknown.

## 4. What remains unresolved

ROUND147 is static DTB evidence only. It does not establish:

- whether GenPD/OPP alone meets the actual device's UFS performance and sequencing requirements;
- runtime RPMh votes or the actual active/sleep/wake corner;
- provider probe success or regulator enable state;
- physical PMIC input parents and actual voltage rails;
- whether HOS4.3's five ARC child-supply edges and other ARC consumers are required for this device's full boot;
- exact Huawei HOS4.3 ARC driver source / behavior;
- resource-specific CMD-DB AUX map bytes for the seven HOS ARC resources;
- proxy-consumer property matrix and correct `sync_state` / legacy cleanup timing;
- final post-ABL FDT/RAM map, selected DTBO identity, boot-v2 / ramdisk policy, AVB and tested recovery.

The HOS vendor graph and candidate graph remain structurally different. Neither the existence of a generic Qualcomm ARC reference nor a successful kernel build is sufficient evidence to copy its numeric AUX map or enable it in the candidate.

## 5. Decision and next actions

1. **Do not add ARC nodes to the current DTS yet.** The present omission is explicit and the correct ARC semantics / exact HOS AUX data remain unproven.
2. Preserve the current compiled candidate as the existing reproducible build baseline. Do not silently mutate its 23-patch tree or its reported Tree SHA.
3. Keep GenPD as the sole MMCX owner in the existing candidate unless a reviewed single-owner arbitration design deliberately replaces it.
4. Before any ARC integration, obtain:
   - authoritative HOS4.3 driver provenance or an explicitly labelled generic-reference adaptation plan;
   - exact resource-specific CMD-DB AUX records and format/version;
   - full proxy site-to-supply mapping and lifecycle evidence;
   - a complete resource-ownership table proving no duplicate CMD-DB writer.
5. Use the newly authorized ROUND149 ADB read-only runtime collection to compare actual HOS4.3 UFS, regulators, RPMh, power domains and logs. If current stock FDT is readable under ordinary shell permission, correlate its exact nodes and properties; do not escalate on denial.
6. After that evidence is reviewed, make one consolidated driver/DTS design decision and only then prepare the next integrated candidate build.

## 6. First-boot disposition

**First device boot remains BLOCKED / NOT AUTHORIZED.** ROUND147 closes only the candidate compiled-DTB ARC inventory gap. It does not close FDT/RAM, PMIC physical input, runtime UFS/RPMh, boot-chain, AVB or recovery gates.

No source, DTS, configuration, patch or binary was changed by this review. No device operation was performed by 1号 AI.

## 7. ROUND147 delivery process note

The ROUND147 executor reported that the taskbook had occupied the eventual report path and that the report replaced it. The taskbook remains retrievable from the pre-report branch commit referenced by the Agent. For subsequent rounds, keep taskbook, start prompt and report in distinct path names so the task definition is not displaced by its deliverable.

— END OF AI1 ROUND147 REVIEW —
