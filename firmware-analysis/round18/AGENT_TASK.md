# ROUND18 — ACK 6.18.33 补丁集成、schema/Kconfig 与首次 Image 编译

**状态：已授权执行。**  
设备：Huawei MatePad 11 (2021) DBY-W09 / KONA / SM8250 v2.1 / Snapdragon 865。  
固定源码：ACK tag android17-6.18.33_r00；common commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a。  
本轮目标：使用 ROUND16 已准备好的 WSL + Repo 工作区，在独立副本中真实应用补丁、验证 UFS/QMP UFS PHY binding、验证 Kleaf/Bazel/Kconfig，并首次编译 DBY-W09 storage-first Image。  
报告唯一上传位置：firmware-audit-v1:firmware-analysis/round18/round18_patch_schema_kconfig_first_build.txt

---

## 0. ROUND16 状态更正：不重做环境部署

ROUND16 旧状态 BLOCKED_BY_HOST_SECURITY_POLICY 已被新报告正式覆盖。当前权威证据：

- 分支：firmware-audit-v1
- 文件：firmware-analysis/round16/round16_wsl_ack_workspace_deployment.txt
- 大小：20,158 bytes
- Git blob：c9516f20d3e13cb5d5ec42e41bec4c8a05b25123
- 分支尖端：99f93d2e81ccb88715bf47ed1aff167d4cd98c55
- 结论：WSL_AND_PINNED_ACK_WORKSPACE_READY

已实测完成：

- WSL 2.7.3.0 / WSL kernel 6.6.114.1-1。
- Ubuntu 24.04.5 LTS，发行版 Ubuntu-24.04，位于 D:\WSL\Ubuntu-24.04，WSL2。
- 默认 Linux 用户 kerneldev，uid 1000，非 root。
- 已有完整 Repo workspace：/home/kerneldev/work/matepad11/ack-6.18.33。
- 官方 common-android17-6.18 manifest 已同步完成：58 projects，约 41 GiB。
- common/ 已 detached 到精确 commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a，git status --short 为 0 行。
- Clang r584948c、Rust 1.91.1.p3、Bazel 8.7.0 已实测与 ROUND39 预期一致。
- 完整 manifest revisions 已记录于本地 metadata/repo-manifest-revisions.xml。

开始时只做轻量只读复核：路径存在、repo manifest -r、common HEAD/clean 状态、工具版本。不得重新部署 WSL/Ubuntu，不得 repo init、repo sync、重下载源码或工具链。不要因为旧报告或历史任务书还出现 BLOCKED 状态而重做部署。

## 1. 本轮明确授权

用户已明确授权本地 Agent 在已部署 WSL 环境中完成以下操作：

1. 创建独立、可丢弃的 ROUND18 ACK workspace 副本；原始 ROUND16 workspace 必须保持 pristine。
2. 在副本中应用本任务列出的 driver、DT binding、Kleaf BUILD/config 补丁；允许对副本中的补丁和源码作必要的最小修正。
3. 执行真实 git apply --check、git apply、git diff --check、scripts/checkpatch.pl。
4. 执行 UFS 与 QMP UFS PHY 的 dt_binding_check、dt-doc-validate、dt-validate，并用 dtc 编译/验证测试用例。
5. 集成 Kleaf target，执行 Bazel query/cquery、实际 Kconfig 解析和最终 .config 检查。
6. 编译 DBY-W09 storage-first Image-only target；失败时诊断、修复、重跑，直到成功或证明存在外部基础设施限制。
7. 上传本轮脱敏文本报告到 firmware-audit-v1。

本授权只覆盖临时源码副本中的补丁和编译，不包含平板设备操作、boot packaging 或任何分区写入。

## 2. 现有环境资源与 Gate

ROUND16 实测 WSL VM 可见内存约 7.3 GiB，Windows 宿主约 15.16 GiB。按以下规则：

- 本轮不修改 %USERPROFILE%\.wslconfig，不执行 wsl --shutdown，不改变 mirrored networking，不修改 WSL memory 参数。
- 构建前记录 free -h、nproc、df -h、可读取的 cgroup memory.max/current。
- 初次构建使用保守并发度，建议 tools/bazel build --jobs=2。
- Bazel 命令经 tee 记录时必须 set -o pipefail。
- D: 剩余空间必须保持至少 100 GiB。ROUND16 记录约 275.28 GiB；复制前重新确认。低于 100 GiB 时先停并报告，禁止删除原 workspace 或 VHDX 内容腾空间。
- 若发生明确 OOM，保存 OOM/cgroup 证据、峰值内存、Bazel 日志和失败命令，不要重复同一高负载重试。报告为何需要修改 WSL memory，等待操作者对修改 .wslconfig 的单独明确授权。本轮任务本身不授权修改它。
- kerneldev 密码字段仍为锁定状态。正常 Git、Kconfig、Bazel、编译均应以普通用户运行；不要主动执行 passwd、sudo 或安装系统包。若系统包确实缺失，记录缺失包并继续其他可执行阶段，不要自行提权。
- 若 dt-schema Python 工具缺失，可在 ROUND18 临时目录建立独立 venv，并根据固定 ACK 源码内 binding requirements 安装此轮所需 Python 工具；不得 sudo apt、不得 pip --break-system-packages、不得修改系统 Python。记录依赖文件 hash、安装版本与命令。若网络/依赖阻断，只标记 schema gate BLOCKED，仍继续 patch、Kleaf、Kconfig 和 Image 工作。

## 3. 隔离工作区

现有工作区：

/home/kerneldev/work/matepad11/ack-6.18.33

建议独立副本：

/home/kerneldev/work/matepad11/ack-6.18.33-round18

在确认原 common clean、D: 空间不少于 100 GiB 后，使用本地复制方式（cp -a 或 rsync -a）复制完整 Repo workspace，保留 .repo、项目目录、符号链接。该操作是本机复制，不是重新下载或 repo sync。目标目录已存在时不得覆盖，改用新的空目录并记录。

所有 patch、BUILD/config、Bazel output 只在 ROUND18 副本中进行。严禁修改原始 /home/kerneldev/work/matepad11/ack-6.18.33/common。

留存以下基线证据：

- 原 workspace common HEAD 与 git status --short。
- 副本 repo manifest -r 的文件及 SHA-256。
- 副本 common HEAD、git status --short、git describe --tags --always。
- Makefile VERSION/PATCHLEVEL/SUBLEVEL。
- patch 前后 git diff --stat、完整 diff SHA-256。

若原工作区已经被其他任务改动，不要 reset、clean 或覆盖；记录状态并停止使用该目录。

## 4. 固定 ACK 与工具链复核

唯一合法基线：

- tag：android17-6.18.33_r00
- annotated tag object：369fecee1ecf4c78af4889640c618cc9a19f3921
- dereferenced commit：8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

不得换成纯 Linux v6.18.33、移动 branch HEAD 或其他 ACK tag。

只复核现有工具：

- clang-r584948c，输出含 based on r584948c / clang 22.0.1。
- Rust 1.91.1.p3。
- tools/bazel version，预期 Build label 8.7.0。Kleaf wrapper 不接受 tools/bazel --version；不要误把这个 wrapper 参数错误当工具链故障。
- dtc --version，ROUND16 已安装 device-tree-compiler 1.7.0。

不要重新下载工具链或改变 manifest revisions。

## 5. 补丁集成清单与真实应用顺序

所有补丁必须先核对 Git blob SHA，再逐个执行真实 git apply --check 和 git apply。记录命令、退出码、修改文件和 SHA。禁止使用 in-memory hunk simulation 冒充应用成功。

| 顺序 | 内容 | 采用文件与 Git blob |
|---|---|---|
| 1 | ROUND36：SM8250 dual power-domain schema exception | main: `kernel-baseline/round36/0001-dt-bindings-ufs-allow-sm8250-dual-power-domains.patch.draft`；dad87ef8dfefee6141b8a7949982c007c4a03b4a |
| 2 | ROUND52-0001：VDDP/VCCQ-parent shared binding | 二号 AI 分支 `ai-parallel/stagea-port-until-boot`：`kernel-baseline/round61/patches/round52-0001-context-corrected.patch`；当前观察 blob e47219d4a944b44f5c1461689b76e77b4f0317a8。执行前必须重新核对分支 HEAD 与 blob。该补丁会整体改写 `qcom,ufs-common.yaml`，因此后续必须重新补回 ROUND36 的 minItems 修正。 |
| 3 | ROUND36 corrected range：SM8250 允许 1 或 2 个 power-domains | 二号 AI 分支：`kernel-baseline/round61/patches/round36-corrected-power-domain-range.patch`；当前观察 blob a6e8eeaf9303e428e644245749e6daec4d0e38ac。必须在 ROUND52-0001 之后应用；先真实 `git apply --check`。 |
| 4 | ROUND32 corrected clock cardinality：正确 ACK schema 上限 8 项 | 二号 AI 分支：`kernel-baseline/round61/patches/round32-corrected-sc7180-clock-names.patch`；当前观察 blob 2a038774ffac4cc0d742a52baeb1d41ce2aa1dfb。该版本已修正 hunk 计数（3 old / 4 new），但现有证据只有 exact-source context comparison；**尚无此最新 blob 真实 `git apply` 成功记录**。必须先真实 `git apply --check`，通过后才可 apply。 |
| 5 | ROUND33：UFS dual-GenPD / required-OPP driver | 二号 AI 分支：`kernel-baseline/round61/patches/round33-checkpatch-clean.patch`；f1d54e5e0379183fbdfb3ca6132c6d0fc61d4622 |
| 6 | ROUND52-0002：VDDP managed lifecycle | 二号 AI 分支：`kernel-baseline/round61/patches/round52-0002-checkpatch-clean.patch`；7e5df841b756dfef803edec486d9a5e3e753f47b |
| 7 | ROUND63-0002：QMP UFS PHY binding 的 vdda-phy-always-on | main: `kernel-baseline/round63/0002-dt-bindings-phy-qmp-ufs-vdda-phy-always-on.patch.draft`；a6668eebe293f9a35e9c08d6be4f37c4340e7ddd |
| 8 | ROUND63-0001：QMP UFS PHY always-on regulator lifecycle | main: `kernel-baseline/round63/0001-phy-qcom-qmp-ufs-preserve-vdda-phy-always-on.patch.draft`；a06b7d3fc19e0b23895b0013ab9ac322d84cdda5 |

必须从相应 GitHub ref/path 取得补丁并核对 SHA-1 Git blob 身份；不得因为文件路径相同而从错误分支读取旧版本。

### ROUND32 原始补丁已废弃；采用最新修正版候选并先做真实 apply-check

主线旧补丁 `kernel-baseline/round32/0001-dt-bindings-ufs-add-sm8250-compatible.patch.draft`（blob `efe2d932da34716c631de22d89aba19730cc7f50`）**从 ROUND18 应用序列中永久移除**，不得下载或应用。固定 ACK `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` 已在 `Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.yaml` 的 `select` 中选择 `qcom,sm8250-ufshc`；在 `qcom,ufs.yaml` 再添加该 compatible 会造成重复 schema 选择。

二号 AI 早期 clock patch blob `fade9cb2bdfd544c6736c7595af8380726edf318` 在真实 Actions Runs `45448025597` / `45447645008` 中因 hunk context/count 错误而 `git apply --check` 失败，**该旧 blob 已被后续版本取代**，不得再用。

二号 AI 当前分支最近一次观察到的状态（2026-11-25）：branch HEAD `faae6c044369c24afbdc270eb53fd2e0d31ad451`；`PROGRESS.md` blob `2a4c91b9e7a74e3021783bde3b2221d84ea63aee`。其最新 clock patch blob 为 `2a038774ffac4cc0d742a52baeb1d41ce2aa1dfb`，hunk 已改为 3 old / 4 new，且 exact-source context comparison 匹配；但截至该进度记录，**尚未有该最新 blob 的真实 hosted git apply 成功证据**。该 patch 只是本轮候选，仍须由 ROUND18 本地副本独立执行真实 apply-check。

ROUND18 必须遵守以下顺序：

1. 从当前二号 AI 分支重新读取最新 branch HEAD、`PROGRESS.md` 和表格中所列 patch 文件，核对当前 blob SHA；若分支已前进，按最新实际 blob 更新报告，不可把本段快照 SHA 当作永久不变。
2. 在固定 ACK 副本确认 `qcom,sc7180-ufshc.yaml` 已选择 SM8250，clock-names 有八个有序 const 项；ROUND32 corrected patch 只能修改该正确 schema 的 SM8250 分支，不得再次修改 `qcom,ufs.yaml` 的 compatible selector。
3. 对 ROUND32 corrected patch 单独运行真实 `git apply --check`。返回 0 后再 `git apply`、`git diff --check`；若失败，先修 hunk/context 并重复 check，不得跳过检查。
4. ROUND36/ROUND52 的顺序必须是：ROUND36 原始 patch → ROUND52-0001 shared-schema patch → ROUND36 corrected range patch（将 power-domains 设为 minItems: 1、maxItems: 2）→ ROUND32 corrected clock-names patch。原因：ROUND52-0001 会整体重写 `qcom,ufs-common.yaml`，若先应用 ROUND36 corrected range patch，该修改会被 ROUND52 覆盖。
5. ROUND36 corrected range patch `a6e8eeaf9303e428e644245749e6daec4d0e38ac` 和 ROUND32 corrected clock patch `2a038774ffac4cc0d742a52baeb1d41ce2aa1dfb` 都必须在 ROUND18 副本逐个真实 `git apply --check`、apply、diff-check；二号 AI 的 in-memory/context comparison 不是本地应用证据。
6. 用 ACK 的 dtschema 2023.9 依赖执行 dt-doc-validate / dt_binding_check 和 fixtures：SM8250 一域、二域均接受；三域拒绝；非 SM8250 二域拒绝；clock-names 7/8/9 分别拒绝/接受/拒绝。保留 strict unevaluatedProperties，不得以删除 example 或放宽 schema 获得 PASS。

二号 AI 最新进度指出：它已确认 ROUND36 的 maxItems: 2 在 dtschema 2023.9 处理后会被解释为精确两项，因此补充 minItems: 1 是必要修复；还发现 ROUND52 全文件替换会覆盖先前的 ROUND36 修复。它最新工作流已重排为上述顺序，但最新验证 run 尚待结果。ROUND18 必须独立复核，不得把待运行工作流描述为 PASS。

若 clock/schema gate 暂时无法通过，记录对应 BLOCKED，仍继续其它不依赖该 gate 的 Kleaf query、Kconfig、Image-only 构建。不得因单一 schema gate 提前停止整个 ROUND18。
### ROUND57：本轮明确不应用

ROUND57 patch blob 3656f05ad01d54452b83591b762faaa71a16f592 在二号 AI 的真实 dt-schema 流程中发现，对固定八项 clock-names.items 列表额外增加 minItems/maxItems 会触发 schema meta-schema 不兼容。因此本轮不应用 ROUND57，不得屏蔽 meta-schema 错误。

固定 ACK 的正确选中 schema 已列出八个有序 const clock names，但现有规则只有 minItems: 8，仍需用 7/8/9 项正反例验证上限。按上方 ROUND32 废弃/修正版门槛，在真实 git apply 通过后才验证精确八项约束；若 maxItems 与 ACK meta-schema 冲突，研究兼容表达。禁止重复 ROUND57 的无效限制。

### ROUND37：本轮明确排除

ROUND37 board DTS patch blob 486654c8d0b1b785190253270f5e83f796f07362 仍然只针对仓库 review-only DTS 草案，不是 ACK 内核 DTS source path；RAM handoff 和 PMIC 输入拓扑也未关闭。本轮不得把它应用到 ACK common，不编译 board DTS。

### 每个 patch 的验证要求

- 逐个核对 Git blob SHA。
- 单 patch 执行 git apply --check，再 git apply。
- 每个 patch 应用后执行 git diff --check。
- 检查实际 diff 文件/行数与预期一致。
- ROUND33、ROUND52-0002、ROUND63-0001 三个 driver patch 执行 scripts/checkpatch.pl --no-signoff --strict。
- 不得伪造 Signed-off-by，不得代任何人签署。修复本轮新增代码的实际 warning/error/check；如保留，逐项说明理由。
- 完成后保存补丁顺序、总 diff SHA-256、修改文件清单与行数统计。

## 6. UFS / QMP UFS PHY schema 验证

目标 binding：

- Documentation/devicetree/bindings/ufs/qcom,ufs.yaml
- Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.yaml（ROUND18-local SM8250 clock-names 修正版目标）
- Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml
- Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml

ACK Makefile 的 DT_SCHEMA_FILES 过滤使用冒号拆分，变量必须冒号分隔，不是空格分隔。示例：

~~~bash
DT_SCHEMA_FILES='Documentation/devicetree/bindings/ufs/qcom,ufs.yaml:Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.yaml:Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml:Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml' \
  make ARCH=arm64 dt_binding_check
~~~

保存完整 stdout/stderr 和返回码；确认日志实际选择了四个 schema 和 example，而不是只因 make exit 0 就误判成功。追加直接工具检查：

- dt-doc-validate 对四个相关 schema（qcom,ufs.yaml、qcom,sc7180-ufshc.yaml、qcom,ufs-common.yaml、QMP UFS PHY schema）直接运行。
- 对生成的所有 UFS / QMP UFS PHY example DTB 直接运行 dt-validate，并将任何 validation diagnostics 作为失败处理。
- 记录 dtc 版本和完整命令。
- 所有命令必须保留真实 exit code；不得被 Makefile 内部的 || true 隐藏。

### 6.1 必须覆盖的正反例

UFS Host：

- SM8250 + 8 clocks + 8 clock-names + 1 power-domain：接受。
- SM8250 + 8 clocks + 8 clock-names + 2 power-domains（MMCX index 0、GCC UFS_PHY_GDSC index 1）：schema 层接受。
- 7 clock-names：拒绝。
- 9 clock-names：拒绝。
- 3 power-domains：拒绝。
- 非 SM8250 Qualcomm UFS compatible 使用 2 power-domains：拒绝。
- qcom,vddp-ref-clk-supply 存在但缺 max-microamp：拒绝。
- qcom,vccq-parent-supply 存在但缺 max-microamp：拒绝。
- 只有 max-microamp、没有对应 supply phandle：按 binding 既定约束验证并记录。
- 合法 VDDP supply/load pair：接受。

QMP UFS PHY：

- 带可选 vdda-phy-always-on 的有效节点：接受。
- 不带该属性的旧式有效节点：接受。
- boolean 写成非 boolean 值：拒绝。
- 未知属性：继续由 strict schema 拒绝。

每个 fixture 保存 DTS、DTB、dtc 命令和 dt-validate 返回码。不得通过删 example 或屏蔽错误来换取 PASS。

### 6.2 必须继续处理的已知 UFS example diagnostics

二号 AI真实 schema run 已发现：

- qcom,ufs.example.dtb 报 power-domains too short。
- unevaluatedProperties 将 interrupts、iommus、phys/phy-names、resets、regulator supplies 等通用 UFS 属性误判为未评估属性。
- Makefile/example target 即使返回 0 也可能吞掉相关 diagnostics。

必须沿 schema composition、allOf、引用 common schema 的实际验证路径定位并修复，保持 SM8250 clock-names 八项约束、ROUND36 双 GenPD 和 ROUND52 supply/load 规则的设计意图；旧 ROUND32 的重复 compatible 选择不属于要保留的设计。不允许删除 unevaluatedProperties: false、全面放宽 schema、屏蔽错误、删除 example 或跳过 dt-validate。修复后重新跑正反例和直接 dt-validate。

## 7. Kleaf / Bazel / config validator

复用二号 AI已完成的 ROUND58/ROUND61 产物：

- Kleaf BUILD patch：二号 AI分支 kernel-baseline/round61/patches/round58-kleaf-target.patch；blob dc8f4b5932f6aabaeef068b2d25cf6f9fe9be0ec。
- config validator：kernel-baseline/round61/check_dby_w09_config.py；blob 5622b1e8e3dcf1c683e252e2abb1177de0b44435。
- unit tests：kernel-baseline/round61/tests/test_check_dby_w09_config.py；blob 82acac9f1602228ed9a780a98f7aadc046d55cad。
- 来源分支：ai-parallel/stagea-port-until-boot。

在 ROUND18 副本：

1. 对 Kleaf patch 真实执行 git apply --check、git apply、git diff --check。
2. 复制 validator 和 tests，记录来源 SHA。
3. 运行 Python unit tests，报告实际通过数量。
4. buildifier -mode=check（若 manifest/工作区提供），修复本轮 BUILD patch 引入的格式错误。
5. 执行 tools/bazel version、tools/bazel query //common:dby_w09、tools/bazel cquery --output=files //common:dby_w09。
6. 核实 target 采用 gki_defconfig + post_defconfig_fragments、没有 base_kernel，且为 Image-first 输出；不得臆造 DTB/DTBO/boot.img/vendor_boot/init_boot 输出。
7. 若 Kleaf API/属性不匹配，以固定 ACK workspace 的 BUILD API 为准最小修正；禁止改用 legacy build.sh 或 build.config.gki.aarch64。

## 8. 实际 Kconfig 与最终 .config

通过真实 Kleaf target 生成配置，不得把手写 fragment、ROUND31 静态依赖闭环或 synthetic test 说成最终 config PASS。

- gki_defconfig 为基础。
- storage-first fragment 必须通过 post_defconfig_fragments 注入。
- 执行 target 使 Kleaf 实际完成 defconfig + olddefconfig / 最终配置校验。
- 提取 Kleaf 生成的最终 .config，对它运行 ROUND61 config validator。
- 记录 .config SHA-256 和 validator 完整输出。
- 逐项确认 UFS、QMP PHY、SM8250 GCC、RPMhPD、ICC、SMMU、DM、EROFS 等首阶段关键驱动为 built-in =y。
- hidden Kconfig symbols 不得直接手写赋值，须验证由真实 select/depends 链解析。
- 不得添加 # nocheck 隐藏关键配置失败。
- 若关键配置缺失或成为 =m/=n，定位真实 Kconfig 依赖，修正最小输入后重新解析并复测。
- 明确区分显式 fragment 项、上游 inherited 项和由 select 自动得到的项。

## 9. 首次 Image 编译

本轮主要产物是 ACK-derived DBY-W09 storage-first Image。只编译 Image，不构建 board DTB/DTBO，不打包 boot.img：

~~~bash
set -o pipefail
tools/bazel build --jobs=2 //common:dby_w09 2>&1 | tee /path/to/round18-image-build.log
~~~

执行前确认实际 target label 和输出路径；若 ROUND58 target 需要按 pinned Kleaf API 修正，以真实 query/cquery 为准。所有 tee pipeline 必须 set -o pipefail。

构建失败时：

1. 定位第一个有因果意义的 Bazel/Kconfig/compiler 错误。
2. 判断 patch/API/config/toolchain/memory/disk/network 类别。
3. 在 ROUND18 副本最小修复。
4. 对受影响项目重跑 apply/diff/checkpatch/schema/config checks。
5. 再执行完整 Image build。
6. 记录每次失败和修复，不得把重试隐藏为一次 PASS。

成功时保存：

- 完整 Bazel 命令、exit code、开始/结束时间。
- ACK commit、manifest hash、Kleaf/Bazel/Clang/Rust 版本。
- build log 路径和 SHA-256。
- Image 精确路径、文件大小、SHA-256。
- .config、System.map、vmlinux 的路径/存在性/大小/hash（适用时）。
- git diff --stat、补丁清单与本轮 source modifications。
- WSL 内存与磁盘数据。

成功后的状态只能写 IMAGE_BUILD_PASS / STAGE_A_BUILD_READY，不代表 Stage A 已完成，更不代表设备可刷写或已成功启动。

## 10. Board DTS / DTB / first-boot gates 继续隔离

本轮可以对 UFS/QMP PHY binding examples 执行 dtc 和 dt-validate；不得把 board DTS draft 冒充真实 ACK DTS 编译输入。

以下事项保持 BLOCKED/UNKNOWN：

- ROUND37 仍只针对 review-only DTS 草案，不应用到 ACK source。
- HOS4.3 post-ABL FDT 的真实 RAM memory node/reg 或 Linux EFI-stub handoff 未知。
- 34 个 reserved-memory child 不能替代 RAM map；不得猜内存范围。
- PM8150 L5 physical input supply topology 未知；不得编造 vdd/vin/vph parent 或 dummy regulator。
- HOS4.3 ARC parent/proxy consumer 未移植；ROUND63 的 PHY 89900µA load 不是 ROUND48/51 L5/L9 临时 100mA proxy vote 的替代。
- AVB footer/vbmeta descriptors/ramdisk 内容仍按 ROUND12 BLOCKED；不得安装或调用未知来源 avbtool。
- legacy boot header v2、独立 ramdisk、DTBO/rootparam 与 ABL 的精确组合仍未完成验证。

因此本轮不执行 board dtbs_check、不编译 board DTB/DTBO、不做 boot image assembly/packaging。上述 first-boot gates 不得阻止 Image-only 编译。

## 11. 绝对禁止

- 不重新部署 WSL/Ubuntu，不改动 C: 上既有 Ubuntu。
- 不重新 repo init、repo sync、重新下载 ACK/kernel source/toolchain。
- 不修改原始 ack-6.18.33 workspace。
- 不修改 main、ack18-dby-w09-dts-draft、二号 AI专属分支或 PR #1；firmware-audit-v1 仅允许上传本轮报告。
- 不连接/操作平板，不执行 ADB/fastboot，不解锁、不 root、不刷机、不写分区、不触碰 boot/ramdisk/vbmeta。
- 不修改 .wslconfig，不修改 WSL networking/memory，不绕过 WorkBuddy/Windows 安全策略。
- 不伪造结果；不把 hosted runner 结果冒充本机 WSL 结果；不把静态 hunk/synthetic tests 冒充真实执行。

## 12. 交付报告

完成可执行阶段后，只上传一份脱敏 UTF-8 文本报告：

branch: firmware-audit-v1  
path: firmware-analysis/round18/round18_patch_schema_kconfig_first_build.txt

报告至少包含：

1. 状态表：PATCH_APPLY、DT_BINDING、KLEAF_QUERY、KCONFIG、IMAGE_BUILD 各自 PASS/FAIL/PARTIAL/BLOCKED/NOT_RUN。
2. ROUND16 新报告 blob c9516f20... 和 branch tip 99f93d2...。
3. WSL workspace/common/toolchain 复核和内存/磁盘数据。
4. 副本创建方式；证明原 workspace pristine。
5. 各 patch blob、真实 apply、diff-check、checkpatch 命令/返回码。
6. schema fixtures 的 DTS/DTB、dtc 和 dt-validate 结果，全部 example diagnostics。
7. Kleaf patch/validator/test SHA、buildifier、Bazel query/cquery。
8. final .config SHA 与关键 symbol 逐项结果。
9. Image build 命令、日志 hash、Image size/hash。
10. 全部失败/修复/重跑和未运行项目；写明第一遗留 blocker。
11. 去除 Windows 用户名、个人 profile、环境 token；禁止上传 raw firmware、boot/ramdisk/DTBO、VHDX、密钥、代理凭证或设备序列号。

二号 AI的 ai-parallel/stagea-port-until-boot 分支由它自己维护。本地 ROUND18 结果可作为交叉验证证据，但不得推送或覆盖它的代码分支。

## 13. 完成条件

本轮结束于：真实补丁集成、schema 验证、Kleaf query、实际 Kconfig/.config、首次 Image 编译结果和报告归档。

若 schema 失败但 Kconfig/Image 可以独立推进，继续执行，不得因单一 schema diagnostics 提前退出。若发生 OOM，按第 2 节停止内存相关重试，但继续低资源阶段。

本轮不要求执行设备启动。不得自动进入 Stage B DerpFest。Stage A 必须等到 ACK 6.18.33 内核在平板实际上机启动，并通过 UFS/storage/basic hardware 验收后才算完成。

**立即从 ROUND16 已存在的工作区开始；本轮不包含任何环境部署或重新 Repo sync 步骤。**

---

## ROUND18 revision 1 — ROUND32 schema ownership correction（2026-11-25）

本 revision 覆盖本任务旧版第 5 节中 ROUND32 的原始补丁条目及旧应用顺序。旧 ROUND32 blob `efe2d932da34716c631de22d89aba19730cc7f50` 已废弃；二号 AI 修正版 blob `fade9cb2bdfd544c6736c7595af8380726edf318` 也在真实 apply-check 中失败，不能原样应用。详细依据及本地重新制作、先 check 后 apply 的强制门槛见本 revision 上方专节。

本任务 revision 不改变 Stage A/Stage B 顺序、ACK pin、workspace 隔离、Image-only 范围、设备安全边界或报告目的地。二号 AI 专属分支继续由二号 AI 独立维护；ROUND18 只读取它已提交的补丁作为候选/参考，不向该分支写入任何内容。

---

## ROUND18 revision 2 — 最新 ROUND61 patch ordering / hunk correction（2026-11-25）

本 revision supersedes revision 1 关于 ROUND32 corrected candidate 必须完全由 ROUND18 重新制作的要求：二号 AI 已把 hunk count 修正为 3 old / 4 new，当前观察候选 blob 为 `2a038774ffac4cc0d742a52baeb1d41ce2aa1dfb`。它仍未获得真实 hosted apply PASS，因此 ROUND18 必须先本地真实 `git apply --check`，通过后才能 apply。旧候选 blob `fade9cb2bdfd544c6736c7595af8380726edf318` 仍然废弃。

同时新增 ROUND36 corrected power-domain range patch（blob `a6e8eeaf9303e428e644245749e6daec4d0e38ac`），必须在 ROUND52-0001 完整文件替换之后应用。修订后的准确顺序为：ROUND36 → ROUND52-0001 → ROUND36 corrected range → ROUND32 corrected clock count → ROUND33 → ROUND52-0002 → ROUND63 PHY binding → ROUND63 PHY driver。各 patch 仍需本地逐项核 SHA、真实 apply-check、apply 和 diff-check。

二号 AI 当前观察 HEAD `faae6c044369c24afbdc270eb53fd2e0d31ad451`；其最新 `PROGRESS.md` blob `2a4c91b9e7a74e3021783bde3b2221d84ea63aee` 报告：由于 ROUND52-0001 会全文件替换 UFS common schema，工作流现已重新排序；新的 UFS/manifest runs 当时仍 pending。执行时必须重读最新分支，不得把该快照以后的状态写成已知。

