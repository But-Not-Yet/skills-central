---
name: serving-llms-vllm
description: "用 vLLM 跑高吞吐 LLM 服务时使用：OpenAI API、量化。只要要部署或调优线上推理、把模型服务化，就主动加载，即使用户只说「把它跑起来当 API」。"
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [vllm, torch, transformers]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [vLLM, Inference Serving, PagedAttention, Continuous Batching, High Throughput, Production, OpenAI API, Quantization, Tensor Parallelism]

---

# vLLM — 高性能 LLM 服务

## 何时使用

用于部署生产级 LLM API、优化推理延迟/吞吐，或在显存受限下服务模型。支持 OpenAI 兼容 endpoint、量化（GPTQ/AWQ/FP8）与张量并行。

## 快速开始

vLLM 通过 PagedAttention（分块 KV cache）与 continuous batching（混合 prefill/decode 请求），吞吐比标准 transformers 高 24 倍。

**安装**：
```bash
pip install vllm
```

**基础离线推理**：
```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-3-8B-Instruct")
sampling = SamplingParams(temperature=0.7, max_tokens=256)

outputs = llm.generate(["Explain quantum computing"], sampling)
print(outputs[0].outputs[0].text)
```

**OpenAI 兼容服务**：
```bash
vllm serve meta-llama/Llama-3-8B-Instruct

# Query with OpenAI SDK
python -c "
from openai import OpenAI
client = OpenAI(base_url='http://localhost:8000/v1', api_key='EMPTY')
print(client.chat.completions.create(
    model='meta-llama/Llama-3-8B-Instruct',
    messages=[{'role': 'user', 'content': 'Hello!'}]
).choices[0].message.content)
"
```

## 常用工作流

### 工作流 1：生产 API 部署

照抄这份清单并跟踪进度：

```
Deployment Progress:
- [ ] Step 1: Configure server settings
- [ ] Step 2: Test with limited traffic
- [ ] Step 3: Enable monitoring
- [ ] Step 4: Deploy to production
- [ ] Step 5: Verify performance metrics
```

**第 1 步：配置服务参数**

按模型大小选配置：

```bash
# For 7B-13B models on single GPU
vllm serve meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --max-model-len 8192 \
  --port 8000

# For 30B-70B models with tensor parallelism
vllm serve meta-llama/Llama-2-70b-hf \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.9 \
  --quantization awq \
  --port 8000

# For production with caching and metrics
vllm serve meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --enable-prefix-caching \
  --port 8000 \
  --host 0.0.0.0
# 注：当前 vllm serve CLI 没有 --enable-metrics/--metrics-port（10-23 核官方 CLI 页，
# 只有 --enable-per-request-metrics 等细粒度开关；/metrics 端点默认可用）。
```

**第 2 步：用有限流量测试**

上线前先做负载测试：

```bash
# Install load testing tool
pip install locust

# Create test_load.py with sample requests
# Run: locust -f test_load.py --host http://localhost:8000
```

确认 TTFT（time to first token）< 500ms 且吞吐 > 100 req/sec。

**第 3 步：开启监控**

vLLM 在 9090 端口暴露 Prometheus 指标：

```bash
curl http://localhost:9090/metrics | grep vllm
```

要盯的关键指标：
- `vllm:time_to_first_token_seconds` - 延迟
- `vllm:num_requests_running` - 活跃请求数
- `vllm:gpu_cache_usage_perc` - KV cache 利用率

**第 4 步：部署到生产**

用 Docker 保证部署一致：

```bash
# Run vLLM in Docker
docker run --gpus all -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --enable-prefix-caching
```

**第 5 步：核对性能指标**

检查部署是否达标：
- TTFT < 500ms（短 prompt）
- 吞吐 > 目标 req/sec
- GPU 利用率 > 80%
- 日志中无 OOM 报错

### 工作流 2：离线批量推理

用于在没有服务开销的情况下处理大数据集。

照抄这份清单：

```
Batch Processing:
- [ ] Step 1: Prepare input data
- [ ] Step 2: Configure LLM engine
- [ ] Step 3: Run batch inference
- [ ] Step 4: Process results
```

**第 1 步：准备输入数据**

```python
# Load prompts from file
prompts = []
with open("prompts.txt") as f:
    prompts = [line.strip() for line in f]

print(f"Loaded {len(prompts)} prompts")
```

**第 2 步：配置 LLM engine**

```python
from vllm import LLM, SamplingParams

llm = LLM(
    model="meta-llama/Llama-3-8B-Instruct",
    tensor_parallel_size=2,  # Use 2 GPUs
    gpu_memory_utilization=0.9,
    max_model_len=4096
)

sampling = SamplingParams(
    temperature=0.7,
    top_p=0.95,
    max_tokens=512,
    stop=["</s>", "\n\n"]
)
```

**第 3 步：跑批量推理**

vLLM 会自动批处理请求以提升效率：

```python
# Process all prompts in one call
outputs = llm.generate(prompts, sampling)

# vLLM handles batching internally
# No need to manually chunk prompts
```

**第 4 步：处理结果**

```python
# Extract generated text
results = []
for output in outputs:
    prompt = output.prompt
    generated = output.outputs[0].text
    results.append({
        "prompt": prompt,
        "generated": generated,
        "tokens": len(output.outputs[0].token_ids)
    })

# Save to file
import json
with open("results.jsonl", "w") as f:
    for result in results:
        f.write(json.dumps(result) + "\n")

print(f"Processed {len(results)} prompts")
```

### 工作流 3：量化模型服务

在有限显存里塞下大模型。

```
Quantization Setup:
- [ ] Step 1: Choose quantization method
- [ ] Step 2: Find or create quantized model
- [ ] Step 3: Launch with quantization flag
- [ ] Step 4: Verify accuracy
```

**第 1 步：选择量化方法**

- **AWQ**：最适合 70B 模型，精度损失最小
- **GPTQ**：模型支持广，压缩不错
- **FP8**：H100 GPU 上最快

**第 2 步：找到或创建量化模型**

用 HuggingFace 上现成的量化模型：

```bash
# Search for AWQ models
# Example: TheBloke/Llama-2-70B-AWQ
```

**第 3 步：带量化 flag 启动**

```bash
# Using pre-quantized model
vllm serve TheBloke/Llama-2-70B-AWQ \
  --quantization awq \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.95

# Results: 70B model in ~40GB VRAM
```

**第 4 步：核对精度**

测试输出是否达到预期质量：

```python
# Compare quantized vs non-quantized responses
# Verify task-specific performance unchanged
```

## 何时用、何时换替代方案

**以下情况用 vLLM：**
- 部署生产级 LLM API（100+ req/sec）
- 服务 OpenAI 兼容 endpoint
- 显存有限但要用大模型
- 多用户应用（聊天机器人、助手）
- 需要低延迟 + 高吞吐

**以下情况改用替代方案：**
- **llama.cpp**：CPU/边缘推理，单用户
- **HuggingFace transformers**：研究、原型、一次性生成
- **TensorRT-LLM**：仅 NVIDIA，追求极限性能
- **Text-Generation-Inference**：已在 HuggingFace 生态内

## 常见问题

**问题：加载模型时显存不足**

降低显存占用：
```bash
vllm serve MODEL \
  --gpu-memory-utilization 0.7 \
  --max-model-len 4096
```

或用量化：
```bash
vllm serve MODEL --quantization awq
```

**问题：首 token 慢（TTFT > 1 秒）**

对重复 prompt 开启 prefix caching：
```bash
vllm serve MODEL --enable-prefix-caching
```

长 prompt 开启 chunked prefill：
```bash
vllm serve MODEL --enable-chunked-prefill
```

**问题：model not found 报错**

自定义模型用 `--trust-remote-code`：
```bash
vllm serve MODEL --trust-remote-code
```

**问题：吞吐低（<50 req/sec）**

提高并发序列数：
```bash
vllm serve MODEL --max-num-seqs 512
```

用 `nvidia-smi` 查 GPU 利用率 — 应 >80%。

**问题：推理比预期慢**

确认张量并行用的是 2 的幂的 GPU 数：
```bash
vllm serve MODEL --tensor-parallel-size 4  # Not 3
```

开启投机解码加速生成：
```bash
vllm serve MODEL --speculative-model DRAFT_MODEL
```

## 进阶主题

**服务部署模式**：Docker、Kubernetes 与负载均衡配置，见 [references/server-deployment.md](references/server-deployment.md)。

**性能优化**：PagedAttention 调参、continuous batching 细节与基准结果，见 [references/optimization.md](references/optimization.md)。

**量化指南**：AWQ/GPTQ/FP8 配置、模型准备与精度对比，见 [references/quantization.md](references/quantization.md)。

**故障排查**：详细报错信息、调试步骤与性能诊断，见 [references/troubleshooting.md](references/troubleshooting.md)。

## 硬件要求

- **小模型（7B-13B）**：1x A10（24GB）或 A100（40GB）
- **中模型（30B-40B）**：2x A100（40GB），配张量并行
- **大模型（70B+）**：4x A100（40GB）或 2x A100（80GB），用 AWQ/GPTQ

支持的平台：NVIDIA（首选）、AMD ROCm、Intel GPU、TPU

## 资源

- 官方文档：https://docs.vllm.ai
- GitHub：https://github.com/vllm-project/vllm
- 论文："Efficient Memory Management for Large Language Model Serving with PagedAttention"（SOSP 2023）
- 社区：https://discuss.vllm.ai



