---
name: project-debt-ledger
version: 1.0.0
author: Nekonya (小喵)
license: MIT
description: "进入项目、承诺任务、结算欠账时使用：项目根欠账文件的读写约定。"
metadata:
  hermes:
    tags: [process, project-discipline, debt]
    related_skills: [engineering-workflow-loop, unattended-mission-planning]
---

# 项目欠账账本（跨项目约定）

## When to Use
进入任何项目干活之前；本轮答应了但没做完的事；欠账结算时。主人裁定（2026-10-06）：每个项目根目录放一份欠账文件，新会话进项目先读它。

## 约定
- **位置与命名**：项目根一份，`欠账与必读_YYYYMMDD.md`（建档后原地更新，不另起新档）。分节：欠账 / 已结算 / 生产安排（可选）。
- **开局强制读取**：新会话在某项目里开工前，先读该项目的欠账文件，再动手。这是「回头提醒我补」不失踪的唯一机制。
- **写入义务**：任何口头承诺而本轮未落盘的任务，当场写进该项目的欠账文件——「要做的」跨轮未落即成欠账（与 marker-probe-experiments 的当轮落盘规则同源）。
- **结算**：做完移入「已结算」节，带时间戳与产物指针，不删行——结算记录本身是审计线索。
- **归属**：任务属于哪个项目就记在哪个项目；跨项目共用的状态（运维、环境）住 `运维状态_*.md`，不进欠账。

## 现有账本
- `~/Documents/Hermes/欠账与必读_20261006.md`（Hermes 工作区根：深库沙箱、生产尾巴）
- `~/Documents/Hermes/灵感笔记调研_20260929/欠账与必读_20261005.md`（标记研究项目）
- `~/Documents/UPenn/欠账与必读_20261006.md`（课业根：课程状态、选课账本、Silvaco 作业）
- 新项目开工时按上述约定新建。