---
name: chat-inline-statusboard
description: "在桌面版聊天里做内嵌状态板/看板/活面板时使用。只要涉及 ::preview 组件、主题变量、回话按钮、多线项目状态一览或交互式检查单，就主动加载，即使用户只是想要一个「长在聊天里的可视化面板」。不用于持久 sidebar/pane（用 hermes-desktop-plugins）或 CLI/TUI 界面。"
version: 1.4.1
author: Nekonya (小喵)
license: internal
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [desktop, preview, ui, statusboard]
    category: productivity
---

# 聊天内嵌状态板（::preview 组件）

## 何时使用

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
8. **动态生成的行/卡片必须用内联 onclick，不用 `data-hermes-send`**。`data-hermes-send` 是**加载期扫描**绑定的，对 `innerHTML` 之后才出现的元素不保证生效；由 JS 模板拼出来的行一律写 `onclick="window.hermes.send('...')"`，属性里的提示词用 `JSON.stringify(prompt)` 注入以免引号炸掉 HTML。静态写死的按钮两者皆可。
9. **长表两条硬约束**：表头 `position:sticky; top:0; background:var(--card)`；表格套 `max-height:430px; overflow:auto` 的滚动容器。表列多时数字列一律 `text-align:right; font-variant-numeric:tabular-nums`，否则不齐整。列过 15 左右再给滚动容器加 `max-width:min(1180px,94vw)`——22 列 `nowrap` 会把测量宽度撑爆。
10. **用 Python 生成 JS 时，拼出来的 JS 必须先过语法检查再发**。两个具体坑：(a) `${...}` 只在**反引号模板字面量**里有意义，写进普通单引号字符串就变成了字面文本（表里会直接显示 `${r["x"]}`）；(b) 拼接链里漏引号会出现 `+<td ...>` 这种**裸标签**——这是语法错误，`render()` 一抛异常整个表体永远填不上，表现为「组件空白、看不到」。**验证方法**：抽出 `<script>` 写入临时 `.js` 跑 `node --check`（本机有 node），再用一个假 `document`/`window` 桩 eval 一遍确认 `render()` 不抛异常、`el.innerHTML` 长度正常、首行有真实数值。只看括号平衡不够——平衡但语义错照样炸。

## 制作流程（状态板型，从零到发）

1. 收集内容：从最近的报告/判据文件里取**每条线的真实现状 + 数字**（read_file/落盘件）。
2. 设计网格：几条线几张卡；每卡三行结构固定（干什么/现状/馈入）。
3. 写 HTML（三件套铁律全过）→ 回复正文里放 `::preview{file=...}` 单独一行。
4. **验证**：面板出现且主题协调（明暗两看）；按钮点击后确认回话到达、且**面板被更新**；窗口缩放不破布局。

## 组件型（四种常用变体）

- **状态板**（四线/六线卡片网格，见铁律 5）。
- **检查单/进度条**：用 `data-hermes-send` 做每行「✓ 已完成」按钮，点了发隐藏指令让助手更新状态+重画面板。
- **小型仪表**（如预算/GPU/时间闸读数）：纯 div 条形（width %），**不需要**图表库；要图就用 fig 的 PNG 走 MEDIA: 发，别把 canvas 硬塞进聊天组件。
- **数据表型**（几十到几百行的数据集要筛选/排序/带行动按钮，见下节）。

## 数据表型（大数据集交互表）

适用：把一个**枚举出来的数据集**（模型仓清单、价格对比、文献列表、候选方案矩阵）以可筛选可排序的活表落在聊天里，每行还能直接触发下一轮工作。

**管线（四步，全部内生）**：

1. **源头用 API 枚举，不用人肉粘贴**。用户粘的清单必然漏。先找该站的结构化接口（HuggingFace: `/api/models?author=<user>&limit=1000`，靠 `Link: rel="next"` 翻页），全量拉下来落一个 JSON。
2. **逐项补字段**（多线程抓详情，`ThreadPoolExecutor(max_workers=10)` 足够；209 个仓约 5 秒）。**边拉边存**，脚本可断点续跑。
3. **Python 拼 HTML**，`json.dumps(rows)` 注入成 JS 数组，排序/筛选全在前端，无服务器无网络。
4. 回复里 `::preview{file=...}` 渲染，同时落 CSV + Markdown 供下载（MEDIA:）。

**行动按钮分两层**：

- **行级**：状态相关的动作（如「拉这个」/「看看」）。按行的数据决定按钮形态与提示词——**提示词由行的字段动态拼**，并且要写全（写清判据、落盘位置、结束条件），因为用户点它时期望的是执行不是闲聊。
- **顶部批量**：跨行操作（「拼入另一批数据」「按某维度重排」）。
- 行级按钮还常见一类**无副作用的纯前端按钮**（只看 GGUF / 重置筛选）——它们不挂 send，只调本地 JS。

**多列表必须先定列号，不能默认第一列**。上游官方基准表常是「同一家族多型号横向对照」，下表头可能是 `['', 'Qwen3.5-27B', 'Gemma4-31B', 'Qwen3.5-35BA3B', 'Qwen3.6-35BA3B', …]`——该卡对应的型号可能在第 5 列。**取错列会把整列分数换成别的型号的**，而且数值看着完全合理，不会报错。正确做法：**解析表头 → 用归一化匹配（去除非字母数字、小写、子串包含）定位该卡对应的列号 → 按列号取值**；匹配不到时才退到第一列。发布后至少抽 2–3 张卡人工交叉验一列。

**跨表取值要标来源**：同一数据集里，不同列可能来自不同表（如 agentic 分来自上游对照表，而 KL/MMLU 来自 lm-eval 块）。**在表头或副标题里把来源分开写明**，否则用户会把两本账揉成一个结论。

**缺口要显式说明**：源数据里没有的字段（如逐量化档的 PPL）不要留空让人误读成 0——表里写「—」，并单独一句话说明「共 X/Y 个仓有该字段」。

### 视图控制（宽/缩放/弹出/全屏）

用户看完长表必问的四件事，逐个给：

- **表格 = 页面宽**：**不要给滚动容器加 `max-width`**——框架宽度按内容测量，`max-width` 会让表比框架窄。直接让表驱动宽度（避免无限宽）；真要限宽就用 `max-width:min(1180px,94vw)`，但那是为了防 20+ 列 `nowrap` 撑爆。
- **缩放**：纯前端，外层包一个 `#zbox`，按钮设 `#zbox.style.zoom`（Chromium/webview 支持）。**必带上下限钳制**（如 0.5–2.4），并把当前百分比回显在按钮上。
- **弹出窗口化**：**不能靠 `window.open()`**（iframe 沙箱常禁弹窗）。正解是挂 `window.hermes.send('用 desktop_preview 把 <文件> 开在侧边预览面板里，标签叫 <名>')`——助手那一轮拿到指令后调 `desktop_preview(action='open', url='<绝对路径>')`，面板是持久侧栏，比内嵌组件大得多。
- **全屏**：**实测确认——内嵌 iframe 的 `requestFullscreen()` 被沙箱拒**（按钮点下去后兜底分支执行了）。所以必须写 `.catch(兜底)` 且 `if(!el.requestFullscreen)` 也走兜底；兜底 = 发 `window.hermes.send` 让助手开预览面板 + 套大空间布局。**要诚实告知用户哪一路生效。**
- **二者都是可选，不是默认项**：弹出 + 全屏做成按钮挂着就行，但**不要在交付时主动加**——用户实测后觉得「没必要」，明确叫停了（2026-10-06）。先交「全宽 + 缩放」，用户真要再补。

面板控制类工具（助手侧，不是文件内）：`desktop_preview` 开/关/读侧边预览面板；`focus_pane` 显式聚焦 chat/files/terminal/review/sessions（不含 preview）；`apply_layout` 套布局预设（default/focus/terminal-deck/quad）；`gui_tour(surface='preview')` 在预览页上做引导圈点。

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
