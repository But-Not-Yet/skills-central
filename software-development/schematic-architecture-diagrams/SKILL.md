---
name: schematic-architecture-diagrams
description: 用脚本生成函数级电路图式架构图（drawio/SVG/HTML）时加载。
version: 1.0.0
author: Nekonya (小喵), Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [diagram, architecture, drawio, svg, routing, visualization]
    related_skills: [deep-code-review, hermes-context-engine-plugins]
---

# 函数级电路图式架构图生成

## When to Use（何时用）

- 主人要「系统架构图」「函数级」「电路图式」「多级包含关系」「有向箭头表示连接和依赖」。
- 要改已有架构图（加模块、改分区、调布线）。
- 要交付 drawio / SVG / HTML 三件套，或只要其中一件。

## 核心判据：主人要的是「电路图」，不是「流程图」

- **模块当 IC**：每个叶子盒子是集成电路，不是流程节点。盒子是硬障碍物，走线必须绕开它们。
- **走线不重叠**：两条线不能共线（同一条线段上跑两根线）。交叉可以，重叠不行。
- **有向箭头**：箭头方向 = 数据/控制流向，不是「关系」这种模糊说法。
- **多级包含**：容器套容器（zone → sub-group → leaf），层级必须一眼看出来。

## 工序（脚本生成，不靠手画）

1. **定分区**：先列 zone（大背景框），再列 sub-group（分区内小组），最后列 leaf（函数/文件级盒子）。每个 zone 给颜色 + 标题。
2. **画盒子**：`d.box(id, x, y, w, h, label, parent_container, color)`。label 写「文件名 · 函数名」这种双段式。
3. **布线**：`d.edge(eid, src, dst, label, color, dashed)`。脚本用 A* 在 10px 网格上走 Manhattan 折线，把叶子盒子当硬障碍物。
4. **校验**：跑 `validate()`，要求 `LEAF VALIDATION: CLEAN`（盒子无重叠、无出界）。
5. **导出**：drawio（`mxfile` XML）→ SVG（原生或 `xvfb-run drawio -x -f svg`）→ HTML（自包含报告，含图例/读图顺序/文件函数索引）。

已有生成器脚本参考：`gen_tiered_arch.py`（Tiered 项目，约 986 行，含 A* 布线、SVG 渲染、HTML 包装）。

## 布线的硬规则（踩过的坑）

- **`orthogonalEdgeStyle` 不避中间障碍**。drawio 自带的这个样式只避源/目标两个框，不避中间盒子。要真正避障，必须在脚本里自己算路径、把折点写成显式 waypoint。
- **密集布局下调惩罚项不降交叉数**。给「线复用」加惩罚、给端口加分槽，实测都让交叉从 48 涨到 66/69。原因是惩罚让线绕远路、从不同偏移出发反而制造新交叉。**密度才是约束**，不是惩罚权重。要真降交叉，得改布局（拉稀疏盒子、换层次化布局 Sugiyama），不是调参。
- **交叉 ≠ 重叠**。电路图里交叉是标准画法（`jumpStyle=arc` 画小桥，表示不连通）。重叠（两根线共线段）才是缺陷。校验时分开统计，别把交叉当失败。
- **sub-group 标题不能当硬障碍物**。只有 zone 标题（`z_` 前缀）要当障碍；sub-group 标题只是标签，堵住它会让顶侧端口不可达，产生 NOPATH。
- **端口偏移点落在框外**。`_port()` 返回 `x2 + margin + 1`，是框外 6px 的点，不是框体边缘的端口。要真端口，得改成框边上的点并加分槽。

## 校验指标

- `LEAF VALIDATION: CLEAN` — 叶子盒子无重叠、无出界。
- `ROUTE FAILURES` — 布线失败（NOPATH）的边清单。有失败要逐条看起点/终点是否被障碍堵死。
- `EDGE CROSSINGS: N` — 交叉数，质量指标，不是失败判据。

## 交付物

- `.drawio` — 可编辑源件（mxfile XML），带正交边与跨线小桥。
- `.svg` — 原生矢量，可直接嵌入 HTML。
- `.html` — 自包含报告，含图例、读图顺序、文件/函数索引表。
- `_netlist.md` — 网表，可读、可脚本比对。

## 铁律

- **先跑脚本再报数**。不靠看图验收，靠 `validate()` 的机械输出。
- **改脚本前先备份**。布线参数调错了会让交叉数暴涨，改完立刻跑一遍对比数字。
- **M3c/检察官这类「同目标不同层」的模块，画成总线**：确定性层（零模型）→ 可选语义层（有模型）→ 单一记录 → 渲染器。不要画成两个平行盒子。
