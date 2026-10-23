---
name: huggingface-hub
description: "用 hf CLI 操作 HuggingFace 时使用：搜索、下载、上传模型与数据集。只要要动 Hub 上的资源（模型、数据集、Space），就主动加载，即使用户只说「把这个模型拉下来」。"
version: 1.0.1
author: Hugging Face
license: MIT
tags: [huggingface, hf, models, datasets, hub, mlops]
platforms: [linux, macos, windows]
---

# Hugging Face CLI (`hf`) Reference Guide

The `hf` command is the modern command-line interface for interacting with the Hugging Face Hub, providing tools to manage repositories, models, datasets, and Spaces.

> **重要：** `hf` 命令取代了已废弃的 `huggingface-cli` 命令。

## 快速开始
*   **安装：** `curl -LsSf https://hf.co/cli/install.sh | bash -s`
*   **帮助：** 用 `hf --help` 查看所有可用功能与真实示例。
*   **认证：** 推荐用 `HF_TOKEN` 环境变量或 `--token` flag。

---

## 核心命令

### 通用操作
*   `hf download REPO_ID`：从 Hub 下载文件。
*   `hf upload REPO_ID`：上传文件/文件夹（推荐用于单次提交。也支持大目录的断点续传）。
*   `hf upload-large-folder REPO_ID LOCAL_PATH`：**[已废弃]** — 改用 `hf upload`。
*   `hf sync`：在本地目录与 bucket 之间同步文件。
*   `hf env` / `hf version`：查看环境与版本详情。

### 认证（`hf auth`）
*   `login` / `logout`：用来自 [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) 的 token 管理会话。
*   `list` / `switch`：管理并在多个已存 token 间切换。
*   `whoami`：显示当前登录的账号。

### 仓库管理（`hf repos`）
*   `create` / `delete`：创建或永久删除仓库。
*   `duplicate`：把 model、dataset 或 Space 克隆到新的 ID。
*   `move`：在 namespace 之间迁移仓库。
*   `branch` / `tag`：管理类 Git 的引用。
*   `delete-files`：按模式删除指定文件。

---

## 专项 Hub 交互

### Dataset 与 Model
*   **Datasets：** `hf datasets list`、`info` 与 `parquet`（列出 parquet URL）。
*   **SQL 查询：** `hf datasets sql SQL` — 通过 DuckDB 对 dataset 的 parquet URL 执行裸 SQL。
*   **Models：** `hf models list` 与 `info`。
*   **Papers：** `hf papers ls` — 查看每日论文。

### Discussion 与 Pull Request（`hf discussions`）
*   管理 Hub 贡献的生命周期：`list`、`create`、`info`、`comment`、`close`、`reopen` 与 `rename`。
*   `diff`：查看 PR 中的改动。
*   `merge`：完结 pull request。

### 基础设施与算力
*   **Endpoints：** 部署与管理 Inference Endpoints（`deploy`、`pause`、`resume`、`scale-to-zero`、`catalog`）。
*   **Jobs：** 在 HF 基础设施上跑算力任务。含 `hf jobs uv`（带内联依赖跑 Python 脚本）与 `stats`（资源监控）。
*   **Spaces：** 管理交互式应用。含 `dev-mode` 与 `hot-reload`，无需整体重启即可改 Python 文件。

### 存储与自动化
*   **Buckets：** 类 S3 的完整 bucket 管理（`create`、`cp`、`mv`、`rm`、`sync`）。
*   **Cache：** 用 `list`、`prune`（删除游离修订）与 `verify`（校验和检查）管理本地存储。
*   **Webhooks：** 通过管理 Hub webhook 自动化工作流（`create`、`watch`、`enable`/`disable`）。
*   **Collections：** 把 Hub 条目组织进合集（`add-item`、`update`、`list`）。

---

## 进阶用法与技巧

### 不下载整包、抽样数据集（datasets-server rows API）
*   `curl "https://datasets-server.huggingface.co/rows?dataset=OWNER/NAME&config=default&split=train&offset=N&limit=100"` — 分页返回行。每条记录嵌在 `{"row": {...}}` 下，字段要先取 `row` 再取列名（直接按列名取会 KeyError）。
*   很多数据集按类别/type 排序存储：只在头部取样只会看到第一个类别。按 offset 步长（≈ 总行数/10）扫多个窗口才能覆盖全部类别。
*   偶发 502：跳过该 offset 继续或重试，不要中断整轮扫描。
*   需要聚合统计时改用 `hf datasets sql`（DuckDB 跑 parquet URL）。

### 全局 flag
*   `--format json`：产出机器可读输出，便于自动化。
*   `-q` / `--quiet`：输出仅限 ID。

### 扩展与 skills
*   **Extensions：** 用 `hf extensions install REPO_ID` 通过 GitHub 仓库扩展 CLI 功能。
*   **Skills：** 用 `hf skills add` 管理 AI 助手 skills。
