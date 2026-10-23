---
name: voice-cloning-pipeline
description: 给零样本 TTS 克隆备参考音频并上板合成时使用，含 B 站抓声与质检。要音色素材或跑克隆管线就加载。
---

# 零样本 TTS 克隆管线（参考音频 → 板端合成）

核心原理：flow-matching 零样本克隆把**参考音频的风格整段迁移**到合成文本——音色、语速、气声、慵懒感全在 prompt wav 里；参考音频本身不需要是目标情绪（念歌词的切片照样能克隆出「御姐腔念撩人台词」），文本里写情绪符号没用。控制通道只有两个：参考音频选材、合成文本内容。

## 管线顺序（不可乱）

1. **抓素材**：B 站搜索用 yt-dlp `bilisearchN:关键词`，必须带 `--user-agent`（Chrome UA）+ `--add-header "Referer:https://www.bilibili.com/"`，否则 412 反爬。`--flat-playlist` 拿不到标题——要挑素材就别用 flat。下载 `-f bestaudio -x --audio-format m4a`。选**说话类**切片，唱歌类必带伴奏直接排除。详见 `references/bilibili-audio-prep.md`。
2. **底噪质检（主人的硬规矩：有噪音或 BGM 直接整条删）**：帧级 RMS，语音电平取 85 分位，间隙电平取「低于语音-20dB 帧」的中位数；间隙中位 > -40 dBFS = 有铺底 → 整条删，不做降噪抢救。代码在 references。
3. **裁段**：找最长连续语音段（0.4s 内停顿算连续），取 10~20 秒（太短风格覆盖不够）。转 24 kHz 单声道 16-bit WAV，链上 `highpass=f=60,afftdn,loudnorm`。
4. **ASR 逐字转写参考文本**：faster-whisper（small/int8/CPU）转写 prompt 段，产出与音频**严格逐字**的 prompt text。参考文本与音频不逐字匹配会破坏对齐、音质直接受损——数字写法（「36年」vs「三十六年」）都算不匹配，禁止手写参考文本。
5. **上板合成**：scp 到板上，sherpa-onnx venv 里跑 generate，num_steps=4。

## ZipVoice 专属坑

- **部署目录布局**：encoder/decoder/tokens/lexicon/espeak-ng-data 在 `sherpa-onnx-zipvoice-distill-int8-zh-en-emilia/` 子目录里，vocos_24khz.onnx 在**上一层**——配置里两个路径不同源，别拼同一个目录变量。
- **省略号「…」是词表 OOV**，会被 lexicon 直接丢弃——文本里的停顿全靠模型瞎猜。合成文本用逗号制造停顿；慵懒拖腔靠换更软的参考音频实现，不靠文本符号。
- **情感标签不存在**：蒸馏版/基础版 tokens.txt 里 0 个方括号标记；只有 ZipVoice-Dialog 档有 [LAUGHS] 等发声事件标记，且 sherpa-onnx 未转换该档。
- 板上 RTF 会漂移（同一管线两次实测 0.9~1.2 与 2~3 差一倍多）——生产规划前必须当场复测，别引用历史数字。

## VoxCPM2 情感克隆（2026-10-07 主人耳朵裁定可用）

- **管线**：`model.generate(text="(英文情感指令)正文", reference_wav_path=锚音频)` —— ref 隔离模式 + 文本开头括号指令，音色保住且情感遵循度好（主人实测）。prompt 续写模式（prompt_wav_path+prompt_text）里塞括号指令会崩对齐，两种模式别混用。
- **验收尺子分级（主人裁定）**：whisper ASR 对带情绪软语/气声/拖腔识别极差、会误判成乱码——ASR 只许验正常语速实义句的字准，情感软语必须主人耳朵裁决，ASR 不许一票否决。
- 笔记本 CUDA（5070 Ti）RTF ~0.5-1.0（短句更快），48kHz 原生输出；模型加载 53~238s 是一次性成本。Windows 上 Start-Process 后台跑 python 会无声死（日志 0 字节），前台直跑正常。
- **极限情感档（NSFW 娇喘级）可用**：括号指令直接压露骨发声描述有效——`breathy and seductive, soft moans and gasps between phrases, whimpering, intimate whisper close to the ear` / `rising pleasure, trembling voice, escalating moans, breathless, high pitched whimpers` 两档配方都跑通过。喘点位置写进正文（拟声词+逗号停顿，逗号顶替省略号），指令管发声质感、文本管喘的节奏。产物仍走耳朵裁决尺子。
- **逐短句情绪标签不支持**：官方 Style Control 只认正文**开头一处**括号指令（管整句），无 Orpheus 式行中 `[Whisper]` 方括号标签——社区微调加行中标签也无效且过拟合。行中插圆括号短语是未定义行为：实测会把时长拖爆、触发 `Badcase detected, audio_text_ratio` 自动重试（模型自判比例失控的信号），别当控制通道用。逐句情绪变化靠**正文拟声词+标点节奏**表达，不靠标签。
- **停顿控制 = 标点选类 + 开头指令写 pause 描述**：逗号=短停（0.2~0.6s 均匀）、句号=长停但可能失控成 3~5s 深渊；要「换气级」中长停（0.7~1.8s），在开头指令里显式写 `long pauses between phrases` 类描述再配句号断句，实测分布最自然。
- **停顿可量化验证**：交耳朵前先跑帧级静音统计（20ms 帧、RMS -45dBFS 判语音帧、列出 ≥0.15s 静音段）——停顿「不对」这类反馈能落成数字对照表，多版配方并排比分布。
- 笔记本 SSH：`laptop-training` 别名可能指向失效的 VPN 地址挂住超时——超时别重试别名，直接 `Alonzo@192.168.50.29`（LAN）+ `id_ed25519_deploy_laptop` 连，scp Windows 路径用正斜杠。
- 权重 openbmb/VoxCPM2（4.62 GB，笔记本直连 hf 24s 拉完）；0.5B 旧档 16kHz 音质差一档，GGUF 转换仓库只认 0.5B。
- 板上无 ffmpeg 系统库时 torchaudio.load(torchcodec) 炸：soundfile 顶替 torchaudio.load 即可（读 wav 够用）；板上 ffmpeg 7.1.5 主人已批准 apt 装好（2026-10-07）。

## Qwen3-TTS 线（2026-10-07 源码+官方文档一手核验）

- **能力矩阵（官方表+源码互证）**：instruct 情感通道只有 1.7B-CustomVoice/VoiceDesign 有；Base 档（克隆用）无 instruct 通道（包装器签名无此参数，Reddit SpragAI/qwen3-tts-emotion-tags 微调实证不响应）；**0.6B-CustomVoice 的 instruct 被源码硬关**（modeling 层 `if tts_model_size in "0b6": instruct=None`）——情感天花板必须 1.7B。
- **全线无 inline 标签**：官方词表 151,643 token 零副语言 token（added_tokens 全是 ChatML 家族）；论文（arXiv 2601.15621）控制机制只有「prepend 前置指令」一种。文本语义通道存在（「哈哈哈哈哈」写正文可影响韵律），但不是标签。
- **乃琳路线（主人裁定）**：官方 finetuning/ 单说话人 SFT（jsonl: audio+text+ref_audio，全数据集共用同一 ref_audio）→ 微调后走 `generate_custom_voice(speaker="新名")`，乃琳变内置说话人。备选后手：情感 x-vector 仿射（task vector 加到说话人嵌入，Reddit 作者实测，免微调）。
- **环境钉版坑（笔记本 Windows）**：`pip install qwen-tts` 默认拉 transformers 5.x → `check_model_inputs() missing 1 required positional argument` 崩 import；qwen-tts 0.1.1 钉 `transformers==4.57.3`。--system-site-packages venv 还会撞系统层旧 kernels（`StrictDataclassFieldValidationError: import_name`）——正解三件套：venv 内 `pip install transformers==4.57.3 "huggingface_hub<1.0" -U kernels`。
- **实测性能**：1.7B 加载仅 6s（远快于 VoxCPM2 的 53~238s）；Base 克隆 RTF≈3.3 是无 flash-attn 非流式最差档，别当上限报。速度层候选：Serveurperso/Qwen3-TTS-GGUF + qwentts.cpp（CUDA，非均匀量化，0.6B Q4_K_M 629MB+tokenizer 255MB；注意它 README 的 mode 命名与官方反着）；franken_tts（纯 Rust CPU，x86 4vCPU 仅 0.52x 实时，3588 无数据）。
- **手搓绕包装器（C2 教训）**：直接调 `model.generate(instruct_ids=...)` 配 voice_clone_prompt 时，ICL 模式下 `ref_code=None` 会在 :2191 下标崩——包装器会填 ref_code，手搓必须自己填齐或走非 ICL。
- **Kokoro-82M 已排除**（乃琳线）：无情感标签（issue #89/#254/#36 全悬空）、无零样本克隆（54 预设音色）；官方 `[词](/IPA/)` 语法是 misaki G2P 发音覆盖不是情感，社区传「标签」多系误传。适合「不要音色只要快」场景。

## 交付纪律

- 合成结果转 MP3 再发（桌面端 WAV 预览不可靠；MEDIA 投递用文档目录，缓存目录会 file not found）。
- **±条件对照产物必须可反查标签映射**：远端日志留生成顺序与 SAVED 行，scp 后本地与远端逐文件对 MD5——主人耳朵会抓「标反了」，届时当场拿三道账（日志顺序、文件名、双侧哈希）自证，不靠记忆辩解。
- **单样本对照不定论**：采样温度高（如 0.9）时两版单次差异可能被随机性淹没、时长差也不足以证明通道生效——判情感通道有无，每条件连采多次比组内/组间方差，先排除标签错位再排除随机。
- 每条产物标清参考来源切片与分工（冷艳/软/气声…），让主人按耳朵挑生产参考。
- 素材法律线：B 站/DLsite 素材个人自娱可用，商用无授权——涉及产品化要提醒。
