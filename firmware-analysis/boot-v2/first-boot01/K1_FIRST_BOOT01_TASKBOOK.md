# K1-FIRST-BOOT01 — PREP10 单次 Fastboot RAM Boot 实机测试

**签发：AI1（ChatGPT）**  
**执行：WorkBuddy Agent（必须在连接目标平板的 Windows 主机上执行）**  
**项目：Huawei MatePad 11 DBY-W09 / HWDBY / SM8250(Kona)**  
**任务性质：一次性临时启动尝试 + 主机侧观察；不得刷写、擦除或修改设备分区。**  
**授权状态：用户已明确授权本任务规定的唯一一次 `fastboot boot`。**

---

## 0. 任务目标与边界

这是第一次真实设备启动尝试。目标不是要求一次达到 Android 桌面，而是回答三个问题：

1. 当前 Hybrid ABL 是否接受冻结的 PREP10 boot-v2 镜像作为 RAM boot 输入；
2. 若接受，主机是否观察到设备离开 Fastboot 并重新枚举；
3. 是否出现 ADB `device` 状态，从而确认启动至少到达 K3（ADB 用户态可用阶段）。

**本轮仅允许一次 `fastboot boot` 命令。** 命令一旦发出，即视为唯一一次尝试已经消耗；不因超时、无 ADB、屏幕黑屏或结果不明确而重发。

### 绝对禁止

- `fastboot flash`、`erase`、`format`、`update`、`set_active`、`boot` 以外的任何写入/安装命令；
- `fastboot reboot`、`reboot-bootloader`、`oem`、`flashing`、`bootctl` 等模式切换/解锁/锁定命令；
- ADB `shell`、`root`、`remount`、`push`、`install`、`sideload`、`reboot` 或任何数据写入命令；
- EDL/9008、HiSuite 恢复、TWRP、刷写 recovery、修改 vbmeta/ABL；
- 第二次 `fastboot boot`，或任何替代镜像/ramdisk 的启动尝试；
- 代替用户长按电源键、拔插电源、按键组合或进行其他物理恢复操作；
- 擅自判定设备已经变砖或自行执行恢复。

`fastboot boot` 本身不执行 boot 分区 flash，但这不等于整个启动过程绝对零写入：被启动的内核/init 可能探测、挂载或触及其他分区。因此不得把本测试描述成“完全无持久化风险”。本轮不主动进入 ADB shell，也不执行任何主动写入操作。

---

## 1. 冻结候选身份（不得替换）

文件名：

`dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img`

预期大小：`46,563,215` bytes  
预期 SHA-256：

`d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091`

AOSP boot header version：`2`  
Kernel Image SHA-256：

`f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21`

PREP10 其他冻结身份：

- ACK tag：`android17-6.18.33_r00`
- ACK commit：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`
- Kleaf target：`//common:dby_w09`
- patched source tree SHA-256：`c56d93eafa35057d65176db6594d67d5144868a0`
- embedded ramdisk：`519,986` bytes，SHA-256 `a4b94ff6bb2d9525fa6ad0010d8efa4c6fe2bd49d36956115c26a656b631af3c`
- DTB slot：`1,216,399` bytes，SHA-256 `7bb9a1fba8d4574bce9d54795d67217d6f72857e792cbafa626ece3459b996b7`

PREP10 身份此前已有独立重现与验证。本任务不重新制作、不修改、不重打包该镜像。

### 候选文件定位规则

1. 在之前 PREP10 构建输出目录、项目工作目录、任务交付目录及用户桌面/下载目录中查找上面**精确文件名**。
2. 对找到的候选计算实际文件大小与 SHA-256。
3. 如果没有找到，或大小/hash 不完全匹配，立即停止；不从其它 ZIP、PREP06、旧候选或网络下载替代。
4. 如果找到多个副本，只允许使用 hash/size 完全匹配的副本，并在报告中记录实际绝对路径；不要更改文件名或文件内容。

---

## 2. 阶段 A — 设备连接与只读前置检查

先建立本次唯一测试日志目录，例如：

`K1_FIRST_BOOT01_YYYYMMDD_HHMMSS/`

保存命令原始 stdout/stderr、时间戳、退出码。日志中如出现设备序列号，公开报告必须脱敏（只保留末 4 位或统一写 `<REDACTED>`）。

### A1. 核验候选

输出以下字段：

```text
CANDIDATE_FILENAME
CANDIDATE_ABSOLUTE_PATH
CANDIDATE_SIZE_BYTES
CANDIDATE_SHA256
CANDIDATE_IDENTITY = PASS | FAIL
```

只有 `46,563,215` bytes 且 SHA-256 完全匹配时才可进入 A2。

### A2. 核验 Fastboot 设备数量

执行只读命令：

```powershell
fastboot devices -l
```

继续条件：检测到**恰好一个** Fastboot 设备。零个或多于一个均停止，不执行 boot。

选定该设备的 serial，并在后续所有 Fastboot 命令中使用显式 `-s <serial>`，避免误操作其他设备。日志与报告脱敏 serial。

### A3. 只读 getvar 基线复核

对同一 serial 执行并保存原始输出：

```powershell
fastboot -s <serial> getvar product
fastboot -s <serial> getvar unlocked
fastboot -s <serial> getvar secure
fastboot -s <serial> getvar is-userspace
fastboot -s <serial> getvar partition-size:boot
```

此前已知基线：

```text
product = kona
unlocked = yes
secure = yes
is-userspace = no
partition-size:boot = 0x6000000
```

注意：`kona` 是平台标识，不能单独作为机型身份；`secure=yes` 与 `unlocked=yes` 必须如实记录，不得将 unlocked 推导成 ABL 必定接受未签名 RAM boot。

以下任一情况发生即停止且不执行启动：

- 设备 serial 数量不是 1；
- `is-userspace` 不是 `no`（不在 bootloader Fastboot）；
- `unlocked` 不为 `yes`；
- product/boot partition size 与上述基线明显不符；
- getvar 显示设备身份或状态不一致；
- 主机 USB 连接不稳定，或 Agent 无法确认目标设备就是本项目平板。

`secure=yes` 是已知基线，不是停止条件；它意味着 ABL 可能拒绝 RAM boot 镜像，应将拒绝视为有效测试结果，而不是尝试绕过认证。

### A4. 进入唯一启动命令前的闸门

报告并复核：

```text
CANDIDATE_IDENTITY = PASS
FASTBOOT_DEVICE_COUNT = 1
FASTBOOT_TARGET_SELECTED = PASS
GETVAR_BASELINE = MATCH
TEST_ATTEMPT_REMAINING = 1
```

全部通过才进入阶段 B。任意一项失败则 `PREBOOT_GATE = STOP`，不得发出 `fastboot boot`。

---

## 3. 阶段 B — 唯一一次 fastboot boot

**只允许执行这一条启动命令一次：**

```powershell
fastboot -s <serial> boot "<PREP10 的绝对路径>"
```

不得添加第二个 ramdisk 参数，不得拼接任何额外镜像，不得更改 cmdline，不得先后尝试其他文件。按 PREP10 冻结原样发送。

必须记录：

- 命令发出时间；
- fastboot 完整 stdout 和 stderr；
- 进程退出码；
- 命令是否正常返回、报错或持续挂起；
- 若输出有 `Sending` / `Booting` / `OKAY` / `FAILED` 等行，逐字保存；
- 命令后 USB 设备是否断开/重新枚举（只记录主机观察，不做设备操作）。

### B1. 结果分类

- 明确收到 ABL `FAILED`、`Load Error`、`Failed to load/authenticate boot image` 等拒绝信息：`ABL_RAMBOOT = REJECTED`。立即结束，不重试。
- 收到发送/启动 `OKAY`：仅标记 `FASTBOOT_COMMAND = ACCEPTED_OR_ACKNOWLEDGED`，不可据此声称 kernel 已成功运行。
- 命令超过 180 秒仍未返回：`FASTBOOT_COMMAND = HUNG_OR_TIMEOUT`。不要杀进程，不再启动任何 fastboot 命令，不做断电/重启；保留现场并向用户报告。
- 其他错误：原样记录，分类 `UNKNOWN_ERROR`，立即结束。

注意：fastboot 对下载/启动请求的 `OKAY` 可能只代表 ABL 接受/处理了请求，不能证明 Linux 已完成解压、跳转或执行到 init。

---

## 4. 阶段 C — 主机侧观察（只读，最多 5 分钟）

只有阶段 B 命令正常返回、设备未处于明显挂死状态时，才进行此观察。

### C1. USB / Fastboot 状态

在启动命令返回后记录：

```powershell
fastboot devices -l
```

然后观察 Windows 设备管理器/PnP 是否发生 USB 设备移除与重新枚举。只能观察，不能禁用/启用设备、拔插线缆或手动切换接口。

### C2. ADB 轮询

最多 5 分钟，每 5 秒一次，执行只读：

```powershell
adb devices -l
```

保存每次时间戳和输出。若看到唯一目标设备进入 `device` 状态：

- 立即记录 `ADB_STATE = DEVICE` 和首次出现时间；
- 停止轮询；
- 不再执行 `adb shell` 或其他 ADB 命令。

如果设备显示 `offline`、`unauthorized` 或仅处于 `recovery/sideload` 类状态，原样记录，不等同于 ADB K3 成功。

如果连接了多台 ADB 设备或无法将出现的 ADB 设备唯一对应到本次目标平板，标记 `ADB_TARGET_IDENTITY = AMBIGUOUS`，不得声称成功。

5 分钟内无 ADB `device` 状态：

`ADB_STATE = NOT_OBSERVED_WITHIN_300S`

这**不能**判定内核未启动，也不能判定 kernel panic。

### C3. 立即停止的情形

出现以下任一情况，结束所有观察，不做恢复操作：

- 设备突然断开且未重新出现；
- 主机 Fastboot/ADB 均无法识别设备；
- 平板疑似冻结、黑屏或持续重启；
- Fastboot 命令挂起；
- 出现任何要求解锁、刷写、擦除、确认恢复或更改安全状态的提示。

Agent 只需保全日志并报告。**设备强制重启、长按电源、拔线或其他物理恢复，必须等待用户另行明确指示。**

---

## 5. 阶段 D — 结果判读矩阵

| 观察结果 | 允许得出的结论 | 不允许得出的结论 |
|---|---|---|
| ABL 明确拒绝镜像 | 当前 ABL 拒绝本次 PREP10 RAM boot 请求 | 不代表 kernel 自身不能启动；不得绕过/重试 |
| fastboot `OKAY`，之后 ADB `device` | 本次镜像被接受，内核/启动链至少推进到 ADB 用户态可用阶段（K3 里程碑） | 不代表显示、触控、Wi-Fi、UFS 全部正常，也不代表完整 Android 可用 |
| fastboot `OKAY`，USB 重新枚举，无 ADB | 至少发生主机侧 USB 状态变化 | 不足以单独证明 kernel 成功或失败 |
| fastboot `OKAY`，5 分钟无 ADB | K3 ADB 信号未观察到 | 不等于 kernel 未运行、panic 或设备变砖 |
| USB 完全消失 | 主机侧设备断开/未重枚举 | 不能区分 kernel panic、DWC3/PHY/供电/角色切换失败、设备卡死或线缆/主机问题 |
| 命令挂起/主机无响应 | 当前观测结果不完整 | 不能推断 ABL 已接受或拒绝 |

本轮无 UART12 物理串口，无已确认 framebuffer/fbcon，USB early console 不存在。因此如果没有 ADB，只能得到“早期启动阶段不可观测/结果不确定”的结论。

---

## 6. 交付物与上传要求

完成后立即生成：

`K1_FIRST_BOOT01_REPORT.zip`

ZIP 至少包含：

1. `K1_FIRST_BOOT01_REPORT.md` — 中文总报告与明确最终判定；
2. `host_command_log.txt` — 命令、stdout/stderr、退出码、时间戳（serial 脱敏）；
3. `usb_adb_observation.csv` — USB/Fastboot/ADB 观察时间线；
4. `SHA256SUMS.txt` — 报告包内部文件 SHA-256。

总报告必须包含：

```text
CANDIDATE_IDENTITY
PREBOOT_GATE
FASTBOOT_DEVICE_COUNT
GETVAR_BASELINE
FASTBOOT_COMMAND
ABL_RAMBOOT
USB_REENUMERATION
ADB_STATE
ADB_TARGET_IDENTITY
KERNEL_EXECUTION_CONFIDENCE
K3_SUCCESS_SIGNAL
PERSISTENT_PARTITION_WRITE_COMMANDS_ISSUED = NO
RETRY_COUNT = 0
PHYSICAL_RECOVERY_PERFORMED = NO
FINAL_RESULT = ABL_REJECTED | K3_ADB_ONLINE | INCONCLUSIVE_NO_ADB | HOST_OR_DEVICE_HUNG | PREBOOT_STOP
```

需明确写明：没有发出任何 flash/erase/update/bootctl/adb shell 命令；若测试未能进入阶段 B，则 `RETRY_COUNT=0`，`FASTBOOT_BOOT_COMMAND_ISSUED=NO`；若已发出命令，则 `FASTBOOT_BOOT_COMMAND_ISSUED=YES` 且唯一尝试已消耗。

若项目 Git 工作目录和已配置的 GitHub 认证可用，优先将脱敏报告、日志摘要及 ZIP 上传至仓库：

`hhdy/matepad11-dby-w09-agent-reports`

建议目录：

`firmware-analysis/boot-v2/first-boot01/`

建议文件名：

- `K1_FIRST_BOOT01_REPORT.md`
- `K1_FIRST_BOOT01_REPORT.zip`

不得为了上传而安装新工具、改变系统策略或复制设备敏感数据。若 GitHub 不可用，直接交付本地 ZIP，并给出完整路径与 SHA-256。

---

## 7. 一次性任务停止条件

满足以下任一条件即结束：

- 候选或设备身份前置检查失败；
- ABL 拒绝；
- ADB `device` 首次出现；
- 观察达到 300 秒仍无 ADB；
- 设备/主机挂起或 USB 完全消失；
- 出现任何未授权操作提示。

**无论结果如何，本任务只执行一次。完成报告后立即停止，交 AI1 审核。不得自行安排 K1-FIRST-BOOT02，不得重复启动，不得刷写，不得自动恢复。**
