# K1_BOOT_LOAD_ALIGN02_CORR01 — 修正 allocator 证据与 ACK header source pin

- 日期：2026-11-28；只读静态核验（未连接设备、未改镜像/源码/配置）
- AI1 审核指认正确：ALIGN02 的 0x30858 / 0x55944 站点确为**协议 vtable 方法槽**，非 gBS->AllocatePages；本轮完成修正与真链闭合。

## 0. 最终字段

```
ORDINARY_PATH_PROTOCOL_GUID      = {A04D2E95-8E39-B92B-3475-9EDD62779846}（厂商标签 x0=UTF-16 "secdata"；协议名 UNKNOWN——实现不在本 PE）
ORDINARY_PATH_METHOD_0x28        = UNKNOWN（实现不在冻结文件集；GUID 在 PE 内仅 1 次出现=调用点）
FASTBOOT_PROTOCOL_GUID           = {A000398E-69C9-3B72-225B-4E965964D211}（名称 UNKNOWN；同上，仅 1 次出现）
FASTBOOT_METHOD_0x28             = UNKNOWN（同上）
EFI_GBS_ALLOCATEPAGES_SITES      = 1（0x3468C；gBS 基址数据流证明，v2 脚本，两个反例 0 计数）
IMAGEBUFFER_ALLOCATOR            = EFI gBS->AllocatePages（经 helper 0x34624；调用点 0x2F73C/0x2F8B8 → 写入 Info+0x130 于 0x30344）
IMAGEBUFFER_POINTER_KIND         = identity-mapped 物理地址（UEFI boot services 期，无 vir2phys 转换）
IMAGEBUFFER_ALIGNMENT_GUARANTEE  = 4 KiB（EFI 页分配器：AllocateType=AllocateAnyPages(0)，MemoryType=EfiBootServicesData(4)，EFI_SIZE_TO_PAGES）
IMAGEBUFFER_PHYS_RESIDUE         = runtime UNKNOWN
STOCK_ALIGNMENT                  = UNKNOWN（经验：每次实机启动成功 ⟹ 该实例 ≡0，非静态保证）
PREP10_ALIGNMENT                 = UNKNOWN（需 buf≡0x180000，静态不可证）
ACK_HEAD_TEXT_OFFSET_SOURCE      = CONFIRMED（head.S L59 .quad 0 即 text_offset 槽；本树无 _kernel_offset_le 符号）
ACK_SOURCE_COMMIT_PIN            = PASS（git rev-parse HEAD = 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a，40 位逐字匹配）
TEXT_OFFSET_0x80000_FIX          = CONDITIONAL（源码级修改 .quad 0→.quad 0x80000 影响 __PHYS_OFFSET/入口推导与重定位生成，需完整重建与验证；绝非"仅改 header 字段即安全"）
BOOT_WRITE_GATE                  = HOLD
FINAL_RESULT                     = ALIGNMENT_UNKNOWN
```

## 1. 阶段 A：普通分区路径对象识别（修正）

0x32968 = **gBS->LocateProtocol 尾调用包装**：`ldr x8,[x8,#0x140]; br x8`（x0=GUID@0x107F70，x1=NULL，x2=&[x23]）。
GUID 字节 `952e4da0 398e2bb9 34759edd 62779846` → `{A04D2E95-8E39-B92B-3475-9EDD62779846}`（混合端序正确解析）。
返回接口对象：`[x23]`；`ldr x9,[x8]` = 接口首字段（版本/Revision），`cmp x9,#0x20 lsl 12`（≥0x20000 版本门控）；`[x8,#0x28]` = **该接口 vtable 第 6 槽方法**。调用实参 x0=UTF-16 "secdata"（分区名标签）→ 该方法为**分区块查询类**，其返回值（0x30874 `mov x21, x0`）用于分区大小检查路径，**与 ImageBuffer 分配无关**（0x30838 分支的 w2=7/EfiBootServicesData 同属此查询族）。
**实现不在本 PE**：GUID 全镜像仅调用点 1 次命中 → 方法目标 = UNKNOWN；缺少组件 = 该 UEFI protocol provider 模块（不在 abl.img，可能在 XBL/Huawei UEFI driver 集中，冻结文件集未含）。

## 2. 阶段 B：fastboot 路径对象识别（修正）

0x55930 = gBS->LocateProtocol（x0=GUID@0x107FA0 = `8e3900a0 c969723b 225b4e96 5964d211` → `{A000398E-69C9-3B72-225B-4E965964D211}`，x1=NULL，x2=&[x29-0x98]）；`ldur x8,[x29,#-0x98]` = 返回接口；`[x8,#0x28]` = 方法槽，w0=0xC5(197)（紧邻 0x55910 `cmp w8,#0xC5` 门控同值——接口版本/能力检查通过后回传同常数）。实现同样不在本 PE（GUID 仅 1 次命中）→ UNKNOWN；**该调用点与 gBS->AllocatePages 无关**（AI1 指认正确）。其对 download buffer 的贡献 = UNKNOWN（需 provider 模块）。

## 3. 阶段 C：安全 allocator 站点清单（v2 脚本）

脚本 `scripts/safe_alloc_scan.py`：跟踪任意寄存器 `[x?,#0xFE8]` 加载为 gBS 基址；ABI 感知（bl/blr 仅清 x0–x17，保留 x19–x28）；仅当槽加载时刻基址寄存器可证为 gBS 才计数。
结果（`evidence_safe_alloc.txt`）：gBS 加载 262；gBS 基槽加载 235；**AllocatePages(+0x28) = 1（0x3468C）**；AllocatePool(+0x40) = 7；CopyMem 43、LocateProtocol 86、ExitBootServices 1（0x34EA0）等直方图完整。
**反例验证：0x30858 / 0x55944 均 0 计数 ✓**（ALIGN02 的"32 站点"说法正式撤销）。

## 4. 阶段 D：ImageBuffer 真实分配链（新闭合）

```
LoadImageAndAuth 族（func 0x2FE10–0x322C0）
  ├─ 0x2F73C / 0x2F8B8:  bl 0x34624                       （两条启动路径共用同一分配 helper）
  │     0x34624 helper:
  │       0x34674  tst x20,#0xfff; lsr x9,x20,#0xC; cinc x2,x9,ne   ; EFI_SIZE_TO_PAGES(size)
  │       0x34680  mov w0,wzr                               ; AllocateType = AllocateAnyPages(0)
  │       0x34684  mov w1,#4                                ; MemoryType = EfiBootServicesData(4)
  │       0x34688  ldr x8,[x23,#0xFE8]                      ; x23=0x118000 → gBS（数据流干净）
  │       0x3468C  ldr x8,[x8,#0x28]                        ; gBS->AllocatePages
  │       0x34690  blr x8                                   ; (AnyPages, BsData, pages, &base)
  │       返回 x22 = [x24-0x10] = UEFI 页分配基址（无 +offset 重整）
  └─ 0x30344:  stp x22, x26, [x20, #0x130]                  ; Info+0x130 = ImageBuffer, +0x138 = ImageSize
BootLinux 0x36F04:  ldr x9,[x21,#0x130]                    ; 读用（LOAD_MAP01 已证）
```

∴ **ImageBuffer = gBS->AllocatePages 直接结果**：4 KiB 页粒度、AnyPages、BsData；**无 2 MiB 对齐请求/掩码/搬移**（helper 全体已核）。指针为 UEFI identity-mapped 物理地址（ExitBootServices 前后无转换——ABL 全程以物理地址操作，0x34EA0 唯一 ExitBootServices 后直接 blr kernel）。
对齐结论维持：`(ImageBuffer_phys + 0x80000 − text_offset) mod 0x200000` 的 2 MiB 余数 = **runtime UNKNOWN**；stock 经验 ≡0 不构成保证且与 PREP10 需求互斥 → **PREP10 = UNKNOWN（HOLD）**。

## 5. 阶段 E：ACK header slot 源码核定（commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a）

- `arch/arm64/kernel/head.S` L56-70（64-byte 头全录，见 `ack_head_header_source_resolution.md`）：**L59 `.quad 0` 即 offset 0x08 text_offset 槽**（行内注释 "Image load offset from start of RAM, little-endian"）；L60 = `le64sym _kernel_size_le`（offset 0x10）；L62 = `le64sym _kernel_flags_le`（offset 0x18）。
- `arch/arm64/kernel/image.h`：`HEAD_SYMBOLS` **只定义 _kernel_size_le/_kernel_flags_le 两个符号（L63-66）——本树不存在 _kernel_offset_le 符号**（老树的符号已被内联 `.quad 0` 取代）。因此不存在"另一槽位混淆"：前轮报告直接引 L59 正确；"TEXT_OFFSET" 名称在 Makefile 中 0 命中（grep 实测）。
- `DEFINE_IMAGE_LE64(sym,data)`（L37-39）：`sym_lo32 = DATA_LE32(data & 0xffffffff); sym_hi32 = DATA_LE32(data >> 32)` → `_kernel_size_le = _end - _text` = 45,547,520 ✓；`_kernel_flags_le = __HEAD_FLAGS = 0xA` ✓（BE=0、PAGE_SIZE=(12-10)/2=01b、PHYS_BASE=1 无条件）。
- config 三项：构建 config 文件不在本地可寻处（PREP06 包未检出该文件）→ PARTIAL；但 PAGE_SHIFT=12 由冻结 Image flags bit1..2=01b 与 Kconfig 推得；RELOCATABLE/RANDOMIZE_BASE 值未核——列入 CONDITIONAL 依据（改 text_offset 需同时复核 relocation 生成）。
- **TEXT_OFFSET_0x80000_FIX = CONDITIONAL**：修改点是 head.S L59（源码级，非"header 字段"）；影响 `__PHYS_OFFSET` 推导与入口重定位链，必须完整重建 + 重验，不支持"只改一个字段肯定安全"。

## 6. 交付与核验

6 件套 + 2 脚本 + 4 份反汇编证据 → `firmware-analysis/boot-v2/boot-load-align02-corr01/`；commit 后从 GitHub 回读全部文件核对 blob SHA 与内容。设备操作：无。
