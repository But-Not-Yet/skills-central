# ARFIMA / 行为长记忆提案审查 — 实战案例知识库

会话：2026-08 对《分数阶组织动力学：ARFIMA状态空间框架...》（v1.0 → v2.1）的完整审查。以下发现可推广到任何"行为计数 + 长记忆"类研究。

## Python ARFIMA 生态现实（工具链空白）
- `statsmodels` 无 ARFIMA；其 `ARIMA/SARIMAX` 的 `d` 仅支持整数。
- PyPI `fracdiff` 仅提供分数阶差分算子——无 MLE、无 GPH。
- `fracdiff`（CRAN，Martin Maechler，v1.5-3）是 R 包；`forecast::arfima` 也是 R。Python 需自实现：GPH = FFT → 周期图 → 低频 log-log 回归（50–100 行）；Whittle MLE = 最小化 Σ[log f(ω_j) + I(ω_j)/f(ω_j)]。
- 自实现并开源（MIT）可把生态空白转化为贡献：工具贡献 + 可复现性证据。
- ROCm/GPU 不是瓶颈：ARFIMA 估计是低维优化（2–4 参数），CPU 并行（Joblib）+ numba 足以应付 5000 序列批量。GPU 只对 ABM 仿真和 LSTM 基线有意义。论文中须诚实声明，避免审稿人"加速表演"批评。

## GH Archive / BigQuery 数据事实
- 数据集总量 ≈17TB（2011–2025）。BigQuery 免费额度 = 每月 1TB 扫描；7 年 `day.*` 全扫描约 2.5–7TB → 1–2 次查询即耗尽。缩至 3 年或哈希抽样；写明成本上限（如 $50；GCP 新用户 $300 额度可覆盖）。
- 事件语义：`COUNTIF(type='PushEvent')` 计数的是 push 次数 ≠ commit 数——真实 commit 数是 `JSON_EXTRACT_SCALAR(payload, '$.size')`（该次 push 包含的 commit 数）。`PullRequestEvent` 含 opened/closed/merged → 过滤 `payload.action = 'opened'`。
- Bot 污染：第一层 `actor.login NOT LIKE '%[bot]'`；第二层已知 bot 名单（dependabot[bot]、renovate[bot]、github-actions[bot]、greenkeeper[bot]、snyk-bot、codecov[bot]…）。Bot 没有"离职"行为 → 会摧毁流失研究。
- 中位开发者周度 commit 计数 >90% 为零 → 零膨胀陷阱（见下）。日尺度 vs 周尺度对比应作稳健性检查（周聚合还会削弱 burst 动力学——恰是分数阶模型要捕捉的信号）。

## 零膨胀 → 伪长记忆（生死关陷阱）
- 文献：Saha 2020 "Pitfalls in long memory research"（Cogent Econ & Finance）——GPH 在此类数据上可系统性偏差；Granger & Hyung 2004 "Occasional structural breaks and long memory"——偶发机制切换可模仿长记忆。
- 推荐零模型对照设计（个体层面）：(1) 拟合两阶段零模型（Bernoulli 活跃/非活跃状态 + 活跃期 ARMA 强度）；(2) 模拟 ~500 条匹配零占比/边际分布的对照序列；(3) 真实 vs 对照分别 GPH；(4) 判定：真实拒绝率显著 > 对照拒绝率（置换检验 p<0.05）⇒ d>0 非伪迹。同时报告 H0 size（名义水平 ±0.02 内）、BH-FDR 控制（q<0.05）、功效曲面整体形态。
- 个体层面先行：Granger (1980) 截面聚合——异质短记忆个体聚合出伪长记忆。群体/子群体分析仅作探索性。

## 功效分析数字（短序列）
- n = 52–104 周观测时 GPH SE ≈ 0.15–0.25。
- 真实 d=0.3、SE≈0.2 ⇒ 单个体检验功效 ≈ 30–45%。
- 后果：「>40% 个体显著 d>0」这类门槛在记忆真实存在时也可能**统计不可达**——是设计缺陷而非科学结论。
- 修法：在（序列长度 × 真实 d × 零占比）网格上模拟功效曲面；按预期数据形态取功效 ≥0.8 的阈值为 τ*；数据检验前预注册冻结；功效曲线本身作为方法论贡献发表（备选预案：≥78 周序列、双周聚合）。

## 需仿真验证的映射断言（α↔d↔H）
- Caputo 阶次 α、Hurst H、ARFIMA d 三者无普适等价。标准结论：fGn 增量 d = H − 1/2。α↔d 仅在特定离散化方案下成立（Comte & Renault 1998 特定条件）。标为"先在 ABM 仿真验证的假设"（估计 d̂ 随设定 α 的单调性）；不成立则删除连续-离散统一叙事，保留纯离散 ARFIMA。
- ABM 模拟器：L1 scheme 全历史卷积为 O(T²)——「1000 agents × 104 周 < 10 秒」不成立。模拟器须先对 Mittag-Leffler 解析解做数值验证；缩减到 ~200 agents 或用短记忆截断（保留最近 L=52 步）/ FFT 卷积。

## 审稿人预期管理
- 5 项"首次/首创"收敛为 3 项核心贡献（如：大规模个体层面实证 + 开源可复现工具包 + Diebold-Mariano 正式预测比较）。
- 加"本文不声称的创新"小节（不发明新估计器、不证新收敛定理）。
- 两篇论文策略：第一篇 = 聚焦实证（结果中等先 arXiv，结果强直投期刊）；第二篇 = 完整控制框架（状态空间+Kalman+MPC+TE）+ 企业真实数据（合同授权）→ DSS/EJOR 层级。MPC 工程障碍须点名：无限记忆核需 Oustaloup 有理逼近、在线实时求解、干预执行闭环。

## 使修订后提案可信的参考文献补充
- [A1] Andrews & Guggenberger (2003) bias-reduced GPH —— 替代朴素 GPH。[A2] Granger & Hyung (2004)。[A3] Bai & Perron (1998/2003) 结构断点。[A4] Saha (2020) 长记忆陷阱。[A5] Diebold & Mariano (1995) 预测比较检验。

## v2.1 重构地图（修订后提案长什么样）
0. 诚实空白声明 + "本文不声称的创新" → 1. 预注册假设（功效反推 τ*、零膨胀防御、聚合警告）→ 2. 文献表加"采用/改进/未使用"列 → 3. 理论中 α↔d 标为待验证假设 → 4. 修正 SQL + 3 年范围 + 成本上限 + 数据质量报告（非零周 >30%、bot 残留 <5%）→ 5. Python 自实现工具链 + 诚实 ROCm 边界 + 分段平稳 pipeline → 6. Phase 0 四面墙 / Phase 1 核心 / Phase 2 稳健性+投稿 → 7. 24 周时间线 → 8. 区间化预期 + 最小发表标准 + 扩展风险表 → 参考文献 A1–A5 → 附录（框架预告、工具包结构、数据可用性）。

## 修订后验证清单（grep 残留扫描）
- [ ] 旧武断阈值（如 ">40%"）无残留（仅允许作为"已被功效分析替代"的说明出现）
- [ ] 不可运行 import（`from fracdiff`、`statsmodels.tsa.arfima`）无残留
- [ ] 旧数据范围（7 年/2019 起始）无残留
- [ ] 旧时间线（16 周）无残留
- [ ] 旧 SQL 错误（PushEvent 当 commits）无残留
- [ ] 强"首次/首创"声明无残留
- [ ] 参数等价断言（d=1−α）已标为待验证假设
- [ ] 旧投稿目标（"DSS 首选"）已改为条件化策略
