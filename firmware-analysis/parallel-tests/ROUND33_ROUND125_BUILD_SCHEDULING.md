# 并行验证调度追加 — ROUND33 / ROUND125

更新日期：2026-11-25

## AI2 ROUND33 复验当前状态

- 第一份 ROUND33 revalidation report 的实际执行对象是 Stage A branch HEAD `c4ee77184e2bf4e4eadf6280e67a510be5e729e5`。
- 报告证实 patch 16/17 identity、17-patch apply、checkpatch 都通过，但 host harness 失败：
  - ROUND31 legacy suite: 38 checks / 12 failures；
  - ROUND32 suite: SIGSEGV 139，ghost non-self target 测试仍按旧 deferred 语义并解引用 `ERR_PTR(-EINVAL)`。
- 2号 AI 随后只修改了 host tests/mock（没有改变 patch16/17 runtime semantics），在当前 AI2 branch 后续 commit 中补充 provider-level self-target fixtures / target registration，并把 ghost cross-target 场景改为预期 `-EINVAL`，另加 deferred self-target unregister 测试。
- **这次修复尚未被 Agent 重测。** ROUND33 仍不算通过；schema、完整 Image 和 ROUND58 回归仍待在修复后的实际树上验证。

历史失败报告保留：
`firmware-analysis/round33/AI2_ROUND33_REVALIDATION_REPORT.txt`

## AI1 ROUND125 新任务

候选分支：`ai1/round125-qmp-ufs-rail-state`  
任务书：`firmware-analysis/round125/TEST_AGENT_ROUND125_TASKBOOK.md`  
候选补丁：`kernel-baseline/round125/0001-qmp-ufs-rail-state.patch`

ROUND125 目标是 AI1 ROUND63 后的 QMP UFS L5/L9 双 rail state accounting，和 ROUND33 不同文件，但 full Image build 必须避开 ROUND33 的重测 build。

## 构建调度规则

1. ROUND33 修复后的 host suites 必须先重测；通过后再完成其 schema/config/full Image build，并发布 `ROUND33 FULL BUILD SLOT RELEASED`。
2. ROUND125 可先进行 identity、patch apply、source gates、checkpatch 和目标对象编译；不得修改 AI2 workspace。
3. 在 ROUND33 发布完整构建时段释放前，ROUND125 不得运行第二个完整 Image build。
4. 两个 Agent 窗口必须使用独立 clone/worktree/build workspace。
5. 任一任务需要设备访问时，必须在连接前停下并征求用户明确许可。当前两个任务均不需要设备访问。


## Agent assignment confirmation (2026-11-25)

用户已确认：**ROUND33 修复后的重新验证任务已经由 2号 AI 交给本地 Agent 再次处理。**
因此：
- 不再重复派发 ROUND33，也不向用户要求再次安排；
- ROUND33 复测期间，Agent 优先执行 2号 AI 的 ROUND33 任务；
- ROUND125 任务书已就绪，但不能假定 Agent 已开始它；
- 1号 AI 继续独立源码审查/补丁工作。ROUND125 等 ROUND33 完成后再占用 Agent 进行独立验证；完整 Image 构建仍按前文顺序排队。
