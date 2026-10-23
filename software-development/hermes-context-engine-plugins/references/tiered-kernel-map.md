# 包装器插件实例：Tiered 的六面生命周期

这是一份「装饰器包裹型上下文引擎插件」的完整实例地图。用于审查或扩展同类插件，不是 Tiered 的发布文档。

## 文件分工

| 文件 | 角色 |
|---|---|
| `engine.py` | `TieredEngine(ContextEngine)`：token 代理、生命周期转发、存根层、`select_context`、`compress` 熔断 |
| `__init__.py` | `register(ctx)`：先注册独立能力（factcheck hooks），再装载内层引擎；失败要响亮 |
| `factcheck.py` | 可选模块：L1 正则抽断言 / L2 本地判决 / L3 软注入；不是主干 |
| `factcheck_state.py` | 每会话开关，原子写缓存 |
| `assembly_probe.py` | post_llm_call 的装配历史采样，识别摘要载体 |
| `request_probe.py` | select_context 的 wire 请求采样，看 index0/空内容/载体 |

判主干与模块，用 commit 出现顺序：先有的是引擎包装，后加的是 factcheck 与探针。只读最近改的模块会把挂件当主干。

## 六个生命周期面

| 面 | 问题 | 插件位置 |
|---|---|---|
| 装配 | 模型这次看到什么 | `select_context` 入口 |
| 压缩 | 什么被压掉、什么留下 | `prune_tool_results_only` + `compress` |
| 回插 | 摘要怎么重新进入历史 | 请求侧载体合同 |
| 披露 | 旧内容以什么粒度存在 | 存根阶梯 + 摘要指针 |
| 导向 | 模型被轻轻推向哪 | pre/post 钩子上的提示卡 |
| 证据 | 出了事能不能复盘 | 探针 + 台账 + 归档 |

## 压缩回插合同（核心）

摘要载体在 `select_context` 之前已插好。宿主可能把相邻 user 消息就地合并，导致载体被并进用户文本或产生空行。插件能做的是**只修请求、不改持久历史**：

- 载体必须是独立 `role=user` 消息；头部 `[Recent Summary (d0, node N)]` 后必须换行；正文非空。
- 被并进用户文本就拆回独立条；顺序错就按原下标稳定修复；空载体丢弃并在请求里留一行指针。
- 任何修复写进载体台账（session、turn、index、node、depth、动作、request_len），不做静默修补。
- 不重排持久历史。重排等于伪造时间线；请求侧修复是唯一安全落点。
- **首版保守实现**：原序保持、不做排序；空正文与重复 node 用指针替换该行 content（保留 row 与下标），不删行；copy-on-change。排序键与 M-02 合并拆分留 C3c/M2。
- **先钉宿主合并时序**：`_merge_consecutive_users` 相对 `select_context` 在前还是在后，决定 M-02 是「检测已合并」还是「预防再合并」。`after` 或未核验时，M-02 只能留证/`skip`，不要在请求侧硬拆；硬拆可能伪造时间线。

### 载体合同最小测试矩阵（M1）

实现 M1 前先把这些 fixture 写成红测试；请求侧只修副本，不改持久历史。

| 用例 | 输入 | 期望 |
|---|---|---|
| 正常请求 | 独立载体 + 新 user | 输出逐下标恒等，返回 None |
| 被并入用户文本 | 载体正文与 user 文本焊在一条 | 拆成两条；拆分点先冻结，判不了就 UNVERIFIED |
| 顺序错位 | d1 载体在 d0 前 | 按冻结键稳定排序（建议 depth 升、node 升），两次运行一致 |
| 空正文 | 头部后全空白 | 丢载体 + 留 node 指针；不把空行送上 wire |
| 重复 node | 同 node 两条 | 去重保一条（建议首次出现） |
| role≠user | assistant 引用了载体头部 | 不视为载体，原样透传 |
| 内联引用 | 正文里引号包住头部、无换行 | 不是载体，不拆不动 |
| 深/持久载体 | Depth-2 / Durable 头部 | 识别并按同一合同处理 |
| 多载体 | 同轮 2-5 条 | 各自独立、顺序稳定、不互相吞并 |
| copy-on-change | 任一含载体输入 | 输入 list/行 dict 不被就地改写 |
| 工具桩 | role=tool + `[tiered:` 前缀 | 不匹配载体、不被 marker sweep 误清 |

## 渐进披露阶梯

- L0 原文：最近工具结果、最近回合。
- L1 存根：旧的大结果换成「已丢弃，可重跑取回」的指针，带幂等前缀，避免二次存根。
- L2 摘要载体 + node 指针：保留可展开的检索把手。
- L3 只留索引：极旧、低再访问概率的内容。

策略必须确定性：按年龄、大小、上下文压力、再访问概率选档；不叫模型做披露决策。

## 导向总线

- 挂点：`pre_tool_call`、`post_tool_call`、`pre_llm_call`、`post_llm_call`。
- 每张卡有 id、when、text、ttl、dedupe_key；每轮最多 3 张、每张不超过 200 字、一轮过期。
- 默认只提示不阻断；硬拦只留给不可逆动作，且由主人逐项开启。
- 每轮新增模型调用必须为 0；能本地查的（卡号、路径、IP、git hash、服务名）不叫模型。

## 确定性断言检查（M3a）

- 八类：`card_id`、`path`、`ip`、`service`、`git_hash`、`number_unit`、`universal`、`completion`。
- 每类一个可注入 resolver（默认只读 kanban CLI / 文件系统 / git / systemctl）；`True/False/None` → `PASS/FAIL/UNVERIFIED`。
- `number_unit`、`universal`、`completion` 看同段证据指针：没有就 `UNVERIFIED`，不猜 `PASS`。
- 卡片构建最多 3 张、每张 ≤200 字、`ttl=1`、按 `kind:value` 去重；全 PASS 返回空。
- 本层先做库 + CLI + fixtures，不接 hook；接线留给 M3b。零模型、零风险，先把可复现的检查做出来。

**M3a 已知限制**（实现前就知道，不要当缺陷重开）：

- 绝对路径需要 `--base-dir`；空 `base_dir` 时返回 `UNVERIFIED`，是保守降级。
- IP 只查 known-host 白名单（ssh config + provider base_url），不查角色映射；`NODE II=.195` 这种已知但角色错位的案例要等 M3b 的 role→host 表。
- `number_unit` / `universal` / `completion` 是段落级启发式，同段别处有来源指针就可能 `PASS`；只做导向，不做硬判。
- 测试是一个 `test_run()` 循环 30 条 fixture；诊断粒度偏粗，扩展时优先拆成命名用例。

## 复核卡（trust card）的检查器契约

复核卡负责把回复里的路径、提交、数字挑出来，给 PASS/FAIL/UNVERIFIED 并附证据。它只做确定性检查，不是语义核验；实现时这四处容易连环假警报：

1. **hook 必须传 `base_dir`**：`on_post_llm_call` 与 `on_transform_llm_output` 都调 `check_text(response)` 时，相对路径没有可信寻址空间，全部降成 `UNVERIFIED`。hook 里从会话 workspace/repo 取根目录并显式传入；没有可信根才允许降级，且文案要写“核验器不可用”，不能写“文件不存在”。
2. **路径正则要保留相对路径**：只从 `/` 或 `~` 起匹配的 regex 会把 `tests/foo.py` 截成 `/foo.py`；即使补了 `base_dir`，也会查错位置而 FAIL。用路径 token 边界匹配，并加相对路径用例。
3. **卡片构建要保留 `status` 与 `evidence`**：`build_cards` 只保留 FAIL/UNVERIFIED 时，不能把 `CheckResult` 压成只有 `claim`；卡面必须能区分“已核验”“文件不存在”“核验器不可用”。所有 path 统一写“文件不存在”会把 resolver 缺失伪装成实物缺失，诱导改掉本来正确的路径。
4. **hash 正则要排除日期与文件名片段**：短十六进制正则会把纯数字日期串和文件名片段当 commit。用 `git cat-file -e <hash>^{commit}` 做最终判据；正则先排除纯数字 token 和已知文件名片段。

验收矩阵至少四组：相对路径存在、绝对路径缺失、纯数字日期串、真实 commit。再加一条 hook 端到端用例：用 fake ctx 捕获 `post_llm_call`/`transform_llm_output`，断言卡片带 status/evidence、相对路径不被截断、同一 turn 不重复追加 `::preview`。单体 `check_text` 全绿不能证明插件接线正确。

## 后台验证器成本审计

判决调用之外，评分管线常被忽略：

```
每条攻击 K 次采样 + 每对攻击双序各一次
= K·A + A(A−1) 次/判决
```

算例：10 次判决、33 条攻击、K=3 → 99 次采样 + 88 次双序 = 187 次评分调用；加 10 次判决 = 197 次单槽位调用。审计步骤：

1. 读归档，按 session 数判决条数与攻击条数。
2. 按上面的公式估算评分调用，标明「按代码路径估算」。
3. 读 `usage.prompt_tokens` 求判决 prompt 总量与均值。
4. 在线只留判决；评分移到离线脚本，默认关。
5. 后台任务加单飞租约，主调用在飞时丢弃本次。

## 发布前检查

- **发布由主人拍板；未获批准前只做本地匿名提交**，不建 remote、不 push，版本号与 tag 也先不动。
- `plugin.yaml` 的 homepage 不是占位符；版本与 tag 对齐。
- 默认值不写死本机模型名、endpoint、绝对路径；persona 词表走 gitignore。
- 测试基线可复跑；`hermes plugins validate` 通过；两条装载路径都打印 ACTIVE。
- profile 副本用部署脚本从主仓同步，禁止手工复制造成版本漂移。
- 发布前 `git grep` 本机绝对路径与个人信息，人工通读一遍。
