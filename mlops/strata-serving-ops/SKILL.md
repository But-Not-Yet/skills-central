---
name: strata-serving-ops
category: mlops
description: 改动或诊断 Strata 生产服务（启动参数、thinking 行为、对话缓存/段缓存、chat 模板）时加载。把旧 llama.cpp 启动脚本的行为对照迁移到 Strata 也走这里。llama.cpp 基准类任务归 llama-serving-bench，规则别混用。
version: 1.0.0
author: Nekonya
license: MIT
metadata:
  hermes:
    tags: [strata, serving, rocm, production, thinking]
    related_skills: [llama-serving-bench, llama-cpp]
---

# Strata 生产服务运维（自研引擎，与 llama.cpp 分家）

## When to Use
改动/诊断 Strata 生产服务（部署形态、启动参数、thinking 行为、对话缓存/段缓存、chat 模板）时。或把旧 llama.cpp 启动脚本（Start_Qw3.8FlashNxt_*.sh*）的行为对照迁移到 Strata 时。llama.cpp 基准类任务走 llama-serving-bench，不要混用其规则。

## 部署形态（先核链路再动手）
**单元名映射（先看这里，别按旧名找链）**：`strata-server.service` = Strata 生产链（**enabled 开机自启**，主人裁定 2026-10-12 调换）。`llama-server.service` 现在跑的是 **OrcaRouter llama.cpp**（`Start_Qw3.8Orca27B_*.sh` 启动脚本，**disabled，按需手动起**）。两者都占 8080，手动起 llama 前先停 strata。核身份一律 `systemctl cat` 看两个单元的内容，不按名字猜。开禁状态以 `systemctl is-enabled` 现查为准。
- **headless（`systemctl isolate multi-user.target`）会连带切服务**：isolate 是全量对账：停掉 target 闭包外所有在跑的单元。拉起闭包内所有 enabled 但未跑的单元。用 `systemctl start` 手动起的 disabled 单元活不过下一次 isolate。所以「谁在 8080」由此二者的 enabled 状态决定，与谁按了 headless 无关。查「谁切了服务」先 `journalctl` 找 `sudo ... COMMAND=/usr/bin/systemctl isolate` 行（auth 日志有 sudo 命令原文，是阳性证据，比空输出反证硬）。
Strata 链本身：`strata-server.service` → `Strata/setup.sh`（venv 引导）→ `exec python setup.py` → `serve/server.py`（HTTP 层，8080）→ `build-hip/strata --serve …`（引擎本体，AMD/HIP 构建）。
- **启动参数表 = `Strata/strata-iq3_s.json`**：顶层即 serve 配置（`exe` + `args` 是引擎命令行。serve 层参数如思考预算也在顶层）。**serve 层选项（`host`、`port`、`reasoning_budget_tokens`…）只能放顶层键，塞进 `args` 数组引擎不认、打 usage 退出，表象是 `engine exited before it was ready`**。server.py 从顶层键取 serve 参数（如 `cfg.get("host")`），args 数组原封透传给引擎二进制。
- 生产二进制看配置 json 的 `exe`：本部署现指 `<ROOT>/engine/strata`（官方 layout 产物）；`build-hip/strata` 是构建树产物，不等于线上。验证新构建含某特性：对 `exe` 指向的那个文件跑 `--version` 和 `strings`，再与 `/proc/<pid>/exe` 的 sha 对平。
- **变更配方**：先备份 `.bak-<变更名>`，再 patch 最小 diff，然后用 python json 回读核验。**重启由主人来跑**：agent 不自行重启生产，准备好后招呼主人（他说过重启类动作可以「直接叫我」）。未重启前，运行进程的参数以 `/proc/<pid>/cmdline` 为准（配置改了进程不知道）。
- **服务停生死两态盲区（2026-10-18 实测）**：agent 若直接 SIGTERM 服务进程，systemd 认其为干净退出（exit 0）——`Restart=on-failure` **不拉起**，单元停在 inactive；polkit 又拒用户 `systemctl restart`（Interactive authentication required）。此时绝不要用 setup.sh 手动拉替身进程（脱离监管且与后续 systemd 抢端口），正确动作只有一条：请主人 `sudo systemctl restart strata-server`。杀引擎换装 exe 前先想清楚这一步的代价（8080 停机到主人下次重启为止）。
- **换装引擎二进制（服务在跑时）**：直接 cp 覆盖会被服务进程抱死（`OSError: Text file busy`）。配方：`mv engine/strata <旧名>` → `cp <新构建> engine/strata` → **同步更新 `engine/BUILD.json` 的 `version` 与 `src`**（src 用 source_hash 算法对新树复算，见指纹节；json 与盘上 exe 不一致，setup 下次启动就触发重编）→ `engine/strata --version` 冒烟，再请主人重启。回退双保险：就地旧 exe 副本一步 `mv` 即回，或 `setup.py --rollback-engine` 一键互换。
- **setup.py 自动化必带 `--yes`**：交互向导遇 stdin 关闭会以「input ended before a setup answer was received」退 1（首跑还会问选哪个模型）；这个退 1 未动任何盘上状态，加 `--yes` 重跑即可，别当编译失败排查。
- **对外可达（host 越出回环）**：config 顶层加 `"host": "0.0.0.0"`（server.py `a.host = a.host or cfg.get("host") or "127.0.0.1"`，缺省锁 127.0.0.1，VPN 对面必然 unreachable）。监听越出本机时 **IP 直连自动放行**（LAN 地址自动进 answers 名单），**主机名/域名访问会被 DNS rebinding 防护拒**——要能连需加 `"allowed_hosts"` 或 api_key；0.0.0.0 且无 api_key = 局域网内人人可用。生效要重启。
- 日志：`Strata/strata-iq3_s.log`（引擎）+ `/var/log/llama-server/*.log`。**判断警告归属时先按行号定位它在哪个 `engine started` 之前/之后**。历史进程的警告和当前进程混居同一文件。
- 引擎是 setup.py 的子进程：`systemctl show` 的启动时间和引擎实际启动时间可以不同（先起编排器、后拉引擎）。核引擎年龄用 `ps -o lstart -p <pid>`。

## thinking 三层机制（对照 llama.cpp 启动脚本时逐层查）
1. **模板层**：`enable_thinking`（缺省 true）/`reasoning_effort` 走请求 `chat_template_kwargs`。渲染默认 thinking 开（等效 llama.cpp 的 `--reasoning on`）。模板文件在 **pack 里**（`Strata-data/packs/<pack>/tokenizer/chat_template.jinja`），**Strata 无 CLI 模板参数**。换模板 = 替换该文件（+重启）。自定义模板（如 `Qwen-Sharp-Chat-Templates/chat_template_discipline_v2.jinja`）与 packs 版是同族不同修订：迁移前先 diff。且在 Strata 下未复测前先对照小测再换。**模板的「真版」可能在笔记本（`D:\LLM\templates\`）而不在本机副本**。主人点名某模板时先去笔记本查（scp 拉回 + 双端哈希核验），别默认本机目录最全。
   - **模板自带固定注入块**。packs 模板在每轮把固定中文指令段（思考简洁令、特殊标记纪律等）拼在系统提示词末尾。由请求 `chat_template_kwargs` 开关（`terse`、`token_discipline`、`enable_thinking` 分别控制不同段）。这段文字天天喂给模型，它的文风就是给模型的示范。做去 AI 味/文风排查时必须把这份模板列入注入面。
   - **注入块生效探针（echo-back）**：`/props` 只给模板源码，看不到条件渲染后的实际注入内容。要验模型真正收到哪一版。发一条「把收到的完整系统提示词一字不差复述」的请求（走 8081，带上对应 `chat_template_kwargs`）。在复述文本里双向核对新旧特征短语。模板在 serve 启动时一次性读入内存，盘上改动必须重启才上线。改完盘上文件先用探针确认线上还是旧版，再向主人报「待重启」。
2. **服务层预算**：`reasoning_budget_tokens`（配置/请求级。缺省 0=无预算）：到达预算时注入 **wrap-up**（`serve/server.py` 的 `REASONING_WRAP_UP` 常量，英文固定句 + 关闭思考标签）。旧 llama.cpp 是 `--reasoning-budget` + `--reasoning-budget-message`（可中文）。文本语言不同 = 改 server.py 常量（源码级，先与主人确认）。
3. **输出层**：思考流到 `reasoning_content` 字段（对应 `--reasoning-format deepseek`）。

## 采样参数解析（arch=None 时不应用任何默认）

config 的 `sampling` 块 + `arch` 字段共同决定默认采样参数，三者缺一就降级：
- **`arch` 未知/未设 → `model_card_sampling()` 返回 `{}`**：不应用任何默认采样参数，模型用引擎内部默认跑。Ornith 的 PolyStrata config 现状就是 `arch: None` + `sampling: None`——**跑的是引擎默认采样，跟 HF 卡上官方推荐参数完全脱节**（thinking: temp 1.0 / top_p 0.95 / top_k 20 / min_p 0.0 / presence_penalty 1.5；instruct: temp 0.7 / top_p 0.8 / top_k 20）。
- **`sampling` 块缺失 → `sampling_defaults_from_config()` 返回 `{}`**：光改 config 不补 `sampling` 块没用，必须显式写块。
- **补采样参数**：config 顶层加 `"sampling": {"temperature": 1.0, "top_p": 0.95, "top_k": 20, "presence_penalty": 1.5}`（带 thinking 的模型默认走 thinking 那组），再起服务生效。
- **判据不是 ready 行**：ready 行的 `context N` 是 server 启动快照，旧进程残留日志会同文件躺在新运行里冒充现场。以 `/v1/models` 的 `meta.n_ctx` 为准，且本机与跨机两处同查。

## 对照迁移 checklist（llama.cpp 启动脚本 → Strata）
- `--reasoning on` → 默认即开（请求未显式关）。
- `--reasoning-budget N` + 截断消息 → `reasoning_budget_tokens` + wrap-up 常量（文本语言单独决策）。
- `--chat-template-file X` → packs 内模板文件（无 CLI 覆盖）。
- 段化/对话缓存等 → `args` 数组（以 `strata --help` + 该二进制 `strings` 为准。如 `--conversation-segment-cache` / `--conversation-segment-dir` / `--conversation-segment-budget-mib`）。
- 采样参数在请求侧/服务层，配置位置先 grep `serve/server.py` 与 json，不猜。
- `--n-gpu-layers/-ngl`、`--ctx-size` → **不存在**。引擎是权重全常驻显存流派，长上下文/卸载的旋钮是 `--kv-resident N`（QSA 层只留 N cells 常驻显存、整条 K/V 进锁页内存，省出的显存喂专家槽；上下文 ≤N cells 不走流式）+ `--kv-grow`（K/V 按请求实际到达的格数才占显存）。PLE n-gram 表原生 SSD 流式（`--ple-io direct` 默认 unbuffered 直读；`--ple-row-cache`/`--ple-inflight` 调缓存与并发）。别拿 llama.cpp 的「留几层上 GPU」思路往 Strata 配置里写。
- `--cache-type-k/--cache-type-v` → `--kv int8|q8_0|q4_0|k8v4` 一族。
- `--jinja` → n/a（server 层持有 chat 模板，引擎无模板参数）。`--temp` 简写也拒收，只认 `--temperature`——**引擎拒收一切未知 flag 并打 usage 退出**，llama.cpp 腔拼写会让整条启动链当场死。
- `-hf`/`-f`/`-a`（模型与词表定位）→ `--native <gguf，指向 shard-00001>` + `--pack <tokenizer pack 目录>`（`tools/strata_tokenizer.py --gguf <shard1> --out <dir>` 一次性生成；server  tokenize，引擎吃 token id）。PLE 表在 ≥4 shard 时引擎自己定位（config 里删 `--ple-gguf` 行），单文件/少 shard 必须显式 `--ple-gguf <第二块 shard>`。
- MTP/投机解码（qwen4exp 主路）→ `--spec N`（verify 窗口）、`--spec-min-p`、`--suffix-draft`（后缀 prompt-lookup 混合）、`--batch-mtp`、`--mtp-max-t`。这条路的 MTP draft 层要从原始 checkpoint 抽：`tools/mtp_fetch.py fetch --out <-dir>` → `mtp_pack.py` → `mtp_rt.py`，再在 args 追加 `"--mtp","<DIR>"`；不配 MTP 目录时 `--spec` 只是纯 verify 模式。**q36（qwen35moe）另路见下节——它的 `--mtp` 吃文件自带 MTP 块，不走这三步。**
- **看板卡/任务规格里写 Strata flag 示例时不许用 llama.cpp 腔**（本卡吃过：模板照抄 llama.cpp 拼写会整批无效）；把「flag 逐个对照 `strata --help` 输出修正后才许进交付脚本」写成卡的硬性验收项——编译 worker 实测确实靠这条闸门自己纠回了全部拼写。

## q36 独立引擎路（GGUF 架构 qwen35moe，0.1.44 起）
引擎按 GGUF 文件的 `general.architecture` 自动切路（`src/qwen35/q36_engine.cu`；`--list-architectures` 打印 qwen4exp qwen35moe）。这条路是「own-path family」，与 qwen4exp 的 pack 世界**规矩完全不同**：
- **单文件 GGUF 直吃**：no pack、no expert profile、no PLE（`--ple-gguf` 不出现）、no compat-bf16 工序。ORCA.md 那套 iq_pack/PLE/MTP 三步流只属 qwen4exp 及其二创，别套给 qwen35moe 系 GGUF。
- 启动配方四件：`--native <gguf>` `--max-context N` `--prefill auto` `--mtp 2`（N=每步 draft 数，用**文件自带 MTP 块** drafting）。tokenizer 唯一要打的包：`tools/strata_tokenizer.py --gguf <file> --out <pack>`（只出 tokenizer，权重零转换）。
- 拒收 Flash-Next 旋钮：`--kv`、`--rope-scaling`、`--low-ram`、`--resident-budget-gib` 在这条路无效/被拒。KV 是 fp32，每 token ~44KB（11 层×2 头×256×2×4）——192K 上下文光 KV ≈8.4G内存，长上下文预算按这个算，别按 qwen4exp 的 int8 `--kv` 想。
- hybrid 卸载：**全部专家在 RAM 留一份拷贝**（塞不进 VRAM 的走 CPU）——setup 门槛：Q8_0 需 52G RAM、UD-Q6_K_XL 44G、UD-Q4_K_XL 32G。内存小的机器先按文件体积+10G 判能不能起。
- 限制：单 GPU、vision 未接线（mmproj 不必下）、Intel Arc 拒收。
- **官方文档滞后于合并代码**：MODELS.md 仍写「Strata runs one model」、`strata_inspect.py` 还留着「knows but does not run yet」旧注释，而 setup.py 的 `OWN_PATH_FAMILIES`/`QWEN36_FILES` 已是正式 family（pinned 哈希、`install_own_path` 生成完整 config+启动脚本）。「Strata 支不支持架构 X」的答案以 **setup.py 的 family 表 + `src/` 里有没有该 arch 的 engine 路径 + `--list-architectures`** 为准，docs/README 只当参考；strata_inspect.py 的 PREVIEW 注释是预览期残留，别引用成现行状态。
- **格式门、手术与免手术备胎**：native kernel 三张白名单的逐 tensor 普查法、GGUF 格式手术工具配方（含 Windows 32 位 fseek 截断坑）、PolyStrata 备胎引擎与 llama.cpp 混合卸载调参——全在 `references/qwen36-family-serving.md`。

## PolyStrata 备胎引擎路（Windows 笔记本，见 `references/polystrata-serving.md`）

PolyStrata 是 Strata 的 Windows 分支 fork（`VecSzn/PolyStrata`），跑在笔记本（NVIDIA 5070 Ti 12G）上，与生产机 Strata 分属不同机器、不同 GPU 架构。它是 Ornith 等模型的备胎/并行节点。

- **Web UI 不是 llama.cpp 的**：PolyStrata 自带 `web/app.js`（64KB，`st-` 前缀 CSS：`st-tab`/`st-composer`/`st-btn`），不是 llama.cpp 的 `chat.html`+`webui.js`+`#chat-output`。打开 PolyStrata 端口看到的是 PolyStrata 自己的界面，别误以为 llama.cpp 还在跑。用户浏览器若打开旧标签页（llama.cpp 昨晚在 8082 跑过）会看到 llama 界面——**先查端口-进程-HTML 三证，再下「谁在跑」的结论。**
- **host 绑定用命令行显式 `--host`，别信 setup.py 写 config**：PolyStrata 的 `setup.py` 每次跑都 `write_config` 整体重写模型 config，`--host` 字段（在 SETUP_KEYS 里）仍会丢失，server 仍绑 `127.0.0.1`。可靠做法是绕过 setup.py，直接 `python serve/server.py --engine strata --config <cfg> --host 0.0.0.0 --port 8080`。launcher .bat 先按 `netstat -ano | findstr :8080 | findstr LISTENING` 第五 token 的 PID 杀旧进程（`taskkill /f /pid <pid>`，别只靠 `/im strata-poly.exe`——真监听者是 python 进程不是 strata-poly.exe 父壳，`/im` 有时杀不动），再起 server.py。起完以 netstat 监听地址为准，别信 `ready:` 自报的 `127.0.0.1`。
- **--max-context**：config args 里写 `--max-context N`。Ornith 是 MoE（每四层一层 full-attention），KV 成本比 dense 低；引擎 RSS 走 RAM 不走 VRAM。poly 的 KV 走自适应流式（auto）。改 context 后以 `/v1/models` 返回的 `n_ctx` 为准，跨机 `curl http://<VPN-IP>:8080/v1/models` 复验。
- 起服与验证顺序（杀旧→起新→验本机→验外线→验 UI）见 `references/polystrata-serving.md`；模型实底（别名/量化/APEX 档/微调辨识）见同文件 §5。

## 验证配方（变更后）
- 「新参数生效」判定：比对 `/proc/<pid>/cmdline` 与配置 args（回读核验）。日志的 `engine started` 行是金标准快照。**serve 层参数看启动的 Settings 块**（逐项列出，如 `reasoning_budget_tokens 6144`）。
- **模板生效**：`curl /props` 的 `chat_template` 字段就是模板源码：**用 sha256 核对身份，别用版本标记**。同族姊妹修订常常共享同一个 `template_version` 字符串，拿标记核对分不出换没换上。双重判据：目标文件 sha256 对上（哈希前先 `encode('utf-8')`）+ 双向核对修订特有短语（新短语在、旧短语不在）。换装前后各采一次。
- **换模板/重启前先查该文件的验收状态**：盘上文件可能比「已验收版」新。中间可能留着未验收的实验修订（看板卡 blocked、交接记录明写「先验收实物再讨论重启」）。**重启会把指向路径的当前盘上内容带上线**（启动时读文件），未验收修订不得被动上线。顺序：sha 核对 → 验收状态核对 → 再换/重启。给服务引用模板优先指向独立副本（评审目录之外），别直指实验现场（pack 本体被动跟随）。
- **budget 的「已生效」与「已触发」是两层**：配置读到（Settings 打印）≠ 路径走通。wrap-up 只在思考量到达预算时出现（日志 `thinking budget reached (N tokens): wrapping up the thinking` + 注入文本）。近期思考量远低于预算时零触发是正常，别当配置失效。
- 段缓存。无「stays off」警告 + 段目录（`--conversation-segment-dir`）出现段文件（**引擎启动后的恢复/预填充阶段就会批量切段**，不止「首次 park」）。`spill/` 下 `spill-*.bin` 是整文件回退层。
- **段路径性能特征（实测）**：restore 墙钟随深度增长（≈34K→0.4s、≈97K→1s、≈165K→1.9s）。**收益随 token 数递减**（大 prompt 仅比整文件快 ~4–30%），瓶颈在 K/V 拷贝 + 逐 token 复核而非文件读取。别把「百毫秒级」期待套到 100K+ 的 prompt 上，要提速从拷贝/复核下手。
- 参数名先在 `--help`/`strings` 里确认，再写进 json。写错名引擎会起不来或静默忽略。
- 重启后的验证五连：Settings 块（参数）/ `/props`（模板）/ `/health`（服务）/ 段目录（段化）/ 日志 thinking 行（思考计数）。
- **切换前先抓基线再换**（主人指令化流程）：切版本前，把下列东西归档进同一目录。一，三份日志备份。二，身份（`/proc/<pid>/exe` sha、cmdline 关键参数、lstart）。三，盘态（段/spill 计数与 manifest）。四，**按进程 Era 的性能分位数**，算法是从最后一个 `engine started` 锚起。正则抽 `prompt N = M reused …` 行，算复用率/prefill/decode 的 p25/中位/p75，标明 n。再加切换后对照判据清单，全写进一个日期命名的记录文件。所有数字必须可从备份日志复算。写错的数当场改（基线文件先自过有一说一）。切换后拿同一把尺子对，落差 >20% 要归因。
- **部署后的核实清单（实操版，五步）**：① `journalctl -u strata-server --since <时刻> | grep -E 'Stopping|Started'`。② `pgrep -f 'build-hip/strata --serve'`，再 `sha256sum /proc/<pid>/exe`。哈希要**对上当前磁盘 `build-hip/strata`**。③ `/proc/<pid>/cmdline` 抽查关键参数。④ 引擎日志出现**新代码独有的行为行**（patch 生效的最硬证据）。⑤ `ready:` 行 + `ss -tlnp :8080`。别拿历史构建的 hash 对比，同一树两次构建的链接非确定，hash 会不同。汇报「服务状态」前先 `systemctl show strata-server -p ActiveEnterTimestamp -p MainPID`。主人可能已自行重启应用配置（实际发生过：agent 还在准备部署，主人已重启），别按旧快照说话。
- **serve 启动会编译新源码，但别把「编译成功」当「新引擎在跑」**（2026-10-16 实例）：编译与拉引擎是并行的。01:34:58 restart，约 1 分钟内 `engine/strata` 产出，01:35:31 跑的却是旧二进制。**官方 layout 产物路径 = `<ROOT>/engine/strata`**，以 serve.log `[ok] engine compiled:` 行与 `engine/BUILD.json`（version/archs/src 哈希）为准。本部署 json 的 `exe` 若仍指 `build/strata`（独立旧拷贝），重启后加载的还是旧版：checkout 换了源码并不会自动换加载路径。判据三连缺一不可：`/proc/<pid>/exe` sha 对上 `engine/strata`、该二进制 `--version` 报新版、json `exe` 与编译行同文件。修法：备份 json，`exe` 改指 `engine/strata`（此后每次重启自动跟随新构建），再重启。**vision 程序不在 engine/ 里时 BUILD.json 记 `"vision": "none"`，json 顶层 vision 段的 exe 可仍指 `build/strata-vision`。换引擎后必须用真图问答复测编码器与新引擎的协议兼容性。**

### 新 worktree 里编译引擎（换目录验证源码时）
仓库的 `third_party/llama.cpp` 不在 git 跟踪面（`git ls-files` 输出 0 行，主仓里的副本是 setup.py 按 zip 解包的）。新 worktree 直接 configure 会死在 `ggml is not an existing directory`。配方：照 setup.py 的 `LLAMA_CPP_COMMIT` 下载 `https://github.com/ggml-org/llama.cpp/archive/<commit>.zip` 解到 `third_party/llama.cpp`，再 configure。HIP 侧必带生产缓存同款参数（从旧 `build-hip/CMakeCache.txt` 抠：Release、`STRATA_ENABLE_HIP=ON`、arch、`-DCMAKE_PREFIX_PATH=/opt/rocm`。漏 PREFIX_PATH 会死在 `find_package(hip)`）。改源码前用 `git diff <前tip>..<新tip> -- setup.py | grep LLAMA_CPP_COMMIT` 确认 pin 没变，免触发 175M 重下载。

### BUILD.json `src` 指纹的引用纪律
BUILD.json 的 `src` 字段单值吻合只能证明「这份 BUILD.json 配这份二进制」，**不得引用成「二进制=某源码树」**。那是把单字段吻合拔高成整树一致。要断言对上某树就现场复算：照 setup.py 的 `source_hash` 算法，对该树跑一遍，与 BUILD.json 值相等才算。算法细节：SHA256(LLAMA_CPP_COMMIT) 依次吸收 `ENGINE_SOURCES` 面（CMakeLists.txt/cmake/src/include/third_party/ggml 每文件路径+字节，CRLF 归一，取前 16 hex）。复算时把 `git rev-parse HEAD` 同场打印，断言才带完整指针。复算要落成常驻可重跑的脚本存档（本机现成：`~/Documents/Hermes/切换基线_20261016/verify_src_fingerprint.py`，跑一遍直接印 复算=… BUILD.json=… 一致/不一致），核验工件不能只活在会话终端回显里——审计要的是开得到、可重跑的证据。另记：serve/server.py 不在引擎指纹面。serve 层改动（wrap-up、budget）要用模板 sha + Settings 块另行证明，不搭 src 指纹的车。文档/README 提交不进指纹面，可顺手 `git diff <旧tip>..<新tip> -- <源码面>`，空输出即可确认旧指纹继续成立。

## 对话缓存：跨重启存活（patch c84e271 起）与诊断速查
- **跨重启存活 patch**（2026-10-07 提交 `c84e271`，部署后生效）：每个 tier 在 park 时把 manifest 写入文件（`parked-manifest-v1.bin` / `segment-manifest-v1.bin`。带版本号与 FNV 指纹，用 tmp+rename 原子写）。启动时 adopt 这些清单（按现存文件过滤幽灵、id 续接）。重启语义从「全清」改为「保留清单+清孤儿」。**首次部署的第一次重启仍有一次过渡清空**（旧文件无 manifest 认领）。回退：`--no-conversation-cache-persist` 或删 manifest 文件。核对：`/proc/<pid>/exe` 哈希对上**当前磁盘**构建物 + manifest 文件诞生。
- **启动日志读法（kept/removed）**：`spill directory …; kept N parked file(s) from a previous run, removed M orphan(s)`（段 tier 同构）。N=认领存活、M=清孤儿。**首次部署的第一次重启 N=0**（过渡清空），**此后正常重启 N≥1** 才是「跨重启存活」的实证。N 恒 0 先查「有没有 park 过」（manifest 写没写出来）。
- **恢复金字塔（诊断基线）**。checkpoint 0.24–0.38s（RAM 常驻，主力）＞ live（transient K/V）0.36s ＞ segment 0.7–1.8s ＞ file 0.95–2.1s ＞＞**全量重读 100–196s＝异常态**。遇慢恢复先问「副本为什么没有」。
- **准入门（save 与 read 都过筛）**：放行 ⇔ `MemAvailable ≥ need(1.5–3.5G，随会话大小) + floor(min-free，现 512)`。**不认 swap**、遥测缺失也拒。存档捕获被拒＝`skip parking`＝该轮无副本→下轮全量重读。RAM 水位是上游变量。
- **参数语义坑**：`--conversation-cache-mib` 现仅=「restore↔park 间 transient K/V 上限」（deprecated）。**`--conversation-cache-slots` 被引擎忽略**。停放容量实际由磁盘侧（段预算 `--conversation-segment-budget-mib`）决定。
- **日志配对法**：serve `reading X of Y`=进度（无 of 行=请求级累计心跳）。strata `prompt N tokens = M reused + X read in T ms`=同一请求另一面（Y=N、T≈耗时、完成时 X≈Y−5）。两侧按数字+时间指纹配对（无时间戳）。**serve 首行 X=复用+8192**：第一个 8K chunk 走完才打印。复用 16,384 时，首行显示 24,576。别拿首行当复用深度（以引擎 `restored/reused` 行的 M 为准）。
- **诊断全景文档**。`~/Documents/Hermes/重读诊断_20261007/`（01 配对与裁决 / 02 跨重启设计+实现 / 03 重建曲线+脚本 / 04 切换重读根因 / 05 长段切片设计）。
- **复用塌缩诊断（切换后大重读/部分重读）**：先读 `references/segment-cache-debugging.md`，里面有 manifest 解析配方。深段在否→逐出排除→内容分叉 vs 整段过滤的判定树、自愈时限、报告口径。

## vision 图像链路（CPU 编码器 + Q8_0，2026-10-12 上线）
- **开关是 `--vision`（引擎 args）+ 顶层 `"vision"` 段**，不叫 mmproj。mmproj 文件喂给独立的 `strata-vision` 编码进程（llama.cpp mtmd）。serve 层检测到 vision 段而 args 缺 `--vision` 会自动补（CPU 模式不补 vram-reserve。gpu 模式补 700）。
- **上线配方**：① 编编码器：`cmake -S tools/vision -B build-vision -DLLAMA_DIR=third_party/llama.cpp -DSTRATA_VISION_CUDA=OFF -DSTRATA_PORTABLE=OFF` + `cmake --build build-vision --target strata-vision`，产物拷到 `build/strata-vision`。② mmproj 量化 Q8_0：`llama-quantize <BF16 mmproj> <out> Q8_0`（866→589 MiB，CPU 编码省约 280 MiB 内存、300 token 下更快，文档推荐 CPU 模式用 Q8_0。精度余弦 0.997+ 为文档值未独立复现）。③ 配置加顶层 `"vision": {exe, mmproj, model(=args 里 native shard1), gpu:false, max_tokens:300, threads:CPU核数/2}`，args 加 `--vision --vram-reserve-mib 700`。④ 重启（重启由主人来跑）。
- **开销账**：GPU 编码器约 1.4 GB 显存（生产卡 23.6/24 GB 满水位时塞不下）。CPU 编码器不占显存、编码时进程常驻约 0.6 GB 级内存，用完即退。
- **生效验证四连**：`/proc/<pid>/cmdline` 含 `--vision`。`pgrep -a strata-vision` 有进程。`/v1/models` 的 `input_modalities` 含 `image`。真图 base64 走 `/v1/chat/completions` 问答成功（行为级证据最硬）。冒烟可独立跑 `build/strata-vision --mmproj <f> --model <shard1>`，首行 `READY <维度>` 即通，不碰在跑引擎。
- **mmproj 文件名带 Uncensored 不代表血统冲突**：视觉塔在消融/二创变体间通用，mtmd 只认 Qwen-VL 格式。同族性最终以真图问答行为裁决。

## 跟主线（上游合并/fork 跟进评估）
上游极活跃（几天就是数百到上千提，引擎包几天一版），「要不要跟主线」评估按固定四步跑，全程只读不动工作树：
1. **账目**：`git fetch origin main --tags` → `git rev-list --count HEAD..origin/main` 得落后的提交数，`git rev-list --count origin/main..HEAD` 得咱比上游多出的提交数。**fetch 要先证实有效再数账**：quiet fetch 可能没动本地 ref，数出 0 新提交而远端实际几百笔外——先 `git ls-remote origin refs/heads/main` 拿权威现值与本地 `git rev-parse origin/main` 对平；fetch 完再对一次，并顺手看 `git tag --sort=creatordate | tail`，本地 tag 列表同样可能是旧的。落后量会随 fetch 明显变化，别拿旧引用算出的便宜结论当数。本地自研分支（当前是 `f-<engine>-prod`，历史上有 `f-cache-persist-manifest`）多出的那些提交，正是评估对象本身。**动手合并前先清点全部 remote 并查证是否已做过**：`git remote -v` 逐个列（自有 fork 也是一行），主人说「已经 merge 追新」或状态看似已存在时，先在 fork 上找那个 commit（`git ls-remote fork` 拿分支头 + `git merge-base --is-ancestor <目标> <候选>` 验包含关系）；origin 没有只说明上游没有，不说明这活没人做过——对着 origin 重演已完成的合并，只会撞出无谓冲突再白拆一遍。
2. **方向红线：只能「主线并入咱分支」，不许 `reset --hard` 追官方**。先 grep 上游 log（persist/manifest/restart 等功能词），确认咱的自研功能上游有没有对应实现（跨重启 manifest 至今没有）。reset 会把自研功能直接蒸发。同理，将来给上游提 PR：独立、成文件、上游没有的功能是硬候选。改动咱缓存状态机整体的那些（park-on-displacement、supersede 类），与上游自家缓存改动语义纠缠。先开 issue 探 maintainer 意向再提 PR，raw PR 会挂灰。
   - **同名「parking」不是同一个东西**：上游 `--conversation-cache-mib/slots` 是 host-RAM 缓存（docs 明写 bounded host-RAM），咱 fork 是磁盘为准 + 跨重启 manifest + 前缀段。判上游有没有覆盖咱的功能，用四个模式 grep 上游树：`conversation-cache-dir`、`conversation-segment`、`parked-manifest`、`kept .* parked file`；再确认咱改过的缓存文件在上游基线上有没有提交。上游的 SESSION SAVE/RESTORE 是手动存盘，不是自动停放；DeepSeek 路的 SLOT_KEEP 只在独立引擎包、RAM 槽，不构成覆盖。
3. **冲突成本干跑**：`git diff --name-only <merge-base>..HEAD` 与 `..origin/main` 求交集看撞面（通常交集很小）。再用 `git merge-tree --write-tree HEAD origin/main` 无副作用模拟合并（首行是 tree hash，后随 CONFLICT 行）。数真实冲突 hunk：`git cat-file -p <tree>:<冲突文件> | grep -c '^<<<<<<<'`。自动并上 ≠ 语义对。serve/server.py 咱的东西（中文 wrap-up 常量、按 id 恢复、manifest）并入后，要列入回归复核清单。
   - **Strata 特有的两处语义接缝**：`src/program/generate.cpp` 的缓存默认值与上游新加的缓存自动定容块（上游按 RAM 缓存写，咱的盘缓存没有 RAM 条目，默认值不同时这段就是死代码，要显式停用并注释）；`serve/server.py` 的 Monitor 正则（上游要 `parked=P bytes=B`，咱的停放行是 `parked N tokens to disk … entries=… bytes=…`，恢复行是 `restored from file (N tokens, X ms)`，不改就监控卡全零）。文本零冲突也会在这两处出语义问题。
4. **价值映射到本机**：上游 release notes 的性能条目大多绑硬件。**gfx12/RDMA4 的默认开关对 gfx1100（7900 XTX）不生效**，至多是 opt-in 环境变量，别按 release notes 记账提速。对咱真值钱的通常是 serve 层与缓存的**正确性** fix。咱的 serve/server.py 就是从上游 fork 的，同一 bug 在咱链上同样存在。grep 上游 log 按 `hip|rdna|serve|park|restore|cache` 过滤取交集。官方「答案 byte-identical」指的是官方树默认模型，对咱 fork 未复验就别引用成结论。合并目标选热修补丁版（x.y.z.1），releases 页先看「Update:」后续勘误。
   - **大版本号 ≠ 引擎动了**：release notes 开头常单列「Engine package version X.Y.Z.W」——主版本号跳（0.1→0.2）可能全是壳（App/Terminal/打包），引擎只挪了 patch 位。判「值不值得追」先对引擎包版本与咱在跑基线的差，再数引擎面提交（`git log --oneline <咱基线>..<tag> -- src/ serve/`），别看版本号和 App 功能记账。
   - **App 版本与引擎包版本分开查，引擎包还会按模型家族分家**：release notes 会写「engine packages are version X」和「your Qwen engine does not change: every engine package is still the X file, byte for byte」。一个 App 发布可能只加另一个家族的独立引擎包（DeepSeek），Qwen 引擎逐字节不动；点版本也可能只改 Control。先确定「最新一个适用于咱家族的引擎包版本」，再数那个版本之前的引擎面提交，别拿最新 App tag 当引擎版本。
   - **gfx1100 的追新结论要落到提交实物**：先按 `gfx1100|7900|rdna3|RX 7000` grep 提交标题做初筛（多数会是打包、文档、更新提示），再看 `git log <基线>..<引擎tag> -- src/kernels/` 的硬件关键词分布。若大头是 trellis/Gyro/WMMA(gfx12)/Pascal/CPU AVX/IQ 量化，说明没有本机的引擎提速；真正的收益通常是 serve 层与长 prompt 的正确性修复。
   - **Qwen3.8 的 QSA 没有独立目录，不能按家族名或提交标题判断相关性**：QSA 是 48 层里的 12 层全注意力（`full_attention_interval=4`），代码散在 `src/kernels/cuda/qsa_*.cu`、`include/strata/core/layer.hpp` 的 `QsaState`、`include/strata/kernels/qsa*.hpp` 和 `conversation_snapshot.*`。评估上游 QSA 改动先 grep 这些实物文件，再看 `git log <基线>..<引擎tag> -- src/kernels/cuda/qsa_prompt_attn.cu src/kernels/cuda/qsa_select.cu include/strata/core/layer.hpp`。硬件落点看开关：gfx12 默认、gfx11 需 `STRATA_HIP_WMMA=1`（`STRATA_PA_GFX11` 在 0.1.45 就存在）、`auto` 只选 gfx12；没有 gfx1100 实测就别说有增益。
   - **合并前确认盘缓存依赖的 QSA 接口有没有动**：`git log <基线>..<引擎tag> -- include/strata/core/layer.hpp include/strata/core/geometry.hpp include/strata/core/conversation_snapshot.hpp src/core/conversation_snapshot.cpp`。空输出说明 `QsaState`/快照接口未变，盘缓存不需要跟着改；有提交则先评估 manifest 和快照格式。
   - **Known limits 一节是硬件适配的第一手证据**：维护者会自报「包已构建但从没在 X 卡上跑过」「调优表未打进包里、排期到下一个补丁版」。咱的卡（gfx1100/RX 7000 系）落在这种自报未验证名单里时，追 beta 等于给生产机当测试床——等点版本补上再追。官方自报性能全是别机测量，引用必标「咱机未复验」。
   - **PR 接受窗口会翻转**：给上游递 PR 前，按 github-pr-workflow 的「提 PR 前先测上游接受模式」重测一轮（合并 drought、清台模板、CONTRIBUTING 硬闸）——几周前「直接收 PR」的结论到供稿时可能已失效。

### 版本映射与 QSA 边界（2026-10-24 实测）

- **App 版本 ≠ 引擎版本**：0.2.1=引擎 0.1.46；0.2.2=0.1.47；0.2.3=0.1.48；0.2.4 的 Qwen 引擎仍是 0.1.48（逐字节不变），只加 DeepSeek 独立引擎 0.1.49；0.2.4.1 只改 Control。追 Qwen 主路只追到 0.1.48，不追 0.2.4.x。
- **QSA 是 qwen4exp 的 12/48 层全注意力**，状态在 `QsaState`（`include/strata/core/layer.hpp`），不叫 `src/qwen4exp/`。0.1.45→0.1.48 的 QSA 改动落在 gfx12（WMMA 默认）、SYCL、CUDA（Volta/Turing）；gfx11 的 `STRATA_HIP_WMMA=1` 在 0.1.45 已可选，0.1.48 仍非默认，`auto` 只选 gfx12。`QsaState`、`geometry.hpp`、`conversation_snapshot.*` 在这窗口 0 提交，磁盘缓存补丁不用改。
- 0.2.3 Known limits 明写 RX 7000「built and checked, not run on real hardware」；gfx1100 的追新收益按正确性修复与减少漂移算，不按 QSA 提速算。

## 排查陷阱
- **重启时的「stopped unexpectedly (exit code -15)」**：`systemctl restart` 的 SIGTERM 会先落到引擎，serve 把它当意外停止。打印通用的「usual cause is running out of RAM」文案，然后自动拉起（「starting the engine again」）。**先对照重启时刻再怀疑 OOM**，别误报。
- **serve 关闭路径的 AttributeError**（`close()` 里 `self.proc` 为 None，出现在 `server.err.log`）：SIGTERM 清理时的无害噪音，每次重启一条，非异常。
- **日志分居两个文件**：serve 层的 print（Settings / thinking / done 行）在 `/var/log/llama-server/server.log`。引擎输出在 `Strata/strata-iq3_s.log`。grep 错文件会得出「没生效」的假结论。
- **大日志提取用原生 open() 逐行读**（做统计或生成新文件时）。read_file 工具与 execute_code 的 helper 输出带 `N|` 行号前缀（回写即污染交付件）且 2000 行读取约 100K 字符处截断。统计会静默少数据（实测一次块计数 92 vs 103）。日志无时间戳，锚点用行号字面量（`engine stopped`、`parks=1` 计数重置行）而非时间。
- **引擎日志含二进制垃圾字节**：grep 报 `binary file matches` 后不打印匹配行，加 `-a`；python 统计用 `open(path,'rb')` 逐行 `decode('utf-8','replace')` 再跑正则，直接文本读会静默漏行。
- **正则要按日志原文字面拼**：复用行完整格式是 `prompt N tokens = M reused + X read in T ms`，`tokens =` 和 `reused + X read in` 都是字面量——按缩写形式 `prompt N = M reused` 拼的正则匹配 0 行还以为没数据。
- **压缩事件的日志指纹**：连续两请求 prompt 落差 >50K 且后一条仍 >20K＝上游对话压缩（LCM 类）触发，后一条的 read 列即重预填充代价（实测中位 ~13K token / ~20s，复用大头存活）。按 `engine started` 分段后每段最大 prompt 封顶在同一数值＝某条外部阈值线在掐顶，不是引擎窗口不够。停放快照随会话深度线性涨（13 万 token ≈ 2.2 GB snapshot），拉长会话前先看 `evicted … under the spill budget` 计数。现成统计脚本：`scripts/prompt-size-analysis.py [日志] [--era]`（分位数/分桶/压缩事件代价/冷预填充速率/分段封顶一次跑齐，基线复算直接用它）。
- **数据目录与仓库平级**：`Strata-data/` 是 `Strata/` 的兄弟目录（`~/Documents/LLM/Strata-data`）。从仓库内用相对路径访问（`Strata-data/…`）会解析到不存在的路径并静默 not found（可被误读为「段/文件都被清了」）。涉及数据目录的命令一律写绝对路径。
