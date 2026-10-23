---
name: searxng-selfhost-ops
version: 1.0.0
author: Nekonya (小喵)
license: MIT
description: 改、加、验收 NAS 上 docker 版 SearXNG 时加载。
metadata:
  hermes:
    tags: [searxng, docker, nas, search, ops]
---

# SearXNG 自托管运维（NAS docker 实例）

## When to Use

主人要改/验收 SearXNG（NAS `192.168.50.10:8090`，容器 `searxng` + `redis`）时加载：加引擎、查 429、验引擎是否出结果、limiter/valkey 配置都算。SSH 用 `ssh -i ~/.ssh/orangepi_key -o IdentitiesOnly=yes -o BatchMode=yes lacitadelle@192.168.50.10`。

## 配置面与改法

- 生效配置 = `/etc/searxng/settings.yml`（宿主绑定挂载 `/srv/dev-disk-by-uuid-f087.../Docker/searxng/searxng/`，属主 root）。文件带 `use_default_settings: true`：override 里按引擎名追加条目即按名合并，不必抄全表。
- 内置引擎全表在容器内 `/usr/local/searxng/searx/settings.yml`（391 个引擎）。审计谁开谁关用容器 venv python + yaml 解析该文件，别用 grep 相邻行猜 `disabled`（字段不相邻）。
- **写权限死结（实测）**：宿主目录 root 属主、lacitadelle 连 ls 都拒；容器里 `-u root` 也无 CAP_DAC_OVERRIDE（CapEff 0xc1），写不进绑定挂载；`sudo -S` 喂密码被 Hermes 工具闸拦。正确路线：文件 scp 到 Pi 的 /tmp → 请主人跑 `sudo cp` + `docker restart`。改前先让主人备份成带日期名。
- 改完必验：`docker exec searxng /usr/local/searxng/.venv/bin/python -c "import yaml;..."` 解析通过再重启。

## 引擎机制（决定怎么加）

- **引擎按类别触发**：general 查询只跑 general 类引擎；学术（crossref/openalex/pubmed/google scholar/europepmc/semantic scholar/openaire）只在 science/research 分类出结果。加几十个引擎几乎不加延迟，真实代价是被风控挂起。
- **Suspended 会自动过期**，不是永久禁用；`unresponsive_engines` 字段逐查询给挂起名单和原因。
- 部分引擎默认已启用（arxiv、pubmed、mdn、docker hub、mojeek、google scholar 等），写 override 前先查内置表，别重复开。
- 坑：日志里的注册名 ≠ 显示名（`torch: can't register engine` 实际是 startpage）；google 无 consent cookie 报 `access denied`；google cse 无 API key 就是废的；wolframalpha 每次 timeout（默认超时掐死慢引擎，需单独放宽才可能活）；中文引擎被风控后连查会 `unexpected crash`（搜狗认生）。

## 验引擎通不通：必须从容器内打

出口 IP 以容器实测为准，别引用旧印象（本机与 Orange Pi 是同一 Comcast 美国住宅出口，曾误记成新加坡被主人纠正；`docker exec searxng wget -qO- ifconfig.me` 一测便知）。

容器 venv **没有 requests**，连通性脚本用标准库 `urllib.request`（HTTPError 取 e.code 当状态码）。流程：本机写脚本 → scp 到 Pi → `docker cp` 进容器 → venv python 跑。以容器结果为准，本机结果只作对照。

## 验收查询回路

`curl "http://192.168.50.10:8090/search?q=...&format=json"` → python `Counter(r['engine'])` 数结果分布 + 读 `unresponsive_engines`。加 `&categories=science|research|it` 验非 general 线。重启后头几秒服务未就绪会连接秒断（HTTP=000），等 10 秒重试再下结论。

## limiter 与 redis

- 内网查询吃 429 = limiter 把自家人拉黑：把家网段写进 `limiter.toml` 的 `pass_ip`（优先级最高，放行后连 UA 都不查）。limiter 活体证据：redis 里出现 `SearXNG_limiter.token` 键。
- valkey 接线验证：容器内 `from searx import valkeydb; valkeydb.initialize()` 返 True + `client().ping()`。
- 结果缓存是否真进 redis 要单独看 dbsize 是否随查询增长，limiter 用上了 ≠ 结果缓存挂上了。
- 查询到底发没发给 redis：`timeout 12 docker exec redis redis-cli monitor` 后台跑、中间打一发查询、再读输出捕获（这版 redis-cli 的 monitor 不支持 `--count`）。429 与 dbsize=0 同现 = limiter 秒拒、查询根本没到引擎层，先修 limiter 再谈缓存路径。
