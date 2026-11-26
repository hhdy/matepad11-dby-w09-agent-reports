# AI2-ROUND34 — 真实 regulator-core 生命周期测试可行性审计报告

- 任务 ID：AI2-ROUND34
- 任务归属：2号 AI 专属任务书；执行者为本地测试 Agent
- 报告分支：`firmware-audit-v1`
- 报告文件（本文件）：`firmware-analysis/round34/AI2_ROUND34_KERNEL_NATIVE_LIFECYCLE_TEST_REPORT.md`
- 审计时间：2026-11-25（UTC+8）
- 固定 ACK：`aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`（`android17-6.18.33_r00`）
- Stage A 分支：`ai-parallel/stagea-port-until-boot`
- Stage A HEAD（本轮）：`05ec10c35e6b39881f2faae3e60d19c45de2ba75`
- 报告分支 HEAD（本轮基线）：`6e59b32d6f16eb568d03f3c4e5e4b61f1acb39a8`

## 总体判定：BLOCKED — 未提交 KUnit 测试改动

**结论：在“不修改生产代码语义、不复制/模拟 regulator-core 关键逻辑”的约束下，无法建立满足任务书第 2 节全部最低覆盖项的内核原生 KUnit 集成测试。**

因此本轮按任务书第 2 节与第 6 节要求停止：不提交伪集成测试，不修改 17 个已验收补丁，不修改 `proxy-consumer.c` 生产行为，不修改 `regulator core` 生产行为，不触发完整 Image build，不自动进入 ROUND35。

已完成的实证工作：固定 ACK 与 17-patch 身份核验、真实 17-patch 树重建、KUnit/regulator 设施审计、真实 `regulator_unregister()` 顺序核对、现有 host 回归 38/38 与 83/83 复跑。

---

## 1. 输入身份与工作树核验 — PASS

| 项目 | 值 | 结果 |
|---|---|---|
| 报告分支 HEAD | `6e59b32d6f16eb568d03f3c4e5e4b61f1acb39a8` | PASS |
| Stage A 分支 HEAD | `05ec10c35e6b39881f2faae3e60d19c45de2ba75` | PASS |
| ACK 固定提交 | `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` | PASS |
| 17-patch series | `kernel-baseline/round61/round32-stagea-series.txt`（Stage A HEAD 版本，patch 1–17） | PASS |
| 隔离工作区 | `/home/kerneldev/work/matepad11/round34-agent/`（独立于 ROUND124 与 ROUND33 工作区） | PASS |
| 17-patch 内核树 | `/home/kerneldev/work/matepad11/round34-agent/kernel-17` | PASS |

说明：`kernel-17` 是从 ACK `8ad08f75` 的归档快照建立的一次性 git 树，本地初始提交 `b1fbc098c47205be0bcf701aa4b24cd2761cb29d` 只是本 Agent 的 disposable snapshot commit，**不是** ACK 提交身份；ACK 身份由归档来源与逐补丁 blob/SHA-256 校验共同固定。

关键命令与返回值：

```bash
git rev-parse origin/firmware-audit-v1                     # -> 6e59b32d6f16eb568d03f3c4e5e4b61f1acb39a8, RC=0
git rev-parse origin/ai-parallel/stagea-port-until-boot    # -> 05ec10c35e6b39881f2faae3e60d19c45de2ba75, RC=0
bash /mnt/d/workbuddy/2026-11-25-22-04-11/setup_round34.sh # -> DONE fail=0, RC=0
```

17 个补丁全部按 series 顺序从 Stage A HEAD 的 Git 对象导出，并逐项核对 Git blob SHA 与 SHA-256：`17/17 PASS`。应用结果：

```text
RC_CHECK=0   x17
RC_APPLY=0   x17
RC_DIFFCHECK=0 x17
APPLY17_FAIL=0
FINAL_DIRTY=16
```

offset 记录（与 ROUND33 已验收记录一致，零 fuzz）：

```text
patch 16: Hunk #1 offset -25, Hunk #2 offset -2, Hunk #3 offset +2
patch 17: Hunk #1 offset +1,  Hunk #2 offset -2
```

17-patch 树中 `drivers/regulator/proxy-consumer.c` SHA-256：`dc24fa52ec12d2bdedf97696b894ac1446b6ba8f23cb6525bcde7597237fbf9c`。

---

## 2. ACK 中 KUnit / regulator 测试设施审计 — PASS（审计完成）

| 审计项 | 源码证据 | 结论 |
|---|---|---|
| KUnit 框架存在 | `lib/kunit/Kconfig:5` `menuconfig KUNIT`；`lib/kunit/` 含 `test.c`、`device.c`、`of.h` 等 | PASS：框架可用 |
| KUnit 自动运行点 | `lib/kunit/test.c:1049` `late_initcall(kunit_init);` | 与 ROUND33 proxy retry 同属 `late_initcall`，早于 `late_initcall_sync` |
| regulator 子系统 KUnit 接线 | `drivers/regulator/Kconfig`、`drivers/regulator/Makefile` 中 `grep KUNIT` = NONE | BLOCKED：无测试专用 Kconfig/Makefile 接线 |
| regulator KUnit 测试文件 | `drivers/regulator/*test*`、`*kunit*` = NONE | BLOCKED：pinned ACK 无现成 regulator KUnit 测试 |
| test regulator provider | `drivers/regulator/` 无 KUnit provider；仅有 `dummy.c`、`fixed.c` 等非 KUnit provider | BLOCKED：无现成可复用的 KUnit 原生 provider |
| KUnit OF overlay helper | `include/kunit/of.h:25` `of_overlay_fdt_apply_kunit()`，`include/kunit/of.h:112` `of_overlay_apply_kunit()` | PASS：DT/self-target 构造在设施层面可行 |
| KUnit device helper | `include/kunit/device.h:47` `kunit_device_register()` | PASS：可创建测试设备 |
| 产品 `.config` 中 KUnit | `CONFIG_KUNIT=m`、`CONFIG_KUNIT_TEST=m`、`KUNIT_ALL_TESTS` 未设置 | 产品配置为模块式 KUnit；测试配置须另建，不改产品 `.config` |
| 产品 `.config` 中 proxy | `CONFIG_REGULATOR_PROXY_CONSUMER=y` | PASS：真实生产实现参与构建 |

产品 `.config` 来源：`/home/kerneldev/work/matepad11/ack-6.18.33-a30/bazel-bin/common/dby_w09/.config`，size `238410`，SHA-256 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`。本轮未修改它。

---

## 3. 真实执行路径与顺序证据 — PASS（源码级）

`drivers/regulator/core.c:6043-6069` 的真实 `regulator_unregister()` 顺序如下：

```c
6043 void regulator_unregister(struct regulator_dev *rdev)
6048         if (rdev->supply) { ... regulator_put(rdev->supply); }
6054         flush_work(&rdev->disable_work.work);
6056         regulator_proxy_consumer_unregister(rdev);
6058         mutex_lock(&regulator_list_mutex);
6060         WARN_ON(rdev->open_count);
6061         regulator_remove_coupling(rdev);
6062         unset_regulator_supplies(rdev);
6063         list_del(&rdev->list);
6065         device_unregister(&rdev->dev);
6067         mutex_unlock(&regulator_list_mutex);
```

即 ROUND33 的生产语义是：`proxy vote/handle` 清理发生在 core 的 open-count 警告、coupling 清理、list 删除与 device_unregister **之前**。本轮只核对源码顺序，没有把 mock 结果表述为内核原生测试结果。

`drivers/regulator/proxy-consumer.c` 的关键真实实现：

- `proxy_consumer_apply_votes()`：`proxy-consumer.c:125`，真实调用 `regulator_set_voltage()` / `regulator_set_load()` / `regulator_enable()`。
- `proxy_consumer_validate_self_target()`：`proxy-consumer.c:197`，通过 `of_parse_phandle(..., "proxy-supply", 0)` 验证 self-target。
- `regulator_proxy_consumer_register()`：`proxy-consumer.c:241-357`，真实调用 `of_regulator_get()` 或 `regulator_get()`；`-EPROBE_DEFER` 进入 deferred 列表。
- `regulator_proxy_consumer_remove()`：`proxy-consumer.c:360-409`，真实调用 `regulator_disable()`、`regulator_set_load(...,0)`、`regulator_set_voltage(...,0,INT_MAX)`、`regulator_put()`。
- `regulator_proxy_consumer_unregister()`：`proxy-consumer.c:422-435`，由 `regulator_unregister()` 在 core teardown 前调用。
- `regulator_proxy_consumer_retry_deferred()`：`proxy-consumer.c:446`，`late_initcall(...)` 于 `proxy-consumer.c:486`。
- `regulator_proxy_consumer_remove_all()`：`proxy-consumer.c:492`，`late_initcall_sync(...)` 于 `proxy-consumer.c:510`。

真实查找路径：`of_regulator_get()` → `_of_regulator_get()`（`drivers/regulator/of_regulator.c:686`）→ `of_regulator_dev_lookup()` → `of_get_regulator()` / `of_find_regulator_by_node()`；legacy 路径走 `_regulator_get()`（`drivers/regulator/core.c:2331`）→ `regulator_dev_lookup()`。

---

## 4. 最低覆盖项逐项可行性判定 — BLOCKED

| 任务书第 2 节要求 | 真实代码路径是否可达 | 判定与阻塞原因 |
|---|---|---|
| 实际注册 proxy owner regulator 与 self-target proxy-supply | 理论可达：KUnit OF overlay + 真实 `regulator_register()` + `of_regulator_get()` | PARTIAL：ACK 无现成 regulator KUnit provider，需新增测试专用 provider/overlay；本身不阻塞，但下列项目阻塞 |
| handle 获取、enable、`regulator_set_load()` vote | 真实 API 可达（`proxy-consumer.c:125,181,320-341`） | PARTIAL：可测，但不足以构成完整任务验收 |
| `late_initcall_sync` 等价撤销路径 | `regulator_proxy_consumer_remove_all()` 为 `static int __init`（`proxy-consumer.c:492`），`late_initcall_sync` 于 `:510`；KUnit 自动运行点为 `late_initcall`（`lib/kunit/test.c:1049`），模块式 KUnit 更晚运行 | **BLOCKED**：测试无法在不改生产代码的前提下安全调用该函数；`.init.text` 在启动后被释放，直接按 initcall 表调用等价于释放后使用 |
| owner unregister 时先撤销 vote/handle，再进入 core open-count/list teardown | 顺序证据见 `core.c:6056` → `:6060-6065` | **BLOCKED**：断言“先后”需要在 `regulator_unregister()` 内部设置观测点；现有 pinned ACK 无 KUnit static stub/tracepoint；加 hook 属于生产代码改动 |
| deferred consumer 未获取 handle 时注销且不触碰 regulator API | 代码路径在 `proxy-consumer.c:368-377`；host mock 已覆盖 | PARTIAL：真实 core 下构造 deferred 还需 DT/provider 测试设施，且仍受上述两点阻塞 |
| 重复 teardown 幂等、失败路径不泄漏 | `proxy-consumer.c:422-435`、`360-409`；host mock 已覆盖 | PARTIAL：同上，无法形成真实内核原生集成测试 |

**关键判定：至少两项最低覆盖项必须在生产代码加入测试 seam 才能真实验证。任务书第 3 节明确规定“如测试 seam 必须改动生产代码，先停止并在报告中提出设计，不要自行实施”。因此本轮停止，不提交 KUnit 测试 patch。**

如果只提交其余可测部分，则无法覆盖 `late_initcall_sync` 与 unregister 顺序，会形成“看起来像集成测试、实际是黑盒 + mock 补洞”的伪集成测试，违反任务书第 2 节末段，因此不提交。

---

## 5. 现有 host 回归 — PASS（无回归）

使用 Stage A HEAD 的 `kernel-baseline/round61/tests/run_tests.sh`（从 Git 对象以 LF 原样导出），在 17-patch 树上复跑：

```bash
bash run_tests.sh <kernel-17> <tests-dir>
```

结果：

```text
source sha256: dc24fa52ec12d2bdedf97696b894ac1446b6ba8f23cb6525bcde7597237fbf9c
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

这些是 **host mock** 测试；它们继续执行的是编译进可执行文件的真实 `proxy-consumer.c` 源码，但 `regulator_*` API 由 mock 提供，**不是** regulator core 内核原生集成测试。

---

## 6. 产品配置与构建边界 — PASS

- 产品 `.config` SHA-256（构建前/后同一文件）：`0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`。
- 本轮未新增/修改任何 Kconfig、Makefile、defconfig、Kleaf target 或产品 `.config`。
- 未触发 `tools/bazel build //common:dby_w09`；未生成/上传 Image、vmlinux、System.map、DTB、DTBO、boot.img、vbmeta 或 AVB 产物。
- 未连接平板；未使用 ADB/fastboot/recovery/root；未读写分区；未访问 HOS4.3 固件证据。

---

## 7. 建议的后续设计（需 2号 AI 批准，本轮未实施）

若 2号 AI 决定准许最小测试 seam，建议如下设计；全部改动应受 `CONFIG_KUNIT` 保护，且不得改变 `CONFIG_KUNIT=n` 时的生产语义：

1. `drivers/regulator/proxy-consumer.c`
   - 将 `regulator_proxy_consumer_remove_all()` 的实质逻辑抽成非 `__init` 的静态 helper，例如 `regulator_proxy_consumer_revoke_all()`。
   - `late_initcall_sync(regulator_proxy_consumer_remove_all)` 继续调用该 helper，生产调用顺序与语义不变。
   - 增加 `#ifdef CONFIG_KUNIT` 的测试专用导出包装，使 KUnit 测试能调用同一 helper，而不是复制逻辑。

2. `drivers/regulator/core.c`
   - 在 `regulator_unregister()` 的 `regulator_proxy_consumer_unregister(rdev)` 调用点与后续 `WARN_ON(open_count)` / `list_del()` 之间，加入 `CONFIG_KUNIT` 保护的 KUnit static stub 或测试专用 tracepoint，用于断言“先撤销 proxy，后进入 core teardown”。

3. `drivers/regulator/Kconfig` / `Makefile`
   - 新增测试专用选项（例如 `REGULATOR_PROXY_CONSUMER_KUNIT_TEST`），默认 N，不被产品 `.config` 或 `KUNIT_ALL_TESTS` 自动选中；只在独立 KUnit 测试配置中启用。

4. 测试用例
   - 通过 `of_overlay_apply_kunit()` 构造 provider 节点、self-target `proxy-supply` 与 proxy-consumer 属性；用真实 `regulator_register()` 注册 provider；用真实 `regulator_proxy_consumer_register()` / `regulator_unregister()` 驱动路径。
   - 对 deferred、重复 teardown、失败回滚分别设用例；不得用 mock 替代 regulator core。

上述任一改动都必须由 2号 AI 评审并单独授权；本 Agent 本轮没有实施其中任何一项。

---

## 8. 状态汇总

| 项目 | 状态 |
|---|---|
| Stage A / ACK / 17-patch 身份核验 | PASS |
| 17-patch 顺序应用（零 fuzz，已知 offset） | PASS |
| KUnit/regulator 设施审计 | PASS |
| 真实 `regulator_unregister()` 顺序证据 | PASS |
| 产品 `.config` 未变、未完整构建 | PASS |
| host 回归 38/38 与 83/83 | PASS |
| 内核原生 KUnit 集成测试实施 | BLOCKED（需生产 seam 授权） |
| ROUND35 / 其他分支 / 设备访问 | NOT RUN / 未执行 |

本轮到此停止；等待 2号 AI 独立审查报告并决定下一步。
