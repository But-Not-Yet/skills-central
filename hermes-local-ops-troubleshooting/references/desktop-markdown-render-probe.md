# 桌面 markdown / 公式渲染探针

主人报「桌面版渲染不出 X（公式/markdown）」时用。目标：两层复现，定位到底是渲染器不支持还是自己发的写法触发失败。

## 先定位渲染链（读源码，别上网找插件）

桌面版 markdown 渲染**在树内**，KaTeX 内置，不存在「缺插件所以不渲染」。相关三处（`~/.hermes/hermes-agent/apps/desktop/`）：

- `src/components/assistant-ui/markdown-text.tsx` —— 聊天正文的装配点，math 插件在这里配（`singleDollarTextMath: true`，即 `$x$` 走行内）。
- `src/lib/markdown-preprocess.ts` —— 预处理：货币 `$` 转义、夹中文的裸 `$` 对转义、多行 hugging display math 拆行。
- `src/lib/katex-memo.ts` —— KaTeX 封装（带 LRU 缓存）。失败策略：严格模式抛 → 宽松模式重试 → 仍失败就画一个 `katex-error` span，**把源码原样印到屏幕上**。这就是「看起来整个软件不支持 LaTeX」的实际来源。
- 现成范例：`src/lib/file-preview-math.render.test.tsx` 就是这条链的渲染测试，照它抄装配即可。
- KaTeX 本体版本：读 `~/.hermes/hermes-agent/node_modules/katex/package.json`。

## 探针一：KaTeX 能力（秒级，不碰 UI）

**写成 .js 文件，别用 shell 里的 `node -e`**：LaTeX 反斜杠会被 JS 字符串转义吃掉，`\u` 开头直接 `Bad character escape sequence`。文件里用 `String.raw` 包公式源码：

```js
const katex = require('/home/<user>/.hermes/hermes-agent/node_modules/katex');
const html = katex.renderToString(String.raw`\sum_{n=0}^{N}d^{n} \tag{7.4}`, {
  displayMode: true, throwOnError: false, strict: 'ignore', errorColor: '#f00',
});
console.log(html.includes('katex-error') ? 'FAIL' : 'OK');
```

**`displayMode` 两个值都要试**：`\tag` 一类命令只在 display 有效，只测 `true` 会漏掉「单行 `$$` 实际走行内通道」这条真失败。

## 探针二：整条聊天链（含 markdown 预处理），jsdom 渲染

在 `apps/desktop/` 下临时建 `src/lib/tmp-<topic>.probe.test.tsx`，复刻聊天装配：`preprocessMarkdown(source)` 喂进 `<Streamdown mode="static" plugins={{ math: createMemoizedMathPlugin({ singleDollarTextMath: true }) }}>`。跑：

```bash
cd ~/.hermes/hermes-agent/apps/desktop && npx vitest run src/lib/tmp-<topic>.probe.test.tsx
```

**关键坑：这个环境里 vitest 的 `console.log` 可能整段不出现**（自己打的输出标记抓不到，输出看着是空的）。把事实拼成字符串塞进断言，让它进失败 diff：

```ts
expect(lines.join('\n')).toBe('FORCE-DIFF')   // 事实出现在 "Received" 段
```

**DOM 判据**：`.katex` 个数 > 0 = 渲染成功；`.katex-error` 个数 > 0 = 渲染失败、屏幕上就是源码文本；`.katex-display` 区分 display 与 inline。一次探针把多种写法并排放（单行/own-line/围栏/行内带中文…），逐行出计数。

测完删临时文件，`git status --porcelain` 确认工作树干净。

## 汇报纪律

- 分清两层结论：**「写法触发失败」**（改自己的格式，见 `chat-math-typesetting` 的写法表）与 **「渲染器不支持」**（才谈插件/上游 issue）。后者要先被探针二证伪，不能凭印象说。
- 顺手报版本状态但标清未核：源码 mtime vs `apps/desktop/dist` 构建时间可查；**当前窗口实际加载的是哪份 dist 常无法从进程表确认**，这条一律标未核，别断言「你跑的就是这份」。
- 插件只在主人要附加功能时才提（例：点公式复制 LaTeX 源码——KaTeX 把原文存在 DOM 的 `<annotation encoding="application/x-tex">` 里，读它就是逐字节原文，不是反推）。上游有未合并的 feature request 时提一句即可，别把「装插件」当渲染失败的第一解法。
