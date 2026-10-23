# 宿主调用点地图与审查清单

路径均相对 `~/.hermes/hermes-agent/`。行号只作定位起点，以源码为准。

## 引擎选择与装载

| 事 | 位置 | 要点 |
|---|---|---|
| config → 引擎 | `agent/agent_init.py` `_select_context_engine` | `context.engine` 串 → `load_context_engine`。值为 `compressor` 短路返回 None（内置） |
| 发现路径 | `plugins/context_engine/__init__.py` | 先 bundled `plugins/context_engine/<name>/`，后用户 `$HERMES_HOME/plugins/<name>/`。`_is_context_engine_dir` 只查 `__init__.py` 是否含 `register_context_engine`/`ContextEngine` 字样 |
| 装载用户引擎 | 同上 | 用户引擎走 `user_plugin_host().load_instance(..., capture="register_context_engine", base_ref="agent.context_engine:ContextEngine")` |
| 注入绑定 | `agent/agent_init.py` | `getattr(engine,"bind_session_state")` 并调 `(session_db=, session_id=)` |
| 模型/阈值 | `agent/agent_init.py` | 写 `engine.model_thresholds`、调 `engine.update_model(model=,context_length=,base_url=,api_key=,provider=,api_mode=)` |
| 会话边界 | `run_agent.py` | `on_session_end → on_session_reset → on_session_start` |

## 每轮 / 每请求钩子

| 钩子 | 调用点 | 提交/返回契约 |
|---|---|---|
| `prune_tool_results_only` | `agent/turn_preflight.py` | 返回 `(msgs, n)`。**只在「`n` 非零 且 `msgs is not 原对象`」时换列表**。只换内存，不重建 conversation_history |
| `select_context` | `agent/conversation_loop.py` | 先过 `_engine_overrides_hook`。返回 None 或非法值 → 原样放行（fail-open）。非空 dict 列表才替换 |
| `should_compress_info` | 宿主多处。内置在 `agent/context_compressor.py` | 返回 `(bool, reason|None)`。有 reason 宿主会 warning 而非静默跳过 |
| 压缩参数过滤 | `agent/conversation_compression.py` | `inspect.signature`。有 VAR_KEYWORD 放行全部，否则按参数名交集 |

## 思考字段两步过滤

- `agent/context_engine.py` 的 `select_context` docstring：宿主在 **prompt cache-control 与每个请求 sanitizer 之前**跑它。替换列表会从改动点起重推导 cache 断点。
- `agent/message_sanitization.py` `apply_reasoning_content_policy`：严格侧 `pop("reasoning_content")`。回显侧要求每条 assistant 带它（空串 400，用单空格补）。
- Anthropic 原生用 `thinking`/`redacted_thinking` 块，规则不同：先前 assistant 的块必须原样回传、API 校验未改动。剥旧思考在原生路由会 400。

## 审查清单模板

按序：

1. 健康自检：激活标记文件末行、调度器心跳、库 `PRAGMA integrity_check`、config 的 `context.engine` 行。
2. 全读主审源码（engine 主体、注册入口、各套单测）+ 对照面（宿主 ABC、调用点、内层引擎关键函数）。大文件分段读，防止结果被上下文层存根。
3. 逐条验收：判据取规格原文，给「达标/存疑/不达标」+ 行号。测不了的标「无法验证」。
4. 缺陷猎捕分级：正确性（数据/功能错）→ 行为偏差 → 健壮性 → 风格。每条：问题 + 证据行号 + 复现实验 + 风险。
5. 实践对照：检索最新同类实践，结论带 URL 与日期、标已核验/未核验。
6. 改进清单（只列不改）按「正确性修复 / 健壮性加固 / 性能 / 实践对齐」四级，供逐条拍板。

## 已验证的复现探针模式

- 熔断复位：构造必然抛错的假内层 → 连读到阈值 → 断言开闸 → 调 `on_session_reset()` → 断言应复位。
- 内层解析：空沙箱 `HERMES_HOME`（`plugins/` 下无目标目录）→ 调 `create(inner_name=...)` → 断言抛 `not available`。
- 跑法：`python3 -I -c "import sys; sys.path.insert(0,'<hermes-agent>'); exec(open('probe.py').read())"`。
