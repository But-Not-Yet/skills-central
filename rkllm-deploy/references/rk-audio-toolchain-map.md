# RK 工具链世代判定与 SBC 音频栈选型地图

## 工具链世代判定（谈部署前先对表）
- 板载 NPU 世代决定可用仓库：RK3588/RK3576/RK3568/RK3566/RK3562/RV1103/RV1106/RV1126B → `airockchip/rknn-toolkit2` + `rknn_model_zoo`；RK1820/RK1828 协处理器与 RK3572 → `rknn3-toolkit` + `rknn3-model-zoo`（第三代）；RK1808/RV1109/RV1126 → 第一代 rknn-toolkit。判定依据是 rknn3-toolkit README 的官方平台表，不是记忆里的旧版图。
- rknn3 支持「RK3588/RK3576 当 host + RK1820/28 协处理器」模式，但模型跑在协处理器上——**纯 Orange Pi（无外挂协处理器）即使官方 model zoo 有该模型的示例也不能走 rknn3**。官方示例存在 ≠ 你的板子能用。
- rkllm/rkllm-runtime 只管 LLM。CHANGELOG 里出现「audio」只代表多模态音频**输入**接口，不代表 TTS 合成输出；要确认某模型类别是否支持，逐版本读 `airockchip/rknn-llm/CHANGELOG.md`，README 支持列表滞后。

## TTS/ASR 方案选型（RK3588 类 SBC）
决策点先定一个：**实时对话还是离线生成**。RTF（生成时长/音频时长）> 1 的方案进不了实时对话管线。

- **Qwen3-TTS 系**：Qwen 官方开源推理栈 = Python `qwen-tts` + vLLM，SBC 跑不动；要用它的模型（声克隆、表现力）只能靠第三方推理实现。darkautism/qwen3-tts（Rust/Candle，RK3588 纯 CPU，支持声克隆）作者自报 RTF 2.6~3.3，非实时。单人维护、无 release 的仓库上板前先查 `pushed_at`、stars、open issues 判活跃度，断供风险自担。
- **实时优先**：paroli（Piper 流式 C++，RK3588 NPU 可选加速，作者实测 RTF ~0.16）或 sherpa-onnx（kokoro-82M / VITS / Pocket TTS，CPU）。音质与表现力明显低于 Qwen3-TTS 系。
- **ASR on RK3588 NPU**：sherpa-onnx 的 RKNN zipformer（k2-fsa 官方文档提供导出流程与预训练模型）是 toolkit2 世代最成熟的路；sherpa-onnx 的 TTS-on-RKNN 长期是 open feature request，别按已实现来规划。
- 推荐组合：实时对话 → paroli/sherpa 系先通管线，音质后升级；离线高质量+声克隆 → Qwen3-TTS 系接受非实时；ASR+TTS 都要 → ASR 走 sherpa RKNN zipformer，TTS 按用途二选一。

## GitHub 生态侦察套路（判断仓库「过时与否」）
- 仓库健康度用 API 一次拿全：`api.github.com/repos/<owner>/<name>` 看 `pushed_at`/`stargazers_count`/`archived`；issues（state=all）与 releases 分开拉，无 release + 单人 + 长期未推 = 高断供风险信号。
- **airockchip 的仓库列表要用 `/users/airockchip/repos`**——`/orgs/` 端点对该主体返回 Not Found，别误判为仓库不存在。
- README 取 `raw.githubusercontent.com` 原文，不读渲染页；raw 路径 404 时先换默认分支名（main/master）再下结论。
- API 偶发限流时 sleep 几秒重试即可，响应体是 dict 且带 `message` 字段就是在报错，先看 message 再改策略。