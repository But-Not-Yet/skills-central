# LCM FTS5 rebuild recipe (verified 2026-10-05)

## When to use
- `PRAGMA integrity_check` 报 `database disk image is malformed`
- 主表 `messages`/`summary_nodes` 仍可读（`SELECT COUNT(*)` 出数字）
- FTS5 搜索或 tiered 的 FTS 依赖失效

## Quick verification
```bash
sqlite3 ~/.hermes/lcm.db "SELECT COUNT(*) FROM messages;"  # 例：33969
sqlite3 ~/.hermes/lcm.db "SELECT COUNT(*) FROM summary_nodes;"  # 例：303
sqlite3 ~/.hermes/lcm.db "SELECT COUNT(*) FROM messages_fts MATCH 'plan mode';"  # 例：1
```

## Pre-rebuild
1. 停写（生产环境）：
   - `sudo systemctl restart hermes-gateway` 或 `pkill -f "gateway run"`
2. 备份（必须）：
   - `cp ~/.hermes/lcm.db ~/.hermes/lcm.db.bak_YYYYMMDD_HHMM`

## Rebuild (sqlite3 CLI)
```sql
-- 1. Drop FTS5 shadow tables first (simple B-tree indexes) DROP TABLE IF EXISTS messages_fts_data;
DROP TABLE IF EXISTS messages_fts_idx;
DROP TABLE IF EXISTS messages_fts_docsize;
DROP TABLE IF EXISTS messages_fts_config; DROP TABLE IF EXISTS nodes_fts_data;
DROP TABLE IF EXISTS nodes_fts_idx;
DROP TABLE IF EXISTS nodes_fts_docsize;
DROP TABLE IF EXISTS nodes_fts_config;
-- 2. Drop main FTS5 tables DROP TABLE IF EXISTS messages_fts;
DROP TABLE IF EXISTS nodes_fts;
-- 3. Recreate FTS5 tables CREATE VIRTUAL TABLE messages_fts USING fts5(content, content=messages, content_rowid=store_id);
CREATE VIRTUAL TABLE nodes_fts USING fts5(summary, content=summary_nodes, content_rowid=node_id);
-- 4. Re-insert marker rows INSERT INTO messages_fts(messages_fts) VALUES('rebuild');
INSERT INTO nodes_fts(nodes_fts) VALUES('rebuild');
-- 5. Recreate triggers (copy from hermes-lcm/plugin.yaml or command.py) CREATE TRIGGER IF NOT EXISTS msg_fts_insert AFTER INSERT ON messages BEGIN INSERT INTO messages_fts(rowid, content) VALUES (new.store_id, new.content); END;
CREATE TRIGGER IF NOT EXISTS msg_fts_delete AFTER DELETE ON messages BEGIN INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.store_id, old.content); END;
CREATE TRIGGER IF NOT EXISTS msg_fts_update AFTER UPDATE OF content ON messages BEGIN INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.store_id, old.content); INSERT INTO messages_fts(rowid, content) VALUES (new.store_id, new.content); END;
CREATE TRIGGER IF NOT EXISTS nodes_fts_insert AFTER INSERT ON summary_nodes BEGIN INSERT INTO nodes_fts(rowid, summary) VALUES (new.node_id, new.summary); END;
CREATE TRIGGER IF NOT EXISTS nodes_fts_delete AFTER DELETE ON summary_nodes BEGIN INSERT INTO nodes_fts(nodes_fts, rowid, summary) VALUES('delete', old.node_id, old.summary); END;
```

## Post-rebuild verification
```bash
sqlite3 ~/.hermes/lcm.db "SELECT COUNT(*) FROM messages_fts MATCH 'plan mode';"  # 例：1
sqlite3 ~/.hermes/lcm.db "SELECT COUNT(*) FROM nodes_fts WHERE nodes_fts='rebuild';"  # 例：1
```

## Notes
- If `DROP TABLE IF EXISTS` for shadow tables fails with `may not be dropped`, they're already gone (skip those lines).
- If `messages_fts` already exists, drop it first (line 12).
- FTS5 rebuild is fast and does NOT require VACUUM.
- After rebuild, restart gateway/dashboard to reload plugin.
