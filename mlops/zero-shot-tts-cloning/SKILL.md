---
name: zero-shot-tts-cloning
description: 用零样本克隆 TTS（ZipVoice 等）做音色定制时使用，含参考音频制备与克隆质量诊断。
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

主人要用零样本克隆 TTS（ZipVoice、XTTS、CosyVoice 类）定制音色时；或克隆成品音质差要诊断时；或要从 B 站/网络素材制备参考音频时。只要话题落在「克隆某个声音」或「克隆出来不像/糊/乱」，就加载。

参考音频决定一切：克隆迁移的是 prompt 里的音色、语速、气声、韵律——文本写不出「慵懒」，只能挑对的素材。情绪/语速需求 = 素材选材问题，不是参数问题。

## 开工前：先读模型自己的规格，别套通用经验

- 动手前查该模型 README 的 prompt 长度与格式建议。通用 zero-shot TTS 的「10~20 秒最佳」经验会害死人：ZipVoice 官方推荐单说话人 **<3 秒**，实测 18s prompt 比 3s 慢 5~7 倍 RTF，且官方明说长 prompt 会降质量。
- 「支持特殊标记吗」要三处对质，README 一句话不算数：① README 机制描述 ② 部署档 tokens.txt 实查（grep 方括号 token 计数）③ 家族其它档的词表。README 常为整个家族写，落到具体部署档可能是 0 个标记可用。
- 词表 OOV 标点（如省略号 …）会被静默丢弃——停顿只能靠参考音频带，文本里写省略号无效。合成文本尽量只用词表内标点（逗号/句号）。

## 参考音频制备流程（顺序即规矩）

1. **选材**：按目标音色/语速搜素材。高能直播切片=语速快，耳语/电台段=慢而气声重。唱歌类必带伴奏，先排除。
2. **下载**（B 站）：yt-dlp 需带 UA + Referer 头否则 412 反爬；`bilisearch` 加 `--flat-playlist` 拿不到标题，去 flat 直接 `--print "%(id)s | %(duration)s | %(view_count)s | %(title)s"`。个别视频（大会员）无 bestaudio，跳过即可。
3. **噪音/BGM 质检**：帧级 RMS（50ms 窗），语音电平取 85 分位、停顿间隙取 15 分位；间隙中位电平 > -40dBFS 判有铺底 BGM，**整条删**（主人规矩：有噪音或背景音乐直接删，不做修复）。-50dBFS 以下算干净。**但直播/电台源上所有自动 BGM 判据都不可靠**：间隙能量法漏掉垫在语音底下的 BGM；「最静秒」测到的可能是器乐间奏（据此判「无 BGM」会把唱歌段当说话切出来）；窄带稳定峰对音量起伏的直播垫乐不报警。指标只做粗筛缩小范围，**最终裁决一律发片段给主人耳朵**，被耳朵否决就换路不要修指标。给主人 A/B 试听的每条片段一律过 `loudnorm=I=-16:TP=-1.5`（主人点过名：不归一化没法比）。
4. **裁窗**：在干净素材里找语音最密的窗口（滑动窗数语音帧占比），时长按模型规格（ZipVoice 推荐 <3s，实测完整句 4~6s 质量更稳、RTF 仍 ~1）。别只取开头——开头可能是静音或弱音。
5. **prompt 信息密度是生死线（比情感浓度优先）**：对每个候选窗口跑 ASR 数汉字/秒，按密度降序给主人挑，实义句 ≥3 字/秒才可用。纯语气词/呻吟拖腔的 prompt（「啊，喜欢姐姐嘛」）文本↔音频逐字锚点几乎不存在——一个「啊」拖两秒没法对齐——flow-matching 先验塌，长句中段必崩成复读乱码，哪怕它情感最浓。情感靠台词本身带语气词补，不靠 prompt 的呻吟。
5. **逐字 ptext（最易破的规矩）**：ptext 必须是对**裁好的窗口本身**跑 ASR 的转写，禁止从更长音频的转写稿上手截前半句——窗口实际内容 ≠ 长稿前缀，喂词与音频偏差直接导致克隆胡言乱语（flow-matching 靠 prompt 文本-音频逐字对齐学发音，对齐崩=瞎编）。截完逐字回填，宁可 ASR 慢一遍。
6. **耳语/低音量素材**：whisper 类 ASR 在耳语下会丢重复结构、时间戳不可信（把静音吞进段里）。低音量素材用能量滑窗定位语音段，别信 whisper 时间戳；转写结果给主人听写校正，主人的耳朵比 whisper 准。

## 诊断「音质不行」的变量剥离顺序

0. **成品先过 ASR 逐字对质**：把合成音频转写出来跟目标文本比。胡言乱语的典型签名=「开头正常→中段复读/乱字→结尾锚定能听懂」（full 版「不,不,不,不…」），这是对齐崩溃不是音质问题，别再调 steps/量化。同时看生成时长：同文本下成品远超正常长度（拖到 1.5~3 倍）= 对齐崩的前兆指标。
1. ptext 与 prompt 音频是否逐字匹配（最常见、最致命）
2. prompt 长度是否超模型推荐档
3. 采样步数（steps）损失
4. 量化档（int8 vs fp32）——量化阶梯实验
5. vocoder 采样率上限（物理天花板，换参数无解）
6. 参考素材本身质量

RTF 异常变慢先查 prompt 长度再查硬件——长 prompt 吃推理时间是机制性的，不是板子热了。

## Windows 部署 CosyVoice 类仓库的连环坑（2026-10-07 实测，一次踩齐）

- cmd 经 SSH 跑 `cd D:\...` 不带 `/d` **不切盘**（当前盘仍是 C），requirements 报「文件不存在」先怀疑这个，别怀疑文件。
- openai-whisper 的 setup.py 依赖 `pkg_resources`，setuptools≥81 已移除 → 先 `pip install "setuptools<81"` 再 `pip install openai-whisper --no-build-isolation`；**requirements.txt 整包也要带 --no-build-isolation 重跑**，否则 whisper 在 build isolation 的新 env 里再炸一次，且失败会静默中断后续依赖（hyperpyyaml 等全没装上）。
- pip 默认拉 **CPU 版 torch**（Windows 上无脑装），装完必须 `torch.cuda.is_available()` 验真身，假 True 没有——不对，是假 CPU：验完再 `pip install torch==X+cuYYY --index-url https://download.pytorch.org/whl/cuYYY`。
- 磁盘满是隐形杀手：git clone 报 `invalid index-pack output`、hf 下载报 os error 112 都可能是盘满而非网络。先 `Get-PSDrive D` 看 Free 再重试网络，别对着 GitHub 反复重试浪费十分钟。
- 每步 pip 结束必须 findstr 自己埋的 OK 哨兵（PIP_OK）+ import 冒烟测试双验，exit code 0 不代表装完（&& 链里 findstr 之类的小失败会吞掉整链）。

## 工具坑

- faster-whisper 与 PyAV ≥19 冲突（`av.open() got unexpected keyword 'metadata_errors'`）：绕开它的解码器，用 wave+numpy 把 WAV 读成 float32 数组直接喂 `transcribe(audio_array)`。
- 板上 sherpa-onnx 部署目录常有嵌套子目录（模型在 `sherpa-onnx-*-emilia/` 下、vocoder 在上一层），报 File doesn't exist 先 find 实际布局再改路径。
- 音频处理链：ffmpeg `highpass=f=60,afftdn,loudnorm` → 24kHz 单声道 pcm_s16le；给主人试听一律转 MP3（桌面端 WAV 预览不可靠）。
- ssh 里跑带中文的 heredoc python 易被引号炸——落成 .py 文件 scp 上板再执行。

## BGM 素材抢救：demucs 音源分离

音色对但带 BGM 的素材，用 demucs 剥伴奏（实测 htdemucs 剥得干净，主人耳朵验收过）：`pip install --user demucs`（会带 CPU 版 torch），`python3 -m demucs --two-stems=vocals <音频>`，CPU 实测 ~4 秒音频/秒（35s 音频 8s 跑完），产物在 `sep_out/htdemucs/<名>/vocals.wav`。分离后人声仍要过密度筛选——分离治 BGM，治不了语气词 prompt 的对齐崩（带 BGM 原版当 prompt 对照组一样崩，伪影不是主犯）。选材优先级：天然零 BGM 源 > 分离救活的源。详见 references/audio-source-mining.md。
