# [发给测试Agent] ROUND124 新窗口独立验证任务书
## 1号 AI 的 UFS core 双补丁组合验证

- 任务 ID：TEST-AGENT-ROUND124-NEW-WINDOW
- 下发方 / 技术负责人：1 号 AI（ChatGPT）
- 执行方：用户本地 WorkBuddy 测试 Agent
- 审核方：1 号 AI（ChatGPT）
- 任务性质：只读验证、补丁应用检查、编译、测试、报告
- 报告分支：firmware-audit-v1
- 本任务不属于 2 号 AI；Agent 不得替 2 号 AI 修改或验证其 ROUND33 代码。

## 0. 新窗口必须先理解的项目背景

目标设备是 Huawei MatePad 11 2021，型号 DBY-W09，Qualcomm KONA / SM8250。用户希望最终运行 Android 17 DerpFest，但顺序不可颠倒：

1. 先完成 Stage A：把固定 ACK 6.18.33 内核适配到 DBY-W09，并完成可重复构建、启动路径、存储与基础设备验收。
2. 只有 Stage A 验收通过后，才进入 Stage B：Android 17 DerpFest device/vendor/HAL 集成。

本轮只做 Stage A 的离线源码与构建验证。当前不能宣称设备已经启动、UFS 已在真机工作或内核移植已经完成。

固定源码：
- 仓库：aosp-mirror/kernel_common
- 标签：android17-6.18.33_r00
- 固定 commit：8ad08f75ddf056e1ee600e1339e0463c5fcbdc9
- 禁止用 Linux stable v6.18.33 或移动的 android17-6.18 HEAD 替代。

项目参与者有三方，绝不能混淆：
- 1 号 AI（ChatGPT）：本任务补丁所有者和技术负责人。
- 2 号 AI：独立开发者，拥有 ai-parallel/stagea-port-until-boot 分支。本任务严禁修改其分支或将其工作混入本测试。
- 测试 Agent（你）：只按本任务测试，不编写、修改或修复内核补丁。

## 1. 本轮唯一目标

独立验证 1 号 AI 准备的两个 UFS core 候选补丁，按 ROUND120 → ROUND122 顺序叠加到指定的 Stage A ROUND32（15-patch）基线上，确认它们能否同时精确应用、通过源码门槛、编译 UFS 对象并完成完整 DBY-W09 Image 构建。

这是一轮组合验证，不是新功能设计，不是设备测试，也不是向 2 号 AI 分支集成。

## 2. 必须固定的输入身份

项目仓库：
hhdy/matepad11-dby-w09-agent-reports

### 2.1 固定 Stage A 基线

分支：ai-parallel/stagea-port-until-boot
本轮基线 commit（必须 checkout 这个精确 commit，不得改用当前分支 HEAD）：
5f587aaa40853cf3ec754f7455930aa404bf9b9a

原因：本任务明确要以 ROUND32 15-patch 工作树为基线，不包含后来 2 号 AI ROUND33 的 patch 16/17。即使 Stage A 分支已经前进，也必须使用上述不可变 commit 和其中的 kernel-baseline/round61/round32-stagea-series.txt。
基线 ACK 必须仍为：
8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

先确认 15 个 Stage A patch 身份、顺序、SHA-256 与 series 记录；任何不匹配均停止并报告 BLOCKED，不得自行更新期望值。

### 2.2 1号 AI 候选补丁

候选分支：ai1/round124-ufs-core-combined-candidates
本轮发布时记录的候选 branch head：
c89805ee96d64f3771fcdd0ee227296706d63dfa

必须按以下顺序应用：

| 顺序 | 补丁文件 | Git blob SHA | SHA-256 |
|---|---|---|---|
| 1 | kernel-baseline/round124/0001-ufs-core-per-hba-async-domain.patch | f604c8672fcbc98f3e9645f5e8888c8a34b1c11e | 12efbe8a14d80f8b657bad763a344b5439abeb572158079beb32daba05e02bc7 |
| 2 | kernel-baseline/round124/0002-ufs-core-vreg-load-first.patch | 64dd2ad9022251e2411a1a745aeb920a0badfa85 | 2f335f513fd1f7013a0edbc2e0d9eb5dca9ae68055eff4fd526b1c4274cfca66 |

必须同时核对 Git blob SHA 与本地文件 SHA-256。任何一个身份不符，立即停止，不得编辑、重新生成或“修复”补丁。

## 3. 具体测试流程

### A. 隔离环境与基线确认

1. 新建独立 disposable clone / worktree / build workspace，目录只供 ROUND124 使用。不能与 ROUND33 窗口共用目录或 Bazel output base。
2. checkout 固定 Stage A commit 5f587aaa40853cf3ec754f7455930aa404bf9b9a 的 15-patch 状态。
3. 确认 ACK commit、manifest identity、ROUND32 15-patch series、原工作树 dirty paths 和原有文件身份。
4. 记录 workspace 初始 HEAD、tracked/untracked 状态、dirty path 列表和可复核快照 hash。
5. 不要执行 branch checkout 或 reset 操作于用户已有工作区；所有操作仅发生于新建临时副本。

### B. 补丁身份与顺序应用

1. 下载并确认上述两个补丁 blob 和 SHA-256。
2. 在 15-patch Stage A 临时树上依次执行：
   - 对 ROUND120：git apply --check --verbose；成功后 git apply；再 git diff --check。
   - 对 ROUND122：git apply --check --verbose；成功后 git apply；再 git diff --check。
3. 记录每条命令的真实输出和退出码，并检查是否有 offset 或 fuzz。PASS 要求两个补丁均为零 offset、零 fuzz。
4. 两个候选补丁叠加后，新增 source path 应恰好为：
   - drivers/ufs/core/ufshcd.c
   - drivers/ufs/core/ufshcd-priv.h
   Stage A 原有改动必须完整保留。若出现意外的第三个 source path，停止分析并报告，不得擅自改代码。
5. 明确禁止将 AI2 ROUND33 patch 16 或 patch 17 放入本次测试；不得因为它们存在于当前 Stage A 分支就把它们加入 15-patch 基线。

### C. ROUND120 async lifecycle 源码门槛

检查实际应用后的源码，逐项给出文件/函数/行号或代码片段证据：

1. async domain、cookie、scheduled 状态只增加在私有 struct ufs_hba_priv 中；公开 struct ufs_hba 和公共头文件不应被修改。
2. ufshcd_alloc_host() 在可能调度 scan 前初始化 async_domain.pending、registered 状态和 scheduled=false。
3. 唯一 UFS scan schedule site 使用 async_schedule_domain()，并保存其 cookie。
4. ufshcd_remove() 在读取 WLUN 或 teardown 前，通过 cookie + 1 join 该 HBA 的 exact async domain。
5. 无 scan 已调度时，不得等待未初始化 cookie。
6. 检查所有 ufshcd_alloc_host() 调用方与 remove 调用路径，确认没有调用方在 join 前持有会造成死锁的 host_sem。
7. 只能确认源码调用关系；不得将此门槛写成运行时已经通过。

### D. ROUND122 regulator load ordering 源码门槛

1. ufshcd_disable_vreg() 必须先执行带错误检查的 ufshcd_config_vreg(dev, vreg, false)，随后才调用 regulator_disable()。
2. load 清零失败时必须提前返回，不再尝试 regulator_disable()。
3. vreg->enabled 只能在 regulator_disable() 成功之后清零。
4. ufshcd_enable_vreg() 对已启用句柄的 early-exit 前，必须先尝试重新应用 active load；不得为已启用句柄重复 regulator_enable()。
5. 报告必须保留已知限制：该补丁没有解决所有 regulator post-decrement error、devm release 与 nonzero enable_count teardown 风险。不得称为完整 teardown 安全修复。

### E. 组合影响面

必须确认：
- 不修改 public UFS struct layout。
- 不改 Kconfig、DTS、regulator core、binding、defconfig、AVB 或 boot packaging。
- 两个补丁只触及上述两个 UFS core source paths。
- 不调整 Stage A 原有任何 patch 来迁就候选。

### F. 风格检查与对象编译

1. 两份补丁分别执行 ACK scripts/checkpatch.pl --strict --no-signoff。
2. 分别报告 errors、warnings、CHECKs、退出码；不得自行修补风格。
3. 使用固定 manifest/Kleaf toolchain 和同一 Stage A .config 编译 drivers/ufs/core/ufshcd.o。
4. 由于 ufshcd-priv.h 是共享私有头文件，应额外编译所有 UFS core objects，或者提供证据说明选定 Kleaf 目标已经重建所有依赖对象。
5. 记录 object build 输出、实际退出码及 .config SHA-256。

### G. 完整 Image build

完整 Image build 只在本窗口执行；不要与 ROUND33 同时运行。

命令：
tools/bazel build //common:dby_w09 --jobs=8 --local_ram_resources=6144

要求：
- 使用固定 manifest-pinned Repo/Kleaf workspace，ACK 必须为上述 commit。
- 记录 manifest commit、manifest-pinned.xml SHA-256、Clang、Rust、Bazel 版本。
- 不得使用未锁定的系统 Clang 或其他 ACK revision。
- 记录 Image、System.map、vmlinux、.config 的大小和 SHA-256。
- 确认最终 .config 与同一 Stage A 15-patch 基线的 .config 字节一致；若不一致，查明并记录真实原因，不得直接标 PASS。
- 不上传 Image、vmlinux、System.map 或其他构建产物。

### H. 工作区还原

1. 恢复临时副本至叠加补丁前的 15-patch Stage A 状态。
2. 证明原 dirty path 列表与初始完全一致，并核对 diff/snapshot hash。
3. 清理本任务临时 staging/worktree；保留可复核日志和 hash，但不得泄露用户目录名、令牌或隐私数据。
4. 不得清理或修改 ROUND33 窗口工作区。

## 4. 并行资源协调

ROUND124 是本轮第一个完整 Image build，拥有优先构建时段。

- 允许与 ROUND33 窗口并行进行 patch hash、apply、diff、source gate、checkpatch、host/schema tests。
- ROUND33 窗口不得与本任务同时运行完整 Bazel Image build。
- 完成本轮 full build、还原工作区、上传并读回报告后，向用户报告“ROUND124 BUILD SLOT RELEASED”。不要代替 ROUND33 窗口运行其构建。

如果发现 full build 即将与另一个完整 Bazel build 重叠，应停止启动 build 并通知用户协调。不得为了并行而降低测试要求或复用另一窗口的 build 结果。

## 5. 绝对禁止

- 不得编辑/重排/修复/重新生成任何一个候选 patch。
- 不得写内核 C、DTS、binding、测试、Kconfig 或 firmware。
- 不得修改 main、ack18-dby-w09-dts-draft、PR #1、ai-parallel/stagea-port-until-boot、firmware-audit-v1 上的其他文件或任何 AI2 分支。
- firmware-audit-v1 只允许新增本任务唯一报告文件。
- 不得将 1 号 AI 候选合入 AI2 Stage A。
- 不得包括 patch 16/17，不得启动 ROUND125。
- 不得访问、上传或重新导出 HOS4.3 原始固件、FDT、DTBO 或设备标识。

### 平板连接审批闸门

本任务不需要连接平板。若任何命令或测试被判断为需要 USB、ADB、fastboot、recovery、串口或任何设备接口，必须在连接前停止，并提交：
- 需要何种设备访问；
- 具体目的；
- 拟执行命令；
- 为什么不能用离线源码/编译验证替代。

只有用户明确授权后，才可另行建立设备任务书。即使只读访问也适用。不得自行连接。

## 6. 唯一交付物与结束条件

完成后仅新增并上传以下文件到 firmware-audit-v1：
firmware-analysis/round124/TEST_AGENT_ROUND124_COMBINED_UFS_CORE_REPORT.txt

报告必须包括：
- 精确 ACK、Stage A commit、15-patch series、manifest 和工具链身份；
- 两个 patch 的 Git blob SHA 与 SHA-256；
- 每步命令、退出码、零 offset/fuzz 证据；
- ROUND120/ROUND122 每个源码 gate 的证据；
- checkpatch 统计与退出码；
- UFS 对象编译结果；
- 完整 Image build、Image/System.map/vmlinux/.config 哈希；
- 工作区恢复前后证据；
- 明确声明没有连接平板、没有访问分区、没有执行禁止动作；
- 全部状态按 PASS / FAIL / BLOCKED / NOT RUN 区分。

报告上传后必须重新从 GitHub 读回，确认内容与本地报告一致。随后立即停止，不得自动启动其他 Round。