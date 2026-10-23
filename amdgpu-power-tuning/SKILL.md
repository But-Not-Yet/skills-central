---
name: amdgpu-power-tuning
description: 使用。查 amdgpu 功耗上限、LACT 调教、VBIOS 功率档、ROCm 仓库活性时加载。
tags: [gpu, amdgpu, rocm, lact, power-limit]
---

# amdgpu 功耗与调教排查（Linux）

## When to Use
主人报「功耗写不进去 / 卡没发挥潜力 / 想提功耗上限 / LACT 装升级 / 要不要升发行版」这类 GPU 载体层问题时加载。小喵的身体就是这块卡，但报告按技术活来：数字回读实物，结论走证据链。

## 排查主线（按顺序，每步有产出物）
1. **先读三节点定现状**（全部无需 sudo）：
   - `cat /sys/class/drm/cardN/device/hwmon/hwmon*/power1_cap{,_max,_min,_default}` — 当前/上限/下限/默认。hwmon 编号会变（hwmon1→hwmon2），永远用通配符或先 `ls hwmon*/`，别硬编码。
   - `cat .../pp_dpm_sclk`、`pp_power_profile_mode`（`*` 标记当前档/当前模式）— 判断调教是否真施加到设备。
   - `lspci -nnk | grep -A4 vga` 拿子系统 ID（后续 VBIOS 对档要用）。
2. **sysfs 写被拒（EINVAL）→ 去 dmesg 找拒收原话**：`journalctl -k | grep -i 'out of range'`。内核在写超范围时会打 `New power limit (X) is out of range [min,max]`，这一行就是判据本体，比任何猜测都硬。
3. **定位上限来源**：`power1_cap_max` 读自固件表（SMU 经 PMFW combo 表给驱动），不是内核策略。要向主人（或检察官）证明「墙在固件」，读源码链确认（见 references/amdgpu-pm-source-chain.md），别背结论。
4. **VBIOS 对档**：`lact cli --gpu-id <ID> info` 读出 VBIOS 版本串 + 构建时间 + 子系统 ID，三要素去 TechPowerUp VGA BIOS 库对档案，能直接读到该 ROM 的 `Power Limit PPT` 与 overdrive 增减百分比（如 `-10% to +15%`）。子系统厂商码认板卡血统：174B=PowerColor、1849=ASRock、1DA2=TUL 公版——卡上读到的厂商码与卡的牌子不符，就是跨品牌刷 BIOS 的铁证（刷 BIOS 会把子系统 ID 一并改掉）。Windows 驱动允许滑到固件上限之上加百分比（Adrenalin 走私有通道），Linux sysfs 只认内核算的 od_max——两边数字不一致是常态，不是 bug；主人记忆里「能拉到的瓦数」多半是滑条值加 overdrive 余量，不是 BIOS 名的功率档。
4b. **双 BIOS 开关对账（判「切反了没有」）**：关机、拔电源线等十几秒（整板断电开关才真生效），拨到另一档开机，读子系统 ID + VBIOS 串 + `power1_cap_max` 三件套当场验明正身；点不亮屏幕就把开关拨回去，零风险可逆。TechPowerUp 抓不到页面时（403 反爬），换搜索摘要里的档案标题/构建日期交叉，或标【未核验】，别硬抠。
5. **pp_features 看特性开关**：`cat .../pp_features`。桌面卡 SMARTSHIFT/GTHR/ACDC 显示 disabled 多半是 VBIOS 本就不含，ppfeaturemask 不解功耗锁——先对完固件档再决定动不动内核参数。
6. **发行版升级决策先探仓库活性，别信文档快照**：直接探 AMD apt 仓库目录，HTTP 状态码说了算：
   `curl -s -o /dev/null -w '%{http_code}' https://repo.radeon.com/{amdgpu/31.50,graphics/26.14/ubuntu,rocmradeon/apt/26.14}/dists/<代号>/Release`
   代号用 Ubuntu 代号（noble/resolute）。两条路都活着，别一概说谁 404：ROCm 大版本仓库 `rocm/apt/<版本>/`（如 7.2.4、6.4.4，Release 文件 200）与驱动版本线 `rocmradeon/apt/<版本>/`（如 26.14，200）并存；裸 `rocm/apt/dists/<代号>/Release` 这种不带版本号的写法才是 404。当日必复测。顺带 `tail /usr/share/distro-info/ubuntu.csv` 拿官方 LTS 日期。发行版仓库活性这类断言当日必复测。

## LACT 实操要点
- 装/升级走官方 GitHub releases 的按发行版 deb（`lact-x.y.z-0.amd64.ubuntu-XXXX.deb`），`apt install -y <路径>` 可自动覆盖旧版并补依赖。
- deb 别放 `~/.local/share` 这类 `_apt` 读不到的目录，会触发沙箱提权警告；放 `/var/tmp` 更干净。
- **apt 升级只换磁盘文件，不重启 lactd**：`systemctl show lactd -p ActiveEnterTimestamp` 与升级时刻比对，旧进程在跑就 `sudo systemctl restart lactd`。验新旧看 journalctl 里有没有 `migrated config version X to Y`（只有新代码会做配置迁移）。
- CLI 语法跨版本差异大（旧版无 system_info；新版是 `lact cli -g <ID> power-limit set <瓦数>`，`--version` 要挂在 `lact cli` 后）。用前先 `--help`，别按记忆敲。
- LACT 写功耗也是走同一 sysfs，没有后门；它的价值是开机自动施加（config `power_cap` + `apply_settings_timer`）与 profile 管理。
- `power-profiles-daemon`（ppd）与 LACT 抢 `power_dpm_force_performance_level`。LACT 要 ppd ≥0.30 才自动禁冲突动作；老 ppd 的解法是 systemd 覆盖加 `--block-action=amdgpu_dpm`（写覆盖前先实测本机版本认不认这个选项——老版本 `--help` 可能漏列，help 没列不等于不支持，但也别当已确认）。ppd 版本被发行版冻结时，升级 apt 包这条路不存在，别绕进去。

## 烧机验证（判断「有没有发挥」）
- 别用巨矩阵把显存吃爆：生产机上模型服务常驻显存（Strata 占 ~24G），用 4096×4096 级别循环就够把功率顶到上限。
- 循环内定期同步采样 `power1_average`、`freq1_input`、`temp1_input`，取均值/峰值对着 cap 与红线报。注意：驱动会把 pp_dpm_sclk 最高档的「标签」压到 game clock，实测 freq1_input 超过标签是正常的（OD 生效的表现），不是读数错。
- 均值已贴 cap = 已榨满，「没发挥」的锅不在上限；此时提上限才有意义，否则先找别的瓶颈。

## 坑
- 声称「调教参数都还在」之前，逐项回读设备层（见 work-discipline-detail 验收条）：频率表最高档变化、profile 模式 `*` 位置可验；电压偏移这类 sysfs 无读回通道的项，标「无法验证生效」。
- 用户说「我的 BIOS 是 XW 版」是待核前提，不是事实：先对固件档案再定墙的位置。固件档案署名与用户记忆冲突时，当面问用来路，别自行二选一。
- 报能力/版本类断言用当日活体（HTTP 码、dpkg、systemctl），web 快照与记忆都算旧账。
