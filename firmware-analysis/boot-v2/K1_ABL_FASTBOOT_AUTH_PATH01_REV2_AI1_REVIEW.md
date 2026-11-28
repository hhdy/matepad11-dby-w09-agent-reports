# K1-ABL-FASTBOOT-AUTH-PATH01-REV2 — AI1 独立审核报告

**审核日期：** 2026-11-28  
**审核对象：** `K1_ABL_FASTBOOT_AUTH_PATH01_REV2_REPORT.zip`  
**ZIP SHA-256：** `c2e605d3f4acea00983664518e0dada84c941571b9dcaf443468342655e5c226`  
**最终结论：** **Stage A ACCEPTED（附 PT_LOAD 数值勘误）；Stage B PARTIAL，认证门禁 UNKNOWN；Stage C PARTIAL（描述符分类错误且 r155 vbmeta 缺失）；Stage D 日志时序成立。当前不得据此批准 `fastboot boot`。**

---

## 1. ZIP、文件清单与哈希验收

- ZIP SHA-256 与 Agent 声明完全一致。
- ZIP CRC / `testzip()` 通过，共 40 个条目。
- `SHA256SUMS.txt` 中 39 个被列明文件的哈希全部独立复算通过；ZIP 自身清单不对自己做哈希。
- ZIP 含 3 份 ABL 原始输入（r155 ABL、stock ABL、GhostLock `abl_unlock.img`）、工具箱 vbmeta、两个 PE 派生产物、分析脚本与报告。
- ZIP **不含** manifest 中列出的 `R155\\vbmeta.img`（SHA 前缀 `e9b6e8ac…`）原始转储。这一缺失影响 Stage C 的独立复核。

报告和输入文件都能读取。交付包本身：**PASS**。

## 2. Stage A：Hybrid ABL 身份链 — PASS

### 2.1 独立核对的完整 SHA-256

| 输入 | 大小 | SHA-256 | AI1 |
|---|---:|---|---|
| r155 当前 ABL 转储 | 4,194,304 B | `b39de91b88ef13db83892cd2e8dc4b914f7f9ed86954039fb1f64fbbf8460011` | PASS |
| stock ABL 备份 | 4,194,304 B | `2190a37e9672375e7dda8c839d43e586be0c017709d77c0ff1fa6dab91a0029e` | PASS |
| GhostLock `abl_unlock.img` | 602,112 B | `552e96d2565627563b7f2b072f720efd048abdf11fa050959aec55e7d3f0b79d` | PASS |
| 当前 Hybrid PE 载荷 | 2,597,064 B | `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404` | PASS |
| toolkit vbmeta 文件 | 1,048,576 B | `af615d9fb0aebf99bb32f5328a9d90497a3ae0460dc6ffffb6e9bf077d636350` | PASS |

REV2 任务书的 Hybrid PE SHA 字符串确实少了一个字符；以本轮完整哈希 `…93747dbb404` 为准。

### 2.2 三方 Hybrid 关系独立复现

AI1 重新执行字节比较，以下关系全部成立：

- `r155[0:602112] == abl_unlock.img`；
- `r155[602112:] == stock_abl.img[602112:]`；
- 三文件大小分别符合清单；
- stock 与 r155 的全部差异都在 `[0, 602112)`；
- 不同字节数 401,135；连续差异区间 1,541 个。

因此可以确认：**所提交的 r155 ABL 转储，其前 602,112 B 与 `abl_unlock.img` 完全相同，剩余部分与 stock ABL 完全相同。** 这是输入文件层面的字节级事实。

### 2.3 LZMA / PE 提取链独立复现

AI1 从 r155 ABL 容器的 `0x3078` 处按 LZMA_ALONE 解压：

- Hybrid 输出 2,597,064 B，SHA-256 精确为 `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747b404`；
- stock 输出 2,531,528 B，SHA-256 `44cda9af120520805bad31d0684afdf7411ce22baf9158a660e05e880e7d9176`。

A3 复现通过。两份解压 PE 的体积相差 65,536 B，编译路径标识不同，说明两份嵌入载荷并非同一 PE 的少量位修订。

### 2.4 必须勘误的 ELF PT_LOAD 数值

报告把 ELF32 `PT_LOAD` 写成 `[0x3000, 0x93000) = 602,112 B`。这把**结束文件偏移**误当成**段长度**：

- `p_offset = 0x3000`；
- `p_filesz = 0x90000 = 589,824 B`；
- `p_offset + p_filesz = 0x93000`。

`abl_unlock.img` 总长度 `0x93000 = 602,112 B`，两者不是同一个数值。前 0x3000 B 为容器/ELF 前置数据；PT_LOAD 实际载荷从 0x3000 开始，长度 0x90000。正确表述应为：**补丁窗口长度 602,112 B；唯一 PT_LOAD 的文件范围为 `[0x3000,0x93000)`，段长 589,824 B。**

因此“PT_LOAD 恰为 602,112 B”的数值结论错误；“后续分区尾部未被该 PT_LOAD 覆盖”是成立的范围事实，但不能仅凭这个段表绝对断言整个 ABL loader 永远不会读取其他容器字节。

## 3. Stage B：Fastboot 认证路径 — PARTIAL，多个函数级定位无效

Agent 将整体结论定为 PARTIAL、签名门禁 UNKNOWN，这个总级别是谨慎的；但报告中若干函数地址映射和 xref 结论经独立反汇编复核并不成立，需撤销或降级。

### 3.1 `getvar:secure` xref 错配

报告称 `0x2e358` 的 ADRP+ADD 引用了字符串 `secure`（0xcaf2b），随后将 `0x4bac0` 定为 secure 布尔值函数。实际指令为：

```asm
0x2e350  adrp x0, #0xca000
0x2e358  add  x0, x0, #0xf25
0x2e35c  bl   0x31270
```

该地址计算为 `0xca000 + 0xf25 = 0xcaf25`，指向 `serialno` 字符串内部的 `ialno`，并非 `secure` 起始地址 `0xcaf2b`。

同一分派片段的 `0x2e378`：

```asm
0x2e370  adrp x0, #0xca000
0x2e378  add  x0, x0, #0xc8c
0x2e37c  bl   0x31270
0x2e380  bl   0x4bac0
```

计算目标为 `0xcac8c`，也不是 `secure`。因此**0x4bac0 作为 `getvar:secure` 值函数的映射没有被证明，应撤回**。当前 `secure` 变量字符串存在，但实际注册/分派、状态来源与返回值仍为 UNKNOWN。

### 3.2 ADRP/ADD xref 扫描器有陈旧寄存器状态 bug

`fb_setup_xref.py` / `fb_table3.py` 先收集一个窗口内寄存器历史 ADRP，然后回溯寻找任意较早且页地址匹配的 ADRP。若在该 ADRP 后寄存器已被另一条 ADRP 写入不同页，脚本仍会继续选择更老的 ADRP，产生不成立的 xref。它没有按控制流/寄存器定义维护 reaching definition，也没有可靠处理跨基本块状态。

由此造成下列已提交映射错误：

- `0x1de90` 并没有通过所给 ADRP+ADD 指令引用 `0xcbc34`；对应片段中 `0x1de88` 的页寄存器是 `0xc6000`，`0x1de90` 的 ADD 目标为 `0xc6c33`。
- `0x41aa0` 的前序 `0x419fc ADRP x1, #0xd1000` 与 `0x41aa0 ADD x1, x1, #0xc2f` 得到 `0xd1c2f`，不是 `0xcbc34`。
- 因此将 `0x41824` 函数称为认证失败/ CmdBoot 函数，依据不足。

另有一条有效引用：

```asm
0x3052c  adrp x0, #0xcb000
0x30530  add  x0, x0, #0xc33
0x30540  bl   0x2b794
```

`0xcb000 + 0xc33 = 0xcbc33`，它确实指向 `Failed to load/authenticate boot image: %r` 字符串附近（字符串起始偏移存在一个字节差异）。但该点只证明**有代码路径引用这条诊断消息**；当前提交的证据尚未把调用者完整识别为 Fastboot CmdBoot，也未闭合认证结果、EFI 加载/跳转与错误返回的完整链路。

### 3.3 命令表和 FastbootCommandSetup 结论不成立

`fb_table3.py` 的 `cstr()` 只允许 `0x109000 <= pointer < N`，但 Hybrid PE 中相关字符串位于约 `0xca000`–`0xd0000`，导致候选字符串指针被过滤，最终 `entries=0` 没有任何否定意义。

`fb_table2_out.txt` 在 `0xcc668` 起展示出疑似 16 B `{字符串指针, 代码指针}` 交替记录，例如：

- `0xcc668`: `0xcabee` / `0x2ea1c`
- `0xcc708`: `0xcac6d` / `0x30398`
- `0xcc858`: `0xcad7d`（`continue`）/ `0x32eb0`

这是一段**候选静态指针对区域**，但当前脚本没有成功枚举，且若干名称是尾部合并字符串或普通日志文本；不能据此认定完整命令表已闭合，也不能认定一定不存在静态表。

声称 `FastbootCommandSetup` 字符串引用位于 `0x2f5b0` 等位置同样不成立：例如 `0x2f5b0` 的 ADRP+ADD 组合指向 `0xcba65`，不是 `FastbootCommandSetup` 的 `0xcb061`。应将相关注册逻辑标为 UNKNOWN。

### 3.4 构建流指纹与 RAM boot 诊断字符串

AI1 对两个派生 PE 重新计数：

- Hybrid：`china_compile` 43 个 NUL 分隔字符串，`c_per_F_compile` 0；
- stock：`c_per_F_compile` 43 个 NUL 分隔字符串，`china_compile` 0。

因此“不同构建路径指纹”有支持。但报告中 stock `c_per_F_compile ×3` 的计数有误，应修正为 43（按本轮采用的 NUL 分隔字符串计数口径）。

`Failed to load/authenticate boot image: %r`：Hybrid 1 处，stock 0 处。  
`Load Error`：Hybrid 1 处，stock 1 处。

所以“失败诊断前缀只在 Hybrid 载荷出现”成立；“Load Error 状态名仅工程构建有”不成立。更重要的是，某条错误文本只存在于一个 PE，**不等于已经证明该 PE 独有完整 RAM boot 路径或独有签名策略**。字符串可能属于错误日志、库函数或未被执行的分支。报告据此称同型号 retail ABL 失败案例“不能外推”过强；更准确结论是：对方使用的 retail ABL 与本机 Hybrid PE 构建指纹不同，因此其结果不能直接视作本机必然结果，但仍然是同平台风险样本，不能由字符串差异排除。

### 3.5 Stage B 最终定级

| 问题 | AI1 状态 |
|---|---|
| 当前 Hybrid PE 的 Fastboot 相关字符串存在 | PASS（仅存在性） |
| `getvar:secure` handler / 状态源 | UNKNOWN（原 xref 错配） |
| `getvar:unlocked` | PARTIAL（应答器局部地址可见，状态查询内部未闭合） |
| `download → CmdBoot → auth → EFI/跳转` | UNKNOWN / PARTIAL（目前没有完整调用链） |
| unlock 是否绕过 RAM boot image auth | UNKNOWN |
| `secure=yes` 的当前 ABL 具体行为 | UNKNOWN |
| Hybrid 与 stock 属不同构建流 | PASS（构建路径字符串差异） |
| RAM boot 专用认证/失败路径在 Hybrid 独有 | UNKNOWN（诊断字符串不足以证明） |

Agent 保留 `RAMBOOT_AUTH_BYPASS_BY_UNLOCKED=UNKNOWN` 是正确的。当前没有足够证据把它改为 PASS，也没有理由进行实机 RAM boot。

## 4. Stage C：vbmeta 解析 — PARTIAL；描述符类别解码错误

### 4.1 toolkit vbmeta 文件自身可独立解析

`inputs/toolkit_vbmeta.img`：

- 1,048,576 B；SHA-256 `af615d9fb0aebf99bb32f5328a9d90497a3ae0460dc6ffffb6e9bf077d636350`；
- `AVB0` @ 0；header 1.0；algorithm type 1（`RSA2048_SHA256`）；
- auth block 320 B；aux block 9,280 B；
- flags `0x00000000`；rollback index 0；rollback_index_location 2；
- header 中存在 256 B 签名字段与 520 B public-key blob。

这里的 `RSA2048_SHA256` 是头部算法字段，签名区和公钥 blob 存在；本轮没有在已知硬件信任根下完成密码学验签，故不要表述为“签名有效/硬件接受”。

### 4.2 14 个 tag=4 不是 property descriptors

这是本轮最严重的 Stage C 解析错误。

AOSP `avbtool.py` 明确定义：

- `AvbPropertyDescriptor.TAG = 0`；
- `AvbChainPartitionDescriptor.TAG = 4`，包含 `rollback_index_location`、分区名长度、公钥长度、flags、60 B 保留区、分区名和公钥。

参考：

- AOSP `avbtool.py`，Property TAG=0：<https://android.googlesource.com/platform/external/avb/+/23c8439bb647e483b80f9bac6974798a06a4ae5f/avbtool.py>
- AOSP `avbtool.py`，Chain Partition TAG=4：<https://android.googlesource.com/platform/external/avb/+/main/avbtool.py>

AI1 直接解析工具箱 vbmeta 的 descriptor 区 `[0x240, 0x2468)`，得到 **14 个 tag=4，0 个 tag=0**。它们是 Chain Partition Descriptor，不是包含 boot/ramdisk/dtbo digest 的 Property Descriptor。名称与 rollback location 实测为：

| 分区 | rollback_index_location | public key 长度 |
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

因此报告中“14 个 tag=4 PROPERTY 描述符”“boot/ramdisk/dtbo 摘要属性两版一致”等说法不成立，必须撤回。当前已打包的只有 toolkit vbmeta，因此不能比较第二份 r155 vbmeta 的 chain descriptors、公钥、rollback locations 或 SHA。

### 4.3 flags 位名的脚本映射颠倒

AOSP 定义：

- bit 0：`HASHTREE_DISABLED`；
- bit 1：`VERIFICATION_DISABLED`。

参考：AOSP `avb_vbmeta_image.h` 变更说明与 `fs_avb.cpp` 对应位检查：

- <https://android.googlesource.com/platform/external/avb/+/1297b7205f73b3cb037e95762a936a80cb1cc5fb%5E1..1297b7205f73b3cb037e95762a936a80cb1cc5fb/>
- <https://android.googlesource.com/platform/system/core/+/main/fs_mgr/libfs_avb/fs_avb.cpp>

随包 `vbmeta_scan2.py` 把 `flags & 1` 标为 verification_disabled，把 `flags & 2` 标为 hashtree_disabled，名称颠倒。对于本文件 `flags=0`，两位都未置位的结论仍然正确；但脚本必须修正位定义，不能用于非零 flags 文件。

### 4.4 r155 vbmeta 状态

主报告、manifest 声称 r155 vbmeta SHA 为 `e9b6e8ac…`、rb_loc=3；但 ZIP 没有该文件，也没有其可复现提取脚本输出。AI1 本轮不能独立复验该 SHA 或 rb_loc=3。

即便历史 r155 快照存在，也不能代替当前设备 live vbmeta 状态；当前 live vbmeta 仍 UNKNOWN。

**Stage C：PARTIAL。** 仅 toolkit 文件头部及其 chain descriptor 可独立复核；属性描述符与第二份 vbmeta 的比较无效/不可复核。

## 5. Stage D：15:51 模式切换日志

随包日志摘录时序清楚：

- 15:51:23.473：工具箱记录当前模式 ADB；
- 15:51:23.478：工具箱记录“重启到 Fastboot…”；
- 15:51:27.118：工具箱记录“已发送重启命令”；
- 15:51:28.639：设备断开；
- 15:51:37.607：工具箱记录 Fastboot 模式重新连接。

因此可以确认这次 Fastboot 会话前，MatePad11Toolkit 在 ADB 状态下发送了重启操作。日志**没有保留原始命令行/argv**，故只能说“工具箱发送了重启到 Fastboot 的命令”，不能将其写成已取证的精确命令 `adb reboot bootloader`。用户点击来源、工具箱事件触发来源也未由日志证明。该部分 Agent 的“工具箱发起，Agent 本身未调用重启”是比“用户手动按键进入”更符合当前日志的描述。

Stage D 时序判断：**PASS（工具箱记录的事件链）；调用来源/精确 argv UNKNOWN。**

## 6. 恢复资产结论

恢复资产清单只证明报告所列材料在工具箱目录中被登记，并非执行验证：

- Stock ABL 备份：存在且 hash 已确认；恢复写回未演练；
- EDL programmer / Firehose / Sahara 工具：报告称在册；没有成功 9008 / programmer / Firehose 会话；`UNVERIFIED / LAST RESORT`；
- TWRP：报告称曾刷入；启动及恢复能力未验证；
- HiSuite：只证明已安装；不能证明适用于当前 C00 / HOS4.3 恢复；
- stock boot / ramdisk 备份不受本轮影响，原有冻结 hash 继续有效。

恢复能力仍应为 **PARTIAL / NOT EXERCISED**。

## 7. 最终判定

| 阶段 | AI1 判定 | 是否关闭 |
|---|---|---|
| ZIP / 清单完整性 | PASS | 是 |
| Stage A Hybrid ABL 字节身份及 LZMA 提取 | PASS（含 PT_LOAD 数值勘误） | 是 |
| Stage B Fastboot 认证路径 | PARTIAL；secure/unlock/auth/boot 完整链 UNKNOWN | 否 |
| Stage C vbmeta | PARTIAL；tag4 分类错误，r155 文件缺失 | 否 |
| Stage D 模式切换日志 | 时序 PASS，精确 argv UNKNOWN | 是（证据范围内） |
| 一次性 `fastboot boot` 授权 | **NOT APPROVED / HOLD** | 否 |

### 当前最重要的确定事实

1. 当前 r155 ABL dump 的前 602,112 B 与 GhostLock `abl_unlock.img` 完全一致，后缀与 stock ABL 完全一致。
2. 它解出的 PE 载荷身份为 `a14e29...bb404`；stock ABL 解出不同大小、不同编译流的 PE。
3. Fastboot `secure` 值函数、`unlocked` 对 RAM boot 的影响、以及 CmdBoot 的认证/跳转链尚未被可靠闭合。
4. Toolkit vbmeta 的 14 个 descriptor 是 chained partition descriptors，不是 properties；r155 vbmeta 原件未随包提供。
5. 当前 Hybrid ABL 中出现一条 `Failed to load/authenticate boot image: %r` 消息，但仅凭字符串不能证明完整 RAM boot handler 或解锁绕过逻辑。

**结论：REV2 的 Stage A 很重要且已通过；Stage B/C 不能接受为函数级认证路径闭环。当前不应发放 `fastboot boot` 授权。**

— AI1 独立审核结束 —
