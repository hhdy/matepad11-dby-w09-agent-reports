# ROUND63 — DBY-W09 UFS PHY vdda-phy-always-on lifecycle compatibility

**Date:** 2026-11-24  
**Owner:** Primary AI  
**Status:** PINNED-SOURCE DIFFERENCE CONFIRMED; DRIVER + BINDING CANDIDATE DRAFTS CREATED; NO REAL PATCH APPLY / CHECKPATCH / DT-SCHEMA / COMPILE / HARDWARE TEST  
**Device:** Huawei MatePad 11 2021 DBY-W09 / KONA / SM8250 v2.1  
**Stage:** A — ACK 6.18.33 only

## 1. Finding summary

A previously unmodelled HOS4.3 UFS PHY property affects regulator lifetime:

`vdda-phy-always-on`

The local HOS4.3 ROUND8 DTBO inventory reports this boolean on stock overlay entry 8, fragment@63, target `/soc/ufsphy_mem@1d87000`. The same fragment also contains:
- `vdda-phy-supply`;
- `vdda-phy-max-microamp = 89900`;
- `vdda-pll-supply`;
- `vdda-pll-max-microamp = 18800`.

Exact local report:
- `firmware-analysis/round8/round8_summary.json`
- Git blob SHA: `2e5eec1be7d1364d90de7a8a500b516fcdddf3e1`
- Evidence boundary in that report is explicitly stock DTBO entry 8 only. It does not establish which overlay is selected in every current boot path or prove runtime regulator state.

The existing main-branch board DTS draft already models both analog supplies and their load values, but it omitted `vdda-phy-always-on`. This leaves the ACK candidate semantically different from the HOS4.3 UFS PHY policy when the UFS PHY is powered off.

## 2. Exact ACK 6.18.33 source behavior

Pinned ACK:
- tag: `android17-6.18.33_r00`
- commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

### 2.1 QMP UFS PHY driver ignores the property

File:
`drivers/phy/qualcomm/phy-qcom-qmp-ufs.c`

Git blob:
`8af777f7ddd0385a6bb9d9b9563f0e6329699cd3`

The fixed ACK driver's SM8250 regulator list is:

```c
static const struct regulator_bulk_data sm8250_ufsphy_vreg_l[] = {
    { .supply = "vdda-phy", .init_load_uA = 89900 },
    { .supply = "vdda-pll", .init_load_uA = 18800 },
};
```

Those load values already match the values in the HOS4.3 DTBO entry-8 inventory.

Current ACK behavior:
1. `qmp_ufs_probe()` obtains the regulator handles with `devm_regulator_bulk_get_const()`.
2. `qmp_ufs_power_on()` calls `regulator_bulk_enable()` for every regulator in the list, then enables PHY clocks.
3. `qmp_ufs_power_off()` powers down the PHY, disables clocks, then unconditionally calls `regulator_bulk_disable()` for every regulator in the list.
4. The driver never reads `vdda-phy-always-on`.

Consequently the ACK implementation disables the vdda-phy consumer enable reference at PHY power-off. That is not equivalent to the HOS4.3 property policy.

### 2.2 The current ACK binding also rejects the property

File:
`Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml`

Git blob:
`fba7b2549ddee7ee4e048277a11a7da053d52887`

The binding includes `qcom,sm8250-qmp-ufs-phy`, declares `vdda-phy-supply` and `vdda-pll-supply`, and ends with `additionalProperties: false`. It does not declare:
- `vdda-phy-always-on`;
- `vdda-phy-max-microamp`;
- `vdda-pll-max-microamp`.

The current board draft's two max-microamp properties therefore are not valid against this pinned ACK binding. The QMP UFS PHY driver does not read those DT properties: the SM8250 load values are compiled into its static `vreg_list`. Keeping redundant board properties would neither change the ACK load vote nor pass the strict binding without extra schema entries.

## 3. Downstream Qualcomm consumer semantics

A pinned downstream Qualcomm/OnePlus SM8150 kernel provides a concrete example of how the property is consumed:

- repository: `LineageOS/android_kernel_oneplus_sm8150`
- commit: `9f007fac27dce21d29d8230753b71d5634b8a00e`
- file: `drivers/phy/qualcomm/phy-qcom-ufs.c`
- blob: `f70871f45279ccb15f668ec7ce974c0f82d79004`

That driver:
- reads `vdda-phy-always-on` into the `vdda_phy` regulator state;
- normally enables vdda-phy on PHY power-on;
- if the property is set, PHY power-off calls `regulator_set_load(vdda_phy, 0)` instead of `regulator_disable(vdda_phy)`;
- continues to disable the other PHY regulator rails normally.

This is downstream implementation evidence for the intended Qualcomm consumer-level meaning. It is not the user's exact HOS4.3 driver binary and is not used as proof of current runtime state.

## 4. ACK regulator-core behavior relevant to a correct port

Pinned ACK source:
- `drivers/regulator/core.c`, blob `39d317ad73a33c4aa27e179cc436d8bf4daf5bcc`;
- `drivers/regulator/devres.c`, blob `2cf03042fddf4263d05c95e29dd534003fb8246c`.

Relevant semantics:
- `devm_regulator_bulk_get_const()` copies the static bulk data and acquires the regulator handles; `_regulator_bulk_get()` applies each positive `init_load_uA` through `regulator_set_load()`.
- `regulator_bulk_enable()` enables the consumer handles. The regulator core adds the load votes of enabled consumers when recalculating DRMS mode.
- `regulator_bulk_disable()` drops the consumer enable counts. The active load aggregation no longer includes a consumer whose enable count is zero. The stored `uA_load` value remains on the handle, so a subsequent enable can restore the vote.
- `regulator_set_load()` accepts a non-negative return as success; successful mode-setting implementations may return a non-negative mode value. The candidate handles only negative values as errors.

This allows the ACK port to preserve the consumer-level policy without forcing the PMIC provider globally always-on from its initial probe.

## 5. Proposed ACK adaptation

The preferred candidate keeps the existing behavior unchanged for every QMP UFS PHY node without the optional property.

When `vdda-phy-always-on` is present:
1. Validate that the first regulator in the selected PHY configuration is `vdda-phy` and that there is at least one further rail. The currently pinned Qualcomm PHY lists put `vdda-phy` first and `vdda-pll` second.
2. On the first PHY power-on, restore the vdda-phy load to its pinned `init_load_uA` and acquire one regulator enable reference.
3. Enable the remaining PHY rails (vdda-pll and any later entries) through the normal bulk helper.
4. On PHY power-off, disable the remaining rails normally, set the vdda-phy load vote to zero, and retain the one vdda-phy enable reference.
5. On later power-on, restore the load vote without adding a second enable reference, and then enable the other rails.
6. Register a device-managed cleanup action after the bulk regulator get. Reverse devres ordering makes the action run before the bulk handles are freed; it clears the load vote and balances the retained vdda-phy enable on provider removal.
7. If the property is absent, call the original bulk enable/disable path.

This is deliberately not translated to a provider-level `regulator-always-on` constraint. A global provider constraint could power L5 during regulator-provider registration, before the first UFS PHY use. The consumer-level property is better represented by retaining this one consumer's enable reference after first use and dropping its DRMS vote while idle.

The candidate uses the pinned SM8250 values already present in ACK's static regulator list (89900µA / 18800µA); it does not invent new values or parse vendor-specific max-microamp properties.

## 6. Candidate patch artifacts

Driver candidate:
- `kernel-baseline/round63/0001-phy-qcom-qmp-ufs-preserve-vdda-phy-always-on.patch.draft`
- current Git blob SHA: `b0f6b5f72d773bf9797b527ff4d2ab71060b6d54`
- adds optional property state, managed teardown, and separate regulator enable/disable handling when the property is present.

Binding candidate:
- `kernel-baseline/round63/0002-dt-bindings-phy-qmp-ufs-vdda-phy-always-on.patch.draft`
- Git blob SHA: `a6668eebe293f9a35e9c08d6be4f37c4340e7ddd`
- declares the optional boolean so the strict QMP UFS PHY binding accepts the node.

Board draft correction:
- `dts/dby-w09-ack18-board.dts.draft`
- updated Git blob SHA: `ceb12e3d869225f10e9d8d2beb277d66b4bb709c`
- now carries `vdda-phy-always-on;`
- removes `vdda-phy-max-microamp` and `vdda-pll-max-microamp`, because the ACK SM8250 QMP UFS configuration already provides those exact current loads and the binding/driver do not consume the board-side properties.

The board file remains a review-only `.dts.draft`, not a real ACK source-tree DTS input. The protected `ack18-dby-w09-dts-draft` branch has not been modified.

## 7. Remaining technical checks before adoption

This is source/design work only. The following have **not** run:
- `git apply --check` or actual `git apply` in the complete ACK worktree;
- `git diff --check`;
- `scripts/checkpatch.pl`;
- `dt_binding_check` for the modified QMP UFS PHY binding;
- `dtc` / `dtbs_check` on a real DBY-W09 source-tree DTS;
- C compilation of the QMP UFS PHY driver;
- runtime regulator load/enable/disable transitions;
- PHY power-cycle, UFS link resume or suspend/resume on hardware.

Required next tests:
1. Apply both candidate patches to the exact pinned source worktree and run checkpatch / diff checks.
2. Validate a positive SM8250 fixture with `vdda-phy-always-on`, and a negative fixture without the property to prove original behavior remains unchanged.
3. Run QMP UFS PHY `dt_binding_check` and `dtbs_check`.
4. Compile the QMP UFS PHY driver with the Stage-A Kleaf target.
5. Inspect UFS device-link/removal ordering and verify the cleanup action runs before regulator handles are released.
6. On hardware, validate first PHY power-on, PHY power-off (L5 remains enabled with zero vote), second power-on (load vote restored without duplicate enable count), and device removal/unbind.

Additional unresolved hardware gate: ROUND21 / ROUND11 report that the PM8150 L5 physical input supply relationship is not resolved in the inspected HOS4.3 base-FDT scope. The always-on policy patch does not solve or prove that electrical parent input. Do not invent a `vdd-supply`, `vin-supply` or `vph-pwr-supply` parent to silence warnings.

## 8. Project impact

ROUND63 adds a genuine Stage-A integration item. It should be inserted into the UFS source patch sequence after the existing UFS binding/driver drafts and before board-DTS validation:

- existing UFS schema / GenPD / VDDP series: ROUND32 → ROUND57 → ROUND36 → ROUND52-0001 → ROUND37 board delta (only when migrated into a real DTS file) → ROUND33 → ROUND52-0002;
- add the QMP UFS PHY binding candidate and QMP driver candidate before validating the final board DTS.

The exact order between independent QMP PHY and UFS Host patch files can be chosen for clean worktree application, but both must be present before the real board DTB is schema-validated.

This does not block the independent Image-only build work, except that the final QMP driver integration must be compiled before a boot candidate can be considered.

**Conclusion:** do not silently omit HOS4.3 `vdda-phy-always-on`. The ACK driver and binding currently lack the property. ROUND63 supplies a source-based candidate adaptation, but it remains unvalidated until real apply, schema, compile and hardware checks pass.
