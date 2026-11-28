# K1-FASTBOOT-GATE01 — AI1 独立审核与门禁结论修订

**审核日期：** 2026-11-28  
**审核对象：** `K1_FASTBOOT_GATE01_REPORT.zip`  
**项目：** Huawei MatePad 11 DBY-W09 / SM8250 / HarmonyOS 4.3.0.196(C00E100) / ACK Android 17 6.18.33  
**ZIP SHA-256：** `39a7884c9e22b0602d1e2b401c9b81e749ebe105d237bbe3c897e8c8b4966517`  
**AI1 结论：** **交付资料验收通过；撤销 `READY_FOR_EXPLICIT_BOOT_AUTHORIZATION`。当前为 `NO-GO FOR IMMEDIATE RAM-BOOT AUTHORIZATION`（待针对性核实），不得执行 `fastboot boot`。**

## 1. ZIP 与内部文件复核

- ZIP 大小：8,316 B；SHA-256 与 Agent 声明完全一致。
- ZIP CRC / `testzip()`：通过。
- 条目数：5；未发现多余缓存文件。
- `SHA256SUMS.txt` 覆盖的 4 个文件 SHA-256 均由 AI1 独立重算并通过。
- 报告、主机环境、fastboot 工具、设备只读记录均可正常解码。

因此，本轮交付物身份和完整性接受。这里的“接受”仅指报告包，不等于接受其 READY 判定。

## 2. 设备只读证据复核

### 2.1 已由 ZIP 原始记录支持

- `adb devices -l`：DBY-W09 / HWDBY 在 Android 模式在线。
- `fastboot devices -l`：无设备。
- 因设备未处于 Fastboot，B2 `fastboot getvar` 全部未执行；本轮没有擅自切换模式。
- `ro.boot.flash.locked=0`。
- `ro.boot.verifiedbootstate=orange`。
- `ro.boot.slot_suffix` 为空；`ro.build.version.release=12`；`ro.product.device=HWDBY`。

### 2.2 解锁状态判断

`flash.locked=0` 与 Verified Boot `orange` 是当前 bootloader 已解锁的有力、相互一致的证据。AOSP 说明：UNLOCKED 状态对应 ORANGE；若支持 `androidboot.flash.locked`，解锁时应为 `0`，并且 ORANGE 状态会映射到 `ro.boot.flash.locked=0`。

因此可以接受“当前启动状态呈现为 unlocked / orange”。但它们不是两条完全独立的证据链：两项属性都由启动链向 Android 传递，应该表述为同一启动状态的交叉印证，而不是“双重独立证据”。此外，这些 Android 属性不能代替进入 bootloader 后读取的设备侧 Fastboot 变量。

AOSP 参考：
- https://source.android.com/docs/security/features/verifiedboot/device-state
- https://source.android.com/docs/core/architecture/bootloader/locking_unlocking

## 3. READY 判定存在的关键逻辑错误

### 3.1 主机 fastboot 有 `boot` 命令，不等于设备 ABL 接受 `boot`

主机 `fastboot 37.0.3-16887417` 的 `--help` 确实列出：

`boot KERNEL [RAMDISK [SECOND]] — Download and boot kernel from RAM.`

这只证明主机程序包含该命令。报告 B1 证明设备仍在 Android 模式，B2 未执行；因此本轮没有任何当前设备侧证据证明 ABL 支持或接受 RAM boot。报告第 1 节把“当前 Android + ADB 健康、主机 fastboot 可用”记为“模式与能力无明显冲突”并给 ✓，证据不足。

AOSP 的 Fastboot 操作要求设备处于 bootloader 模式：
- https://source.android.com/docs/core/architecture/bootloader/locking_unlocking

### 3.2 同型号公开实机证据与 READY 结论相冲突

AI1 找到两份与 DBY-W09 / SM8250 直接相关的公开资料：

1. **同型号实机记录（2026-08-25 更新，DBY-W09 / C635 / SM8250）**：记录者在 Bootloader 已解锁后执行 `fastboot boot apatch-boot.img`。镜像发送成功，但 ABL 返回：

   `Booting ... FAILED (remote: 'Failed to load/authenticate boot image: Load Error')`

   之后该个体通过 `fastboot flash boot` 成功启动 patched boot。该记录明确区分了 RAM boot 被拒绝与分区 flash 成功。它不是当前用户这台 C00 / HOS 4.3 个体的同一 firmware/ABL，故不能据此断言当前个体一定拒绝；但它足以推翻“仅凭 unlocked 属性和主机 fastboot 子命令即可认为没有明显冲突”的推理。

   参考： https://blog.kinn-kinn.com/blog/su-wo-kudasai-matepad11-root （第 10.3 节；2026-08-24 至 25 实机测试；明确标注为 DBY-W09 / C635 特定个体）

2. **同机型主线 Linux 移植仓库**：README 描述目标为 Huawei MatePad 11 DBY-W09 / Snapdragon 865，并明确写明 `fastboot boot`（RAM boot）被拒绝，测试改为刷写分区。该 README 没有在相应段落附完整原始失败日志，证据等级低于上面的实机日志；但它是同型号、同 SoC 的直接风险提示。

   参考： https://github.com/svesnav/linux-dby-w09 （README “Boot flow”）

结论：当前个体是否支持 RAM boot 仍 UNKNOWN，但存在同型号实证反例。故本轮不能判为 READY，不能把“待验证”重写成“无明显冲突”。

## 4. 恢复路径被报告高估

Agent 确认主机有：
- stock live boot 备份：100,663,296 B / SHA-256 `7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8`；
- stock separate ramdisk：2,097,152 B / SHA-256 `4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb`；
- stock package boot 变体：100,663,296 B / SHA-256 `027f88fd6f318523925ca27a4d681d17a9bbca904b0c471ccc05e651d3da19b8`；
- HiSuite 14.0.0.380 已安装；设备 recovery / erecovery 分区存在（依据 PREP12-N 清单）。

同时，完整出厂 OTA / UPDATE.APP 未找到。报告没有验证 HiSuite 对当前 C00 / HOS 4.3.0.196 的实际恢复选项，也没有完成一次恢复演练。因此可以说“有 stock boot/ramdisk 备份和设备原生 recovery 分区”，但不能说“原厂恢复路径已验证”。HiSuite 已安装不等于已确认可恢复此具体版本/区域。

RAM boot 不会把所传 boot image 写入 boot 分区，这一点不应误解为整个运行过程绝对无持久化副作用。若内核和 ramdisk 实际运行并访问内部存储，不能仅凭命令名保证没有对数据分区的影响。失败后原 boot 分区仍未被本次命令直接覆盖，是有价值的风险降低，但不是完整恢复保证。

恢复资料情况：**PARTIAL / NOT EXERCISED**。

## 5. K1 可观测性尚未解决

即使未来确认 ABL 能接受 RAM boot，仍不能把“设备黑屏/无输出”解释为内核未启动或启动失败：

- PREP12-N 已确认候选 DTB 缺少已验证的 framebuffer/simplefb 路径，pixel format 和 scanout handoff 未知；当时结论是 framebuffer K1 BLOCKED。
- UART12 earlycon 仍是 HOLD：SE4 时钟、电源域、GPIO pinmux、GENI protocol、PCB TX 路由均未得到实机确认。

PREP12 AI1 审核：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/boot-v2-first-package-prep/firmware-analysis/boot-v2/PREP12_AI1_REVIEW_AND_UART_EARLYCON_CORRECTION.md

所以当前不仅 RAM boot 接受性未知，而且即使 ABL 接受，也没有一个已验证的 K1 早期输出通道。不能把一次不可观测的黑屏测试当作有效的启动验证。

## 6. 按门禁条件重新判定

| 条件 | AI1 复核 | 说明 |
|---|---|---|
| 候选镜像身份 | PASS | 本轮仅凭报告中的现场 hash 声明；候选冻结身份此前已在 K1-HOST-PREP01 独立验收 |
| 主机 fastboot 工具 | PASS（主机端） | 版本与 `boot` help 项存在；不代表设备端支持 |
| 设备身份 | PASS | ADB / getprop 记录一致 |
| bootloader 解锁状态 | PASS（Android 属性证据） | `0` + `orange` 一致，但非两条完全独立证据 |
| 设备侧 fastboot / RAM boot 能力 | UNKNOWN / CONFLICTING EVIDENCE | 本轮不在 Fastboot；同型号已存在 RAM boot 被拒绝的实机证据 |
| 原厂恢复路径 | PARTIAL | stock boot/ramdisk 与 recovery 分区存在；完整 UPDATE.APP 缺失，HiSuite 对当前版本恢复能力未验证 |
| 早期启动可观测性 | NOT READY | framebuffer BLOCKED；UART12 HOLD |

**最终判定：NO-GO FOR IMMEDIATE `fastboot boot` AUTHORIZATION。** 这不是断言当前个体一定拒绝 RAM boot，而是现有证据不满足 READY 门槛，且同型号反例与观测通道缺失都没有被处理。

## 7. 下一步建议（有边界，不再泛化审计）

不开始 PREP15，不重做 XBL / ABL / DTB 大范围静态扫描，不刷分区。

下一步只做一次有明确边界的 **K1-FASTBOOT-PROBE02**：

1. 先由用户明确授权设备进入 Fastboot；优先由用户手动关机后按 Power + Volume-Down 进入，不从 Android 执行 `adb reboot`。
2. 进入后只执行任务书 B2 的只读 `fastboot getvar`，补齐 `product / unlocked / secure / version / version-bootloader / max-download-size / is-userspace / slot-count / current-slot / has-slot:boot / partition-size:boot / partition-type:boot`。
3. 禁止全部 `fastboot oem`、`fastboot boot`、flash、erase、reboot 和任何写入。
4. 记录 bootloader 版本和 USB 识别情况，与上述同型号拒绝记录对照。
5. 同时在主机端核实是否存在针对当前 C00 / HOS4.3 的可执行官方恢复入口；不能只以“HiSuite 已安装”作为恢复证明。

PROBE02 仍不能证明 RAM boot 一定会被接受；它的作用是识别当前 ABL/bootloader 版本，并判断是否有足够依据提出一次性启动申请。只有在输出通道或启动结果判据也有明确方案后，才重新评估一次性 RAM boot。

## 8. 操作边界

本次审核仅检查上传 ZIP、使用 AOSP 官方文档和公开同型号资料。未连接设备，未发送 ADB / Fastboot / OEM 命令，未重启、临时启动、刷写或修改任何分区。

— AI1 独立审核完 —
