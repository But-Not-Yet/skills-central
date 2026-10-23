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
| 客户端乐观回显 | 库投影来自 `get_messages_as_conversation`，不经客户端回显 |

## 宿主代码地图（行号会漂，先 grep 定位）

- `hermes_state_common.py` `SCHEMA_SQL`：`messages_display_order_insert` 触发器，`AND (active = 1 OR compacted = 1)` 排除 inactive 孪生行。**每次 writable open 都 `executescript(SCHEMA_SQL)`**（同文件注释），所以直接改数据库里的触发器不持久，下次打开就被重建回原样。
- `hermes_state_messages.py` `_reconcile_display_orders`：同一过滤条件；只在压缩/归档后调用（`_publish_compression` / `_archive_and_compact`），**撤回/重写路径不调用**。
- `hermes_state_mutation_transcript.py` `rewind_in_transaction`：软删 `active=0`，可能插入 replacement，不调用 reconcile。
- `hermes_state_messages.py` `replace_messages_in_transaction`：重写/重试路径，软删 + 插入，不调用 reconcile。
- `hermes_state_messages.py` `_insert_message_rows`：所有插入路径的唯一入口（flush、compaction clone、replace、rotation handoff、import）。插入 SQL 已写 `display_identity`，`display_order` 由触发器赋。
- `hermes_state_messages.py` `_ensure_display_order` / `_DISPLAY_INDEX_MISSING_SQL`：只在 `display_order`/`display_identity` 为 NULL 时才触发回填，不覆盖「槽位错但非 NULL」的行。

## 修法优先级

1. **P1-2a（低风险，推荐先做）**：在 `_insert_message_rows` 插入循环结束后加一条批量 `UPDATE`——对 `display_order = id` 且存在同 `display_identity` 的 inactive 孪生行（`active=0 AND compacted=0`）且 `display_order < id` 的新行，回填 `MIN(peer.display_order)`。一处覆盖全部插入路径，不动触发器、不改折叠口径。
2. **P1-3（治现存数据）**：一次性 SQL 回填 `active=1 AND display_order=id` 且有 inactive 孪生行的记录，先备份 `state.db`。
3. **P1-1（触发器）**：中高风险，会影响 compaction 代际折叠口径。先跑 P1-2a + P1-3 稳定后再评估；动它必须连带跑 `tests/hermes_state/` 全量。

## 复现与验收

- `~/.hermes/cache/scratch/repro_host_display_order_gap.py`：退出码 0 = 缺陷复现，2 = 未复现，1 = 导入失败。
- 统计坏行 SQL：`SELECT count(*) FROM messages m WHERE m.active=1 AND m.display_order=m.id AND EXISTS (SELECT 1 FROM messages p WHERE p.session_id=m.session_id AND p.display_identity=m.display_identity AND p.id<>m.id AND p.active=0 AND p.compacted=0 AND p.display_order IS NOT NULL AND p.display_order<m.id);`
- 修完复查同一 SQL 应归零。

## 更新存活（宿主源码补丁）

- 宿主 `hermes-agent` 是 git clone，`install-stamp.json` 的 `updateMechanism` 决定更新方式。更新会 autostash 本地改动，pull 后尝试 `stash apply`；上游改同一文件时补丁留在 stash 不落地。
- 给宿主打源码补丁用**本地分支 + 提交**（更新器检测到自定义分支时改走 `git merge origin/main`，本地提交保留；冲突时更新停止不动树）。别把未提交改动留在 detached HEAD 上。
- 补丁文件（`~/.hermes/patches/*.patch`）作为第二重保险；每次更新后核对补丁是否还在树上。

## 陷阱

- **别把 `_reconcile_display_orders` 当万能修理工**：它只在压缩后跑，撤回/重写路径不调用。照报告原样改 reconcile，撤回场景仍修不到。
- **别直接改数据库里的触发器**：`SCHEMA_SQL` 每次 writable open 都重建，改完下次打开就还原。
- **插件洗白不等于宿主没问题**：注入进 `api_content`，显示读 `content`；插件零 `state.db` 写。显示顺序错乱先查宿主槽位继承。
- **触发器改动的连带风险**：它同时服务 compaction 代际折叠；改 WHERE 条件会让所有会话的折叠口径漂移。
