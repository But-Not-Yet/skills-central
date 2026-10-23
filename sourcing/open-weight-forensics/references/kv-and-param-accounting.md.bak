# KV 与参数量：从主件算真账

目的：判断一个模型能不能装进给定的「显存 + 内存」池子。不要读二手指南，自己算。

## 三条数据源（都从主件取）

1. **`config.json`** —— 层数、注意力头数、head_dim、`layer_types`（哪些层真的有 KV）、MLA 参数。
2. **`model.safetensors.index.json`** —— 张量名清单。用它得到**真实层号集合**（不要信 config 里的 `num_layers` 是否够用，两边对照才算数）与每层张量种类。
3. **`/api/models/<repo>/tree/main` 里各 `.safetensors` 的 `size` 之和** —— 这是**真实权重总量**，除以 dtype 字节数即总参数量。比模型卡标的数字可靠（可交叉验证卡片是否夸大）。

## KV 公式（每 token，fp16/bf16）

先判定一个词：**哪些层真的有 KV 缓存**。看 `layer_types`：

- `full_attention` → 有 KV
- `linear_attention` / `sliding_attention` → 线性层只有**常量状态**（不算 KV）；滑动窗口层被 window 封顶

**A. 标准 / GQA：**

```
KV_per_token = n_kv_layer × num_key_value_heads × head_dim × 2(K和V) × dtype_bytes
```

**B. MLA（DeepSeek/GLM/Xing 等）：**

```
KV_per_token = n_layer × (kv_lora_rank + qk_rope_head_dim) × dtype_bytes
```

（MLA 存的是**压缩潜变量**，不是展开后的 K/V。发见 `kv_lora_rank` + `qk_rope_head_dim` 同时存在就是 MLA，别拿 `num_key_value_heads` 去乘。）

## 实测过的三个例子（2026-10）

| 模型 | 机制 | KV/token | 128K | 备注 |
|---|---|---|---|---|
| Qwen3.6-35B-A3B | 40 层，仅 **10 层**有 KV，2 个 KV 头 × head_dim 256 | 20 KB | 2.5 GiB | 线性注意力占大头，KV 极省 |
| GLM-4.7-Flash | MLA，47 层，(512+64) | 52.9 KB | 6.6 GiB | 层多 + 无混合，最贵 |
| LongCat-Flash-Lite-Sparse | MLA，**仅 14 层**，(512+64) | 15.75 KB | 1.97 GiB | 层少就省，与参数总量无关 |

**核心认知：KV 大小看「多少层有 KV × 每层多宽」，与参数量总量无关。** 69B 的 MoE 可以比 30B 的 KV 更省。

## 常见陷阱（都踩过）

- **二手站的 KV 估算不可信**。实测：某站给 Ornith-1.5-35B 标「128K 要 67.2 GB KV」，而按 config 算（同 Qwen 同构）只要 2.5 GB——差了 26 倍。**冲突时以主件为准。**
- **只读半个 config 就下判定**。实例：只看到 `num_key_value_heads=32` 就判「MHA，KV 爆炸」，补读才发现有 `kv_lora_rank`——是 MLA。**先把 config 读全。**
- **拿 `num_layers` 当真**。某些仓的层数藏在其它字键下（如 `num_hidden_layers` vs `num_layers` vs `text_config.*`），不一致时以索引里实际出现的层号为准。
- **忽略可用内存折扣**。宣称「12 GiB 显存 + 32 GB 内存 = 44 GB」是理论值；实际要扣系统与后台（Windows 下约 4–6 GB）。算能不能装时用**可用值**，不用理论值。

## 输出格式

用三列表：`量化档 | 权重 | +KV@目标上下文 | +开销 | 总计 | 判定`。判定分三档：✅装得下 / ⚠️贴边 / ❌超。把目标规格摆出来，不要只说「差不多能跑」。
