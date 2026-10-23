---
name: pretext
description: "用 pretext 做创意浏览器 demo 时使用。只要要做 DOM-free 文本排版类演示——文字绕移动图形回流、文字几何游戏、逐字粒子、动态排版。就主动加载，即使用户只说「做个炫酷的文字 demo」。不用于纯 CSS 能解决的静态页面或无文字角色的 canvas 生成艺术（考虑 p5js）。"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative-coding, typography, pretext, ascii-art, canvas, generative, text-layout, kinetic-typography]
    related_skills: [p5js, claude-design, excalidraw, architecture-diagram]
---

# Pretext 创意 Demo

## 概览

[`@chenglou/pretext`](https://github.com/chenglou/pretext) 是 Cheng Lou（React core、ReasonML、Midjourney）写的 15KB 零依赖 TypeScript 库，用于 **DOM-free 的多行文本测量与排版**。它只做一件事：给定 `(text, font, width)`，返回换行位置、逐行宽度、逐字形位置与总高度——全部通过 canvas 测量，无回流。

听起来像底层管道。其实不是。因为它快且几何化，它是一个**创意原语**：你可以在 60fps 下让段落绕着一个移动的精灵回流。做以真实单词构成关卡几何的游戏，让 ASCII logo 由散文驱动。把文字打碎成带有精确逐字形起始位置的粒子，或在没有任何 `getBoundingClientRect` 抖动的情况下紧凑排布多行 UI。

本 skill 的存在是为了让 Hermes 用它做出**炫酷 demo**——那种人们会发到 X 上的。社区 demo 合集见 `pretext.cool` 与 `chenglou.me/pretext`。

## 何时使用

用户要求以下内容时使用：
- 一个「pretext demo」/「炫酷的 pretext 玩意」/「文字即 X」
- 文字绕移动图形流动（hero 区、编辑风布局、动态长文页面）
- 使用**真实单词或散文**（而非等宽点阵）的 ASCII-art 效果
- 游戏场地 / 障碍 / 砖块由文字构成的游戏（字母俄罗斯方块、散文打砖块）
- 带逐字形物理的动态排版（打碎、散开、聚群、流动）
- 排版生成艺术，尤其是非拉丁文字或混合文字
- 多行「收缩包裹」UI（仍能容纳文本的最小容器宽度）
- 任何需要*在渲染前*知道换行位置的东西

不要用于：
- CSS 已能解决布局的静态 SVG/HTML 页面——直接用 CSS
- 富文本编辑器、通用行内格式化引擎（pretext 有意保持窄）
- 图片 → 文字（用 `ascii-art` / `ascii-video` skill）
- 无文字角色的纯 canvas 生成艺术——用 `p5js`

## 创作标准

这是在浏览器中渲染的视觉艺术。pretext 返回数字。*画东西的是你*。

- **不要交付「hello world」demo。** `hello-orb-flow.html` 模板只是*起点*。每个交付的 demo 都必须加入有意的配色、动效、构图，以及一个用户没要求但会欣赏的视觉细节。
- **深色背景、暖色核心、考究的调色板。** 经典的琥珀配黑（CRT / 终端）可以，冷白配炭灰（编辑风）与低饱和粉彩（孔版印刷）也行。挑一种并坚持。
- **比例字体才是重点。** pretext 的整体气质就是「非等宽」——顺势而为。用 Iowan Old Style、Inter、JetBrains Mono、Helvetica Neue 或一款可变字体。绝不用默认 sans。
- **真实的来源 / 文本，而非 lorem ipsum。** 语料应有意义。短宣言、诗歌、真实源码、拾得的文本、库自身的 README——绝不用 `lorem ipsum`。
- **首帧即优秀。** 无加载状态、无空白帧。demo 必须在打开的瞬间就显得可交付。

## 技术栈

每个 demo 一个自包含的 HTML 文件。无构建步骤。

| 层 | 工具 | 用途 |
|-------|------|---------|
| 核心 | `@chenglou/pretext`，经 `esm.sh` CDN | 文本测量 + 行排版 |
| 渲染 | HTML5 Canvas 2D | 字形渲染、逐帧合成 |
| 分词 | `Intl.Segmenter`（内置） | 为 emoji / CJK / 组合标记做字形切分 |
| 交互 | 原生 DOM 事件 | 鼠标 / 触摸 / 滚轮——无框架 |

```html
<script type="module">
import {
  prepare, layout,                   // use-case 1: simple height
  prepareWithSegments, layoutWithLines,  // use-case 2a: fixed-width lines
  layoutNextLineRange, materializeLineRange, // use-case 2b: streaming / variable width
  measureLineStats, walkLineRanges,  // stats without string allocation
} from "https://esm.sh/@chenglou/pretext@0.0.6";
</script>
```

锁定版本。撰写时为 `@0.0.6`——若 demo 行为异常，去 [npm](https://www.npmjs.com/package/@chenglou/pretext) 查最新版。

## 两种用例

几乎所有事情都可归约为这两种形态之一。两者都要掌握。

### 用例 1 —— 先测量，再用 CSS/DOM 渲染

```js
const prepared = prepare(text, "16px Inter");
const { height, lineCount } = layout(prepared, 320, 20);
```

文本仍由浏览器绘制。pretext 只告诉你盒子在给定宽度下有多高，**无需**读取 DOM。用于：
- 行内含换行文本的虚拟化列表
- 需要精确卡片高度的瀑布流
- 「这个标签放得下吗？」的开发期检查
- 远程文本加载时防止布局偏移

**让 `font` 与 `letterSpacing` 与你的 CSS 精确同步。** canvas 的 `ctx.font` 格式（例如 `"16px Inter"`、`"500 17px 'JetBrains Mono'"`）必须与渲染的 CSS 一致，否则测量会漂移。

### 用例 2 —— 自己*同时*测量与渲染

```js
const prepared = prepareWithSegments(text, FONT);
const { lines } = layoutWithLines(prepared, 320, 26);
for (let i = 0; i < lines.length; i++) {
  ctx.fillText(lines[i].text, 0, i * 26);
}
```

创作工作就在这里。绘制由你掌控，所以你可以：
- 渲染到 canvas、SVG、WebGL 或任意坐标系
- 代入逐字形变换（旋转、抖动、缩放、透明度）
- 把行元数据（宽度、字形位置）当作几何来用

对于**逐行可变宽度**的流动（文字绕形状、文字在环形带内、文字在非矩形列中）：

```js
let cursor = { segmentIndex: 0, graphemeIndex: 0 };
let y = 0;
while (true) {
  const lineWidth = widthAtY(y);  // your function: how wide is the corridor at this y?
  const range = layoutNextLineRange(prepared, cursor, lineWidth);
  if (!range) break;
  const line = materializeLineRange(prepared, range);
  ctx.fillText(line.text, leftEdgeAtY(y), y);
  cursor = range.end;
  y += lineHeight;
}
```

这是整个库里最重要的模式。它解锁了「文字绕着被拖拽的精灵流动」——那个在 X 上爆火的 demo。

### 值得了解的辅助函数

- `measureLineStats(prepared, maxWidth)` → `{ lineCount, maxLineWidth }` —— 最宽的行，即多行收缩包裹宽度。
- `walkLineRanges(prepared, maxWidth, callback)` —— 遍历各行而不分配字符串。当你不需要字符本身、只想对字形做统计 / 物理时使用。
- `@chenglou/pretext/rich-inline` —— 同一套系统，但面向混排字体 / chip / @提及的段落。从子路径导入。

## Demo 配方模式

社区合集（见 `references/patterns.md`）聚成少数几个强模式。挑一个即兴发挥——除非用户要求，不要发明新类别。

| 模式 | 关键 API | 示例构想 |
|---|---|---|
| **绕障碍回流** | `layoutNextLineRange` + 逐行宽度函数 | 编辑风段落，绕被拖拽的光标精灵让开 |
| **文字即几何的游戏** | `layoutWithLines` + 逐行碰撞矩形 | 每块砖都是一个量到的单词的打砖块 |
| **打碎 / 粒子** | `walkLineRanges` → 逐字形 (x,y) → 物理 | 点击后炸成字母的句子 |
| **ASCII 障碍排版** | `layoutNextLineRange` + 量到的逐行障碍跨度 | 位图 ASCII logo、形状变形，以及让文字绕其真实几何让开的可拖拽线框对象 |
| **编辑风多栏** | 每栏 `layoutNextLineRange` + 共享游标 | 带引言块的动态杂志跨页 |
| **动态字体** | `layoutWithLines` + 随时间变化的逐行变换 | 星球大战爬字幕、波浪、弹跳、故障 |
| **多行收缩包裹** | `measureLineStats` | 自动缩到最紧凑容器的引言卡片 |

可用的单文件起手模板见 `templates/donut-orbit.html` 与 `templates/hello-orb-flow.html`。

## 工作流

1. 依据用户的 brief，从上面的表里**挑一个模式**。
2. **从模板起步**：
   - `templates/hello-orb-flow.html` —— 文字绕着移动的球回流（绕障碍回流模式）
   - `templates/donut-orbit.html` —— 进阶示例：量到的 ASCII logo 障碍、可拖拽的线框球体 / 立方体、变形的形状场、可选择的 DOM 文本。以及仅开发用的控件。
   - 用 `write_file` 在 `/tmp/` 或用户工作区写一个新的 `.html`。
3. **替换语料**为契合 brief 的内容。真实散文，10-100 句，无 lorem。
4. **调校美学**——字体、调色板、构图、交互。这才是正经工作。不要跳过。
5. **本地验证**：
   ```sh
   cd <dir-with-html> && python3 -m http.server 8765
   # then open http://localhost:8765/<file>.html
   ```
6. **检查控制台**——若用错误的字体字符串调用 `prepareWithSegments`，pretext 会抛错。`Intl.Segmenter` 在每个现代浏览器中都可用。
7. **把文件路径给用户**，而不只是代码——他们想打开它。

## 性能注意事项

- `prepare()` / `prepareWithSegments()` 是昂贵的调用。每个文本 + 字体组合只做**一次**。缓存句柄。
- 窗口变化时，只重跑 `layout()` / `layoutWithLines()`——绝不重新 prepare。
- 对于文本不变但几何每帧变化的动画，对正常长度的段落，在紧凑循环里跑 `layoutNextLineRange` 足够便宜。可以每帧在 60fps 下执行。
- 逐帧渲染 ASCII 遮罩时，保留一个单元格缓冲（`Uint8Array` / 类型化数组）。从单元格或投影几何推导量到的逐行障碍跨度，合并跨度，然后在绘制文字前把这些跨度喂给 `layoutNextLineRange`。
- 让视觉动画与布局动画保持耦合。若球体变形为立方体，用同一个值对渲染的单元格缓冲与障碍跨度一起做补间。否则 demo 看起来像是贴上去的，而非物理回流。
- 做淡出时，优先用图层不透明度，而非改变字形强度或障碍缩放。把瞬态 ASCII 精灵放在自己的 canvas 上，用 CSS/GSAP 的不透明度淡化该 canvas，这样几何看起来不会缩小。
- canvas 的 `ctx.font` 设置出奇地慢。若字体不变，每帧只设**一次**，而非每次 `fillText` 都设。

## 常见坑

1. **CSS / canvas 字体字符串漂移。** `ctx.font = "16px Inter"` 量的是它，但 CSS 写的是 `font-family: Inter, sans-serif; font-size: 16px`。*只要* Inter 加载了就没事。若 Inter 404，CSS 回退到 sans-serif，测量就漂移 5-20%。始终 `preload` 字体，或用 web-safe 字体族。

2. **在动画循环里重复 prepare。** 只有 `layout*` 便宜。每帧重调 `prepare` 会拖垮性能。把 prepared 句柄放在模块作用域。

3. **忘记用 `Intl.Segmenter` 做字形切分。** emoji、组合标记、CJK——`"é".split("")` 会给你两个字符。采样单个可见字形时用 `new Intl.Segmenter(undefined, { granularity: "grapheme" })`。

4. **`break: 'never'` 的 chip 没配 `extraWidth`。** 在 `rich-inline` 中，若对原子 chip/@提及 用 `break: 'never'`，还必须为药丸内边距提供 `extraWidth`——否则 chip 外框会溢出容器。

5. **从 `unpkg` 用只有 TypeScript 入口的 `@chenglou/pretext`。** 用 `esm.sh`——它会自动把 TS 导出编译成浏览器可用的 ESM。`unpkg` 会 404 或返回原始 TS。

6. **等宽回退悄悄毁掉整个重点。** 看到像是等宽输出的用户，往往是 CSS `font-family` 掉到了 `monospace`。用 DevTools 核实实际渲染的字体。

7. **绕形状流动时跳过行 vs 调整宽度。** 若这一行的走廊太窄放不下一个行，就*跳过这一行*（`y += lineHeight; continue;`），而不是给 `layoutNextLineRange` 传一个极小的 maxWidth。pretext 会返回看起来像坏掉的单字形行。

8. **交付一个冷冰冰的 demo。** 默认首帧看起来像教程级。加上：暗角、细微扫描线、闲置自动运动、一个精心挑选的交互响应（拖拽、hover、滚动、点击）。没有这些，「炫酷的 pretext demo」只会沦为「实习生复刻 README」。

## 验证清单

- [ ] demo 是单个自包含 `.html` 文件——双击或 `python3 -m http.server` 即可打开
- [ ] 经 `esm.sh` 导入 `@chenglou/pretext` 且锁定版本
- [ ] 语料是真实散文，非 lorem ipsum，且契合 demo 概念
- [ ] 传给 `prepare` 的字体字符串与 CSS 字体完全一致
- [ ] `prepare()` / `prepareWithSegments()` 只调用一次，而非每帧
- [ ] 深色背景 + 考究调色板——不是默认白画布
- [ ] 至少一个交互响应（拖拽 / hover / 滚动 / 点击）或闲置自动运动
- [ ] 用 `python3 -m http.server` 本地测过，确认无控制台错误
- [ ] 在中端笔记本上 60fps（或记录了优雅降级）
- [ ] 一个用户没要求、但「多走一英里」的细节

## 参考：社区 Demo

克隆这些以获取灵感 / 模式（均为类 MIT，来自 [pretext.cool](https://www.pretext.cool/)）：

- **Pretext Breaker** —— 单词砖块打砖块 —— `github.com/rinesh/pretext-breaker`
- **Tetris × Pretext** —— `github.com/shinichimochizuki/tetris-pretext`
- **Dragon animation** —— `github.com/qtakmalay/PreTextExperiments`
- **Somnai editorial engine** —— `github.com/somnai-dreams/pretext-demos`
- **Bad Apple!! ASCII** —— `github.com/frmlinn/bad-apple-pretext`
- **Drag-sprite reflow** —— `github.com/dokobot/pretext-demo`
- **Alarmy editorial clock** —— `github.com/SmisLee/alarmy-pretext-demo`

官方 playground：[chenglou.me/pretext](https://chenglou.me/pretext/) —— accordion、bubbles、dynamic-layout、editorial-engine、justification-comparison、masonry、markdown-chat、rich-note。
