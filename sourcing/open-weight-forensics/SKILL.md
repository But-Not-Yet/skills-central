---
name: open-weight-forensics
description: "验证开源模型权重与量化的断言时使用。只要有人声称某模型的张量、量化档或权重统计如何，就主动加载，即使是社区传言。远程取张量字节自算统计，跨实例对照。"
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [research, verification, quantization, model-artifacts, epistemics]
---

# 开源模型权重取证

## When to Use

有人（含你自己、含社区帖子）断言某开源模型「权重坏了」「某层张量异常」「量化损伤大」「去审查版毁能力」时。或需要比对两种量化格式的精度时。**不要转述讨论区——直接测量。** 配套的抽象纪律见 mechanism-claim-discipline（本技能是它在模型产物上的实例化 + 具体配方）。

## 核心优势

不下载完整权重。用 HTTP Range 只取目标张量的字节。一次尺度异常断言通常在 MB 级流量内就能证完（例：一个 `[8192,1,4]` BF16 张量 64 KB）。

## 管线

1. 列文件：`GET https://huggingface.co/api/models/<repo>` → `siblings[].rfilename`，找 `model.safetensors.index.json` 与各分片。
2. 定位张量：`GET https://huggingface.co/<repo>/resolve/main/model.safetensors.index.json` → `weight_map`（张量名 → 分片）。
3. 读分片头：`Range: bytes=0-7` 得 u64 LE 头长 L。再取 `bytes=8-<8+L-1>` 得 JSON（每张量的 dtype / shape / data_offsets）。
4. 取张量字节：`Range: bytes=<8+L+off0>-<8+L+off1-1>`。
5. 解码：BF16 = `(uint16 << 16).view(float32)`。F32/F16 直接 `np.frombuffer`。
6. 统计：std / absmean / max / min，与跨层中位数比。

现成脚本：`scripts/hf_tensor_stats.py <repo> <name_substring>`（加 `--list` 先 dump 张量名谱系）。

## GGUF 元数据读取（架构键与量化 provenance）

`pip install gguf` 后用 `GGUFReader`。遇私有量化码（标准枚举不认的 type，如 Strata 私有档）会在张量段抛 ValueError。子类化覆写 `_build_tensors(self,*a,**k): pass` 跳过张量段，metadata 段照常解析。字段值是 `f.contents()` **方法调用**（属性读出来是 bound method）。架构结论从 metadata 取：`general.architecture/name/description/size_label`、`<arch>.*` 超参（层数、注意力间隔、indexer、rope 分段）。`quantize.imatrix.*` 给量化 provenance（chunks_count/dataset/entries_count——「imatrix=1000」这类断言的指针就在这里）。手写 struct 解析 GGUF 极易在变长类型上漂位——用库，别手搓。

## 判据分级（照 reporting 纪律）

- 测量在原始权重上复现 → 「已验证」。
- 因果机制（为什么这个尺度异常）→ 「假说」，除非有对照实验。
- 「修复后错误降 X%」若用作者自定义指标、且只对被改动对象计算 → **循环论证**。定义指标 → 把对象拉到最小化该指标 → 报告指标变好。它证明的是指标被最小化了，不是模型变好，中间没有一步测模型能力。

## 硬规则

1. **先分清原始 BF16 还是量化产物**。GGUF 的 σ 是量化后的，不能直接与原始权重比。断言方若在 GGUF 上测，先确认那是 BF16 无损转换还是量化档——否则你可能在给量化伪影背书。
2. **同层对照**。宣布「某层某张量异常」前，算同层其他张量（layernorm、gate、in_proj 等）的统计。同层普遍变大 = 末层普遍效应。只有目标张量尖起 = 局部异常。
3. **跨模型对照，但不替两种读法站队**。同族其他尺寸跑同一测量。同族普遍出现 → 排除「该模型的随机损坏」，但**同时支持两种读法**：全族共有的架构/配方特征。或全族共有的训练缺陷。**同一份数据不区分这两者**。要区分就得设计能分辨的判据（该模式是否在非本族架构上缺席、是否随训练步数单调变化）。把系统性规律读成「这台的两个坏张量」是高频误判。把系统性规律一口咬定成「所以是特征」同样越界。
4. **命名陷阱**。GGUF / llama.cpp 会重命名张量：Qwen 混合架构官方 `linear_attn.conv1d.weight` 在 llama.cpp 里叫 `ssm_conv1d.weight`。找不到名字时先 `--list` dump 全部张量名模式（正则把层号折叠成 `.N.`）再下结论。**键名 ≠ 机制**：SSM 键名约定会被复用给别的机制——`ssm.*` 键下实际可能是 Gated DeltaNet（delta rule 递推）而非 Mamba2 SSM。宣布某层机制前必须交叉核对推理引擎源码（kernel 头文件的注释与递推实现）与官方模型文档。只凭键名归类必翻车。
5. **排混淆变量**。解释「用户说这模型能力差」前先问：跑的是原版还是去审查/去拒绝二创？什么量化档？哪个导出管线？二创（abliteration）与量化是**独立变量**。社区自称「无损」的二创实测有掉点案例（TruthfulQA/Lambada 掉点、激进档甚至输出语无伦次退回）。不能默认归到底座权重。
6. **血缘核验（「B 是不是 A 换皮」）**。取同名张量逐层对齐，算**余弦相似度 + 相对 L2 差**（脚本：`scripts/hf_tensor_compare.py <repoA> <repoB> <name_substring>`）。余弦 ~0.999x、相对差个位数百分比 = 轻量微调，不是新一代模型。再看哪些张量**几乎未动**（相对差 0.000x 量级）——那是共享底座的指纹。逐层排序还能看出改动集中在哪些层。

7. **厂商基准表按列位置对齐**。HF 模型卡的基准表常是 HTML（`<th>` 表头 + 4–5 个并列模型），且带空单元格。解析时**先取表头行、按列位置对齐**再取值，绝不按数值范围猜哪列是哪个模型。解析出的值个数与表头列数不符时，说明有空单元格被过滤了，回头重解。错位一列 = 一次跨实体挪用（把同代另一档的分当成目标的）。
8. **比较基准数字前先对齐协议与覆盖面**。同一基准名可对应两套做法（对数似然 vs 生成式解析），系统偏差不可忽略。题量少于定值就是子集。另有两条高频误判：**微调/合并模型不继承底座的公开分**（血统对≠分数对）。**家族内部不许跨尺寸取中位数**（得到的数不对应任何真实模型）。详见 `references/benchmark-number-comparability.md`。

## 相关参考

- `references/kv-and-param-accounting.md` —— 从主件算 KV 与参数量的公式与陷阱。
- `references/abliterated-model-evaluation.md` —— 评估去审查/二创版：两个取证站的分工、KL 读法、拒绝率为何不可横比、可信度判据。
- `references/benchmark-number-comparability.md` —— 读/比模型卡上的基准数：协议身份、题量覆盖、微调不继承底座分、不跨尺寸聚合。厂商对照表怎么用。

## 输出

- 逐字给出你自己的测量数字 + 出处（repo、分片、张量名），结论与出处分栏写。
- 只用中文发令的主：结论用中文，代号/术语首现带白话括注。
- 未复现的部分标「未验证」，不许拿讨论区转述顶替测量。
- **工具回显里的 `***` 可能是显示层脱敏，不是文件内容。** 要判断某个文件是否被改坏（例如委派出去的 worker 声称已还原的密钥行）。用**计数或哈希**（`grep -c '<字面量>'`）验，别信回显。
