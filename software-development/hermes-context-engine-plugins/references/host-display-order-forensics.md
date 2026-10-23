# 宿主侧显示顺序缺陷取证（state.db display_order）

## When to use

UI 消息顺序错乱、旧消息跳到队尾、怀疑插件注入污染显示、需要判定插件 vs 宿主 vs LCM vs 客户端。

## 归因判定表

| 候选 | 判据 |
|---|---|
| 插件注入 | 注入只进 `api_content` 侧车，显示读 `content`（`tui_gateway/session_history.py`）；插件全仓零 `state.db` 写（唯一 DB 动作是 `disclosure/carriers.py` 以 `mode=ro` 打开 `lcm.db`） |
| 压缩代际复制 | `engine.compress()` 纯转发内层结果，不复制行、不落库；副本形状来自内层压缩器与宿主 `archive_and_compact` |
| 宿主去重 | `_dedupe_display_generations` 按 `(active, id)` 选代表；去重本身可能正常，错的是被选中 active 行拿的槽位 |
| LCM-X 分裂 | 跨 `session_id` 副本才是分裂；同 session、同 uid、同 timestamp 的多行是本会话代际/重绕副本 |
| 客户端乐观回显 | 桌面端 REST 走 `hermes_cli/web_routers/sessions.py` 的 `/api/sessions/{id}/messages` → `db.get_messages(include_compacted=True)`，它按 `display_order` 分组（`_display_rows_from_conn`）。**`get_messages_as_conversation` 不读 display_order**（按 id 取行再去重），拿它断言顺序会永远看到「旧消息在队尾」 |

## 宿主代码地图（行号会漂，先 grep 定位）

- `hermes_state_common.py` `SCHEMA_SQL`：`messages_display_order_insert` 触发器，`AND (active = 1 OR compacted = 1)` 排除 inactive 孪生行。**每次 writable open 都 `executescript(SCHEMA_SQL)`**（同文件注释），所以直接改数据库里的触发器不持久，下次打开就被重建回原样。
- `hermes_state_messages.py` `_reconcile_display_orders`：同一过滤条件；只在压缩/归档后调用（`_publish_compression` / `_archive_and_compact`），**撤回/重写路径不调用**。
- `hermes_state_mutation_transcript.py` `rewind_in_transaction`：软删 `active=0`，可能插入 replacement，不调用 reconcile。
- `hermes_state_messages.py` `replace_messages_in_transaction`：重写/重试路径，软删 + 插入，不调用 reconcile。
- `hermes_state_messages.py` `_insert_message_rows`：**批量**插入口（flush 批、compaction clone、replace、rotation handoff、import）。**它不是唯一入口**：`append_message` 在同一文件里自己执行 `_INSERT_MESSAGE_SQL`，而撤回/编辑/重生成的副本正是走它。只改 `_insert_message_rows` 时，复现脚本会仍然显示「已复现」——别以为是修法错，是口子没堵全。
- `hermes_state_messages.py` `_ensure_display_order` / `_DISPLAY_INDEX_MISSING_SQL`：只在 `display_order`/`display_identity` 为 NULL 时才触发回填，不覆盖「槽位错但非 NULL」的行。

## 修法优先级

1. **P1-2a（低风险，推荐先做）**：在插入循环结束后加一条批量 `UPDATE`——对 `display_order = id` 且存在同 `display_identity` 的 inactive 孪生行（`active=0 AND compacted=0`）且 `display_order < id` 的新行，回填 `MIN(peer.display_order)`。回填要跑在 `stamp_inserted_row_snapshots` 之前，行摘要得描述最终落盘的形状。不动触发器、不改折叠口径。
   **挂法按调用方意图，不按缝挂**：给 `_insert_message_rows` 加 `inherit_withdrawn_slot=False`（默认关），只有「副本顶替被撤回行」的调用方显式开——每轮 flush（`agent/session_persistence.py` → `append_messages_batch` → `_append_messages_in_transaction`）、撤回交接副本（`rewind_in_transaction`）、单条 `append_message`。压缩、分叉播种、导入、整段替换一律不继承。理由：`archive_and_compact` 先把尾部行改成 `active=0, compacted=0`，再用同 identity、同时间戳插入承载副本，副本本来就要坐在摘要之后的新槽位上；无条件回填会把它们拽回旧位置。
2. **P1-3（治现存数据）**：一次性 SQL 回填 `active=1 AND display_order=id` 且有 inactive 孪生行的记录，先备份 `state.db`。
3. **P1-1（触发器）**：中高风险，会影响 compaction 代际折叠口径。先跑 P1-2a + P1-3 稳定后再评估；动它必须连带跑 `tests/hermes_state/` 全量。

## 复现与验收

- `~/.hermes/cache/scratch/repro_host_display_order_gap.py`：退出码 0 = 缺陷复现，2 = 未复现，1 = 导入失败。**断言必须打在显示投影 `db.get_messages(include_compacted=True)` 上**；打在 `get_messages_as_conversation` 上会永远报「复现」，因为它按 id 排序、根本不看槽位。
- 统计坏行 SQL：`SELECT count(*) FROM messages m WHERE m.active=1 AND m.display_order=m.id AND EXISTS (SELECT 1 FROM messages p WHERE p.session_id=m.session_id AND p.display_identity=m.display_identity AND p.id<>m.id AND p.active=0 AND p.compacted=0 AND p.display_order IS NOT NULL AND p.display_order<m.id);`
- 修完复查同一 SQL 应归零。

## 生产数据回填（服务在写的时候）

- **别开一条长事务**。多 GB 的 `messages` 上跑整表 UPDATE 会长期占住写锁，网关每轮都卡。按 `session_id` 分组，每组一个 `BEGIN IMMEDIATE` + `PRAGMA busy_timeout=30000`，提交即放锁（本机 523 行 / 14 会话 / 12.4 s）。
- **先打含 WAL 的快照**：`sqlite3 "file:…?mode=ro" ".backup <新文件>"`，再对快照 `PRAGMA integrity_check`。早先的备份不含之后写进 WAL 的行，别拿它当回滚点。
- **跑前跑后各数一次**：先用 `mode=ro` 数命中数（只读扫描也要十几秒，别当零成本），跑完用同一谓词复查必须归零；两个数都进交付记录。

## 索引与成本（别照抄「索引可用」的结论）

`idx_messages_display_identity` 是**部分索引**，只覆盖 `(active = 1 OR compacted = 1)` 的可见行；回填要找的恰恰是不可见孪生，用不上它。实测 `EXPLAIN QUERY PLAN` 走的是 `idx_messages_session_active (session_id, active)`，成本与「该会话不可见行数」成正比。实测：普通追加在噪声内（−1%），撤回孪生命中 +1%，单会话 1500 条撤回行时每次追加约 +2 ms；生产同库最大会话只有 600 余条撤回行，所以真实增量在 1 ms 内。报性能前先 `GROUP BY session_id` 量一遍真实分布，再判断病态档存不存在。

## 更新存活（宿主源码补丁）

- 宿主 `hermes-agent` 是 git clone，`install-stamp.json` 的 `updateMechanism` 决定更新方式。更新会 autostash 本地改动，pull 后尝试 `stash apply`；上游改同一文件时补丁留在 stash 不落地。
- 给宿主打源码补丁用**本地分支 + 提交**（更新器检测到自定义分支时改走 `git merge origin/main`，本地提交保留；冲突时更新停止不动树）。别把未提交改动留在 detached HEAD 上。
- 补丁文件（`~/.hermes/patches/*.patch`）作为第二重保险；每次更新后核对补丁是否还在树上。

## 陷阱

- **别把回填无条件挂在共享插入缝上**：压缩与撤回走同一条 `_insert_message_rows`，语义相反。判据固定成这三条既有测试：`tests/hermes_state/test_display_projection_parity.py`、`test_hermes_state.py::TestHandoffTimestampCarry`、`test_session_archived_round_trip.py`——它们会以「摘要行顶掉后面那条」的形状变红（索引处 `[summary 0]` vs `e0 user 3`）。发现方式：拿这批文件在**未改版本**上跑一遍，两边 `FAILED` 清单求差；只看「修后红不红」会漏掉它们（这些文件本来就有环境性失败）。
- **别把 `_reconcile_display_orders` 当万能修理工**：它只在压缩后跑，撤回/重写路径不调用。照报告原样改 reconcile，撤回场景仍修不到。
- **别直接改数据库里的触发器**：`SCHEMA_SQL` 每次 writable open 都重建，改完下次打开就还原。
- **插件洗白不等于宿主没问题**：注入进 `api_content`，显示读 `content`；插件零 `state.db` 写。显示顺序错乱先查宿主槽位继承。
- **触发器改动的连带风险**：它同时服务 compaction 代际折叠；改 WHERE 条件会让所有会话的折叠口径漂移。
