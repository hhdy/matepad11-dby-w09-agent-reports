# ROUND77 — 1号 AI second-pass source review of 2号 AI UFS / QMP PHY integration

**Date:** 2026-11-25  
**Review owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Source baseline:** ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Review type:** read-only fixed-source review; no patch or branch changes

## 1. Scope and verdict

This is an independent second-pass review of the UFS dual-GenPD, UFS VDDP REF_CLK consumer and QMP UFS PHY `vdda-phy-always-on` implementation recorded on the 2号 AI branch.

**Verdict: PASS for the reviewed normal-path source semantics, with minor teardown/error-path robustness notes.** The key required-OPP provider/table identity check, UFS VDDP shutdown ordering and QMP PHY retained-rail/load behavior are consistent with the pinned ACK implementation reviewed below.

This verdict is limited to source semantics. It is **not** a full merge approval, complete hardware power validation, DTB/schema validation, board bring-up or device boot acceptance. No files on the 2号 AI branch or protected DTS branch were changed by this review.

## 2. Reviewed implementation artifacts

2号 AI implementation branch: `ai-parallel/stagea-port-until-boot`.

- [ROUND33 UFS dual-GenPD driver patch](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai-parallel/stagea-port-until-boot/kernel-baseline/round61/patches/round33-checkpatch-clean.patch)
- [ROUND52 VDDP REF_CLK consumer patch](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai-parallel/stagea-port-until-boot/kernel-baseline/round61/patches/round52-0002-checkpatch-clean.patch)
- [ROUND63 QMP UFS PHY always-on patch](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai-parallel/stagea-port-until-boot/kernel-baseline/round61/patches/round63-0001-phy-qcom-qmp-ufs-always-on.patch)
- [ROUND63 integration notes](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai-parallel/stagea-port-until-boot/kernel-baseline/round61/round63-ufs-phy-integration.md)

## 3. UFS required-OPP provider and dual-GenPD validation

The pinned SM8250 DTS structure confirms the assumptions used by `ufs_qcom_validate_required_opp()`:

1. `ufs_mem_hc` owns `ufs_opp_table`.
2. Each available UFS OPP entry has one `required-opps` reference to an RPMhPD OPP node such as `rpmhpd_opp_low_svs` or `rpmhpd_opp_nom`.
3. Each RPMhPD OPP node is a child of `rpmhpd_opp_table`.
4. `rpmhpd_opp_table` is nested under the `rpmhpd: power-controller` provider node.
5. The provider's `operating-points-v2` phandle points back to that exact `rpmhpd_opp_table`.

Therefore walking from the required-OPP node to its parent OPP table and then to the parent power-controller, followed by exact comparison of the provider's `operating-points-v2` target with the containing table, matches the actual pinned tree. The review found no false parent/sibling assumption in this check.

The two-domain attach strategy is also aligned with the known topology: MMCX is attached at index 0 for the single required-OPP slot, and GCC `UFS_PHY_GDSC` remains the second direct domain. The helper restricts the special path to the SM8250 UFS compatible and rejects unknown two-domain layouts instead of guessing. This preserves the generic single-domain path.

The placement is also correct relative to the ACK UFS probe sequence: the Qualcomm probe helper runs before `ufshcd_pltfrm_init()`, while that platform helper parses/initializes the UFS OPP table later. The pinned `dev_pm_opp_set_config()` contract requires configuration before OPPs are initialized. The returned attach-list count is checked for exactly two domains; the OPP required-device mapping is registered as a devres action after the domain-attach resource, so OPP configuration is cleared before those attached GenPD devices are detached. The required-dev index is 0, matching the only required-opps entry. The later generic UFS clock-only OPP configuration is independently managed and does not overwrite that required-dev mapping.

Pinned API references: [`drivers/opp/of.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/opp/of.c) and [`drivers/opp/core.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/opp/core.c).

**Result: PASS (source-structure and intended mapping).** This does not establish HOS4.3 MMCX→MX voltage-corner equivalence; ROUND25 explicitly leaves that translation/dropout behavior unresolved. Do not add a bare MMCX→MX parent or invent corner conversion.

Pinned source: [`arch/arm64/boot/dts/qcom/sm8250.dtsi`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/boot/dts/qcom/sm8250.dtsi).

## 4. VDDP REF_CLK consumer cleanup order

The VDDP patch registers its cleanup action after `devm_regulator_get()`, and after the UFS HBA / Qualcomm host allocations have already been registered with devres.

Pinned ACK teardown order is:

1. platform remove calls `ufshcd_pltfrm_remove()`;
2. `ufshcd_remove()` calls `ufshcd_hba_exit()`;
3. `ufshcd_hba_exit()` calls the Qualcomm variant exit first;
4. the generic UFS supply teardown then disables the generic UFS rails, including VCCQ;
5. after the remove callback returns, devres executes the later VDDP cleanup action before releasing its managed regulator handle and before earlier host/HBA allocations.

Thus the VDDP consumer does **not** turn off the VCCQ-parent rail from inside `ufs_qcom_exit()`, and its normal cleanup occurs after generic VCCQ shutdown. The ordering resolves the specific ROUND40 concern for the VDDP consumer. The current patch does not claim to manage the separate VCCQ-parent/S8 rail's physical input path.

Because L6 DRMS load is aggregated among enabled consumers, the VDDP 100 µA vote is applied on the UFS host consumer while the handle is enabled; it can coexist with the generic VCCQ consumer's load request. The pinned regulator core only recalculates DRMS for a changed load on an enabled consumer.

**Result: PASS (normal remove ordering and load-vote model).** Physical S8 parent wiring, voltage margin and actual hardware enable behavior remain separate board-level evidence gates.

Pinned sources:
- [`drivers/ufs/core/ufshcd.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c)
- [`drivers/ufs/host/ufshcd-pltfrm.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufshcd-pltfrm.c)
- [`drivers/ufs/host/ufs-qcom.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf0563c5fcbdc9a/drivers/ufs/host/ufs-qcom.c)
- [`drivers/regulator/core.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf0563c5fcbdc9a/drivers/regulator/core.c)

## 5. QMP UFS PHY retained vdda-phy behavior

The QMP patch limits the special handling to a DT node that explicitly declares `vdda-phy-always-on`, verifies that `vdda-phy` is the first configured PHY regulator and requires at least one additional rail. On the normal path:

- first PHY power-on sets the configured active load and takes one persistent enable reference on `vdda-phy`;
- subsequent PHY power cycles do not take duplicate enable references;
- the remaining PHY rails (including `vdda-pll`) continue to use the normal bulk enable/disable path;
- PHY power-off clears the active load vote but deliberately retains the `vdda-phy` enable reference;
- a device-managed action balances that retained enable before the managed regulator handles are released.

The pinned regulator core confirms that load votes from a disabled consumer do not contribute to DRMS; when the retained consumer is enabled, its requested load participates. The bulk regulator helpers unwind partially enabled/disabled lists on failure, matching the patch's intended normal retry behavior.

The cleanup action is registered after the managed regulator bulk-get and before later PHY/provider resources. Devres LIFO ordering therefore tears down later PHY/provider resources, runs the retained-`vdda-phy` cleanup, and only then releases the regulator handles.

The corresponding binding patch adds `vdda-phy-always-on` as an optional boolean in a schema with `additionalProperties: false`, so explicitly declaring it is necessary and sufficient for the new property to be accepted. The 2号 AI's hosted Phase-B record reports two positive PHY fixtures (property absent and empty boolean present) with empty diagnostics, plus one negative fixture (cell-valued property) rejected as expected. This is corroborating test evidence from the 2号 AI branch, not a new test run by 1号 AI.

**Result: PASS (normal power-on, power-off and managed cleanup ordering).**

Pinned sources:
- [`drivers/phy/qualcomm/phy-qcom-qmp-ufs.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/phy/qualcomm/phy-qcom-qmp-ufs.c)
- [`drivers/phy/phy-core.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/phy/phy-core.c)
- [`drivers/regulator/core.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf0563c5fcbdc9a/drivers/regulator/core.c)

## 6. Minor error-path and operational notes

These are robustness issues to track, not evidence of a normal-path bring-up failure:

1. **QMP retained-rail cleanup failure accounting:** `qmp_ufs_vdda_phy_cleanup()` clears its local enabled flag even if `regulator_disable()` fails. A failed regulator disable can leave the regulator enable reference outstanding; subsequent managed `regulator_put()` may therefore trigger the regulator core's unbalanced-enable warning. Preserve/report the failed state rather than representing the reference as successfully balanced.
2. **QMP power-off return behavior:** the patched `qmp_ufs_power_off()` logs a regulator-disable/load-clear error but returns success. The baseline also ignored the bulk-disable return, so this is not wholly new, but the new load-vote failure can leave a stale request. Consider propagating the error where the PHY API contract permits, or explicitly retain a diagnostic state.
3. **VDDP disable failure:** the VDDP cleanup callback returns early if regulator disable fails, intentionally avoiding clearing the load while the rail may still be enabled. This is safer than falsely clearing the vote, but managed release may still report an outstanding enable reference. Keep this as an error-path limitation; no failure injection was run.
4. **PHY supplier unbind:** the pinned PHY core creates a stateless device link for `phy_get()`. It does not create an active supplier/consumer ordering guarantee against manually unbinding the provider. Any manual teardown test must unbind/remove the UFS consumer before unbinding the QMP PHY provider. Normal dependency-ordered device removal is the expected path.

The review did not execute error injection, runtime suspend/resume, rail measurement or a device test. These notes should be assessed by 2号 AI before a final implementation freeze.

## 7. Relationship to current project gates

2号 AI's ROUND61 record reports:
- Phase A patch application/checkpatch: PASS;
- Phase B UFS/QMP binding validation: PASS;
- Phase C Kleaf/Bazel target query/cquery: PASS;
- Phase D manifest-pinned ACK 6.18.33 Image build and 33/33 required config symbols: PASS.

Those are the 2号 AI branch's reported results; ROUND77 independently checks only the source semantics described above. It does not re-run or independently verify the hosted CI/Image artifacts.

The overall Stage A is still **NOT COMPLETE**:
- Phase E is BLOCKED by missing final HOS4.3 ABL-to-kernel memory/FDT handoff evidence and authoritative PM8150 physical input-parent topology.
- Phase F is BLOCKED for deterministic boot packaging by unresolved ABL DTBO selection, boot path/temporary-boot acceptance and AVB/vbmeta_cust evidence.
- Phase G device validation is NOT RUN.

Do not generate or flash a boot candidate, change AVB, or proceed to Android 17 DerpFest Stage B based on this source-review PASS.

## 8. Work performed and not performed by 1号 AI

Performed: read-only inspection of the exact pinned ACK sources and the 2号 AI's patch artifacts; source-level lifecycle and semantics review.

Not performed: no patch edit, no branch write, no real `git apply`, no compiler/Kleaf/Bazel/schema invocation, no kernel/Image/DTB build, no device connection, no ADB/fastboot/boot/flash, no power-rail measurement.

**Final review status: PASS for normal-path source semantics; minor cleanup/error-path notes remain for 2号 AI to consider. Stage A remains incomplete and board/boot gates remain closed.**
