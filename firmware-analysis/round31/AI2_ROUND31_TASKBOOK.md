# 2号 AI 专属任务书 — AI2-ROUND31
## Stage A 实际移植：HOS4.3 PM8150 L5/L9 临时 proxy-consumer 生命周期

**任务归属：2号 AI 专属任务书。** 本任务只属于2号 AI；执行者为用户本地 Agent。不得合并、代执行或覆盖1号 AI 的任务。  
**任务 ID：** AI2-ROUND31  
**任务类型：** 实际内核移植编程、测试和完整 Image 重编；不是研究报告任务。  
**唯一 Stage A 工作分支：** `ai-parallel/stagea-port-until-boot`  
**报告/任务书分支：** `firmware-audit-v1`  
**固定 ACK：** tag `android17-6.18.33_r00`，commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`。

## 0. 本轮唯一目标

把 HOS4.3 中已确认的 PM8150 L5 / L9 临时 proxy-consumer 请求及其生命周期，按真实 Qualcomm 语义移植到固定 ACK Stage A 内核。目标不是永久增加 regulator load，而是实现：
- regulator 注册时建立对应的临时 proxy consumer；
- 按已确认的 HOS4.3 请求字段投票；
- 在 vendor 语义规定的 `late_initcall_sync` 阶段统一撤销临时请求；
- 单个 regulator teardown 时正确注销该 regulator 的 proxy；
- 所有失败/延迟探测/卸载路径不泄漏 regulator handle、enable reference 或 load vote。

本轮只处理 L5/L9 proxy 生命周期。**不实现 ARC provider，不改 PMIC parent supply，不改 QMP PHY always-on。**

## 1. 权威输入与必须阅读材料

1. 固定 ACK 源码：commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`。
2. Qualcomm KONA 语义对照：commit `cad09e061ef6cf689a4a1e54d27562e0f042236a`：
   - `drivers/regulator/proxy-consumer.c`
   - `drivers/regulator/core.c`
   - 对应 regulator binding / DTS 中的 proxy 属性使用方式。
3. HOS4.3 本地证据（只读，不重新导出固件）：
   - ROUND13：`firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt`，blob `c3dd45dac71ee45e34697b1fb78abccc40f94b26`。
   - ROUND48：`kernel-baseline/round48/ack-hos43-pmic5-mode-enum-translation-and-dts-decision.md`。
   - ROUND51：`kernel-baseline/round51/round14-arc-value-semantics-proxy-vote-and-round11-edge-reconciliation.md`。
4. Stage A 最新任务记录：`kernel-baseline/round61/PROGRESS.md`；ROUND30 已验收，QMP PHY patch series 和 Image build 为当前基线。
5. Stage A 当前有序 patch series、Kleaf workflow、config validator、tests 与现有 ROUND30 patch 文件。

## 2. 已确认事实（不得重新解释或扩大）

ROUND13 本地静态证据确认：
- L5 provider group：`/soc/rsc@18200000/rpmh-regulator-ldoa5`；child regulator-name `pm8150_l5`。
- L5 有 `proxy-supply`，目标 phandle 124 指向其对应 child；child 有 `qcom,proxy-consumer-enable`，且 `qcom,proxy-consumer-current = 100000` µA。
- L9 provider group：`/soc/rsc@18200000/rpmh-regulator-ldoa9`；child regulator-name `pm8150_l9`。
- L9 有 `proxy-supply`，目标 phandle 125 指向其对应 child；child有 `qcom,proxy-consumer-enable`，且 `qcom,proxy-consumer-current = 100000` µA。
- L6 无 proxy-supply；不得给 L6 添加 proxy。
- ROUND48 已明确：该请求是临时 boot-time proxy vote；永久 `regulator-system-load=<100000>` 不是等价实现，必须在 `late_initcall_sync` 撤销。
- 不能把 proxy 语义改成 `regulator-always-on`、永久 system-load、永久 enable 或其他常驻负载。
- 这些记录是静态 FDT 证据和 KONA source cross-reference，不等于设备 runtime 已验证。

**特别注意：** ROUND13 的 phandle 描述看似指向 regulator 自身 child。必须回到 ROUND13 的完整原文、KONA `proxy-consumer.c` 和 regulator core call site，核实 property 所在节点、phandle 目标、proxy regulator handle 获取方式和是否存在递归/自引用。若无法证明这是 KONA driver 预期的有效拓扑，立即停止 proxy 实现，不得猜测另一条 supply 或自行改写 phandle。

## 3. 实际代码工作

在固定 ACK 的 disposable worktree 中完成：

1. 先核实 KONA `proxy-consumer.c` 的精确生命周期、数据结构、错误处理、handle 获取、set_load / enable 顺序、`late_initcall_sync` 撤销、单 regulator unregister 语义；逐项映射到 ACK 当前 regulator core API。
2. 核对 ACK 的 `regulator_register` / unregister / devres 生命周期、probe defer、device shutdown、late initcall 顺序及 regulator handle 的锁语义。
3. 若兼容性和 DTS phandle 语义已证明安全，实际移植最小必要实现：
   - 优先保留独立 helper 文件和清晰的 regulator-core hook，不要把实现塞进无关 PMIC driver；
   - 对 L5/L9 只在 HOS4.3 确认的属性存在时注册；
   - current 必须来自属性值 100000 µA，不硬编码给所有 rail；
   - enable flag 只按原语义处理；
   - 只在 `late_initcall_sync` 撤销临时请求；
   - individual regulator unregister 时安全清理其 proxy；
   - 防止重复注册、重复撤销、双重 disable、负载票据泄漏和 regulator core 锁递归。
4. 需要的 Kconfig / Makefile / binding / fixture 必须一并实现。binding 必须严格声明实际使用的属性，不得用宽松 `additionalProperties: true` / `unevaluatedProperties: true` 吞诊断。
5. 对现有 Stage A DTS draft，仅在准确 property placement、phandle 和 schema 语义被证明后，新增临时 proxy 属性到 Stage A review patch；不得改 protected DTS branch、PR #1 或 main 的 review draft。
6. 不得改写现有 UFS QMP PHY / UFS Host / GenPD / VDDP / Kleaf patch 的语义或顺序；本轮 patch 必须追加在现有 series 的正确位置。
7. 如果确认 KONA helper 无法安全移植到 ACK（例如 ACK regulator core 无法保证 late-init 清理顺序，或本地 proxy-supply 是无法解析的自引用），停止代码实现并给出最小、可复现的阻塞证据。不要提交半成品。

## 4. 必须验证

- 精确 ACK HEAD / 所有关键源 blob 身份。
- `git apply --check`、实际 apply、`git diff --check`、ACK `checkpatch.pl --strict`。
- 正向 fixture：无 proxy 属性的普通 regulator 行为不变；L5/L9 确认的 enable/current 属性被识别。
- 负向 fixture：缺失 proxy-supply、错误 phandle、非法 current、enable flag 类型错误、未声明属性必须被拒绝。
- 验证临时 proxy 只在预期阶段存在；`late_initcall_sync` 后 load 与 enable request 平衡归零。
- 验证 individual regulator unregister、probe defer、注册失败和重复清理路径。
- 尽可能添加 KUnit 或可执行的最小单元测试；不可只用 grep/静态字符串存在证明 lifecycle 正确。
- 用固定 ACK manifest-pinned Kleaf 环境重新构建完整 `//common:dby_w09` Image；ROUND30 的旧 Image PASS 不自动覆盖本轮新增代码。
- 回归 ROUND58 config validator：33/33 必需符号仍为 =y，11/11 helper tests 不退化。
- 记录 Image / System.map / vmlinux / .config 大小与 SHA-256；不上传大型构建产物。

## 5. 明确禁止事项

未经用户单独明确授权，绝不：
- 连接/操作平板；ADB、fastboot、recovery、reboot、unlock、root、flash、临时启动；
- 读取或写入任何设备分区；
- 构建或重打包 boot、DTBO image、AVB/vbmeta/footer，或关闭验证；
- 猜测 PM8150 L5/L9 的物理 parent supply、VPH_PWR、ARC→VRM 关系或任何 PMIC 电压；
- 把 proxy 临时票据永久化；
- 重新导出/上传 HOS4.3 原始固件、FDT、DTBO 或设备标识；
- 修改 main、firmware-audit-v1 内容分支、ack18-dby-w09-dts-draft 或 PR #1；
- 混入 1号 AI 的任务、报告或未授权改动。

## 6. 交付与停止规则

唯一报告路径：
`firmware-analysis/round31/AI2_ROUND31_STAGEA_PROXY_CONSUMER_IMPLEMENTATION_REPORT.txt`
报告分支：`firmware-audit-v1`。

在 Stage A 分支提交经过真实测试的源 patch、binding、fixtures、必要脚本和 patch-series 更新；更新 PROGRESS，列出每项测试、精确 SHA、构建结果和剩余硬件阻塞。若不能安全实现，报告具体阻塞和已完成的真实 source-level work。

**只交付本轮这一份报告后立即停止。不得自动启动 ROUND32。** 本任务仍是 2号 AI 专属，不得与1号 AI并行任务合并。
