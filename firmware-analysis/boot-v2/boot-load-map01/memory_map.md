# memory_map.md — stock / PREP10 实际加载内存图（按 Hybrid ABL 实际公式）

所有地址为相对 ImageBuffer 的偏移（ImageBuffer 为 UEFI AllocatePages 分配的启动镜像缓冲，基地址绝对值静态不可知；stock 实机可启动反证 `buf ≡ 0 (mod 2MB)`）。

## 分区启动（boot 分区写入后正常开机；ImageBuffer = 96 MiB 整分区缓冲）

| 对象 | stock（gz kernel） | PREP10（raw Image） | 证据 |
|---|---|---|---|
| ImageBuffer | 0x0 – 0x6000000（100,663,296 B） | 同左 | LoadImageAndAuth 整分区 |
| KernelLoadAddress | +0x80000 | +0x80000 | csel@0x374AC（64 位路径） |
| kernel 末端 | +0x374F010（gz 解压 57,470,992 B） | +0x2B3EA00（raw 44,820,992 B） | CopyMem@0x37818 / inflate@0x39AB0 |
| RamdiskLoadAddress R | +0x5DE9000 | +0x5E57000 | end − (round_down(ramdisk+B+page)+page) @0x374D0–0x37508 |
| DeviceTreeLoadAddress D / TagsAddress | +0x5BE8000 | +0x5C56000 | R − 4K − 2M @0x374FC–0x37508 |
| 容量检查 D−kLoad | +0x5B68000 PASS | +0x5BD6000 PASS | @0x37504 |
| kernel ↔ R/D | 无重叠（余 0x2499000） | 无重叠（余 0x3117600） | 计算 |
| separate ramdisk → initrd | R 区（linux,initrd-start/end 写入 FDT） | 同左 | 0x3F0F0/0x3F33C |
| 最终 FDT | D（或 ufdt overlay 新缓冲）→ x0 | 同左 | 0x381BC / 0x38870 |
| ABL 自身/UEFI 运行时 | AllocatePages 池、栈、heap（与载荷区分离，UEFI 内存图管理） | 同左 | 系统性质 |
| kaslr-seed | FDT chosen 节点（PRNG） | 同左 | 0x3EFC4 |

敏感性：放置公式中 B 项（slot-0x28）取 0 或 dtb_size 时，R/D 偏移差异 ≤1.7 MiB，全部 PASS/无重叠结论不变。

## `fastboot boot`（RAM 下载路径；ImageBuffer = 下载缓冲，ImageSize = 下载字节数）

PREP10 原文件 46,563,215 B：

| 对象 | 偏移 |
|---|---|
| KernelLoadAddress | +0x80000 |
| kernel 末端 | +0x2B3EA00 |
| R | +0x2ABEF8F（end − 0x1A9000） |
| D | +0x28BDF8F |
| 容量检查 | 0x283DF8F > 0 → **通过**（ABL 不检查 kernel 末端 vs R！） |
| **kernel ↔ R/D** | **重叠 0x4FA71 B（≈318 KiB）→ 拷贝破坏 ramdisk/DTB 暂存区** |

→ 对应 K1-FIRST-BOOT01 失败（详见主报告 §4）。若镜像按分区大小填充（≥ ~102 MiB 才能完全容纳本公式需要的 kernel+ramdisk+DTB+2MB 间隙——svesnav 项目正是以 96 MiB 全分区镜像交付），则下载缓冲足够大、R/D 落在 kernel 末端之上，无重叠。

## 字面头部地址（仅存档对照，ABL 不使用）

| 字段 | 值 | 实际用途 |
|---|---|---|
| kernel_addr=0x00008000 | 仅 32 位路径偏移（csel 另一支） | 64 位路径未使用 |
| ramdisk_addr=0x02000000 | 未读取（解析器跳过 +0x14） | 无 |
| dtb_addr=0x01F00000 | 未作为目的地址读取（+1652 字段无 dest 用法） | 无 |
| tags_addr=0x00000100 | 未读取 | 无 |

## ARM64 Image 头契约对照

| | stock（gz 内层） | PREP10 |
|---|---|---|
| text_offset | 0x80000 | 0x0 |
| image_size | 70,504,448（含 BSS） | 45,547,520 |
| flags | 0x10 | 0xA = LE + 4K 页 + PHYS_BASE（可重定位） |
| ABL 放置 | buf+0x80000 ≡ 0x80000 (mod 2MB) | buf+0x80000 ≡ 0x80000 (mod 2MB) |
| 契约要求 | 2MB 对齐基址 + 0x80000 ✓ 相容 | 加载地址本身 2MB 对齐 ✗ 相差 0x80000（主报告 §5 风险项） |
