# ROUND143 — ARM64 启动交接、EFI 内存地图与 FDT / reserved-memory 独立审查

- **执行者：2号 AI**
- 目标：Huawei MatePad 11 (2021) DBY-W09 / KONA / SM8250 v2.1
- 固定 ACK：aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9
- Candidate content tree：afe9517f8062b96bfeb5b4dd5714942861e6a44b
- 报告分支：ai2/round143-arm64-fdt-memory-handoff-audit
- 报告路径：firmware-analysis/round143/AI2_ROUND143_ARM64_BOOT_HANDOFF_FDT_MEMORY_AUDIT.md

> **本报告不能授权或证明首次设备启动。First boot remains BLOCKED / NOT AUTHORIZED.**

## 0. 结论摘要

**PARTIAL — PINNED SOURCE TRACE COMPLETE, TARGET HANDOFF UNKNOWN**

固定 ACK 源码已明确普通 AArch64 FDT 启动如何取得 /memory、零大小 tuple 如何处理、EFI stub 如何把 UEFI memory map 元数据交给内核、内核在什么条件下使用 EFI map 建立 RAM，以及 reserved-memory 静态/动态区域的解析顺序和标志处理。

DBY-W09 当前证据没有确定实际 ABL→Linux 路径，也没有最终交给 Linux 的 post-ABL FDT、可验证的 EFI memory map 描述符内容，或候选内核实际启用 EFI stub / FDT 参数解析所需的配置证据。因此：

- Candidate DTB 已知的 /memory@80000000 tuple 是零大小；固定 ACK 的普通 FDT memory scanner 会跳过它。
- 这不等于零大小 tuple 在所有启动路径上都必然致命。若实际进入 EFI stub，且该内核启用了 EFI FDT 参数解析并收到完整、有效的 UEFI metadata/map，EFI memory descriptors 可以成为 System RAM 来源。
- ABL 内部使用 UEFI、加载 PE/COFF Image、执行 EFI stub entry、内核最终成功接收有效 EFI memory map，是四个不同命题。现有项目证据没有证明其中任何一个发生在目标设备相关启动中。
- linux,usable-memory-range 主要用于 kdump 的内存范围限制；第一段是 cap，第二段才会显式 memblock_add()。不能泛化成“有这个属性就有完整 RAM map”。
- Candidate 的 18 个 reserved-memory 子节点与 HOS4.3 vendor base FDT 的 37 个子节点是不同 FDT 工件的计数，不构成已证明缺陷，也不能据此复制 vendor 节点。
- EFI stub 会删除 FDT header 的 /memreserve/ entries；固定 ACK 仍会在 EFI memory map 建立后解析最终 FDT 的 /reserved-memory 子树。EFI map 不会自动免除 reserved-memory 逐节点核对。

## 1. 证据分类与边界

- **PINNED SOURCE**：直接读取固定 ACK commit 的源码。
- **PUBLISHED REPORT**：直接读取已公开 ROUND137–ROUND141 报告。
- **INFERENCE**：只在上述来源约束下作出的推论。
- **UNKNOWN / NOT FOUND**：现有证据不能证明。

没有读取 Agent 私有工作区，也没有将报告摘要冒充原始设备证据。ROUND137–ROUND141 报告属于已公开报告证据，不是本轮重新采集的设备原始数据。

## 2. Direct AArch64 entry：FDT 与 RAM 路径

### 2.1 启动协议契约

**PINNED SOURCE —** [Documentation/arch/arm64/booting.rst L32-L42](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/Documentation/arch/arm64/booting.rst#L32-L42) 要求 boot loader 负责发现并初始化 Linux 将使用的 RAM；[同文件 L163-L168](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/Documentation/arch/arm64/booting.rst#L163-L168) 对普通 AArch64 entry 的寄存器约定为：

- x0 = system RAM 中 FDT blob 的物理地址；
- x1、x2、x3 = 0（保留）。

固定 ACK [arch/arm64/kernel/head.S L46-L55](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/kernel/head.S#L46-L55) 将 x0 定义为 FDT physical pointer；primary_entry() 在 L85-L87 保存启动参数；preserve_boot_args() 在 L168-L175 将 x0 保存到 x21 并记录 x0–x3；随后 [L231-L235](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/kernel/head.S#L231-L235) 将 x21 写入 __fdt_pointer。

[arch/arm64/kernel/setup.c L170-L194](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/kernel/setup.c#L170-L194) 的 setup_machine_fdt() 对 FDT 做映射并调用 early_init_dt_scan()；FDT 校验失败时进入早期错误处理循环。setup_arch() 在 L293 调用 setup_machine_fdt(__fdt_pointer)。x1–x3 非零会在 [setup.c L373-L377](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/kernel/setup.c#L373-L377) 产生违反启动协议警告。

### 2.2 普通 FDT memory scanner 的实际行为

**PINNED SOURCE —** [drivers/of/fdt.c L1000-L1028](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/of/fdt.c#L1000-L1028) 的 early_init_dt_scan_root() 从根节点读取 #address-cells 与 #size-cells，并以此解码 memory reg tuple。

[drivers/of/fdt.c L1034-L1085](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/of/fdt.c#L1034-L1085) 的 early_init_dt_scan_memory()：

1. 只处理 device_type="memory" 且 status 可用的节点；
2. 优先读取 linux,usable-memory，没有时才读取 reg；
3. 按根节点 cell 数解码每个 base/size tuple；
4. 对 size == 0 直接 continue，不调用 early_init_dt_add_memory_arch()，也不将其计为 found memory。

[drivers/of/fdt.c L1246-L1274](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/of/fdt.c#L1246-L1274) 显示 early_init_dt_scan_nodes() 的顺序是 chosen → memory scan → linux,usable-memory-range → KHO；它没有因 memory scanner 返回 0 而在此处直接拒绝整个 FDT。因此零大小 tuple 的确定后果是：**该 tuple 不提供 RAM**，而不是“FDT 在这一行立即必然停止启动”。

### 2.3 Candidate 零大小 tuple

**PUBLISHED REPORT —** ROUND140 §4.3（报告第 275–276 行）记录 candidate DTB：

/memory@80000000 reg = <0x0 0x80000000 0x0 0x0>

该报告明确将其标为 bootloader-filled placeholder，不是 RAM map。ROUND141 §3.1（第 113–123 行）已将其与固定 ACK early_init_dt_scan_memory() 的 size == 0 跳过逻辑对应。

**结论：** Candidate DTB 单独凭该 tuple 没有提供可用 RAM 范围。若目标实际走普通 direct entry，且最终 FDT 仍只有该零大小 tuple、又没有其他有效内存来源，则当前源码路径没有从这个 tuple 建立 RAM 的办法。不能把该结论扩展为“EFI 路径也绝无补救可能”。

### 2.4 linux,usable-memory-range 与其他早期来源

**PINNED SOURCE —** [drivers/of/fdt.c L879-L923](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/of/fdt.c#L879-L923) 的注释说明该属性主要用于 crash dump kernel，最多处理两个 range。第一段调用 memblock_cap_memory_range() 限制已有 memory；第二段在非零时调用 memblock_add()。因此：

- 它不是普通完整 RAM map 的同义词；
- 第一段本身是 cap，不会把缺失的第一段 RAM 自动加入；
- 第二段是一个明确的 add 行为，必须取得真实值并按该实现分析；
- 当前项目没有公布 candidate/final FDT 中该属性的完整值，不能推定它存在或可补足 RAM。

同一文件 L925-L946 的 KHO 路径要求启用 CONFIG_KEXEC_HANDOVER 且 /chosen 同时提供 linux,kho-fdt 与 linux,kho-scratch，然后调用 kho_populate()。这是专用 kexec handover 机制，不是一般 ABL/direct-entry RAM 发现机制；目标配置和属性均 UNKNOWN。

## 3. EFI-stub 与 EFI memory-map 路径

### 3.1 EFI PE/COFF entry 不等于普通 direct entry

**PINNED SOURCE —** [arch/arm64/kernel/efi-header.S L18-L50](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/kernel/efi-header.S#L18-L50) 显示 PE/COFF header 受 CONFIG_EFI 条件控制，PE entry point 指向 __efistub_efi_pe_entry。固定 ACK [drivers/firmware/efi/libstub/efi-stub-entry.c L25-L82](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/firmware/efi/libstub/efi-stub-entry.c#L25-L82) 定义 efi_pe_entry(handle, systab)，保存 EFI system table pointer、校验其 signature、获取 loaded-image protocol、处理命令行和 kernel image relocation，再调用 efi_stub_common()。

[drivers/firmware/efi/libstub/efi-stub.c L143-L174](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/firmware/efi/libstub/efi-stub.c#L143-L174) 中 efi_stub_common() 最终调用 efi_boot_kernel()。架构入口 [drivers/firmware/efi/libstub/arm64-stub.c L46-L58](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/firmware/efi/libstub/arm64-stub.c#L46-L58) 将 EFI stub 内核入口偏移定位到实际 primary_entry；[drivers/firmware/efi/libstub/arm64.c L131-L139](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/firmware/efi/libstub/arm64.c#L131-L139) 的 efi_enter_kernel() 以 enter_kernel(fdt_addr, 0, 0, 0) 进入内核。

因此 EFI stub 完成后，内核 primary entry 收到的仍是 x0=FDT、x1–x3=0；区别在于 EFI stub 已在 FDT 中写入 UEFI handoff metadata，并在跳转前完成 ExitBootServices 流程。

### 3.2 EFI stub 如何取得并发布 memory map

**PINNED SOURCE —** [drivers/firmware/efi/libstub/fdt.c L65-L121](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/firmware/efi/libstub/fdt.c#L65-L121) 显示 EFI stub：

- 删除 FDT header 的所有 /memreserve/ entries（注释明确说明 UEFI boot 时内核将从 UEFI memory map 找 reserved regions）；
- 在 /chosen 写入 linux,uefi-system-table；
- 预留 linux,uefi-mmap-start、linux,uefi-mmap-size、linux,uefi-mmap-desc-size、linux,uefi-mmap-desc-ver 属性位置。

[drivers/firmware/efi/libstub/fdt.c L147-L181](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/firmware/efi/libstub/fdt.c#L147-L181) 的 update_fdt_memmap() 在获取最终 memory map 后，将 map physical address、map byte size、descriptor size 和 descriptor version 写回 /chosen。

[同文件 L184-L206](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/firmware/efi/libstub/fdt.c#L184-L206) 的 exit_boot_func() 保存 struct efi_boot_memmap，生成 runtime virtual map，并调用 update_fdt_memmap()。L210-L292 的 allocate_new_fdt_and_exit_boot() 构造新 FDT，并调用 efi_exit_boot_services()。helper [drivers/firmware/efi/libstub/efi-stub-helper.c L411-L480](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/firmware/efi/libstub/efi-stub-helper.c#L411-L480) 获取当前 memory map、执行 map processing callback、调用 ExitBootServices；若 map key 因 map 变化失效，会按代码路径重取 map 并重试。

### 3.3 内核如何恢复 EFI metadata

**PINNED SOURCE —** [drivers/firmware/efi/Makefile L14-L18](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/firmware/efi/Makefile#L14-L18) 显示 fdtparams.o 只有在 CONFIG_EFI_PARAMS_FROM_FDT 时才加入构建。

[drivers/firmware/efi/fdtparams.c L20-L58](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/firmware/efi/fdtparams.c#L20-L58) 定义 /chosen 参数名。非 Xen 路径需要以下五项：

1. linux,uefi-system-table
2. linux,uefi-mmap-start
3. linux,uefi-mmap-size
4. linux,uefi-mmap-desc-size
5. linux,uefi-mmap-desc-ver

[fdtparams.c L84-L132](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/firmware/efi/fdtparams.c#L84-L132) 的 efi_get_fdt_params() 从 initial FDT 读取这些字段。FDT 不存在或 system-table 首字段缺失时返回 0；system-table 已找到但后续任一 map 字段缺失时也返回 0。因此对该固定实现而言，五项是 EFI handoff 被识别并恢复 map 所需的完整属性集合，不是只看到 system-table 属性就足够。

### 3.4 EFI map 是否能补足零大小 /memory

**PINNED SOURCE —** [drivers/firmware/efi/efi-init.c L137-L157](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/firmware/efi/efi-init.c#L137-L157) 定义哪些 EFI descriptors 可用作 System RAM；[L159-L230](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/firmware/efi/efi-init.c#L159-L230) 的 reserve_regions() 在非 KHO 情况下先移除此前从 DT 得到的 memblock memory，再遍历 EFI descriptors：

- is_memory() 仅将带 WB/WT/WC cacheability attribute 的描述符作为可添加 memory 的候选；
- is_usable_memory() 仅接受 Loader Code/Data、ACPI Reclaim、Boot Services Code/Data、Conventional、Persistent 等列举类型，并且要求 EFI_MEMORY_WB；
- 可添加但不属于 usable System RAM 的 descriptor 会被 memblock_mark_nomap()；
- EFI soft-reserve 开启且 descriptor 带 EFI_MEMORY_SP 时跳过；
- ACPI Reclaim memory 另行 memblock_reserve。

[drivers/firmware/efi/efi-init.c L233-L270](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/firmware/efi/efi-init.c#L233-L270) 的 efi_init() 先通过 efi_get_fdt_params() 取得 system table 和 map data；无 system-table 参数就直接返回。EFI map early mapping 失败会 panic；UEFI system-table/config-table 初始化失败会 unmap map 并返回；只有成功后才调用 reserve_regions()，再重新处理 linux,usable-memory-range。

**结论：是，固定 ACK 存在一个有条件的替代 RAM 来源。** 如果候选内核确实启用 CONFIG_EFI、CONFIG_EFI_PARAMS_FROM_FDT 和对应 EFI stub 构建，且目标实际执行 EFI PE entry / stub，生成了完整五项 /chosen metadata，map 地址/长度/descriptor 格式有效，system table 校验和后续初始化成功，那么 EFI descriptors 可以在没有非零 DT /memory tuple 时提供 RAM。它不是“ABL 使用 UEFI”自动触发的，也不是只凭 Image 有 PE header 就能成立。

### 3.5 四个不同命题与目标证据

| 命题 | 固定源码能说明什么 | DBY-W09 当前状态 |
|---|---|---|
| ABL 内部使用 UEFI 服务 | 仅说明 bootloader 可能调用 UEFI；不证明它以 EFI stub 启动 Linux | **UNKNOWN**；ROUND137 未找到 ABL binary / ABL log |
| ABL 加载 PE/COFF Image | PE header / entry point 使这种方式成为可能；不能证明目标 ABL 实际选择它 | **UNKNOWN**；没有 ABL log 或实际启动记录 |
| 执行 EFI stub entry | 需要进入 efi_pe_entry 并运行 stub；stub 生成 FDT metadata、获取 map 并 ExitBootServices | **UNKNOWN**；没有 stub trace 或最终 /chosen metadata |
| 内核实际收到有效 EFI map | 需要编译启用 FDT params、五项属性、有效 map descriptors、有效 system table 并成功完成 efi_init() | **UNKNOWN**；没有完整 metadata/map capture，也未确认候选 config 对应选项 |

ROUND137 §4 的唯一 partial bootloader trace 是 ro.boot.dtbo_idx=2。它只说明该次启动发布了 DTBO index，不说明 UEFI、PE/COFF、EFI stub 或 EFI memory map。

## 4. reserved-memory 的固定源码语义

### 4.1 解析入口、root cells 与 ranges

**PINNED SOURCE —** [arch/arm64/mm/init.c L205-L310](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/mm/init.c#L205-L310) 显示 arm64_memblock_init() 在完成 memory map 调整、kernel/initrd reservation 后调用 early_init_fdt_scan_reserved_mem()。

[drivers/of/fdt.c L499-L527](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/of/fdt.c#L499-L527) 的 early_init_fdt_scan_reserved_mem() 在 memblock 已激活后调用 fdt_scan_reserved_mem()，随后处理 FDT header /memreserve/ entries。

[drivers/of/of_reserved_mem.c L203-L223](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/of/of_reserved_mem.c#L203-L223) 的 __reserved_mem_check_root() 要求 /reserved-memory 的 #size-cells 和 #address-cells 与 root cell 数一致，并要求 ranges 属性存在。该实现检查的是“属性存在”，源码这段没有验证 ranges 内容必须为空。

### 4.2 Static reg reservations

[drivers/of/of_reserved_mem.c L152-L199](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/of/of_reserved_mem.c#L152-L199) 的 __reserved_mem_reserve_reg()：

- 以 root address/size cell 数解析 reg tuples；
- tuple 长度不符合 cell stride 时跳过该节点；
- no-map 存在时走 memblock_mark_nomap()，否则走 memblock_reserve()；
- 对 shared-dma-pool 且带 reusable 的区域执行 dma_contiguous_early_fixup()。

所以静态节点只有在节点可用、root format 通过、reg 可解析且 size 非零时才会产生实际 reservation。单纯存在一个 reserved-memory child 名称并不等于已经成功保留某段 RAM。

### 4.3 Dynamic size / alignment / alloc-ranges

[drivers/of/of_reserved_mem.c L291-L342](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/of/of_reserved_mem.c#L291-L342) 的 fdt_scan_reserved_mem() 先处理所有静态 reg 节点；只有静态解析返回 -ENOENT 且 child 有 size 时，才将该节点放入 dynamic queue；所有静态节点处理后再分配 dynamic 节点，避免动态分配覆盖静态 reservation。

[drivers/of/of_reserved_mem.c L397-L490](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/of/of_reserved_mem.c#L397-L490) 的 __reserved_mem_alloc_size()：

- size 必须符合 root size-cell 长度；
- alignment 如存在，按 root address-cell 长度解析；
- alloc-ranges 如存在，按 root address+size cell stride 解析为 start/size 范围，逐段尝试分配；
- 没有 alloc-ranges 时调用架构 allocator 在可用范围内分配；
- no-map 标志传给 allocator；
- shared-dma-pool + reusable + !no-map 会影响 CMA alignment；分配成功后 shared-dma-pool + reusable 会执行 contiguous early fixup。

Dynamic allocation 的最终物理地址由运行时 memblock 状态和 allocator 决定，不能仅凭节点名或 size 推断固定地址。

### 4.4 no-map、reusable 与互斥组合

**PINNED SOURCE —** no-map 在静态 reservation 路径中触发 memblock_mark_nomap()（of_reserved_mem.c L136-L148、L173-L185），含义不只是“保留”，还会从普通线性映射中排除该范围。

reusable 在该实现中是被读取的布尔属性；对 shared-dma-pool 它触发 CMA/contiguous early fixup；对非 shared-dma-pool 的区域，后续 init 路径还会记录 reusable size（L590-L613）。不能把所有 reusable 区域都理解成同一种 CMA 行为。

在本次固定 ACK 的 of_reserved_mem.c 解析路径中，未发现对 no-map 与 reusable 同时出现的显式互斥拒绝检查。静态 shared-dma-pool 路径会在 no-map reservation 成功后仍按 reusable 属性调用 contiguous fixup；dynamic 路径的 alignment 条件包含 !nomap，但成功后 fixup 判断只看 shared-dma-pool 和 reusable。**不据此认可这种组合为合法 DTS**：固定 ACK 仓库中的 reserved-memory YAML binding 文件未找到；同目录 reserved-memory.txt 仅说明文件已迁移到 dtschema 仓库。因此该版本 binding-level 互斥规则在本次 pinned-source corpus 中标记 **NOT FOUND**，必须用对应版本 schema 和真实 FDT 值核对，不能用猜测补齐。

### 4.5 overlap 与 consumer ownership

[drivers/of/of_reserved_mem.c L237-L284](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/of/of_reserved_mem.c#L237-L284) 的 fdt_scan_reserved_mem_reg_nodes() 保存静态 reg 节点并执行 overlap check；dynamic 节点在此前静态 reservation 后分配。Overlap log 是检测证据，不等于所有 owner/consumer 关系都已证明正确。

[drivers/of/of_reserved_mem.c L617-L672](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/of/of_reserved_mem.c#L617-L672) 的 of_reserved_mem_device_init_by_idx() 通过设备节点的 memory-region phandle 解析目标 reserved-memory node，再按该区域的 ops 给设备初始化。因此逐节点审查不能止于 reg：还必须解析 phandle、consumer node、memory-region-names 与实际 driver 使用关系。

### 4.6 解析顺序与 EFI map 的关系

固定 ACK [setup.c L323-L333](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/kernel/setup.c#L323-L333) 的顺序是 efi_init() 在前，arm64_memblock_init() 在后；后者在 [arch/arm64/mm/init.c L309](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/arch/arm64/mm/init.c#L309) 调用 reserved-memory early scan。

因此 EFI 成功路径先以 EFI descriptors 重建 RAM memblock，再由最终 FDT 的 /reserved-memory 子树做静态/动态保留。EFI memory map 不会使 /reserved-memory 节点自动失效。EFI stub 删除的是 FDT header 的 /memreserve/ entries（libstub/fdt.c L71-L76）；这与 /reserved-memory 子树是两套不同机制。

## 5. Candidate 与 HOS4.3 证据对照

| 项目 | 已发布证据 | 本轮判断 |
|---|---|---|
| Candidate /memory@80000000 | ROUND140 §4.3：一个 size=0 placeholder tuple | **PINNED SOURCE + REPORT：**该 tuple 被 scanner 跳过，不提供 RAM |
| Candidate /chosen/linux,uefi-* | ROUND137–ROUND141 未提供完整属性和值；候选 .config 是否启用 CONFIG_EFI_PARAMS_FROM_FDT 未由已读报告证实 | **UNKNOWN / NOT FOUND**；不能断言二进制中每项绝对不存在 |
| Candidate linux,usable-memory-range | 未见完整值或属性级审计 | **UNKNOWN / NOT FOUND** |
| Candidate /reserved-memory | ROUND140 §4.3：18 个 direct children | 只有数量，没有逐节点地址/标志/consumer 对照 |
| HOS4.3 vendor base FDT #0 | ROUND138 §5：37 个 direct children；Appendix A 有节点名称清单，但没有每个节点的完整 reg/flags | 不足以作 range equivalence |
| Live HOS4.3 FDT directory count | ROUND138 §5：st_nlink=39 代表 37 个子目录，不是 39；overlay 0/9 添加 reserved-memory 或 memory-region | 只支持结构计数；不是最终 FDT bytes 或节点属性值 |
| Final post-ABL FDT | ROUND137 §4：/sys/firmware/fdt 存在但 root-only，读取被拒；没有 FDT bytes/hash | **NOT FOUND** |
| ABL artifact / trace | ROUND137 §2–§4：授权 corpus 无 ABL binary；无 ABL→Linux handoff trace；ro.boot.dtbo_idx=2 仅为 partial property | **UNKNOWN** |
| DTBO variant | ROUND137/138：index 2 映射 package table entry 2 / VD 仅在条件成立时可用；设备 DTBO partition hash 未有 | **CONDITIONAL**，不能锁定 vendor variant |
| Boot-v2 / ramdisk | ROUND139：boot-v2、多 FDT section、embedded ramdisk 与独立 ramdisk partition 存在；ABL 选择/拼装行为未知 | 不能确定最终 FDT 来源或 EFI/direct entry |

特别说明：ROUND138 已纠正 live st_nlink=39 的含义为 37 个子目录；ROUND140 的 candidate 18 与 vendor base FDT 37 是不同工件。两者不是可直接判定的“少了 19 个 carveout”。

## 6. 关闭 FDT / memory gate 的最小证据包

### 6.1 必须来自最终 post-ABL FDT

| 必需证据 | 目的 | 最合适来源 |
|---|---|---|
| FDT header、total size、root #address-cells / #size-cells、root compatible/model | 证明结构与目标板身份 | 已有文件仅在确认是本次实际 Linux entry FDT 时可用；否则需要 authoritative final FDT artifact |
| 所有 device_type="memory" 节点的 status、reg 与 linux,usable-memory 全部 tuples | 计算非零可用 RAM 范围 | 最终 post-ABL FDT；candidate DTB 已知 tuple 不足 |
| /chosen/linux,usable-memory-range 全部值（如存在） | 判断 cap/第二段 add | 最终 post-ABL FDT |
| 完整 /reserved-memory 子树 | 核算每个 reservation | 最终 post-ABL FDT |
| 每个 reservation 的 node path/name、compatible、status、reg 或 size、alignment、alloc-ranges、no-map、reusable、phandles | 计算实际地址、大小、flags 和 allocator 结果约束 | 最终 post-ABL FDT；dynamic region 还需 memblock/allocator 结果或确定性约束 |
| 每个 memory-region / memory-region-names consumer reference 与目标 phandle | 确认 modem/ADSP/secure/display 等 owner/consumer | 最终 post-ABL FDT + 固定驱动 consumer source |
| FDT 总体身份与“此 FDT 就是传给 Linux 的那个”的证据 | 防止把 package base DTB 冒充最终 FDT | ABL trace / same-boot handoff record / authoritative final FDT artifact |

取得途径分类：
- 已发布 candidate/vendor 文件可继续只读分析，但不能替代 final post-ABL FDT。
- 若此前已有经过授权的同次启动 FDT artifact，可从已有工件验证。
- 当前报告记录的 live /sys/firmware/fdt 不可读；本任务不尝试绕过权限。未来如需 device capture，必须另行明确授权并采用只读、合规方式。
- 若没有现成 artifact，则需要权威 HOS4.3 ABL/FDT dump 或其他可验证的最终 FDT 工件。

### 6.2 必须用于识别 handoff route

| 必需证据 | Direct entry 所需 | EFI stub 所需 | 取得途径 |
|---|---|---|---|
| 实际 entry method | AArch64 primary entry 记录 | PE/COFF EFI entry / efi_pe_entry 记录 | 现有 ABL log/boot trace；缺失则 UNKNOWN |
| x0 / entry 参数 | x0 为最终 FDT physical address，x1–x3=0 | stub 最终调用 efi_enter_kernel(fdt,0,0,0) 的证据 | 已有同次启动日志/trace；不能从 ro.boot.dtbo_idx 推导 |
| EFI system table | 不适用 | linux,uefi-system-table 指针及可验证 system-table 内容 | final FDT + 对应 map/table artifact |
| EFI map metadata | 不适用 | linux,uefi-mmap-start/size/desc-size/desc-ver 五项 | final FDT |
| EFI descriptor map bytes | 不适用 | 按 desc_size/version 解码所有 descriptor 的 physical range/type/attribute | map pointer 所指的已保存内存 map artifact；仅有 FDT 属性值不足 |
| kernel config | direct FDT path 的配置/构建身份 | CONFIG_EFI、CONFIG_EFI_GENERIC_STUB、CONFIG_EFI_PARAMS_FROM_FDT 等实际候选 config | 已发布 candidate .config 或构建配置工件 |
| 成功消费证据 | 内核收到并扫描正确 FDT | EFI map 映射成功、system table 初始化成功、reserve_regions 实际执行 | 已有 sanitized boot log / trace；不得以 ABL “支持 UEFI”替代 |

### 6.3 Vendor map 对照

必须先确定实际 board variant 与实际 DTBO partition identity/selected entry，再选取对应 HOS4.3 base FDT 和 overlay。对每个 reservation 做逐项对照：

- node path/name、compatible、status；
- static reg range，或 dynamic size / alignment / alloc-ranges；
- no-map / reusable / CMA 相关属性；
- phandle、memory-region consumer 和驱动；
- 与 usable RAM、kernel、initrd、EFI descriptors、其他 carveout 的范围交叠；
- owner 是 bootloader、secure firmware、modem、ADSP、GPU/video/display、Linux CMA 还是其他 consumer。

ROUND138 的 37 个名称列表不能替代 range/owner/consumer 表。不能盲目把 vendor 37 个节点复制进 candidate。

## 7. 最小判定规则

### PASS（仅 FDT / memory gate）

以下条件必须全部满足：

1. 已证明用于 Linux entry 的确切 final FDT 身份、总长度和 root cell encoding；
2. 已证明实际 handoff route；
3. Direct path 下，final FDT 提供足够且非零的 memory tuples；或 EFI path 下，候选 config 启用相应 stub/FDT parser，五项 /chosen metadata 完整，EFI map descriptors 可读取、版本/长度有效、system table 校验成功，且至少有足够的 WB usable descriptors；
4. linux,usable-memory-range（如有）已按固定源码 cap/add 语义计算；
5. 所有静态和动态 reserved-memory 区域都能解析，实际 ranges/flags 与 allocator 约束已知；
6. usable RAM、kernel、initrd、reserved regions 与 firmware-owned carveouts 的交叠关系已核实；
7. 与正确 HOS4.3 board variant / base FDT / selected DTBO 的 per-node range、owner、consumer 对照完成，无未解释的必需 carveout 缺失；
8. 不存在未解决的 reservation overlap 或错误的 no-map/reusable 组合。

该 PASS 只表示 memory/FDT source-and-evidence gate 关闭，不表示整个系统可启动。

### FAIL（需先证明实际 final handoff）

- 已证明实际走 direct entry，final FDT 所有可用 memory tuples 均为零/缺失，且不存在实际可用的其他 RAM 来源；
- 实际走 EFI path，但缺少必需 FDT metadata、EFI map 无法映射、system table 校验失败或无足够 usable WB descriptors，且没有其他已证明的 RAM 来源；
- 最终 FDT cell encoding / reservation tuples 明确无效，或固定 ACK 明确拒绝该 reserved-memory root format；
- 已证明必需 carveout 缺失、usable RAM 与 firmware-owned range 冲突、或静态 reservations 存在未解决的 overlap。

Candidate DTB 的零大小 tuple 本身只证明“该 tuple 不提供 RAM”，不单独构成目标设备最终 handoff 的 FAIL，因为 final FDT 和 entry route 仍未知。

### UNKNOWN（当前状态）

- final post-ABL FDT bytes 不可用；
- ABL 实际 entry route 不明；
- candidate config 中 EFI stub / FDT params 开关未由公开证据确认；
- /chosen/linux,uefi-* 与 EFI map descriptors 未取得；
- linux,usable-memory-range 最终值未知；
- reserved-memory 逐节点 ranges、flags、consumer ownership 未对照；
- device DTBO partition identity 与实际 variant 未锁定。

任一核心项 UNKNOWN，memory/FDT gate 不得 PASS，first boot 继续 BLOCKED。

## 8. NOT FOUND 与 unresolved questions

1. 目标 HOS4.3 ABL binary / build identity / ABL→Linux entry log：**NOT FOUND**（ROUND137）。
2. 实际 Linux entry 时的 x0–x3 capture：**NOT FOUND**。
3. final post-ABL FDT bytes/hash 和属性值：**NOT FOUND**；现有 live FDT 只记录存在/长度/权限，内容不可读。
4. 完整 /chosen/linux,uefi-* 属性：**NOT FOUND**。
5. EFI descriptor map bytes、descriptor version/type/attribute/ranges：**NOT FOUND**。
6. Candidate 实际 CONFIG_EFI / CONFIG_EFI_GENERIC_STUB / CONFIG_EFI_PARAMS_FROM_FDT 状态：本轮已读公开报告没有列出这些 config 值，**UNKNOWN**。
7. Candidate 18 个 reserved-memory 节点逐节点值与 HOS4.3 vendor 37 节点逐项对应：**NOT FOUND**。
8. HOS4.3 binding YAML 在该固定 ACK 仓库路径下：**NOT FOUND**；同目录旧 txt 指向 dtschema 仓库迁移。没有用其他版本 schema 填补。
9. ABL 是否选中 EFI stub、是否实际 ExitBootServices、内核是否成功消费 EFI map：**UNKNOWN**。
10. ro.boot.dtbo_idx=2 不能证明上述任一 EFI/FDT memory handoff 命题。

## 9. 固定 ACK 源码索引

所有以下链接均固定到 commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9，不是当前 mainline。SHA 为该 commit 对应 Git blob identity。

| 源文件 | 关键行 / symbol | Blob SHA |
|---|---|---|
| Documentation/arch/arm64/booting.rst | 32–42 RAM responsibility；98–101 EFI header；138–142 Image placement；163–168 x0–x3 | e4f953839f7181ef5016e7f25e3f729dc5cb7bd7 |
| arch/arm64/kernel/head.S | 46–55 entry contract；85–87 primary_entry；168–185 preserve_boot_args；231–235 __fdt_pointer | 87a822e5c4ca83c279c733a54c79e64bb41870db |
| arch/arm64/kernel/efi-header.S | 18–50 PE/COFF header / entry point | 329e8df9215f5eb6ece40bec14c808c534f25c3a |
| arch/arm64/kernel/setup.c | 170–194 setup_machine_fdt；293 FDT setup；323–333 efi_init before arm64_memblock_init；373–377 x1–x3 warning | 56e69b249c2c5ec911f01c4a4b0a1ee96ae33707 |
| arch/arm64/mm/init.c | 205–310 arm64_memblock_init / reserved-memory scan | 87257fe5d4a5386cb48410763d64f901427209fd |
| drivers/of/fdt.c | 499–527 early_init_fdt_scan_reserved_mem；879–923 usable range；1000–1028 root cells；1034–1085 early_init_dt_scan_memory；1246–1274 scan order | a931cd4beaaa6e3becc3692e3b4b8a0e42d6a691 |
| drivers/of/of_reserved_mem.c | 136–199 static reg/no-map；203–223 root format；237–284 static nodes/overlap；291–342 static-before-dynamic; 397–490 dynamic allocator；550–570 overlap；590–613 init flags；617–672 memory-region consumer | d54cbaac9b822979b4d4479636969c7f452e4cee |
| drivers/firmware/efi/Makefile | 14–18 CONFIG_EFI_PARAMS_FROM_FDT gate | 8efbcf699e4ff9d0717eda19bd029f6a89110de7 |
| drivers/firmware/efi/fdtparams.c | 35–58 property names；84–132 efi_get_fdt_params | b815d2a754eef33b5157830fc739ca47dd666d3f |
| drivers/firmware/efi/efi-init.c | 137–157 usable descriptor type；159–230 reserve_regions；233–270 efi_init | a65c2d5b9e7b6d119206ed0380b4e7574e436c01 |
| drivers/firmware/efi/memmap.c | 19–81 __efi_memmap_init / efi_memmap_init_early | f1c04d7cfd712522b72243fdc2ff2c09700f82c4 |
| drivers/firmware/efi/libstub/efi-stub-entry.c | 25–82 efi_pe_entry | a6c0498351905cbf54b25498797c578dfa4688de |
| drivers/firmware/efi/libstub/efi-stub.c | 143–174 efi_stub_common | 874f63b4a3830ca84ee027e5515359f9b1fd48b7 |
| drivers/firmware/efi/libstub/arm64-stub.c | 46–58 primary_entry_offset | 2c38693561475c062d72df4ac743ea1d9f9f28e4 |
| drivers/firmware/efi/libstub/arm64.c | 131–139 efi_enter_kernel | e57cd3de0a00f47cdae91ccd601c465b995da59b |
| drivers/firmware/efi/libstub/fdt.c | 65–121 memreserve deletion / metadata creation；147–181 map metadata update；184–206 exit callback；210–292 final FDT/ExitBootServices | 6a337f1f8787b3bc68f771500f9fcd4b44a7b4f7 |
| drivers/firmware/efi/libstub/efi-stub-helper.c | 411–480 efi_exit_boot_services | 7aa2f9ad2935627b3eff4fd48f42942f6d93d75b |
| drivers/firmware/efi/libstub/Makefile | 76–87 FDT helper / generic stub / ARM64 stub objects | 94b05e4451dd3f992da629220b8be97c3247d4d2 |

## 10. 本轮合规声明

- 只读取固定 ACK 公共源码和 ROUND137–ROUND141 已公开报告。
- 未连接设备；未使用 USB、ADB、fastboot、recovery、serial、bootloader shell；未读取分区或 live FDT。
- 未访问 2号 Agent / WorkBuddy Agent 私有工作区。
- 未编译、未运行 Kbuild/Kleaf/Bazel/dtc/dtbs_check、未下载依赖或固件。
- 未修改源码、DTS、DTBO、patch、config、candidate tree 或 Image。
- 未制作启动包、未签名、未操作 AVB、未刷写、未尝试首次启动。
- 仅上传本脱敏 Markdown 报告。

## 11. 最终状态

**PARTIAL — PINNED SOURCE TRACE COMPLETE, TARGET HANDOFF UNKNOWN**

固定 ACK 的 direct-entry、EFI stub metadata、EFI map RAM population、zero-sized tuple、reserved-memory parser 与执行顺序均已追踪。目标 ABL 的实际 entry route、最终 FDT、EFI map descriptors、候选 config 开关和 reservation ownership 仍缺少证据。

**This task cannot authorize or establish first device boot. First boot remains BLOCKED / NOT AUTHORIZED.**

— END OF ROUND143 AI2 REPORT —
