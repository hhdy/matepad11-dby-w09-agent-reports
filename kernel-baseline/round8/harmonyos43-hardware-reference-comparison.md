# DBY-W09 HOS 4.3 DTB/DTBO 与同型号 Linux 参考树对照

核验日期：2026-11-24  
设备：Huawei MatePad 11 DBY-W09，Qualcomm KONA / SM8250 v2.1  
对照来源：
- 本项目 ROUND3 / ROUND7 的 HarmonyOS 4.3 boot FDT / DTBO 脱敏报告。
- svesnav 的 DBY-W09 Linux 7.0.14 DTS、rootparam DTBO、THP driver、USB/camera/audio 片段。
- youzjuzi 的 DBY-W09 Linux 7.2.10 设备树/音频资料。
- Linux v6.18 mainline SM8250 DTS、驱动 Kconfig 与源码。
  
范围说明：这是静态源码和 FDT 属性对照，不是新内核编译或设备启动测试。外部 Linux 项目部分基于 HarmonyOS 4.2，HOS 4.3 本地 FDT 是本机事实来源。外部项目的单机功能状态属于维护者证据，不等于第三方独立验证。

## 1. 总结

ROUND7 已经足以确认：DBY-W09 与公开同型号 Linux 移植项目在 SM8250 revision、Huawei board-id、面板系列、THP 触摸、QCA6390 配置、WCD938x 音频链、摄像头资源节点等方面高度对应。

但还不能把外部 DTS 直接复制进 GKI 6.18.33。当前最关键的差异与未知是：
1. HOS 4.3 boot FDT 中 UFS host 和 UFS PHY 两个节点均标记 disabled；同型号 Linux board DTS 会主动启用并补齐电源轨。需先确认 DTBO overlay 是否改变这两个节点的状态，以及 HOS 内核实际使用的 FDT。
2. HOS 4.3 DTBO 包含多个 Debussy/NT36523 面板 profile；外部 Linux 项目选择 110_20d profile。虽然本机存在同名 profile，但仍需解析 fragment target，确认哪个 profile 实际绑定显示主控。
3. HOS 4.3 的 Huawei THP 节点 IRQ 为 GPIO39，外部 THP driver 也使用 GPIO39；但 SPI bus、片选、复位 GPIO 和有效传输频率仍需解析 pinctrl/fragment target 后核对。
4. HOS 4.3 的蓝牙/无线 FDT 使用 QCA6390-compatible 命名；这对 QCA6390 driver family 是强证据，但没有 PCI device/subsystem ID，不能把物理芯片精确型号标成最终确认。
5. HOS 4.3 DTBO 有 WCD938x/WSA881x SoundWire 节点，也有多组 Huawei SmartPA I2C 节点；其中 @0x34–0x37 四个节点与外部项目四颗 TFA9874 放大器的 I2C 地址/数量吻合，但本机 smartpa 的 chip_model 字段仍是 Huawei 私有编码，不能据此单独证明其芯片一定为 TFA9874。
6. 摄像头 DTBO 仅提供通用 qcom,cam-sensor / actuator / EEPROM 节点；外部项目识别后置 OV13B10、前置 Hi846、DW9714，但本机脱敏清单尚未导出这些子树的具体 sensor compatible / GPIO / clock / regulator。

最重要的下一步不是全量重做 DTB 清单，而是从 DTBO entry 8 解析所有 fragment target -> HOS 4.3 base FDT 节点路径。ROUND8 本地任务专门处理这一小段缺口。

## 2. 强匹配：SoC 与 Huawei board identity

| 字段 | HOS 4.3 ROUND3/7 | 同型号 Linux 参考 | 分类 |
|---|---|---|---|
| SoC compatible | qcom,kona | qcom,sm8250（主线板级树）及 KONA/SM8250 common DTS | MATCH（同 SoC 系列；字符串使用层级不同） |
| MSM ID | [356, 131073] = SM8250 v2.1 | QCOM_ID_SM8250 0x20001 | MATCH |
| Base board-id | [0,0] | Huawei base DTS 为 [0,0] | MATCH |
| DTBO board-id | entry 8: 8298 = 0x206a | svesnav rootparam overlay 为 0x206a | MATCH |
| Board identity | entry 8 fragment overlay 写入 boardid [8,2,9,8]、DBY_W09_VG、SH1DBSLM | svesnav DTS / overlay 写同一组字段 | MATCH（值一致） |
| Overlay target | ROUND7 矩阵没保留 target path；overlay 无直系 /rootparam 节点 | svesnav fragment@0 target=&rootparam | NEEDS_TARGET_RESOLUTION |

细节：
- ROUND7 的 rootparam_present=False 只表示 overlay FDT 本身没有名为 /rootparam 的根路径节点。
- entry 8 的 fragment@143/__overlay__ 确实含有 qcom,boardid=[8,2,9,8]、qcom,board_name="DBY_W09_VG"、hardware_version="SH1DBSLM" 等字段。
- 所以“没有 /rootparam 节点”不能解读为“没有写入 rootparam 身份”。overlay 使用 fragment 机制。
- 但 fragment@143 的 target phandle 尚未解析回基树路径；ROUND8 需确认它是否指向 /rootparam。不要仅因字段值相同便跳过 target 验证。

参考：
- [本项目 ROUND3 summary](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round3/round3_summary.json)
- [本项目 ROUND7 DTBO matrix](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round7/dtbo_board_rootparam_matrix.csv)
- [svesnav Huawei board DTS](https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts)
- [svesnav rootparam overlay](https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso)

## 3. UFS / QMP PHY：驱动有了，板级激活尚需核实

HOS 4.3 的确定 boot FDT candidate 0 中：
- /soc/ufshc@1d84000 compatible 为 qcom,ufshc，保留 reg、interrupt、PHY、clock、reset 等描述；status="disabled"。
- /soc/ufsphy_mem@1d87000 具有 ref/ref_aux clock 描述；status="disabled"。
- boot FDT candidate 1/2 也保留相同的 disabled 状态。

Linux v6.18 的 SoC common DTS 中，SM8250 的 ufs_mem_hc / ufs_mem_phy 本来就以 disabled 作为 SoC 默认值。这是 SoC common DTS 的默认模式，不代表主线没有 UFS 驱动。Linux v6.18 已有 SCSI_UFS_QCOM 和 PHY_QCOM_QMP_UFS。

同型号 svesnav Huawei board DTS 则明确：
- &ufs_mem_hc → status="okay"；
- VCC 使用 PM8150L L17 3.0V；
- VCCQ 使用 PM8150L L6 1.2V；
- VCCQ2 使用 PM8150 S4 1.8V；
- &ufs_mem_phy → status="okay"；
- PHY analog supply 使用 PM8150 L5 0.88V，PLL supply 使用 PM8150 L9 1.2V。

**分类：DIFFERENT_VALUE / BOARD ENABLE REQUIRED（但 HOS 实际运行时 FDT 尚未确认）。**

重要限制：
- boot.img 中的 base FDT 是启动镜像内的候选树，不必然等于 ABL 最后交给内核的合成 FDT。
- ROUND7 的 DTBO curated inventory 未显示 UFS target path / UFS overlay property；这不能代替对全部 9 个 DTBO fragment target 的检查。
- 如果 HOS 4.3 最终运行 FDT 中 UFS 仍 disabled，而系统实际能从 UFS 运行，则还需查明华为 vendor kernel 的实际启用方式、运行时 tree 与启动阶段修改，不能只看 boot.img 中的 FDT。
- GKI/ACK 上启用 UFS 前，应确认 DTBO target、供电轨、PHY reset/clock/power-domain、UFS gear 与 regulator load 的完整链路；不能只把 status 改成 okay。

来源：
- [Linux v6.18 SM8250 common DTS](https://github.com/torvalds/linux/blob/v6.18/arch/arm64/boot/dts/qcom/sm8250.dtsi)
- [Linux v6.18 Qualcomm UFS Kconfig](https://github.com/torvalds/linux/blob/v6.18/drivers/ufs/host/Kconfig)
- [Linux v6.18 Qualcomm QMP PHY Kconfig](https://github.com/torvalds/linux/blob/v6.18/drivers/phy/qualcomm/Kconfig)
- [svesnav Huawei UFS board configuration](https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts)
- [linux-msm SM8250 MTP UFS reference](https://github.com/CodeLinaro-mirror/la_kernel_platform_msm-kernel/blob/sm8250/arch/arm64/boot/dts/qcom/sm8250-mtp.dtsi)

本报告纠正上一轮一处引用：Linux NT36523 panel Kconfig 的资料支持“NT36523 通用 panel driver 举例是 Xiaomi BOE panel”，不支持 UFS 结论。UFS 结论来自以上 SM8250 DTS / UFS Kconfig / 同型号 Huawei DTS 源码。

## 4. Display / panel / backlight

HOS 4.3 DTBO entry 8 包含：
- qcom,mdss_dsi_nt36523_wqxga_video_cost，compatible dual_nt36523，有 qcom,panel-cphy-mode。
- lcd_kit_debussy_110_20d_10p9_qcom，compatible 110_20d，有 C-PHY mode 标记。
- 另外还有 110_a09、190_20d、290_20d、csot_nt36523_10p9_1080p_video_default 等 panel profile。
- 有 primary/secondary DSI display fragment。
- 有 TPS65132 (ti,tps65132)。
- 有 Huawei backlight-compatible huawei,hw_lp855x 与 huawei,hw_rt8555，相关 fragment 中 status 为 okay。
- 5.5V fixed regulator display_panel_avdd 存在。

svesnav 同型号 DTS 注释选择 lcd_kit_debussy_110_20d_10p9_qcom；panel chain 为 VCI=PM8150L L11 3.2V、IOVCC=GPIO6 load switch 1.8V、TPS65132 VSP/VSN on GPIO11/12、panel reset GPIO38、RT8555 enable GPIO10；同一 QUP I2C11 bus。

**分类：PANEL FAMILY / PROFILE NAME MATCH；BOARD VALUES PARTIAL MATCH。**
- HOS 4.3 里确实存在 110_20d 和 dual NT36523 C-PHY panel profiles。
- 外部同型号 Linux DTS 指定 110_20d，提供同一面板供电/背光线索。
- HOS 4.3 含多个 profile，ROUND7 尚未解析 fragment target，故不能认定 110_20d 是启动时最后选择的唯一 profile。
- 主线 Linux v6.18 DRM_PANEL_NOVATEK_NT36523 面向特定 NT36523 panel variant（Kconfig 举例 Xiaomi Mi Pad 5/5 Pro BOE panel），不能仅凭 NT36523 family 直接套用 Xiaomi panel driver。DBY-W09 需要 Huawei 专属初始化命令、双 DSI/C-PHY、供电顺序及背光处理。

来源：
- [svesnav Huawei DTS](https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts)
- [Linux v6.18 Novatek NT36523 panel Kconfig](https://github.com/torvalds/linux/blob/v6.18/drivers/gpu/drm/panel/Kconfig)
- [Linux v6.18 Novatek NT36523 panel driver](https://github.com/torvalds/linux/blob/v6.18/drivers/gpu/drm/panel/panel-novatek-nt36523.c)

## 5. Touch / SPI / Huawei THP

HOS 4.3 DTBO entry 8:
- SPI controller node spi@880000 status okay。
- child huawei_thp@10 compatible huawei,thp。
- touch interrupt 编码为 GPIO39。
- parent node SPI max frequency 10MHz。
- children thp_input_dev / thp_pen_input_dev 使用 Huawei compatible。
- Novatek 与 Ilitek subnodes 有 16MHz SPI max frequency。
- 设备属性启用向 firmware 发送 BT 状态和吸附状态。

svesnav 同型号 Linux DTS：
- 触摸使用 spi14，native CS GPIO43、IRQ GPIO39、reset GPIO98。
- SPI frequency 16MHz。
- compatible huawei,dby-w09-thp。
- 配套 huawei-thp-lite.c 提供 /dev/thp 和 /dev/input_mt_wrapper 用户空间 ABI，以匹配 Huawei aptouch_daemon 的 ioctl 与数据结构。

**分类：MATCH（Huawei THP family + IRQ39）；DIFFERENT_VALUE / NEEDS_MAPPING（SPI frequency and controller/CS/reset wiring）。**

这一对照说明上游通用 SPI / input framework 并不足够；要么移植同型号 THP shim，要么重新实现经过确认的 Huawei userspace ABI。当前 EROFS BLOCKED，匹配 AFE firmware / daemon / calibration 仍未被本项目枚举。不能把外部项目的 4.2 私有 touch inputs 假设为本项目 4.3 一致。

来源：
- [svesnav Huawei THP driver](https://github.com/svesnav/linux-dby-w09/blob/main/touch/huawei-thp-lite.c)
- [svesnav Huawei DTS](https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts)
- [youzjuzi firmware preparation](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/firmware-preparation.md)

## 6. WLAN / Bluetooth

HOS 4.3 boot FDT candidate 0：
- CNSS node compatible qcom,cnss-qca6390。
- PCIe controller path qcom,pcie@1c08000，compatible qcom,pci-msm。
- SLIMbus qca6390 child compatible qcom,btfmslim_slave。
HOS 4.3 DTBO entry 8：
- Bluetooth node bt_qca6390 compatible qca,qca6390。
- qcom,qbt_handler fragment disabled。

svesnav 同型号 board DTS 明确使用 QCA6390 PMU、UART6 QCA6390 BT 和 GPIO20/21 enable，且通过 PM8150/PM8150L 多条电源轨供电；youzju 同型号的 firmware prep 亦按 QCA6390 固件与设备校准数据整理。

**分类：MATCH（QCA6390 driver family / CNSS compatible）。**
- 但本机 FDT / 公开资料没有足以确认 PCI vendor/device/subsystem ID 的字段，不能仅凭 compatible 推断最终 silicon stepping 或 board calibration。
- 外部项目与 CoWave README 存在 QCA6390/QCA6391 名称差异；本机 4.3 的 QCA6390-compatible 节点是更直接的证据，但仍需 PCI ID 或对应 vendor firmware identity 闭环。
- Wi-Fi 的 board data、BT NVM、MAC/BD address 都属于设备专有输入；不要从其它设备复制，也不要公开。

来源：
- [svesnav Huawei DTS](https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts)
- [youzjuzi firmware preparation](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/firmware-preparation.md)
- [Linux ath11k QCA6390 support](https://github.com/torvalds/linux/blob/v6.18/drivers/net/wireless/ath/ath11k/core.c)

## 7. Audio / SmartPA / SoundWire

HOS 4.3 DTBO entry 8 contains:
- WCD938x codec / TX slave / RX slave nodes under audio macro / SoundWire.
- Four WSA881x SoundWire nodes.
- Huawei SmartPA nodes at I2C child addresses 0x34–0x37, four nodes share private chip_model=01-02.
- Additional SmartPA alternatives 0x50–0x53 (03-01) and 0x30–0x33 (06-01), plus huawei,smartpakit controller node.

svesnav same-model DTS explicitly identifies four NXP TFA9874 devices at I2C3 addresses 0x34–0x37, connected to Primary TDM on GPIO138–141, 6.144MHz. It also wires WCD938x and uses a four-channel TDM patch.
youzjuzi has a separate TFA9874 driver project. Its README states four revision 0x0c74 amplifiers on Primary TDM0; four private original XML config tables are required and not distributed. Its later limited single-tablet short-session evidence reports all four amplifiers played audio, but no speaker protection algorithm exists.

**Classification: strong topology/address match, exact HOS 4.3 SmartPA silicon mapping UNKNOWN.**
- Four local smartpa nodes at 0x34–0x37 match the four external TFA9874 I2C addresses.
- Local chip_model=01-02 is a Huawei private identifier, not a public TFA9874 part number. Do not decode it by guess.
- Presence of WSA881x nodes could describe a different audio configuration or coexist with the SmartPA topology; target mapping and actual selected path need round8 overlay resolution.
- Upstream WCD938x/WSA framework exists, but TFA9874 support is not built into a general upstream board driver; same-model projects supply board-specific user-space I2C configuration or an out-of-tree module and Primary TDM patch.
- Private TFA XML tables, ADSP firmware, tuning and protection algorithm remain vendor dependencies.

Sources:
- [HOS 4.3 ROUND7 property inventory](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round7/dtb_property_inventory.csv)
- [svesnav audio TDM patch](https://github.com/svesnav/linux-dby-w09/blob/main/sound/sm8250-pri-tdm.py)
- [youzjuzi TFA9874 driver README](https://github.com/youzjuzi/dby-w09-linux/blob/main/drivers/dby-tfa9874/README.md)
- [youzjuzi audio board evidence](https://github.com/youzjuzi/dby-w09-kernel/blob/main/docs/audio-capture.md)

## 8. Camera / USB-C / DP

Camera:
- HOS 4.3 DTBO8 has qcom,cam-sensor0, qcom,cam-sensor1, qcom,actuator, qcom,eeprom0/1, camera flash nodes and CAMSS/CSIPHY/CSID base resources.
- svesnav DTS identifies rear OV13B10 + DW9714 and front Hi846; provides detailed rails, MCLK, reset GPIOs, CCI addresses and CSIPHY routes.
- ROUND7 public curated inventory did not retain the sensor child compatibles/clock/reset/rail values in enough detail to match them. Therefore sensor identification in HOS 4.3 remains UNKNOWN, although the generic camera node topology matches.

USB-C / DP:
- HOS 4.3 boot FDT has FSA4480 I2C switch at /soc/i2c@884000/fsa4480@43 compatible qcom,fsa4480-i2c.
- HOS 4.3 DTBO has PM8150B USB PD PHY / SMB5 USB/type-C nodes.
- svesnav adds Type-C PD connector, FSA4480 mux, NB7VPQ904M retimer, QMP combo PHY and DP endpoint graph.
- Classification: FSA4480/PMIC USB framework MATCH; retimer/DP lane topology and endpoint graph NEEDS_TARGET_RESOLUTION.

Sources:
- [svesnav camera DTS](https://github.com/svesnav/linux-dby-w09/blob/main/camera/camera.dtsi)
- [svesnav USB-C DTS](https://github.com/svesnav/linux-dby-w09/blob/main/usb/typec.dtsi)

## 9. Driver portability to ACK 6.18.33

| Component | v6.18 upstream base | Board-specific work | Current status |
|---|---|---|---|
| SM8250 SoC / GCC / RPMh / pinctrl / interconnect | Present | Huawei device tree, power rails, reserved memory | Public base reusable; local board DTS required |
| UFS host / QMP UFS PHY | Present | Enable, UFS rail mapping, lane/clock/reset/power-domain | High priority; runtime/overlay status unresolved |
| Adreno 650 / DRM MSM | Present | Huawei ZAP firmware, memory carveout and GPU OPP/power | Driver base reusable; firmware/private data dependency |
| ath11k / QCA6390 PCIe | Present | CNSS, power rails, enable GPIOs, calibration / firmware path | Strong local-compatible evidence; exact PCI IDs still UNKNOWN |
| NT36523 display | Generic driver exists | Huawei dual DSI C-PHY panel profile/init commands, power timing, RT8555 | Requires Huawei-specific integration; not a Xiaomi panel drop-in |
| Huawei THP touch | SPI/input framework exists | huawei-thp shim and Huawei user ABI/firmware | Dedicated port/ABI work |
| WCD938x / SoundWire / Q6 | Public bases exist | Huawei WCD938x board routes, TDM and SmartPA | Board-specific patches; private tuning data |
| TFA9874 SmartPA | No general in-tree TFA9874 driver claimed in reference project | I2C initialization, Primary TDM slot mapping, private tables | custom driver/user-space integration |
| Camera | OV13B10/Hi846/DW9714 mainline support exists | CSI topology, sensor child configs, clocks/rails/MCLK | Need local sensor subtree details |
| USB-C / DP | QMP Combo PHY / DWC3 / Type-C frameworks exist | PMIC PD, mux/retimer graph, lane orientation | Need local fragment target mapping |

**KMI caveat:** This table is about mainline v6.18 driver presence and same-model DTS references, not Android KMI binary compatibility. ROUND5 EROFS BLOCKED means no old .ko list, vermagic, dependency/symbol report or VINTF is available. No existing 4.19 vendor module should be assumed loadable in ACK 6.18.33.

**GKI/platform caveat:** Prior ROUND6 research says Android12 + android17-6.18 is outside Google's official compatibility matrix. An ACK kernel packaged with old header v2/ramdisk as custom legacy boot is not automatically a certified GKI image.

## 10. ROUND8 only remaining local evidence task

Current ROUND7 inventory omitted some critical overlay properties, especially target / target-path and full pinctrl/sensor child details. ChatGPT cannot access the existing local FDT binary work copies. The only local follow-up should be:

1. For DTBO entry 8 (board-id 0x206a), map every fragment@N target phandle or target-path to the matching base FDT node path using deterministic boot FDT candidate 0.
2. Confirm whether fragment@143 targets /rootparam.
3. Confirm whether any overlay fragment changes /soc/ufshc@1d84000 or /soc/ufsphy_mem@1d87000 status or rails.
4. Map actual targets of panel fragments (DSI display primary/secondary and candidate panel profile fragments), THP fragment, QCA/PCIe fragments, audio fragments, camera sensor fragments, USB/DP fragments.
5. Resolve pinctrl phandles for touch IRQ/CS/reset, Wi-Fi/BT enable, panel GPIO6/10/11/12/38, UFS reset and USB/DP mux where present; report signal-to-GPIO mapping, no address/private payload.
6. For camera sensor0/1, export only compatible, sensor name/model, I2C address, reset GPIO, MCLK, rails, CSIPHY/CSID endpoint; redact physical addresses and private calibration payloads.
7. For SmartPA nodes, preserve chip_model values only as opaque Huawei identifiers; do not decode to TFA part number.

The local report must remain text-only and redacted. No re-extraction, no parser rewrite, no EROFS, no module analysis, no WSL, no build, no device connection, no write.

Task file: AGENT_TASK_ROUND8.md.

## 11. Overall project boundary

This comparison does not show a successful GKI build or device boot. It narrows the work:
- UFS is a board enable/power integration task, not a missing Qualcomm driver.
- Display and touch require Huawei-specific command/ABI adaptation.
- Wi-Fi uses the QCA6390-compatible driver family, but PCI IDs/calibration still need confirming.
- Audio has clear WCD938x + SmartPA structure; private chip/tuning identity is unresolved.
- The boot chain remains legacy header v2 + independent ramdisk + Huawei board overlay semantics; GKI-compliant header v3/v4/vendor_boot is a separate platform integration question.
- Vendor/ODM EROFS content, modules, firmware and VINTF remain BLOCKED from ROUND5.

No firmware binary, module, DTB/DTBO blob, FDT source dump, private configuration, full local SHA, serial/MAC, token or personal path was uploaded or used. No build, flash, unlock, device connection or partition write took place.
