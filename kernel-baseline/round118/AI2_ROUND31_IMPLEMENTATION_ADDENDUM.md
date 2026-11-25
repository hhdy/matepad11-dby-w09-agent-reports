# 1号 AI 发布给 2号 AI 的补充任务书 — AI2-ROUND31-ADDENDUM

**任务归属：2号 AI（实际内核源码实现）。**
**发布方：1号 AI（ChatGPT），负责独立源码审查与验收。**
**本地 Agent：不是 2号 AI，不得编写、修改、生成或提交任何内核驱动 / regulator core / DTS / binding / source patch。Agent 只可在 2号 AI 完成源代码后，按独立任务执行只读检查、构建或测试。**
**本补充纠正原 ROUND31 任务书中“2号 AI 专属”却将“执行者”写为“用户本地 Agent”的角色冲突。原任务书保留为历史记录，本补充中的角色定义优先。**

## 1. 唯一目标

继续原 AI2-ROUND31：将 HOS4.3 PM8150 L5/L9 100000µA temporary proxy-consumer 生命周期适配至固定 ACK Stage A。

目标 branch：`ai-parallel/stagea-port-until-boot`
固定 ACK：`android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
KONA 参照：`OnePlusOSS/android_kernel_oneplus_sm8250` / `cad09e061ef6cf689a4a1e54d27562e0f042236a`

不处理 ARC、物理 parent supply、永久 system-load、always-on 或 UFS/DTS 其他供电改造。

## 2. 必须采用的设备树/lookup 架构约束

Round115/116 已证明 vendor 与 ACK provider device granularity 不同：

- KONA 4.19 为 L5、L9 各自创建独立 regulator group platform device，所以 group-level `proxy-supply` + `regulator_get(group_dev, "proxy")` 可分别定位两条 rail。
- ACK 6.18 每个 PMIC 创建一个 provider device，L5/L6/L9/L17 是同一个 PM8150 group device 下的多个 regulator children。照搬 KONA helper 的 `regulator_get(group_dev, "proxy")` 会让 L5/L9 两次读取同一 group-level property，可能把两笔票据投到同一条 rail。
- ACK 已有显式 child-node lookup API：`of_regulator_get(group_dev, child_node, "proxy")`。请优先评估并用它把 OF lookup scope 固定到当前 regulator child。等价方案必须同样证明 L5 与 L9 不会串线。
- 候选 Stage A DTS 表达为：L5 child 的 `proxy-supply` 自引用 L5，L9 child 的 `proxy-supply` 自引用 L9；两条属性不得共用 PMIC group 根节点。它是 ACK layout adaptation，不是修改 HOS 原始固件 FDT 的事实。
- ACK `qcom,rpmh-regulator.yaml` 对每个 regulator child 使用 `$ref: regulator.yaml#` 和 `unevaluatedProperties: false`；通用 regulator schema 接受 child `*-supply` 模式。新增 `qcom,proxy-consumer-enable` / `qcom,proxy-consumer-current` 时，必须在 RPMh child schema 明确声明类型、描述和依赖，不得放宽 group 根节点的 additional/unevaluated properties。
- 必须验证 handle 的 regulator target identity：L5 handle 指向 L5，L9 handle 指向 L9，且彼此不同。L6/L17 没有 proxy 属性，不得注册 proxy。

关键 1AI 报告：
- [ROUND115 — ACK per-PMIC proxy scope](./round115/round115-1ai-ack-per-pmic-proxy-scope-review.md)
- [ROUND116 — child lookup and unregister lifetime](./round116/round116-1ai-ack-child-proxy-lookup-and-lifetime.md)

## 3. 必须遵守 ACK 6.18 regulator 语义

- 设置临时票据：为目标 child 获取独立 handle；设置 100000µA stored load；随后 enable。错误时分别回滚 load 与 enable reference。
- 清理顺序与 KONA 旧 helper 不同：proxy 仍 enabled 时先 `regulator_set_load(handle, 0)`；失败则停止，不得继续 disable 或 put；load-zero 成功后才 disable；disable 成功后才清除 retained enabled state。
- ACK DRMS aggregate 只统计 enabled consumer handles；仅 bulk-get/init_load 不算 active vote。
- Round117 已跟踪成功正常 probe 的 UFS/QMP 顺序：UFS HBA init 同步启用 generic VCC/VCCQ；HCE PRE_CHANGE 调用 QMP PHY power-on；QMP power-on 调用 regulator_bulk_enable；之后才 schedule async SCSI scan。因此默认同步成功 probe 路径下，late-init proxy cleanup 前 QMP L5/L9 handles 已 enabled。SM8250 QMP load 配置为 L5 89.9mA、L9 18.8mA。若显式 driver_async_probe cmdline 改变顺序，必须按实际条件限定结论。
- [ROUND114 — KONA vs ACK lifecycle](./round114/round114-1ai-kona-proxy-consumer-ack-compat-review.md)
- [ROUND117 — UFS/QMP vote handoff order](./round117/round117-1ai-ufs-qmp-proxy-handoff-order.md)

## 4. 高风险生命周期阻塞：必须解决，不可只写日志

ACK `regulator_unregister()` 是 void；即使 `rdev->open_count` 非零也会 WARN 后继续注销。devres reverse order 可让后来注册的 proxy cleanup action 先运行，但 cleanup action 返回错误不能 veto 后续 regulator unregister。

所以，必须给出并验证：
1. late_initcall_sync 全局清理与 individual provider unregister 并发时，只执行一次 release；
2. global cleanup 不得 free 一个仍被 devres action 引用的 proxy state object；
3. provider unregister 前必须处理 handle、load vote、enable reference；
4. load-zero/disable 失败时，不得 put 一个仍有 enable_count 的 handle，不得 free 持有该 handle 的状态对象，不得假设 devres action 返回错误会阻止 rdev unregister；
5. 不得因此留下 use-after-free、悬空 provider data、双重释放、enable_count 泄漏或未经说明的 active request；
6. 若固定 ACK 的 void unregister/devres contract 下无法安全实现某个失败路径，必须给出可复现阻塞并停止提交半成品，不得宣称“完整平衡”。

## 5. 最低验收标准

代码由 2号 AI 实际完成并提交：
- helper / core hook / QCOM driver integration；
- child-specific DTS fields；
- Kconfig / Makefile；
- binding；
- positive/negative fixtures 和可执行测试；
- patch-series 更新、完整源构建日志。

必须测试：
- no-proxy child 不改变行为；
- L5/L9 正向注册与 target identity；
- L5/L9 互不串线；
- L6/L17 没有 handle；
- 缺失/错误 self phandle、非法 current、错误 flag 类型；
- load-zero failure（不得 disable）；
- enable failure rollback；
- disable failure state；
- late_initcall_sync 与 provider unregister race；
- 重复清理与 probe defer；
- Kconfig/config validator 33/33 和 ROUND58 helper tests 11/11；
- manifest-pinned Kleaf 完整 `//common:dby_w09` Image rebuild。ROUND61/ROUND30 旧 build 不能代表新 patch 已编译。

本地 Agent 只可在上述代码已提交后执行指定测试/构建，并报告结果；不得写代码修复测试失败。若测试失败，交回 2号 AI 改代码，再由 Agent 重跑。

## 6. 输出

2号 AI 在目标 branch 提交实现与 patch-series；报告仍写到：
`firmware-analysis/round31/AI2_ROUND31_STAGEA_PROXY_CONSUMER_IMPLEMENTATION_REPORT.txt`
报告记录 source commit、patch SHA、fixtures、每项测试、完整 Image build SHA/size、剩余 blocker。

不要启动 ROUND32；不要连接设备或打包/刷写 boot/DTBO/AVB。Stage A 真机启动门槛未关闭前，不得开始 DerpFest Stage B。
