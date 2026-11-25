# ROUND135 — full-tree DTS / dual-GenPD integration validation taskbook

- **下发方 / 技术负责人：1号 AI（ChatGPT）**
- **源码候选负责人：1号 AI（ChatGPT）**
- **执行方：用户本地 WorkBuddy 测试 Agent**
- **独立结果审查方：1号 AI（ChatGPT）**
- **任务性质：只验证固定 23-patch 候选；测试 Agent 不得修改源码、补丁、DTS、配置或本任务书。**
- **授权边界：离线源码、构建和静态测试；不包含任何平板设备访问。**

## 0. 唯一目标

验证 23-patch ROUND135 候选能否在固定 ACK Android Common Kernel 6.18.33 上完成：

1. 精确补丁身份核验和有序应用；
2. DBY-W09 DTS 真实内核路径集成；
3. UFS Host 双 GenPD 顺序与 UFS PHY 原有 domain 的最终 DTB 核验；
4. UFS / RPMhPD / GCC / OPP 依赖的 Kconfig 解析；
5. UFS Qualcomm C 对象编译；
6. 完整 Kleaf `//common:dby_w09` Image 构建；
7. 既有 Host 回归测试。

本轮是 **build/schema/DTB integration validation only**。即使全部通过，也不能说明 PM8150 电气输入、ABL handoff、AVB/DTBO 选择、实际 UFS 枚举或实机启动已通过。

## 1. 固定输入与引用

### 固定内核

- 仓库：`aosp-mirror/kernel_common`
- ACK commit：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`
- 版本：`android17-6.18.33_r00`
- 禁止切换纯 Linux stable `v6.18.33`、移动分支 HEAD 或其他 tag。

### 冻结 17-patch base manifest

- 仓库：`hhdy/matepad11-dby-w09-agent-reports`
- 分支：`ai-parallel/stagea-port-until-boot`
- 路径：`kernel-baseline/round61/round32-stagea-series.txt`
- Git blob：`9a93b7e3a500d807533517a92b98fe244b2ea456`
- 任务前必须重新核验 Git blob 和 manifest 字节；不得从 `main` 猜路径，不得替换为别的 manifest。

### 本轮 23-patch 扩展清单

完整清单和固定 Git blob 位于：

`kernel-baseline/round135/ROUND135_23_PATCH_SERIES_MANIFEST.md`

该文件所在分支：`ai1/round130-stagea-ufs-lifecycle-integration`

要求逐个读取扩展 patch 并核验 Git blob：
- 18–21：原 ROUND130 已验收候选的字节不变副本；
- 22：新内核路径 DTS + qcom Makefile DTB 入口；
- 23：ROUND45 dual-GenPD / required-OPP driver 候选。

关键文件：
- 新 DTS：`kernel-baseline/round135/arch/arm64/boot/dts/qcom/huawei-dby-w09.dts`
- DTS patch：`kernel-baseline/round135/series/22-round135-huawei-dby-w09-real-dts.patch`
- driver patch：`kernel-baseline/round135/series/23-round135-ufs-dual-genpd-driver.patch`

## 2. 安全和禁止事项

1. 不连接平板，不使用 USB、ADB、fastboot、recovery、root、serial 或任何设备接口；不读取或写入分区。
2. 不 boot、不 flash、不生成可刷写包，不修改 boot/vbmeta/DTBO/ramdisk 分区或文件。
3. 不下载、重新提取或读取新的 HOS4.3 固件；本轮不需要固件输入。
4. 不修改 17 个冻结补丁、18–23 号补丁、候选 DTS、Kconfig、产品 config、manifest 或源码。
5. 不修改任何 AI1 / AI2 / main / protected 分支；不创建 PR、不 merge、不 cherry-pick。
6. 必须使用全新隔离临时源码树和新构建输出目录；不得污染、覆盖或清理既有工作树、构建输出、证据。
7. 不为让测试通过而放宽 schema、删负向 fixture、移除兼容检查或添加未经审核的 regulator / memory 属性。
8. 若固定输入缺失、blob / SHA 不匹配、patch 无法应用、工具链不能复现或测试失败，停止对应阶段，保存证据并报告 BLOCKED/FAIL；不得替换输入或自行修复。

## 3. 建立固定 ACK 工作树并应用 23 个补丁

### 3.1 起始树

- 建立全新目录/clone；checkout 固定 ACK commit。
- 记录仓库 remote、`git rev-parse HEAD`、`git status --short`、初始 tree。
- HEAD 必须精确等于 `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`。
- 从指定 AI2 分支读取 17-patch manifest，核验 blob 为 `9a93b7e3a500d807533517a92b98fe244b2ea456`。
- 对 17 个输入逐项核验 manifest 顺序、文件路径、Git blob、SHA-256；不得只比对文件名。

### 3.2 应用顺序

严格按以下顺序应用：
- 1–17：冻结 manifest 全部内容；
- 18：ROUND120 per-HBA async scan join；
- 19：ROUND122 UFS regulator load-first；
- 20：ROUND128 QMP UFS dual-rail V2；
- 21：ROUND126 proxy-consumer load-first；
- 22：ROUND135 real-path DTS + qcom Makefile entry；
- 23：ROUND135 SM8250 UFS dual-GenPD / required-OPP driver。

每个 patch 必须先运行 `git apply --check --verbose`，成功后运行 `git apply --verbose`，随后 `git diff --check`。记录完整命令、stdout/stderr、退出码和每个 hunk 的位置。

**重要：不得再把 “git apply 没有 offset” 当作事实。** ROUND132 的真实 `git apply --verbose` 日志显示冻结 patch 16/17 曾存在 hunk offset；ROUND130 还记录 ROUND128 V2 至少一个 hunk 有 -19 行 offset。本轮必须逐个记录实际 offset，不得将 offset 计为 0，也不得把 offset 隐藏在 GNU patch 结果里。历史记录只作为比对线索，不代表本次自动通过。

- 不允许 fuzz、reject、跳过、重排或部分应用。
- 已知历史 offset：冻结 patch 16/17（见 ROUND132 日志）；ROUND128 V2 patch（见 ROUND130 报告）。将本轮实际 offset 与对应历史证据逐项比对。
- 若出现新增的、与历史记录不一致的 offset，或任意 fuzz/reject / apply 错误，停止并报告 BLOCKED，等待 1号 AI 审查；不得尝试调整 patch 或上下文。
- 17-patch 阶段结束时，记录内容 tree；ROUND132 两棵独立树的基线 tree 记录为 `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`，本轮可将其作为对照，但必须保留实际计算值，不得强行伪造匹配。
- 记录 23-patch 完成后的完整 `git diff --stat`、最终 tree、`git status --short`、binary diff hash；确认差异只来自固定 23 个补丁。

## 4. DTS / binding / DTB 验证

### 4.1 Source-level structural assertions

验证最终合并 DTS 的：
- `/model` 和 root `compatible` 保留自本轮 board DTS；
- UFS Host compatible 是继承的 `qcom,sm8250-ufshc`；
- UFS Host `power-domains` 恰好两个，顺序严格为：
  1. `qcom,sm8250-rpmhpd` / `RPMHPD_MMCX`（index 0）；
  2. `qcom,gcc-sm8250` / `UFS_PHY_GDSC`（index 1）。
- UFS PHY `ufs_mem_phy` 仍只有原本 GCC `UFS_PHY_GDSC`，不得加 MMCX 或改变 domain。
- UFS Host 的 ACK SID mapping 仍继承 `iommus = <&apps_smmu 0xe0>, <&apps_smmu 0x4e0>`；不得因 HOS4.3 FDT 静态缺失而删去或重写。
- 本轮 board DTS 原有 UFS supplies、max-current/load 属性与 `status = "okay"` 全部保留；不得添加猜测的 PMIC 物理 VIN parent。
- qcom DTS Makefile 包含 `huawei-dby-w09.dtb`，没有重复项或其他无关修改。

### 4.2 Schema

在固定 ACK 工作树运行完整可追溯的 UFS / PHY / regulator `dt_binding_check`。至少覆盖本 series 修改的：
- `Documentation/devicetree/bindings/ufs/qcom,ufs.yaml`
- `Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml`
- `Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml`
- `Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml`

记录 dtschema、dtc、yamllint 版本及实际命令/退出码。不得通过删 fixture 或放宽 `unevaluatedProperties`、maxItems、compatible 条件等方式规避报错。

ROUND32 历史记录中 `huawei,dby-w09` 的 root compatible 有已知 undocumented binding gap。若仍触发诊断，完整记录原始输出，区分该已知问题和本轮新增问题；不得为了本轮测试擅自修改 Qualcomm 通用 binding 或伪称 schema 全部通过。

### 4.3 DTB 真实构建与反编译验证

- 用本轮最终 23-patch 工作树、最终产品 .config 和固定 manifest 对应工具链，构建实际 `huawei-dby-w09.dtb`。不得只用单独 hand-written fixture 代替。
- 可以使用 Kbuild 标准目标 `make ARCH=arm64 ... qcom/huawei-dby-w09.dtb` 或完整 `dtbs` 目标；必须记录完整命令、输出目录、工具链版本、退出码。若当前 Kleaf workspace 采用其他标准 DTB target，请把 target 解析依据和实际命令写入报告。
- 使用 `scripts/dtc/dtc -I dtb -O dts`、`fdtdump` 或等价工具反编译**刚刚生成的 DTB**，保存完整或足够定位的原始输出。
- 逐项核验 Host dual-domain phandles / cells / 顺序、PHY 原有 domain、UFS SID、UFS supplies、model/compatible、Makefile 目标名。
- 仅 DTS 源码 grep、临时单文件 dtc 或源 schema fixture 不算完成本节。

## 5. Kconfig 与实际 C / Image 构建

- 使用本轮最终 23-patch 源码和项目固定 Repo / Kleaf / Clang / Rust 工具链。
- 解析并保存最终 `.config`，检查以下依赖符号是否按目标要求启用：`SCSI_UFSHCD`、`SCSI_UFS_QCOM`、`PM_DEVFREQ`、`PM_OPP`、`PM_GENERIC_DOMAINS`、`PM_GENERIC_DOMAINS_OF`、`QCOM_GDSC`、`QCOM_RPMH`、`QCOM_COMMAND_DB`、`QCOM_RPMHPD`、`OF`、`REGULATOR`、`IOMMU_SUPPORT`、`ARM_SMMU`。记录任何模块值 / 缺失值，不能把 `=m` 当成 `=y`。
- ROUND130 产品 `.config` SHA-256 基线为 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`。由于本轮新增候选不改变配置 fragment，先比较本轮生成配置是否保持相同；如不同，报告逐项 diff，不得覆盖旧产物或强行修正。
- 对 `drivers/ufs/host/ufs-qcom.o` 执行独立 target object 编译，并保存完整命令和日志。
- 执行完整 `tools/bazel build --jobs=2 //common:dby_w09`（或记录与 ROUND130 完全一致的工具包装/参数），必须保存 BUILD_RC、最终 Image 大小/SHA-256、`.config`、System.map、vmlinux 摘要。
- 不做 boot image / DTBO / ramdisk / vbmeta / AVB packaging。

## 6. Host regression

从 ROUND130 的原始回归入口与测试源身份复现，不得自行编造或缩减测试集：
- 第一组 38/38；
- 第二组 83/83。
记录入口文件 blob、各测试源码 blob、编译命令、完整输出与退出码。若无法准确复现原测试入口，标记 BLOCKED，不得换测试集。

## 7. 静态检查与偏差报告

- `git diff --check`；
- 对 22 / 23 号 patch 和新增内核 DTS 文件运行 `scripts/checkpatch.pl --strict`，保存完整报告与退出码；
- 对 18–21 号历史 candidate 记录已有 ROUND130 checkpatch 事实，不得擅自修改或自动修复；
- 独立 SPDX 检查若缺少依赖，标记 NOT RUN / BLOCKED 并记录原始错误，不能写成 PASS；
- 报告所有 hunk offset、warnings、checks、errors，不得只写汇总 PASS；
- 不修改代码以清理 CHECK 或 schema warning。

## 8. 交付物

完成后把新文件上传到 `firmware-audit-v1` 分支的 `firmware-analysis/round135/` 目录，禁止覆盖已有 ROUND135 review / manifest / report。

至少交付：
1. `TEST_AGENT_ROUND135_FINAL_REPORT.txt` — 最终完整报告；
2. `round135-23patch-identity-and-apply.log` — 23 个 patch 的输入 SHA / blob / 顺序 / check / apply / offset / tree；
3. `round135-dt-schema-and-dtb.log` — schema、真实 DTB build、dtb 反编译和结构断言；
4. `round135-kconfig-and-kleaf-build.log` — final .config、依赖符号、object compile、Image build 与 artifacts hash；
5. `round135-host-regression.log` — Host 38/38 + 83/83 完整结果；
6. `round135-checkpatch-and-diff.log` — diff check、checkpatch、SPDX、所有 warning/check。

上传后从 `firmware-audit-v1` 回读每个文件，核验非空、内容身份和 Git blob。报告内写出上传 commit SHA、文件 Git blob 和回读结果。

## 9. 结论规则

- 所有 23 个 patch 身份正确并成功应用，offset 已完整披露且无 fuzz / reject / 未审阅的新 offset；schema、DTB compile/inspection、Kconfig、C object、full Image build、Host regressions 与静态检查均有真实日志，才能标记 `PASS — BUILD/DTB INTEGRATION ONLY`。
- 任一身份不符、patch 错误、错误 topology、C compile / DTB / build / regression 失败：`FAIL`。
- 工具、依赖、schema已知兼容 gap 或环境造成必需检查无法完成：`BLOCKED/PARTIAL`，逐项列明。
- 禁止把 source review、旧轮次 build、临时 DTS fixture 或报告计划写成实测。
- 即使 PASS，也必须注明 Phase E/F 仍受 ABL memory handoff、PM8150 物理输入和 ARC 等证据限制；Phase G NOT RUN。

## 10. 完成后停止

上传并回读全部证据后立即停止，不启动其他轮次，不更改源码或分支。把最终报告、commit/blob、PASS/FAIL/BLOCKED 结论交回 1号 AI 审查。未经新的明确指令，不得继续执行其他任务。
