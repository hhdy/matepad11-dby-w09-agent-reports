# ROUND119 — 1号 AI：child self proxy-supply 与固定 ACK fw_devlink cycle handling

审查日期：2026-11-25
任务归属：1号 AI（ChatGPT）固定 ACK driver-core / OF supplier-link 源码审查；不是 Agent 任务，也不是 2号 AI patch 实现。
固定 ACK：android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
关联：ROUND115、ROUND116、AI2-ROUND31

## 1. 本轮结论

ROUND115/116 提出的 child-local self proxy-supply + of_regulator_get(group_dev, child_node, "proxy") 在固定 ACK 的 fw_devlink 中会形成一个 child fwnode 的 self-reference edge；但 ACK driver core 已显式检测 dependency cycle，并将 cycle link relax 为 permissive，随后在 consumer device 与 supplier device 实为同一个 regulator class device 时跳过 device_link_add。

所以：
- self proxy-supply 会被 OF 的通用 "*-supply" supplier parser 看见；
- fw_devlink 会识别出 fwnode self-cycle，并通过 FWLINK_FLAG_CYCLE / permissive cycle handling 处理；
- supplier 最终解析为同一个 rdev device 时，con == sup_dev，core 不会创建 self device link；
- 该代码路径不将 self-cycle 作为 probe defer 的 fatal supplier dependency。
- 但实际 build/runtime 仍应检查 dmesg 是否出现预期的 cycle-relaxed info，而不能只凭源码声称启动日志已验证。

这进一步支持 child-scoped proxy lookup 的可行性，但不能替代 binding/driver tests。

## 2. 源码调用链

### 2.1 OF generic supply parser 识别 child proxy-supply

固定 ACK drivers/of/property.c 的 supplier binding 表含有：
- DEFINE_SUFFIX_PROP(regulators, "-supply", NULL)
- of_supplier_bindings 将 regulators parser 纳入 OF supplier parsing。

因此无论 property 是 vdd-supply、vcc-supply 还是 proxy-supply，只要它位于被 fw_devlink 解析的 OF node 上，都会被 suffix parser 识别为 supplier phandle。Child self proxy-supply 不是被 fw_devlink 忽略的未知属性。

源码：[OF supplier binding suffix parser](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/of/property.c#L1404-L1414)、[OF supplier bindings table](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/of/property.c#L1524-L1545)。

### 2.2 ACK driver core 显式放宽 self dependency cycle

固定 ACK drivers/base/core.c：
1. fw_devlink_create_devlink() 先调用 __fw_devlink_relax_cycles(link->consumer, sup_handle)。
2. __fw_devlink_relax_cycles() 的终止条件明确判断 sup_handle == con_handle，并返回 cycle=true。
3. 调用方将 fwnode link 标记 FWLINK_FLAG_CYCLE，打印 "Fixed dependency cycle(s)" 信息。
4. fw_devlink_get_flags() 对 FWLINK_FLAG_CYCLE 返回 FW_DEVLINK_FLAGS_PERMISSIVE | DL_FLAG_CYCLE。
5. 解析 supplier device 后，如果 con == sup_dev，则跳过 device_link_add，不建立 device-to-itself link。
6. own fwnode link 在正常成功处理后移除。

因此 child node 指向自己的 proxy-supply 会走到显式 cycle-relaxation 路径，而不是创建一个阻止自己 probe 的 device link。

源码：
- [cycle detection and self-node termination](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/base/core.c#L1989-L2014)
- [cycle relaxation and permissive flags](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/base/core.c#L1706-L1712)
- [cycle marking, supplier lookup and con==sup_dev check](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/base/core.c#L2134-L2179)

## 3. 对 ROUND116 推荐 lookup 的影响

- child proxy-supply self-reference 与 of_regulator_get(group_dev, child_node, "proxy") 的显式 lookup 是两条不同的路径：fw_devlink 建立/处理设备依赖图；of_regulator_get 则在 regulator core 中解析当前 child node 的 phandle，按目标 OF node 找到已经注册的 regulator class device。
- 为避免把 parent PMIC platform device 当成 regulator child 自身，可继续优先使用 of_regulator_get(group_dev, child_node, "proxy")。
- regulator core consumer handle 关联的 device link 由 group provider device 指向其 child regulator class device；这与 child node 本身的 fw_devlink self-cycle 处理不同。
- fw_devlink cycle relaxation 是框架提供的兼容处理，不应由新 driver 私自绕过或关闭全局 fw_devlink。
- 正向 fixture 和构建日志应核对 self phandle 解析准确、L5/L9 target 不串线；runtime 日志应确认没有 regulator probe deferred 或 device link failure。出现预期 "Fixed dependency cycle(s)" 仅表示框架放宽 cycle，不表示 rail request 已成功。

## 4. 对 2号 AI 的要求

1. 保留 ROUND115/116 的 child-specific representation 候选，但要在 schema/build fixture 中真实验证。
2. 实际源实现采用显式 child-node lookup 或经过证明的等价方式；不得使用共享 group_dev 的重复 regulator_get("proxy")。
3. 使用正向 L5/L9 fixtures 验证各自 child phandle；负向 fixture 验证错指另一条 rail 时直接失败。
4. 完整 Image build 后检查 fw_devlink / regulator probe log；若有 fatal dependency cycle、deferred probe 未解除或 device link error，先修正，不得以源码“理论上会 relax”代替实测。
5. 不要关闭 fw_devlink 或修改系统全局 link policy来规避该单点 self-reference。
6. Local Agent 仍只允许执行代码完成后的测试/构建，不是本轮内核代码作者。

## 5. 范围与非声明

本轮只读检查 fixed ACK OF supplier parsing 与 driver-core fw_devlink cycle handling。没有修改 AI2 branch、DTS draft、protected DTS branch、firmware、Image 或设备；没有运行 dt-schema、Kleaf build 或 device boot。该报告证明了源码控制流存在 cycle-relaxation，不证明目标板 runtime 采用该 child self-supply 结构或已正常启动。
