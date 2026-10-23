---
name: python-debugpy
description: "调试 Python 时使用：pdb REPL、debugpy 远程（DAP）。只要要设断点、单步、事后剖析（post-mortem）或附着到运行中的进程，就主动加载，即使用户没明说 pdb。print 不够用时上。"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [debugging, python, pdb, debugpy, breakpoints, dap, post-mortem]
    related_skills: [systematic-debugging, node-inspect-debugger]
---

# Python 调试器（pdb + debugpy）

## Overview（概览）

三个工具，按情形挑：

| Tool | 何时用 |
|---|---|
| **`breakpoint()` + pdb** | 本地、交互、最简单。源码里加 `breakpoint()`，正常跑，就在那一行拿到 REPL。 |
| **`python -m pdb`** | 不改源码，把已有脚本放进 pdb 跑。适合快速戳一戳。 |
| **`debugpy`** | 远程 / 无头 / "附着到已在运行的进程。" 说 DAP，可从终端脚本化，适配长命进程（gateway、daemon、PTY 子进程）。 |

**从 `breakpoint()` 开始。** 它是最便宜的、能用的办法。

## When to Use（何时用）

- 测试失败，而 traceback 没揭示为什么某个值不对
- 你要单步走一个函数、看着某个集合在变化
- 长命进程（hermes gateway、tui_gateway）行为异常、又没法重启
- 事后剖析：近生产代码里抛了异常，你想在崩溃点检查局部变量
- 某个子进程 / 子级（Python `_SlashWorker`、PTY 桥接 worker）才是真正的 bug 现场

**不用于：** `print()` / `logging.debug` 一分钟内能解决的事，或 `pytest -vv --tb=long --showlocals` 已经揭示的事。

## pdb Quick Reference（速查）

在任何 pdb 提示符（`(Pdb)`）里：

| 命令 | 动作 |
|---|---|
| `h` / `h cmd` | 帮助 |
| `n` | 下一行（step over） |
| `s` | 步入（step into） |
| `r` | 从当前函数返回 |
| `c` | 继续 |
| `unt N` | 继续直到第 N 行 |
| `j N` | 跳到第 N 行（仅同一函数内） |
| `l` / `ll` | 列出当前行附近 / 整个函数的源码 |
| `w` | where（栈回溯） |
| `u` / `d` | 在栈里上移 / 下移 |
| `a` | 打印当前函数的参数 |
| `p expr` / `pp expr` | 打印 / 美化打印表达式 |
| `display expr` | 每次停下自动打印 expr |
| `b file:line` | 设断点 |
| `b func` | 函数入口处断住 |
| `b file:line, cond` | 条件断点 |
| `cl N` | 清除断点 N |
| `tbreak file:line` | 一次性断点 |
| `!stmt` | 执行任意 Python（含赋值） |
| `interact` | 在当前作用域落入完整 Python REPL（Ctrl+D 退出） |
| `q` | 退出 |

`interact` 命令最强——你可以 import 任何东西、检视复杂对象，甚至调用会改状态的方法。局部变量默认只读；在 `(Pdb)` 提示符里用 `!x = 42` 去改。

## Recipe 1: Local breakpoint（本地断点）

最省事。编辑文件：

```python
def compute(x, y):
    result = some_helper(x)
    breakpoint()           # <-- drops into pdb here
    return result + y
```

正常跑代码。你会落在 `breakpoint()` 那一行，且能完整访问局部变量。

**别忘在提交前删掉 `breakpoint()`。** 用 `git diff`，或加个 pre-commit grep：
```bash
rg -n 'breakpoint\(\)' --type py
```

## Recipe 2: Launch a script under pdb（不改源码，把脚本放进 pdb 跑）

```bash
python -m pdb path/to/script.py arg1 arg2
# Lands at first line of script
(Pdb) b path/to/script.py:42
(Pdb) c
```

## Recipe 3: Debug a pytest test（调试一个 pytest 测试）

非交互诊断用 `terminal` 和标准 runner：

```bash
# Show locals in tracebacks without pdb:
scripts/run_tests.sh tests/path/to/test_file.py --showlocals --tb=long
```

`scripts/run_tests.sh` 把每个文件放进独立子进程捕获输出，所以 `--pdb` 或 `--trace` 在那儿给不出交互提示符。要交互式调试器，只能用 Recipe 5 里准备好的独立开发/测试解释器（绝不用生产代际）：

```bash
.venv/bin/python -m pytest tests/foo_test.py::test_bar --pdb
```

这会绕过 hermetic-env 的保证——调试无妨，但 push 前要在 wrapper 下重跑确认。

## Recipe 4: Post-mortem on any exception（对任意异常做事后剖析）

```python
import pdb, sys
try:
    run_the_thing()
except Exception:
    pdb.post_mortem(sys.exc_info()[2])
```

或者包住整个脚本：

```bash
python -m pdb -c continue script.py
# When it crashes, pdb catches it and you're in the frame of the exception
```

或者在 repl/jupyter 里设一个全局钩子：

```python
import sys
def excepthook(etype, value, tb):
    import pdb; pdb.post_mortem(tb)
sys.excepthook = excepthook
```

## Recipe 5: Remote debug with debugpy（远程调试，附着到运行中的进程）

用于长命进程：Hermes gateway、tui_gateway、某个 daemon、或一个已经行为异常又没法干净重启的进程。

### Setup（准备）

对 Hermes，用一个独立的开发检出与数据 home，不要用活的生产代际。照
[PM 开发工作流](https://hermes-agent.nousresearch.com/docs/reference/package-management#developer-workflow)
做，并激活那个检出——PowerShell：`. .\activate.ps1`。声明的 `dev` extra 含 debugpy，而 PM 激活不会同步它（`all` 把它排除在外）。通过 `terminal`，用准备好的检出里的 Python 构建一个全新的、调用方自有的调试/测试环境：

```bash
source ./activate
python -m pm.build_env --source . --out .venv --group dev --group test
.venv/bin/python -c "import debugpy; print(debugpy.__file__)"
```

该输出路径必须尚不存在。重建前先停掉它的进程，并且只删掉那个一次性环境。调试目标沿用同一个隔离的 `HERMES_HOME`。`.venv/bin/python` 是这个显式构建的调试环境，不是猜出来的应用 venv，下面的套路都经它运行。不要往正在跑的生产环境里加 debugpy；在那儿复现只能用已准备好的调试目标，或在开发环境里安排一次重启。

### Pattern A: Source-edit — process waits for debugger at launch（改源码——进程启动时等调试器）

在入口点顶部附近（或你想调试的函数内部）加上：

```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
print("debugpy listening on 5678, waiting for client...", flush=True)
debugpy.wait_for_client()
debugpy.breakpoint()       # optional: pause immediately once attached
```

启动该进程；它会阻塞在 `wait_for_client()`。

### Pattern B: No source edit — launch with `-m debugpy`（不改源码——用 `-m debugpy` 启动）

```bash
.venv/bin/python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py arg1
```

模块入口的等价写法：

```bash
.venv/bin/python -m debugpy --listen 127.0.0.1:5678 --wait-for-client -m your.module
```

### Pattern C: Attach to an already-running process（附着到已在运行的进程）

需要 PID，且目标环境里预装了 debugpy：

```bash
.venv/bin/python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
# debugpy injects itself into the process. Then attach a client as below.
```

某些内核/安全配置会挡住基于 ptrace 的注入（`/proc/sys/kernel/yama/ptrace_scope`）。修复办法：
```bash
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
```

### Connecting a client from the terminal（从终端连客户端）

最省事的终端侧 DAP 客户端是 VS Code CLI，或一个小脚本。在 Hermes 内有两条务实之选：

**Option 1: `debugpy` 自带的 CLI REPL** —— 不是官方特性，但一个小巧的 DAP 客户端脚本：

```python
# ~/.hermes/cache/scratch/dap_client.py
import socket, json, itertools, time, sys

HOST, PORT = "127.0.0.1", 5678
s = socket.create_connection((HOST, PORT))
seq = itertools.count(1)

def send(msg):
    msg["seq"] = next(seq)
    body = json.dumps(msg).encode()
    s.sendall(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)

def recv():
    header = b""
    while b"\r\n\r\n" not in header:
        header += s.recv(1)
    length = int(header.decode().split("Content-Length:")[1].split("\r\n")[0].strip())
    body = b""
    while len(body) < length:
        body += s.recv(length - len(body))
    return json.loads(body)

send({"type": "request", "command": "initialize", "arguments": {"adapterID": "python"}})
print(recv())
send({"type": "request", "command": "attach", "arguments": {}})
print(recv())
send({"type": "request", "command": "setBreakpoints",
      "arguments": {"source": {"path": sys.argv[1]},
                    "breakpoints": [{"line": int(sys.argv[2])}]}})
print(recv())
send({"type": "request", "command": "configurationDone"})
# ... loop reading events and sending continue/stepIn/etc.
```

一次性自动化没问题，但作为交互式 UX 很痛苦。

**Option 2: 从 VS Code / Cursor / Zed 附着** —— 用户若开着其中之一，可以加个 `launch.json`：

```json
{
  "name": "Attach to Hermes",
  "type": "debugpy",
  "request": "attach",
  "connect": { "host": "127.0.0.1", "port": 5678 },
  "justMyCode": false,
  "pathMappings": [
    { "localRoot": "${workspaceFolder}", "remoteRoot": "<hermes-agent-repo>" }
  ]
}
```

**Option 3: 干脆不用 DAP，改用 `remote-pdb`** —— 通常这才是终端 agent 真正想要的：

对一个独立自有的 Python 项目，在那个项目的开发依赖里声明 `remote-pdb`，并经该项目的包管理器准备其调试环境。这不是 Hermes SDK 的安装配方。对 Hermes，优先用已声明的 debugpy 依赖；下面的 remote-pdb 例子需要一个单独声明、全新构建的调试环境，绝不是在选定应用代际里就地进行 pip 安装。

在你的代码里：
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)   # blocks until connection
```

然后从终端：
```bash
nc 127.0.0.1 4444
# You get a (Pdb) prompt exactly as if debugging locally.
```

当 `debugpy` 的 DAP 协议是杀鸡用牛刀时，`remote-pdb` 是最干净的、对 agent 友好的选择。只有当你确实需要 IDE 集成时才用 `debugpy`。

## Debugging Hermes-specific Processes（调试 Hermes 专属进程）

### Tests
见 Recipe 3。wrapper 会捕获子进程输出，所以要做交互式 pdb 就直接跑 pytest。

### `run_agent.py` / CLI —— 一次性
在准备好的调试检出里，在可疑行附近加 `breakpoint()`，然后跑 `python hermes`。到暂停点，控制权回到你的终端。

### `tui_gateway` 子进程（由 `hermes --tui` spawn）
gateway 作为 Node TUI 的子进程运行。选项：

**A. 改 gateway 源码：**
```python
# tui_gateway/server.py near the top of serve()
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()
```
从准备好的调试检出里启动 `python hermes --tui`。TUI 会看起来冻住（它的后端在等）。连一个客户端；你 `continue` 时执行恢复。在假定子进程继承了调试环境之前，先核实它的解释器与 import。

**B. 在某个具体 handler 用 `remote-pdb`：**
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)   # in the RPC handler you want to trap
```
从 TUI 触发对应的 slash 命令，然后在另一个终端 `nc 127.0.0.1 4444`。

### `_SlashWorker` 子进程
同样的套路——在 worker 的 `exec` 路径里用 `remote-pdb` 配 `set_trace()`。worker 跨 slash 命令是持久的，所以第一次触发会阻塞到你连上；后续 slash 命令正常通过，除非你重新布点。

### Gateway (`gateway/run.py`)
长命。在某个 handler 用 `remote-pdb`，或者既然你本来就要重启 gateway，就用带 `--wait-for-client` 的 `debugpy`。

## Common Pitfalls（常见坑）

1. **在并行/捕获输出的 runner 下 pdb 会静默失效。** 你看不到提示符，测试就那么卡住（pytest-xdist 和 `scripts/run_tests.sh` 的逐文件捕获子进程都如此）。要交互调试，就在单个文件上直接跑 pytest。

2. **CI / 非 TTY 环境里的 `breakpoint()` 会卡住进程。** 本地安全；但绝不能提交它。加个 pre-commit grep 当兜底。

3. **`PYTHONBREAKPOINT=0`** 会禁用所有 `breakpoint()` 调用。断点没命中时先查这个环境变量：
   ```bash
   echo $PYTHONBREAKPOINT
   ```

4. **只有同时调用 `wait_for_client()` 时 `debugpy.listen` 才会阻塞。** 不调它，执行会继续，你的第一个断点可能在客户端连上之前就触发了。

5. **在加固过的内核上附着 PID 会失败。** `ptrace_scope=1`（Ubuntu 默认）只允许同一用户对子进程做 ptrace。变通：`echo 0 > /proc/sys/kernel/yama/ptrace_scope`（需要 root），或一开始就带 `debugpy` 启动。

6. **线程。** `pdb` 只调试当前线程。多线程代码用 `debugpy`（线程感知的 DAP），或逐线程设 `threading.settrace()`。

7. **asyncio。** `pdb` 在协程里能用，但 pdb 里 `await` 需要 Python 3.13+，旧版本要从 `interact` 模式里 `await`。3.11/3.12 下用 `asyncio.run_coroutine_threadsafe` 之类技巧，或经 `asyncio.ensure_future` 用 `!stmt` 式 await。

8. **`scripts/run_tests.sh` 会剥离凭据并设 `HOME=<tmpdir>`。** 若你的 bug 依赖用户配置或真实 API key，在 wrapper 下复现不出来。先直接用裸 `pytest` 复现，再回 wrapper 下确认。

9. **Forking / multiprocessing。** pdb 不跟随 fork。每个子进程都要有自己的 `breakpoint()` 或 `set_trace()`。对 Hermes 子代理，一次只调一个进程。

## Verification Checklist（验证清单）

- [ ] 在独立构建的调试环境里确认：`.venv/bin/python -c "import debugpy; print(debugpy.__version__); print(debugpy.__file__)"`
- [ ] 远程调试时，确认端口确实在监听：`ss -tlnp | grep 5678`
- [ ] 第一个断点真的命中（没命中，多半是 `PYTHONBREAKPOINT=0`、你处在并行/捕获输出的 runner 下、或附着前执行已经结束）
- [ ] `where` / `w` 显示的调用栈符合预期
- [ ] 调试后清理：已提交的代码里没有残留的 `breakpoint()` / `set_trace()`
  ```bash
  rg -n 'breakpoint\(\)|set_trace\(|debugpy\.listen' --type py
  ```

## One-Shot Recipes（一次性配方）

**"这个 dict 为什么少了一个 key？"**
```python
# add above the KeyError site
breakpoint()
# then in pdb:
(Pdb) pp d
(Pdb) pp list(d.keys())
(Pdb) w                # how did we get here
```

**"这个测试单独跑通过，进套件就失败。"**
```bash
scripts/run_tests.sh tests/the_test.py   # confirm it fails under the isolated runner first
# For interactive debugging, or if it only fails WITH other tests, use the
# independent development/test interpreter prepared in Recipe 5:
.venv/bin/python -m pytest tests/ -x --pdb
# Now it pdb-traps at the exact failing test after state accumulated.
```

**"我的 async handler 死锁了。"**
```python
# Add at handler entry
import remote_pdb; remote_pdb.set_trace(host="127.0.0.1", port=4444)
```
触发该 handler。`nc 127.0.0.1 4444`，然后 `w` 看被挂起的帧，`!import asyncio; asyncio.all_tasks()` 看还有什么在待决。

**"对 Ink 子进程 / 子进程里的崩溃做事后剖析。"**
```bash
PYTHONFAULTHANDLER=1 python -m pdb -c continue path/to/entrypoint.py
# On crash, pdb lands at the frame of the exception with full locals
```
