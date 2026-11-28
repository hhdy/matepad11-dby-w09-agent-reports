# PREP10 — K1 Earlycon + ignore_loglevel 主机端预览

## 结论

**仅完成离线 header cmdline 变体；未进行设备测试，不是可刷写/可启动/已接受的镜像。**

PREP09 观察到 ABL 在 boot header cmdline 之后追加 `loglevel=0`。ACK 6.18.33 对应源码 `kernel/printk/printk.c` 中，`ignore_loglevel` 被定义为 `early_param` 并将全局布尔值置 true；打印抑制条件为 `level >= console_loglevel && !ignore_loglevel`。因此将 `ignore_loglevel` 放在 `earlycon` 前面，预期可抵消后续 `loglevel=0` 的级别过滤。

这只解决 printk 过滤，不解决 UART12 是否有可用硬件状态或实体焊盘。GENI earlycon setup 本身会读取 GENI 协议并配置 FIFO/UART 寄存器，但不会打开时钟或选择 pinctrl 状态；这两个条件仍取决于 ABL 交接时遗留配置。

## 本轮唯一修改

将 PREP06 header cmdline 的第一个 token 改为 `ignore_loglevel`，其后所有参数顺序与文本不变。`ignore_loglevel` 放在 `earlycon=qcom_geni,0xa90000` 之前。重算并更新 AOSP boot header v2 SHA-1 ID。

未修改 kernel Image、embedded ramdisk、second、recovery_dtbo、DTB slot、DTBO；未修改 separate ramdisk、vbmeta 或任何设备分区。

## 镜像身份

- 来源 PREP06 SHA-256：`aa25553170ace181bea3d2457962e0d13fff0277511ea7a7bead657e798196a8`
- 输出镜像 SHA-256：`d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091`
- 大小：46,563,215 B
- AOSP boot ID：`8f1501bcba02b9e787386b97171c6d0b852a9ef7`
- cmdline 前缀：`ignore_loglevel earlycon=qcom_geni,0xa90000`

## PREP09 约束与边界

- Live FDT 中 UART12 节点为 `/soc/qcom,qup_uart@a90000`，GPIO34/35 的 `qup12` pinctrl 已声明，但运行 HOS 时 pinmux 为 UNCLAIMED，SE 时钟 enable/prepare count 为 0。
- 此 runtime 状态不能证明 ABL 跳转内核前没有留 mux/clock，但也不能证明它有留。
- 物理 pad、TX/RX 方向、逻辑电平未确认。不能接线。
- 精确 ACK 源码中 `OF_EARLYCON_DECLARE(qcom_geni, "qcom,geni-debug-uart", ...)`；setup 检查 `geni_se_read_proto()`，不启用 clocks/pinctrl。
- ABL 的 `console=NULL` 与 earlycon bootconsole 的相互作用仍未在设备上验证。
- Fastboot 接受性、恢复演练及 K2 fstab 阻断均未改变。

## 操作安全

未连接设备，未执行 ADB/Fastboot/reboot/flash；未重编内核；未修改 DTB/DTBO/ramdisk。

## 二进制核验

- Kernel SHA-256：`f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21`
- Embedded ramdisk SHA-256：`a4b94ff6bb2d9525fa6ad0010d8efa4c6fe2bd49d36956115c26a656b631af3c`
- DTB slot SHA-256：`7bb9a1fba8d4574bce9d54795d67217d6f72857e792cbafa626ece3459b996b7`
- DTBO companion SHA-256：`f185c13de5f9d2ca8dc2610c4cef33d12db601bfa29bae079fb5827951c1a6cc`（仅参考，不代表写分区）

完整 PREP10 二进制仅在本地交付包中，不上传公开仓库。
