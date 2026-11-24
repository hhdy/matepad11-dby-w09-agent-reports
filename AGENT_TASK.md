# AGENT_TASK.md — DBY-W09 / Android 17 / ACK 6.18 内核移植总入口

> **新会话必读：先读取 [PROJECT_HANDOFF.md](./PROJECT_HANDOFF.md)，再执行本文件。**
>
> **阶段顺序不可颠倒：A）先完成并验证 DBY-W09 的 ACK/GKI 6.18.33 内核移植；B）内核阶段验收后，才开始 Android 17 DerpFest 系统移植。** 当前主线仍是阶段 A。Android 12L 只作历史参考，不是当前目标，不要重复进行泛化调研。

> **当前本地 Agent：ROUND12 唯一待办（只读 AVB 元数据核验）。** ROUND11 已完成并上传。ROUND12 只核验现有 HOS4.3 boot/ramdisk/DTBO 与 vbmeta 的 AVB footer / descriptor 关系；只使用本机已有可信工具，无工具则 BLOCKED，不安装、不下载、不使用 WSL。GPT 继续负责其余公开源码审查和 DTS/Kconfig 设计，不重复 ROUND1–ROUND11。

## 当前项目目标

- 设备：Huawei MatePad 11 DBY-W09，KONA / SM8250 v2.1 / Snapdragon 865。
- ROM 目标：Android 17 DerpFest。
- 内核目标：ACK tag `android17-6.18.33_r00`（官方 tag target commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`）；Stage A 以该固定源码为基线，不跟踪会漂移的 branch HEAD。
- **阶段 A（当前唯一主线）：先完成 ACK/GKI 6.18.33 内核的 DBY-W09 DTS / 驱动 / UFS / 电源域 / memory handoff / legacy boot-chain 适配，并以设备实际启动 6.18.33 内核作为核心验收；仅编译成功不算完成。**
- **阶段 B：只有阶段 A 通过验收后，才开始 Android 17 DerpFest 的 device/vendor/product、HAL/VINTF、SELinux、fstab/init 和镜像集成。**
- ROUND29 已将 ROUND27 的 UFS→RPMHPD 双 GenPD 方案细化到精确 ACK .33 probe 时序；当前为 SOURCE-REVIEWED DESIGN ONLY，尚未写 patch、修改 DTS、编译或运行。
- ROUND30 确认 ACK .33 的 SM8250 MMCX 描述符没有 MX parent，而 HOS4.3 有 MMCX→MX ARC parent-supply 边；UFS→MMCX 路由不能直接宣称复现该关系。MMCX→MX 角点/资源等价性继续作为单独 gate，不得猜测添加 DTS parent。
- 阶段 C 才评估 ColorOS 或其他 ROM。
- DerpFest Android 17 manifest 当前 `kernel-6.18.xml` 指向 June 2026 branch（6.18.21），不改变本项目 6.18.33 目标；Stage B 必须集成本项目已验证的 DBY-W09 内核和匹配模块。
- 官方 Android 17 GKI release 页面列出的 September 2026 分支为 6.18.32；本项目的 6.18.33 ACK-derived build 不得未经 KMI/ABI/认证验证就宣称是官方 certified GKI。
- 不要用 `aosp-mirror/kernel_common` 的 `android17-6.18` GitHub mirror branch 作为 6.18.33 版本证明；该 mirror 当前 Makefile 曾显示 6.18.0-rc6。版本以官方 ACK tag 和锁定 commit 为准。
- 同型号 Android 12L 项目仅供具体问题的历史参考，禁止将其重新作为当前主线或重复调查。
- 不宣称官方 GKI certified：现有设备是 boot header v2 + 独立 ramdisk 分区，未发现 vendor_boot / init_boot。ACK 6.18 源码不自动等于官方 GKI 合规。

## 当前公开研究报告

- [ROUND28：Android 17 ACK 6.18.33 源码基线与 Qualcomm 平台增量策略](./kernel-baseline/round28/android17-6.18.33-source-baseline-and-qcom-platform-delta.md)
- [ROUND30：ACK SM8250 MMCX→MX parent/corner 等价性门槛](./kernel-baseline/round30/sm8250-rpmhpd-mmcx-mx-parent-equivalence-gate.md)
- [ROUND29：ACK .33 UFS 双 GenPD / required-OPP probe 接入设计](./kernel-baseline/round29/ack-qcom-ufs-dual-genpd-required-opp-probe-integration.md)
- [ROUND27：ACK SM8250 UFS required-opps 到 RPMHPD 的 GenPD 路径缺口](./kernel-baseline/round27/ack-sm8250-ufs-rpmhpd-required-opp-routing-gap.md)
- [ROUND24：HOS4.3 ARC 逻辑 corner 与 DT 约束语义](./kernel-baseline/round24/hos43-arc-logical-corner-dt-semantics.md)
- [ROUND23：ACK ARC provider 的 RSC 设备层级与请求上下文设计](./kernel-baseline/round23/ack-arc-provider-rsc-device-hierarchy.md)
- [ROUND26：HOS4.3 PM8150 regulator mode/DRMS 属性证据边界](./kernel-baseline/round26/hos43-pm8150-regulator-mode-property-evidence.md)
- [ROUND25：ACK UFS core 电源顺序与 VCCQ/L6 DRMS 聚合](./kernel-baseline/round25/ack-ufs-core-vccq-l6-drms-order-review.md)
- [ROUND24：ACK UFS VDDP REF_CLK 与 L6 DRMS 负载聚合](./kernel-baseline/round24/ack-ufs-vddp-refclk-and-l6-drms-review.md)
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

- UFS HOS4.3 supply map：ROUND9 已完成 Host/PHY rails 映射：VCC/L17、VCCQ/L6、VCCQ2/S4、VDDA-PHY/L5、VDDA-PLL/L9、UFS device REF_CLK pad VDDP/L6（100µA）、HBA/GCC UFS_PHY_GDSC；另有 UFS Host VCCQ parent rail PM8150A S8（1.2–1.4V，210mA）。ROUND23/24 已将 S8 映射到 ACK PM8150L SMPS8，并将 VDDP 与 VCCQ-parent 两项 vendor consumer 属性统一放在 `&ufs_mem_hc`；QMP PHY 只保留 VDDA-PHY/VDDA-PLL。L6 uses pmic5_nldo DRMS, HPM threshold 30mA aggregated: UFS VCCQ max800mA plus VDDP100µA votes combine; S8 uses pmic5_hfsmps510 without DRMS set_load, so its 210mA request may no-op. Patch sketch covers both but remains unapplied/uncompiled; power behavior unverified.
- ROUND7 确认 PM8150 S4/L5/L6/L9/L17 的 regulator 节点和输出电压；ROUND11 对完整 HOS4.3 base FDT 复核后发现四条 parent-supply 全属于 ARC level groups、六条 proxy-supply 属于 ARC proxy 机制，并全 FDT 确认 vdd-s1..s10/vin/vph-pwr 属性零命中。物理 PMIC 输入 supply 仍未确定。
- 同型号公开 Linux 7.0 DTS 使用固定 3.7 V vph_pwr 和 PM8150 vdd-s1..s10-supply links；其头部说明该部分参考 HOS4.2，因此不能直接当作本设备 HOS4.3 已证实事实。当前 ACK DTS 草案已暂时移除这些未确认输入链接。
- ROUND7 的本机脱敏 DTBO inventory 显示 9 个 stock DTBO entry 都有相同的通用哨兵 huawei,modem_id = <0xffffffff 0>；当前最小 rootparam overlay 已保留该字段。它不是设备唯一编号，但新 DTBO 的 ABL 接受性仍未知。
- ACK SM8250 UFS 节点依赖 GCC UFS_PHY_GDSC、RPMh XO clock、apps_smmu 及 ufs-ddr/cpu-ufs interconnect；其 OPP 表引用 RPMHPD required-opps。ROUND27 发现 Host 当前附着 GCC UFS_PHY_GDSC，而 GCC/GDSC 没有到 RPMHPD 的已证实父级/性能状态回调，因此 required-opps 不能视为已生效的 MMCX vote。ACK 提供 devm_pm_domain_attach_list() 多域接口；可让 Host 同时附着 RPMHPD MMCX 与 UFS_PHY_GDSC，并在 OPP table 初始化前将唯一 required-opps index 0 手动映射到 RPMHPD virtual device。不能对两个 domain 直接启用 PD_FLAG_REQUIRED_OPP，因为第二个 required_dev_index 会超出当前单元素 required-opps 数组。此 UFS patch 仍未实现。Kconfig 草案保留 QCOM_RPMHPD。上游 ACK Host driver 原本不消费 `qcom,vddp-ref-clk` / `qcom,vccq-parent`，ROUND23/24 patch sketch 补充两者的可选 regulator get/load/enable/cleanup。L6 具 DRMS 聚合负载；S8 没有 DRMS set_load，210mA vote may no-op。HOS4.3 ARC parent/proxy 不能照搬到 ACK VRM group，且完整 MMCX/CX/MX corner equivalence 尚未建立。
- UFS 的直接 UFS_PHY_GDSC 由 GCC 提供；ACK ufs_opp_table 虽声明 required-opps 指向 RPMHPD OPP，但 ROUND27 确认性能级请求通过当前 GenPD 路由，原始 GCC GDSC 没有已证实的 RPMHPD 父级。QCOM_RPMHPD 暂时保留为待通过 UFS dual-GenPD patch 接通的 provider，不应写成已生效的 UFS vote。
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
