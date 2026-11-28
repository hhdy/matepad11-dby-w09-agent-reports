# K1_BOOT_LOAD_MAP01 — Hybrid ABL 实际 Kernel/DTB/Ramdisk 内存加载布局审计报告

- 日期：2026-11-28
- 性质：只读静态分析（Hybrid ABL PE + stock boot + PREP10 + separate ramdisk）；**未连接设备、未写入、未运行任何固件二进制**
- 分析对象：Hybrid AArch64 ABL PE `a14e29da…dbb404`（2,597,064 B，china_compile 流水线）；PE32+ @0xF10，ImageBase=0，`.text` VA==file offset（已验证恒等映射）

## 0. 结论速览

| 判定字段 | 值 |
|---|---|
| ABL_BOOT_V2_PARSER | **CONFIRMED**（解析 +8 kernel_size / +0x10 ramdisk_size / +0x18 second_size / +0x24 page_size / +0x28 header_version≤2；**+0xC kernel_addr、+0x14 ramdisk_addr、+1652 dtb_addr 不被读取为加载地址**） |
| ABL_KERNEL_DESTINATION | **CONFIRMED** = `ImageBuffer + 0x80000`（64 位路径，csel@0x374AC，全 .text 唯一）；32 位路径 = `ImageBuffer + 0x8000` |
| ABL_KERNEL_RELOCATION | **ABSENT**（raw Image 经 gBS->CopyMem 原样拷贝；gz 经 inflate 解压至同一地址；ABL 不解析 ARM64 Image header 的 text_offset/image_size 字段） |
| ABL_DTB_DESTINATION | **CONFIRMED** = `RamdiskLoadAddress - 4KiB - 2MiB`（0x374FC–0x37508），base DTB 复制到该地址（CopyMem@0x381BC），ufdt overlay 后最终 FDT 指针以 x0 传入 kernel |
| ABL_SEPARATE_RAMDISK_PATH | **PARTIAL**（LoadRamdisk@0x3969C + move_ramdisk_to_img_addr + `linux,initrd-start/end` FDT fixup@0x3D9D4 函数簇确认存在；partition 读取的完整调用链未逐级闭合） |
| EMBEDDED_RAMDISK_USED | **NO**（initrd = separate ramdisk 分区内容，PREP04 字节级证据 + LoadRamdisk 路径；boot 内嵌 ramdisk 未用作 initrd） |
| KERNEL_DTB_OVERLAP | **NONE**（分区启动，stock 与 PREP10 皆无） |
| KERNEL_RAMDISK_OVERLAP | **NONE**（分区启动）；**PRESENT（`fastboot boot` + 46,563,215 B 文件）** |
| PREP10_KERNEL_SIZE_LIMIT | **PASS**（44.8 MB raw < stock gz 解压后 57.4 MB 先例；容量检查 0x5BD6000 余量） |
| PREP10_LOAD_LAYOUT | **SAFE（boot 分区写入路径）**；`fastboot boot` 原文件路径 = staging 重叠（见 §4） |
| FINAL_RESULT | **LOAD_MAP_CONFIRMED_SAFE（分区启动）** + 2 项新发现（§4、§5），均交 AI1 决策 |

## 1. 输入身份（全部匹配任务书冻结值）

| 文件 | SHA-256 | 大小 |
|---|---|---|
| R155 abl.img | `b39de91b…8460011` | 4,194,304 |
| Hybrid ABL PE | `a14e29da…dbb404` | 2,597,064 |
| stock ABL PE | `44cda9af…9176` | 2,531,528 |
| stock boot | `7a95c897…39d24a8` | 100,663,296 |
| PREP10 boot | `d1d76c21…cc091` | 46,563,215 |
| PREP10 kernel (boot 内嵌载荷) | `f89a2839…bad21` | 44,820,992 |
| stock separate ramdisk | `4dd6d91a…cfdbb` | 2,097,152 |

## 2. 阶段 A — 头部事实

- **stock kernel 载荷 = gzip（`1f 8b 08`）**，解压后 57,470,992 B 的 ARM64 Image：`text_offset=0x80000`，`image_size=70,504,448`（含 BSS），flags=0x10。**stock 日常启动已在处理 >57 MB 的解压内核。**
- **PREP10 kernel 载荷 = raw ARM64 Image**（magic 0x644D5241 @+0x38）：`text_offset=0`，`image_size=45,547,520`，flags=0xA = LE + **4K 页** + **PHYS_BASE（可重定位，要求加载基址 2MB 对齐）**。
- 字面头部地址（stock 与 PREP10 同）：kernel_addr=0x8000 / ramdisk_addr=0x2000000 / dtb_addr=0x1F00000。
- **stock 的头部 DTB×ramdisk 字面区间本身就完全重叠**（[0x2000000,0x207EF32) ⊂ DTB 区间）而设备每天正常启动 → 字面地址不可能是最终物理放置，必须以 ABL 实际行为为准（本报告 §3 即为其证明）。
- separate ramdisk 分区 = **mini-bootimg**（`ANDROID!` v1 风格，page_size=2048，自身头部 kernel_addr=0x10008000 / ramdisk_addr=0x12000000，0x800 起 gzip initramfs）——与 v2 头部占位地址不同源。

## 3. 阶段 B — Hybrid ABL 实际加载路径（反汇编证据链）

代码为标准 Qualcomm QcomModulePkg linux-loader（china_compile 构建）。单一巨型函数 0x36C1C–0x388E8 承载 BootLinux 尾段（正常启动与 fastboot RAM boot 共享；`0x8000/0x80000` 偏移选择 csel 在全 .text **仅 1 处** @0x374AC，ExitBootServices 仅 1 处 @0x34EA0）。

| 步骤 | 证据（函数/站点） | 行为 |
|---|---|---|
| 1. ImageBuffer | LoadImageAndAuth@0x2FE10+，gBS->AllocatePages@0x30858 | 整分区读入 UEFI 分配缓冲；`Info+0x130`=ImageBuffer、`+0x138`=ImageSize（0x36F04–0x36F10） |
| 2. 头解析 | 0x36FE0–0x370A4（逐字节 bfi 组装 LE32） | 读 +8/+0x10/+0x18/+0x24/+0x28 → 栈槽 -0x40/-0x38/-0x3C/-0x44/Info+0x458；**不读 +0xC/+0x14** |
| 3. 32/64 位判定 | 0x37368–0x37380 | `ldr w8,[payload+0x38]` cmp 0x644D5241：raw ARM64 → flag=0；否则 flag=1（32 位） |
| 4. **kernel 目的地址** | 0x374A8–0x374C8 | `csel x8, (0x80000 : 0x8000), eq` → **KernelLoadAddress = ImageBuffer + 0x80000**（64 位）；与头部 kernel_addr 无关 |
| 5. **ramdisk/DTB 地址** | 0x374D0–0x37508 | `R = ImageBuffer+ImageSize - (round_down(ramdisk_size+B+page,page)+page)`；`D = R - page - 0x200000`；**容量检查 x27 = D - KernelLoadAddress > 0** 否则报 'Not Enough space left to load kernel image'（0xCF250） |
| 6. kernel 搬移 | raw: CopyMem@0x37818（dst=KernelLoadAddress, src=ImageBuffer+0x1000, len=kernel_size）；gz: 0x39AB0 解压至同一 dst | 无 relocation，无 text_offset 解析 |
| 7. DTB | 0x37BE4（v2 分支）→0x3B3A8/0x39DC0/0x3BA60 → CopyMem@0x381BC（dst=D，src=DTB blob，len=be32 totalsize，空间检查@0x38130）；ufdt overlay（0xE0xxx 簇）；g_fdt_addr（0x21314/0x21808） | 最终 FDT → TagsAddress（栈槽 -0x58，即 D 或 overlay 后新缓冲） |
| 8. separate ramdisk | LoadRamdisk@0x3969C（'INFO: start/end loadramdisk'、BootRamdiskSizeOverLimit）+ move_ramdisk_to_img_addr（0x38520/0x399D4）→ `linux,initrd-start/end` 写入 FDT@0x3F0F0/0x3F33C；kaslr-seed@0x3EFC4 | initrd = separate ramdisk 分区（PREP04 字节级一致）；嵌入 ramdisk 不用作 initrd |
| 9. 关机+跳转 | 0x386D8 bl 0xB5968 → 0x386DC 看门狗 → **0x386E4 bl 0x34DB0 ShutdownUefiBootServices**（GetMemoryMap@0x34E3C + **ExitBootServices@0x34EA4**）→ 0x34F50 反初始化链 → **0x38868–0x3887C：`blr x8`，x8=KernelLoadAddress，x0=TagsAddress(FDT)，x1=x2=x3=0**（arm64 ABI）；32 位路径 0x38894（x2=Tags） | entry = ImageBuffer+0x80000 |

工具链：capstone 5.0.7 线性扫描 + reaching-definitions ADRP/ADD 数据流（复用 CLOSE01 dataflow_xref，修复模块导入 argv 污染）；字符串引用经 composed-VA 普查捕获尾合并引用（98 处命中，见 evidence）。

## 4. 发现一：`fastboot boot` + PREP10 原文件 = ABL 内部 staging 重叠（FIRST-BOOT01 失败机制）

放置公式从 **ImageBuffer+ImageSize 的末端**向下开辟 ramdisk/DTB。`fastboot boot` 时 ImageSize=下载大小：

| 量 | 值（相对 ImageBuffer） |
|---|---|
| 下载/缓冲（PREP10 文件） | 46,563,215 B (0x2C67F8F) |
| KernelLoadAddress | +0x80000 |
| kernel 末端 | +0x2B3EA00 |
| RamdiskLoadAddress R | +0x2ABEF8F |
| DTB D | +0x28BDF8F |
| 容量检查 D>kLoad | 0x283DF8F > 0 **通过**（ABL 只查这个！） |
| **kernel末端 vs R** | **0x2B3EA00 ≥ 0x2ABEF8F → 重叠 0x4FA71 B（~318 KiB）** |

→ 44.8 MB 内核拷贝/解压会覆盖 ramdisk/DTB 暂存区（DTB 容量检查通过让 ABL 继续执行），FDT 被破坏 → 'ERROR: Couldn't find the suitable DTB!' 类失败或带坏 FDT 跳转 → 设备无法启动、无输出、返回/滞留 fastboot。**这与 K1-FIRST-BOOT01 的全部观察一致（下载 OKAY 1.091s、无重枚举、无 ADB、KERNEL_EXECUTION=NOT_CONFIRMED）**：首次 `fastboot boot` 失败无需假设认证拒绝——加载布局溢出已是充分解释。修正后理解：`RAMBOOT_NOT_CONFIRMED_USB_WRITE_TIMEOUT` 的底层机制大概率是本发现（PARTIAL——静态分析无法 100% 排除 USB/认证因素并存）。

分区启动路径无此问题（ImageBuffer=96 MiB 整分区缓冲，R=+0x5E57000，D=+0x5C56000，kernel 末端 +0x2B3EA00，余量 ~0x218 万 KiB 级）。

## 5. 发现二：PREP10 ARM64 Image 头契约与 ABL 固定 +0x80000 放置不相容（风险，交 AI1）

- ABL 不解析 kernel Image header（步骤 3/6 只查 magic 与拷贝），**固定** `+0x80000`。
- stock：Image.gz 内 `text_offset=0x80000` → 要求 2MB 对齐基址 + 0x80000 ↔ ABL 给出的恰是 `buf+0x80000` ✓ **相容**（且实机 stock 正常启动反证 `buf ≡ 0 (mod 2MB)`）。
- PREP10：`text_offset=0` + flags bit3=PHYS_BASE → **要求加载地址本身 2MB 对齐**；`buf+0x80000 ≡ 0x80000 (mod 2MB)` ✗ **不相容**。若 arm64 head.S 严格执行对齐检查，PREP10 即使成功写入分区也可能在极早期无输出地失败。
- 依任务书禁令：**不据此重打包、不改地址、不猜测新镜像**。此为静态推导的 RISK（PARTIAL——最终取决于 head.S 对错位加载的实际容忍度），列入 AI1 决策项。

## 6. 阶段 C — 判定（详细数值见 memory_map.md / stock_vs_prep10_load_ranges.csv）

见 §0 表。关键数字（分区启动、ImageBuffer=0x6000000）：

| 对象 | stock（gz） | PREP10（raw） |
|---|---|---|
| kernel 范围 | +0x80000 … +0x374F010 | +0x80000 … +0x2B3EA00 |
| R（ramdisk/initrd） | +0x5DE9000 | +0x5E57000 |
| D（DTB/Tags） | +0x5BE8000 | +0x5C56000 |
| kernel↔R/D 重叠 | 无（余 0x2499000） | 无（余 0x3117600） |
| 容量检查 | PASS | PASS |

## 7. 阶段 D — svesnav/linux-dby-w09 有限对照

`repack_boot.py`（已取回存档）：以 unpack_bootimg 提取的 **stock mkbootimg 参数原样重打包**（不动 kernel_addr/ramdisk_addr/dtb_addr）；`--kernel` 参数明示 "Replacement **compressed** ARM64 kernel"（Image.gz 路线）；`--full-partition` 模式**将交付镜像填充回 96 MiB 分区布局**。含义：
1. 参考项目与 PREP10 一样保留头部地址——间接印证 ABL 忽略这些字段；
2. 参考项目走 **gz 压缩**路线（与 stock/ABL 解压路径相容），PREP10 是 raw 路线（新路径 + text_offset=0 契约）——**不能把参考项目的可启动性外推到 ACK raw Image**；
3. 参考项目交付 96 MiB 全分区镜像——从工程实践上避开了本报告 §4 的 fastboot staging 溢出（下载缓冲≈分区大小 → R/D 开辟在高处）。
（该仓库 boot 备份哈希 `6fb82f6c…` 与本地 stock `7a95c897…` 不同——不同地区固件，仅作行为对照，不作字节对照。）

## 8. 限制

- LoadImageAndAuth 的 AllocatePages 请求大小未逐指令闭合（上溯为整分区读入，与 'read from %a, 0x%x bytes…partition size 0x%x' 日志及上游模式一致）→ 标注为高置信推断。
- separate ramdisk 的分区读取调用链 PARTIAL（LoadRamdisk/GetImage("ramdisk")/move 链存在性确认，中间指针传递未逐级闭合）。
- slot-0x28（放置公式中的 B 项，DTB 相关大小）的精确来源未闭合——其对判定的影响 <1.7 MiB，不改变任何 PASS/FAIL 结论（已做 B∈{0, dtb_size} 两种敏感性验证，结论不变）。
- head.S 对非 2MB 对齐加载的实际行为未静态验证（§5 标注 PARTIAL）。
- 遵守禁令：未连接设备、未运行固件、未重打包、未修改任何镜像。

## 9. 交付物

K1_BOOT_LOAD_MAP01_REPORT.md（本文件）、stock_vs_prep10_load_ranges.csv、hybrid_abl_load_path.md、memory_map.md、linux_dby_w09_comparison.md、evidence_matrix.csv、SHA256SUMS.txt、scripts/（9 个分析脚本）、evidence/（反汇编与扫描输出）。脱敏上传至 `firmware-analysis/boot-v2/boot-load-map01/`；原始 ABL/boot/ramdisk 不公开。
