---
name: llama-cpp
description: "本地跑 llama.cpp GGUF 推理、在 HF Hub 找模型时使用。只要要用 GGUF 本地推理、挑量化档或找模型，就主动加载，即使用户只说「本地跑一下这个模型」。"
version: 2.1.2
author: Orchestra Research
license: MIT
dependencies: [llama-cpp-python>=0.2.0]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [llama.cpp, GGUF, Quantization, Hugging Face Hub, CPU Inference, Apple Silicon, Edge Deployment, AMD GPUs, Intel GPUs, NVIDIA, URL-first]
---

# llama.cpp + GGUF

用于 llama.cpp 的本地 GGUF 推理、量化档选择，或 Hugging Face 仓库发现。

## 何时使用

- 在 CPU、Apple Silicon、CUDA、ROCm 或 Intel GPU 上跑本地模型
- 为某个 Hugging Face 仓库找到合适的 GGUF
- 从 Hub 构建 `llama-server` 或 `llama-cli` 命令
- 在 Hub 上搜已支持 llama.cpp 的模型
- 枚举某个仓库里可用的 `.gguf` 文件及其大小
- 按用户的 RAM 或 VRAM 在 Q4/Q5/Q6/IQ 变体间做取舍

## 模型发现工作流

优先用 URL 工作流，先别急着要 `hf`、Python 或自定义脚本。

1. 在 Hub 上搜候选仓库：
   - 基础：`https://huggingface.co/models?apps=llama.cpp&sort=trending`
   - 加 `search=<term>` 限定模型家族
   - 用户有尺寸限制时加 `num_parameters=min:0,max:24B` 之类
2. 用 llama.cpp local-app 视图打开仓库：
   - `https://huggingface.co/<repo>?local-app=llama.cpp`
3. local-app 片段可见时，以它为唯一依据：
   - 原样照抄 `llama-server` 或 `llama-cli` 命令
   - 推荐的量化档按 HF 显示的原文照报
4. 把同一个 `?local-app=llama.cpp` URL 当页面文本或 HTML 读取，抽出 `Hardware compatibility` 小节：
   - 优先用它给出的确切量化标签与大小，而非通用表格
   - 保留仓库特有的标签，如 `UD-Q4_K_M` 或 `IQ4_NL_XL`
   - 若抓取到的页面源码里看不到该小节，就明说，并退回 tree API + 通用量化指引
5. 查 tree API 确认实际存在什么：
   - `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`
   - 只保留 `type` 为 `file` 且 `path` 以 `.gguf` 结尾的条目
   - 文件名与字节大小以 `path` 与 `size` 为准
   - 把量化 checkpoint 与 `mmproj-*.gguf` projector 文件、`BF16/` 分片文件区分开
   - 仅在人工兜底时才用 `https://huggingface.co/<repo>/tree/main`
6. 若 local-app 片段无法以文本看到，就用仓库加所选量化档重建命令：
   - 简写量化选择：`llama-server -hf <repo>:<QUANT>`
   - 精确文件兜底：`llama-server --hf-repo <repo> --hf-file <filename.gguf>`
7. 只有当仓库尚未提供 GGUF 文件时，才建议从 Transformers 权重转换。

## 快速开始

### 安装 llama.cpp

```bash
# macOS / Linux (simplest)
brew install llama.cpp
```

```bash
winget install llama.cpp
```

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build --config Release
```

### 直接从 Hugging Face Hub 运行

```bash
llama-cli -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

```bash
llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

### 从 Hub 运行某个确切 GGUF 文件

当 tree API 显示自定义文件名，或缺少确切的 HF 片段时用它。

```bash
llama-server \
    --hf-repo microsoft/Phi-3-mini-4k-instruct-gguf \
    --hf-file Phi-3-mini-4k-instruct-q4.gguf \
    -c 4096
```

### OpenAI 兼容服务检查

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Write a limerick about Python exceptions"}
    ]
  }'
```

## Python 绑定（llama-cpp-python）

`pip install llama-cpp-python`（CUDA：`CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir`；Metal：`CMAKE_ARGS="-DGGML_METAL=on" ...`）。

### 基础生成

```python
from llama_cpp import Llama

llm = Llama(
    model_path="./model-q4_k_m.gguf",
    n_ctx=4096,
    n_gpu_layers=35,     # 0 for CPU, 99 to offload everything
    n_threads=8,
)

out = llm("What is machine learning?", max_tokens=256, temperature=0.7)
print(out["choices"][0]["text"])
```

### 对话 + 流式

```python
llm = Llama(
    model_path="./model-q4_k_m.gguf",
    n_ctx=4096,
    n_gpu_layers=35,
    chat_format="llama-3",   # or "chatml", "mistral", etc.
)

resp = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"},
    ],
    max_tokens=256,
)
print(resp["choices"][0]["message"]["content"])

# Streaming
for chunk in llm("Explain quantum computing:", max_tokens=256, stream=True):
    print(chunk["choices"][0]["text"], end="", flush=True)
```

### Embedding

```python
llm = Llama(model_path="./model-q4_k_m.gguf", embedding=True, n_gpu_layers=35)
vec = llm.embed("This is a test sentence.")
print(f"Embedding dimension: {len(vec)}")
```

也可以直接从 Hub 加载 GGUF：

```python
llm = Llama.from_pretrained(
    repo_id="bartowski/Llama-3.2-3B-Instruct-GGUF",
    filename="*Q4_K_M.gguf",
    n_gpu_layers=35,
)
```

## 选择量化档

先看 Hub 页面，通用经验法则次之。

- 优先用 HF 标记为与用户硬件配置兼容的那个确切量化档。
- 通用对话从 `Q4_K_M` 起步。
- 代码或技术工作，内存允许时优先 `Q5_K_M` 或 `Q6_K`。
- RAM 预算极紧时，考虑 `Q3_K_M`、`IQ` 变体，或仅在用户明确更看重装得下而非质量时用 `Q2` 变体。
- 多模态仓库要单独提 `mmproj-*.gguf`。projector 不是主模型文件。
- 不要规范化仓库原生标签。页面写 `UD-Q4_K_M`，就报 `UD-Q4_K_M`。

## 从仓库提取可用 GGUF

用户问有哪些 GGUF 时，返回：

- 文件名
- 文件大小
- 量化标签
- 是主模型还是辅助 projector

除非被要求，否则忽略：

- README
- BF16 分片文件
- imatrix blob 或校准产物

这一步用 tree API：

- `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`

对 `unsloth/Qwen3.6-35B-A3B-GGUF` 这样的仓库，local-app 页面可能显示 `UD-Q4_K_M`、`UD-Q5_K_M`、`UD-Q6_K`、`Q8_0` 等量化 chip，而 tree API 会带字节大小暴露诸如 `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`、`Qwen3.6-35B-A3B-Q8_0.gguf` 的确切文件路径。用 tree API 把量化标签变成确切文件名。

## 搜索模式

直接套用这些 URL 形状：

```text
https://huggingface.co/models?apps=llama.cpp&sort=trending
https://huggingface.co/models?search=<term>&apps=llama.cpp&sort=trending
https://huggingface.co/models?search=<term>&apps=llama.cpp&num_parameters=min:0,max:24B&sort=trending
https://huggingface.co/<repo>?local-app=llama.cpp
https://huggingface.co/api/models/<repo>/tree/main?recursive=true
https://huggingface.co/<repo>/tree/main
```

## 输出格式

回答发现类请求时，优先给这种紧凑的结构化结果：

```text
Repo: <repo>
Recommended quant from HF: <label> (<size>)
llama-server: <command>
Other GGUFs:
- <filename> - <size>
- <filename> - <size>
Source URLs:
- <local-app URL>
- <tree API URL>
```

## 参考

- **[hub-discovery.md](references/hub-discovery.md)** - 纯 URL 的 Hugging Face 工作流、搜索模式、GGUF 提取与命令重建
- **[advanced-usage.md](references/advanced-usage.md)** — 投机解码、批量推理、语法约束生成、LoRA、多 GPU、自定义构建、基准脚本
- **[quantization.md](references/quantization.md)** — 量化质量取舍、何时用 Q4/Q5/Q6/IQ、模型大小缩放、imatrix
- **[server.md](references/server.md)** — 直接从 Hub 启动服务、OpenAI API endpoint、Docker 部署、NGINX 负载均衡、监控
- **[optimization.md](references/optimization.md)** — CPU 线程、BLAS、GPU offload 经验法则、batch 调参、基准
- **[troubleshooting.md](references/troubleshooting.md)** — 安装/转换/量化/推理/服务问题、Apple Silicon、调试

## 资源

- **GitHub**：https://github.com/ggml-org/llama.cpp
- **Hugging Face GGUF + llama.cpp 文档**：https://huggingface.co/docs/hub/gguf-llamacpp
- **Hugging Face Local Apps 文档**：https://huggingface.co/docs/hub/main/local-apps
- **Hugging Face Local Agents 文档**：https://huggingface.co/docs/hub/agents-local
- **示例 local-app 页面**：https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF?local-app=llama.cpp
- **示例 tree API**：https://huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-GGUF/tree/main?recursive=true
- **示例 llama.cpp 搜索**：https://huggingface.co/models?num_parameters=min:0,max:24B&apps=llama.cpp&sort=trending
- **License**：MIT
