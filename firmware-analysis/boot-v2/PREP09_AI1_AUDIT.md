# PREP09 — AI1 独立审核结论

- 审核对象：`PREP09_LIVE_FDT_UART12_READONLY.zip`
- WorkBuddy ZIP SHA-256：`3427d27f3cc184fb0e15d3174041ecbc1ff21d5842b0fc475152ad0f5c3c5f7d`
- 压缩包大小：18,473 B
- ZIP integrity：PASS
- 内部 `SHA256SUMS.txt`：7/7 文件哈希 PASS
- 设备操作：报告记录只读 ADB + KernelSU root；未重启、未写设备；原始 live FDT 未进入交付 ZIP。

## 1. Live FDT 身份

- Live FDT：800,324 B；SHA-256 `dc0ab259c800d52946d4a3d633fe1546430895d2878054d0376d428a135da52d`；FDT magic/totalsize 自洽。
- `/model`：Huawei Technologies, Inc. DBY-W09。
- `/rootparam/hardware_version`：`SH1DBSLM`，只能标记为 `DT_DECLARED_HARDWARE_VERSION`，不是物理 PCB 丝印或 efuse 证明。
- `/rootparam/qcom,board_name`：`DBY_W09_VD`。
- `/rootparam/qcom,boardid`：四个 BE cell `0x8 0x2 0x0 0x6`，与属性层 `8206` 一致。
- 当前 live FDT 是 HOS 运行时树；不能直接等同于 PREP06 候选 DTB。

## 2. UART12 节点与 runtime 证据

Live FDT 节点 `/soc/qcom,qup_uart@a90000`：

- `status = "okay"`
- `compatible = "qcom,msm-geni-console"`
- MMIO `0xa90000`，长度 `0x4000`
- QUPV3_1 GENI SE4，clock rate 7,372,800 Hz
- default pinctrl 声明 GPIO34/GPIO35、function `qup12`、drive strength 2 mA
- 两个 GPIO 的 TX/RX 方向未由 FDT 明确标识。

HOS 运行时只读观察：

- UART12 platform device 无 `driver` symlink；无 `ttyMSM*`。
- `/proc/consoles` 为空。
- GPIO34/35 在 pinmux 显示 `(MUX UNCLAIMED)`，pinconf 为空。
- QUPV3_1 SE4 时钟 enable/prepare count 为 0（重复采样仍为 0）。
- 其它两个已绑定端口分别映射 ttyHS0/ttyHS1，不是 UART12。

解释边界：这些是 HOS 完全启动后的内核运行时状态，不能据此证明 ABL 跳转 ACK 内核前没有配置过 pinmux 或打开时钟；同样也不能证明它们已配置。

## 3. ACK 源码精确核验

已从 `aosp-mirror/kernel_common` 的确切 ACK 构建提交 `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9` 读取源码：

- `drivers/tty/serial/qcom_geni_serial.c` 声明 `OF_EARLYCON_DECLARE(qcom_geni, "qcom,geni-debug-uart", qcom_geni_serial_earlycon_setup)`。
- `qcom_geni_serial_earlycon_setup()` 会检查 `geni_se_read_proto()`，并初始化 GENI FIFO/UART 寄存器；它本身没有启用相关 clock，也没有选择 pinctrl state。
- 同文件 platform-driver OF match table 没有 `qcom,msm-geni-console`，因此 PREP09 的该 DT compatible 不会由这份驱动正常绑定为 platform device。explicit-address earlycon 与 platform-device probe 是两条不同路径。
- `kernel/printk/printk.c` 将 `ignore_loglevel` 定义为 `early_param`；`suppress_message_printing()` 的条件是 `level >= console_loglevel && !ignore_loglevel`。

源码锚点：

- https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/tty/serial/qcom_geni_serial.c
- https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/kernel/printk/printk.c

## 4. ABL bootargs 影响

PREP09 比较 boot header cmdline 与 live `/chosen/bootargs`：ABL 在镜像 cmdline 后追加 `loglevel=0` 和 `console=NULL`。

- 后置 `loglevel=0` 会压低普通 printk 输出等级。
- `ignore_loglevel` 是独立布尔 early parameter，设置后会让 printk 的级别过滤条件不再抑制消息；它不是一个被后置 `loglevel=0` 清零的数值参数。
- 仍需将 `ignore_loglevel` 放在 `earlycon` 前面，以便它先于 earlycon 初始化时可能发生的打印被解析。
- `console=NULL` 与 earlycon bootconsole 的实际交互仍未在设备上验证。

## 5. K1 UART 路线裁决

`qcom_geni` 名称与 `0xa90000` 地址属于有源码依据的 earlycon 配置；PREP09 进一步证实 0xa90000 是设备 DT/ABL 声明的 console 型 GENI SE。

但输出链仍有未证前提：

1. ABL handoff 时 UART12 的 SE clock 必须可读/可写；
2. GPIO34/GPIO35 必须处于 `qup12` mux；
3. `geni_se_read_proto()` 必须返回 UART；
4. 必须存在可接触的实体 pad，且 TX/RX 方向、电平正确。

因此：`EARLYCON_SOFTWARE_NAME = CONFIRMED`；`UART12_DEVICE_ROLE = STRONGLY_SUPPORTED`；`EARLYCON_PHYSICAL_OUTPUT = UNVERIFIED/LOW`；`UART_PHYSICAL_ACCESS = UNCONFIRMED`。

不能把 GPIO34/35 当作已确认测试焊盘，也不能指导用户接线。不得将 SH1DBYLM BoardView 直接套用到 SH1DBSLM/DBY_W09_VD。

## 6. 下一步

PREP10 是 AI1 基于 PREP06 制作的 host-only 变体：只在 boot header cmdline 开头插入 `ignore_loglevel`，放在 `earlycon=qcom_geni,0xa90000` 之前，并按 AOSP v2 规则重算 ID。它预计解决 ABL 后置 `loglevel=0` 的过滤，但不解决 GPIO 时钟/物理焊盘未知。

PREP07 的 Fastboot 接受性和恢复路径仍未确认；K2 fstab 阻断不变。所有设备操作仍为 NO-GO，需独立的最终授权流程。
