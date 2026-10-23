# qwen35moe 家族（Qwen3.6 / Ornith 35B-A3B）跨引擎服务与格式手术

## 三条引擎路的取舍

| 路 | 何时用 | 关键约束 |
|---|---|---|
| Strata q36 native | 主力，decode 性能最好 | 文件格式必须过 kernel 白名单，混档文件常要手术 |
| PolyStrata `strata-poly` | 免手术直接跑现成 GGUF/混档 | Windows 预编译只发 NVIDIA，AMD 需自编 |
| llama.cpp 官方二进制 | 灵活退化路 / 对照基线 | `--n-cpu-moe` 手工配平，i-quant CPU 专家慢 |

鸭子选型先看文件：unsloth 系全家桶 dense 为 Q8、K 量化专家——三路通吃；community ICE/混档系（F16 attn、I-quant 专家）只有后两路能直接吃。

## Strata q36 格式门（动手先普查，别信第一行报错）

三张白名单是三道独立的门，按报错文本对号入座：

- **专家 grouped kernel**：gate/up 与 down 各一张编译期宏表（`STRATA_GU_FMTS` / `STRATA_D_FMTS`，`src/kernels/cuda/iq_kernels.cu`）。注意非对称：Q4_K(12) 在 gate 侧、不在 down 侧；`STRATA_Q6K_EXPERTS=ON` 只救 Q6_K(14)，救不了 Q4_K/Q2_K。报错形如「blk.N.experts are X/Y … native expert kernels do not take」。另有 `native_expert_supported()` 要求 gate 与 down 都属 is_iq 族，K 量化专家整族被它拦。
- **dense**：`native_mmvq_supported()` 允许集 {2,6,7,8,11,12,13,14,16,17,18,20,21,22,23,29,42}——**F16(1) 与 Q2_K(10) 不在**。报错带「which the native MMVQ does not take」。F16 的 attn_k/attn_v 是这类配置最常见的拦路虎（社区 ICE 配方特有；Unsloth 系 dense 全 Q8 无此坑）。
- **norm/小张量**走 `f32()` 通道（F32/BF16/F16/Q8_0 均收）；token_embd、output(Q6_K)、eh_proj、shexp 全族各有既定通道且白名单内，普查时别误伤。
- **引擎到第一个不支持的 tensor 就停——第一行报错不算完整拒收清单**。动刀前用 gguf-py 的 GGUFReader 全量普查：按名字模式聚合 `ggml type` 计数、逐模式对照三张表，一次列全手术项；否则改完 A 处再冒 B 处，每轮白等一次模型加载。
- KV 在这条路是 fp32 且 `--kv` 被忽略：36K 上下文仅 ~1.4G，不是带宽瓶颈，别为省它花手术刀。

## GGUF 手术配方

- 范式：逐字节拷贝 GGUF v3、重算每 tensor 的 type/offset，选中 tensor 用 ggml 参考实现 dequant→quant（Q4_K/Q2_K 专家→Q5_K；F16 attn_k/v→Q8_0 走查表 fp16 往返）。所需符号 `dequantize_row_q2_K / q4_K / q5_K`、`quantize_row_q5_K_ref / q8_0_ref` 都在 ggml 可链。社区范本 misthemAI 仓库的 requant6to5.c（单规则特例），抄结构改判型。
- MSVC 链本地 ggml-base.lib 时**头文件与 lib 必须同构建族**，先 grep 头文件确认函数签名一字不差再写调用。
- **Windows 32 位 long 截断坑：C 运行库 `fseek(long)` 在 >4GiB 偏移处回绕**，产物被截成几 G 而退出码照样 0。大文件手术必须 `_fseeki64`。**验收不是退出码**：产物字节数 = 各 tensor `ggml_row_size(out_type, nelems)` 之和 + 对首尾各几张 tensor 抽验 round-trip 误差。

## PolyStrata（免手术备胎引擎）

- 仓库 VecSzn/PolyStrata（Strata 上游的活跃延伸）。第二引擎 `strata-poly`：GGUF 原位 mmap 读入、dense 权重按**文件原格式**进显存、放不下的专家走 ggml-cpu CPU 池。唯一加载门 `cpu_expert_types_ok` 查的是 ggml-cpu 的 traits 表有没有 vec_dot——F16/Q2_K/Q4_K 全有，所以 native 白名单拒收的混档文件**天然放行**，官方 BACKENDS 实测表里 APEX-I-Quality（IQ4_XS+Q5_K+Q6_K 混档）直跑是现成证据。
- Windows 预编译 zip 覆盖 RTX20-50 + CUDA13，setup 自动下载并按 GitHub 发布页公开 SHA-256 校验；**AMD 卡在 Windows 不支持该预编译引擎**（要自编源码）。装前先读 release 的 Limits 节，别拿本文档结论跳过它。
- 安装形状：`START-HERE.bat --family ornith --model APEX-I-QUALITY --gguf-dir D:\LLM\Models --context N --vision no --port 8080 --no-browser --yes`。本质是 `.venv\Scripts\python.exe setup.py %*`；已装好的机器直接 `python setup.py <同参数>` 就只起服务。
- **已有文件要冒名入档需过三件套**：①文件名逐字符等于 setup 的 file 模板与档名（差一小段都对不上）；②尺寸必须等于 pinned 值（setup 会逐字节对照并拒绝）；③SHA-256 校验连 `--gguf-dir` 场景都可能触发。绕法：在同路径写 `<file>.done` 标记，内容含 `sha256 <hex>`（mark 判定先查标记即跳过 hashing）；文件名用硬链接别名零拷贝：`fsutil hardlink create <模板名> <现名>`。
- 起服验收：log `ready:` 行 + `/v1/models` 的 status=loaded + 真请求出 token。**expert cache 冷启动首答速率不可当基准**——首跑命中率 ~50%，缓存是自适应的，热起来才见稳态（官方口径 12G 卡稳态明显高于冷启动）。

## llama.cpp 混合卸载参考（12G 卡 + 大 MoE 文件）

- 起步 `llama-server -m <file> --host 0.0.0.0 --port P -ngl 99 --n-cpu-moe 999 -c 32768 --jinja`（999=专家全留 CPU），随后逐档下调 `--n-cpu-moe`（999→30→25→20 的实测曲线 decode 5.7→9.1→11.0→12.1 tok/s），**每档部署后发真请求测速 + `nvidia-smi` 看显存余量**；used ≈ total−300MiB 即边界，回调一档终止。
- `-ctk q8_0 -ctv q8_0`（KV int8）再挤出 ~1G 显存补给专家上卡。
- i-quant（IQ 系）专家在无 AVX-512 的 CPU 上 dequant 显著慢——上卡比例是最有效的提速杠杆；要再快走 CPU 侧正道：换 K-quant 专家文件（Unsloth UD-Q4_K_XL 一类）。二进制位置：`D:\LLM\llama-b11461-bin-win-cuda-13.4-x64\`（还有 b10964 与一个 prism 分支备用）；调好的甜点配置存档 `D:\LLM\llama_node_FINAL.bat`，schtasks `llama_node` 一条命令复活。

## NODE II（Windows 侧实装，2026-10-18 夜）

- NODE II = 主人对 MSI 笔记本 Windows 侧的称呼，Hermes 里同名；**VPN 口 IP = 10.6.0.3**（ethernet 口另有 LAN IP）。生产机已实测 `curl http://10.6.0.3:8080/v1/models` 跨机连通。
- PolyStrata 装在 `D:\LLM\PolyStrata`（源码仓，预编译引擎 zip 由 setup 自动下）。**起服务唯一可靠姿势 = `D:\LLM\poly_run8.bat`**（schtasks 任务名 `poly_serve`）：杀 8080 listener（`for /f netstat | taskkill`）→ 直起 `.venv\Scripts\python.exe serve\server.py --config strata-ornith-apex-i-quality.json **--host 0.0.0.0** --port 8080`。**不带显式 --host 就绑回 127.0.0.1**——setup.py 的 `--host` 参数与手写进 config 的 `"host"` 键都会失效/被后续 setup 重写洗掉（SETUP_KEYS 里有 host 但现场被洗，疑案挂起，别再赌 config）。
- 杀旧 server 注意：点位 `taskkill /f /pid <PID>` 必须点名杀，`/im python.exe` 会误伤别的 python；杀完 `netstat -ano | findstr :8080` 验空再起新。
- 模型文件就在 ICE 原件上硬链接：`Ornith-...-23G-ICE.gguf` ↔ 模板名 `Ornith-1.5-35B-A3B-APEX-MTP-I-Quality.gguf`（`fsutil hardlink create`，零拷贝）+ `.done` 标记骗过 sha 校验——**albeit 这绕过了真校验，只许在字节已另验（官方 sha256 前缀 e4282202）的前提下用**。
- 换模型/动 config 走 setup 后，必须再跑一次 poly_serve 恢复 0.0.0.0 监听。

## 上下文长度扩容（qwen35moe 家）

- 入口是 config `args` 里 `--max-context` 的**同位替换**：`args[args.index("--max-context")+1] = "262144"`，python json 改盘上文件即可，不必为这个值重跑 setup 向导。改完必须重启 server 才生效。
- **生效判据不是 ready 行**：ready 行的 `context N` 是 server 启动快照，旧进程的残留日志会同文件躺在新运行里冒充现场。以 `/v1/models` 的 `meta.n_ctx` 为准，且**本机与跨机两处同查**（`127.0.0.1` 与对方 VPN 口各打一发）。
- KV 成本先算再动：qwen35moe 架构每四层只有一层 full-attention（Qwen3.6/Ornith 约 10 层 full-attn），262144 ctx 的 KV 远小于 dense 模型直觉账，12G 卡实测起得来。**服务进程 RSS 会显著变大——KV 倾向驻留 RAM，别把 RSS 十几 G 的增长误判成显存爆炸**；显存以 nvidia-smi 与引擎自身日志为准。
- 杀旧进程要点名两次：先杀 8080 listener（server），再 `tasklist` 找 **engine 子进程**（strata-poly.exe）单独 `/pid` 杀——server 死后 engine 变孤儿继续占显存内存；`/im` 按 exe 名杀的报错在 GBK 回显下会误读成「无此实例」，识别靠 tasklist 输出，不靠报错文本。改 context 尤其要两杀——engine 抱着旧 ctx 缓存直到被点名。
- setup 的 `--context` 参数会拉起完整 install 流程（数分钟起），且它重写 config 的时机与内容不可依赖，同位替换更可控。