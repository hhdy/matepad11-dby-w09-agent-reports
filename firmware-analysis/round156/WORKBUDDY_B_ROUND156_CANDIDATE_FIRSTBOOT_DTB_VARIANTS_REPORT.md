# ROUND156 — WorkBuddy Window B: Candidate First-Boot DTB Variants

**执行者**：WorkBuddy Window B（2 号 Agent），独立 WorkBuddy 会话。
**任务类型**：离线、scratch-only 的 DTB/DTBO 重建与结构校验。
**停止点**：报告交付即 STOP。未创建 DTBO 容器或 boot.img，未触碰设备。

---

## 1. 范围与隔离声明

| 项 | 实际情况 |
|---|---|
| 使用的源码工作区 | 仅 `round154-windowB/`、`round155-windowB/`（B 侧自己的冻结工件）和新 scratch `r156-windowB/scratch/` |
| Window A 私有工作区 | **未访问** 其 ABL、raw backup、分区镜像、日志；本报告不含任何 A 侧私有路径、二进制或密钥 |
| 设备操作 | 无 ADB、root、fastboot、recovery、分区读写、刷机、重启、启动 |
| 接受分支 / 已收补丁 | 未改动；`patched.dts`、`patched.dts.pp`、`patched.dtb`、`minimal-firstboot.dts/.dtbo`、`patched+minimal.dtb` 全部在交付前重新哈希，与开工基线一致 |
| 构建范围 | 只编译单板 DTB 与 199 B overlay；**无** 完整 Image / kernel 构建 |
| 打包范围 | **无** DTBO 容器、**无** boot.img；任务书 §4.6 明确要求等 Window A 的 ABL 控制流报告 |

所有「验证」均为主机侧 `dtc` 1.7.0 / `fdtoverlay` 1.7.0 和自写只读 FDT 解析器完成；**主机 apply 成功不等于华为 ABL 能识别或应用该 overlay**。

---

## 2. 结论总表

| 变体 | 内容 | 大小 (B) | SHA-256 | 结论 |
|---|---|---:|---|---|
| A | 无 overlay 的 RAM-patched base | 108,680 | `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` | **PASS**：从冻结 pp 逐字节复现 |
| B | 同 base，仅 UART12 `status` 直改为 `okay` | 108,676 | `47ca4ff748baf6e72bc4ab26c4369ef13a15df9443a0a8dac16135ac0a7e78c7` | **PASS**：与 A 仅 1 属性差异 |
| C | A base + target-path UART overlay（host apply） | 108,676 | `647af49b8c21198d9cba99fac444131aaf95e86c99b28af87b610fc46b30cea2` | **PASS**：dtb 与 dtbo 均逐字节复现冻结工件 |
| overlay | 199 B minimal-firstboot target-path dtbo | 199 | `05494d47506a127f7826fb3db3f3319a9865fbcea5c59fd3c3f603653af1a1c2` | **PASS**：从 435 B 源重建一致 |
| 负测试 | 未知 target path overlay | 195 | `f24fe0aca868a943c9bba5092fb1921e481a16909052b7b1d9105ddf5f43f17a` | **PASS**：`fdtoverlay` rc=1 `FDT_ERR_NOTFOUND` |

**内部有效性**：A/B/C 三者的 RAM 图、18 项 reserved-memory、905 节点/239 phandle 无碰撞、UFS host/PHY 依赖闭包、空 `/chosen` 全部一致且通过检查。
**不在 Window B 证据内**：ABL 是否允许无 overlay 直接启动 base、是否要求特定 DTBO 容器、board-id/msm-id 选择策略、DTBO 的加载/应用顺序、三段 RAM 在启动链中的实际写入者与时序。必须由 Window A 的 ABL 控制流报告闭合。

**任何变体均不可标记为 flash-ready。**

---

## 3. 冻结输入、工具版本与构建命令

### 3.1 冻结输入（开工与交付 SHA-256 一致）

| 文件 | 字节 | SHA-256 |
|---|---:|---|
| `round154-windowB/src/patched.dts` | 15,800 | `e5c6a80382d582ab3a95078b84bb7a0d4a79eac58f1bd84b252be313affc83ef` |
| `round154-windowB/out/patched.dts.pp` | 160,988 | `b2b26acbbea2ba93d93c6b03e41e5cb47d503f2e230dd080bc216c39ca49eb10` |
| `round154-windowB/out/patched.dtb` | 108,680 | `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` |
| `round155-windowB/src/minimal-firstboot.dts` | 435 | `515d5a9bfd82e9b8073d172075e05dc454e8b79052de553ac52e9bf99e64114b` |
| `round155-windowB/out/minimal-firstboot.dtbo` | 199 | `05494d47506a127f7826fb3db3f3319a9865fbcea5c59fd3c3f603653af1a1c2` |
| `round155-windowB/out/patched+minimal.dtb` | 108,676 | `647af49b8c21198d9cba99fac444131aaf95e86c99b28af87b610fc46b30cea2` |
| `round155-windowB/dbg/negative.dts` | 131 | `365160c7f48248244e4a430a56fc17fe1334497e966716008a174dfae51f23ac` |
| `round155-windowB/dbg/negative.dtbo` | 195 | `f24fe0aca868a943c9bba5092fb1921e481a16909052b7b1d9105ddf5f43f17a` |

`patched.dts.pp` 是 `patched.dts` 的已冻结预处理产物（含 `sm8250.dtsi` 与 dt-bindings 头展开）。本轮从它编译 DTB，从而**无需读取任何 Window A 源码树**。`dtc-patched.err` 中引用的 `round140-agent2/...sm8250.dtsi` 行号只是 pp 内 `#line` 保留的 warning 来源文本，非本轮读取路径。

### 3.2 工具版本

```
dtc         Version: DTC 1.7.0
cpp         cpp (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
gcc         gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
fdtoverlay  Version: 1.7.0-2build1 (device-tree-compiler)
```
完整日志：`evidence/build.log`、`evidence/negative.log`。A/B 编译时各有 32 行来自 `sm8250.dtsi` 的既有 warning（`avoid_unnecessary_addr_size`、`unique_unit_address`），与 RAM/UART 改动无关；overlay 编译 0 warning。

### 3.3 精确命令

```bash
# A — 无 overlay base（冻结 pp → DTB）
cp frozen-inputs/r154/out/patched.dts.pp scratch/A.dts.pp
dtc -I dts -O dtb -o scratch/A.dtb scratch/A.dts.pp
# → 108680 B / 9d0d7600...，cmp 冻结 patched.dtb = 逐字节相同

# B — scratch 内仅改 UART status（源 diff 见 §4）
cp scratch/A.dts.pp scratch/B.dts.pp
# 在 uart12: serial@a90000 节点内把 status = "disabled"; 改成 "okay";（唯一一处）
dtc -I dts -O dtb -o scratch/B.dtb scratch/B.dts.pp

# C overlay — 从 435 B 源编译
dtc -I dts -O dtb -@ -o scratch/C.dtbo frozen-inputs/r155/src/minimal-firstboot.dts
# → 199 B / 05494d47...，cmp 冻结 dtbo = 逐字节相同

# C — 应用到新 A base（fresh base，不是冻结产物）
fdtoverlay -i scratch/A.dtb -o scratch/C.dtb scratch/C.dtbo
# → 108676 B / 647af49b...，cmp 冻结 patched+minimal.dtb = 逐字节相同
```

---

## 4. 源 diff 与完整属性差异

变体 B 的唯一源改动（`A.dts.pp` → `B.dts.pp`，预处理器输出行 2079）：

```diff
@@ -2076,7 +2076,7 @@
       <&gem_noc 2 0 &config_noc 34 0>;
     interconnect-names = "qup-core",
            "qup-config";
-    status = "disabled";
+    status = "okay";
    };
```

编译后的**完整**节点/属性差异（自写解析器 `fdt156.py`，逐属性字节比较，共 905 节点）：

```
### FULL node/property diff A -> B : 1 entries
  /soc@0/geniqup@ac0000/serial@a90000  status  CHANGED  64697361626c656400 -> 6f6b617900
### FULL node/property diff A -> C : 1 entries
  /soc@0/geniqup@ac0000/serial@a90000  status  CHANGED  64697361626c656400 -> 6f6b617900
### FULL node/property diff B -> C : 0 entries
```

`64697361626c656400` = `"disabled\0"`，`6f6b617900` = `"okay\0"`。
即：**变体 B（DTS 直改）与变体 C（overlay apply）在编译后的设备树语义上完全等价**，二者只比 A 多同一个 UART status 属性；B 与 C 之间零差异。两者大小同为 108,676 B（字符串缩短 5 B，4 字节对齐后减少 4 B）。

---

## 5. 不变式核验

| 检查 | A | B | C | 证据 |
|---|---|---|---|---|
| 节点数 | 905 | 905 | 905 | `evidence/analysis.txt` |
| `device_type="memory"` 节点 | 1（`/memory@80000000`） | 1 | 1 | 同上 |
| 根 `#address-cells` / `#size-cells` | 2 / 2 | 2 / 2 | 2 / 2 | 同上 |
| `reg` cells | 12 cells，精确匹配 EXPECT | 同 | 同 | 同上 |
| `/reserved-memory` 子节点 | 18，三变体逐属性字节相同 | 同 | 同 | 同上 |
| `/memreserve/` entries | 0 | 0 | 0 | 同上 |
| phandle 数 / 碰撞 | 239 / 0 | 239 / 0 | 239 / 0 | 同上 |
| phandle 映射 A↔B / A↔C | 相同 | 相同 | 相同 | 同上 |
| `/chosen` 属性 / 子节点 | 0 / 0 | 0 / 0 | 0 / 0 | 同上 |

精确 RAM tuples（每个变体逐字一致）：

```
<0x0 0x80000000 0x0 0x39900000>,
<0x0 0xc0000000 0x0 0xc0000000>,
<0x2 0x00000000 0x2 0x00000000>
```

---

## 6. UFS host/PHY 依赖闭包（provider-cell-aware）

简单「把每个 u32 当 phandle」的扫描会误把 clock index（如 `0xa2`）读成 endpoint 节点引用。为避免假结论，用 `closure.py` 按每个 provider 节点自身的 `#clock-cells` / `#reset-cells` / `#interconnect-cells` / `#power-domain-cells` 步进，只断言 phandle **槽位**，specifier 值仅报告不作引用解释。A/B/C 三变体结果一致（完整清单见 `evidence/closure.txt`）：

### `/soc@0/ufshc@1d84000`（status=okay）

| 属性 | phandle 槽位 | 目标 | 结论 |
|---|---:|---|---|
| `clocks` | 8（`#clock-cells=1`） | GCC `clock-controller@100000` ×7、RPMh `rsc@18200000/clock-controller` ×1 | PASS，0 malformed |
| `interconnects` | 4（`#interconnect-cells=2`） | `interconnect@16e0000`、`@163d000`、`@9100000`、`@1500000` | PASS，0 malformed |
| `resets` | 1（`#reset-cells=1`） | GCC `clock-controller@100000`，spec `0x21` | PASS |
| `power-domains` | 2（`#power-domain-cells=1`） | `rsc@18200000/power-controller` spec `0x6`(MMCX)、GCC spec `0x4`(UFS_PHY_GDSC) | PASS |
| `operating-points-v2` | 1 | `ufshc@1d84000/opp-table`（含 37500000 / 300000000 两 OPP） | PASS |
| `vcc-supply` / `vccq-supply` / `vccq2-supply` | 各 1 | `ldo17` / `ldo6` / `smps4`（PM8150a，均带 `regulator-name`） | PASS |
| `qcom,vccq-parent-supply` | 1 | `regulators-1/smps8`（PM8150l） | PASS |
| `qcom,vddp-ref-clk-supply` | 1 | `regulators-0/ldo6` | PASS |

**节点闭包 PASS。**

### `/soc@0/phy@1d87000`（status=okay）

| 属性 | phandle 槽位 | 目标 | 结论 |
|---|---:|---|---|
| `clocks` | 3（`#clock-cells=1`） | RPMh clock-controller ×1、GCC ×2 | PASS |
| `resets` | 1 | UFS host 自身，spec 0 | PASS |
| `power-domains` | 1 | GCC，spec `0x4` | PASS |
| `vdda-phy-supply` / `vdda-pll-supply` | 各 1 | `ldo5` / `ldo9`（均带 `regulator-name`） | PASS |

**节点闭包 PASS。**

限定：本检查证明的是 DTB **静态引用闭合**（每个 phandle 槽位指向树内存在节点，supply 目标具备 regulator 身份），不证明这些 regulator 在真实启动中被 enable、电压正确或 S8 输入电源已物理存在——那是 bring-up gate，不是结构检查能给的结论。

---

## 7. 交叉测试

| 测试 | 命令要点 | 结果 |
|---|---|---|
| 正向：target-path overlay 应用到新 base | `fdtoverlay -i scratch/A.dtb -o scratch/C.dtb scratch/C.dtbo` | rc=0，输出 `647af49b…`，与冻结 `patched+minimal.dtb` 逐字节相同 — **PASS** |
| 负向：重建未知 target path overlay | `dtc -I dts -O dtb -@ -o negative.dtbo negative.dts`（`/soc@0/does-not-exist@deadbeef`） | 195 B / `f24fe0ac…`，与冻结 `negative.dtbo` 相同 |
| 负向：unknown path 应用到新 base | `fdtoverlay -i scratch/A.dtb -o negative-out.dtb negative.dtbo` | rc=1，`Failed to apply …: FDT_ERR_NOTFOUND`，**无输出文件** — **PASS** |
| 负向：冻结 negative.dtbo 直接应用 | 同上，输入用冻结副本 | rc=1，`FDT_ERR_NOTFOUND` — **PASS** |
| B/C 等价性 | 全属性 diff（§4） | B↔C 零差异 — **PASS** |
| `/chosen` 空 | 三变体节点检查 | 属性 0、子节点 0 — **PASS** |

---

## 8. `/chosen` 与 bootloader 注入字段清单

**三变体的 `/chosen` 均为空节点**（0 属性、0 子节点）。因此首启时所有 handoff 字段必须由 bootloader/内核注入。下表**只**引用已发布 live FDT 的实测字段与值（来源：`firmware-analysis/round151/..._REPORT.md` §3.4，第 130–166 行）；**不发明任何候选侧取值**，已脱敏项保留 `<REDACTED>`：

| 字段 | 类型 | live FDT 实测值（参考，不是候选注入值） |
|---|---|---|
| `bootargs` | `/chosen` 属性 | 1,507 B / 1,506 字符；现有 boot 的 sanitized 片段含 `earlycon=msm_geni_serial,0xa90000`、`androidboot.hardware=qcom`、`androidboot.console=ttyMSM0`、`nokaslr`、`console=NULL loglevel=0`、`buildvariant=user` |
| `linux,initrd-start` | `/chosen` 属性 | 8 B，`0x00000000f0000000` |
| `linux,initrd-end` | `/chosen` 属性 | 8 B，`0x00000000f015749a` |
| `kaslr-seed` | `/chosen` 属性 | 8 B，`<0x0 0x0>`（当前为零；候选不应假定该值） |
| `androidboot.dtbo_idx` | bootargs token | `2`（该次启动选中的是 Entry 2；**候选侧的取值仍未知**） |
| `androidboot.verifiedbootstate` | bootargs token | `orange` |
| `androidboot.keymaster` | bootargs token | `1` |
| `androidboot.bootdevice` | bootargs token | `1d84000.ufshc` |
| `androidboot.boot_devices` | bootargs token | `soc/1d84000.ufshc` |
| `androidboot.fstab_suffix` | bootargs token | `default` |
| `androidboot.swtype` | bootargs token | `normal` |
| `androidboot.selinux` | bootargs token | `enforce` |
| `androidboot.baseband` | bootargs token | `mdm` |
| `androidboot.product.hardware.sku` | bootargs token | `DBY-W09` |
| `androidboot.serialno` | bootargs token | `<REDACTED>` |
| `normal_reset_type` / `reboot_reason` | bootargs token | `NORMALBOOT` / `NORMALBOOT`（非 `androidboot.` 前缀，同属 bootargs 状态字段） |

live `/chosen` 的完整属性集**只有四项**（`bootargs`、`kaslr-seed`、`linux,initrd-start`、`linux,initrd-end`），无 `linux,uefi-*`、`linux,usable-memory-range` 或任何 EFI handoff 属性。任何候选侧为 `/chosen` 补值的动作都必须来自新的授权与实测，不能由本清单反推。

---

## 9. 变体对比与使用前提

| 若 ABL 的行为是… | 可用变体 | 理由 / 前提 |
|---|---|---|
| 允许不应用任何 overlay，直接加载 base DTB | **A**（无 UART 调试台）或 **B**（UART 已开） | B 与 C 语义完全等价；B 省去 overlay 应用环节，但两者都仍需 ABL 完成 `/chosen` 注入与 RAM fixup。A 无 rescue console |
| 要求存在并应用一个 DTBO/DTBO-like overlay | **C**（base + 199 B target-path overlay） | 已证明 host `fdtoverlay` 可用、负向路径正确报错；但**必须**先确认华为 ABL 支持 `target-path` 形式与 overlay 容器格式，否则 C 只是一条已验证的主机侧路径，不是可刷路径 |
| 需要 UART 但 ABL 完全忽略 overlay | **B** | 直接在 DTS 中开 UART；与 C 的运行时 DTB 结果逐属性相同 |

**ABL 问题清单（Window B 无法回答）**：
1. ABL 是否存在「不应用 overlay 直接启动 base」的路径；
2. 是否要求某种 DTBO 容器头/签名/索引，199 B 裸 overlay 是否被接受；
3. `target-path` patch 形式与 ABL 内部 ufdt 实现的兼容性；
4. board-id / msm-id 的匹配规则是否会拒绝当前 `qcom,board-id=<0 0>`；
5. `/chosen` 注入字段的实际来源与时序；
6. 三段 RAM 是否仍被 ABL 覆写、覆写顺序与 `ddr_device_type` 行为。
第 1–6 项属于 Window A 的 ABL 控制流证据范围；本轮不猜测、不越权。

---

## 10. 本轮踩坑与修正（供后续复用）

1. **自写 FDT 解析器把 tag 常量写反**：`FDT_END_NODE=2` 被误列为 `END`，导致结构遍历在 3 节点处提前 `break`，得出「0 phandle、0 diff」的假 PASS。修正为 `BEGIN, ENDNODE, PROP, NOP, END = 1,2,3,4,9`。
2. **strings block 边界用错**：初版取 `data[off_dt_strings:off_dt_struct]`（空区间），属性名解析报 `subsection not found`。改用 header 中的 `size_dt_strings@32`。
3. **显式空名根节点**：DTB 结构块含根节点自己的 `FDT_BEGIN_NODE("")`；若再合成一个 root，属性会落到多造的子节点、路径变成 `//memory@…`。修正为把空名根 BEGIN 并入合成 root。
4. **phandle 映射是 `value -> list[path]`**，初版当字符串用导致 `unhashable type: list`；已取 `[0]`。
5. **朴素 word-by-word phandle 扫描误报**：把 `clocks` 的 clock index（如 `0xa2`）当 phandle，显示为「指向 endpoint 节点」。`closure.py` 改为按 provider 的 `#*-cells` 步进，只断言槽位。

这些 bug 均在写报告前由脚本自身断言与对照冻结产物发现并修正；最终数字全部来自修正后的脚本，未手工填写。

---

## 11. 禁止项声明

- 无源码分支改动、无已接受补丁编辑、无完整 kernel/Image 构建。
- 无设备 / ADB / root / fastboot / recovery / 分区读写 / 刷机 / 重启 / 启动。
- 无 Window A 私有路径、原始二进制、日志或 ABL 工件的读取。
- 无 DTBO 容器、无 boot.img、无签名或无密钥提取。
- 所有产物仅在 scratch 目录；原冻结工件哈希在交付前复验一致。

---

## 12. 证据索引（本地，未上传二进制）

| 文件 | 内容 |
|---|---|
| `frozen-inputs/` | B 侧 R154/R155 源码、pp、dtb、dtbo 与日志的只读副本 |
| `evidence/build.log` | A/B/C 构建命令、版本、复现与 B 源 diff |
| `evidence/analysis.txt` | 三变体全属性 diff、RAM/reserved-memory、phandle、`/chosen`、朴素 UFS 扫描 |
| `evidence/closure.txt` | provider-cell-aware UFS 闭包逐槽位清单 |
| `evidence/negative.log` | 正向 apply、负向 `FDT_ERR_NOTFOUND`、冻结输入不变性 |
| `fdt156.py` / `analyze.py` / `closure.py` / `build.sh` / `negative.sh` | 本轮全部脚本 |

**验证结论**：A/B/C 在主机侧内部有效且互为受控变体；与华为 ABL 的兼容性、selector 行为和首启注入均不在 Window B 证据内。不标 flash-ready，等待 Window A 的 ABL 控制流报告后再决定是否进入打包阶段。
