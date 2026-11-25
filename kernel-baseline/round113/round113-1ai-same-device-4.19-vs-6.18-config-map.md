# ROUND113 — 1号 AI 独立审查：同设备 vendor 4.19 与 ACK 6.18.33 Stage A 配置映射

审查日期：2026-11-25
任务归属：1号 AI（ChatGPT）；独立源码/config 审查，不是 Agent 任务，也不是 2号 AI patch 实现。
设备：Huawei MatePad 11 DBY-W09 / KONA / SM8250
固定 ACK：android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
4.19 配置来源：zytstudio/DBY-W09-Kernel configs/running.config，blob 4cf9559611d4c1c2f8bacfc3b98f76fb62cead1a
6.18 配置来源：ROUND61 已验证 Kleaf build artifact dby_w09.config；size 238,376 bytes；SHA-256 5f7fd8b32a4127b7ca10d2333d71e6d10aec7a566cf886251f7bc2af253366d7
关联报告：[同型号 vendor 4.19 仓库审查](../references/zytstudio-dby-w09-kernel-4.19-audit.md)

## 1. 结论摘要

外部 4.19 配置与当前 6.18.33 Phase A–D build config 在 UFS host、QCOM UFS、RPMh、UFS PHY、SMMU/IOMMU 等核心方向有明显连续性，但若干驱动已发生 Kconfig/子系统架构变化。最重要的是：

1. Stage A 当前 6.18 config 已包含 UFS core/platform/QCOM host、QCOM UFS QMP PHY、QCOM RPMh regulator、QCOM inline crypto、SM8250 GCC、RPMh power domains 和 ARM SMMU QCOM。
2. 旧 vendor 4.19 的 regulator proxy consumer 并不是新 ACK 中一个现成的同名 Kconfig 组件；固定 ACK Kconfig/search 未找到该符号。它仍是需要独立源码移植的功能差异，当前 2号 AI 的 ROUND31 任务正处理 L5/L9 临时 proxy 生命周期。
3. 当前 Stage A config 没有启用 SM8250 GPU/display/camera clock controller，且 DRM_MSM 关闭；vendor 4.19 config 则启用了 KGSL 与 Kona GPU/display/camera clocks。这是 Stage B 图形/显示/相机支持的明确待办差异，但不阻止先完成 Stage A 的 UFS/storage/basic hardware gate。
4. 不能把每个旧 symbol 的缺失直接判成驱动缺失；需结合固定 ACK 的 Kconfig/Makefile 对照其现代替代 symbol 与对象文件。

## 2. 关键 symbol 映射矩阵

以下旧值来自同型号 vendor 4.19 running.config；新值来自 ROUND61 已构建的 ACK 6.18.33 dby_w09.config。新配置不是未来推测，来自真实 Phase A–D build artifact。

| 功能 | Vendor 4.19 running.config | ACK 6.18.33 Phase D config | 判断 |
|---|---|---|---|
| UFS core | SCSI_UFSHCD=y | SCSI_UFSHCD=y | 保留 |
| UFS platform | SCSI_UFSHCD_PLATFORM=y | SCSI_UFSHCD_PLATFORM=y | 保留 |
| Qualcomm UFS host | SCSI_UFS_QCOM=y | SCSI_UFS_QCOM=y | 保留 |
| Huawei HI1861 vendor command extension | SCSI_UFS_HI1861_VCMD=y | 未出现 | ACK search/Kconfig 未找到同名选项；是否需要该 vendor command 行为仍需从 runtime/use-site 证据判定，不可因 symbol 缺失就认定 UFS 基本不可用 |
| UFS Crypto | SCSI_UFS_CRYPTO=y + SCSI_UFS_CRYPTO_QTI=y | SCSI_UFS_CRYPTO=y + QCOM_INLINE_CRYPTO_ENGINE=y | Kconfig 架构差异；固定 ACK SCSI_UFS_QCOM 在启用 SCSI_UFS_CRYPTO 时 select QCOM_INLINE_CRYPTO_ENGINE。不要机械复制旧 QTI symbol |
| UFS PHY | PHY_QCOM_UFS=y | PHY_QCOM_QMP_UFS=y | 新 ACK 使用 QMP UFS PHY Kconfig 名；需与真实 PHY 节点 compatible/driver probe 对照 |
| QMP PHY framework | MSM_QMP=y | PHY_QCOM_QMP=y | vendor 私有/旧 QMP 层与 common PHY framework 的命名/架构差异 |
| USB QMP PHY | USB_MSM_SSPHY_QMP=y | PHY_QCOM_QMP_USB=y | 现代 PHY provider symbol；USB 的运行验证仍独立 |
| RPMh base | QCOM_RPMH=y + QCOM_COMMAND_DB=y | QCOM_RPMH=y + QCOM_COMMAND_DB=y | 保留 |
| RPMh regulator | REGULATOR_RPMH=y | REGULATOR_QCOM_RPMH=y | 新 ACK 使用明确的 Qualcomm RPMh regulator symbol，非原样同名 |
| Temporary proxy consumer | REGULATOR_PROXY_CONSUMER=y | 无同名 symbol/选项 | 真实功能差异；Round31 正在实现 HOS4.3 L5/L9 临时 proxy lifecycle，不能用永久 system-load / always-on 替代 |
| SMMU | ARM_SMMU=y + IOMMU_DMA=y | ARM_SMMU=y + ARM_SMMU_QCOM=y + IOMMU_DMA=y | 新 ACK 有 Qualcomm SMMU integration；仍需用 board DT 和 runtime 核验实际 attach |
| SM8250 Global Clock Controller | MSM_GCC_KONA=y | SM_GCC_8250=y | 现代 ACK 使用 SM8250 GCC symbol；固定 ACK Kconfig/Makefile 有对应 gcc-sm8250 object |
| GPU clock controller | MSM_GPUCC_KONA=y | SM_GPUCC_8250 is not set | 当前 Stage A 尚未启用 |
| Display clock controller | MSM_DISPCC_KONA=y | SM_DISPCC_8250 is not set | 当前 Stage A 尚未启用 |
| Camera clock controller | MSM_CAMCC_KONA=y | SM_CAMCC_8250 is not set | 当前 Stage A 尚未启用 |
| GPU driver | QCOM_KGSL=y + QCOM_KGSL_IOMMU=y | QCOM_KGSL symbol 不存在；DRM_MSM is not set | 当前 Stage A config 未提供已启用的 3D GPU 驱动路径；Stage B 必须专门解决 |
| GDSC | QCOM_GDSC=y | QCOM_GDSC=y | 保留；不能替代各具体 GCC/ GPUCC / DISPCC clocks |

## 3. 固定 ACK 的源码映射证据

本轮对固定 ACK commit 的以下文件做了只读检查：

- drivers/clk/qcom/Kconfig（blob 6fef0bfc17736b62e89d4d2e434a0a59f4f081aa）
- drivers/clk/qcom/Makefile（blob 8051d481c439bd940e56fcbe40fcaf48f556ff43）
- drivers/phy/qualcomm/Kconfig（blob 60a0ead127fa9f08749e1bc686e15cc5eb341c28）
- drivers/regulator/Kconfig（blob d84f3d054c59d86d91d859808aa73a3b609d16d0）
- drivers/ufs/host/Kconfig（blob 48ee7e9b665efcb376f32746b49fbe437e7dd618）
- drivers/gpu/drm/msm/Kconfig（blob 250246f81ea94f01a016e8938f08e1aa4ce02442）

已核实：
- SM_GCC_8250 是 SM8250 Global Clock Controller；其 Kconfig 选择 QCOM_GDSC，Makefile 将它绑定到 gcc-sm8250.o。当前 Stage A .config 中 SM_GCC_8250=y。
- SM_GPUCC_8250、SM_DISPCC_8250、SM_CAMCC_8250 分别对应 SM8250 GPU、Display、Camera clock controller；Makefile 对应 gpucc-sm8250.o、dispcc-sm8250.o、camcc-sm8250.o。当前 Stage A .config 中三者均未启用。
- PHY_QCOM_QMP_UFS 在固定 ACK PHY Kconfig 中定义为 Qualcomm QMP UFS PHY Driver；当前 Stage A .config 启用。
- REGULATOR_QCOM_RPMH 在固定 ACK regulator Kconfig 中定义为 Qualcomm RPMh regulator driver；当前 Stage A .config 启用。
- SCSI_UFS_QCOM 在固定 ACK UFS Kconfig 中，当 SCSI_UFS_CRYPTO 启用时会 select QCOM_INLINE_CRYPTO_ENGINE；当前 Stage A config 两个均启用。
- 固定 ACK 的 drivers/gpu/drm/msm/Kconfig 提供 DRM_MSM 配置入口，但当前 Stage A config 为 not set。
- 对固定 ACK common kernel 的 HI1861、REGULATOR_PROXY_CONSUMER、QCOM_KGSL 搜索未返回实现命中；这与当前 Kconfig/config 结果一致，但搜索索引不是源码完整性证明。不得仅凭搜索空结果作最终功能判定。

## 4. 对后续阶段的影响

### Stage A（当前优先）

- 当前 storage-first 基线已经启用 UFS core/platform/QCOM host、QMP UFS PHY、RPMh regulator、QCOM inline crypto、SM8250 GCC、QCOM RPMh/GDSC、ARM SMMU QCOM。
- 本轮对照没有发现需要为了照搬 4.19 而立即扩大 Stage A 配置的理由。
- ROUND31 proxy consumer lifecycle 仍须由 2号 AI 按自己的任务实际实现、测试并重建 Image；1号 AI 不替代其编码工作。
- 不得因 6.18 config 已启用某 symbol 就宣称对应设备硬件已成功 probe/工作；还要通过 Phase E/F/G 的真实 boot/handoff/运行验证。

### Stage B（DerpFest / 图形桌面）

- 现有 Phase D .config 明确没有 SM8250 GPUCC、DISPCC、CAMCC，也没有启用 DRM_MSM；旧 4.19 配置曾启用 KGSL 与 Kona GPU/display/camera clocks。
- 因此 DerpFest 的屏幕点亮、DPU/DSI、GPU 3D acceleration、硬件合成和 camera 均未由当前 Phase D build 证明。
- 后续需单独研究 SM8250 DPU/MDSS display path、QMP DSI PHY、SM8250 GPUCC/Adreno 驱动、KGSL 与 Android Adreno userspace/HAL 的兼容性，以及 camera clock path。
- DRM_MSM 即使后续开启，也不能未经接口验证就宣称它可替换 Android Qualcomm KGSL userspace ABI。GPU kernel/userspace interface 是独立兼容性问题。
- 这些 Stage B 工作必须等 Stage A boot/UFS/storage/basic hardware acceptance 后再展开；当前不改变先后顺序。

## 5. 未解决项与禁止推断

1. HI1861 vendor command extension 是否被该设备实际运行路径使用，尚未从 4.19 source/use-site 或 runtime log 证明。
2. 4.19 SCSI_UFS_CRYPTO_QTI 与 6.18 QCOM_INLINE_CRYPTO_ENGINE 的设备级功能等价/ICE firmware/DT 配置，不能仅凭 Kconfig select 判定完全等价。
3. 现代 QMP UFS PHY 和 vendor 4.19 PHY 在真实 DBY-W09 FDT compatible、reset/clock/regulator sequence 上仍需运行时验证。
4. 4.19 的 MSM_GPUCC_KONA 等符号到现代 SM8250 symbols 是 SoC 驱动架构映射，不代表已存在或已测试所需 DT 节点。
5. 4.19 running.config 表明作者设备当时运行过这些功能；它不证明当前 6.18 kernel、当前 ABL、当前 DTBO 或 DerpFest userspace 能使用。
6. 不能把 4.19 的 REGULATOR_PROXY_CONSUMER 配置差异误写成普通 Kconfig 缺漏；Round31 必须对照 Qualcomm proxy-consumer 真正生命周期语义实现。

## 6. 本轮范围

本轮只对照 ROUND61 已保存的 dby_w09.config 与外部公开 running.config，并只读取固定 ACK Kconfig/Makefile。没有修改 AI2 branch、DTS、binding、source patch、firmware、boot image 或设备；没有运行新 build，也没有把 build artifact 上传至 GitHub。
