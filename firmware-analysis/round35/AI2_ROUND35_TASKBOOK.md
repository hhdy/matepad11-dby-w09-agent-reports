# AI2-ROUND35 — KUnit 专用生命周期测试 seam 与真实 regulator-core 集成测试

**任务归属：2号 AI 专属任务书。**
**执行者：用户本地 Agent。** 1号 AI 的任务、分支和产物均不属于本任务。
**日期：2026-11-25（UTC+8）**
**固定 ACK：** `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` (`android17-6.18.33_r00`)
**Stage A 基线：** `ai-parallel/stagea-port-until-boot`，ROUND34 报告记录 HEAD `05ec10c35e6b39881f2faae3e60d19c45de2ba75`。
**授权：** 2号 AI 已明确批准本轮新增 `CONFIG_KUNIT` 专用测试 seam。该授权仅限本任务所列文件和行为，不是对产品运行时语义或设备操作的授权。

## 1. ROUND34 结论与本轮目标

ROUND34 证实 pinned ACK 没有现成 regulator KUnit provider/测试接线。两个关键覆盖项无法在不加测试 seam 时真实验证：
- `late_initcall_sync` 的 bulk revoke：现有实质函数位于 init 段，启动后不能直接调用；
- `regulator_unregister()` 的 proxy teardown 顺序：需要在 proxy unregister 已执行、core open-count/list teardown 尚未开始的位置观测。

本轮目标：在**仅启用独立测试配置**时增加最小 KUnit seam，并用真实 `regulator_register()`、regulator consumer API 和 `regulator_unregister()` 执行路径构造集成测试。不得复制 regulator core 或 proxy-consumer 逻辑来冒充集成测试。

## 2. 严格隔离：产品 17-patch 系列冻结

- 现有 ROUND33 已验收的 17 个生产补丁、binding、review DTS、host harness 和 Stage A 产品 `.config` 全部冻结。
- ROUND35 测试代码以独立测试补丁/测试目录交付，不追加到产品 17-patch series，不改变 `round32-stagea-series.txt` 的生产补丁顺序。
- 所有新增 hook、导出包装、测试 Kconfig/Makefile 接线必须由独立测试选项控制；测试选项默认关闭，不能被产品 defconfig/Kleaf target 自动启用。
- `CONFIG_KUNIT=n` 或 `REGULATOR_PROXY_CONSUMER_KUNIT_TEST=n` 时，生产代码行为、调用顺序、数据结构布局和产品二进制语义必须保持不变。不得增加产品默认启用的 callback、tracepoint、分支或额外全局状态。

## 3. 授权允许的最小测试 seam

允许 Agent 设计并实现以下 KUnit-only seam；实现前先在报告/patch 说明中列出设计，且必须满足第 2 节隔离要求：

1. **bulk revoke helper：** 将 `regulator_proxy_consumer_remove_all()` 中的实际撤销逻辑抽为可在运行期调用的非 `__init` helper；原 `late_initcall_sync` wrapper 必须继续调用同一个 helper。仅在测试配置下提供 KUnit 可调用入口。不得复制撤销逻辑，也不得改变生产 initcall level、执行时机或单次撤销语义。
2. **unregister 顺序观测点：** 在 `regulator_unregister()` 已调用 `regulator_proxy_consumer_unregister(rdev)`、但尚未执行 `WARN_ON(rdev->open_count)`、coupling/list teardown 之前，提供仅测试配置可用的观测 hook。测试须能断言 proxy back-pointer 已清空、proxy handle/vote 已撤销，且此时 rdev 仍处于 core 注册状态。测试配置关闭时不得生成该 hook 的运行时代码。
3. **独立 KUnit 配置：** 新测试选项必须默认 `n`，依赖 proxy consumer 与 KUnit；不得修改产品 `.config`、defconfig 或产品 Kleaf target。若 KUnit 的内建/模块组合导致真实测试无法加载或运行，必须调整为隔离的测试配置并说明，不得偷改产品配置。

Agent 可提出等价且更小的实现，但不得降低上述覆盖要求。若发现必须修改非测试生产语义或无法保持配置关闭时零影响，立即停止并报告。

## 4. 真实测试要求

使用 KUnit OF overlay / KUnit device helper 或经审计的等价方式构造测试 provider 与 self-target DT 节点；实现测试专用 regulator provider ops，至少能记录 enable/disable、set_load、set_voltage 的真实回调次数与参数。通过真实 `regulator_register()` 触发生产 proxy-consumer 注册流程。

最低测试项：
- owner/self-target regulator 注册后，真实 proxy handle 获取成功；检查真实 provider ops 收到 enable 与 `set_load` 请求。
- 调用与 `late_initcall_sync` wrapper 共用的真实 bulk-revoke helper 后，检查真实 provider ops 收到 disable / load=0 / voltage 清理（仅针对实际请求属性），且 proxy back-pointer 清空。
- owner `regulator_unregister()` 真实执行时，在 core teardown 前的测试 hook 断言 proxy handle/vote 已释放、`open_count` 已回落、rdev 仍在 regulator core 注册列表中；随后 unregister 正常完成。
- deferred/no-handle 情况 unregister 不调用 regulator consumer API、不泄漏对象。
- 重复 teardown 幂等；解析/注册/投票失败路径无 handle/vote 泄漏。
- 覆盖顺序应避免 bulk-revoke 的全局 one-shot 状态污染其他用例；必要时采用单一有序测试或隔离测试进程，不得增加只为测试而改变生产状态机的 reset 接口。

**真实性要求：** 测试必须执行 pinned ACK 的真实 regulator core 与 ROUND33 生产 `proxy-consumer.c`。provider ops 可以是测试 fake provider，但 `regulator_register()`、`of_regulator_get()`/`regulator_get()`、consumer vote API、`regulator_unregister()` 必须来自真实内核代码。凡使用 mock 的部分必须明确标注，不得称为内核集成覆盖。

## 5. 验证要求

1. 17 个生产补丁按原顺序在固定 ACK 上应用；逐项记录 blob/SHA、check/apply/diff-check，确认生产 patch identities 未变。
2. 新增 KUnit-only patch 独立应用；`git diff --check` 与 `checkpatch.pl --strict` 通过。
3. 在独立 KUnit 配置下真实编译并运行测试；记录完整命令、配置片段、KUnit TAP 输出、用例数、失败摘要和返回码。仅编译不算测试 PASS。
4. 确认 Stage A 产品 `.config` 构建前后字节完全一致，且没有启用新增测试选项。
5. 复跑 ROUND31 host suite 38/38、ROUND32/33 host suite 83/83。
6. 不要求完整 `//common:dby_w09` Image 构建；不得为测试擅自触发产品 Image build。如测试接线意外影响产品配置，停止并报告。
7. 若 pinned ACK 的 KUnit runner/架构/模块条件无法实际执行测试，结果只能 PARTIAL/BLOCKED，不得将 compile PASS 写成 KUnit PASS。

## 6. 不允许事项

- 不修改 ROUND33 生产补丁语义，不改 L5/L9 self-target 约束，不引入 cross-regulator proxy handle。
- 不修改任何 DTS/DTBO、内存、PMIC、电压、父级 supply、ARC 映射或 board compatible。
- 不构建/生成 boot.img、DTB、DTBO、ramdisk、vbmeta、AVB/footer 或刷机包。
- 不连接/操作/重启平板；不使用 ADB/fastboot/recovery/root；不读写分区。
- 不上传原始 HOS4.3 固件、镜像、私有分区数据、设备标识或密钥；不恢复 HOS4.3 证据上传。

## 7. 交付与停止

唯一报告：`firmware-analysis/round35/AI2_ROUND35_KUNIT_PROXY_LIFECYCLE_REPORT.md`，上传至 `firmware-audit-v1`。

必须附：独立测试补丁路径与 SHA-256、实际 KUnit 配置、TAP 输出、真实执行路径、测试 provider 与真实内核代码边界、产品 `.config` 前后 hash、host 回归结果及所有限制。

若实现过程中发现无法满足真实集成要求，保留已完成的只读审计证据，停止提交不完整 seam，并在报告中给出精确 blocker。

**Agent 完成本轮报告后立即停止，不得自动开始 ROUND36。** 由2号 AI 独立审查并决定后续移植。

## 8. 当前总阶段状态

- Phase A–D：既有证据通过。
- Phase E：BLOCKED（最终 ABL→Linux FDT/EFI 内存交接与 PM8150 物理输入拓扑仍缺证）。
- Phase F：BLOCKED FOR PACKAGING（ABL DTBO 选择、HOS4.3 boot path、`vbmeta_cust` 来源仍未闭环）。
- Phase G：NOT RUN。
- ROUND35 只改善内核生命周期测试证据，不得据此声称板级启动条件满足或设备可启动。