# ROUND40 — UFS VCCQ-parent / VDDP lifetime and merge audit

Date: 2026-11-24

Status: **INTEGRATION ORDER ISSUE IDENTIFIED IN THE EXISTING SUPPLY PATCH SKETCH.** No source code patch was modified or applied in this round. The companion supply sketch must be revised before being merged with ROUND33.

## 1. Fixed ACK 6.18.33 initialization order

Pinned source: ACK tag android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a.

The exact UFS core sequence in drivers/ufs/core/ufshcd.c:
1. initializes/enables host controller rails and clocks;
2. calls ufshcd_setup_vreg(hba, true) for the standard UFS device VCC, VCCQ and VCCQ2 supplies;
3. calls ufshcd_variant_hba_init(), which invokes the Qualcomm ufs_qcom_init().

Therefore both vendor Host supplies in the current DBY-W09 DTS are acquired after standard VCCQ has already been enabled if they are initialized from ufs_qcom_init(). This matches the broad downstream Qualcomm variant-init placement, but it is important for power sequencing.

The exact remove sequence in ufshcd_hba_exit() is:
1. calls ufshcd_variant_hba_exit() (Qualcomm ufs_qcom_exit());
2. then calls ufshcd_setup_vreg(hba, false) to turn off the standard UFS supplies.

Within pinned ufs-qcom.c, ufs_qcom_exit() currently disables lane clocks, powers off/exits the PHY, and returns. It has no optional VCCQ-parent or VDDP fields because ACK does not currently consume those properties.

## 2. Why the current patch sketch needs a lifecycle change

The review-only patches/ufs-qcom-vccq-parent.patch.draft proposes to:
- enable VDDP and VCCQ-parent during ufs_qcom_init();
- disable VCCQ-parent and VDDP in reverse order from out_variant_clear and ufs_qcom_exit().

This is not yet safe to integrate as written. Because ufs_qcom_exit() is invoked before generic UFS VCCQ is disabled, directly disabling an actual VCCQ parent rail there may remove the parent while its child VCCQ consumer is still enabled. The exact hardware relationship implied by the vendor qcom,vccq-parent-supply property must not be guessed, but the driver cleanup order should not assume that disabling the parent before generic VCCQ teardown is always safe.

The initialization-failure path has a related ordering issue: ufshcd_hba_init() handles a variant-init error by first returning from ufs_qcom_init() and then disabling the generic UFS supplies. A manual disable inside ufs_qcom_init()'s out_variant_clear label happens before that core unwind.

## 3. Downstream source behavior is not uniform

A pinned LineageOS OnePlus SM8150 reference at commit 9f007fac27dce21d29d8230753b71d5634b8a00e was inspected:

- VDDP uses an enable helper that first configures regulator load/voltage and then calls regulator_enable(); it is disabled on appropriate link-off transitions.
- VCCQ-parent uses ufs_qcom_config_vreg() for load/voltage configuration. That helper calls regulator_set_load() and optional regulator_set_voltage(), but does not call regulator_enable() or regulator_disable().
- At suspend, that implementation clears the VCCQ-parent load vote only under a specific auto-BKOPS condition; resume reapplies it.
- Its ufs_qcom_exit() does not explicitly disable the VCCQ-parent regulator.

This is one downstream implementation, not proof of the HOS4.3 vendor driver's exact policy. ROUND23 records a different downstream implementation pattern that also enables/disables VCCQ-parent. The two patterns must remain distinct until the HOS4.3 semantics are established.

The current ACK PM8150L S8 regulator ops lack DRMS set_load/get_optimum_mode support (ROUND23/25). Therefore a 210 mA load vote can be a successful no-op under the current provider. That does not answer whether the S8 rail itself should receive an explicit enable reference.

## 4. Safer first-storage lifetime candidate

Before integrating the optional supply patch into the fixed ACK tree, prefer a cleanup design that keeps any explicitly enabled VCCQ-parent rail alive until generic UFS child rails have been turned off.

A candidate design for review:
- Acquire optional supplies from ufs_qcom_init() after generic UFS standard rails have been enabled.
- Track whether each optional regulator has actually been enabled and whether a load vote was applied.
- For any rail that is explicitly enabled and may be upstream of generic VCCQ, register a device-managed cleanup action after the successful enable rather than disabling it inside ufs_qcom_exit(). Driver devres cleanup runs after the remove callback has completed its UFS core teardown, including generic VCCQ shutdown.
- For probe failure, ufs_qcom_init() returns an error, the UFS core first unwinds standard rails, and the driver core then releases devres actions.
- Keep VDDP and VCCQ-parent cleanup policies separate; their downstream behavior and hardware relationships are not identical.
- For the initial storage milestone, it may be reasonable to keep optional rails active for the entire bound lifetime and defer link-off power savings. This is a conservative bring-up choice, not final power-management behavior.

This design still needs careful implementation: the cleanup action must only be registered after a valid reference is acquired, must be ordered before devm regulator_put, and must be idempotent across partial initialization. The exact HOS4.3 S8 enable policy remains UNKNOWN.

## 5. Interaction with ROUND33 dual-GenPD patch

The dual-GenPD helper runs in ufs_qcom_probe() before ufshcd_pltfrm_init(). The VCCQ-parent / VDDP handling runs later inside ufs_qcom_init(), which is called from generic UFS HBA initialization after standard UFS supplies are enabled.

Therefore there is no direct call-order overlap between:
- ROUND33: GenPD attach + required_dev mapping before OPP table creation;
- optional supplies: Host regulator acquisition during Qualcomm variant initialization.

The source patches do both touch drivers/ufs/host/ufs-qcom.c near different regions, and the optional supply patch also touches ufs-qcom.h and qcom,ufs-common.yaml. They must be rebased and integrated as one ordered series rather than independently cherry-picked without conflict review. The binding additions must be layered onto ROUND36's common-schema modifications, not applied by replacing the same file with an older copy.

## 6. Required next checks

- Replace the current optional supply patch sketch with a unified diff against exact ACK .33 source files before claiming it is apply-ready.
- Decide, based on HOS4.3 evidence, whether VCCQ-parent is load-only or must receive an explicit regulator enable reference; do not infer this from its property name alone.
- If explicit enable is used, defer disable until after generic VCCQ shutdown or provide another verified sequencing mechanism.
- Keep VDDP enable/disable and VCCQ-parent load/enable behavior separate.
- Add optional supply properties to qcom,ufs-common.yaml without overwriting ROUND36's compatible-specific power-domains conditional.
- Integrate with updated ROUND33 in a disposable full ACK worktree; run git apply --check, checkpatch, dt_binding_check, dtbs_check, Kconfig resolution, and compile.
- Runtime validation must cover cold probe, failed/deferred probe, UFS link startup, runtime suspend/resume, system suspend/resume, and removal.

## 7. Status boundaries

- ROUND33's updated dual-GenPD patch blob is 565090acbfe9aad00200b3cccbd64a8a45c7c4c3; it remains unapplied/uncompiled.
- The optional supply sketch remains on ack18-dby-w09-dts-draft and was not modified in this round.
- The protected DTS branch, PR #1 and firmware-audit-v1 were not changed.
- ROUND12 remains the only local Agent task.
- No device connection, flashing, partition write, or boot test was performed.

**Conclusion:** the dual-GenPD route and the optional UFS supply support are logically compatible in their probe ordering, but the existing optional-supply cleanup sketch can disable VCCQ-parent too early relative to generic VCCQ. The optional-supply work must be rewritten with separate VDDP/VCCQ-parent policies and a verified teardown lifetime before it is merged into the 6.18.33 driver patch series.
