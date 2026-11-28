# K1-ABL-AUTH-CLOSE01-CORR01 — AI1 直接修正报告

**日期：** 2026-11-28  
**输入：** CLOSE01 与 REV2 交付中的 R155 / toolkit 原始 vbmeta 文件  
**CLOSE01 ZIP SHA-256：** `9bae3303d67190aad43c8073953d43fd7d5d962c269db203fa10a7348c06cc32`  
**REV2 ZIP SHA-256：** `c2e605d3f4acea00983664518e0dada84c941571b9dcaf443468342655e5c226`  
**结论：** 本报告取代 CLOSE01 的 Stage C 结论。Stage B 的 `RAMBOOT_AUTH=UNKNOWN/NO-GO` 保持不变；不需要 Agent 再执行，不批准 `fastboot boot`。

## 1. AOSP 格式定义

用户此前给出的 tag 顺序也需要纠正。AOSP `AvbDescriptorTag` 的准确值：

| Tag | AOSP descriptor |
|---:|---|
| 0 | PROPERTY |
| 1 | HASHTREE |
| 2 | HASH |
| 3 | KERNEL_CMDLINE |
| 4 | CHAIN_PARTITION |

AOSP header offsets：
- 112: `rollback_index` (uint64 BE)
- 120: `flags` (uint32 BE)
- 124: `rollback_index_location` (uint32 BE)
- 128: `release_string`

flags:
- bit 0 = `HASHTREE_DISABLED`
- bit 1 = `VERIFICATION_DISABLED`（AOSP 注释说明此位会禁用 verification，并不解析 descriptors）

官方定义：
- https://android.googlesource.com/platform/external/avb/+/master/libavb/avb_descriptor.h
- https://android.googlesource.com/platform/external/avb/+/master/libavb/avb_vbmeta_image.h
- https://android.googlesource.com/platform/external/avb/+/refs/heads/main/libavb/avb_chain_partition_descriptor.h
- https://android.googlesource.com/platform/external/avb/+/main/avbtool.py

## 2. 原始文件与 Header 结果

| File | Size | SHA-256 |
|---|---:|---|
| R155 vbmeta | 1,048,576 B | `e9b6e8ac9dbcc31ce30234f2cb8ab129c7b2912c7531caef70ea2a2547a2741d` |
| Toolkit vbmeta | 1,048,576 B | `af615d9fb0aebf99bb32f5328a9d90497a3ae0460dc6ffffb6e9bf077d636350` |

两份文件均为 AVB 1.0、`SHA256_RSA2048`，auth block 320 B，aux block 9,280 B，stored hash 32 B、signature 256 B、公钥 blob 520 B，release string `avbtool 1.1.0`。AVB 实际块总长 9,856 B；余下 1,038,720 B 全部为零填充。

| File | flags @120 | HASHTREE_DISABLED | VERIFICATION_DISABLED | header rollback_index_location @124 |
|---|---:|---|---|---:|
| R155 | 0x3 | yes | yes | 0 |
| Toolkit | 0x2 | no | yes | 0 |

以上仅为两个文件的原始 header 值，不是当前设备 live vbmeta 状态，也不能直接推导 Huawei ABL 的运行策略。

## 3. Descriptors：两份均为 14 × Chain Partition，0 × Hash

两份 descriptor 区均为 8,744 B，正确 walk 得到 14 个 tag=4 (`CHAIN_PARTITION`)，没有 tag=2 (`HASH`) 或 tag=0 (`PROPERTY`)。

Chain Partition Descriptor 固定结构：16 B parent descriptor + 4 个 uint32（rollback_index_location、partition_name_len、public_key_len、flags）+ 60 B reserved；随后是分区名和公钥。所有记录长度、零 reserved 与边界通过。

| Partition | descriptor rollback_index_location | Public key size |
|---|---:|---:|
| boot | 1 | 520 B |
| ramdisk | 4 | 520 B |
| vbmeta_system | 2 | 520 B |
| vbmeta_vendor | 3 | 520 B |
| vbmeta_odm | 5 | 520 B |
| eng_vendor | 9 | 520 B |
| eng_system | 10 | 520 B |
| dtbo | 14 | 520 B |
| version | 6 | 520 B |
| vbmeta_hw_product | 7 | 520 B |
| preload | 11 | 520 B |
| preas | 19 | 520 B |
| preavs | 20 | 520 B |
| vbmeta_cust | 8 | 520 B |

因此 CLOSE01 原报告的“14 × Hash Descriptor”“boot image_size=100,663,296 B”及 boot/ramdisk/dtbo digest 对比均撤回。tag=4 是 chain descriptor；这两份文件没有 Hash Descriptor 来支持那些结论。

## 4. 文件比较：仅 flags 一个字节不同

R155 与 toolkit 两份 1 MiB 文件仅有一个差异字节：
- offset `0x7b`（header flags 的最低字节）
- R155 = `0x03`
- toolkit = `0x02`

其余全部相同：256 B header 除该 flags byte 外、320 B auth block、9,280 B aux block、embedded public key、signature、stored digest、14 个 descriptor 列表均一致。

所以撤回“不同公钥”“不同签名”“header rollback_index_location 分别为 3/2”。实际 header rollback_index_location 两者均为 0；3 和 2 是 flags。

## 5. AOSP Digest / RSA 检查

AOSP `avbtool.verify_vbmeta_signature()` 对完整 256 B header + auxiliary block 计算摘要：`SHA256(header[0:256] || auxiliary_block)`，不包含 authentication block。

Stored hash（两份相同）：
`0185207545e263326686e82baaf4096bf550c4973a5db03ba149e8e84aefff7f`

| File | Raw header+aux digest | Matches stored hash | RSA verify with embedded key |
|---|---|---|---|
| R155 flags=3 | `387dcdc6be1e1148f90cce86f38d75c9393101dfe7c1e0179c25ea993ada8372` | FAIL | FAIL |
| Toolkit flags=2 | `f52be205d09871c4a54450b61ee9d3985e9db904b510f01c742b5ca13b65b186` | FAIL | FAIL |

仅在**内存诊断副本**将 header flags [120:124] 清零后，两份计算摘要均为 stored hash，并使用 embedded RSA2048 key（e=65537）通过 PKCS#1 v1.5 / SHA-256 Prehashed 验签。

这说明 stored digest/signature 对应 flags=0 的 header，而当前存储的 flags 分别为 2 和 3。它与签名完成后修改 flags 字节相符，但离线材料不能确定修改者、时间或过程。不得把 flags-zero 副本通过表述成 raw 文件验签通过；也未验证 embedded key 是否属于设备硬件信任根。

## 6. 最终修订

撤回 CLOSE01 原报告中：
1. tag=4 是 Hash Descriptor；
2. 14 个 Hash Descriptor 与 boot image_size / boot、ramdisk、dtbo digest 比较；
3. 两个 vbmeta 使用不同 key/signature；
4. rollback_index_location 分别为 3、2；
5. flags=0；
6. 将 flags 清零后副本通过描述为 raw vbmeta 原件验证成功。

当前设备 live vbmeta 内容仍 UNKNOWN（R155 是历史转储）。Stage A Hybrid ABL 身份链仍 PASS。Stage B Fastboot 认证路径仍 PARTIAL，`SECURE_GETVAR_SOURCE`、`UNLOCKED_BYPASSES_RAMBOOT_AUTH` 和完整 CmdBoot auth chain 仍 UNKNOWN。

**最终门禁：`RAMBOOT_AUTH=UNKNOWN / NO-GO`；没有 fastboot boot 授权。**

本 CORR01 只做本地文件离线解析，没有设备连接、ADB/Fastboot 命令、重启、刷写或分区写入。
