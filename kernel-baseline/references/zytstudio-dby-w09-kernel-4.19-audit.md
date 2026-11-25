# 1号 AI 参考仓库审查 — zytstudio/DBY-W09-Kernel

审查日期：2026-11-25
审查对象：https://github.com/zytstudio/DBY-W09-Kernel
审查时 master HEAD：cf2b854a9d36969856cbe85c1f9c90ac54b8d4d0
项目定位：Huawei MatePad 11 (2021) DBY-W09 / KONA / SM8250 的 HarmonyOS 4.3.0.196 原厂 Linux 4.19.157-perf 内核构建工程。
角色：1号 AI 独立参考资料审查；没有修改外部仓库、AI2 分支、DTS 草案或固件。

## 1. 结论与可用范围

该仓库确实针对同一设备型号 DBY-W09，不是泛用 SM8250 设备项目。它提供同机历史参考，包括运行中的 4.19 内核配置、华为内核构建修正、原厂 boot 镜像布局与作者报告的设备实测经验。

但它的目标是 HarmonyOS 4.3 vendor 4.19.157-perf，不是当前项目固定的 ACK android17-6.18.33_r00。不能直接把其内核源码、配置、构建产物或 patch 视为 6.18.33 适配方案，也不能因其 4.19 内核可启动而推断 6.18.33 已可启动。

处理原则：把它作为同型号设备的历史运行基线和启动/构建辅助证据，按需对照；所有可移植性都必须回到固定 ACK 源码、当前 HOS4.3 FDT/DTBO 和 Stage A 构建验证中重新证明。

## 2. 原厂运行配置（最高价值）

文件：[configs/running.config](https://github.com/zytstudio/DBY-W09-Kernel/blob/master/configs/running.config)
审查时 Git blob：4cf9559611d4c1c2f8bacfc3b98f76fb62cead1a
文件头标明 Linux/arm64 4.19.157 Kernel Configuration，仓库 README / SOURCE-MANIFEST 说明该配置取自设备 /proc/config.gz。

重点配置记录如下（均为该 4.19 配置，不代表当前 ACK 6.18 .config）：

- UFS：CONFIG_SCSI_UFSHCD=y、CONFIG_SCSI_UFSHCD_PLATFORM=y、CONFIG_SCSI_UFS_QCOM=y、CONFIG_SCSI_UFS_HI1861_VCMD=y、CONFIG_SCSI_UFS_CRYPTO=y、CONFIG_SCSI_UFS_CRYPTO_QTI=y。
- UFS PHY：CONFIG_PHY_QCOM_UFS=y。
- RPMh 基础：CONFIG_QCOM_RPMH=y、CONFIG_QCOM_COMMAND_DB=y。
- Vendor 4.19 regulator：CONFIG_REGULATOR=y、CONFIG_REGULATOR_RPMH=y、CONFIG_REGULATOR_STUB=y、CONFIG_REGULATOR_PROXY_CONSUMER=y。
- 特别注意：该配置中 CONFIG_REGULATOR_QCOM_RPMH 是 not set，而 CONFIG_REGULATOR_RPMH=y。二者不能混为同一 Kconfig symbol，也不能把 vendor 4.19 的驱动配置名直接移植到 ACK 6.18。
- QMP/USB：CONFIG_MSM_QMP=y、CONFIG_USB_MSM_SSPHY_QMP=y。
- Kona 时钟/平台：CONFIG_MSM_GCC_KONA=y、CONFIG_MSM_VIDEOCC_KONA=y、CONFIG_MSM_DISPCC_KONA=y、CONFIG_MSM_CAMCC_KONA=y、CONFIG_MSM_GPUCC_KONA=y。
- IOMMU/GPU：CONFIG_ARM_SMMU=y、CONFIG_IOMMU_DMA=y、CONFIG_QCOM_KGSL=y、CONFIG_QCOM_KGSL_IOMMU=y。

### 对 Stage A 的用法

把这份 running.config 当作同机 4.19 历史运行证据，与 ACK 6.18.33 最终 .config 做差异矩阵，优先关注 UFS/UFS crypto/UFS PHY、RPMh/Command DB/regulator、QMP、Kona clocks、SMMU/IOMMU、KGSL 与关键 DMA/内存选项。

差异只用于发现待解释项，不得机械地把 4.19 symbol 复制到 6.18，也不能把 4.19 的 vendor 私有实现当成 ACK upstream driver 的等价物。每个差异必须分别判断：Kconfig 改名/拆分、驱动架构变化、硬件不再需要、由 DT/firmware 负责，还是 Stage A 配置遗漏。

## 3. 华为 4.19 源码与补丁经验

文件：[SOURCE-MANIFEST.md](https://github.com/zytstudio/DBY-W09-Kernel/blob/master/SOURCE-MANIFEST.md)

该工程声明其官方开源源码包为 DBY-W09_HarmonyOS4.0.0_opensource.tar.gz，SHA-256：
52c38060cf2990e44bbc556f39271f6e97af90777a300165443946aa97c72e5f。
源码包没有直接放入该仓库，需从华为开源页面另行取得。

仓库的 scripts/patch_source.py 记录了 vendor 4.19 构建中遇到的修正类型，包括：
- clang 输出多行导致 mkcompile_h 版本提取异常；
- qcacld out-of-tree 构建路径改为 $(srctree)；
- 华为私有 Kconfig 对 KPROBES/KRETPROBES 的额外依赖；
- 5.x backport 引入的若干 -Werror 选项与 4.19 代码不兼容；
- 缺失厂商 XML 输入时生成 lcd_kit_dpd.h stub；
- RTIC .bss 链接布局与非 relocatable arm64 链接问题。

这些是该仓库 vendor 4.19 构建修正记录。尤其缺输入而构造的 LCD stub、链接脚本修改和编译告警降级，不能直接套用到 6.18.33；只能在未来发现同类故障时作为排查线索。

另外 scripts/patch_msm_fault.py 为其华为 display techpack 的导入 dma-buf CPU mmap 路径增加页数组构建与 NULL 防护，防止 msm_gem_fault() 解引用空页数组。该补丁针对 4.19 vendor techpack/display/msm/msm_gem.c 的特定实现。今后只有在 ACK 6.18 对应代码仍存在相同缺陷、且接口/生命周期核验通过时，才考虑独立重写；不得原样 cherry-pick。

## 4. Boot 镜像布局和打包参考

文件：[scripts/pack_boot.py](https://github.com/zytstudio/DBY-W09-Kernel/blob/master/scripts/pack_boot.py)、[docs/BUILD.md](https://github.com/zytstudio/DBY-W09-Kernel/blob/master/docs/BUILD.md)。

该工程描述其设备模板：
- boot 分区容量为 96 MiB；
- Android boot header v2；
- page size 4096；
- gzip kernel payload；
- ramdisk、DTB、cmdline、os_version 与 AVB footer 来自原厂 boot 模板；
- 该项目的打包器替换 kernel payload，并按 payload 长度必要时移动 vbmeta/footer。

其文档称作者在自身测试环境中报告 boot 镜像仅替换 kernel 后可以启动，并称其设备环境 AVB 未强制执行。此为该外部项目/作者环境的记录，不能推断当前设备状态、当前 HOS4.3 ABL 选择行为、6.18.33 启动兼容性或当前项目 AVB/vbmeta_cust 已闭合。

对本项目的用法：作为 DBY-W09 曾使用的 boot header/layout 历史参考。当前项目仍须依 ROUND61 Phase E/F 取得真实 ABL→Linux FDT/memory handoff、boot packaging、DTBO 运行时选择和 AVB/vbmeta_cust 证据；不能因外部项目的 4.19 简化打包流程而跳过这些阶段门槛。

## 5. 项目约束与不采纳事项

1. 不切换项目目标：先完成 ACK 6.18.33 GKI Stage A，再进入 DerpFest Stage B。
2. 不把该仓库 4.19 内核或它的二进制 boot images 当作 6.18.33 移植产物。
3. 不把其 running.config 当作 6.18.33 最终配置；只用于差异审查。
4. 不将其 vendor 4.19 patches 原样应用到 ACK。
5. 不把作者报告的 AVB 状态、DTB 选择或实机验证外推到当前设备/当前 6.18 移植。
6. 不下载、上传或重新分发其未公开在仓库中的大体积华为源码包、boot template 或二进制镜像。

## 6. 本轮核验范围与复现入口

本轮只读审查了公开 GitHub 仓库的 README、SOURCE-MANIFEST、BUILD 文档、running.config、patch_source.py、patch_msm_fault.py 与 pack_boot.py。没有 clone/构建该仓库，没有访问用户设备，没有下载或写入外部源码/镜像，也没有修改该外部仓库。

外部仓库审查时 master HEAD：cf2b854a9d36969856cbe85c1f9c90ac54b8d4d0。
若未来引用，请先重新核对该仓库的当前 HEAD 与文件 blob，避免沿用变化后的引用。
