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

`-I` 阻止 venv 注入；缺 `hermes-agent` 路径会报 `ModuleNotFoundError: No module named 'agent'`。脚本模式 `python -m pkg.tests.x` 在无 venv 时也会因路径缺 `agent` 而失败，用上面的 `exec` 形式最稳。

## 包装器（装饰器）实现的硬规则

这些都踩过，且不是可选的：

- **token-state 属性必须装真描述符，不能靠 `__getattr__` 兜底**。ABC 把 `last_prompt_tokens`、`threshold_tokens`、`context_length`、`compression_count`、`threshold_percent` 等定义为带默认值的**类属性**，普通属性查找命中默认 0，`__getattr__` 永不触发。要在类体后 `setattr(cls, attr, property(get,set,del))`。而且宿主会把 `model_thresholds` 与几个下划线开头的私有属性直接写在选中引擎上，必须逐个显式代理 —— 用一个白名单常量维护它们。
- **`__getattr__` 默认不转发下划线属性**。宿主写的私有属性（例如 `_last_compress_refused_would_grow`）不会自动落到内层，除非显式代理。
- **包装器的 `compress` 必须声明 `**kwargs`（或全候选签名）**。宿主按**选中引擎**的签名过滤压缩参数再调用；窄固定签名会让宿主静默丢掉内层支持的参数。包装器收到全量后再按**内层**签名过滤一次。过滤逻辑镜像宿主 `_supported_compression_kwargs`（`inspect.signature`，有 `VAR_KEYWORD` 就放行全部，否则按参数名取交集）。
- **`prune_tool_results_only` 的提交契约**：无操作必须返回**输入对象本身** + 计数 0；要生效必须返回**新列表对象** + 非零计数。宿主只在「新对象且计数非零」时换列表。返回新对象配 0、或同对象配非零，都会被忽略。
- **`on_session_reset` 必须复位包装器自身的本地状态**（例如熔断器的连续失败计数与开闸位）。宿主要在 `/new`、`/reset` 会话边界驱动 `on_session_end → on_session_reset → on_session_start`；ABC 默认实现本就会清计数，只转发内层就把这份语义丢了，导致故障开闸后新会话继续无自动压缩。
- **解析内层引擎时，引擎名 ≠ 插件目录名**。目录查找走 `user_plugins_dir()/<name>`；目录叫 `hermes-<name>` 时要靠 `hermes-` 前缀兜底。第三路「通用插件系统按 `name` 严格相等」忠实镜像宿主，但对别名（同一引擎的旧名/新名）会脱靶 —— 若引擎名会随版本/配置变，别名集匹配比硬写默认值稳。
- **`register()` 里 catch 装载失败再 return 会造成静默降级**：宿主按自己的回落规则改跑内置 compressor，用户侧可能只看到一句 WARNING。配置指名了你的引擎却拿不到内层引擎，是丢整条链路，不是小错；失败要响亮暴露（日志 + 可见状态）。
- **`select_context` 每请求跑，且在请求 sanitizer 与 cache-control 之前**。返回替换列表会**从改动点起改变 prompt cache 前缀**（断点在选中列表上重推导），所以变换必须确定性、纯内存、无 IO，且不做会自变的决定。

## 思考剥离层：边界、粒度、路由

**边界——Anthropic 硬规则只有一条，落在末轮**：启用 thinking 时，**最后一个** assistant 消息必须以 thinking 块开头（位于最末一组 tool_use/tool_result 之前）；**更早轮**的 thinking 只是「recommend」，可省略。所以「只保留最后一个 assistant 的思考、剥掉更早的」**与硬规则一致，不是主动致错**。

**成本面**：4.6 及以后保留历史轮 thinking 并按输入计费，4.5 及更早服务端剥离——剥旧思考省的是这部分输入计费，属权衡不是缺口。

**Anthropic 官方客户端（Claude Code）不做逐轮剥旧思考**：它只做三种 400 规避（孤儿 thinking-only 消息、末条 trailing thinking、凭据变更后签名字），并在支持模型上用 context-management beta **请求保留**历史 thinking。

**真关口是粒度，不是边界**：字段级 `pop(key)` 删整块思考，删不掉 thinking 文本**内部**的行内孤儿标记（开/闭不成对）；那份标记留在 `content` 里照样把下游正文误判成思考。修法属**标记级卫生**（入库成对保证 + 剥离路径残余清扫），落点在组装层与内层引擎入库/升级边界，不在思考剥离层本身。

**Kimi/DeepSeek echo 族相反**：要求每条 assistant 带 `reasoning_content`（空串 400，用单空格占位）。

官方原文、按模型的保留政策、Claude Code 源码函数与行号见 `references/thinking-block-preservation.md`。

> 反面教训（先前的错误论断，已改正）：曾据『官方校验先前的 thinking 原样回传』判「剥旧思考在 Anthropic 原生路由会主动致错」——把「recommend」当成了硬要求。定边界前必须逐字读官方原文，确认硬要求落在**谁**身上。

## 过滤/改写放哪层：三层候选与成本口径（设计咨询速查）

被问「能不能用插件实现过滤/改写」「会不会太慢」时：先列层给覆盖面，再给实测数字，最后给建议。

- **候选层（按覆盖面排序）**：① 包装器 `select_context` 每请求跑且在 sanitizer 之前——覆盖一切进模型的文本（含回放历史、工具结果回流、任何来源）；② 内层引擎的入库/升级边界——管库内与检索面卫生；「成对保证」只能在入库面表达（请求面只能清扫，不能拒绝入库）；③ 通用插件钩子——`transform_tool_result`（工具结果产出处变形）、`transform_llm_output`（模型输出替换）；`pre_llm_call` 只注入上下文、**不能过滤**（契约已核）。
- **成本口径（先测再答）**：文本级清扫是线性内存操作，用 B5 式 micro-benchmark 给数——校准量级：~800KiB 请求（几百条消息）下，`"命中字符" in text` 快路径 + 单正则替换 ≈ 0.1 ms/遍，最坏（全命中）≈ 0.2 ms/遍；相对秒级生成可忽略，且与宿主每请求既有的 sanitizer 同类。汇报用「实测毫秒 vs 生成秒级」，不用形容词。
- **实现纪律**：只在命中时新建对象（copy-on-change，不动入参）；模式表按目标词表收紧，防误伤代码/标记语言里的正常尖括号；落地走 `fix-batch-workflow` 的批次形状。

## 审查这类插件的顺序

0. **判「某层有害/多余」之前，先回一手来源定意图与边界**：回**设计讨论原文**确认这层的意图（为什么做它、哪条边界是设计如此），再拿**官方规则原文**定边界。两条禁令——① 不拿代码 docstring/注释的自述当设计意图（它是作者的自我描述，可能过时，或本身就是被质疑的对象）；② 不拿官方的「建议/recommend」当硬规定（硬要求通常只有一条，逐字读清它落在**谁**身上）。违任一条都会产出被撤回的判定。
1. 跑健康自检（引擎激活标记、调度器心跳、库完整性、config 里的 `context.engine`）。
2. 全读主审源码 + 对照面（宿主 ABC、各调用点、内层引擎关键函数）。
3. 逐条对照任务书/规格的验收判据，给「达标/存疑/不达标」+ 行号；判据以原文为准，禁事后重解释，测不了的标「无法验证」。
4. 缺陷猎捕：正确性 → 行为偏差 → 健壮性 → 风格，按严重度排。
5. 检索最新实践再评判，结论带 URL 与日期、标已核验/未核验。
6. 出改进清单（只列不改），每条给问题 + 证据行号 + 改法 + 风险，并设计沙箱可跑的最小复现实验。

详细调用点行号、提交判据表、审查清单模板见 `references/host-contract-map.md`。

## 通用陷阱

- **进程内先 import 后读 `os.environ` 的模块级常量会被缓存**。插件在 import 时读环境变量（例如内层名默认值），systemd drop-in 能覆盖，但 CLI 直跑/测试/进程内改 env 行为不一致。要在注册/构造**调用时**读。
- **读大型源码文件要分段读**。整文件读取的结果会被上下文管理层自动存根成一行占位符；被存根后回**原文**重读，结论不许建在存根或摘要上。
- **生产只读**：审查/调试期间不碰生产 `config.yaml`、systemd 单元、服务、数据库；跑验证用隔离 `HERMES_HOME` 沙箱。
