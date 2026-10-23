---
name: touchdesigner-mcp
description: "通过 twozero MCP 控制 TouchDesigner 时使用。只要要在 TD 里搭实时视觉 / 生成艺术 / 音频反应 / VJ 装置网络并操作节点，就主动加载。即使用户只说「用 TD 做个视觉效果」。提供 36 个 MCP 工具与验证过的 GLSL 配方。"
version: 1.1.0
author: kshitijk4poor
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [TouchDesigner, MCP, twozero, creative-coding, real-time-visuals, generative-art, audio-reactive, VJ, installation, GLSL]
    related_skills: [ascii-video, manim-video]

---

# TouchDesigner 集成（twozero MCP）

## 关键规则

1. **绝不猜参数名。** 先对 op 类型调用 `td_get_par_info`。你的训练数据对 TD 2025.32 是错的。
2. **若触发 `tdAttributeError`，停下。** 先对出错的节点调用 `td_get_operator_info` 再继续。
3. **绝不在 script 回调里硬编码绝对路径**。用 `me.parent()` / `scriptOp.parent()`。
4. **优先用原生 MCP 工具而非 td_execute_python。** 用 `td_create_operator`、`td_set_operator_pars`、`td_get_errors` 等。只有复杂的多步逻辑才回退到 `td_execute_python`。
5. **构建前先调用 `td_get_hints`。** 它返回与你所用 op 类型相关的模式。

## 架构

```
Hermes Agent -> MCP (Streamable HTTP) -> twozero.tox (port 40404) -> TD Python
```

36 个原生工具。免费插件（无需付费 / 许可——2026 年 4 月确认）。
上下文感知（知道当前选中的 OP 与网络）。
Hub 健康检查：`GET http://localhost:40404/mcp` 返回含实例 PID、项目名、TD 版本的 JSON。

## 安装（自动化）

运行安装脚本处理一切：

```bash
bash "${HERMES_HOME:-$HOME/.hermes}/skills/creative/touchdesigner-mcp/scripts/setup.sh"
```

脚本会：
1. 检查 TD 是否在运行
2. 若未缓存则下载 twozero.tox
3. 把 `twozero_td` MCP server 加入 Hermes 配置（若缺失）
4. 在 40404 端口测试 MCP 连接
5. 报告还剩哪些手动步骤（把 .tox 拖进 TD、启用 MCP 开关）

### 手动步骤（一次性，无法自动化）

1. **把 `~/Downloads/twozero.tox` 拖进 TD 网络编辑器** → 点击 Install
2. **启用 MCP：** 点击 twozero 图标 → Settings → mcp → "auto start MCP" → Yes
3. **重启 Hermes 会话**以加载新的 MCP server

安装后校验：
```bash
nc -z 127.0.0.1 40404 && echo "twozero MCP: READY"
```

## 环境说明

- **Non-Commercial 版 TD** 分辨率上限 1280×1280。用 `outputresolution = 'custom'` 并显式设置宽 / 高。
- **编解码器：** `prores`（macOS 上首选）或 `mjpa` 作为回退。H.264/H.265/AV1 需要 Commercial 许可。
- 设置参数前始终调用 `td_get_par_info`——参数名随 TD 版本而变（见关键规则 #1）。

## 工作流

### 第 0 步：侦察（构建任何东西之前）

```
Call td_get_par_info with op_type for each type you plan to use.
Call td_get_hints with the topic you're building (e.g. "glsl", "audio reactive", "feedback").
Call td_get_focus to see where the user is and what's selected.
Call td_get_network to see what already exists.
```

无需临时节点、无需清理。这彻底取代了旧的侦察套路。

### 第 1 步：清理 + 构建

**重要：把清理与创建拆成*分开*的 MCP 调用。** 在同一个 `td_execute_python` 脚本里销毁并重建同名节点会导致 "Invalid OP object" 错误。见 pitfalls #11b。

对每个节点用 `td_create_operator`（自动处理视口定位）：

```
td_create_operator(type="noiseTOP", parent="/project1", name="bg", parameters={"resolutionw": 1280, "resolutionh": 720})
td_create_operator(type="levelTOP", parent="/project1", name="brightness")
td_create_operator(type="nullTOP", parent="/project1", name="out")
```

批量创建或连线时，用 `td_execute_python`：

```python
# td_execute_python script:
root = op('/project1')
nodes = []
for name, optype in [('bg', noiseTOP), ('fx', levelTOP), ('out', nullTOP)]:
    n = root.create(optype, name)
    nodes.append(n.path)
# Wire chain
for i in range(len(nodes)-1):
    op(nodes[i]).outputConnectors[0].connect(op(nodes[i+1]).inputConnectors[0])
result = {'created': nodes}
```

### 第 2 步：设置参数

优先用原生工具（校验参数、不会崩溃）：

```
td_set_operator_pars(path="/project1/bg", parameters={"roughness": 0.6, "monochrome": true})
```

表达式或模式用 `td_execute_python`：

```python
op('/project1/time_driver').par.colorr.expr = "absTime.seconds % 1000.0"
```

### 第 3 步：连线

用 `td_execute_python`——不存在原生连线工具：

```python
op('/project1/bg').outputConnectors[0].connect(op('/project1/fx').inputConnectors[0])
```

### 第 4 步：校验

```
td_get_errors(path="/project1", recursive=true)
td_get_perf()
td_get_operator_info(path="/project1/out", detail="full")
```

### 第 5 步：显示 / 捕获

```
td_get_screenshot(path="/project1/out")
```

或通过脚本打开窗口：

```python
win = op('/project1').create(windowCOMP, 'display')
win.par.winop = op('/project1/out').path
win.par.winw = 1280; win.par.winh = 720
win.par.winopen.pulse()
```

## MCP 工具速查

**核心（最常用）：**
| 工具 | 用途 |
|------|------|
| `td_execute_python` | 在 TD 中运行任意 Python。完整 API 访问。 |
| `td_create_operator` | 创建带参数的节点 + 自动定位 |
| `td_set_operator_pars` | 安全设置参数（校验、不会崩） |
| `td_get_operator_info` | 检查单个节点：连接、参数、错误 |
| `td_get_operators_info` | 一次调用检查多个节点 |
| `td_get_network` | 查看某路径下的网络结构 |
| `td_get_errors` | 递归查找错误 / 警告 |
| `td_get_par_info` | 获取某 OP 类型的参数名（取代侦察） |
| `td_get_hints` | 构建前获取模式 / 提示 |
| `td_get_focus` | 哪个网络打开、选中了什么 |

**读 / 写：**
| 工具 | 用途 |
|------|------|
| `td_read_dat` | 读取 DAT 文本内容 |
| `td_write_dat` | 写入 / 修补 DAT 内容 |
| `td_read_chop` | 读取 CHOP 通道值 |
| `td_read_textport` | 读取 TD 控制台输出 |

**视觉：**
| 工具 | 用途 |
|------|------|
| `td_get_screenshot` | 把一个 OP 查看器捕获到文件 |
| `td_get_screenshots` | 一次捕获多个 OP |
| `td_get_screen_screenshot` | 通过 TD 捕获实际屏幕 |
| `td_navigate_to` | 把网络编辑器跳转到某个 OP |

**搜索：**
| 工具 | 用途 |
|------|------|
| `td_find_op` | 跨项目按名称 / 类型查找 op |
| `td_search` | 搜索代码、表达式、字符串参数 |

**系统：**
| 工具 | 用途 |
|------|------|
| `td_get_perf` | 性能剖析（FPS、慢 op） |
| `td_list_instances` | 列出所有运行中的 TD 实例 |
| `td_get_docs` | 某 TD 主题的深入文档 |
| `td_agents_md` | 读 / 写每个 COMP 的 markdown 文档 |
| `td_reinit_extension` | 编辑代码后重载 extension |
| `td_clear_textport` | 调试会话前清空控制台 |

**输入自动化：**
| 工具 | 用途 |
|------|------|
| `td_input_execute` | 向 TD 发送鼠标 / 键盘 |
| `td_input_status` | 轮询输入队列状态 |
| `td_input_clear` | 停止输入自动化 |
| `td_op_screen_rect` | 获取节点的屏幕坐标 |
| `td_click_screen_point` | 点击截图中的某点 |
| `td_screen_point_to_global` | 把截图像素转换为绝对屏幕坐标 |

上表覆盖了典型创作工作流中用到的 32 个工具。其余 4 个（`td_project_quit`、`td_test_session`、`td_dev_log`、`td_clear_dev_log`）是管理 / dev-mode 工具——完整 36 工具参考与完整参数 schema 见 `references/mcp-tools.md`。

## 关键实现规则

**GLSL 时间：** GLSL TOP 里没有 `uTDCurrentTime`。用 Values 页：
```python
# Call td_get_par_info(op_type="glslTOP") first to confirm param names
td_set_operator_pars(path="/project1/shader", parameters={"value0name": "uTime"})
# Then set expression via script:
# op('/project1/shader').par.value0.expr = "absTime.seconds"
# In GLSL: uniform float uTime;
```

回退：用 `rgba32float` 格式的 Constant TOP（8-bit 会钳制到 0-1，冻住 shader）。

**Feedback TOP：** 用 `top` 参数引用，而非直接输入连线。"Not enough sources" 会在首次 cook 后消失。"Cook dependency loop" 警告是预期内的。

**分辨率：** Non-Commercial 版上限 1280×1280。用 `outputresolution = 'custom'`。

**大型 shader：** 把 GLSL 写到 `/tmp/file.glsl`，再用 `td_write_dat` 或 `td_execute_python` 加载。

**Vertex / Point 访问（TD 2025.32）：** `point.P[0]`、`point.P[1]`、`point.P[2]`——不是 `.x`、`.y`、`.z`。

**Extensions：** CONSTANT 模式下 `ext0object` 的格式是 `"op('./datName').module.ClassName(me)"`。用 `td_write_dat` 编辑 extension 代码后，调用 `td_reinit_extension`。

**Script 回调：** 始终通过 `me.parent()` / `scriptOp.parent()` 使用相对路径。

**清理节点：** 迭代前始终 `list(root.children)`，并做 `child.valid` 检查。

## 录制 / 导出视频

```python
# via td_execute_python:
root = op('/project1')
rec = root.create(moviefileoutTOP, 'recorder')
op('/project1/out').outputConnectors[0].connect(rec.inputConnectors[0])
rec.par.type = 'movie'
rec.par.file = '/tmp/output.mov'
rec.par.videocodec = 'prores'  # Apple ProRes — NOT license-restricted on macOS
rec.par.record = True   # start
# rec.par.record = False  # stop (call separately later)
```

H.264/H.265/AV1 需要 Commercial 许可。macOS 上用 `prores`，或用 `mjpa` 回退。
抽帧：`ffmpeg -i /tmp/output.mov -vframes 120 /tmp/frames/frame_%06d.png`

**TOP.save() 对动画没用**——每次都捕获同一张 GPU 纹理。始终用 MovieFileOut。

### 录制前：清单

1. **用 `td_get_perf` 确认 FPS > 0**。若 FPS=0，录制会是空的。见 pitfalls #38-39。
2. **用 `td_get_screenshot` 确认 shader 输出不是黑的**。全黑输出 = shader 错误或缺输入。见 pitfalls #8、#40。
3. **若带音频录制：** 先让音频起播，再把录制延后 3 帧。见 pitfalls #19。
4. **开始录制前先设好输出路径**——在同一脚本里同时设置两者可能产生竞态。

## 音频反应式 GLSL（验证过的配方）

### 正确的信号链（2026 年 4 月测试）

```
AudioFileIn CHOP (playmode=sequential)
  → AudioSpectrum CHOP (FFT=512, outputmenu=setmanually, outlength=256, timeslice=ON)
  → Math CHOP (gain=10)
  → CHOP to TOP (dataformat=r, layout=rowscropped)
  → GLSL TOP input 1 (spectrum texture, 256x2)

Constant TOP (rgba32float, time) → GLSL TOP input 0
GLSL TOP → Null TOP → MovieFileOut
```

### 关键音频反应规则（经验验证）

1. **AudioSpectrum 的 TimeSlice 必须保持 ON**。OFF = 处理整个音频文件 → 24000+ 采样 → CHOP to TOP 溢出。
2. **手动把 Output Length 设为 256**，用 `outputmenu='setmanually'` 与 `outlength=256`。默认输出 22050 采样。
3. **不要用 Lag CHOP 做频谱平滑。** Lag CHOP 以 timeslice 模式运行，会把 256 采样扩到 2400+，把所有值平均到接近零（~1e-06）。shader 拿不到可用数据。这是测试中头号音频同步失败。
4. **也不要用 Filter CHOP**——频谱数据同样有 timeslice 扩张问题。
5. **平滑该放在 GLSL shader 里**（如果需要），用反馈纹理做时间 lerp：`mix(prevValue, newValue, 0.3)`。这样能帧级精确同步、零管线延迟。
6. **CHOP to TOP 的 dataformat = 'r'**，layout = 'rowscropped'。频谱输出是 256x2（立体声）。第一通道采样 y=0.25。
7. **Math gain = 10**（不是 5）。低频段原始频谱值约 0.19。增益 10 给 shader 约 5.0 的可用值。
8. **不需要 Resample CHOP。** 直接通过 AudioSpectrum 的 `outlength` 参数控制输出大小。

### GLSL 频谱采样

```glsl
// Input 0 = time (1x1 rgba32float), Input 1 = spectrum (256x2)
float iTime = texture(sTD2DInputs[0], vec2(0.5)).r;

// Sample multiple points per band and average for stability:
// NOTE: y=0.25 for first channel (stereo texture is 256x2, first row center is 0.25)
float bass = (texture(sTD2DInputs[1], vec2(0.02, 0.25)).r +
              texture(sTD2DInputs[1], vec2(0.05, 0.25)).r) / 2.0;
float mid  = (texture(sTD2DInputs[1], vec2(0.2, 0.25)).r +
              texture(sTD2DInputs[1], vec2(0.35, 0.25)).r) / 2.0;
float hi   = (texture(sTD2DInputs[1], vec2(0.6, 0.25)).r +
              texture(sTD2DInputs[1], vec2(0.8, 0.25)).r) / 2.0;
```

完整构建脚本 + shader 代码见 `references/network-patterns.md`。

## Operator 速查

| 家族 | 颜色 | Python class / MCP type | 后缀 |
|--------|-------|-------------|--------|
| TOP | 紫 | noiseTOP, glslTOP, compositeTOP, levelTop, blurTOP, textTOP, nullTOP | TOP |
| CHOP | 绿 | audiofileinCHOP, audiospectrumCHOP, mathCHOP, lfoCHOP, constantCHOP | CHOP |
| SOP | 蓝 | gridSOP, sphereSOP, transformSOP, noiseSOP | SOP |
| DAT | 白 | textDAT, tableDAT, scriptDAT, webserverDAT | DAT |
| MAT | 黄 | phongMAT, pbrMAT, glslMAT, constMAT | MAT |
| COMP | 灰 | geometryCOMP, containerCOMP, cameraCOMP, lightCOMP, windowCOMP | COMP |

## 安全说明

- MCP 只监听 localhost（端口 40404）。无认证——任何本地进程都能发命令。
- `td_execute_python` 以 TD 进程用户的身份，对 TD Python 环境与文件系统有不受限的访问。
- `setup.sh` 从官方 404zero.com URL 下载 twozero.tox。若担心可自行校验下载。
- 本 skill 绝不把数据发到 localhost 之外。所有 MCP 通信都是本地的。

## 参考文档

| 文件 | 内容 |
|------|------|
| `references/pitfalls.md` | 真实会话中得来的血泪教训 |
| `references/operators.md` | 所有 operator 家族，含参数与用例 |
| `references/network-patterns.md` | 配方：音频反应、生成式、GLSL、instancing |
| `references/mcp-tools.md` | 完整的 twozero MCP 工具参数 schema |
| `references/python-api.md` | TD Python：op()、脚本、extensions |
| `references/troubleshooting.md` | 连接诊断、调试 |
| `references/glsl.md` | GLSL uniform、内置函数、shader 模板 |
| `references/postfx.md` | 后期特效：bloom、CRT、色差、反馈辉光 |
| `references/layout-compositor.md` | HUD 布局模式、面板网格、BSP 式布局 |
| `references/operator-tips.md` | 线框渲染、feedback TOP 设置 |
| `references/geometry-comp.md` | Geometry COMP：instancing、POP vs SOP、变形 |
| `references/audio-reactive.md` | 音频频段提取、节拍检测、包络跟随 |
| `references/animation.md` | LFO、计时器、关键帧、缓动、表达式驱动运动 |
| `references/midi-osc.md` | MIDI/OSC 控制器、TouchOSC、多机同步 |
| `references/particles.md` | POP 与旧版 particleSOP——发射、力、碰撞 |
| `references/projection-mapping.md` | 多窗口输出、corner pin、网格变形、边缘融合 |
| `references/external-data.md` | HTTP、WebSocket、MQTT、Serial、TCP、webserverDAT |
| `references/panel-ui.md` | 自定义参数、panel COMP、按钮 / 滑块 / 字段、panelExecuteDAT |
| `references/replicator.md` | replicatorCOMP——数据驱动克隆、布局、回调 |
| `references/dat-scripting.md` | Execute DAT 家族——chop/dat/parameter/panel/op/executeDAT |
| `references/3d-scene.md` | 灯光装置、阴影、IBL/cubemap、多相机、PBR |
| `scripts/setup.sh` | 自动化安装脚本 |

---

> 你不是在写代码。你是在指挥光。
