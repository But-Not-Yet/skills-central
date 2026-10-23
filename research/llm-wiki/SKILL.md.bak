---
name: llm-wiki
description: "建、查 Karpathy 式 LLM Wiki 互联 markdown 知识库时使用。只要要摄入来源、查询或体检这类 wiki，就主动加载，即使用户只说「把这些资料整理进知识库」。"
version: 2.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wiki, knowledge-base, research, notes, markdown, rag-alternative]
    category: research
    related_skills: [obsidian, arxiv]
---

# Karpathy 的 LLM Wiki

把一套持久、会复利增长的知识库构建与维护为互链的 markdown 文件。
基于 [Andrej Karpathy 的 LLM Wiki 模式](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)。

不同于传统 RAG（每次查询都从头重新发现知识），wiki 把知识编译一次并保持最新。交叉引用已经就位。矛盾已被标出。综述反映了所摄入的一切。

**分工：** 人负责策展来源、指引分析方向。agent 负责摘要、交叉引用、归档并维持一致性。

## 本 skill 何时启用

用户做以下事情时用本 skill：
- 要创建、构建或启动一个 wiki 或知识库
- 要把某个来源摄入、添加或处理进 wiki
- 问一个问题，且配置路径下已存在 wiki
- 要 lint、审计或给 wiki 做体检
- 在研究语境里提到他们的 wiki、知识库或「笔记」

## Wiki 位置

**位置：** 通过 `WIKI_PATH` 环境变量设置（如写在 `${HERMES_HOME:-~/.hermes}/.env` 里）。

未设置时默认 `~/wiki`。

```bash
WIKI="${WIKI_PATH:-$HOME/wiki}"
```

wiki 只是一个 markdown 文件目录 — 用 Obsidian、VS Code 或任意编辑器打开即可。无需数据库，无需特殊工具。

## 架构：三层

```
wiki/
├── SCHEMA.md           # Conventions, structure rules, domain config
├── index.md            # Sectioned content catalog with one-line summaries
├── log.md              # Chronological action log (append-only, rotated yearly)
├── raw/                # Layer 1: Immutable source material
│   ├── articles/       # Web articles, clippings
│   ├── papers/         # PDFs, arxiv papers
│   ├── transcripts/    # Meeting notes, interviews
│   └── assets/         # Images, diagrams referenced by sources
├── entities/           # Layer 2: Entity pages (people, orgs, products, models)
├── concepts/           # Layer 2: Concept/topic pages
├── comparisons/        # Layer 2: Side-by-side analyses
└── queries/            # Layer 2: Filed query results worth keeping
```

**第 1 层 — 原始来源：** 不可变。agent 只读，绝不修改。
**第 2 层 — Wiki：** 由 agent 拥有的 markdown 文件。由 agent 创建、更新并交叉引用。
**第 3 层 — Schema：** `SCHEMA.md` 定义结构、约定与标签分类法。

## 续接已有 wiki（关键 — 每个会话都要做）

当用户已有 wiki 时，**动手前务必先定位自身**：

① **读 `SCHEMA.md`** — 理解领域、约定与标签分类法。
② **读 `index.md`** — 了解有哪些页面及其摘要。
③ **扫 `log.md` 近期内容** — 读最后 20-30 条，了解近期活动。

```bash
WIKI="${WIKI_PATH:-$HOME/wiki}"
# Orientation reads at session start
read_file "$WIKI/SCHEMA.md"
read_file "$WIKI/index.md"
read_file "$WIKI/log.md" offset=<last 30 lines>
```

只有定位之后才去做摄入、查询或 lint。这能避免：
- 为已存在的实体创建重复页面
- 漏掉与已有内容的交叉引用
- 违背 schema 的约定
- 重复已记录的工作

对大型 wiki（100+ 页），新建任何东西前还要对当前主题跑一次 `search_files`。

## 初始化新 wiki

当用户要创建或启动 wiki 时：

1. 确定 wiki 路径（来自 `$WIKI_PATH` 环境变量，或问用户；默认 `~/wiki`）
2. 创建上面的目录结构
3. 问用户 wiki 覆盖什么领域 — 要具体
4. 写针对该领域定制的 `SCHEMA.md`（见下方模板）
5. 写带分节表头的初始 `index.md`
6. 写含创建条目的初始 `log.md`
7. 确认 wiki 就绪，并建议首批要摄入的来源

### SCHEMA.md 模板

按用户领域调整。schema 约束 agent 行为并保证一致性：

```markdown
# Wiki Schema

## Domain
[What this wiki covers — e.g., "AI/ML research", "personal health", "startup intelligence"]

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `transformer-architecture.md`)
- Every wiki page starts with YAML frontmatter (see below)
- Use `[[wikilinks]]` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- **Provenance markers:** On pages that synthesize 3+ sources, append `^[raw/articles/source-file.md]`
  at the end of paragraphs whose claims come from a specific source. This lets a reader trace each
  claim back without re-reading the whole raw file. Optional on single-source pages where the
  `sources:` frontmatter is enough.

## Frontmatter
  ```yaml
  ---
  title: Page Title
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  type: entity | concept | comparison | query | summary
  tags: [from taxonomy below]
  sources: [raw/articles/source-name.md]
  # Optional quality signals:
  confidence: high | medium | low        # how well-supported the claims are
  contested: true                        # set when the page has unresolved contradictions
  contradictions: [other-page-slug]      # pages this one conflicts with
  ---
  ```

`confidence` and `contested` are optional but recommended for opinion-heavy or fast-moving
topics. Lint surfaces `contested: true` and `confidence: low` pages for review so weak claims
don't silently harden into accepted wiki fact.

### raw/ Frontmatter

Raw sources ALSO get a small frontmatter block so re-ingests can detect drift:

```yaml
---
source_url: https://example.com/article   # original URL, if applicable
ingested: YYYY-MM-DD
sha256: <hex digest of the raw content below the frontmatter>
---
```

The `sha256:` lets a future re-ingest of the same URL skip processing when content is unchanged,
and flag drift when it has changed. Compute over the body only (everything after the closing
`---`), not the frontmatter itself.

## Tag Taxonomy
[Define 10-20 top-level tags for the domain. Add new tags here BEFORE using them.]

Example for AI/ML:
- Models: model, architecture, benchmark, training
- People/Orgs: person, company, lab, open-source
- Techniques: optimization, fine-tuning, inference, alignment, data
- Meta: comparison, timeline, controversy, prediction

Rule: every tag on a page must appear in this taxonomy. If a new tag is needed,
add it here first, then use it. This prevents tag sprawl.

## Page Thresholds
- **Create a page** when an entity/concept appears in 2+ sources OR is central to one source
- **Add to existing page** when a source mentions something already covered
- **DON'T create a page** for passing mentions, minor details, or things outside the domain
- **Split a page** when it exceeds ~200 lines — break into sub-topics with cross-links
- **Archive a page** when its content is fully superseded — move to `_archive/`, remove from index

## Entity Pages
One page per notable entity. Include:
- Overview / what it is
- Key facts and dates
- Relationships to other entities ([[wikilinks]])
- Source references

## Concept Pages
One page per concept or topic. Include:
- Definition / explanation
- Current state of knowledge
- Open questions or debates
- Related concepts ([[wikilinks]])

## Comparison Pages
Side-by-side analyses. Include:
- What is being compared and why
- Dimensions of comparison (table format preferred)
- Verdict or synthesis
- Sources

## Update Policy
When new information conflicts with existing content:
1. Check the dates — newer sources generally supersede older ones
2. If genuinely contradictory, note both positions with dates and sources
3. Mark the contradiction in frontmatter: `contradictions: [page-name]`
4. Flag for user review in the lint report
```

### index.md 模板

索引按类型分节。每条一行：wikilink + 摘要。

```markdown
# Wiki Index

> Content catalog. Every wiki page listed under its type with a one-line summary.
> Read this first to find relevant pages for any query.
> Last updated: YYYY-MM-DD | Total pages: N

## Entities
<!-- Alphabetical within section -->

## Concepts

## Comparisons

## Queries
```

**扩展规则：** 任一小节超过 50 条时，按首字母或子领域拆成子节。索引总数超过 200 条时，创建 `_meta/topic-map.md`，按主题分组页面以便更快导航。

### log.md 模板

```markdown
# Wiki Log

> Chronological record of all wiki actions. Append-only.
> Format: `## [YYYY-MM-DD] action | subject`
> Actions: ingest, update, query, lint, create, archive, delete
> When this file exceeds 500 entries, rotate: rename to log-YYYY.md, start fresh.

## [YYYY-MM-DD] create | Wiki initialized
- Domain: [domain]
- Structure created with SCHEMA.md, index.md, log.md
```

## 核心操作

### 1. 摄入

当用户给出一个来源（URL、文件、粘贴文本）时，把它并进 wiki：

① **捕获原始来源：**
   - URL → 用 `web_extract` 取 markdown，存到 `raw/articles/`
   - PDF → 用 `web_extract`（能处理 PDF），存到 `raw/papers/`
   - 粘贴文本 → 存到合适的 `raw/` 子目录
   - 给文件起描述性名字：`raw/articles/karpathy-llm-wiki-2026.md`
   - **加 raw frontmatter**（`source_url`、`ingested`、正文的 `sha256`）。
     同一 URL 再次摄入时：重算 sha256，与存的值比 —
     相同则跳过，不同则标出漂移并更新。这足够便宜，每次重摄入都能做，
     能抓住来源的静默变更。

② 与用户**讨论要点** — 什么有意思、对领域什么重要。（在自动化/cron 语境里跳过 — 直接往下走。）

③ **检查已有什么** — 搜 index.md 并用 `search_files` 找出被提到的实体/概念已有的页面。这就是一个会生长的 wiki 与一堆重复文件的区别。

④ **写或更新 wiki 页面：**
   - **新实体/概念：** 仅当满足 SCHEMA.md 里的 Page Thresholds（2+ 来源提及，或某个来源的核心）才建页
   - **已有页面：** 补新信息、更新事实、更新 `updated` 日期。
     新信息与已有内容矛盾时，遵循 Update Policy。
   - **交叉引用：** 每个新增或更新的页面都必须通过 `[[wikilinks]]` 链到至少 2 个其他页面。检查已有页面是否链回来。
   - **标签：** 只用 SCHEMA.md 分类法里的标签
   - **出处：** 在综合 3+ 来源的页面上，给其论断可追溯到特定来源的段落追加 `^[raw/articles/source.md]` 标记。
   - **置信度：** 对观点密集、快速变化或单一来源的论断，在 frontmatter 里设 `confidence: medium` 或 `low`。除非论断在多个来源间都有良好支持，否则别标 `high`。

⑤ **更新导航：**
   - 把新页面按字母序加进 `index.md` 的正确小节
   - 更新 index 表头里的 "Total pages" 计数与 "Last updated" 日期
   - 追加到 `log.md`：`## [YYYY-MM-DD] ingest | Source Title`
   - 在 log 条目里列出每个创建或更新的文件

⑥ **报告变了什么** — 向用户列出每个创建或更新的文件。

一个来源可能触发 5-15 个 wiki 页面的更新。这很正常、也是想要的 — 这就是复利效应。

### 2. 查询

当用户就 wiki 的领域提问时：

① **读 `index.md`** 找出相关页面。
② **对 100+ 页的 wiki**，还要在所有 `.md` 文件里 `search_files` 搜关键词 — 光靠索引可能漏掉相关内容。
③ 用 `read_file` **读相关页面**。
④ 从已编译的知识里**综合出答案**。引用你取用的 wiki 页面："Based on [[page-a]] and [[page-b]]..."
⑤ **把有价值的答案归档回去** — 若答案是一次实质的对比、深入分析或新颖综述，在 `queries/` 或 `comparisons/` 里建页。别归档琐碎查询 — 只归档重新推导会很痛苦的答案。
⑥ 用查询内容及是否归档来**更新 log.md**。

### 3. Lint

当用户要 lint、体检或审计 wiki 时：

① **孤立页面：** 找出没有其他页面 `[[wikilinks]]` 指入的页面。
```python
# Use execute_code for this — programmatic scan across all wiki pages
import os, re
from collections import defaultdict
wiki = "<WIKI_PATH>"
# Scan all .md files in entities/, concepts/, comparisons/, queries/
# Extract all [[wikilinks]] — build inbound link map
# Pages with zero inbound links are orphans
```

② **断链 wikilink：** 找出指向不存在页面的 `[[links]]`。

③ **索引完整性：** 每个 wiki 页面都应出现在 `index.md`。把文件系统与索引条目对照。

④ **Frontmatter 校验：** 每个 wiki 页面必须具备所有必填字段
   （title、created、updated、type、tags、sources）。标签必须在分类法内。

⑤ **陈旧内容：** `updated` 日期比提及相同实体的最新来源还旧 90 天以上的页面。

⑥ **矛盾：** 同一主题但论断冲突的页面。找出共享标签/实体却陈述不同事实的页面。把所有带 `contested: true` 或 `contradictions:` frontmatter 的页面呈现给用户复查。

⑦ **质量信号：** 列出 `confidence: low` 的页面，以及只引用单一来源却没设 confidence 字段的页面 — 它们要么补旁证，要么降级为 `confidence: medium`。

⑧ **来源漂移：** 对 `raw/` 里每个带 `sha256:` frontmatter 的文件，重算哈希并标出不匹配。不匹配说明原始文件被编辑过（不该发生 — raw/ 不可变），或摄入自一个此后已变化的 URL。不是硬错误，但值得报告。

⑨ **页面大小：** 标出超过 200 行的页面 — 拆分候选。

⑩ **标签审计：** 列出所有在用标签，标出不在 SCHEMA.md 分类法里的。

⑪ **日志轮转：** log.md 超过 500 条时轮转它。

⑫ **报告发现**，带具体文件路径与建议动作，按严重度分组
   （断链 > 孤立页 > 来源漂移 > 争议页 > 陈旧内容 > 风格问题）。

⑬ **追加到 log.md：** `## [YYYY-MM-DD] lint | N issues found`

## 使用 wiki

### 搜索

```bash
# Find pages by content
search_files "transformer" path="$WIKI" file_glob="*.md"

# Find pages by filename
search_files "*.md" target="files" path="$WIKI"

# Find pages by tag
search_files "tags:.*alignment" path="$WIKI" file_glob="*.md"

# Recent activity
read_file "$WIKI/log.md" offset=<last 20 lines>
```

### 批量摄入

一次摄入多个来源时，把更新批处理：
1. 先读完所有来源
2. 找出所有来源中的所有实体与概念
3. 为它们全体检查已有页面（一次搜索，不是 N 次）
4. 一遍创建/更新页面（避免冗余更新）
5. 最后更新一次 index.md
6. 写一条覆盖整批的 log 条目

### 归档

当内容被完全取代或领域范围变化时：
1. 若 `_archive/` 目录不存在就创建
2. 把页面按其原路径移到 `_archive/`（如 `_archive/entities/old-page.md`）
3. 从 `index.md` 移除
4. 更新任何链到它的页面 — 把 wikilink 换成纯文本 + "(archived)"
5. 记录归档动作

### Obsidian 集成

wiki 目录开箱即可当 Obsidian vault 用：
- `[[wikilinks]]` 渲染成可点击链接
- Graph View 可视化知识网络
- YAML frontmatter 驱动 Dataview 查询
- `raw/assets/` 文件夹存放经 `![[image.png]]` 引用的图片

为达到最佳效果：
- 把 Obsidian 的附件文件夹设为 `raw/assets/`
- 在 Obsidian 设置里启用 "Wikilinks"（通常默认开）
- 安装 Dataview 插件以做 `TABLE tags FROM "entities" WHERE contains(tags, "company")` 这类查询

若与本 skill 一起用 Obsidian skill，把 `OBSIDIAN_VAULT_PATH` 设为与 wiki 路径相同的目录。

### Obsidian Headless（服务器与无头机器）

在没有显示器的机器上，用 `obsidian-headless` 代替桌面应用。
它通过 Obsidian Sync 在无 GUI 下同步 vault — 非常适合跑在服务器上的 agent 写入 wiki、而 Obsidian 桌面在另一台设备上读的场景。

**配置：**
```bash
# Requires Node.js 22+
npm install -g obsidian-headless

# Login (requires Obsidian account with Sync subscription)
ob login --email <email> --password '<password>'

# Create a remote vault for the wiki
ob sync-create-remote --name "LLM Wiki"

# Connect the wiki directory to the vault
cd ~/wiki
ob sync-setup --vault "<vault-id>"

# Initial sync
ob sync

# Continuous sync (foreground — use systemd for background)
ob sync --continuous
```

**经 systemd 的持续后台同步：**
```ini
# ~/.config/systemd/user/obsidian-wiki-sync.service
[Unit]
Description=Obsidian LLM Wiki Sync
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/path/to/ob sync --continuous
WorkingDirectory=%h/wiki
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now obsidian-wiki-sync
# Enable linger so sync survives logout:
sudo loginctl enable-linger $USER
```

这让 agent 在服务器上写入 `~/wiki`，而你在笔记本/手机上用 Obsidian 浏览同一个 vault — 改动几秒内出现。

## 陷阱

- **绝不修改 `raw/` 里的文件** — 来源不可变。更正写在 wiki 页面里。
- **务必先定位** — 新会话里任何操作前先读 SCHEMA + index + 近期 log。
  跳过它会造成重复与漏掉交叉引用。
- **务必更新 index.md 与 log.md** — 跳过会让 wiki 退化。它们是导航骨架。
- **别为顺带一提创建页面** — 遵循 SCHEMA.md 里的 Page Thresholds。一个名字在脚注里出现一次，不足以立实体页。
- **别创建没有交叉引用的页面** — 孤立页面不可见。每个页面必须链到至少 2 个其他页面。
- **Frontmatter 必须写** — 它支撑搜索、过滤与陈旧检测。
- **标签必须来自分类法** — 自由标签会退化成噪音。先把新标签加进 SCHEMA.md，再用。
- **保持页面可扫读** — 一个 wiki 页面应在 30 秒内读完。超过 200 行的页面拆分。详细分析移到专门的深入页面。
- **大批量更新前先问** — 若一次摄入会触及 10+ 已有页面，先与用户确认范围。
- **轮转日志** — log.md 超过 500 条时，重命名为 `log-YYYY.md` 并重新开始。
  agent 应在 lint 时检查 log 大小。
- **显式处理矛盾** — 别悄悄覆盖。把两种论断连同日期都记下，在 frontmatter 里标记，标给用户复查。

## 相关工具

[llm-wiki-compiler](https://github.com/atomicmemory/llm-wiki-compiler) 是一个 Node.js CLI，
同样受 Karpathy 启发，把来源编译成概念 wiki。它与 Obsidian 兼容，
所以想要计划/CLI 驱动编译流水线的用户可以让它指向本 skill 维护的同一个 vault。
取舍：它自己掌管页面生成（取代 agent 对建页的判断）且面向小语料库调优。
想要 agent 在环策展时用本 skill；想要批量编译一个来源目录时用 llmwiki。
