---
name: openhue
description: "用 OpenHue CLI 控制 Philips Hue 灯、场景与房间时使用。只要要开关灯、调亮度或改场景，就主动加载，即使用户只说「把灯调暗点」。"
version: 1.0.1
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Smart-Home, Hue, Lights, IoT, Automation]
    homepage: https://www.openhue.io/cli
prerequisites:
  commands: [openhue]
---

# OpenHue CLI

从终端经 Hue Bridge 控制 Philips Hue 灯与场景。

## 前置条件

```bash
# Linux (pre-built binary — releases ship tarballs, not bare binaries)
curl -sL "https://github.com/openhue/openhue-cli/releases/latest/download/openhue_Linux_x86_64.tar.gz" \
  | tar -xz -C /tmp openhue \
  && install -m 0755 /tmp/openhue ~/.local/bin/openhue
# (use openhue_Linux_arm64.tar.gz on ARM64)

# macOS
brew install openhue/cli/openhue-cli
```

首次运行需按下 Hue Bridge 上的按钮完成配对。Bridge 必须与运行 Hermes 的机器在同一局域网。

## 何时使用

- 「开灯 / 关灯」
- 「把客厅灯调暗」
- 「设个场景」或「电影模式」
- 控制指定的 Hue 房间、区域或单只灯泡
- 调亮度、颜色或色温

## 常用命令

### 列出资源

```bash
openhue get light       # List all lights
openhue get room        # List all rooms
openhue get scene       # List all scenes
```

### 控制灯

```bash
# Turn on/off
openhue set light "Bedroom Lamp" --on
openhue set light "Bedroom Lamp" --off

# Brightness (0-100)
openhue set light "Bedroom Lamp" --on --brightness 50

# Color temperature (warm to cool: 153-500 mirek)
openhue set light "Bedroom Lamp" --on --temperature 300

# Color (by name or hex)
openhue set light "Bedroom Lamp" --on --color red
openhue set light "Bedroom Lamp" --on --rgb "#FF5500"
```

### 控制房间

```bash
# Turn off entire room
openhue set room "Bedroom" --off

# Set room brightness
openhue set room "Bedroom" --on --brightness 30
```

### 场景

```bash
openhue set scene "Relax" --room "Bedroom"
openhue set scene "Concentrate" --room "Office"
```

## 快捷预设

```bash
# Bedtime (dim warm)
openhue set room "Bedroom" --on --brightness 20 --temperature 450

# Work mode (bright cool)
openhue set room "Office" --on --brightness 100 --temperature 250

# Movie mode (dim)
openhue set room "Living Room" --on --brightness 10

# Everything off
openhue set room "Bedroom" --off
openhue set room "Office" --off
openhue set room "Living Room" --off
```

## 注意

- Bridge 必须与运行 Hermes 的机器在同一局域网
- 首次运行需物理按下 Hue Bridge 上的按钮授权
- 颜色只对支持彩色的灯泡生效（纯白型号不支持）
- 灯与房间名**区分大小写**——用 `openhue get light` 查准确名称
- 与定时任务配合得很好（如睡前调暗、起床调亮）
