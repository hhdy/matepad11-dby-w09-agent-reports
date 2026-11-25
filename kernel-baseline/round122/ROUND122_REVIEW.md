# ROUND122 — 1号 AI：UFS generic VCC/VCCQ load-first shutdown candidate

**Owner / patch author:** 1号 AI（ChatGPT）  
**Independent test executor:** 用户本地测试 Agent（只执行测试，不修改 patch）  
**Pinned ACK:** aosp-mirror/kernel_common @ 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Candidate branch:** ai1/round122-ufs-vreg-load-order  
**Target source:** drivers/ufs/core/ufshcd.c

## 1. Change

The candidate patch makes two related changes:

1. ufshcd_disable_vreg() now calls ufshcd_config_vreg(..., false) while the regulator consumer enable reference is still held. If load-zero fails, it returns without calling regulator_disable(). This removes the known ACK post-decrement DRMS transition from the normal shutdown sequence for configurable UFS rails.
2. ufshcd_enable_vreg() reapplies the active max_uA load before deciding whether regulator_enable() is needed. If an earlier disable cleared the load but the provider disable failed while retaining the consumer reference, a subsequent enable/reuse restores the active load without incrementing the same enable reference again.

The patch does not change struct ufs_vreg, public struct ufs_hba, DTS, or regulator core. It relies on the existing regulator handle to retain its stored load. It preserves the existing behavior for absent vregs, always_on rails, zero max_uA, and regulators for which ufshcd_config_vreg() intentionally does not configure loads (regulator_count_voltages() <= 0).

## 2. Important limitation retained

This is a targeted ordering correction, **not a complete failed-unbind solution**.

If regulator_disable() itself fails before decrementing the consumer enable reference, ufshcd_disable_vreg() correctly leaves vreg->enabled true and the handle's load at zero. However the current UFS generic supplies are acquired with devm_regulator_get(); the later managed release still calls regulator_put(). ACK regulator_put() warns if enable_count remains nonzero and destroys the consumer handle anyway. A cleanup error cannot veto the managed put. Therefore:
- the known post-decrement DRMS hazard is addressed;
- re-enable after a retained-reference failure restores max_uA;
- true provider-disable failure followed by device devres release remains an open lifetime boundary;
- this patch must not be represented as proving every regulator teardown error path safe.

The fixed-ACK HOS4.3 L17/L6 async RPMh disable evidence and ROUND105/112 constraints remain applicable. Do not use regulator_force_disable() on shared L6, which also has the independent VDDP consumer.

## 3. Exact-source generation checks

The patch was generated from the exact pinned ufshcd.c blob and the combined old function block was matched exactly once. It replaces only the adjacent ufshcd_enable_vreg()/ufshcd_disable_vreg() block; no overlapping hunks are used.

Independent testing must still verify real git apply --check and compilation.

## 4. Required Agent validation

See TEST_AGENT_TASKBOOK.md. Agent must use a disposable pinned ACK worktree and may only validate the candidate. It must not edit the patch, author source, touch the AI2 branch, modify DTS/config/firmware, or access/boot/flash the device.

## 5. Status

- Candidate patch: created in isolated AI1 branch.
- Exact pinned source target: unique match.
- Real git apply / checkpatch / object compile / full Image build: NOT YET RUN.
- Hardware boot and rail behavior: NOT RUN.
- Stage A Phase E/F remain BLOCKED; Phase G NOT RUN.
