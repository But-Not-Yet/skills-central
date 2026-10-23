---
name: obsidian
description: "读写、搜索、创建 Obsidian 笔记库内容时使用。只要涉及 Obsidian vault 的笔记，就主动加载，即使用户只说「记到笔记里」。"
version: 1.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Obsidian, Notes, Markdown, Vault]
    related_skills: []
---

# Obsidian Vault

处理「文件系统优先」的 Obsidian 笔记库时使用：读笔记、列笔记、搜笔记文件、建笔记、追加内容、加 wikilink。

## 库路径

调用文件工具前，先拿到已知或已解析的库路径。

惯例是用 `OBSIDIAN_VAULT_PATH` 环境变量记录库路径，例如放在 `${HERMES_HOME:-~/.hermes}/.env` 里。若未设置，退回 `~/Documents/Obsidian Vault`。

文件工具**不展开 shell 变量**。不要把含 `$OBSIDIAN_VAULT_PATH` 的路径传给 `read_file`、`write_file`、`patch` 或 `search_files`；先把库路径解析出来，再传具体绝对路径。库路径可能含空格——这也是优先用文件工具而非 shell 命令的另一个理由。

若库路径未知，可以用 `terminal` 去解析 `OBSIDIAN_VAULT_PATH` 或检查回退路径是否存在。**路径一旦确定，就切回文件工具。**

## 读笔记

用 `read_file` 传已解析的绝对路径。优先于 `cat`——它带行号与分页。

## 列笔记

用 `search_files` 配 `target: "files"` 与已解析的库路径。优先于 `find` 或 `ls`。

- 列全部 markdown 笔记：在库路径下用 `pattern: "*.md"`。
- 列某个子目录：在该子目录的绝对路径下搜索。

## 搜索

文件名与内容搜索都用 `search_files`。优先于 `grep`、`find`、`ls`。

- 找文件名：`search_files` + `target: "files"` + 文件名 `pattern`。
- 找笔记内容：`search_files` + `target: "content"` + 内容正则作 `pattern`，想只匹配 markdown 时加 `file_glob: "*.md"`。

## 建笔记

用 `write_file` 传已解析的绝对路径与完整 markdown 内容。优先于 shell heredoc 或 `echo`——它避开 shell 引号问题，并返回结构化结果。

## 追加到笔记

不别扭时，优先走原生文件工具流程：

- 先用 `read_file` 读目标笔记。
- 有稳定上下文时（如在某标题后加一节、或在已知结尾块前追加），用 `patch` 做锚定追加。
- 当整篇重写比构造脆弱的 patch 更清楚时，用 `write_file`。

用 `patch` 做锚定追加时，把锚点替换成「锚点 + 新内容」。

没有稳定上下文的简单追加，若 `terminal` 是最清楚的稳妥选项，可以用。

## 定点修改

当前内容能给出稳定上下文时，用 `patch` 做聚焦修改。优先于 shell 文本重写。

## Wikilink

Obsidian 用 `[[Note Name]]` 语法互联笔记。建笔记时用它链接相关内容。
