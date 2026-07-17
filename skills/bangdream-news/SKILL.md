---
name: bangdream-news
description: BanG Dream 官网新闻/告知查询 SOP。给用户提供 BangDream/邦多利/邦邦 企划下 News（お知らせ/リリース/ライブ・イベント/メディア/グッズ 等资讯）的查询与解读。当用户想看最新新闻、搜某条告知/发售/媒体资讯、按时间或企划筛选新闻、或获取某篇新闻全文时，使用本 Skill。定时/推送场景由 scripts/scan_news.py 承担。企划包括 Poppin'Party(ppp)、Afterglow(ag)、Pastel＊Palettes(pp)、Roselia(萝)、ハロー、ハッピーワールド！(hhw)、Morfonica(蝶团)、RAISE A SUILEN(RAS)、MyGO!!!!!(狗)、Ave Mujica(鸡)、夢限大みゅーたいぷ(梦团)、millsage、一家Dumb Rock!、シャッフルユニット。
---

# BanG Dream! News 查询 SOP

## When NOT to use

- 非 BanG Dream 企划相关
- **Live / Event 的票务、抽选、场馆、场贩** → 走 `bangdream-live-query`
- 官方账号动态以外的内容

## 数据源

| 数据源 | 用途 |
|--------|------|
| `https://bang-dream.com/feed/`（RSS，10 条） | 最新几条 / 增量判断（含 pubDate、category、摘要、全文 `content:encoded`） |
| `https://bang-dream.com/news/`（列表 + 筛选表单） | 按关键词/分类/年月/企划翻历史（约 136 页） |
| `https://bang-dream.com/news/<id>/`（详情页） | 单篇全文（正文容器 `p-news-detail__content`） |

> **抓取优先级与 UA 门禁（决策层红线）**：
> - **优先用专用网页抓取工具**（webreader / Tavily 等：自带浏览器 UA、返回干净 markdown、省 token）；仅当环境没有这类工具（如定时脚本无 MCP 会话）才降级到 `curl` / `py`。
> - **红线**：bang-dream.com 对 RSS feed、`/news/`、所有详情页做 UA 门禁——裸 `curl`（默认 UA）一律返回 **404 空桩页（≈228B）**，易被误判成"JS 未渲染"。**任何抓取必须带浏览器 UA。**
> - 工具判定标准、curl/py 骨架见 [网页抓取策略](#网页抓取策略)。

## 查询流程

### 1. 最新列表 / 增量

- 「最近有什么 news」「有没有新的」→ 抓 RSS（10 条，新→旧）。RSS 带 category 与摘要，可直接回答；该篇在最新 10 条内时，全文可取 `<content:encoded>`。
- 字段说明（10 条、无 guid、pubDate/category）见 [News 列表筛选 / RSS 字段](#news-列表筛选--rss-字段)。

### 2. 关键词搜索

- 「搜 MyGO 相关 news」→ `/news/?s=<关键词>`（自由文本，日文需 URL 编码）。实测返回「検索結果」页且结果集过滤，确认生效。

### 3. 按分类 / 年月 / 企划筛选

- 分类 `category`（info / release / live-event / media / goods）、`year`、`month`、`artist[]`；分页 `/news/page/N/`（未筛选约 136 页）。构造规则见 [News 列表筛选 / RSS 字段](#news-列表筛选--rss-字段)。
- **务必翻完分页**，避免漏取。

### 4. 单篇全文

- 拿到 `/news/<id>/` → 抓详情页，正文容器 `<article class="p-news-detail__content c-post-content">`；若该篇在最新 10 条内，也可直接从 RSS `<content:encoded>` 取，免抓详情页。

## 定时推送（scan 脚本）

对话场景用上面的 SOP；**定时 / 推送场景**（cron / hermes 等常驻 agent、无对话上下文）走 `scripts/scan_news.py`：

```bash
python scripts/scan_news.py scan [--state-file <path>]
```

- 读 RSS → 比对 `--state-file`（默认 `~/.bangdream-news/state.json`，或环境变量 `BANGDREAM_NEWS_STATE`）去重 → **只吐宿主中立 JSON**（`new_items`：id / title / link / published_at / category / summary）。
- 去重 key = 文章 ID（RSS 无 guid，用 link 中的数字）。
- **渲染与推送渠道不在脚本内**：JSON 由调度侧（cron 包装 / hermes adapter / 用户配置）决定渲染成 markdown / 飞书卡片 / webhook。`count=0` 表示无更新，是否「静默」由调用方决定。

## Output

标题 + 日期 + 链接（+ 摘要）；全文给标题 + 总结后的正文。不输出抓取 / 完整度判断的过程信息。

## Reference

<div id="news-列表筛选--rss-字段"></div>

- [News 列表筛选 / RSS 字段](./reference/news-filter.md)

<div id="网页抓取策略"></div>

- [网页抓取策略](./reference/fetch-strategy.md)
