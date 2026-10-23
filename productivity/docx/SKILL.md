---
name: docx
description: "创建、读取、编辑 Word .docx/.dotx 与模板时使用。只要涉及 Word 文档、报告/备忘录/信件、批注、修订（红线）或查找替换，就主动加载。即使用户只是提到一个 .docx 文件名。不用于 PDF、表格或演示文稿。"
version: 1.0.0
author: Anthropic (adapted by Nous Research)
license: Proprietary. LICENSE.txt has complete terms
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Word, DOCX, Documents, Office, Productivity]
    category: productivity
    related_skills: [pdf, xlsx, powerpoint, ocr-and-documents]
---

# DOCX 技能

创建、读取、编辑 Word 文档——报告、备忘录、信件、信头、目录、修订（红线）与批注。`.docx` 是 XML 文件的 ZIP 归档。本 skill 兼顾高层创建路径与外科式 XML 编辑。

## 何时使用

只要用户想创建、读取、编辑或操作 Word 文档（.docx）或 Word 模板（.dotx），就用本 skill。触发点包括：任何提到「Word doc」「.docx」「.dotx」，或要求把「报告」「备忘录」「信件」等作为 Word 文件交付。从 .docx 里提取或重组内容。在 Word 文件里查找替换。插入图片。修订或批注。不用于 PDF（见 `pdf` skill）、电子表格（`xlsx`）或演示文稿（`powerpoint`）。

## 前置条件

```bash
npm ls docx --depth=0 2>/dev/null | grep -q docx || npm install docx   # creation (docx-js)
pip show pandoc >/dev/null 2>&1 || true; which pandoc || sudo apt install -y pandoc   # reading
which soffice || sudo apt install -y libreoffice     # rendering/verification
which pdftoppm || sudo apt install -y poppler-utils  # PDF → images
pip install defusedxml lxml   # validation scripts
```

macOS: `brew install pandoc libreoffice poppler`.

## 快速参考

| 任务 | 方式 |
|---|---|
| **创建**新文档 | 写一个 `docx`（npm）脚本——见下方坑 |
| **编辑**已有文档 | `unzip` → 改 `word/document.xml` → `zip`（docx-js 无法打开已有文件） |
| **读取**内容 | `pandoc -t markdown file.docx`（或 `read_file`，它会自动抽取 .docx 文本） |

> 下方脚本路径相对于本 skill 目录。

## 用 docx-js 创建——坑

写脚本并 `require('docx')`。API 模型已知。以下是易踩的雷：

- **页面尺寸默认 A4。** 要 US Letter 就设 `page: { size: { width: 12240, height: 15840 } }`（DXA。1440 = 1″）。
- **横向：** 传纵向尺寸并设 `orientation: PageOrientation.LANDSCAPE`——docx-js 内部会交换宽/高。
- **表格需要双重宽度：** 在表上设 `columnWidths`，并在每个单元格上设 `width`，都用 `WidthType.DXA`（PERCENTAGE 在 Google Docs 里会出问题）。列宽之和必须等于表宽。
- **表格底纹：** 用 `ShadingType.CLEAR`，绝不用 `SOLID`（会渲染成黑色）。
- **列表：** 绝不要字面插入 `•`。用带 `LevelFormat.BULLET` 的 `numbering` 配置。
- **`ImageRun` 需要 `type:`**（`"png"`、`"jpg"` 等）。
- **`PageBreak` 必须在 `Paragraph` 内。**
- **绝不要用 `\n`**——用独立的 `Paragraph` 元素。
- **目录：** 标题必须用内置的 `HeadingLevel.*`。自定义标题样式需设 `outlineLevel`，否则不会出现。
- **不要用表格当水平分隔线**——改用段落底边框。
- **点前导符 / 同行右对齐：** 在 `TextRun` 内用 `PositionalTab`（`alignment: PositionalTabAlignment.RIGHT`、`leader: PositionalTabLeader.DOT`），而不是字面的 `.` 或空格填充。

## 核验产出

写完 `.docx` 后，渲染并查看：

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.docx
pdftoppm -jpeg -r 100 output.pdf page
ls page-*.jpg   # then inspect each with vision_analyze
```

`pdftoppm` 会按总页数的位数给页码补零（`page-01.jpg`…`page-12.jpg`）。

## 编辑已有文档

旧版 `.doc` 文件必须先转换：`python scripts/office/soffice.py --headless --convert-to docx file.doc`。

```bash
unzip -q doc.docx -d unpacked/
find unpacked -type l -delete   # strip symlink entries — docx from external parties is untrusted
python scripts/merge_runs.py unpacked/   # coalesce fragmented runs so text is findable
# edit unpacked/word/document.xml in place — do NOT reformat or pretty-print
(cd unpacked && rm -f ../out.docx && zip -Xr ../out.docx .)
python scripts/office/validate.py out.docx --original doc.docx   # XSD checks; --auto-repair fixes common issues
# redlining? add --author "<the name you redlined under>" to check every edit is tracked
```

Word 会把文本拆到许多 `<w:r>` run 里（修订 id、拼写检查标记），因此你在文档里看到的一个短语。在 XML 里往往并不作为连续字符串存在。`merge_runs.py` 在不改变内容或渲染的前提下合并 `word/document.xml` 中相邻且格式相同的 run。它也直接接受 `.docx`（`python scripts/merge_runs.py doc.docx -o merged.docx`）。

**修订：** 做红线时用 `--author "<你署名做红线的名字>"` 校验（需要 `--original`）。它会报告任何你改了却没有 `<w:ins>`/`<w:del>` 包住的文本，这种失误很容易不小心犯下。且在「接受」视图中不可见。把 run 包进带 `w:id`、`w:author`、`w:date` 属性的 `<w:ins>`/`<w:del>`。在 `<w:del>` 内，文本元素是 `<w:delText>`，不是 `<w:t>`。被删除的段落标记（`<w:pPr><w:rPr><w:del w:id=".." w:author=".." w:date=".."/></w:rPr></w:pPr>`）意为「把这个段落并入下一段」。所以彻底删掉一个段落，就是它再加上把每个 run 都包进 `<w:del>`。`<w:del/>` 必须在 rPr 其他子元素之前。它们的顺序由 schema 强制。

要生成一份接受全部修订的干净副本：`python scripts/accept_changes.py in.docx out.docx`。

接受一个被删除的段落标记，本应把该段落与下一段合并，因此所有 run 都被删除的段落会消失。Word 会这么做。`accept_changes.py` 和 `pandoc --track-changes=accept` 并不总是。两者以同样方式失败——它们剥掉了被删文本，却留下被清空的段落，若该段原本是自动编号的。读起来就像一个游离的空项目符号。

- `pandoc --track-changes=accept` 从不合并段落。
- `accept_changes.py`（LibreOffice）能正确合并，除非被删段落后面跟着一个空的分隔段落。

任一视图中出现的空项目符号都是该视图的产物，而非文档缺陷。段落删除要到 XML 里检查。

## 批注

批注需要六个相互链接的文件。用辅助脚本——若你还要编辑 `document.xml` 就用目录模式（省去一次 unzip/rezip），否则用 `.docx` 直连模式：

```bash
# Against an already-unpacked directory (preferred when also placing markers)
python scripts/comment.py unpacked/ "Fees & expenses cap is too low"
python scripts/comment.py unpacked/ "Agreed" --parent 0

# Against a .docx directly
python scripts/comment.py contract.docx "This cap is too low" -o annotated.docx
```

脚本会写出 `comments.xml`、`commentsExtended.xml`、`commentsIds.xml`、`commentsExtensible.xml`、关系以及内容类型覆盖。批注 ID 自动分配。随后它会打印要加进 `word/document.xml` 的 `<w:commentRangeStart>`/`<w:commentRangeEnd>`/`<w:commentReference>` 片段，好让批注锚定到具体文本。在你放入这些标记之前，批注虽存在却不可见。

## 常见坑

- 不要让 OOXML 经 `xml.etree.ElementTree` 往返——它会改写命名空间前缀并损坏文件。脚本化变换请用 `defusedxml.minidom`。
- 要在解包目录*内部*打包（`cd unpacked && zip -Xr ../out.docx .`），并先 `rm` 目标文件，否则被删的部分会残留在归档里。

## 验证

1. `python scripts/office/validate.py out.docx --original in.docx`——schema、关系与内容类型检查。每个失败都指明其修法。
2. 渲染成 PDF → 图片（见「核验产出」），用 `vision_analyze` 逐页检查——找破损的表格、缺失的图片、间距瑕疵、残留占位文本。

## 相关 skill

`pdf`（PDF 工作）、`xlsx`（电子表格）、`powerpoint`（演示文稿）、`ocr-and-documents`（扫描输入抽取）。
