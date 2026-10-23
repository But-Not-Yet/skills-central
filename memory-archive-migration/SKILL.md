---
name: memory-archive-migration
version: 1.0.0
author: Nekonya (小喵)
license: MIT
description: "memory/USER 逼近上限或主人说「归档迁移」时使用：瘦身迁移流程。"
metadata:
  hermes:
    tags: [hermes, memory, maintenance]
    related_skills: [project-debt-ledger, hermes-local-ops-troubleshooting]
---

# 记忆归档迁移（memory 瘦身）

## When to Use
memory 或 USER 画像逼近字符上限（≥90%）、新条目加不进去、或主人说「归档迁移」时。首轮全量迁移：2026-10-06。

## 去留三问（每条逐项过）
1. **这条不在脑子里，会不会在某轮对话里出错？** 会 → 留（人格铁律、主人稳定画像、环境底层事实）。
2. **是干活才用的规程？** → 迁对应 skill（按需加载，不占每轮注入）。
3. **是任务状态或易变运维？** → 迁项目根文档（欠账文件 / 运维状态文件），memory 只留一行指针或删除。

## 流程
1. 盘点：逐条列出现存条目，按三问分类，先给主人过目清单（他点头才动）。
2. **先落盘后删**：目标位置（skill patch / 文档）写成功并验证，才从 memory 删——顺序反了会两头落空。
3. 验证：memory/USER 余量下降、目标 skill 可加载、落盘文件可读。
4. 台账：迁移记录写进相关项目的欠账文件「已结算」节。

## 工具陷阱（2026-10-06 实录）
- skill_manage 一次批量塞多份完整 SKILL.md（create）会把单次 tool call 膨胀到数万 token，触发界面截断与用户侧中断——**大写入拆成多次调用**，一次一个 create 或只放 patch 级小改。
- 迁移中途被打断时，先盘点「已落盘 vs 已删除」两个集合再续做——本次实际顺序是「先落盘、后删 memory」，中断点恰好停在安全侧（两头都有），续做只需删 memory 一侧。

## 常设规则
- 新条目写入前先过三问——源头把关，不再攒到 99% 才搬家。
- 深库（外部 memory provider）是**缓行决定**：触发条件 = 瘦身后再次溢出（2026-10-06 裁定）。方案与判据见 Hermes 根欠账文件。