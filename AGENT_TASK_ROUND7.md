# AGENT_TASK_ROUND7.md — 只读取证：HarmonyOS 4.3 DTB / DTBO 细粒度属性清单

> 本轮只让本地 Agent 做 ChatGPT 无法直接访问的本地二进制读取。公开上游研究、Linux 6.18 驱动检查、同型号 Linux 7.x 项目源码审查已由 ChatGPT 完成，见：
> [kernel-baseline/round7/same-device-mainline-port-audit.md](./kernel-baseline/round7/same-device-mainline-port-audit.md)
>
> 不要重复网页搜索，不要重新分析 Xiaomi ZIP，不要重新提取固件，不要解包 EROFS，不要编译内核。

## 1. 任务目标

对用户本地已经生成的 HarmonyOS 4.3 DTB / DTBO 工作副本，生成更完整的设备树节点与属性清单，用来与同型号公开主线 Linux 项目进行逐项对照。

唯一可信的本机输入位置来自 ROUND3 报告：
- 本地目录：D:\DBY-W09_FirmwareAnalysis_round3\dtb_work
- 已有工作副本：9 个 DTBO entry + 4 个 boot FDT candidate，共 13 个二进制文件。
- 这些文件已从 ROUND3 解析过的原厂固件中提取，ROUND3 报告确认边界与 FDT 校验结果。
- 若此目录不存在或文件数/内容无法确认，停止并报告；不要重新从固件提取，也不要要求用户重新上传。

本轮只做只读 FDT 属性解析与脱敏摘要，不触碰原始固件，不生成任何可刷入镜像。

## 2. 已知基线（不要重复计算为新成果）

ROUND3 已报告：
- boot DTB 的确定性位置：22,790,144 bytes，model 为 Qualcomm Technologies, Inc. kona v2.1，compatible 为 qcom,kona，msm-id=[356,131073]。
- boot 区域另有 3 个扫描发现的 FDT candidate；必须保留 candidate 身份，不得把它们自动认定为 bootloader 实际选用 DTB。
- 9 个 DTBO entry 均 FDT VALID。
- DTBO table 的 board-id（十进制）：8200、8296、8206、8208、8202、8238、8302、8240、8298。
- 最后一项 8298 = 0x206a。
- DTBO 总大小 2,963,810 bytes。
- DTBO compatible 总体识别为 qcom,kona-qrd。
- 详细值见 firmware-audit-v1 分支的 firmware-analysis/round3/round3_summary.json。

本项目已经完成的公开研究：
- [同型号主线 Linux 对照报告](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round7/same-device-mainline-port-audit.md)
- 同型号 svesnav DTS 声明 msm-id revision 0x20001；其 Huawei rootparam overlay 使用 board-id 0x206a。
- 上述外部项目部分基于 HarmonyOS 4.2，本轮设备事实必须来自用户本机 HOS 4.3 DTB / DTBO。
- 不得将外部 DTS 直接覆盖本机 DTS。

## 3. 输入与工具约束

1. 只使用上述 dtb_work 中现有的 13 个文件。
2. 优先复用 ROUND3 已验证的 Python 标准库 FDT 解析器/结构校验逻辑。可从本地 ROUND3 工具副本或已获取的仓库工具源码中读取，不要重新实现一套不必要的 parser。
3. 不安装第三方 Python 包，不下载 EXE/DLL，不使用来源不明的工具。
4. 如果本机已有可信 dtc / fdtget 可选读取，但不得为本轮安装。没有这些工具不构成失败，标准库 parser 足够。
5. 不调用 ADB、fastboot、WSL，不运行外部 Linux 项目的脚本，不运行固件或 installer 脚本。
6. 仅以只读方式打开 FDT 文件；不能重写、修复、重新编译或改名原始工作副本。
7. 解析遇到非法 token、越界 offset、重复/损坏属性时 fail closed；不能猜测或静默跳过格式错误。

## 4. 必须输出的属性清单

每一个 FDT 文件都要有独立来源标识：boot FDT candidate index / DTBO entry index / 本地工作文件名。记录 model、compatible、FDT totalsize 和验证状态。

重点检索并输出以下节点/属性（仅在实际存在时记录）：

### 4.1 SoC / board / boot identity
- 根节点 model、compatible、qcom,msm-id、qcom,board-id。
- 所有相关节点中的 qcom,boardid、qcom,board_name、qcom,product_name、hardware_version、huawei,modem_id。
- DTBO entry index、id、rev、custom、board-id 和 overlay metadata（__symbols__ / __fixups__ / __local_fixups__）。
- 对于 /rootparam，记录节点和字段是否存在。涉及序列号、MAC、设备唯一身份或其他敏感值一律只记录“存在/已脱敏”，不要输出值。

### 4.2 Display / DSI / panel / backlight
- DSI host/controller 节点、panel compatible / model、resolution/timing、refresh rate、lane count、C-PHY/D-PHY mode、clock frequency。
- panel reset GPIO、VSP/VSN/VCI/IOVCC regulator 引用、TPS65132 / RT8555 等节点。
- 只记录属性名和硬件参数；若属性含私有面板命令数组/大块二进制值，不输出 payload，只记录长度与存在性。

### 4.3 Touch / SPI / I2C
- touch controller compatible、SPI bus/CS、IRQ GPIO、reset GPIO、regulator、clock、pinctrl。
- Novatek/THP/Huawei touch 节点与触控笔节点。
- 触摸固件 blob 名称、路径若可能暴露私有路径，则只输出 basename 或“有/无”。

### 4.4 Wi-Fi / Bluetooth / PCIe
- PCIe controller/port 节点、Wi-Fi/BT compatible、firmware-name、board-data 引用、wlan-enable-gpios、bt-enable-gpios。
- 无线供电 rails、regulator voltage、pinctrl。
- 不能仅凭 compatible 断言实际芯片商业型号；如果 PCI device/subsystem ID 不在 DTB 中，标为 UNKNOWN。
- MAC / BD address / 设备唯一无线身份只记录已脱敏，不输出数值。

### 4.5 UFS / QMP PHY
- UFS host compatible、status、reg、interrupts、clocks、clock-names、resets、phys、phy-names、power-domains、interconnects、regulator supplies。
- QMP UFS PHY compatible、lane/rx/tx 节点、reset 和 clock 引用。
- 对不存在或 disabled 的节点照实记录；不要从 SM8250 通用 DTS 推断本机 HOS 4.3 已启用。

### 4.6 PMIC / regulator / GPIO / clocks / interconnect
- PMIC compatible / pmic-id；所有引用到关键设备的 regulator 名称和 voltage range。
- GPIO / pinctrl 仅输出 pin number、功能描述和 active polarity；不输出无关身份数据。
- clocks / clock-names / power-domains / interconnects。
- 相同供电节点跨多个设备引用时可归并，但必须保留原引用关系。

### 4.7 Audio / USB-C / Camera / sensors
- WCD938x、SoundWire、Q6AFE/ADSP、TFA9874、speaker routing、audio dai-link。
- USB-C、Type-C controller、PD、USB role-switch、DP mux / retimer / PHY。
- camera sensor、CCI/I2C、CSIPHY/CSID、MCLK、regulator、GPIO。
- sensors、hall、keyboard、pen、vibrator。
- 只做属性清点，不解释或试运行固件。

### 4.8 Reserved memory
- 记录节点名称、size、no-map / reusable 与用途线索。
- 公开报告不得输出实际物理地址/精确地址区间；用“地址已脱敏”代替。
- 不得公开 GPU/ZAP/SMEM/ADSP/secure memory 的真实地址。

## 5. 输出文件

本地使用新目录：
D:\DBY-W09_FirmwareAnalysis_round7

只生成：
1. dtb_property_inventory.csv：每个 FDT 每个重点节点的属性名、脱敏属性值/摘要、来源和校验状态。
2. dtbo_board_rootparam_matrix.csv：9 个 overlay entry 的 index/id/rev/custom/board-id/model/compatible/rootparam presence。
3. dby_w09_hw_matrix.txt：按子系统汇总本机 HOS 4.3 已确认数据、缺失数据和待验证项。
4. round7_summary.json：输入文件数、FDT 结构解析状态、entry 覆盖率、未解析项、边界声明。

敏感字段脱敏：
- 不公开任何 MAC/蓝牙地址、序列号、IMEI、设备唯一标识。
- 不公开 reserved-memory 实际地址或精确区间。
- 不公开触摸/显示大块初始化命令的原始 payload。
- 不公开完整本地 SHA-256。
- 不公开用户名、主机名、完整本地路径、认证信息、PAT/token。
- 不上传 DTB/DTBO 二进制、反编译后的完整 DTS、原始 FDT blob 或固件镜像。
- 如果任何字段是否敏感无法确定，宁可只报告属性名和存在性。

## 6. 与外部项目的字段对照

ChatGPT 已完成外部源码审查；Agent 不需要再访问外网，不需要复制或上传外部 DTS。

本地报告只需准备 HOS 4.3 的事实值，后续由 ChatGPT 做下列对照：
- 本机 msm-id / board-id ↔ svesnav Huawei board DTS / rootparam DTBO；
- 本机 panel / DSI / power rails / GPIO ↔ svesnav Huawei board DTS；
- 本机 touch SPI / IRQ / reset ↔ svesnav Huawei THP bridge；
- 本机 WLAN/BT / regulators / enable GPIO ↔ QCA6390/6391 公开项目差异；
- 本机 UFS/QMP ↔ SM8250 上游 SoC DTS 和 Linux 6.18 QCOM UFS/QMP support；
- 本机 WCD938x / SoundWire / USB-C / DP / camera ↔ Linux 6.18 上游 driver/Kconfig 与同型号 Linux port。

匹配分类由后续 ChatGPT 完成：
- MATCH：关键属性和连接完全一致；
- DIFFERENT_VALUE：节点对应，但值/接线/参数不同；
- ONLY_IN_LOCAL_43：本机存在而外部参考未覆盖；
- ONLY_IN_REFERENCE：外部参考存在但本机 4.3 FDT 未发现；
- UNKNOWN：信息缺失或无法确认。

## 7. GitHub 提交规则

只上传以下四份脱敏文本：
- firmware-analysis/round7/dtb_property_inventory.csv
- firmware-analysis/round7/dtbo_board_rootparam_matrix.csv
- firmware-analysis/round7/dby_w09_hw_matrix.txt
- firmware-analysis/round7/round7_summary.json

上传到 firmware-audit-v1 分支。不要创建或推送新 binary 文件；不要更改 main 上的研究报告或任务书；不要合并 PR #1。若本地分支不可用或权限不足，保留本地报告并记录，不索要 PAT。

## 8. 禁止事项与停止条件

- 不从原始 boot.img / dtbo.img 重提取；已有 dtb_work 是唯一输入。
- 不解包 EROFS，不提取 vendor/odm/system/product，不处理模块或固件二进制。
- 不下载官方/非官方工具，不安装软件，不调用 WSL，不修改安全策略。
- 不编译内核、不运行外部项目构建脚本、不刷机、不连接设备。
- 不为得到更多字段访问用户的私人目录或其他磁盘。
- dtb_work 缺失、文件校验不符或解析器不能安全解析时，停止并写明具体阻塞，不得重提取、重建 parser 或用字符串搜索假装完成。

## 9. 完成标准

必须覆盖 13 个现有 FDT 工作副本（若ROUND3报告的文件实际有缺失，逐项列出）；每个 FDT 通过结构边界校验；9 个 DTBO entry 均有 matrix 行；敏感值已脱敏；四份文本报告上传成功或明确记录上传阻塞。

本轮仅完成本地只读属性清单，不等于设备树已可用于 Linux/GKI，不等于已完成驱动适配，也不代表内核能够启动。
