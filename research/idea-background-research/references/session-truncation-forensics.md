# 会话层吞消息取证（Hermes + llama-server 栈，已验证配方）

诊断目标：回复被截断/整条变空、怀疑控制标记触发时的定因与防线决策。

## 1. 分类：先分清「真吞」与正常形态

- state.db 只读打开（`sqlite3.connect("file:...state.db?mode=ro", uri=True)`），messages 表关键字段：`finish_reason`、`content`、`reasoning_content`。
- 真吞 = `role='assistant' AND finish_reason='stop' AND (content='' OR content IS NULL) AND length(reasoning_content)>0`。
- `finish='tool_calls'` 且 content 空是**正常纯工具调用消息**，不计入。`finish='stop'` 且 content 完整、仅显示层吞字是另一回事（丢字符不丢消息）。

## 2. 断点与字面量在场率：区分两种死法

- 读 reasoning_content 尾部 300-400 字符：mid-word 戛然而止 = 流被 EOS 掐死。
- 在全部真吞消息的 reasoning 里搜完整形态（搜索词用 chr() 构造后参数化进 SQL，参数文本零字面量）。**字面量在场率低**（仅零头几条）是「单 token 直接预测」的签名——skip_special_tokens 把预测出的控制 token 从文本剔除，不留痕。**含字面量的消息反而多存活**（拼零件路径不触发控制）。
- 对照组：`finish='stop'` 且 content 完整的消息里搜同形态——有存活样本含它，就证明书写本身不必然致命。纪律失误 ≠ 会话死刑。

## 3. 执行模型溯源：以日志为唯一权威

- agent.log 的 `API call #N: model=... provider=...` 行是「哪台模型跑了哪轮」的唯一权威。不要用记忆里的切换通知/会话系统提示重建时间线——通知发出≠生效，也可能被主动切回。人和模型都会记错因果。
- Hermes 中间层先排除再怀疑它：源码树 grep（chr 构造的搜索词）确认无硬编码标记扫描。日志「Reasoning-only clean stop」是 Hermes 如实报告 EOS 掐死的流，不是它吞的。

## 4. 跨模型免疫探针：决定研究对话用谁跑

- 独立进程探测，被测模型死了不伤调用会话：bash 内 printf 拼接构造字面量（命令文本零完整形态）。`timeout 180 hermes chat -q "Repeat exactly this string and nothing else: $F"`。hermes 首启慢，第一次超时多半是启动不是死亡，重跑再计。
- 探针输出先 SAFE 化（竖线→¦）再进工具结果通道。跑 ≥5 发统计存活率。
- 判定：tokenizer_config.json 的 special tokens 列表无该形态 + 探针存活 + reasoning 里概念性处理该串不死 = **词表免疫**成立。词表无单 token 时模型只能拼零件，永不触发控制。
- openrouter 链路对「|>」可能丢 2 字符（输入输出两侧都见过）——量级小，别误判为截断。

## 5. 防线决策：先分型，再选线（全部实测，勿重走）

两类死亡机制不同、对策不通用——先判断任务属于哪类：

| 类型 | 触发 | 实测死亡率 | 有效对策 |
|---|---|---|---|
| **A 类·直接诱导** | 任务要求输出/复述该 token 的原始形态 | **确定性**（8/8、4/4。各类干预全无效） | 只有规避：任务设计永不要求原始形态。需要原始形态的实验走 API 脚本（chr() 构造 + JSONL 落盘） |
| **B 类·间接诱发** | 讨论相关概念时思考连带预测到它 | **概率性**（历史 129 条。同模型同日既存活也连死） | ①上下文密度控制（占位符纪律、摘要消毒）②死亡后续写恢复（人工续写实证 4/4） |

已实测否决（附机制理由，勿重跑）：
- **负向 logit_bias**：无安全窗口。A 类「说出该 token」确定性 >20 logit（-20 压不住）。正常收尾到 ≤-10 才崩——两侧约束差一个量级。
- **ignore_eos + 模板边界 stop 接管收尾**：EOS 被抑制后模型不走模板边界（不生成 start 侧），直接续写正文，收尾彻底失效。单标记 stop 又对「提及」与「收尾」一视同仁。
- **消毒 rc + 续写重试**：A 类 0/6 活（重试时任务仍要求说出它）。B 类人工续写 4/4 成功——**不要把 A 类的失败推广到 B 类**。
- **强化 system 纪律（连思考都要求用代号）**：A 类 0/6——提示管不到 token 层预测。它的价值在输出卫生与 B 类密度控制，不在救 A 类。

**词表硬标准（选执行模型的前置检查）**：模型词表里该形态若是单 token，A 类必死、B 类概率死。实测：Qwen 3.8 Flash Next 死、GLM-5.3 免疫（tokenizer_config 无该形态 + 复述探针 4/5 活）、MiMO V2.6 Pro 死（词表含该形态单 token）。要跑「必须提及该标记」的任务就先验词表，别等事故。

## 6. B 类放大器：历史结构污染与模板层（生产模板实查确认）

- Hermes 的「Reasoning-only clean stop → 把 rc 当响应返回」会把半截思考写回历史，等于在教模型「思考后即停」。可能自我强化 B 类发生率——治理点是改写这类历史条目而非原样回灌。
- 生产模板（从 /props 提取实查）三条机制成立：① `preserve_thinking` 默认 true——历史 reasoning 被完整写回 think 块。「思考有内容＋正文空」的死亡样本被反复渲染成「思考完直接收尾」的示范（自我强化循环）。② 工具 MUST 强制条款与调用方 system 同块——「无法满足时拿 abort 当合规出口」的逻辑陷阱。③ thinking 关闭时注入空 think 对（空块上下文偏差）。
- 社区同病症（Qwen3.5 修复版模板）的修法方向一致：改写历史渲染 + 放松强制式措辞。本栈治理路径：overlay 注入反截断纪律（渲染沙盒验证过的规程见 references/chat-template-overlay.md）。三项机制逐项对照实验、一次只动一个变量，判据=开关两臂重放死亡对比。
- LCM 压缩器本身是被测模型时（查 config 确认压缩器身份。本部署 auxiliary.compression 为同系 Qwen），摘要里复述字面量同样会死 → 摘要指令需带占位符条款。
