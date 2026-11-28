# K1-ABL-BOOTFAIL-ANALYSIS02 — AI1 独立审核报告

**审核日期：2026-11-28**  
**输入 ZIP：** `K1_ABL_BOOTFAIL_ANALYSIS02_REPORT.zip`  
**输入 ZIP SHA-256：** `ec7d899b9abe6b55e85ddbda7b2ca16883c44445f64008e887baf3f79b531fbe`  
**审核结论：PASS WITH MAJOR QUALIFICATIONS（核心保守结论正确，Host 层关键归因过度确定）**

## 1. 总结

本次报告最重要的最终结论正确且应保留：

```text
FIRST_BOOT01_RESULT          = RAMBOOT_NOT_CONFIRMED_USB_WRITE_TIMEOUT
BOOT_COMMAND_DELIVERY        = NOT_CONFIRMED
ABL_CMD_BOOT_HANDLER_ENTERED = NOT_CONFIRMED
ABL_IMAGE_AUTH_RESULT        = UNKNOWN
ABL_KERNEL_HANDOFF           = NOT_CONFIRMED
KERNEL_EXECUTION             = NOT_CONFIRMED
ROOT_CAUSE                   = UNRESOLVED
```

但报告另有一处关键推断写得过强：把 `AdbWriteEndpointSync` error 121 精确定位到 `"boot"` 四字节命令写入，并进一步解释为 ABL 在下载完成后已停止接受 USB bulk OUT。交付包没有提供足以验证这一调用点的反汇编证据；精确 37.0.3 源码也标为 `NOT_VERIFIED`。

因此：
- `ERROR_121_ORIGIN = HOST_USB_WRITE` 可保留；
- `BOOT_COMMAND_WRITE_PHASE = FAILED` 应降为 `LIKELY / INFERRED`，而非已确认；
- `"boot"` 是超时写入的确切 payload：`INFERRED / NOT_CONFIRMED`；
- “ABL 已进入内部 auth/verify，故 USB endpoint 不再接受写入”只能列为一种假设；
- `ABL_IMAGE_AUTH_RESULT`、`ABL_CMD_BOOT_HANDLER_ENTERED` 和 `KERNEL_EXECUTION` 继续保持 UNKNOWN / NOT_CONFIRMED。

## 2. ZIP 和内部完整性核验

| 检查 | 结果 |
|---|---|
| ZIP 文件大小 | 19,484 B |
| ZIP SHA-256 | 与提交值完全一致 |
| ZIP CRC / testzip | PASS |
| ZIP 成员数 | 10 |
| `SHA256SUMS.txt` | 9 个交付文件全部匹配 |
| 缺失/损坏 ZIP 成员 | 未发现 |

内部 SHA-256 清单逐项匹配：主报告、Host calltrace、Windows USB event review、Hybrid ABL 分析、Hybrid/stock 对比、evidence matrix、source manifest、两个脚本均通过。

### 2.1 阶段 A 输入身份

报告主表和 `identity_check.py` 对 10 个分析输入执行了 SHA-256 核验；`source_identity_manifest.md` 另列出 fastboot.exe、AdbWinApi.dll、AdbWinUsbApi.dll 三个 Host 工具文件身份，合计 13 项。这并非冲突，但建议明确区分“10 个分析输入”和“3 个 Host 工具身份”。

**尺寸勘误：**报告将 R155 ABL dump 实测大小记为 4,194,304 B，并指出任务书旧值 4,796,416 B 是誊写错误。此修正与本轮清单一致，应采用 4,194,304 B；不得继续使用旧尺寸。

限制：原始 ABL/PE/boot 等二进制未包含在本次报告 ZIP 中，因此 AI1 本次能够核验交付包和内部清单，但不能从 ZIP 单独重算那些输入二进制的哈希。输入身份 PASS 是执行方本机复核结果，不是本次对每个原始二进制再次实算的结果。

## 3. Host Fastboot 分析：已确认与未确认的边界

### 3.1 已确认内容

1. 原始 stderr 明确出现 `AdbWriteEndpointSync failed` 与错误 121。
2. 执行方记录 fastboot.exe 版本为 `37.0.3-16887417`，并提供 exe、AdbWinApi.dll 和 AdbWinUsbApi.dll 的路径、大小及哈希。
3. 下载阶段显示 `Sending ... OKAY`；这确认主机 Fastboot 报告 download 事务完成，但不等于本次 AI1 重新读取了设备 RAM。
4. 没有观察到设备返回的 `FAIL` 文本；正确字段是 `REMOTE_FASTBOOT_FAIL_PACKET = NOT_OBSERVED`，不能升级为“协议层确认未发生 FAIL”。

### 3.2 主要缺陷：调用点没有被真正证明

交付的 `scripts/host_trace.py` 实际做的是：
- 在 fastboot.exe 原始字节中搜索 `AdbWriteEndpointSync`、`Booting`、`usb_write` 等字符串；
- 查找 PE 头，输出 import directory RVA 和 section 信息；
- 在整个文件中搜索 `AdbWinApi.dll` 等 DLL 名称。

它没有：
- 解析 Import Directory 的 descriptor/thunk/IAT 并建立函数导入关系；
- 从导入 thunk 追踪真实 call xrefs；
- 反汇编 `usb_write` wrapper；
- 识别调用 `AdbWriteEndpointSync` 时传入的 buffer 指针、长度和 timeout 参数；
- 证明 `Booting` 字符串引用与该写调用在相同控制流中的先后关系。

所以报告中的 `0x2029cc`、`0x24f938` 目前只能按字符串命中偏移处理，不能仅凭该脚本称为两个真实调用点。`usb_write` 字符串偏移也不能自动等同于函数入口或调用位置。

报告明确承认 `EXACT_37_0_3_SOURCE = NOT_VERIFIED`，所以以 AOSP master/近似源码推出 `fb_command("boot")` 的 payload，是合理假设，但不是对本机 37.0.3 二进制的精确证明。

**AI1 修正状态：**

```text
FASTBOOT_EXE_IDENTITY          = PASS (executor-reported; package does not contain exe)
FASTBOOT_VERSION               = 37.0.3-16887417 (executor-reported)
EXACT_37_0_3_SOURCE            = NOT_VERIFIED
ADBWINAPI_ERROR_TEXT           = CONFIRMED
ADBWRITE_IMPORT_OR_CALLSITE    = PARTIAL (provided script does not parse IAT/call xrefs)
ERROR_121_ORIGIN               = HOST_ADBWINAPI_ENDPOINT_WRITE_FAILURE
EXACT_FAILED_WRITE_PAYLOAD     = UNKNOWN / INFERRED_AS_BOOT_COMMAND
BOOT_COMMAND_DELIVERY          = NOT_CONFIRMED
REMOTE_FASTBOOT_FAIL_PACKET    = NOT_OBSERVED
```

### 3.3 “约 5.5 秒 = WinUSB 默认约 5 秒”不能作为证据

AOSP `AdbWriteEndpointSync` API 声明包含显式 `bytes_to_write` 和 `time_out` 参数；timeout 是调用方传入的毫秒数，0 表示不设 timeout。官方头文件说明见：

https://android.googlesource.com/platform/development/+/refs/heads/main/host/windows/usb/api/adb_api.h

因此，5,525 ms 的 Booting 阶段可能与约 5 秒的调用 timeout 相符，但不能称为“WinUSB 默认 5 秒”，也不能仅凭时间长度证明该次失败 API 调用的 payload 是 `"boot"`。必须从精确调用点反汇编出实际 timeout 参数，或提供可信 runtime trace。当前包没有此证据。

Windows 121 的系统定义为 `ERROR_SEM_TIMEOUT`；它说明等待超时，不包含 ABL 镜像认证失败的语义。Microsoft 定义见：

https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-

还应避免直接把 ADBWinApi endpoint API 称为 WinUSB 默认行为。当前证据支持“Windows ADB USB endpoint API 写操作失败”，并不支持特定 WinUSB driver 的默认 timeout 断言。

### 3.4 “ABL 已停止接受 USB bulk OUT”属于假设

报告中“ABL 收到完整 download 后，在处理该数据期间不再接受 USB bulk OUT 写入”这一表述超出证据。

Host API 写超时不能区分：
- 设备端 endpoint/USB 状态；
- Windows ADB USB API / driver / host controller；
- 主机端写操作 timeout 参数和取消行为；
- 设备在 boot 命令阶段进入重置/切换/错误状态。

该段应改成 `POSSIBLE_DEVICE_SIDE_USB_NON_RESPONSE`，并明确只是若干可能原因之一。没有历史 PnP 数据也不能支持“USB 没断开”。

## 4. Hybrid ABL 分析：结论保守，证据包可复现性不足

可保留的分析状态：
- Hybrid PE 身份与提取链：执行方报告 PASS；
- Fastboot 后缀表结构：CONFIRMED（但完整命令到 handler 映射未完成）；
- 0x41824 函数域：PARTIAL，不是已确认函数入口；
- libavb 字符串/断言存在：CONFIRMED；
- `read_is_device_unlocked` 的真实 callback implementation：未定位；
- `Failed to load/authenticate boot image: %r`：Hybrid 有、stock 无，这是构建级字符串差异；不能证明本次调用该失败路径；
- CmdBoot handler registration、完整 auth call、response 分支、USB teardown、ExitBootServices 和 kernel branch：仍然 PARTIAL / UNKNOWN。

### 4.1 可复现材料缺项

`hybrid_abl_cmd_boot_analysis.md` 提到 `dataflow_xref.py`，但 ZIP 的 `scripts/` 只包含 `host_trace.py` 和 `identity_check.py`。没有附：
- 修复后的 `dataflow_xref.py`；
- CmdBoot 候选地址 0x41824 周边的最小汇编摘录；
- 对 0xcc668 指针表/0x2e2e0 分派区域的 CFG；
- 可以核验 stale-ADRP 修复及三个假命中撤销的最小输入/输出摘要。

因此 AI1 接受执行方把 CmdBoot 标为 PARTIAL/UNKNOWN 的谨慎结论，但不能将缺少底层摘录的静态发现升级为 AI1 已独立复现的事实。

### 4.2 Hybrid/stock 等价字段应缩窄

`HYBRID_STOCK_CMD_BOOT_EQUIVALENCE = NO` 如果含义是“不是同一编译产物/字节不同”，成立。若含义是“CmdBoot 语义一定不同”，当前材料不足以证明。建议拆分：

```text
HYBRID_STOCK_BUILD_ARTIFACTS_EQUAL = NO
HYBRID_STOCK_CMD_BOOT_SEMANTIC_EQUIVALENCE = UNKNOWN
```

两份 PE 的 build fingerprint、尺寸和哈希不同，只证明独立构建产物不同；不能单凭字符串差异证明实际认证行为不同。

## 5. Evidence matrix 数据质量

`evidence_matrix.csv` 的内部 SHA-256 正确，但 CSV 结构有两行未正确转义逗号，导致总共 23 行数据中两行解析为 8 列，其余解析为 6 列：

1. “ABL 不含 'Failed to load/authenticate' 的 RAM boot 路径”这一行表述错误：报告已确认该字符串在 Hybrid=1、stock=0。应改成“Hybrid PE 含该错误字符串、stock PE 不含（构建级差异）”。
2. “后缀表 `{suffix_ptr,handler_ptr}`”中的逗号未引用，破坏 CSV 列结构；应将该字段按 RFC 4180 规则双引号包裹。

建议修复后重算 `SHA256SUMS.txt`，但不需要为了这两处格式错误重复 ABL 反汇编。

## 6. 修正后的总状态

```text
ZIP_SHA256_AND_CRC                 = PASS
INTERNAL_SHA256SUMS                = PASS
STAGE_A_INPUT_IDENTITY             = PASS (executor-reported; originals not in this ZIP)
FASTBOOT_EXE_IDENTITY              = PASS (executor-reported)
EXACT_37_0_3_SOURCE                = NOT_VERIFIED
ADBWINAPI_ENDPOINT_WRITE_ERROR     = CONFIRMED
EXACT_FAILED_WRITE_PAYLOAD         = UNKNOWN / LIKELY_BOOT_COMMAND
BOOT_COMMAND_DELIVERY              = NOT_CONFIRMED
WINDOWS_USB_PNP_HISTORY            = NO_HISTORICAL_EVENT_DATA
HYBRID_ABL_IDENTITY                = PASS (executor-reported)
FASTBOOT_COMMAND_TABLE             = PARTIAL
CMD_BOOT_HANDLER                   = PARTIAL
CMD_BOOT_AUTH_CALL                 = UNKNOWN
UNLOCKED_RAMBOOT_AUTH_BYPASS       = UNKNOWN
BOOT_ERROR_RESPONSE_PATH           = PARTIAL
USB_TEARDOWN_OR_RESET_PATH         = UNKNOWN
KERNEL_HANDOFF_PATH                = UNKNOWN
ABL_IMAGE_AUTH_RESULT              = UNKNOWN
KERNEL_EXECUTION                   = NOT_CONFIRMED
ROOT_CAUSE                         = UNRESOLVED
FINAL_RESULT                       = RAMBOOT_NOT_CONFIRMED_USB_WRITE_TIMEOUT
```

## 7. 下一步建议与停止边界

本次静态分析已经完成了它能完成的收口。不要再安排无边界的 ABL 字符串扫描或重复静态审计，也不要因为 `"boot"` 命令写入是“最可能”而把它当成设备端拒绝证据。

**不建议直接转向 `fastboot flash boot`。** 本次失败没有证明 PREP10 的认证失败，也没有证明 flash 路径会接受同一镜像。RAM boot 与 flash 的 ABL 路径尚未闭合，当前 live vbmeta 状态未知。任何 flash 都是持久分区写入，必须独立制定回滚与恢复方案并另行授权。

当前可锁定的结论是：download 流程在主机日志中得到 OKAY；随后 Booting 阶段发生 Windows ADB USB endpoint 写超时；设备端是否收到完整 boot 命令及之后执行到哪里均未知。若未来要再次进行设备实验，必须先形成独立的新任务与新授权，不能复用本轮“一次尝试”的授权。

**审核最终结果：PASS WITH MAJOR QUALIFICATIONS。** 报告核心最终结论合格；需收窄 Host 写入 payload/ABL USB 行为断言，修正 evidence_matrix 两行 CSV，保留所有设备端执行与认证状态为 UNKNOWN。
