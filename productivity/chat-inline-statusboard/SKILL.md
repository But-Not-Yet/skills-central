---
name: chat-inline-statusboard
description: 用户在桌面版聊天里要『长在聊天里』的可视化时加载：状态板、看板、多线项目状态一览、交互式检查单、点一下触发下一轮的回话按钮。只用 write_file + ::preview + 主题变量三件套，不装插件。持久的 sidebar/pane 走 hermes-desktop-plugins，CLI/TUI 界面不走这里。
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
- 要更新独立的架构页/状态页（非聊天内嵌），尤其是把旧快照换成当前看板状态、统计待办、补两线编排。

不适用：持久 sidebar/pane/状态栏，走 hermes-desktop-plugins。TUI/CLI 界面走明文路径。

在 Hermes 桌面版聊天里做**内嵌活面板**：状态板、看板、多线项目状态、自查仪表、交互式检查单。
不需要插件（那是另一套东西，由 hermes-desktop-plugins skill 管 pane/命令）。本 skill 只用三样内生工具：write_file + `::preview` 指令 + app 注入的主题变量。

## 三件套（全部内生，无外部依赖）

1. **写 HTML 文件**（write_file，纯手写 CSS 即可，不需要图表库。卡片/徽章 = div+grid）。
2. **聊天里渲染**：回复中单独一行放
   `::preview{file="/absolute/path.html"}`：行内组件直接长在聊天里，不用用户点开。
3. **主题跟随**：CSS 不写死任何颜色/背景/字体。app 在组件渲染前把当前主题注入为变量，直接用：
   `var(--foreground)`（正文）、`var(--muted-foreground)`（次要文字）、`var(--accent)`（强调/按钮）、
   `var(--border)`（边框）、`var(--card)`（卡片底）。body 置 `background: transparent`，由 app 主题兜底。

## 插件/钩子生成的内联卡（确定性）

同一套 `::preview` 组件也可以由 Python 插件生成，不靠模型手写 HTML：

- 宿主 `transform_llm_output` 钩子返回字符串即替换正文（第一个非空胜出）；在正文末尾追加 `\n\n::preview{file="<绝对路径>"}\n`。
- 卡片内容由结构化数据渲染（claim/status/decision），文件落到 `~/.hermes/cache/<plugin>_cards/<session>/`；一轮最多一张，带 `TIERED_CARDS=0` 类开关。
- 仍守全部铁律：主题变量、透明背景、左对齐、`button{font:inherit}`、静态 `data-hermes-send`、动态行内 `onclick`、HTML 转义。
- 点击回话仍是隐藏用户回合；插件侧要解析 `decision_id/choice/note`，不要只靠散文。隐藏回合可能触发宿主重放，回执/决策别把它当唯一通道。按钮 prompt 可能和用户消息逐字相同，先看卡片文件/来源再判断是谁发的，不要把自动复核当成用户的新意图。
- **插件生成的“信任/待核”卡先过五问**：① 核验器有没有拿到 `base_dir`？路径/哈希 resolver 在空 base 下常返回 `None`，会被误显示成“文件不存在”；② `CheckResult` 的 status/evidence 有没有穿过 `build_cards` 保留？丢掉后所有行都成 `UNVERIFIED`、证据空；③ 路径正则是否保留完整相对路径？`tests/x.py` 被切成 `/x.py`、`disclosure/x.py` 被切成 `/x.py` 是最常见的假阳性；④ git hash 正则是否排除纯日期和文件名片段？`20261022` 这类日期、哈希样的文件名会被误报；⑤ 卡片按钮是否造成“假警告→点按钮复核→新回复再触发卡片”的自指循环？任一问不过，这张卡只能叫“待核提醒”，不能叫“信任卡”。
- **“无法核验”和“不存在”必须分文案**：`UNVERIFIED` 写“核验器不可用/无法核验”，只有 `FAIL` 才写“不存在”。把 resolver unavailable 写成“文件不存在”会诱导人改正确路径。
- **正则/关键词核验最多是待核清单**：它只能证明句子里有没有来源指针，不能证明值对；全称、完工、数字断言要枚举或跑测试。卡上标“确定性核验结果”时，同时标“仅机械检查，非证据”。
- **插件卡要有 kill switch**：按插件提供 `TIERED_CARDS=0` 这类总开关（Tiered 另可用 `TIERED_GUIDANCE=0` 连提醒一起关）；调试期先关，避免每轮追加。

## 铁律（踩过的坑，逐条硬约束）

1. **禁止写死颜色与背景**（`#000`、`rgb(...)`、自定义底色），否则明暗主题切换会穿帮。强调色一律 `var(--accent)`。「危险/待拍板」徽章等语义色，可用品牌无关的具名色（红 `#b85450`、橙 `#d79b00`、绿 `#82b366`、紫 `#9673a6`），且只作边框/文字色，不做大面积填充。
2. **布局贴合测量**：预览框按内容**首行 span 宽度**定宽、按内容自适应高度，所以排版从左对齐开始。**禁止**用 margin:auto / text-align:center / 包裹居中容器（会把整个面板撑成全宽通栏）。高度会随内容伸缩，折叠/展开都能用。
3. **回话按钮**：任意可点元素挂 `data-hermes-send="提示词"`（或 `window.hermes.send("提示词")`）。点击后把提示词作为**隐藏用户回合**发进聊天。两件事必须配套做：a) 提示词写成**可直接执行的完整指令**，含「判据写死」「写入文件的位置」等要求。用户点按钮时期望的是行动，不是闲聊。b) **回答这类回合要更新面板文件本身**（patch 面板里的状态、追加行），不是只回散文。面板是活的，点完按钮状态板必须变。
4. **按钮排版**：`button { font: inherit; }` 必带，否则按钮字体与面板不一致。hover 用 `color-mix(in srgb, var(--accent) 12%, transparent)` 这种主题混合，不写死 hover 色。
5. **信息密度**：状态板的正确粒度是每卡片三行：「它要干什么 / 现状一句 / ↳ 最近一次实验给它的输入」。徽章按状态配色：卡住（红）、待执行（橙）、已实付/完结（绿）、论文级（紫）。多线并行项目先画四线/六线卡片网格，再一格一格填，最后才润色。
6. **文件放项目树内**（可复用、可版本化），不放 /tmp：面板会被反复 patch 更新，路径要稳定。
7. **数字与时效**：面板里的数字/时间戳，来源必须是当次会话的真实工具输出：已写入文件的成品、date。不许凭记忆填。每次 patch 更新面板时同步更新标题里的「截至」时间戳。
8. **动态生成的行/卡片必须用内联 onclick，不用 `data-hermes-send`**。`data-hermes-send` 是**加载期扫描**绑定的，对 `innerHTML` 之后才出现的元素不保证生效。由 JS 模板拼出来的行一律写 `onclick="window.hermes.send('...')"`，属性里的提示词用 `JSON.stringify(prompt)` 注入以免引号炸掉 HTML。静态写死的按钮两者皆可。
9. **长表两条硬约束**：表头 `position:sticky; top:0; background:var(--card)`。表格套 `max-height:430px; overflow:auto` 的滚动容器。表列多时数字列一律 `text-align:right; font-variant-numeric:tabular-nums`，否则不齐整。列过 15 左右再给滚动容器加 `max-width:min(1180px,94vw)`：22 列 `nowrap` 会把测量宽度撑爆。
10. **用 Python 生成 JS 时，拼出来的 JS 必须先过语法检查再发**。两个具体坑：(a) `${...}` 只在**反引号模板字面量**里有意义。写进普通单引号字符串，它就变成字面文本，表里会直接显示 `${r["x"]}`。(b) 拼接链里漏引号会出现 `+<td ...>` 这种**裸标签**。它在 JS 里就是语法层面的异常，`render()` 一抛异常整个表体就永远填不上，表现为「组件空白、看不到」。**验证方法**：抽出 `<script>` 写入临时 `.js`，跑 `node --check`（本机有 node）。再用假 `document`/`window` 桩 eval 一遍。确认 `render()` 不抛异常、`el.innerHTML` 长度正常、首行有真实数值。只看括号平衡不够：平衡但语义错照样炸。

## 制作流程（状态板型，从零到发）

1. 收集内容：从最近的报告/判据文件里取**每条线的真实现状 + 数字**（read_file 或成品文件的实物）。
2. 设计网格：几条线几张卡。每卡三行结构固定（干什么/现状/馈入）。
3. 写 HTML（三件套铁律全过）→ 回复正文里放 `::preview{file=...}` 单独一行。
4. **验证**：面板出现且主题协调（明暗两看）。按钮点击后确认回话到达、且**面板被更新**。窗口缩放不破布局。

## 独立架构页/状态页更新（非聊天内嵌）

独立页与聊天卡共用主题/状态色/时间戳纪律，但多一步“旧快照对活体”：

1. 先读旧 HTML，用 `search_files` 查旧状态、旧“截至”、旧 TODO；旧页只是快照，不是事实源。
2. 取活体：`hermes kanban --board <slug> list --json`、`date`；先定义计数口径——当前 board 的卡 vs 旧 default board 已 done 的归档行，不能混算。
3. 备份 `file.bak-<timestamp>`；整块替换 TODO `tbody` 前先断言 `<tbody>` 唯一；状态块逐个 patch；标题时间戳用当前 `date`，禁止写未来时间。
4. 用户要两线/排期时，加一个 full-width 编排区，并让 Markdown 编排文件做唯一事实源；HTML 只放摘要。
5. 验收：`html.parser` 标签栈 0 错误；用 `search_files` 查旧状态/旧时间应为 0；表内计数等于活体计数；备份存在；新加卡已进表并同步计数。

具体命令、计数口径和模板见 `references/standalone-status-page.md`。

## 组件型（四种常用变体）

- **状态板**（四线/六线卡片网格，见铁律 5）。
- **检查单/进度条**：用 `data-hermes-send` 做每行「✓ 已完成」按钮，点了发隐藏指令让助手更新状态+重画面板。
- **小型仪表**（如预算/GPU/时间闸读数）：纯 div 条形（width %），**不需要**图表库。要图就用 fig 的 PNG 走 MEDIA: 发，别把 canvas 硬塞进聊天组件。
- **数据表型**（几十到几百行的数据集要筛选/排序/带行动按钮，见下节）。

## 数据表型（大数据集交互表）

适用场景：把一个**枚举出来的数据集**做成可筛选可排序的活表，落在聊天里。模型仓清单、价格对比、文献列表、候选方案矩阵都算这类数据集。每行还能直接触发下一轮工作。

**管线（四步，全部内生）**：

1. **源头用 API 枚举，不用人肉粘贴**。用户粘的清单必然漏。先找该站的结构化接口（HuggingFace: `/api/models?author=<user>&limit=1000`，靠 `Link: rel="next"` 翻页），全量拉下来写入一个 JSON。
2. **逐项补字段**：多线程抓详情，`ThreadPoolExecutor(max_workers=10)` 足够（209 个仓约 5 秒）。**边拉边存**，脚本可断点续跑。
3. **Python 拼 HTML**，`json.dumps(rows)` 注入成 JS 数组，排序/筛选全在前端，无服务器无网络。
4. 回复里 `::preview{file=...}` 渲染，同时落 CSV + Markdown 供下载（MEDIA:）。

**行动按钮分两层**：

- **行级**：状态相关的动作（如「拉这个」/「看看」）。按行的数据决定按钮形态与提示词，**提示词由行的字段动态拼**。提示词还要写全（写清判据、写入文件的位置、结束条件），因为用户点它时期望的是执行不是闲聊。
- **顶部批量**：跨行操作（「拼入另一批数据」「按某维度重排」）。
- 行级按钮还常见一类**无副作用的纯前端按钮**（只看 GGUF / 重置筛选）。它们不挂 send，只调本地 JS。

**多列表必须先定列号，不能默认第一列**。上游官方基准表常是「同一家族多型号横向对照」，下表头可能是 `['', 'Qwen3.5-27B', 'Gemma4-31B', 'Qwen3.5-35BA3B', 'Qwen3.6-35BA3B', …]`。该卡对应的型号可能在第 5 列。**取错列会把整列分数换成别的型号的**，而且数值看着完全合理，不会抛异常。正确做法是先解析表头。用归一化匹配（去除非字母数字、转小写、子串包含）定位该卡对应的列号，再按列号取值。匹配不到时才退到第一列。发布后至少抽 2–3 张卡人工交叉验一列。

**跨表取值要标来源**：同一个数据集里，不同列可能来自不同的表。如 agentic 分来自上游对照表，KL/MMLU 来自 lm-eval 块。**要在表头或副标题里把来源分开写明**，否则用户会把两本账揉成一个结论。

**缺口要显式说明**：源数据里没有的字段（如逐量化档的 PPL）不要留空让人误读成 0，表里写「—」。还要单独一句话说明「共 X/Y 个仓有该字段」。

### 视图控制（宽/缩放/弹出/全屏）

用户看完长表必问的四件事，逐个给：

- **表格 = 页面宽**：**不要给滚动容器加 `max-width`**。框架宽度按内容测量，`max-width` 会让表比框架窄。直接让表驱动宽度（避免无限宽）。真要限宽就用 `max-width:min(1180px,94vw)`，那是为了防 20+ 列 `nowrap` 撑爆。
- **缩放**：纯前端，外层包一个 `#zbox`，按钮设 `#zbox.style.zoom`（Chromium/webview 支持）。**必带上下限钳制**（如 0.5–2.4），并把当前百分比回显在按钮上。
- **弹出窗口化**：**不能靠 `window.open()`**（iframe 沙箱常禁弹窗）。正解是挂 `window.hermes.send('用 desktop_preview 把 <文件> 开在侧边预览面板里，标签叫 <名>')`。助手那一轮拿到指令后调 `desktop_preview(action='open', url='<绝对路径>')`。面板是持久侧栏，比内嵌组件大得多。
- **全屏**：**实测确认：内嵌 iframe 的 `requestFullscreen()` 被沙箱拒**（按钮点下去后兜底分支执行了）。所以必须写 `.catch(兜底)`，`if(!el.requestFullscreen)` 也走兜底。兜底 = 发 `window.hermes.send` 让助手开预览面板，再套大空间布局。**要诚实告知用户哪一路生效。**
- **二者都是可选，不是默认项**：弹出 + 全屏做成按钮挂着就行，但**不要在交付时主动加**。用户实测后觉得「没必要」，明确叫停了（2026-10-06）。先交「全宽 + 缩放」，用户真要再补。

面板控制类工具（助手侧，不是文件内）：`desktop_preview` 开/关/读侧边预览面板。`focus_pane` 显式聚焦 chat/files/terminal/review/sessions（不含 preview）。`apply_layout` 套布局预设（default/focus/terminal-deck/quad）。`gui_tour(surface='preview')` 在预览页上做引导圈点。

## 何时不用本组件

- 要**持久面板**（sidebar 级、拖拽停靠、状态栏 chip）→ 用 hermes-desktop-plugins skill（plugin.js）。
- 要**演示型整页**（海报、小游戏、可滚动长页）：它是 standalone PAGE，可以脱离 app 主题自设配色。但聊天内嵌组件永远遵守铁律 1/2。
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
