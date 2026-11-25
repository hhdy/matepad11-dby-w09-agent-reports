# 【测试 Agent 专属任务书】ROUND103 — HOS4.3 PM8150 L6 RPMh disable 配置只读取证

**任务归属：测试 Agent 专属只读取证任务。不是 1号 AI 实现任务，也不是 2号 AI 驱动修改任务。**

- 下发方 / 技术审查方：**1号 AI（ChatGPT）**
- 执行方：**本地测试 Agent（WorkBuddy / 用户本机代理）**
- 任务编号：**TEST-AGENT-ROUND103**
- 固定内核基线：ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- 固件证据基线：用户此前已提供并经 ROUND3/13/14/21/64 等报告取证的 HOS4.3 本地固件提取目录
- 唯一交付物：`firmware-analysis/round103/TEST_AGENT_ROUND103_L6_RPMH_DISABLE_CONFIG_REPORT.txt`
- 上传分支：`firmware-audit-v1`

## 0. 启动前身份与排程

开始报告必须写明：

`接受任务 TEST-AGENT-ROUND103；下发方 1号 AI；执行方测试 Agent；只读固件配置取证；不承担驱动实现。`

**排程冲突规则：** 当前仓库中另有 2号 AI 下发的 AI2-ROUND29 任务，已指定本地 Agent 执行。不得并发操作同一工作区。必须先完成 AI2-ROUND29、上传其唯一报告并明确停止；之后才可开始 ROUND103。不得暂停、覆盖、合并或代替 AI2-ROUND29。

本任务只补齐一个精确的 FDT 事实，不得自动启动 ROUND104。

## 1. 唯一目标

从本地已经提取的 HOS4.3 base FDT 和已有九个 DTBO 中，确定 PM8150 L6 regulator 节点在最终可用静态证据范围内的以下属性是否存在、具体内容是什么，以及 DTBO 是否覆盖/修改这些值：

节点预期路径：

`/soc/rsc@18200000/rpmh-regulator-ldoa6/regulator-pm8150-l6`

需要核实：

1. `qcom,always-wait-for-ack`：是否存在（布尔属性）；如果 DTBO 覆盖，分别列出 base 和各覆盖后情况。
2. `regulator-coupled-with`：是否存在；若存在，解析 phandle 到目标节点路径；同时记录对应的 coupling spread 属性（如存在），不解释未知硬件语义。
3. `vdd-l6-l9-supply`：是否存在；若存在，解析 phandle 到实际 regulator 节点路径。
4. 该 L6 节点是否还存在其他上游 input supply 属性，例如 `vin-supply`、`vdd-supply`、`vph-pwr-supply`；逐项说明 presence/absence。
5. 九个 DTBO 是否有任何 fragment/overlay 修改上述 L6 节点、这些属性或其 phandle 指向。必须区分“未命中”与“解析能力不足”。

**重要目的：** 这组事实用于 1号 AI 判断 load-zero-before-disable 后，PM8150 L6 的 regulator-core disable 错误是否还存在 coupling/parent-supply post-decrement 路径，以及 RPMh ACK 超时行为。不得由该任务推断 PMIC 的物理电源输入或电气原理图关系。

## 2. 输入与只读范围

只允许使用：
- ROUND3/13/14/21/64 已存在的本地 HOS4.3 固件提取目录；
- 上述目录内现成的 base FDT / DTB 和对应九个 DTBO；
- 已安装的设备树读取工具（例如已有的 `fdtget`、`fdtdump`、`dtc`、Python libfdt，如果本机已经具备）。

禁止：
- ADB、fastboot、recovery、root、设备重新启动或连接设备；
- 读取设备分区、提取新固件、重新刷写或改动固件；
- 下载/安装/升级任何工具、源码或 Python 包；
- 修改任何 Git tracked 文件、DTS、DTBO、binding、内核补丁、Kconfig、fragment、Image；
- 修改 ROUND29 任务或任何 2号 AI 开发分支；
- 上传固件二进制、DTB、DTBO、原始地址、物理坐标、密钥或其他敏感元数据。

若现成的 base FDT / DTBO 文件不可读，必须返回 BLOCKED/NOT_CAPTURED；不得通过连接设备补取，不得从别的产品或不同固件版本猜测。

## 3. 工作包 A — 精确确认 base FDT 节点

从已存在的 base DTB/FDT 对象读取目标路径，记录：
- 输入文件的原始文件名（可脱敏目录层级）、文件长度与 SHA-256；
- 工具名称、版本（只报告已安装版本）、实际执行命令；
- 目标节点是否存在；
- 本任务第1节每个属性的精确 presence/absence；
- phandle 属性的数值可在内部用于解析，但**上传报告只记录目标节点路径，不记录 phandle 数值或物理坐标**；
- 如果目标路径名称有差异，按兼容链或 phandle 实际定位，解释节点如何匹配；不得直接认定“节点缺失”。

对 `regulator-coupled-with` 需解析全部 phandle；如果 phandle 无效、未解析、目标节点不存在或工具不能解析，逐项标注具体失败情况，不能静默省略。

## 4. 工作包 B — 九个 DTBO 覆盖核验

只读取现存九个 DTBO：
- 记录每个 DTBO 的输入文件标识、大小、SHA-256；
- 解析其 fragment / target / overlay 内容；
- 搜索所有指向目标 L6 节点的 overlay；
- 搜索任何可能修改目标属性或供电 phandle 的片段；
- 如果可在临时目录内用已有工具将 base DTB 与单个 DTBO 合成，允许只做临时只读合成验证；不允许批量构建完整 Android DT table 或生成启动镜像；
- 对每个 DTBO 给出明确结论：覆盖了目标属性、未覆盖（已完整解析）、或无法判断（写明原因）。

临时文件必须在任务结束前删除。不要修改原始输入。

## 5. 工作包 C — 与固定 ACK provider 行为的证据对照

报告只做事实对照，不写驱动补丁：

- 固定 ACK `drivers/regulator/qcom-rpmh-regulator.c` 将 PM8150 L6 定义为 `pmic5_nldo`，使用 `rpmh_regulator_vrm_drms_ops`，HPM 阈值为 30mA；provider disable 通过 RPMh 请求路径。
- `qcom,always-wait-for-ack` 控制 RPMh provider 是否采用同步等待 ACK 路径。
- 若 base FDT 和所有覆盖后的 DTBO 均未出现该属性，只可写“检查范围内未发现该属性”；不要推断控制器绝不等待 ACK。
- `regulator-coupled-with`、`vdd-l6-l9-supply` 等只用于确认软件 regulator-core topology；它们不是 PMIC 物理输入电源树证据。
- 不得把 provider 声明的 supply 名称 `vdd-l6-l9` 当成已存在的物理上游网络。只有真实 phandle 解析到的节点才可称为 DT regulator parent。

## 6. 报告格式与证据等级

唯一报告：

`firmware-analysis/round103/TEST_AGENT_ROUND103_L6_RPMH_DISABLE_CONFIG_REPORT.txt`

必须包含：
1. 任务编号、归属、执行 Agent、停止规则；
2. 固件版本与输入对象 SHA-256；
3. 工具版本、每条读取命令和退出码；
4. 目标节点完整属性 presence/absence 表；
5. phandle 解析结果（节点路径；禁止输出数值）；
6. 九个 DTBO 的 overlay 逐项结果；
7. base FDT 与 overlay 合成后状态（如执行）；
8. 解析失败或缺失的范围；
9. 清理后的临时目录 / git status 摘要；
10. 明确声明无设备访问、无 ADB/fastboot、无工具安装、无 source/DTS/DTBO/patch/config/Image 修改；
11. 结论严格区分：
   - CONFIRMED PRESENT；
   - CONFIRMED ABSENT IN COMPLETE INSPECTED SCOPE；
   - NOT CAPTURED；
   - BLOCKED / PARSE INCOMPLETE。

报告不能包含物理地址、坐标、原始二进制片段、固件二进制、私钥或签名数据。

## 7. 唯一交付与停止规则

上传成功后：
- 立即停止；
- 不启动 ROUND104；
- 不提交驱动代码，不修改 DTS/binding；
- 不执行内核编译、boot 包装、AVB、刷机或任何设备操作；
- 不擅自判定 VDDP 清理已经安全，也不替 2号 AI作出实现决策。

**角色确认：本任务仅为测试 Agent 的只读取证。驱动实现仍归 2号 AI；源码设计和报告审查归 1号 AI。**
