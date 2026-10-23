---
name: qlora-unsloth-training
category: mlops
description: "跑 Unsloth/QLoRA 微调时使用。只要涉及 Windows/WSL 环境陷阱、环境变量开关或训练监控，就主动加载。"
version: 1.0.0
author: Nekonya
license: MIT
metadata:
  hermes:
    tags: [unsloth, qlora, training, wsl, llama-cpp]
    related_skills: [lcm-summary-tuning, llama-cpp, rkllm-deploy]
---

# QLoRA / Unsloth 训练运行与排障

## When to Use
在 Windows/WSL 混合环境用 unsloth + TRL 跑 QLoRA（LoRA）微调时的环境配置、报错排查、训练监控与进度汇报。

## 环境入口（用户笔记本训练机）
- SSH 别名 `laptop-training`（Windows 主机）；WSL 内命令统一走：`ssh laptop-training wsl.exe -d Ubuntu-24.04 -u <user> -- bash -lc "命令"`。
- Windows Update 重启后可能把 WiFi 网络类别改成 Public，防火墙随即拦 22 端口 → SSH connection timed out、ping 100% loss。排查顺序：先 ping 区分「主机不可达（睡眠/关机）」vs「主机可达但端口被拦（网络类别/防火墙）」，解决方向是网络设为 Private 或放行 sshd；不要盲目重试 SSH 本身。
- 经 ssh→wsl.exe→bash -lc 的三层引号嵌套极易碎（单引号/双引号/转义层层吞），复杂命令（含 python -c、多管道、中文）一律 base64 编码后传：本地 `base64 -w0`，远端 `echo <b64> | base64 -d | bash` 或写入临时 .py/.sh 再执行；SSH 回显中文按 GBK 解码。用 scp 从 stdin 传内容（`scp - laptop:path`）会报 `stat local "-"` 失败，heredoc 经 ssh→wsl.exe→bash 多层会报「此时不应有 <<」语法错，stdin `cat >` 也可能报「系统找不到指定的路径」——文件传输统一走 base64：短的直接 `echo <b64> | base64 -d >`，超命令行长度限制的分块（≤1500 字符/块）`printf %s '<chunk>' >>` 追加到临时 .b64 再解码。
- WSL 内 tmux socket 按用户区分：root 用 `/tmp/tmux-0`，普通用户用 `/tmp/tmux-1000`；`tmux ls` 报 "no server running" 先确认是不是查错了用户的 socket。
- 长训练放 tmux 会话 + 日志落盘（`> logs/xxx.log 2>&1`），SSH 断连不影响训练。点火后就主动告知用户日志路径与实时查看方式（`tail -f <log>`、`tmux attach -t <会话名>`、`wc -l` 输出文件行数），用户会自己看，不要等用户问。
- 启动长训练用**自包含启动脚本**（如 `run_full.sh`）：所有 export 环境变量、cd、训练命令、结束时间戳全部写进脚本文件，tmux 只负责 `bash run_full.sh`——避免多层引号转义丢失环境变量，也让启动命令本身可审计、可复现（脚本落盘并记 sha256）。

## unsloth 真实环境变量开关（先 grep 再设，别凭记忆）
设置任何 unsloth 环境变量前先 `grep -rn 'os.environ' site-packages/unsloth_zoo/fused_losses/*.py`（以及 unsloth/trainer.py、unsloth_zoo/gradient_checkpointing.py）核对真实变量名——网上流传的变量名在新版本里可能根本不存在，设了等于没设。已实测核对（unsloth 2026.9.x）的真实开关：
- fused CE compile：`UNSLOTH_FUSED_CE_COMPILE_DISABLE=1`
- fused CE 分块：`UNSLOTH_CE_LOSS_TARGET_GB` / `UNSLOTH_CE_LOSS_N_CHUNKS`
- 梯度双缓冲：`UNSLOTH_DISABLE_DOUBLE_BUFFER=0/1`（WSL 的 GPU paravisor 对 pinned memory 并发 H2D 敏感，报 `CUDA driver error: device not ready` 时优先关掉它）
- 自动 padding-free：`UNSLOTH_DISABLE_AUTO_PADDING_FREE`
报 "No or negligible GPU memory available for fused cross entropy" 时的正确方向是调大 `UNSLOTH_CE_LOSS_TARGET_GB` 留余量，而不是找开关关掉 fused CE。

## 已验证的框架版本陷阱
- transformers 5.x 把 `torch_dtype` 改名 `dtype`，老 unsloth loader 读 config 会 KeyError → patch loader 兼容两种键名。
- xformers 无新卡（sm_120/CC12.0）内核：fa2/fa3/cutlass 全不支持 → 直接卸载 xformers 让 unsloth 回退 SDPA，比强行配置更稳。
- Windows spawn 多进程：`datasets.map` 多进程会把 unsloth 动态生成的 UnslothSFTTrainer 送进 spawn 子进程 pickle 而崩（`ModuleNotFoundError: UnslothSFTTrainer`）→ SFTConfig 里显式 `dataset_num_proc=1`。
- fused CE 与 transformers trainer 的 `loss *= n` 就地修改冲突（autograd view 被 inplace 改）→ 把 trainer.py 该行改成外积形式 `loss = loss * n`。

## 训练监控的正确姿势
- loss 别从 tqdm 进度条读（tqdm 刷新会覆盖 loss 行）；跑完后从 checkpoint 目录的 `trainer_state.json` → `log_history` 读各 step 的 loss/eval_loss，这是权威来源。
- 最终 adapter 保存路径用绝对路径或先确认 cwd：相对路径 `save_pretrained` 在 schtasks/tmux 环境下可能落错目录报 `PermissionError WinError 5`。
- 决定 max_length 前先测数据 token 长度分布（P50/P90/P95/P99），按 P90~P95 截断通常几乎无损且大幅提速；长尾极重的数据集（P99 是 P50 的几十倍）截长尾是最大的提速来源。

## 评测集下载与解析陷阱（datasets 库 ≥4.x）
- datasets ≥4.0 彻底弃用脚本式数据集：`trust_remote_code=True` 同样不被支持，直接抛 `RuntimeError: Dataset scripts are no longer supported`。旧 README 里的 `load_dataset("haonan-li/cmmlu", ...)` 写法全部失效——先查 HF API 的 siblings 列表（curl 必须加 `-L`：hf-mirror 的 /api 端点对无跟随请求返回 308 重定向且 body 为空），改从 repo 直接下载原始数据文件自行解析。
- CMMLU 原始数据是 `cmmlu_v1_0_1.zip`（zip 内 test/ 与 dev/ 各 60+ 个 csv）：表头为 `,Question,A,B,C,D,Answer`（首列空是题号）。题干本身含中文逗号，naive `split(",")` 会把答案列错位成整段文字——必须用 `csv.reader` 按表头解析；WSL 精简环境常无 unzip 命令，用 python `zipfile.ZipFile.extractall` 解压。
- 抽样后先验证答案列全部 ∈ {A,B,C,D} 再上模型：答案分布异常（出现长文本答案）就是解析错位的信号，先修解析器再跑推理。

## 评估（评测集推理+指标）阶段的固定校验
- **训练前验证格式契约一致性**：验收标准要求的输出格式（如四节骨架）必须先在训练集 assistant 目标上测一遍命中率——system prompt 要求格式 A 而训练目标是格式 B 时，LoRA 会把 B 学牢并冲掉基座模型原生的 A 倾向（骨架符合率反而从 61% 归零）；loss 收敛只证明内容映射学到，不证明格式服从。指标类缺陷先于模型问题排查：拒绝率检测若用宽窗口（如前 80 字）search 拒绝词，会误中摘要正文内的「无法更换」「无法恢复」等合法内容——正确做法是先剥离输出开头的 think 标签对（训练抑制 thinking 后模型常留空标签对，会污染所有首句类指标），再对正文开头 ~20 字符用 `^` 锚定匹配真实拒绝模式；剥离函数用字符串拼接构造标签字面量（"<"+"think"+">"），并在指标中报告剥离后残留计数应为 0。
- A/B 对比（基座 vs LoRA 候选）前必做三项一致性校验：① 评测集内 system prompt 唯一性（对全部行的 system 做 md5 去重计数，必须=1 个版本）；② 基座与 adapter 的 chat_template.jinja md5 一致（不一致=训练改过模板，A/B 变量不干净）；③ 泄漏检测：用 user 内容前若干字符（如前 200 字符）做指纹与训练集求交集，重叠必须为 0。
- 对比推理统一 greedy（do_sample=False），显式覆盖模型自带 generation_config 的 temperature/top_p——A/B 之间只允许差 LoRA 这一个变量。
- 五项指标口径：骨架四节符合率（正则匹配四个标题全命中）、逐字保留率（正则抽 source 中的路径/命令/数值，查是否在 hyp 中原样出现）、拒绝回避率（首句匹配「无法/抱歉/作为AI」类）、ROUGE-1/2/L（jieba 分词后计算，需 pip 装 jieba+rouge）、压缩率=输出长度/输入长度（对照目标区间）。
- 长跑推理脚本要点：逐条 flush 写 jsonl（中断可续/可查进度）、每 N 条打一行 progress 日志、tmux 承载；跑完由 watch 循环（轮询完成标记后自动跑指标脚本）接力出报告，agent 不需要盯完再手动算。
- base vs LoRA 双配置同一脚本跑时，测完 base 后必须 `del model; gc.collect(); torch.cuda.empty_cache()` 并重新 from_pretrained 加载干净基座再挂 adapter——在已 merge 的模型上叠加第二个 adapter 会污染对比。选择题评测：prompt 要求只输出单字母，但 max_new_tokens 要给足（≥64，8 会截断带 think 标签的输出导致提取失败）；提取用 `re.findall(r"[ABCD]", hyp)` 取**最后一个**匹配——首次匹配常命中题干回显或 think 内容里的无关字母（曾使 base 准确率虚降为 0），且不要对输出做任何标签剥离/预处理层，直接在完整输出上取末位匹配即可。

## 长训练的等待与汇报纪律（agent 自身）
- 等待长任务时用固定「每 N 分钟检查一次、最多 M 次」的节奏，不要反复权衡「等多久」再决定——决策无客观判据时的自我权衡是 thinking 重复循环（repetition loop）的触发条件之一。点火后先 sleep 固定短时间（如 90s）tail 一次确认起跑，再进入固定轮询。
- **训练与 agent 解耦**：训练进程的生死必须不依赖 agent——tmux + 日志落盘 + checkpoint 自动保存 + `--resume last` 恢复，agent 轮询只是临时 SSH 读文件；点火命令必须先于轮询发出。agent 轮询退化/断连时训练零损失。
- 进度条等重复模式的大量输出会污染上下文并助长复读；检查训练状态用 `grep loss` / trainer_state.json 拿结构化结果，别 tail 大段进度条。
- 验收 grep nan/inf 时区分真 NaN 与提示文案：Unsloth 预过滤全 -100 标签样本时日志会打出「prevents NaN loss during training」提示，命中 nan 字样但不是真 NaN——确认命中行是 loss/grad 字段本身（如 `grep -E "(loss|grad)[^,]*(nan|inf)"`）而不是只有提示语。
- 自我检测：如果发现自己在输出里反复「我现在调用/（生成）」而工具没真的发出去，立即中断自己并报告。

## /goal 撰写标准（用户验收口径）
- 每个 subgoal 的完成判据必须是**命令可直接核验的客观状态**（文件存在且 >0 字节、数值阈值、10/10 计数、日志含某行），不允许主观描述；每个 subgoal 附「审计方式」列出复核命令（ls/grep/python 解析 trainer_state.json、sha256sum 落盘）。
- 失败路径预定义：每阶段重试上限 2 次，第 3 次暂停交用户裁决并记录复现命令+完整报错，禁止静默换路线；降级动作（如 max_length 降档、关双缓冲）写成量化触发条件。
- 目标参数与脚本实际值冲突时取更严格者（如目标 save_steps=200 而脚本是 100 → 保持 100，在 PROGRESS.md 记录差异），**未经用户批准不擅自改训练脚本**；用户显式拍板的决定直接执行，不再重新权衡论证。
- 进度台账 PROGRESS.md 随每项完成实时更新，记录脚本 sha256 指纹、启动参数、进度基线，作为审计证据链。
