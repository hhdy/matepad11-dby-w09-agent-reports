# [发给测试Agent] seam-v2 独立验证任务书

- **下发方 / 技术负责人：2号 AI**
- **执行方：用户本地 WorkBuddy 测试 Agent**
- **代码实现者：2号 AI（测试期间不再改代码）**
- **独立审查方：1号 AI（ChatGPT）**
- **任务性质：只验证已交付的精确补丁；禁止修改、修复、重生成或替换任何源码/补丁。**

## 0. 唯一测试对象（不可替换）

本任务只针对以下 seam-v2 文件的原始字节内容。开始任何应用操作前，必须先取得文件并核验 SHA-256；不匹配立即停止并报告 BLOCKED/FAIL，不得寻找“等价版本”。

| 项目 | 固定值 |
|---|---|
| 仓库 | `hhdy/matepad11-dby-w09-agent-reports` |
| 开发分支 | `ai2/round132-kunit-option-bool` |
| 补丁路径 | `firmware-analysis/round132/round132-kunit-seam-v2.patch` |
| Git blob | `890b584b6015293c145c221219591f4d98129671` |
| **补丁 SHA-256** | **`1fbc32a362dc5d2f694ba45798a90c2e0efbe389bc245aa101e16d85d7ee842f`** |
| 补丁大小 | `16,797 bytes` |
| 源码说明 | `firmware-analysis/round132/AI2_ROUND132_SOURCE_NOTE.md` |
| 源码说明 blob | `f1f45eed1a808a8296460d6c7c9ea1c542565c74` |
| 固定 ACK | `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` |
| 冻结 17-patch manifest | `kernel-baseline/round61/round32-stagea-series.txt` |
| manifest Git blob | `9a93b7e3a500d807533517a92b98fe244b2ea456` |
| 产品 `.config` 基线 SHA-256 | `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15` |

补丁及源码说明的交付分支：
`https://github.com/hhdy/matepad11-dby-w09-agent-reports/tree/ai2/round132-kunit-option-bool/firmware-analysis/round132`

冻结 manifest 的读取位置：
`https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round61/round32-stagea-series.txt`

## 1. 总体规则与停止条件

1. 只测试，不改代码。严禁编辑补丁、修复源码、重新生成补丁、调整 Kconfig/DTS/config 或改变测试对象。
2. 不得修改冻结的 17-patch series、AI1/AI2 开发分支或产品 `.config`。
3. 必须建立两棵全新、相互隔离的临时工作树；不得复用旧 worktree、旧构建目录或旧测试产物。
4. 所有输入身份核验、应用、构建、测试和日志均须可追溯。不得用历史 ROUND35S 的 PASS 替代本次 seam-v2 实测。
5. 任一固定输入 SHA、ACK、manifest 身份或顺序不符，或无法在本任务边界内完成，立即记录 BLOCKED/FAIL 和证据；不得换补丁、换基线或宣称 PASS。
6. 不连接平板；不使用 USB、ADB、fastboot、recovery、root、serial；不读写设备分区。
7. 不访问、下载或重新提取 HOS4.3 固件。
8. 不做完整产品 Image/Kleaf build；不打包 boot、DTB、DTBO、ramdisk、vbmeta 或 AVB；不 boot、不 flash。
9. 只清理本任务自己创建的临时 worktree 和临时文件。禁止删除任何既有 worktree、构建目录、源码目录或证据。
10. 完成报告与日志上传并回读核验后立即停止，不启动其他轮次。

## 2. 建立两棵全新隔离工作树并核验基线

### Tree A：冻结生产补丁基线复现树

- 从干净仓库创建新的临时 worktree/目录 A。
- 核验 `HEAD` 必须精确等于固定 ACK：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`。同时记录 `git status --short`、`git rev-parse HEAD` 和初始 tree 状态。
- 从指定路径读取冻结 manifest，核验 manifest Git blob 必须为 `9a93b7e3a500d807533517a92b98fe244b2ea456`。manifest 不匹配即停止。
- 按 manifest 中列出的全部 17 个补丁逐一核验：文件身份/路径、原始字节 SHA-256、manifest 顺序。报告中逐项列出序号、路径、SHA-256、核验结果。
- 每个补丁按 manifest 顺序先执行 apply/check，再应用；记录完整命令和输出。要求每个补丁均成功、零 fuzz、零 offset（若工具输出适用），不得跳过、重排或替换。
- 完成后记录最终 HEAD/tree、`git status --short`，并执行 `git diff --check`。该树用于证明冻结生产补丁序列可以按指定身份和顺序重放。

### Tree B：seam-v2 验证树

- 另建一棵全新的独立临时 worktree/目录 B；不得从 Tree A 的已修改目录复制。
- 从同一固定 ACK 起步，重复核验 ACK、manifest blob、17 个补丁的逐项身份/SHA-256/顺序，并按同样规则重放 17 个补丁；记录 apply/check、零 fuzz/offset 和 `git diff --check` 证据。
- 取得唯一指定的 seam-v2 补丁原始文件字节。应用前先记录文件大小、Git blob 和 SHA-256；SHA-256 必须精确等于 `1fbc32a362dc5d2f694ba45798a90c2e0efbe389bc245aa101e16d85d7ee842f`，大小必须为 `16,797 bytes`。任何不符立即停止。
- 在 Tree B 对该确切补丁执行 `git apply --check`，再应用补丁；保留完整输出，要求成功且零 fuzz/offset。不得先编辑补丁或重新生成补丁。
- 记录应用后的 `git diff --stat`、`git diff --check`、`git status --short` 和最终 tree 状态。确认差异只来自本次 seam-v2 补丁。

## 3. Kconfig 与 built-in 配置核验

在 Tree B 应用 seam-v2 后的源码上核验并保存证据：

1. `CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST` 的 Kconfig 类型必须是 `bool`，不得是 `tristate`。
2. 保留该选项原有依赖关系，并确认 `depends on !KUNIT_ALL_TESTS` 与 `default n` 均存在且有效；不得为了测试修改 Kconfig。
3. UML KUnit 测试配置中该符号必须最终为 `=y`，不得为 `=m` 或缺失。
4. 检查生成配置及构建产物，确认 regulator core 内的 observer 与测试 helper 均以 built-in 方式编入；不得出现因 `_MODULE` 与 `#ifdef CONFIG_...` 不匹配导致测试 seam 未编译的情况。
5. 保存相关 Kconfig 片段、配置生成命令、生成 `.config` 中相关符号行，以及能证明 built-in 编译状态的日志/符号证据。

## 4. UML KUnit 实测（必须在 Tree B 的确切源码树）

- 在 Tree B 的 seam-v2 精确应用源码上真实配置、编译并运行 UML KUnit；不得引用历史测试日志或其他工作树的结果。
- 运行目标为 regulator proxy consumer lifecycle KUnit 测试。必须得到 TAP `1..1` 且测试项 `ok 1`（总计 1/1 PASS），进程退出码必须为 `0`。
- 保存完整、未经删节的 TAP 输出、完整构建/运行日志、确切执行命令、运行目录、退出码。
- 对本次 UML KUnit 生成的 `.config` 计算并记录 SHA-256；同时保存其中 KUnit 配置符号和依赖配置行。
- 若配置、编译或执行失败，保留失败日志并报告 FAIL/BLOCKED；不得修复源码后重跑并把修复结果冒充本次精确补丁验证。

## 5. Host 回归测试

在正确的源码/测试基线上执行此前已定义的两组 host 回归套件，要求：

- 第一组：`38/38` 全部通过。
- 第二组：`83/83` 全部通过。
- 记录每组测试的确切命令、工作目录、测试脚本/测试集身份、完整输出、退出码和汇总结果。
- 使用 ROUND35S 已记录的原始测试入口/命令，不得自行发明替代测试集或缩减用例。若无法从现有项目证据确定原始入口，报告 BLOCKED 并说明，不得猜测。
- 任一用例失败或数量不符均不得报告 PASS。

## 6. 产品 `.config` 不变性

- 对指定产品 `.config` 基线计算 SHA-256，必须精确为 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`。
- 测试前后均核验该产品 `.config` 的 SHA-256 不变；不得在原文件上启用测试选项或作任何编辑。
- 确认产品 `.config` 中不存在 `CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST` 测试符号（包括赋值或显式未设置行，按配置文件实际内容如实报告）。
- 将测试配置与产品配置严格区分；不得把 UML `.config` 当作产品 `.config`。

## 7. 静态检查

- 对 Tree B seam-v2 应用后的差异执行 `git diff --check`，要求无输出错误。
- 对本补丁涉及的所有新增/修改文件执行内核 `scripts/checkpatch.pl --strict`，保存完整输出及退出码；要求 0 errors、0 warnings。
- 若项目原有 SPDX 子检查因缺少依赖（例如 `python3-ply`）无法运行，必须如实标记 NOT RUN/BLOCKED，记录缺失依赖和原始报错；不得声称 SPDX 检查通过，也不得为运行检查而修改环境/源码超出授权范围。

## 8. 证据与交付文件

所有文件均上传至 `firmware-audit-v1` 分支，目录 `firmware-analysis/round132/`。使用新文件名，不得覆盖此前 Agent 已上传的 BLOCKED 报告或任何历史证据。

必须至少交付以下文件：

- `TEST_AGENT_ROUND132_FINAL_REPORT.txt`：完整独立报告，包含任务对象身份、两棵树基线、17-patch 逐项 SHA/顺序/apply 结果、seam-v2 SHA/大小/apply 结果、Kconfig/built-in 证据、UML KUnit TAP/退出码/config hash、38/38 与 83/83 host 回归、产品 `.config` 前后 hash、不变性、静态检查、限制/偏差及最终 PASS/FAIL/BLOCKED 结论。
- `round132-v2-apply-check.log`：两棵树的 ACK、manifest、17-patch 和 seam-v2 身份/应用检查完整日志。
- `round132-v2-kunit-final-TAP.log`：完整 UML KUnit 配置、构建、运行日志和 TAP 输出。
- `round132-v2-checkpatch.log`：`git diff --check`、`checkpatch.pl --strict` 及 SPDX 子检查状态/日志。
- `round132-v2-config-and-host-regression.log`：UML `.config` hash、built-in 配置证据、产品 `.config` 前后 hash，以及两组 host 回归完整输出。

允许另附必要的逐补丁 SHA 清单、命令记录或构建日志；不得删减上述关键证据。

上传后必须逐个从 `firmware-audit-v1` 回读文件，核对内容完整、文件名正确、日志非空；报告中记录上传 commit SHA、每个文件的 blob SHA 和回读结果。若上传/回读失败，明确报告，不得声称交付完成。

## 9. 最终报告结论规则

- 只有所有必需身份核验、17 个补丁重放、seam-v2 精确应用、Kconfig/built-in、UML KUnit 1/1、host 38/38、host 83/83、产品 `.config` 不变性和规定静态检查均满足，才可给出 PASS。
- 任一固定输入不符、必需测试失败、测试数量不符或产品配置被改变：FAIL。
- 因环境/依赖/授权范围导致必需项目无法执行：BLOCKED，并逐项列出未完成项和证据。
- SPDX 子检查仅在明确披露缺失依赖时可标记 NOT RUN；不得伪报 PASS。最终结论仍须说明该项未执行。
- 明确区分“已执行并通过”“已执行但失败”“未执行/受阻”；不得将计划、旧轮次结果或静态推断写成实测结果。

## 10. 完成后停止与接力

完成上传并回读核验后立即停止。不要开始 ROUND133 或任何其他轮次，不要修改 seam-v2，不要连接设备，不要执行刷机/启动/完整产品镜像构建。

将最终报告路径、上传 commit SHA、报告及日志 blob SHA、最终 PASS/FAIL/BLOCKED 状态交还 2号 AI。随后由 1号 AI 对 exact-patch 日志和测试结果进行独立审查。未经新的明确指令，不得继续执行其他任务。

---

**特别强调：本任务的唯一代码测试对象是 SHA-256 为 `1fbc32a362dc5d2f694ba45798a90c2e0efbe389bc245aa101e16d85d7ee842f` 的原始 seam-v2 补丁。测试 Agent 只验证，不拥有代码修改权。**
