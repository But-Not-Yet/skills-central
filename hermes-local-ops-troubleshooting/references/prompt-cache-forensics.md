# 本地 llama.cpp 系服务 prompt 缓存破坏法医（Strata / llama-server）

## 症状与机制

- 症状：每轮对话响应极慢（20 万 token 级 prompt 单次预填充 4 分钟），或时快时慢阵发。
- 机制两条，都要查：
  1. **单槽缓存互踢**：prompt 缓存只记最近一条对话流。两条大会话（不同 session）交替打同一服务 = 每次换流 0 复用，双方都付全额重算。这与插件无关，纯并发结构问题。
  2. **异前缀小请求插队**：辅助 LLM 调用（检察官/裁判/分类器）若用独立小 prompt（固定指令+载荷，与会话历史共享零前缀），每次插队即踢掉槽里的大会话 KV，下一次主对话 0 复用。指纹 = 日志里 `461 tokens = 0 reused` 这类小行夹在大 prompt 之间。
- 复用是**最长公共前缀**匹配：`prompt N tokens = M reused + K read`。前缀一致只算尾巴；前缀断裂整段重算。

## 法医流程（日志逐行解析）

1. 抓复用线：`grep -o 'prompt [0-9]* tokens = [0-9]* reused' <服务日志>`，Python 逐行解析成 (行号, prompt, reused)，算复用率。
2. 找「大 prompt 0 复用」连续段（episode），统计段数与时间分布——段数多 = 结构性互踢，不是偶发。
3. 看 episode 前后各 2 行：谁插的队（小 prompt 探针？另一条大流？）。episode 边界 = 凶手切换时刻。
4. 外部 API 通道单独对质：查 agent.log 逐调用 cache 命中统计——外部通道健康与否与本地槽无关，别混案。

## 修法（按凶手分层）

- 异前缀小请求 → **改成共享会话历史前缀**：messages = [会话历史…] + [尾部一条 user 消息装辅助指令+载荷]。LCP 机制下辅助调用自身命中刚预热的前缀，下一次主调用又复用槽里的共享历史段——单槽内两族 prompt 互相兼容。截断只丢最旧居中轮、保住首条 system 消息（前缀字节稳定）。宿主 `post_llm_call` 回调参数里现成带 `conversation_history`。
- 两条大会话互踢 → 结构性：一条挪去外部通道，或服务开多槽（Strata 实测解法见下节「多槽停放」），或给辅助调用起独立实例/端口。
- 验收判据（生效后才宣告）：辅助调用那行变成「大 prompt + 高复用」，且其后主调用不再出现大 prompt 0 复用。改完代码 ≠ 生效——须进程重载后按激活日志时间戳确认（见 SKILL.md「已改 vs 已生效」）。

## 多槽停放（Strata conversation parking，实测）

- 参数：`--conversation-cache-mib <预算MiB> --conversation-cache-slots <N> --conversation-cache-min-free-mib <RAM保底>`。停放条目住主机 RAM 不吃显存；**不并发执行**，只免重算——它治「0 复用全额重灌」，治不了排队。
- 日志指纹：`parked N tokens in X ms; parked=K bytes=... evictions=0`（停放）、`restored N tokens (checkpoint) in X ms`（换回，实测 6 万 token 仅 0.1 秒）、`reused_kv_bytes>0` = 跨流命中。停放后跨流切换从 0 复用变 99%+ 复用。
- **快照实测比纸面估算大**：18 万 token 会话快照 ~3.6 GB（KV int8 + rope + checkpoints + draft 全含），按「别算少」原则配槽预算，别拿纯 KV 系数外推。
- 准入门：停放前查**物理 RAM**（需本次快照 + floor 保底），不够就 `skip parking (physical RAM admission...)` 跳过——它只认物理 RAM 不认 swap。高水位下想停放要调低 floor（默认 2560 → 512），前提是已铺好 swap 缓冲垫。
- 排队与停放的区分：serve 层串行执行，多流仍一个个来——用户「发一句话等很久」而日志全是高复用时，凶手是排队不是缓存，`(cancelled)` 行 = 排队排到客户端放弃。治排队靠缩小辅助调用体积（只带最近几轮），不是加槽。

## 内存与 swap（停放配套）

- Linux 没有按进程的 swappiness；cgroup v2 只有 `memory.swap.max`/`memory.high` 硬限额（systemd 单元 `MemorySwapMax=`/`MemoryHigh=`）。想「单独调某服务的 swappiness」= 不存在，只能调全局或按组限额。
- cgroup swap 记账 ≠ 进程 Swap 字段：shmem/tmpfs 换出页只进 cgroup 的 `memory.swap.current`，smaps_rollup 看不见——两数对不上先算共享内存账，别急着怀疑数据错。
- 高 RAM 水位下扩 swap **别 swapoff 现有 swap**（把已换出页硬搬回 RAM 是 OOM 边缘赌局）：`fallocate` 新文件 + `mkswap` + `swapon` 叠加，零搬页、可单独撤回。非要原地换大，选大服务停机窗口做（停 llama-server 即释放 ~50 GB，搬页从赌局变散步）——顺序：stop 服务 → swapoff/换大/swapon → start 服务，一次重启带上新配置。
