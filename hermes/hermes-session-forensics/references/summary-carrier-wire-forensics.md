# 跨会话 summary carrier 的 wire 取证

适用：模型反复看到旧话题摘要、`assembly_probe` 每轮 index 0 都是 `[Recent Summary ...]`、怀疑长上下文被污染、要回答「这条摘要到底有没有发给模型」。

## 先分清两个问题

- 消息重复/顺序错乱：看 `message-replay-diagnosis.md`。
- 摘要 carrier 污染：本条。两者可以同时发生，但不是同一根因。

## 取证步骤

1. 从 prompt snapshot 取 wire：`~/.hermes/cache/scratch/prompt_snapshot/<session_id>/turn_*.json`；读 `messages[].row.content`（顶层 content 恒 None）。找以 `[Recent Summary (d0, node <N>)]` 开头的 user 行；记录 turn、index、content_len。
2. 找 node 归属：`select node_id, session_id, depth, length(summary) from summary_nodes where node_id=<N>;` 与当前 `session_id` 比较；当前会话 node count 也要查。
3. 找 state.db 源行：`select id, role, active, compacted, message_uid, display_order, length(content) from messages where session_id=<sid> and content like '%[Recent Summary%';` 常见是 `active=0, compacted=1` 的旧行被请求组装重新带进来。
4. 定污染窗口：逐 turn 检查 index 0 是否为 carrier，记 first/last turn；对比 `assembly_probe`（post_llm）与 wire，别混。
5. 判断「发给谁」：请求消息列表与 provider 无关；wire 有就是发给了当时的模型，换本地 localllm 也一样。不要用 `sessions.model` 或 `assembly_probe` 代替 wire。

## 修复边界

- 上下文引擎可在 `select_context` 里解析 node、只读查 `summary_nodes`；`node.session_id != 当前 session` 或 node 不在当前 DAG → drop，替换为指针并记台账。这是请求侧修，安全。
- 宿主侧应把 summary 绑定 `session_id`，新会话/模型切换不复制旧 carrier；`active=0/compacted=1` 的跨会话摘要行不应进入请求。
- 不要用 hidden user 消息/后台 heartbeat 做回执；它们可能触发 durable tail 重放，扩大污染。
- 不要只改 `assembly_probe` 的显示；它本来就不是 wire，必须改请求组装或加 wire 探针。

## 回答模板

- 「会/不会」必须带：wire turn 号、index、role、content 长度、node 的 `session_id` 与当前 session 的对比。
- 如果只在 `assembly_probe` 见到、prompt snapshot 没有：说「装配历史有、wire 没有」，不要再说「已发给模型」。
