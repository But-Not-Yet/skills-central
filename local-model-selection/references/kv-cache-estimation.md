# KV cache 估算（fp16）

`KV = 上下文长度 × 每 token 每层字节 × 有 KV 的层数`。fp16 = 2 字节/元素。
**一切从 config.json 读，不要凭总参数推断，不要抄第三方站。**

## 按架构分三类

### 1. 全注意力 + GQA（标准 Transformer）
每层每 token = `num_key_value_heads × head_dim × 2(K,V) × 2 字节`，再乘层数。
- `head_dim` 缺失时用 `hidden_size / num_attention_heads`。
- `num_key_value_heads == num_attention_heads` → 纯 MHA，KV 最大。

### 2. 混合线性注意力（Qwen3.5 / 3.6、Ornith 系列）
看 `layer_types`：`linear_attention` 层状态恒定、**不随上下文增长**；只数 `full_attention` 层。
实例：Qwen3.6-35B-A3B = 40 层中 10 层 full_attention、16 头里 **2 个 KV 头**、head_dim 256
→ 约 **20 KB/token** → 32K ≈ 0.62 GB，128K ≈ 2.50 GB。
**这类模型的 KV 比同尺寸全注意力模型小一个数量级，是「KV 必须进显存」场景的首选。**

### 3. MLA（DeepSeek / GLM / Xing4.0）
每层每 token = `(kv_lora_rank + qk_rope_head_dim) × 2 字节`。
- GLM-4.7-Flash：47 层 × (512+64) × 2 ≈ 52.9 KB/token → 128K ≈ 6.6 GB
- Xing4.0-29B-A4B：40 层 × 576 × 2 ≈ 45 KB/token → 128K ≈ 5.6 GB
- **判断关：config 里同时有 `num_key_value_heads` 和 `kv_lora_rank` 时，它是 MLA，按潜变量算。** 按 MHA 算会高估十几倍。

### 滑动窗口
`sliding_window` 层 KV 封顶在 window 大小，不随上下文增长（常驻开销）。

## 混合/特殊架构对照表

| 模型 | 机制 | KV/token | 32K | 128K |
|---|---|---|---|---|
| Qwen3.6-35B-A3B / Ornith-1.5（`qwen3_5_moe`） | 10/40 全注意力，2 KV 头 | 20 KB | 0.62 GB | 2.50 GB |
| Gemma4-26B-A4B | ~5 全注意力 + 25 滑窗×1024 | ~40 KB + 常驻 | 1.45 GB | 5.20 GB |
| GLM-4.7-Flash | MLA 47 层 | 52.9 KB | 1.65 GB | 6.61 GB |
| Xing4.0-29B-A4B | MLA 40 层 | 45 KB | 1.41 GB | 5.62 GB |

## 专家卸载 vs 层卸载（本类任务最常错的一处）

- **MoE 专家卸载**：把「每 token 必走」的部分（注意力、稠密 FFN、共享专家）留 GPU，路由专家放内存。每 token 只读激活的几个专家。
  llama.cpp：`-ngl 999 -ot "exps=CPU"`（等价 `--n-cpu-moe N`，N 从最高层起数）；exllamav3：CPU MoE offload（需 AVX2 起，AVX-512 VNNI 更快）。
- **稠密层卸载**：每个 token 都要把卸载层的权重整个读一遍 → 慢一个数量级。**给定「必须部分卸载」约束时，稠密候选直接排除。**
- **保 KV 进显存**：llama.cpp 用 `--cache-type-k f16 --cache-type-v f16`（别用 q4/q8 压 KV，除非显存实在不够）。exllamav3 侧同样把 KV 精度设为 f16。
- 调优顺序：先把专家卸载到「显存刚好被注意力+KV+少量专家占满」，再逐档把专家挪回 GPU 找速度甜点。
