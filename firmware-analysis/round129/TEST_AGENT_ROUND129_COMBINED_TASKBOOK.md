# [发给测试 Agent] AI1-ROUND129 联合复验任务书
## ROUND128 QMP UFS 双 rail 状态 V2 + ROUND126 proxy-consumer load-first teardown

- Task ID：`TEST-AGENT-AI1-ROUND129`
- 下发方 / 技术负责人 / 代码所有者：**1号 AI（ChatGPT）**
- 执行方：用户本地 WorkBuddy 测试 Agent
- 独立审核方：1号 AI（ChatGPT）
- 性质：只读验证、补丁应用、host tests、checkpatch、目标对象编译、完整 Image build、配置回归、恢复工作区
- 报告分支：`firmware-audit-v1`
- **Agent 只验证，不得编写、编辑、修复或重新生成任何补丁、源码、测试或配置。**
- **本任务只属于 1号 AI；不得修改 2号 AI 的 AI2 Stage A 分支。**

## 0. 项目背景与阶段边界

设备：Huawei MatePad 11 2021，DBY-W09，Qualcomm KONA / SM8250。

Stage A 必须先完成固定 ACK 6.18.33 GKI 内核移植、内存/FDT/EFI handoff、电源/存储和实际硬件验收；只有 Stage A 通过后，才开始 Stage B Android 17 DerpFest 适配。

固定源码：
- repo：`aosp-mirror/kernel_common`
- tag：`android17-6.18.33_r00`
- immutable commit：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

严禁替换为 Linux stable v6.18.33 或移动的 android17-6.18 HEAD。

角色区分：
1. 1号 AI（ChatGPT）：ROUND128 补丁所有者；ROUND129 联合验证任务书下发者和验收者。
2. 2号 AI：独立开发 AI；拥有 `ai-parallel/stagea-port-until-boot`。本任务不触碰其分支或实现。
3. Agent：本机测试执行方；不是 2号 AI。只执行本任务。

## 1. ROUND127 失败原因和本轮修正

ROUND127 报告：
`firmware-analysis/round127/TEST_AGENT_ROUND127_COMBINED_REPORT.txt`

ROUND127 结果：
- ROUND126：apply、source gates、host tests、checkpatch、`proxy-consumer.o` 均通过。
- ROUND125：apply/source gates 通过，但 `phy-qcom-qmp-ufs.o` 因 `qmp_ufs_power_off()` 重复定义失败。
- ROUND63 的 17-patch baseline 已经包含一个 `qmp_ufs_power_off()`，并且该函数已调用 `qmp_ufs_regulators_disable(qmp)`。
- ROUND125 原补丁又新增第二个同名回调，造成重定义。这是补丁堆叠缺陷。
- 按 §6.4 stop rule，ROUND127 未运行完整 Image build、产物哈希和 ROUND58 config regression。

ROUND128 V2 已去除重复新增的 `qmp_ufs_power_off()`，复用 ROUND63 既有回调；状态跟踪和 regulator helper 逻辑保留。此修正尚未被应用、编译或独立验证。

## 2. 固定基线及候选补丁身份

仓库：`hhdy/matepad11-dby-w09-agent-reports`

Stage A 固定 commit：
`ai-parallel/stagea-port-until-boot@2f21233148a04afdd61e44b1be7688399967d9d0`

固定 series：
`kernel-baseline/round61/round32-stagea-series.txt`

必须按 series 顺序先应用完整 17 个补丁。ROUND33 第三次复验报告：
`firmware-analysis/round33/AI2_ROUND33_FINAL_REVALIDATION_REPORT.txt`
blob：`f7452f9259e7ed25027758fc39af4c047867b9e7`

ROUND33 已通过：17-patch apply、host suites 38/38 + 83/83、schema、fresh full build、ROUND58 config 33/33 + helper 11/11、workspace restore。它不代表硬件验证。

### 本轮第 18 个补丁：ROUND128 V2（必须使用此版本）

分支：`ai1/round128-qmp-ufs-rail-state-v2`

文件：
`kernel-baseline/round128/0001-qmp-ufs-rail-state-v2.patch`

Git blob：
`22ccec1cabf2d78e61442d19219985135f8341e7`

仅作用于：
`drivers/phy/qualcomm/phy-qcom-qmp-ufs.c`

使用 ROUND128 V2，不得使用旧的 ROUND125 文件：
`kernel-baseline/round125/0001-qmp-ufs-rail-state.patch`
旧文件已知会引入重复 `qmp_ufs_power_off()`，禁止本轮再次应用。

### 本轮第 19 个补丁：ROUND126（此前对象编译通过，但必须联合重验）

分支：`ai1/round126-proxy-consumer-load-first`

文件：
`kernel-baseline/round126/0001-proxy-consumer-load-first.patch`

Git blob：
`c180dbf458403d68b2c32c1d54776a7559e7e5db`

SHA-256：
`eae21b96d34ebff0e7bbd4843bcd4f96cda26b02f83dd6f323b8c571e51fef80`

仅作用于：
`drivers/regulator/proxy-consumer.c`

请从 GitHub 重新读取两个补丁的实际内容，核对 blob，并计算 ROUND128 V2 的 SHA-256。不得依赖本任务书之外的本地旧快照。

## 3. 必须遵守的执行顺序

1. 使用全新 disposable staging/worktree；固定在 ACK commit。
2. 按 `round32-stagea-series.txt` 顺序应用 17 个基础补丁。
3. 再按顺序应用 ROUND128 V2，然后 ROUND126。
4. 每个补丁分别执行：
   - `git apply --check --verbose`
   - `git apply`
   - `git diff --check`
5. 对全部 19 个补丁核对身份和作用路径。记录每一补丁的 RC、offset、fuzz；不得静默接受 fuzz。
6. 记录 overlay 前后 tracked diff hash、changed paths 和未跟踪文件清单。
7. 进行 §4 的源码门槛；再进行 §5 host tests / checkpatch；再进行 §6 对象编译。
8. **若任一对象编译失败，立即停止，不得运行完整 Image build，也不得自行修复。** 报告实际错误和最小复现命令后结束。
9. 只有两个对象均编译成功，才运行 §7 完整构建和配置回归。
10. 按 §8 恢复并哈希验证工作区。

## 4. ROUND128 V2 源码门槛（在实际 19-patch tree 检查）

检查文件：
`drivers/phy/qualcomm/phy-qcom-qmp-ufs.c`

A. **函数定义唯一性（本轮修正重点）**
- 全文件只能有一个定义：`static int qmp_ufs_power_off(struct phy *phy)`。
- 定义必须是 ROUND63 已有的回调；不能在 ROUND128 patch 新增另一个同名函数。
- 该既有回调继续调用本轮更新后的 `qmp_ufs_regulators_disable(qmp)`。
- 检查所有 `qmp_ufs_power_off` 的声明/引用/定义，提供新行号及 grep 证据。

B. **状态表示与布局**
- `struct qmp_ufs` 有 `bool vreg_enabled[2]` 和 `bool vreg_load_active[2]`，旧的单一 `vdda_phy_enabled` 字段不再承担双 rail 状态。
- 特殊路径仅接受 exactly two regulators，且 index 0 为 `vdda-phy`、index 1 为 `vdda-pll`；否则 fail closed。
- property absent 时保留原始 bulk enable/disable path。

C. **初始化与状态转移**
- `devm_regulator_bulk_get_const()` 完成后，以两个 `init_load_uA > 0` 初始化 load-state bits；不得凭空认为 enable reference 已持有。
- enable：先恢复 load；仅在 `vreg_enabled[index]` 为 false 时才调用 `regulator_enable()`；API 成功后才设置 enabled bit。
- disable：先 load-zero；load-zero 失败不得继续 disable；仅在 `regulator_disable()` 成功后清除 enabled bit。
- load-state bit 只在 `regulator_set_load()` 成功后更新。

D. **正常 power-off / 最终 cleanup**
- 复用 ROUND63 既有 power-off callback，不得重复定义。
- hardware power-down、clock off 后，由更新后的 helper 先清理 L9 / vdda-pll，再清 L5 / vdda-phy load；L5 enable reference 按 always-on policy 保留。
- 最终 devm cleanup action 先处理 L9，再处理 L5；action 注册顺序仍保证它在 managed regulator handle put 之前执行。
- 保留限制说明：void devm action 无法 veto 后续 managed regulator_put；persistent failure 的 warning 不可声称已解决。

E. 所有行号均须从实际应用后的文件生成，不可沿用 ROUND127 报告中的行号。

## 5. ROUND126 源码门槛

检查：
`drivers/regulator/proxy-consumer.c`

- `regulator_proxy_consumer_remove()` 中，当 `current_uA > 0` 时，`regulator_set_load(reg, 0)` 必须在 `regulator_disable(reg)` 之前。
- load-zero 失败记录真实返回码；void unregister cleanup 保持 best-effort，不得声称可 veto unregister。
- deferred consumer 的 NULL handle 早退保持安全。
- enable=false 仍清理 load / voltage / handle。
- voltage vote 清理保留原路径。
- per-rdev unregister 与 `late_initcall_sync` bulk revoke 两条调用路径仍存在。
- ROUND33 self-target-only 校验全部保留；ROUND126 不能扩大 proxy-supply 目标范围。
- 不得调用 `regulator_force_disable()`，不得伪造 enable state。

## 6. Host tests / Checkpatch / Object compile

### 6.1 Host tests

在实际的完整 19-patch tree 运行原样 harness：
`bash tests/run_tests.sh`

记录逐项输出、退出码、checks/failures。参考门槛：
- legacy suite：38 checks，0 failures；
- ROUND32/33 suite：83 checks，0 failures，无 crash。

不得修改 harness、mock、fixture 或任何测试文件。

### 6.2 Checkpatch

分别执行：
`scripts/checkpatch.pl --strict --no-signoff <ROUND128 V2 patch>`
`scripts/checkpatch.pl --strict --no-signoff <ROUND126 patch>`

记录 errors / warnings / CHECKs / RC。ROUND126 之前结果是 0E/0W/1C、RC=1；不得将其描述为 clean，需如实记录本轮实际结果。

### 6.3 目标对象编译

使用 manifest-pinned Kleaf Clang 与 Stage A 配置，分别编译：
- `drivers/phy/qualcomm/phy-qcom-qmp-ufs.o`
- `drivers/regulator/proxy-consumer.o`

提供完整命令、工具链版本、退出码、对象大小和 SHA-256。

### 6.4 Stop rule

若任一对象编译有错误，立即停止。不得修复、编辑或重生成任何代码；不得执行 §7 full build。将错误诊断原样写入报告。

## 7. Full Image build + ROUND58 config regression

仅在两个对象均成功编译后执行：

`tools/bazel build //common:dby_w09 --jobs=8 --local_ram_resources=6144`

记录：
- BUILD_RC / duration；
- Image、System.map、vmlinux、.config size 与 SHA-256；
- .config 是否 byte-identical 于 Stage A-only baseline；
- expected .config SHA-256：
  `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`；
- 通过 overlay tracked-diff identity、对象 hash / symbol 等证据证明两个候选补丁确实包含在构建输入中；
- 运行 `check_dby_w09_config.py`，预期 33/33；
- 运行 helper unit tests，预期 11/11。

不得上传 Image、vmlinux、System.map 或其他构建二进制。

## 8. Restore / cleanup

- 逆序撤销 ROUND126、ROUND128 V2，再检查 17-patch baseline。
- 对照 overlay 前后 tracked diff hash、tracked paths、untracked file set，必须完全一致。
- 只清理本任务创建的 disposable worktree、object outputs、temporary logs 和 scratch。
- 不得清理/修改其他 Agent 工作区、AI2 workspace、原 a30 build workspace或任何其他 staging。
- 报告保留去敏化命令、退出码、hash、工具链版本和证据；不得上传二进制。

## 9. 绝对禁止与设备审批闸门

- 不得修改 main、AI2 Stage A 分支、ACK DTS draft、PR #1、ROUND124、ROUND125、ROUND126、ROUND128 source branch 或任何本轮候选补丁。
- 不得将候选补丁合入 AI2 分支。
- 不得连接、启动、刷写、fastboot、ADB、root、解锁或访问任何平板分区。
- 不得使用 USB、ADB、fastboot、recovery、串口或其他设备接口。
- 如果执行过程中有任何步骤似乎需要访问平板，必须先停止，告诉用户访问类型、原因和拟执行命令，等待用户明确许可。未经许可即使只读设备命令也禁止。

本任务必须完全离线。

## 10. 唯一交付物与停止条件

只新增并上传：
`firmware-analysis/round129/TEST_AGENT_ROUND129_COMBINED_REPORT.txt`

报告必须包括：
- 固定 ACK / Stage A commit / 17-patch identities；
- ROUND128 V2 与 ROUND126 的 Git blob / SHA-256；
- 所有 19 个补丁的 apply/check/diff RC、offset、fuzz；
- ROUND128 唯一 power_off 定义 grep 证据、新源码行号；
- ROUND128 与 ROUND126 源码门槛 PASS / FAIL / BLOCKED 证据；
- host tests 38/38 + 83/83 的真实结果；
- checkpatch 统计；
- 两个对象编译结果；
- 如达到条件，完整 Image build、.config 和 artifact hashes、33/33 config、11/11 helper tests；
- workspace restore evidence；
- 明确声明没有连接平板、没有发出任何设备命令。

只上传这一份报告。上传后读回确认，立即停止；不启动 ROUND130，不修改任何代码。
