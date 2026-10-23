---
name: maps
description: "查地理编码、POI、路线、距离与时区时使用（OpenStreetMap/OSRM）。只要涉及地点坐标、附近搜索、导航、行程时间或时区，就主动加载。即使用户只是发来一个位置坐标或问「附近有什么」。"
version: 1.2.0
author: Mibayy
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [maps, geocoding, places, routing, distance, directions, nearby, location, openstreetmap, nominatim, overpass, osrm]
    category: productivity
    requires_toolsets: [terminal]
    supersedes: [find-nearby]
---

# Maps 技能

位置智能，使用免费开放的数据源。8 个命令、44 个 POI
分类，零依赖（仅 Python 标准库），无需 API key。

数据源：OpenStreetMap/Nominatim、Overpass API、OSRM、TimeAPI.io。

本 skill 取代旧的 `find-nearby` skill——find-nearby 的全部功能都由下方的 `nearby` 命令覆盖，同样支持 `--near "<place>"` 快捷方式与多分类。

## 何时使用

- 用户发来 Telegram 位置（消息里含经纬度）→ `nearby`
- 用户想要地名的坐标 → `search`
- 用户有坐标、想要地址 → `reverse`
- 用户问附近的餐厅、医院、药房、酒店等 → `nearby`
- 用户想要驾车/步行/骑行距离或行程时间 → `distance`
- 用户想要两地之间的逐向路线 → `directions`
- 用户想要某地点的时区信息 → `timezone`
- 用户想在某地理区域内搜索 POI → `area` + `bbox`

## 前置条件

Python 3.8+（仅标准库——无需 pip 安装）。

脚本路径：`~/.hermes/skills/maps/scripts/maps_client.py`

## 命令

```bash
MAPS=~/.hermes/skills/maps/scripts/maps_client.py
```

### search — 地名地理编码

```bash
python3 $MAPS search "Eiffel Tower"
python3 $MAPS search "1600 Pennsylvania Ave, Washington DC"
```

返回：lat、lon、显示名、类型、边界框、重要度评分。

### reverse — 坐标转地址

```bash
python3 $MAPS reverse 48.8584 2.2945
```

返回：完整地址拆分（街道、城市、州/省、国家、邮编）。

### nearby — 按分类找地点

```bash
# By coordinates (from a Telegram location pin, for example)
python3 $MAPS nearby 48.8584 2.2945 restaurant --limit 10
python3 $MAPS nearby 40.7128 -74.0060 hospital --radius 2000

# By address / city / zip / landmark — --near auto-geocodes
python3 $MAPS nearby --near "Times Square, New York" --category cafe
python3 $MAPS nearby --near "90210" --category pharmacy

# Multiple categories merged into one query
python3 $MAPS nearby --near "downtown austin" --category restaurant --category bar --limit 10
```

46 个分类：restaurant, cafe, bar, hospital, pharmacy, hotel, guest_house,
camp_site, supermarket, atm, gas_station, parking, museum, park, school,
university, bank, police, fire_station, library, airport, train_station,
bus_stop, church, mosque, synagogue, dentist, doctor, cinema, theatre, gym,
swimming_pool, post_office, convenience_store, bakery, bookshop, laundry,
car_wash, car_rental, bicycle_rental, taxi, veterinary, zoo, playground,
stadium, nightclub.

每条结果包含：`name`、`address`、`lat`/`lon`、`distance_m`、`maps_url`（可点击的 Google Maps 链接）、`directions_url`（从搜索点出发的 Google Maps 路线）。以及可得的推广标签——`cuisine`、`hours`（opening_hours）、`phone`、`website`。

### distance — 行程距离与时间

```bash
python3 $MAPS distance "Paris" --to "Lyon"
python3 $MAPS distance "New York" --to "Boston" --mode driving
python3 $MAPS distance "Big Ben" --to "Tower Bridge" --mode walking
```

模式：driving（默认）、walking、cycling。返回道路距离、耗时，以及用于对比的直线距离。

### directions — 逐向导航

```bash
python3 $MAPS directions "Eiffel Tower" --to "Louvre Museum" --mode walking
python3 $MAPS directions "JFK Airport" --to "Times Square" --mode driving
```

返回带编号的步骤，含指令、距离、耗时、道路名与动作类型（turn、depart、arrive 等）。

### timezone — 坐标对应时区

```bash
python3 $MAPS timezone 48.8584 2.2945
python3 $MAPS timezone 35.6762 139.6503
```

返回时区名称、UTC 偏移与当前本地时间。

### area — 地点的边界框与面积

```bash
python3 $MAPS area "Manhattan, New York"
python3 $MAPS area "London"
```

返回边界框坐标、宽/高（km）与近似面积。可作为 bbox 命令的输入。

### bbox — 在边界框内搜索

```bash
python3 $MAPS bbox 40.75 -74.00 40.77 -73.98 restaurant --limit 20
```

在地理矩形内查找 POI。先用 `area` 取得某命名地点的边界框坐标。

## 处理 Telegram 位置

当用户发来位置时，消息里含 `latitude:` 与 `longitude:` 字段。提取它们直接传给 `nearby`：

```bash
# User sent a pin at 36.17, -115.14 and asked "find cafes nearby"
python3 $MAPS nearby 36.17 -115.14 cafe --radius 1500
```

把结果以编号列表呈现，含名称、距离与 `maps_url` 字段，让用户在聊天里得到可点击打开的链接。对于「现在开门吗」的问题，查 `hours` 字段。若缺失或不清，用 `web_search` 核实，因为 OSM 的营业时间由社区维护，未必总是最新的。

## 工作流示例

**「找罗马斗兽场附近的意大利餐厅」：**
1. `nearby --near "Colosseum Rome" --category restaurant --radius 500`
   — 一条命令，自动地理编码

**「他们发的这个位置附近有什么？」：**
1. 从 Telegram 消息里提取 lat/lon
2. `nearby LAT LON cafe --radius 1500`

**「从酒店怎么走到会议中心？」：**
1. `directions "Hotel Name" --to "Conference Center" --mode walking`

**「西雅图市中心有哪些餐厅？」：**
1. `area "Downtown Seattle"` → 取得边界框
2. `bbox S W N E restaurant --limit 30`

## 常见坑

- Nominatim 服务条款：最多 1 req/s（脚本自动处理）
- `nearby` 需要 lat/lon 或 `--near "<address>"`——二者取其一
- OSRM 的路由覆盖以欧洲和北美最好
- Overpass API 在高峰时段可能较慢。脚本会自动
  在镜像之间回退（overpass-api.de → overpass.kumi.systems）
- `distance` 与 `directions` 用 `--to` 标志指定目的地（非位置参数）
- 若仅有邮编在全球范围内结果含糊，请加上国家/州

## 验证

```bash
python3 ~/.hermes/skills/maps/scripts/maps_client.py search "Statue of Liberty"
# Should return lat ~40.689, lon ~-74.044

python3 ~/.hermes/skills/maps/scripts/maps_client.py nearby --near "Times Square" --category restaurant --limit 3
# Should return a list of restaurants within ~500m of Times Square
```
