# ROUND117 — 1号 AI：固定 ACK UFS/QMP 启动顺序与 L5/L9 临时 proxy vote handoff

审查日期：2026-11-25
任务归属：1号 AI（ChatGPT）独立固定源码审查；不是 Agent 任务，也不是 2号 AI patch 实现。
设备：Huawei MatePad 11 DBY-W09 / KONA / SM8250
固定 ACK：android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
关联：ROUND108、ROUND110、ROUND114、ROUND115、ROUND116、AI2-ROUND31

## 1. 本轮结论

ROUND114 将 QMP devm_regulator_bulk_get_const() 在 probe 时设置 init load 与后续实际 enable 区分开来，这是必要的；但结合 UFS 初始化完整调用图，可以把正常启动路径的时序继续收窄：

**在固定 ACK 的默认同步 platform-driver probe 路径上，UFS QMP PHY 的 L5/L9 regulator consumer enable 发生在 ufshcd_init() 返回、UFS async SCSI scan 被 schedule 之前。因此，只要 DBY-W09 UFS host probe 成功完成，L5/L9 QMP consumer votes 已在 late_initcall_sync 阶段前建立；不能因为 SCSI scan 尚在异步执行就认为 QMP rail vote 尚未接手。**

这是一条源码调用顺序结论，不是 runtime rail measurement，也不表示每次启动都成功完成 UFS probe。若启动命令行通过 driver_async_probe= 显式将这些驱动改为异步 probe，则需按实际 cmdline 重新评估。

## 2. UFS generic VCC/VCCQ 在 HBA 初始化期间同步启用

固定 ACK drivers/ufs/core/ufshcd.c：

1. ufshcd_pltfrm_init() 在 drivers/ufs/host/ufshcd-pltfrm.c 中解析 clock/regulator 信息，然后调用 ufshcd_init(hba, ...)。
2. ufshcd_init() 在 ufshcd_hba_init(hba) 中初始化 regulator：
   - ufshcd_init_hba_vreg() 获取 host controller regulator；
   - ufshcd_setup_hba_vreg(hba, true) 开启 host power；
   - 初始化 clocks；
   - ufshcd_init_vreg() 获取 UFS vcc、vccq、vccq2 handles；
   - ufshcd_setup_vreg(hba, true) 依次调用 ufshcd_toggle_vreg() / ufshcd_enable_vreg()，启用已声明的 UFS supplies；
   - 然后才调用 ufshcd_variant_hba_init(hba)。
3. ufshcd_enable_vreg() 在需要时先配置该 regulator 的 load，再调用 regulator_enable()；成功后记录该 vreg enabled。
4. ufshcd_hba_init() 成功返回后，ufshcd_init() 才调用 ufshcd_hba_enable(hba)。

因此，在 Stage A DTS 中 UFS vcc-supply 指向 PM8150 L17、vccq-supply 指向 L6 的正常成功路径上，generic UFS VCC/VCCQ enable 早于后续 HBA enable 与 SCSI async scan schedule。L17/L6 consumer 是否成功以及供电硬件是否真的达标，仍需 runtime probe/boot 验证。

源码：
- [ufshcd_hba_init regulator sequence](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c#L9770-L9850)
- [ufshcd enable/disable regulator helpers](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c#L9480-L9563)
- [platform regulator parse and ufshcd_init call](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufshcd-pltfrm.c#L644-L703)

## 3. QMP UFS PHY 的 L5/L9 consumer enable 在 ufshcd_hba_enable() 中同步发生

固定 ACK drivers/ufs/host/ufs-qcom.c：

- UFS variant ops 将 hce_enable_notify 指向 ufs_qcom_hce_enable_notify。
- ufshcd_hba_enable() 调用 ufshcd_hba_execute_hce()；HCE PRE_CHANGE 路径调用 ufshcd_vops_hce_enable_notify(hba, PRE_CHANGE)。
- ufs_qcom_hce_enable_notify(PRE_CHANGE) 调用 ufs_qcom_power_up_sequence(hba)。
- ufs_qcom_power_up_sequence() 在 PHY init / mode selection 后调用 phy_power_on(phy)。

固定 ACK drivers/phy/qualcomm/phy-qcom-qmp-ufs.c：
- qmp_ufs_power_on() 的第一步是 regulator_bulk_enable(cfg->num_vregs, qmp->vregs)；成功后才开启 PHY clocks 并执行后续上电。
- QMP provider probe 用 devm_regulator_bulk_get_const() 读取 vreg_list。这一步写入 consumer stored init load，但未等同于 enable。
- SM8250 UFS PHY 配置使用 sm8250_ufsphy_vreg_l：
  - vdda-phy init load = 89,900 µA；
  - vdda-pll init load = 18,800 µA。
- DBY-W09 Stage A DTS draft 已把 vdda-phy-supply 指向 L5、vdda-pll-supply 指向 L9；HOS4.3 overlay 也有对应 UFS PHY rail consumer 证据。

因此，成功的 HBA enable 路径会实际调用 QMP regulator_bulk_enable()，使 L5/L9 QMP consumer enable refs 生效。这个调用位于 ufshcd_init() 内部，且先于 UFS async SCSI scan schedule。

源码：
- [UFS Qualcomm HCE callback](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufs-qcom.c#L487-L620)
- [UFS Qualcomm variant ops / probe](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufs-qcom.c#L2765-L2835)
- [QMP UFS power-on](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/phy/qualcomm/phy-qcom-qmp-ufs.c#L1832-L1855)
- [QMP UFS regulator lists](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/phy/qualcomm/phy-qcom-qmp-ufs.c#L1204-L1212)
- [QMP UFS probe / bulk_get_const](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/phy/qualcomm/phy-qcom-qmp-ufs.c#L2104-L2140)

## 4. SCSI async scan 与 QMP rail handoff 的关系

ufshcd_init() 的执行顺序为：

1. ufshcd_hba_init()；
2. ufshcd_hba_enable()（包含 Qualcomm HCE PRE_CHANGE、QMP PHY phy_power_on()、QMP regulator bulk enable）；
3. UFS link startup、device init、SCSI host registration；
4. async_schedule(ufshcd_async_scan, hba)；
5. ufshcd_init() 返回。

ufshcd_async_scan() 随后才执行 ufshcd_probe_hba() 和 ufshcd_add_lus()。所以 ROUND108 的 async join 是 remove/lifetime 正确性所必需，但它不意味着 boot-time PMIC proxy handoff 必须等待 SCSI LUN scan 完成。对成功的 UFS initialization，QMP rails 在 async scan 开始之前已由同步 HBA enable 建立 consumer refs。

源码：
- [ufshcd_init and async scan scheduling](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c#L10952-L11204)
- [ufshcd_async_scan](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c#L9355-L9383)

## 5. 对 late_initcall_sync 的时间顺序

固定 ACK：
- module_platform_driver() 将这些 built-in platform drivers 注册为 module_init/device_initcall。
- UFS QCOM 与 QMP UFS PHY platform driver 没有设置 PROBE_PREFER_ASYNCHRONOUS；driver_allows_async_probing() 默认只有显式异步 probe 类型或 cmdline/module async 请求才选择 async。
- deferred_probe_initcall() 本身是 late_initcall；它打开 deferred probe、触发 deferred work，并 flush deferred probe work。
- late_initcall_sync() 宏对应 initcall level 7s，位于普通 late_initcall level 7 之后。

因此在默认同步 probe 行为、且没有 driver_async_probe= 显式覆盖时，RPMh regulator / QMP PHY / UFS host 的成功 probe 都会在 late_initcall_sync proxy cleanup 前完成；如 UFS 因 provider 顺序发生 -EPROBE_DEFER，late deferred-probe flush 有机会在 7s cleanup 之前再次完成同步 probe。只有实际成功完成的 UFS host init 才满足前述 QMP enable handoff；probe 失败或仍 deferred 时不能声称 QMP vote 已接手。

源码：
- [initcall sync ordering macros](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/linux/init.h#L299-L310)
- [deferred_probe_initcall](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/base/dd.c#L338-L376)
- [driver async probe default policy](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/base/dd.c#L929-L947)

## 6. 对 AI2-ROUND31 的影响

对 L5/L9 temporary proxy consumer：

- devm_regulator_bulk_get_const() 仅建立 QMP consumer handle 并存储 init load（89.9mA / 18.8mA），不证明这些 votes 已进入 ACK DRMS aggregate。
- 成功的 UFS HBA probe 随后执行 QMP regulator_bulk_enable()，才使这两个 consumer handles enabled，ACK DRMS aggregate 会计入对应 QMP loads。
- late_initcall_sync 清掉 L5/L9 各 100mA proxy vote时，在默认成功同步 probe 路径上，QMP consumer refs 已经存在；因此 ACK regulator_set_load(proxy, 0) 会在 QMP load 仍有效时重新计算 rail mode。
- L5 的 89.9mA、L9 的 18.8mA 是 QMP PHY 的配置 vote 值，不代表只有该负载；其他 consumer votes 仍必须保留在 aggregate 中。
- 该时间序列只说明正常成功 probe 路径上的 software vote handoff，不证明 PMIC 的电压/current、RPMh request 被物理执行或 UFS PHY 最终校准成功。

ROUND114 的“bulk-get 不等于 active vote”原则继续成立；ROUND117 只是证明本机 UFS QMP 的 enable 调用在正常启动调用图中早于 async SCSI scan 和 late-init proxy cleanup。

## 7. 范围与非声明

本轮只读检查固定 ACK UFS core、QCOM host、QMP UFS PHY、driver core 与 initcall 顺序，并对照项目已有 Stage A DTS draft。没有修改 AI2 分支、DTS draft、保护 DTS 分支、firmware、Image 或设备；没有编译/刷写/boot。没有证明实际 boot cmdline 未指定 async probe，也没有 runtime rail measurement。Phase E/F 仍 BLOCKED，Phase G NOT RUN。
