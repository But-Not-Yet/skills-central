# 去审查（uncensored）模型分诊

## 先破三个误解

1. **去审查不是无损的。** 实测规律：MMLU 几乎不动（±0.5–3），**TruthfulQA 普遍掉 5–11 分**，**GSM8K 最先崩**。技术越暴力掉得越狠，且模型越大越糟。
2. **技术比模型更重要。** 同一底座上，手术式（Heretic / ARA / Apostate）保留最好；大锤式（Obliteratus、改 router 的 Abliterix）会把模型打残（空回答率高、语言任务退化）。
3. **MoE 需要专门手法。** 只做稠密去审查，MoE 上会残留大量拒绝；要 **EGA（专家粒度去审查，逐专家 down_proj 切片）** 才降得下来。选 MoE 去审查变体时先确认它做了 EGA。

## 技术横比经验值（同底座）

`Heretic ≈ Huihui（最稳，KL 最低）` > `HauhauCS（改动面最广，达 97% 张量，空回答率最高）` ≈ `AEON（宣称增强，实测每项都降）` > `Abliterix（router 改动，loglikelihood 任务显著退化）`

- **HauhauCS 已被独立取证证伪**：其工具抄自 Heretic 且抹掉署名；「lossless / 0 refusals」声称不成立；同底座横比排名低于 Heretic/Huihui。**下载量是热度不是能力，别凭下载量排序。**
- Heretic 是**非确定性**的：同底座不同次运行结果不同，只有具体那个变体的基准才有意义。
- 用户对自己用过的某个变体有体感时，先查它属于哪种技术再归因；**「去审查版本感觉差」与「底座权重有问题」是两本账，不要混。**

## 同尺指标：UGI 榜

原始 CSV：`https://huggingface.co/spaces/DontPlanToEnd/UGI-Leaderboard/resolve/main/ugi-leaderboard-data.csv`（直接 csv 解析，别转述二手总结）。

四轴：
- **UGI**（0-100）：敏感话题知识广度——愿意说之后到底懂多少
- **W/10**：配合意愿（去审查程度）
- **NatInt**：自然智能（分辨「去了审查」vs「只会胡说」）
- **Writing**：写作质量——RP/创作**唯一**该看的轴

读数：底座模型 W/10 常 0.5–3，去审查后升到 8–10；UGI 从 ~20 升到 40–55。
**同一模型通常有「开思考」与「关思考」两行，分差很大，必须对齐模式再比。**

挑法：
- RP / 创作 → 看 **Writing**，别被高 UGI 骗（GLM-4.7-Flash、gpt-oss 系的 Writing 会塌到 16–25）。
- 安全 / 知识向 → UGI + NatInt。
- **坑**：原始 GSM8K 对思考模型不可用（思考预算耗尽的空回答记 0 分）。剔除空回答后常 <3 分，原始差距可达 40 分。

## 两个口径别混

- 跨基准、跨口径的数字不可比。
- 量化的「per-quantized-weight」与「per-total-file」是两个口径（带高精度嵌入的格式会在第二个口径上反转结论）。报数时必须写明是哪个。
