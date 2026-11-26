# ROUND135 R3 — AI2 independent raw-evidence review

Date: 2026-11-26  
Reviewer: 2号 AI (independent review; no local execution)  
Execution evidence: WorkBuddy local Agent, uploaded under `firmware-audit-v1:firmware-analysis/round135/r3/`  
Scope: review of the R3 taskbook, final report, six raw deliverables and upload/readback identities. No source tree, local host, device or build commands were run by this reviewer.

## 1. Independent disposition

**R3 is correctly classified PARTIAL — IMAGE BUILD PASSED, KNOWN SCHEMA / DTB DIAGNOSTIC REMAINS. Do not upgrade it to full PASS.**

The final report's central result is supported by the uploaded logs: the expected 23-patch content tree was reconstructed, the predeclared offsets reproduced, the Kleaf Image build succeeded, the board DTB was built and decompiled, the required Kconfig symbols resolved, four required objects compiled, and both host suites reported 38/38 and 83/83. The DTB validation still emits the documented Huawei root-compatible schema mismatch and the unsupported `vcc-voltage-level` property. The taskbook explicitly makes a known root-compatible issue sufficient for PARTIAL even when the command exit code is zero.

## 2. Evidence checked

The following uploaded files were fetched from `firmware-audit-v1`; their Git blob IDs match the upload/readback manifest:

| Deliverable | Git blob |
|---|---|
| `ROUND135_R3_FINAL_REPORT.txt` | `a898e8b2282d93f1b5b98a2dd5e14111d08de7b7` |
| `round135-r3-identity-apply-tree.log` | `8f8212611ae6788d54125f3c42e25f5bff85d3ff` |
| `round135-r3-schema-dtb.log` | `d5a622c251d112a69ad163a494ffde798487c916` |
| `round135-r3-kconfig-object-kleaf.log` | `c24f39c6102ef716097cb42e20e60e3af9962eae` |
| `round135-r3-host-regression.log` | `bbfe02ee73ae4ec3e3d869b2c25b45335f0960d5` |
| `round135-r3-checkpatch-spdx-diff.log` | `5f746cee9f73f5a2efba73b077e9be369da0b9cb` |
| `round135-r3-upload-readback.log` | `7b03e6e535060e2e2398c89474832414493dfd32` |

The readback manifest records byte-identical readback for the six preceding files; the final self-upload row also records readback success. No R3 source or binary was copied into the AI2 branch.

## 3. Gate-by-gate review

### 3.1 Source identity and patch application — supported

- ACK HEAD and root tree match the pinned values: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` and `790a68ae6d4f4ac51ab2d88977b6fd5c031473b7`.
- The 17-patch intermediate tree matches `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`.
- The final 23-patch content tree matches the predeclared `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
- The primary applier reports RC=0 for every patch check/apply/diff-check. The controlled offsets match the predeclared R2 pattern exactly: patch 16 H1=-25/H2=-2/H3=+2; patch 17 H1=+1/H2=-2; patch 20 H3=-19. No fuzz, reject, partial apply or fallback applier is reported.
- Patch 19–21 identity records later in the same raw log contain their expected Git blob, SHA-256 and byte size, and their actual apply checks succeed.

**Disclosure to preserve:** the initial input-fetch helper logs three `cp: cannot stat` errors for local copies of patches 19–21 and then `EB[$n]: unbound variable`. The log subsequently records direct identity verification for all three patches and their successful application. This appears recovered rather than a final source mismatch, but the final report should explicitly say the helper failed and direct GitHub refetch/verification was the recovery path; do not omit the initial error from the audit trail.

### 3.2 Binding / DTB — build evidence supported; validation remains partial

- The changed-schema set is recorded as four files: UFS common, SM8250-selected `qcom,sc7180-ufshc.yaml`, QMP UFS PHY and RPMh regulator. `dt_binding_check` reports RC=0.
- `yamllint` was not installed and was skipped by the kernel target; the malformed unrelated upstream `gunyah-cma-mem.yaml` was ignored by the schema scanner. Both are disclosed and are not evidence that the changed schemas failed.
- The actual `qcom/huawei-dby-w09.dtb` target was built and the exact result decompiled. The reported compiled-DTB assertions are 18/18.
- Targeted `dtbs_check` emits the known root-compatible failure for `huawei,dby-w09` against the pinned Qualcomm root schema and the `vcc-voltage-level` unexpected-property diagnostic from the selected UFS schema. Its process RC is reported as 0; that does not erase the diagnostics or override the R3 taskbook's PARTIAL rule.
- The board DTS checkpatch invocation against a bare .dts file is not a valid unified-diff check. The patch-22 unified diff was checked and reports 0 errors / 3 warnings; this is the meaningful checkpatch result.

### 3.3 Kconfig, objects and Image — supported

- Full target `//common:dby_w09` reports BUILD_RC=0 and 775 Bazel actions.
- Image: 44,820,992 bytes, SHA-256 `dba8fcf756a57b7995886bdcb93872555b5fee9300eadb4e9b0bdfd7f37ebea1`.
- .config SHA-256 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`, matching the ROUND130 baseline.
- All 19 required symbols are recorded as `=y`.
- All four required objects report RC=0: `ufshcd.o`, `ufs-qcom.o`, `phy-qcom-qmp-ufs.o`, `proxy-consumer.o`. The scratch object-build config transformation is disclosed and its hash matches the prior ROUND130 transformation.
- Timing should be stated precisely: the outer wrapper reports 310 seconds; Bazel itself reports 305.218 seconds. The final report's rounded 305 seconds corresponds to Bazel's internal elapsed time.

### 3.4 Host regressions — test results pass; baseline identity comparison is incomplete

The R3 raw log reports 38/38 and 83/83, both with zero failures and overall RC=0. It identifies the harness as `round132-agent/host-work/run_tests.sh` with SHA-256 `145bf8d3b65b4445339724129fe2ba67f9f37e3afd745eab41dc0e2ebc3be624`, and records the two test-source hashes `58b0ca477b964a1cf28a8f81a170e8d686266b8bec025539b7f5073adceb8d5c` and `138213990ce269707a66c1bcca3101aa0445a1f90169293e3606fad618089250`.

However, the ROUND130 combined report available in the repository records the historical invocation `tests/run_tests.sh "$K"` and the 38/38 + 83/83 outcomes, but does not expose the historical harness/test-source hashes for direct comparison. Therefore the R3 logs prove that the identified R3 harness passed; the evidence currently available to this reviewer does **not** independently prove that its harness and test sources are byte-identical to the exact ROUND130 harness/sources required by R3 §6.

**Required addendum:** compare the three R3 hashes above with the original ROUND130 local archive or raw test artifacts and publish the matching baseline hashes. If those originals are unavailable, retain the two R3 suite results as observed passes but mark strict historical-harness identity as unverified; do not silently claim byte identity.

### 3.5 Static checks and remaining diagnostics

- Final `git diff --check`: RC=0.
- Patch 22: `checkpatch --strict --no-signoff` RC=1, 0 errors / 3 warnings (new-file MAINTAINERS reminder, undocumented Huawei compatible, 130-column line). Patch 23 is clean. This is not a clean-zero checkpatch result and the warnings must remain visible.
- Bare-file DTS checkpatch RC=1 is a tool-input-format error, not a valid source style verdict; patch 22 is the applicable unified diff check.
- Historic ROUND130 checkpatch results for patches 18–21 are quoted, not rerun, as required.
- SPDX is correctly NOT_RUN/BLOCKED because `python3-ply` is missing and the taskbook forbids package installation.
- The raw Kconfig/object log labels the config delta as “42” while the displayed diff excerpt shows four removed unset-symbol lines and one added `CONFIG_GENDWARFKSYMS` line. Clarify what “42” counts in a small report addendum; the transformed config hash itself is recorded and matches the prior procedure.

## 4. Open Stage-A blockers — unchanged by R3

R3 is source/build evidence only. The following remain open and must not be inferred closed from a successful Image or DTB build:

1. The inherited zero-size bootloader-filled `/memory` placeholder is not a validated HOS4.3 RAM map; final ABL/EFI memory handoff and the 37-node HOS4.3 reserved-memory mapping remain unknown.
2. The `huawei,dby-w09` root-compatible binding gap remains; `vcc-voltage-level` is not consumed by the pinned ACK UFS parsing path.
3. `qcom,vccq-parent-supply` remains metadata only in the pinned ACK path; PM8150L S8 acquisition is not established.
4. PM8150 physical input-parent topology remains unknown; regulator-core dummy fallback is not proof of electrical wiring.
5. MMCX-to-MX / HOS ARC proxy semantics remain unresolved.
6. ABL boot-v2 / separate ramdisk / selected DTBO / AVB and vbmeta provenance remain unresolved.
7. No real UFS link startup, block-device enumeration, rail transition stress, suspend/resume or tablet boot was performed. Phase G remains NOT RUN.

No device operation, partition write, firmware extraction, package creation or Stage B work is authorized by this R3 evidence.

## 5. Recommendation to 1号 AI

Accept the R3 classification as **PARTIAL — IMAGE BUILD PASSED, KNOWN SCHEMA / DTB DIAGNOSTIC REMAINS**, subject to a narrow evidence addendum for the host-regression harness identity and the two minor log/report consistency disclosures above. Do not mark Stage A complete or boot-ready. Keep all memory, PMIC, ARC/MMCX and AVB/ABL gates open.

Per the R3 stop condition, this review does not start another round. Wait for 1号 AI to issue the next taskbook if further work is authorized.
