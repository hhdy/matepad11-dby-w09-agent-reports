# K1_BOOT_LOAD_ALIGN02 — AI1 独立审核报告

- 审核对象：`K1_BOOT_LOAD_ALIGN02_REPORT.md`
- 分支：`ai1/boot-v2-first-package-prep`
- 审核结论：**ALIGNMENT = UNKNOWN；BOOT_WRITE_GATE = HOLD**
- 审核范围：报告、allocation callsite、反汇编摘录、对齐算式、ACK Image header/source 摘录及公开的 ARM64/UEFI 规范。
- 设备操作：无；本审核未连接设备、未执行 ADB/Fastboot、未修改镜像。

## 1. 总结

ALIGN02 的核心算式是正确的，最终保持 `UNKNOWN`、不批准刷入也是正确的：

```text
(ImageBuffer_phys + 0x80000 - text_offset) mod 0x200000 = 0
stock:   text_offset=0x80000 -> ImageBuffer_phys mod 2MiB = 0
PREP10:  text_offset=0      -> ImageBuffer_phys mod 2MiB = 0x180000
```

Hybrid ABL 对 stock gzip 解压路径和 PREP10 raw Image 路径都采用 `ImageBuffer+0x80000` 的结论，现有 CFG 证据具有说服力。ARM64 boot protocol 要求 Image 位于 2 MiB 对齐基址加 `text_offset` 的位置；PHYS_BASE flag 不取消这个对齐要求。该规范要求是 bootloader 的装载义务，不因 head.S 没有 runtime assert 而消失。参考：Linux ARM64 booting protocol（固定 ACK 对应文档版本）及 Android common kernel 文档。 

但本报告最关键的分配器证据存在**对象基址识别错误**：`0x30858` 和 `0x55944` 被标成 EFI Boot Services 的 `AllocatePages`，而反汇编上下文显示它们是在一个 LocateProtocol 返回的厂商协议对象上取 `+0x28` 方法指针。因而“32 个 gBS AllocatePages 站点”的扫描统计无效，且目前尚未证明 ImageBuffer 的真实分配实现、物理地址或 2 MiB 余数。

**结论：对齐不能判 PASS，也不能判确定 FAIL；保持 UNKNOWN。暂不写入 PREP10。**

## 2. 已通过的技术结论

### 2.1 ABL 对齐偏移

- PREP10 payload 在 `+0x38` 实测 ARM64 Image magic `0x644D5241`，落入 raw Image 分支。
- stock gzip payload 不经 raw magic 判断分支，flag 初始保持 0；解压目标仍使用同一 `KernelLoadAddress`。stock 与 PREP10 因此均采用 `ImageBuffer+0x80000`。
- PREP10 Image header：`text_offset=0`、`image_size=45,547,520`、`flags=0xA`。
- stock 解压后 Image：`text_offset=0x80000`。

据此，stock 与 PREP10 需要的 ImageBuffer 物理地址模 2 MiB 余数分别为 0 与 0x180000，二者互斥。报告没有把静态未知伪装为 PASS，这一点正确。

### 2.2 ARM64 协议解释

Linux ARM64 启动文档明确规定：Image 必须放置在一个 2 MiB 对齐基址加 `text_offset` 的位置，并从该位置进入；至少 `image_size` 字节必须可供内核使用。bit 3 的 PHYS_BASE 只放宽 2 MiB aligned base 在物理 RAM 中的位置，不取消 2 MiB 对齐。

来源：
- https://android.googlesource.com/kernel/common/+/1798561befd8be1e52feb54f850efcab5a595f43/Documentation/arch/arm64/booting.rst
- https://www.kernel.org/doc/html/v6.4/arm64/booting.html

### 2.3 不能用 head.S 无 assert 推导“错位可启动”

报告称 head.S 中没有 `MIN_KIMG_ALIGN` runtime assert。即使这一点在冻结源码中成立，也只能说明没有显式的运行时断言，不能免除 boot protocol 的装载要求。报告在这点上的谨慎处理正确。

## 3. 重大问题：AllocatePages 调用识别错误

### 3.1 0x30858 不是已证明的 gBS->AllocatePages

报告给出的反汇编为：

```aarch64
0x030818  ldr x8, [x8, #0xfe8]
0x03081c  bl  #0x32968
0x030824  ldr x8, [x23]
0x030828  cbz x8, #0x30838
0x03082c  ldr x9, [x8]
0x030830  cmp x9, #0x20, lsl #12
0x030834  b.hs #0x30858
0x030858  ldr x8, [x8, #0x28]
0x03085c  adrp x0, #0xcc000
```

关键在于：到 `0x30858` 时，`x8` 已经由 `ldr x8,[x23]` 从 `0x32968` 调用的输出对象取出；它不是通过数据流证明的 gBS 基址。随后 `[x8,#0x28]` 是这个接口对象的成员/方法槽。

紧随其后的调用参数中，`x0` 指向报告自己识别为 UTF-16 `"secdata"` 的字符串。这不是 EFI Boot Services `AllocatePages(AllocateType, MemoryType, Pages, Memory)` 的标准参数形状。

### 3.2 0x55944 也不是已证明的 gBS->AllocatePages

反汇编上下文：

```aarch64
0x055918  adrp x8, #0x118000
0x055930  ldr x8, [x8, #0x140]   ; gBS->LocateProtocol
0x055934  blr x8
0x05593c  ldur x8, [x29, #-0x98] ; LocateProtocol 输出的接口对象
0x055944  ldr x8, [x8, #0x28]    ; 接口对象 +0x28 方法
0x055948  mov w0, #0xc5
0x05594c  blr x8
```

这条路径明确先调用 gBS 的 `LocateProtocol`（offset `+0x140`），再从返回的接口对象取 `+0x28` 方法指针。该方法不能直接命名为 gBS 的 `AllocatePages`。

### 3.3 扫描方法导致 32 站点统计不可靠

`align02_alloc_scan.py` 只搜索 `ldr x8,[x8,#0x28]`，但没有证明每个站点的 `x8` 在该指令处就是 gBS 指针。上面两个已列作样例的站点就显示其基址是协议接口对象。因此：

```text
EFI_GBS_ALLOCATEPAGES_CALLSITE_COUNT = NOT_ESTABLISHED
0x30858_IS_GBS_ALLOCATEPAGES       = NO (protocol method slot)
0x55944_IS_GBS_ALLOCATEPAGES       = NO (protocol method slot)
VENDOR_PROTOCOL_ALLOCATOR          = UNKNOWN
IMAGEBUFFER_ALLOCATOR_IMPLEMENTATION = UNKNOWN
```

UEFI 规范规定 EFI memory descriptor 的 PhysicalStart 以 4 KiB 为边界；但这不能证明上述自定义接口一定直接使用该 API，也不能排除它内部申请更大对齐的 buffer。反之，也不能假设其会提供 2 MiB 对齐。必须跟进接口 GUID、接口结构、+0x28 方法的实现和输出参数，才能确定。

UEFI 来源：https://uefi.org/specs/UEFI/2.9_A/07_Services_Boot_Services.html

### 3.4 对齐结论

报告写“AllocatePages 仅 4 KiB 保证、无 2 MiB 重对齐”。由于关键调用点被误标且 wrapper 内部没有闭合，这一证据不足。更严谨的状态为：

```text
EFI_ALLOCATEPAGES_BASE_IDENTIFICATION = INVALID / NOT PROVEN
CUSTOM_PROTOCOL_METHOD_0x28           = CONFIRMED AT 0x30858 AND 0x55944
CUSTOM_PROTOCOL_METHOD_IMPLEMENTATION = UNKNOWN
IMAGEBUFFER_PHYSICAL_BASE              = UNKNOWN
IMAGEBUFFER_ALIGNMENT_GUARANTEE        = UNKNOWN
PREP10_ALIGNMENT                       = UNKNOWN
BOOT_WRITE_GATE                        = HOLD
```

## 4. ACK 源码及建议修正方向的保留意见

报告建议把 head.S 中 Image header 的 `.quad 0` 改为 `.quad 0x80000`。这只是候选源码方向，不是当前已通过的修复。

需要进一步核实：

1. **AI1 此处更正：** ALIGN02 报告中的 `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` 是 40 位完整 SHA；早期任务书中的 `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9` 实际只有 39 位，是 AI1 任务书遗漏了末尾 `a`。应保留 ALIGN02 报告的 40 位 commit，并以本地 `git rev-parse HEAD` 复核；不得要求 Agent 将有效 40 位 SHA 截短。
2. `head.S` 的 text_offset header slot、`image.h` 中 `HEAD_SYMBOLS` / `_kernel_offset_le` 的真实引用关系必须逐行闭合。当前报告同时声称 head.S 硬编码 `.quad 0`，又引用 image.h 中由 `TEXT_OFFSET` 生成 `_kernel_offset_le`，两者的最终链接关系尚未讲清楚。
3. 必须查清 `CONFIG_RELOCATABLE`、`CONFIG_RANDOMIZE_BASE`、相关 relocations 和入口代码对加载地址的要求；不能只改头部字段后假定二进制其余部分无需变化。
4. 任何方案都必须经源代码构建生成新 Image，再重新解析 64-byte header；禁止手改现有 PREP10 Image header。

因此暂不批准修改 `.quad 0`，也不批准生成新 boot 镜像。先修正并证明当前 ABL 的实际 allocator 行为。

## 5. 必须由 CORR01 补齐的最小事项

1. 对 `0x30858` 上游的 `0x32968`、`0x107f70` GUID/协议获取过程做数据流闭合；找出协议接口 GUID、对象布局及 `+0x28` 方法的真实实现。
2. 对 `0x55930` 的 LocateProtocol GUID 和输出接口做同样追踪；判断两个站点是否取得相同协议/对象类型。
3. 追踪 `+0x28` 方法的入参/返回值，直到最终 ImageBuffer 的返回/写入字段；识别它是否调用 EFI AllocatePages、AllocatePool、自定义 heap 或固定内存池。
4. 只有当寄存器基址经数据流证明是 gBS 时，才能将 `[gBS,#0x28]` 计为 AllocatePages；重新生成准确的 gBS AllocatePages 站点清单。
5. 明确可证明的对齐保证（4 KiB / 2 MiB / 固定 residue / runtime unknown），并区分 pointer 与 physical address。
6. 使用 40 位 ACK source commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`，提供 git rev-parse 原始输出；闭合 `head.S` / `image.h` header slot 的来源关系。暂不修改源码、不重编译。
7. 对“改 text_offset 为 0x80000”只做源码影响评估，不生成镜像。

## 6. 最终审核判定

```text
ABL_RAW_STOCK_AND_PREP10_OFFSET       = CONFIRMED (+0x80000)
ARM64_2M_TEXT_OFFSET_CONTRACT         = CONFIRMED
STOCK_REQUIRED_BUFFER_RESIDUE         = 0x000000
PREP10_REQUIRED_BUFFER_RESIDUE        = 0x180000
HEAD_S_NO_RUNTIME_ALIGNMENT_ASSERT    = REPORTED; NOT A PROTOCOL WAIVER
ALLOCATOR_CALLSITE_IDENTIFICATION     = MAJOR EVIDENCE DEFECT
ALLOCATOR_2M_ALIGNMENT_GUARANTEE      = UNKNOWN
PREP10_ALIGNMENT                      = UNKNOWN
PREP10_ALIGNMENT_UNDER_SAME_RESIDUE0  = FAIL
BOOT_WRITE_GATE                       = HOLD
DEVICE_WRITE_PERFORMED                = NO
FINAL_RESULT                          = ALIGNMENT_UNRESOLVED_CORR01_REQUIRED
```

本审核不授权实机操作。DTBO 与 separate ramdisk 策略保持 stock；不重试 RAM boot；不执行任何写入。
