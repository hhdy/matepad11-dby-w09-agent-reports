# ROUND59 — Ordered UFS patch-series exact-source integration simulation

**Date:** 2026-11-24  
**Status:** ALL 16 HUNKS MATCH EXACT PINNED SOURCE CONTEXT IN ORDERED IN-MEMORY SIMULATION; NO REAL GIT APPLY / SCHEMA / BUILD  
**Device:** Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 rev 2.1  
**Stage:** A — ACK 6.18.33 only  
**Immutable ACK common commit:** \`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a\`

## 1. Objective

Upgrade the UFS patch-series evidence beyond the earlier ROUND52 context-count simulation by replaying every unified-diff hunk in the intended order against exact files fetched at the immutable ACK commit, including:
- ROUND57 from the corrected current main artifact;
- both \`ufs-qcom.c\` and \`ufs-qcom.h\` targets in ROUND52-0002;
- the separate review-only DBY-W09 DTS fixture targeted by ROUND37.

This was performed through an in-memory exact-context patch simulation using the fetched file contents and unified diff hunks. Every source file and patch artifact SHA was checked against the previously recorded immutable identities before application.

**Important boundary:** this is not an execution of Git's \`git apply\` or \`git apply --check\`. No local ACK worktree exists in this environment. No real files were changed. The simulation is a stronger exact-hunk/context/line-anchor check than the prior prose-only context audit, but it must not be described as a real Git apply.

## 2. Exact source files and identities

| Source file | Git blob SHA | Result |
|---|---|---|
| \`Documentation/devicetree/bindings/ufs/qcom,ufs.yaml\` | \`1dd41f6d5258014d59c8c8005bc54f7994351a52\` | Exact expected identity |
| \`Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml\` | \`962dffcd28b44b3489be5615c75e7270a0c45dc4\` | Exact expected identity |
| \`drivers/ufs/host/ufs-qcom.c\` | \`a80c6998406dbc88c25dbd9977699ba481207efe\` | Exact expected identity |
| \`drivers/ufs/host/ufs-qcom.h\` | \`5f979daabd5323184eeee137cc8ecc076193979e\` | Exact expected identity |
| \`dts/dby-w09-ack18-board.dts.draft\` (protected branch fixture, read-only) | \`e86c8707c413a9376b1e332a94e292b86acde3e2\` | Exact expected identity |

All five source blob IDs returned by GitHub matched the exact expected values above. The board DTS fixture is from \`ack18-dby-w09-dts-draft\` and was fetched read-only; that protected branch was not modified.

## 3. Patch sequence and exact application simulation

Required order:

1. ROUND32 — SM8250 UFS compatible and eight-clock base binding.
2. ROUND57 — exact eight-entry \`clock-names\` constraint.
3. ROUND36 — compatible-scoped two-power-domain binding.
4. ROUND52-0001 — VDDP / VCCQ-parent binding properties.
5. ROUND37 — dual-GenPD board DTS delta against the review-only fixture only.
6. ROUND33 — UFS dual-GenPD / required-OPP driver logic.
7. ROUND52-0002 — VDDP managed regulator lifecycle.

### Hunk results

| Patch | Target | Hunk results | Status |
|---|---|---|---|
| ROUND32 | \`qcom,ufs.yaml\` | 3/3 exact (old anchors 24, 39→matched 40 after previous +1, 148→matched 150 after previous deltas) | PASS |
| ROUND57 | \`qcom,ufs.yaml\` | 1/1 exact at resulting line 165 | PASS |
| ROUND36 | \`qcom,ufs-common.yaml\` | 2/2 exact at lines 41 and 64 | PASS |
| ROUND52-0001 | \`qcom,ufs.yaml\` | 2/2 exact; second hunk matched resulting line 85 after first hunk additions | PASS |
| ROUND37 | board DTS draft fixture | 2/2 exact; second hunk matched resulting line 214 after include additions | PASS |
| ROUND33 | \`ufs-qcom.c\` | 2/2 exact; driver implementation hunk matched resulting line 2808 after include additions | PASS |
| ROUND52-0002 | \`ufs-qcom.h\` + \`ufs-qcom.c\` | 4/4 exact: header line 316; C-file lines 17, 1498 and 1656 | PASS |

**Total: 16/16 hunks exact, no fuzz, no nearest-context fallback.**

### Exact patch blob identities

| Patch | Current blob SHA |
|---|---|
| ROUND32 | \`efe2d932da34716c631de22d89aba19730cc7f50\` |
| ROUND57 corrected | \`3656f05ad01d54452b83591b762faaa71a16f592\` |
| ROUND36 | \`dad87ef8dfefee6141b8a7949982c007c4a03b4a\` |
| ROUND52-0001 | \`c0ac84067a900022a077c748b7abb10345f1295f\` |
| ROUND37 | \`486654c8d0b1b785190253270f5e83f796f07362\` |
| ROUND33 | \`2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5\` |
| ROUND52-0002 | \`fb34fbc9701bc7e7b56bb9078ee98c0cdd8caf78\` |

## 4. ROUND57 patch-file defect found and corrected

During parsing of ROUND57, its previous main-branch blob \`f282a695ed1201298f29a54ff0871084d995b3f2\` declared:

\`\`\`
@@ -163,6 +163,8 @@
\`\`\`

But the actual old/new unified-diff body contains 13 old lines and 15 new lines, and after applying ROUND32 the relevant SM8250 clock block begins at line 165, not 163. The old hunk header was therefore malformed and had an incorrect post-ROUND32 anchor.

The canonical main artifact was corrected to:

\`\`\`
@@ -165,13 +165,15 @@
\`\`\`

Current corrected file:
\`kernel-baseline/round57/0001-dt-bindings-ufs-sm8250-clock-names-exact-count.patch.draft\`

Current blob:
\`3656f05ad01d54452b83591b762faaa71a16f592\`

The corrected hunk now applies exactly after ROUND32 in this ordered simulation. ROUND32's original blob and content were not changed. The independent ROUND54 branch is retained as historical review evidence; its candidate was not copied into the canonical series.

## 5. Post-application content assertions

After simulating the complete ordered series, the following expected content checks all passed:

- SM8250 UFS compatible is in the binding select/compatible definition.
- The SM8250 branch constrains \`clocks\` and \`clock-names\` to exactly eight entries.
- VDDP REF_CLK and VCCQ-parent supply/load properties are documented in the UFS binding.
- The common UFS schema keeps the two-domain maximum scoped to SM8250; non-SM8250 Qualcomm UFS remains constrained to one.
- The board DTS draft fixture places RPMHPD MMCX first and GCC UFS_PHY_GDSC second.
- The driver maps the single UFS required-OPP slot to attached domain index 0.
- The VDDP helper and regulator enable/cleanup state are present in the resulting driver source.
- The companion header contains the regulator pointer and VDDP state flags.

A scan of 367 added patch lines found zero lines ending in trailing whitespace. This is a lightweight added-line whitespace scan, **not** a claim that \`git diff --check\` was run.

## 6. What remains NOT_RUN

- Real \`git apply --check\` in a disposable full ACK worktree.
- Real patch application and \`git diff --check\`.
- \`checkpatch.pl\` for driver patches.
- Full YAML parse/JSON-schema composition and the kernel \`dt_binding_check\` target.
- DTS preprocessing, \`dtc\`, \`dtbs_check\`; the ROUND37 fixture is not in a real ACK DTS source path.
- Kconfig resolver, \`olddefconfig\`, final \`.config\`.
- Kleaf/Bazel target definition, Bazel query, kernel object compile, Image build.
- DTB/DTBO, boot image or AVB packaging.
- First-boot memory handoff validation.
- Actual DBY-W09 device boot, UFS link/storage enumeration, suspend/resume or hardware acceptance.

The main current blocker for these operations remains obtaining an authorized local build workspace. ROUND16 was blocked before WSL execution; ROUND17 now diagnoses the actual WorkBuddy execution-policy owner before any retry. Second AI ROUND58 independently prepares the Kleaf target candidate and .config checker.

## 7. Project conclusion

The ordered text series is now **internally exact-context consistent** against the fixed ACK source identities, including the ROUND57 hunk correction and the full two-file ROUND52-0002 patch. It is ready to be rechecked with real Git after the local source workspace exists.

This is not compile approval, schema validation, runtime approval or a boot candidate. Stage A remains ACK 6.18.33 first; do not begin DerpFest Android 17 Stage B until actual kernel boot plus storage/basic-hardware acceptance.
