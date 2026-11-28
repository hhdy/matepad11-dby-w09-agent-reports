# CORR01 — boot_tail_audit.md（阶段 C：完整 96 MiB stock boot 尾部审计）

## Stock boot 结构

| 字段 | 值 |
|---|---|
| 总文件 | 100,663,296 B (96 MiB) |
| kernel_size | 22,256,282 B |
| ramdisk_size | 519,986 B |
| second_size | 0 |
| dtb_size | 1,664,243 B |
| page_size | 4096 |
| header_version | 2 |
| header_size | 1660 |
| kernel @ | 0x1000 |
| ramdisk @ | 0x153b000 |
| DTB @ | 0x15ba000 |
| **payload_end** | **0x1751000 = 24,449,024 B (~23.3 MiB)** |

## 尾部审计结果

| 检查 | 结果 |
|---|---|
| payload_end 之后的尾部 | 76,214,272 B (**72.68 MiB**) |
| 尾部全部内容 | **全零**（0 个非零字节） |
| 最后 64 B | **全零**，无 AVB footer |
| 最后 4 KiB | **全零** |
| 最后 64 KiB | **全零** |
| 最后 1 MiB | **全零** |
| AVB footer magic `AVBf` | **不存在** |
| 非零数据范围 | **不存在**（合并后 0 个非零区域） |

## 结论

Stock boot 分区的 payload 结束于 24,449,024 B，其余 76,214,272 B（76.7%）全部为零。**无 AVB footer、无私有元数据、无签名尾部**。boot 分区没有任何超出 boot image payload 的持久化数据。

写入 PREP10（46,563,215 B）到 boot 分区：
- 覆盖 [0, 46,563,215) — PREP10 全部内容
- 保留 [46,563,215, 100,663,296) — 54,100,081 B，**全零**（PREP10 payload_end 0x2C68000=46,563,328 已超过 46,563,215 但仍在全零区域内）
- **BOOT_PREFIX_WRITE_GATE = PASS**（尾部无需要保留的数据）

注意：PREP10 文件大小 46,563,215 B（精确文件大小），但按 boot v2 page 对齐 payload_end 为 46,563,328 B（下一 4K 边界）。两者都 < 100,663,296 B（分区容量）。
