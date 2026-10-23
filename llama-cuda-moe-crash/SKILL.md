---
name: llama-cuda-moe-crash
description: "MoE 模型 CUDA illegal memory access 崩溃时使用。"
version: 1.0.0
author: Nekonya
license: MIT
metadata:
  hermes:
    tags: [llama.cpp, CUDA, MoE, crash, mmq, patch]
---

# MoE + CUDA illegal memory access（已知 bug 的诊断与修复）

## 何时使用

llama.cpp / ollama 跑 **MoE 模型**（如 Qwen3.6-35B-A3B）时崩：`CUDA error: an illegal memory access was encountered`，
栈指向 `launch_mul_mat_q` / `mmq.cuh`（常见报点 `cudaFuncSetAttribute((mul_mat_q<type,J,false>), ...)` —— 异步报错，真正的越界在上一个内核）。
或出现「prompt 大过某尺寸必崩」的描述。

**典型误导症状（别被带走）**：
- 「prompt 大到某个尺寸必崩」——崩不崩取决于越界读**撞没撞到未映射内存页边界**，不同机器尺寸不同（别人 508/684，我们 ~809），且同一请求换会话历史可能活。
- 「关思考/换内存分配（--fit off、--load-mode none、全 CPU 专家）能修」——**不能**，都是池布局的运气变化。
- 硬件嫌疑排除靠证据：WHEA/TDR/nvlddmkm 无自发事件 + 崩溃高度可复现同签名 → 软件层。

## 根因（已锤死）

`ggml/src/ggml-cuda/mmq.cu` 的 **mul_mat_id（MoE）路径**：`src1_q8_1` 缓冲尾部 padding 用错参数——
传了 `ne11`（MoE 路径下恒为 1 → `get_J_max(...,1)` 返回 0 → 无 padding），应为收集后的列数 `ne12`。
尾块按满宽 J 加载 → 越界读最多一个 y-tile。

同族公开案底（对签名、拿配方、看修复状态）：llama.cpp **#28151**（含一行修复）、**#27792**、**#29847**、ollama **#17740**。

## 修复（一行 + 增量重编译）

**先查上游是否已修**：官方从 **build b11389（2026-10-04）** 起带修复（合并的 PR = #29941，内容即下面这一行）；先跑在 b11389 之前的构建（如 b10964 / b10743）必然中招。后续 #29953（J 选择重构）仍在途——它不改这条崩溃的修复。

源码里定位（**只改 mul_mat_id 分支那处**；非 MoE 分支的同类调用 ne11 是对的、不要动）：
```
// mul_mat_id 分支，形如：
const size_t nbytes_src1_q8_1 = ne12*n_expert_used*ne10_padded * y_block_size/y_values_per_block +
    ggml_cuda_mmq_get_J_max(src0->type, fallback, cc, ne11) * sizeof(block_q8_1_mmq);
                                                                  ^^^^ → ne12
```
补齐之后，尾块越界仍会读、但落在已分配缓冲内（垃圾数据被丢弃）——崩溃消失。

**Windows 远程重编译配方**（本机验证过）：
1. 通过 SSH 拿到源码树 + 确认它构建过（有 `build/`、`CMakeCache.txt`）。
2. 从 `CMakeCache.txt` 读 `CMAKE_MAKE_PROGRAM`（ninja 路径）、`CMAKE_CXX_COMPILER`、`CMAKE_CUDA_COMPILER`、`CMAKE_GENERATOR`。
3. 编辑源文件：**scp 下→改→scp 上**；先按原样归一化行尾（源文件常是 CRLF，锚点用 `\n` 会静默失配），改完还原原行尾；改前 assert 锚点唯一，改后 assert 旧串只剩非 MoE 那处。
4. 重编译交给 `.cmd` 包装脚本（**别把带引号的长命令塞进 ssh 命令行**）：
   ```bat
   @echo off
   call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
   cd /d <build dir>
   cmake --build . --target llama-server --config Release > <log> 2>&1
   echo BUILD_EXIT=%errorlevel% >> <log>
   ```
   cmake 由 vcvars 进 PATH（VS 自带 `Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin`）；ninja 用缓存里的路径。
5. **验证编对地方**：补丁编进 `ggml-cuda.dll`（**不是** loader exe——exe 只有 10KB 壳，mtime 不变是正常的）。查 `ggml-cuda.dll` 时间戳 + 日志 `BUILD_EXIT=0` + 无 error 行。
6. 备份原 DLL/exe（`copy /Y *.bak-<date>`）再换 binary；用**改前必崩的那条请求**验收（同 prompt、同参数），再看服务存活 + 跑完整测试集。

## 边界

- 这是上游建议的缓解（只在 llm 侧修不了根，越界读仍在）；根治要约束 y-tile 加载的更大改动。
- 改第三方/他人源码树（如客户提供的 fork）：改动**不提交**、留独立 `.patch` 文件、备份二进制，报告里注明改动未入库。
- 别把「换个构建」当默认解：同一 bug 常横跨两个相近构建（我们试的两个都中招）——先看源码里那行是 ne11 还是 ne12，比试构建快。
