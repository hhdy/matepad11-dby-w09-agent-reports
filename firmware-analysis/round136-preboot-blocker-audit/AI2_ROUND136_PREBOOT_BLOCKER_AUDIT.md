# AI2 ROUND136 独立审查报告：DBY-W09 首次启动前四项硬门槛

- 任务书：`firmware-analysis/round136-preboot-blocker-audit/AI2_ROUND136_TASKBOOK.md`
- 任务书 Git blob：`031eb24c01272c665268dd2521d4983edce64a27`
- 审查日期：2026-11-26
- 设备：Huawei MatePad 11 (2021) DBY-W09 / KONA / SM8250 v2.1
- 固定 ACK：`aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` (`android17-6.18.33_r00`)
- ACK root tree：`790a68ae6d4f4ac51ab2d88977b6fd5c031473b7`
- ROUND135 R3 候选 content tree：`afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- 审查分支：`ai2/round136-preboot-blocker-audit`
- 审查性质：只读仓库证据与固定 ACK 源码审查；不是本地 Agent 任务

## 1. 最终结论

**ROUND135 R3 应按原任务书继续，不应因本报告四项启动门槛而暂停。** 本轮未发现能够证明 ROUND135 固定候选在源码身份或已知 ACK 语义上无效的证据。四项问题都不阻止纯离线 6.18.33 Image 编译，也不必然阻止纯离线 board DTS/DTB 语法构建；但四项均未达到首次安全实机启动的证据门槛。

必须严格区分三种成果：

1. **Image 可编译**：固定源码、配置、对象和 Kleaf 构建通过。
2. **board DTB 可离线构建**：真实 DBY-W09 DTS 能生成 DTB，schema/dtbs_check 与 DTB 内容检查按 R3 记录结果。
3. **可安全尝试首次实机启动**：最终 ABL handoff、系统 RAM/保留区、电源输入拓扑、UFS 性能域语义、DTBO/ramdisk/AVB/签名与可恢复测试路径均有足够证据。

R3 即使 PASS，也只能支持前两项，不能宣称设备移植完成或允许刷机/启动。

### 1.1 本轮没有改变 R3

ROUND135 当前权威 manifest `kernel-baseline/round135/ROUND135_23_PATCH_SERIES_MANIFEST.md`（blob `9188de2022f88c374bfcaa367c505428812608d9`）和 R3 taskbook（blob `729236571a3b788dfbad464f6430b31d81955bcf`）明确规定：R3 在固定候选树 `afe9517f...` 上进行身份、schema、真实 DTB、Kconfig、对象、Kleaf Image 与 Host regression 验证。R3 taskbook 已授权这些**离线验证**，但不授权 boot package、AVB 操作或设备操作。

ROUND61 Phase E 旧报告曾写“不得生成 board DTB”；该限制针对当时未通过证据门槛的板级迁移/启动用途。ROUND135 R3 是之后明确授权的 disposable offline validation。两者应按用途区分：允许 R3 生成并检查 DTB，不得把该离线 DTB提升为已验证的实机启动 DTB，也不得据此打包。

## 2. 结论矩阵

| 审查项 | 阻塞 6.18.33 Image 编译 | 阻塞纯离线 board DTS/DTB 编译 | 阻塞首次安全实机启动 | 当前状态 | 关闭所需最小证据 |
|---|---|---|---|---|---|
| A — ABL final FDT / memory / EFI handoff | 否 | 否（语法/离线 DTB 可验证） | 是 | BLOCKED | 同一次真实 HOS4.3 启动中，ABL 完成 DTB/DTBO 组合及修补后、进入内核前的脱敏 final FDT；并证明 classic Image 或 EFI-stub 的实际 entry route；完整可用 RAM 与 37 个保留区关系可审计 |
| B — PM8150 physical input parents | 否 | 否（缺 parent 不妨碍 DTS 语法构建） | 是 | BLOCKED | DBY-W09 板级原理图/boardview/netlist 或 HOS4.3 PMIC regulator runtime tree + bootloader rail state，明确 UFS 相关 PM8150/PM8150L 输出的物理输入 parent、约束及 S8 enable owner |
| C — HOS ARC MMCX→MX / ACK RPMHPD 等价性 | 否 | 否 | 是（若要把本次 UFS 存储路径作为安全首启路径） | BLOCKED | 证明 UFS 所需性能状态可由 ACK MMCX 单域满足，或取得目标 HOS4.3 Command DB AUX map 与实际 vote/parent 行为，证明所需 MMCX→MX 级联；无需先证明整个 ARC 图完全移植 |
| D — boot-v2 / ramdisk / DTBO / AVB / test route | 否 | 否 | 是 | BLOCKED | HOS4.3 ABL 实际选择项/组合方式/ramdisk 消费路径、完整 AVB descriptor/chain 与 vbmeta_cust 来源、签名/rollback policy、boot-tool 格式契约及可恢复测试路径 |

说明：表中“否”表示该项本身不阻止纯离线编译，不代表 R3 的实际构建一定 PASS。构建结果必须以 R3 原始日志为准。A/B/C 的缺口阻止把生成的 DTB 当作可信板级启动输入；D 阻止构建可接受的启动包。四项均阻止本轮声称“可以安全首次启动”。

## 3. A — HOS4.3 ABL final FDT、系统内存与 EFI/classic handoff

### 3.1 固定 ACK 的实际内存发现语义

固定 ACK `drivers/of/fdt.c::early_init_dt_scan_memory()`（blob `a931cd4beaaa6e3becc3692e3b4b8a0e42d6a691`，约 lines 1034–1086）只扫描 root 下 `device_type = "memory"` 且可用的节点；优先读取 `linux,usable-memory`，否则读取 `reg`。每个 tuple 的 size 为 0 时直接跳过，不调用 `early_init_dt_add_memory_arch()`。`early_init_dt_scan_nodes()` 会调用此扫描（同文件约 lines 1249–1260）。

固定 ACK `arch/arm64/boot/dts/qcom/sm8250.dtsi`（blob `adf6b49b52c48ca05ed6d0c1251f97ace664ef9d`，lines 683–687）定义：

```dts
memory@80000000 {
    device_type = "memory";
    /* We expect the bootloader to fill in the size */
    reg = <0x0 0x80000000 0x0 0x0>;
};
```

因此 ROUND135 board DTS 继承了一个存在但零尺寸的 memory placeholder。它不是有效 RAM map。`dtc` 可以把它编译进 DTB；内核 classic memory scan 会因 size=0 跳过它。编译通过不等于启动时有可用 RAM。

`/reserved-memory` 是另一个独立扫描/保留流程（`drivers/of/fdt.c` 中 `early_init_fdt_scan_reserved_mem()` / `fdt_scan_reserved_mem()`；同 blob）。保留区不会自动变成 system RAM，也不能替代有效 `/memory`。

### 3.2 EFI-stub 是独立的内存来源，但不能由“UEFI ABL”推断

固定 ACK `drivers/firmware/efi/fdtparams.c::efi_get_fdt_params()`（blob `b815d2a754eef33b5157830fc739ca47dd666d3f`，约 lines 84–133）从 `/chosen` 读取完整参数集合：
- `linux,uefi-system-table`
- `linux,uefi-mmap-start`
- `linux,uefi-mmap-size`
- `linux,uefi-mmap-desc-size`
- `linux,uefi-mmap-desc-ver`

缺少必需属性时函数返回 0。固定 ACK `drivers/firmware/efi/libstub/fdt.c::update_fdt()`（blob `6a337f1f8787b3bc68f771500f9fcd4b44a7b4f7`，约 lines 80–138）在 `/chosen` 写入这些 EFI handoff 属性；`update_fdt_memmap()` 在 ExitBootServices 阶段更新 mmap 地址、大小和 descriptor 元数据（约 lines 147–181）。

固定 ACK `arch/arm64/kernel/setup.c`（blob `56e69b249c2c5ec911f01c4a4b0a1ee96ae33707`，约 lines 317–335）在 `arm64_memblock_init()` 前调用 `efi_init()`。`drivers/firmware/efi/efi-init.c`（blob `a65c2d5b9e7b6d119206ed0380b4e7574e436c01`，约 lines 159–278）在 EFI 参数有效并完成 EFI 初始化后，`reserve_regions()` 会清除此前从 DT memory 节点建立的 memblock（KHO scratch 例外），再按 EFI memory descriptors 建立可用/保留范围。

所以完整 EFI handoff 可以替代 DT memory ranges，但前提是 Linux 确实进入 EFI stub，且可信 `/chosen/linux,uefi-*` 元数据完整。ABL 是 UEFI/EDK2、存在 Qualcomm EFI_KERNEL_PROTOCOL、或 FDT 里偶然出现 EFI 字符串，都不能单独证明 Linux 进入了 PE/COFF `efi_stub_entry`。ARM64 booting contract 将 Image 的 normal code entry 与 PE/COFF EFI entry 明确区分（固定 ACK `Documentation/arch/arm64/booting.rst` blob `e4f953839f7181ef5016e7f25e3f729dc5cb7bd7`，约 lines 90–110）。

### 3.3 HOS4.3 与候选 DTS 证据边界

- 早期 ROUND19 对 HOS4.3 base FDT 的 `/memory` 口径曾写成未发现节点；后续校正为存在 `device_type="memory"` 的零尺寸占位，不能作为 RAM map。不能继续引用早期“完全没有节点”作为最终事实。
- HOS4.3 `/reserved-memory` 子节点数已由 ROUND24 校正为 **37**，不是 ROUND19 早期的 34。物理地址在脱敏报告中被隐藏，且各节点包含 no-map、removed-dma-pool、reusable、size/alignment、dynamic resize 等不同语义。
- ROUND24 的 consumer map 显示多个固件/远端处理器 carveout 是启动前就可能被 XBL/ABL/其他固件占用；没有 final FDT 就无法确认它们是否已由 bootloader 在 RAM map 中扣除或是否仍需 Linux 声明。
- 固定 ACK `sm8250.dtsi` 还带有一组 generic SM8250 reserved-memory ranges（例如 hyp、xbl_aop、cmd_db、smem、removed 及多个 SoC pools）。这些是 SoC 参考 DTS 的静态地址，不是 DBY-W09 HOS4.3 的实测内存图，不能因为编译继承就当成目标板真实 carveout。
- 同设备公开 Linux 7.0 DTS 基于 HOS4.2，不能作为 HOS4.3 的 RAM/保留区坐标模板。

ROUND42 的 FreeABL/SM8250-capable LinuxLoader 参考（报告 blob `1ba87a9079f00aed370c82d3b9a1c8c76ded1c24`）在 DTB/DTBO composition 后查找既有 `/memory` 并更新其 reg；标准路径找不到节点会失败，不会自动创建。它是另一台 SM8250 设备的 ABL-derived source，不是 Huawei HOS4.3 的直接证明。

ROUND75 的 stock artifact/entry-route 研究在 Phase F 汇总中仅作 inference：HOS4.3 stock kernel 是 gzip-compressed normal ARM64 Image，而非 PE/COFF EFI application；stock 能启动说明 boot chain 必然提供了有效 handoff 或其他 memory 修正，但实际最终 FDT 与执行路径仍未被捕获。不得把该推断升级为直接 ABL 观察。

### 3.4 关闭 A 的最小证据

同一次 HOS4.3 启动中，在 ABL 已完成 base DTB + 实际选中 DTBO 的组合/修补之后、即将进入内核之前，取得：
1. 脱敏 final FDT（不是原始 boot.img DTB，也不是 Ubuntu DTB）；
2. 实际 kernel entry route 的可信 trace/log：classic ARM64 Image `primary_entry`，或 Linux EFI-stub `efi_stub_entry`；若走 EFI，需同时保留完整 `/chosen/linux,uefi-*` 参数及可解释的 EFI memory descriptors；
3. 所有有效 system RAM ranges，以及 HOS4.3 37 个 reserved-memory 子节点的 `reg`、`no-map`、`reusable`、`size`、`alignment`、`alloc-ranges`、动态 resize 和消费者引用；
4. 明确 selected DTBO index/table match 与 memory/ reservation 是否被 ABL 修改；
5. 能证明 system RAM 与 no-map/secure/firmware/reusable pools 无重叠、未把 firmware-owned ranges 暴露给 Linux。

脱敏时可以把物理地址转换成一致的相对坐标（例如相对于一个隐藏基址的偏移），但必须保留每个 range 的大小、顺序、重叠/相邻关系、alignment、cell 数和 phandle/consumer 关系；不能把每个地址独立随机化到无法判断冲突的程度。

**A 状态：BLOCKED。** 纯离线编译不被阻止；可信 final memory map 与保留区 handoff 尚未建立。

## 4. B — PM8150 / PM8150L 物理输入供电链

### 4.1 必须分清 consumer-to-output 与 output-to-physical-parent

ROUND135 board DTS 中 UFS 侧已建立的输出 rail 对应关系如下（HOS4.3 本地 consumer map + ACK PMIC regulator 表交叉核对）：

| UFS consumer / 功能 | PMIC 输出 rail | ACK `supply_name` / 物理输入 parent 名称 | HOS4.3 是否建立真实 parent phandle |
|---|---|---|---|
| UFS VCC | PM8150 L17 | `vdd-l13-l16-l17` | 未建立 |
| UFS VCCQ | PM8150 L6 | `vdd-l6-l9` | 未建立 |
| UFS VCCQ2 | PM8150 S4 | `vdd-s4` | 未建立 |
| UFS PHY VDDA | PM8150 L5 | `vdd-l3-l4-l5-l18` | 未建立 |
| UFS PHY PLL | PM8150 L9 | `vdd-l6-l9` | 未建立 |
| UFS device REF_CLK pad supply | PM8150 L6 | `vdd-l6-l9` | 未建立 |
| UFS VCCQ-parent consumer metadata | PM8150L S8 | `vdd-s8` | 未建立；且 ACK UFS driver 不消费该 metadata |

固定 ACK `drivers/regulator/qcom-rpmh-regulator.c` blob `109f0aae09b1df431d2e14d45a64d115e87cdec4`：`pm8150_vreg_data[]` 约 lines 980–1010，`pm8150l_vreg_data[]` 约 lines 1012–1034，明确给出上述 `supply_name`。`rpmh_regulator_init_vreg()` 将该 `supply_name` 放入 regulator descriptor（约 lines 425–455）。这表示 regulator framework 期望一个父级 supply 名称，不表示目标板已提供该父级。

ROUND11 的 HOS4.3 base-FDT 全量属性名扫描在已检查范围内未发现 `vdd-s1..s10-supply`、`vin-supply` 或 `vph-pwr-supply`；找到的 `*-parent-supply` 是 vendor ARC level-provider edges，不是 PM8150 VRM 输入。ROUND16/21 已明确禁止把 ARC parent-supply 或 proxy-supply 伪装成普通 PMIC regulator parent。

`qcom,vccq-parent-supply = <&vreg_s8c_1p2_1p4>` 是 UFS Host 到 PM8150L S8 **输出** rail 的 consumer metadata；它不等于 S8 自身的 `vdd-s8-supply` 输入。固定 ACK `drivers/ufs/host/ufs-qcom.c` 没有对应 `qcom,vccq-parent-supply` parser/enable callback。ROUND51 还确认 S8 的 ACK `pmic5_hfsmps510` ops 没有 `set_load`/DRMS callback，210mA load-only 请求不能作为 rail enable 证据。S8 runtime enable owner/state 仍 UNKNOWN。

### 4.2 Dummy regulator 的准确含义

固定 ACK `drivers/regulator/core.c::regulator_resolve_supply()`（blob `39d317ad73a33c4aa27e179cc436d8bf4daf5bcc`，约 lines 2046–2105）在找不到 regulator parent 且 `have_full_constraints()` 为真时，可以使用 `dummy_regulator_rdev`。Dummy regulator 本身（`drivers/regulator/dummy.c` blob `e5197ec7234d01518b26844c555f3900a4ee5750`，lines 22–30）只有 `always_on = 1` 约束和空 ops。

该 fallback 的平台语义是假定缺失的物理 supply 已经存在并处于 enabled 状态，软件 regulator graph 不再控制它。它不创建真实父级、不向物理 rail 发 enable/vote、不证明父级电压/电流/上电时序，也不证明实际电路连接正确。因而“可能不因缺 parent 而 probe defer”不等于“供电安全”。

### 4.3 编译、probe 与电气安全的分类

- Image 编译：不阻塞。
- 纯离线 DTS/DTB 编译：不阻塞；缺少 parent phandle 本身不是 dtc 语法错误，schema 结果以 R3 实际日志为准。
- UFS probe：不一定被缺 parent 直接阻止；full-constraints 下可能走 dummy parent。但 S8 没有 ACK UFS runtime consumer，rail 是否已由 ABL/其他 RPMh consumer 使能仍未知。
- 首次实机安全启动：阻塞。没有真实输入电源路径、rail owner、约束与状态证据，不能把 dummy fallback 当作电气验证。

### 4.4 关闭 B 的最小证据

优先使用 DBY-W09 对应 revision 的原理图、boardview/netlist 或等效权威硬件资料，列出 S4/L5/L6/L9/L17/S8 的实际 VIN/parent、上游电源、输入范围、使能关系和共用关系。若无法取得，应由已授权的 HOS4.3 本地只读取证提供 PMIC regulator runtime tree / bootloader regulator state，明确 rail parent 与状态；尤其确认 S8 的 enable owner。不能猜 `vph_pwr=3.7V`，不能添加假 fixed-regulator 或推测 `vdd-s*-supply`。

**B 状态：BLOCKED。** 软件图的 parent 缺口不阻止编译，但未建立物理供电安全。

## 5. C — HOS4.3 ARC MMCX→MX 与 ACK SM8250 RPMHPD

### 5.1 HOS4.3 已有证据：至少五条 parent edges，不是完整图

ROUND11 原始枚举发现四条，ROUND14 又确认第五条；ROUND51 依 public KONA driver 的 property-name 解析规则复核。当前可确认的至少五条 base-FDT ARC logical parent edges：

1. CX ALL child → MX ordinary ALL child。
2. CX AO child → MX AO child。
3. MMCX ALL child → MX MMCX-supply ALL child。
4. MMCX AO child → MX AO child（与 CX AO 共用该 target）。
5. MX MMCX-supply ALL child → CX MMCX-supply child（ROUND14 新发现）。

完整总数没有经过新一轮全图 census，不能写成“恰好五条”。ROUND11 另发现六条 `proxy-supply`，这是独立机制，不得计入 parent-edge 数量，也不是物理 PMIC VIN。

ROUND14 / ROUND51 已经补齐了部分此前未知的 HOS4.3 ARC 字段，不能继续沿用旧报告中所有字段均未知的过期结论：
- provider/resource：`mmcxlvl` / `mmcx.lvl`；`mxlvl` / `mx.lvl`。
- MMCX ALL/AO/SO：`qcom,set` = 3/1/2（ALL/ACTIVE/SLEEP），min/init = 64（LOW_SVS），max = 65535（逻辑 MAX ceiling）。
- MX MMCX-supply/AO children：min/init = 16（RETENTION），max = 65535。
- MMCX ALL/AO `qcom,min-dropout-voltage-level` raw value = `0xffffffff`；ROUND51 对 public KONA source 的解读是 ARM64 signed-int 路径上的 -1 logical-level adjustment，而不是“无 dropout” sentinel。该数值的硅片电气 margin 仍未实测。
- MMCX ALL 的 `proxy-supply` 指向自身 ALL child，并有 `qcom,proxy-consumer-enable` 与 voltage range `<384 65535>`（TURBO..MAX），无 proxy-consumer-current。public KONA helper 将其作为 late-init 前的临时 boot request，之后释放；不是 always-on、system-load 或永久 vote。

以上是逻辑 ARC corners，不是微伏值。ROUND14/51 的字段解释依赖 public Qualcomm KONA source commit `cad09e061ef6cf689a4a1e54d27562e0f042236a`；该 source 是语义参考，不是 Huawei HOS4.3 正在运行的 vendor binary 证明。

### 5.2 固定 ACK SM8250 RPMHPD 的真实行为

固定 ACK `drivers/pmdomain/qcom/rpmhpd.c` blob `4c3cbf3abc7504cce3b8211c339b7ada03d65e38`：
- `cx_w_mx_parent` / `cx_ao_w_mx_parent` 的 `.parent` 指向 MX/MX_AO。
- plain `mmcx` / `mmcx_ao` 只有 peer 和 `mmcx.lvl` resource name，没有 `.parent`。
- `sm8250_rpmhpds[]` 将 `RPMHPD_CX` 映射到 CX-with-MX-parent，但 `RPMHPD_MMCX` 映射到 plain `mmcx`，`RPMHPD_MMCX_AO` 映射到 plain `mmcx_ao`；MX 自身独立。
- `rpmhpd_probe()` 只对 descriptor 中非 NULL `.parent` 调用 `pm_genpd_add_subdomain()`（约 lines 1020–1065）。所以 SM8250 MMCX 没有 GenPD parent edge 到 MX。

固定 ACK `drivers/pmdomain/core.c` blob `8adc78d62d05f1f7432a154c7d71ce0ade3f406a`，`genpd_xlate_performance_state()` / `_genpd_set_parent_state()`（约 lines 400–455）只在 GenPD 已有 parent link 时才向 parent 传播 performance state。`drivers/opp/core.c` blob `157c84b689feba9ae2c446083e42de63e94a38a6`，`dev_pm_opp_xlate_performance_state()`（约 lines 2757–2795）在源 OPP table 没有 `required_opp_count` 时原样返回 pstate；它不会自动计算 HOS `qcom,min-dropout-voltage-level`。

### 5.3 ROUND135 patch5 的作用与边界

冻结 patch5 `kernel-baseline/round61/patches/round33-checkpatch-clean.patch`，blob `f1d54e5e0379183fbdfb3ca6132c6d0fc61d4622`，明确实现：
1. 校验 UFS Host domain index 0 为 RPMHPD MMCX；index 1 为 GCC UFS_PHY_GDSC。
2. 校验每个 available UFS OPP 的唯一 `required-opps` 目标属于 RPMhPD provider 精确 OPP table。
3. 通过 `devm_pm_domain_attach_list(PD_FLAG_DEV_LINK_ON)` attach 两个 domain。
4. 将 UFS OPP table 唯一 required-dev slot 映射到 `pd_list->pd_devs[0]`（MMCX，index 0），之后才进入 `ufshcd_pltfrm_init()`。

它能证明 UFS OPP request 被明确路由到 ACK MMCX provider；它**不能**证明 ACK MMCX 进一步向 MX 传播，因为固定 SM8250 descriptor 没有 MMCX→MX parent。patch5 的说明也明确写出不实现 MMCX-to-MX parent propagation。

### 5.4 哪些 ARC 证据仍缺失？

不能把已在 ROUND14/51 捕获的 resource/set/corner/dropout/proxy 字段再次标成未知。当前仍缺：
- HOS4.3 完整 ARC parent-edge 全图 census（现为至少五条，不是完整总数）；
- 每个相关 ARC resource 的完整 Command DB AUX level arrays / 实际硬件 level mapping；
- HOS4.3 实际选中的 DTBO 及其对 ARC provider/child 节点的有效覆盖结果；
- 启动期间与 UFS probe/运行相对应的真实 RPMh active/sleep votes、MMCX/MX resource 请求与父级传播行为；
- 证明 UFS 第一阶段所需 corner 是否可由 ACK plain MMCX vote 单独满足，或确实需要 HOS MMCX→MX parent request。

### 5.5 三种设计方向的比较（不选方案、不写代码）

| 方向 | 优点 | 主要风险 / 前置证据 |
|---|---|---|
| A. 保持共享 ACK SM8250 plain MMCX descriptor | 改动最小；当前 patch5 路由已明确；不影响其他 SM8250 | 仍不等价于 HOS ARC parent graph；必须证明 UFS 的最低启动 corner 可由 MMCX vote 单独满足 |
| B. DBY-W09 专用 MMCX→MX RPMHPD descriptor | 可把 parent 关系限制在目标 board/compatible | 通用 GenPD pstate 默认一对一传递，不复现 arbitrary dropout、独立 ALL/AO/SLEEP child 与第五条 parent edge；需证明 exact OPP/AUX mapping |
| C. 独立移植 ACK ARC provider | 语义上更接近 HOS 的 child-level ARC graph、active/sleep、parent/dropout、proxy aggregation | 工作量最大；需 AUX runtime parsing、provider context、每个 child set/aggregate/enable/proxy 生命周期和 binding；不应在未证明 UFS 需要前并入 storage-first |

**C 状态：BLOCKED。** 不是 Image/DTB 编译阻塞；是首次 UFS 实机启动前必须证明 UFS 角位需求和 MMCX/MX 供电请求行为足够安全。当前没有依据选择 A/B/C 之外的实现，也没有依据改动共享 SM8250 descriptor。

## 6. D — Android boot-v2 / ramdisk / DTBO / AVB / 首次测试路径

### 6.1 已确立的 stock 结构

ROUND64 / ROUND65 既有本地只读证据确认：
- stock `boot.img` 是 Android boot header v2，page size 4096，含 kernel、embedded ramdisk、embedded DTB；已知 stock payload boundary/offset 仅是原始 inventory，不是 replacement 参数。
- 同时存在独立 `ramdisk.img` 分区，header v0、page size 2048；其 payload 为 gzip→CPIO newc。
- stock `dtbo.img` 为 DTBO v0，9 entries，table page size 4096。
- first-stage fstab 位于 base FDT `/firmware/android/fstab`，ROUND65 统计 21 个 child entries（19 core + 2 patch filesystem variants），不在 standalone ramdisk。
- standalone ramdisk inventory 有 17 entries，含 `/init`、`/patch_avb_key`、build.prop 和空目录；未发现 fstab、init rc、ueventd、modules.load 或 `.ko`。这只能证明该 archive 内没有这些条目，不能证明其他分区/路径没有模块加载来源。
- 因此不能把 header-v2 boot.img 内嵌 ramdisk 与独立 ramdisk 分区混为一谈；也不能直接套用现代 vendor_boot/init_boot 布局或公开 Linux SD-root initramfs。

### 6.2 DTBO 选择仍未知

九个 DTBO entry 的 runtime ABL 选择没有直接证据。Entry 8 / board-id `0x206a` 只是候选，不是已选中事实；stock entry 8 有 145 个 fragment targets，指向大量 Huawei vendor-only nodes，与最小 ACK board DTS 不兼容。DT table entry 的 `id/rev/custom` 与 overlay root 的 `qcom,board-id` 是不同字段，不能由一个推导另一个。需要同一次 HOS4.3 boot 的 ABL selection log/trace 与 final FDT 才能关闭。

### 6.3 AVB / vbmeta 已知事实与 anomaly

ROUND64 使用 pinned ACK tree 中已有 AOSP `avbtool 1.4.0` 只读 `info_image`，报告 15 个 image 中 14 个有 footer。root `vbmeta.img` chain metadata 的 targets 包含 `boot`、`ramdisk`、`dtbo` 等；独立 ramdisk 与 DTBO 不因分区独立就自动脱离 AVB 覆盖。footer inventory、descriptor target、签名/rollback policy 是不同证据面；不得把 target 名称当成可直接修改且不必重签的许可。

`vbmeta_cust.img` 必须保留为 UNKNOWN，不能自行修复或解释：
- 文件 inventory size = 1 MiB。
- ROUND19 offset-zero parser 看到一个包含 `cust` hashtree descriptor 的结构，但 public-key/auth-size 有内部不一致。
- ROUND64 AOSP avbtool 从文件尾识别 AVB footer；其 original-image-size / vbmeta pointer 指向 offset 10,375,168，超出 1 MiB 文件；该位置解析出的对象报告 `Algorithm: NONE`、无 descriptors。
- root vbmeta 仍声明 chain target `vbmeta_cust`。

这是两个不同偏移/结构的观察结果，不是可互相覆盖的结论。缺少完整源文件/partition manifest，无法判断是截断、vendor layout 还是其他原因。`cust` 的实际 descriptor coverage 仍 UNKNOWN。不得截断/补齐/重建/重签 `vbmeta_cust`，也不得绕过 AVB。

### 6.4 Boot tool 与真实 HOS4.3 ABL policy

ROUND65 找到 pinned ACK workspace 内 `mkbootimg`，其 `--help` 支持 header-v2、kernel、ramdisk、DTB 和 page-size 参数；它只构建一个包含 embedded sections 的 boot image，不负责单独 ramdisk 分区，也不管理 Huawei ABL DTBO 选择、AVB footer/vbmeta chain 或 signing policy。`unpack_bootimg` 未找到。工具存在不等于重建 stock 结构所需参数/策略已知。

同设备公开 Linux 7.0/HOS4.2 参考报告 fastboot boot 被拒绝，且使用单独 ramdisk 分区；这是 same-device public reference，不是 HOS4.3 Android ABL policy。HOS4.3 是否接受 RAM boot、是否必须写分区、如何选择 ramdisk/DTBO 仍 UNKNOWN。不能把该 Linux 参考直接当作 Android 17 的测试路径。

### 6.5 关闭 D 的最小证据

在任何打包前，至少需要：
1. HOS4.3 stock boot header v2 的完整可信字段清单（包括保留字段、页大小、embedded kernel/ramdisk/DTB payload boundaries、padding/offset），并确认 ABL 实际消费 embedded ramdisk 还是独立 ramdisk，或两者如何组合；
2. standalone ramdisk partition 的完整格式/消费关系与 Android 17 first-stage init/fstab/module-loading expectations；
3. ABL 实际选中的 DTBO entry、table id/rev/custom matching contract、rootparam identity requirements，以及 base DTB + selected DTBO 的最终组合结果；
4. boot、ramdisk、dtbo、vbmeta 与 chained vbmeta 的完整 AVB descriptor/chain 覆盖；`vbmeta_cust` 需要原始完整对象/partition size/manifest 或厂商工具链证据解释 anomaly；
5. HOS4.3 signing key ownership/可用签名路径、rollback index/location policy、verification/enforcement 状态；不要求也不应公开 key 或签名秘密，只需权威 policy 与合法操作路径；
6. 可恢复的实际测试方式：ABL 接受 RAM boot 还是必须写入分区、精确 rollback/restore 方案、验证步骤与明确单独授权。当前 ROUND136 不授权这些动作。

**D 状态：BLOCKED。** 现有 metadata inventory 已有价值，但还不是可重建、可验证或可启动的 Android boot package specification。

## 7. 四项综合：最短闭环顺序

以下是依赖顺序，不是当前执行授权：

1. **继续完成 ROUND135 R3。** 锁定候选 tree SHA，完成 schema/真实 DTB/Kconfig/object/Image/Host checks。R3 PASS 后只宣布 offline build/DTB integration validated。
2. **先关闭 A（final FDT + entry route）。** 没有有效 RAM map 与 firmware/secure reservation reconciliation，后续 board DTB/boot package 都没有安全内存基础。要求 selected DTBO 与 final FDT 在同一证据链中确认。
3. **并行关闭 B（physical input parents）。** 以 schematic/netlist 或权威 HOS4.3 regulator runtime/bootloader state 证明 S4/L5/L6/L9/L17/S8 的输入和 enable owner；不能用 dummy regulator 代替。
4. **关闭 C 的 UFS-specific minimum gate。** 用实际 HOS4.3 Command DB AUX map / runtime vote 或其他权威证据，证明 UFS 必需 corner 由 ACK MMCX plain descriptor 满足，或明确需要怎样的 parent behavior。先不做 full ARC driver port，除非证据证明 UFS 首启依赖它。
5. **关闭 D（boot contract）。** 确认 boot-v2 + standalone ramdisk 消费、selected DTBO、AVB chain/`vbmeta_cust` anomaly、sign/rollback policy、toolchain 和 reversible test route。
6. **1号 AI 单独审查并发布下一份明确授权。** 只有 A/B/C/D 的首启门槛有可审计闭环、候选 DTB 与包格式完全固定、回退路径明确后，才讨论后续 boot package 或设备测试；本报告本身不授权。

## 8. 哪些事项需要本地 WorkBuddy Agent？

本 ROUND136 明确禁止新下载/解包 HOS4.3 固件、补采敏感数据、设备接口操作，并规定本轮只使用仓库已有脱敏报告与公开源码。因此：

- **本轮没有启动 WorkBuddy Agent，也没有要求其暂停或改变 ROUND135 R3。**
- A 的 final pre-entry FDT/entry trace、B 的 PMIC runtime/bootloader rail state、C 的 runtime RPMh votes/Command DB effective map、D 的 ABL selected DTBO/ramdisk/AVB source provenance 都需要 target-local HOS4.3 evidence；现有仓库脱敏材料不足以证明这些事实。
- 这些资料若已存在于用户授权的本地既有采集物，可在未来单独任务书下由 Agent 做离线只读脱敏整理；若必须从新固件或设备实时采集，则不属于 ROUND136 当前授权范围，必须先由用户明确批准新的安全范围和采集方式。

未来独立只读取证的最小输出建议（不在本轮执行）：

| 领域 | 允许输入（需另行授权） | 输出字段 | 明确禁止 |
|---|---|---|---|
| A | 已有 HOS4.3 ABL trace 与已采集 final FDT | entry route、selected DTBO、`/memory`/`linux,usable-memory`、37 reserved children 的脱敏区间/大小/属性/引用、EFI `/chosen` 参数存在性 | 设备连接、ABL shell、bootloader 操作、重新提取固件、上传 raw FDT |
| B | 已有板级 schematic/netlist 或已采集 regulator runtime snapshot | rail 名称、parent net/parent regulator、输入范围、状态/enable owner、测量来源 | 探针/万用表实测、PMIC 写操作、猜测 parent 或电压、上传原理图敏感整页 |
| C | 已有 HOS4.3 脱敏 ARC property report、已获准的 Command DB 元数据与 runtime trace | provider/resource、完整 parent edges、AUX corner map、ACTIVE/SLEEP votes、UFS 对应 vote | 新固件提取、上传 AUX binary/原始 FDT、修改驱动/DTS、运行设备测试 |
| D | 已有 stock image inventory、AVB parser 原始脱敏输出、ABL boot log/partition manifest | header fields、ramdisk consumption、DTBO table match/selected entry、descriptor targets、`vbmeta_cust` 来源、签名/rollback policy、boot acceptance | 写镜像、AVB signing、修改 footer/vbmeta/DTBO/ramdisk、fastboot/recovery/分区操作 |

这些是未来 taskbook 的输入/输出建议，不是本轮 Agent 命令。

## 9. 证据差异与审查限制

### 9.1 已解决的历史口径冲突

- HOS4.3 `/memory`：ROUND19 最初的 no-node 表述已由后续校正为 zero-size placeholder。按最终校正使用：存在 `device_type="memory"`，但 `reg` size=0，不能形成 usable RAM。
- HOS4.3 reserved-memory 数量：ROUND19 早期 34 children 被 ROUND24 校正为 37；本报告统一使用 37。
- ARC parent edges：ROUND11 四条被 ROUND14/ROUND51 增补为至少五条；完整总数未证实。
- ARC resource/set/corner/dropout/proxy：ROUND14 已取得，ROUND51 已解释；本报告不再把这些字段列为未知。缺失的是完整 graph census、完整 AUX map、effective DTBO 与 runtime vote。
- ROUND135 Ubuntu UFS DTB：AI1 reconciliation 明确 Ubuntu DTB 只提供拓扑比较，缺少 Ubuntu 7.3.1-loa UFS driver source，不能据此推翻 ACK patch5 的 dual-GenPD / required-OPP 设计。

### 9.2 证据等级

- `TARGET-LOCAL HOS4.3`：仓库既有脱敏报告/提取记录；不等同于本轮重新读取固件或实时设备。
- `PINNED ACK SOURCE`：固定 commit `8ad08f75...` 的实际源码。
- `SAME-DEVICE PUBLIC REFERENCE`：公开 DBY-W09 Linux 7.0/HOS4.2 项目；只用于结构/流程参考。
- `SAME-SOC REFERENCE`：其他 SM8250 的 FreeABL / Qualcomm source；不能代替 Huawei ABL。
- `PUBLIC VENDOR SOURCE ANALOGUE`：Qualcomm KONA vendor source commit `cad09e...`；用于解释 ARC 语义，不证明 HOS4.3 runtime binary。
- `INFERENCE`：基于 artifact/source 形成的推断，明确不能升格为目标设备直接观察。

否定证据只覆盖原报告明确扫描的文件/属性范围。例如 ROUND11 的 HOS4.3 base-FDT property-name scan 没有发现 `vdd-s*-supply`，不代表所有 bootloader runtime state 或 schematic 都不存在 parent rail。

### 9.3 本轮未执行

本轮没有运行 dtc、dt-schema、dtbs_check、Kconfig、对象编译、Kleaf、Host tests 或设备测试；这些由 ROUND135 R3 taskbook 中的本地 Agent 执行。本轮没有重新解析本地 HOS4.3 固件、没有设备连接、没有写入或打包。

## 10. 1号 AI 决策事项

1. 保持 ROUND135 R3 原样继续；不要因 A/B/C/D 的首启 blocker 停止 Image/DTB 离线验证。
2. R3 PASS 后，状态只标记为 `PASS — BUILD/DTB INTEGRATION ONLY`，Phase E/F 仍 BLOCKED，Phase G NOT RUN。
3. 是否把 C 的 UFS-specific corner proof 定义为首次启动硬门槛；AI2 建议在未证明 plain MMCX 足够前，保持 BLOCKED，不擅自添加 shared MMCX→MX parent 或新 ARC driver。
4. 为 A/B/D 的 target-local evidence 制定独立、明确授权的只读任务；本 ROUND136 不允许获取新 firmware/device data。
5. 本报告不批准 boot package、AVB 修改、签名、分区写入、fastboot/recovery 或任何实机启动尝试。

## 11. 完整来源索引

### 任务书与 ROUND135 候选

- ROUND136 taskbook：`firmware-analysis/round136-preboot-blocker-audit/AI2_ROUND136_TASKBOOK.md` — blob `031eb24c01272c665268dd2521d4983edce64a27`。
- ROUND135 23-patch manifest：`kernel-baseline/round135/ROUND135_23_PATCH_SERIES_MANIFEST.md` — blob `9188de2022f88c374bfcaa367c505428812608d9`。
- ROUND135 R3 taskbook：`kernel-baseline/round135/TEST_AGENT_ROUND135_R3_TASKBOOK.md` — blob `729236571a3b788dfbad464f6430b31d81955bcf`。
- ROUND135 Ubuntu reconciliation：`kernel-baseline/round135/AI1_ROUND135_UBUNTU_REFERENCE_RECONCILIATION.md` — blob `f4dca432c1b244e61aa2d51bbf0ea3f2757a1e4f`。
- Frozen patch 5 UFS dual-GenPD implementation：`kernel-baseline/round61/patches/round33-checkpatch-clean.patch` — blob `f1d54e5e0379183fbdfb3ca6132c6d0fc61d4622`。
- ROUND135 board DTS patch 22：`kernel-baseline/round135/series/22-round135-huawei-dby-w09-real-dts.patch` — blob `ab0108364c835d87ac35ca670347d9d0001a821d`。

### A — memory / ABL / EFI

- ROUND19 memory/reserved-memory review：`kernel-baseline/round19/hos43-memory-reserved-memory-handoff-review.md` — blob `06f91fdf6853b382dfe8fd8da7a83c7aaf24c902`（历史初始口径，须结合后续校正）。
- ROUND42 SM8250 ABL FDT prerequisite：`kernel-baseline/round42/hos43-memory-handoff-sm8250-abl-fdt-prerequisite.md` — blob `1ba87a9079f00aed370c82d3b9a1c8c76ded1c24`。
- ROUND43 fixed ACK classic vs EFI memory scan：`kernel-baseline/round43/ack-6.18.33-fdt-memory-scan-classic-vs-efi-handoff.md` — blob `2a89fdf94ec59d4744d6b2eb752760737c34da53`。
- ROUND24 HOS4.3 reserved-memory/consumer map：`firmware-analysis/round24/round24-hos43-reserved-memory-and-consumer-map.txt` — blob `a0167df755521fa583b4ce3f73b1b2260306b426`。
- Phase E gate summary：`kernel-baseline/round61/phase-e-board-dts-memory-power-gates.md` — blob `3e9f18db04ec4833dd4b033570a816482489cb7b`。
- ACK `drivers/of/fdt.c` — blob `a931cd4beaaa6e3becc3692e3b4b8a0e42d6a691`, `early_init_dt_scan_memory()` lines 1034–1086; reserved-memory scan separate.
- ACK `arch/arm64/boot/dts/qcom/sm8250.dtsi` — blob `adf6b49b52c48ca05ed6d0c1251f97ace664ef9d`, memory placeholder lines 683–687; UFS OPP lines 2550–2576.
- ACK `drivers/firmware/efi/fdtparams.c` — blob `b815d2a754eef33b5157830fc739ca47dd666d3f`, lines 84–133.
- ACK `drivers/firmware/efi/libstub/fdt.c` — blob `6a337f1f8787b3bc68f771500f9fcd4b44a7b4f7`, `update_fdt()` lines 80–138, `update_fdt_memmap()` lines 147–181.
- ACK `drivers/firmware/efi/efi-init.c` — blob `a65c2d5b9e7b6d119206ed0380b4e7574e436c01`, `reserve_regions()` / `efi_init()` lines 159–278.
- ACK `arch/arm64/kernel/setup.c` — blob `56e69b249c2c5ec911f01c4a4b0a1ee96ae33707`, `efi_init()` before `arm64_memblock_init()` lines 317–335.
- ACK `Documentation/arch/arm64/booting.rst` — blob `e4f953839f7181ef5016e7f25e3f729dc5cb7bd7`, ARM64 normal entry vs EFI stub description lines 90–110.

### B — PMIC parents

- ROUND21 ACK PM8150 parent supply / dummy semantics：`kernel-baseline/round21/ack-pm8150-vrm-parent-supply-gap.md` — blob `3402acb92c7fe794fbb106097e00c81e87bcc845`。
- ROUND47 PM8150 mode/DRMS capability：`kernel-baseline/round47/ack-pm8150-regulator-mode-drms-capability-review.md` — blob `656f3dfc1aad11d0c77f4fa29bd542d4b13be030`。
- ROUND16 ARC parent graph distinction：`kernel-baseline/round16/hos43-rpmh-arc-parent-graph-to-ack-dts.md` — blob `0b362af9f603ad6d6e3c1546a8b0aedfa4b83658`。
- ACK `drivers/regulator/qcom-rpmh-regulator.c` — blob `109f0aae09b1df431d2e14d45a64d115e87cdec4`, PM8150/PM8150L tables lines 980–1034; `rpmh_regulator_init_vreg()` lines 425–455.
- ACK `drivers/regulator/core.c` — blob `39d317ad73a33c4aa27e179cc436d8bf4daf5bcc`, `regulator_resolve_supply()` lines 2046–2105.
- ACK `drivers/regulator/dummy.c` — blob `e5197ec7234d01518b26844c555f3900a4ee5750`, dummy regulator constraints lines 22–30.
- ACK `drivers/regulator/of_regulator.c` — blob `32e88cada47a254c3b184f3d1d6d8c1dccdfcc28`, regulator mode/load constraints parsing lines 80–300.

### C — ARC / RPMHPD

- ROUND24 ARC logical corner semantics：`kernel-baseline/round24/hos43-arc-logical-corner-dt-semantics.md` — blob `fae50adc342e84f3e24a793f4fad85ff0134cf88`。
- ROUND30 MMCX→MX equivalence gate：`kernel-baseline/round30/sm8250-rpmhpd-mmcx-mx-parent-equivalence-gate.md` — blob `c6091bd1461e98e1dd4be4bae754096104726788`。
- ROUND50 HOS ARC vs ACK RPMHPD：`kernel-baseline/round50/ack-sm8250-mmcx-mx-arc-parent-semantics-and-remaining-local-gate.md` — blob `d83de793c474769bb1df49c9bedbf6bc152e3f9b`。
- ROUND51 value/proxy/fifth-edge reconciliation：`kernel-baseline/round51/round14-arc-value-semantics-proxy-vote-and-round11-edge-reconciliation.md` — blob `3c85bd2ae648e1975fb2da50eb813ced4844f1f0`。
- ACK `drivers/pmdomain/qcom/rpmhpd.c` — blob `4c3cbf3abc7504cce3b8211c339b7ada03d65e38`, descriptors lines 70–155, SM8250 mapping lines 455–480, parent registration lines 1020–1065.
- ACK `drivers/pmdomain/core.c` — blob `8adc78d62d05f1f7432a154c7d71ce0ade3f406a`, `genpd_xlate_performance_state()` / `_genpd_set_parent_state()` lines 400–455.
- ACK `drivers/opp/core.c` — blob `157c84b689feba9ae2c446083e42de63e94a38a6`, `dev_pm_opp_xlate_performance_state()` lines 2757–2795.

### D — boot-v2 / AVB

- ROUND18 same-device boot/ramdisk/DTBO review：`kernel-baseline/round18/dby-w09-legacy-boot-avb-packaging-review.md` — blob `fa56c4b53d4c30faecaa925c0db7c7ade8e56e8b`。
- ROUND64 AVB/footer/DTBO/ramdisk evidence：`firmware-analysis/round64/round64-dby-w09-hos43-bootv2-ramdisk-dtbo-avb-evidence.md` — blob `b1e27ce5ad37280ed4ed48f1560e10cfad332617`。
- ROUND65 fstab/vbmeta_cust/boot tool audit：`firmware-analysis/round65/round65-first-stage-fstab-vbmeta-cust-and-boot-tool-audit.md` — blob `31f08a03694431c12a076f7d69fce070842944fa`。
- Phase F gate summary：`kernel-baseline/round61/phase-f-boot-packaging-avb.md` — blob `1031ad13eb7c70e9e61eebf7acc4aba6d4f0c109`。

## 12. 安全范围与最终意见

本轮仅读取仓库中的脱敏报告、固定 ACK 源码和候选 patch。没有连接平板，没有 USB/ADB/fastboot/recovery/root/serial，没有访问 bootloader shell，没有读取/写入分区，没有下载/解包新 HOS4.3 固件，没有运行构建/测试，没有生成或修改 boot/ramdisk/DTBO/vbmeta，也没有修改 ROUND135 候选、R3 taskbook 或任何 AI1 分支。

**最终意见：继续 ROUND135 R3；把本报告的 A/B/C/D 维持为首次安全实机启动前四个独立 BLOCKED 门槛。R3 的离线 Image/DTB PASS 不得跨越这些门槛。ROUND136 完成后停止，等待 1号 AI 决定后续只读证据任务。**

---

AI2 ROUND136 独立审查报告结束。