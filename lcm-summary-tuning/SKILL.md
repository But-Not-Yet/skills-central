---
name: lcm-summary-tuning
category: mlops
description: "诊断/调优 Hermes-LCM 摘要质量，或修复损坏的 lcm.db（integrity_check 报错）时使用。"
version: 1.0.0
author: Nekonya
license: MIT
metadata:
  hermes:
    tags: [lcm, summarization, llama-server, sampling]
    related_skills: [llm-monitor-util, llama-cpp]
---

# LCM 摘要质量调优（用户 llama.cpp/ROCm 栈）

## When to Use
LCM 摘要出现截断垃圾节点、重复循环、敏感词回避、压缩率异常（过度压缩或膨胀）、语言漂移时的诊断与调优；或选型/微调 LCM 摘要模型时。

## 根因分层框架（先分层定位，再下药）
1. **机制性截断**：thinking 模式 token 吃光输出预算 → LCM `_deterministic_truncate` 兜底 → 产生 ~510 token 截断垃圾节点并被 DAG 逐层继承。对策：请求里显式 `chat_template_kwargs: {"enable_thinking": false}`（Qwen 系）；并预检 messages token + max_tokens 不超过模型 ctx 的 90%。
2. **分块容量**：leaf chunk 过大（如 20000 token）会让小摘要模型注意力崩溃/复制退化。关键语义（compaction.py 源码）：`LCM_DYNAMIC_LEAF_CHUNK_ENABLED=false` 时 `LCM_LEAF_CHUNK_TOKENS` 退化为**纯触发阈值**——达到阈值后整个 tail 外 backlog 一次压完（单 pass，`to_compact = candidate_raw`），并不按该值分块；想要「固定分块」必须保持 `dynamic=true` 并令 `LCM_DYNAMIC_LEAF_CHUNK_MAX = LCM_LEAF_CHUNK_TOKENS`（base=max 时倍增循环不执行，每 pass 固定块大小，每轮最多 4 pass ≈ 4×chunk）。推荐组合：`LCM_LEAF_CHUNK_TOKENS=4096` + `LCM_DYNAMIC_LEAF_CHUNK_ENABLED=true` + `LCM_DYNAMIC_LEAF_CHUNK_MAX=4096`；分块本身已内建句边界对齐+单句 overlap，无需额外 overlap 配置。健康压缩率约 10-25%（L1_BUDGET_RATIO=0.20）。多轮压缩对逐字规则类信息是悬崖式衰减（Compaction Cliff, arXiv 2608.22752：1 轮后约保留 53%、5 轮后约 10%）——重要规则/承诺/数值应落盘或保证 FTS 可检索，不要依赖摘要链传递。
3. **采样参数**：hermes-lcm 的 `escalation.py` `_call_llm_for_summary` 把 `temperature=0.3` 硬编码、无环境变量；且 llama.cpp 中 **API 请求携带的采样参数会覆盖 CLI 启动参数**。覆盖路径三选一：① 新版 llama.cpp 的 `--ignore-api-samplers`（旧 build 报 invalid argument，先确认版本）② FastAPI 代理拦截重写 body 的采样字段再转发（已验证可行）③ 直接改 escalation.py。历史验证有效的摘要采样组合：temperature 0.7 + repeat_penalty 1.1 + repeat_last_n 256；小模型长文可试 mirostat 2 + num_keep。
4. **模型能力（根因层）**：2B~9B 通用小模型对 2 万 token 中文块的忠实摘要能力本身不足，换模型/调参都只缓解；根治是微调（见下）。
5. **控制标记截流（同族词表风险）**：压缩器与被研究模型同族时（本栈 auxiliary.compression 为 Qwen 系），其词表把聊天控制标记视作单 token 兼 eos——被压缩的对话文本里若在讨论该标记，摘要模型思考中概念性处理它就可能在 token 层直接预测出 eos、被服务端截流，节点整条变空（机制性截断的近亲，但成因在词表而非预算）。对策：LCM_CUSTOM_INSTRUCTIONS 加占位符条款（提及该标记一律用 __IM_END__ 占位符），必要时输入侧消毒；排查空节点/退化节点时先排除这一层。跨模型诊断配方见 idea-background-research 的 session-truncation-forensics。

## 生产拓扑（当前验证过的部署形态）
- 主模型 llama-server（ROCm）端口 8080；socat 8081→8080；LCM lcm-compress 实例在 8181（socat 直通模式下 8081 不跑 FastAPI 代理——两者互斥，部署代理前先 `ss -tlnp` 确认端口占用）。
- 主对话与摘要的最优采样不同 → 摘要用独立实例/独立采样参数（摘要实例的采样参数直接写在其启动脚本里，如 --temp 1.0 --presence-penalty 2.0），不要与主对话共享一套采样设置。
- 摘要模型与主对话异步并行，配置改动前先 `lcm backup`，改后 `lcm doctor` / `lcm_status` 验证。
- 停用专用摘要实例前先检查 config.yaml 的 auxiliary 段：除 compression 外，title_generation / skills_hub / profile_describer 可能仍指向该实例——切换 compression 的 base_url 并不等于该实例闲置。
- 缩小 leaf chunk 会增加每轮压缩 pass 数，留意 spend guard：默认 24 次调用/600 秒窗口，超限后静默 1800 秒并降级为确定性截断（无 LLM 摘要）。小模型单块秒级完成时 24/600s 通常够用，但高频交互会话需监控是否触发 backoff。
- LCM 插件损坏会**静默降级**为 built-in 压缩（行为突变但配置未变时的先查项）：查 errors.log 有无 'file is not a database' 签名，别按「模型变差/参数漂移」方向排查。

## 骨架与解析的关系
LCM 对模型输出**不做任何骨架解析**——摘要文本仅 `lstrip()` 后原样入库（store.py），检索靠 embedding/FTS。四节骨架（`## 当前任务与目标` 等）之所以出现，纯粹是 `LCM_CUSTOM_INSTRUCTIONS`（`~/.hermes/.env`）经 escalation.py 的 `_build_l1_prompt`/`_build_l2_prompt` 以「optional style preference」措辞注入 system_instructions 的效果。含义：① 改骨架格式不需要动 LCM 任何解析代码；② 骨架符合率完全取决于摘要模型对指令的服从度——若训练数据的 assistant 目标不含骨架格式，微调会把基座模型原有的骨架服从性训掉，此时改判据或改训练目标格式，而不是改 LCM。

实测验证（2026-09-28，20 条 seed=42 抽样对照）：把 LCM_CUSTOM_INSTRUCTIONS 改为「强制格式契约」措辞后，LoRA 微调模型的骨架符合率仍为 0%（新旧 prompt 无差异，0/20→0/20），且输出仍带空 ⟨think⟩⟨/think⟩ 前缀对——证实微调后模型的格式完全由训练分布决定，prompt 侧强制措辞对已微调模型无效；基座（未微调）则受 prompt 指令影响（基线曾 61%）。结论：格式必须写进训练标注目标。

## LCM 配置的真实生效来源（改配置前必须先定位在哪层）
- LCM 参数按优先级来自三处，改错层不生效：① systemd drop-in `/etc/systemd/system/hermes-gateway.service.d/override.conf`（Environment= 行，需 sudo 改，改后 `systemctl daemon-reload && systemctl restart hermes-gateway` 才生效）② `~/.hermes/.env`（注意此文件是 CRLF 行尾，用 sed/patch 时按 CRLF 处理）③ `~/.hermes/config.yaml`（auxiliary.compression 段的 base_url/model/timeout/context_length）。
- 验证实际生效值不要猜：`lcm_status` 的 `config` 与 `config_sources` 字段会逐项标注每个参数的生效值和来源（env:XXX 或 config_yaml:XXX）。
- 陷阱：启动脚本里变量与 exec 行可能不一致（如脚本头部 `CTX=65536` 但 exec 行硬编码 `-c 32768`），改脚本变量前先核对 exec 行实际用了哪个参数。
- systemd 单元可能有两个 `[Service]` 段（Environment= 分散在两段），patch 时以 `systemctl cat <unit>` 的输出为准，不要只看主文件。
- Hermes agent 对 auxiliary.compression 的 context_length 有 **64000 硬下限**（低于则 ValueError 拒载）。小窗口模型（如 16K 的板端 LCM 模型）接进来时直接把配置谎报为 64000 绕过——hermes 侧只是不据此提前截断，实际截断发生在推理服务端（如 api_server.py 的 max_context_len），超出窗口的 prompt 由服务端裁掉，压缩质量相应打折。
- 查压缩请求实际长度：板端 Flask 默认 werkzeug 日志不记 prompt_tokens，需到 gateway journal 里找 `Pre-API compression: ~N tokens` 日志行。

## 摘要模型选型结论（实测，勿重复踩）
- MiniCPM5-2B-heretic：重复循环+敏感词回避；Qwen3.5-9B-Defiant：后段复制原文；Gemma-4-E4B：20K 输入无限重复、压缩率 41%（膨胀）；Summarizer-v1-2B：中文差；Mixture-Summarizer：多智能体角色模型，任务不匹配。
- 微调收敛候选：MiniCPM5-2B-Abliterated（LlamaForCausalLM 标准架构、工具链友好、拒绝率 3/100）> Qwen3.8-2B-Distill-Heretic（推理强但 Gated DeltaNet 混合架构，LoRA target 必须覆盖 `linear_attn.in_proj_qkv`/`in_proj_z`/`out_proj`）。数据集首选 CSDS（中文客服对话-摘要对）；5070Ti 12G QLoRA 2 万样本 2 epoch ≈ 3.6h。
- 关键原则：**训练 prompt 模板必须复刻 LCM 实际 L1 prompt**（含 "End with: Expand for details about:"、`<source_data>` untrusted 包裹），训练分布=部署分布。
- uncensored 残余仍会静默过滤敏感词；LCM 侧缓解：L1 prompt 结构化分节（任务状态/决策/文件路径与数值/未决问题）+ 块间 ~10% 重叠，零训练成本。
- 语义检索在摘要质量不稳时先用 FTS；等摘要稳定再开 embedding backfill（劣质摘要会污染语义索引）。

## 每轮生效规则的存放层（压缩生存性）
Hermes system prompt 是三层组装、每次 API 请求全量随行（API 无状态，缓存只省钱）：stable 层（SOUL.md 身份槽、guidance、coding brief）→ context 层（caller system_message、项目上下文文件）→ volatile 层（skills 索引、MEMORY/USER 记忆文件、时间戳）。组装只在压缩后重建。推论：
- 需要**每一轮都约束行为**的规则必须住在组装层（SOUL.md、部署级注入块、LCM_CUSTOM_INSTRUCTIONS）——这些每轮随行。
- 任务卡、文档、按需加载的 skill 正文都敌不过压缩（压缩后即丢失），只能当查询层/归档，不能当执行纪律的存放处。
- session_search 查本会话被压缩掉的细节时，能召回落盘文件与 DB 里的原文；口头约定没落盘就只剩摘要级别。

详见 `references/lcm-test-harness.md`（测试脚本模式与 JSON 对话解析）。