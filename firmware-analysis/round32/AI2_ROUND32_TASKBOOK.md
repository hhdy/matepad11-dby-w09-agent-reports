# 2号 AI 专属任务书 — AI2-ROUND32
## Stage A 实际移植：同一 PM8150 group 内 L5/L9 各自独立的 child-scoped proxy-supply

**任务归属：2号 AI 专属任务书。** 只属于2号 AI，不得与1号 AI任务合并。  
**任务 ID：** AI2-ROUND32  
**类型：** 实际内核编程、DTS/binding、自动化测试、完整 Image 重编。  
**Stage A 分支：** ai-parallel/stagea-port-until-boot  
**报告分支：** firmware-audit-v1  
**固定 ACK：** android17-6.18.33_r00 = 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a。

## 0. 本轮唯一目标

解决 ROUND31 已确认的真实阻塞：ACK 把整个 PM8150 暴露为一个 platform device，当前 proxy helper 只能从 group device 解析一个 proxy-supply，因此无法让 L5 与 L9 各自投票到自己的 regulator。

本轮必须实现并验证一种**每个 regulator child 独立指定 proxy target** 的机制，使同一 PM8150 group 中：
- L5 child 的 proxy consumer 只引用 L5 对应 regulator；
- L9 child 的 proxy consumer 只引用 L9 对应 regulator；
- 两个 child 的 enable/current 请求分别独立创建、分别独立撤销；
- 仍保持 ROUND31 的临时票据生命周期：probe/register 时申请，late_initcall_sync 统一撤销，individual unregister 只清理自己的 handle。

不能通过把 L9 指向 L5、永久 regulator-system-load、regulator-always-on 或永久 enable 来规避问题。

## 1. 必须继承的基线

1. 精确 ACK：8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a。
2. 当前 Stage A 已有 12-patch series：kernel-baseline/round61/round31-stagea-series.txt。
3. ROUND31 helper patch：kernel-baseline/round61/patches/round31-0001-regulator-add-proxy-consumer.patch。
4. ROUND31 binding patch：kernel-baseline/round61/patches/round31-0002-regulator-proxy-consumer-binding.patch。
5. ROUND31 Kconfig patch：kernel-baseline/round61/patches/round31-0003-dby-w09-enable-proxy-consumer.patch。
6. ROUND31 审阅结论和限制：kernel-baseline/round61/PROGRESS.md 最后两节。
7. HOS4.3 静态输入只使用既有 sanitized 证据：
   - ROUND13 firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt；
   - ROUND48 kernel-baseline/round48/ack-hos43-pmic5-mode-enum-translation-and-dts-decision.md；
   - ROUND51 kernel-baseline/round51/round14-arc-value-semantics-proxy-vote-and-round11-edge-reconciliation.md。
8. 不要再声称 ROUND31 的 group-level proxy-supply 已完成 L5+L9；它只实现了通用 helper。

## 2. 设计门槛：先证明 API，再写实现

在动代码前，逐项追踪固定 ACK：
- regulator_register()、regulator_dev_lookup()、of_regulator_dev_lookup()、of_get_regulator()、regulator_get()、consumer handle 分配/释放和 rdev 引用计数。
- 确认是否已有安全的 regulator-by-device-node 获取 API；若没有，设计最小 regulator-core helper，让 proxy helper 可以通过 child node 的 proxy-supply phandle 获取正确的 struct regulator *。
- 不得直接解引用未加锁的 regulator_class 私有对象、伪造 device、绕过 regulator core 引用计数，或持有错误锁调用 regulator API。
- 处理 self-target 场景：L5 proxy target 是 L5 本身、L9 target 是 L9 本身。必须证明 handle 建立发生在 rdev 完成注册并可被查找之后；不产生递归注册、锁递归、refcount 泄漏。
- 处理 probe 顺序、deferred probe、target 尚未注册、target unregister、bulk late-init revoke 与 individual unregister 并发。
- 如果固定 ACK API 无法安全支持 child-scoped regulator handle，停止实现，提供最小可复现的源码级阻塞证明，不得猜测或先提交半成品。

## 3. DTS / binding 设计要求

目标方案优先采用 child-scoped proxy-supply：
- L5 child 的 proxy-supply = <&vreg_l5>；
- L9 child 的 proxy-supply = <&vreg_l9>；
- 各自的 qcom,proxy-consumer-enable 和 qcom,proxy-consumer-current = <100000> 仍放在各自 child。
- group-level proxy-supply 的 ROUND31 兼容行为应保留给旧式单 proxy group；若 group-level 与 child-level 同时出现，必须有明确、可测试的优先级或直接拒绝歧义，不能静默覆盖。
- schema 严格声明属性；不得放宽 additionalProperties / unevaluatedProperties。
- 只有当 binding、helper、实际 DT 结构三者完全一致且负向验证覆盖歧义时，才可把两个 child 的属性加入 Stage A review DTS patch。
- 不得修改 main、PR #1、ack18-dby-w09-dts-draft 或 firmware-audit-v1 受保护内容。

## 4. 生命周期与错误路径

- 每个 child 对应一个独立 proxy consumer object / regulator handle。
- L5 和 L9 的 set_load / enable / voltage votes 必须完全隔离。
- late_initcall_sync 只撤销尚存票据一次；清空每个 rdev 的反向指针。
- individual unregister 只撤销该 rdev 的票据；late-init 与 unregister 不可 double-disable / double-put。
- regulator_get、set_voltage、set_load、enable 任一步失败，反向释放已申请的资源。
- 注册失败不能让后续 unregister 解引用 ERR_PTR 或悬空指针。
- target provider unregister 时不能出现 consumer handle 指向已释放 rdev。
- 确认 ACK 的 regulator core delayed unused-regulator cleanup 与 late_initcall_sync 的时序影响；不要把“撤销 proxy”说成“保证 rail 一直保持开启”。

## 5. 必须提交的自动化测试

ROUND31 的 38-check host mock harness 没有进入仓库，本轮必须补齐可复现测试：
- 提交真实测试源文件、mock API headers、构建/运行脚本或 KUnit 测试；不能只提交报告中的断言数字。
- 测试两个 child 指向不同 target regulator：各自只对自身 target 投票。
- 测试两个 child 的 enable/current 独立；撤销一个不影响另一个。
- 测试 late_initcall_sync bulk revoke、individual unregister、重复 teardown。
- 测试 target 缺失/deferred probe、target unregister、错误 phandle、child/group 双重声明冲突。
- 测试普通无 proxy 属性的 regulator 行为不变。
- schema 正向/负向 fixture 必须覆盖 L5/L9 双 target、错误类型、缺属性、错误 phandle、未声明属性和歧义输入。

## 6. 构建和回归

- 更新 Stage A patch series，ROUND31 既有 12 patches 必须原样保留或通过明确的追加 patch 修复；不要偷偷改写历史 patch blob。
- 在精确 ACK disposable worktree 对全 series 逐个执行 git apply --check、git apply、git diff --check。
- 对新增 patch 运行 ACK scripts/checkpatch.pl --strict。
- 运行真实 dt_binding_check、dt-doc-validate 和 fixture gate；保留诊断日志并用内容断言判断 negative case。
- 使用 manifest-pinned Kleaf 重新构建完整 //common:dby_w09 Image；ROUND31 build 不自动覆盖本轮新增代码。
- ROUND58 config validator：33/33 必需 symbols 仍为 =y；11/11 helper tests 不退化。
- 记录 Image / System.map / vmlinux / .config 的大小与 SHA-256；不要上传构建产物。

## 7. 严格禁止

未经用户单独明确授权，绝不：
- 连接或操作平板；ADB、fastboot、recovery、reboot、unlock、root、flash、临时启动；
- 读取或写入任何设备分区；
- 构建/重打包 boot、DTBO image、AVB/vbmeta/footer 或关闭验证；
- 猜测 PM8150 parent supply、VPH_PWR、ARC→VRM 关系或 PMIC 电压；
- 上传/重新导出 HOS4.3 原始固件、FDT、DTBO 或设备标识；
- 改写 ROUND31 临时票据为永久票据；
- 合并 1号 AI 的任务或修改其文件。

## 8. 交付和停止

唯一报告路径：
firmware-analysis/round32/AI2_ROUND32_CHILD_SCOPED_PROXY_IMPLEMENTATION_REPORT.txt
分支：firmware-audit-v1。

Stage A 分支提交实际 patch、严格 binding、DTS fixture、可复现 host/KUnit 测试源与脚本、patch series 更新、PROGRESS 记录。报告需明确列出源 API 设计、测试结果、构建 hash、是否真正完成 L5+L9 独立投票表达，以及所有未解决硬件问题。

**只交付 ROUND32 这一份报告后立即停止，不得自动启动 ROUND33。**