---
name: github
description: "用 gh CLI 操作 GitHub 时使用：PR、issue、审查、仓库、认证。只要涉及 GitHub 认证、issue、PR 生命周期或仓库管理，就主动加载，即使用户没明说 gh。各工作流先读对应 references 再动手。"
version: 2.0.0
author: Ben Barclay (benbarclay), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, gh, git, pull-requests, issues, code-review, repos, auth, ci]
    category: software-development
    related_skills: [codebase-inspection, requesting-code-review]
---

# GitHub

用 `gh` CLI 端到端打理 GitHub（标注处用 REST 兜底）：认证、issue、PR 生命周期、issue 到 PR 的交付、代码审查、仓库管理。本技能合并了原先六个技能；每个工作流都完整地存在各自的 reference 文件里——开工前**务必**先读对应的 reference，下面正文只做导航。

## Routing（路由）

| 任务 | 先读 |
|---|---|
| 认证坏了 / 新机器 / token 或 SSH 配置 / gh login | `references/auth.md` |
| 创建、分诊、打标签、指派、关闭 issue | `references/issues.md` |
| 建分支、提交、开 PR、盯 CI、合并 | `references/pr-workflow.md` |
| 把一个 ISSUE 推进到已验证的 PR（完整交付环） | `references/issue-to-pr.md` |
| 审查别人的 PR：diff、行内评论、裁决 | `references/code-review.md` |
| 克隆/创建/fork 仓库、remote、release | `references/repo-management.md` |

配套资产：`scripts/gh-env.sh` + `scripts/git-credential-token.py`（认证助手）、`templates/`（PR 正文、bug 报告、功能请求）、`references/ci-troubleshooting.md`、`references/conventional-commits.md`、`references/github-api-cheatsheet.md`、`references/review-output-template.md`。

## Core discipline（核心纪律，每个工作流都适用）

- 每会话预检一次：`gh auth status`——失败就先走 `references/auth.md`，别的都往后放。
- 优先 `gh` 而非裸 REST；只有当 porcelain 缺该端点时才降到 `gh api`（速查表列了这些端点）。
- 没自己跑过 `gh pr checks` 就别报 CI 绿；没核过 `state,mergedAt` 就别声称已合并。
- 写之前读全上下文：`gh issue view --comments` / `gh pr view --comments`——决策在讨论串里，不在标题里。
- 创建任何东西前先扫重复：`gh pr list --search` / `gh issue list --search`。

## Verification（验证）

- 每个任务的「完成」由它自己的 reference 文件定义。
- 横切面：一切关于远端状态（CI、合并、release、issue 状态）的断言都要有新鲜的 `gh` 读取作后台，绝不凭记忆。
