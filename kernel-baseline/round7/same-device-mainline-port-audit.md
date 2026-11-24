# DBY-W09 同型号主线 Linux 项目与 Linux 6.18 驱动能力对照

核验日期：2026-11-24  
目标设备：Huawei MatePad 11 DBY-W09 / Qualcomm KONA / SM8250  
用途：为 Android Common Kernel android17-6.18（源码分支当前版本 6.18.33）收集同型号硬件与启动链证据。  
范围：公开 GitHub 源码、项目文档及 Linux v6.18 上游源码静态阅读。没有运行外部脚本、下载完整内核树、连接设备、刷机或编译。

## 1. 结论摘要

**DBY-W09 并不是没有新内核支持的空白设备。** 已找到多条公开的同型号主线 Linux 7.x 开发项目：

| 项目 | 公开内核基线 | 可供本项目使用的资料 | 证据边界 |
|---|---|---|---|
| [svesnav/linux-dby-w09](https://github.com/svesnav/linux-dby-w09) | Linux 7.0.14 | Huawei board DTS、rootparam DTBO、面板/触摸/电源/音频/USB/相机适配代码、构建配置 | README 的功能状态属于项目维护者声明，不等于独立复现 |
| [youzjuzi/dby-w09-kernel](https://github.com/youzjuzi/dby-w09-kernel) + [项目中心](https://github.com/youzjuzi/dby-w09-linux) | Linux 7.2.10，21 个补丁 | 设备树来源、私有输入边界、补丁说明、H/R/O/U 证据等级和已知问题 | 项目明示独立第三方复现仍未完成，部分功能只在一台设备上测试 |
| [CoWave-Fall/linux-on-arm-matepad11](https://github.com/CoWave-Fall/linux-on-arm-matepad11) | Linux 7.3.4（状态页记录） | 另一套 U-Boot、Linux、Arch Linux ARM 及硬件 bring-up 参考 | 状态表不能替代每项驱动的源码和测试范围审查 |

这些项目不是 Android GKI 6.18.33 移植项目，也不是可直接刷入的 Android 内核包。价值在于可复用的硬件事实线索：GPIO、供电、PMIC、面板连接、触摸协议、设备树、启动器限制与固件文件类别。不要使用这些项目发布的 kernel、boot、recovery、DTB、DTBO 或模块替代本项目固件。

建议参考顺序：
1. 用 youzjuzi 项目检查功能证据等级、私有输入与未解决问题。
2. 用 svesnav 项目查看更完整的 Huawei board DTS、rootparam DTBO 和构建选项。
3. 用 CoWave 项目进行第三方交叉参考，但不将其功能状态表视为本机 HOS 4.3 证据。

## 2. 强交叉验证：SM8250 revision 与 Huawei DTBO board-id

本项目 ROUND3 的 HarmonyOS 4.3 报告给出：
- 确定的 boot DTB：msm-id 为十进制 [356, 131073]，即十六进制 [0x164, 0x20001]，对应 KONA v2.1。
- 9 个 DTBO entry 的 board-id 为十进制：8200、8296、8206、8208、8202、8238、8302、8240、8298。
- 最后一个 board-id 为 8298，即 0x206a。
- 报告文件：[ROUND3 round3_summary.json](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round3/round3_summary.json)。

[svesnav Huawei DTS](https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts) 同样声明 SM8250 revision 0x20001。其 [dby-w09-rootparam.dtso](https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso) 使用 board-id 0x206a，并向 /rootparam 写入 Huawei board identity。

svesnav README 还报告：ABL 所选的 DTBO entry 必须填充 /rootparam，其他 entry 会使设备退回 fastboot；该项目也报告 fastboot boot RAM boot 被拒绝。来源：[svesnav README boot flow](https://github.com/svesnav/linux-dby-w09#boot-flow)。

**这组 ID 对应关系很强：** 我们的 HOS 4.3 DTBO 报告确实存在 board-id 0x206a，外部同型号项目也把 0x206a 用作 Huawei DBY-W09 overlay ID。后续 DTBO 设计必须保留并正确处理这个启动契约，不能只放入 generic SM8250 DTB 而忽略 rootparam。

但外部项目的一些早期硬件输入以 HarmonyOS 4.2 为基线，而本项目固件是 HarmonyOS 4.3。外部 DTS 只能当参考，本项目 4.3 的 boot DTB/DTBO 才是本机板级事实来源。

## 3. UFS：不是从零寻找 Qualcomm 865 驱动

Linux v6.18 上游已经包含：
- SCSI_UFS_QCOM：Qualcomm UFS host-specific hooks；
- PHY_QCOM_QMP_UFS：Qualcomm QMP UFS PHY；
- arch/arm64/boot/dts/qcom/sm8250.dtsi：SM8250 SoC 级设备树。

同型号 svesnav Linux 7.0.14 的构建脚本还明确把 SCSI_UFS_QCOM 和 PHY_QCOM_QMP_UFS 设为 built-in。

源码入口：
- [Linux v6.18 SM8250 DTS](https://github.com/torvalds/linux/blob/v6.18/arch/arm64/boot/dts/qcom/sm8250.dtsi)
- [Linux v6.18 UFS Kconfig](https://github.com/torvalds/linux/blob/v6.18/drivers/ufs/host/Kconfig)
- [Linux v6.18 Qualcomm QMP PHY Kconfig](https://github.com/torvalds/linux/blob/v6.18/drivers/phy/qualcomm/Kconfig)
- [同型号 svesnav 构建配置](https://github.com/svesnav/linux-dby-w09/blob/main/configure-and-build.sh)

**结论：** “SM8250/865 完全缺少 UFS 主线驱动”这一笼统判断不成立。通用 UFS host 与 QMP UFS PHY 驱动已经存在，并且同型号主线 Linux 项目使用它们。

仍须以本项目 HOS 4.3 设备树核对 UFS 节点、QMP PHY lane、时钟、复位、regulator、功耗状态切换和实际控制器属性。驱动存在不等于华为板级参数正确，也不保证从 4.19 升级后立即可以启动。

## 4. Linux v6.18 公共驱动和 DBY-W09 板级缺口

以下是 Linux v6.18 mainline 静态代码检查。Google android17-6.18 ACK 与 torvalds/linux v6.18 并非完全相同的 commit tree；选定 ACK commit 后还要复核相关文件差异。

| 子系统 | 上游基础支持 | DBY-W09 仍需适配/确认的部分 | 当前判断 |
|---|---|---|---|
| SM8250 SoC | clocks、power domains、interconnect、pinctrl、PMIC 和 SoC DTS 基础 | HOS 4.3 的节点状态、reserved memory、PMIC rails、电压和 GPIO pinmux | 公共基础可复用，板级 DTS 必须定制 |
| UFS | Qualcomm UFS host + QMP UFS PHY | UFS PHY、时钟、reset、regulators、gear/power mode 与 bootloader handoff | 驱动不是空白，板级配置是重点 |
| GPU | DRM MSM / Adreno 6xx 基础驱动；同型号项目报告 Adreno 650 + freedreno | Huawei ZAP shader、固件名、内存保留区及固件版本 | 驱动基础存在，设备私有固件要核验 |
| Wi-Fi / BT | ath11k PCI 支持 QCA6390 和 QCA6391 系列 | 本机 HOS 4.3 芯片变体、PCI ID、board calibration、BT NVM、供电与 enable GPIO | 驱动基础存在，实际芯片型号 UNKNOWN |
| 显示 | MSM DRM、DSI、PHY、backlight/regulator 框架；上游有 NT36523 通用面板驱动 | Huawei 面板完整 DSI mode、双链路/C-PHY、初始化命令、TPS65132 电源时序、RT8555 背光与 reset GPIO | 高风险板级工作，不能直接套 Xiaomi panel |
| 触摸/手写笔 | SPI、输入子系统基础 | Huawei THP 接口、Novatek 控制器、aptouch_daemon 协议、匹配触摸固件 | 存在明显的专用驱动/userspace 缺口 |
| 音频 | QDSP6/Q6AFE、APR、SoundWire、WCD9380/9385 codec 基础 | TFA9874 扬声器 TDM routing、Q6AFE/Q6routing、DAI link、通道映射与 DSP firmware | 公共 DSP/codec 基础存在，板级音频链需适配 |
| 摄像头 | OV13B10、Hi846、DW9714 sensor/lens 项目已出现在上游 Kconfig | CAMSS/CSIPHY、CCI、MCLK、rails、sensor mode、设备树 graph | 部分驱动已有，不代表整套相机链可用 |
| USB-C / DP | QMP Combo PHY、DWC3、Type-C/TCPC/MUX 框架 | PMIC Type-C、mux、GPIO、DP lane、HDMI audio route | 公共框架存在，需核对板级拓扑 |

上游源码入口：
- [SM8250 SoC DTS](https://github.com/torvalds/linux/blob/v6.18/arch/arm64/boot/dts/qcom/sm8250.dtsi)
- [SM8250 Xiaomi Elish common DTS（仅作同 SoC 参考）](https://github.com/torvalds/linux/blob/v6.18/arch/arm64/boot/dts/qcom/sm8250-xiaomi-elish-common.dtsi)
- [MSM DRM Kconfig](https://github.com/torvalds/linux/blob/v6.18/drivers/gpu/drm/msm/Kconfig)
- [Novatek NT36523 panel driver](https://github.com/torvalds/linux/blob/v6.18/drivers/gpu/drm/panel/panel-novatek-nt36523.c)
- [ath11k Kconfig](https://github.com/torvalds/linux/blob/v6.18/drivers/net/wireless/ath/ath11k/Kconfig)
- [WCD938x SoundWire Kconfig](https://github.com/torvalds/linux/blob/v6.18/sound/soc/codecs/Kconfig)
- [OV13B10 / Hi846 / DW9714 Kconfig](https://github.com/torvalds/linux/blob/v6.18/drivers/media/i2c/Kconfig)

### 4.1 Xiaomi Elish 设备树的使用边界

Linux v6.18 已有 sm8250-xiaomi-elish-common.dtsi。其 SoC revision 同样为 SM8250 0x20001，但 Xiaomi board-id 为 0x10008，与 Huawei 本机 DTBO 的 0x206a 不同。

可借鉴 Qualcomm 公共 SoC 节点、PMIC/clock/interconnect 的定义结构；不能把 Elish 的 board-id、panel、GPIO、regulator 或整份 DTS 覆盖到 DBY-W09。此前检查的小米 Pad 5 Pro ColorOS ZIP 也没有 kernel source、DTS、defconfig 或 patch，仍只是 reference-only。

### 4.2 NT36523 控制器名称相同，不代表面板驱动通用

Linux v6.18 的 DRM_PANEL_NOVATEK_NT36523 Kconfig 说明中，举例的是 Xiaomi Mi Pad 5 / 5 Pro 的 BOE panel。

svesnav 同型号项目则单独定义 DRM_PANEL_HUAWEI_DBY_W09，并处理 Huawei 面板初始化与背光/供电时序；另一同型号项目还要求所有者提供来自运行时 FDT 的私有 panel command data。

所以不能因为华为面板使用 NT36523-family 控制器，就直接启用小米的面板描述。必须匹配 panel descriptor、DSI timing、lane/PHY mode、init command、电源和触摸协同。

### 4.3 QCA6390 / QCA6391 的型号冲突

公开同型号项目之间存在芯片称呼不一致：
- svesnav 与 youzjuzi 的固件/代码按 QCA6390 组织；
- CoWave README 的硬件表写 QCA6391；
- ath11k 驱动家族支持这两种芯片，不能据此判断用户这台设备具体装的是哪一种。

本项目应结合 HOS 4.3 DTB/DTBO、PCI vendor/device/subsystem ID、vendor firmware path 与 calibration 文件来确认。不能只按 Snapdragon 865 或小米同 SoC 设备推断无线芯片。

## 5. 启动链：原厂 legacy boot v2 与 GKI 标准启动布局的差别

本项目 ROUND1/2 已确认：
- 原厂 boot.img 使用 Android boot header v2；
- ramdisk 位于独立 ramdisk 分区；
- 无 vendor_boot / init_boot；
- boot image 内含 DTB 区域，ROUND3 确定 DTB offset 为 22,790,144 bytes。

svesnav 同型号项目报告其 Linux 启动方案：
- ABL 读取 header v2 的 boot；
- 从单独 ramdisk 分区读取 ramdisk；
- 将新 kernel、DTB、cmdline 与旧 header v2 布局组合；
- 单独处理 ramdisk 与 DTBO；
- ABL 需要正确选中 board-id 0x206a 的 rootparam overlay；
- fastboot boot RAM boot 被拒绝，项目因此依赖分区更新测试。

来源：[svesnav README boot flow](https://github.com/svesnav/linux-dby-w09#boot-flow) 与 [rootparam overlay](https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso)。

这提示一种需要研究的自定义包装方案：研究是否可以在保留原厂 boot v2、独立 ramdisk、DTBO/rootparam 契约的情况下加载新内核。但这不等于符合官方 GKI 结构，也不等于本项目已验证。

AOSP 规范区分通用 boot、vendor_boot 和 boot header 版本：
- [Generic boot partition](https://source.android.com/docs/core/architecture/partitions/generic-boot)
- [Vendor boot partitions](https://source.android.com/docs/core/architecture/partitions/vendor-boot-partitions)
- [Boot image header](https://source.android.com/docs/core/architecture/bootloader/boot-image-header)

因此：
1. 不可将 Google 发布的 GKI boot.img 直接当作 DBY-W09 header v2 boot 镜像使用。
2. 若自行编译 ACK 内核，再按旧 header v2 打包，初期应称为 ACK-based custom legacy-boot kernel；在 GKI boot layout、KMI/VTS 等要求没有满足前，不称 certified GKI。
3. 保留 Android 12 旧 ramdisk 与迁移 Android 17 GKI 是两个不同的软件集成目标。
4. 当前只做静态研究，不执行测试性刷写、解锁或分区写入。

## 6. 同型号项目揭示的私有输入

youzjuzi 项目说明其公开 board DTS 仍依赖所有者 runtime FDT 生成的 memory include、私有 panel command data；触摸还依赖匹配 AFE 源和多项私有 touch-plan inputs。

其固件准备文档将以下项目列为该项目的本机输入示例：
- QCA6390 Wi-Fi 固件和设备专用 board data；
- 蓝牙固件与设备专用 NVM；
- Adreno 650 GPU firmware / Huawei ZAP；
- Novatek THP 固件。

这些是外部 HarmonyOS 4.2 基线的线索，不代表本项目 HOS 4.3 中的文件路径、内容或型号必然相同。不要公开这些固件、校准数据、面板命令表、原始 manifest、MAC/序列号或本地完整摘要。

资料入口：
- [youzjuzi device-tree guide](https://github.com/youzjuzi/dby-w09-kernel/tree/main/dts)
- [youzjuzi firmware preparation](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/firmware-preparation.md)
- [youzjuzi patch notes](https://github.com/youzjuzi/dby-w09-kernel/blob/main/docs/patch-notes.md)
- [svesnav Huawei DTS](https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts)
- [svesnav Huawei THP bridge](https://github.com/svesnav/linux-dby-w09/blob/main/touch/huawei-thp-lite.c)

## 7. 本项目下一步路线

继续以 Android Common Kernel / GKI 6.18.33 为目标做研究，不因发现 Linux 7.x 项目就擅自将项目切换成 Linux 桌面移植。把同型号 Linux 7.x 项目视为设备树和硬件 bring-up 的证据来源。

最有价值的下一步是**逐项枚举本项目 HOS 4.3 的原始 DTB / 9 个 DTBO 属性，再与同型号 DTS 交叉比对**。这是本机的二进制工作副本，ChatGPT 当前无法直接访问；这部分才需要本地 Agent。

只读 inventory 至少覆盖：
- base DTB 的 model / compatible / msm-id / board-id；
- 9 个 overlay 的 index、board-id、id/rev、model、compatible、rootparam；
- DSI/display/panel、SPI touch、PCIe/WLAN、UFS/QMP；
- PMIC、regulator 电压、GPIO、clocks、interconnect；
- WCD938x/SoundWire/audio、USB-C/DP mux、camera；
- reserved-memory 的节点名称和用途（敏感私有地址不公开）。

将各节点分类为 MATCH / DIFFERENT_VALUE / ONLY_IN_LOCAL_43 / ONLY_IN_REFERENCE / UNKNOWN；外部项目中 HarmonyOS 4.2 设备树不得覆盖本项目 4.3 的硬件事实。

随后才做 EROFS 内容枚举（待可信读取工具）及 vendor module/KMI/VINTF 审核。ROUND5 的 EROFS BLOCKED 状态不变；未取得可信工具前不自写解码器、不下载未知二进制、不绕过 WSL 安全限制。

## 8. 证据边界

- 本报告确认的是公开源码/文档中存在相关代码和维护者报告；不证明其与本项目 HOS 4.3 的每个板级参数相同。
- 代码存在不等于本机 4.3 已启动验证。
- 外部项目的功能状态属于其自身设备/固件/构建和有限测试范围；没有把它们写成第三方独立复现。
- Linux v6.18 mainline 与 Google android17-6.18 ACK 并非相同 commit tree；实际移植前必须在选定 ACK commit 上复核相关文件。
- 本报告没有下载完整内核树，没有运行任何外部 build/installer/flash 脚本，没有连接或操作平板，没有编译内核。
