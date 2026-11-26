# AI2-ROUND35R — ROUND35 补丁与测试证据一致性修复结果

- 任务 ID：AI2-ROUND35R
- 任务归属：2号 AI 专属任务书
- 执行者：本地 Agent
- 报告分支：`firmware-audit-v1`
- 报告路径：`firmware-analysis/round35r/AI2_ROUND35R_TASK_RESULT.md`
- 报告时间：2026-11-26（UTC+8）
- 固定 ACK：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Stage A 分支：`ai-parallel/stagea-port-until-boot`
- Stage A 基线 HEAD：`45cb9b6c6e68bc69a024c1544112cb3c5738efe6`
- 冻结生产补丁系列：17 个补丁；本轮未修改其内容、顺序或语义

## 总体判定：PASS

ROUND35 的证据不一致已修复。本轮从固定 ACK 新建两个全新工作树，逐项核验并按序应用 17 个冻结生产补丁；以「ACK + 17 个生产补丁已应用」为明确父基线重新生成独立的 KUnit seam 补丁；在第二个全新工作树上重新应用 17 个生产补丁与 seam 补丁，零 fuzz；在该源码树上重新编译并运行 UML KUnit，TAP 通过且退出码为 0。TAP 日志、源码树差异哈希与 seam 补丁哈希已互相对应。产品 `.config` 前后哈希一致且未启用测试选项，host 回归 38/38 与 83/83 通过。

本轮不是产品移植轮次，也未做完整产品 Image build。KUnit 通过不代表设备启动验证通过；Phase E/F 仍依赖真实 ABL FDT/EFI memory map 与 PM8150 供电拓扑证据，Phase G 未执行。

---

## 1. 固定源码身份与 17-patch 基线 — PASS

### 1.1 源码与系列清单身份

| 项目 | 值 | 结果 |
|---|---|---|
| 固定 ACK commit | `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` | PASS |
| ACK 描述 | `Merge android17-6.18 into android17-6.18-lts` | PASS |
| 本地内核裸仓库 | `/home/kerneldev/work/matepad11/ack-6.18.33-a30/.repo/projects/common.git` | PASS |
| 系列清单 | `kernel-baseline/round61/round32-stagea-series.txt` | PASS |
| 系列清单 git blob SHA-1 | `9a93b7e3a500d807533517a92b98fe244b2ea456` | PASS |
| 系列清单 SHA-256 | `36e1ab53bca5d8fb832a60644055f18ff37abbf02b135be4ce3dd4170efa2e15` | PASS |
| 系列清单字节数 / 行数 | `6599` / `81` | PASS |
| 第一干净树 | `/home/kerneldev/work/matepad11/round35r-agent/tree-a` | PASS |
| 第二干净树 | `/home/kerneldev/work/matepad11/round35r-agent/tree-b` | PASS |
| 两树基线 HEAD | `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` | PASS |

系列清单通过 GitHub API blob base64 原样导出，避免 Windows Git `core.autocrlf` 的 CRLF 污染。17 个生产补丁逐项与系列清单记录的 git blob SHA-1 和 SHA-256 比对，全部 MATCH。

### 1.2 17 个生产补丁身份

| # | 系列记录中的补丁路径 | SHA-256 | 结果 |
|---|---|---|---|
| 01 | `round36/0001-dt-bindings-ufs-allow-sm8250-dual-power-domains.patch.draft` | `9bd87c76939df51da1bbda992b4e289b462d505ffef51b76b0903c624bd81171` | MATCH |
| 02 | `round61/patches/round52-0001-context-corrected.patch` | `74ef372913a17cb4cf156586b6803d7732a34911a8db6e40ad8588af4e6127e6` | MATCH |
| 03 | `round61/patches/round36-corrected-power-domain-range.patch` | `5b3dbd2f7624ae37214bbbd7f315045a1751fede4b740ea1cc954a71d58a3764` | MATCH |
| 04 | `round61/patches/round32-corrected-sc7180-clock-names.patch` | `f1fe33f0fb8fb0e1c8254b6f0c8dd99241b99a028563efbbd6be2eb74fbc6836` | MATCH |
| 05 | `round61/patches/round33-checkpatch-clean.patch` | `e95e2ee727adcb128f0f6b720db31e3779b4b76bd53414353b15af8c6e080d65` | MATCH |
| 06 | `round61/patches/round52-0002-checkpatch-clean.patch` | `d3f9bc5294a409dd55caf17f076302f62e4250f60857091b4590a1e94cb6aff4` | MATCH |
| 07 | `round61/patches/round63-0002-qmp-ufs-phy-binding.patch` | `534412c3dba85890c47f7bb66117910ac13c5b89385d1ff735480108a095f2a0` | MATCH |
| 08 | `round61/patches/round63-0001-phy-qcom-qmp-ufs-always-on.patch` | `d33e1d405cc6c855de9a3867ec7e39a25e7bec2f6f74924cb1bbc6a86b1f9539` | MATCH |
| 09 | `round61/patches/round58-kleaf-target.patch` | `bd9f124ab9ac865dfe452e6f29faf75e0e58db8a31c9e183a9962ae6b15e8dec` | MATCH |
| 10 | `round61/patches/round31-0001-regulator-add-proxy-consumer.patch` | `38f8daf2cf247cb10c203b7f98d19dc4ff8b3b033692e73177b6b47645fdb003` | MATCH |
| 11 | `round61/patches/round31-0002-regulator-proxy-consumer-binding.patch` | `1f89f0b7c1a5b16f2a968f1459aa3687555737a2eef41ca506cfcfd9114173c6` | MATCH |
| 12 | `round61/patches/round31-0003-dby-w09-enable-proxy-consumer.patch` | `c55529184c29fe88ee8b3b0fd57a209e6a6ef6e39c7af310f9cc218214708435` | MATCH |
| 13 | `round61/patches/round32-0001-regulator-child-scoped-proxy-consumer.patch` | `9b47f5bf125924d3ca8db4018e0f3338a8b0d85311fd4749d4821d36768aa650` | MATCH |
| 14 | `round61/patches/round32-0002-regulator-child-scoped-proxy-binding.patch` | `30a1ee7123480bd1e5ffefb7ca163e749355a5edf75285ed75333f68c8923d15` | MATCH |
| 15 | `round61/patches/round32-0003-dby-w09-child-scoped-proxy-review-dts.patch` | `3f524acc4bacdbcdd3cdf6e5d2d91bd0e62d42b8e71c767f24dac77235201594` | MATCH |
| 16 | `round61/patches/round33-0001-regulator-proxy-self-target-only.patch` | `7b4858f5bf8f80e83092275afc1add586676b45ebc4f343fa9d2fcb218ec2de4` | MATCH |
| 17 | `round61/patches/round33-0002-regulator-proxy-self-target-binding.patch` | `d19fb3b6ddf43ed5c05c1ca6dc3d7a57602514fb954bb3854b5a7ee78d681d05` | MATCH |

`ALL_17_MATCH=YES`。第一棵树逐项结果：`CHECK_RC=0 x17`、`APPLY_RC=0 x17`、`DIFFCHECK_RC=0 x17`、`APPLY17_FAIL=0`。第二棵树使用 `git apply --check --verbose` / `git apply --verbose`，全部 `CHECK_RC=0`、`APPLY_RC=0`、`DIFFCHECK_RC=0`，日志中每个补丁均显示 `Applied patch ... cleanly`，无 fuzz。

已知并记录在案的 offset（仍为零 fuzz）：

- patch 16：`Hunk #1 offset -25 lines`、`Hunk #2 offset -2 lines`、`Hunk #3 offset 2 lines`
- patch 17：`Hunk #1 offset 1 line`、`Hunk #2 offset -2 lines`

应用 17 个补丁后，两棵树的 tracked diff SHA-256 均为 `3e47464fadffa8663fa9560846d42a476d69bc6106482265f05a79aa8ad89bbf`，状态均为 12 modified + 4 untracked，与既有 ROUND33/34/35 记录一致。

---

## 2. 独立 seam 补丁基线、身份与完整性 — PASS

### 2.1 明确父基线

seam 补丁不是相对 ACK，也不是相对旧 R35 工作目录，而是相对「ACK + 完整 17 个生产补丁已应用」的精确源码树。

| 项目 | 值 |
|---|---|
| seam 父提交（一次性本地提交，未推送） | `931abc6165cffaf81965dd61700b14bbc8cc52a4` |
| seam 父树 | `77e2b2b1515b3813f7538aedffe4c5a4e90edb57` |
| 父提交说明 | `ROUND35R disposable parent: 17 production patches applied` |
| 父提交工作区状态 | 干净（0 entries） |
| 导出方式 | `git diff --binary`（父提交之后仅含本轮 seam 差异） |

该父提交只为固定证据基线，不进入任何远端分支，也不替代固定 ACK 身份。

### 2.2 seam 补丁身份

| 项目 | 值 |
|---|---|
| 文件 | `firmware-analysis/round35r/round35r-kunit-seam.patch` |
| SHA-256 | `14c62ec878e701a10e6eef211704262300e2ac742286c18f1e5c7496eaeb9049` |
| 字节数 | `16740` |
| 行数 | `471` |
| `git diff --stat` | 7 files changed, 398 insertions(+), 1 deletion(-) |
| touched paths | `drivers/regulator/Kconfig`、`drivers/regulator/Makefile`、`drivers/regulator/core.c`、`drivers/regulator/kunit-proxy-consumer.dtso`（新增）、`drivers/regulator/proxy-consumer-kunit.c`（新增）、`drivers/regulator/proxy-consumer.c`、`include/linux/regulator/proxy-consumer.h` |
| `git diff --check` | RC=0 |

与旧补丁 `round35-kunit-seam.patch`（SHA-256 `a6d5ad90...`）不同，本补丁不再包含 17-patch 系列已经引入的 `REGULATOR_PROXY_CONSUMER` Kconfig/Makefile/core.c 注册与生产 unregister 调用。它只包含以下测试 seam：

1. `drivers/regulator/Kconfig`：仅新增受 `KUNIT` 约束且 `default n`、`depends on !KUNIT_ALL_TESTS` 的 `REGULATOR_PROXY_CONSUMER_KUNIT_TEST`。
2. `drivers/regulator/Makefile`：仅为测试内核模块与 DT overlay 添加构建对象。
3. `drivers/regulator/core.c`：仅在 `regulator_proxy_consumer_unregister(rdev)` 之后、core teardown 之前插入 `#ifdef CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST` 保护的 observer 调用。
4. `drivers/regulator/proxy-consumer.c`：把原 `regulator_proxy_consumer_remove_all()` 的撤销主体抽为共享 helper `regulator_proxy_consumer_revoke_all()`；生产 wrapper `late_initcall_sync(regulator_proxy_consumer_remove_all)` 在非测试配置下仍调用同一 helper；测试配置下由 `regulator_proxy_consumer_kunit_revoke_all()` 调用同一 helper，并提供只读 `regulator_proxy_consumer_kunit_removed()`。
5. `include/linux/regulator/proxy-consumer.h`：声明全部 KUnit seam 符号。
6. 新增测试源文件与 self-target DT overlay。

生产行为不变：非测试配置仍注册同一个 `late_initcall_sync` wrapper，仍调用同一撤销逻辑，撤销顺序与 one-shot 语义不变。唯一实现层差异是 helper 从 `.init.text` 移至常规 `.text`，这是 R35 任务书已授权的可运行期调用 seam 的必然结果，不改变产品配置或调用语义。

### 2.3 第二棵干净树的完整应用

应用日志见 `round35r-apply-check.log`（SHA-256 `7d1052953149b62fe5245d846d9385789198f41b3f4ed60180b7e24aafe55a78`）。

| 步骤 | 结果 |
|---|---|
| 全新 clone 并 checkout ACK | PASS，`HEAD=8ad08f75...` |
| 17 个生产补丁 `git apply --check --verbose` | 17/17 RC=0 |
| 17 个生产补丁 `git apply --verbose` | 17/17 RC=0，全部 `Applied patch ... cleanly` |
| 应用后 `git diff --check` | 17/17 RC=0 |
| 17-patch 后 tracked diff SHA-256 | `3e47464fadffa8663fa9560846d42a476d69bc6106482265f05a79aa8ad89bbf` |
| seam `git apply --check --verbose` | RC=0，7 个路径全部检查通过 |
| seam `git apply --verbose` | RC=0，7 个路径全部 `Applied patch ... cleanly` |
| seam 后 `git diff --check` | RC=0 |
| seam 后完整 diff SHA-256 | `722104f9220a4f46538ce6dc1091c53369c01a298377cfa3d89053da17eceabf` |

seam 应用后，tree-a 与 tree-b 的 7 个 touched files 逐文件 SHA-256 全部 MATCH；具体值记录在 `logs/touched_file_identity.txt`（本地工作目录证据）。这排除了「TAP 来自另一棵源码树」的可能。

---

## 3. KUnit seam 符号可追踪性 — PASS

符号审计文件：`round35r-symbol-audit.txt`，SHA-256 `d1097b4c0a2d6ff5555a9cae629c8f8f6ea7a8d7f4acbf913a3d8520505e26a7`。

| 符号 | 定义位置 | 声明位置 | 调用/引用位置 |
|---|---|---|---|
| `CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST` | `drivers/regulator/Kconfig` | Kconfig 符号 | `drivers/regulator/Makefile`、`core.c`、`proxy-consumer.c`、测试文件 |
| `regulator_proxy_consumer_revoke_all` | `drivers/regulator/proxy-consumer.c`（static helper） | 无（文件内 static） | 生产 wrapper 与 KUnit wrapper |
| `regulator_proxy_consumer_kunit_revoke_all` | `drivers/regulator/proxy-consumer.c` | `include/linux/regulator/proxy-consumer.h` | `drivers/regulator/proxy-consumer-kunit.c`（Phase 4） |
| `regulator_proxy_consumer_kunit_removed` | `drivers/regulator/proxy-consumer.c` | `include/linux/regulator/proxy-consumer.h` | `drivers/regulator/proxy-consumer-kunit.c`（Phase 1） |
| `regulator_proxy_consumer_kunit_observe_unregister` | `drivers/regulator/proxy-consumer-kunit.c` | `include/linux/regulator/proxy-consumer.h` | `drivers/regulator/core.c` 的 KUnit-only seam |

以上定义、声明、调用点均已通过源码 grep 与补丁 grep 双重记录，无缺失声明或孤立定义。

---

## 4. 干净树上的真实 KUnit 构建与运行 — PASS

### 4.1 运行身份

| 项目 | 值 |
|---|---|
| 源码树 | `/home/kerneldev/work/matepad11/round35r-agent/tree-b` |
| 源码 HEAD | `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` |
| seam 补丁 SHA-256（运行前） | `14c62ec878e701a10e6eef211704262300e2ac742286c18f1e5c7496eaeb9049` |
| 源码树完整 diff SHA-256（运行前） | `722104f9220a4f46538ce6dc1091c53369c01a298377cfa3d89053da17eceabf` |
| 构建目录（全新） | `/home/kerneldev/work/matepad11/round35r-agent/kunit-build-final` |
| KUnit 配置 | `/home/kerneldev/work/matepad11/round35r-agent/.kunitconfig` |
| 生成 `.config` SHA-256 | `66d2720df6db2173b2801ec715392a066425b8baad3e77f07d2284ad895fb224` |
| 命令 | `python3 tools/testing/kunit/kunit.py run --build_dir <build_dir> --kunitconfig <kunitconfig> --jobs 8 --timeout 120` |
| 架构 | `ARCH=um`（UML） |
| 运行退出码 | `RUN_RC=0` |
| 运行后源码 diff SHA-256 | `722104f9220a4f46538ce6dc1091c53369c01a298377cfa3d89053da17eceabf`（未变） |
| 运行后 seam 补丁 SHA-256 | `14c62ec878e701a10e6eef211704262300e2ac742286c18f1e5c7496eaeb9049`（未变） |
| TAP 日志 | `round35r-kunit-final-TAP.log`，SHA-256 `7bedf7270b48420430f4d708b24c6e05efd0c851236038eb3d7cdb2d7d211338` |

TAP 日志中的源码树、构建目录、seam 补丁哈希、运行前后 diff 哈希均在同一日志内记录，并与本报告的交付文件哈希一致。

### 4.2 TAP 关键输出

```text
[00:10:55] ====== regulator-proxy-consumer-lifecycle (1 subtest) ======
[00:10:55] [PASSED] proxy_kunit_lifecycle
[00:10:55] ======= [PASSED] regulator-proxy-consumer-lifecycle ========
[00:10:55] Testing complete. Ran 1 tests: passed: 1
[00:10:55] Elapsed time: 42.843s total, 3.232s configuring, 39.495s building, 0.080s running
RUN_RC=0
```

### 4.3 测试真实性与边界

| 组件 | 来源 | 是否 fake |
|---|---|---|
| `regulator_register()` / `regulator_unregister()` | 固定 ACK 真实 `drivers/regulator/core.c` | 否 |
| `regulator_proxy_consumer_register()` / `unregister()` / 共享撤销 helper | 17-patch 树中的 ROUND33 生产 `proxy-consumer.c` | 否 |
| `of_regulator_get()` / self-target 解析 | 真实 `drivers/regulator/of_regulator.c` | 否 |
| `regulator_enable()` / `set_voltage()` / `set_load()` / `disable()` | 真实 regulator core consumer API | 否 |
| DT self-target 节点 | KUnit `of_overlay_apply_kunit()` + 测试专用 `.dtso` | 测试专用 DT，非产品 DTS |
| provider `regulator_ops` 回调 | 测试 fake provider | 是，仅硬件侧回调 fake |

单一有序测试覆盖任务书要求的四类场景：

1. **self-target 注册与真实投票**：真实 `regulator_register()` 后 `rdev->proxy_consumer` 有效；`proxy_consumers_removed=false`；provider 观测到 `set_voltage`、`set_load(100000)`、`enable`；真实 `of_regulator_get()` 解析同一 self-target。
2. **owner unregister 顺序**：真实 `regulator_unregister()` 触发 core.c seam；观测到 proxy back-pointer 已清空、设备仍注册、`open_count=0`、provider `disable` 次数增加，证明 proxy teardown 先于 core teardown。
3. **无 handle / 幂等**：`of_node=NULL` 注册后 `proxy_consumer=NULL`；`regulator_proxy_consumer_unregister(NULL)` 与重复 unregister 不触发 consumer API；observer 只在真实 unregister 时调用一次；相关检查在 `regulator_unregister()` 前完成，避免 use-after-free。
4. **bulk revoke 清理（最后执行）**：显式调用与生产 wrapper 共享的 `regulator_proxy_consumer_kunit_revoke_all()`；断言 handle 清空、`disable` 次数增加、`load_uA` 归零、电压清理经 core 钳制在约束范围内。

未把 compile-only 写成 PASS；日志包含实际 UML 内核启动与 TAP 结果。

---

## 5. 静态检查与产品隔离 — PASS

### 5.1 静态检查

| 检查 | 结果 |
|---|---|
| `git diff --check`（seam 导出后） | RC=0 |
| `git diff --check`（第二棵树 seam 应用后） | RC=0 |
| `checkpatch.pl --strict --no-signoff --ignore FILE_PATH_CHANGES` | `total: 0 errors, 0 warnings, 0 checks, 433 lines checked`，RC=0 |
| SPDX checker 依赖 | 环境中 `python3-ply` 缺失，`scripts/spdxcheck.py` 输出两条 `ModuleNotFoundError: No module named 'ply'` traceback；已原样保留在 `round35r-checkpatch.log`，未隐去，也未 modify checker |
| checkpatch 日志 | `round35r-checkpatch.log`，SHA-256 `f483915f0bfb2fe14d075e632f6f48041f667fd9002991b703941d4b62fa2e68` |

忽略的 `FILE_PATH_CHANGES` 仅为新增测试文件触发的 MAINTAINERS 提示，不是代码风格错误。

### 5.2 产品 `.config` 隔离

| 项目 | 值 |
|---|---|
| 路径 | `/home/kerneldev/work/matepad11/ack-6.18.33-a30/bazel-bin/common/dby_w09/.config` |
| SHA-256（host 回归前） | `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15` |
| SHA-256（host 回归后） | `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15` |
| 字节数 | `238410` |
| 与既有 Stage A 参考值 | MATCH |
| `CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST` | NOT_PRESENT（前后均为 NOT_PRESENT） |
| 完整产品 Image build | 未执行 |

### 5.3 host 回归

使用当前 Stage A 分支 HEAD 的 committed host harness，按 git blob 原样导出，避免旧 clone 的 CRLF/陈旧 mock 污染：

| 文件 | git blob SHA-1 |
|---|---|
| `run_tests.sh` | `e29f8a237e1836420dfcd85b7d970cf8d9a956d8` |
| `test_proxy_consumer_r31.c` | `14515c62c48d95e86bfc6dca9c2070c81e031489` |
| `test_proxy_consumer_round32.c` | `aff9ec3c5bc65c880726431b5f23750b19339c1f` |
| `mock/mock_core.h` | `98820fc6c6439237563dad52c4129db022fb1260` |
| `mock/linux/errno.h` | `8a8e39690876ebe9ffd3b56c553c2c773c2e333f` |

编译的真实源文件 `drivers/regulator/proxy-consumer.c` SHA-256：`bcbda30ba6cd7c48251a1c6e9665707863868d615576bac869d29e12a7efe14c`。

```text
--- test_proxy_consumer_r31 ---
COMPILE_RC=0
checks=38 failures=0
RESULT: PASS
TEST_RC=0
--- test_proxy_consumer_round32 ---
COMPILE_RC=0
checks=83 failures=0
RESULT: PASS
TEST_RC=0
HARNESS_RESULT: PASS
HOST_RC=0
CONFIG_AND_HOST_RESULT=PASS
```

日志：`round35r-config-and-host-regression.log`，SHA-256 `79e0876e74f5ab8353c90fbc792ef1a5528ad53d4fa033f4eed7ca5dffbb20b7`。

---

## 6. 安全边界与停止规则 — PASS

| 禁止项 | 本轮状态 |
|---|---|
| 修改冻结的 17 个生产补丁 | 未发生；17/17 SHA-256 与系列清单一致 |
| 连接、操作、重启平板；ADB/fastboot/recovery/root；分区读写 | 未发生 |
| 刷机、临时启动、解锁、签名、AVB/footer 处理 | 未发生 |
| 修改产品 DTS/DTBO、内存布局、reserved-memory、PMIC、电压、父级 supply、ARC/VRM 映射 | 未发生；新增 DT 仅测试专用 `.dtso` |
| 修改 Kleaf 产品目标或产品 defconfig | 未发生 |
| 完整产品 Image build、boot.img、DTB/DTBO、ramdisk、vbmeta、刷机包 | 未执行、未生成、未上传 |
| 访问或上传 HOS4.3 固件证据 | 未发生 |
| 自动开始 ROUND36 或 Phase E/F/G 修改 | 未发生；本轮完成后立即停止 |

---

## 7. 交付文件与 SHA-256

| 文件 | SHA-256 | 说明 |
|---|---|---|
| `AI2_ROUND35R_TASK_RESULT.md` | 自引用，无法在文件内静态写全；见上传后 readback 回执 | 本报告 |
| `round35r-kunit-seam.patch` | `14c62ec878e701a10e6eef211704262300e2ac742286c18f1e5c7496eaeb9049` | 独立 seam 补丁 |
| `round35r-kunit-final-TAP.log` | `7bedf7270b48420430f4d708b24c6e05efd0c851236038eb3d7cdb2d7d211338` | 干净树实际 KUnit 日志 |
| `round35r-apply-check.log` | `7d1052953149b62fe5245d846d9385789198f41b3f4ed60180b7e24aafe55a78` | 第二棵树完整应用日志 |
| `round35r-checkpatch.log` | `f483915f0bfb2fe14d075e632f6f48041f667fd9002991b703941d4b62fa2e68` | 完整静态检查日志 |
| `round35r-symbol-audit.txt` | `d1097b4c0a2d6ff5555a9cae629c8f8f6ea7a8d7f4acbf913a3d8520505e26a7` | KUnit seam 符号审计 |
| `round35r-config-and-host-regression.log` | `79e0876e74f5ab8353c90fbc792ef1a5528ad53d4fa033f4eed7ca5dffbb20b7` | 产品配置与 host 回归证据 |

TAP 日志 `round35r-kunit-final-TAP.log` 对应的源码树为 `tree-b`，源码 HEAD `8ad08f75...`，完整 diff SHA-256 `722104f9220a4f46538ce6dc1091c53369c01a298377cfa3d89053da17eceabf`，所用 seam patch SHA-256 `14c62ec878e701a10e6eef211704262300e2ac742286c18f1e5c7496eaeb9049`。三者与日志内记录一致。

---

## 8. 验收条件逐项结论

| # | 验收条件 | 结果 |
|---|---|---|
| 1 | 17 个生产补丁身份与内容完全未变 | PASS |
| 2 | seam patch 明确以 17-patch-applied tree 为基线，不重复引入生产代码 | PASS |
| 3 | seam patch 包含全部实际需要的 KUnit helper 定义/声明，符号引用无缺失 | PASS |
| 4 | 第二个干净工作树可按顺序完整应用 17 个生产补丁和 seam patch，零 fuzz | PASS |
| 5 | KUnit 在刚应用的源码树上真实构建并运行，TAP 通过，退出码 0 | PASS |
| 6 | TAP 日志、源码树、seam patch 的身份哈希互相对应 | PASS |
| 7 | checkpatch/diff-check、产品配置隔离、host 回归证据完整 | PASS |
| 8 | 未触碰任何禁止事项 | PASS |

**最终判定：PASS。**

按任务书第 7 节，ROUND35R 完成后立即停止，不自动开始 ROUND36 或 Phase E/F 修改。KUnit 结果仅覆盖内核原生 regulator 生命周期 seam，不构成设备启动证据。
