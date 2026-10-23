# LaTeX 编辑陷阱与编译验证清单（patch 工具 × .tex 文件实战教训）

来源：2026-08 战略报告（人力资源.tex）编辑实战。用户报告"无法编译"，根因是 patch 引入的双重转义与多处 TikZ/pgfplots/pgfgantt 语法错误。以下每条都对应一次真实编译失败。

## 陷阱 1：patch new_string 中 LaTeX 单反斜杠被写成双反斜杠（最严重）

- 症状：`\section` → `\\section`、`\begin` → `\\begin`、`\item` → `\\item`、数学模式 `$y_{\mathrm{raw}}$` → `$y_{\\mathrm{raw}}$`、`$\checkmark$` → `$\\checkmark$`，整段环境全部编译失败。
- 根因：在 patch 参数里写 LaTeX 命令时按 JSON/Python 习惯过度转义。
- 规则：**patch 的 new_string 里 LaTeX 命令一律单反斜杠**。提交后立刻全文搜索双重转义残留并还原：
  - 搜索模式：`\\\\section`、`\\\\subsection`、`\\\\begin`、`\\\\end`、`\\\\item`、`\\\\checkmark`、`\\\\times`、`\\\\addplot`、`\\\\gantttitle`、`\\\\ganttbar`
  - 行首锚定搜索 `^\\\\\\\\(section|begin|end|item)` 可快速定位整段被污染的区域。

## 陷阱 2：TikZ 节点与定位

- `\n`（Python 风格换行）在 TikZ 节点内**无效** → 节点文本换行用 `\\`，且节点样式必须带 `align=center`（建议封装 `box/.style={draw, rounded corners, align=center, ...}`）。
- `right=1.5cm of X` 定位语法**必须** `\usetikzlibrary{positioning}`，否则直接报错。
- 引入顺序（放在 ctex/hyperref 之后）：
  ```latex
  \usepackage{pgfplots}
  \pgfplotsset{compat=1.17}
  \usepackage{pgfgantt}
  \usetikzlibrary{positioning}
  ```

## 陷阱 3：pgfgantt 甘特图

- `time slot format=isodate-yearmonth` 与标签内含裸 `&`（如"论文 & 数据探索"）→ 解析失败。
- 稳妥写法：整数时间槽 `\begin{ganttchart}{1}{14}` + `\gantttitle{2026}{5}` 手动标注年/季 + 标签内 `\&` 转义。
- `\gantttitlelist{Q3,Q4,Q1}{1,...,3}` 的列表数必须等于时间槽数。

## 陷阱 4：longtable / tabular 行尾与特殊字符

- `\\[2pt]` 行距控制在 `p{}` 列的某些位置会报错/错位 → 数据行统一裸 `\\` 行尾，行距靠 `\renewcommand{\arraystretch}` 或 booktabs 间距控制。
- 单元格内希腊字母必须数学模式：`(α, τ)` → `($\alpha$, $\tau$)`。
- Unicode 非断字连字符 `‑`（U+2011）LaTeX 不识别 → 一律改 `--`（如 第28--29条）。
- 表内 `✓/✗` 用 `$\checkmark$` / `$\times$`，不要直接贴 Unicode 字符。

## 陷阱 5：figure 插入位置

- 在 itemize 的 `\item` 文本中间插入 figure 环境会把句子截成两段 → 先写完句子，figure 放在该 `\item` 文本结束之后、下一个 `\item` 之前，或移出列表。
- pgfplots 的 axis 选项里 `width=0.9\linewidth` 注意单反斜杠（同陷阱 1）。

## 陷阱 6：中文路径/中文文件名 latexmk 编译失败（Windows CP936）

- 症状：latexmk 报 `! ==> Fatal error occurred`，日志中文件名显示为乱码（如 `ʵʩ`），根因是 CP936 控制台代码页无法正确处理中文文件名。
- 注意：**并非所有中文路径都会失败**——同一台机器上 `人力资源.tex` 可就地编译，而 `实施方案.tex` 失败。遇到失败不要排查宏包，先换路径。
- 可靠兜底流程（每次必成）：
  ```bash
  mkdir -p /tmp/latex_build && cp "原文件.tex" /tmp/latex_build/main.tex
  cd /tmp/latex_build && latexmk -pdf -interaction=nonstopmode main.tex
  cp main.pdf "回原目录/目标名.pdf"
  ```
- **目标 PDF 被阅读器占用**（cp 报 `Device or resource busy`）：不要覆盖，改存为新文件名 `_vX.X.pdf`（如 `实施方案_v1.1.pdf`），并在汇报中说明。

## 编译验证（每次 .tex 编辑后必做，不验证不报告完成）

1. `latexmk -pdf -interaction=nonstopmode 文件.tex`；若中文路径失败，按陷阱 6 走 /tmp 流程。
2. 日志尾部出现 `Output written on xxx.pdf (N pages, ...)` 才算成功；否则按日志最后一个 Error 定位。
3. 声明完成前，用 search_files 全文扫 `^\\\\\\\\(section|begin|end|item)` 与 `\\\\addplot` 确认无双重转义残留。
4. 编译产物（.aux/.log/.out）中 "Missing character: There is no X in font nullfont" 通常意味着正文混入了未被环境包裹的命令字符（如双重转义后的 `\\` 文本）。
