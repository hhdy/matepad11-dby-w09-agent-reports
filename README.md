# MatePad 11 DBY-W09 — Agent 只读采集与固件清单报告

本仓库收录针对华为 MatePad 11（型号 DBY-W09，KONA / SM8250）的只读采集结果，
用于 GKI 6.18.33 内核移植的前期调研。**当前顺序：先移植并验证 6.18.33 内核，再移植 Android 17 DerpFest；Android 12L 仅为历史参考。** 新会话必须先读 [PROJECT_HANDOFF.md](./PROJECT_HANDOFF.md) 和 [AGENT_TASK.md](./AGENT_TASK.md)。所有设备侧操作均为只读，未执行刷机、
重启、解锁、root、EDL 或任何分区写入。

## 目录

- `round1-adb/` — 第一轮 ADB 只读采集（设备属性、分区布局、内核信息、工具版本）
- `round2-adb/` — 第二轮 ADB 只读采集（CPU 频率、PCI ID、live DTB 状态、DRM/USB/input）
- `firmware-hos43/` — 本地鸿蒙 4.3 固件包只读检查（文件清单、白名单镜像 SHA-256、脚本修正说明）

## 设备关键事实（实机）

- SoC：KONA / SM8250，soc_id 356 rev 2.1；CPU 三簇最大频率 1.8048 / 2.4192 / 2.8416 GHz（判定为 865 规格，非 870）
- 系统：Android 12 / API 31，安全补丁 2022-08-01
- 内核：4.19.157-perf+，独立 `ramdisk` 分区，无 `vendor_boot` / `init_boot`
- 布局：传统非 GKI vendor 布局，与 Android 17 / GKI 6.18.33 基线差距较大

## 状态说明

- 设备侧采集：已完成，序列号与 MAC 地址已脱敏
- WSL / GKI 基线编译：未执行。本会话中 `wsl.exe` 调用被命令安全策略拦截，且系统未安装 Ubuntu 24.04，相关文件在各报告中标注为 `NOT AVAILABLE`
- 固件镜像 ZIP（约 78 MB，含 11 个启动镜像）：仅保存在本地，未上传本仓库；本仓库仅含文本报告

## 隐私

设备序列号、MAC 地址已在共享副本中脱敏。固件哈希属于公开镜像的校验值。
