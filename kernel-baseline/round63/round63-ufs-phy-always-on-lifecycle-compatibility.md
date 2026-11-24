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
- current Git blob SHA: `a06b7d3fc19e0b23895b0013ab9ac322d84cdda5`
- adds optional property state, managed teardown, and separate regulator enable/disable handling when the property is present.

Binding candidate:
- `kernel-baseline/round63/0002-dt-bindings-phy-qmp-ufs-vdda-phy-always-on.patch.draft`
- Git blob SHA: `a6668eebe293f9a35e9c08d6be4f37c4340e7ddd`
- declares the optional boolean so the strict QMP UFS PHY binding accepts the node.

Board draft correction:
- `dts/dby-w09-ack18-board.dts.draft`
- updated Git blob SHA: `c209d519614fb0ff89b042ce274191b20120a09a`
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


## 9. Static candidate hardening update (2026-11-24)

Before recording this update, the QMP candidate was rechecked against additional pinned header/source contracts:

- All **15** `regulator_bulk_data` lists in pinned `phy-qcom-qmp-ufs.c` put `vdda-phy` at index 0 and `vdda-pll` at index 1. The current SM8250 entries are 89900µA and 18800µA. The candidate still validates that the first supply is `vdda-phy` before using this special path.
- Pinned `include/linux/regulator/consumer.h` blob `56fe2693d9b2284d04ebae50165f9aa7b1b3fee4` confirms `regulator_bulk_data.init_load_uA` is a public field documented as the initial load applied by the bulk-get API.
- Pinned `include/linux/device.h` blob `26eb9a0157f836be303513eb2ffda7d492ca40ff` includes `linux/device/devres.h`; that header blob is `8c5f57e0d613492fd0b2ec97dd384181608192fc` and declares `devm_add_action_or_reset()`. The QMP source already includes `linux/platform_device.h`, which pulls in the device header. The candidate additionally adds explicit `linux/string.h` for its `strcmp()` validation.
- The final driver patch blob is now `a06b7d3fc19e0b23895b0013ab9ac322d84cdda5` (after correcting new-file anchors following the explicit string header addition).

A deterministic in-memory exact-context replay of the final candidate against the exact pinned blobs succeeded:
- Driver: **5/5 hunks exact**, declared old/new counts match, no nearest-context fallback.
- Binding: **1/1 hunk exact**, declared old/new counts match.
- Source blobs were `8af777f7ddd0385a6bb9d9b9563f0e6329699cd3` (driver) and `fba7b2549ddee7ee4e048277a11a7da053d52887` (binding).

This replay is not Git's `git apply --check` or an actual disposable-worktree application. It proves only that the candidate hunk contexts and line anchors match the fetched pinned text. No checkpatch, dt_binding_check, compile or hardware test has run.


### Board draft metadata refresh

After the initial ROUND63 board update, the explanatory comment was refined to say the pinned ACK SM8250 vreg list supplies the 89900/18800µA votes. Current review-only board DTS blob is `c209d519614fb0ff89b042ce274191b20120a09a`. No change was made to the protected DTS branch.


### Separate HOS4.3 boot-time proxy-vote gap remains open

ROUND63 does **not** implement the HOS4.3 temporary 100mA ARC proxy-consumer requests previously documented for PM8150 L5/L9 in ROUND48/51. The local evidence indicates those temporary votes are removed by the vendor `late_initcall_sync` path; ACK has no equivalent generic proxy-consumer helper. The new QMP PHY logic manages only the PHY consumer's own 89900µA active load and retained vdda-phy enable after first use. It does not create a 100mA boot-time proxy vote, does not reconstruct the HOS ARC parent/proxy graph, and does not claim full HOS4.3 power-policy equivalence.

This remains a separate boot sequencing / regulator-policy gate. Do not translate it into `regulator-system-load`, `regulator-always-on`, or a permanent load vote without evidence. The physical PM8150 L5 parent input is also unresolved.


### L5 DRMS intent and candidate text hygiene

The existing ROUND47/48 source review establishes that PM8150 L5 is a PMIC5 NLDO with `get_optimum_mode` and `set_mode` support, HPM threshold 30mA, and the board draft allows LPM/HPM with DRMS. Therefore the candidate's 89900µA active vote is above the HPM threshold, while a zero load vote can select LPM without disabling the output. This is source-contract reasoning only; no physical mode readback has been made.

A lightweight scan of the final driver patch's added lines found:
- 152 added lines;
- zero added lines longer than 100 characters;
- zero added lines with trailing whitespace.

This is only text hygiene, **not** `checkpatch.pl` or `git diff --check`.


### PHY provider removal boundary — stateless device link

A further pinned-source check found a lifecycle limitation that must remain explicit:

- ACK `drivers/phy/phy-core.c`, blob `04a5a34e7a950ae94fae915673c25d476fc071c1`: `phy_get()` adds a device link with `DL_FLAG_STATELESS`; `phy_put()` removes it.
- ACK `drivers/base/core.c`, blob `3099dbca234aba38bde00e5f4d2567121c8612d0`: `device_links_unbind_consumers()` ignores links without `DL_FLAG_MANAGED`.
- ACK `Documentation/driver-api/device_link.rst`, blob `ee913ae1637117b8479cd6670e4cce09ed1bc0ad`: a stateless link is intended when driver presence on the supplier is irrelevant and correct suspend/resume/shutdown ordering is needed; it does not give the core managed consumer-unbind behavior.

Therefore the ROUND63 cleanup action is ordered before the QMP PHY provider's managed regulator handles are released, but the stateless PHY link does **not** prove that manually unbinding the QMP PHY provider will first unbind every UFS consumer. This is a broader generic-PHY supplier-lifetime boundary, not introduced solely by ROUND63.

For normal UFS host removal, the consumer driver is expected to shut down the PHY and release its managed PHY reference before the provider is removed. Do not manually unbind the QMP PHY platform device while the UFS host remains bound. ROUND61 must review the exact normal remove path and device-link behavior, and report this boundary rather than claiming universal supplier-unbind safety. No forced-unbind test is authorized or required for the first boot milestone.


### Normal UFS consumer removal sequence verified

The pinned ACK removal path provides a normal consumer-first shutdown sequence:

1. `drivers/ufs/host/ufshcd-pltfrm.c`, blob `5ac7afe759346debfc2910fb219d8e491ba08b64`: `ufshcd_pltfrm_remove()` calls `ufshcd_remove(hba)`.
2. `drivers/ufs/core/ufshcd.c`, blob `2cf7aa8e0a9472f9024d4251ac2f9d7da830e219`: `ufshcd_remove()` stops the HBA and calls `ufshcd_hba_exit()`; the latter calls `ufshcd_variant_hba_exit()` before generic regulator/clock/HBA-supply teardown.
3. `drivers/ufs/host/ufs-qcom.c`, blob `a80c6998406dbc88c25dbd9977699ba481207efe`: Qualcomm `ufs_qcom_exit()` calls `phy_power_off()` and `phy_exit()`. The UFS device's devm PHY reference and stateless link are released during the subsequent devres unwind after the remove callback.

This proves the normal UFS host remove callback requests PHY power-off/exit before its `devm_phy_get()` reference is released. It does not make the stateless link a managed supplier-presence dependency; a separate manual unbind of the QMP PHY provider while UFS remains bound is still unsupported and must not be used as a test path. QMP provider removal after UFS consumer removal runs the ROUND63 cleanup action before its managed regulator handles are freed.
