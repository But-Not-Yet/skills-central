# 外部评审一场会话：取证 recipe

用于「给一个 session_id，分析这个 agent 在会话里出了什么问题」。目标不是打分，是给出可回原文的证据链和可执行的整改。

## 数据源

- `~/.hermes/lcm.db` 的 `messages` 表：store_id、session_id、role、content、tool_calls、timestamp。只读 URI 打开。
- `~/.hermes/state.db` 的 `sessions` 与 `session_model_usage`：模型归属与用量。
- 会话原文分页：`lcm_load_session(session_id=...)`。摘要块只当索引，引用数字与状态必须回原文。

## 轮次切分

以 user 消息为界；一条 user 到下一个 user 之前的所有 assistant/tool 行算同一轮。

```python
rows = con.execute(
    "select store_id, role, content, tool_calls, timestamp "
    "from messages where session_id=? order by store_id", (sid,)).fetchall()
turns = []
for r in rows:
    if r[1] == 'user':
        turns.append({'u': r[2] or '', 'aid': [], 'tools': []})
    elif r[1] == 'assistant' and turns:
        if (r[2] or '').strip():
            turns[-1]['aid'].append(r[2])
        if r[3]:
            turns[-1]['tools'].extend(
                tc['function']['name'] for tc in json.loads(r[3]))
```

## 行为信号（只做客观计数）

- **用户纠错轮**：人工读每条 user 首句，标「纠错/质疑/看不懂」。不写正则打语义标签。
- **助手撤回语言**：统计 `改口/认账/拔高/驳回` 的出现次数与涉及轮次；再看这些轮里有没有「全部/已/均/从未」。
- **静默丢失**：连续 user 行之间没有 assistant/tool 行；同一问题重复发送。这是会话管道可靠性问题，不是模型推理问题。
- **英文兜底串/空回复**：以 assistant 形态出现的系统错误串；单列，不要混进模型行为。
- **工具面**：按 function name 计数；同一 `(name, args)` 重复、非零退出、traceback 分别计数；看最大单轮工具数。
- **摘要块**：以 user 形态出现的 `[Recent Summary (d0, node N)]` 等只当索引；统计它们出现的轮次与长度，别把其中的断言当证据。

## 报告模板

```
一、结论（三到五条，按伤害排序）
二、主要问题
   每条：现象（带轮次/引文）→ 根因 → 外部依据 → 整改
三、共同根因（一张因果链）
四、缓解路径（今天/本周/结构性）
五、验收判据（可量化）
六、立即执行清单
七、外部依据（编号 + 标题 + 编号/URL）
```

外部依据只列实际核过编号与标题的条目；工程博客要写发布日期。正文引用用 `[n]`，文末给完整清单。

## 口径陷阱

- lcm 的 timestamp 是入库时刻，不是发送时刻；响应延迟不可测，别拿 0.0s 当结论。
- 摘要块里的断言比原文更硬；引用前回原文，冲突以原文为准。
- 用户纠错轮必须人工读，正则会把「你确定？」「我有点晕」这类漏掉或误伤。
- 全称词计数是信号不是判决；要配撤回次数和具体引文一起看。
- 模型归属用 `session_model_usage` 区间；`sessions.model` 只是快照。
