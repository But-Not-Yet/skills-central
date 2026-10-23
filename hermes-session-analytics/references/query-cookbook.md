# 会话库查询配方

全部以只读打开：

```python
import sqlite3
def sdb(p):
    d = sqlite3.connect(f'file:{p}?mode=ro', uri=True); d.row_factory = sqlite3.Row; return d
st = sdb('/home/alonzo/.hermes/state.db')
lc = sdb('/home/alonzo/.hermes/lcm.db')
```

## 会话概览（按主人消息量排序）

```sql
SELECT session_id, COUNT(*) n, SUM(role='user') nu, MIN(timestamp) t0, MAX(timestamp) t1
FROM messages GROUP BY session_id ORDER BY nu DESC LIMIT 30;
```

跨人格的 worker 概览（每臂一条）：

```sql
SELECT model, source, COUNT(*), SUM(tool_call_count), SUM(reasoning_tokens), SUM(output_tokens)
FROM sessions GROUP BY model, source ORDER BY 3 DESC;
```

## 模型归属：按 usage 区间给每条消息打标签

```python
ivs = []
for r in st.execute('SELECT model, billing_base_url, first_seen, last_seen FROM session_model_usage WHERE session_id=?', (sid,)):
    b = (r['billing_base_url'] or '').lower()
    kind = 'local' if ('127.0.0.1' in b or 'localhost' in b) else ('cloud' if 'openrouter' in b else 'other')
    ivs.append([r['first_seen'], max(r['last_seen'], r['first_seen']), kind, r['model']])
ivs.sort()

def kind_at(t):
    hit = [iv for iv in ivs if iv[0] <= t <= iv[1]]
    if hit: return hit[-1][2]
    prev = [iv for iv in ivs if iv[0] <= t]
    if prev: return max(prev, key=lambda x: x[0])[2]
    nxt = [iv for iv in ivs if iv[0] > t]
    return min(nxt, key=lambda x: x[0])[2] if nxt else 'unknown'
```

## 入库重复的折叠（统计前必做）

```python
rows = []
for r in raw:                      # raw = ORDER BY timestamp 的消息序列
    if rows and rows[-1]['role'] == r['role'] and (rows[-1]['content'] or '') == (r['content'] or ''):
        continue
    rows.append(r)
```

## 复读率（全文精确 hash，同会话内）

```python
import hashlib, collections
seen = collections.Counter()
for r in rows:
    if r['role'] == 'assistant' and len(r['content'] or '') >= 200:
        seen[hashlib.md5(r['content'].encode()).hexdigest()] += 1
dup_rate = sum(n - 1 for n in seen.values() if n > 1) / max(sum(seen.values()), 1)
```

真伪判别：对重复组看 `store_id` 间距与时间差——相邻几行且同秒 = 入库伪影（已折叠）。隔着几十行、差几分钟 = 真复读。

## 看板导出与各臂对照

```bash
hermes kanban list --archived --json > scratch/kanban_tasks.json
```

分组要点：`provider_override` 决定 base_url 类别（localllm / node-ii / custom → 本地，openrouter → 云端）。无 override 的 worker 卡 = coder 人格默认模型。`started_at`→`completed_at` 是墙钟，但不是因果关系证据（任务难度未配平，只能作观察）。

## GGUF / 元数据

看 KV 预算请用 `local-open-weight-model-selection` 的 `scripts/gguf_kv_budget.py`。本技能只管会话数据。
