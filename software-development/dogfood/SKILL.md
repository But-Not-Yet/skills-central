---
name: dogfood
description: "对 Web 应用做探索式 QA 时使用：找 bug、留证据、出报告。只要要系统性浏览网页、复现问题并输出结构化缺陷报告，就主动加载，即使用户没明说 dogfood。走浏览器工具集五阶段流程。"
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qa, testing, browser, web, dogfood]
    related_skills: []
---

# Dogfood：系统化的 Web 应用 QA 测试

## Overview（概览）

本技能引导你用 browser 工具集对 Web 应用做系统化的探索式 QA 测试。你会导航应用、与元素交互、为问题留存证据，并产出一份结构化的缺陷报告。

## Prerequisites（前置）

- 必须有 browser 工具集（`browser_navigate`、`browser_snapshot`、`browser_click`、`browser_type`、`browser_vision`、`browser_console`、`browser_scroll`、`browser_back`、`browser_press`）
- 用户给出目标 URL 与测试范围

## Inputs（输入）

用户提供：
1. **Target URL** — 测试的入口点
2. **Scope** — 聚焦哪些区域/功能（或 "full site" 表示全面测试）
3. **Output directory**（可选）— 截图与报告的存放处（默认：`./dogfood-output`）

## Workflow（流程）

按这个五阶段系统化流程走：

### Phase 1: Plan（规划）

1. 创建输出目录结构：
   ```
   {output_dir}/
   ├── screenshots/       # Evidence screenshots
   └── report.md          # Final report (generated in Phase 5)
   ```
2. 依据用户输入确定测试范围。
3. 规划要测的页面与功能，画出粗略站点地图：
   - 落地页/首页
   - 导航链接（页眉、页脚、侧栏）
   - 关键用户流程（注册、登录、搜索、结账等）
   - 表单与交互元素
   - 边界情况（空状态、错误页、404）

### Phase 2: Explore（探索）

对计划中的每个页面或功能：

1. **导航**到该页面：
   ```
   browser_navigate(url="https://example.com/page")
   ```

2. **拍快照**理解 DOM 结构：
   ```
   browser_snapshot()
   ```

3. **检查控制台**有无 JavaScript 报错：
   ```
   browser_console(clear=true)
   ```
   每次导航后、每次重要交互后都要做。静默的 JS 报错是高价值发现。

4. **拍带标注的截图**，目视评估页面并识别可交互元素：
   ```
   browser_vision(question="Describe the page layout, identify any visual issues, broken elements, or accessibility concerns", annotate=true)
   ```
   `annotate=true` 标志会在可交互元素上叠加编号 `[N]` 标签。每个 `[N]` 对应后续浏览器命令所用的 ref `@eN`。

5. **系统化测试交互元素**：
   - 点击按钮和链接：`browser_click(ref="@eN")`
   - 填表单：`browser_type(ref="@eN", text="test input")`
   - 测键盘导航：`browser_press(key="Tab")`、`browser_press(key="Enter")`
   - 滚动内容：`browser_scroll(direction="down")`
   - 用非法输入测试表单校验
   - 测试空提交

6. **每次交互后**检查：
   - 控制台报错：`browser_console()`
   - 视觉变化：`browser_vision(question="What changed after the interaction?")`
   - 预期行为 vs 实际行为

### Phase 3: Collect Evidence（收集证据）

对发现的每个问题：

1. **截图**展示该问题：
   ```
   browser_vision(question="Capture and describe the issue visible on this page", annotate=false)
   ```
   保存响应里的 `screenshot_path`——报告里会引用它。

2. **记录细节**：
   - 问题出现的 URL
   - 复现步骤
   - 预期行为
   - 实际行为
   - 控制台报错（若有）
   - 截图路径

3. 用问题分类法给问题**定级分类**（见 `references/issue-taxonomy.md`）：
   - 严重度：Critical / High / Medium / Low
   - 类别：Functional / Visual / Accessibility / Console / UX / Content

### Phase 4: Categorize（归类）

1. 通览所有收集到的问题。
2. 去重——把同一 bug 在不同位置表现的问题合并。
3. 给每个问题定最终的严重度与类别。
4. 按严重度排序（Critical 在前，然后 High、Medium、Low）。
5. 按严重度与类别统计数量，供执行摘要使用。

### Phase 5: Report（报告）

用 `templates/dogfood-report-template.md` 的模板生成最终报告。

报告必须包含：
1. **执行摘要**：问题总数、按严重度的分布、测试范围
2. **逐问题小节**，含：
   - 问题编号与标题
   - 严重度与类别徽标
   - 观察到问题的 URL
   - 问题描述
   - 复现步骤
   - 预期行为 vs 实际行为
   - 截图引用（内嵌图片用 `MEDIA:<screenshot_path>`）
   - 相关的控制台报错
3. 所有问题的**汇总表**
4. **测试说明**——测了什么、没测什么、有什么阻碍

报告保存到 `{output_dir}/report.md`。

## Tools Reference（工具速查）

| Tool | 用途 |
|------|---------|
| `browser_navigate` | 访问某 URL |
| `browser_snapshot` | 取 DOM 文本快照（无障碍树） |
| `browser_click` | 按 ref（`@eN`）或文本点击元素 |
| `browser_type` | 往输入框里打字 |
| `browser_scroll` | 页面上/下滚动 |
| `browser_back` | 浏览器历史后退 |
| `browser_press` | 按键 |
| `browser_vision` | 截图 + AI 分析；用 `annotate=true` 加元素标签 |
| `browser_console` | 取 JS 控制台输出与报错 |

## Tips（技巧）

- **导航后、重要交互后一律检查 `browser_console()`。** 静默的 JS 报错属于最有价值的发现。
- **需要推断可交互元素位置、或快照 ref 不清晰时，用 `browser_vision` 配 `annotate=true`。**
- **用合法与非法输入各测一遍**——表单校验 bug 很常见。
- **长页面滚到底**——折叠线以下的内容可能有渲染问题。
- **测导航流程**——端到端点完多步流程。
- **检查响应式行为**，留意截图里可见的布局问题。
- **别忘了边界情况**：空状态、超长文本、特殊字符、快速连点。
- 把截图汇报给用户时带上 `MEDIA:<screenshot_path>`，让他们能内嵌看到证据。
