---
name: xlsx
description: "创建、读取、编辑 Excel .xlsx/.xlsm/.csv 表格时使用。只要涉及电子表格的读写、改公式、格式转换或清理脏表数据，就主动加载，即使用户只是随口提到某个表格文件名。不用于 Word（用 docx）、PDF 或纯文本交付。"
version: 1.0.0
author: Anthropic (adapted by Nous Research)
license: Proprietary. LICENSE.txt has complete terms
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Excel, XLSX, Spreadsheets, Office, Productivity]
    category: productivity
    related_skills: [docx, pdf, powerpoint]
---

# XLSX 技能

创建、读取、编辑 Excel 工作簿——公式、格式、图表、数据清洗与格式转换。每个含公式的产出在交付前都必须重算且无错误。

## 何时使用

只要电子表格文件是主要输入或产出，就用本 skill：打开、读取、编辑或修复已有的 .xlsx、.xlsm、.xltx、.csv 或 .tsv 文件；从零或从其他数据新建表格；在表格格式间转换；把杂乱的表格数据清理成规范表格。只要用户按名称或路径提到某个表格文件——哪怕随口一提——就触发。当交付物是 Word 文档（`docx` skill）、HTML 报告、独立脚本或 Google Sheets API 集成时不要触发。对财务级建模惯例（DCF、LBO、三表模型），可选的 `excel-author` skill 在本 skill 之上加了更严的标准。

## 前置条件

```bash
pip install openpyxl pandas "markitdown[xlsx]"
which soffice || sudo apt install -y libreoffice   # formula recalculation (scripts/recalc.py)
```

macOS: `brew install libreoffice`.

## 快速参考

| 任务 | 方式 |
|---|---|
| **创建**或**编辑**（含公式/格式） | `openpyxl`——见下方坑 |
| **批量数据**进出 | `pandas`（`read_excel`、`to_excel`） |
| **快速查看**某个表 | `markitdown file.xlsx`——每个表一个 `## SheetName`；也能读 `.xlsm`。没有单元格坐标，因此别据此规划编辑。（`read_file` 也会自动抽取 .xlsx） |
| **读取**模型（公式*与*值） | 两次 `load_workbook` 遍历——见坑 |

> 下方脚本路径相对于本 skill 目录。

## 每个产出的要求

- **专业字体**（Arial、Times New Roman）贯穿全文，除非用户另有要求。
- **零公式错误。** 只要 `recalc.py` 报告 `errors_found` 就绝不交付。若你认为某个错误在你之前就有，拿出证据：用 `data_only=True` 载入*原始*文件，查看该单元格。你引入的错误和你继承的错误看起来一模一样。
- **用公式，绝不硬编码结果。** 写 `sheet['B10'] = '=SUM(B2:B9)'`，而不是 Python 算出的总数。输入变化时表必须能重算。
- **字面遵循用户的规格。** 精确的标签页名、精确的列标题，以及他们写明的公式。任何算出别的东西的重新设计都算失败，再优雅也一样。
- **记录每个假设与硬编码数字**，写在读者能看到的地方——单元格批注，或表末的相邻单元格。有真实来源就引用；数字来自用户就明说。
- **为他人填写而*你创建*的工作簿**需要一段简短图例，说明要编辑哪些单元格，并加一行真实感示例值展示期望格式。绝不要给你被要求编辑的文件加这样的行。
- **编辑已有文件：精确匹配它的惯例。** 它们覆盖这里的所有准则。先找出它的指定输入单元格——以独特的字体颜色、填充或底纹标记——只在那里写，且不碰任何已有公式。

## 重算（文件含公式时强制）

openpyxl 把公式写成字符串，**没有缓存值**。在你重算之前，任何读缓存值的东西——`pandas`、`load_workbook(data_only=True)` 以及大多数预览器——都会把每个公式单元格读成 `None`。

```bash
python scripts/recalc.py output.xlsx [timeout_seconds]   # default 30
```

LibreOffice 会计算每个公式，文件被**原地重写**，你会得到 JSON：`status`（`success` | `errors_found`）、`total_formulas`、`total_errors`，以及一个 `error_summary`，每种错误类型最多列出 100 个单元格（`locations_truncated` 说明它扣下了多少——以 `total_errors` 为准，不要信列表长度）。按它指出的位置修正后重跑。**JSON 里是 `error` 键而非 `status` 意味着什么都没重算**，且只有这一种情况退出码非零——`errors_found` 退出码是 0，所以绝不要把干净退出当成干净工作簿。

**重算通过只证明你的公式能*求值*，不证明它们*正确*。** 范围差一或引用错行会产出干净、无错误但数字错误的结果。先写 2–3 个公式并确认它们取到预期的值，再铺开整张网格。

**链接到其他文件的工作簿**若你再用 openpyxl 保存并重算，会**丢失这些链接**。这类公式形如 `='[1]Returns Analysis'!$B$2`——`[1]` 是工作簿外部引用列表的索引，指向*磁盘上另一个文件*，而非某个表。那个文件很少在场，因此单元格的缓存值是其数据的唯一依托。openpyxl 保存时会剥掉该值；LibreOffice 随后必须真正解析该引用，失败，写入 `#NAME?`，并删除所有链接。此时 `recalc.py` 拒绝运行——在覆盖保存前先把这些单元格的值拷出来（`--force` 可强制覆盖，并接受这一丢失）。

## 选择能通过核验的公式

LibreOffice 实现的函数比 Excel 少，某个它无法求值的函数会变成字面 `#NAME?` 烤进你交付的文件里。

- **优先用 Excel 2007 时代的函数**——`SUMIFS`、`INDEX`、`MATCH`、`IFERROR`、`SUMPRODUCT`——它们无需前缀。
- **有六个 2007 之后的函数可用，但必须带 `_xlfn.` 前缀**，因为 openpyxl 把你的公式原样写进 XML，而 Excel 存储 2007 之后的函数名时带前缀（其界面会隐藏前缀）：`_xlfn.TEXTJOIN`、`_xlfn.CONCAT`、`_xlfn.IFS`、`_xlfn.SWITCH`、`_xlfn.MAXIFS`、`_xlfn.MINIFS`。写成裸名都会得到 `#NAME?`。
- **绝不要用 `XLOOKUP`、`XMATCH`、`SORT`、`FILTER`、`UNIQUE` 或 `SEQUENCE`。** LibreOffice 无法可靠地求值它们；能做到的较新版本会溢出（spill）数组函数，而 openpyxl 写的文件没有 spill 元数据，因此只有范围左上角单元格得到值——而 `recalc.py` 会对这个被截断的结果报告 `total_errors: 0`。查找用 `INDEX`/`MATCH`，排序、过滤、去重都在 Python 里做，再写单元格。
- LibreOffice 无法解析的公式会被写回成**小写**——它旁边的 `#NAME?` 是个快速线索。

## openpyxl 坑

- **读取模型需要两次载入。** `data_only=True` 给出缓存值但公式没了；默认给出公式字符串但没有值。一次遍历无法两者兼得。
- **若保存，`data_only=True` 具破坏性。** 那个工作簿已没有公式，保存会把每一个都永久替换成字面值。
- **对 openpyxl 刚写的文件用 `data_only=True` 到处都返回 `None`**——先跑 `recalc.py`。（结果为 `""` 的公式也会读回 `None`。）
- **合并单元格：只写左上角锚点。** 范围内其他单元格都是 `MergedCell`，其 `.value` 只读。
- **`.xlsm` 会丢失宏，除非给 `load_workbook` 传 `keep_vba=True`**。
- **含空格的表名在跨表引用中必须加引号**：`='Assumptions Inputs'!$B$5`。不加引号会求值成 `#VALUE!`。

## 财务模型

除非用户另有要求，或已有文件本就另有一套做法。

**颜色：** 硬编码输入与情景杠杆用蓝色文字（`0,0,255`）· 公式用黑色 · 指向其他表的链接用绿色（`0,128,0`）· 指向其他文件的链接用红色（`255,0,0`）· 关键假设与用户应填的单元格用黄色填充（`255,255,0`）。

**数字：** 货币 `$#,##0`，单位在表头标明（`Revenue ($mm)`）· 零渲染为 `-`，百分比中亦然（`$#,##0;($#,##0);-`）· 负数用括号 · 百分比 `0.0%`，**以分数存储**（`0.15` 渲染为 `15.0%`；存 `15` 会渲染成 `1500.0%`）· 估值倍数 `0.0x` · 年份用文本（`"2024"`，绝不用 `2,024`）。

**结构：** 每个假设单独放一个带标签的单元格，由使用它的公式引用（`=B5*(1+$B$6)`，绝不用 `=B5*1.05`）· 每个预测期的公式保持一致，因为行中间被单独改动的某个单元格是最常见的静默错误 · 对可能为零的分母加保护。

要获取完整的投行惯例（勾稽检查、敏感性表、命名区域），安装可选 skill：`hermes skills install official/finance/excel-author`。

## 验证

1. `python scripts/recalc.py output.xlsx` → `status: success`、`total_errors: 0`。
2. 抽查 2–3 个计算单元格与期望值（在重算*之后*用 `load_workbook(data_only=True)`）。
3. `markitdown output.xlsx`——扫查缺失的表、错位的表头、残留占位符。

## 相关 skill

`docx`（Word 文档）、`pdf`（PDF 工作）、`powerpoint`（演示文稿）、可选 `excel-author`（财务级建模标准）。
