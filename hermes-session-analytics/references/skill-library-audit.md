# 技能库审计配方（来源、使用率、许可）

主人问「这些技能是谁写的 / 有没有用 / 许可干不干净」时跑这套，三个维度各自独立出表。

## 一、来源审计（自写 vs 自带）

自带技能随安装包发布在 `~/.hermes/hermes-agent/skills/`（安装目录用 `hermes --version` 的 Install directory 行确认）。逐个 SKILL.md 比 md5 分三类：原封未动 / 改写过（diff 行数分轻重）/ 不在自带清单（自写）。

```python
import os, hashlib
def collect(root):
    out = {}
    for dp, dirs, files in os.walk(root):
        if 'SKILL.md' in files:
            p = os.path.join(dp, 'SKILL.md')
            out[os.path.relpath(dp, root)] = hashlib.md5(open(p,'rb').read()).hexdigest()
    return out
b, u = collect('/home/alonzo/.hermes/hermes-agent/skills'), collect(os.path.expanduser('~/.hermes/skills'))
# 交集比 hash 分未改/改过；u-b = 自写。mtime 给自写排时间线。
```

- 轻改（只汉化 description）与重写（整篇正文换掉）分开报，用 difflib 数 diff 行——主人要的是「改动深度」，不是一个「都改过」。
- `.archive/` 目录下的技能排除在活跃计数外，单独报。

## 二、使用率审计（哪些技能真被加载过）

`skill_view` 的调用记录在宿主 `state.db` 的 `messages` 表里，**不在 `tool_calls` 字段**（该字段对 role='tool' 行恒为空）。正确取法：

```python
import re, collections
sv = collections.Counter()
for content, in st.execute("SELECT content FROM messages WHERE role='tool' AND tool_name='skill_view'"):
    m = re.search(r'"name"\s*:\s*"([^"]+)"', content or '')
    if m: sv[m.group(1)] += 1
```

按 profile 切段：`messages JOIN sessions` 取 `profile_name`。**宿主 state.db 只有 default profile 的行**；coder / researcher 等 worker 的加载记录在各自 `~/.hermes/profiles/<profile>/state.db`，跨人格结论必须逐库查，查不到就标未核验，不许从宿主库的 profile 分布推「worker 没加载过」。

判读规则：
- 加载次数为 0 或个位数的方法论技能 = 没进过战场。「技能不够」先证伪成「技能不被加载」，两种病药方相反（装更多不解决后者）。
- 拿自写高频技能当对照基线，才有「效果不好」的归因底气。
- 给某个 profile 装技能只喂那个 profile——各 profile 的 skills/ 是独立副本，主库装了 worker 吃不到。

## 三、许可审计

许可写在每个 SKILL.md 的 frontmatter（`license:` 字段），**不能按仓库整体许可一刀切**：同一仓库内混着 Apache 2.0、MIT 与 Proprietary（Anthropic 系文档四件套类技能标 Proprietary，adapted 后仍是）。要 MIT/Apache 的，逐技能读 frontmatter 出许可表再搬；CC BY 内容要留 attribution。
