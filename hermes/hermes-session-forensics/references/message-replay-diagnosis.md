# 消息重放与 active-row 取证

适用：桌面端 UI 把旧消息画到队尾、同一条用户消息出现多次、模型回复与最后一条可见消息不对应。先按宿主重放查，不要先归因给上下文插件的载体规范化。

## 数据源

- `state.db.messages`：宿主消息表，关键列 `id, session_id, role, content, timestamp, active, observed, display_kind, message_uid, display_order`。UI 通常只渲染 `active=1` 的行，并按 `id`/`display_order` 排序。
- `lcm.db.messages`：上下文引擎的逐条副本；`lcm_inspect` 的 `ingest_reconciliation` 会记录 `replayed durable tail` 一类重放。
- `assembly_probe`：`~/.hermes/cache/scratch/assembly_probe/probe.jsonl`，记录每轮 `index=0` 的摘要载体；用来区分「消息重复」与「旧 summary carrier 污染」。

## wire 证据 vs 装配探针

- `prompt_snapshot/<session>/turn_<N>.json` 是实际请求：正文在 `messages[].row.content`，顶层 `content` 常为 None。判断「有没有发给模型」只看这里，或 `request_probe`（若开）。
- `assembly_probe` 记录的是 `post_llm_call` 的 `conversation_history`，不是 wire；它可以在请求里已经没有某条 carrier 时仍报 index 0。不能用它证明已发送。
- 回答此类问题要带 turn 号、index、role、content 长度，不凭 probe 的一句话。

## 取证 SQL

把 `<session_id>` 换成目标会话；只读 URI 打开。

```sql
-- 1. 总量与 active 量
select count(*) as total, sum(active) as active
from messages where session_id = '<session_id>';

-- 2. 按 role/active 看哪一类在膨胀
select role, active, count(*)
from messages where session_id = '<session_id>'
group by role, active order by 3 desc;

-- 3. 同一 message_uid 的多份副本\.message_uid 是消息身份，不是行 id
select message_uid, count(*) as copies,
       sum(active) as active_copies,
       min(id) as first_row, max(id) as last_row
from messages
where session_id = '<session_id>' and message_uid is not null
group by message_uid having count(*) > 1
order by copies desc limit 20;

-- 4. 可疑消息的每份副本：看 active 与 display_order
select id, role, active, observed, display_kind,
       display_order, timestamp, length(content), substr(content,1,80)
from messages
where session_id = '<session_id>'
  and (message_uid = '<message_uid>'
       or content like '%<distinctive_text>%')
order by id;

-- 5. 队尾的 active 行：旧 timestamp 却有大 id/大 display_order
select id, role, active, display_order, timestamp, substr(content,1,60)
from messages
where session_id = '<session_id>' and active = 1
order by id desc limit 30;

-- 6. hidden/异步 user 消息（可能的触发源）
select id, display_kind, active, timestamp, substr(content,1,80)
from messages
where session_id = '<session_id>'
  and role = 'user'
  and display_kind in ('hidden','async_delegation_complete')
order by id desc limit 20;

-- 7. 旧 summary carrier（与重复消息分开看）
select id, role, active, display_kind, timestamp, substr(content,1,120)
from messages
where session_id = '<session_id>'
  and content like '%[Recent Summary%'
order by id;
```

LCM 侧：

```sql
-- 同一条消息在 LCM 里是否被批量打上同一秒
select timestamp, count(*)
from messages where session_id = '<session_id>'
group by timestamp order by 2 desc limit 10;
```

`lcm_inspect` 里看 `ingest_reconciliation.reason` 是否含 `replayed durable tail`、`replayed_tool_segment_rows`，以及 `messages.min_store_id/max_store_id`。

## 判读

1. **同 message_uid 多副本、只有一份 active**：这是宿主重放/重激活，不是用户重发。用户重发通常换新的 message_uid。
2. **active 副本的 `display_order` 等于新行 id**：UI 按 order/id 排序就会把它推到队尾。健康的重放副本应保留原 `display_order`（例如原消息的 order 是 142554，副本行是 143306）。
3. **旧 timestamp + 大 id**：重放把入库时刻写成当前时间，发送时刻仍是旧值；不要拿 timestamp 判顺序，用 `display_order`/原 id。
4. **hidden user 消息**：后台进程 heartbeat、`[ASYNC DELEGATION COMPLETE]` 以 user 角色入库，可能是重放触发源；先停这些来源，再用轮首读板/桌面插件做回执。
5. **summary carrier 单独算**：`assembly_probe` 每轮 index 0 出现旧话题的 `[Recent Summary ...]`，是摘要载体污染；它与「同一条消息重复」不是同一个 bug，别混成一条根因。

## 根因机制：为什么只有第一条错

- 同一 `message_uid` 的多份副本共享 `display_identity`；`messages_display_order_insert` 触发器找 peer 时和 `_reconcile_display_orders` 重算时都只看 `(active=1 OR compacted=1)` 的行。
- 原始行已被置 `active=0` 时，新 active 副本插入找不到同 identity 的 active/compacted peer，触发器回退成 `new.id`；重算也把新副本当作该 identity 的第一行，于是 `display_order` 留在队尾。
- 其它重放消息在插入/重算时还有 active/compacted peer，所以继承了原顺序；只有「原行先失活、后插 active 副本」的那条会错。
- 持久修法：触发器的 peer 子查询和 `_reconcile_display_orders` 的 `first_id` 计算要包含同 `display_identity` 的 inactive 行（只更新 active/compacted 行）。单条 `display_order` 回填是临时修复，下一次 reconcile 可能重置。

## 修复检查单

1. 备份：`cp -a state.db state.db.bak-<timestamp>`；要动 LCM 也一并备份。不要在桌面端正在写会话时直接改库；能停写就停写。
2. 先确认：目标 `message_uid` 恰好一份 active；找到原始行（最早、`display_order` 正确的行）与重放副本。
3. 修复二选一：
   - 把 active 副本的 `display_order` 回填为原始行的 `display_order`（或原 id）；单条 `UPDATE` 放在事务里，改完立即 `select` 回读。
   - 或重新激活原始行、把重放副本置 `active=0`；保证同一 `message_uid` 仍只有一份 active。
4. **不要删行、不要改 content、不要批量重排**；只改 `active/display_order` 这类展示元数据，且逐条回读。
5. 让桌面端重载/刷新；验收：目标消息回到原位置、`sum(active)` 与唯一 active `message_uid` 数不变、队尾不再出现旧 timestamp 的 active 行。
6. 停掉 hidden user 消息来源（后台进程 heartbeat、异步回执），改用轮首 `kanban_list/show` 或桌面插件 toast；否则下一次重放会再次写坏。

## 边界

- 这是宿主 `state.db` 的展示层修复，不是上下文插件的 carrier 规范化；插件侧无法修 active-row 重放，只能检测/报告。
- 全称断言（「所有重复都清理了」）必须带 `sum(active)`、唯一 `message_uid` 数、修复前后对照；只报单条回读不算穷尽。
