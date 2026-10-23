---
name: evaluating-llms-harness
description: "用 lm-eval-harness 跑 LLM 基准（MMLU、GSM8K 等）时使用。只要要测模型质量、做模型对比或报学术分数，就主动加载，即使用户只说「对比一下这两个模型」。"
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [lm-eval, transformers, vllm]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Evaluation, LM Evaluation Harness, Benchmarking, MMLU, HumanEval, GSM8K, EleutherAI, Model Quality, Academic Benchmarks, Industry Standard]

---

# lm-evaluation-harness — LLM 基准测试

## 内容概览

在 60+ 学术基准（MMLU、HumanEval、GSM8K、TruthfulQA、HellaSwag）上评测 LLM。用于基准模型质量、对比模型、报告学术结果或跟踪训练进展。这是 EleutherAI、HuggingFace 及各大实验室采用的行业标准。支持 HuggingFace、vLLM、API。

## 快速开始

lm-evaluation-harness 用标准化 prompt 与指标在 60+ 学术基准上评测 LLM。

**安装**：
```bash
pip install lm-eval
```

**评测任意 HuggingFace 模型**：
```bash
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu,gsm8k,hellaswag \
  --device cuda:0 \
  --batch_size 8
```

**查看可用任务**：
```bash
lm_eval --tasks list
```

## 常用工作流

### 工作流 1：标准基准评测

在核心基准（MMLU、GSM8K、HumanEval）上评测模型。

照抄这份清单：

```
Benchmark Evaluation:
- [ ] Step 1: Choose benchmark suite
- [ ] Step 2: Configure model
- [ ] Step 3: Run evaluation
- [ ] Step 4: Analyze results
```

**第 1 步：选择基准套件**

**核心推理基准**：
- **MMLU**（Massive Multitask Language Understanding）- 57 个学科，多选
- **GSM8K** - 小学数学应用题
- **HellaSwag** - 常识推理
- **TruthfulQA** - 真实性与事实性
- **ARC**（AI2 Reasoning Challenge）- 科学题

**代码基准**：
- **HumanEval** - Python 代码生成（164 题）
- **MBPP**（Mostly Basic Python Problems）- Python 编程

**标准套件**（发布模型时推荐）：
```bash
--tasks mmlu,gsm8k,hellaswag,truthfulqa,arc_challenge
```

**第 2 步：配置模型**

**HuggingFace 模型**：
```bash
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,dtype=bfloat16 \
  --tasks mmlu \
  --device cuda:0 \
  --batch_size auto  # Auto-detect optimal batch size
```

**量化模型（4-bit/8-bit）**：
```bash
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,load_in_4bit=True \
  --tasks mmlu \
  --device cuda:0
```

**自定义 checkpoint**：
```bash
lm_eval --model hf \
  --model_args pretrained=/path/to/my-model,tokenizer=/path/to/tokenizer \
  --tasks mmlu \
  --device cuda:0
```

**第 3 步：跑评测**

```bash
# Full MMLU evaluation (57 subjects)
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu \
  --num_fewshot 5 \  # 5-shot evaluation (standard)
  --batch_size 8 \
  --output_path results/ \
  --log_samples  # Save individual predictions

# Multiple benchmarks at once
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu,gsm8k,hellaswag,truthfulqa,arc_challenge \
  --num_fewshot 5 \
  --batch_size 8 \
  --output_path results/llama2-7b-eval.json
```

**第 4 步：分析结果**

结果保存在 `results/llama2-7b-eval.json`：

```json
{
  "results": {
    "mmlu": {
      "acc": 0.459,
      "acc_stderr": 0.004
    },
    "gsm8k": {
      "exact_match": 0.142,
      "exact_match_stderr": 0.006
    },
    "hellaswag": {
      "acc_norm": 0.765,
      "acc_norm_stderr": 0.004
    }
  },
  "config": {
    "model": "hf",
    "model_args": "pretrained=meta-llama/Llama-2-7b-hf",
    "num_fewshot": 5
  }
}
```

### 工作流 2：跟踪训练进展

在训练过程中评测 checkpoint。

```
Training Progress Tracking:
- [ ] Step 1: Set up periodic evaluation
- [ ] Step 2: Choose quick benchmarks
- [ ] Step 3: Automate evaluation
- [ ] Step 4: Plot learning curves
```

**第 1 步：设置周期性评测**

每 N 个训练步评测一次：

```bash
#!/bin/bash
# eval_checkpoint.sh

CHECKPOINT_DIR=$1
STEP=$2

lm_eval --model hf \
  --model_args pretrained=$CHECKPOINT_DIR/checkpoint-$STEP \
  --tasks gsm8k,hellaswag \
  --num_fewshot 0 \  # 0-shot for speed
  --batch_size 16 \
  --output_path results/step-$STEP.json
```

**第 2 步：选择快速基准**

适合频繁评测的快基准：
- **HellaSwag**：1 块 GPU 上约 10 分钟
- **GSM8K**：约 5 分钟
- **PIQA**：约 2 分钟

频繁评测时避开（太慢）：
- **MMLU**：约 2 小时（57 个学科）
- **HumanEval**：需要执行代码

**第 3 步：自动化评测**

集成进训练脚本：

```python
# In training loop
if step % eval_interval == 0:
    model.save_pretrained(f"checkpoints/step-{step}")

    # Run evaluation
    os.system(f"./eval_checkpoint.sh checkpoints step-{step}")
```

或用 PyTorch Lightning 回调：

```python
from pytorch_lightning import Callback

class EvalHarnessCallback(Callback):
    def on_validation_epoch_end(self, trainer, pl_module):
        step = trainer.global_step
        checkpoint_path = f"checkpoints/step-{step}"

        # Save checkpoint
        trainer.save_checkpoint(checkpoint_path)

        # Run lm-eval
        os.system(f"lm_eval --model hf --model_args pretrained={checkpoint_path} ...")
```

**第 4 步：画学习曲线**

```python
import json
import matplotlib.pyplot as plt

# Load all results
steps = []
mmlu_scores = []

for file in sorted(glob.glob("results/step-*.json")):
    with open(file) as f:
        data = json.load(f)
        step = int(file.split("-")[1].split(".")[0])
        steps.append(step)
        mmlu_scores.append(data["results"]["mmlu"]["acc"])

# Plot
plt.plot(steps, mmlu_scores)
plt.xlabel("Training Step")
plt.ylabel("MMLU Accuracy")
plt.title("Training Progress")
plt.savefig("training_curve.png")
```

### 工作流 3：对比多个模型

用于模型对比的基准套件。

```
Model Comparison:
- [ ] Step 1: Define model list
- [ ] Step 2: Run evaluations
- [ ] Step 3: Generate comparison table
```

**第 1 步：定义模型清单**

```bash
# models.txt
meta-llama/Llama-2-7b-hf
meta-llama/Llama-2-13b-hf
mistralai/Mistral-7B-v0.1
microsoft/phi-2
```

**第 2 步：跑评测**

```bash
#!/bin/bash
# eval_all_models.sh

TASKS="mmlu,gsm8k,hellaswag,truthfulqa"

while read model; do
    echo "Evaluating $model"

    # Extract model name for output file
    model_name=$(echo $model | sed 's/\//-/g')

    lm_eval --model hf \
      --model_args pretrained=$model,dtype=bfloat16 \
      --tasks $TASKS \
      --num_fewshot 5 \
      --batch_size auto \
      --output_path results/$model_name.json

done < models.txt
```

**第 3 步：生成对比表**

```python
import json
import pandas as pd

models = [
    "meta-llama-Llama-2-7b-hf",
    "meta-llama-Llama-2-13b-hf",
    "mistralai-Mistral-7B-v0.1",
    "microsoft-phi-2"
]

tasks = ["mmlu", "gsm8k", "hellaswag", "truthfulqa"]

results = []
for model in models:
    with open(f"results/{model}.json") as f:
        data = json.load(f)
        row = {"Model": model.replace("-", "/")}
        for task in tasks:
            # Get primary metric for each task
            metrics = data["results"][task]
            if "acc" in metrics:
                row[task.upper()] = f"{metrics['acc']:.3f}"
            elif "exact_match" in metrics:
                row[task.upper()] = f"{metrics['exact_match']:.3f}"
        results.append(row)

df = pd.DataFrame(results)
print(df.to_markdown(index=False))
```

输出：
```
| Model                  | MMLU  | GSM8K | HELLASWAG | TRUTHFULQA |
|------------------------|-------|-------|-----------|------------|
| meta-llama/Llama-2-7b  | 0.459 | 0.142 | 0.765     | 0.391      |
| meta-llama/Llama-2-13b | 0.549 | 0.287 | 0.801     | 0.430      |
| mistralai/Mistral-7B   | 0.626 | 0.395 | 0.812     | 0.428      |
| microsoft/phi-2        | 0.560 | 0.613 | 0.682     | 0.447      |
```

### 工作流 4：用 vLLM 评测（推理更快）

用 vLLM 后端，评测快 5-10 倍。

```
vLLM Evaluation:
- [ ] Step 1: Install vLLM
- [ ] Step 2: Configure vLLM backend
- [ ] Step 3: Run evaluation
```

**第 1 步：安装 vLLM**

```bash
pip install vllm
```

**第 2 步：配置 vLLM 后端**

```bash
lm_eval --model vllm \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,tensor_parallel_size=1,dtype=auto,gpu_memory_utilization=0.8 \
  --tasks mmlu \
  --batch_size auto
```

**第 3 步：跑评测**

vLLM 比标准 HuggingFace 快 5-10 倍：

```bash
# Standard HF: ~2 hours for MMLU on 7B model
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu \
  --batch_size 8

# vLLM: ~15-20 minutes for MMLU on 7B model
lm_eval --model vllm \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,tensor_parallel_size=2 \
  --tasks mmlu \
  --batch_size auto
```

## 何时用、何时换替代方案

**以下情况用 lm-evaluation-harness：**
- 为学术论文做模型基准
- 在标准任务上对比模型质量
- 跟踪训练进展
- 报告标准化指标（大家用同样的 prompt）
- 需要可复现的评测

**以下情况改用替代方案：**
- **HELM**（Stanford）：更宽的评测（公平性、效率、校准）
- **AlpacaEval**：用 LLM 评委评指令遵循
- **MT-Bench**：对话式多轮评测
- **自定义脚本**：领域专属评测

## 常见问题

**问题：评测太慢**

用 vLLM 后端：
```bash
lm_eval --model vllm \
  --model_args pretrained=model-name,tensor_parallel_size=2
```

或减少 fewshot 示例：
```bash
--num_fewshot 0  # Instead of 5
```

或只评测 MMLU 的子集：
```bash
--tasks mmlu_stem  # Only STEM subjects
```

**问题：显存不足**

减小 batch size：
```bash
--batch_size 1  # Or --batch_size auto
```

用量化：
```bash
--model_args pretrained=model-name,load_in_8bit=True
```

开启 CPU offloading：
```bash
--model_args pretrained=model-name,device_map=auto,offload_folder=offload
```

**问题：结果与报告不符**

检查 fewshot 数量：
```bash
--num_fewshot 5  # Most papers use 5-shot
```

检查确切的任务名：
```bash
--tasks mmlu  # Not mmlu_direct or mmlu_fewshot
```

确认模型与 tokenizer 匹配：
```bash
--model_args pretrained=model-name,tokenizer=same-model-name
```

**问题：HumanEval 不执行代码**

安装执行所需的依赖：
```bash
pip install human-eval
```

开启代码执行：
```bash
lm_eval --model hf \
  --model_args pretrained=model-name \
  --tasks humaneval \
  --allow_code_execution  # Required for HumanEval
```

## 进阶主题

**基准说明**：全部 60+ 任务的详细描述、测什么、怎么解读，见 [references/benchmark-guide.md](references/benchmark-guide.md)。

**自定义任务**：创建领域专属评测任务，见 [references/custom-tasks.md](references/custom-tasks.md)。

**API 评测**：评测 OpenAI、Anthropic 等 API 模型，见 [references/api-evaluation.md](references/api-evaluation.md)。

**多 GPU 策略**：数据并行与张量并行评测，见 [references/distributed-eval.md](references/distributed-eval.md)。

## 硬件要求

- **GPU**：NVIDIA（CUDA 11.8+），也能跑 CPU（非常慢）
- **显存**：
  - 7B 模型：16GB（bf16）或 8GB（8-bit）
  - 13B 模型：28GB（bf16）或 14GB（8-bit）
  - 70B 模型：需要多 GPU 或量化
- **耗时**（7B 模型，单块 A100）：
  - HellaSwag：10 分钟
  - GSM8K：5 分钟
  - MMLU（全量）：2 小时
  - HumanEval：20 分钟

## 资源

- GitHub：https://github.com/EleutherAI/lm-evaluation-harness
- 文档：https://github.com/EleutherAI/lm-evaluation-harness/tree/main/docs
- 任务库：60+ 任务，含 MMLU、GSM8K、HumanEval、TruthfulQA、HellaSwag、ARC、WinoGrande 等
- 排行榜：https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard（用的就是这个 harness）



