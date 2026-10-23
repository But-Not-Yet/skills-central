---
name: claude-code
description: "把编程任务委派给 Claude Code CLI 时使用。只要要开 feature、修 bug、提 PR 或做代码审查，就主动加载，即使用户只说「用 Claude Code 干」或「让 CC 跑一下」。不用于纯本地手工改代码。"
version: 2.2.1
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Claude, Anthropic, Code-Review, Refactoring, PTY, Automation]
    related_skills: [codex, hermes-agent, opencode]
---

# Claude Code — Hermes 编排指南

通过 Hermes terminal 把编码任务委派给 [Claude Code](https://code.claude.com/docs/en/cli-reference)（Anthropic 的自主编码代理 CLI）。Claude Code v2.x 能自主读取文件、编写代码、执行 shell 命令、派生子代理，并管理 git 工作流。

## 前置条件

- **安装：** `npm install -g @anthropic-ai/claude-code`
- **认证：** 运行一次 `claude` 登录（Pro/Max 用浏览器 OAuth，或设置 `ANTHROPIC_API_KEY`）
- **Console 认证：** `claude auth login --console`（API key 计费）
- **SSO 认证：** `claude auth login --sso`（Enterprise）
- **查看状态：** `claude auth status`（JSON）或 `claude auth status --text`（人类可读）
- **健康检查：** `claude doctor` —— 检查自动更新器与安装状态
- **版本检查：** `claude --version`（需 v2.x+）
- **更新：** `claude update` 或 `claude upgrade`

## 两种编排模式

Hermes 与 Claude Code 的交互有两种根本不同的方式，按任务选择。

### 模式 1：Print Mode（`-p`）—— 非交互（多数任务首选）

Print mode 执行一次性任务，返回结果后退出。无需 PTY，无交互提示。这是最干净的集成路径。

```
terminal(command="claude -p 'Add error handling to all API calls in src/' --allowedTools 'Read,Edit' --max-turns 10", workdir="/path/to/project", timeout=120)
```

**何时使用 print mode：**
- 一次性编码任务（修 bug、加 feature、重构）
- CI/CD 自动化与脚本
- 用 `--json-schema` 做结构化数据抽取
- 管道输入处理（`cat file | claude -p "analyze this"`）
- 任何不需要多轮对话的任务

**Print mode 跳过所有交互对话框** —— 无 workspace 信任提示，无权限确认。这使它非常适合自动化。

### 模式 2：通过 tmux 的交互式 PTY —— 多轮会话

交互模式提供完整的对话式 REPL，可发送追问、使用斜杠命令，并实时观察 Claude 工作。**需要 tmux 编排。**

```
# Start a tmux session
terminal(command="tmux new-session -d -s claude-work -x 140 -y 40")

# Launch Claude Code inside it
terminal(command="tmux send-keys -t claude-work 'cd /path/to/project && claude' Enter")

# Wait for startup, then send your task
# (after ~3-5 seconds for the welcome screen)
terminal(command="sleep 5 && tmux send-keys -t claude-work 'Refactor the auth module to use JWT tokens' Enter")

# Monitor progress by capturing the pane
terminal(command="sleep 15 && tmux capture-pane -t claude-work -p -S -50")

# Send follow-up tasks
terminal(command="tmux send-keys -t claude-work 'Now add unit tests for the new JWT code' Enter")

# Exit when done
terminal(command="tmux send-keys -t claude-work '/exit' Enter")
```

**何时使用交互模式：**
- 多轮迭代工作（重构 → 审查 → 修复 → 测试循环）
- 需要 human-in-the-loop 决策的任务
- 探索式编码会话
- 需要使用 Claude 的斜杠命令（`/compact`、`/review`、`/model`）

## PTY 对话框处理（交互模式的关键）

Claude Code 首次启动时最多弹出两个确认对话框。你必须通过 tmux send-keys 处理：

### 对话框 1：Workspace 信任（首次访问某目录）
```
❯ 1. Yes, I trust this folder    ← DEFAULT (just press Enter)
  2. No, exit
```
**处理：** `tmux send-keys -t <session> Enter` —— 默认选项即正确。

### 对话框 2：单项权限提示（常规流程）

每个需要批准的工具调用（写文件、shell 命令、网络）都会弹出提示。只回答当前这一条提示 —— 这与为整轮运行禁用提示不同：
```
# Read the prompt before answering it
terminal(command="tmux capture-pane -t <session> -p -S -30")
# Allow this one action (Enter = default "Yes"); Esc declines it
terminal(command="tmux send-keys -t <session> Enter")
```
绝不要用定时器盲发 `Enter` 去批准你尚未读过的提示 —— 那不过是多此一举的 bypass flag。

比完全 bypass 更窄的 opt-in 是 `--permission-mode acceptEdits`：工作目录内的文件编辑被接受，shell 及其他工具调用仍会提示。仅在审查任务后、于专用 worktree 中使用。

### 稳健的对话框处理模式
```
# Default launch — keep permission prompts enabled
terminal(command="tmux send-keys -t claude-work 'claude \"your task\"' Enter")

# Handle trust dialog (Enter for default "Yes")
terminal(command="sleep 4 && tmux send-keys -t claude-work Enter")

# Now wait for Claude to work
terminal(command="sleep 15 && tmux capture-pane -t claude-work -p -S -60")
```

**注意：** 对某目录首次接受信任后，信任对话框不再出现。

### Opt-in：--dangerously-skip-permissions（仅限隔离环境）

这将为整轮运行禁用权限提示 —— 无提示地授予文件系统、shell 与网络访问。仅可在一次性 worktree 或隔离容器中使用。
```
❯ 1. No, exit                    ← DEFAULT (safe choice)
  2. Yes, I accept
```
接受方式：`tmux send-keys -t <session> Down && sleep 0.3 && tmux send-keys -t <session> Enter`

## CLI Subcommands

| Subcommand | Purpose |
|------------|---------|
| `claude` | Start interactive REPL |
| `claude "query"` | Start REPL with initial prompt |
| `claude -p "query"` | Print mode (non-interactive, exits when done) |
| `cat file \| claude -p "query"` | Pipe content as stdin context |
| `claude -c` | Continue the most recent conversation in this directory |
| `claude -r "id"` | Resume a specific session by ID or name |
| `claude auth login` | Sign in (add `--console` for API billing, `--sso` for Enterprise) |
| `claude auth status` | Check login status (returns JSON; `--text` for human-readable) |
| `claude mcp add <name> -- <cmd>` | Add an MCP server |
| `claude mcp list` | List configured MCP servers |
| `claude mcp remove <name>` | Remove an MCP server |
| `claude agents` | List configured agents |
| `claude doctor` | Run health checks on installation and auto-updater |
| `claude update` / `claude upgrade` | Update Claude Code to latest version |
| `claude remote-control` | Start server to control Claude from claude.ai or mobile app |
| `claude install [target]` | Install native build (stable, latest, or specific version) |
| `claude setup-token` | Set up long-lived auth token (requires subscription) |
| `claude plugin` / `claude plugins` | Manage Claude Code plugins |
| `claude auto-mode` | Inspect auto mode classifier configuration |

## Print Mode 深入

### 结构化 JSON 输出
```
terminal(command="claude -p 'Analyze auth.py for security issues' --output-format json --max-turns 5", workdir="/project", timeout=120)
```

返回一个 JSON 对象，包含：
```json
{
  "type": "result",
  "subtype": "success",
  "result": "The analysis text...",
  "session_id": "75e2167f-...",
  "num_turns": 3,
  "total_cost_usd": 0.0787,
  "duration_ms": 10276,
  "stop_reason": "end_turn",
  "terminal_reason": "completed",
  "usage": { "input_tokens": 5, "output_tokens": 603, ... },
  "modelUsage": { "claude-sonnet-4-6": { "costUSD": 0.078, "contextWindow": 200000 } }
}
```

**关键字段：** `session_id` 用于恢复会话，`num_turns` 为 agentic 循环次数，`total_cost_usd` 用于花费追踪，`subtype` 用于成功/错误识别（`success`、`error_max_turns`、`error_budget`）。

### 流式 JSON 输出
要实时流式传输 token，使用带 `--verbose` 的 `stream-json`：
```
terminal(command="claude -p 'Write a summary' --output-format stream-json --verbose --include-partial-messages", timeout=60)
```

返回换行分隔的 JSON 事件。用 jq 过滤出实时文本：
```
claude -p "Explain X" --output-format stream-json --verbose --include-partial-messages | \
  jq -rj 'select(.type == "stream_event" and .event.delta.type? == "text_delta") | .event.delta.text'
```

流事件包含 `system/api_retry`，带 `attempt`、`max_retries` 与 `error` 字段（如 `rate_limit`、`billing_error`）。

### 双向流式
要实时输入与输出双向流式传输：
```
claude -p "task" --input-format stream-json --output-format stream-json --replay-user-messages
```
`--replay-user-messages` 会在 stdout 上重新回显用户消息以作确认。

### 管道输入
```
# Pipe a file for analysis
terminal(command="cat src/auth.py | claude -p 'Review this code for bugs' --max-turns 1", timeout=60)

# Pipe multiple files
terminal(command="cat src/*.py | claude -p 'Find all TODO comments' --max-turns 1", timeout=60)

# Pipe command output
terminal(command="git diff HEAD~3 | claude -p 'Summarize these changes' --max-turns 1", timeout=60)
```

### JSON Schema for Structured Extraction
```
terminal(command="claude -p 'List all functions in src/' --output-format json --json-schema '{\"type\":\"object\",\"properties\":{\"functions\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}}},\"required\":[\"functions\"]}' --max-turns 5", workdir="/project", timeout=90)
```

从 JSON 结果中解析 `structured_output`。Claude 在返回前会按 schema 校验输出。

### 会话续接
```
# Start a task
terminal(command="claude -p 'Start refactoring the database layer' --output-format json --max-turns 10 > ~/.hermes/cache/scratch/session.json", workdir="/project", timeout=180)

# Resume with session ID
terminal(command="claude -p 'Continue and add connection pooling' --resume $(cat ~/.hermes/cache/scratch/session.json | python -c 'import json,sys; print(json.load(sys.stdin)[\"session_id\"])') --max-turns 5", workdir="/project", timeout=120)

# Or resume the most recent session in the same directory
terminal(command="claude -p 'What did you do last time?' --continue --max-turns 1", workdir="/project", timeout=30)

# Fork a session (new ID, keeps history)
terminal(command="claude -p 'Try a different approach' --resume <id> --fork-session --max-turns 10", workdir="/project", timeout=120)
```

### 面向 CI/脚本的 Bare Mode
```
terminal(command="claude --bare -p 'Run all tests and report failures' --allowedTools 'Read,Bash' --max-turns 10", workdir="/project", timeout=180)
```

`--bare` 跳过 hooks、plugins、MCP 发现与 CLAUDE.md 加载。启动最快。需要 `ANTHROPIC_API_KEY`（跳过 OAuth）。

要在 bare mode 下有选择地加载上下文：
| 加载项 | Flag |
|---------|------|
| 追加系统提示 | `--append-system-prompt "text"` 或 `--append-system-prompt-file path` |
| 设置 | `--settings <file-or-json>` |
| MCP server | `--mcp-config <file-or-json>` |
| 自定义 agent | `--agents '<json>'` |

### 过载时的 Fallback 模型
```
terminal(command="claude -p 'task' --fallback-model haiku --max-turns 5", timeout=90)
```
当默认模型过载时自动回退到指定模型（仅 print mode）。

## 完整 CLI Flags 参考

### 会话与环境
| Flag | 作用 |
|------|--------|
| `-p, --print` | 非交互一次性模式（完成后退出） |
| `-c, --continue` | 恢复当前目录最近一次会话 |
| `-r, --resume <id>` | 按 ID 或名称恢复指定会话（无 ID 时弹出交互选择器） |
| `--fork-session` | 恢复时创建新 session ID 而非复用原 ID |
| `--session-id <uuid>` | 为会话使用指定 UUID |
| `--no-session-persistence` | 不把会话保存到磁盘（仅 print mode） |
| `--add-dir <paths...>` | 授予 Claude 访问额外工作目录 |
| `-w, --worktree [name]` | 在 `.claude/worktrees/<name>` 的隔离 git worktree 中运行 |
| `--tmux` | 为该 worktree 创建 tmux 会话（需 `--worktree`） |
| `--ide` | 启动时自动连接可用的 IDE |
| `--chrome` / `--no-chrome` | 启用/禁用用于网页测试的 Chrome 浏览器集成 |
| `--from-pr [number]` | 恢复与指定 GitHub PR 关联的会话 |
| `--file <specs...>` | 启动时下载的文件资源（格式：`file_id:relative_path`） |

### 模型与性能
| Flag | 作用 |
|------|--------|
| `--model <alias>` | 模型选择：`sonnet`、`opus`、`haiku`，或类似 `claude-sonnet-4-6` 的完整名 |
| `--effort <level>` | 推理深度：`low`、`medium`、`high`、`xhigh`、`max` |
| `--max-turns <n>` | 限制 agentic 循环次数（仅 print mode。防止失控） |
| `--max-budget-usd <n>` | 以美元为上限限制 API 花费（仅 print mode） |
| `--fallback-model <model>` | 默认模型过载时自动回退（仅 print mode） |
| `--betas <betas...>` | 在 API 请求中携带的 Beta headers（仅 API key 用户） |

### 权限与安全
| Flag | 作用 |
|------|--------|
| `--dangerously-skip-permissions` | 仅 opt-in：禁用所有权限提示（写文件、bash、网络）。仅限一次性 worktree / 隔离容器 —— 见上文「Opt-in」 |
| `--allow-dangerously-skip-permissions` | 将 bypass 作为*可选项*启用，但默认不启用 |
| `--permission-mode <mode>` | `default`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions` |
| `--allowedTools <tools...>` | 白名单指定工具（逗号或空格分隔） |
| `--disallowedTools <tools...>` | 黑名单指定工具 |
| `--tools <tools...>` | 覆盖内置工具集（`""` = 无，`"default"` = 全部，或工具名） |

### 输出与输入格式
| Flag | 作用 |
|------|--------|
| `--output-format <fmt>` | `text`（默认）、`json`（单结果对象）、`stream-json`（换行分隔） |
| `--input-format <fmt>` | `text`（默认）或 `stream-json`（实时流式输入） |
| `--json-schema <schema>` | 强制输出符合 schema 的结构化 JSON |
| `--verbose` | 完整逐轮输出 |
| `--include-partial-messages` | 随到随包含部分消息块（stream-json + print） |
| `--replay-user-messages` | 在 stdout 重新回显用户消息（stream-json 双向） |

### 系统提示与上下文
| Flag | 作用 |
|------|--------|
| `--append-system-prompt <text>` | **追加**到默认系统提示（保留内置能力） |
| `--append-system-prompt-file <path>` | 把文件内容**追加**到默认系统提示 |
| `--system-prompt <text>` | **替换**整个系统提示（通常应改用 --append） |
| `--system-prompt-file <path>` | 用文件内容**替换**系统提示 |
| `--bare` | 跳过 hooks、plugins、MCP 发现、CLAUDE.md、OAuth（启动最快） |
| `--agents '<json>'` | 以 JSON 动态定义自定义子代理 |
| `--mcp-config <path>` | 从 JSON 文件加载 MCP server（可重复） |
| `--strict-mcp-config` | 仅使用来自 `--mcp-config` 的 MCP server，忽略其他所有 MCP 配置 |
| `--settings <file-or-json>` | 从 JSON 文件或内联 JSON 加载额外设置 |
| `--setting-sources <sources>` | 逗号分隔的加载来源：`user`、`project`、`local` |
| `--plugin-dir <paths...>` | 仅为本会话从这些目录加载插件 |
| `--disable-slash-commands` | 禁用所有 skills/斜杠命令 |

### 调试
| Flag | 作用 |
|------|--------|
| `-d, --debug [filter]` | 启用调试日志，可带分类过滤（如 `"api,hooks"`、`"!1p,!file"`） |
| `--debug-file <path>` | 把调试日志写入文件（隐式启用 debug mode） |

### Agent 团队
| Flag | 作用 |
|------|--------|
| `--teammate-mode <mode>` | agent 团队的显示方式：`auto`、`in-process` 或 `tmux` |
| `--brief` | 启用 `SendUserMessage` 工具用于 agent 到用户的通信 |

### --allowedTools / --disallowedTools 的工具名语法
```
Read                    # All file reading
Edit                    # File editing (existing files)
Write                   # File creation (new files)
Bash                    # All shell commands
Bash(git *)             # Only git commands
Bash(git commit *)      # Only git commit commands
Bash(npm run lint:*)    # Pattern matching with wildcards
WebSearch               # Web search capability
WebFetch                # Web page fetching
mcp__<server>__{tool}   # Specific MCP tool
```

## 设置与配置

### 设置层级（优先级从高到低）
1. **CLI flags** —— 覆盖一切
2. **本地项目：** `.claude/settings.local.json`（个人，gitignored）
3. **项目：** `.claude/settings.json`（共享，git-tracked）
4. **用户：** `~/.claude/settings.json`（全局）

### 设置中的权限
```json
{
  "permissions": {
    "allow": ["Bash(npm run lint:*)", "WebSearch", "Read"],
    "ask": ["Write(*.ts)", "Bash(git push*)"],
    "deny": ["Read(.env)", "Bash(rm -rf *)"]
  }
}
```

### 记忆文件（CLAUDE.md）层级
1. **全局：** `~/.claude/CLAUDE.md` —— 适用于所有项目
2. **项目：** `./CLAUDE.md` —— 项目专属上下文（git-tracked）
3. **本地：** `.claude/CLAUDE.local.md` —— 个人项目覆盖（gitignored）

在交互模式下用 `#` 前缀快速写入记忆：`# Always use 2-space indentation`。

## 交互式会话：斜杠命令

### 会话与上下文
| Command | 用途 |
|---------|---------|
| `/help` | 显示所有命令（含自定义与 MCP 命令） |
| `/compact [focus]` | 压缩上下文以省 token。CLAUDE.md 在压缩后保留。例如 `/compact focus on auth logic` |
| `/clear` | 清空对话历史以全新开始 |
| `/context` | 以彩色网格可视化上下文用量并给出优化提示 |
| `/cost` | 查看 token 用量，含按模型与缓存命中细分 |
| `/resume` | 切换到或恢复另一个会话 |
| `/rewind` | 回退到对话或代码的先前检查点 |
| `/btw <question>` | 提一个附带问题，不增加上下文开销 |
| `/status` | 显示版本、连通性与会话信息 |
| `/todos` | 列出对话中跟踪的行动项 |
| `/exit` 或 `Ctrl+D` | 结束会话 |

### 开发与审查
| Command | 用途 |
|---------|---------|
| `/review` | 请求对当前改动做代码审查 |
| `/security-review` | 对当前改动做安全分析 |
| `/plan [description]` | 进入 Plan 模式并自动开始任务规划 |
| `/loop [interval]` | 在会话内安排重复任务 |
| `/batch` | 为大规模并行改动自动创建 worktree（5-30 个） |

### 配置与工具
| Command | 用途 |
|---------|---------|
| `/model [model]` | 会话中切换模型（用方向键调整 effort） |
| `/effort [level]` | 设置推理 effort：`low`、`medium`、`high`、`xhigh` 或 `max` |
| `/init` | 创建用于项目记忆的 CLAUDE.md 文件 |
| `/memory` | 打开 CLAUDE.md 进行编辑 |
| `/config` | 打开交互式设置配置 |
| `/permissions` | 查看/更新工具权限 |
| `/agents` | 管理专用子代理 |
| `/mcp` | 管理 MCP server 的交互式 UI |
| `/add-dir` | 添加额外工作目录（对 monorepo 有用） |
| `/usage` | 显示套餐限额与限流状态 |
| `/voice` | 启用按键说话语音模式（20 种语言。按住 Space 录音，松开发送） |
| `/release-notes` | 版本发行说明的交互式选择器 |

### 自定义斜杠命令
创建 `.claude/commands/<name>.md`（项目共享）或 `~/.claude/commands/<name>.md`（个人）：

```markdown
# .claude/commands/deploy.md
Run the deploy pipeline:
1. Run all tests
2. Build the Docker image
3. Push to registry
4. Update the $ARGUMENTS environment (default: staging)
```

用法：`/deploy production` —— `$ARGUMENTS` 会被替换为用户输入。

### Skills（自然语言调用）
与斜杠命令（手动调用）不同，`.claude/skills/` 中的 skills 是 markdown 指南，当任务匹配时 Claude 会通过自然语言自动调用：

```markdown
# .claude/skills/database-migration.md
When asked to create or modify database migrations:
1. Use Alembic for migration generation
2. Always create a rollback function
3. Test migrations against a local database copy
```

## 交互式会话：键盘快捷键

### 通用控制
| Key | 操作 |
|-----|--------|
| `Ctrl+C` | 取消当前输入或生成 |
| `Ctrl+D` | 退出会话 |
| `Ctrl+R` | 反向搜索命令历史 |
| `Ctrl+B` | 将运行中的任务转入后台 |
| `Ctrl+V` | 将图片粘贴进对话 |
| `Ctrl+O` | 转录模式 —— 查看 Claude 的思考过程 |
| `Ctrl+G` 或 `Ctrl+X Ctrl+E` | 在外部编辑器中打开提示 |
| `Esc Esc` | 回退对话或代码状态 / 总结 |

### 模式切换
| Key | 操作 |
|-----|--------|
| `Shift+Tab` | 循环切换权限模式（Normal → Auto-Accept → Plan） |
| `Alt+P` | 切换模型 |
| `Alt+T` | 切换思考模式 |
| `Alt+O` | 切换 Fast Mode |

### 多行输入
| Key | 操作 |
|-----|--------|
| `\` + `Enter` | 快速换行 |
| `Shift+Enter` | 换行（备选） |
| `Ctrl+J` | 换行（备选） |

### 输入前缀
| Prefix | 操作 |
|--------|--------|
| `!` | 直接执行 bash，绕过 AI（如 `!npm test`）。单独用 `!` 切换 shell 模式。 |
| `@` | 带自动补全地引用文件/目录（如 `@./src/api/`） |
| `#` | 快速写入 CLAUDE.md 记忆（如 `# Use 2-space indentation`） |
| `/` | 斜杠命令 |

### 技巧："ultrathink"
在提示中使用关键词 "ultrathink"，可在特定轮次达到最大推理 effort。无论当前 `/effort` 设置为何，它都会触发最深思考模式。

## PR 审查模式

### 快速审查（Print Mode）
```
terminal(command="cd /path/to/repo && git diff main...feature-branch | claude -p 'Review this diff for bugs, security issues, and style problems. Be thorough.' --max-turns 1", timeout=60)
```

### 深度审查（交互 + Worktree）
```
terminal(command="tmux new-session -d -s review -x 140 -y 40")
terminal(command="tmux send-keys -t review 'cd /path/to/repo && claude -w pr-review' Enter")
terminal(command="sleep 5 && tmux send-keys -t review Enter")  # Trust dialog
terminal(command="sleep 2 && tmux send-keys -t review 'Review all changes vs main. Check for bugs, security issues, race conditions, and missing tests.' Enter")
terminal(command="sleep 30 && tmux capture-pane -t review -p -S -60")
```

### 按 PR 编号审查
```
terminal(command="claude -p 'Review this PR thoroughly' --from-pr 42 --max-turns 10", workdir="/path/to/repo", timeout=120)
```

### 带 tmux 的 Claude Worktree
```
terminal(command="claude -w feature-x --tmux", workdir="/path/to/repo")
```
在 `.claude/worktrees/feature-x` 创建隔离 git worktree，并为其创建 tmux 会话。可用时使用 iTerm2 原生分屏。加 `--tmux=classic` 使用传统 tmux。

## 并行 Claude 实例

同时运行多个相互独立的 Claude 任务：

```
# Task 1: Fix backend
terminal(command="tmux new-session -d -s task1 -x 140 -y 40 && tmux send-keys -t task1 'cd ~/project && claude -p \"Fix the auth bug in src/auth.py\" --allowedTools \"Read,Edit\" --max-turns 10' Enter")

# Task 2: Write tests
terminal(command="tmux new-session -d -s task2 -x 140 -y 40 && tmux send-keys -t task2 'cd ~/project && claude -p \"Write integration tests for the API endpoints\" --allowedTools \"Read,Write,Bash\" --max-turns 15' Enter")

# Task 3: Update docs
terminal(command="tmux new-session -d -s task3 -x 140 -y 40 && tmux send-keys -t task3 'cd ~/project && claude -p \"Update README.md with the new API endpoints\" --allowedTools \"Read,Edit\" --max-turns 5' Enter")

# Monitor all
terminal(command="sleep 30 && for s in task1 task2 task3; do echo '=== '$s' ==='; tmux capture-pane -t $s -p -S -5 2>/dev/null; done")
```

## CLAUDE.md —— 项目上下文文件

Claude Code 会从项目根目录自动加载 `CLAUDE.md`。用它持久化项目上下文：

```markdown
# Project: My API

## Architecture
- FastAPI backend with SQLAlchemy ORM
- PostgreSQL database, Redis cache
- pytest for testing with 90% coverage target

## Key Commands
- `make test` — run full test suite
- `make lint` — ruff + mypy
- `make dev` — start dev server on :8000

## Code Standards
- Type hints on all public functions
- Docstrings in Google style
- 2-space indentation for YAML, 4-space for Python
- No wildcard imports
```

**写具体。** 不要写「写好的代码」，而写「JS 用 2 空格缩进」或「测试文件用 `.test.ts` 后缀命名」。具体指令能省下纠错轮次。

### Rules 目录（模块化 CLAUDE.md）
规则很多的项目，用 rules 目录代替一个庞大的 CLAUDE.md：
- **项目规则：** `.claude/rules/*.md` —— 团队共享，git-tracked
- **用户规则：** `~/.claude/rules/*.md` —— 个人，全局

rules 目录中的每个 `.md` 文件都会作为额外上下文加载。这比把所有内容塞进单个 CLAUDE.md 更清晰。

### 自动记忆
Claude 会自动把学到的项目上下文存到 `~/.claude/projects/<project>/memory/`。
- **上限：** 每项目 25KB 或 200 行
- 这与 CLAUDE.md 分开 —— 它是 Claude 自己对项目的笔记，跨会话累积

## 自定义子代理

在 `.claude/agents/`（项目）、`~/.claude/agents/`（个人）中定义专用 agent，或通过 `--agents` CLI flag（会话）：

### Agent 位置优先级
1. `.claude/agents/` —— 项目级，团队共享
2. `--agents` CLI flag —— 会话专属，动态
3. `~/.claude/agents/` —— 用户级，个人

### 创建一个 Agent
```markdown
# .claude/agents/security-reviewer.md
---
name: security-reviewer
description: Security-focused code review
model: opus
tools: [Read, Bash]
---
You are a senior security engineer. Review code for:
- Injection vulnerabilities (SQL, XSS, command injection)
- Authentication/authorization flaws
- Secrets in code
- Unsafe deserialization
```

调用方式：`@security-reviewer review the auth module`

### 通过 CLI 的动态 Agent
```
terminal(command="claude --agents '{\"reviewer\": {\"description\": \"Reviews code\", \"prompt\": \"You are a code reviewer focused on performance\"}}' -p 'Use @reviewer to check auth.py'", timeout=120)
```

Claude 可编排多个 agent："Use @db-expert to optimize queries, then @security to audit the changes."

## Hooks —— 事件驱动的自动化

在 `.claude/settings.json`（项目）或 `~/.claude/settings.json`（全局）中配置：

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write(*.py)",
      "hooks": [{"type": "command", "command": "ruff check --fix $CLAUDE_FILE_PATHS"}]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -q 'rm -rf'; then echo 'Blocked!' && exit 2; fi"}]
    }],
    "Stop": [{
      "hooks": [{"type": "command", "command": "echo 'Claude finished a response' >> ~/.hermes/cache/scratch/claude-activity.log"}]
    }]
  }
}
```

### 全部 8 种 Hook 类型
| Hook | 触发时机 | 常见用途 |
|------|--------------|------------|
| `UserPromptSubmit` | Claude 处理用户提示之前 | 输入校验、日志 |
| `PreToolUse` | 工具执行之前 | 安全闸门、拦截危险命令（exit 2 = 拦截） |
| `PostToolUse` | 工具结束后 | 自动格式化代码、跑 linter |
| `Notification` | 权限请求或等待输入时 | 桌面通知、告警 |
| `Stop` | Claude 完成一次回复时 | 完成日志、状态更新 |
| `SubagentStop` | 子代理完成时 | agent 编排 |
| `PreCompact` | 上下文记忆被清空之前 | 备份会话转录 |
| `SessionStart` | 会话开始时 | 加载开发上下文（如 `git status`） |

### Hook 环境变量
| Variable | 内容 |
|----------|---------|
| `CLAUDE_PROJECT_DIR` | 当前项目路径 |
| `CLAUDE_FILE_PATHS` | 正在修改的文件 |
| `CLAUDE_TOOL_INPUT` | 工具参数（JSON） |

### 安全 Hook 示例
```json
{
  "PreToolUse": [{
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -qE 'rm -rf|git push.*--force|:(){ :|:& };:'; then echo 'Dangerous command blocked!' && exit 2; fi"}]
  }]
}
```

## MCP 集成

为数据库、API 与服务添加外部工具 server：

```
# GitHub integration
terminal(command="claude mcp add -s user github -- npx @modelcontextprotocol/server-github", timeout=30)

# PostgreSQL queries
terminal(command="claude mcp add -s local postgres -- npx @anthropic-ai/server-postgres --connection-string postgresql://localhost/mydb", timeout=30)

# Puppeteer for web testing
terminal(command="claude mcp add puppeteer -- npx @anthropic-ai/server-puppeteer", timeout=30)
```

### MCP 作用域
| Flag | 作用域 | 存储 |
|------|-------|---------|
| `-s user` | 全局（所有项目） | `~/.claude.json` |
| `-s local` | 本项目（个人） | `.claude/settings.local.json`（gitignored） |
| `-s project` | 本项目（团队共享） | `.claude/settings.json`（git-tracked） |

### Print/CI 模式下的 MCP
```
terminal(command="claude --bare -p 'Query database' --mcp-config mcp-servers.json --strict-mcp-config", timeout=60)
```
`--strict-mcp-config` 忽略除 `--mcp-config` 之外的所有 MCP server。

在聊天中引用 MCP 资源：`@github:issue://123`

### MCP 限制与调优
- **工具描述：** 每个 server 的工具描述与 server 指令上限 2KB
- **结果大小：** 默认有上限。用 `maxResultSizeChars` 注解可为大输出放宽到最多 **500K** 字符
- **输出 token：** `export MAX_MCP_OUTPUT_TOKENS=50000` —— 限制 MCP server 输出以防上下文被淹没
- **传输方式：** `stdio`（本地进程）、`http`（远程）、`sse`（server-sent events）

## 监控交互式会话

### 读取 TUI 状态
```
# Periodic capture to check if Claude is still working or waiting for input
terminal(command="tmux capture-pane -t dev -p -S -10")
```

留意这些指示符：
- 底部出现 `❯` = 正在等待你的输入（Claude 已完成或在提问）
- `●` 行 = Claude 正在积极使用工具（读取、写入、运行命令）
- `⏵⏵ bypass permissions on` = 状态栏显示权限模式
- `◐ medium · /effort` = 状态栏中的当前 effort 等级
- `ctrl+o to expand` = 工具输出被截断（可交互展开）

### 上下文窗口健康度
在交互模式下用 `/context` 查看上下文用量的彩色网格。关键阈值：
- **< 70%** —— 正常运行，完整精度
- **70-85%** —— 精度开始下降，考虑 `/compact`
- **> 85%** —— 幻觉风险显著飙升，使用 `/compact` 或 `/clear`

## 环境变量

| Variable | 作用 |
|----------|--------|
| `ANTHROPIC_API_KEY` | 用于认证的 API key（OAuth 的替代） |
| `CLAUDE_CODE_EFFORT_LEVEL` | 默认 effort：`low`、`medium`、`high`、`max` 或 `auto` |
| `MAX_THINKING_TOKENS` | 限制思考 token（设为 `0` 完全禁用思考） |
| `MAX_MCP_OUTPUT_TOKENS` | 限制 MCP server 输出（默认值不定。例如设为 `50000`） |
| `CLAUDE_CODE_NO_FLICKER=1` | 启用 alt-screen 渲染以消除终端闪烁 |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` | 出于安全从子进程中剥离凭证 |

## 成本与性能技巧

1. 在 print mode 中**用 `--max-turns`** 防止失控循环。多数任务从 5-10 起步。
2. **用 `--max-budget-usd`** 设成本上限。注意：系统提示缓存创建的最低费用约 $0.05。
3. 简单任务**用 `--effort low`**（更快更便宜）。复杂推理用 `high` 或 `max`。
4. CI/脚本**用 `--bare`** 跳过插件/hook 发现开销。
5. **用 `--allowedTools`** 只保留所需（如审查时只用 `Read`）。
6. 交互式会话中上下文变大时**用 `/compact`**。
7. 只需分析已知内容时，**用管道输入**而非让 Claude 读文件。
8. 简单任务**用 `--model haiku`**（更便宜），复杂多步工作用 `--model opus`。
9. print mode 中**用 `--fallback-model haiku`** 优雅处理模型过载。
10. **为不同任务开新会话** —— 会话持续 5 小时。全新上下文更高效。
11. CI 中**用 `--no-session-persistence`** 避免磁盘上累积保存的会话。

## 陷阱与坑

1. **交互模式必须用 tmux** —— Claude Code 是完整 TUI 应用。在 Hermes terminal 中单用 `pty=true` 也能work，但 tmux 提供用于监控的 `capture-pane` 和用于输入的 `send-keys`，这对编排至关重要。
2. **`--dangerously-skip-permissions` 警告对话框默认为「No, exit」** —— 该默认是安全答案。只有当你刻意在隔离环境中 opt-in bypass 时才发送 Down 再 Enter。Print mode（`-p`）完全跳过该对话框。
3. **`--max-budget-usd` 最低约 $0.05** —— 仅系统提示缓存创建就花这么多。设得更低会立即报错。
4. **`--max-turns` 仅限 print mode** —— 交互式会话中会被忽略。
5. **Claude 可能用 `python` 而非 `python`** —— 在没有 `python` symlink 的系统上，Claude 的 bash 命令首次会失败，但会自我纠正。
6. **会话恢复要求同一目录** —— `--continue` 查找当前工作目录最近一次会话。
7. **`--json-schema` 需要足够的 `--max-turns`** —— Claude 必须先读文件才能产出结构化输出，这需要多轮。
8. **信任对话框每个目录只出现一次** —— 仅首次，之后缓存。
9. **后台 tmux 会话会持续存在** —— 完成后务必用 `tmux kill-session -t <name>` 清理。
10. **斜杠命令（如 `/commit`）仅在交互模式可用** —— `-p` 模式下改以自然语言描述任务。
11. **`--bare` 跳过 OAuth** —— 需要 `ANTHROPIC_API_KEY` 环境变量或设置中的 `apiKeyHelper`。
12. **上下文退化是真实存在的** —— 上下文窗口使用超 70% 后 AI 输出质量可测地下降。用 `/context` 监控并主动 `/compact`。

## Hermes Agent 的规则

1. **单任务优先用 print mode（`-p`）** —— 更干净、无需处理对话框、结构化输出
2. **多轮交互工作用 tmux** —— 编排该 TUI 的唯一可靠方式
3. **始终设置 `workdir`** —— 让 Claude 专注于正确的项目目录
4. **print mode 中设置 `--max-turns`** —— 防止死循环与失控成本
5. **监控 tmux 会话** —— 用 `tmux capture-pane -t <session> -p -S -50` 检查进度
6. **留意 `❯` 提示符** —— 表示 Claude 在等待输入（已完成或在提问）
7. **清理 tmux 会话** —— 完成后杀掉以免资源泄漏
8. **向用户报告结果** —— 完成后总结 Claude 做了什么、改了什么
9. **不要杀掉慢会话** —— Claude 可能在做多步工作。改为检查进度
10. **用 `--allowedTools`** —— 把能力限制到任务真正所需
