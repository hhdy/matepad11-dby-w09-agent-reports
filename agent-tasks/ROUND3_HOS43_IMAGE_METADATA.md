# ROUND3 — HarmonyOS 4.3 启动镜像 / super 元数据离线解析

**执行者：本地 Agent**  
**仓库：** `hhdy/matepad11-dby-w09-agent-reports`  
**分支：** `analysis/hos43-initial-triage`  
**安全边界：** 只读。不要连接设备；不要运行固件中的 BAT/EXE/脚本；不要刷写、解锁、重启、root 或修改分区；不要读取/上传 persist、modemst、fsg、oeminfo、RPMB、用户数据或设备密钥。  
**目的：** 解析已下载的 HarmonyOS 4.3 固件中的 boot、ramdisk、DTBO、vbmeta 和 super 元数据，建立 Android GKI 6.18.33 的启动集成依据。

## 0. 先做安全检查

- 公开仓库中 `round1-adb/adb_device_report.txt` 曾包含设备序列号。执行者不得将该文件原样复制到任何新报告。
- 用户已被提醒撤销聊天中暴露的 GitHub PAT。任务中不需要 PAT，也不应把 token 写入命令、remote URL、日志或报告。
- 推荐仅在本地工作目录解析。提交前对所有报告做敏感字段扫描；如发现序列号、IMEI、MAC、Android ID、账户、凭据或私有密钥，必须遮蔽。
- 不修改原始固件包。所有解包输出写入新的工作目录。

## 1. 确认固件文件

使用已上传的 `firmware-hos43/package_inventory.csv` 找到本地固件包及以下镜像（如果存在）：

- `boot.img`
- `ramdisk.img`
- `dtbo.img`
- `vbmeta*.img`
- `super.img`

对原始文件只读取 SHA-256、文件大小和时间戳。不要上传这些完整二进制文件。

## 2. 工具检查

只检查本机已有工具；不要为了本任务执行未知安装脚本。

优先检查：
- `magiskboot`
- Android `unpack_bootimg`（AOSP）
- `avbtool.py`
- `mkdtimg`
- `lpdump`
- `lpunpack`
- `dtc`
- `file`
- `xxd` / `hexdump`
- WSL Ubuntu（如已有）

在报告中记录工具版本/路径。工具缺失时记录，不要自行下载来路不明的二进制。

## 3. Boot / ramdisk 解析

对 `boot.img` 执行只读解析，至少记录：

- Android boot header version
- header size
- kernel size / ramdisk size / second-stage size（若存在）
- page size
- kernel image 类型及压缩方式（若可判断）
- cmdline（敏感内容检查后）
- OS version / patch level 字段（若 header 有）
- image 是否包含 DTB，DTB size / offset（若工具支持）
- ramdisk 的压缩格式
- ramdisk 解包后的顶层目录和文件清单（只列路径，不上传私钥/证书内容）
- init、fstab、init*.rc、ueventd*.rc、模块加载配置路径
- boot image 是否带签名/AVB footer，记录工具输出

对独立 `ramdisk.img` 单独记录格式、压缩方式、header 和目录结构。不要假定 `boot.img` 与独立 ramdisk 的内容相同。

如果工具支持 `unpack_bootimg`，可参考：
```bash
unpack_bootimg --boot_img boot.img --out boot_unpacked
```
工具输出目录必须是新的空目录。若命令不兼容，停止并记录，不要尝试修改镜像。

## 4. DTBO 解析

对 `dtbo.img`：

- 读取 magic、header、总大小、entry 数量、每个 entry 的 size、offset、id、rev、custom fields（工具可支持的范围）
- 使用只读工具 dump/extract 每个 DTBO entry 到本地
- 对提取的 DTB/DTBO 用 `dtc` 反编译成 DTS
- 搜索并记录与 Huawei/DBY-W09/SM8250/KONA/rootparam 相关的节点、compatible、overlay target 和属性
- 记录 DSI panel、touch、PMIC、GPIO、UFS、USB、audio、WLAN、reserved-memory、OPP、CPU、rootparam 等节点路径
- 只提交脱敏 DTS 摘要或必要节点；不要把完整原始 DTB 上传

## 5. AVB / vbmeta 解析

对所有 `vbmeta*.img`：

- 使用本机 AOSP `avbtool.py info_image`（若可用）读取 header、algorithm、rollback index/location、flags、auth descriptor、hash/hashtree descriptor、partition name 和 chain partition
- 不要尝试验证或绕过签名；不修改 vbmeta
- 只报告 metadata，不输出密钥或完整签名数据

## 6. super.img 只读元数据

对 `super.img`：

- 先检查是否 sparse image，记录 magic 和文件格式
- 使用 `lpdump` 读取 super metadata，记录 metadata slots、block device、group、logical partition 名称、size、extent 数量、属性、slot suffix 情况
- 若 `lpdump` 不可用，记录工具缺失，不要尝试写入或转换原始 super
- 可在本地工作目录使用 `lpunpack` 将逻辑分区提取到新的目录，但这是读取原文件并产生新文件；需先确认磁盘空间充足
- 如果提取成功，优先分析 `vendor`、`odm`、`system`、`system_ext`、`product`、`cust`、`hw_product`（存在时）
- 对 ext4/f2fs 镜像仅使用只读方式检查；不要 mount rw。若 WSL 不具备安全只读挂载能力，使用 `debugfs`/`fsck -n` 或记录无法解析，不要改镜像
- 不上传整个 vendor/system 镜像。只上传文本清单、必要的脱敏 XML/config/rc/fstab 和模块 metadata

## 7. Vendor / ODM / HAL / modules

如果从 super 提取出相关逻辑分区，生成：

- `vendor/etc/vintf/manifest.xml`
- `vendor/etc/vintf/compatibility_matrix.xml`（存在时）
- `vendor/etc/vintf/manifest/*.xml`
- `odm/etc/vintf` 下相关 manifest/matrix（存在时）
- `vendor/etc/fstab*`、`odm/etc/fstab*`、`vendor/etc/init` 中相关 init rc 文件
- `vendor/lib/modules`、`odm/lib/modules` 的模块路径清单
- `modules.load`、`modules.dep`、`modules.softdep`、`modules.alias`（存在时）
- module 文件的 `modinfo` metadata：name、vermagic、depends、alias、license、signer（不要提交模块二进制）
- HAL/service 名称与 manifest instance 清单
- firmware 文件名/目录清单（只列名称，不上传 firmware binaries）

**不上传**：`/data`、用户配置、账号数据、设备身份、校准数据、TEE/keymaster 密钥、完整固件二进制、原始模块二进制。

## 8. 输出文件

在本地创建：

```
round3-hos43-image-analysis/
  README.md
  image_hashes.txt
  boot_header_report.txt
  boot_ramdisk_inventory.txt
  dtbo_report.txt
  dtbo_nodes_summary.txt
  vbmeta_report.txt
  super_lpdump.txt
  logical_partition_inventory.csv
  vendor_vintf/
  vendor_fstab_init/
  vendor_modules/
  vendor_hal_services.txt
  vendor_firmware_inventory.txt
  tools_versions.txt
  limitations.txt
```

提交前检查所有文本报告是否含设备序列号、IMEI、MAC、Android ID、账户、token、密码、私钥或个人路径；将个人路径替换为 `<LOCAL_PATH>`。

## 9. 提交

将报告放入仓库：

```
round3-hos43-image-analysis/
```

提交到 `analysis/hos43-initial-triage` 分支，commit message：

`Add read-only HarmonyOS 4.3 boot and super analysis`

如果某项工具/镜像无法解析，写清：
- 工具缺失/错误
- 镜像文件名与 SHA-256
- 已尝试的只读命令
- 错误输出（先脱敏）
- 不要用猜测补齐

## 10. 最终给 ChatGPT 的摘要

请在 `README.md` 最后附一个不超过 50 行的结论：

1. boot header / page size / boot version
2. boot 中 kernel、ramdisk、DTB 的关系
3. 独立 ramdisk 的用途和结构
4. DTBO entry 数量、目标设备和 rootparam 相关发现
5. vbmeta chain / partition descriptors 的结构
6. super 的逻辑分区及大小
7. Vendor/ODM 的 Android API、VINTF、HAL、模块布局
8. 当前 GKI 6.18.33 启动打包最大的未知点
9. 仍需本地 Agent 或实机只读验证的项目
