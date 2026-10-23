---
name: excalidraw
description: "生成 Excalidraw 手绘风图表时使用。只要要做架构图、流程图、时序图、概念图并输出 `.excalidraw` JSON 文件，就主动加载，即使用户只说「画个流程图」。无需账号或 API key。"
version: 1.0.1
author: Hermes Agent
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Excalidraw, Diagrams, Flowcharts, Architecture, Visualization, JSON]
    related_skills: []

---

# Excalidraw 图表 Skill

通过编写标准 Excalidraw 元素 JSON 并保存为 `.excalidraw` 文件来创建图表。这些文件可拖放到 [excalidraw.com](https://excalidraw.com) 查看与编辑。无需账号、无需 API key、无需渲染库——只要 JSON。

## 何时使用

为架构图、流程图、时序图、概念图等生成 `.excalidraw` 文件。文件可在 excalidraw.com 打开，或上传获得可分享链接。

## 工作流

1. **加载本 skill**（你已经做了）
2. **编写 elements JSON** —— 一个 Excalidraw 元素对象数组
3. **保存文件**，用 `write_file` 创建 `.excalidraw` 文件
4. **可选上传**，用 `terminal` 运行 `scripts/upload.py` 获得可分享链接

### 保存图表

把你的 elements 数组包进标准 `.excalidraw` 信封，用 `write_file` 保存：

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "hermes-agent",
  "elements": [ ...your elements array here... ],
  "appState": {
    "viewBackgroundColor": "#ffffff"
  }
}
```

保存到任意路径，例如 `~/diagrams/my_diagram.excalidraw`。

### 上传获得可分享链接

通过 terminal 运行上传脚本（位于本 skill 的 `scripts/` 目录）：

```bash
python skills/creative/excalidraw/scripts/upload.py ~/diagrams/my_diagram.excalidraw
```

这会上传到 excalidraw.com（无需账号）并打印一个可分享 URL。需要 `cryptography` pip 包（`pip install cryptography`）。

---

## 元素格式参考

### 必需字段（所有元素）
`type`、`id`（唯一字符串）、`x`、`y`、`width`、`height`

### 默认值（可跳过——会自动应用）
- `strokeColor`：`"#1e1e1e"`
- `backgroundColor`：`"transparent"`
- `fillStyle`：`"solid"`
- `strokeWidth`：`2`
- `roughness`：`1`（手绘观感）
- `opacity`：`100`

画布背景为白色。

### 元素类型

**Rectangle（矩形）**：
```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 100 }
```
- `roundness: { "type": 3 }` 表示圆角
- `backgroundColor: "#a5d8ff"`、`fillStyle: "solid"` 表示填充

**Ellipse（椭圆）**：
```json
{ "type": "ellipse", "id": "e1", "x": 100, "y": 100, "width": 150, "height": 150 }
```

**Diamond（菱形）**：
```json
{ "type": "diamond", "id": "d1", "x": 100, "y": 100, "width": 150, "height": 150 }
```

**带标签的形状（容器绑定）** —— 创建一个绑定到形状的 text 元素：

> **警告：** 不要在形状上使用 `"label": { "text": "..." }`。这不是合法的
> Excalidraw 属性，会被静默忽略，产生空白形状。你*必须*
> 使用下面的容器绑定方式。

形状需要 `boundElements` 列出 text，text 需要 `containerId` 指回形状：
```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 80,
  "roundness": { "type": 3 }, "backgroundColor": "#a5d8ff", "fillStyle": "solid",
  "boundElements": [{ "id": "t_r1", "type": "text" }] },
{ "type": "text", "id": "t_r1", "x": 105, "y": 110, "width": 190, "height": 25,
  "text": "Hello", "fontSize": 20, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "r1", "originalText": "Hello", "autoResize": true }
```
- 适用于 rectangle、ellipse、diamond
- 设置 `containerId` 后，Excalidraw 会自动居中文本
- text 的 `x`/`y`/`width`/`height` 是近似值——Excalidraw 会在加载时重算
- `originalText` 应与 `text` 一致
- 始终包含 `fontFamily: 1`（Virgil / 手绘字体）

**带标签的箭头** —— 同样的容器绑定方式：
```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow",
  "boundElements": [{ "id": "t_a1", "type": "text" }] },
{ "type": "text", "id": "t_a1", "x": 370, "y": 130, "width": 60, "height": 20,
  "text": "connects", "fontSize": 16, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "a1", "originalText": "connects", "autoResize": true }
```

**独立文本**（仅标题与注释——无容器）：
```json
{ "type": "text", "id": "t1", "x": 150, "y": 138, "text": "Hello", "fontSize": 20,
  "fontFamily": 1, "strokeColor": "#1e1e1e", "originalText": "Hello", "autoResize": true }
```
- `x` 是左边缘。要在位置 `cx` 居中：`x = cx - (text.length * fontSize * 0.5) / 2`
- 不要依赖 `textAlign` 或 `width` 来定位

**Arrow（箭头）**：
```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow" }
```
- `points`：相对元素 `x`、`y` 的 `[dx, dy]` 偏移
- `endArrowhead`：`null` | `"arrow"` | `"bar"` | `"dot"` | `"triangle"`
- `strokeStyle`：`"solid"`（默认） | `"dashed"` | `"dotted"`

### 箭头绑定（把箭头连接到形状）

```json
{
  "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 150, "height": 0,
  "points": [[0,0],[150,0]], "endArrowhead": "arrow",
  "startBinding": { "elementId": "r1", "fixedPoint": [1, 0.5] },
  "endBinding": { "elementId": "r2", "fixedPoint": [0, 0.5] }
}
```

`fixedPoint` 坐标：`top=[0.5,0]`、`bottom=[0.5,1]`、`left=[0,0.5]`、`right=[1,0.5]`

### 绘制顺序（z-order）
- 数组顺序 = z-order（最前 = 底层，最后 = 顶层）
- 渐进输出：背景区 → 形状 → 其绑定文本 → 其箭头 → 下一个形状
- 不好：所有矩形，然后所有文本，然后所有箭头
- 好：bg_zone → shape1 → text_for_shape1 → arrow1 → arrow_label_text → shape2 → text_for_shape2 → ...
- 绑定的 text 元素始终紧跟其容器形状之后

### 尺寸指南

**字号：**
- 正文、标签、描述的最小 `fontSize`：**16**
- 标题与 heading 的最小 `fontSize`：**20**
- 仅次级注释的最小 `fontSize`：**14**（尽量少用）
- 绝不使用低于 14 的 `fontSize`

**元素尺寸：**
- 带标签的矩形 / 椭圆最小尺寸：120x60
- 元素之间至少留 20-30px 间隙
- 宁可少而大，不要多而碎

### 调色板

完整颜色表见 `references/colors.md`。速查：

| 用途 | 填充色 | Hex |
|-----|-----------|-----|
| 主要 / 输入 | 浅蓝 | `#a5d8ff` |
| 成功 / 输出 | 浅绿 | `#b2f2bb` |
| 警告 / 外部 | 浅橙 | `#ffd8a8` |
| 处理 / 特殊 | 浅紫 | `#d0bfff` |
| 错误 / 关键 | 浅红 | `#ffc9c9` |
| 备注 / 决策 | 浅黄 | `#fff3bf` |
| 存储 / 数据 | 浅青 | `#c3fae8`

### 技巧
- 整张图一致使用该调色板
- **文本对比度至关重要** —— 绝不要在白色背景上用浅灰。白底上文本颜色下限：`#757575`
- 不要在文本里用 emoji —— Excalidraw 的字体不渲染它们
- 深色模式图表见 `references/dark-mode.md`
- 更多示例见 `references/examples.md`


