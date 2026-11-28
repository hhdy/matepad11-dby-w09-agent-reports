# K1-USB-OBSERVABILITY-CHECK01 — AI1 独立审核

审核日期：2026-11-28  
审核对象：`K1_USB_OBSERVABILITY_CHECK01_REPORT.zip`  
结论：**PASS WITH QUALIFICATIONS**  
设备操作：未执行；本审核不构成 `fastboot boot` 授权。

## 1. 交付完整性

- ZIP：15,235 B；SHA-256 `e8cb1a0210fb6f092f11b8c8e5c274854f9d2f60347e7cd80806cf3301abc54c`，与提交值一致。
- ZIP CRC 通过；SHA256SUMS 中列出的 8 个文件逐一重算匹配。
- ZIP 共 9 个条目（含 SHA256SUMS）。
- **缺项：**报告第 7 节列出 `host_tools_versions.txt`，但压缩包没有该文件，SHA256SUMS 也没有对应记录。属于交付清单缺项，不影响 USB 主结论。

## 2. 确认通过的部分

实际 build config 中 `CONFIG_USB_GADGET=y`、`CONFIG_USB_DWC3=y`、`CONFIG_USB_DWC3_QCOM=y`、`CONFIG_USB_DWC3_DUAL_ROLE=y`、`CONFIG_USB_ROLE_SWITCH=y`、`CONFIG_USB_CONFIGFS=y`、`CONFIG_USB_CONFIGFS_F_FS=y`、`CONFIG_USB_F_FS=y`、`CONFIG_USB_CONFIGFS_ACM=y`、`CONFIG_USB_F_ACM=y`。据此可确认相关驱动/function 已编译进内核。

`CONFIG_USB_FUNCTIONFS=n` 不否定 ConfigFS FunctionFS 路径：本构建启用的是 `USB_CONFIGFS_F_FS` / `USB_F_FS`。Linux Kconfig 将前者定义为 ConfigFS FunctionFS function，并选择后者；DWC3 的 `DUAL_ROLE` 是 host/gadget 双角色模式。参考：[Linux gadget Kconfig](https://github.com/torvalds/linux/blob/master/drivers/usb/gadget/Kconfig)、[Linux DWC3 Kconfig](https://github.com/torvalds/linux/blob/master/drivers/usb/dwc3/Kconfig)。

ramdisk 清单支持：embedded ramdisk 没有 init/adbd/USB gadget rc；separate ramdisk 含 init stub 与 init.real，但没有列出 adbd 或 USB gadget rc。结合既有 PREP04 字节级 handoff 证据，实际 initrd 为 separate ramdisk 的结论可接受。

## 3. 必须收窄的表述

1. `ADBD_BINARY_AND_INIT_PATH=ABSENT` 过强。本轮只证明 **ramdisk 内不存在 adbd/USB init 配置**；没有检查 system/vendor 分区中的 `/system/bin/adbd`、vendor init rc、USB 属性触发器或实际 FunctionFS composition。应改为：
   `ADBD_BINARY_AND_INIT_PATH=UNKNOWN (ABSENT_IN_RAMDISK)`。
   `ADB_REACHABLE_AFTER_INIT=POSSIBLE` 可保留，但须以 first-stage mount、second-stage init、system/vendor 配置及 UDC 正常为条件。

2. `init.real` 关键字未命中是负面字符串证据，不等于对二进制控制流的穷尽证明。

3. `CONFIG_USB_EARLY_CONSOLE` 在 build config 中 not found，说明本构建没有该配置项记录。压缩包未包含对冻结源码树的 grep 结果，因此“源码无此驱动”的绝对说法没有在本包中独立证明。操作性结论仍是未发现可用于 K1 的 USB early-console 路径。

4. USB 断开/重连本身不能证明 kernel 已运行到 DWC3 probe；可能只是 ABL 交接时的 USB reset。只有识别到新的 Linux gadget/ADB/ACM 设备描述符，才可作为正向枚举证据；单纯枚举仍不等价于 K3。

5. “USB 栈全部 built-in”不准确，因为 `CONFIG_USB_SERIAL=m`。应限定为本轮关键 FunctionFS/ConfigFS/ACM 配置为 built-in。驱动编译存在也不保证目标 DTB、PHY、时钟、供电、role-switch 与 UDC runtime probe 成功。

## 4. AI1 修正后的状态

```
PREP10_IDENTITY                  = PASS
BUILD_CONFIG_IDENTITY            = PASS
USB_UDC_DRIVER                   = CONFIRMED (compiled; runtime probe unknown)
USB_GADGET_FRAMEWORK             = CONFIRMED (compiled)
USB_FUNCTIONFS_ADB_CONFIG        = CONFIRMED (kernel function compiled; userspace composition unknown)
ADBD_BINARY_AND_INIT_PATH        = UNKNOWN (absent from ramdisk; system/vendor not audited)
USB_CDC_ACM_GADGET               = CONFIRMED (function compiled; runtime activation unknown)
USB_EARLY_CONSOLE                = ABSENT (no usable K1 path identified)
ADB_REACHABLE_AFTER_INIT         = POSSIBLE (conditional)
RAMDISK_HANDOFF                  = CONFIRMED (PREP04 prior byte-level evidence)
K1_EARLY_OBSERVABILITY           = INADEQUATE
K3_USB_ADB_SUCCESS_SIGNAL        = AVAILABLE (conditional, not guaranteed)
```

## 5. 对下一步的影响

本轮目标已达到：现有内核含 FunctionFS/ConfigFS gadget 所需的关键编译配置；如果启动经过 K2 并运行到合适的 second-stage USB init，ADB 有机会成为 K3 成功信号。K1 仍不可观测。

**建议停止追加离线 USB 可观测性审计，转入单次受控 K1-FIRST-BOOT01 决策阶段。**但必须等待用户明确授权一次 `fastboot boot`；本审核未执行设备命令、未切换模式、未重启、未刷写，也未授权 Agent 操作设备。

首次尝试解释规则：ABL 明确拒绝则停止；出现可识别 Linux gadget/ADB 则按对应阶段记里程碑；无 ADB 或 USB 消失一律记为 INCONCLUSIVE，不得据此断言 kernel 未启动/panic，也不得自动循环重试。

**最终：PASS WITH QUALIFICATIONS。** 核心发现可靠；需修正 ADB 全系统路径状态、USB 重枚举推断强度、USB early-console 的源码绝对措辞，以及交付清单缺失项。
