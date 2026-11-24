# AGENT_TASK.md — DBY-W09 / Android 17 / ACK 6.18 内核移植总入口

> **当前本地 Agent：暂无待执行任务。** ROUND10 已完成并上传。下一阶段是 GPT 负责的公开源码核对与 ACK 6.18 板级 DTS 设计，不需要本地 Agent 重复解析 FDT/DTBO，也不需要重新上传固件。

## 当前项目目标

- 设备：Huawei MatePad 11 DBY-W09，KONA / SM8250 v2.1 / Snapdragon 865。
- ROM 目标：Android 17 DerpFest。
- 内核目标：ACK `android17-6.18`，当前研究基线目标 6.18.33。
- 第一阶段优先完成 DBY-W09 ACK 派生设备内核的 DTS / UFS / legacy boot-chain 基础。
- 注意：现有设备是 boot header v2 + 独立 ramdisk 分区，未发现 vendor_boot / init_boot。使用 ACK 6.18 源码不自动等于官方 GKI 合规。先按 ACK 6.18 派生的 DBY-W09 定制内核推进，除非后续证明能安全完成标准 GKI 启动架构 retrofit。

## 当前公开研究报告

- [ROUND14：ACK 6.18 UFS 早期启动 Kconfig 依赖审查](./kernel-baseline/round14/ack18-dby-w09-bootcritical-kconfig-review.md)
- [ROUND13：第一版 ACK 板级 DTS / 最小 rootparam DTBO 设计](./kernel-baseline/round13/ack18-dby-w09-initial-dts-and-dtbo-design.md)
- [ROUND12：ROUND10 boot-chain 证据更新与 ACK DTS 基础](./kernel-baseline/round12/round10-boot-chain-update-and-ack18-dts-foundation.md)
- [ACK 6.18 DTS 草案分支](https://github.com/hhdy/matepad11-dby-w09-agent-reports/tree/ack18-dby-w09-dts-draft/dts)
- [ROUND11：Android 17 / ACK 6.18 内核优先移植方案](./kernel-baseline/round11/android17-6.18-dby-w09-kernel-port-plan.md)
- [ROUND10：ACK 6.18 板级 DTS 兼容性评估](./kernel-baseline/round10/ack18-board-dts-migration-assessment.md)
- [ROUND9：ACK 6.18 驱动兼容矩阵](./kernel-baseline/round9/dby-w09-6.18-driver-compatibility-matrix.md)
- [ROUND8：HOS4.3 硬件参考对照](./kernel-baseline/round8/harmonyos43-hardware-reference-comparison.md)
- [ROUND6：上游 GKI 基线研究](./kernel-baseline/round6/upstream-baseline-research.md)

## 本地 Agent 历史结果

- [ROUND10 本机 boot/ramdisk 报告](https://github.com/hhdy/matepad11-dby-w09-agent-reports/tree/firmware-audit-v1/firmware-analysis/round10)：2 份文本，`COMPLETE_WITH_BLOCKED_SUBITEMS`。
  - cmdline 范围：`NO_PANEL_SELECTOR_FOUND_IN_CMDLINE_SCOPE`。
  - ramdisk：`BLOCKED`，未读取，不得写成全局无 selector。
  - mount/fstab/module/firmware 路径：`NOT_READ_BLOCKED`。
  - `ACTIVE_PROFILE=UNKNOWN`。
- [ROUND9 本机报告](https://github.com/hhdy/matepad11-dby-w09-agent-reports/tree/firmware-audit-v1/firmware-analysis/round9)：4 份文本，UFS supply 8/8 闭环；panel ACTIVE_PROFILE、camera model、redriver model 仍 UNKNOWN。
- [ROUND8 本机报告](https://github.com/hhdy/matepad11-dby-w09-agent-reports/tree/firmware-audit-v1/firmware-analysis/round8)：3 份文本，145/145 overlay target resolved，fragment@143 -> /rootparam。
- ROUND7：13/13 FDT valid，9 个 DTBO board-id 已校验。
- ROUND5：EROFS 内容枚举 BLOCKED；vendor/odm 模块、firmware、VINTF、KMI 仍 UNKNOWN。

## 当前重点技术事实

- Google ACK 源码父分支为 `android17-6.18`；先前 branch HEAD Makefile 识别为 6.18.33。但 Google Android 17 GKI release page 当前公开的 2026-09 认证 release 是 6.18.32；源码分支/Tag 不能当成已认证 GKI image。
- ACK SM8250 DTSI 已有 UFS Host `ufs_mem_hc`、QMP PHY `ufs_mem_phy` / `ufs_mem_phy_lanes`、SPI14 `spi14`，可按 ROUND9 HOS4.3 事实制定板级 enable/rail mapping。
- UFS host 的 ACK SoC 节点使用 GCC UFS PHY BCR reset 和 UFS_PHY_GDSC power-domain；PHY 的 reset specifier 是 `<&ufs_mem_hc 0>`。
- UFS rails 需按 ROUND9 的 PM8150 rail map迁移；`vdd-hba` 映射到 GDSC，不应重复作为通用 regulator，`qcom,vccq-parent-supply` 是下游扩展。
- HOS `qcom,dsi-default-panel` 指向 overlay 域 CSOT NT36523 默认候选，不代表 runtime active。ROUND10 cmdline scan only 没有 selector；ramdisk scan blocked；ACTIVE_PROFILE 继续 UNKNOWN。
- 当前 boot layout 为 v2 + 独立 ramdisk，不存在标准 vendor_boot/init_boot 证据。ACK 6.18 kernel image 与 GKI boot architecture retrofit 是两个独立问题。

## 下一阶段由 GPT 负责

1. ROUND13 已形成第一版 minimal board DTS 和单 fragment rootparam DTBO 草案，位于 `ack18-dby-w09-dts-draft` 分支 `dts/` 目录；文件后缀 `.draft`，不供构建或刷写。
2. ROUND14 已完成 UFS early-boot Kconfig 依赖审查；对应的 built-in storage-first fragment 位于实现草案分支 `config/dby-w09-ack18-storage-first.fragment.draft`，仍未运行 Kconfig resolution。
3. 关键架构决定：原 HOS4.3 stock DTBO entry 8 有 145 个 fragment target，引用大量 vendor-only path / symbol，不能直接用于 minimal ACK base DTS。新 DTS 必须搭配单独的最小 DBY-W09 rootparam overlay，ABL 接受性仍 UNKNOWN。
4. GPT 下一步继续审查 PMIC 输入供电和 rootparam/ABL 契约，并补齐早期 DTS 的 clock / SMMU / PMIC / console 节点依赖；panel、THP、WLAN、audio、camera 等暂不启用。
5. 只有在 source review 完成后才考虑允许的离线构建环境与静态校验。未真正 dtc/dt-schema/Kconfig/Kleaf 编译、image packaging 或 device boot 时，不得声称验证通过或可启动。

## 何时需要重新下发本地任务

只在工作涉及本机文件、已存在的固件副本、Windows 环境或确有本机只读验证时创建新任务。
ROUND10 ramdisk BLOCKED 的解除条件是：本机已有可信 Android boot unpack 工具（或可审计的已批准提取工具）并且用户明确授权。不得自写 boot parser、安装未知 EXE/DLL、绕过 Windows 命令安全策略或调用 WSL。
不要求重新上传固件，也不重复 ROUND1–ROUND10 已完成的 FDT/DTBO 解析。

## 仓库与安全边界

- 仓库：`hhdy/matepad11-dby-w09-agent-reports`
- 本地 Agent 分支：`firmware-audit-v1`；GPT 公开研究放 `main`。
- PR #1 必须保持 Draft，未经用户明确授权不得合并。
- 仅上传脱敏文本 / 源码；不得上传固件、boot/ramdisk、DTB/DTBO/FDT、内核、模块、firmware 二进制、manifest 原件、完整本地 SHA-256、设备序列号/MAC、token/PAT 或私人完整路径。
- 不刷机、不解锁、不连接设备、不 root、不写分区、不加载模块、不挂载可写文件系统、不编译，直到用户明确改变边界。
- 未实际执行的动作标记 `NOT_RUN` / `BLOCKED` / `UNKNOWN`，不得虚报完成。
