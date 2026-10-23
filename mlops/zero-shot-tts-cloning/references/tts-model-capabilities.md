# 开源 TTS 能力矩阵（乃琳线实测核验，2026-10）

选型前先跑一遍「四处对质」流程复核，此表是快照不是真理。

| 模型 | 中文 | 零样本克隆 | 行内标签 | 情感控制通道 | 备注 |
|---|---|---|---|---|---|
| Qwen3-TTS (0.6B/1.7B, Base/CustomVoice/VoiceDesign) | ✅ | ✅ 仅 Base 档 | ❌ 三档 added_tokens 实测零标签 | instruct 前置（仅 CustomVoice，0.6B 被代码硬关） | instruct 与克隆分属两档互斥。正文语义自适应影响韵律。社区 SpragAI/qwen3-tts-emotion-tags 用 LoRA 蒸馏标签=原生不支持的反证 |
| Fun-CosyVoice3-0.5B | ✅ | ✅ 3s 级 | ✅ 训进词表 | instruct2 固定句式集 + 18 方言 | 唯一「中文+克隆+标签」三者齐全。0.5B 快一个量级（加载 15s、RTF<1） |
| CosyVoice2-0.5B | ✅ | ✅ | ✅ 同词表 | instruct2 | 标签机制同源 |
| Chatterbox-Turbo (350M) | ❌ 仅英语 | ✅ | ✅ 原生 [chuckle][laugh] | exaggeration/cfg_weight 旋钮 | 英文内容备选。全家内置 Perth 神经水印 |
| Chatterbox-Multilingual V3 (500M) | ✅ 23 语 | ✅ | ❌ | exaggeration（借参考音频的情绪强度） | 无标签 |
| Kokoro-82M | ✅ | ❌ 仅 54 预设音色 | ❌（[Kokoro](/IPA/) 是 G2P 发音覆盖非情感） | 无 | 无克隆=乃琳线一票否决。适合「不要音色只要快」（CPU 实时） |

核验路径备忘：
- Qwen3-TTS 词表：HF 模型卡 `tokenizer_config.json` → added_tokens_decoder（33 个 ChatML 标记，无情感 token）。论文控制机制=prepend instructions。
- CosyVoice 标签：仓库 `cosyvoice/tokenizer/tokenizer.py` 的 special_tokens 清单 + `example.py` 官方行内标签示例 + `cosyvoice/utils/common.py` instruct_list。
- 商业 API（阿里云 qwen-tts-flash / CosyVoice 云版）与开源版是两本账，SSML `<break>` 只有商业版有。
