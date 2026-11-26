[发给测试Agent]

你是本项目的本地 WorkBuddy 测试 Agent，不是 2号 AI。

请执行 **ROUND135 Revision 1（patch-22 修复后的完整 23-patch 重验证）**。

## 角色
- 下发方 / 技术负责人：1号 AI（ChatGPT）
- 源码候选负责人：1号 AI（ChatGPT）
- 执行方：你（本地 WorkBuddy 测试 Agent）
- 独立审查方：1号 AI（ChatGPT）

## 先读文件
在分支 `ai1/round130-stagea-ufs-lifecycle-integration`：
1. `kernel-baseline/round135/TEST_AGENT_ROUND135_TASKBOOK.md`（必须阅读末尾 Revision 1 addendum；当前 Git blob `865c0f2a7eb15f3cf8594c757cf658005d33ea3f`）
2. `kernel-baseline/round135/ROUND135_23_PATCH_SERIES_MANIFEST.md`（当前 blob `ffcb225b4a28974350bd1cc8588fdb95df9372d0`）
3. `kernel-baseline/round135/ROUND135_PATCH22_REMEDIATION_1AI_REVIEW.md`

固定输入：
- ACK `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`
- 冻结 17-patch manifest blob `9a93b7e3a500d807533517a92b98fe244b2ea456`
- 更新 DTS blob `58293f7a62a50f8109886c92ce4b9cd14d7980e2`
- 修正 patch 22 blob `ea15a051d75cb0c9b8319fff30f0c7cf6bb7ed6f`
- patch 23 blob `2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5`

## 本轮目标
按 taskbook Revision 1 从全新隔离目录重放补丁 1–21，确认 17-patch content tree 精确等于 `77e2b2b1515b3813f7538aedffe4c5a4e90edb57)，然后依次应用修正 patch 22 和 patch 23。两者都通过后，继续完成原任务书中的真实 dt_binding_check、真实 board DTB、完整 dtbs_check、DTB 反编译、Kconfig/.config、UFS object、完整 Kleaf Image build、38/38 + 83/83 回归和静态检查。

**旧 ROUND135 首轮报告是历史 BLOCKED，不要覆盖或改写。新报告和日志全部上传到 `firmware-audit-v1/firmware-analysis/round135/r1/`。**

禁止修改任何补丁或源文件，禁止忽略空白、缩减上下文、3-way apply、fuzz、跳过或重排补丁。禁止连接平板或使用 USB/ADB/fastboot/recovery/serial；不提取固件、不打包、不启动、不刷写、不读写分区；不 merge/cherry-pick/PR。若任何固定身份不符或 apply 失败，立即保存日志并停止交给 1号 AI。

完成上传并回读所有文件后停止。不要自行进入下一轮。
