# 外部依据对照（检索于 2026-10-05，来源限定：arXiv / QS 前 50 大学公开课件 / 教材）

本 skill 的核心论点与下列合格来源对照。小喵的 P4 经历是这些原则的反面例证。

## 1. 工程与设计科学的分野 — arXiv:2501.07195（已读摘要）

Mendez, Avgeriou, Kalinowski, bin Ali, *Teaching Empirical Research Methods in Software Engineering* (2025)，Springer 手册编者导言。
- 要点（摘要大意）：软件工程的大量知识传统上根植于 rationalist 论证与 design-science（设计导向）。empirical SE（受控实证研究）是后来才确立的「科学实践」标准。「造出可用的东西」与「用受控研究裁决知识」是学科内明确区分的两条路。
- 对应：第 0 步物种判定。两物种不共用任务书。
- 链接：https://arxiv.org/abs/2501.07195

## 2. 不确定环境下的工程决策与柔性设计 — MIT OCW ESD.71《Engineering Systems Analysis for Design》(de Neufville, Fall 2008，已读 syllabus)

- 要点（课程主页原文大意）：未来必然不确定，好设计 = 在整个可能场景范围内交付价值。柔性设计让运营者保留「规避下行风险、抓住上行机会」的调整余地。案例显示柔性设计平均提升约 25% 期望表现。先修课 ESD.70J《Engineering Economy Module》讲长期项目估值与「一次建大 vs 增量开发」的权衡。
- 对应：工程规矩 3（禁用开关 = 柔性设计的最低成本形态——一行配置的回滚权就是保留的期权）。规矩 2（增量交付优于一次追最优）。
- 链接：https://ocw.mit.edu/courses/esd-71-engineering-systems-analysis-for-design-fall-2008/

## 3. Satisficing（够用即止）— Herbert Simon

- 出处等级：教材级概念（Simon《Administrative Behavior》1947/1997。经济学与工程管理教材普遍收录）。概念核心：搜索最优解所需的信息成本本身是成本，到达接受阈值即停是理性行为。
- 状态标注：**教材原文未逐字核**，按公认概念引用。写进正式文档需回教材页码。
- 对应：工程规矩 2。P4 教训 = 为测一个不需要测的数修了三轮仪器。

## 小喵的对照反思

P4 逐条命中反模式：验收里混入归因断言（违反 1 的分野）、为归因修仪器三轮（违反 3）。每轮修订合规但问题没人要（违反 2 的「价值来自场景适应而非完美」）。若当时有禁用开关思维，第一轮就该收：装得上、不坏事 → 交付。主人觉得没改善 → 禁用 → 反馈驱动下一版。三个通宵的仪器维修费，本可以是一句「主人觉得没用吗？」。
