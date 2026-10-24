# ::preview 内联卡宽度上限 = 640 CSS 像素（宿主写死）

实物源码：`apps/desktop/src/components/assistant-ui/inline-preview-directive.tsx`

- `const MAX_COLUMN_WIDTH = 640`（54 行）；生效行 `Math.min(contentWidth, MAX_COLUMN_WIDTH)`（513 行）。
- 宽度只在**首帧测一次**后不再随窗口伸缩（23 行注释：防 %-width 子元素每次变窄回流死循环）。测量脚本在 263 行区：width = body 直接子元素 getBoundingClientRect 的并集（文档本身永远填满视口，所以量子元素）。
- 结论：聊天内联 ::preview 卡片**永远不可能与会话等宽**（除非改宿主代码）。设计宽画布按 ≤640px 设计；要全宽看大图走右侧预览面板（right-rail preview.tsx / webview）那条路。
- 写死 1240px 画布的后果：被压到 640，节点挤成一团——内容侧修法是重画窄版，不是等宿主。
