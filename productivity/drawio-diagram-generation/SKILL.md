---
name: drawio-diagram-generation
description: 要画 .drawio 图时使用。先生成后跑几何校验再真渲染目测。
version: 1.0.0
category: productivity
---

# drawio 图生成（无重叠管线）

触发：任何要产出/修 .drawio 文件的任务（流程图、逻辑链、架构图）。

本机无专用 drawio skill/tool/plugin（catalog 有 drawio-diagram-builder 未装；tool_search 两轮空）。重叠反复发生的根因：手摆坐标不跑几何校验。解药已建好：

## 管线（三步缺一不可）
1. **生成**：import `~/.hermes/scripts/drawio_kit.py` 的 `Deck`（box/text/edge/save——style 串全部生成器拼，杜绝手写引号残缺吞属性）。坐标从「布局台账」起：每类元素一个固定 y 带，节点不跨带，边只在相邻框之间或穿过声明为空的通道带。
2. **校验**：`validate(path)` 三重——vertex AABB 两两重叠、边折线 vs 非端点框相交（Liang-Barsky 裁切，exit/entry 锚点按 w/h 换算）、页边界 16px（越界直接 OUT-OF-PAGE）。必须打印 `VALIDATION: CLEAN` 才进下一步。
3. **真导出目测**：`xvfb-run -a /usr/bin/drawio -x -f png -o out.png in.drawio --no-sandbox`（2>/dev/null 吞 dbus 噪音），自己读导出图查内容级错误（豆腐块/标签错位/文字溢出），布局正确性不靠这一步兜底。

## 布局铁律（每条都对应一次真事故）
- ⚠/标记嵌入节点文字（`\n⚠B`），禁止散落独立文本节点——漂浮标签必撞框或撞线。
- 等宽 N 列居中公式 `(page - (N·W + (N-1)·gap)) / 2` 要先看总宽与页宽的关系：**框总数×宽 > 页宽时先加页宽再排**，否则首尾出页（实测抓到 -41 与 1721 两个越界框）。
- 回环边只走空白通道（单 waypoint 居中），别在通道里塞第二个元素。
- 中文标签换行用 `\n`；style 必带 `html=1;whiteSpace=wrap`。

## 校验器自身的坑
判据可疑先用「已知干净图」标定再信它：锚点把 AABB 当 (x,y,w,h) 换算过一次，12 条合规边全被误判 EDGE-CROSSES——误报风暴 = 校验器坏了，不是图坏了。kit 里 validate() 已修，动 kit 后重跑本 skill 的三步。

## 别做的事
- 不用 vision 判边距数值（黑边/letterbox 曾致误报「贴边」）；边距只信 XML 或 kit。
- 不手写整份 mxfile XML——写完才发现引号残缺、重复 id、悬空边的概率极高。
