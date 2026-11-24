# ROUND38 — DBY-W09 UFS dual-GenPD patch-series manifest and validation matrix

Date: 2026-11-24

Status: **SCHEMA PATCH PAIR APPLIES TO EXACT PINNED SOURCE FILES; BOARD DTS AND DRIVER REMAIN DRAFTS.** This report consolidates the UFS MMCX route work from ROUND32–40 and defines the next full-tree integration sequence.

## 1. Fixed baseline

- ACK tag: `android17-6.18.33_r00`
- Immutable target commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Target device: Huawei MatePad 11 2021 DBY-W09, KONA / SM8250 rev 2.1.
- This is Stage A kernel port work. Do not move to Android 17 DerpFest integration until the ACK-derived 6.18.33 kernel has actually booted and passed storage / basic hardware validation.

## 2. Patch artifacts and exact source identities

| Round | Artifact | Target | Source/patch identity | Current state |
|---|---|---|---|---|
| 32 | `round32/0001-dt-bindings-ufs-add-sm8250-compatible.patch.draft` | ACK `qcom,ufs.yaml` | source blob `1dd41f6d5258014d59c8c8005bc54f7994351a52`; patch blob `efe2d932da34716c631de22d89aba19730cc7f50` | Exact-file apply PASS |
| 36 | `round36/0001-dt-bindings-ufs-allow-sm8250-dual-power-domains.patch.draft` | ACK `qcom,ufs-common.yaml` | source blob `962dffcd28b44b3489be5615c75e7270a0c45dc4`; patch blob `dad87ef8dfefee6141b8a7949982c007c4a03b4a` | Exact-file apply PASS |
| 37 | `round37/0001-dby-w09-ufs-host-dual-genpd-dts.patch.draft` | Protected board DTS draft file | source blob `e86c8707c413a9376b1e332a94e292b86acde3e2`; patch blob `486654c8d0b1b785190253270f5e83f796f07362` | Exact single-file fixture `git apply --check` / apply / diff-check PASS; protected branch unchanged |
| 33 | `round33/0001-scsi-ufs-qcom-sm8250-dual-genpd-required-opp.patch.draft` | ACK `drivers/ufs/host/ufs-qcom.c` | source blob `a80c6998406dbc88c25dbd9977699ba481207efe`; updated patch blob `565090acbfe9aad00200b3cccbd64a8a45c7c4c3` | Both hunk contexts/counts match; exact provider OPP-table identity check added; not applied |

Related reports:
- ROUND32 binding coverage / 8-clock single-reg description.
- ROUND33 dual-GenPD UFS driver design.
- ROUND34 pinned-source OPP / GenPD lifetime review.
- ROUND35 current board DTS single-domain integration gap.
- ROUND36 common binding maxItems constraint and scoped fix.
- ROUND37 DBY-W09 board DTS delta.
- ROUND38 RPMhPD provider registration, deferred-probe rollback and required-OPP table identity review.
- ROUND40 UFS VCCQ-parent / VDDP teardown ordering and merge-lifetime audit.

## 3. Required patch order for a disposable full-source worktree

1. Start from the exact ACK tag / commit above. Do not use a moving `android17-6.18` branch or upstream Linux stable v6.18.33.
2. Apply ROUND32 to `Documentation/devicetree/bindings/ufs/qcom,ufs.yaml`.
3. Apply ROUND36 to `Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml`.
4. Integrate the ROUND37 board DTS delta into a real board DTS source path. ROUND37 currently targets the repository's review-only `.dts.draft` file; it is not yet an upstream kernel DTS path.
5. Apply ROUND33 to `drivers/ufs/host/ufs-qcom.c`.
6. Build the final combined DTS/DTB and inspect the actual emitted UFS Host `power-domains` array.

The schema patches are independent file changes. The board DTS and driver are coupled by the hard order contract:

- UFS Host power-domain index 0: RPMHPD MMCX.
- UFS Host power-domain index 1: GCC UFS_PHY_GDSC.
- UFS Host's sole `required-opps` slot maps to attached virtual GenPD index 0 (MMCX).
- UFS PHY's own GCC UFS_PHY_GDSC property remains unchanged.

## 4. What has actually passed

### Exact source patch application

A single temporary directory was populated with the two pristine schema files from the pinned ACK commit. Their local `git hash-object` IDs matched the exact GitHub source blob IDs in §2. Then:

- ROUND32 `git apply --check`: PASS.
- ROUND32 `git apply`: PASS.
- ROUND36 `git apply --check` after ROUND32: PASS.
- ROUND36 `git apply`: PASS.
- Combined `git diff --check`: PASS.

Both source files were then parsed with PyYAML. The relevant ROUND32 SM8250 clock/reg branch and ROUND36 dual-power-domain condition were composed into a focused JSON Schema Draft 7 check. Expected results all passed:
- SM8250 with 8 named clocks, one reg window, and 2 power domains: accepted.
- Original SM8250 one-domain layout: accepted.
- SM8250 with 3 domains, 9 clocks, a wrong eighth clock name, or 2 reg windows: rejected.
- Non-SM8250 Qualcomm UFS with 2 domains: rejected.

### Driver and board source context

- Updated ROUND33's include and probe hunks match the exact pinned `ufs-qcom.c` source at the declared old line positions; hunk old/new counts match. The helper now verifies that the provider's operating-points-v2 phandle is the exact table node containing the required-opps target.
- ROUND37's complete board DTS source fixture hash matched the protected source blob exactly; its exact patch file also matched the patch blob. `git apply --check`, `git apply`, and `git diff --check` passed on the isolated one-file fixture; the protected branch itself was not changed.
- ROUND34 confirms from pinned-source API review that the two-domain attach-list / required-dev mapping order is consistent with the UFS OPP initialization order and devres unwind sequence; repeated OPP configs use independent tokens and the later clock-only config does not clear required_dev.

## 5. What has NOT passed

The following are still NOT_RUN:
- `dt_binding_check` for the complete Qualcomm UFS schema graph.
- `dtbs_check` against the actual combined DBY-W09 DTS.
- DTS preprocessing, `dtc`, DTB/DTBO output inspection.
- `git apply --check` for ROUND33 in a complete kernel source tree.
- `checkpatch.pl` on ROUND33.
- Full Kconfig resolution / `olddefconfig` / final built-in verification.
- Kernel build and module build.
- Probe/deferred-probe, runtime-PM/device-link, MMCX vote, GCC GDSC, UFS link, storage enumeration, suspend/resume, and actual device boot.

The isolated environment used for these checks has no `dtc`, `dt-doc-validate`, `dt-validate`, Python `dtschema`, or `checkpatch.pl`. A full ACK source worktree and Android build toolchain were not materialized.

## 6. Remaining independent power-tree gate

ROUND30 remains open. HOS4.3 reports an MMCX ARC → MX ARC parent-supply edge, while the pinned ACK SM8250 RPMHPD descriptor uses a plain MMCX domain without an MX parent. The generic GenPD/OPP translation does not automatically reproduce the vendor dropout-voltage delta. Do not add an MMCX→MX parent or claim full HOS4.3 corner equivalence without the missing source evidence.

The dual-domain UFS request-routing change and MMCX→MX corner equivalence are separate validation gates.

## 7. Branch / device safety

- All ROUND32–38 reports and patch drafts are on `main`.
- `ack18-dby-w09-dts-draft` remains unchanged; ROUND37 was applied only to a local exact-blob fixture, not to the protected branch.
- PR #1 remains open / Draft / unmerged.
- `firmware-audit-v1` remains unchanged; ROUND12 AVB metadata report has not appeared.
- ROUND12 AVB report is uploaded but BLOCKED; ROUND13 and ROUND14 local audits are complete. The Local Agent queue is empty. Do not repeat FDT scans or create another local task unless a new, distinct local-only fact becomes necessary. Do not change device state.
- No device connection, unlocking, flashing, partition writing, or boot testing was performed.

**Conclusion:** the schema patch pair is now a viable exact-source candidate and the UFS dual-domain integration has a precise patch order and validation matrix. This is not yet a compiled kernel, validated DTB, working MMCX vote, or bootable DBY-W09 image.


## 9. ROUND38 provider registration and OPP-table identity review

- The pinned SM8250 RPMhPD descriptor maps RPMHPD_MMCX (ID 6) to the mmcx resource and installs the GenPD performance-state callback.
- RPMhPD probe configures and initializes domains; of_genpd_add_provider_onecell() creates indexed OPP tables before marking domains as having a provider and registering the provider with the OF GenPD core.
- With one operating-points-v2 phandle, the indexed OPP helper maps each provider index request to index 0, so the SM8250 RPMhPD domains use the declared common table.
- If a provider is not ready, GenPD attach returns deferred-probe state. dev_pm_domain_attach_list() rolls back already-attached virtual domains and device links if a later domain attach fails.
- ROUND33 now compares the OPP table node containing the required-opps target with the provider's operating-points-v2 phandle. Current ROUND33 patch blob SHA: `565090acbfe9aad00200b3cccbd64a8a45c7c4c3`.
- This is pinned-source review and source hunk checking only. No full-tree patch application, build, runtime PM test or hardware validation is claimed.

## 8. ROUND37 exact-blob board-DTS patch application update

The entire protected board DTS source blob (`e86c8707c413a9376b1e332a94e292b86acde3e2`) was reconstructed in a local temporary fixture and verified byte-for-byte with `git hash-object`. The repository's ROUND37 patch (`486654c8d0b1b785190253270f5e83f796f07362`) was also reconstructed and its hash matched. On this isolated exact-file fixture, `git apply --check`, `git apply`, and `git diff --check` all passed. The resulting temporary DTS contains the intended MMCX-first / GCC-GDSC-second ordering. This is a single-file exact-blob apply result, not a full ACK tree build or DT validation. The protected DTS branch remains untouched.

## 10. ROUND40 — companion UFS supply lifetime gate

Fixed ACK source shows `ufshcd_hba_exit()` calls the Qualcomm variant exit callback before it disables generic UFS VCC/VCCQ/VCCQ2. Therefore the current `patches/ufs-qcom-vccq-parent.patch.draft` must not be integrated unchanged if it directly disables VCCQ-parent in `ufs_qcom_exit()`: that would disable a possible parent before generic VCCQ teardown. Probe-failure cleanup inside `ufs_qcom_init()` can also happen before the core disables its generic rails.

A pinned downstream OnePlus SM8150 example treats VDDP and VCCQ-parent differently: VDDP has enable/disable handling, while VCCQ-parent uses load/voltage configuration and PM/BKOPS-dependent vote changes; its `ufs_qcom_exit()` does not explicitly disable VCCQ-parent. Another downstream family differs, so no single vendor policy can be assumed for DBY-W09 HOS4.3.

Do not merge the existing source sketch with ROUND33 yet. The supply patch needs an exact `.33_r00` diff and separate policies. If either rail gets an explicit enable reference, final cleanup should occur after generic UFS child rails have been disabled (for example via a device-managed action registered after enable, subject to full review of devres order); VDDP and VCCQ-parent must not share an assumed identical enable/disable policy. The HOS4.3 S8 enable semantics remain UNKNOWN. See `kernel-baseline/round39/ufs-vccq-parent-vddp-lifetime-and-merge-audit.md`.


## 7. ROUND45 driver patch revision

ROUND45 updated the ROUND33 driver artifact to Git blob SHA `2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5`. It validates every available UFS OPP entry rather than only the first available child, checks the target OPP node is available, requires the provider's single `operating-points-v2` table to be the exact target-containing table node, and balances OF node references on error and success paths.

The source-compatible hunk check against the pinned ACK `drivers/ufs/host/ufs-qcom.c` passed for both hunks (12/18 include lines; 15/214 probe/helper lines). Diffstat: 205 insertions. This remains a source-context verification, not full-tree `git apply`, checkpatch, compile, schema or runtime verification. Unknown SM8250 UFS two-domain layouts are explicitly fail-closed; the currently supported order is MMCX index 0, GCC UFS_PHY_GDSC index 1. Full details: `../round45/ack-ufs-dual-genpd-all-opp-validation.md`.


## ROUND52 integration series update (2026-11-24)

ROUND52 adds the downstream UFS supply binding and VDDP lifecycle changes. The intended end-to-end source sequence is now:

1. ROUND32: add `qcom,sm8250-ufshc` selection/compatible and its clock/reg description in `qcom,ufs.yaml`.
2. ROUND36: allow the SM8250-specific two-domain UFS Host layout in `qcom,ufs-common.yaml` while retaining one domain for other Qualcomm compatibles.
3. ROUND52-0001: add and type `qcom,vddp-ref-clk-supply`, `qcom,vddp-ref-clk-max-microamp`, `qcom,vccq-parent-supply`, and `qcom,vccq-parent-max-microamp`; require positive max-load values when their supply phandles are present.
4. ROUND37: DBY-W09 board DTS delta, MMCX domain index 0 + GCC UFS_PHY_GDSC index 1, plus the board's VDDP/VCCQ-parent supply declarations.
5. ROUND33: UFS dual-GenPD attach and required-opps -> MMCX mapping in `ufs-qcom.c`.
6. ROUND52-0002: VDDP/L6 managed get + load + enable + deferred cleanup. It is written against the post-ROUND33 `ufs-qcom.c` include block and leaves S8/VCCQ-parent unconsumed by the initial ACK driver.

ROUND52 artifacts:
- `kernel-baseline/round52/0001-dt-bindings-ufs-vddp-vccq-parent-supplies.patch.draft` — blob `c0ac84067a900022a077c748b7abb10345f1295f`.
- `kernel-baseline/round52/0002-ufs-qcom-sm8250-vddp-refclk-managed-lifecycle.patch.draft` — blob `fb34fbc9701bc7e7b56bb9078ee98c0cdd8caf78`.
- Design report: `kernel-baseline/round52/round52-storage-first-ufs-vddp-integration-and-binding-closure.md`.

A source-backed in-memory unified-diff simulation was performed against exact pinned ACK pristine files and the protected branch's unchanged board DTS file (read-only). In the order above, all patch contexts and declared line counts matched: ROUND32 3/3 hunks; ROUND36 2/2; ROUND52-0001 2/2; ROUND37 2/2; ROUND33 2/2; ROUND52-0002 header 1/1 and driver 3/3. This is **context/order simulation only**, not an actual Git worktree `git apply`, schema validation or build. Full-tree apply/checkpatch/dt-schema/dtc/Kconfig/Kleaf build/boot remain NOT_RUN.

The VDDP patch uses mandatory `devm_regulator_get(dev, "qcom,vddp-ref-clk")` only when `qcom,vddp-ref-clk-supply` exists. It registers its state-flagged cleanup action immediately after the managed get; the action is released after `ufshcd_remove()` has shut down generic VCCQ and before `regulator_put()`. S8 has no enable or mode vote in this first driver patch.


ROUND52-0002 lifetime refinement: the cleanup callback's `host` and `host->hba` remain valid during devres release. `ufshcd_alloc_host()` registers its `scsi_host_put` action before variant init; the variant's `devm_kzalloc()` action and then the VDDP cleanup action are registered later. ACK devres releases LIFO, so cleanup runs before either object storage is released, while also running after `ufshcd_remove()` has completed generic VCCQ shutdown.

## ROUND52 final hunk-position correction

The latest ROUND52-0002 driver patch blob is fb34fbc9701bc7e7b56bb9078ee98c0cdd8caf78. Its final third C-file hunk is anchored at @@ -1584,5 +1656,9 @@, after the +1 include and +71 VDDP-helper deltas. The earlier provisional new line 1654 has been corrected.

The final strict in-memory application pass requires each hunk to match both its declared old-side context at the precise old line plus accumulated preceding deltas and its declared newStart equal to oldStart plus accumulated deltas. All 15 hunk applications pass without fuzz/nearest-match fallback. This is not a real git apply or full worktree test; full-tree apply, checkpatch, schemas, DTB, Kconfig and build remain NOT_RUN.

The VDDP cleanup callback's host and host->hba pointers also remain valid during devres: the HBA release action and variant devm allocation are registered before the VDDP cleanup action, so reverse-order release runs cleanup first, after generic UFS VCCQ teardown but before either object storage is freed.


## ROUND57 — independent-review schema correction (2026-11-24)

ROUND54 independently identified that ROUND32's SM8250-specific branch sets exactly eight `clocks` but leaves the `clock-names` array count at the common schema's 7..9 range. The branch already enumerates exactly eight positional names, and the pinned SM8250 DTSI has exactly eight clocks/names.

The primary AI accepted R54-001 as a valid P3 schema-hardening correction and created a separate follow-up draft, leaving the historical ROUND32 file and SHA unchanged:

- `kernel-baseline/round57/0001-dt-bindings-ufs-sm8250-clock-names-exact-count.patch.draft`
- Report: `kernel-baseline/round57/sm8250-ufs-clock-names-exact-count-follow-up.md`
- Second-AI review report: `ai-parallel/round54/ROUND54_REVIEW.md` on branch `ai-parallel/round54-ufs-review`
- Second-AI candidate reviewed: `ai-parallel/round54/candidates/0001-qcom-ufs-sm8250-clock-names-exact-count.patch`, blob `6f3715c8b068556baf2993477c2387df98f8a574`.

**Corrected intended series order:**
1. ROUND32 — SM8250 compatible / eight-clock base binding branch.
2. ROUND57 — require exactly eight `clock-names`.
3. ROUND36 — compatible-scoped dual-power-domain schema support.
4. ROUND52-0001 — VDDP / VCCQ-parent binding properties.
5. ROUND37 — board DTS delta, only after migration into a real kernel DTS source path.
6. ROUND33 — UFS dual-GenPD / required-OPP driver.
7. ROUND52-0002 — VDDP managed lifecycle.

No full-tree apply or dt_binding_check/dtbs_check was performed for ROUND57. The follow-up is a draft, not a validation PASS. Full integration/build and device gates remain NOT_RUN.

## ROUND59 — complete ordered exact-source patch simulation (2026-11-24)

ROUND59 fetched each source file at the exact ACK commit and verified all source blob IDs against the existing recorded identities:
- `qcom,ufs.yaml`: `1dd41f6d5258014d59c8c8005bc54f7994351a52`
- `qcom,ufs-common.yaml`: `962dffcd28b44b3489be5615c75e7270a0c45dc4`
- `ufs-qcom.c`: `a80c6998406dbc88c25dbd9977699ba481207efe`
- `ufs-qcom.h`: `5f979daabd5323184eeee137cc8ecc076193979e`
- protected board draft fixture: `e86c8707c413a9376b1e332a94e292b86acde3e2` (read-only).

The corrected ordered list was replayed in-memory against those exact source contents:
ROUND32 → ROUND57 → ROUND36 → ROUND52-0001 → ROUND37 (review-only board fixture) → ROUND33 → ROUND52-0002.

All **16/16 hunks** matched the exact old-side context and declared new line anchor, with no fuzz / nearest-context fallback. ROUND52-0002 was routed to its two real target files: `ufs-qcom.h` (one hunk) and `ufs-qcom.c` (three hunks). A post-application text assertion set confirmed the intended compatible, eight-clock names, dual-domain schema, supply binding, MMCX-first/GCC-second draft topology, required-OPP mapping and VDDP lifecycle fields. A lightweight scan found no trailing whitespace among 367 added lines.

This was an **in-memory exact-context simulation**, not a real Git worktree application. Do not label it `git apply --check` or `git diff --check`. Full-tree Git apply/diff-check, checkpatch, dt-schema, DTB, Kconfig, Kleaf and compile remain NOT_RUN.

### ROUND57 correction identified by ROUND59

The previous ROUND57 blob `f282a695ed1201298f29a54ff0871084d995b3f2` had malformed hunk counts (declared 6/8; actual 13/15) and the wrong post-ROUND32 anchor (163 rather than 165). The canonical main patch is corrected to `@@ -165,13 +165,15 @@`, blob `3656f05ad01d54452b83591b762faaa71a16f592`. Use this corrected blob only.

Full evidence: `kernel-baseline/round59/round59_ufs_patch_series_exact_source_integration.md`.
