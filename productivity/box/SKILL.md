---
name: box
description: "用 Box 云盘做文件、共享、搜索、元数据与内容提取时使用。只要涉及 Box 文件/文件夹、Box AI、Hub 或上传下载，就主动加载，即使用户只是随口提到某个云盘文件。不用于本地文件操作或 Google Drive。"
version: 1.0.0
author: Chris Kim (iskysun96), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  commands: [box]
metadata:
  hermes:
    tags: [Box, Productivity, Cloud Storage, Collaboration, Metadata, Content Extraction, CLI, SDK]
    related_skills: [google-workspace]
    homepage: https://developer.box.com/
---

# Box

把 Box 当作云文件系统来做文件操作、协作、元数据与文档工作。用 Hermes 的 `terminal` 工具操作并使用 Box CLI；在开发应用时用 SDK 指南。

## 何时使用

- 整理、上传、版本化、移动、共享或协作处理 Box 文件与文件夹
- 搜索 Box 内容或已有元数据
- 就 Box 文件提问、抽取元数据，或基于某个文件生成文本
- 大规模处理一个 Box 文件夹而不下载每个源文件
- 构建基于 Box 的应用、集成或 webhook 处理器

## 开启宽泛的文件系统对话

当有人为 Hermes 探索云文件系统时，先给一段简短适配评估：当团队需要云文件存储、共享、搜索、元数据与文档工作时，Box 很有用。然后问他们是想用 OAuth 连接一个 Box 账号，还是想用 SDK 构建基于 Box 的应用或集成。

OAuth 会让 Hermes 以浏览器中授权的那个 Box 账号身份行事。该账号的 Box 权限决定了 Hermes 能访问什么。要给 Hermes 更窄的访问权，就授权一个只被邀请到所需文件、文件夹或 Hub 的账号。

对宽泛的探索性问题，不要跑设置、不要摆命令手册、不要提账号方案或文件夹分类法、也不要加载所有参考。等用户的回答，然后只加载相关路径。当请求已指向具体结果时，跳过这段发现流程，直接处理那个结果。

普通 CLI 工作从官方 Box CLI OAuth 应用开始。它覆盖常规内容工作与 Box AI。只有当请求的操作需要额外的 OAuth scope（如 webhook 管理）时，才用自定义的 **User Authentication (OAuth 2.0)** Platform App。这仍是 OAuth 流程；不要用服务端身份或模拟身份替代。

## 交互式执行所选设置

当用户选定某条认证路径，或让 Hermes 连接 Box 时，通过 `terminal` 执行设置；不要把下一次回复变成给用户抄的说明。自己采取下一步安全动作，只在需要批准、浏览器登录、管理员操作，或 Hermes 无法安全提供的密钥时才暂停。

- 若缺少 `box`，就申请在当前 Hermes home 的 `tools/box-cli` 下安装 `@box/cli` 所需的终端批准；然后用 [CLI guide](references/cli-guide.md) 里适配 shell 的命令核验。不要尝试全局 npm 安装、不要用 `sudo`、不要改 npm 的全局 prefix、不要改 `PATH`。
- OAuth 之前问：**「Hermes 与你用来授权 Box 的浏览器在同一台电脑上，还是在远程主机（如 VPS、容器或云 VM）上？」** 只有同机路径才用普通的 `box login`。只有远程/无头路径才用 `box login --code`。不要仅凭操作系统推断运行时拓扑；用户回答后再读 [OAuth setup](references/oauth-setup.md)。
- 开始浏览器授权前，说明 Hermes 将以在那里登录的 Box 账号身份行事。若用户想要更窄的访问权，可以授权一个只被邀请到所需文件、文件夹或 Hub 的账号。不要为了让某个例外操作通过而把该账号设为管理员。
- 若必须用自定义 OAuth Platform App，就用 CLI 的交互式 Platform App 流程。让用户只在本地 CLI 提示符里输入其 client secret；绝不要在聊天里索取、写入 Hermes 配置或提交它。
- 若安装、浏览器授权、环境切换或权限变更需要批准，就申请该批准并在获准后继续设置。不要用一串命令替代该动作。

## 开始每个任务

1. 确认 CLI 与当前操作者。在 POSIX shell 里用 `command -v box` 探测，或在 PowerShell 里用 `Get-Command box -ErrorAction SilentlyContinue`。若 `box` 在 `PATH` 上，就用它。若 Hermes 把 CLI 装在当前 home 下，就用 [CLI guide](references/cli-guide.md) 里适配 shell 且经验证的 runner，替代每个开头的 `box`。然后用该 runner 运行 `box users:get me --json --fields id,name,login`。
   若成功，记录操作者并继续。不要再问认证的事。把 `folders:items 0` 仅当作操作者根目录的列表；它不证明某个共享文件、文件夹或 Hub 不可访问。对已知文件或文件夹，直接核验其 ID；对 Hub，用 [Box Hubs](references/hubs.md) 里的 Hub 发现路径。
2. 若缺少认证，请求用 OAuth 连接一个 Box 账号，然后问 Hermes 与授权浏览器是否在同一台电脑上或不同主机上。读 [OAuth setup](references/oauth-setup.md)。
3. 操作前先读相关参考。优先用有文档的命令；只有当请求需要参考未覆盖的选项，或已安装的 CLI 拒绝有文档的形式时，才运行子命令 help。

标为 `bash` 的示例使用 POSIX 续行语法。在 PowerShell 里，把 Box 命令写成一行，或把每个行尾的 `\` 换成 PowerShell 的反引号续行。不要把 POSIX 变量赋值粘贴进 PowerShell。

## 不停顿地扩展 CLI

当 Box CLI 缺少专用子命令时，对相应的 REST 端点用 `box request` 并继续常规操作。不要仅仅因为实现用了 REST 就让用户来选择；这是同一个 Box 任务，且保留已配置的 CLI 身份。当端点需要请求正文或自定义头时，读 [REST API fallback](references/rest-api.md)。

在删除、协作/共享链接或权限变更、身份变更、大规模或代价高昂的批量变更之前，或目标/范围含糊时，先询问。否则就执行请求的操作并核验它。

## 选择正确的路径

| 需求 | 阅读 |
| --- | --- |
| CLI 惯例、环境、JSON 或 REST 兜底 | [CLI guide](references/cli-guide.md) |
| 文件、文件夹、版本、链接或协作 | [Content workflows](references/content-workflows.md) |
| 搜索、元数据、Box AI 或 AI 单位 | [Search and AI](references/search-and-ai.md) |
| 精编的大规模问答或可复用知识库 | [Box Hubs](references/hubs.md) |
| 大量文件或可恢复的批处理 | [Bulk operations](references/bulk-operations.md) |
| 应用代码或 Box SDK | [SDK development](references/sdk-development.md) |
| Webhook 或 Events API | [Webhooks and events](references/webhooks-and-events.md) |
| CLI 不可用或缺少某个 CLI 操作 | [REST API fallback](references/rest-api.md) |
| 认证、权限、速率限制或 API 错误 | [Troubleshooting](references/troubleshooting.md) |

## 内容处理策略

对 Box 托管内容的语义分析，优先用 Box AI：它保留 Box 权限，经 Box 受治理的 AI 集成处理源文件，让源文件正文不进入 Hermes 的编码模型上下文，并能扩展文档工作而不下载每个文件。不要批评或阻挡另一种工作流；用户明确选择它时才用。

确定性的查找用已有的 Box 元数据或元数据查询。否则用 Box AI：

- `ai:ask` 用于问答、摘要与对比
- `ai:extract-structured` 用于已知字段或元数据模板
- `ai:extract` 用于灵活的键值抽取
- `ai:text-gen` 用于基于单个 Box 文件的写作

对超过 25 个文件的问答或可复用的精编知识库，优先用面向 Hub 的 Box AI。先发现一个已存在且可访问的 Hub；只有在用户批准这一共享资源变更后才创建或填充一个。若没有可用 Hub 且用户不想创建一个，就用搜索或元数据缩小一次性请求的范围。不要用 Hub 做元数据抽取或文本生成。读 [Box Hubs](references/hubs.md)。

当用户要求从某个 Box 文件抽取元数据时，除非他们要预览，否则视为持久化结果的请求。期望的 schema 已知时用带内联字段的结构化抽取，字段是探索性的时用自由形式抽取。当某个兼容的既有企业模板能表示全部所请求字段时复用它。否则把扁平标量结果存入内置的 `global.properties` 元数据实例，或当结果含嵌套对象、表格或必须保留其类型的值时，在源文件旁上传一个 JSON sidecar。每次写入都要读回并与预期结果比对。绝不静默用文件描述替代、附上不完整或无关的模板、截断字段或丢弃字段。

不要创建或更改元数据模板。Box 不允许创建全局模板，而企业模板的管理超出了 Hermes 常规的 OAuth 内容工作流。若用户需要可复用的带类型企业元数据而又无兼容模板，说明必须由 Box Admin 或获授权的 Co-Admin 另行创建，保持既有结构化元数据不变，并汇报所持久化的 `global.properties` 实例或 JSON sidecar。完整的抽取与回写工作流见 [Search and AI](references/search-and-ai.md)。

第一次 Box AI 请求之前，说明 Box AI 必须已启用、会消耗 AI 单位，且仍受当前操作者权限限制；不要等对方确认。返回给 Hermes 的 AI 响应仍可能含敏感信息。只有当实质性批次的文件范围或预期 AI 单位用量含糊，或用户未明确要求该规模时才确认。见 [Search and AI](references/search-and-ai.md)。

## 安全操作

- 优先用 ID 而非路径，并在诊断文件缺失前先核验当前操作者。
- 用 `--json` 与 `--fields` 保持输出精简。对变更，先盘点、确认含糊或大的范围，再读回结果。
- 有序的 CLI 变更要串行执行，让进度与恢复毫不含糊。可扩展的工作用有文档的批量输入支持或受限的 SDK 并发。
- 不要仅为提供导航就创建共享链接。共享链接会改变访问权，需要明确确认。
- 不要把密钥放进聊天、命令输出、源码管理或日志。

## 汇报结果

对每个单独汇报的 Box 条目，包含其 ID 与可点击的导航链接：

- File: `https://app.box.com/file/<FILE_ID>`
- Folder: `https://app.box.com/folder/<FOLDER_ID>`
- Hub: `https://app.box.com/hubs/<HUB_ID>`

对大批量，链接源文件夹与目标文件夹及例外项，而不是罗列数百个条目。人可能打不开只对已连接 Box 账号可见的内容；要明确说明这一点。每份写入摘要都包含操作者与所做的核验。

## 核验

任何写入之后，用同一操作者取回该文件或文件夹，或列出其父级，并确认返回的 ID 与名称。对元数据写入，取回该元数据实例，把每个返回字段与预期值比对；仅 HTTP 成功不算核验。报告缺失、被规范化或被拒绝的值。对一次性的设置检查，创建一个冒烟文件夹、核验它，然后仅在用户授权清理时才删除它。
