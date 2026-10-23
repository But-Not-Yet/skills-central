---
name: sketch
description: "快速做可丢弃的 HTML 设计草案时使用。只要要一次给出 2-3 个 UI 变体做并排比较（「先看几个方向」「A 和 B 哪个好」），就主动加载。即使用户只说「草拟个界面」。不用于要交付的生产级组件或成品页（考虑 claude-design）。"
version: 1.0.1
author: Hermes Agent (adapted from gsd-build/get-shit-done)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [sketch, mockup, design, ui, prototype, html, variants, exploration, wireframe, comparison]
    related_skills: [spike, claude-design, popular-web-designs, excalidraw]
---

# Sketch

当用户想在**投入之前先看设计方向**时使用本 skill——以可丢弃的 HTML 草案探索 UI/UX 想法。重点在于生成 2-3 个可交互变体，让用户并排比较视觉方向，而非产出可直接交付的代码。

当用户说「草拟这个界面」「给我看看 X 可能长什么样」「比较布局 A 和 B」「这个 UI 给我 2-3 版」「让我看几个变体」「动手做之前先 mockup 一下」这类话时加载本 skill。

## 何时不要用

- 用户要生产级组件——用 `claude-design`，或正经实现
- 用户要精致的一次性 HTML 制品（落地页、演示）——用 `claude-design`
- 用户要图表——用 `excalidraw`、`architecture-diagram`
- 设计已经定下——直接实现即可

## 若用户装了完整的 GSD 系统

若 `gsd-sketch` 作为同级 skill 出现（通过 `npx get-shit-done-cc --hermes` 安装），你可以用 **`gsd-sketch`** 获得更完整的工作流。带 MANIFEST 的持久化 `.planning/sketches/`、frontier mode 分析、跨历次 sketch 的一致性审计，以及与 GSD 其余部分的集成。本 skill 是轻量独立版——一次性草拟，不带状态机制。

> **注意：** 上游 GSD 项目（[gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)）在 GitHub 上已**归档 / 不再维护**。npm 包（`get-shit-done-cc`）仍可安装，但请把它当作一个已归档的社区项目。这个独立的 `sketch` skill 才是维护中的路径，无需额外依赖。

## 核心方法

```
intake  →  variants  →  head-to-head  →  pick winner (or iterate)
```

### 1. 需求收集（若用户已给足信息则跳过）

生成变体前，先拿到三样东西——一次问一个，别一股脑全问：

1. **感觉。** 「它该给人什么感觉？形容词、情绪、氛围。」——*「平静、编辑风、像 Linear」*比*「极简」*信息量大得多。
2. **参考。** 「哪些应用、网站或产品捕捉到了你想象中的感觉？」——真实参考胜过抽象描述。
3. **核心动作。** 「用户在这个界面上做的最重要的一件事是什么？」——所有变体都应很好地服务于此。否则它们只是装饰。

每个回答后简短复述，再问下一个。若用户一开始就把三者都给了，直接跳到变体。

### 2. 变体（2-3 个，绝不做 1 个，很少做 4+）

一次产出 **2-3 个变体**。每个变体都是完整、独立的 HTML 文件。不要描述变体——直接做出来。重点是比较。

每个变体应取**不同的设计立场**，而非不同像素值。三个好的变体轴：

- **密度：** 紧凑 / 疏朗 / 超密集（选两个对比强烈的极端）
- **侧重：** 内容优先 / 动作优先 / 工具优先
- **美学：** 编辑风 / 实用主义 / 俏皮
- **布局：** 单栏 / 侧边栏 / 分栏
- **基底：** 卡片式 / 裸内容 / 文档式

选一个轴，围绕它拉开差距。只换强调色的两个变体是白费功夫——用户分不出区别。

**变体命名：** 描述立场，而非编号。

```
sketches/
├── 001-calm-editorial/
│   ├── index.html
│   └── README.md
├── 001-utilitarian-dense/
│   ├── index.html
│   └── README.md
└── 001-playful-split/
    ├── index.html
    └── README.md
```

### 3. 做成真正的 HTML

每个变体是一个**自包含的单一 HTML 文件**：

- 内联 `<style>` —— 无构建步骤、无外部 CSS
- 系统字体，或通过 `<link>` 引入一个 Google Font
- 可通过 CDN 用 Tailwind（`<script src="https://cdn.tailwindcss.com"></script>`）没问题
- 逼真的假内容——真实的句子、真实的名字，不要「Lorem ipsum」
- **可交互**：链接可点、hover 有效、至少一个状态切换（开 / 关、过滤、toggle）。一张冻结的静态图比一个粗糙的动画版更糟。

在浏览器中打开它。若看起来有问题，先修好再给用户看。

**视觉验证变体——用 Hermes 的浏览器工具。** 不要只写 HTML 就指望它能渲染。加载每个变体并实际查看：

```
browser_navigate(url="file:///absolute/path/to/sketches/001-calm-editorial/index.html")
browser_vision(question="Does this layout look clean and readable? Any visible bugs (overlapping text, unstyled elements, broken images)?")
```

`browser_vision` 返回对页面实际内容的 AI 描述，外加一张截图路径。能抓出纯源码检查漏掉的布局 bug（例如静默失败的字体导入、塌陷的 flex 容器）。修好后重新导航，直到每个变体看起来都对。

**默认 CSS reset + 系统字体栈**，便于快速起步：

```html
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    color: #1a1a1a;
    background: #fafafa;
    line-height: 1.5;
  }
</style>
```

### 4. 变体 README

每个变体的 `README.md` 回答：

```markdown
## Variant: {stance name}

### Design stance
One sentence on the principle driving this variant.

### Key choices
- Layout: ...
- Typography: ...
- Color: ...
- Interaction: ...

### Trade-offs
- Strong at: ...
- Weak at: ...

### Best for
- The kind of user or use case this variant actually serves
```

### 5. 正面比较

所有变体做完后，以对比形式呈现。不要只罗列——要**给出观点**：

```markdown
## Three takes on the home screen

| Dimension | Calm editorial | Utilitarian dense | Playful split |
|-----------|----------------|-------------------|---------------|
| Density   | Low            | High              | Medium        |
| Primary action visibility | Low | High | Medium |
| Scan-ability | High | Medium | Low |
| Feel | Calm, trusted | Sharp, tool-like | Inviting, energetic |

**My take:** Utilitarian dense for power users, calm editorial for content-forward audiences. Playful split is weakest — tries to do both and commits to neither.
```

让用户挑一个赢家，或把两个合成一个混合版，或再来一轮。

## 主题化（当项目已有视觉识别时）

若用户已有主题（颜色、字体、token），把共享 token 放入 `sketches/themes/tokens.css`，并在每个变体中 `@import`。token 保持精简：

```css
/* sketches/themes/tokens.css */
:root {
  --color-bg: #fafafa;
  --color-fg: #1a1a1a;
  --color-accent: #0066ff;
  --color-muted: #666;
  --radius: 8px;
  --font-display: "Inter", sans-serif;
  --font-body: -apple-system, BlinkMacSystemFont, sans-serif;
}
```

别给一次性草案过度 token 化——三个颜色加一个字体通常就够了。

## 可交互性门槛

当用户能以下操作时，草案就算足够可交互：

1. **点击一个主要动作**，并有可见的事发生（状态变化、modal、toast、导航假动作）
2. **看到一个有意义的状态切换**（过滤列表、切换模式、开 / 关面板）
3. **hover 可识别的交互元素**（按钮、行、标签页）

再多就是给一次性草案过度工程化。再少就只是一张截图。

## Frontier mode（决定接下来草拟什么）

若已有草案，且用户问「接下来该草拟什么？」：

- **一致性缺口** —— 来自不同草案的两个胜出变体各自做了独立选择，却还没被组合到一起
- **未草拟的界面** —— 被提及但从未探索
- **状态覆盖** —— happy path 已草拟，但空 / 加载 / 错误 / 1000 项状态没有
- **响应式缺口** —— 只在一个视口验证过。在移动端 / 超宽屏还成立吗？
- **交互模式** —— 静态布局已有。转场、拖拽、滚动行为没有

提出 2-4 个命名候选。让用户挑。

## 输出

- 在仓库根目录创建 `sketches/`（若用户遵循 GSD 约定则为 `.planning/sketches/`）
- 每个变体一个子目录：`NNN-stance-name/index.html` + `README.md`
- 告诉用户如何打开：macOS 上用 `open sketches/001-calm-editorial/index.html`，Linux 上用 `xdg-open`，Windows 上用 `start`
- 变体保持可丢弃——若你觉得需要保留某个草案，它就该被提升为真实项目代码，而非当作资产收藏

**单个变体的典型工具序列：**

```
terminal("mkdir -p sketches/001-calm-editorial")
write_file("sketches/001-calm-editorial/index.html", "<!doctype html>...")
write_file("sketches/001-calm-editorial/README.md", "## Variant: Calm editorial\n...")
browser_navigate(url="file://$(pwd)/sketches/001-calm-editorial/index.html")
browser_vision(question="How does this look? Any obvious layout issues?")
```

对每个变体重复，然后呈现对比表。

## 出处

改编自 GSD（Get Shit Done）项目的 `/gsd-sketch` 工作流——MIT © 2025 Lex Christopherson（[gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)）。上游 GSD 仓库现已在 GitHub 上**归档 / 不再维护**。`get-shit-done-cc` npm 包仍可安装（`npx get-shit-done-cc --hermes --global`），并附带持久化 sketch 状态。主题 / 变体模式参考与一致性审计工作流，但请把它当作已归档的社区项目。
