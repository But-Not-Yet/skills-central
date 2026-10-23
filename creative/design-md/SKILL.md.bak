---
name: design-md
description: "编写 / 校验 / 导出 Google DESIGN.md token 规格文件时使用。只要要写 design token、design system 规格，或对 DESIGN.md 做 lint / diff / export / WCAG 对比度校验，就主动加载，即使用户只说「做个设计规范」。不用于纯视觉灵感或一次性 HTML 设计（考虑 popular-web-designs / claude-design）。"
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, design-system, tokens, ui, accessibility, wcag, tailwind, dtcg, google]
    related_skills: [popular-web-designs, claude-design, excalidraw, architecture-diagram]
---

# DESIGN.md Skill

DESIGN.md 是 Google 的开放规格（Apache-2.0，`google-labs-code/design.md`），用于向编码 agent 描述一套视觉识别。一个文件包含两部分：

- **YAML front matter** —— 机器可读的 design token（规范性取值）
- **Markdown 正文** —— 人类可读的设计理由，按规范章节组织

token 给出精确取值。散文告诉 agent 这些取值*为什么*存在、该如何应用。CLI（`npx @google/design.md`）会 lint 结构与 WCAG 对比度、对版本做 diff 以发现回归，并导出为 Tailwind 或 W3C DTCG JSON。

## 何时使用本 skill

- 用户要 DESIGN.md 文件、design token 或 design system 规格
- 用户希望多个项目或工具之间保持一致的 UI / 品牌
- 用户粘贴了现有 DESIGN.md，要 lint、diff、export 或扩展它
- 用户要把一份风格指南转成 agent 可消费的格式
- 用户要对调色板做对比度 / WCAG 无障碍校验

若只是找纯视觉灵感或布局示例，改用 `popular-web-designs`。若要从零设计一次性 HTML 制品（原型、演示、落地页、组件实验）并关注*过程与品味*，改用 `claude-design`。本 skill 针对的是*正式规格文件*本身。

## 文件结构

```md
---
version: alpha
name: Heritage
description: Architectural minimalism meets journalistic gravitas.
colors:
  primary: "#1A1C1E"
  secondary: "#6C7278"
  tertiary: "#B8422E"
  neutral: "#F7F5F2"
typography:
  h1:
    fontFamily: Public Sans
    fontSize: 3rem
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  body-md:
    fontFamily: Public Sans
    fontSize: 1rem
rounded:
  sm: 4px
  md: 8px
  lg: 16px
spacing:
  sm: 8px
  md: 16px
  lg: 24px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.sm}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.primary}"
---

## Overview

Architectural Minimalism meets Journalistic Gravitas...

## Colors

- **Primary (#1A1C1E):** Deep ink for headlines and core text.
- **Tertiary (#B8422E):** "Boston Clay" — the sole driver for interaction.

## Typography

Public Sans for everything except small all-caps labels...

## Components

`button-primary` is the only high-emphasis action on a page...
```

## Token 类型

| 类型 | 格式 | 示例 |
|------|--------|---------|
| Color | 任意 CSS 颜色（hex、`rgb()`、`oklch()`、颜色名） | `"#1A1C1E"`, `"oklch(62% 0.18 250)"` |
| Dimension | 数字 + 单位（`px`、`em`、`rem`） | `48px`, `-0.02em` |
| Token 引用 | `{path.to.token}` | `{colors.primary}` |
| Typography | 含 `fontFamily`、`fontSize`、`fontWeight`、`lineHeight`、`letterSpacing`、`fontFeature`、`fontVariation` 的对象 | 见上 |

组件属性白名单：`backgroundColor`、`textColor`、`typography`、`rounded`、`padding`、`size`、`height`、`width`。变体（hover、active、pressed）是**单独的组件条目**，用相关联的 key 名（`button-primary-hover`），而非嵌套。

## 规范章节顺序

章节是可选的，但出现的章节应按此顺序排列。linter 会标记顺序错乱的章节（`section-order`，warning）与重复标题——按规范，消费者会拒绝重复项，所以返回文件前两者都要修好。

1. Overview（别名：Brand & Style）
2. Colors
3. Typography
4. Layout（别名：Layout & Spacing）
5. Elevation & Depth（别名：Elevation）
6. Shapes
7. Components
8. Do's and Don'ts

未知章节会被保留而非报错。只要值类型合法，未知 token 名也会被接受。未知组件属性会产生 warning。

## 工作流：编写新的 DESIGN.md

1. **询问用户**（或推断）品牌调性、强调色与字体方向。若用户提供了网站、图片或氛围，把它转成上文的 token 形态。
2. **用 `write_file` 写 `DESIGN.md`** 到其项目根目录。始终包含 `name:` 与 `colors:`；其他章节可选但建议包含。
3. **在 `components:` 章节使用 token 引用**（`{colors.primary}`），而不是重新敲十六进制值。让调色板保持单一来源。
4. **对它 lint**（见下）。返回前修好任何失效引用或 WCAG 不达标项。
5. **若用户已有项目**，同时把 Tailwind 或 DTCG 导出写在文件旁（`tailwind.theme.json`、`tokens.json`）。

## 工作流：lint / diff / export

CLI 是 `@google/design.md`（Node）。使用 `npx`——无需全局安装。

```bash
# Validate structure + token references + WCAG contrast
npx -y @google/design.md lint DESIGN.md

# Compare two versions, fail on regression (exit 1 = regression)
npx -y @google/design.md diff DESIGN.md DESIGN-v2.md

# Export to Tailwind v3 theme JSON (`tailwind` is a back-compat alias)
npx -y @google/design.md export --format json-tailwind DESIGN.md > tailwind.theme.json

# Export to a Tailwind v4 CSS @theme block (--color-*, --text-*, --radius-*, ...)
npx -y @google/design.md export --format css-tailwind DESIGN.md > theme.css

# Export to W3C DTCG (Design Tokens Format Module) JSON
npx -y @google/design.md export --format dtcg DESIGN.md > tokens.json

# Print the spec itself — useful when injecting into an agent prompt
npx -y @google/design.md spec --rules-only --format json
```

所有命令都接受 `-` 表示 stdin。`lint` 在出错时返回 exit 1（仅有 warning 则 exit 0）。`export` 只要导出成功就 exit 0，无论源文件里的 lint 结果如何——要以此把关需单独跑 `lint`。输出默认是 JSON；若要以结构化方式报告发现，就解析它。

在 Windows 上，`design.md` 这个 bin 名可能与 `.md` 文件关联冲突（静默无操作，或用编辑器打开文件）。改用去点的别名：`npx -y -p @google/design.md designmd lint DESIGN.md`。

### Lint 规则参考（9 条规则，截至 CLI 0.3.0）

- `broken-ref`（error）—— `{colors.missing}` 指向不存在的 token
- `contrast-ratio`（warning）—— 组件 `textColor` 与 `backgroundColor` 低于 WCAG AA（4.5:1）
- `missing-primary`（warning）—— 定义了颜色但没有 `primary` token
- `missing-typography`（warning）—— 定义了颜色但没有 typography token
- `orphaned-tokens`（warning）—— 颜色 token 从未被任何组件引用
- `section-order`（warning）—— 章节顺序不符合规范
- `unknown-key`（warning）—— 顶层 YAML key 看起来是某个 schema key 的拼写错误（`colours:` → `colors:`）；自定义扩展 key 保持静默
- `token-summary`、`missing-sections`（info）—— 计数与缺失的可选章节

当用户在意无障碍时，在总结中明确点出——WCAG 发现是使用这个 CLI 最重的理由。

## 易错点

- **不要嵌套组件变体。** `button-primary.hover` 是错的；把 `button-primary-hover` 作为同级 key 才对。
- **十六进制颜色必须写成带引号的字符串。** 否则 YAML 会卡在 `#` 上，或把 `#1A1C1E` 这类值异常截断。
- **负尺寸也要加引号。** `letterSpacing: -0.02em` 会被解析成 YAML flow——写成 `letterSpacing: "-0.02em"`。
- **即使 linter 只给 warning，章节顺序也很重要。** 若用户给你的散文顺序是乱的，保存前按规范列表重排——符合规范的消费者期望如此。
- **Typography 子属性拼错会被静默丢弃。** 截至 CLI 0.3.0，像 `fontwight:` 这样的拼写错误不会产生任何提示，值也会从导出中消失——对照 schema 核对子属性名（`fontFamily`、`fontSize`、`fontWeight`、`lineHeight`、`letterSpacing`、`fontFeature`、`fontVariation`）。
- **`version: alpha` 是当前规格版本**（截至 2026 年 7 月，CLI 0.3.0）。规格标记为 alpha——留意破坏性变更。
- **Token 引用按点分路径解析。** `{colors.primary}` 有效；`{primary}` 无效。

## 规格权威来源

- 仓库：https://github.com/google-labs-code/design.md（Apache-2.0）
- CLI：npm 上的 `@google/design.md`
- 生成的 DESIGN.md 文件许可：随用户项目；规格本身是 Apache-2.0。
