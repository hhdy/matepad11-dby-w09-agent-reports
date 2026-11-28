# PREP12-N — AI1 独立审核与 UART earlycon 语义纠正

- 审核日期：2026-11-28
- ZIP：PREP12_K1_DISPLAY_LOG_ROUTE.zip
- ZIP SHA-256：c56192e726603f9e7c3d454657ad21ff9440602db590deed7c8aff39b2d855d6
- ACK commit：8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

## 1. 交付验收

ZIP 32,330 B，8 项；SHA-256 与交付记录一致。SHA256SUMS.txt 中 7 个文件哈希全部重新核验通过。PREP10 boot 二进制缺失一事保留为缺失，没有替代来源。

PREP12 的只读取证可以结项：88 项分区目录完整；未读取分区内容；fresh live FDT 与 PREP09 哈希一致；本机 splash 地址/大小确认而 format 未知；候选 DTB 的 framebuffer/simplefb 配置缺失；设备刷写仍 NO-GO。

## 2. 接受的硬件/显示结论

- 本机 splash 区域：0x9c000000 / 0x2300000；pixel format UNKNOWN。
- disp_rdump_region@9c000000 与 splash 前 8 MiB 重叠，不得当作普通空闲 framebuffer 使用。
- ABL 字面量路径为 /reserved-memory/splash_region；本机节点名为 cont_splash_region@9c000000；匹配逻辑和 kernel handoff 时 scanout 连续性尚未证明。
- 因此不制作 K1 framebuffer candidate，不填入社区 VG 的 a8r8g8b8，也不照搬其 geometry。
- abl_log/kernel_log 等所查分区名不存在；没有读取任何分区内容。

## 3. 纠正 AI1 先前对 console=NULL 的判断

PREP12 正确发现：printk.c 的 console_setup() 对小写 "null" 使用 ttynull；ABL 是大写 "NULL"，因此进入通用路径，登记名为 "NULL" 的 preferred console。它不匹配普通 console 驱动。

但 AI1 先前推断“console=NULL 必然让已注册 earlycon 静默”是错误的，现撤销。

精确 ACK 启动顺序：
1. start_kernel() 调 setup_arch()，生成 boot_command_line。
2. parse_early_param() 先解析 earlycon 和 console 的 early alias。
3. earlycon=qcom_geni,0xa90000 通过 drivers/tty/serial/earlycon.c 的 setup_earlycon()，成功后调用 register_console()。
4. 这个 early pass 中 console=ttynull / console=NULL 只尝试把值当 earlycon 名称；不匹配时 -ENOENT 被忽略，不调用 printk.c::console_setup()，也不设置 preferred_console。
5. 后续普通 parse_args() 才调用 printk.c::console_setup()，按顺序登记 console=ttynull 和 ABL 尾部 console=NULL。

所以若 GENI earlycon 硬件 setup 成功，它可能先以 CON_BOOT 注册。之后的幽灵 preferred console 不会仅凭改变 preferred_console 就注销已经注册的 bootconsole。

进一步，drivers/tty/ttynull.c 后续注册的 ttynull console 匹配的是第一条 console=ttynull，但 ABL 尾部的 NULL 才是最后 preferred 项，因此 ttynull 不一定成为 CON_CONSDEV；register_console() 自动注销 bootconsole 的 handover 条件也不应被假定已触发。后续 QCOM ttyMSM real console 若无法匹配最后的 NULL 项，也不会自然接管。

此为源码推导，不是本机 UART 输出实测。必须把“console=NULL 阻断普通 preferred console”和“console=NULL 关闭已注册 bootconsole”区分开。

源码：
- https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/init/main.c#L207
- https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/tty/serial/earlycon.c#L249
- https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/kernel/printk/printk.c#L2591
- https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/kernel/printk/printk.c#L3997
- https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/tty/ttynull.c#L57

ignore_loglevel 确实能避免 loglevel=0 的等级过滤，但不能开启 UART 硬件。

## 4. GENI 硬件仍未证实

精确 ACK qcom_geni_serial_earlycon_setup() 要求 membase 可访问、geni_se_read_proto() 返回 GENI_SE_UART，并读写 GENI SE/FIFO/UART 寄存器；该 setup 路径本身没有显式打开 QUP SE clock，也没有配置 GPIO pinmux。

故 earlycon printk 路径不再因 console=NULL 被判死，但硬件可用性仍未知：ABL 跳转前 QUPV3_1 SE4 的时钟/电源域是否保持、GPIO34/35 是否仍为 UART mux、GENI protocol 是否仍是 UART，以及 PCB TX 是否可访问，都没有证据。PREP09 的 HOS 完整启动后 clock/mux 状态不能代表 ABL handoff 瞬间。

源码：
- https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/tty/serial/qcom_geni_serial.c#L1470

## 5. 决策修订

- framebuffer K1：BLOCKED；本轮不继续。
- 不批准为了 UART earlycon 去做 early_init_dt_scan_chosen() 的 console=NULL filter patch；它不是 earlycon 注册的必要条件，并可能改变后续 console handover。
- 保留 PREP10 ignore_loglevel + earlycon=qcom_geni,0xa90000 作为待审候选思路，但 PREP10 镜像二进制本体尚未重新找到/核验。
- 唯一下一步：WorkBuddy 对已冻结 ABL 二进制做一轮离线函数级静态审计，解码 UartLogCtlCmdline 的条件/命令入口，以及 QUPV3_1 SE4、GPIO34/35 的时钟、电源域、pinmux 和 ABL handoff 是否关闭/保留。
- 如果 ABL 输入 hash 不匹配或缺失，停止。若证据仍不充分，输出 HOLD，不再做泛化检查。
- 任何实机启动前仍需先证明 fastboot 接受与恢复路径；当前 DEVICE_FLASH = NO-GO。此审核没有执行设备命令、重启、刷写、修改或编译。
