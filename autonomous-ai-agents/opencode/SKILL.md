---
name: opencode
description: "把编程任务委派给 OpenCode CLI 时使用。只要要开 feature、审查 PR 或做重构，就主动加载，即使用户只说「用 OpenCode 干」或「让另一个编码代理跑」。不用于 Claude Code / Codex 专属流程。"
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, OpenCode, Autonomous, Refactoring, Code-Review]
    related_skills: [claude-code, codex, hermes-agent]
---

# OpenCode CLI

把 [OpenCode](https://opencode.ai) 当作由 Hermes terminal/process 工具编排的自主编码 worker。OpenCode 是 provider 无关的开源 AI 编码代理，带 TUI 与 CLI。

## 何时使用

- 用户明确要求使用 OpenCode
- 想让外部编码代理实现/重构/审查代码
- 需要带进度检查的长时编码会话
- 想在隔离 workdir/worktree 中并行执行任务

## 前置条件

- 已安装 OpenCode：`npm i -g opencode-ai@latest` 或 `brew install anomalyco/tap/opencode`
- 已配置认证：`opencode auth login` 或设置 provider 环境变量（OPENROUTER_API_KEY 等）
- 验证：`opencode auth list` 应至少显示一个 provider
- 代码任务需 git 仓库（推荐）
- 交互式 TUI 会话用 `pty=true`

## 二进制解析（重要）

不同 shell 环境可能解析到不同的 OpenCode 二进制。若在你自己的终端与 Hermes 中行为不同，检查：

```
terminal(command="which -a opencode")
terminal(command="opencode --version")
```

如有需要，固定显式二进制路径：

```
terminal(command="$HOME/.opencode/bin/opencode run '...'", workdir="~/project", pty=true)
```

## 一次性任务

对边界明确、非交互的任务用 `opencode run`：

```
terminal(command="opencode run 'Add retry logic to API calls and update tests'", workdir="~/project")
```

用 `-f` 附加上下文文件：

```
terminal(command="opencode run 'Review this config for security issues' -f config.yaml -f .env.example", workdir="~/project")
```

用 `--thinking` 显示模型思考：

```
terminal(command="opencode run 'Debug why tests fail in CI' --thinking", workdir="~/project")
```

强制指定模型：

```
terminal(command="opencode run 'Refactor auth module' --model openrouter/anthropic/claude-sonnet-4", workdir="~/project")
```

## 交互式会话（后台）

对需要多轮往来的迭代工作，在后台启动 TUI：

```
terminal(command="opencode", workdir="~/project", background=true, pty=true)
# Returns session_id

# Send a prompt
process(action="submit", session_id="<id>", data="Implement OAuth refresh flow and add tests")

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send follow-up input
process(action="submit", session_id="<id>", data="Now add error handling for token expiry")

# Exit cleanly — Ctrl+C
process(action="write", session_id="<id>", data="\x03")
# Or just kill the process
process(action="kill", session_id="<id>")
```

**重要：** 不要用 `/exit` —— 它不是合法的 OpenCode 命令，会打开 agent 选择器对话框。改用 Ctrl+C（`\x03`）或 `process(action="kill")` 退出。

### TUI 按键绑定

| Key | 操作 |
|-----|--------|
| `Enter` | 提交消息（必要时按两次） |
| `Tab` | 在 agent 间切换（build/plan） |
| `Ctrl+P` | 打开命令面板 |
| `Ctrl+X L` | 切换会话 |
| `Ctrl+X M` | 切换模型 |
| `Ctrl+X N` | 新建会话 |
| `Ctrl+X E` | 打开编辑器 |
| `Ctrl+C` | 退出 OpenCode |

### 恢复会话

退出后，OpenCode 会打印一个 session ID。恢复方式：

```
terminal(command="opencode -c", workdir="~/project", background=true, pty=true)  # Continue last session
terminal(command="opencode -s ses_abc123", workdir="~/project", background=true, pty=true)  # Specific session
```

## 常用 Flags

| Flag | 用途 |
|------|-----|
| `run 'prompt'` | 一次性执行并退出 |
| `--continue` / `-c` | 继续最近一次 OpenCode 会话 |
| `--session <id>` / `-s` | 继续指定会话 |
| `--agent <name>` | 选择 OpenCode agent（build 或 plan） |
| `--model provider/model` | 强制指定模型 |
| `--format json` | 机器可读的输出/事件 |
| `--file <path>` / `-f` | 向消息附加文件 |
| `--thinking` | 显示模型思考块 |
| `--variant <level>` | 推理 effort（high、max、minimal） |
| `--title <name>` | 为会话命名 |
| `--attach <url>` | 连接到运行中的 opencode server |

## 流程

1. 验证工具就绪：
   - `terminal(command="opencode --version")`
   - `terminal(command="opencode auth list")`
2. 边界明确的任务用 `opencode run '...'`（无需 pty）。
3. 迭代任务以 `background=true, pty=true` 启动 `opencode`。
4. 用 `process(action="poll"|"log")` 监控长任务。
5. 若 OpenCode 请求输入，通过 `process(action="submit", ...)` 回应。
6. 用 `process(action="write", data="\x03")` 或 `process(action="kill")` 退出。
7. 向用户总结文件改动、测试结果与后续步骤。

## PR 审查工作流

OpenCode 内置 PR 命令：

```
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

或在临时克隆中审查以隔离：

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && opencode run 'Review this PR vs main. Report bugs, security risks, test gaps, and style issues.' -f $(git diff origin/main --name-only | head -20 | tr '\n' ' ')", pty=true)
```

## 并行工作模式

使用各自独立的 workdir/worktree 避免冲突：

```
terminal(command="opencode run 'Fix issue #101 and commit'", workdir="~/.hermes/cache/scratch/issue-101", background=true, pty=true)
terminal(command="opencode run 'Add parser regression tests and commit'", workdir="~/.hermes/cache/scratch/issue-102", background=true, pty=true)
process(action="list")
```

## 会话与成本管理

列出过往会话：

```
terminal(command="opencode session list")
```

查看 token 用量与成本：

```
terminal(command="opencode stats")
terminal(command="opencode stats --days 7 --models anthropic/claude-sonnet-4")
```

## 陷阱

- 交互式 `opencode`（TUI）会话需要 `pty=true`。`opencode run` 命令不需要 pty。
- `/exit` 不是合法命令 —— 它会打开 agent 选择器。用 Ctrl+C 退出 TUI。
- PATH 不一致可能选中错误的 OpenCode 二进制/模型配置。
- 若 OpenCode 看似卡住，杀之前先查看日志：
  - `process(action="log", session_id="<id>")`
- 避免多个并行 OpenCode 会话共用一个工作目录。
- 在 TUI 中提交可能需按两次 Enter（一次定稿文本，一次发送）。

## 验证

冒烟测试：

```
terminal(command="opencode run 'Respond with exactly: OPENCODE_SMOKE_OK'")
```

成功标准：
- 输出包含 `OPENCODE_SMOKE_OK`
- 命令退出无 provider/model 错误
- 代码任务：预期文件已改且测试通过

## 规则

1. 一次性自动化优先用 `opencode run` —— 更简单且不需要 pty。
2. 仅在需要迭代时使用交互式后台模式。
3. 始终把 OpenCode 会话限定在单个 repo/workdir。
4. 长任务时，从 `process` 日志给出进度更新。
5. 报告具体结果（改动的文件、测试、剩余风险）。
6. 用 Ctrl+C 或 kill 退出交互式会话，绝不用 `/exit`。
