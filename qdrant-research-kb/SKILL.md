---
name: qdrant-research-kb
version: 1.0.0
author: Nekonya (Hermes)
license: MIT
description: 碰主人的数学 RAG 知识库时加载：Qdrant 集合读写、rag_utils.py 管线、BM25 混合检索、稀疏向量 backfill、mcp__research_kb__* 工具，以及 v3 升级计划的续做。给已验证的集合布局、陷阱清单和可跑片段。
category: research
metadata:
  hermes:
    tags: [qdrant, rag, hybrid-retrieval, bm25, research-corpus]
    related_skills: [llm-wiki, arxiv]
---

# Qdrant 科研语料库（RAG v3.x）运维

## 何时使用

主人的数学科研 RAG 知识库的任何工作：Qdrant 集合（`research_corpus`、`research_corpus_hybrid`）、`rag_utils.py` 管线、BM25 混合检索、稀疏向量 backfill、`mcp__research_kb__*` MCP 工具。或续做 v3.4→v3.5 升级计划（Phase B/C/D/E）。

架构：Qdrant（docker）+ `rag_utils.py` 管线 + MCP server（`mcp__research_kb__search_knowledge`）喂给 Hermes。

版本注记：v3.4 建成 24,279 点（下文集合布局节的 22,746 是旧集，已停更）。混合 backfill 已完成：逐点 scroll 回读证实 `research_corpus_hybrid` 每点 `""` 键下 dense + `text_sparse` 分量都在——别再引用旧档里「稀疏为 0」的说法。

## 环境事实

- **生产主机是家里 Orange Pi**（192.168.50.10，15G ARM，无 GPU）：项目根 `/srv/dev-disk-by-uuid-f0870af7-c775-4b06-95af-5f832267725e/Alonzo/RAG/code/`（venv、`rag_utils.py`、`mcp_server_http.py`、`model_cache/` 都在里面）。桌面端旧项目根是建设期，已迁走；本地改完要同步到 Pi 才算生产生效。
- 项目 Python 一律走项目 venv：`<root>/venv/bin/python`：bash 的系统 python 缺 qdrant_client/sentence-transformers。
- Qdrant 容器 `qdrant-research`（v1.19.1，当日未复验——Pi 不在本机网段可达范围）现跑在 Pi 上，端口 6333/6334，网络 `rag_qdrant_research_default`。上游已出 v1.20.0（2026-10-22，新增 BM25 全文索引等），升级前先核咱家混合查询用的 Query API 行为有无变更。宿主重启后容器退出（143/SIGTERM），`docker start qdrant-research` 恢复，`curl -s http://localhost:6333/collections` 验证。Pi 上集合可能显 grey 状态而数据完好——别见 grey 就判损坏。
- MCP server 是 Pi 上的宿主进程 `mcp_server_http.py`（监听 8765）；Hermes 侧 `~/.hermes/config.yaml` 的 `mcp_servers.research_kb` 用 `transport: streamable-http`、`url: http://192.168.50.10:8765/mcp`。Embed 模型：microsoft/harrier-oss-v1-0.6b（1024 维），reranker bge-reranker-v2-m3；模型实物在 Pi 的 `model_cache/`。现行值以 Pi 上 `rag_utils.py` grep 为准，本条是快照。
- 管线计划在 `<Hermes>/.hermes/plans/`（`*-rag-v35-upgrade.md` = 原计划含评审整合记录。`2026-09-24-rag-v35-roadmap.md` = 最新校准路线图含步骤顺序）。续做升级工作前先读最新路线图。
- 截至 2026-09-25 的状态：dense-only 决定已提交（`fetch_n` 修复，commit 5bd95c9）。hybrid 只作 `USE_HYBRID` 开关保留。Step 4 摄取脚本是 `scripts/08_arxiv.py` + `scripts/09_openalex.py`。arXiv 406 失败是 IP 突发限流（见 `arxiv` skill）：`08_arxiv.py` 现对 406/429/503 指数退避重试（60s 基、240s 顶、抖动、`ARXIV_MAX_ATTEMPTS`/`ARXIV_FIRST_BACKOFF` 环境量）。不改 UA/编码。`09_openalex.py` 用 polite-pool `mailto` + 游标分页，概念 ID 实测（C52622258 信息论、C91575142 最优控制、C2983030100 非线性动力学）。

## 集合布局（当前，已验证）

- `research_corpus`：生产，22,746 点，默认**无名** dense 向量（1024, Cosine, int8 量化）。
- `research_corpus_hybrid`：混合测试集合：dense 同样**默认无名**，稀疏是命名 `text_sparse` 带 `Modifier.NONE`。生产检索现行 dense-only（`USE_HYBRID=0`），但稀疏分量已回填完（逐点验过），混合开关随时可用。
- 共享 BM25 状态：`<root>/sparse_state/encoder.json`（`term2id`、`idf`、`avgdl`，k1=1.5, b=0.75）。

## 关键陷阱（每条都花过真实调试时间）

1. **命名/默认向量的 upsert 格式**：把命名键指向集合的默认（无名）dense 向量会报 `Not existing vector name error: <name>`。dense 无名的混合集合，upsert 写成 `PointStruct(id=..., vector={"": dense_vector, "text_sparse": SparseVector(...)})`：空字符串键 = 默认分量。命名稀疏可正常合并。
2. **qdrant-client 字段名**：`CollectionInfo` 上稀疏配置属性是 `params.sparse_vectors`，不是 `sparse_vectors_config`（那只是 create_collection 的参数名）。读错名会 pydantic AttributeError。另注意：即使点已带命名稀疏分量，集合配置可能仍报稀疏配置为 `null`。要验证稀疏真的落了。用 `with_vector=true` 滚一个点看逐点向量字典（默认 dense 在 `""` 下 + 命名稀疏条目），别看集合级配置。
3. **BM25 单一 IDF 契约**：Qdrant 稀疏侧必须 `Modifier.NONE`，因为客户端编码器已把完整 BM25 分数烘进存储值。查询侧用 `score = tf * idf`（无长度归一化，负 IDF 截到 0，Lucene 惯例）。查询必须发同一编码器实例/状态预编码的 `SparseVector`，绝不发原始文本（服务端分词器/IDF 会与存储不匹配）。
4. **Backfill 时 dense+稀疏分开处理**：从源集合复制 dense 时带 `with_vectors=True` 滚动。只合并稀疏的 upsert 完全不碰 dense（Qdrant 对同点 id 的命名分量做合并）。
5. **全量 backfill 前先跑 10 点试验**：写入后滚回并打印两个分量的存在/维度。然后分批（100/批，`wait=True`）带逐批进度日志和 try/except。
6. 任何中断后先复查实时状态（`docker ps -a`、集合状态/points_count）再重做：backfill 可能已经完成。

## Backfill 流程（稀疏向量进混合集合）

1. `docker start qdrant-research`。确认两个集合都绿。
2. 跑 `<root>/backfill_hybrid.py <小N>`（10 点）：端到端验证 scroll→encode→upsert→readback。
3. 全量：`venv/bin/python backfill_hybrid.py`（约 22.7k 点，批 100，约 45s）。
4. 验证：逐点回读显示 dense dim=1024 且 sparse dims>0。`points_count` 与源一致。抽样稀疏查询（如 "Lyapunov stability"）返回合理 top-k。

稀疏编码器契约细节在 `<root>/sparse_encoder.py`：`BM25Encoder.build(docs)` 建排序 term2id + 截断 IDF，`encode_doc` 返回完整 BM25 文档分数。`encode_query` 返回 tf*idf 查询权重，状态持久化到 `sparse_state/encoder.json`。摄取/查询/backfill 必须共享这一个状态文件。

## 验证片段

```bash
# 集合健康（字段是 sparse_vectors，不是 sparse_vectors_config）
curl -s http://localhost:6333/collections/research_corpus_hybrid
```

```python
# MCP streamable-http 直连探测（不依赖 Hermes）：initialize 响应头取 mcp-session-id，
# 后续请求带 mcp-session-id 头；响应是 SSE 帧，从 data: 行取 JSON。
# 顺序：initialize → notifications/initialized → tools/call search_knowledge。
# 缺 session 头会报 "Bad Request: Missing session ID"，不是服务挂了。
```

```python
# 混合查询走 Query API（qdrant-client >= 1.10）
client.query_points(collection_name="research_corpus_hybrid",
    prefetch=[models.Prefetch(query=models.SparseVector(indices=q_idx, values=q_vals),
                             using="text_sparse", limit=10)],
    query=models.FusionQuery(fusion=models.Fusion.RRF), limit=5, with_payload=True)
```

## 基准（2026-09-25 已验证）

- `scripts/bench_eval.py`（commit ae36adf）：3×25 查询基准 → `output/bench_report.md` + `bench_results.json`。GPU（7900 XTX, torch 2.13.0+rocm10.0.0）：embed 15.2 ms/查询，端到端 p50 229 ms，ANN recall@10 对精确 = 1.0。hit@1 0.88（3 个失误 = 分块粒度伪影）。必须带 `EMBED_DEVICE=auto` 跑：=cpu 时慢约 1500 倍（22 s/查询），任何前台工具调用都会超时。全程 GPU 上约 18 s。
- GPU 上 embedding 热态很快（批 1635 docs/s）但模型加载后首批有 MIOpen 内核编译抖动（约 6 s）。计时前先预热。
- llama-server 内存压力会杀掉 qdrant-research 容器（143）。任何基准前先 `curl localhost:6333`。在 `docker start` 前开始的基准会 ConnectError。
- `output/` 被 gitignore。报告用 `git add -f`。
- **Pi ARM CPU 生产稳态（实测，模型常驻）**：MCP HTTP 往返 2.5–4.6 s/查询（0.6B embed 纯 CPU）。给其他 0.3B 级 embedder 估 Pi 耗时可按参数量比例打底，但必须实测后才写进验收判据。
- **open-webui（同 Pi，3000 端口）是另一套栈**：它的 RAG 用 `all-MiniLM-L6-v2` + 辅 `bge-micro-v2`（缓存 923MB 在 open-webui-data 卷），与科研库的 harrier 向量维度与模型都不兼容——两套 embedding 别混用、别互相查询。
- 已知未决：reranker 分数方向检查待做（生产调用 `reranker.compute_score(pairs, normalize=True)`）。

## 会话工作流注记

- 主人的标准工作流：先呈大纲/理由，批准后再实现。每步用真实工具输出验证后才报成功（编译并回读，不是声明）。
- `tests/test_hybrid.py` 是混合检索的 TDD 门（`QDRANT_URL=:memory:` 隔离）。Task B3 落地前必须 FAIL，之后必须 PASS。
