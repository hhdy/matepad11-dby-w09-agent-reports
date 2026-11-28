# AI2 — ACK Android 17 ARM64 Image Entry / text_offset 静态审查

- 日期：2026-11-28
- 目标：Huawei MatePad 11 DBY-W09 VD；ACK android17-6.18.33_r00；Huawei ABL boot-v2 direct-partition path
- 审查范围：只读核对 ACK 固定上游提交的 ARM64 Image header、early entry、PI mapping/relocation、PHYS_OFFSET/kimage_voffset 定义；与 ADAPT02 已确认的 ABL kernel destination/alignment 事实对照
- 固定 ACK commit：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`
- 源码读取镜像：`raspberry-vanilla/android_kernel_brcm_rpi`，读取均固定到上述 commit；这是 ACK commit 的 GitHub 源码镜像，不代表本轮已经读取 ROUND157 的完整 23-patch 工作树
- 本轮没有修改源码、编译、制作镜像、连接设备或读写分区

## 1. 结论摘要

| 项目 | 结论 |
|---|---|
| ACK Image header 当前 text_offset | `0`，确认 |
| header 之后的启动入口 | `primary_entry`；x0 被保存为 FDT 参数 |
| early mapping | 由 `__pi_early_map_kernel` 对应的 PI 代码执行；从实际物理 `_text` 地址计算映射偏移 |
| relocations | `CONFIG_RELOCATABLE` 启用时，PI `relocate_kernel()` 应用 RELA relative；若 CONFIG_RELR 同时启用还处理 RELR |
| arm64 PHYS_OFFSET | 本提交的 `memory.h` 没有 `__PHYS_OFFSET` 宏；`PHYS_OFFSET` 是基于运行时 `memstart_addr` 的定义 |
| kimage_voffset | 在 primary switched 阶段按内核虚拟 `_text` 与物理入口地址 x0 的差值设置 |
| 仅把 header text_offset 由 0 改为 0x80000，是否需要同步改 PHYS_OFFSET/relocation 算法 | 在本次检查的固定上游代码中，没有发现这种直接依赖；这是 Image header/bootloader placement metadata 的变化，不是现有 PI relocation 算法的输入 |
| 改为 0x80000 是否已经解决 ABL 对齐 | **否**。它只把所需 ImageBuffer residue 从 0x180000 改为 0；ABL AllocatePages 仍只有 4KiB 页粒度证据，没有 2MiB 对齐保证 |
| 源码适配最终结论 | **CONDITIONAL / NOT APPROVED**；必须在实际 c56d93e… 候选树和最终 .config 上复核，且必须解决运行时 allocator residue 证据 |

## 2. Image header 与 entry

固定提交的 `arch/arm64/kernel/head.S` 在 ARM64 Image header 中写入：

- code0：`efi_signature_nop`
- code1：`b primary_entry`
- text_offset：`.quad 0`
- 后续为 image_size、flags、reserved、magic、PE header offset

因此 ACK 当前 Image 的 text_offset=0 与 ADAPT02 的二进制 header 读取一致。header 的 code1 进入 `primary_entry`；入口注释要求 MMU off、D-cache off，x0 为物理 FDT 地址。primary entry 通过 preserve_boot_args 保存 x0..x3，并沿 `__primary_switch` 进入 PI early-map 路径。

源码：
- https://github.com/raspberry-vanilla/android_kernel_brcm_rpi/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/kernel/head.S
- https://github.com/raspberry-vanilla/android_kernel_brcm_rpi/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/include/asm/image.h

## 3. Early mapping 与 relocations

`arch/arm64/kernel/pi/map_kernel.c` 的 `early_map_kernel()` 以运行时 `(u64)&_text` 作为 pa_base，并计算：

```c
u64 va_base, pa_base = (u64)&_text;
u64 kaslr_offset = pa_base % MIN_KIMG_ALIGN;
...
va_base = KIMAGE_VADDR + kaslr_offset;
map_kernel(kaslr_offset, va_base - pa_base, root_level);
```

其注释明确说明，KASLR offset 的低位来自 kernel image 的物理放置，以满足 early kernel mapping 的 2MiB block descriptor 约束。该逻辑读取实际物理 `_text` 地址，不读取 Image header 的 text_offset 字段。

`map_kernel()` 在启用 `CONFIG_RELOCATABLE` 时走 two-pass mapping，并调用 `relocate_kernel(kaslr_offset)`。PI Makefile 仅在 `CONFIG_RELOCATABLE` 下编入 `relocate.pi.o`。

`arch/arm64/kernel/pi/relocate.c` 的 RELA 路径仅处理 `R_AARCH64_RELATIVE`，写入位置为 `r_offset + offset`、写入值为 `r_addend + offset`；若 `CONFIG_RELR` 启用且 offset 非零，再应用 RELR entries。未发现该函数以 text_offset 作为参数或读取 header 字段。

源码：
- https://github.com/raspberry-vanilla/android_kernel_brcm_rpi/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/kernel/pi/map_kernel.c
- https://github.com/raspberry-vanilla/android_kernel_brcm_rpi/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/kernel/pi/relocate.c
- https://github.com/raspberry-vanilla/android_kernel_brcm_rpi/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/kernel/pi/Makefile

## 4. PHYS_OFFSET 与 kimage_voffset

本提交 `arch/arm64/include/asm/memory.h` 定义：

```c
extern s64 memstart_addr;
#define PHYS_OFFSET ({ VM_BUG_ON(memstart_addr & 1); memstart_addr; })
extern u64 kimage_voffset;
```

因此在这个 arm64 源码版本中，实际定义是运行时 `PHYS_OFFSET`，不是 `__PHYS_OFFSET`。本次读取的 arm64 `memory.h` 没有 `__PHYS_OFFSET` 宏。

此外，`head.S` 的 primary switched 路径把 `_text - x0` 保存为 `kimage_voffset`。这依赖运行时映像地址与入口物理地址，不依赖 header text_offset 的数值本身。由此，不能把“修改 text_offset 必然要同步修改 PHYS_OFFSET/relocation”当成已证实结论；在固定上游代码中没有发现这种直接耦合。

源码：
- https://github.com/raspberry-vanilla/android_kernel_brcm_rpi/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/include/asm/memory.h
- https://github.com/raspberry-vanilla/android_kernel_brcm_rpi/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/kernel/head.S
- https://github.com/raspberry-vanilla/android_kernel_brcm_rpi/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/mm/init.c

## 5. 与 ABL load-map 对照

ADAPT02 已经由目标设备 ABL 的静态反汇编证据确认：

- raw Image 与 gzip inflate 最终目的地址均为 `ImageBuffer + 0x80000`；
- `ImageBuffer` 来自 `gBS->AllocatePages(AllocateAnyPages, EfiBootServicesData, EFI_SIZE_TO_PAGES(size))`；
- 已证实的分配粒度为 EFI 4KiB 页；没有发现 2MiB 对齐请求、掩码或二次搬移；
- 实际运行时 `ImageBuffer_phys mod 0x200000` 未知。

ARM64 boot protocol 要求 Image 放在“2MiB aligned base + text_offset”处。因此：

| Image header text_offset | ABL Image 起始地址 | 需要的 ImageBuffer_phys mod 2MiB |
|---:|---:|---:|
| 0（当前 ACK） | ImageBuffer + 0x80000 | 0x180000 |
| 0x80000（拟议 header-only 改动） | ImageBuffer + 0x80000 | 0 |

把 text_offset 改成 0x80000，会让 ACK 的放置约束与 stock Image 的约束一致；它**不会**使任意 4KiB 对齐的 AllocatePages 返回地址自动变成 2MiB 对齐。stock 成功启动只能说明成功实例满足了 stock 的位置要求，不能证明 allocator 对所有 ACK-sized allocation 都保证 residue=0。

协议来源：
- https://github.com/raspberry-vanilla/android_kernel_brcm_rpi/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/Documentation/arch/arm64/booting.rst

## 6. 修订后的工程判断

1. **上游源代码层面**：header text_offset 由 0 改为 0x80000，没有发现必须同步修改 arm64 PHYS_OFFSET 或 PI relocation 算法的直接依据。它主要改变 bootloader 应如何放置 Image。
2. **ABL 装载层面**：header-only 修改把要求从 ImageBuffer residue=0x180000 改为 residue=0，但 ABL 的 AllocatePages 仍没有 2MiB 保证。因而不能据此把对齐风险标为 PASS。
3. **实际候选树层面**：ROUND157 的完整 23-patch 候选工作树（RAM patch 前 tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b`，后续候选 tree `c56d93eafa35057d65176db6594d67d5144868a0`）未在本轮被直接读取；必须对该精确工作树复核 head.S、linker、PI objects、relocation table 和 .config，特别是 CONFIG_RELOCATABLE / CONFIG_RELR。
4. **入口 ABI**：本轮确认了内核入口的源码要求，但没有证明目标 ABL 在进入 ACK 时的 MMU/cache/EL/寄存器状态全部满足要求；这仍是独立启动契约项。

## 7. Gate

- `UPSTREAM_HEAD_TEXT_OFFSET_ZERO=CONFIRMED`
- `UPSTREAM_PI_MAPPING_USES_RUNTIME_IMAGE_ADDRESS=CONFIRMED`
- `UPSTREAM_RELOCATION_DOES_NOT_CONSUME_TEXT_OFFSET=CONFIRMED`
- `ARM64_PHYS_OFFSET_IS_MEMSTART_ADDR=CONFIRMED`
- `ABL_IMAGEBUFFER_2M_ALIGNMENT=UNKNOWN`
- `C56_PATCHED_TREE_REVIEW=NOT_PERFORMED`
- `ACK_HEADER_ONLY_ADAPTATION=CONDITIONAL`
- `ACK_ANDROID17_DIRECT_ABL_BOOT=BLOCKED`

**决定：本轮静态审查缩小了源码风险范围，但不批准直接改头字段后制作镜像或启动。下一步必须读取精确 c56 候选树与最终 .config，并取得 ABL runtime ImageBuffer 物理地址 residue 的可信证据；否则 alignment gate 仍为 UNKNOWN。**

— END —
