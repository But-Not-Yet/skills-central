---
name: kanban-dispatch
description: 给 coder、检察官这类 worker 派活时加载：看板开卡、设模型、回读核验、暂停恢复、验收交卷；要设计多镜头并行评审卡、或复核 worker 自报的交付，也是这份。
version: 1.0.0
author: Nekonya
license: MIT
metadata:
  hermes:
    tags: [kanban, dispatch, worker-profiles, review]
---

# 看板派卡与验收（coder / 检察官 / 多角色编排）

## When to Use（触发）

- 要把实现或审查工作派给 worker profile（coder、red-team-auditor）：开卡、设模型、回读核验、暂停恢复、验收交卷。
- 要设计并行评审卡（多镜头分工）或复核 worker 自报的交付。
- 两台机器（本机 serving + 远端节点）同时派活，或要把剩余任务拆成两条低交叉线。

## 工序

1. **派卡前先报**：派几个、各自干什么、用哪个模型、为何需要隔离或并行，都要先报。这些花钱手段要逐次取得主人明确批准。批准目标不等于批准手段。主会话负责目标、关键判据、范围裁决、及时纠偏与验收。细读源码、详细方案起草、批量核验与实现优先交本地 worker，别让昂贵的 API 主会话代做。用户明确要求本地执行时，模型与 provider 锁定本地，不许自动回退云端。除另获批准，不开云端子代理。单本地 serving 先一张卡串行做，主会话交接后不并行重做同一份调查。对看板当前状态做短回读。交卷后只复核承重证据和方向偏差，不默认重跑 worker 的全部工序。
2. **开卡（kanban_create）**：卡体只放要点，规格书/方案文件是唯一事实源（卡内写明「动手前完整读」加绝对路径）。验收判据冻结进卡。建卡后卡体前提过期时用 `hermes kanban edit <id> --title ... --body "$(cat 文件)"` 整体重写（正文经文件传入防引号坑），改完 show 回读抬头确认落地。改写/润色类卡要多冻两样：字数方向（只许降／持平／限量升）——不设时改写的自然趋势是把注入面的短文越写越长；以及豁免类白名单（词表行本体、文件名与约定名、引语内原文、被点名原话），预先写明要 worker 自登。硬约束逐条列（fail-open、TDD、署名铁律、不 push 上游、不改格式）。分阶段的活要明确写「阶段二不在本卡」。
3. **模型指定**：开卡时用 `model` + `provider` 字段。卡已建好用 `hermes kanban set-model <id> <model> --provider <p>`，它**只对下一次 dispatch 生效**。模型随主人当次指令（可能指定本地，也可能点名云端如 `z-ai/glm-5.3-flash`），派卡前按当次指令检查一遍。不带 override 的卡跑 profile 默认模型（coder 默认=本地 localllm）。**换模型先查卡是否已被接走**：已 claimed/running 的 run 会拿旧模型跑到底，set-model 救不了它。抢救序：① **先 `set-model` 再 `reclaim`**。set-model 对在跑的 run 无效，但管住下一次 dispatch。reclaim 把卡放回 ready 后 dispatcher 秒级就可能重派，若 set-model 落在重派之后，新 worker 仍带旧 override，只能二次 reclaim。② 进程还活着就补 `kill <pid>`。③ 没动静就补一次 `hermes kanban dispatch`。④ **验证以新 worker 命令行实锤**。`cat /proc/<pid>/cmdline` 应见 `-m <新模型> --provider <新provider>`，实锤到手前不宣告改派成功。主人手动把卡改成 ready 也等于一次 reclaim：旧 run 会被标 reclaimed，dispatcher 立刻起新 run。此时核 `runs` 的 run 号、`model_override_set` 事件、旧 worker pid 是否已消失、新 worker 命令行是否带新模型；看到 `running` 不等于旧模型还在跑，也不要再点一次 ready/dispatch 造出第三跑。dispatch 摘要报 `Spawned: 0 / Memory pressure` 时别下结论，以 ps/show 的实际 run 为准。云端模型卡体内白纸黑字注明主人批准与覆盖范围。**provider override 先在 assignee 自己的配置中预检**：只读取所需 provider 名和路由字段，不回显 token。当前 profile 的配置不能证明另一个 profile 已配置好。缺配置的卡先挂起并明确缺什么，不能静默换到云端；有现成的、同时具备 provider 与 skills 的 profile 时，改派它（`reassign`）优先于改配置。只有用户明确授权修改该 profile 时，才备份并按有效配置格式补齐 provider、回读核验，再 unblock 并验证实际 run。worker 在构造阶段崩掉时，task log 可能只有 `Kanban owner refused: Kanban execution unknown; retained by owner`；真 traceback 在 `~/.hermes/profiles/<profile>/logs/managed-worker.log`，看见 `Unknown provider` 或 `Unknown skill(s)` 就按启动参数错误处理，别原样重派。`max-retries=1` 的卡首次失败会 blocked，`reclaim` 对 blocked 无效；`reassign` 后用 `unblock` 重派，回读新 run。没有授权就不改其它 profile 的配置、技能或人格。
4. **写后回读（铁律）**：凡关键字段写入（model_override、priority、assignee、body），必须 `kanban_show` 回读核验后再宣告成功。模型偶发 DSML 参数泄漏（相邻参数被吞进同一字段），CLI 输出说成功不等于字段落地。
5. **评审镜头去相关**：并行评审卡给不同镜头、不同 brief。冷读工件镜头（先自判再对 narrative）、实跑执行镜头、契约镜头（对照原验收）各派一张。同镜头并行只会重复发现同一类问题。评审卡里写明「其他镜头已覆盖的部分」，职责是攻它们之外的部分。
6. **角色分离**：评审只出清单不改码。正确缺陷走 `kanban_request_changes` 回给实现者，不用 block。
7. **暂停/停止**：先 `kanban_block` 后 SIGTERM。反过来的序列里 block 会失败并复活卡（worker 实测证伪过旧提案）。批量暂停用 `~/.hermes/scripts/pause_workers.sh`。
8. **验收**：交卷后 `kanban_show` 读 runs 的 metadata（tests_run/verify_done/commits/known_limits），把「实现者自报 limits」当待核声明独立复核。报告要带行号级证据（日志行/代码行/哈希）。抽验 2-3 处引用点（直接读那一行原文）即可低成本定其信用等级。全对则通过，一处失配即升级为全量审计。实机判据（性能、吞吐、无风暴类）必须真机 serving 复测，测试绿不算数。对判官/检察官判决产物的质量审计（证据指针当场开考）见 `references/verifier-evidence-audit.md`。审判卡用 `parents=[实现卡]` 门控：实现 done 就自动解锁，不靠口头接力。评审进行中捞到的现场实锤用 `kanban_comment` 递进台账（带日志行加代码行号），让裁决把它算进去。评审与上线并行时，这是唯一能让判决覆盖最新事实的通道。

**审计+测试全绿 ≠ 状态机角落已覆盖**：还有 rewind 类「输入比缓存状态短」的角落。两轮评审（实现者镜头加对抗镜头）之后，它仍被真实流量炸出来。签收前把活体系统过一遍交互矩阵（增长 / 切换 / rewind / 崩溃 / 多会话并发），实机判据才算数。验收加生命周期透镜：临时产物必须在成功路径上回收。只靠启动时清理的，就是泄漏类缺陷。

**验收执行细则（工具层）**：① 跑自报测试前先探测有依赖的解释器。对候选 python 逐个 `"$C" -c 'import pytest'`，装了包的那把才是能复现的。本机常见是 hermes-agent 的 venv，默认 python 常缺依赖。探测到再跑套件，别因默认环境缺包就宣告「无法验证」。② 读测试文件本体再采信测试报告。断言必须落在**行为**上（写入文件的产物、复算哈希、失败路径、隔离文件）。对着源码文字做快照式断言是假绿，绿也不采。③ worker 的演示产物没写入文件（tmp 被清）时，用等价合成数据自己重建并记录**自家数字**。复现成本低就不把引用点标「未验」。④ 署名核验顺查两层 config（repo-local 加 `--global`）：全局层可能挂着真实邮箱，机制与处置见 git-repo-hygiene。⑤ **冻结件/锚点类工件的复核不许抽验，必须全量对锚**。工件引用的每个文件都复算 sha256，每个引用行号都实开文件逐字比对原文。结论还要回它声称的依据文档逐条对表。这类工件的全部价值就是锚点本身，一处失配整条链作废。工件主动登记行号偏移或出处差异（而不是掩盖）是质量信号，验收时记功。⑥ **语义改写类工件的保全核对用集合比对不用计数**：反引号段按内容做多重集相等比对，hash、数字 token、引语对逐一值逐一值比——计数相等不等于内容相等，速记段被展开成完整形态时那个段已被替换而计数照旧持平。差异用 diff 定位后逐条归类：良性澄清（缩略引用展开为可执行命令、语义零损）放行入账，损坏退回。宣布「守恒」要分维度带档位：计数维的守恒断言覆盖不到内容维，全称断言没逐项实测就被检察官按越权击落。
9. **定时批次（主人睡觉时的无人值守流水线）**：解锁动作用 `no_agent=true` 的 cron 加解锁脚本（`~/.hermes/scripts/*.sh` 里 `hermes kanban unblock <id>`）。到点跑 shell，不烧一个 token。deliver='local' 只静默正常输出，脚本非零退出或超时仍发 error alert。错时派发（每张间隔 2 分钟）防 dispatcher 同时起多个 worker 抢内存。不许主人错过的卡保持 blocked 挂起，只有「无需在场」的卡进自动批次。排卡前先按「是否需要主人在场」分开排队。
10. **恢复被阻塞的卡（开工令形态）**：① `kanban_show` 读现值，沿用用户已设好的模型与优先级。核 assignee 自己的本地 provider 路由，只取所需配置字段，不回显凭据。检查客户端实际连接的端口健康。后端健康不证明桥接端口健康，客户端模型别名也不必等于 health 中的权重名。依赖未就绪的卡保持 blocked，不静默换 endpoint、provider 或派云端替代。② **先把「指令转写」写成评论再 unblock**。口头授权、待批项放行范围、实施边界和原判据都写到卡上：worker 不读主会话聊天。③ 再 unblock。工具调用与 CLI 都用同一个明确 board，CLI 格式为 `hermes kanban --board <slug> ...`。不能凭另一块板的空派发摘要判断任务未启动。④ 回读 `claimed/spawned`，看到 run 在跑或有心跳再报开工。ready 只表示已放行。⑤ **恢复派发后用 worker 命令行实锤模型 override 没丢**：`ps` 或 `/proc/<pid>/cmdline` 应见 `-m <override模型> --provider <override provider>`。卡的 override 字段理论上随卡保留，但「配置在卡上」不等于「这次 dispatch 用了它」。实锤到手前只报「已派出」，不报「按指定模型在跑」。需要手工 dispatch 时先限数量并预览，避免启动无关卡。预览 spawned 为空也可能是调度器已先接走，先读该卡现 run，不重新建卡或重复启动。
11. **判决书/审计清单回收（检察官或外部核验到手时）**：逐条先回文件核验再表态，三选一。**接受**：改口要**写入文件**：原句保留，再加「修订注」注明原表述档位与被驳点，只在对话里认错不算。**反驳**：附证据、开得到文件。「找不到/没说过」类主张先全库检索。会话检索默认范围常只覆盖当前会话（`lcm_grep` 须显式 `session_scope='all'`）。检索时要披露词表/范围/结果数。结果是工具回显或转述的要剔除。**待核**：写明核法。复述断言带档位：实测（可指日志/代码行）/ 演绎（附推理链）/ 推演（注明与实测差距）。「全部/唯一/精确在 X」这类全称没逐项实测就降级为区间加上界。程序报警的复核必须对**写入文件的全文**重新跑检测。贴进对话的节选经过工具截断，截断处正是盲区。拿截断摘句宣布「全部为误报」是抢跑。对着原文全文核验之前，该断言只能标待核。

## 项目地图与单槽位串行

- **进度按线报，不把展示层原型算进运行时**：项目分成展示层/运行时/运维多线时，先报线名、卡号、状态、产物路径，每条线单独算完成度。展示层 Hook 能跑不等于运行时子系统已交付；不要用一个 UI 卡的存在证明整条线完成。
- **向主人解释 `blocked` 时先按用途分组**：常驻地图/索引（永不派）、等主人拍板（宿主补丁/上游接缝）、插件外文档/运维（不归 worker）。`blocked` 不是失败，也不是自动队列；先给这三类和处置建议，再列卡号，别让主人自己翻译一排 `t_` 号。
- **项目卡堆积到主人分不清时，先建一张 blocked 地图卡**：按主题分组（主干 / 模块 / 诊断 / 相邻项目 / 无关实验），每张卡一句用途与状态；地图卡常驻不派发，历史卡先不归档。没有地图就归档，下一次还会在同一堆卡里迷路。
- **代码卡用 `--workspace dir:<repo>`**：默认 scratch 是隔离临时目录，worker 看不到仓库；要它直改仓库就把绝对路径写进 `--workspace dir:`，卡体再写「不要另建副本」。
- **`--model` 写端点实际服务的 id**：provider 配置里的 `model` 可能只是别名（配置写 A，`/v1/models` 返回 B）。派卡前 `curl -s <base_url>/v1/models` 取实际 id，再写卡；写错会 404 或静默换默认模型。
- **弱模型任务书八节**：目标 / 先读清单（文件:行）/ 改动文件 / TDD 步骤 / 验收命令 / 回滚 / 禁止项 / 交卷格式。每节写死绝对路径与命令；弱模型不会用常识补契约空白。
- **多面板按 board 计数，硬上限要核活体**：所有 CLI 用 `hermes kanban --board <slug> ...`；`boards switch` 只改默认 board，不改变各 board 独立的 DB 与 dispatcher。只看当前 board 的 running 会漏掉另一块板。`kanban.max_in_progress` 写进配置不等于运行中的 gateway 已重读；内存压力门只限「每 tick 新增一个」，跨 tick 会累积。发现第三张时先停后 spawn 的卡：`block` 后按 `/proc/<pid>/cmdline` 找 task id，再 SIGTERM；`reclaim` 只在 active run 上有效。`assign` 不要在 blocked 卡上用——它会重新入队并可能立刻起 worker。完整命令与选卡规则见 `references/multi-board-concurrency.md`。
- **`dispatch --max N` 是当前 board 的总并发上限，不是本 tick 放 N 张**：已有 1 张 running 时 `--max 1` 会 `Spawned: 0`；两槽要 `--max 2`。先 `--dry-run` 看 `Spawned` 与 memory pressure，再实际 dispatch；不要把 `Spawned: 0` 当卡死。
- **卡上 `skills` 先按目标 profile 可见性核验**：主会话 `skill_view` 能看见，不证明目标 profile 能强制加载；不可见技能会让 worker 启动即崩（Unknown skill(s)），连任务正文都没读。跨 profile 没有可见技能名时用 `skills=[]`，卡体给共享 SKILL.md 绝对路径。详见 `references/worker-skill-scope.md`。

## 两机两线编排（重/轻分工）

两台机器同时干活时，先分线，再派卡；不是把 ready 卡全放出来。

- **一线一机、线内串行**：全局 `max_in_progress=2`；每条线同一时刻只跑一张，完成一张再放下一张。
- **重活留主 serving，轻活给远端**：主 serving 跑核心实现/状态机/租约；远端只接机械可验、读多于写、或文档/回归 fixtures/旧卡处置。远端卡体写全绝对路径、输出格式、禁止项；不要让它逐行审代码。
- **文件所有权先切开**：A 线独占核心源码（如 `provenance/`、`engine.py`、`guidance/`、`core/`），B 线独占 `tests/regression/`、`scripts/`、`docs/`、看板控制。两线不碰同一文件；测试目录按子目录切。
- **同仓库并行前先看文件锁是否真的接线**：模块 + CLI + 单测全绿不等于 dispatcher 会调用它；没接派发前，同仓库只允许一张卡，哪怕另一台机器空着。
- **顺序用父边锁死，不靠口头**：先 `kanban_link` 再 unblock；父卡已 done 时 unblock 可能立刻 promote+dispatch，注意抢跑。`blocked` 卡（尤其 `--initial-status blocked`）不会自动解锁，只有 `todo` 会在父卡 done 后自动 promote；要无人值守队列就先把父边补齐再 `unblock`。CLI 的 link 是位置参数：`hermes kanban --board <slug> link <parent> <child>`，写 `--parent/--child` 会被拒。
- **模型按线设，逐卡回读**：`set-model` 只对下一次 dispatch 生效；批量设完用 `list --json` 核 `model_override/provider_override`，不要只看 CLI 回执。运行中的卡要改模型，先 set-model 再 reclaim，并核旧 worker 已消失。
- **进度看产物，不只看心跳/日志**：代码写入型 worker 的日志可能只有 `Session:`；用 `find <workspace> -newermt` 看文件 mtime/新增测试。连续 10 分钟无新写入再按卡死处理。
- **槽位空着不是开工理由**：依赖未到、或第二张要进同一仓库且文件锁未接线时，宁可空着；硬塞会制造新的同树覆盖。
- **看板替换先问需求，不自研 runner**：主人明确保留 Hermes 社区看板，控制面繁琐不等于要重写；只有看板不能满足硬需求或主人明确要求时，才提自研 runner/harness。被否决的 spike 收尾：先 `unlink` 它作为父卡的全部下游边，再 `archive`，并在卡上留 comment；只 `block` 会让 release 卡永远等一个不做的实验。

模板、命令与验收清单见 `references/two-machine-lanes.md`。

## 交卷回执与订阅（worker 完成 ≠ 主会话收到）

- **父卡关系只决定调度，不产生回执。** `kanban_complete` 把终态事件写给 `kanban_notify_subs` 里的订阅；没有订阅，卡会安静地 done，主会话只能在看板里发现。派卡后要么用带 origin chat 的建卡工具让 `kanban.auto_subscribe_on_create` 生效，要么在 CLI 建卡后补订阅。
- **CLI 建卡不会自动订阅**：`hermes kanban create` 没有聊天身份，`auto_subscribe_on_create` 不触发。补订阅命令（desktop/api_server）：
  `hermes kanban notify-subscribe <id> --platform api_server --chat-id "$HERMES_SESSION_ID" --chat-type dm --delivery-mode notify+wake`
- **`api_server` 平台禁用 `--delivery-mode notify`**：`APIServerAdapter.send()` 恒返回 `SendResult(success=False, error="API server uses HTTP request/response, not send()")`；`add_notify_sub` 对 `api_server` 的默认模式是 `notify+wake`，显式 `notify` 会覆盖默认，订阅变死信。省略 `--delivery-mode` 或写 `notify+wake`/`wake`。
- **验证订阅不是看 "Subscribed" 回执**：`hermes kanban notify-list <id>` 要看到 `mode=notify+wake`；`kanban_notify_subs.last_event_id` 必须随 `task_events` 的 `completed` 事件前进。游标停在订阅时刻、事件号更大，就是没投递。
- **`notify+wake` 仍不投递时查网关 `active_platforms`**：`_claim_for_sub` 对不在 `runner.adapters` 里的平台在 debug 级直接跳过（`adapter not connected`），订阅行看着正常但游标不动。`api_server` 平台还要确认网关确实提供了该适配器；没有就换一个已连接的平台，别只改 delivery_mode。
- **worker 完成没有推送时先查板，不假设还在跑**：`kanban_show` 的 status/completed、`runs` 的 outcome、日志末行三条独立证据。卡 done 不等于主会话已审阅；补订阅只影响未来事件，不重放历史（新订阅从当前最大 event 开始）。
- **别把 `delegate_task` 的父会话回执套到 kanban 上**：前者把子代理结果送回父回合；后者是持久队列，默认不推。要回执就订阅，要自动审阅就建 wake 订阅或周期查板。
- **订阅/`cron deliver=all` 仍可能没有投递目标**：桌面会话若是 stateless HTTP，网关没有可推送的 adapter，`deliver=all` 会报 `no delivery target resolved`，订阅游标也不前进。先看 `last_delivery_error` 与 `kanban_notify_subs.last_event_id`，不要把「已建订阅」当「回执已送达」。可靠兜底是每回合开头 `kanban_list`/`kanban_show` 读板，或做桌面插件 toast；不要为回执反复重建订阅。
- **hidden user 消息不能当回执通道**：后台进程 heartbeat、`[ASYNC DELEGATION COMPLETE]` 这类消息以 user 角色写进会话；宿主可能因此重放 durable tail，把旧消息重新激活并打乱 UI 顺序。用它们做回执，等于用会话完整性换一条通知。回执走真实聊天 adapter 或桌面插件；没有就轮首读板。

## 陷阱

- **kanban_block 只是台账记号、不发信号**：worker 不主动读卡就不知道被停。停与恢复各在卡上留一条 comment（为何停、何时恢复），新 worker 读卡就看见，不用猜。
- **看门狗 SIGTERM 后卡不结算终态、会永挂 running**：卡上要设 `max_runtime_seconds`。设了它，dispatcher 到点 SIGTERM 后会自己写 timed_out 结果。实测发现，不带上限的看门狗 SIGTERM 会漏写终态，卡永挂 running，10-15 实例靠人工 reclaim。带时限的超时行为今日未复验。
- **spike 卡不能沿用默认 30 分钟上限**：1 天 spike 一旦交付物是测量 harness，就别把“生成 harness”和“在临时库上跑它”都塞给同一个 35B worker。默认 `max_runtime_seconds=1800` 会在它写完脚本、还在跑对照时 SIGTERM，`max_retries=1` 直接把卡 block；这不是远端能力不足，是配置不匹配。开卡时显式 `--max-runtime`，或拆成“生成/检查 harness”与“shell 直接执行 harness 并收 JSON”两段；后者几分钟能跑完，前者也不会撞墙。看到 timed_out 先读 workspace 产物和 `max_runtime_seconds` 再判断。
- **工具调用偶发吞参数**：set-model 等命令跑完回卡上读一遍，确认参数真写上了再往下走。
- **时长估算按模型分档**：本地模型做读多于写的活会慢，还有复读区间（100–150K token 区间），云端快。给主人估时要先报用的是哪个模型。
- **深度审查卡要锁范围**：卡体里给出 diff 定界命令（`git diff <base>..HEAD --stat`）与重点攻击点清单。否则评审者会把整仓当对象，时长爆炸。
- **superseded 设计不留活图**：方案转折后，对话里发过的旧框图/旧流程图作废，要明确声明「以规格书为准」。别让旧图继续误导下一轮讨论。
- **单模型主机的排卡纪律**：本机只能同时跑一个模型时，worker 与主会话共享同一个 serving。给 worker 排卡严禁并发多卡，一次一单，长任务排主人不用的时段。给主人估时要把排队等待算进去。
- **多机 serving 池按难度分派**：主力机单模型排队时，还有第二台机器可用。它的 serving 在 config.yaml 注册成 provider（如笔记本节点），可以接 worker 卡。这样买到的是真算力，不是隔离。分派按难度。素材已在卡体点名的、产出机械可验（pytest 红绿即判据）的卡给弱模型/小窗口模型。要逐行核代码的、或冻结件决定下游资格的卡留主力模型。主会话负责盯进度与验收兜底。给小窗口模型的卡上留评论写明「按卡体点名处切片读，别整吞大文件」。派低能力远端节点（35B-A3B 量级）的卡，卡体本身就要按主人要求写细：输入逐个绝对路径列全、输出格式逐列定死、明令「不许改代码」，并自带回退条款（干不完怎么留痕、读数存疑怎么办）与最后保障——小模型不会用常识补契约里的空白。硬件溢出共池（显存装不下走内存）会慢，估时按慢档报。**边界：worker 的模型/硬件可换（产物有人复核），实验被试的硬件不可换**。剖面/测量类数字即证据，必须与档案基线同机同栈产出。换栈数字会漂，与旧档案不可比。
- **内存压力下 dispatcher 一次只放一个新 worker**：两张卡同时 ready 时，第一张 spawn 后第二张可能等下一 tick；`Spawned: 0` 不等于任务失败。用 `kanban_list --status running` 加 `/proc/<pid>/cmdline` 确认两边都在跑，别急着重派或宣告只起了一张。
- **被试模型别兼当 worker 大脑**：worker 模型等于被试模型时（远端实验节点当 worker）时，被测长文要读进上下文。它和 agent 循环抢同一个 serving 窗口，必然撑爆。日志形如「grown too long」、rc=1，dispatch 只报 worker crashed。改道：重活交自带直连被试端点的脚本（自切块、断点续跑、拼接、程序化自检、幂等不怕复跑）。worker 的角色降为「脚本操作员」：起脚本 → tail 日志 → 粘贴 stdout 计数行与程序检证据交卷。卡上评论明令禁止 cat/sed 被测正文进自身上下文。崩溃重派前先写「执行角色改写」评论再放行。主会话可先代跑首发推进进度，worker 复跑幂等脚本自然跳过已完成块。
- **worker 自报摘要 ≠ 活体**：晨间汇总前对关键断言逐条实测（`profile list` / `search_files` 查文件存在性 / `kanban_show` 字段）。worker 的完成通知是自报不是验收，同 profile 多 worker 交叉领卡时更甚（依赖边靠 kanban_link 自动等待，别靠口头转述）。「下游卡已随本卡自动解锁」这类依赖断言同样要逐卡 `kanban_show` 核 status 加 parents。多 parent 卡只要还有一个 parent 未 done 就停在 todo，单看本卡 done 会误报解锁。
- **hook 接线必须用集成测试验收**：worker 说「已接上 pre/post hook」时，先读 `__init__.py` 看组件是否实例化、`pre_llm_call` 是否真的 drain；组件单测全绿不等于 hook 注册生效。用 fake ctx 捕获回调，实际跑一次 post→pre，断言注入内容出现；没有这条集成测试就按未接线处理。
- **请求侧修复要在 wire 上验收**：只断言 hook 返回值会误判。宿主在 hook 之后可能还有第二道合并/清洗（例如把相邻 user 行重新焊接），会把修复结果吃掉。先读完整装配链，测试到最终请求，或明确写「该修复只在 hook 层成立」。
- **判据阈值的闸 FAIL 就不放行、也不事后放宽**：预注册的阈值（如 Kendall τ≥0.8）在 N 小样本下可能等价于全对。先在判据文件里登记好这个推论再跑，结果出来不许以「差一点」放宽。改判据必须主人批复，且本轮作废重跑。
- **机制未确认清楚就不写修复卡**：活体系统的悬案先派「只诊不改」卡。允许 build-tests 探针转储数据结构，禁止生产源码改动与引擎操作。修复卡引诊断结论作事实源。机制假设没过数据闸不许进卡：立「漂移/竞态」类假设前，先画 prompt 尺寸序列排除用户 rewind/删改类事件。写错的根因叙述会带偏整条修复链，还烧掉一轮审判。
- **「前置」卡必须是目标卡的父卡，不是子卡**：给某卡加「动手前先做 X」的前置卡时，X 要建成目标卡的**父**。写法有两种：`parents=[X]` 写在目标卡上。或建 X 时不带 parents，再 `link X 目标卡`。挂成目标卡的**子卡**会死锁：子卡被父卡门住，父卡正是那个目标卡，X 永远 ready 不了。建卡时若把前置写成 `parents=[目标卡]`，`kanban_create` 照收不误（返回 gated_by=目标卡），也不返回错误。必须回读 `show` 核 parents/children 方向才发现。纠正用 `unlink 父 子` 加 `link 子 父` 反向。
- **建卡前查重（在跑加已排卡全列）**：同题材/同文件域的卡先 `kanban_list` 比一遍再建。重复的代价是两个 worker 并行啃同一件事，烧到第三方发现才停。发现重复后保留规格更完整的一张，另一张停用去重。停用说明里写清重复根源（供后续建卡自查）。
- **卡正文引用的每个卡号必须来自当场看板输出**：写「给卡 X/Y/Z 设覆写」这类点名活之前，先 `kanban_list` 把目标逐一验在库再落笔（10-22 实例：主会话往 worker 卡正文写了四张『GPU 批卡』卡号，全是记忆发明——库里 no such task，grep 项目文件连 GPU-1~4 代号都不存在；worker 正确地 block 挂起等主人，反而比主会话靠谱）。文件路径同理：项目文件里的代号也要 grep 确认真有再引。worker 挂起报「卡不存在」时，先怀疑主会话的账，别怀疑看板。纠卡流程：edit 换正文（写明旧号作废原因）→ comment 留更正记录 → unblock 续跑。
- **35B 级 worker 誊写必失真，交卷后主会话逐字对账**（10-22 双实例：规程行「脑子规矩」被誊成「脑子规整」、「忘设」誊成「忘办」；交卷 summary 还把「四张卡」当标题重复，无视卡上已改「7 张」）：要求 worker 原样贴行的活，验收必须 sed 实测该行原文并逐字 diff，不许只看交卷 summary；抓到错主会话直接 patch 勘正提交，别为两个字重开卡轮。**交卷时刻贴的纠正评论可能进不了 worker 上下文**（评论晚于 spawn 一步就被吞），要 worker 必做的修正写进卡正文再 edit+unblock，或接受主会话事后勘正。
- **worker 自报路径也要对账**：fenced delegate 下 CLI 写被围栏拒，worker 改走 kanban_db.set_model_override 直写——结果有效（show 回读绿）但交卷里「任务正文 sanctioned 的备选路径」是发明（卡正文没写过这条）。验收只认实物回读，路径叙事当文学看；直写走了官方函数才不算破 schema，看到 worker 裸写 SQL 要查表结构。
- **引用自己的实测结论时禁缩写**（10-22 检察官点名）：正文引卡上 model 行写「node-ii-lan:coder-iq1_m」——把 qwen3.8-flash-next-coder-iq1_m 掐了头，「逐字对账」的说法就自相矛盾。规则：凡宣称逐字/原样的引用，正文必须原样全串，不许为了省字掐型号前缀。
- **service 名逐字匹配坑（sudo/sudoers）**：sudoers 白名单写 `/usr/bin/systemctl … strata-server.service` 全名时，裸名 `systemctl start strata-server` 要密码、带 `.service` 后缀免密直通（sudo 对参数逐字匹配，不做 unit 别名解析）。给免密圈定的服务写脚本/看门狗，命令里的 unit 名必须与白名单字符级一致，写完 `sudo -n <同一条命令>` 实弹验一次。
- **worker 的 blocked 理由也会过期**：block 引用的前置快照（「配置无参数、进程无 flag」）可能在处置前已被满足。先查活体（当前配置内容加当前进程命令行）再决定。前置确已满足就评注「快照过时加现状证据」并 unblock，别按字面让卡干等。同一原因反复 unblock 再 block，会自动升级 triage。
- **状态栏是活的，卡正文前提与父卡交接元数据都是快照**：放行一张被挂起的「修 X」卡前，先核 X 在 HEAD 是否还成立——`git log`/`git blame` 涉事行、`git merge-base --is-ancestor <疑似修复提交> HEAD`、读代码实物行。修复常以顺手提交并入主干（别的线干活时顺路治了它），动手的人没有义务回来勘这张卡。若修复已在库，不许照原文执行：把卡正文目标改写成「X 已由提交 <hash> 修复，剩余工作是验证与销账」再放行，否则 worker 会修一个不存在的缺陷并把旧账当真传下去。父卡交接元数据（worker_context 的 Parent task results）是 parent 完工时刻的记录，会自动注入每个后续 worker 的上下文——其中事实被新提交推翻后要当场在受影响卡上留指针评论勘掉，否则旧事实随每次派发转录一层、越转录越显现行最新（审计→卡→转述三阶变质）。自家提交动了某张挂起卡的前提文件时，交卷同时就去那张卡留指针评论。勘误卡若排在它所勘任务的正后方（依赖链死锁），别等链自纠，评论就地勘。**查证的过期要一次清尽所有转录处**：卡正文重写、涉事旧报告尾部追加勘误注（不改原文，注明断言的成立时刻与作废时刻）、索引/代号表行、待办快照节、排在后面的未来勘误卡上挂提醒条（注明已修何处、届时只需复核），改完 git 提交留痕——单点修正堵不住多条转录路径。
- **停服窗口的卡用脚本办，不用 worker**：worker 的大脑就跑在本机 serving 上，停服即 worker 同灭，验收与计算都没人执行。分两形态，其一主人在场的验收形态：独立一键脚本交主人直跑（sudo 只有主人能动手，脚本里写全停服/起服命令与耗时预期）。脚本必备四件：①预检——涉事进程确实不在（pgrep -x）、空闲显存≥需求（rocm-smi 读数换算）、参考输入哈希等于冻结值且缺失时自动从原件恢复；②读数与冻结账本逐项 PASS/FAIL 打印，判据取**同机同栈**的实测账本，不拿别台机器的数；③带时间戳的 tee 日志加结果 json 留痕，作销账凭据（主人只需回一句「过了」，凭据在文件里）；④退出码分流（0 过 / 1 预检不过 / 2 读数不符），读数不符时脚本原话写明「别改代码，把屏幕结果发回判读」。发货前实测各分支：服务未停时跑一遍验预检拦截；拿冻结账本伪造探针输出喂比对器，验 PASS 路径。其二主人不在场的无人值守批形态（夜里重算/长 GPU 批）：主人睡前跑一条 `sudo bash 脚本`，脚本自身已是 root，自己停服起服。必备件：预检全绿才许停服（不过就一物不碰）；停服是主体唯一动 systemctl 处；显存释放轮询 ≤30s 带上限；python 原地覆盖旧数据时先带哈希归档旧账，跑成后把旧文件名回填原件（旧报告与勘误的引用不断链），新数据存新名带协议头（测量约定+git 提交号+时刻）；每步独立进程独立 `timeout -k 60 N` 限时（一步崩不拖另一步）；`trap finalize EXIT INT TERM` 兜底——任何退出路径必起回服务（先 is-active 判断防重复起）、限时轮询健康检查、把 root 新产物 chown 回主人、写逐步骤 PASS/FAIL/TIMEOUT 的 STATUS 文件——早上验收只读状态文件，「脚本跑过了」不算完工。夜里批只做无脑确定性计算；对照表、报告这类要用脑的活白天派卡走远端节点。成败以退出码与脚本自带成功行判定，不以 stderr 体量判定——pandas 可选加速器（旧 numpy 编译的 numexpr/bottleneck）会喷长 traceback 仍退出 0，别当失败、别在无人值守中途去修环境。宣称「已实测」前逐分支确认真的执行过：在第一个闸就退出的干跑没测到后续任何分支——把脚本拷到 /tmp 跳过首闸真跑深分支；trap 路径用「退出点改 sleep 的副本」发 TERM 演练。rocm-smi 显存字节按行尾列取（`awk '/GPU\[0\]/ && /Used Memory/{print $NF}'`）——行形如「GPU[0]: VRAM … (B): <bytes>」，按首个冒号切段取到的是 VRAM 一词而非数字，后续当数用就报未绑定变量。
- **auto-decomposer 拆卡不带上下文**：被 block 的 root 卡（同因 block 达阈值时尤甚）会被 auto-decomposer 拆成子卡。子卡们 gate 住 root，全部完成才唤醒 root。子卡卡体只复刻 root 的部分上下文，**不含 root 最近一轮的进展**。在跑的子卡上要先留协调评论，同步实况：哪些已实现、在等谁放行、本卡可做部分、重申边界。否则它会重复已完成的实现，或空等一个已被满足的批准而再次 block。
- **unblock 即派 worker（即使卡的意图是「主会话自办」）**：dispatcher 只认 assignee 加 status，卡体里写「小喵自办/不派 worker」不阻止 dispatch。主会话要亲手做的活**不要 unblock**：一旦 unblock，default/profile worker 会被派出并与主会话**并行重复作业**。此时正确处置：**留协调评论同步已完成项**（列明哪些已做、产物路径），让它复跑幂等动作后自然做完。读日志/写文档类无副作用，动库/写盘类做成幂等就不怕复跑。只为非幂等动作才停杀（先 block 后 SIGTERM）。另：卡被 live worker 持有时 `kanban_complete` 会被拒（error 提示 expected_run_id/force），等 worker 收束完毕，或由 operator 显式 force。

- **needs_input 闸夜里没人开（10-17 实例）**：有人把「每张完工主会话验收后放下一张」设计成 needs_input 粘性闸。主会话只在用户发言时活着。深夜整条链悬空 11.5 小时，而前四张实测 72 分钟就跑完了。批量串行卡的默认形态应是 dependency 父卡边自动跟单（done→promote→dispatch 无人值守）。人工闸只留给「下一张的内容本身要人拍板」的卡。主人不在场的时段，不许用它串联整条链。——10-18 复发修订（小喵自己踩的，判决入库）：想停掉在跑卡片去「等依赖」，必须先建/挂父边、后 block；父边还不存在时 block，工具会把它重记成 needs_input 粘性（返回字段 rekind_reason=no_open_parent 当场就把答案喊出来了，没人接），此后父卡 done 也不自动放行，夜间悬空 8 小时。对主人承诺卡片走向时，只许承诺工具返回字段背书的档位：block 回执写着 needs_input 粘性的卡，被口述成「一 done 自动 ready dispatcher 接走」是无据承诺——那句「不用为这条 blocked 回执做任何操作」同步标撤回：放行前实际要做 show/unblock/comment 四步才接上。补一刀同族竞态：**unblock 前先读父卡现状态——爹已 done 时 unblock 等于立刻 promote 加秒级 dispatch，卡当场抢跑**（接线时爹恰好完工的常见情形）。要把卡串在某张卡后面，unblock 那一刻爹必须仍在跑；爹已 done 就补挂一张在跑卡为父，或接受抢跑后逐卡回读实况再对主人措辞。停掉指定卡的 worker 进程：遍历 /proc/*/environ 匹配 HERMES_KANBAN_TASK=<task_id> 精确定位 pid 再 SIGTERM，别按进程名猜（多 worker 同 cmdline）。
- **编排描述引用卡体逐字，状态断言带 as-of（10-18 检察官判决入库）**：向主人转述下游卡的走向（『clean 则直通』『不干净就 block』）时，引卡体原文条款或明标「按建卡意图，条款未逐字复核」——凭记忆转述卡体语义属未据断言。『在跑/已核验』是 as-of 快照：coder 首 run 验完 running 后照样撞 3600s 超时回队，全称链核验要说清核验时刻覆盖的字段（status/model/parents），事件推翻之后的状态不算失效但要当回合重验。宣称『已立 X 记录』必须当场指落点（comment id、文件路径+哈希）；依附他物收据的记录（如交接评论内的一条）要点名该评论 id，否则被记为口头宣称。
- **机制首用断言要标「预期」**：dispatcher 自动 promote/spawn、门链自动接棒这类机制行为，在首个 promoted/spawned 事件回执到手前只能表述为「预期会自动，回执到了告诉您」——10-18 实例：「交卷后其六自动接棒」出口时无回执，同轮已承认旁路卡曾推翻链态，属先断言后取证。：主会话没有跨回合的常驻哨兵，只能在自家回合内轮询，回合结束即停。对主人说「监测已挂上」会被当成有后台眼睛盯着，落空一次就失信。正确措辞：worker 交卷由系统推送给主人，主人转达后主会话立即做方向验收。真要跨回合自动盯，就显式建 cron/后台终端，否则不宣称「挂着」。
- **人工中继=断点，多轮审查-修复循环必须卡片自终止**（10-18 实例：计划写「循环直到验收」，卡间交接全押在主会话转接上，结果夜间链条悬空十几个小时）：红队↔coder 这类复审循环从第 1 轮起就建好第 2 轮卡，parents=[上一轮卡]，让 done→promote→dispatch 无人值守；建卡权不是隔离屏障：dispatcher-spawned worker 的注入工具集里虽无 kanban_create 工具，但 terminal 里的 `hermes kanban create` CLI 照用不误——10-18 二验：检察官 worker 用 CLI 自建了修复卡与预建门链卡正面撞车（同父同 assignee 双 coder 并发啃同仓库，dir 卡直写生产树，scratch 卡白烧 token）。预建链与 worker 自建卡二选一：链已预建就在卡体明写「下一轮卡已由主会话预建（卡号 X），你无需也无权另建；verdict 只写 summary/metadata 字段」；要 worker 自建就别预建，并在 worker 交卷后逐卡查重（parents+assignee 相同即重复）。
- **被主人手动挂起的卡 = 后排加未验收，其盘上产物不得借其它动作被动上线**。review 阶段被用户挂起的卡，磁盘上可能已留下未验收的产物。模板、配置、脚本都算。任何会加载该产物的动作都要先停一下：服务重启、批量发布、让下游卡消费都属于这类。动手前先核该卡的挂起状态与交接记录（「先验收实物，再讨论重启」）。重启会把未验收稿带上线，事后要按「谁让它上线的」认账，不要等主人察觉「好像不对」才发现。
- **进度把握被质疑时交「信息源×落笔时间×活体事实」对照表**：主人说「我感觉你进度把握有问题」这类话，别再辩护结论，现场重建账本——枚举每个写状态的地方（审计原文、整改卡、旧报告、代码实物、看板活体、产物文件、快照节），每行用 git author/commit date 挂上落笔时刻，再对当日活体（读码、find 产物、kanban_list 现查）；落笔之后存在触碰涉事文件的提交，即该行过期时刻。根因叙述按转录链走：谁在何时把谁的旧快照抄成了现行说法。表每一行必须带一句白话说明这行说的是什么事（见 delivery-critic-gate 人话闸），引用与时间是证据不是正文。
- **worker 跑得久 ≠ 卡死：下「慢/卡」判断前先读它的日志**：完整 worker 日志在 `~/.hermes/kanban/logs/<task_id>.log`，逐条记录工具调用、耗时与收尾报告。代码写入型 worker 还要看 workspace 文件 mtime/新增测试：日志只有 `Session:`、心跳在、文件却在连续更新，就是在写；连续 10 分钟无新写入再按卡死处理。久跑的常见正当原因：① 全套用例本身长（大仓逐文件串行可达 ~25 分钟，单文件可到 40s）。② worker 正在做 **stash 基线比对**（见下条）。判活体看 heartbeat 连续性与日志末行的当前步骤，不看秒表。据此回复主人前先取证。把正常长跑报成错误结论，比慢本身更糟。
- **重复循环的收尾签名与恢复**：日志末尾出现 `Response dominated by repeated text — stopping the stream mid-loop` 加 `[kanban-worker-exit] rc=1`，进程可能已成 `Zs [hermes] <defunct>`，卡却仍挂 running。处置顺序：① `hermes kanban log <id> | tail` 与 `ps -p <pid>` 取证；② `hermes kanban reclaim <id>` 放回 ready；③ 先验它倒下前是否已提交（`git log` / `git status` / 跑套件），有货就 `hermes kanban complete --force <id> --summary ... --metadata ...` 结案，别急着重跑；④ 没货或只差一小步，就开一张极小的跟进卡，卡体写死「两条命令都过就提交并结案，不许再研究 X」。重复循环多发生在提交后的自检、导入、测试顺序这类歧义上，开放式调查会再次把它送进同一圈。
- **弱模型任务书要带停止条件**：机械卡写「通过即提交，不扩大调查」；否则 35B 会在 `importlib.reload`、测试顺序这类歧义上反复自证。
- **worker 的 `reasoning_effort` 是 profile 级，不是卡级**：机械活把 coder/researcher profile 的 `reasoning_effort` 从 `xhigh` 调到 `medium`（先备份原配置）；xhigh 会让 35B 在导入/测试顺序这类歧义上反复自证。难任务要 high 就单独改配置或开 high profile，不在卡里偷偷放大。
- **并行第二台机器时，第二张卡只做文件不相交或只读分析**：两个 worker 同时改同一仓库并各自 commit 会抢 git index；优先派只读报告卡（`workspace dir` 指文档目录、不改仓库），或给 worktree。并行前逐个核 profile/provider/模型，主会话分别验收。worker 禁用 `git stash`/`git add -A`；`git stash` 会把另一个 worker 正在改的文件卷走。
- **「全套无回归」必须可审计**：套件里本就存在既有失败时，卡规格要写明「先 `git stash` 跑一次基线、逐文件比对」。要证明失败是既有而非本次引入。验收时抽验它给出的基线比对结论：只报「全绿」而基线里本就有红的，等于没验。反之基线一致则是合格证据，不要把既有失败算成回归。

## 相关技能

- `sdlc-review`：评审车道的判决流程（approve/request-changes/escalate）与轮次镜头表。
- `deep-code-review`：被派发评审卡时的工作流本体。
- `git-repo-hygiene`：提交署名与零个人信息红线。
