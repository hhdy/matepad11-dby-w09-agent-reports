# K1_DBY_W09_UBOOT_CHAINLOADER_ONEPASS01 — 综合报告（§12 续行更新版）

- 首版 commit `361f3894`；本版为 §12 授权后的一次性构建续行更新 + §13 控制设计纠错（2026-11-28）
- §12 授权：用户明确授权 Ubuntu 24.04 主机 APT 安装构建依赖 + 主机端源码固定/构建/FIT 组装/离线验证；**非设备操作授权**
- 全程无设备连接、无设备侧读取、无 reboot/临时启动、无分区写入/刷写、无 AVB/vbmeta 修改、无原始固件上传
- **CoWave `pack-recovery.sh`（blob `0f3076bc…`）被禁止运行：该脚本使用 AVB flags=2 关闭校验，违反"不得修改/关闭验证"边界——本任务未运行它**

## 1. 环境与工具（§12.1）

- Ubuntu 24.04 noble（WSL2），679 GB 可用，12 核，7 GB RAM
- 安装（APT --no-install-recommends）：`gcc-aarch64-linux-gnu`、`device-tree-compiler`、`u-boot-tools`、bison/flex/libssl-dev/libgnutls28-dev/libncurses-dev/python3-dev/python3-setuptools/python3-pyelftools/swig/pkg-config/bc
- 版本：aarch64-linux-gnu-gcc **13.3.0**；dtc **1.7.0**；mkimage **2025.10**；host gcc 13.3.0

## 2. CoWave 源码固定（§12.2）

- Repo `CoWave-Fall/linux-on-arm-matepad11`，checkout **`b76d7e095104fc2a010f2d1dc43121a9e3484464`**，tree `2d6b79e3df31bfad1001da6e565a155794b5e7f7` ✓（与任务书一致；commit 未签名——记录，不声称签名验证）
- blob SHA 核验：defconfig `38a39ecd…` ✓、build-uboot.sh `bb1e94b8…` ✓、pack-fit.sh `529bebcf…` ✓、fetch-sources.sh `a640962b…` ✓、pack-recovery.sh `0f3076bc…` ✓（均与 §12.2 表一致）；patches 目录 tree `a4440e3c…`（5 个补丁按顺序 `patch -p1` 全部应用成功，PATCHES_APPLIED）
- 未运行 `fetch-sources.sh`（其会抓 Linux 7.3.4）；仅按固定 SHA 取 U-Boot v2026.10

## 3. U-Boot v2026.10 获取与构建（§12.3–12.4）

- 源码包 `u-boot-v2026.10.tar.gz`（github u-boot tag v2026.10），SHA-256 **`f943a883…b60c739` 校验通过**（与任务书/CoWave fetch-sources.sh 一致）
- 5 补丁应用成功；`make O=build CROSS_COMPILE=aarch64-linux-gnu- dby-w09_defconfig`
- **§12.4 显式配置调整**：`CONFIG_CMD_ABOOTIMG` defconfig 未含且默认未启（AI1 预判正确）→ 追加 `CONFIG_CMD_ABOOTIMG=y` + `olddefconfig` 重生成
- **最终 .config 实测值**（非推断）：

```
CONFIG_POSITION_INDEPENDENT=y      CONFIG_INIT_SP_RELATIVE=y
CONFIG_SYS_INIT_SP_BSS_OFFSET=0x180000
CONFIG_ARCH_SNAPDRAGON=y           CONFIG_NR_DRAM_BANKS=24
CONFIG_DEFAULT_DEVICE_TREE="qcom/sm8250-huawei-dby-w09"
CONFIG_SYS_BOOTM_LEN=0x8000000     (128 MiB 解压上限)
CONFIG_ANDROID_BOOT_IMAGE=y        CONFIG_ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR=y
CONFIG_FIT=y                       CONFIG_CMD_BOOTM=y
CONFIG_OF_LIBFDT=y                 CONFIG_OF_BOARD_SETUP=y
CONFIG_SAVE_PREV_BL_FDT_ADDR=y     CONFIG_SAVE_PREV_BL_INITRAMFS_START_ADDR=y
CONFIG_CMD_ABOOTIMG=y              CONFIG_USB_FUNCTION_FASTBOOT=y
```

- 构建成功（-j12）：`u-boot` ELF 10,619,264 B sha `e0f24a18…93ad60`；`u-boot.bin` 1,548,760 B sha `f6dd2ae7…d99753`；`u-boot.map` sha `949cb0f4…fbcbcb`
- PIE/ELF 审计：Type=**DYN**（PIE ✓）；Entry point **0x0**（PIE 相对入口，4 KiB 对齐 ✓ 平凡满足）；relative relocation 条目 6,675 行段
- **ADB 交接路径就绪**：`CMD_ABOOTIMG=y` + `ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR=y` + v0–v2 parser（AI1 源码闭环）→ `abootimg addr <wrapper>` + `bootm <FIT> <wrapper>`（禁冒号形式）

## 4. FIT 组装与验证（§12.5）

- 输入身份（重算）：ACK Image `prep_kernel.bin` sha `f89a2839…bad21`（44,820,992 B）；VD DTB `prep_dtb.bin` sha `7bb9a1fb…996b7`（1,216,399 B）；gzip -6 → `Image.gz` 17,860,410 B
- ITS：kernel（gzip，load/entry=0x91000000，**CoWave 参考地址，CONDITIONAL**——最终 RAM map 未捕获不作为本机已证布局）+ fdt（load=0x96000000，位于解压末端 0x93D80000 之上，无重叠）；配置名 `conf-dby-w09-vd`；**未写入任何 RAM tuples**
- **完整 FIT 实际生成**：`dby-w09-ack.itb` = **19,078,551 B（18.20 MiB）≤ reserved3 25,165,824 B（24 MiB）→ 容量 PASS（真实文件）**
- `mkimage -l` / `dumpimage -l` 结构解析 PASS：Kernel Image/gzip/17.03 MiB/AArch64/Load=Entry=0x91000000；Flat Device Tree/uncompressed/1.16 MiB/Load=0x96000000；默认配置 conf-dby-w09-vd ✓

## 5. Android v0 外置 ramdisk wrapper（§12.5.5）

- live wrapper `4dd6d91a…cfdbb` 本轮未重传；ADDENDUM01 实测：v0 头、payload@0x800 长 1,406,106、gzip→cpio newc（init/init.real/ksu.ko）
- 路线核验：最终 .config `CMD_ABOOTIMG=y`+`IGNORE_BLOB_ADDR=y`（§3）+ AI1 v0–v2 parser 源码闭环 + 本地字段算术一致 → **wrapper 解析路径 = CONFIRMED（config+source 级）**；sandbox bootm 实测未运行（无沙箱环境落盘）→ 标 PARTIAL
- 原始 ramdisk/CPIO 未上传 ✓

## 6. 六份 recovery 备份 provenance —— 已闭环（§12.6）

r155 `capture_manifest.tsv`（设备侧双次 SHA + 主机回读四列，label→/dev/block/by-name 精确对应）证明：

| label | 块设备 | 设备侧 SHA（双次一致） |
|---|---|---|
| recovery | sda19/by-name/recovery | `95641758…1c5548` |
| erecovery | sda16/by-name/erecovery | `95641758…1c5548`（**真机内容本就相同**） |
| recovery_ramdisk | sda20 | `b6fa0371…2295`（== erecovery_ramdisk sda17） |
| erecovery_ramdisk | sda17 | 同上 |
| recovery_vbmeta | sda24 | `bf59d55d…507b`（≠ erecovery_vbmeta `ed04c848…`） |
| erecovery_vbmeta | sda23 | `ed04c848…6c73f` |

**结论：重复哈希是 HOS4.3 出厂内容本身（recovery 与 erecovery 主镜像/ramdisk/vendor 逐字节一致，仅 vbmeta 不同），非采集错误。** 六文件各自独立双次设备侧验证 + 主机回读一致 → **`RECOVERY_WRITE_SURFACE_BACKUPS = COMPLETE`**（GATE02 的 INCOMPLETE 升级）。

## 7. 认证门禁（§11.6，保持谨慎）

LoadImageAndAuth/VB2 路径存在；对 recovery 容器替换 kernel 后能否通过既有认证 = **UNKNOWN**（与前轮一致）。若需 OEM 私钥/vbmeta 修改 → AUTH_BLOCKED。未生成 recovery 候选。

## 8. 最终门禁（§7）

| 门 | 值 | 变化 |
|---|---|---|
| HOST_PACKAGE_READINESS | **READY**（U-Boot 构建 ✓ 17 项 config ✓ PIE ✓；FIT 真实文件 ✓ 19,078,551 B ≤ 24 MiB ✓ 解析 ✓；wrapper 解析路径 config+source 级 ✓；残留：sandbox bootm 实测 PARTIAL） | BLOCKED → READY |
| DEVICE_BOOT_READINESS | **HOLD**（备份 COMPLETE↑；但 entry chain CONDITIONAL、initrd label PARTIAL、RAM/final-FDT UNKNOWN、认证 UNKNOWN、reserved-memory 37 节点对照未做） | NO_GO → HOLD |
| USER_AUTHORIZATION_GATE | **AUTHORIZATION_REQUIRED**（final-FDT 只读 capture 为 RAM/reserved 唯一权威证据） | 不变 |
| **ONEPASS_RESULT** | **HOST_READY_DEVICE_HOLD** | PARTIAL_BLOCKED → 升级 |

**HOST_READY_DEVICE_HOLD 不是刷写授权。** 设备侧任何操作（含 final-FDT 只读采集）须用户另行明确授权（§11.7/§11.8 预置流程适用）。

## 9. 残留未闭合项（最小证据）

1. recovery→BootLinux 两级调用链：blr 根数据流 pass（静态）
2. recovery initrd label/payload form：LoadRamdisk 调用者参数窗（静态）
3. ABL `/memory/reg`、memreserve、reserved-memory：final-FDT capture（设备只读，需授权）
4. reserved-memory 37 children 对照：final-FDT capture 后进行
5. sandbox bootm 命令路径实测（可选 host 项）
6. 认证行为：ABL 对 recovery 容器的 AVB 判定（静态或授权后验证）

## 10. 二进制不入库声明

U-Boot ELF/bin/map、FIT itb、gzip Image、DTB、wrapper ramdisk 及全部原始固件**仅存本地**（`/home/kerneldev/build/`、workspace `UBOOT_CHAINLOADER_ADAPT01/fit/`），GitHub 仅上传本脱敏报告与脚本清单 ✓

## 13. 设计纠错（控制 FDT 静态 RAM tuples / framebuffer reservation）— 已完成

**发现确认**：CoWave `0004-dts-qcom-add-dby-w09.patch`（本地树 `dts/upstream/src/arm64/qcom/sm8250-huawei-dby-w09.dts` L35-40）在内部控制 FDT 写入三段静态 RAM tuples（0x80000000+0x3BB00000、0xC0000000+0xC0000000、0x180000000+0x100000000，≈7.93 GiB）+ `cont-splash@9C000000`/35 MiB no-map + `simple-framebuffer@9C000000`（1600×2560, stride 6400, a8r8g8b8）。`board_fdt_blob_setup()`（`arch/arm/mach-snapdragon/board.c` L212-226）优先解析内部 FDT 的 memory 信息——若内部 `/memory/reg` 有效非零，`SAVE_PREV_BL_FDT_ADDR=y` 也不会走 previous-BL 路径。

**纠错执行**（本地纠错，不改 CoWave pristine）：
1. 删除控制 DTS 的静态 `memory { reg = 三段 tuples }` 节点（保留其余控制节点）；纠正后源 sha256 `fd4f3bde…c3b2981a`。
2. 重建：`MAKE_EXIT_CODE=0`（显式捕获，无管道掩码）；重建产物：
   - `u-boot` ELF sha **`d0d85843…b025162123`**
   - `u-boot.bin` sha **`33741739…3f3e46`**
   - `u-boot.map` sha `949cb0f4…`（不变）
   - `u-boot.dtb` sha **`e522efd2…680fab`**
   - `.config` sha `6faf3b40…`（配置未变）
3. **编译产物核验**：重建后 `u-boot.dtb` **根级 `/memory` 节点消失（decompile count=0）** → 内部 `qcom_parse_memory()` 无有效 `/memory/reg` → 按已源码闭环逻辑返回 `-ENODATA` → `board_fdt_blob_setup()` 走 `get_prev_bl_fdt_addr()` external FDT 路径（fallback 源码证据：board.c L213-224，internal/external 双有效性检查，internal memory 优先仅在存在时生效）。**SAVE_PREV_BL_FDT_ADDR 现在真实生效。**
4. **reserved-memory / framebuffer 逐项标记（未取得 HOS4.3 final-FDT 前一律 CONDITIONAL/UNPROVEN，不声称安全）**：

| 节点 | 范围 | 属性 | 判定 |
|---|---|---|---|
| cont-splash@9C000000 | 0x9C000000 + 0x2300000 (35 MiB) | no-map | **CONDITIONAL-UNPROVEN**（CoWave HOS4.2 splash 记录；本机 XBL splash 配置未捕获） |
| framebuffer@9C000000 | 同上 | simple-framebuffer 1600×2560 a8r8g8b8 | 同上 |
| memory@80000000 | 0x80000000 + 0x600000 (6 MiB) | no-map | sm8250.dtsi 标准 Qualcomm carveout（zap/removed-mem 类）**CONDITIONAL** |
| memory@80700000 | +0x160000 (1.4 MiB) | no-map | 同上 **CONDITIONAL** |
| memory@80860000 | +0x20000 (128 KiB) | no-map | 同上 **CONDITIONAL** |
| memory@80900000 | +0x200000 (2 MiB) | no-map | 同上 **CONDITIONAL** |

   这些节点影响 U-Boot 自身 LMB 保护行为，**不影响 ABL→U-Boot 的真实 RAM map 来源**（后者由 prev-BL external FDT 提供）。设备侧 final-FDT capture 后逐项 MATCH/DIFFERENT 复核。

## 14. recovery_ramdisk 哈希澄清（响应审计质询）

- "旧 SHA `1a703a84…`"为**无效串**：来自一次终端管道中断的 62 字符截断输出（非真实哈希），从未进入任何报告正文。
- 干净重算（本轮）：本地 `r155/copies-primary/recovery_ramdisk.img` 37,748,736 B sha256 = **`b6fa0371…2295`**，与 `capture_manifest.tsv` 的 sda20（by-name/recovery_ramdisk）设备侧双次 SHA 逐字一致；erecovery_ramdisk 同值（出厂内容相同，§6）。**无实际差异。**

## 15. 验证严谨性补强（响应审计质询）

- 重建退出码显式捕获：`MAKE_EXIT_CODE=0`（无 `| tail` 掩码；失败分支会直接输出日志尾并退出非零）。
- `dumpimage -l`（FIT `dby-w09-ack.itb`）退出码 **0** 显式验证。
- FIT 本体不受本纠错影响（FIT 内含 ACK DTB，非 U-Boot 控制 DTB）；19,078,551 B ≤ 24 MiB 结论不变。

## 16. 门禁更新（纠错后）

| 门 | 值 | 说明 |
|---|---|---|
| HOST_PACKAGE_READINESS | **READY**（维持；控制 FDT 已去除静态 RAM，prev-BL fallback 为已证实路径） | — |
| DEVICE_BOOT_READINESS | **HOLD**（维持：entry chain CONDITIONAL、initrd label PARTIAL、RAM/final-FDT UNKNOWN、认证 UNKNOWN、reserved-memory 对照 CONDITIONAL 待 capture） | 纠错通过前不解除 |
| USER_AUTHORIZATION_GATE | **AUTHORIZATION_REQUIRED** | — |
| ONEPASS_RESULT | **HOST_READY_DEVICE_HOLD** | — |
