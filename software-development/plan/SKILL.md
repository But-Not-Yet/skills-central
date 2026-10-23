---
name: plan
description: "只把 markdown 计划写进 .hermes/plans/、不执行代码时使用。只要用户要计划而非执行、或要拆解多步功能的实现方案，就主动加载，即使用户没明说 plan mode。附一份写优质实现计划的工艺。"
version: 2.0.0
author: Hermes Agent (writing-craft adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, plan-mode, implementation, workflow, design, documentation]
    related_skills: [subagent-driven-development, test-driven-development, requesting-code-review]
---

# Plan 模式

用户要的是计划而非执行时，用本技能。

## Core behavior（核心行为）

本轮你只做规划。

- 不要实现代码。
- 除计划 markdown 文件外，不要编辑项目文件。
- 不要跑会改动状态的终端命令、不要 commit、push 或做任何外部动作。
- 需要时可以只用读命令/工具查看仓库或其他上下文。
- 你的交付物是一份 markdown 计划，存进活动工作区下的 `.hermes/plans/`。

## Output requirements（产出要求）

写一份具体、可执行的 markdown 计划。

在相关时包含：
- 目标
- 当前上下文 / 假设
- 提议的做法
- 分步计划
- 可能改动的文件
- 测试 / 验证
- 风险、取舍与待决问题

若任务与代码有关，写明精确文件路径、可能的测试目标与验证步骤。

## Save location（保存位置）

用 `write_file` 把计划存到：
- `.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md`

把它视为相对于活动工作目录 / 后端工作区。Hermes 的文件工具是后端感知的，所以用这个相对路径能在 local、docker、ssh、modal、daytona 各后端上把计划留在工作区里。

若运行时给了具体目标路径，就用那个精确路径。
若没有，自己在 `.hermes/plans/` 下起一个像样的带时间戳文件名。

## Interaction style（交互风格）

- 请求足够清楚，就直接写计划。
- `/plan` 没带明确指令，就从当前对话上下文推断任务。
- 若真的欠定，问一句简短的澄清，而不是猜。
- 存好计划后，简要回复你规划了什么、以及保存路径。

---

# Writing the Plan Well（把计划写好）

本技能余下部分是撰写*优质*实现计划的手艺——也就是上面那个 markdown 文件里该放的内容。

## Overview（概览）

写实现计划时，假设执行者对这个代码库零上下文、品味堪忧。把需要的一切都写清：要碰哪些文件、完整代码、测试命令、要查的文档、怎么验证。给他们一口大小的任务。DRY。YAGNI。TDD。频繁提交。

假设执行者是个熟练开发者，但对这套工具链或问题域几乎一无所知。假设他们不太懂好的测试设计。

**核心原则：** 好计划让实现变得显而易见。若有人还得猜，计划就是不完整的。

## When a Full Implementation Plan Helps（何时值得写完整实现计划）

**在这些之前一律要用：**
- 实现多步功能
- 拆解复杂需求
- 通过 subagent-driven-development 委派给子代理

**这些情况下别跳过：**
- 功能看起来简单（假设会招来 bug）
- 你打算自己实现（未来的你需要指引）
- 独自工作（文档很重要）

## Bite-Sized Task Granularity（一口大小的任务粒度）

**每个任务 = 2-5 分钟的专注工作。**

每一步是一个动作：
- "写失败的测试" —— 一步
- "跑它，确认失败" —— 一步
- "实现最小代码让测试通过" —— 一步
- "跑测试，确认通过" —— 一步
- "提交" —— 一步

**太大：**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**合适的大小：**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Plan Document Structure（计划文档结构）

### Header（必需）

每份计划都必须以这样的头开头：

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Task Structure（任务结构）

每个任务照这个格式：

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Writing Process（写作流程）

### Step 1: Understand Requirements（搞懂需求）

读懂：
- 功能需求
- 设计文档或用户描述
- 验收判据
- 约束

### Step 2: Explore the Codebase（勘察代码库）

用 Hermes 工具理解项目：

```python
# Understand project structure
search_files("*.py", target="files", path="src/")

# Look at similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Check existing tests
search_files("*.py", target="files", path="tests/")

# Read key files
read_file("src/app.py")
```

### Step 3: Design Approach（设计做法）

敲定：
- 架构模式
- 文件组织
- 需要的依赖
- 测试策略

### Step 4: Write Tasks（写任务）

按顺序建任务：
1. 搭建/基础设施
2. 核心功能（每个都走 TDD）
3. 边界情况
4. 集成
5. 清理/文档

### Step 5: Add Complete Details（补齐细节）

每个任务都包含：
- **精确文件路径**（不是 "配置文件"，而是 `src/config/settings.py`）
- **完整代码示例**（不是 "加校验"，而是实际代码）
- **精确命令**带预期输出
- **验证步骤**，能证明任务可用

### Step 6: Review the Plan（复查计划）

检查：
- [ ] 任务顺序合理、有逻辑
- [ ] 每个任务都一口大小（2-5 分钟）
- [ ] 文件路径精确
- [ ] 代码示例完整（可复制粘贴）
- [ ] 命令精确且带预期输出
- [ ] 没有缺失的上下文
- [ ] 应用了 DRY、YAGNI、TDD 原则

## Principles（原则）

### DRY (Don't Repeat Yourself)

**坏：** 在 3 处复制粘贴同一段校验
**好：** 抽出校验函数，处处复用

### YAGNI (You Aren't Gonna Need It)

**坏：** 为未来需求加 "灵活性"
**好：** 只实现当下需要的

```python
# Bad — YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # Not needed yet!
        self.metadata = {}     # Not needed yet!

# Good — YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

### TDD (Test-Driven Development)

每个会产出代码的任务都应包含完整的 TDD 循环：
1. 写失败的测试
2. 跑一遍确认失败
3. 写最小代码
4. 跑一遍确认通过

细节见 `test-driven-development` 技能。

### Frequent Commits（频繁提交）

每完成一个任务就提交：
```bash
git add [files]
git commit -m "type: description"
```

## Common Mistakes（常见错误）

### Vague Tasks（任务含糊）

**坏：** "加认证"
**好：** "建带 email 和 password_hash 字段的 User model"

### Incomplete Code（代码不完整）

**坏：** "第 1 步：加校验函数"
**好：** "第 1 步：加校验函数" 后面跟上完整的函数代码

### Missing Verification（缺验证）

**坏：** "第 3 步：测一下能跑"
**好：** "第 3 步：跑 `pytest tests/test_auth.py -v`，预期：3 passed"

### Missing File Paths（缺文件路径）

**坏：** "建 model 文件"
**好：** "创建：`src/models/user.py`"

## Execution Handoff（执行交接）

存好计划后，给出执行方案：

**"计划已完成并保存。可以用 subagent-driven-development 来执行——我会每个任务派一个全新子代理，走两阶段审查（先规格合规、再代码质量）。要开始吗？"**

执行时，用 `subagent-driven-development` 技能：
- 每个任务派一个新的 `delegate_task`，带完整上下文
- 每个任务后做规格合规审查
- 规格通过后做代码质量审查
- 两项审查都通过才继续

## Remember（记住）

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**好计划让实现变得显而易见。**
