# 真实素材图检索（deck / 文档 / 网页交付）

顺位：Wikimedia Commons API（有 JSON 接口与许可证元数据，机器友好）＞ 网站官方 API ＞ 前端页面。多数图库前端（Unsplash 等）挂着 Anubis 工作量证明墙，`web_extract` 只会拿到验证页——别纠结语料，直接走 Commons。

## 检索

```bash
curl -s -A 'DeckResearch/1.0 (contact: researcher)' \
  "https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch=<QUERY_URL编码>&gsrnamespace=6&gsrlimit=8&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=1600"
```

- **`gsrnamespace=6` 必带**（File: 命名空间）。漏了它，`generator=search` 配 `prop=imageinfo` 返回光秃秃的 `{"batchcomplete":""}`——看着像查无此图，其实是空查询，不是没素材。
- gsrsearch 里可拼 `%26filetype:bitmap` 限定位图；再按 `width>=1200` 过滤掉小图。
- `iiprop` 必须带 `extmetadata`：`LicenseShortName` 是许可证、`Artist` 是作者串。**下载前**确认可商用与署名义务；署名行格式：`作者, “作品名”, via Wikimedia Commons, 许可证缩写`。CC BY / CC BY-SA 可商用须署名；Public domain 可免署名但仍建议标注来路。
- 下载 `thumburl`（按 `iiurlwidth` 预生成的宽度，1600–2000 足够 4K 投影），**剥掉 `?utm_…` 查询串**再 curl；原图常 >10MB 别拉全尺寸。

## 限速

- 连发会在共享出口上吃 “You are making too many requests to the API”：检索调用之间 `sleep 5–8`；多个已知标题合并成一条 `titles=A|B|C`（URL 编码 `|`）的 imageinfo 查询，而不是发 N 条 search。
- UA 别用 curl 默认值，带个描述性标识更稳。

## 用图

- 下载后用 `file` / `identify` 确认真实尺寸格式再引用，别信 API 报的 size。
- 需要固定比例时 cover 裁切：`convert in.jpg -gravity center -crop <W>x<H>+0+0 +repage -resize 2000x out.jpg`（先按目标比例从中心裁，再缩放）。
- 「只有用户自己的往事」类配图不找替身：留 dashed NOTE 占位并注明不许编造。用了网图，正文或脚注要写明是示意照片、不对应讲者即将讲述的故事，防止被当成假回忆。
