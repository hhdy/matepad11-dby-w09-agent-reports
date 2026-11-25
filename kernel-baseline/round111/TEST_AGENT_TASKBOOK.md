# 1号 AI 专属只读取证任务书 — TEST-AGENT-ROUND111

## DBY-W09 HOS4.3 PM8150 L17 / UFS VCC regulator teardown 属性核验

**任务 ID：** TEST-AGENT-ROUND111  
**下发方：** 1号 AI（ChatGPT）  
**执行方：** 用户本地只读测试 Agent  
**任务性质：** 已有固件工作副本只读取证；不是驱动实现任务。  
**固定 ACK 对照：** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**目标设备：** Huawei MatePad 11 DBY-W09 / KONA / SM8250  
**关联报告：** ROUND90、ROUND103、ROUND105、ROUND106、ROUND107、ROUND109、ROUND110。

> **角色隔离：** 本任务只属于 1号 AI 下发给本地只读 Agent 的证据任务。Agent 不是 2号 AI。Agent 不得修改内核、DTS、binding、补丁或 Git 开发分支。实际实现仍由 2号 AI 负责。

---

## 1. 唯一目标

UFS generic VCC 使用 PM8150 L17 / LDO17。固定 ACK 将 L17 映射为 PMIC5 PLDO，具备 DRMS mode control，HPM threshold 10mA；UFS VCC 的当前候选负载为 800mA。ROUND90 已确认 load-zero-before-disable 可避免 regulator core 在 consumer enable_count decrement 后执行非零 load 的 DRMS 更新。

但目前已有 HOS4.3 只读取证：
- ROUND103 完整检查 L6；
- ROUND106 完整检查 L5；
- **尚未以相同证据标准检查 L17 的 `qcom,always-wait-for-ack`、coupling 和 upstream supply 属性。**

本任务只回答：HOS4.3 的 PM8150 L17 provider / regulator 节点是否声明会影响 ACK `regulator_disable()` 错误边界的 ACK/coupling/parent 配置；九个 stock DTBO 是否覆盖这些属性？

精确目标：
- PMIC regulator group：`/soc/rsc@18200000/rpmh-regulator-ldoa17`
- L17 regulator child：`/soc/rsc@18200000/rpmh-regulator-ldoa17/regulator-pm8150-l17`
- 一并检查该 group 的全部 regulator child nodes，识别可能从 sibling 指向 L17 的反向耦合关系。

## 2. 输入约束

仅使用 ROUND3 已有、已验证的 HOS4.3 工作副本和既有审查产物：

1. Base boot FDT candidates 0、1、2（ROUND3 已解析工作副本）。
2. Stock DTBO entries 0..8（ROUND3 已解包/解析工作副本）。
3. ROUND103 / ROUND106 已验证的 parser、phandle index、fragment-target resolution、overlay composition 核验模式。
4. ROUND13 的 L17 身份、mode/DRMS 和电压静态证据。
5. 不重复检查 L5、L6 已经完成的字段；本轮目标仅为 L17。

禁止重新提取、重新解包固件或创建新的固件工作区。若现有输入缺失、结构校验失败或哈希不一致，记录唯一阻塞并停止，不得重提取。

## 3. 必须逐项核对的属性

对三个 base FDT candidates 分别检查 L17 group 与 L17 child。

### A. RPMh ACK 配置
- `qcom,always-wait-for-ack`（presence/absence、属性长度和 raw value）。
- 分别检查 L17 child、group 以及必要的 provider 层节点。
- 固定 ACK 的 RPMh driver 是从单个 regulator child node 读取此属性；因此报告必须明确 child 自身值，不能只记录 group-level 检查结果。
- 检查 RSC subtree 的其他可能 L17 同组 regulator child 是否有该属性，但不能误认为兄弟节点属性自动继承到 L17。

### B. Regulator coupling
逐项检查：
- `regulator-coupled-with`
- `regulator-coupled-max-spread`
- `regulator-coupled-min-spread`
- `regulator-coupled-no-balance`
- HOS vendor coupling-like property（如有，原样记录，不要默认等价于 upstream binding）。

同时扫描整个 `/soc/rsc@18200000` 子树内的反向 coupling：是否有其他 regulator child 的 phandle 指向 L17 child。所有 phandle 必须用既有 base phandle index 解析成完整节点路径；不得仅凭 cell 数字猜测。

### C. 普通 upstream supply / parent
在 L17 group、L17 child 和必要的 RSC subtree 范围内检查：
- `vdd-l13-l16-l17-supply`
- `vin-supply`
- `vdd-supply`
- `vph-pwr-supply`
- 其他直接声明在 L17 provider/group/child 上的 `*-supply` / `*-parent-supply` 属性。

请区分：
- 普通 regulator parent supply property；
- HOS vendor `proxy-supply`；
- voltage-level / ARC 关系。

如果发现 `proxy-supply`，必须解析 phandle target 并说明它是否属于 proxy 语义；不得将其直接报告成物理输入 parent。

ACK PM8150 L17 的 driver `supply_name` 是 `vdd-l13-l16-l17`。这个 C 字符串只定义 Linux regulator core lookup 名称，不能证明实际物理供电网。

### D. DTBO 覆盖范围
逐一检查九个 stock DTBO：
- 是否有 fragment 目标为 L17 group、L17 child 或其 regulator sibling；
- 是否以 overlay property、fixup 或 local-fixup 方式增加、删除、替换上述 A/B/C 属性；
- 对已有 base/overlay composition 结果，检查最终目标节点值；
- 九个 entry 必须分别列出。不能假定 entry 8 是实际启动选择。
- 如果 overlay target 无法解析，标记 unresolved，不得猜测。

## 4. 结果必须区分的结论

请给出以下独立结果：

1. L17 的 `qcom,always-wait-for-ack`：三个 base 候选精确状态，以及九个 DTBO 是否覆盖。
2. Coupling：L17 child 自身声明、反向引用搜索结果、三个 base 是否一致。
3. Parent supply：普通 DT upstream 属性是否存在；如不存在，应区分“FDT 中无该 property”和“ACK regulator core 在 full constraints 下可能采用 dummy fallback”。
4. Vendor proxy：如存在，给出精确 phandle target；必须明确不能凭 proxy-supply 推断真实电气输入。
5. Overlay matrix：entry0..8 对以上属性是否均无修改；如有差异逐项列出。
6. Failure-boundary classification：根据固定 ACK driver 行为，静态配置更接近同步 `rpmh_write()` 还是异步 `rpmh_write_async()`；不要仅根据 regulator type 猜测。

**不要**报告运行时电压、使能状态、PMIC ACK 实际完成状态、ABL 当前选中的 DTBO entry 或电气原理图结论。

## 5. 工具与工作区安全边界

- 只允许使用 ROUND3 已审查 parser，以及 ROUND8/9/103/106 已审查的解析模式。
- 不得下载、安装、编译或运行任何新的二进制工具或脚本。
- 不得修改/覆盖/重新解包/重打包 base FDT、DTBO、parser 或其他 ROUND 的工作文件。
- 如需临时输出，仅写入 ROUND111 专属临时目录，结束时清理自己创建的临时文件。
- 不得访问设备，不得使用 ADB / fastboot / recovery / reboot / unlock / root / flash。
- 不得读取或写入设备分区；不得构建 boot / DTBO image / AVB / vbmeta。
- 不得上传二进制 FDT、DTBO、固件、完整原始属性 dump 或本地绝对路径。
- 仅输出必要属性名、布尔长度、raw cell、解析后的节点路径、输入结构校验摘要和逐 entry 结果。

## 6. 唯一交付

报告分支：`firmware-audit-v1`  
唯一报告路径：

`firmware-analysis/round111/TEST_AGENT_ROUND111_L17_RPMH_DISABLE_CONFIG_REPORT.txt`

报告至少包含：
- task ID / issuing AI / executor；
- 输入工作副本身份和结构验证结果；
- 三个 base FDT 的 A/B/C 属性对照；
- 全 RSC subtree 指向 L17 的反向 coupling 搜索结果；
- 九个 DTBO 逐项覆盖矩阵；
- 已有 overlay composition / fragment-target 核验结果；
- unresolved / not present / not run 项；
- 未修改任何固件输入、parser、内核源、其他 ROUND 或 Git 开发分支的声明。

## 7. 停止规则

上传唯一报告后立即停止。不得启动 ROUND112 或任何后续任务；不得修改 2号 AI 的源代码、补丁、DTS、binding 或 patch series。

若输入缺失、解析失败或不能保持安全边界，停止并在报告中记录阻塞；不得重新提取固件或扩大任务范围。

**本任务的唯一成果是只读证据报告，不是代码补丁。**
