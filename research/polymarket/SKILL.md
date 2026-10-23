---
name: polymarket
description: "查 Polymarket 市场、价格、订单簿、历史时使用。只要问预测市场、赔率或事件概率，就主动加载，即使用户只说「X 有多大可能发生」。"
version: 1.0.0
author: Hermes Agent + Teknium
tags: [polymarket, prediction-markets, market-data, trading]
platforms: [linux, macos, windows]
---

# Polymarket — Prediction Market Data

Query prediction market data from Polymarket using their public REST APIs.
All endpoints are read-only and require zero authentication.

完整 endpoint 参考（含 curl 示例）见 `references/api-endpoints.md`。

## 何时使用

- 用户问预测市场、赔率或事件概率
- 用户想知道「X 发生的概率是多少？」
- 用户专门问 Polymarket
- 用户要市场价格、订单簿数据或价格历史
- 用户要监控或跟踪预测市场动向

## 关键概念

- **Event** 包含一个或多个 **Market**（1:多关系）
- **Market** 是二元结果，Yes/No 价格在 0.00 到 1.00 之间
- 价格就是概率：价格 0.65 表示市场认为有 65% 可能
- `outcomePrices` 字段：JSON 编码的数组，如 `["0.80", "0.20"]`
- `clobTokenIds` 字段：两个 token ID [Yes, No] 的 JSON 编码数组，用于价格/订单簿查询
- `conditionId` 字段：用于价格历史查询的十六进制字符串
- 成交量以 USDC（美元）计

## 三个公开 API

1. **Gamma API**（`gamma-api.polymarket.com`）— 发现、搜索、浏览
2. **CLOB API**（`clob.polymarket.com`）— 实时价格、订单簿、历史
3. **Data API**（`data-api.polymarket.com`）— 成交、未平仓量

## 典型工作流

当用户问预测市场赔率时：

1. 用 Gamma API 的 public-search endpoint 按其查询 **搜索**
2. **解析**响应 — 抽出 event 及其嵌套的 market
3. **呈现**市场问题、以百分比表示的当前价格与成交量
4. 被要求时**深入** — 用 clobTokenIds 查订单簿、conditionId 查历史

## 呈现结果

为可读性把价格格式化成百分比：
- outcomePrices `["0.652", "0.348"]` 变成 "Yes: 65.2%, No: 34.8%"
- 始终显示市场问题与概率
- 有成交量时一并给出

示例：`"Will X happen?" — 65.2% Yes ($1.2M volume)`

## 解析双重编码字段

Gamma API 把 `outcomePrices`、`outcomes` 与 `clobTokenIds` 作为 JSON 字符串
嵌在 JSON 响应里（双重编码）。用 Python 处理时，用
`json.loads(market['outcomePrices'])` 解析出真正的数组。

## 速率限制

很宽松 — 正常使用基本碰不到：
- Gamma：每 10 秒 4,000 次请求（一般）
- CLOB：每 10 秒 9,000 次请求（一般）
- Data：每 10 秒 1,000 次请求（一般）

## 限制

- 本 skill 只读 — 不支持下单交易
- 交易需要基于钱包的加密认证（EIP-712 签名）
- 部分新市场可能没有价格历史
- 交易有地理限制，但只读数据全球可访问
