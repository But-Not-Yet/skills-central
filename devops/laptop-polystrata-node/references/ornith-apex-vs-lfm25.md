# Ornith APEX 与 LFM2.5：NODE II 模型选择

## 当前节点（活体）

- 模型：Ornith-1.5-35B-A3B，Qwen3.5 MoE，35B 总参 / 约 3B 激活，256 路由专家 / 8 激活，40 层 + 1 原生 MTP，262144 上下文，MIT。
- 量化：APEX I-Quality，22.8 GB。注意力全 40 层 Q6_K；共享专家 Q8_0；路由专家边缘层 Q6_K、次边缘 Q5_K、中间 blk10-29 IQ4_XS。
- APEX 是量化档名，不是微调；MTP 是原生层；expert-profile 是 PolyStrata 的运行时专家缓存画像。
- 引擎：PolyStrata 0.1.45，单槽位，8 GB 会话缓存，约 7 GB 专家缓存，`--kv fp16`。
- 体检：VRAM 11.45-11.48 / 12.82 GB，RAM 31.75-32.06 / 33.84 GB；解码 70-96 tok/s，预填约 1.25k tok/s；40k prompt 预填 4-20 s，100k 约 19 s。

## 长上下文重复的机制

Ornith 的架构是 `qwen3_5_moe`：40 层里 **30 层线性注意力**（状态大小固定），只有 10 层全注意力保留精确 KV。上下文推到十万 token 以上，那 30 层的固定状态被早期内容填满，近期内容的精确记忆退化，模型开始忘了自己刚说过什么，于是复读。

这是**架构给的额度用完了**，不是采样写错。penalty 只能压住表面症状，根治要换架构。

## 引擎能力地图（换型第一道闸）

`D:\LLM\PolyStrata\docs\` 里，模型有专页才算引擎跑过且量过：

| 文档 | 模型 | 本节点 44 G 池判定 |
|---|---|---|
| `MODELS.md` | Qwen3.8-Flash-Next | Q2_0 要 37.6 GB；32 GB 内存档官方只给 Coder 版（IQ1_M，512 专家留 256），注明弱在代码之外与非英语 → 主人用中文，出局 |
| `GLM.md` | GLM 5.3 Flash | 321B，装不下 |
| `DEEPSEEK.md` | DeepSeek V4 Flash | IQ2_XXS 90.9 GB，装不下 |
| `LFM.md` | **LFM2.5-24B-A2B** | **唯一落地** |
| 无 | Gemma-4-26B-A4B | `gemma4.cpp` 有代码、无专页 = 未验证路径，不进对比表 |

llama.cpp 新合入但本引擎没有实现的架构同样出局：flint（`FlintForCausalLM`）、Raon-1-mini（KRAFTON 自有架构），`src/poly/` 里都没有对应文件。

## LFM2.5-24B-A2B 实测（引擎 doc 原值）

测试机是 8 GB 显存的笔记本（i7-14700HX + 32 GB RAM），比本节点更弱，所以本机只会更快。

| 量化 | 下载 | 专家 | RAM 需求 | 首字 | 读 prompt | 写回答 |
|---|---:|---:|---:|---:|---:|---:|
| UD-Q4_K_XL | 14.9 GB | 14.0 GB | 约 20 GB | 8.3-8.4 s | 3,575-3,601 tok/s | 67-68 tok/s |
| UD-Q3_K_XL | 10.9 GB | 10.2 GB | 约 16 GB | 7.9-8.0 s | 3,758-3,811 tok/s | 80-81 tok/s |
| QAD-Q4_0 | 13.6 GB | 12.9 GB | 约 18 GB | 8.1 s | 3,685-3,694 tok/s | 72-73 tok/s |

- 架构：30 层三 token 短卷积（状态只有两个向量）+ 10 层全注意力（8 个 KV 头 × 64）。**每 token KV 20,480 字节，128K 只比 32K 多 2.0 GB。**
- 131K 上下文：读一遍 44.7-45.4 s（2,700 tok/s），之后写 35 tok/s。
- **长上下文不是完美的**：123,609 token 文档在 15%/50%/85% 埋三条事实，问三个问题，**只命中后两条，最远那条编造**（doc 原话：最远的事实是模型最没把握的地方）。失效模式从「严重重复」变成「远处细节不可信」。
- **无 MTP 草稿块**：引擎只能从对话里重复的文本猜，投机解码加速拿不到。
- 官方明说不推荐单独做知识密集任务，要配检索。
- 授权：LFM Open License v1.0，商用只给年营收一千万美元以下的公司。

## 选择规则

- 编码/agentic 主力：Ornith。SWE-bench Verified 79、Terminal-Bench 2.1 67.8、GPQA 89.2。
- 快速工具路由/第二设备：LFM2.5-24B-A2B。24B / 2B 激活，131072 上下文；AutomationBench 27.69、ToolSandbox 80.71、LiveClaw 48.09（对 Qwen3.6-35B-A3B 的 38.19）、IFEval 96.75；但 SWE-bench Verified 51.0、GPQA 74.42。
- **换型的触发条件**：penalty 压不住长上下文重复，才轮到换。只拿速度理由换不划算——当前解码不慢，换 LFM 是拿编码质量换内存。
- 微调：暂不做。35B MoE BF16 约 70 GB，12 GB 笔记本做不了；失败样本更像任务歧义 + xhigh，不是知识缺口。将来要微调，先 BF16 基座 + LoRA + 留出集，再 APEX 量化。

## 维护坑

- 旧 `strata-ornith.json` 可能仍指旧 Huihui 23G/32768；真源是 `strata-ornith-apex-i-quality.json`。重启前对 `/props` 的 model_path 与配置 args 核一遍。
- coder 的 `reasoning_effort=xhigh` 对机械任务过长；降到 medium/high。
- `/metrics` 的显存/内存是采样数组；单点只代表当刻，全程断言要读 history。
