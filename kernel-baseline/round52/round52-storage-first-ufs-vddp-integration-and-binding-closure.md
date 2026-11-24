# ROUND52 — Storage-first UFS VDDP integration and binding closure

Date: 2026-11-24
Baseline: ACK android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
Status: SOURCE-REVIEWED PATCH DRAFTS; NOT APPLIED / NOT BUILT

## 1. Decision after ROUND14 / ROUND51

ROUND14/51 settles the UFS optional-supply split:
- VDDP REF_CLK -> PM8150 L6: consume in the first ACK UFS patch as load 100µA + regulator_enable().
- VCCQ-parent -> PM8150L S8: do not acquire or request load, enable, disable, or voltage in the first ACK patch. ACK pmic5_hfsmps510 has no DRMS callback, so a 210mA regulator_set_load() is a no-op. No HOS4.3 static init-enable / boot-on / always-on property or runtime enable state is known. Preserve board S8 initial RET, but do not force it on.
- Keep qcom,vccq-parent-supply / max-microamp as source-topology metadata only; the initial ACK driver patch does not consume it.

## 2. Binding gap and schema draft

Fixed ACK qcom,ufs.yaml explicitly sets unevaluatedProperties: false. Its referenced qcom,ufs-common.yaml is permissive today, but the qcom VDDP and VCCQ-parent extension properties are not explicitly documented or typed in qcom,ufs.yaml. ROUND52 adds definitions for:
- qcom,vddp-ref-clk-supply and qcom,vddp-ref-clk-max-microamp;
- qcom,vccq-parent-supply and qcom,vccq-parent-max-microamp.

Patch: kernel-baseline/round52/0001-dt-bindings-ufs-vddp-vccq-parent-supplies.patch.draft
- Blob SHA: 949798446f6135844f5e2d841fca06a0d25ea6d6
- Depends on ROUND32 adding qcom,sm8250-ufshc to the qcom,ufs.yaml compatible list.
- Exact pristine source blob reviewed: qcom,ufs.yaml = 1dd41f6d5258014d59c8c8005bc54f7994351a52.
- Its two unified-diff hunks were checked against the patch text (5/26 and 3/16 context/new-line counts); no full-tree apply or dt_binding_check was run.

## 3. VDDP lifecycle driver patch draft

Patch: kernel-baseline/round52/0002-ufs-qcom-sm8250-vddp-refclk-managed-lifecycle.patch.draft
- Blob SHA: bf60bdda7cf0c679b35a4f8dac1676c63a9e3ce0.
- Fixed ACK source blobs reviewed: ufs-qcom.c = a80c6998406dbc88c25dbd9977699ba481207efe; ufs-qcom.h = 5f979daabd5323184eeee137cc8ecc076193979e.
- Intended patch order: ROUND33 dual-GenPD UFS driver draft first, then ROUND52-0002. Its include hunk expects the post-ROUND33 pm_domain/pm_opp include lines; header fields do not conflict with ROUND33.
- It reads qcom,vddp-ref-clk-max-microamp, uses devm_regulator_get(dev, "qcom,vddp-ref-clk") when the qcom,vddp-ref-clk-supply property exists, sets the load, and enables the supply before ufs_qcom_setup_clocks() powers up the Qualcomm PHY.
- It registers devm cleanup after devm_regulator_get(). The cleanup disables VDDP and then clears its load. The devres release order is after ufshcd_remove() completes generic UFS VCCQ shutdown and before the managed regulator handle is put.
- VDDP is held enabled for the entire bound lifetime in this first storage-focused iteration. Suspend/resume rail switching is intentionally deferred.
- State flags are set only after successful operations. If load setup fails, no vote is marked. If enable fails, deferred cleanup clears the successfully set load. If action registration fails, devm_add_action_or_reset invokes cleanup immediately while the state flags are still false.
- Cleanup is best-effort. If regulator_disable() fails, it logs and retains the load vote rather than lowering load while the enable reference may still be active. This failure path is not runtime-tested.

## 4. Combined source sequence

1. ROUND32: qcom,ufs.yaml compatible/clock/reg description.
2. ROUND36: qcom,ufs-common.yaml compatible-scoped dual-domain allowance.
3. ROUND52-0001: typed qcom VDDP/VCCQ-parent supply properties.
4. ROUND37: DBY-W09 board DTS delta, with power-domains index 0 MMCX and index 1 GCC UFS_PHY_GDSC.
5. ROUND33: UFS dual-GenPD required-OPP driver integration.
6. ROUND52-0002: VDDP managed supply lifecycle.

The qcom,vccq-parent-supply property remains binding metadata only; ROUND52 driver does not parse it. Full HOS ARC/MMCX-to-MX equivalence and the MMCX temporary proxy request remain independent power-domain/boot-handoff gates. Neither ROUND33 nor ROUND52 resolves those gaps.

## 5. Checks performed and not performed

Performed:
- Re-fetched the fixed ACK qcom,ufs.yaml, ufs-qcom.c and ufs-qcom.h blobs and checked all authored patch hunk line counts.
- Re-verified KONA UFS semantics: VDDP does load+enable and disable-then-clear-load; VCCQ-parent is load-only.
- Confirmed ROUND52-0002 is ordered after ROUND33 because its include context expects ROUND33's pm_domain/pm_opp additions.
- Inspected devm_regulator_get() and fixed ACK UFS variant init / remove placement.

NOT_RUN:
- Full-tree git apply / combined git apply --check.
- checkpatch.pl.
- dt_binding_check / dtbs_check / dtc.
- Final Kconfig/.config resolution.
- Kleaf/Bazel build.
- Image packaging, device boot, UFS enumeration/read/write, runtime power-state, suspend/resume or actual S8/VDDP measurements.

## 6. Agent requirement and next gate

No new Local Agent task is justified for ROUND52: these changes use already-known public ACK source and the existing ROUND13/14 local properties. Do not rescan FDT, EROFS or AVB. A future local task is justified only if a concrete implementation step requires a distinct fact unavailable from the existing reports.

Stage A ACK 6.18.33 remains the only milestone. Stage B DerpFest stays deferred until actual Stage A device boot and UFS/storage/basic-hardware acceptance. Protected ack18-dby-w09-dts-draft remains untouched; PR #1 remains Draft.


## ROUND52 source-contract addendum — regulator ID, DRMS trigger and cleanup ordering

A final fixed-ACK source pass confirms the custom regulator ID in the driver draft is exact:
- ACK drivers/regulator/of_regulator.c implements of_get_regulator() by constructing `<id>-supply` and parsing that property from the consumer node.
- Therefore `devm_regulator_get_optional(dev, "qcom,vddp-ref-clk")` resolves the existing board property `qcom,vddp-ref-clk-supply`, matching KONA's use of `devm_regulator_get(dev, vreg->name)` with vreg->name set to `qcom,vddp-ref-clk`.

The VDDP load-before-enable sequence also has the required ACK DRMS trigger:
- ACK drivers/regulator/core.c regulator_enable path increments the same handle's enable_count; when it becomes 1 and that handle has a nonzero uA_load, it calls drms_uA_update().
- regulator_set_load() by itself only updates DRMS when the handle is already enabled.
- Thus ROUND52's set_load(100) then regulator_enable() sequence is materially different from S8's load-only call: VDDP's first enable triggers the L6 DRMS aggregate, while S8 remains a no-op on fixed ACK due to no HFSMPS510 DRMS callback and no enable reference.

Source anchors:
- [ACK OF regulator consumer lookup](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/of_regulator.c#L615-L634)
- [ACK regulator enable / DRMS transition](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L2857-L2868)
- [ACK regulator_set_load handle enable-count gate](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L4955-L4964)

This addendum is still source review, not a compiled or runtime validation.
