---
name: hermes-session-forensics
version: 1.0.0
author: Nekonya (小喵)
license: MIT
description: 做本机会话的行为/用量分析与消息重放取证时加载；基础设施故障走 hermes-local-ops-troubleshooting。
metadata:
  hermes:
    tags: [hermes, telemetry, sqlite, analysis, forensics]
    related_skills: [hermes-local-ops-troubleshooting, lcm-summary-tuning]
---

# Hermes 会话遥测取证（行为与用量分析）

## When to Use

主人要分析本机会话数据时加载。典型问题：「分析我和 agent 的交互模式」「对比两个模型/两臂的行为」。「统计用量、会话生命周期、轮换」「查某模型从什么时候开始退化」「误删了会话能不能找回」也算。本 skill 管**从本机数据里取证出数**。基础设施排障走 hermes-local-ops-troubleshooting。

## 数据源地图（权威度从高到低）

| 存储 | 路径 | 给什么 |
|---|---|---|
| state.db（每 profile 一份） | `~/.hermes/state.db`、`~/.hermes/profiles/<p>/state.db` | `sessions` 表：每会话 model、started/ended_at、message_count、tool_call_count、api_call_count、input/output/reasoning_tokens、source（desktop/kanban/oneshot）、profile_name、title。`session_model_usage` 表：按（会话 × 模型）记 billing_base_url、first_seen/last_seen、api_call_count、token 分项，是**模型归属的唯一可用区间源** |
| lcm.db（插件库） | `~/.hermes/lcm.db` | `messages` 表：逐条 role/content/tool_calls/timestamp。`metadata` 表：compaction_telemetry |
| 看板 | CLI `hermes kanban list --archived --json` | 卡片状态、model_override/provider_override、started/completed_at。worker 会话在对应 profile 的 state.db（source='kanban'） |
| 日志 | `~/.hermes/logs/agent.log` | 派发/完成/错误行 |
| LCM prompt 快照 | `~/.hermes/cache/scratch/prompt_snapshot/<session_id>/turn_<N>.json` | 每轮完整 prompt 回放（schema `lcm-prompt-snapshot/v1`）。**正文在 `messages[].row.content`，顶层 `content` 恒为 None**——按顶层读会读出满屏 None。末轮文件=整场对话全量。主人点名某会话 ID 要看内容时先试这里；只在 scratch 存活（闲置 24h 被清），过期回落 lcm.db。**点名 ID 未必是当前会话**——读快照顶部 `session_id`/`platform` 字段对身份再下结论，别拿当前会话 ID 恰好相符就当同一场（desktop 与 TUI 会话可以同名同时段并行） |

`~/.hermes/kanban/kanban.db` 可能是 **0 字节死文件**，别从它读，用 CLI。

会话删除只清 state.db（`sessions` 行 + 名下 `messages`），**lcm.db 的 `messages` 按 session_id 完整存活**——找回被删会话优先去 lcm.db，见 `references/session-recovery.md`。lcm.db 另有每日快照 `~/.hermes/lcm.db.daily.YYYYMMDD` 做兜底。

## 四条口径铁律（踩过才知道）

1. **`sessions.model` ≠ 当时在跑的模型**。会话可中途换模型，该字段只是某时刻快照。逐消息归属必须用 `session_model_usage` 的 [first_seen, last_seen] 区间 + `billing_base_url` 判本地/云端（127.0.0.1/localhost/moa://local = 本地。openrouter/api.* = 云端），子臂按 base_url 再拆。候选会话筛选可以用 sessions.model，**出数的归属必须走区间**。
2. **compaction_telemetry 的 model 是摘要器，不是聊天模型**：拿它判聊天模型会张冠李戴。
3. **lcm.db 的 timestamp 是入库时刻，不是发送时刻**。同一轮 user/assistant 常同毫秒 → **响应延迟/回合墙钟从这套数据里测不出来**，如实标「数据限制：不可测」。不拿假数字顶替。
4. **lcm.db 有入库重复**：相邻行可能同 role 同 content（含 0 字节工具载体行）。统计前先折叠相邻完全相同行。但**跨轮隔分钟级的同文重发是真现象**，不是重复摄入，别一起折叠掉。

## 度量定义与陷阱

- **工具调用频率**：用 lcm 的 `tool_calls` JSON 长度计数。分母写清是「assistant 消息总数」还是「含工具的消息数」，混用会出 >100% 的假比率。轮的口径 = 两条主人消息之间。
- **思考长度**：**本地服务多数不上报 reasoning token**。content 里也没有 think 标记（本机全库零出现）→ 只有 `session_model_usage` 里 reason>0 的调用能测，其余标「未上报」。可引外部基准做方向性锚点，不许当精确值。
- **会话时长**：desktop 会话挂着不关，`ended_at − started_at` 是空闲膨胀值。算每小时速率要么用首末消息的活跃跨度，要么干脆不用。
- **复读/退化**：逐字重复率 = 同会话内 ≥200 字 assistant 回复的全文 hash 重复占比（窗口 7200s）。**必带时间轴**：同一模型在不同引擎配置时代的数字不可混用（本机实例：引擎修复前 71%、修复后 0%）。报退化先查是不是引擎史，别归因给模型。
- **每模型对比必须防混杂**：量化档、引擎配置。任务难度任一不同就是混杂（跨模型比工具调用准确率时，不同量化档 = 不可归因）。难度不配平的对比只能报观察，不能报因果。

## UI 顺序错乱 / 消息重放（active-row 取证）

桌面端把旧消息画到队尾、模型回复却不对应它时，先按宿主重放查，不要先怀疑插件载体回插。

1. 查 `state.db.messages`：`count(*)`、`sum(active)`、按 role/active 分组。
2. 对可疑消息按 `message_uid` 或原文精确匹配，看 `active`、`display_order`、`timestamp`；同一 `message_uid` 可能有多份副本，只有一份 active。
3. active 副本的 `display_order` 若等于新行 id，而其它重放副本保留原 `display_order`，UI 按 order/id 排就会把它推到队尾。
4. 查 `lcm_inspect` 的 `ingest_reconciliation` 是否出现 `replayed durable tail`；查 lcm 消息的 timestamp 是否成批落在同一秒。
5. hidden user 消息（后台进程 heartbeat、`async_delegation_complete`）可能是触发源；它们被写进会话后，宿主可能重放 durable tail。停掉这些来源，不要用它们做回执。
6. `assembly_probe` 的 index 0 若反复出现旧话题的 `[Recent Summary ...]`，那是另一个 summary carrier 污染，不是同一条消息重复。先用 `prompt_snapshot` 核 wire，再查 `summary_nodes.session_id` 是否属于当前会话；`assembly_probe` 是 post_llm 历史，不是 wire。详见 `references/summary-carrier-wire-forensics.md`。

修复：先备份 `state.db`；按 `message_uid` 保留 active 副本并把 `display_order` 回填原位置，或走宿主修复/新会话；不要手删行。详细 SQL 与修复检查单见 `references/message-replay-diagnosis.md`。

## 外部评审一场会话（行为审查，不是用量统计）

主人点名一个 session_id、要「外部评审」时，按这个顺序：

1. **先计数再读文**：user/assistant/tool 三条总数、时间跨度、工具名分布。轮 = 两条 user 消息之间。
2. **全量读原文**：`lcm_load_session` 分页或只读 sqlite；摘要块以 user 形态出现时只当索引，不当证据。
3. **行为信号只做客观计数**：
   - 用户纠错轮：人工逐条读 user 首句，标「纠错/质疑/看不懂」，给比例。
   - 助手撤回语言：`改口/认账/拔高/驳回` 的出现次数与涉及轮次。
   - 静默丢失：连续 user 消息之间没有 assistant/tool 行；同一问题重复发送。
   - 英文兜底串/空回复：以 assistant 形态出现的系统错误串。
   - 全称词：`全部/已/均/从未` 的出现次数，配合撤回次数看「声明式验收」。
4. **模型归属**走 `session_model_usage` 区间；不要用 `sessions.model` 贴整场标签。
5. **工具面**：按 function name 计数；同一 `(name,args)` 重复、非零退出、traceback 都记下来。
6. **交付**：问题清单（现象/证据/根因/整改）+ 外部依据（只列核过编号的）+ 验收判据；每条证据带轮次或 store_id。

具体查询与脚本形状见 `references/agent-behavior-review.md`。

## 项目进度考古（「实验 X 进行到哪了 / 有哪些成果」类问题）

数据源优先级从高到低，跳级用就是翻车路径：

1. **看板 live 态**：`kanban_list` 按 status 分趟拉（todo/blocked/running 各一次，limit 拉满），这是任务状态的唯一现值源。主人说「从看板看」就照办，别先淹进会话检索。
2. **项目根定位三件套**：README / 交接卡 / 待办与必读（项目目录里找同名文件）。它们是带日期快照，引用任何一条前先当场验活。
3. **git log 断日期争议**：`git log --pretty='%h %ad %ci %s' --date=...`。历史重建仓的分桶提交只回填**作者日**，实时提交 author date 与 commit date 双双现值——日期归属争议用双日期字段实锤，不靠文件 mtime 或记忆。
4. **裁决状态先 grep 裁决链**：说「X 待主人裁决」之前，先在 `.hermes/plans/` 与档案里 grep 该编号/议题——冻结件常带「按草案原文批准」字样，裁决后没人回头改旧交接卡的「待裁」行。旧交接文件里的「待拍板」大概率已经过期。
5. **LCM 检索是最后手段**：跨会话 `lcm_grep` 命中常是摘要回放重复噪音，只当线索，数字判据一律回文件原文。

报告成果清单时逐条带出处（文件:行），且区分「已终态 / 挂了卡未跑 / 只有草案未立项」三档——预注册草案落盘不等于实验跑过，脚本缺失（ls 核对）直接证明未实施。

## 汇报纪律

- 逐条数字给「口径 + 范围 + n」。全称词（全部/从未）配穷尽性核查或收窄（域内检察见 delivery-critic-gate 闸 A）。
- 采样窗口说清是抽样还是全量。启发式分类（正则）不要冒充语义标注：语义判断要么人工逐条读，要么明标「启发式」。
- **被审 agent 的自我承认、摘要块、上一轮汇报都是「会话自述」，不是独立证据**：能回 store_id/文件/commit 的必须回；回不到的在正文标「会话自述，未独立核」。不要把「它自己承认了」写成「已核验」。
- **「全读」只用于真正逐条读全文的角色**：工具结果只读前 N 字、只按错误标记抽样的，必须在范围里写明；否则「原文全读」是越权断言。
- 起出数前先报意图与口径，再动手。

## 深度

`references/model-behavior-comparison.md`：两模型/两臂行为的对照 recipe（指标定义、可执行查询片段、混杂处理）。

`references/session-recovery.md`：误删/丢失会话的找回 recipe（存活面判定、lcm.db 导出、回插 state.db 的字段要求）。

`references/agent-behavior-review.md`：外部评审一场会话的取证 recipe（轮次切分、行为信号计数、报告模板、口径陷阱）。

`references/message-replay-diagnosis.md`：UI 顺序错乱/消息重放的 SQL 取证与修复检查单。

`references/summary-carrier-wire-forensics.md`：跨会话 summary carrier 的 wire 取证、污染窗口与修复边界。
