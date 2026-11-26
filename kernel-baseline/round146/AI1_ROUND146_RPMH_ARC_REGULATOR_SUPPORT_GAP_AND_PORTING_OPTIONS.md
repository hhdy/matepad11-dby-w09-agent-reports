# AI1 ROUND146 — HOS4.3 RPMh ARC regulator model vs pinned ACK 6.18.33 support gap

- Author: **1号 AI (ChatGPT)**
- Date: 2026-11-26
- Device: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Kernel target: Android 17 ACK android17-6.18.33_r00
- Immutable ACK commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- Candidate tree: afe9517f8062b96bfeb5b4dd5714942861e6a44b
- Inputs: accepted HOS4.3 ROUND139 inventory, accepted ROUND140 candidate report, pinned ACK, public generic Qualcomm RPMh ARC reference from OnePlus SM8475 commit 7278ce9a3c8539b4630d6988cc80f90c31c07336.
- Scope: static source audit only. No source/DTS/config changes, no build, no device access, no local Agent workspace access.

## 1. Disposition

**CONFIRMED SOURCE GAP:** HOS4.3 v2.1 FDT contains seven ARC provider groups with compatible string "qcom,rpmh-arc-regulator", including mmcxlvl, mxlvl, and cxlvl. The pinned ACK drivers/regulator/qcom-rpmh-regulator.c implements only two RPMh regulator types — VRM and XOB — and its OF match table covers per-PMIC qcom,*-rpmh-regulators groups. It has no ARC type and no qcom,rpmh-arc-regulator match. ROUND139's corpus comparison also found zero ACK hits for the HOS ARC compatible.

**ARCHITECTURAL IMPLICATION:** HOS ARC child parent-supply edges are regulator-framework supply dependencies, not merely aliases for generic power-domain parent pointers. A Qualcomm ARC regulator implementation can register individual child ARC regulators, map each child regulator's parent-supply property to regulator_desc.supply_name, and let regulator core recursively enable/disable the parent. The pinned ACK regulator core already has nested child-regulator lookup and recursive supply handling, but the pinned ACK RPMh regulator driver does not register ARC child regulator devices.

**NO IMMEDIATE PATCH IS SAFE:** The public Qualcomm implementation reviewed here is a generic reference from another device/kernel, not exact Huawei HOS4.3 source. It establishes a plausible model, not the precise HOS binary behavior. A direct copy/backport is not justified without API adaptation and board-specific reconciliation. The candidate GenPD UFS OPP patch may provide a partial UFS performance vote, but it has not been proven equivalent to the full HOS ARC provider-child graph.

First device boot remains **BLOCKED / NOT AUTHORIZED**.

## 2. HOS4.3 facts established by ROUND139

ROUND139 establishes seven groups among the 47 rpmh-regulator-* groups that use compatible "qcom,rpmh-arc-regulator":
- mxlvl → resource mx.lvl
- cxlvl → resource cx.lvl
- mmcxlvl → resource mmcx.lvl
- lmx.lvl, lcx.lvl, gfx.lvl and ebi.lvl

It establishes five ARC child regulator parent-supply edges:

| Provider group / child | DT property | Resolved parent child | Meaning |
|---|---|---|---|
| cxlvl | pm8150_s3_level-parent-supply | mxlvl / regulator-pm8150a-s3-level | CX ALL → MX ALL |
| cxlvl | pm8150_s3_level_ao-parent-supply | mxlvl / regulator-pm8150a-s3-level-ao | CX AO → MX AO |
| mmcxlvl | pm8150a_s4_level-parent-supply | mxlvl / regulator-pm8150a-s3-mmcx-sup-level | MMCX ALL → MX MMCX-supply ALL |
| mmcxlvl | pm8150a_s4_level_ao-parent-supply | mxlvl / regulator-pm8150a-s3-level-ao | MMCX AO → MX AO |
| mxlvl | pm8150a_s3_mmcx_sup_level-parent-supply | cxlvl / regulator-pm8150-s3-mmcx-sup-level | MX MMCX-supply → CX MMCX-supply |

These are provider-child ARC regulator dependencies. They are not physical PMIC input parents of the six UFS rails and do not establish the missing L5/L6/L9/L17/S4/S8 VIN topology.

ROUND139 also finds the HOS UFS node has no power-domains or OPP link and uses legacy qcom,msm-bus. The ARC graph exists independently from the UFS direct consumer declarations.

Sources:
- [ROUND139 ARC provider-child edge inventory](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md#L137-L167)
- [ROUND139 complete HOS ARC groups and ACK coverage census](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md#L177-L200)

## 3. Pinned ACK driver coverage

The exact pinned ACK source blobs:
- drivers/regulator/qcom-rpmh-regulator.c — 109f0aae09b1df431d2e14d45a64d115e87cdec4
- drivers/regulator/of_regulator.c — 32e88cada47a254c3b184f3d1d6d8c1dccdfcc28
- drivers/regulator/core.c — 39d317ad73a33c4aa27e179cc436d8bf4daf5bcc

### 3.1 RPMh regulator type support is VRM/XOB only

At qcom-rpmh-regulator.c lines 24–30, the enum contains only VRM and XOB. There is no ARC variant. Its match table includes per-PMIC groups such as qcom,pm8150-rpmh-regulators and qcom,pm8150l-rpmh-regulators. It does not include qcom,rpmh-arc-regulator.

The Kconfig symbol REGULATOR_QCOM_RPMH builds qcom-rpmh-regulator.o; enabling it does not silently add the older ARC aggregator.

Immutable source:
- [Pinned ACK RPMh regulator enum](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c#L20-L34)
- [Pinned ACK RPMh regulator match table](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c#L1640-L1752)
- [Kconfig option](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/Kconfig#L1124-L1134)
- [Makefile object mapping](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/Makefile#L118-L126)

### 3.2 The regulator core supports nested child-supply dependencies

Pinned ACK of_regulator.c lines 571–640 contains of_get_child_regulator(), which recursively traverses a provider node's child hierarchy looking for the requested supply phandle. of_get_regulator() first checks the consumer node, then searches the provider's nested child nodes.

Pinned ACK core.c lines 1975–2140 resolves the supplier regulator, checks provider binding, recursively resolves the supplier's own parent and establishes the supply relationship.

Pinned ACK core.c lines 2898–3060 recursively enables the parent supply before enabling the child, and releases the parent supply when the child's final consumer disables it.

Thus, the generic regulator framework plumbing for nested ARC child-supply dependencies exists in pinned ACK. The missing component is an ARC regulator producer driver that registers each ARC resource and assigns each child regulator's parent-supply relationship.

Immutable source:
- [Nested child regulator lookup](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/of_regulator.c#L571-L640)
- [Supply resolution and recursive parent lookup](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L1975-L2140)
- [Recursive regulator enable/disable](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L2898-L3060)

## 4. Public Qualcomm ARC implementation reference

This audit reviewed a public Qualcomm vendor RPMh ARC regulator implementation:
- Repository: OnePlusOSS/android_kernel_oneplus_sm8475
- Commit: 7278ce9a3c8539b4630d6988cc80f90c31c07336
- File: drivers/regulator/rpmh-regulator.c

This is a generic Qualcomm implementation reference from a different target, **not** proof that this is the exact Huawei HOS4.3 source or binary.

The reference driver:
1. Defines three RPMh regulator types: VRM, ARC and XOB.
2. Binds qcom,rpmh-arc-regulator in its OF match table.
3. Reads qcom,resource-name, resolves CMD-DB address and slave ID, validates CMD_DB_HW_ARC, and reads each resource's ARC hardware-level to consumer-level mapping from CMD-DB AUX data.
4. Enumerates each child regulator node and registers a regulator-framework device for that child.
5. Provides ARC operations to set/list/get a child ARC level and aggregate child requests over active and sleep sets.
6. In rpmh_regulator_init_vreg_supply(), constructs <regulator-name>-parent-supply. If present on the aggregate provider or child node, it sets regulator_desc.supply_name to <regulator-name>-parent. Otherwise, optional vin-supply maps to vin.
7. Registers each child regulator using devm_regulator_register(), then registers a proxy consumer. Regulator core resolves the nested parent-supply relationship.

Reference source:
- [Qualcomm vendor ARC types and structures](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/rpmh-regulator.c#L20-L75)
- [ARC operations and CMD-DB AUX mapping](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/rpmh-regulator.c#L1153-L1316)
- [ARC parent-supply setup and child regulator registration](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/rpmh-regulator.c#L1645-L1830)
- [ARC match and aggregate probe](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/rpmh-regulator.c#L1835-L1990)

This provides a plausible explanation of the HOS FDT model: MMCX ALL child may acquire MX MMCX-supply ALL as its parent, and that MX child may acquire CX MMCX-supply as its parent. But the external code is not HOS-specific. Exact HOS driver revision, patches and runtime behavior remain unverified.

## 5. Relationship to ROUND144 / ROUND145 GenPD findings

The candidate design:
- attaches UFS to RPMHPD_MMCX and GCC UFS_PHY_GDSC;
- maps the one UFS required-opps slot to attached MMCX domain device at index 0;
- has correct required_dev_index=0 according to ROUND144 and pinned ACK OPP API;
- selects plain MMCX descriptor with no parent in SM8250;
- uses CX descriptor whose parent points to MX;
- cannot safely fix that with a one-line descriptor substitution because the existing mmcx_w_cx_parent points to the distinct plain cx object, not the selected cx_w_mx_parent object (ROUND145).

Broader implication:

**GenPD parent-state propagation and ARC regulator child-supply recursion are different mechanisms.** GenPD propagates a performance state through registered power-domain objects and OPP state mapping. The vendor ARC driver registers separately named child regulator devices, maintains per-child requests and active/sleep votes, resolves nested supplies, and sends resource-specific CMD-DB level votes. A GenPD parent pointer does not create those child regulator devices or their regulator-core enable dependencies.

A restricted GenPD implementation may eventually be proven equivalent for the exact UFS consumer set, but this has not been established. In particular, the vendor MMCX → MX MMCX-supply → CX MMCX-supply chain is not proven equivalent to coarse MMCX → CX GenPD hierarchy.

Sources:
- [ROUND144 UFS OPP mapping / probe-order audit](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round144/AI1_ROUND144_UFS_OPP_REQUIRED_DEVICE_AND_PROBE_ORDER_AUDIT.md)
- [ROUND145 RPMhPD descriptor identity audit](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round145/AI1_ROUND145_RPMHPD_ARC_PARENT_DESCRIPTOR_COMPATIBILITY_AUDIT.md)

## 6. Candidate DTB evidence boundary

ROUND140 independently confirms the compiled candidate DTB has UFS host attached to RPMHPD_MMCX and UFS_PHY_GDSC, two UFS OPP entries with required-opps to the RPMhPD table, two ICC paths, per-PMIC regulators for UFS L5/L6/L9/L17/S4, a candidate VDDP REF_CLK consumer, and no candidate consumer for qcom,vccq-parent-supply to PM8150L S8.

However, the published ROUND140 report does not provide a full compiled-candidate-DTB census of all qcom,rpmh-arc-regulator nodes or their children. This audit does **not** claim that the compiled candidate DTB definitely contains or omits those compatible nodes.

The source support conclusion is:
- if a candidate DTB contains HOS-compatible ARC provider nodes, pinned ACK has no matching driver;
- if those nodes are omitted, the candidate is replacing the HOS ARC provider model and must prove that its alternative expresses all required dependency and vote behavior.

The exact ARC-node inventory in the compiled candidate DTB is a narrow read-only check for the owner of the ROUND140 output workspace. Other agents must not inspect that private workspace.

Sources:
- [ROUND140 candidate DTB UFS provider/OPP/ICC review](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round140-independent-preboot-tests/firmware-analysis/round140/round140-agent2-independent-build-and-preboot-test-report.md#L246-L276)
- [ROUND140 candidate UFS supply consumer matrix](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round140-independent-preboot-tests/firmware-analysis/round140/round140-agent2-independent-build-and-preboot-test-report.md#L340-L381)

## 7. Implementation path comparison

| Option | Assessment | Coverage / missing evidence |
|---|---|---|
| Keep current ACK regulator model + UFS GenPD OPP mapping | Valid ACK design, vendor equivalence incomplete | UFS MMCX OPP vote and PMIC UFS rails; does not reproduce five HOS ARC child-supply edges, runtime votes unproven |
| Add only MMCX→CX/MX GenPD parent | Incomplete; one-line substitution is object-identity unsafe | Coarse parent state only; no ARC child regulators, per-child request aggregation or nested regulator supplies |
| Port/adapt Qualcomm aggregate ARC regulator implementation to ACK 6.18.33 | Closest source-level match to HOS compatible and child-supply model | Must adapt modern regulator/proxy APIs, verify PMIC/ARC mappings, active/sleep sets, resource AUX data and error handling; avoid duplicate votes with GenPD |
| Hybrid: keep GenPD for UFS OPP and separately add ARC regulator providers | Possible but not established | Must define ownership of mmcx.lvl and avoid duplicate/conflicting requests |
| Model the graph as custom GenPD domains only | Not preferred absent stronger proof | Does not inherently reproduce ARC child regulator devices and regulator-framework dependencies |

## 8. Recommended disposition

1. Keep required_dev_index=0; ROUND144 confirmed it.
2. Do not make a one-line MMCX descriptor substitution; ROUND145 established the object-identity mismatch.
3. Do not claim the HOS ARC child-supply graph is represented by the current UFS GenPD design.
4. Ask the 2号 Agent to inventory ARC nodes and child supply edges in its own existing ROUND140 compiled DTB artifact only; no rebuild or network access.
5. If exact HOS4.3 ARC driver provenance is already present among accessible firmware or existing evidence, compare it; do not restart the known private implementation search.
6. Before selecting ARC driver port vs GenPD replacement, prove resource names, CMD-DB AUX maps, child aggregation, active/sleep behavior, proxy consumers, parent supply ordering and ownership of UFS's MMCX vote.
7. Keep physical PMIC inputs, final ABL FDT/RAM/reservations, ICC runtime votes, boot-v2/ramdisk/DTBO, AVB and tested recovery gates open.

## 9. Final status

- ACK ARC driver support: **ABSENT — source-confirmed**
- HOS4.3 ARC provider-child graph: **PRESENT — ROUND139 static evidence**
- Generic Qualcomm ARC driver reference: **FOUND — not HOS-specific proof**
- ACK regulator-core nested supply plumbing: **PRESENT — source-confirmed**
- Candidate compiled DTB ARC-node inventory: **NOT PUBLISHED / UNVERIFIED**
- Safe complete MMCX parent-chain implementation: **NOT ESTABLISHED**
- First device boot: **BLOCKED / NOT AUTHORIZED**

No source or DTS was changed. No build or device operation was performed.
