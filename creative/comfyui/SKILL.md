---
name: comfyui
description: "用 ComfyUI 跑扩散工作流生成图像 / 视频 / 音频时使用。只要要出图、跑 SDXL/Flux/SD3 工作流、做 img2img / inpaint / ControlNet，或装模型与自定义节点，就主动加载。即使用户只说「生成一张图」。支持本地与 Comfy Cloud。"
version: 5.1.0
author: [kshitijk4poor, alt-glitch, purzbeats]
license: MIT
platforms: [macos, linux, windows]
compatibility: "Requires ComfyUI (local, Comfy Desktop, or Comfy Cloud) and comfy-cli (auto-installed via pipx/uvx by the setup script)."
prerequisites:
  commands: ["python3"]
setup:
  help: "Run scripts/hardware_check.py FIRST to decide local vs Comfy Cloud; then scripts/comfyui_setup.sh auto-installs locally (or use Cloud API key for platform.comfy.org)."
metadata:
  hermes:
    tags:
      - comfyui
      - image-generation
      - stable-diffusion
      - flux
      - sd3
      - wan-video
      - hunyuan-video
      - creative
      - generative-ai
      - video-generation
    related_skills: [stable-diffusion-image-generation]
    category: creative
---

# ComfyUI

通过 ComfyUI 生成图像、视频、音频与 3D 内容：用官方 `comfy-cli` 做安装 / 生命周期管理。用直接的 REST/WebSocket API 执行工作流。

## 本 skill 内容

**参考文档（`references/`）：**

- `official-cli.md` —— 每一条 `comfy ...` 命令，含标志
- `rest-api.md` —— REST + WebSocket 端点（本地 + 云端）、负载 schema
- `workflow-format.md` —— API 格式 JSON、常见节点类型、参数映射
- `template-integrity.md` —— 把 `comfyui-workflow-templates` 从编辑器格式转成 API 格式：Reroute 绕过、带点的动态输入 key（`values.a`、`resize_type.width`）。云端的怪癖（302 重定向、免费档 1 个并发任务、1080p VRAM 上限）、Discord 兼容的 ffmpeg 拼接。作者 [@purzbeats](https://github.com/purzbeats)。只要你从官方模板起步，就加载它。

**脚本（`scripts/`）：**

| 脚本 | 用途 |
|--------|---------|
| `_common.py` | 共享的 HTTP、云端路由、节点目录（不要直接运行） |
| `hardware_check.py` | 探测 GPU/VRAM/磁盘 → 建议本地还是 Comfy Cloud |
| `comfyui_setup.sh` | 硬件检测 + comfy-cli + ComfyUI 安装 + 启动 + 校验 |
| `extract_schema.py` | 读取工作流 → 列出可控参数 + 模型依赖 |
| `check_deps.py` | 对照运行中的服务器检查工作流 → 列出缺失的节点 / 模型 |
| `auto_fix_deps.py` | 先跑 check_deps，再 `comfy node install` / `comfy model download` |
| `run_workflow.py` | 注入参数、提交、监控、下载输出（HTTP 或 WS） |
| `run_batch.py` | 带参数扫描地提交工作流 N 次，并行度到你的档位 |
| `ws_monitor.py` | 执行中任务的实时 WebSocket 查看器（实时进度） |
| `health_check.py` | 校验清单运行器——comfy-cli + 服务器 + 模型 + 冒烟测试 |
| `fetch_logs.py` | 拉取指定 prompt_id 的 traceback / 状态消息 |

**示例工作流（`workflows/`）：** SD 1.5、SDXL、Flux Dev、SDXL img2img、SDXL inpaint、ESRGAN 放大、AnimateDiff 视频、Wan T2V。见 `workflows/README.md`。

## 何时使用

- 用户要求用 Stable Diffusion、SDXL、Flux、SD3 等生成图像
- 用户想运行某个具体的 ComfyUI 工作流文件
- 用户想把生成步骤串起来（txt2img → 放大 → 人脸修复）
- 用户需要 ControlNet、inpainting、img2img 或其他高级流水线
- 用户要求管理 ComfyUI 队列、检查模型，或安装自定义节点
- 用户想通过 AnimateDiff、Hunyuan、Wan、AudioCraft 等生成视频 / 音频 / 3D

## Architecture: Two Layers

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: comfy-cli (official lifecycle tool)        │
│   Setup, server lifecycle, custom nodes, models     │
│   → comfy install / launch / stop / node / model    │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│ Layer 2: REST/WebSocket API + skill scripts         │
│   Workflow execution, param injection, monitoring   │
│   POST /api/prompt, GET /api/view, WS /ws           │
│   → run_workflow.py, run_batch.py, ws_monitor.py    │
└─────────────────────────────────────────────────────┘
```

**为什么是两层？** 官方 CLI 在安装与服务器管理上很出色，但对工作流执行的支持极少。REST/WS API 填补了这个空缺——脚本处理 CLI 不管的参数注入、执行监控与输出下载。

## 快速开始

### 检测环境

```bash
# What's available?
command -v comfy >/dev/null 2>&1 && echo "comfy-cli: installed"
curl -s http://127.0.0.1:8188/system_stats 2>/dev/null && echo "server: running"

# Can this machine run ComfyUI locally? (GPU/VRAM/disk check)
python3 scripts/hardware_check.py
```

若什么都没装，见下方 **安装与上手**——但始终先跑硬件检测。

### 一行健康检查

```bash
python3 scripts/health_check.py
# → JSON: comfy_cli on PATH? server reachable? at least one checkpoint? smoke-test passes?
```

## 核心工作流

### 第 1 步：拿到 API 格式的工作流 JSON

工作流必须是 API 格式（每个节点有 `class_type`）。它们来自：

- ComfyUI web UI → **Workflow → Export (API)**（新版 UI）或旧的 "Save (API Format)" 按钮（旧版 UI）
- 本 skill 的 `workflows/` 目录（可直接运行的示例）
- 社区下载（civitai、Reddit、Discord）——通常是编辑器格式，必须载入 ComfyUI 再重新导出

编辑器格式（顶层 `nodes` 与 `links` 数组）**不能直接执行**。脚本会检测到并提示你重新导出。

### 第 2 步：看看哪些可调

```bash
python3 scripts/extract_schema.py workflow_api.json --summary-only
# → {"parameter_count": 12, "has_negative_prompt": true, "has_seed": true, ...}

python3 scripts/extract_schema.py workflow_api.json
# → full schema with parameters, model deps, embedding refs
```

### 第 3 步：带参数运行

```bash
# Local (defaults to http://127.0.0.1:8188)
python3 scripts/run_workflow.py \
  --workflow workflow_api.json \
  --args '{"prompt": "a beautiful sunset over mountains", "seed": -1, "steps": 30}' \
  --output-dir ./outputs

# Cloud (export API key once; uses correct /api routing automatically)
export COMFY_CLOUD_API_KEY="comfyui-..."
python3 scripts/run_workflow.py \
  --workflow workflow_api.json \
  --args '{"prompt": "..."}' \
  --host https://cloud.comfy.org \
  --output-dir ./outputs

# Real-time progress via WebSocket (requires `pip install websocket-client`)
python3 scripts/run_workflow.py \
  --workflow flux_dev.json \
  --args '{"prompt": "..."}' \
  --ws

# img2img / inpaint: pass --input-image to upload + reference automatically
python3 scripts/run_workflow.py \
  --workflow sdxl_img2img.json \
  --input-image image=./photo.png \
  --args '{"prompt": "make it watercolor", "denoise": 0.6}'

# Batch / sweep: 8 random seeds, parallel up to cloud tier limit
python3 scripts/run_batch.py \
  --workflow sdxl.json \
  --args '{"prompt": "abstract"}' \
  --count 8 --randomize-seed --parallel 3 \
  --output-dir ./outputs/batch
```

`seed` 传 `-1`（或配合 `--randomize-seed` 省略它）会为每次运行生成一个新的随机种子。

### 第 4 步：呈现结果

脚本会向 stdout 输出描述每个输出文件的 JSON：

```json
{
  "status": "success",
  "prompt_id": "abc-123",
  "outputs": [
    {"file": "./outputs/sdxl_00001_.png", "node_id": "9",
     "type": "image", "filename": "sdxl_00001_.png"}
  ]
}
```

## 决策树

| 用户说 | 工具 | 命令 |
|-----------|------|---------|
| **生命周期（用 comfy-cli）** | | |
| 「安装 ComfyUI」 | comfy-cli | `bash scripts/comfyui_setup.sh` |
| 「启动 ComfyUI」 | comfy-cli | `comfy launch --background` |
| 「停止 ComfyUI」 | comfy-cli | `comfy stop` |
| 「安装 X 节点」 | comfy-cli | `comfy node install <name>` |
| 「下载 X 模型」 | comfy-cli | `comfy model download --url <url> --relative-path models/checkpoints` |
| 「列出已安装模型」 | comfy-cli | `comfy model list` |
| 「列出已安装节点」 | comfy-cli | `comfy node show installed` |
| **执行（用脚本）** | | |
| 「一切就绪了吗？」 | script | `health_check.py`（可选带 `--workflow X --smoke-test`） |
| 「这个工作流里我能改什么？」 | script | `extract_schema.py W.json` |
| 「检查 W 的依赖是否满足」 | script | `check_deps.py W.json` |
| 「修复缺失依赖」 | script | `auto_fix_deps.py W.json` |
| 「生成一张图」 | script | `run_workflow.py --workflow W --args '{...}'` |
| 「用这张图」（img2img） | script | `run_workflow.py --input-image image=./x.png ...` |
| 「8 个随机种子的变体」 | script | `run_batch.py --count 8 --randomize-seed ...` |
| 「给我看实时进度」 | script | `ws_monitor.py --prompt-id <id>` |
| 「取回任务 X 的错误」 | script | `fetch_logs.py <prompt_id>` |
| **直接 REST** | | |
| 「队列里有什么？」 | REST | `curl http://HOST:8188/queue`（本地）或 `--host https://cloud.comfy.org` |
| 「取消它」 | REST | `curl -X POST http://HOST:8188/interrupt` |
| 「释放 GPU 显存」 | REST | `curl -X POST http://HOST:8188/free` |

## 安装与上手

当用户要求安装 ComfyUI 时。**第一件事是问他们想要 Comfy Cloud（托管、零安装、需 API key）还是本地（在自己机器上装 ComfyUI）**。在他们回答之前，不要开始跑安装命令或硬件检测。

**Official docs:** https://docs.comfy.org/installation
**CLI docs:** https://docs.comfy.org/comfy-cli/getting-started
**Cloud docs:** https://docs.comfy.org/get_started/cloud
**Cloud API:** https://docs.comfy.org/development/cloud/overview

### 第 0 步：问本地还是云端（永远先做）

建议话术：

> 「你想在本机本地运行 ComfyUI，还是用 Comfy Cloud？
>
> - **Comfy Cloud** —— 托管在 RTX 6000 Pro GPU 上，所有常见模型预装，零安装。需要 API key（实际运行工作流需要付费订阅。免费档只读）。没有够用的 GPU 时最佳。
> - **本地** —— 免费，但你的机器*必须*满足硬件要求：
>   - NVIDIA GPU，**≥6 GB VRAM**（SDXL 需 ≥8 GB，Flux / 视频需 ≥12 GB），或
>   - 支持 ROCm 的 AMD GPU（Linux），或
>   - Apple Silicon Mac（M1+），**≥16 GB 统一内存**（推荐 ≥32 GB）。
>   - Intel Mac 与没有 GPU 的机器*不行*——改用云端。
>
> 你想要哪种？」

分流：

- **云端** → 跳到 **Path A**。
- **本地** → 先跑硬件检测，再根据结论从 Path B–E 中选一条。
- **不确定** → 跑硬件检测，让结论来决定。

### 第 1 步：校验硬件（仅当用户选了本地）

```bash
python3 scripts/hardware_check.py --json
# Optional: also probe `torch` for actual CUDA/MPS:
python3 scripts/hardware_check.py --json --check-pytorch
```

| 结论    | 含义                                                       | 动作 |
|------------|---------------------------------------------------------------|--------|
| `ok`       | ≥8 GB VRAM（独显）或 ≥32 GB 统一内存（Apple Silicon）       | 本地安装——用报告里的 `comfy_cli_flag` |
| `marginal` | SD1.5 可用。SDXL 吃紧。Flux / 视频基本不行                  | 轻量工作流可本地，否则 **Path A（云端）** |
| `cloud`    | 无可用 GPU、<6 GB VRAM、<16 GB Apple 统一内存、Intel Mac、Rosetta Python | **改用云端**，除非用户明确强制本地 |

脚本还会显示 `wsl: true`（带 NVIDIA 直通的 WSL2）与 `rosetta: true`（Apple Silicon 上的 x86_64 Python——必须以 ARM64 重装）。

若结论是 `cloud` 但用户想要本地，不要默默继续。原样展示 `notes` 数组，并问他们是想 (a) 改用云端，还是 (b) 强制本地安装（对现代模型会 OOM 或慢到不可用）。

### 选择安装路径

先跑硬件检测。下表是在用户已告知其硬件时的回退：

| 情况 | 推荐路径 |
|-----------|------------------|
| 硬件检测为 `verdict: cloud` | **Path A：Comfy Cloud** |
| 无 GPU / 想零承诺先试试 | **Path A：Comfy Cloud** |
| Windows + NVIDIA + 非技术 | **Path B：ComfyUI Desktop** |
| Windows + NVIDIA + 技术 | **Path C：Portable** 或 **Path D：comfy-cli** |
| Linux + 任意 GPU | **Path D：comfy-cli**（最省事） |
| macOS + Apple Silicon | **Path B：Desktop** 或 **Path D：comfy-cli** |
| 无头 / 服务器 / CI / agent | **Path D：comfy-cli** |

全自动路径（硬件检测 → 安装 → 启动 → 校验）：

```bash
bash scripts/comfyui_setup.sh
# Or with overrides:
bash scripts/comfyui_setup.sh --m-series --port=8190 --workspace=/data/comfy
```

它内部会跑 `hardware_check.py`，当结论是 `cloud` 时拒绝本地安装（除非 `--force-cloud-override`），挑选正确的 `comfy-cli` 标志。并优先用 `pipx`/`uvx` 而非全局 `pip`，以免污染系统 Python。

---

### Path A：Comfy Cloud（无本地安装）

面向没有够用 GPU 或想零安装的用户。托管在 RTX 6000 Pro。

**Docs:** https://docs.comfy.org/get_started/cloud

1. 在 https://comfy.org/cloud 注册
2. 在 https://platform.comfy.org/login 生成 API key
3. 设置 key：
   ```bash
   export COMFY_CLOUD_API_KEY="comfyui-xxxxxxxxxxxx"
   ```
4. 运行工作流：
   ```bash
   python3 scripts/run_workflow.py \
     --workflow workflows/flux_dev_txt2img.json \
     --args '{"prompt": "..."}' \
     --host https://cloud.comfy.org \
     --output-dir ./outputs
   ```

**定价：** https://www.comfy.org/cloud/pricing
**并发任务：** Free/Standard 1、Creator 3、Pro 5。免费档
**无法通过 API 运行工作流**——只能浏览模型。`/api/prompt`、`/api/upload/*`、`/api/view` 等需要付费订阅。

---

### Path B：ComfyUI Desktop（Windows / macOS）

面向非技术用户的一键安装器。目前为 Beta。

**Docs:** https://docs.comfy.org/installation/desktop
- **Windows (NVIDIA):** https://download.comfy.org/windows/nsis/x64
- **macOS (Apple Silicon):** https://comfy.org

Desktop **不支持** Linux——用 Path D。

---

### Path C：ComfyUI Portable（仅 Windows）

**Docs:** https://docs.comfy.org/installation/comfyui_portable_windows

从 https://github.com/Comfy-Org/ComfyUI/releases 下载，解压，运行 `run_nvidia_gpu.bat`。通过 `update/update_comfyui_stable.bat` 更新。

---

### Path D：comfy-cli（全平台——推荐给 agent）

官方 CLI 是无头 / 自动化场景的最佳路径。

**Docs:** https://docs.comfy.org/comfy-cli/getting-started

#### 安装 comfy-cli

```bash
# Recommended:
pipx install comfy-cli
# Or use uvx without installing:
uvx --from comfy-cli comfy --help
# Or (if pipx/uvx unavailable):
pip install --user comfy-cli
```

非交互式禁用分析：
```bash
comfy --skip-prompt tracking disable
```

#### 安装 ComfyUI

```bash
comfy --skip-prompt install --nvidia              # NVIDIA (CUDA)
comfy --skip-prompt install --amd                 # AMD (ROCm, Linux)
comfy --skip-prompt install --m-series            # Apple Silicon (MPS)
comfy --skip-prompt install --cpu                 # CPU only (slow)
comfy --skip-prompt install --nvidia --fast-deps  # uv-based dep resolution
```

默认位置：`~/comfy/ComfyUI`（Linux）、`~/Documents/comfy/ComfyUI`（macOS/Win）。用 `comfy --workspace /custom/path install` 覆盖。

#### 启动 / 校验

```bash
comfy launch --background                       # background daemon on :8188
comfy launch -- --listen 0.0.0.0 --port 8190    # LAN-accessible custom port
curl -s http://127.0.0.1:8188/system_stats      # health check
```

---

### Path E：手动安装（高级 / 不支持硬件）

面向 Ascend NPU、Cambricon MLU、Intel Arc 或其他不支持的硬件。

**Docs:** https://docs.comfy.org/installation/manual_install

```bash
git clone https://github.com/Comfy-Org/ComfyUI.git
cd ComfyUI
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu130
pip install -r requirements.txt
python main.py
```

---

### 安装后：下载模型

```bash
# SDXL (general purpose, ~6.5 GB)
comfy model download \
  --url "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" \
  --relative-path models/checkpoints

# SD 1.5 (lighter, ~4 GB, good for 6 GB cards)
comfy model download \
  --url "https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors" \
  --relative-path models/checkpoints

# Flux Dev fp8 (smaller variant, ~12 GB)
comfy model download \
  --url "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors" \
  --relative-path models/checkpoints

# CivitAI (set token first):
comfy model download \
  --url "https://civitai.com/api/download/models/128713" \
  --relative-path models/checkpoints \
  --set-civitai-api-token "YOUR_TOKEN"
```

列出已安装：`comfy model list`。

### 安装后：安装自定义节点

```bash
comfy node install comfyui-impact-pack             # popular utility pack
comfy node install comfyui-animatediff-evolved     # video generation
comfy node install comfyui-controlnet-aux          # ControlNet preprocessors
comfy node install comfyui-essentials              # common helpers
comfy node update all
comfy node install-deps --workflow=workflow.json   # install everything a workflow needs
```

### 安装后：校验

```bash
python3 scripts/health_check.py
# → comfy_cli on PATH? server reachable? checkpoints? smoke test?

python3 scripts/check_deps.py my_workflow.json
# → are this workflow's nodes/models/embeddings installed?

python3 scripts/run_workflow.py \
  --workflow workflows/sd15_txt2img.json \
  --args '{"prompt": "test", "steps": 4}' \
  --output-dir ./test-outputs
```

## 图片上传（img2img / Inpainting）

最简单的办法是在 `run_workflow.py` 里用 `--input-image`：

```bash
python3 scripts/run_workflow.py \
  --workflow workflows/sdxl_img2img.json \
  --input-image image=./photo.png \
  --args '{"prompt": "make it cyberpunk", "denoise": 0.6}'
```

该标志上传 `photo.png`，再把其服务端文件名注入到名为 `image` 的 schema 参数。inpainting 就传两个：

```bash
python3 scripts/run_workflow.py \
  --workflow workflows/sdxl_inpaint.json \
  --input-image image=./photo.png \
  --input-image mask_image=./mask.png \
  --args '{"prompt": "fill with flowers"}'
```

通过 REST 手动上传：
```bash
curl -X POST "http://127.0.0.1:8188/upload/image" \
  -F "image=@photo.png" -F "type=input" -F "overwrite=true"
# Returns: {"name": "photo.png", "subfolder": "", "type": "input"}

# Cloud equivalent:
curl -X POST "https://cloud.comfy.org/api/upload/image" \
  -H "X-API-Key: $COMFY_CLOUD_API_KEY" \
  -F "image=@photo.png" -F "type=input" -F "overwrite=true"
```

## 云端注意事项

- **Base URL：** `https://cloud.comfy.org`
- **认证：** `X-API-Key` 头（WebSocket 用 `?token=KEY`）
- **API key：** 设置一次 `$COMFY_CLOUD_API_KEY`，脚本会自动读取
- **输出下载：** `/api/view` 返回 302 到签名 URL。脚本会跟随它，并在从存储后端拉取前剥离 `X-API-Key`（不要把 API key 泄漏给 S3/CloudFront）。
- **与本地 ComfyUI 的端点差异：**
  - `/api/object_info`、`/api/queue`、`/api/userdata` —— 免费档 **403**。仅付费可用。
  - `/history` 在云端重命名为 `/history_v2`（脚本自动路由）。
  - `/models/<folder>` 在云端重命名为 `/experiment/models/<folder>`（脚本自动路由）。
  - WebSocket 里的 `clientId` 目前被忽略——某用户的所有连接会收到同一广播。在客户端按 `prompt_id` 过滤。
  - `subfolder` 在上传时被接受但被忽略——云端是扁平命名空间。
- **并发任务：** Free/Standard: 1、Creator: 3、Pro: 5。超出的会自动排队。用 `run_batch.py --parallel N` 跑满你的档位。

## 队列与系统管理

```bash
# Local
curl -s http://127.0.0.1:8188/queue | python3 -m json.tool
curl -X POST http://127.0.0.1:8188/queue -d '{"clear": true}'    # cancel pending
curl -X POST http://127.0.0.1:8188/interrupt                      # cancel running
curl -X POST http://127.0.0.1:8188/free \
  -H "Content-Type: application/json" \
  -d '{"unload_models": true, "free_memory": true}'

# Cloud — same paths under /api/, plus:
python3 scripts/fetch_logs.py --tail-queue --host https://cloud.comfy.org
```

## 易错点

1. **必须 API 格式** —— 每个脚本与 `/api/prompt` 端点都要求 API 格式的工作流 JSON。脚本会检测编辑器格式（顶层 `nodes` 与 `links` 数组），并提示你通过 "Workflow → Export (API)"（新版 UI）或 "Save (API Format)"（旧版 UI）重新导出。

2. **服务器必须运行** —— 所有执行都需要一个活着的服务器。`comfy launch --background` 会启动一个。用 `curl http://127.0.0.1:8188/system_stats` 校验。

3. **模型名必须精确** —— 区分大小写，包含文件扩展名。`check_deps.py` 会做模糊匹配（带 / 不带扩展名与文件夹前缀），但工作流本身必须用规范名。用 `comfy model list` 查看已安装内容。

4. **缺失自定义节点** —— "class_type not found" 意味着某个必需节点没安装。`check_deps.py` 会报告该装哪个包。`auto_fix_deps.py` 替你执行安装。

5. **工作目录** —— `comfy-cli` 会自动检测 ComfyUI 工作区。若命令报 "no workspace found"，用 `comfy --workspace /path/to/ComfyUI <command>` 或 `comfy set-default /path/to/ComfyUI`。

6. **云端免费档 API 限制** —— 免费账号下 `/api/prompt`、`/api/view`、`/api/upload/*`、`/api/object_info` 都返回 403。`health_check.py` 与 `check_deps.py` 会优雅处理并给出清晰提示。

7. **视频 / 音频工作流的超时** —— 当输出节点是 `VHS_VideoCombine`、`SaveVideo` 等时会自动检测。默认从 300 秒跳到 900 秒。用 `--timeout 1800` 显式覆盖。

8. **输出文件名里的路径穿越** —— 服务器提供的文件名会经 `safe_path_join`，拒绝任何逃出 `--output-dir` 的路径。保持这个保护开启——带自定义保存节点的工作流可能产生任意路径。

9. **工作流 JSON 就是任意代码** —— 自定义节点会运行 Python，所以提交一个未知工作流与 `eval` 有相同的信任画像。运行前先审查来自不可信来源的工作流。

10. **自动随机种子** —— 在 `--args` 里传 `seed: -1`（或用 `--randomize-seed` 并省略 seed）以获得每次运行的新种子。实际种子会记录到 stderr。

11. **`tracking` 提示** —— 首次运行 `comfy` 可能询问分析。用 `comfy --skip-prompt tracking disable` 非交互式跳过。`comfyui_setup.sh` 会替你做。

## 校验清单

用 `python3 scripts/health_check.py` 一次跑完整个清单。手动版：

- [ ] `hardware_check.py` 结论为 `ok`，或用户明确选择了 Comfy Cloud
- [ ] `comfy --version` 可用（或 `uvx --from comfy-cli comfy --help`）
- [ ] `curl http://HOST:PORT/system_stats` 返回 JSON
- [ ] `comfy model list` 显示至少一个 checkpoint（本地），或
      `/api/experiment/models/checkpoints` 返回模型（云端）
- [ ] 工作流 JSON 是 API 格式
- [ ] `check_deps.py` 报告 `is_ready: true`（或云端免费档仅有
      `node_check_skipped`）
- [ ] 用小工作流试跑完成。输出落在 `--output-dir`
