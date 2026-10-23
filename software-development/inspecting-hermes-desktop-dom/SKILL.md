---
name: inspecting-hermes-desktop-dom
description: "通过 CDP 读 Hermes 桌面端实时 DOM/CSS 时使用。只要要验证桌面端 UI 改动是否真生效、查哪条 CSS 规则胜出或读渲染进程报错，就主动加载。即使用户没明说 CDP。不用于性能剖析。"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [desktop, electron, cdp, dom, ui-verification, self-inspection]
    related_skills: [node-inspect-debugger, systematic-debugging, dogfood]
---

# 检查 Hermes 桌面端的实时 DOM

## Overview（概览）

当你在开发 `apps/desktop`、而用户正运行同一个 app 时（`hgui` / `npm run dev`），你可以读他们眼前那个窗口的**实时渲染 DOM**。计算样式、几何、究竟哪条 CSS 规则胜出、控制台输出——而不是从 `.tsx` 去猜、然后猜错。

dev-server 运行时会在 `127.0.0.1:9222` 上自动开一个 Chrome DevTools Protocol 端口。渲染进程就是一个 Chromium 页面，所以 DevTools 能读的东西，脚本也能读。

**这不能取代用眼睛看。** CDP 回答的是*事实性*问题（"计算出的 padding 是多少"、"这个元素渲染了吗"、"哪个选择器命中"）。它没法告诉你结果好不好看。色彩平衡、间距手感、以及"这丑不丑"，仍要靠用户的眼睛或一张截图。事实交给 CDP。审美交给用户。

## When to Use（何时用）

- 验证一次 UI 改动在运行中的 app 里真的生效了
- "这个元素怎么还是 X？"——改任何东西之前先找出胜出的规则
- 为即将改动的组件找一个稳定的选择器
- 在真实节点上查一个 design token 的计算值
- 读用户提到、但复制不出来的渲染进程控制台报错

**不用于：** 性能剖析或堆分析（`node-inspect-debugger`、`debugging-hermes-desktop`），或任何「真正的疑问是『这样看起来对不对』」的场合。

## The port（端口）

任何 dev-server 运行都在 `127.0.0.1:9222` 上开放。恰好两种情况关闭（`apps/desktop/electron/dev-cdp.ts`）：

- **打包构建** — 永远关闭，且没有任何环境值能覆盖它。
- **没有 `HERMES_DESKTOP_DEV_SERVER`** — 未打包的 `electron .` 对着 `dist/` 跑，是打包版冒烟测试的方式，所以它表现得像打包版。

`HERMES_DESKTOP_CDP_PORT` 可挪动端口（`=9333`）或禁用它（`=off`）。

动手前先查：

```bash
curl -s --max-time 3 http://127.0.0.1:${HERMES_DESKTOP_CDP_PORT:-9222}/json/version
```

空 → 没有端口。别悄悄去猜别的端口。

**绝不要为了拿端口去重启用户的 app。** 那会毁掉他们的会话与状态。改为启动你自己的隔离实例（见下）。

## Reading the DOM（读 DOM）

`apps/desktop/scripts/eval.mjs` 就是那个单行工具：

```bash
cd apps/desktop
node scripts/eval.mjs "document.querySelectorAll('[data-slot]').length"
```

多步作业用共享客户端——它带 target 发现与 promise 感知的 eval：

```js
import { CDP, SELECTORS } from './scripts/perf/lib/cdp.mjs'

const cdp = await CDP.connect({ port: 9222, match: '5174' })
const out = await cdp.eval(`JSON.stringify({
  radius: getComputedStyle(document.documentElement).getPropertyValue('--radius-scalar').trim(),
  composer: !!document.querySelector('[data-slot="composer-rich-input"]')
})`)
cdp.close()
```

`scripts/perf/lib/cdp.mjs` 里的 `SELECTORS` 保存着稳定的 `data-slot` 钩子（composer、thread viewport、assistant message、turn pair、profile rail）。优先用它们，别自创 `querySelector`——组件挪窝时它们是作为一个整体更新的。

## 它最擅长的问题：哪条规则胜出？

因为一个样式「没生效」就去改每一处调用点，是典型的浪费。先读真实节点：

```js
const el = document.querySelector('[data-slot="aui_assistant-message-root"] a')
JSON.stringify({
  ownClasses: el.className,
  weight: getComputedStyle(el).fontWeight,
  parents: (() => {
    const out = []
    let n = el
    while ((n = n.parentElement) && out.length < 6) out.push(n.className)
    return out
  })()
})
```

若该节点自身不带类，那这个值是**继承**来的——横扫调用点修不好它，你需要祖先规则。插件样式表（例如 `@tailwindcss/typography` 的 `prose a { font-weight: 500 }`）经常压过工具类。在共享类上覆盖，而不是逐处覆盖。

## Your own isolated instance（你自己的隔离实例）

当没有端口、或你不能打扰用户的窗口时：

```bash
cd apps/desktop
HERMES_HOME=$HOME/.hermes/cache/scratch/cdp-probe-home \
HERMES_DESKTOP_DEV_SERVER=http://127.0.0.1:5174 \
HERMES_DESKTOP_CDP_PORT=9333 \
  npx electron . --user-data-dir=$HOME/.hermes/cache/scratch/cdp-probe-userdata
```

单独的 `--user-data-dir` 绕开 Electron 的单实例锁，所以它不会和一个正在跑的 `hgui` 撞车。单独的 `HERMES_HOME` 让它远离真实会话。出于同样的理由，挑一个 9222 以外的端口。后台运行，用完杀掉。

若要连性能测试台一起，`npm run perf:serve` 做同样的事，并烤入一个临时 `HERMES_HOME`。

## Pitfalls（坑）

- **绝不要为「腾出」什么而杀掉用户的 dev server 或 app。** 服务中途被杀会毁掉 Chromium 的 socket 池，随之而来的 `ERR_NETWORK_CHANGED` 会栽赃到你刚改动的东西上。
- **一次性 `HERMES_HOME` 没有后端。** app 会为 `hermes:api` 记 `ECONNREFUSED`，并可能自行退出。渲染进程仍会挂载、DOM 仍可读——赶紧读，别把自行退出的探针误当成端口坏了。Chromium 绑定时会记 `DevTools listening on ws://127.0.0.1:<port>/…`。那一行就是端口已开的证据。
- **轮询，别只探一次。** 刚启动的 app 需要一两秒端口才应答。
- **绝不要 dump 整个 DOM。** 桌面端渲染几百个节点，`outerHTML` 会淹没你的上下文。在被求值的表达式里投射出一个小的 JSON 对象。
- **给 `CDP.connect` 传 `match`。** 不传的话你可能挂到宠物浮层、快速输入窗口或某个 devtools target，而不是主窗口。
- **`cdp.eval` 直接返回该值。裸的 `Runtime.evaluate` 会双重嵌套它**（`.result.result.value`）。用包装器。
- **本仓库里 `import.meta.env.DEV` 在 `vite dev` 下是 `true`。** `apps/desktop/scripts/profile-typing-lag.md` 里声称相反的注记已过时。
