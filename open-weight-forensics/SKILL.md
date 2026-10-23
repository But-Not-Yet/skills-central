---
name: open-weight-forensics
description: "验证关于开源模型权重/量化的断言时使用：远程取张量字节自算统计，跨实例对照。"
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [research, verification, quantization, model-artifacts, epistemics]
---

# 开源模型权重取证

## When to Use

有人（含你自己、含社区帖子）断言某开源模型「权重坏了」「某层张量异常」「量化损伤大」「去审查版毁能力」时；或需要比对两种量化格式的精度时。**不要转述讨论区——直接测量。** 配套的抽象纪律见 mechanism-claim-discipline（本技能是它在模型产物上的实例化 + 具体配方）。

## 核心优势

不下载完整权重。用 HTTP Range 只取目标张量的字节，一次尺度异常断言通常在 MB 级流量内就能证完（例：一个 `[8192,1,4]` BF16 张量 64 KB）。

## 管线

1. 列文件：`GET https://huggingface.co/api/models/<repo>` → `siblings[].rfilename`，找 `model.safetensors.index.json` 与各分片。
2. 定位张量：`GET https://huggingface.co/<repo>/resolve/main/model.safetensors.index.json` → `weight_map`（张量名 → 分片）。
3. 读分片头：`Range: bytes=0-7` 得 u64 LE 头长 L；再取 `bytes=8-<8+L-1>` 得 JSON（每张量的 dtype / shape / data_offsets）。
4. 取张量字节：`Range: bytes=<8+L+off0>-<8+L+off1-1>`。
5. 解码：BF16 = `(uint16 << 16).view(float32)`；F32/F16 直接 `np.frombuffer`。
6. 统计：std / absmean / max / min，与跨层中位数比。

现成脚本：`scripts/hf_tensor_stats.py <repo> <name_substring>`（加 `--list` 先 dump 张量名谱系）。

## 判据分级（照 reporting 纪律）

- 测量在原始权重上复现 → 「已验证」。
- 因果机制（为什么这个尺度异常）→ 「假说」，除非有对照实验。
- 「修复后错误降 X%」若用作者自定义指标、且只对被改动对象计算 → **循环论证**：定义指标 → 把对象拉到最小化该指标 → 报告指标变好。它证明的是指标被最小化了，不是模型变好，中间没有一步测模型能力。

## 硬规则

1. **先分清原始 BF16 还是量化产物**。GGUF 的 σ 是量化后的，不能直接与原始权重比。断言方若在 GGUF 上测，先确认那是 BF16 无损转换还是量化档——否则你可能在给量化伪影背书。
2. **同层对照**。宣布「某层某张量异常」前，算同层其他张量（layernorm、gate、in_proj 等）的统计。同层普遍变大 = 末层普遍效应；只有目标张量尖起 = 局部异常。
3. **跨模型对照**。同族其他尺寸跑同一测量。同族普遍出现的模式 = **系统性配方特征**，不是该模型的随机损坏。把系统性规律读成「这台的两个坏张量」是高频误判。
4. **命名陷阱**。GGUF / llama.cpp 会重命名张量：Qwen 混合架构官方 `linear_attn.conv1d.weight` 在 llama.cpp 里叫 `ssm_conv1d.weight`。找不到名字时先 `--list` dump 全部张量名模式（正则把层号折叠成 `.N.`）再下结论。
5. **排混淆变量**。解释「用户说这模型能力差」前先问：跑的是原版还是去审查/去拒绝二创？什么量化档？哪个导出管线？二创（abliteration）与量化是**独立变量**——社区自称「无损」的二创实测有掉点案例（TruthfulQA/Lambada 掉点、激进档甚至输出语无伦次退回），不能默认归到底座权重。

## 输出

- 逐字给出你自己的测量数字 + 出处（repo、分片、张量名），结论与出处分栏写。
- 只用中文发令的主：结论用中文，代号/术语首现带白话括注。
- 未复现的部分标「未验证」，不许拿讨论区转述顶替测量。
