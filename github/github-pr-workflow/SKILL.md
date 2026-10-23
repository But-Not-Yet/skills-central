---
name: github-pr-workflow
description: "跑 GitHub PR 全流程时使用：分支、提交、开 PR、CI、合并。只要要开 PR、盯 CI 或合代码，就主动加载，即使用户只说「把这个改动提上去」。"
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Pull-Requests, CI/CD, Git, Automation, Merge]
    related_skills: [github-auth, github-code-review]
---

# GitHub Pull Request 工作流

管理 PR 生命周期的完整指南。每节先给 `gh` 写法，再给没有 `gh` 的机器用的 `git` + `curl` 兜底。

## 前置条件

- 已通过 GitHub 认证（见 `github-auth` skill）
- 位于带 GitHub remote 的 git 仓库内

### 快速检测认证

```bash
# Determine which method to use throughout this workflow
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  # Ensure we have a token for API calls
  if [ -z "$GITHUB_TOKEN" ]; then
    if _hermes_env="${HERMES_HOME:-$HOME/.hermes}/.env"; [ -f "$_hermes_env" ] && grep -q "^GITHUB_TOKEN=" "$_hermes_env"; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" "$_hermes_env" | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(uv run python3 "${HERMES_HOME:-$HOME/.hermes}/skills/github/github-auth/scripts/git-credential-token.py")
    fi
  fi
fi
echo "Using: $AUTH"
```

### 从 git remote 提取 Owner/Repo

很多 `curl` 命令需要 `owner/repo`。从 git remote 里提取它：

```bash
# Works for both HTTPS and SSH remote URLs
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
echo "Owner: $OWNER, Repo: $REPO"
```

---

## 1. 创建分支

这部分是纯 `git` — 两种情况完全一样：

```bash
# Make sure you're up to date
git fetch origin
git checkout main && git pull origin main

# Create and switch to a new branch
git checkout -b feat/add-user-authentication
```

分支命名约定：
- `feat/description` — 新功能
- `fix/description` — bug 修复
- `refactor/description` — 代码重构
- `docs/description` — 文档
- `ci/description` — CI/CD 改动

## 2. 提交

用 agent 的文件工具（`write_file`、`patch`）改代码，然后提交：

```bash
# Stage specific files
git add src/auth.py src/models/user.py tests/test_auth.py

# Commit with a conventional commit message
git commit -m "feat: add JWT-based user authentication

- Add login/register endpoints
- Add User model with password hashing
- Add auth middleware for protected routes
- Add unit tests for auth flow"
```

提交信息格式（Conventional Commits）：
```
type(scope): short description

Longer explanation if needed. Wrap at 72 characters.
```

类型：`feat`、`fix`、`refactor`、`docs`、`test`、`ci`、`chore`、`perf`

## 3. 推送并创建 PR

### 推送分支（两种情况一样）

```bash
git push -u origin HEAD
```

### 创建 PR

**用 gh：**

```bash
gh pr create \
  --title "feat: add JWT-based user authentication" \
  --body "## Summary
- Adds login and register API endpoints
- JWT token generation and validation

## Test Plan
- [ ] Unit tests pass

Closes #42"
```

选项：`--draft`、`--reviewer user1,user2`、`--label "enhancement"`、`--base develop`

**用 git + curl：**

```bash
BRANCH=$(git branch --show-current)

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{
    \"title\": \"feat: add JWT-based user authentication\",
    \"body\": \"## Summary\nAdds login and register API endpoints.\n\nCloses #42\",
    \"head\": \"$BRANCH\",
    \"base\": \"main\"
  }"
```

响应 JSON 里含 PR `number` — 存下来给后续命令用。

要建成草稿，在 JSON body 里加 `"draft": true`。

## 4. 监控 CI 状态

### 检查 CI 状态

**用 gh：**

```bash
# One-shot check
gh pr checks

# Watch until all checks finish (polls every 10s)
gh pr checks --watch
```

**用 git + curl：**

```bash
# Get the latest commit SHA on the current branch
SHA=$(git rev-parse HEAD)

# Query the combined status
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Overall: {data['state']}\")
for s in data.get('statuses', []):
    print(f\"  {s['context']}: {s['state']} - {s.get('description', '')}\")"

# Also check GitHub Actions check runs (separate endpoint)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/check-runs \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for cr in data.get('check_runs', []):
    print(f\"  {cr['name']}: {cr['status']} / {cr['conclusion'] or 'pending'}\")"
```

### 轮询到完成（git + curl）

```bash
# Simple polling loop — check every 30 seconds, up to 10 minutes
SHA=$(git rev-parse HEAD)
for i in $(seq 1 20); do
  STATUS=$(curl -s \
    -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['state'])")
  echo "Check $i: $STATUS"
  if [ "$STATUS" = "success" ] || [ "$STATUS" = "failure" ] || [ "$STATUS" = "error" ]; then
    break
  fi
  sleep 30
done
```

## 5. 自动修 CI 失败

CI 失败时，诊断并修复。这个循环两种认证方式都适用。

### 第 1 步：拿到失败详情

**用 gh：**

```bash
# List recent workflow runs on this branch
gh run list --branch $(git branch --show-current) --limit 5

# View failed logs
gh run view <RUN_ID> --log-failed
```

**用 git + curl：**

```bash
BRANCH=$(git branch --show-current)

# List workflow runs on this branch
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?branch=$BRANCH&per_page=5" \
  | python3 -c "
import sys, json
runs = json.load(sys.stdin)['workflow_runs']
for r in runs:
    print(f\"Run {r['id']}: {r['name']} - {r['conclusion'] or r['status']}\")"

# Get failed job logs (download as zip, extract, read)
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs && cat ci-logs/*.txt
```

### 第 2 步：修复并推送

定位问题后，用文件工具（`patch`、`write_file`）修掉：

```bash
git add <fixed_files>
git commit -m "fix: resolve CI failure in <check_name>"
git push
```

### 第 3 步：验证

用上面第 4 节的命令重新检查 CI 状态。

### 自动修复循环模式

被要求自动修 CI 时，按这个循环走：

1. 检查 CI 状态 → 找出失败
2. 读失败日志 → 理解报错
3. 用 `read_file` + `patch`/`write_file` → 修代码
4. `git add . && git commit -m "fix: ..." && git push`
5. 等 CI → 重新检查状态
6. 仍失败就重复（最多 3 次，然后问用户）

## 6. 合并

**用 gh：**

```bash
# Squash merge + delete branch (cleanest for feature branches)
gh pr merge --squash --delete-branch

# Enable auto-merge (merges when all checks pass)
gh pr merge --auto --squash --delete-branch
```

**用 git + curl：**

```bash
PR_NUMBER=<number>

# Merge the PR via API (squash)
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d "{
    \"merge_method\": \"squash\",
    \"commit_title\": \"feat: add user authentication (#$PR_NUMBER)\"
  }"

# Delete the remote branch after merge
BRANCH=$(git branch --show-current)
git push origin --delete $BRANCH

# Switch back to main locally
git checkout main && git pull origin main
git branch -d $BRANCH
```

合并方式：`"merge"`（merge commit）、`"squash"`、`"rebase"`

### 开启自动合并（curl）

```bash
# Auto-merge requires the repo to have it enabled in settings.
# This uses the GraphQL API since REST doesn't support auto-merge.
PR_NODE_ID=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['node_id'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/graphql \
  -d "{\"query\": \"mutation { enablePullRequestAutoMerge(input: {pullRequestId: \\\"$PR_NODE_ID\\\", mergeMethod: SQUASH}) { clientMutationId } }\"}"
```

## 7. 完整工作流示例

```bash
# 1. Start from clean main
git checkout main && git pull origin main

# 2. Branch
git checkout -b fix/login-redirect-bug

# 3. (Agent makes code changes with file tools)

# 4. Commit
git add src/auth/login.py tests/test_login.py
git commit -m "fix: correct redirect URL after login

Preserves the ?next= parameter instead of always redirecting to /dashboard."

# 5. Push
git push -u origin HEAD

# 6. Create PR (picks gh or curl based on what's available)
# ... (see Section 3)

# 7. Monitor CI (see Section 4)

# 8. Merge when green (see Section 6)
```

## 8. 从 fork 给上游供稿（跨仓 PR）

- **先核 PR 开到哪去**：fork 的 main 恰好同步到上游 main 时，Compare 页的提交数/文件数/增删行数两个方向一模一样，极易误读成「这是给我自己的 PR」。两个判别特征：base 下拉必须是 `base repository: <上游owner>/<repo> ← main`；`Allow edits by maintainers` 这个勾**只在上游 PR 创建页出现**，fork 内部对比页没有。这两点没亲眼确认就别点绿按钮。
- **fork 的 main 留着别删**：它是同步落点（`git push fork origin/main:main` 一条命令快进追平）+ Sync-fork 按钮的干净靶子。删掉后默认分支落到工作分支，Sync 按钮会把它变成「Discard commits」陷阱。GitHub 不许删默认分支；要换默认先在 Settings → Branches 改（只能网页点，改默认分支的 API 要 token）。工作分支是 PR 源，main 退居纯镜像。
- **开 PR 前先核基点、追平再开**：主人裁定——maintainer 收 PR 的默认动作是本地合并测试，不该赌 needs-rebase 的 PR 被优待，也不该请 maintainer 当你的 rebase 清洁工。担心方案/测试不全面时，绿按钮先按停：追平 + 测试基线对照过完再开（见下条核验法与 kanban-dispatch 的基线判据）。
- **核上游动静（实测翻车点）**：`git fetch -q origin` 可能静默没更新本地 ref，`git log <基点>..origin/main` 数出 0 新提交、而远端真动了几百笔——单信号会把冲突面判成零。三连核：① `git ls-remote origin refs/heads/main` 是权威现值，不吃本地缓存；② `git merge-tree $(git merge-base <ours> <theirs>) <ours> <theirs>` 干跑冲突面（不动工作树；输出里 `changed in both` = 两边都动的文件、`^<<<<<<< ` 计数 = 真冲突 hunk 数）；③ 对怀疑文件逐个比 `git rev-parse <基点>:<file>` 与 `git rev-parse <新上游>:<file>` 的 blob 哈希。信号互相矛盾时以 ls-remote 与 blob 哈希为准，fetch 指定 sha（`git fetch origin <sha>`）补齐缺失对象再复算。
- **PR 正文照上游模板逐节填**：仓库带模板就原样用它的小节骨架（Title/Summary/What changed/Extra Notes 之类），不改结构只填内容；标题风格先 `git log --oneline` 看 repo 现行惯例再定（供稿仓常是小写 `subsystem: 短句`，未必是通用 Conventional Commits）。正文数字只写本机实测过的真实请求（标硬件、后端、请求规模），账面数（commit/files/增删）用 `git diff <基点>..HEAD --stat` 实算并对平页面显示。
- **Extra Notes 留门缝**：一句「愿意拆小 PR / 改开关名 / 保持 fork」就够，给 maintainer 退路也防止显得护短；Issue 行没有对应 issue 就留空。

### 提 PR 前先测上游接受模式（供稿前置闸）

活跃仓的 PR 洪水会让「直接开 PR」变成抽奖——开 PR 之前先花几分钟量 maintainer 的真实收法，再定走 PR 还是走 issue：

1. **漏斗计数先跑 search API**（一个 count 一个请求，无 token 也可用）：`search/issues?q=repo:<owner>/<repo>+is:pr`（总量）、加 `is:merged` / `is:open` / `is:closed is:unmerged` 各一发。closed-unmerged 占九成 = 裸 PR 会被淹，改走 issue 先行。
2. **全量列表算两个分布**：`/pulls?state=all&per_page=100` 翻页到底（匿名 REST 约 60 请求/时，先 `/rate_limit` 看预算）。一看 `merged_at` 的时间分布——最近若干周合并数为零 = 「直接收 PR」通道已关，账上还在的 merged 全是历史窗口期的。二看高产提交者的 merged 数——交几十笔并零的作者是撒网式投稿（多为各家 agent 批量投），他们的 PR 形态不是范本。
3. **抽样读 closed-unmerged 的评论线程**（`/issues/<n>/comments`，抽 8–10 笔足够）分清真闸与模板：批量关闭模板（「too many to review, closing everything」式）说明队列在清台；逐行号点测试、命令拆 PR 的是真审。**注意另一种收法：「你的改动已进 main、带你的署名」类回复 = 该仓接受的主形态是功能进 main + 致谢署名，决策点在 issue 线程而不是 PR 本身**——这类仓里「PR 没被 merge」不等于工作被拒。
4. **CONTRIBUTING.md 按目标 tag 就地读**：`git show <tag>:CONTRIBUTING.md`（不依赖网络与上游网页）。大功能/架构/默认值改动是否要求 issue 先行拿范围共识、标题是否强制 `[Area]` 前缀、是否一 PR 一问题、被拒提案是否禁止换题重投——这些是硬闸，通常只有「聚焦修复与基准报告」允许直进 PR。
5. **tracker reset / 大版本清台是窗口**：批量关闭模板常附「rebase 到新 main 重新开 PR」的官方邀请，且此刻队列干净——是挂号 issue 与重递 PR 的最佳时点。上游接受状态随季节翻转（收 PR 窗口会开关），每次供稿前重测，别沿用几周前的结论。

## 常用 PR 命令速查

| 操作 | gh | git + curl |
|--------|-----|-----------|
| 列出我的 PR | `gh pr list --author @me` | `curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open"` |
| 查看 PR diff | `gh pr diff` | `git diff main...HEAD` (local) or `curl -H "Accept: application/vnd.github.diff" ...` |
| 添加评论 | `gh pr comment N --body "..."` | `curl -X POST .../issues/N/comments -d '{"body":"..."}'` |
| 请求审查 | `gh pr edit N --add-reviewer user` | `curl -X POST .../pulls/N/requested_reviewers -d '{"reviewers":["user"]}'` |
| 关闭 PR | `gh pr close N` | `curl -X PATCH .../pulls/N -d '{"state":"closed"}'` |
| 检出他人的 PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N && git checkout pr-N` |
