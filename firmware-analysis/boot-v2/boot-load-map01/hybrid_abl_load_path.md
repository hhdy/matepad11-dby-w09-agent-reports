# hybrid_abl_load_path.md — Hybrid ABL 加载路径证据链

对象：`abl-hos43-pe.bin`（sha256 `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`）。
PE32+ @0xF10：machine=0xAA64，ImageBase=0，SizeOfImage=0x27A000，sections：.text VA=0x1000（0x108000，RX）、.data VA=0x109000（RW）、.reloc。**VA==file offset 恒等映射已验证**（探测 0x105B26/0x118E68/0xCC668/0x62B44/0xB4630 全部 identity）。

## 关键函数图

| VA | 角色 | 依据 |
|---|---|---|
| 0x2FE10–0x322C0 | LoadImageAndAuth 族 | 'LoadImageAndAuth'/'LoadImageAndAuthVB2' 字符串簇 + FailedLoadAuthBootImage 引用（0x30530 等） |
| 0x34DB0 | ShutdownUefiBootServices | GetMemoryMap(gBS+0x38)@0x34E3C + **ExitBootServices(gBS+0xE8)@0x34EA0/0x34EA4（全 .text 唯一）** |
| 0x34F50 | 退出反初始化链 | 0x34F54–0x34F74 连续 9 个 BL（0x64184/0x63CB0/0x63C68/0x690FC/0x690CC/0x63F70/0x64050/0x63DD8/0x645F0） |
| **0x36C1C–0x388E8** | **BootLinux 主函数**（单一函数，7.2 KB，多出口） | 近邻 prologue 检测 + census：全部 98 处加载路径字符串引用落在此函数及 0x3969C/0x3D9D4/0x4D2C8 等 |
| 0x3969C | LoadRamdisk | 'INFO: start/end loadramdisk'、'Error: Ramdisk size is over the limit'、move_ramdisk_to_img_addr、OverflowKernelCopy |
| 0x39AB0 | 解压/inflate | 'the input data is not a gzip package.'、zlib_calloc 字符串簇 |
| 0x3B3A8 | GetDtbOffset/DTB 校验 | 'DTB offset is incorrect, kernel image does not have appended DTB' |
| 0x3B6E0 | RAM 分区选择 | 以 &[x20-0xB8] 为出参被 0x37D78 调用；返回分区描述符 |
| 0x3D9D0/0x3D9D4 | UpdateDeviceTree/内存图 | 'Invalid memory configuration, check memory partition table'、'RAM Partitions'、kaslr-seed、linux,initrd-start/end 写入 |
| 0x4D2C8 | Stall 轮询（非跳转） | gBS->Stall(+0xF8)@0x4D4BC，ms×1000 |
| 0x60D0C / 0x611B0 / 0x611D8 | DebugPrint / 调试门 | PREP13 既有结论，本轮复现 |
| 0x62B44 / 0x62DC8 / 0x62F28 | AsciiStrLen / AsciiStrnCmp / 比较辅助 | PREP13 既有结论 |
| 0x118FE8 | gBS 指针 | `adrp x8,0x118000; ldr x8,[x8,#0xFE8]` 全文件高频 |
| gBS+0x160 / +0x140 / +0xE8 / +0x28 / +0xF8 | CopyMem / LocateProtocol / ExitBootServices / AllocatePages / Stall | EFI_BOOT_SERVICES 标准偏移（0x160 CopyMem 由 dst/src/len 三参调用形态确认） |

## 主路径汇编证据（节选，完整 dump 在 evidence/）

**头解析（0x36FE0–0x370A4，x23=ImageBuffer）：**
```
0x036FE8  ldrb w9,[x23,#0x29] ...        ; u32@(hdr+0x28)=header_version → Info+0x458; cmp #2, b.hi 错误
0x037014  ... bfi → stur w10,[x20,#-0x40] ; u32@(hdr+0x08)=kernel_size
0x03703C  ... → stur w10,[x20,#-0x38]     ; u32@(hdr+0x10)=ramdisk_size
0x037060  ... → stur w10,[x20,#-0x3C]     ; u32@(hdr+0x18)=second_size
0x03707C  ... → stur w8,[x20,#-0x44]      ; u32@(hdr+0x24)=page_size；[x20-0x18]=hdr+0x40(cmdline)
  （+0x0C kernel_addr / +0x14 ramdisk_addr：无任何加载/使用）
```

**32/64 判定（0x37368）：**
```
0x037368  ldr  w8,[x26,#0x38]            ; payload[0x38]
0x03736C  mov  w9,#0x5241 ; movk w9,#0x644d,lsl #16   ; 0x644D5241
0x037374  cmp  w8,w9 ; b.eq 0x37384      ; raw ARM64 → flag([x20-0x10])=0
0x03737C  mov w8,#1 ; sturb w8,[x20,#-0x10]  ; 32 位 → flag=1
```

**kernel 目的地址（0x374A8，全 .text 唯一 0x8000/0x80000 对）：**
```
0x0374AC  mov w10,#0x8000 ; mov w12,#0x80000
0x0374B8  cmp w8,[x20-0x10],#0 ; csel x8,x12,x10,eq   ; 64位→0x80000
0x0374C0  add x8,x8,x9                    ; + ImageBuffer
0x0374C8  stp x8,x9,[x20,#-0x70]          ; [kload, ImageBuffer+ImageSize]
```

**ramdisk/DTB 开辟 + 容量检查（0x374D0–0x37508）：**
```
0x0374DC  add w9,w9,w10 ... and w9,w9,w10 ; round_down(A+B+C,page)（A=slot-0x38,B=slot-0x28,C=page）
0x0374F0  ldp x10,x11,[x20,#-0x70]
0x0374F8  sub x9,x11,x9                   ; R = end - rounded(-page)
0x0374FC  add w11,w8,#0x200,lsl #12       ; page+2MB
0x037500  sub x11,x9,x11                  ; D = R - page - 2MB
0x037504  subs x27,x11,x10                ; 容量检查 D-kload（唯一检查）
0x037508  stp x9,x11,[x20,#-0x60]         ; [R, D]；D→TagsAddress 槽-0x58
  失败路径 → 'Not Enough space left to load kernel image'(0xCF250) 引用@0x376CC/0x37BD0
```

**kernel 拷贝（raw 路径 0x377FC–0x37830）与解压路径（0x3775C bl 0x39AB0，出参 [x20-0xA4]=解压大小）：**
```
0x037818  adrp x8,0x118000; ldr x8,[x8,#0xFE8]; ldr x8,[x8,#0x160]  ; gBS->CopyMem
0x03781C  ldur x0,[x20,#-0x70]  ; dst=KernelLoadAddress
0x037824  mov  x1,x26           ; src=payload
0x037820  ldur w2,[x20,#-0x40]  ; len=kernel_size
0x037830  blr  x8
```

**DTB → D（0x38198–0x381BC）：** `x24=[x20-0x58]`（=D），`w2=be32([x25+4])`（fdt totalsize），CopyMem(dst=D, src=blob)。空间检查 `cmp x23=(R-D), size` @0x38130。

**关机与跳转：**
```
0x0386E4  bl 0x34DB0                      ; ShutdownUefiBootServices
0x034EA0  ldr x8,[x8,#0xE8]; blr x8       ; ExitBootServices（全文件唯一）
0x038868  ldur x8,[x20,#-0x70]            ; x8=KernelLoadAddress
0x038870  ldur x0,[x20,#-0x58]            ; x0=TagsAddress=最终 FDT
0x03886C/74/78  mov x1/x2/x3, xzr
0x03887C  blr x8                          ; 进入 kernel（arm64 ABI）
```

## 唯一性证明

- `movz #0x8000 / movz #0x80000(lsl16)` 对：全 .text **仅 0x374AC 一处**（编码级扫描）→ 正常启动与 fastboot boot 共享同一放置代码。
- gBS->ExitBootServices：全 .text **仅 0x34EA0 一处** → 单一关机路径。
- 0x644D5241 magic 比较出现于 0x37708/0x37834（appended-DTB/kernel 检查）与 0x3736C（32/64 判定）。
