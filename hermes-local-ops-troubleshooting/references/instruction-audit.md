# 指令面体检（system prompt 体量 + 技能索引描述）

## 一、用真实请求转储测体量

- 样本：`~/.hermes/sessions/request_dump_*.json`（取最新即可；结构 = `request.body.{messages, tools}`；system = `messages[0].content`）。
- 分段（按标记切）：`You run on Hermes Agent` / `## Skills` / `MEMORY (your personal notes)` / `USER PROFILE (who the user is)` / `Active Hermes profile` / `Conversation started` / `# Hermes runtime environment`。
- 数 token：`llama-tokenize -m <Qwen3.8 gguf> --stdin --show-count`（CPU 二进制 `~/Documents/LLM/llama.cpp/build/bin/llama-tokenize`；输出末行 `Total number of tokens: N`，无需 GPU）。字符数精确，token 数 = Qwen 词表近似，汇报时标注口径。
- 英中配比：CJK 正则 `[\u4e00-\u9fff\u3000-\u303f\uff01-\uff5e]` 与 `[A-Za-z]` 逐段计数。
- 参考量级（本机单会话实测）：固定前缀 ≈23K token；工具 schema 约占一半；中文占比不足一成（大头是上游英文层：内置纪律段 + 工具 schema）。

## 二、技能索引的描述从哪来（改描述前必读）

- 普通技能（skills 树）：索引取 SKILL.md frontmatter 的 `description:`；改完**当场生效**（`skills_list` 同进程即刷新）。
- 插件技能（索引 category=plugin，如 `hermes-lcm-x:hermes-lcm`）：描述来自**插件注册代码**的 `register_skill(..., description=...)` 实参，不是 SKILL.md——只改 SKILL.md 索引不变；改注册串后需**进程重启**才生效（注册发生在插件装载时）。
- 批量改法：先 `tar czf ~/.hermes/skills_backup_*.tar.gz -C ~/.hermes skills`（备份，13MB 量级）→ 旧描述→新描述映射、按 frontmatter `^description:` 行**整行**精确匹配替换（新值用双引号包裹，文本内避免英文双引号）→ 全量 parse 校验（117 个活跃 SKILL.md，应 0 异常）→ `skills_list` 复核。
- 描述句式（本用户）：中文、「触发+能力」（「……时使用」），技能名与术语留英文；单条短句，不写营销词。
