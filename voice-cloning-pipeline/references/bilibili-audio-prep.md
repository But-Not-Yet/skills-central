# B 站音频抓取与质检代码

## 搜索与下载

```bash
# 装（一次性）
pip install --user yt-dlp

UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

# 搜（带标题挑素材；flat 模式标题全是 NA）
yt-dlp "bilisearch10:关键词" \
  --print "%(id)s | %(duration)s | %(view_count)s | %(title)s" \
  --playlist-end 10 \
  --user-agent "$UA" --add-header "Referer:https://www.bilibili.com/"

# 下载纯音轨
yt-dlp -f bestaudio -x --audio-format m4a -o "BV号.%(ext)s" \
  "https://www.bilibili.com/video/BV号/" \
  --user-agent "$UA" --add-header "Referer:https://www.bilibili.com/" --no-playlist
```

坑：直播录像类（FM/电台）常要大会员，报 `No video formats found!` 就放弃换源，别死磕。

## 转 24kHz 单声道

```bash
ffmpeg -y -i in.m4a -ar 24000 -ac 1 raw.wav
```

## 底噪质检（判 BGM/噪音铺底）

```python
import wave, numpy as np
def noise_audit(path):
    with wave.open(path) as w:
        sr = w.getframerate()
        d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768.0
    win = int(sr*0.05)
    db = np.array([20*np.log10(np.sqrt(np.mean(d[i*win:(i+1)*win]**2))+1e-9) for i in range(len(d)//win)])
    speech = np.percentile(db, 85)
    gaps = db[db < speech-20]
    gap_db = np.median(gaps) if len(gaps) else float('nan')
    # gap_db > -40 → BGM/噪音铺底，整条删；-40~-50 偏吵慎用；< -50 干净
    return gap_db
```

## 裁最长连续语音段

```python
def longest_speech(data, sr, target=(10.0, 20.0)):
    win = int(sr*0.05); n = len(data)//win
    db = np.array([20*np.log10(np.sqrt(np.mean(data[i*win:(i+1)*win]**2))+1e-9) for i in range(n)])
    voiced = db > np.percentile(db, 85) - 20
    pad = int(0.4/0.05)                      # 0.4s 内停顿算连续
    v = voiced.copy()
    for i in range(n):
        if voiced[i]: v[max(0,i-pad):min(n,i+pad)] = True
    runs, i = [], 0
    while i < n:
        if v[i]:
            j = i
            while j < n and v[j]: j += 1
            runs.append((i, j)); i = j
        else: i += 1
    runs = [(a,b) for a,b in runs if (b-a)*0.05 >= target[0]]
    if not runs: return None
    a, b = max(runs, key=lambda r: min(r[1]-r[0], 320))
    return a*0.05, min((b-a)*0.05, 18.0)     # (起点, 时长)
```

裁切 + 净化链：

```bash
ffmpeg -y -i raw.wav -ss <start> -t <len> \
  -af "highpass=f=60,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5" \
  -ar 24000 -ac 1 -c:a pcm_s16le prompt.wav
```

## ASR 逐字转写（faster-whisper）

坑：faster-whisper 传文件路径会经 PyAV 解码，新版 PyAV（≥19）报 `open() got an unexpected keyword argument 'metadata_errors'`——**绕开解码器，用 wave+numpy 读成 float32 数组直接喂 transcribe()**：

```python
import wave, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel('small', device='cpu', compute_type='int8')
with wave.open('prompt.wav') as w:
    audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768.0
segs, _ = m.transcribe(audio, language='zh', beam_size=5, vad_filter=True)
prompt_text = ''.join(s.text for s in segs).strip()
```

## sherpa-onnx ZipVoice 调用骨架

```python
import sherpa_onnx as s
D = "<部署根>/sherpa-onnx-zipvoice-distill-int8-zh-en-emilia"
zcfg = s.OfflineTtsZipvoiceModelConfig(
    tokens=f"{D}/tokens.txt", encoder=f"{D}/encoder.int8.onnx",
    decoder=f"{D}/decoder.int8.onnx",
    vocoder="<部署根>/vocos_24khz.onnx",          # 注意：vocoder 在上一层！
    data_dir=f"{D}/espeak-ng-data", lexicon=f"{D}/lexicon.txt")
tts = s.OfflineTts(s.OfflineTtsConfig(model=s.OfflineTtsModelConfig(
    zipvoice=zcfg, num_threads=4, provider="cpu")))
audio = tts.generate(text, prompt_text, prompt_samples, prompt_sr, speed=1.0, num_steps=4)
```
