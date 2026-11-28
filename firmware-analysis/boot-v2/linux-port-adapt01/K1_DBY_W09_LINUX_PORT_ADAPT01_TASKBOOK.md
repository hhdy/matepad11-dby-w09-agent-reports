# K1-DBY-W09-LINUX-PORT-ADAPT01 — 按 svesnav/linux-dby-w09 适配 ACK 6.18.33 分区包

**签发：AI1（ChatGPT）**  
**执行：WorkBuddy Agent（本机离线）**  
**目标：Huawei MatePad 11 DBY-W09 / HWDBY / SM8250(Kona)**  
**性质：离线候选包制作与审计；禁止连接设备、写分区或重启。**

## 0. 用户指定基准

后续以同型号工程 https://github.com/svesnav/linux-dby-w09 为主要参考，不再把 HarmonyOS 4.2 与 4.3 的版本号差异作为阻碍，也不重复做版本比较。

本任务只复用该工程已经验证的 DBY-W09 boot-v2 / separate ramdisk / DTBO 分区布局、镜像打包、备份、SHA-256 读回验证设计。我们的目标仍是 Android ACK 17 / kernel 6.18.33，**不得把 Kubuntu Linux 7.0 的 kernel、DTB、cmdline、SD-root initramfs 或 userspace 搬入 Android 启动链。**

## 1. 参考仓库与冻结源码文件

主项目：svesnav/linux-dby-w09，branch main。参考快照：

- README 更新提交：116cb1fe06110543ce03217e8bd8f35c12ca89c3
- README blob：3f7a18eb8a9ec7cf2917521ba4d694202f5b1200
- dby-w09-rootparam.dtso：f7f3d5dfc370ecaafdd78cc04274d21735c9eeb1
- repack_boot.py：143c6f4c634a34cd2068ecd3c42cb471b8b832fb
- build_dev_images.sh：d1cbb590396f0cbb7bb229ece2fae8ebf12d2dd3
- pack_dtbo.py：210f27355cf034c7cbe8313e4ca66e73dd4d15bc
- install_images.py：38ba88276409c13d3da8291680071979fa19cc2e

安装器：svesnav/dby-w09-installer
- matepad.sh：9a1242ca7e8281df3c3e3c2877725eb153a55179
- app/src/main/assets/boot-linux.sh：c1a127aaf4d566602c5950ba5ce6c4feef4cc1d4

配套系统：svesnav/kubuntu-dby-w09
- boot-switch/boot-linux.sh：c1a127aaf4d566602c5950ba5ce6c4feef4cc1d4

Agent 先对照这些 blob SHA。远端 main 若变化，本轮仍按以上冻结内容；不要静默改用其它版本。

## 2. 参考项目的实际安装机制（重要）

README 和启动脚本表明：

1. ABL 接受 boot header v2 的 boot 分区镜像，并从独立 ramdisk 分区加载 ramdisk。
2. 该设备的 fastboot boot（RAM boot）被拒绝，项目转为分区镜像切换。
3. 项目 DTBO 必须包含 ABL 能接受的 /rootparam overlay；错误 overlay 会使平板返回 Fastboot。
4. 项目在 HarmonyOS 已取得 root 后，通过 /dev/block/by-name 等路径找到分区。
5. boot-linux.sh 先校验 SHA256SUMS，再以 dd 写入 boot、ramdisk、dtbo，逐分区读回指定长度并核验 SHA-256，最后 sync/reboot。
6. matepad.sh 先从设备读取并备份 stock boot、ramdisk、dtbo；该项目把用户的原厂分区镜像留作返回 HarmonyOS 的恢复输入。
7. install_images.py 是在已运行该 Linux 的环境写入；HarmonyOS 安装器的实际写入路径是 root helper + boot-linux.sh。

不要把项目的 Fastboot flash 原厂恢复示例误写为日常 Linux 启动路径。本轮只写离线打包和待审阅的写入/恢复计划，不能执行 dd、fastboot flash 或 reboot。

## 3. 我们自己的冻结输入

### ACK / PREP10
- ACK tag：android17-6.18.33_r00
- commit：8ad08f75ddf056e1ee600e1339e0463c5fcbdc9
- Kleaf target：//common:dby_w09
- source tree SHA-256：c56d93eafa35057d65176db6594d67d5144868a0
- Kernel Image：44,820,992 B，SHA-256 f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21
- kernel release：6.18.33-android17-5-maybe-dirty-4k
- PREP10 boot-v2：46,563,215 B，SHA-256 d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091
- embedded ramdisk：519,986 B，SHA-256 a4b94ff6bb2d9525fa6ad0010d8efa4c6fe2bd49d36956115c26a656b631af3c
- PREP10 DTB slot：1,216,399 B，SHA-256 7bb9a1fba8d4574bce9d54795d67217d6f72857e792cbafa626ece3459b996b7
- 实际构建 config：config-used-for-build.config，SHA-256 0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15

PREP10 原本为 fastboot boot 试验构建。本轮必须判断它是否需按项目 repack_boot.py 方式从本机 stock boot v2 重打包，不能直接假设 PREP10 就是合格分区候选。

### 本机原厂分区及板级身份
- stock live boot backup SHA-256：7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8；boot 分区大小 100,663,296 B（96 MiB）。
- stock package boot variant SHA-256：027f88fd6f318523925ca27a4d681d17a9bbca904b0c471ccc05e651d3da19b；不可替代 live backup。
- stock separate ramdisk：2,097,152 B，SHA-256 4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb。
- 当前机型板级 variant：DBY_W09_VD。
- 历史 live FDT：800,324 B，SHA-256 dc0ab259c800d52946d4a3d633fe1546430895d2878054d0376d428a135da52d。
- 历史 live FDT 记录 board id <0x08 0x02 0x00 0x06>、hardware_version SH1DBSLM。
- 本机 stock DTBO 备份的 SHA、size、分区长度尚未冻结；必须从已有 PC 备份定位并核验，禁止连接设备重读。

## 4. Android separate ramdisk 策略

本任务是 ACK Android 启动，不是启动 Kubuntu。因而：

- 不采用参考项目的 sd_root_init.sh、static busybox、LINUX70ROOT、Linux 7.0 initramfs 或 Linux modules。
- 保留当前本机 Huawei separate ramdisk 原件，其中含 init/init.real 与 KernelSU 路径。
- 当前原则：RAMDISK_ACTION=KEEP_STOCK_NO_WRITE；除非已有直接证据证明 Android ACK 必须修改 separate ramdisk，否则不生成新 ramdisk，不写该分区。
- 检查 PREP10 embedded ramdisk 与 stock boot v2 的关系，原则上保留冻结的 519,986 B embedded ramdisk。
- 如果发现 separate ramdisk handoff 或 header 处理存在矛盾，报告给 AI1，不自行替换 Linux initramfs。

## 5. 最大阻塞：VD 与项目 VG rootparam 不一致

参考项目的 dby-w09-rootparam.dtso 包含：

- root compatible：huawei,dby-w09 / qcom,sm8250
- root qcom,board-id：<0x206a 0>
- rootparam qcom,boardid：<0x08 0x02 0x09 0x08>
- rootparam qcom,board_name：DBY_W09_VG
- rootparam qcom,product_name：DBY-W09
- hardware_version：SH1DBSLM

但我们的历史 live FDT 对应 DBY_W09_VD、board id <0x08 0x02 0x00 0x06>、hardware_version SH1DBSLM。不能把项目 VG 字段直接复制到本机 VD 变体。

**禁止原样使用项目 VG DTBO 作为本机最终候选。**

必须从本机原厂 DTBO/历史 live FDT 取证：

1. 解析 stock DTBO table header、所有 entry 的 id/rev/custom、FDT overlay 内容。
2. 找到 ABL 对本机设备选取的 stock overlay entry。项目 README 提及 stock overlay 8，但不得仅凭序号假设本机也相同。
3. 从本机 stock entry 提取 /rootparam 全部属性，与历史 live FDT 逐字段比较。
4. 分清 root qcom,board-id <0x206a 0> 与 rootparam qcom,boardid 的不同语义，不能混为一谈。
5. 查明项目 VG 值是否只适用于该作者的板级批次，以及 ABL 是否会复制/规范化这些字段。必须有本机 stock DTBO 或同仓库构建证据。
6. 只有当 DTBO table 的 ABL 匹配字段与本机 stock 规则兼容，且 /rootparam 值与本机 VD 原厂 overlay 匹配，才可制作本机 dtbo.img。
7. 缺少 VD rootparam 依据时，DTBO_CANDIDATE=BLOCKED；不得用 VG 值暂时代替。

## 6. Stage A — 参考项目脚本复核

逐个分析冻结脚本：
- repack_boot.py：stock boot v2 unpack/repack、stock header 参数、embedded ramdisk、kernel/DTB/cmdline 替换、输出大小逻辑。
- build_dev_images.sh：生成 Linux initramfs、ramdisk 分区 payload、boot、DTBO 的完整序列；指出 Linux 专属部分。
- pack_dtbo.py：Android DT table header/entry 结构、table entry ID/custom/alignment。
- boot-linux.sh：HarmonyOS root 分区映射、SHA precheck、dd 写入、readback、reboot。
- matepad.sh：原厂分区备份位置、boot/ramdisk/dtbo 读取方式。
- install_images.py：备份、分区大小检查、写后 readback 的 Linux 侧方法。

标出哪些脚本只打包、哪些会写设备。禁止直接运行任何会碰设备的脚本。

## 7. Stage B — 按项目方式重打包 ACK boot v2

1. 必须使用 SHA 完全匹配的本机 stock live boot backup 作为基础；不可用 package variant 代替。
2. 复核原厂 boot v2 的 page size、base/offset、header fields、cmdline、OS version/patch、embedded ramdisk、DTB 与 boot ID。
3. 以冻结 ACK Image 作为 kernel payload；保留本机 stock embedded ramdisk；DTB 仅用 PREP10 已核验 DTB 或本任务证明与 VD 兼容的 DTB。禁止引入 Linux 7.0 DTB。
4. cmdline 对照 stock 与 PREP10，每个 token 标注保留/删除/新增理由；不得静默删除 Huawei bootargs，也不得直接搬用 Linux 项目 cmdline。
5. 检查 repack 后 kernel/ramdisk/DTB offsets、size、alignment、header version 和 AOSP boot ID；生成镜像必须能由独立 parser 再解析出相同 payload hashes。
6. boot 分区大小为 96 MiB。记录候选文件是否只写入分区前缀；若只写前缀，明确写入区间和未触及尾部，并核实 boot partition 是否有尾部 AVB/footer 或私有数据。
7. 不要套用项目 repack_boot.py 中该作者 stock boot 的硬编码 SHA 或 24,412,160 B payload 常量；本机文件不同，必须按本机真实 input 计算。ACK kernel 44,820,992 B 不得因参考作者 payload size 较小而截断。
8. 如 boot header/ramdisk/DTB 元数据不能可靠保留，BOOT_CANDIDATE=BLOCKED。

## 8. Stage C — 仅在 VD rootparam 通过后生成 DTBO

1. DTBO table 结构可参考项目 pack_dtbo.py（magic 0xD7B7AB1E，header 32 B，entry 32 B），但 entry 的 id/rev/custom、total_size、offset、alignment 均以本机 stock DTBO/ABL 规则为准。
2. 不得仅仅复制项目单 entry + 全零 entry 字段，除非已经证明本机 ABL 匹配规则允许。
3. overlay 只满足本机 ABL 的 /rootparam 需求；不要将 Linux 7.0 显示、触控、GPU、音频、USB、电源等 DTS 变化整包带入 Android ACK。
4. DTBO 候选应能通过 dtc 编译，再独立反编译/解析；逐字段证明 /rootparam 与本机 stock VD overlay 相符。
5. 记录所保留的 stock overlay entries、entry index、id/rev/custom、size/offset、alignment、table total_size。
6. 无法确认 VD overlay 时，DTBO_CANDIDATE=BLOCKED，不输出假装可刷入的 dtbo.img。

## 9. Stage D — 候选包与未来写入方案（不执行）

仅对通过 gate 的项目输出候选：
- boot.img：ACK kernel + 本机 stock boot v2 header/embedded ramdisk + 已验证 DTB/cmdline。
- dtbo.img：只有 VD rootparam 已准确匹配后才生成。
- ramdisk.stock-reference：保留原 separate ramdisk 的原件 hash/大小，仅作为参考，不写入。
- SHA256SUMS.txt
- partition_map.md
- packaging_repro.md
- apply_plan_NOT_EXECUTED.md
- restore_plan_NOT_EXECUTED.md

未来可审核的写入计划可仿照该项目：HarmonyOS root → 读取 /dev/block/by-name 映射 → 先备份完整 boot/ramdisk/dtbo → 核对目标分区长度 → 按文件 SHA 写入 → 逐分区读回对应长度并 SHA 验证 → 所有 readback PASS 后才考虑重启。该步骤只写成文档，不执行。ramdisk 当前计划保持 stock、不写。

任何 readback mismatch 的未来处置必须是立即停止，不继续下一分区、不自动 reboot。写入和恢复必须有单独授权；本任务不构成设备写入授权。

## 10. 输出字段

    PROJECT_REFERENCE_IDENTITY  = PASS | FAIL
    STOCK_BOOT_IDENTITY         = PASS | FAIL
    STOCK_RAMDISK_IDENTITY      = PASS | FAIL
    STOCK_DTBO_IDENTITY         = PASS | FAIL | UNKNOWN
    BOARD_VARIANT               = VD
    ROOTPARAM_MATCH             = CONFIRMED | MISMATCH | UNKNOWN
    BOOT_V2_REPACK              = PASS | BLOCKED
    ACK_KERNEL_PAYLOAD          = PASS | FAIL
    EMBEDDED_RAMDISK_POLICY     = KEEP_STOCK | OTHER_WITH_EVIDENCE
    SEPARATE_RAMDISK_ACTION     = KEEP_STOCK_NO_WRITE
    DTBO_CANDIDATE              = PASS | BLOCKED
    BOOT_CANDIDATE              = PASS | BLOCKED
    PARTITION_SIZE_CHECK        = PASS | FAIL | UNKNOWN
    IMAGE_PACKAGE               = READY_FOR_REVIEW | INCOMPLETE
    DEVICE_WRITE_PERFORMED      = NO
    DEVICE_REBOOT_PERFORMED     = NO
    FINAL_RESULT                = CANDIDATES_READY_FOR_AI1_REVIEW | BLOCKED_ON_VD_ROOTPARAM | BLOCKED_ON_BOOT_REPACK

交付 ZIP：K1_DBY_W09_LINUX_PORT_ADAPT01_REPORT.zip。包括中文总报告、复现脚本、最小必要解析摘录、通过 gate 的候选镜像、分区映射、未执行的写入/恢复计划、SHA256SUMS。

若某一候选未通过 gate，不得用旧 PREP10 或 VG DTBO 冒充最终候选；报告缺失的具体文件和证据。

## 11. 严格禁止

- 不连接平板，不执行 ADB/Fastboot 命令，不读取设备状态。
- 不执行 dd、fastboot flash、erase、format、update、reboot、set_active 或任何设备写入/重启。
- 不使用 EDL/9008、HiSuite、TWRP 或恢复流程。
- 不使用 Kubuntu Linux 7.0 initramfs、Image.gz、DTB、cmdline、modules 代替 Android ACK 组件。
- 不把项目 VG rootparam 直接复制到本机 VD。
- 不修改原始 stock boot、ramdisk、dtbo、FDT、ACK Image 或 PREP10；所有生成文件写入独立输出目录。
- 不访问 userdata、persist、oeminfo、TEE key、IMEI、MAC、校准数据。
- 不生成候选后自动刷写。全部文件交 AI1 审核，再等待用户对实际设备写入单独授权。

## 12. 完成后停止

本轮目标是完全基于 DBY-W09 Linux 项目的真实打包/分区切换设计，为当前 Android ACK 6.18.33 准备合适候选，并且先解决 VD rootparam 对齐问题。完成 ZIP 和报告后立即停止，交 AI1 审核。