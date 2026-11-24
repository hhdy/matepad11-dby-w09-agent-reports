# PROJECT_HANDOFF.md — DBY-W09 GKI 6.18.33 → Android 17 DerpFest 总交接

更新：2026-11-24  
适用：新 ChatGPT 会话、GPT 上游源码研究、本地 Agent 只读固件检查、内核与 ROM 移植规划。

> **新会话必读：先读本文件，再读根目录 `AGENT_TASK.md`。本文件是项目目标、阶段顺序和反复调查事项的权威交接入口。不要重复询问已确认的目标，也不要把历史参考项目误作当前目标。**

## 1. 最终目标与严格阶段顺序

设备：Huawei MatePad 11 2021，型号 DBY-W09，Qualcomm KONA / SM8250 v2.1 / Snapdragon 865。

用户确认的最终目标：在该平板上运行 Android 17 DerpFest，底层使用移植到 DBY-W09 的 ACK/GKI 6.18.33 内核。

**严格按以下顺序执行，不能颠倒，也不能把两阶段混在一起：**

### 阶段 A — 先移植并验证 6.18.33 GKI/ACK 内核

这是当前唯一主线。

1. 以 Android Common Kernel / ACK 的 `android17-6.18` 源码体系为基础，目标版本按 6.18.33 对齐。
2. 先完成 DBY-W09 的内核适配：SM8250 板级 DTS、PM8150/PM8150L、RPMh/GenPD、UFS/QMP PHY、时钟、复位、interconnect、SMMU、内存与 reserved-memory、UART/调试、旧版 ABL 启动链及镜像格式。
3. 完成对应 Kconfig、必要驱动补丁、模块/内建策略和设备树验证。
4. 先建立可重复的内核构建产物，完成内核启动路径与设备上的启动验证。内核验证所用测试环境/ramdisk/ROM 基线需先审查 boot chain 和 AVB 事实后决定，不要未经验证就假定 Android 17 系统已准备好。
5. 阶段 A 的验收目标是：设备能够加载并运行这个 6.18.33 内核，启动路径可重复、关键存储和基础设备可验证，内核日志/启动状态有可审查证据。仅成功编译、生成 Image 或写好 DTS 不算“内核移植完成”。

阶段 A 未通过验收前，不进入完整 DerpFest 设备移植，不把 Android 17 userspace/HAL 集成当作当前主要工作。

### 阶段 B — 内核完成后，再移植 Android 17 DerpFest

阶段 A 验收后才开始。

1. 以 DerpFest Android 17 manifest 为系统源码基线。
2. 新建/完善 DBY-W09 device tree、vendor tree、必要 proprietary blobs、VINTF manifest/matrix、SELinux、fstab、init、产品配置和 lunch target。
3. 将阶段 A 已验证的 DBY-W09 6.18.33 内核与 DerpFest 的 boot/ramdisk/vendor_boot 预期结构正确集成；必须遵循设备实际的 ABL header-v2 + 独立 ramdisk 布局，不能照抄现代具有 vendor_boot/init_boot 的设备。
4. 处理 Android 17 与 HOS4.3 Vendor/HAL 的跨版本兼容，优先用可验证的 VINTF、HAL、模块和启动证据解决问题。
5. 首先实现可进入 Android 17 DerpFest 桌面，再逐项补齐触控、显示、GPU、音频、相机、Wi-Fi/蓝牙、休眠、电池/充电等功能。

### 阶段 C — 后续 ROM

Android 17 DerpFest 稳定后，才评估 ColorOS 或其他 Android ROM。ColorOS 不是当前阶段任务。

## 2. 已调查的历史参考：Android 12L（不要重复当作目标）

同型号 DBY-W09 的 Android 12L / API32 研究已经查过多次，主要公开资料：

- https://github.com/glasses666/dby-w09-boot-research

用途：同一设备的启动链、Vendor、VINTF/GNSS、音频和硬件适配历史参考。遇到具体 HAL、VINTF、boot-chain 或硬件问题时，可针对性复用已有证据。

**明确结论：Android 12L 不是当前目标 ROM，不是阶段 A，也不是阶段 B。不要重新介绍它作为主要路线，不要重复做“这台平板能否运行 Android 12L”的搜索。** 用户没有提出新的 Android 12L 专项问题时，只按需引用，不重复调研。

其他同设备 Linux 项目也仅用于设备树、硬件和启动链交叉参考，不改变 Android 17 DerpFest 目标：
- https://github.com/svesnav/linux-dby-w09
- https://github.com/CoWave-Fall/linux-on-arm-matepad11

## 3. 上游基线与版本控制注意事项

- DerpFest Android 17 manifest：https://github.com/DerpFest-AOSP/android_manifest/tree/17
- Manifest 初始化入口：`repo init -u https://github.com/DerpFest-AOSP/android_manifest.git -b 17 --git-lfs`
- Android 17 manifest 的 `snippets/kernel-6.18.xml` 指向 ACK common kernel 的 `android17-6.18-2026-06`，其官方 release baseline 为 6.18.21；这是 DerpFest manifest 的通用默认值，不是本项目的 6.18.33 目标。
- **ROUND28 已锁定 Stage A 的官方 ACK 源码标签：`android17-6.18.33_r00`，tag target commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`。** 不要把纯 Linux stable `v6.18.33` 标签当作 ACK 源码替代品，也不要跟踪移动的 `android17-6.18` HEAD。
- 官方 GKI release-build 页面将 2026-09 Android 17 / 6.18 certified branch 标为 6.18.32；`android17-6.18.33_r00` 是官方 ACK tag，但自定义 DBY-W09 构建是否满足 GKI KMI/ABI/certification 仍需独立验证。报告必须准确称为 ACK-derived / GKI-based，除非认证条件有证据。
- 阶段 B 构建 DerpFest 时，必须覆盖其 manifest 默认的 6.18.21 kernel 引用，集成已验证的 DBY-W09 6.18.33 Image/DTB/DTBO/模块；不能改变 Stage A 目标来迎合默认 manifest。
- 需要记录 Android common source ref、kernel Makefile 版本、补丁序列、配置来源、编译器版本、构建命令、Image/DTB/DTBO 产物身份，避免阶段 A 内核版本漂移。
- ACK-derived、GKI-based、GKI-compatible 与官方 GKI certified 是不同概念。除非实际通过对应 ABI/KMI、GKI build/validation 及模块兼容要求，不要声称官方认证 GKI。项目目标仍按用户习惯称“6.18.33 GKI 内核移植”，技术报告应注明实际构建类型与验证边界。

## 4. 设备事实（已确认）

- SoC：KONA / SM8250，SoC ID 356，revision 2.1；按 Snapdragon 865 规格，不要误写为 Snapdragon 870。
- 系统/固件：用户当前研究的是别人移植的 HarmonyOS 4.3。
- 原始内核：4.19.157-perf+。
- 启动：Android boot image header v2，独立 `ramdisk` 分区；现有采集未发现 `vendor_boot` / `init_boot`。
- 分区：具有 Android dynamic partitions / `super` 结构；vendor / odm 文件系统有 EROFS 特征。
- 固件本体、分区镜像和敏感设备标识仅保存在用户本地，不上传公开仓库。

权威本机证据位于本仓库 `round1-adb/`、`round2-adb/`、`firmware-hos43/` 和后续已审查的 ROUND 报告。

## 5. 仓库当前布局与工作边界

主仓库：https://github.com/hhdy/matepad11-dby-w09-agent-reports

- `main`：GPT 可公开完成的上游源码研究、交接文档、脱敏分析报告。
- `firmware-audit-v1`：本地 Agent 的只读固件报告分支；截至 2026-11-24 的仓库核验，该分支目前只有 ROUND11 报告，ROUND12 尚未上传，不能标记完成。
- `ack18-dby-w09-dts-draft`：ACK 6.18 板级 DTS / rootparam DTBO 草案分支。
- PR #1：保持 Draft，不得擅自合并。

协作规则：
- GPT 优先自行完成可通过公开源码、GitHub、上游文档和已有报告完成的研究、对照与设计；不要把这些任务交给本地 Agent。
- 只有必须访问用户本机文件、检查已有工具/环境、对本地固件执行只读提取或读取设备状态时，才编写本地 Agent 任务书。
- 本地 Agent 只读；不刷机、不解锁、不 root、不写分区、不执行 fastboot 写操作、不安装工具、不下载固件、不编译内核。任务书要求的工具不存在时必须 BLOCKED 并停止。
- 需要新建本地任务时，先检查 ROUND 编号和既有任务，确保不重复。当前 ROUND12 已是唯一活动本地任务。
- 未运行、未验证的步骤明确标注 NOT_RUN / BLOCKED / UNKNOWN / DESIGN ONLY。不能把源代码推理写成设备运行结论。

## 6. 已完成的内核移植研究（无需从零重做）

仓库 `kernel-baseline/round6` 至 `round27` 已有连续研究记录。重点内容：

- ROUND13：第一版 ACK 板级 DTS / 最小 rootparam overlay 设计。
- ROUND14：ACK 6.18 UFS 早期启动 Kconfig 依赖。
- ROUND15：UFS 启动依赖与 rootparam 修正。
- ROUND16：HOS4.3 RPMh ARC parent graph 与 ACK DTS 映射。
- ROUND17：ACK 6.18 GENI UART / console 区分。
- ROUND18：DBY-W09 legacy boot / ramdisk / DTBO 打包路径。
- ROUND19：HOS4.3 memory / reserved-memory handoff 风险。
- ROUND20：Android first-stage、device-mapper、EROFS 配置。
- ROUND21：ACK PM8150 VRM parent-supply 与 dummy regulator 风险。
- ROUND22：ACK RPMh ARC 与 proxy-consumer 适配可行性。
- ROUND23：ACK ARC provider 设备层级、RSC 请求上下文；UFS VCCQ parent rail。
- ROUND24：UFS VDDP REF_CLK / L6 DRMS 负载聚合；ARC 逻辑 corner 约束。
- ROUND25：UFS core 电源顺序与 VCCQ/L6 DRMS 聚合。
- ROUND26：HOS4.3 PM8150 regulator mode / DRMS 属性证据边界。
- ROUND27：ACK SM8250 UFS required-OPP 到 RPMHPD 的 GenPD 路由缺口。
- ROUND28：ACK `android17-6.18.33_r00` 源码基线、DerpFest manifest 版本冲突、Qualcomm 6.12 SoC driver delta 的借鉴边界。
- [ROUND29：ACK .33 UFS 双 GenPD / required-OPP probe 接入设计](./kernel-baseline/round29/ack-qcom-ufs-dual-genpd-required-opp-probe-integration.md)：QCOM probe 在通用 UFS init 前 attach MMCX + UFS_PHY_GDSC，显式把唯一 required-opps index 0 映射到 MMCX；只使用 `PD_FLAG_DEV_LINK_ON`，禁止对两个域使用 `PD_FLAG_REQUIRED_OPP`。已核实 RPMHPD provider 在可 attach 前先注册 indexed GenPD OPP table。方案仍未实现/编译/测试。

现有草案：
- `dts/dby-w09-ack18-board.dts.draft`
- `dts/dby-w09-ack18-rootparam.dtso.draft`
- `config/dby-w09-ack18-storage-first.fragment.draft`
- `dts/README.md`

这些仍是 DRAFT，尚未完成 dtc、dt-schema、最终 Kconfig 解析、内核编译、设备启动或硬件验证。

## 7. 当前已知关键阻塞

### 7.1 源码基线 / GKI 版本身份

ROUND28 已将阶段 A 源码固定为官方 ACK tag `android17-6.18.33_r00`，tag target commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`。DerpFest manifest 的 kernel 6.18 snippet 默认 June 2026 / 6.18.21，官方 September 2026 certified GKI release branch 为 6.18.32；两者都不能替代用户指定的 .33 ACK tag。后续需冻结完整 manifest、构建工具链、配置和模块产物身份。

SM7325 Android 17 / 6.18 参考项目展示 ACK + Qualcomm 6.12 SoC driver delta 的移植方式，但使用不同 SoC/板级硬件及 header-v4/vendor_boot 结构；只能借鉴构建及模块同步方法，不能复制 DTS、boot config 或 vendor modules。

### 7.2 UFS / RPMHPD

ROUND27 已确认：SM8250 UFS OPP 表存在 RPMHPD required-opps，但 UFS Host 当前附着 GCC UFS_PHY_GDSC。已审查的 GCC/GDSC 路径没有建立到 RPMHPD MMCX 的性能状态传播关系。因此不能把已有 required-opps 属性当成实际 MMCX vote。

ROUND29 已将设计缩小并精确到 ACK `.33_r00`：在 `ufs_qcom_probe()` 中、`ufshcd_pltfrm_init()` 之前，用 `devm_pm_domain_attach_list()` 附着 MMCX（index 0）和 GCC UFS_PHY_GDSC（index 1），仅使用 `PD_FLAG_DEV_LINK_ON`；再用 `devm_pm_opp_set_config()` 将唯一 required-opps index 0 指向第一个虚拟 GenPD 设备。通用 UFS 后续仍按原样设置 clock OPP config 并初始化 OPP table，不需要改通用 `ufshcd-pltfrm.c` 或 `ufs_hba_variant_ops`。

ROUND29 另确认 `of_genpd_add_provider_onecell()` 在注册 GenPD provider 之前先为 RPMHPD 域注册 indexed OPP table，因此 attach-list 成功后再绑定 required_dev，不会因 RPMHPD OPP table 尚未注册而触发 `-ENODEV`。这只是源码顺序证明，运行时未验证。不能对两个域使用 `PD_FLAG_REQUIRED_OPP`，因为它会把 index 1 映射到不存在的第二个 required-opps 槽位。设计报告列出剩余的 DTS order、probe defer、runtime-PM、错误 unwind、实际 vote、HOS corner 对等验证。尚未实现、编译或测试。

### 7.3 HOS4.3 ARC / proxy

ROUND11 找到 4 条 ARC level parent-supply 边和 6 条 ARC proxy-supply 边；它们属于 Vendor RPMh ARC/proxy，不是 VRM 物理输入。ACK 上游 qcom-rpmh-regulator 不等同于旧 Vendor ARC provider。不能把 vendor ARC 节点直接搬进 ACK DTS。

### 7.4 PM8150 电源输入与 DRMS

完整 base FDT 相关扫描未发现 `vdd-s1..s10-supply`、`vin-supply`、`vph-pwr-supply`。HOS4.3 L5/L6/L9 的 DRMS/allowed-modes 约束仍需 ROUND13 定向核验。不得根据 HOS4.2 参考树臆造供电或模式属性。

### 7.5 Memory / reserved-memory

HOS4.3 base FDT 未发现普通 `/memory` 节点，但有 34 个 reserved-memory 子节点。ABL 替换 DTB 的可用内存注入与保留区 handoff 未闭环，是内核设备树进入实际启动前的 gate。

### 7.6 Legacy boot / AVB / ramdisk

ROUND12 正在检查现有 boot / ramdisk / dtbo / vbmeta 的 AVB footer 和 descriptor 覆盖关系。该任务完成前，不要确定最终镜像重打包策略、dm-verity/FEC 配置或启动测试写入方案。
ROUND10 ramdisk 内容仍 BLOCKED；Android first-stage module 路径及模块目录是否可用尚未确认。UFS/QMP 因此在当前 storage-first 设计中倾向内建，但最终要以构建与启动设计审查为准。

## 8. 当前任务队列

### 本地 Agent（唯一活动任务）

- **ROUND12：只读 AVB 元数据核验**，任务书：`firmware-analysis/round12/AGENT_TASK.md`。
- 只检查现有 HOS4.3 boot / ramdisk / dtbo / vbmeta 的 footer 与 descriptor 范围。
- 仅使用本机已安装、可信、已审查工具；工具缺失则 BLOCKED。不得安装、下载、写 parser、调用 WSL 或更改安全策略。
- 报告只放脱敏文本在 `firmware-audit-v1`，完成后停止；不更新 `main`、ACK DTS 草案分支或 PR #1。

### GPT 侧（当前继续工作）

- 以 ROUND28 锁定的 `android17-6.18.33_r00` 和 ROUND29 方案继续完成 UFS 双 GenPD patch 草案、DTS binding/order 检查和 probe defer/runtime-PM 生命周期审查；方案未经编译和实机验证，不能标为完成。
- 建立可复现的 GKI-derived build config / toolchain pin；先厘清哪些 Qualcomm 6.12 SoC 平台增量是 6.18.33 ACK 里缺失的，再决定逐个回移哪些驱动。
- 继续按内核阶段 A 排序，不提前开始完整 DerpFest device/vendor tree 实施。
- ROUND12 完成后，再按既有队列审查 ROUND13 的 HOS4.3 regulator mode/DRMS 属性。
- 每一轮先读本文件和已有报告，再开展新工作；不要重新做 Android 12L 的泛化调研。

## 9. 阶段验收定义

### 阶段 A：6.18.33 内核移植完成，至少要求

- 源码 ref、版本、补丁和配置均锁定并可复现。
- DTS 编译及 schema 验证通过；Kconfig 最终配置闭环。
- Image、DTB、DTBO、boot/ramdisk 相关布局与 AVB 结构有可追溯构建记录。
- 在不破坏原系统恢复能力的受控条件下，设备能够实际启动 6.18.33 内核。
- UFS/rootfs 或 Android first-stage 所需关键存储链工作。
- 有启动日志、内核版本和关键硬件枚举证据。仅编译成功不算完成。

### 阶段 B：Android 17 DerpFest 移植完成，至少要求

- 有可重复构建的 DBY-W09 DerpFest device/vendor/product 配置。
- Vendor/HAL/VINTF/SELinux/fstab/init 与 6.18.33 内核匹配。
- 能完成 first-stage、mount、zygote、SystemServer 并进入桌面。
- 主要硬件功能逐项记录 PASS / PARTIAL / BLOCKED；不把“进入桌面”描述成所有硬件已完成。

---

**新会话的正确起点：读取 `AGENT_TASK.md`，确认 ROUND12 状态，随后继续阶段 A 的 ACK 6.18.33 内核移植。不要重新讨论 Android 12L，不要提前跳到 DerpFest 全系统适配，也不要改动 PR #1 或 ACK DTS 草案分支，除非当前任务明确授权。**
