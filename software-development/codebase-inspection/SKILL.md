---
name: codebase-inspection
description: "用 pygount 体检代码库时使用：行数、语言构成、占比。只要要算 LOC、拆语言构成或看代码与注释比，就主动加载，即使用户没明说 pygount。不用于功能级代码审查。"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [LOC, Code Analysis, pygount, Codebase, Metrics, Repository]
    related_skills: [github]
prerequisites:
  commands: [pygount]
---

# 用 pygount 体检代码库

用 `pygount` 分析仓库的代码行数、语言构成、文件数与代码/注释比。

## When to Use（何时用）

- 用户要 LOC（代码行数）统计
- 用户要看仓库的语言构成
- 用户问代码库规模或组成
- 用户要代码与注释比
- 泛泛的「这个仓库有多大」类问题

## Prerequisites（前置）

```bash
pip install --break-system-packages pygount 2>/dev/null || pip install pygount
```

## 1. 基本汇总（最常用）

拿到含文件数、代码行、注释行的完整语言构成：

```bash
cd /path/to/repo
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,.eggs,*.egg-info" \
  .
```

**重要：** 始终用 `--folders-to-skip` 排除依赖/构建目录，否则 pygount 会爬进去，耗时很长甚至卡死。

## 2. 常用目录排除

按项目类型调整：

```bash
# Python projects
--folders-to-skip=".git,venv,.venv,__pycache__,.cache,dist,build,.tox,.eggs,.mypy_cache"

# JavaScript/TypeScript projects
--folders-to-skip=".git,node_modules,dist,build,.next,.cache,.turbo,coverage"

# General catch-all
--folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,vendor,third_party"
```

## 3. 按语言过滤

```bash
# Only count Python files
pygount --suffix=py --format=summary .

# Only count Python and YAML
pygount --suffix=py,yaml,yml --format=summary .
```

## 4. 逐文件详细输出

```bash
# Default format shows per-file breakdown
pygount --folders-to-skip=".git,node_modules,venv" .

# Sort by code lines (pipe through sort)
pygount --folders-to-skip=".git,node_modules,venv" . | sort -t$'\t' -k1 -nr | head -20
```

## 5. 输出格式

```bash
# Summary table (default recommendation)
pygount --format=summary .

# JSON output for programmatic use
pygount --format=json .

# Pipe-friendly: Language, file count, code, docs, empty, string
pygount --format=summary . 2>/dev/null
```

## 6. 解读结果

汇总表的列：
- **Language** — 检测到的编程语言
- **Files** — 该语言的文件数
- **Code** — 实际代码行数（可执行/声明式）
- **Comment** — 注释或文档行数
- **%** — 占总量的百分比

特殊伪语言：
- `__empty__` — 空文件
- `__binary__` — 二进制文件（图片、编译产物等）
- `__generated__` — 自动生成的文件（启发式判定）
- `__duplicate__` — 内容完全相同的文件
- `__unknown__` — 无法识别的文件类型

## Pitfalls（坑）

1. **始终排除 .git、node_modules、venv** — 不设 `--folders-to-skip`，pygount 会爬遍一切，在庞大依赖树上可能耗时数分钟甚至卡死。
2. **Markdown 显示 0 代码行** — pygount 把全部 Markdown 内容归为注释而非代码，这是预期行为。
3. **JSON 文件代码行偏低** — pygount 统计 JSON 行可能偏保守；要准确统计 JSON 行数，直接用 `wc -l`。
4. **大型 monorepo** — 超大仓库考虑用 `--suffix` 只针对特定语言，而非全量扫描。
