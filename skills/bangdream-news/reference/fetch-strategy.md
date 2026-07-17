# 网页抓取策略

> **bang-dream.com 站点抓取纪律（news 与 live-query 共用同一套）**：工具优先级、UA 纪律、curl/py 兜底骨架统一在此表达。SKILL.md 与 news-filter.md 只留决策/红线 + 指向本文件的链接。
> 验证日期：2026-07-17（news 侧复核 RSS feed、`/news/`、详情页，UA 门禁与 live-query 一致）；站点改版或门禁策略变更后需复核。

## 优先级

1. **优先：专用网页抓取工具**（webreader / Tavily 等）——自带浏览器 UA、返回干净 markdown、省 token、少踩 404。
2. **兜底：`curl` 或 `py` 脚本**——仅当环境没有专用工具时（如定时脚本无 MCP 会话）使用，且**必须带浏览器 UA**。

> 取代旧版「curl 直连优先」：专用工具返回正文即用、无需自解析 HTML，更顺手。

## 专用工具判定标准

**自带浏览器 UA、且能返回正文 DOM/markdown 的抓取服务，即为"专用工具"，优先用。**

只给标题/摘要、不给正文的纯搜索类工具不算——它只能用来**发现** URL，正文仍需专用抓取工具或兜底。

## 示例名单（非穷举，会变）

撰写时已知的专用抓取工具，**仅作示例**；以判定标准为准：

| 工具 | 形态 | 备注 |
|------|------|------|
| `web-reader` / `web_reader`（webReader） | MCP | URL → markdown，自带 UA |
| Tavily 系列（`tavily_extract` / `tavily_crawl` 等） | MCP | extract 取正文、crawl 批量 |

> 名单会随环境过期；标准恒定。以标准为准，名单仅辅助识别。

## 兜底骨架（curl / py）

**红线**：裸 `curl`（默认 UA）对 RSS feed、`/news/`、`/events/` 及所有详情页一律返回 **404 空桩页（≈228B）**，易被误判成"JS 未渲染"。**任何兜底必须带浏览器 UA。**

实测（2026-07-17 news 侧复核）：
- `https://bang-dream.com/feed/`（RSS）：无 UA → `404 / 228B`；带浏览器 UA → `200 / application/rss+xml / ~30KB / 10 条`。
- `https://bang-dream.com/news/`：无 UA → `404`；带 UA → `200 / ~47KB`，SSR。
- `https://bang-dream.com/news/2371/`（详情页）：带 UA → `200 / ~32KB`，SSR，正文容器 `<article class="p-news-detail__content c-post-content">`。

### curl

```bash
curl -sS \
  -A '<浏览器 UA>' \
  -H 'Accept-Language: ja,en;q=0.8' \
  '<url>'
```

- `-A '<浏览器 UA>'`：**必带**（否则 404）。`<浏览器 UA>` 替换为任意近期桌面浏览器 UA（Chrome / Firefox / Safari 当前版均可，门禁只验"像不像浏览器"，不绑版本）。
- `-H 'Accept-Language: ja,en;q=0.8'`：日文内容，建议带。
- `<url>`：RSS feed、`/news/` 列表、详情页、或带筛选/分页的构造 URL（见下）。

### py（requests）

```python
import requests

UA = "<浏览器 UA>"  # 任意近期桌面浏览器 UA，必带（否则 404）
headers = {"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"}
resp = requests.get("<url>", headers=headers, timeout=20)
resp.raise_for_status()
html = resp.text  # SSR，直接含卡片/筛选/正文 DOM，BeautifulSoup 解析即可
```

## 分页与筛选

`/news/` 列表页的筛选参数（`s` / `category` / `year` / `month` / `artist[]`）、分页路径 `/page/N/`（未筛选约 136 页）、RSS feed 字段（10 条、去重用文章 ID、pubDate/category）等，见 [News 列表筛选 / RSS 字段](./news-filter.md)。兜底抓 `/news/` 列表须**翻完所有分页**。
