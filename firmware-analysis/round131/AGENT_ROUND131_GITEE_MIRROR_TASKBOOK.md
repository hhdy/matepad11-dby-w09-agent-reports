# [发给测试 Agent] ROUND131 — Gitee 六仓库只读镜像到 GitHub

任务 ID：AGENT-ROUND131-GITEE-MIRROR
下发方：1号 AI（ChatGPT）
执行方：用户本地 WorkBuddy Agent
审核方：1号 AI（ChatGPT）

用户明确授权本轮将以下公开 Gitee 仓库复制到 GitHub，以便 1号 AI 后续直接阅读。**这是复制，不是迁移/删除。Gitee 原仓库必须保持不变。**
这不是内核开发任务，不分配给 2号 AI。

## A. 六个源与目标

GitHub 目标 owner 固定为本项目现有 GitHub 账号 owner：hhdy。目标全部创建为 Private。

| # | Gitee 源 | 新 GitHub 目标 |
|---|---|---|
| 1 | https://gitee.com/gxde-pocket/gxde-kernel-dby-w09.git | hhdy/gxde-kernel-dby-w09 |
| 2 | https://gitee.com/gxde-pocket/gxde-hwsupport-dby-w09.git | hhdy/gxde-hwsupport-dby-w09 |
| 3 | https://gitee.com/gxde-pocket/gxde-dby-w09.git | hhdy/gxde-dby-w09 |
| 4 | https://gitee.com/gxde-pocket/pocket-linux.git | hhdy/pocket-linux |
| 5 | https://gitee.com/gxde-pocket/gxde-touch-calibration.git | hhdy/gxde-touch-calibration |
| 6 | https://gitee.com/uni-xnu-dby-w09/UniXNU-dby_w09.git | hhdy/UniXNU-dby_w09-gitee-mirror |

第 6 项目标必须带 -gitee-mirror，避免覆盖 WQSQW/UniXNU-dby_w09、bangbang0822 等任何已有仓库。

## B. 账号与覆盖保护

1. 运行 gh auth status 与 gh api user。确认 GitHub 登录身份是 hhdy 且具有创建 hhdy private repositories 的权限。否则停止报告；不可擅自改用其他 owner。
2. 对六个目标逐一运行 gh repo view hhdy/<name>。若任意目标已存在，不得覆盖、不得 force-push、不得改变其 refs；该目标标记 SKIPPED_TARGET_EXISTS，继续其余目标。
3. 新建独立临时目录，绝不覆盖/复用/删除已有目录。
4. 不执行任何 Gitee push。源仓库完全只读。
5. 不需要平板、USB、ADB、fastboot 或串口访问；禁止接触设备。

## C. 每仓镜像步骤

对每个目标仓库：

1. 新临时目录运行：
   git clone --mirror <GITEE_URL> <name>.git
   若 clone 失败，记录 stderr、退出码，不要生成空仓库假装成功。
2. 记录 source URL、HEAD、git remote -v、git show-ref 输出、refs 数量、heads 数量、tags 数量、最近提交 SHA、git count-objects -v。
3. 检查 git lfs 是否安装及 .gitattributes / LFS pointer。若仓库用 LFS：
   git lfs fetch --all origin
   镜像后：
   git lfs push --all github
   并记录 LFS 对象数量与传输/核验结果。没有 LFS 则明确记 NONE。
4. 检查 .gitmodules 与所有 gitlink/submodule SHA；记录 URL 和具体 SHA。主仓库镜像不能假称已镜像外部 submodule。不要擅自替换 .gitmodules URL。
5. 创建新的 Private GitHub 仓库：
   gh repo create hhdy/<name> --private --confirm
   若命令行 gh 版本没有 --confirm，使用其支持的等价非交互参数。不得创建 public。
6. 添加 GitHub remote，例如：
   git remote add github https://github.com/hhdy/<name>.git
   在 GitHub 目标确实为空时运行：
   git push --mirror github
   GitHub 拒绝平台保留 refs 时，不要删除源 refs；改为推送 heads/tags/notes 可推 refs，并把遗漏 ref 逐一列出。
7. 推送后重新从 GitHub 目标运行 git clone --mirror 到第二个独立临时目录，核验 source / target refs。逐一对比所有目标 heads 与 tags 的名称和 commit SHA；核对默认分支、最新 commit、对象完整性。存在 LFS 时验证 GitHub 能 fetch 全部 LFS 对象。
8. 每个 GitHub 仓库必须确认 Private=true。不得将源仓库的私密 local config、凭据或本地未跟踪内容上传；只镜像源端公开 Git refs 内容。
9. 全部结束后删除本轮创建的临时 clone 与 scratch；不要删除其他 Agent 工作目录或任何既有 build tree。

## D. 唯一报告和验收

只新增并上传：
firmware-analysis/round131/AGENT_ROUND131_GITEE_MIRROR_REPORT.txt
上传到本仓库 firmware-audit-v1 分支。

报告需逐仓记录：
- source URL、目标 GitHub URL、私有状态；
- clone RC、source HEAD、默认分支、refs/heads/tags 数量；
- 所有 refs 是否完整，若不完整列出缺失 refs；
- 目标端逐 ref SHA 对比是否一致；
- LFS 是否存在及对象是否完整；
- submodule path / URL / gitlink SHA；
- 最近 commit SHA、对象数量/仓库大小；
- SKIPPED / FAILED / PASS 实际结果；
- 设备安全声明：没有连接平板、没有执行任何设备命令；
- 原 Gitee 源未被修改。

只交这一份脱敏文本报告，不上传二进制或 token/凭据。报告上传后读回确认并停止，不开启 ROUND132。