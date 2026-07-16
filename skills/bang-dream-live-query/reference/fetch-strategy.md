# 网页抓取策略

> bang-dream-live-query 的**抓取层单一信源**：工具优先级、UA 纪律、curl/py 兜底骨架统一在此表达。SKILL.md 与 event-filter.md 只留决策/红线 + 指向本文件的链接。
> 验证日期：2026-07-16；站点改版或门禁策略变更后需复核。

## 优先级

1. **优先：专用网页抓取工具**（webreader / Tavily 等）——自带浏览器 UA、返回干净 markdown、省 token、少踩 404。
2. **兜底：`curl` 或 `py` 脚本**——仅当环境没有专用工具时用，且**必须带浏览器 UA**。

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

**红线**：裸 `curl`（默认 UA）对 `/events/` 及详情页返回 **404 空桩页（≈228B）**，易被误判成"JS 未渲染"。**任何兜底必须带浏览器 UA。**

实测（2026-07-16）：无 UA → `404 / 228B`；带浏览器 UA → 列表页 `200 / ~59KB`、详情页 `200 / ~40KB`，SSR 标记（`artist[]`、`event_tag`、`公演`、`チケット` 等）全部命中，确认服务端渲染、无需 JS。

### curl

```bash
curl -sS \
  -A '<浏览器 UA>' \
  -H 'Accept-Language: ja,en;q=0.8' \
  '<url>'
```

- `-A '<浏览器 UA>'`：**必带**（否则 404）。`<浏览器 UA>` 替换为任意近期桌面浏览器 UA（Chrome / Firefox / Safari 当前版均可，门禁只验"像不像浏览器"，不绑版本）。
- `-H 'Accept-Language: ja,en;q=0.8'`：日文内容，建议带。
- `<url>`：列表页、详情页、或带筛选/分页的构造 URL（见下）。

### py（requests）

```python
import requests

UA = "<浏览器 UA>"  # 任意近期桌面浏览器 UA，必带（否则 404）
headers = {"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"}
resp = requests.get("<url>", headers=headers, timeout=20)
resp.raise_for_status()
html = resp.text  # 列表页 SSR，直接含卡片/筛选 DOM，BeautifulSoup 解析即可
```

## 分页与筛选

列表页 `/events/` 的筛选参数（`artist[]` / `event_tag` / `year` / `month` / `s`）、分页路径 `/page/N/`、多选拼接等构造规则，见 [Live / Event 页面筛选说明](./event-filter.md)。兜底抓列表页须**翻完所有分页**（未筛选 16 页，筛选后减少）。
