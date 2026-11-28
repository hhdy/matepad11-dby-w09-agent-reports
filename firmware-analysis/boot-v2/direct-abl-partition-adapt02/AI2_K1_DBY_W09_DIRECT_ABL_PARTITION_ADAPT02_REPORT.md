# AI2 ADAPT02 修订结论（2026-11-28）

只读研究。设备未连接；未运行 ADB/Fastboot；未修改源码、编译、制作镜像或写分区。

## 最终字段

- SVESNAV_REFERENCE_IDENTITY=PASS（12 个冻结文件 blob SHA 全部匹配）
- ABL_FASTBOOT_BOOT_REFUSAL=REPORTED（项目 README 报告；未做设备实测）
- STOCK_BOOT_V2_REPACK_METHOD=CONFIRMED（参考脚本解包 stock v2、替换 kernel/DTB/cmdline、AOSP mkbootimg 重建）
- SVE_KERNEL_PAYLOAD_FORMAT=IMAGE_GZ
- SVE_UNCOMPRESSED_TEXT_OFFSET=0x80000（arm64 协议预期；未直接测量 release 二进制）
- ABL_GZIP_KERNEL_DEST_OFFSET=0x80000
- PREP10_RAW_ALIGNMENT=UNKNOWN
- ACK_IMAGE_GZ_ALIGNMENT=UNKNOWN
- ACK_SOURCE_ADAPTATION_NEEDED=UNKNOWN
- ANDROID_RAMDISK_POLICY=KEEP_STOCK
- VD_DTBO_POLICY=KEEP_STOCK_VD_ENTRY2
- BOOT_PARTITION_SIZE_CHECK=PASS（PREP10 46,563,215 B 小于 96 MiB；只证明容量）
- SEPARATE_RAMDISK_AVB_FOOTER=VERIFIED（引用既有离线审计，本轮未重读原始分区）
- WRITE_READBACK_ROLLBACK_PLAN=PARTIAL
- DIRECT_ABL_ACK_ANDROID=BLOCKED
- RECOMMENDED_NEXT_STEP=单独授权只读确定 ACK 尺寸 ImageBuffer 物理地址 modulo 2MiB 余数；或先由 AI1 独立审查条件性 head.S text_offset 源码修正。
- DEVICE_WRITE_PERFORMED=NO；DEVICE_CONNECTED=NO

## 对齐结论（本轮关键修订）

既有 Hybrid ABL load-map 反汇编证明 raw ARM64 Image 与 gzip inflate 两条路径都使用 KernelLoadAddress=ImageBuffer+0x80000；gzip inflate 目的地址相同。既有 ALIGN02-CORR01 修正后的真实调用链证明 ImageBuffer 来自 EFI gBS->AllocatePages(AllocateAnyPages, EfiBootServicesData, EFI_SIZE_TO_PAGES)，只保证 4KiB 页粒度，未发现 2MiB 对齐请求、掩码或二次搬移。

ACK commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9 的 Image header text_offset=0、flags=0xA。公式 (ImageBuffer_phys + 0x80000 - text_offset) mod 0x200000 = 0，故 ACK 要求 ImageBuffer_phys mod 2MiB=0x180000。stock text_offset=0x80000 要求余数 0。stock 成功只是运行时实例经验，不是 allocator 保证。ACK gzip 仍保留内层 text_offset=0，故所需余数仍为 0x180000；Image.gz 不会修复对齐。运行时余数未知，不能判 PASS。

ALIGN02-CORR01 曾提出 head.S L59 text_offset 槽 0→0x80000 的条件性源码方向；可能影响 __PHYS_OFFSET、relocations 和入口约定，必须先独立审查、完整重建和协议验证。本任务未修改或编译。

## 分区与 Android 适配

svesnav 是 Linux v7.0.14 + microSD ext4 Kubuntu。它的 busybox + sd_root_init.sh initramfs 会挂载 LINUX70ROOT 并 switch_root 到 Linux /sbin/init，不是 Android init。保留 Huawei separate ramdisk（既有证据含 init/init.real 与 KernelSU），也保留 boot 内 stock embedded ramdisk。bootconfig handoff、ACK Android 17 first-stage init/fstab/dynamic partitions/dm-verity 兼容性仍未闭环。

svesnav dby-w09-rootparam.dtso 是 VG（board-id 0x206a、boardid [8,2,9,8]、DBY_W09_VG），不能用于本机 VD。保留 stock VD DTBO Entry 2 和 androidboot.dtbo_idx=2 行为；ROUND159 已独立核验该组件的精确 VD rootparam 与静态 selector 证据，但不代表整包可启动。

参考 repack_boot.py 的 stock SHA 6fb82f6c... 与本机 stock boot SHA 7a95c897... 不同，禁止套用固定 hash guard。--full-partition 的 STOCK_PAYLOAD_SIZE=24,412,160 是脚本边界，不是分区容量；本机既有 boot-tail 审计记录 payload_end=24,449,024，差 36,864 B，且尾部全零/无 AVB footer。参考安装器会备份完整旧分区，但写后只校验写入前缀；无自动回滚，依赖人工恢复。既有本机 boot/ramdisk/DTBO 容量和备份 SHA 本轮只引用，未重新读取原始备份。

## 总结

架构有参考实现，但 ACK kernel alignment 与 Android first-stage/bootconfig 尚未闭环，因此 DIRECT_ABL_ACK_ANDROID=BLOCKED。下一步只做独立授权的只读 alignment 证据或源码方案审查；不制作镜像、不写分区。交 AI1 审核。