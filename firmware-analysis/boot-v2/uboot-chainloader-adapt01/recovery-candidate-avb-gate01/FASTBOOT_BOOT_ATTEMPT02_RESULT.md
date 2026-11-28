# FASTBOOT_BOOT_ATTEMPT02 — 决定性结果（硬件按键进入路径，2026-11-29）

## 完整终端输出

```
fastboot getvar product  → product: kona                    (0.003s ✓)
fastboot getvar unlocked → unlocked: yes                    (0.001s ✓ unlocked 确认)
fastboot boot recovery-uboot-candidate.img
  Sending 'boot.img' (27272 KB)   OKAY [  0.639s]           ← 27.9MB 完整下载成功
  Booting                          FAILED (remote: 'Failed to load/authenticate boot image: Load Error')
fastboot: error: Command failed
```

## 判定

**ABL 在 UNLOCKED 态明确拒绝候选，并返回了真实 remote 错误串**：
`Failed to load/authenticate boot image: Load Error`

该串与 AUTH/CLOSE01 轮在 Hybrid 工程 ABL 中定位到的 `Failed to load/authenticate boot image: %r`（VA 0xCBC34，hybrid=1 独有字符串）精确对应——**这是整个项目首次获得的 ABL 接受/拒绝实机证据**。

## 由此确立的事实

1. **USB 写问题根因 = 进入路径**：`adb reboot bootloader` 进入的 fastboot 不响应标准协议写（getvar 全超时）；**硬件按键进入则完全正常**（getvar 0.003s、下载 0.639s）。该路径依赖为可复现环境事实，后续所有 fastboot 操作必须硬件按键进入。
2. **ABL 下载通道正常**：27.9MB 0.639s 送达——download→authenticate 管道工作。
3. **ABL Unlock 态并不放行未签名/完整替换 Kernel 的 Recovery 镜像**：`LoadImageAndAuth` 对候选执行了 load/authenticate 并失败。结合 AVB Gate01（candidate 缺分区级 footer/child vbmeta，签名链 FAIL）——**拒绝原因与 Gate01 预测一致：signed chain 不满足**。至于是签名失败还是结构装载失败（'Load Error' vs 独立 verify error），本轮 remote 串未细分，静态上属于 LoadImageAndAuth 的通用错误汇点。
4. **RECOVERY_CANDIDATE_DEVICE_READY = HOLD 维持且原因已从 UNKNOWN 变为已证实**：候选按当前形态（无分区级 footer/child vbmeta、无 OEM 签名）**不会被 ABL 接受**。解除 HOLD 需要签名的 recovery 容器（OEM key 不在手，AUTH_BLOCKED）或证明 unlocked 跳过路径（已被本次实验否定——unlocked 态依然走了 authenticate 并失败）。

## 设备后状态

`fastboot devices`：仍在 fastboot（boot 失败后 ABL 返回 fastboot 界面，未重启）；无任何分区被写入；TWRP/系统未受影响。

## 旧问题同步修正

- FIRST-BOOT01 的『download OKAY 后 boot 写超时』在此路径下未复现——那次的失败模式与 USB 进入路径相关（PREP10 探测当时也是经 adb reboot bootloader 进入的 wedged 态）。
- **Abl unlocked 态校验行为从 UNKNOWN 升级为已测 FAIL**：`ABL_UNLOCKED_RECOVERY_ACCEPTANCE = FAIL`（对本候选形态）。

## 对路线的最终含义

U-Boot Recovery 链式路线在**当前 ABL 上不可行**，除非：
- 获得 OEM 签名（不可得），或
- 证实/构造 ABL 会接受的其他 recovery 形态（例如 TWRP 的 ramdisk-only swap 形态——已证明可运行，但那保留 HOS kernel，无法承载 U-Boot），或
- 改用其他启动入口（reserved3 FIT 直读等）——需重新评估入口可行性。

**下一步建议交 AI1**：基于『unlocked 态 ABL 拒绝完整 kernel 替换 recovery（Load Error）』这一决定性事实，重新评估 U-Boot chainloader 路线是否继续；或转向 ①ramdisk-only 形态研究（kernel 无法替换，路线价值有限）②EDL/9xx 通道（GhostLock 工具链已有）③其他启动入口。

## MILESTONE 1 ACHIEVED — U-Boot 2026.10 实机运行（2026-11-29 补）

`adb reboot recovery` 后设备重启，USB 枚举变为 PID_4EE0 "Android Sooner Single ADB Interface" + fastboot 序列号 `?`；`getvar all` 回显 **version-bootloader: U-Boot 2026.10**、downloadsize=0x07000000（112 MiB）。用户屏幕显示 `dwc3-generic-peripheral usb@a600000` 日志 + fastboot 活动记录（usb@a600000 = SM8250 DWC3，与 ACK cmdline 的 usbcontroller 参数同控制器）。

**确认事实**：
- ABL → recovery 候选加载 → U-Boot kernel 运行 → DRAM 初始化 → USB fastboot 上线：**全链路实机打通**
- U-Boot fastboot 协议响应正常（getvar product=qrd / version=0.4 / all）
- CoWave env（0005 patch）已生效：`preboot=scsi scan`（UFS 自动扫描）；bootmenu：`Boot Linux from reserved3`（scsi read FIT→0x98000000→bootm）/ `Boot HarmonyOS`（bcb）/ `Enable fastboot mode` / `Reset`
- `oem help` → not recognized（U-Boot 无 oem 处理器，无碍）；`ep1in-bulk not queued` 为 gadget 噪声

当前设备处于 U-Boot fastboot 模式（bootmenu_2）。下一里程碑需用户授权：写 FIT v2（20,484,879 B）到 reserved3，随后经 U-Boot 菜单 `Boot Linux from reserved3` → bootm ACK。
