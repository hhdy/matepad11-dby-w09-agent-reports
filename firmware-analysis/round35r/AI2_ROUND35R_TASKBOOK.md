# AI2-ROUND35R — ROUND35 补丁与测试证据一致性修复任务书

- 任务归属：**2号 AI 专属任务书**
- 执行者：本地 Agent
- 目标：修复 ROUND35 报告、补丁、测试工作树之间的证据不一致；本轮不是产品移植轮次。
- 固定 ACK：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Stage A 基线分支：`ai-parallel/stagea-port-until-boot`
- Stage A 基线 HEAD：`45cb9b6c6e68bc69a024c1544112cb3c5738efe6`
- 冻结生产补丁系列：17 个补丁；不得修改其内容、顺序或语义。
- ROUND35 当前报告：`firmware-analysis/round35/AI2_ROUND35_KUNIT_PROXY_LIFECYCLE_REPORT.md`
- ROUND35 当前补丁：`firmware-analysis/round35/round35-kunit-seam.patch`

## 1. 2号 AI 已发现的阻断问题

当前 `round35-kunit-seam.patch` 实际只有 5 个 diff 文件：

1. `drivers/regulator/Kconfig`
2. `drivers/regulator/Makefile`
3. `drivers/regulator/core.c`
4. `drivers/regulator/proxy-consumer-kunit.c`
5. `drivers/regulator/kunit-proxy-consumer.dtso`

但报告称它还修改了 `drivers/regulator/proxy-consumer.c`，并修改了 `include/linux/regulator/proxy-consumer.h`；实际补丁中没有这两个文件。测试代码却调用 `regulator_proxy_consumer_kunit_revoke_all()` 和 `regulator_proxy_consumer_kunit_removed()`。因此当前仓库证据不能证明测试日志由所提交补丁生成。

另外，当前补丁的 Kconfig/Makefile/core.c diff 看起来可能混入了生产 17-patch 系列本身的变更。必须明确补丁基线，不能把相对 ACK 的生产代码差异冒充为独立 KUnit seam。

## 2. 本轮唯一目标

建立可复现的、独立于 17 个生产补丁的 ROUND35 KUnit 测试补丁，并证明最终 TAP 日志确实由该补丁在指定源码树上生成。

## 3. 必须执行的核验与修复

### 3.1 固定源码身份与基线

- 从固定 ACK `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` 创建干净工作树。
- 严格按既有 series 顺序应用冻结的 17 个生产补丁，逐个记录文件名、SHA-256、`git apply --check` 和 `git apply` 退出码。
- 应用后记录 `git rev-parse HEAD`（若以补丁方式应用则记录基线 commit 与完整 `git diff` 身份）、`git status --short`、17-patch series blob SHA-256。
- 不得以之前残留的 `round35-agent` 或 `kunit-r35` 工作目录作为唯一证据；必须新建干净目录，避免旧对象或旧构建产物污染。

### 3.2 重新生成真正独立的 seam 补丁

- 以“ACK + 完整 17 个生产补丁已应用”的源码树作为 seam 补丁的明确父基线。
- 从该基线单独实施 KUnit-only seam；导出的 seam patch 只能包含本轮测试 seam 所需差异，不得重复包含 17 个生产补丁已经引入的代码。
- 报告声称修改的 `proxy-consumer.c`、`proxy-consumer.h` 若确实需要，必须出现在实际 diff 中；若不需要，则必须修改报告和测试代码，解释真实实现位置，禁止仅靠文字声称。
- `regulator_proxy_consumer_kunit_revoke_all()` 与 `regulator_proxy_consumer_kunit_removed()` 的定义、声明、调用点必须完整可追踪；对所有 KUnit seam 符号执行源码搜索并把结果写入报告。
- 导出的 patch 必须用 `git diff --binary` 或等效方式从该精确基线生成；记录 patch 文件 SHA-256、字节数、行数、`git diff --stat` 和全部 touched paths。
- 在第二个全新工作树中，先应用 17 个生产补丁，再应用该 seam patch；必须 `git apply --check` 与 `git apply` 全部成功，零 fuzz；记录完整输出。

### 3.3 在刚刚干净应用的源码树中重新运行 KUnit

- 必须使用刚刚 3.2 节验证通过的源码树和同一份 seam patch，不能使用别的工作目录或先前构建缓存。
- 重新执行 UML `ARCH=um` KUnit 构建和运行；保留完整原始 TAP/runner 日志、命令行、退出码、内核构建目录、运行目录。
- 测试必须真实执行 pinned ACK regulator core 与 ROUND33 生产 proxy-consumer 代码；provider ops 可使用 fake provider，但必须明确边界。
- 至少验证 self-target 注册/真实投票、owner unregister 顺序、无 handle/幂等、bulk revoke 清理。不得把 compile-only 写成 PASS。
- 运行结束后记录构建源码树 `git diff --binary` 的 SHA-256、源码 HEAD/补丁哈希，证明运行的源码与提交的 seam patch 完全一致。

### 3.4 静态与产品隔离检查

- `git diff --check`、`checkpatch.pl --strict`；若 SPDX checker 缺依赖，单独说明，不得把 traceback 隐去。
- 重新核对产品 `.config` 前后 SHA-256 完全一致，且 `CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST` 不存在/未启用。
- 重新运行现有 host 回归，要求 38/38 与 83/83 通过；若测试树变化导致不能运行，明确报告，不得伪报。
- 不执行完整产品 Image build；不生成 boot.img、DTB/DTBO、ramdisk、vbmeta、AVB/footer 或刷机包。

## 4. 严格安全边界

- 不连接、操作、重启平板；不使用 ADB/fastboot/recovery/root；不读写任何分区。
- 不刷机、不临时启动、不解锁、不签名、不处理 AVB/footer。
- 不修改产品 DTS/DTBO、内存布局、reserved-memory、PMIC、电压、父级 supply、ARC/VRM 映射、Kleaf 产品目标或产品 defconfig。
- 不访问或上传 HOS4.3 固件证据；不恢复此前暂停的固件证据上传。
- 不修改冻结的 17 个生产补丁。

## 5. 交付文件

在 `firmware-analysis/round35r/` 提交：

- `AI2_ROUND35R_TASK_RESULT.md`：完整结果报告，包含基线、命令、退出码、源码身份、补丁身份、限制。
- `round35r-kunit-seam.patch`：相对“17 个生产补丁已应用”的干净基线生成的独立 seam patch。
- `round35r-kunit-final-TAP.log`：本轮从干净树实际运行的完整 KUnit 日志。
- `round35r-apply-check.log`：第二个干净树上应用 17 patches + seam patch 的完整日志。
- `round35r-checkpatch.log`：完整静态检查日志。
- `round35r-symbol-audit.txt`：KUnit seam 所有定义/声明/引用的 grep 结果。
- `round35r-config-and-host-regression.log`：产品配置哈希与 host 回归证据。

报告必须给出上述文件各自 SHA-256，并说明 TAP 日志对应的源码树与 seam patch SHA-256。

## 6. 验收条件

以下条件必须全部满足才可标记 PASS：

1. 17 个生产补丁身份与内容完全未变。
2. seam patch 明确以 17-patch-applied tree 为基线，不重复引入生产代码。
3. seam patch 包含全部实际需要的 KUnit helper 定义/声明，且符号引用无缺失。
4. 第二个干净工作树可按顺序完整应用 17 个生产补丁和 seam patch，零 fuzz。
5. KUnit 在这份刚刚干净应用的源码树上真实构建并运行，TAP 测试通过，退出码为 0。
6. TAP 日志、源码树、seam patch 的身份哈希互相对应。
7. checkpatch/diff-check、产品配置隔离、host 回归证据完整。
8. 未触碰任何禁止事项。

任一条件不能满足：报告 `BLOCKED` 或 `PARTIAL`，准确说明原因，不得写 PASS，不得伪造/复用旧 TAP 日志。

## 7. 停止规则

- 本轮仅完成 ROUND35R 后立即停止，不得自动开始 ROUND36 或 Phase E/F 修改。
- 由 2号 AI 独立审查报告、补丁和日志后决定下一步。
- 不得把本轮 KUnit 测试通过表述为设备启动验证通过；Phase E/F 仍然依赖真实 ABL FDT/EFI memory map 与 PM8150 供电拓扑证据，Phase G 不得执行。