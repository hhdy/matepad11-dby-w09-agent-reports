# PREP11 — DBY-W09 精确 PCB 版本 BoardView / UART12 物理路径公开资料核验

- 执行者：完成 PREP04-FIX01 / PREP05 / PREP07 / PREP08 / PREP09 的同一 WorkBuddy 会话
- 技术审核：AI1
- 设备：Huawei MatePad 11 DBY-W09 / SM8250 / HOS 4.3
- 执行日期：2026-11-28
- 本轮性质：**纯离线公开资料核验 + 本地冻结件复算**。未连接平板，未执行 ADB / Fastboot / reboot / EDL，未拆机、未短接、未探测焊盘、未刷写、未重编译。

---

## 0. 判定表（本轮唯一权威结论）

| 判定字段 | 结果 | 依据强度 |
|---|---|---|
| `BOARDVIEW_MATCH` | **UNKNOWN** | 见 §3 |
| `BOARD_REVISION_PROVENANCE` | **DT_DECLARED_ONLY**（SH1DBSLM 仍只是 DT 声明值，非丝印/efuse 独立证明） | 见 §3.2 |
| `UART12_SOC_ROLE` | **CONFIRMED**：0xa90000 = SM8250 系列 debug UART（QUPV3_1 SE4，GPIO34/35） | L0 + L2，见 §4.1 |
| `UART12_TX_RX_DIRECTION` | **UNKNOWN** | 无任何来源标注方向 |
| `UART12_PAD_OR_TESTPOINT` | **UNKNOWN** | 无匹配板级资料 |
| `UART12_NET_NAME` | **UNKNOWN** | 同上 |
| `UART12_GND_REFERENCE` | **UNKNOWN** | 同上 |
| `UART12_LOGIC_LEVEL` | **UNKNOWN**（不采用 Snapdragon 通用经验猜测） | 同上 |
| `UART12_BAUD` | **115200 8N1（SM8250 惯例，L2）**，非本板证明 | 见 §4.2 |
| `UART_PHYSICAL_ACCESS` | **UNCONFIRMED（与 PREP09 相同，未改变）** | — |
| `ALTERNATIVE_LOG_PSTORE` | **COMPILED / NO_BACKEND**（可编译进内核，但 DT 无 ramoops 节点，永不实例化） | 见 §5.2 |
| `ALTERNATIVE_LOG_NETCONSOLE` | **NOT_COMPILED**（`# CONFIG_NETCONSOLE is not set`） | 见 §5.3 |
| `ALTERNATIVE_LOG_PANEL` | **FEASIBLE_ON_HW / NOT_BUILT_IN_OUR_KERNEL**（社区同板 port 正是靠面板取日志；我们的构建关掉了 VT/fbcon） | 见 §5.5 |
| `K1_OBSERVABILITY_AS_BUILT` | **单一通道**：只有 earlycon，且其硬件前提未证 | 见 §6 |

**一句话结论：**

> 公开资料里**不存在**可自由访问、且能证明与本机 `SH1DBSLM / DBY_W09_VD` 同一块 PCB 的 BoardView 或原理图，因此 GPIO34/35 的焊盘、网络名、TX/RX 方向、GND 参考点、逻辑电平**全部保持 UNKNOWN**，禁止接线。
> 与此同时，本轮找到一个比 UART12 更现实的方向：**这块板上真正被验证可用的 K1/K2 观察通道是面板（splash framebuffer + fbcon），不是 UART** —— 社区同板 Linux port 的 boot cmdline 就是 `console=tty0 fbcon=...`。而**我们的 ACK 6.18.33 构建把这套关了**（`# CONFIG_VT is not set`、候选 DTB 无 `simple-framebuffer` 节点、`# CONFIG_DRM_PANIC is not set`）。这是配置层的取舍，不是硬件未知。

---

## 1. 范围与合规

### 1.1 本轮实际执行的动作

- 读取公开网页与公开 Git 仓库（GitHub raw / API / 搜索引擎）。
- 复算本机已有冻结件：`config-used-for-build.config`、PREP06 候选 boot 镜像、候选 DTB。
- 读取本机既有交付物（PREP05/07/09）作为事实基线。

### 1.2 明确未执行（任务书禁止项逐条）

| 禁止项 | 本轮状态 |
|---|---|
| 连接平板 / ADB / Fastboot / reboot / EDL | 未执行（本轮零设备交互） |
| 拆机 / 短接 / 接探针 / 测量焊盘 | 未执行 |
| 写 GPIO / 切 pinmux / 开时钟 / 加载模块 | 未执行 |
| 购买付费 BoardView / 绕过付费墙 | 未执行（付费源仅记录存在，未访问内容） |
| 把 9008 EDL test point 当 UART 点位 | 未执行（检索到该类资料一律标记为"排除"） |
| 用 SH1DBYLM 资料替代 SH1DBSLM | 未执行 |
| 改 PREP06/PREP10 镜像、重编 kernel/DTB/DTBO、刷写 | 未执行（镜像仅只读解析） |
| 给试探接线 / 盲测电压建议 | 未给出（见 §7） |

### 1.3 证据等级定义（本报告全篇使用）

| 等级 | 含义 |
|---|---|
| **L0** | 上游/厂商源码，任何人可复算 |
| **L1** | 本机冻结件复算（配置、镜像、DTB 二进制） |
| **L2** | 公开第三方实测文档（含社区 port 源码与其实测记录） |
| **L3** | 付费/受限/来源不明资料（本轮**未访问**，不可作为判定依据） |
| **L4** | 推断（本报告不把 L4 升格为 CONFIRMED） |

---

## 2. 事实基线（不得改变）

来自 PREP08 / PREP09，本轮未重新取证，仅引用：

1. `ro.board.hardware_version = SH1DBSLM`，且 `ro.settings.use_dts_hwversion = true` → 该值是 **DT 声明值**。
2. Live FDT `/rootparam`：`hardware_version=SH1DBSLM`、`qcom,board_name=DBY_W09_VD`、`product_name=DBY-W09`、`qcom,boardid` = 四 cell `<0x8 0x2 0x0 0x6>`。
3. `/soc/qcom,qup_uart@a90000`：`status="okay"`、`compatible="qcom,msm-geni-console"`、`reg=<0xa90000 0x4000>`、QUPV3_1 SE4、pinctrl GPIO34/GPIO35 / function `qup12` / drive 2 mA。
4. HOS 运行时：GPIO34/35 `(MUX UNCLAIMED)`、SE4 时钟 enable/prepare = 0、无 `ttyMSM*`、`/proc/consoles` 为空。
5. PREP10 候选 cmdline 前缀：`ignore_loglevel earlycon=qcom_geni,0xa90000`。

---

## 3. A — 精确板版匹配

### 3.1 检索覆盖（可复核，详见 `sources.md` §B）

本轮对以下 6 类查询做了公开检索，访问日期 2026-11-28：

| # | 查询意图 | 结果 |
|---|---|---|
| 1 | `MatePad 11 DBY-W09 boardview schematic 主板 图纸` | 只有 **付费订阅** 产品（W2R 声称有 MatePad 11 的 schematic/boardview/bitmap，需 app 订阅）→ L3，未访问 |
| 2 | `"SH1DBYLM" boardview` | 无相关命中（返回无关站点） |
| 3 | `"SH1DBSLM" OR "SH1DBYLM" 华为 主板 编号` | 无相关命中（返回华为企业文档） |
| 4 | `"DBY-W09" boardview brd schematic download free` | 无 DBY-W09 命中（返回通用 boardview 工具站） |
| 5 | `DBY-W09 主板 点位图 测试点 UART 串口 引出` | 只有 **9008 EDL 短接点位** 教程（ONFIX 付费 / 东海论坛 / TrueSight 转载）→ 按任务书**排除** |
| 6 | `MatePad 11 DBY-W09 teardown mainboard PCB photo test pads` | 只有 EDL 短接点 + 泛泛拆解文（无网络名、无坐标、无 UART 标识）→ 不可用 |

补充检索（用于 §5）：`sm8250 "0xa90000" uart12 debug uart console` → 命中 3 条高价值公开源（见 §4.1），但这些是 **SoC 级**，不含本板焊盘。

**结论：** 公开、合法、可自由访问的范围内，**没有**型号明确为 `SH1DBSLM` 或 `DBY_W09_VD` 的 BoardView / schematic / 维修手册。唯一声称覆盖 "MatePad 11" 的 boardview 属付费订阅（L3），且其页面只标机型名，不标 PCB 版本字符串。

### 3.2 `SH1DBSLM` 到底证明了什么（重要澄清）

本轮发现一条独立佐证：公开社区 DBY-W09 Linux port 的设备树 `sm8250-huawei-dby-w09.dts` 第 50 行写着：

```dts
hardware_version = "SH1DBSLM";
```

其文件头自述：

> "Board identity, memory map and the UFS/USB supplies were checked against the stock HarmonyOS 4.2 device tree (extracted/merged.dts)."

同一仓库的 `dby-w09-rootparam.dtso`（ABL 覆盖层）也写 `hardware_version = "SH1DBSLM"`、`qcom,board_name = "DBY_W09_VG"`、`qcom,boardid = <0x08 0x02 0x09 0x08>`。

这说明两件事，但**没有**第三件：

- ✅ `SH1DBSLM` 不是本机孤例，而是 **HOS 4.2/4.3 的 DBY-W09 stock DT 里普遍出现的声明值**（L2）。
- ✅ 该值的来源是 **DT**，与该仓库作者的取证方式（从设备 stock DT 提取）完全一致 → 与我们 PREP08 的 `use_dts_hwversion=true` 判断互相印证。
- ❌ **没有**证明它是主板丝印、efuse 或料号。丝印层面到底印的是 `SH1DBSLM`、`SH1DBYLM` 还是别的，公开资料**无法回答**。

注意：社区 dtso 里 `board_name` 是 `DBY_W09_VG`，本机 live 是 `DBY_W09_VD`，`qcom,boardid` 也差两位（`0x08 0x02 0x09 0x08` vs `0x08 0x02 0x00 0x06`）。也就是说，**同为 DBY-W09、同报 SH1DBSLM，board_name 与 boardid 仍有差异** —— 这本身就是"机型码 ≠ 单一 PCB 修订"的直接例证。

### 3.3 同一机型内的硬件差异（追加警示）

一条公开维修工具日志（GSM-Forum，DBY-W09 EDL 会话）报告 SoC 为：

```
SoC : [Snapdragon 870] [SM8250-AC] [0x000C30E1]
```

而本机与官方规格为 SM8250（Snapdragon 865）。同类机型存在 SM8250 与 SM8250-AC 两种 die 变体，这在 MatePad 11 上意味着**同一机型码下至少有 SoC 变体级差异**。该日志为工具自动解码（L2，非权威），但足以说明：

> 以 "MatePad 11 / DBY-W09" 为粒度找来的 boardview，**在原理上**就不能保证对应本机主板；必须叠加 PCB revision 级证据。

### 3.4 A 部分结论

```
BOARDVIEW_MATCH = UNKNOWN
可信度：高（负面证据覆盖 6 类查询 + 付费源已识别）
禁止：把任何 MatePad 11 / SH1DBYLM 资料的焊盘、网络名、测试点用于本机
```

按任务书第 101 行要求：**停止在 `BOARDVIEW_MATCH = UNKNOWN`**，需要用户提供与本机主板丝印一致的高清照片，或合法取得的、标注该 PCB 版本的 BoardView。**本轮不填任何猜测值。**

---

## 4. B — GPIO34 / GPIO35 的物理网络

任务书把 B 部分门控在"精确板版资料匹配"之后。既然 A = UNKNOWN，B 的板级部分依法只能写 UNKNOWN。但为避免下一轮重复劳动，本节把**SoC 级已确认部分**与**板级未知部分**严格分层记录。

### 4.1 SoC 级：四条独立来源互相印证（L0 + L2）

| 来源 | 关键内容 | 等级 |
|---|---|---|
| 上游 `arch/arm64/boot/dts/qcom/sm8250.dtsi`（torvalds/linux master） | 第 2028 行 `uart12: serial@a90000`，`compatible="qcom,geni-debug-uart"`，`reg=<0 0xa90000 0 0x4000>`，`clocks=<&gcc GCC_QUPV3_WRAP1_S4_CLK>`，`pinctrl-0=<&qup_uart12_default>`；第 5767 行 `qup-uart12-default-state { pins = "gpio34","gpio35"; function="qup12"; }`；第 1791 行 wrapper `geniqup@ac0000` = `qupv3_id_1` | L0 |
| u-boot `board/qualcomm/debug-sm8250.config` | `CONFIG_DEBUG_UART_BASE=0xa90000`、`CONFIG_DEBUG_UART_MSM_GENI=y`、`CONFIG_DEBUG_UART_CLOCK=14745600` | L0 |
| Linux 补丁 `sm8250-edo: Set UART alias and stdout-path`（Konrad Dybcio, 2023-09-12，已合入） | `serial0 = &uart12;` + `stdout-path = "serial0:115200n8"`，注释称 "route the console to the debug uart **in the microSD slot**" | L0 |
| yecw/UniXNU-kebab `docs/bring-up.md`（OnePlus 8T，SM8250，2026-10-24 实测） | "A UART console also exists (**0xA90000, GPIO34/35, 115200 8N1**)" | L2 |

四条独立来源一致给出：**0xa90000 + GPIO34/35 = SM8250 平台的 debug UART，惯例 115200 8N1**。这使 `UART12_SOC_ROLE = CONFIRMED` 有充分依据，也解释了为何 Huawei 在 live DT 里把该节点标成 `qcom,msm-geni-console`。

同时注意第三条来源的措辞：Sony Xperia（同为 SM8250）把这条 debug UART **引到 microSD 卡槽的引脚上**。这是关键反证：

> 同一个 SoC 内的同一个 UART，**物理落点完全由板厂决定**。SoC 级确认不能推出板级焊盘。

### 4.2 TX / RX 方向为什么不能从 pinctrl 推出（技术说明）

- pinctrl 只描述 **pinmux 功能选择**（`function="qup12"`）与电气属性（drive-strength / bias），**不描述方向**。
- 2-wire UART 的 TX/RX 方向由 **GENI SE 的协议配置 + 封装内走线**决定，二者都不在 DT 里。
- 因此即便拿到匹配 boardview，也应以 **网络名（如 `UART12_TX` / `UART_DEBUG_TX`）+ 器件 pinout + 连线关系**为证；仅凭"GPIO34 编号更小"之类排序**不可**作为依据（本轮拒绝该推断）。

### 4.3 板级：逐项 UNKNOWN（详见 `gpio34_gpio35_route.md`）

| 要素 | 状态 | 原因 |
|---|---|---|
| SoC package ball / 封装引脚号 | **UNKNOWN** | 需 SM8250 datasheet 的 pin list（非公开）；TLMM 编号 ≠ 封装球号 |
| 净名（net name） | **UNKNOWN** | 需匹配 schematic / boardview |
| 焊盘 / 测试点编号 | **UNKNOWN** | 同上；公开只有 9008 EDL 短接点（已排除） |
| TX / RX 归属 | **UNKNOWN** | 见 §4.2 |
| GND 明确参考点 | **UNKNOWN** | 需匹配板级资料；电池负极/屏蔽罩属通用经验，不采纳为板级结论 |
| 逻辑电平（1.8 V / 3.3 V） | **UNKNOWN** | 需匹配电路的 IO 电源域；**禁止**按 Snapdragon 经验猜测 |

### 4.4 B 部分结论

```
UART12_SOC_ROLE        = CONFIRMED (L0×3 + L2)
UART12_TX_RX           = UNKNOWN
UART12_PAD_NET_GND_VCC = UNKNOWN
UART_PHYSICAL_ACCESS   = UNCONFIRMED   ← 与 PREP09 一致，未改善
```

**没有可安全接入的实体路径。** 在拿到 PCB revision 级证据前，UART12 不能作为 K1 的观察手段。

---

## 5. C — 替代 K1 观察通道（只评估，不实施）

依据：冻结件 `config-used-for-build.config`（sha256 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`，8 688 行，`Linux/arm64 6.18.33`，clang 22.0.1）+ PREP06 候选 boot 镜像（sha256 `aa25553170ace181bea3d2457962e0d13fff0277511ea7a7bead657e798196a8`）复算。**未重编译、未改配置。**

### 5.1 三层判定矩阵

| 通道 | ① 编译进内核 | ② DT / 运行前提 | ③ K1 阶段实际可用 |
|---|---|---|---|
| earlycon `qcom_geni` @0xa90000 | **YES**（`CONFIG_SERIAL_EARLYCON=y`、`CONFIG_SERIAL_QCOM_GENI=y`、`CONFIG_SERIAL_QCOM_GENI_CONSOLE=y`；Image 内 earlycon 表项 `name='qcom_geni'`/`compatible='qcom,geni-debug-uart'`） | **不需** DT 节点（explicit-address 路径）；但需 ABL 遗留 pinctrl+clock | **唯一通道，但前提未证**（PREP09：运行时未 mux、时钟未 enable） |
| pstore / ramoops | **YES**（`CONFIG_PSTORE=y`、`CONFIG_PSTORE_RAM=y`、`CONFIG_PSTORE_CONSOLE=y`、`CONFIG_PSTORE_PMSG=y`、`CONFIG_PSTORE_COMPRESS=y`、`PSTORE_DEFAULT_KMSG_BYTES=10240`；Image 内 `ramoops` 58 次 / `pstore` 121 次） | **NO**：候选 DTB `/reserved-memory` 18 个直接子节点，**全部**是 `memory@*`（唯一带 compatible 的是 `qcom,cmd-db`），**`ramoops` 节点数 = 0**；候选 DTB 全文 `ramoops` 字符串 0 次；`/chosen` 属性 0 个（无 bootargs） | **不可用**（驱动在，后端永不注册） |
| pstore console（`console=pstore`） | YES | 同上，无后端 | **不可用** |
| netconsole | **NO**（`# CONFIG_NETCONSOLE is not set`） | — | **不可用** |
| USB serial console | **NO**（`# CONFIG_U_SERIAL_CONSOLE is not set`；`CONFIG_USB_SERIAL=m` 仅 ftdi，模块须用户态加载） | — | **不可用**（K1 无用户态、无模块加载） |
| 面板 console（simple-framebuffer + fbcon，`console=tty0`） | **NO**（`# CONFIG_VT is not set`；`# CONFIG_DRM_PANIC is not set`） | 候选 DTB **无** `simple-framebuffer` 节点 | **不可用（当前构建）**，但**硬件上可行**，见 §5.5 |
| `last_kmsg` / Android ram_console | **NO**（`CONFIG_VT` 无关，但无 `ANDROID_RAM_CONSOLE` 类符号） | — | **不可用** |
| 分区级 boot log（abl_log / kernel_log） | 与本内核无关（由 ABL/厂商写入） | 取决于本机是否存在此分区 | **UNVERIFIED**，见 §5.6 |

补充两条硬事实：

- **arm64 根本没有 `CONFIG_EARLY_PRINTK` 这个符号**。已核对 ACK 精确提交 `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9` 的 `arch/arm64/Kconfig.debug`，全文件只有 `PID_IN_CONTEXTIDR`、`DEBUG_EFI`、`ARM64_RELOC_TEST` 三项。所以 `.config` 里"没有 EARLY_PRINTK"不是缺陷，arm64 的早期打印机制就是 `CONFIG_SERIAL_EARLYCON` + `OF_EARLYCON_DECLARE`。
- `CONFIG_PANIC_ON_OOPS=y` 且 `CONFIG_PANIC_TIMEOUT=-1` → 任何 oops 立刻 panic，且**永不自动重启**，设备停在原地。这对 K1 取证是负面组合：既没有持久化后端，又不会自己重启，只能人工断电，而断电会清掉任何 RAM 缓冲。

### 5.2 pstore / ramoops：为什么"编译了"等于"不可用"

ramoops 的绑定链条是：DT 节点（`compatible = "ramoops"`）→ `platform_driver` probe → `pstore` 后端注册 → `PSTORE_CONSOLE` / `PMSG` 才有落点。

已用 ACK 源码核对：

- `fs/pstore/ram.c` 的 `dt_match[]` 只有 `{ .compatible = "ramoops" }`；
- `fs/pstore/Kconfig` 中 `config PSTORE_RAM` 描述为 "Log panic/oops to a RAM buffer" —— 即 ramoops 驱动本体；
- `config PSTORE_CONSOLE` 描述为 "pstore will log all kernel messages, even if no oops or panic happened"，但依赖 `PSTORE` 后端。

候选 DTB 里 `ramoops` 节点为 0 → 该 driver 的 probe 永远不会被调用 → 后端不存在 → 两条 pstore 通道同时死。PREP07 已得出同一结论，本轮用二进制复算再次确认（并纠正了一处可能的误读：`ramoops` 字符串出现在 **kernel 段 58 次**，在 **DTB 段 0 次**，在 ramdisk 段 0 次）。

附带损失：PREP07 已记录 **stock DTB（slot0）有 37 个 reserved-memory 子节点**，含 `res_xbl_uefi_log_region`、`disp_rdump_region`、`mem_dump_region`、`kerneldump`；而候选 DTB 只剩 18 个 `memory@*`。也就是说，**为了过 ABL/DTB 闸门而拼的候选 DTB，把厂商的 dump 保留区一起裁掉了**。即便将来加 ramoops，也应在保留区布局上与 stock 对齐，否则可能踩到 ABL 或固件的预期。

### 5.3 netconsole

`# CONFIG_NETCONSOLE is not set`，无讨论空间。即使开启，K1 阶段没有网络栈、没有 MAC/PHY 驱动，netconsole 也只能在 K3 之后才有意义。

### 5.4 USB / USB-C

- `CONFIG_USB_SERIAL=m`：只有 `ftdi_sio` 编成模块（`CONFIG_USB_SERIAL_FTDI_SIO=m`），其余全 not set。模块需要用户态 `insmod`，K1 没有。
- `# CONFIG_U_SERIAL_CONSOLE is not set`：gadget 串口控制台关闭，无法把 USB-C 当 CDC-ACM console。
- 结论：K1 阶段 USB 口只能供电/充电，不是日志通道。

### 5.5 面板 console —— 本轮最有价值的发现

社区同板 port（`svesnav/linux-dby-w09`，mainline Linux 7.0）的 `boot-cmdline.txt` 全文只有一行：

```
clk_ignore_unused pd_ignore_unused console=tty0 fbcon=font:TER16x32 loglevel=7 ignore_loglevel panic=0 rdinit=/init
```

其 DTS 里对应的 framebuffer 是：

```dts
/* The bootloader leaves the Huawei logo scanning out of this buffer. */
framebuffer: framebuffer@9c000000 {
    compatible = "simple-framebuffer";
    reg = <0x0 0x9c000000 0x0 0x2300000>;
    width = <1600>; height = <2560>; stride = <(1600 * 4)>;
```

互相印证：kebab（OnePlus 8T，同 SM8250）的 bring-up 记录里，"Debug channel without UART"一节说的正是用 **0x9C000000 splash framebuffer** 画日志，并明确写 "The panel is enough"。两台不同厂商的 SM8250 设备，**同一个 splash 基址 0x9C000000**，说明这是 Qualcomm 平台的通用 splash 区域，`DBY-W09` 的 bootloader 也留下了它（社区 port 能显示即证明）。

**这对我们意味着什么：**

| 项目 | 现状 | 说明 |
|---|---|---|
| 硬件可行性 | **CONFIRMED（L2）** | 同板社区 port 已实测可显示内核日志 |
| 我们的构建 | **不可用** | `# CONFIG_VT is not set` → 无 `tty0`/fbcon；`# CONFIG_DRM_PANIC is not set` → 无 panic 上屏 |
| 我们的候选 DTB | **不可用** | 无 `simple-framebuffer` 节点（`/chosen` 0 属性、顶层节点无 framebuffer） |
| 补救代价 | **一次重编译 + 一处 DTB 改动** | 开 `CONFIG_VT`/`CONFIG_FRAMEBUFFER_CONSOLE`（或 `DRM_SIMPLEDRM`）+ DTB 加 `simple-framebuffer@9c000000` + cmdline 加 `console=tty0` |

注意：这属于**改动构建**，本轮任务书明确禁止，因此**只作为建议上交 AI1**，未实施。它的价值在于：**把"K1 无观察通道"从硬件死局降级为配置取舍**。

### 5.6 分区级 boot log（新增待核项）

kebab bring-up 文档记录该机有 `abl_log`(16 MiB，ABL 自己的启动日志) 与 `kernel_log`(32 MiB，上一次内核日志缓冲)。若 DBY-W09 也有同类分区，那它就是**不需要改内核、不需要 UART**的事后取证通道（HOS 起来后 root 只读 `dd` 出来即可）。

本机现状：

- 已有分区清单（R155 只读采集）共 18 项：`abl / boot / dtbo / erecovery* / ramdisk / recovery* / vbmeta* / xbl / xbl_config`，**不含** `abl_log`、`kernel_log`。
- 但该清单是**面向启动链的筛选子集**，不是 `/dev/block/by-name` 全量，因此**不能据此断言本机没有这两个分区**。

→ 判定 `UNVERIFIED`。核实成本极低（一次只读 `ls -l /dev/block/by-name`），但本轮禁止 ADB，故留作下一轮候选动作。

### 5.7 C 部分结论

```
ALTERNATIVE_LOG_PSTORE     = COMPILED / NO_BACKEND
ALTERNATIVE_LOG_NETCONSOLE = NOT_COMPILED
ALTERNATIVE_LOG_USB        = NOT_COMPILED
ALTERNATIVE_LOG_PANEL      = FEASIBLE_ON_HW / NOT_BUILT_IN_OUR_KERNEL
ALTERNATIVE_LOG_PARTITION = UNVERIFIED (cheap to check, read-only)
K1_OBSERVABILITY_AS_BUILT  = earlycon 单通道，且硬件前提未证
```

---

## 6. 决策建议（提交 AI1 裁定，本轮不执行）

按"投入产出 / 风险"排序：

1. **停止对 UART12 物理接入的继续投入。**
   理由：A = UNKNOWN 且公开范围内无解；即使拿到 boardview，仍要面对"GPIO34/35 运行时未 mux、SE4 时钟未 enable"这两个 ABL 遗留状态未知的问题（PREP09）。**"先有眼睛再有手"这条原则在这里的结论是：眼睛不在这条线上。"**

2. **把"面板 console"作为 K1 的首选观察通道立项评估。**
   这是本轮唯一被实测证明在本板上可用的通道（L2，同板社区 port）。所需改动全部在离线侧：内核配置 + DTB 一个节点 + cmdline 一个 token。**它不依赖任何未证的硬件前提**。

3. **只读核实日志分区（低成本、零风险）。**
   下一轮若允许 ADB，仅 `ls -l /dev/block/by-name` + `stat` 即可判定是否存在 `abl_log` / `kernel_log` 类分区。存在则等于白送一条事后取证通道。

4. **补 PCB revision 级证据，但改由用户侧提供。**
   任务书指定的正解是：与本机主板丝印一致的高清照片（重点是 SoC 周边、屏蔽罩边缘、丝印 `SH1DB…` 字样区域），或合法取得的对应 BoardView。拿到后本轮 §4.3 的 6 个 UNKNOWN 才可能逐项转正。

5. **不建议**：以 `SH1DBYLM` 或任意 "MatePad 11" boardview 作为替代证据；以 9008 短接点当 UART；按 1.8 V/3.3 V 经验盲测。

---

## 7. 限制与不确定性（必须随报告一起读）

1. `SH1DBSLM` 依旧只是 **DT 声明值**。社区 dtso 里同报 `SH1DBSLM` 但 `board_name=DBY_W09_VG`、`boardid=0x08 0x02 0x09 0x08`，与本机 `DBY_W09_VD` / `0x08 0x02 0x00 0x06` 不同 → 该字符串**不足以区分 PCB 修订**。
2. 公开检索的"未找到"只代表**在 2026-11-28 用列出的 6 类查询、在可访问的公开索引里未找到**，不等于绝对不存在。付费库（W2R 等）可能确实有，但本轮按规则未访问、也不作为证据。
3. 本报告对 `UART12_SOC_ROLE` 的确认是 **SoC 级**；本板的物理落点仍完全未知。**SoC 级确认不得被引用为"可以接线"的依据。**
4. 候选 DTB 的 `/chosen` 为空、无 bootargs —— 说明 cmdline 全在 boot header 里，这与 PREP10 的改法自洽；但也意味着 DTB 侧无法通过 `/chosen/bootargs` 补参数。
5. `PSTORE_DEFAULT_KMSG_BYTES=10240`（10 KiB）：即便将来补上 ramoops，单条 record 只有 10 KiB，长日志会被截断，需要同时调大 `record-size`。
6. 本轮未复核 PREP08 报告里 `MatePad-11-SH1DBYLM` 标签的**原始页面 URL**（该字符串来自更早轮次记录，本轮 6 类查询未再命中任何显示该标签的公开页面）。无论其来源如何，字符串层面与本机不一致，结论不变。

---

## 8. 附录：复算命令（任何人可重跑）

```bash
# 1) 冻结配置
sha256sum prep04/work/config-used-for-build.config
# 期望 0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15

grep -E "PSTORE|NETCONSOLE|SERIAL_EARLYCON|SERIAL_QCOM_GENI|USB_SERIAL=m|U_SERIAL_CONSOLE|CONFIG_VT|DRM_PANIC" \
     prep04/work/config-used-for-build.config

# 2) 候选镜像分段 + ramoops 落点
python - <<'PY'
import struct
p="prep07/work/prep06/PREP06_K1_EARLYCON_PREVIEW/dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img"
b=open(p,'rb').read()
ks=struct.unpack_from("<I",b,8)[0]; rs=struct.unpack_from("<I",b,16)[0]; ds=struct.unpack_from("<I",b,1648)[0]
K=b[4096:4096+ks]
R=b[44826624:44826624+rs]
D=b[45346816:45346816+ds]
for n,s in (("KERNEL",K),("RAMDISK",R),("DTB",D)):
    print(n, len(s), "ramoops=", s.count(b"ramoops"), "pstore=", s.count(b"pstore"))
# 期望 KERNEL 44820992 ramoops=58 pstore=121 / RAMDISK ramoops=0 / DTB ramoops=0
PY

# 3) 候选 DTB 的 reserved-memory 与 /chosen
#    使用 r156/fdt156.py 解析（纯 Python），结果：节点 905，reserved-memory 18 子节点全 memory@*，ramoops 0，/chosen 0 属性
```

---

## 9. 本轮交付物清单

| 文件 | 内容 |
|---|---|
| `PREP11_REPORT.md` | 本文件，A/B/C 判定与依据 |
| `sources.md` | 全部来源 URL、版本、访问日期、引用位置 + 负面检索日志 |
| `gpio34_gpio35_route.md` | SoC 级已确认项 / 板级 UNKNOWN 逐项说明（无匹配证据，不填猜测值） |
| `alternative_k1_logging.md` | 三层矩阵 + 逐通道配置证据 + 面板 console 建议 |
| `SHA256SUMS.txt` | 上述 4 份文本的 SHA-256 |
