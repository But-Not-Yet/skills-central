# Ornith APEX 与 LFM2.5：NODE II 模型选择

## 当前节点（活体）

- 模型：Ornith-1.5-35B-A3B，Qwen3.5 MoE，35B 总参 / 约 3B 激活，256 路由专家 / 8 激活，40 层 + 1 原生 MTP，262144 上下文，MIT。
- 量化：APEX I-Quality，22.8 GB。注意力全 40 层 Q6_K；共享专家 Q8_0；路由专家边缘层 Q6_K、次边缘 Q5_K、中间 blk10-29 IQ4_XS。
- APEX 是量化档名，不是微调；MTP 是原生层；expert-profile 是 PolyStrata 的运行时专家缓存画像。
- 引擎：PolyStrata 0.1.45，单槽位，8 GB 会话缓存，约 7 GB 专家缓存，`--kv fp16`。
- 体检：VRAM 11.45-11.48 / 12.82 GB，RAM 31.75-32.06 / 33.84 GB；解码 70-96 tok/s，预填约 1.25k tok/s；40k prompt 预填 4-20 s，100k 约 19 s。

## 选择规则

- 编码/agentic 主力：Ornith。SWE-bench Verified 79、Terminal-Bench 2.1 67.8、GPQA 89.2。
- 快速工具路由/第二设备：LFM2.5-24B-A2B。24B / 2B 激活，131072 上下文，Q4_0 13.6 GB；AutomationBench 27.69、ToolSandbox 80.71、LiveClaw 48.09、IFEval 96.75；但 SWE-bench Verified 51.0、GPQA 74.42。
- 只用速度理由换 LFM 不划算：当前解码不慢，瓶颈是内存余量、长上下文预填和 xhigh 思考打转；换 LFM 会拿编码质量换内存。
- 微调：暂不做。35B MoE BF16 约 70 GB，12 GB 笔记本做不了；失败样本更像任务歧义 + xhigh，不是知识缺口。将来要微调，先 BF16 基座 + LoRA + 留出集，再 APEX 量化。

## 维护坑

- 旧 `strata-ornith.json` 可能仍指旧 Huihui 23G/32768；真源是 `strata-ornith-apex-i-quality.json`。重启前对 `/props` 的 model_path 与配置 args 核一遍。
- coder 的 `reasoning_effort=xhigh` 对机械任务过长；降到 medium/high。
- `/metrics` 的显存/内存是采样数组；单点只代表当刻，全程断言要读 history。
