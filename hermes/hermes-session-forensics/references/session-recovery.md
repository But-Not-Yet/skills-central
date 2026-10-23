# 误删会话的找回

桌面端删除会话 = 从 state.db 硬删（`sessions` 行与名下 `messages` 一起清，无软删标记、`hermes sessions` 无 restore 子命令）。但消息正文在别处仍有多份存活副本，找回按下面顺序走。

## 存活面判定（先查哪里还活着，再动手）

1. **lcm.db（首选，通常是最全的一份）**：`SELECT role, content, tool_calls, timestamp FROM messages WHERE session_id='<id>' ORDER BY timestamp, store_id`。会话删除不动这张表，全量逐条都在（含工具调用）。按只读连接开：`sqlite3 -readonly` 或 `mode=ro` URI，别锁活库。
2. **回退分支（rewind/fork）**：桌面端每次回退新建一个 session id，消息前缀整段复制进 state.db。删掉父会话后，分支行仍存活且 `parent_session_id` 清成 NULL——查分支：`SELECT id,parent_session_id,title,message_count,datetime(started_at,'unixepoch','localtime') FROM sessions WHERE title LIKE '%<关键词>%' OR id IN (<已知分支id>)`。
3. **每日快照**：`~/.hermes/lcm.db.daily.YYYYMMDD`（另有各式手工备份）。当活库 lcm.db 也缺该会话时（如更早删除后又被 compaction 清理）按快照日期倒序找最近一份含该 session_id 的。
4. 孤儿消息核查：`SELECT m.session_id,COUNT(*) FROM messages m LEFT JOIN sessions s ON s.id=m.session_id WHERE s.id IS NULL GROUP BY m.session_id` —— 空则 state.db 里确无残留。

## 不知道被删会话的 id？

用存活分支的第一条主人消息当指纹，去 lcm.db 认亲：分支消息（state.db）与 lcm.db 各 session_id 的首条 user 内容比对（首条主人消息文本一致即同一血统）。lcm.db 侧枚举近期会话：`SELECT session_id,COUNT(*),MAX(datetime(timestamp,'unixepoch','localtime')) FROM messages GROUP BY session_id ORDER BY 3 DESC`。

## 导出交付

从 lcm.db 导出两份：原始 JSONL（逐行 store_id/role/content/tool_name/tool_calls/timestamp，机器可再导入）+ 可读 Markdown（只留 user/assistant、折叠相邻重复行、跳过 `<untrusted_tool_result` 开头的工具回声、按时间戳排版）。放 `~/Documents/Hermes/找回会话_<日期>/` 并 MEDIA: 递给主人。

## 回插 state.db（要重新出现在侧边栏并能续聊时）

可行但要写活库，动手前先备份 state.db。要件：
- 重建 `sessions` 行（id、source='desktop'、started_at、model 等）。
- `messages` 表显示字段要补对：`display_order`、`message_uid`、`display_identity`（有 trigger 维护这些列，插错会渲染乱序或撞唯一约束）。
- 表里**没有** `deleted` 列——可见性字段是 `archived`/`hidden`/`auto_archived`。猜列名先 `PRAGMA table_info(sessions)`，别硬写。
回插属于改活库的写操作，按站规先报意图、得主人在场确认再执行。
