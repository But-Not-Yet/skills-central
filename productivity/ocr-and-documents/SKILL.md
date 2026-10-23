---
name: ocr-and-documents
description: "从 PDF 或扫描件提取文字时使用（pymupdf、marker-pdf）。只要涉及扫描件 OCR、复杂版式/公式/表格抽取或批量文档转 markdown，就主动加载。即使用户只是说「把这份扫描件转成文字」。不用于 PDF 合并/拆分/表单（用 pdf）。"
version: 2.3.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [pdf, docx, powerpoint]
---

# PDF 与文档抽取

DOCX：见 `docx` skill（创建/编辑），或用 `python-docx` 做结构化读取。
PPTX：见 `powerpoint` skill（完整的创建/读取/编辑支持）。
PDF 操作（合并、拆分、表单、水印、创建）：见 `pdf` skill。
本 skill 覆盖 **从 PDF 与扫描文档中提取文字**。

## 第 1 步：有远程 URL 吗？

若文档有 URL，**总是先试 `web_extract`**：

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

它通过 Firecrawl 完成 PDF 转 markdown，无本地依赖。

仅在以下情况用本地抽取：文件在本地、web_extract 失败，或需要批量处理。

## 第 2 步：选择本地抽取器

| 特性 | pymupdf (~25MB) | marker-pdf (~3-5GB) |
|---------|-----------------|---------------------|
| **文本型 PDF** | ✅ | ✅ |
| **扫描型 PDF (OCR)** | ❌ | ✅（90+ 语言） |
| **表格** | ✅（基础） | ✅（高精度） |
| **Equations / LaTeX** | ❌ | ✅ |
| **代码块** | ❌ | ✅ |
| **表单** | ❌ | ✅ |
| **页眉/页脚移除** | ❌ | ✅ |
| **阅读顺序检测** | ❌ | ✅ |
| **图片抽取** | ✅（内嵌） | ✅（带上下文） |
| **Images → text (OCR)** | ❌ | ✅ |
| **EPUB** | ✅ | ✅ |
| **Markdown 输出** | ✅（经 pymupdf4llm） | ✅（原生，质量更高） |
| **安装体积** | ~25MB | ~3-5GB（PyTorch + 模型） |
| **速度** | 即时 | ~1-14s/page (CPU), ~0.2s/page (GPU) |

**决策**：除非需要 OCR、公式、表单或复杂版式分析，否则用 pymupdf。

若用户需要 marker 的能力，但系统没有约 5GB 空闲磁盘：
> 「这份文档需要 OCR/高级抽取（marker-pdf），它需要约 5GB 用于 PyTorch 和模型。你的系统有 [X]GB 空闲。选项：腾出空间；提供一个 URL 让我用 web_extract；或者我试用 pymupdf——它适用于文本型 PDF。但处理不了扫描文档或公式。」

---

## pymupdf（轻量）

```bash
pip install pymupdf pymupdf4llm
```

**通过辅助脚本**：
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**内联**：
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf（高质量 OCR）

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**通过辅助脚本**：
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI**（随 marker-pdf 安装）：
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## arXiv 论文

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## 拆分、合并与搜索

pymupdf 原生支持这些——用 `execute_code` 或内联 Python：

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

无需额外依赖——pymupdf 一个包就覆盖拆分、合并、搜索与文字抽取。

---

## 注意

- 对 URL，`web_extract` 永远是首选
- pymupdf 是稳妥的默认项——即时、无需模型、到处能用
- marker-pdf 用于 OCR、扫描件、公式、复杂版式——仅在需要时安装
- 两个辅助脚本都接受 `--help` 查看完整用法
- marker-pdf 首次使用时下载约 2.5GB 模型到 `~/.cache/huggingface/`
- 对 Word 文档：`pip install python-docx`（胜过 OCR——解析真实结构）
- 对 PowerPoint：见 `powerpoint` skill（使用 python-pptx）
