---
name: ascii-art
description: "生成 ASCII art 时使用。只要要做文字横幅、cowsay 气泡、装饰边框或图片转 ASCII，就主动加载，即使用户只说「搞个 ASCII 图」。覆盖 pyfiglet、cowsay、boxes、image-to-ascii 与在线 API。"
version: 4.0.0
author: 0xbyt4, Hermes Agent
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ASCII, Art, Banners, Creative, Unicode, Text-Art, pyfiglet, figlet, cowsay, boxes]
    related_skills: [excalidraw]

---

# ASCII Art Skill

针对不同 ASCII art 需求的多个工具。所有工具都是本地 CLI 程序或免费 REST API——无需 API key。

## 工具 1：文本横幅（pyfiglet — 本地）

把文本渲染成大型 ASCII art 横幅。内置 571 种字体。

### 安装

```bash
pip install pyfiglet --break-system-packages -q
```

### Usage

```bash
python3 -m pyfiglet "YOUR TEXT" -f slant
python3 -m pyfiglet "TEXT" -f doom -w 80    # Set width
python3 -m pyfiglet --list_fonts             # List all 571 fonts
```

### 推荐字体

| 风格 | 字体 | 适合 |
|-------|------|----------|
| 简洁现代 | `slant` | 项目名、标题 |
| 粗壮块状 | `doom` | 标题、logo |
| 大而清晰 | `big` | 横幅 |
| 经典横幅 | `banner3` | 宽幅展示 |
| 紧凑 | `small` | 副标题 |
| 赛博朋克 | `cyberlarge` | 科技主题 |
| 3D 效果 | `3-d` | 启动页 |
| 哥特 | `gothic` | 戏剧化文本 |

### 技巧

- 预览 2-3 种字体，让用户挑最喜欢的
- 短文本（1-8 字符）最适合 `doom` 或 `block` 这类细节丰富的字体
- 长文本更适合 `small` 或 `mini` 这类紧凑字体

## 工具 2：文本横幅（asciified API — 远程，免安装）

免费 REST API，把文本转成 ASCII art。250+ 种 FIGlet 字体。直接返回纯文本——无需解析。在未安装 pyfiglet 时使用，或作为快捷替代方案。

### 用法（通过 terminal curl）

```bash
# Basic text banner (default font)
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello+World"

# With a specific font
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Slant"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Doom"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Star+Wars"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=3-D"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Banner3"

# List all available fonts (returns JSON array)
curl -s "https://asciified.thelicato.io/api/v2/fonts"
```

### 技巧

- 在 text 参数中把空格 URL 编码为 `+`
- 响应就是纯文本 ASCII art——没有 JSON 包裹，可直接展示
- 字体名区分大小写。用 fonts 端点获取确切名称
- 任何带 curl 的终端都能用——无需 Python 或 pip

## 工具 3：Cowsay（消息艺术）

经典工具，把文本包进带 ASCII 角色的对话气泡中。

### 安装

```bash
sudo apt install cowsay -y    # Debian/Ubuntu
# brew install cowsay         # macOS
```

### Usage

```bash
cowsay "Hello World"
cowsay -f tux "Linux rules"       # Tux the penguin
cowsay -f dragon "Rawr!"          # Dragon
cowsay -f stegosaurus "Roar!"     # Stegosaurus
cowthink "Hmm..."                  # Thought bubble
cowsay -l                          # List all characters
```

### 可用角色（50+）

`beavis.zen`, `bong`, `bunny`, `cheese`, `daemon`, `default`, `dragon`,
`dragon-and-cow`, `elephant`, `eyes`, `flaming-skull`, `ghostbusters`,
`hellokitty`, `kiss`, `kitty`, `koala`, `luke-koala`, `mech-and-cow`,
`meow`, `moofasa`, `moose`, `ren`, `sheep`, `skeleton`, `small`,
`stegosaurus`, `stimpy`, `supermilker`, `surgery`, `three-eyes`,
`turkey`, `turtle`, `tux`, `udder`, `vader`, `vader-koala`, `www`

### 眼睛 / 舌头修饰符

```bash
cowsay -b "Borg"       # =_= eyes
cowsay -d "Dead"       # x_x eyes
cowsay -g "Greedy"     # $_$ eyes
cowsay -p "Paranoid"   # @_@ eyes
cowsay -s "Stoned"     # *_* eyes
cowsay -w "Wired"      # O_O eyes
cowsay -e "OO" "Msg"   # Custom eyes
cowsay -T "U " "Msg"   # Custom tongue
```

## 工具 4：Boxes（装饰边框）

为任意文本绘制装饰性 ASCII art 边框 / 外框。内置 70+ 种样式。

### 安装

```bash
sudo apt install boxes -y    # Debian/Ubuntu
# brew install boxes         # macOS
```

### Usage

```bash
echo "Hello World" | boxes                    # Default box
echo "Hello World" | boxes -d stone           # Stone border
echo "Hello World" | boxes -d parchment       # Parchment scroll
echo "Hello World" | boxes -d cat             # Cat border
echo "Hello World" | boxes -d dog             # Dog border
echo "Hello World" | boxes -d unicornsay      # Unicorn
echo "Hello World" | boxes -d diamonds        # Diamond pattern
echo "Hello World" | boxes -d c-cmt           # C-style comment
echo "Hello World" | boxes -d html-cmt        # HTML comment
echo "Hello World" | boxes -a c               # Center text
boxes -l                                       # List all 70+ designs
```

### 与 pyfiglet 或 asciified 组合

```bash
python3 -m pyfiglet "HERMES" -f slant | boxes -d stone
# Or without pyfiglet installed:
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=HERMES&font=Slant" | boxes -d stone
```

## 工具 5：TOIlet（彩色文本艺术）

类似 pyfiglet，但带 ANSI 颜色效果与视觉滤镜。终端装点利器。

### 安装

```bash
sudo apt install toilet toilet-fonts -y    # Debian/Ubuntu
# brew install toilet                      # macOS
```

### Usage

```bash
toilet "Hello World"                    # Basic text art
toilet -f bigmono12 "Hello"            # Specific font
toilet --gay "Rainbow!"                 # Rainbow coloring
toilet --metal "Metal!"                 # Metallic effect
toilet -F border "Bordered"             # Add border
toilet -F border --gay "Fancy!"         # Combined effects
toilet -f pagga "Block"                 # Block-style font (unique to toilet)
toilet -F list                          # List available filters
```

### 滤镜

`crop`、`gay`（彩虹）、`metal`、`flip`、`flop`、`180`、`left`、`right`、`border`

**注意**：toilet 通过 ANSI 转义码输出颜色——在终端中有效。但并非所有场景都能渲染（例如纯文本文件、部分聊天平台）。

## 工具 6：图片转 ASCII Art

把图片（PNG、JPEG、GIF、WEBP）转成 ASCII art。

### 方案 A：ascii-image-converter（推荐，现代）

```bash
# Install
sudo snap install ascii-image-converter
# OR: go install github.com/TheZoraiz/ascii-image-converter@latest
```

```bash
ascii-image-converter image.png                  # Basic
ascii-image-converter image.png -C               # Color output
ascii-image-converter image.png -d 60,30         # Set dimensions
ascii-image-converter image.png -b               # Braille characters
ascii-image-converter image.png -n               # Negative/inverted
ascii-image-converter https://url/image.jpg      # Direct URL
ascii-image-converter image.png --save-txt out   # Save as text
```

### 方案 B：jp2a（轻量，仅 JPEG）

```bash
sudo apt install jp2a -y
jp2a --width=80 image.jpg
jp2a --colors image.jpg              # Colorized
```

## 工具 7：搜索现成 ASCII Art

从网上搜索精选 ASCII art。使用 `terminal` 配合 `curl`。

### 来源 A：ascii.co.uk（现成艺术推荐）

按主题归类的大量经典 ASCII art 合集。艺术内容位于 HTML 的 `<pre>` 标签内。用 curl 抓取页面，再用一小段 Python 提取艺术。

**URL 模式：** `https://ascii.co.uk/art/{subject}`

**第 1 步——抓取页面：**

```bash
curl -s 'https://ascii.co.uk/art/cat' -o /tmp/ascii_art.html
```

**第 2 步——从 pre 标签提取艺术：**

```python
import re, html
with open('/tmp/ascii_art.html') as f:
    text = f.read()
arts = re.findall(r'<pre[^>]*>(.*?)</pre>', text, re.DOTALL)
for art in arts:
    clean = re.sub(r'<[^>]+>', '', art)
    clean = html.unescape(clean).strip()
    if len(clean) > 30:
        print(clean)
        print('\n---\n')
```

**可用主题**（用作 URL 路径）：
- 动物：`cat`, `dog`, `horse`, `bird`, `fish`, `dragon`, `snake`, `rabbit`, `elephant`, `dolphin`, `butterfly`, `owl`, `wolf`, `bear`, `penguin`, `turtle`
- 物件：`car`, `ship`, `airplane`, `rocket`, `guitar`, `computer`, `coffee`, `beer`, `cake`, `house`, `castle`, `sword`, `crown`, `key`
- 自然：`tree`, `flower`, `sun`, `moon`, `star`, `mountain`, `ocean`, `rainbow`
- 角色：`skull`, `robot`, `angel`, `wizard`, `pirate`, `ninja`, `alien`
- 节日：`christmas`, `halloween`, `valentine`

**技巧：**
- 保留作者签名 / 缩写——这是重要礼仪
- 每页可能有多件作品——为用户挑最好的
- 通过 curl 稳定可用，无需 JavaScript

### 来源 B：GitHub Octocat API（趣味彩蛋）

返回随机的 GitHub Octocat 配上一句语录。无需认证。

```bash
curl -s https://api.github.com/octocat
```

## 工具 8：趣味 ASCII 小工具（通过 curl）

这些免费服务直接返回 ASCII art——适合当趣味附加。

### QR 码转 ASCII Art

```bash
curl -s "qrenco.de/Hello+World"
curl -s "qrenco.de/https://example.com"
```

### 天气转 ASCII Art

```bash
curl -s "wttr.in/London"          # Full weather report with ASCII graphics
curl -s "wttr.in/Moon"            # Moon phase in ASCII art
curl -s "v2.wttr.in/London"       # Detailed version
```

## 工具 9：LLM 生成自定义艺术（兜底）

当以上工具都没有所需内容时，直接用这些 Unicode 字符生成 ASCII art：

### 字符调色板

**Box Drawing:** `╔ ╗ ╚ ╝ ║ ═ ╠ ╣ ╦ ╩ ╬ ┌ ┐ └ ┘ │ ─ ├ ┤ ┬ ┴ ┼ ╭ ╮ ╰ ╯`

**Block Elements:** `░ ▒ ▓ █ ▄ ▀ ▌ ▐ ▖ ▗ ▘ ▝ ▚ ▞`

**Geometric & Symbols:** `◆ ◇ ◈ ● ○ ◉ ■ □ ▲ △ ▼ ▽ ★ ☆ ✦ ✧ ◀ ▶ ◁ ▷ ⬡ ⬢ ⌂`

### 规则

- 最大宽度：每行 60 字符（终端安全）
- 最大高度：横幅 15 行，场景 25 行
- 仅等宽：输出必须在固定宽度字体中正确渲染

## 决策流程

1. **把文本做成横幅** → 装了 pyfiglet 就用它，否则用 curl 调 asciified API
2. **把消息包进趣味角色艺术** → cowsay
3. **加装饰性边框 / 外框** → boxes（可与 pyfiglet/asciified 组合）
4. **某具体事物的艺术**（猫、火箭、龙） → curl 抓 ascii.co.uk + 解析
5. **图片转 ASCII** → ascii-image-converter 或 jp2a
6. **QR 码** → curl 调 qrenco.de
7. **天气 / 月亮艺术** → curl 调 wttr.in
8. **自定义 / 创意内容** → 用 Unicode 调色板由 LLM 生成
9. **任何未安装的工具** → 安装它，或回退到下一选项
