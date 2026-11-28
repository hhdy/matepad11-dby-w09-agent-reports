# K1-ABL-BOOTFAIL-ANALYSIS02 — PREP10 Fastboot Boot 传输超时 / Hybrid ABL 启动路径离线分析

**签发：AI1（ChatGPT）**  
**执行：WorkBuddy Agent（Windows 主机离线分析）**  
**项目：Huawei MatePad 11 DBY-W09 / HWDBY / SM8250(Kona)**  
**任务性质：只读离线主机取证 + AArch64 ABL PE 静态分析。**  
**授权边界：不连接设备，不执行设备 Fastboot/ADB 命令，不重启、不刷写。**

## 0. 目标与当前事实

K1-FIRST-BOOT01 唯一一次 fastboot boot 的原始 stderr：

    Sending 'boot.img' (45471 KB)  OKAY [ 1.091s]
    Booting  FAILED (AdbWriteEndpointSync failed: 信号灯超时时间已到 (121))
    fastboot: error: Command failed

上传日志记载 18:35:41.149 发出命令，18:35:42.240 下载阶段 OKAY，18:35:47.840 Booting 阶段失败；18:36:18 一次 fastboot devices 枚举仍可见 fastboot，adb devices 为空。命令总耗时 6,616 ms。

AI1 已审核并纠正结论：
- Booting FAILED 不能直接等同设备返回 Fastboot FAIL 数据包。
- AdbWriteEndpointSync failed 是主机 Windows USB transport 写端点调用报错；不能仅凭错误文本证明 ABL 已完整收到 boot 命令或拒绝了镜像。
- 严格结论为 RAMBOOT_NOT_CONFIRMED_USB_WRITE_TIMEOUT。ABL_RAMBOOT 与 KERNEL_EXECUTION 均应保持 UNKNOWN / NOT_CONFIRMED。
- 唯一一次 RAM boot 已消耗，绝对禁止重试。

本任务回答：
1. AdbWriteEndpointSync 对应 fastboot boot 事务中的哪次 USB 写操作？
2. 实际 fastboot 37.0.3-16887417 的 Booting 标签、命令发送、响应读取和错误传播顺序是什么？
3. Hybrid ABL 的 Fastboot boot handler、认证、装载、USB response/teardown 和 kernel handoff 路径，哪些可由准确二进制静态确认？
4. 本次失败能定位到哪一层，哪些仍然未知？

## 1. 冻结输入与哈希

### 1.1 实机报告 ZIP
- 文件：K1_FIRST_BOOT01_REPORT.zip
- SHA-256：3806ad0305f164e0c0daf785c53140afb843004f72372be45ea38b01c6a96880
- Windows 原路径：C:\Users\Administrator\Desktop\K1_FIRST_BOOT01_REPORT.zip
- 内含报告、host_command_log.txt、usb_adb_observation.csv、boot_stdout.txt、boot_stderr.txt、SHA256SUMS.txt。
- boot_stderr.txt 是可读原始错误。host_command_log.txt 中文编码存在乱码。
- ZIP CRC 通过，但 SHA256SUMS 中 host_command_log.txt 不匹配：清单 d68492ff2712d3277c5b4226061e6587103ee22eaa788c531b449f2b2e945911；内含文件实际 SHA 5debbdde8211864c75aca605a2d24d559b15e01030bef3bc1a1326288c770b9a。其余五项匹配。

### 1.2 Host / Fastboot 基线（需核对本机 exe）
- 执行方先前记录版本：37.0.3-16887417。
- 设备 getvar 记录：product=kona、unlocked=yes、secure=yes、is-userspace=no、partition-size:boot=0x6000000。
- 目标 serial 已脱敏，不尝试还原。

### 1.3 PREP10
- 文件：dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img
- 大小：46,563,215 bytes
- SHA-256：d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091
- Kernel Image SHA-256：f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21
- ACK tag android17-6.18.33_r00；commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9。
- 仅做文件离线复核，不得再次发送或启动。

### 1.4 Hybrid ABL / stock ABL
- R155 当前 ABL 转储：4,796,416 B；SHA-256 b39de91b88ef13db83892cd2e8dc4b914f7f9ed86954039fb1f64fbbf8460011。
- toolkit stock ABL：4,194,304 B；SHA-256 2190a37e9672375e7dda8c839d43e586be0c017709d77c0ff1fa6dab91a0029e。
- GhostLock abl_unlock.img 前缀：602,112 B；SHA-256 552e96d2565627563b7f2b072f720efd048abdf11fa050959aec55e7d3f0b79d。
- R155[0:602112] 等于 GhostLock 前缀，R155[602112:] 等于 stock ABL 同偏移尾部；401,135 个差异字节、1,541 个差异范围。
- R155 ABL 的 LZMA_ALONE 流在文件偏移 0x3078；解出 AArch64 PE 2,597,064 B，SHA-256 a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404。
- stock PE 2,531,528 B；SHA-256 44cda9af120520805bad31d0684afdf7411ce22baf9158a660e05e880e7d9176。
- Hybrid PE 与 stock PE 不同，不能用 stock PE 控制流代替 Hybrid 路径。
- ELF PT_LOAD 正确值 p_offset=0x3000、p_filesz=0x90000（589,824 B）、end=0x93000。602,112 B 是补丁前缀/窗口长度，不是 PT_LOAD 长度。
- Hybrid PE 含字符串 Failed to load/authenticate boot image: %r；单独字符串命中不证明它由 CmdBoot 调用。

### 1.5 vbmeta 边界
- R155 vbmeta：1 MiB，SHA e9b6e8ac9dbcc31ce30234f2cb8ab129c7b2912c7531caef70ea2a2547a2741d，flags@120=0x3。
- toolkit vbmeta：1 MiB，SHA af615d9fb0aebf99bb32f5328a9d90497a3ae0460dc6ffffb6e9bf077d636350，flags@120=0x2。
- 两份只差 offset 0x7b 一字节；14 个 tag=4 ChainPartition descriptors、0 个 tag=2 Hash descriptors。
- raw header+aux digest 不匹配 stored digest；只有将内存副本 flags 清零后才匹配。不得说原件验签通过。
- 当前 live vbmeta 未读取。SECURE_GETVAR_SOURCE、UNLOCKED_BYPASSES_RAMBOOT_AUTH、RAMBOOT_IMAGE_AUTH_CALL、FLASH_BOOT_AUTH_COMPARISON 均 UNKNOWN。

## 2. 阶段 A — 输入身份

在既有工作目录和原始交付包中定位文件。对每个文件记录路径、大小、SHA-256。身份不匹配就停止该分析分支，不能用相似文件替代，也不要无限全盘扫描。记录 Ghidra/IDA/Binary Ninja/objdump 等工具版本与架构设置。不要运行从固件提取的二进制。

## 3. 阶段 B — Windows Fastboot Host call trace

### B1. 实际 fastboot.exe
- 只检查历史工作目录/SDK platform-tools 文件；记录 fastboot.exe 绝对路径、大小、SHA-256、签名/文件版本和相关 DLL 的路径、版本、哈希。
- 可执行 fastboot --version 读取本机程序版本，但不得附带设备参数。
- 确认是否为 37.0.3-16887417；不匹配则报告实际版本。不得下载或替换工具。

### B2. 精确源码映射
- 找到与该二进制版本对应的 platform-tools/system-core 源码或可信版本映射；记录 tag/commit、路径和行号。
- 若只有 AOSP master 或其他 tag，标记 EXACT_37_0_3_SOURCE=NOT_VERIFIED，不得声称与本机 binary 完全相同。
- 逐步跟踪 CLI fastboot boot、镜像读取、download:size、DATA 响应、bulk data 写入、download 完成状态、Booting 文本打印位置、boot 命令写入 bulk OUT、随后 OKAY/FAIL/INFO 读取和 AdbWriteEndpointSync 错误传播。
- 对每个 AdbWriteEndpointSync 调用点记录函数、写入内容类型、长度（若可知）、timeout、错误码来源和调用栈。
- 对照 6,616 ms 总耗时分析最可能位置；没有 transport debug trace 不得编造写入内容或字节数。
- 必须区分主机 Windows USB endpoint write timeout 与设备 Fastboot FAIL response。

### B3. 历史 USB/PnP 日志
- 只读查询 2026-11-28 18:35:30 至 18:36:30 GMT+8 已存在的 Windows Kernel-PnP、USBHUB3、DriverFrameworks-UserMode、DeviceSetupManager 事件。
- 不启用新 tracing、不插拔、不重连、不安装驱动。
- 若历史记录不存在，写 NO_HISTORICAL_EVENT_DATA。无记录不能推断没有 USB 断连。
- 记录 Provider、Event ID、时间、脱敏设备实例 ID、描述和脱敏 XML。

Host 字段：FASTBOOT_EXE_IDENTITY、FASTBOOT_VERSION、EXACT_37_0_3_SOURCE、BOOT_COMMAND_CALL_SEQUENCE、DOWNLOAD_DATA_PHASE、BOOT_COMMAND_WRITE_PHASE、ADBWRITE_ENDPOINT_CALLSITE、ERROR_121_ORIGIN、REMOTE_FASTBOOT_FAIL_PACKET、WINDOWS_USB_PNP_EVENT。

## 4. 阶段 C — Hybrid ABL PE 静态分析

### C1. 提取
- 仅从哈希匹配的 R155 ABL 在 offset 0x3078 解 LZMA_ALONE，检查 Hybrid PE 尺寸/hash；从核验过的 stock ABL 独立提取 stock PE。
- 反汇编必须标出 PE file offset 与 AArch64 VA/RVA，说明映射依据。不可将 file offset 当 VA。
- 不运行、仿真或写入设备。

### C2. Fastboot command table / dispatch
- 在 Hybrid PE 定位 boot command 注册项及 handler/function pointer；以 download/getvar/flash 作交叉参照。
- 追踪 dispatch 如何解析命令并调用 handler；handler 返回值如何变成 OKAY/FAIL/INFO 或 USB teardown/reset。
- 若存在回调/异步状态机，闭合相应路径；处理 Wn/Xn alias、寄存器 kill、间接函数表和函数指针。
- 单个字符串、函数名猜测、单一 ADRP xref 或 decompiler 输出不足以证明完整调用链。

### C3. CmdBoot 路径
尽可能建立并逐边标注证据等级的路径：Fastboot boot RX → command dispatch/CmdBoot → image buffer/length → boot header parse → auth/signature/rollback → load/decompress/relocation → kernel/ramdisk/DTB handoff → response/USB teardown → kernel branch。

必须回答：
1. RAM boot 与 flash boot 是否走不同认证路径；不可用 flash handler 代替 CmdBoot。
2. secure/unlocked getvar 源头；是否存在 unlocked 绕过条件；记录布尔方向、调用者和控制流证据。
3. Failed to load/authenticate boot image: %r 的真实 xref、调用函数、CmdBoot 可达性以及错误后行为。
4. boot v2 header 接受条件、各 payload 大小/地址限制、load base、entry point 和异常路径。
5. 是否存在正常 boot handoff 中的 USB 停止/复位，以及相对 kernel branch 的顺序。
6. 是否存在 auth/parse failure 不发 FAIL 而令 USB endpoint 无响应的分支。没有证据就写 UNKNOWN。
7. 静态代码存在 auth failure 分支不等于本次执行触发该分支。

### C4. Hybrid 与 stock 对比
- 比较 command table、CmdBoot、auth、load、response 和 handoff 函数，记录 VA、函数长度/hash、基本块和调用边差异。
- 特别分析 GhostLock prefix 是否改变 boot command table、auth dispatch、USB response 或 handoff。
- 不得用 china_compile / c_per_F_compile 各 43 个字符串命中数相等作为行为相同的证明。

静态字段：HYBRID_ABL_IDENTITY、HYBRID_PE_IDENTITY、FASTBOOT_COMMAND_TABLE、CMD_BOOT_HANDLER、CMD_BOOT_AUTH_CALL、UNLOCKED_RAMBOOT_AUTH_BYPASS、BOOT_IMAGE_PARSE_PATH、KERNEL_HANDOFF_PATH、BOOT_ERROR_RESPONSE_PATH、USB_TEARDOWN_OR_RESET_PATH、HYBRID_STOCK_CMD_BOOT_EQUIVALENCE。

CMD_BOOT_AUTH_CALL=ABSENT 只有在 command table、handler 间接调用及相关调用链足够闭合时才允许；否则 UNKNOWN。

## 5. 阶段 D — 日志与静态证据关联

每项 claim 标记 OBSERVED / SOURCE_CONFIRMED / BINARY_CONFIRMED / INFERRED / UNKNOWN。

至少回答：
- Sending ... OKAY 能确认哪一个 host/protocol 阶段完成？不能额外推断的部分是什么？
- Booting 文本在发送 boot 命令之前还是之后打印？
- error 121 的 AdbWriteEndpointSync 写入内容是什么？不能确定就 UNKNOWN。
- boot command 是否可能完整到达 ABL？是否有直接证据？
- 是否观察到远端 FAIL 帧？区分 stderr 未显示与协议层确认未收到。
- 测试后 31 秒的一次 Fastboot 枚举只证明该时刻能枚举。
- 无 USB event log 不能证明 USB 未重枚举。
- 没有 handoff/UART/ADB/Linux gadget descriptor，KERNEL_EXECUTION 不能判 certainty NO。

最终状态模板：

    FIRST_BOOT01_RESULT = RAMBOOT_NOT_CONFIRMED_USB_WRITE_TIMEOUT
    HOST_FASTBOOT_LAYER = ...
    BOOT_COMMAND_DELIVERY = CONFIRMED | NOT_CONFIRMED | UNKNOWN
    ABL_CMD_BOOT_HANDLER_ENTERED = CONFIRMED | NOT_CONFIRMED | UNKNOWN
    ABL_IMAGE_AUTH_RESULT = PASS | REJECTED | UNKNOWN
    ABL_KERNEL_HANDOFF = CONFIRMED | NOT_CONFIRMED | UNKNOWN
    KERNEL_EXECUTION = CONFIRMED | NOT_CONFIRMED | UNKNOWN
    ROOT_CAUSE = CONFIRMED | PROBABLE | UNRESOLVED

ABL_IMAGE_AUTH_RESULT=REJECTED 必须有直接设备侧运行证据或可严格绑定本次请求的日志。静态分支不够。

## 6. 严格禁止

- 不连接平板，不检查当前设备状态，不执行任何 fastboot/adb 设备命令。
- 不重启、不拔插、不切 USB mode、不按设备按键、不重启 fastboot server。
- 不运行第二次 fastboot boot；不 flash/erase/format/update/set_active，不修改任一分区。
- 不 EDL/9008，不运行 HiSuite/TWRP 或恢复流程。
- 不改 ABL、PE、vbmeta、PREP10 或原始日志；分析脚本/导出单独保存。
- 不运行 ABL/PE/固件提取二进制、kernel、init、adbd。
- 不访问 userdata、persist、oeminfo、TEE key、IMEI、MAC、校准数据。
- 不安装或更新工具/驱动/固件，不下载替代镜像。
- 不把未经证实的推论写成事实，不进行无边界全盘扫描。

## 7. 交付

生成 K1_ABL_BOOTFAIL_ANALYSIS02_REPORT.zip，包含：
1. K1_ABL_BOOTFAIL_ANALYSIS02_REPORT.md — 中文总报告与结论等级；
2. fastboot_host_calltrace.md — exe 身份、精确源码映射、调用顺序与 AdbWriteEndpointSync 调用点；
3. windows_usb_event_review.md — 历史 PnP 记录；若无记录明确写明；
4. hybrid_abl_cmd_boot_analysis.md — CmdBoot、auth、load、response、handoff 证据；
5. hybrid_stock_diff.md — 对应函数差异；
6. evidence_matrix.csv — claim、证据类别、文件、offset/VA/line、置信度和限制；
7. SHA256SUMS.txt — 对所有交付文件重新准确计算哈希。

可附最小必要反汇编片段和 CFG，不附完整 ABL/PE/boot/ramdisk/vbmeta 原件，不上传敏感数据。

如 GitHub 认证和本地仓库已可用，上传脱敏报告、证据矩阵与 ZIP 至 hhdy/matepad11-dby-w09-agent-reports，目录 firmware-analysis/boot-v2/bootfail-analysis02/。若不可用，不安装 gh 或其他工具，交付本地 ZIP 全路径与 SHA-256。

## 8. 停止条件

- 文件身份不匹配即停止该分支，不用相似版本替代。
- Hybrid CmdBoot 间接调用不能闭合就标 PARTIAL/UNKNOWN，不无限扫描。
- 找不到 37.0.3 精确源码则 EXACT_37_0_3_SOURCE=NOT_VERIFIED。
- 没有历史 USB/PnP 记录就记录缺失，不补采。
- 完成后立即停止，交 AI1 审核；不设计下一轮设备启动，不请求用户切模式。

本任务的目标是把 error 121 定位到主机 Fastboot 调用链的哪一步，并审查 Hybrid ABL CmdBoot 静态路径能否解释失败；不是强行宣布已经找到认证拒绝根因。