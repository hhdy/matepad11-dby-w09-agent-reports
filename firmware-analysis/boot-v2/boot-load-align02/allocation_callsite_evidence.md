# allocation_callsite_evidence.md

PE: `a14e29da…dbb404`（VA==file offset，LOAD_MAP01 已证）。gBS 指针 = `[0x118FE8]`。

## 站点清单
`gBS->AllocatePages(+0x28)` 共 32 处、`AllocatePool(+0x40)` 30 处 — 见 `evidence/align02_alloc_sites.txt`（本轮生成）。

## 普通分区启动路径（LoadImageAndAuth 族，func 0x2FE10–0x322C0）
```aarch64
0x030858  ldr  x8, [x8, #0x28]            ; AllocatePages
0x03085C  adrp/add x0 = 0xCC52E           ; 实测字节 = UTF-16 "secdata"（华为分区标签）
0x030864  mov x1, x21 ; mov x2, x22 ; mov x3, xzr
0x030870  blr x8
```
- 兄弟分支 0x30838：`mov w2,#7`（=EfiBootServicesData）、`ldr x8,[x8,#0x58]` — 同族包装调用。
- **调用点形参含标签字符串 → 华为包装层分配器**；内部最终为 EFI 页分配器（PACK 层未逐级闭合 = PARTIAL，不影响结论）。

## fastboot 路径（func 0x5573C 族）
```aarch64
0x055918  adrp x8, 0x118000 ; ldr x8, [x8, #0xFE8]   ; gBS
0x055930  ldr x8, [x8, #0x140]                        ; LocateProtocol
0x055944  ldr x8, [x8, #0x28]                         ; AllocatePages（包装）
0x055948  mov w0, #0xC5 ; blr x8                      ; w0=0xC5=197（类型/标签参数）
```
（`evidence/align02_dis_alloc_fastboot.txt`；与分区路径共用分配入口族。）

## 对齐逻辑搜索
- loader 路径（0x36C1C–0x388E8）与分配点附近**无** `0x1fffff` 掩码、`+0x180000` 修正、二次对齐分配。
- 全 .text `movz #0x8000 / #0x80000` 选择对唯一（0x374AC）→ 两路径共享放置代码。
- **结论：静态可证的仅 4 KiB 对齐；2 MiB 余数为运行时事实 → UNKNOWN。**
