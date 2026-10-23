---
name: baoyu-infographic
description: "生成信息图时使用。只要要做 infographic / 视觉摘要 / 高密度信息大图，或从文本、文件、URL、主题生成一张图，就主动加载，即使用户只提到「信息图」「可视化」这类词。21 种 layout × 21 种 style 可自由组合。"
version: 1.56.1
author: 宝玉 (JimLiu)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [infographic, visual-summary, creative, image-generation]
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-infographic
---

# 信息图生成器

改编自 [baoyu-infographic](https://github.com/JimLiu/baoyu-skills)，适配 Hermes Agent 的工具生态。

两个维度：**layout**（信息结构）× **style**（视觉美学）。任意 layout 可与任意 style 自由组合。

## 何时使用

当用户要求制作信息图、视觉摘要、information graphic，或使用「信息图」「可视化」「高密度信息大图」这类词时触发本 skill。用户提供内容（文本、文件路径、URL 或主题），并可选择指定 layout、style、宽高比或语言。

## 选项

| 选项 | 取值 |
|--------|--------|
| Layout | 21 种（见 Layout 画廊），默认：bento-grid |
| Style | 21 种（见 Style 画廊），默认：craft-handmade |
| Aspect | 命名：landscape (16:9)、portrait (9:16)、square (1:1)。自定义：任意 W:H 比例（例如 3:4、4:3、2.35:1） |
| Language | en、zh、ja 等 |

## Layout 画廊

| Layout | 适合 |
|--------|----------|
| `linear-progression` | 时间线、流程、教程 |
| `binary-comparison` | A vs B、前后对比、优缺点 |
| `comparison-matrix` | 多因素对比 |
| `hierarchical-layers` | 金字塔、优先级层级 |
| `tree-branching` | 分类、分类体系 |
| `hub-spoke` | 中心概念与相关项 |
| `structural-breakdown` | 爆炸视图、剖面 |
| `bento-grid` | 多主题、概览（默认） |
| `iceberg` | 表层与隐藏面 |
| `bridge` | 问题 - 解决方案 |
| `funnel` | 转化、筛选 |
| `isometric-map` | 空间关系 |
| `dashboard` | 指标、KPI |
| `periodic-table` | 分类集合 |
| `comic-strip` | 叙事、序列 |
| `story-mountain` | 情节结构、张力弧线 |
| `jigsaw` | 相互关联的部件 |
| `venn-diagram` | 重叠概念 |
| `winding-roadmap` | 旅程、里程碑 |
| `circular-flow` | 循环、周期性过程 |
| `dense-modules` | 高密度模块、数据丰富指南 |

Full definitions: `references/layouts/<layout>.md`

## Style 画廊

| Style | 描述 |
|-------|-------------|
| `craft-handmade` | 手绘、纸艺（默认） |
| `claymation` | 3D 黏土人偶、定格动画 |
| `kawaii` | 日系可爱、粉彩 |
| `storybook-watercolor` | 柔和绘画、奇想 |
| `chalkboard` | 黑板上的粉笔 |
| `cyberpunk-neon` | 霓虹光、未来感 |
| `bold-graphic` | 漫画风、半色调 |
| `aged-academia` | 复古科学、棕褐 |
| `corporate-memphis` | 扁平矢量、鲜艳 |
| `technical-schematic` | 蓝图、工程 |
| `origami` | 折纸、几何 |
| `pixel-art` | 复古 8-bit |
| `ui-wireframe` | 灰阶界面 mockup |
| `subway-map` | 交通线路图 |
| `ikea-manual` | 极简线稿 |
| `knolling` | 有序平铺 |
| `lego-brick` | 玩具积木搭建 |
| `pop-laboratory` | 蓝图网格、坐标标记、实验级精度 |
| `morandi-journal` | 手绘涂鸦、温暖莫兰迪色调 |
| `retro-pop-grid` | 1970 年代复古波普艺术、瑞士网格、粗描边 |
| `hand-drawn-edu` | 马卡龙粉彩、手绘抖动、火柴人 |

Full definitions: `references/styles/<style>.md`

## 推荐组合

| 内容类型 | Layout + Style |
|--------------|----------------|
| 时间线 / 历史 | `linear-progression` + `craft-handmade` |
| 分步操作 | `linear-progression` + `ikea-manual` |
| A vs B | `binary-comparison` + `corporate-memphis` |
| 层级 | `hierarchical-layers` + `craft-handmade` |
| 重叠 | `venn-diagram` + `craft-handmade` |
| 转化 | `funnel` + `corporate-memphis` |
| 循环 | `circular-flow` + `craft-handmade` |
| 技术 | `structural-breakdown` + `technical-schematic` |
| 指标 | `dashboard` + `corporate-memphis` |
| 教育 | `bento-grid` + `chalkboard` |
| 旅程 | `winding-roadmap` + `storybook-watercolor` |
| 分类 | `periodic-table` + `bold-graphic` |
| 产品指南 | `dense-modules` + `morandi-journal` |
| 技术指南 | `dense-modules` + `pop-laboratory` |
| 潮流指南 | `dense-modules` + `retro-pop-grid` |
| 教育图示 | `hub-spoke` + `hand-drawn-edu` |
| 流程教程 | `linear-progression` + `hand-drawn-edu` |

默认：`bento-grid` + `craft-handmade`

## 关键词快捷方式

当用户输入包含这些关键词时，**自动选择**关联的 layout，并在第 3 步把关联 style 作为首选推荐。命中的关键词跳过基于内容的 layout 推断。

若某个快捷方式有 **Prompt Notes**，把它们作为附加样式说明追加到生成的 prompt（第 5 步）中。

| 用户关键词 | Layout | 推荐 Style | 默认 Aspect | Prompt Notes |
|--------------|--------|--------------------|----------------|--------------|
| 高密度信息大图 / high-density-info | `dense-modules` | `morandi-journal`, `pop-laboratory`, `retro-pop-grid` | portrait | — |
| 信息图 / infographic | `bento-grid` | `craft-handmade` | landscape | 极简：干净画布、充足留白、无复杂背景纹理。只用简单卡通元素与图标。 |

## 输出结构

```
infographic/{topic-slug}/
├── source-{slug}.{ext}
├── analysis.md
├── structured-content.md
├── prompts/infographic.md
└── infographic.png
```

Slug：从主题取 2-4 个词的 kebab-case。冲突时追加 `-YYYYMMDD-HHMMSS`。

## 核心原则

- 忠实保留源数据——不摘要、不改写（但在写入输出前**清除任何凭证、API key、token 或密钥**）
- 在组织内容前先定义学习目标
- 为视觉传达而组织（标题、标签、视觉元素）

## 工作流

### 第 1 步：分析内容

**加载参考**：阅读本 skill 的 `references/analysis-framework.md`。

1. 保存源内容（文件路径或粘贴 → 用 `write_file` 写入 `source.md`）
   - **备份规则**：若 `source.md` 已存在，重命名为 `source-backup-YYYYMMDD-HHMMSS.md`
2. 分析：主题、数据类型、复杂度、语气、受众
3. 检测源语言与用户语言
4. 从用户输入中提取设计指令
5. 把分析存入 `analysis.md`
   - **备份规则**：若 `analysis.md` 已存在，重命名为 `analysis-backup-YYYYMMDD-HHMMSS.md`

详细格式见 `references/analysis-framework.md`。

### 第 2 步：生成结构化内容 → `structured-content.md`

把内容转成信息图结构：
1. 标题与学习目标
2. 各章节含：核心概念、内容（逐字）、视觉元素、文字标签
3. 数据点（所有统计 / 引文精确照抄）
4. 来自用户的设计指令

**规则**：仅 Markdown。不新增信息。忠实保留数据。从输出中清除任何凭证或密钥。

详细格式见 `references/structured-content-template.md`。

### 第 3 步：推荐组合

**3.1 先查关键词快捷方式**：若用户输入命中**关键词快捷方式**表中的关键词，自动选择关联 layout，并优先把关联 style 作为首选推荐。跳过基于内容的 layout 推断。

**3.2 否则**，基于以下推荐 3-5 个 layout×style 组合：
- 数据结构 → 匹配的 layout
- 内容语气 → 匹配的 style
- 受众预期
- 用户的设计指令

### 第 4 步：确认选项

用 `clarify` 工具与用户确认选项。由于 `clarify` 一次只处理一个问题，先问最重要的：

**Q1 —— 组合**：给出 3+ 个 layout×style 组合及理由。让用户选一个。

**Q2 —— Aspect**：询问宽高比偏好（landscape/portrait/square 或自定义 W:H）。

**Q3 —— Language**（仅当源语言 ≠ 用户语言）：询问文本内容该用哪种语言。

### 第 5 步：生成 Prompt → `prompts/infographic.md`

**备份规则**：若 `prompts/infographic.md` 已存在，重命名为 `prompts/infographic-backup-YYYYMMDD-HHMMSS.md`

**加载参考**：读取所选 layout 的 `references/layouts/<layout>.md` 与 style 的 `references/styles/<style>.md`。

组合：
1. 来自 `references/layouts/<layout>.md` 的 layout 定义
2. 来自 `references/styles/<style>.md` 的 style 定义
3. 来自 `references/base-prompt.md` 的基础模板
4. 第 2 步的结构化内容
5. 全部文本用已确认的语言

`{{ASPECT_RATIO}}` 的**宽高比解析**：
- 命名预设 → 比例字符串：landscape→`16:9`、portrait→`9:16`、square→`1:1`
- 自定义 W:H 比例 → 原样使用（例如 `3:4`、`4:3`、`2.35:1`）

用 `write_file` 把拼好的 prompt 保存到 `prompts/infographic.md`。

### 第 6 步：生成图片

用第 5 步拼好的 prompt 调用 `image_generate` 工具。

- 把宽高比映射到 image_generate 的格式：`16:9` → `landscape`、`9:16` → `portrait`、`1:1` → `square`
- 自定义比例选最接近的命名 aspect
- 失败时自动重试一次
- 把生成的图片 URL / 路径保存到输出目录

### 第 7 步：输出总结

报告：主题、layout、style、aspect、语言、输出路径、创建的文件。

## 参考文档

- `references/analysis-framework.md` —— 分析方法论
- `references/structured-content-template.md` —— 内容格式
- `references/base-prompt.md` —— Prompt 模板
- `references/layouts/<layout>.md` —— 21 个 layout 定义
- `references/styles/<style>.md` —— 21 个 style 定义

## 易错点

1. **数据完整性至上** —— 绝不摘要、改写或篡改源统计数字。「增长 73%」必须保持「增长 73%」，不能变成「显著增长」。
2. **清除密钥** —— 写入任何输出文件前，始终扫描源内容中的 API key、token 或凭证。
3. **每节一个信息** —— 每个信息图章节应传达一个清晰概念。章节塞太多会降低可读性。
4. **风格一致** —— 参考文件中的 style 定义必须贯穿整张信息图一致应用。不要混用 style。
5. **image_generate 的宽高比** —— 该工具只支持 `landscape`、`portrait`、`square`。`3:4` 这类自定义比例应映射到最接近的选项（此处为 portrait）。
