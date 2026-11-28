# K1-BOOT-LOAD-ALIGN02-CORR01 — 修正 ImageBuffer allocator 证据与 ACK Image header source pin

- 签发：AI1
- 执行：WorkBuddy Agent（本机离线，GitHub 集成已接入）
- 目标：MatePad 11 DBY-W09 / HWDBY / SM8250 / VD
- 性质：只读静态反汇编 + 精确源码核验；不连接设备、不运行设备命令、不修改或重编译固件。
- 主报告：firmware-analysis/boot-v2/boot-load-align02/K1_BOOT_LOAD_ALIGN02_REPORT.md
- AI1 审核：firmware-analysis/boot-v2/boot-load-align02/K1_BOOT_LOAD_ALIGN02_AI1_REVIEW.md

## 0. 本轮目的

ALIGN02 最终结论 PREP10 ALIGNMENT=UNKNOWN 是正确的，但 AI1 审核发现 allocation evidence 有重大对象识别错误：

- 0x30858 的 ldr x8,[x8,#0x28] 是对一个由 0x32968 调用后经 [x23] 取出的厂商协议接口对象取方法槽，不是已证明的 gBS->AllocatePages。
- 0x55944 的 ldr x8,[x8,#0x28] 位于 gBS->LocateProtocol(+0x140) 返回接口之后，是该接口对象 +0x28 方法槽，不是 gBS->AllocatePages。
- 原扫描脚本只匹配 ldr x8,[x8,#0x28]，未做基址数据流分析，因此“32 个 gBS AllocatePages 站点”统计不成立。
- x0="secdata"（普通路径）和 x0=0xC5（fastboot 路径）也不是 EFI AllocatePages 的标准参数形状。

本轮唯一目标：从协议 GUID 到 +0x28 方法实现，再到真正的 ImageBuffer 分配与物理地址，补齐数据流。同时闭合 ACK 头部 text_offset 源码的实际生成关系。不得扩大成整套 ABL 重分析。

## 1. 冻结身份

### Hybrid ABL PE
- PE SHA-256：a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404
- PE VA==file offset 恒等映射已由 LOAD_MAP01 验证。
- 普通分区路径关键范围：0x307C0–0x30874。
- Fastboot 路径关键范围：0x558E0–0x5596C。
- 关联 helper：0x32968、0x32A28、0x32AF0、0x3283C、0x32B5C；这些函数的准确角色仍需重新验证，不能只用函数名猜测。

### ACK source commit
已核定的完整 40 位 commit：
8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

AI1 早期任务书中的 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9 只有 39 位，是遗漏末尾 a 的截断值；ALIGN02 报告给出的 40 位 commit 才是正确候选 pin。Agent 必须对本地源码树执行 git rev-parse HEAD，并将原始值与上面 40 位完整 SHA 比对。

### PREP10
- Image SHA-256：f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21
- Image size：44,820,992 B
- text_offset：0
- image_size：45,547,520 B
- flags：0xA
- magic：0x644D5241
- ABL raw kernel target：ImageBuffer + 0x80000（ALIGN02/LOAD_MAP01 指令级证据）

## 2. 阶段 A — 重新识别普通分区路径的对象与方法

从原始 PE 反汇编精确分析下列代码，不得沿用先前脚本对 +0x28 的命名：

    0x030800  adrp x8, #0x118000
    0x030804  adrp x0, #0x107000
    0x030808  mov  x1, xzr
    0x03080c  add  x0, x0, #0xf70
    0x030810  mov  x2, x23
    0x030814  str  xzr, [x23]
    0x030818  ldr  x8, [x8, #0xfe8]
    0x03081c  bl   #0x32968
    0x030820  tbnz x0, #0x3f, #0x30838
    0x030824  ldr  x8, [x23]
    0x030828  cbz  x8, #0x30838
    0x03082c  ldr  x9, [x8]
    0x030830  cmp  x9, #0x20, lsl #12
    0x030834  b.hs #0x30858
    0x030858  ldr  x8, [x8, #0x28]
    0x03085c  adrp x0, #0xcc000

要求：
1. 还原 0x32968 的函数体、caller 与参数语义。判断它是 gBS wrapper、LocateProtocol helper、还是厂商服务 helper；提供完整 VA/RVA/offset 和指令证据。
2. 定位 0x107000+0xF70 的 GUID/协议标识，按 GUID 字段端序正确解析。不得仅凭字符串猜协议名。
3. 明确 [x23] 返回对象的类型，以及 [object,#0x28] 的函数指针槽来源。
4. 追踪 0x30858 实际调用目标的函数实现、caller/callee、形参和返回值。
5. 如实现再次调用 EFI Boot Services，必须在每个间接调用处证明 function table base 来自 gBS，而不是其他协议接口。
6. 追踪从协议方法到 ImageBuffer 地址、长度、最终字段 Info+0x130/+0x138 的完整数据流。若无法到达，明确 PARTIAL/UNKNOWN。
7. 不得将 EFI GUID 结构体中的内存地址直接当作物理分配地址。

## 3. 阶段 B — 重新识别 Fastboot 下载路径

关键片段：

    0x055918  adrp x8, #0x118000
    0x055930  ldr  x8, [x8, #0x140]   ; gBS->LocateProtocol table slot
    0x055934  blr  x8
    0x05593c  ldur x8, [x29, #-0x98] ; LocateProtocol out-interface
    0x055944  ldr  x8, [x8, #0x28]  ; interface method slot
    0x055948  mov  w0, #0xc5
    0x05594c  blr  x8

要求：
1. 取回 0x55930 的完整 x0 GUID 参数、x1/x2 输出参数，解析 GUID 并确定协议接口。
2. 找出 LocateProtocol 输出接口 +0x28 方法真实目标。
3. 还原方法参数 w0=0xC5 的语义、输出缓冲区/地址参数、长度、返回状态。
4. 追踪它如何提供 fastboot download buffer；区分 USB 接收缓冲、boot image staging buffer、kernel final destination。
5. 追踪该方法内是否存在 EFI AllocatePages、AllocatePool、厂商 carveout、固定物理地址池或超分配/2 MiB 对齐。
6. 不要把 gBS->LocateProtocol 返回的 protocol vtable 方法槽称作 gBS->AllocatePages。

## 4. 阶段 C — 形成可审核的真正 allocator 站点清单

重做 align02_alloc_scan.py 或新建安全脚本：

- 不能只匹配 ldr x8,[x8,#0x28]。
- 必须从 gBS 全局指针的来源开始做寄存器/栈槽数据流跟踪。
- 只有当站点的基址确定是 gBS，且偏移是 AllocatePages 的真实 Boot Services slot，才能计入 EFI AllocatePages。
- 对函数 wrapper / protocol method，单独归类并跟进。
- 每个候选站点列出 instruction VA/RVA/file offset、基址对象来源、数据流链、function table slot、EFI Boot Services method 名称或 vendor protocol GUID + method index、置信度。
- 如静态脚本不能正确恢复跨函数的数据流，报告人工闭环的局限；不能声称“32 sites”是准确数值。
- 至少用 0x30858 和 0x55944 两个已知反例证明新脚本不会再次误分类。

## 5. 阶段 D — ImageBuffer 真实地址与对齐保证

确认 allocator 后，回答：

1. 正常分区启动的 ImageBuffer 是由哪个方法分配、以什么返回地址保存？
2. fastboot download buffer 是否同一对象/同一 allocator，还是另一对象？
3. 分配单位与对齐由哪个 API/固件实现保证？
4. 是否存在显式 2 MiB aligned allocation、向上/向下对齐、固定 carveout、物理地址约束或地址回传？
5. ImageBuffer 指针是否确为物理地址，或在 ExitBootServices 前后存在 virtual-to-physical 转换？
6. 哪些是静态保证，哪些是 runtime-dependent？
7. 若最终只能证明 4 KiB，给出被闭合的真实 EFI AllocatePages 路径；若 allocator 仍未知，不得引用 UEFI 4 KiB 页规范给 vendor method 下结论。

保留对齐公式：

    (ImageBuffer_phys + 0x80000 - text_offset) mod 0x200000 = 0
    stock required residue   = 0x00000
    PREP10 required residue  = 0x180000

结果可为 PASS/FAIL/UNKNOWN；没有确定物理地址余数时必须 UNKNOWN。

## 6. 阶段 E — ACK source header slot 核验

用精确 commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a：

1. 原样提供 arch/arm64/kernel/head.S header 64-byte 区域完整行（不是只摘 L59），标明 offset 0x08 的 text_offset、0x10 image_size、0x18 flags。
2. 原样提供 arch/arm64/kernel/image.h 中所有相关宏和 HEAD_SYMBOLS 展开关系。
3. 查明 head.S 中 .quad 0 与 _kernel_offset_le/TEXT_OFFSET 是否为同一 header slot；如果不是，说明报告前轮为何混淆。
4. 用编译器预处理/汇编阶段的只读展开输出（若现有构建树可用）或链接 Map / objdump 证明最终 offset 0x08 的值来源。
5. 核对实际 config 中 CONFIG_RELOCATABLE、CONFIG_RANDOMIZE_BASE、PAGE_SHIFT，以及它们与 head.S 入口和 relocation 代码的关系。
6. 不得修改 .quad 0，不重编译，不生成新 Image。
7. 只对“改 text_offset 为 0x80000”做源码影响评估；不认可“只改一个 header 字段肯定安全”的未证明说法。

## 7. 最终报告字段

    ORDINARY_PATH_PROTOCOL_GUID      = <GUID or UNKNOWN>
    ORDINARY_PATH_METHOD_0x28        = <function VA or UNKNOWN>
    FASTBOOT_PROTOCOL_GUID           = <GUID or UNKNOWN>
    FASTBOOT_METHOD_0x28             = <function VA or UNKNOWN>
    EFI_GBS_ALLOCATEPAGES_SITES      = <verified count or UNKNOWN>
    IMAGEBUFFER_ALLOCATOR            = <EFI API / vendor protocol / UNKNOWN>
    IMAGEBUFFER_POINTER_KIND         = <physical / virtual / identity-mapped / UNKNOWN>
    IMAGEBUFFER_ALIGNMENT_GUARANTEE  = <4K / 2M / fixed residue / UNKNOWN>
    IMAGEBUFFER_PHYS_RESIDUE         = <known value / runtime UNKNOWN>
    STOCK_ALIGNMENT                  = PASS / FAIL / UNKNOWN
    PREP10_ALIGNMENT                 = PASS / FAIL / UNKNOWN
    ACK_HEAD_TEXT_OFFSET_SOURCE      = CONFIRMED / PARTIAL / UNKNOWN
    ACK_SOURCE_COMMIT_PIN            = PASS / FAIL
    TEXT_OFFSET_0x80000_FIX          = VALIDATED / CONDITIONAL / UNSUPPORTED
    BOOT_WRITE_GATE                  = GO_FOR_FINAL_REVIEW / HOLD
    FINAL_RESULT                     = ALIGNMENT_PROVEN / ALIGNMENT_FAIL / ALIGNMENT_UNKNOWN

## 8. 交付与 GitHub 回读

仓库：hhdy/matepad11-dby-w09-agent-reports
目录：firmware-analysis/boot-v2/boot-load-align02-corr01/

必须提交：
- K1_BOOT_LOAD_ALIGN02_CORR01_REPORT.md
- protocol_guid_and_vtable_map.md
- verified_allocator_sites.csv
- ack_head_header_source_resolution.md
- evidence_matrix.csv
- SHA256SUMS.txt
- 仅本轮必要、脱敏的分析脚本和反汇编片段。

所有内容直接经 GitHub 集成提交。提交后从 GitHub 读回每个报告文件，记录 commit SHA、blob SHA 和内容核验。原始完整 ABL/boot/ramdisk 和设备敏感资料不得上传。

## 9. 严格禁止

- 不连接平板、不执行 ADB/Fastboot/OEM 命令、不查询当前设备模式。
- 不启动、不重启、不刷写、不擦除、不读写分区。
- 不修改 ABL/vbmeta/boot/ramdisk/DTBO/DTB/Image。
- 不编辑 ACK 源码、不改变 head.S、不重新编译、不重新打包、不生成候选镜像。
- 不执行固件提取出的任何二进制。
- 不扩大为全量 ABL 反汇编；只沿两个已确定的 protocol callsite 及其 helper/vtable method 闭环。

## 10. 停止条件

- 找到协议 GUID 和 +0x28 方法目标，完成真实 allocator 证据与 ImageBuffer 数据流后立即停止。
- 若接口实现位于不在当前冻结文件集中的组件，写明缺少哪一个精确文件/PE/库及为何缺少；不得拿同型号网络固件替代。
- 如果真实物理地址余数只能运行时确定，最终仍为 UNKNOWN；提出最小需要的只读设备侧观测种类，等待用户和 AI1 明确授权。
- 绝不因为 UNKNOWN 而擅自启动或刷写。

本任务仅修复 ALIGN02 的证据链缺口，不制作 Image，不代表刷写授权。
