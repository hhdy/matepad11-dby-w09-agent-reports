# CORR01 — stock_prep10_comparison.md（阶段 D：stock boot 与 PREP10 完整对照）

## Header 逐字段对照

| 字段 | Stock | PREP10 | 异同 |
|---|---|---|---|
| magic | `ANDROID!` | `ANDROID!` | SAME |
| header_version | 2 | 2 | SAME |
| page_size | 4096 | 4096 | SAME |
| header_size | 1660 | 1660 | SAME |
| kernel_size | 22,256,282 | 44,820,992 | **DIFF**（ACK > HOS kernel） |
| kernel_addr | 0x8000 | 0x8000 | SAME |
| ramdisk_size | 519,986 | 519,986 | SAME |
| ramdisk_addr | 0x2000000 | 0x2000000 | SAME |
| second_size | 0 | 0 | SAME |
| tags_addr | 0x100 | 0x100 | SAME |
| os_version | 0x1600014b | 0x1600014b | SAME |
| dtb_size | 1,664,243 | 1,216,399 | **DIFF**（PREP04 candidate DTB < stock DTB） |
| dtb_addr | 0x1f00000 | 0x1f00000 | SAME |
| recovery_dtbo_size | 0 | 0 | SAME |
| name | (empty) | (empty) | SAME |
| extra_cmdline | (empty) | (empty) | SAME |
| AOSP boot ID | `e14cadb6…` | `8f1501bc…` | DIFF（不同 payload） |

## Cmdline 对照

Stock（432 字符，首→末）:
`earlycon=msm_geni_serial,0xa90000 → … → buildvariant=user nokaslr`

PREP10（442 字符，首→末）:
`ignore_loglevel earlycon=qcom_geni,0xa90000 → … → buildvariant=user nokaslr`

| 变更 | 说明 |
|---|---|
| `ignore_loglevel ` 前缀 | **PREP10 新增**（PREP10 设计目的，覆盖 ABL 追加的 loglevel=0） |
| `earlycon=msm_geni_serial` → `earlycon=qcom_geni` | PREP06 改名（适配 ACK 驱动名），保留 |

## 载荷哈希对照

| 载荷 | Stock | PREP10 | 匹配 |
|---|---|---|---|
| kernel | （HOS kernel，非 ACK） | `f89a2839…bad21` ✓（ACK Image 冻结值） | N/A |
| ramdisk | 519,986 B / `a4b94ff6…1af3c` ✓ | 519,986 B / `a4b94ff6…1af3c` ✓ | SAME |
| DTB | 1,664,243 B（stock DTB） | 1,216,399 B / `7bb9a1fb…996b7` ✓（PREP04 candidate） | DIFF |

## PREP10 构建来源判定

`PREP10_BOOT_V2_PARSE = PASS`（有效 boot v2，所有字段可解析）

PREP10 **不是**从 stock boot 重打包的——它是一份独立构建的 boot v2 镜像：
- kernel 替换为 ACK Image（内核 SHA 与冻结值一致）
- DTB 替换为 PREP04 candidate DTB（SHA 与冻结值一致）
- embedded ramdisk 与 stock 完全一致（SHA 一致）
- cmdline 在 stock 基础上做了两处已知变更（ignore_loglevel 前缀 + earlycon 改名）
- 所有结构参数（page_size/header_version/header_size/addresses/os_version）与 stock 一致

`STOCK_BASE_REPACK_REPRODUCED = N/A`（PREP10 不是 stock 的复制品；它是一份新构建，共享 stock 的结构参数和 ramdisk，但替换了 kernel/DTB/cmdline 前缀）

## ignore_loglevel 决策

`ignore_loglevel` 在 PREP10 cmdline 中（PREP10 设计目的：覆盖 ABL 追加的 `loglevel=0`，使 kernel printk 不被抑制）。

**本参数不能弥补 K1 无可观察通道**——`ignore_loglevel` 只影响 kernel printk 级别过滤，不创造输出通道。如果 kernel 在 earlycon 初始化前就 panic，`ignore_loglevel` 无用。

**`IGNORE_LOGLEVEL_POLICY = AI1_DECISION`**（保留=维持 UART12 earlycon 调试意图；移除=更接近 stock 行为；交 AI1）

## Separate ramdisk

`SEPARATE_RAMDISK_ACTION = KEEP_STOCK_NO_WRITE`

ABL 加载 separate ramdisk 分区（非 PREP10 embedded ramdisk）作为 kernel initrd——PREP04 字节级证实。Stock separate ramdisk 包含 init/init.real/ksu.ko，不含 adbd/Kubuntu initramfs。不修改。
