# AGENT_TASK.md — DBY-W09 / Android 17 / ACK 6.18 内核移植总入口

> **当前本地 Agent：ROUND11 唯一待办（只读）**。只核验 HOS4.3 base FDT 中 PM8150 RPMh regulator 的输入供电 parent links。GPT 已完成可通过公开 ACK 源码、同型号公开仓库和现有 ROUND7/9 报告完成的工作；不要重做 ROUND1–ROUND10，也不要重新上传固件。

## 当前项目目标

- 设备：Huawei MatePad 11 DBY-W09，KONA / SM8250 v2.1 / Snapdragon 865。
- ROM 目标：Android 17 DerpFest。
- 内核目标：ACK android17-6.18；目前以 branch Makefile 6.18.33 作为研究基线。
- 第一阶段优先完成 ACK-derived DBY-W09 定制内核的 DTS / UFS / legacy boot-chain 基础。
- 不宣称官方 GKI certified：现有设备是 boot header v2 + 独立 ramdisk 分区，未发现 vendor_boot / init_boot。ACK 6.18 源码不自动等于官方 GKI 合规。

## 当前公开研究报告

- [ROUND15：UFS 启动依赖与 rootparam 修正](./kernel-baseline/round15/ack18-storage-bringup-dependency-and-rootparam-correction.md)
- [ROUND14：ACK 6.18 UFS 早期启动 Kconfig 依赖审查](./kernel-baseline/round14/ack18-dby-w09-bootcritical-kconfig-review.md)
- [ROUND13：第一版 ACK 板级 DTS / 最小 rootparam DTBO 设计](./kernel-baseline/round13/ack18-dby-w09-initial-dts-and-dtbo-design.md)
- [ACK 6.18 DTS / Kconfig 草案分支](https://github.com/hhdy/matepad11-dby-w09-agent-reports/tree/ack18-dby-w09-dts-draft)
- [ROUND12：ROUND10 boot-chain 证据更新与 ACK DTS 基础](./kernel-baseline/round12/round10-boot-chain-update-and-ack18-dts-foundation.md)
- [ROUND11 之前的内核优先移植方案](./kernel-baseline/round11/android17-6.18-dby-w09-kernel-port-plan.md)

## 当前重点事实

- UFS HOS4.3 supply closure 已在 ROUND9 完成 8/8：UFS Host VCC/L17、VCCQ/L6、VCCQ2/S4；QMP PHY VDDA-PHY/L5、VDDA-PLL/L9、VDDP-REF-CLK/L6；HBA 对应 GCC UFS_PHY_GDSC。
- ROUND7 FDT property inventory 确认 PM8150 S4/L5/L6/L9/L17 的 regulator 节点名称和输出电压属性；但该 CSV 未记录 regulator 的 parent input-supply links。CSV 未记录不等于原始 FDT 一定没有。
- 同型号公开 Linux 7.0 DTS 使用固定 3.7 V vph_pwr 和 PM8150 vdd-s1..s10-supply links；其头部说明该部分参考 HOS4.2，因此不能直接当作本设备 HOS4.3 已证实事实。当前 ACK DTS 草案已暂时移除这些未确认输入链接。
- ROUND7 的本机脱敏 DTBO inventory 显示 9 个 stock DTBO entry 都有相同的通用哨兵 huawei,modem_id = <0xffffffff 0>；当前最小 rootparam overlay 已保留该字段。它不是设备唯一编号，但新 DTBO 的 ABL 接受性仍未知。
- ACK SM8250 UFS 节点依赖 GCC UFS_PHY_GDSC、RPMh XO clock、apps_smmu 及 ufs-ddr/cpu-ufs interconnect。Kconfig 草案已加上 QCOM_CLK_RPMH、SM8250 interconnect、SCSI DMA 等。
- QCOM_RPMHPD 不是当前 UFS GCC GDSC 路径的必需项；仅在后续节点真的引用 RPMh power-domain 时加入。
- Panel ACTIVE_PROFILE=UNKNOWN；ROUND10 ramdisk BLOCKED；EROFS 内容 BLOCKED；system/cust/hw_product filesystem 类型和完整 fstab 未明。

## ROUND11 — 本地 Agent 唯一任务

任务文件：[firmware-analysis/round11/AGENT_TASK.md](./firmware-analysis/round11/AGENT_TASK.md)

只读核验 HOS4.3 base boot FDT 的 PM8150 RPMh regulator 输入供电 parent topology，重点是 apps_rsc 下 regulator group 的 vdd-s*-supply / vin-supply / 类似 parent supply 属性及 phandle 目标路径。只检查已有本机副本和已经安装、可信、可审计的只读 FDT 检查工具。

严格限制：
- 如果没有现成可信工具可用，直接标记 BLOCKED；不安装工具，不下载 EXE/DLL，不写新 parser，不调用 WSL，不绕过 Windows 执行策略。
- 不重新解析 ROUND1–ROUND10 已完成的工作，不要扫描 ramdisk/EROFS，不要连接设备。
- 不执行 ADB/fastboot/刷机/解锁/root/分区写入/模块加载/可写挂载/编译。
- 不导出或上传 DTB/DTBO/FDT/boot/ramdisk/固件/二进制/完整本地路径/本地 SHA256/设备唯一标识。
- 只允许上传简短脱敏文本结论：工具是否已存在、检查是否成功、属性名、供电 parent 的非敏感节点路径或“未见/无法确认”。如发现通用电压数值可报告，但不要上传其他硬件全量信息。
- 对每个未完成检查标记 NOT_RUN / BLOCKED / UNKNOWN，不作缺失推断。

## ROUND11 完成后

把简短文本结果提交至本地 Agent 分支 firmware-audit-v1 的 firmware-analysis/round11/，然后停止，不要触碰 main、DTS 草案分支或 PR。

## 仓库与安全边界

- 仓库：hhdy/matepad11-dby-w09-agent-reports
- 本地 Agent 分支：firmware-audit-v1；GPT 公开研究放 main。
- PR #1 必须保持 Draft，未经用户明确授权不得合并。
- 不要求重新上传固件；不重复 ROUND1–ROUND10。
- 不刷机、不解锁、不连接设备、不 root、不写分区、不加载模块、不挂载可写文件系统、不编译。
- 未实际执行的动作必须标记 NOT_RUN / BLOCKED / UNKNOWN。
