# sources.md — PREP11 来源清单

- 访问日期：**2026-11-28**（全部来源均为当日检索/抓取）
- 抓取方式：`raw.githubusercontent.com` 原始文件 / GitHub REST API / 公开搜索引擎
- 证据等级：L0 上游或厂商源码（可复算）；L1 本机冻结件；L2 公开第三方实测文档；L3 付费或受限（本轮**未访问内容**，仅记录存在）；L4 推断（不作结论）

---

## A. 直接支撑判定的来源

### A-1 upstream Linux — SM8250 uart12 与 pinctrl（L0）

- 标题：`arch/arm64/boot/dts/qcom/sm8250.dtsi`
- 来源：https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/qcom/sm8250.dtsi
- 抓取：https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/sm8250.dtsi （HTTP 200，178,419 B）
- 版本/日期：master 分支，抓取日 2026-11-28
- 引用位置（行号以当日 master 为准）：
  - L1791 `qupv3_id_1: geniqup@ac0000`（wrapper = QUPV3_1，`reg=<0 0xac0000 0 0x6000>`）
  - L2028 `uart12: serial@a90000`，`compatible = "qcom,geni-debug-uart"`，`reg = <0x0 0x00a90000 0x0 0x4000>`，`clocks = <&gcc GCC_QUPV3_WRAP1_S4_CLK>`，`pinctrl-0 = <&qup_uart12_default>`
  - L5767 `qup_uart12_default: qup-uart12-default-state { pins = "gpio34", "gpio35"; function = "qup12"; }`
- 支撑结论：UART12 = 0xa90000 + GPIO34/35 + function `qup12`，属 SoC 级事实，与本机 live FDT 完全一致。

### A-2 u-boot — SM8250 debug UART 配置（L0）

- 标题：`board/qualcomm/debug-sm8250.config`
- 来源：https://github.com/u-boot/u-boot/blob/master/board/qualcomm/debug-sm8250.config
- 内容：`CONFIG_DEBUG_UART=y`、`CONFIG_DEBUG_UART_ANNOUNCE=y`、`CONFIG_DEBUG_UART_BASE=0xa90000`、`CONFIG_DEBUG_UART_MSM_GENI=y`、`CONFIG_DEBUG_UART_CLOCK=14745600`
- 配套邮件：https://lists.u-boot-project.org/pipermail/u-boot/2024-August/562615.html （Caleb Connolly，2024-08-21，新增 sdm845/sm6115/sm8250 debug 配置片段）
- 支撑结论：0xa90000 是 SM8250 平台公认的 debug UART 基址。注意 u-boot 用 14,745,600 Hz 作源时钟，本机 SE4 为 7,372,800 Hz，二者皆为 115200 的整数倍（×128 / ×64），不矛盾。

### A-3 upstream — sm8250-edo（Sony Xperia）把 uart12 设为 console（L0）

- 标题：`[PATCH] arm64: dts: qcom: sm8250-edo: Set UART alias and stdout-path`
- 来源：https://lore.kernel.org/linux-devicetree/20230912-topic-edoconsole-v1-1-b392ea67e539@linaro.org/T/
- 作者/日期：Konrad Dybcio，2023-09-12；2023-09-14 由 Bjorn Andersson 合入
- 引用原文：
  - `aliases { serial0 = &uart12; };`
  - `chosen { stdout-path = "serial0:115200n8"; }`
  - 提交说明："The GENI UART driver requires one specifies a numeric alias. Do so and set the stdout-path to route the console to **the debug uart in the microSD slot** by default."
- 支撑结论：① uart12 是 SM8250 板的 debug console；② 惯例 115200 8N1；③ **物理落点由板厂决定**（Sony 引到 microSD 槽）→ 这是"SoC 级 ≠ 板级"的关键反证。

### A-4 社区实测 — OnePlus 8T（kebab, SM8250）bring-up 记录（L2）

- 标题：`docs/bring-up.md` — "kebab bring-up (measured on hardware, 2026-10-24)"
- 来源：https://github.com/yecw/UniXNU-kebab/blob/main/docs/bring-up.md
- 引用原文（关键三处）：
  - "A UART console also exists (**0xA90000, GPIO34/35, 115200 8N1**) and the 2023 UARTSerialPortLib can be ported back into the current tree, but the hardware adapter was not available; everything below was found through the framebuffer."
  - "**Debug channel without UART** — The panel is enough: … SiliciumPkg then links FrameBufferSerialPortLib, so every DEBUG()/Print() call is drawn into the splash framebuffer that ABL leaves behind. Flash, boot, photograph or record the screen."
  - 分区表片段："abl_log(16 MiB) ABL's own boot log; holds the last few boots … kernel_log(32 MiB) last kernel log buffer area"
- 支撑结论：① 再次确认 0xa90000/GPIO34-35 = SM8250 debug UART、115200 8N1；② **另一台 SM8250 设备同样以 splash framebuffer 面板作为无 UART 时的唯一调试通道**；③ 提出 `abl_log` / `kernel_log` 分区这一事后取证思路（本机待核）。

### A-5 公开社区 DBY-W09 Linux port — 同板设备树与 cmdline（L2）

- 仓库：https://github.com/svesnav/linux-dby-w09 （mainline Linux 7.0 port，pushed 2026-11-02）
- 引用文件与位置：
  - `sm8250-huawei-dby-w09.dts`
    - L1–L14 文件头："Board identity, memory map and the UFS/USB supplies were checked against **the stock HarmonyOS 4.2 device tree (extracted/merged.dts)**."
    - **L50 `hardware_version = "SH1DBSLM";`**
    - L55–L58：`aliases { /* qcom_geni_serial needs a line number ("Invalid line -19"). */ serial0 = &uart6; };`
    - L502 `&uart6 { status = "okay"; bluetooth { compatible = "qcom,qca6390-bt"; … } }`
    - L706 注释："`/* UART6 (QCA6390 Bluetooth) is on the first QUP wrapper. */`"
    - 全文件检索：`uart12` / `a90000` / `geni-debug` **0 命中**
    - `framebuffer: framebuffer@9c000000 { compatible = "simple-framebuffer"; reg = <0x0 0x9c000000 0x0 0x2300000>; width=<1600>; height=<2560>; }`（注释："The bootloader leaves the Huawei logo scanning out of this buffer."）
  - `dby-w09-rootparam.dtso`
    - `qcom,boardid = <0x08 0x02 0x09 0x08>;`
    - `qcom,board_name = "DBY_W09_VG";`
    - `hardware_version = "SH1DBSLM";`
    - 注释说明 Huawei ABL 会拒绝未按 stock overlay 填充 `/rootparam` 的 DTBO 条目
  - `boot-cmdline.txt`（全文）
    - `clk_ignore_unused pd_ignore_unused console=tty0 fbcon=font:TER16x32 loglevel=7 ignore_loglevel panic=0 rdinit=/init`
- 支撑结论：
  1. `SH1DBSLM` 是 DBY-W09 stock DT 的**普遍声明值**，非本机孤例 → 但仍是 DT 声明，不是丝印（§3.2）。
  2. 同为 DBY-W09 且同报 `SH1DBSLM`，其 `board_name=DBY_W09_VG` / `boardid=…0x09 0x08` 与本机 `DBY_W09_VD` / `…0x00 0x06` **不同** → 机型码 + 该字符串都不足以区分 PCB 修订。
  3. 该 port **不使用 UART12**，其内核日志走 **面板 `console=tty0` + fbcon**（§5.5）→ 本板事实上可行的 K1 观察通道是屏幕。
  4. 其 cmdline 含 `clk_ignore_unused pd_ignore_unused`，说明该板 early boot 的时钟/电源域关闭行为需要显式豁免 —— 与 PREP09"SE4 时钟未 enable"同源，值得 AI1 关注。

### A-6 ACK 精确源码 — 早期 console 与 pstore 语义（L0）

- 提交：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`（aosp-mirror/kernel_common）
- `arch/arm64/Kconfig.debug`：https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/Kconfig.debug
  - 全文件仅 3 个 config：`PID_IN_CONTEXTIDR`、`DEBUG_EFI`、`ARM64_RELOC_TEST` → **arm64 不存在 `CONFIG_EARLY_PRINTK`**
- `fs/pstore/Kconfig`：https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/fs/pstore/Kconfig
  - L68–L77 `config PSTORE_RAM` "Log panic/oops to a RAM buffer"（即 ramoops）
  - L37–L42 `config PSTORE_CONSOLE` "pstore will log all kernel messages, even if no oops or panic happened"
- `fs/pstore/ram.c`：`dt_match[]` 仅 `{ .compatible = "ramoops" }`；`parse_u32("record-size", …)`
- `drivers/tty/serial/qcom_geni_serial.c`：
  - L1523 `OF_EARLYCON_DECLARE(qcom_geni, "qcom,geni-debug-uart", qcom_geni_serial_earlycon_setup)`
  - L1895–L1905 match table 仅 `qcom,geni-debug-uart` 与 `qcom,geni-uart`（**无** `qcom,msm-geni-console`）
- 支撑结论：arm64 早期打印只走 earlycon；ramoops 必须靠 `compatible="ramoops"` 的 DT 节点；GENI 驱动不认 `qcom,msm-geni-console`。

---

## B. 负面检索日志（可复核的"未找到"）

引擎：公开 Web 搜索；日期 2026-11-28；语言中英混用。

| # | 查询串（原样） | 命中情况 | 处置 |
|---|---|---|---|
| 1 | `MatePad 11 DBY-W09 boardview schematic 主板 图纸` | 仅 W2R 订阅页（w2rsolutions.in/blog/post/matepad-11）声称有 MatePad 11 schematic/boardview/bitmap，需 app 订阅；ONFIX 教程目录；华为官网支持页 | L3，未访问内容；不可作证据 |
| 2 | `"SH1DBYLM" boardview` | 无相关命中（返回无关站点） | — |
| 3 | `"SH1DBSLM" OR "SH1DBYLM" 华为 主板 编号` | 无相关命中（返回华为企业文档） | — |
| 4 | `"MatePad-11-SH1DBYLM" OR "SH1DBYLM" 点位图` | 无相关命中（仅机型规格页/消委会 PDF） | — |
| 5 | `"DBY-W09" boardview brd schematic download free` | 无 DBY-W09 命中（通用 boardview 工具站/论坛目录） | — |
| 6 | `DBY-W09 主板 点位图 测试点 UART 串口 引出` | 仅 9008 EDL 短接点位教程（onfix.cn 付费、donghairom.com、tsight.io 转载） | **按任务书排除**（EDL ≠ UART） |
| 7 | `Huawei MatePad 11 DBY-W09 teardown mainboard PCB photo test pads` | 仅 EDL 短接 + 泛泛拆解（无网络名/坐标/UART 标识） | 不可用 |
| 8 | `sm8250 "0xa90000" uart12 debug uart console` | **命中 A-2 / A-3 / A-4** | 采纳（SoC 级） |

### B-1 明确不采纳的来源及理由

| 来源 | 类型 | 不采纳理由 |
|---|---|---|
| w2rsolutions.in（MatePad 11 页） | L3 付费订阅 | 未购买、未绕过付费墙；页面只标机型名，不标 PCB 版本字符串 |
| onfix.cn / donghairom.com / tsight.io 短接图 | 9008 EDL test point | 任务书明令"不把 9008 EDL test point 当作 UART 点位" |
| gsmhosting 论坛 DBY-W09 EDL 日志 | L2，工具自动解码 | 仅用作"同机型存在 SM8250-AC(870) 变体"的旁证，不作硬件权威 |
| 各类"Snapdragon 调试口默认 1.8 V"经验帖 | L4 推断 | 无匹配电路/IO 电源域证据，禁止升格 |

---

## C. 本机冻结件（L1，可复算）

| 文件 | 大小 / 行数 | SHA-256 |
|---|---|---|
| `prep04/work/config-used-for-build.config` | 8,688 行 | `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15` |
| `prep07/.../dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img`（PREP06） | 46,563,215 B | `aa25553170ace181bea3d2457962e0d13fff0277511ea7a7bead657e798196a8` |
| 同上，内核段 | 44,820,992 B | `ramoops` 58 命中 / `pstore` 121 命中 |
| 同上，ramdisk 段 | 519,986 B | `ramoops` 0 / `pstore` 0 |
| 同上，DTB 段（`dtb_size=1,216,399` @45,346,816） | 1,216,399 B | `ramoops` 0 / `pstore` 0；节点 905；`/reserved-memory` 18 子节点全 `memory@*`；`/chosen` 0 属性 |
| PREP10 镜像（AI1 制，仅参考） | 46,563,215 B | `d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091` |

候选 DTB 关键节点（本轮只读复算）：

```
/soc@0/geniqup@ac0000/serial@a90000
    compatible = qcom,geni-debug-uart
    status     = disabled          ← 候选 DTB 里是 disabled（与 live FDT 的 okay 相反）
    reg        = 0x0 0xa90000 0x0 0x4000
同址 i2c@a90000 / spi@a90000 同为 disabled
```

> 这条很重要：**live FDT 的 `okay` + `qcom,msm-geni-console` 来自 HOS 的 DTBO overlay（`dtbo_idx=2`），不是我们候选 boot.img 里的 DTB。** 我们的候选 DTB 保持 `disabled` 且 compatible 为 `qcom,geni-debug-uart`。因此候选镜像里只有 **explicit-address earlycon** 这条路径能到 UART12，platform driver 路径（`console=ttyMSM0`）在本构建里根本不会 probe。

---

## D. 未使用但已识别的可能来源（供 AI1 决策，非本轮结论）

| 来源 | 性质 | 说明 |
|---|---|---|
| Huawei Open Source Release Center | 官方，公开 | 若发布 DBY-W09 的 HOS 内核源码包，可拿到 **vendor DTS**（含 rootparam/保留区），但**仍不含 PCB 焊盘**；且包体巨大，本轮未下载 |
| W2R / ZXW 等付费 boardview 库 | L3 | 可能确有 "MatePad 11" 条目，但需订阅；且机型粒度不足以证明 PCB 修订匹配 |
| 本机主板实拍（用户侧） | 最佳 | 任务书第 101 行指定的正解：与本机主板丝印一致的高清照片（SoC 周边、屏蔽罩、丝印区） |
