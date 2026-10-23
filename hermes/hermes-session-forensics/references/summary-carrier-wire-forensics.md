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

## 全新会话被污染：绑定链取证（先排除，再定罪）

侧边栏手动新开的会话首轮就带旧会话摘要时，别急着套「压缩轮换携带」——轮换要求旧会话终结。按序排除：

1. **证明确是全新会话**：agent.log 的 `conversation turn: session=<sid> history=0` 行——history=0 证明宿主层首轮无携带。有这行就不是轮换/续接。
2. **排除检索污染**：state.db 按该 session_id 数 `session_search`/`lcm_recall`/`lcm_grep` 工具调用数，零调用即排除「agent 自己搜到了旧会话」。
3. **排除轮换**：查旧会话最后一条消息的时间戳——晚于新会话出生 = 两会话并存，非父子换代，轮换理论作废。
4. **定罪靠绑定日志**：grep agent.log 的 `compression boundary kept <旧sid> bound` 行——新会话已跑数分钟而常驻引擎仍绑旧会话，就是绑定切换失败（常见触发：包装层 bind_session_state 抛异常被吞，fail-open 沿用旧绑定）。绑定错 → select_context 组装旧会话 DAG → 旧摘要以新会话名义 ingest。
5. **归属登记是结果不是原因**：污染载体 ingest 后 `summary_nodes.session_id` = 新会话，查归属表会「合法」。判据必须是 ingest 前的 wire 快照＋绑定日志，不是归属表。

**「本会话遗留」口径连带**：会话首条消息可能就是携带摘要，里面装着旧会话的待办。报「本会话还有什么没做」之前，先对 history=0 行与首条真人消息的时间戳——早于它的待办是携带件，不算本会话的账。

## 修复边界

- 上下文引擎可在 `select_context` 里解析 node、只读查 `summary_nodes`；`node.session_id != 当前 session` 或 node 不在当前 DAG → drop，替换为指针并记台账。这是请求侧修，安全。
- 宿主侧应把 summary 绑定 `session_id`，新会话/模型切换不复制旧 carrier；`active=0/compacted=1` 的跨会话摘要行不应进入请求。
- 不要用 hidden user 消息/后台 heartbeat 做回执；它们可能触发 durable tail 重放，扩大污染。
- 不要只改 `assembly_probe` 的显示；它本来就不是 wire，必须改请求组装或加 wire 探针。

## 回答模板

- 「会/不会」必须带：wire turn 号、index、role、content 长度、node 的 `session_id` 与当前 session 的对比。
- 如果只在 `assembly_probe` 见到、prompt snapshot 没有：说「装配历史有、wire 没有」，不要再说「已发给模型」。
