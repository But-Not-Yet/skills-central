---
name: test-driven-development
description: "走测试驱动开发（TDD）时使用：RED-GREEN-REFACTOR，先写测试再写码。只要要写新功能、修 bug 或重构，就主动加载，即使用户没明说 TDD。没看过测试失败就不算数。"
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [testing, tdd, development, quality, red-green-refactor]
    related_skills: [systematic-debugging, subagent-driven-development]
---

# 测试驱动开发（TDD）

## Overview（概览）

先写测试。看它失败。写最小代码让它通过。

**核心原则：** 若你没亲眼看过测试失败，你就不知道它测的是不是对的东西。

**违背规则的字面，就是违背规则的精神。**

## When to Use（何时用）

**永远：**
- 新功能
- 修 bug
- 重构
- 行为改动

**例外（先问用户）：**
- 一次性原型
- 生成的代码
- 配置文件

冒出 "就这一次跳过 TDD" 的念头？停下。那是自我合理化。

## The Iron Law（铁律）

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

在测试之前写了代码？删掉它。重来。

**没有例外：**
- 别把它留作 "reference"
- 别在写测试时 "改编" 它
- 别看它
- 删就是删

从测试全新实现。就这样。

## Red-Green-Refactor Cycle（红-绿-重构循环）

### RED —— 写失败测试

写一个最小的测试，展示应该发生什么。

**好测试：**
```python
def test_retries_failed_operations_3_times():
    attempts = 0
    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise Exception('fail')
        return 'success'

    result = retry_operation(operation)

    assert result == 'success'
    assert attempts == 3
```
名字清晰、测的是真实行为、只测一件事。

**坏测试：**
```python
def test_retry_works():
    mock = MagicMock()
    mock.side_effect = [Exception(), Exception(), 'success']
    result = retry_operation(mock)
    assert result == 'success'  # What about retry count? Timing?
```
名字含糊、测的是 mock 不是真实代码。

**要求：**
- 每个测试一个行为
- 名字清晰有描述性（名字里有 "and"？拆开它）
- 真实代码，不用 mock（除非真的躲不开）
- 名字描述行为，不描述实现

### Verify RED —— 看它失败

**强制。永不跳过。**

```bash
# Use terminal tool to run the specific test
pytest tests/test_feature.py::test_specific_behavior -v
```

确认：
- 测试失败（而不是拼写错误导致的报错）
- 失败信息符合预期
- 失败是因为功能缺失

**测试立刻通过？** 你在测已有行为。修测试。

**测试报错？** 修错误，重跑直到它以正确方式失败。

### GREEN —— 最小代码

写最简单、能让测试通过的代码。不多一点。

**好：**
```python
def add(a, b):
    return a + b  # Nothing extra
```

**坏：**
```python
def add(a, b):
    result = a + b
    logging.info(f"Adding {a} + {b} = {result}")  # Extra!
    return result
```

别加功能、别重构别的代码、别超出测试去 "改进"。

**GREEN 阶段作弊没关系：**
- 硬编码返回值
- 复制粘贴
- 重复代码
- 跳过边界情况

我们会在 REFACTOR 里修。

### Verify GREEN —— 看它通过

**强制。**

```bash
# Run the specific test
pytest tests/test_feature.py::test_specific_behavior -v

# Then run ALL tests to check for regressions
pytest tests/ -q
```

确认：
- 测试通过
- 其他测试仍通过
- 输出干净（无错误、无警告）

**测试失败？** 修代码，不是修测试。

**其他测试失败？** 现在就修回归。

### REFACTOR —— 清理

只在绿了之后：
- 去重复
- 改名字
- 抽 helper
- 简化表达式

全程保持测试绿。别加行为。

**重构中测试失败？** 立刻回退。步子迈小点。

### Repeat（重复）

为下一个行为写下一个失败测试。一次一个循环。

## Avoid Horizontal Slices（别横向切片）

**不要**先把所有测试写完、再写所有实现。那是横向切片：RED 变成 "写一堆靠想象编出来的测试"，GREEN 变成 "让这堆通过"。它产出脆弱的测试，因为测试是在实现还没教会你「到底哪些行为和接口才重要」之前就设计好的。

改用纵向曳光弹：

```text
WRONG:
  RED:   test1, test2, test3, test4
  GREEN: impl1, impl2, impl3, impl4

RIGHT:
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  RED→GREEN: test3→impl3
```

一条曳光弹就是一条端到端的行为切片。它证明路径走得通、让你了解接口，并让下一个测试扎根于你刚学到的东西。

## Why Order Matters（顺序为何重要）

**"我事后写测试来验证它能跑"**

事后写的测试立刻通过。立刻通过什么都证明不了：
- 可能测错了东西
- 可能测的是实现而非行为
- 可能漏掉你忘了的边界情况
- 你从没见它抓住过 bug

测试先行逼你看到测试失败，从而证明它确实在测某样东西。

**"我已经手动测过所有边界情况了"**

手动测试是临时的。你以为什么都测了，但其实：
- 没有测过什么的记录
- 代码变了没法重跑
- 压力下容易忘掉用例
- "我试的时候是好的" ≠ 全面

自动化测试是系统的。每次都以同样方式跑。

**"删掉 X 小时的活儿太浪费"**

沉没成本谬误。时间已经没了。你现在的选择：
- 删掉并用 TDD 重写（高置信度）
- 留着它、事后补测试（低置信度，大概率有 bug）

真正的「浪费」是留着你无法信任的代码。

**"TDD 教条，务实就该变通"**

TDD **就是**务实：
- 在提交前抓 bug（比事后调试快）
- 防回归（测试立刻抓住破坏）
- 记录行为（测试展示怎么用代码）
- 使重构可行（随便改，测试抓破坏）

"务实"的捷径 = 在生产里调试 = 更慢。

**"事后测能达到同样目的——重在精神不重形式"**

不。事后测回答 "这代码做了什么？" 测试先行回答 "它应该做什么？"

事后测被你自己的实现带偏。你测的是你建的东西，而非要求的东西。测试先行逼迫你在实现之前发现边界情况。

## Common Rationalizations（常见自我合理化）

| 借口 | 现实 |
|--------|---------|
| "太简单，不用测" | 简单代码也会坏。测试只要 30 秒。 |
| "我事后测" | 测试立刻通过证明不了任何事。 |
| "事后测能达到同样目的" | 事后测 = "这代码做了什么？" 测试先行 = "它应该做什么？" |
| "已经手动测过了" | 临时 ≠ 系统。没记录、不能重跑。 |
| "删掉 X 小时太浪费" | 沉没成本谬误。留着未验证代码就是技术债。 |
| "留作参考，先写测试" | 你会改编它。那就是事后测。删就是删。 |
| "得先探索一下" | 行。把探索扔掉，从 TDD 开始。 |
| "测试难 = 设计不清" | 听测试的。难测 = 难用。 |
| "TDD 会拖慢我" | TDD 比调试快。务实 = 测试先行。 |
| "手动测更快" | 手动证明不了边界情况。每次改动你都得重测。 |
| "已有代码没测试" | 你在改进它。给已有代码补测试。 |

## Red Flags — STOP and Start Over（红旗：停下，重来）

若你发现自己做了其中任何一件，就删掉代码、用 TDD 重来：

- 测试之前就有代码
- 实现后才写测试
- 测试首次运行就立刻通过
- 说不清测试为什么失败
- 测试是 "事后" 补的
- 为 "就这一次" 找理由
- "我已经手动测过它了"
- "事后测能达到同样的目的"
- "留作参考" 或 "改编已有代码"
- "已经花了 X 小时，删掉太浪费"
- "TDD 教条，我在务实"
- "这次情况不同，因为……"

**以上全部意味着：删代码。用 TDD 重来。**

## Verification Checklist（验证清单）

标记工作完成之前：

- [ ] 每个新函数/方法都有测试
- [ ] 实现之前亲眼看过每个测试失败
- [ ] 每个测试都以预期原因失败（功能缺失，而非拼写错误）
- [ ] 写了能让每个测试通过的最小代码
- [ ] 所有测试通过
- [ ] 输出干净（无错误、无警告）
- [ ] 测试用真实代码（mock 仅在不必要时才用）
- [ ] 边界情况与错误都已覆盖

勾不齐全部？你跳过了 TDD。重来。

## When Stuck（卡住时）

| 问题 | 解决 |
|---------|----------|
| 不知道怎么测 | 写你期望的 API。先写断言。问用户。 |
| 测试太复杂 | 设计太复杂。简化接口。 |
| 什么都得 mock | 代码太耦合。用依赖注入。 |
| 测试 setup 巨大 | 抽 helper。还复杂？简化设计。 |

## Hermes Agent Integration（与 Hermes Agent 的集成）

### Running Tests（跑测试）

每一步都用 `terminal` 工具跑测试：

```python
# RED — verify failure
terminal("pytest tests/test_feature.py::test_name -v")

# GREEN — verify pass
terminal("pytest tests/test_feature.py::test_name -v")

# Full suite — verify no regressions
terminal("pytest tests/ -q")
```

### With delegate_task

派子代理做实现时，在 goal 里强制 TDD：

```python
delegate_task(
    goal="Implement [feature] using strict TDD",
    context="""
    Follow test-driven-development skill:
    1. Write failing test FIRST
    2. Run test to verify it fails
    3. Write minimal code to pass
    4. Run test to verify it passes
    5. Refactor if needed
    6. Commit

    Project test command: pytest tests/ -q
    Project structure: [describe relevant files]
    """,
    toolsets=['terminal', 'file']
)
```

### With systematic-debugging

发现 bug？写一个能复现它的失败测试。走 TDD 循环。该测试证明修复、并防回归。

没有测试，永不修 bug。

## Testing Anti-Patterns（测试反模式）

- **测 mock 行为而非真实行为** — mock 应该验证交互，而不是替换被测系统
- **测实现细节** — 测行为/结果，不测内部方法调用
- **只测顺风路径** — 永远要测边界情况、错误与边界
- **脆弱测试** — 测试应验证行为而非结构；重构不该弄断它们

## Final Rule（最终裁决）

```
Production code → test exists and failed first
Otherwise → not TDD
```

没有用户明确许可，就没有例外。
