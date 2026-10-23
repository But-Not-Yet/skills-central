---
name: research-kb-usage
description: "数学/控制论/信息论/动力学问题的检索纪律：必须先查 research_kb，引用来源，禁止凭记忆作答。"
version: 1.0.0
---

# research_kb 使用纪律

当用户提出数学领域问题（定义、定理、公式、证明、综述、对比）时，执行以下纪律：

1. **检索优先**：任何数学 claim 都必须先调 `search_knowledge` 找证据，不凭记忆回答。复杂问题（写综述、对比 X 和 Y）需要多次检索不同子主题，不要一次检索就答。
2. **引用来源**：每条引用必须给出 `source` 和 `url`，格式：
   > [source: nlab, url: https://ncatlab.org/nlab/show/Lyapunov+function]
3. **chunk_text 是证据不是答案**：只能复述检索到的片段，不能脑补延伸。chunk 里的 LaTeX macro 读不通时意译补全（如 `\geq` → 「大于等于」）。`$...$` 是 inline 数学、`$$...$$` 是 display 数学，回答时保留 LaTeX 语法不转纯文本。
4. **空结果诚实声明**：检索 0 结果或 top1 score < 0.4 时，告知用户「知识库里没找到，建议换措辞或加来源」——不要瞎编。
5. **多源对比优先**：命中多个 source（nLab + proofwiki + 教材）时列多源视角，不只引一家。
6. **已知数据缺口**：无 source coding theorem、无 arXiv 论文、PlanetMath 含非数学条目——遇这些主题明确告知「覆盖不足」。
