# [发给测试Agent] AI1-ROUND127 联合验证任务书
## ROUND125 QMP UFS 双 rail 状态 + ROUND126 proxy-consumer load-first teardown

- Task ID：TEST-AGENT-AI1-ROUND127
- 下发方 / 技术负责人：1号 AI（ChatGPT）
- 执行方：用户本地 WorkBuddy 测试 Agent
- 代码所有者：1号 AI（ChatGPT）
- 独立审核方：1号 AI（ChatGPT）
- 任务性质：只读验证、补丁应用、源码门槛、host tests、checkpatch、对象编译、完整 Image build、恢复工作区
- 报告分支：firmware-audit-v1
- **本任务只属于 1号 AI。Agent 只验证，不得编写、编辑、修复或重新生成补丁/源码/测试。**
- **不得修改 2号 AI 的 AI2 Stage A 分支。**

## 0. 项目背景与阶段顺序

设备：Huawei MatePad 11 2021，DBY-W09，Qualcomm KONA / SM8250。

项目目标严格按两阶段执行：
- Stage A：先完成固定 ACK 6.18.33 内核在 DBY-W09 上的移植、构建、板级内存/电源/boot handoff 核验，以及实际设备启动和存储/基础硬件验收。
- Stage B：只有 Stage A 通过后，才开始 Android 17 DerpFest device/vendor/HAL/ROM 适配。

固定源码：
- aosp-mirror/kernel_common
- tag android17-6.18.33_r00
- immutable commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9

不能用 Linux stable v6.18.33 或移动的 android17-6.18 HEAD 替代。

### 角色边界

1. 1号 AI（ChatGPT）：本轮两份候选补丁的所有者，完成设计、实现和源码审查。
2. 2号 AI：独立开发 AI，拥有 ai-parallel/stagea-port-until-boot。本轮不得修改它的代码/测试/分支。
3. 测试 Agent（你）：只执行本任务的本地验证和构建，不是 2号 AI，不得改代码或修补测试。

## 1. ROUND33 已完成，当前任务可以开始

ROUND33 的第三次复验已通过全部门槛：
- 最终报告：firmware-analysis/round33/AI2_ROUND33_FINAL_REVALIDATION_REPORT.txt
- 报告 blob：f7452f9259e7ed25027758fc39af4c047867b9e7
- 17-patch apply/check/diff：PASS
- host suites：38/38 + 83/83
- Schema：dtschema 2023.9 / 2026.9，14/14
- full tools/bazel build //common:dby_w09：BUILD_RC=0
- ROUND58 config 33/33，helper 11/11
- workspace restore hash-verified
- Agent 已完成并释放完整 Image 构建时段。

ROUND33 只证明 mock-level host lifecycle、Schema 和编译，不证明硬件行为。不得刷写/启动设备。

## 2. 固定验证基线

### 2.1 Stage A 17-patch baseline

仓库：hhdy/matepad11-dby-w09-agent-reports

分支：ai-parallel/stagea-port-until-boot
固定 commit：2f21233148a04afdd61e44b1be7688399967d9d0
固定 ACK：8ad08f75ddf056e1ee600e1339e0463c5fcbdc9

从固定 commit 读取：
kernel-baseline/round61/round32-stagea-series.txt

严格使用该系列第 1–17 项，按文件记录的顺序逐一应用。第 16/17 项是已通过 ROUND33 第三次复验的 self-target-only driver / binding 补丁，不得遗漏或用旧 patch16 替换。

ROUND33 最终报告记录的身份：
- patch16 blob 3899e2b7ce7f6e028bf3f79ed31fc47cf442abfe
- patch16 SHA-256 7b4858f5bf8f80e83092275afc1add586676b45ebc4f343fa9d2fcb218ec2de4
- patch17 blob d2e818296118672bd708db34ed08d817fcd3895b
- patch17 SHA-256 d19fb3b6ddf43ed5c05c1ca6dc3d7a57602514fb954bb3854b5a7ee78d681d05

17 项顺序应用时，记录真实 offset/fuzz。ROUND33 已报告 patch16/17 会发生非零 offset，但 fuzz=0；不要误判为 patch identity 不匹配。

### 2.2 AI1 ROUND125 patch — 第 1 份新增候选

分支：ai1/round125-qmp-ufs-rail-state

文件：
kernel-baseline/round125/0001-qmp-ufs-rail-state.patch

Git blob：
b2a9a1e6c8f75e858f75e93a5b4ed35ec6bed05d

SHA-256：
71b8a64d20ca0fad1037099cbc864a6aceebacebce057eceb7d4a745cabde330

仅修改：
drivers/phy/qualcomm/phy-qcom-qmp-ufs.c

### 2.3 AI1 ROUND126 patch — 第 2 份新增候选

分支：ai1/round126-proxy-consumer-load-first

文件：
kernel-baseline/round126/0001-proxy-consumer-load-first.patch

Git blob：
c180dbf458403d68b2c32c1d54776a7559e7e5db

SHA-256：
eae21b96d34ebff0e7bbd4843bcd4f96cda26b02f83dd6f323b8c571e51fef80

仅修改：
drivers/regulator/proxy-consumer.c

### 2.4 两份候选的 source review

- ROUND125：kernel-baseline/round125/ROUND125_QMP_UFS_RAIL_STATE_REVIEW.md
- ROUND126：kernel-baseline/round126/ROUND126_PROXY_CONSUMER_LOAD_FIRST_REVIEW.md

## 3. 隔离与补丁应用顺序

1. 新建本任务专用 disposable clone/worktree 和独立 Bazel output base。不得与 ROUND33 的已结束工作区、ROUND124、其他任务共用同一目录。
2. checkout 固定 ACK 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9。
3. 按固定 Stage A series 顺序应用 1–17 项。每个补丁均执行：
   - git apply --check --verbose
   - git apply
   - git diff --check
   记录命令、真实退出码、offset、fuzz。
4. 核对 ROUND125 / ROUND126 patch blob 和 SHA-256，与本任务书完全一致。不匹配即停止并 BLOCKED，不得修复。
5. 在 Stage A 17-patch 树上按以下顺序应用：
   - ROUND125 QMP patch；
   - ROUND126 proxy-consumer patch。
6. 两份新增 patch 各自执行 git apply --check、git apply、git diff --check。要求新增 patch 均 zero offset、zero fuzz。
7. 与 17-patch baseline 相比，新增 dirty paths 必须严格只有：
   - drivers/phy/qualcomm/phy-qcom-qmp-ufs.c
   - drivers/regulator/proxy-consumer.c
8. 不得在 AI2 分支 checkout、commit、apply、reset 或改动任何文件。

## 4. ROUND125 — QMP 双 rail 状态机源码门槛

检查实际应用后的 drivers/phy/qualcomm/phy-qcom-qmp-ufs.c：

A. state:
- struct qmp_ufs 中独立存在 vreg_enabled[2] 与 vreg_load_active[2]。
- vdda-phy-always-on=false 时保留原有 regulator_bulk_enable/disable 路径。
- special path fail-closed：num_vregs==2；index0 为 vdda-phy；index1 为 vdda-pll。

B. init:
- devm_regulator_bulk_get_const() 设置初始 init_load_uA。
- 两个 vreg_load_active 初始值按对应 init_load_uA > 0 设置。
- vreg_enabled 初始 false，不得把已设置 load 误判为 enable reference 已持有。

C. transitions:
- power-on 先恢复各路 active load，再检查 enable reference。
- enabled bit 为 true 时不得重复 regulator_enable。
- regulator_enable 成功后才能将 enabled bit 置 true。
- teardown 先 regulator_set_load(0)，成功后再 regulator_disable。
- 对应操作失败时不得伪造 state bit。

D. power-off/unbind:
- normal PHY power-off：hardware power-down、clocks off 后，L9 load-zero/disable；L5 load-zero 但保持 L5 enable reference。
- L9 cleanup 失败后仍尝试 L5 load-zero。
- hardware 已 off 后 regulator cleanup error 不得造成 PHY core power_count 与 hardware state 不一致；回调按候选方案记录错误并返回成功。
- final devm cleanup 先处理 L9，再处理 L5；每路 load-zero 成功后才 disable；失败 state 不清除。
- 报告 void devm action 无法阻止后续 managed regulator_put，持续失败仍可能导致 nonzero enable_count warning。

## 5. ROUND126 — proxy-consumer load-first teardown 源码门槛

检查实际应用后的 drivers/regulator/proxy-consumer.c：

A. regulator_proxy_consumer_remove():
- 若 current_uA > 0，regulator_set_load(consumer->reg, 0) 必须位于 regulator_disable(consumer->reg) 之前。
- 只有 current_uA > 0 才调用 load-zero；没有 load vote 时不增加无意义调用。
- enable=false 情形仍正常清理 load / voltage / regulator handle。
- deferred consumer 没有 reg handle 的早退路径保持不变，不得解引用 NULL 或 ERR_PTR。
- voltage vote 清理仍按原有路径进行。
- 函数仍正确从 per-rdev unregister 和 late_initcall_sync bulk revoke 两条路径调用。

B. 失败边界：
- load-zero 失败仍记录真实错误；本候选维持 void regulator_unregister 路径的 best-effort cleanup，不得声称能 veto regulator_unregister。
- 不得调用 regulator_force_disable，不得伪造 enable state，也不得声称 persistent provider-disable failure 已解决。

C. 原有 ROUND33 self-target-only 规则：
- 不得被 ROUND126 破坏；self-target validation 与 proxy registration path 必须保留。

## 6. Host tests / Checkpatch / Object compile

1. 在应用 Stage A 17 + ROUND125 + ROUND126 的同一实际树上运行：
   bash tests/run_tests.sh
   预期 legacy suite 38/38，ROUND32/33 suite 83/83。记录每一条真实输出和退出码；不可修改测试。
2. 对 ROUND125 和 ROUND126 分别运行：
   scripts/checkpatch.pl --strict --no-signoff
   记录 errors/warnings/CHECK/RC；不可修改 patch。不得把 RC=1 说成 clean。
3. 用 manifest-pinned Kleaf Clang/toolchain 与 Stage A 配置分别编译：
   - drivers/phy/qualcomm/phy-qcom-qmp-ufs.o
   - drivers/regulator/proxy-consumer.o
   记录完整命令、退出码、对象大小与 SHA-256。
4. 若 object compile 有错误，停止并报告；Agent 不得修补代码。

## 7. Full Image build

ROUND33 的完整构建任务已完成并正式释放。ROUND127 可在本任务的独立 staging 中执行一次完整构建，不需要等待 ROUND33。

命令：
tools/bazel build //common:dby_w09 --jobs=8 --local_ram_resources=6144

成功后记录：
- BUILD_RC / duration
- Image、System.map、vmlinux、.config 的 size / SHA-256
- .config 是否 byte-identical 于 Stage A 17 baseline（expected baseline SHA-256：0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15）
- Image 内容确实包含本轮两份 patch（结合 overlay tracked diff identity、changed object hashes 或 symbols，不得只凭构建成功推断）

不得上传构建二进制。

## 8. Restore / cleanup

1. 将 ROUND125 / ROUND126 两份候选从 disposable tree 中撤销。
2. 检查 pre-overlay / post-restore dirty paths、tracked diff hash、untracked file set 完全一致。
3. 删除本任务临时 worktree、object output 和 build logs；不得清理或改动其他 Agent 工作区。
4. 只保留脱敏后的命令、退出码、hash、工具链版本和报告。

## 9. 绝对禁止与平板连接审批闸门

- 不得修改或修复任何补丁、源码、测试、fixture、binding、DTS、config 或 series。
- 不得修改 main、AI2 Stage A、ACK DTS draft、PR #1、ROUND124、ROUND125、ROUND126 source branches。
- 不得将两份候选合并进 AI2 分支。
- 不得刷写、boot、fastboot、root、解锁或进行任何分区操作。
- 不得上传 Image、vmlinux、System.map、固件、FDT、DTBO 或设备标识。

本任务纯离线，不需要连接平板。如任何步骤似乎需要 USB、ADB、fastboot、recovery、串口或其他设备接口，必须在连接前停止，告诉用户访问类型、原因和拟执行命令，等待用户明确许可。未经明确许可，不得执行任何设备命令，即使只读也禁止。

## 10. 唯一交付物与停止条件

完成后仅新增：
firmware-analysis/round127/TEST_AGENT_ROUND127_COMBINED_REPORT.txt

报告包含：
- 固定 ACK 与 Stage A commit/17 patch identity；
- ROUND125/ROUND126 blob、SHA-256；
- 每一条 patch apply/check/diff 真实 RC、offset、fuzz；
- 两份源码门槛 PASS/FAIL/BLOCKED 证据与行号；
- host tests 38/38 + 83/83 真实结果；
- 两份 checkpatch 统计；
- 两个对象编译结果；
- 完整 Image 构建和 config/artifact hashes；
- workspace restore evidence；
- 明确声明没有连接平板，没有执行任何禁止操作。

只上传本轮唯一报告文件。读回核对成功后立即停止，不得自动启动 ROUND128。
