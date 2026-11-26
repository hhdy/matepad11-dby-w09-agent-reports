# 【2号 AI 专属任务书】ROUND27 — Kleaf/Bazel 设备树验证

**任务归属：2号 AI 下发。不是 1号 AI 任务，也不是双方共用任务。**

- 下发方 / 技术负责人：**2号 AI（本 ChatGPT 助手）**
- 执行方：**本地 Agent（WorkBuddy / 用户本机执行代理）**
- 任务编号：**AI2-ROUND27**
- 1号 AI：不执行本任务；如另行参与，仅可独立审阅结果。
- 基线：ACK `android17-6.18.33_r00`，common `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- 唯一报告：`firmware-analysis/round27/AI2_ROUND27_KLEAF_DTB_DTBO_SCHEMA_REPORT.txt`
- 上传分支：`firmware-audit-v1`

## 0. 任务身份确认

本文件是 ROUND27 当前唯一有效执行指令。Agent 是执行者，不是“2号 AI”。仓库中旧的 `START_PROMPT.md`、`AGENT_TASK.md` 仅作背景参考，不得覆盖本文件。若收到 1号 AI 的其他任务，必须分开处理；有冲突时暂停冲突部分并报告，不得合并或自行选择。

开始执行记录必须写明：`接受任务 AI2-ROUND27；下发方 2号 AI；执行方本地 Agent`。

## 1. 前置检查

在 `firmware-audit-v1` 分支确认并读取：

- `firmware-analysis/round25/round25-hos43-mmcx-mx-arc-request-semantics.txt`
- `firmware-analysis/round26/round26-sm8250-vs-hos43-reserved-memory-interval-audit.txt`

2号 AI 已在本轮对话中审阅 ROUND25、ROUND26 并放行 ROUND27。旧版任务书引用的 `firmware-analysis/round25-26/PRIMARY_AI_REVIEW_2026-11-25.md` 在该分支当前无法读取，故不再作为启动条件。两份报告任一不可读取则停止，报告 `NOT_STARTED`；不得猜测或绕过。

## 2. 目标与输入

在本机已有 ROUND18 WSL/ACK workspace 的**一次性副本**中，使用现有已检出的 Kleaf/Bazel 工具链，验证：
1. DBY-W09 rev2 base DTB；
2. rootparam DTBO；
3. base DTB + rootparam DTBO composite DTB；
4. 对 composite DTB 执行最窄可用的真实 schema 验证。

输入文件来自仓库 `main`：
- `dts/dby-w09-ack18-board.dts.rev2.candidate`，Git blob SHA `9918efe3f253a3e4821689ffeb899d5a0f237e8f`
- `dts/dby-w09-ack18-rootparam.dtso.draft`，Git blob SHA `c7e5b145d4308e0675ff648b4e046033c5560083`

不得将此任务扩展为 kernel/Image 构建、dtbo.img 表打包、boot.img 打包或设备启动测试。

## 3. 安全边界（不可突破）

- 不连接或操作平板；禁止 ADB、fastboot、recovery、reboot、unlock、root、flash、临时启动及任何分区读写。
- 不下载、安装、更新工具链；不 repo init/sync；不拉取新源码；不改 WSL 配置。
- 不修改 tracked ACK source、DTS、Kconfig、fragment、`.config`、patch 或 Image。
- 不执行 `kernel_build`、`//common:dby_w09`、Image、olddefconfig、menuconfig 或完整内核构建。
- 不构建 `dtbo_image`，不决定 Android DT table id/rev。
- 不生成/修改 boot.img、dtbo.img、vbmeta、AVB footer、签名或刷机包。
- 不推断 HOS4.3 ABL 的 overlay 选择，不宣称设备可启动。
- 所有临时文件仅在 disposable ROUND18 workspace copy 中创建，结束前清理。
- 不上传二进制、源文件、原始构建日志或含敏感路径/物理地址的内容。

任何步骤若需要越过以上边界，立即停止并报告。

## 4. 工作包 A：锁定本地工具版本

只读取现有 ROUND18 workspace：
- 检查根 `MODULE.bazel`、`MODULE.bazel.lock`、`build/kernel/kleaf/bzlmod/bazel.MODULE.bazel`、repo manifest 和本地解析依赖。
- 记录实际 rules_devicetree 版本/提交、Bazel 版本、devicetree toolchain。
- 查看本地锁定规则源码，确认 `dtb()`、`dtbo()`、`dtb_composite()` 的实际 API/属性。
- 确认 `//common:dtc_includes_aarch64` target 存在。

不得用 upstream HEAD 替代本地 pin。无法确认精确版本或 API 时，标记 BLOCKED，不得猜测。

## 5. 工作包 B：临时 staging / BUILD

- 核对两个输入文件的 Git blob SHA 或 SHA-256；只能使用现有 checkout/已连接仓库内容，不得下载新源码。
- 在 disposable workspace copy 的 `common/arch/arm64/boot/dts/qcom/` 临时创建：
  - `huawei-dby-w09.dts`
  - `huawei-dby-w09-rootparam.dtso`
  - 临时 `BUILD.bazel`
- BUILD 只能使用本地锁定版本支持的 rules_devicetree API。
- base DTB target 启用 symbols，srcs 包含 board DTS 和同目录 `sm8250.dtsi`，依赖 `//common:dtc_includes_aarch64`。
- overlay target 构建 rootparam DTBO；composite target 组合 base DTB 与 overlay。
- 只建以上三个目标，不得创建 `dtbo_image`。

## 6. 工作包 C：受限 Bazel 验证

依次执行并记录精确命令、退出码：
1. 对三个临时 target 执行 `bazel query`；
2. 每个 target 执行 `bazel cquery --output=files`；
3. 只对 base DTB、rootparam DTBO、composite DTB 三个 target 执行 `bazel build`。

记录 target label、命令、退出码、输出大小和关键 warning/error（报告中的路径须脱敏）。不得构建 kernel/Image 或 dtbo_image。规则加载/分析/构建失败时保留准确错误并停止对应子任务，不得修改 tracked source 以求通过。

## 7. 工作包 D：Composite 属性 / Schema

用现有 `fdtget`、`fdtdump`、`dtc` 检查 composite DTB：

**Root / rootparam**
- root model、compatible、root `qcom,board-id`；
- `/rootparam` 五项值：
  - `qcom,boardid <0x08 0x02 0x09 0x08>`
  - `board_name = DBY_W09_VG`
  - `product_name = DBY-W09`
  - `hardware_version = SH1DBSLM`
  - `modem id = <0xffffffff 0>`
- 分别记录 overlay root 与 composite root 的 `qcom,board-id`；不得与 Android DT table entry id/rev 混淆。
- 声明 composite 成功不代表 HOS4.3 ABL 会选择 VG overlay。

**UFS Host / PHY**
- Host `power-domains` 顺序：RPMhPD MMCX index 0，GCC UFS_PHY_GDSC index 1；
- PHY 仅保留 GCC UFS_PHY_GDSC；
- Host 检查 `vcc`、`vccq`、`vccq2`、`qcom,vddp-ref-clk`、`qcom,vccq-parent`；
- PHY 检查 `vdda-phy`、`vdda-phy-always-on`、`vdda-pll`；
- 确认不存在 `vdd-hba-supply`。

**Schema**
- 优先使用本地 Makefile/tooling 真正支持的 targeted `dtbs_check`；
- 否则使用本地已存在的 dtschema `dt-validate` 对 composite DTB 和已处理 schema 验证；
- 按适用性覆盖 UFS host/common、SM8250 clock/power-domain、QMP UFS PHY、PM8150 RPMh regulator schema。
- 记录 schema 集合、命令、所有 warning/error 和退出码，不得过滤诊断。dtc exit 0 不等于 schema PASS。

## 8. 清理与完整性

结束前删除临时 DTS、overlay、临时 qcom BUILD.bazel。确认 disposable copy 的 qcom 目录恢复原状；确认原 ROUND18 workspace 的 patch、`.config`、Image 和既有输出未变化；记录清理后的 git status。不得删除/覆盖 ROUND18 既有产物。

## 9. 唯一交付物

只上传一份脱敏 UTF-8 文本报告至：

`firmware-audit-v1:firmware-analysis/round27/AI2_ROUND27_KLEAF_DTB_DTBO_SCHEMA_REPORT.txt`

报告包含：任务归属、前置检查、精确工具 pin、三个 target 的 labels/query/cquery/build 命令及退出码、产物大小、composite 属性检查、schema 集合及完整诊断、清理/完整性证明、未完成事项与限制，并明确声明未执行 kernel/Image、dtbo_image、boot.img、AVB 或设备操作。

报告上传成功后立即停止，不开始 ROUND28，不生成启动包，不连接设备。若前置或工具条件不满足，提交 BLOCKED/NOT_STARTED 报告，不得猜测补齐。

---

**最终确认：AI2-ROUND27；下发方是 2号 AI；执行方是本地 Agent；不是 1号 AI 任务，也不是双方共用任务。**
