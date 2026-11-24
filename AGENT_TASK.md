# AGENT_TASK.md — DBY-W09 / Android 17 / ACK 6.18 内核移植总入口

> **当前本地 Agent：暂无待执行任务。** ROUND10 已完成并上传。下一阶段是 GPT 负责的公开源码核对与 ACK 6.18 板级 DTS 设计，不需要本地 Agent 重复解析 FDT/DTBO，也不需要重新上传固件。

## 当前项目目标

- 设备：Huawei MatePad 11 DBY-W09，KONA / SM8250 v2.1 / Snapdragon 865。
- ROM 目标：Android 17 DerpFest。
- 内核目标：ACK `android17-6.18`，当前研究基线目标 6.18.33。
- 第一阶段优先完成 DBY-W09 ACK 派生设备内核的 DTS / UFS / legacy boot-chain 基础。
- 注意：现有设备是 boot header v2 + 独立 ramdisk 分区，未发现 vendor_boot / init_boot。使用 ACK 6.18 源码不自动等于官方 GKI 合规。先按 ACK 6.18 派生的 DBY-W09 定制内核推进，除非后续证明能安全完成标准 GKI 启动架构 retrofit。

## 当前公开研究报告

- [ROUND12：ROUND10 boot-chain 证据更新与 ACK DTS 基础](./kernel-baseline/round12/round10-boot-chain-update-and-ack18-dts-foundation.md)
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

1. 从 ACK `android17-6.18` 及公开同型号 Linux 资料，形成 minimal DBY-W09 board DTS 草案。
2. 以 ROUND9 已确认 rails 和 ROUND7/8 overlay/rootparam 事实为准；panel、THP、WLAN、audio、camera 等未闭环设备先禁用/隔离。
3. 针对原厂 DTBO 目标和 `__symbols__` / `__fixups__`，说明新 DTS 必须满足的兼容条件；不假定旧 DTBO 自动适用于新 DTB。
4. 再决定是否建立独立实现分支。未真正同步源码/编译/启动测试时，不得声称 build pass 或 bootable。

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
