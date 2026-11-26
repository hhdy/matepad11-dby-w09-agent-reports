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
- 在同一最终工作树、相同 `O=` / 工具链 / schema 版本下，额外运行完整 `dtbs_check`（例如 `make ARCH=arm64 ... dtbs_check`）。若必须全量构建 DTB，保留完整日志；不得用单文件 `dtc` 代替 `dtbs_check`。
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
3. `round135-dt-schema-and-dtb.log` — schema、dtbs_check、真实 DTB build、dtb 反编译和结构断言；
4. `round135-kconfig-and-kleaf-build.log` — final .config、依赖符号、object compile、Image build 与 artifacts hash；
5. `round135-host-regression.log` — Host 38/38 + 83/83 完整结果；
6. `round135-checkpatch-and-diff.log` — diff check、checkpatch、SPDX、所有 warning/check。

上传后从 `firmware-audit-v1` 回读每个文件，核验非空、内容身份和 Git blob。报告内写出上传 commit SHA、文件 Git blob 和回读结果。

## 9. 结论规则

- 所有 23 个 patch 身份正确并成功应用，offset 已完整披露且无 fuzz / reject / 未审阅的新 offset；schema、dtbs_check、DTB compile/inspection、Kconfig、C object、full Image build、Host regressions 与静态检查均有真实日志，才能标记 `PASS — BUILD/DTB INTEGRATION ONLY`。
- 任一身份不符、patch 错误、错误 topology、C compile / DTB / build / regression 失败：`FAIL`。
- 工具、依赖、schema已知兼容 gap 或环境造成必需检查无法完成：`BLOCKED/PARTIAL`，逐项列明。
- 禁止把 source review、旧轮次 build、临时 DTS fixture 或报告计划写成实测。
- 即使 PASS，也必须注明 Phase E/F 仍受 ABL memory handoff、PM8150 物理输入和 ARC 等证据限制；Phase G NOT RUN。

## 10. 完成后停止

上传并回读全部证据后立即停止，不启动其他轮次，不更改源码或分支。把最终报告、commit/blob、PASS/FAIL/BLOCKED 结论交回 1号 AI 审查。未经新的明确指令，不得继续执行其他任务。


---

## Revision 1 — mandatory rerun after patch-22 remediation (2026-11-26)

**This addendum supersedes the original patch-22 / DTS file identities above.** The previous run correctly blocked at patch 22 because the Makefile hunk context used spaces rather than the literal TAB in the fixed ACK file. Do not use the old patch-22 blob `d303439a9fde864ea765f59ef0888ada3f20468c` or old DTS blob `f51c5691d2955909149ba8f76d0b99dcf671e36f`.

### Current authoritative candidate identities

- Updated 23-patch manifest blob: `ffcb225b4a28974350bd1cc8588fdb95df9372d0`
- Updated DTS source blob: `58293f7a62a50f8109886c92ce4b9cd14d7980e2`
- Corrected patch 22 blob: `ea15a051d75cb0c9b8319fff30f0c7cf6bb7ed6f`
- Patch 23 unchanged blob: `2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5`
- Frozen 17-patch manifest remains blob: `9a93b7e3a500d807533517a92b98fe244b2ea456`
- Exact ACK qcom Makefile blob remains: `296688f7cb26550f75bce65826f234bc24110356`

Re-fetch the manifest and verify every blob/SHA before execution. The corrected patch 22 has literal TAB characters in the six Makefile context rows and the new DTB target row. Do not normalize tabs to spaces.

The updated DTS synchronizes with the latest reviewed main DTS while retaining the extra dual-domain Host property. It must contain:
- `vdda-phy-always-on;`;
- no `vdda-phy-max-microamp` or `vdda-pll-max-microamp` properties;
- accurate comment that included `sm8250.dtsi` supplies the bootloader-filled zero-size `/memory` placeholder;
- 37 HOS4.3 reserved-memory children;
- UFS Host domains MMCX index 0 then GCC UFS_PHY_GDSC index 1;
- no guessed RAM addresses, PMIC physical input parents or synthetic regulators.

### Rerun procedure

1. Use a **new isolated clean source tree and new output directory**. Do not resume or mutate the preserved first-run tree under `round135-agent/a30`; retain it as historical evidence.
2. Re-verify exact ACK commit and all 23 patch identities.
3. Re-apply patches 1–21 in immutable manifest order with the required per-patch `git apply --check --verbose`, `git apply --verbose`, and `git diff --check`. Report all offsets; known historical offsets must match the prior logs. The corrected 17-patch content tree must again equal `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`.
4. Apply corrected patch 22, then patch 23. Do not proceed on any error, fuzz, reject or unreviewed offset. Do not use `--ignore-whitespace`, `--3way`, reduced context, manual edits or patch regeneration.
5. If both patches apply, proceed with all original taskbook sections §4–§7: source assertions; the four binding schemas; real `huawei-dby-w09.dtb` build; full `dtbs_check`; decompile of the newly built DTB; final .config and all 14 symbols; `ufs-qcom.o`; full `//common:dby_w09` Image build; exact 38/38 and 83/83 Host regressions; diff/checkpatch/SPDX logs.
6. Do not treat an old ROUND18/ROUND130 build, the prior 21-patch tree, or the previous Agent's historical regression results as ROUND135 R1 results. Re-run what the original taskbook requires against the complete corrected 23-patch tree.
7. Preserve all prior ROUND135 report/log files. Upload this rerun as new, non-overwriting files under `firmware-analysis/round135/r1/` on `firmware-audit-v1` (final report plus apply, schema/DTB, Kconfig/build, regressions, and checkpatch logs). Read back every uploaded file and record commit/blob identities.
8. Stop after upload and readback. No device connection, ADB/fastboot/recovery/serial, firmware extraction, boot/flash, partition read/write, packaging or branch merge.

The first ROUND135 report remains historically BLOCKED. The rerun can be marked PASS only under original §9's full criteria and only after 1号 AI independently reviews its raw logs. If the corrected patch still fails, stop and report the exact failure; do not repair it locally.


---

## Revision 2 — dual-tree identity / expected-tree establishment and controlled-offset protocol (2026-11-26)

**This revision supersedes the original patch-22/patch-23 input identity in §1 and R1 addendum.** The first Agent run remains historical BLOCKED. The R1 patch22 fix is preserved, and the series has since been corrected to remove a duplicate driver patch. Do not execute R1 using its old patch23 file or old identity.

### R2 roles

- 下发方 / 技术负责人 / 源码候选负责人：**1号 AI（ChatGPT）**
- 执行方：**用户本地 WorkBuddy 测试 Agent**
- 独立核验方：**2号 AI**
- 最终复核和决定是否下发后续完整测试：**1号 AI**

2号 AI is an independent reviewer, not the local Agent executor. The Agent must not ask 2号 AI to perform local commands or modify code.

### R2 fixed identities

- ACK repo/ref: `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`
- ACK root tree: `790a68ae6d4f4ac51ab2d88977b6fd5c031473b7`
- Frozen 17 manifest: `ai-parallel/stagea-port-until-boot:kernel-baseline/round61/round32-stagea-series.txt`
- Frozen manifest blob: `9a93b7e3a500d807533517a92b98fe244b2ea456`
- Frozen 17-patch post-series content tree, pre-established by ROUND132 two-tree replay: `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`
- ROUND135 23-patch manifest: this branch, `kernel-baseline/round135/ROUND135_23_PATCH_SERIES_MANIFEST.md`, blob `6268dd363c08f549e2fd092364adafc65bce93e9`
- Updated board DTS source blob: `58293f7a62a50f8109886c92ce4b9cd14d7980e2`
- Patch 22 (board DTS file only): `ab0108364c835d87ac35ca670347d9d0001a821d`
- Patch 23 (qcom Makefile DTB target only): `ceb72ed206d97beb2c2fa8558cb120ee186cb685`
- Frozen patch 5 already contains the ROUND45 UFS dual-GenPD / required-OPP driver implementation: blob `f1d54e5e0379183fbdfb3ca6132c6d0fc61d4622`. **Do not add or apply the former duplicate driver patch** `2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5`; that separate file has been removed from the series.
- Patch 23's new path is `kernel-baseline/round135/series/23-round135-huawei-dby-w09-dtb-makefile.patch`. It must not be confused with the removed former driver patch.

Re-fetch the manifest on the specified branch and check every blob / byte size / SHA-256 for all 23 entries before applying. The fixed ACK Makefile blob for the exact TAB-sensitive hunk remains `296688f7cb26550f75bce65826f234bc24110356`.

### Why R2 has two stages

The exact full 23-patch final Git Tree SHA has not yet been independently established. The 17-patch SHA `77e2b2b1515b3813f7538aedffe4c5a4e90edb57` is only the frozen 17-patch intermediate tree. **It must never be copied or relabelled as the 23-patch expected tree.**

Therefore R2 is deliberately limited to independently establishing the completed 23-patch tree identity. It is not yet authorization to run schema, DTB, Kconfig, compile, Image build or regressions. After R2 upload, 2号 AI independently verifies both trees and raw logs; 1号 AI then records the verified full 23-patch expected Tree SHA in a follow-on taskbook revision before any downstream validation begins.

### R2-A — create two truly independent clean trees

Create **two separate Git repositories / working copies** from the exact fixed ACK source, named Tree A and Tree B. They must not share:
- a Git index;
- an object database via alternates or shared object store;
- a linked-worktree common repository;
- mutable source files or build/output directories.

A new independent clone with no hardlinks (for example, a local clone using `--no-hardlinks`) is acceptable if the starting HEAD is exactly the pinned ACK and each clone has its own `.git` object directory. Do not merely run two sequential applies in one worktree or use two linked worktrees sharing one Git repository.

For each tree, before applying anything, record:
- `git rev-parse HEAD` = exact fixed ACK commit;
- `git rev-parse HEAD^{tree}` = `790a68ae6d4f4ac51ab2d88977b6fd5c031473b7`;
- `git status --porcelain=v1` empty;
- `git rev-parse --git-dir` and `git rev-parse --git-common-dir`, demonstrating the two trees do not share a common Git directory;
- initial tree SHA and source/manifest identity records.

Do not reuse or mutate the preserved original ROUND135 first-run tree under `round135-agent/a30`, nor any previous ROUND130 / ROUND18 build workspace. Do not recreate WSL, repo init, repo sync, install packages or download a new compiler. Use the already available pinned local ACK source as the source to make two new independent local clones.

### R2-B — apply exactly 23 patches in both trees

In **each** tree, apply the 23 entries in the exact order in the updated manifest:
1–17 frozen series; 18 ROUND120; 19 ROUND122; 20 ROUND128 V2; 21 ROUND126; 22 DBY-W09 board DTS file; 23 qcom Makefile DTB target.

For every single patch in both trees:
1. Record source Git blob, byte size and SHA-256 against the manifest.
2. Run `git apply --check --verbose`; save complete stdout/stderr and exit code.
3. If and only if it returns 0, run the actual `git apply --verbose`; save complete stdout/stderr and exit code.
4. Run `git diff --check`; save complete output and exit code.
5. Capture and enumerate every hunk offset emitted by both primary commands. No summary counter may replace the per-hunk table.

No fuzz, rejects, partial apply, skip, reorder, manual edit, context reduction, `--ignore-whitespace`, `--unidiff-zero`, `--3way`, or fallback applier. Any identity mismatch, failed check/apply, reject, context relaxation, or unexplained file causes immediate stop in that tree; preserve raw logs and report BLOCKED/FAIL. Never “fix” an input inside a test tree.

### R2-C — explicit controlled-offset rule

Use the project policy file `kernel-baseline/round132/ROUND132_OFFSET_ACCEPTANCE_POLICY_1AI.md` (blob `6712f686da9940937ed87eab2f4b27d44cb29626`) as the normative rule. The following requirements are mandatory:

- A nonzero hunk offset is **not automatically a failure**, but it must be reported accurately for each patch/hunk in both Tree A and Tree B.
- Both `git apply --check` and the actual `git apply` must return 0. There must be no failed hunk, reject, skip, partial application, fuzz, ignored whitespace, context relaxation or 3-way repair.
- The same offset pattern must reproduce in Tree A and Tree B. Any new nonzero offset not already present in the historical evidence must be individually called out for explicit AI1/AI2 review; it is not self-accepted merely because both tools returned 0.
- Historical known offsets expected to recur are:
  - patch 16: H1 `-25`, H2 `-2`, H3 `+2`;
  - patch 17: H1 `+1`, H2 `-2`;
  - patch 20 / ROUND128 V2: H3 `-19` (confirm the actual current patch/manifest position; do not shift its identity or mislabel its patch index).
- Patches with no emitted offset must be reported as “no offset line emitted by the primary applier”, not inferred from a separate GNU patch diagnostic.
- Any secondary tool output (for example GNU `patch --dry-run`) must be separately labelled and never merged into the primary `git apply` offset table.
- Run and report clean `git diff --check` in both trees.

The offset rule does **not** authorize choosing a resulting-tree SHA after seeing arbitrary results and calling that the expected value. R2 only establishes a candidate expected full-series tree, which 2号 AI must independently verify before 1号 AI pins it as the expected SHA for later testing.

### R2-D — expected tree SHA outputs and stopping gate

At the end of patch 17 in each tree:
- calculate the full content tree with all patch changes included in a temporary index or staged index;
- require Tree A's 17-stage tree and Tree B's 17-stage tree to equal the predeclared `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`;
- record the exact commands, raw output, and index/worktree restoration state.

After patch 23 in each tree:
- calculate the **full 23-patch resulting Git Tree SHA** from the complete resulting content (include all modified and untracked files; do not use plain `git write-tree` on an unstaged index and mistake the unchanged HEAD tree for the resulting tree);
- record `git diff --stat`, `git status --short`, `git diff --check`, total changed paths, and the final content tree SHA;
- Tree A and Tree B final 23-patch Tree SHAs must be exactly equal.

The full expected 23-patch SHA is intentionally **not hard-coded yet** because a trustworthy value has not been established. Do not invent one, use the 17-patch SHA, or copy the SHA from only one tree. R2 must deliver the same candidate 23-patch tree SHA from both independent trees.

**R2 stop condition:** upload the preflight logs/report and read them back from GitHub; then stop. Do not run dt_binding_check, dtbs_check, board DTB build, DTB decompile, Kconfig, UFS object compile, Kleaf/Image build, Host regressions, checkpatch or SPDX in R2. These stages will be authorized in a later taskbook only after 2号 AI independently validates the exact 23-patch result-tree SHA and 1号 AI pins that SHA before execution.

### R2 deliverables

Upload new, non-overwriting files to `firmware-audit-v1/firmware-analysis/round135/r2-preflight/`:
1. `ROUND135_R2_PREFLIGHT_FINAL_REPORT.txt` — Tree A / Tree B outcome, full candidate tree SHA, exact blockers, executor statement.
2. `round135-r2-tree-a-identity-apply.log` — Tree A exact identity, per-patch check/apply/diff logs, offsets, intermediate tree17 and final tree23.
3. `round135-r2-tree-b-identity-apply.log` — same for independent Tree B.
4. `round135-r2-tree-equivalence-and-offsets.log` — side-by-side per-patch/per-hunk offsets; Tree A/B initial, 17-stage and 23-stage SHA; diff-check and tree equality assertions.
5. `round135-r2-upload-readback.log` — uploaded commit, Git blob, nonempty readback and content identity for every delivered file.

Preserve the first-run and R1 historical reports/logs. Upload no kernel binaries or firmware.

### Safety / branch boundaries

- No tablet, USB, ADB, fastboot, recovery, serial, root, boot, flash or partition access.
- No firmware read, download or extraction.
- No patch/source/DTS/config modification by Agent; no patch repair.
- No changes to main, AI2 branch, protected DTS branch or PR #1; no cherry-pick/merge/PR.
- Do not overwrite any previous ROUND135 file.
- R2 stops after upload and readback. Wait for 2号 AI independent verification and 1号 AI follow-up authorization.
