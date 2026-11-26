# ROUND135 — AI2 independent taskbook audit (controlled-offset policy)

- Reviewer: 2号 AI
- Review type: read-only taskbook / acceptance-policy consistency audit
- Review date: 2026-11-26
- Review branch: `ai2/round135-controlled-offset-taskbook-audit`
- Base: AI2 branch commit `c696f53caa2d653970a45b6ec23eecf56d0b6cef`
- Reviewed taskbook: `ai1/round130-stagea-ufs-lifecycle-integration:kernel-baseline/round135/TEST_AGENT_ROUND135_TASKBOOK.md`
- Taskbook blob: `d37c5536c697b9d587ce9dcf6315b5758610fae1`
- Reviewed manifest: `kernel-baseline/round135/ROUND135_23_PATCH_SERIES_MANIFEST.md`
- Manifest blob: `a492fe78228836fceb980363143aff35365c9d6f`
- Governing policy: `main:kernel-baseline/round132/ROUND132_OFFSET_ACCEPTANCE_POLICY_1AI.md`
- Policy blob: `6712f686da9940937ed87eab2f4b27d44cb29626`

## 1. Executive finding

**ROUND135 is a valid next integration-validation candidate, but the currently published Agent taskbook is not yet ready to execute under the user's project-wide controlled-offset policy.** This is a taskbook/policy mismatch, not a finding that the 23-patch source candidate is incorrect.

The current PROJECT_HANDOFF records that ROUND135 Agent validation has NOT STARTED. This audit did not start an Agent, run a build, apply patches, or modify any AI1 source/manifest/taskbook.

## 2. Candidate identity reviewed

- Fixed ACK: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` (`android17-6.18.33_r00`).
- Frozen base: 17 patches from `ai-parallel/stagea-port-until-boot`, manifest blob `9a93b7e3a500d807533517a92b98fe244b2ea456`.
- Extensions 18–21: exact ROUND130 candidates.
- Patch 22: real-path DBY-W09 DTS + qcom Makefile entry, blob `d303439a9fde864ea765f9ef0888ada3f20468c`.
- Patch 23: SM8250 UFS dual-GenPD / required-OPP driver candidate, blob `2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5`.
- The manifest describes a disposable validation candidate and explicitly retains unresolved ABL memory handoff, PM8150 physical input rails, MMCX-to-MX ARC/corner equivalence, AVB/DTBO and boot-chain gates.

## 3. Blocking taskbook gaps against the controlled-offset policy

The ROUND132 policy requires exact base and inputs, successful primary check/apply, per-hunk offset disclosure, no fuzz/context relaxation, a predeclared expected final content-tree SHA, at least two independently created clean trees producing that exact SHA, a clean resulting worktree, and independent review of raw logs.

The current ROUND135 taskbook needs the following corrections before dispatch:

1. **No predeclared full-series expected tree.** It records the ROUND132 17-patch tree `77e2b2b1515b3813f7538aedffe4c5a4e90edb57` as a comparison value, but does not declare the expected resulting tree for the complete 23-patch series. The 17-patch tree is not the 23-patch expected tree.
2. **Only one fresh source tree is operationally specified.** The taskbook asks for a fresh isolated clone/tree, but does not require two independently created clean trees to apply all 23 exact inputs and produce the same predeclared final tree SHA.
3. **The offset rule is still historical-offset gated.** It says an offset differing from known historical offsets must stop the run. Under the new policy, a nonzero or previously unseen offset is not automatically a failure: it must be fully disclosed and reproducible in both clean trees, with no context relaxation, and both trees must equal the predeclared expected tree. The reviewer may still block a suspicious offset if raw evidence indicates misapplication.
4. **No explicit ban list for all context-relaxation paths.** The taskbook bans fuzz/reject/skip/partial application, but should also explicitly forbid whitespace-ignore modes, `--unidiff-zero`, fallback/reject/three-way repair, and any other dropped/relaxed-context path.
5. **Primary and secondary diagnostics need a sharper split.** Keep `git apply --check --verbose` and actual `git apply --verbose` as the primary applier evidence. Any GNU `patch` or other diagnostic must be separately labelled secondary and must not be used to rewrite or conceal primary offsets.

## 4. Required taskbook amendment

1号 AI, as ROUND135 source owner and Agent dispatcher, should revise its own taskbook/manifest before the local WorkBuddy Agent is given the task. The amendment should:

- Preserve the exact 23-patch manifest and all current patch blobs; do not regenerate, edit, reorder or replace any input.
- Compute and publish the exact expected post-23-patch Git content-tree SHA **before** the Agent run. Record the exact fixed ACK commit/tree, patch manifest identity, and method used to derive the expected tree.
- Require two independently created clean source trees, each starting from the exact ACK commit and independently verifying all 23 patch blobs/SHA-256/size/order.
- In both trees, run primary `git apply --check --verbose` and actual `git apply --verbose` for every patch; record every offset per patch and hunk, plus commands and exit codes.
- Require both final trees to equal the predeclared expected SHA exactly; record `git diff --check`, index/worktree status and unexplained-file checks for both.
- Permit controlled nonzero offsets only when the offset pattern is reproducible across the two trees and all other exact-input / exact-result gates pass. Do not require zero offset and do not automatically fail solely because an offset differs from old historical examples.
- Explicitly forbid fuzz, ignored whitespace, `--unidiff-zero`, context dropping/relaxation, fallback, reject-based repair and three-way repair.
- Keep any GNU `patch --dry-run` output as secondary diagnostics, clearly separated from the primary Git applier logs.
- State which one of the two identical resulting trees is used for schema, dtbs_check, real DTB inspection, Kconfig, object compile, Kleaf build and Host regression. The second tree is an independent exact-application/result-tree reproduction; do not imply tests ran twice unless they actually did.
- Preserve all current device/firmware safety exclusions and stop conditions.

## 5. Current ROUND135 status

- Candidate source review: the handoff records 1号 AI's source-level review of the dual-GenPD / required-OPP driver as PASS. This is source review only.
- 23-patch full-tree apply: NOT RUN.
- dt-schema / dtbs_check / real DBY-W09 DTB build and decompile: NOT RUN.
- Final Kconfig / UFS C object / full Kleaf `//common:dby_w09` build: NOT RUN.
- Host regression 38/38 and 83/83 for the full 23-patch candidate: NOT RUN.
- Agent execution: NOT STARTED per current handoff.
- Phase E/F: BLOCKED on independent hardware/boot-chain evidence; Phase G: NOT RUN.

## 6. Role and safety boundary

This is an AI2 read-only review note. It does not alter the AI1 branch, candidate source, patch manifest, taskbook, product configuration, protected branches, firmware or device. 2号 AI does not dispatch the local WorkBuddy Agent on 1号 AI's behalf. The Agent remains test-only and may run only after the authoritative dispatcher publishes the corrected taskbook and the user hands it to the Agent.

No tablet connection, USB, ADB, fastboot, recovery, root, serial, partition read/write, boot, flash, firmware extraction, boot-package generation, AVB/DTBO/ramdisk packaging or HOS4.3 work was performed.

## 7. Review disposition

**ROUND135 candidate: READY FOR TASKBOOK AMENDMENT; NOT READY FOR AGENT DISPATCH under the controlled-offset standard.**

After the taskbook is amended by its owner, the next progress gate is Agent execution of the offline validation scope and upload/readback of raw evidence. No later round should start automatically.