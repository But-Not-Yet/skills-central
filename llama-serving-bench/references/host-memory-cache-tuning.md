# 宿主机内存与推理缓存调优（锁页专家 + 会话缓存 + swap 编排）

## 何时使用

推理服务（llama.cpp lazy/ncmoe、Strata 等锁页 MoE 引擎）出现长上下文请求 0 复用、parking/skip parking 日志刷屏、MemAvailable 踩线时；或需要把冷会话缓存编排进 swap、给服务设 cgroup 内存压力时。

适用于把 MoE 专家锁页驻留 RAM、会话/KV 缓存放 anon 内存的推理服务。三个动作：诊断缓存为何失效、用 cgroup 内存压力把冷缓存编排进 swap、验证没伤到热页。

## 缓存失效诊断（先量化，再下结论）

1. 从引擎日志统计 prompt 行：`prompt N tokens = A reused + B read`，累计 reused/read 算总体命中率。**总体命中率高 ≠ 缓存健康**——失效常集中在长 prompt 区间：按 prompt 长度分桶看 reused=0 的分布，0 复用聚集在哪一档，失效点就在哪一档。
2. 命中率断层与 parking 日志对齐：`skip parking (...)` 次数 vs 成功 parked 次数。skip 之后紧跟的 prompt 行就是全量重读（长上下文一次重读可达百秒级）。
3. 闸门算术用活体 `/proc/meminfo` 验：准入条件是 `MemAvailable ≥ 快照字节 + min_free 保底`。快照字节按引擎日志的 `need ... MiB` 读，别用估算。差几百 MiB 的临界失败是常态——余量薄的机器会间歇性踩线。
4. 根因模式（判定前先对照）：引擎常有两道闸串着——第一道按缓存自身预算逐出，第二道问宿主机真实空闲内存。**第二道判决是终审、不回头调第一道**，就是「缓存里明明有可腾的内存，快照仍被扔」的根因。上游修复思路是逐出-重试循环（逐一个 parked、查一次 /proc/meminfo、再判），16 MiB 段级分配一释放立即回到内核可见，无需等待间隔。

## cgroup 内存压力编排（把冷缓存放进 swap，不改代码）

前提事实链，逐项核验后再动手：
- 服务在 systemd 下跑（`/proc/<pid>/cgroup` 归到 system.slice/<unit>）→ `systemctl set-property <unit> MemoryHigh=...` **不重启即生效**。
- `cudaHostRegister`/`pin_user_pages` 锁页的专家区不可换出（GUP 长期引用期间内核禁止解除映射换页）——不是优先级低，是机制禁止。注意 `VmLck` 计数器只计 `mlock()` 系统调用，驱动 pin 不计入，**VmLck=0 不代表没锁**。
- Linux 没有「单个堆分配指到 swap」的手段；等价手段是 cgroup 压力：kswapd 只能回收 anon，锁页区不在可回收池里，挤压方向被强制约束。

**MemoryHigh 定标（关键算术）**：可回收池 ≈ 进程 RSS − 锁页体积（用 smaps 逐映射实测，别用 RSS 减报告值猜）。设 X 意味着 kswapd 必须挤 `RSS − X`。X 必须满足：挤出的量 < 冷缓存体积——差额会吃进活动会话的 KV，那才是真热页（每秒被摸几千次），被换出即 decode thrash。热页保护只是尽力而为：accessed 位只有近因一个比特，压力足够时会穿透 active list；anon 页没有文件页的 workingset/refault 保护，高压下更早被牺牲。宁可设松一档，靠验证读数收紧。

**为什么值得做**：冷缓存进 swap 后 MemAvailable 抬升 → 闸门通过、快照不丢；下次恢复 = 顺序读快照（秒级），对比全量重读长上下文（百秒级）约几十倍。与上游补丁互补：swap 保住快照，补丁兜 swap 也不够时的最坏情况。

**陷阱**：
- `MemoryMax` 别设——低于 RSS 的硬顶会触发 OOM kill 生产服务。只用 MemoryHigh（软压，挤不动就忍着）。
- 快照保存本身分配新页，高压下新写的快照页可能立即被换出——这正是「缓存住 swap」的目标态，不是故障。

## 验证四连（设完必跑，缺一不可）

1. smaps 逐映射核验：换出页必须落在缓存段的地址区间，**专家锁页区 VmSwap 必须为 0**——有异常立即 `systemctl set-property <unit> MemoryHigh=infinity` 撤销。
2. 复跑长上下文会话，确认 parking 闸门日志从 skip 变通过、重读消失。
3. decode tok/s 对照基线，回退即活动 KV 被误伤，放宽一档重来。
4. 结论落盘运维账本，参数变更记录在案（值、理由、验证读数）。
