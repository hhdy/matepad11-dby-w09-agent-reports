# AGENT_TASK.md — DBY-W09 / Android 17 / ACK 6.18 内核移植总入口

> **新会话必读：先读取 [PROJECT_HANDOFF.md](./PROJECT_HANDOFF.md)，再执行本文件。**
>
> **阶段顺序不可颠倒：A）先完成并验证 DBY-W09 的 ACK/GKI 6.18.33 内核移植；B）内核阶段验收后，才开始 Android 17 DerpFest 系统移植。** 当前主线仍是阶段 A。Android 12L 只作历史参考，不是当前目标，不要重复进行泛化调研。

> **当前本地 Agent 队列为空。** ROUND12 AVB 报告已上传但在可信工具门槛 BLOCKED；ROUND13 regulator 审计、ROUND14 ARC/S8 属性审计均已上传并完成。不要重跑 ROUND11/13/14，也不要安装 AVB 工具。ROUND13 与历史 `kernel-baseline/round13` DTS 设计属于不同工作流。最新状态见本文件末尾。

## 当前项目目标

- 设备：Huawei MatePad 11 DBY-W09，KONA / SM8250 v2.1 / Snapdragon 865。
- ROM 目标：Android 17 DerpFest。
- 内核目标：ACK tag `android17-6.18.33_r00`（官方 tag target commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`）；Stage A 以该固定源码为基线，不跟踪会漂移的 branch HEAD。
- **阶段 A（当前唯一主线）：先完成 ACK/GKI 6.18.33 内核的 DBY-W09 DTS / 驱动 / UFS / 电源域 / memory handoff / legacy boot-chain 适配，并以设备实际启动 6.18.33 内核作为核心验收；仅编译成功不算完成。**
- **阶段 B：只有阶段 A 通过验收后，才开始 Android 17 DerpFest 的 device/vendor/product、HAL/VINTF、SELinux、fstab/init 和镜像集成。**
- ROUND29 已将 ROUND27 的 UFS→RPMHPD 双 GenPD 方案细化到精确 ACK .33 probe 时序；当前为 SOURCE-REVIEWED DESIGN ONLY，尚未写 patch、修改 DTS、编译或运行。
- ROUND30 确认 ACK .33 的 SM8250 MMCX 描述符没有 MX parent，而 HOS4.3 有 MMCX→MX ARC parent-supply 边；UFS→MMCX 路由不能直接宣称复现该关系。MMCX→MX 角点/资源等价性继续作为单独 gate，不得猜测添加 DTS parent。
- ROUND31 已对照 .33_r00 的 UFS/QMP/CLK/RPMh/GenPD/ICC/SMMU/DM/EROFS Kconfig，修订 storage-first fragment 注释，明确 UFS→PM_DEVFREQ→PM_OPP 和 GCC→QCOM_GDSC→GENPD 的隐藏依赖；Kconfig resolver 尚未运行。
- ROUND32 确认 ACK .33 的 qcom,ufs.yaml 漏列 qcom,sm8250-ufshc；固定源 blob `1dd41f6d5258014d59c8c8005bc54f7994351a52` 与本地测试 fixture 匹配，补丁 blob `efe2d932da34716c631de22d89aba19730cc7f50` 与仓库草案匹配。在该精确文件 fixture 上 `git apply --check`、`git apply`、`git diff --check` 均 PASS。仍未运行 dt_binding_check / dtbs_check，也未做完整 ACK 工作树集成。
- ROUND33 已准备独立 `ufs-qcom.c` driver patch 草案：仅对 SM8250 双域 MMCX→UFS_PHY_GDSC 拓扑生效；验证两个 provider/ID、UFS required-opps 目标 RPMhPD provider，并在通用 UFS init 前 attach 双域、把唯一 required_dev index 0 映射到 MMCX。ROUND38 加入更严格的 table identity 检查：provider 的 operating-points-v2 phandle 必须与 required-opps target 所属 OPP table 节点相同。当前 ACK 源 blob `a80c6998406dbc88c25dbd9977699ba481207efe`、patch blob `565090acbfe9aad00200b3cccbd64a8a45c7c4c3`；两个 hunk 源上下文与声明行数均匹配。仍未 full-tree git apply、checkpatch、编译或设备验证。
- ROUND34 对固定 ACK tag 的 `drivers/pmdomain/core.c`、`drivers/base/power/common.c`、`drivers/opp/core.c` / `of.c`、UFS QCOM 与平台 glue 做了源码级时序/生命周期审查：generic GenPD 确实跳过多 power-domains 设备；attach-list 返回已附着数量，`PD_FLAG_DEV_LINK_ON` 加入 `DL_FLAG_RPM_ACTIVE`；OPP allocator 在 required-dev config 前已解析 required-opps table metadata；UFS clock config 和 OPP table 的调用顺序适合该映射；同一 OPP table 多次 `dev_pm_opp_set_config()` 使用独立 token/flags，后续 clock-only config 不覆盖 earlier `required_dev`；devres 清理时先撤销 OPP 相关资源再拆 GenPD。未发现已核实的 API 顺序或资源生命周期缺陷。报告位于 round34；patch 仍未 `git apply`、checkpatch、编译、schema 验证或实机运行。
- ROUND35 检查现有 `ack18-dby-w09-dts-draft` 的实际 board DTS：`&ufs_mem_hc` override 没有声明 `power-domains`，所以仍继承 ACK SM8250 UFS Host 的单域 GCC `UFS_PHY_GDSC`；ROUND33 helper 因 `num_domains == 1` 会返回并保留 generic path，MMCX 映射在当前 DTS 下不会启动。下一版集成必须把 MMCX 放 index 0、GCC GDSC 放 index 1，并检查 schema / final DTB。报告只写在 main，未改 protected DTS branch。ROUND35 report path: `kernel-baseline/round35/dby-w09-ufs-dual-genpd-dts-integration-gap.md`。未运行 dtc/schema/build/device test。
- ROUND36 在固定 ACK tag 的精确 `qcom,ufs-common.yaml` 中确认 `power-domains.maxItems=1`，已新增 compatible-scoped schema draft（SM8250 最多 2，其他 Qualcomm UFS 最多 1）。目标文件 GitHub blob SHA `962dffcd28b44b3489be5615c75e7270a0c45dc4` 与本地测试 fixture `git hash-object` 完全一致；ROUND36 patch（blob SHA `dad87ef8dfefee6141b8a7949982c007c4a03b4a`）在该精确文件 fixture 上 `git apply --check`、`git apply`、`git diff --check` 均 PASS；PyYAML 解析和独立 JSON Schema Draft 7 条件逻辑测试通过。将 ROUND32/36 两个修改后的 schema 条件组合后，JSON Schema Draft 7 逻辑测试也按预期接受 SM8250 八 clocks/单 reg/一至两个 PD，并拒绝多于两个 PD、错误 clock/reg 布局及非 SM8250 双域。没有完整 ACK worktree、未运行 dt-schema/dtc；ROUND33 未做 full-tree apply。报告 `kernel-baseline/round36/sm8250-ufs-power-domain-schema-limit.md`，补丁 `kernel-baseline/round36/0001-dt-bindings-ufs-allow-sm8250-dual-power-domains.patch.draft`。
- ROUND37 新增板级双域 DTS patch draft：显式 include `qcom,gcc-sm8250.h` / `qcom,rpmhpd.h`，在 `&ufs_mem_hc` 增加 MMCX index 0、GCC `UFS_PHY_GDSC` index 1。当前受保护 board DTS 文件 blob `e86c8707c413a9376b1e332a94e292b86acde3e2` 与完整本地 fixture SHA 完全一致，patch blob `486654c8d0b1b785190253270f5e83f796f07362` 与本地补丁 SHA 完全一致；临时单文件 fixture 上 `git apply --check`、`git apply`、`git diff --check` 均 PASS。只加在 main，GitHub 保护分支未改；未 dtc/schema 验证。报告 `kernel-baseline/round37/dby-w09-ufs-dual-genpd-board-dts-delta.md`。
- ROUND38 进一步审查固定 ACK 的 RPMhPD provider 注册顺序、OPP table indexed fallback、GenPD deferred-probe 和 attach-list partial-failure rollback。ROUND33 当前 patch 增加 provider operating-points-v2 phandle 与 required-opps 目标 containing-table 节点相等性检查，patch blob `565090acbfe9aad00200b3cccbd64a8a45c7c4c3`；两个 hunk 的固定源上下文和数量核验 PASS。完整工作树 apply / checkpatch / compile / device test 仍 NOT_RUN。报告 `kernel-baseline/round38/rpmhpd-provider-registration-and-ufs-opp-table-identity.md`。
- ROUND40 审查 UFS VCCQ-parent/VDDP 的 probe/exit 顺序：ACK generic UFS rail teardown 发生在 Qualcomm variant exit 之后，因此现有供电草案若在 variant exit 直接关闭 VCCQ-parent 有父子 rail 顺序风险；下游 VDDP 与 VCCQ-parent 的行为也不一致。需要将两者策略分开，并确保任何 parent rail cleanup 晚于通用 VCCQ 关闭。没有修改保护分支的供电 patch sketch，也没有合并或运行设备测试。报告 `kernel-baseline/round40/ufs-vccq-parent-vddp-lifetime-and-merge-audit.md`。
- ROUND41 对照固定 ACK `.33_r00` 的 `gki_defconfig` 与 `BUILD.bazel`：generic UFS core/platform、DM、EROFS 已启用，但 Qualcomm UFS glue、QMP UFS PHY、SM8250 GCC、RPMhPD、SM8250 ICC、Command DB/RPMh、QCOM RPMh regulator、ARM SMMU 未在 GKI config 中启用。当前 ROUND31 要求它们 built-in，ROUND10/12 尚未证明 separate ramdisk 能提前加载完整依赖，所以默认选无 `base_kernel` 的 full custom `kernel_build`，按 pinned `yukawa` 示例（srcs=kernel_aarch64_sources + GKI defconfig + full Image/modules/DTB outputs）构建；ROUND31 fragment 应作为唯一 `post_defconfig_fragments` 项：同一 manifest 分支 Kleaf 文档说明在 `make defconfig` 后应用并执行 `olddefconfig`，且要求所有配置存在于 final `.config`；关键驱动依赖若未满足会被检查拦截，不加 `# nocheck`。GKI mixed `base_kernel` 只作条件备选。另 full-image `yukawa` 样例没有 `kmi_symbol_list` / `kernel_abi`，所以不能声称自动继承 GKI KMI enforcement；后续需要设备专属 symbol list + `kernel_abi` 目标，并在真实 module set / ABI baseline 形成后再启用 enforcement。Kconfig、Kleaf query、构建均 NOT_RUN。报告 `kernel-baseline/round41/gki-defconfig-storage-driver-gap-and-full-kernel-build-decision.md`。
- ROUND38 整理 UFS dual-GenPD patch series manifest：明确固定 ACK commit、ROUND32 + ROUND36 schema patch、ROUND37 board DTS delta、ROUND33 driver patch 的依赖顺序及 SHA。ROUND32/36 两个 schema patch 已在同一临时目录、使用两个精确 ACK source blobs 按序 `git apply --check` / apply 成功，组合 `git diff --check`、YAML parse 和 JSON Schema 条件测试通过；ROUND37 board DTS 也在完整精确源文件 fixture 上 `git apply --check` / apply / diff-check PASS；ROUND33 driver 当前仍只有固定源文件 hunk context 验证。报告 `kernel-baseline/round38/ufs-dual-genpd-patch-series-manifest.md`。完整 dt-schema/DTB/Kconfig/build/device verification 仍未完成。
- ROUND39 固定 ACK `.33_r00` 的构建入口和工具链：legacy `build.config.gki.aarch64` 不可用，使用 Kleaf/Bazel；KMI generation 5、Clang `r584948c`、Rust `1.91.1.p3`。ROUND41 已决定默认用 no-`base_kernel` full custom `kernel_build`（pinned `yukawa` pattern），而不是 mixed GKI build；ROUND31 fragment 放 `post_defconfig_fragments`，必须审查最终 `.config`。本轮进一步核对现代 Kleaf DT build separation：用 `rules_devicetree` 的 `dtb()` / `dtbo()` 编译 `.dts/.dtso`，并用 `dtbo_image` 打包 DTBO partition；`dtb_image` 是 boot/vendor_boot 内嵌 DTB，不可混用。完整 workspace / `repo manifest -r`、Bazel query、Kconfig 和 build 仍未运行。报告 `kernel-baseline/round39/ack-6.18.33-kleaf-build-toolchain-baseline.md`。

- 阶段 C 才评估 ColorOS 或其他 ROM。
- DerpFest Android 17 manifest 当前 `kernel-6.18.xml` 指向 June 2026 branch（6.18.21），不改变本项目 6.18.33 目标；Stage B 必须集成本项目已验证的 DBY-W09 内核和匹配模块。
- 官方 Android 17 GKI release 页面列出的 September 2026 分支为 6.18.32；本项目的 6.18.33 ACK-derived build 不得未经 KMI/ABI/认证验证就宣称是官方 certified GKI。
- 不要用 `aosp-mirror/kernel_common` 的 `android17-6.18` GitHub mirror branch 作为 6.18.33 版本证明；该 mirror 当前 Makefile 曾显示 6.18.0-rc6。版本以官方 ACK tag 和锁定 commit 为准。
- 同型号 Android 12L 项目仅供具体问题的历史参考，禁止将其重新作为当前主线或重复调查。
- 不宣称官方 GKI certified：现有设备是 boot header v2 + 独立 ramdisk 分区，未发现 vendor_boot / init_boot。ACK 6.18 源码不自动等于官方 GKI 合规。

## 当前公开研究报告

- [ROUND28：Android 17 ACK 6.18.33 源码基线与 Qualcomm 平台增量策略](./kernel-baseline/round28/android17-6.18.33-source-baseline-and-qcom-platform-delta.md)
- [ROUND33：SM8250 UFS 双 GenPD driver patch 草案](./kernel-baseline/round33/sm8250-ufs-dual-genpd-patch-design.md)
- [ROUND34：ROUND33 UFS 双 GenPD 固定 ACK 源码与生命周期审查](./kernel-baseline/round34/round33-pinned-source-lifecycle-review.md)
- [ROUND35：DBY-W09 UFS 双 GenPD 的 DTS 集成缺口](./kernel-baseline/round35/dby-w09-ufs-dual-genpd-dts-integration-gap.md)
- [ROUND36：SM8250 UFS 双域 binding 数量约束](./kernel-baseline/round36/sm8250-ufs-power-domain-schema-limit.md)
- [ROUND37：DBY-W09 UFS Host 双 GenPD board DTS delta](./kernel-baseline/round37/dby-w09-ufs-dual-genpd-board-dts-delta.md)
- [ROUND38：UFS dual-GenPD patch series manifest](./kernel-baseline/round38/ufs-dual-genpd-patch-series-manifest.md)
- [ROUND39：ACK 6.18.33 Kleaf 构建基线与工具链锁定](./kernel-baseline/round39/ack-6.18.33-kleaf-build-toolchain-baseline.md)
- [ROUND38：RPMhPD provider 注册与 UFS OPP table identity 审查](./kernel-baseline/round38/rpmhpd-provider-registration-and-ufs-opp-table-identity.md)
- [ROUND40：UFS VCCQ-parent / VDDP 供电生命周期审查](./kernel-baseline/round40/ufs-vccq-parent-vddp-lifetime-and-merge-audit.md)
- [ROUND41：GKI defconfig 存储驱动缺口与 full-image Kleaf 构建决策](./kernel-baseline/round41/gki-defconfig-storage-driver-gap-and-full-kernel-build-decision.md)
- [ROUND42：HOS4.3 内存交接与 SM8250 ABL FDT 前置条件](./kernel-baseline/round42/hos43-memory-handoff-sm8250-abl-fdt-prerequisite.md)
- [ROUND43：ACK 6.18.33 classic FDT 与 EFI-stub 内存交接区分](./kernel-baseline/round43/ack-6.18.33-fdt-memory-scan-classic-vs-efi-handoff.md)
- [ROUND44：ROUND33 required-opps 首项检查与 ACK OPP parser 一致性](./kernel-baseline/round44/round33-required-opps-first-entry-parser-alignment.md)
- [ROUND32：SM8250 UFS binding 覆盖与 schema 补丁草案](./kernel-baseline/round32/sm8250-ufs-binding-coverage-and-schema-draft.md)
- [ROUND31：ACK 6.18.33 存储优先 Kconfig 依赖闭环](./kernel-baseline/round31/ack-6.18.33-storage-first-kconfig-dependency-closure.md)
- [ROUND30：ACK SM8250 MMCX→MX parent/corner 等价性门槛](./kernel-baseline/round30/sm8250-rpmhpd-mmcx-mx-parent-equivalence-gate.md)
- [ROUND29：ACK .33 UFS 双 GenPD / required-OPP probe 接入设计](./kernel-baseline/round29/ack-qcom-ufs-dual-genpd-required-opp-probe-integration.md)
- [ROUND27：ACK SM8250 UFS required-opps 到 RPMHPD 的 GenPD 路径缺口](./kernel-baseline/round27/ack-sm8250-ufs-rpmhpd-required-opp-routing-gap.md)
- [ROUND24：HOS4.3 ARC 逻辑 corner 与 DT 约束语义](./kernel-baseline/round24/hos43-arc-logical-corner-dt-semantics.md)
- [ROUND23：ACK ARC provider 的 RSC 设备层级与请求上下文设计](./kernel-baseline/round23/ack-arc-provider-rsc-device-hierarchy.md)
- [ROUND26：HOS4.3 PM8150 regulator mode/DRMS 属性证据边界](./kernel-baseline/round26/hos43-pm8150-regulator-mode-property-evidence.md)
- [ROUND25：ACK UFS core 电源顺序与 VCCQ/L6 DRMS 聚合](./kernel-baseline/round25/ack-ufs-core-vccq-l6-drms-order-review.md)
- [ROUND24：ACK UFS VDDP REF_CLK 与 L6 DRMS 负载聚合](./kernel-baseline/round24/ack-ufs-vddp-refclk-and-l6-drms-review.md)
- [ROUND23：UFS VCCQ parent rail 与 ACK 驱动适配](./kernel-baseline/round23/ufs-vccq-parent-rail-and-ack-driver-adaptation.md)
- [ROUND23：ACK ARC provider 设备结构与请求聚合设计](./kernel-baseline/round23/ack-arc-provider-device-and-aggregation-design.md)
- [ROUND22：ACK RPMh ARC 与 proxy-consumer 移植可行性](./kernel-baseline/round22/ack-rpmh-arc-and-proxy-consumer-port-feasibility.md)
- [ROUND21：ACK PM8150 VRM parent-supply 与 dummy regulator 风险审查](./kernel-baseline/round21/ack-pm8150-vrm-parent-supply-gap.md)
- [ROUND20：Android first-stage 模块加载、动态分区与 EROFS 配置](./kernel-baseline/round20/android17-first-stage-module-dm-erofs-review.md)
- [ROUND19：HOS4.3 内存节点与 reserved-memory 交接审查](./kernel-baseline/round19/hos43-memory-reserved-memory-handoff-review.md)
- [ROUND18：DBY-W09 legacy boot / ramdisk / DTBO 打包路径审查](./kernel-baseline/round18/dby-w09-legacy-boot-avb-packaging-review.md)
- [ROUND17：ACK 6.18 GENI UART / console 映射审查](./kernel-baseline/round17/ack18-geni-uart-console-mapping-review.md)
- [ROUND16：HOS4.3 RPMh ARC parent graph 与 ACK DTS 映射](./kernel-baseline/round16/hos43-rpmh-arc-parent-graph-to-ack-dts.md)
- [ROUND15：UFS 启动依赖与 rootparam 修正](./kernel-baseline/round15/ack18-storage-bringup-dependency-and-rootparam-correction.md)
- [ROUND14：ACK 6.18 UFS 早期启动 Kconfig 依赖审查](./kernel-baseline/round14/ack18-dby-w09-bootcritical-kconfig-review.md)
- [ROUND13：第一版 ACK 板级 DTS / 最小 rootparam DTBO 设计](./kernel-baseline/round13/ack18-dby-w09-initial-dts-and-dtbo-design.md)
- [ACK 6.18 DTS / Kconfig 草案分支](https://github.com/hhdy/matepad11-dby-w09-agent-reports/tree/ack18-dby-w09-dts-draft)
- [ROUND12：ROUND10 boot-chain 证据更新与 ACK DTS 基础](./kernel-baseline/round12/round10-boot-chain-update-and-ack18-dts-foundation.md)
- [ROUND11 之前的内核优先移植方案](./kernel-baseline/round11/android17-6.18-dby-w09-kernel-port-plan.md)

## 当前重点事实

- UFS HOS4.3 supply map：ROUND9 已完成 Host/PHY rails 映射：VCC/L17、VCCQ/L6、VCCQ2/S4、VDDA-PHY/L5、VDDA-PLL/L9、UFS device REF_CLK pad VDDP/L6（100µA）、HBA/GCC UFS_PHY_GDSC；另有 UFS Host VCCQ parent rail PM8150A S8（1.2–1.4V，210mA）。ROUND23/24 已将 S8 映射到 ACK PM8150L SMPS8，并将 VDDP 与 VCCQ-parent 两项 vendor consumer 属性统一放在 `&ufs_mem_hc`；QMP PHY 只保留 VDDA-PHY/VDDA-PLL。L6 uses pmic5_nldo DRMS, HPM threshold 30mA aggregated: UFS VCCQ max800mA plus VDDP100µA votes combine; S8 uses pmic5_hfsmps510 without DRMS set_load, so its 210mA request may no-op. Patch sketch covers both but remains unapplied/uncompiled; power behavior unverified.
- ROUND7 确认 PM8150 S4/L5/L6/L9/L17 的 regulator 节点和输出电压；ROUND11 对完整 HOS4.3 base FDT 复核后发现四条 parent-supply 全属于 ARC level groups、六条 proxy-supply 属于 ARC proxy 机制，并全 FDT 确认 vdd-s1..s10/vin/vph-pwr 属性零命中。物理 PMIC 输入 supply 仍未确定。
- 同型号公开 Linux 7.0 DTS 使用固定 3.7 V vph_pwr 和 PM8150 vdd-s1..s10-supply links；其头部说明该部分参考 HOS4.2，因此不能直接当作本设备 HOS4.3 已证实事实。当前 ACK DTS 草案已暂时移除这些未确认输入链接。
- ROUND7 的本机脱敏 DTBO inventory 显示 9 个 stock DTBO entry 都有相同的通用哨兵 huawei,modem_id = <0xffffffff 0>；当前最小 rootparam overlay 已保留该字段。它不是设备唯一编号，但新 DTBO 的 ABL 接受性仍未知。
- ACK SM8250 UFS 节点依赖 GCC UFS_PHY_GDSC、RPMh XO clock、apps_smmu 及 ufs-ddr/cpu-ufs interconnect；其 OPP 表引用 RPMHPD required-opps。ROUND27 发现 Host 当前附着 GCC UFS_PHY_GDSC，而 GCC/GDSC 没有到 RPMHPD 的已证实父级/性能状态回调，因此 required-opps 不能视为已生效的 MMCX vote。ACK 提供 devm_pm_domain_attach_list() 多域接口；可让 Host 同时附着 RPMHPD MMCX 与 UFS_PHY_GDSC，并在 OPP table 初始化前将唯一 required-opps index 0 手动映射到 RPMHPD virtual device。不能对两个 domain 直接启用 PD_FLAG_REQUIRED_OPP，因为第二个 required_dev_index 会超出当前单元素 required-opps 数组。此 UFS patch 仍未实现。Kconfig 草案保留 QCOM_RPMHPD。上游 ACK Host driver 原本不消费 `qcom,vddp-ref-clk` / `qcom,vccq-parent`，ROUND23/24 patch sketch 补充两者的可选 regulator get/load/enable/cleanup。L6 具 DRMS 聚合负载；S8 没有 DRMS set_load，210mA vote may no-op。HOS4.3 ARC parent/proxy 不能照搬到 ACK VRM group，且完整 MMCX/CX/MX corner equivalence 尚未建立。
- UFS 的直接 UFS_PHY_GDSC 由 GCC 提供；ACK ufs_opp_table 虽声明 required-opps 指向 RPMHPD OPP，但 ROUND27 确认性能级请求通过当前 GenPD 路由，原始 GCC GDSC 没有已证实的 RPMHPD 父级。QCOM_RPMHPD 暂时保留为待通过 UFS dual-GenPD patch 接通的 provider，不应写成已生效的 UFS vote。
- UART：ACK 将 uart2(qcom,geni-debug-uart) 作为 ttyMSM/earlycon console 候选，将 uart6(qcom,geni-uart) 作为 ttyHS 普通串口；HOS4.3 androidboot.console 与物理串口映射尚未证实，两个节点均暂缓启用。见 ROUND17。
- Legacy boot：HOS4.3 本机文件大小与同型号公开项目的 boot 96 MiB、ramdisk 2 MiB、DTBO 24 MiB 一致；同型号公开流程保留 boot header v2 + 嵌入 ramdisk，另更新 ramdisk 分区及 /rootparam DTBO。ROUND12 已上传但 AVB footer 与 vbmeta descriptor 检查因无可信已安装工具而 BLOCKED；覆盖关系仍 UNKNOWN。
- Android 首阶段：支持在逻辑分区挂载前从 initramfs /lib/modules 按内核版本/page-size 加载模块；DBY-W09 legacy ABL 是否按 AOSP 要求暴露此目录仍 UNKNOWN。当前 UFS/QMP 保守内建。ROUND20 已确认 BLK_DEV_DM=y 和 EROFS_FS=y；无 DM_LINEAR 独立 Kconfig 项。DM_VERITY/FEC 仍等待 AVB descriptors 与 ramdisk fstab；ROUND12 因无可信 AVB 工具而 BLOCKED，不能据此假定 descriptors。
- 内存 / 保留区：ROUND7 的 HOS4.3 base FDT 无 /memory 节点，但含 34 个 /reserved-memory 子节点；同型号 HOS4.2 公共 DTS 也没有普通 /memory 节点且只显式保留 4 个节点。ROUND42 对照公开 SM8250 FreeABL LinuxLoader 发现，标准路径会查找既有 /memory，缺失则 EFI_NOT_FOUND；随后从 EFI_RAMPARTITION_PROTOCOL 更新其 reg，不自动创建节点。该参考不是 Huawei ABL，因此实际 HOS4.3 最终 post-ABL FDT 仍 UNKNOWN；不要再假定 ABL 一定注入 memory node。其可选 carveout-removal path 读取既有 /reserved-memory/no-map 并扣除 RAM banks，不会重建 34 个子节点。见 ROUND19/ROUND42；最终 memory/reserved-memory 是实际 DTB 编译和启动前硬性 gate。 在参考实现中该错误会沿 LoadAddrAndDTUpdate 传播并让非 RUMI 平台停止正常 boot；FdtPathOffset 可匹配唯一 memory@unit-address，不是字面名强制。 ROUND43 对照 ACK 自身：classic path 只从带 `device_type=memory` 的 FDT root child 读 RAM；真正 EFI-stub entry + 完整 `/chosen/linux,uefi-*` 元数据可由 UEFI map 重建 memblock，是一条独立例外。仅有 UEFI ABL 或 Qualcomm EFI_KERNEL_PROTOCOL 不足以证明使用 Linux EFI stub。 ROUND44 对照固定 OPP core 发现 `_opp_table_alloc_required_tables()` 明确只检查第一个可用 OPP entry；ROUND33 同样使用首项来检查唯一 required-opps provider 与其 OPP table identity，符合 ACK 的 table-level 解析逻辑，不需要增加逐项扫描。该结论仍是源码审查，未 full-tree apply/build。
- Panel ACTIVE_PROFILE=UNKNOWN；ROUND10 ramdisk BLOCKED；EROFS 内容 BLOCKED；system/cust/hw_product filesystem 类型和完整 fstab 未明。

## ROUND11 — 已完成

任务书：[firmware-analysis/round11/AGENT_TASK.md](./firmware-analysis/round11/AGENT_TASK.md)

脱敏结果：[round11_pmic_parent_supply_findings.txt](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round11/round11_pmic_parent_supply_findings.txt)

结论摘要：
- 4 条 `*-parent-supply` 属于 HOS4.3 legacy RPMh ARC level groups，不是 PM8150 VRM 物理输入。
- 6 条 `proxy-supply` 属于 ARC proxy 机制，不是外部输入 supply。
- 全 FDT 扫描未发现 `vdd-s1..s10-supply`、`vin-supply`、`vph-pwr-supply`。
- 所有 11 条 phandle 均已解析；BLOCKED=NONE，UNKNOWN=NONE。
- ACK 不支持把 vendor `qcom,rpmh-arc-regulator` 节点直接搬入上游 VRM regulator；性能级使用 ACK SM8250 rpmhpd/OPP 模型。完整 MMCX/CX/MX corner 等价性仍未建立。

**历史状态说明：** ROUND12 AVB 报告已在 `firmware-audit-v1` 上传并 BLOCKED；ROUND13 regulator mode/DRMS 报告也已上传完成。当前本地 Agent 队列为空。

## 仓库与安全边界

- 仓库：hhdy/matepad11-dby-w09-agent-reports
- 本地 Agent 分支：firmware-audit-v1；GPT 公开研究放 main。
- PR #1 必须保持 Draft，未经用户明确授权不得合并。
- 不要求重新上传固件；不重复 ROUND1–ROUND10。
- 不刷机、不解锁、不连接设备、不 root、不写分区、不加载模块、不挂载可写文件系统、不编译。
- 未实际执行的动作必须标记 NOT_RUN / BLOCKED / UNKNOWN。


## 最新公开源码核验补充：ROUND44（2026-11-24）

GPT 已完成 ROUND44：在固定 ACK android17-6.18.33_r00 commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a 上复核 UFS 双 GenPD probe / required-OPP 映射顺序。核心 API 顺序符合设计，固定 SM8250 UFS OPP 表的两个条目均为单 required-opps；但 ROUND33 补丁在完整工作树 apply 前必须补上“遍历所有可用 OPP 条目”的验证，并明确该双域规则是 DBY-W09 专用还是对所有 SM8250 UFS 生效。MMCX-to-MX、内存 handoff、AVB 等独立 gate 仍未关闭。报告详见：

- kernel-baseline/round44/ack-ufs-dual-genpd-probe-contract-review.md

该轮没有修改 firmware-audit-v1、ack18-dby-w09-dts-draft 或 PR #1，也没有运行完整内核构建或设备测试。当前队列状态以后续 ROUND12/13 完成记录为准。


## 最新公开源码/补丁进度：ROUND45（2026-11-24）

ROUND45 已更新 ROUND33 UFS 双 GenPD 驱动补丁：
- 遍历 UFS OPP 表的所有可用子节点，不再只检查第一个。
- 每个条目必须恰好有一个 required-opps；目标节点必须可用，属于 operating-points-v2 表；表的父节点必须是 qcom,sm8250-rpmhpd；provider 唯一的 operating-points-v2 phandle 必须指向完全相同的表节点。
- 补齐 OF 节点引用的错误路径/成功路径释放，并拒绝空 OPP 表。
- 明确 fail-closed 双域策略：单域沿用 generic path；双域只支持 MMCX index 0 + GCC UFS_PHY_GDSC index 1；未知双域布局失败，不得静默继续。

更新补丁：
- kernel-baseline/round33/0001-scsi-ufs-qcom-sm8250-dual-genpd-required-opp.patch.draft
- 当前 blob SHA：2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5
- 新增 205 行；两个 hunk 的数量和固定 ACK 源码旧侧上下文均复核 PASS（12/18；15/214）。

ROUND45 仅完成补丁文本/hunk/source-context 静态核验。完整 ACK 工作树 git apply、checkpatch、编译、dt-schema、dtc/dtbs_check、Kconfig、Kleaf 和设备验证均 NOT_RUN。完整报告：kernel-baseline/round45/ack-ufs-dual-genpd-all-opp-validation.md。

不得改动 firmware-audit-v1、ack18-dby-w09-dts-draft 或 PR #1。Stage A 仍是唯一主线，Stage A 通过设备启动与存储验收前不得开始完整 DerpFest Stage B。


ROUND45 补充 Kconfig 源码核验：固定 ACK 源码中 UFS core → PM_DEVFREQ → PM_OPP；SM8250 GCC → QCOM_GDSC → PM_GENERIC_DOMAINS（PM=y 时）；PM_GENERIC_DOMAINS_OF 随 OF 自动启用；QCOM_RPMHPD 依赖 QCOM_RPMH + QCOM_COMMAND_DB，均已由 storage-first fragment 请求。未发现新增 helper 还需要额外直接配置符号；最终 Kleaf/Kconfig resolver 与 .config 核验仍 NOT_RUN。


## 最新公开源码核验：ROUND46（2026-11-24）

ROUND46 已对固定 ACK `android17-6.18.33_r00` commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` 的 `drivers/opp/of.c` / `drivers/opp/core.c` 做精确源码契约复核：

- OPP framework 的 `_opp_table_alloc_required_tables()` 以第一个可用 OPP entry 确定整张表的 `required_opp_count`；这是 table-level 槽位发现。
- 后续 `_of_opp_alloc_required_opps()` 会对每个具体 OPP entry，按该 count 解析对应的 `required-opps[i]`。因此不能把“第一个 entry 决定槽位数”误解为“只需要校验第一个 entry”。
- ROUND45 的 ROUND33 驱动补丁预检全部可用 UFS OPP entry，每项强制恰好一个有效 MMCX required-opps target，与固定 ACK 的单槽位表结构一致，并能在通用 OPP 建表前提前发现后续 entry 的缺失/错误引用。
- `_opp_set_required_dev()` 对 `required_dev_index` 做 required_opp_count 边界检查；index 0 与单 required-opps 槽位匹配。GCC UFS_PHY_GDSC 保持作为第二个已附着电源域，不映射到不存在的第二个 required-opps 槽位。
- `devm_pm_opp_set_config()` 成功时返回 0；ROUND33 的错误判断方式正确。

精确源 blob：`drivers/opp/of.c` = `505d79821584e28f454dae673cf85078762b2ec7`；`drivers/opp/core.c` = `157c84b689feba9ae2c446083e42de63e94a38a6`。

**结论：** ROUND45 的全可用 OPP 条目预检与 ACK parser 的 table-discovery/per-entry-link 两阶段语义一致；本轮无需再改 ROUND33 补丁。ROUND46 报告：`kernel-baseline/round46/ack-opp-required-opps-parser-contract-review.md`。

以上仅为固定源码静态审查；full-tree git apply、checkpatch、编译、最终 Kconfig/.config、dt-schema、DTB、Kleaf、运行时 MMCX vote、UFS 启动和设备实机启动均仍 NOT_RUN。ROUND12 已上传但 AVB 检查 BLOCKED；ROUND13 已上传完成。ROUND30 MMCX-to-MX、ROUND42/43 memory handoff、ROUND40 VCCQ-parent/VDDP teardown 仍是独立门槛。

Stage A 仍是唯一当前主线：先让 DBY-W09 实际启动 ACK 6.18.33 并通过存储/基础硬件验收；未通过前不开始完整 Android 17 DerpFest Stage B。


## 最新公开源码研究：ROUND47（2026-11-24）

ROUND47 已完成 ACK .33_r00 PM8150 regulator mode / DRMS 能力审查。固定源码结果：

- `regulator-initial-mode`：只在 regulator 注册初始化阶段设置一次，不代表动态 DRMS。
- `regulator-allowed-modes`：映射到 valid_modes_mask，并开放 regulator mode change。
- `regulator-allow-set-load`：只开放 REGULATOR_CHANGE_DRMS 权限；不会为硬件驱动凭空增加 get_optimum_mode 或 set_load callback。ACK binding 要求它与 allowed-modes 配套。
- PMIC5 LDO：HPM→REGULATOR_MODE_NORMAL，LPM→REGULATOR_MODE_IDLE。
- PMIC5 SMPS：HPM→FAST/PWM，AUTO→NORMAL，LPM→IDLE/PFM，映射不同，不能把 LDO 模式枚举套到 SMPS。
- DBY-W09 UFS PM8150 L5/L6/L9 为 `pmic5_nldo`，有 `get_optimum_mode + set_mode` DRMS 路径，HPM threshold=30 mA。
- PM8150 L17 为 `pmic5_pldo`，有 DRMS 路径，HPM threshold=10 mA。
- PM8150 S4 与 PM8150L S8 为 `pmic5_hfsmps510`，有手动 set_mode/get_mode，但没有 get_optimum_mode 或 set_load。即使打开 allow-set-load，regulator core 也会以 success no-op 返回，不会自动切换模式。
- DRMS 聚合 enabled consumers 的 load votes + regulator-system-load；LDO 根据阈值选 HPM/LPM，再由 allowed-modes 约束。allowed-modes 不能排除高负载时可能需要的 HPM，否则可能在 mode constrain 阶段失败。

当前 board DTS draft 对 PM8150 S4/L5/L6/L9/L17 设置了 HPM initial mode，但没有 allow-set-load / allowed-modes；PM8150L S8 目前没有 mode/DRMS 属性。这是 draft state，不代表 HOS4.3 原始值。

同设备公开 Linux DTS 属 HOS4.2 交叉参考：PM8150 UFS rails 写 HPM initial mode；LPM/HPM + allow-set-load 是在 PM8150L L6/L9 microSD rail 上出现。不得据此假定 HOS4.3 相同，也不得机械复制到 PM8150 UFS L6 或 S8。

**ROUND13 local evidence 已完成：** upstream `regulator-*` mode/DRMS/suspend 属性名在所检查 HOS4.3 scope 内均为 `NOT_FOUND_IN_INSPECTED_SCOPE`；本机使用 vendor `qcom,supported-modes` / `qcom,mode-threshold-currents` / `qcom,init-mode`。S4 无 mode metadata；L5/L6/L9/L17 为 PMIC5 LDO；S8 为 PMIC5 HFSMPS。详细值、overlay 边界及 ACK 转换见 `firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt` 与 `kernel-baseline/round48/ack-hos43-pmic5-mode-enum-translation-and-dts-decision.md`。

ROUND47 是固定 ACK 源码能力审查；ROUND13 现在已补齐 HOS4.3 静态字段结果，但没有任何运行时 mode 读数。当前本地 Agent 队列为空；Stage A 6.18.33 内核仍是唯一主线，实际启动和存储验收前不开始 DerpFest Stage B.


## 历史本地任务状态（2026-11-24）— ROUND12 BLOCKED；ROUND13 已完成

ROUND12 已上传到 `firmware-audit-v1`：
`firmware-analysis/round12/round12_avb_metadata_findings.txt`

结果：**BLOCKED at tool gate**。本机没有已安装可信 avbtool / 已审查 AVB helper；已审查脚本不解析 AVB footer 或 vbmeta descriptors。未执行 AVB 解析，没有安装/下载工具，没有使用 WSL 或更改安全策略。因此 footer、original-image-size、descriptor coverage 和链式 vbmeta 关系继续 BLOCKED / UNKNOWN。不要从 AVB0 magic 或文件大小推断。

ROUND13 **已完成并上传** HOS4.3 PM8150 UFS regulator mode / DRMS metadata audit；当前无活动本地任务。
- 任务书：`firmware-analysis/round13/AGENT_TASK.md`（本文件所在仓库 main）。
- 只读扫描已有 ROUND3 base boot-FDT work copy 和 ROUND7/8 stock DTBO work copies；重用 ROUND3 已审查 parser 与 ROUND9 resolution pattern。
- 目标：PM8150 S4/L5/L6/L9/L17 与 PM8150L S8 的 initial-mode、allowed-modes、allow-set-load、system-load 和 suspend-state mode/on-off 属性，保留节点路径及 fragment-to-target 关联。
- 不安装工具、不下载、不写 parser、不重提取固件、不连接设备、不写分区。
- 只将脱敏文本结果上传到 `firmware-audit-v1` 的 `firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt`；上传后停止。
- 该 `firmware-analysis/round13` 与历史 `kernel-baseline/round13` ACK DTS 设计是不同命名空间，不应混淆。

ROUND47 提供 ACK 侧 regulator DRMS 解释；ROUND13 已补充实际 HOS4.3 本机字段，ROUND48 已完成公开 SM8250 vendor enum 交叉核验并更新 main DTS draft。不要把 HOS4.2 公共 DTS 当作 HOS4.3 证据。

---

## Historical queue snapshot — ROUND12/13 complete, ROUND14 dispatched at that time

This is an archived snapshot from before the ROUND14 upload. It is retained only to explain the historical task sequence and is not a current instruction.

- ROUND12 was uploaded but BLOCKED at the trusted AVB tool gate.
- ROUND13 was uploaded and COMPLETE.
- ROUND14 was then dispatched as a single local read-only extraction task and is now COMPLETE, as documented in the current status block below.
- The Stage A ACK 6.18.33 / Stage B DerpFest order has not changed.
 
## Historical task dispatch record — ROUND14 (superseded)

ROUND14 was once the sole active Local Agent task. It has since been completed, uploaded to `firmware-audit-v1`, and superseded by the current empty-queue status below. The detailed task book and original instructions are retained for audit history only; **do not execute or repeat them**.


## Latest queue/status correction — ROUND14 complete; ROUND51 reviewed (2026-11-24)

- ROUND14 is uploaded on firmware-audit-v1 at firmware-analysis/round14/round14_arc_mmcx_mx_power_properties.txt (Git blob 2a1cf742ec45b1b17c98c006da241fb7737f6fcd). The Local Agent followed the stop-after-upload rule. Do not repeat FDT parsing or ROUND11/13 scans.
- ROUND51 public-source report: kernel-baseline/round51/round14-arc-value-semantics-proxy-vote-and-round11-edge-reconciliation.md.
- There are now at least five proven HOS4.3 base-FDT parent-supply edges; ROUND11's count of four was incomplete, and the full total remains unverified.
- 0xffffffff min-dropout is not a no-dropout sentinel in the KONA ARC code path; it is read into signed int and added to the ARC logical level path as -1 on the ARM64 target. Do not normalize it to zero.
- HOS MMCX ALL has a temporary proxy request at TURBO..MAX; it is not permanent system-load/always-on. ACK currently lacks an equivalent helper.
- S8 has no static enable/boot-on/always-on property in inspected scope. qcom,set=3 and init-mode=RET are not enable. ACK S8 set_load is no-op; do not force enable. Board DTS initial mode is corrected to RET and runtime enable remains UNKNOWN.
- ROUND49 VDDP/L6 enable + deferred cleanup remains; S8 load-only/get/enable/disable is omitted from the initial ACK UFS patch.
- No ROUND15 local task is active. Do not prepare another Local Agent task unless subsequent implementation demonstrably needs a distinct fact that cannot be obtained from fixed/public source.
- Main-only draft/report updates are recorded in PROJECT_HANDOFF.md and dts/README.md. Protected ack18-dby-w09-dts-draft branch remains untouched; PR #1 remains Draft.
- All full-tree apply, checkpatch, dt-schema, dtc/dtbs_check, final Kconfig/.config, Kleaf build, boot packaging, device boot, UFS/storage and basic hardware validation remain NOT_RUN. Stage A ACK 6.18.33 is the sole active milestone; Stage B DerpFest waits for successful Stage A device acceptance.


## Latest public-source design — ROUND52 (2026-11-24)

- ROUND52 report: kernel-baseline/round52/round52-storage-first-ufs-vddp-integration-and-binding-closure.md.
- New binding draft: kernel-baseline/round52/0001-dt-bindings-ufs-vddp-vccq-parent-supplies.patch.draft.
- New UFS driver draft: kernel-baseline/round52/0002-ufs-qcom-sm8250-vddp-refclk-managed-lifecycle.patch.draft.
- Intended series order after ROUND32/36/37/33 is documented in ROUND52. VDDP/L6 gets a managed load+enable reference; cleanup runs after generic UFS VCCQ shutdown and before regulator_put. S8 has no get/load/enable/disable or voltage request in the initial ACK driver patch.
- ROUND52's patch hunk counts were statically checked, but no complete source-tree apply/checkpatch/schema/build was run.
- No Local Agent task is active or needed for ROUND52. The next complete integration/build gate requires a full ACK worktree and an authorized build environment; do not ask the read-only Agent to compile or modify source.


## ROUND52 final context-validation update (2026-11-24)

- The full intended patch order was strictly simulated in memory against the exact ACK .33_r00 pristine files and the protected board DTS file fetched read-only. All 15 hunks matched exact old context and declared old/new line positions after cumulative deltas, without fuzz or nearest-context fallback: ROUND32 3/3, ROUND36 2/2, ROUND52 binding 2/2, ROUND37 2/2, ROUND33 2/2, ROUND52 driver header 1/1 and driver 3/3.
- This is source-context/order simulation only, not a real git worktree apply, dt-schema, build or runtime test.
- Updated full manifest: kernel-baseline/round38/ufs-dual-genpd-patch-series-manifest.md. Latest ROUND52 report: kernel-baseline/round52/round52-storage-first-ufs-vddp-integration-and-binding-closure.md.
- No Local Agent is needed or active. The next blocked boundary is a full authorized ACK source/build worktree, not another local firmware scan.


ROUND52 final identities: binding patch c0ac84067a900022a077c748b7abb10345f1295f; VDDP driver patch fb34fbc9701bc7e7b56bb9078ee98c0cdd8caf78; report acd35ab048a437e03957cf6a7f5ffd2c82885378; series manifest 3b6a07c2c29b07f3e95af6d342f84117ecb993c9. The HBA/host pointer lifetime check is recorded in ROUND52: devres LIFO releases the later VDDP cleanup action before the earlier variant-host and HBA release actions.


## ROUND15 taskbook index — read-only Stage-A build environment inventory (2026-11-24)

- Taskbook: `firmware-analysis/round15/AGENT_TASK.md` on `main`.
- Purpose: inventory only existing local ACK 6.18.33 source checkouts, already-installed Linux-capable toolchains, and disk capacity.
- Status: **READY FOR LOCAL AGENT — NOT DISPATCHED; no report uploaded yet.**
- Allowed result: one sanitized text report at `firmware-analysis/round15/round15_stagea_build_environment_inventory.txt` on `firmware-audit-v1`.
- Do not install/download/sync/build, start WSL/VM/container, or touch the device. No repeat of ROUND12/13/14; do not overlap the GitHub-connected second AI's ROUND54.


## ROUND55 — Stage-A execution sequence reference (2026-11-24)

Primary AI has consolidated the existing evidence in `kernel-baseline/round55/stage-a-execution-gate-matrix.md`. This is a planning/reference report, not a new local Agent task.

Key split:
- ROUND15 checks existing local source/build-environment availability only.
- Source patch application, schema checks, Kconfig resolution and kernel compilation can proceed in a disposable ACK worktree once an authorized source/build environment exists.
- AVB, ramdisk, trusted final memory handoff and packaging remain separate gates before creating/using a board boot candidate.
- Do not let unresolved boot packaging block source-level validation, but do not claim first-boot readiness until the memory/boot-chain gates are closed.

Current parallel work:
- Second AI ROUND54: independent UFS patch review, dedicated branch `ai-parallel/round54-ufs-review`; template exists, review not yet completed.
- Local ROUND15: read-only source/build environment inventory taskbook exists; not yet dispatched/reported.


## Current local Agent queue — ROUND16 environment deployment (2026-11-24)

ROUND15 is complete and uploaded. Its result is `NO_EXISTING_BUILD_WORKSPACE_FOUND`; see the sanitized report at `firmware-analysis/round15/round15_stagea_build_environment_inventory.txt` on `firmware-audit-v1`.

The user has explicitly authorized the local Agent to deploy the build environment. The current task is:

- `firmware-analysis/round16/AGENT_TASK.md`
- Goal: deploy WSL2 Ubuntu 24.04 on D:, install minimal official Ubuntu host packages, synchronize only the official kernel Repo manifest `common-android17-6.18`, pin `common` to ACK commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`, record manifest/toolchain versions.
- Status: **READY FOR LOCAL AGENT — NOT YET REPORTED COMPLETE.**
- This is the first task allowed to install software and synchronize source, limited strictly to the scope in ROUND16. No security-policy bypass, no Defender/security disabling, no forced reboot, no BIOS modification, no device access, no flashing.
- It must stop before patch application or kernel compilation. Upload only its sanitized text report to `firmware-audit-v1`, then stop.

ROUND54 remains the separate second-AI source review on `ai-parallel/round54-ufs-review`; do not overlap the tasks.

ROUND16 copy/paste start prompt: `firmware-analysis/round16/START_PROMPT.md`.


## ROUND54 completed; ROUND57 follow-up added (2026-11-24)

The second GitHub-connected AI completed its independent UFS review on `ai-parallel/round54-ufs-review`. Report verdict: `PASS WITH NON-BLOCKING FINDINGS`; one P3 finding only. No proven P1/P2 driver lifecycle defect was found at source-review level.

R54-001: ROUND32 constrains SM8250 `clocks` to 8 but does not constrain `clock-names` count, while the shared schema allows 7..9. Primary AI reviewed and accepted the correction as a separate ROUND57 follow-up:
- patch: `kernel-baseline/round57/0001-dt-bindings-ufs-sm8250-clock-names-exact-count.patch.draft`
- report: `kernel-baseline/round57/sm8250-ufs-clock-names-exact-count-follow-up.md`
- updated series order: ROUND32 → ROUND57 → ROUND36 → ROUND52-0001 → ROUND37 → ROUND33 → ROUND52-0002.
No full-tree apply or dt_binding_check/dtbs_check was run; this is still a patch draft.

## Current active local Agent task — ROUND16 deployment

ROUND15 is complete. The user authorized environment deployment. The current local Agent task is now ROUND16:
- `firmware-analysis/round16/AGENT_TASK.md`
- Copy/paste execution prompt: `firmware-analysis/round16/START_PROMPT.md`

Execute WSL2 + Ubuntu 24.04 deployment, minimal official host packages, official kernel Repo manifest sync, and pin ACK common to `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`. Stop before patch application and kernel compilation. Never bypass a Windows security block, disable security software, force a reboot, change BIOS/UEFI, or operate the tablet. Upload only the sanitized report to `firmware-audit-v1`, then stop.

Current status: **READY FOR LOCAL AGENT — deployment result not yet uploaded.** Do not claim environment readiness until the report verifies it.


## 最新派发指针校正 — ROUND16 BLOCKED；ROUND17 + ROUND58 并行（2026-11-24）

本节覆盖此前“ROUND16 READY FOR LOCAL AGENT / deployment result not yet uploaded”的旧状态。

**ROUND16 已上传终态报告：BLOCKED_BY_HOST_SECURITY_POLICY。** 不是部署成功，也不是源同步部分成功。未安装 distro、未 apt、未 repo sync、未 pin、未编译。

已确认 Store WSL 2.7.3.0 与注册在 C: 的既有 WSL2 distro Ubuntu；VirtualMachinePlatform 已 Enabled。ROUND15 的“无 WSL”结论应修正为“ROUND15 未能查询 WSL”；ROUND16 才确认已安装。wsl.exe 被 Command Security Program Blacklist 阻止，Agent 非提升上下文。

### 当前本地 Agent 任务：ROUND17（等待用户人工前置动作）

- Task: `firmware-analysis/round17/AGENT_TASK.md`
- Start prompt: `firmware-analysis/round17/START_PROMPT.md`
- User action required: 手动在 Security Center → Command Security → Program Blacklist 移除/允许 `C:\Windows\System32\wsl.exe`；随后以管理员身份重新启动 local Agent。
- Agent 不得编辑黑名单、绕过安全策略、关闭安全软件或重试其他执行路径。
- 主 AI 决策：保留现有 C: Ubuntu，不迁移/不注销/不覆盖；在 D: 新装独立 Ubuntu-24.04 到 `D:\WSL\Ubuntu-24.04`。
- Store WSL 2.7.3.0 先做 CLI 验证，不盲目全量重装；VMP 已启用，不预启用 legacy WSL 或 HypervisorPlatform。省略 `--no-launch`，正常首次启动并由用户亲自创建 Linux 账户，再验证发行版 Version=2、Ubuntu 24.04 noble、D: BasePath。
- ROUND17 后续同步 official kernel manifest、pin ACK common 到 `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`，采集 manifest/toolchain；本轮仍不编译。

### 当前第二 AI 任务：ROUND58（实现而非复审）

- Branch: `ai-parallel/round58-kleaf-target-audit`
- Task: `kernel-baseline/round58/ROUND58_TASK.md`
- Start prompt: `kernel-baseline/round58/START_PROMPT.md`
- Deliverables: concrete no-`base_kernel` full-image Kleaf BUILD patch candidate; deterministic final .config validation Python helper and tests; exact post-ROUND17 integration/build runbook.
- 必须只写它的专属分支，不修改 main / firmware-audit-v1 / protected DTS / PR #1。
- 不可声称实际 Bazel/build 已运行；第一版目标聚焦 Image，不臆造 DTB/boot packaging。

当前并行队列：
1. 用户处理 WSL blacklist 和 elevated Agent 前置条件。
2. 本地 Agent 等待后执行 ROUND17。
3. 第二 AI 执行 ROUND58。
4. 主 AI 独立准备并审核实际 patch/build 集成。

PR #1 保持 Draft/Open/unmerged；Stage A ACK 6.18.33 先于 Stage B Android 17 DerpFest。


## Correction to ROUND17 security-policy instructions (2026-11-24)

Do not follow the older appended note that directs the user to "Security Center → Command Security → Program Blacklist". That menu path was inferred without identifying the policy product and is now explicitly withdrawn. The user confirmed the menu is not present.

ROUND16 wording proves only that the local Agent's sandbox blocked execution of `wsl.exe`; it does not prove the block belongs to Windows Security Center, Microsoft Defender or a named endpoint product. The policy owner is UNKNOWN.

The current ROUND17 taskbook is diagnostic-first and supersedes all previous ROUND17 instructions:
- passively identify local Agent app/version/execution mode and policy source;
- use the exact product's official docs to find any supported authorization procedure;
- do not retry wsl.exe, do not use alternate shells/wrappers/copies/renames, do not bypass or disable security;
- do not launch the whole Agent elevated until a later step actually requires elevation.

## ROUND59 当前补丁系列核验与 WorkBuddy 状态（2026-11-24）

- ROUND59 report: `kernel-baseline/round59/round59_ufs_patch_series_exact_source_integration.md`.
- 完整 UFS patch order ROUND32 → ROUND57 → ROUND36 → ROUND52-0001 → ROUND37 (board .dts.draft fixture only) → ROUND33 → ROUND52-0002; 16/16 exact hunk contexts and new line anchors matched against exact source blobs in an in-memory simulation.
- This is not real `git apply`, `git diff --check`, dt-schema, Kconfig or build. See ROUND59 for full identities and boundaries.
- ROUND57 hunk defect fixed: current canonical patch blob is `3656f05ad01d54452b83591b762faaa71a16f592`, header `@@ -165,13 +165,15 @@`. Do not use prior blob `f282a695...`.
- The local Agent product is known: WorkBuddy, model DeepSeek V4.1 Flash. ROUND17 should let WorkBuddy identify its own command execution policy/approval mechanism from its own app context. Do not direct the user to the unverified Windows Security Center menu and do not blindly ask for elevation.
- The second AI remains assigned ROUND58 on `ai-parallel/round58-kleaf-target-audit`.
