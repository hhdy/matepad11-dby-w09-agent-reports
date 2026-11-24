# ROUND38 — DBY-W09 UFS dual-GenPD patch-series manifest and validation matrix

Date: 2026-11-24

Status: **SCHEMA PATCH PAIR APPLIES TO EXACT PINNED SOURCE FILES; BOARD DTS AND DRIVER REMAIN DRAFTS.** This report consolidates the UFS MMCX route work from ROUND32–37 and defines the next full-tree integration sequence.

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
| 37 | `round37/0001-dby-w09-ufs-host-dual-genpd-dts.patch.draft` | Protected board DTS draft file | source blob `e86c8707c413a9376b1e332a94e292b86acde3e2`; patch blob `486654c8d0b1b785190253270f5e83f796f07362` | Both hunk contexts match; not applied |
| 33 | `round33/0001-scsi-ufs-qcom-sm8250-dual-genpd-required-opp.patch.draft` | ACK `drivers/ufs/host/ufs-qcom.c` | source blob `a80c6998406dbc88c25dbd9977699ba481207efe`; patch blob `454a4443035cf3451c87e2735f0b876d65d52f8b` | Both hunk contexts match; not applied |

Related reports:
- ROUND32 binding coverage / 8-clock single-reg description.
- ROUND33 dual-GenPD UFS driver design.
- ROUND34 pinned-source OPP / GenPD lifetime review.
- ROUND35 current board DTS single-domain integration gap.
- ROUND36 common binding maxItems constraint and scoped fix.
- ROUND37 DBY-W09 board DTS delta.

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

- ROUND33's include and probe hunks match the exact pinned `ufs-qcom.c` source at the declared old line positions; hunk old/new counts match.
- ROUND37's two hunks match the full current protected board DTS draft text at the declared old line positions; hunk old/new counts match.
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
- `ack18-dby-w09-dts-draft` remains unchanged; ROUND37 has not been applied.
- PR #1 remains open / Draft / unmerged.
- `firmware-audit-v1` remains unchanged; ROUND12 AVB metadata report has not appeared.
- ROUND12 remains the only local Agent task. Do not start more local tasks or change device state.
- No device connection, unlocking, flashing, partition writing, or boot testing was performed.

**Conclusion:** the schema patch pair is now a viable exact-source candidate and the UFS dual-domain integration has a precise patch order and validation matrix. This is not yet a compiled kernel, validated DTB, working MMCX vote, or bootable DBY-W09 image.
