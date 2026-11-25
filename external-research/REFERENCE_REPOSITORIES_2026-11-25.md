# DBY-W09 外部仓库研究记录（2026-11-25）

> 用途：把本轮用户提供的设备专用 UEFI、原厂内核和 GPU 参考仓库统一归档，供后续 ChatGPT 会话和本地 Agent 查阅。此文档只记录公开源码、仓库说明和作者自述；不代表已经在本项目设备上复现。
>
> **项目路线不变：先完成 Huawei MatePad 11 DBY-W09 的 ACK/GKI-derived Linux 6.18.33 内核移植与启动验证，再进行 Android 17 DerpFest 移植。** 不得把下列历史/异平台仓库当作 6.18.33 内核源代码，也不得因此提前转向 ROM 或 XNU/macOS。

## 结论总览

| 仓库 | 实际定位 | 对本项目的用途 | 能否直接移植到 ACK 6.18.33 |
|---|---|---|---|
| [WQSQW/uefi-dby_w09](https://github.com/WQSQW/uefi-dby_w09) | DBY-W09 专用 Mu-Silicium / EDK2 UEFI 平台配置 | 启动链、内存布局、PMIC/SPMI、实体按键、UEFI/ACPI 线索 | 不能直接移植；作为板级硬件证据交叉核对 |
| [zytstudio/DBY-W09-Kernel](https://github.com/zytstudio/DBY-W09-Kernel) | DBY-W09 HarmonyOS 4.x 的 Linux 4.19.157-perf 厂商内核构建工程 | 原厂运行配置、Huawei 旧驱动/补丁、启动镜像打包方式 | 不能；目标版本和架构路线不同，但属于最有价值的同设备 Android kernel 对照资料 |
| [bangbang0822/adreno740-a650](https://github.com/bangbang0822/adreno740-a650) | XNU/IOKit 的 Adreno 740 驱动代码，导入了 A650 fork 的部分 A6XX 路径 | A650 CP/Ring、APRIV、RPTR shadow、提交/缓存维护行为研究 | 不能；OS ABI、GMU 配置和 A740 专用代码都不匹配 Linux/SM8250 |
| TheBula97（此前用户提供的 EDL/固件类仓库） | 当前交接摘要仅保留为 Qualcomm EDL/固件辅助工具类别，原始精确 URL 和文件级分析未保留 | 可能用于匹配设备的救援/固件包检查；不是内核源码来源 | 未审计，不得据此使用 loader 或执行刷写 |

---

## 1. DBY-W09 专用 UEFI：WQSQW/uefi-dby_w09

仓库：[https://github.com/WQSQW/uefi-dby_w09](https://github.com/WQSQW/uefi-dby_w09)

### 已核对内容

- 仓库包含 `Platforms/Huawei/dby_w09Pkg`，其中有 `DeviceBuild.py`、`dby_w09.dsc`、`dby_w09.fdf` 和平台 Library 实现，说明它不是普通资料页，而是 DBY-W09 的 UEFI 平台适配代码。
- `Platforms/Huawei/dby_w09Pkg/Library/MemoryMapLib/MemoryMapLib.c` 描述 SM8250/Kona 的 UEFI 内存区域。源码注释称表来自 Renegade/edk2-msm 的 SM8250 设备实现，并声称其显示、UFS 已在 DBY-W09 真机跑通；这属于**源码作者的验证声明**，不是本项目独立复测。
- 文件中可重点留意的内存区域包括：
  - Display Reserved：`0x9C000000`，长度 `0x02400000`；
  - DXE Heap：`0xC0000000`，长度 `0x0E000000`；
  - UEFI FD：`0xCE000000`，长度 `0x02000000`；
  - RAM Partition：`0xD0000000` 起，长度 `0x130000000`。
- 同一文件记录了内存范围重叠问题：PSTORE 原先的长度会覆盖 HLOS 7 起始地址，UEFI MemoryInit 的校验会因此停住；仓库将 PSTORE 范围改为 `0x00400000`。这对理解 UEFI 阶段内存图、reserved memory 和 Linux 早期内存切分很有参考价值。
- `KeypadDeviceLib.c` 记录 PM8150 SPMI v5 的平台访问线索：
  - SPMI core：`0x0C440000`；
  - observer：`0x0E600000`；
  - cnfg：`0x0C40A000`；
  - 音量+：PM8150 GPIO6，状态寄存器 `0xC510`；
  - 电源键 KPDPWR：PON `0x810` 的 bit 0；
  - 音量- RESIN：PON `0x810` 的 bit 1。
- 该文件特别解释了 SPMI v5 observer 读事务、PPID→APID 反查、ownership 表和 observer channel 步长。不能把它误当成 v2/v3 arbiter 的访问方式。

### 对 6.18.33 移植的实际用途

1. 将 PM8150 SPMI 地址、GPIO/PON 位定义与 HOS4.3 DTB、ACK `drivers/spmi/spmi-pmic-arb.c`、`drivers/pinctrl/qcom/pinctrl-spmi-gpio.c`、`drivers/input/misc/qpnp-power-on.c` 对照。
2. 将显示保留区、PSTORE、HLOS、UEFI FD 和 RAM Partition 的物理范围与 HOS4.3 memory map、DTB reserved-memory、ACK `memblock`/reserved-memory 处理交叉核验。
3. 将 UEFI 设备树、ACPI 和平台窗口信息作为 boot chain 辅助证据；不能把 UEFI 资源表直接复制成 Linux DTS。
4. 需要确认具体设备是否确实使用某个 GPIO/PMIC 中断、寄存器窗口或 reserved-memory 区域时，以设备固件和 ACK binding/driver 共同验证。

### 明确限制

- 仓库是 UEFI/EDK2 平台项目，不是 Linux 内核移植。
- 根目录 `Status.md` 当前没有 DBY-W09 / dby_w09 条目，因此不能据此宣称该设备已列入项目正式支持设备清单。
- UEFI 内存图中的注释与地址是重要线索，但仍需与 HOS4.3 实机固件证据核对；特别是 RAM 总量、保留区边界和不同启动阶段的映射，不允许只凭注释推断。
- 仓库中的 Qualcomm UEFI 二进制驱动不是 Linux 驱动，不能直接拿来作为 ACK 模块或驱动源代码。

参考文件：
- [MemoryMapLib.c](https://github.com/WQSQW/uefi-dby_w09/blob/main/Platforms/Huawei/dby_w09Pkg/Library/MemoryMapLib/MemoryMapLib.c)
- [KeypadDeviceLib.c](https://github.com/WQSQW/uefi-dby_w09/blob/main/Platforms/Huawei/dby_w09Pkg/Library/KeypadDeviceLib/KeypadDeviceLib.c)
- [仓库 README](https://github.com/WQSQW/uefi-dby_w09/blob/main/README.md)
- [设备状态列表](https://github.com/WQSQW/uefi-dby_w09/blob/main/Status.md)

---

## 2. 同设备 HarmonyOS 4.x 厂商内核：zytstudio/DBY-W09-Kernel

仓库：[https://github.com/zytstudio/DBY-W09-Kernel](https://github.com/zytstudio/DBY-W09-Kernel)

### 定位与重要性

这是本批仓库中与 Android/Linux 设备内核最直接相关的一份，但它的目标是华为厂商 Linux `4.19.157-perf`，**不是 GKI，也不是 6.18.33**。项目说明它针对 MatePad 11 2021 / DBY-W09 / Snapdragon 865(Kona)，为 HarmonyOS 4.x 构建多个 boot 镜像变体。

仓库没有把完整内核树放在 GitHub。它要求从华为开源页面取得外部源码归档：

- 文件：`DBY-W09_HarmonyOS4.0.0_opensource.tar.gz`
- 声明大小：580,000,000 bytes（约 554 MiB）
- SHA-256：`52c38060cf2990e44bbc556f39271f6e97af90777a300165443946aa97c72e5f`
- 源码路径：`Code_Opensource/kernel`
- 版本：Linux `4.19.157-perf`（Huawei DBY-W09 / HarmonyOS 4.3.0.196）

未取得并校验该归档前，不得声称已检查其中的完整 Huawei drivers/DTS 源码。仓库中的 `configs/running.config`、脚本、补丁和说明文档则可直接作为公开参考。

### 应重点保留的资料

**A. `configs/running.config`：原厂运行配置基线**

README 将它说明为从设备 `/proc/config.gz` 取得的配置。它是配置参考，不是目标配置模板。可对照的硬件/驱动族包括：

- `CONFIG_ARCH_KONA=y`
- UFS：`CONFIG_HUAWEI_QCOM_UFS`、`CONFIG_SCSI_UFSHCD`、`CONFIG_SCSI_UFS_QCOM`、`CONFIG_PHY_QCOM_UFS`
- PMIC/SPMI：`CONFIG_SPMI`、`CONFIG_SPMI_MSM_PMIC_ARB`、`CONFIG_PINCTRL_KONA`、`CONFIG_PINCTRL_QCOM_SPMI_PMIC`
- RPMh：`CONFIG_QCOM_RPMH`、`CONFIG_REGULATOR_RPMH`、`CONFIG_QCOM_CLK_RPMH`
- GPU：`CONFIG_QCOM_KGSL`、`CONFIG_QCOM_KGSL_IOMMU`
- Wi-Fi：`CONFIG_CNSS_QCA6390`、`CONFIG_QCA_CLD_WLAN`
- USB/Type-C：`CONFIG_USB_DWC3_QCOM`、`CONFIG_TYPEC` 及 Huawei USB 相关选项
- 触控配置含 Synaptics DSX/TCM、FTS、ST 等多个驱动族；仅仅编进配置不等于设备实际触控芯片已确认。
- 显示相关配置中有 `CONFIG_DRM_MIPI_DSI`、`CONFIG_MSM_EXT_DISPLAY`，但 `CONFIG_DRM_MSM` 未启用；不能将 Huawei 4.19 vendor display stack 简单视为上游 DRM/MSM 已经可用。

将这些旧内核配置映射到 ACK 6.18.33 时，必须逐一检查当前 Kconfig 符号、依赖、驱动实现和 DTS compatible；禁止把整份 4.19 配置直接复制进 6.18。

**B. `scripts/configure.sh`：厂商内核配置约束**

构建脚本从 `running.config` 开始，并关闭 `RELOCATABLE` 和 `RANDOMIZE_BASE`。作者注释给出的原因是 Huawei RTIC section 不能重定位，内核必须运行在链接地址。该限制属于 4.19 Huawei vendor 内核的实现约束，不能直接移植到 ACK 6.18.33；需要在 6.18 目标源码中重新验证是否存在相同结构/约束。

**C. `scripts/patch_source.py` 和 `scripts/patch_msm_fault.py`：老内核故障线索**

仓库补丁涉及旧版 Huawei 内核编译环境、外部模块构建和显示 GEM/dma-buf fault 路径。尤其 `patch_msm_fault.py` 针对 `msm_gem_fault` 中 dma-buf 页数组缺失导致的潜在空指针访问，尝试从 sg table 建立 page array，并在不可用时返回 SIGBUS。

这可以用来检索类似症状和理解旧 vendor 代码修改原因；只有当 ACK 6.18.33 的对应函数、数据结构和调用路径确实存在同样问题时，才考虑重新设计修复。不得原样套用 4.19 patch。

**D. `scripts/pack_boot.py`：旧设备 boot 封装参考**

脚本明确处理 Android boot header v2、4 KiB page size，保留原 ramdisk、DTB、cmdline、os_version 和 image id，只替换压缩内核 payload；当新 payload 超过原 payload 结束位置时，移动 AVB footer 中的 vbmeta 并重写 footer。README/manifest 记录的设备 boot 分区为 96 MiB、slotless。

对本项目有用的是理解 DBY-W09 旧 ABL/boot image 封装与独立 ramdisk 布局。它不是 GKI boot.img/v4 或现代 vendor_boot 设备的通用打包器；6.18.33 产物封装必须按本项目真实分区、ABL、DTB/DTBO 和 AVB 证据单独验证。

### 作者声称的验证边界

项目 Release/提交说明中包含 HarmonyOS 4.x（包含 HOS4.3）测试声明和多种 boot 镜像变体。相关运行结果应归类为仓库作者自述；除非本项目另有设备日志/可复现步骤，不得当成本项目独立完成的内核启动验证。

参考文件：
- [README.md](https://github.com/zytstudio/DBY-W09-Kernel/blob/master/README.md)
- [SOURCE-MANIFEST.md](https://github.com/zytstudio/DBY-W09-Kernel/blob/master/SOURCE-MANIFEST.md)
- [running.config](https://github.com/zytstudio/DBY-W09-Kernel/blob/master/configs/running.config)
- [configure.sh](https://github.com/zytstudio/DBY-W09-Kernel/blob/master/scripts/configure.sh)
- [pack_boot.py](https://github.com/zytstudio/DBY-W09-Kernel/blob/master/scripts/pack_boot.py)

### 后续可执行的源码对照任务

1. 取得官方 554 MB Huawei 源码归档后，先核对 SHA-256 与上述 manifest 一致，再抽取设备相关 DTS/DTSI 和 UFS、SPMI/PMIC、pinctrl、RPMh、KGSL、display、CNSS/Wi-Fi、USB/Type-C 源码。
2. 以 ACK `android17-6.18.33_r00` 为目标，对照上面各驱动族，区分“上游已有实现”“Huawei 私有扩展”“DTS 数据差异”“必须新增的板级 glue”。
3. 把 4.19 配置映射做成 6.18 符号对照表，记录旧符号、新符号、依赖、目标状态和证据来源；配置选项不能代替实际设备识别。
4. 只将经过 ACK 源码核实的差异转化为补丁或 DTS 工作，不要把旧内核当作移植底座。

---

## 3. Adreno 650/A740 XNU 参考：bangbang0822/adreno740-a650

仓库：[https://github.com/bangbang0822/adreno740-a650](https://github.com/bangbang0822/adreno740-a650)

### 必须准确理解它是什么

README 将其描述为运行于 SM8550 的 Adreno 740 kernel GPU driver，硬件命令和 scanout copy 在名为 sheng 的平台上得到验证。仓库的 `Info.plist` 将组件类型标为 `KEXT`，使用 IOKit personalities；因此这是 XNU/IOKit 代码，不是 Linux DRM/MSM 驱动。

但它也不是“完全与 A650 无关”。其导入提交 `5c738e659ef7754bfb02ff1e0080211d2f62f668` 的说明为：

> A650 fork content (FFT-infra/Adreno650 70771a7) with the A650 paths the DBY-W09 build needs

已抽样比对多个源文件 SHA，当前仓库与 `FFT-infra/Adreno650` 的 `70771a7` 导入提交在这些文件上完全相同。代码中保留了一些 A6XX generation 6 路径，但整体设备匹配、A740 硬件初始化表和 GMU 配置并没有因此自动变成完整 SM8250/A650 适配。

### 对 A650 最有价值的技术记录

**A. 硬件 APRIV 与 CP Ring RPTR shadow**

来源提交 `FFT-infra/Adreno650@70771a71795d7e1a78afdb82badd7943adb0a3a0` 记录：

- A650 芯片 ID：`0x06050002`（这是该提交作者引用的 A650 芯片识别值；DBY-W09 的实际读数仍须从本机 HOS4.3/DTB/GPU 日志确认）。
- A650 被描述为有 `ADRENO_QUIRK_HAS_HW_APRIV`。
- 在该硬件特性下，Linux 主线 `a6xx_hw_init()` 会按 `hw_apriv` 状态选择 CP Ring 控制寄存器值；若错误设置 `CP_RB_CNTL.NO_UPDATE`（bit 27），CP 可能停止更新内存 RPTR shadow。
- 对应代码的 Ring 路径改为读取 shadow；错误状态会造成读指针停住、Ring 被认为已满、后续 submit 返回 Busy。

作者在该提交中报告的板上数据：

| 指标 | 修复前 | 修复后 |
|---|---:|---:|
| Submit failures | 2480 | 0 |
| WPTR writes | 6 | 636 |
| self-test rounds | 4 | 4 |

上述数字是作者提交信息中的自述结果，不是本项目设备复测，不得当作 DBY-W09 已验证结论。

**B. A6XX 与 A7XX 的 CP/Ring 路径有实质差异**

仓库源码区分 generation 6 与 generation 7：
- A6XX CP 初始化走 `a6xx_cp_init()` 的八字 `CP_ME_INIT` 路径，不发送 A7XX 的 `CP_THREAD_CONTROL` 和 A740 power-up register list。
- A6XX Ring 使用对应的 cache flush/fence、context/page-table prologue 和 CCU invalidate 行为。
- A6XX 与 A7XX 的提交封包不能混用；不能因为两代都使用 Adreno PM4 就假定所有 packet sequence 相同。

重点代码：
- `NativeAdrenoRing.cpp`
- `NativeAdrenoRing.h`
- `NativeAdrenoCpInit.cpp`
- `NativeAdrenoCpInit.h`

**C. 当前主分支仍残留 A740/SM8550 专属内容**

- `NativeAdrenoA740HwInit.h` 的寄存器/HWCG/CP protect 表明确命名为 A740。
- `NativeAdrenoPwrup.cpp` 使用 `buildA740()` 和 A740 power-up register list。
- `NativeAdrenoService.cpp` 的 GMU 启动使用 `SHENG_GMU_*` 固件、命令数据库、投票与配置参数。
- `Info.plist` 的 IOKit personality 仍名为 `sheng SM8550 Adreno`。
- GMU 固件默认弱符号为零长度；没有正确平台固件和规则，代码会拒绝启动 GMU。

因此，当前仓库只能作为 A6XX 公共命令处理行为、内存/缓存同步思路及特定 A650 调试线索的旁证；不能直接拿来替代 Linux `drivers/gpu/drm/msm`、Linux `a6xx_gmu.c` 或 DBY-W09 DTS。

### 对本项目后续工作

1. 先确认 DBY-W09 实际 GPU 芯片 ID、GPU revision、GMU 型号/固件和硬件 APRIV 特性；不可只因 SoC 是 SM8250 就把别的平台记录直接认作本机事实。
2. 在 ACK `android17-6.18.33_r00` 中核对 `drivers/gpu/drm/msm/adreno/a6xx_gpu.c`、`a6xx_gmu.c`、`a6xx.xml`、`a6xx_catalog.c` 和 PM4 定义。
3. 重点比较 `hw_apriv` / `ADRENO_QUIRK_HAS_HW_APRIV`、`CP_RB_CNTL_NO_UPDATE`、`CP_RB_RPTR_ADDR`、`a6xx_get_rptr()`、`a6xx_cp_init()`、`a6xx_set_pagetable()` 和 `a6xx_submit()` 的实际 ACK 6.18.33 实现。
4. 只将经 ACK 源码与 DBY-W09 硬件证据双重确认的差异用于移植；不复制 XNU KEXT、IOKit ABI、A740 硬件表或 sheng GMU 启动逻辑。

参考文件：
- [当前仓库 README](https://github.com/bangbang0822/adreno740-a650/blob/main/README.md)
- [Info.plist](https://github.com/bangbang0822/adreno740-a650/blob/main/Info.plist)
- [Ring implementation](https://github.com/bangbang0822/adreno740-a650/blob/main/NativeAdrenoRing.cpp)
- [CP initialization](https://github.com/bangbang0822/adreno740-a650/blob/main/NativeAdrenoCpInit.cpp)
- [A740 hardware initialization table](https://github.com/bangbang0822/adreno740-a650/blob/main/NativeAdrenoA740HwInit.h)
- [导入 A650 fork 的提交](https://github.com/bangbang0822/adreno740-a650/commit/5c738e659ef7754bfb02ff1e0080211d2f62f668)
- [原始 A650 路径提交](https://github.com/FFT-infra/Adreno650/commit/70771a71795d7e1a78afdb82badd7943adb0a3a0)

---

## 4. TheBula97 EDL/固件类仓库：待补全精确链接

此前交接信息仅保留了“用户提供过 TheBula97 的 Qualcomm 固件/EDL 辅助仓库”这一分类，没有保留可核验的完整仓库 URL、仓库名和文件路径。因此这里不编造仓库身份或内容，也不把它记作已完成源码审计。

可供后续审查的判断标准：
- 若包含 DBY-W09 / SM8250 对应的 Firehose programmer、Sahara loader、`rawprogram*.xml`、`patch*.xml`、分区 XML 或完整工厂包，可能帮助固件恢复、分区布局和镜像来源核验。
- 通用 Qualcomm EDL 工具不是设备专属 loader，也不是 Linux 内核源代码。
- loader、firehose programmer、分区 XML 和 firmware 必须匹配 SoC、板级目标、存储类型、签名策略与固件版本。不能将其他 SM8250 设备的 loader/XML 直接用于 DBY-W09。
- 本项目目前的移植主线不要求进入 EDL 或刷写。任何可能写入设备的操作都必须另行审核、明确授权，并先具备完整备份和可恢复方案。

---

## 5. 后续会话的固定使用规则

1. 新会话先阅读根目录 `PROJECT_HANDOFF.md`、`AGENT_TASK.md`，再阅读本文件和对应 ROUND 报告。
2. 上述仓库只作为按问题调用的参考资料，不要每轮重新搜索并重复确认已有结论。
3. 所有代码/硬件结论按证据等级标注：
   - **仓库可见事实**：当前可直接从源码、配置或清单核对；
   - **作者自述**：提交说明、README 中声称的实机测试；
   - **本项目已验证**：必须有 DBY-W09 本机日志、已审核固件证据或 ACK 精确源码对照；
   - **待验证**：不能作为补丁设计的既定事实。
4. UEFI 表、4.19 vendor kernel、XNU KEXT 均不可作为 6.18.33 移植底座。当前目标内核始终是 ACK `android17-6.18.33_r00`。
5. 不能因为发现某个仓库有“成功启动”“有 GPU 代码”或“有 UFS 代码”，就跳过本项目设备树、固件和驱动链条的独立核验。
6. 本文件更新时应补充来源 URL、commit/ref、关键文件路径、可复核的证据，以及明确的不可移植边界；不要只写模糊的“有参考价值”。
