# ROUND114 — 1号 AI：Qualcomm KONA 临时 proxy-consumer 语义与 ACK 6.18.33 移植边界

审查日期：2026-11-25
任务归属：1号 AI（ChatGPT）独立源码审查；不是 Agent 测试任务，也不是 2号 AI 实际 patch 任务。
设备证据：HOS4.3 ROUND13 / ROUND106 / ROUND107 / ROUND111。
固定 ACK：android17-6.18.33_r00，commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a。
Vendor 对照：OnePlusOSS/android_kernel_oneplus_sm8250，commit cad09e061ef6cf689a4a1e54d27562e0f042236a。
关联任务：AI2-ROUND31（L5/L9 temporary proxy-consumer port）。

## 1. 本轮最重要的结论：L5/L9 proxy-supply 自引用是有意的 consumer lookup，不是物理 parent supply

ROUND13 记录的 HOS4.3 静态结构：
- L5 provider group：/soc/rsc@18200000/rpmh-regulator-ldoa5；child regulator-name pm8150_l5。
- L9 provider group：/soc/rsc@18200000/rpmh-regulator-ldoa9；child regulator-name pm8150_l9。
- group 上有 proxy-supply，phandle 解析回各自 group 的 child regulator。
- 对应 child 上有 qcom,proxy-consumer-enable 与 qcom,proxy-consumer-current = 100000 µA。
- L6 没有 proxy-supply / proxy-consumer，不得添加。
- ROUND111 进一步证明 L17 没有 proxy-supply；L5/L9 语义不得转移到 L17。

公开 KONA 源码解释了看似自引用的结构为什么有效：

1. KONA rpmh_regulator_probe() 中 dev = &pdev->dev，node = dev->of_node；因此 dev->of_node 是 RPMh regulator group/provider node。见 [rpmh_regulator_probe](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/rpmh-regulator.c#L1859-L1881)。
2. 每个 child 的 rpmh_vreg 单独保存 vreg->of_node；regulator_config.dev = dev（group device），regulator_config.of_node = vreg->of_node（individual child）。见 [rpmh_regulator_init_vreg](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/rpmh-regulator.c#L1806-L1823)。
3. KONA regulator_register() 在 rdev 注册完成后调用 regulator_proxy_consumer_register(dev, config->of_node)，所以 helper 的 reg_dev 是 group device，reg_node 是 child node。见 [regulator core registration](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/core.c#L4759-L4766)。
4. proxy helper 先在 child 上读取 qcom,proxy-consumer-* 属性，再执行 regulator_get(reg_dev, "proxy")。见 [proxy consumer registration](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/proxy-consumer.c#L46-L147)。
5. regulator_get() 的 OF lookup 使用 reg_dev->of_node，并读取名为 proxy-supply 的 phandle，再按目标 child node 找到已注册 regulator。见 [of_get_regulator / regulator_dev_lookup](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/core.c#L234-L257) 与 [lookup](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/core.c#L1541-L1564)。

所以，group 的 proxy-supply -> 自己 child，建立的是“由 group device 代为获取同一个 regulator 的 proxy consumer handle”这一临时请求关系。它不是该 regulator 的电气 parent，不应翻译为 regulator input-supply，也不能证明 L5/L9 的物理输入供电网络。

这条结论是由固定 KONA 源码调用链解释 ROUND13 已解析的节点关系，不是对实际电流/电压或 runtime regulator state 的观测。

## 2. KONA proxy-consumer 的注册和生命周期

源码：[drivers/regulator/proxy-consumer.c](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/proxy-consumer.c)。

### 2.1 注册顺序

- child 没有任何 proxy-consumer 属性时，helper 返回 NULL。
- 检查全局移除标志后分配 proxy 状态。
- 读取 child 的 enable/current/voltage 属性。
- 使用 provider group device 调用 regulator_get(dev, "proxy")。
- 如有 voltage，先设置电压范围。
- 如 current > 0，调用 regulator_set_load()。
- 如 enable=true，再调用 regulator_enable()。
- 成功后才将 consumer 放入全局 proxy list。
- 初始化失败路径尝试清回 load / voltage 并 regulator_put()。

对 L5/L9，现有证据确认 current=100000 µA 且 enable=true，无需臆造 voltage request。

### 2.2 两种释放入口

KONA 实现有两个释放入口：
- individual provider unregister：regulator core 在 regulator_unregister() 中调用 regulator_proxy_consumer_unregister()，在 provider rdev 从 regulator registry 移除前处理该对象。见 [KONA unregister hook](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/core.c#L4795-L4812)。
- system boot handoff：proxy-consumer helper 通过 late_initcall_sync(regulator_proxy_consumer_remove_all) 统一释放所有临时 proxy requests；设全局 proxy_consumers_removed 标志，之后不再接受新注册。见 [late_initcall_sync cleanup](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/proxy-consumer.c#L200-L222)。

KONA 的意图是 boot 早期暂时保留 PMIC request，等待普通设备驱动完成 probe 后，在 late_initcall_sync 撤销，让正常设备 consumer votes 接手。它不是永久负载约束，也不是 regulator-always-on。

## 3. 不能原样复制 KONA cleanup 顺序：ACK regulator core 语义不同

这是 AI2-ROUND31 实现必须处理的关键 ABI/行为差异。

### 3.1 KONA 4.19 行为

KONA regulator_set_load() 在设置 uA_load 后无条件调用 drms_uA_update()，没有 ACK 6.18 的 enable_count gate 和失败回滚。见 [KONA regulator_set_load](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/core.c#L3665-L3677)。

KONA regulator_disable() 使用 regulator_dev 全局 use_count；在多个用户情况下先调用 drms_uA_update()，但忽略其错误再递减 use_count；最后一个用户则走 provider disable。见 [KONA _regulator_disable](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/core.c#L2350-L2393)。

因此 KONA helper 的原始 remove() 顺序是 disable -> set_load(0) -> voltage reset，并在失败后仍继续 put/list_del/kfree。其 rc 会被后续清理操作覆盖；late_initcall_sync 的 remove_all 也不检查每个 remove 返回值。这个实现的失败语义不可直接移植到 ACK。

### 3.2 固定 ACK 6.18.33 行为

ACK core 中每个 struct regulator consumer 自己保存 enable_count 与 uA_load，不等同于 KONA 4.19 的旧式 global use_count 语义。

- _regulator_handle_consumer_disable() 先执行 regulator->enable_count--，然后在 uA_load 非零且该 handle enable_count 变为 0 时调用 drms_uA_update()；如果 DRMS 失败，函数返回错误，但不会把 enable_count 加回来。见 [ACK consumer disable](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L2879-L2895)。
- ACK regulator_set_load() 先保存旧 load 并更新新值；只有 handle 当前 enabled 且 load 值改变时才调用 drms_uA_update()；失败会将 stored load 回滚。未启用的 handle 调用 set_load 只保存请求，不触发 DRMS。见 [ACK regulator_set_load](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L4950-L4968)。

### 3.3 适配 ACK 的必要操作顺序

注册时：
1. regulator_get(proxy handle)。
2. regulator_set_load(handle, 100000) 先写入 consumer stored load。
3. regulator_enable(handle)；首次 enable 将触发该 handle 的 DRMS 更新；enable 失败时 ACK core 会回滚 enable_count，helper 必须清除此前存入的 load 并平衡 handle。
4. 只有完整成功后，才将其纳入待 late-init cleanup 的状态表。

释放时，顺序必须与 KONA 源码原样相反：
1. 若 proxy handle 仍 enabled，先调用 regulator_set_load(handle, 0)，让同步 DRMS mode transition 在 enable reference 尚未递减时完成。
2. 若 load-zero 返回错误，ACK core 会恢复原 stored load；helper 不得继续 regulator_disable，也不得假装 vote 已清除。必须保留能重试的 state/handle，并记录错误。
3. load-zero 成功后，才调用 regulator_disable(handle)。
4. disable 成功后才清除 enabled-reference 状态。disable 失败不得提前标记 ref 已释放。
5. voltage 清理（仅若该 proxy 实际设置过 voltage）不能掩盖 load/enable cleanup 的先前错误。
6. regulator_put、移出 list、free 状态前，必须明确证明不再有 outstanding enable ref / load vote，或定义受控而不会丢失 provider lifetime 的终止错误策略。

这是 ROUND90 / ROUND105 / ROUND107 / ROUND112 的 UFS regulator-core 错误顺序原则在 proxy helper 中的直接应用。必须分开维护 load vote 与 enable ref；单一 boolean 不足以表达 ACK 的失败状态。

注意：ROUND106 证明 L5 未设置 qcom,always-wait-for-ack，故 L5 disable callback 按 ACK RPMh driver 是 async write；这不改变 load-zero 所触发的 DRMS mode request 可能同步等待 ACK 的事实。L9 的 ACK flag 应按对应 child 的本地证据单独核对，不要把 L5 属性结论自动复制给 L9。

## 4. ACK 6.18.33 目前没有该 helper 的现成接线

固定 ACK 检查：
- drivers/regulator/Kconfig 没有 REGULATOR_PROXY_CONSUMER 项。
- drivers/regulator/Makefile 没有 proxy-consumer.o。
- regulator_dev 没有 proxy_consumer pointer。
- regulator_register() 在 device_add() / rdev_init_debugfs() 后继续 coupling/supply resolve，没有 KONA 的 proxy register hook。
- regulator_unregister() 没有 individual proxy unregister hook。

因此这是需要真实 ACK source integration 的功能移植，不是添加一条 DTS 属性就能生效。AI2-ROUND31 的源码、Kconfig/Makefile、binding、fixtures 和 cleanup state machine 均需要实际实现和完整构建验证。

## 5. 必须由 2号 AI 决定和验证的 unresolved engineering details

本报告不代写 patch；以下必须由 2号 AI 在其 Stage A 实现中解决，并用真实测试证明：

1. **注册失败策略：** KONA core 目前保存 helper 返回值但没有将 proxy helper 错误作为 regulator_register() 失败；ACK port 必须明确处理 NULL / ERR_PTR、probe defer、OOM、load failure、enable failure，不能把 ERR_PTR 当可用对象。
2. **cleanup failure 与 handle lifetime：** regulator_unregister() 是 void，provider devres teardown不能无限等待；如果 load-zero/disable 请求失败，helper 如何避免释放尚持有 outstanding vote/ref 的 handle、同时避免 provider rdev 被释放后留下悬空指针？若无可靠策略，必须将真实阻塞报告清楚，不能伪造“完全平衡”。
3. **global list/lock ordering：** KONA helper 在全局 proxy list mutex 持有期间调用 regulator_get/set_load/enable/disable/put。ACK port 必须做 lockdep/调用图审查，避免 proxy-list lock、regulator ww_mutex、regulator_list_mutex、deferred probe 与 provider unregister 的锁顺序死锁；不能只复制旧锁结构。
4. **late_initcall_sync：** 必须在全部目标 PMIC regulator 子节点已注册并完成常规 consumer probe 后撤销临时票据；设置 removed state 后，迟到的注册请求必须有明确行为。
5. **状态模型：** per-proxy 记录 stored load、enable ref、是否设置 voltage、late-init cleanup 状态以及 individual unregister 状态；必须防止 late-init 与 individual unregister 并发 double-remove。
6. **真实 HOS属性：** 只为 ROUND13 证据覆盖的 PM8150 L5/L9 处理，不能对每个 RPMh regulator 泛化 100mA；L6、L17、S4、S8 不得添加同类 proxy。
7. **测试：** registration positive/absent/malformed fixtures；load-zero failure；enable failure rollback；disable error；late-init与unregister race；重复清理；probe defer；完整 manifest-pinned //common:dby_w09 Image build；ROUND58 33/33 config + 11/11 tests regression。

## 6. Task ownership clarification

AI2-ROUND31 is an actual **2号 AI kernel implementation task**. The user's local Agent is a separate read-only/test/build execution tool and is not 2号 AI. The currently published ROUND31 taskbook says both “2号 AI 专属” and “executor is user's local Agent”; those statements conflict with the user's established role boundary.

1号 AI has not edited the AI2 taskbook or Stage A branch. Before any further execution, the task owner must correct the executor assignment so actual source coding belongs to 2号 AI; only a specifically scoped local build/test or device-file evidence operation may be assigned to the test Agent. Do not let the task ownership label conceal a transfer of kernel implementation to the Agent.

## 7. Evidence and non-claims

Source blobs examined:
- KONA proxy-consumer.c: 6ae1c7a0381537a6556a45d1cf89c20f285d6d80
- KONA regulator core: 9fc11af942334b43d4c42bca34144bd9e55a5ead
- KONA rpmh-regulator.c: e6667c59818621a99bc53fc560e353d8c25e14e5
- KONA regulator Kconfig: 5e96575e685916bb908e8ab1429f59dad68ecfc3
- KONA regulator Makefile: 62f3005dcbe0fe839a21b460b516eb4050318da0
- ACK regulator core: 39d317ad73a33c4aa27e179cc436d8bf4daf5bcc
- ACK regulator driver.h: 3f63da8c4b141258ee55f6da9c35e23561b79011
- ACK regulator Kconfig: d84f3d054c59d86d91d859808aa73a3b609d16d0
- ACK regulator Makefile: b3101376029d71b0e8e2133dd28aa6660815fee0

This round is source-level review only. No source patch, Stage A branch, protected DTS branch, PR, firmware, build artifact, boot image, or device was changed or tested. This does not close Phase E/F/G and does not establish device bootability.


## 3.4 额外确认：KONA 与 ACK 对“未启用 consumer 的 load vote”计入 DRMS 的规则也不同

这不仅是 set_load 是否 rollback 的差异，还会影响 late-init handoff 时究竟有哪些负载被用于选择 HPM/LPM：

- KONA drms_uA_update() 直接遍历 consumer_list，把每个 sibling->uA_load 全部加总，不检查该 handle 是否 enabled。见 [KONA DRMS aggregation](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/core.c#L750-L828)。
- 固定 ACK drms_uA_update() 仅当 sibling->enable_count 非零时才把 sibling->uA_load 加入 current_uA。见 [ACK DRMS aggregation](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L969-L1005)。
- 因此 KONA regulator_set_load() 对尚未 enable 的 consumer 也会立即重新计算/应用 DRMS；ACK regulator_set_load() 对未 enabled handle 仅存储 vote，不立即执行 DRMS。ACK 需要等该 handle 后续 enable 才把 load 纳入 aggregate。

这对 UFS/QMP 尤其重要：ROUND107 已确认 QMP 的 regulator bulk-get 会在 probe 期间设定 init_load_uA，即 load vote 可早于 power-on / enable 存在。不能简单假设“probe 已经执行”就等于它的 load 在 ACK DRMS aggregate 中有效。

在 KONA 旧实现里，已 probe 但暂未 enabled 的 QMP/UFS handles 的 load 也会参与 DRMS；在 ACK 里则只有 enable_count > 0 的 handles 参与。ROUND108 还记录 UFS async scan 的异步生命周期，不能用“late_initcall_sync 已执行”推断 async scan 及 QMP/UFS 所有 consumer 已进入正确电源状态。

因此 AI2-ROUND31 必须验证 late_initcall_sync 释放 100mA 临时 proxy vote 时，实际接手的 UFS/QMP consumer 是否已经 enable，或者是否有其他明确且有证据的 active vote 保持所需模式。不能因为 UFS regulator handles 已经 bulk-get / init_load 已保存，就直接声称 ACK aggregate 会持续计算这些电流。若没有实际 overlap 证据，应保留为 HOS→ACK DRMS accounting / boot handoff 差异，不得伪造 full semantic equivalence。
