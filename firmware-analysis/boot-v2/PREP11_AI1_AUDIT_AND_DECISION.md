# PREP11 — AI1 独立审核与修正意见

- 审核对象：`firmware-analysis/boot-v2/PREP11_BOARDVIEW_UART12_PUBLIC_EVIDENCE/`
- WorkBuddy 提交所在分支：`ai1/boot-v2-first-package-prep`
- WorkBuddy 提交 commit：`3bb3ce7b73586d5eb4eb8488b4f71b32cecb8d42`
- 审核日期：2026-11-28
- 审核者：AI1（ChatGPT）

## 1. 文件交付验收

指定目录下五个文件已存在：`PREP11_REPORT.md`、`sources.md`、`gpio34_gpio35_route.md`、`alternative_k1_logging.md`、`SHA256SUMS.txt`。报告有明确证据等级、来源 URL、检索范围和操作安全记录；本轮没有设备交互。SHA256 清单列出了四份文本报告的内容哈希。

## 2. AI1 接受的结论

### 2.1 UART12 实体线路：停止投入

- `BOARDVIEW_MATCH = UNKNOWN`：接受。
- SoC 级 `0xa90000 = QUPV3_1 SE4 / GPIO34 / GPIO35 / qup12`：有上游 SM8250 DTS、U-Boot debug 配置和第三方 SoC 实测相互印证。
- TX/RX 方向、package ball、net name、PCB 焊盘、GND、逻辑电平全为 UNKNOWN：接受。
- 因而 `UART_PHYSICAL_ACCESS = UNCONFIRMED`，不得接线、不得短接、不得盲测。

后续不再继续搜索不匹配 BoardView，也不再要求用户拆机。除非用户主动提供准确 PCB revision 的实物照片或合法 BoardView，否则 UART12 只保留为 SoC 级备用路径。

### 2.2 当前 ACK 构建并无可用的非 UART K1 通道：接受

依据冻结的实际 Kleaf config 与候选 DTB：
- pstore/ramoops 驱动已编译，但候选 DTB 没有 `compatible = "ramoops"` 预留区；当前无后端。
- netconsole 未编译。
- USB gadget serial console 未编译；USB host 串口依赖模块与用户态。
- `CONFIG_VT`、framebuffer console 未启用，候选 DTB 也没有 simple-framebuffer 节点。
- 因此目前 K1 观察能力仍然不足，不能把 PREP06/PREP10 当作已具备可靠观察通道。

### 2.3 社区 framebuffer 路线是重要线索，但不是本机精确板版的已证结论

公开社区仓库 `svesnav/linux-dby-w09` 的 DTS/boot-cmdline 确实展示了一个可用的 DBY-W09 屏幕日志方案：
- `/chosen/framebuffer@9c000000`，格式 `a8r8g8b8`，1600×2560，stride 6400；
- 配套 `/reserved-memory/splash_region@9c000000`，大小 `0x2300000`，带 `no-map`；
- cmdline 使用 `console=tty0 fbcon=font:TER16x32`、`clk_ignore_unused`、`pd_ignore_unused` 和 `ignore_loglevel`。
- Linux simplefb 需要 firmware/bootloader 已经初始化且仍在 scanout 的 framebuffer；内核只是映射预分配 buffer。<https://cateee.net/lkddb/web-lkddb/FB_SIMPLE.html>

但报告必须降低“同板已证实”的表述强度：
- 社区 DTS 的 `qcom,board_name = DBY_W09_VG`、`qcom,boardid=<0x08 0x02 0x09 0x08>`；
- 本机 PREP09 live FDT 是 `DBY_W09_VD`、`qcom,boardid=<0x08 0x02 0x00 0x06>`；
- 社区 DTS 的 panel 驱动名为 `lcd_kit_debussy_110_20d_10p9_qcom`，本机 PREP09 bootargs 中是 `lcd_kit_debussy_290_20d_10p9_qcom`。

因此只能得出“同一 DBY-W09 产品家族中有一个成功使用 panel/fbcon 的社区移植”；不能直接认定本机 VD 的 splash buffer 地址、大小、格式、panel scanout 状态与 VG 一致。

## 3. PREP11 漏掉的决定性命令行问题：ABL 的 console=NULL

PREP09 的脱敏 live bootargs 显示：
- boot image header 内 cmdline 到 `nokaslr` 结束；
- ABL 在后面追加 `console=NULL loglevel=0`。

AI1 从与实际构建 commit 完全一致的 ACK 源码 `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9` 独立确认：
- `kernel/printk/printk.c` 的 `console_setup()` 对 `console=null` 的处理是调用 `__add_preferred_console("ttynull", ...)`；
- 同一源码注释明确：“The last preferred console added will be used for kernel messages…”
- 因而 header cmdline 里的 `console=tty0` 会被 ABL 后置的 `console=NULL` 覆盖，tty0 不会成为最终 preferred console。
- PREP10 的 `ignore_loglevel` 只改变 loglevel 过滤，不会撤销 `ttynull` 的 preferred-console 选择。

精确 ACK 源码：
- https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/kernel/printk/printk.c
- 对应公开上游实现也解释了 `console=null` 会建立 ttynull preferred console：<https://github.com/torvalds/linux/blob/master/kernel/printk/printk.c>

因此，**仅仿照社区 cmdline 在 boot header 加 `console=tty0` 不够**。新的 framebuffer 候选必须显式解决 ABL 后置 console override。一个可能的方案是 arm64 `CONFIG_CMDLINE_FORCE`：它会用编译时默认 cmdline 替代 bootloader 传入的全部参数；但这会同时丢掉 ABL 的所有其他 kernel bootargs，必须先评估哪些参数对 K1 安全启动不可缺少。不要误用 `CONFIG_CMDLINE_EXTEND`：精确 ACK 的 `drivers/of/fdt.c` 将 bootloader DT bootargs 追加到编译时默认 cmdline 后面，仍会让 `console=NULL` 最后生效。

arm64 Kconfig 语义：
- `CMDLINE_FORCE`：永远使用默认 kernel command string，即便 bootloader 传入其他参数。<https://linux.googlesource.com/linux/kernel/git/torvalds/linux/%2B/36ae1c45b2cede43ab2fc679b450060bbf119f1b/arch/arm64/Kconfig>
- `CMDLINE_EXTEND`：bootloader arguments 追加到默认 cmdline 后面；不适合用来压过后置 `console=NULL`。<https://android.googlesource.com/kernel/common/%2B/9c8c166d55869f56eda278e2c3191dba92f1ac55/arch/arm64/Kconfig>

## 4. Framebuffer 地址与保留区必须先做本机校验

AI1 在 PREP10 候选 DTB 中独立解析到：
- RAM 节点覆盖范围包含 `0x9c000000`；
- 候选 DTB 当前没有 `simple-framebuffer` 节点；
- 当前 `/reserved-memory` 没有 `0x9c000000..0x9e300000` 的 splash/no-map 预留项。

社区方案若使用 `0x9c000000 / 0x2300000`，必须同时考虑 reserved-memory/no-map，否则该区域位于普通 RAM 范围，存在被内核内存分配器使用的风险。必须先以本机 live FDT、ABL handoff 与当前 panel variant 证据确认地址/大小/格式，不得盲目复制 VG 的 carveout。

精确 ACK simplefb 驱动读取 `width/height/stride/format`，优先使用 `memory-region`，否则读 `reg`；驱动还会申请 framebuffer 资源。代码：<https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/video/fbdev/simplefb.c>。

## 5. 下一步决策

不做 PREP11 的第二轮 BoardView 搜索；不接线；不刷写。

下一步只做 PREP12：
1. 只读核实本机完整 `/dev/block/by-name`，判断是否存在 `abl_log` / `kernel_log` 等日志分区，记录名字与容量，不读取分区内容；
2. 重新只读提取最小必要 live FDT/display 信息，确定本机 splash/framebuffer 地址、长度、格式、reserved-memory path；
3. 对照现有 ABL PE 的字符串、xref 与调用路径，确认 ABL 是否要求一个特定 splash reserved-memory 节点才能 handoff framebuffer；
4. 对照精确 ACK Kconfig 与 `drivers/of/fdt.c`，给出能够处理 ABL 后置 `console=NULL` 的安全 K1 命令行策略，并明确会丢失哪些 bootloader args；
5. 若上述证据完整，才提交一个独立 K1 framebuffer candidate build plan / host-only build；若不完整，停止构建并报告唯一缺失项。

PREP11 的总体裁定：`UART12_PHYSICAL = NO-GO`；`FB_CONSOLE_ROUTE = PROMISING_BUT_NOT_YET_PROVEN_FOR_THIS_BOARD_REVISION`；`DEVICE_FLASH = NO-GO`。
