# ROUND123 — 1号 AI：ACK regulator_disable 后置失败与 UFS 消费者状态一致性审查

**执行者：1号 AI（ChatGPT）**  
**类型：固定源码审查 / ROUND122 Agent 报告复核**  
**基线：** `aosp-mirror/kernel_common @ 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`（`android17-6.18.33_r00`）  
**候选补丁：** `ai1/round122-ufs-vreg-load-order` / `kernel-baseline/round122/0001-ufs-core-vreg-load-first.patch`  
**测试报告：** `firmware-analysis/round122/TEST_AGENT_ROUND122_UFS_VREG_LOAD_ORDER_REPORT.txt`

## 1. ROUND122 验证结果复核

ROUND122 的本地测试 Agent 报告已从 `firmware-audit-v1` 读回。候选补丁未经修改，执行了固定 ACK worktree 的真实 apply、对象编译和 Stage A Kleaf 完整构建：

- patch SHA-256：`2f335f513fd1f7013a0edbc2e0d9eb5dca9ae68055eff4fd526b1c4274cfca66`；Git blob：`64dd2ad9022251e2411a1a745aeb920a0badfa85`。
- 固定 ACK commit：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`。
- `git apply --check` / apply / `git diff --check` 均 RC=0；报告记载零 offset、零 fuzz；只改 `drivers/ufs/core/ufshcd.c`。
- `drivers/ufs/core/ufshcd.o`：pristine 与 patched 两份独立构建均 RC=0；目标对象 SHA 不同（pristine `e96226b4…`，patched `4a31b63a…`）。
- Stage A 构建工作树叠加候选 patch 后，`tools/bazel build //common:dby_w09 --jobs=8 --local_ram_resources=6144` 返回 `BUILD_RC=0`；Image SHA-256 `453a46a241ce86bc8445f2a886c38942a2fb36aa9ee4573bf17c5ad6454936a7`。构建后恢复了原 Stage A 工作树，Agent 报告中记录的 dirty-line 数恢复为原值。
- `checkpatch.pl --strict`：0 errors、0 warnings、2 CHECK，RC=1。两个 CHECK 是原补丁前就存在的 continuation-line 对齐提示；Agent 未修改候选补丁。这应记为“无 error/warning，但仍有 2 个 style CHECK”，不能写成 checkpatch RC=0。
- 未访问设备、未执行 ADB/fastboot/刷写；未修改 AI2 分支。

**验收判定：ROUND122 = BUILDABLE CANDIDATE / 静态与构建验证 PASS。** 这不等于 UFS 电源故障生命周期全部安全，也不代表已集成至 AI2 Stage A 分支或已在实机验证。

## 2. ROUND122 真正修复的 ACK 故障路径

固定 ACK 的 `drivers/regulator/core.c` 证明：

1. `regulator_set_load()`（约第 4950 行）先写新 `uA_load`；若消费者仍有 enable reference 且 DRMS 更新失败，会恢复旧 `uA_load` 并返回错误。
2. ROUND122 在 `ufshcd_disable_vreg()` 中先执行 `ufshcd_config_vreg(..., false)`，只有返回成功才调用 `regulator_disable()`。因此 load-zero / DRMS 失败时，旧 load 被恢复，UFS 不会继续减少 regulator enable reference。
3. `_regulator_handle_consumer_disable()`（约第 2879 行）先递减 `regulator->enable_count`，之后才在 `uA_load != 0` 且计数归零时运行 `drms_uA_update()`。通过先成功设置 load 为 0，ROUND122 消除了这条“consumer count 已递减、随后 DRMS 失败”的特定失败路径。
4. `ufshcd_enable_vreg()` 先重设 active load，再检查 `vreg->enabled`，因此对“enable reference 仍保留、前次 load 已清零”的情况，能先恢复 load 且不重复调用 `regulator_enable()`。

因此 ROUND122 的目标路径和补丁顺序有源码依据，Agent 的 apply / compile / build 结果也支持该补丁作为可构建候选保留。

## 3. 尚未解决的第二类 post-decrement failure

ROUND122 报告把“regulator_disable 后置错误”主要归纳成 enable_count 已递减后 DRMS 更新失败。固定 ACK 复核后，需要进一步精确区分：

- `_regulator_disable()`（约第 3019–3071 行）在调用 `_regulator_handle_consumer_disable()` 后，仍可能调用 `regulator_balance_voltage()`（有 coupled regulators 时），以及递归调用父供电的 `_regulator_disable(rdev->supply)`。
- 这些操作发生在 consumer `enable_count` 已递减之后；若其中任一项返回错误，外层 `regulator_disable()` 仍可能返回负数，但 consumer reference 已经减少。
- ROUND122 的 load-zero 顺序可避免 `_regulator_handle_consumer_disable()` 内部因非零 `uA_load` 而触发的 DRMS 错误，但**不能**保证 coupling balance 或 parent-supply disable 永不在递减后失败。
- 此时 UFS 的 `ufshcd_disable_vreg()` 会因 `regulator_disable()` 返回负数而保留 `vreg->enabled = true`。下一次 `ufshcd_enable_vreg()` 会恢复 load，但因为 `vreg->enabled` 仍为 true 而跳过 `regulator_enable()`。如果 consumer reference 实际已递减到 0，load 恢复本身不会恢复 enable reference。

所以该补丁修复了一个明确且重要的 DRMS 顺序故障，但不能声称能处理所有“返回错误但计数已部分变化”的 regulator core 路径。UFS driver 目前也没有公开接口查询该 `struct regulator` handle 的 consumer `enable_count`；不能仅凭 `regulator_is_enabled()`（它查询 regulator 输出，不是这个 consumer handle 的 enable reference）安全推断是否应再次 enable。

## 4. Detach / devres 边界仍然开放

固定 ACK 还确认：

- `devm_regulator_get()` 在 `drivers/regulator/devres.c` 注册 release callback；callback 无条件调用 `regulator_put()`。
- `_regulator_put()`（`drivers/regulator/core.c` 约第 2444 行）在 `regulator->enable_count` 非零时执行 `WARN_ON`，随后仍然销毁 consumer handle，不提供可返回错误来阻止 managed release 的接口。
- UFS `ufshcd_hba_exit()`（`drivers/ufs/core/ufshcd.c` 约第 9835 行）调用 `ufshcd_setup_vreg(hba, false)`，但不检查返回值；`ufshcd_remove()` 后续调用该 exit 路径，不能因 regulator disable 错误而 veto devres teardown。
- 因此 provider disable 真正失败且 enable reference 保留时，detach 仍可能出现 regulator_put WARN 后丢弃 handle。ROUND122 没有解决这一点，且不能用 `regulator_force_disable()` 作为共享 L6 rail 的通用补救。

## 5. 后续实现约束

1. ROUND122 patch 保留在 AI1 独立候选分支，不直接合并到 main、DTS 草案或 AI2 分支。
2. 后续研究必须把 regulator_disable 的错误分成“consumer count 递减前返回”与“consumer count 递减后返回”；不得只按返回码推断 handle 状态。
3. 不可在 UFS 驱动里盲目对 disable error 再调用 `regulator_enable()`：对计数仍保留的路径会重复增加 reference。
4. 不可盲目将 `vreg->enabled=false`：对计数仍保留的路径会造成下一次重复 enable。
5. 需要继续评估的方向是 regulator-core 是否能向 consumer 提供一致的 disable 结果/状态契约，或明确界定本项目目标 PM8150 regulator topology 是否会触发 coupling / parent-supply 后置错误；没有源码和设备树证据前，不在通用 core 或 UFS 生命周期上做猜测性补丁。
6. 实机测试、运行时供电状态、PM8150 实际 VIN parent topology 仍 NOT RUN / UNKNOWN；本轮构建通过不改变 Phase E/F BLOCKED 与 Phase G NOT RUN。

## 6. 审查结论

ROUND122 Agent 验证按其任务范围通过；本轮 1号 AI 复核发现其“load restore”不等于完整恢复 consumer enable reference。应将 ROUND122 作为修复 DRMS ordering 的可构建候选，而不是最终 teardown-safe 方案。下一步继续做固定 ACK / HOS4.3 PM8150 topology 的源码证据审查，再决定是否需要新的 regulator-core 接口/修正；暂不派发新的 Agent 代码或设备任务。
