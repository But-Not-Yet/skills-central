---
name: architecture-diagram
description: "画深色科技风架构图时使用。只要要做系统 / 云基础设施 / 微服务拓扑的 SVG+HTML 图，就主动加载，即使用户只说「画个架构图」。不用于科学插画、平面图、手绘白板（考虑 excalidraw）。"
version: 1.0.0
author: Cocoon AI (hello@cocoon-ai.com), ported by Hermes Agent
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, diagrams, SVG, HTML, visualization, infrastructure, cloud]
    related_skills: [concept-diagrams, excalidraw]
---

# 架构图 Skill

生成专业、深色主题的技术架构图，输出为带内联 SVG 图形的独立 HTML 文件。无需外部工具、无需 API key、无需渲染库——只需写出 HTML 文件并在浏览器中打开。

## 适用范围

**最适合：**
- 软件系统架构（前端 / 后端 / 数据库分层）
- 云基础设施（VPC、region、subnet、托管服务）
- 微服务 / service-mesh 拓扑
- 数据库 + API 映射图、部署图
- 任何适合深色网格背景美学的技术基础设施主题

**优先考虑其他 skill 的情况：**
- 物理、化学、数学、生物等科学主题
- 实体对象（载具、硬件、解剖、剖面）
- 平面图、叙事流程、教育 / 教科书风格可视化
- 手绘白板草图（考虑 `excalidraw`）
- 动画讲解（考虑动画类 skill）

若该主题有更专门的 skill 可用，优先使用它。若没有合适的，本 skill 也可作为通用 SVG 图表的兜底——只是输出会带上下文描述的深色科技美学。

基于 [Cocoon AI 的 architecture-diagram-generator](https://github.com/Cocoon-AI/architecture-diagram-generator)（MIT）。

## 工作流

1. 用户描述其系统架构（组件、连接、技术栈）
2. 按下方设计系统生成 HTML 文件
3. 用 `write_file` 保存为 `.html` 文件（例如 `~/architecture-diagram.html`）
4. 用户在任意浏览器中打开——离线可用，无依赖

### 输出位置

将图表保存到用户指定路径，或默认保存到当前工作目录：
```
./[project-name]-architecture.html
```

### 预览

保存后，建议用户打开它：
```bash
# macOS
open ./my-architecture.html
# Linux
xdg-open ./my-architecture.html
```

## 设计系统与视觉语言

### 调色板（语义映射）

用特定的 `rgba` 填充与十六进制描边来区分组件类别：

| 组件类型 | 填充 (rgba) | 描边 (Hex) |
| :--- | :--- | :--- |
| **前端** | `rgba(8, 51, 68, 0.4)` | `#22d3ee` (cyan-400) |
| **后端** | `rgba(6, 78, 59, 0.4)` | `#34d399` (emerald-400) |
| **数据库** | `rgba(76, 29, 149, 0.4)` | `#a78bfa` (violet-400) |
| **AWS/云** | `rgba(120, 53, 15, 0.3)` | `#fbbf24` (amber-400) |
| **安全** | `rgba(136, 19, 55, 0.4)` | `#fb7185` (rose-400) |
| **消息总线** | `rgba(251, 146, 60, 0.3)` | `#fb923c` (orange-400) |
| **外部** | `rgba(30, 41, 59, 0.5)` | `#94a3b8` (slate-400) |

### 字体与背景
- **字体：** JetBrains Mono（等宽），从 Google Fonts 加载
- **字号：** 12px（名称）、9px（副标签）、8px（注释）、7px（微标签）
- **背景：** Slate-950（`#020617`），叠加细微的 40px 网格图案

```svg
<!-- Background Grid Pattern -->
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
</pattern>
```

## 技术实现细节

### 组件渲染
组件是圆角矩形（`rx="6"`），1.5px 描边。为防止箭头透过半透明填充显示出来，使用**双矩形遮罩技巧**：
1. 先画一个不透明背景矩形（`#0f172a`）
2. 再在其上画半透明样式矩形

### 连接规则
- **Z 顺序：** 在 SVG 中*尽早*绘制箭头（网格之后），使其渲染在组件框下方
- **箭头：** 通过 SVG marker 定义
- **安全流向：** 使用 rose 色（`#fb7185`）的虚线
- **边界：**
  - *安全组：* 虚线（`4,4`），rose 色
  - *Region：* 大间距虚线（`8,4`），amber 色，`rx="12"`

### 间距与布局逻辑
- **标准高度：** 60px（服务）；80-120px（大型组件）
- **垂直间距：** 组件之间至少 40px
- **消息总线：** 必须放在服务之间的*间隙*中，不得与它们重叠
- **图例位置：** **关键。** 必须放在所有边界框之外。计算所有边界的 Y 坐标最小值，把图例放在其下方至少 20px 处。

## 文档结构

生成的 HTML 文件采用四段式布局：
1. **Header：** 标题，带脉动圆点指示器与副标题
2. **主 SVG：** 图表位于一个圆角边框卡片内
3. **摘要卡片：** 图表下方三张卡片组成的网格，用于概述高层信息
4. **Footer：** 极简元数据

### 信息卡片模式
```html
<div class="card">
  <div class="card-header">
    <div class="card-dot cyan"></div>
    <h3>Title</h3>
  </div>
  <ul>
    <li>• Item one</li>
    <li>• Item two</li>
  </ul>
</div>
```

## 输出要求
- **单文件：** 一个自包含的 `.html` 文件
- **无外部依赖：** 所有 CSS 与 SVG 必须内联（Google Fonts 除外）
- **无 JavaScript：** 任何动画（如脉动圆点）都用纯 CSS 实现
- **兼容性：** 必须在任何现代浏览器中正确渲染

## 模板参考

加载完整 HTML 模板以获取确切结构、CSS 与 SVG 组件示例：

```
skill_view(name="architecture-diagram", file_path="templates/template.html")
```

模板包含每种组件类型（前端、后端、数据库、云、安全）、箭头样式（标准、虚线、曲线）、安全组、region 边界与图例的可用示例——生成图表时把它作为结构参考。
