# PREP12 — K1 面板日志 / ABL splash / 日志分区最终只读取证

## 目标

PREP11 已完成公开资料核验。AI1 裁定：

- UART12 物理接入：`NO-GO`。停止寻找焊盘、停止 BoardView 搜索，不接线。
- 面板 framebuffer console：有价值的替代方向，但 PREP11 的社区 DTS 是 `DBY_W09_VG` / boardid `0x08020908`，本机是 `DBY_W09_VD` / boardid `0x08020006`；本机 panel ID 也与社区 DTS 不同。不能直接复制 0x9c000000、0x2300000 和格式参数。
- PREP09 证明 ABL 在 boot header cmdline 后追加 `console=NULL loglevel=0`。精确 ACK `console_setup()` 会把 `console=null` 变成 preferred `ttynull`，最后出现的 console 参数优先。因此只在 boot header 加 `console=tty0` 不会解决面板输出。
- PREP10 的 `ignore_loglevel` 只解决打印等级，不会撤销 `console=NULL`。
- PREP10 候选 DTB 中 `0x9c000000` 位于 RAM 范围内，目前没有覆盖它的 splash/no-map reserved-memory carveout，也没有 simple-framebuffer 节点。

本轮只补齐三个决定性事实：
1. 本机真实 splash/framebuffer 地址、长度、格式、ABL handoff 节点要求；
2. 是否存在可用的 `abl_log` / `kernel_log` 事后日志分区；
3. 是否有不丢失必要 bootloader 参数的 K1 console override 方案。

**本轮不重编内核、不改 DTB、不制作新镜像。** PREP12 完成后 AI1 将直接给出一次性 K1 framebuffer variant 方案，或明确停止原因；不再重新启动 BoardView/UART 搜索。

## 执行角色

- 执行者：此前完成 PREP04-FIX01 / PREP05 / PREP07 / PREP08 / PREP09 / PREP11 的同一个 WorkBuddy 会话。
- 技术审核与决策：AI1（ChatGPT）。
- 设备：Huawei MatePad 11 DBY-W09 / HOS4.3.0.196(C00E100)。
- GitHub 仓库：`hhdy/matepad11-dby-w09-agent-reports`。
- GitHub 分支：`ai1/boot-v2-first-package-prep`。

## A. 只读设备采集：完整分区名字和容量

仅当平板当前正常开机、ADB 已连接且 KernelSU root 权限已授权时执行。无需切换 USB 模式、重新授权或重启。

允许命令（只读）：
- `adb devices -l`
- `adb exec-out su -c id`
- `adb exec-out su -c 'ls -l /dev/block/by-name'`
- 对存在的 `abl_log`、`kernel_log`、`bootfail`、`rainbow` 项，仅读取 symlink target、`stat` 大小和 `blockdev --getsize64`。
- 如 `/dev/block/bootdevice/by-name` 是本机真实路径，可只读列目录并注明路径。

输出仅包含：
- 分区名；
- symlink target（去除任何序列号/唯一设备标识）；
- 分区字节长度；
- 若有多个槽位，准确记录 a/b 或无槽位。

**不要读取任何分区内容，不运行 dd，不导出 boot、ramdisk、userdata、persist、oeminfo 或校准数据。**

如果 ADB 当前未连接、KernelSU root 未授权、命令需要重启/切模式/额外授权，立即停止，不要自行修复连接。

## B. 只读采集本机 live display / splash 信息

使用已存在的 root ADB 只读能力。原始 live FDT 只允许短暂保存在 WorkBuddy 本机分析目录，不进入 GitHub，不进入交付 ZIP。

### B1. Live FDT

通过 stdout 将 `/sys/firmware/fdt` 读到 PC 本地临时文件，计算大小与 SHA-256，解析后只导出以下筛选信息：

- 根节点 `model`、`compatible`；
- `/rootparam/hardware_version`、`qcom,board_name`、`qcom,boardid`；
- `/chosen` 下所有名字含 framebuffer/splash/display 的子节点和属性；
- `/reserved-memory` 下所有直接子节点的 node name、`reg`、`no-map`、`compatible`、phandle；
- 与 panel/MDSS/DSI display 有关节点的 compatible、status、reg、panel id；
- `/chosen/bootargs` 只输出脱敏后的 kernel-relevant token；必须删去 serialno、panel_sn、MAC、IMEI/MEID、HIMNTN、校准值和任何唯一设备标识；
- initrd start/end 只记录是否存在及范围，不输出其他用户数据。

确认并区分：
- DT 声明的 hardware_version；
- board_name / boardid；
- 实际 framebuffer/splash 节点；
- ABL 后追加的 command-line 参数。

### B2. 当前 HOS framebuffer runtime 观察

只读检查以下现有路径（不存在或不可读就记录，不 mount/remount debugfs）：

- `/proc/fb`
- `/sys/class/graphics/fb0/name`
- `/sys/class/graphics/fb0/virtual_size`
- `/sys/class/graphics/fb0/bits_per_pixel`
- `/sys/class/graphics/fb0/stride`（存在时）
- `/sys/class/graphics/fb0/modes`（存在时）
- `/sys/class/graphics/fb0/device/resource` 或其实际只读 resource 属性（存在时）
- `dmesg` 中筛选 framebuffer / splash / simplefb / mdss / dsi 的少量行；输出必须先过滤敏感字段。

注意：HOS 的 fb0 运行时地址/格式不必然等于 ABL 在 kernel handoff 时使用的 splash buffer；必须分开记录。

## C. ABL splash handoff 定点静态核验

使用已在本地工作区保存的 `abl-hos43-pe.bin` / `abl-decompressed.bin`，仅离线检查，不要重新 dump 或上传完整 ABL。

针对以下关键词与引用点进行静态字符串/XREF/控制流核验：
- `splash_region`
- `cont_splash`
- `framebuffer`
- `Could not get splash memory region node`
- `0x9c000000`（如存在）
- reserved-memory path lookup
- framebuffer address / size / format / display handoff writer

必须回答：
1. ABL 是否按固定路径查找一个 reserved-memory splash 节点？
2. 若需要，该节点准确路径/节点名到底是什么（包括是否带 `@unit-address`）？
3. 没有节点时 ABL 是丢弃 splash、跳过 handoff、报错，还是继续显示但不传给 kernel？
4. ABL 使用的 framebuffer 地址与大小是否可从代码或本机 live FDT 证明？
5. 本机 VD variant 的 panel ID 是否影响 splash buffer geometry/format，还是仅影响已初始化的 panel timing？如无法证明，标记 UNKNOWN。

不得仅照抄社区 VG DTS 的 comment；必须注明是代码证据、当前设备 FDT 证据还是社区推断。

## D. ABL commandline 与 ACK console 覆盖方案

以精确 ACK commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9` 为基准，核对：
- `kernel/printk/printk.c` 的 `console_setup()`、`__add_preferred_console()`：`console=NULL` 的实际语义、last-preferred-console 规则；
- `drivers/of/fdt.c` 的 `early_init_dt_scan_chosen()`：`CMDLINE_FORCE`、`CMDLINE_EXTEND`、bootloader DT bootargs 的拼接顺序；
- `arch/arm64/Kconfig` 的 `CMDLINE`、`CMDLINE_FORCE`、`CMDLINE_EXTEND`；
- `drivers/video/fbdev/simplefb.c` 与 `FRAMEBUFFER_CONSOLE` / `FB_SIMPLE` Kconfig 依赖。

对三种方案分别评估：

1. 仅在 boot header 加 `console=tty0`：预期被 ABL 后置 `console=NULL` 覆盖，确认其不可用。
2. `CONFIG_CMDLINE_EXTEND`：默认命令行先于 bootloader DT bootargs，因此后置 `console=NULL` 仍获胜；确认它不能解决问题。
3. `CONFIG_CMDLINE_FORCE` 或一处最小内核 command-line filter patch：如果使用，必须说明会丢弃/保留哪些 bootloader 参数，并评估 K1 所必需的内存、swiotlb、reserved-memory、initrd handoff 是否受影响。

PREP09 已记录的敏感字段不得复制到公开报告或编译参数。不得将设备 serialno、HIMNTN、panel_sn、MAC、校准数据写入任何源码或 GitHub。

如果 FORCE 会丢弃关键启动参数且无法安全重建，或 patch 方案无法证明不改变必要启动参数，则判定 framebuffer console 的 commandline gate 未通过，不要构建。

## E. Framebuffer DT / kernel config 方案可行性（只分析，不实施）

如果 B/C 已确认本机 framebuffer 地址、长度、format 与 ABL handoff 规则，才评估一份 host-only K1 framebuffer variant 的最小差异：

- Kernel config（以精确 ACK Kconfig 为准）：`CONFIG_VT=y`、`CONFIG_FB=y`、`CONFIG_FB_SIMPLE=y`、`CONFIG_FRAMEBUFFER_CONSOLE=y`、字体支持；检查 `DRM_SIMPLEDRM` 冲突和实际依赖。
- DTB：在 `/chosen` 加 simple-framebuffer 节点；在 `/reserved-memory` 添加准确且不冲突的 splash carveout（通常需 no-map）。保留候选 DTB 中原有所有保留区，不得重排/删除既有 reserved-memory。
- Boot commandline：`console=tty0`、`fbcon`、`ignore_loglevel`，必要时保留社区路线中的 `clk_ignore_unused` / `pd_ignore_unused`，但必须依据 ABL 和时钟/power-domain 证据，而不是机械复制。
- 必须说明 K1-only 的命令行策略对 K2/Android userspace 的限制。K2 fstab blocker 仍保持独立，不因屏幕日志可见而宣称系统启动。

本轮只出最小 diff 设计和风险表，不实际修改源码、配置或 DTB。

## 明确禁止

- 不刷写、不 fastboot、不 reboot、不切换 recovery/EDL；
- 不拆机、不短接、不接探针、不测未知 pad；
- 不写分区、不读取任何分区内容；
- 不 mount/remount debugfs；
- 不修改 GPIO/pinctrl/clock/regulator，不加载模块；
- 不重编译内核，不修改 PREP06/PREP10；
- 不生成新的 boot/DTB/DTBO/ramdisk 二进制；
- 不将完整 live FDT、ABL、boot、ramdisk 或其他专有二进制上传 GitHub；
- 不上传未脱敏 bootargs、serialno、HIMNTN、panel_sn、MAC、IMEI/MEID、校准值；
- 不用社区 VG variant 的 0x9c000000 地址/大小直接代替本机 VD 证据。

如果设备当前 ADB/root 条件不满足，完成可离线完成的 ABL/ACK 静态分析后停止，并明确缺少哪一项设备读取；不要自行恢复设备连接。

## GitHub 交付（必须直接 commit + push）

仓库：`hhdy/matepad11-dby-w09-agent-reports`

分支：`ai1/boot-v2-first-package-prep`

目录：`firmware-analysis/boot-v2/PREP12_K1_DISPLAY_LOG_ROUTE/`

必需文件：
- `PREP12_REPORT.md`：最终裁定、工作边界、已完成/未完成项；
- `partition_inventory.txt`：只列分区名、容量、路径（若设备采集可用）；
- `live_display_facts.txt`：脱敏后的 framebuffer/FDT/reserved-memory facts；
- `abl_splash_handoff.md`：ABL 对 splash region 的代码证据与未知项；
- `cmdline_override_analysis.md`：console=NULL、CMDLINE_FORCE/EXTEND、K1 命令行安全分析；
- `framebuffer_variant_diff_plan.md`：如果条件齐备，列最小 DT/config/cmdline diff；若不齐备，写明唯一阻断；
- `SHA256SUMS.txt`：以上文本文件哈希。

完成后：
1. 直接 commit + push 到指定分支和目录；
2. 回复 branch、commit SHA、各文件链接；
3. 不把二进制放到公开仓库；
4. 不附聊天 ZIP，除非任务书外有 AI1 后续明确要求。

## 完成后的停止条件

PREP12 完成即停止。AI1 将直接决定是否制作唯一的 K1 framebuffer host-only candidate，或者判定 panel route 不成立并转向已存在的日志分区。不得自行开始 PREP13 或新的泛化审查轮。
