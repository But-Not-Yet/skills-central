---
name: hermes-context-engine-plugins
description: "开发或审查 Hermes 上下文引擎插件时使用：ContextEngine 实现、装饰器包裹。只要要写/改 context.engine 插件、评审其是否达标或排查引擎没生效，就主动加载，即使用户没明说 ContextEngine。"
version: 1.0.0
author: Independent Researcher
license: MIT
metadata:
  hermes:
    tags: [hermes, context-engine, plugin, code-review]
    related_skills: [hermes-desktop-plugins, hermes-local-ops-troubleshooting]
---

# Hermes 上下文引擎插件：开发与审查

覆盖 `agent/context_engine.py` 的 `ContextEngine` 实现，包括装饰器包裹型插件（外层加确定性层、内层委托给别的引擎）。宿主代码只读，插件代码在 `$HERMES_HOME/plugins/<name>/`。

## When to Use（何时用）

- 写或改一个 context-engine 插件（`context.engine: <name>`）。
- 审查这类插件是否达标、找缺陷。
- 调试「引擎没生效 / 悄悄回落内置 compressor」。

## 第一步：拿契约与调用点，别猜

先读宿主真相，再动手：

- `agent/context_engine.py` — ABC。四个抽象方法：`name`、`update_from_response`、`should_compress`、`compress`。其余是带默认实现的钩子：`should_compress_info`、`prune_tool_results_only`、`select_context`、`on_session_start/end/reset`、`on_turn_complete`、`clone_for_agent`、`update_model`、`get_status`、`get_tool_calls`。
- 宿主每轮/每请求实际调哪个动词、提交契约是什么 — 见 `references/host-contract-map.md`（含各调用点行号与提交判据）。

## 跑插件单测（本机实测命令）

插件内的测试文件常只把 `$HERMES_HOME/plugins` 塞进 `sys.path`，还需要 `hermes-agent` 在路径上才能 `import agent.context_engine`。用宿主 python 加 `-I` 隔离 venv：

```bash
cd ~/.hermes/plugins/<plugin>/tests
python3 -I -c "import sys; sys.path.insert(0,'/home/alonzo/.hermes/hermes-agent'); exec(open('test_x.py').read())"
```

`-I` 阻止 venv 注入。缺 `hermes-agent` 路径会报 `ModuleNotFoundError: No module named 'agent'`。脚本模式 `python -m pkg.tests.x` 在无 venv 时也会因路径缺 `agent` 而失败，用上面的 `exec` 形式最稳。

**红绿测试会假绿**：插件测试常把 `$HERMES_HOME/plugins` 塞进 `sys.path`，import 的是**已安装副本**，不是你正在改的树。验证「修前红、修后绿」时，先把 `sys.modules['<plugin>']` 预绑到导出树（`git archive <base>` 到 scratch），或把 `HERMES_HOME` 指到沙箱；朴素复制树跑出来的绿不可信。

- **测试文件必须自带路径自举**：每个测试文件顶部自己写 `sys.path.insert(0, os.path.expanduser("~/.hermes/plugins"))`，再 import 插件；靠别的测试先插路径会让单文件运行报 `ModuleNotFoundError`，全量套件却假绿。
- **包命名空间用模块级 `__getattr__` 懒转发**：`core/__init__.py` 里 eager `from ..engine import TieredEngine` 在测试 `importlib.reload(engine)` 后会绑到旧类，身份断言失败；改成 `def __getattr__(name): from .. import engine; return getattr(engine, name)`，让命名空间跟当前模块走。

## 插件能修到哪一层：三条硬边界

写路线图前先分清「请求侧」与「持久侧」。这三条不是实现细节，是宿主契约：

1. **`select_context` 只改请求，不改持久历史。** ABC docstring 明确：返回列表是 request-only，`conversation_messages` 只供参考、不许改；宿主还会做结构克隆，防止引擎写穿到持久历史。空消息、摘要顺序错位这类**持久形态**问题，插件只能修请求副本，根因要回宿主或内层引擎修。
2. **上下文引擎不是一等公民。** 宿主用私有属性代理、`getattr(type(compressor), name)` 类级探测、两条模块名装载来使用插件。包装器只能接一张不断变长的代理表；每个宿主改动都可能静默绕过它。这是结构性税，不是单点 bug。
3. **调度与资源模型不在引擎里。** `ContextEngine` 没有租约、优先级、抢占、单槽位这些概念。插件最多发提示卡；拦不住 dispatcher 并行，也拦不住主会话停掉承载自己的服务。

结论：插件能修模型看到的请求、能加确定性导向；持久历史与调度要动宿主。要动就只提三个小接缝：装配定稿前给引擎一个规范化入口、给引擎一等公民接口、给插件一个单槽位租约。先插件、后契约，别先 fork。

## 包装器（装饰器）实现的硬规则

这些都踩过，且不是可选的：

- **token-state 属性必须装真描述符，不能靠 `__getattr__` 兜底**。ABC 把 `last_prompt_tokens`、`threshold_tokens`、`context_length`、`compression_count`、`threshold_percent` 等定义为带默认值的**类属性**，普通属性查找命中默认 0，`__getattr__` 永不触发。要在类体后 `setattr(cls, attr, property(get,set,del))`。而且宿主会把 `model_thresholds` 与几个下划线开头的私有属性直接写在选中引擎上，必须逐个显式代理 。用一个白名单常量维护它们。
- **`__getattr__` 默认不转发下划线属性**。宿主写的私有属性（例如 `_last_compress_refused_would_grow`）不会自动落到内层，除非显式代理。
- **包装器的 `compress` 必须声明 `**kwargs`（或全候选签名）**。宿主按**选中引擎**的签名过滤压缩参数再调用。窄固定签名会让宿主静默丢掉内层支持的参数。包装器收到全量后再按**内层**签名过滤一次。过滤逻辑镜像宿主 `_supported_compression_kwargs`（`inspect.signature`，有 `VAR_KEYWORD` 就放行全部，否则按参数名取交集）。
- **`prune_tool_results_only` 的提交契约**：无操作必须返回**输入对象本身** + 计数 0。要生效必须返回**新列表对象** + 非零计数。宿主只在「新对象且计数非零」时换列表。返回新对象配 0、或同对象配非零，都会被忽略。
- **`on_session_reset` 必须复位包装器自身的本地状态**（例如熔断器的连续失败计数与开闸位）。宿主要在 `/new`、`/reset` 会话边界驱动 `on_session_end → on_session_reset → on_session_start`。ABC 默认实现本就会清计数，只转发内层就把这份语义丢了。导致故障开闸后新会话继续无自动压缩。
- **解析内层引擎时，引擎名 ≠ 插件目录名**。目录查找走 `user_plugins_dir()/<name>`。目录叫 `hermes-<name>` 时要靠 `hermes-` 前缀兜底。第三路「通用插件系统按 `name` 严格相等」忠实镜像宿主，但对别名（同一引擎的旧名/新名）会脱靶 。若引擎名会随版本/配置变，别名集匹配比硬写默认值稳。
- **`register()` 里 catch 装载失败再 return 会造成静默降级**：宿主按自己的回落规则改跑内置 compressor。用户侧可能只看到一句 WARNING。配置指名了你的引擎却拿不到内层引擎，是丢整条链路，不是小错。失败要响亮暴露（日志 + 可见状态）。
- **`select_context` 每请求跑，且在请求 sanitizer 与 cache-control 之前**。返回替换列表会**从改动点起改变 prompt cache 前缀**（断点在选中列表上重推导），所以变换必须确定性。纯内存、无 IO，且不做会自变的决定。

## 单槽位注册：配置不等于生效

宿主只允许一个 context-engine 插件占槽。`ctx.register_context_engine(engine)` 在槽位已被占时只打 WARNING 并返回，不抛异常；后注册的包装器会静默失去引擎功能，而 `context.engine: <wrapper>` 仍可能写在配置里。

- **注册后必须回读槽位身份**：`holder = getattr(getattr(ctx, "_manager", None), "_context_engine", None)`；只有 `holder is engine` 才写 ACTIVE/打成功日志。否则写 `DISABLED slot held by <holder>`，并暴露给用户。不要因为 `register()` 被调用过就当作激活。
- **内层插件先注册时，包装器不能靠内层名配置自动赢**：`hermes-lcm-x` 这类内层插件可能先在目录扫描里注册；`plugins.enabled` 的列表顺序不保证加载顺序，宿主按目录名排序。先查 gateway 日志的 `tried to register a context engine, but one is already registered`，再决定组合方式。
- **包装已注册引擎，不要新建第二个内层引擎**：新建第二个 LCMEngine 会造成双份 ingestion/双写库风险。要么宿主提供组合 API，要么让内层插件在 wrapper 模式下跳过注册，要么原地包住已经注册的 holder 并验证 holder 身份；不要只改 `context.engine` 配置。
- **activation marker 不能自证**：marker 文件由插件自己写，注册被拒时仍可能写 ACTIVE；它不是运行时证据。验收看三样：gateway 日志的注册警告、`_manager._context_engine` 身份、真实请求里包装层是否被调用（探针/输出差异）。marker 文件损坏或并发写 NUL 时更不可信。
- **排查顺序**：`context.engine` 配置值 → 启用插件列表 → gateway 启动日志的注册警告 → holder 身份 → 真实请求探针。配置值只说明意图，不说明槽位。

## 后台模型调用的槽位成本（单槽位部署必读）

- **「off the hot path」只保证不阻塞当前线程，不保证不抢下一个 turn 的推理槽位。** 本地单模型单槽位部署里，后台检察官、评分、复核调用与主会话排同一个槽；按「线程异步」算会低估到离谱，必须按「槽位预算」算。
- **调用数按代码路径算，不按「每 N 轮一次」算。** 评分管线常见乘法：每条攻击 K 次采样 + 每对攻击双序各一次 = `K·A + A(A−1)` 次/判决。一次 10 判决、33 条攻击的会话就是约 187 次评分调用，加判决本身约 197 次单槽位调用。
- **在线路径只留一次判决调用；评分/校准移到离线批处理**（独立脚本读归档，默认关）。默认开着的评分管线是单槽位部署的隐形税。
- **后台任务要单飞租约**：主调用在飞时直接丢弃本次，不排队；一次长超时会把整个会话拖住。租约状态写一行日志，便于回查。
- **报成本给「调用次数 + prompt tokens + 估算依据」**，并标明是实测还是按代码路径估算；不要把估算写成实测。

## 思考剥离层：边界、粒度、路由

**边界——Anthropic 硬规则只有一条，落在末轮**：启用 thinking 时。**最后一个** assistant 消息必须以 thinking 块开头（位于最末一组 tool_use/tool_result 之前）。**更早轮**的 thinking 只是「recommend」，可省略。所以「只保留最后一个 assistant 的思考、剥掉更早的」**与硬规则一致，不是主动致错**。

**成本面**：4.6 及以后保留历史轮 thinking 并按输入计费，4.5 及更早服务端剥离。剥旧思考省的是这部分输入计费，属权衡不是缺口。

**Anthropic 官方客户端（Claude Code）不做逐轮剥旧思考**。它只做三种 400 规避（孤儿 thinking-only 消息、末条 trailing thinking、凭据变更后签名字）。并在支持模型上用 context-management beta **请求保留**历史 thinking。

**真关口是粒度，不是边界**：字段级 `pop(key)` 删整块思考，删不掉 thinking 文本**内部**的行内孤儿标记（开/闭不成对）。那份标记留在 `content` 里照样把下游正文误判成思考。修法属**标记级卫生**（入库成对保证 + 剥离路径残余清扫），落点在组装层与内层引擎入库/升级边界。不在思考剥离层本身。

**Kimi/DeepSeek echo 族相反**：要求每条 assistant 带 `reasoning_content`（空串 400，用单空格占位）。

官方原文、按模型的保留政策、Claude Code 源码函数与行号见 `references/thinking-block-preservation.md`。

> 反面教训（先前的错误论断，已改正）。曾据『官方校验先前的 thinking 原样回传』判「剥旧思考在 Anthropic 原生路由会主动致错」——把「recommend」当成了硬要求。定边界前必须逐字读官方原文，确认硬要求落在**谁**身上。

## 过滤/改写放哪层：三层候选与成本口径（设计咨询速查）

被问「能不能用插件实现过滤/改写」「会不会太慢」时：先列层给覆盖面，再给实测数字，最后给建议。

- **候选层（按覆盖面排序）**：① 包装器 `select_context` 每请求跑且在 sanitizer 之前。覆盖一切进模型的文本（含回放历史、工具结果回流、任何来源）。② 内层引擎的入库/升级边界——管库内与检索面卫生。「成对保证」只能在入库面表达（请求面只能清扫，不能拒绝入库）。③ 通用插件钩子——`transform_tool_result`（工具结果产出处变形）、`transform_llm_output`（模型输出替换）。`pre_llm_call` 只注入上下文、**不能过滤**（契约已核）。`transform_llm_output` 收到 `response_text/session_id/model/platform/turn_id`，返回替换字符串，首个非空返回值生效；它在 assistant 行持久化之前跑，所以在同一条回复里追加 `::preview` 会话卡要在这里做，`post_llm_call` 在它之后跑、来不及进本轮。HTML 卡片契约走 `chat-inline-statusboard`，插件只生成文件与指令，不让模型重写卡片。
- **成本口径（先测再答）**：文本级清扫是线性内存操作，用 B5 式 micro-benchmark 给数——校准量级：~800KiB 请求（几百条消息）下。`"命中字符" in text` 快路径 + 单正则替换 ≈ 0.1 ms/遍，最坏（全命中）≈ 0.2 ms/遍。相对秒级生成可忽略，且与宿主每请求既有的 sanitizer 同类。汇报用「实测毫秒 vs 生成秒级」，不用形容词。
- **实现纪律**：只在命中时新建对象（copy-on-change，不动入参）。模式表按目标词表收紧，防误伤代码/标记语言里的正常尖括号。落地走 `fix-batch-workflow` 的批次形状。

**复核卡（trust card）的检查器契约**：`check_text` 必须传入已知 `base_dir`（hook 调用不是 CLI，不能省）；路径正则要保留完整相对路径（只从 `/` 或 `~` 起匹配会把 `tests/foo.py` 截成 `/foo.py`）；`build_cards` 必须保留 `CheckResult.status` 与 `evidence`，文案区分 UNVERIFIED 与 FAIL；hash 正则排除纯数字日期串和文件名片段。验收必须打到 `post_llm_call`/`transform_llm_output` 端到端，不能只测 `check_text` 单体。实现细节与测试矩阵见 `references/tiered-kernel-map.md` 的复核卡节。

**复核卡的两个致命口子**（消误报时最容易踩）：

- **自噬循环**：注入的提醒文本（如 `【导向提醒】…`）会进模型上下文，模型复述进下一条回复，下一轮扫描又扫到同类字符串，形成「假警告 → 按钮复核 → 新回复又带提醒 → 再假警告」的死循环。`cards.py` 只是渲染器，不负责过滤；扫描输入是 `check_text(assistant_response)`，输入是模型输出。修法：在 `check_text` 之前剥离文本中已有的提醒行，或在注入时打来源标记、扫描时按标记排除。两种做法都要保证真实的、非提醒来源的 hash/path 仍能被检出——不能把过滤做成「一刀切全关」。
- **消误报不能靠抬高长度下限**：把 hash 正则从 `{7,40}` 收紧成 `{9,40}` 能消掉日期误报，但会丢掉 git 默认短 hash（7–8 位，`core.abbrev` 默认值）的全部覆盖。正确修法是保留 `{7,40}`，只排除「纯数字字符串」和「YYYYMMDD 形态的 8 位日期」。判定矩阵必须实测：7 位真实短 hash 要检出、8 位纯日期和纯数字要排除、8 位含字母片段按判据处理。

## 记忆引用审计（R7 类需求）

用户要求“模型引用既往记忆时必须带凭证”时，分两层，不要把它做成第二个事实核查器：

- **确定性层每轮跑，不花模型**：只解析 `ctx://` / `mem://` token，校验 session、`sha16`、上下文包含、TTL；不能核验时标 `unverifiable_source`，不许伪装 PASS。成员检查要用本轮实际装配的 `conversation_history`/prompt snapshot，不能只看全局记忆库；记忆在库里但被上下文切掉，模型引用它就是 `not_in_context`，要求先 `lcm_recall`/`lcm_expand`。
- **语义层搭现有检察官，不另起模型**：单槽位部署里不要为了“这句话是否来自记忆”再起 embedding 或小模型。把“回复原文 + 已校验 token + 违规摘要”作为可选段附加到现有 prosecutor 的同一趟 prompt，解析可选的 `memory_audit` 字段；旧 verdict JSON 保持兼容。确定性检查每轮，语义完整性跟检察官 cadence，二者别混成一个大黑盒。
- **只检查标注是不够的**：token 检查只能验证“有标注的引用”，模型完全可以不标注。未标注记忆断言的识别必须靠模型审计（可搭现有检察官），或在协议层强制结构化输出；不要把“token 全绿”说成“事实核查通过”。
- **哈希只证明“看过”，不证明“支持”**：hash/上下文命中只说明引用存在；断言是否被该记忆支持，仍是语义判断。摘要节点是 S4，不是原文证据；需要原文就展开，不能靠摘要冒充 E3/E4。
- **配置键必须被消费**：`plugin.yaml` 里新增的 `memory_citation.enabled` 只是声明；必须在 hook 代码里 `_cfg(...)` 读取并加 env kill-switch/测试。声明了却没人读，就是假开关，验收时按未实现处理。
- **包装器参数要透传**：给 `_run_prosecutor` 加新参数（如 `memory_section`）时，必须同时改 `_guarded_prosecutor` 的签名和 `run_guarded` 的 lambda；只改内层函数会让 R4 单飞路径静默丢掉新功能。rebase 时保留 guard 包装器，不要用旧调用替换它。
- **S4 是设计约束，不是代码事实**：当前 `memory_protocol` 没有 `tier` 字段；要强制“摘要不能当原文”，必须在校验器里加 source tier/coverage，否则只能标为设计约束，不能写成已实现。


## 审查这类插件的顺序

0. **判「某层有害/多余」之前，先回一手来源定意图与边界**。回**设计讨论原文**确认这层的意图（为什么做它、哪条边界是设计如此），再拿**官方规则原文**定边界。两条禁令。① 不拿代码 docstring/注释的自述当设计意图（它是作者的自我描述，可能过时，或本身就是被质疑的对象）。② 不拿官方的「建议/recommend」当硬规定（硬要求通常只有一条，逐字读清它落在**谁**身上）。违任一条都会产出被撤回的判定。
1. 跑健康自检（**先核槽位 holder 身份**，再看激活标记、调度器心跳、库完整性、config 里的 `context.engine`；标记可能是插件自写的假阳性）。
2. 全读主审源码 + 对照面（宿主 ABC、各调用点、内层引擎关键函数）。
3. 逐条对照任务书/规格的验收判据，给「达标/存疑/不达标」+ 行号。判据以原文为准，禁事后重解释，测不了的标「无法验证」。
4. 缺陷猎捕：正确性 → 行为偏差 → 健壮性 → 风格，按严重度排。
5. 检索最新实践再评判，结论带 URL 与日期、标已核验/未核验。
6. 出改进清单（只列不改），每条给问题 + 证据行号 + 改法 + 风险，并设计沙箱可跑的最小复现实验。

详细调用点行号、提交判据表、审查清单模板见 `references/host-contract-map.md`。

## 通用陷阱

- **进程内先 import 后读 `os.environ` 的模块级常量会被缓存**。插件在 import 时读环境变量（例如内层名默认值），systemd drop-in 能覆盖，但 CLI 直跑/测试/进程内改 env 行为不一致。要在注册/构造**调用时**读。
- **读大型源码文件要分段读**。整文件读取的结果会被上下文管理层自动存根成一行占位符。被存根后回**原文**重读，结论不许建在存根或摘要上。
- **同一插件可能被宿主装载两次**（通用插件系统一份 `hermes_plugins.<name>`，context-engine 目录路径一份 `_hermes_user_context_engine.<name>`）。**两份的钩子命运不同**：只有通用系统那份的 `register_hook` 真的注册；目录路径那份拿到的是 `_EngineCollector`，它继承 `plugin_loader.NoopPluginContext`，只重写 `register_context_engine` 与 `register_command`，基类里 `register_tool = register_hook = register_cli_command = register_memory_provider = _noop`。
  - 后果一：**`plugins.disabled` 只关插件，不关引擎**。`config.yaml` 的 `plugins.disabled` 命中 `gate_manifest` 后插件路径整条跳过，但 `context.engine: <name>` 仍会把同一目录当引擎装进来。此时引擎在跑、钩子全丢，两边都能在日志里看到「成功」。
  - 后果二：**插件自己打的「hook active」日志不是证据**。`register()` 不论拿到真 ctx 还是 Noop collector 都会照打成功行。实现上要数真的落进了 registry 的钩子：全部到位且 ctx 不是 noop 才打 INFO `hook active: hooks=N`；否则打 WARNING `hooks NOT registered: M/N landed`。验收仍要看钩子的可观测产物（有心跳的契约文本、卡片文件、`api_content` 侧车里出现注入段），不看日志。
  - 后果三：**包内兄弟模块必须用相对导入**。以合成命名空间装载时 `from request_probe import record` 必然 `ModuleNotFoundError`，被 fail-open 吞成 WARNING；探针/台账这类「没有数据就当作没问题」的部件，会安静地永远不跑。凡探针零样本，先 grep 它的导入失败告警，再决定「没发现问题」这句话能不能说。
  - 模块级可变状态要假设有两份独立副本。**同进程内**共享走 `sys.modules` 里一个合成模块盒子（`types.ModuleType` + 一个 dict，两份副本都取到同一个对象）；跨进程才走磁盘原子写。**钩子尤其要单飞**：第一份走到 `register()` 的实例在盒子里认领所有权，第二份只打一行 INFO 说明谁拥有、不再注册。不认领的话，引擎侧 collector 一旦换成真 collector（或宿主改了装载顺序），每个钩子立刻双触发，两份去重状态互相打架——tiered 今天靠引擎侧 noop 碰巧没双发，那是侥幸不是设计。认领按角色名比对（同一角色重跑 `register()`，例如插件 reload，必须放行），不要做成一次性布尔。
- **定位装配/顺序问题，在生命周期两端各放一个纯内存探针**：`post_llm_call` 看装配历史，`select_context` 看 wire 请求。探针只扫内存、入队，懒线程写盘；队列封顶丢最旧；默认关，fail-open。装配历史不等于 wire；回答「是否发给模型」只用 wire 探针/prompt_snapshot，不拿 post_llm 的 index 0 当证据。
- **审查自研插件/框架前先读项目史。** 先 `git log --oneline --all`、`git tag`、`git remote -v`、测试数与审计台账，再用 commit 出现顺序区分「主干」与「后挂模块」。把后挂模块当主干，会写出方向错的路线图。
- **区分「闸」与「导向」。** 本用户的插件设计偏好是导向：提示、路标、软注入、可恢复；硬拦只留给不可逆动作且逐项拍板。默认 fail-open、留手动恢复阀；不要用「闸」描述软机制。
- **生产只读**：审查/调试期间不碰生产 `config.yaml`、systemd 单元、服务、数据库。跑验证用隔离 `HERMES_HOME` 沙箱。

## 深度

`references/tiered-kernel-map.md`：包装器插件实例（Tiered）的六面生命周期、摘要载体回插合同、后台验证器成本审计与发布清单。
`references/host-display-order-forensics.md`：UI 消息顺序错乱的宿主侧取证路径（state.db display_order 触发器/回填/插入口）与插件/宿主归因判据，含宿主源码补丁的更新存活策略。
