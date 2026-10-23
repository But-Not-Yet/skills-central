# lcm-x 仓运维现状（as-of 2026-10-18，动 git 前先实物复核，滞后就以 git 为准改这份）

- 本地路径：`~/.hermes/plugins/hermes-lcm-x`（宿主以包名 `hermes_lcm` 注册，测试经 `tests/conftest.py` 自注册）。
- 测试解释器：`~/.hermes/hermes-agent/venv/bin/python`（是 `venv` 不是 `.venv`）。pytest 无 timeout 插件，别传 `--timeout`。
- remote：`fork` = `git@github.com:But-Not-Yet/lcm-x.git`（推送走 `~/.ssh/id_ed25519_github`，IdentitiesOnly），`upstream` = `https://github.com/electricsheephq/lcm-x`（MIT）。旧基线 tag `legacy-0.26.0-private`。
- 生产分支：`f-0.28.0-prod`（fork/main 切出 + 本地补丁队列）；master 留旧版。
- 套件规模：~15k 用例 / tests/ 下 40+ 文件；串行单进程 ~75 分钟且跑不完（内存压力），必须 `scripts/shard_pytest.py` 分片，分片间资源归零。
- 关键背景：宿主 `_merge_consecutive_users` 与 LCM 的 user-role summary carrier 交互是线上症状的根因面；上游有对应 issue 图纸但排期在 Backlog，我方在 fork 上自修。上游对摘要契约做过多轮重写（缺闭合标签容差、reasoning 头拦截等），移植我方摘要补丁前先 `git grep` 新树看哪些语义已被吸收。
- v0.27→v0.28 声明不动存储 schema，升级/回滚是插件级——lcm.db 不需要迁移。
