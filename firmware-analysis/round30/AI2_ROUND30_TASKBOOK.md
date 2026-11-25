# 2号 AI 专属任务书 — AI2-ROUND30
## Stage A 实际代码集成：QMP UFS PHY vdda-phy-always-on + 真实编译

**任务归属：2号 AI 专属任务书。** 本任务只属于2号 AI；执行者为用户本地 Agent。不得合并、代执行或覆盖1号 AI 的任务。  
**任务 ID：** AI2-ROUND30  
**任务类型：** 实际内核移植编程与验证，不是研究报告任务。  
**唯一 Stage A 工作分支：** `ai-parallel/stagea-port-until-boot`  
**报告/任务书分支：** `firmware-audit-v1`  
**固定 ACK：** tag `android17-6.18.33_r00`，commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`。  
**当前目标：** 将 ROUND63 的 QMP UFS PHY always-on 消费者生命周期修复真正集成到 Stage A ACK 内核，并通过真实 patch、binding、Kleaf 编译验证。

---

## 1. 开始前必须核对的输入

1. 阅读 Stage A 的 `kernel-baseline/round61/ROUND61_LONG_RUNNING_STAGEA_MISSION.md` 和最新 `kernel-baseline/round61/PROGRESS.md`。
2. 阅读主分支 ROUND63 说明：
   `kernel-baseline/round63/round63-ufs-phy-always-on-lifecycle-compatibility.md`，blob `bc91a1c5b8112d9466e6b5950ae93ca246c0d366`。
3. 只使用以下最终候选，不得使用旧版：
   - Driver patch：`kernel-baseline/round63/0001-phy-qcom-qmp-ufs-preserve-vdda-phy-always-on.patch.draft`，blob `a06b7d3fc19e0b23895b0013ab9ac322d84cdda5`。
   - Binding patch：`kernel-baseline/round63/0002-dt-bindings-phy-qmp-ufs-vdda-phy-always-on.patch.draft`，blob `a6668eebe293f9a35e9c08d6be4f37c4340e7ddd`。
   - Board review draft（只作后续 DTS 输入参考，不要当真实源文件）：`dts/dby-w09-ack18-board.dts.draft`，blob `c209d519614fb0ff89b042ce274191b20120a09a`。
4. 复核 ROUND58 Kleaf target 和 config validator 的 Stage A 已集成版本/准确 blob，不得盲目覆盖已经成功的 Phase A–D 实现。
5. 复核 ROUND59 UFS patch series 的实际文件与顺序。ROUND63 两个 patch 必须纳入最终 Stage A patch series，置于 UFS binding/driver 改动之后、最终板级 DTS/schema/DTB 验证之前。

若任一输入 blob 与指定 SHA 不符，立即停止该输入的应用并报告差异，不得改用旧版或猜测替代。

## 2. 实际代码集成（必须做）

在精确 ACK commit 的 disposable worktree 中进行，保留 pristine baseline：

1. 证明 HEAD 等于 `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`。
2. 按真实 Git 流程对两个 ROUND63 patch 分别执行 `git apply --check`、`git apply`；记录命令、退出码和修改文件。
3. 执行 `git diff --check`，检查完整 diff。
4. 对 driver patch 执行 ACK 自带 `scripts/checkpatch.pl`；逐项修复新增的真实错误。不要为了消除提示而改动语义或隐藏警告。
5. 独立检查代码逻辑：
   - property 缺省时，原始 bulk enable/disable 行为必须完全保持；
   - property 存在时，首次 power-on 只获取一个 vdda-phy enable reference，并恢复 init_load_uA；
   - power-off 时其余 rail 正常 disable，vdda-phy 保留 enable reference 且 load vote 变为0；
   - 后续 power-on 恢复 load vote，不重复 enable；
   - devm cleanup 在 regulator handle 释放之前运行，并平衡保留的 enable reference；
   - 错误路径不会留下未平衡 enable/load；
   - 必须拒绝不符合 vdda-phy 首位约束的 regulator list，不能错误地对其他 rail 套用特殊处理。
6. 检查所有 pinned ACK QMP UFS regulator lists；验证 vdda-phy / vdda-pll 顺序假设。保留 ROUND63 对15组列表的审查证据，若真实源码不一致则停止并修正代码，不得假定。
7. 审查普通 UFS consumer-first remove 路径：UFS Host remove 应先 power_off/phy_exit，再释放 devm PHY reference。明确 PHY stateless device link 不提供 managed supplier-unbind 语义；不得声称强制先 unbind QMP provider 安全。

## 3. Binding 与负向验证

在固定 ACK 的真实工具链中执行：

1. 对修改的 QMP UFS PHY binding 运行真实 `dt_binding_check`，记录完整命令、工具版本、退出码和诊断。
2. 运行真实 `dt-doc-validate` / `dt-mk-schema`（如内核目标已覆盖则仍记录工具链来源）。
3. 建立正向/负向 fixture：
   - SM8250 PHY 节点含 `vdda-phy-always-on`：应通过；
   - 相同节点不含该可选属性：应通过，证明属性可选；
   - 属性值类型错误：必须失败；
   - 其他未声明属性：必须失败。
4. 对比修改前后诊断，不能用过滤、`additionalProperties: true`、`unevaluatedProperties: true` 或只验证单个临时 schema 的方式制造 PASS。
5. 不要把 `vdda-phy-max-microamp` / `vdda-pll-max-microamp` 加进 DTS 或 schema；当前 ACK SM8250 驱动静态 load 值为89900/18800µA，binding 严格拒绝这两个未声明属性。

## 4. Kleaf 编译与回归

必须使用 Stage A 已验证的固定 ACK / manifest-pinned Kleaf 环境：

1. 把 ROUND63 两个 patch 应用到已经通过 Phase A–D 的完整 Stage A disposable source workspace；保留先前已通过的 UFS、GenPD、VDDP 和 Kleaf 变更。
2. 运行实际 Kleaf/Bazel target query/cquery，确认目标仍可解析且 QMP PHY 驱动源确实进入目标。
3. 编译 QMP UFS PHY 对应对象及完整 `//common:dby_w09` Image target。不能用单文件语法检查或 synthetic build 代替。
4. 使用 `set -o pipefail` 记录日志；不得通过 tee 隐藏构建失败。
5. 若编译失败，定位首个有效错误，在本任务专属 Stage A 分支上修正候选代码/补丁，重跑受影响检查和完整 Image 构建。
6. 回归 ROUND58 config validator，确认 storage-first 必需项仍为 built-in `=y)，不得降低配置要求来绕过构建问题。
7. 记录 Image、System.map、vmlinux、最终 .config 的大小/hash；不要重复上传无关的大型构建文件。

若本地实际没有授权 Linux build runtime 或 manifest/toolchain 不完整，完成所有可做的真实 source-level patch/apply/schema工作，然后停止并明确说明唯一外部阻塞；不得伪造编译结果。

## 5. Stage A patch series 与持久化代码

1. 更新 Stage A 专属分支上的实际 patch series/应用脚本/集成记录，使 ROUND63 binding + driver 两个 patch 成为正式有序集成项。
2. 将经过真实测试的修正 patch、测试 fixture 和必要脚本提交到 `ai-parallel/stagea-port-until-boot`。不要提交 disposable build 输出、固件原始数据、stock images、私密数据或设备标识。
3. 更新 `kernel-baseline/round61/PROGRESS.md`，列明实际 Git apply、checkpatch、dt_binding_check、Kleaf 编译结果及精确 SHA。
4. 若已有 Phase D Image 需要因新增驱动改动重编，必须完成真实重编；原先 Phase D PASS 不自动覆盖新增代码。
5. 代码实现优先于报告；报告仅保留复现命令、结果和未解决阻塞，不要另做泛泛研究文档。

## 6. 独立保留的硬件阻塞与安全边界

ROUND63 不解决以下问题，必须保持独立标记：

- PM8150 L5 物理输入 parent supply 未证实。禁止编造 `vdd-supply`、`vin-supply`、`vph-pwr-supply`。
- HOS4.3 ARC/proxy 的临时100mA boot-time proxy votes、late_initcall_sync 清理语义未移植。禁止把它伪装成永久 `regulator-system-load` 或 `regulator-always-on`。
- stock DTBO entry 8 的发现不证明当前启动实际选择 entry 8，也不证明 runtime regulator 状态。
- ROUND29 Huawei root compatible/schema 实验没有授权修改正式 DTS 或 binding；不要将其临时 schema 直接合入本任务。
- 不要因为驱动/镜像编译成功而宣称 Phase E/F 已关闭或设备可启动。

未经用户另行明确授权，严禁：
- 连接/操作平板、ADB、fastboot、recovery、reboot、unlock、root、flash、临时启动；
- 读取或写入任何分区；
- 构建/重打包 boot、DTBO image、AVB/vbmeta/footer 或关闭验证；
- 擅自恢复 HOS4.3 原始固件资料上传；
- 修改 main、firmware-audit-v1、ack18-dby-w09-dts-draft 或 PR #1。

## 7. 交付与停止规则

唯一交付报告路径：
`firmware-analysis/round30/AI2_ROUND30_STAGEA_QMP_PHY_IMPLEMENTATION_REPORT.txt`
报告分支：`firmware-audit-v1`。

完成真实实现、测试和提交后，上传一次报告并立即停止。不得自动启动 ROUND31，也不得把ROUND29未解决的父板级 schema架构研究扩展成新任务。若遇到必须由用户授权/本地 Agent 提供的外部条件，清楚指出阻塞并停止。

**本任务必须真正做内核移植编程；不得以“已审阅”“计划”“模拟应用”或单独报告代替代码集成与真实测试。**
