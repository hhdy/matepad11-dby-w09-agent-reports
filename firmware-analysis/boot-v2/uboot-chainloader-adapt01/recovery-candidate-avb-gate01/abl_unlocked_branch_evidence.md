# abl_unlocked_branch_evidence.md

- ABL PE：`a14e29da…dbb404`（VA==file offset，LOAD_MAP01 已证）
- 本轮范围：解锁状态源 + UNLOCKED/LOCKED 分支的一次聚焦检查

## 既有证据（引用不重复）

- ADDENDUM01：recovery→共享 BootLinux 尾段（0x36C1C–0x388E8）、gz→ImageBuffer+0x80000、4KiB、x0=FDT = CONFIRMED
- AUTH/CLOSE01 轮：auth 七字段全 UNKNOWN；suffix 表 {suffix_ptr, handler_ptr}（0xCC668+）+ AsciiStriCmp 尾匹配为 fastboot 分发形态；static linear dataflow 无法闭合全部 dispatch

## 本轮检查结果

1. 解锁相关字符串在册：`androidboot.vbmeta.device_state`（0xBFB19）、`PHONE Relocked`（0xC67DE）、`RELOCKED`（0xC6CFF）、`secure`（getvar 处理族 0x4BAC0）、`oem relock`（0xC621A）、`userlock=relocked`（0x1057B1）等。
2. 这些字符串指向 **cmdline 附加与 getvar 应答层**，而非独立的 recovery 校验跳过开关；`LoadImageAndAuth/VB2` 的 AVB 调用链（libavb ops→read_from_partition/validate_public_key…）在字符串层完整（assert fail: ops->…），但其 **unlock-state 输入源**（devinfo 分区 / EFI 变量 / TEE syscall / HIMNTN 位）未能在本轮一次数据流内定位到具体 provider。
3. 决定 UNLOCKED/LOCKED 行为的 provider 不在冻结 PE 内的可能性存在（与 §17.0 两个 vendor protocol GUID 同模式）。

## 结论

`ABL_UNLOCKED_RECOVERY_ACCEPTANCE = UNKNOWN`。缺失的最小证据（二选一）：
- 静态：以 recovery_vbmeta 读取/`validateVBMetaPublicKey` 类调用点为根的跨协议数据流 pass（一次）；
- 设备侧：受控 `fastboot boot candidate` 非持久实验（需另行授权）。
