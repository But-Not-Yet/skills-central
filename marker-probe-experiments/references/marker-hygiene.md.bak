# 标记卫生：家族表、孤儿清扫与取证配方

来源：tiered 插件的 wire 面孤儿清扫与生产库普查；家族清单以 lcm-x `escalation.py` 为准（跨工具一致）。

## 一、家族表（在用的正则源）

- **闭合对**（可成对识别）：开 `<(?P<tag>think|thinking|reasoning|thought|REASONING_SCRATCHPAD)(\s[^<>]*)?>`，闭 `</(?P=tag)\s*>`，IGNORECASE。
- **未闭合起点检测**（lcm-x 用于防摘要漏网，仅检测）另覆盖：管道形（`<|` + 可选 `start_of_` + 词 + `|>`）、方括号形、散文中缀形（`Thinking Process:` / `Chain of thought:`，可带 markdown 井号）。
- 分工：**清扫只用有配对语义的形**（角度族 + 控制 rails）；检测形不进清扫。

## 二、控制 rails（im_start / im_end）

- 成对控制标记；rails 部分由 `chr()` 拼装（`chr(60)+chr(124)+…`），任何书写通道（代码、测试、命令、报告）不出现完整字面量；报告里用占位符掩码。
- 配对 = 栈式：start 入栈、end 弹栈；落单者即孤儿。成对出现的整段模板引用不会被动到。

## 三、孤儿清扫算法（文本级，O(n)）

1. 廉价预检：文本无 `<` 直接跳过（绝大多数消息零成本）。
2. 逐 token 扫描（角度族一个正则、rails 一个正则），记 (家族, 标签, 开/闭, span)。
3. 按（家族, 标签名小写）分栈贪心配对；未配对的 span 收进孤儿表。
4. 有孤儿 → 按 span 切片重建字符串（删段拼接）；无孤儿 → 返回原对象。
5. 幂等天然成立：删除不制造新孤儿；确定性保证前缀稳定。

## 四、范围与契约（生产定稿）

- 只扫 assistant 消息的 `content` 与思考字段串值；工具/用户消息不扫（引用噪声源，见 §五）。
- copy-on-change；无变化返回原对象；整链无变化时宿主拿 None（保持原 no-op 契约）。
- env 开关 `TIERED_MARKER_SWEEP`（默认开、0 关、调用时读）。
- 测试形态：对照测试（无变化/开关）修复前后都过；微基准验证热路径成本（快路径设计）。

## 五、取证配方（只读）

- 打开生产库一律只读 URI：`sqlite3.connect("file:<db>?mode=ro", uri=True)`（或 CLI 只读查询）。
- 计数：先宽松拿总量 → 再**严格前缀**（`content LIKE '<前缀>%'`）+ `COUNT(DISTINCT <消息键>)`；按 `role` 分组看分布。
- 抽样：命中行的上下文 60–90 字符打印，命中原形用掩码替换（防输出通道散播）。
- 判读：命中集中在 tool/user 且上下文是代码/模板/文档 → **引用噪声**；只有生成侧（assistant）的落单标记才谈得上泄漏。无分层就下结论 = 把提及当泄漏。

## 六、跨引用

- 统计分层规则：先分层，再下口（本库细则即本篇 §五）。
- 生产装载探针（PM 启动链）：`hermes-local-ops-troubleshooting`。
- 实现仓库：tiered 插件（`~/.hermes/plugins/tiered`，README 载有 tunable 表）。
