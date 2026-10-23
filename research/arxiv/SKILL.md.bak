---
name: arxiv
description: "按关键词、作者、分类或 ID 搜 arXiv 论文时使用。只要要查论文、读摘要或做文献发现，就主动加载，即使用户只说「帮我找几篇讲 X 的论文」。"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Arxiv, Papers, Academic, Science, API]
    related_skills: [ocr-and-documents]
---

# arXiv Research

通过 arXiv 的免费 REST API 搜索与获取学术论文。无需 API key、无依赖 — 只用 curl。

## 速查

| 操作 | 命令 |
|--------|---------|
| 搜索论文 | `curl "https://export.arxiv.org/api/query?search_query=all:QUERY&max_results=5"` |
| 获取指定论文 | `curl "https://export.arxiv.org/api/query?id_list=2402.03300"` |
| 读摘要（web） | `web_extract(urls=["https://arxiv.org/abs/2402.03300"])` |
| 读全文（PDF） | `web_extract(urls=["https://arxiv.org/pdf/2402.03300"])` |

## 搜索论文

API 返回 Atom XML。用 `grep`/`sed` 解析，或经 `python3` 处理得到干净输出。

### 基础搜索

```bash
curl -s "https://export.arxiv.org/api/query?search_query=all:GRPO+reinforcement+learning&max_results=5"
```

### 干净输出（把 XML 解析成可读格式）

```bash
curl -s "https://export.arxiv.org/api/query?search_query=all:GRPO+reinforcement+learning&max_results=5&sortBy=submittedDate&sortOrder=descending" | python3 -c "
import sys, xml.etree.ElementTree as ET
ns = {'a': 'http://www.w3.org/2005/Atom'}
root = ET.parse(sys.stdin).getroot()
for i, entry in enumerate(root.findall('a:entry', ns)):
    title = entry.find('a:title', ns).text.strip().replace('\n', ' ')
    arxiv_id = entry.find('a:id', ns).text.strip().split('/abs/')[-1]
    published = entry.find('a:published', ns).text[:10]
    authors = ', '.join(a.find('a:name', ns).text for a in entry.findall('a:author', ns))
    summary = entry.find('a:summary', ns).text.strip()[:200]
    cats = ', '.join(c.get('term') for c in entry.findall('a:category', ns))
    print(f'{i+1}. [{arxiv_id}] {title}')
    print(f'   Authors: {authors}')
    print(f'   Published: {published} | Categories: {cats}')
    print(f'   Abstract: {summary}...')
    print(f'   PDF: https://arxiv.org/pdf/{arxiv_id}')
    print()
"
```

## 搜索查询语法

| 前缀 | 搜索范围 | 示例 |
|--------|----------|---------|
| `all:` | 所有字段 | `all:transformer+attention` |
| `ti:` | 标题 | `ti:large+language+models` |
| `au:` | 作者 | `au:vaswani` |
| `abs:` | 摘要 | `abs:reinforcement+learning` |
| `cat:` | 分类 | `cat:cs.AI` |
| `co:` | 评论 | `co:accepted+NeurIPS` |

### 布尔运算符

```
# AND (default when using +)
search_query=all:transformer+attention

# OR
search_query=all:GPT+OR+all:BERT

# AND NOT
search_query=all:language+model+ANDNOT+all:vision

# Exact phrase
search_query=ti:"chain+of+thought"

# Combined
search_query=au:hinton+AND+cat:cs.LG
```

## 排序与分页

| 参数 | 选项 |
|-----------|---------|
| `sortBy` | `relevance`、`lastUpdatedDate`、`submittedDate` |
| `sortOrder` | `ascending`、`descending` |
| `start` | 结果偏移（从 0 起） |
| `max_results` | 结果数量（默认 10，最大 30000） |

```bash
# Latest 10 papers in cs.AI
curl -s "https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=10"
```

## 获取指定论文

```bash
# By arXiv ID
curl -s "https://export.arxiv.org/api/query?id_list=2402.03300"

# Multiple papers
curl -s "https://export.arxiv.org/api/query?id_list=2402.03300,2401.12345,2403.00001"
```

## 生成 BibTeX

拿到论文元数据后，生成一条 BibTeX 条目：

{% raw %}
```bash
curl -s "https://export.arxiv.org/api/query?id_list=1706.03762" | python3 -c "
import sys, xml.etree.ElementTree as ET
ns = {'a': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
root = ET.parse(sys.stdin).getroot()
entry = root.find('a:entry', ns)
if entry is None: sys.exit('Paper not found')
title = entry.find('a:title', ns).text.strip().replace('\n', ' ')
authors = ' and '.join(a.find('a:name', ns).text for a in entry.findall('a:author', ns))
year = entry.find('a:published', ns).text[:4]
raw_id = entry.find('a:id', ns).text.strip().split('/abs/')[-1]
cat = entry.find('arxiv:primary_category', ns)
primary = cat.get('term') if cat is not None else 'cs.LG'
last_name = entry.find('a:author', ns).find('a:name', ns).text.split()[-1]
print(f'@article{{{last_name}{year}_{raw_id.replace(\".\", \"\")},')
print(f'  title     = {{{title}}},')
print(f'  author    = {{{authors}}},')
print(f'  year      = {{{year}}},')
print(f'  eprint    = {{{raw_id}}},')
print(f'  archivePrefix = {{arXiv}},')
print(f'  primaryClass  = {{{primary}}},')
print(f'  url       = {{https://arxiv.org/abs/{raw_id}}}')
print('}')
"
```
{% endraw %}

## 阅读论文内容

找到论文后，读它：

```
# Abstract page (fast, metadata + abstract)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper (PDF → markdown via Firecrawl)
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
```

本地 PDF 处理见 `ocr-and-documents` skill。

## 常用分类

| 分类 | 领域 |
|----------|-------|
| `cs.AI` | 人工智能 |
| `cs.CL` | 计算与语言（NLP） |
| `cs.CV` | 计算机视觉 |
| `cs.LG` | 机器学习 |
| `cs.CR` | 密码学与安全 |
| `stat.ML` | 机器学习（统计） |
| `math.OC` | 优化与控制 |
| `physics.comp-ph` | 计算物理 |

完整列表：https://arxiv.org/category_taxonomy

## 辅助脚本

`scripts/search_arxiv.py` 脚本负责 XML 解析并提供干净输出：

```bash
python scripts/search_arxiv.py "GRPO reinforcement learning"
python scripts/search_arxiv.py "transformer attention" --max 10 --sort date
python scripts/search_arxiv.py --author "Yann LeCun" --max 5
python scripts/search_arxiv.py --category cs.AI --sort date
python scripts/search_arxiv.py --id 2402.03300
python scripts/search_arxiv.py --id 2402.03300,2401.12345
```

无依赖 — 仅用 Python 标准库。

---

## Semantic Scholar（引用、相关论文、作者主页）

arXiv 不提供引用数据或推荐。改用 **Semantic Scholar API** — 免费，基础使用无需 key（1 req/sec），返回 JSON。

### 获取论文详情 + 引用

```bash
# By arXiv ID
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.03300?fields=title,authors,citationCount,referenceCount,influentialCitationCount,year,abstract" | python3 -m json.tool

# By Semantic Scholar paper ID or DOI
curl -s "https://api.semanticscholar.org/graph/v1/paper/DOI:10.1234/example?fields=title,citationCount"
```

### 获取某论文的引用（谁引了它）

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.03300/citations?fields=title,authors,year,citationCount&limit=10" | python3 -m json.tool
```

### 获取某论文的参考文献（它引了谁）

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.03300/references?fields=title,authors,year,citationCount&limit=10" | python3 -m json.tool
```

### 搜索论文（arXiv 搜索的替代，返回 JSON）

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=GRPO+reinforcement+learning&limit=5&fields=title,authors,year,citationCount,externalIds" | python3 -m json.tool
```

### 获取论文推荐

```bash
curl -s -X POST "https://api.semanticscholar.org/recommendations/v1/papers/" \
  -H "Content-Type: application/json" \
  -d '{"positivePaperIds": ["arXiv:2402.03300"], "negativePaperIds": []}' | python3 -m json.tool
```

### 作者主页

```bash
curl -s "https://api.semanticscholar.org/graph/v1/author/search?query=Yann+LeCun&fields=name,hIndex,citationCount,paperCount" | python3 -m json.tool
```

### 有用的 Semantic Scholar 字段

`title`、`authors`、`year`、`abstract`、`citationCount`、`referenceCount`、`influentialCitationCount`、`isOpenAccess`、`openAccessPdf`、`fieldsOfStudy`、`publicationVenue`、`externalIds`（含 arXiv ID、DOI 等）

---

## 完整研究工作流

1. **发现**：`python scripts/search_arxiv.py "your topic" --sort date --max 10`
2. **评估影响力**：`curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:ID?fields=citationCount,influentialCitationCount"`
3. **读摘要**：`web_extract(urls=["https://arxiv.org/abs/ID"])`
4. **读全文**：`web_extract(urls=["https://arxiv.org/pdf/ID"])`
5. **找相关工作**：`curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:ID/references?fields=title,citationCount&limit=20"`
6. **获取推荐**：POST 到 Semantic Scholar 的 recommendations endpoint
7. **跟踪作者**：`curl -s "https://api.semanticscholar.org/graph/v1/author/search?query=NAME"`

## 速率限制

| API | 速率 | 认证 |
|-----|------|------|
| arXiv | ~1 req / 3 秒 | 无需 |
| Semantic Scholar | 1 req / 秒 | 无（带 API key 时 100/秒） |

### 406 Not Acceptable = IP 突发限流，而非请求写法问题

arXiv 的边缘（Fastly/Varnish）通过返回 HTTP **406**（而非 429/503）来执行 IP 突发配额，
响应体为空且无 `Retry-After`。诊断方法是重复同一个请求：若一个带完美 headers/编码的裸请求
也在 200/406 之间随机跳变，那就是限流 — 改 UA headers 与 URL 编码都**没用**。重试模式：
把 406 当 429 处理 — 从 ≥60s 起的指数退避（上限 ~240s，加 jitter），最多约 6 次；
在窗口期内猛敲重试会延长窗口，所以两次尝试之间要静默等待，而不是紧密重试。

## 备注

- arXiv 返回 Atom XML — 用辅助脚本或解析片段得到干净输出
- Semantic Scholar 返回 JSON — 经 `python3 -m json.tool` 提升可读性
- arXiv ID：旧格式（`hep-th/0601001`）vs 新格式（`2402.03300`）
- PDF：`https://arxiv.org/pdf/{id}` — 摘要：`https://arxiv.org/abs/{id}`
- HTML（可用时）：`https://arxiv.org/html/{id}`
- 本地 PDF 处理见 `ocr-and-documents` skill

## ID 版本

- `arxiv.org/abs/1706.03762` 总是指向**最新**版本
- `arxiv.org/abs/1706.03762v1` 指向某个**特定**的不可变版本
- 生成引用时，保留你实际读的那个版本后缀，以防引用漂移（后续版本可能大幅改动内容）
- API 的 `<id>` 字段返回带版本的 URL（如 `http://arxiv.org/abs/1706.03762v7`）

## 撤稿论文

论文可在提交后被撤回。出现这种情况时：
- `<summary>` 字段含撤回声明（找 "withdrawn" 或 "retracted"）
- 元数据字段可能不完整
- 在把一个结果当作有效论文前，务必先看 summary
