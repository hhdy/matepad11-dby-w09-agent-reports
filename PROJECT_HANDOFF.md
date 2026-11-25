# PROJECT_HANDOFF.md — DBY-W09 GKI 6.18.33 → Android 17 DerpFest 总交接

更新：2026-11-25  
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
- 需要新建本地任务时，先检查 ROUND 编号和既有任务，确保不重复。ROUND12 已上传并按工具门槛 BLOCKED；firmware-analysis ROUND13/14 均已上传完成；当前本地 Agent 队列为空。ROUND13 与历史 kernel-baseline/round13 ACK DTS 设计属于不同目录/工作流。
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

ROUND30/50 的 ACK 源码缺口仍然存在：固定 ACK .33 的 SM8250 RPMHPD descriptor 只为 CX 设置 MX parent，MMCX 使用无 parent 的 plain descriptor。ROUND14 已补齐 HOS4.3 MMCX/MX 静态 provider/child 属性：MMCX ALL/AO/SO 的 min/init=64 (LOW_SVS)，MX MMCX-supply/AO 的 min/init=16 (RETENTION)，set 3/1/2=ALL/ACTIVE/SLEEP；ALL/AO dropout 原始值为 0xffffffff。ROUND51 通过公开 KONA 源码确认它被存为 signed int 并作为 -1 加入 ARC 逻辑 parent request path，而不是 no-dropout sentinel。ROUND14 还确认一条新的 MX MMCX-supply→CX MMCX-supply parent-supply，因此至少五条边已知，完整总数仍未盘点。相同 corner 编号不等于 ACK GenPD 已实现 vendor ARC 的 per-child parent/dropout/proxy 语义；不要给共享 MMCX descriptor 加 MX parent。

### 7.3 HOS4.3 ARC / proxy

ROUND11 最初确认 4 条 ARC level parent-supply 边和 6 条 ARC proxy-supply 边；ROUND14 后续确认第五条 parent-supply，因此当前为至少 5 条已证明 parent 边，完整总数仍 UNKNOWN。ROUND14 还确认 MMCX ALL child 有 self-target proxy-supply、proxy-consumer-enable 和 TURBO..MAX 临时 boot voltage request。它们属于 Vendor RPMh ARC/proxy，不是 VRM 物理输入或永久 always-on。ACK 上游 qcom-rpmh-regulator 不等同于旧 Vendor ARC provider；ACK 暂无等价 generic proxy helper。不能把 vendor ARC 节点直接搬进 ACK DTS。详见 ROUND51。

### 7.4 PM8150 电源输入与 DRMS

完整 base FDT 相关扫描未发现 `vdd-s1..s10-supply`、`vin-supply`、`vph-pwr-supply`，所以 PMIC 输出的真实物理输入树仍是独立 gate。ROUND13 完成 mode/DRMS 字段审计，ROUND14 完成 ARC corner/dropout/proxy 与 S8 静态 enable 属性审计；ROUND48/51 已将 HOS vendor enum 映射到 ACK symbolic mode，S8 初始值最终保留 RET，不增加强制 enable。ROUND52 第一版 UFS driver 只实现 VDDP/L6 load+enable 与延迟 cleanup，不消费 S8/VCCQ-parent。DTBO entry selection/effective post-overlay 仍 UNKNOWN；不得根据 HOS4.2 参考树臆造供电或模式属性。

### 7.5 Memory / reserved-memory

HOS4.3 base FDT 未发现普通 `/memory` 节点，但有 34 个 reserved-memory 子节点。ROUND42 对照公开 SM8250 FreeABL LinuxLoader 发现：标准路径要求传入 FDT 已存在 `/memory`，只用 UEFI RAM Partition Protocol 更新其 `reg`，缺失则返回 `EFI_NOT_FOUND`；不创建该节点。故不能假定 ABL 会补 `/memory`。但该项目是另一台 SM8250 设备，并非 Huawei HOS4.3 ABL，真正 post-overlay/post-ABL FDT 仍 UNKNOWN。其 no-map carveout 机制只处理输入树已有 `/reserved-memory` 节点，不重建 HOS4.3 的 34 个子节点。内存范围与保留区语义未闭环，是内核 DTB 编译/启动前 gate。见 ROUND19 / ROUND42。 该参考中缺失/不可解析的 memory node 会沿 LoadAddrAndDTUpdate 返回，非 RUMI 平台的上层启动路径会中止；FdtPathOffset 的查询允许唯一 memory@unit-address 节点解析，并非字面名称强制。 ROUND43 补充了 ACK EFI-stub 例外：只有实际通过 Linux EFI stub 入口启动，并由 stub 向 `/chosen` 写入完整 UEFI memory-map 元数据时，内核才会从 UEFI map 重建 memblock；仅仅运行在 UEFI ABL 上不等于使用该路径。华为实际采用 classic 还是 EFI-stub 入口仍 UNKNOWN。

### 7.6 Legacy boot / AVB / ramdisk

ROUND12 已上传但在工具门槛 BLOCKED：本机没有可信已安装 avbtool / 已审查 AVB helper，boot / ramdisk / dtbo footer 与 vbmeta descriptor 覆盖关系均 UNKNOWN。不得从 `AVB0` magic 或文件大小推断。最终镜像重打包策略、dm-verity/FEC 配置和任何启动测试写入方案仍受 AVB gate 阻塞。
ROUND10 ramdisk 内容仍 BLOCKED；Android first-stage module 路径及模块目录是否可用尚未确认。UFS/QMP 因此在当前 storage-first 设计中倾向内建，但最终要以构建与启动设计审查为准。

## 8. 当前任务队列

### 本地 Agent（当前无活动任务）

- **ROUND12：已交付 / BLOCKED**。报告 `firmware-analysis/round12/round12_avb_metadata_findings.txt` 已上传；无可信已安装 AVB 工具，footer/vbmeta descriptor coverage 仍 UNKNOWN。不要重复执行，也不要安装工具。
- **firmware-analysis ROUND13：已完成 / 已上传**。报告 `firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt`。不要重新扫描。
- **firmware-analysis ROUND14：已完成 / 已上传**。报告 `firmware-analysis/round14/round14_arc_mmcx_mx_power_properties.txt`；只复用 ROUND3 已审核 work copy/parser 和 phandle/path index，没有重跑 ROUND11/13 或 DTBO scan，上传后停止。
- 当前本地 Agent 队列为空。不要重跑 ROUND11/13/14；只有新问题确实需要不同的本机独有事实，且现有工作副本/工具路径可用时，才创建一次性只读任务。
- 不得安装、下载、写 parser、调用 WSL 或更改安全策略。Agent 仅可上传脱敏文本到 `firmware-audit-v1`；不更新 `main`、受保护 ACK DTS 草案分支或 PR #1，不编译，不操作设备。

### GPT 侧（继续 Stage A）

- ROUND32/36 schema、ROUND37 board DTS、ROUND33 dual-GenPD driver 已整理为 patch series；ROUND52 又补充 UFS VDDP/VCCQ-parent binding 及 VDDP/L6 managed lifecycle。严格的内存模拟按 ROUND32 → ROUND36 → ROUND52-0001 → ROUND37 → ROUND33 → ROUND52-0002 顺序验证了 15/15 hunk 的旧/新上下文和精确行号，但这不是实际 `git apply`。
- 当前 VDDP 方案：DTS 属性存在时使用 mandatory `devm_regulator_get("qcom,vddp-ref-clk")`，设置 100µA load 后 enable；cleanup action 在 `ufshcd_remove()` 完成通用 VCCQ shutdown 后执行，并在 `regulator_put()` 前 disable + 清负载。devres LIFO 确保 callback 运行时 HBA 和 variant host 对象仍有效。
- S8/VCCQ-parent 不由第一版 ACK UFS driver 获取或投票；ACK HFSMPS510 没有 DRMS 回调，210mA load-only 请求是 no-op。S8 保留 RET initial，不强制 enable，运行时状态 UNKNOWN。
- ROUND51 已把 MMCX/MX ARC 静态角点、dropout 与第五条 parent edge 对账；完整 ARC graph、effective DTBO 和 runtime vote 仍是单独 gate。
- 当前真正的下一门槛是完整 ACK 6.18.33 工作树和可执行构建环境：实际 `git apply --check`/apply、checkpatch、dt_binding_check、dtbs_check/dtc、最终 Kconfig/.config 和 Kleaf build；此后才可能进入受控设备验证。read-only Local Agent 不得承担源码修改或编译。
- AVB footer/vbmeta、ramdisk、EROFS、memory/reserved-memory final handoff、selected DTBO 与 PMIC 物理输入树仍有各自 blocker。Stage B DerpFest 不得提前开始。
- 每一轮先读本文件和已有报告；不要重新做 Android 12L 泛化调研。

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

**新会话的正确起点：先读本文件及 `AGENT_TASK.md` 末尾的最新状态。ROUND12 AVB 为 BLOCKED；ROUND13/14 已完成；ROUND15 未创建，本地 Agent 队列为空。ROUND49/50/51/52 已更新 UFS、电源域和 ARC 设计，但完整 ACK 工作树 apply、checkpatch、dt-schema、DTB、最终 Kconfig、Kleaf 编译和实机启动均未完成。当前真正门槛是完整 ACK 6.18.33 工作树和构建环境，不是重复解析本机 FDT。不要重新讨论 Android 12L，不要提前跳到 DerpFest 全系统适配，也不要改动 PR #1 或受保护 ACK DTS 草案分支，除非用户明确授权。**


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

Next sequence: harden ROUND33, maintain the ROUND38 patch order (ROUND32 schema → ROUND36 common binding → ROUND37 board DTS → ROUND33 driver), then run complete disposable-tree patch/schema/DTB/Kconfig/build checks only after the AVB and memory/boot-chain gates are addressed. ROUND12 AVB remains BLOCKED; ROUND13 and ROUND14 are complete, and the Local Agent queue is currently empty. Stage B DerpFest work remains deferred until Stage A 6.18.33 actually boots and passes storage/basic-hardware validation.


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

ROUND30 MMCX-to-MX, ROUND42/43 Huawei final memory handoff, ROUND12 AVB and ROUND40 UFS companion-supply teardown remain separate open gates. ROUND12 AVB remains BLOCKED; ROUND13 and ROUND14 are complete, and the Local Agent queue is currently empty. No protected DTS branch, firmware audit branch or PR #1 was modified. Stage B DerpFest work remains deferred until Stage A 6.18.33 actually boots and passes storage/basic-hardware acceptance.


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

ROUND12 AVB report is uploaded but BLOCKED at the trusted-tool gate; ROUND13 and ROUND14 local audits are complete and the Local Agent queue is empty. ROUND30/51 MMCX-to-MX equivalence and ROUND42/43 actual memory handoff remain independent open gates; the UFS VDDP/VCCQ-parent lifecycle design is now documented in ROUND49/51/52. No protected branch, PR #1 or device was changed. Stage B DerpFest remains deferred until Stage A 6.18.33 boots and passes storage/basic-hardware acceptance.


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

Current DBY-W09 board DTS draft (main, review-only) reflects the ROUND48/51/52 corrections: S4 has no forced mode; L5/L9 use HPM initial with LPM/HPM allowed and set-load DRMS; L6/L17 use LPM initial with LPM/HPM allowed and set-load DRMS; S8 uses RET initial with RET/AUTO allowed but no forced enable/boot-on/always-on. No synthetic L5/L9 system-load is used because the vendor proxy request is temporary. These are draft settings only and effective post-overlay values remain UNKNOWN.

The public same-device Linux DTS used as a HOS4.2 cross-reference shows HPM initial mode on the PM8150 UFS rails, while LPM/HPM + allow-set-load appears on PM8150L L6/L9 for microSD. This is **not evidence of actual HOS4.3 settings** and must not be copied mechanically.

ROUND13/14 已完成 HOS4.3 base-FDT 静态字段审计：上游标准 `regulator-*` mode/DRMS 属性在所检查范围内 NOT_FOUND；本机实际使用 provider-level `qcom,supported-modes` / `qcom,mode-threshold-currents` 与 child-level `qcom,init-mode` / `qcom,set`。ROUND48/51 已按固定 ACK enum 完成符号转换并更新 main DTS：L5/L9 HPM initial，L6/L17 LPM initial，LPM/HPM allowed + DRMS；S4 不强制模式；S8 RET initial、RET/AUTO allowed，不强制 enable。MMCX/MX ARC 与 S8 enable 静态属性已在 ROUND14 提取，proxy/ARC 等价性差异见 ROUND51。临时 proxy 生命周期与 ACK 不具备的 ARC/proxy helper 仍是启动期差异；runtime mode/enable 状态均未读取。

ROUND47/48/51 为固定 ACK 与公开 KONA 源码审查；ROUND13/14 为本机静态 FDT 提取，均未读取 runtime regulator mode。完整树 apply、DTS/schema、DTB、Kconfig、Kleaf build 和设备启动仍 NOT_RUN。ROUND12 AVB 继续 BLOCKED；Local Agent 队列为空。Stage A ACK 6.18.33 仍是唯一项目阶段，DerpFest Stage B 继续等待。

## 14. Local evidence status — ROUND12 AVB blocked; ROUND13/14 complete

Updated: 2026-11-24.

- ROUND12 AVB metadata report is uploaded but BLOCKED at the trusted-tool gate. No trusted AVB footer/vbmeta descriptor inspector was available; footer presence, original-image size, descriptor list and chain remain UNKNOWN. Do not install tools or repeat the blocked scan.
- ROUND13 PM8150 mode/DRMS audit is complete and uploaded to `firmware-audit-v1`.
- ROUND14 MMCX/MX ARC corner/dropout/proxy and S8 enable-field extraction is complete and uploaded to `firmware-audit-v1`. It reused only the approved ROUND3 base-FDT work copy/parser and existing phandle/path indices; it did not redo ROUND11/13, reparse DTBO or touch EROFS/AVB/ramdisk/device.
- ROUND51 reconciles ROUND11's four-edge list with the fifth edge confirmed by ROUND14. At least five base-FDT parent-supply edges are known; the full graph count remains unverified. It also establishes ARC symbolic corner semantics, signed -1 dropout handling, the MMCX ALL temporary TURBO..MAX proxy request, and the conservative S8 policy.
- No local Agent task is active. Do not repeat ROUND11/13/14 FDT parsing. A future task is justified only for a distinct local-only fact that cannot be resolved from the existing reports and public fixed source.
- AVB, ramdisk and EROFS remain independently blocked; memory/reserved-memory final handoff, selected DTBO and physical PMIC input tree remain separate gates.

Stage A ACK 6.18.33 remains the only project stage. Stage B DerpFest is deferred until actual kernel boot and UFS/storage/basic-hardware acceptance.
  
## ROUND48 / ROUND51 regulator-mode decision — corrected final state (2026-11-24)

ROUND13 supplied HOS4.3's actual vendor mode fields; ROUND48 translated vendor enum semantics to fixed ACK symbols. The final current DTS proposal is:
- S4: no forced mode because HOS4.3 mode metadata was not found in inspected scope.
- L5/L9: HPM initial, LPM/HPM allowed, DRMS enabled; no permanent `regulator-system-load`, because public KONA proxy-consumer removes its temporary boot request at late_initcall_sync and ACK has no equivalent helper.
- L6/L17: LPM initial, LPM/HPM allowed, DRMS enabled.
- S8: RET initial, RET/AUTO allowed. ROUND48's interim AUTO fallback was withdrawn in ROUND51 after ROUND14 showed no static enable/boot-on/always-on property and fixed ACK HFSMPS510 was shown to have no DRMS load callback. Do not force S8 enable; runtime enable state remains UNKNOWN.

The old Qualcomm vendor enum is PASS=0, RET=1, LPM=2, AUTO=3, HPM=4; fixed ACK uses RET=0, LPM=1, AUTO=2, HPM=3. DTS uses ACK symbolic constants, never raw HOS values.

Reports:
- `kernel-baseline/round48/ack-hos43-pmic5-mode-enum-translation-and-dts-decision.md`
- `kernel-baseline/round51/round14-arc-value-semantics-proxy-vote-and-round11-edge-reconciliation.md`

The board file is a review-only draft on main. No full-tree apply, dtc/dt-schema, Kconfig resolver, Kleaf build, packaging or device test has been run. Protected branch and PR #1 remain untouched.

## ROUND49 / ROUND50 / ROUND51 — UFS rails and ARC graph final decisions (2026-11-24)

### ROUND49/51 — UFS optional rail lifecycle
- VDDP REF_CLK/L6 is the only optional rail consumed by the first ACK UFS driver patch: set the board's 100µA load, enable before Qualcomm PHY power-up, and defer disable + load-clear until after generic UFS VCCQ is shut down during `ufshcd_remove()`.
- S8/VCCQ-parent is not acquired or voted by the first ACK UFS driver. Its 210mA load-only request is a no-op on fixed ACK HFSMPS510; do not add enable/disable, voltage vote, boot-on or always-on. Runtime enable state remains UNKNOWN.
- ROUND52 uses `devm_regulator_get(dev, "qcom,vddp-ref-clk")` when the DTS supply property is present, matching KONA's mandatory get semantics. The cleanup action is registered immediately after the managed get, with flags set only after successful load/enable, so all subsequent failure paths are covered.
- Full lifecycle details: `kernel-baseline/round49/ack-ufs-vddp-vccq-parent-devres-lifecycle-redesign.md`.

### ROUND50/51 — MMCX/MX ARC
- ROUND14 raw values resolve to RETENTION=16, LOW_SVS=64, TURBO=384 and MAX=65535; qcom,set 1/2/3 mean ACTIVE/SLEEP/ALL. These are logical corners, not microvolts.
- Raw min-dropout 0xffffffff is stored as signed -1 by the fixed KONA implementation and added along the ARC logical-level supply propagation path; it is not a no-dropout sentinel.
- ROUND11 identified four edges; ROUND14 confirmed a fifth MX MMCX-supply -> CX MMCX-supply edge. At least five are now known, but a complete parent-edge census is not claimed.
- MMCX ALL has a temporary proxy-consumer-enable request at TURBO..MAX. ACK has no equivalent generic helper. Do not convert it into permanent always-on/system-load.
- Identical canonical corner numbers do not prove that ACK shared SM8250 GenPD has full HOS ARC equivalence. Do not add MMCX->MX to the shared qcom,sm8250-rpmhpd descriptor.

Reports: ROUND49, ROUND50 and ROUND51 under `kernel-baseline/round49`, `round50`, `round51`.

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


## 最新公开源码集成草案 — ROUND52（2026-11-24）

ROUND52 已完成固定 ACK UFS binding / variant driver 的公开源码检查，并在 main 新增两份设计草案；binding 补丁最终增加了 positive-load 与 supply/max-load 配对约束：

- 报告：kernel-baseline/round52/round52-storage-first-ufs-vddp-integration-and-binding-closure.md（最新报告内容 SHA acd35ab048a437e03957cf6a7f5ffd2c82885378）
- Binding patch：kernel-baseline/round52/0001-dt-bindings-ufs-vddp-vccq-parent-supplies.patch.draft（blob c0ac84067a900022a077c748b7abb10345f1295f；34 insertions；两处 hunk 均完成文本行数复核）
- Driver patch：kernel-baseline/round52/0002-ufs-qcom-sm8250-vddp-refclk-managed-lifecycle.patch.draft（blob fb34fbc9701bc7e7b56bb9078ee98c0cdd8caf78；4 处 hunk 均完成文本行数复核）

核心决策：
- ACK qcom,ufs.yaml 没有显式文档化 qcom,vddp-ref-clk-supply/max-microamp 和 qcom,vccq-parent-supply/max-microamp；ROUND52-0001 将四个扩展属性显式加入 schema。
- VDDP/L6：ROUND52-0002 在 ufs_qcom_init() PHY 上电前使用必需的 devm_regulator_get("qcom,vddp-ref-clk")，按 DTS max-microamp 设置负载并 enable；devm cleanup 在 ufshcd_remove() 完成通用 VCCQ 关闭后、regulator_put 前 disable 并清零负载。
- S8/VCCQ-parent：不 acquire、不 set_load、不 enable/disable、不 set_voltage。qcom,vccq-parent-supply 仅是已定义的源拓扑属性；首版 ACK UFS driver 不消费它。
- ROUND52 patch series 预期排在 ROUND32/36 schema、ROUND37 board DTS、ROUND33 dual-GenPD driver 之后。该顺序和 patch hunk 行数已经静态复核，但 combined full-tree apply / checkpatch / dt-schema / build 均 NOT_RUN。

当前无本地 Agent 任务。ROUND52 使用已知 ACK 源码和 ROUND13/14 数据，不需要重跑 FDT。需要真实完整 ACK worktree 才能完成下一阶段 combined git apply、checkpatch、dt-schema、最终 Kconfig 和 Kleaf build；本地 Agent 当前的只读限制并不授权它编译或修改源码。


ROUND52 source-contract addendum: fixed ACK of_regulator.c constructs the consumer property as <id>-supply, so regulator ID "qcom,vddp-ref-clk" resolves exactly to DTS property "qcom,vddp-ref-clk-supply". The final driver patch uses mandatory devm_regulator_get() after detecting the DT property (not optional_get), so a declared-but-unavailable provider defers/fails rather than being silently skipped. The cleanup callback's host and hba pointers remain valid because the VDDP cleanup action is registered after ufshcd_alloc_host() and variant devm_kzalloc(); ACK devres LIFO runs it before either earlier object-release action, and after ufshcd_remove() closes generic VCCQ. Fixed ACK regulator_enable() invokes drms_uA_update() on the consumer's first enable when it already has a nonzero load; therefore VDDP set_load(100µA) then enable is an effective L6 DRMS request. S8 load-only remains ineffective due its handle not enabled and missing HFSMPS510 DRMS callbacks. See ROUND52 report addendum and source links. ROUND52 patch hunk counts were rechecked: binding 2/2 and driver 4/4 hunks have declared counts and exact source positions matching. This remains textual/static verification, not git apply or build.


ROUND52 ordered patch-context simulation update: the final patch series was applied in-memory to exact pinned ACK source contents (plus the protected board DTS source fetched read-only). ROUND32 3/3, ROUND36 2/2, ROUND52-0001 2/2, ROUND37 board 2/2, ROUND33 2/2, ROUND52-0002 header 1/1 and driver 3/3 hunk contexts all matched in dependency order — 15/15 total. The strict verifier checks exact old-side context and both declared old/new line positions after cumulative preceding hunk deltas, without fuzz or nearest-context fallback. This is still an in-memory source simulation, not the actual Git apply command or a disposable full source worktree. No branch was changed. Full-tree git apply --check, checkpatch, dt-schema, dtc/dtbs_check, Kconfig and Kleaf remain NOT_RUN. Latest ROUND52 report content SHA: 93654c9ab0a95edc24fc4036261a7557e098fb13; updated ROUND38 patch-series manifest SHA: 3b6a07c2c29b07f3e95af6d342f84117ecb993c9.


ROUND52 final driver-object lifetime note: fixed ACK ufshcd_alloc_host() registers the SCSI-host release action before Qualcomm variant init. The variant's ufs_qcom_host devm allocation and then VDDP cleanup action are registered later. Devres LIFO runs VDDP cleanup while host and hba are still valid, after ufshcd_remove() has completed generic VCCQ shutdown.


## 16. Parallel AI delegation — ROUND54 (2026-11-24)

The user plans to connect a second GitHub-capable AI to accelerate the project. A non-overlapping work split has been prepared:

- **Primary AI / ChatGPT:** continue ROUND53 and subsequent Stage-A work on main, focusing on Kconfig closure, storage-first boot prerequisites and integration planning.
- **Second AI:** independently red-team review the existing ROUND32/36/37/33/52 UFS patch series, regulator lifecycle/error paths, GenPD/required-OPP logic, binding schema and board DTS consistency.

Second AI onboarding:
- Coordination index: `ai-parallel/README.md`
- Full task contract: `ai-parallel/ROUND54_TASK.md`
- Copy/paste start prompt: `ai-parallel/SECOND_AI_START_PROMPT.md`
- Dedicated branch (already created from latest main): `ai-parallel/round54-ufs-review`
- Required report template: `ai-parallel/round54/ROUND54_REVIEW.md` on the dedicated branch.

The second AI must commit only to its dedicated branch. It may place justified candidate patches under `ai-parallel/round54/candidates/`, but must not overwrite canonical patch drafts or reports. It must not edit main, `ack18-dby-w09-dts-draft`, `firmware-audit-v1`, or PR #1; no PR/merge is requested. The primary AI will review its report before adopting any change. This parallel AI is distinct from the local read-only firmware Agent and does not need local device/firmware access.

Current state at task dispatch:
- ROUND49/50/51 source reviews completed.
- ROUND52 UFS binding + VDDP driver drafts prepared; 15/15 strict in-memory hunk-position simulation passed, but no full-tree git apply/build.
- ROUND53 static Kconfig dependency-closure audit created; actual Kconfig resolution/final `.config`/Kleaf build remain not run.
- Stage A ACK 6.18.33 remains the sole active porting stage; DerpFest Stage B remains deferred until real Stage-A boot and storage/basic-hardware acceptance.


### ROUND53 follow-up — configuration dependency closure refinement

ROUND53 confirms the static source dependency route for UFS/QMP/GCC/RPMh/SM8250 interconnect/RPMhPD/RPMh regulator/SMMU/DM/EROFS against the pinned ACK source. The pinned GKI base already has DM_VERITY, DM_VERITY_FEC and EROFS_FS built-in. A follow-up corrected the fragment so it no longer directly assigns hidden `GENERIC_MSI_IRQ`; arm64 selects GICv3 and (when the inherited `PCI=y`) GICv3 ITS, which selects GENERIC_MSI_IRQ for `SCSI_UFS_QCOM`.

- Current storage-first config fragment blob: `e441d042418667ca6d5d58ca4a53bcd8ccd708c3`.
- Current ROUND53 report blob: `e31686d79bfbcd31ccdfa346d8e738a9f12440ff`.
- Actual Kconfig resolution, olddefconfig/final .config, Kleaf build and runtime remain NOT_RUN.


ROUND53 follow-up: the storage-first fragment now removes direct assignments of hidden `GENERIC_MSI_IRQ`, `SCSI_DMA`, and `OF_RESERVED_MEM`; `PM_OPP` also remains selection-derived from PM_DEVFREQ. The fixed ACK arm64/GICv3-ITS, SCSI/HAS_DMA and OF_EARLY_FLATTREE chains derive these requirements. Current fragment blob: `ae8675357e2f5c57c9ec38e7574b00590b558c63`; current ROUND53 report blob: `b471500b33e987453e4492c80113457f8a34e92e`. These are static-source corrections only; no final `.config` or Kleaf build has run.


## ROUND15 — Stage-A build environment inventory taskbook prepared (2026-11-24)

A narrowly scoped local-only taskbook is now present at `firmware-analysis/round15/AGENT_TASK.md`.

Purpose: inventory whether the user's existing computer already has (a) a complete ACK `android17-6.18.33_r00` source worktree containing pinned commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`, and (b) an existing Linux-capable build environment/toolchain. This is the next practical gate after ROUND53 static Kconfig closure.

The task is **READY FOR LOCAL AGENT — NOT DISPATCHED**. It is strictly read-only: no network fetch/clone/repo sync, tool installation, WSL/VM/container start, patch application, Kconfig, compilation, or device access. Its only allowed deliverable is a sanitized text inventory uploaded to `firmware-audit-v1`.

This is not a repeat of ROUND12/13/14 firmware analysis and does not overlap ROUND54. ROUND54 remains the second GitHub-connected AI's independent UFS patch review on `ai-parallel/round54-ufs-review` only. Stage A ACK 6.18.33 remains the sole porting stage; DerpFest Stage B is still deferred until Stage A boots and passes storage/basic-hardware acceptance.


## ROUND55 — Stage-A execution gate matrix (2026-11-24)

Report: `kernel-baseline/round55/stage-a-execution-gate-matrix.md`.

ROUND55 consolidates existing Stage-A evidence into an execution sequence and separates source/build validation from the later first-boot gates:

- ROUND15 local inventory first checks whether the exact ACK source worktree and an already-existing Linux build environment are available.
- Once a disposable full source workspace exists, validate the patch series in the documented order: ROUND32 → ROUND36 → ROUND52-0001 → ROUND37 → ROUND33 → ROUND52-0002.
- Run real worktree `git apply --check` / apply / diff checks, dt_binding_check, DTB/schema validation where inputs are ready, actual Kleaf Kconfig resolution and final `.config`, then the full-image custom kernel build with no `base_kernel`.
- AVB, ramdisk and trusted memory handoff remain first-boot/image-packaging gates. They do not need to block source-only patch application or kernel compilation, but no board DTB/boot candidate should be promoted without resolving trusted RAM / reserved-memory semantics and the actual boot path.
- ROUND54 remains the second AI's independent UFS review; its branch currently has a report template only. ROUND15 currently has a taskbook only, no execution report.

No source patch, BUILD target, .config, DTB, image, or device partition was changed or built. No device boot is claimed. The order remains ACK 6.18.33 Stage A first; DerpFest Stage B only after Stage-A boot and storage/basic-hardware acceptance.


## 最新环境盘点与部署授权 — ROUND15 / ROUND16（2026-11-24）

### ROUND15 已完成

本地 Agent 已上传 `firmware-analysis/round15/round15_stagea_build_environment_inventory.txt` 到 `firmware-audit-v1`，Git blob SHA `e4d5bcdb8ae2d6f7ff8ae173308badf549b8f0bb`。

结论：`NO_EXISTING_BUILD_WORKSPACE_FOUND`。在限定扫描范围内未找到 ACK 源码树或 Repo workspace；未证实有可用 Linux 构建环境；Windows 侧缺少 kernel build toolchain。D 盘当时有 325.4 GiB 可用。WSL 可执行文件存在，但发行版查询被主机安全程序拦截，因此现有 WSL distro 状态 UNKNOWN，不能宣称 WSL 完全不存在。

### ROUND16 已创建：部署 WSL2 + ACK kernel workspace

用户于 2026-11-24 明确授权本地 Agent 在电脑上部署构建环境。

任务书：`firmware-analysis/round16/AGENT_TASK.md`。

计划采用 WSL2 + Ubuntu 24.04 LTS，发行版安装位置优先为 `D:\\WSL\\Ubuntu-24.04`；ACK workspace 放在 WSL 自己的 Linux 文件系统中，避免在 `/mnt/d` 上直接编译。仅同步官方 Android kernel manifest `common-android17-6.18`，不检出完整 AOSP/DerpFest 平台。将 common kernel 精确 pin 到 `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`，并保存 `repo manifest -r`。

Kleaf 的 Bazel / Clang / Rust 版本应由 Repo manifest 同步的 prebuilts 提供，不在 Windows 全局安装散装编译器。ROUND16 限制部署占用不超过 200 GiB，并保留 D 盘至少 100 GiB 可用。

重要边界：ROUND16 允许官方 WSL、Ubuntu apt 包、Repo sync 和 workspace 创建；不允许绕过 Windows 安全程序、关闭 Defender/安全策略、修改 BIOS、强制重启、删除已有 distro、操作设备或刷写分区。若 WSL 仍被安全策略拦截则 BLOCKED 并停止；若需要重启或 UAC，则交给用户完成，不得自动强行推进。

ROUND16 当前状态：**任务书已上传，等待本地 Agent 执行；尚无部署完成报告。** 本轮不做内核编译。只有环境与精确源码 pin 核验通过后，才进入独立的补丁集成、schema/Kconfig 检查与 Kleaf 编译阶段。

技术决策记录：`kernel-baseline/round56/linux-build-host-deployment-decision.md`。

Stage A ACK 6.18.33 顺序不变；设备实际启动与存储/基础硬件验收前，不进入 DerpFest Stage B。

ROUND16 local Agent copy/paste start prompt: `firmware-analysis/round16/START_PROMPT.md`.


## 并行 AI 审查结果 — ROUND54 完成 / ROUND57 修正（2026-11-24）

第二个 GitHub-connected AI 已在独立分支 `ai-parallel/round54-ufs-review` 完成 ROUND54，最新报告 blob `c9e373bf0e05ebfb62f56395b5466187ec0c2686`，判定 `PASS WITH NON-BLOCKING FINDINGS`。

- 未发现已证实的 P1/P2 UFS driver lifecycle defect。
- 发现一项 P3 schema 缺口：ROUND32 的 SM8250 分支限制 `clocks=8`，但 `clock-names` 仍继承 common schema 的 7..9 条范围。
- 第二个 AI 的独立候选已由主 AI 复核采纳为独立 follow-up draft ROUND57；原 ROUND32 文件不覆盖，历史 SHA 不变。
- ROUND57 patch: `kernel-baseline/round57/0001-dt-bindings-ufs-sm8250-clock-names-exact-count.patch.draft`。
- ROUND57 report: `kernel-baseline/round57/sm8250-ufs-clock-names-exact-count-follow-up.md`。
- 更新后的建议 patch order: ROUND32 → ROUND57 → ROUND36 → ROUND52-0001 → ROUND37 → ROUND33 → ROUND52-0002。
- ROUND57 仍是 patch draft；没有 full-tree apply、dt_binding_check 或 dtbs_check。

第二 AI 的任务已完成，暂不再分配新的 UFS 审查任务。其独立分支保留报告和候选文件，不合并，不修改 protected DTS branch，PR #1 仍 Draft。

### 当前唯一执行瓶颈：ROUND16 本机部署

ROUND15 已证明没有现成 ACK kernel worktree 或可确认的 Linux build host。用户已明确授权部署。下一步是本地 Agent 执行 `firmware-analysis/round16/AGENT_TASK.md`，启动入口 `firmware-analysis/round16/START_PROMPT.md`。

ROUND16 目标：在 D: 部署 WSL2 + Ubuntu 24.04，安装最小官方 Ubuntu host packages，Repo sync 官方 `common-android17-6.18` kernel manifest，把 `common` 精确 pin 到 `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`，并记录 manifest/Clang/Rust/Bazel 版本。保留 D 盘至少 100 GiB 空间；不下载完整 Android/DerpFest 平台；本轮不编译。

如果 Windows 安全程序仍拦截 WSL，必须停止并报告，不得绕过或关闭安全策略；需要管理员或重启时交由用户处理。ROUND16 结束后，才新建独立的 patch integration + schema + Kconfig + Kleaf build 任务。

ROUND16 当前还没有上传部署结果；不得把 WSL 已部署或 ACK workspace 已准备好写成事实。


## 最新状态校正 — ROUND16 BLOCKED；ROUND17/ROUND58 并行派发（2026-11-24）

**本节覆盖上文中“ROUND16 未执行 / ROUND54 未完成 / ROUND16 为当前任务”的旧状态描述。**

### ROUND16 实际结果

ROUND16 已执行并上传，终态为 **BLOCKED_BY_HOST_SECURITY_POLICY**；没有进入部署阶段。报告：
- `firmware-analysis/round16/round16_wsl_ack_workspace_deployment.txt`
- 分支：`firmware-audit-v1`
- 报告 SHA256 在本地与上传文件核对一致；报告大小 15,190 B。

准确事实：
- Store 版 WSL Appx `MicrosoftCorporationII.WindowsSubsystemForLinux 2.7.3.0` 已安装。
- 注册了一个既有 WSL2 发行版 `Ubuntu`（Version=2），位于 C:；具体发行版 Ubuntu 版本未知，目录探测也 UNKNOWN。
- `VirtualMachinePlatform` 已启用；HypervisorPresent / VirtualizationFirmwareEnabled 为 true。
- WSL 程序入口 `C:\Windows\System32\wsl.exe` 被 Windows Security Center 的 Command Security / Program Blacklist 阻止。
- ROUND16 Agent 当前进程非提升；管理员权限是安装/启用组件时的次级门槛。
- 未创建新发行版、未 apt、未 Repo sync、未 pin、未编译，也未接触平板。
- D: 约 325.3 GiB 可用，存储空间不是阻塞原因。

**ROUND15 结论更正：** ROUND15 只是因为无法调用 WSL 而未获得发行版信息，不能据此说“没有 WSL”。ROUND16 才首次确认 Store WSL 2.7.3.0 与已注册的 WSL2 Ubuntu。旧版 `Microsoft-Windows-Subsystem-Linux` 可选功能状态为 Disabled，但不能在没有真实错误的情况下认定 Store WSL2 需要它；`HypervisorPlatform` Disabled 也不能先验判定为 WSL2 问题。不得因 `VMMonitorModeExtensions=False` 建议用户修改 BIOS。

### 下一份本地 Agent 任务：ROUND17

- 任务书：`firmware-analysis/round17/AGENT_TASK.md`
- 启动指令：`firmware-analysis/round17/START_PROMPT.md`
- **等待用户前置动作，尚未派发执行。**

用户必须先手动在 Security Center → Command Security → Program Blacklist 中移除/允许 `C:\Windows\System32\wsl.exe`，然后以“以管理员身份运行”的方式重启本地 Agent。Agent 不得代替用户修改黑名单，也不得尝试任何绕过方法；若仍被拦截立即停止。

主 AI 已指定固定方案：保留原有 C 盘 `Ubuntu` 不动，不迁移、不注销、不覆盖；新装独立 `Ubuntu-24.04` 到 `D:\WSL\Ubuntu-24.04`。先验证已安装 Store WSL 2.7.3.0；当前 VMP 已 Enabled，不盲目重装 WSL，不预先启用 legacy WSL/HypervisorPlatform 组件。发行版安装可直接用 Store WSL CLI 的 `--distribution` + `--location`；省略 `--no-launch`，允许首次启动交互式创建 Linux 用户，然后通过 `wsl --list --verbose`、`/etc/os-release`、注册 BasePath 验证。详见 ROUND17。

ROUND17 目标仍为准备 kernel-only 官方 manifest workspace，固定 common 到 ACK `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` 并记录 Clang/Rust/Bazel。此轮不打补丁、不编译。

### 第二 AI 新任务：ROUND58 Kleaf 实现，不再只做审查

第二 AI 已完成 ROUND54（独立 UFS 审查报告已上传）；ROUND57 已接纳其 P3 schema 精确计数修正为独立 follow-up draft。现在把新的实际构建准备任务分配给第二 AI：

- 分支：`ai-parallel/round58-kleaf-target-audit`
- 任务书：`kernel-baseline/round58/ROUND58_TASK.md`
- 启动指令：`kernel-baseline/round58/START_PROMPT.md`

ROUND58 要求第二 AI 在自己的分支上做可交付实现：基于 pinned ACK / 对应 Kleaf API 创建 no-`base_kernel` full-image Kleaf target patch candidate；制作 storage-first final `.config` 检查脚本和合成配置单元测试；形成 ROUND17 结束后可直接执行的 patch/Kconfig/build runbook。第一轮目标聚焦完整内核 Image 编译，不臆造 DTS/DTB/DTBO/boot image 路径，不声称已经运行 Bazel 或编译。

### 并行分工

| 执行方 | 当前任务 | 目标 |
|---|---|---|
| 用户 | 人工解除指定 wsl.exe 黑名单；以管理员方式重启本地 Agent | 解除 ROUND17 前置阻塞 |
| 本地 Agent | ROUND17（等待用户确认后才执行） | 新装独立 Ubuntu 24.04 到 D:，同步/固定 ACK kernel workspace |
| 第二 AI | ROUND58（专属 GitHub 分支） | 实现 Kleaf target 候选、配置验证工具与编译 runbook |
| 主 AI | 审核 ROUND58；继续固定源码 patch 系列集成准备和交接维护 | 合并工作成果前先核验，不写保护分支 |

PR #1 仍须保持 Draft/Open/unmerged；`ack18-dby-w09-dts-draft` 不得修改。Stage A 仍为唯一主线。编译产物不是设备验收，Stage A 实际启动和存储/基础硬件验收前不得进入 DerpFest Stage B。


## ROUND17 policy-path correction (2026-11-24)

The previous ROUND17 draft told the user to navigate to "Security Center → Command Security → Program Blacklist". This was an unsupported inference from the error phrase "configured Program Blacklist"; the ROUND16 report did not identify the product or policy owner. The user confirmed no such menu exists. **That UI path is withdrawn and must not be repeated.**

Only proven fact: a local Agent invocation of `wsl.exe` was blocked by a sandbox/program-execution policy, but the enforcement layer is UNKNOWN. It may belong to the Agent execution host, a managed policy, endpoint protection or another layer; do not assume Windows Security Center / Defender / any named vendor.

ROUND17 has been rewritten to passive diagnosis only:
- identify local Agent product/version and execution mode from existing UI/metadata/logs;
- identify policy owner and supported authorization flow using official docs for that exact product/version;
- do not call `wsl.exe` again until the block source and authorized approval path are understood;
- no alternate shell, wrappers, renamed/copy binaries, bypasses or security disabling;
- do not launch the whole Agent elevated preemptively; elevation only if a specific official install step demonstrably requires it.

Ask the user for the local Agent product name/version and a screenshot of the block message if passive metadata cannot identify it.

Fixed eventual distro plan remains: preserve current C: Ubuntu, install a separate Ubuntu-24.04 on D: only after supported WSL execution is authorized. ROUND58 second-AI Kleaf implementation continues independently.

## 最新补丁集成进展 — ROUND59（2026-11-24）

ROUND59 已完成完整 UFS 补丁系列的固定源码精确上下文模拟：
`kernel-baseline/round59/round59_ufs_patch_series_exact_source_integration.md`。

固定 ACK commit：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`。五个输入 source blobs（qcom,ufs.yaml / qcom,ufs-common.yaml / ufs-qcom.c / ufs-qcom.h / 只读 board DTS fixture）的 Git SHA 均与预先记录身份完全一致。

按顺序 ROUND32 → ROUND57 → ROUND36 → ROUND52-0001 → ROUND37（仅在 review-only DTS fixture）→ ROUND33 → ROUND52-0002，完成 7 份补丁共 **16/16 hunk** 的精确 old-context / new-line-anchor 匹配；ROUND52-0002 正确拆分到 ufs-qcom.h 与 ufs-qcom.c。无 fuzz 或 nearest-context fallback。367 条新增行的轻量扫描没有发现行尾空白。

重要修正：ROUND59 检出之前 ROUND57 patch 的 unified-diff hunk header 错误（旧 6/新 8 声明，但正文是旧 13/新 15；且 ROUND32 后实际起点是 165 而非 163）。已在 main 修复为 `@@ -165,13 +165,15 @@`，当前 blob SHA `3656f05ad01d54452b83591b762faaa71a16f592`。不要再使用旧 SHA `f282a695...`。ROUND32 原文件未修改。

**验证边界必须准确：** ROUND59 是从 GitHub 获取精确 source blob 后进行的 in-memory exact-context patch replay，不是真实 `git apply --check`、真实工作树应用或 `git diff --check`。也没有运行 checkpatch、dt_binding_check、dtbs_check、Kconfig resolver、Kleaf/Bazel 或编译；ROUND37 仍只对 `.dts.draft` fixture 成立，不是 ACK kernel 树内真实 DTS。该报告将帮助本地 build Agent 后续少走弯路，但不代表可启动镜像。

### WorkBuddy / 本地环境现状

- ROUND16：终态 `BLOCKED_BY_HOST_SECURITY_POLICY`，WSL 未部署、源码未同步。
- 用户已识别本地 Agent 为 **WorkBuddy**，所用模型为 **DeepSeek V4.1 Flash**。模型服务与 WorkBuddy 的命令执行沙箱属于不同层，不能由模型名称推断安全策略菜单或审批机制。
- 用户明确要求由 WorkBuddy 自行处理其命令执行权限/拦截来源；主 AI 不再让用户寻找未经证实的 Windows 菜单。ROUND17 已改为 WorkBuddy 被动诊断实际执行策略、查阅自身应用文档/日志，再按正式授权方式处理；禁止绕过策略或盲目重试 WSL。
- ROUND58：二号 AI 的 Kleaf target / .config helper / build runbook 实现任务在独立分支 `ai-parallel/round58-kleaf-target-audit`，继续并行推进。

下一步：主 AI 继续固定源码层审查与 patch integration prep；ROUND17 由 WorkBuddy 按自身执行策略处理，ROUND58 由二号 AI 实现。拿到真实本地工作树后再做真实 Git apply、schema、Kconfig 和 Image 编译。


## ROUND58 completed / primary review ROUND60（2026-11-24）

二号 AI 已提交 ROUND58 的完整 source-level 构建准备成果，独立分支保持：
`ai-parallel/round58-kleaf-target-audit`。

交付文件：
- Kleaf target patch: `kernel-baseline/round58/0001-add-dby-w09-full-kernel-kleaf-target.patch`（blob `fa2183850a40b3e5054da8b9f410c0a65e820f79`）。
- Final `.config` validator: `kernel-baseline/round58/check_dby_w09_config.py`（blob `5622b1e8e3dcf1c683e252e2abb1177de0b44435`）。
- Unit tests: `kernel-baseline/round58/tests/test_check_dby_w09_config.py`（blob `82acac9f1602228ed9a780a98f7aadc046d55cad`）。
- Implementation report/runbook: `kernel-baseline/round58/round58_kleaf_target_implementation.md`（blob `43be9adf30cc9cbff6443c554ef680e45cebf9b6`）。

ROUND58 设计采用固定 ACK BUILD 中的 no-`base_kernel` full custom kernel_build 样式；以 `gki_defconfig` 为底，复制 storage-first fragment 到源码树并经 `post_defconfig_fragments` 应用，第一阶段仅构建 `Image`，不加臆造的 board DTB/DTBO/boot-image 目标。

主 AI 已完成 ROUND60 独立复核：`kernel-baseline/round60/round60_primary_review_round58_kleaf_and_config_validator.md`。ACK pinned BUILD blob 与 insertion context 匹配；新增 132 行 fragment 与 main canonical config fragment 完全一致。Kleaf 官方 `main-kernel-2026` 文档说明 post fragment 在 defconfig 后应用、随后 olddefconfig 并检查最终 .config。配置检查器源码和九个 synthetic unit-test cases 已审阅；二号 AI 报告九项通过，但主 AI 未声称已在本地完整 checkout 中重新执行该测试。

必须继续准确区分：ROUND58 target patch 已写、静态上下文已检查；真实 git apply、buildifier、Bazel query、Kconfig/Kleaf config、actual .config checker、Image compile 全部仍 NOT_RUN。ROUND58 不是编译成果，也不是 bootable image。

ROUND60 对后续 runbook 加了两个执行注意点：所有 Bazel 命令经 tee 记录时要用 `set -o pipefail` 保留 Bazel 退出码；同一个 `//common:dby_w09` build 不要在两个阶段无缘无故重复执行，第一次得到 .config 后先 cquery/验证，只有源码配置有变化或明确 clean rebuild 才重跑。四个 Bazel jobs 仅是初始保守 CPU 上限，内存上限必须先测量 WSL/cgroup 实际值。

### WorkBuddy ROUND17 最新事实

ROUND17 已上传 `firmware-analysis/round17/round17_wsl_ack_workspace_deployment.txt`（branch `firmware-audit-v1`，blob `8efd13aa67774dceeef5c243f53044d474e3a37f`），状态 `BLOCKED_PENDING_USER_OR_ADMIN_APPROVAL`。

WorkBuddy 5.11.3.0 + sandbox-cli 5.11.4 的内部审计记录和静态资源表明：`wsl.exe` 是 WorkBuddy 自带默认 Program Blacklist 项，不是 Windows Defender 或 Windows 系统黑名单。应用内资源确认英文 UI 字符串为 Settings → Security Center → Program Blacklist。默认项是否能从 5.11.3.0 界面移除仍未由实机 UI 观察验证。ROUND17 没有改设置，没有再次运行 wsl.exe，也没有部署环境。用户已说由 WorkBuddy 自己处理，不要再把排查步骤推回给用户；主 AI 继续内核工作。

保留原 C: Ubuntu 的决定不变。WorkBuddy 解决自身策略后，才可继续独立 Ubuntu 24.04 D: 部署与官方 manifest sync。暂不要求用户以管理员方式盲目重启 WorkBuddy。

### 当前并行职责

- WorkBuddy：自行处理自身命令执行策略；恢复后执行本地部署/ACK workspace。
- 二号 AI：ROUND58 实现已提交并停止；其专属分支保留，不合并。
- 主 AI：继续 Stage A 源码级集成审查与准备；ROUND59 patch series exact-source replay、ROUND60 Kleaf candidate review 已完成。
- 下一次实际 build gate：有可用固定 ACK 工作树时执行真正的 `git apply --check` / 应用 / diff-check、dt_binding_check、Kconfig/Kleaf resolve 和 full custom Image 编译。

PR #1 仍 Draft/Open/unmerged；protected DTS branch 不改。Stage A 仍先于 DerpFest Stage B。


## ROUND61 — 持续式二号 AI 内核实现任务（2026-11-24）

用户明确要求二号 AI 不再只做一次性审查，而是持续承担一条实质性的 Stage A 移植工作流，直到 ACK 6.18.33 内核通过设备启动和存储验收，或只剩必须由用户/本地 Agent 处理的外部硬件动作。

### 二号 AI 新任务分支

- 专属分支：`ai-parallel/stagea-port-until-boot`
- 长期任务书：`kernel-baseline/round61/ROUND61_LONG_RUNNING_STAGEA_MISSION.md`
- 一键启动指令：`kernel-baseline/round61/START_PROMPT.md`
- 持续进度日志：`kernel-baseline/round61/PROGRESS.md`

任务不是只提交报告：二号 AI 必须按阶段持续执行真实补丁应用、UFS binding dt_binding_check、Kleaf/Bazel target 校验、实际 Kconfig/.config 解析、配置检查器验证、完整 DBY-W09 Image 编译；每次失败后修复并重跑受影响步骤。之后继续处理真实 DTS、memory handoff、PMIC 物理供电、AVB/ramdisk/boot header v2、受控启动计划和设备验收。每一阶段均在同一专属分支提交并更新 PROGRESS.md，不得做完单份报告便停止。

允许二号 AI复用 ROUND58 在 `ai-parallel/round58-kleaf-target-audit` 的 BUILD target、Python validator、9 个 synthetic tests；ROUND60 已完成的主审查只是源码设计审查，不等于实际 Bazel/Kconfig/编译通过。ROUND59 的 16/16 仅为 in-memory exact-context replay，不是真实 `git apply`。所有实际检查均须重新执行并留存日志。

### 长期任务阶段

1. 在获准 Linux 环境中建立精确 ACK worktree，common commit 必须为 `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`。
2. 对 ROUND32 → ROUND57 → ROUND36 → ROUND52-0001 → ROUND33 → ROUND52-0002 执行真实 `git apply --check` / apply / diff / checkpatch；ROUND37 是报告仓库里的 DTS fixture，不能假装它已成为内核 source-tree DTS。
3. 对 UFS binding 运行真实 `dt_binding_check`，修正问题并重跑。
4. 集成 ROUND58 Kleaf target 和配置检查器，执行 Bazel query/cquery、最终 Kconfig 解析和实际 .config 检查。
5. 编译 DBY-W09 storage-first full custom Image；失败则定位、修复、重编译，直到成功或有证据的外部执行限制。
6. 在可信 RAM / reserved-memory / PMIC 输入供电信息具备后，将 board DTS 迁入真实 ACK source path，构建 DTB/DTBO。
7. 独立关闭 legacy boot header v2、separate ramdisk、AVB/vbmeta 和 ABL 入口证据；先形成非刷写 packaging/rollback plan。
8. 只有经主 AI/用户审查并明确授权后，才进行任何临时启动/设备操作；不得自行刷写分区、解锁、root 或绕过安全策略。

### 本地 WorkBuddy 状态

ROUND16 因 WorkBuddy 的 command-safety/sandbox 层拦截 `wsl.exe` 而 BLOCKED；ROUND17 已将策略责任定位为 WorkBuddy 自身，不是 Windows Security Center 菜单。用户已明确表示由本地 Agent 自行处理。主 AI 不再要求用户查找不存在的 Windows 菜单，也不让二号 AI重复研究 WorkBuddy。二号 AI 应在其自身合法可用的运行环境里继续；本机 WorkBuddy 的部署问题不构成停止公开源码/补丁工作流的理由。

### 任务边界与当前真实状态

- 二号 AI只能写 `ai-parallel/stagea-port-until-boot`，不能修改 main、firmware-audit-v1、protected DTS branch 或 PR #1。
- PR #1 继续 Draft/Open/unmerged。
- 不得编造 RAM ranges、AVB descriptor、PMIC 输入电源或启动链；不绕过主机安全策略；不刷写设备。
- 当前仍没有实际 kernel build / Image / DTB / boot / UFS storage acceptance 证据。
- Stage A 仍是唯一主线；Stage A 真正验收前不开始 DerpFest Android 17 Stage B。

主 AI / ChatGPT 继续并行推进固定源码分析与设备启动链阻塞项，审查二号 AI 每阶段产物，并将已验证结果同步到主仓库。该长期任务不是把项目交给二号 AI后停止主 AI 工作。


## ROUND62 — DBY-W09 same-device boot-chain reference reconciliation (2026-11-24)

Primary AI inspected the pinned public repository `svesnav/linux-dby-w09` at commit `116cb1fe06110543ce03217e8bd8f35c12ca89c3` and recorded a cross-reference report:

`kernel-baseline/round62/round62_same_device_abl_bootv2_ramdisk_dtbo_reference.md`

Useful same-device findings:
- The external project reports Huawei ABL using boot header v2 plus a separate `ramdisk` partition.
- Its README says `fastboot boot` (RAM boot) is refused on that tested setup.
- Its ABL-accepted DTBO must fill `/rootparam`, or the tablet returns to fastboot.
- It reconstructs a replacement boot image by unpacking the exact stock header-v2 boot image and preserving its metadata.
- It builds a separate ramdisk payload and writes it over the stock ramdisk partition while preserving the footer described by that project's verified stock image.

These are same-model, strong structural cross-references; they are **not** direct proof of the user's current HOS4.3 bootloader/partition/footer behavior. External project describes its own Linux 7.0 environment and the DTS itself references HOS4.2. Never copy its stock image hash, 96 MiB boot size, 2 MiB ramdisk size, offsets, cmdline, AVB footer offsets, RAM map, or DTB into this project.

The reported refusal of `fastboot boot` raises the possibility that a first test may require partition writes. Therefore a temporary RAM-boot route must not be assumed; any write/flash action requires exact local HOS4.3 metadata, a reviewed rollback plan, and separate explicit user authorization. No partition writes are authorized here.

ROUND62 has been added as Phase E/F context to the second AI's ROUND61 long-running mission. It must not block ROUND61 Phase A–D real patch/schema/Kconfig/Image build work. Stage A remains the only mainline; Stage B waits for real Stage-A device acceptance.


## ROUND63 — HOS4.3 UFS PHY vdda-phy-always-on lifecycle gap (2026-11-24)

Primary AI compared the exact local HOS4.3 UFS PHY overlay inventory with the pinned ACK 6.18.33 QMP UFS PHY driver and found a new concrete integration difference.

Local evidence:
- `firmware-analysis/round8/round8_summary.json` on `firmware-audit-v1`, blob `2e5eec1be7d1364d90de7a8a500b516fcdddf3e1`.
- Stock DTBO entry 8 fragment@63 targets `/soc/ufsphy_mem@1d87000` and records `vdda-phy-always-on`, L5 analog supply, and max-load values 89900µA / 18800µA.
- This report is explicitly entry-8 evidence only; actual selected overlay/runtime regulator state remains UNKNOWN.

Pinned ACK evidence:
- `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c`, blob `8af777f7ddd0385a6bb9d9b9563f0e6329699cd3`: SM8250 static vreg list already supplies 89900/18800µA loads, but `qmp_ufs_power_off()` bulk-disables both rails and the driver never parses `vdda-phy-always-on`.
- `Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml`, blob `fba7b2549ddee7ee4e048277a11a7da053d52887`: strict `additionalProperties: false`, no `vdda-phy-always-on` nor the two max-microamp properties.
- `drivers/regulator/core.c`, blob `39d317ad73a33c4aa27e179cc436d8bf4daf5bcc`: a consumer's load vote contributes to DRMS while its regulator enable count is non-zero; dropping load to zero withdraws the active vote.

Downstream Qualcomm behavior cross-check:
- `LineageOS/android_kernel_oneplus_sm8150` commit `9f007fac27dce21d29d8230753b71d5634b8a00e`, `drivers/phy/qualcomm/phy-qcom-ufs.c` blob `f70871f45279ccb15f668ec7ce974c0f82d79004`: recognizes `vdda-phy-always-on`; its PHY power-off path clears the L5 consumer load but does not call regulator_disable for that rail.

Primary AI has added:
- Report: `kernel-baseline/round63/round63-ufs-phy-always-on-lifecycle-compatibility.md`.
- Driver candidate: `kernel-baseline/round63/0001-phy-qcom-qmp-ufs-preserve-vdda-phy-always-on.patch.draft`, current blob `b0f6b5f72d773bf9797b527ff4d2ab71060b6d54`.
- Binding candidate: `kernel-baseline/round63/0002-dt-bindings-phy-qmp-ufs-vdda-phy-always-on.patch.draft`, blob `a6668eebe293f9a35e9c08d6be4f37c4340e7ddd`.
- Main review-only DTS draft now declares `vdda-phy-always-on;` and removes the redundant `vdda-phy-max-microamp=89900` / `vdda-pll-max-microamp=18800` properties because ACK's static SM8250 vreg list already carries those values and the strict schema does not accept the board-side properties. Updated DTS blob `ceb12e3d869225f10e9d8d2beb277d66b4bb709c`.
- `dts/README.md` now records the decision.

The driver candidate retains the vdda-phy consumer enable reference from first PHY power-on through later PHY power-off cycles, toggles its load vote between the pinned init load and zero, leaves other PHY regulator rails on the existing bulk path, and balances the retained enable through a devm cleanup action before regulator handles are released. Nodes without the property retain the old bulk path. This is a design candidate only.

**Not done:** no real git apply, checkpatch, dt_binding_check, C compile, Kconfig, Kleaf build, regulator measurement or hardware test. The provider-removal/device-link ordering and all error paths must be reviewed and tested. ROUND11/21 physical PM8150 L5 input-supply topology remains unresolved; ROUND63 does not invent a physical parent rail.

The updated patch series for real integration now includes the QMP PHY binding and driver candidates before final board DTS schema/DTB validation. See ROUND63 §8 and the ROUND61 long-running AI task update.


### ROUND63 follow-up — exact candidate hunk replay and QMP regulator-list verification

Primary AI checked every QMP UFS `vreg_list` in the exact ACK source: all 15 lists put `vdda-phy` first and `vdda-pll` second; SM8250 load values remain 89900/18800µA. It also checked the pinned `regulator_bulk_data.init_load_uA` field and the device devres action declaration. The candidate now explicitly includes `linux/string.h`.

Final driver patch blob: `a06b7d3fc19e0b23895b0013ab9ac322d84cdda5`. A deterministic in-memory exact-context replay against the exact pinned source blobs verified 5/5 driver hunks and 1/1 binding hunk with declared counts and anchors. This is **not** `git apply`, checkpatch, dt_binding_check or compilation.

Updated report: `kernel-baseline/round63/round63-ufs-phy-always-on-lifecycle-compatibility.md` (commit `2bfe3e0d2d4f6b17e057a8e9e5ffc7b4d4bab2d6`). The second AI ROUND61 task must use the final driver patch blob above and independently run the real worktree checks.


ROUND63 board-draft identity correction: after refining the explanatory comment, the current main review-only `dts/dby-w09-ack18-board.dts.draft` blob is `c209d519614fb0ff89b042ce274191b20120a09a`. This supersedes the earlier intermediate blob `ceb12e3d869225f10e9d8d2beb277d66b4bb709c`; the protected DTS branch remains unchanged.


## ROUND16 最终状态纠正 — 环境与 pinned ACK workspace 已就绪（2026-11-25）

本节覆盖此前所有将 ROUND16 标为 BLOCKED_BY_HOST_SECURITY_POLICY、等待 ROUND17 或“尚未部署/尚未同步”的历史派发指针。不得再按旧状态安排部署。

权威报告位于 firmware-audit-v1：
- firmware-analysis/round16/round16_wsl_ack_workspace_deployment.txt
- blob: c9516f20d3e13cb5d5ec42e41bec4c8a05b25123
- firmware-audit-v1 branch tip: 99f93d2e81ccb88715bf47ed1aff167d4cd98c55
- final status: **WSL_AND_PINNED_ACK_WORKSPACE_READY**

报告已实测确认 WSL 2.7.3.0 / kernel 6.6.114.1-1、Ubuntu 24.04.5 LTS 安装在 D:\\WSL\\Ubuntu-24.04、WSL2、默认用户 kerneldev；官方 common-android17-6.18 manifest 58 projects / 约 41 GiB 已成功同步；common detached HEAD 精确为 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a；工作树 clean；Clang r584948c、Rust 1.91.1.p3、Bazel 8.7.0 与 ROUND39 对账一致。原 C: Ubuntu 未改动。

**禁止重做：** 不重新部署 WSL/Ubuntu，不重装/迁移原发行版，不重新 repo init、repo sync 或下载 ACK 源码/工具链。现有 workspace 为 /home/kerneldev/work/matepad11/ack-6.18.33。

### 当前本地执行任务：ROUND18

- 任务书：firmware-analysis/round18/AGENT_TASK.md（main）
- 启动指令：firmware-analysis/round18/START_PROMPT.md（main）
- 报告目标：firmware-analysis/round18/round18_patch_schema_kconfig_first_build.txt（firmware-audit-v1）
- 授权内容：在独立 ROUND18 workspace 副本中应用指定 ACK UFS/QMP PHY driver 与 binding patches、执行真实 Git/checkpatch、UFS/PHY dt_binding_check + fixtures、Kleaf BUILD patch、Bazel query/cquery、实际 Kconfig/.config 解析和首次 Image-only 编译。
- ROUND18 不修改原始 ACK workspace；不修改 protected DTS branch、PR #1 或二号 AI分支；不连接或操作设备。
- WSL 7.3 GiB 内存本轮先用低并发 jobs=2，不擅自修改 .wslconfig；如 OOM，保存证据并单独等待 memory 配置授权。
- ROUND57 minItems/maxItems 补丁因真实 dt-schema meta-schema 不兼容，本轮跳过，改用正反例验证 8 项约束；ROUND37 board DTS delta 因真实 DTS path / RAM / PMIC gates 未关闭而排除。
- ROUND12 AVB 仍 BLOCKED，但不阻断本轮 Image-only 编译；本轮不生成 board DTB/DTBO 或 boot package。

### ROUND61 二号 AI独立工作

二号 AI继续只写 ai-parallel/stagea-port-until-boot。其已完成真实 Git patch series application，但 UFS schema example validation 仍有 power-domains/unevaluatedProperties diagnostics；Kleaf query、Kconfig 和 Image build 尚未完成。ROUND18 的本地 WSL实测是独立交叉验证，不覆盖它的分支或结果。

Stage A 仍未完成：没有设备启动和 UFS/storage acceptance 证据；Stage B Android 17 DerpFest 仍不得开始。

---

## ROUND18 revision 1 — 修正 ROUND32 补丁集（2026-11-25）

ROUND18 原始任务书第 5 节曾把 ROUND32 的旧 patch blob `efe2d932da34716c631de22d89aba19730cc7f50` 放入 ACK 应用序列。该做法现已废弃：固定 ACK `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` 已由 `qcom,sc7180-ufshc.yaml` 选择 SM8250，在 `qcom,ufs.yaml` 重复添加 compatible 会造成重复 schema 选择。

二号 AI 修正版候选 `round32-corrected-sc7180-clock-names.patch`（当时 blob `fade9cb2bdfd544c6736c7595af8380726edf318`）在真实 GitHub Actions Run `45448025597` 的 `git apply --check` 中仍然失败；此前 Run `45447645008` 同样失败。它不能视为可用补丁。ROUND18 本地 Agent 必须在独立 ACK 副本中基于准确上下文重制最小补丁，先单独通过真实 `git apply --check`，再 apply + diff-check，然后执行 ACK 版本 dt-schema 和 7/8/9 clocks 正反例。

当前二号 AI 专属分支仍由它独立维护；本地 ROUND18 仅读取它的候选补丁和报告，不得向该分支写入。ROUND18 其它可独立推进的 Kleaf/Bazel/Kconfig/Image-only 工作不得因 clock schema gate 阻断而停止。主线授权以 `firmware-analysis/round18/AGENT_TASK.md` revision 1 和 `START_PROMPT.md` 为准。

---

## ROUND18 revision 2 — ROUND61 patch sequencing correction（2026-11-25）

二号 AI 最新 ROUND61 进展发现两个必须反映到本地 ROUND18 的点：
1. `round32-corrected-sc7180-clock-names.patch` 当前观察 blob `2a038774ffac4cc0d742a52baeb1d41ce2aa1dfb` 已修正 hunk count（3 old / 4 new），但仍须本地真实 `git apply --check`；旧 blob `fade9cb2...` 是失败版本，不再采用。
2. 新增 `round36-corrected-power-domain-range.patch` blob `a6e8eeaf9303e428e644245749e6daec4d0e38ac`，必须在 ROUND52-0001 之后应用，因为 ROUND52-0001 会整体替换 `qcom,ufs-common.yaml`。顺序为 ROUND36 → ROUND52-0001 → ROUND36 corrected range → ROUND32 corrected clock count → ROUND33 → ROUND52-0002 → ROUND63 PHY binding/driver。

二号 AI 当时 branch HEAD `faae6c044369c24afbdc270eb53fd2e0d31ad451` / PROGRESS blob `2a4c91b9e7a74e3021783bde3b2221d84ea63aee` 报告工作流顺序已修复，新验证仍 pending。必须读取最新分支而不是沿用快照。`dt_binding_check` / `dt-doc-validate` 要覆盖 qcom,ufs.yaml、qcom,sc7180-ufshc.yaml、qcom,ufs-common.yaml 和 QMP UFS PHY schema。



## 2026-11-25 — 同设备 DerpFest 成功先例与 ROUND18 首次 Image 构建完成

### A. 用户已确认的同设备成功先例（项目固定前提，不得反复询问）

用户明确说明：本项目采用“先移植 ACK/GKI 6.18.33，再移植 Android 17 DerpFest”的路线，正是因为已有另一位开发者在**同一设备 Huawei MatePad 11 DBY-W09、同一 ACK/GKI 6.18.33 内核基线**上成功进入 Android 17 DerpFest 系统。用户提供的进度基准是：约两天进入系统，约一周完善其余功能。

该信息属于用户明确提供的先例事实；本交接更新尚未把该开发者的原始仓库/帖子/提交 SHA 绑定为独立证据，因此不要伪称已完成来源级复核，也不要凭空补造开发者身份或链接。但也**不得再次向用户询问“是否同设备、是否同内核、是否已经有成功案例”**——这些关键前提已经明确确认多次。

执行含义：
1. 将“同一 DBY-W09 + ACK/GKI 6.18.33 + Android 17 DerpFest 已有成功启动先例”视为已知可行性基线；项目不是从零证明这套组合能否启动。
2. 主任务改为尽快定位、复核并复用成功先例的 device tree、内核补丁、boot/ramdisk/DTBO、vendor/HAL/VINTF 和启动参数；再与当前 HOS4.3 固件及 ACK 固定源码做差异分析。凡是能从成功方案复用的内容，不应重新设计或重复探索。
3. 继续遵守用户确定的顺序：先完成 DBY-W09 ACK/GKI 6.18.33 内核适配和构建，再集成 Android 17 DerpFest；不能因为成功先例已经进入 DerpFest，就擅自颠倒用户要求的实施顺序。
4. 把“尽快进入 DerpFest 桌面”设为首要可见里程碑；相机、音频、蓝牙、传感器、休眠等非启动关键功能放到桌面启动后逐项完善。UFS、内存交接、显示/触摸、启动链等实际启动必需项仍需解决，不能为了赶时间编造参数或跳过安全验证。
5. 时间上可以把同设备成功先例作为加速依据，但“2 天 / 1 周”是该先例的用户报告，不是对当前执行周期的保证。每次估时必须基于已复用资料、未闭合 gate 和真实进度，不要再用“从零移植”的假设给出 4–8 周基线。
6. 后续新会话和所有 AI 必须先读本节；不要要求用户重复解释这项背景。优先从现有上下文、公开仓库、已记录项目链接中寻找该成功方案。若暂时无法定位来源，明确记录来源定位待办并继续其他工作，不要把问题退回给用户反复确认。

### B. ROUND18 本地 Agent 最终结果（2026-11-25）

最终脱敏报告：
[`firmware-audit-v1/firmware-analysis/round18/round18_patch_schema_kconfig_first_build.txt`](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round18/round18_patch_schema_kconfig_first_build.txt)

- Git blob：`9d756587c675387d676a53eae3dcca181bde0f26`
- 固定 ACK：`android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- 本机 WSL2 Ubuntu 24.04.5 内真实执行；原始 Repo workspace 起止均 pristine，所有修改均在独立 ROUND18 副本内。
- 补丁集成：9/9 最终补丁真实 `git apply --check`、`git apply`、`git diff --check` 全通过。两项上游候选补丁存在 hunk/空行缺陷，Agent 在副本内做了最小修正后重新以默认完整上下文验证通过；没有写入二号 AI 分支。
- Device-tree schema：4 个目标 schema、4 个 example DTB；`dt_binding_check`、`dt-doc-validate`、直接 `dt-validate` 通过。15 个正反例 MISMATCH_COUNT=0。报告同时记录 dtschema 版本参数差异及 dt-validate 可能 rc=0 但输出诊断的陷阱。
- Kleaf/Bazel：`//common:dby_w09` query 和 cquery 均通过；cquery 得到 .config、Image、System.map、vmlinux 四个预期输出。
- Kconfig：真实 Kleaf config target 生成最终 `.config`；31/31 个 storage-first 必需项为 `=y`，fragment 的 30/30 显式请求项与最终配置一致。
- 首次 Image 编译：真实 `tools/bazel build --jobs=2 //common:dby_w09`，exit 0，耗时约 360 秒。Image 44,820,992 bytes，SHA-256 `983b342ea5f0b48d5b9a808f37ba8405d92d283d1f9303a7c5054e26fbd8d884`；System.map、vmlinux、.config 均生成。内核 banner 为 `6.18.33-android17-5-maybe-dirty-4k`。
- 当前准确里程碑：`IMAGE_BUILD_PASS / STAGE_A_BUILD_READY`。

边界必须准确：ROUND18 没有生成板级 DTB/DTBO、boot.img、vendor_boot、init_boot 或刷机包；没有连接设备、ADB/fastboot、解锁、root、分区写入或实机启动。因此这代表**首次内核 Image 编译成功**，不代表已经点亮平板，也不代表 Stage A 设备验收完成。

### C. 下一步优先级（按“复用成功先例、尽快点亮”执行）

1. 主 AI 与二号 AI优先定位并拆解同设备成功 DerpFest 方案，逐项比较其源码版本、DTS/DTBO、boot header v2/ramdisk、vendor blobs、VINTF/HAL、AVB 和启动命令。能复用的现成实现优先复用；禁止重复证明已由先例证明的组合可行。
2. 将 ROUND18 已成功的补丁集和 Image 构建基线作为当前 ACK build checkpoint，避免重复部署、Repo sync、重跑已通过的 9/9 patch/schema/Kconfig 任务；后续变更必须基于该 checkpoint 做增量验证。
3. 优先闭合真正阻止首次启动的目标专属差异：最终 post-ABL FDT/内存交接、必要 PMIC/UFS 供电、板级 DTS/DTB/DTBO、HOS4.3 legacy boot-v2/ramdisk/AVB 组合。先以成功先例证据核对这些问题是否已被同型号方案解决，再决定是否需要本机额外采集。
4. 首次启动目标为进入 Android 17 DerpFest 桌面；显示/触摸及系统分区挂载等必需路径优先。其他硬件功能作为第二阶段完善。
5. 任何烧写或分区操作仍需用户另行明确授权；不得从“已有开发者成功”推导出本设备已授权写入。



## 2026-11-25 ROUND19 completed; ROUND20 is the next local task

### ROUND19 report and findings

Final sanitized report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round19/round19_hos43_boot_ramdisk_avb_dtbo_audit.txt
Blob: c96b30ca763b29dcc58aada6e93c25faaea8e34d

ROUND19 reused the existing ROUND2/ROUND3 firmware work copies. It did not re-extract firmware, deploy WSL, repo sync, rebuild Image, access the device or modify any original image.

Results:
- Boot-chain inventory and boot-header parsing PASS. boot.img is Android header v2 / 4096-byte page; ramdisk.img is standalone header v0 with kernel_size=0; stock boot payload includes kernel, embedded ramdisk and DTB.
- Ramdisk inventory PASS. The ramdisk is gzip + SVR4 CPIO newc with 17 entries. /init is a statically linked AArch64 ELF; no text fstab, ueventd, init rc, SELinux policy, .ko, modules.load or modules.blocklist is present. /firmware/android/fstab exists in the base DTB. The Android 12 ramdisk/system fingerprint and Android 11 kernel/vendor metadata split is evidenced in the stock package.
- AVB parser audit PASS WITH PRELIMINARY status. No trusted avbtool was installed. A local read-only parser with bounds checks passed 7/7 synthetic tests. Footer/header/descriptor results have independent arithmetic and DTB-list cross-checks, but no independent trusted AVB implementation cross-check exists. Do not treat it as final AVB verification.
- Nine-DTBO audit PASS. Base DTB contains /memory but its reg is all zero. /chosen has bootargs but no linux,uefi-* memory-map metadata. None of the nine DTBOs changes /memory, /chosen, /reserved-memory or /firmware/android/fstab. No stock overlay solves the memory handoff.
- ABL triage BLOCKED / not applicable: no ABL binary exists in the existing extraction directory.
- Important unresolved AVB inconsistency U-8: AVB hashtree image_size values for system, odm and cust exceed independently measured LP partition sizes; the five AVB hashtree image sizes also exceed super.img. Do not use these values as partition geometry until reconciled.

### Superseding user instruction: no further public-repository search for the private success precedent

The user has explicitly clarified that the same-device Android 17 DerpFest developer does not intend to open-source the implementation. Previous handoff wording that asked AIs to locate this private implementation through public repositories/posts is superseded. Do NOT search for it, ask the user to provide it, or repeat the same public repository lookup. The user-confirmed same-device / same ACK-GKI 6.18.33 success is already an accepted project premise. We must implement independently from existing HOS4.3 evidence and the pinned ACK source.

### ROUND20 active task

Task:
- firmware-analysis/round20/AGENT_TASK.md
- firmware-analysis/round20/START_PROMPT.md
- report destination: firmware-audit-v1/firmware-analysis/round20/round20_efi_stub_memory_handoff_and_boot_payload_compatibility.txt

Purpose: read-only inspection of the already-built ROUND18 Image, .config, vmlinux and System.map to determine EFI_STUB / PE-COFF capability and trace ACK's normal-vs-EFI memory handoff path; inspect the stock boot.img kernel payload format; measure deterministic gzip and raw/gzip boot-v2 payload capacity; verify storage drivers are built-in. No rebuild, source modification, firmware modification, device access, ADB/fastboot or boot packaging. Use only existing local files and installed tools.

The most important distinction: an EFI-capable Image does not prove Huawei ABL invokes EFI Stub. Only local Image capability can be established offline; ABL entry choice and final runtime FDT remain UNKNOWN without ABL/device evidence.

ROUND18 must not be repeated: the Image is already built at /home/kerneldev/work/matepad11/ack-6.18.33-round18/bazel-bin/common/dby_w09/Image, size 44,820,992 bytes, SHA-256 983b342ea5f0b48d5b9a808f37ba8405d92d283d1f9303a7c5054e26fbd8d884. No board DTB/DTBO/boot image exists yet.

Continue to keep all device writes/flash/boot operations gated on separate explicit user authorization.

## 2026-11-25 — WQSQW 移植群聊补充：base DTB 空壳、DTBO 变体选择、驱动 built-in

用户提供了另一位 DBY-W09 内核移植者 WQSQW 的群聊记录。该聊天不是正式设计文档，个别架构性说法尚未独立验证；但其中三个工程判断与我们已有 HOS4.3 固件证据高度吻合，应作为后续移植原则：

### 1. Base DTB 可能只是骨架，必须以最终 overlay 后的有效树为准

WQSQW 表述：“华为是留了个空壳指向 DTBO，多固件就由 DTBO 抉择。”

已有本机证据相互印证：
- ROUND7：base FDT 有 `/rootparam` 空节点；root memory node 存在但 `reg` 为全零占位值。
- ROUND8：原厂九个 DTBO entry 均已从已有 work copy 解出，fragment targets 145/145 resolved；entry 8（board-id `0x206a` / VG）包含 UFS Host/PHY 的状态、供电和 `vdda-phy-always-on` overlay 属性。该报告明确说明 overlay 是配置意图，不代表已证明 runtime selection。
- ROUND19：九个变体分别填充 `/rootparam` 的五项产品/板型属性；没有一个 overlay 写入 `/memory`、`/chosen`、`/reserved-memory` 或 `/firmware/android/fstab`。

后续规则：
1. 禁止仅凭 base DTB 直接断定某个硬件节点最终状态。
2. 板级 DTS 对照应按 `base DTB + 实际选中的唯一 DTBO entry + ABL 运行时修改` 重建有效树；不能把九个 DTBO 全部叠加，也不能假设 entry 8 一定在当前设备被 ABL 选中，除非有同次启动证据。
3. 每个关键节点（UFS Host/PHY、panel、touch、Wi-Fi/BT、audio、camera、regulators、reserved-memory、memory、rootparam）都要标记其属性来自 base、selected overlay 还是 ABL handoff。
4. 九个 stock DTBO 不提供 RAM range 或 EFI handoff，不能把 memory gate 误认为只需选择正确 overlay 就会自动解决。

### 2. 启动关键驱动优先 built-in，而不是依赖未挂载分区中的 .ko

WQSQW 表述：“驱动直接编进内核。”

这与当前 storage-first 设计一致，并且 ROUND18 已把第一阶段最关键的驱动设置为 built-in：
- UFS Host / Qualcomm UFS / QMP UFS PHY；
- SM8250 GCC、RPMh、RPMhPD、Interconnect；
- ARM SMMU；
- DM / DM-Verity / FEC；
- EROFS。

ROUND18 的最终 `.config` validator 实测 31/31 项为 `=y`，Image 编译成功。不要重复这些已完成的配置检查。

后续规则：
1. 任何 first-stage mount 必需驱动，优先 built-in，除非能证明模块在系统分区挂载前由可用的 ramdisk/vendor-ramdisk/bootloader 路径加载。
2. 明确区分四种对象：Linux driver（可 built-in 或 `.ko`）、外部 firmware blob（由驱动在运行时加载）、DTB/DTBO 硬件描述、vendor 用户态 HAL/service。不能把“驱动编进内核”误解为驱动需要的 firmware blob 也必须静态链接进 Image。
3. ROUND19 只证明 standalone `ramdisk.img` 的 CPIO 中没有 `.ko` / modules.load；这不证明 vendor、odm 或其他分区绝对没有模块。若未来依赖模块，必须明确其实际分区、加载时机和 first-stage 可达性。
4. 为尽快首次进入桌面，继续采用启动依赖优先：UFS、PHY、RPMh/电源、内存交接、显示/触摸优先；非启动关键相机、蓝牙、音频和传感器可后续完善。

### 3. “HarmonyOS 微内核”群聊解释仅作背景，不直接作为本项目技术结论

群聊中关于“微内核只保留进程调度、内存管理、IPC，文件系统/网络/驱动全部用户态”的表述是概括性讨论，不能据此断定 DBY-W09 HOS4.3 的 Linux/Android 驱动实际架构。我们当前移植目标是 Linux ACK 6.18.33，仍按 Linux kernel driver、device tree、firmware、vendor userspace 的实际分层推进；不要因为群聊措辞改造成微内核式设计。

### 4. 对当前实施的直接影响

- ROUND18 的 built-in storage-first Image 是正确 checkpoint，不回退。
- ROUND19 已有九个 DTBO 证据作为后续有效设备树构建的输入，不重跑九个 entry 的扫描。
- 下一步继续 ROUND20 对现有 Image 做 EFI Stub / PE entry、memory handoff 路径和 boot-v2 payload 体积只读核验。
- 在生成真实板级 DTB/DTBO 前，必须先确定实际 overlay/ABL handoff 证据；未确定的内存地址和 PMIC 物理 parent supply 仍然禁止猜测。
- 本聊天由用户提供，属于有价值的移植经验线索，不等同于 WQSQW 源码或设备运行日志。可与已有报告互相印证的内容按上述边界使用，其他内容保持待验证。

## 2026-11-25 — ROUND20 completed: EFI entry, memory handoff and boot-v2 size audit

Final sanitized report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round20/round20_efi_stub_memory_handoff_and_boot_payload_compatibility.txt
Blob: 4ff1928bd1cc3043f3908b69289503d5650ab900

ROUND20 reused the ROUND18 Image/.config/vmlinux/System.map, pinned ACK source tree, ROUND2 boot.img extraction and ROUND19 image/ramdisk findings. It did not rebuild, modify source/config/firmware, create a boot image, touch AVB, or access the tablet.

Verified results:
- The exact ROUND18 Image has CONFIG_EFI_STUB=y and CONFIG_EFI_GENERIC_STUB=y, a valid ARM64 PE32+ header, EFI_APPLICATION subsystem, and an executable PE entry at RVA 0x23D7C40. The PE field, vmlinux symbol __efistub_efi_pe_entry, and pinned linker expression agree.
- This proves Image capability only. It does NOT prove Huawei ABL invokes the PE entry or that the final runtime FDT includes UEFI metadata.
- ACK source confirms classic arm64 memory discovery skips a /memory reg with size zero. On the EFI-memory path, efi_init() discards DT-derived memblocks and rebuilds from UEFI memory descriptors. Thus this path can bypass the zeroed memory node, but only if the required EFI system-table and memory-map metadata are actually available.
- There are two possible firmware-side ways for kernel EFI memory discovery to be active: enter the PE/COFF EFI stub, which adds linux,uefi-* properties; or enter the ordinary arm64 Image while ABL itself supplies complete linux,uefi-* properties in /chosen. The latter remains possible even though the stock kernel has no PE header.
- The stock kernel payload is gzip, max-compression, mtime=0. The decompressed stock Image has ARM64 magic but res5=0, proving it has no PE header and cannot be launched as an EFI application.
- gzip -n -9 of the ROUND18 Image is 17,802,671 bytes and reproducible. Raw and gzip payload scenarios both fit the given 96 MiB boot capacity. The gzip scenario with the existing ramdisk and DTB ends at 19,996,672 bytes, 4,460,544 bytes below the stock footer original_image_size. This is capacity arithmetic only; any payload change invalidates existing AVB integrity, and ABL acceptance is unproven.
- Storage chain built-ins from ROUND18 are present, and no .ko artefacts were produced. Two config gaps are real: CONFIG_DEVTMPFS is unset and CONFIG_PINCTRL_MSM is unset. Neither is yet proven to block boot; userspace device-node strategy and UFS DT pinctrl use need targeted inspection.

Highest-priority unresolved items:
1. ABL/runtime FDT: determine whether the loader enters PE or classic Image and whether it publishes the UEFI system-table + mmap properties. Existing extracted base DTB alone cannot answer this.
2. DTB preservation on EFI path: CONFIG_EFI_ARMSTUB_DTB_LOADER is off. If the stub runs, it must obtain the existing platform DTB via DEVICE_TREE_GUID; otherwise it generates an empty DTB, losing /firmware/android/fstab and other Huawei nodes.
3. First-stage /dev behavior with CONFIG_DEVTMPFS unset.
4. Whether the actual UFS host/PHY nodes in base DTB and the nine DTBOs reference Qualcomm TLMM pinctrl states, and whether UFS rails/pinctrl are required at early boot.
5. AVB re-signing/verification and exact ABL payload policy remain blocked; do not create or deploy a candidate image.

## 2026-11-25 — ROUND21 dispatched: first-stage devtmpfs and UFS pinctrl/overlay audit

Task files:
- firmware-analysis/round21/AGENT_TASK.md
- firmware-analysis/round21/START_PROMPT.md

ROUND21 is a local, offline, read-only inspection of the existing ROUND19 ramdisk /init ELF, base DTB and nine DTBO work copies, plus the pinned ACK Kconfig/source and ROUND18 final .config. It must answer whether Android first-stage init can create/populate /dev without devtmpfs, and whether UFS host/PHY DTS properties actually require CONFIG_PINCTRL_MSM. It also maps only the relevant UFS supply/power-domain/pinctrl references across variants; no assumption that board-id 0x206a/VG is the runtime-selected overlay.

No re-extraction, WSL deployment, repo sync, network download, package install, Image rebuild, source/config/DTS edits, boot packaging, signing, ADB/fastboot/device connection or flash. Upload one sanitized text report to firmware-audit-v1/firmware-analysis/round21/ and stop. Do not modify main source, protected DTS draft, second-AI branch or PR #1.

The project remains at Stage A build-ready, not device-boot accepted. ROUND18 Image is the stable baseline; do not rebuild until ROUND21 determines whether the two configuration gaps should be corrected.

## 2026-11-25 — ROUND21 completed: first-stage /dev and UFS pinctrl/overlay audit

Final sanitized report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round21/round21_first_stage_devtmpfs_and_ufs_pinctrl_overlay_audit.txt
Blob: 3b38e822f0a00e2f3209b9aebb5da1b0f9463d07

ROUND21 reused the already-existing ROUND18/ROUND19 local work copies. It did not execute /init, modify source/config/DTS/DTBO/firmware, rebuild, package, or access the device.

Verified findings:
- HOS4.3 /init (AArch64 static ELF) explicitly mounts tmpfs on /dev in FirstStageMain, creates /dev/kmsg, random, urandom, ptmx and null with mknod(), and uses netlink uevents plus sysfs coldboot/regeneration to discover/create block nodes. Static code cross-references support this path. No devtmpfs references were found. Therefore CONFIG_DEVTMPFS is NOT required by this exact first stage; CONFIG_TMPFS=y is already present.
- DEVTMPFS_MOUNT is not needed either. Pinned ACK Kconfig explicitly excludes initramfs boot from the automount option's use case; this /init mounts /dev itself.
- Base UFS host / PHY nodes are disabled; all nine stock DTBO variants independently contain UFS PHY/host fragments that enable them and add the RPMh/GDSC rails. The UFS fragments and their UFS fixups are byte-identical across all nine variants. Board-id 0x206a remains a candidate only; no runtime variant selection is proven.
- UFS rails resolve to PM8150 RPMh LDO/SPMI providers and UFS PHY GDSC, not TLMM. The UFS node declares custom dev-reset-assert/deassert pinctrl states on qcom,kona-pinctrl, but pinned ACK 6.18.33 UFS source does not look up these states; host reset uses GCC reset_control and the optional device-reset GPIO is absent in the base node. Thus PINCTRL_MSM is not proven necessary for UFS first-stage probe.
- A new platform compatibility gap is real: HOS TLMM compatible is qcom,kona-pinctrl; pinned ACK SM8250 driver matches only qcom,sm8250-pinctrl. Enabling PINCTRL_MSM/PINCTRL_SM8250 alone will not bind the HOS node. Do not make an unreviewed DTS or driver compatible edit.
- Preserve the overlay's qcom,vccq-parent-supply link from UFS to PM8150A S8, and the shared PM8150 L6 use for both vccq and qcom,vddp-ref-clk. The PMIC regulators' own physical input-parent network remains unresolved.
- Next-build Kconfig recommendation: no symbol from the ROUND20 two-gap list is proven mandatory for the current first-stage UFS mount path. Do not enable DEVTMPFS or DEVTMPFS_MOUNT as a speculative fix. PINCTRL_MSM + PINCTRL_SM8250 may be prudent for other board consumers, but only after the qcom,kona-pinctrl compatible mismatch is deliberately resolved.

New documentation consistency issue found while reviewing the existing main-branch board DTS draft:
- The draft comment says the HOS4.3 base FDT has no /memory node.
- ROUND19 and ROUND20 reports say a /memory node exists with an all-zero reg placeholder.
- ROUND22 must verify this against the existing decompiled DTS and recommend correcting the comment. Do not invent RAM addresses or reserved-memory carveouts.

## 2026-11-25 — ROUND22 dispatched: board-DTS compile readiness and UFS regulator/driver contract audit

Task files:
- firmware-analysis/round22/AGENT_TASK.md
- firmware-analysis/round22/START_PROMPT.md

ROUND22 is a local offline read-only audit to decide whether the existing main-branch DBY-W09 storage-first board DTS draft is structurally ready for a DTB build and whether its UFS regulator properties actually match the exact patched ACK 6.18.33 driver/bindings. It must also reconcile the stale /memory comment and examine whether the missing PM8150 VRM input-parent references are a real software binding requirement or an unresolved electrical/runtime assumption.

The agent may compile a temporary DTB/DTBO from unmodified drafts into the ROUND22 temp directory only, if the existing tools and source include paths permit it. This is a syntax/label test, not a deliverable image and not permission to edit/replace project DTS or package a boot image.

No source/config/DTS/DTBO/firmware edit, no Kconfig run, no kernel rebuild, no AVB/sign/boot packaging, no device/ADB/fastboot/recovery/flash. Use the existing ROUND18/ROUND19 work copies only; do not re-extract firmware or redeploy WSL. Upload one sanitized text report to firmware-audit-v1/firmware-analysis/round22/ and stop.

ROUND18 Image remains the frozen successful build baseline. ROUND21 does not justify adding DEVTMPFS or DEVTMPFS_MOUNT. Do not enable PINCTRL_MSM/PINCTRL_SM8250 until a deliberate compatible strategy is reviewed. Stage A is still not device-boot accepted.


## 2026-11-25 — Supplemental pinned-source finding: HOS vdd-hba-supply is not portable to ACK

A separate direct source pass against the exact ACK commit established an important UFS contract that should be checked in ROUND22:

- HOS4.3's stock UFS overlay adds `vdd-hba-supply` pointing at its `qcom,gdsc` node and also carries `vdd-hba-fixed-regulator`.
- ACK's `ufshcd-pltfrm.c` actively parses optional `vdd-hba-supply`; if present it obtains a normal regulator handle and ACK's `ufshcd/core/ufshcd.c` calls regulator_enable/disable. If absent, ACK treats the HBA supply as already enabled.
- ACK's `drivers/clk/qcom/gdsc.c` registers GDSCs as generic power domains through `of_genpd_add_provider_onecell()`; it does not register a regulator device for the GDSC node. The GDSC driver's own `rsupply` is its upstream input rail, not an output regulator consumer.
- ACK `of_regulator_dev_lookup()` returns `-EPROBE_DEFER` when a supply phandle points to an existing node that has not registered a regulator device. The dummy-regulator fallback is for `-ENODEV` missing-regulator lookup and does not convert this existing-node/no-regulator case into a dummy.
- Consequently, copying the HOS `vdd-hba-supply` phandle to the ACK DTS would be unsafe and could leave UFS probe deferred indefinitely. The existing ACK board draft correctly omits it and retains the SoC DTSI's UFS Host/PHY `power-domains = <&gcc UFS_PHY_GDSC>` declarations. The HOS-only `vdd-hba-fixed-regulator` property is also not consumed by the reviewed ACK UFS path.

Detailed source review: `kernel-baseline/round64/round64-ufs-hba-gdsc-regulator-source-review.md`.

Pinned ACK source anchors:
- `ufshcd-pltfrm.c:L121-L188`, `ufshcd.c:L9499-L9852`
- `gdsc.c:L259-L317,L570-L628`
- `of_regulator.c:L647-L665`, `regulator/core.c:L2210-L2245`

This is source/API evidence, not a runtime result. ROUND22 still performs the full local board-DTS / DTB readiness audit; no source, DTS or build input was changed.


## 2026-11-25 — Supplemental source finding: board DTS must activate the ROUND33 MMCX dual-domain path

The ROUND18 Image includes the ROUND33 UFS driver helper, but the current main-branch `dts/dby-w09-ack18-board.dts.draft` still inherits only one Host domain from the SoC DTSI: GCC UFS_PHY_GDSC. ROUND33 deliberately returns unchanged for a one-domain layout; its MMCX attach and `required_dev[0]` mapping occurs only for exactly two domains.

This matters because:
- ACK UFS platform parsing sets `hba->use_pm_opp = true` when the SoC `operating-points-v2` table is present.
- UFS clock scaling calls `dev_pm_opp_set_opp()`.
- ACK OPP core only emits a `required-opps` performance-state request when the corresponding `required_devs[index]` is non-NULL.
- Without ROUND33's required-device mapping, the UFS OPP table can still scale the UFS clocks, but the associated RPMhPD MMCX vote is skipped.

Therefore the device DTS candidate must integrate ROUND37's dual-domain delta for UFS Host:
`power-domains = <&rpmhpd RPMHPD_MMCX>, <&gcc UFS_PHY_GDSC>;`
with MMCX index 0 and GCC GDSC index 1, plus the required binding includes. The UFS PHY's own GCC GDSC domain remains unchanged. The nine HOS4.3 DTBO variants do not add this Host dual-domain array, so the new ACK board DTS must provide it.

This is not a confirmed hardware failure; it is a source-proven missing performance-domain request in the current DTS draft. The ROUND37 patch was only applied to an isolated exact-file fixture and has not been integrated into an actual ACK DTS path or compiled as a DTB.

Detailed review: `kernel-baseline/round65/round65-ufs-dual-genpd-dts-opp-routing-audit.md`.


## 2026-11-25 — Supplemental source finding: PM8150 missing input-parent properties are schema-optional, but electrical path remains unknown

Exact ACK 6.18.33 source review confirms:
- `qcom,rpmh-regulator.yaml` permits PM8150/PM8150L input supply names in compatible-specific property sets but does not list them as required; top-level required keys are only `compatible` and `qcom,pmic-id`.
- `qcom-rpmh-regulator.c` assigns PMIC descriptor `supply_name` values such as `vdd-s4` and grouped PM8150 LDO parent names into regulator descriptors.
- `regulator/core.c` considers full constraints active when `of_have_populated_dt()` is true. On missing parent lookup `-ENODEV`, the normal regulator get path may use dummy regulator; its comment explicitly assumes the physical parent supply exists and is already enabled.
- A phandle to an existing DT node with no registered regulator is different: `of_regulator.c` returns `-EPROBE_DEFER`, which is not replaced by dummy in that branch.

This establishes why an ACK board DTS may be syntactically/schema-acceptable without the PM8150 input parents, but it does not prove the physical upstream rails exist or are enabled on DBY-W09. Do not fabricate `vph_pwr`, `vdd-s*` links or voltages. Retain the electrical parent map as an independent pre-boot gate.

Detailed note: `kernel-baseline/round66/round66-pm8150-rpmh-parent-supply-dummy-fallback-audit.md`.
