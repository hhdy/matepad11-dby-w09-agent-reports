# ROUND47 — ACK PM8150 regulator mode / DRMS capability review

Date: 2026-11-24

Status: **PINNED ACK DRIVER / REGULATOR CORE / DT BINDING REVIEWED. HOS4.3 ORIGINAL MODE-PROPERTY VALUES REMAIN UNKNOWN PENDING THE LOCAL ROUND13 FDT + DTBO AUDIT.**

## 1. Fixed source baseline

- Device: Huawei MatePad 11 (2021), DBY-W09, KONA / SM8250 v2.1.
- ACK tag: `android17-6.18.33_r00`.
- Immutable commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.

Exact source files and blob IDs:
- `drivers/regulator/qcom-rpmh-regulator.c`: `109f0aae09b1df431d2e14d45a64d115e87cdec4`.
- `drivers/regulator/core.c`: `39d317ad73a33c4aa27e179cc436d8bf4daf5bcc`.
- `drivers/regulator/of_regulator.c`: `32e88cada47a254c3b184f3d1d6d8c1dccdfcc28`.
- `Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml`: `4c5b0629aa3e622579b54a226785139a0b986079`.

## 2. What the DT properties actually do

Pinned ACK `of_regulator.c::of_get_regulation_constraints()` implements these distinct controls:

- `regulator-initial-mode`: maps the RPMh mode through the regulator descriptor's `of_map_mode` and stores a one-time `initial_mode`. During regulator registration, `set_machine_constraints()` calls the driver's `set_mode` once. It is not itself a dynamic load policy.
- `regulator-allowed-modes`: maps each value and populates `valid_modes_mask`; when non-empty, it also enables `REGULATOR_CHANGE_MODE`. This is the mode allow-list / constraint, not the trigger for DRMS by itself.
- `regulator-allow-set-load`: enables `REGULATOR_CHANGE_DRMS`. This authorizes consumer load notifications to participate in dynamic mode switching; it does not create hardware callbacks that the selected regulator driver lacks.
- The binding additionally declares `regulator-allow-set-load` dependent on `regulator-allowed-modes` for the PMIC regulator subnodes.

For PMIC5 LDO mode mapping:
- `RPMH_REGULATOR_MODE_HPM` maps to regulator-core `REGULATOR_MODE_NORMAL`.
- `RPMH_REGULATOR_MODE_LPM` maps to `REGULATOR_MODE_IDLE`.
- `RPMH_REGULATOR_MODE_RET` maps to `REGULATOR_MODE_STANDBY`.
- `FAST` is invalid for the PMIC5 LDO mode map.

For PMIC5 SMPS:
- HPM maps to `REGULATOR_MODE_FAST` / PWM.
- AUTO maps to `REGULATOR_MODE_NORMAL`.
- LPM maps to `REGULATOR_MODE_IDLE` / PFM.
- RET maps to `REGULATOR_MODE_STANDBY`.

## 3. ACK hardware-data mapping for DBY-W09 UFS-related rails

The mapping below follows the fixed ACK PMIC init tables, not the vendor HOS ARC graph.

| DBY-W09 rail | ACK PMIC table entry | HW data / ops | Automatic DRMS support | HPM threshold |
|---|---|---|---|---:|
| PM8150 S4 (UFS VCCQ2) | `pm8150_vreg_data[smps4]` | `pmic5_hfsmps510` / `rpmh_regulator_vrm_ops` | No | N/A |
| PM8150 L5 (QMP VDDA-PHY) | `pm8150_vreg_data[ldo5]` | `pmic5_nldo` / `rpmh_regulator_vrm_drms_ops` | Yes, via get_optimum_mode + set_mode | 30 mA |
| PM8150 L6 (UFS VCCQ + VDDP REF_CLK) | `pm8150_vreg_data[ldo6]` | `pmic5_nldo` / `rpmh_regulator_vrm_drms_ops` | Yes, via get_optimum_mode + set_mode | 30 mA |
| PM8150 L9 (QMP VDDA-PLL) | `pm8150_vreg_data[ldo9]` | `pmic5_nldo` / `rpmh_regulator_vrm_drms_ops` | Yes, via get_optimum_mode + set_mode | 30 mA |
| PM8150 L17 (UFS VCC) | `pm8150_vreg_data[ldo17]` | `pmic5_pldo` / `rpmh_regulator_vrm_drms_ops` | Yes, via get_optimum_mode + set_mode | 10 mA |
| PM8150L S8 (UFS VCCQ parent) | `pm8150l_vreg_data[smps8]` | `pmic5_hfsmps510` / `rpmh_regulator_vrm_ops` | No | N/A |

Important distinction: `rpmh_regulator_vrm_drms_ops` contains `get_optimum_mode` but does **not** contain `set_load`. ACK performs DRMS by summing active consumer load and calling the PMIC hardware `set_mode` callback. It is therefore inaccurate to say that the LDO hardware data implements a direct `set_load` operation.

The LDO thresholds come from the HW-data records:
- `pmic5_nldo.hpm_min_load_uA = 30000`.
- `pmic5_pldo.hpm_min_load_uA = 10000`.

The high-current SMPS record `pmic5_hfsmps510` selects `rpmh_regulator_vrm_ops`, which exposes `set_mode` / `get_mode` but neither `get_optimum_mode` nor `set_load`. As a result, the regulator core's DRMS helper returns success without performing an automatic mode decision for S4 / S8, even if a DT node were to set the DRMS permission flag.

## 4. Regulator-core DRMS decision path

Pinned `drivers/regulator/core.c::drms_uA_update()` behaves as follows:

1. If `REGULATOR_CHANGE_DRMS` is not allowed, return 0 without a mode change.
2. If the driver has neither `get_optimum_mode` nor `set_load`, return 0 without a mode change.
3. For the PMIC5 LDO DRMS ops, sum the load votes from enabled consumers and add `regulator-system-load`.
4. Since these ops have `get_optimum_mode` but not `set_load`, ask the driver for its preferred mode:
   - aggregate load >= that rail's HPM threshold: `REGULATOR_MODE_NORMAL` (PMIC HPM);
   - aggregate load < threshold: `REGULATOR_MODE_IDLE` (PMIC LPM).
5. Constrain the requested mode using `regulator-allowed-modes`, then call the driver's `set_mode`.

The core only recalculates this path on a consumer's changed load when that consumer's regulator handle is enabled. Disabled consumers' stored load does not count toward the aggregate.

Mode allow-list detail: `regulator_mode_constrain()` can fall back from a requested lower-power mode to a permitted higher-power mode (e.g. requested LPM can be clamped to HPM). It does not silently switch a high-load HPM request down to LPM if HPM is excluded; that path can fail with `-EINVAL`. Therefore a genuine HPM/LPM load policy needs both modes available, subject to actual platform evidence.

Another startup detail: if `regulator-initial-mode` is present, `set_machine_constraints()` applies it and does not take the alternate `regulator-system-load` initial-DRMS branch. Later consumer load changes can still trigger DRMS if the node grants DRMS and the selected HW ops support it.

## 5. Implications for the current DBY-W09 DTS draft

The current review-only `dts/dby-w09-ack18-board.dts.draft`:
- requests HPM initial mode on PM8150 S4, L5, L6, L9 and L17;
- does not currently set `regulator-allowed-modes` or `regulator-allow-set-load` on those nodes;
- defines PM8150L S8 with the HOS4.3 voltage window but no initial mode / allowed mode / DRMS properties.

Therefore:
- Those LDOs currently have a static HPM initial request in the draft, not an enabled automatic LPM/HPM policy.
- S8's 210 mA consumer load request cannot by itself switch its mode dynamically under the current ACK S8 HW ops.
- Adding `regulator-allow-set-load` by itself would not be sufficient for the LDOs: allowed modes must also be supplied, and the mode list must allow the required operating range.
- Do not mechanically add HOS4.2 reference properties to HOS4.3.

## 6. HOS4.2 public same-device reference — useful but not proof of HOS4.3

The public same-device Linux DTS (blob `e56b2abcef38a7a76933ead77dbd941fa63bfb49`) provides a cross-reference only:

- PM8150 UFS rails S4/L5/L6/L9/L17 are assigned HPM initial mode in that reference.
- Its `regulator-allow-set-load` plus LPM/HPM `regulator-allowed-modes` appears on PM8150L L6 and L9 nodes used for microSD, not on the PM8150 UFS L6 node.
- PM8150L S8 is configured with HPM initial mode but no DRMS permission/allowed-mode properties in that public DTS.

This public tree is a HOS4.2-based reference, not a decoded representation of the user's HOS4.3 base FDT or stock DTBO. None of those attributes can be promoted to a HOS4.3 fact without the pending local audit.

## 7. Exact remaining ROUND13 evidence requirement

The previous ROUND7 filtered inventory did not export `regulator-initial-mode`, `regulator-allowed-modes` or `regulator-allow-set-load`. The HOS4.3 values remain UNKNOWN.

When the local read-only ROUND13 task is run after ROUND12, inspect only the already-existing base boot FDT and relevant stock DTBO fragments; do not re-extract firmware or repeat unrelated audits. For each PM8150 / PM8150L UFS rail node, record presence/absence and decoded values for:

- `regulator-initial-mode`;
- `regulator-allowed-modes` (all array values and order);
- `regulator-allow-set-load`;
- `regulator-system-load`;
- relevant `regulator-state-standby`, `regulator-state-mem`, `regulator-state-disk` child properties and their `regulator-mode` / on-off settings;
- any DTBO overlay fragment that adds, replaces or deletes these properties.

Target set: PM8150 S4/L5/L6/L9/L17 and PM8150L S8; include other shared-supply consumers only where needed to understand an aggregate L6 load. Keep the exact node path and fragment-to-target association. If a property is absent from the examined base FDT and applicable overlay set, say NOT_FOUND_IN_INSPECTED_SCOPE, not globally absent.

Do not infer an active runtime regulator mode from an initial-mode property. It only documents the requested initial mode; later changes depend on consumer load votes, allow-list constraints, selected HW callbacks and actual runtime state.

## 8. Independent project gates unchanged

- ROUND12 AVB footer / vbmeta descriptor metadata remains the sole active local Agent task; this ROUND47 public-source review did not replace or interrupt it.
- ROUND13 local HOS4.3 mode/DRMS metadata extraction is queued after ROUND12; this report prepares the ACK-side interpretation and exact property checklist, not the local result.
- ROUND30 MMCX-to-MX corner equivalence remains unresolved.
- ROUND42/43 Huawei final FDT and classic-FDT vs Linux EFI-stub memory handoff remain UNKNOWN.
- ROUND40 VCCQ-parent / VDDP teardown ordering remains a separate gate.
- Full-tree patch apply, checkpatch, DTS/schema, DTB, final Kconfig, Kleaf build, runtime UFS probe, PMIC voltage/mode verification and actual 6.18.33 device boot are NOT_RUN.

No device, bootloader, local firmware image, protected branch or PR #1 was accessed or modified.

**Conclusion:** ACK 6.18.33 can dynamically switch the listed PM8150 NLDO/PLDO rails using the generic regulator DRMS path only when both the DT constraints and the rail's HW ops permit it. PM8150 S4 and PM8150L S8 retain manual set_mode support but no automatic DRMS callback. HOS4.3 property values remain unverified until ROUND13 local evidence is available.
