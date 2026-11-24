# ROUND36 — SM8250 UFS dual-domain schema limit and scoped fix

Date: 2026-11-24

Status: **EXACT PINNED SOURCE LIMIT CONFIRMED; SCHEMA PATCH DRAFT CREATED.** No schema checker or DT build was run.

## 1. Fixed source evidence

ACK tag: `android17-6.18.33_r00`  
Tag target commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

The exact target commit's `Documentation/devicetree/bindings/ufs/qcom,ufs.yaml` includes `qcom,ufs-common.yaml` under its `allOf` chain. The exact target commit's `qcom,ufs-common.yaml` currently contains:

```yaml
  power-domains:
    maxItems: 1
```

The common binding is the source of this restriction. The ROUND32 patch adds `qcom,sm8250-ufshc` compatibility and its eight-clock / one-reg-window rule, but it does not modify the included `qcom,ufs-common.yaml` power-domain maximum.

Therefore, the proposed DBY-W09 Host array containing both:
- `<&rpmhpd RPMHPD_MMCX>`
- `<&gcc UFS_PHY_GDSC>`

would violate the inherited `maxItems: 1` constraint unless the shared Qualcomm UFS binding is updated. A compatible-specific rule added only to `qcom,ufs.yaml` cannot relax a stricter `maxItems: 1` applied by an `allOf` reference; the constraint must be changed at its source.

Exact pinned-commit files (the URL uses the immutable target commit, not a moving branch):
- https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml
- https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/ufs/qcom,ufs.yaml

## 2. Proposed scoped schema change

Draft patch:
- `kernel-baseline/round36/0001-dt-bindings-ufs-allow-sm8250-dual-power-domains.patch.draft`

It makes two linked changes in `qcom,ufs-common.yaml`:
1. Raises the base `power-domains.maxItems` ceiling from 1 to 2.
2. Adds a compatible conditional:
   - `qcom,sm8250-ufshc`: `maxItems: 2`, preserving both existing one-domain boards and the proposed two-domain DBY-W09 topology.
   - all other Qualcomm UFS compatibles: `maxItems: 1`, preserving the previous constraint.

This is intentionally scoped; it does not require two domains on every SM8250 board. It only allows a second power-domain specifier on the SM8250 compatible. The driver continues to validate exact provider order and IDs at probe time.

The patch context was checked manually against the exact pinned-commit YAML. It has not been applied or parsed by dt-schema, and no full worktree `git apply --check` was run.

## 3. Combined integration dependency chain

A complete candidate integration now consists of:

1. ROUND32 — add SM8250 UFS compatible and its exact clock/reg layout to `qcom,ufs.yaml`.
2. ROUND36 — allow a second `power-domains` entry only for `qcom,sm8250-ufshc` via the common Qualcomm UFS schema.
3. DTS delta (not yet applied to the protected DTS branch):
   ```dts
   &ufs_mem_hc {
       power-domains = <&rpmhpd RPMHPD_MMCX>,
                       <&gcc UFS_PHY_GDSC>;
   };
   ```
4. ROUND33 — attach the two domains before UFS OPP table creation, mapping the single `required-opps` slot to MMCX.

The UFS PHY itself retains its existing GCC `UFS_PHY_GDSC` property. ROUND30's MMCX→MX parent/corner equivalence remains unresolved and is not changed by these patches.

## 4. Required validation

In a complete worktree at the immutable ACK tag:
- Apply ROUND32 + ROUND36 + ROUND33 in a disposable worktree.
- Run `git apply --check` for each patch and `checkpatch.pl` for the driver patch.
- Run `dt_binding_check` for `qcom,ufs.yaml` and its included `qcom,ufs-common.yaml`.
- Run `dtbs_check` for the combined DBY-W09 DTS.
- Ensure the final DTB has exactly two Host domains in the required order and the UFS PHY remains attached to GCC GDSC.
- Resolve Kconfig, build, then validate actual MMCX votes, GDSC operation, UFS link and storage.
- Do not call any of these validations PASS until they are actually run.

## 5. Boundaries

- No change was made to `ack18-dby-w09-dts-draft`.
- PR #1 remains Draft and untouched.
- No device, firmware, partition, or local file operation occurred.
- ROUND12 remains the sole local Agent task.
- No dt-schema, dtc, Kconfig resolver, kernel compile, runtime test or device boot was run.

**Conclusion:** the two-domain DTS design has a schema blocker in the exact ACK `.33_r00` common Qualcomm UFS binding. ROUND36 prepares a narrow compatible-scoped draft to unblock it, while preserving the former one-domain limit for other Qualcomm UFS controllers. This is a draft-level design fix, not a validation result.
