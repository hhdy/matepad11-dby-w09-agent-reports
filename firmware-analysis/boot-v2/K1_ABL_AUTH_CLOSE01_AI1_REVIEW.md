# K1-ABL-AUTH-CLOSE01 — AI1 独立审核补充结论

**日期：2026-11-28**  
**对象 ZIP SHA-256：** `9bae3303d67190aad43c8073953d43fd7d5d962c269db203fa10a7348c06cc32`  
**结论：** Stage B 的 `RAMBOOT_AUTH=UNKNOWN/NO-GO` 保留；Stage C-FIX 拒绝，需更正报告。不得执行 `fastboot boot`。

## 1. ZIP 和文件核验

ZIP SHA、CRC、18 项文件结构通过；SHA256SUMS 中 14 个条目独立复核通过。Hybrid PE、复现 PE、stock PE、R155 vbmeta 身份均与清单相符。未被 SUMS 覆盖的派生文件及缺失的反汇编摘录应修订清单。

Stage A 的 Hybrid ABL 字节关系与 LZMA 提取链已独立复现通过。REV2 的 PT_LOAD 数值仍须保持勘误：p_offset=0x3000，p_filesz=0x90000（589,824 B），end=0x93000；602,112 B 是补丁窗口/文件长度，不是 PT_LOAD 段长度。

## 2. AOSP descriptor tag：Agent 和用户提供的 tag 说明均需以官方定义更正

AOSP `AvbDescriptorTag` 枚举：
- 0 PROPERTY
- 1 HASHTREE
- 2 HASH
- 3 KERNEL_CMDLINE
- 4 CHAIN_PARTITION

官方源文件：
- https://android.googlesource.com/platform/external/u-boot/%2B/refs/heads/android-tv-s-beta3/include/libavb/avb_descriptor.h
- https://android.googlesource.com/platform/external/avb/%2B/main/avbtool.py

所以 tag=4 绝不是 HashDescriptor；它是 Chain Partition Descriptor。R155 和 toolkit 文件各含 14 个 tag=4、0 个 tag=2 描述符。首项从文件偏移 0x240 开始，tag=4、num_bytes_following=600、rollback_index_location=1、partition_name_len=4、public_key_len=520、flags=0；名称位于 0x29c，值为 boot。这与 Chain descriptor 固定 92 B 头完全吻合。

14 个 chain entries（partition → rollback_index_location）：
`boot:1, ramdisk:4, vbmeta_system:2, vbmeta_vendor:3, vbmeta_odm:5, eng_vendor:9, eng_system:10, dtbo:14, version:6, vbmeta_hw_product:7, preload:11, preas:19, preavs:20, vbmeta_cust:8`。

因此撤销“14 个 AvbHashDescriptor”“boot image_size=100,663,296 B”及“boot/ramdisk/dtbo Hash digest 相同”等结论。

## 3. VBMeta Header 字段与原件比较

AOSP header 的 offset 120 是 `flags`，offset 124 是 `rollback_index_location`；CLOSE01 将它们反读。AOSP 定义 bit0=HASHTREE_DISABLED、bit1=VERIFICATION_DISABLED：
- https://android.git.googlesource.com/platform/external/avb/%2B/refs/heads/main-kernel/avbtool.py
- https://android.googlesource.com/platform/external/u-boot/%2B/ed5e22c8d99ea0993d6904f4a3184f02bf3c1456/lib/libavb/avb_vbmeta_image.h

独立实测：
| 文件 | flags @120 | rollback_index_location @124 |
|---|---:|---:|
| R155 | 0x3 | 0 |
| toolkit | 0x2 | 0 |

R155 flags=3 表示 bit0、bit1 均置位；toolkit flags=2 表示仅 bit1 置位。以上仅是两个本地文件的头部值，不代表当前设备 live vbmeta。

R155 SHA-256：`e9b6e8ac9dbcc31ce30234f2cb8ab129c7b2912c7531caef70ea2a2547a2741d`  
toolkit SHA-256：`af615d9fb0aebf99bb32f5328a9d90497a3ae0460dc6ffffb6e9bf077d636350`

两个 1 MiB 文件只差一个字节：offset 0x7b，R155=03、toolkit=02。其余 256 B header、320 B authentication block、9,280 B auxiliary block完全相同；embedded public key、signature bytes、stored digest 均相同。因此撤销“不同公钥/不同签名”及“rollback location 分别为 3/2”的说法。

## 4. AOSP digest/signature 检查

AOSP `verify_vbmeta_signature()` 对完整 256 B header + auxiliary block 计算摘要，不包含 authentication block：
https://android.googlesource.com/platform/external/avb/%2B/de53827b226bccef7407e4c253b0152e8d9f8e04/avbtool

两份原始文件的 stored digest 都是：
`0185207545e263326686e82baaf4096bf550c4973a5db03ba149e8e84aefff7f`

直接对 raw header+aux 计算：
- R155：`387dcdc6be1e1148f90cce86f38d75c9393101dfe7c1e0179c25ea993ada8372`，不匹配；
- toolkit：`f52be205d09871c4a54450b61ee9d3985e9db904b510f01c742b5ca13b65b186`，不匹配。

在临时内存副本将 flags [120:124] 清零后，两个计算结果均变为 stored digest。AI1 使用内嵌 RSA2048 public key，以 SHA256/PKCS#1 v1.5 的 Prehashed 校验，签名对该 flags=0 副本通过。故可说“签名/digest 对应 flags=0 的 header 副本”；不能说 raw 文件按当前 flags 通过 AOSP 验签，也不能断言修改人或修改时间。标准 AOSP verifier 对两个当前原始 header 的 digest check 均失败。

## 5. Stage B 保留 UNKNOWN

修复版 xref 工具仍不是完整 CFG reaching-definitions 求解器，未统一 kill 所有写寄存器指令，未完整处理 wN/xN alias、函数指针/后缀表注册。故字符串无直接 ADR/ADRP 引用不能证明控制流不存在。

最终 `SECURE_GETVAR_SOURCE`、`UNLOCKED_BYPASSES_RAMBOOT_AUTH`、`RAMBOOT_IMAGE_AUTH_CALL`、`FLASH_BOOT_AUTH_COMPARISON` 仍为 UNKNOWN；保留 `RAMBOOT_AUTH=UNKNOWN/NO-GO` 是正确且必须维持的结论。

## 6. 最终门禁

- Stage A：PASS（附 PT_LOAD 长度勘误）。
- Stage B：PARTIAL；认证路径 UNKNOWN。
- Stage C：原件身份 PASS；CLOSE01 的 tag/结构/header/self-hash 解析 REJECTED。
- Stage D：日志事件时序成立；精确命令 argv/触发来源 UNKNOWN。
- 当前设备 live vbmeta 未读取；R155 是历史快照。
- `fastboot boot`：**NOT APPROVED / NO-GO**。

不再做大范围 ABL/XBL 扫描，不连接设备。只需要 Agent 发布 CLOSE01-CORR01 报告修订：更正 descriptor tags/header offsets/hash method，撤回不成立的描述符、公钥和 image digest 结论；保留所有认证行为 UNKNOWN。不得执行任何设备操作。

— AI1 —
