# 派卡前核验 worker 技能可见性

- 按目标 profile 的技能索引核验 `kanban_create.skills` 中每个名字。主会话能 `skill_view` 不证明 coder profile 能强制加载同名技能。未收录名字会在代理初始化时直接退出，连模型与任务正文都还没有执行。
- 对跨 profile 共享指引，若没有目标 profile 可见的技能名，使用 `skills=[]`，在卡体给共享 SKILL.md 的绝对路径。要求 worker 通过 read_file 只读加载。不要为一次任务改动其它 profile 的技能目录、配置或 SOUL。
- 收到 crashed/pid gone 先读 task run error 与 worker 原始日志，并独立检查目标文件哈希、备份和部分产物。Unknown skill(s) 是启动参数错误，不是模型能力或模板推理错误。不要盲目解锁触发同样的失败。
- 原 CLI 不支持编辑 skills 字段时，优先保留失败卡并建立技能要求已修正的接续卡。明确继承原正文及验收范围，避免无审计记录的数据库直改。回读模型/provider、skills、状态与新 worker 启动记录后才报续跑。旧卡待接续产物验收后再结算。
- 诊断同一个目标 profile 的其它待派卡是否也有相同启动要求。在可见性核验前不要放行，避免重复故障。

## provider 与 skills 双检

- provider 名是 profile 局部配置：主 profile 有 `node-ii-lan`，目标 profile 不一定有。`skills` 通过不代表 provider 通，两个都在 worker 构造阶段消费，缺一个都可能在第一个 token 前退出。
- 失败签名：task log 只有 `Kanban owner refused: Kanban execution unknown; retained by owner`，`show` 看到 running 后转 crashed；真 traceback 在 `~/.hermes/profiles/<profile>/logs/managed-worker.log`，常见 `Unknown provider '<name>'` 或 `Unknown skill(s)`。先读这个日志，再决定重派。
- 恢复：优先 `reassign` 到同时具备该 provider 与技能的 profile，再 `unblock`。`max-retries=1` 失败后卡已 blocked，`reclaim` 对 blocked 无效；不要用 `assign`（会重新入队），也不要直接改 DB。
- `hermes --profile <p> skills list` 的表格会截断长技能名；以 profile 技能目录或完整索引核验，别用截断列判定“没有”。
