# 多面板与硬并发上限

适用：新建项目面板、跨 board 派卡、看到 running 数超过预期，或 `max_in_progress` 设了仍起新 worker。

## 计数

- `hermes kanban boards list` / `boards current` / `boards switch <slug>`。
- 每个 board 有独立 DB 与 dispatcher；`--board <slug>` 是唯一可靠的定位方式。只看当前 board 的 running 会漏掉另一块板。
- 逐板取 `hermes kanban --board <slug> list --status running --json`。
- 进程侧：`pgrep -af 'hermes_cli.main.*kanban task'`；用 `/proc/<pid>/cmdline` 里的 `kanban task t_<id>` 认任务号。board 计数与进程数不一致时，先查孤儿/探针。

## 硬上限

- `hermes config get kanban.max_in_progress` / `hermes config set kanban.max_in_progress 2`。
- 它是宿主级上限；运行中的 gateway 可能缓存旧值，`set` 成功不等于立即生效。用 running 计数验证，不信配置回执。
- 内存压力门只限制「每 tick 新增一个」，连续多 tick 会叠到 3 个以上；不要把它当总量上限。
- 要立刻收口：block 多余卡 → 按 PID 杀 worker → `reclaim`（仅 active run 有效）→ 再 count。之后每次只 unblock 一张。

## 派卡与依赖

- 新 board 建卡：`hermes kanban --board <slug> create ... --parent <id> --initial-status blocked`；`--parent` 可重复。
- `create --parent` 的边是真写入的；`list --json` 可能不展开 parents/children，必须用 `show <id>` 回读。多父卡只要一个父未 done 就停在 todo。
- 排期用 `--initial-status blocked` 停放；`unblock` 一次只放一张。不要一次把多张 ready 卡放出来赌内存门。
- `blocked` 不会自动解锁；`todo` 才会在父卡 done 后自动 promote。要无人值守队列，先把父边补齐，再 `unblock`：父未 done 时落到 todo，父已 done 时可能立刻 dispatch。
- `link` 是位置参数：`hermes kanban --board <slug> link <parent> <child>`；`--parent/--child` 不被接受。
- `dispatch --dry-run` 显示候选 `Spawned: 1` 不等于真实 tick 会派；内存压力与跨 board running 会让真实 tick 报 `Spawned: 0`。先查所有 board 的 running、`max_in_progress`、`free -h`，再看 `list`/`ps` 的实际 run；不要因为 0 就重建卡或直改 DB。

## 暂停与孤儿

- `block` 只改台账，不给 worker 发信号；必须按 task id 找 PID 再 SIGTERM。block 前已 spawn 的 worker 会继续跑，卡面 blocked 也可能有进程。
- `reclaim` 只在卡有 active run 时有效；对 blocked/done 卡会报 `not running or unknown id`。
- `assign` 会把 blocked 卡重新入队；不要在只想改 assignee 时用它。要改 assignee 就保持 blocked，等真要跑时再处理，或另建接续卡。
- `t_` 空任务号的短命进程是 dispatcher spawn 探针，不是一张卡；以 board 的 running 计数为准。

## 选哪张停

- 每台 serving 只留一个 worker；远端与本机各一个，不要在本机放两个 coder 抢同一个槽位。
- 第三张出现时，停后 spawn、进度更浅的那张；保留先跑、更接近交卷的那张。
- 高优先修复占远端，本地留一张；设计/文档卡让路，不要和实现卡抢同一仓库的写锁。
