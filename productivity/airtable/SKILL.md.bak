---
name: airtable
description: "用 curl 直接调用 Airtable REST API 操作表与记录时使用。只要涉及 Airtable 的 base、table、字段、记录增删改查、filterByFormula 或 upsert，就主动加载，即使用户只提到某个 base 名或 PAT。"
version: 1.1.0
author: community
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [AIRTABLE_API_KEY]
  commands: [curl]
metadata:
  hermes:
    tags: [Airtable, Productivity, Database, API]
    homepage: https://airtable.com/developers/web/api/introduction
---

# Airtable — Base、Table 与记录

用 `terminal` 工具、经 `curl` 直接操作 Airtable 的 REST API。没有 MCP 服务器，没有 OAuth 流程，没有 Python SDK——只有 `curl` 和一个 personal access token。

## 前置条件

1. 在 https://airtable.com/create/tokens 创建一个 **Personal Access Token (PAT)**（token 以 `pat...` 开头）。
2. 授予这些 scope（最低限度）：
   - `data.records:read`——读行
   - `data.records:write`——创建 / 更新 / 删除行
   - `schema.bases:read`——列出 base 与 table
3. **重要：** 在同一个 token 界面里，把你想要访问的每个 base 加入该 token 的 **Access** 列表。PAT 按 base 限定作用域——在错误的 base 上，有效 token 也会返回 `403`。
4. 把 token 存在 `${HERMES_HOME:-~/.hermes}/.env`（或经 `hermes setup`）：
   ```
   AIRTABLE_API_KEY=pat_your_token_here
   ```

> 注意：旧式 `key...` API key 已于 2024 年 2 月弃用。现在只有 PAT 和 OAuth token 可用。

## API 基础

- **端点：** `https://api.airtable.com/v0`
- **认证头：** `Authorization: Bearer $AIRTABLE_API_KEY`
- **所有请求**都用 JSON（任何 POST/PATCH/PUT 正文都带 `Content-Type: application/json`）。
- **对象 ID：** base `app...`、table `tbl...`、record `rec...`、field `fld...`。ID 永不改变；名称会变。自动化中优先用 ID。
- **速率限制：** 每个 base 5 请求/秒。`429` → 退避。对单个 base 突发会被限流。

基础 curl 模式：
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?maxRecords=5" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python -m json.tool
```

`-s` 抑制 curl 的进度条——每次调用都保留它，让工具输出对 Hermes 保持干净。经 `python -m json.tool`（总是存在）或 `jq`（若已安装）管道以获得可读 JSON。

## 字段类型（请求正文形状）

| 字段类型 | 写入形状 |
|---|---|
| 单行文本 | `"Name": "hello"` |
| 长文本 | `"Notes": "multi\nline"` |
| 数字 | `"Score": 42` |
| 复选框 | `"Done": true` |
| 单选 | `"Status": "Todo"`（名称必须已存在，除非 `typecast: true`） |
| 多选 | `"Tags": ["urgent", "bug"]` |
| 日期 | `"Due": "2026-04-01"` |
| 日期时间 (UTC) | `"At": "2026-04-01T14:30:00.000Z"` |
| URL / Email / 电话 | `"Link": "https://…"` |
| 附件 | `"Files": [{"url": "https://…"}]`（Airtable 会抓取并转存） |
| 链接记录 | `"Owner": ["recXXXXXXXXXXXXXX"]`（record ID 数组） |
| 用户 | `"AssignedTo": {"id": "usrXXXXXXXXXXXXXX"}` |

在 create/update 正文顶层传 `"typecast": true`，让 Airtable 自动强转值（如即时创建新的 select 选项、把 `"42"` 转成 `42`）。

## 常用查询

### 列出 token 可见的 base
```bash
curl -s "https://api.airtable.com/v0/meta/bases" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python -m json.tool
```

### 列出某个 base 的 table 与 schema
```bash
curl -s "https://api.airtable.com/v0/meta/bases/$BASE_ID/tables" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python -m json.tool
```
变更之前先用它——确认精确的字段名与 ID，暴露 select 字段的 `options.choices`，并显示主字段名。

### 列出记录（前 10 条）
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?maxRecords=10" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python -m json.tool
```

### 获取单条记录
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python -m json.tool
```

### 筛选记录（filterByFormula）
Airtable 公式必须 URL 编码。让 Python 标准库来做——绝不手工编码：
```bash
FORMULA="{Status}='Todo'"
ENC=$(python -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$FORMULA")
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?filterByFormula=$ENC&maxRecords=20" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python -m json.tool
```

有用的公式模式：
- 精确匹配：`{Email}='user@example.com'`
- 包含：`FIND('bug', LOWER({Title}))`
- 多条件：`AND({Status}='Todo', {Priority}='High')`
- 或：`OR({Owner}='alice', {Owner}='bob')`
- 非空：`NOT({Assignee}='')`
- 日期比较：`IS_AFTER({Due}, TODAY())`

### 排序 + 选择特定字段
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?sort%5B0%5D%5Bfield%5D=Priority&sort%5B0%5D%5Bdirection%5D=asc&fields%5B%5D=Name&fields%5B%5D=Status" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python -m json.tool
```
查询参数里的方括号必须 URL 编码（`%5B` / `%5D`）。

### 使用命名视图
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?view=Grid%20view&maxRecords=50" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python -m json.tool
```
视图在服务端应用其保存的筛选 + 排序。

## 常用变更

### 创建记录
```bash
curl -s -X POST "https://api.airtable.com/v0/$BASE_ID/$TABLE" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"Name":"New task","Status":"Todo","Priority":"High"}}' | python -m json.tool
```

### 一次调用最多创建 10 条记录
```bash
curl -s -X POST "https://api.airtable.com/v0/$BASE_ID/$TABLE" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "typecast": true,
    "records": [
      {"fields": {"Name": "Task A", "Status": "Todo"}},
      {"fields": {"Name": "Task B", "Status": "In progress"}}
    ]
  }' | python -m json.tool
```
批量端点每次请求上限为 **10 条记录**。更大的插入，以 10 条为一批循环并短暂 sleep，以遵守 5 req/sec/base。

### 更新记录（PATCH——合并，保留未改字段）
```bash
curl -s -X PATCH "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"Status":"Done"}}' | python -m json.tool
```

### 按合并字段 upsert（无需 ID）
```bash
curl -s -X PATCH "https://api.airtable.com/v0/$BASE_ID/$TABLE" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "performUpsert": {"fieldsToMergeOn": ["Email"]},
    "records": [
      {"fields": {"Email": "user@example.com", "Status": "Active"}}
    ]
  }' | python -m json.tool
```
`performUpsert` 对合并字段值为新的记录执行创建，对合并字段值已存在的记录执行 patch。非常适合幂等同步。

### 删除记录
```bash
curl -s -X DELETE "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python -m json.tool
```

### 一次调用最多删除 10 条记录
```bash
curl -s -X DELETE "https://api.airtable.com/v0/$BASE_ID/$TABLE?records%5B%5D=rec1&records%5B%5D=rec2" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python -m json.tool
```

## 分页

列表端点每页最多返回 **100 条记录**。若响应包含 `"offset": "..."`，在下次调用时传回去。循环直到该字段不存在：

```bash
OFFSET=""
while :; do
  URL="https://api.airtable.com/v0/$BASE_ID/$TABLE?pageSize=100"
  [ -n "$OFFSET" ] && URL="$URL&offset=$OFFSET"
  RESP=$(curl -s "$URL" -H "Authorization: Bearer $AIRTABLE_API_KEY")
  echo "$RESP" | python -c 'import json,sys; d=json.load(sys.stdin); [print(r["id"], r["fields"].get("Name","")) for r in d["records"]]'
  OFFSET=$(echo "$RESP" | python -c 'import json,sys; d=json.load(sys.stdin); print(d.get("offset",""))')
  [ -z "$OFFSET" ] && break
done
```

## 典型 Hermes 工作流

1. **确认认证。** `curl -s -o /dev/null -w "%{http_code}\n" https://api.airtable.com/v0/meta/bases -H "Authorization: Bearer $AIRTABLE_API_KEY"`——预期 `200`。
2. **找到 base。** 列出 base（上一步），或若 token 缺 `schema.bases:read`，直接向用户要 `app...` ID。
3. **查看 schema。** `GET /v0/meta/bases/$BASE_ID/tables`——变更任何东西之前，在会话里本地缓存精确的字段名与主字段名。
4. **写前先读。** 对「把 Y 更新成 X」，先用 `filterByFormula` 解析出 `rec...` ID，再 `PATCH /v0/$BASE_ID/$TABLE/$RECORD_ID`。绝不要猜 record ID。
5. **批量写。** 把相关的创建合并成一个 10 条记录的 POST，以留在 5 req/sec 预算内。
6. **破坏性操作。** 删除无法经 API 撤销。若用户说「删掉所有 X」，先回显筛选条件 + 记录数并确认再动手。

## 常见坑

- **`filterByFormula` 必须 URL 编码。** 含空格或非 ASCII 的字段名也需编码（`{My Field}` → `%7BMy%20Field%7D`）。用 Python 标准库（上面的模式）——绝不手工转义。
- **响应会省略空字段。** 缺少某个 `"Assignee"` 键不代表该字段不存在——而是表示这条记录的值是空的。在断定字段缺失前先查 schema（步骤 3）。
- **PATCH vs PUT。** `PATCH` 把所提供的字段合并进记录。`PUT` 完全替换记录，并清空你没包含的任何字段。默认用 `PATCH`。
- **单选选项必须已存在。** 当 `Shipping` 不在字段选项列表里时写 `"Status": "Shipping"` 会报 `INVALID_MULTIPLE_CHOICE_OPTIONS`，除非传 `"typecast": true`（它会自动创建该选项）。
- **按 base 的 token 限定。** 一个 base 报 `403` 而另一个正常，说明该 token 的 Access 列表不含那个 base——不是 scope 或认证问题。把用户引到 https://airtable.com/create/tokens 去授予。
- **速率限制按 base，而非按 token。** 在 `baseA` 上 5 req/sec 且 `baseB` 上 5 req/sec 没问题；光在 `baseA` 上 6 req/sec 会被限流。留意 `429` 上的 `Retry-After` 头。

## 给 Hermes 的重要提示

- **始终用 `terminal` 工具配 `curl`。** 不要用 `web_extract`（它无法发认证头）或 `browser_navigate`（需要 UI 认证且慢）。
- **加载本 skill 时，`AIRTABLE_API_KEY` 会自动从 `${HERMES_HOME:-~/.hermes}/.env` 流入子进程**——无需在每次 `curl` 调用前重新导出。
- **小心转义公式里的花括号。** 在 heredoc 正文里，`{Status}` 是字面量。在 shell 参数里，`{Status}` 在 `{...}` 花括号展开语境之外是安全的——但动态字符串要先经 `python urllib.parse.quote` 再拼进 URL。
- **用 `python -m json.tool` 美化输出**（总是存在），而非 `jq`（可选）。只有需要筛选/投影时才动用 `jq`。
- **分页是按页，而非全局。** Airtable 的 100 条记录上限是硬限制；无法提高。用 `offset` 循环直到该字段不存在。
- **读非 2xx 响应里的 `errors` 数组**——Airtable 会返回结构化错误码，如 `AUTHENTICATION_REQUIRED`、`INVALID_PERMISSIONS`、`MODEL_ID_NOT_FOUND`、`INVALID_MULTIPLE_CHOICE_OPTIONS`，精确告诉你哪里不对。
