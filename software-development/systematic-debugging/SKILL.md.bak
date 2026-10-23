---
name: systematic-debugging
description: "四阶段根因调试时使用：先弄懂，再动手修。只要遇到测试失败、线上 bug、异常行为或性能问题，就主动加载，即使用户没明说根因。没找到 root cause 之前不许动手修。"
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    related_skills: [test-driven-development, subagent-driven-development]
---

# 系统化调试

## Overview（概览）

乱修浪费时间、制造新 bug。快补丁掩盖底层问题。

**核心原则：** 动手修之前，永远先找到根因。修症状就是失败。

**违背本流程的字面，就是违背调试的精神。**

## The Iron Law（铁律）

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

若没完成 Phase 1，你就不能提修复方案。

## The Feedback Loop Rule（反馈环规则）

反馈环就是调试工作本身。在读代码构建理论之前，先创建或找到一个**紧凑**命令，它能在用户的确切症状上变红、在 bug 修好后变绿。紧凑环快、确定、可由 agent 运行，且足够具体到能抓住这个 bug——而不只是"没崩"。

干净复现难做时，要在搭环上舍得花不成比例的力气。没有可变红的环就靠猜，正是本技能存在的意义所要防的失败模式。

## When to Use（何时用）

任何技术问题都用：
- 测试失败
- 线上 bug
- 异常行为
- 性能问题
- 构建失败
- 集成问题

**尤其在这些时候用：**
- 时间压力下（紧急情况让猜测变得诱人）
- "就一个快补丁" 看起来明摆着
- 你已经试过多个修复
- 上一个修复没用
- 你还没完全搞懂问题

**这些情况下别跳过：**
- 问题看着简单（简单 bug 也有根因）
- 你在赶（赶工保证返工）
- 有人要你**现在**就修好（系统化比乱扑腾快）

## The Four Phases（四个阶段）

必须完成每个阶段才能进下一个。

---

## Phase 1: Root Cause Investigation（根因调查）

**在尝试任何修复之前：**

### 1. 仔细读错误信息

- 别跳过错误或警告
- 它们常含确切答案
- 完整读栈回溯
- 记下行号、文件路径、错误码

**动作：** 对相关源文件用 `read_file`。用 `search_files` 在代码库里找错误字符串。

### 2. 搭一个紧凑反馈环

- 你能用一条命令触发用户的确切症状吗？
- 该命令会因这个 bug 而失败、且只在 bug 修好后通过吗？
- 它够快、能反复跑吗？
- 它确定吗？对偶发 bug，你能把复现率提到足够高、可调试吗？
- 若不可复现 → 收集更多数据，别猜。

**搭环的各种方式——大致按这个顺序试：**

1. **失败测试**，落在能到达 bug 的接缝上：单元、集成或端到端。
2. **HTTP 脚本 / curl**，打运行中的 dev server。
3. **CLI 调用**带固定输入，把 stdout/stderr 与期望输出做 diff。
4. **无头浏览器脚本**（Playwright/Puppeteer）对 DOM、控制台或网络做断言。
5. **重放进抓取的 trace**：HAR、请求 payload、事件日志、队列消息或 webhook body。
6. **一次性测试台**，起系统里最小的有用切片并调用失败路径。
7. **属性 / fuzz 环**，当 bug 是在广阔输入空间上的间歇性错误输出时。
8. **二分测试台**，适合 `git bisect run`，当 bug 出现在两个已知状态之间时。
9. **差分环**，比较旧版 vs 新版、两套配置、两个 provider 或两份数据集。
10. **人在环脚本**，仅作最后手段：把人做步骤脚本化并捕获其结果，好让环保持结构化。

**环一旦存在，就把它收得更紧：**

- 让它更快：缓存 setup、收窄范围、跳过无关初始化。
- 让信号更锐：断言确切症状，而不是泛泛的成功。
- 让它更确定：钉住时间、固定随机种子、隔离文件系统、冻结网络。

对非确定 bug，眼下的目标是更高的复现率而非完美。把触发器跑 100 次、并行化、加压力、收窄时间窗，或注入 sleep。50% 的偶发可调；1% 的通常调不动。

**动作：** 用 `terminal` 工具跑紧凑环：

```bash
# Run a specific failing test
pytest tests/test_module.py::test_name -v

# Or run a scripted repro
python scripts/repro_bug.py

# Or run a high-repetition flaky repro
for i in {1..100}; do pytest tests/test_flake.py::test_name -q || break; done
```

### 3. 检查近期改动

- 什么改了可能导致这个？
- Git diff、近期提交
- 新依赖、配置改动

**动作：**

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git diff

# Changes in specific file
git log -p --follow src/problematic_file.py | head -100
```

### 4. 在多组件系统里收集证据

**当系统有多个组件（API → service → database、CI → build → deploy）时：**

**提修复方案之前，先加诊断探针：**

对**每个**组件边界：
- 记录什么数据进入该组件
- 记录什么数据离开该组件
- 核验环境/配置的传播
- 检查每一层的状态

跑一次以收集证据，显示它**在哪儿**断。
**然后**分析证据，定位失败的组件。
**然后**调查那个具体组件。

### 5. 追数据流

**当错误深在调用栈里时：**

- 坏值从哪儿来？
- 谁带着坏值调用了这个函数？
- 一直往上游追，直到找到源头
- 在源头修，不在症状处修

**动作：** 用 `search_files` 追引用：

```python
# Find where the function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where the variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

### Phase 1 完成清单

- [ ] 错误信息已完整读取并理解
- [ ] 存在一条紧凑环命令，且至少跑过一次
- [ ] 环可变红：它断言用户的确切症状，而非邻近的失败
- [ ] 环是确定的，或偶发 bug 的复现率已高到可调试
- [ ] 近期改动已找出并复查
- [ ] 证据已收集（日志、状态、数据流）
- [ ] 问题已隔离到具体组件/代码
- [ ] 根因假设能被陈述并检验

**停下：** 在你搞懂它**为什么**发生之前，别进 Phase 2。

---

## Phase 2: Pattern Analysis（模式分析）

**修之前先找模式：**

### 0. 把复现最小化

环变红之后，把复现缩到仍能变红的最小场景。**一次砍一处**输入、调用方、配置、数据与步骤，每砍一处后重跑环。只留下对失败承重的东西。

当移除任何剩余元素都会让环变绿时，就完成了。最小复现收窄假设空间，且常常成为最干净的回归测试。

### 1. 找可用的范例

- 在同一代码库里找相似的可运行代码
- 与坏掉的东西相似、而能工作的，是什么？

**动作：** 用 `search_files` 找可比的模式：

```python
search_files("similar_pattern", path="src/", file_glob="*.py")
```

### 2. 对照参考实现

- 若在实现某个模式，就**完整**读参考实现
- 别略读——每一行都读
- 应用前彻底理解该模式

### 3. 找出差异

- 能用的和坏掉的之间差在哪？
- 列出每一处差异，无论多小
- 别假设 "那个不可能有影响"

### 4. 理解依赖

- 它还需要哪些其他组件？
- 需要哪些设置、配置、环境？
- 它做了哪些假设？

---

## Phase 3: Hypothesis and Testing（假设与检验）

**科学方法：**

### 1. 形成可排序、可证伪的假设

- 在检验任何一个之前，先产出 3–5 个看似合理的假设。
- 按可能性和证伪的便宜程度排序。
- 陈述每个假设做出的预测："若 X 是原因，那么改动或观察 Y 应导致 Z 发生。"
- 丢掉或磨锐任何做不出可检验预测的假设。

若用户在场，检验前先把排序表给他们看。他们可能有瞬间重排它的领域知识。若用户不在，就按你的排序继续。

### 2. 最小化检验

- 用尽可能小的探针检验排位最高的假设。
- 一次改一个变量。
- 别同时修多件事。
- 可用时优先用调试器/REPL 检视；一个断点胜过十条日志。
- 若加日志，给每一临时行打上唯一前缀，如 `[DEBUG-a4f2]`，这样清理只需搜一次。

### 3. 继续之前先验证

- 好了吗？→ Phase 4
- 没好？→ 形成**新**假设
- **不要**在上面再叠更多修复

### 4. 当你不知道时

- 说 "I don't understand X"
- 别装懂
- 向用户求助
- 再调研

---

## Phase 4: Implementation（实施）

**修根因，不修症状：**

### 1. 造失败测试用例

- 尽可能简单的复现
- 能自动化就自动化
- 修之前**必须**有
- 用 `test-driven-development` 技能

### 2. 实施单个修复

- 针对已识别的根因
- **一次一个**改动
- 不要 "既然来了就顺手改改"
- 不要夹带重构

### 3. 验证修复

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v

# Run full suite — no regressions
pytest tests/ -q
```

### 4. 修复不奏效时——三振法则

- **停下。**
- 数一数：你试了几个修复了？
- 若 < 3：回 Phase 1，用新信息重新分析
- **若 ≥ 3：停下，质疑架构（见下面第 5 步）**
- 没有架构层面的讨论，**不要**尝试第 4 个修复

### 5. 3+ 个修复都失败：质疑架构

**指向架构问题的模式：**
- 每个修复都在不同地方暴露出新的共享状态/耦合
- 修复要落地需要 "massive refactoring"
- 每个修复都在别处造出新症状

**停下，质疑根本：**
- 这个模式根本上是合理的吗？
- 我们是不是 "纯粹出于惯性在硬撑它"？
- 该重构架构，还是继续修症状？

**再动更多修复之前，先和用户讨论。**

这**不是**假设失败——这是架构错了。

---

## Red Flags — STOP and Follow Process（红旗：停下，走流程）

若你发现自己冒出这些念头：
- "先快补丁，回头再查"
- "就试着改一下 X，看行不行"
- "一次加多个改动，跑测试"
- "跳过测试，我手动验证"
- "大概是 X，我来修那个"
- "我没完全搞懂，但这可能有用"
- "模式说的是 X，但我打算换个改法"
- "主要问题如下：[不走调查就列修复]"
- 追数据流之前就提方案
- **"再试一个修复"（已经试过 2+ 次时）**
- **每个修复都在不同地方暴露出新问题**

**以上全部意味着：停下。回 Phase 1。**

**若 3+ 个修复失败：** 质疑架构（Phase 4 第 5 步）。

## Common Rationalizations

| 借口 | 现实 |
|--------|---------|
| "问题简单，不需要流程" | 简单问题也有根因。对简单 bug，流程很快。 |
| "紧急，没时间走流程" | 系统化调试比猜了又试的乱扑腾**更快**。 |
| "先试这个，然后再查" | 第一个修复定下模式。一开始就做对。 |
| "等确认修复能用了我再写测试" | 未经测试的修复站不住。先写测试才能证明它。 |
| "一次多个修复省时间" | 没法隔离出哪个起了作用。还会造新 bug。 |
| "参考太长，我改编一下这个模式" | 半懂不通保证出 bug。完整读完。 |
| "我看到问题了，我来修" | 看到症状 ≠ 理解根因。 |
| "再试一个修复"（2+ 次失败后） | 3+ 次失败 = 架构问题。质疑模式，别再修。 |

## Quick Reference

| 阶段 | 关键活动 | 成功判据 |
|-------|---------------|------------------|
| **1. Root Cause** | 读错误、复现、查改动、收集证据、追数据流 | 搞懂 WHAT 和 WHY |
| **2. Pattern** | 找可用范例、对比、找差异 | 知道差在哪 |
| **3. Hypothesis** | 形成理论、最小化检验、一次一个变量 | 确认，或新假设 |
| **4. Implementation** | 造回归测试、修根因、验证 | bug 解决、全部测试通过 |

## Hermes Agent Integration（与 Hermes Agent 的集成）

### Investigation Tools（调查工具）

Phase 1 期间用这些 Hermes 工具：

- **`search_files`** — 找错误字符串、追函数调用、定位模式
- **`read_file`** — 带行号读源码，做精确分析
- **`terminal`** — 跑测试、查 git 历史、复现 bug
- **`web_search`/`web_extract`** — 调研错误信息、库文档

### With delegate_task（配合 delegate_task）

复杂多组件调试时，派出调查子代理：

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging skill:
    1. Read the error message carefully
    2. Reproduce the issue
    3. Trace the data flow to find root cause
    4. Report findings — do NOT fix yet

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=['terminal', 'file']
)
```

### With test-driven-development（配合 TDD）

修 bug 时：
1. 写一个能复现 bug 的测试（RED）
2. 系统化调试找出根因
3. 修根因（GREEN）
4. 该测试证明修复、并防回归

## Real-World Impact（真实效果）

来自实际调试会话：
- 系统化做法：15-30 分钟修好
- 乱修做法：2-3 小时乱扑腾
- 一次修好率：95% vs 40%
- 引入的新 bug：近乎零 vs 常见

**别走捷径。别猜。系统化永远赢。**
