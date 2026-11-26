# ROUND135 R3 — pinned 23-patch source / DTB / Image validation taskbook

Date: 2026-11-26  
Taskbook owner / issuing AI / final reviewer: **1号 AI（ChatGPT）**  
Execution agent: **user-local WorkBuddy test Agent**  
Independent review: **2号 AI** (review raw R3 artifacts; do not execute local commands)  
Task class: offline source reconstruction, schema, DTB, Kconfig, object compile, Image build and existing Host regression only.

## 0. Purpose and exact boundary

R2 has produced the same 23-patch content-tree SHA in two independent clean Git trees. Following 2号 AI's recommendation, 1号 AI pins that SHA as the expected R3 source-tree identity:

**EXPECTED ROUND135 23-PATCH CONTENT TREE SHA: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.**

R3 must independently reconstruct this exact source tree, then determine whether the full candidate:
1. passes its changed DT binding schemas and the actual board DTB validation/build;
2. resolves the intended Kconfig dependencies;
3. compiles the UFS / QMP UFS PHY / proxy-consumer objects;
4. builds the full `//common:dby_w09` Image target;
5. repeats the existing Host regression suites.

A successful R3 proves **source-tree reproducibility and the tested source/build foundation only**. It does not prove actual HOS4.3 memory handoff, PM8150 physical input wiring, ARC/MMCX behavior, AVB/DTBO/ramdisk selection, UFS enumeration, hardware rail behavior or tablet boot stability. The R3 Agent must not connect the tablet or perform device operations.

The R2 candidate SHA is now a predeclared expected value, not a value R3 may change after seeing its result. If the reconstructed content tree differs, stop before schema/build and report BLOCKED/FAIL.

## 1. Immutable source inputs

### 1.1 Fixed ACK kernel

- Repository: `aosp-mirror/kernel_common`
- Exact commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Tag/revision: `android17-6.18.33_r00`
- Expected initial root tree: `790a68ae6d4f4ac51ab2d88977b6fd5c031473b7`
- Do not switch to upstream Linux stable `v6.18.33`, another Android common tag, or a moving branch head.

### 1.2 Frozen 17-patch base manifest

- Repository: `hhdy/matepad11-dby-w09-agent-reports`
- Branch: `ai-parallel/stagea-port-until-boot`
- Path: `kernel-baseline/round61/round32-stagea-series.txt`
- Authoritative Git blob: `9a93b7e3a500d807533517a92b98fe244b2ea456`
- Predeclared 17-patch intermediate content tree: `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`
- Re-fetch and verify this exact manifest blob and each of its 17 file blob IDs / SHA-256 / order. Do not replace it with a reports-a30 local snapshot.

### 1.3 Full 23-patch manifest

- Repository: `hhdy/matepad11-dby-w09-agent-reports`
- Branch: `ai1/round130-stagea-ufs-lifecycle-integration`
- Path: `kernel-baseline/round135/ROUND135_23_PATCH_SERIES_MANIFEST.md`
- R2/R3 pinned manifest blob: `9188de2022f88c374bfcaa367c505428812608d9`
- Expected final 23-patch content tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`

Re-fetch the manifest from the exact branch, verify its Git blob is the pinned blob above, and verify every patch input against it. The manifest's section 8 records the R2 candidate tree freeze and the disclosed two-line annotation-only discrepancy between the obsolete local manifest snapshot and the authoritative GitHub frozen manifest. Do not claim those two manifest blobs are byte-identical.

### 1.4 Critical extension patch identities

| Series index | Exact path | Required Git blob |
|---:|---|---|
| 18 | `kernel-baseline/round135/series/18-round120-ufs-per-hba-async-join.patch` | `f604c8672fcbc98f3e9645f5e8888c8a34b1c11e` |
| 19 | `kernel-baseline/round135/series/19-round122-ufs-regulator-load-first.patch` | `64dd2ad9022251e2411a1a745aeb920a0badfa85` |
| 20 | `kernel-baseline/round135/series/20-round128-qmp-ufs-dual-rail-v2.patch` | `22ccec1cabf2d78e61442d19219985135f8341e7` |
| 21 | `kernel-baseline/round135/series/21-round126-proxy-consumer-load-first.patch` | `c180dbf458403d68b2c32c1d54776a7559e7e5db` |
| 22 | `kernel-baseline/round135/series/22-round135-huawei-dby-w09-real-dts.patch` | `ab0108364c835d87ac35ca670347d9d0001a821d` |
| 23 | `kernel-baseline/round135/series/23-round135-huawei-dby-w09-dtb-makefile.patch` | `ceb72ed206d97beb2c2fa8558cb120ee186cb685` |

Additional fixed input facts:
- Board DTS created by patch 22: `arch/arm64/boot/dts/qcom/huawei-dby-w09.dts`; source blob `58293f7a62a50f8109886c92ce4b9cd14d7980e2`.
- Fixed ACK qcom Makefile before patch 23: blob `296688f7cb26550f75bce65826f234bc24110356`; preserve literal TAB characters.
- Patch 22 is DTS-only; patch 23 is Makefile-only.
- The full ROUND45 UFS dual-GenPD / required-OPP implementation is already in frozen patch 5, blob `f1d54e5e0379183fbdfb3ca6132c6d0fc61d4622`. Do not apply the removed duplicate ROUND33/ROUND45 driver patch `2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5`. It is not one of the 23 inputs.

## 2. Role separation and safety requirements

1. 1号 AI owns this taskbook, the candidate series and the final acceptance decision.
2. The local WorkBuddy Agent only executes this taskbook and uploads evidence. It must not alter source, DTS, schema, patches, config fragments, taskbook or branch state.
3. 2号 AI is the independent reviewer of uploaded R3 raw evidence. It is not the local executor and must not be represented as having run the local commands.
4. Use one fresh, isolated source working tree and one fresh build-output directory. Do not reuse or modify R2 Tree A, R2 Tree B, the old R1 `round135-agent/a30`, ROUND130 staging or another existing workspace.
5. Do not install packages, reinitialize Repo, resync the source or download another compiler. Use only the existing pinned local source / toolchain environment. If it is unavailable, report BLOCKED; do not change the toolchain to force a pass.
6. No tablet connection, USB, ADB, fastboot, recovery, root, serial, boot, flash, partition read/write or firmware extraction.
7. Do not create boot/vendor_boot/vbmeta/DTBO/ramdisk images or a flashable package.
8. Do not modify `main`, AI1/AI2 branches, protected DTS branches, PR #1 or any production branch. No merge, cherry-pick or push to a kernel source repo.
9. Do not fix any test failure inside the Agent workspace. Preserve raw evidence and stop at the failed gate.
10. Do not invent or add memory banks, reserved-memory ranges, PMIC input parents, fixed regulators, ARC nodes, regulator votes or device properties.

## 3. Fresh source reconstruction and pinned-tree assertion

### 3.1 Start clean

Create a new independent clone/worktree repository with its own Git directory and object database. Before applying anything, save:
- remote URL and exact commit;
- `git rev-parse HEAD`;
- `git rev-parse HEAD^{tree}`;
- `git status --porcelain=v1`;
- `git rev-parse --git-dir` and `git rev-parse --git-common-dir`;
- exact manifest blob and source patch identities.

Required:
- HEAD = `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`;
- initial tree = `790a68ae6d4f4ac51ab2d88977b6fd5c031473b7`;
- worktree clean.

### 3.2 Apply all 23 patches in manifest order

Apply patches 1–17 from the pinned frozen manifest, then patches 18–23 from the pinned 23-patch manifest. Do not reorder, squash, substitute, omit or regenerate any patch.

For every patch:
1. verify input path, Git blob, byte length and SHA-256;
2. run `git apply --check --verbose` and save complete stdout/stderr/RC;
3. only after check RC=0, run `git apply --verbose` and save complete stdout/stderr/RC;
4. run `git diff --check` and save complete output/RC;
5. capture every offset emitted by both primary commands per hunk.

Forbidden: fuzz, reject, partial apply, skip, whitespace ignore, reduced context, `--unidiff-zero`, `--3way`, hand edits, patch regeneration or any fallback applier.

### 3.3 Required intermediate/final tree values

After patch 17, calculate the full content tree including all changed/new files using a temporary index or an equivalent method that does not confuse an unchanged unstaged index with the resulting worktree. Expected:
`77e2b2b1515b3813f7538aedffe4c5a4e90edb57`.

After patch 23, calculate the full resulting content tree in the same reliable way. It **must equal**:
`afe9517f8062b96bfeb5b4dd5714942861e6a44b`.

At final state also save:
- `git diff --stat`;
- `git status --short`;
- `git diff --check`;
- changed tracked and untracked path lists;
- binary diff SHA-256;
- exact tree computation command, temporary index path and cleanup/restoration record.

If the final tree differs by even one tree hash, stop before schema/build. Do not update the expected SHA, alter inputs, or label the result equivalent.

### 3.4 Controlled hunk offsets — exact accepted pattern

Use the normative policy `kernel-baseline/round132/ROUND132_OFFSET_ACCEPTANCE_POLICY_1AI.md`, blob `6712f686da9940937ed87eab2f4b27d44cb29626`.

The expected primary `git apply` offsets are:
- series patch 16: H1=-25, H2=-2, H3=+2;
- series patch 17: H1=+1, H2=-2;
- series patch 20 / ROUND128 V2: H3=-19.

All are controlled offsets previously reproduced in both R2 trees. Any deviation, any additional nonzero offset or any missing expected offset must be called out and must stop R3 for 1号 AI review. For every other patch, record exactly “no offset line emitted by the primary applier” only when that is what the log shows. Never report an offset count as zero if these hunks are present. Secondary-tool diagnostics, if any, must be labelled separately and must never be mixed into the primary `git apply` table.

Only proceed to §4 if source identity, stage-17 tree, final 23-patch tree, apply results and controlled-offset pattern all match.

## 4. DTS, binding and actual DTB validation

### 4.1 Source/merged-tree assertions

Check the merged result, not only the patch text:

- Root `model` and `compatible = "huawei,dby-w09", "qcom,sm8250"` match the candidate board DTS.
- The inherited Host compatible is `qcom,sm8250-ufshc`.
- UFS Host `power-domains` has exactly two entries in this order:
  1. `&rpmhpd RPMHPD_MMCX` (MMCX index 0);
  2. `&gcc UFS_PHY_GDSC` (GCC UFS_PHY_GDSC index 1).
- The UFS PHY itself retains only its original GCC `UFS_PHY_GDSC`; do not add MMCX to the PHY.
- The original Host SID mappings, clocks, resets, interconnects, OPP table, regulator phandles and status are preserved.
- `arch/arm64/boot/dts/qcom/Makefile` contains exactly one `huawei-dby-w09.dtb` entry with the required tab formatting.
- QMP UFS PHY has `vdda-phy-always-on;`, `vdda-phy-supply` and `vdda-pll-supply`; do not add duplicate max-current properties because the fixed ACK SM8250 QMP list supplies `init_load_uA=89900/18800`.
- Confirm that the patched RPMh regulator binding covers the PM8150/PM8150L compatibles and that all regulator child names / phandles resolve.
- Do not add any guessed `vdd-s*-supply`, `vin-supply`, `vph-pwr-supply`, ARC provider or synthetic fixed regulator.

### 4.2 Mandatory known DTS limits to report, not repair

These are existing evidence gaps and are not permission for Agent edits:

1. The included fixed ACK `sm8250.dtsi` defines a zero-size bootloader-filled `/memory@80000000` placeholder and its generic SM8250 `/reserved-memory` children. This is not a validated DBY-W09 HOS4.3 memory map. ROUND19/24 evidence records 37 HOS4.3 reserved-memory children, with multiple no-map, reusable, size/alignment and dynamic semantics. The final Huawei ABL/EFI memory handoff and complete mapping remain UNKNOWN. Record the inherited compiled DTB structure, but do not invent or copy RAM/reservation ranges.
2. The root compatible `huawei,dby-w09` has the previously documented board-binding gap in the pinned Qualcomm root schema. Record exact dtbs_check diagnostics; do not modify `Documentation/devicetree/bindings/arm/qcom.yaml` or weaken unrelated schema.
3. The candidate DTS contains `vcc-voltage-level`. The pinned ACK `ufshcd_populate_vreg()` implementation reads the supply phandle and `<rail>-max-microamp`; it does not parse `vcc-voltage-level`. Report this fact and the exact schema diagnostic (if any). Do not delete or rewrite the property during R3. Do not claim that this property causes an ACK UFS voltage vote.
4. `qcom,vccq-parent-supply` is retained as topology metadata but the pinned ACK path does not acquire/enable PM8150L S8 from it. Do not claim S8 is powered by this metadata.
5. The candidate's RPMh provider may resolve an unspecified physical input through the regulator-core dummy fallback. That does not prove the real PMIC input network. Physical PM8150 input supply topology remains UNKNOWN.

### 4.3 Binding checks

Run `dt_binding_check` on every binding YAML changed by the 23-patch series. At minimum include:
- `Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml`;
- the Qualcomm UFS schema selected for `qcom,sm8250-ufshc` in this ACK tree (`qcom,sc7180-ufshc.yaml`);
- `Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml`;
- `Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml`.

Use the actual fixed ACK filenames; do not substitute the older `qcom,ufs.yaml` binding for the SM8250-selected binding. Also inspect the exact changed-schema path list from `git diff --name-only` and ensure none is omitted.

Record dt-schema, dtc, Python, yamllint and other relevant tool versions, exact commands and full logs. No schema changes or fixture deletions are allowed.

### 4.4 Build and inspect the actual board DTB

- Build the actual `huawei-dby-w09.dtb` from the final pinned 23-patch source tree using the fixed ACK Kbuild environment and its standard target. Record exact `O=`, architecture, compiler/toolchain and command.
- Run actual `dtbs_check` for the board DTB using the target's standard Kbuild/dt-schema path; record whether it is targeted or full-tree and the exact selector.
- Decompile the exact DTB just produced (not a hand-written fixture) with the source tree's `scripts/dtc/dtc`, `fdtdump` or equivalent.
- Check the final compiled phandles/cells/order for dual Host domains, PHY domain, SID, clocks, OPP, all UFS supplies and PMIC provider nodes.
- Preserve complete logs and the decompiled DTS output (or a file with enough context to inspect each assertion).
- Do not state “DTB PASS” based only on source grep or an isolated ad-hoc dtc command.

## 5. Kconfig, C objects and full Kleaf Image build

### 5.1 Kconfig and .config

Resolve the final product config from the final 23-patch tree with the same pinned Repo/Kleaf configuration mechanism used in ROUND130. Save the complete `.config`, the exact config-generation command and its exit code.

Check at least these symbols and report their exact resolved values:
- `SCSI_UFSHCD`
- `SCSI_UFSHCD_PLATFORM`
- `SCSI_UFS_QCOM`
- `PM_DEVFREQ`
- `PM_OPP`
- `PM_GENERIC_DOMAINS`
- `PM_GENERIC_DOMAINS_OF`
- `QCOM_GDSC`
- `QCOM_RPMH`
- `QCOM_COMMAND_DB`
- `QCOM_RPMHPD`
- `OF`
- `REGULATOR`
- `REGULATOR_QCOM_RPMH`
- `IOMMU_SUPPORT`
- `ARM_SMMU`
- `ARM_SMMU_QCOM`
- `INTERCONNECT_QCOM_SM8250`
- `PHY_QCOM_QMP_UFS`.

The known ROUND130 product .config baseline SHA-256 is `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`. Since R3 uses the same storage-first fragment, compare against that baseline. If it differs, save a complete normalized diff and explain each difference; never force the baseline hash or edit config to match.

### 5.2 Independently compile changed C objects

Using the fixed ACK toolchain and resolved final config, compile at least:
- `drivers/ufs/core/ufshcd.o`;
- `drivers/ufs/host/ufs-qcom.o`;
- `drivers/phy/qualcomm/phy-qcom-qmp-ufs.o`;
- `drivers/regulator/proxy-consumer.o`.

If the dual-GenPD files added by frozen patch 5 produce another relevant object, include it too. Record full command, per-object RC, output size and SHA-256. Do not silently disable symbols or use a different config for object builds; if a temporary config transformation is technically required by the existing tool flow, record both config hashes and exact changed symbols.

### 5.3 Full Kleaf/Image build

Run the exact product target `//common:dby_w09` using the already-proven project Kleaf wrapper and fixed toolchain. Use the established ROUND130 invocation unless the local wrapper requires an explicitly documented equivalent:
```sh
tools/bazel build //common:dby_w09 --jobs=8 --local_ram_resources=6144
```

Do not switch the target, defconfig or fragment. Record BUILD_RC, elapsed time, toolchain versions actually visible in logs (do not guess versions), Bazel/Kleaf action summary and output provenance. Save hashes and sizes for:
- `Image`;
- `.config`;
- `System.map`;
- `vmlinux`.

No boot image, vendor_boot, ramdisk, DTBO, vbmeta, AVB or flashable package is part of R3.

## 6. Existing Host regressions

Re-run exactly the existing test harness and sources used by ROUND130; do not rewrite, regenerate, shrink or replace the tests:
- legacy ROUND31/32 lifecycle suite: expected 38 checks;
- ROUND32/33 suite: expected 83 checks.

ROUND130's exact prior report is:
- `firmware-analysis/round130/TEST_AGENT_ROUND130_COMBINED_REPORT.txt`, blob `def62019b5760d991f41d674e227b9e1af0761df`;
- original command recorded there: `tests/run_tests.sh "$K"`.

Use the same test source/harness identities and invocation recorded in the prior report/logs. Record each source/test harness identity if available, exact command, full output, checks, failures and RC. If the local test harness/sources needed to reproduce the exact tests are unavailable, mark BLOCKED; do not create a replacement suite or claim historical ROUND130 PASS as a new R3 result.

## 7. Static checks and report consistency

- Run final `git diff --check`.
- Run `scripts/checkpatch.pl --strict --no-signoff` for the new board DTS and patch 22/23 content; record exact RC, errors, warnings and CHECK items.
- For patches 18–21, include the historic ROUND130 checkpatch result with the source report/blob identity; do not silently call them clean or auto-fix them.
- Run SPDX validation only if the existing dependency is present. If `python3-ply` or another required dependency is missing, mark NOT RUN / BLOCKED and include the raw error; do not install packages.
- Report every warning, CHECK, error, offset, schema diagnostic, test skip and environment limitation. Do not convert a nonzero RC into PASS because the textual summary looks favorable.

## 8. R3 acceptance outcomes

Use exactly one of the following:

- **PASS — SOURCE / DTB / IMAGE BUILD FOUNDATION ONLY**: exact 23-patch tree and offsets match; all required schema, actual DTB build/inspection, Kconfig, object compile, full Image build and both Host regressions completed with acceptable results and raw logs. No device or boot claim is allowed.
- **PARTIAL — IMAGE BUILD PASSED, KNOWN SCHEMA / DTB DIAGNOSTIC REMAINS**: Image build succeeds but dt_binding_check / dtbs_check has a nonzero result or a known root-compatible issue remains. State the exact diagnostic; do not label full R3 PASS.
- **BLOCKED**: required inputs, source tree, toolchain, test harness or validation stage unavailable; preserve evidence and state the exact blocker.
- **FAIL**: wrong tree/input, unexplained offset, failed apply, C compile/DTB/Image failure, failed functional test or any unexplained source-tree change.

Known gaps (zero-size memory placeholder, unverified reserved-memory handoff, PMIC physical input topology, ARC/MMCX semantics, VCCQ-parent non-consumption, AVB/DTBO/ramdisk path) remain separate hard boot gates irrespective of R3 result.

## 9. Evidence upload and stop

Upload new files only; do not overwrite any R1/R2/Round130 artifacts. Target:
`firmware-audit-v1:firmware-analysis/round135/r3/`

Required deliverables:
1. `ROUND135_R3_FINAL_REPORT.txt` — result, exact scope and all open boundaries;
2. `round135-r3-identity-apply-tree.log` — source identities, per-patch checks/applies/offsets, stage-17 and final tree hashes;
3. `round135-r3-schema-dtb.log` — changed-schema checks, dtbs_check, DTB build, decompile and assertions;
4. `round135-r3-kconfig-object-kleaf.log` — .config, symbols, changed C objects and full Image build hashes;
5. `round135-r3-host-regression.log` — exact 38/38 and 83/83 regression rerun;
6. `round135-r3-checkpatch-spdx-diff.log` — final diff/checkpatch/SPDX and full diagnostics;
7. `round135-r3-upload-readback.log` — upload commit, file Git blobs, nonempty readback and byte identity.

After upload, read every file back from `firmware-audit-v1`, verify its content and Git blob, and record those identities. Then stop immediately and send the results to 2号 AI for independent raw-evidence review and 1号 AI for final acceptance. Do not start any next round.

**There is no device connection or physical tablet test in R3.** R3 ends at source/build validation. Any later hardware test requires a separate 1号 AI taskbook, a separate explicit authorization, and a direct notice to the user before the Agent is instructed to connect the tablet.
