# ROUND60 — Primary review of ROUND58 Kleaf target and final-config validator

**Date:** 2026-11-24  
**Reviewer:** Primary AI  
**Second-AI branch:** \`ai-parallel/round58-kleaf-target-audit\`  
**Status:** SOURCE-LEVEL DESIGN REVIEW PASS; MINOR RUNBOOK CLARIFICATION; NO BAZEL / KCONFIG / COMPILE EXECUTED  
**Fixed ACK:** \`android17-6.18.33_r00\` / \`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a\`

## 1. Reviewed deliverables

Second AI committed the following artifacts only on its dedicated branch:

| Artifact | Blob SHA | Primary review |
|---|---|---|
| \`0001-add-dby-w09-full-kernel-kleaf-target.patch\` | \`fa2183850a40b3e5054da8b9f410c0a65e820f79\` | Source context/fragment consistency PASS |
| \`check_dby_w09_config.py\` | \`5622b1e8e3dcf1c683e252e2abb1177de0b44435\` | Static behavior review PASS |
| \`tests/test_check_dby_w09_config.py\` | \`82acac9f1602228ed9a780a98f7aadc046d55cad\` | Nine test cases inspected |
| \`round58_kleaf_target_implementation.md\` | \`43be9adf30cc9cbff6443c554ef680e45cebf9b6\` | Runbook and evidence boundaries reviewed |

No changes from ROUND58 were copied into main or any protected branch. PR #1 remains Draft/Open/unmerged.

## 2. Kleaf target review

The candidate adds the following full custom target in the pinned ACK common BUILD package:

\`\`\`python
kernel_build(
    name = "dby_w09",
    srcs = [":kernel_aarch64_sources"],
    outs = [".config", "Image", "System.map", "vmlinux"],
    arch = "arm64",
    defconfig = "arch/arm64/configs/gki_defconfig",
    make_goals = ["Image"],
    makefile = ":Makefile",
    post_defconfig_fragments = [
        "arch/arm64/configs/dby_w09_storage_first.fragment",
    ],
    visibility = ["//visibility:private"],
)
\`\`\`

Primary verification:
- Fetched pinned ACK \`BUILD.bazel\` blob is exactly \`3c8178ebce1f27f2c417e4aeaa00fc7001a96be6\`.
- The patch's 5-line insertion context matched exactly at pinned line 1351.
- New target hunk counts are structurally correct: 5 old context lines / 23 new lines.
- The 132 lines added as \`arch/arm64/configs/dby_w09_storage_first.fragment\` match byte-for-byte after newline normalization with the canonical main fragment whose blob is \`ae8675357e2f5c57c9ec38e7574b00590b558c63\`.
- The pinned \`yukawa\` target confirms the no-\`base_kernel\` full-image pattern and the \`Image\`, \`System.map\`, \`vmlinux\` output choices. The pinned allmodconfig test demonstrates \`.config\` as an output used to force build execution when a build-test target has otherwise no distributable outputs.
- \`post_defconfig_fragments\` is the correct stage for storage-first built-in requests: the pinned manifest-declared Kleaf \`main-kernel-2026\` documentation says Kleaf applies the post fragment after base defconfig, calls \`make olddefconfig\`, and checks that every post-fragment setting is present in the final \`.config\`.

This supports the candidate's architecture. It is still a patch candidate: no real \`git apply --check\`, buildifier, Bazel query or Kleaf build was run.

### Output/build target boundary

The target requests only \`Image\` as its explicit make goal and does not declare modules, DTB, DTBO, boot image, vendor_boot, init_boot or flash-package outputs. This is intentional:
- the first milestone needs a full custom kernel with Qualcomm storage/power dependencies built in;
- no real DBY-W09 DTS path is yet integrated into ACK;
- trusted final system-memory handoff is not yet proven;
- boot header/ramdisk/AVB packaging remains a separate first-boot gate.

The target does not declare KMI enforcement or an invented device symbol list. The result must be described as an ACK-derived / GKI-based custom kernel, not an officially certified GKI.

## 3. Config validator review

The checked-in validator uses only Python's standard library and has:
- one required .config positional path;
- deterministic human-readable and JSON output;
- nonzero exit for unreadable/missing input;
- duplicate assignment detection, including duplicate equal-value assignments;
- exact =y enforcement for the required storage-first built-in set, including DM_VERITY and DM_VERITY_FEC inherited from the pinned GKI baseline;
- separate treatment of derived \`ARM_SMMU_QCOM\`: absence is an investigation note, while a present non-y value fails.

The test file contains nine cases covering a valid synthetic config, missing required symbol, =m, =n, conflicting duplicate, missing file, unreadable file, JSON output, and derived SMMU provider if present but modular.

The second AI reports that it executed those nine synthetic tests successfully in its Python environment. This review inspected the committed test source but did not independently rerun the branch's test file from a checked-out copy. Synthetic tests do not equal Kconfig resolution. The helper must ultimately run against the actual Kleaf-emitted .config and its PASS output must be archived.

No source-level validator defect was found in this review. The helper's required symbol set is a first storage-milestone gate; it is not a complete device-feature configuration audit.

## 4. Runbook corrections for actual execution

One command correctness fix is required when the local build round adopts the second-AI runbook. Any Bazel command piped to \`tee\` must preserve the Bazel exit status:

\`\`\`bash
set -o pipefail
tools/bazel build --jobs=4 --verbose_failures //common:dby_w09 \\
  2>&1 | tee logs/round58/dby_w09-image-build.log
\`\`\`

Without \`pipefail\`, a shell pipeline may report the exit status of \`tee\` even when Bazel failed. Use the same pattern for the stock baseline build and schema/checkpatch logs if piped.

The runbook currently shows the identical \`tools/bazel build //common:dby_w09\` command in both the config-resolution gate and the later Image-build gate. On the first execution, Bazel can build the target and produce its declared .config. Then use \`cquery --output=files\`, run the config checker and archive .config. Do not repeat the exact same build solely to start the Image gate; only rerun after a source/config/BUILD change or when explicitly requesting a clean rebuild. The optional stock GKI baseline can be run first as a separate toolchain sanity check.

The suggested four-job CPU cap is a provisional starting point only. Before choosing a memory cap, inspect the effective WSL/cgroup memory limits; Windows-visible RAM alone is not the same as the WSL memory budget.

## 5. UFS driver contract spot-check

As part of this review, rechecked the relevant fixed-source interfaces used by ROUND33:
- \`dev_pm_opp_of_get_opp_desc_node()\` returns the node referenced by the device's first \`operating-points-v2\` phandle and explicitly requires caller \`of_node_put()\`.
- \`_of_init_opp_table()\` records the OPP table node and discovers the required-OPP slot count from the first available OPP entry before the later static OPP table is populated.
- \`dev_pm_opp_set_config()\` must run before OPPs are initialized; it creates/gets the table and installs the \`required_dev\` mapping. This is consistent with ROUND33 calling it in the Qualcomm probe before \`ufshcd_pltfrm_init()\`.
- \`devm_pm_domain_attach_list()\` returns the number of domains attached and stores the provider devices in the returned list. ROUND33's check for exactly two and use of \`pd_devs[0]\` is consistent with the fixed index contract.
- \`_opp_set_required_dev()\` checks \`required_dev_index\` against the required-OPP slot count. The one-slot UFS OPP table uses index 0, mapping the required OPP to MMCX while the GCC UFS_PHY_GDSC remains the second attached domain.

These are source-contract checks only. No runtime device-link, deferred-probe, power-state, MMCX vote or UFS link test was executed. The full ROUND33/ROUND52 driver series remains subject to actual compile and device validation.

## 6. Evidence states after ROUND58

| Gate | Current evidence |
|---|---|
| Kleaf target patch written | YES |
| Target patch exact insertion context checked against pinned BUILD | YES, in-memory/source retrieval |
| Storage-first fragment exact to canonical draft | YES |
| Config validator + nine synthetic tests committed | YES; second-AI reports 9 pass |
| Real Git worktree patch application | NOT_RUN |
| Bazel target query | NOT_RUN |
| Final Kconfig/Kleaf config resolution | NOT_RUN |
| Validator against actual final .config | NOT_RUN |
| Driver compilation | NOT_RUN |
| Full custom Image compile | NOT_RUN |
| Board DTB/DTBO or boot image | NOT_RUN |
| Device boot / UFS storage acceptance | NOT_RUN |

ROUND58 is accepted as a useful source-level build candidate and validation toolset, not a compiled kernel. Keep its branch separate until actual local integration and tests determine whether it should be adopted.

## 7. Next execution order

When WorkBuddy has legitimately prepared the WSL2 Ubuntu / pinned ACK workspace:
1. Verify repo manifest -r and the exact common HEAD.
2. Create a disposable worktree at the immutable ACK commit.
3. Apply ROUND32 → corrected ROUND57 → ROUND36 → ROUND52-0001 → ROUND37 only after real DTS migration → ROUND33 → ROUND52-0002, with real \`git apply --check\`, apply and \`git diff --check\`.
4. Apply the ROUND58 Kleaf BUILD patch and copied fragment; run buildifier/Bazel query.
5. Run UFS \`dt_binding_check\`; keep board DTS/DTB separate until real DTS path and memory strategy are ready.
6. Execute Kleaf config resolution, archive actual .config, run ROUND58 validator, resolve any hidden/dependency failures.
7. Compile the full DBY-W09 Image target with bounded Bazel resources and preserved exit codes.
8. Archive Image/.config hashes, System.map, vmlinux metadata, manifest/toolchain identities and complete logs.
9. Separately resolve AVB, ramdisk and memory handoff before any board boot-image candidate or device attempt.

Stage B DerpFest remains deferred until the ACK-derived kernel actually boots on DBY-W09 and passes storage/basic-hardware acceptance.

## 8. Source references

- Pinned ACK \`BUILD.bazel\` at commit \`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a\`, blob \`3c8178ebce1f27f2c417e4aeaa00fc7001a96be6\`.
- Pinned manifest-declared Kleaf config docs: https://android.googlesource.com/kernel/build/+/refs/heads/main-kernel-2026/kleaf/docs/kernel_config.md
- Kleaf config-order details independently opened during this primary review: lines 70–88 and 208–229 of the above document.
- ROUND58 artifacts listed in §1.
- ROUND59 exact-source UFS series check: \`kernel-baseline/round59/round59_ufs_patch_series_exact_source_integration.md\`.

