---
name: petdex
description: "安装、选择或排查 Hermes 动画宠物（petdex）时使用。只要涉及 hermes pets、桌面/终端吉祥物、display.pet 配置或宠物不显示的问题，就主动加载，即使用户只是说「换个宠物」。"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [petdex, mascot, display, cli, tui, desktop]
    category: productivity
    homepage: https://petdex.dev
---

# Petdex 技能

浏览、安装并选择公共
[petdex](https://github.com/crafter-station/petdex) 画廊里的动画「宠物」吉祥物。安装后的宠物会随
代理活动（空闲、运行工具、审阅、出错、完成）在
Hermes CLI、TUI 和桌面应用中做出反应。本 skill 驱动 `hermes pets` CLI
和 `display.pet` 配置——它不生成精灵图。

## 何时使用

- 用户想要桌面/终端吉祥物，或问起「宠物」/ petdex。
- 用户想更换、预览或停用当前宠物。
- 排查宠物为何不显示（终端图形支持、配置）。

## 前置条件

- 能访问 `petdex.dev` 以获取画廊/manifest（只读，无需认证）。
- Pillow（Hermes 核心依赖）用于解码精灵图——已安装。
- 完整保真的终端渲染：需支持图形协议的终端（kitty、
  Ghostty、WezTerm、iTerm2 或 sixel）。否则自动回退到 truecolor Unicode
  半块字符渲染。

## 如何运行

用 `terminal` 工具运行 `hermes pets <subcommand>`。

## 快速参考

| 目标 | 命令 |
| --- | --- |
| 浏览画廊 | `hermes pets list` （加子串过滤：`hermes pets list cat`） |
| 列出已安装的宠物 | `hermes pets list --installed` |
| 安装宠物 | `hermes pets install <slug>` （加 `--select` 使其生效） |
| 设为当前宠物 | `hermes pets select <slug>` （省略 slug 则弹出选择器） |
| 全局缩放宠物 | `hermes pets scale <factor>` （如 `0.5`，限制在 0.1–3.0） |
| 在终端预览/播放动画 | `hermes pets show [slug] [--cycle] [--state run]` |
| 停用宠物 | `hermes pets off` |
| 移除宠物 | `hermes pets remove <slug>` |
| 诊断配置 | `hermes pets doctor` |

## 流程

1. 找宠物：`hermes pets list <query>`，记下它的 `slug`。
2. 安装 + 激活：`hermes pets install <slug> --select`。
3. 预览：`hermes pets show`（Ctrl+C 停止）。
4. 确认配置：`hermes pets doctor`——显示解析到的宠物、已配置的
   渲染模式、检测到的终端图形协议，以及实际生效的模式。

宠物安装到 `<HERMES_HOME>/pets/<slug>/`（按 profile 隔离）。选择宠物会
把 `display.pet.slug` + `display.pet.enabled` 写入 `config.yaml`。

## 配置

`config.yaml` 中 `display.pet` 下：

- `enabled`（bool）——总开关。
- `slug`（str）——当前宠物；留空 = 第一个已安装的。
- `render_mode`——`auto`（自动检测）| `kitty` | `iterm` | `sixel` | `unicode` | `off`。
- `scale`（float）——原生 192×208 帧的屏幕尺寸（默认 0.33，
  限制在 0.1–3.0）。一个旋钮即可缩放所有界面；可用
  `hermes pets scale <factor>`、`/pet scale` 斜杠命令或桌面端
  外观滑块设置。
- `unicode_cols`（int）——Unicode 回退渲染的列宽。

## 常见坑

- 只有既安装又选中（`enabled: true`）宠物才会显示。
- 在管道/重定向中（无 TTY）终端渲染按设计禁用。
- petdex npm CLI 安装到 `~/.codex/pets`；Hermes 改用自己
  按 profile 隔离的 `<HERMES_HOME>/pets/`——请通过 `hermes pets` 安装。

## 验证

- 当宠物已安装、已选中、已启用且 Pillow 可导入时，`hermes pets doctor`
  会报告 `✓ ready`。
