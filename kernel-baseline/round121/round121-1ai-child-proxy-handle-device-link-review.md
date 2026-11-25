# ROUND121 — 1号 AI：ACK child-scoped of_regulator_get 的 parent-to-child device-link 行为

**Owner:** 1号 AI（ChatGPT）
**Type:** 固定 ACK 6.18.33 source-only review
**Pinned ACK:** 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
**Purpose:** 为 AI2-ROUND32 的 child-scoped self proxy lookup 补全 regulator consumer handle 与 driver-core device-link 的边界。
**No changes:** 本轮未修改 AI2 分支、DTS、binding、固件或内核源树。

## 1. 结论

建议的 lookup 形态：

    proxy = of_regulator_get(group_dev, regulator_child_node, "proxy");

会把两个不同职责分开：

- group_dev：consumer handle 的 device 上下文、日志/sysfs/debugfs 命名上下文；也是 PMIC provider platform device。
- regulator_child_node：OF supply lookup 的明确 node；of_get_regulator() 会从这个 node 读取 proxy-supply phandle，而不是从 group device 的 dev->of_node 读取。
- phandle 目标：of_find_regulator_by_node() 按目标 regulator 的 OF node 在 regulator class 中找出已注册的 rdev，并通过 class device refcount 保持其 device 对象存活。

**关键新增事实：** _regulator_get_common() 仍会尝试调用 device_link_add(group_dev, &target_rdev->dev, DL_FLAG_STATELESS)。由于 target rdev 的 device 是 group_dev 的子设备，ACK 的 device_is_dependent(group_dev, target_rdev_dev) 会由 ancestor 检查判定为 true，device_link_add() 会返回 NULL，拒绝 parent-consumer → child-supplier 的反向依赖。但 _regulator_get_common() 只在返回非 NULL link 时设置 regulator->device_link = true；它不会因该 link 为空而失败，仍然把已获得的 regulator handle 返回给调用者。

因此：
- child-scoped lookup 本身仍可用于创建 proxy regulator handle；
- 不应把 device-link 返回 NULL 当作 regulator lookup 失败；
- 不应伪造 device、改变 parent 关系或强制建立 parent-to-child 依赖；
- regulator_put() 只在 regulator->device_link 为 true 时删除 device link；本场景 link 未建立，不会删除不存在的 link；
- 这不改变 regulator handle/refcount、load、enable 或 unregister 的要求。

## 2. 精确调用链

1. of_regulator_get(group_dev, child_node, "proxy") → _of_regulator_get()。
2. of_regulator_dev_lookup(group_dev, child_node, "proxy") 将显式 child node 传入 of_get_regulator()。
3. of_get_regulator() 生成 proxy-supply 并调用 of_parse_phandle(child_node, ... )。
4. of_find_regulator_by_node(target_node) 调用 class_find_device_by_of_node()；找不到已注册的目标 regulator 时返回 -EPROBE_DEFER，而不是改投到别的 rail。
5. _regulator_get_common() 使用查到的 rdev 建立 consumer handle，并调用 link_and_create_debugfs()。
6. 接着它尝试 device_link_add(group_dev, &rdev->dev, DL_FLAG_STATELESS)。rdev->dev.parent = config->dev 已在 regulator registration 中设置，因此目标 child regulator device 是 group_dev 的后代；device_is_ancestor(group_dev, rdev->dev) 为 true，device_is_dependent() 返回 true，device-link add 被拒绝。
7. _regulator_get_common() 对 NULL link 不返回错误；handle 正常返回。其 device_link 标志保持 false。

## 3. 源码锚点

- of_regulator_get() 与显式 node lookup：
  [drivers/regulator/of_regulator.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/of_regulator.c#L615-L719)
- regulator registration 给 rdev 设置父设备并 device_add()：
  [drivers/regulator/core.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L5890-L6005)
- _regulator_get_common() 在 NULL device link 情况下继续返回 handle：
  [drivers/regulator/core.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L2190-L2330)
- device_link_add() 的 parent/child dependency rejection：
  [drivers/base/core.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/base/core.c#L310-L390)
- device_is_dependent() 明确包含 ancestor 检查：
  [drivers/base/core.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/base/core.c#L200-L250)
- fw_devlink 对 child self-phandle 的 cycle relaxation：
  [drivers/base/core.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/base/core.c#L1989-L2014) 与 [cycle-link creation](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/base/core.c#L2134-L2179)

## 4. 给 AI2-ROUND32 的实现约束

1. 可以继续采用 of_regulator_get(group_dev, child_node, "proxy")；child-node lookup 的 API 语义明确。
2. 预期 device-link 不创建是 ACK device hierarchy 的正常结果；不得把 NULL link 变成 fatal lookup error，也不得更改全局 device-link policy。
3. 仍需验证 L5 child 的 phandle 只解析到 L5、L9 只解析到 L9；两条 handle 独立，L6/L17 不创建 proxy handle。
4. -EPROBE_DEFER 必须保持真实错误并完整 unwind；不能降级到 dummy regulator、group fallback 或另一 rail。
5. 不能把 device 对象 refcount 与 provider driver-data 生命周期混为一谈。provider unregister 前必须释放该 rdev 的 proxy handle；parent-to-child 无 device-link 不会替代这一清理。
6. ROUND118 的清理错误要求仍然有效：先 load-zero while enabled，再 disable；load-zero 失败不得 disable/put；真正 disable 失败时不得 free/put 一个仍有 enable reference 的 handle，也不能假设 devres action 返回错误会阻止 void regulator_unregister()。

## 5. 状态与边界

- Explicit child-node OF lookup path: SOURCE-CONFIRMED.
- Parent-to-child device-link rejection: SOURCE-CONFIRMED.
- NULL link is non-fatal in regulator handle creation: SOURCE-CONFIRMED.
- fw_devlink child self-cycle is relaxed by fixed ACK core: SOURCE-CONFIRMED.
- Runtime dmesg, binding validation, two-child fixtures, full Image build, device boot: NOT RUN by this review.
- No source patch or DTS was modified.

ROUND121 is an additional implementation constraint for AI2-ROUND32, not evidence that L5/L9 child-scoped proxy support has been implemented.
