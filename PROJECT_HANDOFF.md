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
- 分区：具有 Android dynamic partitions / `super` 结构。vendor / odm 曾有 EROFS 相关初步迹象，但当前 EROFS filesystem/content 识别仍 BLOCKED；不得当作已验证的文件系统结论。
- 固件本体、分区镜像和敏感设备标识仅保存在用户本地，不上传公开仓库。

权威本机证据位于本仓库 `round1-adb/`、`round2-adb/`、`firmware-hos43/` 和后续已审查的 ROUND 报告。

## 5. 仓库当前布局与工作边界

主仓库：https://github.com/hhdy/matepad11-dby-w09-agent-reports

- `main`：GPT 可公开完成的上游源码研究、交接文档、脱敏分析报告。
- `firmware-audit-v1`：本地 Agent 的只读固件报告分支；ROUND11、ROUND12、ROUND13 脱敏报告均已上传。ROUND12 因无可信 AVB 工具 BLOCKED，未解析 footer / vbmeta descriptor，覆盖关系仍 UNKNOWN；ROUND13 mode/DRMS 审计已完成，详见其报告与 ROUND48。
- `ack18-dby-w09-dts-draft`：ACK 6.18 板级 DTS / rootparam DTBO 草案分支。
- PR #1：保持 Draft，不得擅自合并。

协作规则：
- GPT 优先自行完成可通过公开源码、GitHub、上游文档和已有报告完成的研究、对照与设计；不要把这些任务交给本地 Agent。
- 只有必须访问用户本机文件、检查已有工具/环境、对本地固件执行只读提取或读取设备状态时，才编写本地 Agent 任务书。
- 本地 Agent 只读；不刷机、不解锁、不 root、不写分区、不执行 fastboot 写操作、不安装工具、不下载固件、不编译内核。任务书要求的工具不存在时必须 BLOCKED 并停止。
- 需要新建本地任务时，先检查 ROUND 编号和既有任务，确保不重复。ROUND12 已上传并按工具门槛 BLOCKED；firmware-analysis ROUND13 已上传完成；当前本地 Agent 队列为空。ROUND13 与历史 kernel-baseline/round13 ACK DTS 设计属于不同目录/工作流。
- 未运行、未验证的步骤明确标注 NOT_RUN / BLOCKED / UNKNOWN / DESIGN ONLY。不能把源代码推理写成设备运行结论。

## 6. 已完成的内核移植研究（无需从零重做）

- ROUND31：ACK .33_r00 UFS/QMP/SM8250 GCC/RPMh/GenPD/ICC/SMMU/DM/EROFS Kconfig 依赖闭环；storage-first fragment 的隐藏依赖注释已更新，最终 Kconfig 解析仍 NOT_RUN。
- [ROUND33：SM8250 UFS 双 GenPD driver patch 草案](./kernel-baseline/round33/sm8250-ufs-dual-genpd-patch-design.md)：在 `ufs_qcom_probe()` / 通用 init 前，仅对双域 MMCX→GCC UFS_PHY_GDSC 拓扑 attach domains，并将 UFS 唯一 `required-opps` slot 0 映射到 MMCX；保留单域路径。ROUND38 已加强检查：不仅验证目标 provider compatible，还解析其 `operating-points-v2`，要求它与 required-OPP 节点所在表是同一个 DT node。当前 ACK `ufs-qcom.c` 源 blob `a80c6998406dbc88c25dbd9977699ba481207efe`、更新后的 patch blob `565090acbfe9aad00200b3cccbd64a8a45c7c4c3`；include/probe 两个 hunk 的旧侧上下文和行数均 PASS。仍未完整工作树 `git apply`、checkpatch、编译或实机验证。
- [ROUND34：ROUND33 UFS 双 GenPD 补丁的固定 ACK 源码与生命周期审查](./kernel-baseline/round34/round33-pinned-source-lifecycle-review.md)：按 `android17-6.18.33_r00` 精确复核 GenPD 多域自动附着规则、attach-list 返回值与 `PD_FLAG_DEV_LINK_ON` 链路标志、OPP required-dev 的初始化时序、多次 OPP config token 不互相覆盖，以及 devres 逆序清理。审查未发现已核实的 API/生命周期冲突；这只是源码审查通过，不代表补丁已应用、编译或设备验证。
- [ROUND35：DBY-W09 UFS 双 GenPD 的 DTS 集成缺口](./kernel-baseline/round35/dby-w09-ufs-dual-genpd-dts-integration-gap.md)：实际读取 `ack18-dby-w09-dts-draft` 上的板级 DTS 后确认，`&ufs_mem_hc` 只补 rails/status，没有覆盖 `power-domains`；因此继承单个 GCC `UFS_PHY_GDSC`，ROUND33 helper 会按兼容逻辑走单域返回路径，MMCX 映射尚未集成。提出下一版 DTS 需要 MMCX index 0 + GCC GDSC index 1；仅写入 main 报告，没有修改 DTS 草案分支。
- [ROUND36：SM8250 UFS 双域 binding 数量约束](./kernel-baseline/round36/sm8250-ufs-power-domain-schema-limit.md)：固定 ACK commit `8ad08f...` 的 `qcom,ufs-common.yaml` 将 `power-domains` 限为 `maxItems: 1`。已新增 compatible-scoped schema patch，仅允许 `qcom,sm8250-ufshc` 最多两个域，其他 Qualcomm UFS 仍最多一个。最终 patch blob SHA `dad87ef8dfefee6141b8a7949982c007c4a03b4a`；目标文件本地测试副本的 Git blob SHA 与上游精确匹配 `962dffcd28b44b3489be5615c75e7270a0c45dc4`，ROUND36 在单文件精确 blob fixture 上 `git apply --check`、`git apply`、`git diff --check` 均 PASS；PyYAML 解析通过，独立 JSON Schema Draft 7 条件逻辑测试通过（SM8250 允许 1/2 个域、拒绝 3 个；其他 UFS 允许 1 个、拒绝 2 个）。另外将 patched ROUND32 `qcom,ufs.yaml` 与 ROUND36 `qcom,ufs-common.yaml` 的相关条件合并做 JSON Schema Draft 7 测试：SM8250 八 clocks/单 reg/two domains 和旧单域场景通过；三域、九 clocks、错误第八时钟名、双 reg，以及非 SM8250 双域均按预期拒绝。此结果不是 dt-schema 规范验证或完整 ACK 工作树验证；dt_binding_check/dtbs_check 尚无工具运行，ROUND33 也未作全树 git apply。
- [ROUND37：DBY-W09 UFS Host 双 GenPD board DTS delta](./kernel-baseline/round37/dby-w09-ufs-dual-genpd-board-dts-delta.md)：新增独立 DTS patch draft，仅给 `&ufs_mem_hc` 增加 MMCX index 0 + GCC `UFS_PHY_GDSC` index 1，并显式 include 两个 domain ID 头文件。patch blob `486654c8d0b1b785190253270f5e83f796f07362`；受保护 DTS 文件 blob `e86c8707c413a9376b1e332a94e292b86acde3e2`。完整源文件与补丁均在本地复建并完成 SHA 精确匹配；临时单文件 fixture 上 `git apply --check`、`git apply`、`git diff --check` 均 PASS。仅未应用到 GitHub 受保护分支，未 dtc/schema 验证。
- [ROUND38：UFS dual-GenPD patch series manifest](./kernel-baseline/round38/ufs-dual-genpd-patch-series-manifest.md)：汇总固定 ACK 基线、四份补丁的 SHA / 依赖顺序、两文件 schema series apply PASS 证据，以及 full-tree / dt-schema / DTB / Kconfig / build / device gates。
- [ROUND39：ACK 6.18.33 Kleaf 构建基线与工具链锁定](./kernel-baseline/round39/ack-6.18.33-kleaf-build-toolchain-baseline.md)：固定 tag 的 legacy build.config.gki.aarch64 已是 error stub，应使用 Kleaf/Bazel；锁定 KMI gen5、Clang r584948c、Rust 1.91.1.p3；比较 pinned BUILD.bazel 的 `yukawa` full-image 与 `db845c`/`wonder` mixed target。经 ROUND41 确认默认采用 no-`base_kernel` full custom kernel_build，storage fragment 放在 `post_defconfig_fragments`；进一步核实现代 Kleaf 用独立 `rules_devicetree` 编译 DTB/DTBO、`dtbo_image` 打包 DTBO 分区，不假定 vendor_boot。尚未 repo sync、query、Kconfig 或 build。
- [ROUND38：RPMhPD provider 注册与 UFS OPP table identity 审查](./kernel-baseline/round38/rpmhpd-provider-registration-and-ufs-opp-table-identity.md)：固定源码证明 MMCX 域存在、provider 在 OPP table 建立后才注册、attach-list 延迟探测失败会回滚已附着域；并把 ROUND33 驱动补丁强化为校验 required-opps table 与 provider operating-points-v2 phandle 完全同一。
- [ROUND40：UFS VCCQ-parent / VDDP 供电生命周期审查](./kernel-baseline/round40/ufs-vccq-parent-vddp-lifetime-and-merge-audit.md)：固定 ACK 的 generic VCCQ rails 在 Qualcomm variant exit 之后才关闭；现有供电草案若在 `ufs_qcom_exit()` 先关闭 VCCQ-parent 可能违反父子 rail 顺序。下游 VDDP 与 VCCQ-parent 管理也不同；供电草案必须分开策略并推迟 cleanup，未修改受保护分支草案。
- [ROUND41：GKI defconfig 存储驱动缺口与 full-image Kleaf 构建决策](./kernel-baseline/round41/gki-defconfig-storage-driver-gap-and-full-kernel-build-decision.md)：精确 `.33_r00` GKI defconfig 未启用 Qualcomm UFS/QMP/GCC/RPMhPD/SM8250 ICC/SMMU 驱动；而首阶段要求它们 built-in、early module loading 未证实。故默认选择不含 `base_kernel` 的 full custom `kernel_build`，参考固定 BUILD.bazel 的 `yukawa` 例子；ROUND31 fragment 应放在 `post_defconfig_fragments`，Kleaf 会对 olddefconfig 后的最终 `.config` 做配置项检查；还需单独建立设备 KMI symbol list / `kernel_abi` 目标，不能自动继承官方 GKI enforcement。未执行 Kconfig/build/ABI。
- [ROUND42：HOS4.3 内存交接与 SM8250 ABL FDT 前置条件](./kernel-baseline/round42/hos43-memory-handoff-sm8250-abl-fdt-prerequisite.md)：公开 SM8250 FreeABL/Qualcomm LinuxLoader 的标准路径会要求输入 FDT 已有 `/memory`，缺失时返回 `EFI_NOT_FOUND`；通过 UEFI RAM Partition Protocol 更新已有 `reg`，不自动创建该节点。该参考适用于另一台 SM8250 设备，不代表 Huawei HOS4.3 ABL；实际最终 FDT 仍 UNKNOWN。其可选 carveout 路径只消费已有 `/reserved-memory` no-map 子节点，不会重建 HOS4.3 的 34 个保留区。 进一步确认该参考上层除 RUMI 外会传播该错误并中止正常 Linux boot path。其路径查找可匹配唯一的 `/memory@...`，不要求字面节点名必须恰好为 `memory`。
- [ROUND43：ACK 6.18.33 classic FDT 与 EFI-stub 内存交接区分](./kernel-baseline/round43/ack-6.18.33-fdt-memory-scan-classic-vs-efi-handoff.md)：内核 classic 路径只从 FDT 的 `device_type=memory` 节点读 `linux,usable-memory`/`reg`；`/reserved-memory` 是独立保留区路径。真正通过 EFI stub 启动且 `/chosen` 带完整 `linux,uefi-system-table` + `linux,uefi-mmap-*` 时，内核可从 UEFI map 重建 memblock 并替换 DT-derived ranges。不能把 Qualcomm UEFI ABL 等同 Linux EFI-stub entry；华为 HOS4.3 实际跳转路径仍 UNKNOWN。
- [ROUND44：ROUND33 required-opps 首项检查与 ACK OPP parser 一致性](./kernel-baseline/round44/round33-required-opps-first-entry-parser-alignment.md)：固定 ACK `drivers/opp/of.c` 明确只需第一个可用 OPP entry 来发现 required-opps table/provider；后续每个 concrete OPP 的 required target 仍逐项 link。ROUND33 helper 正好沿用该语义，并验证 provider `operating-points-v2` 指向同一 table，当前无须增加逐项扫描。未 full-tree apply/build。

- [ROUND32：SM8250 UFS binding 覆盖与 schema 补丁草案](./kernel-baseline/round32/sm8250-ufs-binding-coverage-and-schema-draft.md)：固定 ACK `qcom,ufs.yaml` 漏列 `qcom,sm8250-ufshc`；补丁 blob `efe2d932da34716c631de22d89aba19730cc7f50` 与仓库草案一致，目标源 blob `1dd41f6d5258014d59c8c8005bc54f7994351a52`。在该精确单文件 fixture 上 `git apply --check`、`git apply`、`git diff --check` 均 PASS；仍未运行 dt-schema/dtbs_check，也未在完整 ACK 工作树集成。

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
- [ROUND30：ACK SM8250 MMCX→MX parent/corner 等价性门槛](./kernel-baseline/round30/sm8250-rpmhpd-mmcx-mx-parent-equivalence-gate.md)：HOS4.3 已报告 MMCX→MX ARC 父级边；ACK .33 SM8250 当前选用无 MX parent 的 plain MMCX。即使新建父级边，通用 GenPD/OPP 在当前 RPMHPD OPP 表上也只会一对一传递相同 pstate，不会自动实现 HOS dropout delta。HOS qcom,min-dropout-voltage-level 尚 UNKNOWN，不能擅自新增 parent。
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

ROUND32 已完成单文件精确源 apply 核验，并与 ROUND36 在同一个临时两文件树中按序应用通过：源 blob SHA 分别为 `1dd41f6d...` / `962dffcd...`，补丁 SHA 分别为 `efe2d932...` / `dad87ef8...`；两次 `git apply --check`、实际 `git apply` 和组合 `git diff --check` 均 PASS。PyYAML 解析与相关 JSON Schema 条件逻辑测试通过；仍未运行完整 dt-schema / dt_binding_check / dtbs_check。

ROUND30 的父级对照另发现：HOS4.3 已报告 MMCX ARC → MX ARC parent-supply 边，但 ACK .33 的 SM8250 RPMHPD descriptor 只为 CX 设置 MX parent，MMCX 使用无 parent 的 plain descriptor。若增加 MMCX→MX GenPD 层级，通用 GenPD 会通过 dev_pm_opp_xlate_performance_state() 换算父域 pstate；当前所有 RPMHPD 域使用同一 OPP enum 表且无 required-opps 转换时，helper 原样传递同一个 pstate，并不自动实现 HOS min-dropout delta。HOS 的 qcom,min-dropout-voltage-level 仍 UNKNOWN / NOT_CAPTURED，因此不能直接添加 parent pointer，须把 MMCX→MX corner equivalence 单独列为阻塞项。

### 7.3 HOS4.3 ARC / proxy

ROUND11 找到 4 条 ARC level parent-supply 边和 6 条 ARC proxy-supply 边；它们属于 Vendor RPMh ARC/proxy，不是 VRM 物理输入。ACK 上游 qcom-rpmh-regulator 不等同于旧 Vendor ARC provider。不能把 vendor ARC 节点直接搬进 ACK DTS。

### 7.4 PM8150 电源输入与 DRMS

完整 base FDT 相关扫描未发现 `vdd-s1..s10-supply`、`vin-supply`、`vph-pwr-supply`。ROUND13 已完成 HOS4.3 S4/L5/L6/L9/L17/S8 mode/DRMS 字段核验；ROUND48 已基于公开 SM8250 KONA vendor header/driver 映射其旧 vendor enum，并更新 main 分支 review DTS。DTBO entry selection 与 effective post-overlay 仍 UNKNOWN；不得根据 HOS4.2 参考树臆造供电或模式属性。

### 7.5 Memory / reserved-memory

HOS4.3 base FDT 未发现普通 `/memory` 节点，但有 34 个 reserved-memory 子节点。ROUND42 对照公开 SM8250 FreeABL LinuxLoader 发现：标准路径要求传入 FDT 已存在 `/memory`，只用 UEFI RAM Partition Protocol 更新其 `reg`，缺失则返回 `EFI_NOT_FOUND`；不创建该节点。故不能假定 ABL 会补 `/memory`。但该项目是另一台 SM8250 设备，并非 Huawei HOS4.3 ABL，真正 post-overlay/post-ABL FDT 仍 UNKNOWN。其 no-map carveout 机制只处理输入树已有 `/reserved-memory` 节点，不重建 HOS4.3 的 34 个子节点。内存范围与保留区语义未闭环，是内核 DTB 编译/启动前 gate。见 ROUND19 / ROUND42。 该参考中缺失/不可解析的 memory node 会沿 LoadAddrAndDTUpdate 返回，非 RUMI 平台的上层启动路径会中止；FdtPathOffset 的查询允许唯一 memory@unit-address 节点解析，并非字面名称强制。 ROUND43 补充了 ACK EFI-stub 例外：只有实际通过 Linux EFI stub 入口启动，并由 stub 向 `/chosen` 写入完整 UEFI memory-map 元数据时，内核才会从 UEFI map 重建 memblock；仅仅运行在 UEFI ABL 上不等于使用该路径。华为实际采用 classic 还是 EFI-stub 入口仍 UNKNOWN。

### 7.6 Legacy boot / AVB / ramdisk

ROUND12 已上传但在工具门槛 BLOCKED：本机没有可信已安装 avbtool / 已审查 AVB helper，boot / ramdisk / dtbo footer 与 vbmeta descriptor 覆盖关系均 UNKNOWN。不得从 `AVB0` magic 或文件大小推断。最终镜像重打包策略、dm-verity/FEC 配置和任何启动测试写入方案仍受 AVB gate 阻塞。
ROUND10 ramdisk 内容仍 BLOCKED；Android first-stage module 路径及模块目录是否可用尚未确认。UFS/QMP 因此在当前 storage-first 设计中倾向内建，但最终要以构建与启动设计审查为准。

## 8. 当前任务队列

### 本地 Agent（当前无活动任务）

- **ROUND12：已交付 / BLOCKED**。报告：`firmware-analysis/round12/round12_avb_metadata_findings.txt`。无可信已安装 AVB 工具，未做 footer / descriptor 解析；不重复执行，AVB gate 保持 UNKNOWN。
- **firmware-analysis ROUND13：已完成 / 已上传**。报告：`firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt`；本地 Agent 按要求只上传脱敏文本并停止，不得重跑或要求再次解析 FDT。
- 当前本地 Agent 队列为空。只在新的问题必须依赖本机已有工作副本或可信本地工具、且相关工具确实已存在时，才创建新的只读任务；不得为了推进而创建无有效输入的任务。
- 不得安装、下载、写 parser、调用 WSL 或更改安全策略。报告只放脱敏文本在 `firmware-audit-v1`；不更新 `main`、受保护 ACK DTS 草案分支或 PR #1。

### GPT 侧（当前继续工作）

- ROUND38 已整理 UFS dual-GenPD 补丁序列；ROUND32/36 schema patch pair 与 ROUND37 DTS patch 均通过精确源文件 fixture 的真实 apply 检查，ROUND33 driver 只有 hunk/source-context 核验且已增加 exact OPP-table identity 检查。ROUND39 已锁定 ACK `.33_r00` 的 Kleaf/Bazel 构建入口和工具链常量：KMI gen5 / Clang `r584948c` / Rust `1.91.1.p3`。ROUND40 发现 VCCQ-parent/VDDP companion sketch 的 teardown 顺序风险，未合并前要先重构。ROUND41 对照精确 `gki_defconfig` 与 Kleaf BUILD target 后确定：因 storage-first 要求 Qualcomm UFS/QMP/GCC/RPMhPD/ICC/SMMU built-in、早期 ramdisk module loading 未证实，默认应新增不含 `base_kernel` 的 full-image custom `kernel_build`，按 `yukawa` 例子构建；ROUND31 fragment 应放在 `post_defconfig_fragments`，Kleaf 在 `make defconfig` 后应用、执行 `olddefconfig` 并检查 final `.config`；full `yukawa` 模式本身不自动提供设备 KMI enforcement，后续还需设备专属 `kmi_symbol_list` + `kernel_abi`。ROUND39 进一步核实当前 Kleaf 使用独立 `rules_devicetree` `dtb()/dtbo()` 编译设备树、`dtbo_image` 封装 DTBO 分区；不要把 `dtbs` 塞进 `kernel_build.make_goals` 或假定设备需要 vendor_boot。mixed build 仅作早期模块加载经验证后的条件备选。下一阶段先保存 `repo manifest -r`，取得完整 ACK worktree/toolchain，在 disposable tree 应用 UFS 双域系列、重构供电补丁，再跑 dt-schema、DTB、Kconfig、编译和设备验证。局部测试绝不等于内核已可启动。 ROUND42 对照另一台 SM8250 设备使用的 FreeABL LinuxLoader：标准 ABL 路径不是自动创建 `/memory`，而是要求输入 FDT 已有该节点，缺失时会报 EFI_NOT_FOUND；仅后续用 UEFI RAM Partition Protocol 改写 reg。不能再把“ABL 一定会补 memory 节点”作为设计假设，需取得 Huawei HOS4.3 最终 post-ABL FDT 或准确 ABL 源码。其 no-map carveout 操作也依赖已有 reserved-memory children。 ROUND43 又对照 ACK 内核实际扫描代码，确认 classic FDT 路径只认带 `device_type=memory` 的根节点及 `linux,usable-memory`/`reg`，`/reserved-memory` 不能代替；若真实走 EFI stub 并带完整 `/chosen/linux,uefi-*` 元数据，则 EFI memory map 是另一种内存来源。华为实际 kernel entry path 仍待证据确认。
- 以 ROUND31 的 Kconfig 依赖闭环为起点，对冻结的 GKI base config + board fragment 做真正的 olddefconfig / 最终 .config 解析（在工具链/源码可用时），并逐项核验最终 built-in 状态；不能把 Kconfig 理论关系当成 resolver PASS。
- 建立可复现的 GKI-derived build config / toolchain pin；先厘清哪些 Qualcomm 6.12 SoC 平台增量是 6.18.33 ACK 里缺失的，再决定逐个回移哪些驱动。
- 继续按内核阶段 A 排序，不提前开始完整 DerpFest device/vendor tree 实施。
- ROUND12 AVB 检查已上传并 BLOCKED；ROUND13 mode/DRMS 核验已完成，ACK 侧语义与 DTS 决策见 ROUND47/ROUND48。后续可由 GPT 继续固定 ACK / 公共源码研究；本地 Agent 队列为空。
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

**新会话的正确起点：先读本文件及 `AGENT_TASK.md` 末尾的最新状态。ROUND12 为 BLOCKED、ROUND13 已完成、本地 Agent 队列为空。继续由 GPT 独立完成可从固定 ACK / 公共源码推进的阶段 A 工作；只有确实需要本机已有副本或工具时才新建只读 Agent 任务。不要重新讨论 Android 12L，不要提前跳到 DerpFest 全系统适配，也不要改动 PR #1 或受保护 ACK DTS 草案分支，除非用户明确授权。**


## 10. Latest progress — ROUND44 UFS dual-GenPD probe contract review

Updated: 2026-11-24.

ROUND44 re-read the exact immutable ACK source commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a and verified the proposed ROUND33 UFS probe sequence against the fixed APIs:

- Generic genpd_dev_pm_attach() skips consumers with multiple power-domains entries; it does not bind one domain to the original UFS device. A driver-level devm_pm_domain_attach_list() call in the Qualcomm UFS probe is therefore compatible with the generic core path.
- dev_pm_domain_attach_list() creates indexed virtual-domain devices, returns the attached count, and PD_FLAG_DEV_LINK_ON adds runtime-active device-link behavior. Two attached domains is the expected success count.
- ufs_qcom_probe() invokes ufshcd_pltfrm_init(). The generic UFS OPP setup configures clocks and then adds the OPP table, so ROUND33's required_dev mapping before ufshcd_pltfrm_init() is correctly ordered.
- The pinned SM8250 UFS OPP table currently has two available entries, both with exactly one required-opps reference. The proposed slot-0 mapping to MMCX matches this fixed-source shape.
- The existing ROUND33 exact required-OPP target / provider operating-points-v2 table identity check is useful and must remain.

ROUND44 found two ROUND33 hardening requirements before full-tree application:
1. The helper checks only the first available UFS OPP entry. Revise it to iterate all available OPP children and validate exactly one required-opps entry, RPMhPD provider compatible, and exact provider OPP-table identity for every entry; also handle an empty table and OF reference cleanup.
2. The current compatible/count guard applies to every qcom,sm8250-ufshc with two domains, not just DBY-W09. Decide whether this exact MMCX-then-GCC two-domain contract is intentionally driver-wide, or add a deliberate board opt-in mechanism. Do not silently accept an unknown two-domain layout, because generic GenPD skips attaching both domains.

ROUND30's MMCX-to-MX parent/corner equivalence remains a separate unresolved power-tree gate. ROUND42/43 final memory handoff and ROUND12 AVB inspection remain open. No full kernel tree was applied, no checkpatch/dt-schema/Kconfig/Kleaf build was run, and no device was tested.

Full report: kernel-baseline/round44/ack-ufs-dual-genpd-probe-contract-review.md

Next sequence: harden ROUND33, maintain the ROUND38 patch order (ROUND32 schema → ROUND36 common binding → ROUND37 board DTS → ROUND33 driver), then run complete disposable-tree patch/schema/DTB/Kconfig/build checks only after the AVB and memory/boot-chain gates are addressed. ROUND12 remains the only active local Agent task. Stage B DerpFest work remains deferred until Stage A 6.18.33 actually boots and passes storage/basic-hardware validation.


## 11. Latest progress — ROUND45 all-entry UFS OPP validation hardening

Updated: 2026-11-24.

ROUND45 revised the ROUND33 UFS dual-GenPD driver draft:
- New helper validation iterates every available child OPP in the UFS OPP descriptor table; it no longer checks only the first available entry.
- Every available entry must have exactly one required-opps phandle; the target must exist and be available, belong to an operating-points-v2 table whose parent is qcom,sm8250-rpmhpd, and match the provider's sole operating-points-v2 table by exact device-tree node identity.
- OF node references are released on the success and error paths; an empty available OPP table is rejected.
- The support policy is now explicit: the one-domain generic path remains unchanged; the only currently supported SM8250 UFS two-domain layout is MMCX index 0 plus GCC UFS_PHY_GDSC index 1; other multi-domain layouts fail closed because generic GenPD skips automatic attachment for multi-domain consumers.

Updated ROUND33 patch:
- path: kernel-baseline/round33/0001-scsi-ufs-qcom-sm8250-dual-genpd-required-opp.patch.draft
- Git blob SHA: 2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5
- 205 insertions.
- Both unified-diff hunks were re-counted and compared with the exact pinned ACK ufs-qcom.c at commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a: include hunk 12 old / 18 new; probe/helper hunk 15 old / 214 new. Both count checks and old-side source-context comparisons PASS.

This is not full-tree git apply, checkpatch, C compilation, dt-schema, DTB, Kconfig, Kleaf or device validation. ROUND45 report: kernel-baseline/round45/ack-ufs-dual-genpd-all-opp-validation.md.

ROUND30 MMCX-to-MX, ROUND42/43 Huawei final memory handoff, ROUND12 AVB and ROUND40 UFS companion-supply teardown remain separate open gates. ROUND12 remains the only active local Agent task. No protected DTS branch, firmware audit branch or PR #1 was modified. Stage B DerpFest work remains deferred until Stage A 6.18.33 actually boots and passes storage/basic-hardware acceptance.


ROUND45 supplemental Kconfig call-site review against the exact .33_r00 source confirmed the new helper's OPP/GenPD API dependencies are covered by the planned fragment chain: SCSI_UFSHCD → PM_DEVFREQ → PM_OPP; SM_GCC_8250 → QCOM_GDSC → PM_GENERIC_DOMAINS (when PM=y); PM_GENERIC_DOMAINS_OF is auto-enabled with OF; QCOM_RPMHPD depends on QCOM_RPMH + QCOM_COMMAND_DB, both already requested. drivers/Makefile also includes the pmdomain subtree under PM_GENERIC_DOMAINS. No additional direct config symbol was identified, but final Kleaf .config resolution remains NOT_RUN.


## 12. Latest progress — ROUND46 ACK OPP parser contract cross-check

Updated: 2026-11-24.

ROUND46 rechecked the exact pinned ACK `drivers/opp/of.c` and `drivers/opp/core.c` source blobs against the current ROUND45 UFS dual-GenPD patch:

- `dev_pm_opp_of_get_opp_desc_node()` resolves the device's first `operating-points-v2` phandle and returns a referenced descriptor node.
- `_opp_table_alloc_required_tables()` uses the first available OPP child to determine the table-level `required_opp_count`; this is table-shape discovery, not a per-entry consistency check.
- `_of_opp_alloc_required_opps()` subsequently processes every concrete OPP entry using that previously established count and links the corresponding `required-opps[i]` target. Missing or invalid per-entry targets therefore surface during per-entry parsing/linking.
- ROUND45's current ROUND33 preflight is intentionally stricter: it iterates every available UFS OPP child and requires exactly one valid MMCX provider target for every entry before OPP table initialization. This is consistent with the parser's single-slot contract and catches malformed later entries before generic OPP setup.
- `_opp_set_required_dev()` bounds-checks `required_dev_index` against `required_opp_count`; index 0 matches the one-slot preflight. The GCC UFS_PHY_GDSC remains attached as a separate power domain and is not mapped to a nonexistent second required-opps slot.
- `devm_pm_opp_set_config()` returns 0 on successful managed-action registration; ROUND33's `if (ret)` handling is correct.

Exact pinned source blobs:
- `drivers/opp/of.c`: `505d79821584e28f454dae673cf85078762b2ec7`.
- `drivers/opp/core.c`: `157c84b689feba9ae2c446083e42de63e94a38a6`.

Report: `kernel-baseline/round46/ack-opp-required-opps-parser-contract-review.md`.

**Decision:** no ROUND33 patch change is required from this parser-contract review. Keep ROUND45's all-entry validation. This remains static source review only: full-tree apply, checkpatch, compiler, final Kconfig, dt-schema, DTB, Kleaf build, runtime probe and device boot remain NOT_RUN.

ROUND12 remains the only active local Agent task; its report is not yet present on `firmware-audit-v1`. ROUND30 MMCX-to-MX, ROUND42/43 actual memory handoff, and ROUND40 VCCQ-parent/VDDP teardown remain independent open gates. No protected branch, PR #1 or device was changed. Stage B DerpFest remains deferred until Stage A 6.18.33 boots and passes storage/basic-hardware acceptance.


## 13. Latest progress — ROUND47 ACK PM8150 regulator mode / DRMS capability review

Updated: 2026-11-24.

ROUND47 reviewed the exact ACK `android17-6.18.33_r00` driver, regulator core, OF parser and binding against the current DBY-W09 UFS rail map.

Key source conclusions:
- `regulator-initial-mode` is mapped and applied once during regulator registration; it is not a dynamic load policy.
- `regulator-allowed-modes` populates the valid mode mask and allows mode changes.
- `regulator-allow-set-load` enables the DRMS permission bit, but cannot add callbacks unsupported by the selected PMIC HW-data ops. The binding requires it together with `regulator-allowed-modes`.
- PMIC5 LDO HPM maps to `REGULATOR_MODE_NORMAL`, LPM to `REGULATOR_MODE_IDLE`. The PMIC5 SMPS mapping differs: HPM maps to FAST/PWM, AUTO to NORMAL, LPM to IDLE/PFM.
- PM8150 L5/L6/L9 map to `pmic5_nldo` with `get_optimum_mode + set_mode` and a 30 mA HPM threshold.
- PM8150 L17 maps to `pmic5_pldo` with `get_optimum_mode + set_mode` and a 10 mA HPM threshold.
- PM8150 S4 and PM8150L S8 map to `pmic5_hfsmps510` using the non-DRMS `rpmh_regulator_vrm_ops`; they have manual set_mode/get_mode but no get_optimum_mode or set_load callback. A DRMS load request on these rails can return success without automatic mode switching.
- For LDO DRMS, the core sums enabled consumer load votes plus `regulator-system-load`, selects HPM at/above the HW threshold and LPM below it, then constrains the requested mode against `regulator-allowed-modes`. The allow-list must accommodate the required HPM operating range; an LPM-only list can fail a high-load HPM request.

Current DBY-W09 board DTS draft still has HPM initial mode on PM8150 S4/L5/L6/L9/L17, but no allow-set-load / allowed-modes on those nodes. PM8150L S8 currently has no mode/DRMS attributes. These are draft settings only.

The public same-device Linux DTS used as a HOS4.2 cross-reference shows HPM initial mode on the PM8150 UFS rails, while LPM/HPM + allow-set-load appears on PM8150L L6/L9 for microSD. This is **not evidence of actual HOS4.3 settings** and must not be copied mechanically.

HOS4.3 `regulator-initial-mode`, `regulator-allowed-modes`, `regulator-allow-set-load`, `regulator-system-load` and suspend-mode properties remain UNKNOWN because ROUND7's filtered inventory did not include them. The required local ROUND13 audit (base boot FDT plus applicable stock DTBO fragments) remains queued after the sole active local ROUND12 AVB task. ROUND47 report provides the exact property checklist and ACK-side interpretation:
`kernel-baseline/round47/ack-pm8150-regulator-mode-drms-capability-review.md`.

ROUND47 is public-source review only. No local FDT/DTBO was re-parsed, and no regulator mode was read at runtime. Full-tree apply, DTS/schema, DTB, Kconfig, Kleaf build and device boot remain NOT_RUN. ROUND12 continues independently; no new Agent task was started. Stage A ACK 6.18.33 remains the only active project stage; DerpFest Stage B stays deferred.


## 14. Latest local evidence status — ROUND12 blocked; firmware-analysis ROUND13 queued

Updated: 2026-11-24.

The Local Agent uploaded `firmware-analysis/round12/round12_avb_metadata_findings.txt` to `firmware-audit-v1`. Outcome: **BLOCKED at the trusted-tool gate**:
- `avbtool` / `avbtool.py` and candidate Python modules were not present.
- Previously reviewed ROUND2/3 scripts do not parse AVB footer metadata or vbmeta descriptors.
- The bounded search stopped at the local command safety policy and was not retried.
- No footer check, original-image-size extraction, hash/hashtree descriptor listing or chain-descriptor mapping was performed.
- No tool was installed/downloaded; no WSL, security policy, device or partition action occurred.

Therefore:
- boot.img / ramdisk.img / dtbo.img file sizes are COMPLETE only as previously reported in ROUND2.
- AVB footer presence and original-image-size remain BLOCKED.
- vbmeta descriptor coverage / chained vbmeta relations remain UNKNOWN.
- Do not infer footer/descriptor state from AVB0 magic or image size; keep boot packaging and dm-verity/FEC decisions blocked.

The next local task is now `firmware-analysis/round13/AGENT_TASK.md` on `main`, distinct from the historical `kernel-baseline/round13` ACK DTS design. It reuses only the previously reviewed ROUND3 FDT parser, ROUND9 indexing approach and existing ROUND7/8 FDT/DTBO work copies. It inspects mode/DRMS/suspend properties for PM8150 S4/L5/L6/L9/L17 and PM8150L S8, retaining DTBO fragment-to-target relationships. No new parser/tool is allowed. Only a sanitized text report may be uploaded to `firmware-audit-v1`; the Local Agent must stop after upload.

GPT-side ROUND47 already records the pinned ACK 6.18.33 regulator semantics. ROUND13 will supply the missing HOS4.3 property values; it is not allowed to assume the HOS4.2 public DTS settings are HOS4.3 facts.

ROUND12 remains an unresolved AVB gate. ROUND13 does not close AVB, MMCX-to-MX, Huawei final memory handoff or VCCQ-parent/VDDP teardown gates. Stage A ACK 6.18.33 remains the only project stage; DerpFest Stage B is deferred until actual kernel boot and storage/basic-hardware acceptance.

## ROUND48 最新交接（2026-11-24）：HOS4.3 PMIC5 mode 已解析并更新主分支 DTS

ROUND13 本地 Agent 报告已上传并停止：
- 分支：`firmware-audit-v1`
- 报告：`firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt`
- upstream 属性名 `regulator-initial-mode / regulator-allowed-modes / regulator-allow-set-load / regulator-system-load` 以及 regulator-state suspend nodes 均为 `NOT_FOUND_IN_INSPECTED_SCOPE`，不是全局缺失；HOS4.3 使用 vendor `qcom,*` 属性。
- 六条关键 rail 的真实 vendor 值见 ROUND13 报告和 ROUND48。DTBO 9 个 entries 都未触碰 RSC regulator 子树，但选中 entry 未解析，effective post-overlay 仍 UNKNOWN。

ROUND48 已用公开 Qualcomm SM8250 KONA vendor source 交叉验证 mode enum，并追加核验 proxy-consumer 临时投票生命周期：
- OnePlusOSS `android_kernel_oneplus_sm8250` commit `cad09e061ef6cf689a4a1e54d27562e0f042236a` 的 `qcom,rpmh-regulator-levels.h` 定义旧 vendor enum PASS=0, RET=1, LPM=2, AUTO=3, HPM=4；同仓库 RPMh driver 和 `kona-regulators.dtsi` 对应 rail 配置与 ROUND13 的 L5/L6/L9/L17/S8 结构及原始值吻合。
- 固定 ACK `android17-6.18.33_r00` header 是另一套枚举：RET=0, LPM=1, AUTO=2, HPM=3。DTS 必须按 mode 语义转换并使用 ACK 符号常量，不能复制 HOS 的旧 vendor 数字。
- ROUND47 的 fixed ACK capability 结论不变：L5/L6/L9/L17 有 LDO DRMS callbacks；S4/S8 的 HFSMPS510 无 DRMS load callbacks。

主分支 review-only DTS 已更新：
`dts/dby-w09-ack18-board.dts.draft`
- S4：删除旧 HPM initial-mode；HOS4.3 没有 mode metadata，不再猜测。
- L5/L9：HPM initial；允许 LPM/HPM；启用 DRMS；不添加 `regulator-system-load`。ROUND48 追加核验公开 KONA `proxy-consumer.c` 后确认 100mA proxy vote 是 regulator 注册时建立、`late_initcall_sync` 在设备 probe 完成后撤销的临时启动投票，永久 system-load 会错误地把它变为常驻负载。ACK 尚无等价临时 proxy helper，故启动期 proxy 投票是明确缺口。
- L6/L17：改为 HOS 证据所示 LPM initial；允许 LPM/HPM；启用 ACK 支持的 DRMS。
- S8：HOS 为 RET/AUTO、200mA threshold、initial RET；因 ACK HFSMPS510 无 DRMS callback，且 UFS parent 最大 load vote 210mA，DTS 使用 hardware AUTO 初始模式并允许 RET/AUTO，作为保守功能回退；明确它不是 HOS software threshold policy 的等价实现，也未 runtime 验证。
- upstream property 字符串在 HOS4.3 里 NOT_FOUND_IN_INSPECTED_SCOPE，不应把它写成 HOS 实际字段；这里只是 ACK DTS 对 vendor mode policy 的翻译。

新增报告：
`kernel-baseline/round48/ack-hos43-pmic5-mode-enum-translation-and-dts-decision.md`

ROUND48 只是源码交叉比对和 DTS 文本设计更新；其中曾提出的 L5/L9 system-load 静态近似已由 proxy 生命周期审查纠正并从 DTS 移除；尚未执行 full-tree apply、dtc、dt-schema、Kconfig resolver、Kleaf、编译、打包、启动或实机验证。没有更改 `firmware-audit-v1`、受保护 `ack18-dby-w09-dts-draft` 分支或 PR #1；PR #1 保持 Draft。

当前本地 Agent 队列为空：ROUND12 已上传但因无可信 AVB 工具 BLOCKED；ROUND13 已上传完成。暂不创建新本地任务：AVB / ramdisk / EROFS 项当前仍被工具或输入门槛阻塞，其他可进行的工作优先由 GPT 通过固定 ACK / 公共源码自行完成。Stage A ACK 6.18.33 仍是唯一主线；Stage A 启动和 UFS/基础硬件验收前不启动 Stage B DerpFest。

ROUND48 proxy lifecycle correction: public Qualcomm KONA `drivers/regulator/core.c` invokes `regulator_proxy_consumer_register()` while registering each regulator; the helper applies the 100mA current/enable request. `drivers/regulator/proxy-consumer.c` removes all boot proxy requests at `late_initcall_sync`, after device probing. Therefore the temporary 100mA proxy vote on L5/L9 must NOT be converted to permanent `regulator-system-load`. The DTS draft has been corrected: no system-load properties are present; HPM initial + LPM/HPM allowed + ACK DRMS are retained, while an equivalent temporary ACK proxy helper remains an explicit boot-handoff gap. See updated ROUND48 erratum.


## ROUND49 / ROUND50 最新进展（2026-11-24）

### ROUND49 — UFS optional rails 生命周期设计
报告：kernel-baseline/round49/ack-ufs-vddp-vccq-parent-devres-lifecycle-redesign.md

固定 ACK .33_r00 与公开 SM8250 KONA UFS 驱动对照后，结论是：
- VDDP REF_CLK/L6 是真正的 UFS regulator enable 引用：设置 100µA load，然后 enable；应平衡 disable。
- VCCQ-parent/S8 在 KONA UFS 驱动里仅提交/撤销 load request，不显式 regulator_enable/disable，也不提交单独的电压 vote。不能因为属性名 parent 就擅自给它加 enable 引用。
- KONA 的 load-only 请求有重要限制：固定 KONA regulator core 只有在这个消费者 handle 的 enable_count 非零时才调用 DRMS 更新；而 UFS parent handle 本身未 enable。因此该 load vote 在没有其他使能引用/框架差异的情况下只是缓存值，不证明 S8 真的切换模式。ACK S8 又没有 set_load/get_optimum_mode，所以当前 210mA vote 明确是 no-op。
- ACK removal 顺序已精确确认：generic VCCQ 启用后才调用 Qualcomm variant；remove 时 ufshcd_hba_exit() 先调用 variant exit，再关闭 generic VCCQ；platform .remove() 返回后才走 driver-core devres release。devres LIFO 可让一个在 devm regulator-get 之后注册的 cleanup action 在 regulator_put 前执行，且在 generic VCCQ 已经关闭之后清理 optional supplies。
- 推荐 storage-first 策略：VDDP/L6 正常 set-load + enable；S8 只 load-vote、不 enable/disable/voltage-vote；二者都用延迟的 devm cleanup action 释放，且不在 ufs_qcom_exit() 里提前放掉 parent-side request。S8 初始使能与实际物理父供电仍待本机 FDT 证据。

### ROUND50 — MMCX→MX ARC 与 ACK RPMHPD 的语义差异
报告：kernel-baseline/round50/ack-sm8250-mmcx-mx-arc-parent-semantics-and-remaining-local-gate.md

公开 KONA DTS/驱动证实 vendor MMCX ARC 组把 ALL/AO 两个 child 指向不同的 MX parent child；ARC child 的 qcom,min-dropout-voltage-level 会进入 regulator descriptor 的 min-dropout，再由 regulator core 在 child voltage 之外请求 parent voltage。公共 KONA 示例在 MMCX ALL/AO child 上写 -1，但不能据此认定 DBY-W09 HOS4.3 也是 -1，也不能把它解释成未经验证的特殊枚举。

固定 ACK rpmhpd.c 的 SM8250 descriptor 用 plain MMCX/MMCX_AO，没有 MMCX→MX parent。通用 GenPD parent 传播走 OPP performance-state translation；它不是 vendor regulator parent-supply 的物理/逻辑 voltage propagation，更不会自动实现未捕获的 dropout delta 和 ALL/AO target distinctions。

因此当前不应给共享的 qcom,sm8250-rpmhpd descriptor 直接加 MMCX→MX parent：这会影响所有 SM8250 boards；也不应未经 local property proof 就新建 DBY-W09 特殊 compatible 或移植完整 ARC provider。继续保留 UFS-first ACK RPMHPD/OPP 路线，并把 ARC 等价性作为后续单独 gate。

### 新的本机证据门槛：firmware-analysis ROUND14

ROUND11 已完成 parent/proxy phandle 解析，ROUND24 明确记录 ARC provider/child 的 qcom,resource-name、qcom,set、qcom,init-voltage-level、qcom,min-dropout-voltage-level 未被既有 ROUND7 inventory capture。ROUND13 亦未检查 S8 的 qcom,init-enable / regulator boot-on/always-on 状态。ROUND49/50 的公开源码审查不能代替这些精确本机值。

**当前唯一活动本地任务改为 firmware-analysis ROUND14**：
- 任务书：firmware-analysis/round14/AGENT_TASK.md（在 main）。
- 仅用 ROUND3 原有 base FDT work copy、已审核 parser 与既有 phandle/path 索引；不重新解析 ROUND11 parent 图，不重新扫描 ROUND13 mode/DTBO 全集。
- 重点查 rpmh-regulator-mmcxlvl / rpmh-regulator-mxlvl 的资源名、ALL/AO/SO child 的 set/逻辑 corner/init/dropout/proxy 字段，以及 S8 的 qcom,init-enable / regulator-boot-on / regulator-always-on 等现有字段；只上传脱敏文本。
- 不安装工具、不下载、不写新 parser、不重提取固件、不连接设备、不写分区。按任务书一份文本上传后即停止。
- 该任务完成前，不再创建 ROUND15 或其他本地任务；GPT 仍可继续公开源码研究，但应优先使用 ROUND14 返回的 local facts 决定 ARC/S8 的最终方案。

ROUND49/50 只完成固定 ACK / 公开 KONA 源码审查与设计报告。UFS driver patch 仍未 full-tree apply、checkpatch、dt-schema、Kconfig resolver、Kleaf 编译或设备测试；MMCX→MX parent equivalence 尚未建立。ROUND12 AVB 仍 BLOCKED，ramdisk / EROFS 仍 BLOCKED，memory handoff、physical PMIC input network、UFS teardown/runtime power gates 仍独立开放。PR #1 保持 Draft，保护分支未修改。Stage A ACK 6.18.33 仍是唯一主线，Stage B DerpFest 继续等待真实启动与 UFS/基础硬件验收。


## 最新状态更正 — ROUND14 / ROUND51（2026-11-24）

### ROUND14 已完成并上传

本地 Agent 已按任务书完成并上传：
- firmware-audit-v1 / firmware-analysis/round14/round14_arc_mmcx_mx_power_properties.txt
- SHA-256 与本地一致；Git blob SHA：2a1cf742ec45b1b17c98c006da241fb7737f6fcd
- 仅复用 ROUND3 原有 base-FDT work copy、审核 parser 与 ROUND9 phandle/path index；没有重新跑 ROUND11、ROUND13 或 DTBO，也没有触碰设备、EROFS、AVB、protected DTS branch 或 PR #1。

### ROUND51 已完成公开源码语义复核并更新主分支草案

报告：kernel-baseline/round51/round14-arc-value-semantics-proxy-vote-and-round11-edge-reconciliation.md

- ARC corner: 16=RETENTION、64=LOW_SVS、384=TURBO、65535=MAX；qcom,set 1/2/3 分别为 ACTIVE/SLEEP/ALL。它们都是逻辑角点，不是物理微伏。
- min-dropout: KONA ARC parser 将 qcom,min-dropout-voltage-level 读入 int min_dropout_uV；ARC list_voltage 返回 Command DB 逻辑 level；regulator core 直接相加。原始 0xffffffff 在 ARM64 two's-complement 构建中是 -1，不是 no-dropout sentinel；不得改成 0。
- Parent graph: ROUND11 只报告了四条；ROUND14 新发现 MX MMCX-supply child -> CX MMCX-supply child 的第五条合法 parent-supply。现在能确认至少五条，完整总数仍 UNKNOWN，不能宣称已完成全图盘点。
- MMCX ALL proxy: 本机有 self-target proxy-supply、proxy-consumer-enable、voltage <384 65535>，即临时 TURBO..MAX boot request。公开 KONA proxy-consumer 在 late_initcall_sync 撤销；不能翻译成 permanent system-load 或 always-on。ACK 目前没有等价 helper。
- ARC/GenPD: ACK SM8250 OPP 表拥有相同 corner 名称/数字，但 ACK 选中的 MMCX GenPD 没有 MX parent，且 GenPD 模型无法自然表达所有 HOS per-child parent-supply、ALL/AO/SO 与临时 proxy 请求。不要给共享 qcom,sm8250-rpmhpd descriptor 加父边；完整 ARC 等价性仍是独立 gate。
- S8: ROUND14 未发现 qcom,init-enable / regulator-boot-on / regulator-always-on；qcom,set=3 是集合选择，init-mode RET 是模式，不是 enable。ACK pmic5_hfsmps510 无 get_optimum_mode/set_load，210mA load-only 调用是 no-op。不要强制 enable，不加 boot-on/always-on，不保留无意义 S8 set_load；runtime enable state UNKNOWN。
- S8 DTS initial mode 从先前 ROUND48 的 AUTO fallback 更正回有 HOS 静态证据的 RET；RET/AUTO 仍列为 allowed modes，未加 enable policy。
- VDDP/L6 方案不变：set-load 100µA + enable；在 generic UFS VCCQ teardown 后 deferred cleanup。S8 optional get/load/enable/disable 不纳入第一版 ACK UFS 补丁。

已更新 main：
- dts/dby-w09-ack18-board.dts.draft（blob SHA: dd9035083458ea6ccdb5fdd852b7a1860509fbaf）
- kernel-baseline/round48/ack-hos43-pmic5-mode-enum-translation-and-dts-decision.md（附 ROUND51 S8 correction）
- kernel-baseline/round49/ack-ufs-vddp-vccq-parent-devres-lifecycle-redesign.md（附 S8 no-op correction）
- kernel-baseline/round50/ack-sm8250-mmcx-mx-arc-parent-semantics-and-remaining-local-gate.md（附 ROUND14 corner/edge update）
- dts/README.md（更新边数、S8、proxy 与 ROUND14 状态）

**本地 Agent 当前队列为空；没有创建 ROUND15。** ROUND14 已足以支持当前的保守决策；完整 ARC 全图统计以后若成为实现所需门槛，再另发一个只使用现有解析结果的独立任务，不重跑 FDT parser。

阶段 A 仍未进入完整内核构建：完整工作树 apply、checkpatch、dt-schema、dtc/dtbs_check、最终 Kconfig/.config、Kleaf 构建、镜像打包、实机启动、UFS 识别/读写和基础硬件验收均 NOT_RUN。ROUND12 AVB、ramdisk、EROFS、最终 memory/reserved-memory handoff、selected DTBO 与物理 PMIC 输入树仍有独立 gate。Stage B DerpFest 暂不开始。PR #1 保持 Draft，ack18-dby-w09-dts-draft protected branch 未修改。
