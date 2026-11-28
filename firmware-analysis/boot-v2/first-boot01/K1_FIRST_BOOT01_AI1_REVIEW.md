# K1-FIRST-BOOT01 — AI1 独立审核

**审核日期：2026-11-28**  
**输入：用户上传 `K1_FIRST_BOOT01_REPORT.zip`**  
**ZIP SHA-256：`3806ad0305f164e0c0daf785c53140afb843004f72372be45ea38b01c6a96880`**

## 1. 总判定

**实机尝试失败；ABL 明确拒绝尚未得到证明。**

建议将原报告的最终分类从 `ABL_REJECTED` 更正为：

```text
CANDIDATE_IDENTITY          = PASS (based on executor log)
PREBOOT_GATE                = GO (based on executor log)
DOWNLOAD_STAGE              = OKAY
BOOT_COMMAND_STAGE          = HOST_USB_TRANSPORT_ERROR
REMOTE_FASTBOOT_FAIL_PACKET = NOT_OBSERVED
ABL_RAMBOOT                 = UNKNOWN / NOT_CONFIRMED
POST_TEST_FASTBOOT_VISIBLE  = YES (one enumeration 31s later)
USB_REENUMERATION           = NOT_OBSERVED; continuous USB event trace absent
ADB_STATE                   = NOT_OBSERVED
KERNEL_EXECUTION            = NOT_CONFIRMED
K3_SUCCESS_SIGNAL           = NOT_OBSERVED
RETRY_COUNT                 = 0 (as reported)
FLASH_ERASE_UPDATE_COMMANDS = NOT_REPORTED
FINAL_RESULT                = RAMBOOT_NOT_CONFIRMED_USB_WRITE_TIMEOUT
```

这并不表示 RAM boot 成功。它表示当前原始证据不足以把失败归因于 ABL 的镜像认证拒绝。

## 2. 已核验的事实

- 上传 ZIP 实际 SHA-256 与交付消息中的 ZIP SHA-256 一致。
- ZIP CRC 检查通过，六个成员均可读取。
- 候选文件在 `host_command_log.txt` 中记录为 46,563,215 bytes，SHA-256 `d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091`，与冻结值一致；这是执行方日志记录，上传包没有包含候选原件供本次复算。
- 日志记录一台 Fastboot 设备，getvar 值与历史基线一致：`kona / unlocked=yes / secure=yes / is-userspace=no / partition-size:boot=0x6000000`。
- `boot_stderr.txt` 原文为：

```text
Sending 'boot.img' (45471 KB)                      OKAY [  1.091s]
Booting                                            FAILED (AdbWriteEndpointSync failed: 信号灯超时时间已到 (121))
fastboot: error: Command failed
```

- 日志记录在命令返回约 31 秒后，`fastboot devices -l` 仍枚举到设备；`adb devices -l` 为空。
- 没有证据显示执行了第二次 `fastboot boot` 或持久分区写入命令；按执行日志，本轮唯一启动命令已发出且无重试。

## 3. 关键技术纠正：`Booting FAILED` 不是远端 ABL `FAIL`

Fastboot 协议将远端设备返回的 `FAIL` 定义为响应数据包的前四字节，并规定其后可带设备侧失败原因；这与主机 USB 传输函数报错是不同层级。见 AOSP Fastboot protocol 文档：

- https://android.googlesource.com/platform/system/core/%2B/a057057/fastboot/fastboot_protocol.txt

日志中的具体错误是 `AdbWriteEndpointSync failed`。AOSP Windows Fastboot USB transport 中，`WindowsUsbTransport::Write()` 通过 `AdbWriteEndpointSync()` 写 bulk OUT endpoint，使用 5000 ms timeout；该 API 失败时，主机写函数返回错误，而不是解析到设备发回的 `FAIL` 响应包。见：

- https://chromium.googlesource.com/aosp/platform/system/core/%2B/master/fastboot/usb_windows.cpp

因此，本次输出至少能证明：

1. 镜像 download 阶段完成，并收到设备 `OKAY`；
2. 到 `boot` 命令阶段，Windows Fastboot USB 写端点调用报超时；
3. 日志没有记录到设备发回 `FAIL<reason>` 这样的明确拒绝帧；
4. 无法仅凭这条主机传输错误确定 `boot` 命令是否完整抵达 ABL、ABL 是否已经开始验签，或 ABL 是否已经执行了部分启动处理。

Windows 错误 121 的系统名称是 `ERROR_SEM_TIMEOUT`，描述为 semaphore timeout period has expired。该错误码本身不包含 ABL 验签失败或 boot image 格式错误的语义。见 Microsoft：

- https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-

## 4. “设备仍在 Fastboot”能证明什么

`host_command_log.txt` 只记录命令返回后约 31 秒的一次 `fastboot devices -l` 枚举；没有 Windows PnP 事件、USB descriptor/interface 时间线、连续轮询结果或再次成功的 `getvar` 响应。

因此可以写：

- `POST_TEST_FASTBOOT_VISIBLE = YES`：该时刻主机仍能枚举 Fastboot 接口。
- `ADB_NOT_OBSERVED = YES`：该时刻 ADB 列表为空。

但不能据此证明：

- 整个 31 秒期间 USB 从未断开/重新枚举；
- 设备始终连续处于同一个 bootloader 会话；
- kernel 绝对从未执行过。

没有启动 handoff、UART、K1 log 或 USB event tracing，`KERNEL_EXECUTION` 应写 `NOT_CONFIRMED`，而不是 `NO (certainty)`。

## 5. 交付完整性问题

ZIP 容器 CRC 通过，但 `SHA256SUMS.txt` 中有一条不匹配：

| 文件 | 清单 SHA-256 | ZIP 内实际 SHA-256 | 结果 |
|---|---|---|---|
| `host_command_log.txt` | `d68492ff2712d3277c5b4226061e6587103ee22eaa788c531b449f2b2e945911` | `5debbdde8211864c75aca605a2d24d559b15e01030bef3bc1a1326288c770b9a` | **MISMATCH** |

其余五个文件的 SHA-256 与清单一致。另：`host_command_log.txt` 中 Windows 中文错误文本存在乱码；独立 `boot_stderr.txt` 保留了可读原文。应以 `boot_stderr.txt` 为原始报错证据，并在修订包中修正 checksum 与文本编码。

## 6. 审核后的最终结论

本次实机尝试没有成功完成可确认的 RAM boot。下载阶段明确成功，随后在 `boot` 控制命令的 Windows USB bulk write 阶段出现 error 121。设备在后续一次枚举中仍显示 Fastboot，ADB 未出现。

**最严格、与现有证据相匹配的结论是：`RAMBOOT_NOT_CONFIRMED_USB_WRITE_TIMEOUT`。**

不能写成已证实的“ABL 验签拒绝”或“kernel 从未启动”。可能原因至少包括：ABL 处理 boot 请求时 USB/bootloader 端点停止响应、设备端开始切换或复位导致写端点超时、主机 Windows USB 驱动/接口异常；现有数据不能区分这些路径。

## 7. 下一步边界

- 本轮唯一一次 RAM boot 尝试已经消耗；**不得再次运行 `fastboot boot`**。
- 不因这次失败直接决定 `fastboot flash boot`。刷写属于持久分区写操作，需要独立方案、回滚路径、镜像身份复核和用户单独授权。
- 不执行 `fastboot reboot`、刷写、擦除、解锁/锁定、EDL、TWRP 或任何恢复操作，除非用户另行明确授权。
- 当前优先工作应转为主机侧离线诊断：核实 Agent 使用的 fastboot 37.0.3 二进制对应的 USB transport 实现；结合精确 ABL PE 分析 boot 命令 handler/认证分支；审查当前日志中缺少的 USB/PnP 事件证据。离线分析不能替代第二次启动，也不得暗中触发设备操作。

**审核状态：报告主体事实基本成立；`ABL_REJECTED`、`KERNEL_EXECUTION=NO` 属于证据超范围结论，必须更正。ZIP 内部 checksum 有一项不匹配。**