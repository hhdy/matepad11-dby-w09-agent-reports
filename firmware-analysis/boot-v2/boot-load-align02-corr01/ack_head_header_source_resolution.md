# ack_head_header_source_resolution.md

Source：`a31-apply`，git rev-parse HEAD = `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`（40 位，与任务书逐字一致 → ACK_SOURCE_COMMIT_PIN = PASS）。

## head.S 64-byte Image header 原文（arch/arm64/kernel/head.S L56-70）

```
	__HEAD
	/*
	 * DO NOT MODIFY. Image header expected by Linux boot-loaders.
	 */
	efi_signature_nop			// special NOP to identity as PE/COFF executable   ← offset 0x00 code0
	b	primary_entry			// branch to kernel start, magic                   ← offset 0x04 code1
	.quad	0				// Image load offset from start of RAM, little-endian ← offset 0x08 text_offset
	le64sym	_kernel_size_le			// Effective size of kernel image, little-endian   ← offset 0x10 image_size
	le64sym	_kernel_flags_le		// Informative flags, little-endian                ← offset 0x18 flags
	.quad	0				// reserved                                        ← 0x20
	.quad	0				// reserved                                        ← 0x28
	.quad	0				// reserved                                        ← 0x30
	.ascii	ARM64_IMAGE_MAGIC		// Magic number                                    ← 0x38
	.long	.Lpe_header_offset		// Offset to the PE header.                        ← 0x3C
```

## 槽位结论（阶段 E.3）

**L59 `.quad 0` 就是 offset 0x08 的 text_offset 槽**。本树 `image.h` 的 `HEAD_SYMBOLS`（L63-66）只定义 `_kernel_size_le` 与 `_kernel_flags_le` 两个符号——**不存在 `_kernel_offset_le`**（老树的该符号已改为内联 `.quad 0` 硬编码）；`grep -rn TEXT_OFFSET arch/arm64/Makefile` = 0 命中。前轮报告引 L59 无混淆；名称混淆风险来自旧版内核的 `_kernel_offset_le` 符号体系，特此说明。

## 展开关系（阶段 E.2）

`arch/arm64/kernel/image.h`：
```
L37-39: #define DEFINE_IMAGE_LE64(sym, data)  sym##_lo32 = DATA_LE32((data) & 0xffffffff); sym##_hi32 = DATA_LE32((data) >> 32)
L44-49: __HEAD_FLAG_BE = ARM64_IMAGE_FLAG_BE(1) 若 CONFIG_CPU_BIG_ENDIAN，否则 ARM64_IMAGE_FLAG_LE(0)
L50:    __HEAD_FLAG_PAGE_SIZE = (PAGE_SHIFT - 10) / 2        → 4K(PAGE_SHIFT=12) → 1
L52:    __HEAD_FLAG_PHYS_BASE = 1                            → 无条件
L54-56: __HEAD_FLAGS = __HEAD_FLAG(BE) | __HEAD_FLAG(PAGE_SIZE) | __HEAD_FLAG(PHYS_BASE)  → 0x1010b 的位域合成 = 0xA
L63-66: HEAD_SYMBOLS = DEFINE_IMAGE_LE64(_kernel_size_le, _end - _text); DEFINE_IMAGE_LE64(_kernel_flags_le, __HEAD_FLAGS);
```
冻结 Image 实测：text_offset=0 ✓、image_size=45,547,520 ✓、flags=0xA ✓ —— 源码与产物一一对应（静态一致；未做 objdump/map 旁证，因本地无该 Image 的构建 map，标 CONFIRMED-by-source+artifact-match）。

## config 与 fix 评估（阶段 E.5/E.7）

- 构建 config 文件本地未检出（PREP06 包中无 config-used-for-build.config）→ CONFIG_RELOCATABLE / CONFIG_RANDOMIZE_BASE 未核，PAGE_SHIFT=12 由 Image flags 反推 → **PARTIAL**。
- "改 text_offset=0x80000"（head.S L59 源码级修改）＝ **CONDITIONAL**：影响 `__PHYS_OFFSET`（= load_base + text_offset 语义）与入口重定位链，需完整重建并重新冻结 Image；**不认可"只改一个 header 字段肯定安全"**。
