---
name: powerpoint
description: "创建、读取、编辑 .pptx/.potx 演示文稿时使用。只要涉及幻灯片、deck、模板、演讲备注、图表或设计 QA，就主动加载，即使用户只是提到某个 .pptx 文件名。不用于 docx/xlsx/pdf。"
version: 2.0.0
author: Anthropic (adapted by Nous Research)
license: Proprietary. LICENSE.txt has complete terms
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PowerPoint, PPTX, Presentations, Office, Productivity]
    category: productivity
    related_skills: [docx, xlsx, pdf]
---

# Powerpoint 技能

创建、读取、编辑 PowerPoint 演示文稿——用 pptxgenjs 从零生成、经直接 XML 操作做模板编辑、演讲备注、图表以及设计 QA。`.pptx` 是 XML 文件的 ZIP 归档。

## 何时使用

只要以任何方式涉及 .pptx 或 .potx 文件——作为输入、输出或两者——就用本 skill：创建幻灯片、pitch deck 或演示文稿。从任何 .pptx 读取或抽取文字。编辑已有演示文稿。合并或拆分幻灯片文件。处理模板（.potx）、版式、演讲备注或批注。只要用户提到「deck」「slides」「presentation」，或引用某个 .pptx/.potx 文件名，就触发。

## 前置条件

```bash
npm ls pptxgenjs --depth=0 2>/dev/null | grep -q pptxgenjs || npm install pptxgenjs
pip install "markitdown[pptx]" Pillow defusedxml lxml
which soffice || sudo apt install -y libreoffice     # rendering/QA
which pdftoppm || sudo apt install -y poppler-utils  # PDF → images
```

macOS：`brew install libreoffice poppler`。生成的演示文稿里的图标还会用到 `react-icons react react-dom sharp`（npm）。

## 快速参考

| 任务 | 方式 |
|---|---|
| **创建**新演示文稿 | 写一个 `pptxgenjs` 脚本——见下方坑 |
| **编辑**已有演示文稿，或基于模板构建 | unzip → 改 `ppt/slides/slideN.xml` → zip |
| **读取**内容 | `markitdown deck.pptx`（每张幻灯片一个块，位于 `<!-- Slide number: N -->` 标记下）。可视化网格：`python scripts/thumbnail.py deck.pptx` |

## 脚本

路径相对于本 skill 目录。其余都是普通 Python、`node` 或 shell。

| 脚本 | 作用 |
|---|---|
| `scripts/thumbnail.py deck.pptx [prefix]` | 每张幻灯片带标签的网格，用于挑选模板版式。仅 `.pptx`。务必传 `prefix`——它默认 `thumbnails`，会覆盖同目录下其他演示文稿做的网格 |
| `scripts/add_slide.py unpacked/ slide2.xml [--after slideN.xml]` | 复制一张幻灯片（或 `slideLayoutN.xml`）并处理全部包内簿记。也直接接受 `.pptx`，配 `-o out.pptx` |
| `scripts/clean.py unpacked/` | 删除不再被引用的幻灯片、媒体与关系。要在 `<p:sldIdLst>` 定稿**之后**运行 |
| `scripts/office/validate.py deck.pptx [--original src.pptx]` | Schema、关系、内容类型、图表与幻灯片检查。每个失败都指明其修法。任何基于模板的演示文稿都传 `--original`——它把 schema 检查对齐到模板基线，这样模板自身的 XSD 错误不会被当成你的 |
| `scripts/office/soffice.py --headless --convert-to pdf deck.pptx` | LibreOffice 包装器——裸 `soffice` 在沙箱环境里会卡住 |
| `scripts/geometry_check.py deck.pptx [--edge 0.5] [--gap 0.3]` | 渲染前 EMU 级布局 lint：越边、文本互撞、块间隙过小（见「几何 QA」） |

## 用 pptxgenjs 创建——坑

写脚本并 `require('pptxgenjs')`。API 模型已知。以下是易踩的雷：

- **在添加幻灯片前先设 `pres.layout`。** 默认画布是 `LAYOUT_16x9` = **10" × 5.625"**，不是 13.3" 宽。越过边缘的坐标会被写入而非裁剪——形状只是不在幻灯片上。（`LAYOUT_WIDE` 是 13.3" × 7.5"。）
- **十六进制颜色：绝不带 `#`，绝不用 8 位。** `color: "FF0000"`。`"#FF0000"` 和把 alpha 烤进十六进制（`"00000020"`）**都会损坏文件**。做半透明：填充与图片用 `transparency: 0-100`，阴影用 `opacity: 0.0-1.0`——两者在对方身上会被静默忽略。
- **pptxgenjs 会就地改动选项对象**（首次使用时把值转成 EMU）。绝不要在两次 `add*` 调用间共用一个 `shadow`/选项对象——每次都新建一个对象。
- **阴影 `offset` 必须 ≥ 0**——负偏移会损坏文件。要向上投阴影，用 `angle: 270` 配正偏移。
- **`letterSpacing` 会被静默忽略**——真正的选项是 `charSpacing`。
- **列表：** 每个条目上设 `bullet: true`，绝不用字面的 `•`（会渲染成双项目符号）。除最后一项外，数组每项都设 `breakLine: true`。项目符号段落之间用 `paraSpaceAfter` 隔开，不要用 `lineSpacing`（会产生巨大空隙）。
- **每个输出文件一个 `new pptxgen()`**——绝不要复用一个实例。
- **`rectRadius` 只对 `ROUNDED_RECTANGLE` 有效**，对 `RECTANGLE` 无效。
- **不支持渐变填充**——改用一张渐变图当背景。
- **文本框有内置内边距**——凡是要让文字与同一 x 上的形状、线条或图标对齐，就设 `margin: 0`。
- **演讲备注写进 `slide.addNotes("...")`**（纯文本，每张幻灯片一次），绝不要写在幻灯片上的文本框里。
- **图表保持原生。** PowerPoint 能做的图都用 `addChart()`（组合图传 `{type, data, options}` 数组）。库没有暴露的 PowerPoint 原生特性（趋势线、误差棒），自己算出额外系列或对生成的 OOXML 做后处理。不要退而用一张渲染图。只有 PowerPoint 没有原生形式的图类型（桑基图、关系网络图、弦图）才作为图片放进去。
- **默认图表渲染得很朴素**——没有标题、没有数据标签、配色过时。设 `showTitle` + `title`、`showValue: true` + `dataLabelPosition`、取自你配色的 `chartColors: [...]`，并让边框安静下来（`catAxisLabelColor`/`valAxisLabelColor`、`valGridLine: { color, size }`、`catGridLine: { style: "none" }`，单系列时 `showLegend: false`）。
- **在堆积条形图或柱状图上，`dataLabelPosition` 必须是 `ctr`、`inEnd` 或 `inBase`。** `outEnd` **会损坏文件**。
- **使用 `secondaryValAxis`/`secondaryCatAxis` 的组合系列，需要在图表选项上同时有 `valAxes` 与 `catAxes`，各两项。** 缺了它们，pptxgenjs 会写出它从未声明的轴 *id*，PowerPoint 会**丢弃该图表**并报告文件损坏。只提供 `valAxes` 不够。
- **`writeFile()` 之后，运行 `python scripts/office/validate.py deck.pptx`。** 它会报告上述两类图表故障以及 PowerPoint 拒绝的幻灯片 XML 缺陷，并逐条指明修法。要在生成器里修复，而不是手工改打包好的 XML。
- **绝不要重排 `<p:presentation>` 的子元素。** pptxgenjs 把 `<p:notesMasterIdLst>` 紧接 `<p:sldIdLst>` 写出，并让两个母版指向同一个主题部件。PowerPoint 读它没问题——一旦移动该元素，同一份演示文稿就变得打不开。
- **图标：** 把 `react-icons` 渲染成 SVG（`ReactDOMServer.renderToStaticMarkup`），用 `sharp` 以 ≥256px 光栅化，再经 `addImage({ data: "image/png;base64," + buf.toString("base64") })` 插入——`image/png;base64,` 前缀是必需的。

## 编辑已有演示文稿与模板

先选版式：`python scripts/thumbnail.py template.pptx template-thumbs` 会写出每张幻灯片带标签的网格，并打印它创建的文件——`template-thumbs.jpg`。超过 12 张幻灯片会拆成 `template-thumbs-N.jpg`。**务必传第二个参数，以该演示文稿命名。** 它默认 `thumbnails`，因此在同一目录里做两份演示文稿的缩略图会静默互相覆盖网格（仅用于模板分析——视觉 QA 需要 [转换为图片](#converting-to-images) 的全分辨率渲染。它只接受 `.pptx`，所以先把 `.potx` 复制成一个 `.pptx` 文件名）。配合 `markitdown` 把每个内容章节映射到某张模板幻灯片上，并变换版式。不要把每个章节都放在同一张标题加项目符号的幻灯片上。

```bash
python3 -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall('unpacked')" deck.pptx
python scripts/add_slide.py unpacked/ slide2.xml --after slide2.xml   # duplicate a slide (or slideLayoutN.xml); prints the new slide's path
# reorder / delete slides = edit <p:sldIdLst> in ppt/presentation.xml
python scripts/clean.py unpacked/                                     # after deletions: removes orphaned slides, media, rels
# edit slide content in ppt/slides/slideN.xml
(cd unpacked && rm -f ../out.pptx && zip -Xr ../out.pptx .)           # zip from INSIDE the dir; rm first or deleted parts survive
python scripts/office/validate.py out.pptx --original deck.pptx
```

- **所有结构工作——增、删、重排——都在编辑任何幻灯片内容之前做完。** `add_slide.py` 逐字节复制幻灯片文件，所以在你编辑之后再复制，克隆的是编辑过的内容。而 `clean.py` 会删除任何不在 `<p:sldIdLst>` 里的幻灯片，包括你刚写的那张。
- **绝不要手工复制幻灯片文件**——`add_slide.py` 会做完新幻灯片所需的全部登记并报告它造了什么。它也直接对文件操作：`add_slide.py deck.pptx slide2.xml -o out.pptx`——**务必传 `-o`，否则它会就地重写输入演示文稿。** 复制出的幻灯片仍然*引用*其来源的图表/SmartArt/嵌入对象部件，而非克隆它们。所以编辑其中一张的图表会改变另一张。
- **如果你用 `python-pptx`**，有三件事它做不到：复制幻灯片（它唯一的入口是 `add_slide(layout)`）。通过 `text_frame.text = "..."` 保留格式（那会把段落坍缩成单个无样式 run——改为赋值 `run.text`）。读取多数模板美术用的 SVG/EMF（`add_picture` 会抛 `UnidentifiedImageError`）。
- 旧版 `.ppt` 必须先转换：`python scripts/office/soffice.py --headless --convert-to pptx file.ppt`。`.potx` 模板的解包与打包方式相同——输出保留 `.potx` 扩展名。
- 要复用模板里的某个图标或图片，复制一张已包含它的幻灯片或版式。

填写模板时：

- 若你脚本化 XML 变换，用 `defusedxml.minidom` 解析——让 OOXML 经 `xml.etree.ElementTree` 往返会改写命名空间前缀并损坏演示文稿。
- **模板槽位 ≠ 源条目。** 若模板展示 4 位团队成员而你只有 3 位，就删掉第 4 位的整个组（图片 + 文本框），而不只是其文字。然后在 QA 里检查有无孤立视觉元素。
- 每个列表项一个 `<a:p>`——绝不把多项拼进一个段落。复制相邻的 `<a:pPr>` 以保留间距，并在标题、章节标题与行内标签（`Status:`、`Owner:`）的 `<a:rPr>` 上设 `b="1"`。
- 让项目符号继承自版式。只在需要覆盖时添加 `<a:buChar>`、`<a:buAutoNum>`（编号）或 `<a:buNone>`——绝不在文字里写字面的 `•`。
- 带前后空格的文字，其 `<a:t>` 需要 `xml:space="preserve"`。

## 设计思路

**不要做无聊的幻灯片。** 白底加朴素项目符号不会打动任何人。每张幻灯片都从这份清单里挑些思路。

### 开工之前

- **挑一套大胆、由内容决定的配色**：这套配色应当像是专为*这个*主题设计的。若把你的颜色换到一份完全不同的演示文稿里仍然「能用」，说明你的选择还不够具体。
- **主导胜过均等**：应有一种颜色主导（60-70% 视觉权重），配 1-2 种辅助色调和一种锐利的强调色。绝不要让所有颜色权重相等。
- **明暗对比**：标题页与结论页用深色背景，内容页用浅色（「三明治」结构）。或者通篇坚持深色以营造高级感。
- **坚持一个视觉母题**：挑*一个*独特元素并重复它——圆角图片框、彩色圆圈里的图标。把它贯穿每张幻灯片。**不要把色条或强调条纹当母题**（见「避免」清单）。
- **调性看场合，系统必须统一**：先判断这个 deck 投给什么场合——课程作业 pitch 不是董事会汇报，研究生作业的活气来自口语化正文、第一人称吐槽、道具感卡片，硬套商务汇报腔会被顶回「太正式」。用户点名的调性优先于「避免」清单里的反 AI 默认（调性被认可时，暖底、标题短线都可用）。但调性一换就整套换：**首尾每张幻灯片共用同一套标题栏/标题/落地栏/卡片规则**，版式在系统内变化，只允许封面与收尾页在颜色上略变——每张幻灯片各长一个样子就是「风格不统一」被退回的标准成因。

### 配色方案

选择契合主题的颜色——不要默认用泛泛的蓝色。以下配色供参考：

| 主题 | 主色 | 次色 | 强调色 |
|-------|---------|-----------|--------|
| **午夜主管** | `1E2761`（藏青） | `CADCFC`（冰蓝） | `FFFFFF`（白） |
| **森林与苔藓** | `2C5F2D`（森林绿） | `97BC62`（苔藓绿） | `F5F5F5`（米白） |
| **珊瑚活力** | `F96167`（珊瑚） | `F9E795`（金） | `2F3C7E`（藏青） |
| **暖陶土** | `B85042`（陶土） | `E7E8D1`（沙） | `A7BEAE`（鼠尾草） |
| **海洋渐变** | `065A82`（深蓝） | `1C7293`（青） | `21295C`（午夜蓝） |
| **炭灰极简** | `36454F`（炭灰） | `F2F2F2`（灰白） | `212121`（黑） |
| **青绿信赖** | `028090`（青） | `00A896`（海沫绿） | `02C39A`（薄荷） |
| **莓果与奶油** | `6D2E46`（莓果） | `A26769`（灰玫瑰） | `ECE2D0`（奶油） |
| **鼠尾草静谧** | `84B59F`（鼠尾草） | `69A297`（桉绿） | `50808E`（石板） |
| **樱桃大胆** | `990011`（樱桃） | `FCF6F5`（灰白） | `2F3C7E`（藏青） |

### 每张幻灯片

**每张幻灯片都需要视觉元素**——图片、图表、图标或形状。纯文字幻灯片转瞬即忘。

**真照片自己找，别留空位**：只要图不是只存在于用户手里（自家往事、自家道具实拍），就自己找一张真 CC 授权照片（Wikimedia Commons，可商用）放进页面，作者＋作品名＋许可证放署名页或页脚。检索参数、许可证核验与限速坑见 `references/image-sourcing.md`。只有该组才有的实物（道具照、报名表码）才许留 dashed NOTE 占位并注明「不许编造」；网图当配图时，正文与脚注要写明它是示意、不对应讲者要讲的故事。

**版式选项：**
- 两栏（左文右插图）
- 图标 + 文字行（彩色圆圈里的图标、粗体标题、下方描述）
- 2x2 或 2x3 网格（一侧放图，另一侧放内容块网格）
- 半出血图片（占满左半或右半）叠加内容

**数据展示：**
- 大号数据标注（60-72pt 的大数字，下方小标签）
- 对比栏（前/后、优/劣、并排选项）
- 时间线或流程（带编号的步骤、箭头）

**视觉打磨：**
- 章节标题旁彩色小圆圈里的图标
- 关键数据或标语用斜体强调文字

### 字体排印

**你写进 .pptx 的字体名由用户的 PowerPoint 渲染，而非本环境。** 你的视觉 QA 经 LibreOffice 渲染，它会替换掉自己没有的字体——而对某些字体，替代字宽度不同。所以你的 QA 预览可能显示真实演示文稿并不会有的文字溢出（或恰好放得下）。为让你的 QA 可信：

- **安全字体**（在 QA 中按真实宽度渲染*且*随 Office 附带）：**Arial、Calibri、Cambria、Times New Roman、Courier New、Bookman Old Style、Century Schoolbook**。正文以及任何讲究放得下与否的地方都用这些。
- **零 QA 风险又有个性的标题**。把安全清单里的衬线标题（Cambria、Bookman Old Style、Century Schoolbook）配上安全清单里的无衬线正文（Calibri 或 Arial）。
- **若用户要求安全清单之外的字体**（如 Georgia 或 Trebuchet MS）：在用户要求处照用，但给那些容器留额外余量（约 10%）。且不要相信那些元素的 QA 文字适配。
- **QA 不可靠的字体**（替代字宽度不同——溢出检查可能出错）：Georgia、Trebuchet MS、Impact、Arial Black、Garamond、Consolas、Palatino Linotype。Calibri Light 的替换随环境而异。视为 QA 不可靠。
- **绝不要默认用 Aptos**——Office 2023 年后的默认字体在这里没有度量兼容的替代字*且*在较旧的 Office 安装中缺失。所以两头都不可靠。

| 元素 | 字号 |
|---------|------|
| 幻灯片标题 | 36-44pt 粗体 |
| 章节标题 | 20-24pt 粗体 |
| 正文 | 14-16pt |
| 图注 | 10-12pt 弱化 |

### 间距

- 最小边距 0.5"
- 内容块之间 0.3-0.5"
- 留出呼吸感——不要填满每一寸

### 避免（常见错误）

- **不要重复同一版式**——在各幻灯片间变换栏目、卡片与标注
- **不要居中正文**——段落与列表左对齐。只居中标题
- **不要吝惜字号对比**——标题需要 36pt+ 才能从 14-16pt 正文中跳出来
- **不要默认用蓝**——挑反映具体主题的颜色
- **不要随意混用间距**——选定 0.3" 或 0.5" 的间隙并一致使用
- **不要只精心打扮一张幻灯片而其余留白**——要么全力投入，要么通篇简洁
- **不要做纯文字幻灯片**——加图片、图标、图表或视觉元素。避免朴素的标题加项目符号
- **不要忘了文本框内边距**——把线条或形状与文字边缘对齐时，在文本框上设 `margin: 0`。或把形状偏移以抵掉内边距。
- **不要用低对比元素**——图标*和*文字都需要对背景有强对比
- **绝不要在标题下加强调线**——这是 AI 生成幻灯片的标志。改用空白或背景色
- **绝不要加装饰性色条或强调条纹**——这包括：横跨幻灯片宽度的页眉/页脚条。沿幻灯片某条边向下的竖直侧边条纹、沿卡片或内容块某条边的细强调条纹。以及矩形上的「单边框」。它们读起来像 AI 生成的填充物。若想区分某张卡片，用微妙的背景淡色、投影或图标——而不是边缘条纹。
- **不要默认用米色/奶油色背景**——未指定背景时，用白色（`FFFFFF`）或用户的品牌配色。避免 `F5F5DC`、`FAF0E6`、`FAEBD7`、`FFF8E1` 之类暖中性默认色。
- **不要交付超出形状的文字**——若文字放不下，就缩小字号、拆到多张幻灯片，或放大容器。绝不要让内容被截断或溢出边界。

## QA（必需）

你的第一次渲染通常有几个真实问题——重叠、溢出、错位。找出并修好它们，只重渲染你改动过的幻灯片，然后收工。

### 内容 QA

```bash
markitdown output.pptx
```

检查缺失内容、错别字、顺序错误。

**用模板时，检查残留的占位文本：**

```bash
markitdown output.pptx | grep -iE "\bx{3,}\b|lorem|ipsum|\bTODO|\[insert|this.*(page|slide).*layout"
```

若 grep 有结果，先修好再宣告成功。

**带引用/数据的 deck 再跑「必命中」核对**：把全部必须出现的数字、单位、来源代号、限定语列成清单，对 markitdown 输出逐个 grep 确认存在且没串位（各组统计各归各页、`percentage points` 与 `percent` 不互串、believed 类限定语不丢）。整篇看着没问题不算数。

### 文件 QA（必需）

```bash
python scripts/office/validate.py output.pptx                      # built from scratch
python scripts/office/validate.py output.pptx --original src.pptx  # built from a template
```

**若演示文稿来自模板，务必传 `--original`。** 模板本身可能含有 XSD 拒绝的部件，所以裸跑可能报告你从未造成的失败。而真正的回归可能藏在其间。`--original` 会把 schema 与幻灯片检查对齐到模板基线。结构检查——关系、内容类型、图表——忽略 `--original`，无论如何都会报告模板继承来的问题。所以要就事论事地看它们。

pptxgenjs 会产出 PowerPoint 拒绝打开、而其他所有工具都接受的图表 XML：python-pptx 能打开那些演示文稿，LibreOffice 能渲染。XSD 也能通过。每个失败都指明其修法。要在生成器里修复并重建。

### 几何 QA（渲染前，先跑）

```bash
python scripts/geometry_check.py output.pptx            # --edge/--gap 改尺子
```

直接从 pptx XML 解析每个形状的 EMU 坐标、算旋转后的包围盒，在渲染之前报出坐标级可证的硬伤：越出页边、两个文本框互撞、纵向成块间隙过小。文字坐在带填充的卡片上被当作同一视觉单元，骑跨卡片边缘的数字徽章这类设计不会误报。本步的 flag 是**候选项**：设计成对的小间隙（标题栏↔标题、大数字↔注释）要结合渲染图复核，只有渲染图上看着挤的才改。

### 视觉 QA

把幻灯片转成图片（见 [转换为图片](#converting-to-images)），用 `vision_analyze` 逐张检查。盯着生成代码久了，你往往看到的是预期的而非实际渲染的。所以要用新鲜的眼光看图（`delegate_task` 子代理很适合干这个）。要查找的用户可见缺陷：

- **文字溢出或在框/幻灯片边界被截断——先查这个。** 它是最常见的缺陷，且总是用户可见。（对预览器按「字体排印」一节渲染不可靠的字体，预览是近似的：相信你留出的约 10% 余量，而不是它表面的适配。）
- 元素重叠（文字穿过形状、线条穿过文字、元素堆叠）
- 来源引用或页脚与上方内容相撞
- 元素过近（间隙 < 0.3"）或卡片/区块几乎相触
- 间隙不均（一处大片空白，另一处拥挤）
- 距幻灯片边缘的边距不足（< 0.5"）
- 栏目或类似元素未一致对齐
- 低对比文字（如奶油色背景上的浅灰文字）
- 文字替换后模板装饰错位——如标题下划线按一行定位，但替换后的标题折成了两行
- 低对比图标（如深色背景上的深色图标，没有对比圆圈）
- 文本框过窄导致过度折行
- 残留的占位内容

## 转换为图片

把演示文稿转成单张幻灯片图片以便目视检查：

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
rm -f slide-*.jpg
pdftoppm -jpeg -r 150 output.pdf slide
ls -1 "$PWD"/slide-*.jpg
```

**把上面打印的绝对路径直接传给 `vision_analyze`。** `rm` 清掉上次运行留下的旧图。`pdftoppm` 按页数补零：少于 10 页的演示文稿是 `slide-1.jpg`，10-99 页是 `slide-01.jpg`，100+ 页是 `slide-001.jpg`。

**修复后，重跑上面四条命令**——PDF 必须从编辑过的 `.pptx` 重新生成，`pdftoppm` 才能反映你的改动。

## 相关 skill

`docx`（Word 文档）、`xlsx`（电子表格）、`pdf`（PDF 工作）、可选 `pptx-author`（财务级、由模型驱动的演示文稿）。
