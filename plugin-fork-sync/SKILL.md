---
name: plugin-fork-sync
description: 同步插件/引擎 fork 与上游、重植本地补丁、跑全量回归时使用。
version: 1.0.0
author: Nekonya
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [git, fork, plugin-maintenance, testing]
    related_skills: [git-repo-hygiene, hermes-local-ops-troubleshooting, test-driven-development]
---

# Fork 同步与本地补丁重植

## When to Use

维护「fork 上游 + 本地补丁队列」的仓库（Hermes 插件、推理引擎，如 lcm-x、Strata）时：要拉上游最新树、把本地补丁重植到新基线、或重植后跑全量回归验收。标准流程：同步上游 → 重植补丁 → 全量回归 → 验收 push。

## 动手前必查

- **宿主源码补丁（非 fork）先确认更新机制**：读 `install-stamp.json` 的 `updateMechanism`。git checkout 的更新会 autostash 本地改动，pull 后尝试 `stash apply`；上游改同一文件时补丁留在 stash 不落地。用本地分支+提交（更新器检测到自定义分支改走 `git merge`）或补丁文件+重贴脚本，别把未提交改动留在 detached HEAD 上。
- **上游是否已修目标问题**：读 release notes 全文再下结论，关键词计数不算——修复可能换了措辞；再 `git grep <symbol> upstream/main` 核新树实物。「没修」的结论要有 0 命中或代码实物支撑，推断级结论标「待核」。
- **「上游没动这块」先验路径存在**：`git log <range> -- <dir>/` 对不存在的 pathspec 静默返回 0，看起来像「上游没碰」。先 `git ls-tree -d --name-only <ref> <parent>/` 确认目录真实存在，再数提交。模型家族常没有同名目录（代码散在 core/kernels/program），按家族名找不到不等于没改。
- **按区域数提交用 `git rev-list --count <range> -- <dir>/`**；`git log --name-only | cut | uniq -c` 数的是文件出现次数，一个提交碰多个文件会把它算大，不能当提交数报。
- **上游 schema 兼容性**：notes 里找「schema change / rollback」字样——插件级升级若声明不动存储 schema，就不需要数据迁移，这条直接决定重构/升级路线的成本评估。
- **许可证与 PR 策略**：先开 issue 探上游意向再从 fork 分支提 PR；PR 不成且许可证允许 → 止损切自有分支大改，不为上游排队。

## 评估上游对某模型族的影响（按文件/符号，不按目录）

模型族名未必是源码目录：Strata 的 qwen4exp/QSA 横跨 `src/core/layer.hpp`（`QsaState`）、`src/kernels/cuda/qsa_*.cu`、`src/prefill`、`src/program`，树里没有 `src/qwen4exp/`。按目录名或提交标题搜会给出假的「0 改动」。

- 先 `git grep -l '<symbol>' <upstream>` 找真实文件，再 `git log <base>..<tag> -- <那些文件>`。
- 分开「上游改了这块」与「改的这份在本机 arch 上跑不跑」：同一内核可能只对 gfx12/SYCL/CUDA 生效。看默认值，不只看代码存在。
- 同时查状态结构与快照接口（如 `QsaState`、`conversation_snapshot`）有没有动；这些动了，磁盘缓存补丁才需要按语义重写。

## 同步流程

1. 旧基线兜底：给**当前生产分支**打本地 tag（`git tag legacy-<ver>-private <当前分支>`），不要假定分支名是 master。
2. 先 `git remote -v` 认清哪个是上游、哪个是自有 fork（Strata 是 `origin`=Niko1221/Strata、`fork`=But-Not-Yet/Strata；别的仓库可能是 `upstream`）。再 `git fetch <上游> --tags && git fetch <fork> --tags`（SSH 走 `~/.ssh/id_ed25519_github`，IdentitiesOnly）。fetch 完再 `git ls-remote` 对平远端头，确认 ref 真动了。**tag 引用不带 remote 前缀**：fetch 后直接写 `v<ver>`，`upstream/v<ver>` 会报 not a valid object；补丁计数基线用 `fork/main..HEAD` 这类真实存在的 ref。
3. 先选路线，别默认 cherry-pick：
   - **长期分支带合并历史**（Strata 这类）：从当前生产分支切新分支（`git switch -c f-<ver>-prod f-<old>-prod`），把上游 tag 整树并进来（`git merge --no-ff <upstream-tag>`）。上一轮的 merge commit 就是基线。
   - **干净补丁队列**（fork/main 没有自有提交）：从 `fork/main` 切出，再逐条 `git cherry-pick -x <commit>`。
4. 冲突只改冲突块，**不要用 `git checkout --ours/--theirs` 整文件取一侧**：整文件取一侧会丢掉该文件里已经自动合并好的另一侧改动。手工替换 `<<<<<<<` 块，保留其余自动合并结果。`--ours`/`--theirs` 的方向在 merge 与 cherry-pick 下不同，先看 `git status` 确认当前操作类型。

## 冲突手工移植三问（每条冲突补丁都过）

1. **上游是否已吸收同等语义？** 已吸收的那一半直接砍掉，不重复实现；只把旧行为断言保留为回归用例（改名标注它现在验证的是上游容差仍成立）。
2. **我方净增量到底是什么？** 只移植那一小块，落点按新代码结构选（helper 拆在哪就接在哪）。
3. **老测试锚点还活着吗？** 上游重构常把源码顺序类测试（`inspect.getsource` 找符号）的锚点拆散。处理方式见 test-driven-development 的结构性测试条目：用新调用图上的等价多段不变量重锚，不删测试、不降断言。

移植放宽类补丁时，上游/宿主的硬闸语义（如精确 nonce、唯一性）必须原样保住；为语义一致性改旧测试的期望值要在 commit message 写明理由，防止下轮同步时被当成漂移。

## 自动合并后的语义复核（文本零冲突也要做）

`git merge-tree` 只报文本冲突；上游新代码落进我方改动过的函数，可能编译通过但语义是死的。cherry-pick 全部零冲突**同样不算数**——上游重写过补丁落点的文件时三方合并照样能干净落地，复核必须做。至少查四类：

- **cherry-pick 全绿后的三件套**：①逐条补丁的核心符号在新树 grep 实物；②关键补丁对上游 tag 实物核「上游是否已吸收同等语义」（`git show <tag>:<file>` 直接读落点区，别信 notes 措辞）；③补丁自带的测试文件全部定向跑一遍，唯一失败逐条定罪（多半是上游重构拆了测试锚点——按新调用图重锚、断言强度不降，见三问第 3 问）。

- **上游新默认/自动定容块落进我方分支**：上游按自己的数据结构写「未给值就自动算」，我方若把默认值改成别的，这段就是死代码。合并后 grep 新符号（`auto_...`、`if (x < 0)`），显式决定停用还是改写，并在旁边写一行注释说明「本 fork 的数据结构没有这一层」，防止下轮同步把它当漂移。
- **上游的日志解析器/监控正则对不上我方日志行**：引擎或服务改过日志格式时，上游新加的 regex 会静默读不到数（监控卡全零，不报错）。合并后拿上游 regex 逐个对我方 `fprintf` 行做一次匹配试验；对不上就改日志格式或改正则，二选一写进提交说明。
- **CLI 帮助/usage 字符串**：上游改了某个 flag 的默认语义，帮助行会跟着自动合并；我方把默认值改成了别的含义时，`--help` 仍可能写着上游的「按空闲 RAM 自动定容」，与实际行为相反。合并后 grep 每个被我方改过默认值的 flag，逐条核对帮助文案。
- **上游测试锚点**：上游重构常把测试依赖的符号或顺序拆散；自动合并的测试文件要真编译真跑，不能只看冲突标记。

## 变体：把 fork 插件内化为另一插件的内部组件

当 fork 插件只是另一个插件的 inner（注册竞争、装载顺序耦合时），可把它从宿主插件列表移除、由包装方直接加载——fork 同步流程本身不变，多三条规矩：

- **代码留在 fork 仓原地**，包装方用 `importlib.util.spec_from_file_location` 挂成私有包名（如 `_tiered_lcm_x_internal`），不在宿主插件目录再注册一份——双份加载会复活双路径钩子/双实例那类病。
- **版本锚写死在包装方代码里**：一个 `FORK_ANCHOR` 字典记 upstream/fork 地址、分支、commit、version，注释说明该 commit 在哪个基线之上加了什么——下轮 fork-sync 靠它定位重植面。
- **需要 fork 侧配合的能力改动（如补 detach 支持）提交进 fork 仓**，不塞进包装方；合入后更新 FORK_ANCHOR 的 commit。宿主 config 的 plugins.enabled 移除该条目时留一行注释指向内化模块，防将来排查注册问题时找不到插件去哪了。

## 生产机增量编译（不碰运行中的引擎）

生产盒上引擎常驻几十 GB，编译前先 `free -m`；可用不足 8 GB 时固定 `-j1`，`nice -n 10`，绝不并行赌内存。

- 复用已有的 `build-hip`（Ninja + Release + HIP arch），不删对象、不重建配置；`build-hip/strata` 是验证产物，**不要覆盖 `engine/strata`**。
- `ninja -n` 在 CMake 重跑前只显示 2–3 步，看不到真实工作量；直接跑构建或先 `ninja -C build-hip build.ninja`，CMake 重跑后步数才展开。
- 后台起 `cmake --build build-hip -j1 > log 2>&1; echo EXIT=$? >> log`，配一个只读哨兵每 15–20 秒写「步数/错误数/可用内存/退出码」；构建结束再跑定向测试。哨兵用 `pgrep -f '[c]make --build ...'` 避免匹配自身。

## 全量回归（本机生产盒跑法，三次白跑的教训）

**主人裁定（10-23，lcm-x 0.28.1 同步）**：万级用例的分片全量（~75 分钟）**不值得作为每次同步的门槛**——「跑这玩意没有意义」。现行验收以定向测试（本次触碰文件＋补丁自带测试）＋语义抽查＋宿主侧 shim 契约测试为准；分片全量只在改动压在压缩/回滚等高危路径且主人同意等时再跑，跑前先问。

生产盒内存被常驻模型压着，大套件（万级用例）串行单进程跑**必在中途无声死掉**。规矩：

- 先跑**定向文件**（本次触碰的测试）绿了才进全套。
- 别加仓库没装插件的参数——先用最短试跑看参数被不被认（`--timeout` 这类插件参数最常踩）。
- 全套用 `scripts/shard_pytest.py` 按文件切成用例数均衡的 N 片，**每片独立进程串行跑**——进程退出即资源归零，这是唯一能绕过累积爆点的办法。脚本住在**技能目录**里而非目标仓（仓内没有 `scripts/shard_pytest.py`），先 `cp <技能目录>/scripts/shard_pytest.py /tmp/` 再跑。
- 每片输出写日志文件、结尾 `echo EXIT=$?` 由脚本自己追加：日志里有 EXIT 行=外层 bash 活过会话关闭，日志停在进度中间无 pytest 收尾行=内部 pytest 进程被单独杀。
- 后台起跑必须 `persist_on_release=true` + `notify=true`，否则会话关闭连坐（实测 agent_close 会杀掉未 persist 的后台进程，跑到 59% 白扔）。
- 崩溃归因三板斧：日志最后百分比 × `--collect-only` 用例总数 ≈ 用例序号 → 在收集清单里定位所属文件 → **单独跑该文件**；单跑绿 ⇒ 不是补丁撞的，是资源累积，交给分片；单跑红 ⇒ 才是真回归，先修再重跑。
- 全套参数带 `-q --tb=no -rf`：失败名单直接可数，不灌上下文。

### 既有红名单：先测基线，再谈回归（比条数会骗人）

宿主套件本来就带一批环境性失败时，「修后 N 条红」不承载任何信息。规矩：

- **建干净树当对照组**：`git worktree add --detach /tmp/<名> <修复前 sha>`；在两棵树上跑**同一批文件**（同一命令、同一 `HERMES_HOME=$(mktemp -d)`），把两份失败清单落盘。
- **比「失败用例 ID 集合」，不比条数**。20 条变 17 条可能是「新增 4 条 + 消失 7 条」，合并成一个数字就把真回归洗白了。判据：修后集合是基线的**子集**。多出来的每一条单独归因，不许并进「环境问题」。
- **单文件单跑全绿、整轮才红 = 顺序敏感**，不是补丁撞的：两边各跑三遍确认稳定，再把基线**整轮**也跑一遍钉死归属；没跑基线整轮就写「待核」，不写成「已排除」。
- **回归测试要能被旧代码打红（负对照）**：把修复前 commit 的 `git archive | tar -x` 到临时包，喂同一场景，看它真报出生产里那条错。只会绿的测试不算回归测试。
- 同一套件里「同名目录遮蔽」这类环境形状也会把测试打红（见 `hermes-local-ops-troubleshooting` 的包导入条目），归因时先看失败是代码还是装载形状。

### 引擎类 fork 的回归（CMake/ctest）

- 引擎构建树的测试目标常默认关：先 `grep STRATA_BUILD_CONVERSATION_TESTS build-hip/CMakeCache.txt`；关着就用 `cmake -S . -B build-hip -DSTRATA_BUILD_CONVERSATION_TESTS=ON` 只加测试目标，不重编引擎对象。
- 测试目标编出即可跑，不必等整棵引擎：`ctest --test-dir build-hip -R 'conversation|session_save' --output-on-failure`。
- `ctest` 报 `Not Run` 是二进制还没编到，不是失败；等构建走过那个目标再补跑，别把它记成红。

## 验收与 push

- `git log --oneline upstream基线..HEAD` 计数 = 补丁数（语义相近的可合成一个提交，message 写明合并了哪几条）。
- **README/发布说明里的性能百分比在 push 前复算**：分子分母必须来自同一层。引擎 `reused` 数、serve 进度行的网格数（`reading X of Y`）、段挂载深度是三个量；混用会写出对不上的百分比。复算不过就改数，别改百分比去迁就句子。
- 工作树零脏文件；署名按仓库既有身份，不临时换：Strata 公开 fork 用匿名 `But-Not-Yet`（零个人信息）；学术文档和其他仓库用「独立研究者」。两边都不带个人邮箱、不挂学校院系。
- 定向绿 + 全分片失败名单**归因完毕**（每个失败分类：上游本来就红 / 我方补丁撞的 / 环境问题）才算绿，才 push 分支到 fork。
- 插件类改动 push ≠ 生效：重启宿主（gateway）后验活体（进程在、插件加载、目标链路真跑过）才叫「能正常运作」。
- **重启后必须用「重启时刻之后」的日志断言目标缺陷归零**：`systemctl show -p ActiveEnterTimestamp --value <unit>` 取时刻，只数该时刻之后的行。验收脚本要在旧进程上**全红**（它自己就是负对照），否则它的 PASS 不证明任何事。
- **重启可能揭示修复从未生效**：这时第一件事是证「进程加载的是哪一份」（模块自报 `__file__`、pyc 与源 mtime、进程解释器版本），不是换第三个假设重改代码。

## 支持文件

- `scripts/shard_pytest.py`：把 pytest 收集清单按文件切成用例数均衡的分片，输出每片的文件列表（配合上面的分片跑法）。
- `references/lcm-x-notes.md`：lcm-x 仓的 remote 拓扑、分支名、venv 路径、套件规模等运维现状——先读它再动手，滞后了当场以 git 实物为准更新它。
