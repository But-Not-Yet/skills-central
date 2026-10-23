---
name: ascii-video
description: "制作 ASCII 视频时使用。只要要把视频 / 音频 / 图片转成彩色 ASCII 字符视频（MP4/GIF/序列帧），或做音频可视化、生成式 ASCII 动画。矩阵风效果，就主动加载，即使用户只说「做个 ASCII 动画」。"
platforms: [linux, macos, windows]
---

# ASCII 视频制作流水线

## 何时使用

当用户要求：ASCII 视频、文字艺术视频、终端风视频、字符艺术动画、复古文字可视化、ASCII 音频可视化。把视频转成 ASCII art、矩阵风效果，或任何动态 ASCII 输出时使用。

## 内容概览

适用于任何格式的 ASCII art 视频制作流水线。把视频 / 音频 / 图片 / 生成式输入转成彩色 ASCII 字符视频输出（MP4、GIF、图片序列）。涵盖：视频转 ASCII、音频反应式音乐可视化、生成式 ASCII art 动画、视频 + 音频混合反应式、文本 / 歌词叠加。实时终端渲染。

## 创作标准

这是视觉艺术。ASCII 字符是媒介，电影水准是标准。

**在写下第一行代码之前**，先明确创作概念。情绪是什么？它讲述怎样的视觉故事？是什么让*这个*项目区别于其他所有 ASCII 视频？用户的提示词只是起点——要以创作野心去诠释它，而非逐字转写。

**首次渲染即达到优秀，不可妥协。** 输出必须视觉惊艳，无需多轮返工。若看起来平庸、扁平，或像「AI 生成的 ASCII art」，那就是错的——重新思考创作概念再交付。

**超越参考词库。** 参考文档里的效果目录、shader 预设与调色板库只是起始词库。每个项目都要组合、修改并发明新模式。目录是颜料盒——画由你来画。

**主动发挥创造力。** 当项目需要时，扩展本 skill 的词库。若参考里没有视觉构想所需的东西，就自己构造。至少包含一个用户没要求但会欣赏的视觉瞬间——一个转场、一个效果、一种配色，提升整件作品。

**整体美学优先于技术正确。** 视频中所有场景必须由统一的视觉语言串联——共享的色温、相关的字符调色板、一致的运动词汇。一段技术上正确、但每个场景都用随机不同效果的视频，是美学上的失败。

**密集、分层、考究。** 每一帧都应值得观看。绝不使用纯黑平面背景。始终多网格构图。始终逐场景变化。始终有意的配色。

## 模式

| 模式 | 输入 | 输出 | 参考 |
|------|-------|--------|-----------|
| **Video-to-ASCII** | 视频文件 | 源素材的 ASCII 重建 | `references/inputs.md` § Video Sampling |
| **Audio-reactive** | 音频文件 | 由音频特征驱动的生成式视觉 | `references/inputs.md` § Audio Analysis |
| **Generative** | 无（或种子参数） | 程序化 ASCII 动画 | `references/effects.md` |
| **Hybrid** | 视频 + 音频 | 带音频反应式叠加的 ASCII 视频 | 两个输入参考 |
| **Lyrics/text** | 音频 + 文本/SRT | 带视觉效果的定时文本 | `references/inputs.md` § Text/Lyrics |
| **TTS narration** | 文本引文 + TTS API | 带打字机文本的旁白证言 / 引文视频 | `references/inputs.md` § TTS Integration |

## 技术栈

每个项目一个自包含的 Python 脚本。无需 GPU。

| 层 | 工具 | 用途 |
|-------|------|---------|
| 核心 | Python 3.10+, NumPy | 数学、数组运算、向量化效果 |
| 信号 | SciPy | FFT、峰值检测（音频模式） |
| 图像 | Pillow (PIL) | 字体栅格化、帧解码、图像 I/O |
| 视频 I/O | ffmpeg (CLI) | 解码输入、编码输出、封装音频 |
| 并行 | concurrent.futures | N 个 worker 做批量 / 片段渲染 |
| TTS | ElevenLabs API（可选） | 生成旁白片段 |
| 可选 | OpenCV | 视频帧采样、边缘检测 |

## 流水线架构

每种模式都走同一个 6 阶段流水线：

```
INPUT → ANALYZE → SCENE_FN → TONEMAP → SHADE → ENCODE
```

1. **INPUT** —— 加载 / 解码源素材（视频帧、音频采样、图片，或无）
2. **ANALYZE** —— 提取逐帧特征（音频频段、视频亮度 / 边缘、运动向量）
3. **SCENE_FN** —— scene 函数渲染到像素画布（`uint8 H,W,3`）。通过 `_render_vf()` + 像素混合模式组合多个字符网格。见 `references/composition.md`
4. **TONEMAP** —— 基于百分位的自适应亮度归一化。见 `references/composition.md` § Adaptive Tonemap
5. **SHADE** —— 经 `ShaderChain` + `FeedbackBuffer` 做后处理。见 `references/shaders.md`
6. **ENCODE** —— 把原始 RGB 帧通过管道交给 ffmpeg 做 H.264/GIF 编码

## 创作方向

### 美学维度

| 维度 | 选项 | 参考 |
|-----------|---------|-----------|
| **字符调色板** | 密度渐变、块元素、符号、文字系统（片假名、希腊字母、卢恩、盲文）、项目专用 | `architecture.md` § Palettes |
| **配色策略** | HSV、OKLAB/OKLCH、离散 RGB 调色板、自动生成调和、单色、色温 | `architecture.md` § Color System |
| **背景纹理** | 正弦场、fBM 噪声、domain warp、voronoi、反应扩散、元胞自动机、视频 | `effects.md` |
| **主要效果** | 环、螺旋、隧道、漩涡、波、干涉、极光、火焰、SDF、奇异吸引子 | `effects.md` |
| **粒子** | 火花、雪、雨、气泡、卢恩、轨道、集群 boids、流场跟随、拖尾 | `effects.md` § Particles |
| **Shader 氛围** | 复古 CRT、简洁现代、故障艺术、电影感、梦幻、工业、迷幻 | `shaders.md` |
| **网格密度** | xs(8px) 到 xxl(40px)，逐层混用 | `architecture.md` § Grid System |
| **坐标空间** | 笛卡尔、极坐标、平铺、旋转、鱼眼、Möbius、domain warp | `effects.md` § Transforms |
| **反馈** | 缩放隧道、彩虹拖尾、幽影回响、旋转曼陀罗、色彩演化 | `composition.md` § Feedback |
| **遮罩** | 圆形、环、渐变、文字模板、动画 iris/wipe/dissolve | `composition.md` § Masking |
| **转场** | 交叉淡入、擦除、溶解、故障切换、iris、基于遮罩的揭示 | `shaders.md` § Transitions |

### 逐段变化

整段视频绝不用同一套配置。对每个段落 / 场景：
- **不同的背景效果**（或组合 2-3 个）
- **不同的字符调色板**（匹配情绪）
- **不同的配色策略**（或至少不同色相）
- **调整 shader 强度**（高潮时更多 bloom，安静时更多颗粒）
- **不同的粒子类型**（若启用粒子）

### 项目专属发明

每个项目至少发明以下之一：
- 匹配主题的自定义字符调色板
- 自定义背景效果（组合 / 修改现有积木块）
- 自定义调色板（匹配品牌 / 情绪的离散 RGB 集合）
- 自定义粒子字符集
- 新颖的场景转场或视觉瞬间

不要只从目录里挑。目录是词汇——诗由你来写。

## 工作流

### 第 1 步：创作构想

写任何代码之前，先明确创作概念：

- **情绪 / 氛围**：观者该有什么感受？活力、冥想感、混乱、优雅、不祥？
- **视觉故事**：整段时长里发生什么？积累张力？蜕变？溶解？
- **色彩世界**：暖 / 冷？单色？霓虹？大地色？主色调是什么？
- **字符质感**：密集数据？稀疏星光？有机圆点？几何块？
- **这个*项目*为何不同**：让它独一无二的那一点是什么？
- **情绪曲线**：场景如何推进？以能量开场、推向高潮、收束？

把用户的提示词映射到美学选择。「舒缓 lo-fi 可视化」与「故障赛博朋克数据流」所需的一切都不同。

### 第 2 步：技术设计

- **模式** —— 上述 6 种中的哪一种
- **分辨率** —— 横屏 1920x1080（默认）、竖屏 1080x1920、方形 1080x1080 @ 24fps
- **硬件检测** —— 自动检测核心数 / 内存，设定质量档。见 `references/optimization.md`
- **段落** —— 把时间戳映射到 scene 函数，各自带独立的效果 / 调色板 / 配色 / shader 配置
- **输出格式** —— MP4（默认）、GIF（640x360 @ 15fps）、PNG 序列

### 第 3 步：编写脚本

单个 Python 文件。组件（附参考）：

1. **硬件检测 + 质量档** —— `references/optimization.md`
2. **输入加载器** —— 取决于模式。`references/inputs.md`
3. **特征分析器** —— 音频 FFT、视频亮度，或合成
4. **网格 + 渲染器** —— 带位图缓存的多密度网格。`references/architecture.md`
5. **字符调色板** —— 每项目多个。`references/architecture.md` § Palettes
6. **配色系统** —— HSV + 离散 RGB + 调和生成。`references/architecture.md` § Color
7. **scene 函数** —— 各自返回 `canvas (uint8 H,W,3)`。`references/scenes.md`
8. **Tonemap** —— 自适应亮度归一化。`references/composition.md`
9. **Shader 流水线** —— `ShaderChain` + `FeedbackBuffer`。`references/shaders.md`
10. **scene 表 + 调度器** —— 时间 → scene 函数 + 配置。`references/scenes.md`
11. **并行编码器** —— N-worker 片段渲染，配合 ffmpeg 管道
12. **Main** —— 编排整条流水线

### 第 4 步：质量验证

- **先测单帧**：完整渲染前，在关键时间戳渲染单帧
- **亮度检查**：所有 ASCII 内容 `canvas.mean() > 8`。若偏暗，调低 gamma
- **视觉一致性**：所有场景是否像属于同一段视频？
- **创作构想检查**：输出是否契合第 1 步的概念？若看起来平庸，回到上一步

## 关键实现要点

### 亮度 —— 用 `tonemap()`，而非线性乘数

这是头号视觉问题。黑底 ASCII 天然偏暗。**绝不用 `canvas * N` 乘数**——它们会削平高光。改用自适应 tonemap：

```python
def tonemap(canvas, gamma=0.75):
    f = canvas.astype(np.float32)
    lo, hi = np.percentile(f[::4, ::4], [1, 99.5])
    if hi - lo < 10: hi = lo + 10
    f = np.clip((f - lo) / (hi - lo), 0, 1) ** gamma
    return (f * 255).astype(np.uint8)
```

流水线：`scene_fn() → tonemap() → FeedbackBuffer → ShaderChain → ffmpeg`

逐场景 gamma：默认 0.75、solarize 0.55、posterize 0.50、明亮场景 0.85。深色图层用 `screen` 混合（而非 `overlay`）。

### 字体单元格高度

macOS 上的 Pillow：`textbbox()` 返回的高度不对。改用 `font.getmetrics()`：`cell_height = ascent + descent`。见 `references/troubleshooting.md`。

### ffmpeg 管道死锁

长时间运行的 ffmpeg 绝不要用 `stderr=subprocess.PIPE`——缓冲区在 64KB 时填满并死锁。重定向到文件。见 `references/troubleshooting.md`。

### 字体兼容性

并非所有 Unicode 字符都能在所用字体中渲染。初始化时校验调色板——渲染每个字符，检查是否输出空白。见 `references/troubleshooting.md`。

### 按片段架构

对分段视频（引文、场景、章节），每段渲染为独立片段文件，便于并行渲染与选择性重渲染。见 `references/scenes.md`。

## 性能目标

| 组件 | 预算 |
|-----------|--------|
| 特征提取 | 1-5ms |
| 效果函数 | 2-15ms |
| 字符渲染 | 80-150ms（瓶颈） |
| Shader 流水线 | 5-25ms |
| **总计** | ~100-200ms/帧 |

## 参考文档

| 文件 | 内容 |
|------|----------|
| `references/architecture.md` | 网格系统、分辨率预设、字体选择、字符调色板（20+）、配色系统（HSV + OKLAB + 离散 RGB + 调和生成）、`_render_vf()` 辅助函数、GridLayer 类 |
| `references/composition.md` | 像素混合模式（20 种）、`blend_canvas()`、多网格构图、自适应 `tonemap()`、`FeedbackBuffer`、`PixelBlendStack`、遮罩 / 模板系统 |
| `references/effects.md` | 效果积木块：值场生成器、色相场、noise/fBM/domain warp、voronoi、反应扩散、元胞自动机、SDF、奇异吸引子、粒子系统、坐标变换、时间一致性 |
| `references/shaders.md` | `ShaderChain`、`_apply_shader_step()` 分发、38 个 shader 目录、音频反应式缩放、转场、色调预设、输出格式编码、终端渲染 |
| `references/scenes.md` | scene 协议、`Renderer` 类、`SCENES` 表、`render_clip()`、节拍同步剪辑、并行渲染、设计模式（图层层级、方向弧线、视觉隐喻、构图技法）、各复杂度级别的完整 scene 示例、scene 设计清单 |
| `references/inputs.md` | 音频分析（FFT、频段、节拍）、视频采样、图片转换、文本 / 歌词、TTS 集成（ElevenLabs、声音分配、音频混音） |
| `references/optimization.md` | 硬件检测、质量档、向量化模式、并行渲染、内存管理、性能预算 |
| `references/troubleshooting.md` | NumPy 广播陷阱、混合模式坑、多进程 / 序列化、亮度诊断、ffmpeg 问题、字体问题、常见错误 |

---

## 创作发散（仅在用户要求实验性 / 创意 / 独特输出时使用）

若用户要求创意、实验、出人意料或不循常规的输出，选择最契合的策略。并在生成代码*之前*推演其步骤。

- **强制关联（Forced Connections）** —— 当用户想要跨领域灵感（「让它看起来有机」「工业美学」）
- **概念融合（Conceptual Blending）** —— 当用户点名两个事物来结合（「海洋遇上音乐」「太空 + 书法」）
- **斜向策略（Oblique Strategies）** —— 当用户极度开放（「给我惊喜」「我没见过的东西」）

### 强制关联
1. 选一个与视觉目标无关的领域（天气系统、微生物学、建筑、流体力学、纺织编织）
2. 列出其核心视觉 / 结构元素（侵蚀 → 逐步显露。有丝分裂 → 分裂复制。编织 → 互锁图案）
3. 把这些元素映射到 ASCII 字符与动画模式上
4. 综合——「侵蚀」或「结晶」在字符网格里长什么样？

### 概念融合
1. 说出两个不同的视觉 / 概念空间（例如海浪 + 乐谱）
2. 建立对应（波峰 = 高音，波谷 = 休止，浪花 = 断奏）
3. 有选择地融合——保留最有趣的映射，丢弃牵强的
4. 发展只在融合中才存在的涌现特性

### 斜向策略
1. 抽一条：「把错误奉为隐藏的意图」/「用一个旧点子」/「你最亲近的朋友会怎么做？」/「强调缺陷」/「把它倒过来」/「只要局部，不要整体」/「反转」
2. 结合当前的 ASCII 动画挑战解读这条指令
3. 写代码之前，把这条横向洞见应用到视觉设计上
