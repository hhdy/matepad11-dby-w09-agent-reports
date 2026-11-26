# [发给测试 Agent] ROUND133 — HOS4.3 UFS Host SMMU/IOMMU FDT 只读取证

- **任务归属：1号 AI（ChatGPT）。**
- **下发与审查：1号 AI。**
- **执行者：用户本地 WorkBuddy Agent（只读固件证据执行者，不是 2号 AI）。**
- **不得编写或修改任何内核/DTS/驱动代码。**
- **不需要设备连接；只读取既有 ROUND3 固件工作副本。**
- 固定 Linux 对照：ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.
- 背景审查：[ROUND133 ACK UFS IOMMU cross-check](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round133/ROUND133_ACK_SM8250_UFS_IOMMU_CROSSCHECK.md).

## 1. 目的

固定 ACK 的 `arch/arm64/boot/dts/qcom/sm8250.dtsi` 在 `ufshc@1d84000` 声明：

`iommus = <&apps_smmu 0x0e0 0>, <&apps_smmu 0x4e0 0>;`

`apps_smmu` 的 `#iommu-cells = <2>`，ACK ARM SMMU OF translation 把第一 cell 当作 SID、第二 cell 当作 stream-match mask。ROUND21 既有报告没有显式盘点 HOS4.3 UFS Host 的 `iommus` 属性，因此需从现有 base FDT / DTBO 工作副本补齐这项事实。

本轮只回答 HOS4.3 静态 DT/FDT 的属性和 phandle 关系；不尝试推断 ABL 实际选了哪一份 DTBO，也不探测真实 SMMU 寄存器或运行时 translation。

## 2. 输入和只读约束

仅允许复用已经存在的 ROUND3 工作副本：
- `boot_fdt_candidate_0.dtb`
- `boot_fdt_candidate_1.dtb`
- `boot_fdt_candidate_2.dtb`
- `dtbo_entry_0.dtbo` 至 `dtbo_entry_8.dtbo`
- ROUND3 已审核的 FDT parser / phandle resolver / overlay fixup 解析模式。

禁止重新提取或重新解包固件。不得创建替代固件工作目录。若既有对象或解析工具不可用，报告 BLOCKED，不要重建数据源，不下载或安装工具。

## 3. 必须核对的节点

对 base FDT candidates 0、1、2 分别读取并完整记录：

A. UFS Host:
- 路径：`/soc/ufshc@1d84000`
- compatible、status。
- `iommus` 属性是否存在；若存在，逐项记录 phandle、其后的 cell 数/值，并解析 provider 节点路径。
- `iommu-map`、`iommu-map-mask`、`stream-match-mask`、`iommu-parent` 等相关属性是否存在。
- 与 UFS Host 对应的其他 IOMMU/IOVA 引用只记录，不推断含义。

B. SMMU provider:
- 通过 Host 的 `iommus` phandle 解析真实目标路径，不得只按节点名称搜索。
- 记录 provider 的 `compatible`、`#iommu-cells`、`status`、`reg` 是否存在。
- 记录 provider phandle 解析是否唯一、是否存在 dangling/unresolved 引用。
- 若 host 没有 `iommus`，仍要检查 base FDT 中是否存在 `apps_smmu` 或同等 SMMU provider；不得把 provider 存在误写成 UFS Host 已绑定。

C. UFS PHY:
- 路径：`/soc/ufsphy_mem@1d87000`
- 检查同一批 IOMMU 相关属性及其 phandle（若有），与 Host 侧严格分开。

所有结果按 candidate 0/1/2 分别报告，再总结三者是否一致。

## 4. 九个 DTBO 覆盖检查

对每个 dtbo_entry_0..8 独立检查：

1. 全 overlay 中所有 fragment target，尤其是指向 `ufshc@1d84000`、`ufsphy_mem@1d87000`、SMMU provider 的 fragment。
2. overlay 是否新增/删除/覆盖 `iommus`、`iommu-map`、`iommu-map-mask`、`stream-match-mask`、`iommu-parent`。
3. `__fixups__` / `__local_fixups__` 中与 UFS Host、PHY、SMMU provider 相关的符号与属性位置；必须解析到真实 base 节点路径。
4. 如果没有 fragment 指向目标节点，结构化地说明为什么 overlay 不可能改变该节点；不要把“反编译文本零命中”当作唯一证明。
5. 如有 target/path/fixup 无法解析，逐项列出，不能默认为无修改。

不得把 entry 8 或任何一个 entry 当作运行时已选中。不要把九个 entry 合并在一起，除非只是报告中逐项列出各自的结构化结果。

## 5. 与固定 ACK 的数值对照

仅做静态比较：
- ACK Host: `<&apps_smmu 0x0e0 0>`, `<&apps_smmu 0x4e0 0>`.
- ACK provider `apps_smmu`: `#iommu-cells = <2>`.
- 把两边的 SID / mask 分开比较，输出 MATCH / DIFFERENT / NOT_PRESENT / UNRESOLVED。
- 不要因为数值相同就宣称 HOS4.3 runtime SMMU 配置与 Linux ACK 等价；软件 device-tree property 相同只证明描述相同。

## 6. 工具与结果标准

- 优先使用 ROUND3 已审核的 parser 和 phandle / fixup 解析脚本。
- 若 dtc/fdtget/fdtoverlay 不可用，不得安装；如既有 parser 能充分解析，明确说明用何种结构化方法以及其边界。
- 记录输入长度与 SHA-256，工具版本、实际执行的命令/脚本、退出码、异常/警告。
- 报告里不得包含原始固件二进制或敏感私有数据，不上传 dtb/dtbo。
- 只提交唯一报告：
  `firmware-analysis/round133/TEST_AGENT_ROUND133_UFS_SMMU_FDT_REPORT.txt`
  上传到 `firmware-audit-v1`，回读确认后停止。

## 7. 安全边界与停止规则

- 不连接平板；不使用 USB、ADB、fastboot、recovery、root、serial 或任何设备接口。
- 不读取设备分区，不执行设备命令。
- 不重新提取固件、不重新解包、不下载或安装工具。
- 不修改内核源、DTS、DTBO、binding、Kconfig、config、patch、PR 或任一 Git 开发分支。
- 不执行编译、Kleaf、dtc build、boot packing、AVB、boot、flash。
- 本轮完成后立即停止，不启动 ROUND134 或 Phase E/F/G。
- 若任何步骤可能需要设备访问，立即停止并向用户报告，不能自行切换到设备操作。
