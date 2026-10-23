---
name: skill-library-sync
description: 同步或体检三个 profile 的技能库时加载：git 化单一事实源同步管线。
---

# 技能库 git 化同步（2026-10-22 建成）

## 拓扑
- 事实源：`~/.hermes/skills-central.git`（bare）。default 库 `~/.hermes/skills` = main 分支；coder/researcher 各自分支，remote 指同一 central。
- 角色排除：`~/.hermes/skill_roles.conf`，每行 `profile<TAB>相对路径`。排除项在每个 profile 侧删除并提交（persona/运维小抄不进 worker 库）。加新排除只改这个文件，下轮同步生效。
- 脚本：`~/.hermes/scripts/skill_git_sync.sh`，cron 作业 `skill-git-sync`（every 30m，no-agent，failure-deliver local）。日志 `~/.hermes/skills-sync-report.log`。

## 流向规则（改脚本前必读）
- 双向：profile 本地改动 commit 后 push 自己分支；main 主动 merge `origin/<prof>` 收 worker 成果，再让 profile merge `origin/main` 吃回。
- 冲突不自动裁决语义：机械取 main 版保现场，同时开 red-team-auditor 看板卡（标题「技能回流冲突待判」）。**冲突解决方向永远是 main 优先**，worker 侧改动要靠检察官裁决后才进 main。
- 提交身份固定 `Independent Researcher <noreply@localhost>`（署名红线）。

## 坑（实测踩过）
- 旧 profile 目录接 central 用 `init + reset --soft origin/main` 会把 main 独有文件从工作区抹掉——onboarding 后必须 `git checkout origin/main -- .` 补回，且要在 merge 前验 main 独有文件（kanban-dispatch、work-discipline-detail）在位。
- `hermes cron create --script` 只收 `~/.hermes/scripts/` 下的**裸文件名**，绝对路径被拒。
- central 是本地 bare 仓库，不走 GitHub，零个人信息；要备份就再挂一个 remote（主人 git 红线：匿名 key + IdentitiesOnly）。

## 验收
演练法：default 加一行标记 → 跑脚本 → grep 两 profile 命中；profile 建 `_sync_probe` 技能 → 跑脚本 → default 出现同名文件；删探针再跑一轮确认删除也传播。全绿才算同步活着。
