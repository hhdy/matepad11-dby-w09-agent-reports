# AI2-ROUND36 — Phase E ABL 内存交接与 PM8150 供电拓扑只读取证盘点

**任务归属：2号 AI 专属任务书**
**执行者：本地 Agent**
**分支：firmware-audit-v1**
**类型：只读取证审计；不做驱动/DTS 修改**

## 目标

ROUND35S 已由 2号 AI 独立验收。下一项工作不是继续 KUnit，而是盘点现有可信资料，明确 Phase E 两个硬件证据缺口：

1. ABL 最终交给 Linux 的 FDT 与 EFI memory map / RAM 保留区交接。
2. DBY-W09 主板 PM8150 L5/L9 的真实物理输入供电拓扑。

本轮目标是回答“现有仓库和已存在工作区资料能否证明这些事实；若不能，具体缺哪种原始证据”。本轮不尝试填补缺失事实，不猜测数值。

## 允许范围

- 只读检查 `ai-parallel/stagea-port-until-boot` 和 `firmware-audit-v1` 中已经提交的报告、DTS、binding、patch、日志、manifest 和证据索引。
- 只读检查 Agent 工作区中**此前已存在且已获准使用**的普通文本/源码/报告；对文件记录路径、来源、时间/版本、SHA-256（若可得）。
- 可以对已提交的 DTS/DTB 文本或既有解析结果进行交叉核对；必须区分源 DTS、编译 DTB、ABL 最终 FDT，不能把前两者冒充最终交接数据。
- 可审阅现有 PMIC/regulator DTS、驱动、binding、已有板级文档，建立“软件描述”与“物理连线证据”的区别。
- 只需产出证据矩阵、缺口清单和下一步最小取证请求，不写任何代码。

## 明确禁止

- 不得重新开始 HOS4.3 固件上传；不得下载、提取、解包、分析任何此前未获准使用的新 HOS4.3 固件镜像或分区转储。
- 不得连接/操作平板，不得使用 ADB、fastboot、recovery、root，不得读取或写入设备分区，不得重启、解锁、临时启动或刷机。
- 不得生成、修改或打包产品 DTS/DTBO、boot/vendor_boot/init_boot、vbmeta、AVB/footer、ramdisk 或刷机包。
- 不得运行产品 Image build；不得改动冻结的 17 个生产补丁、Kconfig、defconfig、Kleaf 目标或 Stage A 源码。
- 不得猜测 RAM 起止地址、reserved-memory 范围、EFI memory descriptor、ABL DTB/DTBO 选择、PM8150 regulator parent、输入电压、负载能力或 PMIC 连接。
- 不得将 Linux DTS 中的 `*-supply` 声明、regulator 节点名称、软件 proxy-vote 或参考平台设计，单独当成 DBY-W09 主板真实物理连线证明。
- 不得把任何“缺失”推断成“硬件不存在”，也不得因未找到证据就自行创建替代值。

## 工作流 A：ABL 最终内存交接

1. 搜索两个指定分支中已经存在的 ABL、boot chain、FDT、EFI memory map、reserved-memory、DTB/DTBO、boot path 报告和证据索引。
2. 建立事实矩阵，至少列出：
   - RAM bank 的 base/size 与来源；
   - ABL/TrustZone/Hypervisor/firmware carveout 的 base/size 与来源；
   - 最终 FDT `/memory/reg`；
   - 最终 FDT `reserved-memory` 的每个相关节点、`reg`、`no-map`、`reusable`、`memory-region` 消费者；
   - EFI memory map 中各 descriptor 的类型、物理范围、属性；
   - ABL 实际选中的 DTB/DTBO、选择条件和版本身份；
   - 证据究竟是源码声明、静态 DTB、ABL 日志、运行时最终 FDT、EFI map，还是二手报告。
3. 对每项标记 `PROVEN` / `PARTIAL` / `MISSING` / `CONFLICT`，不得混淆不同证据等级。
4. 特别确认是否存在 ABL 最终 FDT 与 EFI memory map 的直接证据。若不存在，明确指出不能完成最终内存安全审查。

## 工作流 B：PM8150 物理供电拓扑

1. 搜索已提交的 DBY-W09 DTS、PM8150 regulator 节点、L5/L9、`*-supply`、proxy-consumer、RPMh regulator、板级原理图/PCB/硬件设计资料索引。
2. 对 L5、L9 分别记录：
   - DTS 中声明的 regulator 节点与 parent supply；
   - driver/binding 能证明的芯片内部 regulator 类型与软件语义；
   - 是否有 DBY-W09 专属原理图、PMIC pin/rail net 名称、BOM/板级电源树等物理证据；
   - 输入电压、最大/持续电流、启动时序等是否有可信来源；
   - 软件 proxy-vote 只证明软件请求，不证明真实物理 parent rail。
3. 重点核实 L5/L9 输入 parent 是否由板级原理图或等价硬件原始资料直接证明。参考机型 DTS 或 Qualcomm 公版 DTS 只能作为旁证，不能升级为本机物理事实。
4. 若没有硬件原始资料，输出精确的最小缺件清单，例如：对应主板 revision 的 PMIC 电源树/原理图页、L5/L9 pin 与上游 net 的连续性、上游 rail 电压/电流规格。不得要求用户重复上传已明确禁止的 HOS4.3 镜像。

## 证据等级

- `A — Direct`: DBY-W09 对应硬件 revision 的原始 ABL handoff dump / final FDT / EFI map，或原理图/板级电源树原件。
- `B — Corroborating`: 与该设备精确匹配的 ABL 日志、DTB/DTBO、板级设计说明或经校验的硬件测量记录。
- `C — Software-only`: DTS、driver、binding、Kconfig、公开参考平台源码。
- `D — Inference`: 根据节点名、参考机型、软件请求或常见平台结构推断。D 级不得用于解除 Phase E blocker。

## 交付物

在 `firmware-analysis/round36/` 提交：

- `AI2_ROUND36_EVIDENCE_AUDIT.md`：总报告与明确结论。
- `abl-memory-evidence-matrix.md`：ABL/FDT/EFI/DTB/DTBO 证据矩阵。
- `pm8150-physical-topology-matrix.md`：L5/L9 软件描述与物理证据矩阵。
- `missing-evidence-request.md`：解除阻塞所需的最小原始证据清单；区分用户可提供资料与必须由设备/硬件实验取得的资料。
- `source-hashes.txt`：审阅文件路径、分支/commit、SHA-256 或 Git blob SHA，便于复核。

报告必须引用精确文件路径、commit、行号/节点名和证据哈希。不能只写“搜索过，没有找到”。若仓库证据不足，结论应为 `BLOCKED — direct evidence absent`，并给出下一步最小请求。

## 验收标准

- ABL 与 PM8150 分开审计，不得用一个领域的证据替代另一个领域。
- 每条关键事实均标记证据等级与状态，并给出来源身份。
- 明确区分最终 ABL FDT 与静态 DTS/DTB；明确区分物理供电连线与软件 regulator 描述。
- 没有任何猜测数值、生产代码修改、固件上传、设备操作或打包动作。
- 若资料缺失，准确列出下一步最小取证请求，不得宣称 Phase E 已解除。

## 停止规则

完成报告后立即停止，等待 2号 AI 独立审查。不得自动进入 Phase E 修改、ROUND37、产品构建或任何设备操作。Phase E/F 维持 BLOCKED，Phase G 维持 NOT RUN，除非 2号 AI 在审查直接证据后另行书面授权。