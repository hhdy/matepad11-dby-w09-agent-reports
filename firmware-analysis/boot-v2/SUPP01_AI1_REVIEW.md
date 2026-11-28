# SUPP01 — AI1 独立审核报告

**审核日期：** 2026-11-28  
**对象：** `SUPP01_UNLOCKBL_FOLDER_ASSESSMENT.zip`  
**ZIP SHA-256：** `47bacd7070df1a9bcfd1f2ed52a0df450a784d8fdf50a5246d533a9fe7297201`  
**报告 SHA-256：** `03eb974fdb693d23d6fb6402f4f2969d5add35d8bce796e8f19fd1071062c2e9`

**结论：SUPP01 报告包完整性 PASS；其关键发现具有高价值，但当前 ABL 身份、vbmeta 状态和恢复能力仍有待原始证据复核。不得据此批准 `fastboot boot`。**

## 1. 交付核验

AI1 已对上传 ZIP 进行复算：

- ZIP 5,596 B，SHA-256 与上列一致；
- CRC / testzip 通过；
- 共 2 个条目：`SHA256SUMS.txt`、`SUPP01_UNLOCKBL_FOLDER_ASSESSMENT_REPORT.md`；
- 内部报告 SHA-256 与独立上传 Markdown 完全一致：`03eb974fdb693d23d6fb6402f4f2969d5add35d8bce796e8f19fd1071062c2e9`。

注意：ZIP 不含 `abl.img`、`abl_unlock.img`、ROUND155 ABL 分区转储、`abl_check.py`、`vbmeta.img`、原始日志或 EDL 工具。因此 AI1 验证了报告本身的完整性，但没有独立复现其三方字节比较及历史日志结论。报告中的相关内容应标为“报告声明/待源文件复核”。

## 2. 重要发现：当前 ABL 据称为 Hybrid ABL

SUPP01 报告声称，当前 ABL 分区 4,194,304 B 由 GhostLock 工程补丁前 602,112 B 和 stock ABL 后 3,592,192 B 组成：

- ROUND155 当前 ABL 转储前 602,112 B = `abl_unlock.img`；
- 转储剩余字节 = stock `abl.img` 对应尾部；
- 全部差异在补丁窗口内。

如果使用原始文件复现通过，则当前在用 ABL 应视为“工程补丁前段 + stock 后段”的混合体；`abl_unlock.img` 只是 602,112 B 补丁前缀，绝不是完整 ABL 镜像，严禁将其当成完整镜像使用。

报告还称 PREP13 的 `a14e29...` PE 载荷是从 ROUND155 当前分区转储解出的。若提取链能复现，则 PREP13 函数级分析是针对设备当前在用 ABL，而非另一个 stock 副本。

**状态：HIGH-VALUE / SOURCE REPRODUCTION REQUIRED。** 原始输入、完整 SHA-256 和比较脚本未包含在 ZIP 内。后续必须补齐所有源文件完整哈希，并复现混合关系与 PE 提取链。

## 3. 必须纠正的过度表述

### 3.1 Orange 不证明 AVB/verity 全部关闭

AOSP 将 ORANGE 定义为 bootloader 处于 unlocked 状态，正常 Verified Boot 信任链无法建立；它不自动证明当前 vbmeta flags、dm-verity 行为或所有镜像认证路径均已关闭。AOSP 参考：
- https://source.android.com/docs/security/features/verifiedboot/device-state
- https://source.android.com/docs/security/features/verifiedboot/boot-flow

SUPP01 只称 2026-11-21 写入过一个 1 MiB `vbmeta.img`，没有当前 vbmeta 分区读取哈希，也没有该镜像解码后的 AVB flags/descriptors。应分别记录：
- 曾写入 vbmeta：日志声明；
- 该文件具体 flags：待离线解析；
- 当前设备 vbmeta 分区内容：UNKNOWN；
- 当前 dm-verity / AVB policy：UNKNOWN；
- Fastboot `secure=yes` 是否被绕过：UNKNOWN。

Fastboot 的 `secure=yes` 是独立门禁语义。AOSP Fastboot 规范将其定义为要求在安装或启动镜像前提供签名的 secure bootloader；当前华为 ABL 如何将其与 unlock/GhostLock 状态结合，必须查实际控制流：
https://android.googlesource.com/platform/system/core/+/main/fastboot/README.md

### 3.2 fastboot boot 不是“绝对零持久化”

`fastboot boot` 通常不会把传入 boot image 写入 boot 分区；但若候选内核/ramdisk 获得执行权，它仍可能访问并写入 userdata 或其他块设备。因此不能保证整个 RAM boot 尝试绝对无持久化副作用，也不能把“boot 分区未被命令直接覆盖”称为“设备状态完全可回滚”。

### 3.3 EDL/TWRP/HiSuite 不是已验证恢复路径

- EDL 工具材料存在，不等于设备成功进入 9008、接受 programmer 或完成 Firehose 会话；
- 报告称 TWRP 曾写入 recovery_ramdisk，不等于已证明当前能启动 TWRP 并执行恢复；
- HiSuite 已安装，不等于已验证能恢复当前 C00 / HOS4.3；
- stock ABL 备份存在，不等于已验证写回路径。

恢复能力应标为 **PARTIAL / NOT EXERCISED**；EDL 是 **UNVERIFIED / LAST RESORT**。

## 4. 模式切换日志存在矛盾

SUPP01 记载 2026-11-28 15:51:47 工具箱发送过“重启到 Fastboot”；而 PROBE02 声明设备由用户手动进入、Agent 零重启/零模式切换。

目前无法仅凭报告判断是用户点击工具箱按钮、Agent 调用脚本，还是日志仅记录提示。需要只读导出 `20261128.log` 对应行及前后至少 30 行，明确命令、调用组件和操作来源。来源未厘清前，将“Agent 零模式切换”标记为待核对；不预先归责，也不继续宣称已证明零模式切换。

## 5. UniXNU/iPadOS 档案

报告登记的 UEFI/XNU USB 调试、UFS/SM8250 驱动、面板供电、Panel_290_20d_10p9、Battery/SmartPA/GeniI2c 经验具有潜在复用价值。但它们只能作为独立硬件资料源；不能把 UEFI/XNU 成功外推为 ACK Linux 驱动已工作，也不要把该项目并入当前 ACK 源码或变成并行大任务。

## 6. 最终状态

| 项目 | AI1 状态 |
|---|---|
| SUPP01 报告包完整性 | PASS |
| 当前 ABL 为 hybrid 的报告结论 | HIGH-VALUE / NEEDS SOURCE REPRODUCTION |
| PREP13 `a14e29...` 为当前 active ABL payload | REPORT CLAIM / REPRODUCTION REQUIRED |
| 当前 ABL `secure/unlocked/boot` 认证路径 | UNKNOWN |
| 当前 vbmeta 与 verity 状态 | UNKNOWN |
| EDL 救援能力 | UNVERIFIED / LAST RESORT |
| stock ABL 回写能力 | BACKUP REPORTED / RESTORE UNVERIFIED |
| TWRP 恢复能力 | FLASH REPORTED / BOOT & RESTORE UNVERIFIED |
| 一次性 `fastboot boot` 授权 | **NOT APPROVED** |

## 7. 下一步

不重做 PREP13/PREP14 泛化分析，也不重新连接设备。只执行修订后的 `K1-ABL-FASTBOOT-AUTH-PATH01-REV2` 离线窄审计：

1. 找到并给 ROUND155 转储、stock ABL、GhostLock patch、`a14e29...` PE、vbmeta 文件计算完整 SHA-256；
2. 复现三方 Hybrid ABL 字节关系与 PE 提取链；
3. 当前 Hybrid ABL 做 Fastboot `secure/unlocked/download/boot/flash` 认证控制流审计，stock ABL 作为对照；
4. 离线解析 vbmeta 文件，但不把文件状态外推为当前分区；
5. 导出 2026-11-28 15:51:47 日志上下文，解决模式切换来源矛盾；
6. 不执行设备命令、重启、OEM、分区读写、EDL、短接、签名或镜像修改。

— AI1 独立审核结束 —
