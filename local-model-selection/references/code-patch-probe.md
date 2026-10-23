# 代码补丁探针（SWE-bench 类原题）

自建选择题库的说服力有限。要对比两个量化档 / 两个模型在**真实仓库级修复任务**上的能力，
用真实基准原题。本文是这条路的搭建与判分纪律；判分协议四条、INVALID 闸、答案 key 自校、
天花板效应等通用条款见 `quant-quality-probe.md`。

## 1. 选基准前先问：判分环境能不能立起来

- **Terminal-Bench 依赖 Docker**（官方 harness 自己声明）——目标机没有 Docker 时直接出局，不要花时间试。
- **SWE-bench 可以绕开 Docker**：git + python + pytest 就够，代价是要处理「老仓库要老解释器」（见 §3）。
- 实例从 HF datasets-server 取，别去 clone 官方 harness：
  `/rows?dataset=princeton-nlp/SWE-bench_Verified&config=default&split=test&offset=N&length=100`
  （每页上限 100，翻页凑全量）。需要的字段：`instance_id / repo / base_commit / patch /
test_patch / problem_statement / FAIL_TO_PASS`。
- **挑仓库比挑题目重要**：Verified 里 django 占近半，仓库大、依赖重、单题测试以分钟计。
  要**纯 Python + 依赖少 + 测试秒级**的仓库（sympy 一类）才能批量跑。优先「<15 分钟修复」难度档。
- **只用一个仓库**能把搭建成本压到最小；跨仓库的多样性在这里不值那份折腾。

## 2. 判分环境必须先过 gold 探路（最关键的一步）

**拿 gold patch 都跑不绿的判分环境，测出来的分数全是废数。** 逐题探路：

1. `git checkout -f <base_commit>` → `git clean -fdx`
2. 应用 `test_patch` → 跑 FAIL_TO_PASS → **必须失败**
3. 应用 gold `patch` → 跑 FAIL_TO_PASS → **必须全绿**

两步都符合，这题才可用。不符合的（年代 / 依赖 / patch 冲突）**当场剔除**，否则坏题会混进总分。

`FAIL_TO_PASS` 可能只给测试名、不带文件路径——测试文件从 `test_patch` 的 `+++ b/<path>` 行解析出来。

## 3. 老仓库要老解释器（无 Docker 时的轻量等效）

Python 版本推进会删掉老仓库依赖的接口（`collections.Mapping` 移入 `collections.abc`、
`distutils` 从标准库移除）。**装一个 `sitecustomize.py` 到 venv 的 site-packages 一次补齐，
胜过装多个 Python 版本**：

- 把 `collections` 下缺失的 ABC 名从 `collections.abc` 逐个补回（`Mapping` / `Sequence` /
  `Iterable` / `Callable` 等一整组）。
- `distutils` 靠 `pip install setuptools` 注入。

这层补丁让同一个解释器跨年代跑通，是官方 per-repo Docker 镜像的等效物。
**报错形态**：`from collections import Mapping` → `ImportError`；`from distutils.version import
StrictVersion` → `ModuleNotFoundError`。看到这两个就是缺这层补丁，不是题目坏了。

## 4. 裸聊天接口 → 一次性 patch 协议

llama-server 只有 `/v1/chat/completions`，没有 agent loop。协议：

- 提示词 = 题面 + **文件清单里各文件的当前内容** → 要求**只输出 unified diff**。
  只给文件清单（从 gold patch 的 `diff --git a/<path>` 解析）当定位提示，**绝不把 gold patch
  内容放进提示词**。
- 解析时优先取 ``` 包裹的块，否则从第一个 `diff --git` 起截到末尾。
- **不传 `temperature` / `top_k`**（用模型自己的预设；强制贪心对真实使用场景无意义），
  **reasoning 必开**。理由见 `quant-quality-probe.md` §1。
- **★ 拼提示词时不要给源文件字符数设上限。** 设了就会在不知情的情况下把 bug 位置切掉：
  实测 `MAX_SRC_CHARS=24000`，35 题里 27 个文件超限、 8 题的 bug 落在截断之外；
  模型看不到代码只能编，补丁自然应用不上——**症状伪装成「模型格式差」，真因是喂了残缺输入**，
  而这两个假设的整改方向完全不同。因上下文确实必须截断时，**在提示词里留 `(truncated)` 标记
  并在运行时拒绝该题**，不要让它冒充结果。
- **输出了源文件里不存在的代码，先查「它被喂了什么」，别先归因「幻觉」。**
  模型不可能写出它没见过的行；看到「它怎么会知道这个」的瞬间，就该去 dump 一份真实提示词读一眼。
  手里有 dump 的产物就必须读过，不能只看长度之类的摘要数字。

## 5. ★ patch 应用必须多级容错——否则把做对的判成 0

**模型写的 hunk 头计数常差 ±1。`git apply` 会直接以 `corrupt patch` 拒收，而 GNU `patch` 照收。**
容错链按序试，任一成功即通过：

1. `git apply --whitespace=nowarn`
2. `git apply --3way --whitespace=nowarn`
3. `git apply -C1 --whitespace=nowarn`
4. **`patch -p1 --forward --batch --no-backup-if-mismatch -i <diff>`** ← 兜底，最宽松

少了第 4 级会得出「模型全 0」的假结论：实测里模型产出的补丁与 gold **语义等价**，
却被 `git apply` 逐条拒收。诊断手法：拿被拒的 diff 手动跑这三种应用器，对比报错——
`git apply -v` 会报 `corrupt patch at <file>:<line>`（行号落在补丁末尾之后，因为它还在找
hunk 体里不存在的行），而 `patch --dry-run` 直接说 `checking file ...` 无错。

## 5b. 判分层：逐条解析测试状态，且对齐官方语义

**退出码不够用。** 官方判分是**逐条解析测试状态**（`swebench/harness/grading.py` 与
`log_parsers/python.py`：按行首 `PASSED` / `FAILED` / `ERROR` / `SKIPPED` / `XFAIL` / `XPASS`
切词，`parts[1]` 是测试 ID）。所以 pytest 必须带 **`-rA`**，否则日志里只有进度点、没有逐条状态。

**写自己的判分器之前先读官方实现**（`SWE-bench/SWE-bench`，harness 在 `swebench/harness/`）。
本类任务最容易漏掉的三条官方判据：

1. **★ 状态表的 key 是全路径 ID（`path::test`），而数据集给的 F2P / P2P 是裸测试名。**
   只按全路径建索引 → 查裸名全部 `MISSING` → **所有模型一律 0 分，而且不报任何错**。
   必须**同时按裸名建索引**（`m[tc] = st; m[tc.split('::')[-1]] = st`）。
   症状识别：每题都显示「补丁应用成功但测试没过」，且换个模型结果一模一样。
2. **resolved = FAIL_TO_PASS 全过 且 PASS_TO_PASS 全过。** 只看 F2P 会把「修好目标但弄坏
   一大片」的补丁判成通过。P2P 也在数据集里（每题几十到上百条）。
3. **拒绝改动了测试文件的补丁**（官方规则）。从 diff 的 `+++ b/<path>` 扫，命中 `/tests/`
   或 `test_*.py` 就判失败。

**P2P 条目同样是裸测试名，不能当 pytest 目标传**（会被当成文件路径 → 收集错误）。
官方对「日志里没出现的 P2P」按**静默通过**处理（源码注释原话 `Assume silent success`），
所以回归闸的正确写法是：只有日志里**真的出现且为 FAILED / ERROR** 的 P2P 才算被破坏。

顺带：数据集 schema 在换代。老 schema（`princeton-nlp/SWE-bench_Verified`）没有
`eval_script` 字段，新 harness 走 `make_test_spec` 读它。取题前先核自己手上是哪一版。

## 6. 地板效应（与天花板效应相对）

真实基准可能**太难**：两个量化档都考 0，同样分不出高下。

- 先跑 2–3 题冒烟，确认**参照档得分既不为 0 也不为满分**，再投全量。
- 落在任一端就换协议（给更多文件上下文 / 换成直接问「这行改什么」）或换难度档，
  别硬跑全量交一张全 0 表。

## 7. 运行时坑

- **每题后必须复位工作树**：`git checkout -f <base>` + `git clean -fdx`。中断会在仓库里留下
  `.git/index.lock`，之后每题都报 `test_patch apply failed`——**看着像题目坏，其实是锁**。
  清 `index.lock` 再复位即可。
- **两个跑批进程不能共用同一个仓库**：它们各自 checkout 不同 base_commit，会互相踩。
  **正解是「每实例一个 git worktree」，预建一次**：`git worktree add --detach <dir> <base_commit>`。
  每个实例固定在自己的 commit 上，题间只需同 commit 内回退（`git checkout -f -- .`），
  **不再做全量 commit 切换**——这既是提速的主要来源，也是唯一安全的并行方式。
- **调试期把每题的提示词、模型原始输出、抽出的 diff 分别落盘**：「没通过」时要能第一时间
  分辨「补丁没应用」与「补丁应用了但没修好」——这两者的整改方向完全不同。
- **长跑逐题落盘**，别只在末尾写汇总：中断即全失，而探路 + 全量动辄十几分钟到小时级。
- **每个外部调用单独计时**。把 `checkout; clean` 合成一个计时器，出问题时无法归因——必须拆到
  「每个 subprocess 一个计时器」。合并计时后即使总量对不上也看不出是哪一条，接着只能靠猜；
  一猜就错。
- **★ 首轮跑会慢得多，别把冷启动算成你的代码慢。** 新建 worktree 目录、pytest 写出几千个
  `.pyc` → **Windows Defender 实时扫描**逐个文件过。实测：同一份 replay 脚本，第一次
  `reset` 段 172 秒，**第二次 5 秒（34 倍）**，而逐题结果完全一致。
  **优化之前先冷热各跑一次**；只跑一次会把「首次扫描」误判成 git / clean 慢，
  然后去改根本没问题的命令。
- **`temperature=0` 不等于可复现。** llama.cpp 同参数重跑同一模型，通过项会变——
  实测同一模型两次都报 5/35，但**通过的不是同一批题**（差 ±2 题）。
  所以**两个模型差 1 题不构成结论**，报告里必须写明这个抖动幅度。

## 8. 结果分析：先核可比性，再谈胜负

拿到通过率先别报。三项必做：

1. **报有效分母，不只是 pass/total。** 补丁**没应用上**的题不是模型的失败，是判分环境的失败。
   分别报「pass/total」与「pass/(total − apply_fail)」，并把 apply_fail 计数摆出来。
   一半题都应用不上时，两个百分点的差距根本没有分辨力。
2. **小样本先做显著性检验再宣布胜者。** n 在几十的量级时，几个百分点的差距通常在噪声内
   （Fisher 精确检验能一眼看出）。先给 p 值，再决定要不要说「A 比 B 好」。
3. **读模型产出的补丁本身，别只看聚合分。** 聚合分丢掉机制，而机制才是能用来判断的信号。
   把每题 diff 与 gold 并排，看**改了哪些文件 / 加删行数 / 是否绕开根因**。
   常见的三类毛病各对应一类修法：**过度工程**（一行修复写成上百行、顺手重构无关函数）、
   **只改表层**（改报错字符串的措辞而不动分支逻辑）、**跑题**（改了与题面无关的文件）。
   实测中聚合分给的是「不显著」，而读 diff 得到的模式是一致的、可解释的——**结论靠后者**。

**apply 失败率本身有一半是模型属性，别全推给 harness。** diff 更长、格式更差的模型
更频繁被拒收；模型自己把 hunk 写坏是它在这个任务上的真实短板。区分方法：看**同样被拒**的
diff 里有多少是「手动 `patch` 也收不了」的——那部分才是模型的问题，其余是 harness 的。

## 9. 提速：砍什么，绝不能砍什么

**先量再砍。** 单题 LLM 时间里**提示词评估往往是大头**（整文件上下文下，6k token 的提示词
按本机 PP 就是 5–6 秒），输出生成反而次要。非 LLM 开销（复位、pytest 启动）另算一份。

**绝不能砍的：把提示词裁到只给「该改的那一段」。** 用 gold hunk 位置做窗口化确实是最大的
提速杠杆，但它同时是 **oracle 提示**，而且——**若这个模型是要拿去当自主 subagent 用的，
裁掉全文件就把「自己找该改哪里」这个唯一要测的技能删掉了**。用户会当场点破这一点。
**规格对齐优先于速度**：先问「这个基准要回答的问题是什么」，裁上下文只在那问题确实是
「在给定区域写对修复」时才成立，且必须对所有模型一致、并声明与整文件协议不可比。

**要压时间预算，砍题数，不砍保真度。** 提是：报告里写清 n 变了，说明噪声变大。

**replay 模式是这一类的标配工具**：把上一轮落盘的模型 diff 当成输入重放整条判分链，不调模型。
一举两得：

- **量纯 harness 开销**（无需服务在跑，随时可测）。
- **验证 harness 改动是否保行为**——重放得到与上一轮**逐题完全一致**的结果，才敢说优化没动语义。
  这比省下来的那几秒值钱得多。

**开销修完之后的形状**：隔离 + 清理优化把非 LLM 开销从 338 秒压到 **39 秒**，
于是 **LLM 生成占到 92%**。此时 harness 侧已经没有可榨的了——**时间预算完全由模型决定**
（生成速度 × 题数）。用户要「一个模型 N 分钟」时，唯一诚实的答法是**减题数**并声明 n 变了，
不是继续动 harness。参考量级：同一台机同 35 题，快模型 336 秒、慢模型 490 秒。
