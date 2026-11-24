# AGENT_TASK_ROUND8.md — 最小本地补充：DTBO8 fragment target / GPIO / 设备子树解析

> ROUND1–ROUND7 已完成。ChatGPT 已直接完成公开源码 / 同型号 Linux 项目 / Linux v6.18 驱动研究，并把对照报告放在 main：
> [kernel-baseline/round8/harmonyos43-hardware-reference-comparison.md](./kernel-baseline/round8/harmonyos43-hardware-reference-comparison.md)
>
> **本轮仅做无法由 ChatGPT 远程完成的本机 FDT 二进制读取。** 不要重复网页搜索、外部 GitHub 审查、ROUND6 PATH 工具检查、固件分析或 DTB 全量 inventory。

## 1. 唯一输入

只使用 ROUND3 已存在的本地工作副本：
- 目录：`D:\DBY-W09_FirmwareAnalysis_round3\dtb_work`
- 基树：`boot_fdt_candidate_0.dtb`（ROUND3 确定性 boot FDT，KONA v2.1）
- 目标 overlay：`dtbo_entry_8.dtbo`（board-id 8298 / 0x206a，对应 DBY_W09_VG）
- 其余 DTBO / FDT 文件不需要重新解析。

如果两个文件不存在、FDT 不能通过结构校验，立即停止并报告；不要从固件重新提取、不要要求用户重传。

## 2. 已知值（不要重复计算为新发现）

来自 ROUND7：
- 13/13 个 FDT 工作副本结构校验 VALID。
- base FDT candidate 0：model Qualcomm Technologies, Inc. kona v2.1 SoC；compatible qcom,kona；msm-id [356,131073]；base board-id [0,0]。
- DTBO entry 8：board-id [8298,0]；compatible qcom,kona-qrd / qcom,kona / qcom,qrd；model Huawei Technologies DBY-W09。
- entry 8 fragment@143/__overlay__ 属性：qcom,boardid [8,2,9,8]、qcom,board_name DBY_W09_VG、hardware_version SH1DBSLM、huawei,modem_id。敏感字段不可输出完整值。
- HOS 4.3 base FDT 的 UFS host / UFS PHY status 当前被解析为 disabled，但这不等于已确定内核启动时使用的最终 FDT。
- HOS 4.3 entry 8 有面板候选、THP、QCA6390、WCD938x/WSA881x、SmartPA、camera、USB/Type-C 相关 fragment。

外部对照已由 ChatGPT 完成，不要重复找资料：
- svesnav 同型号 DTS / rootparam overlay 使用 msm-id 0x20001 与 Huawei board-id 0x206a。
- 同型号 DTS 将 UFS host + PHY 启用并添加 UFS rails；UFS/QMP UFS 驱动在 Linux 6.18 已存在。
- 参考 panel profile 为 lcd_kit_debussy_110_20d_10p9_qcom；Huawei THP IRQ GPIO39；QCA6390；WCD938x；四个 TFA9874 在 I2C 0x34–0x37 / Primary TDM。
- 外部项目部分以 HOS 4.2 为基线，不能覆盖 HOS 4.3 本机事实。

## 3. 必须完成的解析

复用 ROUND7 使用的标准库 FDT parser / 结构校验函数。不要重写 parser 或安装第三方工具。如果原本调用的 parser 不存在、无法定位或不能安全复用，停止并报告，不要另写第二套解码器。

### A. fragment target 映射（本轮核心）

1. 扫描 dtbo_entry_8.dtbo 中全部 fragment@N 节点。
2. 对每个 fragment 读取 target phandle / target-path。
3. 通过 base FDT 的 phandle 与 linux,phandle 节点索引，将每个 target 解析到 base FDT 实际 node path。
4. 如 target 是未解析外部引用，按 overlay 的 __fixups__ / __symbols__ 关系尝试只读解析；未能解析时明确标记 TARGET_UNRESOLVED，不猜测。
5. 特别核验 fragment@143 的 target 是否为 /rootparam。只输出路径和属性名称，不输出 phandle 数值。
6. 对每个 fragment，记录 overlay 子树的根 compatible / 关键子节点名称，便于识别它修改的是显示、触摸、无线、音频、摄像头还是 PMIC 节点。
7. 输出所有 fragment 的总数、已解析数、未解析数和重复目标数。

### B. UFS target/status 追踪

检查 entry 8 的所有 fragment target 及其 overlay 子树，明确回答：
- 是否有任何 fragment target 指向 /soc/ufshc@1d84000？
- 是否有任何 fragment target 指向 /soc/ufsphy_mem@1d87000？
- 是否有 overlay property 修改上述节点的 status、vcc/vccq/vccq2、vdda-phy/vdda-pll、clocks、resets、phys 或 power-domains？
- 是否有节点只修改相关 regulator provider，而不直接修改 UFS host？
- 若无，结论只能写“entry 8 中未发现对 UFS host / PHY 的 overlay 修改”，不要进一步推断其他八个 DTBO 或运行时 FDT。
- 如果有，分别报告 overlay target、属性名和脱敏值。

### C. Pinctrl / GPIO 关联（只输出与关键硬件有关的映射）

解析 entry 8 覆盖的节点与 base FDT pinctrl：
- THP：SPI controller、CS、IRQ GPIO39、reset GPIO / pinctrl、SPI frequency。
- WLAN/BT：CNSS / PCIe / BT node 使用的 pinctrl states 与 GPIO pin number（若可由引用映射）。
- Panel/backlight：GPIO6、GPIO10、GPIO11、GPIO12、GPIO38 对应的 IOVCC/backlight/bias/reset signals（若本机 FDT 中有引用）。
- SmartPA：I2C bus 目标、I2C 地址和 chip_model 原样作为不透明字段，不要解码 chip_model。
- UFS：reset / clock / regulator 引用，只需列出名称与解析状态，不输出 MMIO 物理地址。

### D. Camera 子树（只导出安全硬件摘要）

对 entry 8 的 cam-sensor0 / cam-sensor1 / actuator / eeprom fragment：
- target path；
- compatible / sensor name / model id（若有且非隐私）；
- I2C bus address；
- reset GPIO；
- MCLK source/frequency；
- AVDD/DVDD/IOVDD supply phandle 解析后的 regulator 名称和电压值（若可确定）；
- CAMSS / CSIPHY / CSID endpoint 和 lane count。
不要输出 EEPROM 内容、校准数据、原始大块属性、物理寄存器地址。

### E. Audio / USB-C 简要 target 映射

只需给出：
- WCD938x / WSA881x / Huawei SmartPA fragment 的目标节点路径；
- SmartPA 0x34–0x37 与 0x30–0x33 / 0x50–0x53 各节点的 chip_model 不透明值；
- PM8150B Type-C / PD PHY / SMB5 节点；
- FSA4480 / retimer / USB DWC3 / QMP Combo PHY / DP 节点及互连端点。
不要导出 DSP firmware、SmartPA 私有表、音频寄存器初始化或设备身份信息。

## 4. 输出报告

本地目录：`D:\DBY-W09_FirmwareAnalysis_round8`

只生成三个脱敏文本文件：
1. `dtbo8_fragment_target_map.csv`
   - fragment name、target path、target resolution state、overlay root child names、top-level compatible summaries。
2. `dtbo8_board_hardware_resolution.txt`
   - rootparam 目标、UFS overlay 是否修改、关键 GPIO/pinctrl mapping、panel / THP / WLAN / SmartPA / camera / USB target mapping。
3. `round8_summary.json`
   - 输入文件存在性、FDT validation、fragment 数量、target resolved/unresolved 数、UFS target changes found、每个子系统覆盖情况、边界布尔值。

安全脱敏：
- 不输出任何物理 MMIO address / reserved memory 地址 / 完整 memory range。
- 不输出 MAC/BD address、序列号、IMEI、cookie、token、PAT。
- 不输出 panel init command payload、AFE/SmartPA private tables、EEPROM/calibration payload、firmware blobs。
- 不输出完整本地 SHA-256、完整本地路径、用户名或主机名。
- I2C 设备地址、GPIO pin 数量、clock/voltage values 可以作为硬件参数；但若字段含隐私或不能确定，报告存在性而非值。
- 不上传反编译全量 DTS、FDT/DTBO blob 或二进制。

## 5. GitHub 回传

只允许上传三个脱敏文本文件至 `firmware-analysis/round8/`，分支 `firmware-audit-v1`。
不改写 ROUND1–ROUND7 的历史报告，不改 main 分支的研究报告，不合并 PR #1。
如果上传权限不可用，就保留本地报告并说明；不要索要 PAT。

## 6. 禁止事项

- 不从原始 boot.img / dtbo.img 重新提取。
- 不解析 vendor/odm EROFS，不提取模块或 firmware。
- 不调用 WSL、ADB、fastboot、repo、Bazel、make、clang。
- 不安装工具、不下载 EXE/DLL、不修改 Windows 执行/安全策略。
- 不编译内核、不连接或修改平板、不写任何分区。
- 不扫描其他磁盘或无关目录。
- 不把外部 Linux 项目的值覆盖到 HOS 4.3 FDT。
- 若目标 phandle 无法可靠解析，必须 fail closed，保留 UNKNOWN/TARGET_UNRESOLVED。

## 7. 完成标准

- 现有 base FDT 与 DTBO entry 8 均通过结构校验；
- entry 8 全部 fragment 均有一行记录；
- 能够确定 fragment@143 是否指向 /rootparam；不能确定则明确 UNRESOLVED；
- 对 UFS host/PHY 的 overlay 修改情况有明确、边界受限的结论；
- 关键子系统 target/GPIO 信息有证据来源；
- 三份脱敏报告提交成功或明确记录上传阻塞。

本轮完成仅是 DTBO target 与板级属性映射，不代表 UFS 已启用、panel 已选定、摄像头/音频/Wi-Fi 驱动已移植或 ACK 内核可启动。
