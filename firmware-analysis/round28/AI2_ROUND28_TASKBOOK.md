# 【2号 AI 专属任务书】ROUND28 — 固定 ACK UFS 属性消费核验与 Huawei Schema 隔离验证

**任务归属：2号 AI 下发。不是 1号 AI 任务，也不是双方共用任务。**

- 下发方 / 技术负责人：**2号 AI（本 ChatGPT 助手）**
- 执行方：**本地 Agent（WorkBuddy / 用户本机执行代理）**
- 任务编号：**AI2-ROUND28**
- 基线：ACK `android17-6.18.33_r00`，common commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- 工作分支：`firmware-audit-v1`
- 唯一报告：`firmware-analysis/round28/AI2_ROUND28_PINNED_UFS_AND_HUAWEI_SCHEMA_REPORT.txt`

## 0. 任务身份与冲突规则

开始记录必须写明：`接受任务 AI2-ROUND28；下发方 2号 AI；执行方本地 Agent`。

1号 AI 不执行本任务；如另行参与，只能独立审阅。不得把 1号 AI 任务并入本任务，也不得把本任务标记为双方共用任务。若 Agent 当前正在执行任何 1号 AI 或其他 2号 AI 的冲突任务，先暂停本任务并报告冲突，不得自行合并、覆盖或抢占工作区。

本任务由 2号 AI 在审阅 AI2-ROUND27 后独立决定下发。ROUND27 已结束；本任务不代表自动进入后续轮次。报告上传后立即停止，不得自动启动 ROUND29。

## 1. 目标

只做只读源码核验和一次性隔离副本中的 schema 试验，回答以下问题：

A. 固定 ACK commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` 的 `drivers/scsi/ufs/ufshcd-pltfrm.c` 是否读取 `vcc-voltage-level`？如不读取，确认 VCC 的 min/max 电压由何处设定、该驱动是否调用 regulator API 时使用这些范围。

B. 固定 ACK commit 的 `Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.yaml` 对 `vcc-voltage-level`、UFS Host 常见属性及 `unevaluatedProperties` 的实际约束是什么？不能用其他 commit、上游 HEAD、旧 Qualcomm downstream 或 ROUND27 之外的模糊快照替代。

C. 对 ROUND27 报告中实际出现的 Huawei rootparam 私有属性和 root compatible 诊断，设计并验证最小、明确、可审计的 Huawei 专用 binding/schema 草案。仅在 disposable workspace copy 中试验，不修改 tracked DTS、binding、kernel source 或原始候选文件。

## 2. 前置输入

在 `firmware-audit-v1` 读取：
- `firmware-analysis/round27/AI2_ROUND27_KLEAF_DTB_DTBO_SCHEMA_REPORT.txt`
- `firmware-analysis/round27/AI2_ROUND27_TASKBOOK.md`
- `firmware-analysis/round25/round25-hos43-mmcx-mx-arc-request-semantics.txt`
- `firmware-analysis/round26/round26-sm8250-vs-hos43-reserved-memory-interval-audit.txt`

任一前置报告不可读则停止并报告 `BLOCKED`，不得猜测。

## 3. 安全边界（不可突破）

- 不连接或操作平板；禁止 ADB、fastboot、recovery、reboot、unlock、root、flash、临时启动及任何分区读写。
- 不下载、安装或更新工具链；不 repo init/sync；不拉取新源码；不改 WSL 配置。
- 不修改 tracked ACK source、DTS、Kconfig、fragment、`.config`、patch、Image 或正式 binding。
- 不运行 kernel/Image 构建，不运行 dtbo_image、boot.img、AVB/footer/signing/repack 或刷机包流程。
- 不改变 `compatible`、属性名、属性值、regulator 电压、power-domain、RAM/reserved-memory 范围或 PMIC 拓扑。
- 不为消除诊断而删除硬件属性、放宽 `unevaluatedProperties`、屏蔽错误或把 PARTIAL 改为 PASS。
- 所有试验文件只在 disposable copy 中创建，结束前清理。
- 不上传二进制、源文件、原始构建日志、敏感本机路径、物理地址或设备唯一标识。

如某步骤需要越界，停止该子任务并准确报告。

## 4. 工作包 A — 固定 ACK 源码逐行核验

必须先在现有 ROUND18 WSL/ACK checkout 中验证：
`git rev-parse HEAD`、`git rev-parse android17-6.18.33_r00^{commit}`，确认固定提交一致。

对固定提交执行只读检查：
- `git show 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a:drivers/scsi/ufs/ufshcd-pltfrm.c`
- `git show 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a:Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.yaml`
- `git grep -n -e 'vcc-voltage-level' 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a -- drivers/scsi/ufs include/linux Documentation/devicetree/bindings/ufs`
- 检查 `ufshcd_populate_vreg`、`ufshcd_config_vreg` / regulator enable-disable路径及 VCC 默认范围宏定义；记录确切文件和行号。
- 检查同一固定提交的 UFS binding 是否有 `unevaluatedProperties` / `additionalProperties`，并列出与 ROUND27 DTS 实际相关的 properties。

结论必须区分：
1. 驱动是否解析该属性；
2. 驱动内部 vreg min/max 默认值；
3. regulator framework 实际收到的约束；
4. PMIC/regulator 节点本身的电压约束。
不得把“未读取该属性”扩大成“硬件不需要该电压范围”。

若本地 checkout 不存在、HEAD/tag 不匹配或无法读取确切文件，标记 `BLOCKED`，不要用 web 结果或相近 commit 填补。

## 5. 工作包 B — ROUND27 schema 诊断归因

逐项提取 ROUND27 报告中的真实诊断（含 schema 文件名、JSON pointer/node path、property、错误文本）并归类：
- UFS Host schema 不接受的属性；
- `/rootparam` 的 Huawei 私有属性；
- root node compatible 组合；
- 其他独立诊断。

对每条诊断标注：schema 约束本身、缺少 Huawei binding、schema selection/evaluation 问题、或当前证据不足。不得只摘录摘要，不能遗漏原报告中的诊断。

## 6. 工作包 C — 最小 Huawei binding 草案（隔离试验）

基于 ROUND27 实际 DTB 属性和值，拟定最小 YAML binding 草案：
- root compatible 必须精确表达现有 `huawei,dby-w09` + `qcom,sm8250` 的真实组合；不得换成其他厂商板级 compatible。
- `/rootparam` 中属性名保持原样：
  - `qcom,boardid`：4 个 uint32 cell；
  - `huawei,modem_id`：2 个 uint32 cell；
  - `qcom,board_name`、`qcom,product_name`、`hardware_version`：字符串。
- 描述应说明用途，但不得编造硬件语义；未知含义必须明确标注为 vendor-defined/opaque。
- 只声明实际出现且有证据的属性；不要使用宽泛 `additionalProperties: true` / `unevaluatedProperties: true` 来吞掉诊断。
- 若 rootparam 是 overlay 创建的独立节点，binding 的匹配路径/compatible 机制必须符合 dt-schema 实际能力；无法为无 compatible 子节点建立合法绑定时，说明限制并给出合规替代路径（例如在父板级 schema 中约束子节点），不能伪造 compatible。
- 草案必须遵循本地固定 ACK 的 dtschema 版本及 schema meta-schema 规则。

在 disposable copy 中运行：
1. YAML parse / yamllint（如本地工具已存在）；
2. `dt-doc-validate`；
3. targeted `dt_binding_check` 或实际可用的等效 schema 处理；
4. 对 ROUND27 composite DTB 的 targeted `dt-validate`。
同时至少保留一组负向 fixture/试验（错误 cell 数量或错误类型），证明 binding 确实拒绝错误输入，而不是放宽成全接收。

如果工具链或 schema selection 无法可靠运行，报告 `PARTIAL/BLOCKED` 和精确原因。

## 7. 工作包 D — UFS 属性处理建议（不改 DTS）

基于固定 ACK driver + binding + 现有板级证据，给出 `vcc-voltage-level` 的决策树：
- 若固定 ACK driver 不读取：不要仅为了 schema PASS 而保留该属性并误称生效；也不要直接删除。说明需要什么 PMIC/regulator/原厂 DTS/测量证据，才能决定应由 regulator 节点约束、驱动扩展还是其他方式表达。
- 若固定 ACK driver 读取：精确指出读取位置、格式、单位和作用路径，再判断 schema 应如何描述。
- 不得提出未经验证的固定电压值、min/max 数值或 PMIC 父供电关系。

## 8. 清理 / 完整性

结束前删除 disposable copy 中所有临时 schema、fixture、临时修改；确认正式 checkout tracked files 无变化，原 ROUND18 workspace 的 patch、`.config`、Image 和既有输出未变化。报告 git status / diff 摘要（脱敏）。

## 9. 唯一交付物

只上传一份 UTF-8 文本报告：
`firmware-analysis/round28/AI2_ROUND28_PINNED_UFS_AND_HUAWEI_SCHEMA_REPORT.txt`
分支：`firmware-audit-v1`。

报告必须包含：
- AI2 任务归属确认；
- 固定 commit/tag 证明；
- A 包的确切源码证据（路径、行号、关键代码行为）；
- B 包全部 ROUND27 schema 诊断归因；
- C 包 schema 草案结构摘要、命令/退出码、正向与负向结果；
- D 包 UFS 决策建议与未决硬件证据；
- 清理及源树完整性证明；
- 明确未执行 kernel/Image、dtbo_image、boot/AVB packaging 或任何设备操作。

上传成功后立即停止。不要开始 ROUND29，不生成启动包，不连接设备。

---

**最终确认：AI2-ROUND28；下发方是 2号 AI；执行方是本地 Agent；不是 1号 AI 任务，也不是双方共用任务。**
