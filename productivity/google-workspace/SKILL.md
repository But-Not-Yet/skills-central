---
name: google-workspace
description: "用 gws CLI 或 Python 操作 Gmail、Calendar、Drive、Docs、Sheets 时使用。只要涉及收发邮件、日程、云盘文件、通讯录或 Google 表格/文档，就主动加载，即使用户只是说「看下我邮箱」。"
version: 1.1.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token（由设置脚本创建）
  - path: google_client_secret.json
    description: Google OAuth2 client 凭据（从 Google Cloud Console 下载）
metadata:
  hermes:
    tags: [Google, Gmail, Calendar, Drive, Sheets, Docs, Contacts, Email, OAuth]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [himalaya]
---

# Google Workspace

Gmail、Calendar、Drive、Contacts、Sheets 与 Docs——经由 Hermes 托管的 OAuth 和一个轻量 CLI 包装器。安装了 `gws` 时，本 skill 用它作为执行后端以获得更广的 Google Workspace 覆盖。否则回退到内置的 Python 客户端实现。

## 参考

- `references/gmail-search-syntax.md`——Gmail 搜索运算符（is:unread、from:、newer_than: 等）

## 脚本

- `scripts/setup.py`——OAuth2 设置（运行一次以授权）
- `scripts/google_api.py`——兼容性包装 CLI。可用时优先用 `gws` 执行操作，同时保留 Hermes 既有的 JSON 输出契约。

## 首次设置

设置完全非交互——你一步步驱动它，因此在
CLI、Telegram、Discord 或任何平台上都能用。

先定义一个简写：

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
```

### 第 0 步：检查是否已设置好

```bash
$GSETUP --check
```

若打印 `AUTHENTICATED`，跳到「用法」——设置已完成。

### 第 1 步：分诊——问用户需要什么

开始 OAuth 设置前，问用户*两个*问题：

**问题 1：「你需要哪些 Google 服务？只要邮箱，还是也要
Calendar/Drive/Sheets/Docs？」**

- **只要邮箱** → 他们完全不需要本 skill。改用 `himalaya` skill
  ——它用一个 Gmail App Password（设置 → 安全性 → 应用
  密码）即可工作，2 分钟就能设好。不需要 Google Cloud 项目。
  加载 himalaya skill 并按其设置说明操作。

- **邮箱 + Calendar** → 继续用本 skill，但鉴权时用
  `--services email,calendar`，让同意屏幕只请求
  他们真正需要的 scope。

- **只要 Calendar/Drive/Sheets/Docs** → 继续用本 skill，并使用
  更窄的 `--services` 集，如 `calendar,drive,sheets,docs`。

- **完整 Workspace 访问** → 继续用本 skill，并使用默认的
  `all` 服务集。

**问题 2：「你的 Google 账号是否启用了 Advanced Protection（登录需要硬件
安全密钥）？如果不确定，多半没有
——这是一项需要你主动登记的功能。」**

- **否 / 不确定** → 正常设置。继续往下。
- **是** → 他们的 Workspace 管理员必须把该 OAuth client ID 加入组织的
  允许应用列表，第 4 步才能工作。事先告知他们。

### 第 2 步：创建 OAuth 凭据（一次性，约 5 分钟）

告诉用户：

> 你需要一个 Google Cloud OAuth client。这是一次性设置：
>
> 1. 创建或选择一个项目：
>    https://console.cloud.google.com/projectselector2/home/dashboard
> 2. 从 API Library 启用所需的 API：
>    https://console.cloud.google.com/apis/library
>    启用：Gmail API, Google Calendar API, Google Drive API,
>    Google Sheets API, Google Docs API, People API
> 3. 在这里创建 OAuth client：
>    https://console.cloud.google.com/apis/credentials
>    Credentials → Create Credentials → OAuth 2.0 Client ID
> 4. Application type: "Desktop app" → Create
> 5. 若应用仍在 Testing，在此把用户的 Google 账号加为测试用户：
>    https://console.cloud.google.com/auth/audience
>    Audience → Test users → Add users
> 6. 下载 JSON 文件并告诉我文件路径
>
> 重要 Hermes CLI 提示：若文件路径以 `/` 开头，不要在 CLI 里把裸路径作为单独一条消息发送。因为它可能被误认为斜杠命令。改在一整句里发，例如：
> `The JSON file path is: /home/user/Downloads/client_secret_....json`

他们给出路径后：

```bash
$GSETUP --client-secret /path/to/client_secret.json
```

若他们粘贴的是原始的 client ID / client secret 值而非文件路径，
你自己替他们写一个合法的 Desktop OAuth JSON 文件，存到某个
明确的位置（例如 `~/Downloads/hermes-google-client-secret.json`），再对该文件运行
`--client-secret`。

### 第 3 步：获取授权 URL

用第 1 步选定的服务集。示例：

```bash
$GSETUP --auth-url --services email,calendar --format json
$GSETUP --auth-url --services calendar,drive,sheets,docs --format json
$GSETUP --auth-url --services all --format json
```

这会返回带 `auth_url` 字段的 JSON，并把确切 URL 存到
`~/.hermes/google_oauth_last_url.txt`。

本步的代理规则：
- 提取 `auth_url` 字段，把那个确切 URL 作为单独一行发给用户。
- 告诉用户浏览器在批准后很可能在 `http://localhost:1` 失败，这是预期内的。
- 让他们从浏览器地址栏复制*整段*重定向后的 URL。
- 若用户遇到 `Error 403: access_denied`，直接把他们引到 `https://console.cloud.google.com/auth/audience` 把自己加为测试用户。

### 第 4 步：交换 code

用户会回贴一个形如 `http://localhost:1/?code=4/0A...&scope=...` 的 URL，
或只是 code 字符串。两者都行。`--auth-url` 步骤会在本地存一个临时的
待处理 OAuth 会话，让 `--auth-code` 之后能完成 PKCE 交换，
即使在无头系统上：

```bash
$GSETUP --auth-code "THE_URL_OR_CODE_THE_USER_PASTED" --format json
```

若 `--auth-code` 因 code 过期、已被使用，或来自
较早的浏览器标签页而失败，它现在会返回一个新的 `fresh_auth_url`。这种情况下，
立即把新 URL 发给用户，让他们只用最新的
浏览器重定向重试。

### 第 5 步：核验

```bash
$GSETUP --check
```

应打印 `AUTHENTICATED`。设置完成——从今往后 token 自动刷新。

### 注意

- token 存在 `~/.hermes/google_token.json` 并自动刷新。
- 待处理的 OAuth 会话状态/verifier 临时存在 `~/.hermes/google_oauth_pending.json`，直到交换完成。
- 若安装了 `gws`，`google_api.py` 会让它指向同一个 `~/.hermes/google_token.json` 凭据文件。用户无需另跑一套 `gws auth login` 流程。
- 撤销：`$GSETUP --revoke`

## 用法

所有命令都走那个 API 脚本。设 `GAPI` 作简写：

```bash
GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"
```

### Gmail

```bash
# Search (returns JSON array with id, from, subject, date, snippet)
$GAPI gmail search "is:unread" --max 10
$GAPI gmail search "from:boss@company.com newer_than:1d"
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"

# Read full message (returns JSON with body text)
$GAPI gmail get MESSAGE_ID

# Send
$GAPI gmail send --to user@example.com --subject "Hello" --body "Message text"
$GAPI gmail send --to user@example.com --subject "Report" --body "<h1>Q4</h1><p>Details...</p>" --html
$GAPI gmail send --to user@example.com --subject "Hello" --from '"Research Agent" <user@example.com>' --body "Message text"

# Reply (automatically threads and sets In-Reply-To)
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."
$GAPI gmail reply MESSAGE_ID --from '"Support Bot" <user@example.com>' --body "Thanks"

# Labels
$GAPI gmail labels
$GAPI gmail modify MESSAGE_ID --add-labels LABEL_ID
$GAPI gmail modify MESSAGE_ID --remove-labels UNREAD
```

### Calendar

```bash
# List events (defaults to next 7 days)
$GAPI calendar list
$GAPI calendar list --start 2026-03-01T00:00:00Z --end 2026-03-07T23:59:59Z

# Create event (ISO 8601 with timezone required)
$GAPI calendar create --summary "Team Standup" --start 2026-03-01T10:00:00-06:00 --end 2026-03-01T10:30:00-06:00
$GAPI calendar create --summary "Lunch" --start 2026-03-01T12:00:00Z --end 2026-03-01T13:00:00Z --location "Cafe"
$GAPI calendar create --summary "Review" --start 2026-03-01T14:00:00Z --end 2026-03-01T15:00:00Z --attendees "alice@co.com,bob@co.com"

# Delete event
$GAPI calendar delete EVENT_ID
```

### Drive

```bash
# Search existing files
$GAPI drive search "quarterly report" --max 10
$GAPI drive search "mimeType='application/pdf'" --raw-query --max 5

# Get metadata for a single file
$GAPI drive get FILE_ID

# Upload a local file (auto-detects MIME type)
$GAPI drive upload /path/to/report.pdf
$GAPI drive upload /path/to/image.png --name "Logo.png" --parent FOLDER_ID

# Download (binary files download as-is; Google-native files export to a
# sensible default — Docs→pdf, Sheets→csv, Slides→pdf, Drawings→png)
$GAPI drive download FILE_ID
$GAPI drive download DOC_ID --output ~/doc.pdf
$GAPI drive download DOC_ID --export-mime text/plain --output ~/doc.txt

# Create a folder
$GAPI drive create-folder "Reports"
$GAPI drive create-folder "Q4" --parent FOLDER_ID

# Share
$GAPI drive share FILE_ID --email alice@example.com --role reader
$GAPI drive share FILE_ID --email alice@example.com --role writer --notify
$GAPI drive share FILE_ID --type anyone --role reader        # anyone with link
$GAPI drive share FILE_ID --type domain --domain example.com --role reader

# Delete — defaults to trash (reversible). Use --permanent to skip the trash.
$GAPI drive delete FILE_ID
$GAPI drive delete FILE_ID --permanent
```

### Contacts

```bash
$GAPI contacts list --max 20
```

### Sheets

```bash
# Create a new spreadsheet
$GAPI sheets create --title "Q4 Budget"
$GAPI sheets create --title "Inventory" --sheet-name "Stock"

# Read
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"

# Write
$GAPI sheets update SHEET_ID "Sheet1!A1:B2" --values '[["Name","Score"],["Alice","95"]]'

# Append rows
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[["new","row","data"]]'
```

### Docs

```bash
# Read
$GAPI docs get DOC_ID

# Create a new Doc (optionally seeded with body text)
$GAPI docs create --title "Meeting Notes"
$GAPI docs create --title "Draft" --body "First paragraph..."

# Append text to the end of an existing Doc
$GAPI docs append DOC_ID --text "Additional content to append"
```

## 输出格式

所有命令返回 JSON。用 `jq` 解析或直接读。关键字段：

- **Gmail search**: `[{id, threadId, from, to, subject, date, snippet, labels}]`
- **Gmail get**: `{id, threadId, from, to, subject, date, labels, body}`
- **Gmail send/reply**: `{status: "sent", id, threadId}`
- **Calendar list**: `[{id, summary, start, end, location, description, htmlLink}]`
- **Calendar create**: `{status: "created", id, summary, htmlLink}`
- **Drive search**: `[{id, name, mimeType, modifiedTime, webViewLink}]`
- **Drive get**: `{id, name, mimeType, modifiedTime, size, webViewLink, parents, owners}`
- **Drive upload**: `{status: "uploaded", id, name, mimeType, webViewLink}`
- **Drive download**: `{status: "downloaded", id, name, path, mimeType}`
- **Drive create-folder**: `{status: "created", id, name, webViewLink}`
- **Drive share**: `{status: "shared", permissionId, fileId, role, type}`
- **Drive delete**: `{status: "trashed" | "deleted", fileId, permanent}`
- **Contacts list**: `[{name, emails: [...], phones: [...]}]`
- **Sheets get**: `[[cell, cell, ...], ...]`
- **Sheets create**: `{status: "created", spreadsheetId, title, spreadsheetUrl}`
- **Docs create**: `{status: "created", documentId, title, url}`
- **Docs append**: `{status: "appended", documentId, inserted_at, characters}`

## 规则

1. **未经用户确认，绝不发送邮件、创建/删除日历事件、删除 Drive 文件、共享文件，或修改 Docs/Sheets。** 展示将要做的事（收件人、文件 ID、内容、共享角色）并请求批准。对 `drive delete`，优先用默认的回收站（可逆）而非 `--permanent`。
2. **首次使用前检查认证**——运行 `setup.py --check`。若失败，引导用户完成设置。
3. **复杂查询用 Gmail 搜索语法参考**——用 `skill_view("google-workspace", file_path="references/gmail-search-syntax.md")` 加载它。
4. **日程时间必须带时区**——始终用带偏移的 ISO 8601（如 `2026-03-01T10:00:00-06:00`）或 UTC（`Z`）。
5. **尊重速率限制**——避免连珠炮式的顺序 API 调用。能批量读就批量读。

## 排查

| 问题 | 修复 |
|---------|-----|
| `NOT_AUTHENTICATED` | 运行上面的第 2-5 步设置 |
| `REFRESH_FAILED` | token 被撤销或过期——重做第 3-5 步 |
| `HttpError 403: Insufficient Permission` | 缺 API scope——`$GSETUP --revoke` 后重做第 3-5 步 |
| `AUTHENTICATED (partial)` 或 "Token missing scopes" | 新的写入能力（Drive 写/删、Docs 创建/编辑）需要重新授权。`$GSETUP --revoke` 后重做第 3-5 步以授予升级后的 scope。 |
| `HttpError 403: Access Not Configured` | API 未启用——用户需在 Google Cloud Console 启用它 |
| `ModuleNotFoundError` | Run `$GSETUP --install-deps` |
| Advanced Protection 阻止鉴权 | Workspace 管理员必须把该 OAuth client ID 加入允许列表 |

## 撤销访问

```bash
$GSETUP --revoke
```
