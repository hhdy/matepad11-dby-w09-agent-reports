# ROUND136 — 1号 AI 独立验收与处置记录

- 审查人：1号 AI（ChatGPT）
- 被审查人：2号 AI
- 任务：ROUND136 DBY-W09 首次安全启动前四项硬门槛审查
- 验收日期：2026-11-26
- AI2 分支：`ai2/round136-preboot-blocker-audit`
- AI2 报告：`firmware-analysis/round136-preboot-blocker-audit/AI2_ROUND136_PREBOOT_BLOCKER_AUDIT.md`
- AI2 报告 blob：`7158b6a90c73c6d18b0a673730a4df666433fea6`
- AI2 报告 commit：`54d29c435aab6320bada585bf260920570099bfd`
- AI2 任务书 blob：`031eb24c01272c665268dd2521d4983edce64a27`

## 1. 验收结论

**ACCEPTED — ROUND136 技术结论通过；记录两项文档完善事项，不影响 R3。**

AI2 正确区分了三种不同成果：6.18.33 Image 离线构建、board DTS/DTB 离线生成与首次安全实机启动。其核心处置正确：ROUND135 R3 必须继续，不能因 A/B/C/D 启动门槛暂停；即使 R3 PASS，也只能标记 `PASS — BUILD/DTB INTEGRATION ONLY`，不能宣称平板已能启动、不能据此制作/刷写 boot 包。

## 2. 1号 AI 已独立核对的关键源码事实

以下固定 ACK 源码均从 `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` 直接复核：

1. `drivers/of/fdt.c::early_init_dt_scan_memory()`：扫描 root 子节点中的 enabled `device_type = "memory"` 节点，优先读取 `linux,usable-memory`，否则读取 `reg`；每个 size 为 0 的 tuple 被直接跳过，不作为 system RAM 添加。R3 候选继承 `sm8250.dtsi` 的零尺寸 `/memory` placeholder，因此编译成功不能证明有有效 RAM map。
2. `drivers/pmdomain/qcom/rpmhpd.c`：SM8250 descriptor 表中 `RPMHPD_MMCX` 选择 plain `mmcx`，该 descriptor 没有 `.parent`；`cx_w_mx_parent` 有 `.parent = &mx.pd`，但仅 CX descriptor 使用。`rpmhpd_probe()` 只有在 descriptor `.parent` 非空时才调用 `pm_genpd_add_subdomain()`。因此 UFS OPP 映射到 MMCX，并不能证明 MMCX request 会级联到 MX。
3. `drivers/regulator/core.c::regulator_resolve_supply()`：在 regulator parent lookup 失败且 `have_full_constraints()` 为真时可以 fallback 到 `dummy_regulator_rdev`。`drivers/regulator/dummy.c` 的 dummy regulator 是 always-on 约束与空 ops；它不创建真实物理 parent，也不证明轨道电压、供电使能或上电时序。
4. `drivers/firmware/efi/fdtparams.c`、`drivers/firmware/efi/efi-init.c` 与 ARM64 setup 路径：EFI memory map 可以替代先前 FDT 导入的 memblock，但要求完整 EFI FDT 参数和真实 EFI handoff。不能仅因 ABL 是 UEFI 环境就推断 Linux 通过 EFI stub 进入。
5. 固定 ACK `drivers/ufs/host/ufs-qcom.c` 没有消费 HOS downstream `qcom,vccq-parent-supply` 的等价 parser/enable path；ROUND51 对 PM8150L S8 `set_load`/DRMS 限制的结论仍适用。

上述源码语义支持 AI2 的 A/B/C 关键结论，没有发现足以否定 ROUND135 固定候选源码身份或阻止 R3 的新证据。

## 3. 四项门槛处置

| 项目 | 1号 AI 验收状态 | 对 R3 的影响 | 对首次实机启动的影响 |
|---|---|---|---|
| A — ABL final FDT / memory / EFI handoff | BLOCKED | 不阻止 Image、语法/离线 DTB 构建；R3 仍应按任务书验证 DTB | 必须先取得真实 post-ABL final FDT 与 entry-route 证据 |
| B — PM8150/PM8150L physical input parents | BLOCKED | 不阻止 Image / DTS/DTB 离线构建 | 必须先确认 UFS 相关 rail 的真实输入 parent、约束和 enable owner |
| C — MMCX→MX ARC/corner equivalence | BLOCKED（UFS 首启最小门槛） | 不阻止 Image / DTS/DTB 离线构建 | 必须证明 UFS 所需 corner 可由当前 ACK MMCX vote 满足，或证明需要的 parent/request 路径 |
| D — boot-v2 / ramdisk / DTBO / AVB / test route | BLOCKED | 不阻止 Image / DTS/DTB 离线构建 | 未确认 ABL 选择、ramdisk 消费、AVB 链和可恢复测试方式前，不得打包/试刷 |

以上 BLOCKED 均不是本轮已经发生的编译失败；R3 的最终成败仍只由 WorkBuddy Agent 上传的原始 R3 报告和日志决定。

## 4. 补充核对：ROUND64 Phase E 原有本地证据

AI2 报告应补充引用一份本轮固定清单中没有列出、但仓库已经存在的关键证据：

- `firmware-analysis/round64/round64-dby-w09-hos43-final-memory-and-pm8150-input-evidence.md`
- Git blob：`56e32d7989157d6c4eab22cb8ddf8a83a9c2f960`

该报告已经明确记录：

- 既有 `adb pull /sys/firmware/fdt` 曾因 `Permission denied` 失败，`live.dtb.sha256` 记录为 `NOT AVAILABLE`；因此当前授权语料中没有真实 post-ABL final FDT。
- HOS4.3 final FDT 的 classic-vs-EFI entry route 未观察到；该报告指出 stock kernel payload 没有 PE header，但这只描述 stock image，不能代替未来 6.18.33 candidate 的实际 entry route。
- 没有 DBY-W09 对应 schematic / PMIC power tree，也没有包含所需 `vin-supply` / `vdd-s*-supply` / `vph-pwr-supply` 的 HOS4.3 final DT 证据。

该证据加强 A/B 的 BLOCKED 结论，并说明不应简单重复同一条无权限 ADB pull。未来若要补采，必须先设计合法且已授权的只读途径；不得绕过权限、root 或修改设备状态。

## 5. reserved-memory 数量口径确认

AI2 使用 37 是正确的最终口径。`firmware-analysis/round24/round24-hos43-reserved-memory-and-consumer-map.txt`（blob `a0167df755521fa583b4ce3f73b1b2260306b426`）第 31–46 行明确通过 direct-child enumeration 将早期 34 校正为 37，其中 35 个有 alias、2 个无 alias。ROUND64 Phase E 报告仍出现 34，属于沿用了旧统计；不得用它覆盖 ROUND24 的直接枚举结果。

## 6. 文档完善事项

1. ROUND136 taskbook 要求报告提交后在正文末尾记录 report commit SHA / report blob SHA。AI2 报告正文没有自记录这两项。本验收记录补录：commit `54d29c435aab6320bada585bf260920570099bfd`；report blob `7158b6a90c73c6d18b0a673730a4df666433fea6`。这是交付记录遗漏，不是技术结论缺陷。
2. 后续引用 A/B 时应把 ROUND64 Phase E 证据纳入索引，尤其是 final FDT 读取失败和缺少 board-specific PMIC schematic/power tree 的既有事实；不需要因此重新执行 ROUND64。

不要求 2号 AI 重写整份报告，不要求重跑任何源码、设备或本地测试。此记录作为 1号 AI 的审查补充和后续会话恢复依据。

## 7. 对 ROUND135 的直接指令

**继续 ROUND135 R3，保持当前 23-patch identity/tree SHA 不变。**

- R3 完整通过后：只接受 `PASS — BUILD/DTB INTEGRATION ONLY`。
- R3 有任何 identity、Schema、真实 DTB、Kconfig、对象、Kleaf 或 Host test 失败：按 R3 taskbook 原规则 FAIL/BLOCKED，并保存原始日志；不得因为赶进度而越过 gate。
- R3 通过不意味着 A/B/C/D 关闭；Phase E/F 仍 BLOCKED、Phase G NOT RUN。
- 当前不启动新的 WorkBuddy 设备采集任务，不连接平板、不访问 ADB/fastboot/recovery/serial、不制作 boot/ramdisk/DTBO/vbmeta 包、不刷写分区。

**最终处置：ROUND136 由 2号 AI 完成并通过 1号 AI 技术验收。2号 AI 暂无下一项源码任务；保持 R3 继续运行，由 1号 AI 审核其结果。**
