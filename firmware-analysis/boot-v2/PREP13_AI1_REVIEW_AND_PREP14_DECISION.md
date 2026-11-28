# PREP13 — AI1 独立审核与 PREP14 决策

- 审核日期：2026-11-28
- 审核对象：`PREP13_ABL_UART_HANDOFF_STATIC_AUDIT.zip`
- ZIP 大小：17,023 B
- ZIP SHA-256：`7d93cdc805d01b68e3ca2885f5ee4e7a401d5fec7b2430bed5921011205be2c2`
- ACK 源码基线：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`
- 决策：PREP13 交付 PASS；UART12 仍 HOLD；批准一次使用 ROUND155 既有本地备份的定向 XBL / xbl_config 离线审计。

## 1. 交付完整性

AI1 已直接读取上传 ZIP 并重新计算：
- ZIP SHA-256 与交付记录完全一致；
- 5 个条目齐全；
- `PREP13_REPORT.md`、`uartlog_cmdline_function.md`、`qup12_clock_gpio_handoff.md`、`ack_earlycon_crosscheck.md` 四份正文哈希均与 `SHA256SUMS.txt` 一致；
- ZIP 不含 ABL、XBL、boot、ramdisk、Image、FDT 等二进制。

交付完整性 PASS。但 ZIP 没有包含本轮自写分析脚本或中间反汇编材料；报告称这些脚本留在 Agent 工作区。因而本次可以核验文档和哈希，不能仅凭 ZIP 独立复现全部 ABL 三路负扫描和函数级反汇编。

## 2. PREP13 技术结论审核

### 接受的结论

1. `abl-hos43-pe.bin` 的尺寸 / SHA-256 与冻结身份一致（本轮 ZIP 未包含二进制，因此 AI1 核对的是交付报告与既有冻结身份，不声称重新对二进制复算）。
2. `UartLogCtlCmdline` 的主要范围、HIMNTN 读写、bit17 置位/清零路径、`0x4849` 签名和 cmdline 追加等反汇编线索具有内部一致性；函数仍为 `PARTIAL` 合理。
3. 精确命令 `fastboot oem uart` 字面量存在、HIMNTN 通用写入格式存在，足以把 OEM UART 功能列为强线索；但命令表项到具体函数指针槽、bit17 与最终 cmdline 选择分支尚未全部解码。因此不要把它升级成“已完整证明命令效果”，更不得现在执行该命令。
4. ACK `qcom_geni_serial_earlycon_setup()` 通过显式 MMIO 基址读取 GENI protocol；该 setup 路径没有主动 enable SE clock 或设置 GPIO pinmux。earlycon 是否成功仍取决于入口时硬件状态。
5. `console=NULL` 不能简单等同于“已注册的 `CON_BOOT` earlycon 必然静默”。精确 ACK 的早期参数解析和 `register_console()` 时序支持保留 earlycon 输出的可能性；这纠正了 AI1 之前对 `console=NULL` 的过度绝对化判断。
6. 本机 ABL 中没有发现对目标 UART12 / QUP / TLMM / GCC 地址的直接静态引用，是有价值的负面搜索结果；PREP13 将 handoff 最终判为 `UNKNOWN`，总体 `K1_UART12_ROUTE = HOLD` 正确。

### 必须降低证据等级的表述

PREP13 的部分文字把“三种定向扫描没有命中”写成“ABL 不配置、不关闭、不拥有 UART12”。严格说，当前证据只能支持：

> 在已检查的 ABL payload 中，使用 MOVZ/MOVK 常量构造、对齐指针/字面量池、QUP/GENI/TLMM/GCC 字符串搜索等指定方法，没有找到直接 UART12 硬件编程证据。

这不排除通用 UEFI clock / GPIO / MMIO protocol、运行时取得基址、表驱动寄存器配置、间接函数调用或 ExitBootServices 前的全局电源策略。PREP13 自己将 C6 的全局 clock gate / power shutdown 留作 UNKNOWN 是正确的；因此不能在同一报告中把所有 ABL 硬件动作整体排除。

同样，`Abl Log Save to Emmc` + `RbWritePartition` 能支持“存在 ABL 日志写入 EMMC 的路径”，但不足以证明 ABL 所有 DebugPrint / 调试日志都只走 EMMC。此点不改变 earlycon 决策。

### 当前状态表

| 项目 | AI1 审核状态 |
|---|---|
| PREP13 ZIP / 内部报告哈希 | PASS |
| ABL 函数级解码 | PARTIAL（接受） |
| `fastboot oem uart` 字面量 | STRONG clue；分发器映射未完全闭合 |
| HIMNTN bit17 与 UART cmdline 关联 | STRONG clue；最终选择分支未完全闭合 |
| ABL 目标地址直接硬件编程证据 | 指定搜索方法下未发现；不能推出全局不存在 |
| ABL→kernel 时 SE4 时钟状态 | UNKNOWN |
| ABL→kernel 时 GPIO34/35 mux 状态 | UNKNOWN |
| GENI protocol at handoff | UNKNOWN |
| UART12 earlycon 路线 | HOLD，不判死刑 |
| Framebuffer K1 路线 | BLOCKED；格式 / scanout / console 变体仍未解决 |
| 设备刷写 / 临时启动 | NO-GO，直到受控启动和恢复路径另行验收 |

## 3. 重要的新依据：XBL 已在 ROUND155 捕获

AI1 回查了 ROUND155 原始只读分区捕获报告，确认两个既有本地备份曾被精确读取并通过尺寸、设备端第二次 SHA-256、主机回读 SHA-256 核验：

| 分区 | 大小 | SHA-256 |
|---|---:|---|
| `xbl` | 4,018,176 B | `7819d2af26438a817600080dc2340006fd3b9a5b6ea7a60509f3faf2e5d201c2` |
| `xbl_config` | 4,325,376 B | `5c63be1b477669a4f693dd98ad31954884a0907ebf1ae94b5c4a36ef9a34aa5c` |

ROUND155 报告还记录：`xbl` 为 AArch64 ELF、15 个 LOAD 段，版本字符串 `BOOT.XF.3.2-00363-SM8250-1`；`xbl_config` 为 64-bit ARM ELF、4 个 LOAD 段。XBL 中已见 `/chosen`、`/reserved-memory/splash_region`、`LcdkitInitPanelInfo` 和 DDR MemoryMap 配置字符串。

因此，下一步不需要再读平板，也不需要重新捕获分区。应只定位 Agent 本地已存在的 ROUND155 `xbl` / `xbl_config` 副本，先核验哈希，再做狭义静态审计。如果既有副本已不存在，立即停止并如实报告；不得重新连接设备补读。

## 4. AI1 决策：只批准 PREP14 一次定向 XBL 审计

PREP14 的唯一问题：**XBL / xbl_config 是否为 QUPV3_1 GENI SE4（UART12，0xa90000）准备、启用或保持时钟、电源域与 GPIO34/35 qup12 pinmux，并且这些状态是否有证据跨越 XBL→ABL→kernel 交接。**

只分析 ROUND155 已捕获的 `xbl` 与 `xbl_config`。不扩大到其他固件分区、不重新 dump 设备、不运行 `fastboot oem uart`、不接线、不构建、不刷机。

PREP14 完成后，AI1 直接作最终决策：
- 若发现完整可追溯的 SE4 时钟 / GPIO mux 配置与保持路径：整理一次 K1 earlycon 候选包和受控测试前置门槛；
- 若发现明确关闭 / 清理路径：UART12 earlycon 判为 BLOCKED，转入现有非 UART 日志设计；
- 若仍不能闭合：保持 HOLD，不再安排泛化 XBL/ABL 扫描。只有在 fastboot 临时启动可接受性与可信恢复路径明确后，才考虑一次受控 K1 观察。

**本次 AI1 批准的 Agent 轮次上限：PREP14 这一轮。完成后不再以“继续搜索”作为默认下一步。**

## 5. 安全边界

- 禁止 ADB、fastboot、OEM、重启、临时启动、刷写、解锁、EDL、分区读写、拆机或接触 UART pad。
- 不执行 `fastboot oem uart` / `fastboot oem himntn`。这些涉及设备持久配置，当前没有用户授权。
- 不修改任何源码、config、DTS、DTB、DTBO、boot、ramdisk、Image 或固件。
- 仅使用已捕获二进制的本地副本；不得为了补缺重新读取设备。
- 只交付去敏文本分析、脚本和哈希清单；不得把原始 XBL / XBL_CONFIG 二进制上传到公开仓库。