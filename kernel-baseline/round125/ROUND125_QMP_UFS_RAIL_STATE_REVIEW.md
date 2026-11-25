# ROUND125 — AI1 QMP UFS retained-rail state candidate

- Owner / patch author: **1号 AI（ChatGPT）**
- Independent validation: 用户本地测试 Agent（只测试、编译、上传报告，不修改代码）
- AI2 owner: independent development AI; its branch is not modified by this candidate
- Candidate branch: `ai1/round125-qmp-ufs-rail-state`
- Fixed ACK: `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Stage A source base: `ai-parallel/stagea-port-until-boot@5f587aaa40853cf3ec754f7455930aa404bf9b9a`, using exactly the first 15 ROUND31/32 patches; the pending AI2 ROUND33 patch 16 is excluded.
- AI2 prerequisite patch: ROUND63 `round61/patches/round63-0001-phy-qcom-qmp-ufs-always-on.patch`, Git blob `99fffb10603b38bc30a0e6c9db99b0e9888a7b82`, SHA-256 `d33e1d405cc6c855de9a3867ec7e39a25e7bec2f6f74924cb1bbc6a86b1f9539`.

## 1. Problem statement

ROUND63 introduced a `vdda-phy-always-on` special path in `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c`, but its state accounting was incomplete:

1. It tracked only the retained `vdda-phy` enable reference. The trailing `vdda-pll` enable reference was not recorded separately.
2. The power-off path disabled the trailing rail through a bulk helper. If L9 disable failed before the provider accepted its asynchronous RPMh request, the consumer enable reference remained held, but the software had no state bit for it. A later power-on could increment the same consumer's enable count again.
3. The retained L5 cleanup logged a load-zero failure but still called `regulator_disable()`; it then cleared its enabled flag even if disable failed. That can expose the regulator core's post-decrement DRMS failure and/or discard knowledge of an outstanding reference.
4. A single `enabled` flag cannot represent the independently changing stored load vote and enable reference.

This round adds a state-aware delta after ROUND63. It does not alter AI2's source branch or overwrite ROUND63.

## 2. Fixed-source facts used

The candidate is limited to the existing QMP UFS two-rail special case:

- ROUND109's parser over the pinned ACK QMP UFS PHY source found all 15 regulator-list arrays have exactly two entries, ordered `vdda-phy` then `vdda-pll`. The SM8250 values are 89,900µA and 18,800µA respectively.
- Pinned ACK `devm_regulator_bulk_get_const()` copies the static list and calls `regulator_set_load(init_load_uA)` for positive initial loads while the consumer handles are still disabled. Thus the software load state must be initialized from the two `init_load_uA` fields after the bulk get succeeds.
- Pinned ACK `regulator_set_load()` on an enabled consumer performs the DRMS update immediately. If it fails, the core restores the previous stored load. The candidate changes the local load-state bit only after a successful API return.
- Pinned ACK `regulator_bulk_disable()` walks consumers in reverse order and may re-enable earlier successful entries if a later one fails. This convenience API does not expose enough per-rail state for the partial-failure case, so the property-specific path handles the two rails individually.
- Generic PHY core decrements `phy->power_count` only when the provider `.power_off()` returns success. Qualcomm UFS `ufs_qcom_exit()` is void and ignores `phy_power_off()` errors before continuing teardown. Once the QMP code has set hardware power-down and disabled clocks, returning a regulator-cleanup error would not abort UFS removal and could leave PHY power_count stale. The candidate therefore returns success after hardware power-off while retaining truthful regulator state and logging a vote-cleanup failure.

HOS4.3 evidence already recorded in ROUND106/107/109 shows no `qcom,always-wait-for-ack` or regulator coupling properties for the L5/L9 paths in the inspected base FDT / stock DTBO set. Their provider disable calls therefore use the asynchronous RPMh path under the inspected configuration. A negative asynchronous-disable return is before the provider's TCS-trigger / consumer-count-decrement boundary; success means the request was submitted, not that final physical rail-off was measured. The physical PMIC input topology remains unknown.

## 3. Candidate behavior

The patch adds two independent state arrays to the QMP private object:

- `vreg_enabled[2]`: whether the QMP consumer currently holds an enable reference for each rail.
- `vreg_load_active[2]`: whether the QMP consumer's stored load request is at its configured initial load rather than zero.

When `vdda-phy-always-on` is absent, the original bulk enable/disable path remains unchanged.

When present:

1. The driver fails closed unless there are exactly two regulators and their names are exactly `vdda-phy`, then `vdda-pll`.
2. After `devm_regulator_bulk_get_const()` and DT parsing, it initializes the load-state bits from each copied `init_load_uA` value. Enable bits start false because the bulk get only acquires/configures handles; it does not enable them.
3. Power-on restores each rail's active load first, then calls `regulator_enable()` only if the corresponding enable reference is not already held.
4. If power-on fails, it tries to idle the L9 tail rail and clear L5's load vote, preserving all state bits on failed API transitions. L5's enable reference is retained by the always-on policy.
5. Normal power-off first puts hardware into power-down and disables clocks. It load-zeroes L9 before disabling its reference, then independently load-zeroes L5 while retaining its enable reference. The callback returns success because hardware is down; regulator cleanup failures remain logged and represented in state.
6. The final devm action runs before managed regulator-handle release. It tries to load-zero and disable L9, then L5. A failed load-zero aborts that rail's disable attempt; a failed disable preserves its enabled bit. The managed `regulator_put()` still runs after a void devm action, so a persistent failure can still produce the regulator core's nonzero-enable-count warning. This candidate does not claim to solve that framework limitation.

## 4. Explicit limitations

- A negative regulator API return is not universally proof that an enable reference remains held: generic regulator core can return errors after a decrement on coupled or parent-supply paths. The inspected DBY-W09 L5/L9 static DT evidence narrows that path, but the HOS4.3 physical input mapping / external aliases remain unproven. The candidate keeps its last confirmed state on errors; it does not invent a way to inspect an opaque regulator handle's internal enable count.
- The final void devm cleanup action cannot veto the later managed regulator put. A persistent provider failure can still leave a warning at put time. No `regulator_force_disable()` shortcut is used.
- No hardware state, RPMh ACK, physical voltage, boot, or power-cycle behavior is claimed.
- The candidate overlaps the same QMP UFS source area that AI2 ROUND63 modified. It remains isolated on the AI1 branch and must not be merged to AI2 without coordination.

## 5. Candidate identity and validation status

Patch:
`kernel-baseline/round125/0001-qmp-ufs-rail-state.patch`

- Git blob: `c192fe1488d82b12aa3d3108e036d1141f5e76db`
- SHA-256: `31571a1e4449cb5cceae3f77a102e7d4af488f4ef878af3248e8624c7211617c`
- Changes only: `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c`
- Patch was generated as a delta against the ACK source after applying AI2 ROUND63. Its three hunk contexts and declared old/new line counts were independently checked in the authoring session; sequential application on the full 15-patch workspace and compilation are still **PENDING Agent validation**.

Agent taskbook:
`firmware-analysis/round125/TEST_AGENT_ROUND125_TASKBOOK.md` on `firmware-audit-v1`.

## 6. Acceptance boundary

If Agent identity/apply/source gates, strict checkpatch, target object compilation and fresh full Image build all pass, this may be accepted as an isolated AI1 buildable QMP rail-state candidate. It does not prove runtime fault-injection behavior, actual physical PMIC rails, device boot, or safe final put under a persistent provider failure. Do not merge automatically into AI2 Stage A.
