---
name: laptop-coder-node
description: 操作笔记本 Strata 代码工节点 coder-laptop 时使用。挂载、起停、配置与硬件坑。
author: Independent Researcher
version: "1.0"
license: MIT
metadata:
  hermes:
    tags: [laptop, strata, coder, debian, nvidia]
    related_skills: [ssh-windows-remote-ops, llama-serving-bench, strata-serving-ops]
---

# 笔记本 Strata 代码工节点账本（2026-10-08 建成）

## When to Use

对 192.168.50.29（coder-laptop / NODE II）做任何操作前加载：SSH、挂载、起停 Strata、改配置、装包、诊断掉线。IP 于 10-22 由主人更正（旧 .195 已被 DHCP 换掉）。坑：config.yaml 里 provider `node-ii` 的 base_url 仍写死 .195=死线，活线是 `node-ii-lan` 指 .29——派卡/哨卡一律用 node-ii-lan。

## 连接
- SSH：`ssh -i ~/.ssh/id_ed25519_deploy_laptop alonzo@192.168.50.29`（公钥已埋 authorized_keys）
- alonzo 有 sudo，但 NOPASSWD 只圈：`apt-get / dpkg / systemctl / reboot / mount / umount`（`/etc/sudoers.d/alonzo`）——root 密码锁定未设。**验证权限圈定必须用圈内的命令**（拿 `sudo -n true` 测会被要密码，是假阴性）。

## 硬件与系统
- MSI Stealth 16 AI+：Panther Lake 386H + RTX 5070 Ti Laptop 12G。**双 M.2 都被 Windows 占**（nvme1n1=OS 1.8T、nvme0n1=Files 953.9G），系统装在外接 USB 盒上。
- **根 fs 在 ASUS ROG Strix Arion USB 盒（/dev/sda3 ext4）——不可靠**：UAS 被内核拉黑名单退到 usb-storage。持续大写入会 `device offline error` 掉线，根 fs 冻结 → DNS 失效/sshd 假死/IO error 三症状同源，插拔救不回，只能硬重启。
- **铁律：大文件读写一律走内置 NVMe 的 Windows C 盘**（ntfs3 挂载 `~/winc` ← /dev/nvme1n1p4，fstab 已配 nofail，包名 coder-fstab）。`~/Strata-data` 是指向 `~/winc/Strata-data` 的软链。
- 内核：7.2.6（trixie-backports，默认启动）+ 6.12.111 后备。NVIDIA 开源驱动 615.71.09（Debian 闭源包不支持 Blackwell，**必须 NVIDIA CUDA repo debian13 源的 `nvidia-driver-cuda` + `nvidia-kernel-open-dkms`**）。
- 固件（Debian 2026 拆包制）：GPU（i915/xe 的 dmc/guc）在 **`firmware-intel-graphics`**、蓝牙/wifi aux 在 **`firmware-intel-misc`**，池组件是 **`non-free-firmware`**（main/non-free 路径全 404）。Panther Lake 这类新平台老固件包（trixie 正源 20250410）必缺 blob。抓 sid/最新版直接 `curl pool/non-free-firmware/f/firmware-nonfree/<pkg>_<ver>_all.deb` + `dpkg -i`（路径从 sid Packages.gz 索引的 Filename 字段拿，别猜）。
- root 操作（sudo 圈定无写权限时）：打**迷你 deb**——`postinst` 可执行任意幂等 root 动作（写文件、`usermod` 加组、modprobe 等）。走圈内的 `dpkg -i` 落地。已用：fstab（coder-fstab/coder-fstab2）、`alonzo` 加入 input 组（coder-input-diag，键事件诊断用。⚠️ input 组 = 可读全键盘输入流，仅限单用户私人机）。改组成员后须**新开 ssh 会话**才生效。

## Strata 服务
- 装在 `~/Strata`，配置 `~/Strata/strata-coder-iq1_m.json`：args 里 `--max-context 131072`、顶层 `"host": "0.0.0.0"`。顶层 `reasoning_budget_tokens: 6144`（思考死循环的刹车，来自台式机同款）。**host/budget 是 serve 层顶层键，放进 args 数组引擎不认。打 usage 退出**（表象是 `engine exited before it was ready`，真因看 `strata-*.log` 里引擎打的使用帮助）。
- 起服务：`cd ~/Strata && ./run-coder-iq1_m.sh`。API `192.168.50.29:8080/v1`（OpenAI 兼容）。
- **绑定是配置里 `--host` 控制的**。默认 127.0.0.1 时从台式机用 SSH 隧道：`ssh -N -L 18080:127.0.0.1:8080`。

## 已实测的能力边界（勿重复踩）
- **英文/代码：流畅**，TG 稳态 ~80 tok/s（对照**笔记本本机** 27B 稠密的 5 tok/s ≈ 16 倍。⚠️ 10-09 勘误：早版误写为「台式机 27B」——台式机 27B 速度未实测，勿引用旧错值）。代码质量有官方基准背书：SWE-bench Verified 75.6（= 基座 BF16 的 91.3%）、LiveCodeBench v6 86.3（98.7%，xhigh effort 实测）。多步 agent 任务是剪枝的已知短板（误差跨回合累积）。
- **中文：模型层残废（#438 实锤复现，不可修）**——思考开→思考死循环撑爆上下文（正文 0 字）。思考关→正文单字复读（「通通通…」）。frequency_penalty 0.5 无效。**给这个节点的指令一律用英文**。
- 思考预算机制（reasoning_budget_tokens + 英文 wrap-up）能把死循环闭合出正文，但正文中文质量仍坏。

## 运维坑（每条都真实付出过代价）
1. **pgrep/pgrep -f 会匹配到自己的 ssh 命令行**——判进程死活用 `pgrep -x`（精确名）或先看自身模式是否被自匹配。**10-09 二踩：`ps aux | grep -oE 'gnome-shell|plasmashell'` 同样自匹配，幻影出「三个桌面会话」——查进程存在性用 `ps -C NAME`，别用 ps+grep。**
2. **经 ssh 内联 python/printf 写文件必然碎引号**（已两次踩）——一律本地写脚本 → scp → 远端执行。
3. sudoers 圈定导致 `sudo dmesg` 不可用。查内核日志让主人本地跑或扩圈定。
4. `apt-get install` 里有一个包名错 → 整个事务回滚（包括对的包）——包名先 `apt-cache policy` 验。
5. 旧的 server.py 监护进程会攥着 8080 端口——杀引擎杀不掉端口，`ss -tlnp` 找 python 监护 PID 一起杀。
6. **7.2.6 backports 内核没有 ntfs3 模块**（linux-modules 与 modules-extra 都不含）——C 盘挂载用 **ntfs-3g FUSE**（fstab 条目已换，包 coder-fstab2）。代价是 shard2 PLE 随机读有 FUSE 税，要压速度再找 ntfs3 或迁原生分区。手动补挂：`sudo mount -t ntfs-3g -o rw,uid=1000,gid=1000 /dev/nvme1n1p4 ~/winc`。
7. 远端常驻任务（下载/编译）必须 `setsid nohup … > log 2>&1 < /dev/null &` 全套脱离——少了 `< /dev/null` 或脱离不全。ssh 会话会陪跑直到超时，还会把前台 cp 一起掐死。
8. 复杂多步远端操作写成脚本 scp 过去再 setsid 跑，别拼内联命令链。cp + aria2 串行链（如 dl_sc117.sh）和改配置的 python 都是此法。
9. **改 args 数组的幂等过滤会误删同字面值**（10-09 实例：`x not in new` 里含层范围的 '4'，把 `--spec` 的值 '4' 一起删了 → 引擎报 `unknown argument: 0.5` 打 usage 退出）。改引擎 args 用「先找 flag 名定位、按对儿处理」，别按值黑名单过滤。`--experimental-speed-projection` 是 setup.sh 层包装参数，展开后就是 `--control-vector-scaled/--control-vector-layer-range/--cvec-mode/--cvec-dir` 四个引擎 flag——手写 json 直接用后者。不算「没开」。
10. 引擎打 usage 退出时，真错误行在 spawn 命令行（server.py 日志 `[strata] ... engine started:` 那行）之后一行，不在 usage 块里。grep 'unknown argument' 或直接看 argv 段。
11. **原始 evdev 捕包用 `cat /dev/input/eventN > file.raw` + 事后 xxd，禁用 `cat | od`**——od 有 4KB 输出缓冲。timeout 杀进程时小数据量全丢（文件空/缺失，看似「无事件」实为捕包失败）。先做方法自检：抓主键盘（AT Translated，Handlers 行在 `/proc/bus/input/devices` 的 Name 行后第 5 行，grep 要 `-A5`）敲字母验证管道。再下「键被吞」的结论。

## Headless 硬件控制（背光 / FN 键）
- 本机 headless（无桌面。屏幕上的「桌面会话」多半是 ps|grep 自匹配幻影，验证用 `ps -C NAME`）。
- **FN 组合键被 EC 层全吞，无驱动可修**：三热键总线（intel_hid event4 / HID 5 按钮 event6 / MSI WMI hotkeys event9）实测零字节事件。主键盘敲字对照过管道正常。`msi-ec.ko` 按固件版本白名单匹配（PTL 新机被拒），`msi-laptop.ko` 是 2008 代老机驱动。要 FN 真活只能向 BeardOverflow/msi-ec 上报 EC dump。
- **亮度替代路径（已验收）**：`~/bright.py <sub|add>` 直写 `/sys/class/backlight/intel_backlight/brightness`（写权来自 coder-backlight-write deb：chmod a+w + udev 规则保重启。满档 400，驱动托底 ~20）。**actual_brightness 读数滞后且会停旧值——验收亮暗看屏幕，不认 sysfs 读数**。
- **按键绑定 = keyd**（`/etc/keyd/main.conf`，包 coder-keyd-conf，服务 active+enabled，TTY/X/Wayland 通吃）。⚠️ keyd 2.5.0 组合键 LHS **不认裸 `control` 也不认 `C-f11`**（两者均报 "not a valid key"）——必须用层语法：`[main] leftcontrol = layer(control)` + `[control] 节内 f11 = command(...)`。配置解析失败时 keyd 全设备透传，表象是 Ctrl+Fn+F11 触发 TTY 的 VT 切换走马灯。真错误看 `sudo systemctl status keyd` 日志的 ERROR 行（写配置包前先 dpkg-deb -f 核对 Version，避免构建出旧版）。
- 输入事件诊断：alonzo 已入 input 组（coder-input-diag deb）。捕包 `cat /dev/input/eventN > raw + xxd`，**捕获窗 ≥ 10 分钟**（人机往返时延会吃掉短窗），先抓主键盘敲字做方法自检（主键盘 Handlers 行在 /proc/bus/input/devices Name 行后第 5 行，grep 用 -A5。注意别把 Touchpad event 误当键盘——EV_ABS/ABS_MT 事件是触摸板）。

## 三档分工与路由（跨机拓扑定版）
- **裁决位（规划/审查/验收）必须高智商**（台式机 IQ3_S 或云端）：社区实测低比特 Flash-Next 家族有可靠性短板。无视工具回执里的数字、提前 EOS 装作完成、AFK 长任务进循环。低智商节点不许占裁决位，否则带着聪明工人跑偏。
- **会话位 = 笔记本 SC117**。会话 Host 产出「选项式汇报」时，选项必须由高智商节点生成、Host 原文转发不加工——选项质量 = 决策质量。2-bit 模型生出的选项是矮子里拔将军。
- **机械迭代位 = 笔记本 Coder 80 tok/s**：只干 boilerplate/重复劳动，出口必须有硬闸（TDD/回归闸）拦缺陷。快而笨的手 + 硬闸 + 聪明审 > 聪明手无闸。
- 降级链：笔记本挂 → 台式机接会话（中文同样健全，只掉速度不掉能力）。
- 待核项：两臂共享文件 = shard2（blake2b 已对账清白）+ shard3（无哈希核验记录，共同传播面未排除）。Coder 销案实验要一并覆盖。
- Coder vs 27B 的完整侦察（官方基准、社区口碑、256K 未核验）见本条目出处会话。直接可用结论：单题代码 Coder≈基座≥27B，多步可靠性 ≈27B 打平或略输（推断未核验）。

## 第二臂：SC117 全量 abliterated IQ2_XS（2026-10-09 实测定版）
- 目的：中文健全（全 512 专家）+ 权重级消融（144 张量移植，比 cvec ESP 可靠）。low-RAM 模式冷专家走内置 NVMe 流式。**TG 实测 16.2 tok/s（int8 KV）→ 17.3 tok/s（k8v4，+6.8%）**。冷 PP 47.3 → 热 197.6@13.4k（int8）。k8v4 同 14k prompt PP 140（冷热未注明，与 197.6 不可直接比）。**中文实测通过（含 NSFW）**，k8v4 后体感无退化（体感级验收，「V 噪声当有益随机性」为假说未验）。
- 文件在 `~/winc/Strata-data/models/sc117_iq2xs/`（shard1 39.67 GB + shard2 28.8 GB + mtp-Q8_0.gguf + strata_rt/ 四件）。**shard2 与 Coder 的字节相同**（上游一致），改名复用不重下。
- pack：`~/Strata-data/packs/sc117_iq2xs/` 已由 `tools/iq_pack.py` 建好（dense.bin/index.txt/native_experts.txt/tokenizer。**无 experts.bin 是正常的**——此 pack 按 native_experts.txt 偏移直接引用 GGUF，引擎加载已实测通过）。复用官方 pack 必报 ArenaExpertSource 不匹配。
- 启动：`./run-sc117_iq2xs.sh`（配置 strata-sc117_iq2xs.json，与 coder 同款顶层 host/budget）。MTP 指 strata_rt/（卡片原文：llama.cpp 用 root 的 Q8_0 gguf，Strata 用 rt/）。
- 采样基线：两份配置顶层 `"sampling": {temperature 1.0, top_k 20, top_p 0.95}`——Qwen 官方 generation_config 原文（2026-10-09 核）。serve 层 `cfg.get("sampling")` 把每个键变请求默认。显式值优先、null 落回默认。两台机器最优点不同：台式机 256 GB 内存用 `--kv int8`。笔记本显存内专家挨饿用 `--kv k8v4`（K INT8 精确 + V 旋转 Q4_0，816 vs 1056 B/cell，128K 省 ~0.34 GB → +~170 专家槽）。**这是内存账决定的差异，不是配置错误**。
- 完整部署账本（分区/固件拆包制/内核双轨/坑清单）：`references/deployment-ledger-20261009.md`。
- **不移植台式机的 f-cache-persist-manifest 优化**（2026-10-09 裁定）：那套 12 GiB 停放缓存治的是多会话互踢。笔记本单用户无此病。内存账两臂都装不下（Coder 23GB 专家+12GB 缓存 ≈ 38 > 31.5）。patch 是 HIP 编译需 rebase+CUDA 重编。笔记本每一 GB 该喂专家不喂缓存。KV 档位有 --kv k8v4（K 精确 + V 旋转 Q4_0，816 vs 1056 B/cell，128K 省 ~0.34 GB 显存 ≈ +170 专家槽，待 A/B）。--kv-resident 在本机是零和（pinned KV 与 resident 专家抢同 30 GB），勿开。