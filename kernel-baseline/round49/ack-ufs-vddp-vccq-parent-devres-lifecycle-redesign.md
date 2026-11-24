# ROUND49 — ACK UFS VDDP / VCCQ-parent supply lifecycle redesign

Date: 2026-11-24

## Scope and status

This report reopens the protected legacy patch *as a source-review problem only*. The protected branch `ack18-dby-w09-dts-draft` is not modified. The old patch sketch remains stale and must not be applied as-is.

Fixed ACK baseline:
- tag `android17-6.18.33_r00`
- commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

Public same-platform reference:
- `OnePlusOSS/android_kernel_oneplus_sm8250`
- commit `cad09e061ef6cf689a4a1e54d27562e0f042236a`

No source checkout was built, no patch was applied to a full tree, and no device was accessed. This is a lifecycle design review only.

## 1. Correct interpretation of the two UFS consumer supplies

The public KONA device DTS uses the same property pair and values as the DBY-W09 HOS4.3 mapping:

```dts
qcom,vddp-ref-clk-supply = <&pm8150_l6>;
qcom,vddp-ref-clk-max-microamp = <100>;
qcom,vccq-parent-supply = <&pm8150a_s8>;
qcom,vccq-parent-max-microamp = <210000>;
```

The KONA driver does **not** treat these two rails alike.

### VDDP REF_CLK — PM8150 L6

In KONA `drivers/scsi/ufs/ufs-qcom.c`:
- Parses `qcom,vddp-ref-clk`.
- Calls `ufs_qcom_enable_vreg()`.
- That helper calls `regulator_set_load()`, optionally `regulator_set_voltage()`, then `regulator_enable()`.
- On link-off suspend, it calls `ufs_qcom_disable_vreg()`; resume re-enables it when the selected PM level requires.
- KONA's default VDDP voltage range is 1.2V–1.2V. The DBY-W09 board maps VDDP to fixed PM8150 L6 at 1.2V.

VDDP therefore has an actual regulator enable reference, not merely a load hint. In the DBY-W09 DTS, L6 is also the generic UFS VCCQ supply. The VDDP reference can be balanced independently: disabling its consumer reference does not shut L6 off while the generic VCCQ consumer still holds its own enable reference.

### VCCQ-parent — PM8150L S8

In the same KONA driver:
- Parses `qcom,vccq-parent`.
- Calls `ufs_qcom_config_vreg(..., true)`, which sets load and optional voltage.
- It does **not** call `regulator_enable()` for this consumer.
- Suspend clears its load under a specific policy condition (`!auto_bkops_enabled`); resume restores the load.
- The VCCQ-parent path must not be converted into an unconditional regulator enable/disable pair merely because its name contains “parent”.

KONA's VCCQ-parent path also defaults its min/max voltage vote to 0/0, i.e. the UFS helper does not request a separate voltage range for this parent. Do not invent an S8 voltage vote in the ACK UFS helper.

Source: [KONA UFS driver](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/scsi/ufs/ufs-qcom.c).

## 2. Important caveat: load-only is not proof of an effective DRMS transition

A closer check of the same KONA source reveals an important limitation that must not be hidden:

- KONA `ufs_qcom_config_vreg()` calls `regulator_set_load()` for VCCQ-parent but does not enable that UFS consumer handle.
- KONA `drivers/regulator/core.c` implements `regulator_set_load()` by storing the load on that consumer handle, but calls `drms_uA_update()` only when that *same handle's* `enable_count` is non-zero.
- The public KONA RPMh regulator driver provides a `set_load` callback for mode-configured VRM resources, but that alone does not override the regulator-core enable-count gate.

Therefore the source proves that the KONA UFS code *submits and later clears* a load request; it does not prove that the 210mA request actually causes S8 mode switching when the UFS consumer handle is never enabled. The effective result may depend on other active consumers / board state or a version-specific framework change. Do not repeat the claim that this code necessarily switches S8 to AUTO.

For DBY-W09 ACK this caveat is even more restrictive: ROUND47 establishes that ACK PM8150L S8 is `pmic5_hfsmps510` with no `set_load` or `get_optimum_mode` callback. Its 210mA `regulator_set_load()` vote is therefore a successful no-op in the current fixed ACK driver. It does not enable S8 and does not implement HOS4.3's 200mA RET→AUTO policy.

ROUND14 has now exported the missing static S8 fields from the approved base-FDT work copy: `qcom,init-enable`, `regulator-boot-on`, `regulator-always-on` and the inspected suspend-state nodes are NOT_FOUND_IN_INSPECTED_SCOPE. This does not establish live enable state or the physical S8 input path. Do not schedule another FDT scan for these properties; ROUND14 is complete.

## 3. ACK teardown ordering

Fixed ACK .33 source proves this removal order:

1. `ufshcd_hba_init()` enables the generic UFS supplies before it calls the Qualcomm variant init.
2. If Qualcomm variant init fails, generic `ufshcd_setup_vreg(hba, false)` is called in the `out_disable_vreg` unwind path.
3. On normal HBA exit, `ufshcd_hba_exit()` calls `ufshcd_variant_hba_exit()` **before** `ufshcd_setup_vreg(hba, false)`.
4. The platform driver's remove path calls `ufshcd_remove(hba)`.
5. The driver core's unbind sequence calls the platform/bus `.remove()` callback before `device_unbind_cleanup()`; that cleanup then calls `devres_release_all()`.
6. ACK devres releases its recorded actions in reverse order. A custom action registered after the managed regulator get therefore runs before the managed regulator handle is put.

This gives a safe place for final managed VDDP cleanup: a devm action that runs only after `ufshcd_remove()` has completed generic UFS VCCQ shutdown, but before devm regulator handles are put.

Fixed-source anchors:
- ACK `drivers/ufs/core/ufshcd.c`, blob `2cf7aa8e0a9472f9024d4251ac2f9d7da830e219`
- ACK `drivers/ufs/host/ufs-qcom.c`, blob `a80c6998406dbc88c25dbd9977699ba481207efe`
- ACK `drivers/ufs/host/ufshcd-pltfrm.c`, blob `5ac7afe759346debfc2910fb219d8e491ba08b64`
- ACK `drivers/base/dd.c`, blob `2996f4c667c42f7915260339ca588cda8e5b391a`
- ACK `drivers/base/devres.c`, blob `9893d656302d9795911b7e524f300999c395fef4`
- ACK `drivers/regulator/devres.c`, blob `2cf03042fddf4263d05c95e29dd534003fb8246c`
- ACK `drivers/regulator/core.c`, blob `39d317ad73a33c4aa27e179cc436d8bf4daf5bcc`

The regulator API documents that every `regulator_enable()` must be balanced by `regulator_disable()` before `regulator_put()`; `regulator_put()` warns if the handle still has a non-zero enable count. A deferred devm action must therefore balance VDDP's explicit enable before the managed put runs.

## 4. Proposed storage-first ACK implementation policy

This is the recommended *design* for the initial storage milestone. It deliberately does not attempt to reproduce downstream runtime suspend/BKOPS policy yet.

### VDDP / L6
- Read/require `qcom,vddp-ref-clk-supply` to decide whether the downstream extension is present; when present, use mandatory `devm_regulator_get(dev, "qcom,vddp-ref-clk")`. If the phandle is declared but the regulator is not available, allow probe defer/failure instead of silently skipping it.
- Require a positive `qcom,vddp-ref-clk-max-microamp` value. The DBY-W09 board value is 100µA; use the board's fixed 1.2V L6 constraint rather than inventing a new voltage range.
- Register `devm_add_action_or_reset()` immediately after the managed regulator get, before load/enable. Then call `regulator_set_load()`, set the load flag only on success, call `regulator_enable()`, and set the enable flag only on success.
- The cleanup action disables VDDP, then clears its load. If disable fails, log and retain the load vote rather than clearing load while the enable reference may remain.
- On device removal, generic VCCQ has shut down before the action runs. The action also runs before `regulator_put()`; because the UFS core's HBA release and the variant host allocation actions were registered earlier, devres LIFO keeps both `hba` and `ufs_qcom_host` alive during the callback.

### VCCQ-parent / S8
- **Do not acquire S8 in the first ACK UFS driver patch.** Do not call `regulator_set_load()`, `regulator_enable()`, `regulator_disable()`, or `regulator_set_voltage()` for VCCQ-parent.
- ROUND14 found no static S8 init-enable / boot-on / always-on declaration in the inspected base FDT; fixed ACK HFSMPS510 has no DRMS callbacks, so a 210mA load-only request would be a no-op.
- Preserve `qcom,vccq-parent-supply` and its max-current metadata in the board binding only as a documented downstream topology extension, not as an initial driver action. The board S8 node keeps RET initial and RET/AUTO allowed; runtime enable state remains UNKNOWN.

### Error unwind

- If VDDP load setup fails after the cleanup action has been registered, the enable flag remains false and the deferred action has no rail-enable reference to drop.
- If VDDP enable fails after the load vote was accepted, the load flag remains true and the deferred action clears it.
- If `devm_add_action_or_reset()` registration itself fails, the action runs immediately while both state flags are still false.
- Do not call the cleanup path from `ufs_qcom_exit()` as well as the devm action; avoid double-disable / double-clear.
- If cleanup `regulator_disable()` fails, log it and retain the load vote; the subsequent managed regulator put will warn if the enable count remains non-zero. This failure recovery remains a known code-review limitation, not a runtime-tested condition.

### Suspend/resume for first boot

Do not add link-off suspend/resume voting in the first storage patch. Keep the VDDP/L6 reference enabled while the UFS HBA is bound and release it only after generic UFS rail shutdown at remove. The first ACK driver patch does not acquire or vote S8/VCCQ-parent at all. This is a conservative storage bring-up policy, not an assertion that it is the final power-saving policy. Once storage works, downstream KONA suspend/BKOPS behavior can be considered separately against exact ACK callbacks.

## 5. Rejected old implementation

The protected-branch sketch `patches/ufs-qcom-vccq-parent.patch.draft` is not to be applied as-is:
- it enables and disables both optional rails, while KONA uses enable/disable for VDDP but load-only for VCCQ-parent;
- it releases optional supplies inside `ufs_qcom_exit()`, which runs before ACK generic VCCQ supplies are disabled;
- the old sketch has no deferred cleanup action after core removal.
The protected branch remains untouched. This report and any future replacement sketch stay on `main` unless the user explicitly authorizes a protected-branch update.

## 6. Remaining evidence and verification gates

- ROUND14 completed the static S8 field extraction: no `qcom,init-enable`, `regulator-boot-on`, `regulator-always-on` or suspend-state nodes were found in the inspected base-FDT scope. Do not repeat that local scan.
- HOS4.3 live S8 enable state remains UNKNOWN; static FDT properties are not runtime reads. The physical S8 input-parent network remains unresolved.
- ACK S8 has no DRMS callback; the 210mA load-only vote would be a no-op, so it is omitted from the first ACK UFS driver patch.
- L6 input parent remains electrically unresolved; a regulator-core dummy supply does not establish the physical power tree.
- Full-tree apply, checkpatch, binding schema, dtc/dtbs_check, Kconfig resolution, Kleaf build, UFS boot, suspend/resume, and runtime regulator traces are all NOT_RUN.
- Stage A ACK 6.18.33 remains the only project milestone. Stage B DerpFest is deferred.


## ROUND51 correction — VCCQ-parent/S8 load-only path is not an implementation requirement (2026-11-24)

ROUND14 confirms the HOS4.3 S8 base-FDT child has qcom,set=<3>, init voltage 1.2 V and vendor init-mode RET, but no qcom,init-enable, regulator-boot-on or regulator-always-on property in the inspected scope. qcom,set chooses active/sleep request sets; it is not enable. No runtime S8 enable read was performed.

Fixed ACK pmic5_hfsmps510 uses rpmh_regulator_vrm_ops, which has no get_optimum_mode/set_load callback. Fixed ACK regulator_set_load() stores a per-consumer load value but only invokes drms_uA_update() when that same consumer's enable_count is nonzero. The KONA UFS VCCQ-parent handle is not explicitly enabled. Consequently the 210mA load-only vote is not a reliable mode vote, and in ACK it is a successful no-op. ROUND51 therefore supersedes any reading of the storage-first design as requiring an S8 load call: omit the S8 get/load/enable/disable path from the initial ACK UFS patch. Do not add an enable reference or boot-on/always-on constraint without new evidence. Keep runtime S8 enable state UNKNOWN and leave the VCCQ-parent DTS mapping as unused topology metadata only if the custom binding allows it.

The VDDP/L6 lifecycle conclusion is unchanged: acquire, set 100µA, enable; release with deferred cleanup after generic UFS VCCQ teardown. See ROUND51 for full source proof and exact links. No patch was applied or compiled.


## ROUND52 refinement — VDDP uses mandatory devm regulator get when its DTS property exists

The first ROUND52 driver helper explicitly checks for qcom,vddp-ref-clk-supply and then uses `devm_regulator_get(dev, "qcom,vddp-ref-clk")`, matching KONA's required get semantics. If the property is absent on another SM8250 board the feature is skipped; if it is present but the provider is unavailable, probe defers/fails instead of silently treating the rail as absent. This refinement does not change the delayed cleanup ordering. See ROUND52 patch 0002.
