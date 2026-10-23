# 渲染比对 与 控制符兼容性

## 为什么必须渲染

模板是程序，不是文本。「两个模板功能一样」这个判断只能由**输出**支撑——特性字符串勾选表只能判「有没有这个分支」，判不了「分支产出什么」。

典型踩坑：勾选表显示两个模板同为 Qwen 家族、都带 `preserve_thinking` / `tool_call` / `developer`，于是判「已一致、不需迁移」；实际一渲染，**每个用例都不同**——因为其中一个在思考开启时默认注入一段推理强度提示，另一个不注。这个差异在字符串层面看不见，在行为层面很大。

**规则**：任何「A 和 B 等价 / 不需要换」的结论，必须附带一张渲染 diff。

## 渲染脚手架

HF 系模板用 `jinja2.sandbox.ImmutableSandboxedEnvironment`，并注入 `raise_exception`（模板用它做校验）与 `tojson`。

```python
import jinja2, json
from jinja2.sandbox import ImmutableSandboxedEnvironment

def make_env():
    e = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
    e.filters["tojson"] = lambda x, **kw: json.dumps(x, ensure_ascii=False)
    def raise_exception(msg):
        raise RuntimeError("TEMPLATE_REJECT: " + str(msg))
    e.globals["raise_exception"] = raise_exception
    return e

def render(path, args):
    src = open(path, encoding="utf-8").read()
    return make_env().from_string(src).render(**args)
def render_text(src, args):
    return make_env().from_string(src).render(**args)   # 直接拿线上的字符串（/props）
```

拿「线上实际在跑的模板」时不要读文件，去拿服务返回的字符串（去问进程，见 `deployment-paths.md`）。

## 用例矩阵（至少这六条）

每条都单独跑、单独 diff；汇总成一张「live=N 字符 / 候选=M 字符 / 同·异」的表。

| # | 构造 | 它在探什么 |
|---|---|---|
| 1 | `system + user` | 基线；系统提示有没有被改写 |
| 2 | `system + system + user`（**双 system**） | 多 system 是否被合并；名字不同不等于功能不同——要看渲染 |
| 3 | `system + developer + user` | developer role 支持 |
| 4 | 带 `tools=[...]` | 工具协议块、工具调用格式、工具场景下思考段的写法 |
| 5 | `user / assistant(带 reasoning_content) / user` | 历史思考是否保留（`preserve_thinking`），多轮格式 |
| 6 | 同上但 `enable_thinking=False` | 关思考路径是否自洽（**常见的倒退都是只修了开思考那一路**）|

```python
CASES = {
 "1 sys+user":       dict(messages=[{"role":"system","content":"SYS"},{"role":"user","content":"hi"}], add_generation_prompt=True),
 "2 dual-system":    dict(messages=[{"role":"system","content":"S1"},{"role":"system","content":"S2"},{"role":"user","content":"hi"}], add_generation_prompt=True),
 "3 sys+dev+user":   dict(messages=[{"role":"system","content":"SYS"},{"role":"developer","content":"DEV"},{"role":"user","content":"hi"}], add_generation_prompt=True),
 "4 with-tools":     dict(messages=[{"role":"system","content":"SYS"},{"role":"user","content":"hi"}],
                          tools=[{"type":"function","function":{"name":"f","description":"d",
                                  "parameters":{"type":"object","properties":{}}}}], add_generation_prompt=True),
 "5 multi-turn":     dict(messages=[{"role":"user","content":"Q1"},{"role":"assistant","content":"A1","reasoning_content":"RC"},{"role":"user","content":"Q2"}], add_generation_prompt=True),
 "6 think-off":      dict(messages=[{"role":"system","content":"SYS"},{"role":"user","content":"hi"}], add_generation_prompt=True, enable_thinking=False),
}
```

读结果的要点：
- **长度差是信号，不是结论**；用 `difflib.unified_diff` 看具体多/少了什么。
- 关心三类差异：**多出来的系统提示段**、**控制标记写法**、**关思考路径**。
- 模板可能抛 `raise_exception`（校验失败）——把异常当结果记，不要当环境错误跳过（通常意味着那组输入在你的模板里非法）。

## 静默丢内容：改完必须断言「新内容真的在里面」

渲染不报错 ≠ 内容生效。模板能安静地把一整段丢掉，一个字都不警告。

### 机制：同名嵌套 block-set

```jinja
{%- set core %}
{%- set core %}      {#- 同名又开一层 -#}
   ……整段规则……
{%- endset %}
{%- endset %}
```

内层先赋值，外层紧接着把它**覆盖成空字符串**。最小复现（真测过）：

```python
"{% set x %}{% set x %}ABCDEF{% endset %}{% endset %}[{{ x }}]"  →  "[]"
"{% set x %}ABCDEF{% endset %}[{{ x }}]"                          →  "[ABCDEF]"
```

**`set` / `endset` 计数配平不能当体检**——4 对 4 是配平的，`core` 照样是空。修法是把重复的那一对合并成单层。

### 检查代码

```python
KEYWORDS = ["新加的那句", "另一句"]      # 你这次改动引入的关键词
out = render_text(template_src, CASES["1 sys+user"])
for kw in KEYWORDS:
    assert kw in out, f"KEYWORD MISSING FROM RENDER: {kw!r}"
```

### 为什么要连「改前」也查

踩到这个 bug 的通常是**写模板的那一手**，不是这次改动。若只查自己新加的，会误以为旧段落在生效：
- 基于「这条纪律在起作用」做的所有 A/B **全部作废**——实验在对着空气测；
- 还会反向得出「这条纪律没用」的错误结论。

**判据固定为「关键词在不在渲染输出里」，不是「有没有抛异常」。**

## 控制符兼容性（跨家族迁移前必查）

控制标记不是普通文本，它们必须是**词表里的独立 token**。模板输出了一个不在词表里的标记 → tokenizer 把它切碎当普通文本 → 模型看到一个陌生的字符串而非常规控制符 → **不报错，只是变笨/失控**。

检查法：扫 GGUF 词表里目标标记是否存在（`scripts/gguf_inspect.py --vocab-check`）。

经验结论（真测过）：
- Qwen 系标记（`<|im_start|>` / `<|im_end|>` / `<|endoftext|>` / `<|vision_start|>`）在 **Qwen** 词表里命中；在 **Gemma** 与 **Xing** 词表里**零命中**。
- Gemma 用自己的体系（`<|turn>` / `<|channel>thought` / `<|think|>`）。
- Xing 用自己的体系。
- 因此：**Qwen 系模板只能在 Qwen 系模型间搬**。同名标看似旁系的两个模型，控制符重叠需要实测，不能推。

寄托在模板里的「私有标记」（如某个占位符约定）是**部署专属**的，它的理由往往绑在特定推理引擎的行为上（例：引擎把某个字面量 token 当立即结束信号）——把它搬到别的引擎上通常只是噪声。判据：那条纪律是否引用了引擎行为。

## 领域提醒：`high` 可能是 `xhigh` 的别名

推理强度这类枚举经常做别名归一（`high` / `max` 之类映射到 `xhigh`，两档之间没有中间档），而模板自己对非法值抛异常。
判断「某个档位到底注入了什么」，看模板里的分支，并**用 `medium` 当「什么都不注入」的基准**。

## 量化模板效果：先数 token，别数字符

比两个模板「谁产出得多」，**跨语言比字符数是错的**。同一个 tokenizer 实测：中文约 **0.6 token/字**，英文约 **0.14 token/字**——差 4 倍。中英混排的两次输出，字符数一比全是假信号。

llama-server 自带 `/tokenize`，拿它数：

```bash
curl -s -X POST localhost:8080/tokenize -H 'Content-Type: application/json' \
  -d '{"content":"要数的文本"}' | jq '.tokens | length'
```

注意 `usage.completion_tokens` **含思考段**，而 `message.content` 不含。

## 模板 A/B 的臂设计与读数

### 三臂，不是两臂

| 臂 | 内容 | 作用 |
|---|---|---|
| A | **出厂模板**（GGUF 内置 / 官方） | 基线 |
| B | **原版定制模板**（改动前） | 隔离「换模板」这个变量 |
| C | **改后模板** | 隔离「这次改动」这个变量 |

只跑 A vs C 会把**两件事**混在一起（换成了定制模板 + 这次改动），分不出差异来自哪一个。B 臂是必须的——这是最常见的实验设计错误。

### 读数：纪律类提示词会把 token 从正文挪进思考

实测过一个反直觉的结果：给模型加「简洁」纪律后，
- 正文 token **减半**（1273 → 641）——字面目标达成；
- 但思考 token **涨了 27%**（6534 → 8324）；
- **总量反而比出厂模板更高**。

**判「省不省」看 `completion_tokens` 总量，不看正文长度。** 用户看到的连长一点，不代表性价更高。

### 探针设计

- 一条探针只探一件事，题面逐字节固定，各臂完全一致。
- 记录 `finish_reason` 与 `usage`；`finish_reason=length` 的样本判 INVALID 而不是当低分。
- **探测行为规则要用「压力陷阱」，不要用中性题**：例如测「不编造引用」就用「帮我找一篇证明 X 的论文，给出作者和 DOI」——然后**逐条核实它给出的编号**（真测过：常给出**真编号 + 假标题/假作者**，比纯编造更难识破，因为编号能打开）。框架说对了不等于内容没编。
