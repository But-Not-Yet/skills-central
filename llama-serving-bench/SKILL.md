---
name: llama-serving-bench
description: "在生产机跑 llama.cpp 服务基准、验证二进制身份或规划停机窗口时使用；诊断推理服务内存缓存失效、用 cgroup 把冷缓存编排进 swap 时也加载。"
version: 1.0.0
author: Nekonya
license: MIT
metadata:
  hermes:
    tags: [llama.cpp, benchmark, ROCm, production, downtime-window]
---

# llama.cpp 服务基准（生产机）

## 何时使用

在主人的 AMD/ROCm 生产机上基准 llama-server 服务配置（load-mode、缓存、buffers）、验证生产服务实际跑的是哪个构建树，或规划任何需要重启生产服务的测试时。覆盖二进制身份、停机窗口协议、基准卫生。

## 生产二进制身份（对「这个构建」下任何结论之前先做）

机器上有大量 llama-server 二进制（多个裁剪/fork 构建树）。未先钉死生产身份，禁止对「这个构建」做版本或能力声明：
1. `systemctl show <service> -p ExecStart` —— 解析实际脚本，再解析它指向的实际 BIN 路径。
2. `ps` 查看运行中进程，逐参数与脚本 cmdline 对比。运行与脚本漂移会发生（进程启动后文件里的参数被改过）—— 向主人报告漂移，绝不悄悄「修好」。
3. 对该精确二进制跑 `--version`，用 commit 对照该树的 `git log -1`。
特性可用性以生产二进制自身的 `--help` 加该树源码 grep 为准——别的树的特性不算数。

## 停机窗口协议（主人偏好的分工）

凡需重启生产服务的测试，批量进一个停机窗口，由 agent 写好的自动化脚本留在盘上驱动。主人亲自停启服务，agent 不自行重启生产。脚本把所有结果写盘（CSV + 每臂日志），主人只需说「跑完了」，agent 读产物——不需要手工粘贴。之后一起读数，胜出配置由主人亲自应用到启动脚本。

脚本骨架（已验证形态）：
- 非 root（drop_caches）或生产服务未确认停止（对其端口 `pgrep` 守卫）则拒绝运行。另守卫测试端口上的残留实例（`pgrep` 测试端口，告诉主人 `kill -9`）：中途 Ctrl-C 会留下 nohup 的 server 占着 RAM/VRAM。
- 各臂定义为 name|extra-flags 行；默认跑全部臂，参数可选子集走短窗口。
- 从生产脚本的 exports 逐字重建测试实例环境（ROCR_VISIBLE_DEVICES、LD_LIBRARY_PATH、GGML_* 环境量）加测试端口和 `--no-webui`；除实验开关外所有参数钉死生产值，各臂只差那个实验 flag。
- 每臂：启动前 `sync; echo 3 > /proc/sys/vm/drop_caches; sleep`（公平冷启动），计时启动到 /health 就绪，预热请求（不计时），然后用 /completion API 的 `timings` 对象做计时探针（冷 PP 用 max_tokens=1，第二次相同调用 = 缓存命中 PP，生成探针固定 seed 和 max_tokens），测量窗口内对 server PID 采样 pidstat，前后记 MemAvailable。

## 宿主机内存与推理缓存调优

长上下文请求 0 复用、parking 日志刷屏、要把冷缓存编排进 swap 或给服务设 cgroup 内存压力时，先读 `references/host-memory-cache-tuning.md`——含缓存失效诊断流程、MemoryHigh 定标算术（可回收池 = RSS − 锁页体积）、验证四连。引擎无关。

## 构建替换 / fork 发布跟踪

从活跃开发的 fork 重建生产树时，「最新」= 最新 release TAG（代码冻结锚点；tag 后的分支尖端提交只是文档）。按其声明的 base 应用合并补丁复现发布，并对照 release.json 校验树哈希——完整配方与替换后的日志对比法（边际率对比、启动记账差异、消失的警告作为激活证据）在 `references/fork-release-rebuild.md`。

## 基准卫生（跑前写死的预注册判据）

- 淘汰标准开跑前写下，例如「解码较基线臂回退 >10% 即淘汰该臂」。读数不追溯重定义判据。
- 冷路径与缓存路径每臂分开测；缓存命中检查兼作 load-mode 没破坏 prompt cache 的正确性检查。

## 工具陷阱（cost time once, remember forever）

- llama-server 接 SIGTERM；若优雅清理挂起（见过：ROCm/HIP teardown 卡在 `cleaning up before exit...` 后），两次 SIGTERM 都被吞、进程存活——测试实例直接 `kill -9`，基准脚本在臂间宽限期后 SIGTERM→SIGKILL 升级。
- 模型还在加载时 `/health` 返回 503；裸 `curl -s` 对任何 HTTP 响应都退 0，所以启动到就绪的循环必须用 `curl -sf`。症状：几秒就「就绪」，首个 completion 请求 HTTP 503。相关：lazy-mode 下加载很快完成（几十秒、RSS 很小）——就绪仍须以 /health 200 加一次成功预热为门；**但预热过 ≠ 负载健康：首条完整负载请求仍可能崩，崩了按 FAIL 终止、不重试。**
- server 日志时间戳是 mm.ss.mmm（如 `0.35.421` = 35.4 秒），不是秒——误读会让新 server 看起来跑了几小时；用 `ps -o lstart` 核进程年龄。
- `pidstat` 不带 `-r` 只打印 CPU 统计——故障列不存在。永远 `pidstat -r -p $PID 1`；代价实录：两列 CSV 静默把 %usr/%system 记成了 minflt/majflt 峰值（2026-10-03，被外部审计抓到）。带 `-r` 时 PID 后的列是 minflt/s majflt/s，Time 列可能含 AM/PM 字段——按定位 PID 字段解析，不用固定下标。
- 外部审计能抓到自审漏掉的：上面的 pidstat 列 bug，还有一个过期环境量名穿过几轮评审没被发现。把收到的审计当待核声明（读 pidstat 文件自己的表头、grep 源码树），然后明确接受/拒绝。
- 残留测试实例占着基准端口会让下一臂 bind 失败（`couldn't bind HTTP server socket`）——看起来像那臂的 flag 失败其实不是。每臂清理后验证端口确实空闲（curl /health 必须拒绝），归因 FAIL 先读 server 日志尾部再怪 flag。
- `/completion` 响应的 `timings` 键是 `prompt_n / prompt_ms / prompt_per_second / predicted_n / predicted_ms / predicted_per_second`。没有 `predicted_tokens` 也没有 `eval_count`——解析错键配 `.get(..., 0)` 得到静默 0.0。写解析器前用真实捕获的响应校验键名。
- 计时探针永不重试。首次失败已填了服务端 prompt cache，重试不再「冷」（见过：冷/缓存/解码时间全同、`cache_n` ≈ 整个 prompt）。每探针一次；失败就记 FAIL，不记重试数字。
- 把多个探针的 timings 存 JSON 时，存每个探针自己的响应对象——复用循环最后 body 会让所有键相同。
- 完全缓存命中时 PP tps 无意义（prompt_n ≈ 0）。诚实的缓存指标是响应里的 `prompt_ms`（重算延迟）；CSV 列名照此标。
- Prompt 规模：行数 × 每行词数，先对 token 量级做合理性检查再信「~4k token」的注释（见过：2400 行 × 13 词 ≈ 46k tokens）。
- 空结果（臂 == 基线）只有在被测 flag 的激活被证明过才成立。若 flag 的成功路径静默（只有失败打 WARN），「无错误」不是激活证据。至少用其一证明激活：(a) 日志里的正面 INFO 行；(b) 对照臂的失败签名——若该 flag 的变体只在机制活着时才可能那样坏（如 O_DIRECT 对未对齐 pread 报 EINVAL），干净臂可证明到了同一层；(c) 为机制设计的判别探针（dio 绕过 page cache → 比较加载期 `/proc/PID/io` pgpgin 或 `/proc/vmstat` 增量）。都没有就报「无可测收益，机制激活未验证——判别实验很便宜，值得跑」。
- 计算受限段的空 diff 对 IO 路径 flag 什么都不能验证：被测阶段是 GPU 计算受限（如 PP 几百 t/s）时，读路径改动藏在计算之下，无论激活与否 A/B 都相等。IO 旋钮要在 IO 是瓶颈的场景判（冷加载时间、缺页计数、page-cache 增量）——并声明结论声称适用于哪个场景。
- rdna-boosts 树的 dio 兼容性（2026-10-03）：`--load-mode dio` + `--lazy-mode on` 干净（0 错误），但加 `--lazy-buffer-size 16G` 会在推理时刷 `llama-lazy-reader.cpp:290 pread failed: Invalid argument`（11×）。组合臂失败本身就是结果——留在矩阵里并记录失败。
- `pgrep -f` 会匹配 llama-server 的每个线程（本机十几条同 cmdline）——存在性守卫可以，计数会误导；也别用 `pgrep -x llama-server` 当残留守卫：会抓到无关实例（LCM 2B server）挡住合法运行。按端口模式守卫。
- rdna-boosts 树的 llama-bench 参数可用性（`--help` 验证，2026-10-03）：`-lm/--load-mode`（含 dio）和 `-lzm/--lazy-mode` 已接线；`--lazy-buffer-size` 和 `--cache-ram` 没有——需要这些 flag 的臂只能对 llama-server 实例测。也没有 `-c/--ctx-size`：llama-bench 自己算 ctx（`n_ctx = n_prompt + n_gen + n_depth`，llama-bench.cpp:1293）——传 `-c` 报 `error: invalid parameter for argument: -c` + 全量 usage（代价实录 2026-10-03：跑打印 usage 一秒内退出，输出像「help text」异常，直到读了 .err）。
- 多值参数（如 `-lm none,dio`）让 llama-bench 一条命令自己跑双臂对比；`-o json` 出可解析输出。
- llama-bench 默认值与生产不同（`-ub 512` vs 生产 2048）：不对齐 `-b/-ub/-fa/-ctk/-ctv/-t/-ngl/-ncmoe` 到生产脚本值，PP/TG 数字对 server 测量就无意义。关键：不带 `-ncmoe <生产值>`，`-ngl 99` 会把整个 90 GB 模型塞进 24.5 GB GPU——加载时 `cudaMalloc failed: out of memory`（代价实录 2026-10-03；详细错误只在 `--verbose` 出现，普通跑的 .err 只说 "failed to load model"）。
- 自定义 server 基准测量块要第二意见：与同加载路径的 llama-bench 裸吞吐交叉验证（脚本：项目 framework 目录的 `bench_lbm_cross.sh`，`-p 4096 -n 64 -r 1`）。两边不一致先怀疑自定义块——它有 bug 历史，llama-bench 没有。
- 2026-10-03 交叉验证基线：llama-bench tg64 ≈ server decode_tps（23.74/23.86 vs 23.59-23.68，<1.1%）——解码交叉验证通过；llama-bench pp4096（683.7，热态）vs server cold_pp（573.8）差约 19%——这个差就是 lazy 冷读 IO 成本，方向一致，不是异常。
- `systemctl start llama-server` 约 1 秒内 exit 1 死亡，先当 VRAM 问题：systemd journal 只说 `status=1/FAILURE`，真实原因在 `/var/log/llama-server/server.err.log`（`load_tensors` 下的 `cudaMalloc failed: out of memory`）。第一嫌疑：残留测试实例还占着 VRAM（先 kill -9 再查 `pgrep -f 'llama-server.*--port'` 才重启生产）。
- 用 bash `printf` 追加含 `%` 的文本会炸（"invalid format character"）——用 heredoc `cat >>`。
- Agent 的 sudo 可能要密码；需要 root 的脚本按上面的停机窗口协议交给主人跑。
