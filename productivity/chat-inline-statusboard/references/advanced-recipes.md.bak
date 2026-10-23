# 进阶配方（聊天内嵌组件）

## 1. 自更新面板的标准模式（回话闭环）

面板不是静态物——完整闭环 = 面板展示状态 → 按钮发隐藏指令 → 助手干活 → **patch 面板文件** → 面板变。

实现要点：
- 面板里每条线/项带 `id`（如 `<div class="card" id="line-probe">`），方便 patch 定位。
- 助手回答按钮指令时，工具调用用 patch 改对应卡片的徽章文字/颜色/状态行，例：
  `<span class="badge b-stuck">卡住</span>` → `<span class="badge b-paid">已完结</span>`。
- 状态行更新格式：`<p class="gift">↳ …</p>` 追加新的馈入行（旧馈入行折叠成 `<del>` 或删除，保三行粒度）。
- 标题时间戳同步：`（截至 2026-10-05 16:00 EDT）` → 新的 `date -Iseconds` 输出。

## 2. 语义色徽章系统（跨面板统一）

| 状态 | class | 边框/文字色 | 用途 |
|---|---|---|---|
| 卡住/失败 | `b-stuck` | #b85450 | 等用户输入、FAIL、STUCK |
| 待执行/弹药齐 | `b-armed` | #d79b00 | 排期中、已就绪未跑 |
| 已完结 | `b-paid` | #82b366 | 验证过、有数的完成 |
| 论文级资产 | `b-paper` | #9673a6 | 可直接进论文的结果 |
| 普通/进行中 | （默认） | var(--muted-foreground) | 中性 |

颜色语义在所有面板保持一致——用户看第二次就能读状态。

## 3. 多面板项目的文件组织

```
<项目树>/framework/dataset_v2/
  boards/
    four_threads_status.html     # 主状态板
    e9_verdicts.html             # 专题：E9 裁决链
    k6_executor.html             # 专题：控制器弹药
```
- 主板放总览；专题板从主板按钮跳（按钮 data-hermes-send="打开 e9_verdicts 面板"→ 助手发 ::preview 新面板）。
- 每板标题带「截至」时间戳；同屏最多开两块板（聊天流是垂直的，多了叠罗汉）。

## 4. 嵌入已有图片/图表（混排）

- E 线实验的 PNG 图（figures_E9/fig3_injection_decay.png 等）**不能**用本地 markdown 图片路径放进面板——聊天内嵌组件只认 HTML 文件本身。
- 正确做法：a) 面板里放数据摘要（关键数字表）；b) 真图在**聊天正文**用 `MEDIA:/path/fig3.png` 单独发（桌面版会内联渲染）；c) 面板与图互为补充：板管状态、图管证据。

## 5. 典型开场白文案模式（给用户的按钮提示词写法）

- 差：`继续`（无信息量，助手还要猜）
- 差：`解释一下`（指向不明）
- 好：`按合流顺序给 E10 包 + P1 v2 重训 + M1 的预注册草案，判据和阵亡条款写死`
- 好：`把 G4 行为②的近平局例外写进冻结件草案，标「待指挥官批准」`

模式：**动词 + 对象 + 交付形态 + 约束**。按钮是给未来自己下的订单。

## 6. 排版陷阱补遗

- `grid-template-columns: 1fr 1fr` 在窄预览（侧边栏半宽）会挤——可用 `repeat(auto-fit, minmax(280px, 1fr))` 自适应。
- 行内 flex 徽章换行错位：h3 上加 `flex-wrap: wrap`。
- 中文长词（URL/文件名）撑破卡片：p 里加 `word-break: break-all` 或 `overflow-wrap: anywhere`。
- 面板高度超过一屏时首行会被测量成全宽：把最宽元素（宽表）放卡片内且限 `max-width: 100%; overflow-x: auto`。
