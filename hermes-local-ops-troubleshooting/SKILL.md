---
name: hermes-local-ops-troubleshooting
version: 1.0.0
author: Nekonya (小喵)
license: MIT
description: "排查本机 Hermes 运维时使用。只要遇到 cron 不触发、调度器冲突、LCM 库损坏或隔离沙箱异常，就主动加载。"
metadata:
  hermes:
    tags: [hermes, cron, gateway, lcm, sqlite, ops]
    related_skills: [hermes-agent, lcm-summary-tuning]
---

## When to Use

本机 Hermes 基础设施出问题时：cron 任务不触发、`hermes cron status` 报警、LCM 库损坏报错、需要装/撤 gateway 服务，或怀疑数据库被写坏；需要体检或编辑指令面（system prompt 体量、技能索引描述）时也读这份。

生产栈**当前状态**（服务在不在跑、配置改到哪了）不在本 skill——唯一账本 = `~/Documents/Hermes/运维状态_20261006.md`。本 skill 只管排障方法。

# Hermes 本机运维排障

## cron 不触发：先分清谁在驱动调度

- **三种进程的官方分工**（源码 `hermes_cli/gateway.py`、`web_server.py`、`main.py` 实测核对）：`gateway run` = 消息平台接入 + **cron 调度**（唯一 systemd 路径的调度器）；`hermes serve` = headless 后端，**无浏览器 UI**（打开端口只看到提示语）；`hermes dashboard` = 后端 + 浏览器 SPA 二合一（桌面应用的旧回退路径就是拉它当后端）。给桌面远程连后端用 serve 或 dashboard 都行；要 cron 必须有 gateway run 或桌面自管后端。
- **ticker 只在两条路径启动**：① `gateway run`；② 桌面应用**亲手拉起**的后端（`web_server.py` 的 `is_desktop_owned_backend()` 门）。**systemd 起的 serve/dashboard 永远不 tick cron**——unit 名叫 hermes-gateway 但跑 serve/dashboard 时，cron 就是静默死亡。判定调度器是否活着看 `~/.hermes/cron/ticker_heartbeat` 的 mtime + PID，这是唯一铁证。
- `hermes cron status` 只认 gateway 心跳：桌面自管后端在驱动时它会误报「No scheduler is serving」。status 的否定 ≠ 任务不会响。
- **判定方法 = 实测，不信任何一方的声明**：建一个 3 分钟后的一次性任务（`hermes cron create "3m" "<短回复>" --repeat 1 --deliver origin`），到点看响不响。这是唯一可靠的验证。
- **双调度器是事故源**：`hermes serve` 与 `gateway run` 在同一 HERMES_HOME 并存时，两个调度器互抢工——cron worker 被对方 SIGTERM、fire-claim 双重认领、结果被丢弃（上游已知 bug，修复方向 = 每 home 单一调度器所有者）。装用户级 gateway 前先确认桌面/serve 后端是否已在跑；已在跑就不要再装。
- 主人自己用 systemctl 管理的服务**不要擅自动**：没有 sudo 权限就看不到它的日志，改坏了无法自证。要重启先请主人跑。
- **`hermes gateway install --system` 会「修复」同名 unit**：它检测到 ExecStart 与当前安装器模板不符就覆盖（「Repairing outdated system service」），手工改的 ExecStart（如换成 dashboard）会被冲掉。想让 dashboard 常驻必须给它**独立命名的 unit**，别复用 hermes-gateway.service。
- **sudo 跑 hermes 的两个坑**：sudo 的 PATH 不含 `~/.local/bin`（command not found）；即使用绝对路径，启动器的隔离 Python 在 root 下会因 uid 所有权检查拒绝加载依赖（`ModuleNotFoundError: ruamel`）。可靠写法：`sudo <repo>/venv/bin/python -m hermes_cli.main <子命令>`——unit 的 ExecStart 用的就是这个 venv，依赖必齐。

## LCM 库损坏（反复发生，按流程处置）

1. **确诊**：`sqlite3` 只读 URI 连 `~/.hermes/lcm.db` 跑 `PRAGMA integrity_check`；`database disk image is malformed` = 坏。同时看 `~/.hermes/logs/agent.log` 的 `Failed to load plugin 'hermes-lcm'` 时间戳，定位损坏窗口（首次报错时间 ~ 最后一次正常写入之间）。
2. **找备份**：每日快照在 `~/.hermes/lcm.db.daily.YYYYMMDD`。恢复前必须**逐份验证**：integrity_check = ok + 关键表行数合理（messages / summary_nodes）。别信文件名，信 PRAGMA。
3. **恢复 = 停写 → 换文件 → 验证 → 重载**。⚠️ 停服务会杀掉 agent 自己（见「生产停机窗口铁律」）——换文件必须由主人跑脚本；无人值守时宁可让系统跑在降级态（内置 compressor）并报告。全量抢救的完整流程见「LCM 库全量抢救流程」节。
4. **第 N 次损坏要升级问题**：同一库反复损坏（本机已六次，均发生在多进程活跃使用期）时，「再修一次」不是正确答案——立根因排查项（无界增长 6MB→122MB/12天 + 多写者 WAL 是结构性候选，修剪/轮转工程待立项）。第六次的实际解法：.recover 全量抢救 + 升级 hermes-lcm → lcm-x 0.26.0（同一作者的存储加固后继，3000+ 提交的存储修复不在旧版里）。
5. 损坏期间所有依赖 LCM 的验证（如 tiered 的 inner=lcm 臂）实际跑在 compressor 上——对照实验设计必须按真实状态写判据。

## FTS5 损坏的修复（`messages_fts`/`nodes_fts` 索引树坏，主表可读）

- **失败路径（别踩）**：`sqlite3` CLI 或 Python 直接 `DROP TABLE` 时，若 FTS5 的四个 shadow 表（`_data`, `_idx`, `_docsize`, `_config`）仍在，会抛 `may not be dropped`；Python 脚本用 URI 连库时，一碰 shadow 表就报 `database disk image is malformed`（因为主表 B-tree 也有散落坏页）。
- **可修复内容**：FTS5 的 FTS 索引树 + 触发器（`messages_fts`/`nodes_fts` 及对应触发器）；主表 `messages`/`summary_nodes` 的数据本身未坏。
- **验证判据**：`SELECT COUNT(*) FROM messages_fts MATCH 'plan mode'` 能出数字；`PRAGMA integrity_check` 不再报 `malformed`（仅对 FTS5 表）。
- **修复步骤（CLI）**：
  1. 只读模式验证主表：`sqlite3 lcm.db "SELECT COUNT(*) FROM messages;"` 出数字（如 33969）。
  2. 停写：确保 gateway/lcm-compress 进程不在写（`pkill -f "gateway run"` 或重启服务；生产只读时慎用）。
  3. 备份：`cp lcm.db lcm.db.bak_YYYYMMDD_HHMM`。
  4. 重建 FTS5（key：先删 shadow 表，再删主 FTS5 表，再重建）：
     ```sql
     DROP TABLE IF EXISTS messages_fts_data;
     DROP TABLE IF EXISTS messages_fts_idx;
     DROP TABLE IF EXISTS messages_fts_docsize;
     DROP TABLE IF EXISTS messages_fts_config;
     DROP TABLE IF EXISTS messages_fts;
     CREATE VIRTUAL TABLE messages_fts USING fts5(content, content=messages, content_rowid=store_id);
     INSERT INTO messages_fts(messages_fts) VALUES('rebuild');
     -- 触发器用 CREATE TRIGGER 语句重建（见 hermes-lcm/plugin.yaml 内源码）
     ```
  5. 验证：`sqlite3 lcm.db "SELECT COUNT(*) FROM messages_fts MATCH 'plan mode';"`。
  6. 重载：重启 gateway/dashboard。

## 生产停机窗口铁律（2026-10-05 事故实证）

- **agent 进程住在 `hermes-dashboard.service` 的 cgroup 里**（`/proc/self/cgroup` = `0::/system.slice/hermes-dashboard.service`；谱系：回合 shell → dashboard 后端本体）。`systemctl stop hermes-gateway hermes-dashboard` 会把 agent 自己一起 SIGTERM——回合死在 stop 之后，无法汇报、无法重启服务（实证：19:49 停机，19:58 主人手动拉起，停机 8 分 52 秒）。
- **主人裁定（最高优先级）**：任何停生产操作必须先停下汇报获准；停机任务一律写成带检查点的脚本落盘，何时停、何时跑由主人决定；主人从自己的终端跑（他的 shell 不在服务 cgroup 里）。
- agent 获明示代跑时：`sudo systemd-run --scope --unit=<名> bash 脚本`——脱离服务 cgroup；`nohup`/`setsid` 无效（杀的是 cgroup 不是会话）。
- 停机脚本必须带失败兜底：`trap` 在 EXIT 时查服务状态、非 active 就 `systemctl start` 拉回，保证任何一步失败都不留停机残局。
- 范例：`~/Documents/Hermes/CC_vs_Hermes_调研_20261004/切换_lcmx_20261005.sh`（七步检查点 + trap 兜底，2026-10-05 主人执行成功，全程约 1 分钟）。
- **上线（让新插件代码生效）的脚本骨架**：守卫（目标版本号 + 工作树干净，不满足直接退出、不动服务）→ 宽限秒数 → 重启 gateway + dashboard → 验证 → 回滚备忘；日志 tee 落盘。验证「新代码已加载」要抓**只有新代码才会写出的产物特征**（新格式日志字段、新版本号），服务 active ≠ 新代码在跑——本机模式：激活标记格式可当版本指纹（旧代码只有 `ACTIVE inner=…`；新代码带 requested=/via= 字段），重启后 `tail -n +$((旧行数+1))` 只看新增行。
- **agent 侧 sudo 开关**：默认未启用——`~/.hermes/.env` 里 `SUDO_PASSWORD` 是注释行，`sudo -n true` 报 "a password is required"。未启用时停机/上线脚本一律交主人终端跑；若主人启用了它，走 `sudo -S` 从 stdin 读口令（`echo "$SUDO_PASSWORD" | sudo -S …`），口令绝不进命令行与日志。

## systemd drop-in 陷阱：缺 [Service] 段头 = 静默不加载（10-05 实证）

- drop-in 文件必须以 `[Service]` 段头开头；只写一行 `Environment="X=Y"` 会被 systemd **静默忽略**（段外裸键不报错不生效），而 `systemctl cat` 照样把文件拼出来显示——「cat 显示、show -p Environment 不认、重启也没用」三症状同源。
- 修好段头后 daemon-reload，**重启前**就能用 `systemctl show -p Environment` 验证（loaded 配置即时更新）——这是零停机验证点，不用拿重启试错。
- agent 在 execute_code 上下文里没有 sudo tty（密码缓存只在本 terminal 上下文）；别试猜密码，直接把需要 sudo 的步骤写进脚本交主人跑。
- kill 服务主进程（单 PID）≠ systemctl stop（杀整个 cgroup）：agent 会话进程是 dashboard 主进程的子进程，kill 主进程后 agent 被 reparent 存活——但这是**未批准的生产动作**，一样违反停机铁律；agent 存活纯害侥幸机制，不许当手段用。

## LCM 库全量抢救流程（2026-10-05 第六次损坏实战）

前置：系统 sqlite3（Ubuntu 3.45.1）**没编 sqlite_dbpage**，`.recover` 直接报 `no such table: sqlite_dbpage`。自编二进制：

```bash
curl -s -O https://sqlite.org/2024/sqlite-amalgamation-3450100.zip && unzip -o -q sqlite-amalgamation-3450100.zip
gcc -O2 -DSQLITE_ENABLE_DBPAGE_VTAB -DSQLITE_ENABLE_DBSTAT_VTAB -DSQLITE_ENABLE_MATH_FUNCTIONS \
    -DSQLITE_ENABLE_FTS3 -DSQLITE_ENABLE_FTS5 -DSQLITE_ENABLE_RTREE shell.c sqlite3.c \
    -o sqlite3-rec -lpthread -ldl -lm
```

流程（全部在副本上操作，原件只读；scratch 目录 24h 无活动会被清，成品要拷去耐久位置）：

1. 三件套快照 + sha256 对账（原件 vs 副本逐字节一致才算备份可信）。
2. 全量恢复：`sqlite3-rec "file:坏库?mode=ro" ".recover" | sqlite3-rec 恢复.db`（输出里 sqlite_sequence/sqlite_master 的 Parse error 是无害噪音）。122MB 约 1 秒，integrity_check = ok。
3. 对账：恢复库各表行数 ≥ 最近健康日备（messages/summary_nodes/metadata），是超集才算赢；metadata 里 schema_version 应为 5（lcm-x 的 refuse_schema_version_too_new 守卫同值放行）。
4. **`.recover` 不重建 FTS5 虚表**：影子表（_data/_idx/_docsize/_config）和触发器都在，虚表对象消失。修法：DROP 四组 shadow 表 → 用健康日备的 DDL 重建两个虚表（external content 挂主表）→ `INSERT INTO xxx_fts(xxx_fts) VALUES('rebuild')` → MATCH 冒烟出数字。
5. VACUUM 压实 → `install -m 600` 上岗 + 留耐久副本（.bak）+ sha256 记录。
6. `.dump` 备选路径：输出以 `ROLLBACK; -- due to errors` 结尾，直接回放=整段回滚；`sed` 末行为 COMMIT 再回放可用但劣于 .recover，仅作兜底。

## 宿主配置写回器（已知破坏形态）

运行中的 GUI 宿主会在外部编辑 config.yaml 后 ~1s 内覆写回内存态，且写回会丢段头（`context:`/`dashboard:`）或写入控制字符 U+0001。集成测试要钉死配置就用隔离 `HERMES_HOME`（配置副本 + 符号链接 plugins + 全新 state），不碰真实配置。

## 隔离沙箱探针：先复刻生产启动链，再设 HERMES_HOME

在本机用隔离 `HERMES_HOME` 验证插件/引擎（装载、register、解析实验）时，不要直接在裸 `python3 -I` 里 import 宿主模块：第三方依赖来自 PM 依赖代际，不在解释器本体内。典型症状：`ModuleNotFoundError: No module named 'ruamel'`（`hermes_yaml` 模块级硬依赖），插件装载整链失败、常被吞成「engine not available」。

**正确顺序（= 生产启动链，缺一即败）**：

1. `sys.path.insert(0, '<hermes-agent 根>')`；
2. `from pm.environments import activate_dependencies; activate_dependencies(Path('<hermes-agent 根>'))` —— 把 PM 选中的代际 site-packages 挂上 `sys.path`（本机实测为 `~/.hermes/installs/<id>/environments/<id>/venv/lib/python3.14/site-packages`）；**必须在任何 hermes 模块 import 之前**。入口就用这个函数——别走 `pm.activate()`：它会先经 `plugins_state → utils → hermes_yaml`，在依赖挂载前撞同一缺失。激活成功判据：随后 `import ruamel` 通过；
3. 设沙箱 `HERMES_HOME`（`get_hermes_home()` 逐次读 env、无缓存——实测；但要在首次调用前设好），并清掉会漏进 shell 的服务 env（如 systemd drop-in 的 `TIERED_INNER`）；
4. 之后才 import 被测模块并跑装载。

**防误载真件的守卫（必带）**：装载前断言 `get_hermes_home() == 沙箱`；装载后断言目标模块 `__file__` 落在沙箱目录下——否则可能已把生产引擎在本进程里执行了。

**三个连带事实**：

- 插件加载器**复用 `sys.modules`**（`plugin_loader` docstring 原文 "reusing sys.modules when loaded"）——**改插件文件不会热生效**；新代码在进程重启后的装载才生效。汇报必须区分「已改」与「已生效」。
- 激活标记写在 `$HERMES_HOME/cache/` 下：沙箱探针不污染生产日志；反向也应用 tail 核验探针有没有留痕。同一进程为**每次 agent 初始化**重跑 register()，日志逐行累积（同一 pid 多行属正常，不是异常重启）。
- `hermes plugins validate` 输出的 `◆ Isolation — runs in the plugin host (plugins.isolation: host)` 是**静态 host-ready 判定**（插件只经对象基面通信、可安全入驻宿主进程），**不是**本机运行模式；本机模式看 `plugins.isolation` 配置（缺省 `in_process`）并实测 register 跑在哪个进程（激活日志的 pid）。

起步模板：`templates/hermes_sandbox_probe.py`（复制后改 fake 引擎与断言）。

## 插件「loaded but no instance found」= 启用开关没开

- 日志三连 `Context engine 'X' loaded but no engine instance found` + `falling back to built-in compressor`，且重启后**没有任何**该插件的激活日志（连 register 的报错都没有）= 插件根本不在启用列表——桌面插件菜单的开关写 config.yaml 的 plugins 段，由主人切换；不是代码坏了。别去复现 import（复现环境缺依赖代际会另报 ruamel 之类假线索，见下节沙箱探针）。
- 修复后验证只看一件事：重启/重载时间戳**之后**出现插件自己的激活日志行（如 `factcheck hook active` / `tiered context engine active`）。三态分开汇报：盘上代码已改 ≠ 进程已注册 ≠ 功能已跑过（状态文件/实际调用产物才算第三态）。
- 良性噪音识别：`tried to register a context engine, but one is already registered` 出现在通用插件路径（内层引擎先占位），context_engine 专用加载路径仍会拿到包装实例——引擎激活行在 = 无害，别当故障追。

## 插件「注册了但从不触发」：按触发链逐环对质，别猜

- 症状：激活日志在、会话每轮都过 hook，但功能产物（状态文件、调用日志行）始终不出现。第四态补全三态链：盘上已改 ≠ 已注册 ≠ 每轮被调用 ≠ **触发条件真的满足过**。
- 排法 = 读源码把触发链列成序列（豁免过滤 → 计数器 → 阈值 → 实际调用），拿**本会话真实回复样本**逐环喂进去测，哪环断了在哪环修。禁止从「N 轮早该满了」直接跳到「hook 没挂上」。
- 红线坑：**确定性表面线索的豁免正则必须拿它要豁免的那类文本的常见格式做对抗测试**。单星号旁白模式会命中 markdown `**粗体**` 的内侧——报告体回复整轮被静默豁免，计数器一次都不加。加任何豁免规则时同步写回归用例：代表性工作体文本（粗体、行内代码、引用）必须**不**豁免，真旁白/颜文字必须照豁免。

指令面体检（请求转储测体量 + 技能索引描述来源与批量改法）：见 `references/instruction-audit.md`。
本地服务 prompt 缓存破坏（每轮全额重预填充、0 reused 阵发段）的法医与修法：见 `references/prompt-cache-forensics.md`。
