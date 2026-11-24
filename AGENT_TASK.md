# AGENT_TASK.md — DBY-W09 / Android 17 / ACK 6.18 内核移植总入口

> **当前本地 Agent：ROUND12 唯一待办（只读 AVB 元数据核验）。** ROUND11 已完成并上传。ROUND12 只核验现有 HOS4.3 boot/ramdisk/DTBO 与 vbmeta 的 AVB footer / descriptor 关系；只使用本机已有可信工具，无工具则 BLOCKED，不安装、不下载、不使用 WSL。GPT 继续负责其余公开源码审查和 DTS/Kconfig 设计，不重复 ROUND1–ROUND11。

## 当前项目目标

- 设备：Huawei MatePad 11 DBY-W09，KONA / SM8250 v2.1 / Snapdragon 865。
- ROM 目标：Android 17 DerpFest。
- 内核目标：ACK android17-6.18；目前以 branch Makefile 6.18.33 作为研究基线。
- 第一阶段优先完成 ACK-derived DBY-W09 定制内核的 DTS / UFS / legacy boot-chain 基础。
- 不宣称官方 GKI certified：现有设备是 boot header v2 + 独立 ramdisk 分区，未发现 vendor_boot / init_boot。ACK 6.18 源码不自动等于官方 GKI 合规。

## 当前公开研究报告

- [ROUND23：UFS VCCQ parent rail 与 ACK 驱动适配](./kernel-baseline/round23/ufs-vccq-parent-rail-and-ack-driver-adaptation.md)
- [ROUND23：UFS VCCQ parent rail 与 ACK 驱动适配](./kernel-baseline/round23/ufs-vccq-parent-rail-and-ack-driver-adaptation.md)
- [ROUND23：ACK ARC provider 设备结构与请求聚合设计](./kernel-baseline/round23/ack-arc-provider-device-and-aggregation-design.md)
- [ROUND22：ACK RPMh ARC 与 proxy-consumer 移植可行性](./kernel-baseline/round22/ack-rpmh-arc-and-proxy-consumer-port-feasibility.md)
- [ROUND21：ACK PM8150 VRM parent-supply 与 dummy regulator 风险审查](./kernel-baseline/round21/ack-pm8150-vrm-parent-supply-gap.md)
- [ROUND20：Android first-stage 模块加载、动态分区与 EROFS 配置](./kernel-baseline/round20/android17-first-stage-module-dm-erofs-review.md)
- [ROUND19：HOS4.3 内存节点与 reserved-memory 交接审查](./kernel-baseline/round19/hos43-memory-reserved-memory-handoff-review.md)
- [ROUND18：DBY-W09 legacy boot / ramdisk / DTBO 打包路径审查](./kernel-baseline/round18/dby-w09-legacy-boot-avb-packaging-review.md)
- [ROUND17：ACK 6.18 GENI UART / console 映射审查](./kernel-baseline/round17/ack18-geni-uart-console-mapping-review.md)
- [ROUND16：HOS4.3 RPMh ARC parent graph 与 ACK DTS 映射](./kernel-baseline/round16/hos43-rpmh-arc-parent-graph-to-ack-dts.md)
- [ROUND15：UFS 启动依赖与 rootparam 修正](./kernel-baseline/round15/ack18-storage-bringup-dependency-and-rootparam-correction.md)
- [ROUND14：ACK 6.18 UFS 早期启动 Kconfig 依赖审查](./kernel-baseline/round14/ack18-dby-w09-bootcritical-kconfig-review.md)
- [ROUND13：第一版 ACK 板级 DTS / 最小 rootparam DTBO 设计](./kernel-baseline/round13/ack18-dby-w09-initial-dts-and-dtbo-design.md)
- [ACK 6.18 DTS / Kconfig 草案分支](https://github.com/hhdy/matepad11-dby-w09-agent-reports/tree/ack18-dby-w09-dts-draft)
- [ROUND12：ROUND10 boot-chain 证据更新与 ACK DTS 基础](./kernel-baseline/round12/round10-boot-chain-update-and-ack18-dts-foundation.md)
- [ROUND11 之前的内核优先移植方案](./kernel-baseline/round11/android17-6.18-dby-w09-kernel-port-plan.md)

## 当前重点事实

- UFS HOS4.3 supply map：ROUND9 已完成 8/8 的 Host/PHY 主电源闭合：VCC/L17、VCCQ/L6、VCCQ2/S4、VDDA-PHY/L5、VDDA-PLL/L9、VDDP-REF-CLK/L6、HBA/GCC UFS_PHY_GDSC；另有独立 UFS Host VCCQ parent rail PM8150A S8（1.2–1.4V，210mA）。ROUND23 已将它映射到 ACK PM8150L S8（ROUND7 三个有效 boot-FDT 候选均有此节点），并添加 qcom,vccq-parent consumer 属性与驱动 patch sketch。ACK S8 VRM ops 不支持 DRMS set_load，210mA load vote 可能 no-op；实际 enable/power 和 HOS suspend/resume 等价尚未 runtime 验证。
- ROUND7 确认 PM8150 S4/L5/L6/L9/L17 的 regulator 节点和输出电压；ROUND11 对完整 HOS4.3 base FDT 复核后发现四条 parent-supply 全属于 ARC level groups、六条 proxy-supply 属于 ARC proxy 机制，并全 FDT 确认 vdd-s1..s10/vin/vph-pwr 属性零命中。物理 PMIC 输入 supply 仍未确定。
- 同型号公开 Linux 7.0 DTS 使用固定 3.7 V vph_pwr 和 PM8150 vdd-s1..s10-supply links；其头部说明该部分参考 HOS4.2，因此不能直接当作本设备 HOS4.3 已证实事实。当前 ACK DTS 草案已暂时移除这些未确认输入链接。
- ROUND7 的本机脱敏 DTBO inventory 显示 9 个 stock DTBO entry 都有相同的通用哨兵 huawei,modem_id = <0xffffffff 0>；当前最小 rootparam overlay 已保留该字段。它不是设备唯一编号，但新 DTBO 的 ABL 接受性仍未知。
- ACK SM8250 UFS 节点依赖 GCC UFS_PHY_GDSC、RPMh XO clock、apps_smmu 及 ufs-ddr/cpu-ufs interconnect；其 OPP 表有 RPMhPD required-opps。Kconfig 草案已加上 QCOM_CLK_RPMH、SM8250 interconnect、SCSI DMA、QCOM_RPMHPD 等。UFS `qcom,vccq-parent-supply` 上游驱动未支持，ROUND23 的 source patch draft 会补充可选 regulator enable/load handling；PM8150L S8 没有 set_load op，210mA vote 可能 no-op。HOS4.3 ARC parent/proxy 不能照搬到 ACK VRM group，且完整 MMCX/CX/MX corner equivalence 尚未建立。
- UFS 的直接 UFS_PHY_GDSC 由 GCC 提供；但 ACK 的 ufs_opp_table 通过 required-opps 引用 RPMhPD OPP，因此当前配置保留 QCOM_RPMHPD 以满足 UFS OPP 缩放路径。
- UART：ACK 将 uart2(qcom,geni-debug-uart) 作为 ttyMSM/earlycon console 候选，将 uart6(qcom,geni-uart) 作为 ttyHS 普通串口；HOS4.3 androidboot.console 与物理串口映射尚未证实，两个节点均暂缓启用。见 ROUND17。
- Legacy boot：HOS4.3 本机文件大小与同型号公开项目的 boot 96 MiB、ramdisk 2 MiB、DTBO 24 MiB 一致；同型号公开流程保留 boot header v2 + 嵌入 ramdisk，另更新 ramdisk 分区及 /rootparam DTBO。HOS4.3 boot/ramdisk/dtbo AVB footer 与 vbmeta descriptor 覆盖范围尚待 ROUND12 只读核验。
- Android 首阶段：支持在逻辑分区挂载前从 initramfs /lib/modules 按内核版本/page-size 加载模块；DBY-W09 legacy ABL 是否按 AOSP 要求暴露此目录仍 UNKNOWN。当前 UFS/QMP 保守内建。ROUND20 已确认 BLK_DEV_DM=y 和 EROFS_FS=y；无 DM_LINEAR 独立 Kconfig 项，DM_VERITY/FEC 等待 ROUND12。
- 内存 / 保留区：ROUND7 的 HOS4.3 base FDT 无 /memory 节点，但含 34 个 /reserved-memory 子节点；同型号 HOS4.2 公共 DTS 也没有普通 /memory 节点且只显式保留 4 个节点。ABL 可能注入 usable-memory 描述，但 HOS4.3 ACK handoff 未证实。见 ROUND19；memory/reserved-memory 是实际 DTB 构建前必查 gate。
- Panel ACTIVE_PROFILE=UNKNOWN；ROUND10 ramdisk BLOCKED；EROFS 内容 BLOCKED；system/cust/hw_product filesystem 类型和完整 fstab 未明。

## ROUND11 — 已完成

任务书：[firmware-analysis/round11/AGENT_TASK.md](./firmware-analysis/round11/AGENT_TASK.md)

脱敏结果：[round11_pmic_parent_supply_findings.txt](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round11/round11_pmic_parent_supply_findings.txt)

结论摘要：
- 4 条 `*-parent-supply` 属于 HOS4.3 legacy RPMh ARC level groups，不是 PM8150 VRM 物理输入。
- 6 条 `proxy-supply` 属于 ARC proxy 机制，不是外部输入 supply。
- 全 FDT 扫描未发现 `vdd-s1..s10-supply`、`vin-supply`、`vph-pwr-supply`。
- 所有 11 条 phandle 均已解析；BLOCKED=NONE，UNKNOWN=NONE。
- ACK 不支持把 vendor `qcom,rpmh-arc-regulator` 节点直接搬入上游 VRM regulator；性能级使用 ACK SM8250 rpmhpd/OPP 模型。完整 MMCX/CX/MX corner 等价性仍未建立。

**当前本地 Agent：ROUND12 唯一待办（只读 AVB 元数据核验）。** ROUND11 已完成。ROUND12 只检查现有 HOS4.3 boot/ramdisk/DTBO/vbmeta 的 AVB footer 与 descriptor 覆盖；只使用本机已有可信工具，无工具则 BLOCKED，不安装、不下载、不使用 WSL。GPT 继续做公开源码与配置审查，不重复 ROUND1–ROUND11。

## 仓库与安全边界

- 仓库：hhdy/matepad11-dby-w09-agent-reports
- 本地 Agent 分支：firmware-audit-v1；GPT 公开研究放 main。
- PR #1 必须保持 Draft，未经用户明确授权不得合并。
- 不要求重新上传固件；不重复 ROUND1–ROUND10。
- 不刷机、不解锁、不连接设备、不 root、不写分区、不加载模块、不挂载可写文件系统、不编译。
- 未实际执行的动作必须标记 NOT_RUN / BLOCKED / UNKNOWN。
