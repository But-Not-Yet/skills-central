---
name: hermes-agent-skill-authoring
description: "写仓库内（in-repo）SKILL.md 时使用：frontmatter 与结构规范。只要要把技能提交进 hermes-agent 仓库、或改 skills/、optional-skills/ 下的技能，就主动加载，即使用户没明说 HARDLINE 标准。照 AGENTS.md 的硬线规范走。"
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, authoring, hermes-agent, conventions, skill-md]
    related_skills: [requesting-code-review]
---

# 编写 Hermes-Agent 技能（仓库内）

## Overview（概览）

SKILL.md 可以住在两个地方：

1. **用户本地：** `~/.hermes/skills/<maybe-category>/<name>/SKILL.md` — 个人的，不共享。用 `skill_manage(action='create')` 创建。
2. **仓库内（本技能讲的就是这种）：** hermes-agent 仓库里的 `skills/<category>/<name>/SKILL.md` 或 `optional-skills/<category>/<name>/SKILL.md` — 提交进仓库、随包发布。用 `write_file` + `git add`。`skill_manage(action='create')` 不针对这棵树。

仓库内的技能必须满足仓库的**硬线编写标准**（见 AGENTS.md 的 "Skill authoring standards (HARDLINE)"——那一节是真理来源。本技能是可操作的走查）。审查者会拒掉违反它们的 PR，所以一开始就达标比事后返工便宜。

## When to Use（何时用）

- 用户要你「在这个分支 / 仓库 / 提交里」加一个技能
- 你要提交一个应当随 hermes-agent 发布的可复用工作流
- 你在改 `skills/` 或 `optional-skills/` 下已有的技能（小改用 `patch`，重写用 `write_file`。仓库内技能 `skill_manage` 仍能做 patch，但不能做 `create`）
- 不用于：`~/.hermes/skills/` 下的个人技能（直接用 `skill_manage` 就行）

## Decide the Tier First: Bundled vs Optional（先定层级）

- **Bundled（`skills/<category>/`）** — 日常主力行为、对各类用户都广泛有用、占用小。硬门槛：你要能面不改色地说「一个用户每月会加载它 5 次以上」。
- **Optional（`optional-skills/<category>/`）** — 小众、垂直行业专用（区块链、游戏、金融、某个 app）、周期任务/一次性任务类技能。或任何重量级的东西。用 `hermes skills install official/<category>/<skill>` 安装。

**拿不准就选 optional。** 以后升级容易。降级是折腾。「凡是用得上的人都觉得有用」是 optional 层的理由，不是 bundled 的。

按工具**本质上是什么**来选类别。而不是它「感觉像什么」（一个 AI-agent CLI 归 `autonomous-ai-agents/`，哪怕它「感觉像生产力工具」）。用 `search_files(pattern='*', target='files', path='skills')` 确认已有类别，别随手发明新的一级类别。

**不要 router / index / hub 技能。** 核心内容是一张指向兄弟技能的路由表的技能，只增加一跳间接层。还重复了兄弟技能自己的 `When to Use` 触发词。如果抽掉「改去加载技能 X」这类指针后技能就空了，那就别写。目录和每个兄弟技能的触发词已经把这件事做了。

## Required Frontmatter（必需的 frontmatter）

Validator 的真理来源：`tools/skill_manager_tool.py::_validate_frontmatter`。Validator 的硬性要求：

- 第一个字节就是 `---`（前面不能有空行）。
- 正文之前以 `\n---\n` 收尾。
- 能按 YAML mapping 解析。
- 有 `name` 字段。
- 有 `description` 字段（validator 上限 1024 字符——但请看下方的仓库硬线，严得多）。
- 收尾 `---` 之后正文非空。

仓库标准形状（所有字段都应齐全，即使 validator 不强制它们）：

```yaml
---
name: my-skill-name               # lowercase, hyphens, ≤64 chars (MAX_NAME_LENGTH)
description: Concise capability statement, under sixty chars.
version: 0.1.0                    # semver; new skills start at 0.1.0
author: Real Name (github-handle), Hermes Agent
license: MIT
platforms: [linux, macos, windows]   # audit, don't guess — see Platform Gating
metadata:
  hermes:
    tags: [Short, Descriptive, Tags]
    related_skills: [other-in-repo-skill]
---
```

### `description` 规则（HARDLINE——validator 的 1024 不是标准）

- **≤ 60 字符。** 一句话。以句号结尾。
- 说清能力，而不是实现，且不要重复技能名。
- 不要营销词（"powerful"、"comprehensive"、"seamless"、"advanced"）。
- 系统提示的 skill 索引在 57 字符 + "..." 处截断——触发词/能力必须在这个窗口里自洽。
- 若 description 含 `:`，用双引号包住，否则 YAML 会把它解析成 mapping，文档生成器就崩。引号不计入 60。

好：`Track named companies for material news with cited digests.`
坏：`Use when a user asks to monitor named competitors or companies for product launches, pricing changes, funding, ...`（240 字符——审查被拒）

### `author` 规则

- **先署人**，再把 "Hermes Agent" 作为次要协作者：`Ben Barclay (benbarclay), Hermes Agent`。
- 投稿技能绝不能只写 `author: Hermes Agent`——署人，不署工具，即便（尤其）文本是 agent 起草的。
- 维护者自编技能：`Teknium (teknium1), Hermes Agent`。

### `related_skills` 规则

- 每个条目都必须解析到与你的 PR 处于同一树状态的、仓库内**已存在**的技能。不要引用只规划过、在别的 PR 里、或只存在于 `~/.hermes/skills/` 的技能。
- 逐个核验：`search_files(pattern='<name>', target='files', path='skills')`（以及 `optional-skills/`）。

## Platform Gating: audit, don't trust（平台门控：审计，别信）

`platforms:` 按宿主 OS 门控加载。依据技能的正文与脚本实际调用什么来设定：

| 技能只用到…… | `platforms:` |
|---|---|
| Hermes 工具 + 标准库 Python + 跨平台 CLI | `[linux, macos, windows]` |
| bash 管道、`grep`/`awk`/`sed` 链、heredoc | `[linux, macos]` |
| `osascript`、`defaults`、`pmset` | `[macos]` |
| `apt`/`systemctl`/`/proc` | `[linux]` |

<!-- no-tmp: ok — names the anti-pattern skill authors must avoid -->
在 `scripts/` 里该搜的 POSIX 专属信号：`fcntl`、`termios`、`pty`、`os.fork`、`os.killpg`、`signal.SIGKILL`、`os.kill(pid, 0)` 存活检查、硬编码的 `/tmp` `/proc` `/etc`。默认姿势：先修成跨平台（`tempfile.gettempdir()`、`pathlib.Path`、`psutil.pid_exists`）。只有当依赖真的绑死某平台时才收窄，并在 `## Pitfalls` 里说明理由。

## Size Limits（体量上限）

- 整个 SKILL.md：强制 ≤ 100,000 字符（`MAX_SKILL_CONTENT_CHARS`），但目标是**简单技能 ~100 行、复杂技能 ~200 行**。同级技能多在 8-14k 字符。
- 臃肿或分支专属的材料放进 `references/*.md`、`templates/` 或 `scripts/`——从 SKILL.md 指过去，不要内联。
- 别指望模型每次调用都内联写解析器或非平凡逻辑——在 `scripts/` 里放个辅助脚本，按路径引用它。

## Body Structure（正文结构，现代章节顺序）

```
# <Skill> Skill
2-3 sentence intro: what it does, what it doesn't do, dependency stance.

## When to Use          — bulleted triggers (+ "Don't use for:" counter-triggers)
## Prerequisites        — exact env vars, installs, API key sourcing
## How to Run           — canonical invocation through the `terminal` tool
## Quick Reference      — flat command list, no narration
## Procedure            — numbered steps, each with a checkable completion criterion
## Pitfalls             — known limits, things that look broken but aren't
## Verification         — how to prove the skill worked
```

并非每个章节都适用于每个技能（纯流程的任务型技能可能没有 Quick Reference）。但 When to Use + 可操作的正文 + Pitfalls + Verification 是最低要求。砍掉营销式引言、"Setup Check" 空操作，以及重复讲解 Prerequisites 里已有的环境变量。

### Reference Hermes tools, not raw shell（引用 Hermes 工具，而非裸 shell）

技能需要某种能力时，用反引号点名正确的 Hermes 工具：`terminal`、`read_file`、`write_file`、`patch`、`search_files`、`web_search`、`web_extract`、`browser_navigate`、`vision_analyze`、`delegate_task`、`cronjob`。不要点名 agent 已包装过的 shell 工具（`grep` → `search_files`，`cat` → `read_file`，`sed`/`awk` → `patch`，`find`/`ls` → `search_files target='files'`）。CLI 包装型技能应把调用写成 `terminal(command="{tool} ...", timeout=...)`——裸 shell 叙述（"run `foo --version`"）是会被审查驳回的不合规。若技能依赖某个 MCP server，点名它并在 Prerequisites 里记下配置。

### Never use machine-local paths（绝不用机器本地路径）

写仓库相对路径（`skills/...`、`tools/skill_manager_tool.py`）。把 `/home/<you>/...` 路径烤进一个已提交的技能，会坑到其他所有用户，是即刻的审查红旗。

## Writing Quality Principles（写作质量原则）

技能存在的意义，是让 agent 的流程更可预测——agent 稳定地遵循同一套有用的纪律。

1. **为流程可预测性优化。** 一行若不能改变行为，就删掉。
2. **选对上下文负载。** description 每轮都要付费。细节放正文或链接的 reference。
3. **每步以完成判据收尾。** 可勾选，必要时穷尽："每个改动过的文件都交代到位" 胜过 "总结改动"。
4. **把规则和它管的概念放在一起。**
5. **用强力的引导词**（"tight loop"、"root cause"、"regression test"）胜过冗长重复的解释。
6. **删掉重复和空操作。** "Be careful" 和 "use best practices" 不会改变模型行为——换成可勾选的判据，或删掉。

## Tests and Docs（测试与文档，仓库技能必需）

1. **测试**放在 `tests/skills/test_<skill>_skill.py`——只用标准库 + pytest + `unittest.mock`，不连真实网络。用 `scripts/run_tests.sh tests/skills/test_<skill>_skill.py -q` 跑。（通用的 `tests/tools/test_skill_manager_tool.py` 通过，证明不了**你的**技能如何。）
2. **文档重生成：** 跑 `python website/scripts/generate-skill-docs.py`，然后守住范围纪律——生成器会重写**每一个**自动生成的页面。把不属于你的改动全部 `git checkout --` 掉。最终 diff 只能出现你的 SKILL.md、你那一页 per-skill 文档、一行目录行。以及 `website/sidebars.ts` 里的一行插入（用 `search_files(pattern='<your-slug>', path='website/sidebars.ts')` 核验——恰好一处命中，否则该页就是孤儿）。
3. **`.env.example`**（仅当技能需要新环境变量时）：一个清晰分隔的注释块。文件里别的地方一概不碰。

## Workflow（工作流）

1. 用 `search_files(target='files')` **勘察**目标类别里的同级技能，读 2-3 个同级 SKILL.md，对齐语气与结构。宁可扩展已有技能，也别新造一个狭窄的兄弟技能。
2. **定层级和类别**（见上）。拿不准就 optional——且推送前先问，别默认。
3. 用 `write_file` **起草**到 `skills/<category>/<name>/SKILL.md`（或 `optional-skills/...`）。
4. **本地校验**：
   ```python
   import re, pathlib
   from ruamel.yaml import YAML
   content = pathlib.Path("skills/<category>/<name>/SKILL.md").read_text()
   assert content.startswith("---")
   m = re.search(r'\n---\s*\n', content[3:])
   fm = YAML(typ="safe").load(content[3:m.start()+3])
   assert "name" in fm and "description" in fm
   assert len(fm["description"]) <= 60, f"description {len(fm['description'])} chars — hardline is 60"
   assert fm["description"].endswith(".")
   assert "platforms" in fm
   assert len(content) <= 100_000
   ```
   还要核验每个 `related_skills` 条目在仓库内存在。
5. **加测试 + 重生成文档**（见上一节）。
6. 在当前分支上 **git add + commit**。开 PR。
7. **注意：** 当前会话的 skill loader 有缓存——`skill_view` / `skills_list` 要等到新会话才看得见新技能。这是预期行为，不是 bug。

## Editing Existing In-Repo Skills（改已有的仓库内技能）

- **小修：** `skill_manage(action='patch', ...)` 对仓库内技能有效，`patch` 也一样。
- **大改：** 用 `write_file` 重写整个 SKILL.md。
- **配套文件：** 用 `write_file` 写到技能目录下的 `references/`、`templates/` 或 `scripts/`。
- **一律提交**——仓库内技能是源码，不是运行时状态。frontmatter 变了就重跑文档生成器。

## Common Pitfalls（常见坑）

1. **对仓库内技能用 `skill_manage(action='create')`。** 它写到 `~/.hermes/skills/`，不是仓库树。用 `write_file`。
2. **把 validator 的上限当成标准。** validator 容许 1024 字符的 description。审查拒掉超过 60 的。validator 不检查 `platforms:`、author 格式、测试或文档——审查会查。
3. **投稿技能写 `author: Hermes Agent`。** 先署人。
4. **`---` 前有前导空白。** 任何前导空行或 BOM 都会让校验失败。
5. **description 太泛、或触发词埋在第 57 字符之后。**
6. **`related_skills` 指向仓库内不存在的技能**（用户本地的、规划中的、或在兄弟 PR 里的）。
7. **重复造同级技能。** 先勘察类别。扩展而非另开兄弟。
8. **跳过文档生成器、或把它的无关漂移推上去。** 两个方向都错：不重生成 = 技能成孤儿、没有文档页。盲目重生成 = diff 膨胀、塞满别的技能的漂移。
9. **指望当前会话看得见新技能。** loader 在会话开始时初始化。
10. **任技能堆积沉淀物。** 加一条规则时，删掉它所取代的旧措辞。

## Verification Checklist（验证清单）

- [ ] 层级是有意定的（bundled 门槛：每月 5+ 会话。否则用 `optional-skills/`）
- [ ] 文件在 `skills/<category>/<name>/SKILL.md` 或 `optional-skills/<category>/<name>/SKILL.md`
- [ ] Frontmatter 从第 0 字节起是 `---`，以 `\n---\n` 收尾
- [ ] `name`、`description`、`version`、`author`、`license`、`platforms`、`metadata.hermes.{tags, related_skills}` 全部齐全
- [ ] Description ≤ 60 字符、一句话、以句号结尾、无营销词
- [ ] `author` 先署人类贡献者
- [ ] `platforms:` 是照实际正文/脚本审计出来的，不是从同级技能抄的
- [ ] 每个 `related_skills` 条目都在仓库内可解析
- [ ] 正文遵循现代章节顺序。命令通过 Hermes 工具表述
- [ ] 文件里任何地方都没有机器本地路径
- [ ] 每个有序步骤都有可勾选的完成判据
- [ ] `tests/skills/test_<skill>_skill.py` 在 `scripts/run_tests.sh` 下通过
- [ ] 文档在范围纪律下重生成。侧栏对该 slug 恰好一条记录
- [ ] 在目标分支上 `git add` + commit。PR 已开
