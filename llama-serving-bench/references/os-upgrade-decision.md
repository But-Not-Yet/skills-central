# 生产推理机的 OS 升级决策（LTS → LTS）

## 何时使用

主人问「要不要把生产机从 Ubuntu 24.04 升到 26.04（或任意 LTS→LTS）」「升了有性能收益吗」「图形栈/驱动会怎样」时。也用于任何「为了性能/支持窗口而升级宿主发行版」的取舍判断。

## 先破一个默认假设：LTS 不等于旧内核（HWE 陷阱）

**动口前第一件事：读活体内核，别从发行版号推内核版本。**

```bash
uname -r                                   # 真实在跑的内核（本机实测 7.0.0-34-generic）
dpkg -l | grep -E '^ii.*linux-image'       # 已装内核（可能同时有 6.8 与 7.0 两份）
apt list --installed 2>/dev/null | grep linux-generic-hwe
systemctl get-default                      # 默认 boot target
lsb_release -ds; grep VERSION_ID /etc/os-release
```

本机实测：**Ubuntu 24.04.5 LTS 跑着 7.0.0-34 内核**——因为走的是 **HWE（Hardware Enablement）内核**。`linux-generic-hwe-24.04` 把 LTS 的内核一路推到新硬件代次，**不用升发行版就拿到新内核**。

**代价实录**：小喵拿「24.04 = 内核 6.8」的刻板印象讲了一整套「升 26.04 能拿到内核 7.0 的收益（新调度器 / UDP 重写 / XFS 自愈）」，主人当场打回「我现在不就是 7.0 内核吗？」——**整个论述的前提是错的**。这是「不核验就断言」的典型，和 mechanism-claim-discipline 同源。

## 厂商栈可能已超前于目标发行版（增量可能为负）

**别默认「新发行版 = 更新的驱动/计算栈」。** 走厂商官方仓库（AMD/ROCm、NVIDIA CUDA）的机器，图形与计算栈常常已经跑在发行版发布节奏前面。升级发行版反而可能把它拉回标准版 = **降级**。

动手前量当前栈，与目标发行版标准版对照：
```bash
# GPU 硬件
dpkg -l | grep -iE '^ii.*mesa'                       # 双 Mesa？发行版版 + 厂商版并存
lspci -nn | grep -iE 'vga|3d|display'
which vulkaninfo && vulkaninfo --summary | grep -A5 GPU0   # driverVersion = 实际在用的 Mesa？
# ROCm / HIP
dpkg -l | grep -iE 'rocm|hip|amdgpu' | head
dkms status                                          # 厂商 DKMS 覆盖了哪些内核
hipconfig --version 2>/dev/null
ls /etc/apt/sources.list.d/ | grep -iE 'rocm|amdgpu'  # 厂商源开着吗（Enabled: yes/no）
```

本机实测：装了两套 Mesa——发行版 **25.2.8**（默认路径）与 AMD 专有 **26.1.3**。`vulkaninfo` 报 driverVersion 25.2.8 = 实际在用发行版那套。ROCm **10.0**（AMD 官方 stable 源）、`amdgpu-dkms 7.1.3`（自编译内核模块，覆盖 6.8/7.0 多个内核）。**26.04 标准版是 Mesa 26.0**——比本机专有栈的 26.1.3 还旧。结论：升 26.04 的图形栈收益 ≈ 0，且有降级风险。

**顺带查 `.distUpgrade` / `.dpkg-dist` 残留**（`ls /etc/apt/sources.list.d/`）：这些是升级工具留下的痕迹，说明该栈以前经历过升级冲突。再叠一次发行版升级风险不小。

## AMD GPU 有内核级性能回退史（ROCm 计算负载）

Ubuntu 内核团队会对 **AMDGPU 计算回退**发预警（实证：某 7.0.x 内核点版本在 ROCm 计算密集负载下慢到 **42×**，根因是 AMDGPU HMM 代码的重试循环，上游已修但 Ubuntu 因发布时序仍推了坏版本，官方建议 ROCm 用户避开该点版本）。

**对推理机（尤其跑 ROCm 的）的含义**：HWE 内核每个点版本都要留意 AMD/ROCm 回退——**与升不升发行版无关**。是 HWE 路线本身的风险。升级决策里要把这条算进去：升到新发行版会换整套内核-驱动协同版本，进入活跃战场。

## 升级的真实成本（违 LTS 的坑）

LTS→LTS 不是「换几个包」。实证升级（24.04.4 → 26.04.1）会替换底层栈：

| 组件 | 24.04 | 26.04 | 对推理机的冲击 |
|---|---|---|---|
| 内核 | 6.8 | 7.0（你 HWE 已有） | — |
| Python | 3.12 | **3.14** | **所有 venv 断**（解释器符号链接指 3.14，包仍在 3.12/site-packages，第三方 import 全挂）——升级前 `pip freeze` 备份每个 venv |
| systemd | 255 | 259 | `isolate` 行为可能变 → 重新验证 headless/gui 切模式脚本 |
| sudo | sudo (C) | **sudo-rs (Rust)** | 脚本对 sudo 边角行为的依赖可能出意外 |
| coreutils | GNU | **uutils (Rust)** | 同上 |
| OpenSSH | 9.6 | 10.2 | 远程访问前想好兜底 |

**第三方 deb 源是升级崩掉的第一大原因**：升级工具会给所有非 Ubuntu 源加 `Enabled: no`，且**事后不帮你打开**。升级前先禁用 PPA / Docker / 厂商源。升级后确认目标源有目标发行版的 suite，再逐个改回。

## 交付纪律

给「要不要升」的建议前，至少核完四件：
1. **活体内核版本**（`uname -r`）——别推。
2. **图形/计算栈当前版本**（Mesa / ROCm / DKMS）——与目标发行版标准版对照，判断增量符号。
3. **推理服务的直接受益证据**——「内核升级让推理快 X%」这类断言要实测支撑。没有就诚实说「我没搜到直接证据」，收益主要在桌面/图形栈，不在推理主业务。
4. **代价清单**——venv 断裂、systemd 行为变、厂商源重配、AMD 回退史。

结论按「收益落在哪、风险落在哪」分开写，交主人拍板。生产机升级前先克隆演练（官方与实测源都这么建议）。升级后第一件事是验证推理服务能起来 + venv 是否重建 + 切模式脚本是否还正常。
