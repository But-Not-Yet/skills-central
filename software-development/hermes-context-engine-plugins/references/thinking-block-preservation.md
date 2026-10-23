# 思考块保留与剥离：官方规则、客户端实践、我们该怎么做

## Anthropic 硬规则：只有一条，落在末轮

出处 = Claude Code issue #14264 复现的 API 400 原文（复现文本即官方校验信息）：

> When thinking is enabled, a **final** assistant message must start with a thinking block (preceding the lastmost set of tool_use and tool_result blocks). **We recommend** you include thinking blocks from previous turns. To avoid this requirement, disable thinking.

- **硬要求**：最后一个 assistant 消息必须以 thinking 块开头，且位于最末一组 tool_use/tool_result 之前。
- **软建议**：「We recommend」——更早轮的历史 thinking **可省略**。
- 直接推论：剥掉「更早轮」的思考不违反硬规则。把「recommend」读成「必须」会得出错误的「会 400」，是本技能库先前犯过的错。

## 按模型的历史 thinking 保留政策

官方 extended-thinking 文档「thinking block preservation by model」：4.6 及以后**保留**历史轮 thinking 且按**输入计费**；4.5 及更早服务端**剥离**。客户端若剥旧思考，省的就是这部分输入计费，且不触硬规则——属成本权衡，不是缺口。

## Anthropic 官方客户端（Claude Code）怎么做

源码 `src/utils/messages.ts`，三种变换全部是 400 规避、不是成本优化：

- `filterOrphanedThinkingOnlyMessages` —— 删掉「纯 thinking、且没有同 id 正文兄弟可合并」的孤儿 assistant 消息（compaction 切片会造出这种，签名不匹配 = 400）。
- `filterTrailingThinkingFromLastAssistant` —— 注释白纸黑字「The API doesn't allow assistant messages to end with thinking/redacted_thinking blocks」，剥末条末尾连续的 thinking 块。
- `stripSignatureBlocks` —— 只在线索签名失效时（例如 `/login` 换了凭据，签名绑旧 key）剥 thinking/redacted_thinking/connector_text。

外加 `src/utils/betas.ts` + `src/constants/betas.ts`：`CONTEXT_MANAGEMENT_BETA_HEADER = 'context-management-2025-06-27'`，对 `modelSupportsContextManagement()` 为真的模型带此 beta **请求保留**历史 thinking。

要点：CC **不做**「逐轮剥旧思考省 token」。

## 思考剥离层：边界对，关口在粒度

- **边界**：「只保留最后一个 assistant 的思考」与硬规则一致。
- **粒度（真关口）**：字段级 `pop('reasoning_content'|'thinking'|...)` 删整块思考，删不掉 thinking 文本**内部**的行内标记（开/闭不成对）。该标记留在 `content` 里，下游（模板/解析器/别的模型）读到就把它后面的正文误判成思考——这是泄漏的放大器。
- **修法属标记级卫生**：入库/回放边界加「成对保证」（开闭计数不等则拒绝入库或先修复），所有剥离路径加「残余清扫」（闭合对删完后把残余开/闭孤儿一律删掉）。落点在组装层与内层引擎的入库/升级路径，**不在**请求侧思考剥离层。

## 严格侧 vs 回显族

- 严格侧（本地 llama.cpp/Qwen 之类）：组装层已整体剥 `reasoning_content`，请求侧思考剥离层 = 验证性 no-op。
- 回显族（Kimi/DeepSeek）：要求每条 assistant 带 `reasoning_content`（空串 400，用单空格占位），剥除有害。
