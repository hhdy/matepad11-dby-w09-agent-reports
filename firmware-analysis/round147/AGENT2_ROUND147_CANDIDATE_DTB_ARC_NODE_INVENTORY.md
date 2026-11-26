# ROUND147 Taskbook — 2号 Agent read-only inventory of existing ROUND140 candidate DTB ARC providers

## Assignment identity

- **Assigned executor: 2号 Agent**, the local agent that created the ROUND140 independent build artifacts.
- This is NOT 2号 AI and NOT WorkBuddy Agent.
- The 2号 Agent must inspect only its own existing ROUND140 workspace.
- 1号 AI owns review and integration of the result.

## Goal

ROUND139 establishes that the HOS4.3 vendor FDT contains seven qcom,rpmh-arc-regulator groups and five provider-child ARC parent-supply edges. ROUND146 establishes that the pinned ACK RPMh regulator driver has no qcom,rpmh-arc-regulator match and only VRM/XOB types.

The ROUND140 report does not enumerate every ARC-compatible node in the compiled candidate DTB. This round closes only that narrow evidence gap by inspecting the already-built candidate DTB from ROUND140.

## Exact existing workspace

Use only the 2号 Agent's own pre-existing files:
- Candidate source tree: /home/kerneldev/work/matepad11/round140-agent2/tree
- Existing logs: /home/kerneldev/work/matepad11/round140-agent2/logs
- Existing Kleaf output: /home/kerneldev/work/matepad11/round140-agent2/a30build
- Existing DTB output: /home/kerneldev/work/matepad11/round140-agent2/out-dtb

Do not use another agent's files. Do not let another agent inspect this workspace.

## Candidate artifact identity

The ROUND140 report states that its candidate DTB is:
- File: qcom/huawei-dby-w09.dtb under the existing out-dtb output
- Size: 108648 bytes
- SHA256: cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e

Verify that the exact existing file still has this size and SHA before inspecting it. If the exact path differs, identify the file using the existing ROUND140 log only. Do not rebuild or regenerate the DTB.

## Required read-only checks

1. Identify the exact existing DTB path; record size, SHA256, mtime if available, and its matching ROUND140 build/log provenance.
2. Decompile the existing DTB to DTS text using a read-only inspection operation. Writing a temporary text dump to a new temporary file is allowed; do not overwrite the existing DTB, source DTS, or build products.
3. Count all nodes with compatible = "qcom,rpmh-arc-regulator".
4. For each such group, record:
   - full node path;
   - status property, including explicit status or absent;
   - qcom,resource-name;
   - all available child regulator-name values;
   - every child-specific or aggregate-level *-parent-supply property and its resolved phandle target/path;
   - all qcom,proxy-consumer-enable and proxy-supply occurrences, if any.
5. Count nodes with compatible = "qcom,pm8150-rpmh-regulators" and "qcom,pm8150l-rpmh-regulators"; record each node path, status, PMIC ID, child regulator names and status.
6. Search the entire decompiled candidate DTB for:
   - mmcx.lvl, mx.lvl, cx.lvl resource strings;
   - rpmh-regulator-mmcxlvl, rpmh-regulator-mxlvl and rpmh-regulator-cxlvl node names;
   - qcom,rpmh-arc-regulator compatible;
   - *-parent-supply and vin-supply on ARC group/child nodes.
7. Separate observations from interpretations. If the candidate has zero ARC groups, say only that the compiled candidate has none; do not imply the binary will fail. If groups exist, state whether pinned ACK has a driver match (ROUND146 establishes no match).
8. Compare against ROUND139 HOS facts without using or opening another agent's private files. The relevant evidence is public in the ROUND139 report:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md
9. If any check cannot be completed from existing artifacts, mark NOT FOUND / NOT RUN and explain why.

## Restrictions

- No build, bazel, make, compilation, tests, boot, or flashing.
- No network fetches or downloads.
- No tablet connection: no ADB, fastboot, recovery, UART, root or partition access.
- No source, DTS, patch, Kconfig, config, or binary modifications.
- No cleanup or deletion.
- Do not touch another agent's workspace.
- Do not assume a missing DT status means powered; it only affects node availability semantics.
- Do not invent missing ARC resources or CMD-DB AUX data.

## Deliverable

Upload one report to this branch:

- Branch: agent2/round147-candidate-arc-node-inventory
- Path: firmware-analysis/round147/AGENT2_ROUND147_CANDIDATE_DTB_ARC_NODE_INVENTORY.md

Include the exact artifact hash and all node/edge tables. Upload, read the file back to verify the content, then stop.

## Expected outcome

This is a static artifact inventory only. It does not authorize first boot or resolve physical PMIC inputs, final ABL RAM/FDT, runtime RPMh votes, AVB or recovery.
