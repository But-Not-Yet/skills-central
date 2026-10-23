---
name: minicpmo-duplex-laptop
description: 操作笔记本 MiniCPM-o 双工语音栈时用：编译、起停、注入人设、级联复用。
version: 1.0.0
author: Nekonya
license: MIT
metadata:
  hermes:
    tags: [minicpmo, duplex, windows, llama-cpp-omni, laptop]
---

# MiniCPM-o 4.5 双工栈（笔记本 Windows）

## When to Use
碰笔记本上这套双工语音栈就算：编译/重建 omni 引擎、起停 OmniSvc 服务、改人设注入、跑 duplex_probe、诊断 decode 崩溃，以及级联改造里复用它的 ASR/TTS/双工前端。

2026-10-21 主人裁定该路线弃用（9B 无思考能力，见 mem0），但栈活着，级联改造时耳朵和嘴复用这套。全程开源：llama.cpp-omni (MIT) + 官方 GGUF (Apache 2.0)。

## 硬件与路径
- 笔记本 laptop-training（192.168.50.29），RTX 5070 Ti Laptop 12GB，模型加载后显存 11310/12227 MiB（92.5%，极紧，别再往里塞东西）。
- 引擎：`D:\LLM\omni-v1.0.22`（worktree，tag v1.0.22 官方零补丁）。**master 有 decode 崩溃回归**（0xc0000005 @ +0x15c1a，issue #114），必须用 v1.0.22。
- Demo：`D:\LLM\MiniCPM-o-Demo`（Comni 分支），venv `.venv2`。权重 `D:\LLM\MiniCPM-o-4_5-gguf`（Q4_K_M）。
- 端口：cpp 引擎 19080、worker 22440、gateway 8040。页面 `http://localhost:8040/audio_duplex`。
- 编排：计划任务 `OmniSvc`（脚本 `D:\LLM\run_omni_service.bat`）。

## 编译配方（MSVC+CUDA）
- `cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON -DLLAMA_CURL=OFF -DCMAKE_CXX_FLAGS="/Zc:preprocessor" -DCMAKE_CUDA_FLAGS="-Xcompiler=/Zc:preprocessor"`。CURL=OFF 防找不到 CURL；/Zc:preprocessor 修 CCCL fatal C1189。203 目标约 7 分钟。
- master 才有 `src/llama-moe-slot.cpp`（POSIX iovec 缺 _WIN32 保护，需 6 行补丁）；v1.0.22 无此文件，不用打。
- demo 的 cpp_backend 找 `llama-server.exe`，产物名是 `llama-omni-server.exe`——复制同名文件接上。

## 起停服务（关键坑）
- **`schtasks /run` 对已在运行的任务不放第二份**——改配置后必须杀再启：跑 `D:\LLM\kill_omni.bat`（按端口 19080/22440/8040 杀 + `taskkill /f /im llama-server.exe`），再 `schtasks /run /tn OmniSvc`。
- bat 必须 CRLF；SSH 回显 GBK，脚本只打 ASCII。

## 人设（SOUL）注入——唯一活口
- **双工模式下前端 textarea 完全无效**：cpp_backend `[BUG FIX 3]` 后 duplex_prepare 跳过 update_session_config（调它清 KV 会段错误），注释自招「前端切 system_prompt 不再生效，要重启 worker」。上游把按钮藏了（`<summary style="display:none">`，原版就有，不是嫁接）。
- 唯一注入点 = 启动时 `_call_omni_init` 的 `voice_clone_prompt`（`<|im_start|>system\n{人设}\n<|audio_start|>`，拼 ref_audio）。
- 现行补丁：`core/processors/cpp_backend.py` 加 `_duplex_soul_content()` 读 `D:\LLM\MiniCPM-o-Demo\soul_prompt.txt`，传进两处 `_call_omni_init` 调用。备份 `.bak-soulinject`。改人设 = 改 soul_prompt.txt → kill_omni → 重启。
- **验收只认引擎层证据**：worker.log 里 `custom_prompt=True` + 打出人设开头 + `n_keep` 从 21 涨到 1021。textarea 有字 ≠ 注入成功（10-21 翻过车，被主人点破）。
- 容量红线：n_ctx=8192。完整 SOUL.md ≈9300 token 装不下；压缩版 3996 字节 ≈1000 token，n_keep=1021 占窗口 12.5%。SOUL 里塞不进的东西（长样例、统计表）砍掉不心疼，9B 执行不动。

## 性能实底（22:23 通话实测）
- 双工节拍中位 1.000s/轮踩实时线；worker qsize=0、采样窗口内 dropped=0；语音合成 1s 音频只用 0.17s（6 倍余量）。慢的不是引擎——是 9B 稠密底子加每秒强制发言没思考空间。

## 脚本存放
`~/.hermes/cache/scratch/`：`soul_duplex_v2.txt`（现行压缩人设）、`patch_soul_inject.py`、`kill_omni.bat`、`duplex_probe3-6.py`、`run_omni_v22_build.bat`、`omni_solo.bat`（solo 起 19081）。scratch 24h 会被清，重要件已上笔记本 `D:\LLM\`。
