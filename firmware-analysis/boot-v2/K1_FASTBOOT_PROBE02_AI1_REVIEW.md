# K1-FASTBOOT-PROBE02 — AI1 独立验收报告

**审核日期：** 2026-11-28  
**审核对象：** `K1_FASTBOOT_PROBE02_REPORT.zip`  
**ZIP SHA-256：** `c5be8faa036525e7c6790d9f6d7b32ff6ffe1a5e4c18e072839cf634808695aa`  
**AI1 结论：** **PROBE02 交付包及只读采集结果接受；`fastboot boot` 仍为 NO-GO，不能据此发放启动授权。**

## 1. ZIP 与内部校验

- ZIP 大小：5,658 B；SHA-256 与 Agent 声明精确一致。
- ZIP CRC / `testzip()`：通过。
- 共 5 个条目，无额外缓存文件。
- `SHA256SUMS.txt` 覆盖的 4 个交付文件 SHA-256 全部独立复算通过。
- 报告、设备识别、getvar 原始输出、环境记录可正常读取。

交付包完整性：**PASS**。

## 2. 设备只读事实

| 项目 | 原始记录 | AI1 判定 |
|---|---|---|
| Fastboot 设备识别 | `fastboot devices -l` 成功 | PASS |
| Android ADB 交叉检查 | 空列表 | 与 bootloader Fastboot 状态一致 |
| `product` | `kona` | 原样接受；不是 DBY-W09 型号标识 |
| `unlocked` | `yes` | bootloader 层解锁状态直接证据 |
| `secure` | `yes` | **重要安全门禁，不能淡化为熔丝备注** |
| `version` | `GetVar Variable Not found` | 不支持 / UNKNOWN |
| `version-bootloader` | 空值 | 版本字符串 UNKNOWN；不应表述为“已确认变量存在” |
| `max-download-size` | `805306368`（768 MiB） | 下载上限大于候选体积，只能说明传输尺寸有余量 |
| `is-userspace` | `no` | PASS，当前是 bootloader Fastboot，不是 fastbootd |
| `slot-count/current-slot/has-slot:boot` | 均不支持 | 不能用这三个变量单独证明 A-only |
| `partition-size:boot` | `0x6000000` = 100,663,296 B | 与 PREP12-N 先前分区清单一致 |
| `partition-type:boot` | `raw` | 原样记录 |

设备身份方面，报告声称 Fastboot 序列号与此前 ADB 识别的 DBY-W09/HWDBY 是同一台设备。由于 ZIP 内两轮序列号均已打码，AI1 接受 Agent 的现场交叉核对声明，但无法仅凭本 ZIP 独立重做序列号逐字符比较。后续建议使用相同的本地 salted hash 作为稳定匿名标识，不要公开完整序列号。

## 3. 关键修正：`secure: yes` 是潜在启动签名阻断项

Agent 报告将 `secure: yes` 备注为“安全熔丝机型，不做延伸解释”。这项解释不准确，且漏掉了 Fastboot 协议定义中最重要的含义。

AOSP Fastboot 规范对客户端变量 `secure` 的定义是：

> If the value is "yes", this is a secure bootloader requiring a signature before it will install or boot images.

即 `secure=yes` 表示该 bootloader 要求镜像在安装或启动前通过签名要求。AOSP Fastboot 0.4 协议还记录了旧式 `verify` 命令：secure bootloader 需要先验证下载数据的数字签名，否则 `flash` 和 `boot` 会被忽略。

参考：
- 当前 AOSP Fastboot README：  
  https://android.googlesource.com/platform/system/core/+/main/fastboot/README.md  
  见 Client Variables 中 `secure` 定义。
- AOSP Fastboot 0.4 protocol：  
  https://android.googlesource.com/platform/system/core/+/a057057/fastboot/fastboot_protocol.txt  
  见 `verify:%08x` 命令说明。

**必须保持技术边界：**
- `secure=yes` 不等于我们已经证明当前华为 ABL 必然拒绝这份镜像；
- `unlocked=yes` 也不能在没有华为 ABL 代码路径/实测依据时，自动解释为绕过 `secure` 签名门禁；
- 因此 `secure=yes` 是一个实质性 UNKNOWN / potential blocker，必须在授权 `fastboot boot` 前弄清楚；
- 当前交付中没有提供与候选镜像匹配的 Fastboot `verify` 签名材料，也没有证明 Huawei ABL 在 unlocked 状态如何处理该字段。

这项发现进一步加强了“不应立即尝试 RAM boot”的结论。

## 4. 哪些数据不能被过度解释

1. **`max-download-size=768 MiB`**：比候选镜像 46.56 MB 大，只支持“传输大小没有超过报告的 Fastboot 下载上限”。它不证明 ABL 接受 `boot` 命令、不证明镜像签名通过、不证明内核能启动。
2. **`partition-size:boot=96 MiB`**：这是 boot 分区容量信息。对 `fastboot boot` 的 RAM 启动接受性没有直接证明力；不能把它当成 RAM boot 容量或兼容性证据。
3. **slot 变量不支持**：`slot-count/current-slot/has-slot:boot` 返回 not found，并不等同于直接确认 A-only。A-only 结论仍来自此前 PREP12-N 分区目录未发现 `_a/_b` 后缀。
4. **`version-bootloader` 空值**：原始输出是 `version-bootloader:` 后无内容。应报告“值为空 / 版本字符串不可用”，不能确定版本号，也不能与同型号失败案例做版本匹配。AOSP 文件还指出旧设备对未知变量可能返回空的 OKAY，因此不要将空值表述为变量已被有效实现。
5. **`product=kona`**：它不是 DBY-W09 型号字符串。应与此前 ADB 识别及稳定设备匿名标识结合判断；不可仅凭 `kona` 反推产品 SKU。

## 5. 与同型号 RAM boot 反例合并后的门禁

此前已找到 DBY-W09 / SM8250 同型号公开记录：解锁设备执行 `fastboot boot` 时发生 `Failed to load/authenticate boot image: Load Error`；另一个同机型移植项目也记录 RAM boot 被拒绝。它们不是当前 C00 / HOS 4.3.0.196 个体的同一 ABL 版本，所以不能断言当前设备必然失败；但是与本轮 `secure=yes`、bootloader 版本字符串缺失结合后，风险不能判为低。

参考：
- https://blog.kinn-kinn.com/blog/su-wo-kudasai-matepad11-root
- https://github.com/svesnav/linux-dby-w09

此外，启动可观测性仍未解决：Framebuffer K1 为 BLOCKED，UART12 earlycon 为 HOLD。即使 ABL 接受镜像，也可能无法通过屏幕或 UART 得到足以判断启动阶段的输出。

## 6. 最终门禁结论

| 门禁条件 | 结果 |
|---|---|
| 交付包完整性 | PASS |
| Fastboot 设备识别 | PASS |
| 当前为 bootloader Fastboot | PASS (`is-userspace=no`) |
| bootloader 解锁状态 | PASS (`unlocked=yes`) |
| 候选体积不超过 max-download-size | PASS（仅传输上限） |
| boot 分区尺寸一致 | PASS（仅分区容量事实） |
| 当前 ABL/bootloader 版本 | UNKNOWN |
| `secure=yes` 对本机 ABL 的具体行为 | UNKNOWN / POTENTIAL BLOCKER |
| Huawei ABL 是否接受 `fastboot boot` | UNKNOWN；同型号有失败反例 |
| K1 早期输出通道 | NOT READY（Framebuffer BLOCKED / UART HOLD） |
| 原厂完整恢复包与当前版本恢复演练 | PARTIAL / NOT EXERCISED |

**结论：`K1-FASTBOOT-PROBE02 = ACCEPTED / CLOSED`；`fastboot boot` = `NO-GO FOR IMMEDIATE AUTHORIZATION`。**

这不是认定当前设备一定拒绝 RAM boot，而是目前有实际安全门禁未知、同型号失败反例、bootloader 版本缺失和早期可观测性缺口。不能把 `unlocked=yes`、`max-download-size` 足够或 boot 分区容量一致合并成 RAM boot 已可执行的证明。

## 7. 唯一建议的下一项工作：窄范围 ABL Fastboot 认证路径审计

不再发起另一轮 getvar，不再扫描 XBL/ABL 的无关子系统，不进行任何设备操作。

只对此前已冻结且哈希为  
`a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`  
的原始 ABL PE 做一个有界离线审计，回答：

1. ABL 的 Fastboot `boot` 命令处理路径在哪里？
2. `getvar:secure` 的返回值来自哪个状态/变量？
3. `unlocked` 状态是否会绕过 `secure` 对下载镜像的签名/认证要求？
4. 是否存在 Fastboot 下载后必须执行的签名验证/认证调用，使用何种签名数据和信任根？
5. `fastboot boot` 与 `flash boot` 是否走不同认证路径？同型号 RAM boot 被拒绝是否能由该路径解释？

要求：
- 仅使用上述精确哈希的 ABL；哈希不匹配或原始文件缺失立即停止。
- 用函数级反汇编、交叉引用和控制流证据；字符串存在/缺失不作为最终结论。
- 输出 PASS / FAIL / UNKNOWN，并引用具体函数、地址、调用链及证据强度。
- 不运行任何 Fastboot 命令，不连接设备、不重启、不签名、不刷写、不改镜像。
- 若静态控制流无法证明 unlocked 状态如何作用于 secure gate，明确报告 UNKNOWN，不推测。

只有当认证路径能证明候选镜像在当前状态下可能被 RAM boot 接受，且屏幕/UART 至少有一个可用的启动结果判据后，才重新讨论一次性 `fastboot boot` 授权。

— AI1 独立审核结束 —
