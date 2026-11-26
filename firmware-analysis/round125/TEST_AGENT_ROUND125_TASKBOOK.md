# SUPERSEDED — DO NOT EXECUTE THIS STANDALONE TASKBOOK

ROUND33 has now passed all gates and AI1 has prepared ROUND126. The active
Agent task is the combined AI1 ROUND127 taskbook, which validates both
ROUND125 and ROUND126 on the same verified Stage A 17-patch baseline and uses
one full Image build:

firmware-analysis/round127/TEST_AGENT_ROUND127_COMBINED_TASKBOOK.md

The older standalone ROUND125 instructions below are retained as history
only. Do not use their 15-patch baseline or their instruction to exclude
ROUND33 patches 16/17.

---

# [发给测试Agent] AI1-ROUND125 独立验证任务书
## QMP UFS PHY 的 L5/L9 双 rail 状态管理候选

- Task ID: TEST-AGENT-AI1-ROUND125
- 下发方 / 技术负责人：1号 AI（ChatGPT）
- 执行方：用户本地 WorkBuddy 测试 Agent
- 代码所有者：1号 AI
- 审核方：1号 AI（ChatGPT）
- 测试类型：补丁身份、精确应用、源码门槛、checkpatch、目标对象编译、完整 Image 构建
- 报告分支：firmware-audit-v1
- **Agent 只测试，不得编辑或修复补丁/源码/测试。**
- **本任务不属于 2 号 AI；不得修改 AI2 分支。**

## 0. 项目背景与目标

设备：Huawei MatePad 11 2021，DBY-W09，Qualcomm KONA / SM8250。

项目目标按严格顺序执行：
- Stage A：先完成 DBY-W09 的 ACK 6.18.33 内核移植、可重复构建、内存/电源/启动链核验以及设备启动和存储验收。
- Stage B：只有 Stage A 验收通过后，才开始 Android 17 DerpFest 的 device/vendor/HAL 适配。

固定源码为 aosp-mirror/kernel_common 的 `android17-6.18.33_r00`，commit：
`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`。
不得用 Linux stable v6.18.33 或移动的 android17-6.18 HEAD 替代。

项目角色必须严格区分：
- 1号 AI（ChatGPT）：本轮 patch 所有者、设计和源码审查负责人。
- 2号 AI：独立开发 AI，拥有 `ai-parallel/stagea-port-until-boot`。
- 测试 Agent（你）：只做任务书范围内的离线验证和构建；不是 2号 AI，不得编写或修复内核代码。

## 1. 本轮唯一目标

验证 1号 AI 的 QMP UFS 双 rail 状态管理补丁是否可以精确应用到 AI2 ROUND63 已有的 Stage A 15-patch 树，满足源码状态机门槛，经过 checkpatch，并编译 QMP UFS PHY 对象及完整 DBY-W09 Image。

本轮只验证离线源码。不得连接平板或声称真实 PHY/PMIC rail 行为已验证。

## 2. 固定输入身份

仓库：`hhdy/matepad11-dby-w09-agent-reports`

### 2.1 固定 Stage A 基线

AI2 branch：
`ai-parallel/stagea-port-until-boot`

固定基线 commit：
`5f587aaa40853cf3ec754f7455930aa404bf9b9a`

固定 ACK commit：
`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

使用固定 commit 中 `kernel-baseline/round61/round32-stagea-series.txt` 的 **第 1–15 项**，即 ROUND31 + ROUND32 的已应用验证基线。该历史记录在第 15 项后面可能附有 ROUND33 pending patch 16 记录；本任务严格只应用 1–15，**禁止应用任何 ROUND33 patch 16/17**。

ROUND63 QMP UFS PHY change is item 8 of this 15-patch sequence:
- File: `kernel-baseline/round61/patches/round63-0001-phy-qcom-qmp-ufs-always-on.patch`
- Expected Git blob: `99fffb10603b38bc30a0e6c9db99b0e9888a7b82`
- Expected SHA-256: `d33e1d405cc6c855de9a3867ec7e39a25e7bec2f6f74924cb1bbc6a86b1f9539`

这项 patch 必须已按第 8 项顺序应用，然后才应用本任务的 AI1 patch。不要用未经过验证的当前 AI2 branch HEAD 替代固定 commit。

### 2.2 AI1 ROUND125 candidate

Candidate branch:
`ai1/round125-qmp-ufs-rail-state`

Patch:
`kernel-baseline/round125/0001-qmp-ufs-rail-state.patch`

Expected Git blob:
`b2a9a1e6c8f75e858f75e93a5b4ed35ec6bed05d`

Expected SHA-256:
`71b8a64d20ca0fad1037099cbc864a6aceebacebce057eceb7d4a745cabde330`

Patch 只改：
`drivers/phy/qualcomm/phy-qcom-qmp-ufs.c`

必须重新计算 patch 的 Git blob / SHA-256。任何一个不符，立即停止并报告 BLOCKED，不得编辑、修复或重新生成 patch。

## 3. 隔离工作区

1. 创建本任务独立 disposable clone/worktree/build staging。
2. 不得与 ROUND33 Agent 窗口、ROUND124 工作区、AI2 分支现有工作区共用同一工作目录或 Bazel output base。
3. checkout 精确 ACK commit，应用 Stage A 系列第 1–15 项，再应用 ROUND125 patch。
4. 不得应用 AI2 ROUND33 patch 16/17，也不得应用 AI1 ROUND120/122 candidate；本轮单独验证 QMP patch。
5. 不得在 AI2 工作分支上 checkout、reset、apply、commit 或修改文件。

## 4. 补丁应用步骤

对基础 Stage A 的第 1–15 个 patch，逐个执行：
- `git apply --check --verbose`
- `git apply`
- `git diff --check`

随后核对 ROUND63 patch 仍与预期 blob/SHA 一致，并确认它属于已应用的 15 项基线。最后应用 ROUND125：
- `git apply --check --verbose 0001-qmp-ufs-rail-state.patch`
- `git apply 0001-qmp-ufs-rail-state.patch`
- `git diff --check`

记录每条命令的真实输出、退出码、offset/fuzz。ROUND125 要求零 offset、零 fuzz。若任一 hunk 失败，不得手工调整 hunk。

ROUND125 相对 Stage A 基线的增量应严格只有：
`drivers/phy/qualcomm/phy-qcom-qmp-ufs.c`

不得改变 Stage A 原有文件或 AI2 patch。

## 5. 必须核对的源码门槛

直接检查应用后的真实源码，给出函数/行号/片段证据。

### A. 双 rail 私有状态

1. `struct qmp_ufs` 有独立的 `vreg_enabled[2]` 和 `vreg_load_active[2]` 状态。
2. `vdda_phy_always_on` 为 false 时，原先的 `regulator_bulk_enable/disable` 普通路径不变。
3. special path 必须 fail-closed：`num_vregs == 2`，index 0 supply 为 `vdda-phy`，index 1 supply 为 `vdda-pll`；其他布局拒绝，不猜测。

### B. 初始负载状态

1. `devm_regulator_bulk_get_const()` 在 probe 中已复制 `init_load_uA` 并设置正数初始负载。
2. special property 解析后，`vreg_load_active[i]` 按各自 `init_load_uA > 0` 初始化。
3. enable bits 初始为 false；不能把已设置初始 load 误判为 enable reference 已持有。

### C. load transition

1. load active 时使用对应 `init_load_uA`，idle 时使用 0。
2. 只有 `regulator_set_load()` 成功后才改变 `vreg_load_active[index]`。
3. load-zero 失败后不得调用同一 rail 的 `regulator_disable()`；state 必须保留。

### D. enable-reference transition

1. power-on 必须先恢复 active load，再判断当前 enable reference 是否已经持有。
2. 对 `vreg_enabled[index] == true` 的 rail 不得再次调用 `regulator_enable()`。
3. 只有 `regulator_enable()` 成功后才把 enabled bit 置 true。
4. disable 路径必须 load-zero first；只有 `regulator_disable()` 成功才清除 enabled bit。
5. disable 或 load-zero 失败不得清除相应状态位。

### E. Power-on / partial failure

1. 两个 rail 必须各自跟踪；L9 的前次 disable 失败而仍持有 enable reference 时，下一次 power-on 不得重复 enable。
2. power-on 中途失败时，应尝试使 L9 回到 idle，并清零 L5 load；不能因为一个 rail 清理失败就伪造另一个 rail 的状态。
3. clock enable 失败后的 unwind 必须调用 state-aware disable helper，不能丢弃残余引用状态。

### F. Power-off / final cleanup

1. normal power-off：先硬件 power-down、关 clocks；然后 L9 load-zero → disable，L5 load-zero 但保留其 enable reference。
2. L9 cleanup failure 不得阻止尝试 L5 load-zero。
3. PHY 硬件已关、clocks 已关后，regulator cleanup failure 需要记录状态并返回成功，不能用 regulator 错误造成 PHY core power_count 与实际硬件状态不一致。
4. final devm action 必须处理 L9 与 L5：先 load-zero，成功后再 disable；L9 在前、L5 在后；任一路失败都不能提前清除状态位，且仍继续尝试另一路。
5. 必须说明 devm callback 为 void，不能阻止后续 managed regulator_put；persistent disable failure 仍可能产生 nonzero enable_count warning。不得声称该边界被完全消除。

## 6. Checkpatch 和编译

1. 在固定 ACK tree 对 ROUND125 patch 单独执行：
   `scripts/checkpatch.pl --strict --no-signoff`
   记录 errors / warnings / CHECK / 退出码，不修改 patch。
2. 使用 manifest-pinned Kleaf Clang/Rust/Bazel toolchain 编译：
   `drivers/phy/qualcomm/phy-qcom-qmp-ufs.o`
   使用本轮 Stage A 配置；记录完整命令、退出码、对象大小与 SHA-256。
3. 检查是否有其他编译目标因头文件/宏等受到影响；本补丁只改 .c 文件，但仍记录依赖编译事实。

## 7. 完整 Image build 时段约束

完整命令：
`tools/bazel build //common:dby_w09 --jobs=8 --local_ram_resources=6144`

**当前 ROUND33 最新复验报告发现测试套件失败；2号 AI 随后更新了 test harness，但该新版本还没有独立 Agent 验证。ROUND33 revalidation 是当前优先验证任务。**

因此本轮严格两阶段：

- 可先做 patch identity、1–15 apply、ROUND125 apply、源码门槛、checkpatch 和 QMP 对象编译。
- 不得与 ROUND33 Agent 同时启动完整 Image build。
- 在完整 Image build 前，检查 `firmware-analysis/round33` 最新报告和并行派发文档。只有 ROUND33 已完成其修复后重测、完整 Image build 已结束，并明确发布 `ROUND33 FULL BUILD SLOT RELEASED`，才可开始本轮完整 Image build。
- 如果 ROUND33 尚未验证完成，停止在：
  **ROUND125 PREBUILD COMPLETE — WAITING FOR ROUND33 BUILD SLOT**
  将已完成的前置验证记录给用户；不要自行推测资源已释放。
- 收到用户明确继续指令或派发文档已明确释放后，再运行 full build。

完整 build 成功后，记录 Image、System.map、vmlinux、.config 大小和 SHA-256；确认 .config 对比同一 15-patch baseline 没有非预期变化。不得上传构建产物。

## 8. 工作区清理

1. 构建后还原 ROUND125 patch 对临时 Stage A 树的增量。
2. 验证 ROUND125 前后 dirty paths 与 tracked diff SHA 完全一致。
3. 删除本任务独立 staging/worktree 与对象临时文件；不得清理其他 Agent 工作区。
4. 只保留脱敏日志、命令、工具链、hash、退出码和报告。

## 9. 绝对禁止

- 不得修改/修复/reformat/re-generate ROUND125 patch。
- 不得修改 AI2 的 ROUND63/ROUND32/ROUND33 源码、patch、tests、fixtures、series 或 PROGRESS。
- 不得修改 main、DTS draft、PR #1、ROUND124 文件或其他 AI1 patch。
- 不得把 ROUND125 合并到 AI2 分支。
- 不得新增 DTS、binding、Kconfig 或 boot 包装改动。
- 不得上传构建二进制、固件、FDT、DTBO 或设备标识。
- 不得使用 regulator_force_disable 或任何 force-disable shortcut。

### 平板连接审批闸门

本任务完全离线，不需要连接平板。如任何步骤似乎需要 USB、ADB、fastboot、recovery、串口或其他设备接口，必须在连接前停止，写明访问类型、原因、拟执行命令并交给用户。未经用户明确许可，任何设备命令都禁止执行，即使只读。不得刷机、root、解锁、reboot、分区读写或临时启动。

## 10. 唯一交付物与停止条件

完成后仅新增：
`firmware-analysis/round125/TEST_AGENT_ROUND125_QMP_UFS_RAIL_STATE_REPORT.txt`

报告需包含：
- 固定 ACK、Stage A commit、准确采用的 1–15 patch 身份；
- ROUND63 patch identity；
- ROUND125 blob / SHA-256；
- 每条 apply/check/diff 退出码与 offset/fuzz；
- 每个源码门槛的 PASS/FAIL/BLOCKED 证据；
- checkpatch 真实统计；
- QMP object build 结果；
- 若构建时段已释放，完整 Image 结果与 hashes；否则明确标记 NOT RUN（等待 ROUND33 build slot）；
- workspace restore 证据；
- 明确声明无设备访问 / 无禁止操作。

只上传本轮唯一报告文件，读回核对成功后立即停止，不得自动启动 ROUND126。
