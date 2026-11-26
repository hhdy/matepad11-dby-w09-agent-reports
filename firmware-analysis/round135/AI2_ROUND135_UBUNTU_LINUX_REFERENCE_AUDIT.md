# AI2 独立审查报告：DBY-W09 Ubuntu Linux 参考包

- 审查对象：用户上传的 `DBY-W09_LINUX_LASTEST_VER (1).zip`
- 审查日期：2026-11-26
- 项目目标：Huawei MatePad 11 DBY-W09，Android ACK `android17-6.18.33_r00`
- 对照对象：ROUND135 修正后的 23-patch 候选树 `afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- 审查角色：AI2 独立审查；不代替 AI1 的源码决策

## 1. 结论摘要

**结论：有条件采纳为 DBY-W09 硬件/设备树参考资料；不得将该 Ubuntu FIT、内核、模块或其 DTB 直接作为 Android 启动产物。**

该包包含三个 FIT 启动镜像及可提取的设备树：110 full、110 stable、190 full。三个 FIT 内嵌 DTB 均可解析，且包内 `SHA256SUMS` 所列 25 个文件全部校验通过。110 full 与 110 stable 的 UFS 控制器、UFS PHY、UFS 电源轨和 OPP 节点一致；190 full 相对 110 full 的 DTB 差异集中在面板 `compatible` 值。

本次最重要发现：Ubuntu DTB 的 UFS 控制器 `power-domains` 只指向 GCC 的 `UFS_PHY_GDSC`；MMCX 性能等级是通过 UFS OPP 节点的 `required-opps` 引用 RPMh power-domain OPP 实现的。ROUND135 当前 DTS 草稿则把 RPMHPD MMCX 与 GCC UFS_PHY_GDSC 同时写入 UFS `power-domains`，且当前草稿片段没有看到与 Ubuntu 对应的 UFS OPP table。**这是需要 AI1 优先核对的高优先级差异，不在本报告中直接判定为错误或自行修改。**

## 2. 包内容与完整性

README 声明：更新日期 2026-11-25、Linux 内核 `7.3.1-loa`、Ubuntu 26.04 GNOME。压缩包共 35 个目录/文件条目，包含三个 FIT、`misc-boot-recovery.img`、内核模块归档、音频配置/工具、显示修复脚本及 Venus 控制脚本。

| 文件 | SHA-256 |
|---|---|
| 原始 ZIP | `ac2b6f80abb12a4fc15b4cf5dc76beaef21ffe72bc2125a767aa506d9beb86ca` |
| `FIT_110/dby-w09-110-full.itb` | `c2acce19b70f7d4bc9e86e9fc49289ea44c1084010817902023eb01af9a50272` |
| `FIT_110/dby-w09-110-stable.itb` | `581a96f57b6e7b09dabc5bbda7be40df8701d584b539941875b23ed19f9b7c22` |
| `FIT_190/dby-w09-190-full.itb` | `c03480bbd3b0302421ef011bbc52d0ce7949a65f45317bd452d81c8176d4031d` |

包内 `SHA256SUMS` 的 25 项文件校验全部通过。该结果只证明文件与包内校验清单一致，不证明发布者身份、来源链真实性或设备实测真实性。

## 3. FIT / DTB 结构审查

三个 `.itb` 文件本身是 FIT 格式 FDT 容器。已从每个 FIT 的 `/images/fdt` `data` 属性提取 DTB，并检查其 FDT 结构。提取 DTB 的 SHA-256：

| FIT | 提取 DTB SHA-256 |
|---|---|
| 110 full | `613bf834f0a0e4188bd203e2cc3acc07825ce6e82a6375b9789cfa5b451b5364` |
| 110 stable | `ff891f22edcbcf14ad3925b078904267c0d07589d222d39ce3f964b3654585d1` |
| 190 full | `eed35d83d991db8232fa4bb4cc944216605295ac30f0e773222e0e4efcea6168` |

110 full DTB 根节点：
- `model = "Huawei MatePad 11 (DBY-W09)"`
- `compatible = "qcom,sm8250-mtp", "qcom,sm8250"`

注意：model 字符串标记为 DBY-W09，但根节点 compatible 仍是通用 Qualcomm SM8250 MTP compatible，并非 `huawei,dby-w09`。因此不能仅凭 model 字符串就把该 DTB 视为 Android 专用、已完成 schema 验证的 DBY-W09 DTS 源码。它仍然是非常有价值的同设备 Linux 参考 DTB。

## 4. UFS / PHY / OPP：重点发现

110 full 与 110 stable 的以下节点及关键属性一致：
- UFS host：`/soc@0/ufshc@1d84000`，compatible 包含 `qcom,sm8250-ufshc`，状态 `okay`，双 lane。
- UFS PHY：`/soc@0/phy@1d87000`，compatible `qcom,sm8250-qmp-ufs-phy`，状态 `okay`。
- UFS host 的 `power-domains` 解析为 GCC provider（`qcom,gcc-sm8250`）及 ID `4`；该 ID 对应此 DTB 中 GCC 的 UFS PHY GDSC 电源域。
- UFS PHY 的 `power-domains` 同样引用 GCC provider / ID `4`。
- UFS host 有 37.5MHz 和 300MHz 两个 OPP 节点；其 `required-opps` 分别引用 RPMh power-controller OPP 表中的 level 64 与 level 256。

Ubuntu DTB 中 UFS 电源消费者关系：

| 消费者属性 | DTB 指向的 PMIC regulator | DTB 电压窗口 |
|---|---|---:|
| `vcc-supply` | PM8150 L17 (`vreg_l17a_3p0`) | 2.496–3.010 V |
| `vccq-supply` | PM8150 L6 (`vreg_l6a_1p2`) | 固定 1.2 V |
| `vccq2-supply` | PM8150 S4 (`vreg_s4a_1p8`) | 1.8–1.92 V |
| UFS PHY `vdda-phy-supply` | PM8150 L5 (`vreg_l5a_0p88`) | 固定 0.88 V |
| UFS PHY `vdda-pll-supply` | PM8150 L9 (`vreg_l9a_1p2`) | 固定 1.2 V |

UFS host 的 `vcc-max-microamp`、`vccq-max-microamp`、`vccq2-max-microamp` 在该 DTB 中均为 800000。UFS OPP 为 37.5MHz→RPMh level 64、300MHz→RPMh level 256。

### 4.1 与 ROUND135 当前 DTS 草稿的差异

当前 ROUND135 patch 22（`kernel-baseline/round135/series/22-round135-huawei-dby-w09-real-dts.patch`，blob `ab0108364c835d87ac35ca670347d9d0001a821d`）的 UFS host 草稿写有：

```dts
power-domains = <&rpmhpd RPMHPD_MMCX>,
                <&gcc UFS_PHY_GDSC>;
```

同一段草稿没有出现 Ubuntu DTB 中的 UFS OPP table / `required-opps` 配置。Ubuntu DTB 则将 GCC UFS PHY GDSC 放在 `power-domains`，并通过 UFS OPP 的 `required-opps` 引用 RPMh performance level。

**AI2 建议 AI1 优先核对：**
1. ACK `android17-6.18.33_r00` 的 UFS host 驱动及 OPP / GenPD 实现，确认 MMCX 应通过 `required-opps` 还是 `power-domains` 表达。
2. 检查 ROUND135 当前双 `power-domains` 声明是否与 ACK 驱动的 power-domain cell 数量、调用路径及 SoC DTSI 约定一致。
3. 检查是否需要为 UFS host 补充 OPP table，以及 37.5MHz / 300MHz 与 RPMh level 64 / 256 是否适用于目标 ACK 驱动和设备。
4. 只有在 ACK 源码、binding/schema 与驱动调用路径核实后，才决定是否修改 patch 22；不能仅照抄 Ubuntu DTB。

这是静态差异审查建议，不是已完成的 ACK 驱动验证，也没有进行任何构建或设备测试。

## 5. 屏幕 / 双 DSI 参考

110 full DTB 包含两个启用的 SM8250 DSI controller（`dsi@ae94000` 与 `dsi@ae96000`），并带有双 DSI 相关属性。主面板节点 compatible 为 `huawei,dby-w09-panel`。

110 full 与 190 full 的 DTB 对比显示，面板节点 `compatible` 从 `huawei,dby-w09-panel` 改为 `huawei,dby-w09-190-20d`, `novatek,nt36523`；README 将 190 full 限定为 BOE 190_20d 面板。该差异为面板选择提供了重要线索，但不能仅凭包内 README 推断用户手中设备的实际面板型号。

110 full 与 110 stable 的面板 compatible 一致；full DTB 另有 `rotation` 属性，而 stable DTB 未见该属性。两版本还有音频、远端处理器、视频编解码、GPIO/电源引用等差异，不能把 stable 与 full 的差别简单概括成仅仅“有无音频”。

**建议：** 将 110/190 面板 compatible、双 DSI 节点和相关电源消费者作为 DTS 对照资料；当前项目 `ACTIVE_PROFILE` 仍应保持 UNKNOWN，直到有目标设备面板身份的可靠证据。

## 6. PMIC / 电源树：能证明与不能证明的内容

Ubuntu DTB 确实包含 PM8150 / PM8150L RPMh regulator provider，以及 UFS、PHY、DSI、面板消费者到部分 regulator 的引用。它可以帮助交叉核对 regulator 名称、电压窗口和消费者连接。

但对 PMIC regulator provider 节点的静态检查，没有发现可用于证明 PMIC 输出物理输入网络的 `vdd-supply` / `vin-supply` 等输入关系；本 DTB 中出现的 `vin-supply` 位于 panel fixed-regulator 节点，不是 PM8150 VRM 输出的完整板级输入拓扑。

因此，该包**不能补齐** ROUND36 / Phase E 中 DBY-W09 PMIC 物理输入供电拓扑的证据缺口，也不能替代板级原理图、boardview、netlist 或实测证据。不要据此臆造 `vph_pwr`、`vdd-s*-supply` 或 fixed regulator。

## 7. 内存交接 / ABL handoff

本次审查提取并检查的是 Ubuntu FIT 内嵌 DTB。它不包含 Android ABL 向目标 ACK 内核最终交付的 live FDT 证据，也不能证明 Android 启动时最终 `/memory/reg`、保留内存区域或 ABL fixup 的行为。

因此，ROUND36 Phase E 的 ABL memory handoff / final FDT 缺口仍为 BLOCKED。不能把 Ubuntu DTB 中的静态内存描述当作 Android ABL handoff 证明。

## 8. 其他可参考内容

- 音频：包内有 `matepad_tfa9874.c`、TFA9874 配置 XML、UCM 配置及服务脚本，可作为四扬声器/麦克风路径的线索；不能直接纳入 ACK 内核，也不能据此声称 Android 音频已适配。
- 显示修复：包含显示电源与屏幕修复脚本。README 记录偶发线条、屏幕重建和触摸短暂失效等已知问题。这些信息可用于理解 Linux bring-up 风险，不等于 Android 显示问题已有解决方案。
- Venus：README 声明 Venus 模块默认 blacklist，需通过关屏→加载→亮屏流程启用，并记录启用时显示干扰。这是 Linux 用户空间与驱动组合的行为说明，不应直接移植成 Android 启动策略。
- 内核模块：归档标记为 `7.3.1-loa` 配套模块；必须与其对应内核匹配，不应放入 ACK 6.18.33。
- README 中包含向 `reserved3` / `misc` 写入镜像的命令。本次没有执行这些命令，也不建议在本项目阶段照搬。

## 9. 证据等级与限制

| 项目 | AI2 判断 |
|---|---|
| ZIP 内部完整性 | PASS：SHA256SUMS 25 项全部通过 |
| FIT 内嵌 DTB 提取与结构解析 | PASS：三个 FIT 均成功提取 DTB 并解析 |
| DBY-W09 设备树参考价值 | 有价值：model 标记 DBY-W09，包含 UFS / 双 DSI / PMIC 等节点 |
| UFS 电源消费者与电压配置 | 可作为交叉参考；不是 ACK 6.18.33 的直接验证 |
| UFS GenPD / OPP 对照 | 发现高优先级差异，要求 AI1 对照 ACK 驱动与 binding |
| 面板实际型号 | UNKNOWN：README 的 110/190 描述不能证明用户设备实际面板 |
| PMIC 物理输入供电拓扑 | NOT PROVEN |
| Android ABL 最终 FDT / 内存交接 | NOT PROVEN |
| ACK dtc / dt-schema / DTB build | NOT RUN |
| ACK UFS compile / Image build / Host regression | NOT RUN |
| 实机启动或硬件测试 | NOT RUN |

工具限制：本次进行了 ZIP 清单/校验、FIT 结构解析及内嵌 DTB 属性提取。未运行 `dtc`、`dt-schema`、ACK 构建系统或设备测试。因此本报告不是 DTS schema 通过证明。

## 10. 给 AI1 的行动建议

1. 将此 Ubuntu 包登记为只读参考基线，保留原始 ZIP SHA-256 与三个 DTB SHA-256。
2. 优先复核 ROUND135 patch 22 的 UFS `power-domains` 与 OPP 建模差异；审查结果应引用 ACK 6.18.33 实际驱动、binding 和 SoC DTSI，而不是只引用 Ubuntu DTB。
3. 对照 UFS rails、双 DSI、panel compatible 和 regulator 消费者关系；任何移植修改都应单独形成补丁并重新审查。
4. 不要从该包推断 PMIC 物理输入拓扑或 ABL 最终内存图；Phase E 原有阻塞项保持不变。
5. 本报告不授权 ROUND135 下游测试，不授权启动新的 Agent 任务，也不改变当前候选树 SHA。

## 11. 安全与范围声明

本次只进行了离线文件检查。没有连接平板，没有执行 USB / ADB / fastboot / recovery / root / serial 操作，没有读取或写入设备分区，没有执行刷机、boot package、AVB、DTBO、ramdisk 打包或设备启动测试；没有运行包内安装脚本或执行其写盘命令；没有修改 ROUND135 源码、补丁或候选树。

**最终意见：Ubuntu 参考包值得纳入 DBY-W09 项目证据库；它显著增强 UFS / PHY / 双 DSI / 面板与音频适配的参考资料，但不能解除 Phase E 阻塞，也不能替代 ROUND135 的 ACK 源码验证。UFS GenPD/OPP 差异是应优先交由 AI1 核对的具体事项。**

---

AI2 独立审查报告结束。