# K1_DBY_W09_UBOOT_CHAINLOADER_ADAPT01 — ADDENDUM01（§13.5 两组剩余本地证据）

- 日期：2026-11-28；只读（本地冻结文件）；未连接设备
- 范围：严格按 §13.5.2 — A. live separate ramdisk wrapper；B. HOS4.3 ABL recovery→U-Boot 交接。不重复 AI1 已源码闭环的通用审查。

## A. Live separate ramdisk wrapper（冻结 `4dd6d91a…cfdbb`，实测 SHA 匹配 ✓）

| 字段 | 实测值 |
|---|---|
| 文件 SHA-256 | `4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb`（MATCH） |
| magic | `ANDROID!` ✓ |
| 头部类型 | **v0 经典 10 字段头**（@40 header_version 位=0，无 v1/v2 字段） |
| kernel_size / kernel_addr | 0 / 0x10008000 |
| ramdisk_size / ramdisk_addr | 1,406,106 (0x15749A) / 0x12000000 |
| second_size | 0 |
| tags_addr / page_size | 0x10000100 / **2048** |
| ramdisk payload offset | **0x800**（= ALIGN(page_size) + ALIGN(kernel_size=0)，v0 算术） |
| payload 边界 | end=0x157C9A < 2 MiB 分区 ✓ |
| payload SHA-256 | `4f71768ac33c494b2afdc7ea8dd224ea2af53a08e9542f07f9ae7c21de6cfa16` |
| gzip magic | 1f8b08 ✓ |
| 解压后 | 3,192,124 B，sha256 `e662b994155779c627a5b035e1560b346e2d7756d992b65609b8c225ed88d608` |
| CPIO | **070701 newc，19 条目**；**init (2,712 B) / init.real (2,880,584 B) / ksu.ko (305,048 B) 全部在位** ✓ |

**U-Boot v2026.10 `CMD_ABOOTIMG` 路线兼容性**：观测头为 v0；AI1 已源码闭环 `android_image_get_data()` 支持 v0–v2，且 `ARCH_SNAPDRAGON` 选择 `ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR` → v0 wrapper 的**就地 ramdisk 指针/长度**可被正确返回。本地字段算术（ALIGN(2048)+ALIGN(0)=0x800）与解析器 v0 算术一致。**LIVE_RAMDISK_CMD_ABOOTIMG_COMPATIBILITY = CONFIRMED**（无需自定义 raw-initrd patch；禁用 `bootm FIT wrapper:size` 冒号形式）。

## B. HOS4.3 ABL recovery→U-Boot 交接（冻结 Hybrid PE `a14e29da…dbb404`）

1. **recovery 载荷走同一加载族**：recovery-dtbo 头字段解析实证于 loader 族函数 0x4BB88（'Invalid recovery dtbo'）、0x4BCF0（'Recovery Dtbo Offset'）、0x4BD84（'Recovery Dtbo Size'）；分区选择字符串 'bootmode: %d, PartitionName %a Adjusted to %a'（0xC06CF）与 'resuce_recovery'（0xC62DD）在文件内。recovery 镜像 = boot v2 + recovery_dtbo，仅分区名与 extra 字段不同 → 与普通/fastboot 路径**共享 0x36C1C–0x388E8 BootLinux 尾段**。
2. **压缩 U-Boot payload 的放置与入口**（gz 路径，LOAD_MAP01/CORR01 已证，recovery 同尾段适用）：gz 检测 @0x3720C → flag 保持 0 → **解压目的 = KernelLoadAddress = ImageBuffer + 0x80000**（0x374AC csel 唯一）；ImageBuffer 来自 **gBS->AllocatePages**（CORR01：helper 0x34624 → 唯一站点 0x3468C）= **4 KiB 对齐**；+0x80000 保持 4 KiB 边界。入口 = 尾段 0x38868–0x3887C `blr x8`（x8=kload），x1=x2=x3=0。
3. **x0 = 最终 FDT**：`ldur x0, [x20,#-0x58]`（TagsAddress = recovery DTB + recovery_dtbo 合并后的最终 FDT）→ 与 U-Boot `save_boot_params()`/`get_prev_bl_fdt_addr()` 的 x0 约定对接（AI1 已源码闭环该 fallback 链）。**ABL_X0_FINAL_FDT = CONFIRMED**。
4. **`/memory/reg` 来源**：`UpdateDeviceTree`（0x3D9D0 族）dump 中无 memory-bank 写入证据（grep 0 命中）；ABL 侧是否由 EFI RAM Partition Protocol 构造真实 `/memory/reg` banks = **UNKNOWN**。按 AI1 修正：U-Boot 侧 `board_fdt_blob_setup()` 优先内部 control-FDT RAM map（CoWave 三段固定 tuples，本机无 byte 级 final-FDT capture → CONDITIONAL），内部 FDT 无有效 `/memory/reg` 时回退 `get_prev_bl_fdt_addr()`（即 ABL 传入 FDT）。**TARGET_RAM_BANK_SOURCE = UNKNOWN（ABL 侧）/ CONDITIONAL（CoWave tuples）**。

## Gates

| Gate | 值 |
|---|---|
| RECOVERY_TO_UBOOT_HANDOFF | **CONFIRMED**（同尾段 + recovery_dtbo 解析实证 @0x4BB88/0x4BCF0/0x4BD84；gz 解压→+0x80000→blr，4KiB 保持） |
| ABL_X0_FINAL_FDT | **CONFIRMED**（x0=TagsAddress=最终合并 FDT @0x38868–0x3887C） |
| LIVE_RAMDISK_CMD_ABOOTIMG_COMPATIBILITY | **CONFIRMED**（v0 wrapper + AI1 源码闭环 v0-v2 + IGNORE_BLOB_ADDR；本地字段算术一致） |
| TARGET_RAM_BANK_SOURCE | **UNKNOWN（ABL 侧 /memory/reg 写入）/ CONDITIONAL（CoWave 固定 tuples，缺本机 final-FDT capture）** |

## 仍 BLOCKED/UNKNOWN 清单（严格）

- 两个 vendor protocol provider（{A04D2E95…}/{A000398E…}）所在模块——不在冻结文件集。
- ABL UpdateDeviceTree 是否写真实 /memory/reg banks——需 byte 级 final-FDT capture（设备侧，未授权不做）。
- CoWave 三段 RAM tuples 对本机 VD 的有效性——无本机 capture，CONDITIONAL。
- recovery/recovery_vbmeta 写入面与回滚备份完备性——§7 审计未在本 addendum 范围（维持 NO-GO 直到清单补齐）。
- U-Boot 最终 .config 各项实际值——CoWave 构建产物未在本地（AI1 侧已部分源码核验）。

## 停止声明

按 §13.5.3：单份 addendum + GitHub 回读后停止。无设备操作、无镜像制作、无写入授权变更。
