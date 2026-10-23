# 生产 llama-server 行为探针模式（已验证）

## logit_bias：施加点与读法

- 先 curl /props 读采样链：logit_bias 挂在 **penalties 段（top-k/top-p 之前）**——正偏置是 logit 空间的绝对增量，softmax 前生效。够强的正偏置必然存活到采样终点，EOS 检测在采样之后（forced token 不进输出文本）。
- 正向阶梯（+1/+2/+5/+10/+20/+50/+100）× n=5/档、温度 0、seed 固定。**crossover 档位 = 模型分布对该 id 的回避强度**（第一个定量读数），要二分细化就往两档之间补发。
- 负向禁音（证「决策在模型」）与正向强制（证「执行在机构」）必须**双向夹击**才算闭合。单向禁音有「想说被禁 / 本不想念」的双向不可辨认问题。
- 施加场景选**模型本不想说目标 id 的普通问答**。在模型自然要说它的场景（复述）加偏置测不出东西。
- 靶 id（eos/bos）从 GGUF 头读（tokenizer.ggml.eos_token_id），不从文档假设。

## finish=stop 的歧义（ChatML 系）

ChatML 系的 eos_token_id 常与被测控制标记 id 是同一个——**自然收尾与强制截断的 finish_reason 都是 stop**。截断判据走内容完整性（对照无偏置基线的完成度），不走 finish_reason。

## 稳定性复跑要扫 seed

- llama.cpp 的 seed 语义：同 seed + 温度>0 **仍是零方差回放**——测分布稳定性必须每发换 seed（如 seed=1000+序号）。
- 方差真实出现（输出在两态间抖动）才证明不是 seed 回放的假稳定。判据预注册为「有方差后触发率 ≥ 阈值」。

## 产出纪律

- 每档原始记录落 .jsonl（逐发追加），判读另写 .md：结果表、判据命中与否。诚实边界（否定的判据也是数据，记录在案）、预算计数。
- 同一实验的对照臂先想清楚再跑。单读数区分不了两个机制时（如「标记特异回避」vs「eos 分布尾部普遍性质」）。补对照臂比多跑主臂信息量大。

## 收尾 margin 实测（logprobs）

- 普通问答带 `logprobs: true, top_logprobs: 5`：收尾步 top1（eos）对 top2 的 logprob 差 = 自然收尾强度。生成中途目标 id 是否进 top-5 = 中途回避距离（与正 bias crossover 互为印证，两读数来自同一枚硬币）。
- 用途：给负向 bias 定安全窗口。**实测结论：对「标记 id 兼任 eos」的场景窗口不存在，勿再试**——诱导侧「模型明确要说该 id」时确定性 >20 logit（-20 也压不住），收尾侧要 bias ≤-10 才崩（-5 尚可。短答案收尾 margin ~4 是单场景读数，长回复 margin 更大）。两侧约束差一个量级，别硬调参数。阶梯扫描配方（0/-5/-10/-15/-20 × 诱导/短答/长文 × n=3，判据=诱导场景 dead=0 且收尾场景 complete=3/3）见 references/session-truncation-forensics.md。

## 模板层取证与 overlay（/props chat_template）

- `/props` 除采样链外还返回 `chat_template` 全量字段：模板内建提示词（terse 风格层、工具 MUST 条款、preserve_thinking 历史渲染）全在里面。行为「玄学」时先提取落盘、冻结原件，再谈改。
- 编辑规程、条款文本设计。沙盒渲染验证（jinja2 多用例 + 程序化位置断言）与 `--chat-template-file` 部署回滚步骤见 references/chat-template-overlay.md。
- 生产是 minja（非 jinja2）：沙盒通过 ≠ 生产通过，最终以 llama-server 实际加载 + /props 复查为准。
