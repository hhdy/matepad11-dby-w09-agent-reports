# DBY-W09 — GKI 6.18.33 上游基线核验（ChatGPT 独立研究）

核验日期：2026-11-24  
设备目标：Huawei MatePad 11 DBY-W09 / Qualcomm KONA / SM8250  
范围：Google Android Common Kernel 官方文档、Gitiles 当前分支与 BUILD.bazel；不涉及本地编译。

## 1. 结论先行

“GKI 6.18.33”目前应准确描述为：

- **活跃源码分支 HEAD：** `android17-6.18`，Makefile 报告 VERSION=6、PATCHLEVEL=18、SUBLEVEL=33，即 Linux 6.18.33。
- **官方已发布 GKI：** Android 17 的公开 release 页面列出的 2026-09 发布系列为 6.18.32；最新检索到的 respin 行为 `android17-6.18-2026-09_r10`（2026-10-26）。GKI release cadence 页面明确列出 2026 年 11 月无发布。
- 因此，**6.18.33 是当前上游开发分支版本，但不能称为已发布/认证的 GKI 6.18.33。** 本轮未找到官方发布页上明确的 6.18.33 release/certified artifact。
- 更重要的是，Google 官方兼容矩阵中 Android 12 仅支持 `android12-5.10`；`android17-6.18` 对应 Android 17。将 6.18.33 用于 DBY-W09 当前 Android 12 / API 31 用户空间，不属于 Google 官方支持/测试组合。

这并不等于技术上绝对不能做自定义移植，但意味着不能把它描述为受官方支持的 GKI 组合，且 userspace / HAL / vendor 侧兼容工作很可能远大于单纯替换内核。

## 2. 活跃源码分支的版本与精确来源

Google Gitiles 当前分支页面：
- Branch: `refs/heads/android17-6.18`
- Observed commit: `76bdb627cab87dfa1d901810e22ee7fae6d3dc89`
- Gitiles 页面显示提交时间：2026-11-21（提交作者时间 2026-11-18）。
- Makefile blob: `cb847d1580d9ba96e4fd9ed724950587ddfb98c7`
- Makefile 字段：`VERSION = 6`、`PATCHLEVEL = 18`、`SUBLEVEL = 33`。

来源：
- [android17-6.18 分支 HEAD](https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18)
- [该分支 Makefile](https://android.1.googlesource.com/kernel/common/+/refs/heads/android17-6.18/Makefile)

注意：Gitiles 提交 SHA 与 Makefile blob SHA 是不同对象，不可混用。上面两个 SHA 已分别标注。

## 3. 官方 GKI release 与分支 HEAD 不是同一概念

官方 Android 17 / 6.18 release 页面：
- [android17-6.18 release builds](https://source.android.com/docs/core/architecture/kernel/gki-android17-6_18-release-builds)
- 2026-09 发布系列版本字段为 6.18.32。
- 公开索引检索到 `android17-6.18-2026-09_r10`，日期 2026-10-26。
- [GKI release cadence](https://source.android.com/docs/core/architecture/kernel/gki-releases) 显示 2026 年 11 月为 “No release this month”。

因此建议区分以下状态：

| 标识 | 官方证据 | 状态 |
|---|---|---|
| `android17-6.18` branch HEAD | Gitiles HEAD + Makefile | SOURCE_BRANCH_HEAD=6.18.33 |
| `android17-6.18-2026-09` release family | 官方 release page | RELEASE_KERNEL_VERSION=6.18.32 |
| `android17-6.18-2026-09_r10` | 官方 release page 索引 | 2026-10-26 的已列 respin |
| GKI 6.18.33 certified release | 未见官方 release entry | NOT_CONFIRMED / 不得声称已发布 |

官方 release 页面说明其 artifact table 对 certified build 单独列出 certified GKI artifact；不要把普通 kernel source branch 或普通 CI 输出当成认证 GKI。要锁定可复现的正式发布构建，应使用该 release 对应的 `manifest_$BID.xml`，而不是只记一个移动中的 branch 名。

## 4. Android 平台兼容矩阵：当前最大的目标风险

Google 官方 Android Common Kernel compatibility matrix：
[Android common kernels](https://source.android.com/docs/core/architecture/kernel/android-common)

当前表格列出的组合中：
- Android 12 (2021) → `android12-5.10`
- Android 17 (2026) → `android17-6.18`，以及官方表中其它跨版本兼容的较早 GKI 分支。
- Android 12 表格没有列出 `android17-6.18`。

这意味着 DBY-W09 当前实机 Android 12 / API 31 与 `android17-6.18` 不构成官方支持组合。不能把“内核能编译”或“设备可能启动”理解为 CTS/VTS/GKI 官方兼容。

产品路线要明确分成：
1. **保留 Android 12 userspace：** 官方受支持的 GKI 分支方向是 `android12-5.10`，不是 6.18.33。
2. **坚持 GKI 6.18.33：** 应按 Android 17 平台的方向规划，需要处理 Android 17 userspace、HAL、vendor interface、boot image / ramdisk 及设备适配；不能只是把 6.18.33 内核塞入现有 Android 12 系统。
3. **只追求 Linux 6.18.33：** 那是 Linux kernel 自定义移植路线，不能直接称为 Android 17 GKI 认证移植。

最终 Android userspace 目标目前仍为 NEEDS_PRODUCT_DECISION；本报告不替用户擅自选择。

## 5. Kleaf / ARM64 / KMI 源码证据

Google Gitiles 中 `android17-6.18` 分支的 `BUILD.bazel`：
- blob: `e890348c545693c4e599db504f9d4355e0a897dc`
- 明确加载 `//build/kernel/kleaf:common_kernels.bzl` 的 `common_kernel` 规则，分支不是缺少 Kleaf 的 legacy build.sh-only tree。
- GKI ARM64 target 声明为 `common_kernel(name = "kernel_aarch64")`。
- 架构：`arch = "arm64"`。
- 配置入口：`arch/arm64/configs/gki_defconfig`。
- GKI target 声明 `kmi_enforced = True`。
- KMI base symbol list：`gki/aarch64/symbols/base`。
- `trim_nonlisted_kmi = True`。
- 同文件定义 `kernel_aarch64_16k`，并显式设置 `page_size = "16k"`。
- BUILD 文件还定义 `kernel_aarch64` / `kernel_dist` aliases。Kleaf 常规 Common Kernel dist target 按官方文档为 `//common:kernel_aarch64_dist`；16KB target 族为 `kernel_aarch64_16k_dist`。

来源：
- [android17-6.18 BUILD.bazel](https://android.1.googlesource.com/kernel/common/+/refs/heads/android17-6.18/BUILD.bazel)
- [Android 官方 Build kernels 文档](https://source.android.com/docs/setup/build/building-kernels)
- [Kleaf common kernel target API](https://android.git.googlesource.com/kernel/build/+/a600a8cdf4ca3c3ed7afc9a9e5f21bc6854c567a/kleaf/docs/api_reference/common_kernels.md)

补充：Google 的通用 Build kernels 文档给出的 ARM64 GKI distribution command 是：
`tools/bazel run //common:kernel_aarch64_dist`。
该命令是未来构建说明，不表示本机已经具备工具或已成功编译。

## 6. KMI 对 DBY-W09 旧 vendor 模块的影响

Google 官方 stable KMI 文档说明：
- KMI 稳定性只针对同一 LTS 与 Android kernel branch/version（例如 `android16-6.12`），不能跨 GKI kernel branch 随意混用。
- GKI 与 vendor modules 要像一起构建的一样工作；仅使用 KMI symbol list 中的符号。
- 官方推荐使用对应 branch manifest 描述的 hermetic LLVM/toolchain、Bazel/Kleaf 构建环境。

来源：[Maintain a stable kernel module interface](https://source.android.com/docs/core/architecture/kernel/stable-kmi)

对 DBY-W09 的直接含义：
- 旧内核为 `4.19.157-perf+`，现有 vendor / odm 内容仍因 ROUND5 缺少可信 EROFS reader 而 BLOCKED。
- 目前没有真实 `.ko` 列表、vermagic、depends、符号需求、VINTF 或 Huawei vendor source。
- 因而不能宣称旧 4.19 模块可直接装入 GKI 6.18.33；需要先取得源码或模块证据，再决定重编、移植、替代或剔除。
- 仅有 KONA / SM8250 SoC 共性不代表 board-level display、touch、regulator、GPIO、panel、PMIC、thermal、camera 等驱动可以通用。

## 7. 4 KB / 16 KB 不能仅由 boot header page_size 推断

ROUND1 报告中的 boot image header page_size=4096 是 Android boot image layout 的页对齐字段，不等价于内核配置中的 `CONFIG_ARM64_4K_PAGES`，也不能单独证明设备运行时 PAGE_SIZE。

当前 BUILD.bazel 里同时有默认 ARM64 GKI target 与显式 page_size=16k target。DBY-W09 的内核 page size 仍记为 UNKNOWN，下一步应从可信的旧 kernel config / runtime evidence / vendor build config 中确认，之后再固定 4KB 还是 16KB。不要在证据不足时构建或选择 16KB 变体。

## 8. 对项目路线的建议（不替用户做最终平台选择）

现阶段最重要的不是立刻 sync / build，而是确认目标到底是哪一种：
- A. Android 12 保持不变 + 内核升级：应先重新评估 GKI 6.18.33 是否为合适目标，因为官方兼容矩阵不支持该组合。
- B. Android 17 + GKI 6.18.33：在软件栈目标上与官方分支匹配，但属于整套系统移植，当前旧 boot layout / vendor HAL / EROFS vendor data / Huawei board driver 资料都仍是重大未知。
- C. 纯 Linux 6.18.33：应使用 Linux 主线/合适发行版 kernel 配置作为另一条研究线，不用 GKI 认证术语混淆。

在作出目标选择前，可以继续不依赖用户本机的工作：阅读 android17-6.18 公共 DTS/Qualcomm 驱动、比对 SM8250 上游支持情况、研究旧 boot header 兼容要求、追踪官方 release 与 branch manifest。上述工作由 ChatGPT 直接完成，不应转给本地 Agent。

## 9. 当前明确的未知 / 阻塞

| 项目 | 状态 | 解决方式 |
|---|---|---|
| Huawei vendor / odm 文件目录、模块、firmware、VINTF | BLOCKED | 可信 EROFS reader 在用户本机可用后，由本地 Agent 做只读枚举 |
| GKI 6.18.33 本机源码同步 | NOT RUN | 本地环境探测与后续明确授权后再决定；不可越过命令安全策略 |
| 本机 Kleaf/Bazel 构建 | NOT RUN | 不代表构建失败；尚未执行 |
| DBY-W09 runtime PAGE_SIZE / CONFIG_ARM64_4K_PAGES | UNKNOWN | 需要可信运行时或内核配置证据 |
| Android 12 vs Android 17 最终 userspace 目标 | NEEDS_PRODUCT_DECISION | 用户确认项目目标，不由 Agent 推测 |
| Bootloader 对 boot header v3/v4 / vendor_boot 的接受能力 | UNKNOWN | 需后续基于现有资料静态研究；不应实机写入测试 |

## 10. 执行边界

本报告由 ChatGPT 依据公开官方文档和 Google Gitiles 独立完成。没有连接平板、下载源码树或内核镜像、安装软件、执行 Kleaf、调用 WSL、刷机或写分区。ROUND5 的 EROFS BLOCKED 状态保持不变。
