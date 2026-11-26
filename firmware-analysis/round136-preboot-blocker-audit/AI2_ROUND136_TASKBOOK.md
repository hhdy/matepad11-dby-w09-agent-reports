# ROUND136 — 2号 AI 独立审查任务书：DBY-W09 首次启动前四项硬门槛

- 任务编号：ROUND136
- 任务所有者 / 最终决策者：1号 AI（ChatGPT）
- 执行者：**2号 AI（独立审查 AI）**
- 执行分支：`ai2/round136-preboot-blocker-audit`
- 交付目录：`firmware-analysis/round136-preboot-blocker-audit/`
- 目标文件：`AI2_ROUND136_PREBOOT_BLOCKER_AUDIT.md`
- 基准日期：2026-11-26
- 审查类型：只读源码与既有证据审查；不是 WorkBuddy Agent 任务

> 重要角色区分：1号 AI = ChatGPT，负责移植方案、候选代码和最终审核；2号 AI = 本任务执行者，负责独立只读审查；本地 WorkBuddy Agent = 另一独立执行工具，当前正在执行 ROUND135 R3 构建验证，不是 2号 AI。本任务不得转交给 WorkBuddy Agent，也不得占用或改变 R3 执行。

## 1. 任务目标与优先级

这次不是重新研究整个设备，也不是重复 ROUND135 R2。目标是在 ROUND135 R3 继续执行的同时，独立确定 DBY-W09 6.18.33 内核候选距离**首次安全实机启动**还缺哪些关键证据，并把问题收敛为可执行的最短验证清单。

请只审查四个指定领域：

1. Huawei HOS4.3 ABL 最终 FDT、系统内存与 EFI/classic kernel handoff。
2. PM8150/PM8150L 的物理输入电源父级与 UFS 相关供电链。
3. HOS4.3 RPMh ARC 的 MMCX→MX parent/corner 依赖，与 ACK 6.18.33 SM8250 RPMHPD 实现是否等价。
4. Android boot header v2、独立 ramdisk、DTBO 选择、AVB/vbmeta descriptor 和可用启动测试路径。

**首要结论必须回答：这四项中哪些阻止 6.18.33 Image 编译，哪些只阻止可信的 board DTB/启动包，哪些是第一次接触实机前必须关闭的硬门槛？** 不要把“内核可以编译”与“设备可以启动”混为一谈。

本任务与 ROUND135 R3 并行。除非发现会直接使候选源代码无效的硬证据，否则不得要求暂停、重做或修改 R3。R3 目前仍按原任务书执行身份、Schema、真实 DTB、Kconfig、对象编译、Kleaf Image 和 Host regression。

## 2. 固定输入身份

### 2.1 ACK 与 ROUND135 候选

- ACK repo/ref：`aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`（Android 17 / 6.18.33 固定源码提交）。
- ACK root tree：`790a68ae6d4f4ac51ab2d88977b6fd5c031473b7`。
- ROUND135 23-patch expected content Tree SHA：`afe9517f8062b96bfeb5b4dd5714942861e6a44b`。这是 content tree SHA，不是 commit SHA，也不是 Image SHA。
- ROUND135 manifest 当前已核验 blob：`9188de2022f88c374bfcaa367c505428812608d9`（AI1 分支 `ai1/round130-stagea-ufs-lifecycle-integration`）。
- ROUND135 候选 board DTS blob：`58293f7a62a50f8109886c92ce4b9cd14d7980e2`。
- UFS dual-GenPD / required-OPP 驱动实现在冻结 patch 5 中，blob：`f1d54e5e0379183fbdfb3ca6132c6d0fc61d4622`；ROUND135 不应再重复加入旧 ROUND45 duplicate driver patch。
- ROUND135 R2 双树预检和受控 Offset 已由 2号 AI 独立接受；预期 tree SHA 已锁定。不得重复 R2 两树预检或再要求 2号 AI 重做 offset 审计。

### 2.2 必须先阅读的既有结论（只读输入，不要重复执行）

以下文件是本次审查的固定历史底稿。使用时要核对对应 blob 与内容，不得只依据文件名或旧聊天摘要：

| 主题 | 文件与 blob |
|---|---|
| HOS4.3 base FDT memory / reserved-memory | `kernel-baseline/round19/hos43-memory-reserved-memory-handoff-review.md` — `06f91fdf6853b382dfe8fd8da7a83c7aaf24c902` |
| SM8250 ABL memory path 参考及 Huawei ABL 未验证边界 | `kernel-baseline/round42/hos43-memory-handoff-sm8250-abl-fdt-prerequisite.md` — `1ba87a9079f00aed370c82d3b9a1c8c76ded1c24` |
| ACK classic FDT 与 EFI-stub memory handoff 差异 | `kernel-baseline/round43/ack-6.18.33-fdt-memory-scan-classic-vs-efi-handoff.md` — `2a89fdf94ec59d4744d6b2eb752760737c34da53` |
| PM8150 physical VRM parent gap | `kernel-baseline/round21/ack-pm8150-vrm-parent-supply-gap.md` — `3402acb92c7fe794fbb106097e00c81e87bcc845` |
| HOS4.3 ARC parent graph to ACK DTS | `kernel-baseline/round16/hos43-rpmh-arc-parent-graph-to-ack-dts.md` — `0b362af9f603ad6d6e3c1546a8b0aedfa4b83658` |
| HOS4.3 ARC logical corner / DT semantics | `kernel-baseline/round24/hos43-arc-logical-corner-dt-semantics.md` — `fae50adc342e84f3e24a793f4fad85ff0134cf88` |
| MMCX→MX versus ACK SM8250 RPMHPD | `kernel-baseline/round30/sm8250-rpmhpd-mmcx-mx-parent-equivalence-gate.md` — `c6091bd1461e98e1dd4be4bae754096104726788` |
| ACK PM8150 mode / DRMS limits | `kernel-baseline/round47/ack-pm8150-regulator-mode-drms-capability-review.md` — `656f3dfc1aad11d0c77f4fa29bd542d4b13be030` |
| ARC fifth edge / corner semantics / proxy-vote reconciliation | `kernel-baseline/round51/round14-arc-value-semantics-proxy-vote-and-round11-edge-reconciliation.md` — `3c85bd2ae648e1975fb2da50eb813ced4844f1f0` |
| MMCX→MX ACK implementation review and remaining local gate | `kernel-baseline/round50/ack-sm8250-mmcx-mx-arc-parent-semantics-and-remaining-local-gate.md` — `d83de793c474769bb1df49c9bedbf6bc152e3f9b` |
| Phase E memory/PM8150 gate summary | `kernel-baseline/round61/phase-e-board-dts-memory-power-gates.md` — `3e9f18db04ec4833dd4b033570a816482489cb7b` |
| Same-device boot-v2 / ramdisk / DTBO / AVB prior source review | `kernel-baseline/round18/dby-w09-legacy-boot-avb-packaging-review.md` — `fa56c4b53d4c30faecaa925c0db7c7ade8e56e8b` |
| ROUND64 sanitized AVB/footer/descriptor evidence | `firmware-analysis/round64/round64-dby-w09-hos43-bootv2-ramdisk-dtbo-avb-evidence.md` — `b1e27ce5ad37280ed4ed48f1560e10cfad332617` |
| ROUND65 fstab / ramdisk / vbmeta_cust / boot-tool / ABL selection audit | `firmware-analysis/round65/round65-first-stage-fstab-vbmeta-cust-and-boot-tool-audit.md` — `31f08a03694431c12a076f7d69fce070842944fa` |
| Phase F AVB/boot-package gate summary | `kernel-baseline/round61/phase-f-boot-packaging-avb.md` — `1031ad13eb7c70e9e61eebf7acc4aba6d4f0c109` |
| ROUND135 Ubuntu UFS reference reconciliation (do not redo) | `kernel-baseline/round135/AI1_ROUND135_UBUNTU_REFERENCE_RECONCILIATION.md` — `f4dca432c1b244e61aa2d51bbf0ea3f2757a1e4f` |

ROUND135 候选 DTS 的特别注意项：DTS 注释说明它继承 ACK `sm8250.dtsi` 中 `device_type = "memory"` 的零尺寸 `/memory` 占位；HOS4.3 base-FDT 的公开清单记录 37 个 reserved-memory 子节点（旧 ROUND19 统计为 34，ROUND24 修正为 37），但真实物理地址已脱敏，且最终 ABL 填充行为仍未知。审查必须核对候选 DTS 实际内容，不能把注释或占位节点当成有效系统 RAM map。

## 3. 工作流与时间效率

1. 先阅读本任务第 2 节列出的固定报告，制作“已知证据 / 未解决事实”差异表；不重新跑已完成的 Agent 本地检查。
2. 对确实影响结论的 ACK 源码语义，直接检查固定 ACK commit `8ad08f75...` 的源文件与调用路径；记录文件路径、函数/符号、精确行号或稳定代码片段。禁止引用浮动 `android17-6.18` 分支代替固定 commit。
3. 对公开源码/文档的补充只用于填补明确缺口；必须给出确切 repo、commit/tag、文件和行号/URL。不要广泛搜集无关仓库。
4. 按第 4 节四个工作流并行审查；如果某条证据在授权范围内不存在，就明确标为 `UNKNOWN / LOCAL EVIDENCE REQUIRED`，不要推测或等待更多信息。
5. 最后用第 5 节矩阵给出可操作结论，并提交一个完整报告。不要为得到“PASS”而自行降低门槛。

## 4. 四项审查内容

### A. HOS4.3 ABL 最终 FDT 与系统内存交接

必须回答：

- 固定 ACK 6.18.33 classic ARM64 路径如何从 FDT 得到可用 RAM？实际检查哪些 `/memory` 属性/节点，零尺寸 `reg` 是否可形成有效 memblock RAM？
- EFI-stub 路径需要哪些可信 `/chosen/linux,uefi-*` 元数据？什么证据才能证明实际进入 Linux EFI stub，而不是仅仅 ABL 是 UEFI/EFI 环境？
- HOS4.3 原始 base FDT 的 `/memory` 零值占位、37 个 reserved-memory children，与 ROUND135 candidate DTS 的继承关系分别能证明什么，不能证明什么？
- 当前板级 DTB 即使 `dtc`、schema、`dtbs_check` 全部通过，是否仍可能因最终 FDT 没有有效 RAM 或 reservation 冲突而无法进入内核？
- 关闭该门槛所需的最小权威证据是什么？必须明确要求最终 ABL 已完成 DTB/DTBO 选择与修补后、即将进入内核时的 sanitized FDT，以及真实 kernel entry route；说明如何安全脱敏且保留节点地址范围/大小关系。

禁止：从另一款 SM8250 设备、HOS4.2 或公开 Linux 端口复制 RAM 地址；把 reserved-memory 当作 system RAM；假设 ABL 一定会把零尺寸占位填好；凭 `efi` 字样推断 EFI-stub handoff。

### B. PM8150 / PM8150L 物理输入供电链

必须回答：

- 明确区分 UFS consumer → PMIC regulator output 与 PMIC regulator 自己的 `vdd-*-supply` / `vin-supply` 物理输入 parent。不能把前者误当后者。
- 结合 ROUND11/14/21/47/51 已有证据，列出 UFS VCC、VCCQ、VCCQ2、PHY VDDA/PLL/REFCLK、VCCQ parent S8 所关联的输出 rail，并指出哪些物理输入 parent 在 HOS4.3 证据中未建立。
- 解释 ACK regulator core 在 full-constraints/DT populated 下可能采用 dummy regulator 的精确语义：它是否只是软件图缺少 parent 时假设外部电源已存在，是否能证明真实供电已使能？
- 评估缺失物理 parent 对 kernel Image 编译、DTB 编译、UFS probe、实际电气安全分别属于哪一种门槛。不要把“可能不阻止 probe”写成“供电安全”。
- 给出关闭门槛所需的最小可信证据来源（HOS4.3 PMIC regulator runtime tree / bootloader regulator state / 原理图或同等权威输入电源资料），并明确哪项必须由本地只读取证提供。

禁止：猜测 `vph_pwr = 3.7 V`、补假 fixed-regulator、猜接 `vdd-s*-supply`、把 ARC parent-supply/proxy-supply 转成普通 regulator supply；也不得仅因 same-device Linux 7.0 / HOS4.2 DTS 有相关属性就套用。

### C. HOS4.3 ARC MMCX→MX 与 ACK SM8250 RPMHPD 等价性

必须回答：

- 根据 ROUND14/16/24/30/50/51，准确描述 HOS4.3 五条 ARC parent edges、MMCX→MX 的方向、corner/level 语义、临时 proxy vote 与 boot-time proxy 的区别。不得混淆 ARC regulator 图、RPMhPD GenPD 图和 PM8150 VRM 图。
- 在固定 ACK commit 中检查 SM8250 实际选用的 RPMHPD descriptor：MMCX descriptor 是否有 parent、CX-with-MX-parent 是否只用于 CX、性能状态请求是否沿 parent 传播到 MX。
- 结合 ROUND135 driver patch5：UFS Host 的一个 `required-opps` request 被映射到 MMCX（domain index 0），GCC `UFS_PHY_GDSC` 保留为 index 1。说明这能证明请求被送到哪个 provider，但不能自动证明 MMCX→MX 的 ARC 级联。
- 判断是否存在任何新证据足以证明 ACK MMCX 对 HOS4.3 MMCX→MX 完全等价；如没有，精确列出缺失的 HOS4.3 resource/set/corner/Command DB AUX map 或 runtime vote 证据。
- 对三种可能方案（共享 ACK SM8250 descriptor 加 parent、DBY-W09 专用 RPMHPD descriptor、实现独立 ARC provider）只做风险/所需证据比较，不写代码、不替 1号 AI 做未经证据支持的方案选择。

禁止：因 corner 数值相似就宣称等价；把 MMCX proxy 的暂时启动票说成 always-on；自行添加 MMCX→MX parent 或新 ARC driver；仅凭 Ubuntu DTB 反推 Ubuntu UFS driver 行为（ROUND135 Ubuntu reconciliation 已明确其 UFS driver source 未提供）。

### D. Android boot-v2 / ramdisk / DTBO / AVB 与首次测试路径

必须回答：

- 复述 ROUND64/65 已经确立的 stock 结构：boot header v2、embedded kernel/ramdisk/DTB、独立 ramdisk 分区、DTBO v0 / 9 entries、fstab 在 base FDT 的 `/firmware/android/fstab`、独立 ramdisk 内容与模块加载证据边界。
- 准确解释 AVB 已知事实：boot/ramdisk/dtbo 的 footer 与 root vbmeta descriptor 覆盖；不能把 descriptor target 视为可以不重签就修改，也不能混淆 footer inventory 与签名/回滚策略。
- 单独审查 `vbmeta_cust.img`：1 MiB 文件与 footer original-image-size/pointer 超出文件、offset-zero 内部结构观察和 avbtool `Algorithm: NONE`/no descriptors 是两个不同证据面；在没有完整来源前保持 UNKNOWN，不提出修复。
- 九个 DTBO entry 的运行时 ABL 选择仍未知；entry 8 / board-id 0x206a 仅候选，不等于选中。列出获得真实选中项所需的 ABL log/最终 FDT/可信 bootloader trace。
- 区分 public same-device Linux reference 中“可能需要写分区/不接受 fastboot boot”的观察与 HOS4.3 Android 实际 policy；不能仅凭同设备 Linux 参考决定 Android 测试方法。
- 给出任何制作或试启动前必须补齐的最小元数据清单，包括 boot header 保留字段、ramdisk 分区实际消费关系、DTBO 选中项、AVB/vbmeta 覆盖链、签名/回滚策略、可恢复路径与明确授权。

禁止：生成/修改 boot、ramdisk、DTBO、vbmeta 镜像；运行写入工具；假定 `fastboot boot` 可用或不可用；把公开 Linux 端口 initramfs 当 Android 17 ramdisk；修改或绕过 AVB。

## 5. 必须提交的结论矩阵

每个工作流 A/B/C/D 必须分别给出如下状态，不得只写一个笼统 BLOCKED：

| 审查项 | 编译 6.18.33 Image 是否阻塞 | board DTS/DTB 纯离线编译是否阻塞 | 首次安全实机启动是否阻塞 | 当前状态 | 关闭所需最小证据 |
|---|---|---|---|---|---|
| A — ABL FDT / memory / EFI handoff | | | | | |
| B — PM8150 physical input parents | | | | | |
| C — MMCX→MX ARC/corner equivalence | | | | | |
| D — boot-v2 / ramdisk / DTBO / AVB | | | | | |

状态只能使用：`PASS`、`PARTIAL`、`UNKNOWN`、`BLOCKED`、`NOT APPLICABLE`。对每个 `BLOCKED`/`UNKNOWN` 写明是哪项具体事实缺失、证据属于本地固件还是公开源码、谁有能力取得；不能用推测补齐。

最后必须给出四个明确回答：

1. **是否应继续 ROUND135 R3？** 正常预期为继续，除非你发现候选身份/源码层面可证伪的问题；不得仅因启动门槛未关闭而阻止 Image 编译。
2. **R3 PASS 后能宣称什么？** 必须将离线编译/DTB 通过与硬件启动区分。
3. **首次实机启动前的最短闭环顺序是什么？** 按依赖关系排序，不列泛泛愿望清单。
4. **哪些环节必须新开 WorkBuddy Agent 本地只读取证？** 给出精确输入、采集点、输出字段、禁止操作；只提出建议，不自行启动 Agent 或把工作转派给 Agent。

## 6. 证据引用与审查质量

- 每个重要结论必须引用现有报告的文件路径 + blob SHA + 章节/表格；同时给出对应固定 ACK 源文件、函数/符号及行号（涉及 ACK 行为时）。
- 区分证据等级：`TARGET-LOCAL HOS4.3`、`PINNED ACK SOURCE`、`SAME-DEVICE PUBLIC REFERENCE`、`SAME-SOC REFERENCE`、`INFERENCE`。
- 明确写出否定证据覆盖范围。比如“在某个 base-FDT 全量属性扫描里没有发现”不等于“所有 bootloader runtime state 不存在”。
- 有冲突时记录原始口径、后续更正轮次和采用理由。特别注意 reserved-memory 旧统计 34 与 ROUND24 后的 37，不得重复旧数字。
- 不得将历史 unknown 改写成 pass；不得把没有报告的工具/本地数据视为不存在；不得将同一设备开源参考当成 Huawei HOS4.3 的直接证据。

## 7. 禁止事项与安全边界

- 绝对只读；不得修改任何内核源码、DTS、Kconfig、补丁、manifest、R3 taskbook、R3 输出或 AI1 分支。
- 不得执行 `git apply`、编译、刷机、打包、AVB signing、分区写入或运行任何设备操作。
- 不得请求或操作用户平板，不使用 USB/ADB/fastboot/recovery/serial，不访问 bootloader shell。
- 不下载/解包新的本地 HOS4.3 固件或补采敏感数据；仅使用仓库已存在的脱敏报告与可公开取得的源码。
- 不得要求 WorkBuddy Agent 暂停 ROUND135 R3，也不得把本任务内容混入 Agent 的 R3 执行任务。
- 本任务唯一允许的仓库写入，是在本分支提交 ROUND136 审查报告及必要的短小证据索引；不做 cherry-pick、merge 或 PR。

## 8. 交付与停止规则

在本分支新增：

`firmware-analysis/round136-preboot-blocker-audit/AI2_ROUND136_PREBOOT_BLOCKER_AUDIT.md`

报告至少包含：执行范围、固定输入身份、证据差异表、A/B/C/D 四项结论、编译/DTB/实机启动门槛矩阵、最短闭环顺序、需要 1号 AI 决策的问题、需要本地 Agent 的下一步只读采集建议、完整来源索引。

提交后执行文件 readback，确认内容与 blob SHA，并在报告末尾或单独小节记录 commit SHA / report blob SHA。完成后停止，不自行接续设计实现。

**本 ROUND136 的成功标准不是把所有门槛写成 PASS，而是准确分离“内核可编译”“DTB 可编译”“能安全尝试首次启动”三种状态，并为每个未关闭门槛给出最短、可审计的证据闭环。**
