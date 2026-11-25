# 1号 AI 专属只读取证任务书 — TEST-AGENT-ROUND106

## DBY-W09 HOS4.3 PM8150 L5 / QMP UFS PHY regulator teardown 属性核验

**任务 ID：** TEST-AGENT-ROUND106  
**下发方：** 1号 AI（ChatGPT）  
**执行方：** 用户本地只读测试 Agent  
**任务性质：** 既有固件工作副本只读取证；不是驱动实现任务。  
**固定 ACK 对照：** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**目标设备：** Huawei MatePad 11 DBY-W09 / KONA / SM8250  
**关联报告：** ROUND105、ROUND103、ROUND90、ROUND99、ROUND100、ROUND77。

> **角色隔离：** 本任务仅属于 1号 AI 下发给本地只读 Agent 的取证任务。Agent 不等于 2号 AI。Agent 不得修改内核、驱动、DTS、binding、补丁或 Git 开发分支。实际内核编程仍由 2号 AI 负责。

---

## 1. 唯一目标

ROUND103 已完整核对 PM8150 L6 对应 VDDP 的 ACK/coupling/parent 属性。ROUND105 发现 QMP UFS PHY 的 `vdda-phy` 使用 PM8150 L5，但 L5 尚未达到与 L6 相同的 FDT 证据标准。

本任务只回答以下静态设备树问题：

**HOS4.3 的 PM8150 L5 provider / regulator 节点是否声明了会影响 ACK `regulator_disable()` 错误边界的 `qcom,always-wait-for-ack` 或 regulator coupling；是否存在其普通 upstream regulator parent supply 属性；九个 stock DTBO 是否覆盖这些配置？**

精确目标：
- PMIC regulator group：`/soc/rsc@18200000/rpmh-regulator-ldoa5`
- L5 regulator child：`/soc/rsc@18200000/rpmh-regulator-ldoa5/regulator-pm8150-l5`
- 一并检查该 group 的全部 regulator child nodes（如 l5-ao / l5-so），以识别可能从 sibling 指向 L5 的耦合关系。

## 2. 输入约束

仅使用 ROUND3 已有、已验证的 HOS4.3 工作副本及既有审查产物：

1. Base boot FDT candidates 0、1、2（ROUND3 已解析工作副本）。
2. Stock DTBO entries 0..8（ROUND3 已解包/解析工作副本）。
3. ROUND103 已验证的 parser、phandle index、fragment-target resolution、overlay composition 模式。
4. ROUND11/ROUND13/ROUND103 的既有报告用于理解属性和核对结果，不重复其已完成的全量工作。

禁止重新提取或重新解包固件；禁止创建替代固件工作区。若上述输入当前缺失或哈希/结构校验不通过，报告输入缺失并停止，不要重新提取。

## 3. 必须逐项核对的属性

对三个 base FDT candidates 分别核对 L5 group 与 L5 child：

### A. RPMh provider ACK 配置
- `qcom,always-wait-for-ack`（存在性、属性长度、raw value）
- 检查它是否出现在 L5 child、group 或其他可能影响实际 L5 regulator 的同级节点；不要把 group 层其他无关属性当成 driver 读取的配置。

### B. Regulator coupling
- `regulator-coupled-with`
- `regulator-coupled-max-spread`
- `regulator-coupled-min-spread`
- `regulator-coupled-no-balance`（如存在）
- 查找整个 `/soc/rsc@18200000` 子树内是否有其他 regulator 节点的 `regulator-coupled-with` phandle 指向 L5 child；不能只检查 L5 节点自己的属性。
- 所有 phandle 必须用现有 base phandle index 解析成完整节点路径，禁止根据数字猜测。

### C. 普通上游 supply / parent
在 L5 group、L5 child 和必要的 RSC subtree 范围内，检查：
- `vdd-l3-l4-l5-l18-supply`
- `vin-supply`
- `vdd-supply`
- `vph-pwr-supply`
- 其他直接出现在目标 provider/group 上的 `*-supply` / `*-parent-supply` 属性。

特别注意：
- ROUND11 已记录 L5 group 的 vendor `proxy-supply`，它指向 RPMh proxy consumer 节点，不等价于物理输入 parent。
- 请原样记录该属性及 phandle target，但不得将它报告成物理输入 rail。
- 不得根据 ACK 的 `supply_name` 字符串推断实际电路连接。

### D. DTBO 覆盖范围
逐一检查全部 9 个 DTBO：
- 是否存在 fragment 目标落在 L5 group、L5 child 或其任何 regulator sibling；
- 是否以 overlay property、fixup 或 local-fixup 方式添加、删除、替换上述 A/B/C 属性；
- 对可用的既有 base/overlay composition 结果，核实最终合成后的目标节点值。
- 保持九个 entry 分别列示；不能把 entry 8 当成唯一实际启动 overlay。
- 如 overlay 目标无法解析，明确列为 unresolved，不得猜测。

## 4. 结果必须区分的结论

请分别给出：

1. `qcom,always-wait-for-ack`：三个 base 候选的精确状态，以及所有 DTBO 是否有覆盖。
2. Coupling：L5 child 自身是否声明 coupling；RSC 子树是否存在其他 regulator 反向耦合到 L5；三份 base 是否一致。
3. Parent supply：实际 FDT 普通 parent 属性是否存在；若没有，区分“DT 中无此 property”与“Linux regulator core 可能使用 dummy regulator fallback”。
4. Vendor proxy：记录 `proxy-supply` 的确切 phandle target，并明确它不证明物理上游 input。
5. Overlay matrix：entry 0..8 对上述字段是否均无修改，或逐个列出差异。

所有结论必须是静态 FDT 证据；不准写出运行时 L5 电压、开关状态或 ABL 当前选用 entry 的推断。

## 5. 工具与工作区安全边界

- 仅允许使用 ROUND3 已审查 parser 及 ROUND9/ROUND8/ROUND103 已审查解析模式。
- 不得下载、安装、编译、运行新的二进制工具或脚本。
- 不得修改、重写、覆盖、解包、重新打包 base FDT / DTBO 或 parser。
- 如需临时输出，只能写入 ROUND106 专属临时目录；结束时清理自己创建的临时文件。
- 不得改变其他 ROUND 工作目录、已有报告或 Git checkout 状态。
- 不得访问设备，不得使用 ADB / fastboot / recovery / reboot / unlock / root / flash。
- 不得读写任何设备分区；不得创建 boot / DTBO image / AVB / vbmeta 产物。
- 不得上传二进制 FDT、DTBO、固件、完整原始 property dump 或本地绝对路径。
- 输出只包括必要的属性名、原始 cell/布尔长度、解析后的节点路径、输入结构校验摘要和逐 entry 结果。

## 6. 唯一交付

报告分支：`firmware-audit-v1`  
唯一报告路径：

`firmware-analysis/round106/TEST_AGENT_ROUND106_L5_RPMH_DISABLE_CONFIG_REPORT.txt`

报告至少包括：
- task ID / issuing AI / executor；
- 输入工作副本身份与结构校验状态；
- 三个 base FDT 对 A/B/C 属性的对照表；
- 所有指向 L5 的反向 coupling phandle 搜索结果；
- 九个 DTBO 逐项覆盖矩阵；
- 可用 overlay composition 的结果；
- 所有 unresolved / not present / not run 状态；
- 证明没有修改固件输入、parser、其他 ROUND、内核源或开发分支的声明。

## 7. 停止规则

上传上述唯一报告后，立即停止。不得启动 ROUND107 或任何后续任务；不得修改 2号 AI 的源代码、补丁或 patch series。

若遇到输入缺失、解析失败、工作副本损坏或安全边界无法维持，停止并在报告中写明唯一阻塞；不得重提取固件、不得自行扩大范围。

**本任务的唯一成果是只读证据报告，不是代码补丁。**
