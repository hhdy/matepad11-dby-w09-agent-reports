# ROUND133 — 1号 AI 独立审查与技术结论

日期：2026-11-26  
任务：HOS4.3 UFS Host SMMU/IOMMU FDT 只读取证  
执行者：用户本地 WorkBuddy Agent（只读）  
审查者：1号 AI（ChatGPT）  
固定 ACK：`aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`

## 1. 审查结论

**任务执行结果：PASS（仅限任务书规定的静态 FDT/DTBO 证据范围）。**

已通读原任务书及 Agent 完整报告。报告覆盖三个既有 base FDT 候选、九个 DTBO、UFS Host、UFS PHY、SMMU provider、phandle/fixup 解析和与固定 ACK 的 SID/mask 对照。报告记录 12 个 FDT 对象全部完成双解析器结构一致性核对，1299/1299 个 overlay fragment target 均解析成功，未报告 unresolved/ambiguous target。

Agent 严格遵守只读和停止边界：没有重提取固件、安装工具、修改源码/DTS/配置、连接设备或执行构建/启动/刷写。唯一提交物是脱敏报告，没有上传 DTB/DTBO 原始二进制。

报告 Git blob：`b953aa1627a067dde6491ee85ea415f177ec5daa`  
报告：[TEST_AGENT_ROUND133_UFS_SMMU_FDT_REPORT.txt](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round133/TEST_AGENT_ROUND133_UFS_SMMU_FDT_REPORT.txt)  
任务书：[TEST_AGENT_ROUND133_UFS_SMMU_FDT_TASKBOOK.md](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round133/TEST_AGENT_ROUND133_UFS_SMMU_FDT_TASKBOOK.md)

说明：原始 DTB/DTBO 留在用户本地且未上传，因此本审查是对完整报告、方法、输入身份和任务书符合性的审查，不声称 1号 AI 在云端重新解析了本地二进制。

## 2. HOS4.3 静态 FDT 事实

### 2.1 三个 base FDT 候选

三个候选均存在节点 `/soc/ufshc@1d84000`，compatible 为 `qcom,ufshc`，基础树中 status 均为 `disabled`。

三个候选的 UFS Host 均没有：
- `iommus`
- `iommu-map`
- `iommu-map-mask`
- `stream-match-mask`
- `iommu-parent`

UFS PHY `/soc/ufsphy_mem@1d87000` 同样没有上述 IOMMU 属性。三个候选在本任务所关心的 Host/PHY/SMMU 事实上一致，尽管根节点型号分别标为 KONA v2.1、v2、v1。

### 2.2 SMMU provider 存在，但 UFS Host 没有绑定

三个候选均包含 `/soc/apps-smmu@15000000`，compatible 为 `qcom,qsmmu-v500`，`#iommu-cells = <2>`，phandle 解析唯一（报告中的 phandle 72）。另有 KGSL SMMU provider。

**不能把 apps SMMU provider 存在误读成 UFS Host 已连接该 provider。** 因为 Host 本身没有 `iommus` 属性，没有可供解析的 Host→provider phandle；报告正确判为 NOT_BOUND，而不是 dangling reference。

### 2.3 九个 DTBO

九个 DTBO 的 UFS 相关 overlay 结构一致：
- `fragment@63` 指向 `/soc/ufsphy_mem@1d87000`，设置 PHY compatible/status 和 PHY rails。
- `fragment@64` 指向 `/soc/ufshc@1d84000`，设置 Host status 和 UFS VCC/VCCQ/VCCQ2/VDDP/VDD-HBA 等 regulator consumers。

这些 UFS fragment 没有新增任何 IOMMU 属性，也没有 fragment 指向 apps SMMU provider。全部 overlay 的 IOMMU 家族属性计数为 0；UFS 相关 10 处 fixup 为 2 个 target phandle 和 8 个供电/GDSC phandle，没有 SMMU/IOMMU fixup symbol。

因此，在本次扫描的三个 base FDT 与九个 DTBO 静态对象中，HOS4.3 没有 UFS Host→SMMU 的设备树绑定描述。

## 3. 与固定 ACK 6.18.33 的差异

固定 ACK 的 `sm8250.dtsi` 已经在 UFS Host 声明：

```dts
iommus = <&apps_smmu 0x0e0 0>, <&apps_smmu 0x4e0 0>;
```

两个 SID 分别为 `0x0e0`、`0x4e0`，mask 均为 `0`；provider 的 `#iommu-cells = <2>`。HOS4.3 侧有相同的 cells 数，但 Host 没有 iommus 属性，因此 SID/mask 的判定应为 **NOT_PRESENT**，不是 DIFFERENT，也不是 MATCH。

另一个差异是 provider compatible：
- HOS4.3：`qcom,qsmmu-v500`
- 固定 ACK SM8250 DTSI：`qcom,sm8250-smmu-500`、`qcom,smmu-500`、`arm,mmu-500`

对固定 ACK 的驱动源码继续核对：
- `arm-smmu.c` 的顶层 `arm_smmu_of_match[]` 包含 `arm,mmu-500`，不包含单独的 `qcom,qsmmu-v500`。
- `arm-smmu-qcom.c` 的 Qualcomm implementation table 包含 `qcom,sm8250-smmu-500`，映射到 SM8250 对应的 SMMU-500 implementation data。

所以，**不得把 HOS4.3 的 `qcom,qsmmu-v500` compatible 直接复制覆盖 ACK provider compatible 列表**。应保留固定 ACK 针对 SM8250 的 compatible 定义。

固定源码位置：
- [ACK SM8250 UFS Host 与 SMMU provider](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/boot/dts/qcom/sm8250.dtsi)
- [ACK ARM SMMU platform compatible match](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/iommu/arm/arm-smmu/arm-smmu.c#L1954-L1962)
- [ACK Qualcomm SM8250 SMMU implementation match](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/iommu/arm/arm-smmu/arm-smmu-qcom.c#L716-L727)

## 4. 对当前板级 DTS 草案的处置

当前 `dby-w09-ack18-board.dts.draft` include 固定 ACK 的 `sm8250.dtsi`，对 `&ufs_mem_hc` 的板级 overlay 只补充已研究的 supply/status 属性，没有重新声明或删除 `iommus`。因此当前 ACK 派生板级树会继承 SM8250 SoC DTSI 的两个 UFS SID。

本次结果**不构成删除 ACK 两条 SID 的依据，也不需要添加重复的 board-level `iommus` 属性**。先保留上游 ACK 定义，记录 HOS4.3 静态描述差异，后续在启动链与 DMA/IOMMU 生命周期审查中继续核验。

## 5. 严格的证据边界

本次结果只证明所检查的静态固件 FDT/DTBO 对象没有 UFS Host 的 `iommus` 描述。它不证明：
- ABL 实际选中了哪个 base FDT 或哪一个 DTBO；
- 设备运行时 UFS 是否处于 SMMU bypass、identity path 或其他模式；
- bootloader/安全固件是否预配置了 SMMU；
- SMMU stream table、context bank、translation regime 或真实寄存器内容；
- Linux ACK 运行时初始化这两个 SID 后一定能正常工作。

三个 base FDT 是从 boot.img 扫描得到并通过 header/结构解析的候选，不能当作已确认的 live DTB。九个 DTBO 也不能推定其中任何一个已被 ABL 选中。

因此，准确表述是：**HOS4.3 被检查的静态 FDT/DTBO 不声明 UFS Host 到 apps SMMU 的映射；固定 ACK 6.18.33 则显式声明两个 UFS SID。运行时差异仍 UNKNOWN。**

## 6. 阶段状态

- ROUND133 静态取证任务：**PASS / 已审查接受**。
- ACK UFS SMMU mapping：源码已有，当前 board DTS draft 继承；不重复声明。
- HOS4.3 UFS SMMU runtime 行为：**UNKNOWN / 未证明**。
- Stage A Phase E/F：仍 BLOCKED（ABL 内存/FDT handoff、PMIC physical parent topology、boot/DTBO/AVB 等已有阻塞项不因本轮消失）。
- Phase G：NOT RUN。
- 未修改生产补丁、DTS、Kconfig、产品配置、AI1/AI2 分支；未连接设备、编译、启动或刷写。
