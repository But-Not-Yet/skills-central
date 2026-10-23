---
name: zero-shot-tts-cloning
description: 要克隆某个声音时加载（ZipVoice、XTTS、CosyVoice 类零样本 TTS）：参考音频制备流程、克隆结果不像/糊/乱的变量剥离顺序、CosyVoice 系调教与 Windows 部署坑。基调一条：音色语速韵律全在参考音频里，文本写不出『慵懒』。
version: 1.0.0
author: Nekonya
license: MIT
metadata:
  hermes:
    tags: [tts, zipvoice, voice-cloning, audio]
    related_skills: [llama-cpp, local-model-selection]
---

# 零样本 TTS 克隆管线

## When to Use

主人要用零样本克隆 TTS（ZipVoice、XTTS、CosyVoice 类）定制音色时。或克隆成品音质差要诊断时。或要从 B 站/网络素材制备参考音频时。只要话题落在「克隆某个声音」或「克隆出来不像/糊/乱」，就加载。

参考音频决定一切：克隆迁移的是 prompt 里的音色、语速、气声、韵律。文本写不出「慵懒」，只能挑对的素材。情绪/语速需求 = 素材选材问题，不是参数问题。

## 开工前：先读模型自己的规格，别套通用经验

- 动手前查该模型 README 的 prompt 长度与格式建议。通用 zero-shot TTS 的「10~20 秒最佳」经验会害死人：ZipVoice 官方推荐单说话人 **<3 秒**，实测 18s prompt 比 3s 慢 5~7 倍 RTF。且官方明说长 prompt 会降质量。
- 「支持特殊标记吗」要四处对质，README 一句话不算数。① README 机制描述 ② 部署档 tokens.txt 实查（grep 方括号 token 计数）③ 家族其它档的词表 ④ HF 模型卡 `tokenizer_config.json` 的 added_tokens 全集。⑤ 仓库源码里 tokenizer 类的 `add_special_tokens` 清单：有的模型把标签注册在源码 special_tokens 里而不在 HF config，两处都要查才算数。README 常为整个家族写，落到具体部署档可能是 0 个标记可用。反向实证同样硬：社区为加某标记专门造语料微调，即证明原生不支持。
- 词表 OOV 标点（如省略号 …）会被静默丢弃。停顿只能靠参考音频带，文本里写省略号无效。合成文本尽量只用词表内标点（逗号/句号）。

## 参考音频制备流程（顺序即规矩）

1. **选材**：按目标音色/语速搜素材。高能直播切片=语速快，耳语/电台段=慢而气声重。唱歌类必带伴奏，先排除。
2. **下载**（B 站）：yt-dlp 需带 UA + Referer 头否则 412 反爬。`bilisearch` 加 `--flat-playlist` 拿不到标题，去 flat 直接 `--print "%(id)s | %(duration)s | %(view_count)s | %(title)s"`。个别视频（大会员）无 bestaudio，跳过即可。
3. **噪音/BGM 质检**：帧级 RMS（50ms 窗），语音电平取 85 分位、停顿间隙取 15 分位。间隙中位电平 > -40dBFS 就判有铺底 BGM，**整条删**（主人规矩：有噪音或背景音乐直接删，不做修复）。-50dBFS 以下算干净。**但直播/电台源上所有自动 BGM 判据都不可靠**：间隙能量法漏掉垫在语音底下的 BGM。「最静秒」测到的可能是器乐间奏（据此判「无 BGM」会把唱歌段当说话切出来）。窄带稳定峰对音量起伏的直播垫乐不报警。指标只做粗筛缩小范围，**最终裁决一律发片段给主人耳朵**，被耳朵否决就换路不要修指标。给主人 A/B 试听的每条片段一律过 `loudnorm=I=-16:TP=-1.5`（主人点过名：不归一化没法比）。
4. **裁窗**：在干净素材里找语音最密的窗口（滑动窗数语音帧占比）。时长按模型规格（ZipVoice 推荐 <3s，实测完整句 4~6s 质量更稳、RTF 仍 ~1）。别只取开头：开头可能是静音或弱音。
5. **prompt 信息密度是生死线（比情感浓度优先）**：对每个候选窗口跑 ASR 数汉字/秒，按密度降序给主人挑。实义句 ≥3 字/秒才可用。纯语气词/呻吟拖腔的 prompt（「啊，喜欢姐姐嘛」），文本与音频的逐字锚点几乎不存在。一个「啊」拖两秒就没法对齐。flow-matching 先验塌，长句中段必崩成复读乱码，哪怕它情感最浓。情感靠台词本身带语气词补，不靠 prompt 的呻吟。呻吟/娇喘类素材的选材判据是能量包络的节奏，不是有声密度。密度峰筛出来是连成一片的「产房叫」。真呻吟=包络峰间距规律（0.8~2.5s 一次）+ 动态范围大（>25dB）。滑窗对包络峰间距 CV+动态范围打分，密度只做粗筛。纯呻吟窗当 zero-shot 锚属低密度高危档。成品时长虚胖 20%+ 是对齐崩的前兆，必过 ASR 对质。
5. **逐字 ptext（最易破的规矩）**：ptext 必须是对**裁好的窗口本身**跑 ASR 的转写。禁止从更长音频的转写稿上手截前半句：窗口实际内容不等于长稿前缀。喂词与音频偏差直接导致克隆胡言乱语（flow-matching 靠 prompt 文本-音频逐字对齐学发音，对齐崩=瞎编）。截完逐字回填，宁可 ASR 慢一遍。
6. **耳语/低音量/呻吟素材**：whisper 类 ASR 在耳语下会丢重复结构，时间戳也不可信（会把静音吞进段里）。低音量素材用能量滑窗定位语音段，别信 whisper 时间戳。呻吟/拟声段会被硬转成实义字（拖音「别～」转成「别别别」），`no_speech_prob ≥ 0.5` 即拟声信号、转写只当参考。ptext 以主人听写为准，主人的耳朵比 whisper 准。

## 诊断「音质不行」的变量剥离顺序

0. **成品先过 ASR 逐字对质**：把合成音频转写出来跟目标文本比。胡言乱语的典型签名是「开头正常→中段复读/乱字→结尾锚定能听懂」（full 版「不,不,不,不…」）。这是对齐崩溃不是音质问题，别再调 steps/量化。同时看生成时长：同文本下成品远超正常长度（拖到 1.5~3 倍）= 对齐崩的前兆指标。
1. ptext 与 prompt 音频是否逐字匹配（最常见、最致命）
2. prompt 长度是否超模型推荐档
3. 采样步数（steps）损失
4. 量化档（int8 vs fp32）：做量化阶梯实验
5. vocoder 采样率上限（物理天花板，换参数无解）
6. 参考素材本身质量

RTF 异常变慢先查 prompt 长度再查硬件：长 prompt 吃推理时间是机制性的，不是板子热了。

多模型选型对比（各家克隆/标签/情感通道核验结果与核验路径）见 references/tts-model-capabilities.md。

## CosyVoice 系（开源 v2/v3）调教要点

- **行内标签是训进词表的 special token**（`[breath] [sigh] [laughter] [quick_breath] [lipsmack]` 等，见仓库 tokenizer 源码的 add_special_tokens），句中插入即响应。这是它相对 Qwen3-TTS 全线的独占能力。但标签清单里没有细粒度情绪词（无 [whisper]/[moan]），喘与叹只能靠 breath/sigh 间接表达。
- **长文本按标点切块逐句合成再拼接**（CLI 的 text_normalize split=True），接缝天然赶拍「抢话」。且**每个合成块末尾模型习惯性补一口吸气**（能量上表现为接缝前 ~300ms 的 -5~-21dB 鼓包）。治法是逐块**按能量自适应裁尾**：从块尾向前找最后一个真有声帧，保留其后 ~150ms，只剪静音和气声。再配块尾淡出与句间交叉淡化拼接，不要硬插零值静音（硬拼接缝生硬）。**禁固定毫秒数硬裁**。实测硬裁 350ms 会吃掉压在块尾的实义字。同文本两条在同一位置缺同一个字，就是拼接脚本干的，不是模型崩。裁线阈值必须**按每块自身语音电平取相对值**，例如 85 分位减 18dB。绝对阈值会把软声锚（语音电平本身才 -35dB）的句尾整段当气声误剪。诊断吸气残留就用静音谷定位：找 < -45dB 的连续段，再查它前 350ms 的能量。
- **speed 参数判死**：实现是对 mel 频谱线性插值拉伸（源码 token2wav），非 1.0 档出电音。官方 issue 挂着「speed interpolation 质量差」。要慢就写标点，别调 speed。
- **正文语义反向拉唱法**（论文 text semantics 通道）：锚定音色底子，台词语气词定腔调走向。「嘛/哦/呀/啦」堆多了音色往甜妹漂，撤掉甜词才回锚的本色。要什么腔调就写什么腔调的词。
- **instruct 只吃官方固定句式集**（common.py 的 instruct_list：开心/伤心/方言/快慢那套）。自由措辞在分布外，模型会退回「helpful assistant」的默认人格，音色被稀释。情感靠锚的底色+正文语义+标签，不靠自由 instruct。
- **台词里的语气词会被逐字念出**：每句缀「嗯」当情绪垫字，成品就句句带这个口癖。鼻音拖尾还会被裁尾切出怪音。语气词密度十句留一，句尾用标点收。
- **锚的底噪会被克隆搬进成品**：直播软语源间隙电平普遍在 -17~-37dB（气声加房间噪声垫底）。间隙 15 分位 > -40dB 的锚即使音色对也会让成品句尾脏。选锚先全库扫间隙电平，≤ -50dB 档优先。
- torchaudio ≥2.9 起读写后端并入 torchcodec（PyTorch 官方 2.9 release notes 原文；技能旧版写 2.10 是记晚了一版）：Windows 无对应 wheel 时装不上，脚本里 monkey-patch `torchaudio.load/save` 用 soundfile 顶替即可跑通。
- **prompt 音频有 30 秒硬闸**：speech tokenizer 源码 assert `do not support extract speech token for audio longer than 30s`：CLI 层不截断，tokenizer 却直接拒。多段拼接复合锚必须先验总长 <30s 再喂（留 0.5s 余量）。查「最长支持多少」要翻到 tokenizer 层的 assert，CLI/frontend 无截断不等于无上限。
- **复合锚（多段拼接 prompt）的对齐脆弱性**：锚越长、其中纯呻吟/低密度段占比越高，对齐越脆。实测 29s 复合锚（含 ~10s 纯呻吟）出片吞整段台词（成品时长砍半）、换 ptext 写法后退化成 0.3s 或 conv kernel 尺寸崩。规则：复合锚里呻吟占比压到 ~30% 以下、ptext 的拟声段只对应锚里最小的一段。别把每段呻吟都在文本里喂一遍（音频里有就够了）。成品时长异常（砍半或虚胖 20%+）一律 ASR 逐段对质定位吞了哪段，再决定减锚还是减文本。
- **复合锚响度均衡是必查项（10-08 实测）**。多段拼接锚里喘段常比说话段响 19dB+（整体 LUFS 却正常。粗测还会被静音帧拉高、虚报差值，要按有声帧 50ms 窗 85 分位精测）。响度差会被模型当韵律特征学走，喘段压倒性响，等于告诉引擎「这人常态是尖叫」。修法：按 >=150ms 静音缝分段、逐段增益对齐到最响段（段内动态要保留，禁止整条压缩：娇喘要的就是动态）。峰值超 0.89 整体回落防削波、最后 loudnorm 交付。脚本模板 bal_batch.py。
- **复合锚甜点配方（主人耳朵裁决）**：总长 15~20s、说话段占 60~80%、其余喘段。说话段必须语态多样化（平淡/御姐/软语混拼。单一语态的锚情感平）。喘段一律尾部淡出裁切 + 喘后 ~0.25s 人造静音间隔，防截断毛刺喂进 tokenizer。实测梯度：6~9s 短锚（只带喘）稳定但情感平，15~20s 多语态复合居中，29s 多语态复合情感最浓。**情感来自多语态说话段，不来自锚长。也不来自 BGM/demucs 伪影**（带/去 BGM 单变量对照两版都一般，BGM 情感载体假设判死）。成品情感不对时，把**喂进去的复合锚本身**也转 MP3 交主人耳朵验（拼接结构带时间轴报账）。先验料再改配方。喘料选材走主人耳朵：把未筛候选窗整批交主人挑，挑中再切段→ASR→demucs，不自作主张先处理。
- **inline 标签词表是封闭集**（tokenizer 源码 add_special_tokens 一手）：`[breath] [noise] [laughter] [cough] [clucking] [accent] [quick_breath] [hissing] [sigh] [vocalized-noise] [lipsmack] [mn]` + `<strong></strong>` `<laughter></laughter>` 两对包裹。没有 pause/结巴/whisper/moan 这类。主人给的自定义标注（`[breath in]`/`[停顿]`/`[结巴]`）必须映射进词表：近义标签替换、停顿落标点、结巴落字面重复。映射前先查源码原文，不凭记忆。

## Windows 部署 CosyVoice 类仓库的连环坑（2026-10-07 实测，一次踩齐）

- cmd 经 SSH 跑 `cd D:\...` 不带 `/d` **不切盘**（当前盘仍是 C），requirements 报「文件不存在」先怀疑这个，别怀疑文件。
- openai-whisper 的 setup.py 依赖 `pkg_resources`，setuptools≥81 已移除 → 先 `pip install "setuptools<81"` 再 `pip install openai-whisper --no-build-isolation`。**requirements.txt 整包也要带 --no-build-isolation 重跑**，否则 whisper 在 build isolation 的新 env 里再炸一次。且失败会静默中断后续依赖（hyperpyyaml 等全没装上）。
- pip 默认拉 **CPU 版 torch**（Windows 上无脑装），装完必须 `torch.cuda.is_available()` 验真身。更阴的坑是：**requirements.txt 会把已钉好的 CUDA torch 静默顶回旧版**（实测 cu128 被顶回 2.3.1+cu121）。requirements 装完必须再 `pip list | findstr torch` 复核版本再跑。RTX 50 系（Blackwell sm_120）遇旧核报 `CUDA error: no kernel image is available`。解药是 requirements 之后再补一轮 `pip install torch==X+cuYYY torchaudio==X+cuYYY --index-url https://download.pytorch.org/whl/cuYYY`。
- 从仓库外调脚本时 sys.path[0]=脚本目录而非仓库根，`import 包名` 报 ModuleNotFound。冒烟测试 cd 进仓库跑通过≠脚本从别处调也通过，脚本里显式 `sys.path.insert(0, 仓库根)`。
- 磁盘满是隐形杀手：git clone 报 `invalid index-pack output`、hf 下载报 os error 112 都可能是盘满而非网络。先 `Get-PSDrive D` 看 Free 再重试网络，别对着 GitHub 反复重试浪费十分钟。
- 每步 pip 结束必须 findstr 自己埋的 OK 哨兵（PIP_OK）+ import 冒烟测试双验。exit code 0 不代表装完（&& 链里 findstr 之类的小失败会吞掉整链）。

## 工具坑

- faster-whisper 与 PyAV ≥19 冲突（`av.open() got unexpected keyword 'metadata_errors'`）：绕开它的解码器，用 wave+numpy 把 WAV 读成 float32 数组直接喂 `transcribe(audio_array)`。
- 板上 sherpa-onnx 部署目录常有嵌套子目录（模型在 `sherpa-onnx-*-emilia/` 下、vocoder 在上一层）。报 File doesn't exist 先 find 实际布局再改路径。
- 音频处理链：ffmpeg `highpass=f=60,afftdn,loudnorm` → 24kHz 单声道 pcm_s16le。给主人试听一律转 MP3（桌面端 WAV 预览不可靠）。
- ssh 里跑带中文的 heredoc python 易被引号炸：落成 .py 文件 scp 上板再执行。
- ffprobe/ffmpeg 一次只吃一个输入文件：多文件当多参数会报 `Argument 'X' provided as input filename, but 'Y' was already specified`：改用 for 循环逐文件跑。
- 远程长探针被本地中断（scp/ssh 链掐断）不等于远端没跑完：先读远端日志 tail 与产物清单再决定重跑。重跑前先查 `*_ALL_DONE` 哨兵，别盲目复跑浪费 GPU 时间。

## BGM 素材抢救：demucs 音源分离

音色对但带 BGM 的素材，用 demucs 剥伴奏（实测 htdemucs 剥得干净，主人耳朵验收过）：`pip install --user demucs`（会带 CPU 版 torch）。`python3 -m demucs --two-stems=vocals <音频>`，CPU 实测 ~4 秒音频/秒（35s 音频 8s 跑完），产物在 `sep_out/htdemucs/<名>/vocals.wav`。分离后人声仍要过密度筛选：分离治的是 BGM。它治不了语气词 prompt 的对齐崩（带 BGM 原版当 prompt 对照组一样崩，伪影不是主犯）。选材优先级：天然零 BGM 源 > 分离救活的源。详见 references/audio-source-mining.md。

两个 demucs 后续坑：① **产物是 44.1kHz 立体声**，直接喂只吃 24k 单声道的模型会 assert。先 `ffmpeg -ac 1 -ar 24000 -sample_fmt s16` 转成模型规格再传，别传原始产物。② **demucs 只剥间隙里的 BGM，垫在语音底下的漏声剥不掉**（实测间隙 -30→-35dB，仍不过 -40 红线）。「去 BGM 版」不等于干净锚，主人验收前照标 BGM 嫌疑。

## 音频分析前的声道/采样率验真

任何帧级能量分析、切窗、拼接之前，先 ffprobe 声道数与采样率。**立体声按单声道读会把时长虚胖一倍**，所有段边界、密度峰坐标就此全作废。实测例：46.8s 假象实为 23s，切出的「重复段」全是错位。多段拼接前逐段 assert 采样率一致，demucs/ffmpeg 产物尤其要验。
