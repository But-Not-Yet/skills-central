---
name: codex
description: "把编程任务委派给 OpenAI Codex CLI 时使用。只要要开 feature、重构或审查 PR，就主动加载，即使用户只说「用 Codex 干」或「让 Codex 跑一下」。不用于 Claude Code / OpenCode 专属流程。"
version: 1.0.1
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Codex, OpenAI, Code-Review, Refactoring]
    related_skills: [claude-code, hermes-agent]
---

# Codex CLI

通过 Hermes terminal 把编码任务委派给 [Codex](https://github.com/openai/codex)。Codex 是 OpenAI 的自主编码代理 CLI。

## 何时使用

- 构建 feature
- 重构
- PR 审查
- 批量修 issue

需要 codex CLI 与 git 仓库。

## 前置条件

- 已安装 Codex：`npm install -g @openai/codex`
- 已配置 OpenAI 认证：`OPENAI_API_KEY`，或来自 Codex CLI 登录流程的 Codex OAuth 凭证
- **必须在 git 仓库内运行** —— Codex 拒绝在仓库外运行
- 在 terminal 调用中用 `pty=true` —— Codex 是交互式终端应用

对 Hermes 自身，`model.provider: openai-codex` 在 `hermes auth add openai-codex` 之后使用来自 `~/.hermes/auth.json` 的 Hermes 托管 Codex OAuth。对独立 Codex CLI，有效的 CLI OAuth 会话可能位于 `~/.codex/auth.json`；不要仅凭缺少 `OPENAI_API_KEY` 就断定 Codex 认证缺失。

## 一次性任务

```
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

临时性工作用（Codex 需要 git 仓库）：
```
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

## 后台模式（长任务）

```
# Start in background with PTY
terminal(command="codex exec --sandbox workspace-write 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if Codex asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

## 关键 Flags

| Flag | 作用 |
|------|--------|
| `exec "prompt"` | 一次性执行，完成后退出 |
| `--sandbox workspace-write` (`-s`) | 沙箱化，但自动批准 workspace 内的文件改动（推荐的自动构建模式） |
| `--dangerously-bypass-approvals-and-sandbox` | 无沙箱、无批准（最快也最危险；`--yolo` 仍作为隐藏别名可用） |
| `--sandbox danger-full-access` | 无 Codex 沙箱；当宿主 service 上下文破坏 bubblewrap 时有用 |

> **已弃用：** `--full-auto` 仍可用，但现行 CLI 会提示改用 `--sandbox workspace-write`。

## Hermes Gateway 注意事项

从 Hermes gateway/service 上下文（例如 Telegram 驱动的 agent 会话）调用 Codex CLI 时，即使同一命令在用户的交互式 shell 中可用，Codex 的 `workspace-write` 沙箱化也可能失败。典型症状是 bubblewrap/user-namespace 错误，如 `setting up uid map: Permission denied` 或 `loopback: Failed RTM_NEWADDR: Operation not permitted`。

在该上下文中，优先用：

```
codex exec --sandbox danger-full-access "<task>"
```

改为以进程边界作为安全层：显式 `workdir`、启动前干净的 git 状态、收窄的任务提示、`git diff` 审查、针对性测试，以及在提交大范围改动前的人工/agent 确认。

## PR 审查

克隆到临时目录以安全审查：

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## 用 Worktree 并行修 Issue

```
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 ~/.hermes/cache/scratch/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 ~/.hermes/cache/scratch/issue-99 main", workdir="~/project")

# Launch Codex in each
terminal(command="codex --sandbox workspace-write exec 'Fix issue #78: <description>. Commit when done.'", workdir="~/.hermes/cache/scratch/issue-78", background=true, pty=true)
terminal(command="codex --sandbox workspace-write exec 'Fix issue #99: <description>. Commit when done.'", workdir="~/.hermes/cache/scratch/issue-99", background=true, pty=true)

# Monitor
process(action="list")

# After completion, push and create PRs
terminal(command="cd ~/.hermes/cache/scratch/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# Cleanup
terminal(command="git worktree remove ~/.hermes/cache/scratch/issue-78", workdir="~/project")
```

## 批量 PR 审查

```
# Fetch all PR refs
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")

# Review multiple PRs in parallel
terminal(command="codex exec 'Review PR #86. git diff origin/main...origin/pr/86'", workdir="~/project", background=true, pty=true)
terminal(command="codex exec 'Review PR #87. git diff origin/main...origin/pr/87'", workdir="~/project", background=true, pty=true)

# Post results
terminal(command="gh pr comment 86 --body '<review>'", workdir="~/project")
```

## 规则

1. **始终用 `pty=true`** —— Codex 是交互式终端应用，没有 PTY 会挂起
2. **需要 git 仓库** —— Codex 不会在 git 目录外运行。临时工作用 `mktemp -d && git init`
3. **一次性任务用 `exec`** —— `codex exec "prompt"` 运行后干净退出
4. **构建用 `--sandbox workspace-write`** —— 自动批准沙箱内改动（为此 `--full-auto` 已弃用）
5. **长任务用后台** —— 用 `background=true` 并用 `process` 工具监控
6. **不要干扰** —— 用 `poll`/`log` 监控，对长任务保持耐心
7. **可并行** —— 批处理时同时运行多个 Codex 进程
