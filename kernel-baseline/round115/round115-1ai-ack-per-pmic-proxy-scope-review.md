# ROUND115 — 1号 AI：ACK per-PMIC regulator grouping 对 KONA proxy-supply 节点作用域的影响

审查日期：2026-11-25
任务归属：1号 AI（ChatGPT）独立源码/设备树架构审查；不是 Agent 任务，也不是 2号 AI patch 实现。
固定 ACK：android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
Vendor 语义对照：OnePlusOSS/android_kernel_oneplus_sm8250 @ cad09e061ef6cf689a4a1e54d27562e0f042236a
Stage A DTS：main/dts/dby-w09-ack18-board.dts.draft，blob 3c35a806a2b672c60661fb293687084e98c7455c
关联：ROUND113、ROUND114、AI2-ROUND31

## 1. 新发现：不能把 KONA 的 group-level proxy-supply + regulator_get(group_dev, "proxy") 原样移到 ACK

这是 Round31 设计中的关键设备树节点作用域差异。

### 1.1 KONA vendor 4.19 的布局

KONA vendor DTS 为每个 PMIC5 LDO 构造独立 provider platform-device node，例如：
- /rpmh-regulator-ldoa5：一个 provider group，子节点有 pm8150_l5、pm8150_l5_ao、pm8150_l5_so；group 级 proxy-supply 指向 pm8150_l5；仅 pm8150_l5 child 有 qcom,proxy-consumer-enable/current=100000。
- /rpmh-regulator-ldoa9：另一个独立 provider group，proxy-supply 指向 pm8150_l9；仅该 child 有 enable/current=100000。

KONA 的 rpmh regulator driver 为该 LDO group 创建独立 platform device；proxy helper 收到该 group device 作为 reg_dev，并用 regulator_get(reg_dev, "proxy")。因此 L5/L9 各自的父 group 都能拥有不同的 proxy-supply 属性。

源码：[KONA DTS L5/L9](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/arch/arm64/boot/dts/vendor/qcom/kona-regulators.dtsi#L186-L282)，[KONA RPMh regulator child registration](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/rpmh-regulator.c#L1806-L1823)。

### 1.2 固定 ACK 6.18 的布局不同

ACK qcom-rpmh-regulator.c 每个 PMIC 创建一个 platform device，然后在同一个 device 中遍历所有 regulator child：
- rpmh_regulator_probe() 将 dev = &pdev->dev，并遍历 dev->of_node 下全部 available child；
- 每个 child 调用 rpmh_regulator_init_vreg(vreg, dev, node, ...)；
- reg_config.dev = dev（同一个 PMIC group device）；
- reg_config.of_node = node（不同 child）；
- 每个 child 都调用 devm_regulator_register(dev, ...)。

源码：[ACK rpmh_regulator_probe / child loop](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c#L1575-L1604)，[ACK per-child regulator registration](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c#L414-L495)。

当前 DBY-W09 Stage A DTS 正是这种 ACK 结构：同一个 regulators-0 / PM8150 provider group 同时容纳 ldo5、ldo6、ldo9、ldo17 等不同 regulator child。

### 1.3 未改动的 KONA helper 会发生错误映射

若在 ACK 中沿用 KONA 原接口，把 reg_dev 传成共同的 PMIC group device，然后对 L5 与 L9 都调用 regulator_get(reg_dev, "proxy")：

- 两次 lookup 都读取同一个 regulators-0 的 proxy-supply 属性；
- 一个 group node 只能有一个 proxy-supply 属性值；
- 因而不能同时分别指向 L5 和 L9；
- 若指向 L5，L5 helper 与 L9 helper 都会获得 L5 handle；L9 的 100mA/enable 临时请求就错误地叠加到 L5；
- 若指向 L9，则反之；不能通过重复同名属性表达第二个 phandle。

这不是普通 schema 拼写问题，而是 vendor 与 upstream provider device granularity 不同导致的 lookup scope 不兼容。**AI2-ROUND31 不得把单个 parent group proxy-supply 方案直接复制到 Stage A 的一个 PMIC group。**

## 2. ACK 为每个 regulator 保留独立 child OF node：可行的适配入口

固定 ACK regulator core 有一个重要事实：

- regulator_register() 调用 regulator_of_get_init_data(dev, desc, config, &rdev->dev.of_node)，使单独的 regulator class device 拥有对应 child OF node；
- rdev->dev.parent = config->dev，仍然是共享 PMIC group device；
- regulator_dev_lookup() 的 DT lookup 使用 consumer device 自身的 dev_of_node(dev)，因此 regulator_get(&rdev->dev, "proxy") 会从该 child node 查找 proxy-supply；
- regulator_resolve_supply() 则用 rdev->dev.parent 作为实际 regulator parent-supply lookup device，并根据 provider driver 的 supply_name 解析真正 parent input。

源码：[ACK regulator OF-node setup](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L5850-L5905)，[ACK regulator DT lookup](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L1975-L1986)，[ACK parent supply resolution](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L2046-L2070)。

据此，最小而清晰的现代 ACK 适配候选是：

1. 把 proxy consumer 请求属性留在每个具体 regulator child（L5 child 自己、L9 child 自己）。
2. 对 ACK board DTS，将 self proxy-supply 放在对应 child node 并指向自身 phandle，而不是把 L5/L9 两个不同请求都放到共同 PMIC group node。
3. core hook 在具体 rdev 已注册后，使用该 child 的 regulator device 作为 lookup consumer（概念上 regulator_get(&rdev->dev, "proxy")），使 lookup 作用域就是当前 child node。
4. 验证解析得到的 proxy rdev 正好等于当前 rdev；若不是 self-reference 或解析失败，拒绝该 proxy registration 并记录可诊断错误，不能 silently 把投票应用到其他 regulator。

这样每个 child 独立拥有自己的 proxy-supply，L5 与 L9 不再争用同一个 PMIC group property。由于 regulator_resolve_supply() 使用 rdev->dev.parent 解析真正 parent input，而 proxy lookup 使用 rdev->dev.of_node，这两种 scope 可以分开；child 的 proxy-supply 不会仅因属性名以 -supply 结尾，就自动变成该 regulator 的实际电气 parent input。仍须用固定 ACK 的实际 DT lookup、schema 和完整测试证明这一点。

这是一个适配设计方向，不是已经实现的 patch。还需验证 hook 的确切插入位置、锁顺序、device registration 时序和自引用 handle 生命周期。若 2号 AI 选择不同方案，必须证明同样能在同一个 PMIC group 中分别准确创建 L5 与 L9 consumer handles。

## 3. Binding / DTS 必须如何区分

固定 ACK schema：
[qcom,rpmh-regulator.yaml](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml)
[regulator.yaml](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/Documentation/devicetree/bindings/regulator/regulator.yaml)

- qcom,rpmh-regulator.yaml 的 PMIC group 根节点使用 unevaluatedProperties: false，且没有 group-level proxy-supply 声明；把 proxy-supply 放在共同 PMIC group 根节点不是当前 schema 已声明的结构。
- regulator.yaml 对 regulator child 提供 .* -supply$ 对应的通用 supply phandle pattern；child-level proxy-supply 是候选的 ACK board representation。
- qcom,proxy-consumer-enable 与 qcom,proxy-consumer-current 是 regulator child 上的 Qualcomm 私有控制属性；binding 必须在 RPMh regulator child schema 范围内明确声明 Boolean flag 与 uint32 current 类型，并提供正/负 fixtures。
- HOS4.3 原始固件 FDT 不做改写；这里只是在新建 ACK board DTS 时采用 child-specific representation。报告必须明确写成“ACK layout adaptation”，不可说原厂固件就是 child-level proxy-supply。
- 当前 main DTS review draft 尚未包含 L5/L9 proxy fields；本报告没有修改该 draft。

## 4. 错误边界与 ROUND114 的关系

即使使用 regulator_get(&rdev->dev, "proxy") 解决 L5/L9 各自 lookup 作用域，也不能改变 ROUND114 的 ACK regulator-core 错误顺序：
- 100mA stored load 必须先设置，然后 enable；
- late-init / provider unregister 时，enabled handle 必须先 load-zero；
- load-zero/DRMS 失败时不得继续 disable；
- disable 成功后才标记 enable ref 释放；
- stored load 与 enable ref 需要独立状态；
- KONA cleanup 的 disable-first / unconditional free 错误处理不可照搬；
- KONA 与 ACK 对未启用 consumer 的 DRMS load aggregation 不同，late-init 释放时必须验证实际 active UFS/QMP vote 的交接，而不能把 bulk-get 与 active enable 混为一谈。

## 5. 对 AI2-ROUND31 的要求

任务书已要求先证明 self-reference，不可猜测。本轮源码审查进一步证明：
- KONA group-level property 结构适用于 KONA 每 rail 独立 provider device；
- ACK 采用每 PMIC 一个 provider device、多个 child regulator；
- 当前 Stage A 同一 regulators-0 同时承载 L5/L9，因此原 helper 的 regulator_get(group_dev, "proxy") 对两个 child 无法分别定位；
- ACK regulator class device 保留 child of_node，提供 child-specific lookup 入口。

2号 AI 应在 disposable worktree 中基于固定 ACK 实际实现和测试 child-scoped lookup；不得由本地 Agent 编写内核代码。必须验证 L5 handle == L5 rdev、L9 handle == L9 rdev、L5 handle != L9 rdev，以及没有 proxy 属性的 L6/L17 不建立任何 proxy handle。然后再做负向 phandle/schema fixtures 和完整 Image build。

## 6. 角色边界再次确认

AI2-ROUND31 仍是 2号 AI 实际 kernel port 任务。当前发布 taskbook 的“执行者为用户本地 Agent”与用户明确的角色规则冲突。1号 AI 未编辑 AI2 taskbook 或 ai-parallel/stagea-port-until-boot。任务 owner 必须先纠正 coding executor；Agent 只承担独立测试/构建执行。不要把 Agent 报告等同于实际 kernel patch。

## 7. 范围与非声明

本轮仅使用公开固定 ACK 源码、公开 Qualcomm KONA 源码和项目已保存的 Stage A DTS draft 做只读分析。没有修改 AI2 branch、DTS draft、DTS protected branch、PR、firmware、Image 或设备；没有编译或 boot。当前没有证明 L5/L9 proxy 已实际实现或可启动。
