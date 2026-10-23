# 模板部署路径与验证

## 模板可能同时住在四个地方

| 位置 | 谁读它 |
|---|---|
| **GGUF 元数据** `tokenizer.chat_template` | llama.cpp 等直接读 GGUF 的运行时 |
| 模型目录的 `chat_template.jinja` 文件 | transformers ≥ 4.51（含当前 LM Studio / oMLX） |
| `tokenizer_config.json` 里的 `chat_template` 键 | 较老的运行时（只读内嵌键，**忽略 .jinja 文件**） |
| 自建引擎的 tokenizer 包目录（如 `.../packs/<model>/tokenizer/chat_template.jinja`） | 那个引擎自己 |

**双子源陷阱（最常见的「我换了但没生效」）**：目录里同时有 `.jinja` 文件和旧的 `tokenizer_config.json` 内嵌副本时。**新旧运行时各读一个**，拿到的行为不一样。放新文件到旧内嵌副本旁边 = 静默无效果。

不确定运行时读哪个时，**两边都打**：`.jinja` 文件放完整版，`tokenizer_config.json` 放**压缩成单行的同一模板**。注意：两个副本的**文本必然不同**（完整 vs 压缩），所以**不能拿文本比对当校验。要比渲染输出**（见 `rendering-and-comparison.md`）。

## 验证清单：模板真的生效了吗

**不要信启动参数。** 去问正在跑的进程：

```bash
curl -s localhost:8080/props | jq -r .chat_template | sha256sum   # 与源文件哈希比
curl -s localhost:8080/props | jq -r .chat_template | head -c 300 # 看开头长什么样
```

llama-server 还有 `POST /apply-template`，可对给定 messages 直接拿渲染结果。

有自检脚本就用自检脚本（能一次报出「所有模板来源 + 是否一致 + 提示词在不在」的那种）。

## llama.cpp：临时 vs 持久

```bash
# 临时（本次启动有效，完全替换 GGUF 内置模板）
llama-server -m model.gguf --chat-template-file my.jinja --reasoning-format deepseek -ngl 99

# 持久（写回 GGUF，不用重量化）
pip install gguf
gguf-new-metadata --chat-template-file my.jinja input.gguf output.gguf
```

两个顺序陷阱：
- `--jinja` 在现行 build **已默认开**。老 build 要显式加，且**必须放在 `--chat-template-file` 之前**（否则模板会被当成「不认识的模板名」而只接受内置列表）。
- flag 是**单次生效**的：忘一次就静默退回内置模板。要跨多次启稳定生效，用 `gguf-new-metadata` 写回去，或写进启动脚本。

`--reasoning-format` 是 **API 响应层**的设置，对 `llama-cli` 无效。

## 自建引擎（tokenizer 包目录）

引擎从自己的 tokenizer 包目录读 `chat_template.jinja`。验证方式一样：拉 `/props` 拿哈希与文件比。
**仍然要先读引擎自己的源码/配置**，确认它确实读这个文件、以及有没有缓存。不要凭目录里有个 `.jinja` 就断定它在用。

## 换了模板会连带改变什么（迁移前必须写下来）

把模板差异分三类，每类单独报告：

1. **多出来的提示段**——最影响行为的一类（简洁纪律、标记纪律、推理强度提示）。
2. **控制标记写法**——影响 token 对齐与 prefix cache。并行工具调用块之间的**一个换行 vs 两个换行**这种细节会改变 token 流，关系到多轮 agentic 的 prefix 命中。
3. **默认值**——两个模板各自 `default(...)` 落到哪里。迁移会把「开来」变成「关掉」或反之，这是无声的行为变更。

## 迁移到多个模型时：先分类，不要一刀切

同一个自定义模板**不是对所有模型都适用**：

- 同家族同代：迁移通常是**空操作**（先渲染确认，可能本来就是一个模板），或者一次净升级。
- 同家族跨代：可行。但**新增特性未必被旧模型理解**（例：模板里注入的推理强度提示是给新代设计的，旧代没有这个能力）——当作**待 A/B 的实验**，不要当场宣定。
- 异家族：**不可行**，控制符零重叠（见 `rendering-and-comparison.md`）。

先跑词表检查分类，再对可行的那一档设计 A/B（同一批 agentic 题，带模板 / 不带模板各一轮）。而不是直接全量替换。
