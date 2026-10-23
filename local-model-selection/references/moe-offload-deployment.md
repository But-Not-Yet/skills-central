# MoE 专家卸载：部署参数推导与排障

选完模型之后的下一步。目标：把「能不能跑」变成「用哪组参数跑」，并把首次加载与
首块 PP 的停顿和稳态性能区分开。

## 1. 卸载块数 N 的推导（不估，算）

llama.cpp 的 `--n-cpu-moe N` / `-ot "exps=CPU"` 把路由专家放内存。**N 数的是前 N 层**（`blk.0`…`blk.(N−1)`，从第 0 层起），所以：

自证方法：`--n-cpu-moe 3` 等价于 `-ot "blk\.(0|1|2)\.ffn_(up|down|gate|gate_up)_(ch|)exps=CPU"`。
方向搞反不影响内存账（卸载的块数一样），但会影响你对日志与摆放的判断。

```
N = 含专家的块总数 − 能留在 GPU 的块数
能留 GPU 的块数 = (可用显存 − 非专家权重 − KV − 计算缓冲) / 每块专家体积
```

- 先跑 `scripts/gguf_expert_split.py <model.gguf>` 拿真实拆分（只读文件头，不下整模型）。
- **非专家张量是显存地板**：注意力、稠密 FFN、共享专家、norm、embedding 每 token 必走，
  不能卸载。它决定「这个模型在这个显存上到底能不能跑」。
- 留 **≥800 MiB 余量**。余量不足一块专家时不要再往上加，先降上下文或降 KV 精度。
- 注意含专家的块数**可能比 `n_layer` 多**（MTP / nextn 预测块也带专家张量）。按脚本报的
  实际块数算，别用 config 里的层数。

### 1b. 自动摆放（`--fit`）不等于最优——手工摆放常赢

llama.cpp 默认 `--fit on`，会自己算卸载量。**但只要你显式设了 `-ngl` / `--n-cpu-moe` /
`--cpu-moe` / `-ot` 任何一个，fit 就放弃并让位**（日志：`failed to fit params to free
device memory: ... already set by user ... abort`）。`--fit-target`（默认 1024 MiB 余量）、
`--fit-ctx`（可缩上下文，不低于 4096）可调。

**fit 优化的是「装得下」，不是「每 token 少读多少字节」。** 实测：fit 选出的卸载块数与手工值
**相同**，却把 **4.4 GiB 更多权重推进了宿主映射缓冲**，TG 掉约三成。

判定方法——两遍对比 `CPU_Mapped model buffer size`：

- 手工 `-ngl 99 + --n-cpu-moe N` 的价值是**稠密/热权重全部留在 GPU**，只有专家进内存。
- fit 若把一部分**稠密**权重也溢出到宿主内存，那部分每个 token 都要读一遍；溢出同体积的专家便宜得多
  （专家按 8/256 稀疏激活，稠密是全量）——这就是它变慢的机制。
- 只有**模型超卖显存、已掉进驱动换页区**时 fit 才真正救场（见下）。

### 1c. Windows 上的 V 形：卸载太少 vs 太多

- **太少** → 超卖显存。Windows 上 NVIDIA 驱动的 System Memory Fallback 会**静默**用宿主内存兜底、
  按需跨 PCIe 换页，吞吐崩到约 1/5（Linux 原生 CUDA 一般直接分配失败，更健康）。
- **膝盖** → 恰好装下，最快。
- **太多** → 每多一层多走一趟 PCIe，稳定线性下滑。

所以方向是「找**最少能糊弄过去**的卸载量」，不是「能卸载多少就卸载多少」。
手工摆放若正落在膝盖上，fit 帮不上忙——它只解决左臂的超卖问题。

## 2. mmap 与 CPU 覆盖的耦合（最容易误判的一处）

llama.cpp 在「专家卸载到 CPU」且 mmap 启用时会警告：

```
tensor overrides to CPU are used with mmap enabled - consider using --load-mode none
```

**机制**：CPU 侧专家默认是**虚拟映射**，首次触碰要从磁盘分页进内存 → **第一个 PP 块
可能慢一个数量级**（几十秒），页驻留之后才恢复。

**但 `--load-mode none` 不是无条件更好**：它要求 CPU 侧缓冲**一次性常驻内存**。
所以先核：

```
CPU 侧专家总量  vs  启动时的空闲内存
```

- **装得下** → 用 `--load-mode none`，首块不再卡。
- **装不下** → **mmap 正是让它能跑起来的东西**，别关。接受「每会话首次预热」，靠 prompt cache
  顶后续请求。硬上 `none` 会 OOM 或把系统拖进交换。

取值：`auto`（默认）/ `none` / `mmap` / `mlock`。`mlock` 同样要求常驻且需权限。

## 3. 从运行时日志核账（启动日志就是账本）

| 日志行 | 它告诉你什么 |
|---|---|
| `CPU_Mapped model buffer size` / `CUDA0 model buffer size` | 两侧权重的实际占用，拿来核你的估算 |
| `CUDA0 KV buffer size` | KV 是否真在显存（「KV 必须进显存」场景的验收项） |
| `CUDA0 compute buffer size` | 计算缓冲，常被估算忽略 |
| `graph splits` | 每 token 的 host↔device 往返次数；MoE 卸载下很大是正常的，但它是 TG 的主要拖累 |
| `projected to use X MiB vs Y MiB free` / `cannot meet free memory target` | 余量告警（软告警，不是错误）；需要缩多少会直接写出来 |
| `system_info` 行的 CPU 指令集 | 决定 CPU 专家路径走哪一档：有 AVX-512 VNNI 走快速档，只有 AVX2/AVX-VNNI 走较慢档 |
| `draft acceptance = …` / `spec statistics: draft-mtp: …` | 投机解码命中率与平均接受长度。**开着 MTP 时 TG 已含这份增益**，不是裸速 |
| `tensor overrides to CPU are used with mmap enabled` | 加载模式与 CPU 覆盖耦合的告警，见第 2 节 |

另：加载日志里的张量类型统计（`type nvfp4: N tensors` 之类）和 `file type` 行是**格式是否真被识别的验收项**——
加载成功不代表量化路径走对了，先确认类型行再谈性能。

## 4. PP 慢的诊断：算边际速率，别看累计

`slot print_timing ... prompt processing, n_tokens = N, t = T s / R tokens per second`
里的 R 是**累计平均**，会把首块的停顿摊薄到看不出来。

**逐行相减算边际**：`(T₂−T₁) / (N₂−N₁)`。

- **首块远慢于后续** → 是加载/分页/首次内核启动，不是算力。措施：按第 2 节处理加载模式；
  把 `--ubatch-size` 提上去。
- **`--ubatch-size` 是 PP 的主杠杆，但有代价。** 默认 `-ub 512` 对 CPU+GPU 混合明显偏小：
  实测 512→2048→8192 时 PP 约 380→1110→2090 t/s（≈5.5×），TG 基本不动（到 8192 才掉约 7%）。
  **机制**：更大 ubatch 把「读一遍宿主权重」与 PCIe 传输摊到整批上；TG 一次一个 token，摊不掉。
  **代价**：ubatch 越大计算缓冲越大 → 吃显存 → 逼你多卸载 → 又拖慢 TG。PP 重的负载（长上下文
  审查）值得往上推，但每推一档都要重核显存余量。
- **`--parallel` 显式设成 1。** 不设时自动开多个 slot、各配一份 KV，白吃显存。
- **全段都慢** → 才是算力或内存带宽问题，此时改卸载层数/上下文才有意义。

## 5. 复制启动脚本当母版：按架构挑，不按新旧

给 MoE 配启动脚本时，拿**稠密模型**的脚本当母版会静默丢掉 MoE 专用开关
（`--n-cpu-moe` / `-ot exps=CPU`、`--load-mode none`、`--ubatch-size`），
而丢掉的恰恰是 MoE 跑得动的前提。

改脚本前把母版里**每个 flag 过一遍**「这个模型需不需要」，而不是只改模型路径与采样参数。
最好直接选一个**同架构**的脚本当母版。

**换推理引擎前先核开关**：自建/分支构建与官方发布版的 flag 集合可能不同。
把脚本里用到的每个 flag 对目标二进制 `--help` 过一遍，再决定换不换。

## 6. 速度的物理上限（先算再调，免得白调）

TG 在单卡 + 专家卸载下由**内存带宽**钉死：

```
每 token 从内存读的量 ≈ 激活专家数 × 层数 × 3 投影 × (hidden × expert_ffn) × bpw/8
```

拿它除以内存带宽得到理论上限，再看实测差多少。差距大才值得调（减少 graph splits、
提高 CPU 向量档、把更多专家挤上 GPU）；差距小时调参只是自我安慰——真要提高只有
上更多显存、换支持 AVX-512 的 CPU、或换更小的模型。

**推论一：TG 约与「宿主常驻权重字节数」成反比。** 换更小的量化（或更小的模型）会直接抬 TG，
不只是「上更多显存」一条路。

**推论二：格式的 CPU 内核成熟度是独立变量。** 专家跑在 CPU 上时，该格式的 CPU 反量化/点积内核
质量直接决定 TG。新格式（NVFP4 一类）的 CPU 路径通常远落后于 Q4_K / IQ 系打磨多年的
AVX2/AVX-VNNI 内核，且官方讨论里承认其 NVFP4 存在职责划分不清、CPU 反量化实现有争议。
所以「更小但内核不成熟」的档未必比「更大但内核成熟」的快——换格式做 A/B 时把这条列成显式变量。

**推论三：读 TG 前先确认有没有开投机解码。** 开了 MTP 时 TG 已含草稿增益（实测同一模型
`mean acc len = 2.92`，即裸速只有报出值的约 1/3）；不核 `draft acceptance` 就归因硬件会得出错误结论。
另：MTP 需要量化时**保住草稿头**，不少转换会把它丢掉——加载日志里核 `spec common_specu: adding
speculative implementation 'draft-mtp'` 是否出现。

## 7. 远程 Windows 上的操作要点

- **看文件大小用 PowerShell，不用 `cmd dir`**。经 SSH 看远程文件时 `cmd /c dir` 的体积列会滞后或失真
  （下载中的文件显示 0 字节，实际已写了几 GB）。用
  `powershell -NoProfile -Command "(Get-Item '<path>').Length"` 拿真实字节数；
  要独立交叉验证就看**目标盘剩余空间的变化量**。
- **下载要防静默失败**。`curl` 不加 `-f` 时，HTTP 错误页会被当成正文写进 `-o` 文件
  （表现为文件只有十几字节的错误文本），且退出码仍为 0。**加 `-f`** 让 HTTP 错误报错退出，
  再用文件大小核对。
- **文件名要用仓库 API 给的真实路径**。从列表或展示里抄名字容易拿到被截断/美化过的显示名
  （前缀被裁掉），拿去下载就是 404。用 API 返回的 `rfilename` / `path` 原值。
- **写启动脚本**：GBK + CRLF，且**在目标机上生成**而不是本地写好再传
  （详见 `windows-bat-editing` 技能）。给新模型**新建文件名**，别覆盖用户现成脚本。

### 7c. 远程启长驻进程：SSH 的方式会随会话死

**从 SSH 会话里拉起的进程会被连带杀掉。** Windows 把会话的子进程挂在同一个 job object 上，
会话一结束（或那次调用返回）进程树就被清理。症状极具欺骗性：进程一度真的活着——健康端点
返回 503（llama.cpp 在「模型还在加载」时就是 503，**不是失败**）——然后凭空消失。
**快照看到「活着」不等于终态**；声称「起来了」之前必须回到测一次 `nvidia-smi` 占用或进程列表。
（503 确实表示服务在响应；问题在于它之后死了，而不是它没起来过。两件事别混。）

- **长任务用计划任务，不用 `Start-Process`。** `schtasks /create /tn <名> /tr "<bat>" /sc once
  /st 23:59 /f` 再 `schtasks /run /tn <名>`：它挂在 Task Scheduler 服务下，与 SSH 会话无关，
  断连也继续跑。bat 里把输出重定向到日志文件，之后轮询日志。用完 `schtasks /delete /tn <名> /f` 清掉。
- **服务就绪要三项一起核**：进程存在 + 端口 `LISTENING` + 健康端点 `{"status":"ok"}`。
  只看端口会在「端口在听但模型没加载完」时误判。
- **换模型前先杀旧服务**（`taskkill /IM llama-server.exe /F`），否则端口冲突，两个都起不来。
- **测前核模型身份，防测错模型。** `/v1/models` 返回 `id` / `aliases` 与 `meta`
  （`n_params` / `size` / `ftype` / `n_ctx`）——拿它对着磁盘上那个文件核一遍。
  旧进程没关干净时，端口、健康、占用全部看着正常，只有 alias 会出卖你。
- **不要替用户启动 GUI 服务。** 交互式进程（带 `pause` 的 .bat、需要窗口的引擎）经远程拉起
  既不可靠也难回收；让用户自己点，代理只负责写脚本、核就绪、跑测试。用户自己提这个分工时，接受它。
### 7b. 传文件过去（比生成文件更容易出事）

- **先确认连接真的通。** 远程命令**返回空**时先怀疑连接，不是「那边没这个文件」：
  跑一条最短探针（`hostname`）看退出码。SSH 配置里的地址会过期（VPN 与局域网地址互切），
  此时所有命令都静默返回空——包括本该报错的那些。
- **优先 `scp`，不用 base64 走命令行。** Windows 命令行上限约 **8191 字符**，base64 把文件撑大
  三分之一，边界附近的脚本会报「命令行太长」——**若把 stderr 重定向掉就完全看不见**，
  只能从随后「远端行为不对」反推。
- **不要吞远程写入命令的 stderr**（`>/dev/null 2>&1`）。失败原因就在那里。
- **传完两边对哈希**，不凭「写入成功」字样声称成功：本地 `sha256sum`，
  远端 `powershell -NoProfile -Command "(Get-FileHash '<path>' -Algorithm SHA256).Hash.ToLower()"`。
- **远端 Python 输出中文会乱码**（控制台 GBK）——跑前设 `$env:PYTHONIOENCODING='utf-8'`。
- **PowerShell 把 `a,b,c` 当数组**——逗号分隔的参数值必须加引号（`--ids 'nd1,nd2'`），
  否则静默拆成多个参数、过滤条件失效。
