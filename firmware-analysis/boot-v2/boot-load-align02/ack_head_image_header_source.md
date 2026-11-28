# ack_head_image_header_source.md

Source tree：`a31-apply` @ `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`（git rev-parse 实测 = 任务书冻结 commit）。

## text_offset = 0 的来源
`arch/arm64/kernel/head.S` L56-70（__HEAD 段，"DO NOT MODIFY. Image header expected by Linux boot-loaders."）：
```
L59:  .quad 0                // Image load offset from start of RAM, little-endian
L60?: le64sym _kernel_size_le  // Effective size of kernel image
L62?: le64sym _kernel_flags_le // Informative flags
...
L68?: .ascii ARM64_IMAGE_MAGIC
```
**L59 硬编码 `.quad 0`**；`grep -rn TEXT_OFFSET arch/arm64/Makefile` = 0 命中（本树已无 TEXT_OFFSET 机制）→ 生成 text_offset=0 ✓（PREP10 实测 0）。

## flags = 0xA 的来源
`arch/arm64/kernel/image.h` L40-57：
```
__HEAD_FLAG(field) = (__HEAD_FLAG_##field << ARM64_IMAGE_FLAG_##field##_SHIFT)
#ifdef CONFIG_CPU_BIG_ENDIAN __HEAD_FLAG_BE=BE #else =LE     → bit0=0
__HEAD_FLAG_PAGE_SIZE = (PAGE_SHIFT - 10) / 2                → 4K(PAGE_SHIFT=12) → 01b → bit1..2=01
__HEAD_FLAG_PHYS_BASE = 1                                    → 无条件 → bit3=1
__HEAD_FLAGS = BE|PAGE_SIZE|PHYS_BASE                        → 0b1010 = 0xA
```
→ 与冻结 Image flags=0xA 精确一致。flags bit3 语义（booting.rst）：放宽 2MiB aligned base 在 RAM 中的位置，**不放宽对齐本身**。

## head.S 运行时对齐行为
- `grep -c MIN_KIMG_ALIGN arch/arm64/kernel/head.S` → **0**：无任何运行时对齐 assert/检查分支。
- `primary_entry`（L85 `SYM_CODE_START`）；寄存器约定注释 L81-83：x21 = "FDT pointer passed at boot in x0"（与 ABL blr kload, x0=TagsAddress 一致）。
- 结论：对齐是 boot 协议义务（booting.rst mandatory placement），head.S 不显式检查——错位装载既非源码可证的必然 panic，也非可容忍；其后果不可静态断言。

## Kconfig 说明
PAGE_SHIFT=12（4K）由构建 config 决定，与 flags bit1..2=01 一致；RELOCATABLE/RANDOMIZE 的具体 config 值本轮未展开（PHYS_BASE 无条件置位已使 flags 与实测吻合，无需 config 旁证）。
