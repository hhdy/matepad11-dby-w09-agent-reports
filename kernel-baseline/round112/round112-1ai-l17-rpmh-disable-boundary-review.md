# ROUND112 — 1号 AI 独立审查：PM8150 L17 / UFS VCC disable failure boundary

任务归属：1号 AI（ChatGPT）独立源码审查
执行性质：对 Agent 已交付静态证据进行独立解释，并对照固定 ACK 源码；不是 Agent 任务，也不是 2号 AI patch 实现。
设备：Huawei MatePad 11 DBY-W09 / KONA / SM8250
固定 ACK：android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
Agent 证据：[ROUND111 报告（firmware-audit-v1）](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round111/TEST_AGENT_ROUND111_L17_RPMH_DISABLE_CONFIG_REPORT.txt)
报告 blob：f6423267249b46ffdab34474d3be34a603ccbb7b

## 1. 独立审查结论

ROUND111 输入身份、结构解析、phandle/fixup 解析和九个 DTBO fragment target 扫描给出了足以支持本轮静态结论的证据。三个 base candidates 对 L17 group/child 字段一致；九个 DTBO 均无 unresolved/dangling fragment target。Agent 遵守只读范围，未修改 parser、固件输入、内核源码或开发分支。

### 1.1 L17 RPMh disable 是异步请求

目标：
- Provider group：/soc/rsc@18200000/rpmh-regulator-ldoa17
- L17 child：/soc/rsc@18200000/rpmh-regulator-ldoa17/regulator-pm8150-l17

HOS4.3 三个 base FDT 的 L17 child 均没有 qcom,always-wait-for-ack；group 同样没有；全树也没有该属性。九个 stock DTBO 均不添加该属性，也不 target/重定义 L17/RSC provider。

固定 ACK drivers/regulator/qcom-rpmh-regulator.c：
- child 初始化时以 of_property_read_bool(node, "qcom,always-wait-for-ack") 读取该属性；
- rpmh_regulator_disable() 将 enable=false 传给 rpmh_regulator_set_enable_state()；
- 发送函数仅在 wait_for_ack || vreg->always_wait_for_ack 时调用 rpmh_write()，否则调用 rpmh_write_async()。

因此，按 HOS4.3 静态配置，L17 disable 使用 rpmh_write_async()。它返回的是请求提交/排队一侧的结果，不等待 PMIC 最终 ACK；不能把 disable 返回 0 解释为已测得 L17 物理电源关闭，也不能把同步 RPMh timeout 套到这个 disable callback。

### 1.2 不能因此跳过 load-zero 的同步失败处理

这与 regulator_set_load(0) 是另一条调用路径，必须分别看待。

固定 ACK 的 RPMh regulator mode/DRMS 更新路径通过 rpmh_regulator_vrm_set_mode_bypass() 发送同步请求（wait_for_ack=true）。对一个已启用且当前负载非零的 consumer，regulator_set_load(0) 会先更新 DRMS aggregate/mode；如果需要从 HPM 切到 LPM，该模式请求可以等待 ACK 并返回 -ETIMEDOUT 等错误。regulator core 在该失败路径回滚 consumer 的 stored load，enable reference 仍保留。

因此 L17 的安全 teardown 顺序仍必须是：

1. 在 consumer 仍 enabled 时执行 regulator_set_load(vcc, 0)；
2. 若 load-zero/DRMS 返回失败，立即停止本轮关闭，不得继续 regulator_disable(vcc)；保留准确的 enabled/stored-load 状态，供后续安全重试/恢复；
3. 只有 load-zero 成功后才调用 regulator_disable(vcc)；
4. 只有 disable 返回成功，才把本地 retained enable-reference 状态标记为已释放。

步骤 2 是同步 DRMS 错误边界；步骤 3 是异步 RPMh disable 提交边界。不能把两者合并成“regulator_disable 异步，所以整个 power-off 不会 timeout”。

### 1.3 L17 的 DTS parent/proxy/coupling 证据

ROUND111 证明：
- L17 group/child 均无普通 *-supply / *-parent-supply；
- 全树没有 vdd-l13-l16-l17-supply、vin-supply、vph-pwr-supply；
- ACK 静态 regulator 描述符仍设置 supply lookup 名 vdd-l13-l16-l17。这是 regulator core 的查找键，不是 FDT 电气证据；
- 当 DT 已填充、无同名 regulator/property 且 full constraints 生效时，固定 ACK core 的 supply resolution 会使用 dummy regulator fallback。此为源码推导，不是 Agent 观测到的运行时日志或对象状态；
- L17 没有 vendor proxy-supply；
- L17 自身无 upstream coupling 属性，RSC 范围无 phandle 反向引用；
- 九个 DTBO 唯一 L17 相关内容是 UFS consumer /fragment@64：vcc-supply = <&pm8150_l17>，vcc-max-microamp = 800000。这是 UFS 使用 L17，不是 L17 的父供电或 coupling；
- 每个 entry 同时包含 UFS VCC voltage range <2504000 2950000> 和其他 UFS consumer supplies；这些是静态 overlay 内容，不能推断实际 ABL 选择 entry。

物理输入 topology 仍为 OPEN。不得用静态表里的 vdd-l13-l16-l17 字符串补造 DTS parent-supply。

## 2. 对 2号 AI 实际实现的约束（不是代写 patch）

2号 AI 实现 UFS generic VCC/L17 teardown 时应纳入以下状态要求：
- 分开记录 regulator stored-load 是否为零、consumer enable reference 是否仍持有；不能用单一 enabled 标志代表两者。
- load-zero 失败时不得继续 disable，也不得清除 retained enable state。
- disable 失败时不得提前清除 retained enable state；但要认识到异步错误只表明请求提交失败，不代表已知 PMIC 物理状态。
- disable 成功只表示异步请求已提交，不是物理 rail 已经完成关闭的 runtime proof。
- 后续重试/重新 power-on 不得无条件重复 enable，避免重复计数 consumer reference。
- 若 HBA remove/devres release 需要处理残余引用，必须按 ROUND102/108/110 已确定的 HBA private wrapper、async join 和 teardown 顺序实现；不要恢复 ROUND95 的 android_oem_data1/devm sidecar 方案。
- 这些是设计审查要求，不代表任何 patch 已集成。

## 3. 证据边界

本轮未执行运行时电压/电流/ACK 测量、未读取 ABL 实际选择的 DTBO entry、未重组 FDT/DTBO、未连接设备、未打包/刷写镜像。Agent 报告不关闭 Phase E/F，Phase G 仍未运行。

## 4. 最终判定

L17 disable callback：异步 RPMh write。L17 load-zero 的 DRMS mode transition：仍可能是同步 RPMh ACK/timeout。这两个结论必须在后续 UFS VCC state machine 和 error path 中同时体现。

下一步由 1号 AI 继续独立固定 ACK 源码审查；实际代码仍由 2号 AI 在 ai-parallel/stagea-port-until-boot 负责。
