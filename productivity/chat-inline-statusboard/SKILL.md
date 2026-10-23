---
name: chat-inline-statusboard
description: 在桌面版聊天内做状态板/看板/活面板（::preview 组件+主题变量+回话按钮）时使用。
version: 1.1.0
author: Nekonya (小喵)
license: internal
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [desktop, preview, ui, statusboard]
    category: productivity
---

# 聊天内嵌状态板（::preview 组件）

## When to Use

- 用户在**桌面版**里要「状态板/看板/仪表/多线状态一览/交互检查单」这种直接长在聊天里的可视化。
- 多线项目汇报时，用户已经看不懂纯文字线索，需要一眼读清「谁在哪、卡在哪、下一步」。
- 需要用户点一下就触发下一轮工作（回话按钮）的交互式面板。

不适用：持久 sidebar/pane/状态栏 → hermes-desktop-plugins；TUI/CLI 界面 → 明文路径。

在 Hermes 桌面版聊天里做**内嵌活面板**：状态板、看板、多线项目状态、自查仪表、交互式检查单。
不需要插件（那是另一套——hermes-desktop-plugins skill 管 pane/命令），本 skill 只用三样内生工具：write_file + `::preview` 指令 + app 注入的主题变量。

## 三件套（全部内生，无外部依赖）

1. **写 HTML 文件**（write_file，纯手写 CSS 即可，不需要图表库；卡片/徽章 = div+grid）。
2. **聊天里渲染**：回复中单独一行放
   `::preview{file="/absolute/path.html"}` ——行内组件直接长在聊天里，不用用户点开。
3. **主题跟随**：CSS 不写死任何颜色/背景/字体。app 在组件渲染前把当前主题注入为变量，直接用：
   `var(--foreground)`（正文）、`var(--muted-foreground)`（次要文字）、`var(--accent)`（强调/按钮）、
   `var(--border)`（边框）、`var(--card)`（卡片底）。body 置 `background: transparent`，由 app 主题兜底。

## 铁律（踩过的坑，逐条硬约束）

1. **禁止写死颜色与背景**（`#000`、`rgb(...)`、自定义底色）——明暗主题切换会穿帮。强调色一律 `var(--accent)`；「危险/待拍板」徽章等语义色可用品牌无关的具名色（红 `#b85450`、橙 `#d79b00`、绿 `#82b366`、紫 `#9673a6`）只作边框/文字色，不做大面积填充。
2. **布局贴合测量**：预览框按内容**首行 span 宽度**定宽、按内容自适应高——排版从左对齐开始，**禁止**用 margin:auto / text-align:center / 包裹居中容器（会把整个面板撑成全宽通栏）。高度会随内容伸缩，所以折叠/展开都能用。
3. **回话按钮**：任意可点元素挂 `data-hermes-send="提示词"`（或 `window.hermes.send("提示词")`）——点击后把提示词作为**隐藏用户回合**发进聊天。两件事必须配套做：a) 提示词写成**可直接执行的完整指令**（含「判据写死」「落盘位置」等要求），因为用户点按钮时期望的是行动不是闲聊；b) **回答这类回合要更新面板文件本身**（patch 面板里的状态、追加行），不是只回散文——面板是活的，点完按钮状态板必须变。
4. **按钮排版**：`button { font: inherit; }` 必带，否则按钮字体与面板不一致；hover 用 `color-mix(in srgb, var(--accent) 12%, transparent)` 这种主题混合，不写死 hover 色。
5. **信息密度**：状态板的正确粒度 = 每卡片三行——「它要干什么 / 现状一句 / ↳ 最近一次实验给它的输入」。徽章表状态：卡住（红）、待执行（橙）、已实付/完结（绿）、论文级（紫）。多线并行项目先画四线/六线卡片网格，再一格一格填，最后才润色。
6. **文件放项目树内**（可复用、可版本化），不放 /tmp——面板会被反复 patch 更新，路径要稳定。
7. **数字与时效**：面板里出现的数字/时间戳必须来自当次会话的真实工具输出（落盘文件、date 输出），不许凭记忆填；每次 patch 更新面板时同步更新标题里的「截至」时间戳。

## 制作流程（状态板型，从零到发）

1. 收集内容：从最近的报告/判据文件里取**每条线的真实现状 + 数字**（read_file/落盘件）。
2. 设计网格：几条线几张卡；每卡三行结构固定（干什么/现状/馈入）。
3. 写 HTML（三件套铁律全过）→ 回复正文里放 `::preview{file=...}` 单独一行。
4. **验证**：面板出现且主题协调（明暗两看）；按钮点击后确认回话到达、且**面板被更新**；窗口缩放不破布局。

## 组件型（三种常用变体）

- **状态板**（四线/六线卡片网格，见铁律 5）。
- **检查单/进度条**：用 `data-hermes-send` 做每行「✓ 已完成」按钮，点了发隐藏指令让助手更新状态+重画面板。
- **小型仪表**（如预算/GPU/时间闸读数）：纯 div 条形（width %），**不需要**图表库；要图就用 fig 的 PNG 走 MEDIA: 发，别把 canvas 硬塞进聊天组件。

## 何时不用本组件

- 要**持久面板**（sidebar 级、拖拽停靠、状态栏 chip）→ 用 hermes-desktop-plugins skill（plugin.js）。
- 要**演示型整页**（海报、小游戏、可滚动长页）→ 它是 standalone PAGE，可以脱离 app 主题自设配色；但聊天内嵌组件永远遵守铁律 1/2。
- 目标界面是 CLI/TUI（无预览组件）→ 文件路径明文给出，别发 ::preview。

## 最小模板（可直接复制起步）

```html
<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8"><style>
body { font-family: var(--font-family, system-ui, sans-serif); color: var(--foreground);
       background: transparent; margin: 0; padding: 14px 16px; font-size: 13.5px; line-height: 1.55; }
h2 { font-size: 16px; margin: 0 0 10px; }
.sub { color: var(--muted-foreground); font-size: 12px; margin-bottom: 12px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.card { border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; background: var(--card); }
.card h3 { margin: 0 0 6px; font-size: 13.5px; display: flex; align-items: center; gap: 8px; }
.badge { font-size: 10.5px; padding: 1px 8px; border-radius: 999px; border: 1px solid var(--border); color: var(--muted-foreground); }
.card p { margin: 4px 0; }
.gift { color: var(--accent); font-size: 12px; }
button { margin-top: 10px; font: inherit; font-size: 12.5px; padding: 6px 14px; border-radius: 8px;
         border: 1px solid var(--accent); color: var(--accent); background: transparent; cursor: pointer; }
button:hover { background: color-mix(in srgb, var(--accent) 12%, transparent); }
</style></head><body>
<h2>标题（含截至时间戳）</h2>
<div class="sub">一句话副标题</div>
<div class="grid">
  <div class="card"><h3>线 1 <span class="badge">状态</span></h3>
    <p>干什么</p><p>现状（带数字）</p><p class="gift">↳ 最近实验的输入</p></div>
  <!-- 更多卡片 -->
</div>
<button data-hermes-send="完整的可执行指令提示词">行动按钮</button>
</body></html>
```
