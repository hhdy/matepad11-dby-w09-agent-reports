# AI2-ROUND34 — 真实 regulator-core 生命周期测试（2号 AI 专属任务书）

**任务归属：2号 AI 专属任务书。**
**执行者：用户本地 Agent。** 1号 AI 的任务、分支和产物均不属于本任务。
**日期：2026-11-25（UTC+8）**
**基线分支：** `ai-parallel/stagea-port-until-boot`
**固定 ACK：** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
**任务类型：** 仅内核原生测试可行性审计；若有安全、可复现路径，再提交测试专用改动。不得修改运行时驱动语义。

## 1. ROUND33 已验收事实

ROUND33 的 17-patch 系列、host mock 测试（ROUND31 38/38、ROUND32/33 83/83）、schema gates、完整 `//common:dby_w09` Image build 和 ROUND58 配置回归均已通过。ROUND33 的 unregister 生命周期结论由代码审查确认，但测试仍是 host mock，不是实际 regulator-core/KUnit 集成执行。

本轮只补这一项证据缺口：用 ACK 内核真实 regulator core 的注册/获取/注销路径，验证 proxy handle、vote 清理和 owner unregister 顺序。不要重复 ROUND33 全套 Image 构建。

## 2. 目标

审计 pinned ACK 中 KUnit/regulator 测试设施，判断能否对 `drivers/regulator/proxy-consumer.c` 与实际 `regulator_unregister()` 路径建立可执行的内核原生测试。

若可行，新增**测试专用** KUnit 覆盖，至少验证：
- 实际注册 proxy owner regulator 与其 self-target proxy-supply；
- proxy consumer handle 获取、enable 与 `regulator_set_load()` vote；
- `late_initcall_sync` 等价撤销路径（若无法直接调用 initcall，需采用可审计的测试 seam，不得改变生产语义）；
- owner regulator unregister 时先撤销 proxy vote、释放 handle，再进入 regulator core 的 open-count/list teardown；
- deferred consumer 在未获取 handle 时注销，不触碰 regulator API；
- 重复 teardown 幂等，失败路径不泄漏 handle/vote。

若 KUnit 无法真实驱动 regulator core 的生命周期，或只能通过复制/模拟其关键逻辑实现测试，则不要提交伪集成测试；报告精确限制并停止。

## 3. 允许修改范围

仅在 `ai-parallel/stagea-port-until-boot` 分支新增/修改测试专用文件、测试 Kconfig/Makefile 接线（且不得改变产品默认配置）、测试文档和必要的最小测试 seam。

**禁止修改：**
- 17 个已验收 kernel patches 的任何运行时代码或 binding；
- `proxy-consumer.c` 的生产行为、regulator core 的生产行为、DTS/DTBO/内存/电源配置；
- Stage A 产品 `.config`、Kleaf 产品 target、现有 17-patch 顺序或 ROUND33 测试语义。

如测试 seam 必须改动生产代码，先停止并在报告中提出设计，不要自行实施。

## 4. 必须完成的核验

1. 确认工作树和 ACK commit 精确匹配；不得在非固定 ACK 上测试。
2. 检查 pinned ACK 已有 regulator KUnit 测试、test regulator provider、Kconfig/Makefile 接线与运行方式；引用具体源文件和函数。
3. 说明测试真实执行的代码路径，逐项区分真实 regulator core、真实 proxy-consumer 实现、mock/fake provider，以及未覆盖部分。
4. 若实施测试：记录 patch、`git diff --check`、checkpatch、KUnit 编译/运行命令、返回码、测试用例数和完整失败摘要；能运行则必须实际运行，不能只编译后称 PASS。
5. 验证测试配置不改变产品 `.config`；不要触发完整 Image build，除非测试接线意外影响产品配置，此时先停止并报告。
6. 现有 host suites 38/38 与 83/83 仍须通过，确保无回归。
7. 报告实际 `regulator_unregister()` 调用顺序与测试断言对应关系；不得把 mock 生命周期结果表述为内核原生测试。

## 5. 严格安全边界

- 不连接、操作或重启平板；不使用 ADB/fastboot/recovery/root。
- 不读取或写入任何分区；不刷写、不临时启动。
- 不生成或修改 boot.img、DTB、DTBO、ramdisk、vbmeta、AVB/footer 或刷机包。
- 不上传原始 HOS 固件、镜像、私有分区数据、设备标识或密钥。
- 不猜测 RAM、reserved-memory、PMIC 物理输入、稳压器父级、电压、ARC→VRM 或 DTBO 表项。
- 不重新启动 HOS4.3 固件证据上传。

## 6. 交付与停止规则

唯一报告：`firmware-analysis/round34/AI2_ROUND34_KERNEL_NATIVE_LIFECYCLE_TEST_REPORT.md`，上传至 `firmware-audit-v1`。

报告必须给出 PASS / PARTIAL / BLOCKED 判定，并附精确 commit、文件路径、命令、返回码、测试证据与限制。若不可行，提交只读审计报告即可，不要为了交付而造测试。

**完成本轮后立即停止。不得自动开始 ROUND35，不得继续修改其他移植代码。** 由2号 AI 独立审查报告并决定下一步。

## 7. 当前阶段状态（不得擅自提升）

- Phase A–D：已通过既有证据。
- Phase E：BLOCKED（最终 ABL→Linux FDT/EFI 内存交接、PM8150 物理输入拓扑缺证）。
- Phase F：BLOCKED FOR PACKAGING（ABL DTBO 选择、HOS4.3 boot path、`vbmeta_cust` 来源未闭环）。
- Phase G：NOT RUN。
- ROUND34 不能解除上述硬件/启动链阻塞，也不得据此声称设备可启动。