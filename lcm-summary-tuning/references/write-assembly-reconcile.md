# LCM 写入路径、装配会话绑定与重放对账（诊断配方）

诊断三类问题时的代码入口与实验配方：跨会话摘要载体（装配漂移）、摘要写入质量守卫。重摄取/对账异常。行号会漂——用符号名 grep 定位。

## 写入路径（摘要节点的唯一写点）

- 摘要节点只经 `compaction.py` 的 `CompactionMixin` 内 `self._dag.add_node(...)` 写入（`dag.py` 的 `add_node` 是 SQL 层，调用点唯一）。写入位于大函数 `_compress_impl`——**`compress` 只是公共入口**。改/断言「压缩函数」前先 `grep -n 'def ' compaction.py` 定位真正实现体，否则 `inspect.getsource` 拿错函数、结构断言白写。
- **写前守卫模式**（本地副本已实现，可作模板）。模块级判据函数（纯函数、可单测）+ 调用侧「命中 → `sweep_stop_reason = "summary_result_rejected"` + `break` 在 add_node 之前」+ 源码顺序结构断言（`inspect.getsource(_compress_impl)` 里守卫调用 index < `add_node` index）。守卫必须「拒绝但不消费」：backlog 保留、下一轮重试，不写脏节点。
- 实测残缺签名：摘要文本以提示词自己的格式说明开头（`<summary body ending with ...`）＝生成侧无视输出契约。同型还有空/纯空白。检测保持窄（只测前缀与空），避免误伤 verbatim 小源与引擎自产合成文本（`Filtered replies derived from ignored messages.`）。

## 装配的会话绑定（跨会话载体根因）

- 装配渲染在 `engine.py` 的 `_assemble_context`：查询用 `self._session_id`。节点按 session 过滤的 SQL 本身正确（`dag.py` 的 `get_uncondensed_at_depth`）——不要往 SQL 层找 bug。
- `self._session_id` 是**共享引擎实例的覆盖式绑定**——每次 `on_session_start` 覆盖（`_apply_session_start_metadata`）。上游注释自述该字段会被侧信道/并发会话「偷走」。防御（`_foreground_session_id` 不被侧信道覆盖）只加在操作者视图，**装配查询未受保护**——会话交错窗口内。A 的装配用到 B 的 session 查到 B 的节点，渲染进 A 的历史并持久化（跨会话载体）。
- 时间学两种指纹：秒级紧耦合（实时偷走窗口）与数小时老节点（重绑定恢复路径写回旧指针）。诊断入口：比对装配渲染节点的归属会话 vs 当轮会话。
- 修复方向（本地副本）：把「请求的会话」显式传参进装配、替代全局 `_session_id`。渲染前双源一致性检查＋逐条归属校验（不一致宁缺勿串）。**难点（实测）**：`_assemble_context` 及其调用链当前都没有 session 参数（`_session_id` 是 LCM 内部唯一会话来源）。双源的「第二源」需上溯 `_assemble_overflow_recovery_context` 的调用者去找请求上下文——开工前先追通这一层，否则「显式传参」无处可传。

## 重放对账：整会话重摄取的实验配方

- 机制：重启/重放时对账按内容身份摘要比对存储尾巴。**任何内容改写**（不是只删消息）都会让身份失配 → 光标归零 → 整会话重摄取（消息重复入库）。
- 实验（只用测试 API，不改 LCM 代码。包注册方式抄 `tests/conftest.py`，引擎构造仿 `tests/test_reconcile_tool_scaffold_excerpt.py`）：
  1. `_make_engine(tmp)`：LCMConfig 指临时目录 + 大输出外置阈值调小 + `on_session_start`。
  2. turn1 = user / assistant(带 tool_calls) / tool(大结果) / assistant。`engine._ingest_messages(turn1)`。记 `_store.get_session_count(session)`。
  3. turn2 = 历史 + 1 条新消息。对待测消息做改动（替换内容 / 删除）。`engine._ingest_cursor_needs_reconcile = True`。`_ingest_messages(turn2)`。
  4. 断言 `count == N+1`。不等即重摄取。**必须带阳性对照臂（删除消息）与基线臂（原样）**——没有阳性对照，空结果说明不了任何事。
- 实测结论：**同位置替换（条数/角色不变、只换 content）照样触发整会话重摄取**——凡「内容改写型」压缩/打桩。都要考虑对账影响。可行豁免通道 = 让内容改写携带稳定的幂等标记前缀。由对账侧认识该前缀（删消息方案不可行，因为连替换都触发）。
- 判读陷阱：重摄取的危害不在当下计数，而在把已存消息重复入库、改变后续装配输入。「省 token」与「搅动对账」要分开记账。

## 存量跨会话载体清点与清理（只读→动库的配方）

- **清点**（只读，sqlite `file:...?mode=ro` 连接）。正则扫 `messages.content` 提取 node id（载体头模式与运行期识别对齐）→ 对账 `summary_nodes.session_id` vs 行自身 `session_id` → 不一致即死载体。输出「引用条数 / distinct 行数 / 按会话组合分布」+ 明细 JSONL。
- 规模实录：单个库数百条引用、上百行、跨十几个会话组合——**系统性形态，不是孤例**。清点数字留作修复前后对比基线（修复后应不再增长）。
- **两种形态决定清理粒度**。载体行式（content 以载体头开头、整条即载体——可整条删）vs 转储/引用式（正文内部嵌引用，如历史转储里同一载体头重复出现多次——**含真实用户/工具内容，不能整条删**）。
- 清理动作纪律（**已实操走通**）。全库备份（`sqlite3 lcm.db ".backup 备份路径"`——在线备份 API、不停服务）→ **副本演练**（cp 备份 → 副本上 dry-run + execute 各跑一遍验证）→ **活库单事务**（同一 DELETE，`executemany` + 单 commit）→ **三重后验**：`PRAGMA integrity_check` + 死引用复算（脚本自带 remaining 校验）+ 受影响行 CSV 导出留档。
- **不做文件替换**：lcm.db 是活跃库（gateway 持 fd）——文件级替换会甩掉连接句柄。SQL 事务等价且安全。「副本修 → 原位替换」的文件替换式纪律只适用于**离线**库。活跃库一律「备份 → 副本演练 → 活库事务」。
- 删除的度量换算：**删的行数 ≠ 消除的引用数**（一行载体可含多次引用。实测 95 行消除 127 个引用）——报告时两个数字都给。删除脚本做 dry-run/--execute 双模、两模都导出清单 CSV 可复核。
- **删除同样触发重摄取**（见上节：任何内容改写都触发，删除是它的最强形式）。「数据被重存」列为已知代价、清理后观察即可。转储式引用（含真实内容）走「正文内剥离」是另一件事，另立卡，不顺手扩大范围。

## lcm.db 修剪与 lifecycle 清理（动库前先量）

- **修剪 ≠ 无脑 VACUUM**：先量化回报。VACUUM + FTS optimize 在实心库上回收极小（实测 308MB → 303MB，1.7%）。这本身是**正常结论**（库主体是 messages 本体 + FTS 索引的真实数据）。查构成：`SELECT name, SUM(pgsize)/1024/1024 AS mb FROM dbstat GROUP BY name ORDER BY 2 DESC LIMIT 12`——messages 本体与 messages_fts_data 通常两个大头。回收期望低于 5% 时就报告「库为实心、无需修剪」，不为小回收量冒险撞锁。
- **FTS optimize 是结构整理不是空间回收**：`INSERT INTO messages_fts(messages_fts) VALUES('optimize')`（nodes_fts 同理）合并段——实测尺寸可能反涨。真实回收看随后 VACUUM。VACUUM 在 WAL 下实测秒级（300MB 库）——先副本预演拿回收数字，再决定是否为 3.5MB 级回收动活库独占锁。
- **lifecycle fragmentation**（lcm_doctor 唯一 warn 项，6 类详单）：`lcm_lifecycle_state` 一行一会话（conversation_id 主键）。stale = `current_session_id`/`last_finalized_session_id` 指向的 session 在 messages 与 summary_nodes 皆无。保守清理 = **置 NULL 消引用、不删行**。判定 SQL：`NOT EXISTS(messages m WHERE m.session_id = l.current_session_id) AND NOT EXISTS(summary_nodes n WHERE ...)`。副本演练 → 活库事务，同载体清理纪律。lcm_doctor 的计数是**时刻快照**——重跑会漂（会话自然消化），以现场重算为准。

## survival_fit 的 drop 只裁装配（「历史损失账」判读）

- 日志签名：`LCM survival fit applied (reason=noop, conversation=<id>, dropped_rows=N, store_ids=<a>..<b>, tokens=X->Y, budget=Z)`——**先查再慌**：`SELECT COUNT(*) FROM messages WHERE store_id BETWEEN a AND b`。实测 dropped_rows=70 的行**全部完好留在库**（COUNT=70）——drop 是**装配渲染层**裁剪（active context 不含这些整回合），**不是 SQL 删除**。「删除能否恢复」类追索的常见正确结论就是「无需恢复，数据本来就在」。
- 触发链。摘要被拒（`summary result rejected at level 3; 0 leaves written, backlog kept`——写入守卫的正确行为）→ `LCM compression no-op` → survival_fit 接管（reason=noop）→ whole-turn cut 裁最老可裁整回合。`exit fit skipped: no whole-turn cut ... reaches the exit cap` = 退出侧无可裁目标，非错误。
- **与缓存漂移的交叉**：whole-turn cut 按 budget 裁装配前/中段、每轮位置可能不同。是「prompt 总长非单调波动、每轮中段被改写」的机制候选之一。

## 装配确定性的守卫测试（修复乙模式）

- 目标断言：同状态两次装配**字节一致**。姿势：`out = engine._assemble_context(None, [], persist=False)`（persist=False 写零副作用、纯计算）。`json.dumps(out, ensure_ascii=False, sort_keys=True)` 后比较。tie 场景循环多跑几次。
- **测试 seed 坑（实测踩过）**：构造 depth-1 节点的 `source_ids` **绝不撞已建 depth-0 节点的 node id**。「被更高层引用即 condensed」语义会让该节点正确地从装配消失（uncondensed 排除）。「节点都在输出里」的断言会莫名失败。用不存在的 id（如 9999）。此坑同时顺带验证了排除语义在正常工作。
- tie-breaker 事实（锁定即守卫）：`get_uncondensed_at_depth(newest=True)` = `ORDER BY created_at DESC, node_id DESC` 取前 N 再 `[::-1]` 返回——**选「最新 N 个」、展示「oldest-first」**。`get_session_depths` = `ORDER BY depth`（唯一）。created_at 并列时顺序由 node_id 决定且稳定。
