---
name: simplify-code
description: "对近期代码改动做四代理并行清理时使用：复用、质量、效率、层次（altitude）。只要用户说 simplify / 清理我的改动 / dry run，就主动加载，即使用户没明说并行审查。这是清理不是找 bug。"
version: 1.1.0
author: Hermes Agent (inspired by Claude Code /simplify)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-review, cleanup, refactor, delegation, subagent, parallel, simplify]
    related_skills: [requesting-code-review, test-driven-development]
---

# Simplify Code —— 并行审查与清理

用四个各自聚焦的审查者**并行**审查你近期的代码改动，汇总他们的发现，应用值得应用的修复。

**这是一遍清理，不是猎 bug。** 你在提升**已经能用**的代码质量——去重复、压平不必要的复杂度、砍浪费、把创可贴式修复做得更深。别在这儿找正确性 bug。那是 `requesting-code-review` 的活。

**核心原则：** 四个窄审查者胜过一个大审查者。每个只针对一类问题在代码库里深挖——复用、质量、效率、层次（altitude）——注意力不被四件事稀释。它们并发跑，所以你只付一次审查的延迟，而不是四次。

## When to Use（何时用）

用户说以下任何一句时触发本技能：

- "simplify" / "simplify my changes" / "simplify these changes"
- "review my code" / "review my recent changes" / "clean up my changes"
- "/simplify"（如果他们带着 Claude Code 的习惯过来）

用户可能加的可选修饰语——照办：

- **Focus（聚焦）：** "simplify focus on efficiency" → 只跑效率审查者（或把汇总向它加权）。可识别的焦点：`reuse`、`quality`（也接受 `simplification`）、`efficiency`、`altitude`。
- **Dry run（空跑）：** "simplify but don't change anything" / "just report" → 跑四个审查者，呈现发现，**什么都不**应用。应用前先问。
- **Scope（范围）：** "simplify the last commit" / "simplify staged" / "simplify src/foo.py" → 相应地收窄 diff 来源（见 Phase 1）。

**不要**每次编辑后自动跑它，也别把它挂到无关任务的末尾。它花掉四个子代理的 token——只在用户明确要求时调用。

## The Process（流程）

### Phase 1 — Identify the changes（确定改动）

抓取要审查的 diff。按用户所求来选来源，默认顺序如下：

```bash
# 1. Default: uncommitted working-tree changes (tracked files)
git diff

# 2. If that's empty, include staged changes
git diff HEAD

# 3. Scoped variants the user may request:
git diff --staged                 # "staged changes"
git diff HEAD~1                    # "the last commit"
git diff main...HEAD              # "this branch" / "my PR"
git diff -- src/foo.py            # specific file(s)
```

若 `git diff` 与 `git diff HEAD` 都为空，且没有 git 仓库或没有改动，就退回用户明确点名的文件。或本会话里刚创建/编辑过的文件。若你确实找不到任何改动的代码，就直说并停下——没东西可简化。

抓取完整 diff 文本。留意大小：若非常大（比如 >2000 改动行），提醒用户四个子代理各背一份完整 diff 会很费 token。并在继续前提议收窄（按目录、按提交）。

### Phase 2 — Launch four reviewers in parallel（并行派出四个审查者）

用 `delegate_task` 的**批处理模式**——把四个任务放进一个 `tasks` 数组，让它们并发跑。四路正是这个模式的正确扇出。在任何默认安装里都在 `delegation.max_concurrent_children` 预算内。

**没有 delegation 可用？** 若你在此上下文里调不了 `delegate_task`（你是叶子子代理、委派被禁用、或预算耗尽），**不要**跳过审查。也不要去掉角度。亲自在此上下文里依次走完四个审查者角度——同样的检索标准、同样的发现格式。然后在最终总结里明确说这是一遍单次内联审查、而非并行扇出，让用户知道实际跑的是什么。

给**每个**审查者**完整 diff**（不是碎片——跨文件问题藏在缝隙里）加上仓库绝对路径。好让他们检索更大的代码库。每个审查者拿 `terminal`、`file`、`search` 工具集（以便 `git`、`read_file`、`search_files`/grep）。

告诉每个审查者：
- 去现有代码库里找证据（别只凭 diff 推理）。
- **应用切斯特顿之栏（Chesterton's Fence）：** 在标记任何东西该删之前，先对那一行跑 `git blame` 搞懂它为何存在。若无法判定其原始用途，标 `confidence: low`——别猜。
- 以结构化输出报告发现，带具体的代价、置信度与风险：
  ```
  file:line → problem → cost (what's duplicated/wasted/harder to maintain) → suggested fix | confidence: high/medium/low | risk: SAFE/CAREFUL/RISKY
  ```
  **cost** 字段逼每条发现自证——说不清问题实际代价的发现多半是吹毛求疵。
  - **SAFE** = 已证明不影响行为（未用的 import、注释掉的代码、直通包装器）。直接自动应用这些。
  - **CAREFUL** = 有改进但不变语义（重命名局部变量、压平嵌套三元、抽 helper）。带测试验证后应用。
  - **RISKY** = 可能改变行为或破坏公开契约（N+1 重构、公开 API 改名、内存生命周期改动）。标给人工审查——**不要**自动应用。
- 跳过吹毛求疵与纯风格折腾。只标出实质性改善代码的东西。

传这四个目标（用户焦点排除掉的就不传）：

**Reviewer 1 —— Code Reuse（代码复用）**
> 审查这份 diff，找那些重复了代码库里已有功能的代码。检索工具模块、共享 helper 与邻近文件（用 search_files / grep），看有没有现成的函数、常量或模式可供新代码调用。而非重复造。要标：重复已有函数的新函数。现有工具本就能做的手写逻辑（手写字符串/路径处理、自定义环境检查、临时类型守卫、重复实现的解析）。每条都点出现有该用的东西以及它在哪。

**Reviewer 2 —— Code Quality（代码质量）**
> 审查这份 diff 的质量问题。找：冗余状态（与现有状态重复、或可由其推导的值。本不必存在的缓存）。参数蔓延（该重构函数时却硬塞新参数）。带变化的复制粘贴（本该共享抽象、却近乎重复的代码块）。漏抽象（暴露内部、打破既有封装边界）。字符串当类型用（已有常量/enum/registry 却用裸字符串——标之前先查权威 registry）。深层嵌套条件（三元链、3+ 层的 if/else 金字塔——用守卫子句、提前返回或查找表压平）。AI 生成的糊状模式（上面 `count++` 却配 `// increment counter` 这类复述显然代码的多余注释。对已校验输入做多余的防御式 null 检查。绕过类型系统的 `as any` 强转。与文件其余部分不一致的模式）。每条都给出具体的重构。

**Reviewer 3 —— Efficiency（效率）**
> 审查这份 diff 的效率问题。找：无用功（重复计算、重复读文件、重复 API 调用、N+1 访问模式）。错失的并发（本可并行的独立操作却串行）。热路径臃肿（启动时或每次请求路径上的重/阻塞工作）。TOCTOU 反模式（操作前先检查存在性，而不是直接做操作并处理错误）。内存问题（无界增长、缺清理、监听器/句柄泄漏。长期存活的回调、或以闭包形式构建并捕获整个外围作用域的对象——被捕获的一切只要对象活着就都活着，所以宁可要一个小类或只复制所需字段的显式结构体）。过宽的读（能读一片却加载整文件）。静默失败（空 catch 块、被忽略的错误返回、`except: pass`、不做处理的 `.catch(() => {})`、错误传播的缺口——这些掩盖 bug，至少该在吞掉前记条日志）。每条给出具体修法以及它为什么更快或更安全。

**Reviewer 4 —— Altitude（层次）**
> 审查这份 diff 里实现深度不对的改动——在共享基础设施上层层叠加创可贴。而不是去修基础设施本身。修得太浅的迹象。在通用代码路径上加特例来处理某一个调用方（`if (caller == X)` 分支、类型检查、魔数逃生口）。在调用点补了症状，而兄弟调用点仍留着同样的缺陷。在早先的 workaround 上再叠一层 workaround。为避免碰真正该改的东西而加包装器。为了绕开一个坏默认值而引入配置或开关，而不是去修那个默认值。每条都指出改动在躲的底层机制，并描述更深的修法——泛化共享路径、修根默认值、或修整类 bug。并诚实地注记：当更深的修法大到该自成一个任务、而非本次清理的一部分时。先读周边代码与 `git blame`：看着像创可贴的东西，有时是有意的边界（兼容垫片、分阶段迁移、vendored 代码隔离）。那些别标。

### Phase 3 — Aggregate and apply（汇总并应用）

等四个都返回（批处理模式会一起返回）。

1. **合并**发现成一张清单，审查者重叠处去重——当两条发现指向同一行或同一底层机制，收敛成一条。
2. **丢弃误报**——你上下文最多。不必跟审查者争，直接把弱或错的建议静默丢掉。
3. **化解冲突。** 审查者可能互相打架（Reviewer 1："用现成的 util X"。Reviewer 3："X 慢，内联它"）。默认化解次序：**正确性 > 用户声明的焦点 > 可读性/复用 > 微性能。** 除非该路径确属热点，否则别应用会伤害清晰度的性能「修复」。当两条建议互斥且都站得住，选改动代码更少的，并注记另一条。
4. **按风险层级顺序应用：**
   - **先 SAFE**（自动应用）：未用的 import、注释掉的代码、直通包装器、多余的断言。之后跑测试。
   - **再 CAREFUL**（带验证应用，一次一个文件）：重命名局部变量、压平三元、抽 helper、合并重复。每个文件后跑测试。破坏的就回退。
   - **最后 RISKY**（标出待审——**不要**自动应用）：N+1 重构、公开 API 改动、并发修复、错误处理改动。逐条给出风险描述与测试覆盖状态。Altitude 发现通常落在这——加深修复意味着碰共享基础设施，所以把更深的修法呈现出来。让用户决定现在就做还是作为后续。
   若用户选了空跑，呈现全部三层、什么都不应用。
5. **验证**你没弄坏东西：对触及的文件跑项目里的针对性测试（不是全套）。并重跑仓库用的任何 linter/类型检查。若某个修复弄坏了测试，回退那一条并报告。
6. **总结**你改了什么：按审查者类别与风险层级分组的已应用修复短清单。外加你刻意跳过的发现及原因。若你是内联跑的（没有委派），在这里说明。

## Pitfalls（坑）

- **扇出别超过 4。** 更多审查者意味着更高成本、更多要调和的冲突建议，而不是更好覆盖。四个类别已覆盖这个空间。
- **给每个审查者整份 diff。** 把 diff 拆给不同审查者就违背了设计——跨文件重复和 N+1 只有看全貌才会显形。
- **审查者是检索，不是猜。** 一条没指向现有工具的复用发现（"大概有个 helper 吧"）就是噪音。要求 `file:line` 证据。缺证据的丢掉。
- **应用 ≠ 重写。** 这是清理用户近期改动，不是把整个模块重构一遍的许可证。把编辑限制在 diff 触及范围加一个修复所需的最小周边改动。Altitude 发现是印证这条规则的例外：当正确修法比 diff 更深时，**标出来**。别在一次清理里擅自重建共享机制。
- **别漂进猎 bug。** 若审查者抖出一个真的正确性 bug，醒目地报告它——但作为单独的"发现一个 bug"注记。别揉进清理修复里。正确性审查是另一遍、另一套验证标准。
- **尊重项目约定。** 若仓库有 AGENTS.md / CLAUDE.md / HERMES.md 或 linter 配置，把这些规则折进审查者 prompt，让建议贴合本色风格。而不是跟它对着干。
- **大 diff 会炸上下文。** diff 很大就先收窄再委派——四个子代理各背 5000 行 diff 很贵，还可能被截断。
- **别过度信任死代码工具。** `knip`、`ts-prune`、`depcheck` 会把**动态**使用的导出也标红（基于字符串的 import、反射）。删之前一律 grep 符号名——工具报告干净不算证据。
- **没查公开契约就重命名。** 导出名、API 路由路径、DB 列名、配置键都是契约——哪怕名字很烂，重命名也会弄坏消费者。公开契约改动一律标 RISKY。永不自动重命名它们。
- **删「多余」的错误处理。** 空 catch 块或被忽略的错误可能是有意的——在那个上下文里，错误是可预期且良性的。标出来，别删。让人来决定。
- **不是每个特例都是创可贴。** 兼容垫片、分阶段迁移、围绕 vendored 代码的隔离层看着像 altitude 违规，却是有意的设计。标之前查 `git blame` 与周边注释。意图不明就标 `confidence: low`。

## Related（相关）

若你的安装里有 `subagent-driven-development` 技能（可选），它覆盖互补的场合：实现**期间**的并行审查，逐任务。本技能是独立的**事后**清理遍。提交前的安全/质量闸用 `requesting-code-review`——那是猎 bug。这是清理。
