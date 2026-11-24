# ROUND45 — Harden UFS dual-GenPD OPP validation across all entries

Date: 2026-11-24

Status: **ROUND33 DRAFT UPDATED; BOTH UNIFIED-DIFF HUNKS AND OLD-SIDE SOURCE CONTEXT MATCH THE PINNED ACK FILE. FULL-TREE APPLY / CHECKPATCH / BUILD REMAIN NOT_RUN.**

## 1. Fixed baseline

- Device: Huawei MatePad 11 (2021), DBY-W09, KONA / SM8250 v2.1.
- ACK tag: android17-6.18.33_r00.
- Immutable commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a.
- Exact source file: drivers/ufs/host/ufs-qcom.c.
- Exact source blob previously pinned by ROUND33/38: a80c6998406dbc88c25dbd9977699ba481207efe.

This is Stage A kernel-port work. The Android 17 DerpFest Stage B remains deferred until the device has actually booted the Stage A 6.18.33 kernel and passed storage/basic-hardware acceptance.

## 2. Why the patch was changed

ROUND44 confirmed that the core probe ordering is consistent with the ACK APIs, but found that the previous ROUND33 helper inspected only the first available child of the UFS OPP table.

The exact pinned SM8250 UFS table currently contains two available OPP entries, each with one required-opps reference. The old check happened to pass that fixed table, but it did not establish that every currently available or later-added OPP entry used the same valid required-opps provider/table relationship.

ROUND45 updates the draft so the validation is applied to every available OPP child before the domains are attached and before generic UFS initialization adds the OPP table.

## 3. Changes made to the ROUND33 patch draft

Updated artifact:

- kernel-baseline/round33/0001-scsi-ufs-qcom-sm8250-dual-genpd-required-opp.patch.draft
- Current Git blob SHA: 2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5
- Diffstat: 205 insertions in drivers/ufs/host/ufs-qcom.c.

### 3.1 Per-entry required-OPP validator

New helper: ufs_qcom_validate_required_opp().

For every available UFS OPP entry, it checks:

1. Exactly one required-opps phandle exists.
2. The referenced target node exists and is available.
3. The target is a child of an operating-points-v2 table node.
4. The table's parent is compatible with qcom,sm8250-rpmhpd.
5. The provider advertises exactly one operating-points-v2 table.
6. That provider table resolves to the exact same device-tree node as the table containing the required-opps target.

The exact-table node identity check remains in place; a compatible string alone is not accepted as proof that the correct table was referenced.

All node references acquired by parsing the required-OPP target, its parent table, provider parent and provider OPP-table phandle are released on both success and error paths.

### 3.2 Whole-table validator

New helper: ufs_qcom_validate_opp_table().

- Obtains the UFS OPP descriptor node using dev_pm_opp_of_get_opp_desc_node().
- Iterates every available child with for_each_available_child_of_node().
- Calls the per-entry validator for every child.
- Stops and releases the current child reference on the first invalid entry.
- Rejects an empty available OPP table.
- Releases the OPP descriptor node on every exit.

This makes the preflight contract independent of the current number of UFS OPP entries.

### 3.3 Explicit two-domain driver contract

The patch now documents its supported SM8250 UFS two-domain contract:

- index 0: qcom,sm8250-rpmhpd / RPMHPD_MMCX;
- index 1: qcom,gcc-sm8250 / UFS_PHY_GDSC.

The one-domain generic path remains unchanged. Unknown two-domain layouts fail closed. This is a deliberate fail-closed driver contract: the generic GenPD core skips automatic attachment when a consumer has multiple power-domains entries, so silently accepting an unknown two-domain layout could leave UFS without either domain attached.

DBY-W09 is the board currently adding this topology. The code does not claim that it has become a generic implementation for arbitrary multi-domain SM8250 UFS layouts.

## 4. Static patch verification performed

The current patch was fetched back from GitHub and both unified-diff hunks were parsed against the exact pinned ACK ufs-qcom.c source fetched from commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a.

| Hunk | Old lines | New lines | Count check | Old-side source match |
|---|---:|---:|---|---|
| Includes | 12 | 18 | PASS | PASS |
| Probe/helper insertion | 15 | 214 | PASS | PASS |

Other static assertions:

- Total patch additions reconcile to 205 lines: PASS.
- A whole-table for_each_available_child_of_node() loop exists: PASS.
- Exact provider-table pointer identity comparison exists: PASS.
- The required-OPP validator has explicit cleanup labels for provider, table and target-node references: PASS.
- Current patch diffstat matches the hunk arithmetic: PASS.

These checks establish that the patch file's declared hunk lengths and old-side contexts match the fixed source. They are not a substitute for running git apply --check on a complete ACK source checkout.

## 5. Validation not performed

The following remain NOT_RUN:

- git apply --check / git apply in a complete immutable ACK worktree.
- checkpatch.pl.
- C compiler / kernel object build.
- dt_binding_check / dt-schema.
- Combined DBY-W09 DTS preprocessing, dtc, dtbs_check and emitted DTB inspection.
- Kconfig resolver / olddefconfig / final .config audit.
- Kleaf / Bazel workspace sync or kernel image build.
- Device probe, MMCX performance-state observation, GCC GDSC state, UFS link startup, storage enumeration, runtime-PM suspend/resume or real boot.

No device, bootloader, firmware or local partition was accessed or modified.

## 6. Remaining independent blockers

- ROUND30: ACK SM8250 MMCX still has no established HOS4.3-equivalent MMCX-to-MX parent/corner behavior.
- ROUND42/43: Huawei HOS4.3's actual final FDT / classic-FDT versus EFI-stub memory handoff is still UNKNOWN; no guessed RAM ranges may be added.
- ROUND12: read-only AVB footer / vbmeta descriptor inspection remains the only active local Agent task.
- ROUND40: VCCQ-parent / VDDP companion supply driver sketch still has teardown-order concerns and is not part of this ROUND33 patch.

The protected branch ack18-dby-w09-dts-draft, firmware-audit-v1 and PR #1 were not changed.

## 7. Next sequence

1. Keep the updated ROUND33 patch as DRAFT.
2. In a disposable checkout of the exact ACK commit, apply the schema pair (ROUND32 then ROUND36), integrate the ROUND37 board DTS delta into a real source path, and then apply this hardened ROUND33 driver patch.
3. Run full-tree patch, checkpatch, dt-schema, DTB and Kconfig checks.
4. Close AVB and memory/boot-chain questions before selecting a boot-image packaging/test strategy.
5. Continue Kleaf full-image build work only with a reproducible pinned workspace and reviewed final configuration.
6. Do not start full DerpFest device/vendor/system integration until the 6.18.33 kernel has actually booted and passed Stage A acceptance.

**Conclusion:** The ROUND33 patch draft now validates every available UFS OPP entry and has exact hunk-count/source-context agreement with the pinned ACK driver file. The implementation remains uncompiled and untested; MMCX-to-MX, memory handoff and AVB are still separate gates.
