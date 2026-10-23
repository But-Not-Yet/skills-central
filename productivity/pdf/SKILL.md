---
name: pdf
description: "创建、合并、拆分、填写、加密 PDF 时使用。只要涉及 PDF 的合并/拆分/旋转、水印、表单填写、加密解密或提取文字表格，就主动加载，即使用户只是提到一个 .pdf 文件。不用于扫描件重度 OCR（用 ocr-and-documents）或自然语言改字（用 nano-pdf）。"
version: 1.0.0
author: Anthropic (adapted by Nous Research)
license: Proprietary. LICENSE.txt has complete terms
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Forms, Office, Productivity]
    category: productivity
    related_skills: [ocr-and-documents, nano-pdf, docx, xlsx]
---

# PDF 技能

创建、合并、拆分、变换并保护 PDF 文件——合并、页面操作、表单填写、水印、加密以及文字/表格抽取。扫描文档的重度文字抽取优先用 `ocr-and-documents` skill；对现有 PDF 文字做自然语言编辑优先用 `nano-pdf`。

## 何时使用

只要用户想对 PDF 文件做任何事就用本 skill：读取或抽取文字/表格、合并多个 PDF、拆分 PDF、旋转页面、添加水印、创建新 PDF、填写 PDF 表单、加密/解密、抽取图片，或对扫描件 PDF 做 OCR。只要用户提到 .pdf 文件或要求生成一份，就用本 skill。

## 前置条件

```bash
pip install pypdf pdfplumber reportlab
which pdftotext || sudo apt install -y poppler-utils   # pdftotext, pdftoppm, pdfimages
which qpdf || sudo apt install -y qpdf                 # CLI merge/split/decrypt
```

macOS：`brew install poppler qpdf`。OCR 附加：`pip install pytesseract pdf2image` + `sudo apt install -y tesseract-ocr`。

> 下方脚本路径相对于本 skill 目录。表单填写有独立流程——读 [forms.md](forms.md) 并照做。进阶库用法（pypdfium2、pdf-lib）与排查：[reference.md](reference.md)。

## 快速参考

| 任务 | 最佳工具 | 命令/代码 |
|------|-----------|--------------|
| 合并 PDF | pypdf | 每页 `writer.add_page(page)` |
| 拆分 PDF | pypdf | 每页一个文件 |
| 抽取文字 | pdfplumber | `page.extract_text()` |
| 抽取表格 | pdfplumber | `page.extract_tables()` |
| 创建 PDF | reportlab | Canvas 或 Platypus |
| 命令行合并/拆分 | qpdf | `qpdf --empty --pages ...` |
| OCR 扫描件 PDF | pytesseract | 先转成图片（或用 `ocr-and-documents`） |
| 填写 PDF 表单 | 见 [forms.md](forms.md) | `scripts/fill_fillable_fields.py` 等 |
| 编辑已有文字 | `nano-pdf` skill | `nano-pdf edit file.pdf <page> "<instruction>"` |

## 常用操作

### 合并 / 拆分 / 旋转（pypdf）

```python
from pypdf import PdfReader, PdfWriter

# Merge
writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf"]:
    for page in PdfReader(pdf_file).pages:
        writer.add_page(page)
with open("merged.pdf", "wb") as f:
    writer.write(f)

# Split: one file per page
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    w = PdfWriter(); w.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as f:
        w.write(f)

# Rotate
page = reader.pages[0]
page.rotate(90)  # clockwise
```

### 抽取文字与表格（pdfplumber）

```python
import pdfplumber, pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    tables = [pd.DataFrame(t[1:], columns=t[0])
              for page in pdf.pages
              for t in page.extract_tables() if t]
```

### 创建 PDF（reportlab）

```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate("report.pdf", pagesize=letter)
styles = getSampleStyleSheet()
story = [Paragraph("Report Title", styles["Title"]), Spacer(1, 12),
         Paragraph("Body text...", styles["Normal"]), PageBreak(),
         Paragraph("Page 2", styles["Heading1"])]
doc.build(story)
```

**下标/上标：** 绝不要用 Unicode 下标/上标字符（₀₁₂、⁰¹²）——内置字体缺少这些字形，会渲染成实心黑方块。在 `Paragraph` 对象内用 `<sub>`/`<super>` 标记：`Paragraph("H<sub>2</sub>O", styles['Normal'])`。对 canvas 绘制的文字，手动调整字号与位置。

### 命令行工具

```bash
pdftotext -layout input.pdf output.txt                     # text, layout preserved
pdftotext -f 1 -l 5 input.pdf output.txt                   # pages 1-5
qpdf --empty --pages file1.pdf file2.pdf -- merged.pdf     # merge
qpdf input.pdf --pages . 1-5 -- pages1-5.pdf               # split range
qpdf input.pdf output.pdf --rotate=+90:1                   # rotate page 1
qpdf --password=pw --decrypt encrypted.pdf decrypted.pdf   # remove password
pdfimages -j input.pdf img                                 # extract images
```

### 水印

```python
from pypdf import PdfReader, PdfWriter

watermark = PdfReader("watermark.pdf").pages[0]
reader, writer = PdfReader("document.pdf"), PdfWriter()
for page in reader.pages:
    page.merge_page(watermark)
    writer.add_page(page)
with open("watermarked.pdf", "wb") as f:
    writer.write(f)
```

### 密码保护

```python
writer.encrypt("userpassword", "ownerpassword")
```

### OCR 扫描件 PDF

```python
import pytesseract
from pdf2image import convert_from_path

pages = convert_from_path("scanned.pdf")
text = "\n\n".join(pytesseract.image_to_string(img) for img in pages)
```

扫描件的批量/结构化抽取，`ocr-and-documents` skill（pymupdf、marker-pdf）是更好的路子。

## 表单填写

先读 [forms.md](forms.md)——它区分可填写（AcroForm）PDF 与扁平扫描表单，并逐一讲解辅助脚本：

- `scripts/check_fillable_fields.py`——该 PDF 有 AcroForm 字段吗？
- `scripts/extract_form_field_info.py` / `scripts/extract_form_structure.py`——枚举字段
- `scripts/fill_fillable_fields.py`——填写 AcroForm 字段
- `scripts/fill_pdf_form_with_annotations.py`——在扁平表单上叠加文字
- `scripts/check_bounding_boxes.py`、`scripts/create_validation_image.py`——可视化核验位置

## 常见坑

- `page.extract_text()` 在纯图片页上返回 `None`——用 `or ""` 兜底并回退到 OCR。
- pypdf 保留加密标志：读加密 PDF 需要 `PdfReader(path, password=...)` 才能访问页面。
- reportlab 坐标以左下角为原点，单位是点（1/72″）——不是左上角。
- 用批注叠加填写扁平表单时，交付前务必渲染一张校验图并检查位置。

## 验证

1. 用 `PdfReader` 打开产出并断言预期页数。
2. 从产出中重新抽取文字（`pdftotext` 或 pdfplumber），确认你添加的内容在其中。
3. 对任何视觉产物（水印、填写过的表单、创建的报表）：`pdftoppm -jpeg -r 100 output.pdf page`，用 `vision_analyze` 检查图片。

## 相关 skill

`ocr-and-documents`（扫描文档文字抽取）、`nano-pdf`（原地自然语言改字）、`docx`（Word）、`xlsx`（电子表格）、`powerpoint`（演示文稿）。
