# [发给测试Agent] AI2-ROUND33 新窗口重新验证任务书
## 2号 AI 的 regulator proxy self-target-only 补丁（patch 16 + patch 17）

- 任务 ID：TEST-AGENT-AI2-ROUND33-REVALIDATION-NEW-WINDOW
- 下发方 / 技术负责人：2 号 AI（独立开发 AI）
- 执行方：用户本地 WorkBuddy 测试 Agent
- 代码所有者：2 号 AI
- 第一审核方：2 号 AI
- 独立复核方：1 号 AI（ChatGPT）在报告上传后复核
- 任务性质：只读验证、补丁应用检查、自动化测试、schema 检查、编译、报告
- 报告分支：firmware-audit-v1
- 重要：你是测试 Agent，不是 2 号 AI。代码已经由 2 号 AI 写入专属分支；本轮不得编写、重写、编辑或修复代码。

## 0. 新窗口必须先理解的项目背景

设备是 Huawei MatePad 11 2021，型号 DBY-W09，Qualcomm KONA / SM8250。最终项目目标是 Android 17 DerpFest，但严格按两阶段推进：
- Stage A：先移植固定 ACK 6.18.33 内核到 DBY-W09，完成可重复内核构建、内存/电源/boot handoff 审查，以及设备启动和存储/基础硬件验收。
- Stage B：只有 Stage A 验收通过后，才开始 Android 17 DerpFest 的 device/vendor/HAL/ROM 适配。

本轮属于 Stage A。编译成功不等于设备内核已启动，也不代表实际 UFS、PMIC 电源或 L5/L9 在真机上已经工作。

固定源码：
- aosp-mirror/kernel_common
- tag android17-6.18.33_r00
- immutable commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9

不要用 Linux stable v6.18.33 代替 ACK，不要切换到移动的 android17-6.18 HEAD。

## 1. 角色边界

本项目有三个不同参与者：
1. 1 号 AI（ChatGPT）：进行独立源码审查、候选方案和跨任务审查。
2. 2 号 AI：独立开发者，拥有 Stage A 实际实现分支 ai-parallel/stagea-port-until-boot。本任务补丁由它实现。
3. 测试 Agent（你）：只执行本任务的本地验证、构建和报告上传。你不是 2 号 AI；你不得决定替换方案，也不得修复它的代码。

你只负责验证，不负责实现。如果失败，提供精准证据让 2 号 AI 决定修复。不要把 Agent 测试任务误当成 2 号 AI 代码任务。

## 2. ROUND33 为什么存在

ROUND32 已增加 child-scoped proxy-supply，使 PM8150 同一 regulator group 内的 L5、L9 可以各自拥有 proxy consumer，避免两路临时负载票误落到同一 rail。

ROUND32 的生命周期审查发现一个重要边界：
- proxy consumer handle 实际存放在请求方/owner regulator rdev 的 per-rdev 状态里。
- 如果 child proxy-supply 可以指向任意其他 regulator，那么 target regulator 可能先 unregister，而 owner 的清理 hook 尚未运行。
- ACK regulator_unregister() 中 open_count warning 不是禁止注销的保护；出现 open handles 时 core 仍可能继续 unregister。
- 因此，不能只依赖 target 的 open_count warning，也不能允许 owner 与 target 任意不同。

2 号 AI 的 ROUND33 选择了一个范围严格、可验证的解决策略：**self-target-only**。
- child-scoped proxy-supply 必须指向发起该 proxy request 的同一个 regulator child node。
- legacy provider/group-level proxy-supply 也必须解析为当前请求 child 自己；因此 legacy 模式只允许 group 中唯一匹配的 child 提交 proxy request，其他 child 的跨目标请求必须被拒绝。
- 不允许跨 regulator proxy handle。
- 必须在获取 regulator handle 或应用任何 proxy vote 之前校验 phandle。非 self-target 返回 -EINVAL。
- 每个 proxy handle 的 owner 和 target 都是同一个 regulator rdev；owner unregister hook 负责撤销自己的 handle。
- Binding 文档必须准确描述运行时 self-target 约束。
- L5/L9 方案仍然保留：L5 的 proxy-supply 指向 L5 自身，L9 的 proxy-supply 指向 L9 自身，因此两路独立 self-target 不互相覆盖。

本任务要验证 2 号 AI 的提交能否真实应用、测试、通过 schema 和完整 Image build；不能只验证 Markdown 描述。

## 3. 当前要验证的固定候选身份

仓库：
hhdy/matepad11-dby-w09-agent-reports

Stage A 分支：
ai-parallel/stagea-port-until-boot

本任务锁定分支快照 commit：
c4ee77184e2bf4e4eadf6280e67a510be5e729e5

必须从该精确 commit 读取 patch、series、tests、manifest 和进度文件。不得把“当前最新分支 HEAD”作为动态输入；如该 commit 内容与以下身份不一致，停止并报告 BLOCKED。

固定 ROUND32 基线：
98fda4151bea7b4a7a717054c431f59a7ff23bb6

ROUND33 之前的基础 15-patch series：
kernel-baseline/round61/round32-stagea-series.txt

ROUND33 增加的 patch 16 和 patch 17：

| 顺序 | 文件 | Git blob SHA | SHA-256 |
|---|---|---|---|
| 16 | kernel-baseline/round61/patches/round33-0001-regulator-proxy-self-target-only.patch | 3899e2b7ce7f6e028bf3f79ed31fc47cf442abfe | 7b4858f5bf8f80e83092275afc1add586676b45ebc4f343fa9d2fcb218ec2de4 |
| 17 | kernel-baseline/round61/patches/round33-0002-regulator-proxy-self-target-binding.patch | d2e818296118672bd708db34ed08d817fcd3895b | d19fb3b6ddf43ed5c05c1ca6dc3d7a57602514fb954bb3854b5a7ee78d681d05 |

当前应验证的顺序 series 是 17 个 patch：
- 1–15：ROUND31 + ROUND32 的既有补丁，保持不变；
- 16：ROUND33 runtime self-target-only 校验；
- 17：ROUND33 regulator binding 描述同步更新。

patch 16 / patch 17 必须同时满足 Git blob 与 SHA-256。若不符，不得更新期望值或修复补丁。

### 历史失败报告必须保留

此前第一次 ROUND33 验证曾因当时的 patch 16 hunk counts 格式损坏而失败。该历史报告位于：
firmware-analysis/round33/AI2_ROUND33_TARGET_UNREGISTER_LIFECYCLE_REPORT.txt

它是失败版本的历史证据，禁止覆盖、删除或改写。当前任务是对已经拆分修正的 patch 16 + patch 17 进行第二次独立验证，必须新增报告，不得沿用旧 PASS/FAIL。

## 4. 独立工作区与隔离要求

1. 使用单独的 ROUND33 disposable clone/worktree/build workspace。
2. 不得与 ROUND124 窗口共用 Git 工作目录、Bazel output base、Repo checkout 或 staging 目录。
3. 本任务只能修改临时 disposable worktree；源仓库和所有 AI 分支均不可直接修改。
4. 先核验 Stage A 快照 commit、15-patch series、patch 16/17 的 blob 与 SHA-256。
5. 不要直接在 2 号 AI 的 branch checkout 上执行 apply；从固定 ACK 建立一次性 worktree，逐项应用完整 17-patch series。

## 5. 严格测试步骤

### A. 身份核验与完整 series apply

1. 固定 checkout ACK commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9。
2. 读取并核验 15-patch 基线 series 的每一个文件、顺序、Git blob 与 SHA-256。
3. 核验 patch 16/17 的当前 blob / SHA-256 与上表一致。
4. 使用一次性 ACK worktree，按完整 17-patch series 顺序逐个执行：
   - git apply --check；
   - git apply；
   - git diff --check。
5. 每一个 patch 都记录检查、应用、diff-check 的退出码；记录任何 offset/fuzz。全部补丁需精确应用，无 offset、无 fuzz。若任一 patch 失败，立即停止；不得编辑、修复、重生成或重排任何 patch。
6. 记录最终变更路径与统计，确认 patch 16 只修改 drivers/regulator/proxy-consumer.c，patch 17 只修改 Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml；Stage A 的既有变更完整保留。

### B. Patch 16 运行时源码门槛

直接检查应用后的真实源码，不要只看 patch 描述：

1. self-target helper 是否从 proxy-supply 属性解析 phandle。
2. phandle 解析后是否比较实际 device_node identity，而不只是节点名字字符串或 compatible。
3. 目标不相同是否在 regulator_get/of_regulator_get 之前返回 -EINVAL。
4. 非 self-target 拒绝路径是否在任何 enable/load vote 之前发生。
5. child-scoped 和 legacy provider-level 两种路径是否都覆盖。
6. legacy provider-level mapping 下，只有 proxy-supply 指向自己的 child 才能发起 proxy request；其他 child 的跨目标请求必须失败。
7. 校验失败时是否正确释放 node reference、解锁并返回；不得泄漏 of_node_get/parse reference。
8. 成功路径是否仍保留 ROUND32 的 deferred retry、自身 handle 所有权和 cleanup 流程。
9. 不得误认为该方案支持任意 cross-target 生命周期；它明确拒绝跨 regulator target。

### C. Binding 门槛

检查 qcom,rpmh-regulator.yaml：
1. child-level proxy-supply 描述明确写出 phandle 必须指向当前 regulator child 自身。
2. legacy provider-level 描述明确写出只能由 target 自身的 child 请求 proxy consumer。
3. 文档和运行时实现一致。
4. group-level 与 child-level 混用仍然被禁止。
5. 不得放宽 unevaluatedProperties/additionalProperties，不得删除现有严格性或吞掉未知属性诊断。

### D. 可复现 host tests

执行仓库提交的：
kernel-baseline/round61/tests/run_tests.sh

确认测试真实编译并执行相关 proxy-consumer 实现，不可用简单 grep 数量代替。至少核对：
- ROUND31 原始 38 checks 仍通过；
- ROUND32 原有测试套件仍通过；
- ROUND33 新增的 9 条断言实际执行；
- child cross-target 在 handle lookup 前被拒绝；
- legacy provider-level cross-target 在 lookup 前被拒绝；
- legacy self-target 正向路径仍通过；
- 原有 child self-target、group/child 混用拒绝、deferred retry 行为无回退；
- cleanup 幂等与 node reference 配对行为未被破坏。

必须记录 run_tests.sh 真实输出的总 checks、失败数、退出码。不要把“38 + 73 + 9”预先写成实际通过数；只有命令真实输出才是证据。若工具脚本拆分输出，分别记录各 suite 结果并汇总真实总数。

### E. Binding / schema / DTS gates

1. 对完整 17-patch disposable tree 执行真实 dt_binding_check。
2. 对被修改的 qcom,rpmh-regulator.yaml 执行 dt-doc-validate。
3. 执行相关 UFS / PMIC regulator 正向与负向 DTS fixtures。
4. 至少证明合法 self-target 配置通过、错误 phandle/type/undeclared property 按预期拒绝；legacy 与 child 的合法/非法组合均覆盖。
5. 保留严格 schema 行为。若工具缺失或 ACK 上游既有 schema warning/error 造成退出码不清晰，必须逐项说明，不能把 warning 隐藏后标 PASS。

### F. ROUND58 配置回归

执行仓库已有 ROUND58 配置检查：
- 33/33 必需 config symbols 应为 =y；
- helper tests 11/11 应通过。

必须从本次实际 17-patch build/config 的 .config 运行；不得引用 ROUND32 旧 build 的结果替代本轮结果。

### G. 完整 manifest-pinned Image build（受构建时段约束）

完整命令：
tools/bazel build //common:dby_w09 --jobs=8 --local_ram_resources=6144

要求：
1. 使用仓库锁定的 manifest-pinned Repo/Kleaf workspace。
2. 固定 ACK commit 仍是 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9。
3. 核对 manifest commit 和 manifest-pinned.xml SHA-256。
4. 记录真实 Clang、Rust、Bazel 版本/身份，不得拿 PATH 中任意工具冒充 pinned toolchain。
5. 记录 Image、System.map、vmlinux、.config 的大小与 SHA-256；构建产物不得上传。
6. 报告本次 17-patch Image build 的实际结果，不得拿以前 ROUND32 或 ROUND61 build 结果替代。

**资源调度：ROUND124 窗口优先执行完整 Image build。**
你可以与 ROUND124 同时进行 SHA 核验、patch apply、静态门槛、host tests、schema checks 和 config regression；但抵达本节时不得启动完整 Bazel Image build。
先完成前述检查并整理 evidence，向用户报告：
ROUND33 PREBUILD COMPLETE — READY FOR FULL IMAGE BUILD
随后暂停，不得与 ROUND124 同时编译。收到用户明确的继续指令（确认 ROUND124 build 已完成并释放构建时段）后，再执行本节 G 和 H，最后上传完整报告。不得自行推测另一个窗口已释放资源。

### H. 工作区还原和清理

1. 还原一次性 worktree 到应用 patch 前的状态。
2. 证明临时工作区文件、dirty paths、diff snapshot 在清理前后符合预期。
3. 清理 ROUND33 专用 staging/worktree；不得清理 ROUND124 或用户现有目录。
4. 构建产物不上传；只保留经过脱敏的命令日志、源码路径、SHA 和退出码。

## 6. 绝对禁止事项

- 不得编辑、修复、重新生成、重排 patch 16/17 或 1–15 任一历史 patch。
- 不得修改 kernel C、DTS、YAML binding、Kconfig、测试脚本、fixtures、series、PROGRESS 或 manifest。
- 不得创建额外 patch；不得提交到 ai-parallel/stagea-port-until-boot 或 1 号 AI 分支。
- Agent 不得替 2 号 AI做代码决策。任何失败只记录证据、停止受影响下游门槛并报告给 2 号 AI。
- 不得覆盖/删除第一次失败报告。
- 不得自动启动 ROUND34 或其他新 Round。
- 不得修改 main、ack18-dby-w09-dts-draft、PR #1、ROUND124 候选或 ROUND124 报告。
- 不得创建 boot、DTBO、AVB/vbmeta/footer 包，不得做刷机/解锁/root/分区操作。
- 不得猜测 PM8150 parent supply、VPH_PWR 或 PMIC 电压。
- 不得上传 HOS4.3 固件、FDT、DTBO、设备身份信息或构建二进制。

### 平板连接审批闸门

本任务仅为离线源代码、测试和构建，不需要连接平板。如任何步骤似乎需要 USB、ADB、fastboot、recovery、串口或其他设备接口，必须先停止，不得连接或发设备命令；将具体需要、理由和命令报告给用户，等待用户明确批准后另发独立设备任务书。该规则也适用于只读访问。

## 7. 唯一交付物和结束条件

只新增一份 revalidation 报告到 firmware-audit-v1：
firmware-analysis/round33/AI2_ROUND33_REVALIDATION_REPORT.txt

禁止覆盖历史失败报告：
firmware-analysis/round33/AI2_ROUND33_TARGET_UNREGISTER_LIFECYCLE_REPORT.txt

报告必须明确区分：
- 候选补丁已提交；
- 本次离线测试是否通过；
- schema / host test / config / full Image 各自状态；
- 未执行或被资源时段阻塞的项目；
- 没有任何设备访问；
- 是否证明的是 self-target-only 限制，而不是通用 cross-target tracking。

每个项目只能使用 PASS / FAIL / BLOCKED / NOT RUN / UNKNOWN。给出真实命令、退出码、日志摘要、patch identities、工具链、产物 hash 和 cleanup 证据。

报告完成后，从 GitHub 读回确认上传成功，立即停止。不要启动 ROUND34。