# twrp_install_effect.md

ZIP：`/mnt/d/解锁bl/download/twrp.zip`，33,121,159 B，sha256 `d24331b5…5ad591`（BUILD01 已登记）。解包：**单文件 `twrp.img`**（33,386,938 B），无 META-INF/installer 脚本。

## twrp.img 静态解析

- `ANDROID!` boot **v0**：page_size=2048，**kernel_size=0**，ramdisk_size=33,384,890 B，second=0
- cmdline 残段（UTF-16/历史头，可读部分）：`…oidboot.hardware=qcom msm_rtb.filter=0x237 ehci-hcd.park=3 lpm_levels.sleep_disabled=1`
- **无 AVBf footer**（全镜像扫描 NONE）；无 vbmeta

## 语义

kernel_size=0 + 仅 ramdisk = "ramdisk-only swap"：刷入 recovery 后，ABL 加载**原 recovery kernel** + **TWRP ramdisk**（若 ABL 按分区内容装配）。也就是说，若用户确实将该镜像刷入 recovery 并成功进入 TWRP，则设备侧发生过：**recovery 分区内容被整段替换为无 kernel、无 AVB footer 的镜像，且 ABL 仍完成 kernel+ramdisk 装配并启动**。

## 判定

`TWRP_INSTALL_EFFECT = PARTIAL`：
- 可证：ZIP 形态 = ramdisk-only、无 AVB 元数据、无 vbmeta 修改载荷；
- 不可证：刷入是否实际发生、ABL 是否对其做过校验、recovery_vbmeta 是否被 (TWRP 流程之外的) 其他步骤改动——本地无刷入日志，按任务书不连接设备补证。
- 推论限制：即便 TWRP 曾成功启动，也**不能**证明"原厂 recovery_vbmeta 在未更改时允许任意 recovery"——该刷入发生在解锁态，且 ramdisk-only swap 的校验行为与完整镜像替换不同。
