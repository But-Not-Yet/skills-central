---
name: blogwatcher
description: "监控博客与 RSS/Atom 源（blogwatcher-cli）时使用。只要要盯博客更新、导入 OPML 或管理已读，就主动加载，即使用户只说「这些博客有更新吗」。"
version: 2.0.0
author: JulienTant (fork of Hyaxia/blogwatcher)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [RSS, Blogs, Feed-Reader, Monitoring]
    homepage: https://github.com/JulienTant/blogwatcher-cli
prerequisites:
  commands: [blogwatcher-cli]
---

# Blogwatcher

用 `blogwatcher-cli` 跟踪博客与 RSS/Atom 源更新。支持自动发现 feed、HTML 抓取兜底、OPML 导入，以及已读/未读文章管理。

## 安装

任选一种方式：

- **Go：** `go install github.com/JulienTant/blogwatcher-cli/cmd/blogwatcher-cli@latest`
- **Docker：** `docker run --rm -v blogwatcher-cli:/data ghcr.io/julientant/blogwatcher-cli`
- **二进制（Linux amd64）：** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **二进制（Linux arm64）：** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **二进制（macOS Apple Silicon）：** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **二进制（macOS Intel）：** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`

全部 release：https://github.com/JulienTant/blogwatcher-cli/releases

### Docker + 持久化存储

默认数据库位于 `~/.blogwatcher-cli/blogwatcher-cli.db`。在 Docker 里，容器重启会丢失它。用 `BLOGWATCHER_DB` 或 volume 挂载来持久化：

```bash
# Named volume (simplest)
docker run --rm -v blogwatcher-cli:/data -e BLOGWATCHER_DB=/data/blogwatcher-cli.db ghcr.io/julientant/blogwatcher-cli scan

# Host bind mount
docker run --rm -v /path/on/host:/data -e BLOGWATCHER_DB=/data/blogwatcher-cli.db ghcr.io/julientant/blogwatcher-cli scan
```

### 从原版 blogwatcher 迁移

若从 `Hyaxia/blogwatcher` 升级，迁移你的数据库：

```bash
mv ~/.blogwatcher/blogwatcher.db ~/.blogwatcher-cli/blogwatcher-cli.db
```

二进制名从 `blogwatcher` 改成了 `blogwatcher-cli`。

## 常用命令

### 管理博客

- 添加博客：`blogwatcher-cli add "My Blog" https://example.com`
- 带显式 feed 添加：`blogwatcher-cli add "My Blog" https://example.com --feed-url https://example.com/feed.xml`
- 用 HTML 抓取添加：`blogwatcher-cli add "My Blog" https://example.com --scrape-selector "article h2 a"`
- 列出已跟踪博客：`blogwatcher-cli blogs`
- 移除博客：`blogwatcher-cli remove "My Blog" --yes`
- 从 OPML 导入：`blogwatcher-cli import subscriptions.opml`

### 扫描与阅读

- 扫描所有博客：`blogwatcher-cli scan`
- 扫描单个博客：`blogwatcher-cli scan "My Blog"`
- 列出未读文章：`blogwatcher-cli articles`
- 列出所有文章：`blogwatcher-cli articles --all`
- 按博客过滤：`blogwatcher-cli articles --blog "My Blog"`
- 按分类过滤：`blogwatcher-cli articles --category "Engineering"`
- 标记文章已读：`blogwatcher-cli read 1`
- 标记文章未读：`blogwatcher-cli unread 1`
- 全部标为已读：`blogwatcher-cli read-all`
- 某博客全部标为已读：`blogwatcher-cli read-all --blog "My Blog" --yes`

## 环境变量

所有 flag 都可用带 `BLOGWATCHER_` 前缀的环境变量设置：

| 变量 | 说明 |
|---|---|
| `BLOGWATCHER_DB` | SQLite 数据库文件路径 |
| `BLOGWATCHER_WORKERS` | 并发扫描 worker 数（默认：8） |
| `BLOGWATCHER_SILENT` | 扫描时只输出 "scan done" |
| `BLOGWATCHER_YES` | 跳过确认提示 |
| `BLOGWATCHER_CATEGORY` | 按分类的文章默认过滤 |

## 输出示例

```
$ blogwatcher-cli blogs
Tracked blogs (1):

  xkcd
    URL: https://xkcd.com
    Feed: https://xkcd.com/atom.xml
    Last scanned: 2026-04-03 10:30
```

```
$ blogwatcher-cli scan
Scanning 1 blog(s)...

  xkcd
    Source: RSS | Found: 4 | New: 4

Found 4 new article(s) total!
```

```
$ blogwatcher-cli articles
Unread articles (2):

  [1] [new] Barrel - Part 13
       Blog: xkcd
       URL: https://xkcd.com/3095/
       Published: 2026-04-02
       Categories: Comics, Science

  [2] [new] Volcano Fact
       Blog: xkcd
       URL: https://xkcd.com/3094/
       Published: 2026-04-01
       Categories: Comics
```

## 备注

- 未提供 `--feed-url` 时，从博客首页自动发现 RSS/Atom feed。
- RSS 失败且配置了 `--scrape-selector` 时，退回 HTML 抓取。
- RSS/Atom feed 里的分类会被存储，可用于过滤文章。
- 从 Feedly、Inoreader、NewsBlur 等导出的 OPML 文件批量导入博客。
- 数据库默认存于 `~/.blogwatcher-cli/blogwatcher-cli.db`（用 `--db` 或 `BLOGWATCHER_DB` 覆盖）。
- 用 `blogwatcher-cli <command> --help` 发现所有 flag 与选项。
