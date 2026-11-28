# FASTBOOT_BOOT_ATTEMPT01 — 执行结果（§7.2 唯一一次已授权非持久探测）

- 日期：2026-11-29（§7 授权的单次尝试，本次已消耗）
- 候选：`rcand-tmp/recovery-uboot-candidate.img`，27,926,528 B，SHA `b48e9185…811990`（与 BUILD01 冻结值一致 ✓）
- 设备：`W3VBB21724204537` fastboot 模式（自 FIRST-BOOT01 起停留）

## 完整终端输出

```
D:\Tools\platform-tools\fastboot.exe getvar product
getvar:product   FAILED (AdbWriteEndpointSync failed: 信号灯超时时间已到 (121))
Finished. Total time: 5.008s
D:\Tools\platform-tools\fastboot.exe getvar unlocked
getvar:unlocked   FAILED (AdbWriteEndpointSync failed: 信号灯超时时间已到 (121))
Finished. Total time: 5.008s
D:\Tools\platform-tools\fastboot.exe boot recovery-uboot-candidate.img
Sending 'boot.img' (27272 KB)   FAILED (AdbWriteEndpointSync failed: 信号灯超时时间已到 (121))
fastboot: error: Command failed
```

## 结果分类

- **主机侧 USB 写超时（WinUSB error 121）**，非 ABL 拒绝报文：连 `getvar product/unlocked` 都无法送达 → 设备 fastboot 端点当前**不接受任何 USB bulk 写**。
- 下载阶段即失败（`Sending 'boot.img'` 未完成）→ **`boot` 命令从未发出** → ABL 从未收到候选，未进入接受/拒绝判定。
- 与 FIRST-BOOT01 对比：FIRST-BOOT01 是下载 OKAY(1.091s) 后 `boot` 命令写超时；本次连 27,272 KB 下载都写不进去——设备 fastboot USB 栈自 FIRST-BOOT01 后处于更深的无响应态（长时间停留 fastboot 的可能性大）。

## 后状态（仅枚举）

`fastboot devices`：仍在 fastboot（未重启、未变砖）；`adb devices`：无。设备保持原状。

## 判定

- **FASTBOOT_BOOT_ATTEMPT01 = FAIL（USB_WRITE_TIMEOUT_HOST_SIDE）**
- **NOT evidence of ABL rejection**——不能据此判定 ABL 是否接受/拒绝候选。
- 单次授权已消耗，不重试（对无响应端点重试无意义；需用户物理干预让设备退出当前 wedged fastboot 态——例如长按电源重启回系统再重新进 fastboot，或重启回 HOS——之后如需再次探测需重新授权）。

## 对整体路线的影响

ZERO new information about ABL/AVB acceptance（命令未达设备）。Gate01 的 HOLD 维持不变：ABL unlocked acceptance 仍 UNKNOWN、tail semantics 仍 UNKNOWN。下一步（需用户操作）：先把设备从 wedged fastboot 带回可用状态（长按电源 ≥10s 或 重启回 HOS），确认 ADB 可用后，再评估是否重新授权一次新的探测。

**声明：仅执行了 devices/getvar/boot（一次）；无 flash、无 erase、无分区写入、无 vbmeta 操作、无重启命令。**
