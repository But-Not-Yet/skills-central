---
name: ssh-windows-remote-ops
description: "通过 SSH 驱动 Windows 主机时使用。传文件、起长任务、输出编码三类陷阱在此处高频，先加载再动手。"
version: 1.0.0
author: Nekonya
license: MIT
metadata:
  hermes:
    tags: [ssh, windows, remote-ops, scp, schtasks, encoding]
---

# SSH 驱动 Windows 主机

在远程 Windows 上跑命令、传文件、起长任务时的固定做法与陷阱。
（.bat 自身的 CRLF / 编码问题另见 `windows-bat-editing`。）

## 何时使用

动作经过 SSH 落到 Windows 主机上时——传文件、跑脚本、起服务、起长任务。
下面六条都是「不问就踩、踩了才知道」的类型，而且症状多半指向错误的方向
（空返回像文件不存在、静默失败像代码写坏了）。

## 1. 传文件：用 scp，不要把内容塞进命令行

**Windows 命令行上限 8191 字符。** 把文件 base64 后拼进 ssh 命令行，超过就失败——
若同时吞掉了 stderr（`>/dev/null 2>&1`），症状是「命令返回 0，但文件没变」，
看起来像写入逻辑坏了。**先看 stderr，别先怀疑自己的代码。**

```bash
scp -o ConnectTimeout=10 -o BatchMode=yes -o IdentitiesOnly=yes \
    -i ~/.ssh/<key> local.py "User@host:D:/path/"
```

远程路径用 `User@host:D:/path/` 形式。短文件用 base64 亦可，但要有长度意识。

**传完两边对哈希**，不要假设「写成功」：本地 `sha256sum`，远端
`powershell -NoProfile -Command "(Get-FileHash '<路径>' -Algorithm SHA256).Hash.ToLower()"`。

## 2. 长任务与常驻服务：用 schtasks，不要 Start-Process

**SSH 拉起的子进程挂在会话的 job object 上，SSH 一断，整个进程树被一起清理。**
症状是任务「刚起来就没了」，或你先看到它在响应、过一会儿再查发现它死了。

**这条同样管「起服务 / 常驻进程」**——不限于批处理作业。模型服务、看门狗、监听器都算在这里。

### 最坑的是它会间歇性成功

`Start-Process -WindowStyle Hidden -PassThru` 有时拉起来的进程**真的活下来了**，于是你以为方法通了；换个时刻同一写法当场就死。结果是「失败 → 重试 → 偶尔成功 → 再失败」的循环，白烧很久，
还会把「进程死了」误归因成别的（脚本写错、显存不够、模型加载失败）。

**看到「同一写法时灵时不灵」，先换机制，不要重试。** 这是 job object 回收的随机性，不是你的脚本坏了。

### 退路：让用户从桌面双击

交互会话里启动的进程不受 SSH 的 job object 管辖。摸到路后直接请用户双击启动，
并提醒他**别关那个窗口**（关了服务就停）。这比继续折腾分离启动快得多。

### launcher .ps1 要参数化

把目标 .bat 路径当参数传（`-File launch.ps1 -Target <bat>`），不要给每个 .bat 复制一份 .ps1——
否则目标一变就得同步改 N 个文件，改漏一个就跑到旧目标上，而**症状是「启动成功但跑的是旧配置」**，
极难发现。

做法：写一个 .bat 把输出重定向到日志，交给计划任务跑：

```bat
@echo off
cd /d D:\path
set PYTHONIOENCODING=utf-8
D:\path\.venv\Scripts\python.exe D:\path\job.py >> D:\path\job.log 2>&1
```

```
schtasks /create /tn <名> /tr "D:\path\run_job.bat" /sc once /st 23:59 /f
schtasks /run /tn <名>
```

之后轮询日志文件；用完 `schtasks /delete /tn <名> /f` 清理——**测试任务用完即删**：`/sc once /st 23:59` 的触发器到点会自己开火（忘删等于定时炸弹）。

**回显成功 ≠ 已执行。** `schtasks /create`、`/run` 的「成功」字样、WMI `Invoke-CimMethod` 返回的 PID，都只证明「创建/尝试」发生，不证明脚本真的跑了——见过回显全部成功、产物始终不落盘的案例（原因未定位）。**判执行的唯一证据是产物**：日志文件、进程表、端口。给一个几十秒的观察窗仍无产物：把结论钉成「未执行，原因未定位」，**不要无限换机制**，直接转上面的「请用户双击」退路。

**长任务必须自己增量落盘**：每个单元跑完写一次结果文件，并支持跳过已完成的续跑。
否则会话一断或任务一停，全部结果丢掉。

## 3. 输出编码

Windows 控制台默认 **GBK**。Python 打印非 GBK 字符（emoji、✅❌、部分符号）会
`UnicodeEncodeError` 直接中断脚本。

- 设 `$env:PYTHONIOENCODING='utf-8'`（PowerShell）或 `set PYTHONIOENCODING=utf-8`（bat）
- **脚本里仍然不要用 emoji**——环境量不是每条调用路径都传得到；写 `PASS` / `FAIL` 更稳
- 回显中文乱码只是显示层问题，**不影响文件内容**。判文件内容用计数或哈希，不看回显

**从 PowerShell 重定向到文件（`cmd > out.txt`）写的是 UTF-16LE（带 BOM）。** 文件看着正常，
但把 `--help` / 日志这样拉回 Linux 后，**做纯字节匹配的工具搜 ASCII 字符串零命中**——
每个字符之间夹着 `\x00`，文件大小约为文本的两倍。症状是「命令成功、文件非空、就是搜不到」，
很容易误判成命令没输出。（少数 BOM 敏感的工具会自动转码而看不出问题，所以别拿「我能搜到」
去否定这个坑：换一个工具结论就反。）

```bash
iconv -f UTF-16LE -t UTF-8 out.txt > out.utf8.txt   # 读之前先转码，后续工具都不用挑
```

不如在远程侧就指定编码：`... | Out-File -Encoding utf8 out.txt`，
或用 `[IO.File]::WriteAllText('D:\out.txt', $text)`。

## 4. 调本机程序

- **用绝对路径**调解释器（`D:\...\.venv\Scripts\python.exe`），不依赖 PATH
- `python -c "..."` 的嵌套引号经 cmd 会被吃掉，症状是
  `SyntaxError: unterminated string literal`。**写成脚本文件传过去**，别在命令行里塞代码
- 脚本接收的路径参数同样用绝对路径

### 4b. 传 `.ps1` 时：**UTF-8 无 BOM 会被当成 GBK 读**

自己在 Linux 上写好的 `.ps1` 传过去，**含中文就解析失败**：

```
表达式或语句中包含意外的标记“)”
字符串缺少终止符
MissingVariableNameAfterForeach
```

根因不是语法错，是 **PowerShell 5 默认按 ANSI/GBK 读无 BOM 的 .ps1**，
多字节字符被拆坏后引号配对被破坏。**注意：这和“控制台回显乱码”不同——
回显乱码只是显示层，这个会让脚本压根跑不起来。**

两条都要做：

```python
# 1) 内容里不写非 ASCII —— 输出串全用英文（PASS / FAIL / DELETED）
# 2) 传之前转 CRLF
import io
raw = open('x.ps1','rb').read().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
open('x_crlf.ps1','wb').write(raw)
```

然后用 `-File` 跑（不要用 `-Command` 拼）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\path\x.ps1 -DryRun
```

**同一限制也适用于将复杂 PowerShell 直写在 ssh 命令行里的情形**：`\$_`、`\$d`
这类转义会被 ssh → cmd → powershell 三层剥掉，症状是 `ParserError: MissingVariableNameAfterForeach`。
**含变量、循环、`$_` 的一律改走「写 .ps1 → scp → -File 执行」；无变量的单行 PS 可以直接内联**——外层 bash 双引号 + PowerShell 段用 `\"` 转义 + 内部参数一律用单引号。（实测稳定的形状：`Get-FileHash` 单文件哈希、`Get-CimInstance -Filter 'ProcessId=…'`、`Get-WinEvent -FilterHashtable @{…}` 都是一层内联跑通的。）

**内联 PS 的参数值含空格必须单引号包住**：`Select-String -Pattern A gen,B gen`（逗号分隔且含空格）经三层剥引号后变成位置参数，报 `PositionalParameterNotFound`——看着像 PS 语法病，实为剥引号。写 `-Pattern 'A gen','B gen'`。同理 `findstr` 的 `/i "a b"` 形状在 ssh 单引号段里只剩外层双引号可用，包不住就改走 PS。

**删除/批量删除类脚本先带 `-DryRun` 开关跑一遍**：先打印命中清单与分类计数，
确认无误再真删。另外，**按同一个词根写模式极易漏族**（实测：
`dbg_diff_*` 删完后又跑出 `v2diff_*`、`v2log_*`、`v2raw_*` 三族）——
先 `Get-ChildItem | Group-Object { ... }` 按词根聚类看全谱，再写模式。

## 5. SSH 别名可能指向不可达地址

网络环境切换（VPN ↔ 局域网）后，ssh config 里的 `HostName` 可能仍指向旧地址。
**症状是命令返回空**——不是报错，是空，很容易误判成「文件/目录不存在」。

- 连不上先探连通性确认该走哪条路：`ping -c2 -W2 <ip>`
- **不要改用户的 ssh config**：改错了，他下次换网络时更难查
- 会话内做一个带显式地址的封装脚本（`exec ssh -o … User@<ip> "$@"`），后续命令都用它

## 6. 状态断言纪律

状态类断言（服务在跑吗、任务完成吗）**开口前先查活体**：进程表、端口监听、
健康端点、资源占用。并**区分「在响应」与「可用」**——健康端点返回加载中（如 503）
只说明进程活着，不代表它能干活。

**快照会过期。** 报「好了」之前，在任务**该完成的时刻**再查一次；
别拿一次中途成功的探活当终态。

**回显不是事实、前提先取证。** 命令自己报「成功」不等于世界变了（见第 2 节）；「已重启 / 已生效」这类**实验前提**先核证据再下分支结论——凭推测会把分支判错（例：判定「重启后仍复现」，一查开机时间，机器根本没重启过）。

**只读取证速查**（单行 PS 内联的形状见 4b）：
- 开机时间：`(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToString()`（本机无 `wmic`，别用）
- 进程真实命令行（服务实际吃的参数，与启动脚本互证）：`(Get-CimInstance Win32_Process -Filter 'ProcessId=<PID>').CommandLine`
- 崩溃取证（进程崩了、窗口输出拿不到时）：`Get-WinEvent -FilterHashtable @{LogName='Application'; Id=1000; StartTime=(Get-Date).AddMinutes(-15)} -MaxEvents 1 | Format-List TimeCreated,Message`——给故障模块与异常码（`0xc0000409` = 快速失败）
- GPU 残留：`nvidia-smi --query-gpu=name,memory.used,utilization.gpu,temperature.gpu --format=csv`
- 谁在机器旁：`quser`（交互会话与空闲时长）
