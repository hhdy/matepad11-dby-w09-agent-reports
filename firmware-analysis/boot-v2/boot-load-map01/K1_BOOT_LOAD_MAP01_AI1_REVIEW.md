# K1_BOOT_LOAD_MAP01 — AI1 独立审核

审核对象：GitHub commit `cb766eae35649865b7c5aa69c06995ea71de6b13`
审核目录：`firmware-analysis/boot-v2/boot-load-map01/`
审核结论：**CORE LOAD-PATH CONFIRMED / FINAL IMAGE WRITE GATE STILL HOLD**

## 1. 总结

这是本项目目前最有价值的 ABL 逆向结果之一。Hybrid ABL 中 boot-v2 组件放置代码已有较强指令级证据，确认它不会简单按 boot header 里的 `kernel_addr`、`ramdisk_addr`、`dtb_addr` 字段进行最终物理加载。

因此，之前 AI1 单纯按 header 地址计算出的 kernel/DTB/ramdisk 重叠，是错误的静态假设；应以 Hybrid ABL 实际放置公式为准。

但“Hybrid ABL 真实加载行为已全部闭环”仍然说得过满。报告本身将 separate ramdisk 完整读取路径标为 PARTIAL，ImageBuffer 分配大小/绝对地址和 ARM64 Image 对齐契约也未完全证明。本轮进一步发现，报告遗漏了一个重要的 raw Image `image_size` 检查，并且 RAM boot overlap 的字节数和最小缓冲区估算存在计算错误。

**当前建议：接受分区启动路径的 load-map 核心逻辑；不再以 header literal addresses 作为阻塞；但在确认 ImageBuffer 对齐契约之前，仍不批准 PREP10 boot 写入。**

## 2. 已确认的真实 ABL 放置规则

对 SHA 匹配的 Hybrid PE（2,597,064 B，SHA-256 `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`），报告提供以下指令级证据：

- boot-v2 parser @`0x36FE0–0x370A4` 读取 `kernel_size`、`ramdisk_size`、`second_size`、`page_size`、`header_version`；未使用 header `kernel_addr`、`ramdisk_addr`、`dtb_addr` 作为最终放置目的地址。
- 64-bit/raw ARM64 kernel 目标地址由 `csel` @`0x374AC` 选出，随后 @`0x374C0` 加上 `ImageBuffer`，得到 `KernelLoadAddress = ImageBuffer + 0x80000`。
- DTB/Ramdisk 区域由 ImageBuffer 尾部向下计算：`R` 由 ImageBuffer+ImageSize 和 ramdisk/page/相关 slot 值计算；`D = R - page_size - 2 MiB`。
- raw kernel 使用 `gBS->CopyMem` @`0x37818`，目标为 `KernelLoadAddress`，源为 boot payload 的 kernel 区，长度来自 boot header `kernel_size`；gzip 路径进入 inflate @`0x39AB0`。
- DTB 通过 `CopyMem` @`0x381BC` 放到 `D`，后续进行 FDT/DTBO overlay 并把最终 FDT 指针传给内核。
- UEFI `ExitBootServices` @`0x34EA0`，BootLinux 主流程调用 shutdown @`0x386E4`；最终通过 `blr x8` @`0x3887C` 跳到 kernel load address，x0 传 FDT，x1-x3 清零。

因此以下结论可以接受：

```text
ABL_KERNEL_DESTINATION      = ImageBuffer + 0x80000 (64-bit)
ABL_DTB_DESTINATION         = dynamically computed D
ABL_HEADER_ADDR_FIELDS      = not used as final 64-bit load destinations
BOOT_V2_PARSER              = CONFIRMED (relevant size/version fields)
KERNEL_ENTRY_HANDOFF        = CONFIRMED (entry and FDT register handoff)
```

## 3. 分区启动的正常内存图：可接受，但有一个分配前提

按完整 96 MiB boot 分区作为 ImageBuffer（`0x6000000`）计算，Agent 给出的 PREP10 map 是：

| 对象 | ImageBuffer 相对地址 |
|---|---:|
| KernelLoadAddress | `+0x80000` |
| Kernel file-copy end | `+0x2B3EA00` |
| ARM64 Image image_size footprint end | `+0x2BF0000` |
| DTB D | `+0x5C56000` |
| Separate ramdisk R | `+0x5E57000` |

在这个 96 MiB ImageBuffer 前提下，kernel 的文件载荷和 image_size 所要求的内存范围都低于 D/R 区域，kernel 与 DTB/initrd 区域没有重叠，capacity check 也通过。

但报告 §8 自己承认 `LoadImageAndAuth` 的 AllocatePages 请求大小未逐指令闭合；因此 `ImageBuffer = 完整 96 MiB 分区缓冲` 仍属于高置信推断，而不是全链条已确认事实。写入 boot 分区后的普通启动路径很可能会采用完整分区大小，但报告应把以下状态分开：

```text
ABL_KERNEL_DESTINATION_FORMULA = CONFIRMED
PARTITION_IMAGEBUFFER_SIZE     = HIGH_CONFIDENCE_INFERENCE (96 MiB)
NORMAL_BOOT_NO_OVERLAP         = CONDITIONAL_ON_96MIB_IMAGEBUFFER
```

这不是否定 map，而是保留其明确的输入前提。

## 4. 重要纠正：Fastboot RAM boot 的第二个 image_size 检查被漏掉

报告目前强调 `0x37504` 处的 `D - KernelLoadAddress > 0` 检查，并写成 ABL 只检查这个容量条件。实际反汇编还有一个针对 ARM64 raw Image 的第二检查：

```text
0x037848  ldur x8, [x20, #-0x58]   ; D
0x03784C  ldur x9, [x20, #-0x70]   ; KernelLoadAddress
0x037850  ldr  x10, [x26, #0x10]   ; ARM64 Image header image_size
0x037854  sub  x8, x8, x9           ; D - KernelLoadAddress
0x037858  cmp  x10, x8              ; image_size vs available span
0x03785C  b.ls 0x3789c              ; only fits if image_size <= D-kload
```

按本轮已冻结数据：

| 项目 | 数值 |
|---|---:|
| PREP10 download/ImageBuffer size | 46,563,215 B |
| `D - KernelLoadAddress` | 42,196,879 B |
| PREP10 ARM64 `image_size` | 45,547,520 B |
| 超出 | **3,350,641 B** |

所以对本次 46,563,215 B 的 `fastboot boot` 请求，`0x37504` 的初始正值检查通过，并不代表 raw Image 最终通过；到 `0x37858`，`image_size` 比可用 span 多出 3,350,641 B，控制流将走失败分支，而不是到后面的 DTB copy / kernel handoff。

**这是目前对 FIRST-BOOT01 最有力的静态解释。** 它比简单宣称“FDT 被覆盖”更准确：
- report 在 `0x37818` 已经执行 kernel `CopyMem`，随后才执行 `image_size` 容量比较；
- 但是 `0x37858` 的 size check 会在后续 DTB copy/最终 kernel entry 前失败；
- 这解释了为何该 RAM boot 请求不应能到 kernel handoff；
- 它不能单凭静态分析证明 Windows 端具体 error 121 的因果链，也不能证明设备端运行时一定执行到了这条分支。此前的主机 USB endpoint timeout 仍是实际观察，root cause 只能写 probable/strongly supported。

应更新字段：

```text
FASTBOOT_RAMBOOT_IMAGE_SIZE_CHECK = FAIL (static PREP10 arithmetic)
FASTBOOT_RAMBOOT_KERNEL_HANDOFF   = NOT_REACHED_ON_THIS_PATH (static control flow)
FIRST_BOOT01_ROOT_CAUSE           = PROBABLE ABL raw-Image capacity rejection
REMOTE_FASTBOOT_FAIL_PACKET       = NOT_OBSERVED
HOST_USB_ERROR_121                = OBSERVED
```

## 5. 两处数值/表述错误

### 5.1 RAM boot overlap 数值

报告给出 `kernel_end=0x2B3EA00`、`R=0x2ABEF8F`。两者差值为：

```text
0x2B3EA00 - 0x2ABEF8F = 0x7FA71
```

不是报告中的 `0x4FA71`。以 kernel file-copy length 计算，kernel 复制区间越过 R 的长度是 522,865 B（约 510.6 KiB）。如果考虑 ARM64 `image_size` footprint，则还要使用 `image_size` 单独计算，不应把 file-copy end 与 image_size end 混为一谈。

### 5.2 最小 RAMboot ImageBuffer 估算

报告写 `minimum coherent ImageBuffer ~102,240,143 B`，但当前公式数据直接说明，随着 download buffer 增加，D 与 buffer end 一起向上移动，而 `D-kload` 对 ImageBuffer 的增长是一对一的。以当前实测差额估算，`image_size` guard 所需的 buffer 增量约为 3,350,641 B，得到约 49,913,856 B 的边界值（若 slot-0x28/B 项和其他 layout 参数保持不变）。因此 102,240,143 B 这个估算与本报告自己的 D-kload 公式不相符，需删除或给出另一个独立约束的推导。该数值不影响本轮分区启动的 96 MiB 条件计算，也不构成再次 RAMboot 的理由。

## 6. 仍未闭合的两个启动契约

### 6.1 Separate ramdisk 完整读取调用链仍是 PARTIAL

报告自己标记 `ABL_SEPARATE_RAMDISK_PATH=PARTIAL`。已定位 `LoadRamdisk@0x3969C`、ramdisk mini-bootimg 解析、copy/move helper 和 `linux,initrd-start/end` FDT fixup，但从 BootLinux 主流程到 partition read callback、源分区 buffer、目标 R 区域的完整调用/参数传递尚未逐级闭合。

因此不能称四条数据路径（kernel / DTB / embedded ramdisk / separate ramdisk）全部闭环。已具备足以支持“当前 Android initrd 来自 separate ramdisk”的既有 PREP04 字节证据；本轮 ABL 侧 caller chain 仍应标 PARTIAL。

### 6.2 PREP10 raw Image 的 2 MiB placement contract 仍是实际写入阻塞

PREP10 kernel header：
- `text_offset=0`
- `image_size=45,547,520`
- `flags=0xA`（LE + 4 KiB page + bit 3 physical placement）

Hybrid ABL 对 64-bit kernel 的 load address 固定为 `ImageBuffer + 0x80000`。Linux ARM64 boot protocol 要求 Image 被放置在一个 2 MiB 对齐基址加 `text_offset` 的位置；bit 3 允许这个 2 MiB 对齐基址位于可用 RAM 的其他位置，不会取消 2 MiB alignment requirement。官方说明：

- https://www.kernel.org/doc/html/next/arm64/booting.html
- https://android.googlesource.com/kernel/common/%2B/1798561befd8be1e52feb54f850efcab5a595f43/Documentation/arch/arm64/booting.rst

据此：PREP10 的 `text_offset=0` 要求 kernel entry/load address 本身 2 MiB 对齐；而 ABL 固定增加 `0x80000`。要使其满足协议，`ImageBuffer` 的物理基址需满足 `ImageBuffer mod 2 MiB = 0x180000`。当前报告没有从 AllocatePages 调用参数、实际分配器或可验证 memory map 证明这个对齐。

报告依据 stock kernel（内层 Image `text_offset=0x80000`）能正常启动，推断 `ImageBuffer mod 2 MiB = 0`。如果普通分区启动的 ImageBuffer 在 PREP10 路径中仍是同一种 96 MiB 分配、同一物理对齐，则 PREP10 的 kernel address 会错开 0x80000，无法满足 text_offset=0 的对齐契约。此项必须解决，不能只根据 partition capacity PASS 忽略。

这项是目前最重要的写入 gate：

```text
ABL_KERNEL_LOAD_OFFSET            = CONFIRMED (+0x80000)
PREP10_ARM64_TEXT_OFFSET          = CONFIRMED (0)
PREP10_2M_ALIGNMENT_REQUIREMENT   = APPLIES
IMAGEBUFFER_PHYSICAL_ALIGNMENT    = UNKNOWN
PREP10_KERNEL_ENTRY_ALIGNMENT     = UNKNOWN / POTENTIAL MISMATCH
BOOT_WRITE_GATE                   = HOLD_PENDING_ALIGNMENT_PROOF
```

## 7. 审核后的整体状态

```text
ABL_BOOT_V2_PARSER                = CONFIRMED (relevant fields)
ABL_KERNEL_DESTINATION            = CONFIRMED
ABL_DTB_DESTINATION               = CONFIRMED (formula)
ABL_KERNEL_COPY_OR_INFLATE        = CONFIRMED
ABL_KERNEL_ENTRY_HANDOFF           = CONFIRMED
ABL_EXIT_BOOT_SERVICES            = CONFIRMED
ABL_SEPARATE_RAMDISK_CALL_CHAIN    = PARTIAL
NORMAL_PARTITION_LOAD_MAP          = CONDITIONAL_SAFE (96MiB ImageBuffer assumption)
FASTBOOT_RAMBOOT_PREP10_SIZE_GUARD = FAIL (image_size > D-kload)
FASTBOOT_RAMBOOT_OVERLAP_BYTES     = REPORT ARITHMETIC CORRECTION REQUIRED
PREP10_2M_ALIGNMENT                = UNRESOLVED
DEVICE_WRITE_PERFORMED             = NO
FINAL_RESULT                       = LOAD_PATH_CORE_CONFIRMED; BOOT_WRITE_HOLD
```

## 8. 下一步

不需要再重复整个 ABL 反汇编，也不需要重做 DTBO/内核编译。下一项只需针对 PREP10 boot write gate：

1. 从 Hybrid ABL 的 `LoadImageAndAuth` / `ImageBuffer` allocation callback，确认 96 MiB 分区 image buffer 的实际分配方式、alignment 参数和地址保证；若实际物理地址由 runtime 分配决定且静态无法得到，明确这一限制。
2. 对照 ACK 6.18.33 的 `arch/arm64/kernel/head.S` / Image header，说明 `text_offset=0, flags=0xA` 在 ABL `ImageBuffer+0x80000` 路径中是否可用。不能只引用一般规范，要核对本次实际内核构建产物的 Image header 和 head.S。
3. 补上 `0x37850–0x3785c` 第二个 image_size 检查，修正 RAMboot 解释、overlap 算术和 102MB 最小 buffer 计算。
4. 对 separate ramdisk 保持原厂的计划不变；若 caller chain 无法闭合，继续 PARTIAL，不为此重新扩展无边界扫描。

**本审核不授权写入。** 目前可以确认 ABL 的核心 boot v2 组件布局代码，但还不能把 PREP10 标为完全可写入。只有 2 MiB 对齐契约与真实 ImageBuffer 分配条件闭合后，才应评估进入 boot-only 写入；DTBO 和 separate ramdisk 继续保持 stock。