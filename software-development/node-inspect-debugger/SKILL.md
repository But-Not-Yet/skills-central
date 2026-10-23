---
name: node-inspect-debugger
description: "用 --inspect 加 CDP 从命令行调试 Node.js 时使用。只要要让 runtime 断点、单步、走调用栈或读闭包变量（console.log 不够时），就主动加载，即使用户没明说 --inspect。"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, nodejs, node-inspect, cdp, breakpoints, ui-tui]
    related_skills: [systematic-debugging, python-debugpy]
---

# Node.js Inspect 调试器

## Overview（概览）

当 `console.log` 不够用时，从终端以编程方式驱动 Node 内置的 V8 inspector。你能拿到真正的断点、step in/over/out、走调用栈、dump 局部/闭包作用域，以及在暂停帧里求任意表达式的值。

两个工具，选一个：

- **`node inspect`** — 内置、零安装、CLI REPL。适合快速戳一戳。
- **`ndb` / 经 `chrome-remote-interface` 走 CDP** — 可从 Node/Python 脚本化。适合要自动化大量断点、跨多次运行收集状态，或从 agent 循环里非交互调试的场合。

**优先用 `node inspect`。** 它永远可用，且 REPL 很快。

## When to Use（何时用）

- 一个 Node 测试失败，你要看中间状态
- ui-tui 崩溃或行为不对，你想在渲染前检查 React/Ink 状态
- tui_gateway 子进程（`_SlashWorker`、PTY 桥接 worker）行为异常
- 你要检查闭包里的某个值，`console.log` 不打补丁够不着
- 性能：附着到运行中的进程抓 CPU profile 或堆快照

**不用于：** `console.log` 一分钟内能解决的事。断点驱动的调试更重。有实打实收益时才用。

## Quick Reference: `node inspect` REPL（速查）

在首行暂停启动：

```bash
node inspect path/to/script.js
# or with tsx
node --inspect-brk $(which tsx) path/to/script.ts
```

`debug>` 提示符接受：

| 命令 | 动作 |
|---|---|
| `c` or `cont` | 继续 |
| `n` or `next` | 单步跳过（step over） |
| `s` or `step` | 单步进入（step into） |
| `o` or `out` | 单步跳出（step out） |
| `pause` | 暂停运行中的代码 |
| `sb('file.js', 42)` | 在 file.js 第 42 行设断点 |
| `sb(42)` | 在当前文件第 42 行设断点 |
| `sb('functionName')` | 函数被调用时断住 |
| `cb('file.js', 42)` | 清除断点 |
| `breakpoints` | 列出所有断点 |
| `bt` | 回溯（调用栈） |
| `list(5)` | 显示当前位置附近 5 行源码 |
| `watch('expr')` | 每次暂停时求 expr 的值 |
| `watchers` | 显示被监视的表达式 |
| `repl` | 在当前作用域进入 REPL（Ctrl+C 退出 REPL） |
| `exec expr` | 求一次表达式的值 |
| `restart` | 重启脚本 |
| `kill` | 杀掉脚本 |
| `.exit` | 退出调试器 |

**在 `repl` 子模式下：** 输入任意 JS 表达式，包括访问局部/闭包变量。`Ctrl+C` 退回 `debug>`。

## Attaching to a Running Process（附着到运行中的进程）

当进程已经在跑时（例如一个长期存活的 dev server 或 TUI gateway）：

```bash
# 1. Send SIGUSR1 to enable the inspector on an existing process
kill -SIGUSR1 <pid>
# Node prints: Debugger listening on ws://127.0.0.1:9229/<uuid>

# 2. Attach the debugger CLI
node inspect -p <pid>
# or by URL
node inspect ws://127.0.0.1:9229/<uuid>
```

要让进程一开始就带着 inspector 启动：

```bash
node --inspect script.js           # listen on 127.0.0.1:9229, keep running
node --inspect-brk script.js       # listen AND pause on first line
node --inspect=0.0.0.0:9230 script.js   # custom host:port
```

经 tsx 跑 TypeScript 时：

```bash
node --inspect-brk --import tsx script.ts
# or older tsx
node --inspect-brk -r tsx/cjs script.ts
```

## Programmatic CDP（从终端脚本化）

当你想自动化——设很多断点、抓作用域状态、脚本化一个复现——就用 `chrome-remote-interface`：

```bash
npm i -g chrome-remote-interface        # or project-local
# Start your target:
node --inspect-brk=9229 target.js &
```

驱动脚本（存为 `~/.hermes/cache/scratch/cdp-debug.js`）：

```javascript
const CDP = require('chrome-remote-interface');

(async () => {
  const client = await CDP({ port: 9229 });
  const { Debugger, Runtime } = client;

  Debugger.paused(async ({ callFrames, reason }) => {
    const top = callFrames[0];
    console.log(`PAUSED: ${reason} @ ${top.url}:${top.location.lineNumber + 1}`);

    // Walk scopes for locals
    for (const scope of top.scopeChain) {
      if (scope.type === 'local' || scope.type === 'closure') {
        const { result } = await Runtime.getProperties({
          objectId: scope.object.objectId,
          ownProperties: true,
        });
        for (const p of result) {
          console.log(`  ${scope.type}.${p.name} =`, p.value?.value ?? p.value?.description);
        }
      }
    }

    // Evaluate an expression in the paused frame
    const { result } = await Debugger.evaluateOnCallFrame({
      callFrameId: top.callFrameId,
      expression: 'typeof state !== "undefined" ? JSON.stringify(state) : "n/a"',
    });
    console.log('state =', result.value ?? result.description);

    await Debugger.resume();
  });

  await Runtime.enable();
  await Debugger.enable();

  // Set a breakpoint by URL regex + line
  await Debugger.setBreakpointByUrl({
    urlRegex: '.*app\\.tsx$',
    lineNumber: 119,       // 0-indexed
    columnNumber: 0,
  });

  await Runtime.runIfWaitingForDebugger();
})();
```

运行它：

```bash
node ~/.hermes/cache/scratch/cdp-debug.js
```

Hermes 专属注意：`chrome-remote-interface` **不在** `ui-tui/package.json` 里。不想弄脏项目的话，装到一个一次性位置：

```bash
mkdir -p ~/.hermes/cache/scratch/cdp-tools && cd ~/.hermes/cache/scratch/cdp-tools && npm i chrome-remote-interface
NODE_PATH=~/.hermes/cache/scratch/cdp-tools/node_modules node ~/.hermes/cache/scratch/cdp-debug.js
```

## Debugging Hermes ui-tui（调试 Hermes ui-tui）

TUI 是 Ink + tsx 构建的。两个常见场景：

### 在 dev 下调试单个 Ink 组件

`ui-tui/package.json` 有 `npm run dev`（tsx --watch）。直接跑 tsx 就能加上 `--inspect-brk`：

```bash
cd <hermes-agent-repo>/ui-tui
npm run build    # produce dist/ once so transpile isn't needed on first load
node --inspect-brk dist/entry.js
# In another terminal:
node inspect -p <node pid>
```

然后在 `debug>` 里：

```
sb('dist/app.js', 220)     # or wherever the suspect render is
cont
```

它暂停时，`repl` → 检查 `props`、state refs、`useInput` handler 的值等。

### 调试运行中的 `hermes --tui`

TUI 是从 Python CLI 里 spawn 出 Node 的。最省事的路径：

```bash
# 1. Launch TUI
hermes --tui &
TUI_PID=$(pgrep -f 'ui-tui/dist/entry' | head -1)

# 2. Enable inspector on that Node PID
kill -SIGUSR1 "$TUI_PID"

# 3. Find the WS URL
curl -s http://127.0.0.1:9229/json/list | jq -r '.[0].webSocketDebuggerUrl'

# 4. Attach
node inspect ws://127.0.0.1:9229/<uuid>
```

与 TUI 交互（在它窗口里打字）会继续推进执行。你的调试器可以在任意 `sb(...)` 断点处把它暂停。

### 调试 `_SlashWorker` / PTY 子进程

那些是 Python 不是 Node——用 `python-debugpy` 技能。只有 Node 部分（Ink UI、tui_gateway 客户端、`ui-tui/` 下 tsx 跑的测试）用本技能。

## Running Vitest Tests Under the Debugger（在调试器下跑 Vitest 测试）

```bash
cd <hermes-agent-repo>/ui-tui
# Run a single test file paused on entry
node --inspect-brk ./node_modules/vitest/vitest.mjs run --no-file-parallelism src/app/foo.test.tsx
```

在另一个终端：`node inspect -p <pid>`，然后 `sb('src/app/foo.tsx', 42)`、`cont`。

用 `--no-file-parallelism`（vitest）或 `--runInBand`（jest），只留一个 worker——调试一整个 worker 池很痛苦。

## Heap Snapshots & CPU Profiles (Non-interactive)（堆快照与 CPU profile，非交互）

从上面那个 CDP 驱动脚本出发，把 Debugger 换成 `HeapProfiler` / `Profiler`：

```javascript
// CPU profile for 5 seconds
await client.Profiler.enable();
await client.Profiler.start();
await new Promise(r => setTimeout(r, 5000));
const { profile } = await client.Profiler.stop();
require('fs').writeFileSync('~/.hermes/cache/scratch/cpu.cpuprofile', JSON.stringify(profile));
// Open ~/.hermes/cache/scratch/cpu.cpuprofile in Chrome DevTools → Performance tab
```

```javascript
// Heap snapshot
await client.HeapProfiler.enable();
const chunks = [];
client.HeapProfiler.addHeapSnapshotChunk(({ chunk }) => chunks.push(chunk));
await client.HeapProfiler.takeHeapSnapshot({ reportProgress: false });
require('fs').writeFileSync('~/.hermes/cache/scratch/heap.heapsnapshot', chunks.join(''));
```

## Common Pitfalls（常见坑）

1. **TS 源码里的行号对不上。** 断点命中的是产出的 JS，不是 `.ts`。要么 (a) 在构建出的 `dist/*.js` 里断，要么 (b) 启用 sourcemap（`node --enable-source-maps`）再用 `sb('src/app.tsx', N)`。但只在会跟随 sourcemap 的 CDP 客户端里有用，`node inspect` CLI 不跟随。

2. **`--inspect` vs `--inspect-brk`。** `--inspect` 会启动 inspector 但不暂停。附着得太晚，脚本就冲过了你的第一个断点。需要在任何代码跑起来之前设断点时，用 `--inspect-brk`。

3. **端口冲突。** 默认是 `9229`。若有多个 Node 进程在做 inspect，传 `--inspect=0`（随机端口），再从 `/json/list` 读出实际 URL：
   ```bash
   curl -s http://127.0.0.1:9229/json/list   # lists all inspectable targets on the host
   ```

4. **子进程。** 在父进程上开 `--inspect` **不会** inspect 它的子进程。用 `NODE_OPTIONS='--inspect-brk' node parent.js` 传播给每个子进程。注意它们各自需要唯一端口（`NODE_OPTIONS='--inspect'` 被继承时 Node 会自动递增端口）。

5. **后台被杀。** 若在目标暂停时用 `Ctrl+C` 退出 `node inspect`，目标会一直保持暂停。要么先 `cont`，要么显式 `kill` 掉目标。

6. **经 agent 终端跑 `node inspect`。** 它是个 PTY 友好的 REPL。在 Hermes 里用 `terminal(pty=true)` 启动，或 `background=true` + `process(action='submit', data='...')`。非 PTY 前台模式能跑一次性命令，但做不了交互式单步。

7. **安全。** `--inspect=0.0.0.0:9229` 等于暴露任意代码执行。除非有隔离网络，否则始终绑 `127.0.0.1`（默认）。

## Verification Checklist（验证清单）

搭好调试会话后，核验：

- [ ] `curl -s http://127.0.0.1:9229/json/list` 恰好返回你期望的那个 target
- [ ] 第一个断点真的命中了（没命中，多半是漏了 `--inspect-brk` 或在执行完成后才附着）
- [ ] 暂停时的源码列表显示的是对的文件（对不上 = sourcemap 问题，见坑 1）
- [ ] 在 `repl` 里 `exec process.pid` 返回的是你想附着的那个 PID

## One-Shot Recipes（一次性配方）

**"这个变量为什么在第 X 行是 undefined？"**
```bash
node --inspect-brk script.js &
node inspect -p $!
# debug>
sb('script.js', X)
cont
# paused. Now:
repl
> myVariable
> Object.keys(this)
```

**"进这个函数的调用路径是什么？"**
```
debug> sb('suspectFn')
debug> cont
# paused on entry
debug> bt
```

**"这条 async 链卡住了——卡在哪？"**
```
# Start with --inspect (no -brk), let it run to the hang, then:
debug> pause
debug> bt
# Now you see the stuck frame
```
