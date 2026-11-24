# AGENT_TASK_ROUND9.md — DBY-W09 HOS 4.3 phandle / GPIO / sensor node 补充核验

日期：2026-11-24  
任务性质：严格只读、本地现有 FDT 工作副本的定点属性解析。  
目标：为 ACK / GKI 6.18.33 板级 DTS 对照补齐 ROUND8 后尚未解析的 supply / pinctrl / GPIO / camera / Type-C 连接关系。

## 0. 开始前必须阅读

1. 先阅读仓库根目录 `AGENT_TASK.md`。
2. 再阅读本文件。
3. 阅读 ChatGPT 的 ROUND9 公开驱动兼容矩阵：
   `kernel-baseline/round9/dby-w09-6.18-driver-compatibility-matrix.md`
4. 阅读 ROUND8 已完成的三份报告，避免重复：
   `firmware-analysis/round8/dtbo8_fragment_target_map.csv`
   `firmware-analysis/round8/dtbo8_board_hardware_resolution.txt`
   `firmware-analysis/round8/round8_summary.json`

## 1. 输入范围（仅现有工作副本）

只允许读取 ROUND3 已经存在的两个文件：

- `D:\DBY-W09_FirmwareAnalysis_round3\dtb_work\boot_fdt_candidate_0.dtb`
- `D:\DBY-W09_FirmwareAnalysis_round3\dtb_work\dtbo_entry_8.dtbo`

仅复用 ROUND3 FDT parser 及 ROUND8 用过的 target/fixup/symbol 解析能力。不要重新提取固件，不要重新扫描原始镜像，不要重写 parser。

如果已有 parser 无法安全读取某类属性或 phandle：
- 对应字段标记 `UNKNOWN` / `NOT_EXPORTED_BY_EXISTING_PARSER`；
- 记录具体原因；
- 停止该子项；
- 不要通过新写二进制 parser、安装工具或临时脚本绕过限制。

不得要求用户重新上传固件或重复提供已知路径。

## 2. 本轮只做以下定点核验

### A. UFS supply / PHY / controller 引用解析

已知：
- fragment@63 → `/soc/ufsphy_mem@1d87000`
- fragment@64 → `/soc/ufshc@1d84000`

本轮仅解析 entry 8 中这些 supply / clock / reset / power-domain phandle 的引用目标：
- `vdda-phy-supply`
- `vdda-pll-supply`
- `vcc-supply`
- `vccq-supply`
- `vccq2-supply`
- `vdd-hba-supply`
- `vddp-ref-clk-supply`
- `qcom,vccq-parent-supply`
以及已有属性中能安全映射的 clocks/resets/power-domains。

输出目标 regulator/controller 节点路径、regulator-name、min/max microvolt、相关 max-load 值（若属性存在）。不要输出 MMIO 地址、物理地址或完整 phandle 原始数组。

不得把 `0xffffffff` external fixup placeholder 当作最终 regulator 目标。必须追踪 entry 8 `__fixups__` 到 base `__symbols__`；无法闭环则标记 UNKNOWN。

### B. THP / SPI14 pinctrl 与 GPIO

检查 fragment@89 及其引用目标，尽可能解析：
- SPI controller / SPI14；
- native chip-select pin；
- THP IRQ GPIO；
- THP reset GPIO；
- default / idle（或 sleep）pinctrl state；
- 父 SPI 10 MHz 与 Novatek/Ilitek 子节点 16 MHz 的属性层级。

重点区分：
- FDT 直接 GPIO number；
- pinctrl state 下实际 pin number/function；
- 仅为 phandle，尚未解析的引用。

不能把同型号 Linux DTS 中 GPIO43 / GPIO39 / GPIO98 的参考值冒充本机 HOS4.3 的直接提取值。

### C. Panel / backlight pinctrl 与 profile 选择关系

仅检查已知 entry 8 fragments：
- fragment@22、@78、@79、@80、@81、@82；
- fragment@39、@40、@61、@62、@86、@87；
- fragment@83、@142；
以及与这些 fragment properties 实际引用的 pinctrl/supply/DSI node。

尽可能确定：
- profile node / target path 与 DSI primary/secondary 的关联；
- `/huawei,lcd_panel` 中公开可读的 profile selector 字符串/整数；
- VCI / IOVCC / TPS65132 VSP/VSN / RT8555 enable / panel reset 的 GPIO 与 regulator 映射；
- panel C-PHY / dual-DSI flags（仅导出标志，不输出 init command payload）。

如果仍有多个 profile 且无法判断活动 profile，明确写 `ACTIVE_PROFILE=UNKNOWN`，不要按同型号 Linux DTS 的 110_20d 推定本机最终选择。

禁止输出 panel init command arrays、厂商私有二进制 payload 或完整 display tuning 数据。

### D. WLAN / Bluetooth enable GPIO 与 rail phandle

仅围绕本机已存在的：
- `/soc/qcom,cnss-qca6390@b0000000`
- PCIe node `/soc/qcom,pcie@1c08000`
- SLIMbus QCA6390 node
- entry 8 fragment@71、@76、@77、@136、@137、@140
检查 WLAN_EN、BT_EN、pinctrl state、regulator/supply phandle 的本机引用关系。

只输出 GPIO/pinctrl 名称、GPIO number、regulator-name、voltage range 等必要字段。不得输出 MAC/BD address、NVM、calibration、firmware 数据。

### E. Camera sensor0 / sensor1 board properties（不读取校准数据）

仅检查：
- fragment@131 → `/soc/qcom,cci@ac4f000`
- fragment@132 → `/soc/qcom,cci@ac50000`
及其 sensor/actuator 的常规设备树节点。

允许导出：
- sensor model/name/compatible（若直接存在）；
- I2C slave address；
- reset / powerdown GPIO；
- MCLK / clock frequency；
- AVDD / DVDD / IOVDD supply 引用目标及 regulator name/电压；
- CSIPHY / CSID / endpoint remote-endpoint 路径；
- actuator 的 compatible 与 I2C address（若存在）。

禁止读取或输出：
- EEPROM / OTP / calibration payload；
- sensor register init tables；
- camera firmware；
- NVM / serial / module identity；
- 私有 tuning 数据。

如本机只显示通用 `qcom,cam-sensor`，必须将 sensor model 标记为 UNKNOWN，不得根据同型号 Linux 项目直接填入 OV13B10 / Hi846。

### F. USB-C / DP mux / retimer / PHY endpoint

仅检查：
- base `/soc/i2c@884000/fsa4480@43`；
- fragment@66 的 redriver@1c；
- fragment@9 / @10 / @11；
- fragment@2 中 Type-C / USB-PD 节点；
以及实际被引用的 pinctrl/supply/endpoint phandle。

尽可能输出：
- FSA4480 / redriver compatible（保留本机原始字符串）与 I2C address；
- QMP Combo PHY / USB / DP endpoint 关联路径；
- orientation / mux / retimer control GPIO；
- regulator supply 引用目标。

不得仅凭同型号 Linux port 将 `onnn,redriver` 改写为 `onnn,nb7vpq904m`；除非本机 FDT 存在直接型号证据，否则本机 model 保持 UNKNOWN。

## 3. 输出文件（纯脱敏文本）

在本机新建目录：

`D:\DBY-W09_FirmwareAnalysis_round9\`

输出以下 4 个文件：

1. `round9_pin_gpio_phandle_map.csv`
   - 子系统、源 fragment/node、property、解析目标路径、GPIO/pinctrl/regulator 名称、必要的电气参数、解析状态、证据类型。
2. `round9_camera_public_node_inventory.csv`
   - 只包含本任务 E 允许的 sensor/actuator board properties；不含 EEPROM/calibration。
3. `round9_panel_ufs_resolution.txt`
   - 记录 UFS supply 解析、THP GPIO、panel profile 选择关系及所有仍 UNKNOWN 的字段。
4. `round9_summary.json`
   - 输入文件名（不含完整本地路径）、parser 复用情况、各子项统计、BLOCKED/UNKNOWN 原因、输出文件清单。

所有文件必须是 UTF-8 文本。对未成功解析的值不得猜测。GPIO number、I2C 地址、regulator 逻辑名称和电压范围可保留；地址空间物理地址一律脱敏。

## 4. GitHub 上传

只上传以上 4 份脱敏文本到：
- 仓库：`hhdy/matepad11-dby-w09-agent-reports`
- 分支：`firmware-audit-v1`
- 目录：`firmware-analysis/round9/`

上传前检查文件内容不得包含：
- FDT/DTBO/boot/vendor/odm 二进制或任何固件二进制；
- EEPROM / OTP / camera calibration / firmware / NVM / audio tuning payload；
- 完整 local SHA-256；
- serial / IMEI / MAC / Bluetooth address / Wi-Fi address；
- token / PAT / cookie；
- 用户名、主机名、完整私人本地路径；
- 未脱敏物理 MMIO 地址或 reserved-memory 地址。

若发现任何上述内容，先从报告中剔除再上传。

## 5. 严禁事项

- 不刷机、不解锁、不连接设备、不 ADB、不 fastboot。
- 不 root、不写分区、不加载模块、不挂载可写文件系统。
- 不编译内核、不运行 Kleaf/Bazel。
- 不调用 WSL，不绕过 Windows 命令安全策略，不更改 execution policy，不关闭安全软件。
- 不下载或安装未知 EXE/DLL。
- 不安装/使用未经核验来源的二进制工具。
- 不写自制 FDT/DTBO 二进制 parser。
- 不读取 EROFS，不分析 vendor/odm 模块或 firmware。
- 不重新提取或复制任何固件文件。
- 不上传任何二进制文件。

## 6. 完成判据

- 能安全解析的字段有 source path / property / target path 证据；
- 无法解析的字段明确标记 UNKNOWN / BLOCKED / NOT_EXPORTED；
- 不对活动 panel profile、sensor model、redriver model、QCA 芯片 stepping 作无证据推断；
- 只上传 4 份脱敏文本；
- 保持本地原始 FDT/DTBO 工作副本未修改。
