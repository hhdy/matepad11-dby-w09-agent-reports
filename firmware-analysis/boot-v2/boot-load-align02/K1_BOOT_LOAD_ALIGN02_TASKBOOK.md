# K1-BOOT-LOAD-ALIGN02 — PREP10 ARM64 Image / Hybrid ABL 实际分配对齐契约核验

- 签发：AI1
- 执行：WorkBuddy Agent（本机离线；通过已连接 GitHub 直接交付）
- 目标设备：Huawei MatePad 11 DBY-W09 / HWDBY / SM8250(Kona)，板级 VD
- ACK：`android17-6.18.33_r00`
- kernel source commit：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`
- source tree identity（patched tree）：`c56d93eafa35057d65176db6594d67d5144868a0`
- PREP10 Image SHA-256：`f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21`（44,820,992 B）
- Hybrid ABL PE SHA-256：`a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`
- 当前 boot 候选：`dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img`，SHA-256 `d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091`（46,563,215 B）
- 性质：只读源码、构建产物和 Hybrid ABL 静态核验；不连接设备、不执行 Fastboot/ADB、不写分区、不修改镜像。

## 0. 本轮只回答一个问题

**PREP10 的 ARM64 Image 被 Hybrid ABL 放置到 `ImageBuffer + 0x80000` 后，是否满足本次 ACK Image 的 2 MiB 对齐启动契约？如果满足，证据是什么；如果不满足或无法证明，具体缺少什么？**

本轮不重新做整套 ABL 反汇编，不重新解析 DTBO，不重编内核，不生成新 boot 候选。必须使用下文已冻结的事实和公式；不得把“96 MiB 空间足够”当成“加载地址对齐正确”。

## 1. 冻结输入和既有证据

### 1.1 Hybrid ABL 已确认事实

上一轮 `K1_BOOT_LOAD_MAP01` 已确认：

- AArch64 raw Image 分支的目的地址为 `KernelLoadAddress = ImageBuffer + 0x80000`，证据位于 Hybrid PE RVA/VA `0x374A8–0x374C8`，核心选择指令在 `0x374AC`。
- 分支判断读取待加载 kernel payload 的 `+0x38`，与 ARM64 Image magic `0x644D5241` 比较：相等走 64-bit/raw Image 分支；不相等走另一分支。证据 `0x37368–0x37380`。
- 另一分支的偏移为 `ImageBuffer + 0x8000`。gzip kernel 后续由 inflate 路径写入该目的地址（具体是否被当前调用路径采用，仍需根据原始字节和控制流确认）。
- ABL 不以 boot header 中的 `kernel_addr` / `ramdisk_addr` / `dtb_addr` 作为最终 64-bit kernel 放置地址。
- PE 文件偏移与 VA/RVA 的映射关系已在上一轮验证；本轮必须沿用 RVA/VA，不得将 file offset 冒充 VA。
- 原始证据目录：`firmware-analysis/boot-v2/boot-load-map01/`，特别是 `hybrid_abl_load_path.md`、`memory_map.md`、`evidence/dis_bootlinux_full.txt`、`evidence/stage_b1_output.txt`、`evidence/dis_loadauth.txt`、`evidence/dis_loadramdisk.txt`。

### 1.2 PREP10 ACK Image 头部

上一轮冻结解析值：

```text
Image magic       = 0x644D5241
text_offset       = 0x0000000000000000
image_size        = 45,547,520 B
flags             = 0x000000000000000A
flags bit 1..2    = 01b -> 4 KiB page size
flags bit 3       = 1 -> PHYS_BASE / physical placement may be anywhere in physical RAM
ABL raw dest      = ImageBuffer + 0x80000
```

注意：flags bit 3 允许 2 MiB aligned base 位于可用 RAM 中的任意位置，**不取消 Image 必须相对于 2 MiB aligned base 按 text_offset 放置的要求**。

### 1.3 必须核对的 Linux ARM64 启动规范

固定使用 ACK 目标 commit 的：
- `Documentation/arch/arm64/booting.rst`
- `arch/arm64/kernel/head.S`
- 以及相关头部生成定义 / Makefile / linker 变量（仅为解释 `text_offset`、`image_size`、`flags` 来源所需）。

对照官方 ARM64 boot protocol：Image 必须放置在一个 2 MiB 对齐物理基址加 `text_offset` 的位置；从 Image 起始位置起，至少 `image_size` 字节需可供 kernel 使用。flags bit 3 只放宽 aligned base 在 RAM 中的位置，不放宽 2 MiB 对齐本身。

引用文档：
- https://kernel.org/doc/html/v6.14/arch/arm64/booting.html
- https://android.googlesource.com/kernel/common/+/1798561befd8be1e52feb54f850efcab5a595f43/Documentation/arch/arm64/booting.rst

## 2. 一个必须先纠正的历史推断

上一轮 AI1 审核中曾写过“stock 实机能启动，反证 ImageBuffer 基址 `≡ 0 (mod 2 MiB)`”。**这条推断没有被证明，不能沿用。**

原因：Hybrid ABL 的分支偏移取决于待加载 payload 的 `+0x38` magic 检测。stock boot 内核载荷为 gzip，而解压后的 stock ARM64 Image 的 `text_offset=0x80000`。必须先读取 stock gzip payload 的实际 `+0x38`，确认是否命中 ARM64 magic；如果不命中，ABL 使用的目的偏移可能是 `+0x8000`，而不是 `+0x80000`。

如果确认 stock 实际目的偏移为 `+0x8000`，则 stock 启动协议所要求的 ImageBuffer 余数是：

```text
(ImageBuffer + 0x8000 - 0x80000) mod 0x200000 = 0
ImageBuffer mod 0x200000 = 0x78000
```

对 PREP10 raw Image：

```text
(ImageBuffer + 0x80000 - 0x0) mod 0x200000 = 0
ImageBuffer mod 0x200000 = 0x180000
```

以上是待用真实 payload 分支和 ARM64 规范验证的算式，不得把推导值伪装成实测的 ImageBuffer 物理地址。

如果 stock payload 实际命中另一个分支，则按真实分支重算并解释。**本节的目的就是避免把 stock 能启动错误地推导成 ImageBuffer 为 2 MiB 对齐。**

## 3. 阶段 A — 输入身份复核

核对本地已有材料：
1. Hybrid ABL PE 的 SHA-256 与本任务冻结值一致。
2. PREP10 kernel Image SHA-256、大小与冻结值一致。
3. stock live boot SHA-256 与既有记录一致。
4. stock boot 中 kernel compressed payload 的偏移、长度和压缩 magic；解压出的 ARM64 Image SHA（若已有）与 `text_offset/image_size/flags` 头部值。
5. ACK source commit / source tree identity 与本任务一致。

身份不一致的输入不得继续用于推导；不得联网下载“相似版本”或替换 ABL。

## 4. 阶段 B — 精确核验 Hybrid ABL 的 ImageBuffer 分配

只分析上一轮定位的 `LoadImageAndAuth` / Fastboot boot 数据路径中真正分配和持有 `ImageBuffer` 的 EFI AllocatePages 调用。需要从指令级证据回答：

1. 逐个列出与普通分区启动、Fastboot RAM boot 对应的 ImageBuffer 申请路径；若同一路径则用 caller/xref 证明，不能只因函数相似就合并。
2. 对每个 `gBS->AllocatePages` 调用，恢复到调用点的 AArch64 ABI 参数：
   - `AllocateType`（AllocateAnyPages / AllocateMaxAddress / AllocateAddress）；
   - `MemoryType`；
   - `Pages`；
   - `Memory` 输入/输出指针及调用前初始化值；
   - 调用后返回的物理基址如何进入 ImageBuffer 字段。
3. 检查调用前后是否有超分配、按 2 MiB 对齐的地址向上/向下取整、二次分配、搬移、偏移修正、地址掩码或显式 `& ~0x1fffff` / `+0x180000` 等逻辑。
4. 检查 Fastboot download buffer 是谁分配、容量是多少，是否与正常分区 ImageBuffer 使用同一分配入口；区分“下载接收缓冲”和“解压/最终 kernel 目的区”。
5. 如果调用方仅请求 EFI `AllocatePages`，且没有强制 2 MiB 对齐或重定位，那么只能证明至少页对齐（4 KiB），**不能**声称得到 2 MiB 对齐或某个固定的 `mod 2 MiB` 余数。
6. UEFI allocator 的实际物理返回地址如无法从 ABL 二进制静态确定，明确标为 runtime-dependent / UNKNOWN；不要以 stock 正常启动作循环论证。
7. 每个关键调用提供：Hybrid PE hash、VA/RVA、file offset（分列）、前后至少 8–16 条反汇编指令、调用者、参数恢复过程和置信度。

必须区分：
- `ImageBuffer` 的虚拟指针；
- EFI AllocatePages 返回的物理地址；
- kernel 最终物理加载地址；
- UEFI 中间 staging buffer；
不能混用它们。

## 5. 阶段 C — 核对 ACK 6.18.33 的 Image 头部来源与 head.S

在精确 source commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9` 上执行只读核对：

1. 读取 `arch/arm64/kernel/head.S`，定位 Image header 的 `text_offset`、`image_size`、`flags` 生成符号和入口 `primary_entry`。
2. 追踪 `_kernel_offset_le`、`_kernel_size_le`、`_kernel_flags_le` 的定义和值来源；说明本构建为什么生成 `text_offset=0`、`flags=0xA`。
3. 检查目标 build config 中所有可能影响 Image 头与位置契约的配置，如 ARM64 page size、relocatable/physical placement、随机 text offset（若该分支存在）及对应 Makefile/头文件定义。不得只凭配置名猜测，要展示 source 定义。
4. 对照冻结 Image 的原始 64-byte header，独立解析并与构建源码/构建记录核对。
5. 解释 `head.S` 实际如何使用物理入口地址、`__PHYS_OFFSET` / `TEXT_OFFSET`（如适用）、relocation/KASLR 前提；严格区分：
   - boot protocol 的 mandatory placement requirement；
   - `head.S` 是否显式执行 runtime alignment assertion；
   - 即使无显式 assert，错位装载是否仍违反启动契约。
6. 不得声称“head.S 不检查对齐，所以错位也能启动”；也不得声称“head.S 必定 panic”而没有直接分支证据。

交付必须包含精确源码 commit 链接和逐段引用（文件路径 + 行号/源码片段），而不是引用 master/main。

## 6. 阶段 D — 建立可复核的对齐算式

确认实际分支后，对 stock 与 PREP10 分别列：

| 项目 | stock | PREP10 |
|---|---:|---:|
| payload byte +0x38 | 实测值 | 实测值 |
| ABL branch selected | +0x8000 / +0x80000 | +0x8000 / +0x80000 |
| decompressed/raw Image text_offset | 实测 | 0 |
| image_size | 实测 | 45,547,520 |
| required ImageBuffer mod 2 MiB | 推导值 | 推导值 |
| AllocatePages alignment guarantee | 证据 | 证据 |
| runtime ImageBuffer physical address known? | YES/NO | YES/NO |
| kernel entry address aligned? | PASS/FAIL/UNKNOWN | PASS/FAIL/UNKNOWN |

公式统一使用：

```text
(ImageBuffer_phys + ABL_kernel_offset - text_offset) mod 0x200000 = 0
```

其中 `ABL_kernel_offset` 必须来自对应 payload 在 Hybrid ABL 中实际选择的分支。所有输入必须有来源。若 `ImageBuffer_phys` 只知 4 KiB 对齐而不知道其 2 MiB 余数，最终对齐判定必须是 UNKNOWN，不得写 PASS。

同时核对至少 `image_size` 字节的内核内存窗口是否可用。该项沿用 load-map 现有数值即可，不扩展重做整个 memory map。

## 7. 阶段 E — 输出工程结论与可行修正方向（不制作镜像）

结论必须回答：

1. 当前 PREP10 raw Image 在当前 Hybrid ABL 固定 `+0x80000` 放置路径下：
   - ALIGNMENT = PASS / FAIL / UNKNOWN；
   - 如果 FAIL，说明是必然错位还是取决于动态 allocator；
   - 如果 UNKNOWN，准确指出缺少的 runtime 事实。
2. 仅凭当前 stock 能启动，是否能证明 PREP10 能满足对齐？给出严格逻辑。
3. 在不改 ABL/DTBO/separate ramdisk 的前提下，理论上有哪些源码层修正方向值得后续评估：
   - 调整 ACK ARM64 Image 的 `text_offset` / 构建配置；
   - 生成与现有 ABL gzip 分支兼容的 Image.gz；
   - 若可验证，调整 bootloader 可接受的载荷形式/offset。
   对每个方向只说明依据、预期影响和还需验证的条件；**不得实际改配置、重新编译、修改 64-byte Image header、重打包或生成新候选。**
4. 明确推荐下一步的唯一最小行动；如果无法得到静态保证，说明需要哪一种最小的设备侧观测，先交用户批准，不得自行执行。

## 8. 交付与 GitHub 规则

Agent 已接入 GitHub。必须直接提交到仓库，不得再以 gh 未安装退回 ZIP-only。

仓库：`hhdy/matepad11-dby-w09-agent-reports`

目录：`firmware-analysis/boot-v2/boot-load-align02/`

至少提交：
- `K1_BOOT_LOAD_ALIGN02_REPORT.md`
- `evidence_matrix.csv`
- `stock_prep10_alignment_math.csv`
- `allocation_callsite_evidence.md`
- `ack_head_image_header_source.md`
- `SHA256SUMS.txt`
- 本轮实际用到的解析脚本/源码片段（只提交脱敏分析工具和必要摘录，不公开原始完整 ABL、boot、ramdisk 或私有固件）。

提交要求：
1. 在本分支直接新增文件，不覆盖历史报告。
2. 所有关键源文件和分析脚本计算 SHA-256。
3. GitHub 提交后必须重新从 GitHub fetch/read 回所有报告文件，核对 commit SHA、文件 blob SHA 与内容。
4. 不上传 stock 原始分区 dump、完整 ABL、用户数据或设备敏感信息。
5. 最终报告要有清楚的 PASS/FAIL/UNKNOWN；任何未能闭环的运行时地址必须保留 UNKNOWN。

## 9. 严格禁止

- 不连接平板、不查询设备状态、不切换模式。
- 不运行 ADB/Fastboot/OEM 命令；不再尝试 `fastboot boot`。
- 不执行 `fastboot flash`、`dd`、分区写入或读回。
- 不重启、不恢复、不执行 EDL/HiSuite/TWRP/bootctl。
- 不修改 ABL、vbmeta、boot、ramdisk、DTBO、DTB、kernel Image。
- 不改 kernel config、不重新编译、不重新打包、不生成候选镜像。
- 不执行从固件提取的任何二进制。
- 不扩展为第二轮全量 ABL 反汇编；只复核分配调用、已有 loader 分支和 ACK Image header contract。

## 10. 停止条件

- 若 allocator 的 2 MiB 余数能从指令级约束严格证明，完成算式并停止。
- 若 AllocatePages 只保证 4 KiB、实际返回地址依赖 UEFI runtime，则如实标 UNKNOWN，明确不能批准写入。
- 若发现上一轮 AI1 “stock 反证 ImageBuffer mod 2 MiB = 0”的推断不成立，必须在报告里明确更正，不要重复引用。
- 本任务不构成启动测试或分区写入授权。所有设备操作均需用户单独明确授权。

**目标是解决 PREP10 最后一个 boot-write gate；不允许通过猜测对齐地址来推进刷写。**
