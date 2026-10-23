---
name: popular-web-designs
description: "生成模仿知名网站的 HTML/CSS 时使用。只要要做像 Stripe、Linear、Vercel 等真实产品那种风格的页面、落地页或仪表盘，就主动加载。即使用户只说「做个网页」。收录 54 套真实 design system。"
version: 1.0.0
author: Hermes Agent + Teknium (design systems sourced from VoltAgent/awesome-design-md)
license: MIT
tags: [design, css, html, ui, web-development, design-systems, templates]
platforms: [linux, macos, windows]
triggers:
  - build a page that looks like
  - make it look like stripe
  - design like linear
  - vercel style
  - create a UI
  - web design
  - landing page
  - dashboard design
  - website styled like
---

# Popular Web Designs

54 套真实世界的 design system，供生成 HTML/CSS 时直接使用。每套模板完整捕捉某个站点的视觉语言：调色板、字体层级、组件样式、间距系统、阴影、响应式行为。以及带精确 CSS 取值的实用 agent prompt。

## 相关设计 skill

- **`claude-design`** —— 用于设计*过程与品味*（界定 brief、产出变体、验证本地 HTML 制品、避免 AI 设计套路）。当用户想要一个精心设计、风格仿照某知名品牌的页面时，与本 skill 搭配：`claude-design` 驱动工作流。本 skill 提供视觉词汇。
- **`design-md`** —— 当交付物是正式的 DESIGN.md token 规格文件、而非渲染好的制品时使用。

## 使用方法

1. 从下方目录中挑一套设计
2. 加载它：`skill_view(name="popular-web-designs", file_path="templates/<site>.md")`
3. 生成 HTML 时使用其中的 design token 与组件规格
4. 搭配 `generative-widgets` skill，通过 cloudflared 隧道提供结果

每套模板顶部都有一块 **Hermes Implementation Notes**，包含：
- CDN 字体替代与 Google Fonts `<link>` 标签（可直接粘贴）
- 主字体与等宽字体的 CSS font-family 栈
- 提醒用 `write_file` 创建 HTML、用 `browser_vision` 验证

## HTML 生成模式

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title</title>
  <!-- Paste the Google Fonts <link> from the template's Hermes notes -->
  <link href="https://fonts.googleapis.com/css2?family=..." rel="stylesheet">
  <style>
    /* Apply the template's color palette as CSS custom properties */
    :root {
      --color-bg: #ffffff;
      --color-text: #171717;
      --color-accent: #533afd;
      /* ... more from template Section 2 */
    }
    /* Apply typography from template Section 3 */
    body {
      font-family: 'Inter', system-ui, sans-serif;
      color: var(--color-text);
      background: var(--color-bg);
    }
    /* Apply component styles from template Section 4 */
    /* Apply layout from template Section 5 */
    /* Apply shadows from template Section 6 */
  </style>
</head>
<body>
  <!-- Build using component specs from the template -->
</body>
</html>
```

用 `write_file` 写文件，用 `generative-widgets` 工作流（cloudflared 隧道）提供服务，并用 `browser_vision` 验证结果，确认视觉准确。

## 字体替代参考

多数站点使用 CDN 上拿不到的专有字体。每套模板都映射到一个能保留设计特质的 Google Fonts 替代字体。常见映射：

| 专有字体 | CDN 替代 | 特质 |
|---|---|---|
| Geist / Geist Sans | Geist (on Google Fonts) | 几何感、字距压缩 |
| Geist Mono | Geist Mono (on Google Fonts) | 干净等宽、连字 |
| sohne-var (Stripe) | Source Sans 3 | 轻字重优雅 |
| Berkeley Mono | JetBrains Mono | 技术感等宽 |
| Airbnb Cereal VF | DM Sans | 圆润、友好的几何感 |
| Circular (Spotify) | DM Sans | 几何感、温暖 |
| figmaSans | Inter | 干净的人文主义 |
| Pin Sans (Pinterest) | DM Sans | 友好、圆润 |
| NVIDIA-EMEA | Inter (or Arial system) | 工业感、干净 |
| CoinbaseDisplay/Sans | DM Sans | 几何感、可信赖 |
| UberMove | DM Sans | 粗体、紧凑 |
| HashiCorp Sans | Inter | 企业感、中性 |
| waldenburgNormal (Sanity) | Space Grotesk | 几何感、略窄 |
| IBM Plex Sans/Mono | IBM Plex Sans/Mono | Google Fonts 上有 |
| Rubik (Sentry) | Rubik | Google Fonts 上有 |

当模板的 CDN 字体与原字体一致（Inter、IBM Plex、Rubik、Geist）时，无替代损失。当使用替代字体（Circular 用 DM Sans、sohne-var 用 Source Sans 3）时，严格遵循模板的字重、字号与字距取值。它们承载的视觉识别比具体字体本身更多。

## 设计目录

### AI 与机器学习

| 模板 | 站点 | 风格 |
|---|---|---|
| `claude.md` | Anthropic Claude | 暖陶土色强调、干净编辑风布局 |
| `cohere.md` | Cohere | 鲜艳渐变、数据丰富的仪表盘美学 |
| `elevenlabs.md` | ElevenLabs | 深色电影感 UI、音频波形美学 |
| `minimax.md` | Minimax | 大胆深色界面配霓虹强调 |
| `mistral.ai.md` | Mistral AI | 法式极简、紫色调 |
| `ollama.md` | Ollama | 终端优先、单色极简 |
| `opencode.ai.md` | OpenCode AI | 开发者中心的深色主题、全等宽 |
| `replicate.md` | Replicate | 干净白画布、代码优先 |
| `runwayml.md` | RunwayML | 电影感深色 UI、媒体丰富布局 |
| `together.ai.md` | Together AI | 技术感、蓝图风设计 |
| `voltagent.md` | VoltAgent | 虚空黑画布、祖母绿强调、终端原生 |
| `x.ai.md` | xAI | 冷峻单色、未来极简、全等宽 |

### 开发者工具与平台

| 模板 | 站点 | 风格 |
|---|---|---|
| `cursor.md` | Cursor | 利落深色界面、渐变强调 |
| `expo.md` | Expo | 深色主题、紧凑字距、代码中心 |
| `linear.app.md` | Linear | 极简深色模式、精确、紫色强调 |
| `lovable.md` | Lovable | 俏皮渐变、友好的开发者美学 |
| `mintlify.md` | Mintlify | 干净、绿色强调、阅读优化 |
| `posthog.md` | PostHog | 俏皮品牌、开发者友好的深色 UI |
| `raycast.md` | Raycast | 利落深色 chrome、鲜艳渐变强调 |
| `resend.md` | Resend | 极简深色主题、等宽强调 |
| `sentry.md` | Sentry | 深色仪表盘、数据密集、粉紫强调 |
| `supabase.md` | Supabase | 深色祖母绿主题、代码优先的开发者工具 |
| `superhuman.md` | Superhuman | 高级深色 UI、键盘优先、紫色辉光 |
| `vercel.md` | Vercel | 黑白精确、Geist 字体系统 |
| `warp.md` | Warp | 类 IDE 深色界面、块式命令 UI |
| `zapier.md` | Zapier | 暖橙、友好的插画驱动 |

### 基础设施与云

| 模板 | 站点 | 风格 |
|---|---|---|
| `clickhouse.md` | ClickHouse | 黄色强调、技术文档风 |
| `composio.md` | Composio | 现代深色配多彩集成图标 |
| `hashicorp.md` | HashiCorp | 企业级干净、黑白 |
| `mongodb.md` | MongoDB | 绿叶品牌、聚焦开发者文档 |
| `sanity.md` | Sanity | 红色强调、内容优先的编辑风布局 |
| `stripe.md` | Stripe | 标志性紫色渐变、weight-300 优雅 |

### 设计与生产力

| 模板 | 站点 | 风格 |
|---|---|---|
| `airtable.md` | Airtable | 多彩、友好、结构化数据美学 |
| `cal.md` | Cal.com | 干净中性 UI、面向开发者的极简 |
| `clay.md` | Clay | 有机形状、柔和渐变、艺术指导布局 |
| `figma.md` | Figma | 鲜艳多色、俏皮而专业 |
| `framer.md` | Framer | 大胆黑蓝、动效优先、设计导向 |
| `intercom.md` | Intercom | 友好蓝色调、对话式 UI 模式 |
| `miro.md` | Miro | 亮黄强调、无限画布美学 |
| `notion.md` | Notion | 温暖极简、衬线标题、柔和表面 |
| `pinterest.md` | Pinterest | 红色强调、瀑布流网格、图片优先布局 |
| `webflow.md` | Webflow | 蓝色强调、精致营销站美学 |

### 金融科技与加密

| 模板 | 站点 | 风格 |
|---|---|---|
| `coinbase.md` | Coinbase | 干净蓝色识别、聚焦信任、机构感 |
| `kraken.md` | Kraken | 紫色强调深色 UI、数据密集仪表盘 |
| `revolut.md` | Revolut | 利落深色界面、渐变卡片、金融科技精确 |
| `wise.md` | Wise | 亮绿强调、友好清晰 |

### 企业与消费

| 模板 | 站点 | 风格 |
|---|---|---|
| `airbnb.md` | Airbnb | 暖珊瑚强调、摄影驱动、圆润 UI |
| `apple.md` | Apple | 高级留白、SF Pro、电影感影像 |
| `bmw.md` | BMW | 深色高级表面、精确工程美学 |
| `ibm.md` | IBM | Carbon design system、结构化蓝色调 |
| `nvidia.md` | NVIDIA | 绿黑能量、技术力量美学 |
| `spacex.md` | SpaceX | 冷峻黑白、满幅影像、未来感 |
| `spotify.md` | Spotify | 深色上的鲜艳绿、粗体字、专辑封面驱动 |
| `uber.md` | Uber | 大胆黑白、紧凑字体、都市能量 |

## 如何挑选设计

把设计匹配到内容：

- **开发者工具 / 仪表盘：** Linear, Vercel, Supabase, Raycast, Sentry
- **文档 / 内容站点：** Mintlify, Notion, Sanity, MongoDB
- **营销 / 落地页：** Stripe, Framer, Apple, SpaceX
- **深色模式 UI：** Linear, Cursor, ElevenLabs, Warp, Superhuman
- **浅色 / 干净 UI：** Vercel, Stripe, Notion, Cal.com, Replicate
- **俏皮 / 友好：** PostHog, Figma, Lovable, Zapier, Miro
- **高级 / 奢华：** Apple, BMW, Stripe, Superhuman, Revolut
- **数据密集 / 仪表盘：** Sentry, Kraken, Cohere, ClickHouse
- **等宽 / 终端美学：** Ollama, OpenCode, x.ai, VoltAgent