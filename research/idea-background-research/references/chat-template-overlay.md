# 聊天模板 overlay 注入与位置学（llama-server，已验证）

用途：往生产 llama-server 的对话模板注入/修改常驻指令（纪律条款、风格约束）。或诊断「模板内建提示词」造成的行为异常（回复偏干、提前 abort、思考回灌）。不改 GGUF：启动参数 `--chat-template-file` 覆盖，删参数即回滚。

## 位置学（先记这条）

- **文本越靠后，权威越强**（recency。Lost in the Middle, arXiv 2307.03172：上下文首尾权重最高、中段骤降）。要强施加的常驻指令放整个 system 块的**收尾**。可注入文本里最强的可行位（其后只剩对话消息与生成提示）。别按「放开头更显眼」的直觉设计——那是弱位。
- 应用例：token 占位符纪律属长期常驻 → 注入模板 system 尾。不放 SOUL（system 头部，最弱位）、不放 memory（头部 + 字符预算限制）。

## 模板结构（生产定制版实查）

- 提取：`curl -s http://<host>:<port>/props` → JSON 的 `chat_template` 字段（30K 字符级）落盘分析。**先冻结原始副本**（回滚与对照用）。模板首行 `template_version` 变量可自查版本。
- system 块是**单块**，内部顺序：`[reasoning_instructions] → [tools 定义 + MUST 强制条款（有工具时）] → [_sc = 调用方 system + 内建 terse 提示]`。生成提示以 assistant 头 + 预填 think 开标签收尾（thinking 关时注入空 think 对）。
- 内建提示词与控制开关（行为玄学先查这些）：
  - **terse 提示**（英文 lead + 中文 core。kwarg `terse` 默认 true，拼在调用方 system 之后）：强加「答案先行、只留必需」风格——「回复偏干」的表象常是它，不是人格文件失效。可 `chat_template_kwargs: {"terse": false}` 关闭。
  - **工具 MUST 条款**：强制式措辞（必须立即输出工具调用、不得有对话文本）——社区同病症定位的「逻辑陷阱」。模型无法满足时会拿 abort 当合规出口。kwarg `suppress_tool_instructions` 可抑制。
  - **preserve_thinking / preserve_reasoning 默认 true**：历史 reasoning 被完整写回 think 块。「思考有内容＋正文空」的历史样本被反复渲染成「思考完直接收尾」的示范（自我强化循环）。
- **minja 提醒**：生产用 llama.cpp 的 minja（非 jinja2）。编辑只做 set/if 同类构造。jinja2 通过 ≠ 生产通过，最终以 llama-server 实际加载 + /props 复查为准。

## overlay 编辑规程

1. 抽取 + 冻结原始（见上）。
2. 注入段拼在组装变量**最后**（本部署为 `_sc` 的 terse 之后）：terse 拼装块后追加同构 if 块。`_sc` 为空时纪律段直接顶上。
3. **kwarg 开关**（模板内建 terse 同款模式，照抄）：`{%- set _disc_on = token_discipline if token_discipline is defined else true %}`——默认开、传 false 完整回落原行为。对照实验臂干净。
4. **条款文本设计**：
   - 条款每轮随请求发送，**自身绝不能含原始形态、也不写其名称**——否则条款自己成了诱发源。用占位符（__IM_END__）+ 类别描述（「ChatML 族回合结束标记」）指代。
   - 讲后果不讲内部术语（「推理引擎会把它当作消息立即结束信号」>「EOS 字样」）——让模型理解因果。不引导深加工。
   - 义务用**正向措辞**（「必须输出正文内容」>「不要直接结束回合」），防反弹效应。
   - 保留 chr() 构造条款（覆盖 agent 写代码落盘字面量场景）。
5. **沙盒渲染验证**（部署前，本机 jinja2）：parse + 5 类强制用例渲染——有工具/无工具/空 system/开关 off/terse off。程序化断言注入段位置：find 标记 → 其后第一个块 opener 必须是消息角色。且标记与最近 im_end 之间无其他开块 → 开关 off 用例断言标记消失。程序断言比人眼可靠。
6. 部署：`--chat-template-file <path>`。重启后 `/props` 复查 chat_template 含新文本。回滚=删参数重启。
7. **判据**：纪律是否真生效走对照实验（开关两臂 × 真实诱发场景重放）——「加载成功」不是成效证据。
