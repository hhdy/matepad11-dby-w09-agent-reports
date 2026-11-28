# K1-USB-OBSERVABILITY-CHECK01 — 现有 ACK / PREP10 USB 诊断通道可用性检查

**签发：AI1（ChatGPT）**  
**执行：WorkBuddy Agent（本机离线）**  
**项目：Huawei MatePad 11 DBY-W09 / HWDBY / SM8250(Kona)**  
**任务性质：仅主机端文件检查；不连接平板、不重启、不运行设备命令、不修改源码或镜像。**

## 0. 本任务为什么存在

目前已完成：
- PREP10 候选镜像身份冻结：`d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091`；46,563,215 B。
- Hybrid ABL 当前载荷身份及容器字节关系已独立复现。
- Fastboot 设备层查询已证明 `unlocked=yes`、`secure=yes`、`is-userspace=no`，但 ABL 对 RAM boot 镜像认证的具体行为仍 UNKNOWN。
- Framebuffer K1 路线 BLOCKED。
- UART12 earlycon 路线 HOLD：QUPV3_1 SE4 clock、GPIO34/35 qup12 mux、GENI protocol 在 ABL handoff 的实际状态仍无可靠证据。

因此目前存在一个实际问题：**即使有一天 ABL 接受 PREP10 并进入 ACK 内核，当前电脑是否有任何已有的 USB 诊断路径能观察到启动进展？**

本任务只查本机已有 ACK build config、PREP10 boot 与 ramdisk 文件，不制作新内核、不修改 init、不改镜像。目标是回答：
1. 是否能从现有 image/ramdisk 配置判断，ACK 到达 Android init 后是否可能重新枚举为 ADB；
2. 有没有已经编译并可在早期阶段使用的 USB console / USB serial gadget；
3. USB ADB 如果存在，它到底只能证明 K3（最小用户态），还是能观察 K1（内核早期日志）。

**不要把“ADB 可能出现”宣传成“有 K1 早期日志”。**

## 1. 冻结输入身份（不得替换）

### 内核构建
- ACK tag：`android17-6.18.33_r00`
- commit：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`
- Kleaf target：`//common:dby_w09`
- build source tree SHA：`c56d93eafa35057d65176db6594d67d5144868a0`
- Kernel Image SHA-256：`f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21`
- 实际 build config：`config-used-for-build.config`，238,410 B，SHA-256 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`
- `config-olddefconfig-normalized.config` 不是实际构建 config，不得替代。

### PREP10 候选
- 文件：`dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img`
- 大小：46,563,215 B
- SHA-256：`d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091`
- Header version：2
- cmdline prefix：`ignore_loglevel earlycon=qcom_geni,0xa90000`
- kernel payload SHA-256：`f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21`
- embedded ramdisk：519,986 B，SHA-256 `a4b94ff6bb2d9525fa6ad0010d8efa4c6fe2bd49d36956115c26a656b631af3c`
- DTB slot：1,216,399 B，SHA-256 `7bb9a1fba8d4574bce9d54795d67217d6f72857e792cbafa626ece3459b996b7`

### 独立 ramdisk
- stock separate ramdisk 备份大小：2,097,152 B
- SHA-256：`4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb`

如任何冻结文件不存在或哈希不匹配：记录 `MISSING_OR_MISMATCH`，停止依赖该文件的检查。不得用其它版本的 config、boot、ramdisk 替代。

## 2. 阶段 A — 精确身份复核

1. 找出实际 build config、Image、PREP10 boot、embedded ramdisk、separate ramdisk。
2. 为每个文件记录：文件名、大小、SHA-256、绝对路径（报告公开版可仅保留相对路径）。
3. 解析 PREP10 boot v2，确认 kernel 与 embedded ramdisk 的哈希和尺寸仍与冻结值一致。
4. 不修改/重打包候选镜像。

## 3. 阶段 B — Kernel USB / Gadget / Console 配置审计

只读取准确匹配 SHA 的 `config-used-for-build.config`。搜索并记录下列配置项的实际值（`y/m/n/not found`），不可把 `olddefconfig` 文件结果代入：

### USB 控制器 / Peripheral / Gadget
- `CONFIG_USB`
- `CONFIG_USB_GADGET`
- `CONFIG_USB_DWC3`
- 所有 `CONFIG_USB_DWC3_*` Qualcomm / MSM / QCOM 相关配置（以文件中真实存在项为准）
- `CONFIG_USB_ROLE_SWITCH`
- `CONFIG_USB_CONFIGFS`
- `CONFIG_USB_CONFIGFS_F_FS`
- `CONFIG_USB_F_FS`
- `CONFIG_USB_CONFIGFS_F_ACM`
- `CONFIG_USB_CONFIGFS_ACM`
- `CONFIG_USB_G_SERIAL`
- `CONFIG_USB_SERIAL`
- `CONFIG_USB_CONFIGFS_UEVENT`
- `CONFIG_USB_CONFIGFS_F_MASS_STORAGE`
- `CONFIG_USB_FUNCTIONFS`
- `CONFIG_ANDROID`
- `CONFIG_USB_ANDROID`（若该版本存在）

### Debug / Console
- `CONFIG_EARLY_PRINTK`
- `CONFIG_SERIAL_EARLYCON`
- `CONFIG_SERIAL_QCOM_GENI`
- `CONFIG_SERIAL_QCOM_GENI_CONSOLE`
- `CONFIG_USB_EARLY_CONSOLE`（仅当 config/source 确实存在此选项时记录；不得假设有此项）
- `CONFIG_USB_GADGET_DEBUG_FILES`
- USB serial / ACM / FunctionFS 相关模块是否 built-in 或 module。

如果需要检查源码是否存在某驱动/ Kconfig 项，只允许在本机已存在、且与 frozen commit 一致的源码树中 grep；不要在线下载其它版本源码替代。

需要明确区分：
- USB device controller 驱动存在；
- UDC gadget framework 已启用；
- FunctionFS / ADB function 可用；
- 有专门早期 USB console；
- 有 USB serial gadget；
它们是不同能力，不能混为一谈。

## 4. 阶段 C — PREP10 embedded ramdisk 与独立 ramdisk 检查

1. 在 PC 端只读解包 embedded ramdisk 和 separate ramdisk，保留原始文件哈希；解包结果存到临时目录。
2. 记录实际格式（gzip/lz4/cpio 等）、条目数和关键文件哈希；不得解包或查看用户数据。
3. 只检查启动诊断相关文件：
   - `/init`
   - `init*.rc`
   - `ueventd*.rc`
   - `fstab*`
   - `/system/bin/adbd`、`/system/bin/charger` 等必要二进制是否存在（只记录存在性、文件 hash、ELF 架构，不运行）
   - USB gadget 相关脚本/属性/节点
4. 搜索并记录真实命中：
   - `adbd`
   - `sys.usb.config`
   - `sys.usb.state`
   - `sys.usb.controller`
   - `androidboot.usbcontroller`
   - `ffs.adb`
   - `functionfs`
   - `usb-ffs/adb`
   - `setprop sys.usb.config adb`
   - `write /config/usb_gadget`
   - `start adbd`
   - `mount functionfs` / `mount configfs`
   - `UDC` bind / gadget composition
5. 必须给出 init 顺序：哪些动作发生在 first-stage init 之前、first-stage init 后、late-init/boot 后。不要把一个字符串命中当作实际执行路径。
6. 如果 candidate boot 的 embedded ramdisk 和 separate ramdisk 如何组合/选择无法从已知 ABL handoff 证实，明确 `RAMDISK_HANDOFF = UNKNOWN`，不自行选一个作为 active ramdisk。
7. 不要改 `init*.rc`，不添加 adbd，不生成测试 ramdisk，不重打包 boot。

## 5. 阶段 D — USB 观察能力矩阵

根据 B/C 真实证据，对以下每项给出 `CONFIRMED / POSSIBLE / ABSENT / UNKNOWN`，附文件、行号、config symbol 或调用顺序：

| 通道 | 定义 | 能证明到哪一阶段 |
|---|---|---|
| Fastboot `boot` 返回值 | ABL 对下载/boot 请求的响应 | 只证明 ABL 的请求处理结果，不证明 kernel 执行到哪一步 |
| Kernel USB device re-enumeration | Linux UDC/gadget 初始化后主机看到 USB device 变化 | 通常只证明 kernel 已推进到 USB controller/gadget 初始化附近；需要精确限制推断 |
| ADB online | FunctionFS + adbd + init/USB 属性配置实际成功 | K3 最小用户态/ADB，不是 K1 early log |
| USB CDC ACM / serial gadget | Gadget ACM function + UDC bind + host serial driver | 若只在 userspace init 配置，不能作为 K1 early console |
| USB early console | 内核在 init 前已能用 USB 传输 printk | 只有发现准确驱动、配置和初始化路径才可 PASS |
| UART12 earlycon | `qcom_geni` earlycon at `0xa90000` | K1；目前 HOLD |
| Framebuffer/fbcon | kernel fbcon 在本机 splash 接管后显示日志 | K1；目前 BLOCKED |

对“设备 USB 消失/重连”必须给出三类解释及无法区分项。不得声称 USB 消失就代表 kernel panic，也不得声称 ADB 不出现就代表 kernel 未启动。

## 6. 最终结论规则

报告必须给出：

```
PREP10_IDENTITY                  = PASS | FAIL
BUILD_CONFIG_IDENTITY            = PASS | FAIL
USB_UDC_DRIVER                   = CONFIRMED | ABSENT | UNKNOWN
USB_GADGET_FRAMEWORK             = CONFIRMED | ABSENT | UNKNOWN
USB_FUNCTIONFS_ADB_CONFIG        = CONFIRMED | ABSENT | UNKNOWN
ADBD_BINARY_AND_INIT_PATH        = CONFIRMED | ABSENT | UNKNOWN
USB_CDC_ACM_GADGET               = CONFIRMED | ABSENT | UNKNOWN
USB_EARLY_CONSOLE                = CONFIRMED | ABSENT | UNKNOWN
ADB_REACHABLE_AFTER_INIT         = CONFIRMED | POSSIBLE | ABSENT | UNKNOWN
RAMDISK_HANDOFF                  = CONFIRMED | UNKNOWN
K1_EARLY_OBSERVABILITY           = ADEQUATE | INADEQUATE | UNKNOWN
K3_USB_ADB_SUCCESS_SIGNAL        = AVAILABLE | UNAVAILABLE | UNKNOWN
```

判定规则：
- 即使 ADB 路线可行，也必须标注为 K3 success signal，不可冒充 K1 log channel。
- 若 USB early console、UART earlycon 和 framebuffer 均未有已确认路径，则 `K1_EARLY_OBSERVABILITY=INADEQUATE`。
- 如果 ADB 是唯一可用路径，必须解释第一次测试中“设备未出现 ADB”无法区分的情况，不得把它当失败定论。
- 不因本任务通过就自动批准 `fastboot boot`。

## 7. 严格禁止

- 不连接平板；不执行 ADB/Fastboot/OEM 命令；不 reboot 或切换模式。
- 不执行 `fastboot boot` / flash / erase / format / update。
- 不读取任何设备分区，不使用 EDL/9008。
- 不运行 `adbd`、init 或任何从 ramdisk 提取的二进制。
- 不修改内核 config、源码、DTS、DTB、DTBO、boot、ramdisk。
- 不重新编译，不生成新镜像，不改候选 SHA。
- 不访问或读取 userdata、persist、oeminfo、TEE key、IMEI、MAC、校准数据。

## 8. 交付

输出：`K1_USB_OBSERVABILITY_CHECK01_REPORT.zip`

必须包含：
1. `K1_USB_OBSERVABILITY_CHECK01_REPORT.md`
2. `kernel_usb_config.txt`
3. `ramdisk_usb_init_audit.md`
4. `observability_matrix.md`
5. `host_tools_versions.txt`
6. `SHA256SUMS.txt`

ZIP 不得包含完整 Kernel Image、完整 boot、完整 ramdisk、设备唯一标识或敏感数据。可包含最小必要的脱敏 init 片段（只保留相关行并标注来源文件/行号）。报告与复现脚本可以上传 GitHub；原始固件不上传。

若 config/image/ramdisk 缺失或哈希不匹配，交付 stop report，不使用替代版本。

## 9. 停止条件

任务完成后立即停止，提交 ZIP 给 AI1。不得继续生成候选，不得尝试实机启动，不得让用户进入任何模式。

**这是一轮有明确终点的最后可观测性检查：它只决定 USB 能否成为启动后的成功信号，以及 K1 阶段是否仍完全不可观测。它不允许尝试启动。**