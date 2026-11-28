# CORR01 — packaging_repro.md（候选打包与复现说明）

## 候选文件

- 文件名：`dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img`
- 大小：46,563,215 B
- SHA-256：`d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091`
- 来源：PREP10 构建轮产物（K1_HOST_CANDIDATE_PREP），本 CORR01 轮**零字节改动**，原样交付。

## 候选构成（溯源）

| 载荷 | 来源 | 冻结 SHA-256 |
|---|---|---|
| kernel (44,820,992 B) | ACK android17-6.18.33 构建轮冻结 Image | `f89a2839…bad21` |
| embedded ramdisk (519,986 B) | stock boot 原样（fstab.qcom + e2fsck，无 init） | `a4b94ff6…1af3c` |
| DTB (1,216,399 B) | PREP04 candidate DTB | `7bb9a1fb…996b7` |
| cmdline | stock cmdline + `ignore_loglevel ` 前缀 + `earlycon=qcom_geni` 改名 | —（见 stock_prep10_comparison.md） |
| 结构参数 | 与 stock boot v2 全同（page 4096 / hv 2 / hdr 1660 / 地址同） | — |

## 复现步骤（审计者视角）

1. 校验候选哈希：`sha256sum dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img` → 期望 `d1d76c21…cc091`。
2. 解析 boot v2 头（`scripts/boot_tail_audit.py` 中的 `parse_hdr` 即解析逻辑）：核对 header comparison 表的 SAME/DIFF 项。
3. 解析 stock DTBO：`node scripts/dtbo_parse_corr01.js <dtbo.img> <outdir>`（或 WSL：`python3 -I scripts/dtbo_parse_corr01.py`），核对 `dtbo_parse_corr01_output.txt`。
4. 尾部审计：`python3 -I scripts/boot_tail_audit.py`（需 stock boot.img + PREP10 输入路径见脚本头部），核对 `boot_tail_audit_output.txt`。
5. 对照本报告 §2–§4 判定。

## 交付渠道

- 报告/脚本/元数据：仓库 `hhdy/matepad11-dby-w09-agent-reports`，分支 `ai1/boot-v2-first-package-prep`，目录 `firmware-analysis/boot-v2/linux-port-adapt01-corr01/`。
- 候选 boot：同仓库 GitHub Release 资产（>25 MiB 不适合 git blob；Release 资产上限 2 GiB）。
- 不公开：原厂完整固件（r155 全量）、设备序列号/IMEI、ksu 内部细节。

## SHA256SUMS.txt

打包时生成，覆盖本目录全部交付文件（含 9 个 dtbo 抽取条目与两份解析输出）。
