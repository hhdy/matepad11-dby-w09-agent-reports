# PREP14 — ROUND155 既有 XBL / xbl_config 的 UART12 交接专项离线审计

**签发者：AI1（ChatGPT）**  
**执行者：WorkBuddy Agent（本地离线）**  
**项目：Huawei MatePad 11 DBY-W09 / SM8250 / ACK Android 17 6.18.33**  
**任务类型：一次性、严格限界的静态固件审计。不是设备测试，不是新一轮设备取证。**

## 0. 先读：本轮目标

PREP12 已完成显示路径证据收集。PREP13 已完成 ABL UART12 专项分析。AI1 已审核 PREP13：

- PREP13 ZIP 完整性与内部四份报告哈希全部 PASS；
- `console=NULL` 不足以证明已注册的 `CON_BOOT` earlycon 必然静默；
- ABL 中的定向扫描未发现直接 QUP/GENI/TLMM/GCC 编程证据，但这不是“整个 ABL 不可能通过通用固件 API 操作硬件”的证明；
- ABL→kernel 入口时 SE4 时钟 / power domain / GPIO34/35 mux / GENI protocol 仍未知；
- `K1_UART12_ROUTE = HOLD`，不是 BLOCKED；
- framebuffer 路线仍 BLOCKED，不得混入本任务。

PREP14 只解决一个问题：**ROUND155 已经捕获的 XBL 与 xbl_config 是否设置/保持 QUPV3_1 GENI SE4（UART12）所需的硬件状态，及其交给 ABL 时的可追溯性。**

完成 PREP14 后，AI1 直接决策 UART12 路线。PREP14 是本方向批准的最后一轮 Agent 静态审计。不得自行开 PREP15 或扩大到无边界固件搜索。

## 1. 不依赖旧聊天的项目事实

### 1.1 设备和目标

- 设备：Huawei MatePad 11 DBY-W09，SoC SM8250 / Snapdragon 865，A-only。
- 当前 donor/reference firmware：HOS 4.3.0.196(C00E100)，Android 12；它只用于识别设备 boot chain，不是 Android 17 目标系统。
- 内核：ACK `android17-6.18.33_r00`。
- 固定源码 commit：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`。
- 构建 source tree SHA：`c56d93eafa35057d65176db6594d67d5144868a0`。
- Kleaf target：`//common:dby_w09`。
- 冻结 Image SHA：`f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21`。
- 已有成功 build，但本任务严禁重编译或改动。

### 1.2 设备 UART12 拓扑（PREP09/PREP11 已确认的 SoC 层事实）

| 项 | 身份 |
|---|---|
| GENI UART MMIO | `0xa90000` |
| QUPV3_1 wrapper | `0xac0000` |
| SE | QUPV3_1 GENI SE4 |
| GCC/QUP clock 名称 | `gcc_qupv3_wrap1_s4`（及其 parent / interconnect 依赖） |
| GPIO | GPIO34 / GPIO35 |
| pin function | `qup12` |
| TLMM base（live FDT） | `0x0f000000` |
| live FDT node | `/soc/qcom,qup_uart@a90000`，compatible `qcom,msm-geni-console`，status okay |
| ABL entry-time hardware state | 尚无直接证据 |

PCB 的 UART12 TX/RX pad、GND、逻辑电平和物理可接入性仍 UNKNOWN；不得接线、拆机或探针。

### 1.3 PREP12/PREP13 决策背景

- PREP12 fresh live FDT SHA：`dc0ab259c800d52946d4a3d633fe1546430895d2878054d0376d428a135da52d`。
- PREP12 确认 splash framebuffer 物理区域 `0x9c000000` / `0x2300000`，但像素 format UNKNOWN；因此 framebuffer K1 candidate 不制作。
- PREP13 精确 ACK earlycon 路径：`earlycon=qcom_geni,0xa90000` 为显式 MMIO 形式，不依赖 DT compatible/status；`qcom_geni_serial_earlycon_setup()` 会读 GENI protocol 并配置 FIFO/UART，但不主动 enable clock 或 pinmux。
- `ignore_loglevel` 可覆盖 `loglevel=0` 的 printk 等级过滤。
- `console=NULL` 的大小写与 console preferred 处理不能简单推导为“earlycon 必然停止”。成功注册的 earlycon 可能在无 real console 接管时继续存在。
- 所以此处决定 UART K1 路线仍 HOLD，唯一硬件核心未知在 XBL/更早阶段的 SE4 时钟 / GPIO mux / power 状态。

## 2. 仅允许使用的本地输入：ROUND155 已有副本

ROUND155 的原始只读捕获报告（公开报告仓库已有文本记录）：

`firmware-analysis/round155/WORKBUDDY_A_ROUND155_READONLY_BOOTCHAIN_PARTITION_CAPTURE_REPORT.md`

该报告记录 18/18 分区完成精确字节数、主机 SHA256、设备端第二次 SHA256、主机回读 SHA256 核验。XBL 两项为：

| 本地文件/分区 | 预期大小 | 预期 SHA-256 |
|---|---:|---|
| `xbl` | 4,018,176 B | `7819d2af26438a817600080dc2340006fd3b9a5b6ea7a60509f3faf2e5d201c2` |
| `xbl_config` | 4,325,376 B | `5c63be1b477669a4f693dd98ad31954884a0907ebf1ae94b5c4a36ef9a34aa5c` |

已知容器身份（只作交叉校验，必须重新验证）：
- `xbl`：ELF 64-bit AArch64 EXEC，无 section headers，15 个 LOAD segments；版本字符串 `BOOT.XF.3.2-00363-SM8250-1`。
- `xbl_config`：ELF 64-bit ARM EXEC，无 section headers，4 个 LOAD segments。
- XBL 既有 strings 包含 `/chosen`、`/reserved-memory/splash_region`、`LcdkitInitPanelInfo:uBoardId %u hw_get_dts_info failed`、DDR MemoryMap config 等。

**输入处理规则：**
1. 只在当前 Agent 本地已有目录 / 既有 ROUND155 备份副本中查找这两个文件。
2. 找到后先记录绝对路径（仅写报告内部，不上传隐私路径）、大小与 SHA256；必须精确匹配上表。
3. 任一文件缺失或哈希不符：立即停止对应分析，写 `INPUT_MISSING_OR_MISMATCH`，不得连接平板补读，不得从其他来源猜测/替代。
4. 不需要也不允许再读取 ABL、设备分区或其他固件分区；ABL 的已知身份仅作为关联上下文：解压 PE payload 2,597,064 B，SHA `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`。
5. 不将原始 XBL / xbl_config 二进制放入交付 ZIP 或公开仓库。

## 3. A — 容器 / 段 / firmware volume 清点

对精确哈希输入完成：

- ELF header、entry、program headers、LOAD ranges、权限、align、段重叠与 file/memory size 校验；
- 检查 ELF segment 内是否嵌套 Qualcomm image header、UEFI firmware volume (`_FVH`)、FFS、GUID-defined compressed section、LZMA/LZ4/GZIP 等封装；
- 对每个可安全解析的 FV/FFS：列 GUID、文件类型、section type、压缩算法、压缩/解压尺寸和解压 payload SHA256；
- 列出所有模块/载荷清单，尤其是 Clock、GPIO/TLMM、QUP、GENI、Serial/Debug、DEVCFG、PMIC、Power Domain、UEFI DXE/PEI 类模块；
- 不能识别的压缩段或 module 记录 offset、magic、长度和失败原因，不得默默跳过后声称全镜像扫描完整。

不运行固件，不调用设备，不执行 extracted payload。

## 4. B — QUPV3_1 SE4 / UART12 时钟审计

目标定位：`gcc_qupv3_wrap1_s4` 与其 parent / branch clock / QUP wrapper。分析要求：

1. 以 SoC SM8250 的已知 register map 为线索，但必须先在 XBL/XBL_CONFIG 中定位时钟驱动代码或配置表，不能只扫描字符串。
2. 对直接寄存器操作，追踪基址取得方式、offset、bit mask、寄存器写入值、执行函数和调用路径。
3. 对 clock protocol / HAL API / clock driver，追踪 `Clock_Enable/Disable/SetClockFrequency` 或同义函数的调用参数，识别 SE4 对应 clock ID，追踪 parent dependency 和 disable/cleanup 路径。
4. 如果使用 table-driven configuration：给出 table entry、index、调用者和 runtime condition；若只有某个 `QUPV3_1_SE4` 字符串，没有配置写入或实际 API 调用，不得判定 clock enabled。
5. 核实 XBL 在移交 ABL 前是否可能全局关闭 clocks、清理未使用时钟、切换 boot/performance mode；如调用链不完整或经函数指针无法闭合，必须保留 UNKNOWN。
6. 分开记录“XBL 曾 enable 过”“XBL 移交前仍 enabled”“ABL 移交 kernel 时仍 enabled”三种不同结论；前者不能替代后两者。

## 5. C — GPIO34/35 / qup12 pinmux 审计

目标：GPIO34、GPIO35 的 TLMM mux、pull、drive strength、方向与 QUP12 function。

1. 定位 TLMM driver / GPIO HAL / pinctrl API / table-driven pin configuration；不能只依靠字符串 grep。
2. 查明 GPIO34/35 的具体 mux function selector 与 TLMM register offset；偏移和值必须由本地 SoC 配置或 XBL 表项佐证，不得凭其他机型照搬。
3. 追踪 QUPV3_1 SE4 UART12 的 GPIO mux 设置调用路径，以及后续 reset/default/sleep/deinit/ExitBootServices 时是否还原为 GPIO/input/安全态。
4. 分开记录“曾配置 qup12”“移交 ABL 时仍为 qup12”“移交内核时仍为 qup12”；无读取/未恢复状态的直接证据时保持 UNKNOWN。
5. 若 XBL_CONFIG 保存 board-specific GPIO config，比较其 board identity / SKU / platform 条件，确认是否适用于 DBY-W09 当前板版；不可把其他 board variant 配置当成本机。

## 6. D — GENI SE4 protocol、power domain 与调试 UART 区分

1. 查明 SE4 的 GENI firmware/protocol 初始化路径。确定 XBL 是否加载/配置 SE firmware，何时设置 UART protocol，以及是否在 ABL 入口时保持。
2. 核实相关 power domain、interconnect、regulator / CX/MX vote 的调用与释放；分开区分 power collapse prevent、clock enable 和 pinmux。
3. 如果 XBL 有自己的 UEFI debug UART，必须判断它是否就是 `0xa90000` / SE4 / GPIO34/35，还是另一条 UART。不能将“XBL 有串口日志”推断为“目标 UART12 可用”。
4. 若 XBL 通过共用 SerialIo/DebugPort protocol 或动态 base / PCD / device config 选择 UART，追踪实际实例 ID 和物理 MMIO base；未能映射到 0xa90000 时仍 UNKNOWN。
5. 对任何 global ExitBootServices / ReadyToBoot / DXE shutdown / handoff callback，检查是否影响 SE4 clock/power/GPIO；如果实际调用链无法解析，不可声称状态保持。

## 7. E — XBL_CONFIG 专项

- 解析 `xbl_config` 结构与 board-specific 配置项；识别是否包含 UART12/GENI/QUP/clock/GPIO 的默认态或覆盖项。
- 将配置中的 board ID / platform ID / SKU / revision 与 PREP08/PREP09 本机证据对照：本机 `DBY_W09_VD`、boardid `<0x08 0x02 0x00 0x06>`；社区 `VG` 配置不适用。
- 任何 variant 无法确认时写 `VARIANT_MATCH = UNKNOWN`，不允许择取“看起来像”的 config。
- 检查 XBL 是否使用 xbl_config 内的 generic clock/pinmux tables；如果是，追踪 table index 到目标 SE4 / GPIO34/35。

## 8. F — 与 PREP13 / ACK 的 handoff 联合判定

最终必须分别给出以下字段，不要只给一项总判断：

```text
XBL_INPUT_IDENTITY              = PASS | FAIL
XBL_CONTAINER_PARSE             = PASS | PARTIAL | FAIL
XBL_SE4_CLOCK_CONFIGURED        = YES | NO | UNKNOWN
XBL_SE4_CLOCK_AT_ABL_HANDOFF    = ON | OFF | UNKNOWN
XBL_SE4_POWER_AT_ABL_HANDOFF    = ON | OFF | UNKNOWN
XBL_GPIO34_35_QUP12_CONFIGURED  = YES | NO | UNKNOWN
XBL_GPIO34_35_AT_ABL_HANDOFF    = QUP12 | OTHER | UNKNOWN
XBL_GENI_SE4_UART_PROTO         = UART | OTHER | UNKNOWN
ABL_TO_KERNEL_STATE_PRESERVED   = YES | NO | UNKNOWN
UART12_EARLYCON_K1_ROUTE        = PLAUSIBLE | BLOCKED | HOLD
```

每个字段必须引用具体 file offset / ELF VA / module GUID / table index / 指令片段或明确说明只有字符串线索。不要用 XBL 内出现 UART 字样、出现 `Lcdkit` 或存在 clock driver 这种一般事实填 YES。

判定规则：
- `PLAUSIBLE` 需要至少有：SE4 正确 clock 在 handoff 前后 ON 的可追溯证据、GPIO34/35 的 qup12 mux 保持证据、GENI protocol 是 UART，以及 ABL→kernel 没有关闭这些资源的合理证据。
- `BLOCKED` 需要直接发现 XBL 或紧接 handoff 的路径将目标资源关闭 / 清除 / 配置成非 UART，且无后续恢复路径。
- 其余一律 `HOLD`。

即使 PLAUSIBLE，也只是有理由准备 K1 host-side candidate，不代表可刷写或实机安全。

## 9. 禁止事项

- 不连接平板、不执行 ADB / fastboot / OEM / EDL；不运行 `fastboot oem uart` 或 `fastboot oem himntn`。
- 不重启、不临时启动、不刷写、不解锁、不擦除、不写任何分区。
- 不读取新的分区内容，不重新 dump xbl / xbl_config，不进行全 UFS dump。
- 不接线、不拆机、不探测 UART pad。
- 不修改源码、config、DTS、DTB、DTBO、boot、ramdisk、Image 或任何固件。
- 不编译内核，不生成启动镜像。
- 不因为缺失输入而转向其他公开固件或其他机型镜像替代。
- 不启动 PREP15，不向用户索要额外的一般性调查。

## 10. 输出与交付

输出目录：`PREP14_XBL_UART_HANDOFF_AUDIT/`

必须包含：
1. `PREP14_REPORT.md` — 总结、判定字段、唯一结论；
2. `xbl_container_inventory.md` — ELF/FV/FFS/压缩模块清单；
3. `xbl_se4_clock_trace.md` — clock/power API、寄存器和调用链；
4. `xbl_gpio34_35_pinmux_trace.md` — TLMM mux 设置、恢复和 handoff；
5. `xbl_config_variant_audit.md` — board variant 与 config 关联；
6. `abl_xbl_kernel_handoff_matrix.md` — XBL、ABL、ACK earlycon 状态对照；
7. `SHA256SUMS.txt` — 所有报告文件哈希；
8. `tools/` 下本轮自写脚本和准确命令/工具版本（可复现所执行扫描）。

打包成 `PREP14_XBL_UART_HANDOFF_AUDIT.zip`，回传给用户/ChatGPT 审核。ZIP 不得包含原始 xbl / xbl_config / ABL / 任何 boot chain 二进制、设备数据、密钥或隐私信息。报告可另行提交 GitHub，但 GitHub 不是交付前提。

若输入缺失、hash mismatch、ELF/FV 无法解析或调用链无法闭合，仍交付简短报告和准确 stop reason；不延展任务。

## 11. 执行完成后的停止条件

完成 ZIP、哈希清单与报告后立即停止，不继续自发探索。回报内容只需说明：输入身份、发现的最强直接证据、上述字段、K1 建议以及 ZIP SHA-256。等待 AI1 最终审核。