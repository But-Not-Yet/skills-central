---
name: ssh-windows-remote-ops
description: 动作经 SSH 落到 Windows 主机上时先加载再动手：传文件、跑脚本、起长任务、远程 webui 备素材、编码回显。陷阱集中在四处且症状大多指向错误方向（空返回像文件不存在、静默失败像代码写坏），不问就踩。
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

动作经 SSH 落到 Windows 主机上时用这套做法。传文件、跑脚本、起服务、起长任务都算。
下面六条都是「不问就踩、踩了才知道」的类型，
症状还多半指向错误的方向：空返回像文件不存在，静默失败像代码写坏了。

## 1. 传文件：用 scp，不要把内容塞进命令行

**Windows 命令行上限 8191 字符。** 文件 base64 后拼进 ssh 命令行，超过就会失败。
若同时吞掉了 stderr（`>/dev/null 2>&1`），症状是「命令返回 0，但文件没变」。
看起来像写入逻辑坏了。**先看 stderr，别先怀疑自己的代码。**

**scp 目标目录不存在时会造出一个同名文件**：`scp x.py host:D:/new/dir/` 里 `dir` 不存在时，远端出现的是一整个名为「dir」的文件，之后往这「目录」里传的每件东西都砸在这个文件上。首个 scp 前先 `mkdir D:\new\dir`（或先放 `dir /b` 验目录真的存在）。

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

**这条同样管「起服务 / 常驻进程」，不限于批处理作业。** 模型服务、看门狗、监听器都算在这里。

### 最坑的是它会间歇性成功

`Start-Process -WindowStyle Hidden -PassThru` 有时拉起来的进程**真的活下来了**，于是你以为方法通了。换个时刻再用同一写法，进程当场就死。你会陷入「失败、重试、偶尔成功、再失败」的循环，白烧很久，
还会把「进程死了」误归因成别的（脚本写错、显存不够、模型加载失败）。

**看到「同一写法时灵时不灵」，先换机制，不要重试。** 这是 job object 回收的随机性，不是你的脚本坏了。

### 退路：让用户从桌面双击

交互会话里启动的进程不受 SSH 的 job object 管辖。摸到路后直接请用户双击启动，
并提醒他**别关那个窗口**（关了服务就停）。这比继续折腾分离启动快得多。

### launcher .ps1 要参数化

把目标 .bat 路径当参数传（`-File launch.ps1 -Target <bat>`），不要给每个 .bat 复制一份 .ps1。
否则目标一变就得同步改 N 个文件。改漏一个，新任务就跑到旧目标上。
**症状是「启动成功但跑的是旧配置」**，极难发现。

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

之后轮询日志文件。用完 `schtasks /delete /tn <名> /f` 清理，**测试任务用完即删**。`/sc once /st 23:59` 的触发器到点会自己开火（忘删等于定时炸弹）。

**`/end` + `/delete` 只删任务定义，已拉起的子进程树照活。** 症状是任务列表里没了、端口还占着、显存没释放（llama-server 实测）。杀常驻进程以进程表为唯一证据：`Get-CimInstance Win32_Process -Filter 'name="llama-server.exe"'` 拿 PID → `taskkill /PID <pid> /F` → 复查 `nvidia-smi` 与端口，确认释放再起下一家。

**改完启动脚本重跑服务，生效以脚本指纹为证。** 换过 .bat 参数（如 llama-server 的 `-c`）再 `/run`，读**新日志**里引擎打出的参数行（`load_model: … n_ctx_slot = …`）确认新值生效。`health` 200 只证明服务活着，不证明跑的是新参数。实测出现过 scp 了新 bat、任务重跑后引擎仍按旧 ctx 服务，health 全程 ok。一份日志要查多次就 scp 回本地 grep。逐次远程 findstr 既付往返延迟，还容易被编码错配搜出假结果。

**launcher 退出 = 它拉起的孩子陪葬。** setup 型脚本（装完环境、起服务、自己就退）经计划任务跑时，服务是它的子进程：launcher 一退，控制台会话回收整棵进程树——日志里 `ready:` 都打出来了，再查端口已无人监听。**长时服务必须是 bat 自己的前台执行体**（bat 不退出，计划任务会话就一直抱着它）：服务命令写成 bat 的最后一行前台命令（或直接调 `python setup.py <args>`，让 setup 停在「起服务」那一步不自然退出也行——只要退出发生在服务死之后）。

**vsdevcmd.bat 横幅会炸掉 bat 的后续执行**：`call vsdevcmd.bat >> log 2>&1` 把它的多行 `*` 横幅重定向进日志后，bat 在 call 之后当场静默死亡（LastTaskResult=1，call 后第一行 echo 都不执行，stderr 全空）。同机 `>nul 2>&1` 写法跑通、`>> log 2>&1` 写法必死，A/B 对照实锤（横幅带 ANSI/Unicode 字符，cmd 重定向管道遇之而断）。修法固定：**vsdevcmd 的输出一律 `>nul 2>&1`，别进日志**；编译器可用性用 call 之后的 `where cl >> log` 取证。

**非交互必防按键暂停**：setup 类 .bat 常带「press any key」，stdin 无入就永久挂着。喂空行 `echo. | cmd /c run.bat` 解除；进度改为读日志里自打印的 START_AT + 里程碑行。

**重定位任务目标别 `/change /tr`**：改了触发器路径再 `/run`，任务可能仍按创建时的旧路径跑。换脚本一律 `/delete /f` + `/create` 重建，`/run` 前先 `/query /fo list /v` 核「Task To Run」已是新值；`/create` 与 `/run` 别挤一行还 `2>nul` 吞错——创建失败时 `/run` 会报「找不到指定的文件」，先查创建是否真成功。

**回显成功 ≠ 已执行。** `schtasks /create`、`/run` 打出的「成功」字样、WMI `Invoke-CimMethod` 返回的 PID，都只证明「创建/尝试」发生过，不证明脚本真的跑了。见过回显全部成功、产物始终没写进文件的案例（原因未定位）。**判执行的唯一证据是产物**：日志文件、进程表、端口。给了几十秒观察窗仍无产物，就把结论钉成「未执行，原因未定位」。**不要无限换机制**，直接转上面的「请用户双击」退路。

**长任务必须自己增量写入文件**：每个单元跑完写一次结果文件，并支持跳过已完成的续跑。
否则会话一断或任务一停，全部结果丢掉。

**本地中断 ≠ 远端中断**：ssh 前台命令被 agent 侧中断（用户插话、工具超时、
"Orphan recovery" 提示）时，远端子进程常常**已经或将继续跑完**：
cmd/python 不接 SIGHUP 就活着。症状是「我以为没跑，其实产物都在」。
**重试前先查远端**：`dir /b <产物>` + `powershell Get-Content <log> -Tail 15`，
确认没跑再重跑。盲目重试等于把 GPU 时间重复烧一遍。

### 2a2. 远程 MATLAB 一键批跑（`-batch` + schtasks）

形状和 python 作业完全一样。写 .m（内容纯 ASCII，传前转 CRLF），把 `matlab -sd D:\dir -batch "脚本名" > D:\dir\run.log 2>&1` 装进 .bat，用 schtasks 一次性任务拉起。本地用短 ssh 轮询日志末尾的自打印完成标记（脚本末尾自己 `fprintf('DONE_...')`），产物 `dir /b <figsdir>` 确认后再 scp 回本地。脚本开头加 `set(0,'DefaultFigureVisible','off')`，出图用 `exportgraphics`（批处理模式无显示会话）。

- **重跑前先 `taskkill /IM matlab.exe /F`**：上一轮失败的 matlab.exe（含 CrashHandler/JVM 子进程）还占着会话与日志，新 run 会卡死或读到旧产物。
- **`-batch` 报 `Licensing error`（如 -10,32）= 当前 ssh 账户没有已激活的 license**。日志横幅会打出它找到的 license 文件路径。路径里若嵌着另一个用户名（交互式登录用户 vs ssh 用户），激活就在别人的 `AppData\Roaming\MathWorks` 下。这类问题换命令解决不了，报主人到机器前处理，可先走桌面双击路径。
- **cmd 的 `>` 重定向按控制台代码页写日志**：内容多为 ASCII，中文段是 GBK。拉回本地要用 `iconv -f GBK -t UTF-8` 读。UTF-16LE 是 PS 重定向的形态，先看头几字节再选转码。
- **Control System Toolbox 的对象函数只吃 sys 对象**：`c2d(ss(A,B,C,D), h, 'zoh')` 返回 `dsys.A`/`dsys.B`。直接喂裸矩阵（`c2d(A,B,C,0,h,'zoh')`）会报 `Too many input arguments`，看着像参数写错，实为 API 的形态问题。

## 2b. Hermes 侧壳卫生：fire-and-poll，别前台挂长 SSH

前台 ssh 跑长任务（下载/装环境/推理）时，用户插话或工具超时会把命令「挪去后台且不杀」。
每个被挪走的都在那里挂着一只 SSH 壳。`ssh 跑 && ssh 查` 链式写法一只壳占两条连接，翻倍堆积。
后台壳退出晚。早已处置过的结果会以迟到通知回声重报一遍。exit 255/-15 多半只是 kill 壳的动作，不能证明任务失败，去日志找 `*_OK` 再定性。

**正确形状（fire-and-poll）**：远程侧分离启动（schtasks /tr 或 `start /b "" cmd /c "job > job.log 2>&1"`），
本地用**短 ssh 轮询日志**（`findstr /c:"ALL_DONE" job.log`），每次短连接完即退，零残留壳。
常驻服务例外：一条 ssh 挂着可以，但要 persist 且心里记账。

**收尾自查**：`ps aux | grep "ssh.*<ip>" | grep -v grep`。除了常驻服务，其余验完结果就 kill。
「后台任务数量」本身就是卫生指标，超过 2 只就该清。

## 3. 输出编码

Windows 控制台默认 **GBK**。Python 打印非 GBK 字符（emoji、✅❌、部分符号）会
`UnicodeEncodeError` 直接中断脚本。

- 设 `$env:PYTHONIOENCODING='utf-8'`（PowerShell）或 `set PYTHONIOENCODING=utf-8`（bat）
- **脚本里仍然不要用 emoji**：环境量不是每条调用路径都传得到。写 `PASS` / `FAIL` 更稳
- 回显中文乱码只是显示层问题，**不影响文件内容**。判文件内容用计数或哈希，不看回显

**从 PowerShell 重定向到文件（`cmd > out.txt`）写的是 UTF-16LE（带 BOM）。** 文件看着正常，
但把 `--help` / 日志这样拉回 Linux 后，**做纯字节匹配的工具搜 ASCII 字符串会零结果**：
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
- **退出码取证别内联**：`cmd /c foo.exe & echo %ERRORLEVEL%` 在同一命令行里 `%ERRORLEVEL%` 于解析期就展开成常量，恒不值得信。退出码写进 .bat 单独一行 `echo EXIT=%ERRORLEVEL% >> log`，ssh 侧只读日志。
- **新编 exe 拉起报 -1073741515（0xC0000135）= 缺 DLL**：症状只有退出码没有报错文本。把构建产物 bin 目录的依赖 DLL（ggml*.dll 一族）拷到 exe 旁边再跑；按码先查缺库，再怀疑程序本体。

### 4b. 传 `.ps1` 时：**UTF-8 无 BOM 会被当成 GBK 读**

自己在 Linux 上写好的 `.ps1` 传过去，**含中文就解析失败**：

```
表达式或语句中包含意外的标记“)”
字符串缺少终止符
MissingVariableNameAfterForeach
```

根因不是语法错，是 **PowerShell 5 默认按 ANSI/GBK 读无 BOM 的 .ps1**，
多字节字符被拆坏后引号配对被破坏。**注意：这和「控制台回显乱码」不同，
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

**同一限制也适用于把复杂 PowerShell 直写在 ssh 命令行里的情形**：`\$_`、`\$d`
这类转义会被 ssh → cmd → powershell 三层剥掉，症状是 `ParserError: MissingVariableNameAfterForeach`。
**含变量、循环、`$_` 的一律改走「写 .ps1 → scp → -File 执行」。无变量的单行 PS 可以直接内联，一律用「外层 bash 单引号包住整条 ssh 命令、PS 段用双引号、PS 内部参数用单引号」的形状**：`ssh host 'powershell -NoProfile -Command "Get-PSDrive D | Select-Object Free"'`。外层双引号 + `\"` 转义的形状只对不含 bash 展开字符的扁平命令可靠；命令一旦带 `$_`、方法调用括号（`Get-Size()` 类、`[math]::Round(...)`、`(...)` 嵌套），bash 在 eval 层就把引剥乱，症状是本地 shell 报 `syntax error near unexpected token '('`——错在本地不在远端，别去远端找原因。（实测稳定的形状：`Get-FileHash` 单文件哈希、`Get-CimInstance -Filter 'ProcessId=…'`、无 `$_` 的 `Get-WinEvent -FilterHashtable @{…}` 单层内联跑通；要访问管道变量就走脚本文件或改 Select-Object 属性直取。）

**内联 PS 的参数值含空格必须单引号包住**。`Select-String -Pattern A gen,B gen`（逗号分隔且含空格）经三层剥引号后变成位置参数，报 `PositionalParameterNotFound`，看着像 PS 语法问题，实为剥引号。写 `-Pattern 'A gen','B gen'`。同理 `findstr` 的 `/i "a b"` 形状在 ssh 单引号段里只剩外层双引号可用，包不住就改走 PS。

**删除/批量删除类脚本先带 `-DryRun` 开关跑一遍**：先打印待删清单与分类计数，
确认无误再真删。另外，**按同一个词根写模式极易漏族**（实测：
`dbg_diff_*` 删完后又跑出 `v2diff_*`、`v2log_*`、`v2raw_*` 三族）。
先 `Get-ChildItem | Group-Object { ... }` 按词根聚类看全谱，再写模式。

## 5. SSH 别名可能指向不可达地址

网络环境切换（VPN ↔ 局域网）后，ssh config 里的 `HostName` 可能仍指向旧地址。
**症状是命令返回空**。命令不返回错误信息，只返回空，很容易误判成「文件/目录不存在」。

- 连不上先探连通性确认该走哪条路：`ping -c2 -W2 <ip>`
- **不要改用户的 ssh config**：改错了，主人下次换网络时更难查
- 会话内做一个带显式地址的封装脚本（`exec ssh -o … User@<ip> "$@"`），后续命令都用它
- **反向坑：ssh 走别名通了，scp 手打裸 `user@IP` 却报 Permission denied**。别名里嵌着正确的 `User`（大小写可能与本地用户名不同，Windows 常是大写开头）与 `IdentityFile`，裸地址两个都不带。同一台机器上 ssh 与 scp 一律走同一个别名，别手拼地址。

### 5c. VPN/WireGuard 非对称不通：主人连得上本机、本机连不到远端

主人到本机遇通、本机到远端 ping/SSH 超时，说明链路非对称（对向通证明隧道服务端活着）。按「本机到远端」这一向查，别乱改别名：

1. 先本机 `ip route get <远端VPN地址>`：路由走 LAN 网关而非 wireguard 接口 = 本机根本没有进隧道的路由，后面全不用查，先修本机 VPN 客户端。
2. 路由对了仍超时（超时不等于拒绝，是丢包）：查远端入站拦截。新近重建的网卡容易被划进防火墙最严的网络 profile。把诊断三连交给用户，**接口真实名以回传为准**（不预设叫 wg0）。顺序：查 profile 列表 → 把该接口改 Private → 改不动就直接开入站规则（TCP 目标端口 + ICMP）。
3. VPN 配置文本自身两查。`AllowedIPs` 里网段写成 `/32` 就是单主机地址，整段进不了隧道（段应为 `/24`）。客户端改动必须对路由器/服务端 peer 同步。服务端 peer 的 AllowedIPs 不含该客户端主机地址时，回程包不知塞进哪条隧道。
4. **修复效果归因要等一手证据**。「跑了某条命令后症状消失」只能报「执行后症状消失」，不能直接报「它是根因」。拦截点往往是多嫌疑并存。给用户诊断命令时不许预告输出形态（「一目了然」）或预判根因，标推演，等输出回传再定罪。

## 6b. 远程 webui 要上传素材：先画「用户在哪台机器」的地图

远程主机起的 webui（gradio 等），**上传对话框翻的是用户浏览器所在机器的盘，不是远程主机的盘**。
给面板备素材时，文件必须落在用户看得见的文件系统（本机工作目录/共享盘），
拷到远程主机 D 盘 = 拷进了用户够不着的地方（10-08 实例：拷到笔记本 D:\LLM\s2pro\ref 被问「在哪里」，
而素材早已 scp 回本机工作目录，一步多余的弯路 + 一次 HTTP 服务打补丁）。
动手前先答三问：用户的浏览器在哪台机器？那台机器能看见哪些路径？素材现在在哪？

## 6. 状态断言纪律

状态类断言（服务在跑吗、任务完成吗）**开口前先查活体**：进程表、端口监听、
健康端点、资源占用。还要**区分「在响应」与「可用」**：健康端点返回加载中（如 503）
只说明进程活着，不代表它能干活。

**快照会过期。** 报「好了」之前，在任务**该完成的时刻**再查一次。
别拿一次中途成功的探活当终态。

**回显不是事实，前提先取证。** 命令自己报「成功」不等于世界变了（见第 2 节）。「已重启」「已生效」这类**实验前提**先核证据再下分支结论。凭推测会把分支判错（实例：判定「重启后仍复现」，一查开机时间，机器根本没重启过）。

**预检数字读不到 = 阻断，不许 fallback 默认值放行。** 磁盘余量、显存、内存这类数值门槛，命令读失败/乱码/空返回时按「无证据」处理：先修读数命令（多半是引号形状问题，见 4b）再放行后续动作。代码里 `free is None → 当空间够` 这种兜底等于用假数字做真决策（实例：Get-PSDrive 读数被引号剥死，兜底放行起了 23G 下载，实际只剩 16G，起完才暴雷再止损）。

**只读取证速查**（单行 PS 内联的形状见 4b）：
- 开机时间：`(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToString()`（本机无 `wmic`，别用；新装 Windows 主机也在移除 `wmic`，报「不是内部或外部命令」只是工具缺失，改走 PS，别当成机器坏了）
- 进程真实命令行（服务实际吃的参数，与启动脚本互证）：`(Get-CimInstance Win32_Process -Filter 'ProcessId=<PID>').CommandLine`
- 崩溃取证（进程崩了、窗口输出拿不到时）：`Get-WinEvent -FilterHashtable @{LogName='Application'; Id=1000; StartTime=(Get-Date).AddMinutes(-15)} -MaxEvents 1 | Format-List TimeCreated,Message`。给出错误模块与错误码（`0xc0000409` = 快速失败）。
- GPU 残留：`nvidia-smi --query-gpu=name,memory.used,utilization.gpu,temperature.gpu --format=csv`
- 谁在机器旁：`quser`（交互会话与空闲时长）
