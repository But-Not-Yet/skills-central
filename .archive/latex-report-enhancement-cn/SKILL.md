---
name: latex-report-enhancement-cn
title: LaTeX 报告可视化增强（中文简洁版）
description: 为商务/战略报告在 LaTeX 中快速加入结构化表格、TikZ 流程图、pgfplots 数据图、pgfgantt 时间线的简洁指南和常用代码片段。
summary: 提供 LaTeX 文档可视化提升的标准化工作流，包括宏包引入、示例代码、常见坑以及参考文件。
---

## 何时使用
- 需要在 LaTeX 文档中加入 **复杂长表格**（`longtable` + `booktabs`）
- 需要绘制 **流程/架构图**（TikZ）
- 需要展示 **数据趋势**（`pgfplots`）
- 需要展示 **项目里程碑 / 融资甘特图**（`pgfgantt`）
- 想统一 **package** 引入并避免编译警告

## 基本步骤（保持简洁）
1. **检查并添加必要宏包**（一次性放在导言区）
   ```latex
   \usepackage{pgfplots}
   \pgfplotsset{compat=1.17}
   \usepackage{pgfgantt}
   \usepackage{tikz}
   \usetikzlibrary{positioning}
   \usepackage{longtable}
   \usepackage{booktabs}
   ```
2. **复制对应代码块**（见 `references/` 中的示例），粘贴到文档合适位置，确保 `figure` 环境包裹。
3. **更新标签**（`\label{}`）后在正文使用 `\ref{}`。
4. **编译** `latexmk -pdf <file>.tex` 检查无错误。
5. **验证双反斜杠膨胀**：patch 后搜索文件确认无 `\\\\section`、`\\\\begin`、`\\\\end` 等双转义残留（`patch` 工具可能将 `\section` 膨胀为 `\\section`）。

## 常见坑与快速修复
- **宏包未导入**：插入第 1 步的 `\usepackage`，防止 `Undefined control sequence`。
- **TikZ `positioning` 库缺失**：使用 `right=of node` 或E语法时必须加 `\usetikzlibrary{positioning}`，否则报 `Package pgf Error`。
- **pgfplots 版本警告**：必须在加载后执行 `\pgfplotsset{compat=1.17}`（或更高）以消除警告。
- **图表宽度超页**：使用 `width=0.9\linewidth`，避免 `Overfull \hbox`。注意：在 pgfplots `width=` 中写 `\linewidth` 而非 `\\linewidth`（单反斜杠）。
- **Gantt `isodate-yearmonth` 在部分 TeX Live 版本下不稳定**：更可靠的方式是用**整数时间槽** + `\gantttitle` 手动标注年份和季度（见下方修正示例）。
- **Gantt `\gantttitlelist{Q3,Q4,...}` 会触发 `Package PGF Math Error: Unknown function 'Q3'`**：裸 `Q3`/`Q4` 标签被 PGF Math 当函数解析。不要用 `\gantttitlelist` 写季度标签；改用多个 `\gantttitle{26Q3}{2}` 手动标注（季度字母前必须带数字前缀）。
- **Gantt 标签含 `&`**：必须转义为 `\&`，否则 LaTeX 会解析为表格列分隔符。
- **表格跨页断行**：`longtable` 自动分页，若出现 `\end{longtable}` 前缺失请检查 `\midrule` 与 `\endhead` 对齐。
- **longtable, tabular 行内禁用 `\\[2pt]` 间距**：在最后一列后用 `\\[2pt]` 会导致 `Misplaced \noalign`。改用标准 `\\` 行尾或全局 `\renewcommand{\arraystretch}{1.2}`。
- **TikZ 节点换行用 `\\` 而非 `\n`**：Python 风格的 `\n` 在 TikZ 节点中无效。必须加 `align=center` 样式后用 `\\`。
- **patch 工具双反斜杠膨胀**：当使用 `patch` 工具替换含 LaTeX 命令的文本时，反斜杠可能被双重转义（`\section` → `\\section`）。**务必在 patch 后全文搜索 `\\\\section`、`\\\\begin` 等双重转义模式并修复**。
- **Unicode 特殊连字符**：`‑`（U+2011 non-breaking hyphen）、`‑`（U+2013 en dash）等在 pdfLaTeX 下不可识别，统一改为标准 ASCII `--`。

## 示例代码（直接复制）
### 市场规模折线图（pgfplots）
```latex
% fig:hr_market
\begin{figure}[htbp]
  \centering
  \begin{tikzpicture}
    \begin{axis}[
      xlabel={Year},
      ylabel={Market Size (Billion USD)},
      xtick={2025,2026,2027,2028,2029,2030,2031,2032},
      grid=both,
      width=0.9\linewidth,
      height=6cm,
      legend pos=north west,
    ]
      \addplot[color=blue,mark=*] coordinates {
        (2025,49) (2026,55.37) (2027,62.57) (2028,70.71)
        (2029,79.90) (2030,90.29) (2031,101.99) (2032,115.25)
      };
      \addlegendentry{HR Analytics}
    \end{axis}
  \end{tikzpicture}
  \caption{HR Analytics 市场规模（2025--2032）预测，基于 CAGR 13\%}
  \label{fig:hr_market}
\end{figure}
```
### 融资甘特图（pgfgantt，整数时间槽版本，更可靠）
```latex
% fig:gantt — 用整数时间槽 + 手动标题，避免 isodate 兼容问题
\begin{figure}[htbp]
  \centering
  \begin{ganttchart}[
    vgrid, hgrid,
    x unit=0.8cm,
    y unit chart=0.6cm,
    title height=1,
    bar height=0.5,
    bar label font=\small,
    title label font=\small
  ]{1}{14}
    \gantttitle{2026}{5} \gantttitle{2027}{6} \gantttitle{2028}{3} \\
    \gantttitle{26Q3}{2} \gantttitle{26Q4}{3} \gantttitle{27Q1}{2} \gantttitle{27Q2}{2} \gantttitle{27Q3}{2} \gantttitle{27Q4}{2} \gantttitle{28Q1}{1} \\
    \ganttbar{Phase 0: 论文 \& 数据探索}{1}{5} \\
    \ganttbar{Phase 1: MVP (Jira 插件)}{6}{8} \\
    \ganttbar{Pre-Seed 融资}{9}{9} \\
    \ganttbar{首批付费客户}{10}{12} \\
    \ganttbar{Series A 融资}{12}{12} \\
    \ganttbar{扩展至 10--50 客户}{13}{14}
  \end{ganttchart}
  \caption{融资与里程碑甘特图}
  \label{fig:gantt}
\end{figure}
```

## 参考文件（已写入 `references/`）
- `references/pgfplots_guide.md` – pgfplots 常用轴参数、颜色、标记示例。
- `references/pgfgantt_guide.md` – Gantt 图时间格式、里程碑颜色、分组技巧。
- `references/tikz_diagrams.md` – 节点/边简写模板。

## 风格约定（用户偏好）
- 采用 **中文**，保持 **简洁**，不做冗余解释。
- 只在必要时提供代码块；不提供额外背景说明。
- 若文档已有对应宏包，**不重复**添加。

---
