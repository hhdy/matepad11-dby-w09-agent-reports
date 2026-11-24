# AGENT_TASK_ROUND6.md — GKI 6.18.33 基线身份、KMI 与构建环境只读核验

> 接续 ROUND5。ROUND5 已因缺少可信 EROFS 工具链而 BLOCKED。本轮不重复尝试 EROFS，不调用 WSL，不安装工具，不编译内核；先把 GKI 6.18.33 的真实身份、发布状态、Android 平台兼容范围及 Kleaf 构建前提查清。

## 0. 任务目标

为 Huawei MatePad 11 DBY-W09（KONA / SM8250）建立可复核的 Android Common Kernel / GKI 目标基线，重点回答：

1. 用户提出的“GKI 6.18.33”究竟是 android17-6.18 活跃源码分支当前 HEAD，还是 Google 已发布/认证的 GKI release。
2. 对应 Android 平台版本是否与当前设备 Android 12 / API 31 的软件环境匹配。
3. 该分支是否包含 Kleaf / Bazel 构建定义，实际 ARM64 target、4 KB / 16 KB 变体如何命名。
4. 本机是否已有源代码同步和构建所需工具；若没有，明确阻塞点，不进行安装或绕过策略。
5. 给出后续可复现的源码 pin / manifest / 构建前提清单，但本轮不下载完整源码、不同步、不构建。

本任务是只读调研，不是编译任务。不得通过放宽安全策略、执行策略绕过、关闭安全软件或切换未授权环境解决问题。

## 1. 已知事实（不得要求用户重复提供）

设备：
- 型号 DBY-W09，Qualcomm KONA / SM8250，soc_id 356 rev 2.1。
- 实机 Android 12 / API 31；原内核 4.19.157-perf+。
- CPU 三簇最高频率 1.8048 / 2.4192 / 2.8416 GHz，ROUND1 判定为 Snapdragon 865 规格，不是 870。
- 传统 boot + 独立 ramdisk 布局；无 vendor_boot / init_boot。
- boot header v2，boot page_size 字段为 4096；该值是 boot image 页对齐参数，不能单独作为内核 CONFIG_ARM64_4K_PAGES 的证明。
- boot DTB 已识别为 Qualcomm KONA v2.1，msm-id [356, 131073]；9 个 DTBO entry 已验证。
- vendor / odm 已本地提取并确认 EROFS 签名；ROUND5 内容枚举 BLOCKED，因此模块、固件、VINTF 与供应商 KMI 需求仍 UNKNOWN。
- Xiaomi elish 包只有参考价值，没有内核源码、DTS 或 defconfig；不能代替华为 vendor 驱动资料。

边界：
- 不连接设备、不刷机、不解锁、不 root、不写分区、不挂载可写文件系统、不加载模块。
- 不上传固件、分区镜像、DTB/DTBO 二进制、模块、固件二进制、完整本地 SHA-256、设备序列号/MAC、令牌/PAT、个人目录路径。
- 不重复提取 vendor / odm，不再试图自写 EROFS 解码器。
- 不调用 wsl.exe / WSL，不修改命令安全策略。
- 不运行 Bazel / make / clang / repo sync，不进行编译或大文件下载。

## 2. 重要的上游来源与当前已知差异

以下是任务发起时核实过的官方资料入口；执行时应重新核对页面/分支当前值并记录访问日期：

1. Android Common Kernel 分支表：
   https://source.android.com/docs/core/architecture/kernel/android-common
   其中 Android 17 对应分支为 `android17-6.18`；要核实当前支持矩阵以及 Android 12 是否在支持范围内。

2. Google GKI 发布节奏：
   https://source.android.com/docs/core/architecture/kernel/gki-releases
   页面当前列明 2026 年 11 月没有当月 release；请重新核对，不要把活跃分支 HEAD 当成已认证 release。

3. Android 17 / 6.18 发布清单：
   https://source.android.com/docs/core/architecture/kernel/gki-android17-6_18-release-builds
   官方发布表当前显示 2026-09 的最后一组已列 release 为 `android17-6.18-2026-09_r7`，其版本为 6.18.32。请核实后记录；若页面更新则以最新官方数据为准。发布 artifact 表包含 `manifest_$BID.xml`，应优先使用对应 pinned manifest 保证源码复现。

4. Google Gitiles 活跃分支：
   https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/
   当前分支根目录 Makefile 核验值为 VERSION=6 / PATCHLEVEL=18 / SUBLEVEL=33，即源码版本 6.18.33。请重新读取并记录当时 HEAD / Makefile blob 信息，不要将树对象 SHA 冒充 commit SHA。

5. 该分支 BUILD.bazel：
   https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/BUILD.bazel
   当前文件引用 `//build/kernel/kleaf`，包含 ARM64 GKI 的 common_kernel 定义，以及 4 KB / 16 KB 构建变体。请核对实际目标名称与定义。

6. Kleaf / 构建说明：
   https://source.android.com/docs/setup/build/building-kernels
   https://source.android.com/docs/setup/reference/bazel-support
   注意 build-system 支持表可能滞后于新分支；不能只凭旧表未列出 android17-6.18 就断言分支无 Kleaf，也不能只凭 BUILD.bazel 存在就宣称本机可以成功构建。

7. KMI 约束：
   https://source.android.com/docs/core/architecture/kernel/stable-kmi
   https://source.android.com/docs/core/architecture/kernel/android-common
   KMI 与 Android release / kernel branch 相关；不同 GKI 分支或不同 KMI generation 不能任意混用。ROUND5 未得到华为 vendor 模块清单，因此本轮不得声称已有 vendor modules 与 6.18.33 ABI 兼容。

## 3. 第一步：核实 6.18.33 的身份

必须分开记录以下两个概念：

A. 活跃源码分支：
- 分支是否为 `android17-6.18`。
- 从 Google Gitiles 读取最新分支头信息（commit SHA 如页面提供）、Makefile 的 VERSION / PATCHLEVEL / SUBLEVEL。
- 记下访问日期、文件 URL 和证据片段。
- 确认是否为 6.18.33，不要依据分支名猜测。

B. 已发布 / 认证 GKI release：
- 从官方 android17-6.18 release builds 页面列出最近的 release date、tag、kernel version、是否 certified、manifest artifact 是否可用。
- 与分支 A 对比。
- 若最新 release 仍为 6.18.32，而活跃分支 HEAD 已为 6.18.33，则结论必须写成：
  - `SOURCE_BRANCH_HEAD=6.18.33`
  - `LATEST_LISTED_RELEASE=6.18.32`
  - `CERTIFIED_GKI_6.18.33=NOT_CONFIRMED`
  除非官方页面已出现明确的 6.18.33 release/certification 证据。
- 不得把普通源码分支、CI artifact、debug build、certified build 混为一谈。

## 4. 第二步：核实 Android 平台兼容性

- 以官方 Android Common Kernel compatibility matrix 为准，抄录 Android 17 / Android 12 对应的受支持 kernel branches。
- 当前实机 Android 12 / API 31 与 android17-6.18 的兼容状态必须单独判断。
- 若 Android 12 不在官方 android17-6.18 支持矩阵内，写明 `OFFICIAL_MATRIX_SUPPORT=NO`，并解释这代表官方测试/支持范围之外，不代表技术上绝对无法做自定义移植。
- 不要假设设备会继续运行 Android 12；也不要擅自假设会迁移到 Android 17。把“最终 userspace/platform 目标版本”标为 NEEDS_PRODUCT_DECISION。
- 不能将仅有 Linux kernel 6.18.33 的版本号等同于 Android 17 GKI release。

## 5. 第三步：核实 Kleaf / ARM64 构建定义（仅源码阅读）

通过 Google Gitiles 页面或已存在的可信本地源码副本，只读核对：
- `BUILD.bazel` 中加载的 Kleaf rule 路径。
- ARM64 GKI 目标名、dist 目标名、GKI defconfig 路径。
- 4 KB 与 16 KB 变体的目标名、配置差异入口。
- 是否启用 KMI enforcement、symbol list、ABI definition / trim 等机制。
- branch 的 `.bazelversion`、`MODULE.bazel`、`WORKSPACE`、Kleaf 版本 pin / build tools 来源（仅在官方树中确实存在时记录）。
- 如果远端文件不可读，标记 BLOCKED，不要根据其它分支猜测。

特别注意：设备 boot header 的 page_size=4096 不是 kernel page size 配置的直接证据。当前 kernel page size 记为 UNKNOWN，除非已有可信实机报告给出运行时 PAGE_SIZE。

## 6. 第四步：本机工具环境探测（只检测，不安装）

仅在 Windows PowerShell 执行只读命令：
```powershell
$names = @('git','repo','bazel','bazelisk','python','python3','clang','clang-cl','make','ninja','gcc','java')
foreach ($name in $names) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if ($cmd) { [pscustomobject]@{ Name=$name; Source=$cmd.Source; Version=($cmd.Version -as [string]) } }
  else { [pscustomobject]@{ Name=$name; Source='NOT_FOUND'; Version='' } }
}
```
- 不调用 WSL，不运行工具，不安装软件，不联网下载。
- 若 git 或 repo 不存在，则 `SOURCE_SYNC=BLOCKED_MISSING_TOOL`；不准改用脚本绕过安全策略。
- Bazel / Bazelisk / Java / Clang / Make / Ninja 缺失项要如实列出。
- 不要以 `Get-Command` 未找到某命令就推断整个系统绝对没有替代程序；只报告 PATH 可见性和明确检测过的安装路径。
- 记录可用磁盘容量仅作未来规划，不要创建大目录或下载源码。
- 本轮不执行 `repo init`、`repo sync`、`git clone`、`bazel`、`make`、`clang` 或编译。

## 7. 第五步：为后续选择建立决策表

输出一张简短对照表，至少包含：

| Candidate | Official branch/tag | Kernel version | Android platform | Release status | Build definition | Suitability |
|---|---|---|---|---|---|---|
| Active source HEAD | android17-6.18 | 核验值 | Android 17 branch | branch HEAD, not automatically certified | Kleaf target evidence | 供 6.18.33 开发用 |
| Latest listed release | 官方最新 release tag | 核验值 | Android 17 | certified / non-certified / unknown | 对应 manifest | 可复现发布基线 |
| Current device userspace | Android 12 / API 31 | 原内核 4.19.157 | Android 12 | 当前设备事实 | N/A | 与 android17-6.18 官方兼容矩阵对照 |

最终建议必须区分：
- 若坚持 6.18.33：需要以 active branch 的精确 commit 为基线，不得宣称它已经是 certified GKI。
- 若优先可复现的已发布 GKI：以官方最新 release tag 和对应 pinned manifest 为候选；不可假称版本也是 6.18.33。
- 若仍保留 Android 12 userspace：必须显式接受其不在 android17-6.18 官方兼容矩阵内这一风险，或重新评估 Android platform 目标。

不要要求用户现在选择；本轮只给出证据与建议，把最终 userspace 目标标为待产品决策。

## 8. 报告和上传

本地报告输出目录建议：
`DBY-W09_GKI_Baseline_Round6`

只允许上传脱敏文本：
- `gki_source_branch_audit.txt`
- `gki_release_candidates.csv`
- `build_environment_probe.txt`
- `round6_summary.json`

GitHub 目标目录：
`kernel-baseline/round6/`

上传前清理：
- 用户名、完整本地路径、个人目录、机器名、设备序列号/MAC；
- access token、PAT、cookie、认证信息；
- 任何固件二进制、内核 Image、boot.img、模块、签名文件或完整本地 SHA-256。

报告必须明确标出 source facts、official release facts、local environment facts 和 UNKNOWN / BLOCKED 项。不要用推测填空。

## 9. 停止条件

遇到以下情况停止相关子任务并记录：
- Gitiles / Android docs 无法读取，且无可复核官方来源；
- 工具缺失；
- 需要管理员权限、WSL、安装软件、执行策略调整或命令安全策略绕过；
- 需要下载完整内核源码、GKI 二进制或其它大文件；
- 远端 branch / release tag 与报告不一致且无法确认。

不允许为完成任务虚报源码已同步、Kleaf 已运行或内核已编译。

## 10. 完成标准

本轮完成仅意味着：
- GKI 6.18.33 branch identity 与 release status 已拆分核实；
- Android platform compatibility 风险已列明；
- Kleaf build targets / KMI hooks 有源码证据；
- 本机工具链可用性有只读记录；
- 四份脱敏报告上传成功或如实记录上传阻塞。

**本轮不得把“基线调研完成”写成“内核可编译”或“移植成功”。**
