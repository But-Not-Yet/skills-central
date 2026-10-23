# OMV 盒子搜索栈（SearXNG / Crawl4AI / redis）排障与现行拓扑

10-21 实战全记录。访问方式：`ssh -i ~/.ssh/orangepi_key lacitadelle@192.168.50.10`（ssh config 别名 `orangepi`；机器=OrangePi 5 Plus，Armbian/Debian trixie，aarch64，15GiB；容器属 docker 组可免 sudo，改配置要 root 而 sudo 要密码——root 步骤交主人跑）。

## 现行拓扑（10-21 实测）

| 容器 | 端口/状态 | 备注 |
|---|---|---|
| searxng | 宿主 **8090** → 8080（`docker port searxng` 为准，别猜 8888/8080） | `formats: html+json`，agent 用 `GET /search?q=…&format=json` |
| redis | 内网 `redis:6379` | 是给 SearXNG limiter 当后端的；已改 `restart=unless-stopped`（曾被宿主重启摔死 exit 255 躺三周，`restart=no` 是病根） |
| crawl4ai | healthy | 抓取腿，LLM 导向爬虫（抓不是搜），接 SearXNG 后面用 |
| qdrant-research / open-webui / syncthing | Up | 与搜索无关 |

宿主配置文件：`/srv/dev-disk-by-uuid-f0870af7-c775-4b06-95af-5f832267725e/Docker/searxng/searxng/settings.yml`（**ro=true 只读挂载 + root 属主**：容器内 `docker exec` 改不动、宿主普通用户读不了——一律写命令块交主人 sudo 跑）。

## limiter 修好才算上岗：两个坑（都踩过）

1. **`limiter.toml` 缺文件**：这版镜像（2026.9.23）botdetection 要 `/etc/searxng/limiter.toml` 存在，缺了 limiter 整个趴窝（日志 `missing config file` + `The limiter requires Valkey`）。修法：`docker cp searxng:/usr/local/searxng/searx/limiter.toml` 到宿主挂载目录。
2. **配置键是顶层章节 `valkey:` 不是 `server.valkey:`**：`valkeydb.py` 读 `get_setting('valkey.url')`（`redis.url` 已弃用且缩进在 server: 下取不到也无效）。`valkey:\n  url: redis://redis:6379/0` 必须与 `server:` 平级。**判据**：日志出现 `connecting to Valkey` + `connected to Valkey`，且 `docker exec redis redis-cli dbsize` 出数。「查询变快/状态变 Suspended」都**不算**缓存生效的证据（前者是上游挂起少等两家，后者是进程内存态）——10-21 就是拿这两个假证据被自己复验推翻的。
3. 上线后日志 `X-Forwarded-For nor X-Real-IP header is set!` = 无前置代理，limiter 按直连 IP 计数，自用无害。

## 引擎生死账（家宽 Comcast 单 IPv4，无全局 IPv6）

- 活着：bing、yahoo、mojeek、marginalia（点名测试各出真结果）。
- 被 IP 拉黑：google 403、google_cse 无 key、brave 429、startpage（Google 二道贩子跟死）、duckduckgo CAPTCHA（SearXNG 的 UA 被认，**咱家 IP 本身没被 DDG 拉黑**——ddgs 库在台式机实测出好结果）。
- wikidata 对普通词 0 条（只吃实体词，别当它健康也别删）。
- 引擎开关追加同名条目=后写覆盖，直接 tee -a 即可改禁用。ahmia/torch `can't register engine` = 缺 tor 的良性噪音。

## 免 key 搜索备胎（10-21 实测通过，台式机出口）

- **ddgs**：`uv run --with ddgs python3 -c "from ddgs import DDGS; ..."` 免 key 免卡，走 DDG API 端点。
- **Firecrawl keyless MCP**：POST `https://mcp.firecrawl.dev/v2/mcp`（Accept: application/json, text/event-stream）零注册零 key，厂商自报 1000 credits/月。
- Brave Search API：免费 $5/月额度（约 1000 次）但**注册要绑卡**（主人 10-21 实证撞门）。政策两源打架：3 月攻略页写免卡，9 月写 now required——以现场为准。
- 代理轮换（mitmproxy 官方配方）在咱家**没意义**：单 IPv4 无第二出口；治本窟=路由器开 IPv6（Comcast 住宅 /64 轮换源地址），未做。