# DBY-W09 / HarmonyOS 4.3 初步审查记录

日期：2026-11-23  
审查来源：`hhdy/matepad11-dby-w09-agent-reports` 的 `main` 分支现有只读采集报告  
范围：静态审查现有报告；未连接设备、未下载或修改固件二进制、未执行刷写。

## 结论摘要

1. 实机当前运行的是 HarmonyOS 4.3 移植环境：系统属性显示 Android 12 / API 31，内核为 `4.19.157-perf+`。Vendor fingerprint 显示其基础供应商构建为 Android 11 / SDK 30 系列。后续必须以实际 Vendor、VINTF、HAL、固件和内核模块为准，不能把 System API 31 当成完整 Vendor 兼容等级。
2. 当前实机是 Qualcomm KONA / SM8250 平台。已读到 `soc_id=356`、`revision=2.1`、`machine=KONA`、`chip_name=SM8250`。这足以确认 SM8250 平台族，但仅凭当前属性和 cpufreq 上限，尚不能严谨地区分 SM8250 与 SM8250-AC。暂不把“865”或“870”写死到 DTS。
3. 当前实机分区布局没有 `vendor_boot` 或 `init_boot`，却有单独的 `ramdisk`、`boot`、`dtbo`、`recovery_ramdisk` 和多套 `vbmeta_*`。这不是可直接套用标准 Pixel GKI 打包流程的布局。
4. 4.3 固件清单中有约 6.78 GiB 的 `super.img`；设备上 `vendor`、`odm`、`system`、`cust`、`hw_product` 映射为 dm 逻辑设备。当前固件检查只上传了文件清单和 SHA-256，没有上传镜像二进制，因此还没有解析 boot header、ramdisk 内容、DTBO 表或 super 逻辑分区元数据。
5. live FDT 文件大小约 800,316 bytes，但 ADB shell 无权读取。设备树目录清单可以看到 `rootparam` 和大量华为特有节点。下一阶段应从本地固件镜像离线提取 boot/DTBO/DTS 信息，不应尝试在设备上 chmod 或提权读取。
6. 现有 ADB 采集记录显示，设备端没有进行重启、root、fastboot、EDL、分区读取或分区写入。保持这一安全边界。

## 已核对的证据

### 设备与运行环境

- 型号：`DBY-W09`，设备代号 `HWDBY`
- 平台：`ro.board.platform=kona`，`ro.soc.model=SM8250`，`soc0/machine=KONA`
- SoC 属性：`soc_id=356`，`revision=2.1`，`chip_name=SM8250`
- Android 运行时属性：`ro.build.version.release=12`，`ro.build.version.sdk=31`
- Vendor 属性：Vendor build fingerprint 指向 Android 11 / SDK 30 系列
- 内核：`4.19.157-perf+`；构建时间显示为 2024-08-30
- 当前 cpufreq policy max：1,804,800 / 2,419,200 / 2,841,600 Hz
- 内存：`MemTotal` 约 11.4 GiB；报告还显示有 CMA 保留区

**重要修正：** 2.8416 GHz 是当前运行内核报告的 policy 上限，不是对芯片硬件最大频率的独立测量。电源策略、设备树 OPP、温控、移植系统的限频都会影响这个值。需要结合离线 DTB 的 `qcom,msm-id`、`qcom,board-id`、SoC raw ID/version、PMIC/board ID 以及可信硬件资料再确认具体 bin/AC 型号。

### 当前分区与镜像布局

当前 `/dev/block/by-name` 清单中有：

- 启动相关：`boot`、`ramdisk`、`dtbo`
- 恢复相关：`recovery`、`recovery_ramdisk`、`recovery_vendor`、`recovery_vbmeta`、`erecovery*`
- 验证链：`vbmeta`、`vbmeta_cust`、`vbmeta_hw_product`、`vbmeta_odm`、`vbmeta_system`、`vbmeta_vendor`
- 动态分区：`super`，以及运行时的 `system`、`vendor`、`odm`、`cust`、`hw_product` dm 映射

报告中未发现 `vendor_boot`、`init_boot`、`vendor_dlkm`、`system_dlkm` 等标准 GKI 分区名。注意：ADB 下某个挂载路径不存在，不等于整个固件绝对没有相应目录或逻辑分区；需要用 super 元数据和镜像本身进一步确认。

### HarmonyOS 4.3 固件文件清单

本地提取目录：`D:\\workbuddy\\2026-11-23-22-29-12\\MatePad11_HOS43_LocalCheck_20261123_230849`

清单显示 43 个镜像条目。已在本地白名单复制并计算 SHA-256 的 11 个文件为：

- `boot.img`（100,663,296 bytes）
- `dtbo.img`（25,165,824 bytes）
- `ramdisk.img`（2,097,152 bytes）
- `recovery.img`（100,663,296 bytes）
- `recovery_ramdisk.img`（33,554,432 bytes）
- `vbmeta.img`、`vbmeta_cust.img`、`vbmeta_hw_product.img`、`vbmeta_odm.img`、`vbmeta_system.img`、`vbmeta_vendor.img`

未复制的大镜像包括 `super.img`（7,114,729,004 bytes）、`preload.img`、`cache.img`。其中 `vendor.img` / `odm.img` 不在独立文件清单中，预计位于 `super.img` 逻辑分区内，仍需 `lpdump` 核验。

脚本首次运行因目标路径安全检查 bug 复制 0 个文件；Agent 在工作副本修正两处路径分隔符后第二次运行，成功复制 11 个白名单文件。原始下载目录中的脚本没有被修改。修复过程已在 `firmware-hos43/SCRIPT_FIX_NOTE.txt` 记录。

### Vendor 与内核模块的初步观察

第一轮设备报告显示：

- `/vendor/etc/vintf/manifest.xml` 存在，约 34.9 KB
- `/vendor/etc/vintf/compatibility_matrix.xml` 存在
- VINTF manifest 目录中出现 QTI Display、USB、Wi-Fi、Thermal、Neural Networks、Keymaster、Lights、Huawei Sensors 等服务声明
- `/vendor/lib/modules` 中观察到 `gspca_main.ko`、`lcd.ko`、`llcc_perfmon.ko`、`mpq-adapter.ko`、`mpq-dmx-hw-plugin.ko`、`msm_11ad_proxy.ko`、`rdbg.ko`、`rmnet_perf.ko`、`rmnet_shs.ko`、`wigig_sensing.ko`、`wil6210.ko`
- 当前报告中 `/vendor_dlkm`、`/system_dlkm`、`/odm/lib/modules` 挂载路径不存在

这些只是路径和目录清单，不等于完整的驱动清单；还需读取 `modules.load`、`modules.dep`、`modules.softdep` 和 `/proc/modules`，并检查 super 内 vendor/odm 的真实内容。

## 对 Android GKI 6.18.33 方案的影响

- 不能将当前 4.19.157 厂商模块直接装入 6.18.33 内核。模块必须针对目标内核重新构建，并核对 KMI、符号依赖、签名、加载顺序和 ABI。
- 原厂 Vendor/System 组合是 Android 11 Vendor + Android 12 System 的线索；目标 DerpFest Android 17 的 VINTF、VNDK、HAL 和 Vendor API 兼容性尚未验证。不能因 ROM manifest 有 Android 17 分支就宣称可直接复用这套 Vendor。
- 启动链打包和 A/B、AVB、vbmeta descriptor、rollback index 处理必须以实机和固件解析结果为依据。当前还不能生成可刷写 boot 镜像。
- 应把设备专属驱动适配与 GKI 核心分开，优先研究 vendor modules/KMI 方案；若 Huawei 驱动依赖大量 4.19 下游私有 API，则需要估算移植/替换成本。
- 华为专有 rootparam/DTBO 机制是启动兼容性重点，不可省略或用通用 DTBO 替代。

## 安全与隐私问题

公开的 `round1-adb/adb_device_report.txt` 中，`adb devices -l` 一行仍保留了实机序列号，与 README 中“序列号已脱敏”的描述不一致。应立即将仓库设为 Private，并在重新公开前清理此文件以及 Git 历史。单纯删除文件或在新提交中覆盖文本，不会让旧 commit/blob 自动从公开历史消失。

此外，仓库的 `PUSH_INSTRUCTIONS.txt` 建议将 PAT 直接写进 remote URL。不要继续采用这种做法，因为 Token 可能留在 `.git/config`、命令历史、进程列表或日志中。优先使用 Git Credential Manager / `gh auth login`，或者使用 GitHub App/OAuth 授权。聊天中已经暴露的 PAT 必须撤销，不要复用。

## 下一阶段

执行仓库内 `agent-tasks/ROUND3_HOS43_IMAGE_METADATA.md`。重点获取 boot/ramdisk/DTBO/vbmeta/super 的离线元数据和 Vendor VINTF/fstab/module 清单。只上传文本报告、脱敏 XML/配置和 SHA-256；不上传完整 6.8 GiB super、不上传设备身份/校准分区、不执行固件包中脚本、不刷写设备。
