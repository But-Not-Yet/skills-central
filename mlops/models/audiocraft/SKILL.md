---
name: audiocraft-audio-generation
description: "用 AudioCraft 生成音频时使用：MusicGen 文生音乐、AudioGen 文生音效。只要要生成音乐或音效、做文生音频，就主动加载，即使用户只说「来段背景音乐」。"
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [audiocraft, torch>=2.0.0, transformers>=4.30.0]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Multimodal, Audio Generation, Text-to-Music, Text-to-Audio, MusicGen]

---

# AudioCraft：音频生成

Meta AudioCraft 的全面指南：用 MusicGen、AudioGen 与 EnCodec 做文生音乐与文生音频。

## 何时用 AudioCraft

**以下情况用 AudioCraft：**
- 需要从文字描述生成音乐
- 制作音效与环境音
- 构建音乐生成应用
- 需要旋律条件化的音乐生成
- 想要立体声音频输出
- 需要带风格迁移的可控音乐生成

**关键特性：**
- **MusicGen**：带旋律条件化的文生音乐
- **AudioGen**：文生音效
- **EnCodec**：高保真神经音频编解码器
- **多种模型规模**：Small（300M）到 Large（3.3B）
- **立体声支持**：完整立体声音频生成
- **风格条件化**：MusicGen-Style 做基于参考的生成

**以下情况改用替代方案：**
- **Stable Audio**：更长的商业音乐生成
- **Bark**：带音乐/音效的文本转语音
- **Riffusion**：基于频谱图的音乐生成
- **OpenAI Jukebox**：带歌词的原始音频生成

## 快速开始

### 安装

```bash
# From PyPI
pip install audiocraft

# From GitHub (latest)
pip install git+https://github.com/facebookresearch/audiocraft.git

# Or use HuggingFace Transformers
pip install transformers torch torchaudio
```

### 基础文生音乐（AudioCraft）

```python
import torchaudio
from audiocraft.models import MusicGen

# Load model
model = MusicGen.get_pretrained('facebook/musicgen-small')

# Set generation parameters
model.set_generation_params(
    duration=8,  # seconds
    top_k=250,
    temperature=1.0
)

# Generate from text
descriptions = ["happy upbeat electronic dance music with synths"]
wav = model.generate(descriptions)

# Save audio
torchaudio.save("output.wav", wav[0].cpu(), sample_rate=32000)
```

### 用 HuggingFace Transformers

```python
from transformers import AutoProcessor, MusicgenForConditionalGeneration
import scipy

# Load model and processor
processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
model.to("cuda")

# Generate music
inputs = processor(
    text=["80s pop track with bassy drums and synth"],
    padding=True,
    return_tensors="pt"
).to("cuda")

audio_values = model.generate(
    **inputs,
    do_sample=True,
    guidance_scale=3,
    max_new_tokens=256
)

# Save
sampling_rate = model.config.audio_encoder.sampling_rate
scipy.io.wavfile.write("output.wav", rate=sampling_rate, data=audio_values[0, 0].cpu().numpy())
```

### 用 AudioGen 文生音效

```python
from audiocraft.models import AudioGen

# Load AudioGen
model = AudioGen.get_pretrained('facebook/audiogen-medium')

model.set_generation_params(duration=5)

# Generate sound effects
descriptions = ["dog barking in a park with birds chirping"]
wav = model.generate(descriptions)

torchaudio.save("sound.wav", wav[0].cpu(), sample_rate=16000)
```

## 核心概念

### 架构概览

```
AudioCraft Architecture:
┌──────────────────────────────────────────────────────────────┐
│                    Text Encoder (T5)                          │
│                         │                                     │
│                    Text Embeddings                            │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│              Transformer Decoder (LM)                         │
│     Auto-regressively generates audio tokens                  │
│     Using efficient token interleaving patterns               │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                EnCodec Audio Decoder                          │
│        Converts tokens back to audio waveform                 │
└──────────────────────────────────────────────────────────────┘
```

### 模型变体

| Model | Size | 说明 | 用途 |
|-------|------|-------------|----------|
| `musicgen-small` | 300M | 文生音乐 | 快速生成 |
| `musicgen-medium` | 1.5B | 文生音乐 | 均衡 |
| `musicgen-large` | 3.3B | 文生音乐 | 最佳质量 |
| `musicgen-melody` | 1.5B | 文本 + 旋律 | 旋律条件化 |
| `musicgen-melody-large` | 3.3B | 文本 + 旋律 | 最佳旋律 |
| `musicgen-stereo-*` | 不定 | 立体声输出 | 立体声生成 |
| `musicgen-style` | 1.5B | 风格迁移 | 基于参考 |
| `audiogen-medium` | 1.5B | 文生音效 | 音效 |

### 生成参数

| 参数 | 默认值 | 说明 |
|-----------|---------|-------------|
| `duration` | 8.0 | 时长（秒，1-120） |
| `top_k` | 250 | Top-k 采样 |
| `top_p` | 0.0 | 核采样（0 = 关闭） |
| `temperature` | 1.0 | 采样温度 |
| `cfg_coef` | 3.0 | 无分类器引导 |

## MusicGen 用法

### 文生音乐生成

```python
from audiocraft.models import MusicGen
import torchaudio

model = MusicGen.get_pretrained('facebook/musicgen-medium')

# Configure generation
model.set_generation_params(
    duration=30,          # Up to 30 seconds
    top_k=250,            # Sampling diversity
    top_p=0.0,            # 0 = use top_k only
    temperature=1.0,      # Creativity (higher = more varied)
    cfg_coef=3.0          # Text adherence (higher = stricter)
)

# Generate multiple samples
descriptions = [
    "epic orchestral soundtrack with strings and brass",
    "chill lo-fi hip hop beat with jazzy piano",
    "energetic rock song with electric guitar"
]

# Generate (returns [batch, channels, samples])
wav = model.generate(descriptions)

# Save each
for i, audio in enumerate(wav):
    torchaudio.save(f"music_{i}.wav", audio.cpu(), sample_rate=32000)
```

### 旋律条件化生成

```python
from audiocraft.models import MusicGen
import torchaudio

# Load melody model
model = MusicGen.get_pretrained('facebook/musicgen-melody')
model.set_generation_params(duration=30)

# Load melody audio
melody, sr = torchaudio.load("melody.wav")

# Generate with melody conditioning
descriptions = ["acoustic guitar folk song"]
wav = model.generate_with_chroma(descriptions, melody, sr)

torchaudio.save("melody_conditioned.wav", wav[0].cpu(), sample_rate=32000)
```

### 立体声生成

```python
from audiocraft.models import MusicGen

# Load stereo model
model = MusicGen.get_pretrained('facebook/musicgen-stereo-medium')
model.set_generation_params(duration=15)

descriptions = ["ambient electronic music with wide stereo panning"]
wav = model.generate(descriptions)

# wav shape: [batch, 2, samples] for stereo
print(f"Stereo shape: {wav.shape}")  # [1, 2, 480000]
torchaudio.save("stereo.wav", wav[0].cpu(), sample_rate=32000)
```

### 音频续写

```python
from transformers import AutoProcessor, MusicgenForConditionalGeneration

processor = AutoProcessor.from_pretrained("facebook/musicgen-medium")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-medium")

# Load audio to continue
import torchaudio
audio, sr = torchaudio.load("intro.wav")

# Process with text and audio
inputs = processor(
    audio=audio.squeeze().numpy(),
    sampling_rate=sr,
    text=["continue with a epic chorus"],
    padding=True,
    return_tensors="pt"
)

# Generate continuation
audio_values = model.generate(**inputs, do_sample=True, guidance_scale=3, max_new_tokens=512)
```

## MusicGen-Style 用法

### 风格条件化生成

```python
from audiocraft.models import MusicGen

# Load style model
model = MusicGen.get_pretrained('facebook/musicgen-style')

# Configure generation with style
model.set_generation_params(
    duration=30,
    cfg_coef=3.0,
    cfg_coef_beta=5.0  # Style influence
)

# Configure style conditioner
model.set_style_conditioner_params(
    eval_q=3,          # RVQ quantizers (1-6)
    excerpt_length=3.0  # Style excerpt length
)

# Load style reference
style_audio, sr = torchaudio.load("reference_style.wav")

# Generate with text + style
descriptions = ["upbeat dance track"]
wav = model.generate_with_chroma(descriptions, style_audio, sr)  # 官方 MusicGen-Style 页用的是这个入口（melody 位参）
```

### 仅风格生成（无文本）

```python
# Generate matching style without text prompt
model.set_generation_params(
    duration=30,
    cfg_coef=3.0,
    cfg_coef_beta=None  # Disable double CFG for style-only
)

wav = model.generate_with_chroma([None], style_audio, sr)
```

## AudioGen 用法

### 音效生成

```python
from audiocraft.models import AudioGen
import torchaudio

model = AudioGen.get_pretrained('facebook/audiogen-medium')
model.set_generation_params(duration=10)

# Generate various sounds
descriptions = [
    "thunderstorm with heavy rain and lightning",
    "busy city traffic with car horns",
    "ocean waves crashing on rocks",
    "crackling campfire in forest"
]

wav = model.generate(descriptions)

for i, audio in enumerate(wav):
    torchaudio.save(f"sound_{i}.wav", audio.cpu(), sample_rate=16000)
```

## EnCodec 用法

### 音频压缩

```python
from audiocraft.models import CompressionModel
import torch
import torchaudio

# Load EnCodec
model = CompressionModel.get_pretrained('facebook/encodec_32khz')

# Load audio
wav, sr = torchaudio.load("audio.wav")

# Ensure correct sample rate
if sr != 32000:
    resampler = torchaudio.transforms.Resample(sr, 32000)
    wav = resampler(wav)

# Encode to tokens
with torch.no_grad():
    encoded = model.encode(wav.unsqueeze(0))
    codes = encoded[0]  # Audio codes

# Decode back to audio
with torch.no_grad():
    decoded = model.decode(codes)

torchaudio.save("reconstructed.wav", decoded[0].cpu(), sample_rate=32000)
```

## 常用工作流

### 工作流 1：音乐生成流水线

```python
import torch
import torchaudio
from audiocraft.models import MusicGen

class MusicGenerator:
    def __init__(self, model_name="facebook/musicgen-medium"):
        self.model = MusicGen.get_pretrained(model_name)
        self.sample_rate = 32000

    def generate(self, prompt, duration=30, temperature=1.0, cfg=3.0):
        self.model.set_generation_params(
            duration=duration,
            top_k=250,
            temperature=temperature,
            cfg_coef=cfg
        )

        with torch.no_grad():
            wav = self.model.generate([prompt])

        return wav[0].cpu()

    def generate_batch(self, prompts, duration=30):
        self.model.set_generation_params(duration=duration)

        with torch.no_grad():
            wav = self.model.generate(prompts)

        return wav.cpu()

    def save(self, audio, path):
        torchaudio.save(path, audio, sample_rate=self.sample_rate)

# Usage
generator = MusicGenerator()
audio = generator.generate(
    "epic cinematic orchestral music",
    duration=30,
    temperature=1.0
)
generator.save(audio, "epic_music.wav")
```

### 工作流 2：音效设计批处理

```python
import json
from pathlib import Path
from audiocraft.models import AudioGen
import torchaudio

def batch_generate_sounds(sound_specs, output_dir):
    """
    Generate multiple sounds from specifications.

    Args:
        sound_specs: list of {"name": str, "description": str, "duration": float}
        output_dir: output directory path
    """
    model = AudioGen.get_pretrained('facebook/audiogen-medium')
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    results = []

    for spec in sound_specs:
        model.set_generation_params(duration=spec.get("duration", 5))

        wav = model.generate([spec["description"]])

        output_path = output_dir / f"{spec['name']}.wav"
        torchaudio.save(str(output_path), wav[0].cpu(), sample_rate=16000)

        results.append({
            "name": spec["name"],
            "path": str(output_path),
            "description": spec["description"]
        })

    return results

# Usage
sounds = [
    {"name": "explosion", "description": "massive explosion with debris", "duration": 3},
    {"name": "footsteps", "description": "footsteps on wooden floor", "duration": 5},
    {"name": "door", "description": "wooden door creaking and closing", "duration": 2}
]

results = batch_generate_sounds(sounds, "sound_effects/")
```

### 工作流 3：Gradio demo

```python
import gradio as gr
import torch
import torchaudio
from audiocraft.models import MusicGen

model = MusicGen.get_pretrained('facebook/musicgen-small')

def generate_music(prompt, duration, temperature, cfg_coef):
    model.set_generation_params(
        duration=duration,
        temperature=temperature,
        cfg_coef=cfg_coef
    )

    with torch.no_grad():
        wav = model.generate([prompt])

    # Save to temp file
    path = "temp_output.wav"
    torchaudio.save(path, wav[0].cpu(), sample_rate=32000)
    return path

demo = gr.Interface(
    fn=generate_music,
    inputs=[
        gr.Textbox(label="Music Description", placeholder="upbeat electronic dance music"),
        gr.Slider(1, 30, value=8, label="Duration (seconds)"),
        gr.Slider(0.5, 2.0, value=1.0, label="Temperature"),
        gr.Slider(1.0, 10.0, value=3.0, label="CFG Coefficient")
    ],
    outputs=gr.Audio(label="Generated Music"),
    title="MusicGen Demo"
)

demo.launch()
```

## 性能优化

### 内存优化

```python
# Use smaller model
model = MusicGen.get_pretrained('facebook/musicgen-small')

# Clear cache between generations
torch.cuda.empty_cache()

# Generate shorter durations
model.set_generation_params(duration=10)  # Instead of 30

# Use half precision
model = model.half()
```

### 批处理效率

```python
# Process multiple prompts at once (more efficient)
descriptions = ["prompt1", "prompt2", "prompt3", "prompt4"]
wav = model.generate(descriptions)  # Single batch

# Instead of
for desc in descriptions:
    wav = model.generate([desc])  # Multiple batches (slower)
```

### GPU 显存需求

| Model | FP32 显存 | FP16 显存 |
|-------|-----------|-----------|
| musicgen-small | ~4GB | ~2GB |
| musicgen-medium | ~8GB | ~4GB |
| musicgen-large | ~16GB | ~8GB |

## 常见问题

| 问题 | 解决 |
|-------|----------|
| CUDA OOM | 换更小的模型，缩短时长 |
| 质量差 | 提高 cfg_coef，改进 prompt |
| 生成太短 | 检查最大时长设置 |
| 音频有杂音 | 试试不同的 temperature |
| 立体声不生效 | 用立体声模型变体 |

## 参考

- **[Advanced Usage](references/advanced-usage.md)** - 训练、微调、部署
- **[Troubleshooting](references/troubleshooting.md)** - 常见问题与解决

## 资源

- **GitHub**：https://github.com/facebookresearch/audiocraft
- **论文（MusicGen）**：https://arxiv.org/abs/2306.05284
- **论文（AudioGen）**：https://arxiv.org/abs/2209.15352
- **HuggingFace**：https://huggingface.co/facebook/musicgen-small
- **Demo**：https://huggingface.co/spaces/facebook/MusicGen
