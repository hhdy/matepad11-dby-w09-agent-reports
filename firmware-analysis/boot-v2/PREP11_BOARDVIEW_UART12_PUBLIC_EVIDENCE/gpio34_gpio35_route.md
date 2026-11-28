# gpio34_gpio35_route.md — GPIO34 / GPIO35 物理网络追踪

**前置门控：** 任务书要求「只有在精确板版资料匹配的情况下」才能继续追踪 B 部分。
本轮 `BOARDVIEW_MATCH = UNKNOWN`（见 `PREP11_REPORT.md` §3）。
因此按任务书规定：

> **本文件的主表全部为 UNKNOWN，不填任何猜测值。**

为避免下一轮重复劳动，另设 §2「SoC 级已确认（不可用于接线）」单独记录已可复算的 SoC 级事实，并用醒目标注与板级隔离。

---

## 1. 主表：板级物理路径（本机 SH1DBSLM / DBY_W09_VD）

### 1.1 目标链条

```
SoC 封装球号  →  板级净名(net)  →  焊盘/测试点  →  GND 参考点  →  IO 电平
   (ball)         (net name)      (pad / TP)        (GND)        (V)
```

### 1.2 逐项状态

| 环节 | 状态 | 已知内容 | 缺失的证据 | 为什么不能推断 |
|---|---|---|---|---|
| SoC package ball / 封装引脚号 | **UNKNOWN** | TLMM 逻辑编号为 GPIO34 / GPIO35（L0，上游 DTS） | SM8250 datasheet 的 pin list / package ball map | TLMM 逻辑 GPIO 编号 ≠ 封装球号；两者映射只在 SoC datasheet 里，非公开。任何"GPIO34 对应第 N 球"的说法都需要 datasheet 页码 |
| 板级净名（net name） | **UNKNOWN** | — | 匹配本 PCB 版本的 schematic / boardview，需给出 net 名如 `UART12_TX` / `DBG_UART_RX` | 无匹配资料。公开检索到的 DBY-W09 资料全是 9008 EDL 短接点（任务书明令排除） |
| 焊盘 / 测试点编号（pad / TP） | **UNKNOWN** | — | 匹配 boardview 的坐标或 TP 编号（如 `TP1203`） | 同上。ONFIX 付费短接图仅覆盖 EDL，且属 L3 未访问 |
| TX / RX 归属 | **UNKNOWN** | 只知道两脚功能为 `qup12`（双向复用） | 明确网络标注 + 器件 pinout + 连线关系 | pinctrl 只做 mux，不表达方向；方向由 GENI SE 协议配置与封装内走线决定，DT 里没有。**拒绝**用"编号小的是 TX"之类排序规则推断 |
| GND 明确参考点 | **UNKNOWN** | 板上有电池负极/屏蔽罩等通用接地点 | 匹配资料标出的、与 UART 地回路同一参考的测试点 | "电池负极 = GND" 属通用经验（L4），不是本板级结论；在未确认参考点前给接线建议会引入地环路/电位差风险 |
| 逻辑电平（1.8 V / 3.3 V） | **UNKNOWN** | — | 匹配电路中该 IO 电源域（如 `VREG_Lx_1P8`）的实测/标注 | Snapdragon 平台既有 1.8 V 也有可变电平域；**禁止**按经验猜测。接错电平可直接损伤 SoC 引脚 |

### 1.3 结论

```
UART12_TX_RX_DIRECTION = UNKNOWN
UART12_PAD_OR_TESTPOINT = UNKNOWN
UART12_NET_NAME         = UNKNOWN
UART12_GND_REFERENCE    = UNKNOWN
UART12_LOGIC_LEVEL      = UNKNOWN
UART_PHYSICAL_ACCESS    = UNCONFIRMED
```

**因此在当前证据下不存在"可安全接入"的实体路径，不得接线、不得探测焊盘、不得盲测电压。**

---

## 2. SoC 级已确认事实（⚠️ 仅用于理解，禁止用于接线）

> 本节内容全部是 **SoC 级**（SM8250 平台通用），**不指向本机任何一块具体焊盘**。
> 保留本节的目的：一旦将来拿到匹配 boardview，这些是"要找什么"的检索关键词（`qup12` / `UART12` / `0xa90000` / `gpio34` / `gpio35`）。

| 事实 | 值 | 来源 | 等级 |
|---|---|---|---|
| UART12 MMIO 基址 | `0xa90000`，长度 `0x4000` | 上游 `sm8250.dtsi` L2028；u-boot `debug-sm8250.config` | L0 |
| 所属 QUP wrapper | QUPV3_1，`geniqup@ac0000`（`qupv3_id_1`） | 上游 `sm8250.dtsi` L1791 | L0 |
| SE 实例 | SE4（`GCC_QUPV3_WRAP1_S4_CLK`） | 同上 L2032 | L0 |
| 引脚集合 | `gpio34`、`gpio35` | 上游 `sm8250.dtsi` L5767 | L0 |
| pinmux function | `qup12` | 同上 | L0 |
| 2-wire 形态 | 无 CTS/RTS（仅两脚） | 同上（pins 只有两个） | L0 |
| 惯例波特率 | **115200 8N1** | Sony edo `stdout-path="serial0:115200n8"`；kebab 实测记录 "115200 8N1" | L0 + L2 |
| SE 输入时钟（本机实测） | 7,372,800 Hz = 115200 × 64 | PREP09 `uart12_clock_state.txt` | L1 |
| 平台惯例源时钟（u-boot） | 14,745,600 Hz = 115200 × 128 | u-boot `debug-sm8250.config` | L0 |

### 2.1 波特率结论的准确表述

- 本机 `gcc_qupv3_wrap1_s4_clk` 的 rate 为 7,372,800 Hz，这是 **SE 输入时钟**，**不是** baud rate。
- 115200 8N1 是 **SM8250 平台惯例**（三条独立来源），但**本机 ABL/内核实际使用的 baud 未被证明**（开机后无任何 console 输出可观测，无法反推）。
- 因此：`UART12_BAUD = 115200 8N1（平台惯例，L2）`，标注为**待本板验证**，不得写成 CONFIRMED。

### 2.2 三个"已知但不能用"的反例（提醒下一轮别走偏）

1. **Sony Xperia（同为 SM8250）**把这条 debug UART 引到 **microSD 卡槽**的引脚上（L0，`sm8250-edo` 提交说明原文 "the debug uart in the microSD slot"）。
2. **OnePlus 8T（SM8250）**作者确认存在该 UART，但"the hardware adapter was not available"，最终靠 **面板 framebuffer** 完成 bring-up（L2）。
3. **本机 DBY-W09 的社区 port** 的 boot cmdline 用 `console=tty0`（面板），**通篇没有 uart12**（L2）。

→ 三台 SM8250 设备，三个不同的物理答案。**这就是为什么本表必须停在 UNKNOWN。**

---

## 3. 要把本表转正，最小需要什么

按可获得性排序：

| 优先级 | 需要的材料 | 能转正哪些行 |
|---|---|---|
| 1 | 本机主板高清照片（丝印 `SH1DBS…` 区域 + SoC 周边 + 屏蔽罩边缘 + 排线座附近），需能读清丝印与丝印旁的 TP 编号 | 可能转正 pad/TP、GND（若照片含标注）；仍需板级 net 表才能定 TX/RX |
| 2 | 合法取得的、标注该 PCB 版本的 BoardView / schematic（可搜索 `qup12`、`UART12`、`0xa90000`、`gpio34`） | 可转正 net、pad、TX/RX、GND；电平需该图含电源域 |
| 3 | 官方 service manual（含 IO 电源域表） | 可转正 logic level |
| 4 | 示波器/逻辑分析仪 + 已确认焊盘（**须在 1、2 之后**） | 可实测确认 baud 与电平 |

**在 1 或 2 到手之前，任何"应该就是这个点"的说法都是猜测，不予采纳。**
