# ROUND10 — DBY-W09 / ACK android17-6.18 板级 DTS 兼容性与迁移评估

日期：2026-11-24  
范围：ROUND9 本机事实核验 + Google kernel/common 的 SM8250 / 驱动 / binding 对照  
性质：静态源码审查与迁移建议；不是可直接编译的 DTS patch，也不是启动验证报告。

## 1. 结论摘要

ROUND9 四份报告已从 firmware-audit-v1 分支实际读取，文件完整：GPIO/phandle CSV、camera inventory CSV、panel/UFS 说明和 summary JSON。summary 标记 COMPLETE。报告正确保留了 camera model、active panel、redriver model 等 UNKNOWN，没有把外部 Linux 项目的推断覆盖成本机值。

核心判断：

1. SM8250 UFS Host、QMP UFS PHY、GENI SPI、FSA4480、WCD938x/WSA881x、ath11k、部分 camera 和 Type-C 驱动在 Linux / ACK 相关源码中有基础；主要缺口是 board DTS、电源/时钟/端点闭环及 Huawei 私有驱动/配置。
2. 不能按“把 HOS compatible 改成一个主线字符串”简单处理全部子系统。UFS PHY、GENI SPI、FSA4480 有直接的主线映射；WCD938x、THP、QCA639x、panel 和 redriver 必须保留型号/ABI 不确定性。
3. ROUND9 的 UFS 供电关系闭环是很有价值的板级事实，但两个 Qualcomm downstream 属性不能不经驱动检查就原样带入 ACK：qcom,vccq-parent-supply 是下游扩展；qcom,vddp-ref-clk-supply 应按上游 QMP PHY 的 supply 语义重新归属，不应默认继续留在 Host 节点。
4. ACTIVE_PROFILE=UNKNOWN 仍然正确。overlay 的 qcom,dsi-default-panel 指向 CSOT NT36523 双 DSI / C-PHY 默认节点，只能证明静态默认指针，不等于 Bootloader 或运行时已经选择该屏幕配置。
5. 6.18.33 仍是 android17-6.18 活跃源码分支 HEAD，而非已确认发布/认证的 GKI 6.18.33。公开 android17-6.18-2026-09_r8 Kleaf BUILD 列出了一些对应驱动模块目标，但这只证明该标签的构建图有这些目标，不证明本机已经构建、模块能在该设备加载或设备能启动。

建议顺序：先冻结 SoC common DTS 基础；按本报告修正 UFS/GENI/FSA compatible 与供电语义；然后补板级电源、时钟、pinctrl、graph endpoint；再独立处理 Huawei THP / panel / audio 私有 ABI。不要把所有外设一次性加入首个 bring-up DTS。

## 2. ROUND9 本机事实与必要纠错

### 2.1 UFS supply phandle 结果

ROUND9 经 overlay __fixups__ → base __symbols__ 闭环确认：

| 本机属性 | 解析目标 | 本机电气值 | 上游处理建议 |
|---|---|---:|---|
| PHY vdda-phy-supply | PM8150 L5 | 0.88 V / 89.9 mA | 保留为 QMP UFS PHY supply |
| PHY vdda-pll-supply | PM8150 L9 | 1.20 V / 18.8 mA | 保留为 QMP UFS PHY supply |
| Host vcc-supply | PM8150 L17 | regulator 2.496–3.008 V；overlay 2.504–2.950 V / 800 mA | 保留标准 UFS VCC；不要超出 regulator 约束 |
| Host vccq-supply | PM8150 L6 | 1.20 V / 800 mA | 保留标准 VCCQ |
| Host vccq2-supply | PM8150 S4 | 1.80–1.92 V / 800 mA | 保留标准 VCCQ2 |
| Host vdd-hba-supply | ufs_phy_gdsc GDSC | 无固定电压范围 | 标准供电属性；须与 power-domain 语义核验，不能互相替代 |
| HOS qcom,vccq-parent-supply | PM8150A S8 | 1.20–1.40 V / 210 mA | Qualcomm downstream 扩展；ACK 是否消费必须源码确认 |
| HOS qcom,vddp-ref-clk-supply | PM8150 L6 | 1.20 V / 100 µA | 主线 PHY 有可选 vddp-ref-clk-supply；应评估移至 PHY 节点并移除 vendor 前缀 |

标准 UFS common binding 明确列有 vdd-hba-supply、vcc-supply、vccq-supply、vccq2-supply 和相应 max-microamp 字段。SM8250 common DTS 则使用 2-lane UFS、标准 clocks、GCC reset 和 UFS_PHY_GDSC power-domain。HOS 中 VCC overlay 区间位于 PM8150 L17 regulator 的允许范围内；800 mA 是 HOS 本机 overlay 记录，不能因为同型号 Linux 参考板写 750 mA 就擅自改小。

### 2.2 UFS 下游属性与上游 PHY 属性的归属

- qcom,vccq-parent-supply / qcom,vccq-parent-max-microamp 在 Qualcomm downstream UFS Host driver 中存在专用 regulator 解析/负载设置逻辑；它不是 UFS common binding 的标准字段。未在本轮核验的 ACK 分支上游代码中证明它被消费，因此不能把 HOS property 原样带入并假设有效。
- Qualcomm QMP UFS PHY common driver 有可选 vddp-ref-clk regulator 支持；对应设备树字段是 vddp-ref-clk-supply（无 qcom, 前缀），语义属于 PHY reference-clock pad rail。HOS 把 qcom,vddp-ref-clk-supply 放在 Host overlay 中，建议在迁移 DTS 时将电源关系映射到 PHY 节点，并保留 PM8150 L6 / 1.2 V / 100 µA 的本机约束；在确认原厂驱动实际消费方之前，不得直接删除该 rail。
- 上游 SM8250 Host node 用 power-domains = <&gcc UFS_PHY_GDSC>。ROUND9 的 vdd-hba-supply 也指向名为 ufs_phy_gdsc 的 GDSC。两者不是同一个设备树属性；最终 DTS 应分别表达是否需要 regulator consumer 和 power-domain consumer，并确认 provider 是否支持两种接口，避免重复或错误控制 GDSC。
- 上游 PHY 需要的 vdda-phy / vdda-pll 已与本机 0.88 V / 1.20 V、89.9 mA / 18.8 mA 对应。不要误把这两个 rail 放到 Host node。

### 2.3 ROUND9 reset phandle 行的解析语义纠正

ROUND9 CSV 将 Host resets 的原始两 cell [23, 33] 展示成两个节点路径，其中第二个被解释成 thermal-zone trip。这不符合 Device Tree reset specifier 语义：一个 reset 引用由 provider phandle 和该 provider 定义的参数 cells 组成。SM8250 common DTS 的形式是：

    #reset-cells = <1>;
    resets = <&gcc GCC_UFS_PHY_BCR>;
    reset-names = "rst";

因此 33 是 GCC reset ID 参数，而不是第二个 phandle。不要在迁移报告或 DTS 中引用 thermal-zone trip 为 UFS reset controller。当前 reset 应规范化为单个 GCC UFS PHY BCR reset；若 HOS 原始编码与此不一致，应依据 base DTB provider 的 #reset-cells 解释，而不是按裸 32-bit cell 扫描。

ROUND9 的 Host clocks 一项仍为 UNKNOWN（parser 导出的 raw 数组为空），不能称为时钟闭环完成。主线 SM8250 common DTS 给出 8 个 Host clock names：core_clk、bus_aggr_clk、iface_clk、core_clk_unipro、ref_clk、tx_lane0_sync_clk、rx_lane0_sync_clk、rx_lane1_sync_clk；对应 freq-table-hz 与 OPP / interconnect 仍需纳入板级迁移核对。

## 3. Compatible 归一化与板级移植判断

| 子系统 / HOS compatible | Linux / ACK 对照 | 建议 | 置信度 / 限制 |
|---|---|---|---|
| UFS Host qcom,ufshc | SM8250 common DTS 使用 qcom,sm8250-ufshc、qcom,ufshc、jedec,ufs-2.0 | 用 SM8250 specific + generic fallback 列表；补齐主线 Host clocks/reset/power-domain/OPP/interconnect | 高；Host clocks 本机值仍未闭环 |
| UFS PHY qcom,ufs-phy-qmp-v4 | QMP driver 有 qcom,sm8250-qmp-ufs-phy 专用配置 | 改用 qcom,sm8250-qmp-ufs-phy，不要仅保留 HOS vendor compatible | 高；必须按 SM8250 PHY child lanes/reg/clocks/reset binding 建树 |
| GENI SPI qcom,spi-geni | 主线绑定及 driver 使用 qcom,geni-spi | 改为 qcom,geni-spi；以主线 SPI14 controller node 为底，补齐 serial-engine clock / interrupt / pinctrl | 高 |
| Huawei THP huawei,thp | 同型号 Linux shim OF match 为 huawei,dby-w09-thp | 保留 Huawei shim；推荐 DTS 使用 compatible = "huawei,dby-w09-thp", "huawei,thp"，并保证驱动 match；或者给 shim OF table 增加 huawei,thp | 高（存在 ABI）；仍需 daemon/firmware，HOS parent 10 MHz 作为保守上限，不直接升到同型号 port 的 16 MHz |
| FSA4480 qcom,fsa4480-i2c | 上游 driver/schema 使用 fcs,fsa4480 | 改为 fcs,fsa4480；补 vcc-supply、mode/orientation switch 和 Type-C graph port/endpoint | 高（芯片/地址证据）；ROUND9 extcon/端点仍 PARTIAL |
| Redriver onnn,redriver | NB7VPQ904M driver/schema 要求 onnn,nb7vpq904m | 保持 UNKNOWN；只有本机型号证据确认 NB7VPQ904M 后才更改；届时补 VCC、enable GPIO、orientation/retimer switch 和 graph ports | 低；不能从同型号 Linux DTS 直接推定 |
| WCD codec qcom,wcd938x-codec | 上游 binding / driver 只列 qcom,wcd9380-codec、qcom,wcd9385-codec | 不猜 9380/9385；取得确切 variant 证据后选对应 binding。若只能确认 WCD938x 家族，需要显式的 ACK driver/schema 扩展，不是随便换成 9380 字符串 | 中；HOS 仅提供 family-compatible |
| WSA881x | 上游 WSA881x SoundWire driver | 按主线 WSA881x binding / SoundWire graph 建树 | 中高；板级 SoundWire slave ID/端点仍需核验 |
| WLAN / BT qcom,cnss-qca6390、qca,qca6390 | ath11k PCI driver 支持特定 QCA6390 PCI device ID / HW major 路径 | 不能把 CNSS platform node compatible 直接改写成 ath11k compatible；先确定实际 PCI ID、subsystem ID、HW major，再使用对应 ath11k PCI support 和 board data | 低至中；HOS 自报 QCA6391，与 CNSS QCA6390 字符串并存，stepping 未知 |
| Panel candidates | Generic NT36523 panel driver 不等同 Huawei dual-DSI C-PHY profile | 优先基于 DBY-W09 专用 panel driver / command flow 实现；不要将所有候选都启用或仅因 NT36523 家族匹配就复用 generic panel | 中；active profile、背光 IC、init sequence 均未知 |
| Camera sensor0/1 qcom,cam-sensor | 上游 OV13B10 / Hi846 drivers 存在 | 先拿到实际 sensor compatible/ID/I2C address/endpoint；不要仅凭同型号 Linux port 选择 OV13B10/Hi846 | 低；本机 model/address/endpoint UNKNOWN |

### 3.1 UFS compatible 与主线节点骨架参考

以下仅展示 compatible 方向，不是完整可编译 DTS：

    ufs_mem_hc: ufshc@1d84000 {
        compatible = "qcom,sm8250-ufshc",
                     "qcom,ufshc",
                     "jedec,ufs-2.0";
        /* 其余 reg / interrupts / phys / clocks / reset /
           power-domains / OPP / interconnect 必须按 SM8250
           common DTS 与 DBY-W09 本机证据合并。 */
    };

    ufs_mem_phy: phy@1d87000 {
        compatible = "qcom,sm8250-qmp-ufs-phy";
        /* 保留 SM8250 QMP PHY 的 lanes / clocks / resets，
           以及本机解析出的 vdda-phy / vdda-pll。 */
    };

不要复制地址/寄存器列表到新 DTS 后就认为硬件已经完成适配。主线 SM8250 common DTS 中 Host/PHY 默认 disabled；该默认状态是 SoC common DTS 的基线，不代表本机 overlay 未启用，也不证明新内核上能初始化。

## 4. THP / Panel / WLAN / Camera / USB 的保守板级值

### THP
- 本机 GPIO：native CS 43、IRQ 39、reset 98；pinctrl default/idle 分别对应 active/suspend。
- 本机 parent SPI 10 MHz；children 的 16 MHz 是另一层限制，不能覆盖 parent cap。建议首轮上游 DTS 保持不超过 10 MHz，稳定后再凭实测验证提速。
- HOS compatible huawei,thp 与 shim 的 huawei,dby-w09-thp 不同；必须在 DT 与 OF match 里建立明确 alias。generic SPI touchscreen driver 不能代替 Huawei THP char-device/ioctl ABI。
- GPIO136 是 Ilitek child reset；不要误与主 THP reset GPIO98 合并。

### Panel
- 静态 default pointer：CSOT NT36523 10.9-inch 1600×2560 VIDEO、dual DSI、C-PHY、2 lanes per sublink、controller IDs 0/1。
- 其他 profile：110_20d、110_a09、190_20d、290_20d、dual_nt36523。当前不能认定活动项。
- GPIO6 IOVCC、38 reset、11 VSP、12 VSN、10 BL_EN；AVDD fixed regulator 的 pinctrl GPIO99。
- 背光 IC 多候选（LP855x、MP3314、RT4539、RT8555、SYH62758），active unknown。不要在 DTS 中同时启用所有 backlight IC。
- 同型号 Linux 参考采用 110_20d 只能作为候选参考，不能覆盖 HOS 4.3 当前静态 default 指针，更不能当作 active 证据。

### WLAN / BT
- GPIO20 WLAN_EN、GPIO21 BT_EN / reset、GPIO124 shared switch control、GPIO145 BT independent control。
- WLAN rails：S6 (AON/DIG)、S4 (IO)、S5 (RFA1)、S8 (RFA2)；BT rails：S6 (AON/DIG)、L16 (ASD)、S5 (RFA1)、S8 (RFA2)。
- HOS 自报 QCA6391，而 DT compatible 名称包含 QCA6390；必须等待 PCI ID / subsystem / HW major 证据。firmware、board data、BT NVM 和 calibration 未因 ROUND9 解析而闭环。

### Camera
- sensor0/1 目前都只确认 generic qcom,cam-sensor。
- 可用本机 GPIO/时钟线索包括 rear-like sensor0 MCLK GPIO94 / reset GPIO93 / CSIPHY index0，以及 front-like sensor1 MCLK GPIO96 / reset GPIO78 / CSIPHY index2；仍不得以此推断具体 sensor 型号。
- 不写入外部 port 的 sensor I2C 地址、MCLK、EEPROM/OTP 或 calibration 值作为 HOS 4.3 事实。

### USB-C / DP
- FSA4480 地址 0x43；HOS compatible 应规范化为 fcs,fsa4480，但其 graph endpoint、VCC rail 和方向/模式切换属性仍需闭环。
- redriver 地址 0x1c；本机只有 onnn,redriver，芯片型号未知。
- Type-C CC GPIO65；extcon 关系仍 PARTIAL。不要只靠 FSA4480 节点存在就宣称 USB-C / DP 完整连通。

## 5. ACTIVE_PROFILE 继续 UNKNOWN：可以做的非侵入性取证

目前可见的 qcom,dsi-default-panel 是 overlay 静态默认指针。它并不能证明 bootloader 选了这个 profile，也不能证明运行时 LCD-kit 选择没有被属性、硬件探测或 vendor display service 改写。

按证据强弱排序：

1. **现有 boot ramdisk 的静态证据（下一轮 ROUND10）**：只读查看 ramdisk 内 init*.rc、fstab.*、prop.default、bootconfig/cmdline 文件是否出现 panel/lcd/display 相关 property key、脚本触发器或配置文件路径。只输出 property key、文件 basename 和规则摘要，不导出敏感值或 display command payload。它最多提供 boot-chain selector 线索，不能单独确认活动屏幕。
2. **现有本地文本报告**：查找 ROUND3/7/8 已经生成的 9 个 board-id / DTBO 选择记录、rootparam 存在性及 overlay 选择记录；无需重新解析 FDT/DTBO。当前已知 entry 8 对应 board-id 0x206a / DBY_W09_VG，但不等于最终 boot overlay 已应用。
3. **最终权威证据（当前边界下暂不可取）**：Bootloader 最终传给内核的 live FDT、启动日志中实际绑定的 panel driver/profile，或 vendor/odm 中实际被 display service 使用的配置。这些需要设备运行时采集，或读取 EROFS 的 vendor/odm 内容；当前设备连接被禁止，EROFS 仍 BLOCKED。因此不得为了确定 profile 而让 Agent 连设备或另写 EROFS reader。

结论：ROUND10 即便找到 ramdisk selector，也只会把状态提升为“存在 boot-time 选择线索”；没有 live FDT / runtime 选择证据时，ACTIVE_PROFILE 仍保留 UNKNOWN。

## 6. ACK build target 证据与限制

公开的 android17-6.18-2026-09_r8/BUILD.bazel 列有下列 module build targets：ufs-qcom.ko、phy-qcom-qmp-ufs.ko、spi-geni-qcom.ko、fsa4480.ko、nb7vpq904m.ko、ath11k_pci.ko、wcd938x.ko、wsa881x.ko。这表明这些目标在该公开 ACK tag 的 Kleaf build graph 中存在，但不代表它们都属于 protected GKI module、已在当前 6.18.33 branch head 构建，或能无修改加载于 DBY-W09。

此外：
- 当前设备 Android 12 / API31；android17-6.18 对应 Android 17 平台代际，不属于 Google 官方 Android 12 launch-kernel compatibility pair。
- 传统 boot header v2 + 独立 ramdisk，与 Android 17 GKI 设备的 boot/vendor_boot 预期不能直接等同。要移植的不只是 kernel / DTS，还包括启动链、ramdisk、AVB / vendor interface、userspace HAL、KMI 及模块策略。
- ROUND5 EROFS BLOCKED，不能判断旧 4.19 vendor modules 的 vermagic、依赖、符号、私有 firmware、VINTF/KMI 是否兼容。不得假设 4.19 模块能加载到 6.18。

## 7. 当前缺口 / 后续开发门槛

| 项目 | 当前状态 | 解除条件 |
|---|---|---|
| UFS Host clocks / OPP / interconnect | 本机 clocks 列值未由 ROUND9 成功闭环 | 可靠解析已有 base FDT 对应 clock specifier，或以同一 SoC common DTS + 本机验证补齐 |
| UFS GDSC 双重语义 | vdd-hba 与 GDSC / power-domain 关系未确认 | 确认 GDSC provider regulator interface 与 consumer 时序 |
| qcom,vccq-parent ACK 支持 | 未确认 ACK 处理 | 精确检查目标 branch UFS driver；必要时移植下游 regulator load sequencing |
| THP firmware / daemon / ABI | UNKNOWN | EROFS 可信读取或公开协议证据 |
| Panel active profile / backlight IC | UNKNOWN | boot ramdisk 选择线索 + 最终 live FDT / runtime profile |
| QCA639x exact silicon and firmware | UNKNOWN | PCI IDs / HW major / board-data / firmware evidence |
| WCD9380 vs 9385 exact part | UNKNOWN | 硬件明确型号证据或原厂设备树 |
| Camera models / addresses / CSI endpoints | UNKNOWN | 原厂 sensor subnodes / 可靠公开板级证据 |
| Redriver exact model / graph | UNKNOWN / PARTIAL | 本机 part evidence + complete graph/power |
| vendor/odm modules, firmware, VINTF/KMI | EROFS BLOCKED | 可信只读 EROFS 工具 |
| Boot / GKI / platform integration | NOT_TESTED | 单独规划的源码同步、构建、验证与授权流程 |

## 8. 参考来源

**Google Android Common Kernel / Linux source**
- [SM8250 common DTS](https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/arch/arm64/boot/dts/qcom/sm8250.dtsi)
- [QMP UFS PHY driver](https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/phy/qualcomm/phy-qcom-qmp-ufs.c)
- [Qualcomm UFS PHY common support](https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/drivers/phy/qualcomm/phy-qcom-ufs.c)
- [UFS common binding](https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/Documentation/devicetree/bindings/ufs/ufs-common.yaml)
- [GENI SPI binding](https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/Documentation/devicetree/bindings/spi/qcom,spi-geni-qcom.txt)
- [FSA4480 binding](https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/Documentation/devicetree/bindings/usb/fcs,fsa4480.yaml)
- [WCD938x binding](https://android.googlesource.com/kernel/common/+/refs/heads/android17-6.18/Documentation/devicetree/bindings/sound/qcom,wcd938x.yaml)
- [Android17 6.18 r8 Kleaf module build targets](https://android.googlesource.com/kernel/common/+/refs/tags/android17-6.18-2026-09_r8/BUILD.bazel)

**同型号 DBY-W09 公开参考（只作参考，不覆盖本机事实）**
- [svesnav DBY-W09 Linux DTS](https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts)
- [svesnav Huawei THP shim](https://github.com/svesnav/linux-dby-w09/blob/main/touch/huawei-thp-lite.c)
- [svesnav Huawei panel driver](https://github.com/svesnav/linux-dby-w09/blob/main/panel/panel-huawei-dby-w09.c)
- [svesnav camera DTS](https://github.com/svesnav/linux-dby-w09/blob/main/camera/camera.dtsi)
- [svesnav USB Type-C DTS](https://github.com/svesnav/linux-dby-w09/blob/main/usb/typec.dtsi)

**下游属性来源（只用于识别非上游属性语义）**
- [Qualcomm downstream UFS Host driver](https://android.googlesource.com/kernel/msm/+/refs/heads/android-msm-coral-4.14-android10-qpr1/drivers/scsi/ufs/ufs-qcom.c)
- [Qualcomm downstream UFS QMP binding](https://android.googlesource.com/kernel/msm/+/refs/heads/android-msm-coral-4.14-android10-qpr1/Documentation/devicetree/bindings/ufs/ufs-qcom.txt)

## 9. 证据边界声明

本报告没有编译内核、同步源码树、运行 Kleaf、连接设备、刷机、解锁、读取实时日志或解析 EROFS。所有结论来自公开源码与 ROUND9 已上传脱敏文本。

本报告不表示 DBY-W09 的 6.18.33 DTS 已完成、任何外设已工作、任何 GKI module 已成功加载、或系统已经可启动。PR #1 保持 Draft，不合并。
