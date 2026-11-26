[发给测试Agent]

你是用户本地 WorkBuddy 测试 Agent。你不是 2号 AI。

请执行 **ROUND135 Revision 2（两棵独立源码树的 23-patch identity / offset / final-tree preflight）**。

## 角色
- 下发方 / 技术负责人 / 源码候选负责人：1号 AI（ChatGPT）
- 执行方：本地 WorkBuddy 测试 Agent（你）
- 独立核验方：2号 AI
- 最终任务复核方：1号 AI（ChatGPT）

## 必读任务文件
分支：`ai1/round130-stagea-ufs-lifecycle-integration`

1. `kernel-baseline/round135/TEST_AGENT_ROUND135_TASKBOOK.md`，必须阅读文件末尾 **Revision 2**（当前 blob `7bb2c2ea1749e0c7b84469472123d498c5823e8c`）。
2. `kernel-baseline/round135/ROUND135_23_PATCH_SERIES_MANIFEST.md`（当前 blob `6268dd363c08f549e2fd092364adafc65bce93e9`）。
3. `kernel-baseline/round135/ROUND135_PATCH22_REMEDIATION_1AI_REVIEW.md`。
4. `kernel-baseline/round135/ROUND135_PATCH23_DEDUPLICATION_1AI_REVIEW.md`。

## 核心固定身份
- ACK commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- ACK root tree: `790a68ae6d4f4ac51ab2d88977b6fd5c031473b7`
- Frozen 17 manifest blob: `9a93b7e3a500d807533517a92b98fe244b2ea456`
- Frozen 17 post-series tree expected: `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`
- Updated full 23-patch manifest blob: `6268dd363c08f549e2fd092364adafc65bce93e9`
- Patch 22 board DTS only blob: `ab0108364c835d87ac35ca670347d9d0001a821d`
- Patch 23 Makefile DTB entry only blob: `ceb72ed206d97beb2c2fa8558cb120ee186cb685`
- Updated DTS source blob: `58293f7a62a50f8109886c92ce4b9cd14d7980e2`

重要：冻结 patch 5 已包含完整 UFS dual-GenPD / required-OPP driver。旧的 ROUND45 duplicate driver patch 已从本序列移除。**不得再应用旧 patch23 driver**；当前 patch23 是 TAB-exact Makefile DTB entry。必须以最新 manifest 为权威，逐个核验全部 23 个 patch 的 blob、SHA-256、大小及顺序。

## 本次只做什么
建立 Tree A / Tree B 两个真正独立的 clean ACK clone（独立 Git object database、index、工作目录），按清单重放 23 个 patch：
- 每个 patch：`git apply --check --verbose` → `git apply --verbose` → `git diff --check`；
- 逐 patch/逐 hunk 保存所有非零 offset；
- patch17 后，两个树都必须得到 frozen 17 expected tree `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`；
- patch23 后，两棵独立树必须得到完全相同的完整 23-patch final Tree SHA；
- 保存完整原始日志、身份、offset、树 SHA 和 clean-state 记录；
- 上传并回读 R2 preflight 报告后立即停止。

## 关键规则
必须遵守 ROUND132 controlled-offset policy：
`kernel-baseline/round132/ROUND132_OFFSET_ACCEPTANCE_POLICY_1AI.md`

已知历史 offset：
- patch16：H1 -25、H2 -2、H3 +2；
- patch17：H1 +1、H2 -2；
- patch20 / ROUND128 V2：H3 -19。

准确披露实际结果，不可把 offset 写成 0。不得 fuzz、ignore whitespace、降上下文、3-way、skip、reorder、partial apply 或人工修补。两棵树任何身份不符、apply 失败、offset 不同或 tree SHA 不一致，保存证据后停止并报 BLOCKED。

**本轮的完整 23-patch expected Tree SHA 尚未预先钉死。** 你只负责在两个独立树中生成并报告同一个 candidate final Tree SHA，不得自行把单树结果定为 expected。报告上传后由 2号 AI 独立核验原始日志与 Tree SHA，再由 1号 AI 将经核实的 SHA 写入后续任务书。后续 Schema/DTB/Kconfig/编译/Image/回归测试在 R2 不得执行。

## 严格禁止
- 不连接平板；不使用 USB、ADB、fastboot、recovery、serial、root，不读写分区；
- 不读/下载/提取固件；
- 不改 patch、DTS、config 或任何源码；
- 不覆盖旧报告，不修改 main / AI2 / protected DTS branch，不 merge/cherry-pick/PR；
- 不运行 dt-schema、dtbs_check、DTB、Kconfig、C compile、Kleaf/Image build、Host regression、checkpatch 或 SPDX；
- 不重新部署 WSL、不 repo init/sync、不安装依赖。

交付目录：
`firmware-audit-v1/firmware-analysis/round135/r2-preflight/`

完成全部上传和 GitHub 回读核验后停止。不要自行开始 ROUND135 后续测试。
