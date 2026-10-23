---
name: git-repo-hygiene
description: "建或管理本地 git 仓库时使用。只要要提交、重建仓库或处理泄漏，就主动加载——提交身份红线：无邮箱、零个人信息。"
version: 1.0.0
author: Nekonya (小喵)
license: MIT
metadata:
  hermes:
    tags: [git, identity, privacy, hygiene]
    related_skills: [engineering-workflow-loop]
---

# 本地 git 仓库卫生（主人红线）

## When to Use

为主人初始化或管理任何本地 git 仓库时：新库首建、提交、打 tag、身份信息泄漏后的重建、收尾做回滚实测。

## 身份红线（最高优先级）

- 提交身份一律 `Independent Researcher`、**不带邮箱**；仓库全历史零个人信息（邮箱、本机用户名、学校、真名、可关联句柄）。信息安全是主人红线——宁重建，勿将就。
- 落地写法（repo-local；全局配置不擅动，别的仓库共用）：
  ```bash
  git config user.name "Independent Researcher"
  git config user.email ""     # 空字符串 → ident 为 `Independent Researcher <>`
  git var GIT_AUTHOR_IDENT     # 验证；应回 `Independent Researcher <> <ts> <tz>`
  ```
- **陷阱（实测）**：email 只是「未设」时，git 会回落全局配置（可能带着私人邮箱）或自动探测 `user@host`；必须把空字符串**显式设进 repo-local** 才切断这条链。`user.useConfigOnly=true` 挡不住全局配置回落——别拿它当保险。
- **annotated tag 也带身份**：`git tag -a` 的 tagger 字段同样署名；建完 `git cat-file tag <tag>` 核验 `tagger` 行为 `Independent Researcher <>`。

## 建库标准流程

1. 提交前扫描：密钥模式（`sk-|ghp_|AKIA|PRIVATE KEY|password=|api_key=`）+ 个人标识串（邮箱前缀、本机用户名、句柄）；严格匹配、命中逐条人工定性——宽松模式会把文档/模板/代码里的**引用**算成命中（「提到过」≠「泄漏过」），假命中要在结论里写明。
2. `git init -b main` → 设身份 → 写 `.gitignore`（`__pycache__/`、`*.py[cod]` 等）→ `git add -A` → 审 `git status --short` 符合预期 → 提交。
3. 首提交后核验身份三处：`git log --format='%an <%ae>'`；`git cat-file commit HEAD | head`（author + committer 两行）；tag 的 tagger 行。
4. 全历史唯一性：`git log --all --format='%an|%ae|%cn|%ce' | sort -u`——只应出现目标身份。
5. 扫描结论分清「跟踪面」（`git grep` 必须 0 命中）与「未跟踪产物」（pyc 带本机路径串、被 .gitignore 排除即不入库）。
6. 仓库内容也过红线：真实账号/仓库 URL 未确定就不写——用 RFC 2606 占位（`https://example.com/...`）+ 注释「发布前替换」。

## 已泄漏 = 重建，不是 amend

- 本地未推送仓库里出现个人信息：`rm -rf .git` → 重走建库流程 → 重打 tag（本地单提交仓库直接重建最干净，旧历史整体作废）。
- 重建后验证：旧哈希不可达（`git cat-file -t <旧哈希>` 应报错）+ 全目录重扫 0 命中 + reflog 只有新记录。
- 汇报时讲清「从未推送、不存在对外泄漏」，但行为按「已泄漏」处理——工具链留痕零容忍。

## 提交与回滚纪律

- 主人偏好：本地仓库修复直提交 `main`、不搞分支仪式；git 的用途 = 留历史。
- 分批提交按逻辑单元（功能一笔、文档/meta 一笔）；提交信息头部一行 + 正文条目。
- **回滚必须实测**：`git revert --no-commit HEAD`（或提交范围）干跑 → 看 `git diff --cached --stat` 合理 → `git reset --hard -q` 还原 → 核验工作树干净、内容完好。没干跑过的回滚不算存在。
