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
- **上游 schema 兼容性**：notes 里找「schema change / rollback」字样——插件级升级若声明不动存储 schema，就不需要数据迁移，这条直接决定重构/升级路线的成本评估。
- **许可证与 PR 策略**：先开 issue 探上游意向再从 fork 分支提 PR；PR 不成且许可证允许 → 止损切自有分支大改，不为上游排队。

## 同步流程

1. 旧基线兜底：`git tag legacy-<ver>-private master`。
2. `git fetch fork --tags && git fetch upstream --tags`（remote 名固定 `fork`/`upstream`，SSH 走 `~/.ssh/id_ed25519_github`，IdentitiesOnly）。
3. 新生产分支从 `fork/main` 切出：`git checkout -b f-<ver>-prod fork/main`。
4. 逐条 `git cherry-pick -x <commit>`；冲突时 `git checkout --ours <file>` 取上游基，再按上游新结构**手工移植我方语义**——禁止硬合旧 diff。

## 冲突手工移植三问（每条冲突补丁都过）

1. **上游是否已吸收同等语义？** 已吸收的那一半直接砍掉，不重复实现；只把旧行为断言保留为回归用例（改名标注它现在验证的是上游容差仍成立）。
2. **我方净增量到底是什么？** 只移植那一小块，落点按新代码结构选（helper 拆在哪就接在哪）。
3. **老测试锚点还活着吗？** 上游重构常把源码顺序类测试（`inspect.getsource` 找符号）的锚点拆散。处理方式见 test-driven-development 的结构性测试条目：用新调用图上的等价多段不变量重锚，不删测试、不降断言。

移植放宽类补丁时，上游/宿主的硬闸语义（如精确 nonce、唯一性）必须原样保住；为语义一致性改旧测试的期望值要在 commit message 写明理由，防止下轮同步时被当成漂移。

## 全量回归（本机生产盒跑法，三次白跑的教训）

生产盒内存被常驻模型压着，大套件（万级用例）串行单进程跑**必在中途无声死掉**。规矩：

- 先跑**定向文件**（本次触碰的测试）绿了才进全套。
- 别加仓库没装插件的参数——先用最短试跑看参数被不被认（`--timeout` 这类插件参数最常踩）。
- 全套用 `scripts/shard_pytest.py` 按文件切成用例数均衡的 N 片，**每片独立进程串行跑**——进程退出即资源归零，这是唯一能绕过累积爆点的办法。
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

## 验收与 push

- `git log --oneline upstream基线..HEAD` 计数 = 补丁数（语义相近的可合成一个提交，message 写明合并了哪几条）。
- 工作树零脏文件；署名必须「独立研究者」（主人署名铁律）。
- 定向绿 + 全分片失败名单**归因完毕**（每个失败分类：上游本来就红 / 我方补丁撞的 / 环境问题）才算绿，才 push 分支到 fork。
- 插件类改动 push ≠ 生效：重启宿主（gateway）后验活体（进程在、插件加载、目标链路真跑过）才叫「能正常运作」。
- **重启后必须用「重启时刻之后」的日志断言目标缺陷归零**：`systemctl show -p ActiveEnterTimestamp --value <unit>` 取时刻，只数该时刻之后的行。验收脚本要在旧进程上**全红**（它自己就是负对照），否则它的 PASS 不证明任何事。
- **重启可能揭示修复从未生效**：这时第一件事是证「进程加载的是哪一份」（模块自报 `__file__`、pyc 与源 mtime、进程解释器版本），不是换第三个假设重改代码。

## 支持文件

- `scripts/shard_pytest.py`：把 pytest 收集清单按文件切成用例数均衡的分片，输出每片的文件列表（配合上面的分片跑法）。
- `references/lcm-x-notes.md`：lcm-x 仓的 remote 拓扑、分支名、venv 路径、套件规模等运维现状——先读它再动手，滞后了当场以 git 实物为准更新它。
