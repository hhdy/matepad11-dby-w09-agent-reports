# K1_BOOT_LOAD_ALIGN02 — PREP10 Image / Hybrid ABL 对齐契约核验报告

- 日期：2026-11-28；性质：只读静态核验（未连接设备、未写入、未改镜像、未重编译）
- 输入身份：全部匹配任务书冻结值（stage A 输出：stock boot `7a95c897…`、PREP10 boot `d1d76c21…`、ABL PE `a14e29da…`、PREP10 Image `f89a2839…`）

## 0. 结论速览

| 项目 | 结果 |
|---|---|
| **PREP10 ALIGNMENT** | **UNKNOWN（运行时相关）— 且在"与 stock 相同分配"的前提下应为 FAIL（见 §3 算式）** |
| stock 分支 | **+0x80000**（gz 路径 CFG 证据，§1） |
| PREP10 分支 | **+0x80000**（raw Image magic@+0x38 实测命中） |
| AllocatePages 对齐保证 | 仅 4 KiB（EFI 页粒度）；加载路径中**无任何 2 MiB 掩码/重对齐逻辑**；ImageBuffer 物理地址 = 运行时相关，静态不可知 |
| head.S 运行时对齐断言 | **无**（`MIN_KIMG_ALIGN` 在 head.S 中出现 0 次）——错位装载违反的是 boot 协议义务，非内核显式 assert |
| 历史推断更正 | LOAD_MAP01 轮"stock 反证 ImageBuffer≡0 (mod 2MiB)"：分支前提（+0x80000）本轮被 CFG 证据**支持**，但该结论只能作为**运行时经验事实**（stock 每次启动成功 ⟹ 该实例 buf≡0），**不是分配器保证**；且按 §3 算式它反而意味着 PREP10 FAIL，不构成对 PREP10 的支持。AI1 §2 提出的备选假设（stock 走 +0x8000 → buf≡0x78000）被本轮 CFG 证据**否定** |

## 1. 阶段 B 补充：分支选择最终版（gz 路径 CFG 证据）

本轮新增的关键控制流证据（dis 0x371F8–0x37390 + flag 存储全图）：

- flag（栈槽 `[x20-0x10]`）存储点共 3 处：`0x37200`（清零）、`0x37380`（=1）、`0x37894/98`（=1）；读取点：csel@0x374A8、entry 判定@0x38708。
- **gz 载荷不经过 0x37368 的 magic 检查**：0x3720C `bl 0x39D60`（gzip 检测）命中后 `0x37214→0x3721C b 0x37384` 直接跳过 strncmp/magic 块 → **flag 保持 0x37200 清零后的 0**。
- 实测字节：stock 压缩载荷 +0x38 = `0x00C85788`（≠magic，若被检查会置 flag=1）；stock 解压后 +0x38 = `0x644D5241` ✓（0x37834 的 post-copy 校验在 x26=kload 解压镜像上命中 → 不触发 0x37894 的 flag=1）。
- PREP10 raw 载荷 +0x38 = `0x644D5241` ✓（0x37368 命中 → flag 保持 0）。
- 解压目的地址 = `[x20-0x70]` = kload（0x3775C 调用 0x39AB0 的 x2 实参，dump line 727）——**gz 与 raw 最终同地址，gz 路径不改变放置偏移**。

∴ **stock 与 PREP10 都落在 +0x80000 分支**。任务书 §2 的 "+0x8000 备选算式"（buf≡0x78000）不成立。

## 2. 阶段 B：ImageBuffer 分配调用点

32 个 `gBS->AllocatePages(+0x28)` 站点全列于 `evidence/align02_alloc_sites.txt`。代表性调用点（0x30858 一带，普通分区启动路径）：

```aarch64
0x030858  ldr  x8, [x8, #0x28]     ; x8=gBS(0x118FE8) → AllocatePages
0x03085C  adrp x0, 0xcc000 ; add x0, x0, #0x52e   ; x0=UTF-16 "secdata"（华为分区标签）
0x030864  mov  x1, x21 ; mov x2, x22 ; mov x3, xzr
0x030870  blr  x8
```

- 调用形态为**华为包装层**（首参为 UTF-16 分区名标签，如 "secdata"；0x30838 分支另有 `w2=7`（EfiBootServicesData）的兄弟调用）——包装层内部最终走 EFI 页分配器；**两条路径（分区启动 / fastboot 下载缓冲）均未发现 `& ~0x1fffff` 掩码、+0x180000 修正、二次对齐分配或搬移**（全 .text `0x8000/0x80000` 唯一对已证；`0x1fffff` 类掩码未出现在 loader 路径）。
- fastboot 下载缓冲调用点 0x55944 一带为 `w0=0xC5` 的包装调用（`evidence/align02_dis_alloc_fastboot.txt`）——与分区路径共用同一分配入口族（PARTIAL：包装层内部逐级闭合未完成，不影响对齐结论）。
- **EFI AllocatePages 契约 = 4 KiB 页粒度；返回物理地址的 2 MiB 余数是运行时事实** → 静态只能证"至少 4 KiB 对齐"。

## 3. 阶段 D：对齐算式

公式：`(ImageBuffer_phys + 0x80000 − text_offset) mod 0x200000 = 0`

| 项目 | stock | PREP10 |
|---|---|---|
| payload +0x38 实测 | `0x00C85788`（压缩态，不被检查）；解压态 `0x644D5241` | `0x644D5241` |
| ABL 分支 | +0x80000（§1 CFG） | +0x80000 |
| text_offset | 0x80000（解压实测） | 0（Image 头实测） |
| image_size | 70,504,448 | 45,547,520 |
| required ImageBuffer mod 2MiB | **0x00000** | **0x180000** |
| AllocatePages 保证 | 4 KiB（§2） | 4 KiB |
| runtime ImageBuffer 物理地址已知？ | NO（仅经验：stock 每次成功 ⟹ 该实例 ≡0） | NO |
| kernel entry 对齐 | 经验 PASS（stock 实机） | **UNKNOWN；若 buf≡0 则 FAIL（0x80000 mod 2MiB ≠ 0）** |

**逻辑**：stock 与 PREP10 要求的 ImageBuffer 余数**互斥**（0 vs 0x180000）。同一分配入口在 stock 实例上经验性给出 ≡0；若 PREP10 分区启动得到相同分配（同路径、同尺寸分配 96 MiB 分区缓冲，高度相似但无静态保证），则 PREP10 entry ≡ 0x80000 (mod 2MiB)，**违反其 Image 契约 → FAIL**。由于静态无法证明运行时余数，最终判定记 **UNKNOWN（runtime-dependent），不能批准写入**；工作假设为 FAIL。

## 4. 阶段 C：ACK 源码证据（commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` = a31-apply HEAD，git 实测）

- `arch/arm64/kernel/head.S` L59：`.quad 0 // Image load offset from start of RAM` —— **text_offset 在本树硬编码 0**（Makefile 无 TEXT_OFFSET 符号，grep 0 命中）。
- `arch/arm64/kernel/image.h` L45-57：`__HEAD_FLAGS = __HEAD_FLAG(BE)|__HEAD_FLAG(PAGE_SIZE)|__HEAD_FLAG(PHYS_BASE)`；`__HEAD_FLAG_PAGE_SIZE = (PAGE_SHIFT-10)/2`（4K→01b）；**`__HEAD_FLAG_PHYS_BASE = 1` 无条件定义** → flags ≡ 0b1010 = **0xA**，与冻结 Image 头实测一致（`_kernel_size_le = _end - _text` = 45,547,520 ✓）。
- head.S 中 `MIN_KIMG_ALIGN` 出现 **0 次** → 无显式运行时对齐 assert；`primary_entry`（L85）经 x0 接收 FDT（注释 L83 明示）。boot 协议（booting.rst）要求"2 MiB 对齐基址 + text_offset"——这是 bootloader 义务；错位装载的后果无法由源码静态断言（既非必然 panic，也非可容忍）。
- 详细摘录见 `ack_head_image_header_source.md`。

## 5. 阶段 E：工程结论与修正方向（不制作镜像）

1. PREP10 在当前 ABL 固定 `+0x80000` 路径下 **ALIGNMENT = UNKNOWN（运行时相关）；在"与 stock 相同分配"假设下为 FAIL**——必然错位与否取决于 UEFI 分配器当次返回的 2 MiB 余数，静态不可证。
2. stock 能启动**不能**证明 PREP10 满足对齐：两者所需余数互斥（§3），stock 成功反而支持"该分配给出 ≡0"从而 **反对** PREP10。
3. 理论修正方向（仅评估，不执行）：
   - **源码方向 A（首选评估）**：修改 `arch/arm64/kernel/head.S` L59 的硬编码 `.quad 0` 为 `.quad 0x80000`（即恢复 TEXT_OFFSET=0x80000 放置约定；需同步核对 entry 路径对 `__PHYS_OFFSET` 的推导与 relocations 生成）。效果：PREP10 所需余数变为 ≡0，与 stock 经验一致。代价：新 Image（新 SHA）、需重新走构建冻结流程。
   - **方向 B**：改用 Image.gz——**无效**：gz 与 raw 解压/拷贝目的地址同为 `+0x80000`（§1），不改变对齐。
   - **方向 C**：改 bootloader 侧偏移/重定位——违反"不改 ABL"前提，仅记录为理论存在。
4. 唯一最小下一步建议：由 AI1 决策方向 A（源码层恢复 text_offset=0x80000 后重建候选）或先做最小设备侧观测（需要用户单独授权，本轮不执行）。静态路径上 **BOOT_WRITE_GATE 继续 UNKNOWN/BLOCKED**。

## 6. 交付物

`K1_BOOT_LOAD_ALIGN02_REPORT.md`（本文件）、`evidence_matrix.csv`、`stock_prep10_alignment_math.csv`、`allocation_callsite_evidence.md`、`ack_head_image_header_source.md`、`SHA256SUMS.txt`、`scripts/`（3 个分析脚本）。上传至 `firmware-analysis/boot-v2/boot-load-align02/`；不公开原始 ABL/boot/ramdisk。
