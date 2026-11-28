# Android separate ramdisk 与 bootconfig 适配审查

## 1. 参考 Linux ramdisk 不是 Android ramdisk

svesnav README 第 45–49、95–103 行说明其 initramfs 将 microSD 上 ext4 标签 `LINUX70ROOT` 挂载为根文件系统。build_dev_images.sh 第 20–28 行以静态 busybox、`sd_root_init.sh` 和 reboot helper 制作 newc CPIO，再 gzip；第 30–37 行将 gzip payload 包成 header-v0 镜像，空 kernel、page size 2048；第 38–52 行把 payload 覆盖到 stock 2 MiB ramdisk 分区 payload 区并保留 AVB footer。sd_root_init.sh 第 55–80 行搜索 `LINUX70ROOT`、挂载 ext4，最后执行 `switch_root /newroot /sbin/init`。

这条 init 链是 Linux SD-root，不是 Android `/init` / first-stage init。不能将该 payload 替换本机 Huawei Android separate ramdisk。

## 2. 本机 Android 证据与保留策略

任务书及既有本机离线证据报告 separate ramdisk 含 Huawei `init`、`init.real` 和 KernelSU 相关文件；boot embedded ramdisk 报告含 `fstab.qcom` 与 `e2fsck`，未报告有 init/adbd。原始分区 bytes、wrapper/header、CPIO payload 边界和 footer 在本任务中未重新读取；本节为引用既有证据，不是本轮原始备份复核。

| 对象 | 当前证据 | ACK Android 17 适配结论 |
|---|---|---|
| separate ramdisk | Huawei init/init.real、KernelSU；2 MiB 分区；既有离线审计报告 AVB footer | KEEP_STOCK；不要用 Linux SD-root initramfs 覆盖 |
| boot embedded ramdisk | 既有报告含 fstab.qcom/e2fsck | 保留 stock boot v2 组件；其与 separate ramdisk 的启动职责仍以目标 ABL 证据为准 |
| Android first-stage init | 目标 Android 12/HOS4.3 stock 链存在；ACK Android 17 的实际 handoff 未在本任务证据中闭环 | UNKNOWN |
| fstab / dynamic partitions | stock fstab 的精确 ACK 兼容性、first-stage mount 依赖和动态分区元数据路径未完成逐项核对 | UNKNOWN |
| bootconfig | 目标 HOS4.3 传递的完整 bootconfig 内容及 ABL/内核 handoff 未取得可逐项对照的证据 | UNKNOWN |
| AVB / dm-verity | separate ramdisk footer 在先前离线审计中标记 VERIFIED；Android vbmeta chain 与 ACK 内核接口未在本任务重新核验 | UNKNOWN（不能由 footer 单独推出整条 AVB 链兼容） |

**ANDROID_RAMDISK_POLICY = KEEP_STOCK**。这只是分区策略，不等于 Android first-stage init 已验证可启动 ACK 6.18.33。

## 3. cmdline / bootconfig 不可照搬 Linux 模板

公开 boot-cmdline.txt 只有 `clk_ignore_unused pd_ignore_unused console=tty0 fbcon=font:TER16x32 loglevel=7 ignore_loglevel panic=0 rdinit=/init`。其中 `rdinit=/init` 指向 Linux busybox initramfs；它不是 Android cmdline/bootconfig 模板。

README 第 114–121 行说明安装器用 stock boot header v2、原 ramdisk、kernel、DTB 和 command line 构建 boot；matepad-kernel-install 第 196–198 行把 bundle cmdline 传给 boot_with()。这只证明参考 Linux 安装器如何注入 Linux cmdline，不证明 HOS4.3 的 bootconfig 注入路径。

以下项目均须保持 UNKNOWN，除非有目标设备 stock dump、精确 ABL 分析或 ACK Android 17 配置/启动证据：
- `androidboot.dtbo_idx`：既有目标报告将其视为 ABL 选择结果/启动参数，不得未经证明当作 DTBO 选择命令。
- `androidboot.hardware`、`androidboot.verifiedbootstate`、`androidboot.boot_devices`：需要精确保留/比较 stock token；不能从 Linux 项目 cmdline 推断。
- bootconfig 的来源、拼接顺序、传递时机和 ABL 是否独立传递 bootconfig：UNKNOWN。
- first-stage init 所需 fstab、dynamic partitions、AVB/dm-verity 参数：需从目标 stock Android 启动链取证。

## 4. ACK Android first-stage 的必要核验清单

内核进入执行、Android first-stage init 执行、Android framework/DerpFest 完整启动是三个不同验收阶段。进入 first-stage 前至少需证明下列依赖在早期可用，且不能依赖 system/vendor 挂载后才加载的模块：

- UFS host/PHY、interconnect、regulators、clocks、reset 和相关存储控制器依赖；
- devtmpfs、device-mapper、dm-verity/AVB 所需内核接口；
- fstab 实际使用的 ext4/F2FS/EROFS 文件系统；
- fscrypt 与所需 crypto 算法；
- binder/binderfs；
- bootconfig 内核支持及目标 ABL 的传递方式；
- dynamic partition/逻辑分区映射所需接口；
- 目标 Huawei init/init.real、init.rc 导入和 vendor_boot/vendor ramdisk 约定（若目标启动链实际使用）。

当前材料不能逐项证明上述 ACK 配置和 HOS4.3 handoff 已满足。不要以 Linux SD-root 能启动、boot 分区容量足够或 DTBO 组件静态审查通过，替代 Android first-stage 验收。

## 5. 最终结论

- ANDROID_RAMDISK_POLICY=KEEP_STOCK
- Android bootconfig handoff=UNKNOWN
- ACK Android 17 first-stage compatibility=UNKNOWN
- Android framework/DerpFest boot=NOT ESTABLISHED
- 本任务没有制作 ramdisk、修改 bootconfig、连接设备或执行测试。
