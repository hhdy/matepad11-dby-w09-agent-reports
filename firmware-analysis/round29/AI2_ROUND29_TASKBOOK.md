# 【2号 AI 专属任务书】ROUND29 — Huawei 根节点 compatible 正式 Schema 架构验证

**任务归属：2号 AI 下发。不是 1号 AI 任务，也不是双方共用任务。**

- 下发方 / 技术负责人：**2号 AI（本 ChatGPT 助手）**
- 执行方：**本地 Agent（WorkBuddy / 用户本机执行代理）**
- 任务编号：**AI2-ROUND29**
- 基线：ACK `android17-6.18.33_r00`，common commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- 工作分支：`firmware-audit-v1`
- 唯一报告：`firmware-analysis/round29/AI2_ROUND29_HUAWEI_BOARD_BINDING_SCHEMA_REPORT.txt`

## 0. 任务身份、前置状态与冲突规则

开始记录必须写明：`接受任务 AI2-ROUND29；下发方 2号 AI；执行方本地 Agent`。

ROUND28 已由 2号 AI 独立审阅：固定 ACK UFS driver audit PASS；rootparam isolated validation PASS；Huawei board schema overall PARTIAL。ROUND28 的 v3 草案顶层使用 `additionalProperties: true`，未能解决根 compatible 的 `oneOf` 诊断 F1，因此不得将其视为可合入的正式 board binding。

1号 AI 不执行本任务；如另行参与，只能独立审阅。不得把 1号 AI 任务并入本任务，也不得标记双方共用。若 Agent 正在执行冲突任务，暂停并报告冲突，不得自行合并或覆盖。

本任务是 2号 AI 在审阅 ROUND28 后独立决定下发，不是自动轮次。上传唯一报告后立即停止，不得自动启动 ROUND30。

## 1. 唯一目标

解决并证明以下问题，不修改正式源码：
1. 在固定 ACK 6.18.33 的实际 dt-schema 结构中，如何正确表达根节点 compatible 精确组合 `huawei,dby-w09` + `qcom,sm8250`，让 ROUND27 的 root `oneOf` 诊断 F1 被真正处理；
2. 如何在不使用宽泛顶层 `additionalProperties: true` 或 `unevaluatedProperties: true` 的情况下，正确声明根节点板级属性和 `/rootparam` 子节点的五个 Huawei/vendor-defined opaque 属性；
3. 通过真实的完整/适当 targeted schema selection 对 ROUND27 composite DTB 验证，并证明错误 compatible、错误 cell count、错误 property type 均会被拒绝。

不要处理 UFS `vcc-voltage-level`，该属性在固定 ACK generic UFS driver 中未被读取，且硬件/PMIC约束仍未知；保持该诊断原样，不通过删除属性或伪造消费者来消除。

## 2. 前置输入

从 `firmware-audit-v1` 读取并核对：
- ROUND27：`firmware-analysis/round27/AI2_ROUND27_KLEAF_DTB_DTBO_SCHEMA_REPORT.txt`
- ROUND28：`firmware-analysis/round28/AI2_ROUND28_PINNED_UFS_AND_HUAWEI_SCHEMA_REPORT.txt`
- ROUND28 taskbook：`firmware-analysis/round28/AI2_ROUND28_TASKBOOK.md`
- 固定 ACK 本地 checkout 和实际 dtschema 版本。

任一输入不可读，停止并报告 BLOCKED。不得从其他 kernel 版本或 upstream HEAD 猜测。

## 3. 安全边界

- 仅只读检查固定 ACK source/schema + disposable workspace copy 中临时 schema/DTB fixtures。
- 不修改 tracked DTS、正式 binding、kernel source、Kconfig、fragment、`.config`、patch、Image。
- 不修改 ROUND27 的原始候选 DTS、rootparam overlay 或 composite 原件。
- 不下载/安装/更新工具链；不 repo init/sync；不拉新源码。
- 不构建 kernel/Image、dtbo_image、boot.img、dtbo.img、AVB/footer/signing/repack。
- 不连接设备；禁止 ADB/fastboot/recovery/reboot/unlock/root/flash/临时启动/分区读写。
- 不改变 compatible/property 名和值，不虚构新的硬件语义。
- 所有临时文件结束前清理；只上传脱敏文本报告。

## 4. 工作包 A — 固定 ACK board schema 架构检查

在已锁定的 ACK checkout 中只读检查：
- `Documentation/devicetree/bindings/arm/qcom.yaml`（若固定提交存在）；
- 其 `$id`、`select`、`properties.compatible`、`oneOf` / `enum` / `const` 结构；
- 与现有 Qualcomm board binding / root compatible schema 相关的引用和处理逻辑；
- 固定提交中至少两个真实 board binding 示例，重点确认根 compatible 的注册位置、schema 选择方式和 top-level `additionalProperties` / `unevaluatedProperties` 用法。
- ROUND28 v3 草案为何只验证 rootparam，却未解决 F1；解释 targeted `dt-validate -l` 的实际 schema-selection 范围。

记录精确 commit、文件路径、行号、schema id、命令和退出码。不得用当前 Linux master 替代固定 ACK 文件。

## 5. 工作包 B — 设计不宽松的 Huawei board schema

在 disposable copy 中提出并比较最少两种合规架构（若固定 ACK 的工具/规则只允许一种，说明原因）：
- 方案一：在现有 Qualcomm root compatible schema 的受控结构中注册精确 pair；
- 方案二：独立 Huawei board binding，并以固定 ACK 支持的机制与 root compatible 选择规则衔接。

要求：
- 根 compatible 精确为 `huawei,dby-w09` + `qcom,sm8250`，顺序与真实 DTB 一致；
- 不添加伪造 compatible，不替换为其他厂商 compatible；
- root `qcom,board-id` 若被 schema 声明，类型与 cell 数量必须基于 ROUND27 实际数据，语义未知则标记 opaque；
- `/rootparam` 必须仍无虚构 compatible，使用父板级 schema 中对子节点的显式属性约束；
- 五个 rootparam 属性保持原名与已核实类型：
  - `qcom,boardid`: uint32 array，恰好 4 cells；
  - `huawei,modem_id`: uint32 array，恰好 2 cells；
  - `qcom,board_name`: string；
  - `qcom,product_name`: string；
  - `hardware_version`: string；
- 所有 vendor-defined opaque 值的描述不得杜撰硬件含义；
- 顶层不得使用宽泛 `additionalProperties: true` 或 `unevaluatedProperties: true`。如需引用通用 schema，应使用固定 ACK 中可验证的 `$ref` / `allOf` / `unevaluatedProperties: false` 组合；否则用明确 properties/patternProperties 约束实际节点。不能为通过 meta-schema 而开放任意根属性。
- rootparam 子节点必须有 `additionalProperties: false` 或等效严格约束；未声明属性应被拒绝。
- 不得用仅对自定义 schema 的单独验证冒充完整 root compatible 验证。

## 6. 工作包 C — 正负向验证

仅在 disposable copy：
1. YAML parse、`dt-doc-validate`、`dt-mk-schema`；
2. 对 ROUND27 composite DTB 执行固定 ACK dtschema 的完整或足够覆盖 root compatible 的验证，确保实际加载/选择 Huawei board schema；
3. 正向：真实 composite root compatible + rootparam 值应通过 Huawei board/rootparam 部分；
4. 负向 fixture 至少三项：
   - root compatible pair 中一个值错误或顺序/组合错误；
   - `qcom,boardid` cell 数错误；
   - `qcom,board_name` 错误类型；
5. 额外负向：在 `/rootparam` 加入一个未声明属性，应被拒绝；
6. 报告每个诊断的 schema id、node path、property、错误内容、diagnostic count 和退出码。注意 dt-validate 即使产生诊断也可能返回 RC=0，必须同时统计 JSON diagnostics。
7. 单独保留 UFS `vcc-voltage-level` 的原诊断，说明它不属于本任务的修复范围；不得隐藏或过滤。

若完整 schema run 有其他历史/无关诊断，逐项列出，不得宣称全局 PASS。可以单独报告 Huawei board binding 子集 PASS，但必须准确界定。

## 7. 工作包 D — 决策与限制

给出推荐方案及理由：
- 能否在固定 ACK dtschema 中无宽松顶层策略地表达 root compatible；
- `/rootparam` 无 compatible 子节点的合规处理方式；
- 要将草案正式合入前，还缺哪些 code review / upstream compatibility / Huawei provenance 证据。
不得提交或修改正式 binding，不得改 DTS。

## 8. 清理与完整性

- 删除 disposable copy 中所有临时 YAML、处理后的 JSON schema、正负向 DTB fixture 和日志。
- 检查固定 ACK tracked source 与正式 binding 无变化。
- 检查原 ROUND18 的 patch、fragment、`.config`、Image 和既有产物未变化。
- 记录清理后 git status / diff 摘要；预先存在的修改必须与任务新增修改区分。

## 9. 唯一交付物与停止规则

只上传：
`firmware-analysis/round29/AI2_ROUND29_HUAWEI_BOARD_BINDING_SCHEMA_REPORT.txt`
分支：`firmware-audit-v1`。

报告必须包含任务归属、固定 commit、方案比较、精确 schema 文件/行号、schema selection 证明、所有命令/退出码/诊断、正负向验证、未解决事项、清理和未执行设备/构建/AVB声明。

上传成功后立即停止。不得启动 ROUND30，不得修改正式 DTS/binding，不得打包或连接设备。

---

**最终确认：AI2-ROUND29；下发方是 2号 AI；执行方是本地 Agent；不是 1号 AI 任务，也不是双方共用任务。**
