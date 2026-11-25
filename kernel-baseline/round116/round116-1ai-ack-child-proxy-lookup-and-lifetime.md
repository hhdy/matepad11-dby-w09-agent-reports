# ROUND116 — 1号 AI：ACK child-scoped proxy lookup API 与 unregister lifetime 限制

审查日期：2026-11-25
任务归属：1号 AI（ChatGPT）固定 ACK 源码审查；不是 Agent 任务，也不是 2号 AI 代码实现。
固定 ACK：android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
关联：ROUND114、ROUND115、AI2-ROUND31

## 1. ROUND115 的 lookup 方案进一步收敛：优先考虑 of_regulator_get(group_dev, child_node, "proxy")

固定 ACK 已提供一个能把 consumer device 与 OF 查找 node 分开的接口：

- include/linux/regulator/consumer.h 声明 of_regulator_get(struct device *dev, struct device_node *node, const char *id)。
- drivers/regulator/of_regulator.c 的 _of_regulator_get(dev,node,id) 将 node 直接传给 of_regulator_dev_lookup(dev,node,id)。
- of_get_regulator(dev,node,supply) 对传入的 node 执行 of_parse_phandle(node, "proxy-supply", 0)；它不必使用 dev->of_node 作为 lookup scope。
- of_find_regulator_by_node() 使用 class_find_device_by_of_node()，按 phandle 目标 node 找已经注册的 regulator class device。
- regulator_register() 在 device_add(&rdev->dev) 后才返回；qcom-rpmh-regulator 的 devm_regulator_register() 返回时，该 child rdev class device 已经可供 class_find_device_by_of_node() 查找。

因此一个准确的调用形态是：

- dev 参数继续使用共同 PMIC provider platform device（用于日志与 regulator consumer 对象的设备上下文）；
- node 参数使用当前 regulator child 的 rdev->dev.of_node；
- id 使用 proxy。

这样即使 L5 和 L9 共用同一个 PMIC parent device，两次 lookup 也分别从 L5 child / L9 child 的 proxy-supply phandle 解析，不再都读取共同 regulators-0 的 group-level property。

相关源码：
- [consumer.h of_regulator_get API](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/linux/regulator/consumer.h#L679-L692)
- [of_regulator_get implementation](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/of_regulator.c#L615-L719)
- [regulator child OF-node assignment and device_add](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L5855-L6008)
- [QCOM RPMh per-child registration](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c#L414-L495)

### 1.1 为什么不首选 regulator_get(&rdev->dev, "proxy")

直接以 rdev->dev 作为 consumer device 也会通过 dev_of_node(rdev->dev) 读到 child node，因此 lookup scope 本身是正确的。但 regulator core 的 _regulator_get_common() 会：
- 调用 link_and_create_debugfs()，以 rdev->dev 作为 consumer device，再尝试在同一 rdev kobject 下建立指向自身的 sysfs link；
- 调用 device_link_add(dev, &rdev->dev, DL_FLAG_STATELESS)，而此时 consumer 与 supplier 是同一个 device；固定 ACK drivers/base/core.c 明确将 consumer == supplier 的 device_link_add 请求返回 NULL。该 link 失败不使 regulator_get 本身失败，但会产生无意义的 self-link 路径。

所以对这个场景，of_regulator_get(group_dev, child_node, "proxy") 的参数职责更明确；它避免把 rdev 本身同时当成 device consumer 和 regulator supplier。具体 device-link 是否创建仍需在实际实现中检查，但 regulator_get_common 对 device link 返回 NULL 的处理是非致命的。

## 2. 必须验证 lookup 结果属于当前 child，不能只验证 phandle 存在

推荐在 proxy helper 内建立严格不变量：
- L5 child proxy-supply 必须解析到 L5 child；
- L9 child proxy-supply 必须解析到 L9 child；
- L5 handle 与 L9 handle 必须指向不同 rdev；
- L6/L17 没有 proxy 请求，不得创建 proxy handle；
- 若 phandle node 与当前 rdev->dev.of_node 不一致、lookup 返回 -EPROBE_DEFER / -ENODEV / ERR_PTR，必须明确失败，不得降级到 group-level lookup、dummy regulator 或其他 rail。

注意 regulator 是 opaque handle：在普通消费者代码里不能直接读 struct regulator 内部 rdev 指针。若实现必须证明 handle->rdev == 当前 rdev，应由 regulator core 内部 helper 做比较，或先通过同一 node 的 phandle identity 检查并让 core lookup 保证按该 OF node 返回 regulator。不要为了比较而绕过 regulator core 引用计数/锁语义。

## 3. 当前 ACK regulator_unregister() 不能被清理错误 veto

固定 ACK drivers/regulator/core.c 的 regulator_unregister()：
- 如果 rdev 有 parent supply，先处理其 use_count；
- flush disable work；
- 锁定 regulator_list_mutex；
- WARN_ON(rdev->open_count)；
- 无论 open_count 是否为 0，继续移除 coupling/supply/list、释放 GPIO 并 device_unregister(&rdev->dev)。

源码：[ACK regulator_unregister](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L6040-L6060)。

这意味着：
- proxy cleanup 若 load-zero/disable 失败而仍保留 regulator handle，随后 provider unregister 会报 open_count warning 但仍继续 unregister；
- outstanding regulator handle 持有的 device ref 可能延迟 rdev device memory release，但不能因此假设其 regulator provider data / parent devres 仍然有效；
- regulator_put() 明确要求所有 enable references 已先 disable；若 handle 仍 enabled，core 会 WARN_ON(regulator->enable_count)；
- 把 proxy cleanup 包成一个 devm action 只保证它按 devres 逆序先于 regulator unregister 执行，**不能**让 action 返回错误阻止后续 devres 的 regulator unregister。

devres 释放顺序是反向顺序：devres_release_all() 移动 resource entries 后，release_nodes() 使用 list_for_each_entry_safe_reverse() 执行 release callback。源码：[devres release order](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/base/devres.c#L243-L250) 与 [release_nodes](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/base/devres.c#L420-L537)。

所以，如果在 devm_regulator_register() 成功后再注册 proxy cleanup devres action，正常情况下它会先于该 regulator 的 devres unregister action 执行；但如果 cleanup 返回错误，devres 仍会继续执行后续 regulator unregister。不能把“action 顺序正确”误认为“失败可阻止 provider teardown”。

## 4. 对 2号 AI 实现的新增硬要求

AI2-ROUND31 必须回答并测试以下问题：

1. 明确采用 per-child OF lookup（优先评估 of_regulator_get(group_dev, child_node, "proxy")），不能采用共享 group_dev 上重复 regulator_get(group_dev, "proxy")。
2. 注册只发生在 rdev 已 device_add、可由 class_find_device_by_of_node() 查到之后。
3. 验证 self phandle 的 node identity 与 L5/L9 rdev identity；不能仅通过查到任意 regulator 就认为成功。
4. 分别维护 L5/L9 proxy handle 的 stored-load、enable reference、释放状态。
5. late_initcall_sync 的全局移除只释放 consumer vote/handle；如果 devres action 仍会引用状态对象，必须保留对象到 devres cleanup，避免 global cleanup free 与 devres double-free/UAF。
6. Provider unregister 之前必须处理 proxy handle；若 load-zero/disable 失败，必须给出一个不会遗留 open_count、enable_count、悬空 provider data 或 UAF 的策略。仅记录错误、返回负值或依赖 devres action 无法阻止 regulator_unregister。
7. 所有 cleanup 路径要防止 late-init remove 与 individual provider unregister 并发重复操作。
8. 正常 release 顺序仍按 ROUND114：load-zero while enabled -> disable -> put；load-zero 错误不得继续 disable/put。

如果第 6 项在固定 ACK core 的 void unregister / devres teardown 约束下无法安全完成，2号 AI 应报告明确的阻塞，而不是提交一个“正常启动可用、异常 cleanup 不安全”的半成品。

## 5. 范围与非声明

本轮只读检查固定 ACK consumer API、of_regulator lookup、regulator core unregister 和 devres release order。没有修改 AI2 分支、DTS draft、保护分支、固件、Image 或设备；没有执行 build/boot。Round116 是设计约束和风险澄清，不是 proxy consumer 已实现的证据。
