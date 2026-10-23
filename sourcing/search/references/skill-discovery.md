# 技能触发为什么失败——外部证据与处方

来源：Anthropic 官方文档、官方 `skill-creator/SKILL.md`、社区对官方材料的提炼、以及本用户 2026-10-06 的实测。

## 一、根因：undertriggering（欠触发）

Anthropic 官方 `skill-creator/SKILL.md` 原文：

> Note: currently Claude has a tendency to "**undertrigger**" skills — to not use them when they'd be useful. To combat this, please make the skill descriptions a little bit "**pushy**".

→ **技能没被加载不是偶然疏漏，是模型层面已知的、系统性的倾向。** 靠「下次记得」无效，必须改文本。

## 二、机制：描述是唯一的选拔信号

启动时只预载元数据（name + description）；SKILL.md 只在命中后才读。

官方原话：

> The description is critical for skill selection: Claude uses it to choose the right Skill from potentially 100+ available Skills.

装载是纯 in-context 决策——代码层面没有 embedding、没有分类器。**描述没命中，技能等于不存在。**

## 三、处方（四条）

1. **触发词前置**。description 的第一句必须自洽——万一被截断，触发语义不能丢。
2. **写明「即使…」**。列出显式触发场景，并用「即使用户没明说 X」封住欠触发的缝。
3. **加排除条款**。社区（Ruben Hassid）称其为描述里最重要的一行：「正面触发把技能拉进来，排除条款把它推出去，两者抢同一份预算。」
4. **预算意识**。开放 Agent Skills 规范中 description 上限 1024 字符；Claude Code 把 `description` + 可选 `when_to_use` 合计截断在 1536。**本机实测：Hermes 运行时索引不截断**（137 字符描述完整回显）；`hermes-agent-skill-authoring` 里的 60 字符硬线是**仓库投稿/docs 标准**，与本机运行时不矛盾。

## 四、可套用的描述公式

```
<做什么，触发词前置，前 ~50 字符自洽句>。
只要<显式触发场景 A / B / C>，就主动加载，即使用户没明说<关键词>。
<核心纪律一句>
不用于<不该触发的场景>。
```

实例（改前 → 改后）：

- `给答案与文档配可核验引用时使用。`
  → `给答案、报告、文档配可核验引用时使用。只要你的输出引用了任何外部来源，就主动加载，即使用户没要求标注出处。逐条登记来源、内联编号、交付前跑 verify。不用于纯对话或仅凭内部知识作答的场景。`

- `用 lm-eval-harness 跑 LLM 基准时使用。`
  → `用 lm-eval-harness 跑 LLM 基准时使用。只要要测 MMLU、GSM8K 这类分数，就主动加载，即使用户只说「对比一下这两个模型」。`

## 五、B 类失败：加载了却不执行

描述修好只解决「不加载」。另一类失败是**加载了但当摆设**。

- 对比：`grounded-citations` 有一个必须跑的脚本（`verify`）——那是**强制函数**，纪律变成动作。
- 反面：「先跑反证再开口」这种语帚，没有对应动作，加载了也是摆设。

**处方**：每条纪律后面必须挂一个**可跑的动作**（一个脚本、一个探测命令、一个交付前必跑的检查）。挂不上的纪律，改写或删掉。

## 六、跨会话防漏：两条明文动作

来自 Claude Code system prompt 的写法：

> You should **proactively** use the Task tool with specialized agents **when the task at hand matches the agent's description**.

落地成本用户侧的两条：

1. **开工前点名**：任务开始时，把手上的事与技能索引描述逐条比对；命中先加载再动手。
2. **收尾自查**：「有没有哪个 skill 本该防住这次的坑？」答非空 = 回去补。
