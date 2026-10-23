---
name: teams-meeting-pipeline
description: "运行或排查 Teams 会议管线（摘要、转写、Graph 订阅）时使用。只要涉及微软 Teams 会议摘要、action items、pipeline status、replay job 或 Graph webhook 订阅，就主动加载。即使用户只是问「今天的会议摘要怎么没到」。"
version: 1.1.0
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [MSGRAPH_TENANT_ID, MSGRAPH_CLIENT_ID, MSGRAPH_CLIENT_SECRET]
  commands: [hermes]
metadata:
  hermes:
    tags: [Teams, Microsoft Graph, Meetings, Productivity, Operations]
    # Channel-gated: this pipeline only makes sense on the Teams gateway
    # channel (and in cron jobs, where its scheduled summary/replay work
    # actually runs). Hidden from every other session's skills index.
    session_platforms: [teams, cron]
    related_docs:
      - /docs/guides/microsoft-graph-app-registration
      - /docs/user-guide/messaging/teams-meetings
      - /docs/guides/operate-teams-meeting-pipeline
---

# Teams 会议管线

只要用户问起微软 Teams 会议摘要、转写、录音、action items、Graph 订阅，或任何关于 Teams 会议管线的运维问题。就用本 skill。支持任何语言——下方的触发词只是示例，并非穷尽列表。

所有面向运维的东西都是经 terminal 工具运行的 `hermes teams-pipeline` 子命令。本管线没有新增模型工具——CLI 就是接口。

## 何时使用本 skill

用户是在要求：
- 汇总一场 Teams 会议 / 提取 action items / 拉取会议记录
- 检查管线状态、查看某个已存的会议 job，或查看最近的会议
- 重放 / 重跑一个失败或需要重新摘要的已存 job
- 在改动环境或配置后校验 Microsoft Graph 设置
- 排查「会议摘要一直没到」或「没有新会议在摄入」
- 管理 Graph webhook 订阅（创建、续订、删除、查看）
- 设置自动订阅续订（见下方坑）

多语言触发示例（非穷尽）：
- 英文："summarize the Teams meeting"、"pipeline status"、"replay job X"
- 土耳其语："Teams meeting özetle"、"action item çıkar"、"toplantı notu"、"pipeline durumu"、"replay job"

## 前置条件

使用管线前，确认这些已设在 `${HERMES_HOME:-~/.hermes}/.env`：

```bash
MSGRAPH_TENANT_ID=...
MSGRAPH_CLIENT_ID=...
MSGRAPH_CLIENT_SECRET=...
```

若缺少任何一个，把用户引到 Azure 应用注册指南 `/docs/guides/microsoft-graph-app-registration`——在管线能用之前。他们需要一个带管理员同意 Graph 应用权限的 Azure AD 应用注册。

## 命令参考

### 状态与查看（从这里开始）

```bash
hermes teams-pipeline validate              # config snapshot — run first after any change
hermes teams-pipeline token-health          # Graph token status
hermes teams-pipeline token-health --force-refresh   # force a fresh token acquisition
hermes teams-pipeline list                  # recent meeting jobs
hermes teams-pipeline list --status failed  # only failed jobs
hermes teams-pipeline show <job-id>         # full detail of one job
hermes teams-pipeline subscriptions         # current Graph webhook subscriptions
```

### 重跑 / 调试

```bash
hermes teams-pipeline run <job-id>          # replay a stored job (re-summarize, re-deliver)
hermes teams-pipeline fetch --meeting-id <id>   # dry-run: resolve meeting + transcript without persisting
hermes teams-pipeline fetch --join-web-url "<url>"   # dry-run by join URL
hermes teams-pipeline fetch --join-web-url "<url>" --organizer-user-id <id>   # organizer-scoped lookup (required for /meet/ short URLs)
```

### 订阅管理

```bash
hermes teams-pipeline subscribe \
  --resource communications/onlineMeetings/getAllTranscripts \
  --notification-url https://<your-public-host>/msgraph/webhook \
  --client-state "$MSGRAPH_WEBHOOK_CLIENT_STATE"

hermes teams-pipeline renew-subscription <sub-id> --expiration <iso-8601>
hermes teams-pipeline delete-subscription <sub-id>
hermes teams-pipeline maintain-subscriptions            # renew near-expiry ones
hermes teams-pipeline maintain-subscriptions --dry-run  # show what would be renewed
```

## 常见诉求的决策树

- 用户问「今天会议的摘要怎么没收到？」→ 先用 `list --status failed`，再对相关行 `show <job-id>`。若该 job 根本不存在，查 `subscriptions`——webhook 可能已过期（见下方坑）。
- 用户问「设置正常吗？」→ `validate`，然后 `token-health`，再 `subscriptions`。三者都通过就请求一场测试会议并查 `list` 有无新行。
- 用户问「重跑会议 X 的摘要」→ `list` 找到 job ID，`run <job-id>` 重放。若再次失败，`show <job-id>` 查看错误，`fetch --meeting-id` 干跑产物解析。
- 用户问「把会议 X 加入管线」→ 通常不用——管线由订阅驱动，而非逐会议。若他们想摘要某场过去的会议，用 `fetch` 拉转写，创建 job 后再 `run`。

## 关键坑：Graph 订阅 72 小时过期

Microsoft Graph 把 webhook 订阅上限设为 72 小时，且**不会自动续订**。若没有调度 `maintain-subscriptions`，任何手动订阅创建 3 天后，会议通知会静默停止到达。

当用户报告「管线昨天还好使，今天什么都没到」：
1. 运行 `hermes teams-pipeline subscriptions`——若为空或所有条目的 `expirationDateTime` 都在过去，那就是原因。
2. 按上面所示用 `subscribe` 重建。
3. **立即设置自动续订**，经 `hermes cron add`、systemd timer 或普通 crontab。`/docs/guides/operate-teams-meeting-pipeline#automating-subscription-renewal-required-for-production` 的运维 runbook 有全部三种方案。12 小时间隔是安全的（相对 72h 上限有 6 倍余量）。

## 其他坑

- **转写尚未就绪。** 会议结束后 Teams 需要一些时间生成转写产物。对刚结束的会议 `fetch --meeting-id` 可能返回空。等 2-5 分钟重试，或让 Graph webhook 自然驱动摄入。
- **投递模式不匹配。** 若摘要已生成（`list` 显示成功）但 Teams 里什么都没落地，检查 `platforms.teams.extra.delivery_mode` 与匹配的目标配置（`incoming_webhook_url` 或 `chat_id` 或 `team_id`+`channel_id`）。写入器从 config.yaml 或 `TEAMS_*` 环境变量读取这些。
- **Graph 应用权限。** token 获取正常（`token-health` 通过），但当权限已添加而管理员同意未重新授予时，Graph API 调用返回 401/403。让用户在 Azure 门户重新进入应用注册并再点一次「Grant admin consent」。

## 相关文档

当用户需要的深度超出本 skill 覆盖时，把他们引到这些：
- Azure 应用注册演练：`/docs/guides/microsoft-graph-app-registration`
- 完整管线设置：`/docs/user-guide/messaging/teams-meetings`
- 运维 runbook（续订自动化、排查、上线清单）：`/docs/guides/operate-teams-meeting-pipeline`
- Webhook 监听器设置：`/docs/user-guide/messaging/msgraph-webhook`
