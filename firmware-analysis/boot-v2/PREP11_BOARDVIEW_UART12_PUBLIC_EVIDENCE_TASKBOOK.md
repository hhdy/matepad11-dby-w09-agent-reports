# PREP11 — DBY-W09 精确 PCB 版本 BoardView / UART12 物理路径公开资料核验

## 任务目标

PREP09 已证明 UART12 对应当前 live FDT 中的 console 型 GENI SE：MMIO `0xa90000`、QUPV3_1 SE4、GPIO34/GPIO35、pinctrl function `qup12`。但目前 TX/RX 归属、实体焊盘、GND、电平和精确 PCB revision 都没有证据。

本轮只做公开资料与已有本地资料的离线交叉核验，目标是决定 UART12 是否有安全可接入的实体路径，或应停止投入 UART12 并寻找其它 K1 观察方式。

## 执行角色

- 执行者：完成 PREP04-FIX01 / PREP05 / PREP07 / PREP08 / PREP09 的同一个 WorkBuddy 会话。
- 技术审核与最终判断：AI1（ChatGPT）。
- 设备：Huawei MatePad 11 DBY-W09 / SM8250 / HOS4.3。

## 已知事实（不得改变或混淆）

1. PREP08 / PREP09 的设备运行时属性显示 `ro.board.hardware_version=SH1DBSLM`，但 `ro.settings.use_dts_hwversion=true`，因此它是 **DT_DECLARED_HARDWARE_VERSION**，不是实体 PCB 丝印或 efuse 的独立证明。
2. PREP09 live FDT 的 `/rootparam/qcom,board_name=DBY_W09_VD`，`product_name=DBY-W09`，`boardid` 为四个 cell `0x8 0x2 0x0 0x6`。
3. 当前发现的公开 BoardView 页面型号标签为 `MatePad-11-SH1DBYLM`。它与上述 DT 声明值并未证明相同，不得直接套用其焊盘图。
4. PREP09 live FDT UART12：
   - `/soc/qcom,qup_uart@a90000`
   - `compatible = "qcom,msm-geni-console"`
   - `reg = <0xa90000 0x4000>`
   - QUPV3_1 GENI SE4
   - default pinctrl: GPIO34/GPIO35, `function="qup12"`, drive-strength 2 mA
   - FDT 未标明 GPIO34/35 中哪个是 TX、哪个是 RX。
5. PREP09 在 HOS 已完全启动后的 runtime 状态观察到 GPIO34/35 未被 pinctrl claim，UART12 SE clock enable/prepare count 为 0。此状态不能证明 ABL 跳入 ACK 内核前的时钟和 pinmux 状态。
6. PREP06 earlycon 名称 `qcom_geni` 有精确 ACK 源码依据。PREP10 已在离线 boot header cmdline 开头加入 `ignore_loglevel`，预计可抵消 ABL 后置 `loglevel=0`；不解决 clock/pinmux/物理焊盘问题。
7. 当前没有可确认的 UART 线缆、实体 pad、TX/RX 方向或逻辑电平。

## 允许范围

仅使用公开、合法、无需付费绕过的资料和本地已有文件：
- 公共 BoardView / schematic / service manual / repair documentation；
- 公开的 DBY-W09 device tree、Qualcomm SM8250 pinctrl 和 QUP/GENI 文档；
- WorkBuddy 已有本地目录中由用户合法提供的、与本机实际板版有关的照片或维修资料（如确实存在）。
- 可查询已构建内核的实际配置，以评估替代日志通道：`CONFIG_PSTORE`、`CONFIG_PSTORE_RAM` / `CONFIG_RAMOOPS`、`CONFIG_NETCONSOLE`、`CONFIG_EARLY_PRINTK` / earlycon 相关配置。必须使用已冻结的 `config-used-for-build.config`，不可假定开启。

## 需要回答的问题

### A. 精确板版匹配

1. 是否存在型号明确为 `SH1DBSLM` 或 `DBY_W09_VD` 的公开 BoardView / schematic？
2. `MatePad-11-SH1DBYLM` 与 `SH1DBSLM` / `DBY_W09_VD` 的关系是否可由 PCB revision、主板料号、丝印、文件头或官方维修资料证明？
3. 如果无法证明，明确标记 `BOARDVIEW_MATCH = NO / UNKNOWN`，不得推断为同板。

### B. GPIO34 / GPIO35 的物理网络

只有在精确板版资料匹配的情况下，继续追踪：
1. SoC TLMM GPIO34 和 GPIO35 对应的 SM8250 package ball / pinmux 位置；
2. 在匹配 schematic / BoardView 中对应的 net name、器件编号、测试点编号、连接器 pin 或焊盘；
3. 哪一条是 UART TX、哪一条是 UART RX。必须以明确网络标注、芯片 pinout 和连线关系为证；
4. GND 的明确可用参考点；
5. 逻辑电平（例如 1.8 V / 3.3 V）必须从匹配电路、IO 电源域或官方资料证明，禁止按 Snapdragon 通用经验猜测；
6. UART 波特率如不能由准确资料确定，记录为未知；7.3728 MHz clock rate 是 SE 输入时钟，不等于串口 baud rate。

每个结论必须给出来源 URL、文档名称/版本、页号或 BoardView 坐标/网络名，并标注证据等级。没有原理图或 BoardView 支撑的推导不得升格为 CONFIRMED。

### C. 替代 K1 观察通道（只评估，不实施）

检查冻结的 Kleaf 实际配置，判断以下项目是否已构建且是否对 K1 阶段有实际帮助：
- pstore / ramoops；
- netconsole；
- 可用的早期 USB/串口控制台；
- 可在 K1/K2 后获取的本地 crash/log buffer。

区分“编译进内核”“DT/保留内存支持”“设备启动时实际可用”三个层次。不得为得到结果而重编译内核或修改配置。

## 明确禁止

- 不连接平板，不执行 ADB、Fastboot、reboot、EDL 或任何模式切换。
- 不拆机、不短接、不接探针、不测量任何未确认焊盘。
- 不写 GPIO、切换 pinmux、打开时钟、加载模块或改变设备运行状态。
- 不购买付费 BoardView，不绕过付费墙，不使用来源不明的维修资料。
- 不把 9008 EDL test point 当作 UART 点位。
- 不将 SH1DBYLM BoardView 用于 SH1DBSLM / DBY_W09_VD，除非有明确等同证据。
- 不修改 PREP06 / PREP10 镜像，不重编 kernel/DTB/DTBO，不刷写。
- 不给用户任何试探接线建议或盲测电压建议。

## 交付要求：必须上传 GitHub，不要只在聊天中附 ZIP

仓库：`hhdy/matepad11-dby-w09-agent-reports`

分支：`ai1/boot-v2-first-package-prep`

目录：`firmware-analysis/boot-v2/PREP11_BOARDVIEW_UART12_PUBLIC_EVIDENCE/`

提交内容：
- `PREP11_REPORT.md`：按问题 A/B/C 给出结论、证据与限制；
- `sources.md`：来源 URL、标题、版本/发布日期、访问日期、引用页码或 BoardView 坐标；
- `gpio34_gpio35_route.md`：仅有匹配证据时记录 package pin → net → pad/testpoint → GND → voltage；若未匹配则明确写 UNKNOWN，禁止填猜测值；
- `alternative_k1_logging.md`：已编译配置及 K1/K2 实用性分析；
- `SHA256SUMS.txt`：对上述文本文件计算 SHA-256。

完成后必须：
1. 将以上文件直接 commit + push 到指定 GitHub 分支/目录；
2. 回复准确的 commit SHA、每份文件的 GitHub URL；
3. 若找到的是公开的、可合法引用的 BoardView/PDF，可提供原始页面 URL，但不得擅自复制上传受版权保护的文档；
4. 不需要把 ZIP 上传到聊天窗口。AI1 将直接从 GitHub 读取和审核。

如果没有与本机精确板版相符的公开资料，停止在 `BOARDVIEW_MATCH = UNKNOWN`，说明需要用户提供与本机主板丝印一致的高清照片或合法取得的 BoardView。不得为了完成任务而猜测焊盘。
