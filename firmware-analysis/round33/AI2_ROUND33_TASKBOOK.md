# 2号 AI 专属任务书 — AI2-ROUND33
## Stage A 实际内核修复：child-scoped proxy consumer 的 target-unregister 生命周期

**任务归属：2号 AI 专属任务书。** 只属于2号 AI，不得与1号 AI任务合并。  
**任务 ID：** AI2-ROUND33  
**类型：** 实际内核编程、regulator-core 生命周期修复、可复现测试、完整 Image 重编。  
**Stage A 分支：** ai-parallel/stagea-port-until-boot  
**报告分支：** firmware-audit-v1  
**固定 ACK：** android17-6.18.33_r00 = 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a。  
**ROUND32 基线提交：** 98fda4151bea7b4a7a717054c431f59a7ff23bb6。

## 0. 本轮唯一目标

关闭 2号 AI 对 ROUND32 的独立审阅发现的 target-unregister 生命周期缺口。

ROUND32 的 child-scoped proxy-supply 当前允许 child phandle 指向任意 regulator，但 proxy consumer 只挂在请求方/owner rdev 的 rdev->proxy_consumer 上。若被引用的 target rdev 在 owner 之前 unregister，target 的 regulator_unregister() 不会找到并释放该 proxy handle。ACK regulator core 的 WARN_ON(rdev->open_count) 是诊断，不是拒绝 unregister 的保护；不能据此声称 target unregister 已安全处理。

本轮必须在不破坏 ROUND32 L5/L9 自身 self-target 方案的前提下，给出并实现可证明安全的策略：
1. 支持任意 child target 时，必须在 target rdev unregister 之前撤销所有引用它的 proxy consumers，释放 handle、清空 owner back-pointer，并与 individual unregister / bulk revoke 正确串行化；或
2. 若 ACK core 无法安全支持通用 target 生命周期，则将 child-scoped 模式严格限制为 self-target（phandle 必须指向当前 regulator child 本身），在注册时拒绝非 self-target，并证明 L5/L9 需求仍完整满足。不得只在文档中建议 self-target，却不在运行时强制。

先对固定 ACK 的 regulator_unregister()、open_count、regulator handle/refcount、proxy hook 和锁顺序作源码追踪，再决定采用哪条路径。不能以 WARN_ON、mock-only 断言或“正常情况下不会发生”代替保护。

## 1. 必须继承的基线

- 固定 ACK：8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a。
- ROUND31 12-patch series：kernel-baseline/round61/round31-stagea-series.txt。
- ROUND32 追加 patch 13-15：kernel-baseline/round61/round32-stagea-series.txt。
- ROUND32 实现记录：kernel-baseline/round61/round32-child-scoped-proxy-implementation.md。
- ROUND32 测试：kernel-baseline/round61/tests/，必须保留 38-check 与 73-check 两套测试。
- ROUND32 审阅报告：firmware-analysis/round32/AI2_ROUND32_CHILD_SCOPED_PROXY_IMPLEMENTATION_REPORT.txt。
- ROUND32 Stage A commit：98fda4151bea7b4a7a717054c431f59a7ff23bb6。
- L5/L9 review DTS：arch/arm64/boot/dts/qcom/dby-w09-proxy-review.dts，仅 review artifact，不是可启动 DTS。

ROUND32 已实现 child-scoped of_regulator_get(dev, node, "proxy")、group/child 混用拒绝、deferred retry、严格 binding、L5/L9 self-target review DTS、host suites 和完整 Image build。本轮不得回退这些功能，不得改写 ROUND31/32 历史 patch blob；只追加明确的新 patch。

## 2. 设计门槛：必须证明 target 生命周期

逐项审计：
- 固定 ACK 的 regulator_unregister() 是否在 WARN_ON(rdev->open_count) 后仍继续注销 rdev；准确记录注销顺序。
- target handle 对 rdev 的 class/device 引用、open_count、regulator_put 的完整生命周期。
- owner rdev 与 target rdev 相同（self-target）及不同（cross-target）两种路径。
- target unregister 先于 owner unregister、owner unregister 先于 target unregister、late_initcall_sync 与两种 unregister 交错时的行为。
- 所有清理必须在 target rdev 被移除/释放前完成；不得留下 handle 指向正在注销或已注销的 rdev。
- 证明 proxy list mutex、regulator core locks、regulator_disable/set_load/regulator_put 的锁顺序，不得引入反向锁序或在错误锁下调用 regulator API。
- deferred consumer（尚无 handle）也必须从待处理列表正确清理；target 从未注册与 target 已注册后注销必须区分。
- target cleanup、owner cleanup、bulk revoke 必须幂等：每个 enable/load vote 最多撤销一次，每个 handle 最多 put 一次，每个 owner back-pointer 最多清空一次。

如果选择 self-target-only：
- 必须在获取 handle 前从 child 的 proxy-supply 解析 phandle，并确认目标 node 与当前 reg_node 完全相同；非 self-target 一律 -EINVAL。
- 不允许依靠 DTS review 文件“碰巧都 self-target”而放任驱动接受任意 target。
- provider-level ROUND31 legacy group mapping保持兼容；同时审计它的 target-unregister 风险。若同样存在风险，必须用相同安全机制覆盖，或明确给出不扩大风险的严格限制和理由。
- binding description 必须与实际运行时约束一致。

如果选择通用 target tracking：
- 必须建立安全的 target→proxy consumer 反向关联，或提供等效机制。
- target unregister hook 必须早于 core 从 class/list 移除 target 和检查/释放 rdev。
- 需要处理同一 target 被多个 owner 引用、一个 owner 多个 consumer、deferred handle、target/owner 相同、target/owner 不同。
- 不能直接解引用 regulator core 私有对象、绕过 regulator core refcount、伪造 device 或在无锁状态保存裸 rdev 指针。
- 需要安全持有 target node/rdev identity，并在所有清理路径释放对应引用。

## 3. 必须提交的可复现测试

扩展 kernel-baseline/round61/tests/，继续编译测试真实 drivers/regulator/proxy-consumer.c，并增加本轮 target-unregister 覆盖。

至少覆盖：
1. self-target：owner unregister 时先撤销自身 proxy handle，再继续 core unregister；open_count 回到预期值。
2. cross-target（若支持）：target 先 unregister，所有引用 target 的 owner consumer 都被撤销；之后 owner unregister 不重复 disable/put。
3. cross-target（若支持）：owner 先 unregister，target 后 unregister，不发生二次清理。
4. 一个 target 被两个不同 owner 引用时，target unregister 清理两个 consumer，彼此不串票。
5. deferred target 在未注册时 owner unregister / bulk revoke，不能留下悬空列表项。
6. deferred target 后续注册并成功 retry，再分别测试 owner/target teardown。
7. target unregister 与 late_initcall_sync bulk revoke 的顺序交错。
8. 重复 unregister / 重复 bulk revoke / 重复 target cleanup 全部幂等。
9. 任何路径都无残留 enable/load vote、无重复 regulator_put、无 owner back-pointer 悬空。
10. 非 self-target 拒绝测试（若采用 self-target-only）。

Mock 必须明确模拟 regulator core 的注销顺序和 open_count 行为，不能把“调用 proxy helper 的 unregister”伪装成完整的 target unregister。另需增加针对真实 core hook 顺序的源码级断言或 KUnit/in-tree 测试证据。测试必须能从仓库脚本一键复现，输出检查总数、失败数和非零退出码。

## 4. Binding / DTS

- 保留 ROUND32 child-level proxy-supply 声明与 unevaluatedProperties: false。
- 若限制 self-target，schema description 必须明确写出“必须指向该 regulator child 自身”，并提供非 self-target negative runtime fixture/test。
- L5/L9 review DTS 继续表达两个独立 self-target：各自 qcom,proxy-consumer-enable 与 qcom,proxy-consumer-current = <100000>。
- 不添加电压、parent-supply、VPH_PWR 或 PMIC 假设。
- provider-level legacy declaration的兼容性必须有正向测试；group+child 混用必须仍被拒绝。
- 不得通过放宽 additionalProperties / unevaluatedProperties 吞掉诊断。

## 5. 构建和回归

- ROUND31 + ROUND32 的 15 patches 必须保持原样；本轮追加 patch 16+，并记录 blob SHA 与 SHA-256。
- 对完整 series 在精确 ACK disposable worktree 执行每个 patch 的 git apply --check、git apply、git diff --check。
- 新增 patch 运行 ACK scripts/checkpatch.pl --strict。
- 运行真实 dt_binding_check、dt-doc-validate、DTS fixtures 和 runtime negative gates。
- 完整 manifest-pinned Kleaf tools/bazel build //common:dby_w09 重编；不得用 ROUND32 build 结果代替本轮。
- ROUND58 config regression：33/33 必需 symbols =y；helper tests 11/11。
- 记录 Image、System.map、vmlinux、.config 的大小与 SHA-256；不得上传构建产物。
- host test harness / fixtures / scripts 必须提交入仓库；不能只在报告写数字。

## 6. 严格禁止

未经用户单独明确授权，绝不：
- 连接或操作平板；ADB、fastboot、recovery、reboot、unlock、root、flash、临时启动；
- 读取或写入任何设备分区；
- 构建/重打包 boot、DTBO image、AVB/vbmeta/footer 或关闭验证；
- 猜测 PM8150 parent supply、VPH_PWR、ARC→VRM 关系或 PMIC 电压；
- 上传/重新导出 HOS4.3 原始固件、FDT、DTBO 或设备标识；
- 改写 proxy temporary vote 为 permanent vote、system-load 或 always-on；
- 合并 1号 AI 的任务或修改其文件；
- 自动启动 ROUND34。

## 7. 交付和停止

唯一报告路径：
firmware-analysis/round33/AI2_ROUND33_TARGET_UNREGISTER_LIFECYCLE_REPORT.txt

Stage A 分支提交实际 patch、binding/DTS fixture（如有）、可复现测试源与脚本、series 更新和 PROGRESS 记录。报告必须明确：
- 采用 self-target-only 还是通用 target tracking，以及选择依据；
- target unregister 的源码顺序、锁/refcount证明；
- 所有清理路径与测试矩阵；
- 完整构建与回归结果；
- 尚存限制及是否仍有 L5/L9 end-to-end 阻塞。

只交付 ROUND33 这一份报告后立即停止。不得自动启动 ROUND34。