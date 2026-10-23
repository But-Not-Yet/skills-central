---
name: notion
description: "用 Notion API 或 ntn CLI 操作页面、数据库与 Workers 时使用。只要涉及 Notion 页面读写、数据库查询、markdown 端点、文件上传或其 CLI/CDN、Workers，就主动加载。即使用户只是提到某个 Notion 页面。"
version: 2.0.0
author: community
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [NOTION_API_KEY]
metadata:
  hermes:
    tags: [Notion, Productivity, Notes, Database, API, CLI, Workers]
    homepage: https://developers.notion.com
---

# Notion

与 Notion 交互有两条路。同一个集成 token 对两者都适用——按可用性来选。

◆ **`ntn` CLI**——Notion 官方 CLI。语法更短、文件上传一行搞定、Workers 必需。截至 2026 年 5 月仅 macOS + Linux（Windows 支持「即将推出」）。**已安装时默认用它。**
◆ **HTTP + curl**——到处能用，包括 Windows。`ntn` 未安装时的**默认兜底**。

## 设置

### 1. 获取集成 token（两条路都需要）

1. 在 https://notion.so/my-integrations 创建一个集成
2. 复制 API key（以 `ntn_` 或 `secret_` 开头）
3. 存入 `${HERMES_HOME:-~/.hermes}/.env`：
   ```
   NOTION_API_KEY=ntn_your_key_here
   ```
4. 在 Notion 里**把目标页面/数据库共享给该集成**：页面菜单 `...` → `Connect to` → 你的集成名。不这么做，API 对该页面会返回 404，即使它存在。

### 2. 安装 `ntn`（macOS / Linux 上的首选路径）

```bash
# Recommended
curl -fsSL https://ntn.dev | bash

# Or via npm (needs Node 22+, npm 10+)
npm install --global ntn

ntn --version    # verify
```

**跳过 `ntn login`——改用集成 token。** 这可无头运行，无需浏览器：
```bash
export NOTION_API_TOKEN=$NOTION_API_KEY      # ntn reads NOTION_API_TOKEN
export NOTION_KEYRING=0                       # don't try to use the OS keychain
```

把这些 export 加到你的 shell profile（或 `${HERMES_HOME:-~/.hermes}/.env`），让每个会话都继承它们。

### 3. 运行时选择路径

```bash
if command -v ntn >/dev/null 2>&1; then
  # use ntn
else
  # fall back to curl
fi
```

Windows 用户：在原生 `ntn` 发布前完全跳过第 2 步——路径 B 完全够用。若现在就想要 CLI 的顺手，在 WSL2 里安装 `ntn`。

## API 基础

所有 HTTP 请求都必须带 `Notion-Version: 2025-09-03`。`ntn` 会替你处理。在这个版本里，用户口中的「databases」在 API 里叫 **data sources**。

## 路径 A — `ntn` CLI（首选，macOS / Linux）

### 原始 API 调用（curl 的简写）
```bash
ntn api v1/users                                  # GET
ntn api v1/pages parent[page_id]=abc123 \         # POST with inline body
  properties[title][0][text][content]="Notes"
ntn api v1/pages/abc123 -X PATCH archived:=true   # PATCH; := is non-string (bool/num/null)
```

语法说明：
- `key=value`——字符串字段
- `key[nested]=value`——嵌套对象字段
- `key:=value`——带类型的赋值（布尔、数字、null、数组）

### 搜索
```bash
ntn api v1/search query="page title"
```

### 读取页面元数据
```bash
ntn api v1/pages/{page_id}
```

### 以 Markdown 读取页面（对代理友好）
```bash
ntn api v1/pages/{page_id}/markdown
```

### 以 blocks 读取页面内容
```bash
ntn api v1/blocks/{page_id}/children
```

### 从 Markdown 创建页面
```bash
ntn api v1/pages \
  parent[page_id]=xxx \
  properties[title][0][text][content]="Notes from meeting" \
  markdown="# Agenda

- Q3 roadmap
- Hiring"
```

### 用 Markdown patch 页面
```bash
ntn api v1/pages/{page_id}/markdown -X PATCH \
  markdown="## Update

Shipped the prototype."
```

### 查询数据库（data source）
```bash
ntn api v1/data_sources/{data_source_id}/query -X POST \
  filter[property]=Status filter[select][equals]=Active
```

对带 `sorts`、多个筛选子句或复合逻辑的复杂查询，把 JSON 管道传入：
```bash
echo '{"filter": {"property": "Status", "select": {"equals": "Active"}}, "sorts": [{"property": "Date", "direction": "descending"}]}' | \
  ntn api v1/data_sources/{data_source_id}/query -X POST --json -
```

### 文件上传（一行命令——CLI 最大的胜利）
```bash
ntn files create < photo.png
ntn files create --external-url https://example.com/photo.png
ntn files list
```

对比三步 HTTP 流程（创建 upload → PUT 字节 → 引用）。

### 有用的环境变量
| 变量 | 作用 |
|---|---|
| `NOTION_API_TOKEN` | 认证 token（覆盖 keychain）——设成你的集成 token |
| `NOTION_KEYRING=0` | 用基于文件的凭据 `~/.config/notion/auth.json` 取代 OS keychain |
| `NOTION_WORKSPACE_ID` | 跳过工作区选择提示 |

## 路径 B — HTTP + curl（跨平台，Windows 默认）

所有请求共用这个模式：

```bash
curl -s -X GET "https://api.notion.com/v1/..." \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json"
```

在 Windows 上，Windows 10+ 自带的 `curl` 直接可用。PowerShell 用户也可以用 `Invoke-RestMethod`。

### 搜索
```bash
curl -s -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"query": "page title"}'
```

### 读取页面元数据
```bash
curl -s "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### 以 Markdown 读取页面（对代理友好）

比 block JSON 更容易喂给模型。

```bash
curl -s "https://api.notion.com/v1/pages/{page_id}/markdown" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### 以 blocks 读取页面内容（需要结构时）
```bash
curl -s "https://api.notion.com/v1/blocks/{page_id}/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### 从 Markdown 创建页面

`POST /v1/pages` 接受 `markdown` 正文参数。

```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "xxx"},
    "properties": {"title": [{"text": {"content": "Notes from meeting"}}]},
    "markdown": "# Agenda\n\n- Q3 roadmap\n- Hiring\n\n## Decisions\n- Ship MVP Friday"
  }'
```

### 用 Markdown patch 页面
```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}/markdown" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"markdown": "## Update\n\nShipped the prototype."}'
```

### 在数据库里创建页面（带类型属性）
```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"database_id": "xxx"},
    "properties": {
      "Name": {"title": [{"text": {"content": "New Item"}}]},
      "Status": {"select": {"name": "Todo"}}
    }
  }'
```

### 查询数据库（data source）
```bash
curl -s -X POST "https://api.notion.com/v1/data_sources/{data_source_id}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {"property": "Status", "select": {"equals": "Active"}},
    "sorts": [{"property": "Date", "direction": "descending"}]
  }'
```

### 创建数据库
```bash
curl -s -X POST "https://api.notion.com/v1/data_sources" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "xxx"},
    "title": [{"text": {"content": "My Database"}}],
    "properties": {
      "Name": {"title": {}},
      "Status": {"select": {"options": [{"name": "Todo"}, {"name": "Done"}]}},
      "Date": {"date": {}}
    }
  }'
```

### 更新页面属性
```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"properties": {"Status": {"select": {"name": "Done"}}}}'
```

### 向页面追加 blocks
```bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/{page_id}/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "children": [
      {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Hello from Hermes!"}}]}}
    ]
  }'
```

### 文件上传（三步流程）
```bash
# 1. Create upload
curl -s -X POST "https://api.notion.com/v1/file_uploads" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"filename": "photo.png", "content_type": "image/png"}'

# 2. PUT bytes to the upload_url returned above
curl -s -X PUT "{upload_url}" --data-binary @photo.png

# 3. Reference {file_upload_id} in a page/block payload
```

## 属性类型

数据库条目的常用属性格式：

- **标题：** `{"title": [{"text": {"content": "..."}}]}`
- **富文本：** `{"rich_text": [{"text": {"content": "..."}}]}`
- **单选：** `{"select": {"name": "Option"}}`
- **多选：** `{"multi_select": [{"name": "A"}, {"name": "B"}]}`
- **日期：** `{"date": {"start": "2026-01-15", "end": "2026-01-16"}}`
- **复选框：** `{"checkbox": true}`
- **数字：** `{"number": 42}`
- **URL:** `{"url": "https://..."}`
- **Email:** `{"email": "user@example.com"}`
- **关系：** `{"relation": [{"id": "page_id"}]}`

## API 版本 2025-09-03 — Databases vs Data Sources

- **Databases 变成了 data sources。** 查询与读取用 `/data_sources/` 端点。
- **每个数据库有两个 ID：** `database_id` 与 `data_source_id`。
  - 创建页面时用 `database_id`：`parent: {"database_id": "..."}`
  - 查询时用 `data_source_id`：`POST /v1/data_sources/{id}/query`
- 搜索把数据库返回为 `"object": "data_source"`，并带 `data_source_id` 字段。

## Notion Workers（进阶，需要 `ntn`）

Workers 是 Notion 替你托管的 TypeScript 程序。一个 worker 可以暴露以下任意组合：
- **Syncs**——按计划（默认 30 分钟）把外部 API 的数据拉进某个 Notion 数据库。
- **Tools**——在 Notion 的 Custom Agents 里作为可调用工具出现。
- **Webhooks**——接收外部服务（GitHub、Stripe 等）的 HTTP 事件并在 Notion 里行动。

**套餐 / 平台门槛：**
- CLI 在所有套餐可用。**部署 Workers 需要 Business 或 Enterprise。**
- 截至 2026 年 5 月 `ntn` 仅 macOS/Linux。Windows 用户需要 WSL2 或等待原生支持。
- 2026 年 8 月 11 日前免费。之后按 Notion 点数计费。

### 最小 Worker

```bash
ntn workers new my-worker      # scaffold
cd my-worker
# Edit src/index.ts
ntn workers deploy --name my-worker
```

`src/index.ts`:
```typescript
import { Worker } from "@notionhq/workers";

const worker = new Worker();
export default worker;

worker.tool("greet", {
  title: "Greet a User",
  description: "Returns a friendly greeting",
  inputSchema: { type: "object", properties: { name: { type: "string" } }, required: ["name"] },
  execute: async ({ name }) => `Hello, ${name}!`,
});
```

### Webhook 能力

```typescript
worker.webhook("onGithubPush", {
  title: "GitHub Push Handler",
  execute: async (events, { notion }) => {
    for (const event of events) {
      // event.body, event.rawBody (for signature verification), event.headers
      console.log("got delivery", event.deliveryId);
    }
  },
});
```

部署后：`ntn workers webhooks list` 显示 Notion 生成的 URL。把该 URL 当密钥对待——除非你加了签名校验，任何拿到它的人都能 POST 事件。

### Worker 生命周期命令

```bash
ntn workers deploy
ntn workers list
ntn workers exec <capability-key> -d '{"name": "world"}'
ntn workers sync trigger <key>            # run a sync now
ntn workers sync pause <key>
ntn workers env set GITHUB_WEBHOOK_SECRET=...
ntn workers runs list                     # recent invocations
ntn workers runs logs <run-id>
ntn workers webhooks list
```

被要求构建 Worker 时，用 `ntn workers new` 脚手架、在 `src/index.ts` 写代码、用 `ntn workers env set` 设置密钥，然后部署。https://developers.notion.com/workers 的 Notion 文档覆盖完整 API 面。

## Notion 风味 Markdown（被 `/markdown` 端点使用）

标准 CommonMark 加上用于 Notion 专有块的类 XML 标签。缩进用 **tab**。

**超出 CommonMark 的块：**
```
<callout icon="🎯" color="blue_bg">
	Ship the MVP by **Friday**.
</callout>

<details color="gray">
<summary>Toggle title</summary>
	Children indented one tab
</details>

<columns>
	<column>Left side</column>
	<column>Right side</column>
</columns>

<table_of_contents color="gray"/>
```

**行内：**
- Mentions: `<mention-user url="..."/>`, `<mention-page url="...">Title</mention-page>`, `<mention-date start="2026-05-15"/>`
- 下划线：`<span underline="true">text</span>`
- 颜色：`<span color="blue">text</span>`，或首行的块级 `{color="blue"}`
- 数学：行内 `$x^2$`，块级 `$$ ... $$`
- 引用：`[^https://example.com]`

**颜色：** `gray brown orange yellow green blue purple pink red`，外加用于背景的 `*_bg` 变体。

标题 5/6 会坍缩为 H4。多个 `>` 行会渲染成彼此独立的引用块——多行引用要在单个 `>` 里用 `<br>`。

## 选择正确的路径

| 任务 | mac / Linux | Windows |
|---|---|---|
| 读写页面、搜索、查询数据库 | `ntn api ...` | curl |
| 读页面供代理摘要 | `ntn api v1/pages/{id}/markdown` | curl `/markdown` 端点 |
| 上传文件 | `ntn files create < file` | 三步 HTTP 流程 |
| 一次性 API 探索 | `ntn api ...` | curl |
| 构建 Notion 托管的 sync / webhook / 代理工具 | `ntn workers ...` | WSL2 + `ntn workers ...` |

## 注意

- 页面/数据库 ID 是 UUID（带或不带连字符——两者都接受）。
- 速率限制：平均约 3 请求/秒。CLI 不会绕过它。
- API 无法设置数据库**视图**筛选——那是 UI 专属的。
- 创建 data source 时用 `"is_inline": true` 把它嵌入页面。
- 给 curl 始终传 `-s` 抑制进度条（代理输出更干净）。
- 读取时把 JSON 管道过 `jq`：`... | jq '.results[0].properties'`。
- Notion 现在还提供了一个 MCP server（`Notion MCP`，在 DB 操作上比上一版约省 91% token）——若你想在会话里流式访问 Notion。可经 Hermes 的 MCP 支持把它接上，但上面的路径对多数一次性任务已经够用。
