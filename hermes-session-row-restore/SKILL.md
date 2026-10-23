---
name: hermes-session-row-restore
version: 1.0.0
author: Nekonya (小喵)
license: MIT
description: 误删的 Hermes 会话要回插侧边栏时用。动 state.db 手工写会话行都算。
metadata:
  hermes:
    tags: [hermes, sqlite, recovery, state-db]
---

# 误删会话回插 state.db

## When to Use

主人说「误删了会话/能把会话找回来吗」，或任何要往 state.db 的 sessions/messages 手工写行的场合。

## 关键事实

- 桌面删会话 = 硬删：state.db 的 `sessions` 行与 `messages` 行都清掉，CLI 无 undelete。但 **lcm.db 不归会话删除管**——LCM `messages` 表按 session_id 留有全量原文（无损），这是回插的正源。
- 主人回退（rewind/branch）产生的分支会话（sessions 里还在，`model_config._branched_from` 指原会话）带删除前的整行原生消息（reasoning/message_uid 全在），LCM 没有这些字段——缝合序：分支原生行整行复制在前，LCM 尾部增量按 role+content 计数去重补在后；LCM 注入的 `[Recent Summary` / `[Session Arc Summary` 行跳过，LCM 装配会再生成。
- 会话行重建字段取法：model/cwd/system_prompt_hash 从分支行抄；`system_prompts` 表按 hash 的行通常还在（resuming 靠它）；`title` 有唯一索引要先查重。
- 写库时机：gateway 在跑时必翻车（锁/缓存）。两服务 `Restart=always`——脚本中途非零退出会被 systemd 自动拉起，别以为服务还停着。
- 备份：`sqlite3 "file:$DB?mode=ro" "VACUUM INTO '快照'"` 在线事务级一致，配 sha256；2.3G 库约几十秒。

## 坑（实踩）

- 多行 INSERT 用 `executemany`，写成 `execute` 报 "Incorrect number of bindings (statement uses N, there are N×行数 supplied)"。事务内异常自动 rollback，库不受污染，可直接重跑。
- 回插前先回读 `sessions WHERE id=?` 判存在，脚本做成幂等；备份按时间戳命名不覆盖。
- `messages` 表有触发器自动补 message_uid/display_order，插入时留 NULL 即可；display_identity 不补问题不大（读路径会 reconcile）。

## 成品

本实例脚本：`~/.hermes/scripts/restore_session_20261018.sh`（外层：dry-run→停服务→等 inactive→VACUUM 备份→回插→双闸回读→起服务）+ `restore_session_20261018.py`（缝合逻辑）。换个会话 ID 改常量即可复用。
