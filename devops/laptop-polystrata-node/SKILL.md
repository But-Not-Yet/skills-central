---
author: Nekonya
description: 操作笔记本 Windows 上的 PolyStrata/Ornith 节点时使用。
license: MIT
metadata:
  hermes:
    related_skills: [ssh-windows-remote-ops, laptop-coder-node]
    tags: [windows, inference, polystrata, laptop]
name: laptop-polystrata-node
version: 1.0.0
---

# 笔记本 PolyStrata 节点（NODE II，Windows）

## When to Use
SSH 连不上/连错笔记本（IP 变动、VPN 断）、主人问怎么启动引擎、要改 PolyStrata config 或重启引擎、做 KV 量化/速度对比测量、查这台 Win11 的磁盘内存显存指标时加载。

主人家 Windows 笔记本上 Ornith/PolyStrata 推理节点的运维要点。SSH 别名 `laptop-training`。

## 连接
- **笔记本 LAN IP = 192.168.50.29**（2026-10-19 主人确认；192.168.50.231 是别人家的机器，别连）。ssh config 已改指 .29。
- VPN 地址 10.6.0.3 在笔记本休眠后常断，LAN 直连更可靠。
- 密钥 `~/.ssh/id_ed25519_deploy_laptop`，用户 Alonzo。

## 启停
- **启动方式（主人裁定 2026-10-19）：主人双击 `D:\LLM\poly_run8.bat`，点击才开，不加开机自启。** 不要恢复 schtasks 自启。
- agent 远程重启引擎：`ssh laptop-training 'cmd /c "D:\LLM\poly_run8.bat"'` 用 background=true。bat 退出码 255 + GBK 乱码属正常（cmd 包装层报错），杀旧起新真执行了——以 `Get-Process strata-poly | Select Id,StartTime` 的时间戳为准，别信退出码。
- 模型加载：冷缓存 1-2 分钟，热缓存（页面缓存捂着）约 10-15 秒。health `"loaded": true` 为准。
- config：`D:\LLM\PolyStrata\strata-ornith-apex-i-quality.json`（args 含 `--kv fp16 --vram-reserve-mib 512 --max-context 262144 --threads 9`；q8_0 备份 `.bak-q8`；sampling 0.6/0.95/20；host 0.0.0.0）。改 config 前 cp 备份。

## 模型体检（先看活体，不看旧 config）

- `curl -s http://192.168.50.29:8080/props` → `model_path`、`model_alias`、`build_info`、`n_ctx`、`chat_template_caps`。模型路径、量化档、上下文以这里为准。
- `curl -s http://192.168.50.29:8080/metrics` → engine（expert_cache_mib / vram_free_mib）、live、requests（prefill/decode tok/s、hit_rate）、hardware（VRAM/RAM/温度/功耗）、conversation_cache（复用率）。显存/内存是采样数组；单点只代表当刻，全程断言要读 history。
- 进程实锤：`Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'strata|llama' } | Select ProcessId,Name,CommandLine`。实际模型与参数看命令行，不看 `D:\LLM\strata-ornith.json` 这类旧配置。
- 量化：当前是 Ornith-1.5-35B-A3B APEX-MTP-I-Quality（22.8 GB；attention Q6_K、shared Q8_0、routed 中段 blk10-29 IQ4_XS）。APEX 是量化档名，MTP 是原生层，expert-profile 是运行时缓存画像，都不是微调。
- 配置漂移：`strata-ornith.json` 可能仍指旧 Huihui 23G/32768；真源是 `strata-ornith-apex-i-quality.json`。重启前对 `/props` 的 `model_path` 与配置 args 核一遍。
- coder 的 `reasoning_effort=xhigh` 会让 35B 在机械任务上长思考、易打转；机械卡降到 medium/high。体检时显存/内存常只剩约 510 MiB / 1.5 GiB，长上下文和第二个模型都会把它推爆。

模型对比与选择规则见 `references/ornith-apex-vs-lfm25.md`。

## 换型：先查引擎 docs 能力地图，再谈候选

- **`D:\LLM\PolyStrata\docs\` 里一个模型有专页，才算引擎真的跑过、量过。** 现有 `MODELS.md`（Qwen3.8-Flash-Next）、`GLM.md`、`DEEPSEEK.md`、`LFM.md`。`gemma4.cpp` 里有 26B-A4B 的代码但**没有 `GEMMA.md`**——代码在 ≠ 有人验证过，只能算未验证路径。**候选名单先过这道闸，过不了的不进基准比较。**
- **llama.cpp 支持 ≠ 这个引擎支持。** flint 的 `FlintForCausalLM`、Raon 的架构在 `src/poly/` 里根本没有，HF 趋势榜上有名也没用。
- **引擎 doc 页比 HF 模型卡可信**：`LFM.md` 给了每档量化的 RAM 需求、8 GB 笔记本上的实测 tok/s、每 token KV 字节数，还自己承认了长上下文失败案例（123K 三针只命中后两针，最远那针编造）。HF 卡不会写这些。
- 本节点 44 G 池（12 G VRAM + 32 G RAM）的结论：Qwen3.8-Flash-Next 要 37.6 GB 且 32 GB 内存档只能跑 Coder 版（官方注明弱在非代码与非英语，主人用中文，不合适）；GLM 5.3 Flash 321B、DeepSeek V4 Flash 90.9 GB 装不下；**LFM2.5-24B-A2B 是唯一落地的**。具体数字见 `references/ornith-apex-vs-lfm25.md`。

### 长上下文重复：根因与零成本先手

- **根因是架构额度用完了，不是采样写错。** Ornith 是 `qwen3_5_moe`：40 层里 30 层线性注意力，状态大小固定。上下文推到十万 token 以上，固定状态被早期内容填满，近期内容的精确记忆掉下去，模型忘了自己刚说过什么，于是复读。调采样压得住表面，压不住这个。
- **换模型之前先试 penalty，改一行重启五分钟。** `DETAILS.md` 写明 `presence_penalty` / `frequency_penalty` / `repetition_penalty` 都认，配 `penalty_last_n` 控制回看窗口（默认 64，长上下文重复要放宽到 512），三者都能直接写进 run config 的 `sampling` 块。当前 `strata-ornith-apex-i-quality.json` 只有 `temperature 0.6 / top_p 0.95 / top_k 20`，**三个 penalty 一个都没设**。
- **判引擎支持哪些采样参数，看 `DETAILS.md` 的请求字段清单，不要看 `--help`。** `--help` 只列命令行开关；`min_p` 与三类 penalty 是请求或 config 字段，`--help` 里没有不代表不支持。
- 压不住才说明是架构层的事，再上 LFM2.5。

## KV 量化 A/B 测法（2026-10-19 实测结案）
- 引擎 help 只有 `--kv fp16|q8_0`，**无 k8v4**（那是 engine 0.1.25/PR#120 的功能，0.1.45 poly 没有）。
- **KV 缓存不占显存**：poly 引擎把 KV 流进系统内存。37K token 提示词期间 nvidia-smi 峰值增量 ~0MB（fp16 和 q8_0 都一样）。所以 KV 量化省的是 RAM，不会变成「显存多装专家」。
- A/B 程序：改 config 去/加 `--kv q8_0` → 跑 poly_run8.bat 重启（新进程，查 StartTime）→ 同一 32K token 提示词（脚本 `D:\LLM\kv_ab.py`）→ 比 prefill tok/s。实测 fp16 2147 vs q8_0 2173，无差别。
- 验证「参数生效」别只信启动成功：这引擎不回显 kv/quant 行，log/metrics 都没有。
- 引擎 `vram_free_mib=510` 每次开机一致 = `--vram-reserve-mib 512` 实锤生效（/metrics engine 段可查）。

## 测量陷阱（这台 Win11 上）
- WMI 性能计数器子系统坏了：`Win32_PerfRawData/FormattedData_PerfDisk` 返 0/空，`Get-Counter` 也失败，`Win32_ComputerSystem.PhysicalMemory` 返 0。别反复重试这三条路。
- **磁盘测速用 Python FileStream 直读模型文件**（`D:\LLM\stream_read.py`，实测 990 EVO Plus 2TB = 2.1 GB/s）。
- 内存占用用进程 RSS 汇总（`D:\LLM\mem_now.ps1`）；显存用 nvidia-smi 或引擎 /metrics `hardware.gpu_mem_used`（两者口径差 ~300MB，引擎记账偏高，别混用比大小）。
- PowerShell 脚本坑：`-f` 格式化里不能直接调函数（先存变量）；含空格的脚本经 ssh+cmd 引号嵌套会碎——写成 .ps1/.py 文件 scp 过去跑，别拼内联。
- 远程文件要**换文件名 scp**再跑——同名复用会读到陈旧缓存版。
- GBK 乱码：cmd 输出带中文时 `| iconv -f GBK -t UTF-8`；PowerShell 里先把不可打印字符 `-replace` 成 `?`。

## 服务精简（2026-10-19 已做）
关掉 20 个服务（遥测 DiagTrack/WdiSystemHost/InventorySvc/whesvc、OEM 残留 Razer/ASUS/Alienware/Dell、Adobe/Gaming/罗技/三星/Bonjour/ClickToRun/QPCore 等），磁盘读均值 ~230→~70 MB。QPCore、wscsvc、GamingServices 关不死（依赖链自动复活），已接受。回滚清单 `D:\LLM\services_backup.txt`。

## 数字基线（性能模式 Maximum Performance 下）
- 500 token 请求：decode 端到端 64.3 tok/s（含 MTP，接受率 78.4%）；37K prompt：prefill ~2150 tok/s，decode 期 hit_rate 0.48-0.65 波动。
- 节能模式会把速度压到 ~14 tok/s——测速前先 `powercfg /q` 确认 Maximum Performance。
- 思考型模型：max_tokens 要给 reasoning 留预算，否则「reached max tokens while still thinking」只有思考没答案。

## 创作类生成（10-20 实测）
- Ornith 是 agent 向模型（官方定位 self-scaffolding coding），长文色情/文学生成不对口：结构强、血肉模板化，长生成采样退化（动词丢失、逐字复读、意象砸烂——社区多人报 doom loop）。
- 厂商默认采样 0.6/0.95/20 就是本机 config 值——碎句不是参数错。引擎 0.1.45 的 DRY 默认关闭（dry-multiplier 0）、无 min_p。要治退化：`--dry-multiplier 0.5 --dry-penalty-last-n -1` + sampler 重排 `top_k;top_p;min_p;temperature;dry` + `--min-p 0.05`。DRY 治循环复读，不治标点节奏。
- KV 量化与输出质量：Reddit 多人报 Ornith 对 KV 量化极敏感（q4 坏 10-30% 工具调用）；本机 fp16 vs q8_0 实测输出质量未见差异，KV 嫌疑已排除，剩下的是模型本身。现行 config `--kv fp16`（10-19 主人要求改回，备份 .bak-q8）。
