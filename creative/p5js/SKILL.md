---
name: p5js
description: "用 p5.js 写生成艺术时使用。只要要做草图、shader 或交互 demo，就主动加载，即使用户只说「画个东西」。覆盖 2D/3D、粒子、噪声、WebGL、音频反应与导出。"
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative-coding, generative-art, p5js, canvas, interactive, visualization, webgl, shaders, animation]
    related_skills: [ascii-video, manim-video, excalidraw]
---

# p5.js 制作流水线

## 何时使用

当用户要求：p5.js 草图、创意编程、生成艺术、交互可视化、canvas 动画、浏览器视觉艺术、数据可视化、shader 效果。或任何 p5.js 项目时使用。

## 内容概览

使用 p5.js 的交互与生成视觉艺术制作流水线。制作基于浏览器的草图、生成艺术、数据可视化、交互体验、3D 场景、音频反应视觉与动态图形。可导出为 HTML、PNG、GIF、MP4 或 SVG。涵盖：2D/3D 渲染、噪声与粒子系统、流场、shader（GLSL）、像素操作、动态排版、WebGL 场景、音频分析、鼠标 / 键盘交互。以及无头高分辨率导出。

## 创作标准

这是在浏览器中渲染的视觉艺术。canvas 是媒介。算法是画笔。

**在写下第一行代码之前**，先明确创作概念。这件作品传达什么？是什么让观者停下滚动？是什么让它区别于一个代码教程示例？用户的提示词只是起点——要以创作野心去诠释。

**首次渲染即达到优秀，不可妥协。** 输出必须一加载就视觉惊艳。若看起来像 p5.js 教程练习、默认配置，或「AI 生成的创意编程」，那就是错的。交付前重新思考。

**超越参考词库。** 参考文档里的噪声函数、粒子系统、调色板与 shader 效果只是起始词库。每个项目都要组合、分层、发明。目录是颜料盒——画由你来画。

**主动发挥创造力。** 若用户要「一个粒子系统」，就交付一个带涌现集群行为、拖尾幽影回响、调色板偏移的深度雾。以及会呼吸的背景噪声场的粒子系统。至少包含一个用户没要求但会欣赏的视觉细节。

**密集、分层、考究。** 每一帧都应值得观看。绝不用纯白平面背景。始终有构图层级。始终有意的配色。始终有只在不经意细看时才显现的微细节。

**整体美学优先于功能数量。** 所有元素必须服务于统一的视觉语言——共享的色温、一致的描边粗细词汇、和谐的运动速度。一个有十个互不相关效果的草图，比有三个彼此契合的效果更糟。

## 模式

| 模式 | 输入 | 输出 | 参考 |
|------|-------|--------|-----------|
| **生成艺术** | 种子 / 参数 | 程序化视觉构图（静态或动画） | `references/visual-effects.md` |
| **数据可视化** | 数据集 / API | 交互式图表、图、自定义数据展示 | `references/interaction.md` |
| **交互体验** | 无（由用户驱动） | 鼠标 / 键盘 / 触摸驱动的草图 | `references/interaction.md` |
| **动画 / 动态图形** | 时间线 / 分镜 | 定时序列、动态排版、转场 | `references/animation.md` |
| **3D 场景** | 概念描述 | WebGL 几何、光照、相机、材质 | `references/webgl-and-3d.md` |
| **图像处理** | 图像文件 | 像素操作、滤镜、马赛克、点彩 | `references/visual-effects.md` § Pixel Manipulation |
| **音频反应** | 音频文件 / 麦克风 | 声音驱动的生成视觉 | `references/interaction.md` § Audio Input |

## 技术栈

每个项目一个自包含的 HTML 文件。无需构建步骤。

| 层 | 工具 | 用途 |
|-------|------|---------|
| 核心 | p5.js 1.11.3 (CDN) | canvas 渲染、数学、变换、事件处理 |
| 3D | p5.js WebGL mode | 3D 几何、相机、光照、GLSL shader |
| 音频 | p5.sound.js (CDN) | FFT 分析、振幅、麦克风输入、振荡器 |
| 导出 | 内置 `saveCanvas()` / `saveGif()` / `saveFrames()` | PNG、GIF、帧序列输出 |
| 捕获 | CCapture.js（可选） | 确定性帧率视频捕获（WebM、GIF） |
| 无头 | Puppeteer + Node.js（可选） | 自动化高分辨率渲染，经 ffmpeg 输出 MP4 |
| SVG | p5.js-svg 1.6.0（可选） | 用于印刷的矢量输出——需要 p5.js 1.x |
| 自然媒介 | p5.brush（可选） | 水彩、炭笔、钢笔——需要 p5.js 2.x + WEBGL |
| 纹理 | p5.grain（可选） | 胶片颗粒、纹理叠加 |
| 字体 | Google Fonts / `loadFont()` | 通过 OTF/TTF/WOFF2 使用自定义字体 |

### 版本说明

**p5.js 1.x**（1.11.3）是默认版本——稳定、文档齐全、库兼容性最广。除非项目需要 2.x 特性，否则用它。

**p5.js 2.x**（2.2+）新增：取代 `preload()` 的 `async setup()`、OKLCH/OKLAB 颜色模式、`splineVertex()`、shader `.modify()` API、可变字体、`textToContours()`、pointer 事件。使用 p5.brush 必需。见 `references/core-api.md` § p5.js 2.0。

## 流水线

每个项目都走同一条 6 阶段路径：

```
CONCEPT → DESIGN → CODE → PREVIEW → EXPORT → VERIFY
```

1. **CONCEPT** —— 明确创作构想：情绪、色彩世界、运动词汇、让它独一无二之处
2. **DESIGN** —— 选择模式、画布尺寸、交互模型、配色系统、导出格式。把概念映射到技术决策
3. **CODE** —— 写单个 HTML 文件，内联 p5.js。结构：全局变量 → `preload()` → `setup()` → `draw()` → 辅助函数 → 类 → 事件处理器
4. **PREVIEW** —— 在浏览器中打开，校验视觉质量。在目标分辨率下测试。检查性能
5. **EXPORT** —— 捕获输出：PNG 用 `saveCanvas()`，GIF 用 `saveGif()`，MP4 用 `saveFrames()` + ffmpeg，无头批量用 Puppeteer
6. **VERIFY** —— 输出是否契合概念？在目标展示尺寸下是否视觉惊艳？你会把它裱起来吗？

## 创作方向

### 美学维度

| 维度 | 选项 | 参考 |
|-----------|---------|-----------|
| **配色系统** | HSB/HSL、RGB、命名调色板、程序化调和、渐变插值 | `references/color-systems.md` |
| **噪声词汇** | Perlin 噪声、simplex、分形（多倍频）、domain warping、curl 噪声 | `references/visual-effects.md` § Noise |
| **粒子系统** | 基于物理、集群、拖尾、吸引子驱动、流场跟随 | `references/visual-effects.md` § Particles |
| **形状语言** | 几何图元、自定义顶点、贝塞尔曲线、SVG 路径 | `references/shapes-and-geometry.md` |
| **运动风格** | 缓动、弹簧、噪声驱动、物理模拟、lerp、阶梯 | `references/animation.md` |
| **排版** | 系统字体、加载的 OTF、`textToPoints()` 粒子文字、动态 | `references/typography.md` |
| **Shader 效果** | GLSL fragment/vertex、filter shader、后处理、反馈循环 | `references/webgl-and-3d.md` § Shaders |
| **构图** | 网格、放射、黄金比例、三分法、有机散布、平铺 | `references/core-api.md` § Composition |
| **交互模型** | 鼠标跟随、点击生成、拖拽、键盘状态、滚动驱动、麦克风输入 | `references/interaction.md` |
| **混合模式** | `BLEND`, `ADD`, `MULTIPLY`, `SCREEN`, `DIFFERENCE`, `EXCLUSION`, `OVERLAY` | `references/color-systems.md` § Blend Modes |
| **分层** | `createGraphics()` 离屏缓冲、alpha 合成、遮罩 | `references/core-api.md` § Offscreen Buffers |
| **纹理** | Perlin 表面、点绘、排线、半色调、像素排序 | `references/visual-effects.md` § Texture Generation |

### 逐项目变化规则

绝不用默认配置。对每个项目：
- **自定义调色板**——绝不用裸 `fill(255, 0, 0)`。始终用一个设计过的、含 3-7 种颜色的调色板
- **自定义描边粗细词汇**——细强调（0.5）、中等结构（1-2）、粗强调（3-5）
- **背景处理**——绝不用朴素的 `background(0)` 或 `background(255)`。始终有纹理、渐变或分层
- **运动多样性**——不同元素不同速度。主要的 1x，次要的 0.3x，氛围的 0.1x
- **至少一个自创元素**——自定义粒子行为、新颖的噪声应用、独特的交互响应

### 项目专属发明

每个项目至少发明以下之一：
- 匹配情绪的自定义调色板（非预设）
- 新颖的噪声场组合（例如 curl 噪声 + domain warp + 反馈）
- 独特的粒子行为（自定义力、自定义拖尾、自定义生成）
- 用户没要求、但提升作品档次的交互机制
- 制造视觉层级的构图技法

### 参数设计哲学

参数应从算法中自然生长，而非来自通用菜单。问自己：「*这个*系统的哪些属性该可调？」

**好参数**揭示算法的性格：
- **数量**——多少粒子、分支、细胞（控制密度）
- **尺度**——噪声频率、元素大小、间距（控制纹理）
- **速率**——速度、增长率、衰减（控制能量）
- **阈值**——行为何时改变？（控制戏剧性）
- **比例**——占比、力之间的平衡（控制和谐）

**坏参数**是与算法无关的通用控件：
- 「color1」「color2」「size」——脱离上下文毫无意义
- 针对无关效果的开关
- 只改变外观、不改变行为的参数

每个参数都应改变算法*如何思考*，而不只是它*看起来如何*。改变噪声倍频的「turbulence」参数是好的。只改变 `ellipse()` 半径的「particle size」滑块则很肤浅。

## 工作流

### 第 1 步：创作构想

写任何代码之前，先明确：

- **情绪 / 氛围**：观者该有什么感受？沉思？振奋？不安？俏皮？
- **视觉故事**：随时间（或交互时）发生什么？积累？衰减？蜕变？振荡？
- **色彩世界**：暖 / 冷？单色？互补？主色调是什么？强调色呢？
- **形状语言**：有机曲线？锐利几何？圆点？线条？混合？
- **运动词汇**：缓慢漂移？爆发性迸发？呼吸般的脉动？机械般精确？
- **让它独一无二之处**：让这个草图与众不同的那一点是什么？

把用户的提示词映射到美学选择。「放松的生成艺术背景」与「故障数据可视化」所需的一切都不同。

### 第 2 步：技术设计

- **模式** —— 上表 7 种中的哪一种
- **画布尺寸** —— 横屏 1920x1080、竖屏 1080x1920、方形 1080x1080，或响应式 `windowWidth/windowHeight`
- **渲染器** —— `P2D`（默认）或 `WEBGL`（用于 3D、shader、高级混合模式）
- **帧率** —— 60fps（交互）、30fps（氛围动画），或 `noLoop()`（静态生成）
- **导出目标** —— 浏览器展示、PNG 静帧、GIF 循环、MP4 视频、SVG 矢量
- **交互模型** —— 被动（无输入）、鼠标驱动、键盘驱动、音频反应、滚动驱动
- **查看器 UI** —— 对交互式生成艺术，从 `templates/viewer.html` 起步，它提供种子导航、参数滑块与下载。对简单草图或视频导出，用裸 HTML

### 第 3 步：编写草图

对**交互式生成艺术**（种子探索、参数调优）：从 `templates/viewer.html` 起步。先读模板，保留固定部分（种子导航、操作），替换算法与参数控件。这样用户就得到种子 prev/next/random/jump、实时更新的参数滑块，以及 PNG 下载——全部已接好。

对**动画、视频导出或简单草图**：用裸 HTML：

单个 HTML 文件。结构：

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Project Name</title>
  <script>p5.disableFriendlyErrors = true;</script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.11.3/p5.min.js"></script>
  <!-- <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.11.3/addons/p5.sound.min.js"></script> -->
  <!-- <script src="https://unpkg.com/p5.js-svg@1.6.0"></script> -->  <!-- SVG export -->
  <!-- <script src="https://cdn.jsdelivr.net/npm/ccapture.js-npmfixed/build/CCapture.all.min.js"></script> -->  <!-- video capture -->
  <style>
    html, body { margin: 0; padding: 0; overflow: hidden; }
    canvas { display: block; }
  </style>
</head>
<body>
<script>
// === Configuration ===
const CONFIG = {
  seed: 42,
  // ... project-specific params
};

// === Color Palette ===
const PALETTE = {
  bg: '#0a0a0f',
  primary: '#e8d5b7',
  // ...
};

// === Global State ===
let particles = [];

// === Preload (fonts, images, data) ===
function preload() {
  // font = loadFont('...');
}

// === Setup ===
function setup() {
  createCanvas(1920, 1080);
  randomSeed(CONFIG.seed);
  noiseSeed(CONFIG.seed);
  colorMode(HSB, 360, 100, 100, 100);
  // Initialize state...
}

// === Draw Loop ===
function draw() {
  // Render frame...
}

// === Helper Functions ===
// ...

// === Classes ===
class Particle {
  // ...
}

// === Event Handlers ===
function mousePressed() { /* ... */ }
function keyPressed() { /* ... */ }
function windowResized() { resizeCanvas(windowWidth, windowHeight); }
</script>
</body>
</html>
```

关键实现模式：
- **种子随机性**：始终用 `randomSeed()` + `noiseSeed()` 保证可复现
- **颜色模式**：用 `colorMode(HSB, 360, 100, 100, 100)` 获得直观的颜色控制
- **状态分离**：CONFIG 存参数、PALETTE 存颜色、全局变量存可变状态
- **基于类的实体**：粒子、agent、形状作为类，带 `update()` + `display()` 方法
- **离屏缓冲**：用 `createGraphics()` 做分层构图、拖尾、遮罩

### 第 4 步：预览与迭代

- 直接在浏览器中打开 HTML 文件——基础草图无需服务器
- 从本地文件 `loadImage()`/`loadFont()` 时：用 `scripts/serve.sh` 或 `python3 -m http.server`
- 用 Chrome DevTools 的 Performance 标签验证 60fps
- 在目标导出分辨率下测试，而不只是窗口尺寸
- 调参数直到视觉效果契合第 1 步的概念

### 第 5 步：导出

| 格式 | 方法 | 命令 |
|--------|--------|---------|
| **PNG** | 在 `keyPressed()` 中用 `saveCanvas('output', 'png')` | 按 's' 保存 |
| **高分辨率 PNG** | Puppeteer 无头捕获 | `node scripts/export-frames.js sketch.html --width 3840 --height 2160 --frames 1` |
| **GIF** | `saveGif('output', 5)` —— 捕获 N 秒 | 按 'g' 保存 |
| **帧序列** | `saveFrames('frame', 'png', 10, 30)` —— 30fps 下 10s | 然后 `ffmpeg -i frame-%04d.png -c:v libx264 output.mp4` |
| **MP4** | Puppeteer 帧捕获 + ffmpeg | `bash scripts/render.sh sketch.html output.mp4 --duration 30 --fps 30` |
| **SVG** | 配合 p5.js-svg 用 `createCanvas(w, h, SVG)` | `save('output.svg')` |

### 第 6 步：质量验证

- **是否契合构想？** 把输出与创作概念对照。若看起来平庸，回到第 1 步
- **分辨率检查**：在目标展示尺寸下是否锐利？没有锯齿伪影？
- **性能检查**：在浏览器中能否保持 60fps？（动画最低 30fps）
- **颜色检查**：各颜色搭配是否和谐？在亮色与暗色显示器上都测一遍
- **边界情况**：画布边缘会怎样？窗口变化时？运行 10 分钟后？

## 关键实现要点

### 性能——先禁用 FES

Friendly Error System（FES）会增加最多 10 倍开销。每个生产草图都要禁用它：

```javascript
p5.disableFriendlyErrors = true;  // BEFORE setup()

function setup() {
  pixelDensity(1);  // prevent 2x-4x overdraw on retina
  createCanvas(1920, 1080);
}
```

在热点循环（粒子、像素操作）中，用 `Math.*` 而非 p5 包装函数——实测更快：

```javascript
// In draw() or update() hot paths:
let a = Math.sin(t);          // not sin(t)
let r = Math.sqrt(dx*dx+dy*dy); // not dist() — or better: skip sqrt, compare magSq
let v = Math.random();        // not random() — when seed not needed
let m = Math.min(a, b);       // not min(a, b)
```

绝不在 `draw()` 里 `console.log()`。绝不在 `draw()` 里操作 DOM。见 `references/troubleshooting.md` § Performance。

### 种子随机性——始终

每个生成艺术草图都必须可复现。相同种子，相同输出。

```javascript
function setup() {
  randomSeed(CONFIG.seed);
  noiseSeed(CONFIG.seed);
  // All random() and noise() calls now deterministic
}
```

生成内容绝不用 `Math.random()`——只用于性能关键的非视觉代码。视觉元素始终用 `random()`。若需要随机种子：`CONFIG.seed = floor(random(99999))`。

### 生成艺术平台支持（fxhash / Art Blocks）

对生成艺术平台，把 p5 的 PRNG 换成平台的确定性随机：

```javascript
// fxhash convention
const SEED = $fx.hash;              // unique per mint
const rng = $fx.rand;               // deterministic PRNG
$fx.features({ palette: 'warm', complexity: 'high' });

// In setup():
randomSeed(SEED);   // for p5's noise()
noiseSeed(SEED);

// Replace random() with rng() for platform determinism
let x = rng() * width;  // instead of random(width)
```

见 `references/export-pipeline.md` § Platform Export。

### 颜色模式——用 HSB

对生成艺术而言，HSB（色相、饱和度、明度）比 RGB 好操作得多：

```javascript
colorMode(HSB, 360, 100, 100, 100);
// Now: fill(hue, sat, bri, alpha)
// Rotate hue: fill((baseHue + offset) % 360, 80, 90)
// Desaturate: fill(hue, sat * 0.3, bri)
// Darken: fill(hue, sat, bri * 0.5)
```

绝不硬编码裸 RGB 值。定义调色板对象，程序化派生变化。见 `references/color-systems.md`。

### 噪声——多倍频，而非原始

原始 `noise(x, y)` 看起来像平滑的团块。叠加倍频以获得自然纹理：

```javascript
function fbm(x, y, octaves = 4) {
  let val = 0, amp = 1, freq = 1, sum = 0;
  for (let i = 0; i < octaves; i++) {
    val += noise(x * freq, y * freq) * amp;
    sum += amp;
    amp *= 0.5;
    freq *= 2;
  }
  return val / sum;
}
```

对流动的有机形态，用 **domain warping**：把噪声输出回喂为噪声输入坐标。见 `references/visual-effects.md`。

### 用 createGraphics() 做分层——不是可选项

单遍平铺渲染看起来很平。用离屏缓冲做构图：

```javascript
let bgLayer, fgLayer, trailLayer;
function setup() {
  createCanvas(1920, 1080);
  bgLayer = createGraphics(width, height);
  fgLayer = createGraphics(width, height);
  trailLayer = createGraphics(width, height);
}
function draw() {
  renderBackground(bgLayer);
  renderTrails(trailLayer);   // persistent, fading
  renderForeground(fgLayer);  // cleared each frame
  image(bgLayer, 0, 0);
  image(trailLayer, 0, 0);
  image(fgLayer, 0, 0);
}
```

### 性能——尽可能向量化

p5.js 的 draw 调用很贵。面对成千上万的粒子：

```javascript
// SLOW: individual shapes
for (let p of particles) {
  ellipse(p.x, p.y, p.size);
}

// FAST: single shape with beginShape()
beginShape(POINTS);
for (let p of particles) {
  vertex(p.x, p.y);
}
endShape();

// FASTEST: pixel buffer for massive counts
loadPixels();
for (let p of particles) {
  let idx = 4 * (floor(p.y) * width + floor(p.x));
  pixels[idx] = r; pixels[idx+1] = g; pixels[idx+2] = b; pixels[idx+3] = 255;
}
updatePixels();
```

见 `references/troubleshooting.md` § Performance。

### 多草图的 Instance 模式

全局模式会污染 `window`。生产环境用 instance 模式：

```javascript
const sketch = (p) => {
  p.setup = function() {
    p.createCanvas(800, 800);
  };
  p.draw = function() {
    p.background(0);
    p.ellipse(p.mouseX, p.mouseY, 50);
  };
};
new p5(sketch, 'canvas-container');
```

在一个页面里嵌入多个草图或与框架集成时必需。

### WebGL 模式坑

- `createCanvas(w, h, WEBGL)`——原点是中心，不是左上角
- Y 轴是反的（WEBGL 中正 Y 向上，P2D 中向下）
- `translate(-width/2, -height/2)` 以获得类 P2D 坐标
- 每个变换周围都要 `push()`/`pop()`——矩阵栈会静默溢出
- `texture()` 要放在 `rect()`/`plane()` 之前——不是之后
- 自定义 shader：`createShader(vert, frag)`——在多个浏览器上测试

### 导出——按键绑定约定

每个草图都应在 `keyPressed()` 中包含这些：

```javascript
function keyPressed() {
  if (key === 's' || key === 'S') saveCanvas('output', 'png');
  if (key === 'g' || key === 'G') saveGif('output', 5);
  if (key === 'r' || key === 'R') { randomSeed(millis()); noiseSeed(millis()); }
  if (key === ' ') CONFIG.paused = !CONFIG.paused;
}
```

### 无头视频导出——用 noLoop()

用 Puppeteer 做无头渲染时，草图**必须**在 setup 里用 `noLoop()`。否则，在截图很慢的同时 p5 的 draw 循环自由运行——草图跑得太快，就会产生跳帧 / 重复帧。

```javascript
function setup() {
  createCanvas(1920, 1080);
  pixelDensity(1);
  noLoop();                    // capture script controls frame advance
  window._p5Ready = true;      // signal readiness to capture script
}
```

自带的 `scripts/export-frames.js` 会检测 `_p5Ready`，每次捕获调用一次 `redraw()`，实现精确的 1:1 帧对应。见 `references/export-pipeline.md` § Deterministic Capture。

多场景视频用按片段架构：每个场景一个 HTML，独立渲染，用 `ffmpeg -f concat` 拼接。见 `references/export-pipeline.md` § Per-Clip Architecture。

### Agent 工作流

构建 p5.js 草图时：

1. **写 HTML 文件**——单个自包含文件，所有代码内联
2. **在浏览器中打开**——`open sketch.html`（macOS）或 `xdg-open sketch.html`（Linux）
3. **本地资源**（字体、图片）需要服务器：在项目目录里 `python3 -m http.server 8080`，然后打开 `http://localhost:8080/sketch.html`
4. **导出 PNG/GIF**——按上文加 `keyPressed()` 快捷键，告诉用户按哪个键
5. **无头导出**——`node scripts/export-frames.js sketch.html --frames 300` 自动帧捕获（草图必须用 `noLoop()` + `_p5Ready`）
6. **MP4 渲染**——`bash scripts/render.sh sketch.html output.mp4 --duration 30`
7. **迭代打磨**——编辑 HTML 文件，用户刷新浏览器看变化
8. **按需加载参考**——实现过程中用 `skill_view(name="p5js", file_path="references/...")` 加载具体参考文件

## 性能目标

| 指标 | 目标 |
|--------|--------|
| 帧率（交互） | 持续 60fps |
| 帧率（动画导出） | 最低 30fps |
| 粒子数（P2D 形状） | 60fps 下 5,000-10,000 |
| 粒子数（像素缓冲） | 60fps 下 50,000-100,000 |
| 画布分辨率 | 最高 3840x2160（导出）、1920x1080（交互） |
| 文件大小（HTML） | < 100KB（不含 CDN 库） |
| 加载时间 | < 2s 首帧 |

## 参考文档

| 文件 | 内容 |
|------|----------|
| `references/core-api.md` | canvas 设置、坐标系、draw 循环、`push()`/`pop()`、离屏缓冲、构图模式、`pixelDensity()`、响应式设计 |
| `references/shapes-and-geometry.md` | 2D 图元、`beginShape()`/`endShape()`、Bezier/Catmull-Rom 曲线、`vertex()` 系统、自定义形状、`p5.Vector`、有符号距离场、SVG 路径转换 |
| `references/visual-effects.md` | 噪声（Perlin、分形、domain warp、curl）、流场、粒子系统（物理、集群、拖尾）、像素操作、纹理生成（点绘、排线、半色调）、反馈循环、反应扩散 |
| `references/animation.md` | 基于帧的动画、缓动函数、`lerp()`/`map()`、弹簧物理、状态机、时间线排序、基于 `millis()` 的计时、转场模式 |
| `references/typography.md` | `text()`、`loadFont()`、`textToPoints()`、动态排版、文字遮罩、字体度量、响应式文字尺寸 |
| `references/color-systems.md` | `colorMode()`、HSB/HSL/RGB、`lerpColor()`、`paletteLerp()`、程序化调色板、色彩调和、`blendMode()`、渐变渲染、精选调色板库 |
| `references/webgl-and-3d.md` | WEBGL 渲染器、3D 图元、相机、光照、材质、自定义几何、GLSL shader（`createShader()`、`createFilterShader()`）、帧缓冲、后处理 |
| `references/interaction.md` | 鼠标事件、键盘状态、触摸输入、DOM 元素、`createSlider()`/`createButton()`、音频输入（p5.sound FFT/振幅）、滚动驱动动画、响应式事件 |
| `references/export-pipeline.md` | `saveCanvas()`、`saveGif()`、`saveFrames()`、确定性无头捕获、ffmpeg 帧转视频、CCapture.js、SVG 导出、按片段架构、平台导出（fxhash）、视频坑 |
| `references/troubleshooting.md` | 性能剖析、逐像素预算、常见错误、浏览器兼容性、WebGL 调试、字体加载问题、像素密度陷阱、内存泄漏、CORS |
| `templates/viewer.html` | 交互式查看器模板：种子导航（prev/next/random/jump）、参数滑块、下载 PNG、响应式画布。可探索的生成艺术从这里起步 |

---

## 创作发散（仅在用户要求实验性 / 创意 / 独特输出时使用）

若用户要求创意、实验、出人意料或不循常规的输出，选择最契合的策略。并在生成代码*之前*推演其步骤。

- **概念融合（Conceptual Blending）** —— 当用户点名两个事物来结合，或想要混合美学
- **SCAMPER** —— 当用户想对某个已知生成艺术模式来点变化
- **距离联想（Distance Association）** —— 当用户给出单个概念并想探索（「做点关于时间的东西」）

### 概念融合
1. 说出两个不同的视觉系统（例如粒子物理 + 手写）
2. 建立对应（粒子 = 墨滴，力 = 笔压，场 = 字形）
3. 有选择地融合——保留能产生有趣涌现视觉的映射
4. 把这个融合写成统一系统，而非两个系统并排

### SCAMPER 变换
拿一个已知生成模式（流场、粒子系统、L-system、元胞自动机）并系统地改造它：
- **Substitute（替换）**：把圆换成文字字符，把线换成渐变
- **Combine（组合）**：融合两个模式（流场 + voronoi）
- **Adapt（适配）**：把 2D 模式应用到 3D 投影
- **Modify（修改）**：夸大尺度，扭曲坐标空间
- **Purpose（换用途）**：用物理模拟做排版，用排序算法做颜色
- **Eliminate（消除）**：去掉网格、去掉颜色、去掉对称
- **Reverse（反转）**：反向运行模拟，反转参数空间

### 距离联想
1. 锚定在用户的概念上（例如「孤独」）
2. 在三种距离上生成联想：
   - 近（显而易见）：空房间、单独的身影、寂静
   - 中（有趣）：鱼群里逆游的一条鱼、没有通知的手机、地铁车厢之间的缝隙
   - 远（抽象）：质数、渐近曲线、凌晨 3 点的颜色
3. 发展中距离联想——它们足够具体可可视化，又足够出人意料而有趣
