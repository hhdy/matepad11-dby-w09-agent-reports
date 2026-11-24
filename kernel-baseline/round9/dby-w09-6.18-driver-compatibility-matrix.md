# DBY-W09 → ACK / GKI 6.18.33：ROUND8 后驱动与设备树兼容矩阵

核验日期：2026-11-24  
目标设备：Huawei MatePad 11 DBY-W09 / KONA / SM8250 v2.1  
研究范围：ROUND8 的 HOS 4.3 DTBO entry 8 target-resolution 结果、ROUND7 脱敏 FDT 属性、同型号公开 Linux port、Linux v6.18 上游 DTS / driver / binding。  
状态：源码静态对照完成；未编译、未在设备验证；不是可直接套用的完整 DTS patch。

## 1. 核验口径与核心结论

本报告区分三个证据层级：

1. **设备本地证据**：ROUND3 / ROUND7 / ROUND8 从用户设备现有 HarmonyOS 4.3 FDT/DTBO 工作副本提取的脱敏文本。描述设备当前固件的节点、属性和 overlay target，是本设备优先级最高的静态证据。
2. **同型号 Linux 参考**：公开的 svesnav DBY-W09 Linux 7.0.14 源码，以及 youzjuzi DBY-W09 Linux 7.2.10 资料。它们能提供同型号已探索过的板级连接和定制驱动线索，但属于维护者公开成果；部分注释追溯 HarmonyOS 4.2，不应自动当作 HOS 4.3 每个属性的实测真值。
3. **上游 Linux v6.18**：用于判断主线驱动是否存在、驱动匹配什么 compatible、SoC common DTS 如何定义硬件。它不是 Google `android17-6.18` ACK HEAD 的逐文件核验，也不证明 KMI/API 二进制兼容。

**整体结论：SM8250 上游已有多项关键硬件驱动；DBY-W09 的主要工作集中在板级 DTS、Huawei 专有设备接口、私有 firmware/configuration，以及 vendor compatible 到主线 binding 的转换。** 当前没有证据支持“SM8250 缺少 UFS 驱动”或“整套外设驱动可以原样沿用 HOS DTB”。

ROUND8 将 DTBO entry 8 的 145 个 fragment 全部解析：145/145 RESOLVED、0 UNRESOLVED；fragment@143 确认落在 `/rootparam`。这只解决了 entry 8 的 target 对应关系，仍不证明 bootloader 实际应用该 overlay、内核最终收到的运行时 FDT 内容，或某项设备已经能工作。

## 2. UFS：驱动存在，板级 overlay 明确启用；另有 compatible 适配点

### 本机证据

HOS 4.3 base boot FDT candidate 0：
- `/soc/ufshc@1d84000` compatible 为 `qcom,ufshc`，保留 UFS host reg、interrupt、PHY、clock 和 reset 属性，status 为 `disabled`。
- `/soc/ufsphy_mem@1d87000` status 为 `disabled`。

ROUND8 对 entry 8 的解析补上了关键链路：
- fragment@63 → `/soc/ufsphy_mem@1d87000`：status 改为 `ok`；PHY/PLL 供电属性分别带有 89,900 µA 和 18,800 µA 的 load 值。
- fragment@64 → `/soc/ufshc@1d84000`：status 改为 `ok`；提供 VCC、VCCQ、VCCQ2 等 supply phandle，以及最大电流、VCC 电压范围等属性。

这里 overlay 中出现的 `0xffffffff` supply phandle 是 DTBO 外部 phandle/fixup 占位符的表现，不能孤立地视为坏 phandle；必须结合完整 overlay 应用及对应 base symbol/fixup 才能得到最后引用关系。

### Linux v6.18 对照

- SM8250 common DTS 本来就把 UFS host / PHY 设为 disabled，这是 SoC common DTS 的默认状态，不等于 SoC 不支持 UFS。
- UFS host compatible `qcom,ufshc` 可由上游 Qualcomm UFS driver 的通用 OF match 命中。
- 上游 QMP UFS PHY driver 有专门的 `qcom,sm8250-qmp-ufs-phy` 配置：2 lanes、HS Gear 4 上限；PHY/PLL load 89,900 µA / 18,800 µA 与 HOS entry 8 数值一致。
- **关键 compatible 差异**：ROUND8 的目标节点 compatible summary 为 HOS vendor 字符串 `qcom,ufs-phy-qmp-v4`，而 Linux v6.18 PHY driver OF table 使用 `qcom,sm8250-qmp-ufs-phy`。为 ACK/mainline 移植生成板级 DTS 时，应基于主线 SM8250 node/binding，不能照搬这个 HOS vendor 字符串并假设驱动会自动匹配。

### 同型号参考 DTS 与供电核对

svesnav 同型号 board DTS 启用 `&ufs_mem_hc`、`&ufs_mem_phy`，并提供：
- VCC：`vreg_l17a_3p0`，regulator 允许范围 2.496–3.008 V；UFS 节点最大电流 750 mA。
- VCCQ：1.2 V rail；VCCQ2：1.8 V rail；各自最大电流 750 mA。
- PHY：0.88 V；PLL：1.2 V。

HOS entry 8 的 VCC 电压范围为 2.504–2.950 V，落在同型号参考 DTS 中 VCC regulator 的 2.496–3.008 V 范围内；不能把它误判成供电电压冲突。HOS DTBO 的 VCC/VCCQ/VCCQ2 最大电流记录为 800 mA，而同型号 Linux DTS 设为 750 mA，后续板级 DTS 应统一供电约束和 regulator load 语义，不能随手挑选其一。

**结论：UFS 是“驱动已有 + overlay/board power enable + PHY compatible 规范化”的高优先级板级移植项，不是缺少 SM8250 UFS 驱动。** 仍未确认 HOS runtime FDT 实际形态，也未做 UFS 初始化/读写测试。

参考：
- [Linux v6.18 SM8250 common DTS](https://github.com/torvalds/linux/blob/v6.18/arch/arm64/boot/dts/qcom/sm8250.dtsi)
- [Linux v6.18 Qualcomm UFS host driver](https://github.com/torvalds/linux/blob/v6.18/drivers/ufs/host/ufs-qcom.c)
- [Linux v6.18 QMP UFS PHY driver](https://github.com/torvalds/linux/blob/v6.18/drivers/phy/qualcomm/phy-qcom-qmp-ufs.c)
- [Linux v6.18 UFS Kconfig](https://github.com/torvalds/linux/blob/v6.18/drivers/ufs/host/Kconfig)
- [Linux v6.18 QMP PHY Kconfig](https://github.com/torvalds/linux/blob/v6.18/drivers/phy/qualcomm/Kconfig)
- [同型号 Linux UFS board DTS](https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts)

## 3. SPI / Huawei THP touch：框架在上游，设备接口不在上游

### 本机与上游差异

- HOS base FDT 的 `/soc/spi@880000` compatible 为 `qcom,spi-geni`，status 为 `ok`；Linux v6.18 SM8250 DTS 的同一 controller / spi14 使用 `qcom,geni-spi`，而上游 GENI SPI driver OF match 也是 `qcom,geni-spi`。板级 DTS 应以主线 node 为基础并采用主线匹配字符串。
- HOS entry 8 fragment@89 将 `huawei_thp@10` 加到该 SPI controller 下，compatible 为 `huawei,thp`，IRQ 编码为 GPIO39；触控父节点的 SPI 上限为 10 MHz，Novatek / Ilitek 子节点各有 16 MHz 限制。
- 同型号 Linux 参考 DTS 使用 `spi14`，native CS GPIO43、IRQ GPIO39、reset GPIO98，设备 compatible 为 `huawei,dby-w09-thp`，SPI 上限 16 MHz。
- 16 MHz 与 HOS 4.3 parent 10 MHz 并不一致。现阶段应以本机 HOS 4.3 父设备 10 MHz 作为保守基线；不能仅因另一个同型号 Linux port 设为 16 MHz 就直接提升频率。
- 同型号 `huawei-thp-lite.c` 的 OF match 是 `huawei,dby-w09-thp`，并非 HOS 的 `huawei,thp`。移植时需在 DTS 或驱动 OF match 里明确兼容关系。

这不是普通 SPI touchscreen driver 就能解决的工作。同型号项目的 shim 提供 `/dev/thp` 与 `/dev/input_mt_wrapper` ioctl ABI，以服务 Huawei `aptouch_daemon`。触控数据、笔状态、固件交互都涉及 Huawei 专有用户空间接口。ROUND5 EROFS BLOCKED，因此本项目还没有核实对应 daemon、AFE firmware 和校准文件。

参考：
- [Linux v6.18 SM8250 SPI14 DTS](https://github.com/torvalds/linux/blob/v6.18/arch/arm64/boot/dts/qcom/sm8250.dtsi)
- [Linux v6.18 GENI SPI driver](https://github.com/torvalds/linux/blob/v6.18/drivers/spi/spi-geni-qcom.c)
- [同型号 THP DTS / wiring](https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts)
- [同型号 THP shim](https://github.com/svesnav/linux-dby-w09/blob/main/touch/huawei-thp-lite.c)

## 4. Wi-Fi / Bluetooth：QCA6390 驱动族线索强，固件闭环仍缺失

HOS base FDT 有 CNSS node compatible `qcom,cnss-qca6390`，PCIe controller 位于 `/soc/qcom,pcie@1c08000`，SLIMbus Bluetooth child 为 `qcom,btfmslim_slave`。entry 8 的 vendor fragment 将 `bt_qca6390` 放入 `/vendor`，compatible 为 `qca,qca6390`。

同型号 Linux DTS 配置 QCA6390 PMU、WLAN_EN GPIO20、BT_EN GPIO21、PMIC supplies 和 UART6 Bluetooth。上游 ath11k PCI driver 有 QCA6390 PCI device ID `0x1101` 和 HW major 2 路径，ATH11K_PCI Kconfig 也存在。

限制：
- HOS 脱敏 FDT 没有提供足够 PCI vendor/device/subsystem ID，不能从 compatible 推断精确 silicon stepping。
- ROUND5 无可信 EROFS reader，QCA6390 firmware、board data、BT NVM、校准和设备专属地址尚未枚举。驱动在上游存在，不等于无线可用。
- 另一个公开项目 README 对 QCA6390/QCA6391 的表述有差异；本项目应优先依据本机 HOS compatible 和进一步可核验的 PCI/firmware 事实，不以 README 名称定芯片。

参考：
- [Linux v6.18 ath11k PCI driver](https://github.com/torvalds/linux/blob/v6.18/drivers/net/wireless/ath/ath11k/pci.c)
- [Linux v6.18 ath11k Kconfig](https://github.com/torvalds/linux/blob/v6.18/drivers/net/wireless/ath/ath11k/Kconfig)
- [同型号 QCA6390 DTS](https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts)
- [同型号 firmware preparation notes](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/firmware-preparation.md)

## 5. Display / panel / backlight：配置候选很多，不能仅按名字认定活动面板

entry 8 同时含多个 panel profile：
- `dual_nt36523` C-PHY profile；
- `lcd_kit_debussy_110_20d_10p9_qcom` / `110_20d`；
- `110_a09`、`190_20d`、`290_20d`；
- `csot_nt36523_10p9_1080p_video_default`。
并有 primary/secondary DSI fragments、TPS65132、Huawei RT8555/LP855x backlight-compatible nodes，以及 5.5 V `display_panel_avdd` regulator。

fragment target 已解析到 MDP/DSI 主控和相关 I2C/pinctrl 节点，但本轮结果仍不足以确认哪一组 profile 最终被选中、哪些 profile 是 fallback/备选。svesnav 同型号 DTS 注释采用 `lcd_kit_debussy_110_20d_10p9_qcom`，并提供 VCI/IOVCC/TPS65132/RT8555/Reset 的板级配置；这是一条有价值的同型号参考路径，不是 HOS 4.3 已确认的唯一活动 profile。

Linux v6.18 有 NT36523 panel driver，但 generic NT36523 family 不足以证明其 init sequence、双 DSI C-PHY、供电顺序和 Huawei 背光时序可直接用于 DBY-W09。同型号 Linux 项目提供了独立 `huawei,dby-w09-panel` driver 与 panel command header，说明专用面板适配仍是现实工作。

**结论：面板家族/候选配置已对应；活动 profile 与 GPIO/pinctrl 仍需本机证据；不能直接套 Xiaomi/其它 NT36523 panel driver。**

参考：
- [同型号 panel DTS](https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts)
- [同型号 Huawei panel driver](https://github.com/svesnav/linux-dby-w09/blob/main/panel/panel-huawei-dby-w09.c)
- [同型号 RT8555 backlight driver](https://github.com/svesnav/linux-dby-w09/blob/main/panel/rt8555-backlight.c)
- [Linux v6.18 NT36523 panel driver](https://github.com/torvalds/linux/blob/v6.18/drivers/gpu/drm/panel/panel-novatek-nt36523.c)

## 6. Audio / SmartPA：上游 codec 存在，Huawei SmartPA 不能按 generic codec 处理

HOS entry 8：
- fragment@46 指向 Bolero audio macro / SoundWire 链，包含 WCD938x codec、RX/TX macro/slave 和四个 WSA881x 节点。
- HOS WCD codec compatible 为 `qcom,wcd938x-codec`。
- fragment@121 指向 I2C controller，含 12 个 Huawei SmartPA 节点：0x30–0x33（chip_model=`06-01`）、0x34–0x37（`01-02`）、0x50–0x53（`03-01`）。这些编码保持为 Huawei opaque identifier，不解码成芯片型号。
- fragment@125 的 `/hw_adsp_misc` 下另有 `huawei,tfa_smartamp` 与 `huawei,awinic_smartamp` 兼容节点。

上游 Linux v6.18 WCD938x codec driver 接受 `qcom,wcd9380-codec` 与 `qcom,wcd9385-codec`，并非 HOS 的 `qcom,wcd938x-codec` 字符串；同型号 Linux DTS 使用 `qcom,wcd9380-codec`。因此板级移植需规范 compatible 或扩展匹配表。上游也有 WSA881x SoundWire codec driver。

同型号 Linux 参考项目将 I2C 0x34–0x37 四个 SmartPA 识别为四颗 NXP TFA9874，并通过 Primary TDM（四路 slot、6.144 MHz）输出；但本机 HOS 的 `01-02` 并非公开 TFA9874 part number。可判为**地址/数量强匹配**，不能判为 HOS 属性已直接证实 TFA9874。公开项目说明 TFA9874 没有通用上游 driver，需要用户空间 I2C 初始化或专有驱动，并依赖未公开的原厂 XML 配置表；现有短测也未证明长时间 speaker protection。

**结论：WCD938x/WSA881x 有上游基础；SmartPA、TDM routing、初始化表和 Huawei audio userspace 是定制工作。**

参考：
- [Linux v6.18 WCD938x driver](https://github.com/torvalds/linux/blob/v6.18/sound/soc/codecs/wcd938x.c)
- [Linux v6.18 WSA881x driver](https://github.com/torvalds/linux/blob/v6.18/sound/soc/codecs/wsa881x.c)
- [同型号 Primary TDM patch](https://github.com/svesnav/linux-dby-w09/blob/main/sound/sm8250-pri-tdm.py)
- [同型号 TFA9874 notes](https://github.com/youzjuzi/dby-w09-linux/blob/main/drivers/dby-tfa9874/README.md)
- [同型号 audio capture notes](https://github.com/youzjuzi/dby-w09-kernel/blob/main/docs/audio-capture.md)

## 7. Camera：上游 sensor driver 已有，HOS 4.3 仍未给出本轮可确认的 sensor 型号

entry 8 camera fragments：
- fragment@131 → `/soc/qcom,cci@ac4f000`，包含通用 `qcom,cam-sensor0`、actuator、EEPROM。
- fragment@132 → `/soc/qcom,cci@ac50000`，包含通用 `qcom,cam-sensor1`、EEPROM。
- fragment@129 提供 camera GPIO/pinctrl 类信息；fragment@130 还有 camera flash / resource manager。
- 当前 ROUND7 脱敏属性 inventory 对本机 sensor 子树仅保留通用 Qualcomm camera compatible / status / pinctrl names，无法由此确认 sensor I2C 地址和型号。

同型号 Linux 参考 DTS / camera.dtsi 识别为：
- rear OV13B10，CCI0 I2C 0x36，CSIPHY0，MCLK GPIO94，reset GPIO93；AVDD 2.8 V、DVDD 1.2 V 和 I/O 1.8 V rail。
- front Hynix Hi846，CCI1 I2C 0x21，CSIPHY2，MCLK GPIO96，reset GPIO78；同样需对应 AVDD/DVDD/I/O rail。
- rear autofocus DW9714，CCI0 I2C 0x0c，VDD 2.856 V，GPIO154 powerdown。
- Linux v6.18 有 `ov13b10` 和 `hynix,hi846` driver；OV13B10 upstream driver要求 19.2 MHz external clock。参考 port 对 OV13B10 配 19.2 MHz，但 front Hi846 设 24 MHz。

**结论：camera pipeline 的上游基础存在，sensor/actuator/EEPROM/CSI/clock/rail DT 仍需逐项按本机 FDT 补齐。** rear OV13B10/front Hi846/DW9714 属同型号移植项目识别结果，不应伪装成本轮 HOS4.3 FDT 已直接导出的芯片型号。

参考：
- [Linux v6.18 OV13B10 driver](https://github.com/torvalds/linux/blob/v6.18/drivers/media/i2c/ov13b10.c)
- [Linux v6.18 Hi846 driver](https://github.com/torvalds/linux/blob/v6.18/drivers/media/i2c/hi846.c)
- [同型号 camera DTS](https://github.com/svesnav/linux-dby-w09/blob/main/camera/camera.dtsi)

## 8. USB-C / DisplayPort：上游 mux/retimer drivers 存在，但 compatible 需要转换

本机 HOS：
- base FDT 的 FSA4480 节点位于 `/soc/i2c@884000/fsa4480@43`，compatible `qcom,fsa4480-i2c`。
- entry 8 fragment@66 指向同一个 `/soc/i2c@884000` I2C controller，`redriver@1c` compatible 只写 `onnn,redriver`。
- entry 8 fragments 同时涉及 USB/SS PHY、QMP DP display 和 PM8150B Type-C / PD PHY。

上游 Linux v6.18：
- FSA4480 mux driver OF match 为 `fcs,fsa4480`，不含本机 HOS 字符串 `qcom,fsa4480-i2c`。
- NB7VPQ904M redriver driver OF match 为 `onnn,nb7vpq904m`，不含 HOS 泛化字符串 `onnn,redriver`。
- QMP Combo PHY、DWC3、Type-C framework 和 DP bridge/mux 的上游基础存在。

同型号 Linux port 将 I2C 0x43 配成 `fcs,fsa4480`，并把 0x1c redriver 识别为 `onnn,nb7vpq904m`。其中 FSA4480 的芯片/地址对应本机更直接；NB7VPQ904M 的具体型号来自同型号公开 port，而不是本机 HOS 的泛化 compatible，故仍保留来源区分。

**结论：主线驱动存在；需要把 HOS vendor compatible 归一到上游绑定，并确认 USB-C / DP lane endpoint、orientation、redriver path 和供电属性完整一致。**

参考：
- [Linux v6.18 FSA4480 driver](https://github.com/torvalds/linux/blob/v6.18/drivers/usb/typec/mux/fsa4480.c)
- [Linux v6.18 NB7VPQ904M driver](https://github.com/torvalds/linux/blob/v6.18/drivers/usb/typec/mux/nb7vpq904m.c)
- [Linux v6.18 Type-C mux Kconfig](https://github.com/torvalds/linux/blob/v6.18/drivers/usb/typec/mux/Kconfig)
- [同型号 USB-C / DP DTS](https://github.com/svesnav/linux-dby-w09/blob/main/usb/typec.dtsi)

## 9. 目前可复用与不可直接复用的范围

| 子系统 | Linux v6.18 上游基础 | DBY-W09 专属部分 | 当前结论 |
|---|---|---|---|
| SM8250 / GCC / RPMh / pinctrl / interconnect | 有 | Huawei board DTS、供电、reserved memory、GPIO | 上游 SoC 基础可复用 |
| UFS Host | 有，`qcom,ufshc` 可匹配 | enable、rails、clock/reset/power-domain | 高优先级；PHY compatible 要规范化 |
| QMP UFS PHY | 有 SM8250 专用配置 | HOS vendor compatible 与主线字符串映射 | 上游 PHY 存在；DTS 需转换 |
| GENI SPI | 有 | controller compatible 归一、SPI14 CS/IRQ/reset pinctrl | 上游 controller 可用；触控设备另需 shim |
| Huawei THP | 通用 SPI/input 有 | Huawei THP shim、daemon ABI、firmware、频率/中断配置 | 专有移植项 |
| QCA6390 Wi-Fi/BT | ath11k PCI family 有 | CNSS/power/GPIO/UART、board data、firmware、BT NVM | 驱动基础有；运行依赖未闭环 |
| Display / NT36523 family | 有部分 generic panel/DSI | Huawei dual DSI C-PHY profile/init commands/backlight/rails | 专属 panel integration |
| WCD938x / WSA881x | codec/SoundWire drivers 有 | Huawei audio routes / compatible / DSP graph | 上游基础可复用，需板级调试 |
| TFA9874 SmartPA | 无确认的通用上游 driver | I2C config/XML、Primary TDM、私有 tuning/protection | 定制部分较大 |
| OV13B10 / Hi846 | 两个 sensor driver 都有 | CCI、CSIPHY、MCLK、reset、rails、actuator/EEPROM | 上游 sensor driver 可用，板级链需本机数据 |
| FSA4480 / NB7VPQ904M | 两个 mux/redriver driver 有 | HOS compatible 映射、Type-C/DP endpoints | 驱动有，compatible/拓扑需转换 |

## 10. 移植风险排序与剩余证据缺口

按目前静态资料，建议优先级：

1. **UFS + boot/rootparam + 板级电源链**：UFS driver 存在，entry 8 overlay 有明确启用；需确认主线 DTS 兼容字符串、供电 phandle、所有 pinctrl/clock/reset，并保留 ABL 的 `/rootparam` 身份契约。
2. **目标平台选择与 boot model**：ROUND6 已确认 `android17-6.18` branch HEAD 为 6.18.33，但不是已发布认证的 GKI 6.18.33；Android 12 / API 31 与该 Android 17 branch 不属于 Google 官方兼容矩阵组合。ACK/KMI 和 boot header v2/独立 ramdisk兼容不可由 mainline DTS 报告替代。
3. **Display / THP**：都是功能关键且涉及 Huawei 私有 command/ABI；活动 panel profile、touch pinctrl/CS/reset/频率仍需进一步对照。
4. **Wi-Fi / BT**：driver family 线索明确，但 firmware、board data、BT NVM 与 device-specific address 因 ROUND5 EROFS BLOCKED 而未知。
5. **Audio / Camera / USB-C DP**：有相当多上游基础，但还有 Huawei audio config、camera sensor 子树、Type-C compatible 和 endpoint 映射工作。

下一轮最有价值的本地只读补充，不是重复 PATH 检测或再跑完整 FDT inventory，而是从已经存在的 `dtb_work` 文件中补出以下脱敏字段：
- entry 8 触控 fragment 的 SPI native CS / pinctrl state / reset / IRQ mapping；区分 10 MHz parent 和 16 MHz child；
- panel GPIO 6/10/11/12/38 对应的完整 pinctrl state、DSI 主从端和 profile fragment 的引用关系；
- UFS PHY supply phandle、reset/clock/power domain 映射，以及 fragment 63/64 的供电 regulator target；
- CNSS/QCA6390 WLAN_EN / BT_EN 和 rail phandle；
- camera sensor0/1 的 sensor name/compatible、I2C address、reset、MCLK、supply names、CSIPHY/CSID endpoints；不导出 EEPROM/calibration 内容；
- USB Type-C FSA4480/redriver/QMP/DP endpoint 和 supply phandle。
只需要输出纯文本脱敏 CSV/摘要，不需要新提取固件、不需要 EROFS、不需要 build 或设备操作。

## 11. 项目边界与当前状态

- ROUND5 EROFS 内容层继续保持 BLOCKED；旧 4.19 vendor modules、vermagic、depends、symbols、VINTF 和私有 firmware 仍 UNKNOWN。
- 不得假设旧 4.19 vendor module 可装入 ACK 6.18.33；不应以主线 v6.18 match table 代替实际 `android17-6.18` 分支逐文件核对。
- 本报告不是 ACK 6.18.33 build config，也不是可直接提交的 DTS patch。
- 本报告不证明 UFS/显示/触控/音频/相机/Wi-Fi/USB 任何设备已在新内核上工作。
- 未编译、未刷机、未解锁、未连接设备、未写分区、未 root、未加载模块、未安装未知工具。
- PR #1 仍为 Draft；本报告写入 main 不会修改或合并该 PR。
