---
name: himalaya
description: "用 Himalaya CLI 在终端收发邮件时使用（IMAP/SMTP）。只要要在命令行读信、发信或管邮箱，就主动加载，即使用户只说「看看我的邮件」。不用于 Gmail API（用 google-workspace）。"
version: 1.1.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, CLI, Communication]
    homepage: https://github.com/pimalaya/himalaya
prerequisites:
  commands: [himalaya]
---

# Himalaya Email CLI

Himalaya 是一个 CLI 邮件客户端，让你从终端经 IMAP、SMTP、Notmuch 或 Sendmail 后端管理邮件。

本技能与 Hermes 的邮件网关适配器是两回事。网关适配器让别人给 agent 发邮件，用的是 Hermes 内置的 IMAP/SMTP 适配器；本技能让 agent 用终端工具操作邮箱，依赖外部的 `himalaya` CLI。

## 参考件

- `references/configuration.md`（配置文件设置 + IMAP/SMTP 认证）
- `references/message-composition.md`（撰写邮件的 MML 语法）

## 前置条件

1. 已安装 Himalaya CLI（用 `himalaya --version` 验证）
2. 配置文件位于 `~/.config/himalaya/config.toml`
3. 已配置 IMAP/SMTP 凭据（密码须安全存放）

### 安装

```bash
# Pre-built binary (Linux/macOS — recommended)
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh

# macOS via Homebrew
brew install himalaya

# Or via cargo (any platform with Rust)
cargo install himalaya --locked
```

## 配置

跑交互式向导来建账号：

```bash
himalaya account configure
```

或手动创建 `~/.config/himalaya/config.toml`：

```toml
[accounts.personal]
email = "you@example.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@example.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"  # or use keyring

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@example.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"

# Folder aliases (himalaya v1.2.0+ syntax). Required whenever the
# server's folder names don't match himalaya's canonical names
# (inbox/sent/drafts/trash). Gmail is the common case — see
# `references/configuration.md` for the `[Gmail]/Sent Mail` mapping.
folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Trash"
```

> **别名语法的坑。** v1.2.0 之前的文档用的是
> `[accounts.NAME.folder.alias]` 子段（单数 `alias`）。
> v1.2.0 会静默忽略这种写法——TOML 能解析通过，但别名解析器从不读它，
> 于是每次查找都落到标准名上。在 Gmail 上这意味着 SMTP 投递成功**之后**
> 存入「已发送」失败，`himalaya message send` 以非零码退出。
> 任何按该退出码重试的调用方（agent、脚本、用户）都会把整封邮件**连 SMTP
> 一起重发**，给收件人造成重复邮件。务必用 `folder.aliases.X`（复数、
> 点号键、直接放在 `[accounts.NAME]` 下）。

## 与 Hermes 集成的注意事项

- **读、列、搜、移动、删除**都能直接通过 terminal 工具完成
- **撰写/回复/转发**——推荐用管道输入（`cat << EOF | himalaya template send`），可靠性最好。交互式 `$EDITOR` 模式可用 `pty=true` + 后台 + process 工具，但需要预先知道编辑器及其命令
- 用 `--output json` 拿结构化输出，程序化解析更容易
- `himalaya account configure` 向导需要交互输入——用 PTY 模式：`terminal(command="himalaya account configure", pty=true)`

## 常用操作

### 列出文件夹

```bash
himalaya folder list
```

### 列出邮件

列出 INBOX（默认）里的邮件：

```bash
himalaya envelope list
```

列出指定文件夹里的邮件：

```bash
himalaya envelope list --folder "Sent"
```

带分页列出：

```bash
himalaya envelope list --page 1 --page-size 20
```

### 搜索邮件

```bash
himalaya envelope list from john@example.com subject meeting
```

### 读邮件

按 ID 读邮件（显示纯文本）：

```bash
himalaya message read 42
```

导出原始 MIME：

```bash
himalaya message export 42 --full
```

### 回复邮件

要从 Hermes 里非交互地回复，先读原信、拟好回复、再管道送入：

```bash
# Get the reply template, edit it, and send
himalaya template reply 42 | sed 's/^$/\nYour reply text here\n/' | himalaya template send
```

或手工构造回复：

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id>

Your reply here.
EOF
```

回复全部（交互式——需要 `$EDITOR`，改用上面的模板法）：

```bash
himalaya message reply 42 --all
```

### 转发邮件

```bash
# Get forward template and pipe with modifications
himalaya template forward 42 | sed 's/^To:.*/To: newrecipient@example.com/' | himalaya template send
```

### 写新邮件

**非交互式（从 Hermes 里用这个）**——把邮件经 stdin 管道送入：

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya!
EOF
```

或用 headers 参数：

```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

注意：`himalaya message write` 不带管道输入时会打开 `$EDITOR`。这在 `pty=true` + 后台模式下可行，但管道更简单也更可靠。

### 移动 / 复制邮件

移到文件夹（目标文件夹在前，邮件 ID 在后）：

```bash
himalaya message move "Archive" 42
```

复制到文件夹（目标文件夹在前，邮件 ID 在后）：

```bash
himalaya message copy "Important" 42
```

### 删除邮件

```bash
himalaya message delete 42
```

### 管理标记

加标记：

```bash
himalaya flag add 42 --flag seen
```

去标记：

```bash
himalaya flag remove 42 --flag seen
```

## 多账号

列出账号：

```bash
himalaya account list
```

用指定账号：

```bash
himalaya --account work envelope list
```

## 附件

从邮件里保存附件：

```bash
himalaya attachment download 42
```

存到指定目录：

```bash
himalaya attachment download 42 --downloads-dir ~/Downloads
```

## 输出格式

多数命令支持 `--output` 拿结构化输出：

```bash
himalaya envelope list --output json
himalaya envelope list --output plain
```

## 调试

打开调试日志：

```bash
RUST_LOG=debug himalaya envelope list
```

带 backtrace 的完整追踪：

```bash
RUST_LOG=trace RUST_BACKTRACE=1 himalaya envelope list
```

## 提示

- 用 `himalaya --help` 或 `himalaya <command> --help` 查详细用法。
- 邮件 ID 相对于当前文件夹；切换文件夹后要重新列一次。
- 要写带附件的富文本邮件，用 MML 语法（见 `references/message-composition.md`）。
- 密码用 `pass`、系统 keyring，或任何能输出密码的命令安全存放。
