# AI2-ROUND35 — KUnit 专用生命周期 seam 与真实 regulator-core 集成测试报告

- 任务 ID：AI2-ROUND35
- 任务归属：2号 AI 专属任务书；执行者为本地测试 Agent
- 报告分支：`firmware-audit-v1`
- 报告文件（本文件）：`firmware-analysis/round35/AI2_ROUND35_KUNIT_PROXY_LIFECYCLE_REPORT.md`
- 报告时间：2026-11-25（UTC+8）
- 固定 ACK：`aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`（`android17-6.18.33_r00`）
- Stage A 分支：`ai-parallel/stagea-port-until-boot`，HEAD `45cb9b6c6e68bc69a024c1544112cb3c5738efe6`（任务书记录 `05ec10c`，两者 17-patch series blob 均为 `9a93b7e3a500d807533517a92b98fe244b2ea456`，仅 `PROGRESS.md` 不同）
- 报告分支基线 HEAD：`df72b0fd309c4ae029b52c2dc12331477b082096`

## 总体判定：PASS — KUnit 真实集成测试执行通过

本轮在 2号 AI 明确授权的 KUnit-only seam 范围内，实现了真实 `regulator_register()` / `of_regulator_get()` / consumer vote API / `regulator_unregister()` 路径上的集成测试，并在 UML 内核上**真实编译并运行**（非仅编译）：

```text
[PASSED] proxy_kunit_lifecycle
[PASSED] regulator-proxy-consumer-lifecycle
Testing complete. Ran 1 tests: passed: 1
RC=0
```

测试是单一有序测试（single ordered test），按任务书第 4 节要求避免 bulk-revoke 的全局 one-shot 状态污染其他用例，未增加任何生产状态机 reset 接口。

---

## 1. 输入身份与工作树核验 — PASS

| 项目 | 值 | 结果 |
|---|---|---|
| 报告分支 HEAD | `df72b0fd309c4ae029b52c2dc12331477b082096` | PASS |
| Stage A 分支 HEAD | `45cb9b6c6e68bc69a024c1544112cb3c5738efe6` | PASS |
| 固定 ACK 提交 | `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` | PASS |
| 17-patch series blob（Stage A 新旧 HEAD） | `9a93b7e3a500d807533517a92b98fe244b2ea456` | PASS（一致） |
| 隔离工作区 | `/home/kerneldev/work/matepad11/round35-agent/` | PASS（独立于 ROUND124 / ROUND34） |
| 17-patch 内核树 | `/home/kerneldev/work/matepad11/round35-agent/kernel-17` | PASS |
| 该树本地快照 commit | `785f9f664d4b71009324d8ae9412ad955ed7039f` | 仅为 disposable snapshot，非 ACK 身份 |

17 个生产补丁按 series 顺序逐项核对 blob/SHA-256 并应用：

```text
RC_CHECK=0   x17
RC_APPLY=0   x17
RC_DIFFCHECK=0 x17
APPLY17_FAIL=0
FINAL_DIRTY=16
```

offset 记录与 ROUND33/34 已验收结果一致，零 fuzz：patch 16 的 `Hunk#1 offset -25`、`Hunk#2 offset -2`、`Hunk#3 offset +2`；patch 17 的 `Hunk#1 offset +1`、`Hunk#2 offset -2`。生产 17-patch 系列与 `round32-stagea-series.txt` 未被改动。

---

## 2. Seam 设计（实现前依据 ROUND34 报告第 7 节，本轮落地）— PASS

全部改动受 `CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST` 保护，该选项：

- `tristate ... if KUNIT`，`depends on KUNIT && REGULATOR_PROXY_CONSUMER && OF && OF_OVERLAY`
- `depends on !KUNIT_ALL_TESTS`（不会被 KUNIT_ALL_TESTS 自动选中）
- `default n`（产品 defconfig / Kleaf target 不会启用）
- 产品 `.config` 中该符号不存在（见第 5 节）

### 2.1 bulk revoke helper（proxy-consumer.c）

将 `regulator_proxy_consumer_remove_all()` 的实质逻辑抽为单一非 `__init` helper `regulator_proxy_consumer_revoke_all()`：

- 生产配置（测试选项关闭）：`late_initcall_sync(regulator_proxy_consumer_remove_all)` 注册保持不变，wrapper 调用同一 helper，**initcall level / 执行时机 / 单次撤销语义不变**。
- 测试配置：提供 `regulator_proxy_consumer_kunit_revoke_all()` 调用**同一 helper**，测试因此无需复制撤销逻辑。
- 附加只读诊断接口 `regulator_proxy_consumer_kunit_removed()`，仅供测试断言 one-shot 状态。

合规说明：任务书第 3.1 节明确授权"将实际撤销逻辑抽为可在运行期调用的非 `__init` helper，原 `late_initcall_sync` wrapper 必须继续调用同一个 helper"。该抽取会使 helper 从 `.init.text` 移到常规 `.text`（二进制段布局变化），但行为、调用顺序与撤销语义不变；这是授权设计的必然结果。

### 2.2 unregister 顺序观测点（core.c）

在 `regulator_unregister()` 内 `regulator_proxy_consumer_unregister(rdev)` 之后、`mutex_lock(&regulator_list_mutex)` / `WARN_ON(rdev->open_count)` / coupling / `list_del()` 之前，插入 `#ifdef CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST` 保护的 `regulator_proxy_consumer_kunit_observe_unregister(rdev)` 调用。测试配置关闭时该调用及其运行时代码完全不生成。

### 2.3 隔离测试配置的关键调整（第 3.3 节授权）

诊断发现：KUnit builtin suite 由 `init/main.c:1718` 的 `kunit_run_all_tests()`（在 `rest_init()` 中）运行，晚于所有 initcall，包括 `late_initcall_sync(regulator_proxy_consumer_remove_all)`。因此若不调整，测试开始前 `proxy_consumers_removed` 必为 1，任何 proxy 注册都返回 -EPERM（实测 `PTR_ERR=-1`）。

按任务书第 3.3 节"若 KUnit 的内建/模块组合导致真实测试无法加载或运行，必须调整为隔离的测试配置并说明，不得偷改产品配置"的授权，**仅在测试配置下**不自动注册该 initcall wrapper，改由测试显式调用同一 revoke helper。产品配置的 `late_initcall_sync` 注册与语义完全不变。

### 2.4 独立补丁

测试补丁独立于 17-patch series，不追加到 `round32-stagea-series.txt`。

- 补丁路径（本分支）：`firmware-analysis/round35/round35-kunit-seam.patch`
- SHA-256：`a6d5ad901d5495355c47327f9b4c8247dac69a8d120e58ccae6e508a1339aebb`
- 字节数：`15756`，行数：`443`
- 触及文件：`drivers/regulator/Kconfig`、`drivers/regulator/Makefile`、`drivers/regulator/core.c`、`drivers/regulator/proxy-consumer.c`、`include/linux/regulator/proxy-consumer.h`、新增 `drivers/regulator/proxy-consumer-kunit.c` 与 `drivers/regulator/kunit-proxy-consumer.dtso`
- 未触及任何 DTS/DTBO（产品 device tree）、binding、Kleaf target、产品 `.config`

---

## 3. 真实测试实现与执行 — PASS

### 3.1 测试真实性边界

| 组件 | 来源 | 是否 mock |
|---|---|---|
| `regulator_register()` / `regulator_unregister()` | pinned ACK 真实 `drivers/regulator/core.c` | 否 |
| `regulator_proxy_consumer_register()` / `regulator_proxy_consumer_unregister()` / revoke helper | ROUND33 生产 `proxy-consumer.c` | 否 |
| `of_regulator_get()` / self-target 解析 | 真实 `drivers/regulator/of_regulator.c` | 否 |
| `regulator_enable()` / `regulator_set_voltage()` / `regulator_set_load()` / `regulator_disable()` | 真实 regulator core consumer API | 否 |
| DT self-target 节点 | KUnit `of_overlay_apply_kunit()` + `kunit-proxy-consumer.dtso` | 测试专用 DT，非产品 DTS |
| provider `regulator_ops` 回调 | 测试 fake provider（记录 enable/disable/set_voltage/set_load 的次数与参数） | 是（明确标注：仅 provider 侧为 fake） |

因此这是**真实 regulator core + 真实 proxy-consumer 生产代码**的内核集成测试，不是复制核心逻辑的伪集成测试；唯一 fake 是 provider 硬件侧回调，符合任务书允许范围。

### 3.2 测试配置（隔离，非产品配置）

`kunit-r35/.kunitconfig`：

```text
CONFIG_KUNIT=y
CONFIG_OF=y
CONFIG_OF_EARLY_FLATTREE=y
CONFIG_OF_OVERLAY=y
CONFIG_REGULATOR=y
CONFIG_REGULATOR_PROXY_CONSUMER=y
CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST=y
```

生成配置中相关项：

```text
CONFIG_OF=y
CONFIG_OF_EARLY_FLATTREE=y
CONFIG_OF_OVERLAY=y
CONFIG_REGULATOR=y
CONFIG_REGULATOR_PROXY_CONSUMER=y
CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST=y
CONFIG_KUNIT=y
```

runner：`python3 tools/testing/kunit/kunit.py run --build_dir <dir> --kunitconfig <dir>/.kunitconfig --jobs 8 --timeout 120`（UML `ARCH=um`，host gcc 13.3.0）。

### 3.3 覆盖项与断言

单一有序测试 `regulator-proxy-consumer-lifecycle / proxy_kunit_lifecycle`，按顺序覆盖：

1. **注册与投票**：OF overlay 建立 child-scoped self-target 节点（节点自身 `proxy-supply` 指向自身，`qcom,proxy-consumer-enable/voltage/current`）；真实 `regulator_register()` 后 `rdev->proxy_consumer` 为有效 handle（非 ERR_PTR），且 `proxy_consumers_removed=false`。真实 provider ops 收到：`set_voltage(1800000, 1800000)`（单电压 desc 经 core 钳制后的真实值）、`set_load(100000)`、`enable`。
2. **unregister 顺序**：真实 `regulator_unregister(owner)` 触发 core.c seam；观测到 `proxy_pointer_cleared=true`（proxy back-pointer 已空）、`device_still_registered=true`（core teardown 尚未开始）、`open_count=0`、`provider.disable_count` 增加。这四点同时成立，证明"proxy teardown 先于 core teardown"的顺序。
3. **no-handle / 幂等**：`of_node=NULL` 注册（无 proxy 属性）后 `rdev->proxy_consumer=NULL`；重复调用 `regulator_proxy_consumer_unregister()`（含 NULL）不触碰 consumer API、不增加 disable 计数；unregister 的 observer 仍只调用一次。
4. **bulk revoke（最后执行）**：显式调用与 `late_initcall_sync` wrapper 共用的 `regulator_proxy_consumer_kunit_revoke_all()`；断言 `rdev->proxy_consumer=NULL`、`disable_count` 增加、`set_voltage_count`/`set_load_count` 增加、`load_uA` 归零，且电压经 core 钳制到约束范围内。

### 3.4 TAP 输出（原文见 `firmware-analysis/round35/kunit_final_TAP.log`）

```text
[23:40:31] Starting KUnit Kernel (1/1)...
[23:40:31] ====== regulator-proxy-consumer-lifecycle (1 subtest) ======
[23:40:31] [PASSED] proxy_kunit_lifecycle
[23:40:31] ======= [PASSED] regulator-proxy-consumer-lifecycle ========
[23:40:31] Testing complete. Ran 1 tests: passed: 1
[23:40:31] Elapsed time: 3.442s total, 0.000s configuring,
           3.377s building, 0.062s running
```

最终运行 RC=0。中间迭代中出现过 4 次 FAIL，均已按根因修复而非放宽掩盖：三参数 `regulator_register()` 签名、one-shot initcall 顺序、`REGULATOR_CHANGE_STATUS` 缺失、fake provider 缺 `is_enabled`。所有最终断言均为真实内核行为下的通过。

---

## 4. 静态检查 — PASS

- `git diff --check`：RC=0
- `checkpatch.pl --strict --no-signoff --ignore FILE_PATH_CHANGES`：

```text
total: 0 errors, 0 warnings, 0 checks, 415 lines checked
RC=0
```

唯一被 ignore 的类型 `FILE_PATH_CHANGES` 是新增测试文件触发的 MAINTAINERS 提示（新增文件标准提示，非代码风格问题）。环境缺少 `ply` 导致 `spdxcheck.py` 输出两条 traceback，不影响 checkpatch 统计结果。完整日志见 `firmware-analysis/round35/checkpatch_round35_clean.log`。

---

## 5. 产品配置与 host 回归 — PASS

- 产品 `.config`：`/home/kerneldev/work/matepad11/ack-6.18.33-a30/bazel-bin/common/dby_w09/.config`
  - SHA-256（构建前/后同一）：`0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`
  - size：`238410`
  - `CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST`：不存在（NOT_PRESENT）
- 未执行完整 `//common:dby_w09` Image build；未生成/上传 boot.img、DTB/DTBO、ramdisk、vbmeta、AVB/footer 或刷机包。
- host 回归复跑（Stage A 的 `run_tests.sh`，从 Git 对象 LF 原样导出）：

```text
--- test_proxy_consumer_r31 ---
COMPILE_RC=0
checks=38 failures=0
TEST_RC=0
--- test_proxy_consumer_round32 ---
COMPILE_RC=0
checks=83 failures=0
TEST_RC=0
HARNESS_RESULT: PASS
RUNTESTS_RC=0
```

说明：host harness 编译的真实 `proxy-consumer.c` 因加入 KUnit-only helper 而使源文件 SHA-256 由 `dc24fa52...` 变为 `4ded4a86...`；host 用例结果仍为 38/38 与 83/83 全通过，即 seam 对 host 测试无回归。

---

## 6. 不允许事项检查 — PASS

- 未修改 ROUND33 生产补丁语义、L5/L9 self-target 约束，未引入 cross-regulator proxy handle。
- 未修改任何产品 DTS/DTBO、内存、PMIC、电压、父级 supply、ARC 映射或 board compatible。
- 新增 DT 仅为 KUnit 测试专用 `.dtso`，不参与产品构建。
- 未构建/生成 boot.img、DTB、DTBO、ramdisk、vbmeta、AVB/footer 或刷机包。
- 未连接/操作/重启平板；未使用 ADB/fastboot/recovery/root；未读写分区；未访问 HOS4.3 固件证据。
- 未上传任何固件/镜像/私有分区数据/设备标识/密钥。

---

## 7. 限制与说明

1. 本轮只改善内核生命周期测试证据。**不据此声称板级启动条件满足或设备可启动**；Phase E/F 仍为 BLOCKED，Phase G 仍为 NOT RUN。
2. 测试在 UML（`ARCH=um`）上执行，是内核原生 KUnit 集成测试，但不是 arm64 目标板执行；provider 硬件侧为 fake（已明确标注），真实部分为 regulator core 与 proxy-consumer 生产代码。
3. 单电压 fake desc 使 core 将 `set_voltage(1800000, 3300000)` 钳制为 `1800000..1800000`；这是真实 core 行为，测试断言按实况校准。
4. 隔离测试配置下不自动注册 bulk revoke 的 `late_initcall_sync` wrapper（第 2.3 节），这是为使 KUnit executor（`rest_init()` 之后）能覆盖投票/revoke 全流程而做的配置级调整；产品配置完全不变。
5. 报告附带补丁、checkpatch 日志与 TAP 日志三份证据文件，路径见第 2.4 / 4 / 3.4 节。

## 8. 状态汇总

| 项目 | 状态 |
|---|---|
| Stage A / ACK / 17-patch 身份核验 | PASS |
| 17-patch 顺序应用（零 fuzz，已知 offset） | PASS |
| KUnit-only seam 设计与独立补丁 | PASS |
| 独立补丁 diff-check / checkpatch --strict | PASS |
| KUnit 真实编译并运行（1 suite / 1 case，非仅编译） | PASS |
| 产品 `.config` 未变、未启用测试选项、未完整构建 | PASS |
| host 回归 38/38 与 83/83 | PASS |
| 不允许事项检查 | PASS |

按任务书第 7 节，本轮报告提交后立即停止，不自动开始 ROUND36；由 2号 AI 独立审查并决定后续移植。
