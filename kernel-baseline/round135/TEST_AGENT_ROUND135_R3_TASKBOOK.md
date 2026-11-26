# ROUND135 R3 — pinned 23-patch source / schema / DTB / Kleaf validation taskbook

- **Task ID:** TEST-AGENT-AI1-ROUND135-R3
- **下发方 / 技术负责人 / 源码候选负责人 / 最终审查方：1号 AI（ChatGPT）**
- **执行方：用户本地 WorkBuddy 测试 Agent（只验证、构建、测试、报告）**
- **独立中间审查方：2号 AI（仅已完成 R2 的独立审查；本轮不向其分派本地执行）**
- **任务性质：验证固定的 23-patch ROUND135 候选。Agent 不得修改、修复、重排或重新生成任何源码、补丁、DTS、binding、Kconfig、测试或配置。**
- **安全范围：完全离线的源码、schema、DTB、Kconfig、对象编译、Kleaf Image 和 host 测试；不包含任何平板或固件操作。**

## 0. 唯一目标与不可变预期

在固定 ACK android17-6.18.33_r00 上独立重建并验证完整 ROUND135 23-patch 候选。只有新建验证树的完整内容树 SHA 与预先钉死的预期值一致，才允许继续 schema / DTB / Kconfig / compile / Image / host regression。

**预先钉死的完整 23-patch Git content-tree SHA：**

~~~text
afe9517f8062b96bfeb5b4dd5714942861e6a44b
~~~

这只是 Git 内容树 SHA，不是 commit SHA、内核 Image SHA、boot image SHA，也不代表设备已启动。

如果新验证树得到的完整 tree SHA 不完全等于上面的值，立即停止后续所有测试，保留原始证据并报告 BLOCKED / FAIL。不得更新预期 SHA，不得修改 patch/DTS 使其“匹配”。

## 1. R2 已完成证据与审计前提

R2 的两棵独立树已完成 23 个补丁的身份核验与受控 Offset 重放；2号 AI 已独立复核原始报告和日志，接受结果为：

- R2 独立验收报告：firmware-audit-v1:firmware-analysis/round135/r2-preflight/ROUND135_R2_PREFLIGHT_FINAL_REPORT.txt，blob 2d8b006482b4542e6018e27afbe8b4d8fbeed5d8。
- Tree A 原始日志：blob 6fe70593091d0aaed0478b8b5bb100d1479c1b7f。
- Tree B 原始日志：blob 87c7119c687448b1f1336f120a437ec15d8bba6d。
- 双树 Offset / tree 对照：blob 1a191291963d0e78c2138332fb639e5232d9d687。
- 上传与 readback：blob f03511589fba658a503fcb11efb6365396ff8a42。
- 2号 AI 独立验收：ai2/round135-controlled-offset-taskbook-audit:firmware-analysis/round135/AI2_ROUND135_R2_INDEPENDENT_ACCEPTANCE.md，blob 7b8ba0c0cb93dbac375c9d8325bea6b0812e54de。
- 23-patch manifest 的当前权威文件：本分支 kernel-baseline/round135/ROUND135_23_PATCH_SERIES_MANIFEST.md，当前 blob 9188de2022f88c374bfcaa367c505428812608d9。R2 执行时使用的同一 23 项清单快照 blob 为 6268dd363c08f549e2fd092364adafc65bce93e9；最新 manifest 增加了 R2 验收与 tree SHA 记录，23 个 patch 输入身份没有改变。
- 冻结 17-patch manifest：ai-parallel/stagea-port-until-boot:kernel-baseline/round61/round32-stagea-series.txt，blob 9a93b7e3a500d807533517a92b98fe244b2ea456。

R2 两树均得到：
- 17-patch 中间树：77e2b2b1515b3813f7538aedffe4c5a4e90edb57；
- 完整 23-patch 树：afe9517f8062b96bfeb5b4dd5714942861e6a44b。

R2 的本地旧 manifest 快照曾记录 blob 96b52a4fdbc1f63023ec1fbfc9aec12b8176cfdb，而权威冻结 manifest blob 为 9a93b7e3...。2号 AI 已独立获取两个 GitHub 版本，确认差异仅为 patch16/17 行尾状态注释；17 个 patch 的路径、blob、SHA-256、大小和顺序一致。**不要称两个 manifest 文件字节相同；R3 必须重新从权威 blob 9a93b7e3... 验证 patch identities。**

R2 的已复现受控 Offset（Tree A/B 相同）：
- patch16：H1 -25 lines；H2 -2 lines；H3 +2 lines；
- patch17：H1 +1 line；H2 -2 lines；
- patch20（ROUND128 V2）：H3 -19 lines；
- 其他 patch：primary git apply 未输出 offset 行。

这些非零 Offset 已按 ROUND132 受控 Offset 规则接受，R3 不要求零 Offset。R3 新重放必须完整披露并复现同一 Offset 模式；如出现任何新增或不一致 Offset，停止并交 1号 AI 审查，不得自行放行。

## 2. 固定源码、分支和输入身份

### 2.1 固定 ACK

- Repository: aosp-mirror/kernel_common
- Commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- Tag/version: android17-6.18.33_r00
- Root tree: 790a68ae6d4f4ac51ab2d88977b6fd5c031473b7

禁止切换 Linux stable v6.18.33、移动分支 HEAD、其他 tag 或任何新 ACK commit。

### 2.2 固定 23-patch manifest

从分支 ai1/round130-stagea-ufs-lifecycle-integration 读取：
kernel-baseline/round135/ROUND135_23_PATCH_SERIES_MANIFEST.md

当前文件 blob 必须是：
9188de2022f88c374bfcaa367c505428812608d9

逐项重新核验：
- 冻结 patches 1–17：必须与冻结 manifest blob 9a93b7e3a500d807533517a92b98fe244b2ea456 的路径、Git blob、SHA-256、byte size、顺序一致；
- patches 18–21：使用最新 23-patch manifest 所列四个 ROUND130 输入；
- patch 22：DTS-only，Git blob ab0108364c835d87ac35ca670347d9d0001a821d；
- patch 23：qcom Makefile DTB target-only，Git blob ceb72ed206d97beb2c2fa8558cb120ee186cb685；
- board DTS source blob：58293f7a62a50f8109886c92ce4b9cd14d7980e2；
- 固定 ACK qcom Makefile blob：296688f7cb26550f75bce65826f234bc24110356。

**Driver identity clarification:** 完整 SM8250 UFS dual-GenPD / required-OPP 实现已经存在于冻结 patch 5（round33-checkpatch-clean.patch，blob f1d54e5e0379183fbdfb3ca6132c6d0fc61d4622）。不得应用已被排除的旧 ROUND45 duplicate driver patch 2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5。当前 patch22 只增加 board DTS；当前 patch23 只增加 Makefile 的 DTB 目标入口。

## 3. 新验证树建立、补丁重放和预期 Tree SHA gate

1. 建立全新 disposable ACK source tree / clone；不得修改或复用为可写目标的 ROUND130、ROUND135 R1/R2 历史工作树、AI2 分支或现存 a30 工作区。可以从本地已固定 ACK 的对象库创建独立 clone，但 clone 必须拥有自己的 Git object directory / index / working tree，不得用 shared alternate、linked worktree 或硬链接共享对象。不得 repo sync、下载新固件、安装工具或重新部署 WSL。
2. 记录 remote、git version、HEAD、HEAD^{tree}、git-dir、git-common-dir、object alternates、initial git status。必须满足 HEAD 和 root tree 与 §2.1 完全一致，初始工作树 clean。
3. 按 §2.2 对全部 23 个输入逐一核验 Git blob、SHA-256、byte size 和 manifest order。不能只核验文件名。
4. 严格按 manifest 顺序应用 1–17，再 18 ROUND120、19 ROUND122、20 ROUND128 V2、21 ROUND126、22 DTS-only、23 Makefile-only。每个 patch：
   - 先执行 git apply --check --verbose；
   - 只有 check RC=0 时才执行 git apply --verbose；
   - 应用后执行 git diff --check；
   - 保存完整 stdout/stderr、原始命令、环境和 exit code；
   - 逐 patch / 逐 hunk 报告 check 与 actual apply 输出的全部 offset 行。
5. 必须复现 §1 中所有已接受历史 Offset。没有 offset 行的 patch 必须写为“primary applier 未输出 offset 行”，不要推断或改写为某个工具的诊断。
6. 严禁 fuzz、reject、skip、reorder、partial application、manual edit、context reduction、--ignore-whitespace、--ignore-space-change、--ignore-space-at-eol、--unidiff-zero、--3way、fallback applier、reject-based repair 或手工补丁修复。任何身份错、check/apply 错、diff-check 错、额外 Offset、fuzz、reject、上下文放宽或额外文件都要保存证据并停止。
7. patch17 后用临时 index（或等价且完整纳入 untracked 的方法）计算全量内容树，必须等于 77e2b2b1515b3813f7538aedffe4c5a4e90edb57；记录原始命令和临时 index 清理状态。
8. patch23 后同样计算完整 content tree，必须精确等于预先钉死的 afe9517f8062b96bfeb5b4dd5714942861e6a44b。必须包括 modified tracked files 和 new/untracked files。记录 git diff --stat、git status --short、git diff --check、变更路径集合、临时 index 计算方法。Tree SHA 不匹配时 **STOP — 不允许进行任何后续测试**。
9. R2 两独立树原始日志已满足独立重放见证，本轮新建的验证树用于独立重建被钉死的 SHA；不要修改或覆盖 R2 的五份历史证据。

## 4. Ubuntu UFS reference reconciliation（必须按此设计验证，不可自行改动）

必须阅读并遵守：
kernel-baseline/round135/AI1_ROUND135_UBUNTU_REFERENCE_RECONCILIATION.md

结论要点：
- Ubuntu 参考 DTB 的 Host 仅列 GCC UFS_PHY_GDSC，而 UFS OPP 仍引用 RPMhPD；AI2 的报告未包含 Ubuntu 7.3.1-loa 内核驱动源码，因此不能从 DTB 推断其 driver 如何路由 required-OPP。
- 固定 ACK sm8250.dtsi 的 UFS Host 有 37.5MHz/300MHz 两个 required-opps，基线 Host 只连 GCC GDSC。ROUND27 已指出这条默认拓扑本身不能证明实际 RPMhPD/MMCX vote。
- 候选冻结 patch5 的实现是：验证 MMCX index0 + GCC UFS_PHY_GDSC index1；验证每个 available UFS OPP 的单一 required-opps 指向 RPMhPD provider 的精确 OPP table；devm_pm_domain_attach_list(PD_FLAG_DEV_LINK_ON)；把 required_dev 显式设为第一个虚拟 domain（MMCX，index0）；然后才进入 ufshcd_pltfrm_init() 的通用 UFS OPP table 初始化。
- DBY-W09 board DTS 包含 sm8250.dtsi，预期继承原有 operating-points-v2 / OPP / required-opps，不得因 overlay power-domains 覆盖而假定 OPP 消失。

禁止为了匹配 Ubuntu DTB 而删除 MMCX domain、改动 required_dev、增加第二 required-opps slot、删除 GCC domain、修改 UFS PHY power-domain 或重写冻结 patch5。必须检查实际编译 DTB 来证明合并结果。

## 5. DTS source assertions、bindings、真实 DTB 与 dtbs_check

所有检查均针对本轮 §3 已通过 SHA gate 的最终源码树。

### 5.1 Source assertions

报告源文件和实际行号，并使用结构化解析 / grep / 脚本断言：

- root model / compatible 与候选 board DTS 一致；
- UFS Host compatible 为继承的 qcom,sm8250-ufshc；
- Host power-domains 恰好两项，顺序严格为：
  1. qcom,sm8250-rpmhpd / RPMHPD_MMCX；
  2. qcom,gcc-sm8250 / UFS_PHY_GDSC；
- UFS PHY 的 power-domains 仍只指向 GCC UFS_PHY_GDSC；
- UFS Host 仍继承 sm8250.dtsi 中 operating-points-v2 = <&ufs_opp_table>；
- 该 OPP table 的每个 available OPP 均恰有一个 required-opps；当前两个条目应为 37.5MHz→rpmhpd_opp_low_svs、300MHz→rpmhpd_opp_nom，并确认两个目标属于 rpmhpd provider 所广告的同一个准确 operating-points-v2 table；
- drivers/ufs/host/ufs-qcom.c 确实含有 all-available-OPP / provider-table exact-node validator、两个 domain 的 ID/顺序检查、devm_pm_domain_attach_list(PD_FLAG_DEV_LINK_ON) 和 required_dev=pd_list->pd_devs[0] / index 0；这些动作发生在 ufshcd_pltfrm_init() 之前；
- UFS Host IOMMU SID mapping、原 board UFS supplies / max-current / load 属性、status = "okay" 保留；不得删除或重写 inherited IOMMU specifiers；
- UFS PHY 保留 vdda-phy-always-on；不得添加已移除的 vdda-phy-max-microamp / vdda-pll-max-microamp；
- 不添加 guessed PMIC VIN parent、vph_pwr、dummy/fixed regulator 或 RAM 地址；
- qcom Makefile 恰有一个 huawei-dby-w09.dtb 目标，无重复条目、无无关更改；
- S8 的 qcom,vccq-parent-supply 在当前 ACK driver 中只是 DTS metadata；不得报告成已经有 runtime consumer / regulator enable / vote。

### 5.2 dt_binding_check

针对本候选修改的 schema 和依赖图运行真实 dt_binding_check。至少记录以下文件与依赖 schema：
- Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml
- Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.yaml
- Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml
- Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml
并检查 UFS schema 依赖图（包含 qcom,ufs.yaml，如当前 schema 解析实际会涉及）。

记录 dtschema / dtc / yamllint 版本、真实命令、环境、完整日志、exit code、warnings/check/errors。已知 huawei,dby-w09 root compatible 的 undocumented binding gap 必须原样记录；不得弱化 binding、删负向 fixture 或更改无关 Qualcomm schema 来让它通过。与本轮改动直接相关的 schema 失败标记 FAIL；固定 ACK 中可复现的外部工具/历史 schema 环境阻塞要单列 BLOCKED/PARTIAL，不能伪称 PASS。

### 5.3 真实 board DTB 构建

- 使用本轮完整、SHA gate 通过的源码树和固定 ACK 工具链，真正构建 arch/arm64/boot/dts/qcom/huawei-dby-w09.dtb。
- 使用 Kbuild 支持的标准 DTB 目标；记录完整命令、O= 输出目录、工具链版本、日志及退出码。若选择 Kleaf 中不同的标准目标，报告必须证明 target 定义及其输入路径。
- 不得用只对 hand-written fixture 运行 dtc 代替真实 board DTB build。
- 对刚刚生成的 DTB 使用 scripts/dtc/dtc -I dtb -O dts、fdtdump 或等价解析工具反编译，保存完整或足够定位的原始输出。
- 从最终 DTB 而非源 DTS 核验 5.1 全部关键点：双 domain phandle / cells / 顺序；UFS PHY 单 domain；OPP table；两个 required-opps 目标；model/compatible；supplies；IOMMU；Makefile 目标；PHY always-on。
- 明确 DTB 文件 SHA-256 / 大小。

### 5.4 dtbs_check

在同一最终源码树、相同固定 ACK 工具链和明确 O= 目录中运行完整 dtbs_check（不是只有单文件 dtc）。记录真实命令、schema 版本、完整日志和 exit code。若全量检查遇到无关的固定 ACK schema/tool 环境问题，逐条定位并如实分类；不得删除检查项或修改 schema 来规避。

## 6. Kconfig、受影响对象编译、完整 Kleaf Image

### 6.1 最终 .config

使用本轮最终源码 overlay 和固定 Stage A storage-first fragment 解析目标配置，保存完整 .config、来源、SHA-256 和 symbol report。至少核验以下符号是否为 =y（不得把 =m 当作 =y）：

SCSI_UFSHCD, SCSI_UFS_QCOM, PM_DEVFREQ, PM_OPP, PM_GENERIC_DOMAINS, PM_GENERIC_DOMAINS_OF, QCOM_GDSC, QCOM_RPMH, QCOM_COMMAND_DB, QCOM_RPMHPD, OF, REGULATOR, IOMMU_SUPPORT, ARM_SMMU.

ROUND130 .config SHA-256 基线：
0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15

本轮 config 不变更 fragment。比较本轮实际 .config 与上述 SHA / ROUND130 字节基线；如不同，报告完整 diff 和原因，不得强行修改配置或覆盖历史产物。可另外运行 kernel-baseline/round61/check_dby_w09_config.py 的 33-symbol validator 和 11 个 unittest，作为 supplementary regression，并单独列出结果。

### 6.2 受影响 C 对象编译

使用 manifest-pinned Kleaf Clang / LLVM 与本轮最终 .config 编译所有本轮实质修改的 C 翻译单元。至少包括：
- drivers/ufs/core/ufshcd.o
- drivers/ufs/host/ufs-qcom.o
- drivers/phy/qualcomm/phy-qcom-qmp-ufs.o
- drivers/regulator/core.o
- drivers/regulator/proxy-consumer.o

如果实际 diff 还改变其他 C 文件，也必须增加对应 object。保存每个命令、工具链身份、RC、warnings、对象大小与 SHA-256。不要使用系统默认 gcc 替代 pinned LLVM。对象编译失败，停止完整 Image build，并报告原因；不得修改源代码。

### 6.3 Full Kleaf build

上述 source/schema/DTB/config/object 必需门槛全部 PASS 后，执行完整目标：

~~~bash
tools/bazel build --jobs=2 //common:dby_w09
~~~

使用固定 ACK Repo / Kleaf / Clang / Rust 工具链和独立的输出目录。不得移动 repo manifest、更新工具链、重新 repo sync 或安装未知依赖。记录：
- BUILD_RC、完整 build log、elapsed time、Bazel action count；
- Image、System.map、vmlinux、最终 .config 的大小与 SHA-256；
- Repo manifest commit / manifest XML SHA-256；
- 可实际读取到的 Bazel / Clang / Rust 版本；无法读取时标记 PARTIAL / NOT AVAILABLE，不得猜测；
- 证明本轮最终 source tree SHA 和完整 23-patch overlay 是本次 build 的真实输入。

不生成 boot.img、vendor_boot、init_boot、DTBO、ramdisk、vbmeta、AVB 或任何可刷写包；不上传二进制。

## 7. Host regression、checkpatch 与 diff/SPDX

### 7.1 Host regression

必须从本轮最终树运行固定的 ROUND31/32/33 host harness，不能使用旧报告代替：

- Runner: kernel-baseline/round61/tests/run_tests.sh，blob e29f8a237e1836420dfcd85b7d970cf8d9a956d8
- Legacy suite: kernel-baseline/round61/tests/test_proxy_consumer_r31.c，blob 14515c62c48d95e86bfc6dca9c2070c81e031489
- ROUND32/33 suite: kernel-baseline/round61/tests/test_proxy_consumer_round32.c，blob aff9ec3c5bc65c880726431b5f23750b19339c1f
- mock core: kernel-baseline/round61/tests/mock/mock_core.h，blob 98820fc6c6439237563dad52c4129db022fb1260
- errno shim: kernel-baseline/round61/tests/mock/linux/errno.h，blob 8a8e39690876ebe9ffd3b56c553c2c773c2e333f

对上述测试文件逐项核验 blob / SHA-256 / size。用 runner 默认的真实 driver source 编译并运行两个 suite，保存完整编译输出、测试输出、各 RC。期望：
- legacy suite: checks=38, failures=0；
- ROUND32/33 suite: checks=83, failures=0；
- HARNESS_RESULT: PASS，0 crash / 0 SIGSEGV。

注意 runner 的旧注释仍写 ROUND32 suite 73；ROUND33 后新增断言后，ROUND130 实测是 83。以源测试实际执行输出 83/83 为期望，不得删测试或按旧注释降为 73。

测试工作目录、gcc 输出、临时程序和日志必须放在源码树之外。不得更改 mock、runner、测试源或真实 driver。

### 7.2 checkpatch

对当前 ROUND135 patch22（board DTS only）、patch23（Makefile DTB entry only）及新 DTS 源文件运行 scripts/checkpatch.pl --strict；保留完整输出和实际 E/W/C/RC。不要自动修复或修改任何文件。

对 patches18–21，引用 ROUND130 已接受报告中的历史记录并明确标注为历史值，不得冒称 R3 新执行：
- ROUND120: 0E / 4W / 1C / RC=1；
- ROUND122: 0E / 0W / 2C / RC=1；
- ROUND128 V2: 0E / 1W / 0C / RC=1；
- ROUND126: 0E / 0W / 0C / RC=0。

冻结 patch5 的 UFS dual-GenPD driver 已随 ROUND61/ROUND45 历史检查记录；不要把历史 checkpatch 伪装成本轮重新执行结果。最终报告逐项区分 current-run 与 historical evidence。

### 7.3 Diff / SPDX

- 执行最终 git diff --check，并保存完整命令和 RC。
- 检查 working tree / untracked paths 只包含固定 23-patch overlay；验证完整 content tree SHA 仍为 afe9517f8062b96bfeb5b4dd5714942861e6a44b。输出/build 文件放在源码树外。
- 独立 SPDX 检查若依赖缺失，准确标记 NOT RUN / BLOCKED 并记录原始错误；不可写成 PASS。
- 报告所有 warning、CHECK、error、非零 RC，不得只给“clean”摘要。

## 8. 交付物、GitHub 上传与 readback

所有报告均上传到新目录，不覆盖历史报告：

~~~text
firmware-audit-v1:firmware-analysis/round135/r3-validation/
~~~

至少包含：
1. ROUND135_R3_FINAL_REPORT.txt — 固定输入、tree SHA gate、source assertions、各项结果、剩余 blockers、最终结论；
2. round135-r3-identity-apply.log — ACK / manifest / patch blob+SHA+size / apply raw logs / all offsets / tree computation；
3. round135-r3-schema-dtb.log — source assertion、dt_binding_check、真实 board DTB build/decompile、dtbs_check；
4. round135-r3-kconfig-object-kleaf.log — final .config / symbols / affected object compile / full Image build / artifacts hash；
5. round135-r3-host-regression.log — 两组固定测试身份、完整实际测试输出和 RC；
6. round135-r3-checkpatch-diff-spdx.log — patch22/23/new DTS checkpatch、历史 checkpatch 记录、diff-check、SPDX 与所有 warning。

上传后从 GitHub raw / Contents API 回读每个文件，核验非空、byte-identical、Git blob 和 upload commit SHA。报告内记录完整文件身份及 readback。禁止覆盖 R2 任何文件；不上传 Image / vmlinux / DTB 或 firmware 二进制。

## 9. 结论规则

- **PASS — BUILD/DTB INTEGRATION ONLY**：身份 / exact tree SHA / Offset / source gates / schema / 实际 board DTB build 与 inspection / dtbs_check / final Kconfig / 所有受影响 object / full Kleaf Image / 38+83 Host regressions / diff/checkpatch 等均有真实日志且符合本任务要求。
- **FAIL**：已具备完整环境和真实执行条件，但源码断言、binding、DTB、对象编译、Image build、Host tests 或补丁身份发生实质失败。
- **BLOCKED / PARTIAL**：固定工具链或必需依赖缺失、schema/DTB 测试因无法消除的历史工具环境问题未完成、无法安全取得 pinned workspace，或必需测试未运行。逐项说明；不得把未运行写成 PASS。
- 不能使用 source review、ROUND130 build、ROUND61 hosted build、旧 fixture 或预期命令代替本轮实际测试。
- 即使本轮 PASS，也只证明离线 build / DTS integration。**不证明 UFS 真实 probe、MMCX 实际电压投票、MMCx→MX ARC 等价、PMIC physical input、ABL handoff、AVB/DTBO/ramdisk 选择、设备启动或硬件稳定性。**
- Phase E/F 仍按既有证据维持 BLOCKED；Phase G remains NOT RUN。

## 10. 安全边界与完成后停止

严格禁止：
- 连接平板、USB、ADB、fastboot、recovery、root、serial 或任何设备接口；
- 读取/写入设备分区，boot、flash、unlock、重启或设备测试；
- 下载、重新提取或写入 HOS4.3 / Ubuntu 固件；
- 制作、签名、刷写 boot / DTBO / AVB / vbmeta / ramdisk 包；
- 修改 patch、源码、DTS、binding、Kconfig、config、tests、manifest 或任务书；
- 修改 main、AI2 branch、protected DTS branch、PR #1 或任何其他分支；不 cherry-pick / merge / PR；
- 覆盖 ROUND135 R1/R2 历史报告、原始日志或 ROUND130 证据；
- 为通过检查而弱化 schema、删除 fixture、改变测试数或手工修补源码。

若任何必需步骤看似需要设备访问、固件提取、分区读取或写入，立即停止，不执行命令，并在报告中标记 BLOCKED。

完成上述授权范围后，将六份证据上传并逐个 readback，立即停止。不得自行启动 ROUND136 或任何其他轮次；等待 1号 AI 审查结果和明确的新任务书。
