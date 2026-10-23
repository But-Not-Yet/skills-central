# PolyStrata 备胎引擎路（Windows 笔记本）

PolyStrata 是 Strata 的 Windows 分支 fork（`VecSzn/PolyStrata`），跑在笔记本（NVIDIA 5070 Ti 12G）上，与生产机 Strata 分属不同机器、不同 GPU 架构。它是 Ornith 等模型的备胎/并行节点，不是生产主力。下面三条是本机实测里「不问就踩」的坑。

## 1. Web UI 不是 llama.cpp 的，别误以为 llama 还在跑

PolyStrata 自带一套定制界面，**不是** llama.cpp 的 `chat.html` + `webui.js` + `#chat-output` 那套。它的首页只引用 `web/app.js`（约 64KB，自标注 "the PolyStrata web app: Chat, Monitor, About. No framework, no network beyond this server."）+ 三个 `st-` 前缀 CSS（`st-tab`、`st-composer`、`st-btn`、`st-card`），API 走 `v1/chat/completions`（OpenAI 风格）。

判据：`curl http://127.0.0.1:<port>/` 里看到 `<title>PolyStrata</title>`、`st-` 前缀 class、`VecSzn/PolyStrata` GitHub 链接 = PolyStrata 界面；看到 `chat.html`/`webui.js`/`#chat-output` = llama.cpp。两者视觉不同，但同一台机器上若两个都在跑，用户浏览器可能打开的是旧标签页（llama.cpp 昨晚在 8082 跑过），不是当前服务。**先查端口-进程-HTML 三证，再下「谁在跑」的结论。**

## 2. host 绑定：用命令行显式 `--host`，别信 setup.py 写 config

PolyStrata 的 `setup.py` 每次跑都 `write_config` 整体重写模型 config（`SETUP_KEYS` 里确实含 `host`，但实测仍会丢失）。`--host` 经 setup 的 keep-into-config 路径（#179）在我们这台不生效——config 被某轮 setup 重写洗掉，server 仍绑 `127.0.0.1`，VPN 对面必然 unreachable。

**可靠做法：绕过 setup.py，直接起 server.py 并显式带 `--host`。**

```bat
@echo off
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do taskkill /f /pid %%p >nul 2>&1
timeout /t 3 /nobreak >nul
echo POLY_AT %DATE% %TIME% (direct server, host from cmdline) > D:\LLM\poly_serve.log
cd /d D:\LLM\PolyStrata
.venv\Scripts\python.exe serve\server.py --engine strata --config D:\LLM\PolyStrata\strata-ornith-apex-i-quality.json --host 0.0.0.0 --port 8080 >> D:\LLM\poly_serve.log 2>&1
echo POLY_DIRECT_EXIT=%ERRORLEVEL% >> D:\LLM\poly_serve.log
echo SENTINEL_POLY_EXIT >> D:\LLM\poly_serve.log
```

要点：
- **杀旧进程以 netstat LISTENING 的 PID 为准**，不要只靠 `taskkill /im strata-poly.exe`——后者有时杀不动真监听者（实测 `strata-poly.exe` 的 PID 与占 8080 的 python 进程 PID 不是同一个，`/im` 杀的是父壳，真监听者纹丝不动）。`netstat -ano | findstr :8080 | findstr LISTENING` 第五 token 才是占端口者，`taskkill /f /pid <pid>` 精确杀。
- **launcher .bat 的最后一行前台执行 server.py，别让它退出**——setup 型脚本经计划任务跑时 launcher 一退，控制台会话回收整棵进程树（见 `ssh-windows-remote-ops` 第 2 节）。server.py 停在「起服务」那一步不退，计划任务会话就一直抱着它。
- 起完读**新日志**里 `ready:` 行，再 `netstat` 确认监听地址是 `0.0.0.0` 不是 `127.0.0.1`。`ready:` 自报 `127.0.0.1` 时先别信，以 netstat 为准。
- 改完 launcher 重跑，schtasks 任务目标用 `/delete /f` + `/create` 重建（别 `/change /tr`，会按旧路径跑）。

## 3. --max-context 与 KV

- config args 里写 `--max-context N`（如 262144）。Ornith 是 MoE（每四层一层 full-attention），KV 成本比 dense 模型低；引擎 RSS 走 RAM 不走 VRAM（实测 RSS 14–15G 级，吃内存不是显存）。
- poly 的 KV 走自适应流式（auto 兜底），不用像生产机 Strata 那样算 KV 字节预算。
- 改 context 先改 config args 里的 `--max-context` 值，再起服务；判据以 `/v1/models` 返回的 `n_ctx` 为准（跨机 `curl http://<VPN-IP>:8080/v1/models` 复验）。

## 4. 起服与验证顺序（速查）

见 §2 的 launcher 与主 SKILL.md 的「验证配方」；本文件只补模型实底。

## 5. 模型实底：别名、量化、微调分开查

- 三处证据：`GET /props` 看 `model_path`/`model_alias`/`build_info`；`GET /metrics` 看 `engine.model`、`vram_free_mib`、`expert_cache_mib`、`conversation_cache`、`total_slots`；Windows 进程命令行看实际 `--model`/`--max-context`。**以进程命令行为准**：磁盘上的旧 config 可能指向别的模型（实测旧 `strata-ornith.json` 指 Huihui 23G/32768，实际进程跑 APEX 22.8GB/262144）。
- `APEX` 是 MoE 感知量化，不是微调；`MTP` 是模型原生层；`expert-profile.txt` 是运行时专家缓存画像。三者都容易被误认成 fine-tune。
- 量化档看体积加 HF 量化表，不靠猜：APEX I-Quality 22.09GB；注意力 Q6_K、共享专家 Q8_0、路由边缘 Q6_K/Q5_K、中段 blk10-29 IQ4_XS；I-Balanced 24.43GB、I-Compact 16.24GB、I-Mini 13.38GB。
- 12GB 笔记本跑 22.8GB 模型靠专家缓存/内存：体检时 60 点采样 VRAM 11.45–11.48/12.82GB、RAM 31.75–32.06/33.84GB，余量很薄。先降 `--conversation-cache-mib`（8192→4096/6144）再考虑换模型；`/metrics` 的 `vram_free_mib` 与 `ram_used` 是硬证据。
- 换模型判断：Ornith-1.5-35B-A3B 的 SWE-bench Verified 79、GPQA 89.2；LFM2.5-24B-A2B 是 51、74.4，更快更小但编码弱，适合工具路由/端侧，不适合当编码主力。35B MoE 微调成本高且引入新变量，先改任务书/推理档位，不要先微调。
