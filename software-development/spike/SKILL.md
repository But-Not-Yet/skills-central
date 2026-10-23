---
name: spike
description: "开工前的抛弃式验证实验（spike）时使用。只要要先验证想法可行性、比较方案再动手真建，就主动加载，即使用户没明说 spike / 原型。用完即弃。"
version: 1.0.0
author: Hermes Agent (adapted from gsd-build/get-shit-done)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spike, prototype, experiment, feasibility, throwaway, exploration, research, planning, mvp, proof-of-concept]
    related_skills: [sketch, subagent-driven-development]
---

# Spike（抛弃式验证实验）

用户想在真正开工前**把一个想法摸清楚**时用本技能——验证可行性、比较方案，或暴露那些再多调研也回答不了的未知。Spike 生来就是一次性的。一旦把它的债还清，就把它扔掉。

用户说这类话时加载它："let me try this"、"I want to see if X works"、"spike this out"、"before I commit to Y"、"quick prototype of Z"、"is this even possible?" 或 "compare A vs B"。

## When NOT to use this（何时别用）

- 答案能从文档或读代码得知 —— 只做调研，别建
- 工作是生产路径 —— 改用 `plan` 技能
- 想法已经验证过 —— 直接进实现

## If the user has the full GSD system installed（用户装了完整 GSD 系统时）

若 `gsd-spike` 作为兄弟技能出现（经 `npx get-shit-done-cc --hermes` 安装），当用户想要完整 GSD 工作流时，优先用 **`gsd-spike`**：持久的 `.planning/spikes/` 状态、跨会话的 MANIFEST 追踪、Given/When/Then 裁决格式，以及与 GSD 其余部分集成的提交模式。本技能是给没有（或不想用）完整系统的用户的轻量独立版。

## Core method（核心方法）

不论规模，每个 spike 都走这个循环：

```
decompose  →  research  →  build  →  verdict
   ↑__________________________________________↓
                  iterate on findings
```

### 1. Decompose（拆解）

把用户的想法拆成 **2-5 个相互独立的可行性问题**。每个问题就是一个 spike。用 Given/When/Then 框架把它们列成一张表：

| # | Spike | 验证（Given/When/Then） | 风险 |
|---|-------|----------------------------|------|
| 001 | websocket-streaming | Given 一条 WS 连接，when LLM 流式吐 token，then 客户端收到 chunk < 100ms | High |
| 002a | pdf-parse-pdfjs | Given 一份多页 PDF，when 用 pdfjs 解析，then 结构化文本可提取 | Medium |
| 002b | pdf-parse-camelot | Given 一份多页 PDF，when 用 camelot 解析，then 结构化文本可提取 | Medium |

**Spike 类型：**
- **standard** —— 一个方法回答一个问题
- **comparison** —— 同一问题、不同方法（共用编号，加字母后缀 `a`/`b`/`c`）

**好的 spike 问题：** 具体、可行、有可观测输出。
**坏的 spike 问题：** 太宽泛、无可观测输出，或只是 "read the docs about X"。

**按风险排序。** 最可能「杀死」这个想法的 spike 先跑。如果难的部分根本走不通，把容易的部分原型化也没意义。

**跳过拆解** 只在用户已确切知道自己要 spike 什么并说了出来时。那就把他的想法当成单个 spike。

### 2. Align (for multi-spike ideas)（对齐）

呈现 spike 表。问："全按这个顺序建，还是调整？" 在写任何代码前，让用户删、重排或重新表述。

### 3. Research (per spike, before building)（调研）

Spike 不是无调研的——你先调研到足以选对方法，然后再建。每个 spike：

1. **简述它。** 2-3 句：这个 spike 是什么、为什么重要、关键风险。
2. **摆出竞争方法**（若真有得选）：

   | 方法 | 工具/库 | 优点 | 缺点 | 状态 |
   |----------|-------------|------|------|--------|
   | ... | ... | ... | ... | maintained / abandoned / beta |

3. **挑一个。** 说明为什么。若有 2+ 个都可信，就在该 spike 里快速做几个变体。
4. **跳过调研**（对无外部依赖的纯逻辑）。

调研步骤用 Hermes 工具：

- `web_search("python websocket streaming libraries 2025")` —— 找候选项
- `web_extract(urls=["https://websockets.readthedocs.io/..."])` —— 读真实文档（返回 markdown）
- `terminal("pip show websockets | grep Version")` —— 查项目 venv 里装了什么

对没有文档页的库，克隆并经由 `read_file` 读它们的 `README.md` / `examples/`。Context7 MCP（若用户配置了）也是好来源——先 `mcp_*_resolve-library-id` 再 `mcp_*_query-docs`。

### 4. Build（动手建）

每个 spike 一个目录。保持独立。

```
spikes/
├── 001-websocket-streaming/
│   ├── README.md
│   └── main.py
├── 002a-pdf-parse-pdfjs/
│   ├── README.md
│   └── parse.js
└── 002b-pdf-parse-camelot/
    ├── README.md
    └── parse.py
```

**偏向用户能上手交互的东西。** 当唯一输出只是一句 "it works" 的日志行时，spike 就失败了。用户想**摸到** spike 在跑。默认选择，按偏好排序：

1. 一个可运行的 CLI，接收输入并打印可观测输出
2. 一个演示该行为的最小 HTML 页
3. 一个只有一个端点的小 web server
4. 一个用可辨认断言检验该问题的单元测试

**深度胜过速度。** 别在跑通一次顺风路径后就宣称 "it works"。测边界情况。追着意外发现走。只有当调查是诚实的，裁决才可信。

**避免**这些，除非该 spike 特别需要：复杂的包管理、构建工具/打包器、Docker、env 文件、配置系统。一切硬编码——它是 spike。

**构建一个 spike** —— 一个典型的工具序列：

```
terminal("mkdir -p spikes/001-websocket-streaming")
write_file("spikes/001-websocket-streaming/README.md", "# 001: websocket-streaming\n\n...")
write_file("spikes/001-websocket-streaming/main.py", "...")
terminal("cd spikes/001-websocket-streaming && python main.py")
# Observe output, iterate.
```

**并行对比 spike（002a / 002b）—— 委派。** 当两个方法可并行、且都需要真工程（不是 10 行原型）时，用 `delegate_task` 扇出：

```
delegate_task(tasks=[
    {"goal": "Build 002a-pdf-parse-pdfjs: ...", "toolsets": ["terminal", "file", "web"]},
    {"goal": "Build 002b-pdf-parse-camelot: ...", "toolsets": ["terminal", "file", "web"]},
])
```

每个子代理返回自己的裁决；你来写正面对比。

### 5. Verdict（裁决）

每个 spike 的 `README.md` 以这样的结尾收束：

```markdown
## Verdict: VALIDATED | PARTIAL | INVALIDATED

### What worked
- ...

### What didn't
- ...

### Surprises
- ...

### Recommendation for the real build
- ...
```

**VALIDATED** = 核心问题带证据地回答了「是」。
**PARTIAL** = 在约束 X、Y、Z 下能用——把它们记下来。
**INVALIDATED** = 不work，因为某个原因。这也是一次成功的 spike。

## Comparison spikes（对比型 spike）

当两个方法回答同一问题（002a / 002b）时，**背靠背**把它们建出来，最后做一次正面对比：

```markdown
## Head-to-head: pdfjs vs camelot

| Dimension | pdfjs (002a) | camelot (002b) |
|-----------|--------------|----------------|
| Extraction quality | 9/10 structured | 7/10 table-only |
| Setup complexity | npm install, 1 line | pip + ghostscript |
| Perf on 100-page PDF | 3s | 18s |
| Handles rotated text | no | yes |

**Winner:** pdfjs for our use case. Camelot if we need table-first extraction later.
```

## Frontier mode (picking what to spike next)（前沿模式：下一步该 spike 什么）

若已有若干 spike，用户问 "what should I spike next?"，就遍历已有目录找：

- **集成风险** —— 两个已验证的 spike 触及同一资源，却是各自独立测的
- **数据交接** —— spike A 的输出曾被认为与 spike B 的输入兼容；从未被证明
- **愿景缺口** —— 被假定但未验证的能力
- **替代方法** —— 对 PARTIAL 或 INVALIDATED 的 spike 换角度

以 Given/When/Then 提 2-4 个候选。让用户挑。

## Output（产出）

- 在仓库根建 `spikes/`（或用户沿用 GSD 约定时用 `.planning/spikes/`）
- 每个 spike 一个目录：`NNN-descriptive-name/`
- 每个 spike 的 `README.md` 记录问题、方法、结果、裁决
- 代码保持一次性——一个要花 2 天去「清理成生产可用」的 spike，就是个坏 spike

## Attribution（出处）

改编自 GSD（Get Shit Done）项目的 `/gsd-spike` 工作流 —— MIT © 2025 Lex Christopherson（[gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)）。完整的 GSD 系统提供持久化的 spike 状态、MANIFEST 追踪，以及与更广大的规格驱动开发流水线的集成；用 `npx get-shit-done-cc --hermes --global` 安装。
