# K1_DBY_W09_UBOOT_RECOVERY_CANDIDATE_BUILD01 — BUILD_RESULT

- 日期：2026-11-29；纯主机端（WSL Ubuntu-24.04，/home/kerneldev/build/rcand/）；**无设备操作、无分区写入、无 vbmeta 生成/修改、无 avbtool make_vbmeta**
- 注：任务书随附的 `pack_uboot_recovery_candidate.py` 在本机未提供（D:\Downloads 及全盘搜索无）——按任务书 §C 契约在本项目 scripts/ 内忠实实现（JSON 报告、无 avbtool、仅换 kernel、保留全部组件；发现 unpack `-0` 参数文件为 NUL 分隔 exec 格式，解析器已按此实现）

## 结论

```
HOST_RECOVERY_CANDIDATE      = PASS
SOURCE_RECOVERY_IDENTITY     = PASS  (capture_manifest.tsv: label=recovery sda19, 100,663,296 B, sha 95641758…1c5548; 本地重算逐字节一致)
UBOOT_BINARY_IDENTITY        = PASS  (纠错后构建 33741739…3f3e46, 1,548,664 B; 与任务书记录一致; 旧首版 f6dd2ae7 已排除)
HEADER_RECONSTRUCTION        = PASS  (全部不可变字段一致；唯一差异为 layout 派生字段，见下)
STOCK_COMPONENT_PRESERVATION = PASS  (ramdisk a4b94ff6… / dtb 5824389a… / recovery_dtbo 51a5d7b8… 逐字节一致; second=0 与原厂相同不存在)
KERNEL_GZIP_ROUNDTRIP        = PASS  (候选 kernel gunzip sha 33741739… == 最终 u-boot.bin 精确一致)
PARTITION_FIT                = PASS  (候选 27,926,528 B ≤ recovery 分区 100,663,296 B；尺寸来自 §17 已核 capture_manifest 与 partition_map 证据，未读设备)
VBMETA_COMPATIBILITY         = UNKNOWN（本任务不生成/修改 vbmeta；只读解析见下）
DEVICE_BOOT_TEST             = NOT_RUN
```

## 头字段对照（原厂 vs 候选）

一致项：magic=ANDROID!、header_version=**2** ✓、header_size=1660、page_size=4096、kernel_addr=0x8000、ramdisk_addr=0x2000000、tags_addr=0x100、dtb_addr=0x1F00000、os_version=11.0.0 / patch=2020-11、second=0、ramdisk_size=519,986、dtb_size=1,664,243、recovery_dtbo_size=25,165,824、cmdline（cowave 模式 == 原厂全文一致——CoWave recovery cmdline 即原厂 cmdline）。

**唯一差异（预期、layout 派生）**：`recovery_dtbo offset` 原厂 0x15BA000 → 候选 0x10B000。原因：kernel 由 22,254,704 B（gz HOS）替换为 567,203 B（gz U-Boot），mkbootimg 按 v2 布局公式重算 recovery_dtbo 在镜像内的位置；**recovery_dtbo 内容 25,165,824 B 逐字节保留（sha 51a5d7b8…70c0c，即 dtbo 分区镜像本体）**。语义未变，仅位置字段随布局移动。

## recovery_vbmeta 只读解析（不生成新 vbmeta）

libavb 1.0；Algorithm SHA256_RSA2048；Rollback Index 0；**Flags=0**（无 DISABLED 位）；Release 'avbtool 1.1.0'；Descriptors: **Chain Partition descriptor → Partition Name: recovery，Rollback Index Location: 23**。含义：recovery_vbmeta 以链式描述符引用 recovery 分区——候选 kernel 被替换后能否通过该链 = 取决于设备端 ABL/AVB 对 recovery 分区的具体校验形态，**本任务不判定、不修改**。

## TWRP 登记（仅哈希，未触碰）

`<local-twrp-backup-path>` sha256 `d24331b5…5ad591`（33,121,159 B）。

## 交付物（全部本地，未上传任何二进制）

- `/home/kerneldev/build/rcand/recovery-uboot-candidate.img`（27,926,528 B，sha `b48e9185…811990`，UNSIGNED / NOT FOR DEVICE）
- `recovery-uboot-candidate.img.report.json`、`stock-recovery-unpack-info.txt`、`stock-mkbootimg-args.txt`（NUL 分隔 exec 格式）、`candidate-unpack-info.txt`、`component_hashes.tsv`、`SHA256SUMS`
- Windows 侧镜像目录：`UBOOT_CHAINLOADER_ADAPT01/scripts/`（packer + 全部构建脚本）

## 残留/未知

- 认证兼容性 UNKNOWN（AVB 链对替换 kernel 的行为需设备侧证据或 ABL 静态判定，另行授权）
- recovery 分区 label provenance：capture_manifest 四列全一致（sda19/by-name/recovery 双读+回读）；erecovery 与 recovery 内容相同为出厂事实（§17 已解）
