---
name: hermes-memory-providers
version: 1.0.0
author: Nekonya (Hermes)
license: MIT
description: 评估、选型或接入 Hermes 记忆 provider 时加载。含主人的验收底线、目录事实与沙箱实测法。
metadata:
  hermes:
    tags: [hermes, memory, provider, mem0, holographic]
    related_skills: [hermes-context-engine-plugins, memory-archive-migration]
---

# Hermes 记忆 provider 选型与接入

**现行部署态（10-21 晨切换完成）**：memory.provider=mem0（OSS 主动写，auto_extract=false）；写=mem0_add 逐字零 LLM，读=Harrier@Pi:8765/v1/embeddings，抽取 LLM=NODE II ornith-35B（备用），库=生产机嵌入式 qdrant ~/.hermes/mem0_qdrant；插件 fork=But-Not-Yet/mem0 commit 5ea2350e。两周观察判据与现场物证：~/Documents/Hermes/记忆提供商选型_20261021/部署实录_20261021_晨.md。

## When to Use

话题落在「给 Hermes 换/加记忆系统」的任何一步：评估某个 memory 引擎、对比 provider、实测某插件、设计注入/写入路径、或续做选型档案（~/Documents/Hermes/记忆提供商选型_*/）。选型前先过下面四条底线。

## 主人的验收底线（先于一切评估）

- **写入面事实抽取必须至少基于语义（LLM 抽取），正则/关键词句式抽取直接不合格**；检索面最好向量化。评任何 provider 先看它的抽取器是什么，抽取器是正则就出局，别被「可选向量检索」救回来——向量加在检索面不改变写入面是正则这个事实。
- 主人的分层定见：**LCM 管无损原文，MEMORY.md 管有损跨会话任务记忆，两者职责不冲突**；外部 provider 只补「MEMORY.md 溢出后的可检索事实库」这一条窄缝，不替换任何一层。逐字原文这格已被 LCM 占——逐字型 provider（MemPalace 类）与 LCM 功能重复，除非要跨原文矛盾检测才值得装。
- 一切执行本地化：抽取 LLM 和 embedder 都指本地端点，零云端计费 API。本地=零美元但占 GPU 时延，报方案时把这个代价如实写出来。
- 结论前先沙箱实测再报，判据预注册（注入 token 增量、召回率、搬迁存量抽查）。

## Provider 框架事实（官方文档实查）

- 内置 MEMORY.md/USER.md 永远在；外部 provider **单选**、纯增量。接入口是 `MemoryProvider` ABC（`agent/memory_provider.py`），装 `$HERMES_HOME/plugins/<name>/`，`memory.provider: <name>` 激活。
- 激活后宿主自动做：`system_prompt_block` 注入 + **每轮 API 前 `prefetch()` 后台召回注入** + `sync_turn` 逐轮持久化 + `on_session_end`/`on_pre_compress` 抽取 + `on_memory_write` 镜像内置写入（带 previous_content 供精确跟随）。所以任何 provider 都自带「强制注入」——不需要自写 pre_llm_call 或 session hook 补机制。
- 官方目录现状：RetainDB/ByteRover 已移出核心且无人维护，不考虑；Hindsight/Mem0/Honcho/OpenViking 是抽取型（每写调 LLM）；Holographic 由社区从 Nous 接盘。**目录里没有 MemPalace**（它只支持 Claude Code/Codex/Cursor hooks），接 Hermes 要走 MemoryProvider 适配层。
- 文档两页：hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers 与 /docs/developer-guide/memory-provider-plugin。

## 各 provider 的定位速查

- **Mem0（hermes-plugin-mem0，OSS 模式）= 当前主线候选**：语义抽取 + 向量检索 + 全本地可行，源码实查 `_oss_providers.py`：LLM 和 embedder 都走 provider=openai + `openai_base_url` 指任意 OpenAI 兼容端点（`embedding_dims` 显式可配，KNOWN_DIMS 外的模型照写）；向量库默认 qdrant 嵌入式本地路径（qdrant-client 纯本地，不用起服务）或 pgvector。工具面带 `mem0_add`（逐字存不抽取），agent 主动写与 LLM 抽取可并用。抽取由宿主轮后后台 worker 跑，不阻塞回复。
- **Holographic：检索面有向量可选、写入面抽取是正则**——按主人底线出局。剩价值只在「要 FTS5 关键词层、接受 agent 主动 fact_store 写」的场景。它写入校验器拒指令/凭据入库（防记忆注入攻击）。
- **MemPalace**：逐字 + 零 LLM 写入 + 矛盾检测，但与 LCM 逐字层重复，且要写适配层；降级为特殊需求才请。
- 安全通识（MemGhost 类攻击）：文件型和向量型同样被污染，防御只能是「外部来源内容不直接进长期记忆 + 写入可审计」，换系统不免疫。

## 本地服务前置（10-21 两处实测快照，用前验活）

- **RAG 弹药全在 Pi（192.168.50.10），不在生产机**——曾按生产机数弹药说要「下 bge-m3」被主人纠正。Pi 库存：`Alonzo/RAG/models/hub/` 有 microsoft/harrier-oss-v1-0.6b（1024 维 embedder，MCP 进程 8765 已常驻加载，CPU）与 BAAI/bge-reranker-v2-m3（重排器，**不是 embedder**——名字里的 bge-m3 是它的底座，bge-m3 嵌入模型本体两处都没有）；open-webui 容器缓存 all-MiniLM-L6-v2 + TaylorAI/bge-micro-v2（923MB）。Pi 无 ollama、无 TEI。
- Pi:8080 是 RK3588 板载 MiniCPM5-2B（rkllm api_server，LLM 无 embeddings 端点）；Pi 上现成 OpenAI 兼容 embeddings 端点**没有**——接 mem0 要用 harrier 得先在 RAG venv 里起一个小 /v1/embeddings 服务（sentence-transformers 已在该 venv）。
- 生产机 Strata llama-server（8080/8081）提供 /v1/chat/completions，**不提供 /v1/embeddings**（实测 not found）。抽取 LLM 用生产机现成服务，embedder 用 Pi 侧。
- **思考型抽取 LLM 陷阱**：生产 Strata 正文可能整个落在 reasoning_content、content 为空，而 mem0 的抽取 prompt 不带 enable_thinking=false——接前必须验默认模板行为，或给抽取配专用非思考小模型。这是 Mem0 路线沙箱验收第一项。

## Mem0 OSS 接线实坑（10-21 实测，全部翻过车）

- qdrant 维度键是 **embedding_model_dims**（放 vector_store.config 里）；embedder.config 里的 embedding_dims 只是插件读的中间键，裸配它 mem0 会按 1536 默认建集合，1024 查询一来就 `shapes (0,1536) and (1024,) not aligned`。抄插件 _backend.py 的注入位置。
- **~/.mem0/migrations_qdrant 是全局迁移目录**：两个 mem0 实例（冒烟脚本与插件沙箱）并发初始化必撞 `already accessed by another instance` 锁，换 vector_store path 不解锁——串行跑，或先等前一个进程退出。
- 抽取 LLM 选型实测（mem0 官方 FACT_RETRIEVAL_PROMPT 直打）：小 NPU 模型（MiniCPM5-2B 级）输出叙述体不出 JSON，出局；NODE II ornith-35B 2.6s 出合法 JSON 且事实密度好，Strata-8081 关思考 11.1s 也可。抽取用 35B 级起步。
- 插件级沙箱加载法：插件目录名撞 mem0ai 库，用 importlib 把 ~/.hermes/plugins/mem0 注册成别名包（types.ModuleType + submodule_search_locations），再覆写 mod._load_config 注入测试配置（含 auto_extract）；p.initialize(session_id, agent_context='primary') 后 handle_tool_call 直接验 mem0_add/mem0_search，sync_turn 短路用包一层计数断言 0 次。
- **execute_code 核的 PYTHONPATH 会污染子进程**（10-21 翻车）：Hermes 内核 session 的 PYTHONPATH 带着 installs/…/python3.14/site-packages，用它调 3.12 venv python 会混进 3.14 的 pydantic（缺 C 扩展，报 No module named pydantic_core._pydantic_core）。验 venv 健康必须 `env -u PYTHONPATH`；hermes CLI 自身进程无此问题，别把内核环境污染当成 venv 坏了去重装。**同污染会杀宿主 mem0 工具**（TUI 进程继承 3.14 路径时后端报 No module named 'mem0'）：给 3.14 环境补装 mem0ai 后当前会话也不重初始化，TUI 重启才自愈；期间写入用绕行脚本 ~/.hermes/cache/scratch/mem_migrate_20261021.py（qdrant 直写，payload 逐字段仿现行点：channel/user_id/agent_id/role/data/hash=md5(data)/created_at/updated_at/text_lemmatized，md5 去重）。qdrant-client 本地模式新版 API：search→query_points(query=vec)、count 取 .count、scroll 用 with_vectors。
- 分层分工（10-21 主人批准）：规则/红线/裁定/门牌必现留 MEMORY.md/USER.md；机器实底/版本 hash/路径/计划/状态类事实进 mem0。已迁 18 条，对照表与回滚点（.bak-20261021-migrate）在 ~/Documents/Hermes/记忆提供商选型_20261021/分层迁移对照_20261021.md。

## 插件沙箱实测法（Holographic 实例验证过的路子）

隔离沙箱直接实例化 provider 类，不碰生产 Hermes home：

```python
import sys; sys.path.insert(0, '~/.hermes/hermes-agent'); sys.path.insert(0, '<插件目录的父目录>')
import <插件目录名> as prov   # 相对导入的包必须整体 import，spec_from_file_location 会炸
p = prov.<X>MemoryProvider(config={'db_path': '<临时>/f.db', 'scope': 'profile',
                                    'auto_extract': 'true', 'embeddings': 'off'})
p.initialize('sbx1', agent_context='primary')   # session_id 是位置必填参
```

- 测写入：循环 `sync_turn(user, asst, session_id=...)` 计时，之后 `p._flush_counts()` 再读 `p._store.count_facts()`——**count 为 0 先查配置开关而不是判功能坏**：`auto_extract` 是字符串枚举（bool('false') 为真所以收 'true' 字符串），默认 off；`_extracting()` 和方法存在性先验一遍再下结论。
- 测检索：`p.prefetch(query, session_id=另一会话)` 看注入块；`p.handle_tool_call('fact_store', {'action':'add','content':...})` 验工具面直写；查询用真口语短句（短查询召回率是覆盖阈值的常见雷区）。
- 中英双喂：正则/分词的中文盲区只有真中文句子测得出来（句式主语是「主人」不是「我」就全漏）。

## 汇报口径

选型报告写进 ~/Documents/Hermes/记忆提供商选型_<日期>/ 分篇编号；每条断言标「源码实查/沙箱实测/文档自述待核」三态；provider 切换动作（装插件+设 memory.provider）改的是每次开局注入，必须主人点头才动。
