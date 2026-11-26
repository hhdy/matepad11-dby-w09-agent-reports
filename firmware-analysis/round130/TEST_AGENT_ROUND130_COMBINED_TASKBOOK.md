# [发给测试 Agent] AI1-ROUND130 四补丁集成验证

- Task ID: TEST-AGENT-AI1-ROUND130
- 下发方/代码所有者/审核方：1号 AI（ChatGPT）
- 执行方：用户本地 WorkBuddy 测试 Agent（只测试、构建、报告）
- 2号 AI：独立开发 AI；本任务不得修改其 Stage A 分支。
- 本轮纯离线。不得连接平板，不得发 ADB/fastboot/USB/串口/分区命令。
- Agent 不得修改/修复/重新生成任何补丁、源码、DTS、binding、测试、config。

## 1. 目标与固定输入

目标是在同一 21-patch 工作树上，集成此前两组分别通过构建的四份 1号 AI 候选，验证跨组兼容性。分组测试的 PASS 不替代本轮联合验证。

设备：Huawei MatePad 11 DBY-W09 / KONA / SM8250。
Stage A 固定基线：ai-parallel/stagea-port-until-boot@2f21233148a04afdd61e44b1be7688399967d9d0。
ACK：aosp-mirror/kernel_common @ 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a，android17-6.18.33_r00。
基础 series：kernel-baseline/round61/round32-stagea-series.txt，严格应用 17 个基础补丁。
不得改用 15-patch ROUND124 旧基线，也不得跟踪移动的 ACK HEAD。

## 2. 四个候选补丁（顺序不可改变）

从 origin 分支重新获取，核对 blob 和 SHA-256。包装分支 ai1/round130-stagea-ufs-lifecycle-integration 的 kernel-baseline/round130/ 中也有按顺序复制的四个文件，可以用于取值对照。

18. ROUND120 per-HBA async scan join
- origin branch ai1/round124-ufs-core-combined-candidates
- file kernel-baseline/round124/0001-ufs-core-per-hba-async-domain.patch
- blob f604c8672fcbc98f3e9645f5e8888c8a34b1c11e
- SHA-256 12efbe8a14d80f8b657bad763a344b5439abeb572158079beb32daba05e02bc7
- paths ufshcd-priv.h + ufshcd.c

19. ROUND122 UFS regulator load-first
- origin branch ai1/round124-ufs-core-combined-candidates
- file kernel-baseline/round124/0002-ufs-core-vreg-load-first.patch
- blob 64dd2ad9022251e2411a1a745aeb920a0badfa85
- SHA-256 2f335f513fd1f7013a0edbc2e0d9eb5dca9ae68055eff4fd526b1c4274cfca66
- path ufshcd.c
- 必须跟在 ROUND120 后面；两 patch 改 ufshcd.c 不同区段，仍须实测无冲突。

20. ROUND128 V2 QMP UFS dual-rail state
- origin branch ai1/round128-qmp-ufs-rail-state-v2
- file kernel-baseline/round128/0001-qmp-ufs-rail-state-v2.patch
- blob 22ccec1cabf2d78e61442d19219985135f8341e7
- SHA-256 53ef42bb997a46e776f65c256039b13285047f784fed506ab8b22ab7f76e3bfb
- path phy-qcom-qmp-ufs.c
- 禁止用旧 ROUND125 原始补丁（它会重复定义 qmp_ufs_power_off）。

21. ROUND126 proxy-consumer load-first
- origin branch ai1/round126-proxy-consumer-load-first
- file kernel-baseline/round126/0001-proxy-consumer-load-first.patch
- blob c180dbf458403d68b2c32c1d54776a7559e7e5db
- SHA-256 eae21b96d34ebff0e7bbd4843bcd4f96cda26b02f83dd6f323b8c571e51fef80
- path proxy-consumer.c

## 3. 执行步骤

1. 新建独立 disposable staging/worktree，从固定 ACK 开始。不得复用 ROUND127/129 或他人工作区。
2. 核对 17-patch manifest 的 17/17 identities，按顺序 apply。
3. 按第 2 节顺序应用四份候选，逐份运行并保存真实输出：
   - git apply --check --verbose
   - git apply
   - git diff --check
   记录 RC、offset、fuzz。身份错误、冲突或 fuzz 立即停止。
4. 记录 17-patch baseline 与最终 21-patch overlay 的 tracked diff hash、changed paths、untracked set。候选预期只增加四个源路径：ufshcd-priv.h、ufshcd.c、phy-qcom-qmp-ufs.c、proxy-consumer.c。
5. 对 21-patch tree 执行 §4 source gates，§5 host tests/checkpatch/object builds。
6. 任一对象失败，立即停止，不运行完整 Image build，不得自行修复。
7. 所有对象通过才执行 §6 完整 Image build 和 ROUND58 回归。
8. 撤销四份候选，哈希验证准确回到 17-patch baseline。清除本任务 staging、Bazel/object outputs 和临时日志；不得删除/更改其他工作区。

## 4. 必须 source gates（报告实际行号和 grep/源码证据）

**ROUND120 async lifecycle**
- async_domain、async_cookie_t、scheduled flag 只在私有 ufs_hba_priv；不改变 public ufs_hba。
- alloc_host 先初始化 async_domain pending/registered 和 scheduled=false。
- 唯一 UFS scan schedule 保存 async_schedule_domain 返回 cookie。
- remove 在读 HBA WLUN/resource 或 teardown 前 join cookie+1；未 schedule 不等待。
- 核对所有 alloc_host callers/remove paths，确认 join 前没有持有 host_sem 的调用者，避免死锁风险。不能只凭编译通过声称 runtime race 已验证。

**ROUND122 UFS regulator**
- disable 时 load-zero 先于 regulator_disable，load-zero 失败不 decrement；enabled 位只在 disable 成功后清除。
- enable 时在 enabled fast path 前恢复 load，不能重复 enable。
- 明确保留 generic regulator post-decrement/parent-coupling 与 devm put 限制。

**ROUND128 V2 QMP**
- 全文件只有一个 qmp_ufs_power_off() 定义，且复用 ROUND63 既有 callback；不得重复定义。
- vreg_enabled[2] / vreg_load_active[2] 独立跟踪。
- 特殊路径严格 two rails：vdda-phy、vdda-pll；异常布局 fail closed；property absent 保留 bulk path。
- load/enable state 只在对应 API 成功后更新；load-zero 失败不 disable。
- power-off 和最终 cleanup 先 L9 后 L5；idle 保留 L5 enable，final cleanup 才释放。
- 保留 void devm cleanup 不能 veto 后续 managed regulator_put 的限制。

**ROUND126 proxy**
- current_uA>0 时 regulator_set_load(reg,0) 在 regulator_disable 之前。
- 保留真实失败码、void unregister best-effort、deferred NULL early-return、enable=false cleanup、voltage cleanup。
- per-rdev unregister 与 late_initcall_sync bulk revoke 两条路径仍在。
- ROUND33 self-target-only rule 不变；不得 cross-target；不得 regulator_force_disable。

## 5. Host tests / checkpatch / object builds

在未修改的 21-patch tree 运行 bash tests/run_tests.sh，记录完整输出/RC。预期 legacy 38/38、ROUND32/33 83/83、0 failures、无 crash。

四份候选 patch 分别运行 scripts/checkpatch.pl --strict --no-signoff，报告 E/W/C/RC。本轮必须重新跑；ROUND128 V2 历史 0E/1W/0C，ROUND126 历史 0E/0W/1C；ROUND120/122 使用实际输出，不可称全 clean 或自动修复。

使用 manifest-pinned Kleaf Clang 和 Stage A config 编译：
- drivers/ufs/core/ 全部 7 个对象（含 ufshcd.o，因 ufshcd-priv.h 是共享头）
- drivers/phy/qualcomm/phy-qcom-qmp-ufs.o
- drivers/regulator/proxy-consumer.o
共 9 个对象。记录命令、工具链、RC、size、SHA-256。任何失败触发 stop rule。

## 6. Full Image + ROUND58（9 个对象全部 PASS 才允许）

执行：
tools/bazel build //common:dby_w09 --jobs=8 --local_ram_resources=6144

记录 BUILD_RC/duration、Image/System.map/vmlinux/.config size/SHA-256、Bazel action count。预期 .config byte-identical，SHA-256：
0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15。
以 overlay hash、对象 hash/symbol 等证明四份候选确实进入 build。
运行 ROUND58 config validator 33/33 和 helper tests 11/11。
尽可能从本次准确 manifest/logs 记录 manifest commit/XML SHA、Rust/Bazel 版本；没有则 PARTIAL，禁止推测。禁止上传任何二进制。

## 7. 安全、唯一报告、停止

本任务必须完全离线。不得 USB/ADB/fastboot/recovery/serial/其他设备接口；不得 boot/flash/root/unlock/访问分区或发设备命令。若任何步骤似乎需要设备访问，连接前停止，告诉用户类型/原因/拟执行命令，等待明确许可，即使只读也一样。

不得修改 main、AI2 Stage A、ACK DTS draft、PR #1、任何候选源分支、DTS/binding/test/config/firmware 或其他 workspace。

只上传唯一报告：
firmware-analysis/round130/TEST_AGENT_ROUND130_COMBINED_REPORT.txt
到 firmware-audit-v1。报告含身份、apply/offset/fuzz、源码 gates、host tests、checkpatch、9 个对象、full build/config/ROUND58、restore/cleanup、无设备操作声明。脱敏、不上传二进制。上传并 read-back 后立即停止，不得启动 ROUND131。
