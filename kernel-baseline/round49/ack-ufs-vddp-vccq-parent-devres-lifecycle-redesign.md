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

This makes S8 boot enable state and physical parent supply status a separate unresolved gate. ROUND13 did not export the S8 `qcom,init-enable`, `regulator-boot-on`, `regulator-always-on`, or complete physical input-parent context. The next local property scan must read only these already-existing fields from the approved FDT work copy.

## 3. ACK teardown ordering

Fixed ACK .33 source proves this removal order:

1. `ufshcd_hba_init()` enables the generic UFS supplies before it calls the Qualcomm variant init.
2. If Qualcomm variant init fails, generic `ufshcd_setup_vreg(hba, false)` is called in the `out_disable_vreg` unwind path.
3. On normal HBA exit, `ufshcd_hba_exit()` calls `ufshcd_variant_hba_exit()` **before** `ufshcd_setup_vreg(hba, false)`.
4. The platform driver's remove path calls `ufshcd_remove(hba)`.
5. The driver core's unbind sequence calls the platform/bus `.remove()` callback before `device_unbind_cleanup()`; that cleanup then calls `devres_release_all()`.
6. ACK devres releases its recorded actions in reverse order. A custom action registered after `devm_regulator_get_optional()` therefore runs before the managed regulator handle is put.

This gives a safe place for final optional-supply cleanup: a devm action that runs only after `ufshcd_remove()` has completed generic UFS VCCQ shutdown, but before devm regulator handles are put.

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
- Use `devm_regulator_get_optional(dev, "qcom,vddp-ref-clk")`.
- Apply the 100µA load vote; use the board's fixed 1.2V L6 constraint rather than inventing a new voltage range.
- Call `regulator_enable()`; set an explicit state flag only after success.
- Immediately register a `devm_add_action_or_reset()` cleanup action after the successful enable. The action must call `regulator_disable()` and clear the load vote, with error logging.
- Because the action executes after `ufshcd_remove()` returns, generic VCCQ's L6 consumer is already off before the VDDP enable reference is removed. The later devm regulator-put action then releases the handle.

### VCCQ-parent / S8
- Use `devm_regulator_get_optional(dev, "qcom,vccq-parent")`.
- Follow KONA's load-only shape: request the 210mA load, do **not** call `regulator_enable()` or `regulator_disable()`, and do not set a separate voltage.
- Register a deferred cleanup action that clears the load vote before the regulator handle is put.
- Explicitly document that fixed ACK HFSMPS510 lacks `set_load`; the vote is currently a no-op. Do not claim it enables the rail or reproduces HOS mode switching.
- Do not force S8 AUTO or RET from the UFS driver; its static mode choice is held in the DTS draft and still awaits confirmation of local S8 enable/power-tree semantics.

### Error unwind

- If the second (VCCQ-parent) get or load setup fails after VDDP has been enabled, return the error. The devm action will run after the generic UFS init unwind has disabled generic supplies.
- If custom cleanup action registration fails, `devm_add_action_or_reset()` executes the cleanup immediately. This is safe for VDDP while generic VCCQ still owns a separate L6 enable reference; for S8 it only clears the load vote.
- Never manually call the same cleanup path from `ufs_qcom_exit()` as well as a devm action; avoid double-disable / double-clear.
- If cleanup `regulator_disable()` fails, log it; do not silently mark the rail disabled. This failure case still needs review in a real patch because the managed regulator put will follow and the regulator API warns about unbalanced enable references.

### Suspend/resume for first boot

Do not add link-off suspend/resume voting in the first storage patch. Keep VDDP enabled and the VCCQ-parent load request stable while the UFS HBA is bound; release both only after generic UFS rail shutdown at remove. This is a conservative bring-up policy, not an assertion that it is the final power-saving policy. Once storage works, the downstream KONA suspend/BKOPS policy can be considered separately and adapted against exact ACK callbacks.

## 5. Rejected old implementation

The protected-branch sketch `patches/ufs-qcom-vccq-parent.patch.draft` is not to be applied as-is:
- it enables and disables both optional rails, while KONA uses enable/disable for VDDP but load-only for VCCQ-parent;
- it releases optional supplies inside `ufs_qcom_exit()`, which runs before ACK generic VCCQ supplies are disabled;
- the old sketch has no deferred cleanup action after core removal.
The protected branch remains untouched. This report and any future replacement sketch stay on `main` unless the user explicitly authorizes a protected-branch update.

## 6. Remaining evidence and verification gates

- S8 local `qcom,init-enable`, `regulator-boot-on`, `regulator-always-on`, and full power-parent facts are not yet present in the ROUND13 report. Need targeted local read-only extraction from the existing FDT work copy.
- HOS4.3 exact S8 runtime enable status is UNKNOWN; static FDT properties cannot be treated as live reads.
- ACK S8 has no DRMS callback; 210mA vote may be a no-op.
- L6 input parent remains electrically unresolved; a regulator-core dummy supply does not establish the physical power tree.
- Full-tree apply, checkpatch, binding schema, dtc/dtbs_check, Kconfig resolution, Kleaf build, UFS boot, suspend/resume, and runtime regulator traces are all NOT_RUN.
- Stage A ACK 6.18.33 remains the only project milestone. Stage B DerpFest is deferred.
