---
name: latex-research-writing
description: "写 LaTeX 科研文档时使用。只要涉及学术规范、编译验证或中文 LaTeX 处理，就主动加载。"
version: 1.0.0
---

# LaTeX 科研文档写作

## 学术规范
- 缩写符合 IEEE 规范：首次出现写全称 + 括号缩写。
- 学术严谨语气。数学表达式写成可实施级的编号公式。
- 引用须联网核实（作者/年份/期刊卷页），不凭记忆造参考文献。
- 页码/卷号没把握就删掉该字段，宁可条目不完整也不编一个看起来像的。
- 面向审稿人的文档保持克制：不追求形式完备，不做预注册（用户偏好灵活迭代）。
- 面向投资人/客户的文档：不要更深层的数学推导。

## 写给主人本人的文档（非投稿稿）的腔调
- 讨论整理稿是「写给我看的」：人话优先、低术语密度，学术压缩腔会被顶回「完全看不懂」。
- 每节开头先说这一节回答什么问题。术语第一次出现就用日常语言解释（值函数=离目标还有多远 这类）。
- 关键数字必须配基线才能解读（精确率要对照随机基线/目标类占比，否则数字无意义）。
- 写「当前实验进度」一节前，先跑项目仓库 `git log --oneline` 并查看板（kanban_list）——最新提交与看板卡才是最新成果。别只读最新的 .md 文件或凭记忆。
- 归因写档案原文的归因，不外推（失败归训练配方就别写成归模型类）。全称断言（「全部」「已被证伪」）先数证据再写。

## 作业解答 / 数学推导类文档（主人裁定腔调）
- **极简符号化**：推导用公式链推进（`\implies`、`\xrightarrow`、下标注条件），文字只留一句结论或一句核对；长段讨论、逐条英文解释会被顶回「长篇大论太多了」。数值对照用 `tabular`，不用文字复述。
- 主人会亲自动手改其中几节：**他改过的节就是全文文风基准**，新写部分向他靠（结构、公式密度、caption 长度、SOLUTION 缩进层级都照抄），不要再交一个自己风格的版本。
- tex 里的核对数字（如 c2d 差值范数）必须来自实跑的日志/脚本输出回填，禁止先写预估值占位交稿——跑完逐处替换成实测值。
- 外挂解答文件：只写 `\section` 起的内容，不重复 documentclass/`\begin{document}`；主文档 `\input` 挂载，每题前 `\clearpage`。题目点名要求某工具函数（`ode45`、`c2d`）时，该核对必须真用该工具跑（见 ssh-windows-remote-ops 的 MATLAB 一键跑法），Python 只能替代「任一精确积分器」措辞的部分。
- 截止时间临近：先把「只含已验证内容」的最小版本 include + 编译出保底 PDF，再分题迭代——改 include 结构不许让交付窗口内出现编译中断。

## 交付流程
1. 文档修订前先出「修改大纲 + 修改理由 + 引用资料」供用户审阅，批准后再动手。
2. 交付产物新建独立文件夹组织（如 `科研/latex_v2.1/`），不堆在工作区根目录。
3. 中文文档用 XeLaTeX。中文路径编译乱码时复制到 `/tmp/latex_build` 编译后同步 PDF 回原目录。

## 编译验证（交付门槛）
- 每次 .tex 修改后必须 `latexmk` 编译通过（日志尾部出现 `Output written on ...pdf`）才算完成。
- 编译后全文搜索双重转义残留（`\\section`、`\\begin` 这类误转义）。
- 交付标准：0 错误、0 未定义引用、0 Overfull。用日志 grep 验证而非目测：`grep -cE "Reference .* undefined|Citation .* undefined|multiply defined|^! "` 与 `grep -c Overfull` 都应为 0。

## 中文 IEEEtran 单栏配方（Linux TeXLive，已验证）
- 单栏 IEEE 版式：`\documentclass[technote,singlecolumn]{IEEEtran}`——**technote 选项本身仍是双栏**，漏 `singlecolumn` 会被主人当场识破「这是双栏」。
- 栏宽用机器验证：`pdftotext -bbox <pdf> - | grep -oE 'xMax="[0-9.]+"' | sort -g | tail -1`，单栏应接近整页宽（~570pt），双栏只有 ~95pt。
- 中文：`\usepackage[UTF8]{ctex}` + `\setCJKmainfont{AR PL UMing CN}`（本机 AR PL UMing/UKai 可用），编译用 `xelatex` 两遍（交叉引用）。

## 引用核实配方（arXiv API）
- 按编号批量核：`https://export.arxiv.org/api/query?id_list=<id1>,<id2>&max_results=N`，用 python `urllib.request` 走 **https**（http 明文 curl 可能返回空 entry）。比对编号/标题/首作者/年月。
- 编号不确定时按标题检索：`search_query=all:%22<exact title>%22`——会话里转述的 arXiv 编号常错，标题检索能纠出来。
- 主人提供的、API 查不到的新论文：核验注记里单独写明核验方式（谁提供+档案已读全文）。不与「API 已核」混成一类。

## 已知陷阱
- patch 工具编辑 .tex 时 new_string 中 LaTeX 命令必须单反斜杠。
- 含大量反斜杠的多行 tex 用 patch 工具改容易转义漂移（字面换行符混进正文、行被拼接）。改后立即读回目标行；漂移就改走 execute_code：原生 `open()` 读全文 → `str.replace`（先 `assert count==1`）→ 写回。
- 本机无 LibreOffice。pdftoppm（TeXLive 提供）可用于 PDF→图片 QA。
- Python 脚本（generate_ppt.py 等）运行时 venv 污染问题：
  `env -u VIRTUAL_ENV -u PYTHONPATH PATH="/c/Python313:..." /c/Python313/python.exe <script>`
- pip 国内网络用清华镜像：`pip install <pkg> -i https://pypi.tuna.tsinghua.edu.cn/simple`。
