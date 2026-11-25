# ROUND134 — ACK UFS regulator post-decrement error reachability on the current DBY-W09 draft

- **Owner / reviewer:** 1号 AI (ChatGPT)
- **Scope:** fixed-source audit of regulator disable ordering, PM8150 RPMh output supply metadata, current DBY-W09 board DTS draft, and existing HOS4.3 UFS regulator evidence.
- **Fixed ACK:** `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9` (`android17-6.18.33_r00`)
- **Related prior review:** [ROUND123 regulator-disable post-decrement audit](./../round123/round123-1ai-regulator-disable-post-decrement-error-audit.md)
- **Current board design input:** `dts/dby-w09-ack18-board.dts.draft` as present in the AI1 ROUND130 candidate branch; this remains a draft and was not part of the 21-patch ROUND130 build test.
- **HOS4.3 evidence:** [ROUND21 UFS/pinctrl/overlay audit](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round21/round21_first_stage_devtmpfs_and_ufs_pinctrl_overlay_audit.txt), [ROUND13 PM8150 mode/DRMS audit](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt).

## 1. Updated disposition

**The generic post-decrement concern remains valid in the regulator core, but its coupling/real-parent branches are not established as reachable on the current DBY-W09 board DTS draft. Do not add a speculative generic regulator-core patch on that basis.**

For the current draft:
- UFS rails do not declare `regulator-coupled-with`; the regulator core therefore initializes each of these regulators with a one-member coupling descriptor (`n_coupled = 1`). The post-decrement `regulator_balance_voltage()` branch is not entered for those rails.
- The PM8150 / PM8150L regulator child nodes do not declare physical input-supply phandles (the driver-provided `vdd-l...` / `vdd-s...` names are not translated to guessed DT links in this draft).
- If no external alias or separately registered regulator resolves those driver supply names, ACK regulator core's full-constraints behavior falls back to its dummy regulator. The dummy regulator is marked always-on and has no hardware operations. This models an input assumed to be already present; it is **not** an electrical proof or a real PMIC VIN connection.
- The draft's `qcom,vccq-parent-supply = <&vreg_s8c_1p2_1p4>` is a UFS consumer-side relationship from the UFS host to PM8150L S8. It is not S8's own `vdd-s8` physical input, nor is it a parent relation for the L5/L6/L9/L17 output providers.

This is a candidate-specific source analysis, not a final DTB/Kconfig-resolved or runtime result. A separately registered alias/provider or later-added real parent link could change the reachability analysis.

## 2. Fixed ACK disable order

Pinned `drivers/regulator/core.c` gives this relevant order inside `_regulator_disable()`:

1. If this is the final user and the regulator is switchable, call the provider `ops->disable` through `_regulator_do_disable()`.
2. If that provider callback fails, return immediately. The consumer `enable_count` has not yet been decremented.
3. On provider success, call `_regulator_handle_consumer_disable()`, which decrements the consumer `enable_count`.
4. Only after that decrement, run `regulator_balance_voltage()` when `n_coupled > 1`.
5. Only after that decrement, recursively disable `rdev->supply` when `use_count == 0`.

Pinned-source locations:
- [ACK _regulator_disable()](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/core.c#L3019-L3071)
- [ACK _regulator_handle_consumer_disable()](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/core.c#L2879-L2895)
- [ACK regulator_set_load() rollback](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/core.c#L4940-L4970)

The RPMh provider's `rpmh_regulator_disable()` calls `rpmh_regulator_set_enable_state(..., false)`. That function updates its cached `vreg->enabled` only after `rpmh_regulator_send_request()` succeeds. Therefore a normal RPMh provider-command failure is returned from `ops->disable` before the regulator core decrements the consumer reference.

Pinned source:
- [ACK RPMh regulator enable-state request](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/qcom-rpmh-regulator.c#L229-L263)

## 3. Why ROUND122 / ROUND128 protect the current normal disable path

ROUND122 moves the UFS load-zero request ahead of `regulator_disable()`. Pinned ACK `regulator_set_load()` saves the old `uA_load`, attempts DRMS update, and restores the old load if that update fails. Since this happens before `regulator_disable()`, a failed load-zero request returns without reducing the consumer reference.

When load-zero succeeds:
- the subsequent consumer decrement sees `uA_load == 0`, so `_regulator_handle_consumer_disable()` does not issue its post-decrement DRMS update;
- if the RPMh provider's disable request fails, the core returns before decrementing the consumer reference;
- the UFS/QMP software state can retain its enabled-reference flag and restore the active load on the next power-on without blindly acquiring a second enable reference.

Patch/source evidence:
- [ROUND122 UFS load-first patch](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round122-ufs-vreg-load-order/kernel-baseline/round122/0001-ufs-core-vreg-load-first.patch) (Git blob `64dd2ad9022251e2411a1a745aeb920a0badfa85`, SHA-256 `2f335f513fd1f7013a0edbc2e0d9eb5dca9ae68055eff4fd526b1c4274cfca66)).
- [ROUND128 V2 QMP rail-state patch](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round128-qmp-ufs-rail-state-v2/kernel-baseline/round128/0001-qmp-ufs-rail-state-v2.patch) (Git blob `22ccec1cabf2d78e61442d19219985135f8341e7`, SHA-256 `53ef42bb997a46e776f65c256039b13285047f784fed506ab8b22ab7f76e3bfb)).
- [ROUND130 combined build acceptance](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round130/ROUND130_ACCEPTANCE.md). This proves the 21-patch code candidate builds; it does not include or validate the separate board DTS draft.

## 4. Current draft's regulator topology and the dummy-parent boundary

Pinned `drivers/regulator/qcom-rpmh-regulator.c` assigns the following default `supply_name` strings:

| Provider output | RPMh driver supply name |
|---|---|
| PM8150 L5 | `vdd-l3-l4-l5-l18` |
| PM8150 L6 | `vdd-l6-l9` |
| PM8150 L9 | `vdd-l6-l9` |
| PM8150 L17 | `vdd-l13-l16-l17` |
| PM8150 S4 | `vdd-s4` |
| PM8150L S8 | `vdd-s8` |

Pinned driver data:
- [ACK PM8150 / PM8150L regulator tables](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/qcom-rpmh-regulator.c#L980-L1033)

The current DBY-W09 board draft defines the UFS PMIC regulator children with voltage / mode constraints and links the UFS consumers to those outputs. It does not add any of the above `vdd-*-supply` phandles and does not declare `regulator-coupled-with` on those PMIC children.

ACK supply resolution works as follows:
- `of_regulator_dev_lookup()` searches for the relevant `<supply_name>-supply` property on the regulator node and its child subtree.
- If no DT phandle is present, normal alias / map / regulator-name lookup is attempted.
- If no real provider resolves and the populated-DT full-constraints condition applies, the core may select `dummy_regulator_rdev`.
- The dummy regulator is initialized by `regulator_init()`, is marked `always_on`, and has an empty `regulator_ops` table.

Pinned source:
- [ACK DT supply lookup](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/of_regulator.c#L572-L684)
- [ACK supply resolution and dummy fallback](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/core.c#L2046-L2145)
- [ACK full-constraints behavior](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/core.c#L114-L118)
- [ACK regulator dummy implementation](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/dummy.c)
- [ACK dummy initialization in regulator core](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/core.c#L6470-L6495)

Coupling semantics:
- `of_get_n_coupled()` counts `regulator-coupled-with` phandles.
- `regulator_init_coupling()` sets `n_coupled = n_phandles + 1` and returns directly when there are no phandles.
- Thus, for a rail whose final DT has no `regulator-coupled-with`, `n_coupled == 1` and the post-decrement `regulator_balance_voltage()` path is skipped.

Pinned source:
- [ACK coupled-regulator enumeration](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/of_regulator.c#L743-L858)
- [ACK regulator coupling initialization](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/core.c#L5700-L5742)

**Important limitation:** dummy fallback is a software compatibility assumption that the physical input is already present/enabled. It does not prove the PMIC output's electrical input source. The final DT may also gain a supply alias or a real input provider before integration. Do not treat this source-path analysis as permission to add a guessed physical input.

## 5. HOS4.3 evidence cross-check

The existing ROUND21 report resolves the UFS consumers:
- PHY: L5 and L9
- Host: L17, L6, S4, GDSC; additionally the vendor-specific `qcom,vccq-parent-supply` reaches PM8150L S8.
- It states the listed base regulator nodes have no explicit `parent-supply`, while the UFS overlay adds the distinct consumer-side `qcom,vccq-parent-supply -> pm8150a_s8` relation.

This is not evidence that the PMIC outputs have no physical electrical inputs, nor does it make the HOS vendor RPMh implementation equivalent to ACK's parent-supply lookup. It only confirms the static relationships that were actually parsed.

Sources:
- [ROUND21 report, UFS supply providers](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round21/round21_first_stage_devtmpfs_and_ufs_pinctrl_overlay_audit.txt#L341-L363)
- [ROUND13 PM8150 mode and DRMS metadata](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt#L135-L228)

## 6. What remains open

1. **Physical PMIC input tree remains an electrical gate.** The current board DTS draft still has no proven physical inputs for PM8150/PM8150L LDO/SMPS outputs. Do not merge this board DTS or proceed to hardware boot on the assumption that the dummy regulator describes the actual circuit.
2. **Persistent provider disable failure during detach remains unresolved.** UFS and QMP use managed regulator handles; the cleanup / HBA exit paths cannot veto devres teardown. `_regulator_put()` warns on a nonzero consumer enable count but still destroys the handle. A future disable failure at final teardown can therefore still leave a WARN / lost-handle condition.
3. **Future real supply or coupling edges reopen ROUND123's generic post-decrement risk.** If the final DT resolves a real parent whose disable can fail, or adds regulator coupling, then parent / balancing failure can occur after the child's consumer reference has been decremented. Re-review before adding such topology.
4. No runtime RPMh request, actual VIN measurement, final regulator graph, live DT, or board electrical path was observed.
5. The board DTS draft is not dtc/schema validated and was not part of the ROUND130 21-patch build. No device boot evidence exists.

## 7. Implementation decision

- Keep the accepted ROUND120 / ROUND122 / ROUND128 V2 / ROUND126 AI1 candidates unchanged.
- Do not introduce a speculative regulator-core error/enable-count API or force-disable shortcut based on the generic parent/coupling path alone.
- Preserve load-first shutdown ordering.
- Treat final supply-parent resolution and devres failure cleanup as separate design/validation gates.
- No source code, DTS, Kconfig, config fragment, production patch series, protected branch, firmware, or device was modified/accessed during this review.
