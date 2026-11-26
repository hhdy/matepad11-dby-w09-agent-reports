# AI2 ROUND145 TASKBOOK — SM8250 RPMhPD descriptor-object identity and HOS4.3 ARC parent-chain review

## Identity / assignment

- **Assigned executor: 2号 AI (independent AI collaborator).**
- This is NOT a WorkBuddy Agent task and NOT a 2号 Agent task.
- 1号 AI remains the integration owner and will independently evaluate your report.
- Target: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1.
- Kernel: Android 17 ACK `android17-6.18.33_r00`.
- Immutable pinned commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.
- Candidate source tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.

## Purpose

Independently determine whether the current SM8250 RPMhPD descriptor graph represents the HOS4.3 UFS-related ARC parent-supply graph, and whether any apparent low-risk descriptor substitution would actually create a valid GenPD hierarchy.

This review is deliberately narrow and complementary to your ROUND143 ARM64/FDT memory handoff work. Do not repeat generic kernel boot analysis.

## Read these source and evidence items

1. 1号 AI preliminary finding:
   - [AI1 ROUND145 audit](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round145/AI1_ROUND145_RPMHPD_ARC_PARENT_DESCRIPTOR_COMPATIBILITY_AUDIT.md)
2. Exact pinned ACK:
   - `drivers/pmdomain/qcom/rpmhpd.c`
   - `drivers/pmdomain/core.c`
   - `drivers/opp/core.c`
   - `drivers/opp/of.c`
   - `drivers/base/power/common.c`
   - `arch/arm64/boot/dts/qcom/sm8250.dtsi`
3. Accepted HOS4.3 evidence:
   - [ROUND139 PMIC/UFS/ARC static audit](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md)
   - Focus on the ARC parent-edge inventory and the ACK/HOS comparison.

## Required independent questions

### A. Descriptor object identity

Read exact definitions and tables, not just domain names:
- `mmcx`
- `mmcx_w_cx_parent`
- `cx`
- `cx_w_mx_parent`
- `mx`
- `sm8250_rpmhpds[]`
- `sm8350_rpmhpds[]`
- `sm8450_rpmhpds[]`
- `sm8550_rpmhpds[]`

Determine:
1. Which exact `struct rpmhpd` object the SM8250 array selects for MMCX, CX and MX.
2. What exact object `mmcx_w_cx_parent.parent` points to.
3. Whether that pointed-to object is the same object selected at SM8250's CX index.
4. Whether a one-line substitution of `RPMHPD_MMCX = &mmcx_w_cx_parent` would build a valid parent link or point to an unselected/uninitialized GenPD object.
5. Explain why the SM8450 pairing is not automatically portable to SM8250.

### B. GenPD and OPP state propagation

Verify from source:
- `rpmhpd_probe()` initializes only the objects in the selected SoC table and adds parent/subdomain links.
- `of_genpd_add_provider_onecell()` OPP table loading.
- `_of_add_table_indexed()` single-phandle reuse behavior.
- `dev_pm_opp_xlate_performance_state()` behavior when no required-OPP table exists.
- `_genpd_set_performance_state()` scaling-up/down parent propagation.
- `rpmhpd_update_level_mapping()` CMD-DB address, slave ID, and AUX level mapping.

Determine whether a valid parent relation would pass a common logical OPP level one-to-one in this SM8250 DTS/provider design, or whether a separate parent required-OPP map is needed. Cite exact functions and lines.

### C. HOS4.3 ARC graph semantics

From ROUND139, assess:
- MMCX ALL → MX MMCX-supply ALL.
- MX MMCX-supply → CX MMCX-supply.
- MMCX AO → MX AO.
- separate CX ALL/AO → MX ALL/AO.
- Distinguish regulator child parent-supply links from electrical input parents and consumer-side dependencies.

State what the HOS4.3 static evidence proves and what it does not prove about runtime regulator enable/disable, resource mapping, and physical PMIC inputs.

### D. Candidate hierarchy options

Evaluate, do not implement:
1. Keep current SM8250 mapping `MMCX=&mmcx`.
2. Swap only to `mmcx_w_cx_parent`.
3. Copy the SM8450 pair.
4. Build a custom hierarchy that could represent MMCX → MX → CX.
5. Any alternative supported by the actual source.

For each, classify:
- source-valid / invalid / incomplete;
- resource-name correspondence;
- GenPD object identity correctness;
- fit to HOS4.3 child-supply graph;
- evidence still missing.

Do not claim any option is hardware-correct without proof. Do not infer equivalence from string names, OPP levels, or one matching SoC.

## Deliverable

Upload one Markdown report to this branch:

`agent2/round145-rpmhpd-arc-parent-review`

Required path:
`firmware-analysis/round145/AI2_ROUND145_RPMHPD_ARC_PARENT_REVIEW.md`

The report must contain:
- scope and exact pinned commit;
- immutable source file links and line references;
- descriptor-object graph diagram/table;
- source-proven facts vs engineering inferences vs unknowns;
- option comparison matrix;
- a clear disposition: safe to patch / needs more evidence / no safe patch;
- questions that 1号 AI must resolve before changing DTS or RPMhPD.

## Restrictions

- Static source/evidence review only.
- Do NOT connect to the tablet or request ADB, fastboot, recovery, UART, reboot, partitions, or root.
- Do NOT read any private ROUND140/ROUND142 Agent workspace.
- Do NOT run builds or tests.
- Do NOT modify ACK source, DTS, patches, or the candidate branch.
- Do NOT invent CMD-DB resource names or board voltage values.
- Do NOT call a regulator `enabled` merely because its DT `status` property is absent.
- Do NOT change the user's pinned ACK commit or candidate tree.
- Do NOT modify or overwrite 1号 AI's report.

Upload the report to the designated branch, read it back to verify the exact uploaded content, and stop.