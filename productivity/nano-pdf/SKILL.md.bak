---
name: nano-pdf
description: "用自然语言指令编辑现有 PDF 文字时使用。只要涉及改 PDF 里的标题、日期、错字或内容，就主动加载，即使用户只是说「把这份 PDF 的某处改一下」。不用于合并/拆分/加密（用 pdf）或扫描件 OCR（用 ocr-and-documents）。"
version: 1.0.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Editing, NLP, Productivity]
    homepage: https://pypi.org/project/nano-pdf/
    related_skills: [pdf, ocr-and-documents]
---

# nano-pdf

用自然语言指令编辑 PDF：指向某一页，描述要改什么即可。结构性 PDF 工作（合并、拆分、表单、水印、创建）见 `pdf` skill；扫描件文字提取见 `ocr-and-documents`。

## 前置条件

```bash
# Install with uv (recommended — already available in Hermes)
uv pip install nano-pdf

# Or with pip
pip install nano-pdf
```

## 用法

```bash
nano-pdf edit <file.pdf> <page_number> "<instruction>"
```

## 示例

```bash
# Change a title on page 1
nano-pdf edit deck.pdf 1 "Change the title to 'Q3 Results' and fix the typo in the subtitle"

# Update a date on a specific page
nano-pdf edit report.pdf 3 "Update the date from January to February 2026"

# Fix content
nano-pdf edit contract.pdf 2 "Change the client name from 'Acme Corp' to 'Acme Industries'"
```

## 注意

- 页码是 0-based 还是 1-based 取决于版本——若改到了错误的页，用 ±1 重试
- 编辑后务必核验输出 PDF（用 `read_file` 检查文件大小，或打开它）
- 该工具底层用 LLM——需要 API key（用 `nano-pdf --help` 查配置）
- 适合文字修改；复杂版式改动可能需要别的方案
