# AI2 独立研究任务书
# K1-DBY-W09-DIRECT-ABL-PARTITION-ADAPT02
## 基于 svesnav/linux-dby-w09 的第二种启动方式：Huawei ABL 直接启动 + 分区更新，适配 ACK Android 17

- 发起：AI1
- 执行：2号 AI（独立研究；不要与 AI1 的 CoWave U-Boot 研究混线）
- 设备：Huawei MatePad 11 2021 DBY-W09 / HWDBY / SM8250(Kona)
- 本机板级：DBY_W09_VD
- 目标：ACK android17-6.18.33_r00 / Linux 6.18.33，后续 DerpFest Android 17
- 研究路线：**第二种路线——svesnav 的 direct ABL partition boot**。Huawei ABL 直接读取 boot v2、独立 ramdisk 与 DTBO，不经过 CoWave 的 recovery-U-Boot chainloader。
- 性质：只读源码与现有离线证据研究。不连接设备、不运行设备命令、不写分区、不制作候选镜像。

---

## 0. 唯一研究问题

公开项目 https://github.com/svesnav/linux-dby-w09 已在 DBY-W09 上采用 Huawei ABL 直接启动 Linux 的方式。项目说明 ABL 拒绝 fastboot boot，因此开发迭代使用分区镜像更新。

请独立回答：

**能否将 svesnav 的 direct ABL partition boot 方法适配到我们的 ACK 6.18.33 + Huawei Android first-stage init？如果可以，boot、ramdisk、DTBO 哪些分区需要改变？ACK Image 的加载对齐问题如何解决？**

不能只复述 README。必须基于脚本、内核头部、ABL 加载分支、ramdisk 格式、DTBO 匹配、AVB footer、分区容量和回滚证据给出结论。

最终字段：
- DIRECT_ABL_ACK_ANDROID = FEASIBLE / FEASIBLE_WITH_IMAGE_ADAPTATION / BLOCKED / UNKNOWN
- RECOMMENDED_NEXT_STEP = 一个具体的最小行动

AI1 正在独立分析 CoWave U-Boot chainloader。AI2 只负责本任务指定的 svesnav 直接 ABL 分区启动路线。

---

## 1. 本机冻结事实

### 设备与分区
- Board name：DBY_W09_VD
- Live FDT root qcom,board-id：<0x200e 0>
- rootparam qcom,boardid：<0x08 0x02 0x00 0x06>
- rootparam qcom,board_name：DBY_W09_VD
- HarmonyOS：4.3.0.196(C00E100)，Android 12
- 分区 A-only，无 _a/_b 后缀
- boot：96 MiB = 100,663,296 B
- separate ramdisk：2 MiB = 2,097,152 B
- 本机 stock live boot SHA-256：7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8
- 本机 stock separate ramdisk SHA-256：4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb

### ACK 与当前候选
- ACK source ref：android17-6.18.33_r00
- ACK source commit：8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- Patched source tree SHA：c56d93eafa35057d65176db6594d67d5144868a0
- ACK Image SHA-256：f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21
- ACK raw Image：44,820,992 B
- ACK Image header：text_offset=0；image_size=45,547,520；flags=0xA；magic=0x644D5241
- PREP10 boot 候选 SHA-256：d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091
- PREP10 boot 大小：46,563,215 B
- Hybrid ABL PE SHA-256：a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404

### ramdisk 已有分析
- boot embedded ramdisk 约 519,986 B，主要含 fstab.qcom + e2fsck，没有 init/adbd。
- separate ramdisk partition 2 MiB，含 Huawei init / init.real 和 KernelSU 文件。
- separate ramdisk 中 gzip CPIO payload 约 1,406,106 B；wrapper、header、AVB footer 的完整边界仍需按本机证据重核。
- Android 路线原则上应保留 Huawei 原厂 separate ramdisk，除非有直接证据证明 ACK Android first-stage init 必须作特定重打包。

若 AI2 无法直接访问本机原始备份，必须引用已有任务报告并标记“引用已有证据，未重新读取原始分区”；不得虚构复核结果。

---

## 2. svesnav 参考仓库与冻结文件

主仓库：https://github.com/svesnav/linux-dby-w09
已知 main 最近提交：116cb1fe06110543ce03217e8bd8f35c12ca89c3

以下 Git blob SHA 是 AI1 本轮实际回读值，AI2 必须重新 fetch 核对：

| 文件 | Blob SHA | 用途 |
|---|---|---|
| README.md | 3f7a18eb8a9ec7cf2917521ba4d694202f5b1200 | ABL boot flow、分区与恢复策略 |
| repack_boot.py | 143c6f4c634a34cd2068ecd3c42cb471b8b832fb | stock boot v2 重打包 |
| build_dev_images.sh | d1cbb590396f0cbb7bb229ece2fae8ebf12d2dd3 | 制作 boot/ramdisk/dtbo |
| configure-and-build.sh | 0c76aee9e5871b88d768e86f9f4ba67be45fdf09 | Linux 7.0 Image.gz/DTB/DTBO 构建 |
| install_images.py | 38ba88276409c13d3da8291680071979fa19cc2e | Linux 运行态备份、写入、读回 |
| deb/matepad-kernel-install | 8e494a0039ed54955fdde7452ba206ddd98d741a | 三分区构建及安装逻辑 |
| boot-cmdline.txt | b2b60b073d0e4305bebff32939eef1868ce3ea0c | Linux cmdline |
| pack_dtbo.py | 210f27355cf034c7cbe8313e4ca66e73dd4d15bc | 单 overlay DTBO 打包 |
| dby-w09-rootparam.dtso | f7f3d5dfc370ecaafdd78cc04274d21735c9eeb1 | VG rootparam overlay |
| build_release.sh | 1d85c6d7ad9e03bf814e955cb887f61fee803258 | 发布包生成 |
| sd_root_init.sh | a3d85fc0ccd89c9436edef8b530a1177ff0128ca | Linux SD-root initramfs |
| KERNEL_VERSION | e3d1dc406ae0bfe65d7315c69d4daaf1c60d5cdb | v7.0.14 |

svesnav 的目标是 Linux 7.0.14 + microSD ext4 root，不是 ACK Android。它的 sd_root_init.sh、busybox initramfs 不得直接作为本机 Android ramdisk。

---

## 3. 阶段 A — 还原实际 direct ABL 启动与更新流程

按代码还原：
1. ABL 正常 boot v2 启动时读取哪些 boot components。
2. separate ramdisk 分区在启动链中的读取和解析方式。
3. ABL 对 DTBO 与 /rootparam 的要求。
4. fastboot boot 被拒绝的证据来源及其适用范围；不要泛化成所有华为机型。
5. 首次安装和后续更新分别由何种程序完成：HarmonyOS installer app、运行于 microSD Linux 的 install_images.py、matepad-kernel-install。
6. boot、ramdisk、dtbo 三个分区分别为什么被写入。
7. 区分只构造镜像与真正写入设备的步骤。

交付：启动流程图、安装流程图、分区作用矩阵，引用到函数/行号。

---

## 4. 阶段 B — boot v2 重打包与 Image.gz 对齐（关键阶段）

### 4.1 分析 svesnav repack 实现

逐行核对 repack_boot.py 和 matepad-kernel-install 的 boot_with()：
- 从原厂 boot 读取哪些 header v2 字段；
- kernel、DTB、cmdline 替换逻辑；
- embedded ramdisk、second、recovery_dtbo 是否保留；
- header SHA-1 的组成方式和长度字段；
- page padding 和 image 组装顺序；
- 产生的镜像长度是否小于本机 boot 分区；
- 项目 STOCK_PAYLOAD_SIZE=24,412,160 的真实含义；
- --full-partition 的字节处理：哪些范围复制、覆盖、清零，尾部 AVB/footer 如何处理；
- 安装器实际写入的是完整分区还是仅镜像 payload 长度；
- 脚本中的 stock boot SHA 固定值如何校验。

svesnav 固定 stock SHA：
6fb82f6ca823c8acffaece13b161eca6c685a6e26f2c216b50293c3fd5da539d

本机 live stock boot SHA：
7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8

两者不同，禁止直接套用 svesnav 的 hash guard 或脚本默认输入。

### 4.2 Image.gz 是否解决 ABL 加载对齐

必须从源码、压缩 payload 和 Hybrid ABL 证据解释：
- svesnav 构建输出的 Image.gz 解压后 ARM64 Image 的 text_offset、image_size、flags、magic。
- svesnav Linux 配置的 CONFIG_RELOCATABLE、CONFIG_RANDOMIZE_BASE、page size 等。
- ABL 对 raw ARM64 magic 与 gzip payload 选择何种处理分支。
- gzip 解压后的最终 Kernel 物理地址/偏移。
- Image.gz 只是压缩容器，不得声称“更小所以对齐问题消失”。
- 给出 Hybrid ABL 指令级证据；不能闭环时写 UNKNOWN/PARTIAL。
- svesnav 已经成功启动的内核如何满足本机 ABL 对齐要求？它的成功能否证明本机同一分配路径/地址余数，必须严格论证。

### 4.3 PREP10/ACK 三种形态对比

只分析，不生成：

A. 当前 PREP10 raw Image；
B. 同一 ACK Image gzip 压缩后作为 boot kernel payload，但不改解压后 Image header；
C. 通过 ACK 源码/构建配置生成符合 ABL 加载契约的 Image（只提出源码改法，不改代码/编译）。

统一公式：

(ImageBuffer_phys + ABL_kernel_offset - text_offset) mod 0x200000 = 0

分别列出：
- ABL 实际选择路径和指令地址；
- ABL kernel offset；
- Image text_offset；
- 所需 ImageBuffer 物理地址余数；
- 当前 allocator 物理地址余数是否已知；
- alignment PASS/FAIL/UNKNOWN。

如果 allocator 地址余数未知，必须保留 UNKNOWN，不要以 svesnav 启动成功循环论证 ACK 也一定满足。

---

## 5. 阶段 C — Android separate ramdisk / bootconfig 适配

svesnav Linux 方案会把自制 microSD initramfs 包装为 header v0 ramdisk payload，覆盖原厂 2 MiB separate ramdisk 的前部并保留 AVB footer。但这不是 Android initramfs。

必须核实：
1. build_dev_images.sh 如何制作 busybox + sd_root_init.sh + reboot-bootloader gzip CPIO，再封装为 header v0。
2. 原厂 separate ramdisk 的 header version、payload offset、gzip/CPIO 类型、AVB footer 位置及 metadata。
3. 原厂 separate ramdisk 内 Huawei init、init.real、KernelSU 的作用；Android first-stage init 是否必须保持。
4. ABL 加载 separate ramdisk 的实际方式，引用 PREP04/ABL 分析证据。
5. ACK 6.18.33 first-stage init 需要的 bootconfig/cmdline/fstab 接口。
6. Android init、fstab.qcom、first-stage mount、dynamic partitions、vbmeta/dm-verity 对内核的前置需求。
7. 判断本机 Android 直启应 KEEP_STOCK ramdisk、REPACK_REQUIRED 还是 UNKNOWN。
8. 最终判断是否真的需要写 separate ramdisk，不能为了复制 svesnav 三分区脚本而机械覆盖。

输出：
ANDROID_RAMDISK_POLICY = KEEP_STOCK / REPACK_REQUIRED / UNKNOWN

---

## 6. 阶段 D — VD 与 VG 的 DTBO 差异

svesnav dby-w09-rootparam.dtso 是 VG：
- qcom,board-id=<0x206a 0>
- qcom,boardid=<0x08 0x02 0x09 0x08>
- qcom,board_name="DBY_W09_VG"

本机是 VD：
- live FDT root qcom,board-id=<0x200e 0>
- stock DTBO Entry 2 rootparam qcom,boardid=<0x08 0x02 0x00 0x06>
- qcom,board_name="DBY_W09_VD"
- qcom,product_name="DBY-W09"

必须：
1. 复核 stock DTBO Entry 2 的 FDT 内容和 table metadata，无法直接访问时引用已有 VD overlay 核验报告。
2. 查明 ABL 真正的 DTBO overlay 选择来源，不能未经证明把 androidboot.dtbo_idx=2 解释为选择命令。
3. 说明保留 stock DTBO 时 cmdline 是否应保留 androidboot.dtbo_idx=2。
4. 评估 svesnav 单 Entry pack_dtbo.py 是否适配 ABL metadata 匹配；不生成 overlay。
5. 严禁建议把 VG overlay 写入 VD 设备。

输出：
DTBO_POLICY = KEEP_STOCK_VD_ENTRY2 / NEW_VD_OVERLAY_REQUIRED / UNKNOWN

---

## 7. 阶段 E — 分区容量、AVB、备份、写入及恢复机制

本机已有：
- boot 96 MiB
- separate ramdisk 2 MiB
- stock separate ramdisk 末尾有 AVB footer；footer 的准确原始边界应引用 CLOSE01/PREP 证据。
- DTBO 分区大小以本机 partition inventory 为准，不得猜测。
- A-only，没有 _a/_b。

分析 svesnav：
- install_images.py 只允许 boot/ramdisk/dtbo；是否每个任务写前全分区备份、校验镜像 SHA、容量、fsync 和读回 SHA。
- matepad-kernel-install --check 与实际写入代码路径区别。
- unsafe_reason() 的机型、chroot/container、microSD root 检查。
- ramdisk_with() 如何保留 AVB footer。
- 失败是否自动回滚？还是只提示备份路径？
- 备份读取全分区还是仅写入长度；读回校验全分区还是仅写入 payload；说明局限。
- 对本机 Android 能否采用同样的 write-verify-backup 原则，写方案即可，不编写或执行写入脚本。

复核本机恢复备份：
- boot backup 文件、来源、大小、SHA；
- ramdisk backup 文件、来源、大小、SHA；
- dtbo backup 文件、来源、大小、SHA；
- recovery/recovery_vbmeta/misc 仅在相关时列出，不能因存在 TWRP 就当作原厂 recovery 已验证。
若只有任务报告而无原始文件，要说明仅引用，不能冒称本轮重新核验。

输出 partition_write_readback_recovery_matrix.csv，明确 NO-GO 缺项。

---

## 8. 阶段 F — ACK Android 17 直接 ABL 的适配设计

不修改、不编译、不重新打包，只形成可复核的技术方案。

### Kernel
- PREP10 raw Image 能否符合 ABL 当前 raw 路径的 text_offset/alignment 契约。
- ACK Image.gz 是否会命中 gzip/decompress 路径，解压后地址是否满足 ARM64 boot protocol。
- 若不满足，是否能从 ACK 源码/配置层生成合规 Image；禁止手工修改已构建 Image header。
- 给出最小源码修正方向和验证条件。

### Boot v2
- 保留本机 stock boot header v2、embedded ramdisk、page size、boot offsets、recovery_dtbo、header size。
- 只讨论替换 ACK kernel、本机 VD DTB 和经证据批准的 cmdline。
- 复核 AOSP boot image ID 的 SHA1 component + 4-byte length 算法。
- 检查 boot payload 大小与 96 MiB partition、svesnav 的 STOCK_PAYLOAD_SIZE 限制之间的差异。
- 不得套用 svesnav 固定 stock hash。

### Android cmdline / bootconfig
- 保留必需的 stock Android token。
- 分清 androidboot.dtbo_idx、androidboot.hardware、androidboot.verifiedbootstate、androidboot.boot_devices、earlycon 等 token。
- 判断 Android 12 Huawei first-stage init 与 ACK Android 17 的 bootconfig/cmdline 兼容性。
- 需要的 bootconfig 从哪里取得、如何传递必须有依据。

### K3 最小要求
- 检查 binder/binderfs、devtmpfs、dm-verity、fscrypt、F2FS/EROFS、UFS、dynamic partitions、bootconfig 等配置。
- first-stage mount 必需驱动应 built-in，不能依赖 system/vendor 已挂载后才可加载的模块。
- 明确“内核开始执行”“Android first-stage init 执行”“Android framework/DerpFest 完整启动”是三个不同验收阶段。

---

## 9. 阶段 G — 与 CoWave U-Boot 方案比较

AI1 研究 CoWave U-Boot chainloader，AI2 仅需独立比较结论：

| 项目 | svesnav Direct ABL | CoWave U-Boot Chainloader |
|---|---|---|
| 第一阶段 | ABL 直接加载 Linux Image.gz | ABL 启动 U-Boot |
| 首次写入 | Android 依赖决定 boot-only 或 boot+ramdisk+dtbo | recovery + recovery_vbmeta |
| Kernel load alignment | 受 ABL 分支和 Image text_offset 约束 | U-Boot 指定 Kernel load/entry |
| VD overlay | 使用本机 stock VD Entry 2 | U-Boot control FDT 与 kernel FDT 都要 VD 适配 |
| Android ramdisk | 优先保留 stock separate ramdisk | FIT 必须传递/加载 Android ramdisk |
| 调试 | ABL K1 观察能力较弱，Kernel/K3 后观察 | 可先见 U-Boot console |
| 更新方式 | direct ABL partition update | U-Boot Fastboot + FIT 暂存 |

给出客观矩阵，不能因 AI1 负责另一条路线而偏袒任何一方。

---

## 10. 最终判定字段

    SVESNAV_REFERENCE_IDENTITY       = PASS / FAIL
    ABL_FASTBOOT_BOOT_REFUSAL         = CONFIRMED / REPORTED / UNKNOWN
    STOCK_BOOT_V2_REPACK_METHOD       = CONFIRMED / PARTIAL / UNKNOWN
    SVE_KERNEL_PAYLOAD_FORMAT         = IMAGE_GZ / UNKNOWN
    SVE_UNCOMPRESSED_TEXT_OFFSET      = measured value / UNKNOWN
    ABL_GZIP_KERNEL_DEST_OFFSET       = 0x8000 / 0x80000 / UNKNOWN
    PREP10_RAW_ALIGNMENT              = PASS / FAIL / UNKNOWN
    ACK_IMAGE_GZ_ALIGNMENT            = PASS / FAIL / UNKNOWN
    ACK_SOURCE_ADAPTATION_NEEDED       = YES / NO / UNKNOWN
    ANDROID_RAMDISK_POLICY            = KEEP_STOCK / REPACK_REQUIRED / UNKNOWN
    VD_DTBO_POLICY                    = KEEP_STOCK_VD_ENTRY2 / NEW_VD_OVERLAY_REQUIRED / UNKNOWN
    BOOT_PARTITION_SIZE_CHECK         = PASS / FAIL / UNKNOWN
    SEPARATE_RAMDISK_AVB_FOOTER       = VERIFIED / UNKNOWN
    WRITE_READBACK_ROLLBACK_PLAN      = COMPLETE / PARTIAL / UNKNOWN
    DIRECT_ABL_ACK_ANDROID             = FEASIBLE / FEASIBLE_WITH_IMAGE_ADAPTATION / BLOCKED / UNKNOWN
    RECOMMENDED_NEXT_STEP             = one specific action
    DEVICE_WRITE_PERFORMED            = NO
    DEVICE_CONNECTED                  = NO

---

## 11. AI2 交付与 GitHub 规则

仓库：hhdy/matepad11-dby-w09-agent-reports
分支：ai2/direct-abl-partition-adapt02
目录：firmware-analysis/boot-v2/direct-abl-partition-adapt02/

必须提交：
1. AI2_K1_DBY_W09_DIRECT_ABL_PARTITION_ADAPT02_REPORT.md
2. boot_v2_repack_analysis.md
3. abl_imagegz_alignment_analysis.md
4. android_ramdisk_and_bootconfig.md
5. vd_dtbo_policy.md
6. partition_write_readback_recovery_matrix.csv
7. evidence_matrix.csv
8. SHA256SUMS.txt
9. 必要的脱敏分析脚本/资料；禁止上传完整原始固件和设备敏感数据。

提交后逐项 fetch/read-back，记录 commit SHA、Git blob SHA、本地 SHA-256 与内容一致性。

---

## 12. 严格禁止事项

- 不连接平板，不检查当前设备模式，不让用户切换模式。
- 不运行 ADB/Fastboot/OEM/EDL 命令。
- 不执行 fastboot boot 重试。
- 不执行 fastboot flash、dd、分区写入、分区读回。
- 不重启、不刷 recovery、不执行 TWRP/HiSuite。
- 不修改 boot、ramdisk、DTBO、DTB、vbmeta、ABL。
- 不修改 ACK 源码，不改 head.S，不重新编译，不生成新候选镜像。
- 不把 VG overlay 写入 VD。
- 不把 svesnav 的 Linux SD-root initramfs 替换本机 Android separate ramdisk。
- 不套用 svesnav 的固定 stock boot SHA。
- 不把 Image.gz 文件更小误说成已解决 Image 对齐问题。

---

## 13. 停止条件

1. 完成 direct ABL 分区启动的源码证据链和 ACK Android 适配判定后立即停止。
2. 若缺本机离线备份，列出准确文件/字段，不连接设备。
3. 若物理分配地址余数必须运行时才能确认，标 UNKNOWN；提出最小只读观测需求，不执行。
4. 若 ACK Image.gz 需要源码适配，只提出方案，不修改、不编译。
5. 不扩展成通用华为刷机研究，不分析无关机型。
6. 最终报告交 AI1 独立审核，再由 AI1 和用户决定是否进入镜像制作或设备写入阶段。

**成功标准不是“把三个分区刷上去”，而是以可靠证据证明第二种 ABL 直接分区启动法能否用于本机 VD + ACK Android 17，并明确唯一下一步行动。**
