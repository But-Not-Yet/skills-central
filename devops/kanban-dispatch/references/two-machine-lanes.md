# 两机两线编排模板

## When to Use

主 serving + 远端节点同时派活，或要把剩余任务拆成两条低交叉线时。

## 分线表

| 线 | 机器 | 模型 | 任务类型 | 文件所有权 | 顺序 |
|---|---|---|---|---|---|
| A | 主 serving | 强模型 | 核心实现、状态机、租约、硬拦 | 核心源码目录 | 重活链，线内串行 |
| B | 远端节点 | 弱/小模型 | 回归 fixtures、文档、脚本、旧卡处置、只读分析 | tests/regression、docs、scripts、看板控制 | 轻活链，线内串行 |

## 派卡

1. 先按难度分：远端只接机械可验、读多于写、或产物格式可逐列核的卡。远端卡体写全绝对路径、输入输出格式、禁止项、回退条款。
2. 逐卡 `set-model <id> <model> --provider <p>`；`set-model` 只对下一次 dispatch 生效。批量设完 `list --json` 回读 `model_override/provider_override`。
3. 顺序用父边锁：`kanban_link <parent> <child>`；CLI 用位置参数 `hermes kanban --board <slug> link <parent> <child>`（`--parent/--child` 会被拒）。`blocked` 不会自动解锁，`todo` 才会在父卡 done 后自动 promote；要排队就先 link 再 unblock，父卡已 done 时 unblock 可能立刻 promote+dispatch。
4. 同仓库并行前先确认文件锁已接进派发器；模块+CLI+单测全绿不等于 dispatcher 会调用它。没接之前同仓库只跑一张。
5. 不因槽位空着硬塞：依赖未到、或第二张要进同一仓库且文件锁未接线时，宁可空着。

## 进度与卡死判断

- 心跳和 `runs` 只证明 worker 活着；代码写入型还要看 workspace 文件 mtime/新增测试。
- `find <workspace> -newermt '<time>' -type f` 连续出现新文件 = 在写；日志只有 `Session:` 不代表卡死。
- 连续 10 分钟无新写入、无新事件，再按卡死处理：先 `show`/`runs`/`ps`，再 `reclaim`；不要先杀可能正在提交的 worker。
- 主会话每轮回答前重新取 `date` 和 `list --json`；旧快照不能当现行。

## 验收

- A/B 两线的产物文件不相交；跨线只读不写。
- worker 自报测试要在有依赖的解释器里复跑；全量套件的既有失败要基线比对。
- 新加卡/解阻卡要同步更新 HTML 计数和编排文件。
