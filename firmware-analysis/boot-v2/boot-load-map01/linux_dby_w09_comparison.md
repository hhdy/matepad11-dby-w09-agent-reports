# linux_dby_w09_comparison.md — svesnav/linux-dby-w09 有限对照（阶段 D）

范围：仅对照该参考项目对 boot image 组件地址、kernel 压缩格式、boot v2 头参数、DTB/ramdisk 载荷布局的真实构建参数；不重新审计其代码。原始文件已存档：`evidence/svesnav_repack_boot.py`、`evidence/svesnav_boot_cmdline.txt`。

## 事实

1. **kernel 格式 = Image.gz（压缩）**：`repack_boot.py --kernel` 帮助文本明示 "Replacement **compressed** ARM64 kernel"（第 35 行）。该项目的可启动性建立在 ABL 的 gzip 解压路径上。
2. **header 参数 = stock 原样**：用 AOSP `unpack_bootimg.py --format=mkbootimg` 从其 stock boot 备份提取 mkbootimg 参数（含 `--header_version 2` 校验，第 61–63 行），替换 kernel/dtb/cmdline 后用 `mkbootimg-android10.py` 重打包——**kernel_addr/ramdisk_addr/dtb_addr/tags_addr 全部保持 stock 值，无任何改动**。
3. **交付 = 96 MiB 全分区镜像**：`--full-partition` 模式将新 payload 前置写入 96 MiB 分区布局并零填充至 `STOCK_PAYLOAD_SIZE=24,412,160`（第 82–89 行），明示目的 "Preserve the stock 96 MiB partition layout"。
4. 其 stock boot 备份哈希 `6fb82f6c…539d` 与本地 r155 stock `7a95c897…4a8` **不同**（不同地区/批次固件）——仅行为对照，不作字节对照。
5. ramdisk：其镜像链使用 stock 头中的 ramdisk 载荷与 `dby-w09-rootparam.dtso`（repo 根）——DTBO 策略与本项目 CORR01 的 KEEP_STOCK 结论同向。

## 推论（为何不能外推到 ACK raw Image）

| 维度 | svesnav 项目 | PREP10 | 外推是否成立 |
|---|---|---|---|
| kernel 格式 | Image.gz → ABL inflate 路径，解压后尺寸远小于 96 MiB 缓冲 | raw Image → CopyMem 路径 | ✗ 不同代码路径 |
| text_offset 契约 | gz 内层 Image（与 stock 同族契约，2MB+0x80000 相容性沿用 stock 实证） | text_offset=0 + PHYS_BASE（2MB 对齐要求） | ✗ 契约不同（主报告 §5） |
| 交付尺寸 | 96 MiB 全分区（`fastboot boot` 下载缓冲≈分区 → R/D 开辟在 kernel 之上，避开 staging 溢出） | 46,563,215 B 原文件（`fastboot boot` 时 kernel 末端越过 R ≈318 KiB） | ✗ 其可启动性不能证明 PREP10 文件可 RAM boot |
| header 地址 | stock 原样（ABL 忽略） | stock 原样（ABL 忽略） | ✓ 一致（互相印证） |
| ramdisk | stock ramdisk 载荷 + rootparam dtso | separate ramdisk 分区作 initrd（stock 行为） | ≈ 同向 |

结论：参考项目 boots = "Image.gz + 96 MiB 全分区交付" 两个前提的组合效果；PREP10 在两个前提上都不同（raw + 原尺寸文件），因此其成功经验既不覆盖 §4 的 fastboot 溢出，也不覆盖 §5 的 text_offset 契约。该对照恰好为两项发现提供了独立佐证（第 3 条尤其直接）。
