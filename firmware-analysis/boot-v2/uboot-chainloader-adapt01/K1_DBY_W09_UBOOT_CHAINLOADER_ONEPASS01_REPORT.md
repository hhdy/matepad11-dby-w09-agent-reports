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

## 17. §17 final-FDT 只读采集 —— **SUCCESS**（2026-11-29 补采完成）

首轮尝试设备处于 Fastboot（BLOCKED）；用户将平板手动重启回 HOS4.3 并连接 ADB 后，按 §17.3 完成补采。

### 17.0 设备身份（五个允许字段，全部匹配目标）

| 字段 | 值 |
|---|---|
| ro.build.fingerprint | HUAWEI/DBY-W09/HWDBY:12/HUAWEIDBY-W09/104.3.0.196C00:user/release-keys |
| ro.build.version.release | 12 |
| ro.build.version.incremental | 104.3.0.196C00 |
| ro.product.device | HWDBY |
| ro.boot.hardware | qcom |

### 17.0.1 FDT 身份

- 本地路径：`final-fdt-capture/hos43-final-fdt.dtb`（**仅本地，不上传**）
- 字节数：**800,324**（与设备侧 `/sys/firmware/fdt` 文件大小精确一致）
- SHA-256：**`dc0ab259c800d52946d4a3d633fe1546430895d2878054d0376d428a135da52d`**
- header：magic **0xD00DFEED** ✓；totalsize=800,324（==文件长 ✓）；off_struct=0x38；off_strings=0xB1CD4；off_memrsv=0x28；version=17 / last_comp=16
- 采集方式：`adb exec-out su -c 'cat /sys/firmware/fdt'`（KernelSU root，`u:r:ksu:s0`，静默授权，无弹窗、无策略修改）

### 17.0.2 RAM banks（§17.4.B）

`/memory` **存在且非零**（节点名 `memory`，无 @ 后缀；`ddr_device_type=0x7`）。reg 12 cells = 3 banks：

| bank | base | size | end | 备注 |
|---|---|---|---|---|
| 0 | 0x0000000080000000 | 0x39900000 (921.6 MiB) | 0xB9900000 | — |
| 1 | 0x0000000200000000 (8 GiB) | 0x0000000200000000 (8 GiB) | 0x280000000 | — |
| 2 | 0x00000000C0000000 (3 GiB) | 0x00000000C0000000 (3 GiB) | 0x180000000 | — |

**TOTAL = 12.17 GiB（12GB 设备 ✓）**；零长度=0、重叠=0、已排序 ✓。**与 CoWave 8GB 三 tuples 确认不同**（real bank1=0x200000000+8G vs CoWave 0x180000000+4G；bank0 尺寸 921M vs 951M）——纠错删除静态 tuples 的决策再次被证实。

### 17.0.3 memreserve / reserved-memory（§17.4.C）

- **memreserve entries = 0**（FDT 根 memreserve map 为空 → initrd 无 FDT 级保留）
- **/reserved-memory children = 37**（与任务书预期数精确一致 ✓）。关键项：hyp/xbl_aop/cmd-db/res_xbl_uefi_log/smem/removed_region(+0x5300000)/pil_{camera,wlan,ipa_fw,ipa_gsi,gpu,npu,video,cvsp,cdsp,slpi,adsp,spss}/cdsp_secure_heap；共享池类（reusable）：adsp/sdsp/cdsp/mem_dump/sp/user_contig/qseecom/qseecom_ta/secure_display/cnss_wlan/linux,cma/mailbox；显示类：**cont_splash_region@9C000000+0x2300000（35 MiB 真实存在 ✓，无 no-map 属性）**、disp_rdump@9C000000+0x800000（同基址重叠，厂商定义）、dfps_data@9E300000；华为私有：rainbow_mem@B0000000+4M(no-map)、bootfail_mem@B0400000+2K(no-map)、kerneldump(reg 动态)。完整 37 项表在 `evidence_final_fdt_parse.txt`。

### 17.0.4 chosen initrd（§17.4.D）

- `linux,initrd-start = 0x00000000F0000000`；`linux,initrd-end = 0x00000000F015749A` → **长度 = 0x15749A = 1,406,106 B = live separate ramdisk gzip payload 精确值（ADDENDUM01）✓✓**
- **结论：ABL initrd = separate ramdisk 分区的 gzip payload（wrapper 已剥离），放置 0xF0000000（bank2 内）** —— 审计 B 的 initrd 来源与 payload form 由 final-FDT 直接证实（RECOVERY 路径仍 CONDITIONAL，此为 HOS normal 路径证据）。
- **重叠算术**：initrd 区间落在 bank2 [0xC0000000,0x180000000) 内部偏移 0x30000000，与全部 37 个 reserved-memory children 及 cont_splash 无重叠 ✓；但 **memreserve=0、initrd 无 FDT 级保留** → `SAVE_PREV_BL_INITRAMFS_START_ADDR` 只能取 start，end 未保存，LMB 保护需 U-Boot 侧自行处理（不得声称已保留）。
- bootargs 存在（长度已记录，内容不公开）。

### 17.0.5 对照结果（§17.4.C 对照要求）

| 对照 | 结果 |
|---|---|
| U-Boot 控制 DTB cont-splash@9C000000+0x2300000 | **base/size MATCH**（final-FDT cont_splash_region 同值）；**属性 DIFF**（final 无 no-map，U-Boot 控制侧声明 no-map） |
| U-Boot 控制 framebuffer@9C000000 | 区域真实存在 ✓（与 disp_rdump 同基址共存）；simple-framebuffer 节点 final 中 ABSENT（HOS 不向 Linux 导出 fb 节点） |
| U-Boot 控制 4 个 sm8250.dtsi carveout | **MATCH**（hyp/xbl_aop/cmd-db/smem 与 final 同 base/size/no-map） |
| ACK VD DTB 17 个直接 reg children | **MATCH**（base/size/no-map 与 final 对应 children 一致；ACK 即源自本设备 DTB） |
| final-FDT 独有（ACK ABSENT） | 显示类 3 + 华为私有 5 + 共享池 9 + kerneldump 等 ≈ 20 项 → ACK candidate 需按 §11.5 对照补齐/确认非重叠 |
| cdsp_secure_heap@8BF00000 | ACK=+0x4600000 固定 70M；final=reg 动态 → **DIFFERENT/UNKNOWN** |

### 17.0.6 fallback 判定（§17.4.E）

- **ABL_FINAL_FDT_RAM_SOURCE = PRESENT**（非零三 bank）
- **UBOOT_QCOM_EXTERNAL_FDT_FALLBACK_INPUT = usable**：控制 DTB 根 `/memory` 已删（纠错 §13）→ `qcom_parse_memory()` 内部路径 -ENODATA → `board_fdt_blob_setup()` 走 `get_prev_bl_fdt_addr()` external FDT → 该 FDT 含有效非零 RAM → U-Boot 将获得**真实 12GB map**（而非 CoWave 8GB tuples）
- 严格声明：这是**源码路径 + external FDT 输入可用性**的证明；**U-Boot 未在设备上运行**，不构成实机启动结果。
- initrd 注意：external FDT chosen 含 ABL initrd(0xF0000000)；若 U-Boot 采用该 FDT，`boot_fdt_add_mem_rsv_regions` 会保护 chosen 声明的区域；我们走 `abootimg`+FIT 路线时需避免与 0xF0000000–0xF015749A 冲突（FIT 目标区 0x91000000/0x96000000 与之无重叠 ✓）。

### 17.0.7 FINAL_FDT_CAPTURE = SUCCESS；RECOVERY 路径 FDT = UNKNOWN（本 capture 为 HOS normal 启动会话，不自动证明 recovery 模式相同）

## 18. 门禁更新（final-FDT 采集 SUCCESS 后）

| 门 | 值 | 说明 |
|---|---|---|
| HOST_PACKAGE_READINESS | **READY**（不变） | — |
| DEVICE_BOOT_READINESS | **HOLD**（保持——但多项 UNKNOWN 已解除：RAM map=PRESENT 12.17GiB 三 bank、external fallback input=usable、ABL initrd=separate ramdisk gzip payload 确认、reserved-memory 37 项已枚举；仍 HOLD 项：recovery entry chain CONDITIONAL、initrd label PARTIAL、recovery FDT UNKNOWN、认证 UNKNOWN、ACK 20 项 final-only 节点对照待补） | 采集前多项 UNKNOWN → 已解除 |
| USER_AUTHORIZATION_GATE | **AUTHORIZATION_REQUIRED**（final-FDT 只读授权已使用完毕；后续任何设备操作需新授权） | — |
| ONEPASS_RESULT | **HOST_READY_DEVICE_HOLD**（不变，但 HOLD 项数量显著减少） | — |

**声明：本轮仅执行 adb devices/getprop×5/exec-out su -c cat /sys/firmware/fdt（只读）；无重启、无模式切换、无分区读取、无写入/刷写、无 AVB/vbmeta 修改、无 /dev/mem 或旁路读取；原始 FDT 仅存本地未上传。**

## 19. 启动前最终纠错（2026-11-29 增量）

### 19.1 RAM bank 解析修正（fdtget 直读 + 全量解码）

fdtget 实读：/#address-cells=2、/#size-cells=2、/memory/reg 12 cells。根节点名为 `memory`（**无 @ 后缀**——§17.0.2 正则只匹配 memory@ 导致漏报，已修正）。按 4-cell 元组解码（reg 顺序**未排序**）：

| bank | base | size | end | 容量 |
|---|---|---|---|---|
| 0 | 0x0000000080000000 | 0x39900000 | 0xB9900000 | 921 MiB (0.899 GiB) |
| 1 | 0x0000000200000000 | 0x200000000 | **0x400000000** | 8.000 GiB |
| 2 | 0x00000000C0000000 | 0xC0000000 | 0x180000000 | 3.000 GiB |

**TOTAL = 12,776,898,560 B = 11.899 GiB**。§17.0.2 中『bank1 end=0x280000000』与『12.17 GiB』为错误值，以本表为准。排序：**reg 顺序未排序**（按地址序 bank0→bank2→bank1）；重叠=0；间隙=2（0xB9900000→0xC0000000 103 MiB；0x180000000→0x200000000 2 GiB）；零长度=0；溢出=0；top-level `memory`（无 @）节点 PRESENT。证据重生成：`evidence_final_fdt_parse.txt`。

### 19.2 initrd / LMB 论证修正

- `boot_fdt_add_mem_rsv_regions()`（boot/image-fdt.c）只把 **FDT /memreserve 与 /reserved-memory 固定 reg 节点**加入 LMB；**不读取 /chosen/linux,initrd-start/end** → ABL initrd（0xF0000000–0xF015749A）**不会被自动保留**。
- 四地址追踪：**ABL 原 initrd** = gzip payload @0xF0000000（1,406,106 B，bank2 内）；**U-Boot 选取的 ramdisk 数据** = FIT v2 内嵌 `ramdisk-payload.gz`（位于 reserved3 暂存 FIT 缓冲，由 U-Boot 自身读取）；**LMB 目标** = bootm 按 LMB 从最大 bank（0x200000000+8G）顶部向下分配（运行时确定）；**最终 Linux initrd 地址** = `fdt_initrd()` 写入 ACK FDT chosen 的 LMB 分配结果并加最终 reservation。
- 覆盖校验：FIT ramdisk 数据源 = reserved3 暂存缓冲（U-Boot 自管），**不源自 0xF0000000** → 无『搬移覆盖 ABL 原输入』问题；kernel/DTB 区 0x91000000–0x96000000 与 0xF0000000 无交叠 ✓。
- **不得把 `fdt_initrd` 对最终 initrd 的 reservation 误表述为 ABL 原 initrd 已提前保留**——该区域在 U-Boot 侧无自动保护。

### 19.3 wrapper/payload 不一致解决

- final-FDT chosen 0xF0000000 指向 **gzip payload 而非 v0 wrapper** → **禁止 `abootimg addr 0xF0000000`**。normal HOS 路径 RAM 中无完整 wrapper；recovery 路径能否提供 = PARTIAL/UNKNOWN → **CMD_ABOOTIMG 路线 = CONDITIONAL/BLOCKED**。
- **采用方案 B（FIT-native ramdisk）并实测**：FIT v2 `dby-w09-ack-v2.itb` 新增 ramdisk 子镜像（data = live wrapper 0x800 偏移提取的 gzip payload，sha `4f71768a…` 与 ABL initrd 字节级同源；compression=none 原样透传，保持与 ABL 行为一致）。**MKIMAGE_EXIT=0、DUMPIMAGE_EXIT=0（显式）**，三子镜像解析全 PASS。
- **FIT v2 实际尺寸 = 20,484,879 B ≤ 25,165,824 B（24 MiB）→ PASS，余量 4,680,945 B（4.46 MiB）**；sha256 `61e29c68…ef87024`。

### 19.4 reserved-memory 三向最终对照（final 39 正则项=38 实体+1 解析伪影；ACK 19；U-Boot ctrl 20）

**关键更正：ACK 的 `memory@X` 与 final 的 `*_region@X` 为同区域异名**——17 组按 base/size/no-map **全部 MATCH**（仅节点名不同）。完整三向表：`evidence_three_way.txt`。重点：

| 项 | final | ACK | U-Boot ctrl | 判定 |
|---|---|---|---|---|
| 17 组标准 carveout（hyp/xbl_aop/cmd-db/smem/removed/pil_×12） | *_region@X 同值 | memory@X 同值 | memory@X 同值 | **MATCH（异名）** |
| cont_splash_region@9C000000+0x2300000 | 有，无 no-map | ABSENT | cont-splash 同值带 no-map | MATCH(base/size) **属性 DIFF** |
| disp_rdump@9C000000+0x800000 | 有（与 cont_splash 同基址重叠） | ABSENT | ABSENT | FINAL-ONLY |
| cdsp_secure_heap@8BF00000 | 动态 reg（no-map） | 固定 +0x4600000 | 固定同 ACK | base MATCH / size **DIFFERENT** |
| 共享池 dyn 11 项（adsp/sdsp/cdsp/mem_dump/sp/user_contig/qseecom×2/secure_display/cnss_wlan/linux,cma/mailbox） | dyn | ABSENT | ABSENT | FINAL-ONLY（动态分配，ACK 由自身 CMA 供给） |
| rainbow_mem/bootfail_mem/mem_dump/dfps_data/kerneldump | 有 | ABSENT | ABSENT | FINAL-ONLY（华为服务，AOSP 链不需要） |
| framebuffer@9C000000 | ABSENT | ABSENT | 有 | U-ONLY |

**原则：ABL external FDT 用于 RAM bank 解析 ≠ 其 reserved-memory 自动进入 ACK FIT DTB。** ACK DTB 保留标准 17 组（语义明确）；final-only 动态池与华为服务节点不迁移；cont_splash（若 U-Boot 复用 splash）与 cdsp_secure_heap 实际尺寸两项留待实机验证。LMB：U-Boot 运行时应将 external FDT 的 17 个固定 /reserved-memory 加入 LMB；动态池无固定地址不进 LMB。

### 19.5 最终门禁

| 项 | 值 |
|---|---|
| U-Boot 运行时 RAM 来源 | **usable**（external FDT 三 bank 11.899 GiB；控制 DTB 无静态 RAM 已证） |
| kernel/FIT/FDT/ramdisk/U-Boot 区域重叠 | **静态无重叠**（kernel 解压区 0x91000000–0x93D80000；DTB 0x96000000 在其上；initrd 由 LMB 从 bank1 顶部分配；ABL initrd 0xF0000000 与全部目标区无交叠） |
| recovery 两级调用链 / initrd label | **CONDITIONAL / PARTIAL（维持）** |
| recovery 认证合法启动方式 | **UNKNOWN（维持）** |
| host/sandbox PASS vs 实机 PASS | 本报告全部为 **host 级证据**；无任何实机 PASS 声明 |

| 门 | 值 |
|---|---|
| HOST_PACKAGE_READINESS | **READY**（FIT v2 含 ramdisk，20,484,879 B ≤ 24 MiB，解析 PASS） |
| DEVICE_BOOT_READINESS | **HOLD**（不变：entry chain CONDITIONAL、initrd label PARTIAL、recovery FDT UNKNOWN、认证 UNKNOWN） |
| USER_AUTHORIZATION_GATE | **AUTHORIZATION_REQUIRED** |
| ONEPASS_RESULT | **HOST_READY_DEVICE_HOLD** |

**声明：本轮零设备操作——无连接、无 ADB/Fastboot、无重启、无分区读取/写入、无刷写、无 AVB/vbmeta 修改。** 原始 final-FDT 与全部二进制仅存本地，FIT v2 itb 不入库。
