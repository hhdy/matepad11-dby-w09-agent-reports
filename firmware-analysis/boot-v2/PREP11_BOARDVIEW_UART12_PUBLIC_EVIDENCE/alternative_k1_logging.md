# alternative_k1_logging.md — 替代 K1 观察通道评估

> **性质：只评估，不实施。** 本轮未重编译内核、未改配置、未改 DTB/DTBO、未连接设备。
> 依据：冻结件 `config-used-for-build.config`（sha256 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`，8 688 行，`Linux/arm64 6.18.33`）+ PREP06 候选 boot 镜像（sha256 `aa25553170ace181bea3d2457962e0d13fff0277511ea7a7bead657e798196a8`）二进制复算。

---

## 0. 三层判定口径

任务书要求区分三个层次，本文件严格按此分层：

- **① 编译进内核**：配置项在 `.config` 里为 `=y`，且能在 Image 里找到对应符号/字符串。
- **② DT / 保留内存支持**：运行时是否具备触发该通道所需的设备树节点、保留内存或 cmdline 参数。
- **③ K1 阶段实际可用**：在"second stage 挂载之前、无用户态、无模块加载"的 K1 窗口内，是否真的能产出可读输出。

**只有①②③同时为真，才算"可用"。**

---

## 1. 总矩阵

| 通道 | ① 编译进内核 | ② DT / 运行前提 | ③ K1 可用 | 裁定 |
|---|---|---|---|---|
| earlycon `qcom_geni` @0xa90000 | **YES** | explicit-address 路径**不需** DT 节点；但需 ABL 遗留 pinctrl mux + SE clock | **条件性** | 唯一通道，前提未证 |
| pstore / ramoops | **YES** | **NO**（DT 无 `ramoops` 节点） | NO | **COMPILED / NO_BACKEND** |
| pstore console（`console=pstore`） | **YES** | NO（同上） | NO | 不可用 |
| pstore pmsg（`/dev/pmsg0`） | **YES** | NO（同上） | NO | 不可用 |
| netconsole | **NO** | — | NO | **NOT_COMPILED** |
| USB gadget serial console | **NO** | — | NO | 不可用 |
| USB host 串口（ftdi 模块） | 仅 `=m` | 需用户态 `insmod` | NO | 不可用（K1 无用户态） |
| `tty0` / fbcon（面板） | **NO** | NO（候选 DTB 无 `simple-framebuffer`） | NO（本构建） | **硬件可行、构建未开** |
| DRM panic 上屏 | **NO** | — | NO | 不可用 |
| `last_kmsg` / Android ram_console | **NO** | — | NO | 不可用 |
| 分区级 boot log（`abl_log`/`kernel_log`） | 与本内核无关 | 取决于本机是否存在该分区 | **UNVERIFIED** | 待只读核实 |

---

## 2. 逐通道证据

### 2.1 earlycon `qcom_geni` @0xa90000 —— 唯一的实时通道

**① 编译证据（`.config` 原文）**

```
CONFIG_PRINTK=y
CONFIG_PRINTK_TIME=y
CONFIG_PRINTK_CALLER=y
CONFIG_CONSOLE_LOGLEVEL_DEFAULT=7
CONFIG_CONSOLE_LOGLEVEL_QUIET=4
CONFIG_SERIAL_EARLYCON=y
CONFIG_FIX_EARLYCON_MEM=y
CONFIG_SERIAL_QCOM_GENI=y
CONFIG_SERIAL_QCOM_GENI_CONSOLE=y
CONFIG_SERIAL_QCOM_GENI_UART_PORTS=8
# CONFIG_SERIAL_MSM is not set
```

**Image 侧交叉验证（PREP07 已记录，本轮沿用）**：earlycon 表项 `name='qcom_geni'`、`compatible='qcom,geni-debug-uart'`；`msm_geni_serial`（HOS 4.19 下游名）在 Image 内 **0 命中**。

**关于 `CONFIG_EARLY_PRINTK`**：ack 精确提交 `8ad08f75…` 的 `arch/arm64/Kconfig.debug` 全文件只有 `PID_IN_CONTEXTIDR` / `DEBUG_EFI` / `ARM64_RELOC_TEST` 三项 —— **arm64 平台不存在该符号**，所以 `.config` 里没有它不是缺陷；arm64 的早期打印机制就是 `CONFIG_SERIAL_EARLYCON` + `OF_EARLYCON_DECLARE`。

**② DT 前提**：cmdline `earlycon=qcom_geni,0xa90000` 走 explicit-address 分支，**不要求** DT 节点 `status="okay"`（这点很关键：候选 DTB 里 `serial@a90000` 恰恰是 `disabled`，earlycon 仍能初始化）。

**③ K1 可用性**：仍受两个 ABL 遗留状态制约 —— GPIO34/35 的 pinmux、SE4 的 clock gate。PREP09 在 HOS 起来后观测到两者皆为"未生效/未使能"，但**这不能证明 ABL 交棒瞬间的状态**（方向性未知，两向都可能）。

**→ 结论：代码侧已就绪，物理可观测性未证。**

### 2.2 pstore / ramoops —— 驱动在，后端不在

**① 编译证据（`.config` 原文）**

```
CONFIG_PSTORE=y
CONFIG_PSTORE_DEFAULT_KMSG_BYTES=10240
CONFIG_PSTORE_COMPRESS=y
CONFIG_PSTORE_CONSOLE=y
CONFIG_PSTORE_PMSG=y
CONFIG_PSTORE_RAM=y
# CONFIG_PSTORE_BLK is not set
```

`fs/pstore/Kconfig`（ACK 精确提交）语义核对：

- `config PSTORE_RAM` → "Log panic/oops to a RAM buffer"（这正是 ramoops 驱动本体）
- `config PSTORE_CONSOLE` → "pstore will log all kernel messages, even if no oops or panic happened"（依赖 pstore 后端）

**Image 侧交叉验证（本轮二进制复算）**

| 段 | 大小 | `ramoops` | `pstore` |
|---|---|---|---|
| KERNEL | 44,820,992 B | **58** | **121** |
| RAMDISK | 519,986 B | 0 | 0 |
| DTB | 1,216,399 B | **0** | **0** |

→ 驱动确实编进内核；**DTB 段一个 `ramoops` 字符串都没有**。

**② DT 前提（决定性）**

`fs/pstore/ram.c` 的 `dt_match[]` 只有：

```c
{ .compatible = "ramoops" },
```

候选 DTB 复算结果：

```
节点总数                        : 905
/reserved-memory 直接子节点      : 18
  memory@80000000 … memory@8bf00000   （全部为 memory@*）
  唯一带 compatible 的           : memory@80860000 = qcom,cmd-db
名称含 ramoops/pstore/logbuf/dump 的节点 : NONE
compatible 含 ramoops/pstore 的          : NONE
/chosen 属性数                   : 0（无 bootargs）
```

**→ 没有 `compatible="ramoops"` 的节点 → `platform_driver` 永不 probe → pstore 后端永不注册 → `PSTORE_CONSOLE`/`PMSG` 全部空转。**

**③ 补充：即便补上节点，还有两个坑**

1. **保留区被裁过**：stock DTB（slot0）有 **37** 个 reserved-memory 子节点，含 `res_xbl_uefi_log_region`、`disp_rdump_region`、`mem_dump_region`、`kerneldump`；候选 DTB 只剩 18 个 `memory@*`。加 ramoops 时必须重新审视保留区布局，避免与 ABL/固件预期冲突。
2. **`PSTORE_DEFAULT_KMSG_BYTES=10240`（10 KiB）**：单条 record 上限 10 KiB，K1 完整 dmesg 会被截断，需同时调 `record-size`。
3. **RAM 易失性**：ramoops 存在 RAM 里，**能跨 warm reboot，不能跨断电**。而本构建 `CONFIG_PANIC_TIMEOUT=-1`（见 §2.7），panic 后原地挂死，只能人工断电 → 断电即丢。**结论：当前配置下 ramoops 即使补上 DT 也拿不到东西，除非同时把 panic 行为改成自动重启。**

**→ 裁定：COMPILED / NO_BACKEND。不是"可能要调一下"，而是三重阻塞。**

### 2.3 netconsole

```
# CONFIG_NETCONSOLE is not set
```

无讨论空间。且 K1 阶段无网络栈/PHY 驱动，即使开启也只能在 K3 之后起作用。

### 2.4 USB

```
CONFIG_USB_SERIAL=m
CONFIG_USB_SERIAL_FTDI_SIO=m
# CONFIG_USB_SERIAL_SIMPLE is not set
# CONFIG_U_SERIAL_CONSOLE is not set
```

- host 侧串口只有 ftdi 编成**模块** → 需要用户态 `insmod` → K1 不可用；且平板是 USB-C 设备端，不是 host。
- gadget 串口控制台（`U_SERIAL_CONSOLE`）**未开** → 无法把 USB-C 当 CDC-ACM console。
- 其余 `USB_SERIAL_*` 全 `not set`。

→ K1 的 USB 口只能供电/充电，不是日志通道。

### 2.5 面板 console（`console=tty0` + fbcon）—— 本轮最重要发现

**硬件可行性（L2，同板实测）**

社区同板 port `svesnav/linux-dby-w09` 的 `boot-cmdline.txt` 全文：

```
clk_ignore_unused pd_ignore_unused console=tty0 fbcon=font:TER16x32 loglevel=7 ignore_loglevel panic=0 rdinit=/init
```

其 DTS：

```dts
/* The bootloader leaves the Huawei logo scanning out of this buffer. */
framebuffer: framebuffer@9c000000 {
    compatible = "simple-framebuffer";
    reg = <0x0 0x9c000000 0x0 0x2300000>;
    width = <1600>; height = <2560>; stride = <(1600 * 4)>;
```

旁证（不同厂商、同 SM8250）：OnePlus 8T（kebab）bring-up 记录 "Debug channel without UART — The panel is enough … every DEBUG()/Print() call is drawn into the splash framebuffer that ABL leaves behind"，且同样使用 **0x9C000000**。

**我们的构建为什么用不了**

| 检查项 | 结果 |
|---|---|
| `CONFIG_VT` | **`# CONFIG_VT is not set`** → 没有 `/dev/tty0`、没有 fbcon |
| `CONFIG_FRAMEBUFFER_CONSOLE` / `CONFIG_DRM_FBDEV_EMULATION` | 配置中**不存在**（VT 关闭后相关项不出现） |
| `CONFIG_DRM_PANIC` | **`# CONFIG_DRM_PANIC is not set`** → 无 panic 上屏 |
| 候选 DTB `simple-framebuffer` 节点 | **NONE**（顶层节点清单中无 framebuffer/framebuffer@*） |

**→ 硬件上这条路是真的通的（同板已验证），是我们的构建把它关掉了。这是配置取舍，不是硬件死局。**

**若要启用（本轮未实施，仅列成本）**：

1. 内核配置：开启 `CONFIG_VT` + `CONFIG_FRAMEBUFFER_CONSOLE`（或 DRM 路线 `CONFIG_DRM_SIMPLEDRM` / `DRM_FBDEV_EMULATION`）。
2. DTB：新增 `simple-framebuffer@9c000000`（`reg=<0 0x9c000000 0 0x2300000>`，1600×2560×4）。**注意**：候选 DTB 的 `/chosen` 为空，cmdline 全在 boot header，故 `console=tty0` 要加在 **header cmdline**，不能指望 `/chosen/bootargs`。
3. 风险点：`simple-framebuffer` 会与真正的 DRM/DSI 驱动抢显示资源；社区做法是先拿到日志、后续再切真驱动。且候选 DTB 的保留区已经与 stock 不一致，splash 区域是否被覆盖需核对。
4. 收益：一旦可用，K1/K2 全程有**不依赖任何未证硬件前提**的可视通道，且可以直接拍照留存（比串口更抗丢日志）。

### 2.6 分区级 / 厂商 dump 通道

| 候选 | 本机状态 |
|---|---|
| Android `last_kmsg` / `ram_console` | 配置中无相应符号 → **不可用** |
| Huawei `kerneldump` / `mem_dump` / `rainbow` 驱动 | PREP07：Image 内 `kerneldump` 0 命中、`bootfail` 0 命中、`rainbow` 0 命中；`mem_dump` 的 4 次命中是核心 `mem_dump_obj` 符号 → **驱动未编入** |
| ABL `bootfail` | PREP07：ABL 内 `bootfail` 42 次、`boot_fail` 9 次、`BOOTFAIL` 1 次 → 是**失败计数器**，不是日志 |
| ABL 自身日志分区（`abl_log`） / 内核日志分区（`kernel_log`） | **UNVERIFIED**：kebab 有 `abl_log`(16 MiB)/`kernel_log`(32 MiB)；本机 R155 分区清单（18 项，面向启动链的**筛选子集**）不含这两项，但**不是全量 by-name**，故不能断言不存在 |

**→ 这是一条"零成本待核"通道：下一轮若获准只读 ADB，`ls -l /dev/block/by-name` 一条命令即可判定。存在则可 root 只读 `dd` 出来事后分析，不需要改内核、不需要 UART。**

### 2.7 一个容易被忽略的负面配置组合

```
CONFIG_PANIC_ON_OOPS=y
CONFIG_PANIC_TIMEOUT=-1
# CONFIG_BOOTPARAM_SOFTLOCKUP_PANIC is not set
# CONFIG_BOOTPARAM_HARDLOCKUP_PANIC is not set
CONFIG_LOG_BUF_SHIFT=17          # 128 KiB 内核环形缓冲
# CONFIG_SECURITY_DMESG_RESTRICT is not set
```

含义：任何 oops 立即 panic（好，能定位问题），但 **panic 后永不自动重启**（`PANIC_TIMEOUT=-1`），设备停在原地、屏幕冻结（而本构建无 DRM_PANIC，屏幕未必有内容）。此时：

- 没有 pstore 后端 → 日志不落任何持久介质；
- RAM 里的 128 KiB log_buf 随断电消失；
- 唯一能做的只有人工长按断电 → 然后**什么也拿不到**。

**→ 这套组合在 K1 取证上是"最坏配置"：既无持久化，也不自愈。**

---

## 3. 结论与建议（提交 AI1，本轮不执行）

```
ALTERNATIVE_LOG_PSTORE      = COMPILED / NO_BACKEND（三重阻塞：无 DT 节点、10 KiB record、断电即失）
ALTERNATIVE_LOG_NETCONSOLE  = NOT_COMPILED
ALTERNATIVE_LOG_USB         = NOT_COMPILED
ALTERNATIVE_LOG_PANEL       = FEASIBLE_ON_HW（L2 同板实测）/ NOT_BUILT_IN_OUR_KERNEL
ALTERNATIVE_LOG_PARTITION   = UNVERIFIED（低成本只读可核）
K1_OBSERVABILITY_AS_BUILT   = earlycon 单通道，且 pinctrl/clock 前提未证
```

按性价比排序的建议：

1. **面板 console 立项**（最高性价比）：唯一被同板实测验证过的通道，且失败模式是可解释的（黑屏 = 连 splash 都没继承），比"串口没字"更可诊断。
2. **只读核实日志分区**（成本最低）：一条 `ls` 决定是否存在 `abl_log`/`kernel_log` 这类免费事后通道。
3. **ramoops 暂不投入**：需要同时满足"加 DT 节点 + 调 record-size + 改 panic 策略 + 保 warm reboot"，四件事凑齐才有产出，投入产出比最低。
4. **UART12 维持 NO-GO**：见 `gpio34_gpio35_route.md`，板级证据缺失，接线不可行。
5. **`ignore_loglevel`（PREP10）仍然正确且必要**：它解决的是 loglevel 过滤，与上述通道选择正交；无论最终走面板还是串口，都应保留。
