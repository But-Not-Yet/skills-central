---
name: latex-research-writing
description: "写 LaTeX 科研文档时使用。只要涉及学术规范、编译验证或中文 LaTeX 处理，就主动加载。"
version: 1.0.0
---

# LaTeX 科研文档写作

## 学术规范
- 缩写符合 IEEE 规范：首次出现写全称 + 括号缩写。
- 学术严谨语气；数学表达式写成可实施级的编号公式。
- 引用须联网核实（作者/年份/期刊卷页），不凭记忆造参考文献。
- 面向审稿人的文档保持克制：不追求形式完备，不做预注册（用户偏好灵活迭代）。
- 面向投资人/客户的文档：不要更深层的数学推导。

## 交付流程
1. 文档修订前先出「修改大纲 + 修改理由 + 引用资料」供用户审阅，批准后再动手。
2. 交付产物新建独立文件夹组织（如 `科研/latex_v2.1/`），不堆在工作区根目录。
3. 中文文档用 XeLaTeX；中文路径编译乱码时复制到 `/tmp/latex_build` 编译后同步 PDF 回原目录。

## 编译验证（交付门槛）
- 每次 .tex 修改后必须 `latexmk` 编译通过（日志尾部出现 `Output written on ...pdf`）才算完成。
- 编译后全文搜索双重转义残留（`\\section`、`\\begin` 这类误转义）。
- 交付标准：0 错误、0 未定义引用。

## 已知陷阱
- patch 工具编辑 .tex 时 new_string 中 LaTeX 命令必须单反斜杠。
- 本机无 LibreOffice；pdftoppm（TeXLive 提供）可用于 PDF→图片 QA。
- Python 脚本（generate_ppt.py 等）运行时 venv 污染问题：
  `env -u VIRTUAL_ENV -u PYTHONPATH PATH="/c/Python313:..." /c/Python313/python.exe <script>`
- pip 国内网络用清华镜像：`pip install <pkg> -i https://pypi.tuna.tsinghua.edu.cn/simple`。
