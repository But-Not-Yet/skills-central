---
name: research-paper-writing
title: Research Paper Writing Pipeline
description: "写 NeurIPS/ICML/ICLR 机器学习论文时使用：从设计到投稿。只要要做实验设计、写论文、应对评审或投稿，就主动加载，即使用户只说「帮我把这篇论文整出来」。"
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [semanticscholar, arxiv, habanero, requests, scipy, numpy, matplotlib, SciencePlots]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Research, Paper Writing, Experiments, ML, AI, NeurIPS, ICML, ICLR, ACL, AAAI, COLM, LaTeX, Citations, Statistical Analysis]
    category: research
    related_skills: [arxiv, subagent-driven-development, plan]
    requires_toolsets: [terminal, files]

---

# 科研论文写作流水线

面向 **NeurIPS、ICML、ICLR、ACL、AAAI 与 COLM** 的、产出可发表 ML/AI 研究论文的端到端流水线。本 skill 覆盖完整研究生命周期：实验设计、执行、监控、分析、论文写作、评审、修订与投稿。

这**不是线性流水线** — 它是一个迭代循环。结果触发新实验。评审触发新分析。agent 必须处理这些反馈回路。

<!-- ascii-guard-ignore -->
```
┌─────────────────────────────────────────────────────────────┐
│                    RESEARCH PAPER PIPELINE                  │
│                                                             │
│  Phase 0: Project Setup ──► Phase 1: Literature Review      │
│       │                          │                          │
│       ▼                          ▼                          │
│  Phase 2: Experiment     Phase 5: Paper Drafting ◄──┐      │
│       Design                     │                   │      │
│       │                          ▼                   │      │
│       ▼                    Phase 6: Self-Review      │      │
│  Phase 3: Execution &           & Revision ──────────┘      │
│       Monitoring                 │                          │
│       │                          ▼                          │
│       ▼                    Phase 7: Submission               │
│  Phase 4: Analysis ─────► (feeds back to Phase 2 or 5)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
<!-- ascii-guard-ignore-end -->

---

## 何时使用本 skill

以下情况用本 skill：
- 从已有代码库或想法**开始一篇新论文**
- **设计并运行实验**以支撑论文论断
- **撰写或修订**论文的任意小节
- **准备投稿**到某个会议或 workshop
- **回应评审**，补实验或做修订
- 在会议格式之间**转换**论文
- **写非实证论文** — 理论、综述、基准或立场论文（见 [Paper Types Beyond Empirical ML](#paper-types-beyond-empirical-ml)）
- 为 NLP、HCI 或对齐研究**设计人工评测**
- **准备录用后交付物** — poster、talk、代码发布

## 核心哲学

1. **主动。** 交付完整草稿，而不是提问。科学家很忙 — 产出具体的东西让他们能反应，然后再迭代。
2. **绝不臆造引用。** AI 生成的引用错误率约 40%。务必以编程方式抓取。把无法核验的引用标为 `[CITATION NEEDED]`。
3. **论文是一个故事，不是实验的集合。** 每篇论文都需要用一句话说清的一个明确贡献。做不到，就说明论文还没准备好。
4. **实验服务于论断。** 每个实验都必须明确说明它支撑哪个论断。绝不跑与论文叙事无关的实验。
5. **早提交、勤提交。** 每批完成的实验、每次草稿更新 — 都带描述性信息提交。Git log 就是实验历史。

### 主动性与协作

**默认：主动。先起草，带着草稿提问。**

| 置信水平 | 动作 |
|-----------------|--------|
| **高**（仓库清晰、贡献明显） | 写完整草稿、交付、按反馈迭代 |
| **中**（有些歧义） | 写草稿并标出不确定处，继续推进 |
| **低**（重大未知） | 通过 `clarify` 问 1-2 个有针对性问题，再起草 |

| 小节 | 自主起草？ | 随草稿标注 |
|---------|-------------------|-----------------|
| Abstract | 是 | "把贡献表述为 X — 需要就调整" |
| Introduction | 是 | "强调了问题 Y — 有错就纠正" |
| Methods | 是 | "写入了细节 A、B、C — 补齐缺失的部分" |
| Experiments | 是 | "突出了结果 1、2、3 — 需要就重排" |
| Related Work | 是 | "引用了论文 X、Y、Z — 补上我遗漏的" |

**仅在以下情况停下来要输入**：目标 venue 不明、有多种互相矛盾的说法、结果似不完整、用户明确要求先审。

---

## 阶段 0：项目搭建

**目标**：建立工作区、理解已有工作、确定贡献。

### 第 0.1 步：探索仓库

```bash
# Understand project structure
ls -la
find . -name "*.py" | head -30
find . -name "*.md" -o -name "*.txt" | xargs grep -l -i "result\|conclusion\|finding"
```

找这些：
- `README.md` — 项目概览与论断
- `results/`、`outputs/`、`experiments/` — 已有发现
- `configs/` — 实验设置
- `.bib` 文件 — 已有引用
- 草稿文档或笔记

### 第 0.2 步：组织工作区

建立一致的工作区结构：

```
workspace/
  paper/               # LaTeX source, figures, compiled PDFs
  experiments/         # Experiment runner scripts
  code/                # Core method implementation
  results/             # Raw experiment results (auto-generated)
  tasks/               # Task/benchmark definitions
  human_eval/          # Human evaluation materials (if needed)
```

### 第 0.3 步：设置版本控制

```bash
git init  # if not already
git remote add origin <repo-url>
git checkout -b paper-draft  # or main
```

**Git 纪律**：每批完成的实验都带描述性信息提交。示例：
```
Add Monte Carlo constrained results (5 runs, Sonnet 4.6, policy memo task)
Add Haiku baseline comparison: autoreason vs refinement baselines at cheap model tier
```

### 第 0.4 步：确定贡献

写任何东西前，先讲清楚：
- **What**：这篇论文贡献的那一件事是什么？
- **Why**：什么证据支撑它？
- **So What**：读者为什么该在意？

> 向科学家提议："Based on my understanding, the main contribution is: [one sentence]. The key results show [Y]. Is this the framing you want?"（按我的理解，主要贡献是：[一句话]。关键结果显示 [Y]。这是你想要的表述吗？）

### 第 0.5 步：创建 TODO 清单

用 `todo` 工具创建结构化的项目计划：

```
Research Paper TODO:
- [ ] Define one-sentence contribution
- [ ] Literature review (related work + baselines)
- [ ] Design core experiments
- [ ] Run experiments
- [ ] Analyze results
- [ ] Write first draft
- [ ] Self-review (simulate reviewers)
- [ ] Revise based on review
- [ ] Submission prep
```

全项目过程中持续更新它。它充当跨会话的持久状态。

### 第 0.6 步：估算算力预算

跑实验前，估算总成本与时间：

```
Compute Budget Checklist:
- [ ] API costs: (model price per token) × (estimated tokens per run) × (number of runs)
- [ ] GPU hours: (time per experiment) × (number of experiments) × (number of seeds)
- [ ] Human evaluation costs: (annotators) × (hours) × (hourly rate)
- [ ] Total budget ceiling and contingency (add 30-50% for reruns)
```

实验运行时跟踪实际花费：
```python
# Simple cost tracker pattern
import json, os
from datetime import datetime

COST_LOG = "results/cost_log.jsonl"

def log_cost(experiment: str, model: str, input_tokens: int, output_tokens: int, cost_usd: float):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "experiment": experiment,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
    }
    with open(COST_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
```

**预算紧张时**：在投入全量 sweep 前先跑试点实验（1-2 个 seed、任务子集）。调试流水线用更便宜的模型，最终运行再换成目标模型。

### 第 0.7 步：多作者协作

多数论文有 3-10 位作者。尽早确立协作流程：

| 工作流 | 工具 | 何时用 |
|----------|------|-------------|
| **Overleaf** | 基于浏览器 | 多作者同时编辑、无 git 经验 |
| **Git + LaTeX** | 用 `git` + 为 aux 文件配 `.gitignore` | 技术团队、需要基于分支的审阅 |
| **Overleaf + Git sync** | Overleaf 付费版 | 兼得两者 — 实时协作 + 版本历史 |

**小节归属**：每个小节指定一位主作者。其他人评论但不直接编辑。可避免合并冲突与风格不一致。

```
Author Coordination Checklist:
- [ ] Agree on section ownership (who writes what)
- [ ] Set up shared workspace (Overleaf or git repo)
- [ ] Establish notation conventions (before anyone writes)
- [ ] Schedule internal review rounds (not just at the end)
- [ ] Designate one person for final formatting pass
- [ ] Agree on figure style (colors, fonts, sizes) before creating figures
```

**要尽早统一的 LaTeX 约定**：
- `\method{}` 宏，统一方法命名
- 引用风格：`\citet{}` 与 `\citep{}` 的用法
- 数学记号：向量用小写粗体，矩阵用大写粗体，等等
- 英式还是美式拼写

---

## 阶段 1：文献综述

**目标**：找相关工作、确定基线、收集引用。

### 第 1.1 步：确定种子论文

从代码库中已引用的论文入手：

```bash
# Via terminal:
grep -r "arxiv\|doi\|cite" --include="*.md" --include="*.bib" --include="*.py"
find . -name "*.bib"
```

### 第 1.2 步：搜索相关工作

**加载 `arxiv` skill** 做结构化论文发现：`skill_view("arxiv")`。它提供 arXiv REST API 搜索、Semantic Scholar 引用图、作者主页与 BibTeX 生成。

用 `web_search` 做宽泛发现，用 `web_extract` 抓取具体论文：

```
# Via web_search:
web_search("[main technique] + [application domain] site:arxiv.org")
web_search("[baseline method] comparison ICML NeurIPS 2024")

# Via web_extract (for specific papers):
web_extract("https://arxiv.org/abs/2303.17651")
```

可尝试的其他搜索查询：

```
Search queries:
- "[main technique] + [application domain]"
- "[baseline method] comparison"
- "[problem name] state-of-the-art"
- Author names from existing citations
```

**推荐**：安装 **Exa MCP** 做实时学术搜索：
```bash
claude mcp add exa -- npx -y mcp-remote "https://mcp.exa.ai/mcp"
```

### 第 1.2b 步：加深搜索（先宽后深）

一次扁平搜索（一轮查询）通常会漏掉重要的相关工作。采用受深度研究流水线启发的迭代式**先宽后深**模式：

```
Iterative Literature Search:

Round 1 (Breadth): 4-6 parallel queries covering different angles
  - "[method] + [domain]"
  - "[problem name] state-of-the-art 2024 2025"
  - "[baseline method] comparison"
  - "[alternative approach] vs [your approach]"
  → Collect papers, extract key concepts and terminology

Round 2 (Depth): Generate follow-up queries from Round 1 learnings
  - New terminology discovered in Round 1 papers
  - Papers cited by the most relevant Round 1 results
  - Contradictory findings that need investigation
  → Collect papers, identify remaining gaps

Round 3 (Targeted): Fill specific gaps
  - Missing baselines identified in Rounds 1-2
  - Concurrent work (last 6 months, same problem)
  - Key negative results or failed approaches
  → Stop when new queries return mostly papers you've already seen
```

**何时停**：若某轮返回的论文 >80% 已在你的集合里，搜索就饱和了。通常 2-3 轮足够。综述论文预期 4-5 轮。

**对基于 agent 的工作流**：用 `delegate_task` 并行分派每轮的查询。收集结果、去重，再从合并所得生成下一轮查询。

### 第 1.3 步：核验每条引用

**绝不凭记忆生成 BibTeX。务必以编程方式抓取。**

对每条引用，遵循强制的 5 步流程：

```
Citation Verification (MANDATORY per citation):
1. SEARCH → Query Semantic Scholar or Exa MCP with specific keywords
2. VERIFY → Confirm paper exists in 2+ sources (Semantic Scholar + arXiv/CrossRef)
3. RETRIEVE → Get BibTeX via DOI content negotiation (programmatically, not from memory)
4. VALIDATE → Confirm the claim you're citing actually appears in the paper
5. ADD → Add verified BibTeX to bibliography
If ANY step fails → mark as [CITATION NEEDED], inform scientist
```

```python
# Fetch BibTeX via DOI
import requests

def doi_to_bibtex(doi: str) -> str:
    response = requests.get(
        f"https://doi.org/{doi}",
        headers={"Accept": "application/x-bibtex"}
    )
    response.raise_for_status()
    return response.text
```

若无法核验某条引用：

```latex
\cite{PLACEHOLDER_author2024_verify_this}  % TODO: Verify this citation exists
```

**务必告知科学家**："I've marked [X] citations as placeholders that need verification."（我已把 [X] 条引用标为待核验的占位符。）

完整 API 文档与完整的 `CitationManager` 类见 [references/citation-workflow.md](references/citation-workflow.md)。

### 第 1.4 步：组织相关工作

按方法论给论文分组，而不是逐篇罗列：

**好**："One line of work uses X's assumption [refs] whereas we use Y's assumption because..."（一派工作用 X 的假设 [refs]，而我们用 Y 的假设，因为……）
**差**："Smith et al. introduced X. Jones et al. introduced Y. We combine both."（Smith 等人提出 X。Jones 等人提出 Y。我们两者兼顾。）

---

## 阶段 2：实验设计

**目标**：设计直接支撑论文论断的实验。每个实验都必须回答一个具体问题。

### 第 2.1 步：把论断映射到实验

建立显式映射：

| 论断 | 实验 | 预期证据 |
|-------|-----------|-------------------|
| "Our method outperforms baselines" | 主对比（Table 1） | 胜率、统计显著性 |
| "Effect is larger for weaker models" | 模型规模研究 | 单调的改善曲线 |
| "Convergence requires scope constraints" | 有约束 vs 无约束 | 收敛速率对比 |

**规则**：若某实验不映射到任何论断，就别跑。

### 第 2.2 步：设计基线

强基线是录用论文与被拒论文的分野。审稿人会问："Did they compare against X?"（他们跟 X 比了吗？）

标准基线类别：
- **朴素基线**：最简可能做法
- **强基线**：已知最佳的现有方法
- **消融基线**：你的方法去掉一个组件
- **算力对齐基线**：相同算力预算、不同分配

### 第 2.3 步：定义评测协议

跑任何东西前，明确指定：
- **指标**：你在测什么，方向符号（越高/越低越好）
- **聚合**：各 run/任务的结果如何合并
- **统计检验**：用什么检验确立显著性
- **样本量**：多少个 run/问题/任务

### 第 2.4 步：写实验脚本

套用这些来自成功研究流水线的模式：

**增量保存** — 每步后保存结果以便崩溃恢复：
```python
# Save after each problem/task
result_path = f"results/{task}/{strategy}/result.json"
if os.path.exists(result_path):
    continue  # Skip already-completed work
# ... run experiment ...
with open(result_path, 'w') as f:
    json.dump(result, f, indent=2)
```

**产物留存** — 保存所有中间输出：
```
results/<experiment>/
  <task>/
    <strategy>/
      final_output.md          # Final result
      history.json             # Full trajectory
      pass_01/                 # Per-iteration artifacts
        version_a.md
        version_b.md
        critic.md
```

**关注点分离** — 让生成、评测与可视化彼此分开：
```
run_experiment.py              # Core experiment runner
run_baselines.py               # Baseline comparison
run_comparison_judge.py        # Blind evaluation
analyze_results.py             # Statistical analysis
make_charts.py                 # Visualization
```

完整设计模式、cron 监控与错误恢复见 [references/experiment-patterns.md](references/experiment-patterns.md)。

### 第 2.5 步：设计人工评测（若适用）

许多 NLP、HCI 与对齐论文需要人工评测作为主要或补充证据。在跑自动实验前就设计好它 — 人工评测通常前置时间更长（IRB 审批、招募标注员）。

**何时需要人工评测：**
- 自动指标捕捉不到你在意的点（流畅度、有用性、安全性）
- 你的贡献关乎面向人的品质（可读性、偏好、信任）
- NLP venue（ACL、EMNLP）的审稿人对生成任务有此期待

**关键设计决策：**

| 决策 | 选项 | 指引 |
|----------|---------|----------|
| **标注员类型** | 专家、众包工人、终端用户 | 与论断所需相匹配 |
| **量表** | Likert（1-5）、成对比较、排序 | 对 LLM 输出，成对比较比 Likert 更可靠 |
| **样本量** | 每位标注员及总条目数 | 做功效分析，或至少 100 条目、3+ 标注员 |
| **一致性指标** | Cohen's kappa、Krippendorff's alpha、ICC | >2 位标注员用 Krippendorff's alpha；也要报原始一致性 |
| **平台** | Prolific、MTurk、内部团队 | 质量用 Prolific；规模用 MTurk；领域专长用内部 |

**标注指南清单：**
```
- [ ] Clear task description with examples (good AND bad)
- [ ] Decision criteria for ambiguous cases
- [ ] At least 2 worked examples per category
- [ ] Attention checks / gold standard items (10-15% of total)
- [ ] Qualification task or screening round
- [ ] Estimated time per item and fair compensation (>= local minimum wage)
- [ ] IRB/ethics review if required by your institution
```

**报告要求**（审稿人都会核对这些）：
- 标注员人数及其资质
- 标注员间一致性，含具体指标与数值
- 报酬细节（金额、估计时薪）
- 标注界面描述或截图（附录）
- 总标注时间

完整指南（含人工评测数据的统计检验、众包质检模式与 IRB 指引）见 [references/human-evaluation.md](references/human-evaluation.md)。

---

## 阶段 3：实验执行与监控

**目标**：可靠地跑实验、监控进展、从失败中恢复。

### 第 3.1 步：启动实验

长跑实验用 `nohup`：

```bash
nohup python run_experiment.py --config config.yaml > logs/experiment_01.log 2>&1 &
echo $!  # Record the PID
```

**并行执行**：同时跑彼此独立的实验，但要注意 API 速率限制。同一 API 上 4+ 个并发实验会互相拖慢。

### 第 3.2 步：设置监控（Cron 模式）

对长跑实验，设置周期性状态检查。cron prompt 应遵循这个模板：

```
Monitor Prompt Template:
1. Check if process is still running: ps aux | grep <pattern>
2. Read last 30 lines of log: tail -30 <logfile>
3. Check for completed results: ls <result_dir>
4. If results exist, read and report: cat <result_file>
5. If all done, commit: git add -A && git commit -m "<descriptive message>" && git push
6. Report in structured format (tables with key metrics)
7. Answer the key analytical question for this experiment
```

**静默模式**：若自上次检查以来什么都没变，回复 `[SILENT]` 以抑制对用户的通知。只有有消息时才报告。

### 第 3.3 步：处理失败

常见失败模式与恢复：

| 失败 | 检测 | 恢复 |
|---------|-----------|----------|
| API 限流 / 额度耗尽 | 日志中的 402/429 错误 | 等待，然后重跑（脚本会跳过已完成的工作） |
| 进程崩溃 | PID 消失、结果不完整 | 从最后的 checkpoint 重跑 |
| 难题超时 | 进程卡住、日志无进展 | 杀掉并跳过，在结果中注明 |
| 模型 ID 错误 | 引用模型名的报错 | 修 ID 并重跑 |

**关键**：脚本应始终检查已有结果并跳过已完成的工作。这让重跑安全且高效。

### 第 3.4 步：提交已完成结果

每批实验完成后：

```bash
git add -A
git commit -m "Add <experiment name>: <key finding in 1 line>"
git push
```

### 第 3.5 步：维护实验日志

git 提交记录了发生了什么，却没记录**探索树** — 即基于所学决定下一步试什么的决策。维护一份结构化的实验日志来捕捉这棵树：

```json
// experiment_journal.jsonl — append one entry per experiment attempt
{
  "id": "exp_003",
  "parent": "exp_001",
  "timestamp": "2025-05-10T14:30:00Z",
  "hypothesis": "Adding scope constraints will fix convergence failure from exp_001",
  "plan": "Re-run autoreason with max_tokens=2000 and fixed structure template",
  "config": {"model": "haiku", "strategy": "autoreason", "max_tokens": 2000},
  "status": "completed",
  "result_path": "results/exp_003/",
  "key_metrics": {"win_rate": 0.85, "convergence_rounds": 3},
  "analysis": "Scope constraints fixed convergence. Win rate jumped from 0.42 to 0.85.",
  "next_steps": ["Try same constraints on Sonnet", "Test without structure template"],
  "figures": ["figures/exp003_convergence.pdf"]
}
```

**为什么用日志而不只是 git？** git 跟踪文件变更。日志跟踪推理：你为什么试 X、学到了什么、这对下一个实验意味着什么。写论文时，这棵树对 Methods 小节（"we observed X, which motivated Y"）与诚实报告失败都极有价值。

**选择最佳路径**：当日志显示一棵分支树（exp_001 → exp_002a、exp_002b、exp_003）时，找出最能支撑论文论断的那条路径。把死胡同分支作为消融或负结果写进附录。

**每个实验快照代码**：每次运行后复制实验脚本：
```bash
cp experiment.py results/exp_003/experiment_snapshot.py
```
这样即便后续代码有改动，也能精确复现。

---

## 阶段 4：结果分析

**目标**：提取发现、计算统计量、找出故事。

### 第 4.1 步：汇总结果

写分析脚本，使其：
1. 加载一批中的所有结果文件
2. 计算逐任务与聚合指标
3. 生成汇总表

```python
# Standard analysis pattern
import json, os
from pathlib import Path

results = {}
for result_file in Path("results/").rglob("result.json"):
    data = json.loads(result_file.read_text())
    strategy = result_file.parent.name
    task = result_file.parent.parent.name
    results.setdefault(strategy, {})[task] = data

# Compute aggregate metrics
for strategy, tasks in results.items():
    scores = [t["score"] for t in tasks.values()]
    print(f"{strategy}: mean={np.mean(scores):.1f}, std={np.std(scores):.1f}")
```

### 第 4.2 步：统计显著性

始终计算：
- **误差棒**：标准差或标准误，注明是哪种
- **置信区间**：关键结果的 95% CI
- **成对检验**：比较两种方法用 McNemar's test
- **效应量**：Cohen's d 或 h，衡量实际显著性

McNemar's test、bootstrap CI 与 Cohen's h 的完整实现见 [references/experiment-patterns.md](references/experiment-patterns.md)。

### 第 4.3 步：找出故事

分析后，明确回答：
1. **主要发现是什么？** 用一句话说清。
2. **什么让你意外？** 意外结果常常造就最好的论文。
3. **什么失败了？** 失败的实验可能信息量最大。诚实报告失败会增强论文。
4. **需要哪些后续实验？** 结果常常引出新问题。

#### 处理负结果或零结果

当假设错误或结果不明确时，你有三个选项：

| 情形 | 动作 | 适合的 venue |
|-----------|--------|-----------|
| 假设错误但**为什么**有信息量 | 把论文围绕「为什么」的分析来组织 | NeurIPS、ICML（若分析严谨） |
| 方法没打赢基线但**揭示了新东西** | 把贡献重构为理解/分析 | ICLR（看重理解）、workshop 论文 |
| 对流行论断的干净负结果 | 写出来 — 领域需要知道 | NeurIPS Datasets & Benchmarks、TMLR、workshop |
| 结果不明确、没有清晰故事 | 转向 — 跑不同实验或重构 | 别硬凑一篇不存在的论文 |

**怎么写负结果论文：**
- 开头讲社区相信什么、为什么值得检验
- 描述你严谨的方法论（必须滴水不漏 — 审稿人会加倍审视）
- 用统计证据清晰地呈现零结果
- 分析**为什么**预期结果没出现
- 讨论对领域的启示

**明确欢迎负结果的 venue**：NeurIPS（Datasets & Benchmarks track）、TMLR、ML Reproducibility Challenge、各大会的 workshop。有些 workshop 专门征稿负结果。

### 第 4.4 步：制作图与表

**图**：
- 所有图用矢量图（PDF）：`plt.savefig('fig.pdf')`
- 色盲友好调色板（Okabe-Ito 或 Paul Tol）
- 自足的图注 — 读者不看正文也能懂
- 图内不放标题 — 由图注承担此功能

**表**：
- 用 `booktabs` LaTeX 包
- 每个指标的最优值加粗
- 含方向符号（越高/越低越好）
- 小数精度一致

```latex
\usepackage{booktabs}
\begin{tabular}{lcc}
\toprule
Method & Accuracy $\uparrow$ & Latency $\downarrow$ \\
\midrule
Baseline & 85.2 & 45ms \\
\textbf{Ours} & \textbf{92.1} & 38ms \\
\bottomrule
\end{tabular}
```

### 第 4.5 步：决定：继续实验还是开写？

| 情形 | 动作 |
|-----------|--------|
| 核心论断得到支撑、结果显著 | 进入阶段 5（写作） |
| 结果不明确、需要更多数据 | 回到阶段 2（设计） |
| 意外发现指向新方向 | 回到阶段 2（设计） |
| 缺一个审稿人会要的消融 | 跑掉它，再进入阶段 5 |
| 实验都做完但有些失败 | 记下失败，进入阶段 5 |

### 第 4.6 步：写实验日志（通往写作的桥）

进入论文写作前，先创建一份把结果与文字桥接起来的结构化实验日志。这是实验与写作之间最重要的一条结缔组织 — 没有它，写作 agent 就得从原始结果文件里重新推导故事。

**创建 `experiment_log.md`**，结构如下：

```markdown
# Experiment Log

## Contribution (one sentence)
[The paper's main claim]

## Experiments Run

### Experiment 1: [Name]
- **Claim tested**: [Which paper claim this supports]
- **Setup**: [Model, dataset, config, number of runs]
- **Key result**: [One sentence with the number]
- **Result files**: results/exp1/final_info.json
- **Figures generated**: figures/exp1_comparison.pdf
- **Surprising findings**: [Anything unexpected]

### Experiment 2: [Name]
...

## Figures
| Filename | Description | Which section it belongs in |
|----------|-------------|---------------------------|
| figures/main_comparison.pdf | Bar chart comparing all methods on benchmark X | Results, Figure 2 |
| figures/ablation.pdf | Ablation removing components A, B, C | Results, Figure 3 |
...

## Failed Experiments (document for honesty)
- [What was tried, why it failed, what it tells us]

## Open Questions
- [Anything the results raised that the paper should address]
```

**为什么重要**：写作时，agent（或被委派的 sub-agent）可以同时加载 `experiment_log.md` 与 LaTeX 模板，产出有真实结果支撑的初稿。没有这座桥，写作 agent 就得解析原始 JSON/CSV 文件并推断故事 — 这是臆造或误报数字的常见来源。

**Git 纪律**：把这份日志与它描述的结果一起提交。

---

## 迭代精修：策略选择

本流水线的任何产出 — 论文草稿、实验脚本、分析 — 都可迭代精修。autoreason 研究为每种精修策略何时有效、何时失效提供了实证依据。用本节选择正确做法。

### 快速决策表

| 你的情形 | 策略 | 原因 |
|---------------|----------|-----|
| 中档模型 + 有约束任务 | **Autoreason** | 最佳区间。生成—评估差最大。基线会主动破坏弱模型输出。 |
| 中档模型 + 开放任务 | **Autoreason** + 加范围约束 | 加固定事实、结构或交付物，以界定改进空间。 |
| 前沿模型 + 有约束任务 | **Autoreason** | 即便在前沿，也能赢 2/3 的有约束任务。 |
| 前沿模型 + 无约束任务 | **Critique-and-revise** 或**单轮** | Autoreason 排最后。模型自评已足够好。 |
| 具体技术任务（系统设计） | **Critique-and-revise** | 直接的「找—修」循环更高效。 |
| 填模板任务（只有一种正确结构） | **单轮**或**保守** | 决策空间极小。迭代无增益。 |
| 带测试用例的代码 | **Autoreason（代码变体）** | 先结构化分析*为什么*失败再修。恢复率 62% vs 43%。 |
| 很弱的模型（Llama 8B 级） | **单轮** | 模型太弱，产不出多样候选。应投入提升生成质量。 |

### 生成—评估差

**核心洞见**：Autoreason 的价值取决于模型生成能力与自评能力之间的差。

```
Model Tier        │ Generation │ Self-Eval │ Gap    │ Autoreason Value
──────────────────┼────────────┼───────────┼────────┼─────────────────
Weak (Llama 8B)   │ Poor       │ Poor      │ Small  │ None — can't generate diverse candidates
Mid (Haiku 3.5)   │ Decent     │ Poor      │ LARGE  │ MAXIMUM — 42/42 perfect Borda
Mid (Gemini Flash)│ Decent     │ Moderate  │ Large  │ High — wins 2/3
Strong (Sonnet 4) │ Good       │ Decent    │ Medium │ Moderate — wins 3/5
Frontier (S4.6)   │ Excellent  │ Good      │ Small  │ Only with constraints
```

这道差是结构性的，不是暂时的。随着成本下降，今天的前沿会变成明天的中档。最佳区间会移动，但永不消失。

### Autoreason 循环（摘要）

每轮由全新、隔离的 agent 产出三个候选：

1. **Critic** → 找出在位者 A 的问题（不做修复）
2. **Author B** → 依据批判修订 A
3. **Synthesizer** → 合并 A 与 B（标签随机化）
4. **Judge Panel** → 3 位盲评 CoT 评委用 Borda 计数给 A、B、AB 排序
5. **收敛** → A 连续 k=2 轮胜出 → 结束

**关键参数：**
- k=2 收敛（k=1 太早，k=3 太贵且无质量增益）
- 始终用 CoT 评委（收敛快 3 倍）
- 作者温度 0.8，评委 0.3
- 保守的平局规则：在位者胜平局
- 每个角色都是无共享上下文的全新 agent

### 应用到论文草稿

用 autoreason 精修论文本身时：
- **把 ground truth 交给 critic**：真实实验数据、结果 JSON、统计输出。没有这些，模型会臆造消融实验与假的置信区间。
- **至少用 3 位能正常工作的评委**：坏掉的评委解析器不会只是加噪音 — 它会彻底阻止均衡。
- **给修订加范围约束**：说"Address these specific weaknesses"，而不是"improve the paper."

### 失败模式

| 失败 | 检测 | 修复 |
|---------|-----------|-----|
| 不收敛（A 从不胜出） | 20+ 轮里 A 胜率 <15% | 给任务加范围约束 |
| 综合漂移 | 字数无界增长 | 约束结构与交付物 |
| 退化到不如单轮 | 基线得分高于迭代输出 | 切回单轮；模型可能太弱 |
| 过拟合（代码） | 公开测试通过率高、私有测试低 | 用结构化分析，而非只看测试反馈 |
| 评委坏掉 | 解析失败使评委数降到 3 以下 | 先修解析器再继续 |

完整 prompt、Borda 打分细节、模型选择指南、范围约束设计模式与算力预算参考见 [references/autoreason-methodology.md](references/autoreason-methodology.md)。

---

## 阶段 5：论文写作

**目标**：写一篇完整、可发表的论文。

### 大项目的上下文管理

一个有 50+ 实验文件、多个结果目录与大量文献笔记的论文项目，很容易超出 agent 的上下文窗口。主动管理它：

**每个写作任务加载进上下文的内容：**

| 写作任务 | 加载进上下文 | 不要加载 |
|---------------|------------------|-------------|
| 写引言 | `experiment_log.md`、贡献陈述、5-10 篇最相关论文的摘要 | 原始结果 JSON、完整实验脚本、全部文献笔记 |
| 写 Methods | 实验配置、伪代码、架构描述 | 原始日志、其他实验的结果 |
| 写 Results | `experiment_log.md`、结果汇总表、图清单 | 完整分析脚本、中间数据 |
| 写 Related Work | 整理好的引用笔记（第 1.4 步产出）、.bib 文件 | 实验文件、原始 PDF |
| 修订轮 | 完整论文草稿、具体的审稿人关切 | 其余一切 |

**原则：**
- **`experiment_log.md` 是主要的上下文桥梁** — 它汇总写作所需的一切，而无需加载原始数据文件（见第 4.6 步）
- 委派时**一次只加载一节**的上下文。起草 Methods 的 sub-agent 不需要文献综述笔记。
- **做摘要，别塞原始文件。** 200 行的结果 JSON，加载 10 行汇总表。50 页的相关论文，加载 5 句摘要 + 你写的 2 行相关性说明。
- **超大项目**：创建 `context/` 目录，放预压缩的摘要：
  ```
  context/
    contribution.md          # 1 sentence
    experiment_summary.md    # Key results table (from experiment_log.md)
    literature_map.md        # Organized citation notes
    figure_inventory.md      # List of figures with descriptions
  ```

### 叙事原则

**最关键的一条洞见**：论文不是实验的集合 — 它是由证据支撑、有一个明确贡献的故事。

每篇成功的 ML 论文都围绕 Neel Nanda 所说的「叙事」：一个简短、严谨、基于证据的技术故事，带一个读者在意的 takeaway。

**三大支柱（到引言结束必须清清楚楚）：**

| 支柱 | 说明 | 检验 |
|--------|-------------|------|
| **The What** | 1-3 条具体的新颖论断 | 你能用一句话说清它们吗？ |
| **The Why** | 严谨的实证证据 | 实验能把你的假设与替代解释区分开吗？ |
| **The So What** | 读者为什么该在意 | 这与某个公认的社区问题相关吗？ |

**若你无法用一句话说清贡献，那你还谈不上有论文。**

### 本指引背后的来源

本 skill 综合了在顶会大量发表的研究者的写作哲学。写作哲学层最初由 [Orchestra Research](https://github.com/orchestra-research) 编成 `ml-paper-writing` skill。

| 来源 | 关键贡献 | 链接 |
|--------|-----------------|------|
| **Neel Nanda**（Google DeepMind） | 叙事原则、What/Why/So What 框架 | [How to Write ML Papers](https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) |
| **Sebastian Farquhar**（DeepMind） | 5 句摘要公式 | [How to Write ML Papers](https://sebastianfarquhar.com/on-research/2024/11/04/how_to_write_ml_papers/) |
| **Gopen & Swan** | 读者预期的 7 条原则 | [Science of Scientific Writing](https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf) |
| **Zachary Lipton** | 用词、消除模糊措辞 | [Heuristics for Scientific Writing](https://www.approximatelycorrect.com/2018/01/29/heuristics-technical-scientific-writing-machine-learning-perspective/) |
| **Jacob Steinhardt**（UC Berkeley） | 精确、术语一致 | [Writing Tips](https://bounded-regret.ghost.io/) |
| **Ethan Perez**（Anthropic） | 微观清晰度技巧 | [Easy Paper Writing Tips](https://ethanperez.net/easy-paper-writing-tips/) |
| **Andrej Karpathy** | 聚焦单一贡献 | 多场讲座 |

**想深入任一主题，见：**
- [references/writing-guide.md](references/writing-guide.md) — 完整解释与示例
- [references/sources.md](references/sources.md) — 完整参考书目

### 时间分配

在以下各项上花大致**相等**的时间：
1. 摘要
2. 引言
3. 图
4. 其余一切加起来

**为什么？** 多数审稿人在读到你的方法前就已形成判断。读者接触你论文的顺序是：标题 → 摘要 → 引言 → 图 → 也许才是其余。

### 写作流程

```
Paper Writing Checklist:
- [ ] Step 1: Define the one-sentence contribution
- [ ] Step 2: Draft Figure 1 (core idea or most compelling result)
- [ ] Step 3: Draft abstract (5-sentence formula)
- [ ] Step 4: Draft introduction (1-1.5 pages max)
- [ ] Step 5: Draft methods
- [ ] Step 6: Draft experiments & results
- [ ] Step 7: Draft related work
- [ ] Step 8: Draft conclusion & discussion
- [ ] Step 9: Draft limitations (REQUIRED by all venues)
- [ ] Step 10: Plan appendix (proofs, extra experiments, details)
- [ ] Step 11: Complete paper checklist
- [ ] Step 12: Final review
```

### 两轮精修模式

用 AI agent 起草时，采用**两轮**做法（在 SakanaAI 的 AI-Scientist 流水线中成效显著）：

**第 1 轮 — 每节边写边立即精修：**
对每一节，写完整草稿后立即在同一上下文里精修。趁该节还新鲜，抓住局部问题（清晰度、行文、完整性）。

**第 2 轮 — 带着整篇上下文做全局精修：**
所有小节起草完后，带着对整篇论文的认识回访每一节。这能抓住跨节问题：冗余、术语不一致、叙事流，以及某节承诺了另一节没兑现的缺口。

```
Second-pass refinement prompt (per section):
"Review the [SECTION] in the context of the complete paper.
- Does it fit with the rest of the paper? Are there redundancies with other sections?
- Is terminology consistent with Introduction and Methods?
- Can anything be cut without weakening the message?
- Does the narrative flow from the previous section and into the next?
Make minimal, targeted edits. Do not rewrite from scratch."
```

### LaTeX 错误清单

把这份清单附到每个精修 prompt 后面。这些是 LLM 写 LaTeX 时最常见的错误：

```
LaTeX Quality Checklist (verify after every edit):
- [ ] No unenclosed math symbols ($ signs balanced)
- [ ] Only reference figures/tables that exist (\ref matches \label)
- [ ] No fabricated citations (\cite matches entries in .bib)
- [ ] Every \begin{env} has matching \end{env} (especially figure, table, algorithm)
- [ ] No HTML contamination (</end{figure}> instead of \end{figure})
- [ ] No unescaped underscores outside math mode (use \_ in text)
- [ ] No duplicate \label definitions
- [ ] No duplicate section headers
- [ ] Numbers in text match actual experimental results
- [ ] All figures have captions and labels
- [ ] No overly long lines that cause overfull hbox warnings
```

### 第 5.0 步：标题

标题是被读得最多的单一元素。它决定有没有人点进摘要。

**好标题**：
- 陈述贡献或发现："Autoreason: When Iterative LLM Refinement Works and Why It Fails"
- 突出意外结果："Scaling Data-Constrained Language Models"（暗示你能做到）
- 方法名 + 它做什么："DPO: Direct Preference Optimization of Language Models"

**差标题**：
- 太泛："An Approach to Improving Language Model Outputs"
- 太长：超过约 15 个词的都算
- 全是术语："Asymptotic Convergence of Iterative Stochastic Policy Refinement"（这是写给谁的？）

**规则**：
- 有方法名就写进去（便于被引用）
- 含 1-2 个审稿人会搜的关键词
- 除非冒号两边都有意义，否则别用冒号
- 检验：审稿人光看标题能知道领域与贡献吗？

### 第 5.1 步：摘要（5 句公式）

来自 Sebastian Farquhar（DeepMind）：

```
1. What you achieved: "We introduce...", "We prove...", "We demonstrate..."
2. Why this is hard and important
3. How you do it (with specialist keywords for discoverability)
4. What evidence you have
5. Your most remarkable number/result
```

**删掉**「Large language models have achieved remarkable success...」这类泛泛的开场

### 第 5.2 步：图 1

图 1 是多数读者看的第二样东西（在摘要之后）。在写引言前就起草它 — 它会逼你把核心想法讲清楚。

| 图 1 类型 | 何时用 | 示例 |
|---------------|-------------|---------|
| **方法图** | 新架构或流水线 | 展示你系统的 TikZ 流程图 |
| **结果 teaser** | 一个有力的结果就能讲清整个故事 | 柱状图："Ours vs baselines"，差距清晰 |
| **问题示意** | 问题不直观 | 修好前后的失败模式对比 |
| **概念图** | 抽象贡献需要视觉落点 | 方法属性的 2x2 矩阵 |

**规则**：图 1 必须不看任何正文就能看懂。光看图注就应传达核心想法。用色要有目的 — 不是装饰。

### 第 5.3 步：引言（最多 1-1.5 页）

必须包含：
- 清晰的问题陈述
- 方法概览
- 2-4 条贡献列表（双栏格式下每条最多 1-2 行）
- Methods 应在第 2-3 页开始

### 第 5.4 步：Methods

让人能重新实现：
- 概念大纲或伪代码
- 列出所有超参
- 足以复现的架构细节
- 呈现最终设计决策；消融放到实验部分

### 第 5.5 步：实验与结果

对每个实验，明确说明：
- **它支撑什么论断**
- 它如何与主要贡献相连
- 该看什么："the blue line shows X, which demonstrates Y"

要求：
- 误差棒并注明方法（标准差 vs 标准误）
- 超参搜索范围
- 算力基础设施（GPU 型号、总小时数）
- 设定随机种子的方法

### 第 5.6 步：Related Work

按方法论组织，而不是逐篇罗列。慷慨引用 — 审稿人很可能就是相关论文的作者。

### 第 5.7 步：Limitations（必需）

所有主要会议都要求这一节。诚实有好处：
- 审稿人被要求不得因诚实承认局限而扣分
- 先自己指出弱点，抢先化解批评
- 解释为什么这些局限不动摇核心论断

### 第 5.8 步：结论与讨论

**结论**（必需，0.5-1 页）：
- 用一句话重述贡献（措辞与摘要不同）
- 总结关键发现（2-3 句，不是列表）
- 启示：这对领域意味着什么？
- 未来工作：2-3 个具体的下一步（不是含糊的 "we leave X for future work"）

**讨论**（可选，有时与结论合并）：
- 超越直接结果的更广启示
- 与其他子领域的联系
- 诚实评估方法何时有效、何时无效
- 实际部署考量

**切勿**在结论里引入新结果或新论断。

### 第 5.9 步：附录策略

所有主要 venue 对附录都不限页数，且附录对可复现性至关重要。结构：

| 附录小节 | 放什么 |
|-----------------|---------------|
| **证明与推导** | 正文放不下的完整证明。正文可陈述定理并写 "proof in Appendix A." |
| **补充实验** | 消融、scaling 曲线、逐数据集拆分、超参敏感性 |
| **实现细节** | 完整超参表、训练细节、硬件规格、随机种子 |
| **数据集文档** | 数据收集过程、标注指南、许可、预处理 |
| **Prompt 与模板** | 用到的确切 prompt（基于 LLM 的方法）、评测模板 |
| **人工评测** | 标注界面截图、给标注员的说明、IRB 细节 |
| **补充图** | 逐任务拆分、轨迹可视化、失败案例示例 |

**规则**：
- 主论文必须自足 — 审稿人没有义务读附录
- 绝不把关键证据只放附录
- 交叉引用："Full results in Table 5 (Appendix B)"，而不只是 "see appendix"
- 用 `\appendix` 命令，然后 `\section{A: Proofs}` 等

### 页数预算管理

超出页数限制时：

| 削减策略 | 省下 | 风险 |
|-------------|-------|------|
| 把证明移到附录 | 0.5-2 页 | 低 — 标准做法 |
| 精简相关工作 | 0.5-1 页 | 中 — 可能漏掉关键引用 |
| 用子图合并表格 | 0.25-0.5 页 | 低 — 常提升可读性 |
| 谨慎用 `\vspace{-Xpt}` | 0.1-0.3 页 | 细微则低，明显则高 |
| 删掉定性示例 | 0.5-1 页 | 中 — 审稿人喜欢示例 |
| 缩小图 | 0.25-0.5 页 | 高 — 图必须保持可读 |

**切勿**：缩小字号、改页边距、删除必需小节（limitations、broader impact），或对正文用 `\small`/`\footnotesize`。

### 第 5.10 步：Ethics 与 Broader Impact 声明

多数 venue 现在要求或强烈鼓励 ethics/broader impact 声明。这不是套话 — 审稿人会读它，并可能提出伦理关切，触发 desk rejection。

**要写什么：**

| 组成部分 | 内容 | 谁要求 |
|-----------|---------|-------------|
| **正面社会影响** | 你的工作如何造福社会 | NeurIPS、ICML |
| **潜在负面影响** | 滥用风险、两用顾虑、失败模式 | NeurIPS、ICML |
| **公平与偏见** | 你的方法/数据是否有已知偏见？ | 所有 venue（隐含） |
| **环境影响** | 大规模训练的算力碳足迹 | ICML，NeurIPS 也日益要求 |
| **隐私** | 你的工作是否使用或支持处理个人数据？ | ACL、NeurIPS |
| **LLM 披露** | 写作或实验中是否用了 AI？ | ICLR（强制）、ACL |

**怎么写这份声明：**

```latex
\section*{Broader Impact Statement}
% NeurIPS/ICML: after conclusion, does not count toward page limit

% 1. Positive applications (1-2 sentences)
This work enables [specific application] which may benefit [specific group].

% 2. Risks and mitigations (1-3 sentences, be specific)
[Method/model] could potentially be misused for [specific risk]. We mitigate
this by [specific mitigation, e.g., releasing only model weights above size X,
including safety filters, documenting failure modes].

% 3. Limitations of impact claims (1 sentence)
Our evaluation is limited to [specific domain]; broader deployment would
require [specific additional work].
```

**常见错误：**
- 写 "we foresee no negative impacts"（几乎从不成立 — 审稿人对此不信任）
- 含糊："this could be misused" 却不说明怎么被滥用
- 忽略大规模工作的算力成本
- 在要求披露的 venue 忘了披露 LLM 使用

**算力碳足迹**（训练密集型论文）：
```python
# Estimate using ML CO2 Impact tool methodology
gpu_hours = 1000  # total GPU hours
gpu_tdp_watts = 400  # e.g., A100 = 400W
pue = 1.1  # Power Usage Effectiveness (data center overhead)
carbon_intensity = 0.429  # kg CO2/kWh (US average; varies by region)

energy_kwh = (gpu_hours * gpu_tdp_watts * pue) / 1000
carbon_kg = energy_kwh * carbon_intensity
print(f"Energy: {energy_kwh:.0f} kWh, Carbon: {carbon_kg:.0f} kg CO2eq")
```

### 第 5.11 步：Datasheets 与 Model Cards（若适用）

若你的论文**提出新数据集**或**发布模型**，要附结构化文档。审稿人日益期待这一点，NeurIPS Datasets & Benchmarks track 更是强制要求。

**Datasheets for Datasets**（Gebru et al., 2021）— 放入附录：

```
Dataset Documentation (Appendix):
- Motivation: Why was this dataset created? What task does it support?
- Composition: What are the instances? How many? What data types?
- Collection: How was data collected? What was the source?
- Preprocessing: What cleaning/filtering was applied?
- Distribution: How is the dataset distributed? Under what license?
- Maintenance: Who maintains it? How to report issues?
- Ethical considerations: Contains personal data? Consent obtained?
  Potential for harm? Known biases?
```

**Model Cards**（Mitchell et al., 2019）— 发布模型时放入附录：

```
Model Card (Appendix):
- Model details: Architecture, training data, training procedure
- Intended use: Primary use cases, out-of-scope uses
- Metrics: Evaluation metrics and results on benchmarks
- Ethical considerations: Known biases, fairness evaluations
- Limitations: Known failure modes, domains where model underperforms
```

### 写作风格

**句子级清晰度（Gopen & Swan 的 7 条原则）：**

| 原则 | 规则 |
|-----------|------|
| 主谓贴近 | 让主语与谓语靠近 |
| 重音位置 | 把强调放在句末 |
| 话题位置 | 先放语境，新信息在后 |
| 先旧后新 | 熟悉的信息 → 不熟悉的信息 |
| 一单元一功能 | 每段只讲一个点 |
| 动作放进动词 | 用动词，别用名词化 |
| 先语境后新 | 先铺陈再呈现 |

**用词（Lipton、Steinhardt）：**
- 要具体：用 "accuracy" 而非 "performance"
- 消除模糊措辞：除非真不确定，否则去掉 "may"
- 术语全程一致
- 避免增量式措辞：用 "develop" 而非 "combine"

**带示例的完整写作指南**：见 [references/writing-guide.md](references/writing-guide.md)

### 使用 LaTeX 模板

**务必先整体复制模板目录，再在里面写。**

```
Template Setup Checklist:
- [ ] Step 1: Copy entire template directory to new project
- [ ] Step 2: Verify template compiles as-is (before any changes)
- [ ] Step 3: Read the template's example content to understand structure
- [ ] Step 4: Replace example content section by section
- [ ] Step 5: Use template macros (check preamble for \newcommand definitions)
- [ ] Step 6: Clean up template artifacts only at the end
```

**第 1 步：复制完整模板**

```bash
cp -r templates/neurips2025/ ~/papers/my-paper/
cd ~/papers/my-paper/
ls -la  # Should see: main.tex, neurips.sty, Makefile, etc.
```

复制**整个**目录，而不只是 .tex 文件。模板含样式文件（.sty）、参考文献样式（.bst）、示例内容与 Makefile。

**第 2 步：先确认模板能编译**

做**任何**改动前：
```bash
latexmk -pdf main.tex
# Or manual: pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

若未改动的模板编不过，先修好它（通常是缺 TeX 包 — 用 `tlmgr install <package>` 安装）。

**第 3 步：保留模板内容作参考**

别立刻删掉示例内容。把它注释掉，当格式参考：
```latex
% Template example (keep for reference):
% \begin{figure}[t]
%   \centering
%   \includegraphics[width=0.8\linewidth]{example-image}
%   \caption{Template shows caption style}
% \end{figure}

% Your actual figure:
\begin{figure}[t]
  \centering
  \includegraphics[width=0.8\linewidth]{your-figure.pdf}
  \caption{Your caption following the same style.}
\end{figure}
```

**第 4 步：逐节替换内容**

系统地推进：标题/作者 → 摘要 → 引言 → 方法 → 实验 → 相关工作 → 结论 → 参考文献 → 附录。每节之后编译一次。

**第 5 步：使用模板宏**

```latex
\newcommand{\method}{YourMethodName}  % Consistent method naming
\newcommand{\eg}{e.g.,\xspace}        % Proper abbreviations
\newcommand{\ie}{i.e.,\xspace}
```

### 模板陷阱

| 陷阱 | 问题 | 解决 |
|---------|---------|----------|
| 只复制 `.tex` 文件 | 缺 `.sty`，编不过 | 复制整个目录 |
| 修改 `.sty` 文件 | 破坏会议格式 | 绝不编辑样式文件 |
| 乱加包 | 冲突、搞坏模板 | 必要时才加 |
| 过早删除模板内容 | 丢失格式参考 | 保留为注释直到完工 |
| 不常编译 | 错误累积 | 每节之后编译 |
| 图用位图 PNG | 论文里发虚 | 始终用矢量 PDF，`savefig('fig.pdf')` |

### 模板速查

| 会议 | 主文件 | 样式文件 | 页数限制 |
|------------|-----------|------------|------------|
| NeurIPS 2025 | `main.tex` | `neurips.sty` | 9 页 |
| ICML 2026 | `example_paper.tex` | `icml2026.sty` | 8 页 |
| ICLR 2026 | `iclr2026_conference.tex` | `iclr2026_conference.sty` | 9 页 |
| ACL 2025 | `acl_latex.tex` | `acl.sty` | 8 页（长文） |
| AAAI 2026 | `aaai2026-unified-template.tex` | `aaai2026.sty` | 7 页 |
| COLM 2025 | `colm2025_conference.tex` | `colm2025_conference.sty` | 9 页 |

**通用**：双盲，参考文献不计页，附录不限页，必须用 LaTeX。

模板在 `templates/` 目录。编译环境搭建（VS Code、CLI、Overleaf、其他 IDE）见 [templates/README.md](templates/README.md)。

### 表格与图

**表** — 用 `booktabs` 做专业排版：

```latex
\usepackage{booktabs}
\begin{tabular}{lcc}
\toprule
Method & Accuracy $\uparrow$ & Latency $\downarrow$ \\
\midrule
Baseline & 85.2 & 45ms \\
\textbf{Ours} & \textbf{92.1} & 38ms \\
\bottomrule
\end{tabular}
```

规则：
- 每个指标的最优值加粗
- 含方向符号（$\uparrow$ 越高越好，$\downarrow$ 越低越好）
- 数值列右对齐
- 小数精度一致

**图**：
- 所有图与示意图用**矢量图**（PDF、EPS）— `plt.savefig('fig.pdf')`
- **位图**（PNG 600 DPI）仅用于照片
- **色盲友好调色板**（Okabe-Ito 或 Paul Tol）
- 验证**灰度可读性**（8% 的男性有色觉缺陷）
- **图内不放标题** — 由图注承担此功能
- **自足的图注** — 读者不看正文也能懂

### 会议重投

在 venue 之间转换，见阶段 7（投稿准备）— 它涵盖完整转换流程、页数变化表与拒稿后指引。

### 专业 LaTeX 导言区

给任何论文加这些包以提升专业质感。它们与所有主要会议样式文件兼容：

```latex
% --- Professional Packages (add after conference style file) ---

% Typography
\usepackage{microtype}              % Microtypographic improvements (protrusion, expansion)
                                     % Makes text noticeably more polished — always include

% Tables
\usepackage{booktabs}               % Professional table rules (\toprule, \midrule, \bottomrule)
\usepackage{siunitx}                % Consistent number formatting, decimal alignment
                                     % Usage: \num{12345} → 12,345; \SI{3.5}{GHz} → 3.5 GHz
                                     % Table alignment: S column type for decimal-aligned numbers

% Figures
\usepackage{graphicx}               % Include graphics (\includegraphics)
\usepackage{subcaption}             % Subfigures with (a), (b), (c) labels
                                     % Usage: \begin{subfigure}{0.48\textwidth} ... \end{subfigure}

% Diagrams and Algorithms
\usepackage{tikz}                   % Programmable vector diagrams
\usetikzlibrary{arrows.meta, positioning, shapes.geometric, calc, fit, backgrounds}
\usepackage[ruled,vlined]{algorithm2e}  % Professional pseudocode
                                     % Alternative: \usepackage{algorithmicx} if template bundles it

% Cross-references
\usepackage{cleveref}               % Smart references: \cref{fig:x} → "Figure 1"
                                     % MUST be loaded AFTER hyperref
                                     % Handles: figures, tables, sections, equations, algorithms

% Math (usually included by conference .sty, but verify)
\usepackage{amsmath,amssymb}        % AMS math environments and symbols
\usepackage{mathtools}              % Extends amsmath (dcases, coloneqq, etc.)

% Colors (for figures and diagrams)
\usepackage{xcolor}                 % Color management
% Okabe-Ito colorblind-safe palette:
\definecolor{okblue}{HTML}{0072B2}
\definecolor{okorange}{HTML}{E69F00}
\definecolor{okgreen}{HTML}{009E73}
\definecolor{okred}{HTML}{D55E00}
\definecolor{okpurple}{HTML}{CC79A7}
\definecolor{okcyan}{HTML}{56B4E9}
\definecolor{okyellow}{HTML}{F0E442}
```

**注意：**
- `microtype` 对视觉质量影响最大。它在亚像素级别调整字符间距。务必包含。
- `siunitx` 通过 `S` 列类型处理表中小数点对齐 — 省去手动间距。
- `cleveref` 必须在 `hyperref` **之后**加载。多数会议 .sty 会加载 hyperref，所以把 cleveref 放最后。
- 检查会议模板是否已加载其中某些（尤其 `algorithm`、`amsmath`、`graphicx`）。别重复加载。

### siunitx 表格对齐

`siunitx` 让数字密集的表明显更可读：

```latex
\begin{tabular}{l S[table-format=2.1] S[table-format=2.1] S[table-format=2.1]}
\toprule
Method & {Accuracy $\uparrow$} & {F1 $\uparrow$} & {Latency (ms) $\downarrow$} \\
\midrule
Baseline         & 85.2  & 83.7  & 45.3 \\
Ablation (no X)  & 87.1  & 85.4  & 42.1 \\
\textbf{Ours}    & \textbf{92.1} & \textbf{90.8} & \textbf{38.7} \\
\bottomrule
\end{tabular}
```

`S` 列类型会按小数点自动对齐。表头放 `{}` 里可逃逸对齐。

### 子图

并排图的标准写法：

```latex
\begin{figure}[t]
  \centering
  \begin{subfigure}[b]{0.48\textwidth}
    \centering
    \includegraphics[width=\textwidth]{fig_results_a.pdf}
    \caption{Results on Dataset A.}
    \label{fig:results-a}
  \end{subfigure}
  \hfill
  \begin{subfigure}[b]{0.48\textwidth}
    \centering
    \includegraphics[width=\textwidth]{fig_results_b.pdf}
    \caption{Results on Dataset B.}
    \label{fig:results-b}
  \end{subfigure}
  \caption{Comparison of our method across two datasets. (a) shows the scaling
  behavior and (b) shows the ablation results. Both use 5 random seeds.}
  \label{fig:results}
\end{figure}
```

用 `\cref{fig:results}` → "Figure 1"，`\cref{fig:results-a}` → "Figure 1a"。

### 用 algorithm2e 写伪代码

```latex
\begin{algorithm}[t]
\caption{Iterative Refinement with Judge Panel}
\label{alg:method}
\KwIn{Task $T$, model $M$, judges $J_1 \ldots J_n$, convergence threshold $k$}
\KwOut{Final output $A^*$}
$A \gets M(T)$ \tcp*{Initial generation}
$\text{streak} \gets 0$\;
\While{$\text{streak} < k$}{
  $C \gets \text{Critic}(A, T)$ \tcp*{Identify weaknesses}
  $B \gets M(T, C)$ \tcp*{Revised version addressing critique}
  $AB \gets \text{Synthesize}(A, B)$ \tcp*{Merge best elements}
  \ForEach{judge $J_i$}{
    $\text{rank}_i \gets J_i(\text{shuffle}(A, B, AB))$ \tcp*{Blind ranking}
  }
  $\text{winner} \gets \text{BordaCount}(\text{ranks})$\;
  \eIf{$\text{winner} = A$}{
    $\text{streak} \gets \text{streak} + 1$\;
  }{
    $A \gets \text{winner}$; $\text{streak} \gets 0$\;
  }
}
\Return{$A$}\;
\end{algorithm}
```

### TikZ 示意图模式

TikZ 是 ML 论文方法图的标准。常见模式：

**流水线/流程图**（ML 论文最常见）：

```latex
\begin{figure}[t]
\centering
\begin{tikzpicture}[
  node distance=1.8cm,
  box/.style={rectangle, draw, rounded corners, minimum height=1cm, 
              minimum width=2cm, align=center, font=\small},
  arrow/.style={-{Stealth[length=3mm]}, thick},
]
  \node[box, fill=okcyan!20] (input) {Input\\$x$};
  \node[box, fill=okblue!20, right of=input] (encoder) {Encoder\\$f_\theta$};
  \node[box, fill=okgreen!20, right of=encoder] (latent) {Latent\\$z$};
  \node[box, fill=okorange!20, right of=latent] (decoder) {Decoder\\$g_\phi$};
  \node[box, fill=okred!20, right of=decoder] (output) {Output\\$\hat{x}$};
  
  \draw[arrow] (input) -- (encoder);
  \draw[arrow] (encoder) -- (latent);
  \draw[arrow] (latent) -- (decoder);
  \draw[arrow] (decoder) -- (output);
\end{tikzpicture}
\caption{Architecture overview. The encoder maps input $x$ to latent 
representation $z$, which the decoder reconstructs.}
\label{fig:architecture}
\end{figure}
```

**对比/矩阵图**（展示方法变体）：

```latex
\begin{tikzpicture}[
  cell/.style={rectangle, draw, minimum width=2.5cm, minimum height=1cm, 
               align=center, font=\small},
  header/.style={cell, fill=gray!20, font=\small\bfseries},
]
  % Headers
  \node[header] at (0, 0) {Method};
  \node[header] at (3, 0) {Converges?};
  \node[header] at (6, 0) {Quality?};
  % Rows
  \node[cell] at (0, -1) {Single Pass};
  \node[cell, fill=okgreen!15] at (3, -1) {N/A};
  \node[cell, fill=okorange!15] at (6, -1) {Baseline};
  \node[cell] at (0, -2) {Critique+Revise};
  \node[cell, fill=okred!15] at (3, -2) {No};
  \node[cell, fill=okred!15] at (6, -2) {Degrades};
  \node[cell] at (0, -3) {Ours};
  \node[cell, fill=okgreen!15] at (3, -3) {Yes ($k$=2)};
  \node[cell, fill=okgreen!15] at (6, -3) {Improves};
\end{tikzpicture}
```

**迭代循环图**（有反馈的方法）：

```latex
\begin{tikzpicture}[
  node distance=2cm,
  box/.style={rectangle, draw, rounded corners, minimum height=0.8cm, 
              minimum width=1.8cm, align=center, font=\small},
  arrow/.style={-{Stealth[length=3mm]}, thick},
  label/.style={font=\scriptsize, midway, above},
]
  \node[box, fill=okblue!20] (gen) {Generator};
  \node[box, fill=okred!20, right=2.5cm of gen] (critic) {Critic};
  \node[box, fill=okgreen!20, below=1.5cm of $(gen)!0.5!(critic)$] (judge) {Judge Panel};
  
  \draw[arrow] (gen) -- node[label] {output $A$} (critic);
  \draw[arrow] (critic) -- node[label, right] {critique $C$} (judge);
  \draw[arrow] (judge) -| node[label, left, pos=0.3] {winner} (gen);
\end{tikzpicture}
```

### 用 latexdiff 跟踪修订

回应评审必备 — 生成标注版本间改动的 PDF：

```bash
# Install
# macOS: brew install latexdiff (or comes with TeX Live)
# Linux: sudo apt install latexdiff

# Generate diff
latexdiff paper_v1.tex paper_v2.tex > paper_diff.tex
pdflatex paper_diff.tex

# For multi-file projects (with \input{} or \include{})
latexdiff --flatten paper_v1.tex paper_v2.tex > paper_diff.tex
```

它产出删改标红删除线、新增标蓝的 PDF — 这是评审回复附录的标准格式。

### 给 matplotlib 用 SciencePlots

安装并使用，以产出出版级图：

```bash
pip install SciencePlots
```

```python
import matplotlib.pyplot as plt
import scienceplots  # registers styles

# Use science style (IEEE-like, clean)
with plt.style.context(['science', 'no-latex']):
    fig, ax = plt.subplots(figsize=(3.5, 2.5))  # Single-column width
    ax.plot(x, y, label='Ours', color='#0072B2')
    ax.plot(x, y2, label='Baseline', color='#D55E00', linestyle='--')
    ax.set_xlabel('Training Steps')
    ax.set_ylabel('Accuracy')
    ax.legend()
    fig.savefig('paper/fig_results.pdf', bbox_inches='tight')

# Available styles: 'science', 'ieee', 'nature', 'science+ieee'
# Add 'no-latex' if LaTeX is not installed on the machine generating plots
```

**标准图尺寸**（双栏格式）：
- 单栏：`figsize=(3.5, 2.5)` — 放得下一栏
- 双栏：`figsize=(7.0, 3.0)` — 横跨两栏
- 方形：`figsize=(3.5, 3.5)` — 用于热力图、混淆矩阵

---

## 阶段 6：自审与修订

**目标**：投稿前模拟评审流程。尽早抓住弱点。

### 第 6.1 步：模拟评审（集成模式）

从多个视角生成评审。来自自动化研究流水线（尤其是 SakanaAI 的 AI-Scientist）的关键洞见：**带 meta-reviewer 的集成评审，产出的反馈远比单轮评审校准得好。**

**第 1 步：生成 N 份独立评审**（N=3-5）

用不同模型或温度设置。每位审稿人只看论文，不看其他评审。**默认偏负面** — LLM 在评估中有充分记录的正向偏见。

```
You are an expert reviewer for [VENUE]. You are critical and thorough.
If a paper has weaknesses or you are unsure about a claim, flag it clearly
and reflect that in your scores. Do not give the benefit of the doubt.

Review this paper according to the official reviewer guidelines. Evaluate:

1. Soundness (are claims well-supported? are baselines fair and strong?)
2. Clarity (is the paper well-written? could an expert reproduce it?)
3. Significance (does this matter to the community?)
4. Originality (new insights, not just incremental combination?)

Provide your review as structured JSON:
{
  "summary": "2-3 sentence summary",
  "strengths": ["strength 1", "strength 2", ...],
  "weaknesses": ["weakness 1 (most critical)", "weakness 2", ...],
  "questions": ["question for authors 1", ...],
  "missing_references": ["paper that should be cited", ...],
  "soundness": 1-4,
  "presentation": 1-4,
  "contribution": 1-4,
  "overall": 1-10,
  "confidence": 1-5
}
```

**第 2 步：Meta-review（Area Chair 汇总）**

把 N 份评审全喂给 meta-reviewer：

```
You are an Area Chair at [VENUE]. You have received [N] independent reviews
of a paper. Your job is to:

1. Identify consensus strengths and weaknesses across reviewers
2. Resolve disagreements by examining the paper directly
3. Produce a meta-review that represents the aggregate judgment
4. Use AVERAGED numerical scores across all reviews

Be conservative: if reviewers disagree on whether a weakness is serious,
treat it as serious until the authors address it.

Reviews:
[review_1]
[review_2]
...
```

**第 3 步：反思循环**（可选，2-3 轮）

每位审稿人看到 meta-review 后可精修自己的评审。用提前终止哨兵：若审稿人回复 "I am done"（无改动），就停止迭代。

**评审的模型选择**：评审最好用可得的最强模型，即便你是用更便宜的模型写的论文。审稿模型应与写作模型独立选取。

**Few-shot 校准**：若有，就纳入 1-2 份目标 venue 的真实已发表评审作为示例。这会大幅改善评分校准。示例评审见 [references/reviewer-guidelines.md](references/reviewer-guidelines.md)。

### 第 6.1b 步：视觉评审轮（VLM）

纯文本评审会漏掉一整类问题：图质量、版式问题、视觉一致性。若有视觉模型，对编译出的 PDF 单独跑一轮**视觉评审**：

```
You are reviewing the visual presentation of this research paper PDF.
Check for:
1. Figure quality: Are plots readable? Labels legible? Colors distinguishable?
2. Figure-caption alignment: Does each caption accurately describe its figure?
3. Layout issues: Orphaned section headers, awkward page breaks, figures far from their references
4. Table formatting: Aligned columns, consistent decimal precision, bold for best results
5. Visual consistency: Same color scheme across all figures, consistent font sizes
6. Grayscale readability: Would the figures be understandable if printed in B&W?

For each issue, specify the page number and exact location.
```

这能抓住文本评审抓不到的问题：坐标轴标签读不清的图、离首次引用有 3 页之遥的图、图 2 与图 5 调色板不一致，或明显宽于一栏的表。

### 第 6.1c 步：论断核验轮

模拟评审后，单独跑一轮核验。这能抓住审稿人可能漏掉的事实错误：

```
Claim Verification Protocol:
1. Extract every factual claim from the paper (numbers, comparisons, trends)
2. For each claim, trace it to the specific experiment/result that supports it
3. Verify the number in the paper matches the actual result file
4. Flag any claim without a traceable source as [VERIFY]
```

对基于 agent 的工作流：把核验委派给一个只收到论文文本与原始结果文件的**全新 sub-agent**。全新上下文可防止确认偏见 — 核验者不「记得」结果本该是什么。

### 第 6.2 步：给反馈排优先级

收集评审后，归类：

| 优先级 | 动作 |
|----------|--------|
| **Critical**（技术缺陷、缺基线） | 必须修。可能需要新实验 → 回到阶段 2 |
| **High**（清晰度问题、缺消融） | 应在本次修订中修 |
| **Medium**（小写作问题、补充实验） | 时间允许就修 |
| **Low**（风格偏好、边缘建议） | 记为未来工作 |

### 第 6.3 步：修订循环

对每个 critical/high 问题：
1. 找出受影响的具体小节
2. 起草修复
3. 核验修复不破坏其他论断
4. 更新论文
5. 对照审稿人的关切复查

### 第 6.4 步：写评审回复

回应真实评审（投稿后）时，评审回复是与修订不同的一项技能：

**格式**：逐条回应。对审稿人的每个关切：
```
> R1-W1: "The paper lacks comparison with Method X."

We thank the reviewer for this suggestion. We have added a comparison with 
Method X in Table 3 (revised). Our method outperforms X by 3.2pp on [metric] 
(p<0.05). We note that X requires 2x our compute budget.
```

**规则**：
- 回应每个关切 — 你跳过一条审稿人会注意到
- 最强的回应放前面
- 简洁直接 — 审稿人要读几十份回复
- 若在回复期跑了实验，把新结果放进去
- 绝不防御或轻慢，即便是对软弱的批评
- 用 `latexdiff` 生成标注改动的 PDF（见 Professional LaTeX Tooling 小节）
- 感谢审稿人具体、可操作的反馈（不是泛泛的称赞）

**不该做的**：无证据的 "We respectfully disagree"。无解释的 "This is out of scope"。只回应优点、无视弱点。

### 第 6.5 步：跟踪论文演进

在关键里程碑保存快照：
```
paper/
  paper.tex                    # Current working version
  paper_v1_first_draft.tex     # First complete draft
  paper_v2_post_review.tex     # After simulated review
  paper_v3_pre_submission.tex  # Final before submission
  paper_v4_camera_ready.tex    # Post-acceptance final
```

---

## 阶段 7：投稿准备

**目标**：终检、格式化与投稿。

### 第 7.1 步：会议清单

每个 venue 都有强制清单。仔细填完 — 清单不完整可能导致 desk rejection。

以下内容见 [references/checklists.md](references/checklists.md)：
- NeurIPS 16 项论文清单
- ICML broader impact + 可复现性
- ICLR LLM 披露政策
- ACL 强制的 limitations 小节
- 通用投稿前清单

### 第 7.2 步：匿名化清单

双盲评审意味着审稿人不能知道论文作者。核对**全部**这些：

```
Anonymization Checklist:
- [ ] No author names or affiliations anywhere in the PDF
- [ ] No acknowledgments section (add after acceptance)
- [ ] Self-citations written in third person: "Smith et al. [1] showed..." not "We previously showed [1]..."
- [ ] No GitHub/GitLab URLs pointing to your personal repos
- [ ] Use Anonymous GitHub (https://anonymous.4open.science/) for code links
- [ ] No institutional logos or identifiers in figures
- [ ] No file metadata containing author names (check PDF properties)
- [ ] No "our previous work" or "in our earlier paper" phrasing
- [ ] Dataset names don't reveal institution (rename if needed)
- [ ] Supplementary materials don't contain identifying information
```

**常见错误**：补充代码里可见的 git 提交信息、机构工具的带水印图、上一版草稿留下的致谢、匿名期前就挂上的 arXiv 预印本。

### 第 7.3 步：格式化核验

```
Pre-Submission Format Check:
- [ ] Page limit respected (excluding references and appendix)
- [ ] All figures are vector (PDF) or high-res raster (600 DPI PNG)
- [ ] All figures readable in grayscale
- [ ] All tables use booktabs
- [ ] References compile correctly (no "?" in citations)
- [ ] No overfull hboxes in critical areas
- [ ] Appendix clearly labeled and separated
- [ ] Required sections present (limitations, broader impact, etc.)
```

### 第 7.4 步：编译前校验

在尝试 `pdflatex` **之前**跑这些自动检查。在这里抓错比调试编译器输出更快。

```bash
# 1. Lint with chktex (catches common LaTeX mistakes)
# Suppress noisy warnings: -n2 (sentence end), -n24 (parens), -n13 (intersentence), -n1 (command terminated)
chktex main.tex -q -n2 -n24 -n13 -n1

# 2. Verify all citations exist in .bib
# Extract \cite{...} from .tex, check each against .bib
python3 -c "
import re
tex = open('main.tex').read()
bib = open('references.bib').read()
cites = set(re.findall(r'\\\\cite[tp]?{([^}]+)}', tex))
for cite_group in cites:
    for cite in cite_group.split(','):
        cite = cite.strip()
        if cite and cite not in bib:
            print(f'WARNING: \\\\cite{{{cite}}} not found in references.bib')
"

# 3. Verify all referenced figures exist on disk
python3 -c "
import re, os
tex = open('main.tex').read()
figs = re.findall(r'\\\\includegraphics(?:\[.*?\])?{([^}]+)}', tex)
for fig in figs:
    if not os.path.exists(fig):
        print(f'WARNING: Figure file not found: {fig}')
"

# 4. Check for duplicate \label definitions
python3 -c "
import re
from collections import Counter
tex = open('main.tex').read()
labels = re.findall(r'\\\\label{([^}]+)}', tex)
dupes = {k: v for k, v in Counter(labels).items() if v > 1}
for label, count in dupes.items():
    print(f'WARNING: Duplicate label: {label} (appears {count} times)')
"
```

继续前修掉所有告警。对基于 agent 的工作流：把 chktex 输出喂回 agent 并指示做最小修复。

### 第 7.5 步：最终编译

```bash
# Clean build
rm -f *.aux *.bbl *.blg *.log *.out *.pdf
latexmk -pdf main.tex

# Or manual (triple pdflatex + bibtex for cross-references)
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex

# Verify output exists and has content
ls -la main.pdf
```

**若编译失败**：解析 `.log` 文件找第一个错误。常见修复：
- "Undefined control sequence" → 缺包或命令名拼错
- "Missing $ inserted" → 数学符号在数学模式之外
- "File not found" → 图路径错或缺 .sty 文件
- "Citation undefined" → .bib 条目缺失或未跑 bibtex

### 第 7.6 步：各会议专属要求

| Venue | 特殊要求 |
|-------|---------------------|
| **NeurIPS** | 附录中的论文清单；录用后写通俗摘要 |
| **ICML** | Broader Impact Statement（结论之后，不计页数） |
| **ICLR** | 强制 LLM 披露、互评协议 |
| **ACL** | 强制 Limitations 小节、Responsible NLP 清单 |
| **AAAI** | 严格样式文件 — 绝不许任何修改 |
| **COLM** | 面向语言模型社区表述贡献 |

### 第 7.7 步：会议重投与格式转换

在 venue 之间转换时，**绝不在模板间复制 LaTeX 导言区**：

```bash
# 1. Start fresh with target template
cp -r templates/icml2026/ new_submission/

# 2. Copy ONLY content sections (not preamble)
#    - Abstract text, section content, figures, tables, bib entries

# 3. Adjust for page limits
# 4. Add venue-specific required sections
# 5. Update references
```

| 从 → 到 | 页数变化 | 关键调整 |
|-----------|-------------|-----------------|
| NeurIPS → ICML | 9 → 8 | 砍 1 页，加 Broader Impact |
| ICML → ICLR | 8 → 9 | 扩充实验，加 LLM 披露 |
| NeurIPS → ACL | 9 → 8 | 按 NLP 惯例重组，加 Limitations |
| ICLR → AAAI | 9 → 7 | 大幅删减，严格遵守样式 |
| 任意 → COLM | 不定 → 9 | 按语言模型重心重构 |

删页时：把证明移到附录、精简相关工作、合并表格、用子图。
扩页时：加消融、扩充 limitations、纳入更多基线、加定性示例。

**被拒之后**：在新版本里回应审稿人关切，但不要放 "changes" 小节，也不要提及上次投稿（盲审）。

### 第 7.8 步：Camera-Ready 准备（录用后）

录用后，准备 camera-ready 版本：

```
Camera-Ready Checklist:
- [ ] De-anonymize: add author names, affiliations, email addresses
- [ ] Add Acknowledgments section (funding, compute grants, helpful reviewers)
- [ ] Add public code/data URL (real GitHub, not anonymous)
- [ ] Address any mandatory revisions from meta-reviewer
- [ ] Switch template to camera-ready mode (if applicable — e.g., AAAI \anon → \camera)
- [ ] Add copyright notice if required by venue
- [ ] Update any "anonymous" placeholders in text
- [ ] Verify final PDF compiles cleanly
- [ ] Check page limit for camera-ready (sometimes differs from submission)
- [ ] Upload supplementary materials (code, data, appendix) to venue portal
```

### 第 7.9 步：arXiv 与预印本策略

在 ML 里挂 arXiv 是标准做法，但有重要的时机与匿名考量。

**时机决策树：**

| 情形 | 建议 |
|-----------|---------------|
| 投双盲 venue（NeurIPS、ICML、ACL） | 在截稿**之后**挂 arXiv，别提前。提前挂严格说会违反匿名政策，尽管执行力度不一。 |
| 投 ICLR | ICLR 明确允许投稿前挂 arXiv。但别在投稿件本身写作者名。 |
| 论文已在 arXiv，投新 venue | 多数 venue 可接受。**别**在评审期用提及评审意见的改动去更新 arXiv 版本。 |
| Workshop 论文 | arXiv 随时挂都行 — workshop 通常不是双盲。 |
| 想确立优先权 | 担心被抢发就立刻挂 — 但要接受匿名的代价。 |

**arXiv 分类选择**（ML/AI 论文）：

| 分类 | 代码 | 最适合 |
|----------|------|----------|
| Machine Learning | `cs.LG` | 通用 ML 方法 |
| Computation and Language | `cs.CL` | NLP、语言模型 |
| Artificial Intelligence | `cs.AI` | 推理、规划、agent |
| Computer Vision | `cs.CV` | 视觉模型 |
| Information Retrieval | `cs.IR` | 搜索、推荐 |

**列一个主分类 + 1-2 个交叉分类。** 分类越多曝光越大，但只在确相关处交叉。

**版本策略：**
- **v1**：初始投稿（与会议投稿件一致）
- **v2**：录用后带 camera-ready 更正的版本（摘要里加 "accepted at [Venue]"）
- 别在评审期挂出明显回应审稿人反馈改动的 v2

```bash
# Check if your paper's title is already taken on arXiv
# (before choosing a title)
pip install arxiv
python -c "
import arxiv
results = list(arxiv.Search(query='ti:\"Your Exact Title\"', max_results=5).results())
print(f'Found {len(results)} matches')
for r in results: print(f'  {r.title} ({r.published.year})')
"
```

### 第 7.10 步：研究代码打包

发布干净、可运行的代码会显著提升引用量与审稿人信任。把代码与 camera-ready 投稿件一起打包。

**仓库结构：**

```
your-method/
  README.md              # Setup, usage, reproduction instructions
  requirements.txt       # Or environment.yml for conda
  setup.py               # For pip-installable packages
  LICENSE                # MIT or Apache 2.0 recommended for research
  configs/               # Experiment configurations
  src/                   # Core method implementation
  scripts/               # Training, evaluation, analysis scripts
    train.py
    evaluate.py
    reproduce_table1.sh  # One script per main result
  data/                  # Small data or download scripts
    download_data.sh
  results/               # Expected outputs for verification
```

**研究代码的 README 模板：**

```markdown
# [Paper Title]

Official implementation of "[Paper Title]" (Venue Year).

## Setup
[Exact commands to set up environment]

## Reproduction
To reproduce Table 1: `bash scripts/reproduce_table1.sh`
To reproduce Figure 2: `python scripts/make_figure2.py`

## Citation
[BibTeX entry]
```

**发布前清单：**
```
- [ ] Code runs from a clean clone (test on fresh machine or Docker)
- [ ] All dependencies pinned to specific versions
- [ ] No hardcoded absolute paths
- [ ] No API keys, credentials, or personal data in repo
- [ ] README covers setup, reproduction, and citation
- [ ] LICENSE file present (MIT or Apache 2.0 for max reuse)
- [ ] Results are reproducible within expected variance
- [ ] .gitignore excludes data files, checkpoints, logs
```

**投稿用的匿名代码**（录用前）：
```bash
# Use Anonymous GitHub for double-blind review
# https://anonymous.4open.science/
# Upload your repo → get an anonymous URL → put in paper
```

---

## 阶段 8：录用后交付物

**目标**：通过展示材料与社区互动，最大化录用论文的影响力。

### 第 8.1 步：会议 Poster

多数会议要求 poster 环节。Poster 设计原则：

| 元素 | 指引 |
|---------|-----------|
| **尺寸** | 查 venue 要求（通常 24"x36" 或 A0 竖版/横版） |
| **内容** | 标题、作者、一句话贡献、方法图、2-3 个关键结果、结论 |
| **动线** | 从左到右、从上到下（Z 形）或分栏 |
| **文字** | 标题 3m 可读，正文 1m 可读。不要整段 — 只用要点。 |
| **图** | 复用论文的图但更高分辨率。放大关键结果。 |

**工具**：LaTeX（`beamerposter` 包）、PowerPoint/Keynote、Figma、Canva。

**制作**：会前 2+ 周下单。布质 poster 便于携带。许多会议现在也支持虚拟/数字 poster。

### 第 8.2 步：会议 Talk / Spotlight

若获得 oral 或 spotlight 报告：

| 报告类型 | 时长 | 内容 |
|-----------|----------|---------|
| **Spotlight** | 5 分钟 | 问题、方法、一个关键结果。排练到正好 5 分钟。 |
| **Oral** | 15-20 分钟 | 完整故事：问题、方法、关键结果、消融、局限。 |
| **Workshop talk** | 10-15 分钟 | 按 workshop 受众调整 — 可能需要更多背景。 |

**幻灯片设计规则：**
- 一页一个想法
- 文字最小化 — 细节靠讲，别投在屏幕上
- 给关键图做动画，逐步建立理解
- 结尾放一页「takeaway」（一句话贡献）
- 为预期问题准备备用幻灯片

### 第 8.3 步：博客 / 社交媒体

通俗的摘要会显著提升影响力：

- **Twitter/X thread**：5-8 条推文。先说结果，不说方法。附图 1 与关键结果图。
- **博客**：800-1500 字。写给 ML 从业者，不是审稿人。跳过形式化，强调直觉与实际意义。
- **项目页**：含摘要、图、demo、代码链接、BibTeX 的 HTML 页。用 GitHub Pages。

**时机**：论文出现在 proceedings 或 arXiv camera-ready 后 1-2 天内发布。

---

## Workshop 与短文

Workshop 论文与短文（如 ACL short papers、Findings papers）走同样的流水线，但约束与期待不同。

### Workshop 论文

| 属性 | Workshop | 主会 |
|----------|----------|-----------------|
| **页数限制** | 通常 4-6 页 | 7-9 页 |
| **评审标准** | 对完整性要求更低 | 必须完整、彻底 |
| **评审流程** | 通常单盲或轻量评审 | 双盲、严格 |
| **看重的** | 有趣想法、初步结果、立场文章 | 带强基线的完整实证故事 |
| **arXiv** | 随时挂 | 时机有讲究（见 arXiv 策略） |
| **贡献门槛** | 新颖方向、有趣负结果、进行中工作 | 带强证据的重大进展 |

**何时瞄准 workshop：**
- 想在写全文前拿到反馈的早期想法
- 不值得写 8+ 页的负结果
- 对时效话题的立场文章或观点
- 复现研究或可复现性报告

### ACL 短文与 Findings

ACL 系 venue 有不同的投稿类型：

| 类型 | 页数 | 期待内容 |
|------|-------|-----------------|
| **Long paper** | 8 | 完整研究、强基线、消融 |
| **Short paper** | 4 | 聚焦贡献：一个有证据的清晰点 |
| **Findings** | 8 | 差一点进主会的扎实工作 |

**短文策略**：挑**一个**论断并彻底支撑它。别想把长文压进 4 页 — 写一篇不同、更聚焦的论文。

---

## 实证 ML 之外的论文类型

上面的主流水线面向实证 ML 论文。其他论文类型需要不同的结构与证据标准。各类型的详细指引见 [references/paper-types.md](references/paper-types.md)。

### 理论论文

**结构**：引言 → 预备（定义、记号） → 主要结果（定理） → 证明概要 → 讨论 → 完整证明（附录）

**与实证论文的关键差异：**
- 贡献是定理、界或不可能性结果 — 不是实验数字
- Methods 小节被「Preliminaries」与「Main Results」取代
- 证明就是证据，而非实验（不过对理论的实证验证也受欢迎）
- 正文放证明概要、附录放完整证明是标准做法
- 实验小节可选，但若它能验证理论预测就会增强论文

**证明写作原则：**
- 正式陈述定理，所有假设都写明
- 在正式证明前给直觉（"The key insight is..."）
- 证明概要用 0.5-1 页传达主要思路
- 用 `\begin{proof}...\end{proof}` 环境
- 给假设编号并在定理中引用："Under Assumptions 1-3, ..."

### 综述 / 教程论文

**结构**：引言 → 分类法 / 组织 → 详细覆盖 → 开放问题 → 结论

**关键差异：**
- 贡献在于组织、综合与识别开放问题 — 不是新方法
- 在范围内必须全面（审稿人会查漏引）
- 需要清晰的分类法或组织框架
- 价值来自单篇论文不会做的、作品间的联系
- 最佳 venue：TMLR（survey track）、JMLR、Foundations and Trends in ML、ACM Computing Surveys

### 基准论文

**结构**：引言 → 任务定义 → 数据集构建 → 基线评测 → 分析 → 预期用途与局限

**关键差异：**
- 贡献就是基准本身 — 它必须填补一个真实的评测缺口
- 数据集文档是强制而非可选（见 Datasheets，第 5.11 步）
- 必须证明该基准有挑战性（基线没有把它打满）
- 必须证明该基准测的就是你声称它测的（构念效度）
- 最佳 venue：NeurIPS Datasets & Benchmarks track、ACL（resource papers）、LREC-COLING

### 立场论文

**结构**：引言 → 背景 → 论点 / 论证 → 支撑证据 → 反驳 → 启示

**关键差异：**
- 贡献是一个论证，不是一个结果
- 必须认真对待反驳意见
- 证据可以是实证、理论或逻辑分析
- 最佳 venue：ICML（position track）、workshop、TMLR

---

## Hermes Agent 集成

本 skill 为 Hermes agent 设计。它用 Hermes 的工具、委派、调度与记忆来覆盖完整研究生命周期。

### 相关 skills

在特定阶段与其他 Hermes skills 组合使用：

| Skill | 何时用 | 如何加载 |
|-------|-------------|-------------|
| **arxiv** | 阶段 1（文献综述）：搜 arXiv、生成 BibTeX、经 Semantic Scholar 找相关论文 | `skill_view("arxiv")` |
| **subagent-driven-development** | 阶段 5（写作）：并行分节写作，带两阶段评审（先符合规格再质量） | `skill_view("subagent-driven-development")` |
| **plan** | 阶段 0（搭建）：执行前创建结构化计划。写入 `.hermes/plans/` | `skill_view("plan")` |
| **qmd** | 阶段 1（文献）：经 BM25+向量混合检索搜本地知识库（笔记、转录、文档） | 安装：`skill_manage("install", "qmd")` |
| **diagramming** | 阶段 4-5：创建基于 Excalidraw 的图与架构图 | `skill_view("diagramming")` |
| **data-science** | 阶段 4（分析）：用 Jupyter 常驻内核做交互式分析与可视化 | `skill_view("data-science")` |

**本 skill 取代 `ml-paper-writing`** — 它包含 ml-paper-writing 的全部内容，外加完整的实验/分析流水线与 autoreason 方法论。

### Hermes 工具参考

| 工具 | 在本流水线中的用途 |
|------|----------------------|
| **`terminal`** | LaTeX 编译（`latexmk -pdf`）、git 操作、启动实验（`nohup python run.py &`）、进程检查 |
| **`process`** | 后台实验管理：`process("start", ...)`、`process("poll", pid)`、`process("log", pid)`、`process("kill", pid)` |
| **`execute_code`** | 跑 Python 做引用核验、统计分析、数据聚合。经 RPC 具备工具访问。 |
| **`read_file`** / **`write_file`** / **`patch`** | 论文编辑、实验脚本、结果文件。对大 .tex 文件的定点编辑用 `patch`。 |
| **`web_search`** | 文献发现：`web_search("transformer attention mechanism 2024")` |
| **`web_extract`** | 抓取论文内容、核验引用：`web_extract("https://arxiv.org/abs/2303.17651")` |
| **`delegate_task`** | **并行分节写作** — 为每节生成隔离的 subagent。也用于并发引用核验。 |
| **`todo`** | 跨会话的主要状态跟踪器。每次阶段切换后更新。 |
| **`memory`** | 跨会话持久化关键决策：贡献表述、venue 选择、审稿反馈。 |
| **`cronjob`** | 安排实验监控、倒计时、自动化 arXiv 检查。 |
| **`clarify`** | 卡住时（venue 选择、贡献表述）向用户提有针对性的问题。 |
| **cron `deliver:`** | 实验完成或草稿就绪时通知用户（即便用户不在聊天里）— 把检查排成带消息 `deliver:` 目标的 cron job（agent 已无 `send_message` 工具；外发由 cron/`hermes send` 处理）。 |

### 工具使用模式

**实验监控**（最常用）：
```
terminal("ps aux | grep <pattern>")
→ terminal("tail -30 <logfile>")
→ terminal("ls results/")
→ execute_code("analyze results JSON, compute metrics")
→ terminal("git add -A && git commit -m '<descriptive message>' && git push")
→ (final response auto-delivers "Experiment complete: <summary>"; for unattended runs, schedule via cron with a deliver: target)
```

**并行分节写作**（用委派）：
```
delegate_task("Draft the Methods section based on these experiment scripts and configs. 
  Include: pseudocode, all hyperparameters, architectural details sufficient for 
  reproduction. Write in LaTeX using the neurips2025 template conventions.")

delegate_task("Draft the Related Work section. Use web_search and web_extract to 
  find papers. Verify every citation via Semantic Scholar. Group by methodology.")

delegate_task("Draft the Experiments section. Read all result files in results/. 
  State which claim each experiment supports. Include error bars and significance.")
```

每个委派都以**全新 subagent** 运行、无共享上下文 — 在 prompt 里提供全部必要信息。收集输出并整合。

**引用核验**（用 execute_code）：
```python
# In execute_code:
from semanticscholar import SemanticScholar
import requests

sch = SemanticScholar()
results = sch.search_paper("attention mechanism transformers", limit=5)
for paper in results:
    doi = paper.externalIds.get('DOI', 'N/A')
    if doi != 'N/A':
        bibtex = requests.get(f"https://doi.org/{doi}", 
                              headers={"Accept": "application/x-bibtex"}).text
        print(bibtex)
```

### 用 `memory` 与 `todo` 做状态管理

**`memory` 工具** — 持久化关键决策（有界：MEMORY.md 约 2200 字符）：

```
memory("add", "Paper: autoreason. Venue: NeurIPS 2025 (9 pages). 
  Contribution: structured refinement works when generation-evaluation gap is wide.
  Key results: Haiku 42/42, Sonnet 3/5, S4.6 constrained 2/3.
  Status: Phase 5 — drafting Methods section.")
```

重大决策或阶段切换后更新 memory。它跨会话持久。

**`todo` 工具** — 跟踪细粒度进展：

```
todo("add", "Design constrained task experiments for Sonnet 4.6")
todo("add", "Run Haiku baseline comparison")
todo("add", "Draft Methods section")
todo("update", id=3, status="in_progress")
todo("update", id=1, status="completed")
```

**会话启动协议：**
```
1. todo("list")                           # Check current task list
2. memory("read")                         # Recall key decisions
3. terminal("git log --oneline -10")      # Check recent commits
4. terminal("ps aux | grep python")       # Check running experiments
5. terminal("ls results/ | tail -20")     # Check for new results
6. Report status to user, ask for direction
```

### 用 `cronjob` 做 Cron 监控

用 `cronjob` 工具安排周期性实验检查：

```
cronjob("create", {
  "schedule": "*/30 * * * *",  # Every 30 minutes
  "prompt": "Check experiment status:
    1. ps aux | grep run_experiment
    2. tail -30 logs/experiment_haiku.log
    3. ls results/haiku_baselines/
    4. If complete: read results, compute Borda scores, 
       git add -A && git commit -m 'Add Haiku results' && git push
    5. Report: table of results, key finding, next step
    6. If nothing changed: respond with [SILENT]"
})
```

**[SILENT] 协议**：自上次检查以来无变化时，恰好回复 `[SILENT]`。这会抑制对用户的通知投递。只在有值得知道的真实变化时才报告。

**倒计时跟踪**：
```
cronjob("create", {
  "schedule": "0 9 * * *",  # Daily at 9am
  "prompt": "NeurIPS 2025 deadline: May 22. Today is {date}. 
    Days remaining: {compute}. 
    Check todo list — are we on track? 
    If <7 days: warn user about remaining tasks."
})
```

### 沟通模式

**何时通知用户**（通过你的直接/最终回复，或无人值守运行时的 cron `deliver:` 目标）：
- 一批实验完成（附结果表）
- 需要决策的意外发现或失败
- 草稿小节可供审阅
- 临近死线但有未完成任务

**何时不通知：**
- 实验仍在跑、无新结果 → `[SILENT]`
- 例行监控无变化 → `[SILENT]`
- 不需要关注的中间步骤

**报告格式** — 始终包含结构化数据：
```
## Experiment: <name>
Status: Complete / Running / Failed

| Task | Method A | Method B | Method C |
|------|---------|---------|---------|
| Task 1 | 85.2 | 82.1 | **89.4** |

Key finding: <one sentence>
Next step: <what happens next>
```

### 需要人类输入的决策点

真卡住时，用 `clarify` 提有针对性的问题：

| 决策 | 何时问 |
|----------|-------------|
| 目标 venue | 动笔前（影响页数限制、表述） |
| 贡献表述 | 存在多种可行表述时 |
| 实验优先级 | 当 TODO 里的实验多于时间允许时 |
| 投稿就绪度 | 最终投稿前 |

**不要问**（主动、做选择、标出来）：
- 用词、小节顺序
- 突出哪些具体结果
- 引用完整性（用手头找到的先写，标注缺口）

---

## 审稿人评估标准

了解审稿人在找什么有助于聚焦精力：

| 标准 | 他们查什么 |
|-----------|----------------|
| **Quality** | 技术可靠性、论断支撑充分、基线公平 |
| **Clarity** | 行文清晰、专家可复现、记号一致 |
| **Significance** | 社区影响、推进理解 |
| **Originality** | 新洞见（不要求新方法） |

**评分（NeurIPS 6 分制）：**
- 6：Strong Accept — 开创性、无瑕
- 5：Accept — 技术扎实、高影响
- 4：Borderline Accept — 扎实但评估有限
- 3：Borderline Reject — 弱点压过优点
- 2：Reject — 技术缺陷
- 1：Strong Reject — 已知结果或伦理问题

详细指引、常见关切与评审回复策略见 [references/reviewer-guidelines.md](references/reviewer-guidelines.md)。

---

## 常见问题与解决

| 问题 | 解决 |
|-------|----------|
| 摘要太泛 | 若首句能套用到任何 ML 论文，就删掉。从你的具体贡献写起。 |
| 引言超过 1.5 页 | 把背景拆到 Related Work。把贡献要点前置。 |
| 实验缺明确论断 | 每个实验前加："This experiment tests whether [specific claim]..."。 |
| 审稿人觉得难跟 | 加路标、术语一致、图注自足。 |
| 缺统计显著性 | 加误差棒、运行次数、统计检验、置信区间。 |
| 实验范围蔓延 | 每个实验必须映射到具体论断。砍掉不映射的。 |
| 论文被拒需重投 | 见阶段 7 的会议重投。回应审稿人关切但不提及评审意见。 |
| 缺 broader impact 声明 | 见第 5.10 步。多数 venue 要求它。"No negative impacts" 几乎从不可信。 |
| 人工评测被批太弱 | 见第 2.5 步与 [references/human-evaluation.md](references/human-evaluation.md)。报告一致性指标、标注员细节、报酬。 |
| 审稿人质疑可复现性 | 发布代码（第 7.9 步）、记录所有超参、含种子与算力细节。 |
| 理论论文缺直觉 | 在正式证明前加带白话解释的证明概要。见 [references/paper-types.md](references/paper-types.md)。 |
| 结果是负/零 | 见阶段 4.3 关于处理负结果。考虑 workshop、TMLR，或重构为分析。 |

---

## 参考文档

| 文档 | 内容 |
|----------|----------|
| [references/writing-guide.md](references/writing-guide.md) | Gopen & Swan 7 原则、Perez 微观技巧、Lipton 用词、Steinhardt 精确、图设计 |
| [references/citation-workflow.md](references/citation-workflow.md) | 引用 API、Python 代码、CitationManager 类、BibTeX 管理 |
| [references/checklists.md](references/checklists.md) | NeurIPS 16 项、ICML、ICLR、ACL 要求、通用投稿前清单 |
| [references/reviewer-guidelines.md](references/reviewer-guidelines.md) | 评估标准、评分、常见关切、评审回复模板 |
| [references/sources.md](references/sources.md) | 所有写作指南、会议指引、API 的完整书目 |
| [references/experiment-patterns.md](references/experiment-patterns.md) | 实验设计模式、评测协议、监控、错误恢复 |
| [references/autoreason-methodology.md](references/autoreason-methodology.md) | Autoreason 循环、策略选择、模型指南、prompt、范围约束、Borda 打分 |
| [references/human-evaluation.md](references/human-evaluation.md) | 人工评测设计、标注指南、一致性指标、众包质检、IRB 指引 |
| [references/paper-types.md](references/paper-types.md) | 理论论文（证明写作、定理结构）、综述论文、基准论文、立场论文 |

### LaTeX 模板

`templates/` 里的模板涵盖：**NeurIPS 2025**、**ICML 2026**、**ICLR 2026**、**ACL**、**AAAI 2026**、**COLM 2025**。

编译说明见 [templates/README.md](templates/README.md)。

### 关键外部来源

**写作哲学：**
- [Neel Nanda: How to Write ML Papers](https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers)
- [Sebastian Farquhar: How to Write ML Papers](https://sebastianfarquhar.com/on-research/2024/11/04/how_to_write_ml_papers/)
- [Gopen & Swan: Science of Scientific Writing](https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf)
- [Lipton: Heuristics for Scientific Writing](https://www.approximatelycorrect.com/2018/01/29/heuristics-technical-scientific-writing-machine-learning-perspective/)
- [Perez: Easy Paper Writing Tips](https://ethanperez.net/easy-paper-writing-tips/)

**API：** [Semantic Scholar](https://api.semanticscholar.org/api-docs/) | [CrossRef](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | [arXiv](https://info.arxiv.org/help/api/basics.html)

**Venues：** [NeurIPS](https://neurips.cc/Conferences/2025/PaperInformation/StyleFiles) | [ICML](https://icml.cc/Conferences/2025/AuthorInstructions) | [ICLR](https://iclr.cc/Conferences/2026/AuthorGuide) | [ACL](https://github.com/acl-org/acl-style-files)
