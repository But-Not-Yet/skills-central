---
name: github-auth
description: "配置 GitHub 认证时使用：HTTPS token、SSH key、gh CLI 登录。只要要让 agent 能操作 GitHub 仓库、PR、issue 或 CI，就主动加载，即使用户没明说「先登录」。"
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Authentication, Git, gh-cli, SSH, Setup]
    related_skills: [github-pr-workflow, github-code-review, github-issues, github-repo-management]
---

# GitHub 认证配置

本 skill 配置认证，让 agent 能操作 GitHub 仓库、PR、issue 与 CI。它覆盖两条路径：

- **`git`（始终可用）** — 使用 HTTPS personal access token 或 SSH key
- **`gh` CLI（若已安装）** — 更丰富的 GitHub API 访问，认证流程更简单

## 检测流程

当用户要你操作 GitHub 时，先跑这段检查：

```bash
# Check what's available
git --version
gh --version 2>/dev/null || echo "gh not installed"

# Check if already authenticated
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no git credential helper"
```

**决策树：**
1. 若 `gh auth status` 显示已认证 → 没问题，全程用 `gh`
2. 若 `gh` 已安装但未认证 → 用下面的「gh auth」方法
3. 若 `gh` 未安装 → 用下面的「git-only」方法（无需 sudo）

---

## 方法 1：仅用 git 认证（不用 gh、不用 sudo）

任何装了 `git` 的机器都能用，无需 root 权限。

### 方案 A：HTTPS + Personal Access Token（推荐）

这是最通用的方法 — 处处可用，无需 SSH 配置。

**第 1 步：创建 personal access token**

让用户访问：**https://github.com/settings/tokens**

- 点「Generate new token (classic)」
- 起个名字，如 "hermes-agent"
- 勾选 scopes：
  - `repo`（完整仓库访问 — 读、写、push、PR）
  - `workflow`（触发与管理 GitHub Actions）
  - `read:org`（若处理组织仓库）
- 设置过期时间（90 天是合适的默认值）
- 复制 token — 之后不会再显示

**第 2 步：配置 git 保存 token**

```bash
# Set up the credential helper to cache credentials
# "store" saves to ~/.git-credentials in plaintext (simple, persistent)
git config --global credential.helper store

# Now do a test operation that triggers auth — git will prompt for credentials
# Username: <their-github-username>
# Password: <paste the personal access token, NOT their GitHub password>
git ls-remote https://github.com/<their-username>/<any-repo>.git
```

首次输入凭证后即被保存，之后所有操作复用。

**替代方案：cache helper（凭证存内存中，会过期）**

```bash
# Cache in memory for 8 hours (28800 seconds) instead of saving to disk
git config --global credential.helper 'cache --timeout=28800'
```

**替代方案：把 token 直接写进 remote URL（按仓库）**

```bash
# Embed token in the remote URL (avoids credential prompts entirely)
git remote set-url origin https://<username>:<token>@github.com/<owner>/<repo>.git
```

**第 3 步：配置 git 身份**

```bash
# Required for commits — set name and email
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

**第 4 步：验证**

```bash
# Test push access (this should work without any prompts now)
git ls-remote https://github.com/<their-username>/<any-repo>.git

# Verify identity
git config --global user.name
git config --global user.email
```

### 方案 B：SSH key 认证

适合偏好 SSH 或已配好 key 的用户。

**第 1 步：检查已有 SSH key**

```bash
ls -la ~/.ssh/id_*.pub 2>/dev/null || echo "No SSH keys found"
```

**第 2 步：按需生成 key**

```bash
# Generate an ed25519 key (modern, secure, fast)
ssh-keygen -t ed25519 -C "their-email@example.com" -f ~/.ssh/id_ed25519 -N ""

# Display the public key for them to add to GitHub
cat ~/.ssh/id_ed25519.pub
```

让用户在 **https://github.com/settings/keys** 添加公钥
- 点「New SSH key」
- 粘贴公钥内容
- 起个标题，如 "hermes-agent-<machine-name>"

**第 3 步：测试连接**

```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

**第 4 步：配置 git 用 SSH 访问 GitHub**

```bash
# Rewrite HTTPS GitHub URLs to SSH automatically
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

**第 5 步：配置 git 身份**

```bash
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

---

## 方法 2：gh CLI 认证

若 `gh` 已安装，它一步就能同时搞定 API 访问与 git 凭证。

### 交互式浏览器登录（桌面）

```bash
gh auth login
# Select: GitHub.com
# Select: HTTPS
# Authenticate via browser
```

### 基于 token 的登录（无头 / SSH 服务器）

```bash
echo "<THEIR_TOKEN>" | gh auth login --with-token

# Set up git credentials through gh
gh auth setup-git
```

### 验证

```bash
gh auth status
```

---

## 无 gh 时使用 GitHub API

`gh` 不可用时，仍可用 `curl` 搭配 personal access token 访问完整的 GitHub API。其他 GitHub skill 的兜底实现就是这么做的。

### 为 API 调用设置 token

```bash
# Option 1: Export as env var (preferred — keeps it out of commands)
export GITHUB_TOKEN="<token>"

# Then use in curl calls:
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

### 从 git 凭证中提取 token

若 git 凭证已配置好（通过 credential.helper store），可以提取出 token：

```bash
# Read from git credential store
uv run python3 "${HERMES_HOME:-$HOME/.hermes}/skills/github/github-auth/scripts/git-credential-token.py"
```

### 辅助：检测认证方式

在任何 GitHub 工作流开头套用这个模式：

```bash
# Try gh first, fall back to git + curl
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  echo "AUTH_METHOD=gh"
elif [ -n "$GITHUB_TOKEN" ]; then
  echo "AUTH_METHOD=curl"
elif _hermes_env="${HERMES_HOME:-$HOME/.hermes}/.env"; [ -f "$_hermes_env" ] && grep -q "^GITHUB_TOKEN=" "$_hermes_env"; then
  export GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" "$_hermes_env" | head -1 | cut -d= -f2 | tr -d '\n\r')
  echo "AUTH_METHOD=curl"
elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
  export GITHUB_TOKEN=$(uv run python3 "${HERMES_HOME:-$HOME/.hermes}/skills/github/github-auth/scripts/git-credential-token.py")
  echo "AUTH_METHOD=curl"
else
  echo "AUTH_METHOD=none"
  echo "Need to set up authentication first"
fi
```

---

## 故障排查

| 问题 | 解决 |
|---------|----------|
| `git push` 要求输入密码 | GitHub 已停用密码认证。用 personal access token 当密码，或改用 SSH |
| `remote: Permission to X denied` | token 可能缺少 `repo` scope — 用正确的 scopes 重新生成 |
| `fatal: Authentication failed` | 缓存的凭证可能已失效 — 跑 `git credential reject` 后重新认证 |
| `ssh: connect to host github.com port 22: Connection refused` | 试试走 HTTPS 端口的 SSH：在 `~/.ssh/config` 中为 `Host github.com` 加 `Port 443` 与 `Hostname ssh.github.com` |
| 凭证无法持久化 | 检查 `git config --global credential.helper` — 必须是 `store` 或 `cache` |
| 多个 GitHub 账号 | 用 SSH，在 `~/.ssh/config` 里为不同 host alias 配不同 key，或用按仓库的凭证 URL |
| `gh: command not found` 且无 sudo | 用上面的 git-only 方法 1 — 无需安装 |
